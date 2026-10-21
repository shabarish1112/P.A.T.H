from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.schemas.enums import Role


def test_password_hashing_round_trip() -> None:
    encoded = hash_password('CorrectHorseBatteryStaple!')
    assert 'CorrectHorseBatteryStaple!' not in encoded
    assert verify_password('CorrectHorseBatteryStaple!', encoded)
    assert not verify_password('wrong-password', encoded)


def test_jwt_tamper_rejected() -> None:
    settings = get_settings()
    token, _ = create_access_token('abc', 'user@example.com', Role.analyst, settings)
    assert decode_access_token(token, settings)['sub'] == 'abc'
    with pytest.raises(HTTPException):
        decode_access_token(token + 'tampered', settings)


def test_expired_jwt_rejected() -> None:
    settings = get_settings()
    payload = {
        'sub': 'abc',
        'email': 'user@example.com',
        'role': 'analyst',
        'type': 'access',
        'exp': datetime.now(UTC) - timedelta(seconds=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(HTTPException):
        decode_access_token(token, settings)
