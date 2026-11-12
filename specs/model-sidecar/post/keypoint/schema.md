---
id: post.keypoint.schema
title: Keypoint schema
kind: schema
selectors:
  - role=keypoint_detector
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseSpec  # partial: the output check in SidecarModel._check_pose_output_shapes has no packed_keypoints case; keypoint_count is not checked on poses outputs; it forbids the key pose.geometry and reads the removed key pose.decode.is_3d (decisions/entries/90CE-minimal-sidecar-contract.md)
  load: skellytracker/core/sidecar/loader.py::load_sidecar  # partial: the detectors read the point names and the first skeleton only; the derived points are never computed
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

# Keypoint schema

## Fields

The `keypoint` block is required when `role` includes `keypoint_detector`. It declares these items:

- the keypoints that a model produces
- the skeleton or skeletons that join the keypoints
- how the keypoints map onto the canonical (VRM 1.0) skeleton
- how the host decodes raw outputs into keypoints

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint.estimator_type` | enum | yes | The value is `top_down_single_person`, `top_down_multi_person` or `bottom_up`. A top-down model sees one person in each crop (single-person outputs). The host makes each crop with `affine_person_crop` from a box or an ROI of an upstream node. A bottom-up model emits all persons in one pass (for example RTMO or YOLO26-pose). |
| `keypoint.geometry` | enum | yes | The output kind of the family: `2d` or `3d`. A catalog can filter models by it. With `3d`, the model emits a third coordinate, the root-relative depth in `keypoint.decode.depth_unit`. Its form is one of these: `(B, P, 3)` keypoints (`coordinate`), an `instance_keypoints` tensor `(B, I, P, 4)` or a `z` packed component (bottom-up `coordinate`). |
| `keypoint.landmark_schema` | string | no | The keypoint convention that the model uses (for example `COCO_WholeBody`, `COCO17`, `MediaPipe_Hand`, `MediaPipe_Pose`, `LaPa_106`). |
| `keypoint.point_names` | array[string] or `$ref` | yes | The ordered list of keypoint names that the model outputs. The i-th name is the i-th model output index. |
| `keypoint.skeletons` | array[Skeleton] or `$ref` | yes | The named skeletons. Each skeleton joins `point_names` into a different skeleton. |
| `keypoint.derived_points` | object | no | An optional map of derived point name → derivation. The skeleton edges can reference these points. |
| `keypoint.canonical_mapping` | object or `$ref` | no | It maps model keypoint names onto the canonical (VRM 1.0) skeleton (see [Canonical skeleton](canonical-mapping.md#canonical-skeleton)). |
| `keypoint.decode` | object | yes | It sets how the host decodes raw model outputs into keypoints (see below). Required for all `keypoint_detector` models. |
| `keypoint.overlay` | object | no | How a host draws the keypoints and a skeleton ([Overlay](overlay.md#fields)). |

### `outputs` (keypoint)

The fields common to every output are in [Outputs](../../common/outputs.md#fields).

Additional fields on keypoint output tensors:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint_axis` | int | conditional | The axis that holds the keypoints in a keypoint output. The default is `1` for `(B, P, …)` tensors (`simcc_x`/`simcc_y`/`keypoint_coordinates`). For `instance_keypoints` `(B, I, P, …)`, the field is required and its value is `2`. |
| `keypoint_count` | int | no | The number of keypoints in a keypoint output. If the author sets this field, it must equal `len(point_names)`. If the author omits it, its value is `len(point_names)`. |

`instance_keypoints` tensor layout: [Bottom-up keypoints](bottom-up.md#fields).

### `keypoint.point_names`

This is the complete ordered list of the keypoint names that the model produces. The list is **always in the model's output order**. The i-th name corresponds to the i-th row of the keypoint output of the model. Each name must be unique within a sidecar. Write side-specific points literally (for example `right_hand_root`, `left_hand_root`). The keypoint count comes from this list. It is `len(point_names)`.

### `keypoint.skeletons`

Named skeletons join `point_names` entries. A sidecar can list more than one skeleton for the same keypoints. For example, an RTMW wholebody output can use an RTMPose skeleton or an OpenPose skeleton. The selected `skeletons` entry sets the skeleton. The first entry is the default when no skeleton is named.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint.skeletons[].name` | string | yes | The skeleton name. It must be unique within the sidecar (for example `rtmpose_skeleton`, `openpose_skeleton`). |
| `keypoint.skeletons[].edges` | array[[name, name]] | yes | Edge pairs that join `point_names`/`derived_points` names. |

Both names in every edge must appear in `point_names` or `derived_points`.

### `keypoint.derived_points`

The host computes derived points from `point_names`. The skeleton edges can reference derived points (for example `neck` of OpenPose). Each entry has one of these forms:

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `nose_dup: "nose"` | The derived point is the keypoint with that name. |
| mean | `neck: ["left_shoulder", "right_shoulder"]` | The derived point is the unweighted mean of the listed keypoints. |
| weighted | `mid_hip: {left_hip: 0.5, right_hip: 0.5}` | The derived point is the weighted sum of the listed keypoints. The host uses the weights as given. The weights must sum to 1, within an absolute tolerance of `1e-6`. A weight can be negative. |

A derived point is missing when one or more of its source keypoints are missing ([Decoded keypoints](#decoded-keypoints)). The mean and the weighted forms do not drop a missing source. The score of a derived point is the minimum of the scores of its sources. This rule is different from the rule of [`canonical_mapping`](canonical-mapping.md#behaviour).

As in [`canonical_mapping`](canonical-mapping.md#keypointcanonical_mapping), a `prefixes` list expands one entry to both sides. The prefix applies to the derived name and to each source. With `prefixes: [right_hand_, left_hand_]`, `[prefix]palm_center: ["root", "thumb1", "forefinger1"]` produces `right_hand_palm_center = mean(right_hand_root, right_hand_thumb1, right_hand_forefinger1)` and `left_hand_palm_center = mean(left_hand_root, left_hand_thumb1, left_hand_forefinger1)`. An entry without `[prefix]` is literal.

### `keypoint.decode`

This field declares how the raw output tensors of the model become keypoints.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keypoint.decode.method` | enum | yes | The value is `simcc` or `coordinate`. |
| `keypoint.decode.depth_unit` | enum | required when `keypoint.geometry: 3d` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)) | The unit of the root-relative depth coordinate: `m`, `mm` or `pixel` (MediaPipe, scaled by the image width). |

Method-specific field: [`keypoint.decode.coordinate_space`](decode-coordinate.md#fields).

Decode methods:

- [SimCC decode](decode-simcc.md#behaviour)
- [Coordinate decode](decode-coordinate.md#behaviour)

#### Shape key

- `B` — the batch axis (the person crops for a top-down model).
- `I` — the instance axis of a bottom-up `instance_keypoints` tensor. `I` equals the detection row count `Q`.
- `P` — the number of points (`len(point_names)`).
- `H`, `W` — the spatial height and width of the output tensor.
- `X_bins`, `Y_bins` — the SIMCC x and y bin counts. The host reads them from the output tensors. The bin→pixel scale is `input_width / X_bins` and `input_height / Y_bins`.
- For `keypoint.geometry: 3d`, the third coordinate is root-relative depth, in `depth_unit`. Note: for 3D single-person keypoints, `(B, P, 3)` is `x, y, z`. For bottom-up `instance_keypoints`, `(B, I, P, 3)` is `x, y, score`. For 3D bottom-up `instance_keypoints`, `(B, I, P, 4)` is `x, y, z, score`.

## Behaviour

### Decoded keypoints

Each decode method gives a score for each keypoint. Each decode method states the range of its score. A keypoint output with no score (`keypoint_coordinates`) gives the score `1.0` to each keypoint whose coordinates are all finite, and the score NaN to a keypoint with a NaN coordinate. After the decode and the unprojection, a keypoint with a score `<= 0` or a NaN score is missing. The host sets `x`, `y` and, for 3D, `z` of a missing keypoint to NaN and its score to `0`. A host compares the keypoint scores with its thresholds after this rule ([ADR-88WQ](../../../../decisions/entries/88WQ-sidecar-vocabulary.md)).

## Validation rules

### Keypoint (`keypoint_detector`)

- [ ] `V-post.keypoint.schema-1` The sidecar must declare `keypoint` (with `estimator_type` and `geometry`), `keypoint.decode`, `keypoint.point_names` and `keypoint.skeletons` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-post.keypoint.schema-3` `keypoint.estimator_type` must be one of `top_down_single_person`, `top_down_multi_person` or `bottom_up`. `keypoint.decode.method` must be `simcc` or `coordinate`.
- [ ] `V-post.keypoint.schema-4` The names in `keypoint.point_names` must be unique.
- [ ] `V-post.keypoint.schema-5` Every `keypoint.skeletons[].edges` endpoint must appear in `keypoint.point_names` or `keypoint.derived_points`. The `keypoint.skeletons[].name` values must be unique.
- [ ] `V-post.keypoint.schema-6` The names in `keypoint.derived_points` must be unique. Each derivation must be a string (passthrough), a list of names (mean) or a name→number map (weighted). The weights of a weighted derivation must sum to 1, within an absolute tolerance of `1e-6`. Every referenced source name must appear in `keypoint.point_names`.
- [ ] `V-post.keypoint.schema-7` A `simcc` decoder must declare exactly one `simcc_x` output and exactly one `simcc_y` output. It must have `keypoint.geometry: 2d`: the spec has no 3D SimCC decode ([ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)). A `coordinate` decoder must declare exactly one `keypoint_coordinates` output (single-person). For a `bottom_up` model, this decoder must instead declare one primary detection output. It must also declare either one `instance_keypoints` output, or `packed_keypoints` on the `packed_detections` output. It must not declare both ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-post.keypoint.schema-8` If the author sets `keypoint_count` on a keypoint output, it must equal `len(keypoint.point_names)`.
- [ ] `V-post.keypoint.schema-9` `keypoint.geometry` must be `2d` or `3d`. When it is `3d`, `keypoint.decode.depth_unit` must be present and must be one of `m`, `mm` or `pixel`. `depth_unit` must not be present unless `keypoint.geometry: 3d` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

See also [Affine person crop](../../pre/resize-affine-person-crop.md#validation-rules), [Canonical mapping](canonical-mapping.md#validation-rules) and [Bottom-up keypoints](bottom-up.md#validation-rules).

## Implementer guidance

- Take the keypoint count from `len(point_names)` or `keypoint_count`, not from the ONNX shape. The keypoint axis of the real RTMW-M graph is symbolic (`[1, symbolic, 384]`). (OpenMMLab-Exporter [`rtmw/contract.py:12-13`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/68a6c6d103a63d9df10668990d937abb23de73fb/rtmw/contract.py#L12-L13); [`notes/decisions/0019-rtmw-real-export-sidecar-contract.md:27-28`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0019-rtmw-real-export-sidecar-contract.md#L27-L28))
- No exporter checks the third channel of the RTMO `[B, Q, 17, 3]` `instance_keypoints` tensor. The probe of OpenMMLab-Exporter compares x and y only (`kpts[:, :, :2]`). The reading `(x, y, score)` and the activated score come from the spec, not from a measurement ([Bottom-up keypoints](bottom-up.md#fields)). (OpenMMLab-Exporter [`notes/decisions/scripts/rtmo_sidecar_probe.py:97-102`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/scripts/rtmo_sidecar_probe.py#L97-L102))
- The YOLO26-pose graph applies the sigmoid to the keypoint score inside the graph (the third value of each keypoint). (ultralytics 8.4.184 `nn/modules/head.py:765-777`, installed copy in the Ultralytics-Exporter `.venv`)
- Use the decoded keypoint arrays in `point_names` order. Do not reorder them in the detector. Compare the keypoints of a parity test by name, not by array position. ([ADR-0003](../../../../decisions/entries/0003-tracked-points-native-order.md))

## Authoring guidance

- RTMW: `estimator_type` is `top_down_single_person` and `landmark_schema` is `COCO_WholeBody`. `point_names` holds 133 names in the model output order: 0-16 body, 17-22 feet, 23-90 face (`face-0` to `face-67`), 91-111 left hand (from `left_hand_root`) and 112-132 right hand. `skeletons` is one skeleton `wholebody` with 65 edges. The edges are converted from index pairs to names. (OpenMMLab-Exporter [`rtmw/keypoints.py:1-8`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L1-L8), [`rtmw/keypoints.py:12-146`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L12-L146), [`rtmw/keypoints.py:148-217`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L148-L217) and [`rtmw/sidecar.py:154-163`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L154-L163))
- RTMO: `estimator_type` is `bottom_up` and `landmark_schema` is `COCO17`. `point_names` holds the 17 COCO keypoints in COCO order. `skeletons` is one skeleton `coco` with 19 edges. `num_keypoints=17` in the head config (line 467 of the m config) gives `keypoint_count` 17. (OpenMMLab-Exporter [`rtmo/sidecar.py:155-163`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L155-L163) and [`rtmo/keypoints.py:10-52`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/keypoints.py#L10-L52); [`mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py:467`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/6c494a0bcb48acc218b1edd3617b8621b35cc3f4/mmdeploy-convert/model_cfgs/rtmo-m_16xb16-600e_body7-640x640.py#L467))
- YOLO26-pose: `point_names` is the constant `COCO_17_LABELS`, in the same order as the ONNX metadata `kpt_names`. `landmark_schema` is `COCO17` and `estimator_type` is `bottom_up`. The exporter does not read `kpt_names` or `kpt_shape` `[17, 3]` from the graph. Compare the list with the graph metadata when you write a new file. (Ultralytics-Exporter [`yolo_sidecar.py:32-33`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L32-L33), [`yolo_sidecar.py:38-56`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L38-L56), [`yolo_sidecar.py:515-528`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L515-L528); `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, metadata `kpt_names` and `kpt_shape`, untracked, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)
- YOLO26-pose: `skeletons` is one hard-coded skeleton `coco_17` with 16 edges and no upstream key. The Ultralytics `Annotator` skeleton has 19 edges. It adds the eye-eye edge and the two ear-shoulder edges. (Ultralytics-Exporter [`yolo_sidecar.py:58-76`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L58-L76); ultralytics 8.4.184 `utils/plotting.py:351-371`, installed copy in the Ultralytics-Exporter `.venv`)
- MediaPipe landmark models (historical code of Qualcomm-Exporter): `role` is `[keypoint_detector]` and `estimator_type` is `top_down_single_person`. `landmark_schema` is `MediaPipe_FaceMesh` or `MediaPipe_Hand`. The one output is `{name: landmarks, semantic: keypoint_coordinates, keypoint_axis: 1, keypoint_count: 468 or 21, shape [B, P, 3]}`. (Qualcomm-Exporter [`qai_sidecar.py:230-262`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L230-L262) (face); `qai_sidecar.py:270-310`, commit a095041a5e9450df18637596fbaf6409f79e9fc6 on no branch (secondary) (hand and face))
- The `point_names` of the MediaPipe models came from constants of the exporter: 21 hand names from `wrist` to `pinky_tip` in landmark index order, and `face_0000` to `face_0467`. The `skeletons` came from the upstream index pairs (`HAND_LANDMARK_CONNECTIONS`, `FACE_LANDMARK_CONNECTIONS`), converted to name pairs, as one skeleton `<family>_skeleton`. (Qualcomm-Exporter `qai_sidecar.py:15-39, 130-180`, commit a095041a5e9450df18637596fbaf6409f79e9fc6 on no branch (secondary) (hand and face); [`qai_sidecar.py:15`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L15), [`qai_sidecar.py:97-137`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L97-L137) (face))
- The landmark wrapper of Qualcomm-Exporter keeps only `out[-1]`, the landmarks tensor. The ONNX file thus has no output for a face flag, a hand flag or a handedness, and a host cannot gate on presence. The output semantics of the spec are a closed set with no presence score and no handedness ([Outputs](../../common/outputs.md#fields)). (Qualcomm-Exporter [`qai_catalog.py:336-361`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_catalog.py#L336-L361))
- The MediaPipe hand landmark model is top-down, but its crop does not come from a detector box. The pipeline builds a rotated ROI from the wrist, index and pinky keypoints of a body pose. The spec ties `top_down_*` to `affine_person_crop` (V-pre.resize.affine_person_crop-2). (the untracked hand pipeline plan of MediaPipe-Exporter (secondary))

## Examples

```yaml
keypoint:
  estimator_type: top_down_single_person
  geometry: 2d
  point_names:
    - nose
    - left_shoulder
    - right_shoulder
    # ...
  derived_points:
    neck: [left_shoulder, right_shoulder]
  skeletons:
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
