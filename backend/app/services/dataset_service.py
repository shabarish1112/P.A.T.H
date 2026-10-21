from __future__ import annotations

import csv
import io
import math
import uuid
from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from fastapi import HTTPException, Request, UploadFile
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.core.cache import CacheBackend
from app.core.config import Settings
from app.repositories.datasets import DatasetRepository
from app.repositories.leases import LeaseRepository
from app.repositories.settings import SettingsRepository
from app.schemas.auth import AuthUser
from app.schemas.datasets import (
    DatasetDeleteResponse,
    DatasetListResponse,
    DatasetResponse,
    DatasetUploadResponse,
    ValidationIssue,
)
from app.schemas.transactions import CsvTransactionRow

_ALLOWED_COLUMNS = {
    'transaction_id',
    'date',
    'agency',
    'scheme',
    'vendor',
    'district',
    'amount',
    'sanctioned_amount',
    'payment_type',
    'reversal_flag',
    'cancelled_flag',
    'injected_anomaly',
}
_REQUIRED_COLUMNS = {
    'transaction_id',
    'date',
    'agency',
    'scheme',
    'vendor',
    'district',
    'amount',
    'sanctioned_amount',
}


def neutralize_csv_cell(value: object) -> str:
    text = '' if value is None else str(value)
    return f"'{text}" if text.startswith(('=', '+', '-', '@')) else text


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or '').strip().lower()
    if text in {'1', 'true', 'yes', 'y'}:
        return True
    if text in {'0', 'false', 'no', 'n', ''}:
        return False
    raise ValueError('invalid boolean')


def _parse_date(value: str) -> datetime:
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('date must be ISO-8601') from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_csv_rows(
    content: str | Iterable[str],
    max_rows: int = 100000,
    on_row: Callable[[dict[str, object]], None] | None = None,
) -> tuple[list[dict[str, object]], int, list[ValidationIssue]]:
    reader = csv.DictReader(io.StringIO(content) if isinstance(content, str) else content)
    fieldnames = set(reader.fieldnames or [])
    missing = sorted(_REQUIRED_COLUMNS - fieldnames)
    if missing:
        raise HTTPException(status_code=422, detail=f'Missing required columns: {", ".join(missing)}')
    accepted: list[dict[str, object]] = []
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    total = 0
    for row_number, raw in enumerate(reader, start=2):
        total += 1
        if total > max_rows:
            raise HTTPException(status_code=413, detail='CSV exceeds MAX_ROWS')
        filtered = {key: value for key, value in raw.items() if key in _ALLOWED_COLUMNS}
        try:
            normalized = {
                **filtered,
                'date': _parse_date(str(filtered.get('date', ''))),
                'amount': float(str(filtered.get('amount', '')).replace(',', '')),
                'sanctioned_amount': float(str(filtered.get('sanctioned_amount', '')).replace(',', '')),
                'reversal_flag': _to_bool(filtered.get('reversal_flag', False)),
                'cancelled_flag': _to_bool(filtered.get('cancelled_flag', False)),
                'injected_anomaly': _to_bool(filtered.get('injected_anomaly', False))
                if 'injected_anomaly' in filtered
                else None,
            }
            item = CsvTransactionRow.model_validate(normalized)
            if not math.isfinite(item.amount) or not math.isfinite(item.sanctioned_amount):
                raise ValueError('money values must be finite')
            if item.transaction_id in seen:
                raise ValueError('duplicate transaction_id in upload')
            seen.add(item.transaction_id)
            emit = on_row if on_row is not None else accepted.append
            emit(
                {
                    'transaction_id': item.transaction_id,
                    'date': item.date,
                    'agency': item.agency,
                    'scheme': item.scheme,
                    'vendor': item.vendor,
                    'district': item.district,
                    'amount_paise': int(round(item.amount * 100)),
                    'sanctioned_amount_paise': int(round(item.sanctioned_amount * 100)),
                    'payment_type': item.payment_type,
                    'reversal_flag': item.reversal_flag,
                    'cancelled_flag': item.cancelled_flag,
                    'injected_anomaly': item.injected_anomaly,
                    'search_key': item.transaction_id.lower(),
                }
            )
        except (ValidationError, ValueError) as exc:
            if len(issues) < 50:
                issues.append(ValidationIssue(row=row_number, reason=str(exc)))
    return accepted, total, issues


class DatasetService:
    def __init__(
        self,
        repo: DatasetRepository,
        settings_repo: SettingsRepository,
        cache: CacheBackend,
        settings: Settings,
    ) -> None:
        self.repo = repo
        self.settings_repo = settings_repo
        self.cache = cache
        self.settings = settings

    def list_datasets(self) -> DatasetListResponse:
        active = self.settings_repo.get('active_dataset_id')
        return DatasetListResponse(
            items=[
                DatasetResponse(
                    dataset_id=str(doc['dataset_id']),
                    filename=str(doc['filename']),
                    row_count=int(doc['row_count']),
                    created_at=doc['created_at'],
                    created_by=str(doc['created_by']),
                    is_active=doc['dataset_id'] == active,
                )
                for doc in self.repo.list()
            ]
        )

    def delete_dataset(self, dataset_id: str) -> DatasetDeleteResponse:
        if self.settings_repo.get('active_dataset_id') == dataset_id:
            raise HTTPException(status_code=409, detail='Active dataset cannot be deleted')
        if self.repo.get(dataset_id) is None:
            raise HTTPException(status_code=404, detail='Dataset not found')
        self.repo.delete(dataset_id)
        self.cache.invalidate('analytics:')
        self.cache.invalidate('transactions:')
        return DatasetDeleteResponse(dataset_id=dataset_id, deleted=True)

    async def upload(
        self,
        file: UploadFile,
        request: Request,
        actor: AuthUser,
        confirm_replace: bool,
    ) -> DatasetUploadResponse:
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > max_bytes:
            raise HTTPException(status_code=413, detail='Upload exceeds configured size limit')
        if file.size is not None and file.size > max_bytes:
            raise HTTPException(status_code=413, detail='Upload exceeds configured size limit')
        return await run_in_threadpool(self._ingest, file, actor, confirm_replace)

    def _ingest(self, file: UploadFile, actor: AuthUser, confirm_replace: bool) -> DatasetUploadResponse:
        owner = uuid.uuid4().hex
        leases = LeaseRepository(self.repo.db)
        if not leases.acquire('dataset_activation', owner, 3600):
            raise HTTPException(status_code=409, detail='Another upload is in progress')
        dataset_id = uuid.uuid4().hex
        created = False
        wrapper = io.TextIOWrapper(file.file, encoding='utf-8-sig', newline='')
        batch: list[dict[str, object]] = []
        count = 0

        def stage(row: dict[str, object]) -> None:
            nonlocal count
            row['dataset_id'] = dataset_id
            batch.append(row)
            count += 1
            if len(batch) >= 500:
                self.repo.insert_transactions(batch)
                batch.clear()

        try:
            active_dataset = self.settings_repo.get('active_dataset_id')
            if active_dataset and not confirm_replace:
                raise HTTPException(status_code=409, detail='Confirm replacement of the active dataset')
            self.repo.create_dataset(dataset_id, file.filename or 'upload.csv', 0, actor.id)
            created = True
            _, total, issues = validate_csv_rows(wrapper, self.settings.max_rows, stage)
            if count == 0:
                raise HTTPException(status_code=422, detail='No valid rows found')
            self.repo.insert_transactions(batch)
            self.repo.db.datasets.update_one(
                {'dataset_id': dataset_id},
                {'$set': {'status': 'ready', 'row_count': count}},
            )
            self.settings_repo.set('active_dataset_id', dataset_id)
            created = False
            self.cache.invalidate('analytics:')
            self.cache.invalidate('transactions:')
            return DatasetUploadResponse(
                dataset_id=dataset_id,
                filename=file.filename or 'upload.csv',
                rows_received=total,
                rows_accepted=count,
                rows_rejected=total - count,
                issues=issues,
                activated=True,
                created_at=datetime.now(UTC),
            )
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail='CSV must be UTF-8 encoded') from exc
        finally:
            wrapper.detach()
            if created:
                self.repo.delete(dataset_id)
            leases.release('dataset_activation', owner)
