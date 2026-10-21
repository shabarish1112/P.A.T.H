"""Initialize the dedicated local development MongoDB using .env credentials."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import OperationFailure

from scripts.provision_mongo import provision_database


def main() -> None:
    os.chdir(Path(__file__).resolve().parents[1])
    root = Path(__file__).resolve().parents[2]
    values = dotenv_values(root / 'infra' / 'mongo.env')
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
        provision_database(authenticated.path, str(values['PATH_APP_USER']), str(values['PATH_APP_PASSWORD']))
    finally:
        authenticated.close()
    print('Local MongoDB credentials initialized; authentication remains enabled.')


if __name__ == '__main__':
    main()
