from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Role


class UserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
