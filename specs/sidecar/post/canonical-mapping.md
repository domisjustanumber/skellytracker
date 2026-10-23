---
id: post.pose.canonical_mapping
title: Canonical mapping
kind: schema
---

# Canonical mapping

## Fields

### `pose.canonical_mapping`

Maps the model's `tracked_points` onto the freemocap **canonical skeleton** — the [VRM 1.0](https://github.com/vrm-c/vrm-specification/tree/master/specification/VRMC_vrm-1.0) humanoid skeleton (see [Canonical skeleton](#canonical-skeleton)). Each entry keys a **canonical** landmark name to its tracker source: the key is the canonical landmark, and the value names the tracker keypoint(s) that produce it. Three mapping forms are supported, mirroring `TrackerMapping` in `skellytracker/core/io/tracker_mapping.py`:

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `left_elbow: "left_elbow"` | canonical = tracker keypoint at that name |
| mean | `hips_center: ["left_hip", "right_hip"]` | canonical = unweighted mean of the listed keypoints |
| weighted | `head_center: {left_ear: 0.5, right_ear: 0.5}` | canonical = weighted sum, normalised by the sum of the weights of the keypoints that are actually present |

A `prefixes` list makes one entry apply to multiple sides:

```yaml
canonical_mapping:
  prefixes: [right_hand_, left_hand_]
  "[prefix]wrist": "root"
  "[prefix]ring_finger_tip": "ring_finger4"
```

`[prefix]` keys must be YAML-quoted: an unquoted leading `[` opens a flow sequence, which is a parse error as a block-mapping key (see `rtmw/wholebody/rtmw_wholebody_to_canonical_mapping.yaml`).

## Behaviour

`[prefix]X: "Y"` expands, for each `p` in `prefixes`, to canonical `pX` = tracker `pY`. So `[prefix]ring_finger_tip: "ring_finger4"` produces both `right_hand_ring_finger_tip = right_hand_ring_finger4` and `left_hand_ring_finger_tip = left_hand_ring_finger4`. Entries without `[prefix]` are literal.

**Missing-keypoint semantics.** A canonical landmark is produced only when its tracker source is present: a passthrough whose named keypoint is missing is omitted, and mean/weighted forms drop missing keypoints — a weighted sum is normalised by the sum of the weights of the *present* keypoints (not the declared total). This matches `TrackerMapping.apply()`.

Single-part canonical names are unprefixed (`wrist`, `thumb_cmc`); whole-body canonical skeletons with two hands use `prefixes` to produce prefixed names (`right_hand_wrist`, `left_hand_wrist`). `prefixes` apply only here in `canonical_mapping` — `tracked_points` are always authored as a complete, literal list. Note the distinction: `prefixes` is a sidecar authoring convenience, whereas `TrackerMapping` also accepts a runtime `prefix` that strips a prefix from tracker keypoint names before lookup (used to apply one hand mapping to both `right_hand_*` and `left_hand_*` keypoints).

### Canonical skeleton

The canonical skeleton every tracker is mapped onto is the **VRM 1.0** humanoid skeleton. Its humanoid bones (per [`humanoid.md`](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/humanoid.md)) are:

| Group | Bones |
|-------|-------|
| torso | `hips`, `spine`, `chest`, `upperChest`, `neck` |
| head | `head`, `leftEye`, `rightEye`, `jaw` |
| legs | `leftUpperLeg`, `leftLowerLeg`, `leftFoot`, `leftToes`, `rightUpperLeg`, `rightLowerLeg`, `rightFoot`, `rightToes` |
| arms | `leftShoulder`, `leftUpperArm`, `leftLowerArm`, `leftHand`, `rightShoulder`, `rightUpperArm`, `rightLowerArm`, `rightHand` |
| fingers | `leftThumbMetacarpal`…`leftLittleDistal`, `rightThumbMetacarpal`…`rightLittleDistal` |

### Reference mappings in skellytracker

The gold-standard reference for authoring `canonical_mapping` is the existing keypoint detectors. Each carries a tracker→canonical mapping YAML beside it, applied by `TrackerMapping` (`skellytracker/core/io/tracker_mapping.py`):

- `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose_body_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/rtmpose/hand/rtmpose_hand_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/mediapipe/body/mediapipe_body_to_canonical_mapping.yaml`
- `skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_to_canonical_mapping.yaml`

Their canonical landmark naming conventions:

| Region | Canonical names |
|--------|-----------------|
| body | COCO-WholeBody (`nose`, `left_shoulder`, `left_big_toe`, …) plus computed markers `head_center`, `neck_center`, `trunk_center`, `hips_center` |
| hand | MediaPipe Hand (`wrist`, `thumb_cmc`, `pinky_tip`, …) |
| face (standalone) | LaPa_106 (`face_0000`, …, 106 points) |
| face (wholebody) | iBUG 300-W 68-point (`face_0000`, …, `face_0067`) |

> **Name migration (current → VRM 1.0).** The names in this table are the **current** canonical landmark conventions used by the reference detectors. They will be renamed to the VRM 1.0 humanoid bones listed in [Canonical skeleton](#canonical-skeleton) (`hips`, `spine`, …, `leftHand`, `rightHand`, plus the finger bones). Until the rename lands, `canonical_mapping` keys use these current names; after the rename, they must use the VRM 1.0 names.

## Validation rules

### Pose (`pose_estimator`)

- [ ] `V-post.pose.canonical_mapping-1` `pose.canonical_mapping` (when present) has unique keys; each value is a string (passthrough), a list of names (mean), or a name→number map (weighted), and every referenced source name appears in `pose.tracked_points`.

## Implementer guidance

## Authoring guidance
