from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.core.config import Settings, get_settings
from app.repositories.users import UserRepository, get_user_repository
from app.schemas.auth import AuthUser
from app.schemas.enums import Role

_password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_PASSWORD_HASH = _password_hasher.hash('path-dummy-password-for-timing-equalization')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode('utf-8'), right.encode('utf-8'))


def create_access_token(
    user_id: str, email: str, role: Role, settings: Settings, version: int = 0
) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    payload = {
        'sub': user_id,
        'email': email,
        'role': role.value,
        'type': 'access',
        'ver': version,
        'iat': datetime.now(UTC),
        'exp': expires_at,
        'jti': secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_at


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def decode_access_token(token: str, settings: Settings) -> dict[str, object]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token'
        ) from exc
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token type')
    return payload


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthUser:
    payload = decode_access_token(token, settings)
    user_id = str(payload.get('sub', ''))
    user = users.get_by_id(user_id)
    if user is None or not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication credentials'
        )
    if payload.get('ver', 0) != user.get('token_version', 0):
        raise HTTPException(status_code=401, detail='Session revoked; sign in again')
    if user.get('must_change_password') and request.url.path not in {
        '/api/auth/change-password',
        '/api/auth/me',
        '/api/auth/logout',
    }:
        raise HTTPException(status_code=403, detail='Password change required')
    auth_user = AuthUser(
        id=str(user['_id']),
        email=str(user['email']),
        role=Role(str(user['role'])),
        is_active=bool(user.get('is_active', True)),
        must_change_password=bool(user.get('must_change_password', False)),
    )
    request.state.user_id = auth_user.id
    return auth_user


def require_role(*roles: Role) -> Callable[..., AuthUser]:
    def dependency(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
        return current_user

    return dependency
