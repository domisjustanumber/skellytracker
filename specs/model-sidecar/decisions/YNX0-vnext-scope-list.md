# YNX0 — Scope of `vNEXT`

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [ADR-0008](0008-vnext-scope.md) in full. Item 1 restates the rules of ADR-0008
that stay by a link. Items 2 to 6 are new.

1. **The scope list.** [Scope of this revision](../changelog.md#scope-of-this-revision) in the
   changelog is the only list of the models that `vNEXT` must describe. That heading is the only
   source of these rules of ADR-0008: the start list, the Qualcomm-Exporter exclusion, the rule
   that `vNEXT` adds only the features that a model in the list needs and lists the other features
   in [Considered and deliberately not added](../changelog.md#considered-and-deliberately-not-added),
   the RF-DETR rules and the `vNEXT` placeholder name. The heading cites the workflow heading
   [Publishing](../model-addition-workflow/validation-and-publishing.md#publishing) for the release
   step.
2. **Two join events.** A model joins the list when the user accepts a change proposal that the
   model needs. A model also joins the list when skellytracker lands it with the verdict
   `describes`. These two edits apply this entry. They need no decision entry. To remove a model
   from the list, write a new entry. The list is a process list, so a change of the list is a
   non-spec change.
3. **A new batch-conversion profile.** It joins `vNEXT` in the same way. The user accepts its
   proposal, and each model that needs it joins the list.
4. **`vNEXT` text only.** In the spec-build stage, each accepted spec change goes into `vNEXT`. A
   proposal gives only the `vNEXT` text. It never gives a second text for a later revision. A
   proposal that the user has not decided keeps the status `proposed`. It does not move to a later
   revision. Item 7 and part 2.6 of the
   [proposal template](../templates/change-proposal.md) state this. They cite the heading of the
   list, not an entry ID.
5. **The table of features not added.** The table is not a ban. The content PR that adds a feature
   of the table removes its row. This entry does not copy the groups of the table.
6. **Not the intake verdict.** The list is not the verdict `out of scope` of an intake row.

## Reason

- The closed list of ADR-0008 and the rule "every spec change goes into `vNEXT`" did not agree for a
  model outside the list. So the proposals for such a model gave two texts: one for `vNEXT` and one
  for a later revision. The user cannot accept a proposal with two texts.
- The vector tools accept only `spec_revision: vNEXT`. A text for a later revision cannot have
  vectors in the spec-build stage.
- The proposed scope entries ADR-0042 and ADR-0048 each supersede ADR-0008 in full on acceptance. The entry that lands second
  must be written again. Exporters also treated the proposed ADR-0048 as the entry in force.
- The user already decides each acceptance. A separate scope decision for each proposal adds a
  second decision and no new control.
- A list in the spec has one place. A template can cite its heading, so an exporter does not read a
  proposed entry as a rule.
- A model that lands with the verdict `describes` changes no spec text. Without the second join
  event, the list would not name it.

## Consequences

- A recorded proposal that gives a text for a later revision must change in a new version before
  acceptance.
- The proposed entries ADR-0042 and ADR-0048 restate the closed list. This entry does not decide them.
- Each landing of a model or an accepted proposal checks the list.

## Evidence

- The measurement of ADR-0008 for `class_logits` with `selection: nms` (RTMDet-tiny, AP 0.4114 against
  0.4112) is in its row of
  [Considered and deliberately not added](../changelog.md#considered-and-deliberately-not-added).

## Alternatives rejected

- **One scope entry for each proposal** (ADR-0042, ADR-0048). Each one supersedes the entry in force, so the
  second one that lands must be written again.
- **A text for a later revision.** The spec-build stage has no release to name, and the vector tools
  reject it.
- **A scope list with a delta entry for each scope decision.** It adds a second decision to each
  acceptance.
- **"A correction needs no listed model."** It lets a change skip the list, and no proposal needs
  it.

## Not repeated

- Do not read the table of features as a ban. A feature leaves the table when a model in the list
  needs it.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.
- Do not read the list as the intake verdict `out of scope`.
