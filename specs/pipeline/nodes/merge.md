---
id: node.merge
title: Merge node
kind: node
vectors: null
status: {spec: draft}
---

# Merge node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `merge` node joins the keypoints of a `source` to the keypoints of a `target` with another instance source. For example, a hand detector finds hands in the whole image, and a merge puts each hand row in the slot of the nearest body wrist. The output keeps the instance rows of the target ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. Use [`concat`](concat.md) for keypoint sets of one instance source.

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `slots` | `dict[str, str]` | length >= 1 | required | no | Slot name to the target point that anchors the slot, for example `left_hand: body.left_wrist`. | ADR-7NY2 item 6 |
| `source_anchor` | `str` |  | required | no | The point of `source` that the node compares with the slot anchors, for example `hand.wrist`. | ADR-7NY2 item 6 |
| `max_distance` | `float \| None` | > 0.0 | `null` | yes | The largest anchor distance, as a part of the diagonal of the box around the present points of the target row. Empty: no limit. | ADR-7NY2 item 6 |
| `map` | `dict[str, str]` |  | `{}` | no | Target point to slot column `<slot>.<point>`. A present slot point replaces the target point. | ADR-7NY2 item 6 |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `target` | input | `keypoints` |
| `source` | input | `keypoints` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- `target` and `source` are `keypoints` ports. `source` can have any instance source and any `I` ([Graph](../graph.md#behaviour) item 8).
- `slots` maps each slot name to its anchor: a point name of `target`. A slot name is a name. It is the prefix of the columns of that slot.
- `source_anchor` is a point name of `source`. The node compares its position with the slot anchors.
- `max_distance` is a part of the diagonal of the axis-aligned box around the present points of the target row. Empty: the distance has no limit.
- `map` maps a target point name to a slot column `<slot>.<point>`. A present slot point replaces the target point.
- The node adds one column set for each slot, in the order of `slots`. For each point name `<prefix>.<point>` of `source`, in its order, the slot `<slot>` adds the column `<slot>.<point>`. For example, the slot `left_hand` and the source point `hand.wrist` give the column `left_hand.wrist`.

## Behaviour

1. **Empty inputs.** If `target` is empty, the node does not run. The output is empty. An empty `source` does not stop the node. This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows: each slot column is then missing.
2. **Present points.** A point is present when its x and its y are not NaN.
3. **Match.** The node makes a list of candidate pairs. A pair is one present row `j` of `source` and one slot `k` of one present row `i` of `target`, when the `source_anchor` of row `j` and the anchor of slot `k` in row `i` are both present. For each pair:

   ```text
   distance = sqrt((x_source - x_slot)² + (y_source - y_slot)²)
   ```

   When `max_distance` is set, the node drops each pair with `distance > max_distance · diagonal`. `diagonal` is the diagonal of the axis-aligned box around the present points of target row `i`. The node then sorts the pairs by ascending distance. A tie goes to the lower source row, then to the lower target row, then to the earlier slot of `slots`. In this order, the node keeps a pair when its source row and its slot of row `i` have no pair yet. Thus each source row goes to at most one slot, and each slot of each target row gets at most one source row.
4. **Slot columns.** For a kept pair, the columns of slot `k` in row `i` hold the points of source row `j`: x, y, z and score. A slot column with no kept pair is missing: x, y and z are NaN and the score is 0.
5. **Map.** For each entry `target point: slot column` of `map`, in each row `i`: when the slot column is present, the target point gets its x, y, z and score. Else the target point does not change. The anchors of step 3 are the target points before this step.
6. **Output.** The output has the columns of `target`, then the slot columns. It has the rows, the `present` flags, the `instance_score`, the `track_ids`, the instance source, the `I` and the geometry of `target`. A target row that is not present stays a padding row.
7. The timing point is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.merge-1` Each slot name must be a name. A slot column `<slot>.<point>` must not be a point name of `target`. The host checks the columns at load.
- [ ] `V-node.merge-2` Each value of `slots` and each key of `map` must be a point name of `target`. `source_anchor` must be a point name of `source`. Each value of `map` must be a slot column of the node. The reference model checks that the prefix of each value of `map` is a slot name. The host checks the other names at load.
- [ ] `V-node.merge-3` `target` and `source` must have the same `geometry` ([Outputs](../outputs.md#fields)). The host checks this at load.

## Implementer guidance

- This node has a named test and no vector file: `tools/tests/test_pipeline_glue_nodes.py` runs the reference implementation `specs/pipeline/reference/node_merge.py` ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 4).
- The match is greedy, not an optimal assignment.

## Authoring guidance

- To add a face from a face detector, chain a second `merge` after the first one, with the first merge as `target`.
- Without `max_distance`, a source row far from each slot still gets the nearest free slot. Set `max_distance` when the source can find an object of another person.
- `map` with the wrist points replaces the body wrists with the hand wrists. Leave out `map` to keep the body points.

## Examples

A body model with one person, and a hand detector with two hands, as in the example [`rtmpose-hand-detector`](../examples/rtmpose-hand-detector.pipeline.yaml):

```yaml
  - id: body_hands
    type: merge
    inputs: {target: body.keypoints, source: hand.keypoints}
    params:
      slots: {right_hand: body.right_wrist, left_hand: body.left_wrist}
      source_anchor: hand.wrist
      map: {body.right_wrist: right_hand.wrist, body.left_wrist: left_hand.wrist}
```
