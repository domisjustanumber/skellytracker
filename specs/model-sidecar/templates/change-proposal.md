# Change proposal template

This template is phase 2 of the new-model workflow. A proposal asks for one new or changed contract
unit of the sidecar spec, and for its implementation. A contract unit is one part of the spec with its
own algorithm or its own implementing function. A contract unit has one primary section. It can also
change other sections that the same change needs. The manifest `sections` lists each changed section.
The first one is the primary section (heading "Proposal forms" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`). The full workflow is the model addition workflow
(`specs/model-sidecar/model-addition-workflow/README.md` of the skellytracker repo). It is the same
for an exporter and for a human contributor. Where this template says "the exporter", a contributor
that is not an exporter reads "you". The workflow
README gives the stages and the phases. Phase 1 is the model intake template (`specs/model-sidecar/templates/model-intake.md`).

This template has no relative links to other files, so its references stay correct after you copy it.
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. It names each workflow rule by its
heading and the workflow file that holds it, for example "Before you write a proposal" in
`specs/model-sidecar/model-addition-workflow/phase-2-proposal.md`. Read the rule there
(skellytracker ADR-ESP4). Read the skellytracker files in the skellytracker checkout (read-only)
`../freemocap/skellytracker`.

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
7. Before you write, do each step of "Before you write a proposal" in
   `specs/model-sidecar/model-addition-workflow/phase-2-proposal.md`. Choose the form of the
   proposal as "Proposal forms" in `specs/model-sidecar/model-addition-workflow/hand-over.md` says.
8. After you write the proposal, pack the bundle and stop. Do not change a file in skellytracker. The
   only exception: `pack` writes the new version folder of your bundle in `intakes/`. The proposed spec text
   can contain YAML excerpts. Do not write a sidecar file of the model with the proposed fields.

**Section IDs.** For a changed section, use its section ID. For a new section, propose an ID.
"Section IDs" in `specs/model-sidecar/model-addition-workflow/reading-the-spec.md` and "Module names"
in `specs/model-sidecar/model-addition-workflow/reference-implementations.md` give the scheme. The
skellytracker session that lands the change sets the final section ID and the final rule IDs.

## What happens next

You do not do these steps. A skellytracker session does them, and the user decides. Item 2 and
item 3 of `specs/model-sidecar/model-addition-workflow/phase-3-skellytracker.md` give the steps. The
status of the `proposed` entry of the proposal gives its state. A response file in the bundle is a
notice ("Responses" in `specs/model-sidecar/model-addition-workflow/hand-over.md`; skellytracker
ADR-ZXD7).

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
| Base bundle of a follow-up (`base`, or `none`) | |
| Proposed section ID (the `id` in the section file's front matter) | |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | |

## 1. Gap

Give the property, its upstream evidence, and the reason why the nearest section is wrong. Show the
difference with a number where possible. Example: a `center` letterbox in place of `fit` gives an input
max abs diff of 35 on a 333×500 image 
([OpenMMLab-Exporter ADR-0020](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/0020-rtmo-sidecar-contract.md)).

Give the evidence as "Rules" in `specs/model-sidecar/model-addition-workflow/rules.md` says. Cite
each source in a form of the heading "Sources" in the same file. If the
primary evidence is missing, name the primary file or config key that a reader must check. Before
the user accepts the proposal, this part must cite the primary evidence.

| Item | Value |
|---|---|
| Property | |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | |
| Nearest section ID (the `id` in the section file's front matter) | |
| Why the nearest section is wrong | |
| Measured difference (number, image and script) | |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | |

## 2. Spec change

Write the exact normative text as it will appear in the spec. Put one algorithm in one place. Other
sections link to it. Fill in each item. Write `none` for an item that the change does not need.

### 2.1 Sections

The new or changed sections, each with its proposed section ID, its title and its section file. For a
new section, also give its front matter (`id`, `title` and `kind`) and its row in the section map
(`specs/model-sidecar/README.md`).

**Places that the change edits.** Find each place as part 2 of
`specs/model-sidecar/model-addition-workflow/phase-2-proposal.md` says. List each place here, with its
section ID or file, its heading and the edit. Places that a change often edits:

- the `role` values (the Overview in `specs/model-sidecar/README.md`, `common.identity` and its validation
  rules);
- the `semantic` values (`common.outputs` and its validation rules);
- the resize methods (`common.input`, `post.unprojection`, `common.sizes_and_artifacts` and their
  validation rules);
- the storage layout (`format.file_layout`, heading "Storage layout");
- the Overview, the section map and the validation index (`specs/model-sidecar/README.md`);
- the summary of changes (`specs/model-sidecar/changelog.md`).

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
example `V-pre.resize.letterbox-1` (skellytracker ADR-0013). Use the proposed section ID. Use
the form of the heading "Validation rules" in a section file, for example
`specs/model-sidecar/pre/resize-letterbox.md`. Do not renumber an existing rule. A rule ID never
shifts. To delete a rule, name its ID: its number stays unused (skellytracker ADR-6GE2).

Also find each existing rule that names a value that the change adds or changes. Example: rule
`V-pre.resize.affine_crop-2`: a sidecar with a top-down `keypoint.estimator_type` must
declare `input.resize.method: affine_crop`. A top-down model with a new resize method fails
this rule. List each such rule here: changed, or unchanged with the reason. If you do not change a
rule that blocks a model, list it as a follow-up.

### 2.5 Selectors

The `key=value` pairs of a resolved sidecar that make the sidecar use this section. Example:
`input.resize.method=fit`.

### 2.6 Changelog row

The row for the summary of changes (`specs/model-sidecar/changelog.md` heading "Summary of
changes"). The change targets the open target (header). Do not write a `Row` line under
"Revisions" and do not change `schema_version`: the skellytracker session that lands the change
adds the `Row` line under the open target (skellytracker ADR-6GE2).

## 3. Reference implementation

Write the reference implementation as part 3 of
`specs/model-sidecar/model-addition-workflow/phase-2-proposal.md` says. Follow these headings in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md`: "Full section", "Module
names", "Imports of other sections", "A proposal that changes more than one section", "When the other
section has no module", "Code for the cases" and "Run a module that imports another module". Write
the code to `reference/<section_module>.py` in the proposal bundle. Name that file here.

From the 2.0.0 pre-release, write no reference implementation. Write the change of the package
code as `skellytracker.patch` in the proposal bundle, as "Patches" in
`specs/model-sidecar/model-addition-workflow/hand-over.md` says (skellytracker ADR-6J8E). Name the
patch and its `patch_release` here.

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | |
| Functions (one for each algorithm) | |

## 4. Vectors

A test vector is a small worked case: concrete inputs to the algorithm of one section, and the exact
expected output.

- Make the vectors with the reference implementation of part 3.
- Run the numeric cases through the host implementation of the exporter. A host run of an exporter
  compares only the numeric cases. An `error` case and a `failed` case run only against the reference
  implementation, and they do not need `verified_against`. List the host implementation in
  `verified_against` only if it gives the same results. A `verified_against` that the exporter gives
  covers only the numeric cases (skellytracker ADR-ESP4).
- Write `verified_against`, or `unverified: <reason>` in its place, as "Independence" in
  `specs/model-sidecar/model-addition-workflow/sidecar-files.md` says. For example, write
  `unverified: <reason>` when the host code does not exist or is not committed
  (skellytracker ADR-ESP4).
- Include a case for each branch of the algorithm, and the edge cases: rounding ties, strict `>`
  comparisons and tie order.
- If a parameter can be a scalar or one value for each channel (for example `pad_value`), include a
  case with a scalar value on a 3-channel input.
- Use geometry and small arrays. Do not use images or ONNX files. Pixel-exact resize output is out of
  scope. If you need a pixel case, state its tolerance in `compare`.
- Use the form of a skellytracker vector file exactly. `tools/vector_form.py` checks this form
  (skellytracker ADR-8DSW, `decisions/entries/8DSW-vector-files-are-the-case-source.md`). The
  top-level keys are, in this order: `section`, `notes`, `tolerance`, `checks`, `verified_against`
  or `unverified`, and `cases`. The keys of a case are, in this order: `id`, `note`, `function`,
  `checks`, `params`, `input`, `expect`, `compare` and `verified_against`. Do not add other keys.
- Start the file with the 2 comment lines of the example below. Write each other note in `notes` or
  in `note`, not in a YAML comment. `tools/make_vectors.py` does not keep the other comments. The
  comments after the keys of the example are only help for this template.
- `notes` is a list of strings: the reading notes of the file. The first note is
  `Normative text: <path of the section file>`.
- `note` is an optional string about one case.
- `checks` is optional. It names the self-checks of the skellytracker generator. Hosts ignore
  `checks`. A file-level `checks` applies to each case. A case lists only the checks that the file
  does not list. Each name must be `refused` or a key of `CHECKS` in
  `tools/vector_formulas/<section_module>.py` of skellytracker. An unknown name stops the generator.
- A case with `expect: {error: ...}` must list the check `refused`. Use `refused` only in such a
  case. `tools/vector_form.py` checks this (skellytracker ADR-8DSW).
- A case is one call of one function. The reference module has `run(params, input)`. If the section
  has an inverse, the module also has `inverse(params, input)`. Each function returns a mapping. Its
  keys are the keys of `expect`.
- A case without `function` calls `run`. `function` can name another function of the reference
  module, with the same arguments.
- An Inverse case has the `id` `<forward id>-inverse` and `function: inverse`. Put it directly after
  its forward case. Give it the same `params` as the forward case. Its `input` is the forward `input`
  and `model_xy`. Its `expect` is `{source_xy: [<x>, <y>]}`.
- The keys of `params` and the keys of `input` must be different.
- For a refused input, the reference function raises `ValueError`. Do not raise a different
  exception for a refused input.
- Cast each input in the reference function to the dtype that the spec gives, for example `float32`.
  The vector file writes a whole float as an integer.
- An integer must match exactly. `tolerance` is one number for the file. It is the largest allowed
  absolute difference of each fractional value in `expect`, in each case.
- `compare` gives the tolerance of one field: `atol` is the largest allowed absolute difference of the
  field. `period` compares the values of the field modulo that period, for example 2π for an angle.
  `compare` replaces `tolerance` for that field.
- A case for a refused input writes `expect: {error: <value>}`. Do not add another `expect` key.
  Do not give the error message.
- If a validation rule refuses the input, start the message with the rule ID and a colon, for
  example `V-post.object.decode-5: ...`. Then the value is that rule ID. The input must fail exactly
  one rule. The rule must be in a section file, or in part 2.4 of this proposal.
- If the input is not a sidecar value, the value is `no-rule`. Examples are a tensor of the model,
  an argument of the caller and a second sidecar. A `no-rule` case must have a `note`. Give the
  reason in it, for example `note: the input is a tensor, not a sidecar value`
  (skellytracker ADR-8DSW).
- If no rule refuses a sidecar value, the spec needs a new rule. Add it to part 2.4. Do not use
  `no-rule` for that value.
- Do not give a run-time function a sidecar value that a validation rule refuses. Write a
  validator case for that rule. Write the validator case in the vector file of the section that owns
  the rule.
- A validator that reports each failed rule returns `{failed: [<rule IDs>]}`. Sort the list. Do not
  repeat an ID. Write `failed: []` for a valid sidecar. Do not add another `expect` key. Each ID must
  be in a section file, or in part 2.4 of this proposal.
- A validator case can be data only. Write `function: none` and write its `expect: {failed: [...]}`
  yourself. The generator does not run such a case. Use `function: none` only with `failed`
  (skellytracker ADR-8DSW).
- Write NaN as `.nan` and infinity as `.inf`. A NaN expected value is equal to NaN.
- Write the author keys: each key of the example below except `expect`. Then run `fill` of
  `tools/make_vectors.py` in the environment of the skellytracker checkout. It writes `expect` of
  each case with your reference implementation, with 6 decimals and with the emitter of
  skellytracker. It changes no other value. Run it before `pack`. A run after `pack` changes the
  file hashes of the manifest (skellytracker ADR-8DSW, item 6).

  ```sh
  uv run --project ../freemocap/skellytracker --no-sync python -B ../freemocap/skellytracker/tools/make_vectors.py fill <payload folder>/vectors/<section ID>.yaml --reference <payload folder>/reference
  ```

- `fill` runs the code of `--reference`. Give only the `reference/` folder of your own payload.
  Never give the code of another bundle or of a record, also as a copy. `fill` refuses a folder of
  the skellytracker checkout and a folder that is not `<payload folder>/reference` (skellytracker
  ADR-AD33).
- If `fill` prints a problem, correct the author keys or the reference implementation. Then run
  `fill` again. Do not edit `expect` by hand. The only exception is a `function: none` case.
- A `verified_against` entry of the exporter has the form `<Exporter repo>: <file>::<function>`.
  Write the exporter commit in the note at the top of the reference file.
- When skellytracker lands the proposal, `make_vectors.py land` merges your file into the current
  vector file. It keeps the current cases. A case of yours with the `id` of a current case replaces
  that case. List each such `id` here, with the reason. `land` gets this list as `--replaces`.
  Each other case of yours goes at the end. Then `land` runs your reference implementation and
  compares each `expect` within the tolerance. If a check fails, the landing stops
  (skellytracker ADR-8DSW, item 5).
- A vector file must be 256 KiB or smaller. The limit applies to the file that
  `tools/make_vectors.py` writes, with the cases of the other proposals for the section.
- Do not repeat a large value in each case when a smaller value tests the same branch.
- Write the vectors to `vectors/<section ID>.yaml` in the proposal bundle. Name that file here. Do
  not copy the cases into this part.
- The target file in skellytracker is `specs/model-sidecar/vectors/<section ID>.yaml`.

```yaml
# tools/make_vectors.py writes `expect`. Edit the other keys, then run it.
# Hosts ignore `checks`. The names are the self-checks of the generator.
section: <proposed section ID>
notes:
  - "Normative text: specs/model-sidecar/<section file>."
  - <a reading note>
tolerance: <number>                       # the largest absolute difference of a fractional value
checks: [<check name>]                    # optional
verified_against:                         # or, when nothing verified the cases: unverified: <reason>
  - <Exporter repo>: <file>::<function>
cases:
  - id: <case id>
    note: <a note on the case>            # optional; required for {error: no-rule}
    function: <function of the reference module>  # optional: run when absent; none for a data-only validator case
    checks: [<check name>]                # optional; [refused] for an error result
    params: {}
    input: {}
    expect: {}                            # or {error: V-<section-id>-<n>}, {error: no-rule} or {failed: [V-<section-id>-<n>]}
    compare: {}                           # optional: {<field>: {atol: <number>, period: <number>}}
  - id: <case id>-inverse                 # an Inverse case directly after its forward case
    function: inverse
    params: {}                            # the params of the forward case
    input: {model_xy: [<x>, <y>]}         # the input of the forward case and model_xy
    expect: {source_xy: [<x>, <y>]}
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
  exporter for evidence scripts. A script that is only in a local plan folder is not evidence.
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

Write this part as part 6 of `specs/model-sidecar/model-addition-workflow/phase-2-proposal.md` says.
Do not change skellytracker code. Read the package code in
`../freemocap/skellytracker/skellytracker/`.

The code for each contract part today: the Steps column of the table "Implementation status" in
`specs/model-sidecar/TRACEABILITY.md` names the function of each step of each section. Read the whole
file that the Steps column names, also its helpers. The Steps column does not give these parts
(skellytracker ADR-ESP4):

| Contract part | File | Functions or classes |
|---|---|---|
| Detector dispatch by `detector_type` | `skellytracker/core/detectors/detector_base_classes.py` | `OBJECT_DETECTOR_REGISTRY`, `KEYPOINT_DETECTOR_REGISTRY`, `build_object_detector`, `build_keypoint_detector` |
| A stage: one optional object detector and its keypoint detectors | `skellytracker/core/tracker/detection_stage.py` | `DetectionStage` |
| From a sidecar to an ONNX model spec | `skellytracker/core/sidecar/runtime.py` | `sidecar_model_spec` |
| Catalog and discovery of sidecars | none yet | `format.file_layout` (`specs/model-sidecar/format/file-layout.md`, headings "Sidecar roots" and "Discovery") gives the rules (skellytracker ADR-0QKK). |

| Item | Value |
|---|---|
| Module and function | |
| Dispatch point | |
| Validator changes (`model.py`, with rule IDs) | |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | |
| Existing code that the change touches | |

## 7. Exporter impact

List each affected sidecar group: its owner repo, the inventory key or the model, the change and the
host decoder change. Find the groups from the section rows of `specs/model-sidecar/TRACEABILITY.md`,
and from the `model` bundles that `intake_bundle.py list` shows with an affected section in
`sections`. Describe the change to the host decoder of the proposing exporter. At landing,
skellytracker compares this list with the result of `sidecar_trace.py impact`. A `needs-export` row
of an accepted proposal is the request for a new export of the example (heading "Re-export requests"
in `specs/model-sidecar/model-addition-workflow/hand-over.md`; skellytracker ADR-C0YD,
`decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md`).

Each change targets the open target: the next skellytracker release that includes a spec change
(skellytracker ADR-6GE2, `decisions/entries/6GE2-spec-version-follows-skellytracker.md`). Write
only the text of the open target. Do not write a second text for an older or a later version. Each
sidecar has one reading: the current spec text (skellytracker ADR-0QKK,
`decisions/entries/0QKK-no-legacy-layer.md`).

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| | | | |

The old skellytracker package sidecars stay outside the spec until they are deleted. They do not
migrate (skellytracker ADR-AMJ8). Do not list them.

**Reference examples that the change makes invalid.** Read each example in
`specs/model-sidecar/examples/`. Start from the section rows of `specs/model-sidecar/TRACEABILITY.md`.
Write one row for each example that breaks a new or changed rule. The edit must follow from the
change alone. The only exception is a value that you read from the graph of an ONNX file of the
exporter of the example, with `onnx.load(path, load_external_data=False)`. Do not run the file. Give
the value, the file path in the exporter repo and its SHA-256 in the edit text. If the example needs
a value that the change does not give and that the graph cannot give, the impact is `needs-export`
(skellytracker ADR-C0YD item 2, `decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md`).
If a user ruling names the example, write the impact `removed (user ruling)`: the content commit
removes the example, and the row is not a request (skellytracker ADR-C0YD,
`decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md`). If no example breaks a rule, write `none` and the
reason. The heading "When a spec change makes an example invalid" in
`specs/model-sidecar/model-addition-workflow/reference-examples.md` gives the allowed edits.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit`, `needs-export` or `removed (user ruling)`) | Edit text |
|---|---|---|---|
| | | | |

**Candidate example.** Optional. Write it only after the host code implements the proposed text. The
sidecar writer code writes it, with the proposed fields. Put it in `example/detectors/...` of the
proposal bundle, in the storage layout, with each fragment that it names. Write
`example/provenance.yaml` with the `examples` entry and the `fragments` entries, in the form of
`specs/model-sidecar/inventory.yaml`. Do not write `source` in it: the session takes `source` from
the example sidecar (skellytracker ADR-ZXD7). The candidate is not a spec example. After acceptance,
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
- [ ] The intake names the bundle ID of this proposal.
- [ ] The header gives the dependencies, or `none`.
- [ ] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [ ] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [ ] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [ ] Part 2.1 lists each place that the change edits.
- [ ] Part 2 gives the behaviour of each new step on NaN, on inf, on a tie and on an empty input, or
      `out of scope`, as part 2 of "The parts of a proposal" in
      `specs/model-sidecar/model-addition-workflow/phase-2-proposal.md` says.
- [ ] Part 3 names the reference file, and the file exists in the proposal bundle.
- [ ] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [ ] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [ ] Each pixel case in part 4 has its tolerance in `compare`.
- [ ] Each case with a partial input in part 4 names in its `note` the rules that it checks, as part 4
      of "The parts of a proposal" in the same file says.
- [ ] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [ ] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo.
- [ ] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [ ] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [ ] Each citation of upstream code or of the code of another repo is a permalink with a full
      40-character SHA, as "Sources" in `specs/model-sidecar/model-addition-workflow/rules.md` says.
- [ ] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.

A proposal with `to run` in part 5 is ready for a skellytracker session to record. It is not ready for
the user to accept. It stays incomplete until part 5 has the numbers, the script and the commit.

Then stop.
