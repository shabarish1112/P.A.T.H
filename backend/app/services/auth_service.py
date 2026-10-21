from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status

from app.core.config import Settings
from app.core.security import DUMMY_PASSWORD_HASH, create_access_token, create_refresh_token, hash_refresh_token, verify_password
from app.repositories.auth import AuthRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthUser, LoginRequest, TokenResponse
from app.schemas.enums import Role


class AuthService:
    def __init__(self, users: UserRepository, auth: AuthRepository, settings: Settings) -> None:
        self.users = users
        self.auth = auth
        self.settings = settings

    def _login_key(self, email: str, ip: str) -> str:
        return f'{email.lower()}|{ip}'

    def login(self, body: LoginRequest, request: Request) -> tuple[TokenResponse, str, datetime]:
        ip = request.client.host if request.client else 'unknown'
        key = self._login_key(body.email, ip)
        if self.auth.failures(key) >= 5:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Too many login attempts. Try again later.')
        user = self.users.get_by_email(body.email)
        password_hash = str(user['password_hash']) if user else DUMMY_PASSWORD_HASH
        password_valid = verify_password(body.password, password_hash)
        valid = bool(user) and password_valid and bool(user.get('is_active', True))
        if not valid:
            self.auth.record_failed_login(key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')
        self.auth.clear_failures(key)
        role = Role(str(user['role']))
        user_id = str(user['_id'])
        access_token, expires_at = create_access_token(user_id, str(user['email']), role, self.settings)
        refresh_token = create_refresh_token()
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_days)
        self.auth.save_refresh_token(
            user_id,
            hash_refresh_token(refresh_token),
            refresh_expires,
            request.headers.get('user-agent'),
            ip,
        )
        response = TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=AuthUser(
                id=user_id,
                email=str(user['email']),
                role=role,
                is_active=True,
            ),
        )
        return response, refresh_token, refresh_expires

    def refresh(self, refresh_token: str | None, request: Request) -> tuple[TokenResponse, str, datetime]:
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        token_hash = hash_refresh_token(refresh_token)
        stored = self.auth.get_refresh_token(token_hash)
        if stored is None or stored['expires_at'] <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        self.auth.revoke_refresh_token(token_hash)
        user = self.users.get_by_id(str(stored['user_id']))
        if user is None or not user.get('is_active', True):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        role = Role(str(user['role']))
        user_id = str(user['_id'])
        access_token, expires_at = create_access_token(user_id, str(user['email']), role, self.settings)
        new_refresh = create_refresh_token()
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=self.settings.refresh_token_days)
        ip = request.client.host if request.client else 'unknown'
        self.auth.save_refresh_token(
            user_id,
            hash_refresh_token(new_refresh),
            refresh_expires,
            request.headers.get('user-agent'),
            ip,
        )
        response = TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=AuthUser(id=user_id, email=str(user['email']), role=role, is_active=True),
        )
        return response, new_refresh, refresh_expires

    def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            self.auth.revoke_refresh_token(hash_refresh_token(refresh_token))
