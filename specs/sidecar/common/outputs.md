---
id: common.outputs
title: Outputs
kind: common
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::OutputSpec  # partial. No check for unique names (V-common.outputs-1) or for equal outputs in all sizes (V-common.outputs-5). OutputSemantic lacks boxes, scores and class_logits.
  load: missing  # No code binds an ONNX output by name or by semantic. Decoders read the tensors by position.
external_impl: []
tests: [skellytracker/tests/sidecar/test_model_validation.py]
vectors: null
status: {spec: stable, validate: partial, load: missing}
---

# Outputs

## Fields

Each entry describes one ONNX output tensor. `outputs` is required for every sidecar. The fields below are common to every role. The [object-detection](../post/detection-outputs.md#outputs-detection) and [pose-estimation](../post/pose-schema.md#outputs-pose) sections describe the role-specific fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | The name of the ONNX output tensor. It is unique within `outputs`. A sidecar declares one ONNX tensor exactly once. |
| `dtype` | object | yes | A map of precision → output element type, like `input.dtype` (for example `{fp32: float32, fp16: float32}`). The output type can differ from the input precision. Each value is `float32`, `float16`, `uint8` or `int8`. |
| `shape` | array | no | The output tensor shape. `-1` marks a dynamic dimension. A sidecar omits this field for pose outputs whose shape varies with the input size, for example SIMCC bins. If the row dimension of a detection output depends on the size, it is `-1` at the family level. |
| `rank` | int | no | The tensor rank. A sidecar omits it when it omits `shape`. |
| `semantic` | enum | yes | The value is from a closed set: `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints`, `poses`. It links the tensor to `decode` / `pose.decode`. |

## Behaviour

All sizes in a sidecar share one output contract. Each output tensor has the same name, the same semantics and the same keypoint or class count across sizes. Fixed-shape outputs differ only in the batch dimension. Two kinds of output can also vary with the input size: spatial-dependent pose outputs (SIMCC bins, heatmap H×W) and dense per-anchor detection outputs. For size-dependent detection outputs, the family-level `shape` uses `-1` for the row dimension. `batch_artifacts.<N>.output_shapes` carries the concrete shape of each artifact group. A sidecar declares the shapes for each batch in `batch_artifacts.<N>.output_shapes`.

A sidecar with both roles lists every tensor in one `outputs` array. The `semantic` of each tensor routes the tensor to its decoder. These semantics go to `decode` (detection): `detections`, `boxes`, `scores` and `class_logits`. These semantics go to `pose.decode`: `simcc_x`/`simcc_y`/`simcc_z`/`heatmap`/`keypoints`/`poses`. The detection semantics require `role` to include `object_detector`. The pose semantics require `role` to include `pose_estimator`.

## Validation rules

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.outputs-1` The values of `outputs[].name` must be unique.
- [ ] `V-common.outputs-2` Each output must have a `dtype`. Its keys must be a subset of `fp32`/`fp16`/`int8`. The keys must cover the precisions that `batch_artifacts` declares. Its values must be `float32`, `float16`, `uint8` or `int8`.
- [ ] `V-common.outputs-3` On each output, if `rank` is present, it must equal `len(shape)`. The output must omit `rank` when it omits `shape`.
- [ ] `V-common.outputs-4` The `semantic` of each output must be one of `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints`, `poses`. The values `boxes`/`scores`/`class_logits` are marked **(vNEXT)**. The detection semantics require `role` to include `object_detector`. The pose semantics require `role` to include `pose_estimator`.
- [ ] `V-common.outputs-5` All sizes must share the same output names, semantics, and keypoint or class counts. Spatial-dependent dimensions can scale with the input size.

See also [Identity](identity.md#validation-rules), [Sizes and artifacts](sizes-and-artifacts.md#validation-rules) and [Detection outputs](../post/detection-outputs.md#validation-rules).

## Implementer guidance

- Bind each tensor by its sidecar `name`, and route it by its `semantic`. Do not guess from the tensor name.
  - The RTMO tensor named `keypoints` has the semantic `poses`. (OpenMMLab-Exporter `rtmo/sidecar.py:110-139`, eed3361)
  - The RF-DETR tensor named `labels` holds class logits, not class ids. (Roboflow-Exporter `README.md:519-534`, b46b98f)
  - The ONNX decoder of Roboflow-Exporter binds the outputs by a name substring (`dets` or `box`, `labels` or `logit`). If that fails, it binds by shape, and then by position. (Roboflow-Exporter `onnx_runtime/convert_rf_detr_coco.py:74-113`, d0559b9)
  - Its PyTorch adapter renames `pred_boxes` and `pred_logits` to `dets` and `labels`. (Roboflow-Exporter `rf_detr/python_inference.py:86-96`, b46b98f)
- The legacy `yolo26-body.yaml` of Ultralytics-Exporter declares the single tensor `output0` twice, once as `detections` and once as `poses` (both `[1, 300, 57]`). The spec requires unique output names (`V-common.outputs-1`). The proposal [0018](../../../notes/decisions/0018-one-declaration-per-tensor.md) covers this layout. (Ultralytics-Exporter `yolo_sidecar.py:574-582, 596`, f52ef68; local export `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml:13-26`, not in git)

## Authoring guidance

- Write `-1` for an axis that depends on the input size, and put the concrete shapes in `output_shapes`.
  - RTMDet-person has 2100 rows at 320 and 8400 at 640. The family shapes are `[-1, -1, 4]` (`boxes`) and `[-1, -1]` (`scores`). (OpenMMLab-Exporter `rtmdet_person/sidecar.py:110-126` (eed3361) and `rtmdet_person/contract.py:10-11` (f946e5d))
  - RF-DETR writes `[-1, 300, 4]` and `[-1, 300, 91]` with rank 3. (Roboflow-Exporter `rf_detr/sidecar.py:254-270`, b34e351)
  - The RTMW SimCC outputs have no `shape` and no `rank`, because the bin counts scale with the input size. They have only the `semantic` (`simcc_y` when the name ends in `y`, else `simcc_x`), `keypoint_axis: 1` and `keypoint_count: 133`. (OpenMMLab-Exporter `rtmw/sidecar.py:108-120`, eed3361)
- Read the output name, the dtype for each precision, the shape and the rank from the graph. Hard-code only the `semantic` and the fields.
  - Ultralytics-Exporter reads them from the smallest-batch artifact of the first size (name `output0`, dtype `float32` for every precision). (Ultralytics-Exporter `yolo_sidecar.py:342-349, 363-371, 436-464`, f52ef68)
  - Roboflow-Exporter checks the names and the shapes against its identity constants (`num_queries` 300, `num_class_logits` 91). It allows only `float32` and `float16`. (Roboflow-Exporter `rf_detr/sidecar.py:125-151, 225-233`, b34e351)
  - Qualcomm-Exporter writes `detections` with the shape `[1, 896, 5]` and the fields `x1, y1, x2, y2, score`. The 896 anchors are a constant of its catalog, and a check runs the wrapped module once and compares the shape. (Qualcomm-Exporter `qai_sidecar.py:113-123` and `qai_catalog.py:44-46, 58, 155-173`, 4ca4586)
- Ultralytics-Exporter and Qualcomm-Exporter write the smallest native batch present into `outputs[].shape[0]`. The generated files have `1`, for example `[1, 300, 6]`. The spec examples have `-1`. The proposal [0019](../../../notes/decisions/0019-output-shape-batch-axis.md) covers the batch axis of `outputs[].shape`. (Ultralytics-Exporter local export `exports/detectors/object_detectors/yolo26/yolo26.yaml:14-19`, not in git, and `yolo_sidecar.py:342-349, 444-455` (f52ef68); Qualcomm-Exporter `qai_sidecar.py:79-95, 111-113` and `tests/test_qai_sidecar.py:20-52`, 4ca4586)
- After tf2onnx, map the output names by the TFLite output order and shape. Do not use the `Identity_N` numbering. These are plan facts, with no other evidence.
  - Assert the TFLite order and the shapes against a catalog before you rename. (MediaPipe-Exporter plan `plans/hand-pipeline-export.md:345-353`, no git repo)
  - The hand flag and the handedness outputs are both `[1, 1]`, so only the TFLite order (flag, then handedness) tells them apart. (MediaPipe-Exporter plan `plans/hand-pipeline-export.md:146-153, 192`, no git repo)
- The MediaPipe hand landmark model has outputs beyond the landmarks: a presence score, a handedness score and world landmarks. The closed `semantic` set has no value for them. The proposal [0021](../../../notes/decisions/0021-landmark-extra-outputs.md) covers these outputs. (MediaPipe-Exporter plan `plans/hand-pipeline-export.md:252-258, 356-361`, no git repo)

## Examples

```yaml
# One-stage detector + pose model with separate tensors (role: [object_detector, pose_estimator]).
# Excerpt of the RTMO body7 reference example. NMS is inside the graph, so the row count is
# dynamic and the host uses `selection: none`. For the packed single-tensor layout that
# YOLO26-pose emits, see the YOLO26 pose reference example.
outputs:
  - name: dets
    dtype: {fp32: float32}
    shape: [-1, -1, 5]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score]
  - name: keypoints
    dtype: {fp32: float32}
    shape: [-1, -1, 17, 3]
    rank: 4
    semantic: poses
    keypoint_axis: 2
    keypoint_count: 17

decode:                # detection decode — applies to the primary detection tensor
  selection: none      # graph-final rows; no `max_detections`, because the row count is dynamic
  box_format: xyxy
  box_scale: pixel
  score_field: score
  is_person_only: true
  confidence_threshold_default: 0.1

pose:                  # pose decode — `poses` rows follow the surviving detection rows
  estimator_type: bottom_up
  requires_object_detector: false
  # ... tracked_points / connections ...
  decode:
    method: coordinate
    coordinate_scale: pixel
```
