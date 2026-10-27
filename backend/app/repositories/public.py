from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.repositories.base import BaseRepository


class PublicRepository(BaseRepository):
    def consume_limit(self, action: str, ip: str, secret: str, maximum: int) -> None:
        now = datetime.now(UTC)
        bucket = int(now.timestamp()) // 3600
        identity = hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()
        key = f'public:{action}:{identity}:{bucket}'
        doc = self.db.login_attempts.find_one_and_update(
            {'key': key},
            {
                '$inc': {'failures': 1},
                '$set': {'updated_at': now},
                '$setOnInsert': {'created_at': now, 'expire_at': now + timedelta(hours=2)},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if doc and doc['failures'] > maximum:
            raise HTTPException(
                429, 'Hourly limit reached. Try again later.', headers={'Retry-After': '3600'}
            )

    def save(self, analysis_id: str, session_id: str, user_id: str | None, result: dict[str, Any]) -> None:
        self.db.public_analyses.insert_one(
            {
                '_id': analysis_id,
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.now(UTC),
                'expire_at': datetime.now(UTC) + timedelta(hours=24),
                'result': result,
            }
        )

    def get(self, analysis_id: str, session_id: str) -> dict[str, Any]:
        doc = self.db.public_analyses.find_one(
            {
                '_id': analysis_id,
                'session_id': session_id,
                'expire_at': {'$gt': datetime.now(UTC)},
            }
        )
        if not doc:
            raise HTTPException(404, 'Result not found or expired. Upload your CSV again.')
        return dict(doc['result'])
