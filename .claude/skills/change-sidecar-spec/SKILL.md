---
name: change-sidecar-spec
description: Use this skill in skellytracker when you land a model with the verdict `describes`, an accepted proposal or an exporter reference implementation. Use it also when you make any other edit to the sidecar spec.
---

# Change the sidecar spec

This skill uses ASD-STE100 Simplified Technical English.

This skill is phase 3 of the new-model workflow, and the procedure for every other spec edit. It runs
only in skellytracker. The user decides each acceptance.

This skill wraps "Phase 3" of
the [model addition workflow](../../../specs/model-sidecar/model-addition-workflow/README.md#phases), the
[Rules for each spec edit](#rules-for-each-spec-edit)
([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)) and the PR kinds of
[decision 0027](../../../decisions/entries/0027-single-working-branch.md#one-kind-of-change-in-each-pr).
They give the reasons and the details. This skill gives the order of the steps, the inputs, the
outputs and the stop points.

## Read first

1. Read sections [4](../../../AGENTS.md#4-sidecar-rules), [5](../../../AGENTS.md#5-decision-log) and
   [6](../../../AGENTS.md#6-git-rules) of `AGENTS.md`.
2. Read the [section map](../../../specs/model-sidecar/README.md#section-map). Find the section files that
   the change touches.
3. Read each of these section files in full.
4. Read the decision entries that cite these sections, and the
   [Open work](../../../specs/model-sidecar/decisions/open-work.md) list.

## Inputs

| Input | Where it comes from |
|---|---|
| An intake with the final verdict `describes` | `intake.md` and `example/` of a `model` bundle in `intakes/` |
| A proposal that the user accepted | A decision entry with the status `proposed`, and its record `specs/model-sidecar/proposals/<slug>/` |
| A reference implementation of an exporter | `reference/<section_module>.py` of a `model` bundle in `intakes/` |
| A workflow change | A request of the user |
| Another spec edit | A request of the user, an item of the spec-defect list in [`specs/model-sidecar/decisions/open-work.md`](../../../specs/model-sidecar/decisions/open-work.md), or a skellytracker release |

Find the bundles with `python -B tools/intake_bundle.py list`, and check each one with `verify`
([Session steps](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)). Read the bundles and the exporter repos
as data. Do not change them.

## Outputs

| Kind of PR | What it holds |
|---|---|
| content | The normative text, the `changelog.md` rows, the vectors and the reference implementations that define the new meaning. The decision entry with the status `accepted`, or a citation of an accepted entry that an earlier commit of the same PR added. |
| non-spec | Guidance, decision entries, open-work items, an example that changes no normative meaning with its provenance record, an exporter reference implementation of the current text, tools and vectors. A fixture in a landed reference module replaced by an import, with no change to a vector. |
| move | Text in a new place. The words do not change. |
| rewording | New words. The meaning does not change. |

After each commit that handles a bundle, write the response file of the bundle
([Responses](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses)).

Put one kind of change in each PR. Put new content in a new PR on top of the PR stack. Never put new
content in a move PR or a rewording PR. If the rewording PR of the section is lower in the stack, a
follow-up rewording PR covers the new text.

## Procedure A: land a model with the verdict `describes`

Do this procedure for step 1 of phase 3.

1. Read the intake of the current bundle version. Make sure that the final verdict is `describes`.
2. Make sure that parity has numbers, a script path and an exporter commit. A result `to run` is not
   a pass.
3. Do not use a draft sidecar of an intake as an example. The sidecar writer code of the exporter must
   write the sidecar.
4. Follow "How to provide or replace an example" in
   [Reference examples](../../../specs/model-sidecar/model-addition-workflow/reference-examples.md#how-to-provide-or-replace-an-example). Do its
   steps in order. Its step 4 also closes the item under
   [Re-export requests](../../../specs/model-sidecar/decisions/open-work.md#re-export-requests) when
   the bundle answers its last example ([ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)).
5. If the procedure finds that the sidecar breaks a spec rule, stop. Do not correct the example by
   hand. Tell the user that the exporter must change, or that the spec needs a proposal.
6. Add the new guidance of the intake to the "Authoring guidance" heading of each section that it is
   about. Do the steps of [Guidance](#guidance).
7. Land `vector-runs.yaml` of the bundle
   ([Payload](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#payload)). Do this
   step also for a `model` bundle of another verdict, and for a bundle of procedure C. For each item
   of `runs`:
   - Make sure that `vectors_sha256` is the SHA-256 of the current
     `specs/model-sidecar/vectors/<section>.yaml`. If it is not, ignore the run. The response is
     `needs-contributor`: run the cases again.
   - With `result: pass` and each value of `cases` `pass`, add `{<Exporter repo>: <function>}` to
     the file-level `verified_against` of the vector file of the section. If only some cases pass,
     add the entry to those cases only.
   - Skip the run when the exporter is already in the list, or when it is the source of the landed
     reference module. The two count as one implementation
     ([Independence](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)).
   - With `result: fail`, stop and tell the user. A failed case is a spec defect or a host bug. It
     needs a proposal.
   - Run `uv run python tools/make_vectors.py`. Do not edit `expect` by hand.
8. If the model is not in
   [Scope of this revision](../../../specs/model-sidecar/changelog.md#scope-of-this-revision), add
   the model to the list in the same PR
   ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
9. Run the [checks](#checks).
10. Put the example, its provenance record, the guidance, the vector entries and the list change in
    one non-spec PR.

## Procedure B: land an accepted proposal

Do this procedure for step 2 of phase 3.

1. Make sure that the user accepted the proposal. If the user has not decided, stop. If the record
   is not the current version of its bundle, stop and record the new version first (skill
   `propose-sidecar-change`,
   [Record a new version](../propose-sidecar-change/SKILL.md#record-a-new-version)). Each `base`
   proposal and each `depends_on` proposal must be landed: its entry is `accepted` and its content
   commit is on the working branch. Or it lands in the same content commit. If one is
   neither, stop. Land the base first. A rejected base gives the response `needs-contributor`
   ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)).
2. Make the content PR. Do steps 3 to 12.
3. Find the section that owns each rule. Do the steps of [Rules for each spec edit](#rules-for-each-spec-edit).
4. Write the normative text of part 2 of the proposal into the section files. Take the text from
   `specs/model-sidecar/proposals/<slug>/proposal.md`. Apply each part 2 edit to the current text. If
   the quoted anchor text is not in the current text, stop. The response is `needs-contributor`:
   the contributor sends a follow-up bundle, not a new version
   ([Read a response](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#read-a-response)).
5. Write the `changelog.md` row and the `Row` line ([`changelog.md`](#changelogmd)).
6. Before the copy, do the [safety review](#safety-review) of each file. Copy each file in
   `specs/model-sidecar/proposals/<slug>/reference/` to
   `specs/model-sidecar/reference/<section_module>.py`. There is one file for each changed section
   that has an algorithm. For each file: if the target file exists, compare the two files. Each
   difference of behaviour must come from part 2. If the file starts from an older base, stop. The
   response is `needs-contributor`, with a follow-up bundle as in step 4. Find each
   module that a file imports. Each such module must be in `specs/model-sidecar/reference/` or be a
   file that this step copies. If one is not there, stop. Land that module first.
7. Step 7 has no action. The generator runs each reference on each case of its section, and
   `test_file_equals_the_generator_output` checks the result
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
8. The generator uses the copied module. If the change alters the text that a formula module in
   `tools/vector_formulas/` reads, update its `run` in the same content commit. Alternatively, delete
   its `run`, keep its `CHECKS` and give the reason in the decision entry
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
9. Land the vectors of each changed section with this command. It must pass.

   ```sh
   uv run python tools/make_vectors.py land specs/model-sidecar/proposals/<slug>/vectors/<section ID>.yaml [--contribution <contribution record file>...] --replaces [<id>...]
   ```

   Give `--contribution` for the vector file of the section in each contribution record of the
   proposal. Give `--replaces` each `id` that part 4 lists as a replaced case. The tool keeps the
   current cases, puts a part 4 case in the place of the case with its `id` and puts each other new
   case at the end. The tool runs the landed producer and checks the form, the cases, the given
   `expect` and the 256 KiB limit. It writes `specs/model-sidecar/vectors/<section ID>.yaml` only
   when each check passes. If it prints a problem, stop and tell the user. This check proves the
   copy and the generator wiring. It does not verify an independent implementation
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md), item 5).
   `land` puts each `verified_against` entry of the current file, of part 4 and of the
   contributions on the cases that it covers. An entry of the current file does not cover a
   replaced case. An entry that covers each case goes in the file-level `verified_against`. Do not
   add these entries by hand
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)). If the package
   test then fails on a new or replaced case, add the skellytracker entry to that case.
10. Change the status line of the decision entry from `proposed` to `accepted`. Write the date and the
    PR ([Rules](../../../decisions/README.md#rules)). Move its row from the Proposed table to
    the end of the Active table of the [spec log](../../../specs/model-sidecar/decisions/README.md),
    without the Section cell. The entry status is the state of the proposal. No other file holds it
    ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)). Write each `proposed`
    superseding entry of the proposal as `accepted`, and supersede its old entry. Make only
    editorial fixes at acceptance ([Changes at acceptance](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#changes-at-acceptance)).
    Write each plan decision that the user confirmed in the Decision section of the entry. Write it
    in words. Do not cite its item number
    ([User decisions](../../../specs/model-sidecar/model-addition-workflow/rules.md#user-decisions);
    [ADR-FDTD](../../../decisions/entries/FDTD-evidence-sources-and-exporter-permalinks.md)).
11. If the change corrects an item of the spec-defect list in
    [`specs/model-sidecar/decisions/open-work.md`](../../../specs/model-sidecar/decisions/open-work.md), remove the item.
12. Run the [impact](#impact) and the [checks](#checks).
13. Make the non-spec PR on top of the content PR. Do steps 14 to 18. In it, replace the fixtures of
    each section that the content PR lands:
    - Search `specs/model-sidecar/reference/` for `Fixture of <section ID>` of that section.
    - Replace each fixture with an import and a call through the module name.
    - Run `uv run python tools/make_vectors.py --check`. It must pass. If it does not pass, the
      fixture and the module do not agree. Stop and tell the user.
14. Write part 6 of the proposal as the "Implementer guidance" of the section.
15. Add an item for part 6 to the [implementation plan](../../../specs/sidecar-implementation-plan.md),
    in the not-started stage that it belongs to. If no stage fits, add a new stage before the
    release stage
    ([ADR-5WKW](../../../decisions/entries/5WKW-implementation-work-in-the-plan.md)).
16. Add the "Authoring guidance" from the intake. Do the steps of [Guidance](#guidance).
17. If a model that needs the change is not in
    [Scope of this revision](../../../specs/model-sidecar/changelog.md#scope-of-this-revision), add
    the model to the list ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
18. When the exporter writes the sidecar with the new fields, add the example with procedure A.
    When the last commit of the proposal lands, write the response `landed` for each bundle of the
    proposal. Then do [procedure E](#procedure-e-resolve-a-proposal-by-a-different-change)
    for each other open proposal on the same sections.
19. In the implementation stage, implement the section with the skill
    [`implement-sidecar-section`](../implement-sidecar-section/SKILL.md).

## Procedure C: land a reference implementation of an exporter

Do this procedure when a `model` bundle holds a `reference/<section_module>.py` file. Follow
[Reference implementations](../../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations)
and [Independence](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)
in the model addition workflow.

If part 3 of a proposal bundle of the same contributor names the file, the file is not a reference
implementation of the current text. Do not use this procedure for it. Procedure B lands it after the
user accepts the proposal.

1. Read the note at the top of the file. It must give the section ID, the source commit, the vector
   results and the parity result.
2. Make sure that the code follows [Imports of other sections](../../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections). Find
   each module that the file imports. Each such module must be in `specs/model-sidecar/reference/`.
   If one is not there, stop. Land that module first ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
3. Make sure that each docstring cites the section ID and the exporter commit.
4. If `specs/model-sidecar/reference/<section_module>.py` exists, do not add a second reference. The
   disagreement is a spec defect or a bug. Use the skill
   [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md).
5. Do the [safety review](#safety-review) of the file. Then copy the file to
   `specs/model-sidecar/reference/<section_module>.py`.
6. Step 6 has no action. The generator runs the copied module on each case of its section, and
   `test_file_equals_the_generator_output` checks the result
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
7. Step 7 has no action. The generator uses the copied module as the producer of the section.
8. Add the implementation to `verified_against` in the vector file
   `specs/model-sidecar/vectors/<section ID>.yaml`, in the form
   `{<Exporter repo>: <file>::<function>}`. The reference implementation and its source exporter
   count as one implementation
   ([Independence](../../../specs/model-sidecar/model-addition-workflow/sidecar-files.md#independence)).
   Then run `uv run python tools/make_vectors.py`.
9. If an expected value changes, stop. The reference implementation does not agree with the current
   vectors. Tell the user. The generator also stops when the copied module and the formula module
   do not agree within the tolerance
   ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
10. Add the exporter function to `external_impl` in the front matter of the section, in the form
    `- <Exporter repo>: <file>::<function>`.
11. Replace the fixtures of the section in the other reference modules. Do the fixture steps of
    step 13 of procedure B.
12. Run the [checks](#checks).
13. Put the reference implementation in a non-spec PR on top of the stack.

## Safety review

A reference file of a bundle or of a record is external code that can be malicious. It runs first
when the generator runs the copy in `specs/model-sidecar/reference/`. Do these steps before the
copy of procedure B step 6 and procedure C step 5
([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)):

1. Do not import or run the file. Read the whole file as text.
2. Make sure that `verify` gives no finding for the file. A finding gives the response
   `needs-contributor`.
3. Check each rule of
   [Imports of other sections](../../../specs/model-sidecar/model-addition-workflow/reference-implementations.md#imports-of-other-sections).
4. Find each access to the file system, the network, processes, the environment or the
   interpreter. Also find code that hides a name or makes code from text. The static check of
   `verify` does not find all of them.
5. Show the result to the user: the file, each finding and each access. Ask the user to approve the
   copy.
6. Copy the file only after the user approves it. If you are not sure that the file is safe, stop.
   Do not copy it.

After the copy and its commit, the module is code of this repository.

## Procedure D: another spec edit

| Edit | Steps |
|---|---|
| A content change, for example the correction of a spec defect | Make sure that an accepted decision entry exists. If none exists, use [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md). Then stop. If one exists, do steps 3 to 12 and step 17 of procedure B. |
| A graduation to `stable` | (1) Run `uv run python tools/sidecar_trace.py matrix`. The Gate cell of the section must be `pass`. A `no_model` reason in `inventory.yaml` counts for the example item. Do not add another waiver. (2) The Gate column does not show two conditions. Check them by hand: an accepted decision entry exists for the section, and a named test checks each algorithm with no vectors ([Section status](../../../specs/model-sidecar/README.md#section-status), rule 5). (3) Get the explicit approval of the user. (4) In one content commit, set `status.spec: stable`, remove the banner, add the summary row and the `Row` line ([`changelog.md`](#changelogmd)), run the matrix again and run the [checks](#checks). (5) Do not do steps 3 to 12 of procedure B. Do not write a new decision entry. Cite the accepted entry of the section in the commit message ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)). |
| A skellytracker release | [Publishing](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing) gives it. First, find each section with `status.spec: draft`. If one exists, stop and tell the user. The user makes the section `stable` or removes its fields from the release ([Section status](../../../specs/model-sidecar/README.md#section-status), rule 7). Also stop and tell the user when an example or a package sidecar has `batching.batch_conversion` and the `validate` or `load` status of `common.batch_conversion` is not `implemented` ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)). These two checks are stops of the `2.0.0` release ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)). Also stop and tell the user when the SemVer loader of stage M8 of the [implementation plan](../../../specs/sidecar-implementation-plan.md) has not landed: the `2.0.0` release ships it ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md) item 4). Then, in the release PR, set `- Released: yes.` under the version heading of the release in [Revisions](../../../specs/model-sidecar/changelog.md#revisions). If the release ships under another number, rename the unreleased heading and change `schema_version` in each example in the same PR ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). |
| A workflow change | The user asks for it ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)). Write the change in one non-spec commit with a decision entry that gives the reason ([Workflow changes](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#workflow-changes)). The entry is `accepted` in that commit. When the change changes the [Rules](../../../decisions/README.md#rules), change the kit in the same commit: run `uv run python tools/sync_bootstrap_kit.py --write` (it writes the copies and the blocks), and change the rest of the kit templates by hand ([ADR-Z05A](../../../decisions/entries/Z05A-essential-decision-log-rules.md)). |
| A rewording | Do the [meaning check](#meaning-check). Change no meaning. |
| A move | Change no words. Keep the section IDs and the rule IDs. |

## Procedure E: resolve a proposal by a different change

Do this procedure when a content commit lands on a section that another open proposal also changes
([Responses](../../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses);
[ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)).

1. Find the open proposals on the sections of the commit. Read the manifest `sections` of each
   record in `specs/model-sidecar/proposals/`, and the Section cell of the Proposed table of the
   [spec log](../../../specs/model-sidecar/decisions/README.md#proposed). List only the proposals
   whose entry is `proposed`. Also run `python -B tools/intake_bundle.py list` and find the open
   `proposal` bundles on these sections that have no entry.
2. Tell the user about each one. Stop. The user decides: `rejected`, `resolved-otherwise` or keep it
   open.
3. For `resolved-otherwise`, the landed change must be a different proposal bundle with its own
   accepted entry `<X>`. A session never writes that entry itself.
4. Change the status line of the `proposed` entry to `rejected`, with the date and `PR: pending`
   until a PR exists. Write the Reason "Resolved by [ADR-<X>](<path of X>)", with a relative path
   ([ADR-Z05A](../../../decisions/entries/Z05A-essential-decision-log-rules.md)). Move its row to the
   historical table of the [spec log](../../../specs/model-sidecar/decisions/README.md) in the same commit
   ([Rules](../../../decisions/README.md#rules)). The `rejected` entry is the state. The response
   `resolved-otherwise` is a notice of it
   ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)).
5. Write the response `resolved-otherwise` with `resolution`: `by`, `sections`, one row of `goals`
   for each goal of part 1 and each change of part 2, and `contributor_action`. Close each
   contribution of the proposal.
6. Put these edits in one non-spec commit. End its subject with `(ADR-<ID>)` of the rejected entry.
   This procedure changes no Rules and no kit file.

## Rules for each spec edit

### Spec structure

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

### One algorithm in one place

- Write each algorithm in one section only.
- Put each rule in the section of the field that it constrains. The other sections link to it
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- Find each place that the change edits. Part 2 of the proposal lists these places. Examples are the
  closed sets that the change extends, the section map, the validation index and the rules that name
  a changed value.

### Rule IDs and section IDs

- Keep the section ID and the rule IDs of each section. A text change does not change an ID.
- A rule ID has the form `V-<section-id>-<n>`. It has no version part. Give a new rule the next free
  `<n>` of its section.
- A rule ID never shifts. A change that deletes a rule leaves its number unused, so the IDs of a
  section can have gaps. Do not renumber a rule
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). The
  renumbering of [ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md) item 5 applied only
  to the cleanup before version `2.0.0`. It is history.
- For a new section, propose the ID in the scheme `<format|common|pre|post>.<area>[.<name>]`. Add the
  section to the [section map](../../../specs/model-sidecar/README.md#section-map) and to the
  [validation index](../../../specs/model-sidecar/README.md#validation-rules).

### Front matter

- Each section file starts with YAML front matter with these fields.
  [`FrontMatter`](../../../tools/sidecar_trace.py) checks them when `tools/sidecar_trace.py` loads
  the sections.

  | Field | Meaning |
  |-------|---------|
  | `id` | The stable section ID. |
  | `title` | The section title. |
  | `kind` | `format`, `common`, `preprocessor`, `postprocessor` or `schema`. |
  | `selectors` | The `key=value` pairs of a resolved sidecar that select the section, for example `input.resize.method=letterbox`. A `format` or `common` section with `selectors: []` applies to every sidecar. A `common` section that is one optional key has one selector for that key, for example `batching.batch_conversion` ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)). |
  | `implemented_by` | The skellytracker functions, as `path::symbol`, under each step of the kind. A `format`, `common` or `schema` section has `validate` and `load`. A `preprocessor` has `validate`, `forward` and an optional `inverse`. A `postprocessor` has `validate` and `decode`. [`FrontMatter`](../../../tools/sidecar_trace.py) gives the steps. A step with no function is `missing`. |
  | `external_impl` | Exporter host functions that implement the section. It stays empty until an exporter contributes. |
  | `tests` | The skellytracker test files for the section. |
  | `vectors` | The test vector file of the section. |
  | `status` | One value for `spec` and one value for each step of `implemented_by`. `spec` is `stable` or `draft`. [Section status](../../../specs/model-sidecar/README.md#section-status) gives the rules of `draft` and the graduation to `stable` ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)). A step is `implemented`, `partial` or `missing`. A step is `implemented` only when its vectors pass. |

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

### One reading

A spec change has no class ([ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)).

- Each sidecar has one reading: the current text of the spec. Do not add a legacy reading, a
  "Legacy behaviour" heading, a version mark on a rule, an index row or an availability row
  ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md) item 1).

### `changelog.md`

- Add one row to the [summary of changes](../../../specs/model-sidecar/changelog.md#summary-of-changes).
- Append one line ``- Row N: `<fingerprint>`.`` under the open target heading of
  [Revisions](../../../specs/model-sidecar/changelog.md#revisions). `N` is the highest row of the
  summary of changes. Run `uv run pytest tools/tests/test_changelog_revision.py`. When the
  fingerprint is not current, the test fails and gives the new value. Do not bump the version
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md) item 4).
- Write new rows and lines in ASD-STE100. Do not reword the existing rows. Do not change an earlier
  line of Revisions.
- Two content commits of the cleanup before version `2.0.0` were exceptions to these rules. They are
  history. The commit of [ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md) deleted the
  legacy rows. Their numbers stay unused, because decided entries cite rows by number. The commit of
  [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md) turned the
  revision `1.0` into the heading `### 2.0.0` and its row 30 line.
- The open target has the line `- Released: no.`. The session of the release sets
  `- Released: yes.` in the release PR ([procedure D](#procedure-d-another-spec-edit), a skellytracker
  release). A released version does not change.
- After a release, the next content change adds the heading of the version that the user bumps
  skellytracker to on `development`, with `- Released: no.`. It also adds the row of that version to
  the [`schema_version` history](../../../specs/model-sidecar/changelog.md#schema_version-history).
- The session of a skellytracker pre-release appends ``- Pre-release X.Y.Z-<tag>: row N.`` under the
  open target. `N` is the last row that the pre-release holds.

### The open target

- Each spec change and each proposal targets the open target: the next skellytracker release that
  includes a spec change. The open target is `2.0.0`
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- If a model that needs the change is not in
  [Scope of this revision](../../../specs/model-sidecar/changelog.md#scope-of-this-revision), add the
  model to the list in the non-spec PR of the change
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- Do not publish a sidecar to a shared or remote sidecar root until a final skellytracker release
  loads its `schema_version`. The private test repo of the implementation stage is the one exception
  ([Authoring guidance](../../../specs/model-sidecar/format/versioning.md#authoring-guidance);
  [Publishing](../../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing)).
  The frozen package rejects `"2.0.0"` until stage M8 of the
  [implementation plan](../../../specs/sidecar-implementation-plan.md).

### Examples and vectors

- The reference examples belong to the spec. The doc tests check that each example parses, resolves and has provenance. No test runs the `V-` rules on them yet (see M7 of the [implementation plan](../../../specs/sidecar-implementation-plan.md)).
- Each example is a file under `specs/model-sidecar/examples/`, in the `detectors/` layout of the package,
  so that `$ref` paths resolve. The examples use unchanged copies of their fragments, under
  `specs/model-sidecar/examples/detectors/shared/` or next to the sidecar. A fragment has one source:
  a package copy with the same bytes, or a `fragments` entry in `specs/model-sidecar/inventory.yaml`
  (ADR-[yve0](../../../decisions/entries/yve0-example-fragments.md)).
- Each example has a provenance entry in `specs/model-sidecar/inventory.yaml`: its source, the exporter, the
  path of the exporter copy, its `kind`, whether git tracks that copy, the exporter commit of the code
  that writes it, and the edits made to the copy. `kind: export` is a copy of exporter output.
  `kind: forecast` is written from exporter code before the exporter writes that sidecar.
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
- A content change updates the vectors of its section in the same PR.
- A vector that does not agree with the normative text is a spec defect. Correct the text or the
  generator in a content PR.
- Do not mark a vector verified when it comes only from a reading of the text.
- Do not correct an example by hand. A spec-forced edit is not a correction. If a content change
  makes an example invalid, do the spec-forced edit in the same content commit
  ([When a spec change makes an example invalid](../../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid);
  [ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)). Do not land a
  content commit that leaves an example invalid.

### Reference implementations

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

### Impact

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
   [ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)).
   Name each exporter that must regenerate its sidecars. Do not add an item under
   [Re-export requests](../../../specs/model-sidecar/decisions/open-work.md#re-export-requests): its
   one item covers each example, and after it closes, the part 7 row is the request
   ([ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)).
4. Regenerate the traceability matrix with `uv run python tools/sidecar_trace.py matrix`. Do not edit
   `specs/model-sidecar/TRACEABILITY.md` by hand.

The trace tool scans only `specs/model-sidecar/examples/` for sidecars until the package migrates.
The package sidecars stay outside the spec until they migrate
([ADR-NB5F](../../../decisions/entries/NB5F-no-change-classes-and-one-re-export-request.md)).
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

### Guidance

- Write guidance only under the "Implementer guidance" and "Authoring guidance" headings. Guidance is
  informative.
- Each statement must have a source: a repo, a file and a commit. Cite the primary evidence that the
  proposal names. If the proposal has only a secondary source, cite the recorded proposal and mark the
  statement `(secondary)`. Use the forms of
  [Sources](../../../specs/model-sidecar/model-addition-workflow/rules.md#sources)
  ([ADR-FDTD](../../../decisions/entries/FDTD-evidence-sources-and-exporter-permalinks.md)).
- If an exporter and the normative text do not agree, do not resolve it in the guidance. Record a
  `proposed` decision entry with [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md).

### Meaning check

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

### Simplified Technical English

- Write all new text in ASD-STE100. Use short sentences. Use the active voice. Use one instruction in
  each sentence.
- Use "must" for a requirement.
- Keep technical names, field names, enum values, formulas, code and YAML unchanged.

### Stage

- In the spec-build stage, do not change a file under `skellytracker/`. A test fix in
  `skellytracker/tests/` is the only exception
  ([Stages](../../../specs/model-sidecar/model-addition-workflow/README.md#stages)).
- Do not change an exporter repo.

## Checks

The doc tests in `tools/tests/` run in CI: `pyproject.toml` lists `tools/tests` in `testpaths`, and
the lint workflow checks `tools/` and `specs/model-sidecar/reference/`. They check these items:

- The front matter is valid. Section IDs and rule IDs are unique. Each rule has one owner.
- Each `implemented_by` path and symbol exists, or is `missing`. A PR that moves or renames a function
  named by `implemented_by` updates the front matter and `TRACEABILITY.md` in the same PR.
- The selectors of the sections cover each `Literal` value in `skellytracker/core/sidecar/model.py`
  for `resize.method`, `normalization`, `semantic` and `pose.decode.method`. The check skips
  `imagenet_bgr` and `imagenet_rgb` (`MERGED_IMAGENET_MODES` in `tools/tests/test_traceability.py`)
  and asks for the merged mode `imagenet`. The frozen `model.py` keeps the old values until stage M8
  of the [implementation plan](../../../specs/sidecar-implementation-plan.md)
  ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- Each relative link in `AGENTS.md`, `decisions/`, `specs/` and `notes/` resolves, with its `#anchor`.
- Each skeleton copy in the examples equals its package copy, and at least one example refers to it.
- `TRACEABILITY.md` equals a new generation, with line endings normalized.
- Each example parses and resolves. Each example has a provenance entry, and each entry names an
  existing example.
- Each vector file has `verified_against` or `unverified`.
- After the spec defines the hashes, `tools/sidecar_refs.py --check` passes on every example.
- Each spec citation in a code docstring (`specs/model-sidecar/sidecar-spec.md, "<heading>"`) names a heading of
  the frozen index. Stage M11 of the implementation plan deletes the index. Then the test checks
  section IDs ([ADR-CN15](../../../decisions/entries/CN15-spec-readme-is-the-only-entry-point.md)).

Run these commands before each PR. Each command must pass.

1. `uv run python tools/make_vectors.py --check`
2. `uv run python tools/sidecar_trace.py matrix --check`
3. `uv run pytest tools/tests -q`. It also runs the private-data check
   ([Private data](../../../AGENTS.md#8-private-data)).
4. `uv run pytest -m "not video"`
5. `uv run ruff check skellytracker/ tools/ decisions/scripts/`. When `specs/model-sidecar/reference/`
   exists, add it to the command.

## Stop points

| Condition | Action |
|---|---|
| The user has not accepted the proposal. | Stop. Do not change the normative text. |
| A content change has no accepted decision entry. | Use `propose-sidecar-change`. Then stop. |
| An example breaks a spec rule, and no accepted change in this commit gives a spec-forced edit for it. | Stop. Do not correct the example. Tell the user. |
| A new reference implementation changes an expected vector value. | Stop. Tell the user. |
| The [safety review](#safety-review) of a reference file has a doubt, or the user has not approved the copy. | Stop. Do not copy or run the file ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)). |
| The Gate of a `draft` section is not `pass`, or the user has not approved the graduation. | Stop. Do not change `status.spec`. |
| A content commit lands on a section with another open proposal. | Stop. The user decides the outcome of that proposal (procedure E). |
| The PR is ready. | Ask the user before the push ([section 6](../../../AGENTS.md#6-git-rules) of `AGENTS.md`). |
