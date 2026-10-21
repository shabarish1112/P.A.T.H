"""Initialize the dedicated local development MongoDB using .env credentials."""

from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import OperationFailure


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    values = dotenv_values(root / '.env')
    password = values['MONGO_ROOT_PASSWORD']
    username = values['MONGO_ROOT_USER']
    # The localhost exception permits the first admin while auth stays enabled.
    with MongoClient('127.0.0.1', 27017, serverSelectionTimeoutMS=5000) as initial:
        try:
            initial.admin.command(
                'createUser',
                username,
                pwd=password,
                roles=[{'role': 'root', 'db': 'admin'}],
            )
        except OperationFailure as exc:
            # Existing users disable the exception; authenticate normally below.
            if exc.code not in {13, 51003}:
                raise
    authenticated = MongoClient(
        '127.0.0.1',
        27017,
        username=username,
        password=password,
        authSource='admin',
        serverSelectionTimeoutMS=5000,
    )
    try:
        users = authenticated.path.command('usersInfo', values['PATH_APP_USER'])
        if not users['users']:
            authenticated.path.command(
                'createUser',
                values['PATH_APP_USER'],
                pwd=values['PATH_APP_PASSWORD'],
                roles=[{'role': 'readWrite', 'db': 'path'}],
            )
    finally:
        authenticated.close()
    print('Local MongoDB credentials initialized; authentication remains enabled.')


if __name__ == '__main__':
    main()
