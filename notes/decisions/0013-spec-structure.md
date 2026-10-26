# 0013 — Spec structure: section files, rule owners, examples, reference implementations, traceability, STE

**Status:** absorbed into [`change-sidecar-spec/SKILL.md#rules-for-each-spec-edit`](../../.claude/skills/change-sidecar-spec/SKILL.md#rules-for-each-spec-edit), 2026-10-25 (user; the absorption review).

The spec is still one file, [`specs/model-sidecar/sidecar-spec.md`](../../specs/model-sidecar/sidecar-spec.md). This entry records
the structure that the split into section files makes. The split is a move change, and the rewrite in
Simplified Technical English (STE) is a rewording change. Each one is a separate PR
([0015](0015-review-discipline.md)).

## Decision

### Section files

- A move PR splits the spec into section files under `specs/sidecar/`. One file holds one contract
  unit: a part of the spec that has its own algorithm or its own implementing function.
- Each section has a stable section ID, for example `pre.resize.letterbox`,
  `post.det.selection.nms` or `post.pose.decode.simcc`. A text change does not change the ID.
- `specs/sidecar-spec.md` stays as the permanent entry point. After the split, it is a short index.
  It keeps each old heading as an anchor that links to the new file. Thus an existing link such as
  `specs/sidecar-spec.md#inputresize` still goes to the correct text.
- The split moves text only. It changes headings and links, adds front matter with only `id`,
  `title` and `kind`, and adds empty guidance headings. It does not change words.
- The PR that splits the spec also moves `specs/sidecar-spec-exporter-coverage-plan.md` to
  `notes/sidecar-exporter-coverage.md`. The file is evidence for the `vNEXT` changes. It is not spec
  text, and it is not a plan. The user decided this on 2026-10-22.

The layout after the split:

```text
specs/sidecar-spec.md            # permanent entry point: a short index -> specs/sidecar/README.md
specs/sidecar/
  README.md                      # map, reading order, section-ID index, terms, the word "must"
  TRACEABILITY.md                # generated; not edited by hand
  inventory.yaml                 # docs only: example provenance and proposed models
  changelog.md                   # schema_version history and the vNEXT summary of changes
  exporter-guide.md              # the rules that exporters follow
  format/                        # file layout, composition, versioning
  common/                        # identity, sizes and artifacts, batching, input, outputs
  pre/                           # one file for each resize method, interpolation, normalization
  post/                          # unprojection, detection outputs and decode, one file for each
                                 # selection, pose schema, canonical mapping, pose decode, overlay
  examples/detectors/...         # the reference examples, in the package's detectors/ layout
  vectors/<section-id>.yaml      # test vectors
  reference/<section_module>.py  # informative reference implementations
  templates/                     # model-intake.md, change-proposal.md
notes/sidecar-exporter-coverage.md  # evidence for vNEXT; moved from specs/sidecar-spec-exporter-coverage-plan.md
tools/                           # doc tools; the doc tests are in tools/tests/
```

### Section anatomy

Each section file starts with YAML front matter:

| Field | Meaning |
|-------|---------|
| `id` | The stable section ID. |
| `title` | The section title. |
| `kind` | `format`, `common`, `preprocessor`, `postprocessor` or `schema`. |
| `since` | The `schema_version` that added the section. |
| `changed_in` | Each `schema_version` that changed the meaning of the section. |
| `selectors` | The `key=value` pairs of a resolved sidecar that select the section, for example `input.resize.method=letterbox`. `format` and `common` sections apply to every sidecar. |
| `implemented_by` | The skellytracker functions, as `path::symbol`, under `validate`, `forward` and `inverse`. A part with no function is `missing`. |
| `external_impl` | Exporter host functions that implement the section. It stays empty until an exporter contributes. |
| `tests` | The skellytracker test files for the section. |
| `vectors` | The test vector file of the section. |
| `status` | One value for each of `spec`, `validate`, `forward` and `inverse`, for example `stable`, `partial` or `missing`. A part is `implemented` only when its vectors pass. |

An example of front matter (the values are illustrative):

```yaml
---
id: pre.resize.letterbox
title: Letterbox resize
kind: preprocessor
since: v2024.09.1019
changed_in: [vNEXT]
selectors: [input.resize.method=letterbox]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::ResizeSpec
  forward:  skellytracker/core/detectors/processing/image_preprocessing.py::letterbox_preprocess
  inverse:  missing
external_impl: []
tests: [skellytracker/tests/test_image_preprocessing.py]
vectors: vectors/pre.resize.letterbox.yaml
status: {spec: stable, validate: partial, forward: partial, inverse: missing}
---
```

The body has these headings, in this order:

| Heading | Kind of text |
|---------|--------------|
| Fields | normative |
| Behaviour | normative: the forward algorithm and its exact inverse |
| Validation rules | normative; each rule has an ID |
| Legacy behaviour (`schema_version < vNEXT`) | normative; only for sidecars older than `vNEXT` |
| Implementer guidance | informative: how to implement the section |
| Authoring guidance | informative: how to write a sidecar that uses the section |
| Examples | informative |

### One owner for each rule

- Each validation rule has one owning section and a rule ID: `V-<section-id>-<n>`, for example
  `V-pre.resize.letterbox-1`. The split gives each rule of the current validation checklist an ID
  and an owner.
- A rule that joins two sections is in the section of the field that it constrains. The other
  section links to it. Examples: role against output semantic; `requires_object_detector` against
  `affine_person_crop`; `packed_keypoints` against the pose decode.
- Each row of the [Version-aware compatibility](../../specs/model-sidecar/format/versioning.md#version-aware-compatibility)
  table moves into the section that it governs, under the "Legacy behaviour" heading.
  `format/versioning.md` keeps the version comparison rules and an index of these headings.

### Examples

- The reference examples belong to the spec. They are checked against the rules of the spec.
- After the split, each example is a file under `specs/sidecar/examples/`. The folders follow the
  package's `detectors/` layout, so that `$ref` paths resolve. The examples use copies of the shared
  skeleton fragments, under `specs/sidecar/examples/detectors/shared/skeletons/`.
- Each example has a provenance entry in `specs/sidecar/inventory.yaml`. The entry gives:
  - the source of the example;
  - the exporter;
  - the path of the exporter's copy;
  - its `kind`;
  - whether git tracks that copy;
  - the exporter commit of the code that writes it;
  - the edits made to the copy.
- `kind: export` is a copy of exporter output. `kind: forecast` is written from exporter code before
  the exporter writes that sidecar.
- Until the split, the provenance is one line of text above the YAML block of the example. The split
  moves these lines into `inventory.yaml`.
- `inventory.yaml` is docs only. skellytracker does not read it at run time. It is not the index of a
  remote sidecar folder ([0016](0016-sidecar-catalogs.md)). It holds only the data that a scan cannot
  find: the provenance of each example and the `proposed` models.
- The procedure to provide or replace an example is in
  [`specs/sidecar-implementation-plan.md`, "Reference examples"](../../specs/sidecar-implementation-plan.md#reference-examples).

### Reference implementations

- A reference implementation is informative spec code. It is the smallest function that implements
  exactly the text of one section. It uses only NumPy, OpenCV and the Python standard library, and
  it has no import from an exporter or from `skellytracker`. There is one function for each algorithm. Its docstring cites the
  section ID.
- The file is `specs/sidecar/reference/<section_module>.py`. `<section_module>` is the section ID with
  each dot replaced by an underscore, for example `pre_resize_letterbox`, so that the file can be
  imported.
- Only two things add a reference implementation: an accepted spec change proposal, and an exporter
  that implements a section on its host side and contributes the reference for it. The procedure is
  in [0014](0014-spec-lifecycle.md).
- There is no reference implementation yet.
- When an exporter's host code and an existing reference disagree, the exporter has found a spec
  defect or a bug. It writes a proposal. It does not write a second reference.
- `tools/tests` runs each reference function against the vectors of its section.

### Test vectors

- A test vector is a small worked case: concrete inputs to the algorithm of one section, and the exact
  expected output. There is one file for each section ID in `specs/sidecar/vectors/`. A file holds
  numbers only: no images and no ONNX files.
- Vectors are informative. A vector that disagrees with the normative text is a spec defect. A
  content PR corrects the vector or the text.
- A content change to a section updates its vectors in the same PR.
- Each vector file has `verified_against`, a list of the independent implementations that gave the
  same results, or `unverified: <reason>`. A vector that comes only from Claude's reading of the text
  is not verified. [0014](0014-spec-lifecycle.md) gives the independence rule.
- The generator `tools/make_vectors.py` computes the vectors from the normative formulas. When a
  section has a reference implementation, the generator calls it instead.
- Vector cases are geometry and small arrays. Pixel-exact resize output is out of scope, because it
  depends on OpenCV internals. A pixel case, if one is necessary, states a tolerance.

### Traceability

- The trace tool, `tools/sidecar_trace.py`, scans two roots for sidecars: the package
  (`skellytracker/core/detectors/`) and `specs/sidecar/examples/`. A YAML file is a sidecar when its
  top level has `schema_version` and a `model_id` equal to its file name without `.yaml`. The tool
  skips every other YAML file. This is the discovery rule of 0016. The tool uses it before the spec
  states it.
- The tool keys each sidecar as `<model_id>@<source>`, because one `model_id` can have two sources.
  It resolves composition with the existing `resolve_sidecar_composition`.
- The tool normalizes each resolved sidecar: it applies the spec's defaults and the derivations from
  legacy fields, for example `requires_nms: false` to `selection: none`. Then it matches the sidecar
  against the `selectors` of each section.
- The normalization and the selector matching are pure functions on the resolved dict. They have no
  import from `tools/` and use only the package's own dependencies. In the implementation stage, they
  move into `skellytracker/core/sidecar/` without changes. The trace tool then imports them, and the
  capability check of 0016 uses them.
- The tool writes `specs/sidecar/TRACEABILITY.md`: model against section; section to skellytracker
  functions to tests; section to exporter functions; and the `status` of each section. Nobody edits
  it by hand. The `implemented_by` entries that are `missing` are the backlog of the implementation
  stage.
- `impact <git-range>` lists the models, exporters, skellytracker functions, tests and vectors that a
  change affects.
- `examples` compares each example with its exporter's copy, through a sibling checkout. It writes to
  standard output only. CI does not run it, because CI has no exporter checkouts.
- Doc tests in `tools/tests/` run in CI: `pyproject.toml` lists `tools/tests` in `testpaths`, and the
  lint workflow checks `tools/` and `specs/sidecar/reference/`. The doc tests check these items:
  - The front matter is valid. Section IDs and rule IDs are unique. Each rule has one owner.
  - Each `implemented_by` path and symbol exists, or is `missing`. A PR that moves or renames a
    function named by `implemented_by` updates the front matter and `TRACEABILITY.md` in the same PR.
  - The selectors of the sections cover each `Literal` value in `skellytracker/core/sidecar/model.py`
    for `resize.method`, `normalization`, `semantic` and `pose.decode.method`.
  - Each relative link in `AGENTS.md`, `specs/` and `notes/` resolves, with its `#anchor`.
  - Each skeleton copy in the examples equals its package copy, and at least one example refers to
    it.
  - `TRACEABILITY.md` equals a new generation. The test compares text, with line endings normalized.
  - Each example parses and resolves. Each example has a provenance entry, and each entry names an
    existing example. Validation against `SidecarModel` waits for the implementation stage.
  - Each vector file has `verified_against` or `unverified`.
  - After the spec defines the hashes, `tools/sidecar_refs.py --check` passes on every example, and
    no file outside `specs/sidecar/examples/` holds the placeholder
    ([0016](0016-sidecar-catalogs.md)).
  - Each spec citation in a code docstring (`specs/sidecar-spec.md, "<heading>"`) names a heading
    that the permanent index still has.

### Rewrite in Simplified Technical English

- A rewording PR rewrites the spec text in ASD-STE100 Simplified Technical English, with the subset
  that OpenMMLab-Exporter uses: short sentences, the active voice, one instruction in each sentence.
  "must" is the requirement word. Technical names, field names, enum values, formulas, code and YAML
  stay unchanged.
- The rewrite comes after the split and the tooling. It has one commit for each batch of sections.
- Each section file passes four checks before review:
  1. **Invariant tokens** (`tools/check_ste_tokens.py`). The multiset of inline-code tokens,
     numbers, code blocks and table field, type and default cells is the same before and after. The
     tool lists each difference. The reviewing session must approve each one.
  2. **Claims list.** Two agents, each in a new context and neither of them the rewriter, list the
     normative claims of the old text: requirements, defaults, conditions, enums, algorithm steps and
     exceptions. The claims list is the union of the two lists. Each validation rule with an ID is
     also a claim.
  3. **Claims check.** A third agent in a new context quotes, for each claim, the sentence of the new
     text that states it, with a verdict: `same`, `changed` or `missing`. Then it lists the claims in
     the new text that the old text does not make. The reviewing session decides each item that is
     not `same`.
  4. **Clarity probe.** A fourth agent in a new context reads only the new text. It answers questions
     that have exact answers, taken from the vectors. Each answer must be correct. The rewriter
     rewrites the unclear text that causes a wrong answer. The old text gets the same questions. Its
     wrong answers are clarity defects that the rewrite must correct.
- A lint for sentence length and passive voice gives advice only.
- The rewrite PR includes the claims tables and the probe results.
- These parts are not rewritten: the existing changelog rows (they are a record), the YAML in
  `examples/` and `vectors/`, and quoted upstream code. New changelog rows are written in STE.

## Reason

- **A section of the single file has no ID and no metadata.** Thus "used by" and "implemented by"
  have no place to go, and nothing records which sections skellytracker implements. Front matter
  gives each section a place for this data, and the trace tool makes a backlog from it.
- **One feature touches many places.** The spec had `fit` in its summary of changes, and the code
  had `fit`, but the normative text did not. To write it, seven headings of the single file had to
  change ([0012](0012-fit-resize-for-rtmo.md)). With one owner for each rule and the legacy rows in
  their sections, a change to one section needs no edit in other sections. The `Literal` doc test
  finds a value that the code has and no section selects.
- **Examples are code blocks.** Nothing parses or checks them, so they can drift from the exporters
  and from the rules without an error. As files, the doc tests parse and resolve them, and the trace
  tool compares them with the exporter copies.
- **The sidecar cannot hold its provenance.** `SidecarModel` forbids extra keys, and the spec has no
  source field yet. Most exporter sidecars are build output that git does not track, so an exporter
  commit alone does not identify the file. `inventory.yaml` records the data that the file cannot
  hold.
- **There is no place for informative text.** How to implement and how to author a section is known
  only in the exporter repos. The guidance headings give that knowledge a place next to the rule it
  explains.
- **The single file is large.** An agent that changes NMS must read the full file to find the NMS
  text. One file for each contract unit lets an agent read only the sections that it changes.
- **Prose can be read in more than one way.** A reference implementation gives the text one
  executable meaning, and the vectors fix the edge cases (rounding ties, strict `>`, tie order). An
  exporter needs this behaviour for its own host decoder anyway, so the reference is the clean,
  minimal form of code that already passed a parity check. A reference written only from Claude's
  reading of the text has no implementation to agree with. Thus nobody writes a reference
  implementation until an accepted proposal adds one or an exporter contributes one.
- **A fourth reading of the rules must not exist.** The spec and `model.py` already state the rules.
  The trace tool's normalization is a third reading. If the capability check had its own copy, the
  copies could disagree. Thus the normalization and the selector matching are written once, so that
  they can move into the package without changes.
- **A rewrite can lose meaning without a sign.** Each of the four checks finds a different failure.
  The token check finds a changed value or name. Two independent claims lists make sure that one
  agent's omission does not hide a claim. The claims check finds a claim that changed or went
  missing. The clarity probe shows that a reader gets the exact answer from the new text.
- **Short sentences with one requirement each are easier to check.** Each requirement then maps to
  one claim. OpenMMLab-Exporter already writes its documentation in the same STE subset.

## Evidence

- `specs/sidecar-spec.md` has 1,625 lines and 106,300 bytes (2026-10-22). The detection `decode` and
  [Selection behaviour](../../specs/model-sidecar/post/detection-decode.md#selection-behaviour) headings, which hold the NMS
  rules, have 72 lines together.
- The `fit` spec text ([0012](0012-fit-resize-for-rtmo.md)) changed text under seven headings:
  [Compatibility impact](../../specs/model-sidecar/changelog.md#compatibility-impact),
  [`input.resize`](../../specs/model-sidecar/common/input.md#inputresize),
  [Unprojection](../../specs/model-sidecar/post/unprojection.md),
  [`sizes`](../../specs/model-sidecar/common/sizes-and-artifacts.md#sizes),
  [Version-aware compatibility](../../specs/model-sidecar/format/versioning.md#version-aware-compatibility),
  [Validation rules](../../specs/model-sidecar/README.md#validation-rules) and
  [Changelog](../../specs/model-sidecar/changelog.md#schema_version-history).
- `_StrictModel` in `skellytracker/core/sidecar/model.py` sets `extra="forbid"`, and `SidecarModel`
  has no `source` field.
- OpenMMLab-Exporter, Roboflow-Exporter and Ultralytics-Exporter list `exports/` in `.gitignore`.
  The RTMO body7 example comes from OpenMMLab-Exporter's tracked copy,
  `notes/decisions/rtmo-body7.yaml` ([Reference examples](../../specs/model-sidecar/examples/README.md)).
- A comparison on 2026-10-22 found that the RTMW example had drifted from its export, and that the
  YOLO26 examples are forecasts
  ([`specs/sidecar-implementation-plan.md`, "Reference examples"](../../specs/sidecar-implementation-plan.md#reference-examples)).
- OpenMMLab-Exporter has its own checker. `notes/decisions/scripts/rtmo_sidecar_probe.py` implements
  19 `vNEXT` rules again (OpenMMLab-Exporter 0020). Each such checker is one more reading of the
  rules.
- `rtmw-wholebody` has two sources: the package sidecar
  `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` and the
  OpenMMLab-Exporter export in the spec's examples.
- `tools/tests/test_links.py` runs the link check on `AGENTS.md`, `specs/` and `notes/`.

## Alternatives rejected

- **A hand-written model list.** The trace tool scans the folders for sidecars, so a list in
  `inventory.yaml` would only duplicate the scan and drift from it. `inventory.yaml` holds only what
  a scan cannot find.
- **`inventory.yaml` as a runtime catalog or as the index of a remote folder.** The catalog of 0016
  finds sidecars by the discovery rule, with no index file.
- **Provenance inside each sidecar.** `SidecarModel` forbids extra keys. The `source` field of 0016
  holds only the library name and version, not the copy's path, commit or edits.
- **Reference implementations written now.** skellytracker does not implement `vNEXT`, and the
  exporters are only partly built. There is no implementation to build them from or to verify them
  against.
- **A separate normalization table in the capability check.** It would be a fourth reading of the
  rules.

## Not repeated

- Do not state a rule in two sections. Put it in the section of the field that it constrains, and
  link to it.
- Do not edit `TRACEABILITY.md` by hand. Generate it again.
- Do not correct an example by hand. Correct the exporter, or write a spec change proposal.
- Do not mark a vector verified when it comes only from Claude's reading of the text.
- Do not change inline code, numbers or table cells in a rewording PR without an approved
  difference from the token check.
- Do not reword existing changelog rows.

_Edited 2026-10-26 (this PR): link repair._
