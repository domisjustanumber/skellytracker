"""The run-time rules of the keypoint schema: missing keypoints and derived points (section `post.keypoint.schema`)."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


def mark_missing(keypoints: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply the rule of a missing keypoint, after the decode and the unprojection.

    Implements: post.keypoint.schema

    `keypoints` has the shape (..., P, D) and `scores` has the shape (..., P). A keypoint with a
    score `<= 0` or a NaN score is missing: each coordinate becomes NaN and the score becomes 0.
    The results are new float arrays. A host compares the scores with its thresholds after this
    rule.
    """
    points = np.array(keypoints, dtype=np.result_type(keypoints.dtype, np.float32))
    marked = np.array(scores, dtype=np.result_type(scores.dtype, np.float32))
    missing = ~(marked > 0)  # A comparison with NaN is false, so a NaN score is missing too.
    points[missing] = np.nan
    marked[missing] = 0
    return points, marked


def derived_points(
    keypoints: np.ndarray,
    scores: np.ndarray,
    point_names: Sequence[str],
    derived: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the derived points of `keypoint.derived_points`, in the order of the map.

    Implements: post.keypoint.schema

    `keypoints` (..., P, D) and `scores` (..., P) are the results of `mark_missing`, in the order
    of `point_names`. `derived` is `KeypointSpec.derived_points`: a name is the keypoint with that
    name, a list is the unweighted mean of its keypoints, and a map is the weighted sum with the
    weights as given. A derived point is missing when a source is missing: its coordinates are NaN
    and its score is 0. If not, its score is the minimum of the scores of its sources. Returns the
    coordinates (..., N, D) and the scores (..., N).
    """
    index = {name: position for position, name in enumerate(point_names)}
    out_points = np.empty((*keypoints.shape[:-2], len(derived), keypoints.shape[-1]), dtype=keypoints.dtype)
    out_scores = np.empty((*scores.shape[:-1], len(derived)), dtype=scores.dtype)
    for position, derivation in enumerate(derived.values()):
        if isinstance(derivation, str):
            weights = {derivation: 1.0}
        elif isinstance(derivation, Mapping):
            weights = dict(derivation)
        else:
            weights = {name: 1.0 / len(derivation) for name in derivation}
        sources = [index[name] for name in weights]
        source_scores = scores[..., sources]
        missing = ~(source_scores > 0).all(axis=-1)
        if isinstance(derivation, str):
            point = keypoints[..., sources[0], :].copy()
        elif isinstance(derivation, Mapping):
            point = (keypoints[..., sources, :] * np.asarray(list(weights.values()))[:, None]).sum(axis=-2)
        else:
            point = keypoints[..., sources, :].mean(axis=-2)
        point[missing] = np.nan
        out_points[..., position, :] = point
        out_scores[..., position] = np.where(missing, 0, source_scores.min(axis=-1))
    return out_points, out_scores
