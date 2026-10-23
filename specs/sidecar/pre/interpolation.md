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
| `interpolation` | enum | no | Host resize filter; default `linear`. Applies to `letterbox`, `stretch`, `fit`, and `affine_person_crop`. |

`interpolation` is a field of [`input.resize`](../common/input.md#inputresize).

## Behaviour

**Resizes are not antialiased.** Every interpolation value below names the plain OpenCV filter (`cv2.resize` / `cv2.warpAffine`, half-pixel centres) without a downscale-adaptive support. A host using another library must reproduce that behaviour (e.g. torchvision `antialias=False`, not PIL `BILINEAR`).

**Interpolation values:**

| Value | OpenCV constant | Typical use |
|-------|-----------------|-------------|
| `linear` | `cv2.INTER_LINEAR` | YOLO/Ultralytics, mmdet/mmpose, RF-DETR (default) |
| `area` | `cv2.INTER_AREA` | Downscaling with area resampling |
| `cubic` | `cv2.INTER_CUBIC` | Higher-quality upscale |
| `nearest` | `cv2.INTER_NEAREST` | Nearest-neighbor |

## Validation rules

See [Input](../common/input.md#validation-rules).

## Implementer guidance

## Authoring guidance
