from __future__ import annotations

from app.db.mongo import get_db


def stages(plan: dict) -> list[str]:
    found: list[str] = []
    def walk(value):
        if isinstance(value, dict):
            if 'stage' in value:
                found.append(str(value['stage']))
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)
    walk(plan)
    return found


def assert_ixscan(name: str, plan: dict) -> None:
    used = stages(plan)
    if 'IXSCAN' not in used:
        raise SystemExit(f'{name}: expected IXSCAN, got {used}')
    print(f'{name}: IXSCAN OK')


def main() -> None:
    db = get_db()
    active_dataset = db.settings.find_one({'_id': 'active_dataset_id'})
    active_run = db.settings.find_one({'_id': 'active_run_id'})
    if active_dataset:
        plan = db.transactions.find({'dataset_id': active_dataset['value'], 'search_key': {'$regex': '^tx'}}).explain()
        assert_ixscan('transaction prefix search', plan)
    if active_run:
        plan = db.anomalies.find({'run_id': active_run['value']}).sort('rank', 1).explain()
        assert_ixscan('active anomaly rank', plan)
        plan = db.anomalies.find({'run_id': active_run['value'], 'risk': 'High'}).sort('rank', 1).explain()
        assert_ixscan('active anomaly risk/rank', plan)


if __name__ == '__main__':
    main()
