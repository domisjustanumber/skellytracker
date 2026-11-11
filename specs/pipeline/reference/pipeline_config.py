"""Reference model of the pipeline config (draft pipeline spec).

This module is the source of the JSON Schema and of the node tables of the pipeline spec
(ADR-3SF2). ``tools/make_pipeline_schema.py`` makes both from it. Do not edit the schema or a
node table by hand.

The module imports only the standard library and pydantic. It loads by its path, so it is not
in a package. It holds:

- one params model for each node type. Each field has a description, and ``json_schema_extra``
  with ``live`` (the value can change during a run in a later version) and ``source`` (where the
  default comes from);
- one node class for each node type in ``NODE_TYPES``, with ``type``, ``section``, ``Params``,
  ``inputs`` and ``outputs`` (port name to port type) and ``timing_points``;
- ``PipelineConfig``, the model of one pipeline file, with the structural load checks of the
  pipeline spec. Each check raises ``ValueError`` with a message that starts with its rule ID.

The load checks that need a sidecar or an installed model (hashes, roles, decode params, point
names, ``max_instances`` limits) are not in this module. The host does them at load.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The port types. A port of type `any` takes a value of each type.
PORT_TYPES = ("image", "roi", "keypoints", "detections", "tensor", "any")
# A name of a node, a pipeline, a source or an output.
NAME = r"^[a-z][a-z0-9_-]*$"
# `<node>.<port>`, with an optional `@prev`.
PORT_REF = re.compile(r"^(?P<node>[a-z][a-z0-9_-]*)\.(?P<port>[a-z][a-z0-9_]*)(?P<prev>@prev)?$")
SEMVER = r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$"
# The reserved node id of the timing point of one frame call.
RESERVED_NODE_ID = "pipeline"
# The reserved source of the graph: the camera frame of the call, as the port `frame.image`.
FRAME = "frame"
FRAME_PORTS = {"image": "image"}
# An input name that a variadic node accepts: one or more inputs, each with its own name.
VARIADIC = "*"


def param(default: Any = ..., *, description: str, live: bool, source: str, **constraints: Any) -> Any:
    """Return a pydantic field with the `live` and `source` marks of the pipeline spec."""
    return Field(default, description=description, json_schema_extra={"live": live, "source": source}, **constraints)


class Strict(BaseModel):
    """A model that refuses unknown keys."""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------------------------
# Params of the node types
# ---------------------------------------------------------------------------------------------


class DetectorParams(Strict):
    key: str = param(
        description="The catalog key of the model, `<model_id>@<source>`.", live=False, source="ADR-7NY2 item 10"
    )
    sidecar_sha256: str | None = param(
        None,
        description="The SHA-256 of the sidecar file bytes. Required in a shipped or an exported file.",
        live=False,
        source="ADR-7NY2 item 10",
        pattern=r"^[0-9a-f]{64}$",
    )
    size: str = param(description="A size name of the `sizes` of the sidecar.", live=False, source="ADR-7NY2 item 10")
    precision: Literal["fp32", "fp16"] | None = param(
        None,
        description="The precision of the artifact. Empty: fp16 on a GPU EP, fp32 on CPU.",
        live=False,
        source="ADR-7NY2 item 10",
    )
    execution_provider: str | None = param(
        None,
        description="A concrete EP for this node. Empty: the EP of the run.",
        live=False,
        source="ADR-7NY2 item 12",
    )
    max_instances: int = param(
        1,
        description="The number of instance rows that this node makes (object detector or one-stage model).",
        live=False,
        source="ADR-99MH item 1",
        ge=1,
    )
    decode: dict[str, Any] = param(
        default_factory=dict,
        description="Changes of the `decode` fields of the sidecar. The load checks each name against the sidecar.",
        live=False,
        source="ADR-7NY2 item 11",
    )


class MediapipeTasksParams(Strict):
    variant: Literal["pose", "hand", "face", "holistic"] = param(
        description="The Tasks landmarker.", live=False, source="ADR-8NVD item 4"
    )
    max_instances: int = param(
        1,
        description="`num_poses`, `num_hands` or `num_faces`. Holistic is single person: 1.",
        live=False,
        source="MediaPipe Tasks default; ADR-8NVD item 4",
        ge=1,
    )
    pose_model: Literal["lite", "full", "heavy"] = param(
        "heavy",
        description="The pose landmarker model. Only for the variant `pose`.",
        live=False,
        source="MediapipePoseDetectorConfig.model_complexity",
    )
    min_detection_confidence: float = param(
        0.5,
        description="The minimum detection score (Holistic: the pose and the face detection).",
        live=False,
        source="MediaPipe Tasks default",
        ge=0.0,
        le=1.0,
    )
    min_presence_confidence: float = param(
        0.5,
        description="The minimum presence score (Holistic: the landmark confidence of each part).",
        live=False,
        source="MediaPipe Tasks default",
        ge=0.0,
        le=1.0,
    )
    min_tracking_confidence: float = param(
        0.5,
        description="The minimum tracking score in VIDEO mode. Holistic has no tracking option.",
        live=False,
        source="MediaPipe Tasks default",
        ge=0.0,
        le=1.0,
    )
    @model_validator(mode="after")
    def _single_person_holistic(self) -> MediapipeTasksParams:
        if self.variant == "holistic" and self.max_instances != 1:
            raise ValueError("V-node.mediapipe_tasks-1: the variant holistic is single person; max_instances must be 1")
        return self


class DerivedPoint(Strict):
    name: str = Field(description="The name of the new point.", pattern=NAME)
    weights: dict[str, float] = Field(
        description="Point name to weight. A negative weight extrapolates, for example wrist 1.5 and elbow -0.5.",
        min_length=1,
    )


class RoiFromPointsParams(Strict):
    points: list[str | list[str]] = param(
        description="The points of the ROI. A list of names is one point with aliases: the first present name counts.",
        live=False,
        source="ADR-7NY2 item 6",
        min_length=1,
    )
    derived: list[DerivedPoint] = param(
        default_factory=list,
        description="Points made from other points with weights. They can be used in `points` and in the alignment.",
        live=False,
        source="ADR-7NY2 item 6",
    )
    size_rule: Literal["bounds", "alignment"] = param(
        "bounds",
        description="`bounds`: the box around the points. `alignment`: centre at the start point, size 2 × the distance from start to end.",
        live=False,
        source="MediaPipe AlignmentPointsRectsCalculator; ADR-7NY2 item 6",
    )
    alignment_start: str | None = param(
        None, description="The start point of the alignment rule.", live=False, source="ADR-7NY2 item 6"
    )
    alignment_end: str | None = param(
        None, description="The end point of the alignment rule.", live=False, source="ADR-7NY2 item 6"
    )
    target_rotation_deg: float | None = param(
        None,
        description="The rotation target in degrees. Empty: rotation `none`, an axis-aligned ROI.",
        live=False,
        source="MediaPipe rect rotation; ADR-7NY2 item 6",
    )
    score_threshold: float = param(
        0.0,
        description="A point counts only when its score is greater than this value.",
        live=True,
        source="ADR-7NY2 item 6",
        ge=0.0,
        le=1.0,
    )
    shift_x: float = param(0.0, description="Shift along the ROI x axis, in ROI widths.", live=True, source="MediaPipe RectTransformationCalculator default")
    shift_y: float = param(0.0, description="Shift along the ROI y axis, in ROI heights.", live=True, source="MediaPipe RectTransformationCalculator default")
    square_long: bool = param(False, description="Make the ROI square with its longer side.", live=True, source="MediaPipe RectTransformationCalculator default")
    scale: float = param(1.0, description="Multiply the width and the height by this value.", live=True, source="MediaPipe RectTransformationCalculator default", gt=0.0)

    @model_validator(mode="after")
    def _alignment_points(self) -> RoiFromPointsParams:
        no_alignment = self.alignment_start is None or self.alignment_end is None
        if self.size_rule == "alignment" and no_alignment:
            raise ValueError("V-node.roi_from_points-1: the size rule alignment needs alignment_start and alignment_end")
        if self.size_rule == "bounds" and self.target_rotation_deg is not None and no_alignment:
            raise ValueError(
                "V-node.roi_from_points-4: the size rule bounds with a target rotation needs alignment_start and alignment_end"
            )
        return self


class RoiTrackingParams(Strict):
    max_rotation_deg: float = param(
        40.0, description="Keep the previous ROI only when the rotation differs by this much or less.", live=True,
        source="MediaPipe Holistic hand RoiTrackingCalculator (face: 15)", ge=0.0,
    )
    max_offset: float = param(
        0.2, description="The largest x and y offset, as a part of the new ROI size.", live=True,
        source="MediaPipe Holistic hand RoiTrackingCalculator (face: 0.1)", ge=0.0,
    )
    max_size_change: float = param(
        0.4, description="The largest width and height difference, as a part of the new ROI size.", live=True,
        source="MediaPipe Holistic hand RoiTrackingCalculator (face: 0.3)", ge=0.0,
    )
    keypoint_margin: float = param(
        -0.1, description="Each previous point must be inside the new ROI grown by this part (negative: shrunk).", live=True,
        source="MediaPipe Holistic hand RoiTrackingCalculator (face: -0.2)",
    )

    @model_validator(mode="after")
    def _margin(self) -> RoiTrackingParams:
        if self.keypoint_margin <= -1.0:
            raise ValueError("V-node.roi_tracking-1: keypoint_margin must be greater than -1")
        return self


class GateParams(Strict):
    mode: Literal["is_empty", "is_present", "score_above"] = param(
        description="Pass `value` when `condition` is empty, is present, or has a score greater than `threshold`.",
        live=False, source="ADR-7NY2 item 6",
    )
    threshold: float | None = param(
        None, description="The score threshold of the mode `score_above`.", live=True, source="ADR-7NY2 item 6",
        ge=0.0, le=1.0,
    )

    @model_validator(mode="after")
    def _threshold(self) -> GateParams:
        if (self.mode == "score_above") != (self.threshold is not None):
            raise ValueError("V-node.gate-1: the mode score_above needs a threshold, and the other modes have none")
        return self


class NoParams(Strict):
    """A node type with no params."""


class SmoothKeypointsParams(Strict):
    filter: Literal["one_euro", "kalman"] = param(
        "one_euro", description="The filter.", live=False, source="KeypointSmoothingConfig.kind"
    )
    min_cutoff: float = param(1.0, description="one_euro: the minimum cutoff frequency.", live=True, source="KeypointSmoothingConfig", gt=0.0)
    beta: float = param(0.0, description="one_euro: the speed coefficient.", live=True, source="KeypointSmoothingConfig", ge=0.0)
    d_cutoff: float = param(1.0, description="one_euro: the cutoff frequency of the derivative.", live=True, source="KeypointSmoothingConfig", gt=0.0)
    process_noise_pos: float = param(1.0, description="kalman: the process noise of the position (pixels² per frame).", live=True, source="KalmanKeypointSmoothingConfig", gt=0.0)
    process_noise_vel: float = param(0.1, description="kalman: the process noise of the velocity.", live=True, source="KalmanKeypointSmoothingConfig", gt=0.0)
    measurement_noise: float = param(10.0, description="kalman: the measurement noise (pixels²).", live=True, source="KalmanKeypointSmoothingConfig", gt=0.0)
    max_gap_frames: int | None = param(
        None, description="Hold the last value of a missing point for this many frames. Empty: no hold.", live=False,
        source="KeypointSmoothingConfig", ge=1,
    )
    max_velocity: float | None = param(
        None, description="Refuse a point that moves more than this many pixels per frame. Empty: accept each point.",
        live=True, source="KeypointSmoothingConfig", gt=0.0,
    )
    max_consecutive_misses: int | None = param(
        None, description="Reset the filter state after this many frames with no point. Empty: no reset.", live=False,
        source="KeypointResetPolicyConfig", ge=1,
    )
    backoff_multiplier: float = param(
        2.0, description="Multiply the miss limit by this value after a reset with no detection between.", live=False,
        source="KeypointResetPolicyConfig", ge=1.0,
    )
    max_backoff_misses: int | None = param(
        None, description="The largest miss limit after back-off. Empty: no limit.", live=False,
        source="KeypointResetPolicyConfig", ge=1,
    )

    ONE_EURO: ClassVar[frozenset[str]] = frozenset({"min_cutoff", "beta", "d_cutoff"})
    KALMAN: ClassVar[frozenset[str]] = frozenset({"process_noise_pos", "process_noise_vel", "measurement_noise"})

    @model_validator(mode="after")
    def _filter_params(self) -> SmoothKeypointsParams:
        other = self.KALMAN if self.filter == "one_euro" else self.ONE_EURO
        written = sorted(other & self.model_fields_set)
        if written:
            raise ValueError(f"V-node.smooth_keypoints-1: the filter {self.filter} does not take {', '.join(written)}")
        backoff = {"backoff_multiplier", "max_backoff_misses"} & self.model_fields_set
        if backoff and self.max_consecutive_misses is None:
            raise ValueError("V-node.smooth_keypoints-2: backoff_multiplier and max_backoff_misses need max_consecutive_misses")
        return self


class SmoothRoiParams(Strict):
    alpha: float = param(
        0.5, description="The weight of the previous ROI: new = alpha × previous + (1 − alpha) × input.", live=True,
        source="BBoxSmoothingConfig.alpha (freemocap uses 0.4)", ge=0.0, le=1.0,
    )


class FitnessCheck(Strict):
    kind: Literal["min_keypoint_visibility", "keypoints_within_bbox_ratio", "max_frames_without_redetect", "bbox_area_collapse"] = Field(
        description="The check. A check that fails asks for a new detection."
    )
    threshold: float | None = Field(
        None, description="min_keypoint_visibility (0.3) or keypoints_within_bbox_ratio (0.5).", ge=0.0, le=1.0
    )
    n_frames: int | None = Field(None, description="max_frames_without_redetect (30).", ge=1)
    min_area_ratio: float | None = Field(None, description="bbox_area_collapse (0.25).", ge=0.0)
    expansion_ratio: float | None = Field(None, description="bbox_area_collapse (0.05).", ge=0.0)
    min_visibility: float | None = Field(None, description="bbox_area_collapse (0.0).", ge=0.0, le=1.0)

    FIELDS: ClassVar[dict[str, frozenset[str]]] = {
        "min_keypoint_visibility": frozenset({"threshold"}),
        "keypoints_within_bbox_ratio": frozenset({"threshold"}),
        "max_frames_without_redetect": frozenset({"n_frames"}),
        "bbox_area_collapse": frozenset({"min_area_ratio", "expansion_ratio", "min_visibility"}),
    }

    @model_validator(mode="after")
    def _own_fields(self) -> FitnessCheck:
        foreign = sorted((self.model_fields_set - {"kind"}) - self.FIELDS[self.kind])
        if foreign:
            raise ValueError(f"V-node.redetect-1: the check {self.kind} does not take {', '.join(foreign)}")
        return self


class RedetectParams(Strict):
    redetect_interval: int = param(
        1, description="Ask for a new detection at least each this many frames.", live=True,
        source="BBoxPolicyConfig.redetect_interval", ge=1,
    )
    fitness_checks: list[FitnessCheck] = param(
        default_factory=list, description="Checks on the previous frame that ask for a new detection.", live=False,
        source="BBoxPolicyConfig.fitness_checks",
    )


# ---------------------------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------------------------


class NodeType:
    """The fixed facts of one node type."""

    type: ClassVar[str]
    section: ClassVar[str]
    Params: ClassVar[type[BaseModel]]
    inputs: ClassVar[dict[str, str]]
    outputs: ClassVar[dict[str, str]]
    required_inputs: ClassVar[tuple[str, ...]] = ()
    timing_points: ClassVar[tuple[str, ...]] = ("run",)


class Detector(NodeType):
    type = "detector"
    section = "node.detector"
    Params = DetectorParams
    # `rois` is for a top-down keypoint model only; the role of the sidecar decides the ports that it uses.
    inputs = {"image": "image", "rois": "roi"}
    outputs = {"detections": "detections", "rois": "roi", "keypoints": "keypoints"}
    required_inputs = ("image",)
    timing_points = ("preprocess", "inference", "postprocess")


class MediapipeTasks(NodeType):
    type = "mediapipe_tasks"
    section = "node.mediapipe_tasks"
    Params = MediapipeTasksParams
    inputs = {"image": "image"}
    outputs = {"keypoints": "keypoints"}
    required_inputs = ("image",)


class RoiFromPoints(NodeType):
    type = "roi_from_points"
    section = "node.roi_from_points"
    Params = RoiFromPointsParams
    inputs = {"keypoints": "keypoints"}
    outputs = {"rois": "roi"}
    required_inputs = ("keypoints",)


class RoiTracking(NodeType):
    type = "roi_tracking"
    section = "node.roi_tracking"
    Params = RoiTrackingParams
    inputs = {"previous": "roi", "current": "roi", "previous_keypoints": "keypoints"}
    outputs = {"rois": "roi"}
    required_inputs = ("previous", "current")


class Gate(NodeType):
    type = "gate"
    section = "node.gate"
    Params = GateParams
    inputs = {"value": "any", "condition": "any"}
    outputs = {"value": "any"}
    required_inputs = ("value", "condition")


class FirstOf(NodeType):
    type = "first_of"
    section = "node.first_of"
    Params = NoParams
    inputs = {VARIADIC: "any"}
    outputs = {"value": "any"}


class Concat(NodeType):
    type = "concat"
    section = "node.concat"
    Params = NoParams
    inputs = {VARIADIC: "keypoints"}
    outputs = {"keypoints": "keypoints"}


class SmoothKeypoints(NodeType):
    type = "smooth_keypoints"
    section = "node.smooth_keypoints"
    Params = SmoothKeypointsParams
    inputs = {"keypoints": "keypoints"}
    outputs = {"keypoints": "keypoints"}
    required_inputs = ("keypoints",)


class SmoothRoi(NodeType):
    type = "smooth_roi"
    section = "node.smooth_roi"
    Params = SmoothRoiParams
    inputs = {"rois": "roi"}
    outputs = {"rois": "roi"}
    required_inputs = ("rois",)


class Redetect(NodeType):
    type = "redetect"
    section = "node.redetect"
    Params = RedetectParams
    # The output is the input image when a new detection is needed, else empty (the trigger).
    inputs = {"image": "image", "previous_keypoints": "keypoints", "previous_rois": "roi"}
    outputs = {"image": "image"}
    required_inputs = ("image",)


NODE_TYPES: tuple[type[NodeType], ...] = (
    Detector, MediapipeTasks, RoiFromPoints, RoiTracking, Gate, FirstOf, Concat, SmoothKeypoints, SmoothRoi, Redetect,
)
BY_TYPE: dict[str, type[NodeType]] = {node.type: node for node in NODE_TYPES}


# ---------------------------------------------------------------------------------------------
# Node configs and the pipeline file
# ---------------------------------------------------------------------------------------------


class NodeBase(Strict):
    id: str = Field(description="The node id. `pipeline` and `frame` are reserved.", pattern=NAME)
    inputs: dict[str, str] = Field(
        default_factory=dict, description="Input name to `<node>.<port>`, with an optional `@prev`."
    )


class DetectorNode(NodeBase):
    type: Literal["detector"]
    params: DetectorParams


class MediapipeTasksNode(NodeBase):
    type: Literal["mediapipe_tasks"]
    params: MediapipeTasksParams


class RoiFromPointsNode(NodeBase):
    type: Literal["roi_from_points"]
    params: RoiFromPointsParams


class RoiTrackingNode(NodeBase):
    type: Literal["roi_tracking"]
    params: RoiTrackingParams = Field(default_factory=RoiTrackingParams)


class GateNode(NodeBase):
    type: Literal["gate"]
    params: GateParams


class FirstOfNode(NodeBase):
    type: Literal["first_of"]
    params: NoParams = Field(default_factory=NoParams)


class ConcatNode(NodeBase):
    type: Literal["concat"]
    params: NoParams = Field(default_factory=NoParams)


class SmoothKeypointsNode(NodeBase):
    type: Literal["smooth_keypoints"]
    params: SmoothKeypointsParams = Field(default_factory=SmoothKeypointsParams)


class SmoothRoiNode(NodeBase):
    type: Literal["smooth_roi"]
    params: SmoothRoiParams = Field(default_factory=SmoothRoiParams)


class RedetectNode(NodeBase):
    type: Literal["redetect"]
    params: RedetectParams = Field(default_factory=RedetectParams)


NodeConfig = Annotated[
    DetectorNode | MediapipeTasksNode | RoiFromPointsNode | RoiTrackingNode | GateNode | FirstOfNode
    | ConcatNode | SmoothKeypointsNode | SmoothRoiNode | RedetectNode,
    Field(discriminator="type"),
]


class Tap(Strict):
    kind: Literal["record", "replay"] = Field(description="`record` writes the port; `replay` reads it from files.")
    port: str = Field(description="`<node>.<port>`.")
    name: str = Field(description="The name of the tap and of its sub-folder.", pattern=NAME)


class Instrumentation(Strict):
    timing_points: list[str] = Field(
        default_factory=list, description="`<node>.<point>` or `pipeline.run`. Empty: no timing point is on."
    )
    taps: list[Tap] = Field(default_factory=list, description="The record and replay taps.")


class PipelineConfig(Strict):
    """One pipeline file: `<pipeline_id>.pipeline.yaml`."""

    schema_version: str = Field(description="The pipeline spec version, in SemVer, in quotes.", pattern=SEMVER)
    pipeline_id: str = Field(description="The id of the pipeline. The file name is `<pipeline_id>.pipeline.yaml`.", pattern=NAME)
    source: str = Field(description="Who made the file, for example `skellytracker`. The key is `<pipeline_id>@<source>`.", pattern=NAME)
    description: str = Field("", description="A short text for people.")
    nodes: list[NodeConfig] = Field(description="The nodes, in any order.", min_length=1)
    outputs: dict[str, str] = Field(description="Public output name to `<node>.<port>`.", min_length=1)
    instrumentation: Instrumentation = Field(default_factory=Instrumentation, description="Timing points and taps.")

    @model_validator(mode="after")
    def _structure(self) -> PipelineConfig:
        check_structure(self)
        return self


def _port(ref: str, nodes: dict[str, Any], rule: str) -> tuple[str, str, bool]:
    """Return the node id, the port and the `@prev` flag of `ref`, or raise."""
    match = PORT_REF.match(ref)
    if match is None:
        raise ValueError(f"{rule}: {ref!r} is not `<node>.<port>` with an optional `@prev`")
    node_id, port, prev = match["node"], match["port"], match["prev"] is not None
    if node_id == FRAME:
        if port not in FRAME_PORTS or prev:
            raise ValueError(f"{rule}: {ref!r}: the frame has only the port `image`, with no `@prev`")
        return node_id, port, prev
    if node_id not in nodes:
        raise ValueError(f"{rule}: {ref!r} names no node")
    if port not in BY_TYPE[nodes[node_id].type].outputs:
        raise ValueError(f"{rule}: {ref!r} names no output port of a {nodes[node_id].type} node")
    return node_id, port, prev


def check_structure(config: PipelineConfig) -> None:
    """Run the structural load checks of the pipeline spec on `config`."""
    nodes: dict[str, Any] = {}
    for node in config.nodes:
        if node.id in (RESERVED_NODE_ID, FRAME):
            raise ValueError(f"V-pipeline.graph-1: the node id {node.id!r} is reserved")
        if node.id in nodes:
            raise ValueError(f"V-pipeline.graph-1: the node id {node.id!r} is not unique")
        nodes[node.id] = node
    edges: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for node in config.nodes:
        kind = BY_TYPE[node.type]
        variadic = kind.inputs.get(VARIADIC)
        for name, ref in node.inputs.items():
            expected = variadic if variadic is not None else kind.inputs.get(name)
            if expected is None:
                raise ValueError(f"V-pipeline.graph-5: {node.id}: a {node.type} node has no input {name!r}")
            source_id, port, prev = _port(ref, nodes, "V-pipeline.graph-2")
            given = FRAME_PORTS[port] if source_id == FRAME else BY_TYPE[nodes[source_id].type].outputs[port]
            if "any" not in (expected, given) and expected != given:
                raise ValueError(f"V-pipeline.graph-3: {node.id}.{name} takes {expected}, but {ref!r} gives {given}")
            if not prev and source_id != FRAME:
                edges[node.id].add(source_id)
        missing = [name for name in kind.required_inputs if name not in node.inputs]
        if variadic is not None and not node.inputs:
            missing = [VARIADIC]
        if missing:
            raise ValueError(f"V-pipeline.graph-6: {node.id}: missing input {missing[0]!r}")
    _check_acyclic(edges)
    for name, ref in config.outputs.items():
        if re.match(NAME, name) is None:
            raise ValueError(f"V-pipeline.outputs-1: the output name {name!r} is not a name")
        _port(ref, nodes, "V-pipeline.outputs-1")
    for point in config.instrumentation.timing_points:
        node_id, _, point_name = point.partition(".")
        if node_id == RESERVED_NODE_ID and point_name == "run":
            continue
        if node_id not in nodes or point_name not in BY_TYPE[nodes[node_id].type].timing_points:
            raise ValueError(f"V-pipeline.timing-1: {point!r} names no timing point")
    tap_names: set[str] = set()
    for tap in config.instrumentation.taps:
        if tap.name in tap_names:
            raise ValueError(f"V-pipeline.taps-1: the tap name {tap.name!r} is not unique")
        tap_names.add(tap.name)
        _port(tap.port, nodes, "V-pipeline.taps-1")


def _check_acyclic(edges: dict[str, set[str]]) -> None:
    """Raise when the same-frame edges make a cycle (`@prev` edges do not count)."""
    state: dict[str, int] = {}

    def visit(node_id: str, path: tuple[str, ...]) -> None:
        if state.get(node_id) == 2:
            return
        if state.get(node_id) == 1:
            cycle = " -> ".join((*path[path.index(node_id):], node_id))
            raise ValueError(f"V-pipeline.graph-4: the same-frame edges make a cycle: {cycle}")
        state[node_id] = 1
        for source_id in sorted(edges[node_id]):
            visit(source_id, (*path, node_id))
        state[node_id] = 2

    for node_id in sorted(edges):
        visit(node_id, ())
