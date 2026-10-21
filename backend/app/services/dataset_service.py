from __future__ import annotations

import csv
import io
import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, Request, UploadFile
from pydantic import ValidationError

from app.core.cache import CacheBackend
from app.core.config import Settings
from app.repositories.datasets import DatasetRepository
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


def validate_csv_rows(content: str) -> tuple[list[dict[str, object]], int, list[ValidationIssue]]:
    reader = csv.DictReader(io.StringIO(content))
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
            accepted.append(
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
        data = bytearray()
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > max_bytes:
                raise HTTPException(status_code=413, detail='Upload exceeds configured size limit')
        try:
            content = data.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail='CSV must be UTF-8 encoded') from exc
        accepted, total, issues = validate_csv_rows(content)
        if not accepted:
            raise HTTPException(status_code=422, detail='No valid rows found')
        active_dataset = self.settings_repo.get('active_dataset_id')
        if active_dataset and not confirm_replace:
            raise HTTPException(
                status_code=409,
                detail='An active dataset exists; set confirm_replace=true to activate a replacement',
            )
        dataset_id = uuid.uuid4().hex
        docs = [{**row, 'dataset_id': dataset_id} for row in accepted]
        self.repo.insert_transactions(docs)
        self.repo.create_dataset(dataset_id, file.filename or 'upload.csv', len(docs), actor.id)
        self.settings_repo.set('active_dataset_id', dataset_id)
        self.cache.invalidate('analytics:')
        self.cache.invalidate('transactions:')
        return DatasetUploadResponse(
            dataset_id=dataset_id,
            filename=file.filename or 'upload.csv',
            rows_received=total,
            rows_accepted=len(docs),
            rows_rejected=total - len(docs),
            issues=issues,
            activated=True,
            created_at=datetime.now(UTC),
        )
