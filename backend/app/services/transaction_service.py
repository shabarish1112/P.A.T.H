from __future__ import annotations

from fastapi import HTTPException

from app.repositories.settings import SettingsRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.transactions import TransactionDetailResponse, TransactionListResponse, TransactionResponse


def _serialize_transaction(doc: dict[str, object]) -> TransactionResponse:
    return TransactionResponse(
        id=str(doc['_id']),
        transaction_id=str(doc['transaction_id']),
        date=doc['date'],
        agency=str(doc['agency']),
        scheme=str(doc['scheme']),
        vendor=str(doc['vendor']),
        district=str(doc['district']),
        amount_paise=int(doc['amount_paise']),
        sanctioned_amount_paise=int(doc.get('sanctioned_amount_paise', 0)),
        payment_type=str(doc.get('payment_type', 'Electronic')),
        reversal_flag=bool(doc.get('reversal_flag', False)),
        cancelled_flag=bool(doc.get('cancelled_flag', False)),
        dataset_id=str(doc['dataset_id']),
    )


class TransactionService:
    def __init__(self, repo: TransactionRepository, settings_repo: SettingsRepository) -> None:
        self.repo = repo
        self.settings_repo = settings_repo

    def list(self, limit: int, cursor: str | None, query: str | None) -> TransactionListResponse:
        dataset_id = self.settings_repo.get('active_dataset_id')
        if not dataset_id:
            return TransactionListResponse(items=[], next_cursor=None, estimated_total=0)
        docs, next_cursor = self.repo.list_keyset(dataset_id, limit, cursor, query)
        return TransactionListResponse(
            items=[_serialize_transaction(doc) for doc in docs],
            next_cursor=next_cursor,
            estimated_total=self.repo.estimated_count(dataset_id),
        )

    def detail(self, transaction_id: str) -> TransactionDetailResponse:
        dataset_id = self.settings_repo.get('active_dataset_id')
        if not dataset_id:
            raise HTTPException(status_code=404, detail='No active dataset')
        run_id = self.settings_repo.get('active_run_id')
        doc = self.repo.detail_with_context(dataset_id, run_id, transaction_id)
        if not doc:
            raise HTTPException(status_code=404, detail='Transaction not found')
        base = _serialize_transaction(doc).model_dump()
        anomaly = doc.get('anomaly') or {}
        review = doc.get('review') or {}
        return TransactionDetailResponse(
            **base,
            anomaly_score=anomaly.get('score'),
            risk=anomaly.get('risk'),
            rank=anomaly.get('rank'),
            review_status=review.get('status'),
            path_insight=anomaly.get('path_insight'),
        )
