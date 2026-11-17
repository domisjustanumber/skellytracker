# 9HTX — Redesign of the pipeline node and port types: a boolean `flag`, `run_if`, one image, the `outputs` block with three delivered forms, a `merge` with named inputs

**Status:** accepted, 2026-11-17 (user, rulings of 2026-11-17).

## Decision

The user gave these rulings on 2026-11-17. The item numbers are the ruling numbers of the proposal
[`node-and-port-redesign.md`](../../specs/pipeline/proposals/node-and-port-redesign.md). Its
section 2 has the words of the user. Its section 11 gives the points that no ruling settles, each
with a default. The build stages of the proposal write the rules into the spec and the code.

1. The port types are `image`, `boxes`, `keypoints` and `flag`. `tensor` and `any` go. Each input
   lists the types that it accepts.
2. A `flag` is true or false, with no third state. Each node that gives a flag always runs and
   always decides, also when a previous-frame input is empty.
3. Internal boxes can have rotation, score and presence. Each node output is in source-image pixels.
4. An image is only the camera frame. No node gives an image. `gate` and `first_of` accept no
   image. The plumbing never copies an image, and a test proves it. The one BGR to RGB conversion of
   each `mediapipe_tasks` node is allowed. No tap reads an image, and the array-file tap form goes.
5. `@prev` is only on `boxes` and `keypoints` ports.
6. `redetect_trigger` reads the previous boxes and keypoints and gives the flag `redetect`. It has
   no image port. It keeps `last`. No other port gets a new name.
7. `run_if` is a flag input that runs the node only on true: on each `onnx_model`, and on the
   `mediapipe_tasks` variants `body`, `hand` and `face`, not `holistic`. It is the only way to stop
   a detector. `onnx_model` gets no "ran" output.
8. `flag_when` makes a flag from `value` (boxes or keypoints), with the three data tests of `gate`.
9. `gate`: `value` is boxes or keypoints. `condition` is boxes, keypoints (modes `is_present`,
   `is_empty`, `score_above`) or a flag (modes `is_true`, `is_false`). `gate` never passes a flag.
10. `first_of` selects between boxes or between keypoints, never between flags.
11. `merge` has the inputs `body` (required), `left_hand`, `right_hand` and `face`, row for row. A
    part replaces the group of its name in `body`, or adds it. A part with no present row leaves the
    points of `body`. The required `format` is `wholebody` or `holistic`: the node gives exactly
    that layout, and a group with no source is missing. An optional `map` overrides single points.
12. `concat` goes. The position matching of today's `merge` stays as `assign_keypoints`.
13. No hand box node: two `boxes_from_points` nodes do the work.
14. The output is the `outputs` block, not a node type. Each file must have it. Its only keys are
    `wholebody` (canonical names), `holistic` (the four MediaPipe Holistic groups) and `boxes`
    (upright boxes), with one or more. The conversion happens at this block.
15. The delivered keypoints carry `present` and `instance_score`, no `raw_score`, no `track_ids`.
16. The delivered `boxes` carry, for each row, corners, score, class, presence and `detector_ran`:
    true when the detector node that the box comes from ran on that frame. freemocap Core reads
    only the outputs: no `node_ran` and no literal node id.
17. The load refuses a pipeline whose output box can be rotated. The output never changes a box.
18. Later work: a look into one canonical output keypoint set as the only output format.
19. Taps are on `boxes`, `keypoints` and `flag` ports. A flag tap line has `true` or `false`.
20. Before the 2.0.0 pre-release: items 1 to 7, 9, 10 and 14 to 17, and the reader of freemocap
    Core. After it: `merge`, `flag_when`, `assign_keypoints` and the editor.
21. The flag, the trigger with `run_if`, and the image rule are built now. The `outputs` change and
    the reader of Core wait for the pipeline-metrics stage of freemocap.

This entry amends:
[ADR-W5QD](W5QD-pipeline-entries-consolidation.md) items 1, 2 and 3 (the glue nodes, the trigger,
the `outputs` block, the port types, the annotator);
[ADR-4WR9](4WR9-params-schema-in-the-node-catalog.md) item 3 (`any`);
[ADR-2RWC](2RWC-one-boxes-port-type-and-node-descriptions.md) item 6 (the box outputs);
[ADR-97X9](97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) items 1, 5 and 6 (`concat`,
`any`, `@prev`);
[ADR-4MP6](4MP6-pipeline-point-groups-and-canonical-form.md) items 2, 3, 5 and 7 (groups, output
schema, hand side, canonical conversion);
[ADR-PX6Z](PX6Z-keypoint-raw-score-in-the-pipeline-result.md) item 2 (`raw_score` in the result);
[ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md) items 4 and 6 (the trigger, the drawn box);
[ADR-KW76](KW76-merge-replace-add-and-hungarian-match.md), each item (the name `assign_keypoints`);
[ADR-Q5BN](Q5BN-node-ran-in-the-camera-result.md) item 5 (reserved output names);
[ADR-Q59W](Q59W-pipeline-timing-and-taps.md) (the tap forms);
[ADR-6DKT](../../specs/pipeline/decisions/entries/6DKT-instance-rows-carry-class-and-score.md)
item 5 (`concat`).

## Reason

The user wants the least number of port types, inputs that the load validates, and one fixed form
for the result that freemocap Core reads. Today Core has output names and a node id as literals,
and an image port carries a control signal. The entry is not absorbed: no absorb document states
its rules yet.

## Consequences

- The node count goes from 11 to 12. The port type count goes from 5 to 4.
- The tracking of `yolox-rtmw-wholebody` is meant to stay equal. This rests on reasoning until the
  box parity test of [ADR-7E4Z](7E4Z-box-parity-of-the-built-in-with-sfn26.md) runs.
- A pre-release file with `concat` or today's `merge` must change after the pre-release.

## Alternatives rejected

The user first chose each of these, then reversed it: a flag with three states; a gate on an
image; an `output` node type; the mode names `is_set` and `is_not_set`; a hand box node.

## Open work

[open-work.md](../open-work.md)
