from datetime import UTC, datetime, timedelta

import pytest

from .conftest import create_user, login

CSV = 'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n' + '\n'.join(
    f'P-{i},2026-01-01,A,S,V{i % 3},D,{1000 + i * 100},100000' for i in range(12)
)


def analyze(client, **kwargs):
    return client.post('/api/public/analyze', files={'file': ('data.csv', CSV, 'text/csv')}, **kwargs)


def test_guest_analyzes_without_auth_and_cannot_touch_staff_data(client, db):
    db.settings.insert_one({'_id': 'active_dataset_id', 'value': 'staff-data'})
    response = analyze(client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body['rows_accepted'] == 12
    assert len(body['alerts']) == 12
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert client.get('/api/public/analyses/' + body['analysis_id']).status_code == 200
    assert db.settings.find_one({'_id': 'active_dataset_id'})['value'] == 'staff-data'
    assert db.transactions.count_documents({}) == 0
    assert client.get('/api/transactions').status_code == 401
    assert client.post('/api/models/run', json={'model': 'if'}).status_code == 401


def test_guest_result_isolation_tampering_and_expiry(client, db):
    body = analyze(client).json()
    url = '/api/public/analyses/' + body['analysis_id']
    cookie = client.cookies.get('path_guest')
    client.cookies.clear()
    assert client.get(url).status_code == 404
    second = analyze(client).json()
    assert second['analysis_id'] != body['analysis_id']
    assert client.get(url).status_code == 404
    client.cookies.clear()
    client.cookies.set('path_guest', cookie + 'tampered')
    assert client.get(url).status_code == 404
    client.cookies.clear()
    client.cookies.set('path_guest', cookie)
    db.public_analyses.update_one(
        {'_id': body['analysis_id']}, {'$set': {'expire_at': datetime.now(UTC) - timedelta(seconds=1)}}
    )
    assert client.get(url).status_code == 404


def test_public_rejects_bad_uploads_foreign_origins_and_limits_abuse(client):
    assert (
        client.post('/api/public/analyze', files={'file': ('bad.csv', 'bad', 'text/csv')}).status_code == 422
    )
    assert analyze(client, headers={'Origin': 'https://evil.example'}).status_code == 403
    for _ in range(5):
        assert (
            client.post('/api/public/analyze', files={'file': ('bad.txt', 'x', 'text/plain')}).status_code
            == 422
        )
    assert analyze(client).status_code == 429


def test_signup_member_login_logout_and_staff_denial(client, db):
    db.users.create_index('email', unique=True)
    payload = {'email': 'new@example.com', 'password': 'StrongNewPassword!123'}
    response = client.post('/api/auth/signup', json=payload)
    assert response.status_code == 201, response.text
    assert response.json()['user']['role'] == 'member'
    stored = db.users.find_one({'email': payload['email']})
    assert stored['password_hash'] != payload['password']
    assert 'password' not in response.json()['user']
    token, headers = login(client, payload['email'], payload['password'])
    assert token
    assert client.get('/api/auth/me', headers=headers).json()['user']['role'] == 'member'
    assert client.get('/api/transactions', headers=headers).status_code == 403
    assert client.get('/api/users', headers=headers).status_code == 403
    result = analyze(client, headers=headers)
    assert result.status_code == 201
    assert db.public_analyses.find_one({'_id': result.json()['analysis_id']})['user_id'] == str(stored['_id'])
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    assert client.post('/api/auth/refresh').status_code == 401
    assert client.post('/api/auth/signup', json=payload).status_code == 409


@pytest.mark.parametrize('extra', [{'role': 'admin'}, {'is_active': True}])
def test_signup_cannot_assign_privileges(client, extra):
    body = {'email': 'new@example.com', 'password': 'StrongNewPassword!123', **extra}
    assert client.post('/api/auth/signup', json=body).status_code == 422


def test_invalid_signup_and_registration_throttle(client):
    assert (
        client.post('/api/auth/signup', json={'email': 'not-email', 'password': 'short'}).status_code == 422
    )
    for index in range(10):
        response = client.post(
            '/api/auth/signup',
            json={
                'email': f'new{index}@example.com',
                'password': 'StrongNewPassword!123',
            },
        )
        assert response.status_code == 201
    assert (
        client.post(
            '/api/auth/signup',
            json={
                'email': 'blocked@example.com',
                'password': 'StrongNewPassword!123',
            },
        ).status_code
        == 429
    )


def test_guest_bearer_token_cannot_be_used_for_staff_auth(client, db):
    create_user(db, 'staff@example.com', 'admin')
    assert analyze(client).status_code == 201
    assert (
        client.get(
            '/api/users', headers={'Authorization': 'Bearer ' + client.cookies.get('path_guest')}
        ).status_code
        == 401
    )
