from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class ErrorItem(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorItem


class PaginationResponse(BaseModel):
    next_cursor: str | None = None
    estimated_total: int | None = None


class AuditFields(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None


class MongoModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
