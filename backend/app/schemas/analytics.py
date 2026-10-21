from __future__ import annotations

from pydantic import BaseModel


class DeltaMetric(BaseModel):
    value: float | int
    previous: float | int | None
    delta_percent: float | None


class SummaryResponse(BaseModel):
    total_disbursed_paise: DeltaMetric
    total_transactions: DeltaMetric
    active_anomalies: DeltaMetric
    flagged_volume_paise: DeltaMetric
    review_capacity: int
    active_run_id: str | None


class TrendPoint(BaseModel):
    bucket: str
    current: int
    previous: int


class TrendResponse(BaseModel):
    points: list[TrendPoint]
    current_run_id: str | None
    previous_run_id: str | None


class AnalyticsBreakdownItem(BaseModel):
    name: str
    count: int


class AnalyticsBreakdownResponse(BaseModel):
    items: list[AnalyticsBreakdownItem]
