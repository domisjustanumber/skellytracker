# CNSN — Spec-build actions recorded after the fact

**Status:** accepted, 2026-10-28 (user; PR: pending).

## Decision

This entry records three past actions of the spec-build stage. Each action is complete. Each action
went against a rule of [ADR-0014](0014-spec-lifecycle.md) with no decision entry. The user accepted
each action on 2026-10-28.

1. **The precision `int8` is removed at every `schema_version`.** The spec, the examples, the
   inventory and the vectors do not list `int8`
   ([summary row 21](../specs/model-sidecar/changelog.md#summary-of-changes) and the
   [compatibility impact](../specs/model-sidecar/changelog.md#compatibility-impact) of the
   changelog). The package code also changed: `skellytracker/core/sidecar/model.py` and its tests
   `skellytracker/tests/sidecar/test_model_validation.py`,
   `skellytracker/tests/sidecar/test_resolution.py` and
   `skellytracker/tests/test_image_preprocessing.py`. This went against the 0014 rule "no
   implementation change during the spec-build stage". It also went against the rule that the
   meaning of an older `schema_version` never changes.
2. **The batch converter is in the package.** `skellytracker/core/sessions/batch_conversion.py` and
   its tests `skellytracker/tests/test_batch_conversion.py` hold the only batch converter. The
   layout row in `skellytracker/AGENTS.md` names the module. That row is context, not a part of
   this record. This went against the 0014 rule "no implementation change during the spec-build
   stage".
3. **The draft section [`common.batch_conversion`](../specs/model-sidecar/common/batch-conversion.md)
   landed with no decision entry.** This went against the rule that a spec change needs a decision
   entry ([`specs/model-sidecar/AGENTS.md`](../specs/model-sidecar/AGENTS.md)).

These commits are on `dom/sidecar-implementation` and are not on `development` (PR: pending).

This entry adds no rule and no exception for future work. The 0014 rule "no implementation change
during the spec-build stage" stays. A later change under `skellytracker/` in the spec-build stage
needs its own entry with an explicit user waiver. This entry is the precedent for that waiver.

## Reason

- The log must show each action that went against a rule, with the decision of the user. A reader
  then does not take the change as an error, and does not revert it.
- One record for the three actions keeps the read path short. Each action is complete, so this
  entry becomes `done` in the PR that adds it.
- A general exception to 0014 for package code would let later work change the code with no
  decision of the user.

## Consequences

- A PR from `dom/sidecar-implementation` to `development` holds these package-code changes.
- A legacy sidecar that lists `int8` is invalid. The current Ultralytics-Exporter sidecars list
  `int8`. They need a re-export.
- The draft section has a validate status `missing`: `BatchingSpec` in
  `skellytracker/core/sidecar/model.py` rejects the key `batch_conversion`.

## Alternatives rejected

- **Revert the package-code changes.** The spec at every `schema_version` and the converter depend
  on them, and the user accepted them.
- **One entry for each action.** Each action is complete and has no rule that stays. Three entries
  add three index rows and no information.
- **A new exception to 0014 for future package code.** The user kept the 0014 rule.
