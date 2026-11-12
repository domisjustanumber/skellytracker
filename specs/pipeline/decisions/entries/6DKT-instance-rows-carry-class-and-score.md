# 6DKT — Instance rows carry a class and an instance score; tap lines carry their row; `concat` fills an empty input

**Status:** accepted, 2026-11-12 (user).

## Decision

1. **Class.** A `detections` value has `class_index` `(I,)`: the class index that the sidecar
   object decode keeps. A padding row has -1. The output schema and `tap.json` give `class_names`,
   the `object.classes` of the model. A `detections.jsonl` line writes `class`, the class name, in
   place of `category_id`. The consumer maps the name to the category id of its data set.
2. **Instance score.** Each `keypoints` and `roi` value has `instance_score` `(I,)`. The instance
   source sets it: an object detector or a one-stage model gives the detection score of the row,
   and a `mediapipe_tasks` node gives 1.0. Each other node copies it from its input row. `merge`
   copies it from its `target` input. A row that a node keeps from `@prev` keeps its score. A
   padding row has 0. The instance score is not a function of the point scores.
3. **Tap scores.** A `keypoints.jsonl` line and an `roi.jsonl` line write `score`, the
   `instance_score` of the row. A tap applies no rescoring.
4. **Tap rows.** Each JSONL line has `row`, its row index. A replay puts each line in its row and
   refuses a bad `row` (`V-pipeline.taps-6`) and an unknown `class` (`V-pipeline.taps-7`).
5. **`concat`.** An empty input does not stop `concat`. Its columns are missing points: x, y and z
   are NaN, and the score is 0.
6. **`mediapipe_tasks` output.** The output has `geometry: 3d` and `depth_unit: pixel`.

## Reason

- skellybench scores boxes and keypoints with `faster-coco-eval` 1.8.0. Its reference `computeOks`
  sorts the predictions by the instance `score` and reads only x and y of each predicted point
  (`faster_coco_eval/core/cocoeval.py:315`, `:327-328`). skellybench applies the mmpose rescoring
  itself and asks for the raw detector score of each top-down row (skellybench
  `plans/consumer-guide.md:103-106`).
- A top-down keypoint model gives a score for each point only. The detection score of the instance
  source is the standard instance score in mmpose, COCO and skellybench. An ROI has no score, so a
  join of tap files cannot find the score of a hand row that `roi_from_points` makes.
- The `detections` value dropped the class index that the sidecar decode keeps. A class index plus 1
  is not a COCO category id, and a wrong map scored a detector at AP 0.066 in place of about 0.41
  ([Object decode](../../../model-sidecar/post/object/decode.md#authoring-guidance)).
- A fan-out child can have a padding row before a present row. Without `row`, a replay put that
  line on the wrong person.
- Without the exception, a missing hand ROI emptied the whole `concat` output, also the body points.
- MediaPipe scales z by the image width
  ([Coordinate decode](../../../model-sidecar/post/keypoint/decode-coordinate.md)).

## Alternatives rejected

- A tap line with padding rows: strict JSON has no NaN, and a COCO scorer counts each line as a
  detection.
- A consumer join on `(image_id, row)` for the instance score: it fails for a `roi` value and for
  `mediapipe_tasks`.
- An instance score made from the point scores: no model defines it, and skellybench rescores again.
- `category_id` equal to the class index in tap lines.

## Open work

[open-work.md](../open-work.md)
