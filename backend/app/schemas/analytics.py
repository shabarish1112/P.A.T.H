from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.explanations import PaymentExplanation


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


class CriticalFinding(BaseModel):
    explanation: PaymentExplanation | None = None
    priority: str = 'Critical'
    transaction_id: str
    amount_paise: int
    agency: str
    vendor: str
    score: float
    signals: list[str]
    check: str = ''
    amount_display: str = ''


class AnalysisInsightsResponse(BaseModel):
    status: Literal['no_dataset', 'not_analyzed', 'ready']
    dataset_id: str | None = None
    dataset_name: str | None = None
    run_id: str | None = None
    transaction_count: int = 0
    flagged_count: int = 0
    critical_count: int = 0
    narrative: str
    critical_records: list[CriticalFinding] = Field(default_factory=list)
