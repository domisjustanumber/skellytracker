# Open work

This file holds the open work of the [decision log](README.md) of the pipeline spec. The
implementation-stage work is in the
[implementation plan](../../sidecar-implementation-plan.md). The other repository state is in the
root [open-work.md](../../../decisions/open-work.md).

## Draft spec

- **The draft.** Write the draft spec in `specs/pipeline/`: the Pydantic reference model and the
  JSON Schema that a tool makes from it, the node tables, the `V-` rules, the examples, the glue
  reference implementations and their vectors
  ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)).
- **Vector tool.** `tools/make_vectors.py` maps the section prefix `node.` to `specs/pipeline/`,
  with tests. This comes with the draft, before the glue vectors.
- **Node workflow.** After the draft lands: one workflow file and one node-proposal template in
  `specs/pipeline/`, the landing skill `change-pipeline-spec`, and the `node.` mapping of
  `tools/intake_bundle.py` ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)
  item 5).
