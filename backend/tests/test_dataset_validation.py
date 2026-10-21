from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.services.dataset_service import neutralize_csv_cell, validate_csv_rows


def csv_text(rows: str) -> str:
    return 'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount\n' + rows


def test_valid_csv() -> None:
    accepted, total, issues = validate_csv_rows(csv_text('TX-1,2026-01-01,A,S,V,D,100,1000\n'))
    assert total == 1
    assert len(accepted) == 1
    assert accepted[0]['amount_paise'] == 10000
    assert issues == []


@pytest.mark.parametrize(
    'row',
    [
        'TX-1,bad-date,A,S,V,D,100,1000\n',
        'TX-1,2026-01-01,A,S,V,D,-1,1000\n',
        'TX-1,2026-01-01,A,S,V,D,nan,1000\n',
        'TX-1,2026-01-01,A,S,V,D,inf,1000\n',
    ],
)
def test_invalid_rows_reported(row: str) -> None:
    accepted, total, issues = validate_csv_rows(csv_text(row))
    assert total == 1
    assert not accepted
    assert issues and issues[0].row == 2


def test_duplicate_transaction_ids_reported() -> None:
    text = csv_text('TX-1,2026-01-01,A,S,V,D,100,1000\nTX-1,2026-01-02,A,S,V,D,100,1000\n')
    accepted, total, issues = validate_csv_rows(text)
    assert total == 2
    assert len(accepted) == 1
    assert 'duplicate' in issues[0].reason.lower()


def test_missing_column_rejected() -> None:
    with pytest.raises(HTTPException):
        validate_csv_rows('transaction_id,date\nTX-1,2026-01-01\n')


def test_csv_formula_neutralization() -> None:
    assert neutralize_csv_cell('=SUM(A1:A2)').startswith("'")
    assert neutralize_csv_cell('safe') == 'safe'


def test_unknown_columns_are_dropped() -> None:
    text = (
        'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount,secret_extra\n'
        'TX-1,2026-01-01,A,S,V,D,100,1000,drop-me\n'
    )
    accepted, _, issues = validate_csv_rows(text)
    assert not issues
    assert 'secret_extra' not in accepted[0]


def test_upload_rejects_oversize_content_length(monkeypatch) -> None:
    import asyncio
    from types import SimpleNamespace

    from app.services.dataset_service import DatasetService

    class Settings:
        max_upload_mb = 1

    class Request:
        headers = {'content-length': str(1024 * 1024 + 1)}

    class Upload:
        filename = 'large.csv'

        async def read(self, _: int) -> bytes:
            raise AssertionError('body must not be read after oversized Content-Length')

    service = DatasetService.__new__(DatasetService)
    service.settings = Settings()
    service.repo = SimpleNamespace()
    service.settings_repo = SimpleNamespace()
    service.cache = SimpleNamespace()
    actor = SimpleNamespace(id='admin-id')

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.upload(Upload(), Request(), actor, False))
    assert exc.value.status_code == 413
