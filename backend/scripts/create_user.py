from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password
from app.db.mongo import get_db, initialize_database
from app.schemas.enums import Role


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a P.A.T.H. user')
    parser.add_argument('--email', required=True)
    parser.add_argument('--role', required=True, choices=[role.value for role in Role])
    parser.add_argument('--password-stdin', action='store_true', help='Read one password line from stdin (CI only)')
    args = parser.parse_args()
    if args.password_stdin:
        password = sys.stdin.readline().rstrip('\n')
        confirm = password
    else:
        password = getpass.getpass('Password (minimum 12 chars): ')
        confirm = getpass.getpass('Confirm password: ')
    if password != confirm or len(password) < 12:
        print('Passwords must match and be at least 12 characters.', file=sys.stderr)
        return 2
    db = get_db()
    initialize_database(db)
    try:
        db.users.insert_one(
            {
                'email': args.email.strip().lower(),
                'password_hash': hash_password(password),
                'role': args.role,
                'is_active': True,
                'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
            }
        )
    except DuplicateKeyError:
        print('A user with that email already exists.', file=sys.stderr)
        return 3
    print(f'Created {args.role} user {args.email.strip().lower()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
