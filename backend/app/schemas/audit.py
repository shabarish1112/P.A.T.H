from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, object]
    request_id: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
