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

## Authoring guidance

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
