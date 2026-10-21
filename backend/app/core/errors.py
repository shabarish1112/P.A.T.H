from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger('path.error')


def _request_id(request: Request) -> str:
    return getattr(request.state, 'request_id', 'unknown')


def error_payload(code: str, message: str, request_id: str) -> dict[str, dict[str, str]]:
    return {'error': {'code': code, 'message': message, 'request_id': request_id}}


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        return await unhandled_exception_handler(request, exc)
    code = f'HTTP_{exc.status_code}'
    return JSONResponse(
        status_code=exc.status_code, content=error_payload(code, str(exc.detail), _request_id(request))
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)
    return JSONResponse(
        status_code=422,
        content={
            **error_payload('VALIDATION_ERROR', 'Request validation failed', _request_id(request)),
            'details': exc.errors(),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        'unhandled_exception', extra={'request_id': _request_id(request), 'route': request.url.path}
    )
    return JSONResponse(
        status_code=500,
        content=error_payload('INTERNAL_ERROR', 'An unexpected error occurred', _request_id(request)),
    )
