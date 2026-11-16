"""Run the MediaPipe Tasks ``HolisticLandmarker`` on the frames of one camera.

The variant ``holistic`` of the pipeline node ``mediapipe_tasks`` wraps this runner
(``specs/pipeline/nodes/mediapipe_tasks.md``). Holistic is single person, so each
output has one row. In ``video`` mode, one runner keeps the state of one camera.
"""
from __future__ import annotations

import math
import threading
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HolisticLandmarker, HolisticLandmarkerOptions, RunningMode
from numpy.typing import NDArray

from skellytracker.core.detectors.keypoint_detectors._schema_loader import load_point_names
from skellytracker.core.detectors.keypoint_detectors.mediapipe.mediapipe_model_manager import (
    get_holistic_model_path,
)

_ASSETS = Path(__file__).parent / "keypoint_detectors" / "mediapipe"
_BODY = load_point_names(_ASSETS / "body" / "mediapipe_body.yaml")
_HAND = load_point_names(_ASSETS / "hands" / "mediapipe_hand.yaml")
_FACE = tuple(f"face_{i:04d}" for i in range(478))

# (group, result field, point names), in the freemocap order of the node spec.
_PARTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("body", "pose_landmarks", _BODY),
    ("right_hand", "right_hand_landmarks", _HAND),
    ("left_hand", "left_hand_landmarks", _HAND),
    ("face", "face_landmarks", _FACE),
)

POINT_NAMES: tuple[str, ...] = tuple(f"{group}/{name}" for group, _, names in _PARTS for name in names)
"""The 553 point names ``<group>/<name>``: body, right hand, left hand, face."""

GROUPS: tuple[tuple[str, int, int], ...] = tuple(
    (group, sum(len(n) for _, _, n in _PARTS[:i]), len(names)) for i, (group, _, names) in enumerate(_PARTS)
)
"""``(name, start, count)`` of each group, in column order."""

GEOMETRY = "3d"
DEPTH_UNIT = "pixel"

# Holistic gives no visibility for the hand and face landmarks (MediaPipe 1.2.2).
_NO_VISIBILITY_SCORE = 1.0


@dataclass(frozen=True)
class HolisticKeypoints:
    """The keypoints of one frame, with the fields of an ``InstanceKeypoints`` value and ``I`` = 1.

    The columns follow ``POINT_NAMES``. A missing point has NaN coordinates and the score 0.
    """

    xyz: NDArray[np.float64]
    """``(1, P, 3)`` in source-image pixels. z is the MediaPipe depth multiplied by the image width."""
    score: NDArray[np.float64]
    """``(1, P)``: the landmark visibility."""
    present: NDArray[np.bool_]
    """``(1,)``: true when Holistic found at least one part."""
    instance_score: NDArray[np.float64]
    """``(1,)``: 1.0 for a present row, 0 for a padding row."""


def _close_off_thread(landmarker: HolisticLandmarker) -> None:
    # The garbage collector can run on the landmarker's own worker thread; close() waits on that thread.
    try:
        threading.Thread(target=landmarker.close, daemon=True).start()
    except RuntimeError:
        pass  # Interpreter shutdown: MediaPipe ignores its calls from then on.


class HolisticRunner:
    """One MediaPipe ``HolisticLandmarker`` in the running mode ``image`` or ``video``.

    The thresholds go to the Holistic options of the node spec. Each other option keeps its
    Tasks default. Call ``close()`` or use the runner as a context manager. A runner that the
    garbage collector frees closes its landmarker on a separate thread.
    """

    def __init__(
        self,
        running_mode: Literal["image", "video"],
        min_detection_score: float = 0.5,
        min_presence_score: float = 0.5,
    ) -> None:
        self.running_mode = running_mode
        options = HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(get_holistic_model_path())),
            running_mode=RunningMode.VIDEO if running_mode == "video" else RunningMode.IMAGE,
            min_face_detection_confidence=min_detection_score,
            min_pose_detection_confidence=min_detection_score,
            min_face_landmarks_confidence=min_presence_score,
            min_pose_landmarks_confidence=min_presence_score,
            min_hand_landmarks_confidence=min_presence_score,
        )
        self._landmarker = HolisticLandmarker.create_from_options(options)
        self._finalizer = weakref.finalize(self, _close_off_thread, self._landmarker)
        self._finalizer.atexit = False
        self._last_timestamp_ms = -math.inf
        self._last_mediapipe_ms = -1

    def run(self, image: NDArray[np.uint8], timestamp_ms: float | None = None) -> HolisticKeypoints:
        """Detect the landmarks in one BGR image ``(H, W, 3)``.

        In ``video`` mode, ``timestamp_ms`` is required and must increase from call to call.
        A refused call changes no state. ``image`` mode ignores ``timestamp_ms``.
        """
        if not self._finalizer.alive:
            raise RuntimeError("HolisticRunner is closed")
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if self.running_mode == "video":
            if timestamp_ms is None or not timestamp_ms > self._last_timestamp_ms:
                raise ValueError(
                    f"timestamp_ms must increase: got {timestamp_ms} after {self._last_timestamp_ms}"
                )
            # MediaPipe takes integer milliseconds; two frames less than 1 ms apart must not get the same value.
            mediapipe_ms = max(int(timestamp_ms), self._last_mediapipe_ms + 1)
            result = self._landmarker.detect_for_video(mp_image, mediapipe_ms)
            self._last_timestamp_ms, self._last_mediapipe_ms = timestamp_ms, mediapipe_ms
        else:
            result = self._landmarker.detect(mp_image)
        h, w = image.shape[:2]
        return _to_keypoints(result, w, h)

    def close(self) -> None:
        """Close the landmarker. A second call does nothing."""
        if self._finalizer.detach() is not None:
            self._landmarker.close()

    def __enter__(self) -> HolisticRunner:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _to_keypoints(result: Any, w: int, h: int) -> HolisticKeypoints:
    xyz = np.full((1, len(POINT_NAMES), 3), np.nan)
    score = np.zeros((1, len(POINT_NAMES)))
    for (_, field, _), (_, start, count) in zip(_PARTS, GROUPS, strict=True):
        landmarks = getattr(result, field)
        if not landmarks:
            continue
        cols = slice(start, start + count)
        xyz[0, cols] = [(lm.x * w, lm.y * h, lm.z * w) for lm in landmarks]
        score[0, cols] = [_NO_VISIBILITY_SCORE if lm.visibility is None else lm.visibility for lm in landmarks]
    present = np.array([bool(np.isfinite(xyz[0, :, 0]).any())])
    return HolisticKeypoints(xyz=xyz, score=score, present=present, instance_score=present.astype(np.float64))
