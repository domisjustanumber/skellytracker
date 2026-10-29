# Phase 3: what skellytracker does next

You do not do phase 3. A skellytracker session does it. The user decides.

1. **A model with the verdict `describes`.** One non-spec PR (documentation only) in skellytracker
   adds the sidecar as a spec example (under `specs/model-sidecar/examples/`), with its provenance record
   (in `specs/model-sidecar/inventory.yaml`) and any new guidance from the intake. The procedure is
   [Reference examples](reference-examples.md) in this workflow.
   Its preconditions: your writer code writes the sidecar itself (not by hand), at `vNEXT`, with no
   legacy-only fields; your checks pass; parity passes for at least one size. The
   procedure copies your sidecar byte for byte. If your sidecar breaks a spec rule, fix your writer code
   or write a change proposal. Nobody corrects the example by hand. An accepted spec change can make
   an example invalid. Then its content commit makes a spec-forced edit of the example
   ([When a spec change makes an example invalid](reference-examples.md#when-a-spec-change-makes-an-example-invalid);
   [ADR-KDBD](../../../decisions/KDBD-change-classes-and-spec-forced-edits.md)).
2. **A proposal.** skellytracker copies the current version of your proposal bundle byte for byte
   to `specs/model-sidecar/proposals/<slug>/`. It records it as a short decision entry with status
   `proposed`. To change the proposal, pack a new version. skellytracker then replaces the copy in
   full and keeps the same entry ([Versions](hand-over.md#versions);
   [ADR-FADS](../../../decisions/FADS-hand-over-bundles-in-intakes.md)). Each response gives the state
   of your bundle ([Responses](hand-over.md#responses)). The user accepts or rejects the proposal.
   After acceptance:
   - A content PR adds the normative text, the changelog row, the vectors and the reference
     implementation. It sets the decision entry to `accepted` (if it is not accepted yet). It also
     makes the spec-forced edit of each example that the change makes invalid
     ([ADR-KDBD](../../../decisions/KDBD-change-classes-and-spec-forced-edits.md)).
   - A non-spec PR (documentation only) adds the guidance, the implementation proposal (as
     implementer guidance and an open-work item), the example and its provenance record. It
     adds the scope-list row of the model, if it is new
     ([ADR-YNX0](../decisions/YNX0-vnext-scope-list.md)).
   - When skellytracker implements the spec, an implementation PR adds the code.
3. Then you write the sidecar with the new fields, and you finish phase 1 for the model.
4. Each new content PR goes on top of the skellytracker PR stack. It never goes in a move PR or a
   rewording PR. If the rewording PR of the section is lower in the stack, a follow-up rewording PR
   covers the new text. A skellytracker session lands a reference implementation as a non-spec PR on
   top of the stack.
5. In the spec-build stage, no file under `skellytracker/` changes. The only exception is a test fix
   in `skellytracker/tests/`, with one PR for each root cause. A code defect is reported, and its fix
   waits for the implementation stage. Docs, tools, vectors and reference implementations outside
   `skellytracker/` can change.
