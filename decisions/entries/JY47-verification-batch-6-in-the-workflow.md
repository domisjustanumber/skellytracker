# JY47 — Verification batch 6 in the workflow and the bundle tool

**Status:** accepted, 2026-11-06 (user; PR: pending).

## Decision

The workflow, the templates, the skills and `tools/intake_bundle.py` use the verification batches
1, 2, 3 and 6 and 6 input B items. They agree with the Authoring guidance of
`common.batch_conversion` after
[ADR-50BW](../../specs/model-sidecar/decisions/entries/50BW-verification-batches.md).

1. **Tool.** `VERIFICATION_BATCHES = (1, 2, 3, 6)`, `TARGETS = (1, 2, 6)` and
   `INPUT_B_ITEMS = 6`. `SOURCE_BATCH`, `DYNAMIC_BATCHES` and `TOLERANCE` do not change. `batch`
   converts b3 to 1, 2 and 6. `verify` requires batch 6 of each pair for a b3 publish, and the
   publish-rule message names the batches 1, 2, 3 and 6.
2. **Text.** Each restatement of the batches 1, 2, 3 and 4 or of 4 input B items in these files
   changes to 6: [Batch-conversion check](../../specs/model-sidecar/model-addition-workflow/batch-conversion-check.md#batch-conversion-check),
   [Manifest](../../specs/model-sidecar/model-addition-workflow/hand-over.md#manifest) and
   [The session run](../../specs/model-sidecar/model-addition-workflow/hand-over.md#the-session-run),
   [Publishing](../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing),
   the Inputs of the [workflow](../../specs/model-sidecar/model-addition-workflow/README.md#model-addition-workflow),
   step 1b of [phase 1](../../specs/model-sidecar/model-addition-workflow/phase-1-intake.md),
   the Inputs table of the [model intake template](../../specs/model-sidecar/templates/model-intake.md)
   and the Inputs of [`author-sidecar`](../../.claude/skills/author-sidecar/SKILL.md).
3. **Records stay.** The superseded entries JC4T and JB5J, the CRV0 item numbers in
   [ADR-JAA4](JAA4-one-batch-field.md) and the tracked proposal records keep batch 4.
4. **Order.** This commit lands before the next versions of the two model bundles of
   OpenMMLab-Exporter. After it, a bundle with b4 files and 4 input B items fails `verify`.

## Reason

A bundle never holds a workflow change
([Workflow changes](../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes)).
Part 2.1 of the 50BW proposal lists these edits for the session. The spec and the tool must agree,
so the edits land right after the content commit of 50BW. Part 2.1 did not list three of them:
step 1b of phase 1, "for example b2 and b4" in Publishing, and the publish-rule message
`n/fp32/b4` in `tools/tests/test_intake_bundle.py`.

## Consequences

- The v1 model bundles `model-yolox-person@openmmlab-exporter` and
  `model-rtmw-wholebody133@openmmlab-exporter` use b4 and 4 input B items. Their next versions must
  export b6 and write 6 input B items. The user chose this order, so the contributor repacks once.
- The tool tests write 6 input B items and the batches 1, 2, 3 and 6.

## Open work

See [open-work.md](../open-work.md).
