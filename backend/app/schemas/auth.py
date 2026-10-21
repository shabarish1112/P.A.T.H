from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    role: Role
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default='bearer')
    expires_at: datetime
    user: AuthUser


class RefreshResponse(TokenResponse):
    pass


class MeResponse(BaseModel):
    user: AuthUser
