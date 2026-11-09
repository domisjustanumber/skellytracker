# 7F6X — License rows in the model intake

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

The model intake template and its workflow copies follow the sections and rules that landed on
2026-11-09.

1. **License rows.** The template gets the table "License" with rows LC1 to LC6 for the `license`
   block of [`common.license`](../../specs/model-sidecar/common/license.md)
   ([ADR-NBG2](../../specs/model-sidecar/decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md)):
   the mapping, the license of the weights, the training datasets, the datasets of each start
   checkpoint, the license of each dataset with the SPDX List version, and each `unknown` with its
   reason. These rows need no parity run. The Inputs table, the validation checklist and the
   package-limit note name the block. Step 1 of
   [Phase 1](../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md) and the input lists
   of the workflow `README.md` and the skill `author-sidecar` name its sources. The skill gets a hint
   row for the table.
2. **Out of scope and parity.** The template section "Steps outside the model contract" and the
   parity image bullet take the two cases of
   [ADR-R6J9](../../specs/model-sidecar/decisions/entries/R6J9-test-time-steps-and-unreachable-branches.md).
   The parity table gets a row for the branches that no real image reaches.
3. **Row T11.** The row names the cast to `input.dtype` as the last step of `pre.normalize` and
   `V-pre.normalize-3` (changelog row 40).

## Reason

The user asked for a review of the template. A subagent compared it with the current spec and
workflow. The template had no license rows, so the RTMW intake added rows LC1 to LC7 by hand. Two
template texts kept the rule from before ADR-R6J9, and row T11 kept the text from before changelog
row 40.

## Open work

See [open-work.md](../open-work.md).
