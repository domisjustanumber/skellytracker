# 0040 — Spec change: nms-clamp-order

**Status:** proposed, 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `nms-clamp-order`. The eight
parts are in
[`specs/sidecar/proposals/nms-clamp-order/proposal.md`](../../specs/sidecar/proposals/nms-clamp-order/proposal.md).

- **Section.** `post.det.selection.nms` (changed section). The proposal also changes the
  `clamp_boxes` row of `post.det.decode`, step 6 of `post.det.selection.top_k`, step 3 of
  `post.det.selection.none` and the guidance of `post.unprojection`.
- **Change.** The `nms` object gets four optional fields: `clamp_to_input` (default `false`),
  `pre_nms_top_k`, `level_strides` and `min_bbox_size`. With them, the host clamps each candidate box
  to `[0, W_in]` and `[0, H_in]` before the NMS, keeps the top `pre_nms_top_k` candidates of each
  level, and drops each candidate whose width or height in source pixels is `<= min_bbox_size`.
  Step 4 defines the visit order, the box area `max(0, x2 - x1) * max(0, y2 - y1)` and the IoU 0 of a
  zero union. `clamp_boxes` gets the closed bounds `[0, src_w]` and `[0, src_h]`, and a zero-area row
  stays. `V-post.det.selection.nms-1` changes, and `V-post.det.selection.nms-2` (the row count of the
  levels) is new.
- **Version.** `vNEXT`. When a new field is absent, the current meaning stays. A sidecar with an
  older `schema_version` keeps its legacy meaning.
- **Models.** `rtmdet-person` (nano and medium) of OpenMMLab-Exporter: `clamp_to_input: true`,
  `clamp_boxes: false`, `pre_nms_top_k: 1000`, `level_strides: [8, 16, 32]` and `min_bbox_size: 0`.
- **On acceptance.** [0041](0041-rtmdet-host-nms-filters.md) supersedes
  [0011](0011-rtmdet-host-nms.md) in full. [0042](0042-vnext-scope-nms-filters.md) supersedes
  [0008](0008-vnext-scope.md) in full. Both entries have the status `proposed` now. 0041 holds the NMS
  rules, and its evidence is in
  [`evidence.md`](../../specs/sidecar/proposals/nms-clamp-order/evidence.md). 0042 holds only scope
  rules. The proposal also closes the open-work spec defect on `clamp_boxes`.
- **Related.** `roi-transform-and-source` ([0020](0020-roi-transform-and-source.md)) has the scope
  entry [0048](0048-vnext-scope-mediapipe-rotated-crops.md). 0042 and 0048 both supersede 0008. The
  scope entry that lands second supersedes the scope entry in force and restates its scope rules. If
  0048 lands first, 0042 uses the variant text of the proposal. 0041 has no merge point there.
  `landmark-extra-outputs` ([0021](0021-landmark-extra-outputs.md)) and `roi-refiner-role`
  ([0047](0047-roi-refiner-role.md)) edit rows next to the `clamp_boxes` row. No proposal must land
  before this one.

## Reason

- mmdet filters and clamps the RTMDet candidates before the NMS. It keeps the top `nms_pre` (1000)
  candidates of each feature level. It clamps each box to the padded model input. It drops each box
  with a width or a height `<= min_bbox_size` (0) in source pixels. The current spec clamps after the
  NMS, to the source image. It has no cap and no size filter. Thus a sidecar cannot describe the
  mmdet decode.
- The `clamp_boxes` row does not define its upper bound or the result for a box with zero area.
- Step 4 does not define the box area of an inverted box or the IoU of a zero union. Two hosts can
  keep different rows.
- On COCO val2017, the clamp order changes the kept rows on 668 of 5000 nano images and 405 of 5000
  medium images. This number comes from an uncommitted scratch script. It is not evidence.
- The primary evidence is the config keys `nms_pre=1000` and `min_bbox_size=0`, the graph read of the
  three levels, the upstream mmdet output and the mmdet v3.3.0 and mmcv v2.1.0 code lines (part 1).

## Evidence

- Parity: `to run`. The script is not committed. Its proposed name is
  `notes/decisions/scripts/rtmdet_nms_clamp_parity.py` in OpenMMLab-Exporter. The export error and
  the preprocessed-input difference are `to run`.
- Vectors: 29 new cases. In a scratch run, the reference code gives the expected results on the 20
  existing cases and on the 29 new cases. The host `NmsDecoder` of OpenMMLab-Exporter gives the same
  results on 9 cases, differs on `inverted-box-has-area-zero` and has no code for 19 cases. The new
  cases are `unverified`.
- Source: OpenMMLab-Exporter commit
  [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1).

## Open work

See [Open work](README.md#open-work).
