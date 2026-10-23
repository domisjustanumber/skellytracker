---
id: post.unprojection
title: Unprojection
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [role=object_detector, role=pose_estimator]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode  # partial. Checks only where coordinate_scale is valid. DetectionDecodeSpec has no box_scale field.
  decode: skellytracker/core/detectors/processing/object_detection_decode.py::decode_prenms  # partial. No shared unprojection function. Each decoder divides by the letterbox ratio or applies the affine inverse itself (decode_simcc). No normalized_01 or normalized_11 conversion.
external_impl: []
tests:
  - skellytracker/tests/test_object_detection_decode.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
vectors: vectors/post.unprojection.yaml
status: {spec: stable, validate: partial, decode: partial}
---

# Unprojection

## Behaviour

Decoded box and keypoint coordinates are always in the input image of the model, with a **top-left origin**. In this origin, `x` grows to the right and `y` grows down. The host unprojects the coordinates to the source image (see [Unprojection](unprojection.md)). A sidecar cannot override the origin.

The host first converts the decoded coordinates to **model-input pixels**. The value of `box_scale` or `coordinate_scale` sets the conversion:

- `normalized_01`: the host multiplies `x` by the model input width and `y` by the model input height.
- `normalized_11`: the host maps `[-1, 1]` to `[0, width]` for the horizontal axis and to `[0, height]` for the vertical axis.

Then the host maps the coordinates back to the source image. This list gives the mapping for each resize method:

- `letterbox`: [Letterbox resize](../pre/resize-letterbox.md#inverse)
- `stretch`: [Stretch resize](../pre/resize-stretch.md#inverse)
- `fit`: [Fit resize](../pre/resize-fit.md#inverse)
- `none`: [No resize](../pre/resize-none.md#inverse)
- `affine_person_crop`: [Affine person crop](../pre/resize-affine-person-crop.md#inverse)

## Implementer guidance

## Authoring guidance
