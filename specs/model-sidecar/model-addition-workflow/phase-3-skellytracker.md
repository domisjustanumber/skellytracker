# Phase 3: what skellytracker does next

You do not do phase 3. A skellytracker session does it. The user decides.

1. **A model with the verdict `describes`.** One non-spec PR (documentation only) in skellytracker
   adds the sidecar as a spec example (under `specs/model-sidecar/examples/`), with its provenance record
   (in `specs/model-sidecar/inventory.yaml`) and any new guidance from the intake. The procedure is
   "Reference examples" in `../freemocap/skellytracker/specs/sidecar-implementation-plan.md`.
   Its preconditions: your writer code writes the sidecar itself (not by hand), at `vNEXT`, with no
   legacy-only fields; your checks pass; parity passes for at least one size. The
   procedure copies your sidecar byte for byte. If your sidecar breaks a spec rule, fix your writer code
   or write a change proposal. Nobody corrects the example by hand.
2. **A proposal.** skellytracker copies it to `specs/model-sidecar/proposals/<slug>/proposal.md`, with all
   eight parts. It records it as a short decision entry with status `proposed` (skellytracker
   decision faac). If you change the proposal after that copy, tell the user. skellytracker then
   records it again: it replaces the copy in full, ticks the closed items of "Before acceptance"
   and keeps the same entry (skellytracker decision vac0). The user accepts or rejects it. After
   acceptance:
   - A content PR adds the normative text, the changelog row, the vectors and the reference
     implementation. It sets the decision entry to `accepted` (if it is not accepted yet).
   - A non-spec PR (documentation only) adds the guidance, the implementation proposal (as
     implementer guidance and an open-work item), the example and its provenance record. It
     removes the `proposed` entry of the model from `specs/model-sidecar/inventory.yaml`, if one exists.
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
