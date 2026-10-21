from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from app.ml.engine import percentile_risk_labels, precision_recall_at_k, run_model
from app.ml.features import engineer_features
from app.schemas.enums import ModelName, RiskLevel


def rows() -> list[dict[str, object]]:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        {
            'transaction_id': f'TX-{index}',
            'date': base + timedelta(days=index),
            'agency': 'A',
            'scheme': 'S',
            'vendor': 'V' if index < 4 else 'X',
            'amount_paise': 10000 if index < 4 else 900000,
            'sanctioned_amount_paise': 1_000_000,
            'reversal_flag': False,
            'cancelled_flag': False,
        }
        for index in range(5)
    ]


def test_engineer_features_shape_and_vendor_window() -> None:
    matrix, insights = engineer_features(rows())
    assert matrix.shape == (5, 12)
    assert insights[3]['vendor_transactions_30d'] == 4
    assert insights[4]['scheme_utilization'] > 0


def test_engineer_features_rejects_bad_date() -> None:
    bad = rows()
    bad[0]['date'] = '2026-01-01'
    with pytest.raises(ValueError):
        engineer_features(bad)


def test_run_model_is_deterministic_and_top_k_metrics() -> None:
    matrix, _ = engineer_features(rows())
    labels = np.array([0, 0, 0, 0, 1])
    first = run_model(matrix, ModelName.isolation_forest, 2, 50, 42, 1, labels=labels)
    second = run_model(matrix, ModelName.isolation_forest, 2, 50, 42, 1, labels=labels)
    assert np.allclose(first.scores, second.scores)
    assert first.metrics['top_k'] == 2
    assert first.metrics['precision_at_k'] is not None


def test_precision_recall_at_k_hand_computed() -> None:
    labels = np.array([1, 0, 1, 0])
    ranking = np.array([0, 1, 2, 3])
    precision, recall = precision_recall_at_k(labels, ranking, 2)
    assert precision == 0.5
    assert recall == 0.5


def test_risk_labels_percentiles() -> None:
    labels = percentile_risk_labels(np.arange(100, dtype=float))
    assert labels[-1] == RiskLevel.critical
    assert labels[0] == RiskLevel.normal
    assert labels.count(RiskLevel.critical) >= 1


def test_unknown_model_raises() -> None:
    matrix = np.arange(20, dtype=float).reshape(10, 2)
    with pytest.raises((ValueError, TypeError)):
        run_model(matrix, 'bogus', 2, 50, 42, 1)  # type: ignore[arg-type]
