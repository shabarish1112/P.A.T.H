from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi import Path as ApiPath

from app.core.security import require_role
from app.schemas.auth import AuthUser
from app.schemas.datasets import DatasetDeleteResponse, DatasetListResponse, DatasetUploadResponse
from app.schemas.enums import Role
from app.services.audit_service import AuditService
from app.services.dataset_service import DatasetService
from app.services.dependencies import get_audit_service, get_dataset_service

router = APIRouter(prefix='/datasets', tags=['Datasets'])


@router.post(
    '/upload',
    response_model=DatasetUploadResponse,
    status_code=201,
    summary='Validate and activate a CSV dataset',
)
async def upload_dataset(
    request: Request,
    file: Annotated[UploadFile, File(description='UTF-8 CSV')],
    actor: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
    confirm_replace: Annotated[bool, Query(description='Required when replacing an active dataset')] = False,
) -> DatasetUploadResponse:
    result = await service.upload(file, request, actor, confirm_replace)
    audit.record(
        actor,
        'dataset.upload',
        'dataset',
        result.dataset_id,
        {'filename': result.filename, 'rows': result.rows_accepted},
        request.state.request_id,
    )
    return result


@router.get('', response_model=DatasetListResponse, summary='List datasets')
def list_datasets(
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetListResponse:
    return service.list_datasets()


@router.delete('/{dataset_id}', response_model=DatasetDeleteResponse, summary='Delete an inactive dataset')
def delete_dataset(
    dataset_id: Annotated[str, ApiPath(min_length=16, max_length=64, pattern=r'^[a-f0-9]+$')],
    request: Request,
    actor: Annotated[AuthUser, Depends(require_role(Role.admin))],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> DatasetDeleteResponse:
    result = service.delete_dataset(dataset_id)
    audit.record(actor, 'dataset.delete', 'dataset', dataset_id, {}, request.state.request_id)
    return result
