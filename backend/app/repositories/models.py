from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Depends
from pymongo.errors import DuplicateKeyError
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class ModelRepository(BaseRepository):
    def acquire_lock(self, job_id: str) -> bool:
        try:
            self.db.locks.insert_one({'_id': 'model_run', 'job_id': job_id, 'created_at': datetime.now(timezone.utc)})
            return True
        except DuplicateKeyError:
            return False

    def release_lock(self, job_id: str) -> None:
        self.db.locks.delete_one({'_id': 'model_run', 'job_id': job_id})

    def create_job(self, job_id: str, actor_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        doc = {
            'job_id': job_id,
            'status': 'queued',
            'progress': 0,
            'message': 'Queued',
            'run_id': None,
            'created_at': now,
            'updated_at': now,
            'actor_id': actor_id,
        }
        self.db.jobs.insert_one(doc)
        return doc

    def update_job(self, job_id: str, **fields: Any) -> None:
        fields['updated_at'] = datetime.now(timezone.utc)
        self.db.jobs.update_one({'job_id': job_id}, {'$set': fields})

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.db.jobs.find_one({'job_id': job_id})

    def insert_run(self, run_doc: dict[str, Any]) -> None:
        self.db.model_runs.insert_one(run_doc)

    def insert_anomalies(self, anomalies: list[dict[str, Any]]) -> None:
        if anomalies:
            self.db.anomalies.insert_many(anomalies, ordered=True)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self.db.model_runs.find().sort('created_at', -1).limit(limit))

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.db.model_runs.find_one({'run_id': run_id})

    def previous_run(self, current_run_id: str) -> dict[str, Any] | None:
        current = self.get_run(current_run_id)
        if not current:
            return None
        return self.db.model_runs.find_one(
            {'created_at': {'$lt': current['created_at']}},
            sort=[('created_at', -1)],
        )


def get_model_repository(db: Annotated[Database[Any], Depends(get_database)]) -> ModelRepository:
    return ModelRepository(db)
