from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    role: Role
    is_active: bool
    must_change_password: bool = False


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default='bearer')
    expires_at: datetime
    user: AuthUser


class RefreshResponse(TokenResponse):
    pass


class MeResponse(BaseModel):
    user: AuthUser
