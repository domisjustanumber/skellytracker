# 0021 — Pose outputs beside the landmarks: presence, handedness and world landmarks

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Let a single-person `coordinate` pose model declare three kinds of output
beside its one `keypoints` output: an instance presence score, an instance class probability and 3D
world keypoints. The closed `semantic` set of [Outputs](../../specs/sidecar/common/outputs.md#fields)
gets a value for each kind (the exporter plans use `score` and `keypoints_3d`). A presence output
declares its activation and a default threshold, and the host drops the landmarks of a crop whose
presence score fails that threshold. The proposal must state the comparison, because MediaPipe uses
`>= 0.5`. A class-probability output declares the class that its value gives, and whether the model
expects a mirrored image. A world-keypoint output declares its unit.
[`V-common.outputs-4`](../../specs/sidecar/common/outputs.md#validation-rules) and
[`V-post.pose.schema-7`](../../specs/sidecar/post/pose-schema.md#validation-rules) change to allow
these outputs. The field names and the threshold rule come with the full proposal of
[0014](0014-spec-lifecycle.md#new-model-workflow) from the exporter overhaul, with an ONNX file and a
committed parity script. The decision must also say whether the change goes into `vNEXT` or into a
later revision, because the `vNEXT` scope of [0008](0008-vnext-scope.md) does not include
MediaPipe-Exporter.

## Reason

- A MediaPipe hand landmark model has four outputs: `landmarks [B, 21, 3]`, `hand_score [B]`,
  `handedness [B]` and `world_landmarks [B, 21, 3]` in metres. The spec can describe only the first.
- The output `semantic` set is closed. It has no score for the pose role and no 3D world keypoints.
  `V-post.pose.schema-7` allows exactly one `keypoints` output for a `coordinate` decoder. The fields
  `unit`, `positive_class` and `assumes_mirrored_input` do not exist.
- The landmark model always emits landmarks, also for a crop with no hand. Without the presence
  output, a host cannot reject an empty crop. The historical Qualcomm-Exporter wrapper kept only the
  landmarks, so its host could not gate on presence.
- The two exporter plans do not agree on the handedness class (see "Evidence"). A spec field must
  fix the class that the value gives.

## Evidence

No commit and no parity result exist for the plan facts. MediaPipe-Exporter has no git repo, and the
Qualcomm-Exporter hand plan is not tracked.

- The untracked hand plan of MediaPipe-Exporter (plan facts): `hand_score [B]` is the
  presence probability (sigmoid in the graph), and `>= 0.5` means a hand. `handedness [B]` is the
  probability of `Left` (MediaPipe label 0) for a mirrored image. `world_landmarks [B, 21, 3]` is in
  metres. The plan gives `hand_score` and `handedness` the semantic `score`, with
  `positive_class: left` and `assumes_mirrored_input: true`. It gives `world_landmarks` the semantic
  `keypoints_3d`, with the unit `m`.
- The same plan: hidden or gloved hands still give landmarks. On noise inputs, `hand_score` stays
  between 0.003 and 0.011.
- The untracked hand plan of Qualcomm-Exporter (plan facts): `hand_score` with
  `semantic: score`, and `handedness` with `semantic: score` and `positive_class: right`.
- Qualcomm-Exporter `qai_catalog.py` at commit `c7b9132`, `make_landmark_module` (lines 336-361): the
  wrapper returns only `out[-1]`, the landmarks, scaled to pixels. It drops the other outputs.

## Alternatives rejected

- **Drop the extra outputs in an exporter wrapper** (the historical Qualcomm-Exporter approach). The
  host then cannot reject a crop with no hand.
