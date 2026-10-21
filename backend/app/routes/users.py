from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.core.security import require_role
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.schemas.users import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service, get_user_service
from app.services.user_service import UserService

router = APIRouter(prefix='/users', tags=['Users'])


@router.get('', response_model=UserListResponse, summary='List users')
def list_users(
    _: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserListResponse:
    return UserListResponse(items=service.list())


@router.post('', response_model=UserResponse, status_code=201, summary='Create a user')
def create_user(
    body: UserCreate,
    request: Request,
    actor: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> UserResponse:
    result = service.create(body)
    audit.record(
        actor, 'user.create', 'user', result.id, {'role': result.role.value}, request.state.request_id
    )
    return result


@router.patch('/{user_id}', response_model=UserResponse, summary='Update a user role or active state')
def update_user(
    user_id: Annotated[str, Path(min_length=1, max_length=64)],
    body: UserUpdate,
    request: Request,
    actor: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[UserService, Depends(get_user_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> UserResponse:
    result = service.update(user_id, body)
    audit.record(
        actor,
        'user.update',
        'user',
        user_id,
        body.model_dump(exclude_none=True, mode='json'),
        request.state.request_id,
    )
    return result
