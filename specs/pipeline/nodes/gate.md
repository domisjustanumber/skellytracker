---
id: node.gate
title: Gate
kind: node
vectors: vectors/node.gate.yaml
status: {spec: draft}
---

# Gate

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `gate` passes `value` or gives an empty output. A test on `condition` decides. For example,
a gate sends the image to a person detector only when the keypoints of the previous frame are empty
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `mode` | `Literal['is_empty', 'is_present', 'score_above']` |  | required | no | Pass `value` when `condition` is empty, is present, or has a score greater than `threshold`. | ADR-7NY2 item 6 |
| `threshold` | `float \| None` | >= 0.0 | `null` | yes | The score threshold of the mode `score_above`. | ADR-7NY2 item 6; ADR-88WQ item 6 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `value` | input | `any` |
| `condition` | input | `any` |
| `value` | output | `any` |
<!-- /node-table:ports -->

- `value` and `condition` take each port type. The output `value` has the port type of the input
  `value`.
- An instance port is a port of the type `roi`, `keypoints` or `detections`. It has one row for each
  instance ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1). A
  row is present or empty.
- A port value is empty when it has no value, for example an `@prev` value on the first frame or
  the output of a node that did not run. A value of an instance port with no present row is also
  empty.
- **Score of a row.** The mode `score_above` uses the score of a present row of `condition`:
  - `detections`: the `score` of the row.
  - `keypoints`: the mean `score` of the points of the row whose x and y are not NaN. If each point
    of the row is NaN, the score is 0. A score has no upper bound
    ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 6).
  - Other port types have no score (`V-node.gate-2`).

## Behaviour

1. If `value` is empty, the node does not run. The output is empty
   ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). An empty
   `condition` does not stop the node. This is a rule of the node, as
   [Graph](../graph.md#behaviour) item 6 allows, because the mode `is_empty` tests for an empty
   `condition`.
2. The test of a list of present rows of `condition`:
   - `is_empty`: the list has no row.
   - `is_present`: the list has one row or more.
   - `score_above`: the list has a row whose score is greater than `threshold`. The test is strict,
     as each score comparison of the sidecar spec
     ([Selection behaviour](../../model-sidecar/post/object/decode.md#selection-behaviour)).
3. **Row by row.** If `value` and `condition` are both instance ports, the node tests each row `i`
   alone. The list of step 2 holds row `i` of `condition` when that row is present, else it is
   empty. When `condition` has no value, each row of `condition` is empty. Row `i` of the output is
   row `i` of `value` when row `i` of `value` is present and the test passes. Else row `i` of the
   output is empty. The output has one row for each row of `value`.
4. **One test.** Else the node does one test. The list of step 2 holds each present row of
   `condition` when `condition` is an instance port. It holds one row when `condition` is a value of
   another port type, and no row when `condition` has no value. If the test passes, the output is
   `value`, unchanged, also its `instance_score`. Else the output is empty.

## Validation rules

- [ ] `V-node.gate-1` The mode `score_above` needs `threshold`, and the other modes have none.
- [ ] `V-node.gate-2` The mode `score_above` needs a `condition` of the port type `detections` or `keypoints`. The host checks this at load, from the port type of the connected output.
- [ ] `V-node.gate-3` When `value` and `condition` are both instance ports, they must have the same number of rows (`max_instances`). The host checks this at load.

## Implementer guidance

- The score test uses `>`, as the MediaPipe `ThresholdingCalculator` does. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:155-157`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L155-L157))
- An empty row keeps its place in the output. The shapes of the output do not change from frame to
  frame ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
- A missing point has NaN coordinates and the score 0
  ([Decoded keypoints](../../model-sidecar/post/keypoint/schema.md#decoded-keypoints)). The keypoint
  score of the row does not count it.

## Authoring guidance

- To run a detector only when tracking stops, gate the image with `mode: is_empty` on the keypoints
  of the previous frame (`<node>.keypoints@prev`). Join the two ROI paths with `first_of`.
- The keypoint score is a mean over all points of the row. A row with many low-score points
  can fail `score_above` when its important points are visible. Gate on a smaller keypoint set when
  this matters.
- The mode `score_above` on a `roi` condition is a load error (`V-node.gate-2`). Gate on the
  keypoints or the detections that made the ROI.

## Examples

The vector file [`node.gate.yaml`](../vectors/node.gate.yaml) holds the worked cases.

```yaml
- id: detect_when_lost
  type: gate
  inputs: {value: frame.image, condition: body.keypoints@prev}
  params: {mode: is_empty}
```
