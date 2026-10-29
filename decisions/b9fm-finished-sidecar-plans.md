# b9fm — The reference-examples procedure moves to the workflow; the coverage note is frozen evidence

**Status:** accepted, 2026-10-26 (user).

## Decision

- The procedure "Reference examples" moves from `specs/sidecar-implementation-plan.md` to
  [`reference-examples.md`](../specs/model-sidecar/model-addition-workflow/reference-examples.md)
  in the model addition workflow. The old heading stays as a "Moved to" stub, because decision
  entries, proposals and code comments link to it.
- The procedure changes in the move:
  - Step 2(c) and step 5 apply now. The spec requires `source` and `sha256`
    ([0016](0016-sidecar-catalogs.md)), and the examples have them.
  - `tools/sidecar_trace.py` maps the examples to sections and compares them with the exporter
    copies. The procedure no longer calls these tools "planned".
  - `inventory.yaml` gives the state of each example. The dated table of states is removed.
  - Step 7 follows the git rules of `AGENTS.md`. It no longer names a `dom/sidecar-example-<model>`
    branch ([0027](0027-single-working-branch.md)).
  - The citation of OpenMMLab-Exporter commit `38ed76f` becomes a permalink.
- `specs/sidecar-implementation-plan.md` stays until M6 is done. M5 is done. M6 waits for the
  implementation stage ([0014](0014-spec-lifecycle.md)). The list of M6 Part B is replaced by links
  to the backlog that the spec keeps: the front matter of each section, `TRACEABILITY.md`, the
  open work and the skill `implement-sidecar-section`.
- `notes/sidecar-exporter-coverage.md` is frozen evidence. It is not kept current. Only its status
  lines change, each in place, so that its line numbers do not change.
- Retire `notes/sidecar-exporter-coverage.md` at the end of the spec-build stage, after the user
  decides 0041 (`specs/model-sidecar/decisions/0041-rtmdet-host-nms-filters.md`) and 0042
  (`specs/model-sidecar/decisions/0042-vnext-scope-nms-filters.md`) (PR: pending). Before
  that, copy its unique measurements to an evidence entry.

## Reason

- The procedure is a step of phase 3 of the model addition workflow. Decision
  [x64y](x64y-draft-exporter-guide-folder.md) puts the process to add a model in that folder.
- The status line, M5 and M6 Part B of the plan were out of date. A second list of package gaps
  does not stay equal to the spec. The front matter of each section is the list that changes with
  the spec.
- The coverage note holds evidence that no other file holds: the checks of the RF-DETR graphs and
  the RTMDet measurement on 500 images (stretch costs about 1.1 AP). Recorded proposals cite it by
  line number (`size-codes`, `nms-clamp-order`).

## Consequences

- Three recorded proposals cite `specs/sidecar-implementation-plan.md` by line number:
  `model-id-suffix`, `heatmap-decode-refinement` and `simcc-score-rule`. After this change, those
  lines hold other text. A line citation stays correct at the commit that the proposal records, as
  in [x64y](x64y-draft-exporter-guide-folder.md). The session that lands `model-id-suffix` makes
  its edits of the procedure in `reference-examples.md`.
- Code comments under `skellytracker/` cite `specs/sidecar-implementation-plan.md` by milestone.
  Those headings do not change.

## Alternatives rejected

- **Move the procedure to `specs/model-sidecar/examples/README.md`.** That file describes the
  examples of the spec. The procedure is process, and the workflow holds the process.
- **Keep the lines of the plan where the proposals cite them.** Then agents read and follow the
  out-of-date text.
- **Retire the coverage note now.** Proposals cite it by line number, and its evidence is in no
  other file.

## Open work

See [open-work.md](open-work.md).

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._
