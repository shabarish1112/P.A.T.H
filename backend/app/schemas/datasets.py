from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    row: int
    reason: str


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows_received: int
    rows_accepted: int
    rows_rejected: int
    issues: list[ValidationIssue]
    activated: bool
    created_at: datetime


class DatasetResponse(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    created_at: datetime
    created_by: str
    is_active: bool


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]


class DatasetDeleteResponse(BaseModel):
    dataset_id: str
    deleted: bool
