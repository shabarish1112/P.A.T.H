from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import require_role
from app.schemas.audit import AuditLogListResponse
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service

router = APIRouter(prefix='/audit', tags=['Audit'])


@router.get('', response_model=AuditLogListResponse, summary='Read immutable audit events')
def list_audit_logs(
    _: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> AuditLogListResponse:
    return AuditLogListResponse(items=service.list(limit))
