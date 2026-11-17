"""The node type ``mediapipe_tasks``: one MediaPipe Tasks landmarker for each camera.

Implements: node.mediapipe_tasks

The load functions (``output_info``, ``missing_extra``) import no ``mediapipe``. The runner
imports it when it makes the landmarker.
"""
from __future__ import annotations

import functools
import importlib.util
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from numpy.typing import NDArray

from skellytracker.core.pipelines.config import MediapipeTasksParams
from skellytracker.core.pipelines.values import Group, InstanceKeypoints, PortInfo

READS_EMPTY: frozenset[str] = frozenset()
TEMPORAL_IN: tuple[str, ...] = ("video", "live")
"""The running modes in which the node is a temporal node: the landmarker mode ``VIDEO``."""
EXTRA = "mediapipe"
"""The optional extra of ``pyproject.toml`` that the node needs."""

_ASSETS = Path(__file__).parents[2] / "detectors" / "keypoint_detectors" / "mediapipe"
_PART_FILES = {"body": "body/mediapipe_body.yaml", "hand": "hands/mediapipe_hand.yaml", "face": "face/mediapipe_face_contour.yaml"}
_FACE = tuple(f"face_{i:04d}" for i in range(478))
_HOLISTIC = (("body", "body"), ("right_hand", "hand"), ("left_hand", "hand"), ("face", "face"))
# variant: (landmarker class, name part of the options, result field), MediaPipe 1.2.2.
_SINGLE = {
    "body": ("PoseLandmarker", "pose", "pose_landmarks"),
    "hand": ("HandLandmarker", "hand", "hand_landmarks"),
    "face": ("FaceLandmarker", "face", "face_landmarks"),
}
_TIMESTAMP_RULE = "V-node.smooth_keypoints-3"


def missing_extra() -> str | None:
    """Return ``EXTRA`` when MediaPipe is not installed, else ``None``."""
    return None if importlib.util.find_spec("mediapipe") is not None else EXTRA


@functools.cache
def _part(part: str) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    """Return the point names and the connections of one part, from its MediaPipe YAML file."""
    data = yaml.safe_load((_ASSETS / _PART_FILES[part]).read_text(encoding="utf-8"))
    # The face file names only the 136 contour points. The landmarker gives all 478.
    names = _FACE if part == "face" else tuple(data["tracked_points"])
    return names, tuple((a, b) for a, b in data.get("connections", []))


def _layout(node_id: str, variant: str) -> tuple[tuple[str, str], ...]:
    """Return ``(group, part)`` of each group, in column order."""
    return _HOLISTIC if variant == "holistic" else ((node_id, variant),)


def output_info(
    node_id: str, params: MediapipeTasksParams, inputs: dict[str, PortInfo] | None = None,
) -> tuple[dict[str, PortInfo], list[dict[str, Any]]]:
    """Return the facts of the port ``keypoints``, and no warning. It loads no MediaPipe."""
    names: list[str] = []
    groups: list[Group] = []
    edges: list[tuple[str, str]] = []
    for group, part in _layout(node_id, params.variant):
        points, connections = _part(part)
        bad = [p for p in points if "/" in p or any(c.isspace() for c in p)]
        if bad:
            raise ValueError(f"V-pipeline.graph-8: {node_id}: the MediaPipe point name {bad[0]!r} has `/` or whitespace")
        groups.append(Group(group, len(names), len(points), None))
        names += [f"{group}/{p}" for p in points]
        edges += [(f"{group}/{a}", f"{group}/{b}") for a, b in connections]
    info = PortInfo(
        port_type="keypoints", max_instances=params.max_instances, instance_source=node_id,
        point_names=tuple(names), groups=tuple(groups), geometry="3d", depth_unit="pixel", edges=tuple(edges),
    )
    return {"keypoints": info}, []


class MediapipeTasksRunner:
    """The landmarker of one camera.

    ``running_mode`` is the running mode of the run: ``image`` gives the Tasks mode ``IMAGE``,
    ``video`` and ``live`` give ``VIDEO``. ``node_id`` is the group name of the variants ``body``,
    ``hand`` and ``face``. Without it, the group has the name of the variant. Call ``close()``. A
    runner that the garbage collector frees closes its landmarker on a separate thread (ADR-X6S9).
    The runner has no reset and no back-off (ADR-6JWJ).
    """

    def __init__(self, params: MediapipeTasksParams, running_mode: str, node_id: str | None = None) -> None:
        self.point_names = output_info(node_id or params.variant, params)[0]["keypoints"].point_names
        self.max_instances = params.max_instances
        self._video = running_mode != "image"
        self._last_timestamp_ms = -math.inf
        self._last_mediapipe_ms = -1
        self._closed = False
        self._holistic: Any = None
        if params.variant == "holistic":
            from skellytracker.core.detectors.mediapipe_holistic import HolisticRunner

            self._holistic = HolisticRunner(
                "video" if self._video else "image", params.min_detection_score, params.min_presence_score,
            )
            return
        from mediapipe.tasks.python import BaseOptions, vision

        from skellytracker.core.detectors.keypoint_detectors.mediapipe import mediapipe_model_manager as assets
        from skellytracker.core.detectors.keypoint_detectors.mediapipe.landmarker_lifetime import close_on_collect

        cls, part, self._field = _SINGLE[params.variant]
        if params.variant == "body":
            path = assets.get_pose_model_path(assets.MediapipePoseModelComplexity(params.size))
        else:
            path = assets.get_hand_model_path() if params.variant == "hand" else assets.get_face_model_path()
        options = getattr(vision, f"{cls}Options")(**{
            "base_options": BaseOptions(model_asset_path=str(path)),
            "running_mode": vision.RunningMode.VIDEO if self._video else vision.RunningMode.IMAGE,
            f"num_{part}s": params.max_instances,
            f"min_{part}_detection_confidence": params.min_detection_score,
            f"min_{part}_presence_confidence": params.min_presence_score,
            "min_tracking_confidence": params.min_tracking_score,
        })
        self._landmarker = getattr(vision, cls).create_from_options(options)
        self._finalizer = close_on_collect(self, self._landmarker)

    def run(self, image: NDArray[np.uint8], timestamp_ms: float | None = None) -> InstanceKeypoints:
        """Find the landmarks in one BGR image ``(H, W, 3)``.

        In the mode ``VIDEO``, ``timestamp_ms`` must increase from call to call. A refused call
        raises ``ValueError`` before the landmarker call and changes no state. The mode ``IMAGE``
        ignores ``timestamp_ms``.
        """
        if self._closed:
            raise RuntimeError("MediapipeTasksRunner is closed")
        if self._video and (timestamp_ms is None or not timestamp_ms > self._last_timestamp_ms):
            raise ValueError(
                f"{_TIMESTAMP_RULE}: timestamp_ms must increase: got {timestamp_ms} after {self._last_timestamp_ms}"
            )
        if self._holistic is not None:
            found = self._holistic.run(image, timestamp_ms)
            value = InstanceKeypoints(
                self.point_names, found.xyz[..., :2].copy(), found.score, found.score.copy(), found.instance_score, found.present, np.full(1, -1, dtype=np.int64),
                found.xyz[..., 2].copy(),
            )
        else:
            import mediapipe as mp

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image[:, :, ::-1]))
            if self._video:
                # MediaPipe takes integer milliseconds; two frames less than 1 ms apart must not get the same value.
                mediapipe_ms = max(int(timestamp_ms), self._last_mediapipe_ms + 1)  # type: ignore[arg-type]
                result = self._landmarker.detect_for_video(mp_image, mediapipe_ms)
                self._last_mediapipe_ms = mediapipe_ms
            else:
                result = self._landmarker.detect(mp_image)
            h, w = image.shape[:2]
            value = InstanceKeypoints.empty(self.point_names, self.max_instances, "3d")
            for row, landmarks in enumerate(getattr(result, self._field)[: self.max_instances]):
                value.xy[row] = [(lm.x * w, lm.y * h) for lm in landmarks]
                value.z[row] = [lm.z * w for lm in landmarks]  # type: ignore[index]
                value.score[row] = value.raw_score[row] = [1.0 if lm.visibility is None else lm.visibility for lm in landmarks]  # no score map
                value.instance_score[row] = 1.0
                value.present[row] = True
        if self._video:
            self._last_timestamp_ms = timestamp_ms  # type: ignore[assignment]
        return value

    def close(self) -> None:
        """Close the landmarker. A second call does nothing."""
        if self._closed:
            return
        self._closed = True
        if self._holistic is not None:
            self._holistic.close()
        elif self._finalizer.detach() is not None:
            self._landmarker.close()


def make_state(params: MediapipeTasksParams, running_mode: str, node_id: str | None = None) -> MediapipeTasksRunner:
    """Make the state of one camera: its runner. The executor makes one for each camera at start."""
    return MediapipeTasksRunner(params, running_mode, node_id)


def run(
    params: MediapipeTasksParams, inputs: dict[str, Any], state: MediapipeTasksRunner, frame: Any, infos: Any = None,
) -> tuple[dict[str, InstanceKeypoints], MediapipeTasksRunner]:
    """Run the node on one frame of one camera.

    ``state`` is the runner of the camera. It is a native object, so it is mutable, and the same
    object comes back. A refused timestamp raises ``ValueError`` before the landmarker call and
    changes nothing. ``params`` and ``infos`` are not read: no param can change during a run.
    """
    return {"keypoints": state.run(inputs["image"], frame.timestamp_ms)}, state


def close_state(state: MediapipeTasksRunner) -> None:
    """Close the runner of one camera. The executor calls it for each camera at ``close()``."""
    state.close()
