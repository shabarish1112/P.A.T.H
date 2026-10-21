from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class DatasetRepository(BaseRepository):
    def create_dataset(
        self, dataset_id: str, filename: str, row_count: int, created_by: str
    ) -> dict[str, Any]:
        doc = {
            'dataset_id': dataset_id,
            'filename': filename,
            'row_count': row_count,
            'created_at': datetime.now(UTC),
            'created_by': created_by,
            'status': 'staging',
        }
        self.db.datasets.insert_one(doc)
        return doc

    def insert_transactions(self, docs: builtins.list[dict[str, Any]]) -> None:
        if docs:
            self.db.transactions.insert_many(docs, ordered=True)

    def list(self) -> builtins.list[dict[str, Any]]:
        return list(self.db.datasets.find().sort('created_at', -1))

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        return self.db.datasets.find_one({'dataset_id': dataset_id})

    def delete(self, dataset_id: str) -> None:
        self.db.transactions.delete_many({'dataset_id': dataset_id})
        self.db.datasets.delete_one({'dataset_id': dataset_id})

    def existing_transaction_ids(self, dataset_id: str, ids: builtins.list[str]) -> set[str]:
        return {
            str(doc['transaction_id'])
            for doc in self.db.transactions.find(
                {'dataset_id': dataset_id, 'transaction_id': {'$in': ids}},
                {'transaction_id': 1},
            )
        }


def get_dataset_repository(db: Annotated[Database[Any], Depends(get_database)]) -> DatasetRepository:
    return DatasetRepository(db)
