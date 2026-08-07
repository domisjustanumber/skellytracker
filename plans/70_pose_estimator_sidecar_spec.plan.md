---
name: Pose Estimator Sidecar Spec
overview: Extend specs/sidecar-spec.md and sidecar_validation.py for role pose_estimator — keypoint schemas via names_and_connections, pose/decode/output contracts, and input preprocessing types. Implement load_pose_keypoint_definition() using TrackedObjectDefinition. Reference sidecars for RTMW (2D wholebody), RTMW3D (SimCC 3D wholebody), RTMO (one-stage body), and YOLO26 pose. Prerequisite plan 40; consumes plan 60 batch_conversion for fixed-batch pose ONNX where applicable.
todos:
  - id: pose-spec-pose-section
    content: Port and YAML-ify pose_estimator field tables (pose, overlay, postprocessing pose branches) into specs/sidecar-spec.md; align with plan 40 input/batch_artifacts/normalization modes.
    status: pending
  - id: pose-keypoint-config-loader
    content: Implement load_pose_keypoint_definition() in sidecar_validation.py using TrackedObjectDefinition.from_yaml and rtmpose_wholebody composition rules; support keypoint_config, keypoint_definition path, or inline labels; apply keypoint_label_slice with connection filtering.
    status: pending
  - id: pose-output-decode-spec
    content: Document outputs semantic types (simcc_2d, simcc_3d, keypoints, keypoint_scores, packed_poses) and pose.decode profiles; map to rtm_preprocessing/rtm_postprocessing consumers.
    status: pending
  - id: pose-resize-methods
    content: Add input.resize.method values letterbox and affine_person_crop with validation; link affine_person_crop to top_down_single_person and pose.detector.crop_policy.
    status: pending
  - id: pose-sidecar-validation
    content: Add PoseConfig, OverlayConfig, DecodeConfig, DetectorDependency, CropPolicy Pydantic models to sidecar_validation.py; extend SidecarModel with pose/overlay fields; add @model_validator methods (pose_role_requires_pose_overlay, estimator_consistency, keypoint_schema_exclusivity, pose_input_resize_method_consistency, pose_output_keypoint_agreement, simcc_outputs_present, direct_decode_requires_nms). No separate validate_pose_sidecar_metadata() function needed.
    status: pending
  - id: reference-sidecars-rtmw-rtmw3d
    content: Add models/rtmw-x-l_384x288.yaml and models/rtmw3d-l_384x288.yaml reference artifacts with batch_artifacts, imagenet_bgr, keypoint_config, and SimCC output descriptors.
    status: pending
  - id: reference-sidecars-rtmo-yolo26-pose
    content: Add models/rtmo-l.yaml and models/yolo26-pose-nano.yaml examples covering one_stage_multi_person paths; YOLO26 pose defers batch_conversion block to plan 60 pattern.
    status: pending
  - id: pose-preprocess-resolvers
    content: Add resolve_pose_preprocess_profile() mapping sidecar input+pose to rtmo_preprocess, rtmpose_letterbox_preprocess (affine_person_crop), or detector_letterbox_preprocess (letterbox); wire in follow-up session work only if in scope at implementation time.
    status: pending
  - id: pose-documentation
    content: Extend specs/sidecar-spec.md author/consumer guides, models/README.md, CLAUDE.md; changelog row; cross-link names_and_connections directory.
    status: pending
  - id: pose-validation-tests
    content: Unit-test keypoint_config resolution (133 wholebody, 17-body subset for RTMO), RTMW3D simcc_3d outputs, validate_pose_sidecar_metadata failures, overlay skeleton edge generation from connections.
    status: pending
isProject: false
---

# Pose Estimator Sidecar Spec

## Parent plan

Follows [40_detector_sidecar_spec.plan.md](40_detector_sidecar_spec.plan.md) (this document is **plan 70** in sequence). Extends the shared sidecar contract for `role: pose_estimator` while reusing plan 40 primitives (`schema_version`, `onnx.batch_artifacts`, `input.normalization` modes, `input.resize.interpolation`, `sidecar_validation.py` base).

Plan 40 documented `pose.keypoint_config` **spec-only** and deferred the loader — **plan 70 implements** the pose role end-to-end in spec, validation, and `load_pose_keypoint_definition()`.

## Boundary with plans 40, 60, and 50

| Deliverable | Plan 40 | Plan 60 | Plan 50 | Plan 70 (this) |
|-------------|---------|---------|---------|----------------|
| Shared sidecar primitives (YAML, batch_artifacts, normalization, interpolation) | yes | extends batch_conversion | detector consume | consume |
| `input.resize.method: affine_person_crop` | — | — | — | **yes** (pose top-down) |
| `role: detector` contract | yes | — | YOLO26 detector | — |
| `role: pose_estimator` contract | stub (`keypoint_config` doc only) | batch_conversion for pose ONNX | — | **yes** |
| `load_pose_keypoint_definition()` | deferred | — | — | **yes** |
| Pose Pydantic models (`PoseConfig`, `OverlayConfig`, `DecodeConfig` + `@model_validator` on `SidecarModel`) | — | — | — | **yes** |
| `SidecarModelRegistry` / `list_pose_models()` | — | — | — | spec + Pydantic models; **session/catalog wiring optional in this plan** |
| YOLO26 **detector** session path | — | yes | yes | — |

Plan 50 remains detector-focused. Plan 70 does not block plan 50. Pose catalog integration in `RTMPoseSession` / `list_pose_models()` may land in plan 70 or a follow-up plan — spec and validation are mandatory deliverables either way.

## Prerequisite plans

- [**40 — Detector Sidecar Spec**](40_detector_sidecar_spec.plan.md) — YAML format, `onnx.batch_artifacts`, `input` contract, Pydantic `SidecarModel` base
- [**60 — Sidecar batch conversion**](60_sidecar_batch_conversion.plan.md) — recommended before checked-in YOLO26 pose / multi-batch pose ONNX examples that need `batching.batch_conversion` (same `profile_id` / `rewrite_rules` pattern as detectors; role is metadata on the sidecar, not part of `profile_id`)

## Plan sequence

| Order | Plan | Notes |
|-------|------|-------|
| **40** | [40_detector_sidecar_spec.plan.md](40_detector_sidecar_spec.plan.md) | Shared sidecar contract |
| **60** | [60_sidecar_batch_conversion.plan.md](60_sidecar_batch_conversion.plan.md) | Batch conversion (detector + pose) |
| **50** | [50_yolo26_nano_detection.plan.md](50_yolo26_nano_detection.plan.md) | YOLO26 detector catalog |
| **70** (this) | Pose estimator sidecar spec | RTMW, RTMW3D, RTMO, YOLO26 pose |
| future | Pose sidecar catalog / session wiring | If not fully covered in plan 70 implementation |

Plans **45–69** remain reserved.

## Goals

1. **One spec for all pose families** — `role: pose_estimator` sidecars describe preprocessing, outputs, decoding, skeleton overlay, and detector dependency with the same `schema_version` policy as plan 40.
2. **Reuse `names_and_connections`** — keypoint labels and skeleton edges come from [`skellytracker/trackers/rtmpose_tracker/names_and_connections/`](../skellytracker/trackers/rtmpose_tracker/names_and_connections/) via `pose.keypoint_config` or a direct `composed_of` reference; no duplicated label lists in sidecars when a packaged definition suffices.
3. **Cover four reference families** — RTMW (top-down 2D SimCC wholebody), RTMW3D (top-down 3D SimCC wholebody), RTMO (one-stage 2D multi-person), YOLO26 pose (one-stage packed rows).
4. **Explicit input/output types** — document tensor dtypes, coordinate spaces, decode profiles, and how they map to existing `rtm_preprocessing.py` / `rtm_postprocessing.py` helpers.
5. **Validation mirrors spec** — Pydantic `@model_validator` methods on `SidecarModel` (extended with `PoseConfig` / `OverlayConfig` / `DecodeConfig` in plan 70) enforce role-specific rules; human-readable checklist in `specs/sidecar-spec.md`.

## Spec ownership

| Artifact | Location |
|----------|----------|
| Canonical spec (pose sections) | [`specs/sidecar-spec.md`](../specs/sidecar-spec.md) |
| Keypoint YAML sources | [`names_and_connections/*.yaml`](../skellytracker/trackers/rtmpose_tracker/names_and_connections/) |
| Composition logic | [`TrackedObjectDefinition`](../skellytracker/trackers/base_tracker/tracked_object_definition.py) |
| Pydantic models / loader | [`sidecar_validation.py`](../skellytracker/utilities/gpu_utils/sidecar_validation.py) — Pydantic `BaseModel` hierarchy; plan 40 `SidecarModel` extended with `PoseConfig`, `OverlayConfig`, `DecodeConfig` |
| Preprocess/decode helpers | [`rtm_preprocessing.py`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py), [`rtm_postprocessing.py`](../skellytracker/utilities/gpu_utils/rtm_postprocessing.py) |

## Role and estimator types

| `role` | Required sections |
|--------|-------------------|
| `detector` | plan 40 only |
| `pose_estimator` | plan 40 shared sections + `pose`, `overlay`, pose-specific `outputs` / `postprocessing` |

| `pose.estimator_type` | Preprocess | Detector | Examples |
|-----------------------|------------|----------|----------|
| `one_stage_multi_person` | Full-frame letterbox (`input.resize.method: letterbox`) | `requires_detector: false` | RTMO, YOLO26 pose |
| `top_down_single_person` | Person affine crop (`input.resize.method: affine_person_crop`) | `requires_detector: true` | RTMW, RTMW3D |

## Keypoint schema via `names_and_connections`

### Preferred: `pose.keypoint_config`

Same rules as plan 40 — assembly order **must** match [`rtmpose_wholebody.yaml`](../skellytracker/trackers/rtmpose_tracker/names_and_connections/rtmpose_wholebody.yaml):

> `[body.23][right_hand.21][left_hand.21][face.68] = 133 total`

| Config key | Source file | Prefix |
|------------|-------------|--------|
| `body` | `rtmpose_body.yaml` | `""` |
| `hand` | `rtmpose_hand.yaml` | `right_hand_` then `left_hand_` (two copies) |
| `face` | `rtmpose_face.yaml` | `""` (names already `face_0000`…) |

**Alternative:** `pose.keypoint_definition: rtmpose_wholebody.yaml` — load the composite file directly via `TrackedObjectDefinition.from_yaml()` (equivalent to the three-key config above).

### Subset models (RTMO COCO-17)

RTMO outputs **17** body keypoints in standard COCO order — a prefix of [`rtmpose_body.yaml`](../skellytracker/trackers/rtmpose_tracker/names_and_connections/rtmpose_body.yaml) (first 17 of 23 labels).

```yaml
pose:
  keypoint_config:
    body: rtmpose_body.yaml
  keypoint_count: 17
  keypoint_label_slice: [0, 17]   # optional explicit slice; default validates first N labels
```

Consumers resolve labels from `load_pose_keypoint_definition()`, then apply `keypoint_label_slice` or validate `keypoint_count` against the resolved list length.

When `keypoint_label_slice` is present, the loader **must** also filter `connections` to pairs where both endpoints remain in the sliced label set (RTMO COCO-17 drops foot/heel edges from `rtmpose_body.yaml`).

### Schema source mutual exclusivity

Exactly one of the following must be present (validator rejects ambiguous or empty configs):

| Source | Fields |
|--------|--------|
| Region assembly | `pose.keypoint_config` |
| Composite file | `pose.keypoint_definition` (basename under `names_and_connections/`) |
| Inline | `pose.keypoint_labels` + `overlay.skeleton` (and no `keypoint_config` / `keypoint_definition`) |

`pose.keypoint_count` is **always required** in the sidecar; the loader resolves labels and validates `keypoint_count == len(labels_after_slice)`.

### Loader assembly algorithm

`load_pose_keypoint_definition()` must mirror [plan 40 prefix/order rules](40_detector_sidecar_spec.plan.md#pose-sidecar-referencing-names_and_connections):

1. If `pose.keypoint_definition` is set → `TrackedObjectDefinition.from_yaml(names_and_connections_dir / basename)`.
2. Else if `pose.keypoint_config` matches the standard wholebody triple (`body` + `hand` + `face` with default basenames) → delegate to `rtmpose_wholebody.yaml` (same result as manual assembly).
3. Else if `pose.keypoint_config` is set → assemble in fixed order: `body` (`""` prefix) → `hand` right (`right_hand_`) → `hand` left (`left_hand_`) → `face` (`""`); use `TrackedObjectDefinition.concatenate()` or equivalent composition — **ignore YAML key order** in the sidecar file.
4. Else if inline `pose.keypoint_labels` → build a minimal `TrackedObjectDefinition` from labels + `overlay.skeleton` edges.
5. Apply `keypoint_label_slice: [start, end)` to `tracked_points` and filter `connections`.
6. Raise `SidecarValidationError` on missing files, duplicate names after prefixing, or slice/count mismatch.

### RTMW3D wholebody (133)

Use the same `keypoint_config` as RTMW 2D — 3D adds a **decode axis**, not a different label order:

```yaml
pose:
  keypoint_config:
    body: rtmpose_body.yaml
    hand: rtmpose_hand.yaml
    face: rtmpose_face.yaml
  keypoint_count: 133
  coordinate_dims: 3
```

### Loader API

```python
def load_pose_keypoint_definition(
    sidecar: dict,
    *,
    names_and_connections_dir: Path | None = None,
) -> TrackedObjectDefinition:
    """Resolve pose.keypoint_config or pose.keypoint_definition into a TrackedObjectDefinition."""
```

- Default `names_and_connections_dir` → package path beside `rtmpose_wholebody.yaml`.
- Derive `pose.keypoint_labels` and `overlay.skeleton` edges from `TrackedObjectDefinition.tracked_points` and `.connections` when not inlined.
- Raise `SidecarValidationError` when referenced YAML is missing or composition produces duplicate names.

## Input contract (pose-specific)

Reuses plan 40 `input` fields. Pose models commonly use:

| Family | `input.normalization` | `input.resize.method` | `input.color_format` | Notes |
|--------|----------------------|------------------------|----------------------|-------|
| RTMW / RTMW3D | `imagenet_bgr` | `affine_person_crop` | `RGB` | ImageNet stats in BGR channel order on warped crop — see [color_format vs imagenet_bgr](#color_format-vs-imagenet_bgr) |
| RTMO | `custom` (identity on float letterbox) | `letterbox` | `RGB` | Matches [`rtmo_preprocess()`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py) with `mean=None`, `std=None` (letterbox to `float32`, pad `114`, no `/255`) |
| YOLO26 pose | `unit_float` | `letterbox` | `RGB` | Same as YOLO26 detector |

### `color_format` vs `imagenet_bgr`

OpenCV frames are BGR. For `imagenet_bgr`, apply fixed ImageNet mean/std **in BGR channel order** on the warped/letterboxed array **before** optional RGB reorder for NCHW stacking when `color_format: RGB` (matches current `RTMPoseSession` / mmpose ONNX convention). Document this in the spec — do not assume RGB-ordered mean tuples.

RTMO / YOLO26 letterbox paths follow the same `color_format` rule as plan 40 detectors after resize.

### `input.resize.method` (extended)

Plan 40 documents `letterbox` for detectors. Plan 70 adds a second closed value for top-down pose crops:

| Value | Use | Host function |
|-------|-----|---------------|
| `letterbox` | Full-frame one-stage pose (and detectors) | `detector_letterbox_preprocess` (plan 50) or `rtmo_preprocess` when `role: pose_estimator` + `one_stage_multi_person` |
| `affine_person_crop` | Top-down person crop | [`rtmpose_letterbox_preprocess()`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py) — affine warp via `top_down_affine` internally (historical rtmlib name; not full-frame letterbox) |

When `method: affine_person_crop`, `pose.detector.crop_policy` is **required** (`expand_ratio`, `maintain_aspect_ratio`). `expand_ratio` maps to the `padding` argument of `bbox_xyxy2cs` / `rtmpose_letterbox_preprocess` (default `1.25` in current code).

### `input.resize.interpolation`

Required when `input.resize` present (plan 40). Top-down affine warp uses the resolved OpenCV flag (default `linear` for RTMW / RTMW3D).

## Output and decode types

### `outputs[].semantic` (pose)

| Semantic | Description | Example families |
|----------|-------------|------------------|
| `simcc_x` / `simcc_y` | SimCC logits per keypoint axis | RTMW 2D |
| `simcc_z` | SimCC logits for depth axis | RTMW3D |
| `keypoints` | Decoded xy (or xyz) coordinates | Optional decoded ONNX outputs; usually produced in host postprocess for SimCC |
| `keypoint_scores` | Per-keypoint confidence | Derived by SimCC decode (`get_simcc_maximum`) — not a separate ONNX tensor for RTMW/RTMW3D |
| `poses` | Per-person keypoint tensor **or** packed rows | RTMO: `(N, K, 3)` pose tensor; YOLO26: rows inside `output0` |
| `detections` | Person boxes from one-stage models | RTMO: `(N, 5)` det tensor `[x1,y1,x2,y2,score]` before host NMS |

### `pose.decode` profile

| Field | Type | Description |
|-------|------|-------------|
| `pose.decode.mode` | string | `simcc_2d`, `simcc_3d`, `direct`, `packed_rows` |
| `pose.decode.simcc_split_ratio` | number | Required for `simcc_*`; matches `ModelSpec.simcc_split_ratio` (RTMW: `2.0`) |
| `pose.decode.simcc_axes` | array | e.g. `["x", "y"]` or `["x", "y", "z"]` — maps to output tensor names |
| `pose.decode.packed_row_layout` | object | Required for `packed_rows` only (YOLO26 pose) — field order and strides |
| `pose.decode.output_order` | array[string] | Optional for `direct` — ONNX output names in the order expected by `rtmo_postprocess` (det tensor first, pose tensor second) |

**`simcc_2d` (RTMW):** host runs [`get_simcc_maximum()`](../skellytracker/utilities/gpu_utils/rtm_postprocessing.py) on `simcc_x` / `simcc_y`, divides by `simcc_split_ratio`, then maps to source image via [`rtmpose_letterbox_postprocess()`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py) when `coordinate_space: person_crop`.

**`simcc_3d` (RTMW3D):** decode x/y/z SimCC tensors (extend or wrap `get_simcc_maximum` for the z axis); z is root-relative per model training (document units in `outputs[].coordinate_space`). **Implementation note:** no z-axis SimCC helper exists in skellytracker today — plan 70 spec + validation only; runtime decode lands with RTMW3D session wiring.

**`packed_rows` (YOLO26 pose):** `[batch, max_det, 6 + K×stride]` — e.g. `57 = 6 + 17×3` for COCO-17 xy+score per person. NMS is typically embedded in the export (`requires_nms: false`).

**`direct` (RTMO):** two ONNX outputs consumed by [`rtmo_postprocess()`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py): det `(1, N, 5)` and pose `(1, N, K, 3)`. ONNX tensor **names vary by export** — sidecar `outputs[].name` must match the artifact; semantics are `detections` + `poses`. Host runs **multiclass NMS** after inference (`postprocessing.requires_nms: true`).

### Coordinate spaces

| `coordinate_space` | Meaning |
|--------------------|---------|
| `letterboxed_input` | Full-frame letterbox space — apply inverse letterbox for `map_keypoints_to_source_image` |
| `person_crop` | Top-down affine crop — map using detector bbox + warp |
| `root_relative_3d` | RTMW3D z offsets relative to skeleton root (document units in sidecar) |

## `pose` section (required for `pose_estimator`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `estimator_type` | string | yes | `one_stage_multi_person` \| `top_down_single_person` |
| `requires_detector` | boolean | yes | `false` for RTMO / YOLO26 pose; `true` for RTMW / RTMW3D |
| `detector` | object \| null | yes | Crop/detector policy when `requires_detector: true` |
| `input_source` | string | yes | `source_image` \| `person_crop` |
| `instances_per_input` | string | yes | `multiple` \| `single` |
| `keypoint_config` | object | conditional | Region → `names_and_connections` basename |
| `keypoint_definition` | string | conditional | Single composite YAML basename (alternative to `keypoint_config`) |
| `keypoint_count` | integer | yes | Must match resolved label count (after slice) |
| `keypoint_label_slice` | array[2] | no | `[start, end)` into resolved labels (RTMO 17) |
| `coordinate_dims` | integer | no | `2` (default) or `3` for RTMW3D |
| `decode` | object | yes | Decode profile — see above |
| `keypoint_score_default_threshold` | number | yes | Default visibility threshold |
| `bbox_required_for_output_mapping` | boolean | yes | `true` when outputs need bbox to remap coords |

### `pose.detector` (top-down)

```yaml
detector:
  required_role: detector
  target_class_id: 0
  bbox_format: xyxy
  bbox_coordinate_space: source_image
  crop_policy:
    source: detector_box
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  compatible_model_families: [yolo26, yolox]
  # Optional runtime hint — pairing is session config, not validated against models/ at load time:
  # model_id: yolo26-nano
```

## `overlay` section

Required for `pose_estimator`. Prefer **derived skeleton** from `load_pose_keypoint_definition()`:

- Auto-generate `overlay.skeleton` edges from `TrackedObjectDefinition.connections` when sidecar omits inline skeleton.
- Optional `overlay.palette` / `overlay.groups` by region (`body`, `right_hand`, `left_hand`, `face`) — same colors as plan 40 RTMW example.
- **`overlay.skeleton` preset `coco_17_body`:** convenience alias for edges derived from `rtmpose_body.yaml` with `keypoint_label_slice: [0, 17]` (same topology as [`_COCO17_SKELETON`](../skellytracker/trackers/rtmpose_tracker/_skeleton_viz.py), but labels must match `names_and_connections` names). Prefer auto-derivation from the sliced `TrackedObjectDefinition` over hardcoding preset edges in sidecars.

## `postprocessing` (pose)

| Field | Required when |
|-------|---------------|
| `map_keypoints_to_source_image` | `one_stage_multi_person` or letterboxed outputs |
| `map_boxes_to_source_image` | RTMO / YOLO26 when boxes exposed |
| `requires_nms` | `true` for RTMO (`direct` + `rtmo_postprocess`); `false` for YOLO26 pose when NMS is in-graph |
| `nms_thr` | When `requires_nms: true` (RTMO default `0.45`) |
| `score_thr` | When `requires_nms: true` (RTMO default `0.7` in `rtmo_postprocess`) |
| `filter_class_id` | YOLO26 pose when `class_id` is present in packed rows and a single person class is expected |

## Pydantic models (extending `SidecarModel` from plan 40)

Plan 40 defines `SidecarModel` with optional `pose` and `overlay` stubs. Plan 70 adds concrete Pydantic models and `@model_validator` methods for `role: pose_estimator`.

### Pose-specific Pydantic models

```python
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from enum import Enum

class EstimatorType(str, Enum):
    one_stage_multi_person = "one_stage_multi_person"
    top_down_single_person = "top_down_single_person"

class DecodeMode(str, Enum):
    simcc_2d = "simcc_2d"
    simcc_3d = "simcc_3d"
    direct = "direct"
    packed_rows = "packed_rows"

class DecodeConfig(BaseModel):
    mode: DecodeMode
    simcc_split_ratio: float | None = None      # required for simcc_*
    simcc_axes: list[str] | None = None          # ["x","y"] or ["x","y","z"]
    packed_row_layout: dict | None = None         # required for packed_rows
    output_order: list[str] | None = None          # optional for direct

    @model_validator(mode="after")
    def simcc_requires_split_ratio(self):
        if self.mode in (DecodeMode.simcc_2d, DecodeMode.simcc_3d):
            if self.simcc_split_ratio is None:
                raise ValueError(f"simcc_split_ratio required for decode mode {self.mode}")
            if self.simcc_axes is None:
                raise ValueError(f"simcc_axes required for decode mode {self.mode}")
        return self

    @model_validator(mode="after")
    def packed_rows_requires_layout(self):
        if self.mode == DecodeMode.packed_rows and self.packed_row_layout is None:
            raise ValueError("packed_row_layout required for decode mode packed_rows")
        return self

class CropPolicy(BaseModel):
    source: Literal["detector_box"] = "detector_box"
    expand_ratio: float = Field(gt=0, default=1.25)
    maintain_aspect_ratio: bool = True

class DetectorDependency(BaseModel):
    required_role: Literal["detector"] = "detector"
    target_class_id: int = 0
    bbox_format: Literal["xyxy"] = "xyxy"
    bbox_coordinate_space: str = "source_image"
    crop_policy: CropPolicy = Field(default_factory=CropPolicy)
    compatible_model_families: list[str] | None = None

class PoseConfig(BaseModel):
    estimator_type: EstimatorType
    requires_detector: bool
    detector: DetectorDependency | None = None
    input_source: Literal["source_image", "person_crop"]
    instances_per_input: Literal["multiple", "single"]
    keypoint_config: dict[str, str] | None = None       # region → basename
    keypoint_definition: str | None = None               # single composite YAML basename
    keypoint_labels: list[str] | None = None             # inline labels (mutually exclusive)
    keypoint_count: int = Field(gt=0)
    keypoint_label_slice: tuple[int, int] | None = None  # [start, end)
    coordinate_dims: Literal[2, 3] = 2
    decode: DecodeConfig
    keypoint_score_default_threshold: float = 0.3
    bbox_required_for_output_mapping: bool

    @model_validator(mode="after")
    def estimator_consistency(self):
        """Enforce consistent field combinations per estimator_type."""
        if self.estimator_type == EstimatorType.top_down_single_person:
            if not self.requires_detector:
                raise ValueError("top_down_single_person requires requires_detector=true")
            if self.input_source != "person_crop":
                raise ValueError("top_down_single_person requires input_source=person_crop")
            if self.instances_per_input != "single":
                raise ValueError("top_down_single_person requires instances_per_input=single")
            if self.detector is None:
                raise ValueError("top_down_single_person requires pose.detector")
        elif self.estimator_type == EstimatorType.one_stage_multi_person:
            if self.requires_detector:
                raise ValueError("one_stage_multi_person requires requires_detector=false")
            if self.input_source != "source_image":
                raise ValueError("one_stage_multi_person requires input_source=source_image")
            if self.instances_per_input != "multiple":
                raise ValueError("one_stage_multi_person requires instances_per_input=multiple")
        return self

    @model_validator(mode="after")
    def keypoint_schema_exclusivity(self):
        """Exactly one of keypoint_config, keypoint_definition, or keypoint_labels."""
        sources = [
            self.keypoint_config is not None,
            self.keypoint_definition is not None,
            self.keypoint_labels is not None,
        ]
        if sum(sources) != 1:
            raise ValueError(
                "Exactly one of pose.keypoint_config, pose.keypoint_definition, "
                "or pose.keypoint_labels must be set"
            )
        return self

class OverlayPalette(BaseModel):
    body: tuple[int, int, int] | None = None
    hand: tuple[int, int, int] | None = None
    face: tuple[int, int, int] | None = None

class OverlayConfig(BaseModel):
    draw_keypoints: bool = True
    draw_skeleton: bool = True
    keypoint_radius: int = 3
    line_width: int = 2
    score_threshold: float = 0.3
    palette: OverlayPalette | None = None
    # skeleton derived from load_pose_keypoint_definition() when omitted
```

### Extended `SidecarModel` (plan 70 additions)

```python
class SidecarModel(BaseModel):
    # ... plan 40 fields ...
    pose: PoseConfig | None = None        # required when role=pose_estimator
    overlay: OverlayConfig | None = None  # required when role=pose_estimator

    @model_validator(mode="after")
    def pose_role_requires_pose_overlay(self):
        if self.role == ModelRole.pose_estimator:
            if self.pose is None:
                raise ValueError("pose section required for role=pose_estimator")
            if self.overlay is None:
                raise ValueError("overlay section required for role=pose_estimator")
        return self

    @model_validator(mode="after")
    def pose_input_resize_method_consistency(self):
        """Validate input.resize.method matches estimator_type."""
        if self.role == ModelRole.pose_estimator and self.pose and self.input and self.input.resize:
            expected = (
                ResizeMethod.affine_person_crop
                if self.pose.estimator_type == EstimatorType.top_down_single_person
                else ResizeMethod.letterbox
            )
            if self.input.resize.method != expected:
                raise ValueError(
                    f"input.resize.method must be {expected.value} for "
                    f"estimator_type={self.pose.estimator_type.value}"
                )
        return self

    @model_validator(mode="after")
    def pose_output_keypoint_agreement(self):
        """Each output with keypoint-bearing semantic must have keypoint_count matching pose."""
        if self.role != ModelRole.pose_estimator or self.pose is None:
            return self
        kp_semantics = {"simcc_x", "simcc_y", "simcc_z", "poses", "keypoints"}
        for out in self.outputs:
            if out.semantic in kp_semantics:
                if out.keypoint_count is None:
                    raise ValueError(
                        f"output '{out.name}' (semantic={out.semantic}) requires keypoint_count"
                    )
                if out.keypoint_count != self.pose.keypoint_count:
                    raise ValueError(
                        f"output '{out.name}' keypoint_count={out.keypoint_count} "
                        f"does not match pose.keypoint_count={self.pose.keypoint_count}"
                    )
        return self

    @model_validator(mode="after")
    def simcc_outputs_present(self):
        """Validate SimCC decode modes have required outputs."""
        if self.role != ModelRole.pose_estimator or self.pose is None:
            return self
        decode = self.pose.decode
        output_semantics = {o.semantic for o in self.outputs}
        if decode.mode == DecodeMode.simcc_2d:
            for ax in ["simcc_x", "simcc_y"]:
                if ax not in output_semantics:
                    raise ValueError(f"simcc_2d decode requires '{ax}' output")
        elif decode.mode == DecodeMode.simcc_3d:
            for ax in ["simcc_x", "simcc_y", "simcc_z"]:
                if ax not in output_semantics:
                    raise ValueError(f"simcc_3d decode requires '{ax}' output")
        return self

    @model_validator(mode="after")
    def direct_decode_requires_nms(self):
        if (self.role == ModelRole.pose_estimator and self.pose
                and self.pose.decode.mode == DecodeMode.direct):
            if not self.postprocessing.requires_nms:
                raise ValueError("direct decode requires postprocessing.requires_nms=true")
        return self
```

### Validation rules (summary)

All rules from the plan 70 validation section below are covered by Pydantic models and `@model_validator` methods above. The human-readable checklist in `specs/sidecar-spec.md` mirrors these validators. No separate `validate_pose_sidecar_metadata()` function is needed — `SidecarModel.model_validate()` handles it.

### `load_pose_keypoint_definition()` (unchanged from plan 40 spec)

`load_pose_keypoint_definition()` remains a free function (not a Pydantic model method) because it performs I/O (reading `names_and_connections/*.yaml` files) and returns a `TrackedObjectDefinition`, which is outside the scope of pure validation. It takes a validated `PoseConfig` (or dict) as input:

```python
def load_pose_keypoint_definition(
    pose: PoseConfig,
    *,
    names_and_connections_dir: Path | None = None,
) -> TrackedObjectDefinition:
    """Resolve pose.keypoint_config or pose.keypoint_definition into a TrackedObjectDefinition."""
```

Pydantic already validated mutual exclusivity and field presence — the loader only assembles.

## Change set — pose_estimator role (this plan)

| `schema_version` | Introduced by | Pose-specific deltas |
|------------------|---------------|----------------------|
| `vYYYY.MM.BBBB` | bumpver at plan 70 merge | `role: pose_estimator` contract; `input.resize.method: affine_person_crop`; `PoseConfig` / `OverlayConfig` / `DecodeConfig` Pydantic models; `@model_validator` methods on `SidecarModel` (estimator consistency, keypoint schema exclusivity, output/keypoint agreement, SimCC output checks, direct-decode NMS); `load_pose_keypoint_definition()` |

Pose sidecars may ship in the **same** `schema_version` bump as plan 40 if merged together; if plan 70 lands later, bump again and add a changelog row for pose-only fields.

## Estimator family matrix

| Family | `estimator_type` | Keypoints | Decode | Normalization | `keypoint_config` | Detector |
|--------|------------------|-----------|--------|---------------|-------------------|----------|
| RTMW | `top_down_single_person` | 133 | `simcc_2d` | `imagenet_bgr` | body + hand + face | yes |
| RTMW3D | `top_down_single_person` | 133 | `simcc_3d` | `imagenet_bgr` | body + hand + face | yes |
| RTMO | `one_stage_multi_person` | 17 | `direct` | `custom` (float letterbox) | body only (+ slice 17) | no |
| YOLO26 pose | `one_stage_multi_person` | 17 | `packed_rows` | `unit_float` | body only (+ slice 17) | no |

## Reference example: RTMW (`models/rtmw-x-l_384x288.yaml`)

```yaml
---
schema_version: "vYYYY.MM.BBBB"
model_id: rtmw-x-l_384x288
display_name: RTMW-X-L 384x288
family: rtmw
role: pose_estimator

onnx:
  batch_artifacts:
    1:
      precision_artifacts:
        fp32:
          filename: rtmw-x-l_384x288_fp32.onnx
          input_dtype: float32

input:
  name: input
  dtype_by_precision:
    fp32: float32
  shape: [1, 3, 384, 288]
  layout: NCHW
  dynamic_axes: {}
  color_format: RGB
  normalization: imagenet_bgr
  resize:
    method: affine_person_crop
    target_size: [384, 288]
    preserve_aspect_ratio: true
    pad_value: 0
    interpolation: linear
  coordinate_origin: top_left

batching:
  batch_axis: 0
  supports_dynamic_batch: false

outputs:
  - name: simcc_x
    dtype: float32
    shape: [1, 133, 576]
    rank: 3
    semantic: simcc_x
    keypoint_axis: 1
    keypoint_count: 133
    coordinate_space: person_crop
  - name: simcc_y
    dtype: float32
    shape: [1, 133, 768]
    rank: 3
    semantic: simcc_y
    keypoint_axis: 1
    keypoint_count: 133
    coordinate_space: person_crop

pose:
  estimator_type: top_down_single_person
  requires_detector: true
  input_source: person_crop
  instances_per_input: single
  keypoint_config:
    body: rtmpose_body.yaml
    hand: rtmpose_hand.yaml
    face: rtmpose_face.yaml
  keypoint_count: 133
  coordinate_dims: 2
  decode:
    mode: simcc_2d
    simcc_split_ratio: 2.0
    simcc_axes: [x, y]
  keypoint_score_default_threshold: 0.3
  bbox_required_for_output_mapping: true
  detector:
    required_role: detector
    target_class_id: 0
    bbox_format: xyxy
    bbox_coordinate_space: source_image
    crop_policy:
      source: detector_box
      expand_ratio: 1.25
      maintain_aspect_ratio: true
    compatible_model_families: [yolo26, yolox]

postprocessing:
  confidence_threshold_default: 0.3
  map_keypoints_to_source_image: true

overlay:
  draw_keypoints: true
  draw_skeleton: true
  keypoint_radius: 3
  line_width: 2
  score_threshold: 0.3
  # skeleton derived from names_and_connections when omitted
```

## Reference example: RTMW3D (`models/rtmw3d-l_384x288.yaml`)

Same top-down orchestration as RTMW; differences:

```yaml
model_id: rtmw3d-l_384x288
display_name: RTMW3D-L 384x288
family: rtmw3d
role: pose_estimator

outputs:
  - name: simcc_x
    semantic: simcc_x
    keypoint_count: 133
    # shapes per exported ONNX — widths are model-specific
  - name: simcc_y
    semantic: simcc_y
    keypoint_count: 133
  - name: simcc_z
    semantic: simcc_z
    keypoint_count: 133

pose:
  keypoint_config:
    body: rtmpose_body.yaml
    hand: rtmpose_hand.yaml
    face: rtmpose_face.yaml
  keypoint_count: 133
  coordinate_dims: 3
  decode:
    mode: simcc_3d
    simcc_split_ratio: 2.0
    simcc_axes: [x, y, z]
  # detector block same as RTMW

postprocessing:
  map_keypoints_to_source_image: true
  # 3D coords documented as root_relative_3d on simcc_z decode path
```

Validate exported ONNX tensor names/shapes at implementation time and update the example sidecar to match the checked-in artifact.

## Reference example: RTMO (`models/rtmo-l.yaml`)

```yaml
---
schema_version: "vYYYY.MM.BBBB"
model_id: rtmo-l
display_name: RTMO-L COCO
family: rtmo
role: pose_estimator

onnx:
  batch_artifacts:
    1:
      precision_artifacts:
        fp32:
          filename: rtmo-l_fp32.onnx
          input_dtype: float32

input:
  name: input
  dtype_by_precision:
    fp32: float32
  shape: [1, 3, 640, 640]
  layout: NCHW
  dynamic_axes: {}
  color_format: RGB
  normalization:
    mode: custom
    scale: 1.0
    mean: [0.0, 0.0, 0.0]
    std: [1.0, 1.0, 1.0]
  resize:
    method: letterbox
    target_size: [640, 640]
    preserve_aspect_ratio: true
    pad_value: 114
    interpolation: linear
  coordinate_origin: top_left

batching:
  batch_axis: 0
  supports_dynamic_batch: false

pose:
  estimator_type: one_stage_multi_person
  requires_detector: false
  detector: null
  input_source: source_image
  instances_per_input: multiple
  keypoint_config:
    body: rtmpose_body.yaml
  keypoint_count: 17
  keypoint_label_slice: [0, 17]
  coordinate_dims: 2
  decode:
    mode: direct
    output_order: [dets, poses]   # replace with actual ONNX output names from artifact
  keypoint_score_default_threshold: 0.3
  bbox_required_for_output_mapping: false

outputs:
  - name: dets
    semantic: detections
    shape: [1, 8400, 5]
    fields: [x1, y1, x2, y2, score]
    box_format: xyxy
    coordinate_space: letterboxed_input
  - name: poses
    semantic: poses
    shape: [1, 8400, 17, 3]
    fields: [x, y, score]
    keypoint_axis: 2
    keypoint_count: 17
    coordinate_space: letterboxed_input

postprocessing:
  requires_nms: true
  nms_thr: 0.45
  score_thr: 0.7
  confidence_threshold_default: 0.3
  map_boxes_to_source_image: true
  map_keypoints_to_source_image: true

overlay:
  draw_keypoints: true
  draw_skeleton: true
  # skeleton derived from sliced rtmpose_body.yaml when omitted
```

## Reference example: YOLO26 pose (`models/yolo26-pose-nano.yaml`)

One-stage packed output; shares input/normalization with YOLO26 detector (plan 40). **`batching.batch_conversion`** block per [60_sidecar_batch_conversion.plan.md](60_sidecar_batch_conversion.plan.md) (`profile_id: yolo26-pose-static-batch` — confirm `offset_initializer_name` against the exported ONNX at implementation time).

```yaml
---
schema_version: "vYYYY.MM.BBBB"
model_id: yolo26-pose-nano
display_name: YOLO26 Pose Nano
family: yolo26
role: pose_estimator

onnx:
  batch_artifacts:
    2:
      precision_artifacts:
        fp32:
          filename: yolo26-pose-nano_b2_fp32.onnx
          input_dtype: float32

input:
  name: images
  dtype_by_precision:
    fp32: float32
  shape: [2, 3, 640, 640]
  layout: NCHW
  color_format: RGB
  normalization: unit_float
  resize:
    method: letterbox
    target_size: [640, 640]
    preserve_aspect_ratio: true
    pad_value: 114
    interpolation: linear
  coordinate_origin: top_left

batching:
  batch_axis: 0
  supports_dynamic_batch: false
  batch_conversion:
    profile_id: yolo26-pose-static-batch
    source_batch_size: 2
    target_batch:
      minimum: 1
      axis: 0
    rewrite_rules: []   # fill from plan 60 / exporter — placeholder
    validation:
      input_shape: [target_batch, 3, 640, 640]
      output_shapes:
        - [target_batch, 300, 57]

pose:
  estimator_type: one_stage_multi_person
  requires_detector: false
  detector: null
  input_source: source_image
  instances_per_input: multiple
  keypoint_config:
    body: rtmpose_body.yaml
  keypoint_count: 17
  keypoint_label_slice: [0, 17]
  coordinate_dims: 2
  decode:
    mode: packed_rows
    packed_row_layout:
      fields: [x1, y1, x2, y2, score, class_id]
      keypoint_fields: [x, y, score]
      keypoint_stride: 3
      keypoint_start_index: 6
  keypoint_score_default_threshold: 0.7
  bbox_required_for_output_mapping: false

outputs:
  - name: output0
    semantic: poses
    shape: [2, 300, 57]
    coordinate_space: letterboxed_input
    requires_nms: false
    max_detections: 300

postprocessing:
  requires_nms: false
  confidence_threshold_default: 0.7
  map_boxes_to_source_image: true
  map_keypoints_to_source_image: true

overlay:
  draw_keypoints: true
  draw_skeleton: true
```

## Implementation plan

### 1. Spec (`specs/sidecar-spec.md`)

- Port pose sections from retired draft spec; convert JSON examples to YAML.
- Merge plan 40 deltas (normalization modes, `batch_artifacts`, interpolation).
- Add pose author guide: pick `keypoint_config` vs `keypoint_definition`, decode mode, detector dependency.
- Changelog row at plan 70 `schema_version` bump.

### 2. Keypoint loader (`sidecar_validation.py`)

- Implement `load_pose_keypoint_definition()` using `TrackedObjectDefinition` per [loader assembly algorithm](#loader-assembly-algorithm).
- Implement `derive_overlay_skeleton_from_definition(defn) -> list[dict]` (edge list with `from` / `to` label strings).
- Unit-test 133-label order vs `rtmpose_wholebody.yaml`; RTMO 17-slice with connection filtering; hand prefix rules.

### 3. Pose Pydantic models (extend `SidecarModel`)

- Add `PoseConfig`, `OverlayConfig`, `DecodeConfig`, `DetectorDependency`, `CropPolicy` Pydantic models to `sidecar_validation.py`.
- Add `pose: PoseConfig | None` and `overlay: OverlayConfig | None` fields to `SidecarModel`.
- Add `@model_validator` methods to `SidecarModel`: `pose_role_requires_pose_overlay`, `pose_input_resize_method_consistency`, `pose_output_keypoint_agreement`, `simcc_outputs_present`, `direct_decode_requires_nms`.
- `PoseConfig` includes `@model_validator` methods: `estimator_consistency`, `keypoint_schema_exclusivity`.
- `DecodeConfig` includes `@model_validator` methods: `simcc_requires_split_ratio`, `packed_rows_requires_layout`.
- No separate `validate_pose_sidecar_metadata()` function — `SidecarModel.model_validate()` handles everything.
- No `SCHEMA_REQUIREMENTS` callable list — version gating via conditional checks in `@model_validator` methods.

### 4. Preprocess resolver (optional wiring)

- `resolve_pose_preprocess_profile(sidecar) -> PosePreprocessProfile` enum or struct mapping to existing `rtmo_preprocess`, `rtmpose_letterbox_preprocess`, `detector_letterbox_preprocess`.
- `resolve_pose_preprocess_profile` must branch on `input.resize.method` and `input.normalization` (not only `family`).
- Full `RTMPoseSession` / `list_pose_models()` integration may ship in this plan or a follow-up — document either way in PR.

### 5. Reference artifacts (`models/`)

- `rtmw-x-l_384x288.yaml`, `rtmw3d-l_384x288.yaml`, `rtmo-l.yaml`, `yolo26-pose-nano.yaml` (sidecar YAML only until ONNX publishing pipeline lands).

### 6. Documentation

- [`models/README.md`](../models/README.md) — pose sidecar subsection.
- [`CLAUDE.md`](../CLAUDE.md) — pose sidecar + `names_and_connections` linkage.

## Validation plan

- Pydantic model: `SidecarModel.model_validate()` on RTMW sidecar → success; on RTMW with missing `pose` → `ValidationError`.
- `PoseConfig.estimator_consistency`: validates `top_down_single_person` requires detector + `person_crop` + `single`; `one_stage_multi_person` requires no detector + `source_image` + `multiple`.
- `PoseConfig.keypoint_schema_exclusivity`: rejects when 0 or >1 of `keypoint_config`/`keypoint_definition`/`keypoint_labels` are set.
- `Simcc_outputs_present`: validates `simcc_2d` has `simcc_x`+`simcc_y` outputs; `simcc_3d` has `+simcc_z`.
- `pose_output_keypoint_agreement`: validates each keypoint-bearing output's `keypoint_count` matches `pose.keypoint_count`.
- `direct_decode_requires_nms`: validates `postprocessing.requires_nms=true` for `direct` decode.
- `pose_input_resize_method_consistency`: validates `affine_person_crop` for top-down, `letterbox` for one-stage.
- Loader: wholebody 133 order, right/left hand prefixes, face without double-prefix; connection filtering on slice.
- RTMO: 17 labels from body slice; skeleton from filtered `rtmpose_body.yaml` connections.
- RTMW3D: `simcc_3d` requires z tensor; `coordinate_dims: 3`.
- YOLO26 pose: `packed_rows` layout `57 = 6 + 17×3`; `unit_float` letterbox; plan 60 `batch_conversion` block (separate plan 60 tests).
- Reject: `top_down` without detector, `keypoint_count` mismatch, missing `decode.mode`, both `keypoint_config` and `keypoint_definition`, `imagenet_bgr` with `letterbox` on top-down.

## Main risks

- **Exported ONNX shape drift** — SimCC tensor widths differ by input resolution; sidecars must match actual artifacts (validate at session startup). RTMO anchor count (`8400` in example) is illustrative — use real export shapes.
- **RTMW3D z semantics** — root-relative depth units are model-specific; document in sidecar, do not hardcode in validator. Z-axis SimCC decode is not implemented in skellytracker yet.
- **Label slice vs training** — RTMO/YOLO26 must use COCO-17 order matching `rtmpose_body.yaml` first 17 names; foot keypoint edges must be stripped after slice.
- **RTMO normalization** — not `imagenet_bgr` or `unit_float`; current `rtmo_preprocess` uses float letterbox without `/255`. Sidecar must use `custom` identity or a future dedicated mode — do not copy RTMW normalization onto RTMO.
- **`imagenet_bgr` vs `color_format: RGB`** — mean/std apply in BGR order before channel reorder; document clearly to avoid exporter/runtime mismatch.
- **Overlap with legacy `ModelSpec`** — until catalog migrates, sidecars and `ModelSpec` may coexist; plan 70 is the target contract for new pose models.
- **YOLO26 pose `batch_conversion`** — `profile_id` / `rewrite_rules` must be validated against real ONNX; do not copy detector `offset_initializer_name` blindly.

## Related Plans

- [40_detector_sidecar_spec.plan.md](40_detector_sidecar_spec.plan.md) — **prerequisite**; shared sidecar primitives.
- [60_sidecar_batch_conversion.plan.md](60_sidecar_batch_conversion.plan.md) — batch conversion for YOLO26 pose ONNX.
- [50_yolo26_nano_detection.plan.md](50_yolo26_nano_detection.plan.md) — detector counterpart (orthogonal).
- [future_streaming_pipeline_implementation.plan.md](future_streaming_pipeline_implementation.plan.md) — may consume pose sidecars in graph executor.

## Related files

- [`specs/sidecar-spec.md`](../specs/sidecar-spec.md)
- [`skellytracker/trackers/rtmpose_tracker/names_and_connections/`](../skellytracker/trackers/rtmpose_tracker/names_and_connections/)
- [`skellytracker/trackers/base_tracker/tracked_object_definition.py`](../skellytracker/trackers/base_tracker/tracked_object_definition.py)
- [`skellytracker/utilities/gpu_utils/sidecar_validation.py`](../skellytracker/utilities/gpu_utils/sidecar_validation.py)
- [`skellytracker/utilities/gpu_utils/rtm_preprocessing.py`](../skellytracker/utilities/gpu_utils/rtm_preprocessing.py)
- [`skellytracker/utilities/gpu_utils/rtm_postprocessing.py`](../skellytracker/utilities/gpu_utils/rtm_postprocessing.py)
- [`skellytracker/utilities/gpu_utils/model_registry.py`](../skellytracker/utilities/gpu_utils/model_registry.py) — legacy `ModelSpec` reference during migration
