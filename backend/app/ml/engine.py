from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler

from app.ml.utils import downsample
from app.schemas.enums import ModelName, RiskLevel


@dataclass
class EngineResult:
    scores: np.ndarray
    path_lengths: np.ndarray
    pca: np.ndarray
    umap: np.ndarray | None
    risks: list[RiskLevel]
    ranking: np.ndarray
    metrics: dict[str, float | int | None]


def _path_lengths(model: IsolationForest, matrix: np.ndarray) -> np.ndarray:
    columns: list[np.ndarray] = []
    for estimator in model.estimators_:
        path = estimator.decision_path(matrix)
        depths = np.asarray(path.sum(axis=1)).reshape(-1) - 1
        columns.append(depths.astype(np.float64))
    return np.column_stack(columns)


def _score_if(
    matrix: np.ndarray, n_estimators: int, random_state: int, n_jobs: int
) -> tuple[np.ndarray, np.ndarray]:
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination='auto',
        random_state=random_state,
        n_jobs=n_jobs,
    )
    model.fit(matrix)
    scores = -model.score_samples(matrix)
    return scores, _path_lengths(model, matrix)


def _eif_lite_transform(matrix: np.ndarray, random_state: int) -> np.ndarray:
    rng = np.random.default_rng(random_state)
    projection_count = max(matrix.shape[1] * 2, 16)
    projection = rng.normal(0.0, 1.0, size=(matrix.shape[1], projection_count))
    projection /= np.maximum(np.linalg.norm(projection, axis=0, keepdims=True), 1e-12)
    return matrix @ projection


def _dif_lite_transform(matrix: np.ndarray, random_state: int) -> np.ndarray:
    rng = np.random.default_rng(random_state)
    hidden = max(matrix.shape[1] * 4, 32)
    weights = rng.normal(0.0, 1.0 / np.sqrt(matrix.shape[1]), size=(matrix.shape[1], hidden))
    bias = rng.normal(0.0, 0.1, size=(hidden,))
    return np.maximum(0.0, matrix @ weights + bias)


def percentile_risk_labels(scores: np.ndarray) -> list[RiskLevel]:
    if len(scores) == 0:
        return []
    q99, q95, q85, q65 = np.quantile(scores, [0.99, 0.95, 0.85, 0.65])
    labels: list[RiskLevel] = []
    for score in scores:
        if score >= q99:
            labels.append(RiskLevel.critical)
        elif score >= q95:
            labels.append(RiskLevel.high)
        elif score >= q85:
            labels.append(RiskLevel.medium)
        elif score >= q65:
            labels.append(RiskLevel.low)
        else:
            labels.append(RiskLevel.normal)
    return labels


def precision_recall_at_k(labels: np.ndarray, ranking: np.ndarray, top_k: int) -> tuple[float, float]:
    if len(labels) == 0 or labels.sum() == 0:
        return 0.0, 0.0
    k = min(top_k, len(labels))
    selected = labels[ranking[:k]].astype(bool)
    true_positives = int(selected.sum())
    return true_positives / k, true_positives / int(labels.sum())


def run_model(
    matrix: np.ndarray,
    model_name: ModelName,
    top_k: int,
    n_estimators: int,
    random_state: int,
    n_jobs: int,
    labels: np.ndarray | None = None,
    include_umap: bool = False,
    umap_max_rows: int = 5000,
) -> EngineResult:
    if model_name not in {
        ModelName.isolation_forest,
        ModelName.extended_isolation_forest,
        ModelName.deep_isolation_forest,
    }:
        raise ValueError(f'Unknown model: {model_name}')
    if matrix.ndim != 2 or len(matrix) < 2:
        raise ValueError('At least two rows are required for model execution')

    scaled = StandardScaler().fit_transform(matrix)
    transformed = scaled
    if model_name == ModelName.extended_isolation_forest:
        transformed = _eif_lite_transform(scaled, random_state)
    elif model_name == ModelName.deep_isolation_forest:
        transformed = _dif_lite_transform(scaled, random_state)

    scores, path_lengths = _score_if(transformed, n_estimators, random_state, n_jobs)
    ranking = np.argsort(scores)[::-1]
    risks = percentile_risk_labels(scores)
    pca = PCA(n_components=2, random_state=random_state).fit_transform(path_lengths)

    umap_points: np.ndarray | None = None
    if include_umap:
        try:
            import umap
        except ImportError as exc:
            raise RuntimeError('UMAP requested but umap-learn is not installed') from exc
        sampled, sampled_indices = downsample(path_lengths, umap_max_rows, random_state)
        embedded = umap.UMAP(n_components=2, random_state=random_state, n_jobs=1).fit_transform(sampled)
        umap_points = np.column_stack([sampled_indices, embedded])

    metrics: dict[str, float | int | None] = {
        'rows': len(matrix),
        'top_k': min(top_k, len(matrix)),
        'pr_auc': None,
        'precision_at_k': None,
        'recall_at_k': None,
    }
    if labels is not None and len(labels) == len(scores) and labels.sum() > 0:
        precision, recall = precision_recall_at_k(labels, ranking, top_k)
        metrics['precision_at_k'] = round(precision, 6)
        metrics['recall_at_k'] = round(recall, 6)
        metrics['pr_auc'] = round(float(average_precision_score(labels, scores)), 6)

    return EngineResult(
        scores=scores,
        path_lengths=path_lengths,
        pca=pca,
        umap=umap_points,
        risks=risks,
        ranking=ranking,
        metrics=metrics,
    )
