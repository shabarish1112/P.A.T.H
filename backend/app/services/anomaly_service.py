from __future__ import annotations

from app.repositories.anomalies import AnomalyRepository
from app.repositories.settings import SettingsRepository
from app.schemas.anomalies import AnomalyListResponse, AnomalyResponse
from app.schemas.enums import RiskLevel


class AnomalyService:
    def __init__(self, repo: AnomalyRepository, settings_repo: SettingsRepository) -> None:
        self.repo = repo
        self.settings_repo = settings_repo

    def list(self, limit: int, risk: str | None) -> AnomalyListResponse:
        run_id = self.settings_repo.get('active_run_id')
        if not run_id:
            return AnomalyListResponse(items=[], active_run_id=None)
        docs = self.repo.list_for_run(run_id, limit, risk)
        return AnomalyListResponse(
            items=[
                AnomalyResponse(
                    id=str(doc['_id']),
                    run_id=str(doc['run_id']),
                    transaction_id=str(doc['transaction_id']),
                    rank=int(doc['rank']),
                    score=float(doc['score']),
                    risk=RiskLevel(str(doc['risk'])),
                    amount_paise=int(doc['amount_paise']),
                    agency=str(doc['agency']),
                    scheme=str(doc['scheme']),
                    vendor=str(doc['vendor']),
                    district=str(doc['district']),
                    path_insight=doc.get('path_insight', {}),
                )
                for doc in docs
            ],
            active_run_id=run_id,
        )
