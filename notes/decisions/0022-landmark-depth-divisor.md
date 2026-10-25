# 0022 — Depth divisor of MediaPipe landmarks

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only); completed 2026-10-25 (MediaPipe-Exporter
proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `landmark-depth-divisor`.
The eight parts are in
[`specs/sidecar/proposals/landmark-depth-divisor/proposal.md`](../../specs/sidecar/proposals/landmark-depth-divisor/proposal.md).

- **Section:** `post.pose.decode.coordinate` (changed). The proposal also edits `post.pose.schema`
  (the text of `depth_unit` and `V-post.pose.schema-9`), `post.unprojection` (one sentence),
  `format.versioning` (the legacy row), the changelog and the model intake template.
- **Change:** A new optional field `pose.decode.depth_normalize` (a finite number `> 0`, default
  `1.0`) and a new heading "Depth". For `is_3d: true` and `depth_unit: pixel`, the host computes
  `z_in = c * z_raw / depth_normalize`. `c` is the factor of `x` for `coordinate_scale`. Then the host
  computes `z_src = z_in * k`. `k` is the length of the image of a unit `x` step under the resize
  inverse, for example `k = wc / T_w` for `rotated_roi_crop`. The new rule
  `V-post.pose.decode.coordinate-2` allows the field only with `method: coordinate`, `is_3d: true` and
  `depth_unit: pixel`. The changed `V-post.pose.schema-9` allows `depth_unit: pixel` only with
  `method: coordinate` at `vNEXT`.
- **Version:** `vNEXT` (exporter user decision H2). A sidecar with `schema_version < vNEXT` cannot
  declare the field. The heading "Depth" does not apply to it.
- **Models:** the MediaPipe hand landmark model `mediapipe-hand21` (`depth_normalize: 0.4`, MediaPipe
  `kLandmarksNormalizeZ`). The MediaPipe pose and face landmark models need no field (the default
  `1.0`).
- **On acceptance:** this entry supersedes no entry.
- **Related:** the proposal depends on `roi-transform-and-source`
  ([0020](0020-roi-transform-and-source.md)) for `rotated_roi_crop` and its crop ROI `Rc`. It depends
  on the scope entry `vnext-scope-mediapipe-rotated-crops`
  ([0048](0048-vnext-scope-mediapipe-rotated-crops.md)), which adds MediaPipe-Exporter to the `vNEXT`
  scope of [0008](0008-vnext-scope.md). These land first. `landmark-extra-outputs`
  ([0021](0021-landmark-extra-outputs.md)) can land before or after this proposal. `keypoint-visibility`
  ([0039](0039-keypoint-visibility.md)) changes the same single-person form. Other merge points are
  `roi-refiner-role` ([0047](0047-roi-refiner-role.md)), `pose-decode-flip-test`
  ([0045](0045-pose-decode-flip-test.md)), `heatmap-decode-refinement`
  ([0038](0038-heatmap-decode-refinement.md)) and gap record
  [0023](0023-letterbox-floor-and-scale-inverse.md).

## Reason

The hand landmark model returns the raw `z` in crop pixels. MediaPipe divides it by `0.4`. The spec
has no field for that divisor and no rule that maps a `pixel` depth to the source image. Without the
divisor, the depth error has a median of 13.4 px on an image set. With the divisor, the median is
0.216 px. These numbers come from an uncommitted scratch script of MediaPipe-Exporter, so they are
not evidence. Parity is `to run`. The parity script of MediaPipe-Exporter does not exist yet, and
it cannot get a commit while MediaPipe-Exporter has no git repo.

### Gap record (2026-10-23)

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

## Open work

See [Open work](README.md#open-work).
