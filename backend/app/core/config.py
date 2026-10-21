from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'P.A.T.H. API'
    environment: Literal['development', 'test', 'production'] = 'development'
    api_prefix: str = '/api'
    docs_enabled: bool = True

    mongo_uri: str
    mongo_db: str = 'path'

    jwt_secret: str
    jwt_algorithm: Literal['HS256', 'HS384', 'HS512'] = 'HS256'
    access_token_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=30)

    cors_origins: str = 'http://localhost:5173'
    cors_methods: str = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    cors_headers: str = 'Authorization,Content-Type,X-Request-ID'
    max_upload_mb: int = Field(default=25, ge=1, le=250)
    max_rows: int = Field(default=100000, ge=1, le=1000000)
    ml_max_rows: int = Field(default=50000, ge=2, le=1000000)
    model_lock_seconds: int = Field(default=300, ge=30, le=3600)
    host: str = '127.0.0.1'
    workers: int = Field(default=1, ge=1, le=16)
    forwarded_allow_ips: str = '127.0.0.1'
    data_retention_days: int = Field(default=365, ge=30, le=3650)
    audit_retention_days: int = Field(default=365, ge=30, le=3650)

    cache_backend: Literal['memory', 'redis'] = 'memory'
    cache_ttl_seconds: int = Field(default=30, ge=1, le=3600)
    redis_url: str | None = None

    ml_n_jobs: int = Field(default=1, ge=1, le=8)
    ml_umap_max_rows: int = Field(default=5000, ge=100, le=20000)

    mongo_tls_ca_file: str | None = None
    mongo_tls_cert_key_file: str | None = None

    @field_validator('mongo_uri')
    @classmethod
    def validate_mongo_uri(cls, value: str) -> str:
        if not value.startswith(('mongodb://', 'mongodb+srv://')):
            raise ValueError('MONGO_URI must be a MongoDB connection URI')
        if '@' not in value:
            raise ValueError('MONGO_URI must include authentication credentials')
        return value

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters')
        if value.lower().startswith(('change-me', 'replace-me', 'secret')):
            raise ValueError('JWT_SECRET must not use an example/default value')
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]

    @property
    def cors_method_list(self) -> list[str]:
        return [item.strip().upper() for item in self.cors_methods.split(',') if item.strip()]

    @property
    def cors_header_list(self) -> list[str]:
        return [item.strip() for item in self.cors_headers.split(',') if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
