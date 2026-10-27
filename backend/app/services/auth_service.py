from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status

from app.core.config import Settings
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.repositories.audit import AuditRepository
from app.repositories.auth import AuthRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthUser, LoginRequest, PasswordChange, TokenResponse
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
        if self.auth.throttled(key, 5) or self.auth.throttled(f'ip|{ip}', 20):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail='Too many login attempts. Try again later.',
            )
        user = self.users.get_by_email(body.email)
        password_hash = str(user['password_hash']) if user else DUMMY_PASSWORD_HASH
        password_valid = verify_password(body.password, password_hash)
        if user is None or not password_valid or not user.get('is_active', True):
            self.auth.record_failed_login(key)
            self.auth.record_failed_login(f'ip|{ip}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')
        self.auth.clear_failures(key)
        role = Role(str(user['role']))
        user_id = str(user['_id'])
        access_token, expires_at = create_access_token(
            user_id, str(user['email']), role, self.settings, int(user.get('token_version', 0))
        )
        refresh_token = create_refresh_token()
        refresh_expires = datetime.now(UTC) + timedelta(days=self.settings.refresh_token_days)
        self.auth.save_refresh_token(
            user_id,
            hash_refresh_token(refresh_token),
            refresh_expires,
            request.headers.get('user-agent'),
            ip,
            int(user.get('token_version', 0)),
        )
        response = TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=AuthUser(
                id=user_id,
                email=str(user['email']),
                role=role,
                is_active=True,
                must_change_password=bool(user.get('must_change_password', False)),
            ),
        )
        return response, refresh_token, refresh_expires

    def refresh(self, refresh_token: str | None, request: Request) -> tuple[TokenResponse, str, datetime]:
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        token_hash = hash_refresh_token(refresh_token)
        stored = self.auth.consume_refresh_token(token_hash)
        if stored is None:
            reused_id = self.auth.reused_user(token_hash)
            if reused_id:
                self.auth.revoke_all_for_user(reused_id)
                self.users.update(reused_id, {})
                AuditRepository(self.auth.db, self.settings).write(
                    reused_id,
                    '',
                    'auth.refresh.reuse',
                    'user',
                    reused_id,
                    {},
                    getattr(request.state, 'request_id', None),
                )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        user = self.users.get_by_id(str(stored['user_id']))
        if (
            user is None
            or not user.get('is_active', True)
            or stored.get('token_version', 0) != user.get('token_version', 0)
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
        role = Role(str(user['role']))
        user_id = str(user['_id'])
        access_token, expires_at = create_access_token(
            user_id, str(user['email']), role, self.settings, int(user.get('token_version', 0))
        )
        new_refresh = create_refresh_token()
        refresh_expires = datetime.now(UTC) + timedelta(days=self.settings.refresh_token_days)
        ip = request.client.host if request.client else 'unknown'
        self.auth.save_refresh_token(
            user_id,
            hash_refresh_token(new_refresh),
            refresh_expires,
            request.headers.get('user-agent'),
            ip,
            int(user.get('token_version', 0)),
        )
        response = TokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=AuthUser(
                id=user_id,
                email=str(user['email']),
                role=role,
                is_active=True,
                must_change_password=bool(user.get('must_change_password', False)),
            ),
        )
        return response, new_refresh, refresh_expires

    def change_password(self, actor: AuthUser, body: PasswordChange) -> None:
        user = self.users.get_by_id(actor.id)
        if user is None or not verify_password(body.current_password, str(user['password_hash'])):
            raise HTTPException(status_code=400, detail='Current password is incorrect')
        if body.current_password == body.new_password:
            raise HTTPException(status_code=422, detail='Choose a different password')
        self.users.update(
            actor.id,
            {
                'password_hash': hash_password(body.new_password),
                'must_change_password': False,
            },
        )
        self.auth.revoke_all_for_user(actor.id)

    def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            self.auth.revoke_refresh_token(hash_refresh_token(refresh_token))
