---
id: node.roi_tracking
title: ROI tracking
kind: node
vectors: vectors/node.roi_tracking.yaml
status: {spec: draft}
---

# ROI tracking

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `roi_tracking` chooses, for each instance row, between a previous ROI and a current ROI. It
keeps the previous ROI when the two ROIs are near and the previous keypoints are inside the current
ROI. Else it gives the current ROI. A stable crop gives more stable keypoints. The node follows the
MediaPipe `RoiTrackingCalculator`
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `max_rotation_deg` | `float` | >= 0.0 | `40.0` | yes | Keep the previous ROI only when the rotation differs by this much or less. | MediaPipe Holistic hand RoiTrackingCalculator (face: 15) |
| `max_offset` | `float` | >= 0.0 | `0.2` | yes | The largest x and y offset, as a part of the new ROI size. | MediaPipe Holistic hand RoiTrackingCalculator (face: 0.1) |
| `max_size_change` | `float` | >= 0.0 | `0.4` | yes | The largest width and height difference, as a part of the new ROI size. | MediaPipe Holistic hand RoiTrackingCalculator (face: 0.3) |
| `keypoint_margin` | `float` |  | `-0.1` | yes | Each previous point must be inside the new ROI grown by this part (negative: shrunk). | MediaPipe Holistic hand RoiTrackingCalculator (face: -0.2) |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `previous` | input | `roi` |
| `current` | input | `roi` |
| `previous_keypoints` | input | `keypoints` |
| `rois` | output | `roi` |
<!-- /node-table:ports -->

- An ROI is `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians
  ([Graph](../graph.md#behaviour) item 3).
- `previous` is usually an `@prev` value, or an ROI that `roi_from_points` makes from the keypoints
  of the previous frame. `current` is the ROI of this frame.
- `previous_keypoints` is an optional input. An empty optional input does not stop the node
  ([Graph](../graph.md#behaviour) item 6). When it is not connected or it is empty, the node does not
  do the keypoint test (step 7).
- The output has one row for each row of `current`
  ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1). Row `i` of
  each input goes with row `i` of the other inputs, so the inputs have the same number of rows
  (`V-node.roi_tracking-2`).

## Behaviour

1. If `current` is empty, the node does not run. `rois` is empty
   ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).
2. An empty `previous` does not stop the node. This is a rule of the node, as
   [Graph](../graph.md#behaviour) item 6 allows, because `previous` is empty on the first frame. The node then uses an empty row for each row of
   `previous`.
3. The node does steps 4 to 8 for each row `i`. Let `(cx, cy, w, h, r)` be row `i` of `current` and
   `(pcx, pcy, pw, ph, pr)` row `i` of `previous`. If row `i` of `current` is empty, row `i` of
   `rois` is empty. If row `i` of `previous` is empty, row `i` of `rois` is row `i` of `current`.
4. **Rotation.** Let `d = NormalizeRadians(pr - r)`, with `NormalizeRadians` of
   [ROI from points](roi_from_points.md#behaviour). If `|d| > radians(max_rotation_deg)`, row `i`
   of `rois` is the current ROI.
5. **Offset.** All positions go into the frame of the current ROI. For an image point `(x, y)`:
   `u = (x - cx) · cos(r) + (y - cy) · sin(r)` and `v = -(x - cx) · sin(r) + (y - cy) · cos(r)`.
   Let `(u, v)` be the position of `(pcx, pcy)`. If `|u| > max_offset · w` or
   `|v| > max_offset · h`, row `i` of `rois` is the current ROI.
6. **Size.** If `|pw - w| > max_size_change · w` or `|ph - h| > max_size_change · h`, row `i` of
   `rois` is the current ROI.
7. **Keypoints.** If row `i` of `previous_keypoints` is present: for each point of that row whose x
   and y are not NaN, compute `(u, v)` as in step 5. If
   `|u| > (1 + keypoint_margin) · w / 2` or `|v| > (1 + keypoint_margin) · h / 2` for one point,
   row `i` of `rois` is the current ROI. The test does not use the score of the points.
8. If no test of steps 4 to 7 gives the current ROI, row `i` of `rois` is the previous ROI.
   It keeps the `instance_score` of the previous row: the value of the last frame on which the
   instance source ran. Else row `i` has the `instance_score` of the current row
   ([Graph](../graph.md#behaviour) item 8).

Each test uses `>`. A value equal to its limit passes the test.

## Validation rules

- [ ] `V-node.roi_tracking-1` `keypoint_margin` must be greater than -1.
- [ ] `V-node.roi_tracking-2` `previous`, `current` and `previous_keypoints` must have the same number of rows `I`. The host checks this at load, from the instance sources of the connected outputs.

## Implementer guidance

- Compute in float64. The vectors use a tolerance of `1e-6`.
- MediaPipe keeps the previous ROI unless the rotation, the translation or the size differ past
  their limits, or a previous landmark is outside the fresh ROI with its margin. The limits are
  relative to the fresh ROI, in its rotated frame. When the fresh ROI is missing, MediaPipe gives
  no ROI. Step 1 does the same. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:168-172`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L168-L172);
  [`docs/mediapipe-whole-body.md:400-403`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L400-L403))
- A negative `keypoint_margin` shrinks the current ROI for the keypoint test. The default -0.1 is
  the Holistic hand value: each previous landmark must be inside the refined ROI shrunk by 10 %.
- The node keeps no state. A loop through `@prev` gives it the previous ROI.

## Authoring guidance

- The defaults are the values of the Holistic hand branch: 40°, 0.2, 0.4 and -0.1.
  (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:400-403`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L400-L403))
- For the Holistic face branch, set `max_rotation_deg: 15`, `max_offset: 0.1`,
  `max_size_change: 0.3` and `keypoint_margin: -0.2`. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:467-468`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L467-L468))
- To follow Holistic, connect `previous` to a `roi_from_points` node that reads the keypoints of
  the previous frame (`<node>.keypoints@prev`), and connect `previous_keypoints` to the same
  keypoints.
- `roi_tracking` keeps no state, so it is not in the list of stateful nodes. Its `@prev` input makes
  the pipeline stateful ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md)
  item 5).

## Examples

The vector file [`node.roi_tracking.yaml`](../vectors/node.roi_tracking.yaml) holds the worked
cases.

```yaml
- id: face_roi
  type: roi_tracking
  inputs:
    previous: face_prev_roi.rois
    current: face_det_roi.rois
    previous_keypoints: face.keypoints@prev
  params: {max_rotation_deg: 15, max_offset: 0.1, max_size_change: 0.3, keypoint_margin: -0.2}
```
