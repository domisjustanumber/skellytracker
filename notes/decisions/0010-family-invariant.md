# 0010 — Family invariant: a size sets only its shape, target size and artifacts

**Status:** accepted, 2026-10-22 (backfilled from #81).

## Decision

At `schema_version >= vNEXT`, a size entry (`sizes.<size>`) may set only these keys:

- `input.shape`;
- `input.resize.target_size`;
- `onnx`.

Any other key in a size entry is invalid. Examples are `role`, `outputs`, `batching`, `decode`, `pose`,
`overlay`, `input.normalization`, `input.color_format` and `input.resize.method`.

A family has exactly one preprocessing contract and one post-processing contract. If two sizes need a
different channel order, normalization, resize method, output semantics, selection mode, NMS
parameters or class mapping, they must be different families. Each family has its own sidecar.

The host still deep-merges a size entry over the top level. It uses the same merge rules as `base`.
A size entry holds only the three keys above.

A sidecar with `schema_version < vNEXT` keeps the old rule. The host deep-merges every key of its size
entries over the top level. The spec states this in the size-level keys row of
[Version-aware compatibility](../../specs/sidecar-spec.md#version-aware-compatibility).

The spec states the rule in these places:

- change 12 of the [Summary of changes](../../specs/sidecar-spec.md#summary-of-changes);
- [`sizes`](../../specs/sidecar-spec.md#sizes);
- [Model sizes within a family](../../specs/sidecar-spec.md#model-sizes-within-a-family);
- the `vNEXT` size-entry rule in [Validation rules](../../specs/sidecar-spec.md#validation-rules).

## Reason

- The earlier spec text contradicted itself. One sentence said that a size is a partial document that
  the host deep-merges over the top level. Another sentence said that all sizes share the output
  contract. The invariant keeps the sharing rule and removes the override.
- With the invariant, a size cannot redeclare `outputs`, `decode` or `pose`. The validation rule "All
  sizes share the same output names, semantics, and keypoint/class counts" still applies. It checks the
  `output_shapes` of each size.
- RTMDet needed it. A person-only RTMDet family and an 80-class RTMDet family have different NMS
  contracts and different class counts. They cannot be sizes of one family.

## Evidence

- The exporter coverage plan (`notes/sidecar-exporter-coverage.md`) applies the invariant to
  the RTMDet sizes whose backbones take RGB input (ConvNeXt-B and Swin-B). The CSPNeXt sizes take BGR
  input. The coverage plan puts the RGB sizes in a family of their own. OpenMMLab-Exporter 0004 records the
  channel order of each family. The RGB sizes later left that exporter with their weights
  (OpenMMLab-Exporter 0004 and OpenMMLab-Exporter 0005).
- Every size entry in the sidecars of the package sets only `input.shape`, `input.resize.target_size`
  and `onnx`. This holds for `rtmpose-body.yaml`, `rtmpose-hand.yaml`, `rtmpose-face.yaml`,
  `rtmw-wholebody.yaml` and `yolox.yaml` (checked on 2026-10-22).
- The code does not enforce the `vNEXT` rule, and it does not implement the legacy rule either. In
  `skellytracker/core/sidecar/model.py`:
  - `SidecarModel.sizes` is a raw `dict[str, dict[str, Any]]`.
  - `SidecarModel.resolved_size` deep-merges the whole size entry over the top level with
    `_deep_merge`.
  - `resolved_size` then validates only `input` and `onnx` with `SizeSpec`. It drops a size-level
    `decode`, `pose` or `outputs` without an error.
- The detectors read only `input.shape`, `input.resize.target_size` and `onnx` from the resolved size
  (`sidecar_model_spec` in `skellytracker/core/sidecar/runtime.py`, and the `input_size` property of
  each detector config). Each detector passes the top-level `_SIDECAR.input` to `preprocess_image`. A
  size-level `input.normalization` or `input.resize.method` therefore has no effect.

## Alternatives rejected

- Let a size override any key. This was the earlier spec text. It contradicts the rule that sizes
  share the output contract.

## Not repeated

- Do not add a size-level override for normalization, channel order, resize method or decode. Make a
  new family instead.
- Do not read `sizes.<size>` as a partial document that can replace any top-level key.
- Do not rely on the code to reject a bad size entry. `resolved_size` does not check it.
