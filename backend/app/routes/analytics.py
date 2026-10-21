from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.core.security import require_role
from app.schemas.analytics import AnalyticsBreakdownResponse, SummaryResponse, TrendResponse
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.services.analytics_service import AnalyticsService
from app.services.dependencies import get_analytics_service

router = APIRouter(prefix='/analytics', tags=['Analytics'])


def _cache_headers(response: Response, payload: object) -> None:
    raw = json.dumps(payload, default=str, sort_keys=True).encode('utf-8')
    response.headers['ETag'] = f'"{hashlib.sha256(raw).hexdigest()}"'
    response.headers['Cache-Control'] = 'private, max-age=30'


@router.get('/summary', response_model=SummaryResponse, summary='Executive analytics summary')
def summary(
    response: Response,
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> SummaryResponse:
    result = service.summary()
    _cache_headers(response, result.model_dump(mode='json'))
    return result


@router.get(
    '/trend', response_model=TrendResponse, summary='Flagged-count trend for current and previous model runs'
)
def trend(
    response: Response,
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> TrendResponse:
    result = service.trend()
    _cache_headers(response, result.model_dump(mode='json'))
    return result


@router.get(
    '/breakdown',
    response_model=AnalyticsBreakdownResponse,
    summary='Break down active anomalies by dimension',
)
def breakdown(
    response: Response,
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    field: Literal['agency', 'scheme', 'district', 'risk'] = 'agency',
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> AnalyticsBreakdownResponse:
    result = AnalyticsBreakdownResponse(items=service.breakdown(field, limit))
    _cache_headers(response, result.model_dump(mode='json'))
    return result
