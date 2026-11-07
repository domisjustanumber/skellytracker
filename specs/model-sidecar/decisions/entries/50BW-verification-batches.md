# 50BW — Spec change: verification-batches

**Status:** accepted, 2026-11-06 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-06. The record is
[`proposal.md`](../../proposals/verification-batches/proposal.md)
(proposal-verification-batches@openmmlab-exporter@v1).

- Section: [`common.batch_conversion`](../../common/batch-conversion.md).
- Change: only the Authoring guidance changes. The verification batches of the `static-batch-v1`
  check change from 1, 2, 3 and 4 to 1, 2, 3 and 6. The check converts b3 to `N` = 1, 2 and 6.
  Input B holds 6 different preprocessed images of each size. Batch 6 is never published. `S`
  stays 3. The profile, the Behaviour, the `V-` rules, the tolerance and V6 do not change. The
  workflow text and `tools/intake_bundle.py` change in a separate non-spec commit with its own
  entry.
- Target spec version: `2.0.0`.
- Models: `rtmw-wholebody133` and `yolox-person` (measured), and each later family with a b3
  publish.
- Supersedes: none.
- Related: `model-yolox-person@openmmlab-exporter` and `model-rtmw-wholebody133@openmmlab-exporter`
  name this bundle. Neither model waits for it.
- The user confirmed two plan decisions. The verification batches change from 1, 2, 3 and 4 to 1,
  2, 3 and 6. Batch 4 goes, and `S` stays 3. Input B grows from 4 to 6 different preprocessed
  images of each size.
- Landing order: the user decided that this change and its workflow and tool commit land before
  the next versions of the two model bundles. Thus the contributor packs them once, with b6 files
  and 6 input B items.

## Reason

No end user runs batch 4, and its files have no use after the check. The user decided to use
batch 6. The batches 1, 2, 3 and 6 are closer to the batch sizes of end users, so the same files
can later give benchmark values. The coverage stays: b1 is the fallback, b2 is a down-conversion
that is not a multiple of `S`, and b6 is an up-conversion.

## Evidence

Parity: `pass`. The script is `decisions/scripts/batch_conversion_n_variant.py` at
OpenMMLab-Exporter `9810e483c69efddea7a8b93e671d6250eb47c5f0`. It uses the runner of
`tools/intake_bundle.py` and `model_batch_convert` at skellytracker `8351b7f8`, with Python
3.12.13, NumPy 2.4.6, onnx 1.22.0 and onnxruntime 1.27.0 CPU. With `N` = 1, 2 and 6, 66 of 66
tuples of `yolox-person` and `rtmw-wholebody133` pass V3 and V5, with a maximum difference of 0.0.
The control with `N` = 1, 2 and 4 agrees with the hand-over reports for 65 of 66 tuples.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- The header says that the model bundles are not packed yet. Both model bundles now exist.
- The follow-up table of part 2.1 does not list these restatements of batch 4: phase 1 Step 1b
  ([phase-1-intake.md](../../model-addition-workflow/phase-1-intake.md)), "for example b2 and b4"
  in [Publishing](../../model-addition-workflow/validation-and-publishing.md#publishing), and the
  publish-rule message `n/fp32/b4` of `tools/tests/test_intake_bundle.py`.
- The control tuple `yolox-person` l fp16 `N` = 4 on input A gives a box difference of 0.75. The
  evidence calls it onnxruntime 1.27.0 CPU fp16 noise from one run to the next: 20 repeats give 0
  failures. The claim that onnxruntime 1.31 removes the noise has no script (secondary).
- Open question: the same fp16 noise can give a false `does not convert` in any `batch` run. A
  fixed thread count, a repeat of a failed fp16 tuple or a newer onnxruntime can prevent it.
- The evidence names spec commit `b0dfe0bd` for the hand-over control report. The packed reports
  give `8351b7f8`. No checked file changed between the two commits.
- Landing order: after the workflow and tool commit, a model bundle with b4 files and 4 input B
  items fails `verify`. The v1 model bundles of this contributor use b4.
- The changelog row of part 2 links `../../common/batch-conversion.md`. The link must be relative
  to `changelog.md` when it lands.
- Recording this entry makes OpenMMLab-Exporter the owner of `common.batch_conversion` while the
  entry is `proposed` ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
