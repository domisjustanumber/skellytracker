---
id: post.pose.schema
title: Pose schema
kind: schema
---

# Pose schema

## Fields

The pose output contract declares the keypoints a model produces, the skeleton(s) joining them, how they map onto the canonical (VRM 1.0) skeleton, and how raw outputs are decoded into keypoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.estimator_type` | enum | yes | `top_down_single_person`, `top_down_multi_person`, or `bottom_up`. Top-down models see one person per crop (single-person outputs); bottom-up models (e.g. RTMO, YOLO26-pose) emit all persons in one pass. |
| `pose.requires_object_detector` | bool | yes | `true` when the model consumes a person crop produced by an upstream detector (top-down models — the host warps each detection box via `affine_person_crop`); `false` when the model consumes the full image (bottom-up models). Must be consistent with `estimator_type`. |
| `pose.landmark_schema` | string | no | Keypoint convention the model uses (e.g. `COCO_WholeBody`, `COCO17`, `MediaPipe_Hand`, `MediaPipe_Pose`, `LaPa_106`). |
| `pose.tracked_points` | array[string] or `$ref` | yes | Ordered list of keypoint names the model outputs. The i-th name is the i-th model output index. |
| `pose.connections` | array[Skeleton] or `$ref` | yes | Named skeletons; each joins `tracked_points` into a different skeleton. |
| `pose.derived_points` | object | no | Optional map of derived point name → derivation. May be referenced by `connections` edges. |
| `pose.canonical_mapping` | object or `$ref` | no | Maps model keypoint names onto the canonical (VRM 1.0) skeleton (see [Canonical skeleton](canonical-mapping.md#canonical-skeleton)). |
| `pose.decode` | object | yes | How raw model outputs are decoded into keypoints (see below). Required for all `pose_estimator` models. |

### `outputs` (pose)

The fields common to every output are in [Outputs](../common/outputs.md#fields).

Additional fields on pose output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint_axis` | int | conditional | Axis holding the keypoints in a pose output. Default `1` for `(N, K, …)` tensors (`simcc_x`/`simcc_y`/`simcc_z`/`heatmap`/`keypoints`); required (`2`) for `poses` `(B, I, K, …)`. |
| `keypoint_count` | int | no | Number of keypoints in a pose output. When authored, must equal `len(tracked_points)`; when omitted, it is derived as `len(tracked_points)`. |

`poses` tensor layout: [Bottom-up pose](pose-bottom-up.md#fields).

### `pose.tracked_points`

The complete ordered list of keypoint names produced by the model, **always in the model's output order** — the i-th name corresponds to the i-th row of the model's keypoint output. Names must be unique within a sidecar; side-specific points are authored literally (e.g. `right_hand_root`, `left_hand_root`). The keypoint count is derived: `len(tracked_points)`.

### `pose.connections`

Named skeletons joining `tracked_points` entries. A sidecar may list more than one skeleton for the same keypoints — e.g. an RTMW wholebody output can be joined with an RTMPose skeleton or an OpenPose skeleton by selecting a different `connections` entry. The first entry is the default when no skeleton is named.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.connections[].name` | string | yes | Skeleton name, unique within the sidecar (e.g. `rtmpose_skeleton`, `openpose_skeleton`). |
| `pose.connections[].edges` | array[[name, name]] | yes | Edge pairs joining `tracked_points`/`derived_points` names. |

Both names in every edge must appear in `tracked_points` or `derived_points`.

### `pose.derived_points`

Derived points are computed from `tracked_points` and may be referenced by `connections` edges (e.g. OpenPose's `neck`). Each entry uses the same forms as [`canonical_mapping`](canonical-mapping.md#posecanonical_mapping), including the `prefixes` / `[prefix]` expansion:

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `nose_dup: "nose"` | derived = tracker keypoint at that name |
| mean | `neck: ["left_shoulder", "right_shoulder"]` | derived = unweighted mean of the listed keypoints |
| weighted | `mid_hip: {left_hip: 0.5, right_hip: 0.5}` | derived = weighted sum (weights normalised) |

Like `canonical_mapping`, a `prefixes` list expands one entry to both sides — the prefix applies to the derived name and to each source. With `prefixes: [right_hand_, left_hand_]`, `[prefix]palm_center: ["root", "thumb1", "forefinger1"]` produces `right_hand_palm_center = mean(right_hand_root, right_hand_thumb1, right_hand_forefinger1)` and `left_hand_palm_center = mean(left_hand_root, left_hand_thumb1, left_hand_forefinger1)`. Entries without `[prefix]` are literal.

### `pose.decode`

Declares how the model's raw output tensors become keypoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pose.decode.method` | enum | yes | `simcc`, `heatmap`, or `coordinate`. |
| `pose.decode.is_3d` | bool | no | Default `false`. When `true`, the model emits a third coordinate: a `simcc_z` output (simcc), `(N, K, 3)` coordinates (`coordinate`), a `poses` tensor `(B, I, K, 4)`, or a `z` packed component (bottom-up `coordinate`). 3D `heatmap` is **not supported**. |
| `pose.decode.depth_unit` | enum | required when `is_3d: true` | Unit of the root-relative depth coordinate: `m` (RTMW3D), `mm`, or `pixel` (MediaPipe, image-width-scaled). |

Method-specific fields: [`pose.decode.coordinate_scale`](pose-decode-coordinate.md#fields), [`pose.decode.depth_range`](pose-decode-simcc.md#fields).

Decode methods:

- [SimCC decode](pose-decode-simcc.md#behaviour)
- [Heatmap decode](pose-decode-heatmap.md#behaviour)
- [Coordinate decode](pose-decode-coordinate.md#behaviour)

#### Shape key

- `N` — batch size (person crops for top-down models).
- `B`, `I` — batch and instance axes of a bottom-up `poses` tensor; `I` equals the detection row count `Q`.
- `K` — number of keypoints (`len(tracked_points)`).
- `H`, `W` — spatial height and width of the output tensor.
- `X_bins`, `Y_bins` — SIMCC x/y bin counts, read from the output tensors; the bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins`.
- `Z_bins` — SIMCC depth bin count (`is_3d: true` only); bins span `pose.decode.depth_range` linearly.
- For `is_3d: true`, the third coordinate is root-relative depth (RTMW3D), in `depth_unit`. Note: `(N, K, 3)` is `x, y, z` for 3D single-person keypoints, `x, y, score` for bottom-up `poses` `(B, I, K, 3)`, and `(B, I, K, 4)` is `x, y, z, score` for 3D bottom-up `poses`.

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.schema-1` The sidecar declares `pose` (with `estimator_type` and `requires_object_detector`), `pose.decode`, `pose.tracked_points`, and `pose.connections`.
- [ ] `V-post.pose.schema-2` `pose.requires_object_detector` is a boolean and consistent with `pose.estimator_type`: `true` for `top_down_single_person`/`top_down_multi_person`, `false` for `bottom_up`.
- [ ] `V-post.pose.schema-3` `pose.estimator_type` is one of `top_down_single_person`, `top_down_multi_person`, `bottom_up`; `pose.decode.method` is one of `simcc`, `heatmap`, `coordinate`.
- [ ] `V-post.pose.schema-4` `pose.tracked_points` names are unique.
- [ ] `V-post.pose.schema-5` Every `pose.connections[].edges` endpoint appears in `pose.tracked_points` or `pose.derived_points`, and `pose.connections[].name` values are unique.
- [ ] `V-post.pose.schema-6` `pose.derived_points` names are unique; each derivation is a string (passthrough), a list of names (mean), or a name→number map (weighted), and every referenced source name appears in `pose.tracked_points`.
- [ ] `V-post.pose.schema-7` A `simcc` decoder declares exactly one `simcc_x` and one `simcc_y` output, plus one `simcc_z` output iff `is_3d: true`; `heatmap` declares exactly one output with `semantic: heatmap`; `coordinate` declares exactly one `keypoints` output (single-person), or — for `bottom_up` — one primary detection output plus either one `poses` output or `packed_keypoints` on the `detections` output (not both).
- [ ] `V-post.pose.schema-8` `keypoint_count` (when authored on a pose output) equals `len(pose.tracked_points)`.
- [ ] `V-post.pose.schema-9` `pose.decode.is_3d` (when present) is a boolean; when `true`, `pose.decode.depth_unit` is present and one of `m`, `mm`, `pixel`; `depth_unit` and `depth_range` are present only when `is_3d: true`.

See also [Affine person crop](../pre/resize-affine-person-crop.md#validation-rules), [Canonical mapping](canonical-mapping.md#validation-rules) and [Bottom-up pose](pose-bottom-up.md#validation-rules).

## Implementer guidance

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
