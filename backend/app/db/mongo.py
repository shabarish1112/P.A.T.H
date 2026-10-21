from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from app.core.config import Settings, get_settings

_client: MongoClient[Any] | None = None
_db: Database[Any] | None = None


def get_client(settings: Settings | None = None) -> MongoClient[Any]:
    global _client
    if _client is None:
        cfg = settings or get_settings()
        kwargs: dict[str, Any] = {'serverSelectionTimeoutMS': 5000, 'tz_aware': True}
        if cfg.mongo_tls_ca_file:
            kwargs['tlsCAFile'] = cfg.mongo_tls_ca_file
        if cfg.mongo_tls_cert_key_file:
            kwargs['tlsCertificateKeyFile'] = cfg.mongo_tls_cert_key_file
        _client = MongoClient(cfg.mongo_uri, **kwargs)
    return _client


def get_db(settings: Settings | None = None) -> Database[Any]:
    global _db
    if _db is None:
        cfg = settings or get_settings()
        _db = get_client(cfg)[cfg.mongo_db]
    return _db


def reset_db_for_tests(db: Database[Any] | None = None) -> None:
    global _client, _db
    if db is not None:
        _db = db
        _client = None
    else:
        if _client is not None:
            _client.close()
        _client = None
        _db = None


def _ensure_collection_validator(db: Database[Any], name: str, schema: dict[str, Any]) -> None:
    existing = next(db.list_collections(filter={'name': name}), None)
    if existing is None:
        db.create_collection(name, validator={'$jsonSchema': schema})
        return
    if existing.get('options', {}).get('validator') == {'$jsonSchema': schema}:
        return
    db.command({'collMod': name, 'validator': {'$jsonSchema': schema}, 'validationLevel': 'moderate'})


def initialize_database(db: Database[Any] | None = None) -> None:
    database = db if db is not None else get_db()
    transaction_schema = {
        'bsonType': 'object',
        'required': [
            'transaction_id',
            'date',
            'agency',
            'scheme',
            'vendor',
            'district',
            'amount_paise',
            'dataset_id',
        ],
        'properties': {
            'transaction_id': {'bsonType': 'string'},
            'date': {'bsonType': 'date'},
            'amount_paise': {'bsonType': ['int', 'long']},
            'sanctioned_amount_paise': {'bsonType': ['int', 'long']},
            'dataset_id': {'bsonType': 'string'},
            'search_key': {'bsonType': 'string'},
        },
    }
    anomaly_schema = {
        'bsonType': 'object',
        'required': ['run_id', 'transaction_id', 'rank', 'score', 'risk'],
        'properties': {
            'run_id': {'bsonType': 'string'},
            'rank': {'bsonType': 'int'},
            'score': {'bsonType': ['double', 'int', 'long']},
            'risk': {'enum': ['Critical', 'High', 'Medium', 'Low', 'Normal']},
        },
    }
    review_schema = {
        'bsonType': 'object',
        'required': ['transaction_id', 'run_id', 'status', 'actor_id', 'actor_email', 'created_at'],
        'properties': {
            'status': {'enum': ['Pending Review', 'Confirmed Finding', 'False Alert', 'Escalated']},
            'created_at': {'bsonType': 'date'},
        },
    }
    audit_schema = {
        'bsonType': 'object',
        'required': ['actor_id', 'actor_email', 'action', 'resource_type', 'created_at', 'expire_at'],
        'properties': {'created_at': {'bsonType': 'date'}, 'expire_at': {'bsonType': 'date'}},
    }
    refresh_schema = {
        'bsonType': 'object',
        'required': ['user_id', 'token_hash', 'expires_at', 'created_at'],
        'properties': {'expires_at': {'bsonType': 'date'}, 'created_at': {'bsonType': 'date'}},
    }
    user_schema = {
        'bsonType': 'object',
        'required': ['email', 'password_hash', 'role', 'is_active', 'created_at'],
        'properties': {
            'role': {'enum': ['analyst', 'reviewer', 'admin']},
            'is_active': {'bsonType': 'bool'},
            'created_at': {'bsonType': 'date'},
        },
    }
    dataset_schema = {
        'bsonType': 'object',
        'required': ['dataset_id', 'filename', 'row_count', 'created_at', 'created_by'],
        'properties': {
            'dataset_id': {'bsonType': 'string'},
            'row_count': {'bsonType': ['int', 'long']},
            'created_at': {'bsonType': 'date'},
        },
    }
    model_run_schema = {
        'bsonType': 'object',
        'required': ['run_id', 'dataset_id', 'model', 'top_k', 'created_at', 'created_by'],
        'properties': {
            'model': {'enum': ['if', 'eif', 'dif']},
            'top_k': {'bsonType': ['int', 'long']},
            'created_at': {'bsonType': 'date'},
        },
    }
    job_schema = {
        'bsonType': 'object',
        'required': ['job_id', 'status', 'progress', 'created_at', 'updated_at', 'created_by'],
        'properties': {
            'status': {'enum': ['queued', 'running', 'completed', 'failed']},
            'progress': {'bsonType': ['int', 'long']},
            'created_at': {'bsonType': 'date'},
            'updated_at': {'bsonType': 'date'},
        },
    }
    settings_schema = {'bsonType': 'object', 'required': ['_id', 'value']}
    login_attempt_schema = {
        'bsonType': 'object',
        'required': ['key', 'failures', 'expire_at'],
        'properties': {
            'failures': {'bsonType': ['int', 'long']},
            'expire_at': {'bsonType': 'date'},
        },
    }
    for name, schema in (
        ('transactions', transaction_schema),
        ('anomalies', anomaly_schema),
        ('reviews', review_schema),
        ('audit_logs', audit_schema),
        ('refresh_tokens', refresh_schema),
        ('users', user_schema),
        ('datasets', dataset_schema),
        ('model_runs', model_run_schema),
        ('jobs', job_schema),
        ('settings', settings_schema),
        ('login_attempts', login_attempt_schema),
    ):
        _ensure_collection_validator(database, name, schema)

    database.users.create_index([('email', ASCENDING)], unique=True)
    database.refresh_tokens.create_index([('token_hash', ASCENDING)], unique=True)
    database.refresh_tokens.create_index([('expires_at', ASCENDING)], expireAfterSeconds=0)
    database.login_attempts.create_index([('key', ASCENDING)], unique=True)
    database.login_attempts.create_index([('expire_at', ASCENDING)], expireAfterSeconds=0)
    database.transactions.create_index(
        [('dataset_id', ASCENDING), ('transaction_id', ASCENDING)], unique=True
    )
    database.transactions.create_index([('dataset_id', ASCENDING), ('search_key', ASCENDING)])
    database.transactions.create_index([('dataset_id', ASCENDING), ('_id', ASCENDING)])
    database.transactions.create_index([('dataset_id', ASCENDING), ('date', ASCENDING)])
    database.anomalies.create_index([('run_id', ASCENDING), ('rank', ASCENDING)])
    database.anomalies.create_index([('run_id', ASCENDING), ('risk', ASCENDING), ('rank', ASCENDING)])
    database.reviews.create_index(
        [('run_id', ASCENDING), ('transaction_id', ASCENDING), ('created_at', DESCENDING)]
    )
    database.audit_logs.create_index([('created_at', DESCENDING)])
    database.audit_logs.create_index([('expire_at', ASCENDING)], expireAfterSeconds=0)
    database.model_runs.create_index([('created_at', DESCENDING)])
    database.jobs.create_index([('created_at', DESCENDING)])
    database.datasets.create_index([('created_at', DESCENDING)])


def apply_retention(db: Database[Any] | None = None, retention_days: int = 365) -> None:
    database = db if db is not None else get_db()
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    active = database.settings.find_one({'_id': 'active_dataset_id'})
    active_id = active.get('value') if active else None
    old_ids = [
        doc['dataset_id']
        for doc in database.datasets.find(
            {'created_at': {'$lt': cutoff}, 'dataset_id': {'$ne': active_id}}, {'dataset_id': 1}
        )
    ]
    if old_ids:
        database.transactions.delete_many({'dataset_id': {'$in': old_ids}})
        database.datasets.delete_many({'dataset_id': {'$in': old_ids}})


def ping_database(db: Database[Any] | None = None) -> bool:
    database = db if db is not None else get_db()
    database.command('ping')
    return True
