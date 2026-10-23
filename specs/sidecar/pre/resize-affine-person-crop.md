---
id: pre.resize.affine_person_crop
title: Affine person crop
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [input.resize.method=affine_person_crop]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CropPolicySpec  # partial. No crop_policy.pad_value field. SidecarModel._check_pose_requires_affine_crop checks V-pre.resize.affine_person_crop-2.
  forward: skellytracker/core/detectors/processing/affine_crop.py::top_down_affine  # partial. Always uses cv2.INTER_LINEAR and no pad_value. preprocess_image raises when maintain_aspect_ratio is false.
  inverse: skellytracker/core/detectors/processing/simcc_decode.py::decode_simcc  # partial. Applies the inverse to SimCC keypoints only. get_warp_matrix(inv=True) has no caller.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
vectors: vectors/pre.resize.affine_person_crop.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: partial}
---

# Affine person crop

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crop_policy` | object | no | `affine_person_crop` only; see below. |

The top-down pose convention: a person bounding box is warped to `target_size` by an affine transform (center + scale) rather than padding a full frame. Used by top-down models such as RTMW and RTMW3D. `crop_policy` controls how the source bounding box is expanded before the warp:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input.resize.crop_policy.expand_ratio` | float | no | BBox expansion factor before the affine warp; default `1.25`. |
| `input.resize.crop_policy.maintain_aspect_ratio` | bool | no | Default `true`. When `true`, the expanded box is enlarged along its shorter side to the target aspect ratio `T_w / T_h`; when `false`, it is warped directly, distorting aspect. |
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | no | Constant border value for pixels outside the source image; default `0`. An array is per channel, in `input.color_format` order. |

`target_size`, `supports_dynamic_size` and `interpolation` are defined in [`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md). `[T_h, T_w]` is named in [Letterbox resize](resize-letterbox.md#behaviour).

## Behaviour

Normative warp (rotation is always `0`; rotated crops are out of scope):

```text
center   = bbox center
(w, h)   = bbox size * expand_ratio
if maintain_aspect_ratio:
    if w > h * (T_w / T_h): h = w * (T_h / T_w)
    else:                   w = h * (T_w / T_h)
M        = affine map taking the (w, h) box around center onto [0, T_w] x [0, T_h]
dst      = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=pad_value)
```

This matches mmpose `GetBBoxCenterScale(padding=1.25)` + `TopdownAffine`.

### Inverse

Applied as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `affine_person_crop` | Apply the inverse of the affine warp `M`. |

## Validation rules

- [ ] `V-pre.resize.affine_person_crop-1` `input.resize.crop_policy.expand_ratio` (when present) is a positive float, and `crop_policy.maintain_aspect_ratio` (when present) is a boolean.
- [ ] `V-pre.resize.affine_person_crop-2` A sidecar with `pose.requires_object_detector: true` declares `input.resize.method: affine_person_crop`.

See also [Input](../common/input.md#validation-rules), [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules) and [Pose schema](../post/pose-schema.md#validation-rules).

## Implementer guidance

## Authoring guidance
