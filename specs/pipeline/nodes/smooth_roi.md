---
id: node.smooth_roi
title: Smooth ROI
kind: node
vectors: vectors/node.smooth_roi.yaml
status: {spec: draft}
---

# Smooth ROI

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `smooth_roi` smooths the ROI of each instance row over time with an exponential moving
average (EMA). A stable crop gives more stable keypoints
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). The smoothed
ROI is usually the crop of the next frame, so a `smooth_roi` node upstream of a detector makes a
pipeline stateful ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md)
item 5).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `previous_weight` | `float` | >= 0.0, <= 1.0 | `0.5` | yes | The weight of the previous ROI: new = previous_weight × previous + (1 − previous_weight) × input. | BBoxSmoothingConfig.alpha (freemocap uses 0.4); ADR-88WQ item 4 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `rois` | input | `roi` |
| `rois` | output | `roi` |
<!-- /node-table:ports -->

- An ROI is `(cx, cy, w, h, rotation)` in source-image pixels, with `rotation` in radians
  ([Graph](../graph.md#behaviour) item 3).
- `previous_weight` is the weight of the previous output, not the weight of the input.
  `previous_weight = 0` passes the input through. `previous_weight = 1` keeps the first ROI of the
  row. Today's code names it `alpha` ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md)
  item 4).
- The output `rois` has the rows of the input. A row that is not present in the input is not present
  in the output. The `instance_score` of each row passes through unchanged.

## Behaviour

1. **Running mode.** In the running mode `image`, the output is the input, and the node keeps no
   state ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2). The
   steps that follow apply to `video` and `live`.
2. **Empty input.** When `rois` is empty, the node does not run. The output is empty and the state
   does not change ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md)
   item 6).
3. **State.** Each row `i` has its own state: the last output ROI of the row, `prev`. It is empty at
   the start.
4. **Row not present.** When row `i` of the input is not present, row `i` of the output is not
   present. The state of the row does not change.
5. **First ROI of a row.** When row `i` is present and its state is empty, the output is the input
   ROI, and `prev` becomes that ROI.
6. **Next ROIs.** When row `i` is present and has a state, with `in` the input ROI and
   `k = previous_weight`:

   ```text
   cx       = k · prev.cx + (1 - k) · in.cx
   cy       = k · prev.cy + (1 - k) · in.cy
   w        = k · prev.w  + (1 - k) · in.w
   h        = k · prev.h  + (1 - k) · in.h
   turn     = NormalizeRadians(prev.rotation - in.rotation)
   rotation = NormalizeRadians(in.rotation + k · turn)
   ```

   `NormalizeRadians` is that of [ROI from points](roi_from_points.md#behaviour), with a result in
   [-π, π). The rotation moves on the short arc between the two angles. The output is
   `(cx, cy, w, h, rotation)`, and `prev` becomes the output.
7. The `dt` of the frame and the `timestamp_ms` have no effect. In `live`, a dropped frame does not
   change the weight.

## Validation rules

None yet.

## Implementer guidance

- The Behaviour follows skellytracker/core/temporal_processing/bbox_smoothing.py (`apply_bbox_ema`)
  and skellytracker/core/tracker/detection_stage.py (`DetectionStage._smooth_bbox`). With
  `rotation = 0`, the reference gives the same results as that code. The notes of the vector file
  give the comparison.
- Today's boxes have no rotation. The short-arc rule for `rotation` is new in this section. A linear
  mean of two angles near +π and -π gives an angle near 0, which turns the crop.
- Today, a missing box keeps the previous smoothed box in the state. The next box blends with it.
  This section does the same (steps 2 and 4).

## Authoring guidance

- The default `previous_weight` is 0.5. freemocap uses 0.4.
- A larger `previous_weight` gives a steadier crop and more lag. When a person moves fast, a crop with lag
  can cut off a limb.
- Without an `associate` node, the rows have no track identity, so row `i` of two frames can be two
  persons ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). With
  `max_instances: 1`, this does not apply.

## Examples

The vector file [`node.smooth_roi.yaml`](../vectors/node.smooth_roi.yaml) holds the worked cases.

```yaml
- id: crop_smooth
  type: smooth_roi
  inputs: {rois: person.rois}
  params: {previous_weight: 0.4}
```
