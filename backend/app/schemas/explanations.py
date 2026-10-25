from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SignalEvidence(BaseModel):
    key: str
    label: str
    value_text: str
    baseline_text: str
    ratio: float | None = None
    multiple_text: str | None = None
    strength: Literal['very_high', 'high', 'elevated', 'normal'] = 'normal'
    tag: str
    help_text: str


class PaymentExplanation(BaseModel):
    headline: str
    support: str | None = None
    check_first: str
    signals: list[SignalEvidence] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    amount_display: str
