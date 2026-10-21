from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class SettingsRepository(BaseRepository):
    def get(self, key: str, default: Any = None) -> Any:
        doc = self.db.settings.find_one({'_id': key})
        return doc.get('value', default) if doc else default

    def set(self, key: str, value: Any) -> None:
        self.db.settings.update_one({'_id': key}, {'$set': {'value': value}}, upsert=True)


def get_settings_repository(db: Annotated[Database[Any], Depends(get_database)]) -> SettingsRepository:
    return SettingsRepository(db)
