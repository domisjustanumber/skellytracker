"""Reference implementation of the section post.keypoint.decode.simcc, as the proposal simcc-score-rule changes it.

Section ID: post.keypoint.decode.simcc (section file specs/model-sidecar/post/keypoint/decode-simcc.md).
Proposal: simcc-score-rule of OpenMMLab-Exporter, part 3.
Target file in skellytracker: specs/model-sidecar/reference/post_keypoint_decode_simcc.py.
Imported sections: none. Fixtures: none.

source commit: none (no host code). OpenMMLab-Exporter has no committed host SimCC decode. The
functions come from the text of part 2 of the proposal. The parity run of part 5 loaded version 1
of this file. Versions 2 and 3 change only docstrings: the code is the same.

Vector results: the cases of vectors/post.keypoint.decode.simcc.yaml of the proposal bundle. They are
unverified: no exporter and no skellytracker code implements the proposed rule yet.

The module implements the full section: the argmax bin of each axis, the score, the rule for a
score <= 0, the rule for a NaN raw value and the bin-to-pixel scale. The section is 2D only
(skellytracker ADR-9HBB). The keypoints that it returns are in the model-input pixels of the crop.
The unprojection to the source image is the Inverse of the resize method (section
post.unprojection). It is not in this module.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def peak(simcc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """post.keypoint.decode.simcc: the argmax bin and the peak value of each row.

    `simcc` has the shape (B, P, bins), as float32 raw values. No softmax. On a tie, the bin
    is the lowest index (np.argmax). In a row that holds a NaN, the bin is the lowest index of a
    NaN (np.argmax), and the peak is NaN (np.max). Returns (bin, peak), each of shape (B, P).
    """
    return np.argmax(simcc, axis=-1), np.max(simcc, axis=-1)


def keypoint_score(peak_x: np.ndarray, peak_y: np.ndarray) -> np.ndarray:
    """post.keypoint.decode.simcc: the score is peak_y where peak_x > peak_y, else peak_x.

    This is min(peak_x, peak_y) when no peak is NaN. A comparison with a NaN is false. Thus a NaN
    peak_x gives the score NaN, and a NaN peak_y with a number peak_x gives the score peak_x.
    """
    return np.where(peak_x > peak_y, peak_y, peak_x)


def mark_low_scores(bins: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """post.keypoint.decode.simcc: where score <= 0, each axis of the keypoint gets the bin -1.

    `bins` has the shape (B, P, 2). The comparison is not strict: a score of exactly 0 gets the
    bin -1. A NaN score is not <= 0, so its bins stay.
    """
    marked = np.array(bins, dtype=np.int64)
    marked[scores <= 0] = -1
    return marked


def bin_to_pixel(bins: np.ndarray, extent: int, bin_count: int) -> np.ndarray:
    """post.keypoint.decode.simcc: pixel = bin * extent / bin_count, in float64.

    `extent` is the model input width for simcc_x and the height for simcc_y. Bin 0 gives
    pixel 0. The bin -1 gives -extent / bin_count.
    """
    return bins.astype(np.float64) * extent / bin_count


def decode(simcc_x: np.ndarray, simcc_y: np.ndarray, target_size: Any) -> dict[str, np.ndarray]:
    """post.keypoint.decode.simcc: the 2D decode of one batch of crops.

    `target_size` is [height, width] of the model input. Returns the bins (B, P, 2), the
    keypoints (B, P, 2) and the scores (B, P).
    """
    height, width = int(target_size[0]), int(target_size[1])
    if simcc_x.ndim != 3 or simcc_y.ndim != 3 or simcc_x.shape[:2] != simcc_y.shape[:2]:
        raise ValueError("simcc_x and simcc_y must have the shapes (B, P, bins) with the same B and P")
    bin_x, peak_x = peak(simcc_x)
    bin_y, peak_y = peak(simcc_y)
    scores = keypoint_score(peak_x, peak_y)
    bins = mark_low_scores(np.stack([bin_x, bin_y], axis=-1), scores)
    keypoints = np.stack(
        [
            bin_to_pixel(bins[..., 0], width, simcc_x.shape[-1]),
            bin_to_pixel(bins[..., 1], height, simcc_y.shape[-1]),
        ],
        axis=-1,
    )
    return {"bins": bins, "keypoints": keypoints, "scores": scores}


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """post.keypoint.decode.simcc, Behaviour: one case.

    params: `target_size` [height, width]. input: `simcc_x` and `simcc_y`, each (B, P, bins).
    """
    simcc_x = np.asarray(input["simcc_x"], dtype=np.float32)
    simcc_y = np.asarray(input["simcc_y"], dtype=np.float32)
    result = decode(simcc_x, simcc_y, params["target_size"])
    return {
        "bins": result["bins"].tolist(),
        "keypoints": result["keypoints"].tolist(),
        "scores": result["scores"].astype(np.float64).tolist(),
    }
