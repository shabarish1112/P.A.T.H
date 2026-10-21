from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import ReviewStatus


class ReviewBody(BaseModel):
    status: ReviewStatus
    note: str = Field(default='', max_length=2000)


class ReviewResponse(BaseModel):
    id: str
    transaction_id: str
    run_id: str
    status: ReviewStatus
    note: str
    actor_id: str
    actor_email: str
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
