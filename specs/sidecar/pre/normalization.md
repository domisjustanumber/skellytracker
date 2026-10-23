---
id: pre.normalize
title: Normalization
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - input.normalization=none
  - input.normalization=unit_float
  - input.normalization=imagenet_bgr
  - input.normalization=imagenet_rgb
  - input.normalization.mode=custom
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CustomNormalization  # partial. Nothing checks input.color_format against the normalization mode.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::build_normalization_fn  # partial. imagenet_bgr has only the legacy meaning (notes/decisions/0009-imagenet-bgr-meaning.md). No code reads color_format. none and unit_float return float32, not input.dtype.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: vectors/pre.normalize.yaml
status: {spec: stable, validate: partial, forward: partial}
---

# Normalization

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `normalization` | string or object | no | See [Normalization modes](normalization.md). The default is `imagenet_bgr` (the RTMPose convention). |
| `normalization_by_precision` | object | no | This optional override maps a precision (`fp32`, `fp16` or `int8`) to a named mode. The values must be mode strings only. They must not be a `custom` object. Declare a `custom` normalization at the top-level `normalization`. |

`normalization` and `normalization_by_precision` are fields of [`input`](../common/input.md#fields).

## Behaviour

`input.normalization` declares how the host transforms resized pixels before `session.run()`. Use a closed enum string, or a `custom` object.

| Mode | Host behavior | Typical use |
|------|---------------|-------------|
| `none` | Pass pixel values (0–255) unchanged, cast to `input.dtype`. Channel order from `input.color_format`. | Graphs that normalize internally, for example YOLOX |
| `unit_float` | `pixel / 255.0` per channel → `[0, 1]`. Channel order from `input.color_format`. | YOLO26, which uses Ultralytics-style float input |
| `imagenet_bgr` | `(pixel - mean) / std` on 0–255 pixels in **BGR** channel order: B uses mean `103.53` / std `57.375`, G `116.28` / `57.12`, R `123.675` / `58.395`. (Legacy sidecars use a different meaning; see [Version-aware compatibility](#legacy-behaviour).) | RTMDet |
| `imagenet_rgb` | `(pixel - mean) / std` on 0–255 pixels in **RGB** channel order: R uses mean `123.675` / std `58.395`, G `116.28` / `57.12`, B `103.53` / `57.375`. | RTMW, RF-DETR |
| `custom` | `(pixel * scale - mean) / std` on 0–255 channel values | Rare exports that match no named mode |

Both `imagenet_*` modes use the same per-colour ImageNet statistics (`0.485/0.456/0.406` and `0.229/0.224/0.225` × 255). They differ only in the channel order of the tensor.

The host applies normalization after the resize. For `affine_person_crop`, it applies normalization after the affine warp. For `method: none`, it applies normalization directly on the source image.

`none` and `unit_float` treat every channel in the same way, so `input.color_format` must be present with them.

`custom` declares its own channel order in `color_format`. If `custom.color_format` is omitted, the mode inherits `input.color_format`. If that field is also omitted, the mode falls back to `rgb`.

**Named mode (preferred):**

```yaml
input:
  color_format: rgb
  normalization: unit_float
```

**Custom mode:**

```yaml
input:
  normalization:
    mode: custom
    color_format: rgb            # optional; inherits input.color_format, else rgb — order of mean/std
    scale: 0.00392156862745098   # optional; default 1.0
    mean: [0.0, 0.0, 0.0]
    std: [1.0, 1.0, 1.0]
```

**Per-precision overrides:**

```yaml
# For an int8 artifact whose graph takes raw uint8 pixels. The Ultralytics exporter emits this
# override only when an int8 artifact's input dtype is uint8/int8; the current YOLO26 int8
# exports take float32 input, so they need no override.
input:
  dtype: {fp32: float32, fp16: float32, int8: uint8}
  color_format: rgb
  normalization: unit_float
  normalization_by_precision:
    int8: none
```

The resolution order for a selected precision is: `normalization_by_precision[precision]` → top-level `normalization` → default `imagenet_bgr`.

The values of `normalization_by_precision` must be named mode strings only. A `custom` normalization must not be a per-precision override. Declare it at the top-level `normalization` instead.

> ⚠️ The `imagenet_bgr` default is the RTMPose convention. Detector models must declare their normalization explicitly. For most detectors, the default gives incorrect normalization.

### Mode validation

- If `normalization` is omitted, its value is `imagenet_bgr`.
- A string value must be one of `none`, `unit_float`, `imagenet_bgr`, `imagenet_rgb`.
- The object form must have `mode: custom`. If `mean` or `std` is present, it must be a sequence of length 3. If `scale` is present, it must be a positive number. If `color_format` is present, it must be `rgb` or `bgr`.
- The keys of `normalization_by_precision` must be a subset of `fp32`, `fp16`, `int8`. The values must be valid mode strings.
- If any declared precision resolves to `none` or `unit_float`, `input.color_format` must be present. When the field is present, it must agree with `imagenet_rgb` (`rgb`), `imagenet_bgr` (`bgr`) and `custom.color_format`.

## Validation rules

- [ ] `V-pre.normalize-1` If `input.normalization` is present, it must be a valid mode: `none`, `unit_float`, `imagenet_bgr`, `imagenet_rgb` or a `custom` object. A `custom` object must have `mode: custom`. If `mean` or `std` is present, it must have length 3. If `scale` is present, it must be positive. If `color_format` is present, it must be `rgb` or `bgr`.
- [ ] `V-pre.normalize-2` The keys of `normalization_by_precision` must be a subset of `fp32`, `fp16` and `int8`. Its values must be valid mode strings. A value must not be a `custom` object.

See also [Input](../common/input.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `normalization: imagenet_bgr` | The RGB-ordered tuple — mean `(123.675, 116.28, 103.53)`, std `(58.395, 57.12, 57.375)` — applied in order to the B, G, R channels of the BGR frame (B uses `123.675`). This is the rtmlib convention used by the in-repo RTMPose and RTMW sidecars. | BGR-ordered statistics (B uses `103.53`); see [Normalization modes](normalization.md). To keep the legacy behaviour in a `vNEXT` sidecar, declare `normalization: {mode: custom, color_format: bgr, mean: [123.675, 116.28, 103.53], std: [58.395, 57.12, 57.375]}`. |

See also [Input](../common/input.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance
