---
name: change-sidecar-spec
description: Use this skill in skellytracker when you land a model with the verdict `describes`, an accepted proposal or an exporter reference implementation. Use it also when you make any other edit to the sidecar spec.
---

# Change the sidecar spec

This skill uses ASD-STE100 Simplified Technical English.

This skill is phase 3 of the new-model workflow, and the procedure for every other spec edit. It runs
only in skellytracker. The user decides each acceptance.

This skill wraps "Phase 3" of
[decision 0014](../../../notes/decisions/0014-spec-lifecycle.md#new-model-workflow), the structure of
[decision 0013](../../../notes/decisions/0013-spec-structure.md) and the PR kinds of
[decision 0027](../../../notes/decisions/0027-single-working-branch.md#one-kind-of-change-in-each-pr).
They give the reasons and the details. This skill gives the order of the steps, the inputs, the
outputs and the stop points.

## Read first

1. Read sections [4](../../../AGENTS.md#4-sidecar-rules), [5](../../../AGENTS.md#5-decision-log) and
   [6](../../../AGENTS.md#6-git-rules) of `AGENTS.md`.
2. Read the [section map](../../../specs/sidecar/README.md#section-map). Find the section files that
   the change touches.
3. Read each of these section files in full.
4. Read the decision entries that cite these sections, and the
   [Open work](../../../notes/decisions/open-work.md) list.

## Inputs

| Input | Where it comes from |
|---|---|
| An intake with the final verdict `describes` | `plans/sidecar-intake-<model>.md` in an exporter repo |
| A proposal that the user accepted | A decision entry with the status `proposed`, and its proposal file `specs/sidecar/proposals/<slug>/proposal.md` ([faac](../../../notes/decisions/faac-proposal-records.md)) |
| A reference implementation of an exporter | `plans/sidecar-reference-<section_module>.py` in an exporter repo |
| Another spec edit | A request of the user, an item of the spec-defect list in [`notes/decisions/open-work.md`](../../../notes/decisions/open-work.md), or the release step |

Find the exporter files with a scan of `../../*-Exporter/plans/sidecar-*` from the root of the
skellytracker repo. Read the exporter repos. Do not change them.

## Outputs

| Kind of PR | What it holds |
|---|---|
| content | The normative text, the `changelog.md` rows, the vectors and the reference implementations that define the new meaning. The decision entry with the status `accepted`. |
| non-spec | Guidance, decision entries, open-work items, an example that changes no normative meaning with its provenance record, an exporter reference implementation of the current text, tools and vectors. |
| move | Text in a new place. The words do not change. |
| rewording | New words. The meaning does not change. |

Put one kind of change in each PR. Put new content in a new PR on top of the PR stack. Never put new
content in a move PR or a rewording PR. If the rewording PR of the section is lower in the stack, a
follow-up rewording PR covers the new text.

## Procedure A: land a model with the verdict `describes`

Do this procedure for step 1 of phase 3.

1. Read the intake. Make sure that the final verdict is `describes`.
2. Make sure that parity has numbers, a script path and an exporter commit. A result `to run` is not
   a pass.
3. Do not use a draft sidecar of an intake as an example. The sidecar writer code of the exporter must
   write the sidecar.
4. Follow "How to provide or replace an example" in
   [Reference examples](../../../specs/sidecar-implementation-plan.md#reference-examples). Do its
   steps in order.
5. If the procedure finds that the sidecar breaks a spec rule, stop. Do not correct the example by
   hand. Tell the user that the exporter must change, or that the spec needs a proposal.
6. Add the new guidance of the intake to the "Authoring guidance" heading of each section that it is
   about. Do the steps of [Guidance](#guidance).
7. Run the [checks](#checks).
8. Put the example, its provenance record and the guidance in one non-spec PR.

## Procedure B: land an accepted proposal

Do this procedure for step 2 of phase 3.

1. Make sure that the user accepted the proposal. If the user has not decided, stop.
2. Make the content PR. Do steps 3 to 12.
3. Find the section that owns each rule. Do the steps of [Rules for each spec edit](#rules-for-each-spec-edit).
4. Write the normative text of part 2 of the proposal into the section files. Take the text from
   `specs/sidecar/proposals/<slug>/proposal.md`. If the exporter proposal changed after the copy,
   stop. Tell the user, and record the new version first (skill
   [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md)).
5. Write the `changelog.md` rows.
6. Copy the reference implementation of part 3 to `specs/sidecar/reference/<section_module>.py`.
7. If `tools/tests` has no test that runs the reference functions against the vectors of their
   section, add that test in the same PR.
8. Make the generator `tools/make_vectors.py` call the reference implementation for the section.
   Remove the formula version of that section from the generator.
9. Write the vectors with `uv run python tools/make_vectors.py`. Do not edit a vector file by hand.
10. Change the status line of the decision entry from `proposed` to `accepted`. Write the date and the
    PR ([Rules](../../../notes/decisions/README.md#rules)). Move its row from the Proposed table to
    the end of the Active table, without the Section cell. Set `state: accepted` in the front matter
    of `proposal.md` and in the proposal index. Write each `proposed` superseding entry of the
    proposal as `accepted`, and supersede its old entry.
11. If the change corrects an item of the spec-defect list in
    [`notes/decisions/open-work.md`](../../../notes/decisions/open-work.md), remove the item.
12. Run the [impact](#impact) and the [checks](#checks).
13. Make the non-spec PR on top of the content PR. Do steps 14 to 17.
14. Write part 6 of the proposal as the "Implementer guidance" of the section.
15. Add an item for part 6 to the [Open work](../../../notes/decisions/open-work.md) list.
16. Add the "Authoring guidance" from the intake. Do the steps of [Guidance](#guidance).
17. When the exporter writes the sidecar with the new fields, add the example with procedure A. Remove
    the `proposed` entry of the model from `specs/sidecar/inventory.yaml`, if it has one.
    Set `state: landed` in `proposal.md` and in the proposal index when the last PR of the proposal
    lands.
18. In the implementation stage, implement the section with the skill
    [`implement-sidecar-section`](../implement-sidecar-section/SKILL.md).

## Procedure C: land a reference implementation of an exporter

Do this procedure when the scan finds a `plans/sidecar-reference-<section_module>.py` file. Follow
"Reference implementations" and "Independence" of
[decision 0014](../../../notes/decisions/0014-spec-lifecycle.md#reference-implementations-from-exporters).

If part 3 of a proposal in the same exporter repo names the file, the file is not a reference
implementation of the current text. Do not use this procedure for it. Procedure B lands it after the
user accepts the proposal.

1. Read the note at the top of the file. It must give the section ID, the source commit, the vector
   results and the parity result.
2. Make sure that the code uses only NumPy, OpenCV and the Python standard library. It must not
   import from the exporter or from skellytracker.
3. Make sure that each docstring cites the section ID and the exporter commit.
4. If `specs/sidecar/reference/<section_module>.py` exists, do not add a second reference. The
   disagreement is a spec defect or a bug. Use the skill
   [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md).
5. Copy the file to `specs/sidecar/reference/<section_module>.py`.
6. If `tools/tests` has no test that runs the reference functions against the vectors of their
   section, add that test in the same PR.
7. Make the generator `tools/make_vectors.py` call the reference implementation for the section.
   Remove the formula version of that section from the generator.
8. Add the implementation to `verified_against` in the generator. The reference implementation and
   its source exporter count as one implementation.
9. Write the vectors with `uv run python tools/make_vectors.py`. If an expected value changes, stop.
   The reference implementation does not agree with the current vectors. Tell the user.
10. Add the exporter function to `external_impl` in the front matter of the section, in the form
    `- <Exporter repo>: <file>::<function>`.
11. Run the [checks](#checks).
12. Put the reference implementation in a non-spec PR on top of the stack.

## Procedure D: another spec edit

| Edit | Steps |
|---|---|
| A content change, for example the correction of a spec defect | Make sure that an accepted decision entry exists. If none exists, use [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md). Then stop. If one exists, do steps 3 to 12 of procedure B. |
| The release step | Decision [0014](../../../notes/decisions/0014-spec-lifecycle.md#release-step) decides it. In one content PR, replace `vNEXT` with the release version. Do this in the spec, in `changelog.md`, in each example and in the `spec_revision` of each vector file. Then the exporters regenerate their sidecars. |
| A rewording | Do the [meaning check](#meaning-check). Change no meaning. |
| A move | Change no words. Keep the section IDs and the rule IDs. |

## Rules for each spec edit

### One algorithm in one place

- Write each algorithm in one section only.
- Put each rule in the section of the field that it constrains. The other sections link to it
  ([One owner for each rule](../../../notes/decisions/0013-spec-structure.md#one-owner-for-each-rule)).
- Find each place that the change edits. Part 2 of the proposal lists these places. Examples are the
  closed sets that the change extends, the section map, the validation index and the rules that name
  a changed value.

### Rule IDs and section IDs

- Keep the section ID and the rule IDs of each section. A text change does not change an ID.
- A rule ID has the form `V-<section-id>-<n>`. Give a new rule the next free `<n>` of its section.
- Mark a rule that applies only from `vNEXT` with **(vNEXT)**.
- For a new section, propose the ID in the scheme `<format|common|pre|post>.<area>[.<name>]`. Add the
  section to the [section map](../../../specs/sidecar/README.md#section-map) and to the
  [validation index](../../../specs/sidecar/README.md#validation-rules).

### Front matter

- Use the fields of [Section anatomy](../../../notes/decisions/0013-spec-structure.md#section-anatomy).
  The doc tests in `tools/tests/test_traceability.py` check them.
- For a new section, set `since` to the version of the change (`vNEXT` in the spec-build stage). Set
  `external_impl: []`. Set each step of `implemented_by` to `missing`. Set each step of `status` to
  `missing`.
- For a changed meaning, add the version of the change to `changed_in`.
- Change `selectors` when the change adds or removes a value that selects the section.
- A preprocessor has an `inverse` step only when the section has an "Inverse" heading.

### Legacy behaviour

- The meaning of an older `schema_version` never changes.
- Write each legacy difference in the "Legacy behaviour" heading of the section.
- If a section gets a new "Legacy behaviour" heading, add it to the index in
  [Version-aware compatibility](../../../specs/sidecar/format/versioning.md#version-aware-compatibility).

### `changelog.md`

- Add one row to the [summary of changes](../../../specs/sidecar/changelog.md#summary-of-changes).
- Add the change to the `vNEXT` row of the
  [`schema_version` history](../../../specs/sidecar/changelog.md#schema_version-history).
- Write new rows in ASD-STE100. Do not reword the existing rows.

### `vNEXT` or a release version

- In the spec-build stage, every spec change goes into the `vNEXT` revision.
- From the first skellytracker release that ships the spec, a change sets `schema_version` to the
  release that ships it. The change also adds a row to the `schema_version` history
  ([Versions](../../../notes/decisions/0014-spec-lifecycle.md#versions)).
- Do not publish a `vNEXT` sidecar to a shared or remote folder. `load_sidecar` rejects `vNEXT`.

### Examples and vectors

- A content change updates the vectors of its section in the same PR.
- A vector that does not agree with the normative text is a spec defect. Correct the text or the
  generator in a content PR.
- Do not mark a vector verified when it comes only from a reading of the text.
- Do not correct an example by hand. If the change makes an example invalid, list the example and its
  exporter in the PR body. The exporter regenerates the sidecar. Then procedure A replaces the
  example.

### Impact

1. Run `uv run python tools/sidecar_trace.py impact <GIT_RANGE>`. For the commits of the branch, use
   `<parent>..HEAD`, where `<parent>` is the branch of the PR below. For uncommitted changes, use
   `HEAD`.
2. Write the models, the exporters, the skellytracker functions, the tests and the vectors of the
   report in the PR body.
3. Name each exporter that must regenerate its sidecars.
4. Regenerate the traceability matrix with `uv run python tools/sidecar_trace.py matrix`. Do not edit
   `specs/sidecar/TRACEABILITY.md` by hand.

### Guidance

- Write guidance only under the "Implementer guidance" and "Authoring guidance" headings. Guidance is
  informative.
- Each statement must have a source: a repo, a file and a commit.
- If an exporter and the normative text do not agree, do not resolve it in the guidance. Record a
  `proposed` decision entry with [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md).

### Meaning check

Do these checks for each reworded section file
([Rewrite in Simplified Technical English](../../../notes/decisions/0013-spec-structure.md#rewrite-in-simplified-technical-english)):

1. Run `uv run python tools/check_ste_tokens.py --rev <REV> <FILE>`. The user must approve each
   difference. Put the approved differences in an `--allow` file.
2. Get a claims list from two agents in new contexts. Neither agent is the rewriter.
3. Get a claims check from a third agent in a new context.
4. Get a clarity probe from a fourth agent in a new context, with questions from the vectors.
5. Put the claims tables and the probe results in the PR body.

### Simplified Technical English

- Write all new text in ASD-STE100. Use short sentences. Use the active voice. Use one instruction in
  each sentence.
- Use "must" for a requirement.
- Keep technical names, field names, enum values, formulas, code and YAML unchanged.

### Stage

- In the spec-build stage, do not change a file under `skellytracker/`. A test fix in
  `skellytracker/tests/` is the only exception
  ([0014](../../../notes/decisions/0014-spec-lifecycle.md#no-implementation-change-during-the-spec-build-stage)).
- Do not change an exporter repo.

## Checks

Run these commands before each PR. Each command must pass.

1. `uv run python tools/make_vectors.py --check`
2. `uv run python tools/sidecar_trace.py matrix --check`
3. `uv run pytest tools/tests -q`. It also runs the private-data check
   ([Private data](../../../AGENTS.md#8-private-data)).
4. `uv run pytest -m "not video"`
5. `uv run ruff check skellytracker/ tools/`. When `specs/sidecar/reference/` exists, add it to the
   command.

## Stop points

| Condition | Action |
|---|---|
| The user has not accepted the proposal. | Stop. Do not change the normative text. |
| A content change has no accepted decision entry. | Use `propose-sidecar-change`. Then stop. |
| An example breaks a spec rule. | Stop. Do not correct the example. Tell the user. |
| A new reference implementation changes an expected vector value. | Stop. Tell the user. |
| The PR is ready. | Ask the user before the push ([section 6](../../../AGENTS.md#6-git-rules) of `AGENTS.md`). |
