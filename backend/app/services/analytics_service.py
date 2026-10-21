from __future__ import annotations

from app.core.cache import CacheBackend, cache_miss
from app.core.config import Settings
from app.repositories.anomalies import AnomalyRepository
from app.repositories.models import ModelRepository
from app.repositories.reviews import ReviewRepository
from app.repositories.settings import SettingsRepository
from app.repositories.transactions import TransactionRepository
from app.schemas.analytics import AnalyticsBreakdownItem, DeltaMetric, SummaryResponse, TrendPoint, TrendResponse


def _delta(current: float | int, previous: float | int | None) -> DeltaMetric:
    delta = None
    if previous not in (None, 0):
        delta = round(((float(current) - float(previous)) / abs(float(previous))) * 100.0, 2)
    return DeltaMetric(value=current, previous=previous, delta_percent=delta)


class AnalyticsService:
    def __init__(
        self,
        anomalies: AnomalyRepository,
        models: ModelRepository,
        reviews: ReviewRepository,
        settings_repo: SettingsRepository,
        transactions: TransactionRepository,
        cache: CacheBackend,
        settings: Settings,
    ) -> None:
        self.anomalies = anomalies
        self.models = models
        self.reviews = reviews
        self.settings_repo = settings_repo
        self.transactions = transactions
        self.cache = cache
        self.settings = settings

    def summary(self) -> SummaryResponse:
        run_id = self.settings_repo.get('active_run_id')
        dataset_id = self.settings_repo.get('active_dataset_id')
        cache_key = f'analytics:summary:{run_id}:{dataset_id}'
        cached = self.cache.get(cache_key)
        if cached is not cache_miss():
            return SummaryResponse.model_validate(cached)
        current_run = self.models.get_run(run_id) if run_id else None
        previous_run = self.models.previous_run(run_id) if run_id else None
        current_count = self.anomalies.count_for_run(run_id) if run_id else 0
        previous_count = self.anomalies.count_for_run(previous_run['run_id']) if previous_run else None
        current_flagged = self.anomalies.sum_flagged_volume(run_id) if run_id else 0
        previous_flagged = self.anomalies.sum_flagged_volume(previous_run['run_id']) if previous_run else None
        total_transactions = self.transactions.estimated_count(dataset_id) if dataset_id else 0
        previous_dataset_id = previous_run.get('dataset_id') if previous_run else None
        previous_total = self.transactions.estimated_count(previous_dataset_id) if previous_dataset_id else None
        total_disbursed = self.transactions.sum_amount_paise(dataset_id) if dataset_id else 0
        previous_disbursed = self.transactions.sum_amount_paise(previous_dataset_id) if previous_dataset_id else None
        response = SummaryResponse(
            total_disbursed_paise=_delta(total_disbursed, previous_disbursed),
            total_transactions=_delta(total_transactions, previous_total),
            active_anomalies=_delta(current_count, previous_count),
            flagged_volume_paise=_delta(current_flagged, previous_flagged),
            review_capacity=int(current_run.get('top_k', 0)) if current_run else 0,
            active_run_id=run_id,
        )
        self.cache.set(cache_key, response.model_dump(mode='json'), self.settings.cache_ttl_seconds)
        return response

    def trend(self) -> TrendResponse:
        run_id = self.settings_repo.get('active_run_id')
        if not run_id:
            return TrendResponse(points=[], current_run_id=None, previous_run_id=None)
        current = self.models.get_run(run_id)
        previous = self.models.previous_run(run_id)
        current_map = self.anomalies.trend_by_month(run_id, current['dataset_id']) if current else {}
        previous_map = self.anomalies.trend_by_month(previous['run_id'], previous['dataset_id']) if previous else {}
        buckets = sorted(set(current_map) | set(previous_map))
        return TrendResponse(
            points=[TrendPoint(bucket=bucket, current=current_map.get(bucket, 0), previous=previous_map.get(bucket, 0)) for bucket in buckets],
            current_run_id=run_id,
            previous_run_id=previous['run_id'] if previous else None,
        )

    def breakdown(self, field: str, limit: int) -> list[AnalyticsBreakdownItem]:
        run_id = self.settings_repo.get('active_run_id')
        if not run_id:
            return []
        return [AnalyticsBreakdownItem(name=str(item['_id']), count=int(item['count'])) for item in self.anomalies.breakdown(run_id, field, limit)]
