---
id: node.smooth_boxes
title: Smooth boxes
kind: node
vectors: vectors/node.smooth_boxes.yaml
status: {spec: draft}
---

# Smooth boxes

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `smooth_boxes` smooths the box of each instance row over time with an exponential moving
average (EMA) or with a One Euro filter. A stable crop gives more stable keypoints
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6;
[ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 5). The smoothed
box is usually the crop of the next frame, so a `smooth_boxes` node upstream of an `onnx_model` node makes a
pipeline stateful ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md)
item 5).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `filter` | `Literal['ema', 'one_euro']` |  | `"ema"` | no | The filter. | ADR-RA0E item 5 |
| `previous_weight` | `float` | >= 0.0, <= 1.0 | `0.5` | yes | ema: the weight of the previous box: new = previous_weight × previous + (1 − previous_weight) × input. | BBoxSmoothingConfig.alpha; ADR-88WQ item 4 |
| `min_cutoff` | `float` | > 0.0 | `3.0` | yes | one_euro: the minimum cutoff frequency, in Hz. | BBoxSmoothingConfig.min_cutoff of the branch sfn26; ADR-RA0E item 5 |
| `beta` | `float` | >= 0.0 | `0.02` | yes | one_euro: the speed coefficient, in Hz per px/s. | BBoxSmoothingConfig.beta of the branch sfn26; ADR-RA0E item 5 |
| `d_cutoff` | `float` | > 0.0 | `1.0` | yes | one_euro: the cutoff frequency of the derivative, in Hz. | BBoxSmoothingConfig.d_cutoff of the branch sfn26; ADR-RA0E item 5 |
| `reset_after_ms` | `float` | > 0.0 | `500.0` | no | one_euro: start the filter again when the time since the last box of the row is more than this many milliseconds. | BBoxSmoothingConfig.reset_after_seconds of the branch sfn26; ADR-RA0E item 5 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `boxes` | input | `boxes` |
| `boxes` | output | `boxes` |
<!-- /node-table:ports -->

- A box is `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians
  ([Graph](../graph.md#behaviour) item 3).
- `previous_weight` is the weight of the previous output, not the weight of the input.
  `previous_weight = 0` passes the input through. `previous_weight = 1` keeps the first box of the
  row. Today's code names it `alpha` ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md)
  item 4).
- The filter `ema` uses `previous_weight`. The filter `one_euro` uses `min_cutoff`, `beta`,
  `d_cutoff` and `reset_after_ms`. A file must not write a param of the other filter
  (`V-node.smooth_boxes-1`).
- The units: `min_cutoff` and `d_cutoff` are in Hz. `beta` is in Hz per px/s. `reset_after_ms` is in
  milliseconds.
- The output `boxes` has the rows of the input. A row that is not present in the input is not present
  in the output. The `instance_score` and the `class_index` of each row pass through unchanged
  ([ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)).

## Behaviour

1. **Running mode.** In the running mode `image`, the output is the input, and the node keeps no
   state ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2). The
   steps that follow apply to `video` and `live`.
2. **Empty input.** When `boxes` is empty, the node does not run. The output is empty and the state
   does not change ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md)
   item 6). With the filter `one_euro`, an empty `boxes` input also clears the state of each row.
   This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows.
3. **State.** The state of one camera has a state for each row `i`: the last output box of the row,
   `prev` ([Running](../running.md#behaviour) item 5). It is empty at the start. With the filter
   `one_euro`, step 8 gives the state of a row.
4. **Row not present.** When row `i` of the input is not present, row `i` of the output is not
   present. The state of the row does not change. With the filter `one_euro`, the node clears the
   state of the row.
5. **Filter `ema`, first box of a row.** When row `i` is present and its state is empty, the output
   is the input box, and `prev` becomes that box.
6. **Filter `ema`, next boxes.** When row `i` is present and has a state, with `in` the input box and
   `k = previous_weight`:

   ```text
   cx       = k · prev.cx + (1 - k) · in.cx
   cy       = k · prev.cy + (1 - k) · in.cy
   w        = k · prev.w  + (1 - k) · in.w
   h        = k · prev.h  + (1 - k) · in.h
   turn     = NormalizeRadians(prev.rotation - in.rotation)
   rotation = NormalizeRadians(in.rotation + k · turn)
   ```

   `NormalizeRadians` is that of [Boxes from points](boxes_from_points.md#behaviour), with a result in
   [-π, π). The rotation moves on the short arc between the two angles. The output is
   `(cx, cy, w, h, rotation)`, and `prev` becomes the output.
7. With the filter `ema`, the `dt` of the frame and the `timestamp_ms` have no effect. In `live`, a
   dropped frame does not change the weight.
8. **Filter `one_euro`** ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 5). The filter acts on the two corners of the box: `x1 = cx - w / 2`,
   `y1 = cy - h / 2`, `x2 = cx + w / 2` and `y2 = cy + h / 2`. Each of the four values has its own
   estimate `est` and its own derivative `d`, in pixels per second. The state of row `i` also has
   `t_prev`, the `timestamp_ms` of the last frame on which the row was present. `t` is the
   `timestamp_ms` of this frame ([Running](../running.md#behaviour) item 2). `timestamp_ms` must
   increase from frame to frame
   ([`V-node.smooth_keypoints-3`](smooth_keypoints.md#validation-rules)). For a present row `i`:
   1. When the state of the row is empty, or `t - t_prev > reset_after_ms`: for each of the four
      values, `est` is the input value and `d = 0`. The test is strict.
   2. Else, with `dt = (t - t_prev) / 1000`, each of the four values does the case "`detected` and
      `has_est`" of the filter `one_euro` of [Smooth keypoints](smooth_keypoints.md#behaviour)
      step 7, with the input value as `z` and the params `min_cutoff`, `beta` and `d_cutoff` of
      this node.
   3. If `est` of `x1` is greater than `est` of `x2`, exchange these two estimates. Do the same
      for `y1` and `y2`. The derivatives do not move.
   4. `t_prev = t`. The output is `cx = (x1 + x2) / 2`, `cy = (y1 + y2) / 2`, `w = x2 - x1` and
      `h = y2 - y1`, from the four estimates. The rotation of the output is the rotation of the
      input. The filter `one_euro` does not change the rotation.

## Validation rules

- [ ] `V-node.smooth_boxes-1` A file must not write a param of the other filter: `previous_weight` is for the filter `ema`, and `min_cutoff`, `beta`, `d_cutoff` and `reset_after_ms` are for the filter `one_euro` ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 5).

## Implementer guidance

- The Behaviour follows skellytracker/core/temporal_processing/bbox_smoothing.py (`apply_bbox_ema`)
  and skellytracker/core/tracker/detection_stage.py (`DetectionStage._smooth_bbox`). With
  `rotation = 0`, the reference gives the same results as that code. The notes of the vector file
  give the comparison.
- Today's boxes have no rotation. The short-arc rule for `rotation` is new in this section. A linear
  mean of two angles near +π and -π gives an angle near 0, which turns the crop.
- Today, a missing box keeps the previous smoothed box in the state. The next box blends with it.
  With the filter `ema`, this section does the same (steps 2 and 4).
- The filter `one_euro` follows `apply_bbox_one_euro` of the skellytracker branch `sfn26`
  (freemocap/skellytracker at 2d356a6c41f831484251677050fafb2576193060,
  `skellytracker/core/temporal_processing/bbox_smoothing.py:38-64`): the filter on the two corners,
  the start from the input after a gap, the cleared state for a missing box and the sort of the
  corners. The step is `one_euro_step` of
  `skellytracker/core/temporal_processing/one_euro_array.py:35-49` at that commit, which has the
  formula of [Smooth keypoints](smooth_keypoints.md#behaviour) step 7. That code has no rotation.
- A filter on the centre and the size does not give the result of step 8 when `beta` is more than
  0: each corner has its own cutoff from its own derivative.
- The reference model checks `V-node.smooth_boxes-1` in `SmoothBoxesParams`. (skellytracker
  `specs/pipeline/reference/pipeline_config.py`)

## Authoring guidance

- The default `previous_weight` is 0.5.
- The defaults of the filter `one_euro` are the values of the branch `sfn26`: `min_cutoff` 3.0,
  `beta` 0.02, `d_cutoff` 1.0 and `reset_after_ms` 500. The example
  [`yolox-rtmw-wholebody`](../examples/yolox-rtmw-wholebody.pipeline.yaml) uses them
  ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) items 1 and 5).
- The filter `one_euro` uses the time between two frames. In `video`, a camera with no
  `timestamp_ms` gets its time from the run parameter `fps`
  ([Running](../running.md#behaviour) item 2). Give the real frame rate of the video.
- The output box is not clipped to the image. A caller that draws it clips it
  ([ADR-RA0E](../../../decisions/entries/RA0E-built-in-box-behaviour-of-sfn26.md) item 6).
- A larger `previous_weight` gives a steadier crop and more lag. When a person moves fast, a crop with lag
  can cut off a limb.
- Without an `associate` node, the rows have no track identity, so row `i` of two frames can be two
  persons ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). With
  `max_instances: 1`, this does not apply.

## Examples

The vector file [`node.smooth_boxes.yaml`](../vectors/node.smooth_boxes.yaml) holds the worked cases.

```yaml
- id: crop_smooth
  type: smooth_boxes
  inputs: {boxes: person.boxes}
  params: {previous_weight: 0.4}
```
