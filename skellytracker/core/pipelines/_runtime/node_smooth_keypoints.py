"""The node ``smooth_keypoints``: a one-euro or a Kalman filter on the points of each instance row.

Implements: node.smooth_keypoints
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from skellytracker.core.pipelines._runtime.context import FrameContext
from skellytracker.core.pipelines.config import SmoothKeypointsParams
from skellytracker.core.pipelines.values import InstanceKeypoints, PortInfo

# After its first input, an empty input is a miss for the gap hold and the reset (Behaviour step 2).
READS_EMPTY: frozenset[str] = frozenset({"keypoints"})
# The initial velocity variance of the Kalman filter, in (px/s)²: 10 (px/frame)² at 30 fps.
INITIAL_VELOCITY_VARIANCE = 9000.0


@dataclass(frozen=True)
class SmoothKeypointsState:
    """The state of one camera. ``run`` makes a new state at each call and changes no array in place."""

    last_t: float
    """The ``timestamp_ms`` of the last frame that the node ran on."""
    has_state: NDArray[np.bool_]
    """``(I,)``: false for a row whose state is empty."""
    est: NDArray[np.float64]
    """``(I, P, 2)``: the estimate of x and y. NaN for a point with no estimate."""
    d: NDArray[np.float64]
    """``(I, P, 2)``: the one-euro derivative, in pixels per second."""
    v: NDArray[np.float64]
    """``(I, P, 2)``: the Kalman velocity, in pixels per second."""
    cov: NDArray[np.float64]
    """``(I, P, 2, 4)``: the Kalman covariance of each axis, as ``cov00, cov01, cov10, cov11``."""
    t_detected: NDArray[np.float64]
    """``(I, P)``: the time of the last detection of each point. NaN when empty."""
    t_valid: NDArray[np.float64]
    """``(I,)``: the time of the last frame on which the input row had a valid point."""
    last_score: NDArray[np.float64]
    """``(I,)``: the ``instance_score`` of the last present input row. 0 when the row was never present."""
    last_track: NDArray[np.int64]
    """``(I,)``: the ``track_ids`` value of the last present input row. -1 when the row was never present."""


def output_info(
    node_id: str, params: SmoothKeypointsParams, inputs: dict[str, PortInfo]
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Return the facts of the output ``keypoints``: those of the input. The params model checks V-node.smooth_keypoints-1.

    Implements: node.smooth_keypoints
    """
    return {"keypoints": inputs["keypoints"]}, []


def _initial_cov(params: SmoothKeypointsParams, shape: tuple[int, ...]) -> NDArray[np.float64]:
    """Return cov_init = diag(10 measurement_noise, 9000) for each axis of each point (step 5)."""
    cov = np.zeros((*shape, 4))
    cov[..., 0] = params.measurement_noise * 10.0
    cov[..., 3] = INITIAL_VELOCITY_VARIANCE
    return cov


def _one_euro(params: SmoothKeypointsParams, state: SmoothKeypointsState, z: Any, dt: float, detected: Any, hold: Any) -> tuple[Any, ...]:
    """Return ``(est, d, v, cov)`` after the filter ``one_euro`` (step 7). The masks have the shape ``(I, P, 1)``."""
    a_d = 1.0 / (1.0 + 1.0 / (2.0 * math.pi * params.d_cutoff * dt))
    d = a_d * (z - state.est) / dt + (1.0 - a_d) * state.d
    a = 1.0 / (1.0 + 1.0 / (2.0 * math.pi * (params.min_cutoff + params.beta * np.abs(d)) * dt))
    update = detected & ~np.isnan(state.est[..., :1])
    est = np.where(update, a * z + (1.0 - a) * state.est, np.where(detected, z, np.where(hold, state.est, np.nan)))
    return est, np.where(update, d, state.d), state.v, state.cov


def _kalman(params: SmoothKeypointsParams, state: SmoothKeypointsState, z: Any, dt: float, detected: Any, hold: Any) -> tuple[Any, ...]:
    """Return ``(est, d, v, cov)`` after the filter ``kalman`` (step 8). The masks have the shape ``(I, P, 1)``."""
    c00, c01, c10, c11 = (state.cov[..., index] for index in range(4))
    p01 = c01 + dt * c11
    p00 = c00 + dt * c10 + dt * p01 + params.process_noise_pos * dt
    p11 = c11 + params.process_noise_vel * dt
    p10 = c10 + dt * c11
    predicted = state.est + state.v * dt
    s = p00 + params.measurement_noise
    g0, g1 = p00 / s, p10 / s
    innovation = z - predicted
    has_est = ~np.isnan(state.est[..., :1])
    est = np.where(
        has_est,
        np.where(detected, predicted + g0 * innovation, np.where(hold, predicted, np.nan)),
        np.where(detected, z, np.nan),
    )
    v = np.where(has_est, np.where(detected, state.v + g1 * innovation, np.where(hold, state.v, 0.0)), 0.0)
    updated = np.stack([(1.0 - g0) * p00, (1.0 - g0) * p01, p10 - g1 * p00, p11 - g1 * p01], axis=-1)
    cov = np.where(
        has_est[..., None],
        np.where(detected[..., None], updated, np.stack([p00, p01, p10, p11], axis=-1)),
        _initial_cov(params, state.est.shape),
    )
    return est, state.d, v, cov


def run(
    params: SmoothKeypointsParams, inputs: dict[str, Any], state: SmoothKeypointsState | None, frame: FrameContext, infos: Any = None
) -> tuple[dict[str, InstanceKeypoints], SmoothKeypointsState | None]:
    """Filter the points of one frame. Return the output and the new state.

    Implements: node.smooth_keypoints

    The function refuses a ``timestamp_ms`` that does not increase with a ``ValueError`` that
    starts with ``V-node.smooth_keypoints-3``.
    """
    keypoints: InstanceKeypoints = inputs["keypoints"]
    if frame.running_mode == "image":
        return {"keypoints": keypoints}, None
    if state is None and not keypoints.present.any():
        return {"keypoints": keypoints}, None  # before the first input that is not empty (step 2)
    t = frame.timestamp_ms
    if t is None:
        raise ValueError("the node smooth_keypoints needs the timestamp_ms of the frame")
    if state is not None and not t > state.last_t:
        raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase from frame to frame")
    rows, points = keypoints.score.shape
    if state is None:
        state = SmoothKeypointsState(
            last_t=math.nan, has_state=np.zeros(rows, dtype=bool), est=np.full((rows, points, 2), np.nan),
            d=np.zeros((rows, points, 2)), v=np.zeros((rows, points, 2)), cov=_initial_cov(params, (rows, points, 2)),
            t_detected=np.full((rows, points), np.nan), t_valid=np.full(rows, np.nan),
            last_score=np.zeros(rows), last_track=np.full(rows, -1, dtype=np.int64),
        )
    dt = (t - state.last_t) / 1000.0
    # A row that is not present has only missing points.
    z = np.where(keypoints.present[:, None, None], keypoints.xy, np.nan)
    valid = ~np.isnan(z).any(axis=2)
    with np.errstate(invalid="ignore", divide="ignore"):
        # Step 6: the rows with a state.
        has_est = ~np.isnan(state.est[..., 0])
        detected = valid
        if params.max_velocity is not None:
            distance = np.sqrt((z[..., 0] - state.est[..., 0]) ** 2 + (z[..., 1] - state.est[..., 1]) ** 2)
            near = distance <= params.max_velocity * (t - state.t_detected) / 1000.0
            detected = np.where(valid & has_est & ~np.isnan(state.t_detected), near, valid)
        t_detected = np.where(detected, t, state.t_detected)
        hold = ~detected & has_est & (params.max_gap_ms is not None) & (t - t_detected <= (params.max_gap_ms or 0.0))
        step = _one_euro if params.filter == "one_euro" else _kalman
        est, d, v, cov = step(params, state, z, dt, detected[..., None], hold[..., None])
    # Step 5: the first frame of a row. The output is the input.
    new = ~state.has_state
    first = new[:, None, None]
    xy = np.where(first, z, est)
    est = np.where(first, np.where(valid[..., None], z, np.nan), est)
    d = np.where(first, 0.0, d)
    v = np.where(first, 0.0, v)
    cov = np.where(first[..., None], _initial_cov(params, est.shape), cov)
    t_detected = np.where(new[:, None], np.where(valid, t, np.nan), t_detected)
    # Step 9: the reset.
    row_valid = valid.any(axis=1)
    t_valid = np.where(new | row_valid, t, state.t_valid)
    reset = np.zeros(rows, dtype=bool)
    if params.reset_after_ms is not None:
        reset = ~row_valid & (t - t_valid >= params.reset_after_ms)
    # Step 10: the rows.
    last_score = np.where(keypoints.present, keypoints.instance_score, state.last_score)
    last_track = np.where(keypoints.present, keypoints.track_ids, state.last_track)
    present = ~np.isnan(xy).any(axis=2).all(axis=1)
    out = InstanceKeypoints(
        keypoints.point_names, np.where(present[:, None, None], xy, np.nan), np.where(present[:, None], keypoints.score, 0.0),
        np.where(present[:, None], keypoints.raw_score, 0.0), np.where(present, last_score, 0.0),
        present, np.where(present, last_track, -1),
        None if keypoints.z is None else np.where(present[:, None], keypoints.z, np.nan),  # z passes through
    )
    new_state = SmoothKeypointsState(
        last_t=float(t), has_state=~reset, est=est, d=d, v=v, cov=cov, t_detected=t_detected, t_valid=t_valid,
        last_score=last_score, last_track=last_track,
    )
    return {"keypoints": out}, new_state
