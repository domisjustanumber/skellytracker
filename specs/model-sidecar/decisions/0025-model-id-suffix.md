# 0025 — Suffix after the part in `model_id`

**Status:** proposed, 2026-10-23 (from the exporter evidence of OpenMMLab-Exporter, and the proposed
models of MediaPipe-Exporter and Qualcomm-Exporter in the sidecar inventory); completed 2026-10-25 (OpenMMLab-Exporter proposal).

## Decision

**Proposed, not decided.** This entry records the spec change proposal `model-id-suffix`. The eight
parts are in [`specs/model-sidecar/proposals/model-id-suffix/proposal.md`](../../specs/model-sidecar/proposals/model-id-suffix/proposal.md).

- **Section:** `common.identity` (changed). The storage layout of `format.file_layout` changes in the
  same contract unit.
- **Change:** The `model_id` of a keypoint detector is `{family}-{keypoints}` or
  `{family}-{keypoints}-{training}`, in the folder `detectors/keypoint_detectors/{family}/{keypoints}/`.
  `{keypoints}` is a set name and its point count, for example `coco17` or `wholebody133`.
  `V-common.identity-7` checks the id against the two folders. `V-common.identity-8` forbids one
  artifact `filename` in two sidecars of one folder. `V-common.identity-9` makes the count equal to
  `len(pose.tracked_points)`. A family uses `{training}` only when it has more than one upstream
  model with the same keypoint output (authoring guidance; OpenMMLab-Exporter user decision T14).
- **Version:** `vNEXT`. A sidecar with `schema_version < vNEXT` keeps its `{family}-{part}` id and its
  part folder. The four package sidecars stay legacy.
- **Models:** RTMO body7 (`rtmo-coco17-body7`), RTMW (`rtmw-wholebody133`), RTMPose Halpe26
  (`rtmpose-halpe26`), ViTPose 25 points (`vitpose-coco25`), ViTPose++ (`vitposepp-wholebody133`),
  DWPose (`dwpose-wholebody133-ubody`) and the YOLO26 pose forecast (`yolo26-coco17`).
- **On acceptance:** This entry supersedes no entry. The reference examples of RTMO, RTMW and YOLO26
  pose move to keypoint folders. The folder that the proposed entry
  [0017](0017-dual-role-sidecar-folder.md) names changes from `{part}` to `{keypoints}` for `vNEXT`.
- **Related:** `roi-refiner-role` ([0047](0047-roi-refiner-role.md)) gives the id and the folder of
  an ROI refiner outside this grammar. Either proposal can land first. The second one rebases.
  `size-codes` ([0046](0046-size-codes.md)) uses the ids of this proposal. Land this proposal first (soft order).
  `pose-decode-flip-test` ([0045](0045-pose-decode-flip-test.md)) uses the ids as model names only.

## Reason

The Identity text gives `{family}-{part}` for a keypoint detector. Thus one family and one part
get one id, one file name and one catalog key. RTMPose has a COCO-17 body model and a Halpe26 body
model. RTMO has a COCO-only model and a body7 model, both with 17 points. The `body` folder holds
models with 17, 25 and 26 points. A name changes no tensor and no decoded output, so the gap has no
measured difference. Part 5 of the proposal thus has no parity evidence. The vectors are
`unverified`: no host code runs them. The run of 84 of 84 cases used an uncommitted script, so it is
not evidence.

### Gap record (2026-10-23)

Let the `model_id` of a keypoint detector have a suffix after the part. The id starts with
`{family}-{part}`. The `model_id` row of [Identity](../../specs/model-sidecar/common/identity.md#fields)
changes. [`V-common.identity-1`](../../specs/model-sidecar/common/identity.md#validation-rules) does not
change. The full proposal must give the grammar of the suffix, because the ids in use do not agree:
`rtmo-body7` has no hyphen before the suffix, and `mediapipe-hand-landmark` has one. The full
proposal must also say when a model needs a suffix, and when a variant is a new family instead.

- The Identity text says that the `model_id` of a keypoint detector "is `{family}-{part}`". Thus it
  gives one id for each family and part. It cannot express a suffix, and it cannot give two models of
  one family and one part different ids.
- `V-common.identity-1` makes the file basename equal to `model_id`. Two models with one id thus get
  one file name in one part folder. The catalog key of [0016](0016-sidecar-catalogs.md) is
  `<model_id>@<source.name>`, so they also get one catalog key.
- The RTMO body7 reference example has a suffix. Thus an example of the spec does not agree with the
  text of the spec.
- RTMO has more than one variant for the body part. [0012](0012-fit-resize-for-rtmo.md) names coco
  and crowdpose variants beside body7.
- The exporters do not agree on the ids of the MediaPipe hand models (see "Evidence").

## Evidence

- OpenMMLab-Exporter `rtmo/identity.py` at commit `eed3361`: `FAMILY = "rtmo-body7"` (line 24) and
  `SIDECAR_FILENAME = "rtmo-body7.yaml"` (line 26). `FAMILY_BRANCH` (line 27) is
  `detectors/keypoint_detectors/rtmo/body7`.
- The reference example
  [`rtmo/body/rtmo-body7.yaml`](../../specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml)
  has `model_id: rtmo-body7` (line 3) in the `body` part folder.
- The `proposed` models of [`specs/model-sidecar/inventory.yaml`](../../specs/model-sidecar/inventory.yaml) have
  the keys `mediapipe-hand@qualcomm-exporter`, `mediapipe-hand-recrop@qualcomm-exporter`,
  `mediapipe-hand-landmark@mediapipe-exporter` and `mediapipe-hand-recrop@mediapipe-exporter`.
  Qualcomm-Exporter names the hand landmark model `mediapipe-hand`. MediaPipe-Exporter names the
  same model `mediapipe-hand-landmark`. The inventory takes these ids from the untracked plans of the
  two exporters (plan facts). No exporter code writes them: Qualcomm-Exporter has no
  `mediapipe-hand` string at commits `4ca4586` and `c7b9132`, and MediaPipe-Exporter has no code.

## Alternatives rejected

- **Rename the models to `{family}-{part}`.** The RTMO body7 example and OpenMMLab-Exporter must
  change. A family with two models for one part still gets one id, one file name and one catalog key
  for both.

## Open work

See the [Open work](README.md#open-work) list of the decision log.
