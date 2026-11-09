# 1VMX — Spec change: nms-key-exclusion

**Status:** absorbed into [`post/selection-nms.md#validation-rules`](../../post/selection-nms.md#validation-rules), 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-06. The record is
[`proposal.md`](../../proposals/nms-key-exclusion/proposal.md)
(proposal-nms-key-exclusion@openmmlab-exporter@v1).

- Section: [`post.det.selection.nms`](../../post/selection-nms.md).
- Change: no normative text changes. The landed reference module
  `reference/post_det_selection_nms.py` gets `EXCLUDED_FIELDS` and `check_excluded_fields`. It
  refuses `class_logits_output`, `top_k` and `max_detections` with `selection: nms`, as the
  current `V-post.det.selection.nms-1` says. The vector file gets 3 data-only validator cases at
  the end. The 24 numeric cases do not change.
- Target spec version: `2.0.0`.
- Models: `yolox-person` (no sidecar change).
- Supersedes: none.
- Related: `model-yolox-person@openmmlab-exporter`. Its response asked for this change, because the
  landed module did not check the rule.
- The user confirmed two plan decisions. The module refuses the three keys exactly as the current
  text of `V-post.det.selection.nms-1` says, and the text does not change. The gap of
  `class_logits_output` with `selection: nms` (NMS over the scores of each class) is only noted in
  part 8 of the proposal.
- Landing form: the user chose a non-spec commit, as a reference implementation of the current
  text with its vectors. The commit adds no changelog row, and the fingerprint does not change.

## Reason

The landed module accepts a sidecar that `V-post.det.selection.nms-1` refuses: it ignores the three
keys. A reference module must implement exactly the text of its section
([Reference implementations](../../model-addition-workflow/reference-implementations.md#reference-implementations)).
The landed module is code of skellytracker, so a change to it comes as a proposal.

## Evidence

The module is the landed module plus 44 lines and no deletion. For a decode block without the three
keys, it runs the same statements as before. No new parity run loaded it: the pass comes from the
OpenMMLab-Exporter ADR-3NNK reference swap of the landed module. The exporter host passes the 24
numeric cases at OpenMMLab-Exporter `c2e610e`. No validator ran the 3 new cases.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- The landing form: the workflow has no path for a changed reference module with no text change.
  It can be a content commit with an empty part 2, or a non-spec commit of a reference
  implementation of the current text with its vectors. With no text change, the changelog
  fingerprint does not change.
- `make_vectors.py` applied the file-level `checks` to a data-only case, so `fill` and `land`
  failed on this vector file. A tools commit after this record fixes it.
- The intake of `model-yolox-person@openmmlab-exporter` must name this bundle in its next version.
- The comparison of the two modules on 200 random candidate sets has no committed script.
- The 3 cases are the first cases of `V-post.det.selection.nms-1`, so the Gate column of
  `TRACEABILITY.md` can change.
- At landing, do the [safety review](../../../../.claude/skills/change-sidecar-spec/SKILL.md#safety-review)
  of the record copy again before the copy.
- Recording this entry makes OpenMMLab-Exporter the owner of `post.det.selection.nms` while the
  entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
