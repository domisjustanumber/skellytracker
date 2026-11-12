---
id: post.keypoint.bottom_up
title: Bottom-up keypoints
kind: postprocessor
selectors:
  - keypoint.estimator_type=bottom_up
  - outputs[].semantic=instance_keypoints
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

# Bottom-up keypoints

## Fields

For `semantic: instance_keypoints` (bottom-up, separate tensor), the tensor is `(B, I, P, 3)` with `keypoint_axis: 2`. The tensor axes are the batch, the instances (`I`), the points (`P`) and the values `(x, y, score)` of each keypoint. When `keypoint.geometry: 3d`, the tensor is `(B, I, P, 4)` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). In this case, the values of each keypoint are `x, y, z, score`, with `z` as root-relative depth in `keypoint.decode.depth_unit`. The instance axis `I` equals the row axis `Q` of the primary detection output. The model already activates each keypoint `score`, so it is in `[0, 1]` ([Decoded keypoints](schema.md#decoded-keypoints); [ADR-88WQ](../../../../decisions/entries/88WQ-sidecar-vocabulary.md)).

[Shape key](schema.md#shape-key)

### `packed_keypoints` (bottom-up packed rows)

Some one-stage models append the keypoints to each detection row. They do not emit a separate `instance_keypoints` tensor (for example YOLO26-pose: `[B, 300, 57]` = 6 detection columns + 17 × `(x, y, score)`). The sidecar declares such a tensor **once**, as `semantic: packed_detections`, with a `packed_keypoints` object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `packed_keypoints.offset` | int | yes | The index of the first keypoint column. It must equal `len(fields)`. |
| `packed_keypoints.components` | array[enum] | yes | The column order for each keypoint, drawn from `x`, `y`, `z` and `score`. It must contain `x` and `y`. It must contain `z` if and only if `keypoint.geometry: 3d` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). |

```yaml
outputs:
  - name: output0
    dtype: {fp32: float32, fp16: float32}
    shape: [-1, 300, 57]
    semantic: packed_detections
    fields: [x1, y1, x2, y2, score, class_index]
    packed_keypoints:
      offset: 6
      components: [x, y, score]
```

Rules:

- This object is valid only when `role` includes both roles, when `keypoint.estimator_type: bottom_up`, and when `keypoint.decode.method: coordinate`.
- The condition `offset + P * len(components) == shape[-1]` must hold, where `P = len(keypoint.point_names)`. Component `c` of keypoint `k` is in column `offset + k * len(components) + index(c)`.
- Keypoint coordinates are in the space that `object.decode.box_space` sets. `keypoint.decode.coordinate_space` must not be present ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)). The model already activates each keypoint `score`. Thus a packed keypoint score is in `[0, 1]`.

## Behaviour

### Bottom-up decode

Bottom-up models (`bottom_up`, for example RTMO or YOLO26-pose) work on the full image. They decode with `coordinate`. Each detection row `q` has keypoint row `q`. The keypoint row is either `instance_keypoints[b, q]` or the packed keypoint columns of `packed_detections[b, q]`. Thus the instance count always equals the detection row count. The host runs the object decode (`object.decode.selection: none` or `nms`). It emits keypoints for exactly the surviving detection rows, in the same order. The host unprojects the keypoints with the same transform as the boxes.

Selection steps: [Selection: none](../object/selection-none.md#behaviour), [Selection: NMS](../object/selection-nms.md#behaviour).

## Validation rules

### Keypoint (`keypoint_detector`)

- [ ] `V-post.keypoint.bottom_up-1` An `instance_keypoints` output must declare `keypoint_axis: 2`. Its instance axis must equal the row axis of the primary detection output.
- [ ] `V-post.keypoint.bottom_up-2` If `packed_keypoints` is present, it must be on a `packed_detections` output. A sidecar with packed keypoints must have both roles, `estimator_type: bottom_up` and `keypoint.decode.method: coordinate`. `offset` must equal `len(fields)`. `components` must be a list of unique values from `x`, `y`, `z` and `score`. The list must contain `x` and `y`. It must contain `z` if and only if `keypoint.geometry: 3d`. When the last dimension is concrete, `offset + len(point_names) * len(components)` must equal `shape[-1]`. `keypoint.decode.coordinate_space` must not be present when `packed_keypoints` is present. The packed keypoints use `object.decode.box_space` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Keypoint schema](schema.md#validation-rules), [Coordinate decode](decode-coordinate.md#validation-rules) and [Object outputs](../object/outputs.md#validation-rules).

## Implementer guidance

- Pose rows align with detection rows in both bottom-up exports. RTMO: every kept detection has its keypoints inside its own box, and a shifted-row control mostly does not. YOLO26: the exported head gathers the keypoints with the same anchor index as the box, so each of the 300 rows carries its own box and keypoints. (OpenMMLab-Exporter [`notes/decisions/0020-rtmo-sidecar-contract.md:65-67`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L65-L67); ultralytics 8.4.184 `nn/modules/head.py:249-264`, installed copy in the Ultralytics-Exporter `.venv`)
- YOLO26-pose pose mAP50-95 (OKS) on COCO val2017 at batch 2, PyTorch against fp32 ONNX: nano 0.5599 / 0.5598, small 0.6188 / 0.6167, medium 0.6772 / 0.6739, large 0.6917 / 0.6886, xlarge 0.7065 / 0.7034. The fp16 pose AP is within 0.0003 of fp32. The report field `ap` of a pose model is the mean of `box.map` and `pose.map`. (Ultralytics-Exporter `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.report.json` and the reports of the other sizes and precisions, field `performance.*.metrics_detail.pose_ap`, untracked, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4; [`yolo_report.py:170-211`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_report.py#L170-L211))

## Authoring guidance

- For a bottom-up one-stage model with an in-graph NMS, three choices are wrong: `affine_crop` (no upstream box or ROI), `selection: nms` with `max_detections` (the row count varies) and a different letterbox `rounding` as a substitute for `fit`. (OpenMMLab-Exporter [`notes/decisions/0020-rtmo-sidecar-contract.md:97-110`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md#L97-L110))
- YOLO26-pose packed row: 6 columns for the box, the score and the class, then 17 x `(x, y, score)`, in all 57 columns. The constants are `_PACKED_POSE_KEYPOINT_START` 6 and `_PACKED_POSE_KEYPOINT_STRIDE` 3, and the ONNX metadata `kpt_shape` is `[17, 3]`. The builder rejects any other last dimension. In a sidecar, this row is `packed_keypoints: {offset: 6, components: [x, y, score]}`. (Ultralytics-Exporter [`yolo_sidecar.py:126-132`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L126-L132), [`yolo_sidecar.py:569-573`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L569-L573); `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, metadata `kpt_shape`, untracked, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
- The current file of Ultralytics-Exporter declares `output0` a second time as an `instance_keypoints` view (rank 3, `keypoint_axis` 2, 57 entries on axis 2). The commit message says that the spec validator of that time accepted this layout. The spec requires unique output names (V-common.outputs-1). (Ultralytics-Exporter [`yolo_sidecar.py:574-582`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L574-L582), [`yolo_sidecar.py:596`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L596) and the message of [its commit](https://github.com/domisjustanumber/Ultralytics-Exporter/commit/f52ef687a7a651447ff289d0e40a7856c2b7d50c))
