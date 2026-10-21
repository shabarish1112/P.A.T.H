from datetime import UTC, datetime, timedelta

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.repositories.base import BaseRepository


class LeaseRepository(BaseRepository):
    def acquire(self, name: str, owner: str, seconds: int) -> bool:
        now = datetime.now(UTC)
        try:
            result = self.db.locks.find_one_and_update(
                {'_id': name, '$or': [{'expires_at': {'$lte': now}}, {'expires_at': {'$exists': False}}]},
                {'$set': {'owner': owner, 'expires_at': now + timedelta(seconds=seconds)}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            return result is not None
        except DuplicateKeyError:
            return False

    def renew(self, name: str, owner: str, seconds: int) -> bool:
        now = datetime.now(UTC)
        result = self.db.locks.update_one(
            {'_id': name, 'owner': owner, 'expires_at': {'$gt': now}},
            {'$set': {'expires_at': now + timedelta(seconds=seconds)}},
        )
        return result.matched_count == 1

    def release(self, name: str, owner: str) -> None:
        self.db.locks.delete_one({'_id': name, 'owner': owner})
