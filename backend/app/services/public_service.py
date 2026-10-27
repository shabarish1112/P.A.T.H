from __future__ import annotations

import csv
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

from app.core.config import Settings
from app.ml.engine import run_model
from app.ml.features import engineer_features
from app.repositories.leases import LeaseRepository
from app.repositories.public import PublicRepository
from app.schemas.enums import ModelName
from app.schemas.public import PublicAlert, PublicResult
from app.services.dataset_service import validate_csv_rows


class PublicService:
    def __init__(self, repo: PublicRepository, settings: Settings) -> None:
        self.repo = repo
        self.settings = settings

    def analyze(self, content: bytes, model: ModelName, session_id: str, user_id: str | None) -> PublicResult:
        try:
            text = content.decode('utf-8-sig')
            rows, total, issues = validate_csv_rows(
                text, min(self.settings.max_rows, self.settings.ml_max_rows, 4000)
            )
        except (UnicodeDecodeError, csv.Error) as exc:
            raise HTTPException(422, 'Upload a valid UTF-8 CSV file.') from exc
        if len(rows) < 2:
            raise HTTPException(422, 'At least two valid transaction rows are required.')
        owner = secrets.token_hex(16)
        leases = LeaseRepository(self.repo.db)
        if not leases.acquire('public_analysis', owner, 300):
            raise HTTPException(
                429, 'Another public analysis is running. Retry shortly.', headers={'Retry-After': '30'}
            )
        try:
            matrix, _ = engineer_features(rows)
            result = run_model(matrix, model, min(50, len(rows)), 100, 42, 1, include_umap=False)
            alerts = [
                PublicAlert(
                    rank=rank,
                    transaction_id=str(rows[int(index)]['transaction_id']),
                    agency=str(rows[int(index)]['agency']),
                    vendor=str(rows[int(index)]['vendor']),
                    amount_paise=int(str(rows[int(index)]['amount_paise'])),
                    score=float(result.scores[int(index)]),
                    risk=result.risks[int(index)],
                )
                for rank, index in enumerate(result.ranking[:50], start=1)
            ]
            response = PublicResult(
                analysis_id=secrets.token_hex(16),
                model=model,
                rows_received=total,
                rows_accepted=len(rows),
                rows_rejected=total - len(rows),
                issues=issues,
                alerts=alerts,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
            self.repo.save(response.analysis_id, session_id, user_id, response.model_dump(mode='json'))
            return response
        finally:
            leases.release('public_analysis', owner)
