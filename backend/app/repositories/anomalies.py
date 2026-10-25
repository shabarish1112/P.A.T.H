from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from app.repositories.base import BaseRepository, get_database


class AnomalyRepository(BaseRepository):
    def list_for_run(self, run_id: str, limit: int, risk: str | None = None) -> list[dict[str, Any]]:
        filt: dict[str, Any] = {'run_id': run_id}
        if risk:
            filt['risk'] = risk
        return list(self.db.anomalies.find(filt).sort('rank', 1).limit(limit))

    def count_for_run(self, run_id: str, risk: str | None = None) -> int:
        filt = {'run_id': run_id}
        if risk:
            filt['risk'] = risk
        return self.db.anomalies.count_documents(filt)

    def sum_flagged_volume(self, run_id: str) -> int:
        result = list(
            self.db.anomalies.aggregate(
                [
                    {'$match': {'run_id': run_id}},
                    {'$group': {'_id': None, 'total': {'$sum': '$amount_paise'}}},
                ]
            )
        )
        return int(result[0]['total']) if result else 0

    def trend_by_month(self, run_id: str, dataset_id: str) -> dict[str, int]:
        pipeline: list[dict[str, object]] = [
            {'$match': {'run_id': run_id}},
            {
                '$lookup': {
                    'from': 'transactions',
                    'let': {'txid': '$transaction_id'},
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$and': [
                                        {'$eq': ['$transaction_id', '$$txid']},
                                        {'$eq': ['$dataset_id', dataset_id]},
                                    ]
                                }
                            }
                        },
                        {'$project': {'date': 1}},
                    ],
                    'as': 'tx',
                }
            },
            {'$set': {'tx': {'$first': '$tx'}}},
            {'$match': {'tx.date': {'$ne': None}}},
            {
                '$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$tx.date'}},
                    'count': {'$sum': 1},
                }
            },
            {'$sort': {'_id': 1}},
        ]
        return {str(item['_id']): int(item['count']) for item in self.db.anomalies.aggregate(pipeline)}

    def breakdown(self, run_id: str, field: str, limit: int = 10) -> list[dict[str, Any]]:
        if field not in {'agency', 'scheme', 'district', 'risk'}:
            raise ValueError('Unsupported breakdown field')
        pipeline: list[dict[str, object]] = [
            {'$match': {'run_id': run_id}},
            {'$group': {'_id': f'${field}', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1, '_id': 1}},
            {'$limit': limit},
        ]
        return list(self.db.anomalies.aggregate(pipeline))


def get_anomaly_repository(db: Annotated[Database[Any], Depends(get_database)]) -> AnomalyRepository:
    return AnomalyRepository(db)
