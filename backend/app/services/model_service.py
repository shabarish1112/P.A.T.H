from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
from fastapi import HTTPException, status

from app.core.cache import CacheBackend
from app.core.config import Settings
from app.ml.engine import run_model
from app.ml.features import engineer_features
from app.repositories.models import ModelRepository
from app.repositories.settings import SettingsRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.auth import AuthUser
from app.schemas.models import ModelJobResponse, RunRequest

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(
        self,
        models: ModelRepository,
        transactions: TransactionRepository,
        settings_repo: SettingsRepository,
        cache: CacheBackend,
        settings: Settings,
    ) -> None:
        self.models = models
        self.transactions = transactions
        self.settings_repo = settings_repo
        self.cache = cache
        self.settings = settings

    def start_job(self, body: RunRequest, actor: AuthUser) -> ModelJobResponse:
        dataset_id = self.settings_repo.get('active_dataset_id')
        if not dataset_id:
            raise HTTPException(status_code=409, detail='No active dataset')
        job_id = uuid.uuid4().hex
        if not self.models.acquire_lock(job_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A model run is already in progress')
        doc = self.models.create_job(job_id, actor.id)
        return self._serialize_job(doc)

    def execute_job(self, job_id: str, body: RunRequest, actor: AuthUser) -> None:
        try:
            self.models.update_job(job_id, status='running', progress=5, message='Loading transactions')
            dataset_id = self.settings_repo.get('active_dataset_id')
            rows = self.transactions.get_all_for_dataset(dataset_id)
            if len(rows) < 2:
                raise ValueError('At least two transactions are required')
            self.models.update_job(job_id, progress=20, message='Engineering contextual features')
            matrix, insights = engineer_features(rows)
            labels = np.array([1 if row.get('injected_anomaly') is True else 0 for row in rows], dtype=int)
            if labels.sum() == 0:
                labels = None
            self.models.update_job(job_id, progress=40, message='Running anomaly model')
            result = run_model(
                matrix,
                body.model,
                body.top_k,
                body.n_estimators,
                body.random_state,
                self.settings.ml_n_jobs,
                labels=labels,
                include_umap=body.include_umap,
                umap_max_rows=self.settings.ml_umap_max_rows,
            )
            run_id = uuid.uuid4().hex
            now = datetime.now(timezone.utc)
            top_count = min(body.top_k, len(rows))
            anomalies: list[dict[str, Any]] = []
            for rank_position, row_index in enumerate(result.ranking[:top_count], start=1):
                row = rows[int(row_index)]
                anomalies.append(
                    {
                        'run_id': run_id,
                        'dataset_id': dataset_id,
                        'transaction_id': str(row['transaction_id']),
                        'rank': rank_position,
                        'score': float(result.scores[row_index]),
                        'risk': result.risks[row_index].value,
                        'amount_paise': int(row['amount_paise']),
                        'agency': str(row['agency']),
                        'scheme': str(row['scheme']),
                        'vendor': str(row['vendor']),
                        'district': str(row['district']),
                        'path_insight': insights[row_index],
                        'pca': [float(value) for value in result.pca[row_index]],
                    }
                )
            run_doc = {
                'run_id': run_id,
                'model': body.model.value,
                'dataset_id': dataset_id,
                'top_k': top_count,
                'n_estimators': body.n_estimators,
                'random_state': body.random_state,
                'include_umap': body.include_umap,
                'metrics': result.metrics,
                'umap': result.umap.tolist() if result.umap is not None else None,
                'created_at': now,
                'created_by': actor.id,
            }
            self.models.update_job(job_id, progress=80, message='Writing results atomically')
            self.models.insert_run(run_doc)
            self.models.insert_anomalies(anomalies)
            self.settings_repo.set('active_run_id', run_id)
            self.cache.invalidate('analytics:')
            self.cache.invalidate('anomalies:')
            self.models.update_job(job_id, status='completed', progress=100, message='Completed', run_id=run_id)
        except Exception:
            logger.exception('model_job_failed', extra={'job_id': job_id, 'actor_id': actor.id})
            self.models.update_job(job_id, status='failed', progress=100, message='Model run failed. Check server logs with the job id.')
        finally:
            self.models.release_lock(job_id)

    def get_job(self, job_id: str) -> ModelJobResponse:
        doc = self.models.get_job(job_id)
        if not doc:
            raise HTTPException(status_code=404, detail='Job not found')
        return self._serialize_job(doc)

    @staticmethod
    def _serialize_job(doc: dict[str, Any]) -> ModelJobResponse:
        return ModelJobResponse(
            job_id=str(doc['job_id']),
            status=str(doc['status']),
            progress=int(doc['progress']),
            message=str(doc['message']),
            run_id=doc.get('run_id'),
            created_at=doc['created_at'],
            updated_at=doc['updated_at'],
        )
