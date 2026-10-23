---
name: implement-sidecar-section
description: Use this skill in skellytracker when you implement one section of the sidecar spec in the package code, in the implementation stage. Use it also when you plan that work.
---

# Implement a sidecar section

This skill uses ASD-STE100 Simplified Technical English.

This skill implements one section of the sidecar spec in the skellytracker package. It runs only in
skellytracker. It is for the implementation stage and the steady state
([decision 0014](../../../notes/decisions/0014-spec-lifecycle.md#stages)).

The section file gives the normative text. [Decision 0013](../../../notes/decisions/0013-spec-structure.md)
gives the front matter, the vectors, the reference implementations and the traceability. This skill
gives the order of the steps, the inputs, the outputs and the stop points.

## Stage

- [Section 1](../../../AGENTS.md#1-purpose) of `AGENTS.md` names the current stage.
- In the spec-build stage, no file under `skellytracker/` changes
  ([0014](../../../notes/decisions/0014-spec-lifecycle.md#no-implementation-change-during-the-spec-build-stage)).
- In the spec-build stage, do only steps 1 to 4. Report the plan. Then stop.
- If step 3 finds that the work is blocked, do only steps 1 to 3. A blocked section gets no plan.
  Report the result of step 3. Then stop.

## Inputs

- The section ID, for example `post.det.selection.top_k`. The
  [section map](../../../specs/sidecar/README.md#section-map) gives the section file.
- `<section_module>` is the section ID with each dot replaced by an underscore, for example
  `post_det_selection_top_k`.

## Outputs

| Output | Where |
|---|---|
| The code of each step | `skellytracker/`, for example a function under `skellytracker/core/detectors/processing/` and a validator in `skellytracker/core/sidecar/model.py` |
| The line `Implements: <section-id>` | The docstring of each implementing function |
| The vector test | A test in `tools/tests/test_vectors.py` that runs the implementing function on each case of `specs/sidecar/vectors/<section-id>.yaml` |
| The new front matter | `implemented_by`, `status` and `tests` of the section file |
| The new `verified_against` | `tools/make_vectors.py`, then the vector file |
| The new traceability matrix | `specs/sidecar/TRACEABILITY.md` |

## Procedure

### Step 1: Read the section

1. Read the front matter of the section file: `implemented_by`, `status`, `tests`, `vectors`,
   `external_impl` and `selectors`.
2. Read the normative headings: "Fields", "Behaviour" (with "Inverse", if the section has it),
   "Validation rules" and "Legacy behaviour".
3. Read the "Implementer guidance" heading. If it is empty, use only the normative text. Do not guess
   the guidance.
4. Read the sections that the text links to. Read the sections that link to its rules.
5. Read the decision entries that cite the section.
6. Read the [Open work](../../../notes/decisions/README.md#open-work) list and its list of spec
   defects. Find the items about the section.
7. Read the code that `implemented_by` names. Read the tests that `tests` names.

### Step 2: Find the evidence

| Evidence | Where to look |
|---|---|
| A reference example that uses the section | [`TRACEABILITY.md`](../../../specs/sidecar/TRACEABILITY.md#models-and-sections), "Models and sections": the row of the section, in the columns of the models with the root `example` (see "Models") |
| Verified vectors | `specs/sidecar/vectors/<section-id>.yaml`: `verified_against` at the top of the file, or for each case. `unverified: <reason>` means that no implementation verified the file. |
| A reference implementation | `specs/sidecar/reference/<section_module>.py` |
| An exporter implementation | `external_impl` in the front matter, and "External implementations" in `TRACEABILITY.md` |
| An exporter file that waits to land | A scan of `../../*-Exporter/plans/sidecar-*` from the root of this repo: `sidecar-reference-<section_module>.py`, and each `sidecar-proposal-*.md` that changes the section. Read the files. Do not change them. |

If the section has no vector file, the section has no verified vectors.

An exporter file that waits to land is not a reference implementation yet. It does not end a block.
A skellytracker session must land it first, with the skill
[`change-sidecar-spec`](../change-sidecar-spec/SKILL.md).

### Step 3: Find out if the work is blocked

1. The work is blocked when all three conditions are true:
   - no reference example uses the section;
   - the vectors are `unverified`, or the section has no vector file;
   - no reference implementation exists.
2. If the work is blocked, stop. Do not do step 4. Report these items:
   - that the work is blocked;
   - the three missing items;
   - the items that end the block: a reference implementation, a reference example that uses the
     section, or an exporter implementation that verifies the vectors. One of them is sufficient;
   - each exporter file from step 2 that waits to land.
3. Name the exporter that owes each missing item, if
   [Known open items for the exporter overhaul](../../../specs/sidecar/exporter-guide.md#known-open-items-for-the-exporter-overhaul)
   names one. That table can name an exporter for the reference implementation and for the example.
4. Do not write a reference implementation, an example or vectors to remove the block. Do not mark a
   vector verified. A reading of the text alone does not verify a vector
   ([Test vectors](../../../notes/decisions/0013-spec-structure.md#test-vectors)).

### Step 4: Plan the work

1. List the steps of `implemented_by` (for example `validate`, `forward`, `inverse`, `decode` or
   `load`) and their `status`.
2. For each step that is not `implemented`, write where the code goes. Use the implementer guidance.
   If the guidance does not say, write `for the implementer` and the open question.
3. Write the dispatch point, for example a branch in `preprocess_image` in
   `skellytracker/core/detectors/processing/image_preprocessing.py`. If no code dispatches on the
   field of the section yet, write `none yet`. Write where a new dispatch point can go as
   `for the implementer`.
4. Write the validator changes in `skellytracker/core/sidecar/model.py`, with the rule ID of each
   validation rule.
5. Write the tests: the vector test, a test for each rule ID, and a golden parity test if the
   implementer guidance names one.
6. Write the existing code that the change touches. If no code does a step yet (`missing`), write the
   code that the new code calls or replaces, or `none`.
7. Write the legacy behaviour that the code must keep for an older `schema_version`.
8. List the prerequisites: the work in other sections or in the Open work list that this section
   needs first. An example is a field of another section that `model.py` does not have yet. Each
   prerequisite is a separate PR before the PR of this section.
9. `load_sidecar` rejects `vNEXT`. A development build must load `vNEXT` sidecars
   ([0014](../../../notes/decisions/0014-spec-lifecycle.md#vnext-is-not-a-version)). If a test needs a
   `vNEXT` sidecar and a development build cannot load one yet, write that work as the first
   prerequisite. If the Open work list has no item for it, tell the user. Do not design that work in
   this plan.
10. In the spec-build stage, report the plan. Then stop.

### Step 5: Port or compare

1. If a reference implementation exists, port it into the package. The package must not import from
   `specs/`.
2. If `external_impl` names an exporter function, read it in the exporter repo. Do not change the
   exporter repo. Compare its results with your code on the vector cases.
3. If your code does not agree with a reference implementation or with an exporter function, stop.
   You found a spec defect or a bug. Use the skill
   [`propose-sidecar-change`](../propose-sidecar-change/SKILL.md). Do not change the vectors to match
   the code.

### Step 6: Implement and test

1. Implement each step of the plan from the normative text.
2. Keep the legacy behaviour for each older `schema_version`.
3. Implement each validation rule of the section. Add a test for each rule ID to
   `skellytracker/tests/sidecar/test_model_validation.py`.
4. Add the line `Implements: <section-id>` to the docstring of each implementing function.
5. If `tools/tests` has no test that checks the `Implements:` lines, add that test in the same PR.
6. Add a constant with the `path::symbol` of the implementing function to `tools/make_vectors.py`,
   for example `FIT_FUNCTION`.
7. Add a parametrized test to `tools/tests/test_vectors.py` that runs the function on each case of
   `specs/sidecar/vectors/<section-id>.yaml`. Use the constant. An example is
   `test_fit_preprocess_agrees_with_the_case`. The generic test of that file checks only that a name
   in `verified_against` resolves. It does not run the function.
8. Every case must pass. Do not edit a vector file by hand.
9. Add the golden parity test, if the plan has one.
10. Add the constant to `verified_against` of the section in `tools/make_vectors.py`. Then run
    `uv run python tools/make_vectors.py`.
11. skellytracker counts as one implementation in `verified_against`. A vector is fully verified only
    when two independent implementations agree
    ([Independence](../../../notes/decisions/0014-spec-lifecycle.md#independence)).

### Step 7: Update the traceability

1. Write each implementing function in `implemented_by`, as `path::symbol`.
2. Set the `status` of each step:
   - `implemented`: the step does the full normative text, and every case of the vector file passes;
   - `partial`: the step does only a part of the text. Write what is missing in a comment after the
     path in `implemented_by`;
   - `missing`: no function does the step.
3. Add the new test files to `tests`.
4. Regenerate the matrix with `uv run python tools/sidecar_trace.py matrix`. Do not edit
   `specs/sidecar/TRACEABILITY.md` by hand.
5. If the change completes an item of the Open work list, remove the item in the same PR.

### Step 8: Check and stop

1. Run these commands. Each command must pass:
   - `uv run pytest -m "not video"`
   - `uv run ruff check skellytracker/ tools/`
   - `uv run python tools/make_vectors.py --check`
   - `uv run python tools/sidecar_trace.py matrix --check`
2. Do not run `black` or `isort` on the package.
3. Put the implementation in its own PR. Do not put a spec change in it
   ([0027](../../../notes/decisions/0027-single-working-branch.md#one-kind-of-change-in-each-pr)). Put
   each prerequisite of step 4 in its own PR before it.
4. Ask the user before the push ([section 6](../../../AGENTS.md#6-git-rules) of `AGENTS.md`).

## Stop points

| Condition | Action |
|---|---|
| The project is in the spec-build stage. | Do steps 1 to 4. Report the plan. Then stop. |
| No reference example uses the section, the vectors are not verified and no reference implementation exists. | Stop after step 3. Do not plan the work. Report the work as blocked, the missing items, the items that end the block and the exporter that owes each item. Do not write the missing items. |
| Your code does not agree with a reference implementation or an exporter function. | Stop. Use `propose-sidecar-change`. |
| A vector case fails. | Find the cause in the code. Do not change the vector. If the vector does not agree with the text, report a spec defect. |
| The PR is ready. | Ask the user before the push. |
