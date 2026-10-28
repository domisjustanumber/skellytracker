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
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::build_normalization_fn  # partial. imagenet_bgr has only the legacy meaning (specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md). No code reads color_format. none and unit_float return float32, not input.dtype.
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

- The OpenMMLab-Exporter host takes BGR frames. It applies the `imagenet_bgr` statistics directly to the BGR canvas. For `imagenet_rgb`, it flips the channels to RGB first. For `none`, it casts to float32 and flips only when `color_format` is `rgb`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:16, 120-151`, eed3361)
- A BGR mean image `[103.53, 116.28, 123.675]` normalizes to 0 under both ImageNet modes of that host. (OpenMMLab-Exporter `tests/test_onnx_runtime.py:439-443`, adb332c)
- That host supports only `imagenet_bgr`, `imagenet_rgb` and `none`. It raises `ValueError` for `unit_float` and `custom`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:42, 131-132`, eed3361)
- The Roboflow-Exporter host divides by 255, resizes, and then applies `(x - mean) / std` with mean `(0.485, 0.456, 0.406)` and std `(0.229, 0.224, 0.225)` in RGB order. (Roboflow-Exporter `onnx_runtime/preprocess.py:18-19, 74-86`, d0559b9)
- This matches `imagenet_rgb` on 0-255 pixels. Mean x 255 is `123.675 / 116.28 / 103.53`, and std x 255 is `58.395 / 57.12 / 57.375`. The bilinear weights sum to 1, so the result differs from `imagenet_rgb` only by the rounding of the resize. A test checks the channel means with `rtol=2e-3`. (Roboflow-Exporter `tests/test_onnx_runtime.py:164-178`, d0559b9)
- The Roboflow-Exporter resize runs on float data and not on uint8 data. The spec does not state the dtype of the resize. This is a recorded spec defect. ([Open work](../decisions/README.md#open-work), item "The spec does not state these facts, but a host needs them") (Roboflow-Exporter `onnx_runtime/preprocess.py:22-55, 74-78`, d0559b9)

## Authoring guidance

- The RTMW `PoseDataPreprocessor` has `mean=[123.675, 116.28, 103.53]`, `std=[58.395, 57.12, 57.375]` and `bgr_to_rgb=True`. This maps to `normalization: imagenet_rgb` and `color_format: rgb`. The statistics are in RGB order and apply after the flip. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:58-62`, 491c17b; OpenMMLab-Exporter `rtmw/preprocess.py:9-11`, eed3361)
- The RTMO `PoseDataPreprocessor` has `mean=[0, 0, 0]`, `std=[1, 1, 1]` and no `bgr_to_rgb` (the default is `False`). This maps to `normalization: none` and `color_format: bgr`. The model takes raw 0-255 BGR. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:417-421`, 6c494a0; OpenMMLab-Exporter `tests/test_rtmo.py:80-84`, eed3361)
- The RTMDet config has `bgr_to_rgb=False` and mean `(103.53, 116.28, 123.675)`. This maps to `normalization: imagenet_bgr` and `color_format: bgr`. The std is `(57.375, 57.12, 58.395)`. The mmdet config is in the exporter image and not in the repo. (OpenMMLab-Exporter `notes/decisions/0004-channel-order-per-family.md:11-17`, c955162; OpenMMLab-Exporter `onnx_runtime/preprocess.py:39`, eed3361)
- OpenMMLab-Exporter checks the channel order of each family against its configs. (OpenMMLab-Exporter `tests/test_identities.py:63-90`, eed3361)
- RF-DETR uses `IMAGENET_MEAN` and `IMAGENET_STD` in RGB tensor order. This maps to `normalization: imagenet_rgb` and `color_format: rgb`. (Roboflow-Exporter `rf_detr/sidecar.py:248-250`, b34e351; Roboflow-Exporter `onnx_runtime/preprocess.py:18-19`, d0559b9)
- The Ultralytics predictor flips BGR to RGB and then divides by 255. The validator also divides by 255. This maps to `normalization: unit_float`. (ultralytics 8.4.184 `engine/predictor.py:200-202` and `models/yolo/detect/val.py:109`, installed in the Ultralytics-Exporter `.venv`; Ultralytics-Exporter `yolo_sidecar.py:383`, f52ef68)
- The Ultralytics-Exporter sidecar has no `color_format`. Its input contract has the keys `name`, `dtype`, `layout`, `normalization` and `resize`. This is valid only in a legacy file, because a `vNEXT` sidecar with `unit_float` must declare `color_format` ([V-common.input-6](../common/input.md#validation-rules)). (Ultralytics-Exporter `yolo_sidecar.py:19, 379-390`, f52ef68)
- The `qai_hub_models` input spec of the MediaPipe person detector has `value_range=(0.0, 1.0)` and `ColorFormat.RGB`. This maps to `normalization: unit_float`. The Qualcomm-Exporter sidecar writes `unit_float` and no `color_format`. Its host loads RGB with PIL and divides by 255. Its parity run uses a uniform [0, 1) input. (qai_hub_models 0.64.0 `models/mediapipe_pose/model.py:199-215`, installed in the Qualcomm-Exporter `.venv`; Qualcomm-Exporter `qai_sidecar.py:139-150` and `qai_datasets.py:154-166`, 4ca4586; Qualcomm-Exporter `qai_export.py:136`, 8d8e05a)
- Check the graph for normalization nodes before you choose a mode. The YOLO26 fp32 graph has no scaling in front of the model: the only consumer of the input `images` is `/model.0/conv/Conv`. The host must divide by 255. (Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26-nano_b1_fp32.onnx`, untracked output)
- The published RF-DETR fp32 artifact is byte-identical to the raw `model.export()` output. It has no normalization nodes. (Roboflow-Exporter `pipeline/ARTIFACT_CONTRACT.md:9-18`, 4ae67c0; Roboflow-Exporter `rf_detr/export.py:82-98`, 4ae67c0)
- Older RF-DETR graphs have preprocessing inside the graph. They have the initializers `rfdetr_prep_scale` and `rfdetr_prep_bias` and the metadata `rfdetr_input_contract=float_rgb_nchw_0_255`. They expect raw 0-255 RGB, so host ImageNet normalization would normalize twice. The writer rejects them. (Roboflow-Exporter `pipeline/artifacts.py:108-114`, 4ae67c0; Roboflow-Exporter `exports/detectors/object_detectors/rfdetr/rfdetr-small_b1_fp32.onnx`, untracked output)
- In one checkout (Roboflow-Exporter HEAD c64fd2a), 22 of the 24 local `.onnx` files were older graphs of this kind. The constants are `scale = 1 / (255 x std)` and `bias = -mean / std` for each channel. For example, the R channel has `0.0171248 = 1 / 58.395` and `-2.1179 = -123.675 / 58.395`. (Roboflow-Exporter `exports/detectors/object_detectors/rfdetr/*.onnx`, untracked output; initializer values checked in the graph)
- The Ultralytics-Exporter writes `normalization_by_precision: {p: none}` only for a precision whose graph input dtype is `uint8` or `int8`. A test uses a `uint8` fixture. No real YOLO26 export triggers it, because the int8 artifacts take float32 input. (Ultralytics-Exporter `yolo_sidecar.py:391-393`, f52ef68; Ultralytics-Exporter `tests/test_yolo_sidecar.py:274-284`, f52ef68; Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26.yaml:7`, untracked output)
- The legacy `imagenet_bgr` is wrong for a model trained on RGB input. For an RTMPose hand model, it moved the keypoints by a median of 1.86, 6.98, 17.15, 3.10 and 12.34 px on five crops. `imagenet_rgb` gave 0.00 px. The RTMW sidecar in skellytracker may have the same defect. It is not measured. See [decision 0009](../decisions/0009-imagenet-bgr-meaning.md) and the Open work item about the `imagenet_bgr` default note ([Open work](../decisions/README.md#open-work)). (OpenMMLab-Exporter `plans/hand-models-PLAN.md:112-130`, untracked plan file; the only evidence)
