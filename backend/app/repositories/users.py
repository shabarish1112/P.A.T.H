from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from bson import ObjectId
from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class UserRepository(BaseRepository):
    def get_by_email(self, email: str) -> dict[str, Any] | None:
        return self.db.users.find_one({'email': email.lower()})

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None
        return self.db.users.find_one({'_id': ObjectId(user_id)})

    def create(self, email: str, password_hash: str, role: str) -> dict[str, Any]:
        doc = {
            'email': email.lower(),
            'password_hash': password_hash,
            'role': role,
            'is_active': True,
            'created_at': datetime.now(UTC),
        }
        result = self.db.users.insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self.db.users.find().sort('created_at', 1).limit(limit))

    def update(self, user_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        if not ObjectId.is_valid(user_id):
            return None
        self.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': fields, '$inc': {'token_version': 1}})
        return self.get_by_id(user_id)


def get_user_repository(db: Annotated[Database[Any], Depends(get_database)]) -> UserRepository:
    return UserRepository(db)
