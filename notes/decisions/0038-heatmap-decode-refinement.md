# 0038 — Spec change: heatmap-decode-refinement

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `heatmap-decode-refinement`.
The eight parts are in
[`specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md`](../../specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md).

- **Section.** `post.pose.decode.heatmap` (changed section,
  [`post/pose-decode-heatmap.md`](../../specs/model-sidecar/post/pose-decode-heatmap.md)). The section
  ID, the title and the selectors do not change.
- **Change.** The heatmap decode becomes exact. The peak is the first maximum in row-major order. The
  score is the raw maximum value, with no activation. A score `<= 0` puts the keypoint at cell -1 on
  each axis. A new required field `pose.decode.refinement` (`none` or `quarter_offset`) has no
  default. `quarter_offset` moves the peak 0.25 cell toward the higher neighbour on each axis, only
  when `1 < x < W - 1` and `1 < y < H - 1`. The cell maps to crop pixels with `input_width / W` and
  `input_height / H`, with no half-cell offset. New rules `V-post.pose.decode.heatmap-2` (the field
  is required for `method: heatmap`) and `V-post.pose.decode.heatmap-3` (the field is valid only for
  `method: heatmap`). A new "Legacy behaviour" heading keeps the peak cell, with no -1 rule and no
  refinement.
- **Version.** `vNEXT`. A sidecar with `schema_version < vNEXT` uses the legacy row. No package
  sidecar and no example has `method: heatmap`, so no current behaviour changes.
- **Models.** `vitposepp-wholebody133` and `vitpose-coco25` of OpenMMLab-Exporter (the ViTAE test
  pipeline, `post_process='default'` with `use_udp=False`). No sidecar of these models exists yet.
- **On acceptance.** This entry supersedes no entry.
- **Related.** `pose-decode-flip-test` ([0045](0045-pose-decode-flip-test.md)) must land first. This
  proposal links its section and names `V-post.pose.flip_test-3`. `simcc-score-rule`
  ([0024](0024-simcc-score-rule.md)) adds the same -1 rule to `post.pose.decode.simcc`. Other
  proposals edit the same places in `format/versioning.md`, `post/pose-schema.md`, `changelog.md`,
  `templates/model-intake.md` and the vector tooling. The proposal file lists them.

## Reason

The section has one sentence of Behaviour: the host decodes the peak and unprojects it. It gives no
refinement, no cell-to-pixel scale, no score, no tie order and no rule for a maximum `<= 0`. A host
that follows it gives the integer cell. The upstream moves 0.25 cell on each axis for most
keypoints. For a 256x192 input and a 64x48 heatmap, that is 1 crop pixel on each axis. The upstream
code is ViTAE-Transformer/ViTPose `c050ed2`, `keypoints_from_heatmaps` in
`mmpose/core/evaluation/top_down_eval.py`. This is primary evidence.

Two upstream forms of the quarter step disagree. ViTAE tests the two axes together. The mmpose
v1.3.2 function `refine_keypoints` tests each axis alone. For a peak in row 1, ViTAE gives x 2.0 and
mmpose v1.3.2 gives x 2.25 (vector `quarter-y-border-blocks-x`). Thus "decodes the peak" with a
refinement is not exact either.

A composition check found equal crop pixels, equal scores and source pixels within 1.2e-4 px
against the ViTAE decode. That number comes from a scratch script that is not committed. It is not
evidence.

## Evidence

- **Vectors.** 24 cases, `unverified`. No host in an exporter or in skellytracker decodes heatmaps.
  The proposal reports 24 of 24 cases pass against its reference code. That run used a scratch
  runner that is not committed.
- **Parity.** `to run`. The planned OpenMMLab-Exporter scripts are
  `notes/decisions/scripts/heatmap_decode_parity.py` and
  `notes/decisions/scripts/heatmap_decode_parity_worker.py`. They are not written, and they have no
  commit. The run needs the ONNX files of the two models and the ViTAE environment of the exporter
  image.
- **Missing primary evidence.** The ONNX files. An upstream config for the 25-point pipeline (the
  exporter creates that config). The AP effect of the step.
- **Source.** The OpenMMLab-Exporter proposal at commit
  [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1).

## Open work

See [Open work](README.md#open-work).
