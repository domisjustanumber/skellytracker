# V8FK — License evidence and models with no license

**Status:** absorbed into [`model-addition-workflow/README.md`](../../specs/model-sidecar/model-addition-workflow/README.md), [`templates/model-intake.md#license`](../../specs/model-sidecar/templates/model-intake.md#license), 2026-11-10 (user; PR: pending).

## Decision

1. **A license page is primary evidence.** For a `license` row of the model intake, the license page
   of the weights or of a dataset is primary evidence, next to an upstream file and line, a config key
   and a graph read. The row gives its URL and the date of the read
   ([Rules](../../specs/model-sidecar/model-addition-workflow/rules.md#rules)).
2. **No license, no sidecar.** A model must have a known license of its weights
   (`V-common.license-5`). If research finds none, row LC2 is `unknown` with the verdict `gap`. That
   row is blocking, but it goes to no proposal: the session refuses the model, and the model gets no
   sidecar ([Verdicts](../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md#verdicts);
   [Blocking rows](../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md#blocking-rows)).
3. The model intake template states both rules in rows LC2 and LC4 and in the notes of its table
   "License". Row LC4 also names the distillation teacher of
   [ADR-1BS2](../../specs/model-sidecar/decisions/entries/1BS2-distillation-teacher-is-a-start-checkpoint.md).

## Reason

- The user, 2026-11-09, on a license page as evidence: "yes". On a model with an unknown license of
  its weights: "reject. All models must have licenses".
- The old evidence rule named only code, config and graph sources. A strict reading made each
  license row `unverified`, because a license page is none of these.
- The workflow gave no verdict for a model whose weights license is unknown. A `gap` would send it to
  a proposal, but the spec requires a known license, so no spec change can describe the model.
