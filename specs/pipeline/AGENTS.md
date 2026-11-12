# Pipeline Spec Rules

These rules apply to work in skellytracker on the pipeline spec: the pipeline config format, its
node types, its examples and its reference implementations
([ADR-3SF2](../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)).
The root [`AGENTS.md`](../../AGENTS.md) also applies.
The decision log of the pipeline spec is in [`decisions/`](decisions/README.md). Read it with the
root log.

- The pipeline spec is a draft. The decisions of the design are in the root log: start at
  [ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md).
- The pipeline spec never defines model processing. Preprocessing, inference and postprocessing of a
  model are in the [sidecar spec](../model-sidecar/README.md). A change of model processing is a
  sidecar proposal.
- The pipeline spec links to a sidecar definition. It must not restate it
  ([ADR-88WQ](../../decisions/entries/88WQ-sidecar-vocabulary.md) item 7).
- The Pydantic reference model in `reference/` is the source of the JSON Schema and of the node
  tables. Do not edit the schema or a node table by hand. Run the tool that makes them.
- Each node type has one params model with a type, a range, a default, a description and `live`
  for each param, and its ports.
- The glue nodes are a closed set. A pipeline file runs no user code
  ([ADR-AD33](../../decisions/entries/AD33-bundles-are-untrusted-input.md)). A new node type is a
  spec change.
- A pipeline file or a node change comes through [Pipeline contributions](contributions.md). The
  skill [`change-pipeline-spec`](../../.claude/skills/change-pipeline-spec/SKILL.md) lands it
  ([ADR-271H](../../decisions/entries/271H-pipeline-bundles.md)).
- In the spec-build stage, do not change a file under `skellytracker/`.
- An entry whose files are all in `specs/pipeline/` goes in [`decisions/`](decisions/README.md). An
  entry with files in another module goes in the [root log](../../decisions/README.md).
