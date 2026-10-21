from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.core.security import require_role
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.schemas.reviews import ReviewBody, ReviewListResponse, ReviewResponse
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service, get_review_service
from app.services.review_service import ReviewService

router = APIRouter(prefix='/reviews', tags=['Reviews'])


@router.get('', response_model=ReviewListResponse, summary='List reviews for the active run')
def list_reviews(
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[ReviewService, Depends(get_review_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> ReviewListResponse:
    return ReviewListResponse(items=service.list(limit))


@router.put('/{transaction_id}', response_model=ReviewResponse, summary='Record a human validation decision')
def update_review(
    transaction_id: Annotated[str, Path(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9._:-]+$')],
    body: ReviewBody,
    request: Request,
    actor: Annotated[AuthUser, Depends(require_role(Role.reviewer, Role.admin))],
    service: Annotated[ReviewService, Depends(get_review_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ReviewResponse:
    result = service.create(transaction_id, body, actor)
    audit.record(
        actor,
        'review.update',
        'transaction',
        transaction_id,
        {'status': body.status.value},
        request.state.request_id,
    )
    return result
