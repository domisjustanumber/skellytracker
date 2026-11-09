# 1BS2 — A distillation teacher is a start checkpoint

**Status:** absorbed into [`common/license.md#fields`](../../common/license.md#fields), 2026-11-09 (user; PR: pending).

## Decision

In [`common.license`](../../common/license.md), the datasets of a distillation teacher count as
datasets that made the weights. `license.training_data` lists each dataset of the teacher, with
`use: pretraining`, in the same way as each dataset of a checkpoint that the training started from.

## Reason

- The user, asked on 2026-11-09 whether a distillation teacher counts as a start checkpoint:
  "yes".
- A distilled model learns from the outputs of its teacher. The terms of the datasets of the teacher
  can thus apply to the weights, as the terms of a start checkpoint can.
- The text said only "a checkpoint that the training started from". A teacher is not such a
  checkpoint, so two writers could list different datasets for one model. OpenMMLab-Exporter
  already lists the datasets of the RTMW teacher, after a ruling of its own user (OpenMMLab-Exporter
  ADR-EC75, secondary).

## Consequences

- The RTMW example already lists the datasets of its teacher. No example changes.

## Alternatives rejected

- **Leave the teacher out.** The list then misses datasets whose terms can restrict the weights.
