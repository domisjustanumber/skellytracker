---
id: pre.resize.interpolation
title: Interpolation
kind: preprocessor
selectors:
  - input.resize.method=letterbox
  - input.resize.method=stretch
  - input.resize.method=fit
  - input.resize.method=affine_person_crop
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec  # partial. ResizeSpec has no compute_dtype field. Its extra="forbid" rejects each value, also uint8 and float32. It does not check V-pre.resize.interpolation-1.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image  # partial. The affine_person_crop branch ignores interpolation. top_down_affine always uses cv2.INTER_LINEAR. Each branch resizes the uint8 frame and ignores compute_dtype.
external_impl:
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::letterbox
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::affine_person_crop
tests: []
vectors: vectors/pre.resize.interpolation.yaml
status: {spec: stable, validate: partial, forward: partial}
---

# Interpolation

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interpolation` | enum | no | This is the resize filter that the host uses. The default is `linear`. This field applies to `letterbox`, `stretch`, `fit` and `affine_person_crop`. |
| `compute_dtype` | enum | no | This is the dtype in which the host resizes and pads the image: `uint8` or `float32`. The default is `uint8`. This field applies to `letterbox`, `stretch`, `fit` and `affine_person_crop`. [Compute dtype](#compute-dtype) gives the behaviour ([ADR-PHJ3](../decisions/entries/PHJ3-resize-compute-dtype.md)). |

`interpolation` and `compute_dtype` are fields of [`input.resize`](../common/input.md#inputresize).

## Behaviour

**The host does not antialias resizes.** Every interpolation value below names the plain OpenCV filter of `cv2.resize` or `cv2.warpAffine`. [Pixel centres](#pixel-centres) gives the call of each method. These filters have no support that adapts when the host downscales an image. If a host uses another library, it must reproduce that behaviour and the pixel centres of the call. For example, torchvision with `antialias=False` reproduces `cv2.resize`. PIL `BILINEAR` does not.

**Interpolation values:**

| Value | OpenCV constant | Typical use |
|-------|-----------------|-------------|
| `linear` | `cv2.INTER_LINEAR` | YOLO/Ultralytics, mmdet/mmpose, RF-DETR (default) |
| `area` | `cv2.INTER_AREA` | Downscale with area resampling |
| `cubic` | `cv2.INTER_CUBIC` | Upscale with higher quality |
| `nearest` | `cv2.INTER_NEAREST` | Nearest-neighbor |

### Pixel centres

Each resize method that resizes the image uses the pixel-centre convention of one OpenCV call ([ADR-G79P](../decisions/entries/G79P-pixel-centres-per-resize-method.md)). `none` makes no resize call. Its inverse is the identity. The table gives the call of each other method:

| Method | Call | Coordinate | Centre of pixel `i` |
|--------|------|------------|---------------------|
| `letterbox`, `stretch` | `cv2.resize` | A position on the image plane. Pixel `i` covers `[i, i + 1)`. | `i + 0.5` |
| `fit`, `affine_person_crop` | `cv2.warpAffine` | A pixel index. The destination pixel `(x, y)` samples the source at `M^-1 · (x, y, 1)`. | `i` |

`cv2.resize` samples at half-pixel centres for `linear`, `cubic` and `area`. With `cv2.resize`, `nearest` (`cv2.INTER_NEAREST`) gives the destination pixel `x` the source pixel `floor(x * src_n / dst_n)`. This is not a half-pixel rule. The coordinate convention of the table does not change.

The model-input coordinates of [Unprojection](../post/unprojection.md#behaviour) use the convention of the method. The Inverse of each method maps them back in the same convention. No step adds or removes a `0.5` offset.

### Compute dtype

The host resizes and pads the image in `input.resize.compute_dtype` ([ADR-PHJ3](../decisions/entries/PHJ3-resize-compute-dtype.md)). Then the [normalization](normalization.md#behaviour) takes the result and casts it to `input.dtype`.

| Value | Host behaviour |
|-------|----------------|
| `uint8` | The host resizes and pads the 8-bit image. The result is the 8-bit output of the OpenCV filter. |
| `float32` | The host casts the 8-bit image to float32 first. Then it resizes and pads in float32. It does not round or clamp the result. The values stay on the 0-255 scale. |

The pad and the border of the warp have the compute dtype. A `none` resize has no `compute_dtype` ([No resize](resize-none.md#validation-rules)).

## Validation rules

- [ ] `V-pre.resize.interpolation-1` If `input.resize.compute_dtype` is present, it must be `uint8` or `float32` ([ADR-PHJ3](../decisions/entries/PHJ3-resize-compute-dtype.md)).

See also [Input](../common/input.md#validation-rules).

## Implementer guidance

- The OpenMMLab-Exporter host maps `linear`, `area`, `cubic` and `nearest` to `cv2.INTER_LINEAR`, `cv2.INTER_AREA`, `cv2.INTER_CUBIC` and `cv2.INTER_NEAREST`. It resizes with `cv2.resize`. (OpenMMLab-Exporter [`onnx_runtime/preprocess.py:44-49`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L44-L49), [`onnx_runtime/preprocess.py:112-116`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L112-L116))
- The evidence that this resize matches the upstream resize is at AP level. The full host chain gives an fp32 AP within 0.000391 of the source model on COCO val2017 (RTMDet-person nano and medium, batch 1 to 3). (OpenMMLab-Exporter [`notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-48`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md#L41-L48))
- The one pixel-level check compares the new host code with the old host code on 30 COCO images. It does not compare the host with mmdet. (OpenMMLab-Exporter [`notes/decisions/0027-one-decoder-no-torch-on-host.md:61-62`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/963732e271d13c0c90feb8775374ca2bba422c8d/notes/decisions/0027-one-decoder-no-torch-on-host.md#L61-L62))
- The OpenMMLab-Exporter probe calls `cv2.warpAffine` for `fit`. Its host calls `cv2.resize` for `letterbox`. Each call has the convention that [Pixel centres](#pixel-centres) gives for its method. (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:66-69`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L66-L69); OpenMMLab-Exporter [`onnx_runtime/preprocess.py:112-116`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L112-L116))
- The two conventions differ. With `linear` at the scale `s`, one destination pixel samples source positions that differ by `0.5 * (1 / s - 1)` source pixels on each axis. A 2x upscale of `[0, 10, 20, 30]` gives `2.5` with `cv2.resize` and `5.0` with `cv2.warpAffine` at destination `x = 1`. (OpenCV 4.13.0; [ADR-G79P](../decisions/entries/G79P-pixel-centres-per-resize-method.md))
- mmpose v1.3.2 `TopdownAffine` and `BottomupResize` call `cv2.warpAffine` with `INTER_LINEAR`. Their `use_udp` is `False` by default. The top-down and bottom-up pose estimators map the keypoints back with `keypoints / input_size * input_scale + input_center - 0.5 * input_scale`. This is `M^-1` with no `0.5` offset. ([`mmpose/datasets/transforms/topdown_transforms.py:104-118`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L104-L118), [`mmpose/datasets/transforms/bottomup_transforms.py:575-592`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/bottomup_transforms.py#L575-L592), [`mmpose/models/pose_estimators/topdown.py:154-156`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/topdown.py#L154-L156), [`mmpose/models/pose_estimators/bottomup.py:172-174`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/bottomup.py#L172-L174))
- `qai_hub_models` 0.64.0 crops the MediaPipe face and hand ROIs with `cv2.warpAffine`. It maps the landmarks back with `cv2.invertAffineTransform`. (`qai_hub_models` 0.64.0 `utils/image_processing.py:569` and `models/templates/mediapipe/app.py:571-586`, installed in the Qualcomm-Exporter `.venv`)
- The `linear` filter of the Roboflow-Exporter host is a NumPy float32 bilinear resize. It uses half-pixel centres, no antialias filter and clamped edges. Its docstring says that it equals `torchvision` `resize(antialias=False)` and `interpolate(mode="bilinear", align_corners=False)`. (Roboflow-Exporter [`onnx_runtime/preprocess.py:22-55`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L22-L55))
- That resize runs on the float [0, 1] CHW image, not on the uint8 HWC image. This is `compute_dtype: float32` ([Compute dtype](#compute-dtype)). (Roboflow-Exporter [`onnx_runtime/preprocess.py:74-78`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L74-L78))
- Each filter of the [Behaviour](#behaviour) table is linear in the pixel values, and its weights sum to 1. Thus a host can divide the image and the pad value by 255 before a `float32` resize. The result changes only by float32 rounding: at most 3.6e-7 for each filter on a noise image, for `cv2.resize`, and for `cv2.warpAffine` with the border value divided too. ([`resize_compute_dtype_probe.py`](../decisions/scripts/resize_compute_dtype_probe.py), OpenCV 4.13.0, NumPy 2.4.6)
- A text copy of the Roboflow-Exporter host resizes a 480x640 gradient to 560x560. After the normalization, it differs from `float32` by at most 1.19e-6, and from `uint8` by at most 1.27e-2. One 8-bit step is 1.74e-2. On noise, it differs from `float32` by at most 2.47e-4. The host computes its source coordinates in float32: on a 1080x1920 noise image, this gives a difference of up to 2.19e-2 (0-255) against `cv2.resize` in float32, and float64 coordinates give 3.05e-5. ([`resize_compute_dtype_probe.py`](../decisions/scripts/resize_compute_dtype_probe.py), OpenCV 4.13.0, NumPy 2.4.6; Roboflow-Exporter [`onnx_runtime/preprocess.py:74-78`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L74-L78))
- With `float32`, a `cubic` resize can give values below 0 and above 255, because the host does not clamp. On a noise image, the range was -63.66 to 314.37. With `uint8`, OpenCV clamps the values to 0-255. ([`resize_compute_dtype_probe.py`](../decisions/scripts/resize_compute_dtype_probe.py), OpenCV 4.13.0)
- The Python copy and the ONNX copy of that resize are tested as bit-identical (`atol=0`). No test compares it with `cv2.resize` and `INTER_LINEAR`. (Roboflow-Exporter [`tests/test_rf_detr_adapters.py:126-130`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/tests/test_rf_detr_adapters.py#L126-L130))
- Upstream rfdetr 1.11.2 resizes with `F.resize(..., antialias=False)`. A code comment says that this matches the `cv2.INTER_LINEAR` of training. The file `rfdetr/export/_resize.py` holds a NumPy bilinear resize with the same `3 * src_h < 4 * out_h` branch as the Roboflow-Exporter host. (rfdetr 1.11.2 `detr.py:3020-3023` and `export/_resize.py:52`, installed in the Roboflow-Exporter `.venv`; Roboflow-Exporter [`onnx_runtime/preprocess.py:44`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/d0559b9c95a9ba9922045e2bc5aeae9fb596a6b1/onnx_runtime/preprocess.py#L44))
- Do not resize with PIL. The [Behaviour](#behaviour) text says that PIL `BILINEAR` does not reproduce the plain OpenCV filter. The Roboflow-Exporter host uses PIL only to decode the image and to convert it to RGB. (Roboflow-Exporter [`rf_detr/preprocess.py:1-6`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/rf_detr/preprocess.py#L1-L6), [`rf_detr/preprocess.py:21-56`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/rf_detr/preprocess.py#L21-L56))
- The evaluation host of Qualcomm-Exporter resizes with PIL `Image.BILINEAR`, but its sidecar declares `linear`. The repo does not measure the pixel or AP effect. (Qualcomm-Exporter [`qai_datasets.py:160`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_datasets.py#L160) and [`qai_sidecar.py:148`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L148))

## Authoring guidance

- Ultralytics `LetterBox` and the dataset loader use plain `cv2.resize` with `cv2.INTER_LINEAR` and no antialias. The exporter writes `linear`. (ultralytics 8.4.184 `data/augment.py:1711, 1839-1840` and `data/base.py:304, 309, 311`, installed in the Ultralytics-Exporter `.venv`; Ultralytics-Exporter [`yolo_sidecar.py:388`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L388))
- All three OpenMMLab-Exporter writers (RTMDet-person, RTMW and RTMO) write `interpolation: linear` explicitly. (OpenMMLab-Exporter [`onnx_runtime/preprocess.py:28-35`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L28-L35); OpenMMLab-Exporter [`rtmw/preprocess.py:29-35`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/preprocess.py#L29-L35); OpenMMLab-Exporter [`rtmo/preprocess.py:16`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L16), [`rtmo/preprocess.py:20`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/f4511f222fc94f3c6600d6fb9503e1cfa6e37855/rtmo/preprocess.py#L20))
- RF-DETR is `linear` (bilinear, `antialias=False`), not `cubic`. (Roboflow-Exporter [`README.md:499-501`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b46b98fa826ffdef46fdfba66c1f8b189a68f8c6/README.md#L499-L501); Roboflow-Exporter [`rf_detr/sidecar.py:251`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L251); rfdetr 1.11.2 `detr.py:3020-3023`, installed in the Roboflow-Exporter `.venv`)
- The `qai_hub_models` PyTorch path of the MediaPipe person detector resizes with torch `interpolate(mode="bilinear")`. This is `linear`. (qai_hub_models 0.64.0 `utils/image_processing.py:349-351`, installed in the Qualcomm-Exporter `.venv`)
- Write `compute_dtype: float32` when the upstream resizes a float image. rfdetr 1.11.2 divides the uint8 image by 255. Then it resizes the float image. (rfdetr 1.11.2 `detr.py:2993-2995` and `detr.py:3020-3024`, installed in the Roboflow-Exporter `.venv`)
- Omit `compute_dtype` when the upstream resizes the 8-bit image. Ultralytics letterboxes the uint8 image and then divides by 255. The OpenMMLab-Exporter letterbox host fills a uint8 canvas. (ultralytics 8.4.184 `engine/predictor.py:194-202`, installed in the Ultralytics-Exporter `.venv`; OpenMMLab-Exporter [`onnx_runtime/preprocess.py:103-116`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/onnx_runtime/preprocess.py#L103-L116))
- The `qai_hub_models` app of the MediaPipe person detector divides by 255 and then resizes the float frames. The evaluation host of Qualcomm-Exporter resizes the 8-bit image with PIL. Choose the value with a parity run. (qai_hub_models 0.64.0 `utils/image_processing.py:145, 165` and `models/templates/mediapipe/app.py:231-233, 323-325`, installed in the Qualcomm-Exporter `.venv`; Qualcomm-Exporter [`qai_datasets.py:160`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_datasets.py#L160))
