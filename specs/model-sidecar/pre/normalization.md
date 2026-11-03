---
id: pre.normalize
title: Normalization
kind: preprocessor
selectors:
  - input.normalization=none
  - input.normalization=unit_float
  - input.normalization=imagenet
  - input.normalization.mode=custom
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CustomNormalization  # partial. NamedNormalizationMode has imagenet_bgr and imagenet_rgb, not imagenet. CustomNormalization has a color_format field. Nothing checks that input.color_format is present. InputSpec defaults input.normalization to imagenet_bgr (V-pre.normalize-1).
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::build_normalization_fn  # partial. The code has no imagenet mode. imagenet_bgr applies the RGB-ordered statistics to the B, G, R channels (specs/model-sidecar/decisions/entries/0009-imagenet-bgr-meaning.md). The spec does not define that computation. No code reads color_format. none and unit_float return float32, not input.dtype.
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
| `normalization` | string or object | yes | See [Behaviour](#behaviour). It has no default ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). |
| `normalization_by_precision` | object | no | This optional override maps a precision key ([V-common.sizes_and_artifacts-6](../common/sizes-and-artifacts.md#validation-rules)) to a named mode. The values must be mode strings only. They must not be a `custom` object. Declare a `custom` normalization at the top-level `normalization`. |

`normalization` and `normalization_by_precision` are fields of [`input`](../common/input.md#fields).

## Behaviour

`input.normalization` declares how the host transforms resized pixels before `session.run()`. Use a closed enum string, or a `custom` object.

| Mode | Host behavior | Typical use |
|------|---------------|-------------|
| `none` | Pass pixel values (0–255) unchanged, cast to `input.dtype`. Channel order from `input.color_format`. | Graphs that normalize internally, for example YOLOX |
| `unit_float` | `pixel / 255.0` per channel → `[0, 1]`. Channel order from `input.color_format`. | YOLO26, which uses Ultralytics-style float input |
| `imagenet` | `(pixel - mean) / std` on 0–255 pixels, in the channel order of `input.color_format`. Each channel uses the statistics of its color: R uses mean `123.675` / std `58.395`, G `116.28` / `57.12`, B `103.53` / `57.375`. | RTMDet (`bgr`), RTMW and RF-DETR (`rgb`) |
| `custom` | `(pixel * scale - mean) / std` on 0–255 channel values. `mean` and `std` are in the channel order of `input.color_format`. | Rare exports that match no named mode |

The `imagenet` statistics are the ImageNet statistics `0.485/0.456/0.406` and `0.229/0.224/0.225` × 255, in R, G, B order. With `color_format: bgr`, the tensor order is B, G, R, and B uses mean `103.53` / std `57.375`. One mode replaces the modes `imagenet_bgr` and `imagenet_rgb` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

The host applies normalization after the resize. For `affine_person_crop`, it applies normalization after the affine warp. For `method: none`, it applies normalization directly on the source image.

`input.color_format` must be present for each mode. It gives the channel order of the tensor. There is no default ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

`custom` has no `color_format` of its own. It uses `input.color_format` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

**Named mode (preferred):**

```yaml
input:
  color_format: rgb
  normalization: unit_float
```

**Custom mode:**

```yaml
input:
  color_format: rgb              # required; the order of mean and std
  normalization:
    mode: custom
    scale: 0.00392156862745098   # optional; default 1.0
    mean: [0.0, 0.0, 0.0]
    std: [1.0, 1.0, 1.0]
```

**Per-precision overrides:**

```yaml
# For an artifact whose graph takes raw uint8 pixels. The Ultralytics exporter writes this
# override only for a precision whose input dtype is uint8 or int8. The current YOLO26 exports
# take float32 input, so they need no override.
input:
  dtype: {fp32: float32, fp16: uint8}
  color_format: rgb
  normalization: unit_float
  normalization_by_precision:
    fp16: none
```

The resolution order for a selected precision is: `normalization_by_precision[precision]` → top-level `normalization`. There is no default ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).

The values of `normalization_by_precision` must be named mode strings only. A `custom` normalization must not be a per-precision override. Declare it at the top-level `normalization` instead.

## Validation rules

- [ ] `V-pre.normalize-1` `input.normalization` must be present ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). It must be a valid mode: `none`, `unit_float`, `imagenet` or a `custom` object. A `custom` object must have `mode: custom`. It must hold only the keys `mode`, `scale`, `mean` and `std`. If `mean` or `std` is present, it must have length 3. If `scale` is present, it must be positive. `input.color_format` must be present ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-pre.normalize-2` The keys of `normalization_by_precision` must be precision keys ([V-common.sizes_and_artifacts-6](../common/sizes-and-artifacts.md#validation-rules)). Its values must be valid mode strings. A value must not be a `custom` object.

See also [Input](../common/input.md#validation-rules).

## Implementer guidance

- The OpenMMLab-Exporter host takes BGR frames. Its mode `imagenet_bgr` (`imagenet` with `color_format: bgr`) applies the statistics directly to the BGR canvas. Its mode `imagenet_rgb` (`imagenet` with `color_format: rgb`) flips the channels to RGB first. For `none`, it casts to float32 and flips only when `color_format` is `rgb`. (OpenMMLab-Exporter [`onnx_runtime/preprocess.py:16`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L16), [`onnx_runtime/preprocess.py:120-151`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L120-L151))
- A BGR mean image `[103.53, 116.28, 123.675]` normalizes to 0 under both ImageNet modes of that host. (OpenMMLab-Exporter [`tests/test_onnx_runtime.py:439-443`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/adb332ce066323cc3d912b1a8250ee9b88eb3548/tests/test_onnx_runtime.py#L439-L443))
- That host supports only its modes `imagenet_bgr`, `imagenet_rgb` and `none`. It raises `ValueError` for `unit_float` and `custom`. (OpenMMLab-Exporter [`onnx_runtime/preprocess.py:42`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L42), [`onnx_runtime/preprocess.py:131-132`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L131-L132))
- The Roboflow-Exporter host divides by 255, resizes, and then applies `(x - mean) / std` with mean `(0.485, 0.456, 0.406)` and std `(0.229, 0.224, 0.225)` in RGB order. (Roboflow-Exporter [`onnx_runtime/preprocess.py:18-19`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L18-L19), [`onnx_runtime/preprocess.py:74-86`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L74-L86))
- This matches `imagenet` with `color_format: rgb` on 0-255 pixels. Mean x 255 is `123.675 / 116.28 / 103.53`, and std x 255 is `58.395 / 57.12 / 57.375`. The bilinear weights sum to 1, so the result differs from that mode only by the rounding of the resize. A test checks the channel means with `rtol=2e-3`. (Roboflow-Exporter [`tests/test_onnx_runtime.py:164-178`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/tests/test_onnx_runtime.py#L164-L178))
- The [Interpolation implementer guidance](interpolation.md#implementer-guidance) records a spec defect about the dtype of the resize.

## Authoring guidance

- The RTMW `PoseDataPreprocessor` has `mean=[123.675, 116.28, 103.53]`, `std=[58.395, 57.12, 57.375]` and `bgr_to_rgb=True`. This maps to `normalization: imagenet` and `color_format: rgb`. The statistics are in RGB order and apply after the flip. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:58-62`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L58-L62); OpenMMLab-Exporter [`rtmw/preprocess.py:9-11`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/preprocess.py#L9-L11))
- The RTMO `PoseDataPreprocessor` has `mean=[0, 0, 0]`, `std=[1, 1, 1]` and no `bgr_to_rgb` (the default is `False`). This maps to `normalization: none` and `color_format: bgr`. The model takes raw 0-255 BGR. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:417-421`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L417-L421); OpenMMLab-Exporter [`tests/test_rtmo.py:80-84`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/tests/test_rtmo.py#L80-L84))
- The RTMDet config has `bgr_to_rgb=False` and mean `(103.53, 116.28, 123.675)`. This maps to `normalization: imagenet` and `color_format: bgr`. The std is `(57.375, 57.12, 58.395)`. The mmdet config is in the exporter image and not in the repo. (OpenMMLab-Exporter [`notes/decisions/0004-channel-order-per-family.md:11-17`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0004-channel-order-per-family.md#L11-L17); OpenMMLab-Exporter [`onnx_runtime/preprocess.py:39`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L39))
- OpenMMLab-Exporter checks the channel order of each family against its configs. (OpenMMLab-Exporter [`tests/test_identities.py:63-90`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/tests/test_identities.py#L63-L90))
- RF-DETR uses `IMAGENET_MEAN` and `IMAGENET_STD` in RGB tensor order. This maps to `normalization: imagenet` and `color_format: rgb`. (Roboflow-Exporter [`rf_detr/sidecar.py:248-250`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L248-L250); Roboflow-Exporter [`onnx_runtime/preprocess.py:18-19`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L18-L19))
- The Ultralytics predictor flips BGR to RGB and then divides by 255. The validator also divides by 255. This maps to `normalization: unit_float`. (ultralytics 8.4.184 `engine/predictor.py:200-202` and `models/yolo/detect/val.py:109`, installed in the Ultralytics-Exporter `.venv`; Ultralytics-Exporter [`yolo_sidecar.py:383`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L383))
- The `qai_hub_models` input spec of the MediaPipe person detector has `value_range=(0.0, 1.0)` and `ColorFormat.RGB`. This maps to `normalization: unit_float`. The Qualcomm-Exporter sidecar writes `unit_float` and no `color_format`. Its host loads RGB with PIL and divides by 255. Its parity run uses a uniform [0, 1) input. (qai_hub_models 0.64.0 `models/mediapipe_pose/model.py:199-215`, installed in the Qualcomm-Exporter `.venv`; Qualcomm-Exporter [`qai_sidecar.py:139-150`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L139-L150) and [`qai_datasets.py:154-166`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_datasets.py#L154-L166); Qualcomm-Exporter [`qai_export.py:136`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L136))
- Check the graph for normalization nodes before you choose a mode. The YOLO26 fp32 graph has no scaling in front of the model: the only consumer of the input `images` is `/model.0/conv/Conv`. The host must divide by 255. (Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26-nano_b1_fp32.onnx`, untracked output)
- The published RF-DETR fp32 artifact is byte-identical to the raw `model.export()` output. It has no normalization nodes. (Roboflow-Exporter [`pipeline/ARTIFACT_CONTRACT.md:9-18`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/ARTIFACT_CONTRACT.md#L9-L18); Roboflow-Exporter [`rf_detr/export.py:82-98`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/rf_detr/export.py#L82-L98))
- Older RF-DETR graphs have preprocessing inside the graph. They have the initializers `rfdetr_prep_scale` and `rfdetr_prep_bias` and the metadata `rfdetr_input_contract=float_rgb_nchw_0_255`. They expect raw 0-255 RGB, so host ImageNet normalization would normalize twice. The writer rejects them. (Roboflow-Exporter [`pipeline/artifacts.py:108-114`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L108-L114); Roboflow-Exporter `exports/detectors/object_detectors/rfdetr/rfdetr-small_b1_fp32.onnx`, untracked output)
- In one checkout (Roboflow-Exporter HEAD c64fd2a32a51e29cdbf9b1b31473c8e441839d07), 22 of the 24 local `.onnx` files were older graphs of this kind. The constants are `scale = 1 / (255 x std)` and `bias = -mean / std` for each channel. For example, the R channel has `0.0171248 = 1 / 58.395` and `-2.1179 = -123.675 / 58.395`. (Roboflow-Exporter `exports/detectors/object_detectors/rfdetr/*.onnx`, untracked output; initializer values checked in the graph)
- The Ultralytics-Exporter writes `normalization_by_precision: {p: none}` only for a precision whose graph input dtype is `uint8` or `int8`. A test uses a `uint8` fixture. No real YOLO26 export triggers it, because every YOLO26 artifact takes float32 input. (Ultralytics-Exporter [`yolo_sidecar.py:391-393`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L391-L393); Ultralytics-Exporter [`tests/test_yolo_sidecar.py:274-284`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L274-L284); Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26.yaml:7`, untracked output)
- The rtmlib computation applies the RGB-ordered statistics, mean `(123.675, 116.28, 103.53)` and std `(58.395, 57.12, 57.375)`, to the B, G, R channels of the BGR frame. The RTMPose and RTMW sidecars in skellytracker use it. It is wrong for a model trained on RGB input. For an RTMPose hand model, it moved the keypoints by a median of 1.86, 6.98, 17.15, 3.10 and 12.34 px on five crops. `imagenet` with `color_format: rgb` gave 0.00 px. The RTMW sidecar in skellytracker may have the same defect. It is not measured. See [decision 0009](../decisions/entries/0009-imagenet-bgr-meaning.md). (the untracked hand models plan of OpenMMLab-Exporter (secondary); the only evidence)
