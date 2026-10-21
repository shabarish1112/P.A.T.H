from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core.pagination import Pagination, pagination_params
from app.core.security import require_role
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.schemas.transactions import TransactionDetailResponse, TransactionListResponse
from app.services.dependencies import get_transaction_service
from app.services.transaction_service import TransactionService

router = APIRouter(prefix='/transactions', tags=['Transactions'])


@router.get(
    '',
    response_model=TransactionListResponse,
    summary='List active-dataset transactions with cursor pagination',
)
def list_transactions(
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    q: Annotated[str | None, Query(max_length=64)] = None,
) -> TransactionListResponse:
    return service.list(pagination.limit, pagination.cursor, q)


@router.get(
    '/{transaction_id}',
    response_model=TransactionDetailResponse,
    summary='Get a transaction and its current anomaly/review context',
)
def transaction_detail(
    transaction_id: Annotated[str, Path(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9._:-]+$')],
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionDetailResponse:
    return service.detail(transaction_id)
