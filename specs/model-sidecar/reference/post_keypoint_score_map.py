"""Reference implementation of the proposed section post.keypoint.score_map.

Section ID: post.keypoint.score_map (proposed section file specs/model-sidecar/post/keypoint/score-map.md).
Proposal: simcc-score-map of OpenMMLab-Exporter, part 3.
Target file in skellytracker: specs/model-sidecar/reference/post_keypoint_score_map.py.
Imported sections: none. Fixtures: none.

source commit: see the header of proposal.md (OpenMMLab-Exporter onnx_runtime/score_map.py::map_scores
is the host implementation; this file is its minimal form).

The module implements the full section: the pair of each keypoint (the pair of its landmark-schema
group, else the size pair), the missing rule on the raw score, and the logistic map. The raw score is
the score of the decode section (post.keypoint.decode.simcc). This module does not change it.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

RULE_PAIR = "V-post.keypoint.score_map-3"
RULE_GROUP = "V-post.keypoint.score_map-4"


def check_pair(value: dict[str, Any], where: str) -> tuple[float, float]:
    """post.keypoint.score_map: `a` must be a finite number > 0, and `b` a finite number."""
    a, b = value.get("a"), value.get("b")
    for number in (a, b):
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError(f"{RULE_PAIR}: {where} needs finite numbers a and b")
    if a <= 0:
        raise ValueError(f"{RULE_PAIR}: {where}.a must be > 0")
    return float(a), float(b)


def point_pairs(score_map: dict[str, Any], point_groups: list[str] | None, count: int) -> tuple[np.ndarray, np.ndarray]:
    """post.keypoint.score_map: the (a, b) of each of `count` keypoints.

    A keypoint of a group with a pair in `groups` gets that pair. Each other keypoint gets the size
    pair (`a`, `b`).
    """
    a, b = check_pair(score_map, "score_map")
    a_k, b_k = np.full(count, a), np.full(count, b)
    groups = score_map.get("groups") or {}
    if groups and (point_groups is None or len(point_groups) != count):
        raise ValueError("no-rule: point_groups must give the group of each keypoint")
    for name, pair in groups.items():
        members = np.array([g == name for g in point_groups])
        if not members.any():
            raise ValueError(f"{RULE_GROUP}: groups.{name} is not a group of the landmark schema")
        a_k[members], b_k[members] = check_pair(pair, f"score_map.groups.{name}")
    return a_k, b_k


def logistic(z: np.ndarray) -> np.ndarray:
    """post.keypoint.score_map: 1 / (1 + exp(-z)) in float64; z = -inf gives 0, z = +inf gives 1."""
    return 0.5 * (1.0 + np.tanh(0.5 * z))


def map_scores(raw: np.ndarray, score_map: dict[str, Any], point_groups: list[str] | None) -> np.ndarray:
    """post.keypoint.score_map, Behaviour: the mapped score of (..., K) raw scores.

    A missing keypoint (raw NaN or raw <= 0) gets the score 0. Each other keypoint gets
    logistic(a_k * raw + b_k). The arithmetic is float64. The result is float32.
    """
    if score_map.get("method") != "logistic":
        raise ValueError("V-post.keypoint.score_map-2: method must be logistic")
    raw64 = np.asarray(raw, dtype=np.float32).astype(np.float64)
    a_k, b_k = point_pairs(score_map, point_groups, raw64.shape[-1])
    present = raw64 > 0
    mapped = logistic(a_k * np.where(present, raw64, 0.0) + b_k)
    return np.where(present, mapped, 0.0).astype(np.float32)


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """post.keypoint.score_map, Behaviour: one case.

    params: `score_map` (the block of one size) and, when it has `groups`, `point_groups` (the
    landmark-schema group of each keypoint). input: `raw`, the raw decode scores (B, P).
    """
    scores = map_scores(np.asarray(input["raw"], dtype=np.float32), params["score_map"], params.get("point_groups"))
    return {"scores": scores.astype(np.float64).tolist()}
