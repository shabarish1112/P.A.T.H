from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.cache import CacheBackend, get_cache
from app.core.config import Settings, get_settings
from app.repositories.anomalies import AnomalyRepository, get_anomaly_repository
from app.repositories.audit import AuditRepository, get_audit_repository
from app.repositories.auth import AuthRepository, get_auth_repository
from app.repositories.datasets import DatasetRepository, get_dataset_repository
from app.repositories.models import ModelRepository, get_model_repository
from app.repositories.reviews import ReviewRepository, get_review_repository
from app.repositories.settings import SettingsRepository, get_settings_repository
from app.repositories.transactions import TransactionRepository, get_transaction_repository
from app.repositories.users import UserRepository, get_user_repository
from app.services.analytics_service import AnalyticsService
from app.services.anomaly_service import AnomalyService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.dataset_service import DatasetService
from app.services.insight_service import InsightService
from app.services.model_service import ModelService
from app.services.review_service import ReviewService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService


def get_insight_service(
    datasets: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    settings: Annotated[SettingsRepository, Depends(get_settings_repository)],
    models: Annotated[ModelRepository, Depends(get_model_repository)],
    anomalies: Annotated[AnomalyRepository, Depends(get_anomaly_repository)],
) -> InsightService:
    return InsightService(datasets, settings, models, anomalies)


def get_cache_dependency(settings: Annotated[Settings, Depends(get_settings)]) -> CacheBackend:
    return get_cache(settings)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    auth: Annotated[AuthRepository, Depends(get_auth_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(users, auth, settings)


def get_audit_service(repo: Annotated[AuditRepository, Depends(get_audit_repository)]) -> AuditService:
    return AuditService(repo)


def get_user_service(repo: Annotated[UserRepository, Depends(get_user_repository)]) -> UserService:
    return UserService(repo)


def get_dataset_service(
    repo: Annotated[DatasetRepository, Depends(get_dataset_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    cache: Annotated[CacheBackend, Depends(get_cache_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DatasetService:
    return DatasetService(repo, settings_repo, cache, settings)


def get_transaction_service(
    repo: Annotated[TransactionRepository, Depends(get_transaction_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> TransactionService:
    return TransactionService(repo, settings_repo)


def get_model_service(
    models: Annotated[ModelRepository, Depends(get_model_repository)],
    transactions: Annotated[TransactionRepository, Depends(get_transaction_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    cache: Annotated[CacheBackend, Depends(get_cache_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelService:
    return ModelService(models, transactions, settings_repo, cache, settings)


def get_anomaly_service(
    repo: Annotated[AnomalyRepository, Depends(get_anomaly_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
) -> AnomalyService:
    return AnomalyService(repo, settings_repo)


def get_review_service(
    repo: Annotated[ReviewRepository, Depends(get_review_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    cache: Annotated[CacheBackend, Depends(get_cache_dependency)],
) -> ReviewService:
    return ReviewService(repo, settings_repo, cache)


def get_analytics_service(
    anomalies: Annotated[AnomalyRepository, Depends(get_anomaly_repository)],
    models: Annotated[ModelRepository, Depends(get_model_repository)],
    reviews: Annotated[ReviewRepository, Depends(get_review_repository)],
    settings_repo: Annotated[SettingsRepository, Depends(get_settings_repository)],
    transactions: Annotated[TransactionRepository, Depends(get_transaction_repository)],
    cache: Annotated[CacheBackend, Depends(get_cache_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnalyticsService:
    return AnalyticsService(anomalies, models, reviews, settings_repo, transactions, cache, settings)
