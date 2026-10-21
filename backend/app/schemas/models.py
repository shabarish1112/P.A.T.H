from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import ModelName


class RunRequest(BaseModel):
    model: ModelName
    top_k: int = Field(default=50, ge=1, le=5000)
    n_estimators: int = Field(default=200, ge=50, le=1000)
    random_state: int = Field(default=42, ge=0, le=2_147_483_647)
    include_umap: bool = False


class ModelJobResponse(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ModelRunResponse(BaseModel):
    run_id: str
    model: ModelName
    dataset_id: str
    top_k: int
    n_estimators: int
    created_at: datetime
    created_by: str
    metrics: dict[str, float | int | None]
    active: bool


class ModelRunListResponse(BaseModel):
    items: list[ModelRunResponse]
