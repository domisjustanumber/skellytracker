# 52NQ — Spec change: model-id-suffix

**Status:** absorbed into [`common/identity.md#keypoint-detector-id`](../../common/identity.md#keypoint-detector-id), 2026-11-09 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-06. The record is
[`proposal.md`](../../proposals/model-id-suffix/proposal.md)
(proposal-model-id-suffix@openmmlab-exporter@v3). Its follow-up
[ADR-KZ9J](KZ9J-model-id-suffix-rtmo-removed.md) lands in the same content commit.

- Sections: [`common.identity`](../../common/identity.md) and
  [`format.file_layout`](../../format/file-layout.md).
- Change: the `model_id` of a keypoint detector is `{family}-{group}` or
  `{family}-{group}-{variant}`, in the folder `detectors/keypoint_detectors/{family}/{group}/`.
  `{group}` is a body region (`hand`, `face`, `body`, `wholebody`) or a keypoint set with its
  keypoint count, for example `wholebody133` or `coco17`. The heading
  [Keypoint detector id](../../common/identity.md#keypoint-detector-id) gives the grammar. New rule
  `V-common.identity-7`: the id starts with the family and the group of its folder. New rule
  `V-common.identity-8`: the form of the group, and the number of a keypoint set equals
  `len(pose.tracked_points)`. The `{part}` of the storage layout becomes `{group}`. A data-only
  vector file `vectors/common.identity.yaml` has 12 validator cases.
- Target spec version: `2.0.0`.
- Models: RTMW (`rtmw-wholebody133`) and RTMO body7 (`rtmo-coco17-body7`), OpenMMLab-Exporter.
- Supersedes: none.
- The user confirmed three plan decisions on 2026-11-06. The spec gets an id grammar with a
  keypoint-set group and a variant suffix, so the exporter keeps `rtmw-wholebody133`. The spec
  takes the exporter grammar `{family}-{keypoints}[-{training}]` in `{family}/{keypoints}/`
  (OpenMMLab-Exporter ADR-0039). The keypoint-set pattern stays `^[a-z]+[1-9][0-9]*$`, so a set
  name with an inner digit, for example `h36m17`, waits for a model that needs it.
- The user accepted the proposal on rows F1 and L1, which are `exact`. The rules check the file
  path, so they also apply to a sidecar with both roles under `keypoint_detectors/`.
- The example `rtmo-body7` breaks `V-common.identity-7`. A user ruling gives it no rebuild, so the
  content commit removes it
  ([ADR-YS4C](../../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md); ADR-KZ9J).

## Reason

The id `{family}-{part}` could not hold a suffix after the part. Two models of one family and one
part got one id: RTMPose COCO-17 and Halpe-26 both became `rtmpose-body`. The id did not tell the
keypoint set. The [spec defects](../open-work.md#spec-defects) listed this item. The content commit
of this entry removes it.

## Evidence

Parity: none. A name changes no tensor and no decoded output. The vectors are `unverified`: no
validator implements the two new rules.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- Each case of the vector file checks only `V-common.identity-7` and `-8`. Its `input.sidecar`
  is partial, so the other rules of the section would fail on it.
- No case tests the pattern branch of `V-common.identity-7`. A later version can add one.
- The workflow copies of the old rule change in a separate non-spec commit with its own entry
  ([Workflow changes](../../model-addition-workflow/hand-over.md#workflow-changes)).
- The RTMW example lands after this change, in `rtmw/wholebody133/`, so part 7 needs no row for it.
