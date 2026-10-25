from __future__ import annotations

from pydantic import BaseModel

from app.schemas.enums import RiskLevel
from app.schemas.explanations import PaymentExplanation


class AnomalyResponse(BaseModel):
    explanation: PaymentExplanation | None = None
    id: str
    run_id: str
    transaction_id: str
    rank: int
    score: float
    risk: RiskLevel
    amount_paise: int
    agency: str
    scheme: str
    vendor: str
    district: str
    path_insight: dict[str, float | int | str]


class AnomalyListResponse(BaseModel):
    items: list[AnomalyResponse]
    active_run_id: str | None
