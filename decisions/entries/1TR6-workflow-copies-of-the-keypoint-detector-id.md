# 1TR6 — Workflow copies of the keypoint detector id

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

The workflow copies of the old id rule `{family}-{part}` follow the landed rule of
[ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md):
`{family}-{group}` or `{family}-{group}-{variant}` in `keypoint_detectors/{family}/{group}/`.

1. "Identity" of `mapping-hints.md` and row F1 of the model intake template: write the id of the
   grammar. The verdict is `exact`. The `gap` for a second model of one family and one part goes,
   because a variant separates the two models. A new role with no `model_id` rule stays a `gap`.
   The sentence on row F1 in "Rules" of `rules.md` goes.
2. Row L1 of the template, "Path" of `sidecar-files.md`, step 3 of "How to provide or replace an
   example" in `reference-examples.md` and step 5 of the skill `author-sidecar`: `{part}` becomes
   `{group}`. A folder that is not a group, for example `body7`, does not conform
   (`V-common.identity-8`).
3. The texts that name the removed `rtmo-body7` example as a current fact go: the both-roles
   sentence of `sidecar-files.md` and the RTMO paragraph at the end of "How to provide or replace an
   example".
4. Item 1 of the implementation plan names `keypoint_detectors/{family}/{group}/`.

## Reason

The 52NQ proposal leaves these copies to the session that lands it, in a separate non-spec commit
([Workflow changes](../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes)).
The old copies tell an exporter to write `{family}-{part}`, and they call a second model of one family
and one part a `gap`. Both are false after 52NQ.
