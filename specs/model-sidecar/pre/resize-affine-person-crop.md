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
| `crop_policy` | object | no | This field applies to `affine_person_crop` only. See below. |

This resize is the top-down pose convention. The host warps a person bounding box to `target_size` with an affine transform (center + scale). The host does not pad a full frame. Top-down models such as RTMW and RTMW3D use this resize. `crop_policy` controls how the host expands the source bounding box before the warp:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input.resize.crop_policy.expand_ratio` | float | no | This factor expands the bounding box before the affine warp. The default is `1.25`. |
| `input.resize.crop_policy.maintain_aspect_ratio` | bool | no | The default is `true`. When the value is `true`, the host enlarges the expanded box along its shorter side to the target aspect ratio `T_w / T_h`. When the value is `false`, the host warps the expanded box directly. This distorts the aspect ratio. |
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | no | This is the constant border value for pixels outside the source image. The default is `0`. An array gives one value for each channel, in the channel order of `input.color_format`. |

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `supports_dynamic_size` and `interpolation`. [Letterbox resize](resize-letterbox.md#behaviour) names `[T_h, T_w]`.

## Behaviour

The rotation of the warp is always `0`. Rotated crops are out of scope. The normative warp is:

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

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `affine_person_crop` | Apply the inverse of the affine warp `M`. |

## Validation rules

- [ ] `V-pre.resize.affine_person_crop-1` If `input.resize.crop_policy.expand_ratio` is present, it must be a positive float. If `crop_policy.maintain_aspect_ratio` is present, it must be a boolean.
- [ ] `V-pre.resize.affine_person_crop-2` If a sidecar has `pose.requires_object_detector: true`, it must declare `input.resize.method: affine_person_crop`.

See also [Input](../common/input.md#validation-rules), [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules) and [Pose schema](../post/pose-schema.md#validation-rules).

## Implementer guidance

- Compare a host with mmpose at `flip_test=False`. All five RTMW configs set `test_cfg=dict(flip_test=True)`. The sidecar has no field for the flip test, and the exported graph is one forward pass. The effect of the flip test is not measured. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-*.py`, line 117 in the 256x192 configs and line 119 in the 384x288 configs, 491c17b)
- A host script that followed only the spec text matched mmpose `inference_topdown` (`flip_test=False`, same boxes). The spec text was `affine_person_crop`, `imagenet_rgb`, SimCC argmax and the inverse affine. The mean difference was 0.0 to 0.4 px (max 2.4 px) on five confident crops. It was 2.9 px on one crop with mean score 0.10, where a flat SimCC peak changed bin. The model was an RTMPose hand model, not RTMW. The script is not in the repo. (the untracked hand models plan of OpenMMLab-Exporter (secondary); the only evidence)
- No exporter implements the crop or its inverse yet. The module `rtmw/preprocess.py` only declares the `affine_person_crop` values. The consumer of the sidecar runs the preprocessing. (OpenMMLab-Exporter `rtmw/preprocess.py:5-16`, eed3361)

## Authoring guidance

- The mmpose `val_pipeline` has `GetBBoxCenterScale` (no `padding` argument) and `TopdownAffine(input_size=codec['input_size'])`. This maps to `method: affine_person_crop`, `interpolation: linear` and `crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}`. The exporter omits `pad_value`, so the default 0 applies. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:157-161`, 491c17b; OpenMMLab-Exporter `rtmw/preprocess.py:26-35`, eed3361)
- The RTMW `val_pipeline` does not write the value 1.25. Only the `face_pipeline` writes `padding=1.25`. The mmpose v1.3.2 default is not in the repo. Record the source of the value before you write it. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:159, 389`, 491c17b)
- Do not describe a rotated ROI with `affine_person_crop`. The spec fixes the rotation at 0, and the changelog lists rotated crops and a border mode as considered and not added ([Considered and deliberately not added](../changelog.md#considered-and-deliberately-not-added)). The [model intake](../templates/model-intake.md#verdicts) calls a rotated crop a `gap`. An ROI that does not come from a detector box is also a `gap`.
- Qualcomm-Exporter wrote `affine_person_crop` with `expand_ratio: 1.0` for the MediaPipe face landmark model (192x192) and the MediaPipe hand landmark model (256x256). It put the detector-to-ROI constants into pipeline manifests: face `dscale` 1.1, hand `dxy` 0.5 and `dscale` 2.5, and person `dscale` 1.5 with rotation from keypoints 2 and 3 plus pi/2. Its README says that `affine_person_crop` cannot express the rotation-aware ROI of MediaPipe. (Qualcomm-Exporter `qai_sidecar.py:17-35, 270-277, 343-355` and `qai_catalog.py:80-94`, c7b9132; Qualcomm-Exporter `qai_sidecar.py:51-59, 316-323, 389-401` and `qai_catalog.py:113-127`, a095041; Qualcomm-Exporter `README.md:129-132`, c7b9132)
