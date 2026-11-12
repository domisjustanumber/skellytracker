---
id: node.redetect
title: Redetect
kind: node
vectors: vectors/node.redetect.yaml
status: {spec: draft}
---

# Redetect

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `redetect` decides on each frame if a detector must run again. When a new detection is
necessary, the output is the input image. Else the output is empty. This output is the trigger: the
detector node that takes it runs only when it is not empty
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). The node
asks for a detection at a fixed interval, and when a fitness check on the previous frame fails. A
`redetect` node upstream of a detector makes a pipeline stateful
([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 5).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `redetect_interval` | `int` | >= 1 | `1` | yes | Ask for a new detection at least each this many frames. | BBoxPolicyConfig.redetect_interval |
| `fitness_checks` | `list[FitnessCheck]` |  | `[]` | no | Checks on the previous frame that ask for a new detection. | BBoxPolicyConfig.fitness_checks |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `image` | input | `image` |
| `previous_keypoints` | input | `keypoints` |
| `previous_rois` | input | `roi` |
| `image` | output | `image` |
<!-- /node-table:ports -->

- `previous_keypoints` and `previous_rois` are usually `@prev` values: the keypoints and the crop
  ROIs of the previous frame. Each `@prev` value is empty on the first frame
  ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 4).
- `previous_keypoints` and `previous_rois` are optional inputs. An empty optional input does not
  stop the node ([Graph](../graph.md#behaviour) item 6).
- An ROI is `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians
  ([Graph](../graph.md#behaviour) item 3).
- Each item of `fitness_checks` has a `check` and only the fields of that check
  (`V-node.redetect-1`). A field that the item does not write takes its default:

  | `check` | Fields and defaults |
  |---|---|
  | `min_keypoint_score` | `threshold: 0.3` |
  | `keypoints_within_bbox_ratio` | `threshold: 0.5` |
  | `max_frames_without_redetect` | `n_frames: 30` |
  | `bbox_area_collapse` | `min_area_ratio: 0.25`, `expand_ratio: 1.10`, `min_score: 0.0` |

- `expand_ratio` multiplies the width and the height of the box around the points. The default
  1.10 is a margin of 0.05 on each side, as today's code: 1 + 2 · 0.05
  ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 4). A score threshold has
  no upper bound.

## Behaviour

1. **Empty image.** When `image` is empty, the node does not run. The output is empty and the state
   does not change ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md)
   item 6). Empty `previous_keypoints` and `previous_rois` do not stop the node, because they are
   optional inputs.
2. **Running mode.** In the running mode `image`, the output is always the image, and the node keeps
   no state ([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 2).
   The steps that follow apply to `video` and `live`.
3. **State.** The node keeps `last`, the `frame_index` of the last frame on which it gave the image.
   It is empty at the start. Let `n` be the `frame_index` of this frame. In `live`, `frame_index`
   can skip, and a skip counts. `redetect_interval` stays in frames.
4. **Decision.** The node gives the image when one of these is true:
   1. `last` is empty;
   2. `n - last >= redetect_interval`;
   3. a check of `fitness_checks` fails for an instance row (step 5).

   Then `last = n`. Else the output is empty.
5. **Rows.** The checks run for each row `i`, with row `i` of `previous_keypoints` and row `i` of
   `previous_rois`. When an input is empty, each of its rows is missing. A row of `previous_rois`
   that is not present is missing. When both inputs are empty, the checks run once, with no row. A
   point is valid when its x and its y are not NaN.
6. **Checks.** Each check fails only in the case that it gives:
   - `max_frames_without_redetect`: `n - last >= n_frames`.
   - `min_keypoint_score`: the keypoint row is there and has a valid point, and the mean score of
     its valid points is less than `threshold`.
   - `keypoints_within_bbox_ratio`: the keypoint row and the ROI are there, the keypoint row has a
     valid point, and the part of its valid points inside the ROI is less than `threshold`. A point
     `(x, y)` is inside when:

     ```text
     u = cos(rotation) · (x - cx) + sin(rotation) · (y - cy)
     v = -sin(rotation) · (x - cx) + cos(rotation) · (y - cy)
     inside = |u| <= w / 2  and  |v| <= h / 2
     ```

   - `bbox_area_collapse`: the keypoint row and the ROI are there. The counted points are the valid
     points, and only those with `score >= min_score` when `min_score > 0`. The check fails when no
     point is counted, or when the counted points span no width or no height. Else:

     ```text
     width  = max(x) - min(x)          height = max(y) - min(y)
     fails  = w · h > 0  and  width · expand_ratio · height · expand_ratio < min_area_ratio · w · h
     ```

## Validation rules

- [ ] `V-node.redetect-1` Each item of `fitness_checks` must write only `check` and the fields of its `check`: `threshold` for `min_keypoint_score` and `keypoints_within_bbox_ratio`, `n_frames` for `max_frames_without_redetect`, and `min_area_ratio`, `expand_ratio` and `min_score` for `bbox_area_collapse`.

## Implementer guidance

- The Behaviour follows skellytracker/core/temporal_processing/bbox_policy.py
  (`BBoxPolicy.should_redetect`, `MinKeypointVisibilityCheck.fails`,
  `KeypointsWithinBBoxRatioCheck.fails`, `MaxFramesWithoutRedetectCheck.fails`,
  `BBoxAreaCollapseCheck.fails` and `predict_bbox_from_keypoints`). With `rotation = 0` and one row,
  the reference gives the same results as that code. The notes of the vector file give the
  comparison.
- Today skellytracker/core/tracker/detection_stage.py (`DetectionStage.run`) calls
  `should_redetect` with the smoothed box and the keypoints of the previous frame, and sets
  `last_detection_frame` when the detector runs. In this section, `last` is the frame of the last
  trigger. The node cannot see if the detector ran.
- Today's boxes have no rotation. The test for a point inside a rotated ROI is new in this section.
  With `rotation = 0` it is the box test of today, with the edges inside.
- `bbox_area_collapse` makes an axis-aligned box around the points also when the ROI has a rotation.
- A row with no valid point passes `min_keypoint_score` and `keypoints_within_bbox_ratio`, but
  fails `bbox_area_collapse` when its ROI is there. Today's code does the same: the track is lost.
- Today the ONNX-batched path redetects all cameras together when one camera needs it
  (skellytracker/core/tracker/detection_stage.py (`DetectionStage.run_batch`)). This section
  decides for each camera.

## Authoring guidance

- Connect `previous_keypoints` to the keypoints of the previous frame (`<node>.keypoints@prev`) and
  `previous_rois` to the crop ROIs of the previous frame, for example `<smooth_roi node>.rois@prev`.
- The default `redetect_interval: 1` asks for a detection on each frame. Without fitness checks and
  with a larger interval, the node gives the image each `redetect_interval` frames.
- `max_frames_without_redetect` and `redetect_interval` have the same effect. Use one of them.
- `bbox_area_collapse` finds a person who leaves the image or a track that moves to a smaller
  object. Use it when `redetect_interval` is large.

## Examples

The vector file [`node.redetect.yaml`](../vectors/node.redetect.yaml) holds the worked cases.

```yaml
- id: need_person
  type: redetect
  inputs: {image: frame.image, previous_keypoints: smooth.keypoints@prev, previous_rois: crop.rois@prev}
  params:
    redetect_interval: 30
    fitness_checks:
      - {check: min_keypoint_score, threshold: 0.3}
      - {check: bbox_area_collapse}
```
