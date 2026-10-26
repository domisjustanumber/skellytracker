---
id: post.pose.canonical_mapping
title: Canonical mapping
kind: schema
since: v2024.09.1019
changed_in: []
selectors:
  - pose.canonical_mapping
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseSpec._check_pose  # partial: a source may be a derived point; duplicate keys are not detected
  load: skellytracker/core/io/tracker_mapping.py::TrackerMapping  # no skellytracker test covers this class
external_impl: []
tests:
  - skellytracker/tests/sidecar/test_model_validation.py
  - skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py
  - skellytracker/tests/sidecar/test_rtmpose_hand_sidecar.py
  - skellytracker/tests/sidecar/test_rtmw_sidecar.py
vectors: null
status: {spec: stable, validate: partial, load: implemented}
---

# Canonical mapping

## Fields

### `pose.canonical_mapping`

This field maps the `tracked_points` of the model onto the freemocap **canonical skeleton**. The canonical skeleton is the [VRM 1.0](https://github.com/vrm-c/vrm-specification/tree/master/specification/VRMC_vrm-1.0) humanoid skeleton (see [Canonical skeleton](#canonical-skeleton)). Each entry maps a **canonical** landmark name to its tracker source. The key is the canonical landmark. The value names the tracker keypoint or keypoints that produce it. This field accepts three mapping forms. They mirror `TrackerMapping` in `skellytracker/core/io/tracker_mapping.py`:

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `left_elbow: "left_elbow"` | The canonical landmark is the tracker keypoint with that name. |
| mean | `hips_center: ["left_hip", "right_hip"]` | The canonical landmark is the unweighted mean of the listed keypoints. |
| weighted | `head_center: {left_ear: 0.5, right_ear: 0.5}` | The canonical landmark is the weighted sum, normalised by the sum of the weights of the keypoints that are actually present. |

A `prefixes` list makes one entry apply to multiple sides:

```yaml
canonical_mapping:
  prefixes: [right_hand_, left_hand_]
  "[prefix]wrist": "root"
  "[prefix]ring_finger_tip": "ring_finger4"
```

`[prefix]` keys must be YAML-quoted. An unquoted leading `[` opens a flow sequence. A flow sequence is a parse error as a block-mapping key (see `rtmw/wholebody/rtmw_wholebody_to_canonical_mapping.yaml`).

## Behaviour

For each `p` in `prefixes`, the entry `[prefix]X: "Y"` expands to canonical `pX` = tracker `pY`. For example, `[prefix]ring_finger_tip: "ring_finger4"` produces both `right_hand_ring_finger_tip = right_hand_ring_finger4` and `left_hand_ring_finger_tip = left_hand_ring_finger4`. An entry without `[prefix]` is literal.

**Missing-keypoint semantics.** The mapping produces a canonical landmark only when its tracker source is present. If the named keypoint of a passthrough is missing, the mapping omits the landmark. The mean and weighted forms drop the missing keypoints. The mapping normalises a weighted sum by the sum of the weights of the *present* keypoints. It does not use the declared total. This matches `TrackerMapping.apply()`.

Single-part canonical names have no prefix (`wrist`, `thumb_cmc`). Whole-body canonical skeletons with two hands use `prefixes` to produce prefixed names (`right_hand_wrist`, `left_hand_wrist`). `prefixes` apply only here in `canonical_mapping`. The author always writes `tracked_points` as a complete, literal list. Note the distinction: `prefixes` is a convenience for the author of a sidecar. `TrackerMapping` also accepts a runtime `prefix` that strips a prefix from tracker keypoint names before lookup. This lets one hand mapping apply to both `right_hand_*` and `left_hand_*` keypoints.

### Canonical skeleton

The canonical skeleton is the **VRM 1.0** humanoid skeleton. Every tracker maps onto this skeleton. These are its humanoid bones (per [`humanoid.md`](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/humanoid.md)):

| Group | Bones |
|-------|-------|
| torso | `hips`, `spine`, `chest`, `upperChest`, `neck` |
| head | `head`, `leftEye`, `rightEye`, `jaw` |
| legs | `leftUpperLeg`, `leftLowerLeg`, `leftFoot`, `leftToes`, `rightUpperLeg`, `rightLowerLeg`, `rightFoot`, `rightToes` |
| arms | `leftShoulder`, `leftUpperArm`, `leftLowerArm`, `leftHand`, `rightShoulder`, `rightUpperArm`, `rightLowerArm`, `rightHand` |
| fingers | `leftThumbMetacarpal`…`leftLittleDistal`, `rightThumbMetacarpal`…`rightLittleDistal` |

### Reference mappings in skellytracker

The existing keypoint detectors are the gold-standard reference for how to write `canonical_mapping`. Each detector has a tracker→canonical mapping YAML file beside it. `TrackerMapping` (`skellytracker/core/io/tracker_mapping.py`) applies these files:

- `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose_body_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/rtmpose/hand/rtmpose_hand_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_to_canonical_mapping.yaml`

These are the conventions that the detectors use for canonical landmark names:

| Region | Canonical names |
|--------|-----------------|
| body | COCO-WholeBody (`nose`, `left_shoulder`, `left_big_toe`, …) plus computed markers `head_center`, `neck_center`, `trunk_center`, `hips_center` |
| hand | MediaPipe Hand (`wrist`, `thumb_cmc`, `pinky_tip`, …) |
| face (standalone) | LaPa_106 (`face_0000`, …, 106 points) |
| face (wholebody) | iBUG 300-W 68-point (`face_0000`, …, `face_0067`) |

> **Name migration (current → VRM 1.0).** The names in this table are the **current** canonical landmark conventions that the reference detectors use. The names will change to the VRM 1.0 humanoid bones listed in [Canonical skeleton](#canonical-skeleton) (`hips`, `spine`, …, `leftHand`, `rightHand`, plus the finger bones). Until the names change, `canonical_mapping` keys use these current names. After the names change, they must use the VRM 1.0 names.

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.canonical_mapping-1` If `pose.canonical_mapping` is present, its keys must be unique. Each value must be a string (passthrough), a list of names (mean) or a name→number map (weighted). Every referenced source name must appear in `pose.tracked_points`.

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- No exporter writes `pose.canonical_mapping`. The `pose` blocks of OpenMMLab-Exporter and Ultralytics-Exporter hold only `estimator_type`, `requires_object_detector`, `landmark_schema`, `tracked_points`, `connections` and `decode`. Qualcomm-Exporter wrote none. The sidecar author adds the field. (OpenMMLab-Exporter `rtmw/sidecar.py:154-163`, eed3361; Ultralytics-Exporter `yolo_sidecar.py:515-528`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:287-303`, a095041)
- The `tracked_points` of the MediaPipe hand model (`wrist`, `thumb_cmc` to `pinky_tip`) equal the canonical hand names, so a passthrough map fits. The hand mapping of skellytracker is an identity map. (Qualcomm-Exporter `qai_sidecar.py:15-37`, a095041; skellytracker `skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_to_canonical_mapping.yaml`)
- The MediaPipe face names `face_0000` to `face_0467` use the same name pattern as the `LaPa_106` face (`face_0000` and up) with different meanings. A `LaPa_106` mapping does not apply to them. (Qualcomm-Exporter `qai_sidecar.py:15`, c7b9132; [canonical names](#reference-mappings-in-skellytracker))
