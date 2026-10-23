---
id: common.outputs
title: Outputs
kind: common
---

# Outputs

## Fields

Each entry describes one ONNX output tensor. `outputs` is required for every sidecar. The fields below are common to every role; role-specific fields are described in the [object-detection](../post/detection-outputs.md#outputs-detection) and [pose-estimation](../post/pose-schema.md#outputs-pose) sections.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | ONNX output tensor name. Unique within `outputs` — one ONNX tensor is declared exactly once. |
| `dtype` | object | yes | Map of precision → output element type, like `input.dtype` (e.g. `{fp32: float32, fp16: float32}`). May differ from the input precision. Values: `float32`, `float16`, `uint8`, `int8`. |
| `shape` | array | no | Output tensor shape; `-1` marks a dynamic dim. Omitted for pose outputs whose shape varies with the input size (e.g. SIMCC bins). A size-dependent detection row dimension is `-1` at the family level. |
| `rank` | int | no | Tensor rank. Omitted when `shape` is omitted. |
| `semantic` | enum | yes | Closed set: `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints`, `poses`. Links the tensor to `decode` / `pose.decode`. |

## Behaviour

All sizes in a sidecar share one output contract: each output tensor has the same name, semantics, and keypoint/class count across sizes. Fixed-shape outputs differ only in the batch dimension; spatial-dependent pose outputs (SIMCC bins, heatmap H×W) and dense per-anchor detection outputs may also vary with input size. For size-dependent detection outputs, the family-level `shape` uses `-1` for the row dimension; `batch_artifacts.<N>.output_shapes` carries each artifact group's concrete shape. Per-batch shapes are declared via `batch_artifacts.<N>.output_shapes`.

A sidecar with both roles lists every tensor in one `outputs` array. Each tensor's `semantic` routes it to its decoder: `detections`, `boxes`, `scores`, and `class_logits` → `decode` (detection); `simcc_x`/`simcc_y`/`simcc_z`/`heatmap`/`keypoints`/`poses` → `pose.decode`. The detection semantics require `role` to include `object_detector`; the pose semantics require `role` to include `pose_estimator`.

## Validation rules

Rules marked **(vNEXT)**: see [Validation rules](../README.md#validation-rules).

- [ ] `V-common.outputs-1` `outputs[].name` values are unique.
- [ ] `V-common.outputs-2` Each output's `dtype` is present; its keys are a subset of `fp32`/`fp16`/`int8` covering the precisions declared in `batch_artifacts`, and its values are `float32`, `float16`, `uint8`, or `int8`.
- [ ] `V-common.outputs-3` On each output, `rank` (when present) equals `len(shape)`; `rank` is omitted when `shape` is omitted.
- [ ] `V-common.outputs-4` Each output's `semantic` is one of `detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints`, `poses` (`boxes`/`scores`/`class_logits` **(vNEXT)**). The detection semantics require `role` to include `object_detector`; the pose semantics require `role` to include `pose_estimator`.
- [ ] `V-common.outputs-5` All sizes share the same output names, semantics, and keypoint/class counts (spatial-dependent dims may scale with input size).

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
