from __future__ import annotations

from typing import Any

from pymongo.database import Database

from app.db.mongo import get_db


class BaseRepository:
    def __init__(self, db: Database[Any]) -> None:
        self.db = db


def get_database() -> Database[Any]:
    return get_db()
