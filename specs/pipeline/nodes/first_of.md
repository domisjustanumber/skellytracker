---
id: node.first_of
title: First-of node
kind: node
vectors: vectors/node.first_of.yaml
status: {spec: draft}
---

# First-of node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `first_of` node gives the first of its inputs that is not empty ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. A pipeline uses it to select one of two or more sources of the same value, for example a new detection or the box of the previous frame.

## Fields

<!-- node-table:params -->
This node has no parameters.
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `*` | input | `any` |
| `value` | output | `any` |
<!-- /node-table:ports -->

- `inputs` is a list of one or more port references. The input name `*` in the ports table stands for each item of the list. The items have no labels.
- The output `value` has the port type of the inputs ([Graph](../graph.md#behaviour) item 4).

## Behaviour

- The node examines its inputs in the order of the list. The order is the priority. It gives the first input that is not empty.
- When all inputs are empty, the output is empty.
- An empty input does not stop the node. This is a rule of the node, as [Graph](../graph.md#behaviour) item 6 allows.
- An `@prev` input is empty on the first frame, and in the running mode `image` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 4; [ADR-ZYS9](../../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2).
- The output has the instance source of the inputs ([Graph](../graph.md#behaviour) item 8).
- The timing span is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1; [ADR-9PDQ](../../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).

## Validation rules

- [ ] `V-node.first_of-1` All inputs must have the same port type. An input of the port type `any` takes the type of its own inputs ([Graph](../graph.md#behaviour) item 4). An `@prev` input `x@prev` has the port type of `x`, and the rule also compares it ([ADR-97X9](../../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 5).
- [ ] `V-node.first_of-2` When the inputs are instance ports (`boxes` or `keypoints`), they must have one instance source. When they are `keypoints` ports, they must also have the same groups ([Graph](../graph.md#behaviour) item 7; [ADR-4MP6](../../../decisions/entries/4MP6-pipeline-point-groups-and-canonical-form.md)). The host checks this at load.

## Implementer guidance

- The vector file `specs/pipeline/vectors/node.first_of.yaml` holds the cases of this node. `tools/make_vectors.py` runs the reference implementation `specs/pipeline/reference/node_first_of.py` on them ([ADR-Y753](../../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 4).
- The reference model checks `V-node.first_of-1` in `check_structure`. (skellytracker `specs/pipeline/reference/pipeline_config.py`)

## Authoring guidance

- Put the preferred source first in the list.

## Examples

The boxes of the current frame come from a new detection. When the detector did not run, they come from the keypoints of the previous frame.

```yaml
  - id: boxes
    type: first_of
    inputs: [person.boxes, from_points.boxes@prev]
```
