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
    dtype: {fp32: float32, fp16: float32}
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

- Pose rows align with detection rows in both bottom-up exports. RTMO: every kept detection has its keypoints inside its own box, and a shifted-row control mostly does not. YOLO26: the exported head gathers the keypoints with the same anchor index as the box, so each of the 300 rows carries its own box and keypoints. (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:65-67`, 38ed76f; ultralytics 8.4.184 `nn/modules/head.py:249-264`, installed copy in the Ultralytics-Exporter `.venv`)
- YOLO26-pose pose mAP50-95 (OKS) on COCO val2017 at batch 2, PyTorch against fp32 ONNX: nano 0.5599 / 0.5598, small 0.6188 / 0.6167, medium 0.6772 / 0.6739, large 0.6917 / 0.6886, xlarge 0.7065 / 0.7034. The fp16 pose AP is within 0.0003 of fp32. The report field `ap` of a pose model is the mean of `box.map` and `pose.map`. (Ultralytics-Exporter `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.report.json` and the reports of the other sizes and precisions, field `performance.*.metrics_detail.pose_ap`, untracked, HEAD 2e0280e; `yolo_report.py:170-211`, 2e0280e)

## Authoring guidance

- For a bottom-up one-stage model with an in-graph NMS, three choices are wrong: `affine_person_crop` (no upstream person box), `selection: nms` with `max_detections` (the row count varies) and a different letterbox `rounding` as a substitute for `fit`. (OpenMMLab-Exporter `notes/decisions/0020-rtmo-sidecar-contract.md:97-110`, 38ed76f)
- YOLO26-pose packed row: 6 columns for the box, the score and the class, then 17 x `(x, y, score)`, in all 57 columns. The constants are `_PACKED_POSE_KEYPOINT_START` 6 and `_PACKED_POSE_KEYPOINT_STRIDE` 3, and the ONNX metadata `kpt_shape` is `[17, 3]`. The builder rejects any other last dimension. At `vNEXT` this row is `packed_keypoints: {offset: 6, components: [x, y, score]}`. (Ultralytics-Exporter `yolo_sidecar.py:126-132, 569-573`, f52ef68; `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, metadata `kpt_shape`, untracked, HEAD 2e0280e)
- The current legacy file declares `output0` a second time as a `poses` view (rank 3, `keypoint_axis` 2, 57 entries on axis 2). The commit message says that the spec validator of that time accepted this layout. The spec requires unique output names (V-common.outputs-1). Decision [0018](../decisions/0018-one-declaration-per-tensor.md) (proposed) records this question. (Ultralytics-Exporter `yolo_sidecar.py:574-582, 596` and the commit message of f52ef68)
