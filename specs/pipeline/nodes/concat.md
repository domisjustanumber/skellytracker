---
id: node.concat
title: Concat node
kind: node
vectors: vectors/node.concat.yaml
status: {spec: draft}
---

# Concat node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `concat` node joins two or more keypoint sets of one instance source into one keypoint set ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. The instance source of a keypoint set is the node that makes its instance rows ([Graph](../graph.md#behaviour) item 8; [ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). To join keypoint sets of two instance sources, use [`merge`](merge.md).

## Fields

<!-- node-table:params -->
This node has no parameters.
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `*` | input | `keypoints` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- `inputs` is a list of one or more `keypoints` port references. The input name `*` in the ports table stands for each item of the list. The items have no labels.

## Behaviour

- **Empty inputs.** An empty input does not stop the node. This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows. The columns of an empty input are missing points in each row: x and y are NaN, z of a `3d` output is NaN, and the score and the `raw_score` are 0 ([ADR-PX6Z](../../../decisions/entries/PX6Z-keypoint-raw-score-in-the-pipeline-result.md); [ADR-JHB3](../../../decisions/entries/JHB3-keypoints-xy-and-z-and-image-width-and-height.md)). The output schema of the input gives its point names, so the shapes do not change. When each input is empty, the output is empty. For example, a body row with no left-hand ROI still gives the body points, and the left-hand columns are missing.
- The `instance_score` and the `track_ids` of row `i` come from the first input whose row `i` is present. A row with no present input row is a padding row, with the padding values of [Outputs](../outputs.md#fields) ([ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 1).
- Row `i` of each input joins row `i` of the output ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1). Row `i` of the output is present when row `i` of an input is present.
- The output has the points of each input, in the order of the list. A consumer finds a point by its name, not by its column.
- Each point name keeps its group, for example `body/nose`. The output has the groups of each input, in the order of the list ([Graph](../graph.md#behaviour) item 7; [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). The node never replaces a point (`V-node.concat-2`).
- The output has the instance source and the geometry of its inputs.
- The timing span is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1; [ADR-9PDQ](../../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).

## Validation rules

- [ ] `V-node.concat-1` Each input must have the same instance source: the node that makes the instance rows. The load fails when a `concat` node mixes instance sources ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 1 and 7).
- [ ] `V-node.concat-2` The point names of the inputs must not collide ([ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7).
- [ ] `V-node.concat-3` Each input must have the same `geometry` ([Outputs](../outputs.md#fields)). The load fails when a `concat` node mixes `2d` and `3d` inputs.

## Implementer guidance

- The vector file `specs/pipeline/vectors/node.concat.yaml` holds the cases of this node. `tools/make_vectors.py` runs the reference implementation `specs/pipeline/reference/node_concat.py` on them ([ADR-Y753](../../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 4).
- The host does the checks of this section at load, because the instance sources, the point names and the geometries come from the sidecars and the MediaPipe YAML files. The reference model does not do them (`specs/pipeline/reference/pipeline_config.py`).

## Authoring guidance

- To follow the holistic order, list the inputs as body, right hand, left hand and face.

## Examples

The keypoints of a body model and of a hand model join into one set. Both inputs have the instance source `person`, the detector that makes the instance rows.

```yaml
  - id: all_points
    type: concat
    inputs: [body.keypoints, right_hand.keypoints, left_hand.keypoints]
```
