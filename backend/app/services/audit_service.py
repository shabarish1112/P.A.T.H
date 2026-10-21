from __future__ import annotations

from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogResponse
from app.schemas.auth import AuthUser


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        self.repo = repo

    def list(self, limit: int) -> list[AuditLogResponse]:
        return [
            AuditLogResponse(
                id=str(doc['_id']),
                actor_id=str(doc['actor_id']),
                actor_email=str(doc['actor_email']),
                action=str(doc['action']),
                resource_type=str(doc['resource_type']),
                resource_id=doc.get('resource_id'),
                details=doc.get('details', {}),
                request_id=doc.get('request_id'),
                created_at=doc['created_at'],
            )
            for doc in self.repo.list(limit)
        ]

    def record(
        self,
        user: AuthUser,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict[str, object],
        request_id: str | None,
    ) -> None:
        self.repo.write(user.id, user.email, action, resource_type, resource_id, details, request_id)
