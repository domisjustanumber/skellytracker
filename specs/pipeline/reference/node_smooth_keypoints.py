"""Reference implementation of the pipeline section node.smooth_keypoints (draft).

Note:

- Section ID: node.smooth_keypoints.
- Source: skellytracker/core/temporal_processing/keypoint_filtering.py (apply_one_euro_filter,
  apply_kalman_filter) and skellytracker/core/temporal_processing/keypoint_reset_policy.py
  (KeypointResetPolicy.should_reset). The reset of this section clears the filter state. Today the
  reset policy resets the temporal state of a detector.
- Imported section modules: none.

A case is one sequence of frames. Each frame is a list of instance rows, and each row is a list of
points [x, y]. NaN is a missing value. A frame that is null is an empty input. The node runs on it
with each point missing, after the first frame that is not null.
"""

from __future__ import annotations

import math
from typing import Any

DEFAULTS = {
    "filter": "one_euro",
    "min_cutoff": 1.0,
    "beta": 0.0,
    "d_cutoff": 1.0,
    "process_noise_pos": 1.0,
    "process_noise_vel": 0.1,
    "measurement_noise": 10.0,
    "max_gap_frames": None,
    "max_velocity": None,
    "max_consecutive_misses": None,
    "backoff_multiplier": 2.0,
    "max_backoff_misses": None,
}
FILTER_PARAMS = {
    "one_euro": ("min_cutoff", "beta", "d_cutoff"),
    "kalman": ("process_noise_pos", "process_noise_vel", "measurement_noise"),
}
BACKOFF_PARAMS = ("backoff_multiplier", "max_backoff_misses")
RUNNING_MODES = ("image", "video", "live")


def resolve(params: dict[str, Any]) -> dict[str, Any]:
    """Return the params with their defaults, or refuse them (node.smooth_keypoints, Validation rules)."""
    unknown = sorted(set(params) - set(DEFAULTS))
    if unknown:
        raise ValueError(f"unknown params {unknown}")
    resolved = {**DEFAULTS, **params}
    if resolved["filter"] not in FILTER_PARAMS:
        raise ValueError(f"unknown filter {resolved['filter']!r}")
    for name, names in FILTER_PARAMS.items():
        written = [key for key in names if key in params]
        if name != resolved["filter"] and written:
            raise ValueError(f"V-node.smooth_keypoints-1: the filter {resolved['filter']} does not use {written}")
    if resolved["max_consecutive_misses"] is None and any(key in params for key in BACKOFF_PARAMS):
        raise ValueError("V-node.smooth_keypoints-2: the back-off params need max_consecutive_misses")
    return resolved


def alpha(cutoff: float, dt: float) -> float:
    """The smoothing factor of a low-pass filter: 1 / (1 + 1 / (2 pi cutoff dt)) (node.smooth_keypoints)."""
    return 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))


def initial_covariance(p: dict[str, Any]) -> list[list[float]]:
    """P_init = diag(10 measurement_noise, 100 process_noise_vel) (node.smooth_keypoints)."""
    return [[p["measurement_noise"] * 10.0, 0.0], [0.0, p["process_noise_vel"] * 100.0]]


def new_point(xy: list[float], p: dict[str, Any]) -> dict[str, Any]:
    """The state of one point on the first frame of its row (node.smooth_keypoints)."""
    valid = not (math.isnan(xy[0]) or math.isnan(xy[1]))
    return {
        "pos": [xy[0], xy[1]] if valid else [math.nan, math.nan],
        "d": [0.0, 0.0],
        "v": [0.0, 0.0],
        "P": [initial_covariance(p), initial_covariance(p)],
        "missed": 0 if valid else 1,
    }


def one_euro_axis(z: float, est: float, d: float, dt: float, p: dict[str, Any]) -> tuple[float, float]:
    """One one-euro update of one axis. Return the new estimate and derivative (node.smooth_keypoints)."""
    a_d = alpha(p["d_cutoff"], dt)
    d = a_d * (z - est) / dt + (1.0 - a_d) * d
    a = alpha(p["min_cutoff"] + p["beta"] * abs(d), dt)
    return a * z + (1.0 - a) * est, d


def kalman_predict(est: float, v: float, P: list[list[float]], dt: float, p: dict[str, Any]) -> tuple[float, list[list[float]]]:
    """Predict one axis: est + v dt and F P F^T + Q, F = [[1, dt], [0, 1]] (node.smooth_keypoints)."""
    p01 = P[0][1] + dt * P[1][1]
    p00 = P[0][0] + dt * P[1][0] + dt * p01 + p["process_noise_pos"]
    return est + v * dt, [[p00, p01], [P[1][0] + dt * P[1][1], P[1][1] + p["process_noise_vel"]]]


def kalman_update(pred: float, v: float, P: list[list[float]], z: float, p: dict[str, Any]) -> tuple[float, float, list[list[float]]]:
    """Update one axis with the measurement z, H = [1, 0] (node.smooth_keypoints)."""
    s = P[0][0] + p["measurement_noise"]
    k0, k1 = P[0][0] / s, P[1][0] / s
    innovation = z - pred
    covariance = [
        [(1.0 - k0) * P[0][0], (1.0 - k0) * P[0][1]],
        [P[1][0] - k1 * P[0][0], P[1][1] - k1 * P[0][1]],
    ]
    return pred + k0 * innovation, v + k1 * innovation, covariance


def step_point(s: dict[str, Any], xy: list[float], dt: float, p: dict[str, Any]) -> list[float]:
    """Filter one point of a row that has a state. Change s and return [x, y] (node.smooth_keypoints)."""
    x, y = xy
    has_est = not math.isnan(s["pos"][0])
    detected = not (math.isnan(x) or math.isnan(y))
    if detected and has_est and p["max_velocity"] is not None:
        distance = math.sqrt((x - s["pos"][0]) ** 2 + (y - s["pos"][1]) ** 2)
        detected = distance <= p["max_velocity"] * dt
    s["missed"] = 0 if detected else s["missed"] + 1
    gap = p["max_gap_frames"]
    hold = not detected and has_est and gap is not None and s["missed"] <= gap
    if p["filter"] == "one_euro":
        if detected and has_est:
            out = []
            for axis, z in enumerate((x, y)):
                estimate, s["d"][axis] = one_euro_axis(z, s["pos"][axis], s["d"][axis], dt, p)
                out.append(estimate)
        elif detected:
            out = [x, y]
        elif hold:
            out = list(s["pos"])
        else:
            out = [math.nan, math.nan]
        s["pos"] = out
        return out
    if not has_est:
        s["v"] = [0.0, 0.0]
        s["P"] = [initial_covariance(p), initial_covariance(p)]
        s["pos"] = [x, y] if detected else [math.nan, math.nan]
        return list(s["pos"])
    predicted = [kalman_predict(s["pos"][axis], s["v"][axis], s["P"][axis], dt, p) for axis in (0, 1)]
    s["P"] = [covariance for _, covariance in predicted]
    if detected:
        for axis, z in enumerate((x, y)):
            s["pos"][axis], s["v"][axis], s["P"][axis] = kalman_update(predicted[axis][0], s["v"][axis], s["P"][axis], z, p)
    elif hold:
        s["pos"] = [position for position, _ in predicted]
    else:
        s["pos"], s["v"] = [math.nan, math.nan], [0.0, 0.0]
    return list(s["pos"])


def miss_limit(resets: int, p: dict[str, Any]) -> float:
    """max_consecutive_misses x backoff_multiplier^resets, at most max_backoff_misses (node.smooth_keypoints)."""
    limit = p["max_consecutive_misses"] * p["backoff_multiplier"] ** resets
    return limit if p["max_backoff_misses"] is None else min(limit, p["max_backoff_misses"])


def frame_steps(input: dict[str, Any]) -> list[float]:
    """The dt of each frame, in frames: 1 in video, the timestamp step / frame_interval_ms in live (node.smooth_keypoints)."""
    frames = input["frames"]
    if input["running_mode"] != "live":
        return [1.0] * len(frames)
    stamps, interval = input["timestamps_ms"], input["frame_interval_ms"]
    if len(stamps) != len(frames) or not interval > 0:
        raise ValueError("live needs one timestamp_ms for each frame and a frame_interval_ms > 0")
    steps = [math.nan]
    for last, stamp in zip(stamps, stamps[1:]):  # noqa: B905 (one item shorter)
        if not stamp > last:
            raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase from frame to frame")
        steps.append((stamp - last) / interval)
    return steps


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Smooth a sequence of keypoint frames (node.smooth_keypoints, Behaviour).

    input holds running_mode, frames, and in live timestamps_ms and frame_interval_ms. The result
    holds keypoints, one output frame for each input frame.
    """
    p = resolve(params)
    if input["running_mode"] not in RUNNING_MODES:
        raise ValueError(f"unknown running_mode {input['running_mode']!r}")
    if input["running_mode"] == "image":
        return {"keypoints": input["frames"]}
    rows: dict[int, Any] = {}
    misses: dict[int, int] = {}
    resets: dict[int, int] = {}
    shape: list[int] = []
    output = []
    for frame, dt in zip(input["frames"], frame_steps(input)):  # noqa: B905 (the lengths are equal)
        if frame is None and not shape:
            output.append(None)
            continue
        if frame is None:
            frame = [[[math.nan, math.nan] for _ in range(shape[1])] for _ in range(shape[0])]
        shape = [len(frame), len(frame[0])]
        out_frame = []
        for i, row in enumerate(frame):
            if rows.get(i) is None:
                rows[i] = [new_point(xy, p) for xy in row]
                out_frame.append([list(xy) for xy in row])
            else:
                out_frame.append([step_point(s, xy, dt, p) for s, xy in zip(rows[i], row)])  # noqa: B905
            if any(not (math.isnan(x) or math.isnan(y)) for x, y in row):
                misses[i], resets[i] = 0, 0
            else:
                misses[i] = misses.get(i, 0) + 1
            if p["max_consecutive_misses"] is not None and misses[i] >= miss_limit(resets.get(i, 0), p):
                rows[i], misses[i], resets[i] = None, 0, resets.get(i, 0) + 1
        output.append(out_frame)
    return {"keypoints": output}
