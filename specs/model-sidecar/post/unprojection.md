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

- The reference decoder of OpenMMLab-Exporter applies the exact letterbox inverse.
  - It computes `(x - left) * (src_w / new_w)` and `(y - top) * (src_h / new_h)` with the rounded `new_w` and `new_h`. Then it clips to `[0, src_w]` and `[0, src_h]` when `clamp_boxes` is true. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py:161-173`, d2e68d2)
  - Test 1: a 640x480 source letterboxed to 320x240 at `top_left` scales the boxes by 2 and clamps them. The box `[300, 200, 400, 300]` gives `[600, 400, 640, 480]`. (OpenMMLab-Exporter `tests/test_decode_nms.py:86-91`, d2e68d2)
  - Test 2: a 200x100 source with `left` 0, `top` 16 and the new size 64x32 maps the box `(10, 26, 30, 46)` to `(31.25, 31.25, 93.75, 93.75)`. (OpenMMLab-Exporter `tests/test_decode_nms.py:94-98`, d2e68d2)
- Ultralytics `scale_boxes` and `scale_coords` (the path with `ratio_pad=None`) invert the letterbox as `(x - pad) / gain`.
  - The gain is `new / src` for each axis, from the rounded new size. The pad is `round((T - new) / 2 - 0.1)`. Then they clip to the source image. This is the letterbox inverse of the spec with `clamp_boxes`. (`ultralytics` 8.4.184 `utils/ops.py:151-170, 648-664`, installed in the Ultralytics-Exporter `.venv`, not in git)
- Roboflow-Exporter unprojects the RF-DETR boxes in one step.
  - It converts the normalized `cxcywh` boxes to `xyxy`. It multiplies them by `[w, h, w, h]` of the original image and clips them to `[0, scale]`. Then it derives `xywh` from the clipped corners. (Roboflow-Exporter `rf_detr/coco_format.py:130-137`, 16852ca)
  - For `stretch`, this equals the two steps of the spec (`normalized_01` times the target size, then times `src / target`), because the target size cancels. A test maps the box `[0.5, 0.5, 1, 1]` on a 100x100 image to `[0, 0, 100, 100]`. (Roboflow-Exporter `tests/test_onnx_runtime.py:203-216`, 16852ca)
  - The decoder takes the original size as `(width, height)`, but `target_size` is `[height, width]`. The tests use only the square size 100x100, so a swapped tuple would pass them. The accuracy run passes `(image.width, image.height)`. (Roboflow-Exporter `onnx_runtime/convert_rf_detr_coco.py:127-149, 168, 177` and `tests/test_onnx_runtime.py:208, 225, 238` (d0559b9); Roboflow-Exporter `pipeline/accuracy.py:190`, 4ae67c0)
  - skellytracker has no `stretch` unprojection yet. The `stretch` branch of `preprocess_image` returns `resize_meta = 1.0`, so the host has no scale factors. The [decision log](../../../decisions/README.md#open-work) lists this as open work.
- The exporters clamp the boxes to the source image, but the spec does not define the upper bound of the clamp (`[0, W]` or `[0, W - 1]`). The [decision log](../decisions/README.md#open-work) records this.
  - OpenMMLab-Exporter clips to `[0, src_w]` and `[0, src_h]`. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py:169-171`, d2e68d2)
  - Roboflow-Exporter clips to `[0, scale]` of the original image. (Roboflow-Exporter `rf_detr/coco_format.py:133`, 16852ca)
  - Ultralytics clips to the source image after the inverse (`clip_boxes`). (`ultralytics` 8.4.184 `utils/ops.py:151-170`, installed, not in git)
- Decoded coordinates can fall outside the model canvas, so clamp after the unprojection.
  - YOLO26 boxes and keypoints are in pixels of the 640 canvas. The head multiplies the box coordinates by the strides. The keypoints are `(xy + anchor) * stride`. (`ultralytics` 8.4.184 `nn/modules/head.py:226, 772-777`, installed, not in git)
- Qualcomm-Exporter unprojects with `x_src = (x - pad_x) / scale`.
  - The scale is `min(T_w / src_w, T_h / src_h)` without rounding. The pad is `(T - n) // 2`. This mirrors `denormalize_coordinates` of `qai_hub_models`, which also cuts the result to an integer. The letterbox inverse of the spec uses the rounded size. (Qualcomm-Exporter `qai_datasets.py:152-181`, 4ca4586; `qai_hub_models` 0.64.0 `utils/image_processing.py:499-538`, installed, not in git)
  - Example: a 427x640 source in a 128x128 canvas gives `n_w = 85`, `left = 21` and a content right edge at canvas x 106. The Qualcomm-Exporter formula gives 425. The spec formula gives 427. (hand calculation)
  - The Qualcomm-Exporter test (100x50 into 64x64, exact sizes 64x32, pad `(0, 16)`) cannot tell the two formulas apart. (Qualcomm-Exporter `tests/test_qai_datasets.py:55-64`, 4ca4586)
- No exporter has an inverse for `fit`, `none` or `affine_person_crop`, or a keypoint unprojection.
  - OpenMMLab-Exporter leaves the RTMW and RTMO decode to the consumer of the sidecar. (OpenMMLab-Exporter `rtmw/README.md:35-37`, ba0c087)
  - Its `NmsDecoder` raises an error for a `box_format` other than `xyxy` and for a `box_scale` other than `pixel`. (OpenMMLab-Exporter `onnx_runtime/decode_nms.py:108-116`, d2e68d2)
- The plans for the MediaPipe hand crops use a rotated crop with `cv2.getAffineTransform`, and they invert it with `cv2.invertAffineTransform(M)`.
  - The spec fixes the rotation at 0 and has no inverse for a rotated crop. The [changelog](../changelog.md#considered-and-deliberately-not-added) lists rotated crops as not added. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))
  - The plan lists a round-trip test (crop, then inverse, below 1e-3 px). MediaPipe-Exporter has only the plan and no code, so the test does not exist yet. (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))

## Authoring guidance

No exporter evidence yet.
