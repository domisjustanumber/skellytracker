---
id: common.input
title: Input
kind: common
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::InputSpec  # partial. No color_format field (V-common.input-6) and no crop_policy.pad_value. Nothing checks that dtype covers the declared precisions. pad_value is not required for fit.
  load: skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image  # partial. Ignores input.dtype. Raises for method none and for letterbox with preserve_aspect_ratio false.
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_image_preprocessing.py
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# Input

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | The name of the ONNX input tensor. |
| `dtype` | object | yes | A map of precision → ONNX graph input element type, for example `{fp32: float32, fp16: float16, int8: uint8}`. When all variants share one type, every entry is that type, for example `{fp32: float32, fp16: float32, int8: float32}`. The keys are a subset of `fp32`/`fp16`/`int8`. They cover the precisions that `batch_artifacts` declares. |
| `layout` | enum | no | `NCHW` or `NHWC`. The first value is the default. |
| `color_format` | enum | conditional | `rgb` or `bgr`. This is the channel order of the tensor that the model consumes. It is **required** when the normalization of any declared precision resolves to `none` or `unit_float`. Those modes treat every channel in the same way. Otherwise, the field is optional. When the field is present, it must agree with `imagenet_rgb`/`imagenet_bgr` or with `custom.color_format`. |
| `resize` | object | no | The resize configuration (see below). A sidecar can omit this field only when the model consumes the source image unchanged. This has the same effect as `method: none`. `target_size` is set for each size (`sizes.<size>.input.resize.target_size`). The other fields are shared. |

[Normalization](../pre/normalization.md#fields) defines `normalization` and `normalization_by_precision`.

`shape` is **not** a top-level field. A sidecar declares the input image shape for each size as `sizes.<size>.input.shape` (see [Sizes](sizes-and-artifacts.md#sizes)). The batch axis of the shape is always `-1`. The concrete native batch size is in the keys of `batch_artifacts`. It is never in the shape. The channels and the spatial dimensions are concrete. The exception is when [`input.resize.supports_dynamic_size`](#inputresize) is `true`. Then the spatial dimensions are `-1`.

`color_format` is a single top-level value. It covers every precision. A sidecar cannot describe a family whose precisions need different channel orders. The author must split that family.

`input` is required for `object_detector` and `pose_estimator` sidecars. This spec covers **single-input** models only. `input` describes exactly one input tensor. Multi-input models are out of scope.

### `input.resize`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method` | enum | yes | The value is one of the following. `letterbox` is a resize that keeps the aspect ratio, plus a pad. `stretch` is an independent x/y resize with no pad. `fit` is a full-frame affine fit that centres the image with fractional padding. `affine_person_crop` is for top-down pose. `none` passes the source image unchanged, with no resize. |
| `target_size` | array[2] | conditional | `[height, width]` that the host resizes the input to. A sidecar declares it in `sizes.<size>.input.resize.target_size`. It is required when `method` is `letterbox`, `stretch`, `fit` or `affine_person_crop`, unless `supports_dynamic_size: true`. A sidecar omits it when `method: none`. |
| `supports_dynamic_size` | bool | no | The model accepts any input spatial size. The sidecar omits `target_size`. The default is `false`. |
| `pad_value` | int, float, or array[3] | `fit`: yes | This field applies to `letterbox` and `fit` only. It is a raw pixel value (before normalization). An array gives one value for each channel, in the order of `input.color_format`. The field is optional for `letterbox`, with the default `114`. It is required for `fit`. |

Method-specific fields: [`pad_position`, `rounding`, `preserve_aspect_ratio`](../pre/resize-letterbox.md#fields), [`interpolation`](../pre/interpolation.md#fields), [`crop_policy`](../pre/resize-affine-person-crop.md#fields).

When `supports_dynamic_size: true`, the model accepts any input spatial size. The sidecar omits `target_size`. The spatial dimensions of the `input.shape` of the size are `-1`. This applies to `letterbox`, `stretch` and `fit`. For these methods, the host resizes to the runtime-accepted size. It also applies to `affine_person_crop`. For this method, the host warps the crop to the runtime-accepted size. If the flag is not set and `method` is `letterbox`, `stretch`, `fit` or `affine_person_crop`, `target_size` is required.

Each `method` has its own section: [`letterbox`](../pre/resize-letterbox.md), [`stretch`](../pre/resize-stretch.md), [`fit`](../pre/resize-fit.md), [`affine_person_crop`](../pre/resize-affine-person-crop.md), [`none`](../pre/resize-none.md).

## Validation rules

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.input-1` If `input.resize.target_size` is present, it must be an array `[height, width]` of length 2.
- [ ] `V-common.input-2` `input.dtype` must be present. Its keys must be a subset of `fp32`/`fp16`/`int8`. The keys must cover the precisions that `batch_artifacts` declares. Its values must be `float32`, `float16`, `uint8` or `int8`. If `input.layout` is present, it must be `NCHW` or `NHWC`.
- [ ] `V-common.input-3` `input.resize.method` must be `letterbox`, `stretch`, `fit`, `affine_person_crop` or `none`. The values `stretch` and `fit` are marked **(vNEXT)**. `input.resize.interpolation` must be `linear`, `area`, `cubic` or `nearest`.
- [ ] `V-common.input-4` `pad_value` must not be present unless `method` is `letterbox` or `fit`. `pad_position`, `rounding` and `preserve_aspect_ratio` must not be present unless `method: letterbox`. `crop_policy` must not be present unless `method: affine_person_crop`.
- [ ] `V-common.input-5` If `pad_value` or `crop_policy.pad_value` is present, it must be a number or an array of numbers with length 3.
- [ ] `V-common.input-6` **(vNEXT)** If any declared precision resolves to `none` or `unit_float`, `input.color_format` must be present. When the field is present, it must be `rgb`/`bgr`. It must also agree with `imagenet_*` and `custom.color_format`.

See also [Identity](identity.md#validation-rules), [Sizes and artifacts](sizes-and-artifacts.md#validation-rules), [Normalization](../pre/normalization.md#validation-rules) and [Affine person crop](../pre/resize-affine-person-crop.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `color_format` absent with `none`/`unit_float` | Existing host channel order. | Required. |

## Implementer guidance

## Authoring guidance
