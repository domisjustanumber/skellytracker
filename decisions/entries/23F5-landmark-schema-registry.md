# 23F5 — Landmark schema registry: one schema file for each keypoint convention, with its groups and its canonical mapping

**Status:** absorbed into [`landmark-schema.md#landmark-schema`](../../specs/model-sidecar/post/keypoint/landmark-schema.md#landmark-schema), [`file-layout.md#storage-layout`](../../specs/model-sidecar/format/file-layout.md#storage-layout), [`canonical-mapping.md#fields`](../../specs/model-sidecar/post/keypoint/canonical-mapping.md#fields), [`canonical-mapping.md#behaviour`](../../specs/model-sidecar/post/keypoint/canonical-mapping.md#behaviour), [`canonical-mapping.md#validation-rules`](../../specs/model-sidecar/post/keypoint/canonical-mapping.md#validation-rules), [`schema.md#fields`](../../specs/model-sidecar/post/keypoint/schema.md#fields), [`schema.md#validation-rules`](../../specs/model-sidecar/post/keypoint/schema.md#validation-rules), [`hand-over.md#payload`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload), [`model-intake.md#model-intake-template`](../../specs/model-sidecar/templates/model-intake.md#model-intake-template), [`author-sidecar/SKILL.md#inputs`](../../.claude/skills/author-sidecar/SKILL.md#inputs), [`test_landmark_schemas.py`](../../tools/tests/test_landmark_schemas.py), 2026-11-15 (user, design review 2026-11-13; PR: pending).

## Decision

1. **Registry.** A landmark schema is one YAML file `<name>.yaml` in the storage-layout branch
   `landmark_schemas/` of the package root `skellytracker/core/model_zoo` or of the user root of
   the catalog. No other sidecar root has a registry folder. It has `name`, `source`, `groups` (each a `name` and its ordered `points`) and an
   optional `canonical_mapping`. The sidecar section `post.keypoint.landmark_schema` gives the
   format. A doc test checks each package file. The first file is `COCO_WholeBody.yaml`. The other
   schema files come with stage 2.2 of the implementation plan.
2. **Groups.** The shared group names are `body`, `feet`, `face`, `left_hand` and `right_hand`. The
   list is open. The feet are a group of their own. `COCO_WholeBody` has `body` (17), `feet` (6),
   `face` (68), `left_hand` (21) and `right_hand` (21), as `keypoints`, `foot_kpts`, `face_kpts`,
   `lefthand_kpts` and `righthand_kpts` of the COCO-WholeBody data format. The field name is
   `groups`.
3. **Sidecar.** `keypoint.landmark_schema` is required and names a registered schema. A name that
   the registry does not hold is an error. `keypoint.point_names` must equal the point names of the
   schema, in order. A sidecar keeps `point_names` and its `skeletons`. A point name must not
   contain `/` or whitespace: the sidecar rule, the registry loader and the pipeline load refuse it.
4. **Canonical mapping.** The `canonical_mapping` of the schema file replaces the sidecar field
   `keypoint.canonical_mapping`, which leaves the sidecar spec. `post.keypoint.canonical_mapping`
   keeps its ID and describes the mapping of a schema file. Each key is a region: a group name of
   the file. A source can be a point of each group of the file. The file has no `prefixes`. A face
   schema has no mapping: a group of face points has the name `face`, and `face` is never a region.
   A face group passes through with its schema name as its label. There are
   no canonical face names.
5. **Missing rule.** A computed canonical point follows the rule of `keypoint.derived_points`: it is
   missing when one or more sources are missing, and its score is the minimum of the scores of its
   sources. A passthrough keeps the score of its source. This changes the rule "`canonical_mapping`
   keeps its rule for present weights" of [ADR-88WQ](88WQ-sidecar-vocabulary.md) item 6.
6. **New schemas.** A model with a convention that the registry does not hold brings the schema
   file, with its canonical mapping, in its `model` bundle. The exporter writes it. Row K11 of the
   model intake is required: a registered name, or `new` and the source. Row K9 goes. This reverses
   the plan text "skellytracker work, not exporter work" of stage 2.2.
7. **MediaPipe.** This changes item 5 of
   [ADR-0XW9](0XW9-entry-points-layout-guard-test-and-session-code.md): the canonical mappings of
   MediaPipe move to schema files of the registry. The point-name YAML files and the connections
   stay at `core/detectors/keypoint_detectors/mediapipe/`.

## Reason

- The user decided each item in the design review of the pipeline and sidecar specs on 2026-11-13.
- Many models share one convention. One file gives each of them the same groups and the same
  canonical mapping. No exporter wrote `keypoint.canonical_mapping`, and a copy in each sidecar can
  drift.
- The COCO-WholeBody data format keeps the foot points apart from the 17 body points, and RTMW gives
  them at 17-22.
- One missing rule for each computed point. The old rule divided by the present weights, so a
  canonical point moved toward the sources that stayed when one source was missing.
- `face_0000` is a different point in iBUG 300-W, `LaPa_106` and the 478 MediaPipe points, so no
  canonical face name fits each face model.
- The exporter reads the upstream definition of the convention for the intake, so it can write the
  schema file.
- `parts` is the word of `keypoint.overlay.parts`. [ADR-88WQ](88WQ-sidecar-vocabulary.md) item 4
  makes `group` the body-region word.

## Alternatives rejected

- **Keep `keypoint.canonical_mapping` in each sidecar.** Each sidecar of one convention then repeats
  one mapping.
- **A free `landmark_schema` string.** A pipeline cannot then find the groups of a model.
- **Names from the old package file `coco133_tracked_points.yaml`.** Its face and hand names differ
  from the export, so the reference example would need a re-export.
