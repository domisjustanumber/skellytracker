"""Reference implementation of the pipeline section node.smooth_keypoints (draft).

Note:

- Section ID: node.smooth_keypoints.
- Source: skellytracker/core/temporal_processing/keypoint_filtering.py (apply_one_euro_filter,
  apply_kalman_filter) and skellytracker/core/temporal_processing/keypoint_reset_policy.py
  (KeypointResetPolicy.should_reset). This section uses time units: dt in seconds from
  `timestamp_ms`, and durations in milliseconds. The reset of this section clears the filter state
  after a time with no valid point. Today the reset policy resets the temporal state of a detector
  after a number of misses, with a back-off.
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
    "process_noise_pos": 30.0,
    "process_noise_vel": 2700.0,
    "measurement_noise": 10.0,
    "max_gap_ms": None,
    "max_velocity": None,
    "reset_after_ms": None,
}
FILTER_PARAMS = {
    "one_euro": ("min_cutoff", "beta", "d_cutoff"),
    "kalman": ("process_noise_pos", "process_noise_vel", "measurement_noise"),
}
# The initial velocity variance of the Kalman filter, in (px/s)²: 10 (px/frame)² at 30 fps.
INITIAL_VELOCITY_VARIANCE = 9000.0
# The run parameter `fps` (pipeline.running): the timestamps of a `video` run with no timestamps.
DEFAULT_FPS = 30.0
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
    return resolved


def alpha(cutoff: float, dt: float) -> float:
    """The smoothing factor of a low-pass filter: 1 / (1 + 1 / (2 pi cutoff dt)), cutoff in Hz, dt in s."""
    return 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))


def initial_cov(p: dict[str, Any]) -> list[list[float]]:
    """cov_init = diag(10 measurement_noise, INITIAL_VELOCITY_VARIANCE) (node.smooth_keypoints)."""
    return [[p["measurement_noise"] * 10.0, 0.0], [0.0, INITIAL_VELOCITY_VARIANCE]]


def valid(xy: list[float]) -> bool:
    """A point is valid when its x and its y are not NaN (node.smooth_keypoints)."""
    return not (math.isnan(xy[0]) or math.isnan(xy[1]))


def new_point(xy: list[float], t: float, p: dict[str, Any]) -> dict[str, Any]:
    """The state of one point on the first frame of its row (node.smooth_keypoints, step 5)."""
    ok = valid(xy)
    return {
        "pos": [xy[0], xy[1]] if ok else [math.nan, math.nan],
        "d": [0.0, 0.0],
        "v": [0.0, 0.0],
        "cov": [initial_cov(p), initial_cov(p)],
        "t_detected": t if ok else None,
    }


def one_euro_axis(z: float, est: float, d: float, dt: float, p: dict[str, Any]) -> tuple[float, float]:
    """One one-euro update of one axis. Return the new estimate and derivative (node.smooth_keypoints)."""
    a_d = alpha(p["d_cutoff"], dt)
    d = a_d * (z - est) / dt + (1.0 - a_d) * d
    a = alpha(p["min_cutoff"] + p["beta"] * abs(d), dt)
    return a * z + (1.0 - a) * est, d


def kalman_predict(est: float, v: float, cov: list[list[float]], dt: float, p: dict[str, Any]) -> tuple[float, list[list[float]]]:
    """Predict one axis: est + v dt and F cov F^T + noise dt, F = [[1, dt], [0, 1]] (node.smooth_keypoints)."""
    c01 = cov[0][1] + dt * cov[1][1]
    c00 = cov[0][0] + dt * cov[1][0] + dt * c01 + p["process_noise_pos"] * dt
    c11 = cov[1][1] + p["process_noise_vel"] * dt
    return est + v * dt, [[c00, c01], [cov[1][0] + dt * cov[1][1], c11]]


def kalman_update(pred: float, v: float, cov: list[list[float]], z: float, p: dict[str, Any]) -> tuple[float, float, list[list[float]]]:
    """Update one axis with the measurement z, H = [1, 0] (node.smooth_keypoints)."""
    s = cov[0][0] + p["measurement_noise"]
    g0, g1 = cov[0][0] / s, cov[1][0] / s
    innovation = z - pred
    updated = [
        [(1.0 - g0) * cov[0][0], (1.0 - g0) * cov[0][1]],
        [cov[1][0] - g1 * cov[0][0], cov[1][1] - g1 * cov[0][1]],
    ]
    return pred + g0 * innovation, v + g1 * innovation, updated


def step_point(s: dict[str, Any], xy: list[float], t: float, dt: float, p: dict[str, Any]) -> list[float]:
    """Filter one point of a row that has a state. Change s and return [x, y] (node.smooth_keypoints, step 6)."""
    x, y = xy
    has_est = not math.isnan(s["pos"][0])
    detected = valid(xy)
    if detected and has_est and p["max_velocity"] is not None and s["t_detected"] is not None:
        distance = math.sqrt((x - s["pos"][0]) ** 2 + (y - s["pos"][1]) ** 2)
        detected = distance <= p["max_velocity"] * (t - s["t_detected"]) / 1000.0
    if detected:
        s["t_detected"] = t
    gap = p["max_gap_ms"]
    hold = not detected and has_est and gap is not None and s["t_detected"] is not None and t - s["t_detected"] <= gap
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
        s["cov"] = [initial_cov(p), initial_cov(p)]
        s["pos"] = [x, y] if detected else [math.nan, math.nan]
        return list(s["pos"])
    predicted = [kalman_predict(s["pos"][axis], s["v"][axis], s["cov"][axis], dt, p) for axis in (0, 1)]
    s["cov"] = [cov for _, cov in predicted]
    if detected:
        for axis, z in enumerate((x, y)):
            s["pos"][axis], s["v"][axis], s["cov"][axis] = kalman_update(predicted[axis][0], s["v"][axis], s["cov"][axis], z, p)
    elif hold:
        s["pos"] = [position for position, _ in predicted]
    else:
        s["pos"], s["v"] = [math.nan, math.nan], [0.0, 0.0]
    return list(s["pos"])


def timestamps(input: dict[str, Any]) -> list[float]:
    """The timestamp_ms of each frame (node.smooth_keypoints, step 3; pipeline.running, the run parameter fps).

    `live` needs `timestamps_ms`. `video` uses `timestamps_ms` when the case gives it, else
    frame_index × 1000 / fps.
    """
    frames = input["frames"]
    if "timestamps_ms" in input:
        stamps = [float(stamp) for stamp in input["timestamps_ms"]]
    elif input["running_mode"] == "video":
        fps = input.get("fps", DEFAULT_FPS)
        stamps = [index * 1000.0 / fps for index in range(len(frames))]
    else:
        raise ValueError("live needs one timestamp_ms for each frame")
    if len(stamps) != len(frames):
        raise ValueError("a case needs one timestamp_ms for each frame")
    for last, stamp in zip(stamps, stamps[1:]):  # noqa: B905 (one item shorter)
        if not stamp > last:
            raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase from frame to frame")
    return stamps


def run(params: dict[str, Any], input: dict[str, Any]) -> dict[str, Any]:
    """Smooth a sequence of keypoint frames (node.smooth_keypoints, Behaviour).

    input holds running_mode, frames, and timestamps_ms (live) or timestamps_ms or fps (video).
    The result holds keypoints, one output frame for each input frame.
    """
    p = resolve(params)
    if input["running_mode"] not in RUNNING_MODES:
        raise ValueError(f"unknown running_mode {input['running_mode']!r}")
    if input["running_mode"] == "image":
        return {"keypoints": input["frames"]}
    rows: dict[int, Any] = {}
    shape: list[int] = []
    last_t: float | None = None
    output = []
    for frame, t in zip(input["frames"], timestamps(input)):  # noqa: B905 (the lengths are equal)
        if frame is None and not shape:
            output.append(None)
            continue
        dt = math.nan if last_t is None else (t - last_t) / 1000.0
        last_t = t
        if frame is None:
            frame = [[[math.nan, math.nan] for _ in range(shape[1])] for _ in range(shape[0])]
        shape = [len(frame), len(frame[0])]
        out_frame = []
        for i, row in enumerate(frame):
            if rows.get(i) is None:
                rows[i] = {"points": [new_point(xy, t, p) for xy in row], "t_valid": t}
                out_frame.append([list(xy) for xy in row])
            else:
                out_frame.append([step_point(s, xy, t, dt, p) for s, xy in zip(rows[i]["points"], row)])  # noqa: B905
            if any(valid(xy) for xy in row):
                rows[i]["t_valid"] = t
            elif p["reset_after_ms"] is not None and t - rows[i]["t_valid"] >= p["reset_after_ms"]:
                rows[i] = None
        output.append(out_frame)
    return {"keypoints": output}
