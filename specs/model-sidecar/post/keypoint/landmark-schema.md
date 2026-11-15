---
id: post.keypoint.landmark_schema
title: Landmark schema
kind: schema
selectors:
  - role=keypoint_detector
implemented_by:
  validate: missing
  load: missing
external_impl: []
tests: []
vectors: null
status: {spec: draft, validate: missing, load: missing}
---

# Landmark schema

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A landmark schema names the points of one keypoint convention, in output order, and puts them in groups. One YAML file holds one schema. The registry is the set of these files. Each keypoint sidecar names one registered schema in `keypoint.landmark_schema` ([Keypoint schema](schema.md#fields)). A schema file can also hold the canonical mapping of the convention ([Canonical mapping](canonical-mapping.md#fields)) ([ADR-23F5](../../../../decisions/entries/23F5-landmark-schema-registry.md)).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | The schema name, for example `COCO_WholeBody`. It is the file name without `.yaml`. It matches `^[A-Za-z][A-Za-z0-9_]*$`. |
| `source` | string | yes | The document that defines the convention: a URL with a commit, or a URL and the date that you read it. |
| `groups` | array[Group] | yes | The groups, in output order. |
| `groups[].name` | string | yes | The group name. It matches `^[a-z][a-z0-9_-]*$`, the name form of the pipeline spec. Use a shared group name when it fits: `body`, `feet`, `face`, `left_hand` or `right_hand`. The list is open. A group of face points has the name `face`. |
| `groups[].points` | array[string] | yes | The point names of the group, in output order. |
| `canonical_mapping` | object | no | The canonical mapping of the convention ([Canonical mapping](canonical-mapping.md#fields)). A schema of a face has none. |

The point names of a schema are the `points` of its groups, in the order of the groups. Group `k` holds the points from the sum of the counts of groups 0 to `k - 1`. The point names follow `V-post.keypoint.landmark_schema-3`. The field has the name `groups` because the overlay uses `parts` for another concept ([Overlay](overlay.md#fields)).

## Behaviour

1. **Registry folders.** The registry reads each file `*.yaml` in the branch `landmark_schemas/` of two sidecar roots: the package root and the user root of the catalog ([Storage layout](../../format/file-layout.md#storage-layout)). The registry reads no subfolder.
2. **Lookup.** A schema is found by its `name`. A name that no file of the registry holds is an error. The error names the schema. A name in two files is an error. The error names both paths (`V-post.keypoint.landmark_schema-4`).
3. **Sidecar load.** The load of a keypoint sidecar finds the schema that `keypoint.landmark_schema` names, and checks `V-post.keypoint.schema-10` and `V-post.keypoint.schema-11` ([Keypoint schema](schema.md#validation-rules)). Thus the i-th keypoint of the model is in the group that holds the i-th point of the schema. The sidecar keeps `point_names` and `skeletons`.
4. **Canonical mappings.** The registry holds the canonical mappings. A sidecar has no canonical mapping ([Canonical mapping](canonical-mapping.md#behaviour)).
5. **New schemas.** A model with a convention that the registry does not hold brings a new schema file, with its canonical mapping, in its `model` bundle ([Payload](../../model-addition-workflow/hand-over.md#payload)).

## Validation rules

### Schema file

- [ ] `V-post.keypoint.landmark_schema-1` A schema file must have the keys `name`, `source` and `groups`. It can have `canonical_mapping`. It must have no other key and must not repeat a key in a mapping. `name` must match `^[A-Za-z][A-Za-z0-9_]*$` and must equal the file name without `.yaml`. `source` must be a non-empty string.
- [ ] `V-post.keypoint.landmark_schema-2` `groups` must be a non-empty list. Each group must have exactly the keys `name` and `points`. Each group name must match `^[a-z][a-z0-9_-]*$` and must be unique in the file. `points` must be a non-empty list of strings.
- [ ] `V-post.keypoint.landmark_schema-3` Each point name must be unique in the file. It must not contain `/` or a whitespace character.
- [ ] `V-post.keypoint.landmark_schema-4` Two files of the registry must not have the same `name`.

See also [Canonical mapping](canonical-mapping.md#validation-rules) and [Keypoint schema](schema.md#validation-rules).

## Implementer guidance

- `tools/tests/test_landmark_schemas.py` checks each package file against `V-post.keypoint.landmark_schema-1` to `-3` and `V-post.keypoint.canonical_mapping-1`, and each keypoint example against `V-post.keypoint.schema-10` and `-11`. The host checks `-4` at load, because it needs the user root. (skellytracker `tools/tests/test_landmark_schemas.py`)

## Authoring guidance

- `COCO_WholeBody` follows the keypoint order of RTMW: 0-16 body, 17-22 feet, 23-90 face, 91-111 left hand and 112-132 right hand. Its groups are `body` (17), `feet` (6), `face` (68), `left_hand` (21) and `right_hand` (21), as `keypoints`, `foot_kpts`, `face_kpts`, `lefthand_kpts` and `righthand_kpts` of the COCO-WholeBody data format. The point names (`face-0`, `left_hand_root`, `left_thumb1`) are those of the exporter list, not of the data format. (OpenMMLab-Exporter [`rtmw/keypoints.py:12-146`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/keypoints.py#L12-L146); COCO-WholeBody [`data_format.md`](https://github.com/jin-s13/COCO-WholeBody/blob/adc36dab42cbd52480892ba608df85423324ca57/data_format.md))

## Examples

```yaml
name: COCO_WholeBody
source: https://github.com/jin-s13/COCO-WholeBody/blob/adc36dab42cbd52480892ba608df85423324ca57/data_format.md
groups:
  - name: body
    points: [nose, left_eye, right_eye]   # ... 17 points
  - name: feet
    points: [left_big_toe, left_small_toe, left_heel, right_big_toe, right_small_toe, right_heel]
  # face (68), left_hand (21), right_hand (21)
canonical_mapping:
  body:
    nose: nose
    left_big_toe: left_big_toe
    hips_center: [left_hip, right_hip]
```
