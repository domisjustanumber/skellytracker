"""The node type `onnx_model`: one model of the sidecar spec, through the generic detectors.

Implements: node.onnx_model

The node does no model processing of its own. The generic detectors do the preprocessing, the
inference and the decode of the sidecar. The node makes the instance rows of the pipeline.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from skellytracker.core.pipelines._runtime.resolve import ResolvedNode
from skellytracker.core.pipelines.values import InstanceBoxes, InstanceRois

READS_EMPTY: frozenset[str] = frozenset()
Timer = Callable[[str, int, int], None]


def check_runs(node: ResolvedNode) -> None:
    """Raise `ValueError` for a model that this release does not run in a pipeline."""
    if node.model.kind == "bottom_up":
        raise ValueError(f"{node.id}: this release does not run a bottom_up keypoint model in a pipeline")


class OnnxModelRunner:
    """One `onnx_model` node of a run. `sessions` holds one session for each device of the run."""

    def __init__(self, node: ResolvedNode, precision: str, sessions: Sequence[Any]) -> None:
        from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
        from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector

        check_runs(node)
        model = node.model
        self.kind = model.kind
        self.outputs_info = node.outputs_info
        if self.kind == "object":
            self.detectors: list[Any] = [GenericObjectDetector(model.sidecar, model.size, precision, session, model.decode) for session in sessions]
        else:
            self.detectors = [GenericKeypointDetector(model.sidecar, model.size, precision, session) for session in sessions]

    def run(
        self, device: int, images: Sequence[np.ndarray], rois: Sequence[InstanceRois] | None = None, timer: Timer | None = None,
    ) -> list[dict[str, Any]]:
        """Run the model on the images of one call, in one inference call. Return the outputs of each image.

        `device` is the index of the session. `rois` holds the `rois` value of each image of a
        top-down model: the model runs once for each present row. `timer` gets the spans
        `preprocess`, `inference` and `postprocess`.
        """
        detector = self.detectors[device]
        if self.kind == "object":
            return [self._object_rows(found) for found in detector.detect(images, timer=timer)]
        pairs = [(index, int(row)) for index, value in enumerate(rois or ()) for row in np.flatnonzero(value.present)]
        found = detector.detect([images[index] for index, _ in pairs], [rois[index].rois[row].tolist() for index, row in pairs], timer=timer)
        values = [self.outputs_info["keypoints"].empty() for _ in images]
        for position, (index, row) in enumerate(pairs):
            value = values[index]
            value.xy[row] = found.keypoints[position]  # z of a `3d` model stays NaN: the decode of this release gives x and y
            value.score[row] = found.scores[position]
            value.raw_score[row] = found.raw_scores[position]
            value.instance_score[row] = rois[index].instance_score[row]
            value.present[row] = True
        return [{"keypoints": value} for value in values]

    def _object_rows(self, found: Any) -> dict[str, Any]:
        """Return `detections` and `rois` of one image: the first `I` rows of the decode, which are in descending score order."""
        rows = self.outputs_info["detections"].max_instances
        count = min(len(found.scores), rows)
        boxes, rois = InstanceBoxes.empty(rows), InstanceRois.empty(rows)
        xyxy = np.asarray(found.boxes[:count], dtype=np.float64).reshape(count, 4)
        boxes.xyxy[:count] = xyxy
        boxes.score[:count] = rois.instance_score[:count] = found.scores[:count]
        boxes.class_index[:count] = found.class_indices[:count]
        boxes.present[:count] = rois.present[:count] = True
        rois.rois[:count] = np.stack(
            [(xyxy[:, 0] + xyxy[:, 2]) / 2, (xyxy[:, 1] + xyxy[:, 3]) / 2, xyxy[:, 2] - xyxy[:, 0], xyxy[:, 3] - xyxy[:, 1], np.zeros(count)], axis=1,
        )
        return {"detections": boxes, "rois": rois}

    def close(self) -> None:
        """Release the sessions of the detectors."""
        for detector in self.detectors:
            detector.close()
