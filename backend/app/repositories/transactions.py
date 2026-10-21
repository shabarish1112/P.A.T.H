from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Annotated, Any

from bson import ObjectId
from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class TransactionRepository(BaseRepository):
    def exceeds_row_limit(self, dataset_id: str, limit: int) -> bool:
        return self.db.transactions.count_documents({'dataset_id': dataset_id}, limit=limit + 1) > limit

    def list_keyset(
        self,
        dataset_id: str,
        limit: int,
        cursor: str | None,
        query: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        filt: dict[str, Any] = {'dataset_id': dataset_id}
        if cursor:
            if not ObjectId.is_valid(cursor):
                return [], None
            filt['_id'] = {'$gt': ObjectId(cursor)}
        if query:
            normalized = query.strip().lower()
            escaped = re.escape(normalized)
            filt['search_key'] = {'$regex': f'^{escaped}'}
        docs = list(self.db.transactions.find(filt).sort('_id', 1).limit(limit + 1))
        next_cursor = str(docs[limit - 1]['_id']) if len(docs) > limit else None
        return docs[:limit], next_cursor

    def estimated_count(self, dataset_id: str) -> int:
        dataset = self.db.datasets.find_one({'dataset_id': dataset_id}, {'row_count': 1})
        return int(dataset.get('row_count', 0)) if dataset else 0

    def get_by_transaction_id(self, dataset_id: str, transaction_id: str) -> dict[str, Any] | None:
        return self.db.transactions.find_one({'dataset_id': dataset_id, 'transaction_id': transaction_id})

    def sum_amount_paise(self, dataset_id: str) -> int:
        rows = list(
            self.db.transactions.aggregate(
                [
                    {'$match': {'dataset_id': dataset_id}},
                    {'$group': {'_id': None, 'total': {'$sum': '$amount_paise'}}},
                ]
            )
        )
        return int(rows[0]['total']) if rows else 0

    def iter_for_dataset(self, dataset_id: str, limit: int) -> Iterator[dict[str, Any]]:
        yield from (
            self.db.transactions.find({'dataset_id': dataset_id}).sort('_id', 1).limit(limit).batch_size(500)
        )

    def get_all_for_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        return list(self.db.transactions.find({'dataset_id': dataset_id}).sort('_id', 1))

    def detail_with_context(
        self, dataset_id: str, run_id: str | None, transaction_id: str
    ) -> dict[str, Any] | None:
        doc = self.db.transactions.find_one({'dataset_id': dataset_id, 'transaction_id': transaction_id})
        if doc is None:
            return None
        doc['anomaly'] = (
            self.db.anomalies.find_one(
                {'dataset_id': dataset_id, 'run_id': run_id, 'transaction_id': transaction_id}
            )
            if run_id
            else None
        )
        doc['review'] = (
            self.db.reviews.find_one(
                {'run_id': run_id, 'transaction_id': transaction_id}, sort=[('created_at', -1)]
            )
            if run_id
            else None
        )
        return doc


def get_transaction_repository(db: Annotated[Database[Any], Depends(get_database)]) -> TransactionRepository:
    return TransactionRepository(db)
