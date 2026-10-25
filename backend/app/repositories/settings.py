from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class SettingsRepository(BaseRepository):
    def active_run_id(self) -> str | None:
        """Never attach results from an older dataset to the current upload."""
        run_id = self.get('active_run_id')
        dataset_id = self.get('active_dataset_id')
        if not run_id or not dataset_id:
            return None
        run = self.db.model_runs.find_one({'run_id': run_id, 'dataset_id': dataset_id}, {'_id': 1})
        return str(run_id) if run else None

    def get(self, key: str, default: Any = None) -> Any:
        doc = self.db.settings.find_one({'_id': key})
        return doc.get('value', default) if doc else default

    def set(self, key: str, value: Any) -> None:
        self.db.settings.update_one({'_id': key}, {'$set': {'value': value}}, upsert=True)


def get_settings_repository(db: Annotated[Database[Any], Depends(get_database)]) -> SettingsRepository:
    return SettingsRepository(db)
