from __future__ import annotations

from datetime import UTC, datetime

from .conftest import create_user, login


def seed_dataset(db) -> None:
    dataset_id = 'dataset-test'
    db.datasets.insert_one(
        {
            'dataset_id': dataset_id,
            'filename': 'test.csv',
            'row_count': 2,
            'created_at': datetime.now(UTC),
            'created_by': 'seed',
        }
    )
    db.settings.insert_one({'_id': 'active_dataset_id', 'value': dataset_id})
    for index in range(2):
        db.transactions.insert_one(
            {
                'transaction_id': f'TX-{index + 1}',
                'date': datetime(2026, 1, index + 1, tzinfo=UTC),
                'agency': 'A',
                'scheme': 'S',
                'vendor': 'V',
                'district': 'D',
                'amount_paise': 10000 + index,
                'sanctioned_amount_paise': 1000000,
                'payment_type': 'Electronic',
                'reversal_flag': False,
                'cancelled_flag': False,
                'dataset_id': dataset_id,
                'search_key': f'tx-{index + 1} a s v d',
            }
        )


def test_public_health_and_protected_401(client) -> None:
    assert client.get('/health').status_code == 200
    assert client.get('/health/live').status_code == 200
    assert client.get('/api/transactions').status_code == 401


def test_role_enforcement_and_me(client, db) -> None:
    create_user(db, 'analyst@example.com', 'analyst')
    _, headers = login(client, 'analyst@example.com')
    assert client.get('/api/auth/me', headers=headers).status_code == 200
    assert client.get('/api/audit', headers=headers).status_code == 403
    assert (
        client.post(
            '/api/users',
            headers=headers,
            json={'email': 'x@example.com', 'password': 'VeryLongPassword!123', 'role': 'analyst'},
        ).status_code
        == 403
    )


def test_admin_user_management(client, db) -> None:
    create_user(db, 'admin@example.com', 'admin')
    _, headers = login(client, 'admin@example.com')
    response = client.post(
        '/api/users',
        headers=headers,
        json={'email': 'new@example.com', 'password': 'VeryLongPassword!123', 'role': 'reviewer'},
    )
    assert response.status_code == 201
    assert client.get('/api/users', headers=headers).status_code == 200
    assert (
        client.patch(
            f'/api/users/{response.json()["id"]}', headers=headers, json={'is_active': False}
        ).status_code
        == 200
    )


def test_transactions_analytics_anomalies_reviews_paths(client, db) -> None:
    create_user(db, 'reviewer@example.com', 'reviewer')
    _, headers = login(client, 'reviewer@example.com')
    seed_dataset(db)
    assert client.get('/api/transactions', headers=headers).status_code == 200
    assert client.get('/api/transactions?q=TX-', headers=headers).status_code == 200
    assert client.get('/api/transactions/DOES-NOT-EXIST', headers=headers).status_code == 404
    assert client.get('/api/anomalies', headers=headers).status_code == 200
    assert client.get('/api/analytics/summary', headers=headers).status_code == 200
    assert client.get('/api/analytics/trend', headers=headers).status_code == 200
    assert client.get('/api/analytics/breakdown', headers=headers).status_code == 200
    assert client.get('/api/reviews', headers=headers).status_code == 200
    assert (
        client.put(
            '/api/reviews/TX-1', headers=headers, json={'status': 'Pending Review', 'note': 'checked'}
        ).status_code
        == 409
    )


def test_login_lockout(client, db) -> None:
    create_user(db, 'locked@example.com', 'analyst')
    for _ in range(5):
        assert (
            client.post(
                '/api/auth/login', data={'username': 'locked@example.com', 'password': 'wrong-password'}
            ).status_code
            == 401
        )
    assert (
        client.post(
            '/api/auth/login', data={'username': 'locked@example.com', 'password': 'wrong-password'}
        ).status_code
        == 429
    )


def test_validation_422(client, db) -> None:
    create_user(db, 'admin2@example.com', 'admin')
    _, headers = login(client, 'admin2@example.com')
    assert client.get('/api/transactions?limit=9999', headers=headers).status_code == 422
    assert (
        client.post('/api/models/run', headers=headers, json={'model': 'unknown', 'top_k': 5}).status_code
        == 422
    )


def test_all_protected_routes_reject_missing_token(client) -> None:
    protected = [
        ('GET', '/api/auth/me'),
        ('POST', '/api/auth/logout'),
        ('GET', '/api/users'),
        ('GET', '/api/datasets'),
        ('GET', '/api/transactions'),
        ('POST', '/api/models/run'),
        ('GET', '/api/models/jobs/unknown'),
        ('GET', '/api/anomalies'),
        ('GET', '/api/analytics/summary'),
        ('GET', '/api/analytics/trend'),
        ('GET', '/api/analytics/breakdown'),
        ('GET', '/api/reviews'),
        ('PUT', '/api/reviews/TX-1'),
        ('GET', '/api/audit'),
    ]
    for method, path in protected:
        response = client.request(method, path)
        assert response.status_code == 401, (method, path, response.text)


def test_refresh_rotation_and_logout(client, db) -> None:
    create_user(db, 'rotate@example.com', 'analyst')
    login_response = client.post(
        '/api/auth/login', data={'username': 'rotate@example.com', 'password': 'LongTestPassword!123'}
    )
    assert login_response.status_code == 200
    first_cookie = login_response.cookies.get('path_refresh')
    refresh_response = client.post('/api/auth/refresh')
    assert refresh_response.status_code == 200
    second_cookie = refresh_response.cookies.get('path_refresh')
    assert second_cookie and second_cookie != first_cookie
    access = refresh_response.json()['access_token']
    logout_response = client.post('/api/auth/logout', headers={'Authorization': f'Bearer {access}'})
    assert logout_response.status_code == 200


def test_dataset_upload_and_inactive_delete(client, db) -> None:
    create_user(db, 'dataset-admin@example.com', 'admin')
    _, headers = login(client, 'dataset-admin@example.com')
    csv_body = (
        'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n'
        'TX-CSV-1,2026-01-01,A,S,V,D,100,1000\n'
        'TX-CSV-2,2026-01-02,A,S,V,D,120,1000\n'
    )
    response = client.post(
        '/api/datasets/upload',
        headers=headers,
        files={'file': ('test.csv', csv_body, 'text/csv')},
    )
    assert response.status_code == 201
    first_id = response.json()['dataset_id']
    second = client.post(
        '/api/datasets/upload?confirm_replace=true',
        headers=headers,
        files={'file': ('test2.csv', csv_body.replace('TX-CSV-', 'TX-NEW-'), 'text/csv')},
    )
    assert second.status_code == 201
    assert client.delete(f'/api/datasets/{first_id}', headers=headers).status_code == 200
    assert client.get('/api/datasets', headers=headers).status_code == 200


def test_model_job_anomaly_review_and_audit_success(client, db) -> None:
    create_user(db, 'workflow-admin@example.com', 'admin')
    _, headers = login(client, 'workflow-admin@example.com')
    seed_dataset(db)
    run = client.post(
        '/api/models/run',
        headers=headers,
        json={'model': 'if', 'top_k': 1, 'n_estimators': 50, 'random_state': 42, 'include_umap': False},
    )
    assert run.status_code == 202
    job_id = run.json()['job_id']
    job = client.get(f'/api/models/jobs/{job_id}', headers=headers)
    assert job.status_code == 200
    assert job.json()['status'] in {'completed', 'failed'}
    if job.json()['status'] == 'completed':
        anomalies = client.get('/api/anomalies', headers=headers)
        assert anomalies.status_code == 200
        assert len(anomalies.json()['items']) == 1
        transaction_id = anomalies.json()['items'][0]['transaction_id']
        review = client.put(
            f'/api/reviews/{transaction_id}',
            headers=headers,
            json={'status': 'Escalated', 'note': 'Requires source-record review.'},
        )
        assert review.status_code == 200
        assert client.get('/api/audit', headers=headers).status_code == 200


def test_not_found_job(client, db) -> None:
    create_user(db, 'job@example.com', 'analyst')
    _, headers = login(client, 'job@example.com')
    assert client.get('/api/models/jobs/00000000000000000000000000000000', headers=headers).status_code == 404


def test_malformed_job_id(client, db) -> None:
    create_user(db, 'job-invalid@example.com', 'analyst')
    _, headers = login(client, 'job-invalid@example.com')
    assert client.get('/api/models/jobs/missing', headers=headers).status_code == 422
