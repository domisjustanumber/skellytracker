# Change proposal template

This template is phase 2 of the new-model workflow. A proposal asks for one new or changed contract
unit of the sidecar spec, and for its implementation. A contract unit is one part of the spec with its
own algorithm or its own implementing function. One contract unit is one section (one section file
under `specs/sidecar/`). The full workflow is in the exporter guide
(`specs/sidecar/exporter-guide.md` of the skellytracker repo, section "Sidecars"). The decision behind
it is skellytracker decision 0014 (`notes/decisions/0014-spec-lifecycle.md` of the skellytracker
repo). Phase 1 is the model intake template (`specs/sidecar/templates/model-intake.md`).

This template has no relative links to other files, so its references stay correct after you copy it.
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. Read the skellytracker files in the
read-only worktree `../freemocap/skellytracker-latest`.

## How to use this template

1. Write one proposal for each new or changed contract unit. Do not put two units in one proposal.
2. Copy this file to `plans/sidecar-proposal-<slug>.md` in the exporter repo. `<slug>` is a short
   lowercase name of the change, with hyphens, for example `letterbox-floor-rounding`. If that file
   exists, read it and update it in place. Do not overwrite it without a read: git does not track
   `plans/`.
3. Change the title to `# Change proposal: <slug>`.
4. Link the proposal from the intake (`plans/sidecar-intake-<model>.md`, "Proposals and reference
   files").
5. Fill in all eight parts. Do not delete a part. If a part has no content, write `none` and the
   reason. If you do not know a value, write `unknown (<reason>)`.
6. Write the proposed spec text in ASD-STE100 Simplified Technical English. Use short sentences and
   active voice. Use "must" for a requirement. Keep technical names, field names, enum values,
   formulas, code and YAML unchanged.
7. Before you write, read the table "Considered and deliberately not added"
   (`specs/sidecar/changelog.md`).
   If the feature is in it, cite the row in part 1, and give the evidence that a model needs it now.
8. Before you write, find the skellytracker decision entries with the status `proposed` that cover
   your rows. Read the index in `notes/decisions/README.md` of the skellytracker repo. Also read each
   `proposed` entry that the guidance of your sections cites. If an entry covers your rows, do not write a competing proposal:
   - Use the slug of the entry.
   - Cite the entry in the header and in part 1.
   - Add your evidence, your vectors and your parity plan.
   - If your rows need a different change, say where your proposal differs. Give the reason in
     part 8.
   - If the entry is a gap record (its Decision section says so), give the parts that it does not
     have.
9. If this proposal needs another proposal, or another proposal needs this one, write each dependency
   in the header. One parity script can serve several proposals. Cite it in part 5 of each.
10. After you write the proposal, stop. Do not change a file in skellytracker. The proposed spec text
    can contain YAML excerpts. Do not write a sidecar file of the model with the proposed fields.

**Section IDs.** The spec is split into section files under `specs/sidecar/`. Each section file has a
section ID: the `id` in its front matter, for example `pre.resize.letterbox` or
`post.det.selection.nms` (skellytracker decision 0013). The section map (`specs/sidecar/README.md`)
lists each section ID and its file. For a changed section, use its section ID. For a new section,
propose an ID in the same scheme (`<format|common|pre|post>.<area>[.<name>]`). The skellytracker
session that lands the change sets the final section ID and the final rule IDs.

## What happens next

You do not do these steps. A skellytracker session does them, and the user decides.

1. A skellytracker session finds the proposal in the `plans/` folder of the exporter repo. It records
   the proposal as a decision entry with the status `proposed`. If the proposal builds on a gap
   record, the new entry extends the gap record.
2. The user accepts or rejects the proposal.
3. After acceptance:
   - A content PR adds the normative text, the changelog row, the vectors and the reference
     implementation. Together they define the meaning of the change.
   - A non-spec PR (documentation only) adds the guidance, the skellytracker implementation
     proposal (as implementer guidance and an open-work item), the example and its provenance
     record.
   - When skellytracker implements the spec, an implementation PR adds the code.
4. Then the exporter writes the sidecar with the new fields, and finishes phase 1 for the model.

## Header

| Field | Value |
|---|---|
| Title | |
| Slug | |
| Date | |
| Exporter repo | |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | |
| Model, and its intake file (`plans/sidecar-intake-<model>.md`) | |
| Intake rows with the verdict `near-miss` or `gap` | |
| Kind (`new section` or `changed section`) | |
| Proposed section ID (the `id` in the section file's front matter) | |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/sidecar/`) | |
| Depends on (proposal files that must land first, or `none`) | |
| Needed by (proposal files that depend on this one, or `none`) | |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | |
| skellytracker folder that you read (normally `../freemocap/skellytracker-latest`) | |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | |

## 1. Gap

Give the property, its upstream evidence, and the reason why the nearest section is wrong. Show the
difference with a number where possible. Example: a `center` letterbox in place of `fit` gives an input
max abs diff of 35 on a 333×500 image (OpenMMLab-Exporter 0020).

If the only evidence is a secondary source (a plan, a paper, a README or the notes of an exporter),
mark it `(secondary)`. Name the primary file or config key that a reader must check. Before the user
accepts the proposal, this part must cite the primary evidence.

| Item | Value |
|---|---|
| Property | |
| Upstream evidence (file and line, or config key; upstream commit or release) | |
| Nearest section ID (the `id` in the section file's front matter) | |
| Why the nearest section is wrong | |
| Measured difference (number, image and script) | |
| Row in "Considered and deliberately not added" (`specs/sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | |

## 2. Spec change

Write the exact normative text as it will appear in the spec. Put one algorithm in one place. Other
sections link to it. Fill in each item. Write `none` for an item that the change does not need.

### 2.1 Sections

The new or changed sections, each with its proposed section ID, its title and its section file. For a
new section, also give its front matter (`id`, `title` and `kind`) and its row in the section map
(`specs/sidecar/README.md`).

**Places that the change edits.** A change often extends a closed set or a list in more than one
place. Search the spec for each value set or list that the change extends. List each place here, with
its section ID or file, its heading and the edit. Examples:

- the `role` values (the Overview in `specs/sidecar/README.md`, `common.identity` and its validation
  rules);
- the `semantic` values (`common.outputs` and its validation rules);
- the resize methods (`common.input`, `post.unprojection`, `common.sizes_and_artifacts` and their
  validation rules);
- the storage layout (`format.file_layout`, heading "Storage layout");
- the Overview, the section map and the validation index (`specs/sidecar/README.md`);
- the "Legacy behaviour" heading of each changed section, and its index "Version-aware
  compatibility" (`format.versioning`);
- the summary of changes (`specs/sidecar/changelog.md`).

These edits are part of the same contract unit. A new role with its enum and path edits is one
proposal.

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| | | | |

### 2.3 Behaviour

The forward algorithm, step by step. If the section changes coordinates, also give its exact inverse
(see `post.unprojection`, and the heading "Inverse" of each resize section, for example
`specs/sidecar/pre/resize-letterbox.md`).

```text
```

### 2.4 Validation rules

Write one rule on each line. Give each new rule a new rule ID in the form `V-<section-id>-<n>`, for
example `V-pre.resize.letterbox-1` (skellytracker decision 0013). Use the proposed section ID. Mark
each rule that applies only at `vNEXT` with **(vNEXT)** (the validation index in
`specs/sidecar/README.md` gives its meaning). Use the form of the heading "Validation rules" in a
section file, for example `specs/sidecar/pre/resize-letterbox.md`.

Also find each existing rule that names a value that the change adds or changes. Example: rule
`V-pre.resize.affine_person_crop-2`: a sidecar with `pose.requires_object_detector: true` must
declare `input.resize.method: affine_person_crop`. A top-down model with a new resize method fails
this rule. List each such rule here: changed, or unchanged with the reason. If you do not change a
rule that blocks a model, list it as a follow-up.

### 2.5 Selectors

The `key=value` pairs of a resolved sidecar that make the sidecar use this section. Example:
`input.resize.method=fit`.

### 2.6 Legacy behaviour and version effect

- Tell what a sidecar with `schema_version < vNEXT` does. The legacy meaning must not change.
- Until skellytracker releases the spec, every change goes into the `vNEXT` revision. After that
  release, a change sets `schema_version` to the release that ships it.
- Give the new row of the "Legacy behaviour" table of the section, if the change needs one. The index
  of these tables is the heading "Version-aware compatibility" in
  `specs/sidecar/format/versioning.md`.

### 2.7 Changelog row

The row for the `vNEXT` entry of the changelog (`specs/sidecar/changelog.md` heading
"`schema_version` history"), and the row for the summary of changes (heading "Summary of changes" in
the same file).

## 3. Reference implementation

- Write the smallest functions that implement exactly the text of part 2.
- Use only NumPy, OpenCV and the Python standard library. Do not import from the exporter or from
  skellytracker.
- Write one function for each algorithm.
- In each docstring, cite the proposed section ID.
- Your host decoder needs this behaviour. The reference implementation is the clean, minimal form of
  your host code.
- If no host code exists yet, write the functions from the text of part 2. Write
  `source commit: none (no host code)` in the note at the top of the file. Part 4 is then
  `unverified: no host implementation`.
- If the proposal changes a section that has no reference implementation, implement the full section
  as changed (forward, inverse and every value), not only the change. Then this file is also the
  reference-implementation step of that section.
- Write the code to `plans/sidecar-reference-<section_module>.py` in the exporter repo. Name that file
  here.
- `<section_module>` is the proposed section ID with each dot replaced by an underscore
  (`pre.resize.letterbox` gives `pre_resize_letterbox`). A proposal always uses the proposed section
  ID. For a changed section, that is the `id` in the front matter of its section file.
- Python can import the target file `specs/sidecar/reference/<section_module>.py` by its name. The
  exporter file name has hyphens, so Python cannot import it by its name. Load it with
  `importlib.util.spec_from_file_location`, or run it as a script.
- On acceptance, skellytracker adds the code as `specs/sidecar/reference/<section_module>.py`. It is
  informative spec code, not package code. It is the single executable meaning of the new text.

| Item | Value |
|---|---|
| Reference file in the exporter repo (`plans/sidecar-reference-<section_module>.py`) | |
| Target file in skellytracker (`specs/sidecar/reference/<section_module>.py`) | |
| Functions (one for each algorithm) | |

## 4. Vectors

A test vector is a small worked case: concrete inputs to the algorithm of one section, and the exact
expected output.

- Make the vectors with the reference implementation of part 3.
- Run the same cases through the host implementation of the exporter. List it in `verified_against`
  only if it gives the same results.
- The reference implementation and its source exporter count as one implementation in
  `verified_against`. Only exporters and skellytracker count as implementations. Do not list the
  upstream library. If you ran a case through upstream code, write that in a comment.
- If no implementation gave the same results yet (for example, the host code does not exist or is not
  committed), write `unverified: <reason>` in place of `verified_against`. A vector made only from a
  reading of the spec text is not verified.
- Include a case for each branch of the algorithm, and the edge cases: rounding ties, strict `>`
  comparisons and tie order.
- If a parameter can be a scalar or one value for each channel (for example `pad_value`), include a
  case with a scalar value on a 3-channel input.
- Use geometry and small arrays. Do not use images or ONNX files. Pixel-exact resize output is out of
  scope. If you need a pixel case, state its tolerance in `compare`.
- Name the function of the reference file that each case runs (`function`).
- Without `compare`, each expected value must match exactly. In `compare`, `atol` is the largest
  allowed absolute difference of a field. `period` compares the values of a field modulo that period,
  for example 2π for an angle.
- The target file in skellytracker is `specs/sidecar/vectors/<section ID>.yaml`.

```yaml
section: <proposed section ID>
spec_revision: vNEXT
generated_by: <reference file>
verified_against:                         # or, when nothing verified the cases: unverified: <reason>
  - <Exporter repo>: <file>::<function>   # exporter commit <sha>
cases:
  - id: <case id>
    function: <function of the reference file>
    params: {}
    input: {}
    expect: {}
    compare: {}                           # optional: {<field>: {atol: <number>, period: <number>}}
```

## 5. Parity evidence

Follow the parity rules of the exporter guide (section "Sidecars", heading "Parity").

- Run the real model. Use the reference implementation of part 3 in place of the missing spec feature.
  Do every other step exactly as the sidecar declares.
- Set each gate before the run, and record its source.
- Use more than one test image. Each branch of the changed algorithm must run on at least one image.
- Measure the export error first: the ONNX file on the tensor of the upstream preprocessing, compared
  with the upstream model.
- Compare the preprocessed input: give the maximum absolute difference. Expect 0.
- Compare the final outputs in source-image coordinates: the row counts, the boxes for the
  `object_detector` role and the keypoints for the `pose_estimator` role. A model with both roles needs
  both.
- Commit the script in the exporter repo, so that the commit can be cited. Use the folder of the
  exporter for evidence scripts. If the exporter has no such folder, use `notes/decisions/scripts/`
  (OpenMMLab-Exporter uses it). A script that is only in a local `plans/` folder is not evidence.
- Give the numbers, the script and the commit. If one script serves several proposals, cite it here
  and in each of the other proposals.
- If you cannot run the check yet (for example, no ONNX file exists, the upstream cannot run, or the
  exporter has no git repo), write `to run` in the result. Describe the script and its gates. Fill in
  each cell that does not need a number. Write `to run` in each cell that needs a number.
- If you do not know the path or the commit of the script, write `unknown (<reason>)` in its cell.
- A skellytracker session can record a proposal with `to run` as a `proposed` decision entry. Before
  the user accepts the proposal, fill in the numbers, the script and the commit.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | |
| Test images (paths or dataset IDs), and the branch that each image runs | |
| Upstream reference: library, version, config and command | |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | |
| Preprocessed input: maximum absolute difference for each image | |
| Row count for each image: sidecar path and upstream | |
| Final outputs in source-image coordinates: metric and value for each role | |
| Result (`pass`, `fail` or `to run`) | |
| Script path in the exporter repo | |
| Exporter commit of the script | |
| Command | |

## 6. skellytracker implementation proposal

skellytracker does not build this now. It builds it when it implements the spec. Do not change
skellytracker code. On acceptance, this text becomes the implementer guidance of the section and an
open-work item.

This part is advisory: the implementer checks it. Read the package code in
`../freemocap/skellytracker-latest/skellytracker/`. If you cannot find a call site, write
`for the implementer`, and say what is not known.

Write:

- where the code goes: a module and a function under `skellytracker/core/detectors/processing/`, or
  a new module;
- the dispatch point, for example a new branch in `preprocess_image`
  (`skellytracker/core/detectors/processing/image_preprocessing.py`), which selects the resize by
  `input_spec.resize.method`;
- the validator changes in `skellytracker/core/sidecar/model.py`, with the rule IDs of part 2.4;
- the tests: the vectors of part 4, and a golden parity test (for example, the tests in
  `skellytracker/tests/sidecar/` compare detector output with golden fixtures);
- the existing skellytracker code that the change touches (file and function).

The code for each contract part today:

| Contract part | File | Functions or classes |
|---|---|---|
| Resize and normalization | `skellytracker/core/detectors/processing/image_preprocessing.py` | `preprocess_image`, `letterbox_preprocess`, `fit_preprocess`, `build_normalization_fn` |
| Top-down affine crop | `skellytracker/core/detectors/processing/affine_crop.py` | `top_down_affine`, `bbox_xyxy2cs`, `get_warp_matrix` |
| Detection decode, and the box unprojection (a division by the letterbox `ratio`) | `skellytracker/core/detectors/processing/object_detection_decode.py` | `decode_prenms`, `decode_nms_baked_in`, `boxes_to_xyxy`, `nms`, `multiclass_nms` |
| SimCC pose decode, and the keypoint unprojection from the crop | `skellytracker/core/detectors/processing/simcc_decode.py` | `simcc_pose_decode`, `decode_simcc` |
| Detector dispatch by `detector_type` | `skellytracker/core/detectors/detector_base_classes.py` | `OBJECT_DETECTOR_REGISTRY`, `KEYPOINT_DETECTOR_REGISTRY`, `build_object_detector`, `build_keypoint_detector` |
| A stage: one optional object detector and its keypoint detectors | `skellytracker/core/tracker/detection_stage.py` | `DetectionStage` |
| Sidecar loading and composition | `skellytracker/core/sidecar/loader.py`, `skellytracker/core/sidecar/resolution.py` | `load_sidecar`, `resolve_sidecar_composition` |
| From a sidecar to an ONNX model spec | `skellytracker/core/sidecar/runtime.py` | `sidecar_model_spec` |
| Validation | `skellytracker/core/sidecar/model.py` | `SidecarModel`, `ResizeSpec`, `DetectionDecodeSpec`, `PoseDecodeSpec` |
| Catalog and discovery of sidecars | none yet | skellytracker decision 0016 gives the rules. |

| Item | Value |
|---|---|
| Module and function | |
| Dispatch point | |
| Validator changes (`model.py`, with rule IDs) | |
| Tests | |
| Existing code that the change touches | |

## 7. Exporter impact

Name each exporter that must write new fields or regenerate sidecars. Describe the change to the host
decoder of the proposing exporter.

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | | | |
| Roboflow-Exporter | | | |
| Ultralytics-Exporter | | | |
| Qualcomm-Exporter | | | |
| MediaPipe-Exporter | | | |
| The proposing exporter, if it is not in this table | | | |
| skellytracker package sidecars | | | |

The skellytracker package sidecars have `schema_version: "v2024.09.1019"`. Their legacy meaning must
not change.

## 8. Alternatives considered

List each alternative and the reason why you rejected it. Include the near-miss: the nearest section
with its current values. Give numbers where you have them.

| Alternative | Why rejected | Evidence |
|---|---|---|
| | | |

## Before you stop

Tick each box when its condition is true. If the condition of a box does not apply, tick the box and
write `n/a` after it.

- [ ] All eight parts are filled in, or say `none` with a reason.
- [ ] The intake links to this proposal.
- [ ] The header gives the dependencies, or `none`.
- [ ] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [ ] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [ ] Part 2.1 lists each place that the change edits.
- [ ] Part 3 names the reference file, and the file exists in `plans/`.
- [ ] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [ ] Each pixel case in part 4 has its tolerance in `compare`.
- [ ] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [ ] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo.
- [ ] No file in skellytracker changed.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready for
the user to accept. It stays incomplete until part 5 has the numbers, the script and the commit.

Then stop.
