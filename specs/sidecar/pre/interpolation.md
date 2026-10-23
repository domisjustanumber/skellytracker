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

## Authoring guidance
