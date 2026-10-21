from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import RiskLevel


class CsvTransactionRow(BaseModel):
    transaction_id: str = Field(pattern=r'^[A-Za-z0-9._:-]{1,64}$')
    date: datetime
    agency: str = Field(min_length=1, max_length=120)
    scheme: str = Field(min_length=1, max_length=160)
    vendor: str = Field(min_length=1, max_length=160)
    district: str = Field(min_length=1, max_length=120)
    amount: float = Field(ge=0)
    sanctioned_amount: float = Field(ge=0)
    payment_type: str = Field(default='Electronic', min_length=1, max_length=80)
    reversal_flag: bool = False
    cancelled_flag: bool = False
    injected_anomaly: bool | None = None

    @field_validator('agency', 'scheme', 'vendor', 'district', 'payment_type')
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator('amount', 'sanctioned_amount')
    @classmethod
    def finite_money(cls, value: float) -> float:
        if value != value or value in (float('inf'), float('-inf')):
            raise ValueError('must be finite')
        return value


class TransactionResponse(BaseModel):
    id: str
    transaction_id: str
    date: datetime
    agency: str
    scheme: str
    vendor: str
    district: str
    amount_paise: int
    sanctioned_amount_paise: int
    payment_type: str
    reversal_flag: bool
    cancelled_flag: bool
    dataset_id: str


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    next_cursor: str | None = None
    estimated_total: int | None = None


class TransactionDetailResponse(TransactionResponse):
    anomaly_score: float | None = None
    risk: RiskLevel | None = None
    rank: int | None = None
    review_status: str | None = None
    path_insight: dict[str, float | int | str] | None = None
