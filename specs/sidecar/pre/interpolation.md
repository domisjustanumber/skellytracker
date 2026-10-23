---
id: pre.resize.interpolation
title: Interpolation
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - input.resize.method=letterbox
  - input.resize.method=stretch
  - input.resize.method=fit
  - input.resize.method=affine_person_crop
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image  # partial. The affine_person_crop branch ignores interpolation. top_down_affine always uses cv2.INTER_LINEAR.
external_impl: []
tests: []
vectors: null
status: {spec: stable, validate: implemented, forward: partial}
---

# Interpolation

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `interpolation` | enum | no | This is the resize filter that the host uses. The default is `linear`. This field applies to `letterbox`, `stretch`, `fit` and `affine_person_crop`. |

`interpolation` is a field of [`input.resize`](../common/input.md#inputresize).

## Behaviour

**The host does not antialias resizes.** Every interpolation value below names the plain OpenCV filter (`cv2.resize` / `cv2.warpAffine`, half-pixel centres). These filters have no support that adapts when the host downscales an image. If a host uses another library, it must reproduce that behaviour. For example, torchvision with `antialias=False` reproduces it. PIL `BILINEAR` does not.

**Interpolation values:**

| Value | OpenCV constant | Typical use |
|-------|-----------------|-------------|
| `linear` | `cv2.INTER_LINEAR` | YOLO/Ultralytics, mmdet/mmpose, RF-DETR (default) |
| `area` | `cv2.INTER_AREA` | Downscale with area resampling |
| `cubic` | `cv2.INTER_CUBIC` | Upscale with higher quality |
| `nearest` | `cv2.INTER_NEAREST` | Nearest-neighbor |

## Validation rules

See [Input](../common/input.md#validation-rules).

## Implementer guidance

- The OpenMMLab-Exporter host maps `linear`, `area`, `cubic` and `nearest` to `cv2.INTER_LINEAR`, `cv2.INTER_AREA`, `cv2.INTER_CUBIC` and `cv2.INTER_NEAREST`. It resizes with `cv2.resize`. (OpenMMLab-Exporter `onnx_runtime/preprocess.py:44-49, 112-116`, eed3361)
- The evidence that this resize matches the upstream resize is at AP level. The full host chain gives an fp32 AP within 0.000391 of the source model on COCO val2017 (RTMDet-person nano and medium, batch 1 to 3). (OpenMMLab-Exporter `notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:41-48`, c85abf7)
- The one pixel-level check compares the new host code with the old host code on 30 COCO images. It does not compare the host with mmdet. (OpenMMLab-Exporter `notes/decisions/0027-one-decoder-no-torch-on-host.md:61-62`, 963732e)
- The OpenMMLab-Exporter probe calls `cv2.warpAffine` for `fit`. Its host calls `cv2.resize` for `letterbox`. The two calls place the pixel centres in different ways. This is a recorded spec defect. ([Open work](../../../notes/decisions/README.md#open-work), item "The `input.resize` text") (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:66-69`, 38ed76f; OpenMMLab-Exporter `onnx_runtime/preprocess.py:112-116`, eed3361)
- The `linear` filter of the Roboflow-Exporter host is a NumPy float32 bilinear resize. It uses half-pixel centres, no antialias filter and clamped edges. Its docstring says that it equals `torchvision` `resize(antialias=False)` and `interpolate(mode="bilinear", align_corners=False)`. (Roboflow-Exporter `onnx_runtime/preprocess.py:22-55`, d0559b9)
- That resize runs on the float [0, 1] CHW image, not on the uint8 HWC image. The spec does not state the dtype of the resize. This is a recorded spec defect. ([Open work](../../../notes/decisions/README.md#open-work), item "The spec does not state these facts, but a host needs them") (Roboflow-Exporter `onnx_runtime/preprocess.py:74-78`, d0559b9)
- The Python copy and the ONNX copy of that resize are tested as bit-identical (`atol=0`). No test compares it with `cv2.resize` and `INTER_LINEAR`. (Roboflow-Exporter `tests/test_rf_detr_adapters.py:126-130`, 16852ca)
- Upstream rfdetr 1.11.2 resizes with `F.resize(..., antialias=False)`. A code comment says that this matches the `cv2.INTER_LINEAR` of training. The file `rfdetr/export/_resize.py` holds a NumPy bilinear resize with the same `3 * src_h < 4 * out_h` branch as the Roboflow-Exporter host. (rfdetr 1.11.2 `detr.py:3020-3023` and `export/_resize.py:52`, installed in the Roboflow-Exporter `.venv`; Roboflow-Exporter `onnx_runtime/preprocess.py:44`, d0559b9)
- Do not resize with PIL. The [Behaviour](#behaviour) text says that PIL `BILINEAR` does not reproduce the plain OpenCV filter. The Roboflow-Exporter host uses PIL only to decode the image and to convert it to RGB. (Roboflow-Exporter `rf_detr/preprocess.py:1-6, 21-56`, 16852ca)
- The evaluation host of Qualcomm-Exporter resizes with PIL `Image.BILINEAR`, but its sidecar declares `linear`. The repo does not measure the pixel or AP effect. (Qualcomm-Exporter `qai_datasets.py:160` and `qai_sidecar.py:148`, 4ca4586)

## Authoring guidance
