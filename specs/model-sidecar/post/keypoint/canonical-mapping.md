---
id: post.keypoint.canonical_mapping
title: Canonical mapping
kind: schema
selectors:
  - role=keypoint_detector
implemented_by:
  validate: skellytracker/core/model_spec/landmark_schemas.py::check_landmark_schema
  load: missing
external_impl: []
tests: [skellytracker/tests/model_spec/test_loader.py]
vectors: null
status: {spec: stable, validate: implemented, load: missing}
---

# Canonical mapping

## Fields

### `canonical_mapping`

The key `canonical_mapping` of a [landmark schema file](landmark-schema.md#fields) maps the points of the schema onto the freemocap **canonical skeleton** ([Canonical skeleton](#canonical-skeleton)). A sidecar has no canonical mapping ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)). Each key of `canonical_mapping` is a **region**: a group name of the same file. The value of a region maps each canonical point name to its source, in one of the three forms of [`keypoint.derived_points`](schema.md#keypointderived_points):

| Form | YAML | Meaning |
|------|------|---------|
| passthrough | `wrist: left_hand_root` | The canonical point is the point with that name. |
| mean | `hips_center: [left_hip, right_hip]` | The canonical point is the unweighted mean of the listed points. |
| weighted | `head_center: {left_ear: 0.5, right_ear: 0.5}` | The canonical point is the weighted sum of the listed points. The weights sum to 1. |

A source is a point name of the file, in any group. For example, the region `body` of `COCO_WholeBody` reads the toes of the group `feet`. A canonical point name contains no `/` and no whitespace. The file has no `prefixes` and no `[prefix]` form: each region names its own sources. A schema of a face has no `canonical_mapping` ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)).

## Behaviour

1. **Canonical points.** The canonical form of the points of one schema has, for each region, one canonical point for each entry, in the order of the entries. Its name is `<region>/<canonical point name>`. A passthrough keeps the point and its score. A mean or a weighted point uses the rule of [`keypoint.derived_points`](schema.md#keypointderived_points): it is missing when one or more of its sources are missing, and its score is the minimum of the scores of its sources ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)). This rule replaces the rule that dropped a missing source.
2. **Region names.** A region takes the name that its group has in the result. The pipeline spec gives the group of a schema with one group the name of its node or of its merge slot ([Graph](../../../pipeline/graph.md#behaviour) item 7). Thus the region of a one-hand schema gives `left_hand/wrist` from a group `left_hand`, and `right_hand/wrist` from a group `right_hand`: the group name gives the side ([ADR-4MP6](../../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)).
3. **Passthrough groups.** A group that no region reads passes through. Its points keep their names `<group>/<point>`, their positions and their scores. The group keeps its schema name as its label. A face group passes through: there are no canonical face names, because `face_0000` is a different point in iBUG 300-W, `LaPa_106` and the 478 MediaPipe points ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)).
4. **Order.** The canonical points follow the order of the groups: the points of each region at the place of its group, and each passthrough group at its place. A group that a region reads and that is not a region gives no canonical point, for example `feet` of `COCO_WholeBody`.

### Canonical skeleton

The canonical skeleton is the **VRM 1.0** humanoid skeleton. Every tracker maps onto this skeleton. These are its humanoid bones (per [`humanoid.md`](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/humanoid.md)):

| Bone set | Bones |
|-------|-------|
| torso | `hips`, `spine`, `chest`, `upperChest`, `neck` |
| head | `head`, `leftEye`, `rightEye`, `jaw` |
| legs | `leftUpperLeg`, `leftLowerLeg`, `leftFoot`, `leftToes`, `rightUpperLeg`, `rightLowerLeg`, `rightFoot`, `rightToes` |
| arms | `leftShoulder`, `leftUpperArm`, `leftLowerArm`, `leftHand`, `rightShoulder`, `rightUpperArm`, `rightLowerArm`, `rightHand` |
| fingers | `leftThumbMetacarpal`…`leftLittleDistal`, `rightThumbMetacarpal`…`rightLittleDistal` |

### Canonical names

The schema files of the registry hold the canonical mappings. `COCO_WholeBody.yaml` in `skellytracker/core/model_zoo/landmark_schemas/` is the worked example. These are the current canonical point names of each region:

| Region | Canonical point names |
|--------|-----------------------|
| body | COCO-WholeBody (`nose`, `left_shoulder`, `left_big_toe`, …) plus the computed points `head_center`, `neck_center`, `trunk_center`, `hips_center` |
| a hand (`left_hand`, `right_hand`) | MediaPipe Hand (`wrist`, `thumb_cmc`, `pinky_tip`, …) |

> **Name migration (current → VRM 1.0).** The names in this table are the **current** canonical landmark conventions that the reference detectors use. The names will change to the VRM 1.0 humanoid bones listed in [Canonical skeleton](#canonical-skeleton) (`hips`, `spine`, …, `leftHand`, `rightHand`, plus the finger bones). Until the names change, the canonical point names of a region use these current names. After the names change, they must use the VRM 1.0 names.

## Validation rules

### Schema file

- [ ] `V-post.keypoint.canonical_mapping-1` Each key of `canonical_mapping` must be a group name of the file, and must not be `face`. Each canonical point name must not contain `/` or a whitespace character. Each source must be a string (passthrough), a list of one or more names (mean) or a name→number map whose numbers sum to 1, within an absolute tolerance of `1e-6` (weighted). Each name of a source must be a point name of the file ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)).

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- The `point_names` of the MediaPipe hand model (`wrist`, `thumb_cmc` to `pinky_tip`) equal the canonical hand names, so a passthrough map fits. The hand mapping of skellytracker is an identity map. (Qualcomm-Exporter `qai_sidecar.py:15-37`, commit a095041a5e9450df18637596fbaf6409f79e9fc6 on no branch (secondary); skellytracker `skellytracker/core/detectors/keypoint_detectors/mediapipe/hands/mediapipe_hand_to_canonical_mapping.yaml`)
- The MediaPipe face names `face_0000` to `face_0467` use the same name pattern as the `LaPa_106` face (`face_0000` and up) with different meanings, so no canonical face name fits each face model ([Behaviour](#behaviour) item 3). (Qualcomm-Exporter [`qai_sidecar.py:15`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L15))

## Examples

```yaml
canonical_mapping:
  body:
    nose: nose
    left_big_toe: left_big_toe        # a point of the group feet
    hips_center: [left_hip, right_hip]
  left_hand:
    wrist: left_hand_root
    thumb_cmc: left_thumb1
```
