---
id: pre.resize.fit
title: Fit resize
kind: preprocessor
selectors: [input.resize.method=fit]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields  # partial. pad_value is not required (V-pre.resize.fit-1).
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::fit_preprocess  # partial. A scalar pad_value fills only channel 0, and an array of int values raises.
  inverse: missing  # fit_preprocess returns scale, left and top. No code applies (x - left) / s.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: vectors/pre.resize.fit.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: missing}
---

# Fit resize

## Fields

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `pad_value` and `interpolation`.

## Behaviour

The host warps the whole source image onto the `target_size` canvas `[T_h, T_w]` with one affine transform. The transform scales the image by a single factor. The transform centres the image at fractional offsets. Unlike `letterbox`, the host does not round the scaled size or the offsets:

```text
s    = min(T_w / src_w, T_h / src_h)
left = (T_w - src_w * s) / 2          # fractional; not rounded
top  = (T_h - src_h * s) / 2          # fractional; not rounded
M    = [[s, 0, left],
        [0, s, top ]]
border = [pad_value] * 3 if pad_value is a scalar else pad_value
dst  = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=border)
```

`border` has one value for each channel. A scalar `pad_value` fills each channel ([ADR-BJF9](../../../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)).

`warpAffine` is `cv2.warpAffine`. Its pixel centres are at integer coordinates ([Pixel centres](interpolation.md#pixel-centres)). This resize matches mmpose `BottomupResize` (RTMO). A `letterbox` is not equivalent to this resize at any scale other than `1`. A letterbox resize rounds the resized size. Also, `resize` + pad gives different pixels from `warpAffine`, even when the resized size has integer values.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `fit` | `x_src = (x - left) / s`, `y_src = (y - top) / s` — the exact inverse of `M`, using the unrounded `s`, `left` and `top` from the `fit` algorithm. |

The positions are pixel indices of `cv2.warpAffine`. The inverse adds no `0.5` offset ([Pixel centres](interpolation.md#pixel-centres)).

## Validation rules

- [ ] `V-pre.resize.fit-1` A `fit` resize must declare `pad_value`. Each size must declare `input.resize.target_size`. The resize must not declare `pad_position`, `rounding` or `crop_policy` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md); [ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Implementer guidance

- The probe `fit_resize` of OpenMMLab-Exporter is the pseudocode of this section in float64. It builds `M = [[s, 0, left], [0, s, top]]`. It calls `cv2.warpAffine` with `INTER_LINEAR`, `BORDER_CONSTANT` and `borderValue=(pad, pad, pad)`. (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:59-69`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L59-L69))
- OpenMMLab-Exporter ADR-0020 reports `input_max_abs_diff` 0 against mmpose `BottomupResize`. It reports identical detections and keypoints on four images. The tests used one model: RTMO-M, 640x640, fp32. (OpenMMLab-Exporter [`notes/decisions/0020-rtmo-sidecar-contract.md:92-93`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L92-L93), [`notes/decisions/0020-rtmo-sidecar-contract.md:121-122`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L121-L122))
- The probe computes the pixel differences on `image[:, :, 1:]`. Channel 0 is not in the `input_max_abs_diff` figure or in the other pixel-difference figures of ADR-0020. The detection and keypoint comparisons use the full input. (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:180-182`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L180-L182), [`notes/decisions/scripts/rtmo_sidecar_probe.py:211-213`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L211-L213))
- The probe passes one border value for each channel. A scalar `borderValue` fills only channel 0 in OpenCV 4.13.0: `114` gives `[114, 0, 0]`. Expand a scalar `pad_value` to `border` before the call, as the Behaviour does. The skellytracker function `fit_preprocess` passes the scalar unchanged ([implementation plan](../../sidecar-implementation-plan.md#m8--validation-preprocessing-and-decode-gaps)). (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:66-69`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L66-L69))
- No production code in OpenMMLab-Exporter applies `fit`. The module `rtmo/preprocess.py` declares the values only. (OpenMMLab-Exporter [`rtmo/preprocess.py:10`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L10))

## Authoring guidance

- The mmpose `val_pipeline` has `BottomupResize(input_size=input_size, pad_val=(114, 114, 114))`. This maps to `method: fit`, `pad_value: 114` (or `[114, 114, 114]`) and `interpolation: linear`. The block has no `pad_position`, `rounding` or `crop_policy`. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:340`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L340); OpenMMLab-Exporter [`rtmo/preprocess.py:15-21`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L15-L21))
- `input_size` is `(640, 640)` for RTMO-S, RTMO-M and RTMO-L, and `(416, 416)` for RTMO-T. `target_size` follows it. (OpenMMLab-Exporter `rtmo-*.py:52` in [`mmdeploy-convert/model_cfgs/`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs))
- The mmpose `pad_val=(114, 114, 114)` has the same value for each channel. The exporter writes the scalar `114`, and so does the [RTMO body7 reference example](../examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml). The scalar `114` and the array `[114, 114, 114]` give the same border. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:340`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L340); OpenMMLab-Exporter [`rtmo/preprocess.py:15`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L15), [`rtmo/preprocess.py:20`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L20))
- A `letterbox` does not replace `fit`. Against mmpose `BottomupResize`, a `center` letterbox gives these results (OpenMMLab-Exporter [`notes/decisions/0020-rtmo-sidecar-contract.md:77-90`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L77-L90); [ADR-0012](../decisions/entries/0012-fit-resize-for-rtmo.md)):
  - 586x640, scale 1: pixel difference 0, top-box IoU 1.000, keypoint difference 0 px.
  - 320x240, integral scale 2: pixel difference mean 2.07 and max 81, top-box IoU 0.746, keypoint difference mean 1.43 px and max 8.60 px.
  - 333x500, fractional scale: pixel difference mean 0.46 and max 35, top-box IoU 0.988, keypoint difference mean 2.26 px and max 7.90 px.
  - 288x307, fractional scale: pixel difference mean 4.74 and max 88, top-box IoU 0.972, keypoint difference mean 5.13 px and max 17.89 px.
- The pixel differences in the list above cover channels 1 and 2 only. (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:211-213`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L211-L213))
- A `top_left` letterbox changes 83 to 95 percent of the input pixels. It moves the keypoints of the top detection by 29 to 156 px on average. (OpenMMLab-Exporter [`notes/decisions/0020-rtmo-sidecar-contract.md:87-89`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L87-L89))
- The RTMO `data_preprocessor` sets `pad_size_divisor=32`. The sidecar has no field for it. The sizes 416 and 640 are multiples of 32 (13 and 20), so no extra padding applies at these sizes. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:419`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L419))
