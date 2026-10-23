# 0019 — Batch axis of `outputs[].shape`

**Status:** proposed, 2026-10-23 (from the exporter evidence of Ultralytics-Exporter and
Qualcomm-Exporter).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Give `outputs[].shape` the batch rule of `input.shape`. At `vNEXT`, the
batch axis (axis 0) of each top-level `outputs[].shape` must be `-1`. A concrete batch size goes only
into `sizes.<size>.onnx.batch_artifacts.<N>.output_shapes`. When a size lists only one batch key `N`,
the output shapes of that group are the top-level `outputs[].shape`, with axis 0 set to `N`. The rule
gets a new **(vNEXT)** rule ID in [Outputs](../../specs/sidecar/common/outputs.md#validation-rules).
The derivation goes into
[`batch_artifacts`](../../specs/sidecar/common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).
A legacy sidecar keeps its concrete batch axis, and its meaning does not change.

## Reason

- The spec requires `-1` as the batch axis of `input.shape` (`V-common.sizes_and_artifacts-2`). For
  `outputs[].shape`, it says only that "`-1` marks a dynamic dimension". The spec examples write `-1`.
- Two exporters write the smallest native batch of the first size (`1`) in `outputs[].shape[0]`.
  Their sizes list the batches 1, 2 and 3. Thus the top-level shape is correct for one group only.
- The sentence "When a size lists only one batch key, the top-level `outputs[].shape` can replace the
  `output_shapes` of each group" is ambiguous with a concrete batch. For example, size A lists only
  `"1"`, and size B lists only `"2"`. A top-level `[1, 300, 6]` is then wrong for size B. With `-1`
  and the derivation, each group gets its correct shape.

## Evidence

- Ultralytics-Exporter `yolo_sidecar.py` at commit `f52ef68`: `_representative` (lines 342-349)
  selects the first size and its smallest batch. `_output_contracts` (lines 436-455) copies the shape
  of that artifact into `outputs[].shape` (line 453). The generated
  `exports/detectors/object_detectors/yolo26/yolo26.yaml` (git-ignored; the repo HEAD is `2e0280e`)
  has `shape: [1, 300, 6]`, and its `nano` size lists the batch keys `"1"`, `"2"` and `"3"`.
- Qualcomm-Exporter `qai_sidecar.py` at commit `4ca4586`: `write_component_sidecar` sets
  `representative_batch = min(artifacts)` (line 111). It writes
  `output_shape = [representative_batch, ...]` (line 113) as `outputs[].shape` (line 118).
  `_batch_artifacts` (lines 79-95) writes `output_shapes` only when a size has more than one batch.
- The [Outputs](../../specs/sidecar/common/outputs.md#examples) example writes
  `shape: [-1, -1, 5]` and `shape: [-1, -1, 17, 3]`.

## Alternatives rejected

- **A concrete batch axis that is the smallest native batch.** It is correct for one group only. The
  replacement sentence stays ambiguous across sizes.
- **Require `output_shapes` on every group.** Each single-batch size then repeats the top-level shape.
  A concrete top-level batch still disagrees with the other groups.
