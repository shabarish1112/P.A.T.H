from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger('path.request')


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get('X-Request-ID', '')
        request_id = supplied if re.fullmatch(r'[A-Za-z0-9._-]{8,64}', supplied) else str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.user_id = None
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers['X-Request-ID'] = request_id
            return response
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                'request_complete',
                extra={
                    'request_id': request_id,
                    'user_id': getattr(request.state, 'user_id', None),
                    'route': request.url.path,
                    'method': request.method,
                    'latency_ms': latency_ms,
                    'status': status_code,
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; form-action 'self'"
        )
        return response
