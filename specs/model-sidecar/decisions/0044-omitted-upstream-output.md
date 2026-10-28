# 0044 — Spec change: omitted-upstream-output

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `omitted-upstream-output`. The
eight parts are in
[`specs/model-sidecar/proposals/omitted-upstream-output/proposal.md`](../../specs/model-sidecar/proposals/omitted-upstream-output/proposal.md).

- **Section:** none. The change is a verdict rule of the new-model workflow. It changes no section
  file, no sidecar field, no vector and no changelog row.
- **Change:** Phase 1 gets the row verdict `omitted`. It is for an upstream decode output that the
  sidecar deliberately does not declare. Each of six conditions must be true: the omission changes no
  declared output; the spec does not require the output, and "Considered and deliberately not added"
  does not list it; the upstream metric does not read it; for each known consumer, a committed
  measurement shows that a declared output serves it at least as well; the sidecar declares nothing
  for it; an exporter decision entry records the omission. An `omitted` row needs no proposal, and the
  final verdict `describes` accepts it. The edits are in the exporter guide (`phase-1-intake.md`,
  `parity.md`, `mapping-hints.md` and `rules.md`), in `specs/model-sidecar/templates/model-intake.md` and in
  the skill `author-sidecar`.
- **Version:** none. No sidecar changes meaning at any `schema_version`. A non-spec PR lands the
  change.
- **Models:** the two RTMW 384x288 configs (l and x). Their codec sets `decode_visibility=True`, and
  the head stores the softmax visibility as `keypoints_visible`. The RTMW intake row K8a changes from
  `out of scope (0041)` to `omitted (0041)`. Both tags name OpenMMLab-Exporter 0041.
- **On acceptance:** the change edits the exporter guide, the model intake template and the skill
  `author-sidecar` (G1 to G10). It supersedes no entry: [0014](0014-spec-lifecycle.md) is absorbed
  into the exporter guide, so part 2, D1 to D3, does not apply (user decision, 2026-10-25).
- **Related:** `keypoint-visibility` ([0039](0039-keypoint-visibility.md)) is a merge point. G8
  merges its sentence in the hint "Pose". The proposal sets no order: the PR that lands second keeps
  the edits of both. The recommended order lands `keypoint-visibility` first. These proposals edit
  the same guide and template files: `roi-refiner-role` ([0047](0047-roi-refiner-role.md)),
  `roi-transform-and-source` ([0020](0020-roi-transform-and-source.md)), `landmark-extra-outputs`
  ([0021](0021-landmark-extra-outputs.md)), `nms-clamp-order` ([0040](0040-nms-clamp-order.md)),
  `normalize-arithmetic` ([0043](0043-normalize-arithmetic.md)), `model-id-suffix`
  ([0025](0025-model-id-suffix.md)), `size-codes` ([0046](0046-size-codes.md)) and
  `affine-crop-arithmetic` ([0037](0037-affine-crop-arithmetic.md)). `simcc-score-rule`
  ([0024](0024-simcc-score-rule.md)) and `keypoint-visibility` also change the `decode_visibility`
  text of `post.pose.decode.simcc`.

## Reason

- The phase 1 verdicts have no verdict for an upstream decode output that the exporter deliberately
  leaves out. Such an output is inside the runtime contract, so it is not `out of scope`. The spec has
  no field for it, so the test gives `gap`. A `gap` row then needs a proposal for a field that no
  consumer reads.
- For RTMW row K8a, the guide gives `gap`. User decision T36 of OpenMMLab-Exporter gives
  `out of scope (0041)` (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). Thus two
  agents can give one row different verdicts.
- The visibility is not useful. On COCO-WholeBody v1.0 val (12704 hands, GT boxes), it ranks valid
  hands worse than the raw score at every size. The AUC difference is −0.046 to −0.094, and each 95 %
  upper bound is below 0 (OpenMMLab-Exporter 0041, committed scripts: evidence). The COCO-WholeBody
  metric reads only `keypoint_scores`.
- The proposal prefers a new verdict to a wider `out of scope`. One verdict with two tests of
  different strength hides which test a row passed.

## Evidence

- Parity: none (no run). The change adds no algorithm and changes no declared output. Parts 3, 4 and
  5 are `none`.
- The measurement is OpenMMLab-Exporter 0041
  ([`0041-rtmw-wrist-gate.md`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/9deff61c3299c9cd06f933f01d7be07ed3fe0167/notes/decisions/0041-rtmw-wrist-gate.md)).
  Commit `9deff61` also adds its five scripts `notes/decisions/scripts/rtmw_wrist_gate_*.py`.
- The fact that the omission changes no declared output is a code reading of mmpose v1.3.2
  (`simcc_label.py` and `base_head.py`). The reading used a local copy that is not committed. It is
  not primary evidence until it has permalinks.

## Open work

See [Open work](README.md#open-work).
