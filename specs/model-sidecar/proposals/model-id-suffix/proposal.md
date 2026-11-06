# Change proposal: model-id-suffix

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | A keypoint group and a variant suffix in the `model_id` of a keypoint detector |
| Slug | `model-id-suffix` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `c2e610e91fee0a961032e12737ff9147697a7e53` |
| Model, and its `model` bundle ID | `rtmw-wholebody133`, `model-rtmw-wholebody133@openmmlab-exporter` |
| Intake rows with the verdict `near-miss` or `gap` | None. Rows F1 (`model_id`) and L1 (sidecar path) of the RTMW intake are `exact` under the current text, with an exporter departure in the last column: the exporter writes `rtmw-wholebody133` in `detectors/keypoint_detectors/rtmw/wholebody133/`. The user asked for this proposal on 2026-11-06, so that the spec allows the exporter value (part 1, plan decisions). |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `common.identity` (primary); `format.file_layout` (second) |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/common/identity.md`; `specs/model-sidecar/format/file-layout.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of the spec log has skellytracker ADR-3S5G (`pre.resize.affine_person_crop`) and skellytracker ADR-50BW (`common.batch_conversion`). Neither covers `common.identity` or `format.file_layout`. The Proposed table of the root log is empty. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `b065f6e6850686b65bcd08ca944116d739aa62de` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | The `model_id` and the folder of a keypoint detector when one family has more than one keypoint model for one body region. The OpenMMLab-Exporter form is `{family}-{keypoints}[-{training}]` in the folder `{family}/{keypoints}/`. `{keypoints}` is a keypoint set with its point count, for example `wholebody133` or `coco17`. The ids are `rtmw-wholebody133` in `rtmw/wholebody133/` and `rtmo-coco17-body7` in `rtmo/coco17/`. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | A `model_id` is a value that the exporter chooses. It has no upstream evidence ("Rules" in `specs/model-sidecar/model-addition-workflow/rules.md`). The code that writes the values: OpenMMLab-Exporter [`rtmw/identity.py:33-36`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/rtmw/identity.py#L33-L36) and [`rtmo/identity.py:39-42`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/rtmo/identity.py#L39-L42). The upstream fact that makes a part token too small: one family has two keypoint outputs for one body region. mmpose v1.3.2 (`5408bc76f5b848cf925a0d1857899011d8c5b497`, tag `v1.3.2`) has RTMPose body models with 17 points ([`configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb256-420e_body8-256x192.py:77`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb256-420e_body8-256x192.py#L77)) and with 26 points ([`configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py:4`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py#L4)). RTMO has two COCO-17 model lines with different training sets ([`configs/body_2d_keypoint/rtmo/coco/rtmo-m_16xb16-600e_coco-640x640.py:255`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmo/coco/rtmo-m_16xb16-600e_coco-640x640.py#L255) and [`configs/body_2d_keypoint/rtmo/body7/rtmo-m_16xb16-600e_body7-640x640.py:467`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/body_2d_keypoint/rtmo/body7/rtmo-m_16xb16-600e_body7-640x640.py#L467)). |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | (1) The user decided on 2026-11-06 that the RTMW intake needs a proposal for the `model_id`: the spec gets a grammar with a variant suffix, and the exporter does not rename `rtmw-wholebody133`. (2) The exporter grammar and its ids are an exporter decision of the user: [OpenMMLab-Exporter ADR-0039](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0039-keypoint-model-id-format.md). |
| Nearest section ID (the `id` in the section file's front matter) | `common.identity` (the `model_id` row of Fields); `format.file_layout` (Storage layout) |
| Why the nearest section is wrong | The text gives `{family}-{part}` for a keypoint detector and the folder `{family}/{part}/` with the parts `hand`, `face`, `body` and `wholebody`. (1) It cannot express a suffix after the part. The spec itself names this defect: "Spec defects" item 1 of `specs/model-sidecar/decisions/open-work.md`. The reference example `rtmo-body7` in the `body` folder does not follow the text. (2) It has no id for a second model of one family and one part ("Rules" in `rules.md`, row F1). RTMPose COCO-17 and RTMPose Halpe-26 both get `rtmpose-body`. (3) A part does not tell the keypoint output. `rtmw-wholebody` does not say 133 points. |
| Measured difference (number, image and script) | A name changes no tensor and no decoded output. Count of the current reference examples that the text cannot express: 1 of 5 (`rtmo-body7`). |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes (OpenMMLab-Exporter: RTMW) |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none |

## 2. Spec change

The relative links of the proposed text resolve from the record path `specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the section file (an editorial fix).

The quoted text writes the name of the new heading "Keypoint detector id" as text, not as a link. A link to a heading that this proposal adds does not resolve at the current text (skellytracker ADR-730P). At landing, the session makes each such name a link to `common/identity.md#keypoint-detector-id` (an editorial fix).

### 2.1 Sections

Changed section `common.identity`, title "Identity", file `specs/model-sidecar/common/identity.md`.
Changed section `format.file_layout`, title "File layout", file `specs/model-sidecar/format/file-layout.md`.
The section IDs, the titles, the kinds and the selectors do not change. No section-map row changes.

**Places that the change edits.** The line numbers are at the skellytracker commit of the header.
A row with "No edit" names a place that has an affected value and stays valid.

| Place | Heading | Edit |
|---|---|---|
| `common.identity` | front matter, the comment of `implemented_by.validate` (line 7) | The comment names only `V-common.identity-1` to `V-common.identity-6`. After "No code checks V-common.identity-4 to V-common.identity-6: SidecarModel forbids the key source.", add "No code checks V-common.identity-7 or V-common.identity-8." |
| `common.identity` | front matter, `vectors` (line 13) | Replace `vectors: null` with `vectors: vectors/common.identity.yaml` (the file of part 4). |
| `common.identity` | Fields, row `model_id` (line 27) | Replace the description with the text of 2.2. |
| `common.identity` | new heading "Keypoint detector id", after Fields | Add the text of 2.3. |
| `common.identity` | Validation rules (lines 34-39) | Add `V-common.identity-7` and `V-common.identity-8` (2.4). |
| `common.identity` | Implementer guidance, the catalog key example `rtmw-wholebody@openmmlab-exporter` (line 49) | No edit. `rtmw-wholebody` stays valid (a part group). |
| `common.identity` | Authoring guidance, first bullet (line 59) | Replace "Write the family id as `model_id`." with "Write the family id as the `model_id` of an object detector. For a keypoint detector, write `{family}-{group}` or `{family}-{group}-{variant}` (heading "Keypoint detector id")." In the values in use, replace `rtmw-wholebody` with `rtmw-wholebody133` and `rtmo-body7` with `rtmo-coco17-body7`: these are the ids that OpenMMLab-Exporter writes now. After the list, add "The reference examples `rtmw-wholebody` and `rtmo-body7` have older OpenMMLab-Exporter ids. The re-export request rebuilds them." Replace the citations `rtmw/identity.py:25-28` and `rtmo/identity.py:24-27` at `eed3361aa31e02df160c33a18a3db9ba182b5551` with `rtmw/identity.py:33-36` and `rtmo/identity.py:39-42` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. |
| `common.identity` | Authoring guidance, the bullet "OpenMMLab-Exporter writes the id `rtmo-body7`, with a suffix after the part. ..." (line 63) | Replace the bullet with: "OpenMMLab-Exporter writes `rtmw-wholebody133` in `rtmw/wholebody133/` and `rtmo-coco17-body7` in `rtmo/coco17/`. The group is a keypoint set. `body7` is the variant: the training set of the second RTMO COCO-17 model line. `body7` is not a group: it is not a part, and 7 is not the keypoint count 17 (`V-common.identity-8`). The MediaPipe-Exporter plan names `mediapipe-hand-landmark` and `mediapipe-hand-recrop`: the group `hand` with the variants `landmark` and `recrop`." Cite OpenMMLab-Exporter `rtmw/identity.py:33-36` and `rtmo/identity.py:39-42` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. Keep the citation of the MediaPipe-Exporter plan (secondary). |
| `format.file_layout` | front matter, the comment of `implemented_by.validate` (line 7) | No edit. The comment says that no code checks the folder layout. This is also true for the new rules. |
| `format.file_layout` | Behaviour, "File extension and naming", the example `rtmw-wholebody-l-m_fp32.onnx` (line 28) | No edit. The ONNX name rule does not change, and `rtmw-wholebody` stays valid (a part group). |
| `format.file_layout` | Storage layout, the tree (lines 42-67) and the table row of `detectors/keypoint_detectors/{family}/{part}/` (line 73) | Replace `{part}` with `{group}`. In the tree, add the line `{keypoint set}/   # for example wholebody133, coco17` under `keypoint_detectors/{family}/`. Replace the table row with the row of 2.3. |
| `format.file_layout` | Storage layout, the example tree `detectors/keypoint_detectors/rtmw/wholebody/` (lines 83-86) | No edit. `rtmw-wholebody` in `rtmw/wholebody/` stays valid (a part group). |
| `format.file_layout` | Validation rules (line 117) | Add a link to `V-common.identity-7` and `V-common.identity-8`. |
| `format.file_layout` | Authoring guidance, the sub-bullet "OpenMMLab-Exporter writes `detectors/keypoint_detectors/rtmw/wholebody/` and `detectors/object_detectors/rtmdet-person/`." (line 134) | Replace `detectors/keypoint_detectors/rtmw/wholebody/` with `detectors/keypoint_detectors/rtmw/wholebody133/`. Replace the citation `tests/test_rtmw.py:73-77` at `ba0c0876b58650ed472559f1a77780e5da13d370` with `tests/test_rtmw.py:78` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. |
| `format.file_layout` | Authoring guidance, the ONNX name examples `rtmw-wholebody-m_b3_fp32` and `rtmw-wholebody-x-384_b1_fp16` (line 138) | Replace them with `rtmw-wholebody133-m_b3_fp32` and `rtmw-wholebody133-x-384_b1_fp16`. Replace the citation `tests/test_rtmw.py:73-77` at `ba0c0876b58650ed472559f1a77780e5da13d370` with `tests/test_rtmw.py:79-80` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. The ONNX name rule does not change. |
| `format.file_layout` | Authoring guidance, the `schema_version` sub-bullet with the local export `rtmw/wholebody/rtmw-wholebody.yaml:2` (line 150) | No edit. The item is about the quotes of `schema_version`, not about the id. |
| `format.file_layout` | Authoring guidance, the bullet "The folder of two kinds of sidecar does not follow the Storage layout." and its first sub-bullet "OpenMMLab-Exporter writes RTMO to `detectors/keypoint_detectors/rtmo/body7/`. ... Write the RTMO sidecar to the `body` part folder." (lines 151-152) | In the bullet, replace "two kinds of sidecar" with "a sidecar with both roles". Remove the first sub-bullet: OpenMMLab-Exporter writes RTMO to `rtmo/coco17/`, a keypoint-set group, and the Identity Authoring guidance tells why `body7` is not a group. Keep the sub-bullet on the folder of a sidecar with both roles (line 153). |
| `specs/model-sidecar/README.md` | Section map; validation index | No edit. The rows of both sections exist. |
| `specs/model-sidecar/changelog.md` | Summary of changes | Add the row of 2.6. |
| `specs/model-sidecar/decisions/open-work.md` | Re-export requests, "Rebuild of each example" (line 20) | No edit. The item names the current examples by their keys (`rtmw-wholebody`, `rtmo-body7`). Part 7 gives the new id of the RTMO rebuild. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, item 1, the `{family}-{part}` item (lines 39-44) | The content commit removes the item. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item on a sidecar with both roles (lines 63-70) | The item names `rtmo/body7/`. Replace "OpenMMLab-Exporter uses `rtmo/body7/`", with its citation of `rtmo/identity.py:27` at `eed3361aa31e02df160c33a18a3db9ba182b5551`, and the sentence "`body7` is not a part folder", with its link to the file-layout Authoring guidance, with: "OpenMMLab-Exporter uses `rtmo/coco17/`", with a citation of OpenMMLab-Exporter `rtmo/identity.py:42` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. The item stays open: this change does not choose the branch of a sidecar with both roles. |
| `specs/model-sidecar/vectors/common.identity.yaml` | new file | The data-only cases of part 4. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` | example | Breaks `V-common.identity-7` (part 7). |

The rules keep both `V-common.identity-7` and `V-common.identity-8` unchanged (a user decision).

The workflow files repeat the current rule: "Identity" in `model-addition-workflow/mapping-hints.md`,
rows F1 and L1 of `templates/model-intake.md` and the paragraph on a model-specific folder under them,
the path list of "Path" in `model-addition-workflow/sidecar-files.md` and its paragraphs on both
roles and on the folder `body7`, step 3 "Path" of "How to provide or replace an example" in
`model-addition-workflow/reference-examples.md`, step 5 of the skill `author-sidecar`
(`.claude/skills/author-sidecar/SKILL.md`), and the sentence on row F1 in "Rules" of
`model-addition-workflow/rules.md`. This bundle does not change them (heading "Workflow changes" in
`hand-over.md`). The skellytracker session that lands the change updates these copies.

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `model_id` | string | yes | The model identifier. It matches the sidecar basename. For an object detector, it is the family, for example `yolo26`. For a keypoint detector, it is `{family}-{group}` or `{family}-{group}-{variant}`, for example `rtmw-wholebody`, `rtmw-wholebody133` or `rtmo-coco17-body7` (see "Keypoint detector id"). |

### 2.3 Behaviour

New heading "Keypoint detector id" in `common/identity.md`:

```text
model_id  = {family}-{group}
          | {family}-{group}-{variant}
{family}  = ^[a-z0-9]+(-[a-z0-9]+)*$        the family id, for example rtmw, rtmo or yolo26
{group}   = hand | face | body | wholebody  a body region
          | ^[a-z]+[1-9][0-9]*$             a keypoint set: a set name and its keypoint count,
                                            for example wholebody133, coco17, halpe26 or hand21
{variant} = ^[a-z0-9]+(-[a-z0-9]+)*$        one or more tokens, with one - between two tokens
```

- The sidecar of a keypoint detector is `detectors/keypoint_detectors/{family}/{group}/{model_id}.yaml`
  (see [Storage layout](../../format/file-layout.md#storage-layout)). The folder gives `{family}` and
  `{group}`. The `model_id` starts with `{family}-{group}`.
- The number of a keypoint set is the keypoint count `K` of the model: `len(pose.tracked_points)`.
- `{variant}` separates two models of one family with the same group. Examples are a training set
  (`body7`) and a stage of a pipeline (`landmark`). The sidecar basename separates the two sidecars
  in one folder (`V-common.identity-1`).
- A family id can contain `-`, so the `model_id` alone does not give its tokens. The folder gives
  them.
- The ONNX file names, the catalog key `<model_id>@<source.name>` and the discovery rule do not
  change.
- This heading does not choose the branch of a sidecar with both roles. That is a separate spec
  defect of the storage layout.

New table row of "Storage layout" in `format/file-layout.md`:

| Branch | Role | Contents |
|--------|------|----------|
| `detectors/keypoint_detectors/{family}/{group}/` | `pose_estimator` | Keypoint models. `{group}` is a body region (`hand`, `face`, `body`, `wholebody`) or a keypoint set with its keypoint count (for example `wholebody133`). Each sidecar in the folder has the `model_id` `{family}-{group}` or `{family}-{group}-{variant}` ("Keypoint detector id" in [Identity](../../common/identity.md)). |

The change has no forward algorithm and no inverse.

### 2.4 Validation rules

- [ ] `V-common.identity-7` A sidecar in `detectors/keypoint_detectors/{family}/{group}/` must have the `model_id` `{family}-{group}`, or `{family}-{group}-{variant}`. `{family}` and `{variant}` must match `^[a-z0-9]+(-[a-z0-9]+)*$`.
- [ ] `V-common.identity-8` The `{group}` folder of a sidecar in `detectors/keypoint_detectors/` must be `hand`, `face`, `body` or `wholebody`, or match `^[a-z]+[1-9][0-9]*$`. The number of such a group must equal `len(pose.tracked_points)`.

Existing rules that name the changed values:

- `V-common.identity-1` (the basename equals `model_id`): unchanged. The new rules add the folder.
- `V-common.identity-2` to `V-common.identity-6`: unchanged. They do not name `model_id` or a folder.

### 2.5 Selectors

The two rules apply to each sidecar in the branch `detectors/keypoint_detectors/`. The section
`common.identity` has no selectors (`selectors: []`), and this does not change.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Identity | The `model_id` of a keypoint detector is `{family}-{group}` or `{family}-{group}-{variant}`. `{group}` is a body region or a keypoint set with its keypoint count (`wholebody133`). The folder is `keypoint_detectors/{family}/{group}/`. New rules `V-common.identity-7` and `V-common.identity-8`. | RTMW (`rtmw-wholebody133`), RTMO body7 (`rtmo-coco17-body7`) | [Identity](../../common/identity.md) |

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | none. `common.identity` and `format.file_layout` have no algorithm ("When to do the step" in `model-addition-workflow/reference-implementations.md`). The two new rules are validation rules. Part 4 gives their cases as data-only validator cases. |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | none |
| Functions (one for each algorithm) | none |

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/common.identity.yaml` (data-only validator cases, `function: none`) |
| Target file in skellytracker | `specs/model-sidecar/vectors/common.identity.yaml` (new file) |
| `verified_against` | `unverified`: no validator implements `V-common.identity-7` or `V-common.identity-8` yet. |
| Replaced case ids (`--replaces`) | none (new file) |

Each case gives `input.path` (the path of the sidecar under its sidecar root) and `input.sidecar`
(only the blocks that the rules read). The cases cover each branch: a part group, a keypoint-set
group, a variant, a variant with no `-`, a count that does not match, an id that does not start with
the folder, a family folder that does not match, a group that is neither form, and an object
detector.

## 5. Parity evidence

none. The change gives a rule for a name and a folder. A name changes no tensor and no decoded output
("Identity" in `model-addition-workflow/mapping-hints.md`). No run can compare it with an upstream
output.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | none (no runtime quantity) |
| Test images (paths or dataset IDs), and the branch that each image runs | none |
| Upstream reference: library, version, config and command | none |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | none |
| Preprocessed input: maximum absolute difference for each image | none |
| Row count for each image: sidecar path and upstream | none |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | none |
| Result (`pass`, `fail` or `to run`) | none (no runtime effect) |
| Script path in the exporter repo | none |
| Exporter commit of the script | none |
| Command | none |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/sidecar/loader.py::load_sidecar`. It knows the path of the sidecar and its root (`cache_dir`, the sidecar root). After the basename check, it can check the two rules on the path relative to the root. A small helper in the same module can split the path. |
| Dispatch point | `load_sidecar`, after the check "model_id ... does not match sidecar basename". The check applies only when the relative path starts with `detectors/keypoint_detectors/`. |
| Validator changes (`model.py`, with rule IDs) | No change in `skellytracker/core/sidecar/model.py`: `SidecarModel` does not know the path. `load_sidecar` raises `SidecarValidationError` with `V-common.identity-7` or `V-common.identity-8`. `V-common.identity-8` needs the resolved `pose.tracked_points`, so it runs after `resolve_sidecar_composition`. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | A test that writes each data-only case of `vectors/common.identity.yaml` to a temporary sidecar root at `input.path` and checks the failed rules. No golden parity test: the change has no runtime output. |
| Existing code that the change touches | `skellytracker/core/sidecar/loader.py` (`load_sidecar`). The package sidecars stay outside the spec until the package migrates (skellytracker ADR-0QKK). Their folders (`rtmpose/body/`, `rtmw/wholebody/`) use part groups, so they pass. |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` | none. The writer already writes `rtmw-wholebody133` in `rtmw/wholebody133/` (133 points). | none |
| OpenMMLab-Exporter | `rtmo-coco17-body7` | none. The writer already writes `rtmo-coco17-body7` in `rtmo/coco17/` (17 points). | none |
| OpenMMLab-Exporter | `rtmpose-halpe26`, `dwpose-wholebody133-ubody` (no sidecar yet) | none. The ids follow the grammar. | none |
| OpenMMLab-Exporter | `detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` | none for the rules: the example stays valid (part group). The open re-export request rebuilds it as `rtmw-wholebody133`. | none |
| Ultralytics-Exporter | `detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml` | none: `yolo26-body` in `yolo26/body/` is valid. | none |

**Reference examples that the change makes invalid.**

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` | `V-common.identity-7` | `needs-export` | `rtmo-body7` in `rtmo/body/` does not start with `rtmo-body-`. The new id is a choice of the exporter, so it does not follow from the change alone. The OpenMMLab-Exporter writer gives `rtmo-coco17-body7` in `rtmo/coco17/`, with new ONNX file names. The open item "Rebuild of each example" of the re-export request already names this example. |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none |
| Writer code (file, function and commit) | OpenMMLab-Exporter `rtmw/sidecar.py` and `pipeline/sidecar.py` at `d9704753a22792c32a1d3018a0c9e9ea2d279d71`. The RTMW intake is not `describes`, so the exporter writes no RTMW sidecar now. |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep `{family}-{part}`, and the exporter writes `rtmw-wholebody` in `rtmw/wholebody/`. | The user keeps the exporter ids (part 1, plan decisions). The text still has no id for RTMPose COCO-17 and RTMPose Halpe-26 of one family. | Part 1, upstream evidence. |
| `{family}-{part}-{variant}` in `{family}/{part}/`, for example `rtmw-wholebody-133` or `rtmo-body-body7`. | It allows a suffix, but the folder names a region, not the keypoint output. RTMW does not need a variant: it has one model line with 133 points. The user chose the keypoint-set form for the exporter (OpenMMLab-Exporter ADR-0039). | [OpenMMLab-Exporter ADR-0039](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0039-keypoint-model-id-format.md) |
| A keypoint set only: no part groups. | The current examples `rtmw-wholebody` and `yolo26-body` and the package sidecars become invalid. A part group is enough for a family with one model in the region. | Part 7 |
| A suffix with no `-`, for example `rtmo-body7` in `rtmo/body/`. | The id then does not give the end of the group. `body7` reads as a keypoint set with 7 points. | `V-common.identity-8` |
| No rule for the folder: any `model_id` that equals the basename. | Two exporters can then put unrelated ids in one folder, and the folder does not tell the model. The open-work item asks for a rule. | "Spec defects" item 1 of `specs/model-sidecar/decisions/open-work.md` |
| A rule that the keypoint-set name must be a known set (`coco`, `halpe`, `wholebody`). | The spec has no list of keypoint sets. The count check finds the most likely error (a training token in the group). | none |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal: the RTMW intake (`payload/intake.md` of `model-rtmw-wholebody133@openmmlab-exporter`) names `proposal-model-id-suffix@openmmlab-exporter` in rows F1, L1 and F5 and in its proposals table (related, not blocking).
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. A `model_id` has no upstream evidence; part 1 cites the writer code and the upstream configs.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle. n/a: no algorithm.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`. The cases are data-only.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script. n/a: no runtime effect.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. n/a.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
