from datetime import datetime

from pydantic import BaseModel

from app.schemas.datasets import ValidationIssue
from app.schemas.enums import ModelName, RiskLevel


class PublicAlert(BaseModel):
    rank: int
    transaction_id: str
    agency: str
    vendor: str
    amount_paise: int
    score: float
    risk: RiskLevel


class PublicResult(BaseModel):
    analysis_id: str
    model: ModelName
    rows_received: int
    rows_accepted: int
    rows_rejected: int
    issues: list[ValidationIssue]
    alerts: list[PublicAlert]
    expires_at: datetime
