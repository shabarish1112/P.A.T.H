from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pymongo.database import Database

from app.core.config import get_settings
from app.core.time import as_utc
from app.db.mongo import apply_retention
from app.repositories.leases import LeaseRepository
from app.repositories.models import ModelRepository
from app.repositories.settings import SettingsRepository
from app.schemas.auth import AuthUser
from app.schemas.enums import Role
from app.services.dataset_service import validate_csv_rows

from .conftest import create_user, login
from .test_integration import seed_dataset


def test_scheduling_failure_releases_model_lock(client: TestClient, db: Database) -> None:
    from app.services.audit_service import AuditService

    create_user(db, 'schedule@example.com', 'admin')
    _, headers = login(client, 'schedule@example.com')
    seed_dataset(db)
    with (
        patch.object(AuditService, 'record', side_effect=RuntimeError('audit unavailable')),
        pytest.raises(RuntimeError),
    ):
        client.post('/api/models/run', headers=headers, json={'model': 'if', 'top_k': 1})
    assert db.locks.find_one({'_id': 'model_run'}) is None
    assert db.jobs.find_one()['status'] == 'failed'


def test_refresh_consumption_is_atomic(db: Database) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from app.repositories.auth import AuthRepository

    repo = AuthRepository(db)
    repo.save_refresh_token('1', 'test-hash', datetime.now(UTC) + timedelta(days=1), None, 'test')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(repo.consume_refresh_token, ['test-hash', 'test-hash']))
    assert sum(result is not None for result in results) == 1


def test_spoofed_forwarding_header_does_not_bypass_lockout(client: TestClient, db: Database) -> None:
    create_user(db, 'spoof@example.com', 'analyst')
    for index in range(5):
        response = client.post(
            '/api/auth/login',
            headers={'X-Forwarded-For': f'192.0.2.{index}'},
            data={'username': 'spoof@example.com', 'password': 'bad-password'},
        )
        assert response.status_code == 401
    assert (
        client.post(
            '/api/auth/login',
            headers={'X-Forwarded-For': '198.51.100.1'},
            data={'username': 'spoof@example.com', 'password': 'bad-password'},
        ).status_code
        == 429
    )


def test_per_ip_throttle_across_emails(client: TestClient) -> None:
    for index in range(20):
        assert (
            client.post(
                '/api/auth/login',
                data={
                    'username': f'missing{index}@example.com',
                    'password': 'bad-password',
                },
            ).status_code
            == 401
        )
    assert (
        client.post(
            '/api/auth/login',
            data={
                'username': 'another@example.com',
                'password': 'bad-password',
            },
        ).status_code
        == 429
    )


def test_refresh_reuse_revokes_all_sessions(client: TestClient, db: Database) -> None:
    create_user(db, 'reuse@example.com', 'analyst')
    response = client.post(
        '/api/auth/login',
        data={
            'username': 'reuse@example.com',
            'password': 'LongTestPassword!123',
        },
    )
    first = response.cookies['path_refresh']
    response = client.post('/api/auth/refresh')
    assert response.status_code == 200
    token = response.json()['access_token']
    client.cookies.set('path_refresh', first, domain='testserver.local', path='/api/auth')
    assert client.post('/api/auth/refresh').status_code == 401
    assert client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401
    assert db.audit_logs.find_one({'action': 'auth.refresh.reuse'}) is not None


def test_admin_self_protection_and_password_reset(client: TestClient, db: Database) -> None:
    own_id = create_user(db, 'owner@example.com', 'admin')
    other_id = create_user(db, 'other@example.com', 'analyst')
    _, headers = login(client, 'owner@example.com')
    for body in ({'is_active': False}, {'role': 'analyst'}):
        assert client.patch(f'/api/users/{own_id}', headers=headers, json=body).status_code == 409
    _, old_headers = login(client, 'other@example.com')
    assert (
        client.post(
            f'/api/users/{other_id}/reset-password',
            headers=headers,
            json={'new_password': 'Replacement-Password-123!'},
        ).status_code
        == 200
    )
    assert client.get('/api/auth/me', headers=old_headers).status_code == 401
    _, reset_headers = login(client, 'other@example.com', 'Replacement-Password-123!')
    assert client.get('/api/transactions', headers=reset_headers).status_code == 403
    assert (
        client.post(
            '/api/auth/change-password',
            headers=reset_headers,
            json={
                'current_password': 'Replacement-Password-123!',
                'new_password': 'Changed-Password-456!',
            },
        ).status_code
        == 200
    )
    _, changed = login(client, 'other@example.com', 'Changed-Password-456!')
    assert client.get('/api/transactions', headers=changed).status_code == 200


def test_role_change_revokes_tokens(client: TestClient, db: Database) -> None:
    create_user(db, 'admin@example.com', 'admin')
    target = create_user(db, 'target@example.com', 'analyst')
    _, admin = login(client, 'admin@example.com')
    _, old = login(client, 'target@example.com')
    assert client.patch(f'/api/users/{target}', headers=admin, json={'role': 'reviewer'}).status_code == 200
    assert client.get('/api/auth/me', headers=old).status_code == 401


def test_request_id_validation_and_log_minimization(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    response = client.get('/health', headers={'X-Request-ID': 'bad value'})
    assert response.headers['X-Request-ID'] != 'bad value'
    valid = 'trace.valid-123'
    assert client.get('/health', headers={'X-Request-ID': valid}).headers['X-Request-ID'] == valid
    for record in caplog.records:
        if record.name == 'path.request':
            assert not hasattr(record, 'user_email')


def test_lease_expiry_and_owner_fencing(db: Database) -> None:
    leases = LeaseRepository(db)
    assert leases.acquire('job', 'first', 30)
    assert not leases.acquire('job', 'second', 30)
    db.locks.update_one({'_id': 'job'}, {'$set': {'expires_at': datetime.now(UTC) - timedelta(seconds=1)}})
    assert leases.acquire('job', 'second', 30)
    assert not leases.renew('job', 'first', 30)
    leases.release('job', 'first')
    assert leases.renew('job', 'second', 30)


def test_stale_job_recovery(db: Database) -> None:
    db.jobs.insert_one(
        {'job_id': 'stuck', 'status': 'running', 'updated_at': datetime.now(UTC) - timedelta(hours=1)}
    )
    assert ModelRepository(db).recover_stale_jobs(300) == 1
    assert db.jobs.find_one({'job_id': 'stuck'})['status'] == 'failed'


def test_model_row_guard_before_lock(
    client: TestClient, db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_user(db, 'bounded@example.com', 'analyst')
    _, headers = login(client, 'bounded@example.com')
    seed_dataset(db)
    db.transactions.insert_one({'dataset_id': 'dataset-test', 'transaction_id': 'third'})
    monkeypatch.setattr(get_settings(), 'ml_max_rows', 2)
    response = client.post('/api/models/run', headers=headers, json={'model': 'if', 'top_k': 1})
    assert response.status_code == 413
    assert db.locks.find_one({'_id': 'model_run'}) is None


def test_retention_cascades_and_preserves_active(db: Database) -> None:
    old = datetime.now(UTC) - timedelta(days=400)
    for dataset_id in ('old', 'active'):
        db.datasets.insert_one({'dataset_id': dataset_id, 'created_at': old})
        for collection in ('transactions', 'anomalies', 'model_runs'):
            db[collection].insert_one({'dataset_id': dataset_id, 'run_id': dataset_id})
        db.reviews.insert_one({'run_id': dataset_id, 'note': 'review'})
    db.settings.insert_one({'_id': 'active_dataset_id', 'value': 'active'})
    apply_retention(db, 365)
    for collection in ('datasets', 'transactions', 'anomalies', 'model_runs', 'reviews'):
        assert db[collection].count_documents({}) == 1


def test_streaming_upload_rolls_back_failed_activation(client: TestClient, db: Database) -> None:
    create_user(db, 'upload@example.com', 'admin')
    _, headers = login(client, 'upload@example.com')
    with (
        patch.object(SettingsRepository, 'set', side_effect=RuntimeError('unavailable')),
        pytest.raises(RuntimeError),
    ):
        client.post(
            '/api/datasets/upload',
            headers=headers,
            files={
                'file': (
                    'data.csv',
                    'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n'
                    'T1,2026-01-01,A,S,V,D,1,2\n',
                    'text/csv',
                )
            },
        )
    assert db.transactions.count_documents({}) == 0
    assert db.datasets.count_documents({}) == 0


@pytest.mark.parametrize('value', ['nan', 'inf', '-1'])
def test_upload_rejects_bad_money(value: str) -> None:
    accepted, count, issues = validate_csv_rows(
        'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n'
        f'T1,2026-01-01,A,S,V,D,{value},2\n'
    )
    assert count == 1 and not accepted and issues


def test_row_guard_and_naive_datetime() -> None:
    with pytest.raises(HTTPException) as caught:
        validate_csv_rows(
            'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n'
            'T1,2026-01-01,A,S,V,D,1,2\nT2,2026-01-01,A,S,V,D,1,2\n',
            max_rows=1,
        )
    assert caught.value.status_code == 413
    assert as_utc(datetime(2026, 1, 1)).tzinfo == UTC


def test_no_active_dataset_delete_and_invalid_text(client: TestClient, db: Database) -> None:
    create_user(db, 'badcsv@example.com', 'admin')
    _, headers = login(client, 'badcsv@example.com')
    response = client.post(
        '/api/datasets/upload', headers=headers, files={'file': ('bad.csv', b'\xff\xfe', 'text/csv')}
    )
    assert response.status_code == 422
    assert db.datasets.count_documents({}) == 0


def test_last_admin_guard(db: Database) -> None:
    from app.repositories.users import UserRepository
    from app.schemas.users import UserUpdate
    from app.services.user_service import UserService

    own_id = create_user(db, 'only@example.com', 'admin')
    actor = AuthUser(id='different', email='operator@example.com', role=Role.admin, is_active=True)
    with pytest.raises(HTTPException) as caught:
        UserService(UserRepository(db)).update(own_id, UserUpdate(is_active=False), actor)
    assert caught.value.status_code == 409
