from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import get_current_user
from app.schemas.auth import (
    AuthUser,
    LoginRequest,
    MeResponse,
    PasswordChange,
    RefreshResponse,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.dependencies import get_audit_service, get_auth_service

router = APIRouter(prefix='/auth', tags=['Authentication'])
_COOKIE_NAME = 'path_refresh'


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        _COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite='strict',
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path='/api/auth',
    )


@router.post(
    '/login',
    response_model=TokenResponse,
    summary='Authenticate a user',
    responses={
        401: {'description': 'Invalid credentials'},
        429: {'description': 'Login rate limit exceeded'},
    },
)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    try:
        body = LoginRequest(email=form.username, password=form.password)
    except ValidationError as exc:
        raise HTTPException(status_code=401, detail='Invalid email or password') from exc
    token_response, refresh_token, _ = service.login(body, request)
    _set_refresh_cookie(response, refresh_token, settings)
    return token_response


@router.post(
    '/refresh',
    response_model=RefreshResponse,
    summary='Rotate a refresh token and issue a new access token',
    responses={401: {'description': 'Invalid or expired refresh token'}},
)
def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
) -> RefreshResponse:
    token_response, new_refresh, _ = service.refresh(refresh_token, request)
    _set_refresh_cookie(response, new_refresh, settings)
    return RefreshResponse(**token_response.model_dump())


@router.post('/logout', response_model=MessageResponse, summary='Revoke the current refresh token')
def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[AuthUser, Depends(get_current_user)],
    refresh_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
) -> MessageResponse:
    service.logout(refresh_token)
    response.delete_cookie(_COOKIE_NAME, path='/api/auth')
    return MessageResponse(message='Logged out')


@router.get('/me', response_model=MeResponse, summary='Return the validated authenticated session')
def me(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(user=current_user)


@router.post('/change-password', response_model=MessageResponse)
def change_password(
    body: PasswordChange,
    request: Request,
    response: Response,
    actor: Annotated[AuthUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> MessageResponse:
    service.change_password(actor, body)
    audit.record(actor, 'auth.password.change', 'user', actor.id, {}, request.state.request_id)
    response.delete_cookie(_COOKIE_NAME, path='/api/auth')
    return MessageResponse(message='Password changed; sign in again')
