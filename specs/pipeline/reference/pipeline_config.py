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
names, geometries, instance sources, ``max_instances`` limits) are not in this module. The host
does them at load.
"""

from __future__ import annotations

import math
import re
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The port types. A port of type `any` takes a value of each type.
PORT_TYPES = ("image", "roi", "keypoints", "detections", "tensor", "any")
# A name of a node, a pipeline, an output, a tap, a slot or a derived point.
NAME = r"^[a-z][a-z0-9_-]*$"
# The name of a source, as `source.name` of a sidecar (V-common.identity-6 of the sidecar spec).
SOURCE_NAME = r"^[a-z0-9]+(-[a-z0-9]+)*$"
# `<node>.<port>`, with an optional `@prev`.
PORT_REF = re.compile(r"^(?P<node>[a-z][a-z0-9_-]*)\.(?P<port>[a-z][a-z0-9_]*)(?P<prev>@prev)?$")
# A point name in the graph: `<prefix>.<point>` (pipeline.graph, Behaviour item 7).
POINT_NAME = re.compile(r"^(?P<prefix>[a-z][a-z0-9_-]*)\.(?P<point>[^.\s]+)$")
SEMVER = r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$"
# The reserved node id of the timing point of one frame call.
RESERVED_NODE_ID = "pipeline"
# The reserved source of the graph: the camera frame of the call, as the port `frame.image`.
FRAME = "frame"
FRAME_PORTS = {"image": "image"}
# The input name of a variadic node in the reference model. Its `inputs` is a list.
VARIADIC = "*"
# The prefixes of a `mediapipe_tasks` node of the variant `holistic`, in output order.
HOLISTIC_PREFIXES = ("body", "right_hand", "left_hand", "face")
# The tolerance of the weight sum of a weighted derived point (sidecar spec, post.keypoint.schema).
WEIGHT_SUM_TOLERANCE = 1e-6


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
        description="The catalog key of the model, `<model_id>@<source.name>`, with an optional pin `==<version>`.",
        live=False,
        source="ADR-7NY2 item 10; ADR-88WQ item 7",
    )
    sidecar_sha256: str | None = param(
        None,
        description="The SHA-256 of the sidecar file bytes. Required in a shipped or an exported file.",
        live=False,
        source="ADR-7NY2 item 10",
        pattern=r"^[0-9a-f]{64}$",
    )
    size: str = param(description="A size key of the `sizes` of the sidecar.", live=False, source="ADR-7NY2 item 10")
    precision: Literal["fp32", "fp16"] | None = param(
        None,
        description="The precision of the artifact. Empty: fp16 on a GPU EP and fp32 on CPU; fp32 when the size has no fp16 artifact.",
        live=False,
        source="ADR-7NY2 item 10",
    )
    execution_provider: str | None = param(
        None,
        description="A key of the EP catalog for this node, for example `cuda`, `trt-rtx` or `cpu`. Empty: the EP of the run.",
        live=False,
        source="ADR-7NY2 item 12; ADR-9NW0 item 1",
    )
    ep_options: dict[str, str] = param(
        default_factory=dict,
        description="EP options for this node: option names and values that the EP catalog allows for its EP. Empty: the EP options of the run when the node uses the EP of the run, else none.",
        live=False,
        source="ADR-9NW0 item 2",
    )
    max_instances: int = param(
        1,
        description="The number of instance rows `I` that this node makes (object detector or one-stage model).",
        live=False,
        source="ADR-99MH item 1",
        ge=1,
    )
    object_decode: dict[str, Any] = param(
        default_factory=dict,
        description="Changes of the fields of the `object.decode` block of the sidecar. The load checks each name against the sidecar.",
        live=False,
        source="ADR-7NY2 item 11; ADR-88WQ item 7",
    )


class MediapipeTasksParams(Strict):
    variant: Literal["body", "hand", "face", "holistic"] = param(
        description="The Tasks landmarker: pose (`body`), hand, face or holistic.", live=False, source="ADR-48PG item 4; ADR-88WQ item 4"
    )
    max_instances: int = param(
        1,
        description="`num_poses`, `num_hands` or `num_faces`. Holistic is single person: 1.",
        live=False,
        source="MediaPipe `num_poses`, `num_hands`, `num_faces` (Tasks default 1); ADR-48PG item 4",
        ge=1,
    )
    size: Literal["lite", "full", "heavy"] = param(
        "heavy",
        description="The model size of the pose landmarker. Only for the variant `body`.",
        live=False,
        source="MediaPipe asset `pose_landmarker_<size>`; MediapipePoseDetectorConfig.model_complexity",
    )
    min_detection_score: float = param(
        0.5,
        description="The minimum detection score (Holistic: the pose and the face detection).",
        live=False,
        source="MediaPipe `min_*_detection_confidence` (Tasks default 0.5)",
        ge=0.0,
        le=1.0,
    )
    min_presence_score: float = param(
        0.5,
        description="The minimum presence score (Holistic: the landmark score of each part).",
        live=False,
        source="MediaPipe `min_*_presence_confidence`, Holistic `min_*_landmarks_confidence` (Tasks default 0.5)",
        ge=0.0,
        le=1.0,
    )
    min_tracking_score: float = param(
        0.5,
        description="The minimum tracking score in VIDEO mode. Holistic has no tracking option.",
        live=False,
        source="MediaPipe `min_tracking_confidence` (Tasks default 0.5)",
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def _single_person_holistic(self) -> MediapipeTasksParams:
        if self.variant == "holistic" and self.max_instances != 1:
            raise ValueError("V-node.mediapipe_tasks-1: the variant holistic is single person; max_instances must be 1")
        return self


# A derived point: passthrough (a name), mean (a list of names) or weighted (name to weight).
Derivation = str | list[str] | dict[str, float]


def derivation_sources(derivation: Derivation) -> list[str]:
    """Return the source point names of one derivation (sidecar spec, `keypoint.derived_points`)."""
    if isinstance(derivation, str):
        return [derivation]
    return list(derivation)


class RoiFromPointsParams(Strict):
    points: list[str | list[str]] = param(
        description="The points of the ROI. A list of names is one point with aliases: the first present name counts.",
        live=False,
        source="ADR-7NY2 item 6",
        min_length=1,
    )
    derived_points: dict[str, Derivation] = param(
        default_factory=dict,
        description="Derived point name to derivation, in the map form of the sidecar `keypoint.derived_points`: passthrough, mean or weighted.",
        live=False,
        source="ADR-7NY2 item 6; ADR-88WQ item 6",
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
        source="ADR-7NY2 item 6; ADR-88WQ item 6",
        ge=0.0,
    )
    shift_x: float = param(0.0, description="Shift along the ROI x axis, in ROI widths.", live=True, source="MediaPipe RectTransformationCalculator default")
    shift_y: float = param(0.0, description="Shift along the ROI y axis, in ROI heights.", live=True, source="MediaPipe RectTransformationCalculator default")
    square_long: bool = param(False, description="Make the ROI square with its longer side.", live=True, source="MediaPipe RectTransformationCalculator default")
    expand_ratio: float = param(
        1.0, description="Multiply the width and the height by this value.", live=True,
        source="MediaPipe RectTransformationCalculator scale default; ADR-88WQ item 4", gt=0.0,
    )

    @model_validator(mode="after")
    def _rules(self) -> RoiFromPointsParams:
        no_alignment = self.alignment_start is None or self.alignment_end is None
        if self.size_rule == "alignment" and no_alignment:
            raise ValueError("V-node.roi_from_points-1: the size rule alignment needs alignment_start and alignment_end")
        for name, derivation in self.derived_points.items():
            if re.match(NAME, name) is None:
                raise ValueError(f"V-node.roi_from_points-3: the derived point name {name!r} is not a name")
            if not derivation_sources(derivation):
                raise ValueError(f"V-node.roi_from_points-5: the derived point {name!r} has no source")
            if isinstance(derivation, dict) and abs(math.fsum(derivation.values()) - 1.0) > WEIGHT_SUM_TOLERANCE:
                raise ValueError(f"V-node.roi_from_points-5: the weights of {name!r} do not sum to 1")
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
        None, description="The score threshold of the mode `score_above`.", live=True, source="ADR-7NY2 item 6; ADR-88WQ item 6",
        ge=0.0,
    )

    @model_validator(mode="after")
    def _threshold(self) -> GateParams:
        if (self.mode == "score_above") != (self.threshold is not None):
            raise ValueError("V-node.gate-1: the mode score_above needs a threshold, and the other modes have none")
        return self


class NoParams(Strict):
    """A node type with no params."""


class MergeParams(Strict):
    slots: dict[str, str] = param(
        description="Slot name to the target point that anchors the slot, for example `left_hand: body.left_wrist`.",
        live=False,
        source="ADR-7NY2 item 6",
        min_length=1,
    )
    source_anchor: str = param(
        description="The point of `source` that the node compares with the slot anchors, for example `hand.wrist`.",
        live=False,
        source="ADR-7NY2 item 6",
    )
    max_distance: float | None = param(
        None,
        description="The largest anchor distance, as a part of the diagonal of the box around the present points of the target row. Empty: no limit.",
        live=True,
        source="ADR-7NY2 item 6",
        gt=0.0,
    )
    map: dict[str, str] = param(
        default_factory=dict,
        description="Target point to slot column `<slot>.<point>`. A present slot point replaces the target point.",
        live=False,
        source="ADR-7NY2 item 6",
    )

    @model_validator(mode="after")
    def _slots(self) -> MergeParams:
        for slot in self.slots:
            if re.match(NAME, slot) is None:
                raise ValueError(f"V-node.merge-1: the slot name {slot!r} is not a name")
        for target, column in self.map.items():
            match = POINT_NAME.match(column)
            if match is None or match["prefix"] not in self.slots:
                raise ValueError(f"V-node.merge-2: map {target!r}: {column!r} is not a slot column `<slot>.<point>`")
        return self


class SmoothKeypointsParams(Strict):
    filter: Literal["one_euro", "kalman"] = param(
        "one_euro", description="The filter.", live=False, source="KeypointSmoothingConfig.kind"
    )
    min_cutoff: float = param(1.0, description="one_euro: the minimum cutoff frequency, in Hz.", live=True, source="KeypointSmoothingConfig", gt=0.0)
    beta: float = param(0.0, description="one_euro: the speed coefficient, in Hz per px/s.", live=True, source="KeypointSmoothingConfig", ge=0.0)
    d_cutoff: float = param(1.0, description="one_euro: the cutoff frequency of the derivative, in Hz.", live=True, source="KeypointSmoothingConfig", gt=0.0)
    process_noise_pos: float = param(
        30.0, description="kalman: the process noise of the position, in px² per second.", live=True,
        source="KalmanKeypointSmoothingConfig (1 px² per frame at 30 fps)", gt=0.0,
    )
    process_noise_vel: float = param(
        2700.0, description="kalman: the process noise of the velocity, in (px/s)² per second.", live=True,
        source="KalmanKeypointSmoothingConfig (0.1 (px/frame)² per frame at 30 fps)", gt=0.0,
    )
    measurement_noise: float = param(10.0, description="kalman: the measurement noise, in px².", live=True, source="KalmanKeypointSmoothingConfig", gt=0.0)
    max_gap_ms: float | None = param(
        None, description="Hold the last value of a missing point for this many milliseconds after its last detection. Empty: no hold.",
        live=False, source="KeypointSmoothingConfig.max_gap_frames", gt=0.0,
    )
    max_velocity: float | None = param(
        None, description="Refuse a point that moves faster than this many pixels per second since its last detection. Empty: accept each point.",
        live=True, source="KeypointSmoothingConfig", gt=0.0,
    )
    reset_after_ms: float | None = param(
        None, description="Clear the filter state of a row after this many milliseconds with no valid point. Empty: no reset.",
        live=False, source="KeypointResetPolicyConfig", gt=0.0,
    )

    ONE_EURO: ClassVar[frozenset[str]] = frozenset({"min_cutoff", "beta", "d_cutoff"})
    KALMAN: ClassVar[frozenset[str]] = frozenset({"process_noise_pos", "process_noise_vel", "measurement_noise"})

    @model_validator(mode="after")
    def _filter_params(self) -> SmoothKeypointsParams:
        other = self.KALMAN if self.filter == "one_euro" else self.ONE_EURO
        written = sorted(other & self.model_fields_set)
        if written:
            raise ValueError(f"V-node.smooth_keypoints-1: the filter {self.filter} does not take {', '.join(written)}")
        return self


class SmoothRoiParams(Strict):
    previous_weight: float = param(
        0.5, description="The weight of the previous ROI: new = previous_weight × previous + (1 − previous_weight) × input.", live=True,
        source="BBoxSmoothingConfig.alpha (freemocap uses 0.4); ADR-88WQ item 4", ge=0.0, le=1.0,
    )


class FitnessCheck(Strict):
    check: Literal["min_keypoint_score", "keypoints_within_bbox_ratio", "max_frames_without_redetect", "bbox_area_collapse"] = Field(
        description="The check. A check that fails asks for a new detection."
    )
    threshold: float | None = Field(
        None, description="min_keypoint_score (0.3) or keypoints_within_bbox_ratio (0.5).", ge=0.0
    )
    n_frames: int | None = Field(None, description="max_frames_without_redetect (30).", ge=1)
    min_area_ratio: float | None = Field(None, description="bbox_area_collapse (0.25).", ge=0.0)
    expand_ratio: float | None = Field(None, description="bbox_area_collapse (1.10).", gt=0.0)
    min_score: float | None = Field(None, description="bbox_area_collapse (0.0).", ge=0.0)

    FIELDS: ClassVar[dict[str, frozenset[str]]] = {
        "min_keypoint_score": frozenset({"threshold"}),
        "keypoints_within_bbox_ratio": frozenset({"threshold"}),
        "max_frames_without_redetect": frozenset({"n_frames"}),
        "bbox_area_collapse": frozenset({"min_area_ratio", "expand_ratio", "min_score"}),
    }

    @model_validator(mode="after")
    def _own_fields(self) -> FitnessCheck:
        foreign = sorted((self.model_fields_set - {"check"}) - self.FIELDS[self.check])
        if foreign:
            raise ValueError(f"V-node.redetect-1: the check {self.check} does not take {', '.join(foreign)}")
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
    # The inputs that give the type of an `any` output (pipeline.graph, Behaviour item 4).
    any_from: ClassVar[tuple[str, ...]] = ()
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
    any_from = ("value",)


class FirstOf(NodeType):
    type = "first_of"
    section = "node.first_of"
    Params = NoParams
    inputs = {VARIADIC: "any"}
    outputs = {"value": "any"}
    any_from = (VARIADIC,)


class Concat(NodeType):
    type = "concat"
    section = "node.concat"
    Params = NoParams
    inputs = {VARIADIC: "keypoints"}
    outputs = {"keypoints": "keypoints"}


class Merge(NodeType):
    type = "merge"
    section = "node.merge"
    Params = MergeParams
    inputs = {"target": "keypoints", "source": "keypoints"}
    outputs = {"keypoints": "keypoints"}
    required_inputs = ("target", "source")


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
    Detector, MediapipeTasks, RoiFromPoints, RoiTracking, Gate, FirstOf, Concat, Merge, SmoothKeypoints, SmoothRoi,
    Redetect,
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


class VariadicNodeBase(NodeBase):
    inputs: list[str] = Field(  # type: ignore[assignment]
        default_factory=list,
        description="A list of `<node>.<port>`, each with an optional `@prev`. At least one item.",
        json_schema_extra={"minItems": 1},
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


class FirstOfNode(VariadicNodeBase):
    type: Literal["first_of"]
    params: NoParams = Field(default_factory=NoParams)


class ConcatNode(VariadicNodeBase):
    type: Literal["concat"]
    params: NoParams = Field(default_factory=NoParams)


class MergeNode(NodeBase):
    type: Literal["merge"]
    params: MergeParams


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
    | ConcatNode | MergeNode | SmoothKeypointsNode | SmoothRoiNode | RedetectNode,
    Field(discriminator="type"),
]


class Tap(Strict):
    action: Literal["record", "replay"] = Field(description="`record` writes the port; `replay` reads it from files.")
    port: str = Field(description="`<node>.<port>`, with no `@prev`.")
    name: str = Field(description="The name of the tap and of its sub-folder.", pattern=NAME)


class Instrumentation(Strict):
    timing_points: list[str] = Field(
        default_factory=list, description="`<node>.<point>` or `pipeline.run`. Empty: no timing point is on."
    )
    taps: list[Tap] = Field(default_factory=list, description="The record and replay taps.")


class Source(Strict):
    name: str = Field(
        description="Who made the file, for example `skellytracker`. The key is `<pipeline_id>@<name>`.", pattern=SOURCE_NAME
    )
    version: str = Field(description="The version of the file. The newest version of a key wins, in PEP 440 order.", min_length=1)


class PipelineConfig(Strict):
    """One pipeline file: `<pipeline_id>.pipeline.yaml`."""

    schema_version: str = Field(description="The pipeline spec version, in SemVer, in quotes.", pattern=SEMVER)
    pipeline_id: str = Field(description="The id of the pipeline. The file name is `<pipeline_id>.pipeline.yaml`.", pattern=NAME)
    source: Source = Field(description="The source of the file, as the sidecar `source`: `{name, version}`.")
    description: str = Field("", description="A short text for people.")
    nodes: list[NodeConfig] = Field(description="The nodes, in any order.", min_length=1)
    outputs: dict[str, str] = Field(description="Public output name to `<node>.<port>`, with no `@prev`.", min_length=1)
    instrumentation: Instrumentation = Field(default_factory=Instrumentation, description="Timing points and taps.")

    @model_validator(mode="after")
    def _structure(self) -> PipelineConfig:
        check_structure(self)
        return self


def input_items(node: Any) -> list[tuple[str, str]]:
    """Return (input name, port reference) of each input. A variadic input has the name `*`."""
    if isinstance(node.inputs, list):
        return [(VARIADIC, ref) for ref in node.inputs]
    return list(node.inputs.items())


def _port(ref: str, nodes: dict[str, Any], rule: str, *, graph_input: bool = True) -> tuple[str, str, bool]:
    """Return the node id, the port and the `@prev` flag of `ref`, or raise.

    An output or a tap (`graph_input` false) must name an output port of a node, with no `@prev`.
    """
    match = PORT_REF.match(ref)
    if match is None:
        raise ValueError(f"{rule}: {ref!r} is not `<node>.<port>` with an optional `@prev`")
    node_id, port, prev = match["node"], match["port"], match["prev"] is not None
    if not graph_input and (prev or node_id == FRAME):
        raise ValueError(f"{rule}: {ref!r}: an output or a tap must not be `@prev` or the frame")
    if node_id == FRAME:
        if port not in FRAME_PORTS or prev:
            raise ValueError(f"{rule}: {ref!r}: the frame has only the port `image`, with no `@prev`")
        return node_id, port, prev
    if node_id not in nodes:
        raise ValueError(f"{rule}: {ref!r} names no node")
    if port not in BY_TYPE[nodes[node_id].type].outputs:
        raise ValueError(f"{rule}: {ref!r} names no output port of a {nodes[node_id].type} node")
    return node_id, port, prev


def _ref_type(ref: str, nodes: dict[str, Any], seen: frozenset[str] = frozenset()) -> str:
    """Return the port type of a valid port reference. An `any` output takes the type of its inputs."""
    match = PORT_REF.match(ref)
    assert match is not None  # noqa: S101 (`_port` checked the reference)
    node_id, port = match["node"], match["port"]
    if node_id == FRAME:
        return FRAME_PORTS[port]
    kind = BY_TYPE[nodes[node_id].type]
    if kind.outputs[port] != "any" or node_id in seen:
        return kind.outputs[port]
    types = _input_types(nodes[node_id], nodes, seen | {node_id})
    return types.pop() if len(types) == 1 else "any"


def _input_types(node: Any, nodes: dict[str, Any], seen: frozenset[str] = frozenset()) -> set[str]:
    """Return the known types (not `any`) of the inputs that give the type of the `any` output of `node`."""
    names = BY_TYPE[node.type].any_from
    return {_ref_type(ref, nodes, seen) for name, ref in input_items(node) if name in names} - {"any"}


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
        for name, ref in input_items(node):
            expected = kind.inputs.get(name)
            if expected is None:
                raise ValueError(f"V-pipeline.graph-5: {node.id}: a {node.type} node has no input {name!r}")
            source_id, _, prev = _port(ref, nodes, "V-pipeline.graph-2")
            if not prev and source_id != FRAME:
                edges[node.id].add(source_id)
        missing = [name for name in kind.required_inputs if name not in node.inputs]
        if VARIADIC in kind.inputs and not node.inputs:
            missing = [VARIADIC]
        if missing:
            raise ValueError(f"V-pipeline.graph-6: {node.id}: missing input {missing[0]!r}")
    _check_acyclic(edges)
    for node in config.nodes:
        kind = BY_TYPE[node.type]
        for name, ref in input_items(node):
            expected, given = kind.inputs[name], _ref_type(ref, nodes)
            if "any" not in (expected, given) and expected != given:
                raise ValueError(f"V-pipeline.graph-3: {node.id}.{name} takes {expected}, but {ref!r} gives {given}")
        if node.type == "first_of" and len(types := _input_types(node, nodes)) > 1:
            raise ValueError(f"V-node.first_of-1: {node.id}: the inputs have the port types {sorted(types)}")
    _check_point_names(config, nodes)
    for name, ref in config.outputs.items():
        if re.match(NAME, name) is None:
            raise ValueError(f"V-pipeline.outputs-1: the output name {name!r} is not a name")
        _port(ref, nodes, "V-pipeline.outputs-1", graph_input=False)
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
        _port(tap.port, nodes, "V-pipeline.taps-1", graph_input=False)


def _check_point_names(config: PipelineConfig, nodes: dict[str, Any]) -> None:
    """Check that each point name of a param has a known prefix (V-pipeline.graph-8).

    A known prefix is a node id, a prefix of a `holistic` node, or a slot name of a `merge` node.
    The host checks at load that each name is a point of the input port.
    """
    prefixes = set(nodes)
    for node in config.nodes:
        if node.type == "mediapipe_tasks" and node.params.variant == "holistic":
            prefixes.update(HOLISTIC_PREFIXES)
        if node.type == "merge":
            prefixes.update(node.params.slots)
    for node in config.nodes:
        local: set[str] = set()
        if node.type == "roi_from_points":
            params = node.params
            local = set(params.derived_points)
            names = [name for entry in params.points for name in ([entry] if isinstance(entry, str) else entry)]
            names += [name for name in (params.alignment_start, params.alignment_end) if name is not None]
            sources = [name for derivation in params.derived_points.values() for name in derivation_sources(derivation)]
            names = [name for name in names if name not in local] + sources
        elif node.type == "merge":
            names = [*node.params.slots.values(), node.params.source_anchor, *node.params.map]
        else:
            continue
        for name in names:
            match = POINT_NAME.match(name)
            if match is None or match["prefix"] not in prefixes:
                raise ValueError(f"V-pipeline.graph-8: {node.id}: the point name {name!r} has no known prefix")


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
