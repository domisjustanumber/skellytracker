---
id: post.det.outputs
title: Detection outputs
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - outputs[].semantic=detections
  - outputs[].semantic=boxes
  - outputs[].semantic=scores
  - outputs[].semantic=class_logits
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_outputs_semantics  # partial: no boxes, scores, class_logits, class_axis or packed_keypoints; no float dtype check; the fields length is not compared with the shape
  decode: skellytracker/core/detectors/object_detectors/yolox/yolox_decode.py::yolox_detection_decode  # partial: it reads the outputs by position and last dimension, not by semantic or fields
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/test_yolox_detector.py
vectors: null
status: {spec: stable, validate: partial, decode: partial}
---

# Detection outputs

## Fields

### Detection output semantics

An `object_detector` sidecar must declare exactly **one primary detection output**: either one `detections` tensor or one `boxes` tensor. It can also declare companion tensors:

| Semantic | Shape | Dtype | Meaning |
|----------|-------|-------|---------|
| `detections` | `[B, Q, F]` | float | Packed rows. `fields` lists the name of each of the `F` columns (for example `x1, y1, x2, y2, score, class_id`). The output can also carry [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). Primary. |
| `boxes` | `[B, Q, 4]` | float | Box coordinates only. The scores come from a `scores` companion or a `class_logits` companion. Primary. |
| `scores` | `[B, Q]` | float | The confidence of each row. The rows align with the rows of the primary output. |
| `class_logits` | `[B, Q, C]` | float | Logits or scores for each row and each class. The class axis is last, unless `class_axis` sets a different axis. |

`B` is the batch. `Q` is the number of candidates (rows). `C` is the number of class slots of the model. Rules:

- A sidecar must have at most one `scores` output and at most one `class_logits` output.
- The shape of `scores` must equal the shape of the primary output without its final dimension.
- Use `class_logits` only with a `boxes` primary output and `decode.selection: top_k`. Its non-class axes must equal the outer axes `[B, Q]` of `boxes`. `C` must be concrete.

### `outputs` (detection)

The fields common to every output are in [Outputs](../common/outputs.md#fields).

Additional fields on detection output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fields` | array | conditional | The ordered field names for each detection row (for example `[x1, y1, x2, y2, score, class_id]`). Required for `semantic: detections`. Must not be present for the other detection semantics. If `packed_keypoints` is present, its length must equal `packed_keypoints.offset`. Otherwise, its length must equal the last tensor dimension. |
| `class_axis` | int | no | For `class_logits` only: the axis that holds the class dimension. The default is `-1`. A negative value follows Python/ONNX indexing. It must not be the batch axis. |
| `packed_keypoints` | object | no | For a `detections` output only, in one-stage models that can estimate pose. See [`packed_keypoints`](pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows). |

## Validation rules

### Detection (`object_detector`)

- [ ] `V-post.det.outputs-1` The sidecar must declare `decode` and exactly one primary detection output (`detections` or `boxes`). It must declare at most one `scores` output and at most one `class_logits` output.
- [ ] `V-post.det.outputs-2` A `detections` output must declare `fields`. When `shape[-1]` is concrete and `packed_keypoints` is absent, `len(fields) == shape[-1]` must be true. In all other cases, `len(fields) == packed_keypoints.offset` must be true. `fields` must be absent on every other semantic.
- [ ] `V-post.det.outputs-3` The last dimension of a `boxes` output must be `4`. The shape of `scores` must equal the primary shape without its last dimension. The non-class axes of `class_logits` must equal the outer axes of `boxes`. If `class_axis` is present, it must be a valid non-batch axis. The class dimension must be concrete.
- [ ] `V-post.det.outputs-4` The dtypes of `scores`, `class_logits`, `boxes` and `detections` must be float types.

See also [Outputs](../common/outputs.md#validation-rules), [Detection decode](detection-decode.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Legacy behaviour

Availability before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

- RTMDet-person, after the NMS cut, has two outputs: `boxes` `[B, A, 4]` (xyxy, model-input pixels) and `scores` `[B, A]`. The graph applies the sigmoid and squeezes the single class. (OpenMMLab-Exporter `onnx_convert/nms_cut.py:7-20`, 689d3ed)
- `A` is the sum of `(S / stride)^2` over the strides 8, 16 and 32. `A` is 2100 at `S` = 320 and 8400 at `S` = 640. (OpenMMLab-Exporter `notes/decisions/0008-cut-nms-tail.md:59`, c955162)
- The dense output is the complete candidate set. All 16,000 rows (200 x 80) of the capped rtmdet-tiny graph appear in the dense output with the same box and score. (OpenMMLab-Exporter `notes/decisions/0008-cut-nms-tail.md:60`, c955162)
- The YOLO26 `class_id` column holds whole numbers in a float32 tensor (`(index % nc).float()`). Cast the column to an integer before the class mapping. (Ultralytics-Exporter `yolo_sidecar.py:126-132`, f52ef68; ultralytics 8.4.184 `nn/modules/head.py:266-288`, installed copy in the Ultralytics-Exporter `.venv`)
- The wrapper of Qualcomm-Exporter for the MediaPipe person detector joins the two anchor-group heads along dim 1. Then it runs `mediapipe_detector_postprocess`: it clamps the scores to +/-100, applies the sigmoid, decodes the anchors to model-input pixels and converts the centre-size boxes to xyxy. It emits one `detections` output `[B, 896, 5]` with the fields `[x1, y1, x2, y2, score]`. The score is already a probability. (Qualcomm-Exporter `qai_catalog.py:206-250` and `qai_sidecar.py:114-123`, 4ca4586; qai_hub_models 0.64.0 `models/templates/mediapipe/utils.py:147-171`, installed copy in the Qualcomm-Exporter `.venv`)
- Keep every output that a later step needs. The wrapper returns only the four box columns and the score. It drops `coords[..., 4:]`, the keypoint columns that upstream returns with each box. The wiring record of Qualcomm-Exporter lists the keypoints 2 and 3 of upstream for the rotation of the pose ROI. Thus the ONNX output cannot rebuild that ROI. The historical pipeline manifest recorded `roi.mode: axis_aligned_approximation`. (Qualcomm-Exporter `qai_catalog.py:240-248`, 4ca4586; `qai_sidecar.py:27-34, 345-346`, c7b9132)

## Authoring guidance

- Do not keep a capped NMS in the graph. The in-graph NMS of mmdeploy with its default caps (`pre_top_k` 5000, 200 boxes for each class) loses AP against PyTorch: rtmdet-tiny -0.0019, rtmdet-xlarge -0.0027 and rtmdet-person-medium -0.0114 (AR 0.7247 to 0.6977). A capped graph is not the complete candidate set. (OpenMMLab-Exporter `notes/decisions/0008-cut-nms-tail.md:24-35`, c955162)
- RTMO: `dets` is `[-1, -1, 5]` with the fields `[x1, y1, x2, y2, score]`. The real RTMO-M graph declares `[1, -1, -1]`. Thus the contract of the exporter allows a dynamic row axis and an unknown last axis, and it requires 5 when the last axis is known. (OpenMMLab-Exporter `rtmo/contract.py:9-17`, f4511f2; `rtmo/sidecar.py:114-124`, eed3361; `notes/decisions/0020-rtmo-sidecar-contract.md:57-63`, 38ed76f)
- RF-DETR: `dets` is the `boxes` primary output (`[B, 300, 4]`, normalized cxcywh). `labels` is the `class_logits` output (`[B, 300, 91]`, `class_axis` -1). The sidecar has no `scores` tensor and no `detections` tensor. (Roboflow-Exporter `README.md:519-534`, b46b98f; `rf_detr/sidecar.py:254-270`, b34e351)
- YOLO26: the fields `[x1, y1, x2, y2, score, class_id]` follow the rows of Ultralytics `Detect.postprocess`: `[x1, y1, x2, y2, score, class_index, extra]`. (Ultralytics-Exporter `yolo_sidecar.py:126-132`, f52ef68; ultralytics 8.4.184 `nn/modules/head.py:249-264`, installed copy in the Ultralytics-Exporter `.venv`)
