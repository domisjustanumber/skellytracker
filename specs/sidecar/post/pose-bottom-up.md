---
id: post.pose.bottom_up
title: Bottom-up pose
kind: postprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - pose.estimator_type=bottom_up
  - outputs[].semantic=poses
  - outputs[].packed_keypoints
implemented_by:
  validate: skellytracker/core/sidecar/model.py::OutputSpec._check_output  # partial: it requires keypoint_axis 2 on poses; no packed_keypoints; the instance axis is not compared with the row axis
  decode: missing
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
vectors: null
status: {spec: stable, validate: partial, decode: missing}
---

# Bottom-up pose

## Fields

For `semantic: poses` (bottom-up, separate tensor), the tensor is `(B, I, K, 3)` with `keypoint_axis: 2`. The tensor axes are the batch, the instances (`I`), the keypoints (`K`) and the values `(x, y, score)` of each keypoint. When `pose.decode.is_3d: true`, the tensor is `(B, I, K, 4)`. In this case, the values of each keypoint are `x, y, z, score`, with `z` as root-relative depth in `pose.decode.depth_unit`. The instance axis `I` equals the row axis `Q` of the primary detection output.

[Shape key](pose-schema.md#shape-key)

### `packed_keypoints` (bottom-up packed rows)

Some one-stage models append the keypoints to each detection row. They do not emit a separate `poses` tensor (for example YOLO26-pose: `[B, 300, 57]` = 6 detection columns + 17 × `(x, y, score)`). The sidecar declares such a tensor **once**, as `semantic: detections`, with a `packed_keypoints` object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `packed_keypoints.offset` | int | yes | The index of the first keypoint column. It must equal `len(fields)`. |
| `packed_keypoints.components` | array[enum] | yes | The column order for each keypoint, drawn from `x`, `y`, `z` and `score`. It must contain `x` and `y`. It must contain `z` if and only if `pose.decode.is_3d: true`. |

```yaml
outputs:
  - name: output0
    dtype: {fp32: float32, fp16: float32, int8: float32}
    shape: [-1, 300, 57]
    rank: 3
    semantic: detections
    fields: [x1, y1, x2, y2, score, class_id]
    packed_keypoints:
      offset: 6
      components: [x, y, score]
```

Rules:

- This object is valid only when `role` includes both roles, when `pose.estimator_type: bottom_up`, and when `pose.decode.method: coordinate`.
- The condition `offset + K * len(components) == shape[-1]` must hold, where `K = len(pose.tracked_points)`. Component `c` of keypoint `k` is in column `offset + k * len(components) + index(c)`.
- Keypoint coordinates are in the scale that `pose.decode.coordinate_scale` sets. This scale must equal `decode.box_scale`. The model already activates each keypoint `score`.

## Behaviour

### Bottom-up decode

Bottom-up models (`bottom_up`, for example RTMO or YOLO26-pose) work on the full image. They decode with `coordinate`. Each detection row `q` has pose row `q`. The pose row is either `poses[b, q]` or the packed keypoint columns of `detections[b, q]`. Thus the instance count always equals the detection row count. The host runs the detection `decode` (`selection: none` or `nms`). It emits keypoints for exactly the surviving detection rows, in the same order. The host unprojects the keypoints with the same transform as the boxes.

Selection steps: [Selection: none](selection-none.md#behaviour), [Selection: NMS](selection-nms.md#behaviour).

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.bottom_up-1` A `poses` output must declare `keypoint_axis: 2`. Its instance axis must equal the row axis of the primary detection output.
- [ ] `V-post.pose.bottom_up-2` If `packed_keypoints` is present, it must be on a `detections` output. A sidecar with packed keypoints must have both roles, `estimator_type: bottom_up` and `pose.decode.method: coordinate`. `offset` must equal `len(fields)`. `components` must be a list of unique values from `x`, `y`, `z` and `score`. The list must contain `x` and `y`. It must contain `z` if and only if `is_3d: true`. When the last dimension is concrete, `offset + len(tracked_points) * len(components)` must equal `shape[-1]`. For a sidecar with packed keypoints, `pose.decode.coordinate_scale` (default `pixel`) must equal `decode.box_scale` (default `pixel`).

See also [Pose schema](pose-schema.md#validation-rules), [Coordinate decode](pose-decode-coordinate.md#validation-rules) and [Detection outputs](detection-outputs.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `decode.max_detections` on a bottom-up sidecar | Also the fixed instance count of the `poses` tensor. | Detection row count only; the instance count is the row count. |

Availability of `packed_keypoints` before `vNEXT`: [Schema versioning](../format/versioning.md#legacy-behaviour).

## Implementer guidance

## Authoring guidance
