from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class ReviewRepository(BaseRepository):
    def latest(self, run_id: str, transaction_id: str) -> dict[str, Any] | None:
        return self.db.reviews.find_one(
            {'run_id': run_id, 'transaction_id': transaction_id},
            sort=[('created_at', -1)],
        )

    def create(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc = {**doc, 'created_at': datetime.now(UTC)}
        result = self.db.reviews.insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc

    def list(self, run_id: str, limit: int = 200) -> list[dict[str, Any]]:
        return list(self.db.reviews.find({'run_id': run_id}).sort('created_at', -1).limit(limit))

    def investigation_yield(self, run_id: str) -> float | None:
        total = self.db.reviews.count_documents({'run_id': run_id})
        if total == 0:
            return None
        findings = self.db.reviews.count_documents({'run_id': run_id, 'status': 'Confirmed Finding'})
        return findings / total


def get_review_repository(db: Annotated[Database[Any], Depends(get_database)]) -> ReviewRepository:
    return ReviewRepository(db)
