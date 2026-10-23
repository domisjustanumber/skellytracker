---
id: pre.resize.letterbox
title: Letterbox resize
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [input.resize.method=letterbox]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec._check_method_specific_fields  # partial. pad_position and rounding are not required. preserve_aspect_ratio is not forced to true.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::letterbox_preprocess  # partial. Puts the image at the top left, truncates the size, and nothing reads pad_position or rounding. preprocess_image raises for the legacy alias preserve_aspect_ratio false.
  inverse: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial. Divides by one ratio. Does not use the rounded n_w and n_h or the pad offsets.
external_impl: []
tests:
  - skellytracker/tests/test_image_preprocessing.py
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: vectors/pre.resize.letterbox.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: partial}
---

# Letterbox resize

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pad_position` | enum | `letterbox`: yes | The value is `top_left` or `center`. It sets where the resized image sits on the padded canvas. This field applies to `letterbox` only. |
| `rounding` | enum | `letterbox`: yes | The value sets how to round the resized width and height. `half_even` is Python `round`. `half_up` is `floor(x + 0.5)`. This field applies to `letterbox` only. |
| `preserve_aspect_ratio` | bool | no | This field applies to a letterbox resize only. When the field is present, it must be `true`. `false` is a legacy alias for `stretch`. See [Version-aware compatibility](#legacy-behaviour). |

[`input.resize`](../common/input.md#inputresize) and [Interpolation](interpolation.md) define `target_size`, `pad_value` and `interpolation`.

## Behaviour

The host resizes the whole source image with a single scale factor and pads it to `target_size` `[T_h, T_w]`:

```text
s    = min(T_w / src_w, T_h / src_h)
n_w  = max(1, R(src_w * s))         # R = resize.rounding
n_h  = max(1, R(src_h * s))
dst  = full((T_h, T_w, 3), pad_value)
left, top = (0, 0)                                          # pad_position: top_left
left, top = (floor((T_w - n_w) / 2), floor((T_h - n_h) / 2))  # pad_position: center
dst[top:top+n_h, left:left+n_w] = resize(src, (n_w, n_h), <interpolation>)
```

If the position is `center`, any odd remainder goes to the right and the bottom. The pair `half_even` and `center` matches Ultralytics `LetterBox`. The pair `half_up` and `top_left` matches mmdet `Resize(keep_ratio=True)` + `Pad(size=…)`.

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md).

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `letterbox` | `x_src = (x - left) * src_w / n_w`, `y_src = (y - top) * src_h / n_h` — the exact inverse of the resize, using the rounded `n_w`/`n_h` and the pad offsets from the letterbox algorithm. |

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-pre.resize.letterbox-1` **(vNEXT)** A `letterbox` resize must declare `pad_position` (`top_left` or `center`) and `rounding` (`half_even` or `half_up`). If `preserve_aspect_ratio` is present, it must be `true`.

See also [Input](../common/input.md#validation-rules) and [Sizes and artifacts](../common/sizes-and-artifacts.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `letterbox` + `preserve_aspect_ratio: false` | Alias for `method: stretch`. | Invalid; use `stretch`. |
| Letterbox `pad_position` / `rounding` absent | Existing host behaviour (implementation-defined). | Required. |

## Implementer guidance

- The OpenMMLab-Exporter host rounds the scaled size as `max(1, R(x))`. `R` is `floor(x + 0.5)` for `half_up` and Python `round` for `half_even`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:77-83, 99-102`, eed3361)
- The same host fills the canvas with `pad_value`. It pastes the image at `(0, 0)` for `top_left` and at `((T_w - n_w) // 2, (T_h - n_h) // 2)` for `center`. It resizes with `cv2.resize`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:103-116`, eed3361)
- Test with `top_left` and `half_up`: an image 501 wide and 333 high, with target 640x640, gives a resized image 640 wide and 425 high (333 x 640 / 501 = 425.38). The rows from 425 down hold 114. (OpenMMLab-Exporter `tests/test_onnx_runtime.py:397-404`, adb332c)
- Test with `center`: an image 200 wide and 100 high, with target 64x64, gives `left` 0 and `top` 16. (OpenMMLab-Exporter `tests/test_onnx_runtime.py:429-432`, adb332c)
- Test of two copies of the preprocessing: the adapter copy and the runtime copy give bit-identical float32 tensors and equal `(left, top, new_w, new_h)` for six image sizes at targets 320 and 640. (OpenMMLab-Exporter `tests/test_rtmdet_person.py:271-285`, ba0c087)
- Ultralytics `LetterBox` is `half_even` with `center`. It computes `n = max(round(src * r), 1)` with Python `round`. A source 1280 wide and 853 high, with target 640, gives `n_h` 426. `half_up` gives 427. (ultralytics 8.4.184 `data/augment.py:1792-1798`, installed in the Ultralytics-Exporter `.venv`)
- The same code pads with `top = round(dh - 0.1)` and `bottom = round(dh + 0.1)`, where `dh = (T - n) / 2`. This gives `floor((T - n) / 2)` at the top and the left. The odd remainder goes to the bottom and the right. A loop over the remainders 0 to 640 found no difference from the `center` rule of this section. (ultralytics 8.4.184 `data/augment.py:1807-1812`, installed in the Ultralytics-Exporter `.venv`)
- Apply the declared `rounding`. For `half_even` and `half_up`, do not cut the scaled size with `int()` or `floor`. Float error can drop one pixel on the limiting side. Qualcomm-Exporter uses `n = max(1, int(src * s))`. With target 128, 84,828 of the 811,801 source sizes from 100 to 1000 give a limiting side of 127. For example, a source 100 wide and 103 high gives 124x127. `half_up` and `half_even` give 128 for the limiting side in all of these cases. The repo does not record the calculation. An upstream that cuts the size is neither `half_even` nor `half_up`. Do not map it to one of them. Its intake row is a `near-miss` ([decision 0023](../../../notes/decisions/0023-letterbox-floor-and-scale-inverse.md), status proposed). (Qualcomm-Exporter `qai_datasets.py:157-162`, 4ca4586)
- The `letterbox_preprocess` function of skellytracker also cuts the size with `int()`. See the Open work item "Letterbox rounding". ([Open work](../../../notes/decisions/README.md#open-work))

## Authoring guidance

- The mmdet `test_pipeline` has `Resize(scale=(S, S), keep_ratio=True)` and `Pad(size=(S, S), pad_val=dict(img=(114, 114, 114)))`. This maps to `method: letterbox`, `pad_position: top_left`, `rounding: half_up`, `pad_value: 114` and `target_size: [S, S]`. The exporter also writes `interpolation: linear`. (OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmdet_nano_320-8xb32_coco-person.py:81-85`, f29d9bb; OpenMMLab-Exporter `onnx_runtime/preprocess.py:28-35`, eed3361)
- mmdet rounds the resized size with `int(x + 0.5)`. This is `half_up`. (OpenMMLab-Exporter `notes/decisions/0009-detector-output-layout-and-decode.md:52-57`, 38ed76f)
- The RTMDet-person nano config is an adapted copy. It is not a byte copy of the mmpose v1.3.2 config. The medium config inherits `mmdet::rtmdet/rtmdet_m_8xb32-300e_coco.py`, which is not in the repo. The medium values rest on OpenMMLab-Exporter decision 0009 and on AP parity. (OpenMMLab-Exporter `mmdeploy-convert/CONFIG_SOURCES.md:22, 33-34`, 491c17b; OpenMMLab-Exporter `mmdeploy-convert/model_cfgs/rtmdet_m_640-8xb32_coco-person.py:1`, 491c17b; OpenMMLab-Exporter `notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-48`, c85abf7)
- Do not copy the resize from the mmdeploy `pipeline.json`. It describes the mmdeploy SDK runtime, which stretches. It does not describe the mmdet test pipeline. On `rtmdet-tiny` with 500 val images, the letterbox gives AP 0.449 and the stretch gives AP 0.437. (OpenMMLab-Exporter `notes/decisions/0009-detector-output-layout-and-decode.md:52-62`, 38ed76f)
- The Ultralytics `LetterBox` arguments map as follows. `new_shape=(640, 640)` is `target_size`. `padding_value=114` is `pad_value: 114`. `interpolation=cv2.INTER_LINEAR` is `linear`. `center=True` is `pad_position: center`. Python `round` is `rounding: half_even`. (ultralytics 8.4.184 `data/augment.py:1702-1736, 1798`, installed in the Ultralytics-Exporter `.venv`)
- The current Ultralytics-Exporter writes `method: letterbox`, `preserve_aspect_ratio: true`, `pad_value`, `interpolation` and `target_size`. It does not write `pad_position` or `rounding`. Its `schema_version` is `v2024.09.1019`, so the file is a legacy file. A `vNEXT` letterbox must declare both fields ([V-pre.resize.letterbox-1](#validation-rules)). (Ultralytics-Exporter `yolo_sidecar.py:19, 384-389`, f52ef68)
- Ultralytics parity numbers compare different canvases. `Model.val` sets `rect=True` for the PyTorch baseline. The validator sets `rect=False` for a static ONNX model. `predict` uses `LetterBox` with `auto=False` for a non-dynamic ONNX model. No ablation separates this difference from the detector AP gap of 0.0045 to 0.0087 (box AP at batch 2, PyTorch against fp32 ONNX). (ultralytics 8.4.184 `engine/model.py:639`, `engine/validator.py:232-233`, `engine/predictor.py:233-243`, installed in the Ultralytics-Exporter `.venv`; Ultralytics-Exporter `yolo_validation.py:170, 271`, f52ef68; Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26-*_b2_fp32.report.json`, fields `performance.pytorch.ap` and `performance.converted.ap`, untracked output)
- The Ultralytics validation loader resizes the long side to 640 before `LetterBox` runs. It uses `cv2.INTER_LINEAR` and `math.ceil` sizes. A validator AP number thus includes a resize step that the sidecar does not describe. State which upstream path a parity proof compares with. (ultralytics 8.4.184 `data/base.py:296-309, 454-458`, installed in the Ultralytics-Exporter `.venv`)
- The `resize_pad` function of `qai_hub_models`, used by the MediaPipe person detector, centres the image and pads with 0. It resizes with torch `interpolate(mode="bilinear")` and cuts the scaled size with `math.floor`. The `rounding` field has no value for `floor`. The [model intake](../templates/model-intake.md#verdicts) gives an upstream `floor` as its example of a `near-miss`. A proposal for this difference is [decision 0023](../../../notes/decisions/0023-letterbox-floor-and-scale-inverse.md) (status proposed). (qai_hub_models 0.64.0 `utils/image_processing.py:262-360`, installed in the Qualcomm-Exporter `.venv`; Qualcomm-Exporter `qai_datasets.py:152-167`, 4ca4586)
- The Qualcomm-Exporter sidecar of the person detector declares `method: letterbox`, `preserve_aspect_ratio: true`, `pad_value: 0` and `interpolation: linear`. It has no `pad_position` and no `rounding`, so it is a legacy file. (Qualcomm-Exporter `qai_sidecar.py:12, 144-149`, 4ca4586)
- The upstream inverse of `resize_pad` subtracts the pad and divides by the unrounded scale. The inverse of this section uses the rounded `n_w` and `n_h`. See [Unprojection](../post/unprojection.md). (qai_hub_models 0.64.0 `utils/image_processing.py:499-538`, installed in the Qualcomm-Exporter `.venv`)
