---
id: node.first_of
title: First-of node
kind: node
vectors: null
status: {spec: draft}
---

# First-of node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `first_of` node gives the first of its inputs that is not empty ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. A pipeline uses it to select one of two or more sources of the same value, for example a new detection or the ROI of the previous frame.

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

- The input name `*` means one or more inputs. Each input has its own name. The names have no meaning for the node.
- The output `value` has the port type of the inputs.

## Behaviour

- The node examines its inputs in the order of the keys in `inputs` in the file. It gives the first input that is not empty.
- When all inputs are empty, the output is empty.
- An `@prev` input is empty on the first frame, and in the running mode `image` ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 4; [ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 2).
- The timing point is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.first_of-1` All inputs must have the same port type. An input of the port type `any` agrees with each port type.

## Implementer guidance

- This node has a named test and no vector file ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 4).
- The loader must keep the order of the keys of `inputs` as the file gives it.

## Authoring guidance

- Put the preferred source first in `inputs`.

## Examples

The ROIs of the current frame come from a new detection. When the detector did not run, they come from the keypoints of the previous frame.

```yaml
  - id: rois
    type: first_of
    inputs:
      detected: person.rois
      tracked: from_points.rois@prev
```
