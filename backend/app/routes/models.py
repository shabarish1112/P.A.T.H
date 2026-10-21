from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request, status

from app.core.security import require_role
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.schemas.models import ModelJobResponse, RunRequest
from app.services.audit_service import AuditService
from app.services.dependencies import get_audit_service, get_model_service
from app.services.model_service import ModelService

router = APIRouter(prefix='/models', tags=['Models'])


@router.post(
    '/run',
    response_model=ModelJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary='Queue one anomaly model run',
)
def run_model_job(
    body: RunRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    actor: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[ModelService, Depends(get_model_service)],
    audit: Annotated[AuditService, Depends(get_audit_service)],
) -> ModelJobResponse:
    job = service.start_job(body, actor)
    audit.record(
        actor,
        'model.run.queued',
        'model_job',
        job.job_id,
        body.model_dump(mode='json'),
        request.state.request_id,
    )
    background_tasks.add_task(service.execute_job, job.job_id, body, actor)
    return job


@router.get('/jobs/{job_id}', response_model=ModelJobResponse, summary='Get model-job progress')
def get_model_job(
    job_id: Annotated[str, Path(min_length=16, max_length=64, pattern=r'^[a-f0-9-]+$')],
    _: Annotated[AuthUser, Depends(require_role(Role.analyst, Role.reviewer, Role.admin))],
    service: Annotated[ModelService, Depends(get_model_service)],
) -> ModelJobResponse:
    return service.get_job(job_id)
