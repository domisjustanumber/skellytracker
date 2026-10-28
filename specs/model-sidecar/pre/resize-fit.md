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

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `pad_value`, `supports_dynamic_size` and `interpolation`.

## Behaviour

The host warps the whole source image onto the `target_size` canvas `[T_h, T_w]` with one affine transform. The transform scales the image by a single factor. The transform centres the image at fractional offsets. Unlike `letterbox`, the host does not round the scaled size or the offsets:

```text
s    = min(T_w / src_w, T_h / src_h)
left = (T_w - src_w * s) / 2          # fractional; not rounded
top  = (T_h - src_h * s) / 2          # fractional; not rounded
M    = [[s, 0, left],
        [0, s, top ]]
dst  = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=pad_value)
```

A `fit` resize must declare `pad_value`. It must not declare `pad_position`, `rounding`, `preserve_aspect_ratio` or `crop_policy`. This matches mmpose `BottomupResize` (RTMO). A `letterbox` is not equivalent to this resize at any scale other than `1`. A letterbox resize rounds the resized size. Also, `resize` + pad gives different pixels from `warpAffine`, even when the resized size has integer values.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `fit` | `x_src = (x - left) / s`, `y_src = (y - top) / s` — the exact inverse of `M`, using the unrounded `s`, `left` and `top` from the `fit` algorithm. |

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-pre.resize.fit-1` **(vNEXT)** A `fit` resize must declare `pad_value`.

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

- The probe `fit_resize` of OpenMMLab-Exporter is the pseudocode of this section in float64. It builds `M = [[s, 0, left], [0, s, top]]`. It calls `cv2.warpAffine` with `INTER_LINEAR`, `BORDER_CONSTANT` and `borderValue=(pad, pad, pad)`. (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:59-69`, 38ed76f)
- OpenMMLab-Exporter decision 0020 reports `input_max_abs_diff` 0 against mmpose `BottomupResize`. It reports identical detections and keypoints on four images. The tests used one model: RTMO-M, 640x640, fp32. (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:92-93, 121-122`, 38ed76f)
- The probe computes the pixel differences on `image[:, :, 1:]`. Channel 0 is not in the `input_max_abs_diff` figure or in the other pixel-difference figures of decision 0020. The detection and keypoint comparisons use the full input. (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:180-182, 211-213`, 38ed76f)
- The probe passes one border value for each channel. A scalar `borderValue` fills only channel 0 in OpenCV. The skellytracker function `fit_preprocess` passes a scalar. This is a recorded spec defect. ([Open work](../decisions/README.md#open-work), items "`fit` scalar pad" and "The `pad_value` row of `input.resize`") (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:66-69`, 38ed76f)
- The `fit` probe calls `cv2.warpAffine`. The letterbox host of the same exporter calls `cv2.resize`. These two calls place the pixel centres in different ways. This is a recorded spec defect. ([Open work](../decisions/README.md#open-work), item "The `input.resize` text") (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:66-69`, 38ed76f; OpenMMLab-Exporter `onnx_runtime/preprocess.py:112-116`, eed3361)
- No production code in OpenMMLab-Exporter applies `fit`. The module `rtmo/preprocess.py` declares the values only. (OpenMMLab-Exporter `rtmo/preprocess.py:10`, f4511f2)

## Authoring guidance

- The mmpose `val_pipeline` has `BottomupResize(input_size=input_size, pad_val=(114, 114, 114))`. This maps to `method: fit`, `pad_value: [114, 114, 114]` and `interpolation: linear`. The block has no `pad_position`, `rounding` or `crop_policy`. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:340`, 6c494a0; OpenMMLab-Exporter `rtmo/preprocess.py:15-21`, f4511f2)
- `input_size` is `(640, 640)` for RTMO-S, RTMO-M and RTMO-L, and `(416, 416)` for RTMO-T. `target_size` follows it. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-*.py:52`, 6c494a0)
- The mmpose `pad_val=(114, 114, 114)` has the same value for each channel. The exporter writes the scalar `114`, and so does the [RTMO body7 reference example](../examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml). The spec does not say what a scalar `pad_value` fills for `fit`. This is a recorded spec defect, so the scalar form depends on it. The array form does not. ([Open work](../decisions/README.md#open-work), item "The `pad_value` row of `input.resize`") (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:340`, 6c494a0; OpenMMLab-Exporter `rtmo/preprocess.py:15, 20`, f4511f2)
- A `letterbox` does not replace `fit`. Against mmpose `BottomupResize`, a `center` letterbox gives these results (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:77-90`, 38ed76f; [decision 0012](../decisions/0012-fit-resize-for-rtmo.md)):
  - 586x640, scale 1: pixel difference 0, top-box IoU 1.000, keypoint difference 0 px.
  - 320x240, integral scale 2: pixel difference mean 2.07 and max 81, top-box IoU 0.746, keypoint difference mean 1.43 px and max 8.60 px.
  - 333x500, fractional scale: pixel difference mean 0.46 and max 35, top-box IoU 0.988, keypoint difference mean 2.26 px and max 7.90 px.
  - 288x307, fractional scale: pixel difference mean 4.74 and max 88, top-box IoU 0.972, keypoint difference mean 5.13 px and max 17.89 px.
- The pixel differences in the list above cover channels 1 and 2 only. (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:211-213`, 38ed76f)
- A `top_left` letterbox changes 83 to 95 percent of the input pixels. It moves the keypoints of the top detection by 29 to 156 px on average. (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:87-89`, 38ed76f)
- The RTMO `data_preprocessor` sets `pad_size_divisor=32`. The sidecar has no field for it. The sizes 416 and 640 are multiples of 32 (13 and 20), so no extra padding applies at these sizes. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:419`, 6c494a0)
