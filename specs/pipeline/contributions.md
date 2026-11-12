# Pipeline contributions

This file uses ASD-STE100 Simplified Technical English.

This file is the workflow to add a pipeline file or to change a node type of the pipeline spec. It
is the same for an exporter agent and for a human contributor. It is thin: the bundle rules are in
[Hand-over bundles](../model-sidecar/model-addition-workflow/hand-over.md), and this file links to
their headings ([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md) item 7;
[ADR-271H](../../decisions/entries/271H-pipeline-bundles.md)).

## Choose the path

| You want to | Send | Template |
|---|---|---|
| Add a pipeline that uses the current node types | A `pipeline` bundle | [Pipeline intake](templates/pipeline-intake.md) |
| Add a node type, or change the params, the ports or the behaviour of a node type | A `proposal` bundle with `node.<type>` sections | [Node proposal](templates/node-proposal.md) |
| Change how a model is preprocessed, run or decoded | A sidecar proposal, not a node proposal | [Change proposal](../model-sidecar/templates/change-proposal.md) |

The pipeline spec never defines model processing. A detector node only refers to a sidecar
([Pipeline Spec Rules](AGENTS.md)).

## Add a pipeline

1. Read the [pipeline spec](README.md): [Pipeline file](file.md), [Graph](graph.md),
   [Outputs](outputs.md) and the section of each node type that you use.
2. Write `<pipeline_id>.pipeline.yaml`. Set `source.name` to the name of your repo, in lower case.
3. Give each `detector` node its `key` and its `sidecar_sha256`: the SHA-256 of the bytes of the
   sidecar. The model can be landed, or in a `model` bundle that you name in `depends_on`. It can be
   a model of another exporter.
4. If the pipeline needs a node change, send the node proposal first. Name it in `depends_on`.
5. Write `pipeline.md` from the [pipeline intake template](templates/pipeline-intake.md).
6. Pack the bundle as [Pack a version](../model-sidecar/model-addition-workflow/hand-over.md#pack-a-version)
   gives. [Pipeline bundles](../model-sidecar/model-addition-workflow/hand-over.md#pipeline-bundles)
   gives the rules of the kind.

Before stage 1.10 of the [implementation plan](../sidecar-implementation-plan.md), an accepted
pipeline lands as an example in `specs/pipeline/examples/`. After stage 1.10, it lands in
`core/model_zoo/pipelines/`.

## Change a node type

1. Read [Proposal forms](../model-sidecar/model-addition-workflow/hand-over.md#proposal-forms) and
   run `list`. A node section has an owner, as a sidecar section has
   ([Section owner](../model-sidecar/model-addition-workflow/hand-over.md#section-owner)).
2. Write `proposal.md` from the [node proposal template](templates/node-proposal.md). `sections`
   lists only `node.<type>` sections. A node change that comes with a sidecar change is two
   proposals, linked with `depends_on`.
3. A glue node with an algorithm gives `reference/node_<type>.py` and `vectors/node.<type>.yaml`.
   [Reference implementations](../model-sidecar/model-addition-workflow/reference-implementations.md)
   gives the rules of a reference module. Run `fill` of `tools/make_vectors.py` before `pack`.
4. Pack the bundle. The record is `specs/pipeline/proposals/<slug>/`, and the entry is in the
   [pipeline log](decisions/README.md).

From the 2.0.0 pre-release, a node change of the package code comes as `skellytracker.patch`
([Patches](../model-sidecar/model-addition-workflow/hand-over.md#patches)).

## What skellytracker does

A skellytracker session lands a pipeline bundle or an accepted node proposal with the skill
`change-pipeline-spec`. It implements a node type with the skill `implement-pipeline-node`. The
[States](../model-sidecar/model-addition-workflow/hand-over.md#states) and the
[Responses](../model-sidecar/model-addition-workflow/hand-over.md#responses) are those of the
model addition workflow.
