# PX6Z — The keypoint `score` of the pipeline result is the mapped score, and `raw_score` keeps the decode score

**Status:** absorbed into [`outputs.md#fields`](../../specs/pipeline/outputs.md#fields), [`outputs.md#behaviour`](../../specs/pipeline/outputs.md#behaviour), [`README.md#terms`](../../specs/pipeline/README.md#terms), [`taps.md#fields`](../../specs/pipeline/taps.md#fields), [`taps.md#behaviour`](../../specs/pipeline/taps.md#behaviour), [`concat.md#behaviour`](../../specs/pipeline/nodes/concat.md#behaviour), [`merge.md#behaviour`](../../specs/pipeline/nodes/merge.md#behaviour), [`smooth_keypoints.md#fields`](../../specs/pipeline/nodes/smooth_keypoints.md#fields), [`smooth_keypoints.md#implementer-guidance`](../../specs/pipeline/nodes/smooth_keypoints.md#implementer-guidance), [`values.py`](../../skellytracker/core/pipelines/values.py), 2026-11-16 (user, question C1 of 2026-11-16; PR: pending).

## Decision

1. **`score`.** The `score` of a `keypoints` value is the score of the sidecar after its
   [score map](../../specs/model-sidecar/post/keypoint/score-map.md#behaviour) when the size of the
   sidecar has one: a value in `[0, 1]`. Else it is the decoded score of the sidecar. For a
   `mediapipe_tasks` node, it is the landmark visibility of MediaPipe, as before. A missing point
   has the score 0
   ([ADR-F067](../../specs/model-sidecar/decisions/entries/F067-simcc-score-map.md)).
2. **`raw_score`.** A `keypoints` value (`InstanceKeypoints`) has the field `raw_score`, with the
   shape `(I, P)` and the type float64: the decode score of each point before the score map. The
   `onnx_model` node fills it from `KeypointDetections.raw_scores`.
   - When the size of the sidecar has no score map, and for a `mediapipe_tasks` node,
     `raw_score` is equal to `score`. It is never `None`.
   - A missing point and a padding row have `raw_score` 0. The generic keypoint detector gives 0,
     because it applies the missing rule of
     [Decoded keypoints](../../specs/model-sidecar/post/keypoint/schema.md#decoded-keypoints)
     before the map.
   - Each node that copies, moves, holds or passes the score of a point does the same with its
     `raw_score`. Each node that sets the score of a point to 0 also sets its `raw_score` to 0.
   - A `keypoints` tap line has `raw_score`: the list of the `raw_score` of each point. A replay
     reads it.
   - `instance()` and `single()` give the key `raw_score`.
3. **The canonical form.** `CanonicalKeypoints` has no `raw_score`. A computed canonical point has
   no decode score, and the sidecar gives the score of a derived point only from the mapped scores.
4. **The missing rule of the canonical form.** `to_canonical` takes a source point as missing when
   its `raw_score` is 0 or less, not from its score. The rule "a missing point has the score 0"
   does not change.

The spec text is in [Outputs](../../specs/pipeline/outputs.md#fields) and its
[Behaviour](../../specs/pipeline/outputs.md#behaviour) item 9, the score term of the
[README](../../specs/pipeline/README.md#terms), [Taps](../../specs/pipeline/taps.md#fields), and the
nodes [concat](../../specs/pipeline/nodes/concat.md#behaviour),
[merge](../../specs/pipeline/nodes/merge.md#behaviour) and
[smooth_keypoints](../../specs/pipeline/nodes/smooth_keypoints.md#fields).

## Reason

- The user decided on 2026-11-16 that the result score is the normalised score in `[0, 1]`, and
  that the raw score stays available as a second field.
- `raw_score` equal to `score`, not `None`: `z` is `None` only because a `2d` output has no depth.
  Each point has a decode score, so `raw_score` always has a value. `concat` and `merge` can then
  join a value of a model with a score map and a value of MediaPipe with no rule for a mix.
- The name `raw_score` follows rule 9 of the public names: an array with one value for each point
  keeps the singular name of the spec, as `score` does.
- The missing rule from `raw_score > 0`: a mapped score of a present point can round to `0.0` in
  float32 ([Keypoint score map](../../specs/model-sidecar/post/keypoint/score-map.md#behaviour)).
  With the score, that point and each canonical point that reads it would become missing. The rule
  of finite coordinates is not used: a point that `smooth_keypoints` holds has finite coordinates
  and the score 0, and today it is missing in the canonical form. The rule from `raw_score` keeps
  that result, and changes only the case of the rounding.

## Consequences

- Each constructor of `InstanceKeypoints` gives `raw_score` after `score`. The field has no
  default.
- A tap of a `keypoints` port that has no `raw_score` key does not replay.
- The vector files of the glue nodes give no `raw_score`. Their test gives each input
  `raw_score` equal to `score`, and checks that each output keeps them equal.
- The reference modules of `concat` and `merge` in `specs/pipeline/reference/` move only the score.
  Item 2 gives the rule for `raw_score`.

## Evidence

- `skellytracker/core/detectors/generic/keypoint_detector.py`, `GenericKeypointDetector.detect`:
  `raw_scores` is the result of `mark_missing`, so a missing point has the raw score 0.
- `skellytracker/tests/pipelines/test_builtin_models.py`, `check_result`: on the real RTMW model,
  more than 60 of the 133 mapped scores are above 0.4 on each frame of the test video, on the CPU
  EP, before and after this change.

## Alternatives rejected

- `raw_score` is `None` for a model with no score map. Rejected: `concat` and `merge` would need a
  rule for a mix of `None` and an array, and a consumer would need two code paths.
- A `raw_score` in the canonical form, with the minimum of the raw scores for a computed point.
  Rejected: two groups can have two maps, so the minimum of the raw scores has no defined meaning.
- The missing rule from finite coordinates. Rejected: it changes the result for a held point.
