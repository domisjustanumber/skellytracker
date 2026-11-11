# Open work

This file holds the open work of the [decision log](README.md) of the pipeline spec. The
implementation-stage work is in the
[implementation plan](../../sidecar-implementation-plan.md). The other repository state is in the
root [open-work.md](../../../decisions/open-work.md).

## Draft spec

- **Named tests.** `first_of` and `concat` have no vectors. Each needs a named test in
  `tools/tests/` ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)
  item 4).
- **Node workflow.** After the draft lands: one workflow file and one node-proposal template in
  `specs/pipeline/`, the landing skill `change-pipeline-spec`, and the `node.` mapping of
  `tools/intake_bundle.py` ([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)
  item 5).
