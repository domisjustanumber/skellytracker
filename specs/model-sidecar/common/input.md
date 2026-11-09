---
id: common.input
title: Input
kind: common
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::InputSpec  # partial. No color_format field (V-common.input-5) and no crop_policy.pad_value. Nothing checks that dtype covers the declared precisions. pad_value is not required for fit. OnnxDtype of InputSpec.dtype allows int8 (V-common.input-2).
  load: skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image  # partial. Ignores input.dtype. Raises for method none and for letterbox with preserve_aspect_ratio false. The spec does not define preserve_aspect_ratio.
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_image_preprocessing.py
vectors: vectors/common.input.yaml
status: {spec: stable, validate: partial, load: partial}
---

# Input

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | The name of the ONNX input tensor. |
| `dtype` | object | yes | A map of precision → ONNX graph input element type, for example `{fp32: float32, fp16: float16}`. When all variants share one type, every entry is that type, for example `{fp32: float32, fp16: float32}`. The keys are precision keys ([V-common.sizes_and_artifacts-6](sizes-and-artifacts.md#validation-rules)). They cover the precisions that `precision_artifacts` declares ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Each value is `float32`, `float16` or `uint8` (`V-common.input-2`). |
| `color_format` | enum | yes | `rgb` or `bgr`. This is the channel order of the tensor that the model consumes. Each normalization mode uses it ([Normalization](../pre/normalization.md#behaviour); [ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). |
| `resize` | object | no | The resize configuration (see below). A sidecar can omit this field only when the model consumes the source image unchanged. This has the same effect as `method: none`. `target_size` is set for each size (`sizes.<size>.input.resize.target_size`). The other fields are shared. |

[Normalization](../pre/normalization.md#fields) defines `normalization` and `normalization_by_precision`.

`shape` is **not** a top-level field. A sidecar declares the input image shape for each size as `sizes.<size>.input.shape` (see [Sizes](sizes-and-artifacts.md#sizes)). The batch axis of the shape is always `-1`. The batch is in `batching.batch` ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). It is never in the shape. The channels and the spatial dimensions are concrete. The input is NCHW: the shape is `[batch, channels, height, width]` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

`color_format` is a single top-level value. It covers every precision. A sidecar cannot describe a family whose precisions need different channel orders. The author must split that family.

`input` is required for `object_detector` and `pose_estimator` sidecars. This spec covers **single-input** models only. `input` describes exactly one input tensor. Multi-input models are out of scope.

### `input.resize`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method` | enum | yes | The value is one of the following. `letterbox` is a resize that keeps the aspect ratio, plus a pad. `stretch` is an independent x/y resize with no pad. `fit` is a full-frame affine fit that centres the image with fractional padding. `affine_person_crop` is for top-down pose. `none` passes the source image unchanged, with no resize. |
| `target_size` | array[2] | conditional | `[height, width]` that the host resizes the input to. A sidecar declares it in `sizes.<size>.input.resize.target_size`. The section of each `method` tells if it is present ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). |
| `pad_value` | int, float, or array[3] | conditional | It is a raw pixel value (before normalization). An array gives one value for each channel, in the order of `input.color_format`. A scalar `s` gives the same value to each channel: it means `[s, s, s]` ([ADR-BJF9](../../../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)). For `letterbox`, the default is `114`. The section of each `method` tells if it is present ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). |

Method-specific fields: [`pad_position`, `rounding`](../pre/resize-letterbox.md#fields), [`interpolation`, `compute_dtype`](../pre/interpolation.md#fields), [`crop_policy`](../pre/resize-affine-person-crop.md#fields).

Each `method` has its own section: [`letterbox`](../pre/resize-letterbox.md), [`stretch`](../pre/resize-stretch.md), [`fit`](../pre/resize-fit.md), [`affine_person_crop`](../pre/resize-affine-person-crop.md), [`none`](../pre/resize-none.md).

## Validation rules

- [ ] `V-common.input-1` If `input.resize.target_size` is present, it must be an array `[height, width]` of length 2.
- [ ] `V-common.input-2` `input.dtype` must be present. Its keys must be precision keys ([V-common.sizes_and_artifacts-6](sizes-and-artifacts.md#validation-rules)). The keys must cover the precisions that `precision_artifacts` declares ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). Its values must be `float32`, `float16` or `uint8` ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md); [ADR-XH1J](../decisions/entries/XH1J-normalize-input-dtype.md)).
- [ ] `V-common.input-3` `input.resize.method` must be `letterbox`, `stretch`, `fit`, `affine_person_crop` or `none` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). `input.resize.interpolation` must be `linear`, `area`, `cubic` or `nearest`.
- [ ] `V-common.input-4` If `pad_value` or `crop_policy.pad_value` is present, it must be a number or an array of numbers with length 3.
- [ ] `V-common.input-5` The value of `input.color_format` must be `rgb` or `bgr`. [V-pre.normalize-1](../pre/normalization.md#validation-rules) makes it required ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Identity](identity.md#validation-rules), [Sizes and artifacts](sizes-and-artifacts.md#validation-rules), [Normalization](../pre/normalization.md#validation-rules) and the section of each resize `method` ([`input.resize`](#inputresize)).

## Implementer guidance

- Do not infer the input dtype from the precision name. Read `input.dtype` for the precision.
  - The fp16 artifacts keep a `float32` input in OpenMMLab-Exporter, Roboflow-Exporter, Qualcomm-Exporter and the Ultralytics-Exporter CPU exports (`keep_io_types=True`). (OpenMMLab-Exporter [`onnx_convert/FP16_CONTRACT.md:11-16`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6ed34e42d6aab2ff126df9a6e297560f51775772/onnx_convert/FP16_CONTRACT.md#L11-L16) and [`rtmo/contract.py:8-11`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/contract.py#L8-L11); Roboflow-Exporter [`onnx_convert/fp16.py:186-195`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/onnx_convert/fp16.py#L186-L195), [`onnx_convert/fp16.py:204-219`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/onnx_convert/fp16.py#L204-L219); Qualcomm-Exporter [`qai_sidecar.py:74-76`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L74-L76) and [`qai_export.py:86-103`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L86-L103); Ultralytics-Exporter [`yolo_sidecar.py:352-360`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L352-L360), [`yolo_sidecar.py:379-381`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L379-L381) and [`README.md:37`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/README.md#L37))
  - Ultralytics applies `keep_io_types` only when it exports on the CPU. A GPU export is already float16 from `model.half()`, so its fp16 input is float16. The sidecar writer reads the dtype from the graph for this reason. (`ultralytics` 8.4.184 `engine/exporter.py:1235-1240`, installed in the exporter `.venv`, not in git; Ultralytics-Exporter [`tests/test_yolo_sidecar.py:50-79`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L50-L79))
- Every exporter artifact has static spatial dims equal to the `target_size` of its size, so the host must resize to `target_size`. (OpenMMLab-Exporter [`rtmdet_person/contract.py:8-9`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f946e5dd10174202330c63a7ddf1e9f5d4b543d7/rtmdet_person/contract.py#L8-L9), [`rtmw/contract.py:8-10`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/contract.py#L8-L10) and [`rtmo/contract.py:8-11`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/contract.py#L8-L11); Roboflow-Exporter [`pipeline/artifacts.py:119-124`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L119-L124))
- The reference hosts of the exporters decode an image with PIL `convert("RGB")`. They have no BGR path.
  - A host that holds OpenCV BGR frames must convert them to `input.color_format`. (Roboflow-Exporter [`onnx_runtime/preprocess.py:58-62`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L58-L62), [`onnx_runtime/preprocess.py:74-75`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L74-L75); Qualcomm-Exporter [`qai_datasets.py:154`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_datasets.py#L154))
  - The decision log records that the spec does not state that the host frame is BGR. ([decision log](../decisions/README.md#open-work))

## Authoring guidance

- Map `color_format` from the upstream data preprocessor.
  - mmpose `bgr_to_rgb=True` (RTMW) gives `rgb`. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:58-62`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/491c17b43c0f2011dfd386ab5c6345ef0f850ada/mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L58-L62))
  - RTMO sets no `bgr_to_rgb` (the default is `False`), so it gives `bgr`. RTMDet-person has `bgr_to_rgb=False`, so it gives `bgr`. OpenMMLab-Exporter checks each family against its config. (OpenMMLab-Exporter [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:417-421`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L417-L421); OpenMMLab-Exporter [`tests/test_identities.py:63-90`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/tests/test_identities.py#L63-L90))
  - Roboflow-Exporter writes `color_format: rgb` as a constant. (Roboflow-Exporter [`rf_detr/sidecar.py:248-250`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L248-L250))
  - The Ultralytics predictor flips BGR to RGB before it divides by 255. The validation loader also gives RGB (`Format(bgr=0.0)` flips the channels). Thus YOLO26 is `rgb`. (`ultralytics` 8.4.184 `engine/predictor.py:200-202`, `data/dataset.py:355` and `data/augment.py:2521`, installed, not in git)
  - The `qai_hub_models` input spec of the MediaPipe person detector declares `ColorFormat.RGB`, so it is `rgb`. (`qai_hub_models` 0.64.0 `models/mediapipe_pose/model.py:199-211`, installed, not in git)
- Read `input.name` from the single runtime input of the graph.
  - Remove the initializers from `graph.input` first. Some ONNX files list initializers there, so `graph.input[0]` can be a weight. (Roboflow-Exporter [`onnx_runtime/contract.py:20-23`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/contract.py#L20-L23), [`onnx_runtime/contract.py:43-47`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/contract.py#L43-L47))
  - The names in use are `input` (OpenMMLab-Exporter and RF-DETR), `images` (Ultralytics-Exporter) and `image` (Qualcomm-Exporter). (OpenMMLab-Exporter local export `exports/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml`, not in git; Roboflow-Exporter [`rf_detr/sidecar.py:240-241`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L240-L241); Ultralytics-Exporter [`yolo_sidecar.py:242-252`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L242-L252); Qualcomm-Exporter [`qai_export.py:43`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L43))
- Do not write `layout`. The spec has no `layout` field, because the input is always NCHW ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). The exporters write `layout: NCHW` as a constant after a rank-4 check. Roboflow-Exporter also writes `color_format: rgb` without a check of the graph. (Ultralytics-Exporter [`yolo_sidecar.py:292-293`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L292-L293), [`yolo_sidecar.py:382`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L382); Roboflow-Exporter [`rf_detr/sidecar.py:240-251`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L240-L251))
- Write `input.dtype` from the graph for each precision.
  - An fp16 conversion with `keep_io_types=True` keeps the float32 I/O, so the exporters write `{fp32: float32, fp16: float32}`. OpenMMLab-Exporter and Roboflow-Exporter check that the I/O of every published artifact is float32. (OpenMMLab-Exporter [`onnx_convert/FP16_CONTRACT.md:11-16`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6ed34e42d6aab2ff126df9a6e297560f51775772/onnx_convert/FP16_CONTRACT.md#L11-L16) and [`rtmo/contract.py:8-11`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/contract.py#L8-L11); Roboflow-Exporter [`pipeline/artifacts.py:125-130`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L125-L130))
  - Qualcomm-Exporter keys the map by the precisions that it finds across all batches. (Qualcomm-Exporter [`qai_sidecar.py:74-76`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L74-L76), [`qai_sidecar.py:106-110`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L106-L110))
  - With a float32 input for every precision, the sidecar needs no `normalization_by_precision`. (Ultralytics-Exporter [`yolo_sidecar.py:391-393`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L391-L393))
  - An `int8` graph input has no valid `input.dtype` (`V-common.input-2`). With `none`, the pixels 128 to 255 do not fit in `int8`: `200` becomes `-56` and `255` becomes `-1` (NumPy 2.5.4). The other modes give fractional values. Export the graph with a `uint8` or a float input.
- Convert a TFLite or MediaPipe model with `tf2onnx --inputs-as-nchw`. The spec has no NHWC form ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). A TFLite model has an NHWC input. This is a plan fact, with no other evidence.
  - The command `tf2onnx --opset 17 --inputs-as-nchw input_1` gives an NCHW ONNX input. The shapes are `[B, 3, 256, 256]` (re-crop) and `[B, 3, 224, 224]` (landmark). The command removes every layout `Transpose`. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))
