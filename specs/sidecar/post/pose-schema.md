---
id: post.pose.schema
title: Pose schema
kind: schema
since: v2024.09.1019
changed_in: [vNEXT]
selectors:
  - role=pose_estimator
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseSpec  # partial: the output check in SidecarModel._check_pose_output_shapes has no packed_keypoints case; keypoint_count is not checked on poses outputs
  load: skellytracker/core/sidecar/loader.py::load_sidecar  # partial: the detectors read tracked_points and the first connections entry only; derived_points are never computed
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_hand_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_face_sidecar.py
  - skellytracker/tests/sidecar/test_rtmw_sidecar.py
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# Pose schema

## Fields

The pose output contract declares these items:

- the keypoints that a model produces
- the skeleton or skeletons that join the keypoints
- how the keypoints map onto the canonical (VRM 1.0) skeleton
- how the host decodes raw outputs into keypoints

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.estimator_type` | enum | yes | The value is `top_down_single_person`, `top_down_multi_person` or `bottom_up`. A top-down model sees one person in each crop (single-person outputs). A bottom-up model emits all persons in one pass (for example RTMO or YOLO26-pose). |
| `pose.requires_object_detector` | bool | yes | The value is `true` when the model uses a person crop from an upstream detector. This is the case for top-down models: the host warps each detection box with `affine_person_crop`. The value is `false` when the model uses the full image. This is the case for bottom-up models. It must be consistent with `estimator_type`. |
| `pose.landmark_schema` | string | no | The keypoint convention that the model uses (for example `COCO_WholeBody`, `COCO17`, `MediaPipe_Hand`, `MediaPipe_Pose`, `LaPa_106`). |
| `pose.tracked_points` | array[string] or `$ref` | yes | The ordered list of keypoint names that the model outputs. The i-th name is the i-th model output index. |
| `pose.connections` | array[Skeleton] or `$ref` | yes | The named skeletons. Each skeleton joins `tracked_points` into a different skeleton. |
| `pose.derived_points` | object | no | An optional map of derived point name → derivation. The `connections` edges can reference these points. |
| `pose.canonical_mapping` | object or `$ref` | no | It maps model keypoint names onto the canonical (VRM 1.0) skeleton (see [Canonical skeleton](canonical-mapping.md#canonical-skeleton)). |
| `pose.decode` | object | yes | It sets how the host decodes raw model outputs into keypoints (see below). Required for all `pose_estimator` models. |

### `outputs` (pose)

The fields common to every output are in [Outputs](../common/outputs.md#fields).

Additional fields on pose output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint_axis` | int | conditional | The axis that holds the keypoints in a pose output. The default is `1` for `(N, K, …)` tensors (`simcc_x`/`simcc_y`/`simcc_z`/`heatmap`/`keypoints`). For `poses` `(B, I, K, …)`, the field is required and its value is `2`. |
| `keypoint_count` | int | no | The number of keypoints in a pose output. If the author sets this field, it must equal `len(tracked_points)`. If the author omits it, its value is `len(tracked_points)`. |

`poses` tensor layout: [Bottom-up pose](pose-bottom-up.md#fields).

### `pose.tracked_points`

This is the complete ordered list of the keypoint names that the model produces. The list is **always in the model's output order**. The i-th name corresponds to the i-th row of the keypoint output of the model. Each name must be unique within a sidecar. Write side-specific points literally (for example `right_hand_root`, `left_hand_root`). The keypoint count comes from this list. It is `len(tracked_points)`.

### `pose.connections`

Named skeletons join `tracked_points` entries. A sidecar can list more than one skeleton for the same keypoints. For example, an RTMW wholebody output can use an RTMPose skeleton or an OpenPose skeleton. The selected `connections` entry sets the skeleton. The first entry is the default when no skeleton is named.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.connections[].name` | string | yes | The skeleton name. It must be unique within the sidecar (for example `rtmpose_skeleton`, `openpose_skeleton`). |
| `pose.connections[].edges` | array[[name, name]] | yes | Edge pairs that join `tracked_points`/`derived_points` names. |

Both names in every edge must appear in `tracked_points` or `derived_points`.

### `pose.derived_points`

The host computes derived points from `tracked_points`. The `connections` edges can reference derived points (for example `neck` of OpenPose). Each entry uses the same forms as [`canonical_mapping`](canonical-mapping.md#posecanonical_mapping), including the `prefixes` / `[prefix]` expansion:

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `nose_dup: "nose"` | The derived point is the tracker keypoint with that name. |
| mean | `neck: ["left_shoulder", "right_shoulder"]` | The derived point is the unweighted mean of the listed keypoints. |
| weighted | `mid_hip: {left_hip: 0.5, right_hip: 0.5}` | The derived point is the weighted sum, with the weights normalised. |

As with `canonical_mapping`, a `prefixes` list expands one entry to both sides. The prefix applies to the derived name and to each source. With `prefixes: [right_hand_, left_hand_]`, `[prefix]palm_center: ["root", "thumb1", "forefinger1"]` produces `right_hand_palm_center = mean(right_hand_root, right_hand_thumb1, right_hand_forefinger1)` and `left_hand_palm_center = mean(left_hand_root, left_hand_thumb1, left_hand_forefinger1)`. An entry without `[prefix]` is literal.

### `pose.decode`

This field declares how the raw output tensors of the model become keypoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.method` | enum | yes | The value is `simcc`, `heatmap` or `coordinate`. |
| `pose.decode.is_3d` | bool | no | The default is `false`. When `true`, the model emits a third coordinate. Its form is one of these: a `simcc_z` output (simcc), `(N, K, 3)` coordinates (`coordinate`), a `poses` tensor `(B, I, K, 4)` or a `z` packed component (bottom-up `coordinate`). 3D `heatmap` is **not supported**. |
| `pose.decode.depth_unit` | enum | required when `is_3d: true` | The unit of the root-relative depth coordinate: `m` (RTMW3D), `mm` or `pixel` (MediaPipe, scaled by the image width). |

Method-specific fields: [`pose.decode.coordinate_scale`](pose-decode-coordinate.md#fields), [`pose.decode.depth_range`](pose-decode-simcc.md#fields).

Decode methods:

- [SimCC decode](pose-decode-simcc.md#behaviour)
- [Heatmap decode](pose-decode-heatmap.md#behaviour)
- [Coordinate decode](pose-decode-coordinate.md#behaviour)

#### Shape key

- `N` — the batch size (person crops for top-down models).
- `B`, `I` — the batch axis and the instance axis of a bottom-up `poses` tensor. `I` equals the detection row count `Q`.
- `K` — the number of keypoints (`len(tracked_points)`).
- `H`, `W` — the spatial height and width of the output tensor.
- `X_bins`, `Y_bins` — the SIMCC x and y bin counts. The host reads them from the output tensors. The bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins`.
- `Z_bins` — the SIMCC depth bin count (`is_3d: true` only). The bins span `pose.decode.depth_range` linearly.
- For `is_3d: true`, the third coordinate is root-relative depth (RTMW3D), in `depth_unit`. Note: for 3D single-person keypoints, `(N, K, 3)` is `x, y, z`. For bottom-up `poses`, `(B, I, K, 3)` is `x, y, score`. For 3D bottom-up `poses`, `(B, I, K, 4)` is `x, y, z, score`.

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.schema-1` The sidecar must declare `pose` (with `estimator_type` and `requires_object_detector`), `pose.decode`, `pose.tracked_points` and `pose.connections`.
- [ ] `V-post.pose.schema-2` `pose.requires_object_detector` must be a boolean. It must be consistent with `pose.estimator_type`. It must be `true` for `top_down_single_person`/`top_down_multi_person`. It must be `false` for `bottom_up`.
- [ ] `V-post.pose.schema-3` `pose.estimator_type` must be one of `top_down_single_person`, `top_down_multi_person` or `bottom_up`. `pose.decode.method` must be one of `simcc`, `heatmap` or `coordinate`.
- [ ] `V-post.pose.schema-4` The names in `pose.tracked_points` must be unique.
- [ ] `V-post.pose.schema-5` Every `pose.connections[].edges` endpoint must appear in `pose.tracked_points` or `pose.derived_points`. The `pose.connections[].name` values must be unique.
- [ ] `V-post.pose.schema-6` The names in `pose.derived_points` must be unique. Each derivation must be a string (passthrough), a list of names (mean) or a name→number map (weighted). Every referenced source name must appear in `pose.tracked_points`.
- [ ] `V-post.pose.schema-7` A `simcc` decoder must declare exactly one `simcc_x` output and exactly one `simcc_y` output. It must declare one `simcc_z` output if and only if `is_3d: true`. A `heatmap` decoder must declare exactly one output with `semantic: heatmap`. A `coordinate` decoder must declare exactly one `keypoints` output (single-person). For a `bottom_up` model, this decoder must instead declare one primary detection output. It must also declare either one `poses` output, or `packed_keypoints` on the `detections` output. It must not declare both.
- [ ] `V-post.pose.schema-8` If the author sets `keypoint_count` on a pose output, it must equal `len(pose.tracked_points)`.
- [ ] `V-post.pose.schema-9` If `pose.decode.is_3d` is present, it must be a boolean. When `true`, `pose.decode.depth_unit` must be present and must be one of `m`, `mm` or `pixel`. `depth_unit` and `depth_range` must not be present unless `is_3d: true`.

See also [Affine person crop](../pre/resize-affine-person-crop.md#validation-rules), [Canonical mapping](canonical-mapping.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Implementer guidance

- Take the keypoint count from `len(tracked_points)` or `keypoint_count`, not from the ONNX shape. The keypoint axis of the real RTMW-M graph is symbolic (`[1, symbolic, 384]`). (OpenMMLab-Exporter `rtmw/contract.py:12-13`, 68a6c6d; `notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-28`, c85abf7)
- No exporter checks the third channel of the RTMO `[B, Q, 17, 3]` poses tensor. The probe of OpenMMLab-Exporter compares x and y only (`kpts[:, :, :2]`). The reading `(x, y, score)` comes from the spec, not from a measurement. The spec states the activation of the keypoint scores only for `packed_keypoints` ([spec defects](../../../notes/decisions/README.md#open-work), item on facts that a host needs). (OpenMMLab-Exporter `notes/decisions/scripts/rtmo_sidecar_probe.py:97-102`, 38ed76f)
- The YOLO26-pose graph applies the sigmoid to the keypoint score inside the graph (the third value of each keypoint). (ultralytics 8.4.184 `nn/modules/head.py:765-777`, installed copy in the Ultralytics-Exporter `.venv`)

## Authoring guidance

## Examples

```yaml
pose:
  estimator_type: top_down_single_person
  requires_object_detector: true
  tracked_points:
    - nose
    - left_shoulder
    - right_shoulder
    # ...
  derived_points:
    neck: [left_shoulder, right_shoulder]
  connections:
    - name: rtmpose_skeleton
      edges:
        - [nose, left_shoulder]
        - [left_shoulder, right_shoulder]
        # ...
    - name: openpose_skeleton
      edges:
        - [nose, neck]
        - [neck, left_shoulder]
        # ...
  # $ref paths resolve relative to this sidecar's directory.
  canonical_mapping: {$ref: ../../rtmpose/body/rtmpose_body_to_canonical_mapping.yaml}
  decode:
    method: simcc
```
