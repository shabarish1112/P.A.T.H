from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, Request, Response, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.core.security import get_current_user
from app.repositories.base import get_database
from app.repositories.public import PublicRepository
from app.repositories.users import UserRepository, get_user_repository
from app.schemas.auth import AuthUser
from app.schemas.enums import ModelName
from app.schemas.public import PublicResult
from app.services.public_service import PublicService

router = APIRouter(prefix='/public', tags=['Public analysis'])
optional_bearer = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)
_COOKIE = 'path_guest'


def session_id(request: Request, settings: Settings) -> str | None:
    token = request.cookies.get(_COOKIE)
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={'require': ['exp', 'sub', 'type']},
        )
        if payload.get('type') == 'guest' and isinstance(payload.get('sub'), str):
            return str(payload['sub'])
    except InvalidTokenError:
        pass
    return None


async def optional_user(
    request: Request,
    token: Annotated[str | None, Depends(optional_bearer)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthUser | None:
    if token:
        try:
            return await get_current_user(request, token, users, settings)
        except HTTPException:
            pass
    return None


@router.get('/limits')
def limits(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, int]:
    return {
        'max_upload_mb': min(settings.max_upload_mb, 4),
        'max_rows': min(settings.max_rows, settings.ml_max_rows, 4000),
        'retention_hours': 24,
    }


@router.post('/analyze', response_model=PublicResult, status_code=201)
async def analyze(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File()],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Database[Any], Depends(get_database)],
    user: Annotated[AuthUser | None, Depends(optional_user)],
    model: Annotated[ModelName, Query()] = ModelName.isolation_forest,
) -> PublicResult:
    origin = request.headers.get('origin')
    if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
        raise HTTPException(403, 'Submit uploads from this website.')
    repo = PublicRepository(db)
    repo.consume_limit(
        'analyze', request.client.host if request.client else 'unknown', settings.jwt_secret, 6
    )
    maximum = min(settings.max_upload_mb, 4) * 1024 * 1024
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(422, 'Choose a CSV file.')
    content = await file.read(maximum + 1)
    if len(content) > maximum:
        raise HTTPException(413, 'CSV exceeds the public upload size limit.')
    guest = session_id(request, settings) or secrets.token_hex(32)
    result = await run_in_threadpool(
        PublicService(repo, settings).analyze, content, model, guest, user.id if user else None
    )
    token = jwt.encode(
        {'sub': guest, 'type': 'guest', 'exp': datetime.now(UTC) + timedelta(hours=24)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response.set_cookie(
        _COOKIE,
        token,
        httponly=True,
        secure=settings.environment == 'production',
        samesite='strict',
        max_age=86400,
        path='/api/public',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return result


@router.get('/analyses/{analysis_id}', response_model=PublicResult)
def result(
    analysis_id: Annotated[str, Path(pattern=r'^[a-f0-9]{32}$')],
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Database[Any], Depends(get_database)],
) -> PublicResult:
    guest = session_id(request, settings)
    if not guest:
        raise HTTPException(404, 'Result not found or expired. Upload your CSV again.')
    response.headers['Cache-Control'] = 'private, no-store'
    return PublicResult.model_validate(PublicRepository(db).get(analysis_id, guest))
