# 0022 — Depth divisor of MediaPipe landmarks

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Add an optional divisor of the raw depth to
[`pose.decode`](../../specs/sidecar/post/pose-schema.md#posedecode), for a `coordinate` decoder with
`depth_unit: pixel`. The MediaPipe-Exporter plan names it `depth_normalize`. The decoded depth is
`z = z_raw / depth_normalize`, in pixels of the model input. The default is `1.0`, so a sidecar
without the field keeps its current meaning. The proposal must also state how the host unprojects a
`pixel` depth to the source image. The exact text comes with the full proposal of
[0014](0014-spec-lifecycle.md#new-model-workflow) from the exporter overhaul, with an ONNX file and a
committed parity script that compares `z`. The decision must also say whether the change goes into
`vNEXT` or into a later revision, because the `vNEXT` scope of [0008](0008-vnext-scope.md) does not
include MediaPipe-Exporter.

## Reason

- For the hand landmark model, MediaPipe's `TensorsToLandmarksCalculator` computes
  `z / 224 / normalize_z`, with `normalize_z: 0.4`. The ONNX file returns the raw `z` in crop pixels.
  Thus the depth that MediaPipe reports needs a second divisor.
- `pose.decode` has the fields `method`, `is_3d`, `depth_unit`, `coordinate_scale` and `depth_range`.
  `depth_unit: pixel` means "scaled by the image width". It cannot carry the `0.4`. Thus two hosts can
  report depths that differ by a factor of 2.5.
- The historical Qualcomm-Exporter wrapper multiplied `z` by the input width and declared
  `depth_unit: pixel`. This shows a second reading of `pixel`.

## Evidence

No commit and no parity result exist for the plan facts. MediaPipe-Exporter has no git repo.

- The untracked hand plan of MediaPipe-Exporter (plan facts): `z` is
  `z / 224 / normalize_z` with `normalize_z: 0.4`, in MediaPipe `tensors_to_landmarks_calculator.cc`.
  The plan writes
  `decode: {method: coordinate, coordinate_scale: pixel, is_3d: true, depth_unit: pixel, depth_normalize: 0.4}`.
- Qualcomm-Exporter at commit `c7b9132`: `qai_catalog.py`, `make_landmark_module` (lines 336-361),
  multiplies `(x, y, z)` by `(W, H, W)`. `qai_sidecar.py` (lines 251-259) writes `depth_unit: pixel`.
  `README.md` (lines 147-149) says that the third channel is relative, not metric depth.

## Alternatives rejected

- **Scale `z` in an exporter wrapper** (the historical Qualcomm-Exporter approach, with the width).
  Each exporter can then choose a different scale, and the sidecar does not show which one.
