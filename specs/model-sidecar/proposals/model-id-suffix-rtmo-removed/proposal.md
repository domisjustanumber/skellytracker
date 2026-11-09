# Change proposal: model-id-suffix-rtmo-removed

This file uses ASD-STE100 Simplified Technical English.

This bundle is a follow-up of the bundle `proposal-model-id-suffix@openmmlab-exporter` (the base,
skellytracker ADR-52NQ). It holds only the parts of the base that change, under the headings of the
base. A part that does not change says "No change". The text of the base applies to that part. The
session lands the base and this follow-up in one content commit ("Read a response" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`).

The change: the reference example `rtmo-body7` is removed, not rebuilt. The basis is:

- the user ruling of 2026-11-09 that names the example: item 7 of skellytracker ADR-YS4C, the root
  entry that supersedes skellytracker ADR-NB5F. Under item 6 of that entry, the content commit
  removes the example in place of the wait for a rebuild bundle. Step 12 of "When a spec change
  makes an example invalid" in `specs/model-sidecar/model-addition-workflow/reference-examples.md`
  gives the steps. A part 7 row of the removed example is not a request.
- [OpenMMLab-Exporter ADR-8QD0](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/b513d2e31ebef95e2dde5d8561ef731614854167/decisions/entries/8QD0-yolox-and-rtmw-only-0039-ids-in-sidecar.md),
  item 1: the family `rtmo-coco17-body7` is deferred. It gets no sidecar work and no rebuild bundle.

This follow-up makes the three changes of the response r6 of the base: two rows of part 2.1 and one
row of part 7.

## Header

| Field | Value |
|---|---|
| Title | Follow-up of model-id-suffix: the reference example `rtmo-body7` is removed, not rebuilt |
| Slug | `model-id-suffix-rtmo-removed` |
| Date | 2026-11-09 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `3e326df00726df8110773ed62cf38d02948a71a5` |
| Model, and its `model` bundle ID | As the base: `rtmw-wholebody133`, `model-rtmw-wholebody133@openmmlab-exporter`. The removed example is of `rtmo-coco17-body7`. This family is deferred, and it has no `model` bundle. |
| Intake rows with the verdict `near-miss` or `gap` | None (as the base). |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `follow-up` |
| Base bundle of a follow-up (`base`, or `none`) | `proposal-model-id-suffix@openmmlab-exporter` |
| Proposed section ID (the `id` in the section file's front matter) | `common.identity` (primary); `format.file_layout` (second). As the base. |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/common/identity.md`; `specs/model-sidecar/format/file-layout.md`. As the base. |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none. The base is the `base` of this bundle, not a `depends_on` item. |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | skellytracker ADR-52NQ: it records the base. This follow-up builds on it. It does not compete with it. The Proposed table of the root log is empty. skellytracker ADR-YS4C is `accepted`. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `4b1b2dfe0e3747d00eca8f61db8a7d47fc43d66f` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

No change.

## 2. Spec change

### 2.1 Sections

The sections, the titles, the kinds and the selectors do not change. No section-map row changes.

**Places that the change edits.** Each row below replaces the row of the base table with the same
Place and Heading. The Heading cells leave out the line numbers of the base. Each other row of the
base table stays.

| Place | Heading | Edit |
|---|---|---|
| `common.identity` | Authoring guidance, first bullet | Replace "Write the family id as `model_id`." with "Write the family id as the `model_id` of an object detector. For a keypoint detector, write `{family}-{group}` or `{family}-{group}-{variant}` (heading "Keypoint detector id")." In the values in use, replace `rtmw-wholebody` with `rtmw-wholebody133` and `rtmo-body7` with `rtmo-coco17-body7`: these are the ids that OpenMMLab-Exporter writes now. After the list, add "The reference example `rtmw-wholebody` has an older OpenMMLab-Exporter id. The re-export request rebuilds it." Replace the citations `rtmw/identity.py:25-28` and `rtmo/identity.py:24-27` at `eed3361aa31e02df160c33a18a3db9ba182b5551` with `rtmw/identity.py:33-36` and `rtmo/identity.py:39-42` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. (The change from the base: the added sentence does not name `rtmo-body7`, because the content commit removes that example under skellytracker ADR-YS4C.) |
| `specs/model-sidecar/decisions/open-work.md` | Re-export requests, "Rebuild of each example" | Remove `rtmo-body7` from the examples that the item rebuilds. Keep `rtmw-wholebody`. The base gives "No edit", with the list "OpenMMLab-Exporter: `rtmdet-person`, `rtmw-wholebody`, `rtmo-body7`." The item text at skellytracker commit `c34c2cf8363539dd56376251195ac7172b6c2ac2` already has this edit, and the text at the commit of the header is the same: "OpenMMLab-Exporter: `rtmw-wholebody`, as `rtmw-wholebody133`. A user ruling gives no rebuild to `rtmdet-person`, `rtmo-body7`, `yolo26` and `yolo26-body`." |

### 2.2 Fields table

No change.

### 2.3 Behaviour

No change.

### 2.4 Validation rules

No change.

### 2.5 Selectors

No change.

### 2.6 Changelog row

No change.

## 3. Reference implementation

No change. The base has no reference file, and this follow-up has none.

## 4. Vectors

No change. No case is new, and no case changes. This bundle has no vector file.

## 5. Parity evidence

No change (none in the base: no runtime effect).

## 6. skellytracker implementation proposal

No change.

## 7. Exporter impact

The exporter table of the base does not change. The row below replaces the row of the base table
"Reference examples that the change makes invalid" with the same Example.

**Reference examples that the change makes invalid.**

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` | `V-common.identity-7` | Removal under skellytracker ADR-YS4C (user ruling), in place of `needs-export` | `rtmo-body7` in `rtmo/body/` does not start with `rtmo-body-`. The user ruling of 2026-11-09 gives the example no rebuild (skellytracker ADR-YS4C item 7, after [OpenMMLab-Exporter ADR-8QD0](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/b513d2e31ebef95e2dde5d8561ef731614854167/decisions/entries/8QD0-yolox-and-rtmw-only-0039-ids-in-sidecar.md)). The content commit removes the example with step 12 of "When a spec change makes an example invalid" in `specs/model-sidecar/model-addition-workflow/reference-examples.md`. It does not wait for a rebuild bundle. This row is not a request. |

## 8. Alternatives considered

**Reason for this follow-up.** The base is accepted. The base waits for the rebuild bundle of
`rtmo-body7` (part 7, `needs-export`). The user ruling of 2026-11-09 gives that example no rebuild.
skellytracker ADR-YS4C item 7 records the ruling, after
[OpenMMLab-Exporter ADR-8QD0](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/b513d2e31ebef95e2dde5d8561ef731614854167/decisions/entries/8QD0-yolox-and-rtmw-only-0039-ids-in-sidecar.md).
The response r6 of the base (`needs-contributor`) asks for a follow-up with three changes, and this
bundle makes them. A follow-up can change part 2 of its base and give the reason in part 8 ("Section
owner" in `specs/model-sidecar/model-addition-workflow/hand-over.md`).

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason. A part that does not change says "No change".
- [x] The intake names the bundle ID of this proposal. n/a: the follow-up changes no intake row. The RTMW intake names the base.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. n/a: part 1 does not change.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`. n/a: part 1 does not change.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle. n/a: no algorithm.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`. n/a: no case changes.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`. n/a: no case changes.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script. n/a: no runtime effect.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. n/a.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
