from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import require_role
from app.schemas.anomalies import AnomalyListResponse
from app.schemas.auth import AuthUser
from app.schemas.enums import RiskLevel, Role
from app.services.anomaly_service import AnomalyService
from app.services.dependencies import get_anomaly_service

router = APIRouter(prefix='/anomalies', tags=['Anomalies'])


@router.get('', response_model=AnomalyListResponse, summary='List Top-K anomalies for the active model run')
def list_anomalies(
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[AnomalyService, Depends(get_anomaly_service)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 200,
    risk: RiskLevel | None = None,
) -> AnomalyListResponse:
    return service.list(limit, risk.value if risk else None)
