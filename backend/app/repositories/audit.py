from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.core.config import Settings, get_settings
from app.repositories.base import BaseRepository, get_database


class AuditRepository(BaseRepository):
    def __init__(self, db: Database[Any], settings: Settings) -> None:
        super().__init__(db)
        self.settings = settings

    def write(
        self,
        actor_id: str,
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: str | None,
        details: dict[str, object],
        request_id: str | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        self.db.audit_logs.insert_one(
            {
                'actor_id': actor_id,
                'actor_email': actor_email,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'request_id': request_id,
                'created_at': now,
                'expire_at': now + timedelta(days=self.settings.audit_retention_days),
            }
        )

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self.db.audit_logs.find().sort('created_at', -1).limit(limit))


def get_audit_repository(
    db: Annotated[Database[Any], Depends(get_database)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuditRepository:
    return AuditRepository(db, settings)
