"""Privileged bootstrap; never run with the application database identity."""

from pymongo.database import Database

from app.db.mongo import initialize_database


def provision_database(database: Database, username: str, password: str) -> None:
    initialize_database(database)
    database.audit_logs.create_index([('created_at', -1)])
    database.audit_logs.create_index([('expire_at', 1)], expireAfterSeconds=0)
    collections = (
        'transactions',
        'anomalies',
        'reviews',
        'refresh_tokens',
        'users',
        'datasets',
        'model_runs',
        'jobs',
        'settings',
        'login_attempts',
        'locks',
    )
    privileges: list[dict[str, object]] = [
        {
            'resource': {'db': database.name, 'collection': name},
            'actions': [
                'find',
                'insert',
                'update',
                'remove',
                'createIndex',
                'listIndexes',
                'createCollection',
                'collMod',
            ],
        }
        for name in collections
    ]
    privileges.extend(
        [
            {'resource': {'db': database.name, 'collection': ''}, 'actions': ['listCollections']},
            {
                'resource': {'db': database.name, 'collection': 'audit_logs'},
                'actions': ['find', 'insert', 'listIndexes'],
            },
        ]
    )
    command = 'updateRole' if database.command('rolesInfo', 'pathApplication')['roles'] else 'createRole'
    database.command(command, 'pathApplication', privileges=privileges, roles=[])
    roles = [{'role': 'pathApplication', 'db': database.name}]
    if database.command('usersInfo', username)['users']:
        database.command('updateUser', username, roles=roles)
    else:
        database.command('createUser', username, pwd=password, roles=roles)
