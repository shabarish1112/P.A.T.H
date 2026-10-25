from __future__ import annotations

from datetime import UTC, datetime

from .conftest import create_user, login
from .test_integration import seed_dataset


def seed_run(db, critical_count: int = 1) -> None:
    db.model_runs.insert_one(
        {
            'run_id': 'run-insights',
            'dataset_id': 'dataset-test',
            'top_k': critical_count,
            'created_at': datetime.now(UTC),
        }
    )
    db.settings.update_one({'_id': 'active_run_id'}, {'$set': {'value': 'run-insights'}}, upsert=True)
    for index in range(critical_count):
        db.anomalies.insert_one(
            {
                'run_id': 'run-insights',
                'dataset_id': 'dataset-test',
                'transaction_id': f'TX-{index + 1}',
                'rank': index + 1,
                'score': 0.99,
                'risk': 'Critical',
                'amount_paise': 10000,
                'agency': 'A',
                'scheme': 'S',
                'vendor': 'V',
                'district': 'D',
                'path_insight': {'amount_vs_vendor_mean': 4.25, 'vendor_transactions_30d': 12},
            }
        )


def test_insights_requires_authentication(client) -> None:
    assert client.get('/api/analytics/insights').status_code == 401


def test_insights_distinguishes_missing_and_unanalyzed_dataset(client, db) -> None:
    create_user(db, 'insights@example.com', 'analyst')
    _, headers = login(client, 'insights@example.com')
    empty = client.get('/api/analytics/insights', headers=headers)
    assert empty.status_code == 200
    assert empty.json()['status'] == 'no_dataset'
    seed_dataset(db)
    pending = client.get('/api/analytics/insights', headers=headers).json()
    assert pending['status'] == 'not_analyzed'
    assert pending['transaction_count'] == 2
    assert pending['critical_records'] == []


def test_critical_record_can_be_investigated_and_reviewed(client, db) -> None:
    create_user(db, 'insights-reviewer@example.com', 'reviewer')
    _, headers = login(client, 'insights-reviewer@example.com')
    seed_dataset(db)
    seed_run(db)
    response = client.get('/api/analytics/insights', headers=headers)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'private, no-store'
    summary = response.json()
    assert summary['status'] == 'ready'
    assert summary['critical_count'] == 1
    assert summary['flagged_count'] == 1
    assert '2 public fund disbursal records' in summary['narrative']
    assert 'Open a transaction' in summary['narrative']
    record = summary['critical_records'][0]
    assert "about 4.3 times this vendor's usual payment" in record['signals'][0]
    assert record['check'] == "Check: this vendor's earlier invoices."
    assert '12 payments' in record['signals'][1]
    txid = record['transaction_id']
    detail = client.get(f'/api/transactions/{txid}', headers=headers).json()
    assert detail['risk'] == 'Critical'
    assert detail['explanation'] == record['explanation']
    assert detail['total_transactions'] == 2
    decision = client.put(
        f'/api/reviews/{txid}',
        headers=headers,
        json={'status': 'False Alert', 'note': 'Checked source records.'},
    )
    assert decision.status_code == 200
    reviewed = client.get(f'/api/transactions/{txid}', headers=headers).json()
    assert reviewed['review_actor_email'] == 'insights-reviewer@example.com'
    assert reviewed['review_changed_at']
    assert reviewed['review_note'] == 'Checked source records.'
    history = client.get('/api/reviews', headers=headers).json()['items']
    assert len(history) == 1
    assert history[0]['transaction_id'] == txid
    assert history[0]['status'] == 'False Alert'
    assert history[0]['actor_email'] == 'insights-reviewer@example.com'
    assert history[0]['created_at']
    assert db.audit_logs.count_documents({'action': 'review.update'}) == 1


def test_summary_bounds_records_but_counts_all_critical_alerts(client, db) -> None:
    create_user(db, 'bounded-insights@example.com', 'analyst')
    _, headers = login(client, 'bounded-insights@example.com')
    seed_dataset(db)
    seed_run(db, 7)
    data = client.get('/api/analytics/insights', headers=headers).json()
    assert data['critical_count'] == 7
    assert len(data['critical_records']) == 5
    assert [r['transaction_id'] for r in data['critical_records']] == [f'TX-{i}' for i in range(1, 6)]


def test_previous_dataset_results_never_describe_new_upload(client, db) -> None:
    create_user(db, 'new-upload@example.com', 'analyst')
    _, headers = login(client, 'new-upload@example.com')
    seed_dataset(db)
    seed_run(db)
    db.datasets.insert_one({'dataset_id': 'new-upload', 'filename': 'new.csv', 'row_count': 10})
    db.settings.update_one({'_id': 'active_dataset_id'}, {'$set': {'value': 'new-upload'}})
    data = client.get('/api/analytics/insights', headers=headers).json()
    assert data['status'] == 'not_analyzed'
    assert data['dataset_name'] == 'new.csv'
    assert data['critical_records'] == []
    summary = client.get('/api/analytics/summary', headers=headers).json()
    assert summary['active_run_id'] is None
    assert summary['active_anomalies']['value'] == 0
    assert client.get('/api/anomalies', headers=headers).json()['items'] == []
    assert client.get('/api/reviews', headers=headers).json()['items'] == []
