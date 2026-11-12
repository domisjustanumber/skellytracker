# R6J9 — Test-time steps and unreachable branches

**Status:** absorbed into [`phase-1-intake.md#verdicts`](../../model-addition-workflow/phase-1-intake.md#verdicts), [`parity.md#parity`](../../model-addition-workflow/parity.md#parity), 2026-11-10 (user; PR: pending).

## Decision

1. **`out of scope` also covers two steps around the contract.** In "Verdicts" of
   [Phase 1](../../model-addition-workflow/phase-1-intake.md#verdicts), these steps are
   `out of scope`:
   - a test-time augmentation that runs the runtime contract more than once and combines the
     results, for example the flip test of mmpose;
   - a value that the upstream decode computes in addition to the final outputs of the role, when
     the sidecar does not declare it and it changes no final output, for example the keypoint
     visibility of mmpose.

   The row cites the evidence and tells which of the two steps it is.
2. **A branch that no real image reaches.** In step 2 of
   [Parity](../../model-addition-workflow/parity.md), a branch that no real image can reach, for
   example a score `<= 0`, a tie or a NaN of a decode, does not need an image. The intake names the
   branch and its coverage: the vector cases of the section that the host passes, or a committed
   check that runs crafted inputs through the upstream code and compares the host bit for bit.

## Reason

- The RTMW intake has both steps. The old text gave `out of scope` only to a step before or after
  the contract. A strict reading made both rows a `gap`, which needs a spec field for a step that a
  host must not run.
- The final outputs of a role are the contract that parity checks. A step that adds no final output
  or repeats the contract is not a part of it.
- No real RTMW output gives a SimCC score `<= 0`, a tie or a NaN. Step 2 asked for an image that does
  not exist.

## Alternatives rejected

- **A `gap` and a proposal for each step.** The spec would then describe a test-time augmentation and
  an output that no host reads.
- **A user ruling for each row.** The same question then comes back with each model.
