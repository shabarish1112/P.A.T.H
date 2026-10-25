from __future__ import annotations

from datetime import UTC, datetime

from app.ml.features import engineer_features
from app.repositories.transactions import TransactionRepository

from .conftest import create_user, login
from .test_insights import seed_run
from .test_integration import seed_dataset


def test_non_alert_transaction_has_evidence_without_fabricated_score(client, db):
    create_user(db, 'all-records@example.com', 'analyst')
    _, headers = login(client, 'all-records@example.com')
    seed_dataset(db)
    seed_run(db)
    response = client.get('/api/transactions/TX-2', headers=headers)
    assert response.status_code == 200
    detail = response.json()
    assert detail['analysis_status'] == 'not_selected'
    assert detail['explanation']['signals']
    assert detail['path_insight']['vendor_transactions_30d'] == 2
    assert detail['path_insight']['days_since_previous_vendor_payment'] == 1
    assert detail['path_insight']['fiscal_year'] == '2025-26'
    assert detail['anomaly_score'] is None
    assert detail['rank'] is None
    assert detail['risk'] is None
    assert 'flagged' not in detail['explanation']['headline']
    assert db.anomalies.count_documents({}) == 1
    assert db.reviews.count_documents({}) == 0


def test_evidence_available_before_training_and_unknown_record_remains_404(client, db):
    create_user(db, 'before-run@example.com', 'analyst')
    _, headers = login(client, 'before-run@example.com')
    seed_dataset(db)
    detail = client.get('/api/transactions/TX-1', headers=headers).json()
    assert detail['analysis_status'] == 'not_analyzed'
    assert detail['explanation']['signals']
    assert detail['path_insight']['days_since_previous_vendor_payment'] == 365
    assert any(r['value_text'] == 'First payment on record' for r in detail['explanation']['signals'])
    assert client.get('/api/transactions/TX-missing', headers=headers).status_code == 404


def test_on_demand_facts_match_engineering_including_ties_and_year_boundary(db):
    seed_dataset(db)
    template = db.transactions.find_one({'transaction_id': 'TX-1'})
    for txid, date, amount, budget in [
        ('TX-tie', datetime(2026, 1, 2, tzinfo=UTC), 0, 0),
        ('TX-march', datetime(2026, 3, 31, tzinfo=UTC), 120000, 900000),
        ('TX-april', datetime(2026, 4, 1, tzinfo=UTC), 5000, 0),
        ('TX-gap', datetime(2027, 4, 1, tzinfo=UTC), 12000, 0),
    ]:
        db.transactions.insert_one(
            {
                **{k: v for k, v in template.items() if k != '_id'},
                'transaction_id': txid,
                'date': date,
                'amount_paise': amount,
                'sanctioned_amount_paise': budget,
            }
        )
    repo = TransactionRepository(db)
    rows = repo.get_all_for_dataset('dataset-test')
    _, expected = engineer_features(rows)
    for row, signals in zip(rows, expected, strict=True):
        context = repo.explanation_context('dataset-test', row)
        assert repo.contextual_signals('dataset-test', row, context) == signals
