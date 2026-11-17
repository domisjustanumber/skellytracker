---
id: node.boxes_from_points
title: Boxes from points
kind: node
vectors: vectors/node.boxes_from_points.yaml
status: {spec: draft}
---

# Boxes from points

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `boxes_from_points` makes one box from the keypoints of each present instance row. A later
`onnx_model` node crops each box with its rotation ([Node: ONNX model](onnx_model.md#behaviour)). The node uses the MediaPipe rect rules: a rotation from two points, a
box around the points or a box from the alignment points, and then one rect transformation
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It takes the
place of `keypoint_bbox` in a pipeline, but it does not reproduce `keypoint_bbox`
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `points` | `list[str \| list[str]] \| None` | length >= 1 | `null` | no | The points of the box. A list of names is one point with aliases: the first present name counts. Empty: each present point of the input. | ADR-7NY2 item 6; ADR-RA0E item 2 |
| `derived_points` | `dict[str, str \| list[str] \| dict[str, float]]` |  | `{}` | no | Derived point name to derivation, in the map form of the sidecar `keypoint.derived_points`: passthrough, mean or weighted. | ADR-7NY2 item 6; ADR-88WQ item 6 |
| `size_rule` | `Literal['bounds', 'alignment']` |  | `"bounds"` | no | `bounds`: the box around the points. `alignment`: centre at the start point, size 2 × the distance from start to end. | MediaPipe AlignmentPointsRectsCalculator; ADR-7NY2 item 6 |
| `alignment_start` | `str \| None` |  | `null` | no | The start point of the alignment rule. | ADR-7NY2 item 6 |
| `alignment_end` | `str \| None` |  | `null` | no | The end point of the alignment rule. | ADR-7NY2 item 6 |
| `target_rotation_deg` | `float \| None` |  | `null` | no | The rotation target in degrees. Empty: rotation `none`, an axis-aligned box. | MediaPipe rect rotation; ADR-7NY2 item 6 |
| `score_threshold` | `float` | >= 0.0 | `0.0` | yes | A point counts only when its score is greater than this value. | ADR-7NY2 item 6; ADR-88WQ item 6 |
| `shift_x` | `float` |  | `0.0` | yes | Shift along the box x axis, in box widths. | MediaPipe RectTransformationCalculator default |
| `shift_y` | `float` |  | `0.0` | yes | Shift along the box y axis, in box heights. | MediaPipe RectTransformationCalculator default |
| `square_long` | `bool` |  | `false` | yes | Make the box square with its longer side. | MediaPipe RectTransformationCalculator default |
| `expand_ratio` | `float` | > 0.0 | `1.0` | yes | Multiply the width and the height by this value. | MediaPipe RectTransformationCalculator scale default; ADR-88WQ item 4 |
| `min_previous_ratio` | `float \| None` | >= 0.0, <= 1.0 | `null` | yes | The smallest width and height, as a part of the box of `previous_boxes`. Empty: no floor. | BBoxPolicyConfig.min_shrink_ratio_per_frame; ADR-RA0E item 3 |
| `min_reference_ratio` | `float \| None` | >= 0.0 | `null` | yes | The smallest width and height, as a part of the box of `reference_boxes`. Empty: no floor. | BBoxPolicyConfig.min_detected_bbox_ratio; ADR-RA0E item 3 |
| `min_size_px` | `float` | >= 0.0 | `0.0` | yes | The smallest width and height, in source-image pixels. | BBoxPolicyConfig.min_bbox_size_px; ADR-RA0E item 3 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `keypoints` | input | `keypoints` |
| `previous_boxes` | input | `boxes` |
| `reference_boxes` | input | `boxes` |
| `boxes` | output | `boxes` |
<!-- /node-table:ports -->

- A box is `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians,
  clockwise in the image, in `[-π, π)` ([Graph](../graph.md#behaviour) item 3).
- The output has one row for each row of the input
  ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). Row `i` of
  `boxes` comes from row `i` of `keypoints`. An empty row has `present` false.
- A name in `points`, `alignment_start` and `alignment_end` is a point name of the input,
  `<group>/<point>`, for example `body/left_wrist`, or the name of a derived point
  ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). A source of a derived point is a point name of the input.
- `alignment_start` and `alignment_end` are used by the size rule `alignment`, and by the size rule
  `bounds` when `target_rotation_deg` is given. In other cases the node does not use them.
- `points` can be empty. The node then uses each present point of the input
  (Behaviour step 5; [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 2).
- `previous_boxes` and `reference_boxes` are optional inputs. An empty optional input does not stop
  the node ([Graph](../graph.md#behaviour) item 6). They give the sizes of the floors
  `min_previous_ratio` and `min_reference_ratio` (Behaviour step 10;
  [ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 3). Row `i` of each
  input goes with row `i` of `keypoints` (`V-node.boxes_from_points-7`).
- `derived_points` has the forms, the missing rule and the score rule of the sidecar
  [`keypoint.derived_points`](../../model-sidecar/post/keypoint/schema.md#keypointderived_points)
  ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) items 6 and 7). Each source is a
  point name of the input. The sidecar form `[prefix]` is not allowed in a pipeline file.

## Behaviour

1. If `keypoints` is empty, the node does not run. `boxes` is empty
   ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).
2. The node does steps 3 to 10 for each row `i` of `keypoints`. If row `i` is not present, row `i` of
   `boxes` is empty.
3. **Present points.** A point of the input is present when its score is greater than
   `score_threshold` and its x and its y are not NaN. The test is strict, as each score comparison
   of the sidecar spec ([Selection behaviour](../../model-sidecar/post/object/decode.md#selection-behaviour)):
   a score equal to `score_threshold` is not present.
4. **Derived points.** For each entry of `derived_points`: when each source is present, the derived
   point is present at `(Σ w_k · x_k, Σ w_k · y_k)`, over the sources `k`. The weight `w_k` is 1 for
   a passthrough, `1 / n` for a mean of `n` points, and the given weight for a weighted entry. Else
   the derived point is not present. A negative weight extrapolates.
5. **Resolved points.** For each entry of `points`, in its order: a name is one point. A list of
   names is one point with aliases: the first present name of the list counts. The required points
   of the row are the entries of `points`, and `alignment_start` and `alignment_end` when the node
   uses them (see [Fields](#fields)). If a required point is not present, row `i` of `boxes` is
   empty. Let `(x0, y0)` be the point `alignment_start` and `(x1, y1)` the point `alignment_end`.
   When `points` is empty, the resolved points are the present points of row `i` of the input, and
   no point of the input is required. If no point of the input is present, row `i` of `boxes` is
   empty. `alignment_start` and `alignment_end` stay required when the node uses them.
6. **Rotation.** If `target_rotation_deg` is empty, `rotation = 0`. Else:

   ```text
   rotation = NormalizeRadians(radians(target_rotation_deg) - atan2(-(y1 - y0), x1 - x0))
   NormalizeRadians(a) = a - 2π · floor((a + π) / (2π))
   ```

   The result is in `[-π, π)`. Let `c = cos(rotation)` and `s = sin(rotation)`.
7. **Size rule `alignment`.** `cx = x0`, `cy = y0` and `w = h = 2 · sqrt((x1 - x0)² + (y1 - y0)²)`.
   The resolved points of `points` do not change the box.
8. **Size rule `bounds`.** For each resolved point
   `(x, y)` of `points`, compute its position in the box frame: `u = x · c + y · s` and
   `v = -x · s + y · c`. Then:

   ```text
   w  = max(u) - min(u)
   h  = max(v) - min(v)
   uc = (max(u) + min(u)) / 2
   vc = (max(v) + min(v)) / 2
   cx = uc · c - vc · s
   cy = uc · s + vc · c
   ```

   With `rotation = 0` this is the axis-aligned box around the points.
9. **Transform.** Apply these three steps in this order, with `c` and `s` of step 6:
   1. Shift along the box axes: `cx = cx + w · shift_x · c - h · shift_y · s` and
      `cy = cy + w · shift_x · s + h · shift_y · c`.
   2. If `square_long` is true: `w = h = max(w, h)`.
   3. Expand: `w = w · expand_ratio` and `h = h · expand_ratio`.
10. **Floors.** Apply these three floors after step 9, in this order. Each floor keeps `cx`, `cy` and
    `rotation`. Each floor compares the width and the height separately.
    1. If `min_previous_ratio` is given and row `i` of `previous_boxes` is present, with the size
       `(pw, ph)`: `w = max(w, min_previous_ratio · pw)` and `h = max(h, min_previous_ratio · ph)`.
    2. If `min_reference_ratio` is given and row `i` of `reference_boxes` is present, with the size
       `(rw, rh)`: `w = max(w, min_reference_ratio · rw)` and `h = max(h, min_reference_ratio · rh)`.
    3. `w = max(w, min_size_px)` and `h = max(h, min_size_px)`.

    When `previous_boxes` or `reference_boxes` is empty, or its row `i` is not present, its floor does
    not apply. The floors do not use the rotation of `previous_boxes` or of `reference_boxes`.

    Row `i` of `boxes` is `(cx, cy, w, h, rotation)`, present. It has the `instance_score` of row `i`
    of `keypoints` ([Graph](../graph.md#behaviour) item 8). Its `class_index` is -1, because a
    keypoints row has no class ([ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)).

## Validation rules

- [ ] `V-node.boxes_from_points-1` The size rule `alignment` needs `alignment_start` and `alignment_end`.
- [ ] `V-node.boxes_from_points-2` Each name in `points`, `alignment_start` and `alignment_end` must be a point name of the input or a key of `derived_points`. Each source of a derived point must be a point name of the input. The host checks this at load, against the output schema of the input port.
- [ ] `V-node.boxes_from_points-3` Each key of `derived_points` must be a name. A name has no `/`, so it is not a point name of the input ([ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)).
- [ ] `V-node.boxes_from_points-4` The size rule `bounds` with a `target_rotation_deg` needs `alignment_start` and `alignment_end`.
- [ ] `V-node.boxes_from_points-5` A mean derived point must have at least one source. The weights of a weighted derived point must sum to 1, within an absolute tolerance of `1e-6`, as in the sidecar rule `V-post.keypoint.schema-6`.
- [ ] `V-node.boxes_from_points-6` `min_previous_ratio` needs a connected `previous_boxes` input. `min_reference_ratio` needs a connected `reference_boxes` input ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 3).
- [ ] `V-node.boxes_from_points-7` `previous_boxes` and `reference_boxes` must have the instance source and the number of rows `I` of `keypoints`. The host checks this at load, from the instance sources of the connected outputs.

## Implementer guidance

- Compute in float64. The vectors use a tolerance of `1e-6`.
- The point positions are in source-image pixels. Thus `square_long` uses the pixel sizes, as
  MediaPipe does after it multiplies a normalised rect by the image size. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:58-60`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L58-L60))
- The rotation formula and `NormalizeRadians` are those of MediaPipe `DetectionsToRectsCalculator`
  and `AlignmentPointsRectsCalculator`. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:63-77`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L63-L77))
- The order shift, `square_long`, `expand_ratio` is the order of MediaPipe
  `RectTransformationCalculator`. The node has one `expand_ratio` for the width and the height: the
  `scale_x` and `scale_y` of MediaPipe with one value. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:79-90`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L79-L90))
- The box of step 8 does not depend on the origin of the pixel frame. An implementation can
  subtract a point near the box before the rotation, for better float precision.
- A box around one point, or around points on one line, has a width or a height of 0. The node
  gives that box. It does not refuse it.
- The floors of step 10 follow skellytracker/core/temporal_processing/bbox_policy.py
  (`BBoxPolicy.predict_bbox`): the floor from the previous crop (`min_shrink_ratio_per_frame`), the
  floor from the last box of the detector (`min_detected_bbox_ratio`) and the pixel floor
  (`min_bbox_size_px`), each around the centre of the box. With `rotation = 0`, step 10 gives the
  same box as that code.

## Authoring guidance

- To make the Holistic hand box from the pose, add the derived point
  `middle = (2 · index + pinky) / 3`, use the size rule `alignment` from the wrist to `middle` with
  `target_rotation_deg: 90`, then `shift_y: -0.1`, `square_long: true` and `expand_ratio: 2.7`.
  MediaPipe gates this branch on the wrist visibility only (`> 0.1`). `score_threshold: 0.1` also
  tests the index point and the pinky point, so it is stricter. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:384-389`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L384-L389))
- To make the hand box from the previous hand landmarks, use the size rule `bounds` with the
  12 palm points, a derived MCP point with the weights 0.25, 0.25 and 0.5, the alignment from the
  wrist to that point with `target_rotation_deg: 90`, then `shift_y: -0.1`, `square_long: true` and
  `expand_ratio: 2.0`. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:395-399`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L395-L399))
- To make the loose Holistic face box, use the size rule `bounds` with the pose points 0 to 10, the
  alignment from the right eye to the left eye with `target_rotation_deg: 0`, then
  `square_long: true` and `expand_ratio: 3.0`. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:456-457`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L456-L457))
- Use aliases for a point that another model of the same instance source can also give, for example a hand
  wrist and a body wrist. Put the better point first.
- `keypoint_bbox` used the mean of its centre points, the largest distance of point pairs, a square
  box and a minimum size. Do not expect the same boxes from this node
  ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 13).
- To carry a person box from the points of the previous frame, as the example
  [`yolox-rtmw-wholebody`](../examples/yolox-rtmw-wholebody.pipeline.yaml) does, leave `points`
  empty, connect `keypoints` to `<node>.keypoints@prev`, and set `score_threshold` and
  `expand_ratio`. Connect `previous_boxes` to the crop boxes of the previous frame. Connect
  `reference_boxes` to the last box of the detector: a `first_of` node with the inputs
  `[<detector>.boxes, <that first_of node>.value@prev]` holds it
  ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 1).

## Examples

The vector file [`node.boxes_from_points.yaml`](../vectors/node.boxes_from_points.yaml) holds the worked
cases.

```yaml
- id: hand_box
  type: boxes_from_points
  inputs: {keypoints: body.keypoints}
  params:
    points: [body/left_wrist]
    derived_points:
      left_middle: {body/left_index: 0.6666666666666666, body/left_pinky: 0.3333333333333333}
    size_rule: alignment
    alignment_start: body/left_wrist
    alignment_end: left_middle
    target_rotation_deg: 90
    score_threshold: 0.1
    shift_y: -0.1
    square_long: true
    expand_ratio: 2.7
```
