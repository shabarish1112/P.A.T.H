from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.transactions import TransactionRepository


def test_search_regex_input_is_escaped_and_prefix_only(db) -> None:
    repo = TransactionRepository(db)
    db.datasets.insert_one({'dataset_id': 'd', 'row_count': 2})
    for txid in ['TX-100', 'ZZ-200']:
        db.transactions.insert_one(
            {
                'dataset_id': 'd',
                'transaction_id': txid,
                'search_key': txid.lower(),
                'date': datetime.now(UTC),
                'agency': 'A',
                'scheme': 'S',
                'vendor': 'V',
                'district': 'D',
                'amount_paise': 1,
                'sanctioned_amount_paise': 10,
            }
        )
    rows, _ = repo.list_keyset('d', 50, None, 'TX-')
    assert [row['transaction_id'] for row in rows] == ['TX-100']
    injected, _ = repo.list_keyset('d', 50, None, '.*')
    assert injected == []
