# 97X9 — Pipeline rules: instance rows, `@prev` types, a state for each camera and refused calls

**Status:** absorbed into [`concat.md#behaviour`](../../specs/pipeline/nodes/concat.md#behaviour), [`smooth_keypoints.md#behaviour`](../../specs/pipeline/nodes/smooth_keypoints.md#behaviour), [`smooth_keypoints.md#validation-rules`](../../specs/pipeline/nodes/smooth_keypoints.md#validation-rules), [`roi_tracking.md#behaviour`](../../specs/pipeline/nodes/roi_tracking.md#behaviour), [`roi_tracking.md#validation-rules`](../../specs/pipeline/nodes/roi_tracking.md#validation-rules), [`redetect.md#behaviour`](../../specs/pipeline/nodes/redetect.md#behaviour), [`first_of.md#validation-rules`](../../specs/pipeline/nodes/first_of.md#validation-rules), [`mediapipe_tasks.md#validation-rules`](../../specs/pipeline/nodes/mediapipe_tasks.md#validation-rules), [`graph.md#behaviour`](../../specs/pipeline/graph.md#behaviour), [`graph.md#validation-rules`](../../specs/pipeline/graph.md#validation-rules), [`running.md#behaviour`](../../specs/pipeline/running.md#behaviour), [`running.md#validation-rules`](../../specs/pipeline/running.md#validation-rules), 2026-11-13 (user; PR: pending).

## Decision

1. **`concat` rows.** `concat` takes the `instance_score` and the `track_ids` of row `i` from the
   first input whose row `i` is present. A row with no present input row is a padding row.
2. **Held rows.** A row that `smooth_keypoints` holds keeps the `instance_score` and the
   `track_ids` of the last frame on which its input row was present. The values do not decay.
3. **`roi_tracking` source.** The output of `roi_tracking` has the instance source of `current`.
   New rule `V-node.roi_tracking-3`: `previous` and `previous_keypoints` must have the instance
   source of `current`.
4. **`redetect` rows.** A keypoint row of `previous_keypoints` is there when its `present` flag is
   true. `bbox_area_collapse` also fails when `previous_keypoints` is connected, row `i` of
   `previous_rois` is there and row `i` of `previous_keypoints` is missing.
5. **`any` types.** An `any` output gets its port type only from inputs that are not `@prev`. New
   rule `V-pipeline.graph-9`: each `any` output must get its port type from an input that is not
   `@prev`. `V-node.first_of-1` still compares each item, also an `@prev` item.
6. **`@prev` rows.** `x@prev` has the instance source and the `I` of `x`.
7. **A state for each camera.** Each temporal node keeps a separate state for each camera. The node
   section gives the state of one camera. In `live`, a camera that a call does not hold keeps its
   state.
8. **`video` timestamps.** New rule `V-pipeline.running-7`: in `video`, each camera gives
   `timestamp_ms` on all its frames or on none. The fallback `frame_index × 1000 / fps` applies to a
   camera that gives none.
9. **Refused calls.** A call that breaks `V-pipeline.running-6`, `V-pipeline.running-7` or
   `V-node.smooth_keypoints-3` raises one typed error. The call changes no state of any of its
   cameras, also no `@prev` value. The run accepts the next call. Stage 1.10 of the
   [implementation plan](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p)
   names the error. `V-node.smooth_keypoints-3` compares the frames of one camera.
10. **MediaPipe size.** New rule `V-node.mediapipe_tasks-2`: an explicit `size` needs the variant
    `body`. The default of `size` stays `heavy`. The export of stage 1.10 writes only the params
    that a config sets, so that a written config validates again.

## Reason

- A review of the pipeline spec on 2026-11-13 found these gaps. The user decided each item.
- Item 1: the inputs of `concat` can disagree on a row, for example when one row is padding. The old
  text took the first input that is not empty.
- Item 2 follows the hold of `roi_tracking`.
- Item 3: a check of `I` alone lets `previous` follow another detector. Then the output gives rows
  of that detector as rows of `current`.
- Item 4: today a lost track fails `bbox_area_collapse` when its ROI is there, and the detector runs
  on the next frame. With only the `present` flag, a lost track waits for `redetect_interval`.
- Item 5: the type search never follows an `@prev` edge, so it always ends. No example uses an
  `@prev` input as the type source.
- Item 9: one rule for the three timestamp rules. A call is all or nothing, so no camera gets ahead
  of another.
- Item 10: a dump of a default config holds `size: heavy`. Without the export rule, that dump fails
  item 10.

## Consequences

- `gate` with `value: x@prev`, and `first_of` with only `@prev` items, do not load.
- `concat` and `smooth_keypoints` give each row its own `instance_score`. The sentence "the inputs
  have the same value" of `concat` goes.
