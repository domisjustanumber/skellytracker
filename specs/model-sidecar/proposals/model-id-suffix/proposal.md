---
slug: model-id-suffix
section: common.identity
exporter: OpenMMLab-Exporter
decision: "0025"
state: recorded
---

# Change proposal: model-id-suffix

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `model-id-suffix`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. The `python` code block at the end of part 3 is the reference file of the proposal, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | The keypoint output and the training set in the `model_id` of a keypoint detector |
| Slug | `model-id-suffix` (the slug of skellytracker decision 0025) |
| Date | 2026-10-25 (first version 2026-10-23; user decisions Q1 to Q4 and T14 applied 2026-10-23; M1, M2, T42 and the `gap`-row correction applied 2026-10-24; updated 2026-10-25: the pin moved to skellytracker `dom/21-move-sidecar-guide`, and the review fixes of the phase-1 audit were applied) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed; `git status --porcelain` is empty). Commit `1dfec48` is OpenMMLab-Exporter decision 0042 (the pipeline writes `source`, and the RTMDet and RTMW writers write `{filename, sha256}` for each artifact; the entry `notes/decisions/0042-sidecar-source-and-artifact-hashes.md`). Commit `f3aeb47` is OpenMMLab-Exporter decision 0050 (no family writes a sidecar while its intake is not `describes`; `notes/decisions/0050-no-sidecar-while-spec-pending.md`). Commit `d0f4343` added the T14 ids of RTMO and RTMW (OpenMMLab-Exporter decision 0039, `notes/decisions/0039-keypoint-model-id-format.md`; the constants `FAMILY`, `SIDECAR_FILENAME` and `FAMILY_BRANCH` at `rtmo/identity.py:39-42` and `rtmw/identity.py:33-36`; the writers set `"model_id": FAMILY` at `rtmo/sidecar.py:232` and `rtmw/sidecar.py:213` (at `f3aeb47`, since OpenMMLab-Exporter decision 0042; `:211` at `d0f4343`); the tests `test_model_id_is_family_keypoints_training`, `tests/test_rtmo.py:125-137` (`:116-128` at `d0f4343`), and `test_model_id_is_family_keypoints`, `tests/test_rtmw.py:80-90`; the example `notes/decisions/rtmo-coco17-body7.yaml`, which `tests/test_rtmo.py:29` and `:418` compare with the writer output). The line numbers were checked again at `f3aeb47` on 2026-10-24. |
| Model, and its intake file | `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 98 and 178); `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 108 and 187); `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 95 and 180; plan T11); `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 78 and 158; plan T15); `rtmw-wholebody133` (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 133 and 214, both `exact`; its exporter already writes the proposed id and folder, OpenMMLab-Exporter 0039); `rtmo-coco17-body7` (the untracked intake of `rtmo-coco17-body7` of OpenMMLab-Exporter (plan facts), rows F1 and L1 at lines 138 and 228; intake written 2026-10-24; its L1 also needs the folder of a sidecar with both roles, skellytracker 0017, which this proposal does not give) |
| Intake rows with the verdict `near-miss` or `gap` | Row F1 (`model_id`): `gap` for `rtmpose-halpe26`, `vitpose-coco25`, `dwpose-wholebody133-ubody` and `rtmo-coco17-body7`. The current text gives `{family}-{part}`, for example `rtmpose-body`, and another model of the same family and part needs that id (for Halpe26, the skellytracker package sidecar of RTMPose body (COCO-17) has it). Row L1 (sidecar path): `gap` for `rtmo-coco17-body7` only. Its intake gives two reasons: the storage layout has no branch for a sidecar with both roles (skellytracker 0017), and it has only the part folders `hand`, `face`, `body` and `wholebody`. **Not `gap` rows (correction of 2026-10-24).** Row L1 is `exact` in the intakes of `rtmpose-halpe26`, `vitpose-coco25`, `vitposepp-wholebody133` and `dwpose-wholebody133-ubody`, and in `rtmw-wholebody133`: a model-specific folder does not conform, so the sidecar value is the spec path, and the keypoint folder of the exporter is an exporter departure in the last column (`templates/model-intake.md:358-360`). Row F1 is `exact` for `vitposepp-wholebody133` (`vitposepp-wholebody`: no second `vitposepp` model has the part `wholebody`) and for `rtmw-wholebody133`. The last column of each of these rows names this proposal as the reason for the departure. Part 7 lists them. |
| Kind | `changed section` |
| Proposed section ID | `common.identity` (the storage layout of `format.file_layout` changes with it; template item "the storage layout", `templates/change-proposal.md:132`) |
| Section file | `specs/model-sidecar/common/identity.md` |
| Depends on | none. **Related (not a dependency):** the MediaPipe-Exporter proposal `roi-refiner-role` (`specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, slug at its line 47; it builds on skellytracker 0020). Its refiner id `{family}-{part}-roi` or `{family}-{part}-roi-{variant}` is in `detectors/roi_refiners/{family}/{part}/` (its lines 216-221; its rule `V-post.roi_refiner-9`, lines 725-728; user decision Q3 = a, line 60 (header) and lines 3928-3930). That id is outside the keypoint-detector grammar of this proposal. `V-common.identity-7` applies only under `detectors/keypoint_detectors/{family}/{keypoints}/` (2.4), and a refiner gives no keypoints, so it has no `{keypoints}` token (Q1, 2.3). Why it is not a dependency: no rule, function or vector of this proposal reads the `roi_refiners/` branch or a refiner id, and `V-post.roi_refiner-9` does not use a rule of this proposal. Thus either proposal can land first. The relation has two parts. (1) Its user decision Q3 = a answers Q1 of this proposal (2.3). (2) Both proposals edit the same places: the `model_id` row (`common/identity.md:29`), the legacy rows of `common/identity.md`, the storage layout (`format/file-layout.md:44-76`) and its authoring guidance (`format/file-layout.md:155-157`) (its 2.1, lines 243, 246, 253-254). The second content PR must rebase on the first. Line numbers into that file were checked again on 2026-10-24 (review-readiness audit 2). |
| Needed by | `specs/model-sidecar/proposals/size-codes/proposal.md` (its header row "Depends on", `:27`; it applies the user decisions S1 to S9, `:5-8`). It uses this proposal for two parts only: the `vNEXT` example names of its `format.file_layout` edits, and its note on `V-common.identity-8`, which uses `V-common.identity-7`. Both proposals edit `format/file-layout.md:30` and the examples at `format/file-layout.md:85-88`. This proposal keeps the example `rtmw-wholebody-l-m_fp32.onnx` as a legacy file (2.1). The size-code proposal replaces it with `rtmw-wholebody133-m_fp32.onnx` and `rtmw-wholebody133-l-256_fp32.onnx` (its 2.1, row `format.file_layout`, the storage-layout examples, `specs/model-sidecar/proposals/size-codes/proposal.md`; the size of the end model, user decisions S6 and S7, `:152-153` and `:306-310`; its Q6 is closed by S6, `:827-828`; lines checked again on 2026-10-24). The second content PR must rebase on the first. The proposals `pose-decode-flip-test`, `simcc-score-rule`, `heatmap-decode-refinement` and `normalize-arithmetic` use the ids of this proposal as model names only. They do not depend on it. The MediaPipe-Exporter proposal `roi-refiner-role` does not need this proposal. It gives the id and the folder of an ROI refiner outside the grammar of this proposal (row "Depends on", "Related (not a dependency)"; Q1, 2.3). **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit` (checked again on 2026-10-24). `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `simcc-score-rule`, `heatmap-decode-refinement`, `affine-crop-arithmetic`, `size-codes`, `roi-transform-and-source` (MediaPipe-Exporter); `common/identity.md:29, 36-41, 47-51, 76-81` (the `model_id` row, the rules, the legacy rows, the authoring guidance): `roi-refiner-role` (MediaPipe-Exporter); `common/sizes-and-artifacts.md:101`: `size-codes`; `format/file-layout.md:27-30` (file naming): `size-codes`; `format/file-layout.md:44-89` (the storage tree, the branch table, the examples): `roi-refiner-role` (MediaPipe-Exporter), `size-codes`; `format/file-layout.md:155-157` ("Authoring guidance"): `roi-refiner-role` (MediaPipe-Exporter); `format/composition.md:63-74` (the RTMW excerpt): `roi-transform-and-source` (MediaPipe-Exporter); `specs/model-sidecar/README.md:18-19` ("Core properties"): `size-codes`; `exporter-guide/sidecars/workflow/mapping-hints.md:13-32` ("Mapping hints", Identity and Family): `roi-refiner-role` (MediaPipe-Exporter), `size-codes`; `exporter-guide/sidecars/sidecar-files.md:33-50` ("Path"): `roi-refiner-role` (MediaPipe-Exporter); `templates/model-intake.md:229, 355` (rows F1, L1): `roi-refiner-role` (MediaPipe-Exporter); `inventory.yaml:98-129` (the `proposed` entries): `roi-transform-and-source` (MediaPipe-Exporter), `roi-refiner-role` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter); the reference examples under `examples/detectors/keypoint_detectors/` (`rtmo`, `rtmw`, `yolo26`): `size-codes`, `roi-transform-and-source` (MediaPipe-Exporter); skellytracker `notes/decisions/open-work.md:125-131` (`:130-136` at `dom/21-move-sidecar-guide`; the skellytracker 0025 item of "Spec defects"; at `dom/12-single-working-branch` it was `notes/decisions/README.md:159-165`): `roi-refiner-role` (MediaPipe-Exporter); `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `size-codes`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | **skellytracker 0025** (`specs/model-sidecar/decisions/0025-model-id-suffix.md`), a gap record. This proposal gives the parts that skellytracker 0025 does not have: the grammar, the rule for when a model takes the third token, the new-family guidance, the vectors and the reference implementation. The rule is a user decision (T14, 2026-10-23; part 2.3). It differs from the direction of skellytracker 0025 in one point: the second token is the keypoint output, not the part (part 8). **skellytracker 0017** (`specs/model-sidecar/decisions/0017-dual-role-sidecar-folder.md`, gap record) puts a dual-role sidecar under `keypoint_detectors/{family}/{part}/` (`0017-dual-role-sidecar-folder.md:11-16`). This proposal changes `{part}` to `{keypoints}` for `vNEXT` sidecars. It does not change the role rule of skellytracker 0017. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (branch `dom/sidecar-implementation`; no tracked change; `git status --porcelain` lists only the untracked `grep.exe.stackdump`, not a spec file; checked on 2026-10-25). The line numbers of this file were taken at `dom/18-agents-adr-bootstrap-kit` (status clean; checked again on 2026-10-24). At `dom/21-move-sidecar-guide` every cited line of `specs/model-sidecar/`, the templates, the examples, the tools, `skellytracker/core/sidecar/loader.py` and the skellytracker decision entries 0017 and 0025 is unchanged in its text and its line number (only some link targets changed, for example at `format/file-layout.md:156-158`, `common/identity.md:81` and `0017-dual-role-sidecar-folder.md:38`, `:45`), with three exceptions: the skellytracker 0025 item of `notes/decisions/open-work.md` is at `:130-136` (2.1), skellytracker 0028 is superseded by skellytracker 0032 (2.1, the `tools/tests/test_links.py` row), and the allowed-edits rule of `notes/decisions/README.md` moved from `:77-81` to `:80-85` (2.1, the `tools/tests/test_links.py` row). First read at `dom/12-single-working-branch`. From `dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`, the cited files do not change, with three exceptions: `specs/model-sidecar/exporter-guide.md` has one line less after line 445 (at `dom/21-move-sidecar-guide` that file no longer exists: skellytracker 0033 and 0034 moved it to `specs/exporter-guide/sidecars/`); the lines of `tools/check_links.py` move (it now also checks GitHub links in `notes/`); and the "Open work" list moved from `notes/decisions/README.md` to `notes/decisions/open-work.md`. The citations of this file are at `dom/18-agents-adr-bootstrap-kit`. Where a citation names `dom/12-single-working-branch`, it records a past state. Guide citations point to the skellytracker 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). |

## 1. Gap

| Item | Value |
|---|---|
| Property | The `model_id` of a keypoint detector must tell two models of one family apart, and it must name the keypoint output of the model. One family can have several models with one part and different keypoint outputs. One family can also have several models with the same keypoint output and different training sets. |
| Upstream evidence | RTMO, one family with three body config sets: mmpose v1.3.2 `configs/body_2d_keypoint/rtmo/coco/` (COCO only, COCO-17), `rtmo/body7/` (COCO-17, trained on body7) and `rtmo/crowdpose/` (CrowdPose, 14 points; it also has `configs/body_2d_keypoint/rtmo/crowdpose/rtmo-l_16xb16-700e_body7-crowdpose-640x640.py`) (the mmpose v1.3.2 git tree, from the GitHub tree API, not truncated). RTMPose, one family with COCO-17 and Halpe26 body models: `configs/body_2d_keypoint/rtmpose/body8/rtmpose_body8-halpe26.yml` (7 Halpe26 checkpoints, for example `rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605.pth`), `rtmpose_body8-coco.yml` (the COCO-17 checkpoints) and `configs/body_2d_keypoint/rtmpose/coco/rtmpose_coco.yml` (COCO only); `rtmpose-m_8xb512-700e_body8-halpe26-256x192.py:4` (`num_keypoints = 26`). skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose-body.yaml:3` (`model_id: rtmpose-body`) and `rtmpose-body.yaml:40` (`landmark_schema: COCO17`). |
| Nearest section ID | `common.identity` (`model_id`); `format.file_layout` (the storage layout) |
| Why the nearest section is wrong | The `model_id` row says: "For a keypoint detector, it is `{family}-{part}`" (`common/identity.md:29`). That gives one id for each family and part. `V-common.identity-1` makes the file basename equal to `model_id` (`identity.md:36`), so the two models get one file name in one part folder. The catalog key is `<model_id>@<source.name>` (`identity.md:59`), so a host also cannot tell them apart. The part folders (`format/file-layout.md:75`: `hand`, `face`, `body` and `wholebody`) do not name the keypoint output. The `body` folder holds 17, 25 and 26 points. |
| Measured difference | none: a name changes no tensor and no decoded output. The conflict is one id for two models (`rtmpose-body`, 17 points and 26 points; RTMO COCO and RTMO body7, both 17 points). |
| Row in "Considered and deliberately not added" | none (`changelog.md:42-53` has no row about `model_id` or the storage layout) |

skellytracker decision 0025 names more facts: the reference example `rtmo-body7` has a suffix without a hyphen, and
the MediaPipe plans name `mediapipe-hand-landmark` and `mediapipe-hand-recrop`
(`0025-model-id-suffix.md:15, 26-27, 41-44`). The spec text and its own example do not agree.

skellytracker decision 0025 asks the full proposal for three items (`0025-model-id-suffix.md:14-16`): the grammar
of the suffix, when a model needs a suffix, and when a variant is a new family. This proposal gives
the grammar (2.3, 2.4), the rule for the third token (2.3, user decision T14) and the new-family
guidance (2.3).

## 2. Spec change

### 2.1 Sections

Changed section `common.identity`, file `specs/model-sidecar/common/identity.md`. Front matter:
`changed_in: [vNEXT]` (no change); `vectors: vectors/common.identity.yaml` (now `null`,
`identity.md:15`); the `implemented_by` comment of `validate` (`identity.md:9`): change "No code checks
V-common.identity-4 to V-common.identity-6" to "No code checks V-common.identity-4 to
V-common.identity-9".

The storage layout of `format.file_layout` (`format/file-layout.md`) changes in the same contract
unit. Its front matter does not change.

**Places that the change edits.** The line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit`.

| Place | Heading | Edit |
|---|---|---|
| `common.identity` | "Fields", row `model_id` (`identity.md:29`) | Replace the text (see 2.2). |
| `common.identity` | "Validation rules" (`identity.md:36-41`) | Add `V-common.identity-7`, `V-common.identity-8` and `V-common.identity-9` (see 2.4). |
| `common.identity` | "Legacy behaviour" (`identity.md:49-51`) | Add the rows of 2.6. |
| `common.identity` | "Implementer guidance", the catalog key example (`identity.md:59`) | Change `rtmw-wholebody@openmmlab-exporter` to `rtmw-wholebody133@openmmlab-exporter`. |
| `common.identity` | "Authoring guidance", first bullet (`identity.md:76`) | Replace "Write the family id as `model_id`" with "For an object detector, write the family as `model_id`. For a keypoint detector, write `{family}-{keypoints}` or `{family}-{keypoints}-{training}` (see the `model_id` row)". Keep the list of values at the cited commits. Add the `vNEXT` values `rtmw-wholebody133` and `rtmo-coco17-body7` (OpenMMLab-Exporter `rtmw/identity.py` and `rtmo/identity.py`, constant `FAMILY`, at the commit of OpenMMLab-Exporter decision 0039). Add the planned values `rtmpose-halpe26`, `vitpose-coco25`, `vitposepp-wholebody133` and the DWPose id (the untracked pose-models plan of OpenMMLab-Exporter (plan facts) section 1; plan facts). |
| `common.identity` | "Authoring guidance", the bullet about `rtmo-body7` and skellytracker 0025 (`identity.md:80`) | Replace it with the naming guidance of 2.3 (the keypoint token, the training token, the default model, the user decisions Q2 to Q4, the new family, no size as a training token). |
| `format.file_layout` | "File extension and naming" (`file-layout.md:27`, `:30`) | Change the table row "Sidecar (one per family)" to "Sidecar (one per `model_id`)". Replace the first sentence of `file-layout.md:30` ("An ONNX filename gives the size, the batch and the precision") with: "The writer builds an ONNX filename as `{model_id}-{size}_{batch}_{precision}.onnx`. A host reads the size, the batch and the precision from the sidecar, not from the filename. A host must not split an ONNX filename at the hyphens to find the `model_id` or the size. The sidecar lists each artifact `filename`." (`rtmo-coco17-body7-m_b1_fp32.onnx` and `rtmw-wholebody133-l-256_b3_fp32.onnx` have hyphens in the id and in the size.) Keep the example `rtmw-wholebody-l-m_fp32.onnx`: it is the file of the legacy package sidecar. The size-code proposal edits the same line and replaces that example (header, row "Needed by"). |
| `format.file_layout` | "Storage layout", the tree (`file-layout.md:44-69`) | Replace the four part folders under `keypoint_detectors/{family}/` (`:54-65`) with one folder `{keypoints}/  # the keypoint output, for example coco17 or wholebody133 (see Identity)` that holds `{model_id}.yaml` and `{model_id}-{size}_{batch}_{precision}.onnx`. |
| `format.file_layout` | "Storage layout", the branch table (`file-layout.md:75`) | Replace the row with: "`detectors/keypoint_detectors/{family}/{keypoints}/` \| `pose_estimator` \| Keypoint models for each keypoint output. `{keypoints}` is a set name and its point count, for example `coco17` or `wholebody133` (see Identity (`../common/identity.md#fields`)). One folder can hold more than one sidecar. A legacy sidecar uses a part folder (see Legacy behaviour (`#legacy-behaviour`))." |
| `format.file_layout` | "Storage layout", the examples (`file-layout.md:78-89`) | Add the example `detectors/keypoint_detectors/rtmo/coco17/` with `rtmo-coco17-body7.yaml` and `rtmo-coco17-body7-m_b1_fp32.onnx`. Add the comment `# legacy package sidecar (part folder)` to the example `detectors/keypoint_detectors/rtmw/wholebody/` (`:85-88`), or replace it with `rtmw/wholebody133/` and `rtmw-wholebody133-m_b3_fp32.onnx`. |
| `format.file_layout` | new heading "Legacy behaviour", after "Validation rules" (`file-layout.md:118-120`) | Add the table of 2.6. |
| `format.versioning` | "Version-aware compatibility" (`versioning.md:49-63`) | Add the line `- [File layout](file-layout.md#legacy-behaviour)` after the line of File composition (`:53`). `versioning.md:55` already links Identity. |
| `format.file_layout` | "Authoring guidance", OpenMMLab-Exporter (`file-layout.md:138`) | Change `detectors/keypoint_detectors/rtmw/wholebody/` to `rtmw/wholebody133/` and add `rtmo/coco17/`, with the commit of OpenMMLab-Exporter decision 0039. |
| `format.file_layout` | "Authoring guidance", Ultralytics-Exporter (`file-layout.md:139`) | Keep the fact at `f52ef68`. Add: "At `vNEXT`, the folder is `keypoint_detectors/yolo26/coco17/` and the id is `yolo26-coco17`." |
| `format.file_layout` | "Authoring guidance" (`file-layout.md:155-157`) | Remove the bullet about `rtmo/body7/` (`:156`), or mark it done (OpenMMLab-Exporter decision 0039: `rtmo/coco17/`). If you remove it, change the parent bullet (`:155`) from "The folder of two kinds of sidecar" to "The folder of a sidecar with both roles". In `:157`, change "OpenMMLab-Exporter writes RTMO (both roles) under `keypoint_detectors/rtmo/`" to cite `rtmo/identity.py` (`FAMILY_BRANCH`) at the commit of OpenMMLab-Exporter decision 0039. |
| `specs/model-sidecar/README.md` | "Core properties" (`README.md:18-19`) | Change "One sidecar for each model family" (`:18`) to "One sidecar for each `model_id`". Keep the text that the file lists every size. In `:19`, change "A family ships several sizes in one file" to "A sidecar ships several sizes in one file". The two meanings of "family" are in 2.3, "Terms". |
| `common.sizes_and_artifacts` (`common/sizes-and-artifacts.md`) | "Sizes", the family invariant (`:35`); "Sizes and artifacts" (`:101`, `:103`) | In `:35`, change "they belong to **different families** (different sidecars)" to "they belong to **different sidecars** (different `model_id` values). Two such sidecars of a keypoint detector can have the same family token (see Identity (`identity.md#fields`))". In `:101`, change "A family ships several sizes of the same model" to "A sidecar ships several sizes of the same model". In `:103`, change "a separate family" to "a separate sidecar". Keep `:45`: it is about object detectors, where `model_id` is the family. |
| `specs/exporter-guide/sidecars/workflow/README.md`, `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | The file table (`exporter-guide/sidecars/workflow/README.md:19`, `:23`) and "Mapping hints", "Family" (`exporter-guide/sidecars/workflow/mapping-hints.md:27-28`) | In `exporter-guide/sidecars/workflow/README.md:19`, change "One file for each family" to "One file for each `model_id`". In `exporter-guide/sidecars/workflow/README.md:23`, change "the `model_id` of the family" to "the `model_id` of the sidecar". In `exporter-guide/sidecars/workflow/mapping-hints.md:28`, change "they are two families (two sidecars)" to "they are two sidecars (two `model_id` values)". |
| `specs/model-sidecar/templates/model-intake.md` | Step 1 (`:21`) and the family paragraph (`:224-225`) | In `:21`, change "`model_id` of the family" to "`model_id` of the sidecar". In `:224-225`, change "they are two families. Write one intake for each family" to "they are two sidecars. Write one intake for each `model_id`". |
| `specs/model-sidecar/README.md` | "Validation rules" | No edit. The index links each section, not each rule. |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | "Mapping hints for phase 1", "Identity" (`exporter-guide/sidecars/workflow/mapping-hints.md:13-26`) | Replace the text from "For a keypoint detector" (`:15`) to the end of the bullet list (`:26`) with: "For a keypoint detector, `model_id` is `{family}-{keypoints}` or `{family}-{keypoints}-{training}`, for example `rtmw-wholebody133` in `keypoint_detectors/rtmw/wholebody133/` (see `common.identity`). Record the keypoint set, its point count and the upstream sibling models with the same keypoint output. A name changes no tensor and no decoded output, so the `model_id` row is never a `near-miss`. If the spec has no `model_id` rule for the role of the model (a new role), the row is a `gap`." |
| `specs/exporter-guide/sidecars/sidecar-files.md` | "Path" (`exporter-guide/sidecars/sidecar-files.md:38-50`) | Change `keypoint_detectors/{family}/{part}/{model_id}.yaml` and "`{part}` is `hand`, `face`, `body` or `wholebody`" (`:39-40`) to `keypoint_detectors/{family}/{keypoints}/{model_id}.yaml` with "`{keypoints}` is the keypoint output, for example `coco17` (see `common.identity`)". Change "A model-specific folder, such as `body7`, does not conform" and the example path (`:48-50`) to: "A training-set folder, such as `body7`, does not conform. For example, the RTMO body7 reference example has the path `detectors/keypoint_detectors/rtmo/coco17/rtmo-coco17-body7.yaml`." Add: "A keypoint folder can hold more than one `{model_id}.yaml`." |
| `specs/exporter-guide/sidecars/known-open-items.md` | "Known open items for the exporter overhaul" (`exporter-guide/sidecars/known-open-items.md:8`) | Remove the RTMO `rtmo/body7/` row, or mark it done (OpenMMLab-Exporter decision 0039: `rtmo/coco17/`). |
| `specs/model-sidecar/templates/model-intake.md` | Row F1 (`model-intake.md:229`) | Replace the text after "A keypoint detector uses" with: "`{family}-{keypoints}` (`rtmw-wholebody133`), or `{family}-{keypoints}-{training}` (`rtmo-coco17-body7`) when the family has more than one upstream model with the same keypoint output. A name is never a `near-miss`. A new role with no `model_id` rule is a `gap`." |
| `specs/model-sidecar/templates/model-intake.md` | The paragraph about rows that are a `gap` (`model-intake.md:155-158`) | Remove the sentence "Row F1 gives one more `gap` ...". Do this in the same edit as row F1. |
| `specs/model-sidecar/templates/model-intake.md` | Row L1 (`model-intake.md:355`) | Change `keypoint_detectors/{family}/{part}/{model_id}.yaml`, where `{part}` is `hand`, `face`, `body` or `wholebody`, to `keypoint_detectors/{family}/{keypoints}/{model_id}.yaml`, where `{keypoints}` is the keypoint output (`common.identity`). |
| `specs/model-sidecar/changelog.md` | "Summary of changes" (`changelog.md:16-36`) | Add the summary row of 2.7. |
| `specs/model-sidecar/changelog.md` | "Compatibility impact" (`changelog.md:55-59`) | Add the bullet of 2.7. |
| `specs/model-sidecar/changelog.md` | `schema_version` history (`changelog.md:65-68`) | Extend the existing `vNEXT` row (`:68`) with the text of 2.7. Do not add a second `vNEXT` row. |
| `format.composition` (`format/composition.md`) | The RTMW excerpt (`composition.md:63`, `:69`) | Change the path comment to `detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml` and `model_id: rtmw-wholebody` to `model_id: rtmw-wholebody133`. |
| `pre.resize.fit` (`pre/resize-fit.md`) | "Authoring guidance" (`resize-fit.md:74`) | Change the link to `../examples/detectors/keypoint_detectors/rtmo/coco17/rtmo-coco17-body7.yaml`. |
| Reference examples | `specs/model-sidecar/examples/detectors/keypoint_detectors/` | All three `vNEXT` keypoint examples fail `V-common.identity-7`, because a part folder has no point count. Replace `rtmo/body/rtmo-body7.yaml` with `rtmo/coco17/rtmo-coco17-body7.yaml` and `rtmw/wholebody/rtmw-wholebody.yaml` with `rtmw/wholebody133/rtmw-wholebody133.yaml`. Use the regenerated sidecars of OpenMMLab-Exporter (part 7) and the procedure "Reference examples" (`specs/sidecar-implementation-plan.md:218-226`). Move the YOLO26 pose forecast `yolo26/body/yolo26-body.yaml` to `yolo26/coco17/yolo26-coco17.yaml` and change its `model_id`. It is a `vNEXT` forecast written from exporter code (`inventory.yaml:44-55`; `schema_version: "vNEXT"` at line 2 of the file), so it fails `V-common.identity-7` in the part folder, and the move needs no export. The exporter code still writes `yolo26-body`, so the new id is an edit to the forecast (see the `inventory.yaml` row). The id `yolo26-coco17` is derived by this proposal. It is not in the T14 scope list. The user confirmed it (M1, plan T23, 2026-10-24). Ultralytics-Exporter still writes `yolo26-body`. The `$ref` paths of the examples (`../../../shared/...`) do not change: the folder depth stays the same. |
| `specs/model-sidecar/inventory.yaml` | header comment `edits` (`inventory.yaml:15-17`); `examples` (`inventory.yaml:44-55`, `:69-81`, `:83-96`) | Change the three keys and paths. For the YOLO26 pose forecast, set `exporter_layout_path` to `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml` (the exporter still writes the legacy folder). The header allows only two edits ("header comment removed" and "source and hashes added", `:15-17`), and the procedure says "Copy, don't edit" (`specs/sidecar-implementation-plan.md:221`). Thus add a third allowed edit to the header comment: "model_id and folder set to the vNEXT id (forecast only, while the exporter writes the legacy id)". Add it to `edits` of the YOLO26 pose forecast, and add a note that Ultralytics-Exporter `yolo_sidecar.py:22-25` (`f52ef68`) writes `yolo26-body`. The forecast is replaced by an export once Ultralytics-Exporter writes `vNEXT` (`sidecar-implementation-plan.md:216`). For RTMO, the new `exporter_path` is `notes/decisions/rtmo-coco17-body7.yaml` and the new `exporter_layout_path` is `null`. |
| `specs/model-sidecar/inventory.yaml` | `proposed` (`inventory.yaml:98-129`) | The keys are plan facts. Change them only when the exporter plans change (part 7). The MediaPipe-Exporter plan path the untracked hand pipeline export plan of MediaPipe-Exporter (plan facts) (`:117`, `:125`) is now the untracked archived hand pipeline export plan of MediaPipe-Exporter (plan facts). The current plan is the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (no git repo). |
| `specs/model-sidecar/examples/README.md` | "YOLO26 pose", "RTMW WholeBody" and "RTMO body7" (`examples/README.md:19`, `:33`, `:41`) | Change the three "Sidecar:" links and their link texts to the new files. Keep the headings: `specs/model-sidecar/sidecar-spec.md:231` and skellytracker `specs/model-sidecar/decisions/0012-fit-resize-for-rtmo.md:73` link to the anchor `#rtmo-body7-openmmlab-exporter-bottom-up-pose-nms-in-the-graph`. |
| `specs/sidecar-implementation-plan.md` | "Reference examples" table and step 3 (`:214`, `:222`) | In the RTMO body7 row, give the new source (OpenMMLab-Exporter `notes/decisions/rtmo-coco17-body7.yaml`) and its commit. In step 3, change "the spec's part folders are `hand`, `face`, `body` and `wholebody`, so the example goes under `rtmo/body/`" to the keypoint folder `rtmo/coco17/`, and record that OpenMMLab-Exporter decision 0039 fixes the exporter path defect. In `:19`, change "matching the spec's layout exactly" to "matching the legacy layout of the spec (part folders; see File layout, Legacy behaviour (`sidecar/format/file-layout.md#legacy-behaviour`))". The package sidecars stay legacy, so `exactly` is true only for the legacy layout. |
| `tools/tests/test_examples.py` | `test_example_follows_the_storage_layout` (`test_examples.py:114-122`) | The test requires a part folder (`:122`: `parts[2] in {"hand", "face", "body", "wholebody"}`). Change it: a `vNEXT` example must have a keypoint folder that matches `^[a-z0-9]*[a-z][1-9][0-9]*$`, and its `model_id` must pass `V-common.identity-7`. |
| `tools/tests/test_traceability.py` | `EXPECTED_KEYS`, `RTMW_BOTH`, `EXPECTED_APPLICABILITY`, `EXPECTED_NORMALIZATION`, `EXPECTED_CELLS` | Rename `rtmo-body7@openmmlab-exporter` to `rtmo-coco17-body7@openmmlab-exporter` (lines 60, 587, 594, 602, 606, 620, 666, 672, 677). Rename `rtmw-wholebody@openmmlab-exporter` to `rtmw-wholebody133@openmmlab-exporter` (lines 59, 577, 619, 665). Rename `yolo26-body@ultralytics-exporter` to `yolo26-coco17@ultralytics-exporter` (lines 57, 583, 593, 601, 605, 617, 663, 671, 676). Keep `rtmw-wholebody@skellytracker` (legacy package, lines 55, 577, 615, 661). |
| `tools/make_vectors.py` | `BUILDERS` (`make_vectors.py:2411-2421`) | Add a builder for `common.identity` that writes the cases of part 4. Every vector file must equal the output of this tool (`tools/tests/test_vectors.py:111`), and `generated_by` must be `tools/make_vectors.py` (`test_vectors.py:141`). The part 4 block names the reference file as `generated_by`, by the template (`templates/change-proposal.md:251`). The skellytracker port changes that value. |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (`test_vectors.py:32-40`) and `test_cases_have_the_documented_shape` (`:175`) | The part 4 cases have the key `function`, as the template requires (`templates/change-proposal.md:242`, `:256`). `CASE_KEYS` has no `function` key, so the test rejects each case. This vector file is the first one with more than one function. Proposal choice: add `function` to `CASE_KEYS` as an optional key. The template and the test do not agree for every proposal, so the skellytracker session can also change the template. |
| `tools/tests/test_sidecar_trace.py` | the fixture `BAZ` (`test_sidecar_trace.py:52-58`, `:135`, `:171`, `:1052`) | `BAZ` is a `vNEXT` keypoint sidecar `baz` in the part folder `keypoint_detectors/baz/body/`. It fails `V-common.identity-7` and has no `pose.tracked_points` for `V-common.identity-9`. The test expects the status `unavailable` for other reasons (`:1052`). If `tools/sidecar_trace.py` applies the new rules, change the fixture to a keypoint folder (for example `baz/a1/baz-a1.yaml`) and check the expected statuses. If it does not, no edit. |
| `tools/tests/test_links.py` (`tools/check_links.py:125-131`) | `test_relative_links_resolve` | The test checks each relative link in `specs/` and `notes/` (`test_links.py:1`, `check_links.py:128`). After the example moves, these links of skellytracker decision entries point at files that do not exist: `0017-dual-role-sidecar-folder.md:41`, `:43`, `0018-one-declaration-per-tensor.md:33` and `0025-model-id-suffix.md:38`. At `dom/12-single-working-branch`, the decision log did not allow a change to the body of an entry (`notes/decisions/README.md:216` at `dom/12-single-working-branch`). Proposal choice: in these four lines, change only the link target to a GitHub link of the old file at commit `dom/12-single-working-branch`. Keep the link text. `check_links.py` does not resolve a link with a scheme (`check_links.py:106-110`), and the link keeps the exact past state. This edit needs an exception to `README.md:216`. The skellytracker session records the exception by its own rules, and the user decides. Part 8 gives the alternatives. At `dom/18-agents-adr-bootstrap-kit` the exception is moot: the three entries are `proposed` (`notes/decisions/README.md:36-37, 44`), a `proposed` entry can change, and a link repair is an allowed edit of any entry (`README.md:77-81` at `dom/18-agents-adr-bootstrap-kit`, `:80-85` at `dom/21-move-sidecar-guide`; skellytracker 0032, items 1 and 2; skellytracker 0032 supersedes skellytracker 0028 in full, 2026-10-24), but the GitHub link must pin the full SHA `dom/12-single-working-branch` (skellytracker 0032, item 4; `check_links.py:106-109`). |
| `specs/model-sidecar/TRACEABILITY.md` | generated (`TRACEABILITY.md:3`: "do not edit") | Do not edit it by hand. Run `tools/sidecar_trace.py matrix` after the examples, the inventory and `vectors/common.identity.yaml` are in place. The tool then writes the new column keys (now at line 15) and model rows (now `:56`, `:57`, `:59`), and the vectors cell of `common.identity` (now `none` at line 70). |
| skellytracker `notes/decisions/open-work.md` and `notes/decisions/README.md` | "Spec defects", the skellytracker 0025 item (`open-work.md:125-131` at `dom/18-agents-adr-bootstrap-kit`, `:130-136` at `dom/21-move-sidecar-guide`; the "Open work" list moved there from `README.md:159-165` after `dom/12-single-working-branch`); the index row of skellytracker 0025 (`README.md:44`) | Do not close the item until the user accepts this proposal and the ROI-refiner proposal. The item also covers the stage suffix: "A hand landmark model and a hand re-crop model of one family would both get `{family}-hand`" (`open-work.md:128-129` at `dom/18-agents-adr-bootstrap-kit`, `:133-134` at `dom/21-move-sidecar-guide`). The user answered that part through the ROI-refiner proposal (2.3, Q1, answered): the re-crop model is an ROI refiner `mediapipe-hand-roi` in `detectors/roi_refiners/mediapipe/hand/`, not a keypoint id (MediaPipe-Exporter `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, the row for this item). The skellytracker session records the effect by the rules of its decision log. The old title "Suffix after the part in `model_id`" no longer fits. |
| skellytracker `specs/model-sidecar/decisions/0017-dual-role-sidecar-folder.md` (proposed) | "Decision" (`:11-16`) and "Reason" (`:26-27`) | skellytracker 0017 names `keypoint_detectors/{family}/{part}/` and the part folders. Under this proposal, a `vNEXT` dual-role sidecar goes to `keypoint_detectors/{family}/{keypoints}/`. The skellytracker session records this effect by the rules of its decision log. |

Do not change the text of these records of past states:

- skellytracker `decisions/0013-spec-structure.md:298` names the old exporter path
  `notes/decisions/rtmo-body7.yaml` (now OpenMMLab-Exporter `notes/decisions/rtmo-coco17-body7.yaml`)
  and links `examples/README.md`. It has no link to a moved file, so it stays as it is.
- skellytracker `0017-dual-role-sidecar-folder.md:41-43`, `0018-one-declaration-per-tensor.md:33`,
  `0025-model-id-suffix.md:38` and `decisions/scripts/split_manifest.yaml:726-729` (the record of the split) link
  or name `rtmo-body7.yaml`, `rtmw-wholebody.yaml` and `yolo26-body.yaml` under `examples/`. After
  the swap, these names are historical. The four markdown links need the link-only edit of the
  `tools/tests/test_links.py` row. `split_manifest.yaml` is not a markdown file, so the link test
  does not read it.

If the decision rules allow it, a new decision entry can name the new files.

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | yes | The model identifier. It matches the sidecar basename. For an object detector, it is the family, for example `yolo26`. For a keypoint detector, it is `{family}-{keypoints}`, for example `rtmw-wholebody133`, or `{family}-{keypoints}-{training}`, for example `rtmo-coco17-body7`. `{family}` and `{keypoints}` are the names of the two folders that hold the sidecar (Storage layout (`../format/file-layout.md#storage-layout`)). `{keypoints}` is the keypoint output: a set name and its point count, for example `coco17` or `wholebody133`. `{training}` is the training set of the model, for example `body7`. A family uses `{training}` only when it has more than one upstream model with the same keypoint output (see Authoring guidance (`#authoring-guidance`)). A legacy keypoint sidecar has `{family}-{part}` (see Legacy behaviour (`#legacy-behaviour`)). |

### 2.3 Behaviour

```text
A sidecar at detectors/keypoint_detectors/{family}/{keypoints}/{model_id}.yaml,
with schema_version >= vNEXT:

  V-common.identity-7 (the grammar and the folders):
    {family}    must match ^[a-z0-9]+(-[a-z0-9]+)*$
        and no hyphen part of {family} after the first part may match the keypoint pattern
    {keypoints} must match ^[a-z0-9]*[a-z][1-9][0-9]*$
        name  = the characters up to and including the last letter
        count = the digits after the last letter, as an integer (no leading zero, so count >= 1)
    model_id == "{family}-{keypoints}"                 -> valid, no training token
    model_id == "{family}-{keypoints}-{training}"      -> valid, training = {training}
        where the whole {training} matches ^[a-z0-9]+(-[a-z0-9]+)*$
    any other value                                    -> invalid
    The classes [a-z] and [0-9] are ASCII only.

  V-common.identity-9 (the point count):
    count == len(pose.tracked_points) of the resolved sidecar -> valid
    any other case                                             -> invalid

All sidecars with schema_version >= vNEXT in one folder:

  V-common.identity-8 (the artifact files):
    no artifact filename is named by two sidecars      -> valid
    any other case                                     -> invalid
```

The rules read `{family}` and `{keypoints}` from the two folders. A family token, a keypoint token
and a training token can look the same: `yolo26` is a family, and it also matches the keypoint
pattern (name `yolo`, count 26); `body7` is a training token, and it also matches the keypoint
pattern (vectors `family-like-keypoints` and `training-like-keypoints`). For two given folders, the
id has one parse, because the folders fix where the keypoint token and the training token start.

**The family parts (decided in this proposal).** No hyphen part of `{family}` after the first part
may match the keypoint pattern. Without this rule, one id is valid in two folder pairs:
`rtmo-coco17-body7` is valid in `rtmo/coco17/` (training `body7`) and in `rtmo-coco17/body7/` (no
training token). The catalog key is `<model_id>@<source.name>` (`identity.md:59`), so the two
sidecars get one key. That is the defect of part 1. `V-common.identity-8` compares the sidecars of
one folder only, so it does not find this case. With the rule, an id is valid in one folder pair
only: the keypoint token is the first hyphen part after the first part that matches the keypoint
pattern. The first part can match the keypoint pattern, so the family `yolo26` stays valid. No family
in use or in plan has a hyphen (vector `family-part-like-keypoints`; the vector `hyphen-in-family`
uses the synthetic family `ab-cd`). The other choice is a catalog rule that one key may come from one
folder pair only (part 8).

**The ASCII classes (decided in this proposal).** The classes `[a-z]` and `[0-9]` of the three
patterns are ASCII only. A port must not use `\d`, `\w` or `str.isdigit`. In Python, `\d` matches
the fullwidth digit `７`, and `int()` reads `"1７"` as 17. Thus `coco1７` is not valid (vectors
`token-fullwidth-digit`, `token-non-ascii-letter` and `non-ascii-training`).

**The keypoint pattern (decided in this proposal).** The pattern is `^[a-z0-9]*[a-z][1-9][0-9]*$`.
The name ends with a letter, so the count is always the digits after the last letter. Thus each
token has one parse: `h36m17` gives the name `h36m` and the count 17 (Human3.6M, 17 points: mmpose
v1.3.2 `configs/_base_/datasets/h36m.py:2`, `dataset_name='h36m'`, and `:106-109`, the last
keypoint id 16). The name can start with a digit: the mmpose face set `300w` has 68 points (mmpose
v1.3.2 `configs/_base_/datasets/300w.py:2`, `dataset_name='300w'`, and `:129`, the last keypoint id
67), so its token is `300w68`. The count has no leading zero, so one output has one spelling
(`coco17`, not `coco017`). The token has no hyphen and no underscore: it is one folder name and one
token of the id.

**The training pattern (decided in this proposal).** The pattern is `^[a-z0-9]+(-[a-z0-9]+)*$`, the
pattern of `source.name` (`identity.md:27`, `V-common.identity-6`). A hyphen is allowed. For two
given folders, a hyphen gives no second parse, because the training token is the rest of the id
after `{family}-{keypoints}-`. No id in scope uses a hyphen in the training token: the ids of 2.3
shorten the upstream names to one token (`ubody`, `body7`). The hyphen is for future names only.
Upstream training names can have hyphens, for example the DWPose config
`configs/wholebody_2d_keypoint/dwpose/ubody/s1_dis/dwpose_l_dis_m_coco-ubody-256x192.py` and the
RTMO config `configs/body_2d_keypoint/rtmo/crowdpose/rtmo-l_16xb16-700e_body7-crowdpose-640x640.py`
(the mmpose v1.3.2 git tree, from the GitHub tree API, not truncated). Use one token when one token
is sufficient.

**Terms (decided in this proposal).** The spec uses "family" for one sidecar with one contract (the
family invariant, `common/sizes-and-artifacts.md:35`; `exporter-guide/sidecars/workflow/mapping-hints.md:27-28`). Under T14,
`{family}` is the family token: the name of an upstream model line. Several sidecars can share one
family token, for example `rtmo-coco17`, `rtmo-coco17-body7` and `rtmo-crowdpose14`, which differ in
`pose` (17 or 14 points). Thus this proposal uses these words:

- **family token**: the `{family}` part of the id and the first folder under `keypoint_detectors/`.
- **sidecar**: one `model_id`, one file, one contract. The family invariant applies to each sidecar,
  that is, to each `model_id`. For an object detector, the `model_id` is the family, so the two
  meanings are the same.

2.1 lists the places that change "family" to "sidecar" or "`model_id`".

**The naming rule (user decision T14, 2026-10-23).** No validation rule checks it, because it
depends on the upstream models, not on one sidecar. Write it as authoring guidance of
`common.identity` (`identity.md:74-86`). The four rules are the T14 text of the plan
(the untracked pose-models plan of OpenMMLab-Exporter (plan facts); plan facts) with three additions from OpenMMLab-Exporter decision
0039, the tracked record of T14 (`notes/decisions/0039-keypoint-model-id-format.md:3`, `:14-26`;
accepted, user T14; `d0f4343`). The additions are the example `face68` (`0039-keypoint-model-id-format.md:15`), the reference
dataset COCO-WholeBody of `wholebody133` (`0039-keypoint-model-id-format.md:22-23`) and the last sentence of rule 3 (`0039-keypoint-model-id-format.md:24`).

1. `{keypoints}` is the keypoint output: a set name followed by its point count, for example
   `coco17`, `coco25`, `halpe26`, `wholebody133`, `crowdpose14`, `aic14`, `mpii16`, `hand21`,
   `face68`.
2. `{training}` is the training dataset token, from the upstream config or config-folder name, for
   example `body7` (mmpose v1.3.2 config folder `configs/body_2d_keypoint/rtmo/body7/`), `ubody`
   (`configs/wholebody_2d_keypoint/dwpose/ubody/`), `cocktail14`
   (`configs/wholebody_2d_keypoint/rtmpose/cocktail14/`) and `body8`
   (`configs/body_2d_keypoint/rtmpose/body8/`).
3. `{training}` is present only when the family has more than one upstream model with the same
   keypoint output. The default model, which is trained only on the reference dataset of that
   keypoint set (COCO for `coco17`, COCO-WholeBody for `wholebody133`), takes the bare
   `{family}-{keypoints}`. Every other model takes `{training}`. In such a family, a different
   training set alone is a reason for the third token.
4. The sidecar folder is `detectors/keypoint_detectors/{family}/{keypoints}/`, and the id starts
   with that folder pair.

**User decisions after T14 (2026-10-23; plan section 2.2, "After T14", Q2 to Q4; plan facts).** Write
them as authoring guidance of `common.identity`, next to the four rules.

- **One model for a keypoint output (Q4).** Rule 3 applies as written. A family with only one
  upstream model for a keypoint output takes the bare `{family}-{keypoints}`. This is true also when
  that model does not train only on the reference dataset of the keypoint set. The reference dataset
  is necessary only when the family has more than one model with the output. Example: RTMW has one
  model line with the `wholebody133` output. Its configs and its metafile under `configs/` are in
  `configs/wholebody_2d_keypoint/rtmpose/cocktail14/`. That folder has 5 `rtmw-*` configs and
  `rtmw_cocktail14.yml`. Copies of the 5 configs, with the same file names, are in
  `mmpose/configs/wholebody_2d_keypoint/rtmpose/cocktail13/` and
  `projects/rtmpose/rtmpose/wholebody_2d_keypoint/`. All these paths are from the mmpose v1.3.2 git
  tree (the GitHub tree API, not truncated). Each config name has `cocktail14`. Thus RTMW trains on
  `cocktail14`, not on COCO-WholeBody only. Its id is `rtmw-wholebody133`, not
  `rtmw-wholebody133-cocktail14` (OpenMMLab-Exporter decision 0039,
  `notes/decisions/0039-keypoint-model-id-format.md:18-20` and `:32`, `d0f4343`). The Halpe26 model is the same case: `rtmpose-halpe26`, trained on body8
  (metafile `rtmpose_body8-halpe26.yml`).
- **Two models with the same keypoint output and the same training set (Q2).** They are two sizes of
  one sidecar when the family invariant holds. The spec text of the invariant is: "A family has
  exactly one contract for preprocessing and post-processing. If two sizes need a different value for
  any of these items, they belong to **different families** (different sidecars)"
  (`common/sizes-and-artifacts.md:35`). The items are the channel order, the normalization, the resize
  method, the output semantics, the selection mode, the NMS parameters and the class mapping
  (`sizes-and-artifacts.md:37-43`). "All sizes share these parts: `role`, `outputs` semantics,
  `batching`, the input tensor contract (`name`, `dtype`, `layout`, `color_format`, `normalization`,
  `resize` other than `target_size`), `decode` and `pose`. Only these parts are specific to each size:
  `input.shape`, `input.resize.target_size` and the ONNX artifacts" (`sizes-and-artifacts.md:101`).
  skellytracker decision 0010 (accepted) records the rule: "a size sets only its shape, target size
  and artifacts" (`0010-family-invariant.md:1`, `:7-18`). Example: the MediaPipe-Exporter face
  landmark models holistic (192 px) and landmarker (256 px) both give 478 points in a `[1,1,1,1434]`
  tensor and take RGB [0, 1] (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts); secondary,
  no git repo). They are two sizes of one sidecar if the exporter makes their contracts equal. The
  plan has two input tensor names (`serving_default_input_28:0` at `:246`, `input_12` at `:260`), and
  the landmarker has a third output `tongue_out` (`:261`, `:264`). The plan gives the same condition
  (`:265-268`). The plan does not name the training set of either model. The user decision treats the
  two models as one model line. The `model_id` is `mediapipe-<set>478`, and MediaPipe-Exporter
  chooses the set name. The size-code proposal gives the size keys of the two models: `192` and `256`
  (its Q3, closed by the user decision S3; `specs/model-sidecar/proposals/size-codes/proposal.md`,
  lines checked again on 2026-10-24). If the invariant does not hold for
  two such models, they cannot be two sizes, and this format gives them no second id. This proposal
  does not define one. A later proposal defines it when a model needs it.
- **A keypoint set with no single reference dataset (Q3).** Rule 3 needs the reference dataset of a
  keypoint set only when a family has more than one model with that output. T14 defines it for
  `coco17` (COCO), and OpenMMLab-Exporter decision 0039 adds `wholebody133` (COCO-WholeBody) (`0039-keypoint-model-id-format.md:22-23`). For
  `hand21` and the face sets (for example `face68`), several datasets exist. The reference dataset of these sets stays undefined until a model needs it.
  Then this proposal, or a later proposal, defines it. No model in scope needs it. The first known
  case is a `vNEXT` rewrite of the skellytracker package sidecar `rtmpose-hand`: mmpose v1.3.2 has two
  RTMPose `hand21` models, `configs/hand_2d_keypoint/rtmpose/coco_wholebody_hand/` and
  `configs/hand_2d_keypoint/rtmpose/hand5/` (the mmpose v1.3.2 git tree, from the GitHub tree API,
  not truncated).

**Added guidance (decided in this proposal).** These sentences are not in T14. Each has its reason.

- **The same keypoint output.** Two models have the same keypoint output when they have the same
  keypoint token (set name and count). Reason: a definition by the ordered list of points lets two
  models with one set in two orders get two outputs, and then rule 3 gives each one the bare id in
  one folder. The token does not fix the order of the points. `pose.tracked_points` gives the order.
- **A new keypoint token.** Use a token in use when the set is the same. For a new set, take the
  upstream dataset name, remove the characters that the pattern does not allow, and add the point
  count. If the name already ends in the count, do not add the count again: the easy_ViTPose dataset
  name `coco_25` (easy_ViTPose `easy_ViTPose/inference.py:66`, `bb98603`) gives `coco25`. Do not use
  one set name for two different point lists with the same count. Reason: one spelling for one set,
  so that rule 3 can find the siblings.
- **The reference dataset of a set named after one dataset.** For `halpe26`, `crowdpose14`, `aic14`
  and `mpii16`, the reference dataset is the dataset of the set name (Halpe, CrowdPose, AI Challenger
  and MPII). Reason: each of these set names names one dataset, so rule 3 can find the default model
  with no more decision. The user decided only `hand21` and the face sets (Q3, above). The table
  below uses this sentence for one row: RTMO CrowdPose (not exported), where the CrowdPose-only set
  is the default model `rtmo-crowdpose14`. First a proposal choice; the user accepted it (user
  decision T21 (1), 2026-10-23, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)).
- **The source of the training token.** Take the token that separates the model from its upstream
  siblings, from the config or the config-folder name (T14 rule 2). Do not take it from the
  checkpoint name when the two names differ. Remove the characters that the pattern does not allow.
  Reason: the RTMPose COCO-17 package checkpoint is named `body7` (`rtmpose-body.yaml:62`), but its
  metafile lists it for the `body8` config (`rtmpose_body8-coco.yml`).
- **One folder, more than one sidecar.** A keypoint folder can hold more than one sidecar, for
  example `rtmo-coco17.yaml` and `rtmo-coco17-body7.yaml` in `rtmo/coco17/`. Reason: this follows
  from rules 3 and 4.
- **Sizes and training tokens.** A filename joins the `model_id` and the size with a hyphen
  (`{model_id}-{size}_{batch}_{precision}.onnx`), and both can have hyphens (`exporter-guide/sidecars/workflow/mapping-hints.md:30-31`:
  a size name can be any lowercase token). Thus two sidecars in one folder can name the same file
  when the `model_id` of one is the `model_id` of the other plus a token, and a size of the other
  starts with that token. There are two forms:
  - A size-like training token: a sidecar `rtmo-coco17-m` with the size `l` and a sidecar
    `rtmo-coco17` with the size `m-l` both give `rtmo-coco17-m-l_b1_fp32.onnx` (vector
    `artifacts-size-like-training-collision`).
  - A training-like size name: a sidecar `rtmo-coco17` with the size `body7-m` and a sidecar
    `rtmo-coco17-body7` with the size `m` both give `rtmo-coco17-body7-m_b1_fp32.onnx` (vector
    `artifacts-training-like-size-collision`).

  Do not use a size name, or a size name with a hyphen part, as a training token (for example `m`
  or `l-256`). Do not start a size name with a training token of the family. A size stays a key of
  `sizes`. `V-common.identity-7` cannot detect either form (vector `size-like-training`).
  `V-common.identity-8` rejects both.
- **A new family token.** A model takes a new family token when upstream publishes it as a separate
  model line, with its own name, its own weights and its own configs or head. Examples: `rtmw` and
  `dwpose`, both RTMPose architectures; `rtmw3d` (mmpose v1.3.2 `projects/rtmpose3d/`, its own head
  `rtmw3d_head.py`). A successor release of one model line keeps the family token of that line when
  upstream keeps the line name in its config file names. ViTPose++ takes the new family token
  `vitposepp` (user decision T11): the ViTAE README names the models ViTPose++ (ViTAE
  `README.md:80-83` and `:171-178`, `c050ed2`), and they have their own multi-task checkpoints and
  configs (the ViTAE git tree at `c050ed2`:
  `configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/vitPose+_<size>_coco+aic+mpii+ap10k+apt36k+wholebody_256x192_udp.py`,
  sizes `small`, `base`, `large` and `huge`; the README links at `README.md:80-83` use the name
  `ViTPose++_<size>_...` and do not resolve). A family token uses only `[a-z0-9]` and hyphens, so
  drop symbols such as `++`.
- **A different keypoint output.** A different keypoint output is a different sidecar (the family
  invariant: the `pose` contract differs). It is not a reason for a new family token. The keypoint
  output is always the second token.

The ids in scope under the rule. "Not exported" rows show the default model that makes a third
token necessary.

| Model | `model_id` | Folder | Reason for the third token |
|---|---|---|---|
| RTMO COCO (not exported) | `rtmo-coco17` | `rtmo/coco17/` | none: the default model (COCO only; mmpose v1.3.2 `configs/body_2d_keypoint/rtmo/coco/`) |
| RTMO body7 | `rtmo-coco17-body7` | `rtmo/coco17/` | `rtmo` has the COCO-only COCO-17 model above (OpenMMLab-Exporter `rtmo/identity.py:39`, `FAMILY`, `d0f4343`, OpenMMLab-Exporter decision 0039) |
| RTMO CrowdPose (not exported) | `rtmo-crowdpose14`; the body7-pretrained `l` model is `rtmo-crowdpose14-body7` | `rtmo/crowdpose14/` | the CrowdPose folder has a CrowdPose-only set and one `body7-crowdpose` config |
| RTMW | `rtmw-wholebody133` | `rtmw/wholebody133/` | none: one RTMW model line (the `cocktail14` configs and one metafile `rtmw_cocktail14.yml`, mmpose v1.3.2 `configs/wholebody_2d_keypoint/rtmpose/cocktail14/`; OpenMMLab-Exporter `rtmw/identity.py:33`, `FAMILY`, `d0f4343`) |
| RTMPose Halpe26 | `rtmpose-halpe26` | `rtmpose/halpe26/` | none: one Halpe26 model (metafile `rtmpose_body8-halpe26.yml`) |
| RTMPose body COCO-17 (skellytracker package sidecar, body8 checkpoint) | legacy `rtmpose-body`; a `vNEXT` rewrite takes `rtmpose-coco17-body8` | `rtmpose/coco17/` | `rtmpose` has a COCO-only COCO-17 model (`configs/body_2d_keypoint/rtmpose/coco/rtmpose_coco.yml`). The package file names the body7-pretrained checkpoint `rtmpose-s_simcc-body7_pt-body7_420e-256x192-acd4a1ef` (`rtmpose-body.yaml:62`). The metafile `rtmpose_body8-coco.yml` lists it for the `body8` config. |
| DWPose (`ubody` students) | `dwpose-wholebody133-ubody` | `dwpose/wholebody133/` | User decision (plan T15, 2026-10-23): a config set with no published weights counts as a model. mmpose v1.3.2 has two DWPose config sets, `dwpose/coco-wholebody/` (4 configs) and `dwpose/ubody/` (10 configs) (`configs/wholebody_2d_keypoint/dwpose/`). The DWPose README gives checkpoints only for the `ubody` students (`configs/wholebody_2d_keypoint/dwpose/README.md:16-22`). Thus `coco-wholebody` is the default model `dwpose-wholebody133`, and the students take `ubody`. |
| ViTPose 25 points | `vitpose-coco25` | `vitpose/coco25/` | none: one 25-point model (easy_ViTPose dataset `coco_25`) |
| ViTPose++ wholebody | `vitposepp-wholebody133` | `vitposepp/wholebody133/` | none: one wholebody model in the family `vitposepp` (T11) |
| ViTPose, out of scope, reserved | `vitpose-coco17`, `vitpose-aic14`, `vitpose-mpii16`; the ViTAE multi-dataset COCO-17 models `vitpose-coco17-<training>` | `vitpose/<keypoints>/` | `vitpose-coco17` is the COCO-only model (the untracked pose-models plan of OpenMMLab-Exporter (plan facts) section 1; plan facts) |
| YOLO26 pose (Ultralytics-Exporter) | `yolo26-coco17` at `vNEXT` | `yolo26/coco17/` | none: one COCO pose model (Ultralytics-Exporter `yolo_sidecar.py:22-25`, `f52ef68`, writes `yolo26-body` today) |
| MediaPipe hand landmark model (21 points) | `mediapipe-hand21` (to confirm by MediaPipe-Exporter and Qualcomm-Exporter) | `mediapipe/hand21/` | none known |
| MediaPipe face landmark, holistic (192 px) and landmarker (256 px) | one sidecar `mediapipe-<set>478` with two sizes (user decision Q2; MediaPipe-Exporter chooses the set name; the size keys come from the size-code proposal) | `mediapipe/<set>478/` | none: the user decision Q2 treats the two models as one model line with one keypoint output. Training set: unknown (the MediaPipe-Exporter plan names none; secondary, no git repo). If MediaPipe-Exporter finds two different training sets, the two models are not two sizes. Then rule 3 gives a training token to each model other than the default model. A face set has no reference dataset yet, so that case also needs one (Q2 and Q3, above). |
| MediaPipe hand re-crop model | `mediapipe-hand-roi`, outside this grammar (Q1, answered: user decision Q3 = a of the ROI-refiner proposal) | `detectors/roi_refiners/mediapipe/hand/` | none: the model gives a region of interest, not keypoints. The ROI-refiner proposal gives it the role `roi_refiner` and the id `{family}-{part}-roi[-{variant}]`. |

The MediaPipe ids come from untracked plans
(skellytracker `0025-model-id-suffix.md:40-46`).

**Questions for the user.** Q1, Q2, Q3 and Q4 are decided (Q2, Q3 and Q4 above, Q1 below).

- **Q1, a pipeline stage (answered by the user, 2026-10-23).** In this question, "the format" is the `model_id` grammar of this
  proposal, `{family}-{keypoints}` or `{family}-{keypoints}-{training}`, with the folder pair
  `detectors/keypoint_detectors/{family}/{keypoints}/` (2.2; `V-common.identity-7`). Each id of the
  grammar names a keypoint output. A pipeline stage that gives no keypoints has no `{keypoints}`
  token, so the grammar gives it no id and no folder. Example: the planned MediaPipe hand re-crop
  model. It gives `recrop_points [B,2,2]`, a centre point and a scale point of the next crop
  (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts); secondary, no git repo; earlier id
  `mediapipe-hand-recrop`, `inventory.yaml:107-113`, `:123-129`). The exporter guide says: "Known
  case: an ROI refiner is a gap. An ROI refiner is a model that gives a region of interest to the next
  model, for example a hand re-crop model. Do not describe it as a pose estimator with two fake
  keypoints." (`exporter-guide/sidecars/rules.md:6-8`; also `exporter-guide/sidecars/known-open-items.md:13` for the MediaPipe and Qualcomm hand plans).
  skellytracker decision 0020 (proposed, a gap record, `0020-roi-transform-and-source.md:3`, `:8-9`)
  records the ROI transform of the next model, and it "depends on rotated crops ... and on the ROI
  refiner gap" (`0020-roi-transform-and-source.md:21-22`). No decision entry records a role for an
  ROI refiner (the index of skellytracker `notes/decisions/README.md:23-68` at `dom/18-agents-adr-bootstrap-kit`). Thus the id of
  such a model waits for that role. A new role, with its enum and path edits, is one proposal
  (`exporter-guide/sidecars/workflow/phase-2-proposal.md:50`). That proposal adds the branch of the storage layout
  (`exporter-guide/sidecars/sidecar-files.md:45-46`) and the `model_id` rule of the role (`exporter-guide/sidecars/workflow/mapping-hints.md:25`). This
  proposal does not invent a token for it. MediaPipe-Exporter also waits for that role. Its plan
  says "Blocked on: the role proposal (0015) for the sidecar" (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)).
  The number in this quote is MediaPipe-Exporter decision 0015.
  MediaPipe-Exporter decision 0015 (accepted) asks for a new `role` value. The working name is `roi_refiner`. The
  proposal file is `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`. That proposal must build on
  skellytracker 0020 (MediaPipe-Exporter `notes/decisions/0015-recrop-new-sidecar-role.md:8-16`; no
  git repo). The user decision T19 (2026-10-23) gave Q1 to that proposal
  (the untracked pose-models plan of OpenMMLab-Exporter (plan facts); plan facts). **Answer (user decision Q3 = (a) of that proposal,
  2026-10-23; plan T20, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)).** The proposal is
  `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` (slug
  `roi-refiner-role`, its line 47). A refiner sidecar lives in
  `detectors/roi_refiners/{family}/{part}/`, and its id is `{family}-{part}-roi` or
  `{family}-{part}-roi-{variant}`, for example `mediapipe-hand-roi` (its lines 216-221; rule
  `V-post.roi_refiner-9`, lines 725-728; Q3 = (a), "It answers the pipeline-stage question Q1", lines
  231-234 and 3928-3930; lines checked again on 2026-10-24, review-readiness audit 2). Thus a pipeline stage that gives no keypoints is not in the grammar of this proposal.
  This proposal adds no stage token, and `V-common.identity-7` does not apply under `roi_refiners/`.

**Inverse.** none: no coordinates.

### 2.4 Validation rules

- [ ] `V-common.identity-7` **(vNEXT)** A sidecar under
  `detectors/keypoint_detectors/{family}/{keypoints}/` must have a `model_id` that is
  `{family}-{keypoints}` or `{family}-{keypoints}-{training}`. `{family}` and `{keypoints}` are the
  names of the two folders. `{family}` must match `^[a-z0-9]+(-[a-z0-9]+)*$`. No hyphen part of
  `{family}` after the first part may match the pattern of `{keypoints}`. `{keypoints}` must match
  `^[a-z0-9]*[a-z][1-9][0-9]*$`. The whole `{training}` string must match
  `^[a-z0-9]+(-[a-z0-9]+)*$`. The classes `[a-z]` and `[0-9]` are ASCII only.
- [ ] `V-common.identity-8` **(vNEXT)** In one folder, no two sidecars may name the same artifact
  `filename`. The check covers every artifact of every size, batch and precision of each sidecar.
- [ ] `V-common.identity-9` **(vNEXT)** For a sidecar under
  `detectors/keypoint_detectors/{family}/{keypoints}/`, the count of `{keypoints}` (the digits after
  its last letter) must equal `len(pose.tracked_points)` of the resolved sidecar.

The three rules read the path of the sidecar, the other sidecars of the folder, or the resolved
sidecar. Thus they are loader and catalog checks, not checks of one `SidecarModel` (see part 6).

**Why `V-common.identity-9`.** The spec has a keypoint list in each pose sidecar.
`pose.tracked_points` is required (`post/pose-schema.md:39`; `V-post.pose.schema-1`,
`pose-schema.md:117`). It is the ordered list of the keypoint names that the model outputs, and "the
keypoint count comes from this list. It is `len(tracked_points)`" (`pose-schema.md:60`; also the
shape key `K`, `pose-schema.md:107`). Thus a host can check the count of the folder against the
model. Without the rule, `rtmo/coco17/` could hold a 26-point model. The rule counts only
`tracked_points`, not `derived_points` (`pose-schema.md:41`). It uses the resolved sidecar, because
`tracked_points` can be a `$ref` (`pose-schema.md:39`).

Existing rules that name a value of this change:

- `V-common.identity-1` (basename equals `model_id`, `identity.md:36`) does not change. A valid
  `V-common.identity-7` id can still fail it (vector `basename-mismatch`).
- `V-post.pose.schema-1` (`pose-schema.md:117`) does not change. It makes `pose.tracked_points`
  present, so `V-common.identity-9` always has a list.
- `V-post.pose.schema-8` (`pose-schema.md:124`) does not change. With `V-common.identity-9`, a
  `keypoint_count` on a pose output also equals the folder count.
- No rule names `{family}-{part}` or the part folders today. `format.file_layout` has no rules of its
  own (`file-layout.md:118-120`).

Follow-ups, not in this proposal: a third token for an object detector (`object_detectors/{family}/`;
no model in scope needs it); the id and folder of an ROI refiner (Q1, answered: the ROI-refiner proposal gives them);
a second id for two models with the same output and the same training set that do not satisfy the
family invariant (after Q2; no model in scope needs it); the reference dataset of `hand21` and of
the face sets (Q3: undefined until a model needs it).

### 2.5 Selectors

none: `V-common.identity-7` applies to every sidecar under `detectors/keypoint_detectors/` with
`schema_version >= vNEXT`. `V-common.identity-9` applies to the same sidecars. They all have
`pose.tracked_points` (`V-post.pose.schema-1`, selector `role=pose_estimator`, `pose-schema.md:7-8`).
`V-common.identity-8` applies to the sidecars with `schema_version >= vNEXT` in one folder.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` keeps its `model_id` and its part folder. The three rules do
  not apply to it.
- The skellytracker package sidecars `rtmpose-body`, `rtmpose-hand`, `rtmpose-face` and
  `rtmw-wholebody` (all `schema_version: "v2024.09.1019"`, line 2 of each file) stay valid as legacy
  sidecars in their part folders. They would fail `V-common.identity-7` at `vNEXT`, because a part
  folder has no count. A `vNEXT` rewrite of each takes a new id, a new folder and a new catalog key,
  for example `rtmw-wholebody133`. The ids of the other three need the upstream evidence of each model
  (2.3, the table). `rtmpose-hand` also needs the reference dataset of `hand21`, because RTMPose has
  two `hand21` models (2.3, Q3). That dataset stays undefined until the rewrite needs it.
- The catalog keys of the legacy package sidecars do not change. The `detector_type` alias `rtmpose`
  of `rtmw-wholebody@skellytracker` (`format/versioning.md:85`) does not change.
- New rows of the "Legacy behaviour" table of `common.identity` (`identity.md:49-51`):

  ```text
  | `model_id` of a keypoint detector | `{family}-{part}`. Not checked against the folders. | `{family}-{keypoints}` or `{family}-{keypoints}-{training}` (`V-common.identity-7`). The count of `{keypoints}` equals `len(pose.tracked_points)` (`V-common.identity-9`). |
  | Artifact filenames of the sidecars in one folder | Not checked. | Unique across the sidecars (`V-common.identity-8`). |
  ```

- The new "Legacy behaviour" heading of `format.file_layout`:

  ```text
  ## Legacy behaviour

  | Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
  |-----------|-----------------------------------|---------------------------|
  | Folder of a keypoint detector | `detectors/keypoint_detectors/{family}/{part}/`. `{part}` is `hand`, `face`, `body` or `wholebody`. | `detectors/keypoint_detectors/{family}/{keypoints}/` (see [Identity](../common/identity.md#fields)). |
  ```

- The discovery rule (`file-layout.md:111-116`) does not read the folder names. It finds a sidecar in
  either folder form.

### 2.7 Changelog row

`schema_version` history: append this text to the end of the existing `vNEXT` row
(`changelog.md:68`). Do not add a second `vNEXT` row.

```text
The `model_id` of a keypoint detector is `{family}-{keypoints}` or `{family}-{keypoints}-{training}`, in the folder `detectors/keypoint_detectors/{family}/{keypoints}/`; `{keypoints}` is a set name and its point count (V-common.identity-7, V-common.identity-9). The sidecars in one folder must not name the same artifact filename (V-common.identity-8). Legacy sidecars keep the part folders `hand`, `face`, `body` and `wholebody`.
```

Summary of changes: a new row with the five columns of the table (`changelog.md:16`):

```text
| N | Identity, Layout | A keypoint detector `model_id` is `{family}-{keypoints}` or `{family}-{keypoints}-{training}`. `{keypoints}` is the keypoint output, a set name and its point count (`coco17`, `wholebody133`). The keypoint folder replaces the part folder: `keypoint_detectors/{family}/{keypoints}/`. The id must agree with the two folders (V-common.identity-7), and the count must equal `len(pose.tracked_points)` (V-common.identity-9). A family uses `{training}` only when it has more than one upstream model with the same keypoint output. The sidecars in one folder must not name the same artifact filename (V-common.identity-8). | RTMO body7, RTMPose Halpe26, ViTPose 25 points, DWPose (skellytracker decision 0025) | [`model_id`](common/identity.md#fields), [Storage layout](format/file-layout.md#storage-layout) |
```

`N` is the next free number when the proposal merges. Rows 1 to 19 exist (`changelog.md:18-36`).
13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order.
Do not fix `N` before the merge.

"Compatibility impact" (`changelog.md:55-59`): add this bullet.

```text
- A keypoint sidecar authored at `vNEXT` goes to `detectors/keypoint_detectors/{family}/{keypoints}/`. Its `model_id` must be `{family}-{keypoints}` or `{family}-{keypoints}-{training}` (V-common.identity-7), and the count of `{keypoints}` must equal `len(pose.tracked_points)` (V-common.identity-9). The sidecars in one folder must not name the same artifact filename (V-common.identity-8). Legacy sidecars keep their part folders and their ids.
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/model-sidecar/proposals/model-id-suffix/proposal.md` |
| Target file in skellytracker | `specs/model-sidecar/reference/common_identity.py` |
| Functions (one for each rule or value) | `check_basename(model_id, filename) -> bool` (`V-common.identity-1`); `check_role(role) -> bool` (`V-common.identity-2`); `check_required(sidecar) -> bool` (`V-common.identity-3`); `check_source_keys(source) -> bool` (`V-common.identity-4`); `check_source_values(source) -> bool` (`V-common.identity-5`); `check_source_name(name) -> bool` (`V-common.identity-6`); `parse_keypoint_token(keypoints) -> (valid, name, count)` (the keypoint token of `V-common.identity-7` and `V-common.identity-9`); `check_keypoint_model_id(model_id, family, keypoints) -> (valid, training)` (`V-common.identity-7`); `check_unique_artifact_filenames(filenames_by_model_id) -> (valid, duplicates)` (`V-common.identity-8`); `check_keypoint_count(keypoints, tracked_point_count) -> bool` (`V-common.identity-9`); `legacy_default_source(schema_version) -> {name, version}` (the "Legacy behaviour" value of `source`). |

skellytracker has no `specs/model-sidecar/reference/` folder at `dom/18-agents-adr-bootstrap-kit`. Thus the reference file
implements the full section as changed, not only the change (`templates/change-proposal.md:202-204`,
`exporter-guide/sidecars/workflow/phase-2-proposal.md:56-59`). It is also the reference-implementation step of `common.identity`. The
functions do not compare schema versions and do not read files. The caller applies the rules marked
**(vNEXT)** only when `schema_version >= vNEXT`, gives the names of the two folders, and gives
`len(pose.tracked_points)` of the resolved sidecar. The caller uses `legacy_default_source` only for
a legacy sidecar with no `source`. The file uses only the Python standard library.

Source commit: none (no host code). This exporter writes `model_id` from constants
(`rtmw/identity.py:33` and `rtmo/identity.py:39`, constant `FAMILY`; `d0f4343`, the same at `01d9b3d` and at `f3aeb47`). The committed
tests `tests/test_rtmo.py` and `tests/test_rtmw.py` each have one inline test that checks the one id
against its two folders: `test_model_id_is_family_keypoints_training` (`tests/test_rtmo.py:125-137` at `f3aeb47`, the same at `01d9b3d`)
and `test_model_id_is_family_keypoints` (`tests/test_rtmw.py:80-90`). They use the pattern `[a-z]+[0-9]+` with `re.fullmatch`. It differs from
the keypoint pattern of this proposal: it rejects a digit in the set name (`h36m17`, `300w68`), and
it accepts a leading zero and a zero count (`coco017`, `coco0`). The two ids of this exporter pass
both patterns. The tests compare the count with the point list (RTMO: the length of
`COCO17_TRACKED_POINTS`; RTMW: the literal 133). They do not call `check_keypoint_model_id` and do
not run the vectors. Source commit stays none until host code implements the functions and is
committed.

```python
"""Reference implementation of the section common.identity, as the proposal model-id-suffix changes it.

This file uses ASD-STE100 Simplified Technical English.

- Section ID: common.identity (changed; OpenMMLab-Exporter proposal model-id-suffix,
  specs/model-sidecar/proposals/model-id-suffix/proposal.md; builds on skellytracker decision 0025). The model_id
  format is the user decision T14 of 2026-10-23: {family}-{keypoints} or
  {family}-{keypoints}-{training}, in the folder detectors/keypoint_detectors/{family}/{keypoints}/.
- Source commit: none (no host code). The functions come from the text of part 2 of the proposal and
  from the current text of specs/model-sidecar/common/identity.md (skellytracker dom/18-agents-adr-bootstrap-kit; the file is the
  same at dom/12-single-working-branch, and at dom/21-move-sidecar-guide it differs only by one link target at line 81).
- Vectors: this file makes the vectors of part 4. They are unverified: no host implementation.
  Part 4 records the run of the vectors against this file (84 of 84 pass, 2026-10-23; run again
  2026-10-25, 84 of 84 pass).
- Parity result: none (a name changes no tensor and no decoded output).

skellytracker has no specs/model-sidecar/reference/common_identity.py. Thus this file implements the full
section as changed, not only the change (specs/model-sidecar/templates/change-proposal.md:202-204). It is
also the reference-implementation step of common.identity. There is one function for each rule and
for the legacy value, and one helper for the keypoint token:

- check_basename: V-common.identity-1.
- check_role: V-common.identity-2.
- check_required: V-common.identity-3.
- check_source_keys: V-common.identity-4 (vNEXT).
- check_source_values: V-common.identity-5 (vNEXT).
- check_source_name: V-common.identity-6 (vNEXT).
- parse_keypoint_token: the keypoint token of V-common.identity-7 and V-common.identity-9.
- check_keypoint_model_id: V-common.identity-7 (vNEXT, new).
- check_unique_artifact_filenames: V-common.identity-8 (vNEXT, new).
- check_keypoint_count: V-common.identity-9 (vNEXT, new).
- legacy_default_source: the "Legacy behaviour" value of source.

The functions do not compare schema versions. The caller applies the rules marked vNEXT only when
schema_version >= vNEXT (format.versioning). The caller uses legacy_default_source only for a sidecar
with schema_version < vNEXT and no source. The functions do not read files or folders. The caller
gives the names of the two folders and the length of pose.tracked_points of the resolved sidecar.
The functions use only the Python standard library.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

TOKENS = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
"""One or more lowercase tokens joined by one hyphen (the pattern of V-common.identity-6).

V-common.identity-7 uses it for the family and for the training token. Use TOKENS.fullmatch. The
whole string must match. re.match with a "$" anchor also accepts a final newline. The classes
[a-z] and [0-9] are ASCII only. Do not use \\d, \\w or str.isdigit in a port: they also accept
non-ASCII digits and letters.
"""

KEYPOINT_TOKEN = re.compile(r"(?P<name>[a-z0-9]*[a-z])(?P<count>[1-9][0-9]*)")
"""The keypoint token: a set name, then its point count (V-common.identity-7).

The pattern is ^[a-z0-9]*[a-z][1-9][0-9]*$. The name is all characters up to and including the last
letter. The count is the digits after the last letter. It has no leading zero, so it is 1 or more.
Thus each token has one parse: h36m17 gives the name h36m and the count 17. Use
KEYPOINT_TOKEN.fullmatch. The classes are ASCII only (see TOKENS).
"""

ROLES = ("object_detector", "pose_estimator")
"""The values of role (V-common.identity-2)."""

SOURCE_KEYS = frozenset({"name", "version"})
"""The keys of the source mapping (V-common.identity-4)."""

LEGACY_SOURCE_NAME = "skellytracker"
"""The source.name of a legacy sidecar (common.identity, "Legacy behaviour")."""


def check_basename(model_id: str, filename: str) -> bool:
    """common.identity, rule V-common.identity-1: model_id matches the sidecar basename.

    filename is the base name of the sidecar file, with no folder. Return True when it is
    "{model_id}.yaml".
    """
    return filename == f"{model_id}.yaml"


def check_role(role: object) -> bool:
    """common.identity, rule V-common.identity-2: role is a non-empty subset of the two roles.

    Return True for a non-empty list of values of ROLES with no value twice. A subset has each value
    once. skellytracker also rejects a repeated value (skellytracker/core/sidecar/model.py:489-494).
    """
    if isinstance(role, (str, bytes)) or not isinstance(role, Sequence):
        return False
    if not role:
        return False
    return all(value in ROLES for value in role) and len(set(role)) == len(role)


def check_required(sidecar: Mapping[str, object]) -> bool:
    """common.identity, rule V-common.identity-3: the sidecar has display_name, input with name,
    and a non-empty outputs array. Each entry of outputs has name.

    The rule is a presence check. It does not check the types of the values.
    """
    if "display_name" not in sidecar:
        return False
    model_input = sidecar.get("input")
    if not isinstance(model_input, Mapping) or "name" not in model_input:
        return False
    outputs = sidecar.get("outputs")
    if isinstance(outputs, (str, bytes)) or not isinstance(outputs, Sequence) or not outputs:
        return False
    return all(isinstance(entry, Mapping) and "name" in entry for entry in outputs)


def check_source_keys(source: object) -> bool:
    """common.identity, rule V-common.identity-4 (vNEXT): the sidecar has a top-level source
    mapping with exactly the keys name and version.

    source is the value of the top-level key source, or None when the key is absent.
    """
    return isinstance(source, Mapping) and set(source) == SOURCE_KEYS


def check_source_values(source: object) -> bool:
    """common.identity, rule V-common.identity-5 (vNEXT): source.name and source.version are
    non-empty strings.
    """
    if not isinstance(source, Mapping):
        return False
    return all(isinstance(source.get(key), str) and source.get(key) != "" for key in ("name", "version"))


def check_source_name(name: object) -> bool:
    """common.identity, rule V-common.identity-6 (vNEXT): source.name matches
    ^[a-z0-9]+(-[a-z0-9]+)*$. The whole string must match.
    """
    return isinstance(name, str) and TOKENS.fullmatch(name) is not None


def parse_keypoint_token(keypoints: object) -> tuple[bool, str | None, int | None]:
    """common.identity, the keypoint token of rules V-common.identity-7 and V-common.identity-9.

    keypoints is the name of the second folder under detectors/keypoint_detectors/. Return
    (True, name, count) when the whole string matches KEYPOINT_TOKEN. Return (False, None, None)
    for any other value, for example a part folder such as "body", which has no count.
    """
    if not isinstance(keypoints, str):
        return False, None, None
    match = KEYPOINT_TOKEN.fullmatch(keypoints)
    if match is None:
        return False, None, None
    return True, match.group("name"), int(match.group("count"))


def check_keypoint_model_id(model_id: str, family: str, keypoints: str) -> tuple[bool, str | None]:
    """common.identity, rule V-common.identity-7 (vNEXT): check the model_id of a sidecar under
    detectors/keypoint_detectors/{family}/{keypoints}/.

    family and keypoints are the names of the two folders. The family must match TOKENS. A hyphen
    part of the family after the first part must not match KEYPOINT_TOKEN. The keypoint token must
    match KEYPOINT_TOKEN. Return (True, None) for "{family}-{keypoints}", (True, training) for
    "{family}-{keypoints}-{training}" when the whole training token matches TOKENS, and
    (False, None) for any other value.

    The family check makes one model_id valid in one folder pair only. Without it,
    rtmo-coco17-body7 is valid in rtmo/coco17/ (training body7) and also in rtmo-coco17/body7/
    (no training token), and the two sidecars get one catalog key. The first part of the family
    can match KEYPOINT_TOKEN (yolo26).

    The rule does not say when a model must take a training token. That is authoring guidance
    (part 2.3 of the proposal), because it depends on the upstream models, not on one sidecar.
    """
    if not all(isinstance(value, str) for value in (model_id, family, keypoints)):
        return False, None
    if TOKENS.fullmatch(family) is None or not parse_keypoint_token(keypoints)[0]:
        return False, None
    if any(KEYPOINT_TOKEN.fullmatch(part) for part in family.split("-")[1:]):
        return False, None
    base = f"{family}-{keypoints}"
    if model_id == base:
        return True, None
    prefix = base + "-"
    if model_id.startswith(prefix):
        training = model_id[len(prefix):]
        if TOKENS.fullmatch(training):
            return True, training
    return False, None


def check_unique_artifact_filenames(
    filenames_by_model_id: Mapping[str, Sequence[str]],
) -> tuple[bool, list[str]]:
    """common.identity, rule V-common.identity-8 (vNEXT): in one folder, no two sidecars name the
    same artifact filename.

    filenames_by_model_id maps the model_id of each sidecar in one folder to the filename values of
    all artifacts of that sidecar (every size, batch and precision). Return (True, []) when each
    filename belongs to one sidecar. Return (False, names) otherwise. names is the sorted list of the
    filenames that two or more sidecars name. A filename that one sidecar names twice is not a
    finding of this rule.
    """
    owners: dict[str, set[str]] = {}
    for model_id, filenames in filenames_by_model_id.items():
        for filename in filenames:
            owners.setdefault(filename, set()).add(model_id)
    duplicates = sorted(name for name, ids in owners.items() if len(ids) > 1)
    return not duplicates, duplicates


def check_keypoint_count(keypoints: str, tracked_point_count: object) -> bool:
    """common.identity, rule V-common.identity-9 (vNEXT): the count of the keypoint token equals
    the number of keypoints that the sidecar declares.

    keypoints is the name of the second folder. tracked_point_count is len(pose.tracked_points) of
    the resolved sidecar (post.pose.schema: the keypoint count comes from that list). Return True
    when the keypoint token is valid and its count equals tracked_point_count. The count must be
    an int. A bool is not a count, and a float such as 17.0 is not a count.
    """
    if isinstance(tracked_point_count, bool) or not isinstance(tracked_point_count, int):
        return False
    valid, _, count = parse_keypoint_token(keypoints)
    return valid and count == tracked_point_count


def legacy_default_source(schema_version: str) -> dict[str, str]:
    """common.identity, "Legacy behaviour": the source of a sidecar with schema_version < vNEXT and
    no source key.

    Return {name: skellytracker, version: <schema_version>}.
    """
    return {"name": LEGACY_SOURCE_NAME, "version": schema_version}


__all__ = [
    "KEYPOINT_TOKEN",
    "LEGACY_SOURCE_NAME",
    "ROLES",
    "SOURCE_KEYS",
    "TOKENS",
    "check_basename",
    "check_keypoint_count",
    "check_keypoint_model_id",
    "check_required",
    "check_role",
    "check_source_keys",
    "check_source_name",
    "check_source_values",
    "check_unique_artifact_filenames",
    "legacy_default_source",
    "parse_keypoint_token",
]
```

## 4. Vectors

```yaml
section: common.identity
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/model-id-suffix/proposal.md`
unverified: no host code implements these functions or runs these cases; the exporter tests at d0f4343 check only the ids rtmo-coco17-body7 and rtmw-wholebody133
cases:
  - id: default-id
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmw-wholebody133, family: rtmw, keypoints: wholebody133}
    expect: {valid: true, training: null}
  - id: training-id
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body7, family: rtmo, keypoints: coco17}
    expect: {valid: true, training: body7}
  - id: training-two-tokens
    function: check_keypoint_model_id
    params: {}
    input: {model_id: ab-coco17-x-y, family: ab, keypoints: coco17}
    expect: {valid: true, training: x-y}
  - id: legacy-part-folder-wholebody
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmw-wholebody, family: rtmw, keypoints: wholebody}
    expect: {valid: false, training: null}
  - id: legacy-part-folder-body
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmpose-body, family: rtmpose, keypoints: body}
    expect: {valid: false, training: null}
  - id: glued-suffix-in-part-folder
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-body7, family: rtmo, keypoints: body}
    expect: {valid: false, training: null}
  - id: leading-zero-count
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco017, family: rtmo, keypoints: coco017}
    expect: {valid: false, training: null}
  - id: zero-count
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco0, family: rtmo, keypoints: coco0}
    expect: {valid: false, training: null}
  - id: count-without-name
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-17, family: rtmo, keypoints: "17"}
    expect: {valid: false, training: null}
  - id: uppercase-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-COCO17, family: rtmo, keypoints: COCO17}
    expect: {valid: false, training: null}
  - id: uppercase-family
    function: check_keypoint_model_id
    params: {}
    input: {model_id: RTMO-coco17, family: RTMO, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: uppercase-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-Body7, family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: underscore-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: vitpose-coco_25, family: vitpose, keypoints: coco_25}
    expect: {valid: false, training: null}
  - id: underscore-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body_7, family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: non-ascii-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: "rtmo-coco17-body７", family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: empty-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-, family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: double-hyphen
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17--body7, family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: trailing-hyphen-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body7-, family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: wrong-keypoints-folder
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body7, family: rtmo, keypoints: crowdpose14}
    expect: {valid: false, training: null}
  - id: wrong-family-folder
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body7, family: rtmpose, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: empty-family
    function: check_keypoint_model_id
    params: {}
    input: {model_id: "-coco17", family: "", keypoints: coco17}
    expect: {valid: false, training: null}
  - id: hyphen-in-family
    function: check_keypoint_model_id
    params: {}
    input: {model_id: ab-cd-coco17-body7, family: ab-cd, keypoints: coco17}
    expect: {valid: true, training: body7}
  - id: family-part-like-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-body7, family: rtmo-coco17, keypoints: body7}
    expect: {valid: false, training: null}
  - id: digit-in-set-name
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmpose-h36m17, family: rtmpose, keypoints: h36m17}
    expect: {valid: true, training: null}
  - id: digit-first-set-name
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmpose-300w68, family: rtmpose, keypoints: 300w68}
    expect: {valid: true, training: null}
  - id: family-like-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: yolo26-coco17, family: yolo26, keypoints: coco17}
    expect: {valid: true, training: null}
  - id: training-like-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmo-coco17-h36m17, family: rtmo, keypoints: coco17}
    expect: {valid: true, training: h36m17}
  - id: size-like-training
    function: check_keypoint_model_id
    params: {}
    input: {model_id: rtmw-wholebody133-l-256, family: rtmw, keypoints: wholebody133}
    expect: {valid: true, training: l-256}
  - id: trailing-newline
    function: check_keypoint_model_id
    params: {}
    input: {model_id: "rtmo-coco17-body7\n", family: rtmo, keypoints: coco17}
    expect: {valid: false, training: null}
  - id: trailing-newline-keypoints
    function: check_keypoint_model_id
    params: {}
    input: {model_id: "rtmo-coco17\n", family: rtmo, keypoints: "coco17\n"}
    expect: {valid: false, training: null}
  - id: token-coco17
    function: parse_keypoint_token
    params: {}
    input: {keypoints: coco17}
    expect: {valid: true, name: coco, count: 17}
  - id: token-wholebody133
    function: parse_keypoint_token
    params: {}
    input: {keypoints: wholebody133}
    expect: {valid: true, name: wholebody, count: 133}
  - id: token-digit-in-name
    function: parse_keypoint_token
    params: {}
    input: {keypoints: h36m17}
    expect: {valid: true, name: h36m, count: 17}
  - id: token-digit-first-name
    function: parse_keypoint_token
    params: {}
    input: {keypoints: 300w68}
    expect: {valid: true, name: 300w, count: 68}
  - id: token-one-letter-one-digit
    function: parse_keypoint_token
    params: {}
    input: {keypoints: a1}
    expect: {valid: true, name: a, count: 1}
  - id: token-part-folder
    function: parse_keypoint_token
    params: {}
    input: {keypoints: body}
    expect: {valid: false, name: null, count: null}
  - id: token-ends-in-letter
    function: parse_keypoint_token
    params: {}
    input: {keypoints: h36m}
    expect: {valid: false, name: null, count: null}
  - id: token-leading-zero
    function: parse_keypoint_token
    params: {}
    input: {keypoints: coco017}
    expect: {valid: false, name: null, count: null}
  - id: token-count-only
    function: parse_keypoint_token
    params: {}
    input: {keypoints: "17"}
    expect: {valid: false, name: null, count: null}
  - id: token-underscore
    function: parse_keypoint_token
    params: {}
    input: {keypoints: coco_25}
    expect: {valid: false, name: null, count: null}
  - id: token-hyphen
    function: parse_keypoint_token
    params: {}
    input: {keypoints: coco-17}
    expect: {valid: false, name: null, count: null}
  - id: token-uppercase
    function: parse_keypoint_token
    params: {}
    input: {keypoints: Coco17}
    expect: {valid: false, name: null, count: null}
  - id: token-fullwidth-digit
    function: parse_keypoint_token
    params: {}
    input: {keypoints: "coco1７"}
    expect: {valid: false, name: null, count: null}
  - id: token-non-ascii-letter
    function: parse_keypoint_token
    params: {}
    input: {keypoints: "cocö17"}
    expect: {valid: false, name: null, count: null}
  - id: token-not-a-string
    function: parse_keypoint_token
    params: {}
    input: {keypoints: 17}
    expect: {valid: false, name: null, count: null}
  - id: count-match
    function: check_keypoint_count
    params: {}
    input: {keypoints: coco17, tracked_point_count: 17}
    expect: {valid: true}
  - id: count-match-wholebody
    function: check_keypoint_count
    params: {}
    input: {keypoints: wholebody133, tracked_point_count: 133}
    expect: {valid: true}
  - id: count-digit-in-name
    function: check_keypoint_count
    params: {}
    input: {keypoints: h36m17, tracked_point_count: 17}
    expect: {valid: true}
  - id: count-mismatch
    function: check_keypoint_count
    params: {}
    input: {keypoints: coco17, tracked_point_count: 26}
    expect: {valid: false}
  - id: count-digits-of-name
    function: check_keypoint_count
    params: {}
    input: {keypoints: h36m17, tracked_point_count: 3617}
    expect: {valid: false}
  - id: count-part-folder
    function: check_keypoint_count
    params: {}
    input: {keypoints: body, tracked_point_count: 17}
    expect: {valid: false}
  - id: count-bool
    function: check_keypoint_count
    params: {}
    input: {keypoints: a1, tracked_point_count: true}
    expect: {valid: false}
  - id: count-float
    function: check_keypoint_count
    params: {}
    input: {keypoints: coco17, tracked_point_count: 17.0}
    expect: {valid: false}
  - id: basename-match
    function: check_basename
    params: {}
    input: {model_id: rtmpose-halpe26, filename: rtmpose-halpe26.yaml}
    expect: {valid: true}
  - id: basename-mismatch
    function: check_basename
    params: {}
    input: {model_id: rtmpose-halpe26, filename: rtmpose-body.yaml}
    expect: {valid: false}
  - id: basename-wrong-extension
    function: check_basename
    params: {}
    input: {model_id: rtmo-coco17-body7, filename: rtmo-coco17-body7.yml}
    expect: {valid: false}
  - id: role-one
    function: check_role
    params: {}
    input: {role: [pose_estimator]}
    expect: {valid: true}
  - id: role-both
    function: check_role
    params: {}
    input: {role: [object_detector, pose_estimator]}
    expect: {valid: true}
  - id: role-empty
    function: check_role
    params: {}
    input: {role: []}
    expect: {valid: false}
  - id: role-unknown
    function: check_role
    params: {}
    input: {role: [segmenter]}
    expect: {valid: false}
  - id: role-duplicate
    function: check_role
    params: {}
    input: {role: [pose_estimator, pose_estimator]}
    expect: {valid: false}
  - id: role-not-a-list
    function: check_role
    params: {}
    input: {role: pose_estimator}
    expect: {valid: false}
  - id: required-present
    function: check_required
    params: {}
    input: {sidecar: {display_name: RTMPose Halpe26, input: {name: input}, outputs: [{name: simcc_x}, {name: simcc_y}]}}
    expect: {valid: true}
  - id: required-no-display-name
    function: check_required
    params: {}
    input: {sidecar: {input: {name: input}, outputs: [{name: simcc_x}]}}
    expect: {valid: false}
  - id: required-input-no-name
    function: check_required
    params: {}
    input: {sidecar: {display_name: X, input: {}, outputs: [{name: simcc_x}]}}
    expect: {valid: false}
  - id: required-outputs-empty
    function: check_required
    params: {}
    input: {sidecar: {display_name: X, input: {name: input}, outputs: []}}
    expect: {valid: false}
  - id: required-output-no-name
    function: check_required
    params: {}
    input: {sidecar: {display_name: X, input: {name: input}, outputs: [{name: simcc_x}, {}]}}
    expect: {valid: false}
  - id: source-keys-exact
    function: check_source_keys
    params: {}
    input: {source: {name: openmmlab-exporter, version: 0.1.0}}
    expect: {valid: true}
  - id: source-absent
    function: check_source_keys
    params: {}
    input: {source: null}
    expect: {valid: false}
  - id: source-missing-key
    function: check_source_keys
    params: {}
    input: {source: {name: openmmlab-exporter}}
    expect: {valid: false}
  - id: source-extra-key
    function: check_source_keys
    params: {}
    input: {source: {name: openmmlab-exporter, version: 0.1.0, commit: cce619d}}
    expect: {valid: false}
  - id: source-values-strings
    function: check_source_values
    params: {}
    input: {source: {name: openmmlab-exporter, version: 0.1.0}}
    expect: {valid: true}
  - id: source-values-empty-version
    function: check_source_values
    params: {}
    input: {source: {name: openmmlab-exporter, version: ""}}
    expect: {valid: false}
  - id: source-values-number-version
    function: check_source_values
    params: {}
    input: {source: {name: openmmlab-exporter, version: 1.0}}
    expect: {valid: false}
  - id: source-name-valid
    function: check_source_name
    params: {}
    input: {name: openmmlab-exporter}
    expect: {valid: true}
  - id: source-name-uppercase
    function: check_source_name
    params: {}
    input: {name: OpenMMLab}
    expect: {valid: false}
  - id: source-name-double-hyphen
    function: check_source_name
    params: {}
    input: {name: a--b}
    expect: {valid: false}
  - id: source-name-underscore
    function: check_source_name
    params: {}
    input: {name: openmmlab_exporter}
    expect: {valid: false}
  - id: source-name-trailing-newline
    function: check_source_name
    params: {}
    input: {name: "skellytracker\n"}
    expect: {valid: false}
  - id: artifacts-unique
    function: check_unique_artifact_filenames
    params: {}
    input: {filenames_by_model_id: {rtmo-coco17: [rtmo-coco17-m_b1_fp32.onnx], rtmo-coco17-body7: [rtmo-coco17-body7-m_b1_fp32.onnx]}}
    expect: {valid: true, duplicates: []}
  - id: artifacts-size-like-training-collision
    function: check_unique_artifact_filenames
    params: {}
    input: {filenames_by_model_id: {rtmo-coco17-m: [rtmo-coco17-m-l_b1_fp32.onnx], rtmo-coco17: [rtmo-coco17-m-l_b1_fp32.onnx]}}
    expect: {valid: false, duplicates: [rtmo-coco17-m-l_b1_fp32.onnx]}
  - id: artifacts-training-like-size-collision
    function: check_unique_artifact_filenames
    params: {}
    input: {filenames_by_model_id: {rtmo-coco17: [rtmo-coco17-body7-m_b1_fp32.onnx], rtmo-coco17-body7: [rtmo-coco17-body7-m_b1_fp32.onnx]}}
    expect: {valid: false, duplicates: [rtmo-coco17-body7-m_b1_fp32.onnx]}
  - id: artifacts-repeat-in-one-sidecar
    function: check_unique_artifact_filenames
    params: {}
    input: {filenames_by_model_id: {rtmo-coco17-body7: [rtmo-coco17-body7-m_b1_fp32.onnx, rtmo-coco17-body7-m_b1_fp32.onnx]}}
    expect: {valid: true, duplicates: []}
  - id: legacy-default-source
    function: legacy_default_source
    params: {}
    input: {schema_version: v2024.09.1019}
    expect: {source: {name: skellytracker, version: v2024.09.1019}}
```

The cases `family-like-keypoints` and `training-like-keypoints` show that a family token and a
training token can match the keypoint pattern. `yolo26` matches the keypoint pattern, and so do
`body7` and `h36m17`. The rule reads the family and the keypoint token from the folders. The case
`hyphen-in-family` uses a synthetic family with two tokens (`ab-cd`); no keypoint family in use has a
hyphen yet. The case `family-part-like-keypoints` gives the id `rtmo-coco17-body7` in the folder pair
`rtmo-coco17/body7/`. The family part `coco17` matches the keypoint pattern, so the case is invalid,
and the id is valid only in `rtmo/coco17/` (case `training-id`). The case `training-two-tokens` uses
the synthetic id `ab-coco17-x-y`: no id in scope has a hyphen in the training token (2.3).

The cases `legacy-part-folder-wholebody`, `legacy-part-folder-body` and `glued-suffix-in-part-folder`
are the current ids in their part folders. They fail at `vNEXT`. The caller does not apply the rule
to a legacy sidecar (2.6).

The case `size-like-training` shows that the grammar accepts a size name as a training token (2.3).
The two artifact collision cases show the two forms of the file-name collision of 2.3, "Sizes and
training tokens", and that `V-common.identity-8` rejects both. `artifacts-size-like-training-collision`
has the size-like training token `m` (sidecar `rtmo-coco17-m` with the size `l`, sidecar
`rtmo-coco17` with the size `m-l`). `artifacts-training-like-size-collision` has the training-like
size name `body7-m` (sidecar `rtmo-coco17` with the size `body7-m`, sidecar `rtmo-coco17-body7` with
the size `m`). The case `artifacts-repeat-in-one-sidecar` is valid for this rule:
`V-common.identity-8` compares different sidecars only.

The cases `trailing-newline`, `trailing-newline-keypoints` and `source-name-trailing-newline` need a
full match. A port that uses `re.match` with a `$` anchor accepts a final newline (`$` matches before
it) and fails these cases. The case `count-digits-of-name` catches a port that reads all digits of
the token (`h36m17` has the digits `3617`) in place of the digits after the last letter. The case
`count-bool` catches a port in which `True == 1`. The case `count-float` catches a port that accepts
`17.0`, because `17 == 17.0` in Python. The cases `token-fullwidth-digit` (`coco1７`, the fullwidth
digit U+FF17), `token-non-ascii-letter` (`cocö17`) and `non-ascii-training` (`body７`) catch a port
with Unicode classes (`\d`, `\w`): the classes are ASCII only (2.3). The YAML file must be UTF-8.
`source-values-number-version` uses `1.0`, which YAML reads as a number (`identity.md:86`). The cases
`token-count-only` and `count-without-name` write `"17"` in quotes, so that YAML reads a string.
`token-not-a-string` gives the integer 17.

**Run of the vectors.** Script
`scripts/run_identity_vectors.py` in the local temporary scratch folder of session `77365e8d`
(not in the repo). It reads the `yaml` block above from this file, loads the reference file with
`importlib.util.spec_from_file_location` and compares each result with `expect` (also the type of
`count`). Command: `uv run --project <exporter repo> python -I <script>`.
Result, 2026-10-23 (run again after the Q2 to Q4 update, after its review fixes and after the
`d0f4343` update of the `unverified` line; these change no rule, no case and no reference function): 84 cases, 84 pass, 0 fail, no duplicate case id, all 11 functions have cases
(`check_keypoint_model_id` 30, `parse_keypoint_token` 15, `check_keypoint_count` 8,
`check_basename` 3, `check_role` 6, `check_required` 5, `check_source_keys` 4,
`check_source_values` 3, `check_source_name` 5, `check_unique_artifact_filenames` 4,
`legacy_default_source` 1). Run again on 2026-10-24 after the M1 and M2 edits (no rule, no case
and no reference function changed; scratch `omm-proposals/run_all.py`, the same comparison): 84 of
84 pass. Run again on 2026-10-25 after the re-pin to skellytracker `dom/21-move-sidecar-guide` (no rule, no case and
no reference function changed; the top note of the reference file changed; scratch
`run_identity_vectors_2026-10-25.py`, the same comparison, `uv run python -I`): 84 of 84 pass, 0
fail, no duplicate case id, the same 11 function counts. A second script (`scripts/mutants2.py` in the same folder) ran the
vectors against eight wrong ports of the reference file. Each wrong port fails at least one case:
`re.match` with `$` (fails `trailing-newline-keypoints`); the count from all digits of the token
(fails 4 cases, for example `count-digits-of-name`); a bool as a count (fails `count-bool`); no int
check of the count (fails `count-float`); a name that must start with a letter (fails
`digit-first-set-name` and `token-digit-first-name`); `\d` for the count (fails
`token-fullwidth-digit`); Unicode classes for the name, the count and the tokens (fails
`non-ascii-training`, `token-fullwidth-digit` and `token-non-ascii-letter`); no check of the family
parts (fails `family-part-like-keypoints`). This run checks the reference against its own vectors. It
is not a host verification, so the vectors stay `unverified`.

## 5. Parity evidence

none. A `model_id` changes no tensor and no decoded output (the model intake template: "A row for a
name or a path is never a `near-miss`"). The check for this proposal is the rule itself.

Today two inline tests (`f3aeb47`) check the ids of this exporter against their folders:
`tests/test_rtmo.py:125-137` (`rtmo-coco17-body7` in `rtmo/coco17/`) and `tests/test_rtmw.py:80-90`
(`rtmw-wholebody133` in `rtmw/wholebody133/`). Part 3 describes them. They do not call the functions
of the reference file. Plan step 4.5 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), step 4, item 5) adds
`tests/test_sidecar_identity.py`. It holds a standard-library copy of `parse_keypoint_token`,
`check_keypoint_model_id` and `check_keypoint_count` only. It runs `V-common.identity-7` and
`V-common.identity-9` on the `model_id`, the `{family}/{keypoints}` folder and the tracked-point count
of each registered keypoint adapter. It runs the 53 cases of these three functions in part 4 (30
`check_keypoint_model_id`, 15 `parse_keypoint_token`, 8 `check_keypoint_count`), copied into the test
as literal data. It does not read them from the untracked plan folder of OpenMMLab-Exporter. The other 31 cases test the other 8 functions.
The test does not copy them.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | n/a (no numeric output) |
| Test images | n/a |
| Upstream reference | n/a |
| Export error | n/a |
| Preprocessed input | n/a |
| Row count for each image | n/a |
| Final outputs in source-image coordinates | n/a |
| Result | n/a |
| Script path in the exporter repo | n/a. The exporter test that runs the rule is planned: `tests/test_sidecar_identity.py`, plan step 4.5 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)), with the scope of the paragraph above. |
| Exporter commit of the script | n/a |
| Command | n/a |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/sidecar/loader.py`: checks next to the basename check of `V-common.identity-1` (`loader.py:40-46`). The loader knows the path, so it can read `{family}` and `{keypoints}` from the two parent folders. It has the validated sidecar, so it can give `len(sidecar.pose.tracked_points)` to `V-common.identity-9`. |
| Dispatch point | `load_sidecar`, after `expected_basename` (`loader.py:40`). Apply `V-common.identity-7` and `V-common.identity-9` when the sidecar is under `detectors/keypoint_detectors/` of its root and `schema_version >= vNEXT`. |
| Validator changes (`model.py`, with rule IDs) | none in `SidecarModel` (the model does not know the path or the other sidecars). `V-common.identity-7` and `V-common.identity-9` are loader checks. `V-common.identity-8` is a catalog check: the catalog of skellytracker decision 0016 lists the sidecars of each folder, so it can compare their artifact filenames. The catalog also runs `V-common.identity-7` and `V-common.identity-9` when it finds a sidecar. Two sidecars that fail `V-common.identity-8` are both unavailable, and the reason names the filename and the two sidecar paths. |
| Tests | The vectors of part 4 (`specs/model-sidecar/vectors/common.identity.yaml`). A loader test with a temporary root: `keypoint_detectors/rtmpose/halpe26/rtmpose-halpe26.yaml` with 26 tracked points loads; the same file with 17 tracked points fails `V-common.identity-9`; `keypoint_detectors/rtmo/body/rtmo-body7.yaml` at `vNEXT` fails `V-common.identity-7`; a legacy sidecar in a part folder loads. A catalog test with two sidecars in one folder that name one filename. The doc tests of 2.1 (`tools/tests/test_examples.py`, `tools/tests/test_traceability.py`). |
| Existing code that the change touches | `skellytracker/core/sidecar/loader.py` (`load_sidecar`); `skellytracker/tests/sidecar/test_model_validation.py` (or a new loader test); `tools/tests/test_examples.py` (`test_example_follows_the_storage_layout`, `:114-122`); `tools/tests/test_traceability.py` (the key lists of 2.1); `tools/make_vectors.py` and `tools/tests/test_vectors.py` (the vector file of part 4); the four decision-entry links of `tools/tests/test_links.py` (2.1); `tools/tests/test_sidecar_trace.py` (`BAZ`, only if the trace tool applies the rules). |

**Search of the skellytracker code for the part folders and for `model_id` parsing** (`dom/12-single-working-branch`;
`grep` of `skellytracker/` and `tools/` for `model_id`, `keypoint_detectors`, the part names,
`split("-")`, `rsplit(`, `parent.name` and `.parts[`; again at `dom/18-agents-adr-bootstrap-kit`: only the lines of `tools/check_links.py` move, and the new match `tools/check_private_data.py:105` (`rsplit("@", 1)`) splits an e-mail address, not a `model_id`):

| Place | What it does | Effect of the change |
|---|---|---|
| `skellytracker/core/sidecar/loader.py:40-46` (`load_sidecar`) | Compares the basename with `model_id`. Reads no folder name. | The new checks go here (above). |
| `tools/tests/test_examples.py:114-122` (`test_example_follows_the_storage_layout`) | Requires a part folder for each keypoint example (`:122`). | Must change (2.1). This is the only code that checks the part folder names. |
| `tools/tests/test_sidecar_trace.py:52-58`, `:135`, `:171`, `:1052` (the fixture `BAZ`) | Writes a `vNEXT` keypoint sidecar `baz` to `keypoint_detectors/baz/body/baz.yaml` and expects the status `unavailable`. | The fixture fails `V-common.identity-7` and has no `pose.tracked_points`. Change it only if `tools/sidecar_trace.py` applies the new rules (2.1). |
| `tools/tests/test_traceability.py:539-540` | Expects two package files in part folders (`mediapipe/body/mediapipe_body.yaml`, `rtmw/wholebody/rtmw_wholebody_to_canonical_mapping.yaml`) in the skipped list. | none: they are package files, not `vNEXT` sidecars. |
| `tools/tests/test_vectors.py:32-41`, `:111`, `:141`, `:175`; `tools/make_vectors.py:2411-2421` | Requires each vector file to come from `make_vectors.py`, with no `function` case key. | Must change (2.1). |
| `tools/check_links.py:125-131` at `dom/18-agents-adr-bootstrap-kit` (`tools/tests/test_links.py:16`) | Checks the relative links of `specs/` and `notes/`. | Four links of decision entries break when the examples move (2.1, the link-only edit). |
| `tools/tests/test_traceability.py:50-61`, `:572-621`, `:655-679` | Lists the catalog keys of the examples. | Three keys change (2.1). |
| `tools/sidecar_trace.py:363-368` (`_is_sidecar`) and `:416` (the key) | Discovery by `model_id == path.stem`; the key `<model_id>@<source>`. | none: it reads no folder name and does not split `model_id`. |
| `tools/sidecar_refs.py:107-113` (`default_root`) | Finds the root as the parent of the folder `detectors`. | none: it does not read the folders below `detectors`. |
| `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose_body_detector.py:35`, `rtmpose/face/rtmpose_face_detector.py:35`, `rtmpose/hand/rtmpose_hand_detector.py:37`, `rtmw/wholebody/rtmw_wholebody_detector.py:31` | Each loads its package sidecar from a fixed path next to the module. | none: the package sidecars stay legacy in their part folders. |
| `skellytracker/core/sidecar/runtime.py:46` | Says that the spec name is the choice of the caller, "not derived from `sidecar.model_id`/`size`". | none. |
| `decisions/scripts/check_split_verbatim.py:1315-1345` | Compares the "Sidecar:" lines of `examples/README.md` with `decisions/scripts/split_manifest.yaml`. It proves the past split (its docstring, `:1-40`). | for the implementer: the new links of 2.1 differ from the manifest. Its unit tests use small inputs (`tools/tests/test_check_split_verbatim.py:1`). It is not known if a later run against the current tree is expected. |
| Catalog and discovery | none yet (skellytracker decision 0016). | The catalog key changes with `model_id` (`rtmw-wholebody133@openmmlab-exporter`). The legacy package keys do not change. |

No code splits a `model_id` at its hyphens. The match `charuco_annotator.py:114` (`name.split("-")`)
is a Charuco name, not a sidecar id. The `name="body"` and `"wholebody"` strings in `run_demo.py`
files and `skellytracker/examples/demo_bbox_policy.py:66` are stage names, not folders.

## 7. Exporter impact

| Exporter | Affected sidecars | Change | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmo-body7` (written to `rtmo/body7/` before); `rtmw-wholebody` (written to `rtmw/wholebody/` before); the new `rtmpose-halpe26`, `dwpose-wholebody133-ubody`, `vitpose-coco25` and `vitposepp-wholebody133` | RTMO and RTMW: done in code on the branch `rtmo-model-id-variant` (OpenMMLab-Exporter decision 0039, commit `d0f4343`, not pushed): `rtmo-coco17-body7` in `detectors/keypoint_detectors/rtmo/coco17/` and `rtmw-wholebody133` in `detectors/keypoint_detectors/rtmw/wholebody133/` (constants `FAMILY`, `SIDECAR_FILENAME`, `FAMILY_BRANCH` at `rtmo/identity.py:39-42` and `rtmw/identity.py:33-36`). The next run of each family makes fresh raw exports and publishes to the new folders (`notes/decisions/0039-keypoint-model-id-format.md:88-90`). OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMO or RTMW sidecar until the intake of the family is `describes`, so the run writes the new sidecars only at that later round. Thus the regenerated RTMW sidecar for the reference example of 2.1 also comes at that round; the RTMO example uses `notes/decisions/rtmo-coco17-body7.yaml` (2.1, row `inventory.yaml`). The old folders in `exports/` stay until the user decides (`:91-93`). The new families: write each sidecar in its keypoint folder (the untracked pose-models plan of OpenMMLab-Exporter (plan facts) section 1). | none |
| Roboflow-Exporter | none (object detectors only) | none | none |
| Ultralytics-Exporter | `yolo26-body` (`yolo_sidecar.py:22-25`, `POSE_PART = "body"`, `POSE_MODEL_ID`; `:104-107`, `_ROLE_BRANCHES` maps the pose role to `keypoint_detectors/yolo26/body`; `f52ef68`, HEAD `2e0280e`) | It writes `schema_version` `v2024.09.1019` today (`exporter-guide/sidecars/known-open-items.md:12`), so its sidecar is legacy and stays valid. When it writes `vNEXT`, it writes `yolo26-coco17` in `keypoint_detectors/yolo26/coco17/` (one COCO pose model: no training token). This id is derived by this proposal. It is not in the T14 scope list. The user confirmed it (M1, plan T23, 2026-10-24). The Ultralytics-Exporter code still writes `yolo26-body`. The YOLO26 pose forecast example moves now, with a recorded edit of its `model_id` (2.1, `inventory.yaml` row). | none |
| Qualcomm-Exporter | the planned hand models `mediapipe-hand` and `mediapipe-hand-recrop` (the untracked hand pose export plan of Qualcomm-Exporter (plan facts); untracked; HEAD `4ca4586`) | Its plan changes: the hand landmark model becomes `mediapipe-hand21` in `mediapipe/hand21/` (to confirm with its plan). The re-crop model has no id under this format. Q1 is answered: it is an ROI refiner, `mediapipe-hand-roi` in `detectors/roi_refiners/mediapipe/hand/` (the ROI-refiner proposal, user decision Q3 = a; Qualcomm-Exporter must confirm it in its plan). No code writes these ids (skellytracker `0025-model-id-suffix.md:44-46`). | none |
| MediaPipe-Exporter | the planned `mediapipe-hand-landmark` (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), section 3.4, row "Model ID"), `mediapipe-hand-recrop` (section 3.5), `mediapipe-pose-landmark` (section 3.2, 39 output points) and `mediapipe-face-landmark` (section 3.7, 478 points); the manifest paths `mediapipe/hand/` and `mediapipe/hand-recrop/` (section 4); no git repo | Its plan changes: the hand landmark model becomes `mediapipe-hand21` in `mediapipe/hand21/`. The pose and face landmark models need a keypoint token whose count equals their `tracked_points` (for example the 478 face points). The exporter chooses the set names. The re-crop model is an ROI refiner: `mediapipe-hand-roi` in `detectors/roi_refiners/mediapipe/hand/` (Q1, answered by user decision Q3 = a of its proposal `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, which builds on MediaPipe-Exporter decision 0015 and skellytracker 0020). The two face landmark models with 478 points are two sizes of one sidecar `mediapipe-<set>478` (user decision Q2), if the exporter gives them one input tensor name and one output set (2.3, Q2). Its plan section 3.8 "Naming question" then has its answer. The size keys follow the size-code proposal. | none |
| The proposing exporter, if it is not in this table | none (OpenMMLab-Exporter is in the table) | none | none |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-hand`, `rtmpose-face`, `rtmw-wholebody` | none (legacy, `v2024.09.1019`; they stay in their part folders) | none |

The skellytracker package sidecars have `schema_version: "v2024.09.1019"`. Their legacy meaning does
not change.

**Intake rows that are `exact` with an exporter departure (correction of 2026-10-24).** These rows
are not `gap` rows of this proposal. Under the current text, each verdict is `exact`, and the last
column records the value of the exporter as a departure, with this proposal as the reason:

| Intake | Row | Sidecar value (current text) | Exporter value (planned or written) |
|---|---|---|---|
| the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) | F1 (`:133`) | `rtmw-wholebody` | `rtmw-wholebody133` (written, `rtmw/identity.py:33`) |
| same | L1 (`:214`) | `exports/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` | `.../rtmw/wholebody133/rtmw-wholebody133.yaml` (written, `rtmw/identity.py:35-36`) |
| the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) | F1 (`:95`) | `vitposepp-wholebody` | `vitposepp-wholebody133` (planned) |
| same | L1 (`:180`) | `<export root>/detectors/keypoint_detectors/vitposepp/wholebody/vitposepp-wholebody.yaml` | `.../vitposepp/wholebody133/vitposepp-wholebody133.yaml` (planned) |
| the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts) | L1 (`:178`) | `<export root>/detectors/keypoint_detectors/rtmpose/body/<F1 model_id>.yaml` | `.../rtmpose/halpe26/rtmpose-halpe26.yaml` (planned) |
| the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts) | L1 (`:187`) | `<export root>/detectors/keypoint_detectors/vitpose/body/<model_id>.yaml` | `.../vitpose/coco25/vitpose-coco25.yaml` (planned) |
| the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts) | L1 (`:158`) | `<export root>/detectors/keypoint_detectors/dwpose/wholebody/<F1 model_id>.yaml` | `.../dwpose/wholebody133/dwpose-wholebody133-ubody.yaml` (planned) |

The template rule for L1: "A model-specific folder ... does not conform. If the exporter writes to
such a folder, the sidecar value is still the spec path. Write the path of the exporter in the last
column as an exporter defect. The verdict of row L1 stays `exact`." (skellytracker
`specs/model-sidecar/templates/model-intake.md:358-360`, `dom/18-agents-adr-bootstrap-kit`). The keypoint folder of this proposal
is such a folder under the current text. Row F1 is `exact` when no other model of the same family
and part needs the `{family}-{part}` id (`model-intake.md:229`; `exporter-guide/sidecars/workflow/mapping-hints.md:13-26`). If the
user rejects this proposal, the writers must go back to the current form for these rows. The row L1
of `rtmo-coco17-body7` stays a `gap` (header), and this proposal does not change it.

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change: `{family}-{part}` only (the current text) | Two models of one family and one part get one id, one file name and one catalog key. | Part 1 |
| `{family}-{part}` or `{family}-{part}-{variant}`, in `{family}/{part}/` (the first form of this proposal; superseded by user decision T14, 2026-10-23) | The part does not name the keypoint output: the `body` folder holds 17, 25 and 26 points. The variant then had to carry two kinds of fact, the keypoint set (`rtmpose-body-halpe26`, `vitpose-body-coco25`) and the training set (`rtmo-body-body7`). The user chose the keypoint output as the second token, so that the folder tells the output and the third token tells only the training set. The rule for the variant had three options. A, "bare id first": the model with the default keypoint set of the part takes `{family}-{part}`; a training set alone is not a reason for a variant. B, "variant when upstream has several": each model of a family and part with upstream siblings takes a variant. C, "no rule": the grammar only, so one model can have two valid ids. The user chose B with a default model (plan T10, same day), then T14 kept that idea (a bare id for the default model, a third token for each sibling) and changed the second token. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) T6, T10, T14 (plan facts); OpenMMLab-Exporter decision 0039 (`d0f4343`) replaces the earlier form `rtmo-body-body7`, which was never committed (`0039-keypoint-model-id-format.md:72-74`) |
| A new family for each model (for example `rtmpose26-body`) | The family folder then names a keypoint set, not a model family. The reader cannot see that `rtmpose26` is an RTMPose model. Under T14 the keypoint output is in the id, so a new family is not necessary for a new output. | 2.3 ("Added guidance", "A new family token"); skellytracker `0025-model-id-suffix.md:16` leaves the choice to the full proposal |
| A suffix with no hyphen (`rtmo-body7`, the reference example) | The id cannot show where the second token ends, and `body7` is not a keypoint output. | Reference example `rtmo/body/rtmo-body7.yaml:6` (`model_id: rtmo-body7`); skellytracker decision 0025 cites line 3 (`0025-model-id-suffix.md:39`), but the line is 6 |
| The order `{family}-{training}-{keypoints}` (for example `rtmo-body7-coco17`) | The id then does not start with the folder pair `{family}/{keypoints}`. skellytracker decision 0025 gives the direction "the id starts with" the folder pair (`0025-model-id-suffix.md:11-12`). T14 rule 4 says the same. | skellytracker `0025-model-id-suffix.md:11-12`; T14 |
| A separate `training` or `variant` field next to `model_id` | `V-common.identity-1` and the catalog key use `model_id` alone, so the field would not separate the two files. | `identity.md:36`, `:59` |
| A grammar check on the id alone, with no folder | A family token, a keypoint token and a training token can look the same (`yolo26`, `coco17`, `body7`, `h36m17` all match the keypoint pattern). The family-part rule of `V-common.identity-7` gives each id one valid folder pair, but a check of the id alone cannot find a sidecar in the wrong folder. The folders are the location that a host reads, so the rule compares the id with them. | Vectors `family-like-keypoints`, `training-like-keypoints`, `family-part-like-keypoints` |
| No family-part rule; a catalog rule in its place: one `<model_id>@<source.name>` key must come from one folder pair | Without the family-part rule, `rtmo-coco17-body7` is valid in `rtmo/coco17/` and in `rtmo-coco17/body7/`. A catalog rule finds the clash only when both files are in one catalog. The family-part rule rejects the second file alone, and no family in use or in plan has a hyphen part that matches the keypoint pattern. | 2.3, "The family parts"; `identity.md:59` |
| A family token with no hyphen (`^[a-z0-9]+$`) | It also prevents the two folder pairs, but it is stricter than the family-part rule, and the current pattern of the family allows hyphens. The family-part rule keeps the hyphen for a two-token family name. | Vector `hyphen-in-family` |
| "The same keypoint output" defined as the same ordered list of points | Two models of one family with one set in two orders then have two outputs. Rule 3 gives each one the bare id, so the two files get one name in one folder. The definition by the keypoint token (set name and count) has no such case. | 2.3, "Added guidance" |
| Keep the old example files as legacy copies, so that the decision-entry links resolve | The three files have `schema_version: "vNEXT"` in part folders, so they fail `V-common.identity-7` and the new `test_example_follows_the_storage_layout`. | 2.1, the `tools/tests/test_links.py` row |
| An exemption in `tools/check_links.py` for links from decision entries | It hides real broken links in decision entries, and it changes a tool for four lines. | `check_links.py:107-113` |
| The keypoint pattern `^[a-z](?:[a-z0-9]*[a-z])?[1-9][0-9]*$` (the name starts with a letter) | It rejects the mmpose face set `300w` (68 points). Both patterns give the same parse for every token that both accept. | `configs/_base_/datasets/300w.py:2`, `:129` (mmpose v1.3.2) |
| A separator in the keypoint token (`coco-17`, `coco_17`) | A hyphen is the token separator of the id. An underscore is not in the pattern of the other tokens. The T14 examples have no separator. | T14; `identity.md:27` (the token pattern) |
| A training token with no hyphen (`^[a-z0-9]+$`) | No id in scope needs a hyphen in the training token: the ids of 2.3 use `ubody` and `body7`. But upstream training names can have hyphens (`coco-ubody`, `body7-crowdpose`), so the hyphen is kept for future names. For two given folders, a hyphen gives no second parse. | 2.3, "The training pattern" |
| A third token for two models with the same keypoint output and the same training set (for example `mediapipe-<set>478-holistic` and `mediapipe-<set>478-landmarker`) | The user chose two sizes of one sidecar (Q2, 2026-10-23). The family invariant allows it when the two models differ only in `input.shape`, `input.resize.target_size` and the ONNX artifacts. A third token then names a bundle, not a training set, against rule 2. | `common/sizes-and-artifacts.md:35`, `:101`; skellytracker `0010-family-invariant.md:7-18`; 2.3, Q2 |
| A training token for a family with one model of a keypoint output that does not train on the reference dataset (for example `rtmw-wholebody133-cocktail14`) | Rule 3 gives the token only when the family has more than one model with that output. The user confirmed this reading for RTMW (Q4, 2026-10-23). | OpenMMLab-Exporter `notes/decisions/0039-keypoint-model-id-format.md:18-20`, `:32` (`d0f4343`); 2.3, Q4 |
| Define the reference dataset of `hand21` and of the face sets now | No model in scope needs it. The user chose to leave it undefined until a model needs it (Q3, 2026-10-23). | 2.3, Q3 |
| A `{keypoints}` placeholder token for a model with no keypoint output (for example `mediapipe-roi1`) | It describes an ROI refiner as a keypoint model, which the exporter guide forbids. The ROI-refiner proposal gives the refiner its own role, folder and id (Q1, answered). | `exporter-guide/sidecars/rules.md:6-8`; skellytracker `0020-roi-transform-and-source.md:21-22`; MediaPipe-Exporter `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` |
| No count rule (no `V-common.identity-9`) | The folder count could then disagree with the model: `rtmo/coco17/` could hold a 26-point model. The spec has the list for the check. | `pose-schema.md:39`, `:60`, `:117` |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. (Row F1 has the verdict `gap` in the intakes of Halpe26,
  ViTPose 25 points, DWPose and RTMO, and row L1 only in the RTMO intake. Row L1 of the other intakes
  and row F1 of ViTPose++ and RTMW are `exact` with an exporter departure (part 7). Each row links
  this proposal, also in "Proposals and reference files":
  the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts);
  the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts);
  the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts); the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts); the untracked intake of `rtmo-coco17-body7` of OpenMMLab-Exporter (plan facts), added by the review-readiness audit 2, 2026-10-24. All lines checked again on 2026-10-25.)
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
  `none`. This proposal builds on skellytracker 0025, and it names the effect on skellytracker 0017.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. (The RTMO and
  DWPose config paths are paths of the mmpose v1.3.2 git tree, read from the GitHub tree API, not
  truncated.)
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plan folder of OpenMMLab-Exporter.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a (no pixel case)
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
  script. n/a (`none`, a name)
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
  repo. n/a
- [x] No file in skellytracker changed.
- [x] The user decides plan O6a (the DWPose id): `dwpose-wholebody133-ubody` (plan T15). The DWPose row of 2.3 and part 7 are updated.
- [x] The user confirms the derived id `yolo26-coco17` (M1, plan T23, 2026-10-24; 2.1, part 7). It
  is not in the T14 scope list. The Ultralytics-Exporter code still writes `yolo26-body`
  (`yolo_sidecar.py:22-25`, `f52ef68`, HEAD `2e0280e`) at the legacy `schema_version`
  `v2024.09.1019`. Part 7 expects `yolo26-coco17` when it writes `vNEXT`.
- [x] The user accepts that this proposal asks for the three proposal choices that change
  skellytracker rules or tools (M2, plan T22 (4) and T23, 2026-10-24): the link-only edit of four
  decision-entry links (an exception to `notes/decisions/README.md:216` at `dom/12-single-working-branch`; moot at `dom/18-agents-adr-bootstrap-kit`, 2.1), the test-tool changes
  (the `function` case key in `tools/tests/test_vectors.py`), and the new allowed forecast edit of
  `inventory.yaml` (2.1). This exporter never edits skellytracker. The proposal only describes the
  edits that it wants a skellytracker session to make. The skellytracker session still decides on
  each edit under its own rules.
- [x] The user confirms the choices of 2.3 that are not in T14: the family-part rule, the ASCII
  classes, the terms "family token" and "sidecar", and the "Added guidance" block. (User, 2026-10-24:
  all four accepted as written; OpenMMLab-Exporter plan T42.)
- [x] The user answers Q2, Q3 and Q4 (2026-10-23): Q2, two models with the same keypoint output and
  the same training set are two sizes of one sidecar when the family invariant holds; Q3, the
  reference dataset of `hand21` and of the face sets stays undefined until a model needs it; Q4, the
  RTMW reading of rule 3 is correct. 2.3, 2.4, 2.6, part 7 and part 8 have the answers.
- [x] The user answers Q1 (a pipeline stage, such as the MediaPipe hand re-crop model): user decision
  Q3 = (a) of MediaPipe-Exporter `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` (2026-10-23; plan T20):
  `detectors/roi_refiners/{family}/{part}/` with `{family}-{part}-roi[-{variant}]` (2.3, Q1).
- [x] OpenMMLab-Exporter commits OpenMMLab-Exporter decision 0039 and the T14 code: `d0f4343` (2026-10-23, not
  pushed). The header, 2.3, part 3, the `unverified` line of part 4, part 5, part 7 and part 8 cite
  the commit. The line numbers of the header were checked again at `f3aeb47` (OpenMMLab-Exporter decision 0042 is
  commit `1dfec48`) on 2026-10-24.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal. A skellytracker
session checked each item against the proposal text and the files on 2026-10-25.

**Parts**

- [ ] Part 2.1, the row of the reference examples, must say if the artifact filenames of the YOLO26
  pose forecast change. The example has `yolo26-body-nano_b1_fp32.onnx` and eight more files of this
  form. The proposed third allowed edit of `inventory.yaml` covers only the `model_id` and the folder.
- [ ] Part 2.1 must give a source for the moved RTMW example. The row says to use a regenerated
  OpenMMLab-Exporter sidecar. OpenMMLab-Exporter 0050 writes no RTMW or RTMO sidecar while the intake
  of the family is not `describes`. Thus no regenerated RTMW sidecar exists.
- [ ] Part 2.1, the row `tools/tests/test_links.py`, proposes GitHub links that pin the commit of the
  branch `dom/12-single-working-branch`. That commit is not on `development` or `main` of
  skellytracker. A permalink must pin a full SHA on the default branch
  ([0032](../../../../decisions/0032-entry-numbers-and-edits.md)). The proposal must give a
  different repair.
- [ ] The header and part 7 say that the OpenMMLab-Exporter branch `rtmo-model-id-variant` is "not
  pushed". The commits `d0f4343` to `f3aeb47` are now on `main` of the OpenMMLab-Exporter fork. The
  exporter must correct this text. It can then cite these commits with permalinks.

**Evidence**

- [ ] The mmpose v1.3.2 config paths (RTMO `coco`, `body7` and `crowdpose`; DWPose `coco-wholebody`
  and `ubody`; RTMPose `cocktail14` and `hand5`) come from the GitHub tree API. No tracked file
  records this listing. A reviewer must check the paths against the mmpose tag `v1.3.2`.
- [ ] The MediaPipe facts (the face landmark models of 192 px and 256 px, their input tensor names and
  the output `tongue_out`) come only from untracked MediaPipe-Exporter plans (plan facts).
  MediaPipe-Exporter has no git repo. MediaPipe-Exporter and Qualcomm-Exporter must confirm the ids
  `mediapipe-hand21` and `mediapipe-<set>478`.
- [ ] No host code implements the reference functions, so the vectors are `unverified`. The run of 84
  of 84 cases used an uncommitted script. That run is not evidence. The planned OpenMMLab-Exporter test
  `tests/test_sidecar_identity.py` does not exist at `f3aeb47`.
- [ ] OpenMMLab-Exporter 0039 records T14 and the RTMW reading of Q4. The other user decisions that
  the proposal applies (Q1 to Q3, T11, T15, T21 (1), T42, M1 and M2) are only in the untracked
  pose-models plan of OpenMMLab-Exporter (plan facts). The user must confirm them, or the exporter
  must record them in tracked entries.

**Template checklist**

- [ ] The item "Part 2.1 lists each place that the change edits" fails. Part 2.1 does not list these
  places:
  - `.claude/skills/author-sidecar/SKILL.md:61`: "One file for each family. `<model>` is the
    `model_id` of the family". Part 2.1 changes the same words in the exporter guide and in
    `model-intake.md:21`.
  - `.claude/skills/author-sidecar/SKILL.md:170` and `specs/model-sidecar/templates/model-intake.md:358-360`:
    "a model-specific folder such as `rtmo/body7/`". Under the new keypoint pattern, `body7` is a
    valid keypoint token (name `body`, count 7). Part 2.1 rewords the same sentence only in
    `sidecar-files.md:48-50`.
  - `specs/model-sidecar/format/file-layout.md:141-142`: the ONNX name examples `rtmw-wholebody-m_b3_fp32`
    and `rtmw-wholebody-x-384_b1_fp16`.
  - `specs/model-sidecar/changelog.md:31`, row 14 of the summary of changes. It says that RTMW and RTMO
    body7 come from real `vNEXT` exports. After the move, this is not true.
  - `specs/sidecar-implementation-plan.md`, "Reference examples", steps 1 and 7. Step 1 requires a
    sidecar that the exporter writes, with a parity check that passes. Step 7 requires a
    documentation-only PR. The proposal moves the examples in the content PR.
  - `specs/model-sidecar/decisions/0017-dual-role-sidecar-folder.md:25-26`: "The proposed rule moves no exporter
    output and no example". This sentence becomes false.

**Vectors and tooling**

- [ ] Each case has the key `function`. `CASE_KEYS` of `tools/tests/test_vectors.py` has no
  `function` key, and the `Case` class of `tools/make_vectors.py` has no `function` field. Decide the
  case form one time for all proposals.
- [ ] `generated_by` must be `tools/make_vectors.py`. The port needs a `common.identity` builder in
  `BUILDERS`.
- [ ] `clean` of `tools/make_vectors.py` changes a whole float to an int in `input`. The case
  `count-float` (`17.0`) then becomes `17`, and the reference returns `true` against
  `expect: {valid: false}`. The tool or the case must change.
- [ ] `tools/make_vectors.py` writes a string that is not plain with `json.dumps`, so the generated
  file holds ASCII escapes for the characters `７` and `ö`. The note of part 4 "The YAML file must be
  UTF-8" then applies only to the block in this file.
- [ ] `test_file_is_small` requires each vector file to be smaller than 16 KiB. A render of the 84
  cases is approximately 15.6 KB (95%). The role vectors of `roi-refiner-role` can make it larger.
- [ ] The docstring of the reference code cites the proposal and skellytracker branches, not tracked
  commits on `development`. Change these notes before the code goes to
  `specs/model-sidecar/reference/common_identity.py`.

**Decisions for the user**

- [ ] Accept this proposal as the completion of gap record 0025, or not. Its direction differs from
  0025: the second token is the keypoint output, not the part. Decide if the title of 0025 changes.
- [ ] Decide which files outside `specs/` the content PR can change: `tools/make_vectors.py`,
  `tools/tests/test_vectors.py`, `tools/tests/test_examples.py`, `tools/tests/test_traceability.py`,
  `tools/tests/test_sidecar_trace.py`, `.claude/skills/author-sidecar/SKILL.md` and the entries 0017,
  0018 and 0025.
- [ ] Decide how to repair the links to the old example files in 0017 (lines 41 and 43), 0018
  (line 33) and the Evidence of 0025. These links break when the examples move.
- [ ] Decide the sources of the moved examples. RTMO: OpenMMLab-Exporter
  `notes/decisions/rtmo-coco17-body7.yaml`, and at which commit. RTMW: no regenerated export exists.
  YOLO26 pose: a new allowed edit of `inventory.yaml`. The OpenMMLab-Exporter plan defers RTMO from
  this round (T29). Decide if RTMO stays in scope.
- [ ] Decide if the procedure "Reference examples" of `specs/sidecar-implementation-plan.md`
  applies to the moved examples. Its step 1 requires a sidecar that the exporter writes. Its step 7
  requires a documentation-only PR on a branch `dom/sidecar-example-<model>`. The proposal moves
  the examples in the content PR, and the stack branches are `dom/NN-<topic>`.
- [ ] Decide which section owns `V-common.identity-8`. It is a check of the sidecars of one folder (a
  catalog check). Decision 0013 gives one owner for each rule.
- [ ] Decide if the content PR keeps `common.identity` and the storage layout of `format.file_layout`
  in one contract unit, or splits them.
- [ ] Decide where the id table of part 2.3 goes. Some of its ids are plan facts, or wait for a
  confirmation by MediaPipe-Exporter or Qualcomm-Exporter.
- [ ] Decide if the change from `{part}` to `{keypoints}` goes into 0017 now. The RTMO row L1 (the
  folder of a sidecar with both roles) still has no proposal.
- [ ] Decide when the 0025 item of the open work closes. The proposal ties it to the acceptance of
  this proposal and of `roi-refiner-role`.
- [ ] Decide if `decisions/scripts/check_split_verbatim.py` must pass against the current tree after the
  "Sidecar:" links of `examples/README.md` change.
- [ ] Decide one rule for the link of a new "Legacy behaviour" heading in "Version-aware
  compatibility". This proposal adds the link for `format.file_layout`. Some other proposals do not
  add a link for their new heading.

**Merge points**

- [ ] `roi-refiner-role` ([0047](../../decisions/0047-roi-refiner-role.md)) adds the role
  `roi_refiner` to `V-common.identity-2`. The reference code of this proposal (`ROLES`, `check_role`)
  and the vectors `role-one`, `role-both` and `role-unknown` know two roles only. Neither proposal
  lists this merge point. The second content PR must update the reference code and the vectors.
- [ ] `size-codes` ([0046](../../decisions/0046-size-codes.md)) uses the ids of this
  proposal in its storage-layout examples and in its note on `V-common.identity-8`. Land this
  proposal first (soft order).
- [ ] `pose-decode-flip-test` ([0045](../../decisions/0045-pose-decode-flip-test.md))
  uses the ids `rtmpose-halpe26` and `dwpose-wholebody133-ubody` in its part 7 only (soft order).
- [ ] `roi-transform-and-source` ([0020](../../decisions/0020-roi-transform-and-source.md))
  changes the three examples that this proposal moves (`requires_object_detector`). `size-codes`
  changes the sizes of the YOLO26 pose example. Change each example one time, in the landing order.
- [ ] Text merges with other proposals: "Version-aware compatibility" of `format/versioning.md`
  (`affine-crop-arithmetic`, `simcc-score-rule`, `heatmap-decode-refinement`, `size-codes`,
  `roi-transform-and-source`); `common/identity.md` (`roi-refiner-role`, `size-codes`); the storage
  tree and the authoring guidance of `format/file-layout.md` (`roi-refiner-role`, `size-codes`);
  `common/sizes-and-artifacts.md` (`roi-transform-and-source`, `size-codes`, `roi-refiner-role`);
  the RTMW excerpt of `format/composition.md` (`roi-transform-and-source`); and `changelog.md` (all
  13 proposals). The second content PR keeps the edits of both.
- [ ] The text of `roi-refiner-role` cites lines 40-44 of 0025. The completion of 0025 moves these
  lines.
