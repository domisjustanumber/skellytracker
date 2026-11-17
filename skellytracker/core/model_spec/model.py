"""The typed model of a sidecar at spec version 2.0.0.

`load_sidecar` builds a `SidecarModel` from a resolved sidecar that passed `check_sidecar`. The
model has one reading of a sidecar: the current text of the spec. It has no key that the spec does
not define, and it refuses each other key. A field that the sidecar omits has the default of the
spec, when the spec gives one. If not, it is `None`.

The host reads `input.shape`, `input.resize.target_size`, `onnx` and `score_map` of a size from
the size entry (`SidecarModel.sizes`), and each other field from the top level. There is no merge.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from skellytracker.core.model_spec.rules import expand_derived_points

Precision = Literal["fp32", "fp16"]
Role = Literal["object_detector", "keypoint_detector"]
NormalizationMode = Literal["none", "unit_float", "imagenet"]
CoordinateSpace = Literal["pixel", "normalized_01", "normalized_11"]
Derivation = str | list[str] | dict[str, float]

_RESIZING_METHODS = ("letterbox", "stretch", "fit", "affine_crop")
LETTERBOX_PAD_VALUE = 114


class SpecModel(BaseModel):
    """The base of each model: no undefined key, no change after the load, no type coercion."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SourceSpec(SpecModel):
    name: str
    version: str


class LicenseObject(SpecModel):
    id: str
    url: str | None = None
    unknown_reason: str | None = None


class TrainingDataset(SpecModel):
    name: str
    url: str | None = None
    use: Literal["pretraining", "training"]
    license: LicenseObject


class LicenseSpec(SpecModel):
    """The `license` block: the license of the weights and the training data.

    Implements: common.license
    """

    model: LicenseObject
    training_data: Literal["unknown"] | list[TrainingDataset]
    training_data_unknown_reason: str | None = None


class CustomNormalization(SpecModel):
    """`(pixel * scale - mean) / std`. `mean` and `std` are in the order of `input.color_format`."""

    mode: Literal["custom"]
    scale: float = 1.0
    mean: list[float] = Field(default=[0.0, 0.0, 0.0], min_length=3, max_length=3)
    std: list[float] = Field(default=[1.0, 1.0, 1.0], min_length=3, max_length=3)


class CropPolicySpec(SpecModel):
    expand_ratio: float = 1.25
    maintain_aspect_ratio: bool = True
    pad_value: float | list[float] = 0


class ResizeSpec(SpecModel):
    """`input.resize`, without `target_size`. A size entry holds `target_size`.

    `interpolation` and `compute_dtype` have their defaults for each method that resizes the image.
    `pad_value` has its default for `letterbox`. `crop_policy` has its defaults for `affine_crop`.
    A field that does not apply to the method is `None`.
    """

    method: Literal["letterbox", "stretch", "fit", "affine_crop", "none"]
    pad_value: float | list[float] | None = None
    pad_position: Literal["top_left", "center"] | None = None
    rounding: Literal["half_even", "half_up"] | None = None
    interpolation: Literal["linear", "area", "cubic", "nearest"] | None = None
    compute_dtype: Literal["uint8", "float32"] | None = None
    crop_policy: CropPolicySpec | None = None

    @model_validator(mode="before")
    @classmethod
    def _defaults_of_the_method(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data, method = dict(data), data.get("method")
        if method in _RESIZING_METHODS:
            data.setdefault("interpolation", "linear")
            data.setdefault("compute_dtype", "uint8")
        if method == "letterbox":
            data.setdefault("pad_value", LETTERBOX_PAD_VALUE)
        if method == "affine_crop":
            data.setdefault("crop_policy", {})
        return data


class InputSpec(SpecModel):
    """The top-level `input`. An absent `resize` is `method: none`."""

    name: str
    dtype: dict[Precision, Literal["float32", "float16", "uint8"]]
    color_format: Literal["rgb", "bgr"]
    normalization: NormalizationMode | CustomNormalization
    normalization_by_precision: dict[Precision, NormalizationMode] = {}
    resize: ResizeSpec = ResizeSpec(method="none")

    def normalization_for(self, precision: Precision) -> NormalizationMode | CustomNormalization:
        """Return the normalization of one precision: its override, else the top-level value."""
        return self.normalization_by_precision.get(precision, self.normalization)


class BatchConversionSpec(SpecModel):
    profile_id: Literal["static-batch-v1"]


class BatchingSpec(SpecModel):
    batch: Literal[3, 1, "dynamic"]
    batch_conversion: BatchConversionSpec | None = None

    @property
    def supports_dynamic_batch(self) -> bool:
        """True when `batching.batch` is `dynamic`. The host derives this value.

        Implements: common.batching
        """
        return self.batch == "dynamic"


class PackedKeypointsSpec(SpecModel):
    offset: int
    components: list[Literal["x", "y", "z", "score"]]


class OutputSpec(SpecModel):
    """One ONNX output tensor.

    `keypoint_axis` is 1 for `simcc_x`, `simcc_y` and `keypoint_coordinates` when the sidecar omits
    it. `class_axis` is -1 for `class_logits` when the sidecar omits it. An absent `keypoint_count`
    means `len(keypoint.point_names)`.
    """

    name: str
    dtype: dict[Precision, Literal["float32", "float16", "uint8", "int8"]]
    shape: list[int] | None = None
    semantic: Literal[
        "packed_detections", "boxes", "scores", "class_logits",
        "simcc_x", "simcc_y", "keypoint_coordinates", "instance_keypoints",
    ]
    fields: list[str] | None = None
    class_axis: int | None = None
    packed_keypoints: PackedKeypointsSpec | None = None
    keypoint_axis: int | None = None
    keypoint_count: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _defaults_of_the_semantic(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data, semantic = dict(data), data.get("semantic")
        if semantic in ("simcc_x", "simcc_y", "keypoint_coordinates"):
            data.setdefault("keypoint_axis", 1)
        if semantic == "class_logits":
            data.setdefault("class_axis", -1)
        return data

    @model_validator(mode="after")
    def _check_shape(self) -> OutputSpec:
        if self.shape is not None and not (self.shape and all(d == -1 or d > 0 for d in self.shape)):
            raise ValueError("shape must be a non-empty array; a dim is -1 or a positive int")
        return self


class NmsSpec(SpecModel):
    iou_threshold: float
    score_threshold: float
    class_agnostic: bool = False
    post_nms_top_k: int | None = None


class ObjectDecodeSpec(SpecModel):
    """`object.decode`. `min_score` is the default final filter of the host: `score > min_score`."""

    selection: Literal["none", "top_k", "nms"]
    boxes_output: str | None = None
    scores_output: str | None = None
    box_format: Literal["xyxy", "xywh", "cxcywh"] = "xyxy"
    box_space: CoordinateSpace = "pixel"
    score_field: str | None = None
    class_field: str | None = None
    keep_classes: list[str] | None = None
    min_score: float = 0.7
    clamp_boxes: bool = True
    min_box_size: float | None = None
    max_detections: int | None = None
    class_logits_output: str | None = None
    score_activation: Literal["none", "sigmoid"] = "none"
    top_k: int | None = None
    nms: NmsSpec | None = None


class ObjectSpec(SpecModel):
    """`object`. An item of `classes` that is `None` is a gap: a class index that the model does not use."""

    classes: list[str | None]
    decode: ObjectDecodeSpec


class SkeletonSpec(SpecModel):
    name: str
    edges: list[list[str]]


class OverlayPartSpec(SpecModel):
    edges: list[list[str]] | None = None
    prefix: str | None = None
    edge_color: list[float]
    edge_thickness: int = 2
    keypoint_color: list[float] | None = None


class OverlaySpec(SpecModel):
    """`keypoint.overlay`. An absent `skeleton` means the first entry of `keypoint.skeletons`."""

    skeleton: str | list[list[str]] | None = None
    parts: dict[str, OverlayPartSpec] = {}
    keypoint_color: list[float] | None = None


class KeypointDecodeSpec(SpecModel):
    """`keypoint.decode`. An absent `coordinate_space` of a `coordinate` decoder means `pixel`.

    Packed keypoints use `object.decode.box_space`, and have no `coordinate_space`.
    """

    method: Literal["simcc", "coordinate"]
    depth_unit: Literal["m", "mm", "pixel"] | None = None
    coordinate_space: CoordinateSpace | None = None


class KeypointSpec(SpecModel):
    """`keypoint`. `derived_points` holds each `[prefix]` entry one time for each prefix.

    Implements: post.keypoint.schema
    """

    estimator_type: Literal["top_down", "bottom_up"]
    geometry: Literal["2d", "3d"]
    landmark_schema: str
    point_names: list[str]
    skeletons: list[SkeletonSpec]
    derived_points: dict[str, Derivation] = {}
    decode: KeypointDecodeSpec
    overlay: OverlaySpec | None = None

    @model_validator(mode="before")
    @classmethod
    def _expand_the_prefixes(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("derived_points"), dict):
            data = {**data, "derived_points": expand_derived_points(data["derived_points"])}
        return data


class ArtifactSpec(SpecModel):
    """One ONNX artifact: the file of one size and one precision."""

    filename: str
    sha256: str
    url: str | None = None
    url_sha256: str | None = None


class OnnxSpec(SpecModel):
    precision_artifacts: dict[Precision, ArtifactSpec]
    output_shapes: list[list[int]]


class SizeResizeSpec(SpecModel):
    target_size: list[int] | None = None


class SizeInputSpec(SpecModel):
    shape: list[int]
    resize: SizeResizeSpec = SizeResizeSpec()


class ScorePairSpec(SpecModel):
    a: float
    b: float


class ScoreFitSpec(SpecModel):
    dataset: str
    split: str
    recipe: str


class ScoreMapSpec(SpecModel):
    """`sizes.<size>.score_map`: the logistic map of the raw keypoint score of one size to `[0, 1]`.

    Implements: post.keypoint.score_map

    `groups` holds the pair of some groups of the landmark schema. Each other keypoint uses `a` and
    `b`. The host does not read `fit`.
    """

    method: Literal["logistic"]
    a: float
    b: float
    groups: dict[str, ScorePairSpec] = {}
    fit: ScoreFitSpec | None = None


class SizeSpec(SpecModel):
    """One size entry: `input.shape`, `input.resize.target_size`, `onnx` and `score_map`, and no other field."""

    input: SizeInputSpec
    onnx: OnnxSpec
    score_map: ScoreMapSpec | None = None

    @property
    def target_size(self) -> list[int] | None:
        """`[height, width]`, or None for a `none` resize."""
        return self.input.resize.target_size

    def artifact(self, precision: Precision) -> ArtifactSpec:
        """Return the artifact of one precision. Raise `ValueError` when the size does not have it."""
        if precision not in self.onnx.precision_artifacts:
            raise ValueError(f"no precision {precision!r}; the size has {list(self.onnx.precision_artifacts)}")
        return self.onnx.precision_artifacts[precision]


class SidecarModel(SpecModel):
    """A valid sidecar. `sizes` keeps the order of the file: the first size is the default.

    Implements: common.identity
    """

    schema_version: str
    source: SourceSpec
    model_id: str
    display_name: str
    role: list[Role]
    license: LicenseSpec
    input: InputSpec
    batching: BatchingSpec
    outputs: list[OutputSpec]
    object: ObjectSpec | None = None
    keypoint: KeypointSpec | None = None
    sizes: dict[str, SizeSpec]
    # Not a sidecar key: `load_sidecar` sets it from the landmark schema registry.
    _point_groups: tuple[str, ...] | None = PrivateAttr(default=None)

    @property
    def point_groups(self) -> tuple[str, ...] | None:
        """The landmark-schema group of each keypoint, in the order of `keypoint.point_names`.

        `load_sidecar` sets it for a keypoint detector. A model that does not come from
        `load_sidecar` has None.
        """
        return self._point_groups

    @property
    def default_size(self) -> str:
        return next(iter(self.sizes))

    def size(self, name: str) -> SizeSpec:
        """Return one size entry. An unknown size name is an error, not a fallback."""
        if name not in self.sizes:
            raise ValueError(f"no size {name!r} in the sidecar {self.model_id!r}; it has {list(self.sizes)}")
        return self.sizes[name]

    def artifact(self, size: str, precision: Precision) -> ArtifactSpec:
        """Return the artifact of one size and one precision.

        Implements: common.sizes_and_artifacts
        """
        return self.size(size).artifact(precision)

    def output(self, name: str) -> OutputSpec:
        """Return the output with this tensor name."""
        for output in self.outputs:
            if output.name == name:
                return output
        raise ValueError(f"no output {name!r} in the sidecar {self.model_id!r}")
