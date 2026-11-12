---
id: pre.resize.affine_crop
title: Affine crop
kind: preprocessor
selectors: [input.resize.method=affine_crop]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CropPolicySpec  # partial. No crop_policy.pad_value field. SidecarModel._check_pose_requires_affine_crop checks V-pre.resize.affine_crop-2.
  forward: skellytracker/core/detectors/processing/affine_crop.py::top_down_affine  # partial. Always uses cv2.INTER_LINEAR and no pad_value. preprocess_image raises when maintain_aspect_ratio is false. The arithmetic of `M` is not met: the box keeps the dtype of the caller, and the second warp point is above the centre (the rtmlib form). No rotation: `top_down_affine` takes a box only, and `get_warp_matrix` turns the second point above the centre.
  inverse: skellytracker/core/detectors/processing/simcc_decode.py::decode_simcc  # partial. Applies the inverse to SimCC keypoints only. get_warp_matrix(inv=True) has no caller.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
vectors: vectors/pre.resize.affine_crop.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: partial}
---

# Affine crop

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crop_policy` | object | no | This field applies to `affine_crop` only. See below. |

This resize is the top-down crop. The host warps a region of interest (ROI) of the source image to `target_size` with an affine transform. The ROI has a centre, a size and a rotation. A box is an ROI with rotation 0. The host does not pad a full frame. Top-down models such as RTMW and RTMW3D use this resize. `crop_policy` controls how the host grows the ROI along its own axes before the warp:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input.resize.crop_policy.expand_ratio` | float | no | This factor multiplies the width and the height of the ROI before the affine warp. The default is `1.25`. |
| `input.resize.crop_policy.maintain_aspect_ratio` | bool | no | The default is `true`. When the value is `true`, the host enlarges the expanded ROI along its shorter side to the target aspect ratio `T_w / T_h`. When the value is `false`, the host warps the expanded ROI directly. This distorts the aspect ratio. |
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | no | This is the constant border value for pixels outside the source image. The default is `0`. An array gives one value for each channel, in the channel order of `input.color_format`. A scalar `s` gives the same value to each channel: it means `[s, s, s]` ([ADR-BJF9](../../../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)). |

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size` and `interpolation`. [Letterbox resize](resize-letterbox.md#behaviour) names `[T_h, T_w]`.

## Behaviour

The host gives the crop one ROI `(c_x, c_y, w, h, rotation)` for each instance:

- `c_x` and `c_y` are the centre, and `w` and `h` are the size, in source-image pixels. The
  positions follow [Unprojection](../post/unprojection.md#behaviour). The crop uses the values as
  given. It adds no `0.5` offset and removes none.
- `rotation` is in radians. A positive rotation turns the ROI clockwise in the image, because the
  image y axis points down. The ROI x axis is `(cos(rotation), sin(rotation))` and the ROI y axis is
  `(-sin(rotation), cos(rotation))`, in image pixels. `w` is the size along the ROI x axis and `h`
  is the size along the ROI y axis.
- A box `bbox_xyxy = [x1, y1, x2, y2]` (left, top, right, bottom, in source-image pixels) gives the
  ROI with rotation 0 of the first block of the steps.

The normative steps are:

```text
# A box gives the ROI. float32: each value is float32, and the host rounds the result of each
# operation to float32.
x1, y1, x2, y2 = f32(bbox_xyxy)
roi = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, x2 - x1, y2 - y1, 0)

# The crop size, float32.
c_x, c_y, w, h = f32(roi.c_x), f32(roi.c_y), f32(roi.w), f32(roi.h)
e   = f32(expand_ratio)
w   = w * e                          # along the ROI x axis
h   = h * e                          # along the ROI y axis
if maintain_aspect_ratio:
    a = f32(T_w / T_h)
    if w > h * a: h = w / a
    else:         w = h * a

# Three point pairs: P in source pixels, Q in model-input pixels. Each P and Q is float32.
# cs, sn and each expression in f32(...) are float64. f32(...) rounds its result once.
cs = cos(f64(roi.rotation))
sn = sin(f64(roi.rotation))
P0 = (c_x, c_y)                                                 Q0 = (T_w / 2, T_h / 2)
P1 = (f32(c_x - (w * 0.5) * cs), f32(c_y - (w * 0.5) * sn))     Q1 = (0, T_h / 2)
if maintain_aspect_ratio:
    # float32
    P2 = (P1.x - (P0.y - P1.y), P1.y + (P0.x - P1.x))           Q2 = (0, T_h / 2 + T_w / 2)
else:
    P2 = (f32(c_x + (h * 0.5) * sn), f32(c_y - (h * 0.5) * cs)) Q2 = (T_w / 2, 0)

M        = the affine map that takes P0, P1, P2 onto Q0, Q1, Q2, solved in float64
pad      = crop_policy.pad_value
border   = [pad] * 3 if pad is a scalar else pad
dst      = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=border)
```

- `f32(v)` rounds one value to float32 (IEEE 754 binary32, round to nearest, ties to even).
  `T_w / T_h` is a float64 division of the two integers, then one rounding. `w * 0.5` and
  `h * 0.5` are float32 and exact.
- `w > h * a` is a strict comparison of two float32 values. When `w` equals `h * a`, `h` does not
  change.
- `P1` is half the crop width from the centre, against the ROI x axis. With
  `maintain_aspect_ratio: true`, `P2` turns `P0 - P1` by 90 degrees around `P1`, so `M` uses `c`
  and `w` only, not `h`. The branch `h = w / a` and the strict `>` set only `h`: the crop height
  that mmpose returns as `input_scale`. The y scale of `M` comes from the float32 points. It can
  differ from the x scale and from `T_h / h`. Do not make `M` from `T_w / w` and `T_h / h`.
- With `maintain_aspect_ratio: false`, `P2` is half the crop height from the centre, against the
  ROI y axis.
- For rotation 0, `cs` is 1 and `sn` is 0. Then `P1 = (c_x - w * 0.5, c_y)`, and `P2` is
  `(P1.x, P1.y + (P0.x - P1.x))` or `(c_x, c_y - h * 0.5)`. The float64 expression, rounded once,
  equals the float32 operation, because double rounding from binary64 to binary32 is exact for `+`
  and `-`.
- `cos` and `sin` are float64 functions. Two math libraries can give a different last bit. A
  rotation that is not 0 can thus change a point by one float32 step.
- The crop uses the rotation as given. It does not wrap the rotation into `[-π, π)`.
- Each ROI value must be finite. After the aspect step, `w > 0` and `h > 0` must be true. The host
  must refuse an ROI that does not meet these conditions. This section gives no crop for such an
  ROI. NaN and inf are not finite.
- `cv2.getAffineTransform(src, dst)` with the float32 arrays `src = [P0, P1, P2]` and
  `dst = [Q0, Q1, Q2]` gives `M`.

`warpAffine` is `cv2.warpAffine`. Its pixel centres are at integer coordinates
([Pixel centres](interpolation.md#pixel-centres)). For a float32 box and
`maintain_aspect_ratio: true`, `M` is the matrix of mmpose `GetBBoxCenterScale(padding=expand_ratio)`
+ `TopdownAffine`. For an ROI with rotation `r`, the points have the form of mmpose
`get_warp_matrix` with `rot` = `r` in degrees (`TopdownAffine` with `bbox_rotation`).

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `affine_crop` | Apply the inverse of the affine warp `M`. |

The positions are pixel indices of `cv2.warpAffine`. The inverse adds no `0.5` offset ([Pixel centres](interpolation.md#pixel-centres)).

## Validation rules

- [ ] `V-pre.resize.affine_crop-1` If `input.resize.crop_policy.expand_ratio` is present, it must be a positive float. If `crop_policy.maintain_aspect_ratio` is present, it must be a boolean.
- [ ] `V-pre.resize.affine_crop-2` If `keypoint.estimator_type` is `top_down_single_person` or `top_down_multi_person`, the sidecar must declare `input.resize.method: affine_crop`.
- [ ] `V-pre.resize.affine_crop-3` Each size must declare `input.resize.target_size`. An `affine_crop` resize must not declare `pad_value`, `pad_position` or `rounding` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Input](../common/input.md#validation-rules), [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules) and [Keypoint schema](../post/keypoint/schema.md#validation-rules).

## Implementer guidance

- Compare a host with mmpose at `flip_test=False`. All five RTMW configs set `test_cfg=dict(flip_test=True)`. The sidecar has no field for the flip test, and the exported graph is one forward pass. The effect of the flip test is not measured. (OpenMMLab-Exporter `rtmw-*.py` in [`mmdeploy-convert/model_cfgs/`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs), line 117 in the 256x192 configs and line 119 in the 384x288 configs)
- A host script that followed only the spec text matched mmpose `inference_topdown` (`flip_test=False`, same boxes). The spec text was `affine_person_crop`, `imagenet_rgb`, SimCC argmax and the inverse affine. The mean difference was 0.0 to 0.4 px (max 2.4 px) on five confident crops. It was 2.9 px on one crop with mean score 0.10, where a flat SimCC peak changed bin. The model was an RTMPose hand model, not RTMW. The script is not in the repo. (the untracked hand models plan of OpenMMLab-Exporter (secondary))
- A committed parity script compared the RTMW sidecar path with mmpose `inference_topdown` at `flip_test=False`. It ran 49 persons on 10 images, in the 5 sizes, in fp32 and fp16. On the upstream crop, the sidecar normalizer gave the upstream tensor with a difference of 0 (gate G1b). The final keypoints and scores passed gate G5 in each size and precision. On the host crop, the tensor differed by 4 to 5 grey levels (0.070 at 256x192 and 0.086 at 384x288). The host `M` equals the upstream `M` bit for bit. The cause is `cv2.warpAffine` of two OpenCV builds: 5.0.0 on the host and 4.5.4 in the container. (OpenMMLab-Exporter [`decisions/scripts/rtmw_parity.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/scripts/rtmw_parity.py) at `3e326df00726df8110773ed62cf38d02948a71a5`, with mmpose 1.3.2 and onnxruntime-gpu 1.31.1; the parity result in the intake of the bundle `model-rtmw-wholebody133@openmmlab-exporter@v2` (secondary))
- The OpenMMLab-Exporter host code implements the crop and its Inverse. `affine_crop_geometry` follows the float32 steps of `M` of Behaviour. `affine_person_crop` warps the image with that `M`. `unproject_affine` maps the keypoints back with `AffineCropMeta.inverse_matrix`. That inverse is the float64 inverse of the float32 `M`, with the operations of `cv2.invertAffineTransform` in the same order. The module `rtmw/preprocess.py` only declares the `affine_person_crop` values. The consumer of the sidecar runs the preprocessing. (OpenMMLab-Exporter [`onnx_runtime/preprocess.py:472-535`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/onnx_runtime/preprocess.py#L472-L535), [`onnx_runtime/preprocess.py:560-596`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/onnx_runtime/preprocess.py#L560-L596), [`onnx_runtime/preprocess.py:624-638`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/onnx_runtime/preprocess.py#L624-L638) and [`onnx_runtime/preprocess.py:431-445`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/onnx_runtime/preprocess.py#L431-L445); [OpenMMLab-Exporter ADR-HJF1](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/HJF1-host-adopts-landed-spec-text.md) item 7; OpenMMLab-Exporter [`rtmw/preprocess.py:5-16`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/preprocess.py#L5-L16))
- That host passes the 14 forward cases, the 9 Inverse cases and the warp case `scalar-pad-fills-each-channel` of the vector file at skellytracker commit `0631470142fe2b88848091200488a14465047581`. Before OpenMMLab-Exporter ADR-HJF1, the host used the exact-math `M` of the text before [ADR-3S5G](../decisions/entries/3S5G-affine-crop-matrix.md). Then it passed only 7 of the 14 forward cases. ([OpenMMLab-Exporter ADR-HJF1](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/HJF1-host-adopts-landed-spec-text.md), Evidence; the `vector-runs.yaml` of the bundle `model-rtmw-wholebody133@openmmlab-exporter@v2`; part 7 of [`proposal.md`](../proposals/affine-crop-matrix/proposal.md#7-exporter-impact))
- OpenMMLab-Exporter changed this host to agree with the reference module `reference/pre_resize_affine_person_crop.py`. The host and the module give the same `M`, centre, size and inverse on 20000 random boxes. That module comes from a proposal of the same exporter. Thus the host and the module count as one implementation in `verified_against` ([Independence](../model-addition-workflow/sidecar-files.md#independence)). ([OpenMMLab-Exporter ADR-HJF1](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/decisions/entries/HJF1-host-adopts-landed-spec-text.md), Reason and Evidence; the header of `reference/pre_resize_affine_person_crop.py`)
- For a float32 box and `maintain_aspect_ratio: true`, the float32 steps of Behaviour give the `M` of mmpose v1.3.2 bit for bit with `cv2.getAffineTransform`. Another float64 solver can differ in the last bits. On 6370 persons (6352 COCO val2017 persons and 18 synthetic boxes), the exact-math `M` differed from the mmpose `M` by more than 1e-6 for 6226 persons at 256x192 and for 6245 persons at 384x288. The maximum was 2.4e-3 and 3.6e-3. On OpenCV 5.0.0, 5992 crops (256x192) and 6047 crops (384x288) of the 6370 differed, by 1 grey level at most. (OpenMMLab-Exporter [`decisions/scripts/affine_crop_matrix_check.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0d07c982fb6915fee6fa0b8ccac35873c77c4db2/decisions/scripts/affine_crop_matrix_check.py) at `0d07c982fb6915fee6fa0b8ccac35873c77c4db2`, gates G2 and G3; [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md); mmpose [`mmpose/structures/bbox/transforms.py:66-67`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L66-L67), [`mmpose/structures/bbox/transforms.py:406-435`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L406-L435), [`mmpose/datasets/transforms/topdown_transforms.py:67-70`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L67-L70) and [`mmpose/datasets/transforms/topdown_transforms.py:85-118`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L85-L118))
- mmpose computes `P1.x` as `c_x + (-0.5 * w)` in float64 (NumPy 1.24.4 in the exporter image) and stores the result in a float32 array. The float64 result, rounded to float32, always equals the float32 operation of Behaviour (double rounding from binary64 to binary32 is exact for `+` and `-`). The same holds for `P2.y` of the branch with `maintain_aspect_ratio: false`. mmpose `inference_topdown` keeps the dtype of the boxes of the caller. A float64 box gives a float64 centre and crop size; the warp points still round to float32. For a parity run, give mmpose float32 boxes. (mmpose [`mmpose/structures/bbox/transforms.py:411-416`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L411-L416) and [`mmpose/apis/inference.py:169-170`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/apis/inference.py#L169-L170))
- The vectors compare `M`, not crop pixels. OpenCV 4.5.4 and 5.0.0 warp one `M` to different pixels: 0 of 6370 crops equal on each of 6 runs, up to 7 grey levels. (OpenMMLab-Exporter `decisions/scripts/affine_crop_matrix_check.py`, record R1; [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md); [OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/0053-pose-sidecar-parity-runs.md) found 0 of 318 crops equal, up to 6 grey levels)
- mmpose maps the keypoints back with a closed form of the float32 centre and crop size, not with the inverse of `M`. The two differ by float32 rounding only: 9.6e-5 px at most on 6 runs. The inverse of the exact-math `M` gives the mmpose keypoints within 6.5e-5 px (RTMW m-256) and 7.3e-5 px (RTMW x-384). The inverse of the float32 `M` gives them within 8.7e-5 px and 9.5e-5 px. (OpenMMLab-Exporter `decisions/scripts/affine_crop_matrix_check.py`, record R2, the per-model values in the intake row D11 of the bundle `model-rtmw-wholebody133@openmmlab-exporter@v2` (secondary); [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md); mmpose [`mmpose/models/pose_estimators/topdown.py:150-156`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/topdown.py#L150-L156))
- To give the `M` of Behaviour, the package code needs two changes. `preprocess_image` (the `affine_person_crop` branch) must cast the person box to float32. This also applies to the full-frame box, which is float64 now. `get_warp_matrix` must put the second warp point left of the centre (`src_dir = [src_w * -0.5, 0]`, `dst_dir = [dst_w * -0.5, 0]`), as mmpose does. `bbox_xyxy2cs` and `top_down_affine` compute in the dtype of the box. Thus with a float32 box, the aspect fix already rounds `a` to float32. `rtmpose_preprocessing.py` has a second copy of `get_warp_matrix`, `bbox_xyxy2cs` and `top_down_affine`. The branch with `maintain_aspect_ratio: false` raises `NotImplementedError` now. The Inverse in `decode_simcc` uses the closed form of the centre and the scale. It needs no change, because it differs from the inverse of `M` by float32 rounding only. No validator change is necessary. Run the numeric cases of the vector file through `bbox_xyxy2cs`, `top_down_affine` and `get_warp_matrix`. Add a golden test with the three COCO cases: their `M` is the mmpose `M`. (skellytracker `skellytracker/core/detectors/processing/affine_crop.py` (`get_warp_matrix`, `bbox_xyxy2cs`, `top_down_affine`), `skellytracker/core/detectors/processing/image_preprocessing.py` (`preprocess_image`), `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py` and `skellytracker/core/detectors/processing/simcc_decode.py` (`decode_simcc`); part 6 of [`proposal.md`](../proposals/affine-crop-matrix/proposal.md#6-skellytracker-implementation-proposal); [ADR-3S5G](../decisions/entries/3S5G-affine-crop-matrix.md)) (implementation stage)
- A rotated ROI uses the form of mmpose `get_warp_matrix`: `_rotate_point` turns the second point, and for `fix_aspect_ratio=False` the third point, in float64. Then the float32 array rounds each point once. `_get_3rd_point` turns `P0 - P1` in float32. mmpose takes the rotation in degrees (`np.deg2rad(rot)`). For a parity run with mmpose, give `rot = degrees(r)` in float64. (mmpose [`mmpose/structures/bbox/transforms.py:410-428`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L410-L428), [`mmpose/structures/bbox/transforms.py:493-525`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L493-L525) and [`mmpose/datasets/transforms/topdown_transforms.py:99-108`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L99-L108))
- MediaPipe makes its crop matrix in float32 (`const float c = std::cos(sub_rect.rotation)`), and it maps the ROI to the tensor by its corners. The spec does not claim that a MediaPipe crop and an `affine_crop` crop give the same pixels. (mediapipe [`mediapipe/calculators/tensor/image_to_tensor_utils.cc:116-175`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/calculators/tensor/image_to_tensor_utils.cc#L116-L175))
- The pipeline grows the ROI first (`roi_from_points`). Then `crop_policy` grows it again along the ROI axes. The two factors multiply ([Behaviour](../../pipeline/nodes/detector.md#behaviour) of the detector node, item "Crop"). The vector case `roi-expand-along-roi-axes` shows the growth along the ROI axes. ([`proposal.md`](../proposals/affine-crop-rotated-roi/proposal.md#23-behaviour); [ADR-G3FA](../decisions/entries/G3FA-affine-crop-rotated-roi.md))

## Authoring guidance

- The mmpose `val_pipeline` has `GetBBoxCenterScale` (no `padding` argument) and `TopdownAffine(input_size=codec['input_size'])`. This maps to `method: affine_crop`, `interpolation: linear` and `crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}`. The exporter omits `pad_value`, so the default 0 applies. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:157-161`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L157-L161); OpenMMLab-Exporter [`rtmw/preprocess.py:26-35`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/preprocess.py#L26-L35))
- The RTMW `val_pipeline` does not write the value 1.25. Only the `face_pipeline` writes `padding=1.25`. The value 1.25 is the mmpose v1.3.2 default of `GetBBoxCenterScale.__init__(self, padding: float = 1.25)`. Record the source of the value before you write it. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:159`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L159), [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:389`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L389); mmpose [`mmpose/datasets/transforms/common_transforms.py:52`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/common_transforms.py#L52))
- A top-down model whose upstream crops a rotated ROI uses `affine_crop`. The ROI rules (the shift, the square and the scale of the ROI) are pipeline rules (`roi_from_points`), not `crop_policy`. Write in `crop_policy.expand_ratio` only the growth of the preprocessing of the model itself. The border of `affine_crop` is constant (`crop_policy.pad_value`). A model whose upstream fills the border with the edge pixels does not map exactly to this section: that is a `near-miss`. ([`proposal.md`](../proposals/affine-crop-rotated-roi/proposal.md#23-behaviour); [ADR-G3FA](../decisions/entries/G3FA-affine-crop-rotated-roi.md))
- Qualcomm-Exporter wrote `affine_person_crop` with `expand_ratio: 1.0` for the MediaPipe face landmark model (192x192) and the MediaPipe hand landmark model (256x256). It put the detector-to-ROI constants into pipeline manifests: face `dscale` 1.1, hand `dxy` 0.5 and `dscale` 2.5, and person `dscale` 1.5 with rotation from keypoints 2 and 3 plus pi/2. Its README says that `affine_person_crop` cannot express the rotation-aware ROI of MediaPipe. (Qualcomm-Exporter [`qai_sidecar.py:17-35`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L17-L35), [`qai_sidecar.py:270-277`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L270-L277), [`qai_sidecar.py:343-355`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L343-L355) and [`qai_catalog.py:80-94`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_catalog.py#L80-L94); Qualcomm-Exporter `qai_sidecar.py:51-59, 316-323, 389-401` and `qai_catalog.py:113-127`, commit a095041a5e9450df18637596fbaf6409f79e9fc6 on no branch (secondary); Qualcomm-Exporter [`README.md:129-132`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/README.md#L129-L132))
