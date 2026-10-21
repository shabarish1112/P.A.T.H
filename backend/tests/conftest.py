from __future__ import annotations

import os
from datetime import datetime, timezone

os.environ.setdefault('ENVIRONMENT', 'test')
os.environ.setdefault('MONGO_URI', 'mongodb://user:pass@localhost:27017/path_test?authSource=admin')
os.environ.setdefault('MONGO_DB', 'path_test')
os.environ.setdefault('JWT_SECRET', 'test-secret-that-is-long-enough-0123456789abcdef')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:5173')
os.environ.setdefault('DOCS_ENABLED', 'true')

import mongomock
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mongo import reset_db_for_tests
from app.main import app
import app.main as main_module


@pytest.fixture(autouse=True)
def clean_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def db():
    client = mongomock.MongoClient()
    database = client['path_test']
    reset_db_for_tests(database)
    yield database
    client.close()
    reset_db_for_tests(None)


@pytest.fixture()
def client(db, monkeypatch):
    monkeypatch.setattr(main_module, 'initialize_database', lambda: None)
    monkeypatch.setattr(main_module, 'apply_retention', lambda retention_days: None)
    monkeypatch.setattr(main_module, 'ping_database', lambda: True)
    with TestClient(app) as test_client:
        yield test_client


def create_user(db, email: str, role: str, password: str = 'LongTestPassword!123') -> str:
    result = db.users.insert_one(
        {
            'email': email,
            'password_hash': hash_password(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def login(client: TestClient, email: str, password: str = 'LongTestPassword!123') -> tuple[str, dict[str, str]]:
    response = client.post('/api/auth/login', data={'username': email, 'password': password})
    assert response.status_code == 200, response.text
    return response.json()['access_token'], {'Authorization': f"Bearer {response.json()['access_token']}"}
