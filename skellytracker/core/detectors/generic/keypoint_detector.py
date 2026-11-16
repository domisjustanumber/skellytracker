"""The generic keypoint detector: one keypoint model of the sidecar spec, on a batch of crops or images."""
from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from skellytracker.core.detectors.generic.inference import run_batches
from skellytracker.core.detectors.generic.overlay import OverlayGroup, overlay_groups
from skellytracker.core.detectors.processing.post.keypoint_decode_simcc import decode_simcc
from skellytracker.core.detectors.processing.post.keypoint_schema import derived_points, mark_missing
from skellytracker.core.detectors.processing.post.unprojection import resize_inverse
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image
from skellytracker.core.model_spec.model import SidecarModel


@dataclass(frozen=True)
class KeypointDetections:
    """The keypoints of N crops or images, in source pixels.

    `keypoints` are (N, P, 2) float64 in the order of `keypoint.point_names`, and `scores` are
    (N, P). `derived_keypoints` (N, D, 2) and `derived_scores` (N, D) are in the order of
    `keypoint.derived_points`. A missing point has NaN coordinates and the score 0.
    """

    keypoints: np.ndarray
    scores: np.ndarray
    derived_keypoints: np.ndarray
    derived_scores: np.ndarray


@dataclass
class GenericKeypointDetector:
    """One keypoint model: the sidecar preprocessing, the inference and the sidecar decode.

    `sidecar`, `size` and `precision` give each parameter. `session` is an ONNX Runtime session of
    the artifact of that size and precision, with any batch. The detector has no score threshold:
    it applies only the rule of a missing keypoint. It keeps no state between calls.
    """

    sidecar: SidecarModel
    size: str
    precision: str
    session: Any

    def __post_init__(self) -> None:
        keypoint = self.sidecar.keypoint
        if "keypoint_detector" not in self.sidecar.role or keypoint is None:
            raise ValueError(f"{self.sidecar.model_id} is not a keypoint detector")
        if "object_detector" in self.sidecar.role:
            raise ValueError(f"this release does not run {self.sidecar.model_id}: a model with both roles")
        if keypoint.decode.method != "simcc":
            raise ValueError(f"this release has no decode for keypoint.decode.method: {keypoint.decode.method}")
        self.sidecar.artifact(self.size, self.precision)  # an unknown size or precision is an error

    @property
    def takes_crops(self) -> bool:
        """True for a top-down model: each input is an image with an ROI. A `bottom_up` model takes the full image."""
        return self.sidecar.keypoint.estimator_type != "bottom_up"

    @property
    def point_names(self) -> list[str]:
        return self.sidecar.keypoint.point_names

    @property
    def derived_names(self) -> list[str]:
        return list(self.sidecar.keypoint.derived_points)

    @property
    def overlay_groups(self) -> tuple[OverlayGroup, ...]:
        """The edge groups for drawing, from `keypoint.overlay` and `keypoint.skeletons`."""
        return overlay_groups(self.sidecar.keypoint)

    def detect(
        self, images: Sequence[np.ndarray], rois: Sequence[Sequence[Any]] | None = None,
        timer: Callable[[str, int, int], None] | None = None,
    ) -> KeypointDetections:
        """Return the keypoints of each crop of a top-down model, or of each image of a `bottom_up` model.

        An image is a host frame: uint8, BGR, (H, W, 3). For a top-down model, `rois[i]` is the ROI
        `(c_x, c_y, w, h, rotation)` in the pixels of `images[i]`, so an image with two ROIs is in
        `images` two times. A `bottom_up` model takes no `rois`.

        `timer` gets `(span, start_ns, end_ns)` for the spans `preprocess`, `inference` and
        `postprocess` of a call that runs the model, on the clock `perf_counter_ns`.
        """
        if self.takes_crops != (rois is not None):
            raise ValueError(f"an estimator_type {self.sidecar.keypoint.estimator_type} model {'needs' if self.takes_crops else 'takes no'} rois")
        if rois is not None and len(rois) != len(images):
            raise ValueError(f"images and rois need one length: {len(images)} and {len(rois)}")
        keypoint = self.sidecar.keypoint
        count = len(keypoint.point_names)
        session = self._open_session()
        if not images:
            points, scores = np.zeros((0, count, 2)), np.zeros((0, count), np.float32)
        else:
            clock = time.perf_counter_ns
            marks = [clock()]
            prepared = [
                preprocess_image(image, self.sidecar, self.size, self.precision, None if rois is None else rois[index])
                for index, image in enumerate(images)
            ]
            marks.append(clock())
            outputs = run_batches(session, self.sidecar, [tensor for tensor, _ in prepared])
            marks.append(clock())
            simcc = {
                spec.semantic: np.moveaxis(outputs[spec.name], spec.keypoint_axis, 1)
                for spec in self.sidecar.outputs if spec.semantic in ("simcc_x", "simcc_y")
            }
            decoded = decode_simcc(simcc["simcc_x"], simcc["simcc_y"], prepared[0][1].input_size)
            source = np.stack([resize_inverse(decoded["keypoints"][index], geometry) for index, (_, geometry) in enumerate(prepared)])
            points, scores = mark_missing(source, decoded["scores"])
        derived, derived_scores = derived_points(points, scores, keypoint.point_names, keypoint.derived_points)
        if timer is not None and images:
            marks.append(time.perf_counter_ns())
            for index, span in enumerate(("preprocess", "inference", "postprocess")):
                timer(span, marks[index], marks[index + 1])
        return KeypointDetections(points, scores, derived, derived_scores)

    def _open_session(self) -> Any:
        # A local reference: a `close` from an other thread does not stop a call that started.
        session = self.session
        if session is None:
            raise RuntimeError(f"the detector of {self.sidecar.model_id} is closed")
        return session

    def close(self) -> None:
        """Release the session. A `detect` call that runs on an other thread ends normally. A later call raises `RuntimeError`."""
        self.session = None
