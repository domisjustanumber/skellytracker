---
name: Sidecar vs ModelSpec Comparison
overview: Detailed comparison between the existing ModelSpec/@catalog_model registry approach and the proposed sidecar-based ModelSidecarSpec approach.
isProject: false
---

# Sidecar Spec vs. ModelSpec: Approach Comparison

This document compares two approaches to model metadata management in skellytracker:

| Approach | Status | Key Artifact |
|----------|--------|-------------|
| **ModelSpec / @catalog_model** | ✅ In production (`dom/rtmpose-config-models` branch) | `skellytracker/utilities/gpu_utils/model_registry.py` |
| **Model Sidecar Spec** | 🔲 Planned (Plan 40) | `specs/sidecar-spec.md` + `sidecar_validation.py` |

---

## 1. High-Level Philosophy

| Aspect | ModelSpec (Current) | Model Sidecar Spec (Plan 40) |
|--------|---------------------|------------------------------|
| **Metadata location** | Embedded in Python source code (`ModelSpec` factory classmethods) | Co-located YAML file (`{model_id}.yaml`) beside ONNX artifacts |
| **Discoverability** | `@catalog_model` decorator scanned at import time → `MODEL_REGISTRY` | Filesystem scan of `models/*.yaml` → `SidecarModelRegistry` (plan 50) |
| **Adding a model** | Write a new `@classmethod` on `ModelSpec`, add URL to `MODEL_URLS`, commit + release | Write a YAML file, place beside ONNX, no code change needed |
| **Versioning** | Implicit — tied to skellytracker release | Explicit `schema_version` string in each sidecar, comparable to skellytracker version |
| **Extensibility** | New fields require `ModelSpec` schema change + migration | New fields gated by `schema_version`; older sidecars remain valid if `installed >= schema_version` |
| **External tooling** | Exporters must replicate `ModelSpec` logic or produce Python code | Exporters write YAML to a documented spec; skellytracker validates on load |

---

## 2. Model Identity & Catalog

### ModelSpec (Current)

```python
# Hardcoded in model_registry.py
MODEL_URLS: dict[str, str] = {
    "yolox-tiny": "https://download.openmmlab.com/...",
    "rtmo-s": "https://download.openmmlab.com/...",
    # ... 14 entries
}

class ModelSpec(BaseModel):
    source: ModelSource         # URL, HF repo, or local path
    format: Literal["onnx", "pth", "pt", "engine"]
    input_size: tuple[int, int]
    num_keypoints: int
    # ...

    @classmethod
    @catalog_model("yolox-tiny", "YOLOX-Tiny", "detector")
    def yolox_tiny(cls) -> "ModelSpec":
        return cls(source=ModelSource(url=MODEL_URLS["yolox-tiny"]), ...)

# Built at import time
MODEL_REGISTRY = _build_model_registry()   # scans @catalog_model methods
MODEL_CATALOG  = _build_model_catalog(MODEL_REGISTRY)
```

**Characteristics:**
- All models are "known" at release time — adding one means a code change
- `model_id` is an arbitrary string key into `MODEL_URLS`
- Each `@catalog_model` factory produces exactly one `ModelSpec`
- No concept of "variants" (different batch sizes, precisions) within one model entry
- Identity is just `(id, display_name, role)` — no `family`, no schema version

### Model Sidecar Spec (Plan 40)

```yaml
# models/yolo26-nano.yaml — lives beside ONNX files
---
schema_version: "vYYYY.MM.BBBB"
model_id: yolo26-nano
display_name: YOLO26 Nano
family: yolo26
role: detector
# ... full input/output/batching contract follows
```

**Characteristics:**
- Models are data, not code — YAML file is self-describing
- `schema_version` enables forward/backward compatibility checks
- `family` groups related models (e.g., `yolo26`, `rtmw`, `rtmo`)
- `role` is `detector` or `pose_estimator` (vs. current `detector` / `pose` / `one_stage_body`)
- One sidecar describes all batch × precision variants for a model via `onnx.batch_artifacts`
- No download URLs in the sidecar — ONNX files are co-located or resolved by the registry

---

## 3. Preprocessing Contract

### ModelSpec (Current)

```python
class ModelSpec(BaseModel):
    preprocess_mode: Literal["rtmo", "rtmpose_letterbox", "simple_letterbox",
                              "mediapipe", "none"]
    mean: tuple[float, float, float] | None = None
    std: tuple[float, float, float] | None = None
    # No interpolation control — hardcoded cv2.INTER_LINEAR in rtm_preprocessing.py
    # No per-precision dtype variation
    # No explicit normalization mode — derived from mean/std presence
```

**How preprocessing is selected:**
1. Consumer reads `model_spec.preprocess_mode`
2. Dispatches to `rtmo_preprocess()`, `rtmpose_letterbox()`, `simple_letterbox()`, or `mediapipe_preprocess()`
3. Passes `mean`/`std` tuples as parameters
4. Interpolation is always `cv2.INTER_LINEAR` (hardcoded)
5. No per-precision variant support for input dtype

**Pros:**
- Simple — one string picks the pipeline
- Mean/std are explicit numbers, easy to verify

**Cons:**
- `preprocess_mode` is a grab-bag — mixes model architecture (`rtmo`) with resize strategy (`letterbox`) with framework (`mediapipe`)
- Cannot express per-precision differences (e.g., `fp16` uses `unit_float`, `int8` uses raw `uint8`)
- Interpolation is implicit and non-overridable
- Normalization intent is opaque — is `mean=(0,0,0), std=(1,1,1)` the same as "none"? Is `mean=(0,0,0), std=(255,255,255)` the same as `unit_float`?

### Model Sidecar Spec (Plan 40)

```yaml
input:
  name: images
  dtype_by_precision:
    fp32: float32
    fp16: float16
    int8: uint8
  shape: [2, 3, 640, 640]
  layout: NCHW
  color_format: RGB
  normalization: unit_float           # closed enum
  normalization_by_precision:         # per-precision override
    int8: none
  resize:
    method: letterbox
    target_size: [640, 640]
    preserve_aspect_ratio: true
    pad_value: 114
    interpolation: linear             # explicit interpolation
  coordinate_origin: top_left
```

**How preprocessing is selected:**
1. Consumer calls `resolve_normalization_mode(sidecar, precision)` → `"unit_float"`, `"none"`, `"imagenet_bgr"`, or `"custom"`
2. Consumer calls `resolve_resize_interpolation(sidecar.input.resize.interpolation)` → `cv2.INTER_LINEAR`
3. Single `detector_letterbox_preprocess()` path (plan 50), parameterized by resolved values
4. Resolution order: `normalization_by_precision[precision]` → `dtype_by_precision[precision] == uint8` default → top-level `normalization`

**Pros:**
- Semantic normalization modes (`unit_float`, `imagenet_bgr`, `none`) communicate intent
- Per-precision overrides for quantized (`int8`) vs float paths
- Explicit interpolation — no hidden hardcoded defaults
- `dtype_by_precision` and `input_shape` are part of the contract
- Single preprocessing path (plan 50) instead of mode-dispatch spaghetti

**Cons:**
- More fields to author correctly
- `custom` mode still requires raw `scale`/`mean`/`std` tuples for rare cases

---

## 4. ONNX Artifact Management

### ModelSpec (Current)

- **No multi-artifact support** — each `ModelSpec` points to exactly one model file (via `ModelSource`)
- **No batch size axis** — batch dimension is implicit or handled externally
- **No precision variants** — no way to express "this model has fp32 and fp16 ONNX files"
- **Download only** — `resolve_model_path()` downloads a `.zip` and extracts the `.onnx`

### Model Sidecar Spec (Plan 40)

```yaml
onnx:
  batch_artifacts:
    2:
      precision_artifacts:
        fp32:
          filename: yolo26-nano_b2_fp32.onnx
          sha256: "<hex>"
          input_dtype: float32
        fp16:
          filename: yolo26-nano_b2_fp16.onnx
          sha256: "<hex>"
          input_dtype: float16
        int8:
          filename: yolo26-nano_b2_int8.onnx
          sha256: "<hex>"
          input_dtype: uint8
      input_shape: [2, 3, 640, 640]
      output_shapes:
        - [2, 300, 6]
    4:
      precision_artifacts:
        fp32:
          filename: yolo26-nano_b4_fp32.onnx
          # ...
      input_shape: [4, 3, 640, 640]
      output_shapes:
        - [4, 300, 6]
```

**Characteristics:**
- **Multi-batch × multi-precision** — one sidecar lists ALL native variants
- **Batch-dim validation** — `batch_size` must match a key in `batch_artifacts` (plan 40; plan 60 adds conversion)
- **Per-group shapes** — when multiple batch keys exist, each group has its own `input_shape`/`output_shapes`
- **Optional `sha256`** — integrity verification without mandatory hashing
- **Filename convention**: `{model_id}_b{batch}_{precision}.onnx`

---

## 5. Output Contract

### ModelSpec (Current)

```python
class ModelSpec(BaseModel):
    num_keypoints: int = 21
    # No output tensor structure
    # No bounding box format
    # No NMS configuration
    # No class ID semantics
```

The output contract is **entirely implicit** — consumers must know:
- Which output tensor index is detections vs. keypoints (hardcoded in `rtmo_postprocess`)
- Bounding box format (`xyxy` assumed)
- Score field location
- Class ID mapping ("person is class 0" assumed)

### Model Sidecar Spec (Plan 40)

```yaml
outputs:
  - name: output0
    dtype: float32
    shape: [2, 300, 6]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score, class_id]
    box_format: xyxy
    coordinate_space: letterboxed_input
    requires_nms: false
    class_id_base: 0
    person_class_id: 0
    score_field: score
    class_field: class_id
    max_detections: 300
    may_include_non_person_classes: true

postprocessing:
  requires_nms: false
  filter_class_id: 0
  confidence_threshold_default: 0.7
  map_boxes_to_source_image: true
```

**Characteristics:**
- Full output tensor structure declared
- Bounding box format explicit (`xyxy`, `xywh`, `cxcywh`)
- NMS requirements declared
- Class ID semantics self-documenting
- Coordinate space declared (`letterboxed_input` → consumer maps back)

---

## 6. Pose/Keypoint Configuration

### ModelSpec (Current)

```python
class ModelSpec(BaseModel):
    num_keypoints: int = 21
    # No keypoint names
    # No skeleton connections
    # No overlay/palette info
    # No prefix rules for composite (body + hand + face)
```

Keypoint metadata lives in separate `names_and_connections/*.yaml` files, loaded by the RTMPose tracker independently. The `ModelSpec` only carries the count.

### Model Sidecar Spec (Plan 40)

```yaml
pose:
  estimator_type: top_down_single_person
  keypoint_config:
    body: rtmpose_body.yaml
    hand: rtmpose_hand.yaml
    face: rtmpose_face.yaml

overlay:
  palette:
    body: [0, 255, 0]
    hand: [255, 128, 0]
    face: [0, 128, 255]
```

**Characteristics:**
- `keypoint_config` references existing `names_and_connections/*.yaml` by basename
- Prefix rules codified (`body` → no prefix, `hand` → `right_hand_`/`left_hand_`, `face` → no prefix)
- Assembly order fixed: `[body.23][right_hand.21][left_hand.21][face.68]`
- `overlay.palette` for visualization colors
- Full loader deferred to plan 70

---

## 7. Validation & Error Handling

### ModelSpec (Current)

```python
# Pydantic BaseModel — validation at construction time
class ModelSpec(BaseModel):
    source: ModelSource
    format: Literal["onnx", "pth", "pt", "engine"]
    input_size: tuple[int, int]
    # ...

# Registry validation at import time:
def _validate_registry_entry(model_id: str, entry: ModelRegistryEntry) -> None:
    if model_id not in MODEL_URLS:
        raise ValueError(...)
```

- **Pydantic for `ModelSpec` fields** — type coercion, required checks, `Literal` enums
- **Import-time registry validation** — `MODEL_URLS` vs `@catalog_model` consistency
- **No runtime version check** — nothing prevents loading a model spec from a newer skellytracker
- **Error type**: `pydantic.ValidationError` (field-level) or generic `ValueError`

### Model Sidecar Spec (Plan 40) — Also Pydantic

```python
# Pydantic BaseModel hierarchy mirroring the YAML spec
class SidecarModel(BaseModel):
    schema_version: str = Field(pattern=r"^v?\d{4}\.\d{2}\.\d{4}$")
    model_id: str
    role: ModelRole
    onnx: OnnxConfig | None = None
    input: InputConfig | None = None
    # ...

    @model_validator(mode="after")
    def check_schema_version_stable(self): ...

    @model_validator(mode="after")
    def version_not_newer_than_installed(self): ...

# Usage:
raw = yaml.safe_load(path.read_text())
sidecar = SidecarModel.model_validate(raw)  # Pydantic ValidationError on failure
```

**Characteristics:**
- **Same validation engine** — both approaches use Pydantic `BaseModel`
- **Schema version gating** — `@model_validator` methods reject newer sidecars
- **Typed result** — `sidecar` is a `SidecarModel`, not a dict; IDE autocomplete works
- **Composable** — plan 60 adds `BatchingConversionConfig`, plan 70 adds `PoseConfig` as new fields + validators
- **Error type**: standard `pydantic.ValidationError` (no custom error class needed)

---

## 8. Batching Model

### ModelSpec (Current)

```python
class ModelSpec(BaseModel):
    supports_batching: bool | None = None  # None = probe at runtime
    # No batch_size field
    # No batch conversion
    # No native batch size enumeration
```

- Batch support is a boolean flag (or auto-detected)
- No way to express "supports batches of exactly 2 and 4"
- No batch conversion at all — must match native batch

### Model Sidecar Spec (Plan 40)

```yaml
batching:
  batch_axis: 0
  supports_dynamic_batch: false

# Native batches derived from onnx.batch_artifacts keys
# Plan 40: runtime batch must be a key in batch_artifacts
# Plan 60: adds batching.batch_conversion for non-native targets
```

- Native batches enumerated via `onnx.batch_artifacts` keys
- `supports_dynamic_batch` for future dynamic-batch models
- `batch_axis` explicit (typically 0 for NCHW)
- Plan 60 adds `batch_conversion` profiles for translating between native batches

---

## 9. Dependency & Lifecycle

### ModelSpec (Current)

```
skellytracker release
  └── model_registry.py (all models hardcoded)
       ├── MODEL_URLS (download URLs)
       ├── ModelSpec factories (@catalog_model)
       └── MODEL_REGISTRY / MODEL_CATALOG (built at import)
```

- **Coupled to skellytracker release cycle** — new model = new skellytracker release
- **Models downloaded from CDN** at first use, cached in `~/.cache/skellytracker/models/`
- **No offline/distributed model support** without code change

### Model Sidecar Spec (Plan 40)

```
models/
├── yolo26-nano.yaml          ← sidecar (spec contract)
├── yolo26-nano_b2_fp16.onnx  ← ONNX artifact
├── yolo26-nano_b2_fp32.onnx
├── yolo26-nano_b2_int8.onnx
└── rtmw-l-wholebody.yaml     ← future pose estimator sidecar (plan 70)

skellytracker/
├── specs/sidecar-spec.md         ← canonical human-readable spec
├── sidecar_validation.py          ← Python validators (plan 40)
└── SidecarModelRegistry            ← catalog scan (plan 50)
```

- **Decoupled from skellytracker release** — new model = new YAML + ONNX files, no code change
- **Sidecars versioned independently** — `schema_version` determines compatibility
- **ONNX files co-located** with sidecar (or referenced by registry)
- **External exporters** write YAML to the spec, not Python code

---

## 10. Migration Path

The plan is **coexistence**, not replacement:

| Model Source | Registry | Status |
|-------------|----------|--------|
| Existing RTMPose/RTMO/YOLOX/MediaPipe | `MODEL_REGISTRY` / `MODEL_CATALOG` (hardcoded) | ✅ Keep indefinitely |
| New YOLO26 detector | `SidecarModelRegistry` (YAML scan) | 🔲 Plan 40+50+60 |
| Future RTMW3D/RTMO/YOLO26-pose | `SidecarModelRegistry` (YAML scan) | 🔲 Plan 70 |
| New external/community models | `SidecarModelRegistry` (YAML scan) | 🔲 Drop-in YAML |

The `SidecarModelRegistry` sits **beside** `MODEL_CATALOG` — not replacing it. Plan 50's `list_detection_models()` merges both sources. Existing models never need sidecars written for them (though they could be migrated gradually).

---

## 11. Summary Table

| Dimension | ModelSpec (Current) | Model Sidecar (Plan 40) |
|-----------|---------------------|-------------------------|
| Format | Python code (Pydantic) | YAML file |
| Location | `model_registry.py` | `models/{model_id}.yaml` |
| Versioning | None (release-coupled) | `schema_version` string per sidecar |
| Multi-batch | ❌ | ✅ `onnx.batch_artifacts` |
| Multi-precision | ❌ | ✅ per-group `precision_artifacts` |
| Interpolation | Hardcoded `INTER_LINEAR` | Explicit `resize.interpolation` enum |
| Normalization | Raw `mean`/`std` tuples | Semantic enum + `custom` fallback |
| Per-precision dtype | ❌ | ✅ `dtype_by_precision` |
| Output contract | Implicit (count only) | Full tensor structure + semantics |
| Pose config | Separate files only | `keypoint_config` references in sidecar |
| Validation | Pydantic `BaseModel` (field-level) | Pydantic `BaseModel` hierarchy + `@model_validator` (version gate, cross-field) |
| Error handling | `pydantic.ValidationError` / `ValueError` | `pydantic.ValidationError` (standard, with field paths) |
| Schema evolution | Breaking changes in `ModelSpec` | Add fields + `@model_validator` methods; older sidecars valid at their `schema_version` |
| New model workflow | Code change + release | YAML file + ONNX drop-in |
| External tooling | Replicate Python logic | Write YAML to documented spec |
| Batch conversion | ❌ | Plan 60 (`batch_conversion` profiles) |
| Downstream consumer | `preprocess_mode` dispatch | `resolve_normalization_mode()` + `resolve_resize_interpolation()` |

---

## 12. Key Architectural Insight

The **fundamental shift** is from:

> **"The code knows about models"** (ModelSpec — models are enumerated in Python, preprocessing is mode-dispatched, metadata is scattered across factory methods and separate YAML files)

to:

> **"Models describe themselves"** (Sidecar — each model carries its complete I/O contract in a validated YAML file, Pydantic models provide type-safe validation at load time, preprocessing is parameterized from resolved sidecar fields, and the code is a generic consumer of the spec)

**Both approaches use Pydantic** for validation — the difference is where the model metadata lives. In the current approach, Pydantic validates Python-authored `ModelSpec` objects. In the sidecar approach, Pydantic validates YAML-authored `SidecarModel` objects parsed from co-located files. The sidecar approach decouples model metadata from the skellytracker release cycle.

This aligns with the broader rearchitecture goal in the `XX_catch_up_with_upstream` plans: the `core/` package should be a generic pipeline that operates on data-driven model descriptors, not a collection of model-specific code paths.
