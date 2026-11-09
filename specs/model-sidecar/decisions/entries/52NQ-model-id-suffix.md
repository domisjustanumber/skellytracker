# 52NQ — Spec change: model-id-suffix

**Status:** proposed, 2026-11-06 (proposal-model-id-suffix@openmmlab-exporter@v2);
recorded again 2026-11-09 (proposal-model-id-suffix@openmmlab-exporter@v3).

## Decision

**Proposed, not decided.** The proposal is
[`proposal.md`](../../proposals/model-id-suffix/proposal.md).

- Sections: [`common.identity`](../../common/identity.md) and
  [`format.file_layout`](../../format/file-layout.md).
- Change: the `model_id` of a keypoint detector is `{family}-{group}` or
  `{family}-{group}-{variant}`, in the folder `detectors/keypoint_detectors/{family}/{group}/`.
  `{group}` is a body region (`hand`, `face`, `body`, `wholebody`) or a keypoint set with its
  keypoint count, for example `wholebody133` or `coco17`. A new Behaviour heading gives the
  grammar. New rule `V-common.identity-7`: the id starts with the family and the group of its
  folder. New rule `V-common.identity-8`: the form of the group, and the number of a keypoint set
  equals `len(pose.tracked_points)`. The `{part}` of the storage layout becomes `{group}`. A new
  data-only vector file `vectors/common.identity.yaml` has 12 validator cases.
- Target spec version: `2.0.0`.
- Models: RTMW (`rtmw-wholebody133`) and RTMO body7 (`rtmo-coco17-body7`), OpenMMLab-Exporter.
- Supersedes on acceptance: none.
- Related: `model-rtmw-wholebody133@openmmlab-exporter` names this bundle for its rows F1, L1 and
  F5. These rows are `exact`, so the model does not wait for this proposal.

## Reason

The current id `{family}-{part}` cannot hold a suffix after the part. The reference example
`rtmo-body7` in `rtmo/body/` breaks it, which is a recorded spec defect
([open-work.md](../open-work.md#spec-defects)). Two models of one family and one part get one id:
RTMPose COCO-17 and Halpe-26 both become `rtmpose-body`. The id does not tell the keypoint set.

## Evidence

Parity: none. A name changes no tensor and no decoded output. The vectors are `unverified`: no
validator implements the two new rules. v2 fixed both findings of the response to v1. v3 scopes
each vector case to `V-common.identity-7` and `-8`, removes the unlisted sentence of part 2.1 and
records the keypoint-set pattern as plan decision 3 of part 1. The normative text does not change.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- [x] The user must confirm or refuse each plan decision of part 1:
  - the spec gets an id grammar with a keypoint-set group and a variant suffix, and the exporter
    does not rename `rtmw-wholebody133` to `rtmw-wholebody`;
  - the spec adopts the exporter grammar `{family}-{keypoints}[-{training}]` in
    `{family}/{keypoints}/` (OpenMMLab-Exporter ADR-0039);
  - the keypoint-set pattern stays `^[a-z]+[1-9][0-9]*$`, so `h36m17` waits for a model that
    needs it.

  The user accepted the proposal with these decisions on 2026-11-06. (changed 2026-11-09)
- [x] Part 2.4 says "The rules keep both V-common.identity-7 and V-common.identity-8 unchanged (a user
  decision)". Part 1 does not list this decision, and the sentence does not say what is unchanged.
  v3 removes the sentence.
- [x] Each `input.sidecar` of the vector cases is partial, so the other rules of `common.identity`
  would fail on it. The cases expect `failed: []`. The cases must say that they check only
  `V-common.identity-7` and `-8`. This change of meaning needs a new version
  ([Changes at acceptance](../../model-addition-workflow/hand-over.md#changes-at-acceptance)).
  v3 says this in the file note, in each case note and in part 4.
- [x] No `near-miss` or `gap` row drives the proposal: rows F1 and L1 are `exact` with an exporter
  departure. The user decides if a proposal that the user asked for is acceptable on `exact` rows.
  The user accepted it on 2026-11-06.
- [x] The keypoint-set pattern `^[a-z]+[1-9][0-9]*$` refuses a set name with an inner digit, `_` or
  `-`, for example `h36m17`. The user kept the pattern on 2026-11-06. Part 1 and part 8 of v3 record it.
- [x] `V-common.identity-7` and `-8` check the file path. They also apply to the sidecars with both
  roles under `keypoint_detectors/`. The open both-roles defect can change that scope. The user
  accepted this scope with the proposal.
- The workflow copies of the old rule change in a separate non-spec commit with its own entry
  ([Workflow changes](../../model-addition-workflow/hand-over.md#workflow-changes)).
  `specs/sidecar-implementation-plan.md` also names `keypoint_detectors/{family}/{part}/`. The user
  decided this on 2026-11-06. Part 2.1 of v3 lists the copies. (changed 2026-11-09)
- Part 7: the example `rtmo-body7.yaml` becomes invalid (`needs-export`). A user ruling gives it
  no rebuild, so the content commit removes it
  ([ADR-YS4C](../../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md)). (changed 2026-11-09)
- Recording this entry makes OpenMMLab-Exporter the owner of `common.identity` and
  `format.file_layout` while the entry is `proposed`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).
- The content commit removes `rtmo-body7` with step 12 of
  [When a spec change makes an example invalid](../../model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid).
  Parts 2.1 and 7 say that the re-export rebuilds it. This change of meaning needs a follow-up
  bundle (`base` this bundle) that changes both parts. The session lands both in one content
  commit. (changed 2026-11-09)
- The content commit must add `V-common.identity-7` and `-8` to `common/identity.md` before
  `tools/make_vectors.py land` runs. `land` checks each `expect.failed` against the rule IDs of the
  section files. (new 2026-11-09)
- The RTMW example lands after this change, in `rtmw/wholebody133/`, so part 7 needs no row for
  it. (changed 2026-11-09)
- Note: no case tests the pattern branch of `V-common.identity-7`. Each `{family}` and
  `{variant}` of the cases matches `^[a-z0-9]+(-[a-z0-9]+)*$`, but part 4 says that the cases cover
  each branch. A later version can add a case. The session must not add one at acceptance.
  (new 2026-11-09)
