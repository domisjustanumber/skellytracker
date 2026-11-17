---
id: node.flag_when
title: Flag-when node
kind: node
vectors: vectors/node.flag_when.yaml
status: {spec: draft}
---

# Flag-when node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `flag_when` node makes a `flag` from a `boxes` or a `keypoints` value: true or false, for each camera on each frame ([ADR-9HTX](../../../decisions/entries/9HTX-pipeline-node-and-port-redesign.md) item 8). Connect the flag to the input `run_if` of a model node, or to the `condition` of a [`gate`](gate.md) with the mode `is_true` or `is_false`. It is a glue node.

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Set during run | Description | Source |
|---|---|---|---|---|---|---|
| `mode` | `Literal['is_present', 'is_empty', 'score_above']` |  | required | no | The test on all present rows of `value`, as step 2 of `gate`: `is_empty`, `is_present` or `score_above`. | ADR-9HTX item 8 |
| `threshold` | `float \| None` | >= 0.0 | `null` | yes | The score threshold of the mode `score_above`. | ADR-9HTX item 8 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `value` | input | `boxes`, `keypoints` |
| `flag` | output | `flag` |
<!-- /node-table:ports -->

- `value` is required, but an empty `value` does not stop the node (Behaviour step 1).
- The **score of a row** is as the [`gate`](gate.md#fields) gives it: the `instance_score` of a `boxes` row, and the mean score of the present points of a `keypoints` row.

## Behaviour

1. The node runs on each frame. It reads an empty `value`, so an empty `value` does not stop it. This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows.
2. The node does one test for the frame, on the list of all present rows of `value`, with the test of [`gate`](gate.md#behaviour) step 2:
   - `is_empty`: the list has no row.
   - `is_present`: the list has one row or more.
   - `score_above`: the list has a row whose score is greater than `threshold`. The test is strict.
3. The output `flag` is true when the test passes, else false. A flag is never empty ([Graph](../graph.md#behaviour) item 5).
4. The node keeps no state. An `@prev` input makes the pipeline stateful, as each `@prev` input does ([Running](../running.md#behaviour) item 5). In the running mode `image`, each `@prev` value is empty, so the mode `is_empty` on an `@prev` value gives true.
5. The timing span is `run`.

## Validation rules

- [ ] `V-node.flag_when-1` The mode `score_above` needs `threshold`, and the other modes have none. The reference model checks this rule.

## Implementer guidance

- The vector file `specs/pipeline/vectors/node.flag_when.yaml` holds the cases of this node. `tools/make_vectors.py` runs the reference implementation `specs/pipeline/reference/node_flag_when.py` on them.

## Authoring guidance

- To run a detector only when the previous frame has no person, test the keypoints of the previous frame with `is_empty`. On frame 0 the `@prev` value is empty, so the detector runs.
- To pass a value only on a frame with a flag, use [`gate`](gate.md) with the flag as its `condition`.

## Examples

Detect when lost:

```yaml
  - id: lost
    type: flag_when
    inputs: {value: body.keypoints@prev}
    params: {mode: is_empty}
  - id: person
    type: onnx_model
    inputs: {image: frame.image, run_if: lost.flag}
    params: {key: yolox-person@openmmlab-exporter, size: m}
```
