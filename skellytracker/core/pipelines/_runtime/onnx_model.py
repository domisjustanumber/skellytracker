"""The node type `onnx_model`: one model of the sidecar spec, through the generic detectors.

Implements: node.onnx_model

The node does no model processing of its own. The generic detectors do the preprocessing, the
inference and the decode of the sidecar. The node makes the instance rows of the pipeline.

On the EPs of `GRAPH_EPS`, the node runs the preprocess as a graph in its own session and binds the
graph output to the model input in device memory (pipeline.running, Implementer guidance). The
frame stage of the executor uploads the frames (`CallSlots`). The geometry of the inverse comes
from `resize_geometry`, as on the CPU path.
"""
from __future__ import annotations

import functools
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from skellytracker.core.decode.frame import DecodedFrame
from skellytracker.core.pipelines._runtime.resolve import ResolvedModel, ResolvedNode
from skellytracker.core.pipelines._runtime.sessions import FRAME_SIZE_CAP, GRAPH_REFUSED
from skellytracker.core.pipelines.values import InstanceBoxes
from skellytracker.core.pipelines.warnings import PipelineWarning

READS_EMPTY: frozenset[str] = frozenset()
Timer = Callable[[str, int, int], None]
GRAPH_EPS = frozenset({"cuda", "trt-rtx"})
"""The EPs of the GPU preprocess. A test adds `cpu` to run the graph path on the CPU EP."""
SIZE_SETS = 4
"""The most sets of frame sizes with a preprocess session, for each node and device."""
PREPROCESSED_ON_CPU = "preprocessed_on_cpu"
PROBE_SOURCES = [(64, 64), (64, 48)]
"""The frame sizes of the graph build at the start: one size for one camera slot, two sizes for more."""


def check_runs(node: ResolvedNode) -> None:
    """Raise `ValueError` for a model that this release does not run in a pipeline."""
    if node.model.kind == "bottom_up":
        raise ValueError(f"{node.id}: this release does not run a bottom_up keypoint model in a pipeline")


def graph_refusal(model: ResolvedModel, precision: str, slots: int = 1) -> str | None:
    """Return the text of the refusal of the preprocess graph for the combination of the model, or None when the graph takes it.

    With 2 or more camera slots on a device, the probe has two frame sizes, so `none` refuses at the start.
    """
    from skellytracker.core.detectors.processing.pre.graph import PreprocessGraphRefusedError, build_preprocess_graph

    try:
        build_preprocess_graph(model.sidecar, model.size, precision, PROBE_SOURCES[: min(slots, 2)], 1)
    except PreprocessGraphRefusedError as error:
        return str(error)
    return None


@dataclass(frozen=True)
class GraphDevice:
    """One device of a node on the graph path: its device key, its CUDA device id and the batch of its session plan."""

    device_key: str | None
    ep_device_id: Any
    batch: int


@dataclass(frozen=True)
class CallSlots:
    """The device frames of the camera slots of one device in one call, from the frame stage of the executor.

    `values` holds the `OrtValue` of each slot, `sources` the `(width, height)` of each slot, and
    `slot_of` the slot of each `DecodedFrame` of the call, by `id`.
    """

    values: tuple[Any, ...]
    sources: tuple[tuple[int, int], ...]
    slot_of: dict[int, int]


@dataclass
class GraphPath:
    """The GPU preprocess of one node.

    `open(device_key, sources, batch)` gives `(session, reason, text)` (`RunSessions.open_preprocess`).
    `refused` is the text of the graph refusal at the start, else None. `warn` gets each warning.
    """

    open: Callable[[str | None, tuple[tuple[int, int], ...], int], tuple[Any, str | None, str | None]]
    devices: Sequence[GraphDevice]
    device_type: str
    warn: Callable[[PipelineWarning], None]
    refused: str | None = None


class OnnxModelRunner:
    """One `onnx_model` node of a run. `sessions` holds one session for each device of the run.

    With a `graph`, `run` takes the `DecodedFrame` of each image and the `CallSlots` of the device,
    else the host pixels.
    """

    def __init__(self, node: ResolvedNode, precision: str, sessions: Sequence[Any], graph: GraphPath | None = None) -> None:
        from skellytracker.core.detectors.generic.keypoint_detector import GenericKeypointDetector
        from skellytracker.core.detectors.generic.object_detector import GenericObjectDetector

        check_runs(node)
        model = node.model
        self.node_id = node.id
        self.kind = model.kind
        self.outputs_info = node.outputs_info
        self.graph = graph
        self.size_sets: list[set[tuple[tuple[int, int], ...]]] = [set() for _ in sessions]
        self.warned: set[str] = set()
        if self.kind == "object":
            self.detectors: list[Any] = [GenericObjectDetector(model.sidecar, model.size, precision, session, model.decode) for session in sessions]
        else:
            self.detectors = [GenericKeypointDetector(model.sidecar, model.size, precision, session) for session in sessions]

    @property
    def graph_on_at_start(self) -> bool:
        """True when the node starts with its preprocess as a graph (pipeline.timing, `stage_providers`)."""
        return self.graph is not None and self.graph.refused is None

    def run(
        self, device: int, images: Sequence[Any], boxes: Sequence[InstanceBoxes] | None = None, timer: Timer | None = None,
        slots: CallSlots | None = None,
    ) -> list[dict[str, Any]]:
        """Run the model on the images of one call, in one inference call. Return the outputs of each image.

        `device` is the index of the session. `images` holds host frames, or `DecodedFrame`s for a
        runner with a graph. `boxes` holds the `boxes` value of each image of a top-down model: the
        model runs once for each present row. `timer` gets the spans `preprocess`, `inference` and
        `postprocess`. `slots` are the device frames of the call for a runner with a graph.
        """
        detector = self.detectors[device]
        detect = detector.detect
        if self.graph is not None:
            detect = self._graph_detect(device, images, slots)
            if detect is None:
                detect, images = detector.detect, [frame.host for frame in images]
        if self.kind == "object":
            return [self._object_rows(found) for found in detect(images, timer=timer)]
        pairs = [(index, int(row)) for index, value in enumerate(boxes or ()) for row in np.flatnonzero(value.present)]
        found = detect([images[index] for index, _ in pairs], [boxes[index].boxes[row].tolist() for index, row in pairs], timer=timer)
        values = [self.outputs_info["keypoints"].empty() for _ in images]
        for position, (index, row) in enumerate(pairs):
            value = values[index]
            value.xy[row] = found.keypoints[position]  # z of a `3d` model stays NaN: the decode of this release gives x and y
            value.score[row] = found.scores[position]
            value.raw_score[row] = found.raw_scores[position]
            value.instance_score[row] = boxes[index].instance_score[row]
            value.present[row] = True
        return [{"keypoints": value} for value in values]

    def _graph_detect(self, device: int, frames: Sequence[DecodedFrame], slots: CallSlots | None) -> Callable[..., Any] | None:
        """Return a `detect` of the graph path for the frames of one call, or None for the CPU preprocess.

        The set of frame sizes is `slots.sources`: one fixed slot for each camera of the device.
        """
        from skellytracker.core.detectors.generic.inference import session_batch

        graph, place = self.graph, self.graph.devices[device]
        # shortcut: a dynamic model session runs the batch of the graph (cameras x rows), padded, where the CPU
        # path runs the N items; give the graph a symbolic batch when dynamic shapes are proven on TensorRT RTX.
        batch = session_batch(self.detectors[device]._open_session()) or place.batch  # noqa: SLF001 - the closed check of the detector
        session, reason, text = None, None, None
        if graph.refused is not None:
            reason, text = GRAPH_REFUSED, graph.refused
        else:
            known = self.size_sets[device]
            if slots.sources not in known and len(known) >= SIZE_SETS:
                reason, text = FRAME_SIZE_CAP, f"the node has preprocess sessions for {SIZE_SETS} sets of frame sizes on the device"
            else:
                session, reason, text = graph.open(place.device_key, slots.sources, batch)
                if session is not None:
                    known.add(slots.sources)
        if session is None:
            if reason not in self.warned:
                self.warned.add(reason)
                frame_sizes = [[frame.width, frame.height] for frame in frames]
                graph.warn(PipelineWarning(
                    PREPROCESSED_ON_CPU,
                    f"{self.node_id}: the preprocess runs on the CPU ({reason}) for the frame sizes {frame_sizes}: {text}",
                    (self.node_id,),
                    {"node": self.node_id, "reason": reason, "frame_sizes": frame_sizes, "cause": text},
                ))
            return None
        return functools.partial(self._detect_on_graph, device, session, slots, batch)

    def _detect_on_graph(
        self, device: int, preprocess: Any, slots: CallSlots, batch: int, images: Sequence[DecodedFrame],
        rois: Sequence[Sequence[Any]] | None = None, timer: Timer | None = None,
    ) -> Any:
        """The `detect` of the detector on the graph path: `images` and `rois` as `detect` takes them, each image a frame of the call.

        The span `preprocess` holds the geometry and the graph runs, `inference` the model runs and
        `postprocess` the decode (pipeline.timing; OpenMMLab-Exporter ADR-W9RE).
        """
        from skellytracker.core.detectors.generic.inference import preprocess_batches, run_bound_batches
        from skellytracker.core.detectors.generic.object_detector import decode_objects
        from skellytracker.core.detectors.processing.pre.graph import affine_crop_theta
        from skellytracker.core.detectors.processing.pre.preprocess import resize_geometry

        detector = self.detectors[device]
        if not images:
            return detector.detect([], rois, timer=timer)
        session = detector._open_session()  # noqa: SLF001 - the closed check of the detector
        sidecar, size = detector.sidecar, detector.size
        clock = time.perf_counter_ns
        marks = [clock()]
        index = np.array([slots.slot_of[id(image)] for image in images], np.int64)
        target, resize = sidecar.size(size).target_size, sidecar.input.resize
        geometries = [
            resize_geometry(resize, target, image.width, image.height, None if rois is None else rois[item])
            for item, image in enumerate(images)
        ]
        theta = affine_crop_theta(sidecar, size, slots.sources, rois) if resize.method == "affine_crop" else None
        place = self.graph.devices[device]
        groups = preprocess_batches(preprocess, slots.values, index, theta, batch, self.graph.device_type, int(place.ep_device_id or 0))
        marks.append(clock())
        outputs = run_bound_batches(session, sidecar, groups)
        marks.append(clock())
        found = decode_objects(outputs, sidecar, detector.decode, geometries) if self.kind == "object" else detector.decode_outputs(outputs, geometries)
        marks.append(clock())
        if timer is not None:
            for position, span in enumerate(("preprocess", "inference", "postprocess")):
                timer(span, marks[position], marks[position + 1])
        return found

    def _object_rows(self, found: Any) -> dict[str, Any]:
        """Return `boxes` of one image: the first `I` rows of the decode, which are in descending score order."""
        rows = self.outputs_info["boxes"].max_instances
        count = min(len(found.scores), rows)
        boxes = InstanceBoxes.empty(rows)
        xyxy = np.asarray(found.boxes[:count], dtype=np.float64).reshape(count, 4)
        boxes.boxes[:count] = np.stack(
            [(xyxy[:, 0] + xyxy[:, 2]) / 2, (xyxy[:, 1] + xyxy[:, 3]) / 2, xyxy[:, 2] - xyxy[:, 0], xyxy[:, 3] - xyxy[:, 1], np.zeros(count)], axis=1,
        )
        boxes.instance_score[:count] = found.scores[:count]
        boxes.class_index[:count] = found.class_indices[:count]
        boxes.present[:count] = True
        return {"boxes": boxes}

    def close(self) -> None:
        """Release the sessions of the detectors."""
        for detector in self.detectors:
            detector.close()
