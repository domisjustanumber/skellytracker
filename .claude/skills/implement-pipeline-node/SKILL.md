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
apply.

## Inputs

- The section ID, for example `node.roi_from_points`. The section file is
  `specs/pipeline/nodes/<type>.md`.
- `<section_module>` is `node_<type>`, for example `node_roi_from_points`.

## Differences from `implement-sidecar-section`

| Step | For a node type |
|---|---|
| 1. Read the section | Also read the params model of the node type in `specs/pipeline/reference/pipeline_config.py`, and [Graph](../../../specs/pipeline/graph.md) for the ports. The front matter of a node section has only `id`, `title`, `kind`, `vectors` and `status.spec`: skip items 1 and 7 for the front matter. In item 6, read the [open work](../../../specs/pipeline/decisions/open-work.md) of the pipeline log, not the spec defects of the spec log. |
| 2. Find the evidence | The vectors are `specs/pipeline/vectors/node.<type>.yaml`. `first_of` and `concat` have named tests in `tools/tests/`, not vectors. The reference module is `specs/pipeline/reference/node_<type>.py`. An example pipeline that uses the node type is in `specs/pipeline/examples/`. A node type has no `TRACEABILITY.md` row and no `external_impl`. |
| 3. Find out if the work is blocked | An example pipeline in `specs/pipeline/examples/` is the reference example. Skip item 3: the exporter table does not name node types. |
| 4. Plan the work | The node code goes in `core/pipelines/_runtime/`. The params model moves into `core/pipelines/config.py` in stage 1.10 of the [implementation plan](../../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p). The dispatch point is the executor of `_runtime/`, not `preprocess_image`. The validator changes go in `core/pipelines/config.py`, not in `core/sidecar/model.py`. Skip item 9. |
| 5. Port or compare | From the 2.0.0 pre-release, a node proposal gives its code as `skellytracker.patch`. Follow [Patch review](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#patch-review). |
| 6. Implement and test | Add the adapter of the node to `PACKAGE_RUNNERS` of `tools/tests/test_vectors.py`. A node with named tests: run those tests on the package code. The tests for the rule IDs do not go in `test_model_validation.py`. Write their place as `for the implementer` in the plan of step 4. The `verified_against` of item 9 is in `specs/pipeline/vectors/node.<type>.yaml`. |
| 7. Update the traceability | Do only item 5. A node section has no `implemented_by`, step `status` or `tests`, and the pipeline spec has no traceability matrix. |

## Stop points

The [Stop points](../implement-sidecar-section/SKILL.md#stop-points) of `implement-sidecar-section`
apply. A node type never defines model processing. If the work needs it, stop: it is a sidecar
proposal ([Pipeline Spec Rules](../../../specs/pipeline/AGENTS.md)).
