# Change proposal template

This template is phase 2 of the new-model workflow. A proposal asks for one new or changed contract
unit of the sidecar spec, and for its implementation. A contract unit is one part of the spec with its
own algorithm or its own implementing function. One contract unit is one section (one section file
under `specs/model-sidecar/`). The full workflow is the model addition workflow
(`specs/model-sidecar/model-addition-workflow/README.md` of the skellytracker repo). It is the same
for an exporter and for a human contributor. Where this template says "the exporter", a contributor
that is not an exporter reads "you". The workflow
README gives the stages and the phases. Phase 1 is the model intake template (`specs/model-sidecar/templates/model-intake.md`).

This template has no relative links to other files, so its references stay correct after you copy it.
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. Read the skellytracker files in the
skellytracker checkout (read-only) `../freemocap/skellytracker`.

## How to use this template

1. Write one proposal for each new or changed contract unit. Do not put two units in one proposal.
2. Copy this file to `proposal.md` of a `proposal` bundle. Its bundle ID is
   `proposal-<slug>@<contributor>`. `<slug>` is a short lowercase name of the change, with hyphens,
   for example `letterbox-floor-rounding`. The hand-over rules give the other files, the manifest and
   the `pack` command (`specs/model-sidecar/model-addition-workflow/hand-over.md`).
3. Change the title to `# Change proposal: <slug>`.
4. Name the proposal bundle in the intake of the model ("Proposals and reference files").
5. Fill in all eight parts. Do not delete a part. If a part has no content, write `none` and the
   reason. If you do not know a value, write `unknown (<reason>)`.
6. Write the proposed spec text in ASD-STE100 Simplified Technical English. Use short sentences and
   active voice. Use "must" for a requirement. Keep technical names, field names, enum values,
   formulas, code and YAML unchanged.
7. Before you write, read the table "Considered and deliberately not added"
   (`specs/model-sidecar/changelog.md`).
   If the feature is in it, cite the row in part 1, and give the evidence that a model needs it now.
8. Before you write, find the skellytracker decision entries with the status `proposed` that cover
   your rows. Read the index in `specs/model-sidecar/decisions/README.md` of the skellytracker repo. Also read each
   `proposed` entry that the guidance of your sections cites. Run `intake_bundle.py list` and choose
   the form of the proposal: a new proposal, a contribution or a follow-up (`specs/model-sidecar/model-addition-workflow/hand-over.md`,
   "Proposal forms"). If an entry covers your rows, do not write a competing proposal:
   - Cite the entry in the header and in part 1.
   - Add your evidence, your vectors and your parity plan in a contribution.
   - If your rows need a different change, write a follow-up. Say where your proposal differs. Give
     the reason in part 8.
9. If this proposal needs another proposal, write its bundle ID in the header and in `depends_on` of
   the manifest. Do not edit another bundle. `intake_bundle.py list` shows the reverse links. One parity script can serve several proposals. Cite it in part 5 of each.
10. After you write the proposal, pack the bundle and stop. Do not change a file in skellytracker. The
    only exception: `pack` writes the new version folder of your bundle in `intakes/`. The proposed spec text
    can contain YAML excerpts. Do not write a sidecar file of the model with the proposed fields.

**Section IDs.** The spec is split into section files under `specs/model-sidecar/`. Each section file has a
section ID: the `id` in its front matter, for example `pre.resize.letterbox` or
`post.det.selection.nms` (skellytracker decision 0013). The section map (`specs/model-sidecar/README.md`)
lists each section ID and its file. For a changed section, use its section ID. For a new section,
propose an ID in the same scheme (`<format|common|pre|post>.<area>[.<name>]`). The skellytracker
session that lands the change sets the final section ID and the final rule IDs.

## What happens next

You do not do these steps. A skellytracker session does them, and the user decides.

1. A skellytracker session verifies the current version of the bundle. It copies the version byte for
   byte to `specs/model-sidecar/proposals/<slug>/` of the skellytracker repo. It records the proposal
   as a short decision entry with the status `proposed` (`specs/model-sidecar/model-addition-workflow/hand-over.md`, "Session steps"). A
   response file in the bundle gives the state.
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
| Model, and its `model` bundle ID | |
| Intake rows with the verdict `near-miss` or `gap` | |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | |
| Change class (`vnext`, `clarification` or `breaking`; the manifest key `change_class`) | |
| Base bundle of a follow-up (`base`, or `none`) | |
| Proposed section ID (the `id` in the section file's front matter) | |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | |

## 1. Gap

Give the property, its upstream evidence, and the reason why the nearest section is wrong. Show the
difference with a number where possible. Example: a `center` letterbox in place of `fit` gives an input
max abs diff of 35 on a 333×500 image (OpenMMLab-Exporter 0020).

If the only evidence is a secondary source (a plan, a paper, a README or the notes of an exporter),
mark it `(secondary)`. A check-backed claim gives an upstream line as primary evidence
([Rules](../model-addition-workflow/rules.md)). Name the primary file or config key that a reader
must check. Before the user accepts the proposal, this part must cite the primary evidence. Cite each
source in a form of [Sources](../model-addition-workflow/rules.md#sources) ([ADR-FDTD](../../../decisions/FDTD-evidence-sources-and-exporter-permalinks.md)).

| Item | Value |
|---|---|
| Property | |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | |
| Plan decisions about the spec that this proposal uses, in words (or `none`) ([User decisions](../model-addition-workflow/rules.md#user-decisions)) | |
| Nearest section ID (the `id` in the section file's front matter) | |
| Why the nearest section is wrong | |
| Measured difference (number, image and script) | |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | |

## 2. Spec change

Write the exact normative text as it will appear in the spec. Put one algorithm in one place. Other
sections link to it. Fill in each item. Write `none` for an item that the change does not need.

### 2.1 Sections

The new or changed sections, each with its proposed section ID, its title and its section file. For a
new section, also give its front matter (`id`, `title` and `kind`) and its row in the section map
(`specs/model-sidecar/README.md`).

**Places that the change edits.** A change often extends a closed set or a list in more than one
place. Search the spec for each value set or list that the change extends. List each place here, with
its section ID or file, its heading and the edit. Examples:

- the `role` values (the Overview in `specs/model-sidecar/README.md`, `common.identity` and its validation
  rules);
- the `semantic` values (`common.outputs` and its validation rules);
- the resize methods (`common.input`, `post.unprojection`, `common.sizes_and_artifacts` and their
  validation rules);
- the storage layout (`format.file_layout`, heading "Storage layout");
- the Overview, the section map and the validation index (`specs/model-sidecar/README.md`);
- the "Legacy behaviour" heading of each changed section. Add the heading to its index
  "Version-aware compatibility" (`format.versioning`) only if it gives a legacy difference. A new
  field, value or section that is not available before `vNEXT` goes in the availability row of the
  "Legacy behaviour" table of `format.versioning`;
- the summary of changes (`specs/model-sidecar/changelog.md`).

These edits are part of the same contract unit. A new role with its enum and path edits is one
proposal.

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| | | | |

### 2.3 Behaviour

The forward algorithm, step by step. If the section changes coordinates, also give its exact inverse
(see `post.unprojection`, and the heading "Inverse" of each resize section, for example
`specs/model-sidecar/pre/resize-letterbox.md`).

```text
```

### 2.4 Validation rules

Write one rule on each line. Give each new rule a new rule ID in the form `V-<section-id>-<n>`, for
example `V-pre.resize.letterbox-1` (skellytracker decision 0013). Use the proposed section ID. Mark
each rule that applies only at `vNEXT` with **(vNEXT)** (the validation index in
`specs/model-sidecar/README.md` gives its meaning). Use the form of the heading "Validation rules" in a
section file, for example `specs/model-sidecar/pre/resize-letterbox.md`.

Also find each existing rule that names a value that the change adds or changes. Example: rule
`V-pre.resize.affine_person_crop-2`: a sidecar with `pose.requires_object_detector: true` must
declare `input.resize.method: affine_person_crop`. A top-down model with a new resize method fails
this rule. List each such rule here: changed, or unchanged with the reason. If you do not change a
rule that blocks a model, list it as a follow-up.

### 2.5 Selectors

The `key=value` pairs of a resolved sidecar that make the sidecar use this section. Example:
`input.resize.method=fit`.

### 2.6 Legacy behaviour and version effect

- Give the change class: `vnext`, `clarification` or `breaking` (heading "Change classes" in
  `specs/model-sidecar/model-addition-workflow/hand-over.md`; skellytracker ADR-KDBD).
- Tell what a sidecar with `schema_version < vNEXT` does. A `vnext` change does not change the
  legacy meaning.
- Until skellytracker releases the spec, every change goes into the `vNEXT` revision. After that
  release, a change sets `schema_version` to the release that ships it.
- Give the new row of the "Legacy behaviour" table of the section, if the change gives a legacy
  difference. The index of these tables is the heading "Version-aware compatibility" in
  `specs/model-sidecar/format/versioning.md`. A new field, value or section that is not available
  before `vNEXT` goes in the availability row of the "Legacy behaviour" table of that file.
- If a part of the change applies to every `schema_version`, show that it is a clarification. Use
  each condition of the heading "Clarifications" in `specs/model-sidecar/format/versioning.md`.
  Give the result in exact math before the change and after the change. Name each host that stops
  conforming. Write its gap in part 6.
- If the change is `breaking`, give its item for the list "Every-version changes" in the same file.

### 2.7 Changelog row

The row for the `vNEXT` entry of the changelog (`specs/model-sidecar/changelog.md` heading
"`schema_version` history"), and the row for the summary of changes (heading "Summary of changes" in
the same file).

## 3. Reference implementation

- Write the smallest functions that implement exactly the text of part 2.
- Follow "Imports of other sections" in
  `specs/model-sidecar/model-addition-workflow/reference-implementations.md`.
- Write one function for each algorithm.
- In each docstring, cite the proposed section ID.
- Your host decoder needs this behaviour. The reference implementation is the clean, minimal form of
  your host code.
- If no host code exists yet, write the functions from the text of part 2. Write
  `source commit: none (no host code)` in the note at the top of the file. Part 4 is then
  `unverified: no host implementation`.
- If the proposal changes a section, follow "Full section" in
  `specs/model-sidecar/model-addition-workflow/reference-implementations.md`.
- If the proposal changes more than one section, or needs a section that has no module, follow "A
  proposal that changes more than one section" and "When the other section has no module" in the
  same file.
- Write the code to `reference/<section_module>.py` in the proposal bundle. Name that file here.
- `<section_module>` is the proposed section ID with each dot replaced by an underscore
  (`pre.resize.letterbox` gives `pre_resize_letterbox`). A proposal always uses the proposed section
  ID. For a changed section, that is the `id` in the front matter of its section file.
- To load or run a reference file, follow "Run a module that imports another module" in
  `specs/model-sidecar/model-addition-workflow/reference-implementations.md`. Keep your case code outside `reference/` ("Code for the cases").
- On acceptance, skellytracker adds the code as `specs/model-sidecar/reference/<section_module>.py`. It is
  informative spec code, not package code. It is the single executable meaning of the new text.

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | |
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
- Use the case form of `tools/make_vectors.py` exactly. `tools/tests/test_vectors.py` checks this
  form (skellytracker ADR-TA0G, `decisions/TA0G-vector-cases-and-reference-modules.md`). The keys of a case
  are `id`, `function`, `params`, `input`, `expect`, `unproject`, `tolerance`, `compare` and
  `verified_against`. Do not add other keys.
- Name the function of the reference file that each case runs (`function`). Each reference function
  returns a mapping. Its keys are the keys of `expect`.
- For a refused input, the reference function raises `ValueError`. Do not raise a different
  exception for a refused input.
- Cast each input in the reference function to the dtype that the spec gives, for example `float32`.
  The vector file writes a whole float as an integer.
- An integer must match exactly. A case with a fractional value in `expect` or `unproject` needs a
  `tolerance` or a `compare`. `tolerance` is the largest allowed absolute difference of each
  fractional value of the case. A case without a fractional value has no `tolerance`.
- `compare` gives the tolerance of one field: `atol` is the largest allowed absolute difference of the
  field. `period` compares the values of the field modulo that period, for example 2π for an angle.
  `compare` replaces `tolerance` for that field.
- A case for a refused input writes `expect: {error: <value>}`. Do not add another `expect` key.
  Do not give the error message.
- If a validation rule refuses the input, start the message with the rule ID and a colon, for
  example `V-post.det.decode-5: ...`. Then the value is that rule ID. The input must fail exactly
  one rule. The rule must be in a section file, or in part 2.4 of this proposal.
- If the input is not a sidecar value, the value is `no-rule`. Examples are a tensor of the model,
  an argument of the caller and a second sidecar. Tell in the note of the case why no rule applies.
- A sidecar with `schema_version < vNEXT` that uses a feature that is "Not available." also gives
  `no-rule`.
- If no rule refuses a sidecar value, the spec needs a new rule. Add it to part 2.4. Do not use
  `no-rule` for that value.
- Do not give a run-time function a sidecar value that a validation rule refuses. Write a
  validator case for that rule.
- A validator that reports each failed rule returns `{failed: [<rule IDs>]}`. Sort the list. Do not
  repeat an ID. Write `failed: []` for a valid sidecar. Do not add another `expect` key. Each ID must
  be in a section file, or in part 2.4 of this proposal. A validator case can have no `function`
  until an implementation exists.
- The host code of the exporter runs only the numeric cases. An `error` case and a `failed` case
  run only against the reference implementation.
- Write NaN as `.nan` and infinity as `.inf`. A NaN expected value is equal to NaN.
- The generator rounds each expected value to 6 decimals. If the section needs exact values (for
  example `float32` results), write each value with all of its digits, and say so in part 2.1. Then
  the builder of the section writes the values exactly.
- A `verified_against` entry of the exporter has the form `<Exporter repo>: <file>::<function>`.
  Write the exporter commit in the note at the top of the reference file.
- `generated_by` names your reference file. When skellytracker lands the proposal,
  `tools/make_vectors.py` calls the reference implementation through `make_vectors.outcome` and
  writes the vector file again. Then `generated_by` is `tools/make_vectors.py`. The new `cases` must
  be the cases of the current vector file, your cases and the cases of each contribution. A case of
  yours with the `id` of a current case replaces that case. List each such `id` here, with the
  reason. If this is not true, the landing stops.
- A vector file must be 256 KiB or smaller. The limit applies to the file that
  `tools/make_vectors.py` writes, with the cases of the other proposals for the section.
- Do not repeat a large value in each case when a smaller value tests the same branch.
- Write the vectors to `vectors/<section ID>.yaml` in the proposal bundle. Name that file here. Do
  not copy the cases into this part.
- The target file in skellytracker is `specs/model-sidecar/vectors/<section ID>.yaml`.

```yaml
section: <proposed section ID>
spec_revision: vNEXT
generated_by: <reference file>
verified_against:                         # or, when nothing verified the cases: unverified: <reason>
  - <Exporter repo>: <file>::<function>
cases:
  - id: <case id>
    function: <function of the reference file>
    params: {}
    input: {}
    expect: {}                            # or {error: V-<section-id>-<n>}, {error: no-rule} or {failed: [V-<section-id>-<n>]}
    tolerance: <number>                   # only when expect or unproject has a fractional value
    compare: {}                           # optional: {<field>: {atol: <number>, period: <number>}}
```

## 5. Parity evidence

Follow the parity rules of the model addition workflow
(`specs/model-sidecar/model-addition-workflow/parity.md`, heading "Parity").

- Run the real model. Use the reference implementation of part 3 in place of the missing spec feature.
  Do every other step exactly as the sidecar declares.
- Set each gate before the run, as step 1 of Parity says. Give the source of each gate. Write if it
  is a pass gate or a control.
- Use more than one test image. Each branch of the changed algorithm must run on at least one image.
- Measure the export error first: the ONNX file on the tensor of the upstream preprocessing, compared
  with the upstream model.
- Compare the preprocessed input: give the maximum absolute difference. Expect 0.
- Compare each final output of each role, as step 5 of Parity says. Write which output you
  compared.
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
| Gates, set before the run, their source, and pass gate or control | |
| Test images (paths or dataset IDs), and the branch that each image runs | |
| Upstream reference: library, version, config and command | |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | |
| Preprocessed input: maximum absolute difference for each image | |
| Row count for each image: sidecar path and upstream | |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | |
| Result (`pass`, `fail` or `to run`) | |
| Script path in the exporter repo | |
| Exporter commit of the script | |
| Command | |

## 6. skellytracker implementation proposal

skellytracker does not build this now. It builds it when it implements the spec. Do not change
skellytracker code. On acceptance, this text becomes the implementer guidance of the section and an
open-work item.

This part is advisory: the implementer checks it. Read the package code in
`../freemocap/skellytracker/skellytracker/`. If you cannot find a call site, write
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

The skellytracker package sidecars have `schema_version: "v2024.09.1019"`. A `vnext` change does not
change their meaning. For a `clarification` or a `breaking` change, write for each sidecar in the
table if it stays valid. Give the commit that you checked.

**Reference examples that the change makes invalid.** Read each example in
`specs/model-sidecar/examples/`. Start from the section rows of `specs/model-sidecar/TRACEABILITY.md`.
Write one row for each example that breaks a new or changed rule. The edit must follow from the
change alone. If the example needs a value that only an export can give, the impact is
`needs-export`. If no example breaks a rule, write `none` and the reason. The heading "When a spec
change makes an example invalid" in
`specs/model-sidecar/model-addition-workflow/reference-examples.md` gives the allowed edits.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| | | | |

**Candidate example.** Optional. Write it only after the host code implements the proposed text. The
sidecar writer code writes it, with the proposed fields. Put it in `example/detectors/...` of the
proposal bundle, in the storage layout, with each fragment that it names. Write
`example/provenance.yaml` with the `examples` entry and the `fragments` entries, in the form of
`specs/model-sidecar/inventory.yaml`. The candidate is not a spec example. After acceptance,
skellytracker copies the real export.

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | |
| Writer code (file, function and commit) | |
| `sidecar_refs.py --check` result | |

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
- [ ] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [ ] Part 2.1 lists each place that the change edits.
- [ ] Part 2.6 gives the change class, and the header and `change_class` give the same class.
- [ ] Part 3 names the reference file, and the file exists in the proposal bundle.
- [ ] Part 4 names the vector file, and the file exists in the proposal bundle.
- [ ] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [ ] Each pixel case in part 4 has its tolerance in `compare`.
- [ ] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [ ] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo.
- [ ] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [ ] No file in skellytracker changed.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready for
the user to accept. It stays incomplete until part 5 has the numbers, the script and the commit.

Then stop.
