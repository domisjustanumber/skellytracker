---
id: pre.resize.fit
title: Fit resize
kind: preprocessor
since: vNEXT
changed_in: []
selectors: [input.resize.method=fit]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields  # partial. pad_value is not required (V-pre.resize.fit-1). The model accepts fit in a sidecar older than vNEXT.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::fit_preprocess
  inverse: missing  # fit_preprocess returns scale, left and top. No code applies (x - left) / s.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: vectors/pre.resize.fit.yaml
status: {spec: stable, validate: partial, forward: implemented, inverse: missing}
---

# Fit resize

## Fields

`target_size`, `pad_value`, `supports_dynamic_size` and `interpolation` are defined in [`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md).

## Behaviour

The whole source image is scaled by a single factor, centred on the `target_size` canvas `[T_h, T_w]` at fractional offsets, and warped with one affine transform. Unlike `letterbox`, neither the scaled size nor the offsets are rounded:

```text
s    = min(T_w / src_w, T_h / src_h)
left = (T_w - src_w * s) / 2          # fractional; not rounded
top  = (T_h - src_h * s) / 2          # fractional; not rounded
M    = [[s, 0, left],
        [0, s, top ]]
dst  = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=pad_value)
```

`pad_value` is required. `pad_position`, `rounding`, `preserve_aspect_ratio`, and `crop_policy` are invalid with `fit`. This matches mmpose `BottomupResize` (RTMO). A `letterbox` is not equivalent at any scale other than `1`: it rounds the resized size, and `resize` + pad gives different pixels from `warpAffine` even when the resized size is integral.

### Inverse

Applied as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `fit` | `x_src = (x - left) / s`, `y_src = (y - top) / s` — the exact inverse of `M`, using the unrounded `s`, `left` and `top` from the `fit` algorithm. |

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-pre.resize.fit-1` **(vNEXT)** A `fit` resize declares `pad_value`.

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance
