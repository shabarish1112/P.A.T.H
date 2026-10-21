from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np

FEATURE_NAMES = [
    'amount_log',
    'amount_vs_vendor_mean',
    'amount_vs_agency_mean',
    'amount_vs_scheme_mean',
    'vendor_transactions_30d',
    'scheme_utilization',
    'days_since_previous_vendor_payment',
    'month_sin',
    'month_cos',
    'fiscal_year_end',
    'reversal_flag',
    'cancelled_flag',
]


def _financial_year(date: datetime) -> str:
    start = date.year if date.month >= 4 else date.year - 1
    return f'{start}-{str(start + 1)[-2:]}'


def _require_datetime(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError('transaction date must be a datetime')
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def engineer_features(rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[dict[str, float | int | str]]]:
    if not rows:
        return np.empty((0, len(FEATURE_NAMES))), []

    vendor_amounts: dict[str, list[int]] = defaultdict(list)
    agency_amounts: dict[str, list[int]] = defaultdict(list)
    scheme_amounts: dict[str, list[int]] = defaultdict(list)
    vendor_dates: dict[str, list[datetime]] = defaultdict(list)
    scheme_year_spend: dict[tuple[str, str], int] = defaultdict(int)
    scheme_year_budget: dict[tuple[str, str], int] = defaultdict(int)

    normalized: list[dict[str, Any]] = []
    for row in rows:
        date = _require_datetime(row['date'])
        amount = int(row['amount_paise'])
        sanctioned = int(row.get('sanctioned_amount_paise', 0))
        item = {**row, 'date': date, 'amount_paise': amount, 'sanctioned_amount_paise': sanctioned}
        normalized.append(item)
        vendor_amounts[str(row['vendor'])].append(amount)
        agency_amounts[str(row['agency'])].append(amount)
        scheme_amounts[str(row['scheme'])].append(amount)
        vendor_dates[str(row['vendor'])].append(date)
        fy_key = (str(row['scheme']), _financial_year(date))
        scheme_year_budget[fy_key] = max(scheme_year_budget[fy_key], sanctioned)

    for dates in vendor_dates.values():
        dates.sort()

    vendor_means = {key: float(np.mean(values)) for key, values in vendor_amounts.items()}
    agency_means = {key: float(np.mean(values)) for key, values in agency_amounts.items()}
    scheme_means = {key: float(np.mean(values)) for key, values in scheme_amounts.items()}

    order = sorted(range(len(normalized)), key=lambda index: normalized[index]['date'])
    features = np.zeros((len(normalized), len(FEATURE_NAMES)), dtype=np.float64)
    insights: list[dict[str, float | int | str]] = [{} for _ in normalized]
    previous_vendor_date: dict[str, datetime] = {}

    for index in order:
        row = normalized[index]
        date = row['date']
        vendor = str(row['vendor'])
        agency = str(row['agency'])
        scheme = str(row['scheme'])
        amount = int(row['amount_paise'])
        fy = _financial_year(date)
        budget = scheme_year_budget[(scheme, fy)]
        scheme_year_spend[(scheme, fy)] += amount
        utilization = scheme_year_spend[(scheme, fy)] / budget if budget > 0 else 0.0

        dates = vendor_dates[vendor]
        window_start = date - timedelta(days=30)
        left = bisect_left(dates, window_start)
        right = bisect_left(dates, date + timedelta(microseconds=1))
        vendor_30d = right - left

        prior = previous_vendor_date.get(vendor)
        gap_days = max((date - prior).days, 0) if prior else 365
        previous_vendor_date[vendor] = date

        vendor_ratio = amount / max(vendor_means[vendor], 1.0)
        agency_ratio = amount / max(agency_means[agency], 1.0)
        scheme_ratio = amount / max(scheme_means[scheme], 1.0)
        month_angle = 2 * np.pi * (date.month - 1) / 12
        fiscal_year_end = 1.0 if date.month == 3 else 0.0

        features[index] = [
            np.log1p(amount / 100.0),
            vendor_ratio,
            agency_ratio,
            scheme_ratio,
            vendor_30d,
            utilization,
            gap_days,
            np.sin(month_angle),
            np.cos(month_angle),
            fiscal_year_end,
            float(bool(row.get('reversal_flag', False))),
            float(bool(row.get('cancelled_flag', False))),
        ]
        insights[index] = {
            'amount_vs_vendor_mean': round(vendor_ratio, 3),
            'amount_vs_agency_mean': round(agency_ratio, 3),
            'amount_vs_scheme_mean': round(scheme_ratio, 3),
            'vendor_transactions_30d': vendor_30d,
            'scheme_utilization': round(utilization, 4),
            'days_since_previous_vendor_payment': gap_days,
            'fiscal_year': fy,
        }

    return features, insights
