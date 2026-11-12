# SR1E — Reset of the spec-build proposals

**Status:** done, 2026-10-29 (user; PR: pending).

## Decision

On 2026-10-29, the user decided to delete the spec change proposals of the spec-build stage. The
answer was "Yes, delete." This PR makes these changes:

1. It deletes 21 `proposed` entries of the spec log:
   - gap records: 0017 (folder of a sidecar with both roles), 0018 (one declaration for each output
     tensor), 0019 (batch axis of `outputs[].shape`), 0020 (ROI transform and ROI source), 0021
     (pose outputs beside the landmarks), 0022 (depth divisor of MediaPipe landmarks), 0023 (`floor`
     rounding and a scale inverse for `letterbox`), 0024 (SimCC keypoint score rule) and 0025
     (suffix after the part in `model_id`);
   - proposal entries: 0037 (`affine-crop-arithmetic`), 0038 (`heatmap-decode-refinement`), 0039
     (`keypoint-visibility`), 0040 (`nms-clamp-order`), 0041 (RTMDet host `selection: nms` with the
     mmdet filters), 0042 (`vNEXT` scope: two `nms` fields leave the list), 0043
     (`normalize-arithmetic`), 0044 (`omitted-upstream-output`), 0045 (`pose-decode-flip-test`), 0046
     (`size-codes`), 0047 (`roi-refiner-role`) and 0048 (`vNEXT` scope: MediaPipe-Exporter joins,
     rotated crops leave the list).
2. It deletes the 14 proposal records that have no `manifest.yaml`:
   `specs/model-sidecar/proposals/<slug>/` for `affine-crop-arithmetic`,
   `heatmap-decode-refinement`, `keypoint-visibility`, `landmark-depth-divisor`,
   `landmark-extra-outputs`, `model-id-suffix`, `nms-clamp-order` (with `evidence.md`),
   `normalize-arithmetic`, `omitted-upstream-output`, `pose-decode-flip-test`, `roi-refiner-role`,
   `roi-transform-and-source`, `simcc-score-rule` and `size-codes`. The
   [proposal index](../../specs/model-sidecar/proposals/README.md) stays, with its columns and no
   row. The constant `LEGACY_PROPOSAL_FOLDERS` of `tools/tests/test_proposal_records.py`
   goes: each record folder must have a `manifest.yaml`.
3. It removes the `proposed:` list of `specs/model-sidecar/inventory.yaml` with its 4 models:
   `mediapipe-hand@qualcomm-exporter`, `mediapipe-hand-recrop@qualcomm-exporter`,
   `mediapipe-hand-landmark@mediapipe-exporter` and `mediapipe-hand-recrop@mediapipe-exporter`. Its
   code in `tools/sidecar_trace.py`, its tests and the "Proposed models" part of
   `specs/model-sidecar/TRACEABILITY.md` go too. `model` bundles replace the list.
4. The facts of 0017, 0018, 0019 and 0023 go to the spec defects of the spec log
   [open-work.md](../../specs/model-sidecar/decisions/open-work.md). The spec guidance keeps each fact
   and drops its pointer to a deleted entry.

The history of `dom/sidecar-implementation` keeps the deleted files, at
`specs/model-sidecar/decisions/<ID>-<slug>.md` and `specs/model-sidecar/proposals/<slug>/`
(PR: pending). The IDs 0017 to 0025 and 0037 to 0048 stay retired. The Rules allow no new all-digit
ID.

This deletion is the decision of the user on 0041 and 0042 that
[ADR-B9FM](b9fm-finished-sidecar-plans.md) waits for. The user accepted neither entry.
[ADR-0011](../../specs/model-sidecar/decisions/entries/0011-rtmdet-host-nms.md) stays Active.

This entry records a one-off action. It adds no rule.

## Reason

- The user asked for a clean slate. The 21 entries and the 14 records use the formats from before
  [ADR-FADS](FADS-hand-over-bundles-in-intakes.md): gap records, records with no manifest, and part 3
  and part 4 in `proposal.md`. An exporter packs each proposal again as a `proposal` bundle in
  `intakes/`.
- The [Rules](../README.md#rules) allow the deletion:
  - a `proposed` entry can change until the user decides it, and the user decided at a stop before
    the first deletion;
  - the Rules retire all-digit IDs, so these IDs are never given again;
  - no file of these entries was on `development` (`git ls-tree -r development` lists no file in a
    decision folder), so the rule on IDs that were on `development` does not apply;
  - the action is complete and no rule stays, so the status is `done`.
- `tools/check_decision_log.py` needs one index row for each entry file. The deletion removes each
  file and its Proposed row in one commit.

## Consequences

- The text of a decided entry that names one of these IDs stays as history. A link to a deleted file
  in [ADR-A33Q](a33q-vector-case-form.md), [ADR-B9FM](b9fm-finished-sidecar-plans.md) and
  [ADR-VAC0](vac0-record-a-changed-proposal.md) is now a code span with "PR: pending" (link repair).
- A gap that has no proposal bundle goes on the spec-defect list of the spec log `open-work.md`.

## Alternatives rejected

- **Set the 21 entries to `rejected` and keep the 14 folders.** The log then keeps 21 entries and
  14 folders in the old formats, and `LEGACY_PROPOSAL_FOLDERS` stays. The user chose the deletion.
- **A consolidation entry.** It states the rules that stay from a group of decided entries. These
  entries were not decided and have no rule that stays.

_Edited 2026-10-29 (this PR): link repair._
