---
id: node.concat
title: Concat node
kind: node
vectors: null
status: {spec: draft}
---

# Concat node

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A `concat` node joins two or more keypoint sets of one root into one keypoint set ([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). It is a glue node. The root of a keypoint set is the node that makes its instances ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

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

- The input name `*` means one or more inputs. Each input has its own name. Each input is a `keypoints` port.

## Behaviour

- Row `i` of each input joins row `i` of the output ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).
- The output has the points of each input, in the order of the keys in `inputs` in the file.
- Each point name keeps its prefix, for example `body.nose`.
- The output has the root of its inputs.
- The timing point is `run` ([ADR-Q59W](../../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).

## Validation rules

- [ ] `V-node.concat-1` Each input must have the same root: the node that makes the instances. The load fails when a `concat` node mixes roots ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) items 1 and 7).
- [ ] `V-node.concat-2` The point names of the inputs must not collide ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 7).

## Implementer guidance

- This node has a named test and no vector file ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 4).
- The host does the checks of this section at load, because the roots and the point names come from the sidecars and the MediaPipe YAML files. The reference model does not do them (`specs/pipeline/reference/pipeline_config.py`).

## Authoring guidance

None yet.

## Examples

The keypoints of a body model and of a hand model join into one set. Both inputs have the root `person`, the detector that makes the instances.

```yaml
  - id: all_points
    type: concat
    inputs:
      body: body.keypoints
      hands: hands.keypoints
```
