# 2RWC — One port type `boxes`, box names for the glue nodes, and a `description` for each node

**Status:** accepted, 2026-11-16 (user, pipeline editor review of 2026-11-16).

## Decision

1. **One box type.** The port type `boxes` replaces `roi` and `detections`. Its value is
   `InstanceBoxes` with `boxes` `(I, 5)` `(cx, cy, w, h, rotation)`, `instance_score`,
   `class_index`, `present` and `track_ids`. A padding row has NaN, 0, -1, false and -1.
   `InstanceRois` goes.
2. **`onnx_model`.** An object detector gives `boxes`, with rotation 0. Its `instance_score` is the
   detection score, and its `class_index` is the class index of the decode. A one-stage model gives
   `boxes` and `keypoints`. A top-down keypoint model takes `boxes`. The ports `detections` and
   `rois` go.
3. **Class.** `boxes_from_points` gives `class_index` -1, because a keypoints row has no class.
   `hold_boxes`, `smooth_boxes`, `gate` and `first_of` copy it with the row. The output schema gives
   `class_names` for each `boxes` output: the classes of the detector, or null after
   `boxes_from_points`. Each other node keeps the `class_names` of its input.
4. **Gate.** `score_above` on a `boxes` condition tests the `instance_score` of the row.
5. **Taps.** A `boxes` tap writes `boxes.jsonl`: `box`, `bbox` (the axis-aligned bounds), `score`
   (the instance score) and `class` (the class name, or null for -1). A replay gives -1 for a null
   `class` (`V-pipeline.taps-7`).
6. **Renames.** The node types `roi_from_points`, `roi_hold` and `smooth_roi` are now
   `boxes_from_points`, `hold_boxes` and `smooth_boxes`, with their section IDs, rule IDs, files,
   reference modules, vector files and params classes. The ports `rois`, `previous_rois` and
   `reference_rois` are now `boxes`, `previous_boxes` and `reference_boxes`. The check
   `roi_missing` is now `box_missing`. The outputs `person_box` and `person_roi` of
   `yolox-rtmw-wholebody` are now `detector_box` and `crop_box`. No old name has an alias.
7. **Kept names.** `keypoints_within_bbox_ratio` and `bbox_area_collapse` keep the names of the
   fitness checks of `BBoxPolicyConfig`. The sidecar spec keeps "ROI": the sidecar crop takes a
   box as its ROI.
8. **Descriptions.** The pipeline `description` is optional text, with one or more lines. Each node
   has an optional `description`, beside `id`, `type`, `inputs` and `params`. The default is empty.
   `export_pipeline(resolved=False)` keeps it. The built-ins and the examples put the text of their
   YAML comments in these fields.

## Reason

- A `detections` value and a `roi` value hold the same instance box. No node input took
  `detections`, so an editor could not connect a detector box to anything but an output. One type
  lets each box go to each box input.
- The merged row keeps each fact of the two rows: the rotation, the instance score and the class.
  `instance_score` keeps one name for one concept in `keypoints` and `boxes` (public-name rule 10).
- The new names say what the nodes do to boxes.
- An editor that saves a file drops its YAML comments. A `description` field keeps the text.

## Consequences

- A caller that reads `InstanceRois`, `xyxy`, `score` of a box, the outputs `person_box` or
  `person_roi`, or the files `detections.jsonl` and `roi.jsonl` must change. A pipeline file with an
  old name fails to load. 2.0.0 is not released.
- The test of `V-pipeline.running-5` makes `person` run with a patch, because only a one-stage
  model has a second output port.

## Alternatives rejected

- Keep the two types: the editor then has two box types that do not connect.
- A converter node from `detections` to `roi`: a node with no behaviour, and one more node in each
  pipeline.
- The field name `score` for the instance score: `keypoints` already uses `instance_score`.
- No `class_index` on a row that no detector made: each frame must have the same shapes.
- Keep the text only in YAML comments: a save from the editor drops it.
