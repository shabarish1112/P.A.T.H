from __future__ import annotations

import numpy as np


def downsample(matrix: np.ndarray, max_rows: int, random_state: int) -> tuple[np.ndarray, np.ndarray]:
    if len(matrix) <= max_rows:
        indices = np.arange(len(matrix))
        return matrix, indices
    rng = np.random.default_rng(random_state)
    indices = np.sort(rng.choice(len(matrix), size=max_rows, replace=False))
    return matrix[indices], indices
