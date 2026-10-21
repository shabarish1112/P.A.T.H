from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends
from pymongo import ReturnDocument
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class AuthRepository(BaseRepository):
    def save_refresh_token(
        self, user_id: str, token_hash: str, expires_at: datetime, user_agent: str | None, ip: str
    ) -> None:
        self.db.refresh_tokens.insert_one(
            {
                'user_id': user_id,
                'token_hash': token_hash,
                'expires_at': expires_at,
                'created_at': datetime.now(UTC),
                'revoked_at': None,
                'user_agent': user_agent,
                'ip': ip,
            }
        )

    def get_refresh_token(self, token_hash: str) -> dict[str, Any] | None:
        return self.db.refresh_tokens.find_one({'token_hash': token_hash, 'revoked_at': None})

    def revoke_refresh_token(self, token_hash: str) -> None:
        self.db.refresh_tokens.update_one(
            {'token_hash': token_hash, 'revoked_at': None},
            {'$set': {'revoked_at': datetime.now(UTC)}},
        )

    def revoke_all_for_user(self, user_id: str) -> None:
        self.db.refresh_tokens.update_many(
            {'user_id': user_id, 'revoked_at': None},
            {'$set': {'revoked_at': datetime.now(UTC)}},
        )

    def record_failed_login(self, key: str, window_minutes: int = 15) -> int:
        now = datetime.now(UTC)
        expire_at = now + timedelta(minutes=window_minutes)
        doc = self.db.login_attempts.find_one_and_update(
            {'key': key},
            {
                '$inc': {'failures': 1},
                '$set': {'expire_at': expire_at, 'updated_at': now},
                '$setOnInsert': {'created_at': now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(doc.get('failures', 1)) if doc else 1

    def failures(self, key: str) -> int:
        doc = self.db.login_attempts.find_one({'key': key})
        return int(doc.get('failures', 0)) if doc else 0

    def clear_failures(self, key: str) -> None:
        self.db.login_attempts.delete_one({'key': key})


def get_auth_repository(db: Annotated[Database[Any], Depends(get_database)]) -> AuthRepository:
    return AuthRepository(db)
