# Rules for each spec edit

This file is a part of the skill [`change-sidecar-spec`](SKILL.md).

## Spec structure

- Each section file under `specs/model-sidecar/` holds one part of the spec with its own algorithm or
  its own implementing function. One contract unit can change more than one section file
  ([Proposal forms](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#proposal-forms)).
- `specs/model-sidecar/README.md` is the only entry point of the spec. Its
  [section map](../../../specs/model-sidecar/README.md#section-map) gives each section ID and its
  file ([ADR-CN15](../../../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md)).
- `specs/model-sidecar/sidecar-spec.md` is frozen. Do not add a heading to it. Do not add a stub for
  a removed heading. Change it only to repair a link. Stage M11 of the
  [implementation plan](../../../specs/sidecar-implementation-plan.md) deletes it
  ([ADR-CN15](../../../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md)).
- `specs/model-sidecar/` holds `README.md` (the entry point: the section map, the reading order, the
  section-ID index and the terms), `TRACEABILITY.md` (generated), `inventory.yaml`, `changelog.md`, `format/`, `common/`,
  `pre/`, `post/`, `examples/detectors/`, `vectors/<section-id>.yaml`,
  `reference/<section_module>.py`, `templates/` and `model-addition-workflow/` (the process to add a
  model and to request a spec change; it is not a section). The draft exporter guide is in
  `specs/draft/exporter-guide/`. `notes/sidecar-exporter-coverage.md` is frozen evidence.
  It is not spec text. Do not add or remove a line in it.

## One algorithm in one place

- Write each algorithm in one section only.
- Put each rule in the section of the field that it constrains. The other sections link to it
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- Find each place that the change edits. Part 2 of the proposal lists these places. Examples are the
  closed sets that the change extends, the section map, the validation index and the rules that name
  a changed value.

## Rule IDs and section IDs

- Keep the section ID and the rule IDs of each section. A text change does not change an ID.
- A rule ID has the form `V-<section-id>-<n>`. It has no version part. Give a new rule the next free
  `<n>` of its section.
- A rule ID never shifts. A change that deletes a rule leaves its number unused, so the IDs of a
  section can have gaps. Do not renumber a rule
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- For a new section, propose the ID in the scheme `<format|common|pre|post>.<area>[.<name>]`. Add the
  section to the [section map](../../../specs/model-sidecar/README.md#section-map) and to the
  [validation index](../../../specs/model-sidecar/README.md#validation-rules).

## Front matter

- Each section file starts with YAML front matter. The docstring of
  [`FrontMatter`](../../../tools/sidecar_trace.py) gives its fields. `FrontMatter` checks them when
  `tools/sidecar_trace.py` loads the sections.
- The front matter has no `since` and no `changed_in`. The [changelog](../../../specs/model-sidecar/changelog.md)
  is the one record of the changes
  ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md) item 4).
- The body has these headings, in this order: Fields, Behaviour (the forward algorithm and its exact
  inverse), Validation rules, Implementer guidance, Authoring guidance, Examples. The first three are
  normative. The last three are informative.
- For a new section, set `external_impl: []`. Set each step of `implemented_by` to `missing`. Set each step of `status` to
  `missing`. Set `status.spec` to `draft`. Add the draft banner as the first body line after the
  title ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)).
- Change `selectors` when the change adds or removes a value that selects the section.
- A preprocessor has an `inverse` step only when the section has an "Inverse" heading.

## One reading

A spec change has no class ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 1).

- Each sidecar has one reading: the current text of the spec. Do not add a legacy reading, a
  "Legacy behaviour" heading, a version mark on a rule, an index row or an availability row
  ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md) item 1).

## `changelog.md`

- Add one row to the [summary of changes](../../../specs/model-sidecar/changelog.md#summary-of-changes).
- Append one line ``- Row N: `<fingerprint>`.`` under the open target heading of
  [Revisions](../../../specs/model-sidecar/changelog.md#revisions). `N` is the highest row of the
  summary of changes. Run `uv run pytest tools/tests/test_changelog_revision.py`. When the
  fingerprint is not current, the test fails and gives the new value. Do not bump the version
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md) item 4).
- Write new rows and lines in ASD-STE100. Do not reword the existing rows. Do not change an earlier
  line of Revisions.
- Do not reuse the number of a deleted row, because decided entries cite rows by number.
- The open target has the line `- Released: no.`. The session of the release sets
  `- Released: yes.` in the release PR ([procedure D](SKILL.md#procedure-d-another-spec-edit), a skellytracker
  release). A released version does not change.
- After a release, the next content change adds the heading of the version that the user bumps
  skellytracker to on `development`, with `- Released: no.`. It also adds the row of that version to
  the [`schema_version` history](../../../specs/model-sidecar/changelog.md#schema_version-history).
- The session of a skellytracker pre-release appends ``- Pre-release X.Y.Z-<tag>: row N.`` under the
  open target. `N` is the last row that the pre-release holds.

## The open target

- Each spec change and each proposal targets
  [the open target](../../../specs/model-sidecar/changelog.md#revisions): the next skellytracker
  release that includes a spec change ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- If a model that needs the change is not in
  [Scope of this revision](../../../specs/model-sidecar/changelog.md#scope-of-this-revision), add the
  model to the list in the non-spec commit of the change
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- Publish a sidecar only when the publish ban allows it
  ([Publishing](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)).

## Examples and vectors

- The reference examples belong to the spec. The doc tests check that each example parses, resolves and has provenance. No test runs the `V-` rules on them yet (see M7 of the [implementation plan](../../../specs/sidecar-implementation-plan.md)).
- Each example is a file under `specs/model-sidecar/examples/`, in the `detectors/` layout of the package,
  so that `$ref` paths resolve. The examples use unchanged copies of their fragments, under
  `specs/model-sidecar/examples/detectors/shared/` or next to the sidecar. Each fragment has an entry in
  `fragments` of `specs/model-sidecar/inventory.yaml` ([ADR-VV8B](../../../decisions/entries/VV8B-fragments-have-an-inventory-entry.md)).
- Each example has a provenance entry in `specs/model-sidecar/inventory.yaml`: its source, the exporter, the
  path of the exporter copy, its `kind`, whether git tracks that copy, the exporter commit of the code
  that writes it, and the edits made to the copy. `kind: export` is a copy of exporter output
  ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)).
- `inventory.yaml` is docs only. skellytracker does not read it at run time. It is not the index of a
  remote sidecar folder. It holds only the data that a scan cannot find: the provenance of each
  example and each fragment, and the `no_model` reasons.
- A test vector is a small worked case: concrete inputs to the algorithm of one section, and the exact
  expected output. There is one file for each section ID in `specs/model-sidecar/vectors/`. A file holds
  numbers only: no images and no ONNX files.
- Write a validator case in the vector file of the section that owns the rule
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md);
  [Section status](../../../specs/model-sidecar/README.md#section-status)).
- Vectors are informative. Vector cases are geometry and small arrays. Pixel-exact resize output is
  out of scope, because it depends on OpenCV internals. A pixel case, if one is necessary, states a
  tolerance.
- Each vector file has `verified_against`, the list of the independent implementations that gave the
  same results, or `unverified: <reason>`.
  [Independence](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)
  gives the implementations that count, and when a vector is fully verified
  ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).
- `tools/make_vectors.py` computes the vectors with the producer of each section. The producer is
  `specs/model-sidecar/reference/<section_module>.py` when it exists, else
  `tools/vector_formulas/<section_module>.py`. While a reference is the producer and the formula
  module has `run`, the two must agree within the tolerance
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- Each name in `checks` is `refused` or a key of `CHECKS` in
  `tools/vector_formulas/<section_module>.py`. An unknown name stops the generator. A case with an
  `error` result must list `refused`. Use `refused` only in such a case.
- `tools/make_vectors.py` writes `expect` in each file of `specs/model-sidecar/vectors/`. A person
  edits the other keys. Then the person runs `uv run python tools/make_vectors.py`. Do not edit
  `expect` by hand. The only exception is a validator case with `function: none`: its author writes
  its `expect`
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- The generator calls each case through `make_vectors.outcome`. `outcome` changes a `ValueError`
  into the `error` expect: the rule ID at the start of the message, or `no-rule`. A broken case or
  formula calls `vector_form.defect`. Its `CaseDefect`, and any other exception, stops the
  generator.
- The vectors of skellytracker and of a proposal use one form
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)). Part 4 of the
  [change proposal template](../../../specs/model-sidecar/templates/change-proposal.md#4-vectors)
  gives it. `tools/vector_form.py` checks it, and `tools/tests/test_vectors.py` runs that check: the
  top-level keys and the case keys and their order, a `note` in each `no-rule` case,
  `function: none` only with `failed`, different keys in `params` and `input`, a `function` that is
  in the producer, an error as a rule ID or `no-rule`, the check `refused` exactly in each `error`
  case, the rule IDs in `failed`, the place, `params` and `input` of each `<id>-inverse` case, NaN,
  and the entries of `verified_against`.
- A `verified_against` entry is a skellytracker function (`path::function`), which the test
  imports, or an exporter function (`{<Exporter repo>: <file>::<function>}`), which the test checks
  for its form only.
- A vector file must be 256 KiB or smaller. The limit applies to the file that
  `tools/make_vectors.py` writes, with the cases of each proposal for the section.
- A content change updates the vectors of its section in the same commit.
- A vector that does not agree with the normative text is a spec defect. Correct the text or the
  generator in a content commit.
- Do not mark a vector verified when it comes only from a reading of the text.
- Do not correct an example by hand. A spec-forced edit is not a correction. If a content change
  makes an example invalid, do the spec-forced edit in the same content commit
  ([When a spec change makes an example invalid](../../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid);
  [ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4). Do not land a
  content commit that leaves an example invalid. If a user ruling names the example, remove it with
  step 12 of that heading
  ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)).

## Reference implementations

- A reference implementation is informative spec code. It is the smallest function that implements
  exactly the text of one section. Its imports follow
  [Imports of other sections](../../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections). There is one
  function for each algorithm. Its docstring cites the section ID.
- A function or a value marked `Fixture of <section ID>` is temporary. It is not a second reference
  implementation. Replace it when the module of its section lands (procedure B, step 13).
- The file is `specs/model-sidecar/reference/<section_module>.py`. `<section_module>` is the section ID with
  each dot replaced by an underscore, for example `pre_resize_letterbox`.
- Only two things add a reference implementation: an accepted proposal (procedure B), and an exporter
  that implements a section on its host side and contributes it (procedure C).
- When the host code of an exporter and an existing reference disagree, the exporter writes a
  proposal. It does not write a second reference.
- `tools/tests` runs each reference function against the vectors of its section.

## Impact

1. Run `uv run python tools/sidecar_trace.py impact <GIT_RANGE>` on the change of the content commit
   only. Before you commit it, use `HEAD` for the uncommitted changes. After you commit it, use
   `<content commit>^..<content commit>`. Do not use a range that holds other commits.
2. Write the models, the exporters, the skellytracker functions, the tests and the vectors of the
   report in the PR body. In the spec-build stage, give the report to the user, and write a summary of
   it in the message of the last commit of the commit group.
3. Compare the report with the part 7 table of the proposal. An example that the change makes
   invalid and that part 7 does not list is a landing stop: the response is `needs-contributor`, and
   the contributor sends a follow-up bundle with the missing row
   ([When a spec change makes an example invalid](../../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid);
   [ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4).
   Name each exporter that must regenerate its sidecars. Do not add an item under
   [Re-export requests](../../../specs/model-sidecar/decisions/open-work.md#re-export-requests): the
   part 7 row is the request
   ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)).
4. Regenerate the traceability matrix with `uv run python tools/sidecar_trace.py matrix`. Do not edit
   `specs/model-sidecar/TRACEABILITY.md` by hand.

The trace tool scans only `specs/model-sidecar/examples/` for sidecars until the package migrates.
The package sidecars stay outside the spec until they migrate
([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 1).
The tool uses the discovery rule of
[`format.file_layout`](../../../specs/model-sidecar/format/file-layout.md#discovery). It keys each sidecar as
`<model_id>@<source>`, because one `model_id` can have two sources, and it resolves composition with
`resolve_sidecar_composition`. It normalizes each resolved sidecar with the spec defaults, and it
matches the sidecar against the `selectors` of each section.
The normalization and the selector matching are pure functions on the resolved dict. In the
implementation stage, they move into `skellytracker/core/sidecar/` without changes.
`TRACEABILITY.md` gives: model against section; section to skellytracker functions to tests; section
to exporter functions; and the `status` of each section. Each `implemented_by` entry that is
`missing` is backlog of the implementation stage. `sidecar_trace.py examples` compares each example
with its exporter copy through a sibling checkout. It writes to standard output only. CI does not run
it.

## Guidance

- Write guidance only under the "Implementer guidance" and "Authoring guidance" headings. Guidance is
  informative.
- Each statement must have a source: a repo, a file and a commit. Cite the primary evidence that the
  proposal names. If the proposal has only a secondary source, cite the recorded proposal and mark the
  statement `(secondary)`. Use the forms of
  [Sources](../../../specs/model-sidecar/model-addition-workflow/rules.md#sources)
  ([ADR-FDTD](../../../decisions/entries/FDTD-evidence-sources-and-exporter-permalinks.md)).
- If an exporter and the normative text do not agree, do not resolve it in the guidance. Record a
  `proposed` decision entry with [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md).

## Meaning check

Do these checks for each reworded section file
([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)):

1. Run `uv run python tools/check_ste_tokens.py --rev <REV> <FILE>`. It lists each change of the
   multiset of inline-code tokens, numbers, code blocks and the field, type and default cells of the
   tables. The reviewing session must approve each difference. Put the approved differences in an
   `--allow` file.
2. Get a claims list from two agents in new contexts. Neither agent is the rewriter. Each agent lists
   the normative claims of the old text: requirements, defaults, conditions, enums, algorithm steps
   and exceptions. The claims list is the union of the two lists. Each validation rule with an ID is
   also a claim.
3. Get a claims check from a third agent in a new context. For each claim, it quotes the sentence of
   the new text that states it, with a verdict: `same`, `changed` or `missing`. Then it lists the
   claims of the new text that the old text does not make. The reviewing session decides each item
   that is not `same`.
4. Get a clarity probe from a fourth agent in a new context. It reads only the new text, and it
   answers questions with exact answers from the vectors. Each answer must be correct. Rewrite the
   unclear text that causes a wrong answer. Ask the old text the same questions. Its wrong answers are
   clarity defects that the rewrite must correct.
5. Put the claims tables, the approved token differences and the probe results in the PR body. In
   the spec-build stage, give them to the user, and write a summary in the commit message.

Reword after the split and the tools, with one commit for each batch of sections. A lint for sentence
length and passive voice gives advice only. Do not reword the existing changelog rows, the YAML of
`examples/` and `vectors/`, or quoted upstream code.

## Stage

- In the spec-build stage, do not change a file under `skellytracker/`. A test fix in
  `skellytracker/tests/` is the only exception
  ([Stages](../../../specs/model-sidecar/model-addition-workflow/README.md#stages)).
  [Section 3](../../../AGENTS.md#3-install-and-test) of `AGENTS.md` gives the commit of a test or CI
  fix.
- Do not change an exporter repo.
