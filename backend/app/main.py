from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.errors import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.db.mongo import apply_retention, initialize_database, ping_database
from app.routes import analytics, anomalies, audit, auth, datasets, models, reviews, transactions, users
from app.schemas.common import MessageResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    initialize_database()
    apply_retention(retention_days=settings.data_retention_days)
    yield


settings = get_settings()
app = FastAPI(
    title='P.A.T.H. API',
    version='1.0.0',
    description=(
        'Public Anomaly Tracking Hub. An anomaly-screening layer above authoritative public-finance systems. '
        'Unusual != Fraudulent.'
    ),
    docs_url='/docs' if settings.docs_enabled and settings.environment != 'production' else None,
    redoc_url=None,
    openapi_url='/openapi.json' if settings.docs_enabled and settings.environment != 'production' else None,
    lifespan=lifespan,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=settings.cors_method_list,
    allow_headers=settings.cors_header_list,
    expose_headers=['ETag', 'X-Request-ID'],
)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get('/health', response_model=MessageResponse, tags=['Health'], summary='Compatibility health check')
def health() -> MessageResponse:
    return MessageResponse(message='ok')


@app.get('/health/live', response_model=MessageResponse, tags=['Health'], summary='Liveness check')
def health_live() -> MessageResponse:
    return MessageResponse(message='live')


@app.get('/health/ready', response_model=MessageResponse, tags=['Health'], summary='Readiness check')
def health_ready() -> MessageResponse:
    ping_database()
    return MessageResponse(message='ready')




def custom_openapi() -> dict[str, object]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    standard_errors = {
        '401': {'description': 'Authentication required or token invalid'},
        '403': {'description': 'Authenticated role is not permitted'},
        '404': {'description': 'Resource not found'},
        '409': {'description': 'State conflict'},
        '422': {'description': 'Request validation failed'},
        '429': {'description': 'Rate limit exceeded'},
    }
    for path, methods in schema.get('paths', {}).items():
        if path.startswith('/health') or path in {'/api/auth/login', '/api/auth/refresh'}:
            continue
        for operation in methods.values():
            if isinstance(operation, dict) and 'responses' in operation:
                for code, response in standard_errors.items():
                    operation['responses'].setdefault(code, response)
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

for router in (
    auth.router,
    users.router,
    datasets.router,
    transactions.router,
    models.router,
    anomalies.router,
    analytics.router,
    reviews.router,
    audit.router,
):
    app.include_router(router, prefix=settings.api_prefix)
