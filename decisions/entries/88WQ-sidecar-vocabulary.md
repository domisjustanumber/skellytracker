# 88WQ — Sidecar vocabulary: `object` and `keypoint` blocks, the role `keypoint_detector`, and one name for each concept

**Status:** accepted, 2026-11-11 (user).

## Decision

The sidecar spec and the pipeline spec use one name for each concept. Spec version `2.0.0` is not
released, so the old names go, with no alias and no legacy reader.

1. **Roles and blocks.** The role `pose_estimator` becomes `keypoint_detector`. `object_detector`
   stays. The detection fields go into an `object:` block: `object.decode` and `object.classes`.
   `pose:` becomes `keypoint:`, with all its fields (`keypoint.decode`, `keypoint.geometry`,
   `keypoint.estimator_type`). `overlay` becomes `keypoint.overlay`. No decode block is shared.
2. **Layout.** The `post/` sections go into `post/object/` and `post/keypoint/`.
   `post/unprojection.md` stays. Section IDs, rule IDs and vector and reference file names follow:
   `post.det.*` becomes `post.object.*` and `post.pose.*` becomes `post.keypoint.*`. The changelog
   row gives the old-to-new ID map. Decided entries and frozen proposal records keep the old IDs.
3. **Classes.** `object.classes` is the ordered list of class names, in model index order. A `$ref`
   is allowed. Its length must equal the class count `C`. `object.decode.keep_classes` names the
   classes to keep. When it is omitted, the host keeps each row. `class_id_base`, `class_id_map`,
   `is_person_only` and `person_class_id` are removed. The `fields` column `class_id` becomes
   `class_index`.
4. **Names.** `score` for each model confidence (pipeline `visibility` and `confidence` go).
   `point_names` for the full ordered list (`tracked_points` and the pipeline `names` go); a param
   that selects points keeps `points`. `skeletons[]`, each with `name` and `edges` (`connections`
   goes). `overlay.parts` (`overlay.groups` goes). `expand_ratio` for each box multiplier
   (`roi_from_points.scale` goes; `redetect` gives `expand_ratio: 1.10` for `expansion_ratio: 0.05`).
   `box_space` and `coordinate_space` (from `box_scale` and `coordinate_scale`).
   `min_score` (from `confidence_threshold_default`); `nms.score_threshold` stays. Semantics
   `packed_detections`, `keypoint_coordinates` and `instance_keypoints` (from `detections`,
   `keypoints` and `poses`). `group` is the body-region word; the MediaPipe variants are
   `body`, `hand`, `face` and `holistic`. Pipeline `instance_source` (from the graph meaning of
   "root"), `port_type`, tap `action` and redetect `check` (from four meanings of `kind`).
   `previous_weight` (from `smooth_roi.alpha`). `size` is only the model size key.
5. **Letters.** One letter key for both specs: `B` batch, `Q` tensor rows, `I` instance rows,
   `P` points (`K` goes), `C` classes.
6. **Definitions.**
   - A decoded keypoint with score `<= 0` or NaN is missing: x and y are NaN and the score is 0.
     Each decode method states its score range. Pipeline thresholds are `>= 0`, with no upper bound.
   - `derived_points` is one definition, used by both specs. The weighted form uses the weights as
     given, and they must sum to 1. A negative weight is allowed. A derived point is missing when a
     source is missing. `canonical_mapping` keeps its rule for present weights.
   - The sidecar loader refuses duplicate YAML keys.
7. **Pipeline adoption.** The pipeline spec links to sidecar definitions and does not restate them.
   The pipeline `source` is the sidecar `{name, version}` mapping. Pipelines use the sidecar
   catalog key rules: the newest version wins, `<key>==<version>` pins, and `skellytracker` is
   reserved. The `detector` node param `decode` becomes `object_decode`. There is no
   `keypoint_decode` param until a keypoint field can be tuned. The `mediapipe_tasks` params are
   `min_detection_score`, `min_presence_score`, `min_tracking_score` and `size`.
8. **Landing.** Two examples change by forced edits. The four exporters regenerate their sidecars
   on their next export. skellytracker does not change their repos.

## Reason

- Reviews in this session found one concept under two to five names, and one name for two to
  five concepts: `connections`, `kind`, `score`/`visibility`/`confidence`, `class_id` before and
  after the mapping, the semantic `detections` as a raw tensor and as a decoded port value.
  Each one let two readers apply a different meaning.
- `pose_estimator` disagreed with the folders `keypoint_detectors/` and the package classes.
- The pipeline `detections` output has no class field. The four class fields only selected the rows
  to keep, with index arithmetic and `-1` sentinels. A sidecar could not say what it detects.
- A new name in `2.0.0` costs one regeneration. After the release, each rename is a major version.

## Consequences

- About 50 files of the sidecar spec change, with the tools, the vectors and the pipeline spec.
  The vector `expect` values do not change. The changelog fingerprint changes.
- The old package code under `skellytracker/` reads the old names. It does not change: it is
  replaced ([ADR-AMJ8](AMJ8-replace-package-onnx-detectors.md)).

## Alternatives rejected

- A shared `decode` block for `box_scale` and `coordinate_scale`: only one field is close to
  shared, and no model gives them different values.
- New titles with the old IDs and file names: this keeps "pose" in the IDs of `keypoint` fields.
- `lines`, `links`, `bones` or `segments` for `edges`: `segments` and `links` name rigid bodies,
  `bones` implies anatomy, and `lines` names only the drawing.
- MediaPipe option names on `mediapipe_tasks`: shared words make a node swap simple.

## Open work

[open-work.md](../open-work.md)
