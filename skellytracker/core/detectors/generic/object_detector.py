"""The generic object detector: one object model of the sidecar spec, on a batch of images."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from skellytracker.core.detectors.generic.inference import run_batches
from skellytracker.core.detectors.processing.post.object_selection_nms import decode_nms
from skellytracker.core.detectors.processing.pre.preprocess import BatchPreprocessor, ResizeGeometry
from skellytracker.core.model_spec.model import ObjectDecodeSpec, SidecarModel

_PRIMARY = ("packed_detections", "boxes")


@dataclass(frozen=True)
class ObjectDetections:
    """The final detections of one image, in descending score order.

    `boxes` are (N, 4) xyxy in source pixels, float64. `scores` are (N,) float64.
    `class_indices` are (N,) int64 indexes into `object.classes`.
    """

    boxes: np.ndarray
    scores: np.ndarray
    class_indices: np.ndarray


def read_object_outputs(
    outputs: Mapping[str, np.ndarray], sidecar: SidecarModel, decode: ObjectDecodeSpec
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Return the boxes (B, Q, 4), the scores (B, Q) and the class indexes (B, Q) of the object outputs.

    Implements: post.object.outputs

    `outputs` maps each output name to its tensor. The primary output is the one that
    `boxes_output` names, else the one output with the semantic `packed_detections` or `boxes`. The
    boxes of a `packed_detections` output are `fields[0:4]`. The scores are the `score_field`
    column or the `scores_output` tensor, else None. The class indexes are the `class_field`
    column, else None: the sidecar then has no class source in the rows.
    """
    primary = next(
        spec for spec in sidecar.outputs
        if spec.semantic in _PRIMARY and decode.boxes_output in (None, spec.name)
    )
    rows = outputs[primary.name]
    fields = primary.fields or []
    scores = classes = None
    if decode.score_field is not None:
        scores = rows[..., fields.index(decode.score_field)]
    elif decode.scores_output is not None:
        scores = outputs[decode.scores_output]
    if decode.class_field is not None:
        classes = rows[..., fields.index(decode.class_field)]
    return rows[..., :4], scores, classes


def decode_objects(
    outputs: Mapping[str, np.ndarray],
    sidecar: SidecarModel,
    decode: ObjectDecodeSpec,
    geometries: Sequence[ResizeGeometry],
    min_score: float | int | None = None,
) -> list[ObjectDetections]:
    """Decode the object outputs of a batch of images with the mode of `decode.selection`.

    Implements: post.object.decode

    `geometries` holds the resize geometry of each image. `min_score` is the value of the caller
    for the last filter. With None, it is `decode.min_score`. Only `selection: nms` has a decode.
    """
    if decode.selection != "nms":
        raise ValueError(f"this release has no decode for object.decode.selection: {decode.selection}")
    boxes, scores, classes = read_object_outputs(outputs, sidecar, decode)
    if scores is None:
        raise ValueError("selection: nms needs a score source: score_field or scores_output")
    results = []
    for index, geometry in enumerate(geometries):
        found = decode_nms(
            boxes[index], scores[index], None if classes is None else classes[index],
            decode, sidecar.object.classes, geometry.input_size, geometry, min_score,
        )
        results.append(ObjectDetections(found["boxes"], found["scores"], found["class_indices"]))
    return results


@dataclass
class GenericObjectDetector:
    """One object model: the sidecar preprocessing, the inference and the sidecar decode.

    `sidecar`, `size` and `precision` give each parameter. `session` is an ONNX Runtime session of
    the artifact of that size and precision, with any batch. `decode` replaces
    `object.decode` of the sidecar when the caller changes fields of it. The result of a call does
    not depend on an earlier call. The detector uses one input batch again at each call
    (`BatchPreprocessor`), so its preprocess and its model run are one call at a time.
    """

    sidecar: SidecarModel
    size: str
    precision: str
    session: Any
    decode: ObjectDecodeSpec | None = None
    _preprocessor: Any = field(default=None, init=False, repr=False, compare=False)
    _lock: Any = field(default_factory=threading.Lock, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if "object_detector" not in self.sidecar.role or self.sidecar.object is None:
            raise ValueError(f"{self.sidecar.model_id} is not an object detector")
        if "keypoint_detector" in self.sidecar.role:
            raise ValueError(f"this release does not run {self.sidecar.model_id}: a model with both roles")
        self.sidecar.artifact(self.size, self.precision)  # an unknown size or precision is an error
        if self.decode is None:
            self.decode = self.sidecar.object.decode
        if self.decode.selection != "nms":
            raise ValueError(f"this release has no decode for object.decode.selection: {self.decode.selection}")

    @property
    def classes(self) -> list[str | None]:
        return self.sidecar.object.classes

    def detect(
        self, images: Sequence[np.ndarray], min_score: float | int | None = None,
        timer: Callable[[str, int, int], None] | None = None,
    ) -> list[ObjectDetections]:
        """Return the detections of each image. An image is a host frame: uint8, BGR, (H, W, 3).

        `min_score` replaces `object.decode.min_score` in the last filter.

        `timer` gets `(span, start_ns, end_ns)` for the spans `preprocess`, `inference` and
        `postprocess` of a call that runs the model, on the clock `perf_counter_ns`.
        """
        session = self._open_session()
        if not images:
            return []
        clock = time.perf_counter_ns
        with self._lock:  # the next call writes into the batch: the model run ends in the lock
            marks = [clock()]
            if self._preprocessor is None:
                self._preprocessor = BatchPreprocessor(self.sidecar, self.size, self.precision)
            batch, geometries = self._preprocessor.preprocess(images)
            marks.append(clock())
            outputs = run_batches(session, self.sidecar, batch)
            marks.append(clock())
        found = decode_objects(outputs, self.sidecar, self.decode, geometries, min_score)
        marks.append(clock())
        if timer is not None:
            for index, span in enumerate(("preprocess", "inference", "postprocess")):
                timer(span, marks[index], marks[index + 1])
        return found

    def _open_session(self) -> Any:
        # A local reference: a `close` from an other thread does not stop a call that started.
        session = self.session
        if session is None:
            raise RuntimeError(f"the detector of {self.sidecar.model_id} is closed")
        return session

    def close(self) -> None:
        """Release the session. A `detect` call that runs on an other thread ends normally. A later call raises `RuntimeError`."""
        self.session = None
