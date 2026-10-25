# 0021 — Pose outputs beside the landmarks: presence, handedness and world landmarks

**Status:** proposed, 2026-10-23 (from the exporter evidence of MediaPipe-Exporter and
Qualcomm-Exporter; plan facts and historical code only); completed 2026-10-25 (MediaPipe-Exporter proposal);
recorded again 2026-10-25 (MediaPipe-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `landmark-extra-outputs`. The
eight parts are in
[`specs/sidecar/proposals/landmark-extra-outputs/proposal.md`](../../specs/sidecar/proposals/landmark-extra-outputs/proposal.md).

- **Section:** a new section `post.pose.extra_outputs` ("Extra pose outputs", file
  `specs/sidecar/post/pose-extra-outputs.md`, kind `postprocessor`). The change also edits
  `common.outputs`, `post.pose.schema`, `post.pose.decode.coordinate`, `format.versioning`, the
  section map, the changelog and the model intake template.
- **Change:** A model with `pose.estimator_type: top_down_single_person` and
  `pose.decode.method: coordinate` can declare at most one output of each new `semantic`:
  `presence`, `binary_class` and `world_keypoints`. A `presence` output declares `activation`
  (`none` or `sigmoid`) and `score_threshold_default` in `[0, 1)`. The host gives no pose for an
  item that fails the strict test `p > t`, where `t` is a runtime threshold. A `binary_class` output
  declares `labels` (the value is the probability of `labels[0]`), and a `world_keypoints` output
  `[N, K, 3]` declares `unit` (`m` or `mm`) and gets the rotation of the crop ROI. The new rules are
  `V-post.pose.extra_outputs-1` to `-7`, and the rules `V-common.outputs-4` and
  `V-post.pose.schema-7` change.
- **Version:** `vNEXT` (user decision H2 of the proposal). A sidecar with `schema_version < vNEXT`
  cannot declare the new semantics or their fields. The `vNEXT` scope of
  [0008](0008-vnext-scope.md) does not include MediaPipe-Exporter. The scope entry
  `vnext-scope-mediapipe-rotated-crops` ([0048](0048-vnext-scope-mediapipe-rotated-crops.md)) adds
  it.
- **Models:** the MediaPipe hand landmark model of MediaPipe-Exporter, `hand_landmark_full` (the
  size `lite` has the same four outputs), `model_id` `mediapipe-hand21`. The five package sidecars
  do not change.
- **On acceptance:** this entry supersedes no entry. Its status changes to `accepted`.
- **Related:** `roi-transform-and-source` ([0020](0020-roi-transform-and-source.md)) must land
  first, because step 4 uses the crop ROI `Rc` of `rotated_roi_crop`. The scope entry 0048 must
  also come first. `landmark-depth-divisor` ([0022](0022-landmark-depth-divisor.md)) changes the
  same model. `roi-refiner-role` ([0047](0047-roi-refiner-role.md)) uses the same field
  `score_threshold_default` and the same range. `keypoint-visibility`
  ([0039](0039-keypoint-visibility.md)) adds per-point values and edits the same single-person form.
  Other proposals edit the same spec text. The second content PR rebases on the first. The "Before
  acceptance" heading of the proposal lists them.

## Reason

The spec can describe only the landmarks of the MediaPipe hand landmark model. The closed `semantic`
set has no value for a presence score, a class probability or world keypoints.
`V-post.pose.schema-7` allows one `keypoints` output for a `coordinate` decoder. Without the presence
gate, a host gives landmarks for each crop: 31 of 116 image crops and 101 of 438 video hand-frames
have no hand in `HolisticLandmarker`. These numbers come from a scratch script with no commit. They
are not evidence.

The proposal corrects two facts of the gap record below. MediaPipe uses the strict test `> 0.5`
(`ThresholdingCalculator`), not `>= 0.5`. The handedness value is the probability of label item 0,
`Right`, not the probability of `Left` for a mirrored image. The proposal is not ready for
acceptance. Its parity (part 5) is `to run`. The side that `Right` names has only secondary
evidence: OpenMMLab-Exporter 0041 and 0052 and the legacy MediaPipe docstring. The exporter records
an untracked plan decision of OpenMMLab-Exporter (T45) that accepts them in place of a primary
source. The user has not decided this exception.

### Gap record (2026-10-23)

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

No commit and no parity result exist for the plan facts. MediaPipe-Exporter has a git repo since
2026-10-25 (commit `8f708a1ddecd8e035de15a5a9a7b652af035a58a`), but its plan facts, the proposal and
the reference file are in its git-ignored `plans/` folder. MediaPipe-Exporter 0003 and 0006 (tracked)
are parity of the conversion and of the reference hand branch, not of this section. The parity of
the proposal (part 5) is `to run`. The Qualcomm-Exporter hand plan is not tracked.

- OpenMMLab-Exporter 0052 (status `evidence`; on 2026-10-25 its commit is on the local
  OpenMMLab-Exporter `main`, not on `origin/main`): the upstream `HandLandmarker` of `mediapipe`
  1.1.1 gives +0.861 on images that are not mirrored and -0.862 on mirrored images. Thus `Right`
  names the right hand of the person in an image that is not mirrored. The legacy API reads the
  label file of the model metadata (`Left` at item 0). The Tasks graph puts `Right` at item 0.

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

## Open work

See [Open work](README.md#open-work).
