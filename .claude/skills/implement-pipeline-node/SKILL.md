---
name: implement-pipeline-node
description: Use this skill in skellytracker when you implement a node type of the pipeline spec in the package code, in the implementation stage. Use it also when you plan that work.
---

# Implement a pipeline node

This skill uses ASD-STE100 Simplified Technical English.

This skill implements one node type of the [pipeline spec](../../../specs/pipeline/README.md) in
the skellytracker package. It runs only in skellytracker. It has the steps of
[`implement-sidecar-section`](../implement-sidecar-section/SKILL.md), with the pipeline paths. This
file gives only the differences
([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 7).

## Stage

The [Stage](../implement-sidecar-section/SKILL.md#stage) rules of `implement-sidecar-section`
apply. In the spec-build stage, do only steps 1 to 4. Report the plan. Then stop.

## Inputs

- The section ID, for example `node.roi_from_points`. The section file is
  `specs/pipeline/nodes/<type>.md`.
- `<section_module>` is `node_<type>`, for example `node_roi_from_points`.

## Differences from `implement-sidecar-section`

| Step | For a node type |
|---|---|
| 1. Read the section | Also read the params model of the node type in `specs/pipeline/reference/pipeline_config.py`, and [Graph](../../../specs/pipeline/graph.md) for the ports. |
| 2. Find the evidence | The vectors are `specs/pipeline/vectors/node.<type>.yaml`. `first_of` and `concat` have named tests in `tools/tests/`, not vectors. The reference module is `specs/pipeline/reference/node_<type>.py`. An example pipeline that uses the node type is in `specs/pipeline/examples/`. |
| 4. Plan the work | The node code goes in `core/pipelines/_runtime/`. The params model moves into `core/pipelines/config.py` in stage 1.10 of the [implementation plan](../../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p). |
| 5. Port or compare | From the 2.0.0 pre-release, a node proposal gives its code as `skellytracker.patch`. Follow [Patch review](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#patch-review). |
| 6. Implement and test | Add the adapter of the node to `PACKAGE_RUNNERS` of `tools/tests/test_vectors.py`. A node with named tests: run those tests on the package code. |
| 7. Update the traceability | Write `implemented_by`, `status` and `tests` in the front matter of the node section file. |

## Stop points

The [Stop points](../implement-sidecar-section/SKILL.md#stop-points) of `implement-sidecar-section`
apply. A node type never defines model processing. If the work needs it, stop: it is a sidecar
proposal ([Pipeline Spec Rules](../../../specs/pipeline/AGENTS.md)).
