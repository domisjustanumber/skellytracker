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
a gate passes the box from the points of the previous frame only when the flag of a
`redetect_trigger` node is false
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6; [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 9).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `mode` | `Literal['is_empty', 'is_present', 'score_above', 'is_true', 'is_false']` |  | required | no | Pass `value` when `condition` is empty, is present, or has a score greater than `threshold` (a boxes or keypoints condition), or when the flag `condition` is true or false. | ADR-7NY2 item 6; ADR-9HTX item 9 |
| `threshold` | `float \| None` | >= 0.0 | `null` | yes | The score threshold of the mode `score_above`. | ADR-7NY2 item 6; ADR-88WQ item 6 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `value` | input | `boxes`, `keypoints` |
| `condition` | input | `boxes`, `keypoints`, `flag` |
| `value` | output | `boxes`, `keypoints` |
<!-- /node-table:ports -->

- `value` takes a `boxes` or a `keypoints` port. `condition` takes a `boxes`, a `keypoints` or a
  `flag` port. The output `value` gets its port type as [Graph](../graph.md#behaviour) item 4
  gives. A gate never passes an image or a flag ([ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) items 4 and 9).
- An instance port is a port of the type `boxes` or `keypoints`. It has one row for each
  instance ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). A
  row is present or empty.
- A port value is empty when it has no value, for example an `@prev` value on the first frame or
  the output of a node that did not run. A value of an instance port with no present row is also
  empty.
- **Score of a row.** The mode `score_above` uses the score of a present row of `condition`:
  - `boxes`: the `instance_score` of the row ([ADR-2RWC](../../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)).
  - `keypoints`: the mean `score` of the points of the row whose x and y are not NaN. If each point
    of the row is NaN, the score is 0. A score has no upper bound
    ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md) item 6).
- **Flag condition.** A `condition` of the port type `flag` takes only the modes `is_true` and
  `is_false` (`V-node.gate-4`). The modes `is_empty`, `is_present` and `score_above` need a
  `condition` that is not a flag (`V-node.gate-2`; [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 9).

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
3. **Row by row.** When `condition` is not a flag, `value` and `condition` are both instance ports.
   The node then tests each row `i` alone. The list of step 2 holds row `i` of `condition` when that row is present, else it is
   empty. When `condition` has no value, each row of `condition` is empty. Row `i` of the output is
   row `i` of `value` when row `i` of `value` is present and the test passes. Else row `i` of the
   output is empty. The output has one row for each row of `value`.
4. **Flag.** When `condition` is a flag, the node does one test for the frame. The mode `is_true`
   passes when the flag is true. The mode `is_false` passes when the flag is false. If the test
   passes, the output is `value`, unchanged. Else the output is empty. A flag is never empty
   ([Graph](../graph.md#behaviour) item 5; [ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 9).

## Validation rules

- [ ] `V-node.gate-1` The mode `score_above` needs `threshold`, and the other modes have none.
- [ ] `V-node.gate-2` The modes `is_empty`, `is_present` and `score_above` need a `condition` of the port type `boxes` or `keypoints`. The host checks this at load, from the port type of the connected output.
- [ ] `V-node.gate-3` When `value` and `condition` are both instance ports, they must have the same number of rows (`max_instances`). The host checks this at load.
- [ ] `V-node.gate-4` The modes `is_true` and `is_false` need a `condition` of the port type `flag`. The host checks this at load, from the port type of the connected output.

## Implementer guidance

- The score test uses `>`, as the MediaPipe `ThresholdingCalculator` does. (MediaPipe-Exporter
  [`docs/mediapipe-whole-body.md:155-157`](https://github.com/domisjustanumber/MediaPipe-Exporter/blob/8f708a1ddecd8e035de15a5a9a7b652af035a58a/docs/mediapipe-whole-body.md#L155-L157))
- An empty row keeps its place in the output. The shapes of the output do not change from frame to
  frame ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1).
- A missing point has NaN coordinates and the score 0
  ([Decoded keypoints](../../model-sidecar/post/keypoint/schema.md#decoded-keypoints)). The keypoint
  score of the row does not count it.

## Authoring guidance

- A gate does not stop a detector. To run a detector only on some frames, connect a flag to its
  `run_if` input ([Node: ONNX model](onnx_model.md#fields)).
- To use the box from the points of the previous frame only on a frame with no new detection, gate
  it with `mode: is_false` on the flag `redetect` of a `redetect_trigger` node. Join the two box
  paths with `first_of`. The built-in `yolox-rtmw-wholebody` does this.
- The keypoint score is a mean over all points of the row. A row with many low-score points
  can fail `score_above` when its important points are visible. Gate on a smaller keypoint set when
  this matters.
- The mode `score_above` on a `boxes` condition tests the instance score of each box: for a
  detector box, the detection score.

## Examples

The vector file [`node.gate.yaml`](../vectors/node.gate.yaml) holds the worked cases.

```yaml
- id: carried_box
  type: gate
  inputs: {value: points_box.boxes, condition: trigger.redetect}
  params: {mode: is_false}
```
