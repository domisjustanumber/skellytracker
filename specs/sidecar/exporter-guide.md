# Sidecar exporter guide

This guide gives the rules that exporters follow when they write sidecars. An exporter is a repo
that makes ONNX files and writes their sidecars: OpenMMLab-Exporter, Roboflow-Exporter,
Ultralytics-Exporter, Qualcomm-Exporter and MediaPipe-Exporter.

The [sidecar spec](../sidecar-spec.md) is normative. This guide is informative: it tells how to apply
the spec to a new model. If this guide and the spec do not agree, the spec is correct.

## How to use this guide

- skellytracker sessions do not change exporter repos. The exporters will be overhauled soon, and each
  overhaul adopts this guide. (Decided by the user on 2026-10-22.)
- An exporter overhaul copies the [Sidecars](#sidecars) section into the exporter's `AGENTS.md`
  unchanged. After the copy, the agents of that exporter follow the workflow of the section.
- Before its overhaul, an exporter agent runs the workflow only when the user asks. Then it writes only
  the `plans/sidecar-*` files, unless the user permits more.
- The Sidecars section names each file by its path in the read-only worktree, in a code span. It has
  no relative Markdown links, because relative links break when the section is copied to another repo.
  For the same reason, the change proposal template has no relative links to other files. The model
  intake template has them only in the section column of its property tables.
- Worktree paths in the Sidecars section start at the root of the exporter repo. The exporter repos
  and the `freemocap` folder must be in the same parent folder.
- When the Sidecars section changes here, the exporters copy it again.
- Two skills wrap the workflow of the Sidecars section for exporter agents:
  [`author-sidecar`](../../.claude/skills/author-sidecar/SKILL.md) for phase 1 and the
  reference-implementation step, and
  [`propose-sidecar-change`](../../.claude/skills/propose-sidecar-change/SKILL.md) for phase 2. The
  skills give the steps, the inputs, the outputs and the stop points. They link to this guide for the
  rules. The Sidecars section stays the full workflow.

The decisions behind this guide:

- [0013](../../notes/decisions/0013-spec-structure.md): section IDs, rule IDs, reference
  implementations and test vectors.
- [0014](../../notes/decisions/0014-spec-lifecycle.md): the spec lifecycle, the `vNEXT` rule and the
  new-model workflow.
- [0016](../../notes/decisions/0016-sidecar-catalogs.md): sidecar catalogs: `source`, reference
  hashes, roots, discovery and the capability check.

The spec is split into section files under `specs/sidecar/`. The entry point is
[`specs/sidecar-spec.md`](../sidecar-spec.md): it is the permanent index, and it keeps each old
heading as an anchor with a link to the section file that holds the text now. The section map is
[`specs/sidecar/README.md`](README.md#section-map). It lists each section ID and its file. The
sections and headings that this guide uses most:
[`input.resize`](common/input.md#inputresize), [`sizes`](common/sizes-and-artifacts.md#sizes),
[Storage layout](format/file-layout.md#storage-layout),
[Schema versioning](format/versioning.md),
[Version-aware compatibility](format/versioning.md#version-aware-compatibility) (the index of the
"Legacy behaviour" heading of each section),
[Validation rules](README.md#validation-rules) (the validation index),
[Considered and deliberately not added](changelog.md#considered-and-deliberately-not-added) and
[Reference examples](examples/README.md), with the provenance of each example in
[`inventory.yaml`](inventory.yaml).
The templates are [model intake](templates/model-intake.md) and
[change proposal](templates/change-proposal.md).

<!-- Copy from the next heading to the end of the "Sidecars" section into the exporter's AGENTS.md. -->

## Sidecars

### Where to read the spec

- Read the sidecar spec, the templates and the skills in the read-only worktree
  `../freemocap/skellytracker-latest`.
- That worktree is a detached checkout of the local skellytracker branch `dom/sidecar-latest`. It has
  the newest spec work. skellytracker moves the branch and the worktree after each push of spec work.
- Do not read the spec from the skellytracker working tree `../freemocap/skellytracker`. That tree is
  often on a feature branch.
- Do not read the spec from the skellytracker `development` branch. It does not have the newest spec
  work.
- Read the files as normal files. Then the relative links in the spec and in the skills resolve.
- If you think that the worktree is old, refresh it:
  `git -C ../freemocap/skellytracker-latest checkout --detach dom/sidecar-latest`.
  The worktree shares the branches of the skellytracker repo, so you do not need a fetch.
- If the folder `../freemocap/skellytracker-latest` or the branch `dom/sidecar-latest` does not exist,
  stop. Ask the user which skellytracker folder to read. Then read only that folder, and write its
  path in the header of the intake or the proposal.
- Get the commit of the spec text that you read:
  `git -C ../freemocap/skellytracker-latest rev-parse HEAD`. If you read another folder, use that
  folder in the command. Then run `git -C <folder> status --porcelain`. If it lists a file that you
  read, write `+ uncommitted changes` after the commit.
- Never edit a file in the worktree.
- Never commit to skellytracker.

| File | Use |
|---|---|
| `../freemocap/skellytracker-latest/specs/sidecar-spec.md` | The entry point of the spec. It is the permanent index: it keeps each old heading as an anchor with a link to the section file that holds the text now. |
| `../freemocap/skellytracker-latest/specs/sidecar/README.md` | The section map: each section ID and its file. It also has the validation index and the meaning of **(vNEXT)**. |
| `../freemocap/skellytracker-latest/specs/sidecar/format/`, `common/`, `pre/`, `post/` | The section files. They are the normative text of the spec. |
| `../freemocap/skellytracker-latest/specs/sidecar/changelog.md` | The `vNEXT` summary of changes, the table "Considered and deliberately not added" and the `schema_version` history. |
| `../freemocap/skellytracker-latest/specs/sidecar/examples/README.md` | The reference examples. They are not upstream evidence. |
| `../freemocap/skellytracker-latest/specs/sidecar/inventory.yaml` | The provenance of each reference example. |
| `../freemocap/skellytracker-latest/specs/sidecar/templates/model-intake.md` | The template for phase 1. |
| `../freemocap/skellytracker-latest/specs/sidecar/templates/change-proposal.md` | The template for phase 2. |
| `../freemocap/skellytracker-latest/.claude/skills/author-sidecar/SKILL.md` | The skill `author-sidecar`: the steps of phase 1 and of the reference-implementation step. |
| `../freemocap/skellytracker-latest/.claude/skills/propose-sidecar-change/SKILL.md` | The skill `propose-sidecar-change`: the steps of phase 2. |
| `../freemocap/skellytracker-latest/specs/sidecar/exporter-guide.md` | The source of this section. |
| `../freemocap/skellytracker-latest/specs/sidecar-implementation-plan.md` | The procedure that turns an exporter sidecar into a spec example ("Reference examples"). |
| `../freemocap/skellytracker-latest/notes/decisions/` | The skellytracker decision log. |
| `../freemocap/skellytracker-latest/skellytracker/` | The skellytracker package code. Read it for part 6 of a proposal. Do not import it. |

**Path bases.** A path that starts with `skellytracker/` or `specs/` names a file in the skellytracker
repo. Read it in `../freemocap/skellytracker-latest/`. A path that starts with `plans/` names a file
in the exporter repo. Both repos have a `notes/decisions/` folder. Thus always write the repo name with
the number of a decision entry, for example "skellytracker decision 0012" or "OpenMMLab-Exporter
0020". In a file of the exporter, a number without a repo name is a decision of that exporter.

**Decision entries.** The skellytracker decision entries are informative. They give the reasons and
the evidence for the rules. The spec is normative. Read skellytracker decision 0014 (the workflow)
before your first intake. When this section or a template cites another entry, read that entry if its
topic applies to your model.

**Section IDs.** The spec is split into section files under `specs/sidecar/`. `specs/sidecar-spec.md`
is the index. The section map `../freemocap/skellytracker-latest/specs/sidecar/README.md` lists each
section ID and its file. The section ID is the `id` in the front matter of the section file, for
example `pre.resize.letterbox`. Each validation rule has a rule ID in the form `V-<section-id>-<n>`,
for example `V-pre.resize.letterbox-1`. When this section names a spec heading, it also names the
section ID or the file that holds the heading.

**Vectors.** A test vector is a small worked case for the algorithm of one section. The vectors of a
section are in `../freemocap/skellytracker-latest/specs/sidecar/vectors/<section ID>.yaml`. If that
file does not exist, the section has no vectors.

**Reference examples are not evidence.** The reference examples of the spec
(`../freemocap/skellytracker-latest/specs/sidecar/examples/README.md`) show complete sidecars.
`../freemocap/skellytracker-latest/specs/sidecar/inventory.yaml` records the provenance of each
example. They are not upstream evidence. Do not copy a value from an example into the intake. After
you fill in every row, compare your values with the example of the same family, if one exists. Record
each difference in the intake.

**Links to the spec.** In a tracked file of the exporter, name the spec as `specs/sidecar-spec.md` of
the skellytracker repo. That file is the permanent entry point. The section map is
`specs/sidecar/README.md`. You can also name a section file under `specs/sidecar/`, for example
`specs/sidecar/pre/resize-letterbox.md`. Do not link to a URL of a branch. A branch URL breaks when
the branch moves or when someone deletes it. Do not link to the spec with a relative path into a
local skellytracker checkout. That path does not resolve on GitHub or in a different folder layout.
It also points into a working tree that is often on a feature branch. Name the spec in a code span:
`specs/sidecar-spec.md` of the skellytracker repo.

### Rules

- The spec is normative. Do not change its meaning in exporter docs or code.
- If a model property does not map exactly to the spec, do not use an approximate mapping. Write a
  change proposal (phase 2) and stop.
- Known case: an ROI refiner is a gap. An ROI refiner is a model that gives a region of interest to
  the next model, for example a hand re-crop model. Do not describe it as a pose estimator with two
  fake keypoints.
- The evidence for a row is an upstream file and line, an upstream config key, or a read of the ONNX
  graph (the command, and the node or tensor name). A plan, a paper, a README, the notes of an
  exporter and a spec reference example are secondary sources. Mark a secondary citation with
  `(secondary)`. A row that has only a secondary source is `unverified`. The next two bullets give
  the exceptions.
- A `near-miss` or a `gap` compares the property with the spec text. If only a secondary source shows
  the property, still give the row its `near-miss` or `gap` verdict. Mark the source `(secondary)`.
  Name the missing primary evidence in the row. The proposal of the row names it in part 1. Before
  the user accepts the proposal, part 1 must cite the primary evidence.
- A value that the exporter chooses has no upstream evidence. Examples are a name, a rule for the
  YAML file and a path. Judge its row against the spec only. Cite the exporter code that writes the
  value. If no such code exists, cite the exporter plan with `(secondary)`, or write
  `none yet (no code)`. Such a row is not `unverified` only because the code does not exist or you
  cannot read it. The model intake template lists these rows (heading "Verdicts").
- Do not publish a `vNEXT` sidecar to a shared or remote folder (see "Publishing").

### New-model workflow

Use this workflow for each new model. In an exporter repo, do phase 1 and phase 2. Then stop. A
skellytracker session does phase 3.

Two skills give the steps of phase 1 and phase 2. They use the rules of this section:

- `author-sidecar` (`../freemocap/skellytracker-latest/.claude/skills/author-sidecar/SKILL.md`):
  phase 1 and the reference-implementation step.
- `propose-sidecar-change`
  (`../freemocap/skellytracker-latest/.claude/skills/propose-sidecar-change/SKILL.md`): phase 2.

Read each skill file in the worktree. Do its steps in order.

**Files in `plans/`.** Write these files in the `plans/` folder of the exporter repo:

| File | Content |
|---|---|
| `plans/sidecar-intake-<model>.md` | The filled model intake template (phase 1). One file for each family. |
| `plans/sidecar-proposal-<slug>.md` | One change proposal for each gap (phase 2). |
| `plans/sidecar-reference-<section_module>.py` | One reference implementation for each section that you implemented on the host side (see "Reference implementations"). |

- `<model>` is the `model_id` of the family.
- `<slug>` is a short lowercase name of the proposed change, with hyphens, for example
  `letterbox-floor-rounding`.
- `<section_module>` names one section. "Reference implementations" gives the rule.
- Use these file names exactly. A skellytracker session finds the files with a scan of
  `plans/sidecar-*` in each exporter repo.
- `plans/` is a local folder. Do not commit the `plans/sidecar-*` files.
- Before you write a `plans/sidecar-*` file, look for it. If it exists, read it and update it in
  place. Do not overwrite a file that you did not read. Git does not track `plans/`, so you cannot
  undo an overwrite.
- When you stop, tell the user about each `plans/sidecar-*` file that no current intake or proposal
  owns. Do not delete it.

**Files that you commit.** Commit these files in the exporter repo: the sidecar writer code, the host
implementation of each section, and the parity scripts. The intake and the proposals cite their
commits.

**Inputs.** Get these inputs before you start:

- the ONNX files;
- the upstream inference config;
- the upstream preprocessing code and postprocessing code;
- one reference output of the upstream library on a known image.

If an input is missing, do not stop. Write `missing` for it in the intake. Use the best secondary
source for the rows that need the input, and give each of these rows the verdict `unverified`. A
`near-miss` row or a `gap` row can rest on a secondary source (see "Rules"). When you stop, tell the
user which inputs are missing.

**An exporter with no git repo.** If the exporter has no git repo yet, no commit exists:

- Write `none (no git repo)` in each commit cell.
- Write `to run` as each parity result. A script without a commit is not evidence.
- In a vector file, write `unverified: <reason>` in place of `verified_against`.
- The intake and the proposals are allowed, but they are not complete. Complete them when the
  exporter has a git repo and the commits exist.

#### Phase 1: can the current spec describe the model?

Fill `../freemocap/skellytracker-latest/specs/sidecar/templates/model-intake.md`. Write the result to
`plans/sidecar-intake-<model>.md`. The skill `author-sidecar` gives the order of the steps.

1. List every property of the runtime contract of the model. Use three sources:
   - the ONNX graph: each input and each output;
   - the upstream preprocessing pipeline: each transform step, in order;
   - the upstream postprocessing: each decode step, in order.

   An upstream step that does nothing for this model is also a row. The row gives the evidence that
   the step does nothing.

   The runtime contract starts at the inputs of the model: the source image, and the box for
   `affine_person_crop`. It ends at the decoded outputs in source-image coordinates. An upstream step
   before or after the contract is also a row, with the verdict `out of scope`.
2. For each row, write:
   - the property;
   - the upstream evidence (see "Rules");
   - the section ID (the `id` in the front matter of the section file);
   - the sidecar value;
   - a verdict.
3. Give each row one of these verdicts:
   - `exact`: the section describes the property with these values.
   - `near-miss`: the spec has a section and a field for the property, but no value describes the
     property exactly. A detail differs, for example the rounding, the pixel centres, the arithmetic
     precision, the order of steps or the threshold comparison. A detail that the spec does not define
     is also a near-miss when it changes the output for some input. A name or a path changes no
     tensor and no decoded output, so its row is never a `near-miss`.
   - `gap`: the spec has no section and no field for the property, for example a rotated crop, a
     border mode or a role for an ROI refiner. A property that the spec calls out of scope, or that the
     spec lists in "Considered and deliberately not added"
     (`../freemocap/skellytracker-latest/specs/sidecar/changelog.md`), is also a gap.
   - `unverified`: you do not have the evidence for a verdict. Name the missing evidence in the row. If
     you expect a verdict, write it there too.
   - `out of scope`: the step is before or after the runtime contract of this model. Examples: a step
     that makes the box from the outputs of another model, a gate that decides if the model runs, or a
     choice that uses an earlier frame.

   In each row that is not `exact`, write what differs or what is missing.

   To choose between `near-miss` and `gap`, find the section and the field that hold the property. If
   no section and no field hold it, the verdict is `gap`. If a field holds it but none of its values
   describes the upstream, the verdict is `near-miss`.
4. Continue as follows. A `near-miss` row or a `gap` row comes before an `unverified` row:
   - A `near-miss` or `gap` row: go to phase 2 for that row (the skill `propose-sidecar-change`). A
     near-miss is a gap. Do this also when other rows are `unverified`. List those rows in the final
     verdict.
   - An `unverified` row: get the missing evidence. Then give the row its verdict.
   - An `out of scope` row: write no proposal. Tell the user about the row when you stop. The user
     decides if the spec must describe such steps.
5. If no row is `near-miss` or `gap`:
   - The sidecar writer code of the exporter writes the sidecar (see "Sidecar YAML" and "Path"). Do
     not write the sidecar by hand.
   - If you cannot change the writer code yet, write the exact YAML in the section "The sidecar" of
     the intake. It is a draft. A skellytracker session does not use a draft as a spec example.
   - If a row is `unverified`, use the value that you expect for that row. Do not change the writer
     code for that row. Mark each result that depends on the row as provisional.
   - Walk the validation checklist (see "Validation").
   - Prove parity (see "Parity").
6. Write the final verdict:
   - `describes`: every row is `exact` or `out of scope`, and parity passes.
   - `does not describe`: a row is `near-miss` or `gap`, also when other rows are `unverified`.
   - `pending`: no row is `near-miss` or `gap`, but a row is `unverified` or parity is `to run`.

   If parity fails, you missed or misjudged a property. Go back to step 1 and find it. Until you find
   it, the verdict is `pending`. Do not make the tolerance larger to pass.

#### Parity

Parity compares the sidecar path with the upstream library on real images. Phase 1 (step 5) and
phase 2 (part 5) use these rules.

The sidecar path is the host implementation of each section in the exporter. It does the
preprocessing and the decode exactly as the sidecar declares. Write it from the spec text. In phase 2,
the reference implementation of the proposal replaces the missing spec feature.

- If a section has test vectors, your host implementation must pass them first.
- If a reference implementation of the section exists, use it or match it.
- If no reference implementation of the section exists, your plan must include the
  reference-implementation step (see "Reference implementations").

Do these steps:

1. Set the gate of each compared quantity before the run. Use the gate of the exporter (AP or OKS),
   or the numeric floor of the upstream, for example the float32 noise of the upstream computation.
   Record each gate and its source.
2. Choose the test images. Each branch of each section that the sidecar uses must run on at least
   one image. Calculate the branches from the formulas of the spec before you choose. For a resize,
   use source sizes where the scaled size has a fractional part below 0.5, above 0.5 and equal to
   0.5, a size with an odd pad gap, a portrait image, a landscape image, a downscale and an upscale.
   For a detector, use an image with no detection and an image with several detections. One image is
   not enough. Record the reason for each image.
3. Measure the export error. Give the tensor of the upstream preprocessing to the ONNX file. Compare
   its outputs with the outputs of the upstream model on the same tensor.
4. Compare the preprocessed input. Compare the tensor of the sidecar path with the tensor of the
   upstream preprocessing. Give the maximum absolute difference for each image. Expect 0. If it is
   not 0, find the cause and write it. If the cause is a property of the model or of the upstream
   code, the row of that property is not `exact`. If the cause is outside both (for example two
   different OpenCV versions), remove it, or give its maximum and its cause.
5. Compare the final outputs in source-image coordinates (after the unprojection):
   - the row count of each image;
   - for the `object_detector` role: the boxes, the scores and the classes, with box AP or per-row
     box differences;
   - for the `pose_estimator` role: the keypoints and the keypoint scores, with OKS or per-point
     differences.

   A model with both roles needs both comparisons. A keypoint metric does not check the boxes.
   Compare the result with the export error of step 3. The error above the export error comes from
   the sidecar path.
6. Commit the parity script in the exporter repo, so that a commit can be cited. A script that is
   only in the local `plans/` folder is not evidence. Use the folder of the exporter for evidence
   scripts. If the exporter has no such folder, use `notes/decisions/scripts/` (OpenMMLab-Exporter
   uses it).
7. If you cannot run the check, or if you cannot commit the script, write `to run` as the result.
   Give the reason. Describe the script and its gates. You can write the numbers of a run without a
   commit, but they are not evidence.

If the upstream has no Python API (for example, it runs only in C++), take the reference output from
the upstream runtime itself, for example from a build of the upstream that writes its tensors. Do not
use your own copy of the upstream algorithm as the reference. If you cannot run the upstream, the
result is `to run`.

#### Mapping hints for phase 1

- **Graph.** Record the input name, dtype, layout, and static or dynamic dims. Read the dims from the
  graph. A config name or a file name (for example "dynamic") is not evidence of the dims. Record the
  name, dtype and shape of each output. Record the batch of each file and the batch axis. Record the
  I/O dtype for each precision: fp16 files often keep float32 I/O. Look for normalization inside the
  graph (Sub, Div or Mul near the input). Look for NMS or TopK near the outputs. A step inside the
  graph is a row too.
- **NMS inside the graph.** The sidecar does not declare the NMS parameters of the graph, but they
  change the outputs. Record the IoU threshold, the score threshold and the row caps of the graph.
  Compare them with the upstream test config. A different value is an export defect: write it in the
  row.
- **Identity.** Record `model_id`, `display_name` and `role`. For an object detector, `model_id` is
  the family. Thus the folder name and the file name are the same, for example
  `object_detectors/rtmdet-person/rtmdet-person.yaml`. For a keypoint detector, `model_id` is
  `{family}-{part}`, for example `rtmw-wholebody` in `keypoint_detectors/rtmw/wholebody/`. The spec
  has no rule yet for a suffix after the part (the spec example `rtmo-body7`), or for two models of
  one family and one part. skellytracker decision 0025 (status `proposed`) records this question.
  Until the user decides it, the current text applies. A name changes no tensor and no decoded
  output, so the `model_id` row is never a `near-miss`:
  - Write `{family}-{part}` as the sidecar value. The verdict is `exact`. If the exporter or the spec
    example uses an id with a suffix, write that id and decision 0025 in the last column.
  - If another model of the same family and part also needs the id `{family}-{part}`, the current
    text has no id for your model. The row is a `gap`. Build on decision 0025 in phase 2.
  - If the spec has no `model_id` rule for the role of the model (a new role), the row is a `gap`.
    The proposal of the role covers it.
- **Family.** One family has one preprocessing contract and one post-processing contract. If two sizes
  need a different contract, they are two families (two sidecars). Name the files by the convention of
  the spec (the heading "File extension and naming" in
  `../freemocap/skellytracker-latest/specs/sidecar/format/file-layout.md`). The spec allows any
  lowercase token as a size name. Use the size name of the upstream, also for a family with one size.
  If the upstream has no size name, choose a token and write the reason in the intake.
- **Preprocessing.** For each value, record the upstream line behind it. If the "Authoring guidance"
  heading of a spec section has text, use it. Also record:
  - the dtype of the image when the upstream resizes it (for example uint8, before the cast);
  - the arithmetic of the scale, the scaled size and the offsets: float32 or float64, and the order of
    the operations. In float64, `77 * (640 / 77)` is `639.9999999999999`. Thus a rounding at an
    integer or at a tie can change the size;
  - the arithmetic of the normalization. In float32, `pixel / 255` and `pixel * (1 / 255)` differ in
    the last bit for 126 of the 256 byte values;
  - the pixel-centre convention of each resize call. `cv2.resize` uses half-pixel centres.
    `cv2.warpAffine` puts the pixel centres at integer coordinates. A 2x upscale of a ramp gives
    different values with the two calls. The spec text says "half-pixel centres" for both calls. That
    is a known spec defect (the skellytracker decision log lists it). Match the call that the spec
    names for the method. Record the convention of the upstream call in the intake;
  - the border value of each warp, for each channel. In OpenCV, a scalar `borderValue` fills only the
    first channel: `cv2.warpAffine(..., borderValue=114.0)` pads a 3-channel image with
    `[114, 0, 0]`. The spec does not say what a scalar `pad_value` fills for `fit` and
    `affine_person_crop`. That is a known spec defect (the skellytracker decision log lists it). For
    these two methods, give one value for each channel, for example `pad_value: [114, 114, 114]`.
    This form is `exact` under the current text. A scalar `0` gives the same border in both
    readings. A scalar is correct for `letterbox`, because the `letterbox` pseudocode fills every
    channel. The RTMO body7 reference example has the scalar `114` with `fit`, so it depends on the
    spec defect. In your host code, give `cv2.warpAffine` one value for each channel.
- **Outputs and decode.** Record the semantics of each output. Record the `selection`: graph-final
  rows (`none`), top-k over logits (`top_k`), or host NMS (`nms`). Record if the sigmoid is in the
  graph. Take the thresholds from the upstream test config, not from the defaults. Record the class
  IDs. Check `clamp_boxes` against the upstream: the default is `true`, so a sidecar without the field
  clamps the boxes. The spec clamps the boxes to the source-image bounds, but it does not say if the
  upper bound is `src_w` or `src_w - 1`. The spec also does not define the dtype of the score
  comparison. Record what the upstream does.
- **Pose.** Write `tracked_points` in native model output order. Record the connections, the decode
  method and the `landmark_schema`. For a bottom-up model, record how the pose rows align with the
  detection rows. The spec says that a packed keypoint `score` is already activated. The spec has no
  field for a keypoint-score activation. If the host must activate the keypoint scores, that is a gap.
- **Near-misses seen so far.**
  - A letterbox where the upstream code warps to a fractional size. That is `fit`, not `letterbox`
    (OpenMMLab-Exporter 0020).
  - A letterbox where the upstream code cuts the scaled size with `int()` or `floor`. The `rounding`
    field has no value for a cut. skellytracker decision 0023 (status `proposed`) proposes one.
  - An ROI refiner described as a pose estimator with two fake keypoints. That is a gap.

#### Phase 2: propose a spec change and its implementation

Write one proposal for each new or changed contract unit (one section). Fill
`../freemocap/skellytracker-latest/specs/sidecar/templates/change-proposal.md`. Write each proposal to
`plans/sidecar-proposal-<slug>.md`. The skill `propose-sidecar-change` gives the order of the steps.
The intake links to each proposal. Then stop.

Before you write a proposal:

- Read the table "Considered and deliberately not added" of the spec
  (`../freemocap/skellytracker-latest/specs/sidecar/changelog.md`). If your gap is in it, cite the
  row in part 1. Give the evidence that a model needs the feature now.
- Find the `proposed` entries of the skellytracker decision log that cover your rows. Read the index
  in `../freemocap/skellytracker-latest/notes/decisions/README.md`. Also read each `proposed` entry
  that the guidance of your sections cites. If an entry covers your rows, do not write a competing
  proposal:
  - Use the slug of the entry.
  - Cite the entry in the header and in part 1.
  - Add your evidence, your vectors and your parity plan.
  - If your rows need a different change, say where your proposal differs. Give the reason in part 8.
- An entry can be a gap record: its Decision section says so. A gap record gives the gap, the
  evidence and the direction of a change, but not all eight parts. Your proposal gives the parts
  that it does not have. A skellytracker session records your proposal as a new entry that extends
  the gap record.
- If a proposal needs another proposal (for example, a decode that uses the unprojection of a new
  crop), write the dependency in the header of each proposal. One parity script can serve several
  proposals. Cite it in part 5 of each.

A proposal has eight parts:

1. **Gap.** Give the property, its upstream evidence, and the reason why the nearest section is wrong.
   Show it with a number where possible. Example: a `center` letterbox in place of `fit` gives an
   input max abs diff of 35 on a 333×500 image (OpenMMLab-Exporter 0020).
2. **Spec change.** Write the exact normative text as it will appear in the spec:
   - the new or changed sections;
   - the fields table;
   - the behaviour, forward and inverse;
   - the validation rules, with new rule IDs;
   - the selectors;
   - the legacy behaviour and the effect on `schema_version`;
   - the changelog row.

   Also find each place that the change must edit. Search the spec for each closed set or list that
   the change extends, for example the `role` values, the `semantic` values, the resize methods, the
   storage layout (`format.file_layout`), the Overview, the section map and the validation index
   (`../freemocap/skellytracker-latest/specs/sidecar/README.md`), and the "Legacy behaviour" heading
   of each changed section with its index "Version-aware compatibility" (`format.versioning`). Also
   find each rule that names one of these values, for example the rule
   `V-pre.resize.affine_person_crop-2`: a sidecar with `pose.requires_object_detector: true` declares
   `input.resize.method: affine_person_crop`. List each place in the proposal. These edits are part
   of the same contract unit: a new role, with its enum and path edits, is one proposal. The
   proposed text can contain YAML excerpts. Do not write a sidecar file of the model with the
   proposed fields.
3. **Reference implementation.** Write the smallest functions that implement exactly the proposed
   text. Use only NumPy, OpenCV and the Python standard library. Write one function for each
   algorithm. Each docstring cites the proposed section ID. Write the code to
   `plans/sidecar-reference-<section_module>.py`. Make `<section_module>` from the proposed section
   ID. If the proposal changes a section that has no reference implementation, the file implements the
   full section as changed, not only the change. Then this file is also the reference-implementation
   step of that section. Name the file in the proposal. On acceptance, skellytracker adds it as
   `specs/sidecar/reference/<section_module>.py`. It is informative spec code, not package code. It is
   the single executable meaning of the new text. Your host decoder needs this behaviour, so the
   reference implementation is the clean, minimal form of your host code. If no host code exists
   yet, write the functions from the text of part 2. Write `source commit: none (no host code)` in
   the note at the top of the file. Part 4 is then `unverified: no host implementation`.
4. **Vectors.** A test vector is a small worked case: concrete inputs to the algorithm of one section,
   and the exact expected output. Use geometry and small arrays. Do not use images or ONNX files. Make
   the vectors with the reference implementation. Then verify them against your host implementation.
   Include a case for each branch, each tie and each strict comparison. If a parameter can be a scalar
   or one value for each channel (for example `pad_value`), include a case with a scalar value on a
   3-channel input. Pixel-exact resize output is out of scope. If you need a pixel case, state its
   tolerance in `compare`. Write the vectors in part 4 of the proposal, in the YAML form that the
   template gives. On acceptance, skellytracker adds them as
   `specs/sidecar/vectors/<section ID>.yaml`.
5. **Parity evidence.** Run the real model, with the reference implementation in place of the missing
   spec feature. Follow "Parity". Give the numbers, the script and the commit. If you cannot run the
   check yet, write `to run` and describe the script. A skellytracker session can record a proposal
   with `to run` as `proposed`. Before the user accepts the proposal, part 5 must give the numbers,
   the script and the commit.
6. **skellytracker implementation proposal.** skellytracker does not build it now. It builds it when
   it implements the spec. Write:
   - where the code goes: a module and a function under `skellytracker/core/detectors/processing/`,
     or a new module;
   - the dispatch point, for example a branch in `preprocess_image`
     (`skellytracker/core/detectors/processing/image_preprocessing.py`);
   - the validator changes in `skellytracker/core/sidecar/model.py`, with rule IDs;
   - the tests: the vectors, and a golden parity test;
   - the existing skellytracker code that the change touches.

   Read the package code in `../freemocap/skellytracker-latest/skellytracker/`. The template lists the
   code for each contract part. This part is advisory: the implementer checks it. If you cannot find
   a call site, write `for the implementer` and say what is not known. On acceptance, this text
   becomes the implementer guidance of the section and an open-work item.
7. **Exporter impact.** Name the exporters that must write new fields or regenerate sidecars. Describe
   the change to your own host decoder.
8. **Alternatives considered.** Include the near-miss, and the reason why you rejected it.

#### Phase 3: what skellytracker does next

You do not do phase 3. A skellytracker session does it. The user decides.

1. **A model with the verdict `describes`.** One non-spec PR (documentation only) in skellytracker
   adds the sidecar as a spec example (under `specs/sidecar/examples/`), with its provenance record
   (in `specs/sidecar/inventory.yaml`) and any new guidance from the intake. The procedure is
   "Reference examples" in `../freemocap/skellytracker-latest/specs/sidecar-implementation-plan.md`.
   Its preconditions: the exporter writes the sidecar itself (not by hand), at `vNEXT`, with no
   legacy-only fields; the checks of the exporter pass; parity passes for at least one size. The
   procedure copies your sidecar byte for byte. If your sidecar breaks a spec rule, fix the exporter
   or write a change proposal. Nobody corrects the example by hand.
2. **A proposal.** skellytracker records it as a decision entry with status `proposed`. The user
   accepts or rejects it. After acceptance:
   - A content PR adds the normative text, the changelog row, the vectors and the reference
     implementation. It sets the decision entry to `accepted` (if it is not accepted yet).
   - A non-spec PR (documentation only) adds the guidance, the implementation proposal (as
     implementer guidance and an open-work item), the example and its provenance record.
   - When skellytracker implements the spec, an implementation PR adds the code.
3. Then you write the sidecar with the new fields, and you finish phase 1 for the model.

### Reference implementations

If `../freemocap/skellytracker-latest/specs/sidecar/reference/` does not exist, no reference
implementation exists yet. Two things add a reference implementation:

1. an accepted proposal (phase 2, part 3);
2. an exporter that implements a section on its host side.

**Rule.** Your exporter plan can implement a sidecar section on the host side. Then the plan must
include a step that gives the reference implementation of that section to skellytracker. The rule
applies for every verdict of the intake.

- Skip the step if `../freemocap/skellytracker-latest/specs/sidecar/reference/<section_module>.py`
  exists.
- Skip the step if one of your proposals changes the section. The part 3 file of the proposal is the
  reference implementation. If the user rejects the proposal, do the step for the current text.
- A part of the spec without an algorithm needs no reference implementation, for example
  `input.layout`, `input.dtype` or `input.resize.method: none`.
- Do the step from committed host code. If the host code is not committed yet, or if it exists only
  in a plan, write `to run` in the intake. Do the step after the commit. This bullet is for a section
  of the current spec. For part 3 of a proposal, see phase 2.

**Module names.** For `<section_module>`, use the section ID from the front matter of the section file
(`id`), with each dot replaced by an underscore. For example, `pre.resize.letterbox` gives
`pre_resize_letterbox`. The section map `../freemocap/skellytracker-latest/specs/sidecar/README.md`
lists each section ID. For a new section, propose an ID in the same scheme
(`<format|common|pre|post>.<area>[.<name>]`). In a proposal, make `<section_module>` from the
proposed section ID.

- A resize method and its unprojection are one module, because the section file of the method gives
  the inverse with the forward algorithm (the heading "Inverse"). Do not put two sections together in
  one module.
- Write the section ID in the note at the top of the file.
- Python can import the skellytracker file `specs/sidecar/reference/<section_module>.py` by its name.
  The exporter file `plans/sidecar-reference-<section_module>.py` has hyphens in its name, so Python
  cannot import it by its name. Load it with `importlib.util.spec_from_file_location`, or run it as a
  script.
- The heading "Reference mappings in skellytracker" in
  `../freemocap/skellytracker-latest/specs/sidecar/post/canonical-mapping.md` (the old spec heading
  "Reference implementations" under `pose.canonical_mapping`) is about the canonical mapping files of
  the package. It is not about these files.

The step (the skill `author-sidecar` includes it):

1. Write the clean, minimal form of your host code. Use only NumPy, OpenCV and the Python standard
   library. Do not import from the exporter or from skellytracker. Write one function for each
   algorithm. In each docstring, cite the section ID and the exporter commit that the code comes
   from.
2. Run the functions against the vectors of the section (see "Vectors" in "Where to read the spec").
   They must pass. If the vector file says `unverified`, also run the vectors through your host
   code, and record both results. If the section has no vector file yet, record that.
3. Run the functions in place of your host code in the parity check of the exporter. Record that the
   result does not change. If you cannot run the parity check yet, write `to run`.
4. Write the functions to `plans/sidecar-reference-<section_module>.py` in the exporter repo. Put a
   short note at the top of the file: the section ID, the source commit, the vector results and the
   parity result.
5. Stop. A skellytracker session lands the file. It adds `specs/sidecar/reference/<section_module>.py`,
   adds the implementation to `verified_against` in the vector file of the section, and adds the
   exporter function to `external_impl` of the section.

If your host code and an existing reference implementation do not agree, you found a spec defect or a
bug. Write a proposal (phase 2). Do not write a second reference implementation. Two exporters can
write a file for the same section before skellytracker lands one. When skellytracker lands one of
them, this rule applies to the other exporter.

### Independence

- A reference implementation made from the code of an exporter is not independent of that exporter.
- In the `verified_against` list of a vector file, the reference implementation and its source
  exporter count as one implementation.
- Only exporters and skellytracker count as implementations in `verified_against`. Do not list the
  upstream library. The spec describes the upstream library, but the library does not implement the
  spec. If you ran a case through upstream code, write that in a comment in the vector file.
- A vector file without a verified implementation has `unverified: <reason>` in place of
  `verified_against`.
- A vector is fully verified only when at least two independent implementations agree: two exporters,
  or an exporter and skellytracker.
- A vector made only from a reading of the spec text is not verified.

### Sidecar YAML

- Quote the integer batch keys: write `"1":`, not `1:`. An unquoted key is a YAML integer, and schema
  validation rejects it.
- Set `schema_version` to the string `vNEXT` until the release step (see "Publishing"). YAML reads
  `vNEXT` and `"vNEXT"` as the same string, so both forms are correct. The spec examples use both
  forms.
- A size entry contains only `input.shape`, `input.resize.target_size` and `onnx`. All other fields
  are shared at the top level (the family invariant under the `sizes` heading in
  `../freemocap/skellytracker-latest/specs/sidecar/common/sizes-and-artifacts.md`, rule
  `V-common.sizes_and_artifacts-3`).
- Do not write `null` values. Omit an optional field. In the spec, `null` only deletes an inherited key
  in a `base` merge or a `sizes` merge.

### Path

Put the sidecar at its path in the storage layout of the spec (the heading "Storage layout" in
`../freemocap/skellytracker-latest/specs/sidecar/format/file-layout.md`). In the spec, the layout
starts at `{cache_dir}`. In an exporter, the export root has that role. Thus the
sidecar goes to `<export root>/detectors/...` (the export root of OpenMMLab-Exporter is `exports/`).

- `object_detectors/{family}/{model_id}.yaml` for an object detector. `{family}` is the `model_id`.
- `keypoint_detectors/{family}/{part}/{model_id}.yaml` for a pose estimator. `{part}` is `hand`,
  `face`, `body` or `wholebody`.

The spec does not say where a sidecar with both roles goes. The RTMO body7 reference example uses
`keypoint_detectors/`.

If the storage layout has no branch for the role of the model (a new role), row L1 of the intake is
a `gap`. The proposal that adds the role also adds the branch (`format.file_layout`).

A model-specific folder, such as `body7`, does not conform. For example, the RTMO body7 reference
example has the path `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` under
`../freemocap/skellytracker-latest/specs/sidecar/examples/`.

### Validation

- The validation rules are in the section files. Each section file has a "Validation rules" heading,
  and each rule there has a rule ID (`V-<section-id>-<n>`). The validation index is the heading
  "Validation rules" in `../freemocap/skellytracker-latest/specs/sidecar/README.md`. It links to the
  rules of each section, and it gives the meaning of **(vNEXT)**: a rule marked **(vNEXT)** applies
  only when `schema_version >= vNEXT`.
- Walk the "Validation rules" of every section that the sidecar uses.
- A `vNEXT` sidecar must pass every rule, also each rule marked **(vNEXT)**, except the two rules in
  the next bullet.
- `V-format.versioning-1` (the version pattern) and `V-format.versioning-2` (the support by the
  installed release), in `../freemocap/skellytracker-latest/specs/sidecar/format/versioning.md`,
  cannot pass for `vNEXT`. Record them as `n/a at vNEXT`. They apply after the release step (see
  "Publishing").
- Check the "Legacy behaviour" heading of each section that the sidecar uses, if the section has one.
  The index of these headings is "Version-aware compatibility" in
  `../freemocap/skellytracker-latest/specs/sidecar/format/versioning.md`. A `vNEXT` sidecar must not
  use a legacy-only form: `requires_nms` without `selection`, `may_include_non_person_classes`, or
  `letterbox` with `preserve_aspect_ratio: false`.
- Record the rule ID (`V-<section-id>-<n>`) of each rule that you checked in the intake.
- If a row of the intake is `near-miss` or `gap`, do not walk the checklist. Write `skipped`.
- If a row is `unverified` and no row is `near-miss` or `gap`, walk the checklist on the draft. Mark
  each result that depends on an `unverified` row as provisional.
- Run the exporter's own checks. Use a skellytracker sidecar checker only if the spec or this section
  names it.
- Do not use the skellytracker `load_sidecar` to check a `vNEXT` sidecar. It rejects `vNEXT` (see
  "Publishing").

### Publishing

- Do not publish a `vNEXT` sidecar to a shared or remote folder, for example a Hugging Face repo. Keep
  it in the exporter repo.
- The reason: `vNEXT` is not a version. It does not match the `schema_version` pattern
  `vYYYY.0M.BUILD[-TAG]`, so no skellytracker release can load it. (`load_sidecar` validates the
  sidecar with `SidecarModel`, which checks `schema_version` with `parse_skellytracker_version` in
  `skellytracker/core/sidecar/versioning.py`.)
- The release step: skellytracker cuts the first release that ships the spec. One change then replaces
  `vNEXT` with that release version in the spec, the changelog, every example and every vector.
- After the release step, regenerate your sidecars. Set `schema_version` to the skellytracker release
  that is current at export time (the exporter obligation under the heading "Semantics" in
  `../freemocap/skellytracker-latest/specs/sidecar/format/versioning.md`). Then you can publish them.
- A development build of skellytracker will load `vNEXT` sidecars. A release will not (skellytracker
  decision 0016).

### Coming: `source` and hashes (skellytracker decision 0016, accepted)

Until the spec defines `source`, use this list to plan the exporter overhaul. When the spec defines
`source`, follow the spec text.

- Every `vNEXT` sidecar will carry a top-level `source: {name, version}`. `name` is the package name
  of the exporter (for example `openmmlab-exporter`). `version` is the version of that package (for
  example `0.1.0`).
- `source.name: skellytracker` is reserved for the sidecars of the skellytracker package. Do not use
  it.
- Every `$ref`, every `base` and every `filename` artifact will carry a `sha256`. The hash covers the
  exact bytes of the target file.
- A `$ref` mapping will hold exactly `$ref` and `sha256`. A `base` will have the same `{$ref, sha256}`
  form. A skellytracker tool will fill in the hashes.
- Write the real hash of each ONNX file. A reserved placeholder (64 zeros) will be valid only in the
  spec examples.
- Sidecars and fragments will be UTF-8 without a BOM, with LF line endings. A CRLF file will fail.
- Until the spec defines `source`, a `vNEXT` sidecar without these fields is valid. When the spec
  defines `source`, regenerate your `vNEXT` sidecars with the fields.

<!-- End of the "Sidecars" section. -->

## Known open items for the exporter overhaul

These items are true on 2026-10-22. The overhaul plan of each exporter must handle them.

| Exporter | Item |
|---|---|
| OpenMMLab-Exporter | It implements these sections on its host side: the `letterbox` resize and the normalization (`onnx_runtime/preprocess.py`: `letterbox`, `make_normalizer`), `selection: nms` with the letterbox unprojection and the box clamp (`onnx_runtime/decode_nms.py`: `NmsDecoder`), and the `fit` resize (`notes/decisions/scripts/rtmo_sidecar_probe.py`: `fit_resize`, the parity probe of OpenMMLab-Exporter 0020). No reference implementation exists for these sections. The overhaul plan must include the [reference-implementation step](#reference-implementations) for each. |
| OpenMMLab-Exporter | It writes RTMO body7 to `detectors/keypoint_detectors/rtmo/body7/` (`rtmo/identity.py`: `FAMILY_BRANCH`). The part folders of the [storage layout](format/file-layout.md#storage-layout) are `hand`, `face`, `body` and `wholebody`. The overhaul moves the sidecar to `rtmo/body/`. |
| OpenMMLab-Exporter | `Readme.md` links to the spec with a branch URL (`blob/philip/sidecar_implementation/specs/sidecar-spec.md`). `notes/decisions/0009-detector-output-layout-and-decode.md` links to it with a relative path into a sibling checkout. The overhaul names `specs/sidecar-spec.md` of skellytracker in their place. |
| Roboflow-Exporter | It implements `selection: top_k` on its host side (`onnx_runtime/convert_rf_detr_coco.py`: `_select_topk_multiclass`), and the `stretch` resize (`onnx_runtime/preprocess.py`: `preprocess_to_nchw`). No reference implementation exists for these sections. The overhaul plan must include the reference-implementation step for each. |
| Roboflow-Exporter | The spec has no RF-DETR example. The `stretch`, `top_k` and `class_logits` rules have no example. The overhauled Roboflow-Exporter provides that example through the procedure "How to provide or replace an example" in [Reference examples](../sidecar-implementation-plan.md#reference-examples). |
| Ultralytics-Exporter | It writes `schema_version` `v2024.09.1019` (`yolo_sidecar.py`: `SCHEMA_VERSION`). So the YOLO26 [reference examples](examples/README.md) are written from its code, not copied from its exports (`kind: forecast` in [`inventory.yaml`](inventory.yaml)). They are replaced when it writes `vNEXT` sidecars. |
| Qualcomm-Exporter, MediaPipe-Exporter | The local hand plans (`Qualcomm-Exporter/plans/hand-pose-export.md` and `MediaPipe-Exporter/plans/hand-pipeline-export.md`) describe the hand re-crop model as `role: [pose_estimator]` with two points, `crop_center` and `crop_scale`. That is the two-keypoint workaround. An ROI refiner is a gap: the overhaul writes an intake and a change proposal in its place. MediaPipe-Exporter holds only that plan today, and it has no git repo (see "An exporter with no git repo" in [New-model workflow](#new-model-workflow)). |
