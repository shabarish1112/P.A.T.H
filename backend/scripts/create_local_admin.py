"""Create a unique development login for the local-only launcher."""

from __future__ import annotations

import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mongo import get_db, initialize_database


def main() -> None:
    settings = get_settings()
    if settings.environment != 'development':
        raise SystemExit('This helper is restricted to development.')
    from urllib.parse import urlsplit

    if urlsplit(settings.mongo_uri).hostname not in {'127.0.0.1', 'localhost'}:
        raise SystemExit('This helper requires a local MongoDB.')
    db = get_db()
    initialize_database(db)
    if db.users.find_one() is not None:
        print('An application user already exists; no login was changed.')
        return
    path = Path(__file__).resolve().parents[2] / '.local' / 'login.txt'
    path.parent.mkdir(exist_ok=True)
    password = secrets.token_urlsafe(24)
    email = 'local-admin@example.com'
    # Exclusive creation protects a previously generated credential file.
    with path.open('x', encoding='utf-8') as output:
        output.write(
            f'Local development login\nURL: http://localhost:5173\nEmail: {email}\nPassword: {password}\n'
        )
    db.users.insert_one(
        {
            'email': email,
            'password_hash': hash_password(password),
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.now(UTC),
        }
    )
    print(f'Created local admin. Private login details: {path}')


if __name__ == '__main__':
    main()
