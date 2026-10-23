---
id: common.input
title: Input
kind: common
---

# Input

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | ONNX input tensor name. |
| `dtype` | object | yes | Map of precision → ONNX graph input element type, e.g. `{fp32: float32, fp16: float16, int8: uint8}`. When all variants share one type, every entry is that type (e.g. `{fp32: float32, fp16: float32, int8: float32}`). Keys are a subset of `fp32`/`fp16`/`int8` covering the precisions declared in `batch_artifacts`. |
| `layout` | enum | no | `NCHW` (default) or `NHWC`. |
| `color_format` | enum | conditional | `rgb` or `bgr` — the channel order of the tensor the model consumes. **Required** when the normalization resolved for any declared precision is `none` or `unit_float` (those modes are channel-agnostic). Optional otherwise; when authored it must agree with `imagenet_rgb`/`imagenet_bgr` or with `custom.color_format`. |
| `resize` | object | no | Resize config (see below); omitted only when the model consumes the source image unchanged (same effect as `method: none`). `target_size` is per-size (`sizes.<size>.input.resize.target_size`); other fields are shared. |

`normalization` and `normalization_by_precision` are defined in [Normalization](../pre/normalization.md#fields).

`shape` is **not** a top-level field — the input image shape is declared per size as `sizes.<size>.input.shape` (see [Sizes](sizes-and-artifacts.md#sizes)). Its batch axis is always `-1`: the concrete native batch size lives in the `batch_artifacts` keys, never in the shape. The channels and spatial dims are concrete, except that the spatial dims are `-1` when [`input.resize.supports_dynamic_size`](#inputresize) is `true`.

`color_format` is a single top-level value covering every precision. A family whose precisions would need different channel orders cannot be described and must be split.

`input` is required for `object_detector` and `pose_estimator` sidecars. This spec models **single-input** models only — `input` describes exactly one input tensor; multi-input models are out of scope.

### `input.resize`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method` | enum | yes | `letterbox` (aspect-preserving resize + pad), `stretch` (independent x/y resize, no pad), `fit` (full-frame affine fit with centred fractional padding), `affine_person_crop` (top-down pose), or `none` (pass the source image unchanged — no resize). |
| `target_size` | array[2] | conditional | `[height, width]` the input is resized to. Declared in `sizes.<size>.input.resize.target_size`. Required when `method` is `letterbox`, `stretch`, `fit`, or `affine_person_crop`, unless `supports_dynamic_size: true`. Omitted when `method: none`. |
| `supports_dynamic_size` | bool | no | Model accepts any input spatial size; `target_size` is omitted. Default `false`. |
| `pad_value` | int, float, or array[3] | `fit`: yes | `letterbox` and `fit` only. Raw pixel value (before normalization). An array is per channel, in `input.color_format` order. Optional for `letterbox`, with default `114`; required for `fit`. |

Method-specific fields: [`pad_position`, `rounding`, `preserve_aspect_ratio`](../pre/resize-letterbox.md#fields), [`interpolation`](../pre/interpolation.md#fields), [`crop_policy`](../pre/resize-affine-person-crop.md#fields).

When `supports_dynamic_size: true`, the model accepts any input spatial size: `target_size` is omitted and the size's `input.shape` spatial dims are `-1`. This applies to `letterbox`, `stretch`, and `fit` (the host resizes to the runtime-accepted size) and to `affine_person_crop` (the host warps the crop to the runtime-accepted size). When it is not set and `method` is `letterbox`, `stretch`, `fit`, or `affine_person_crop`, `target_size` is required.

Each `method` has its own section: [`letterbox`](../pre/resize-letterbox.md), [`stretch`](../pre/resize-stretch.md), [`fit`](../pre/resize-fit.md), [`affine_person_crop`](../pre/resize-affine-person-crop.md), [`none`](../pre/resize-none.md).

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.input-1` `input.resize.target_size` (when present) is a length-2 `[height, width]` array.
- [ ] `V-common.input-2` `input.dtype` is present; its keys are a subset of `fp32`/`fp16`/`int8` covering the precisions declared in `batch_artifacts`, and its values are `float32`, `float16`, `uint8`, or `int8`. `input.layout` (when present) is `NCHW` or `NHWC`.
- [ ] `V-common.input-3` `input.resize.method` is `letterbox`, `stretch`, `fit`, `affine_person_crop`, or `none` (`stretch` and `fit` **(vNEXT)**), and `input.resize.interpolation` is `linear`, `area`, `cubic`, or `nearest`.
- [ ] `V-common.input-4` `pad_value` is present only when `method` is `letterbox` or `fit`; `pad_position`, `rounding`, and `preserve_aspect_ratio` only when `method: letterbox`; `crop_policy` only when `method: affine_person_crop`.
- [ ] `V-common.input-5` `pad_value` and `crop_policy.pad_value` (when present) are a number or a length-3 array of numbers.
- [ ] `V-common.input-6` **(vNEXT)** `input.color_format` is present when any declared precision resolves to `none` or `unit_float`; when present it is `rgb`/`bgr` and agrees with `imagenet_*` and `custom.color_format`.

See also [Identity](identity.md#validation-rules), [Sizes and artifacts](sizes-and-artifacts.md#validation-rules), [Normalization](../pre/normalization.md#validation-rules) and [Affine person crop](../pre/resize-affine-person-crop.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `color_format` absent with `none`/`unit_float` | Existing host channel order. | Required. |

## Implementer guidance

## Authoring guidance
