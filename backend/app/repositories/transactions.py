from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import timedelta
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

    def explanation_context(self, dataset_id: str, doc: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {}
        for field in ('vendor', 'agency', 'scheme'):
            if not doc.get(field):
                continue
            values = list(
                self.db.transactions.aggregate(
                    [
                        {'$match': {'dataset_id': dataset_id, field: doc[field]}},
                        {'$group': {'_id': None, 'mean': {'$avg': '$amount_paise'}}},
                    ]
                )
            )
            if values:
                context[f'{field}_mean_paise'] = values[0]['mean']
        # Match feature engineering's stable date ordering, including same-day payments.
        first = self.db.transactions.find_one(
            {'dataset_id': dataset_id, 'vendor': doc.get('vendor')},
            sort=[('date', 1), ('_id', 1)],
        )
        if first:
            context['first_payment'] = first['transaction_id'] == doc['transaction_id']
        return context

    def contextual_signals(
        self, dataset_id: str, doc: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, float | int | str]:
        """Calculate payment facts for records outside the saved Top-K; never score them."""
        date = doc['date']
        start_year = date.year if date.month >= 4 else date.year - 1
        fy_start = date.replace(year=start_year, month=4, day=1, hour=0, minute=0, second=0, microsecond=0)
        fy_end = fy_start.replace(year=start_year + 1)
        earlier = {
            '$or': [
                {'date': {'$lt': date}},
                {'date': date, '_id': {'$lt': doc['_id']}},
            ]
        }
        prior = self.db.transactions.find_one(
            {'dataset_id': dataset_id, 'vendor': doc['vendor'], **earlier},
            sort=[('date', -1), ('_id', -1)],
        )
        frequency = self.db.transactions.count_documents(
            {
                'dataset_id': dataset_id,
                'vendor': doc['vendor'],
                'date': {'$gte': date - timedelta(days=30), '$lte': date},
            }
        )
        scheme_year = {
            'dataset_id': dataset_id,
            'scheme': doc['scheme'],
            'date': {'$gte': fy_start, '$lt': fy_end},
        }
        budget_rows = list(
            self.db.transactions.aggregate(
                [
                    {'$match': scheme_year},
                    {'$group': {'_id': None, 'budget': {'$max': '$sanctioned_amount_paise'}}},
                ]
            )
        )
        # Match the stable date/insertion ordering used by feature engineering, including this record.
        spend_rows = list(
            self.db.transactions.aggregate(
                [
                    {
                        '$match': {
                            '$and': [
                                scheme_year,
                                {
                                    '$or': [
                                        {'date': {'$lt': date}},
                                        {'date': date, '_id': {'$lte': doc['_id']}},
                                    ]
                                },
                            ]
                        }
                    },
                    {'$group': {'_id': None, 'spend': {'$sum': '$amount_paise'}}},
                ]
            )
        )
        budget = budget_rows[0].get('budget', 0) if budget_rows else 0
        spend = spend_rows[0]['spend'] if spend_rows else 0
        signals: dict[str, float | int | str] = {
            f'amount_vs_{group}_mean': round(doc['amount_paise'] / max(context[f'{group}_mean_paise'], 1), 3)
            for group in ('vendor', 'agency', 'scheme')
        }
        signals.update(
            {
                'vendor_transactions_30d': frequency,
                'days_since_previous_vendor_payment': max((date - prior['date']).days, 0) if prior else 365,
                'scheme_utilization': round(spend / budget, 4) if budget else 0.0,
                'fiscal_year': f'{start_year}-{str(start_year + 1)[-2:]}',
            }
        )
        return signals

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
