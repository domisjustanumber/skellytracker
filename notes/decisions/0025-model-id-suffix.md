# 0025 — Suffix after the part in `model_id`

**Status:** proposed, 2026-10-23 (from the exporter evidence of OpenMMLab-Exporter, and the proposed
models of MediaPipe-Exporter and Qualcomm-Exporter in the sidecar inventory).

## Decision

**Proposed, not decided.** This entry is a gap record (see [Rules](README.md#rules)). It does not
have the eight parts of a proposal.

Let the `model_id` of a keypoint detector have a suffix after the part. The id starts with
`{family}-{part}`. The `model_id` row of [Identity](../../specs/sidecar/common/identity.md#fields)
changes. [`V-common.identity-1`](../../specs/sidecar/common/identity.md#validation-rules) does not
change. The full proposal must give the grammar of the suffix, because the ids in use do not agree:
`rtmo-body7` has no hyphen before the suffix, and `mediapipe-hand-landmark` has one. The full
proposal must also say when a model needs a suffix, and when a variant is a new family instead.

## Reason

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
  [`rtmo/body/rtmo-body7.yaml`](../../specs/sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml)
  has `model_id: rtmo-body7` (line 3) in the `body` part folder.
- The `proposed` models of [`specs/sidecar/inventory.yaml`](../../specs/sidecar/inventory.yaml) have
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
