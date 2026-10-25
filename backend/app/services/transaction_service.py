from __future__ import annotations

from fastapi import HTTPException

from app.repositories.settings import SettingsRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.transactions import TransactionDetailResponse, TransactionListResponse, TransactionResponse
from app.services.payment_explanation import explain_payment


def _serialize_transaction(doc: dict[str, object]) -> TransactionResponse:
    return TransactionResponse.model_validate({**doc, 'id': str(doc['_id'])})


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
        run_id = self.settings_repo.active_run_id()
        doc = self.repo.detail_with_context(dataset_id, run_id, transaction_id)
        if not doc:
            raise HTTPException(status_code=404, detail='Transaction not found')
        base = _serialize_transaction(doc).model_dump()
        anomaly = doc.get('anomaly') or {}
        review = doc.get('review') or {}
        context = self.repo.explanation_context(dataset_id, doc)
        signals = anomaly.get('path_insight') or self.repo.contextual_signals(dataset_id, doc, context)
        return TransactionDetailResponse(
            **base,
            explanation=explain_payment(
                {**base, 'path_insight': signals},
                context,
                selected_for_review=bool(anomaly),
            ),
            analysis_status='selected' if anomaly else 'not_selected' if run_id else 'not_analyzed',
            total_transactions=self.repo.estimated_count(dataset_id),
            review_actor_email=review.get('actor_email'),
            review_changed_at=review.get('created_at'),
            review_note=review.get('note'),
            anomaly_score=anomaly.get('score'),
            risk=anomaly.get('risk'),
            rank=anomaly.get('rank'),
            review_status=review.get('status'),
            path_insight=signals,
        )
