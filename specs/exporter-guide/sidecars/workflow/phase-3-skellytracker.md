# Phase 3: what skellytracker does next

You do not do phase 3. A skellytracker session does it. The user decides.

1. **A model with the verdict `describes`.** One non-spec PR (documentation only) in skellytracker
   adds the sidecar as a spec example (under `specs/sidecar/examples/`), with its provenance record
   (in `specs/sidecar/inventory.yaml`) and any new guidance from the intake. The procedure is
   "Reference examples" in `../freemocap/skellytracker/specs/sidecar-implementation-plan.md`.
   Its preconditions: the exporter writes the sidecar itself (not by hand), at `vNEXT`, with no
   legacy-only fields; the checks of the exporter pass; parity passes for at least one size. The
   procedure copies your sidecar byte for byte. If your sidecar breaks a spec rule, fix the exporter
   or write a change proposal. Nobody corrects the example by hand.
2. **A proposal.** skellytracker copies it to `specs/sidecar/proposals/<slug>/proposal.md`, with all
   eight parts. It records it as a short decision entry with status `proposed` (skellytracker
   decision 0036). The user accepts or rejects it. After acceptance:
   - A content PR adds the normative text, the changelog row, the vectors and the reference
     implementation. It sets the decision entry to `accepted` (if it is not accepted yet).
   - A non-spec PR (documentation only) adds the guidance, the implementation proposal (as
     implementer guidance and an open-work item), the example and its provenance record.
   - When skellytracker implements the spec, an implementation PR adds the code.
3. Then you write the sidecar with the new fields, and you finish phase 1 for the model.
