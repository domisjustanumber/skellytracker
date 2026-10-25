# Restated rules of 0014 for entry 0044

This file is informative. It is the draft text of the entry that supersedes decision
[0014](../../../../notes/decisions/0014-spec-lifecycle.md) in full when the user accepts the proposal
[`omitted-upstream-output`](proposal.md). The entry is
[0044](../../../../notes/decisions/0044-omitted-upstream-output.md). The text does not fit the entry limit, so it
is in this file (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md), items 5
and 9).

The recording session generated this file on 2026-10-25. A script copied the text of 0014 from the
branch `dom/sidecar-implementation` (0014 last changed in `dom/05-sidecar-split`). Then it applied
only the edits of part 2.1, D1, of the proposal: step 3 adds the verdict `omitted` with the six
conditions of G2, and step 4, step 5 and the parity sentence of step 5 add `omitted`. The script
also changed the relative link targets so that they resolve from this folder. It changes nothing
else. The heading and the status line below are those of 0014. The exporter and the user must
confirm this text ([Before acceptance](proposal.md#before-acceptance)).

---

# 0014 — Spec lifecycle, the `vNEXT` rule and the new-model workflow

**Status:** accepted, 2026-10-22 (user).

## Decision

### Stages

| Stage | What happens | What agents need from the docs |
|-------|--------------|--------------------------------|
| **Spec build** (now) | Exporters add new model types, find gaps and propose spec changes. They learn how to interpret the spec, and they implement decode on their own host side. skellytracker implementation code does not change. | How to author a sidecar for an ONNX model. How to propose a change. Where to record how to interpret and implement a section. Which exporters a spec change breaks. |
| **Implementation in skellytracker** | skellytracker implements each section, in the order that models need them. | A backlog for each section. The implementer guidance and the test vectors from the spec-build stage. A way to show progress. |
| **Steady state** | New models arrive, and some need spec changes. Each change is specified, then implemented in skellytracker and in the exporters. | The spec-build workflow, plus the implementation in the same cycle, with its effect on models, exporters and skellytracker code. |

[0013](../../../../notes/decisions/0013-spec-structure.md) gives the structure that serves these needs: section files, guidance
headings, vectors, `TRACEABILITY.md` and the `impact` command.

### Versions

- During the spec-build stage, each spec change goes into the `vNEXT` revision. Each change has one
  row in the `vNEXT` summary of changes. Until the split, that is the
  [Summary of changes](../../../../specs/sidecar/changelog.md#summary-of-changes) table of the spec. After the
  split, it is in `specs/sidecar/changelog.md`.
- From the first skellytracker release that ships the spec, each change sets `schema_version` to the
  release that ships that change. Each change also adds a changelog row. This is the rule at the start
  of [`schema_version` history](../../../../specs/sidecar/changelog.md#schema_version-history).

### `vNEXT` is not a version

- `vNEXT` is a placeholder. No skellytracker release can load a `vNEXT` sidecar: `load_sidecar`
  rejects the version string (see "Evidence").
- Thus, during the spec-build stage, a `vNEXT` sidecar stays in its exporter repo and in the spec's
  examples. Do not publish a `vNEXT` sidecar to a shared or remote folder.
- One exception: the implementation stage can use a private Hugging Face test repo.
- A development build of skellytracker loads `vNEXT` sidecars. A release does not
  ([0016](../../../../notes/decisions/0016-sidecar-catalogs.md)). A development build is a skellytracker version (`__version__`)
  with a pre-release tag, or a build with an explicit opt-in setting. The code does not do this yet:
  it is implementation-stage work.
- The trace tool only resolves sidecars. It does not validate them. Thus it works with `vNEXT`
  during the spec-build stage.

### Release step

- When the first release that ships the spec is made, one content PR replaces `vNEXT` with that
  release version everywhere: in the spec, in the changelog, in each example and in the
  `spec_revision` of each vector file.
- Then the exporters regenerate their sidecars with the release version. After that, a sidecar can
  be published to a shared or remote folder.
- The reviewer note at the top of the spec says to replace `vNEXT` "before merging". This decision
  moves that step to the first release that ships the spec.

### No implementation change during the spec-build stage

- During the spec-build stage, no file under `skellytracker/` changes.
- Exception: test fixes in `skellytracker/tests/`. A test fix is not implementation. Each root cause
  of a test failure gets its own small PR. If a failure shows a real code defect, report it. The code
  fix waits for the implementation stage.
- Docs, tools, vectors and reference implementations outside `skellytracker/` can change.

### New-model workflow

This is the procedure to add a new model. An agent in an exporter repo runs phases 1 and 2, then
stops. A skellytracker session runs phase 3.

**Phase 1: can the current spec describe this model?** Fill in the model intake template
(`specs/sidecar/templates/model-intake.md`).

1. List each property of the model's runtime contract. Use these three sources:
   - the ONNX graph: each input and output;
   - the upstream preprocessing: each transform step, in order;
   - the upstream postprocessing: each decode step, in order.

   An upstream step that does nothing for this model is also a row. The row gives the evidence that
   the step does nothing.
2. Write these values in each row:
   - the property;
   - the upstream evidence: the file and line, or the config key;
   - the section ID (until the split: the heading of `specs/sidecar-spec.md`);
   - the sidecar value;
   - a verdict.
3. Use one of these row verdicts:
   - `exact`: a section describes the property with these values.
   - `near-miss`: the spec has a section and a field for the property, but no value describes the
     property exactly, for example because of the rounding, the pixel centres, the arithmetic
     precision, the order of steps or the threshold comparison.
   - `gap`: the spec has no section and no field for the property.
   - `unverified`: the agent does not have the evidence for a verdict, for example because an input
     is missing or the only source is secondary.
   - `out of scope`: the step is before or after the runtime contract of the model, which starts at
     the inputs of the model and ends at the decoded outputs in source-image coordinates.
   - `omitted`: the upstream decode gives an output that the sidecar deliberately does not
     declare, and each of these conditions is true:
     1. The output is a value beside the outputs that the sidecar declares, for example a second
        value for each keypoint. Its omission changes no declared output: the tensors, the boxes,
        the scores, the keypoints and the row counts that the sidecar declares are the same with
        and without it. Cite the upstream line that shows this.
     2. The spec does not require the output. The spec does not call it out of scope, and
        "Considered and deliberately not added" does not list it. Such an output stays a `gap`.
     3. The upstream evaluation metric of the model does not read the output. Cite the line that
        reads the metric input.
     4. No known consumer needs the output. A consumer is a host or a model that reads the
        outputs of this model, for example a refiner that gates on a point of its parent. For
        each known consumer that could use the output, a committed measurement shows that a
        declared output serves that consumer at least as well. Cite the measurement.
     5. The sidecar declares nothing for the output: no output, no field and no channel.
     6. An exporter decision entry records the omission, its reason and its evidence. Write its
        number after the verdict, for example `omitted (0041)` for OpenMMLab-Exporter decision
        0041.

   Each row that is not `exact` says what differs or what is missing. Treat a `near-miss` as a
   `gap`.
4. If each row is `exact`, `out of scope` or `omitted`, the sidecar writer of the exporter writes the sidecar.
   Then prove parity:
   1. Run the ONNX model with the preprocessing and the decode that the sidecar declares.
   2. Compare the preprocessed input with the upstream library. The maximum absolute difference is
      normally 0.
   3. Compare the final outputs with the upstream library. They must be within the exporter's AP or
      OKS gate, or within a stated maximum absolute difference.

   These rules apply to the host implementation:

   - During the spec-build stage, the exporter's own host implementation of each section does the
     preprocessing and the decode. The exporter writes it from the spec text.
   - Where a section has vectors, that implementation must pass them first.
   - Where a reference implementation exists, the exporter uses it or matches it. Where none exists,
     the exporter's plan includes a step that contributes one (see "Reference implementations from
     exporters").
5. Write one of these final verdicts:
   - `describes`: each row is `exact`, `out of scope` or `omitted`, and parity passes.
   - `does not describe`: a row is `near-miss` or `gap`.
   - `pending`: no row is `near-miss` or `gap`, but a row is `unverified` or the parity result is
     `to run`.

   If parity fails while each row is `exact`, `out of scope` or `omitted`, a property was missed or judged
   incorrectly. Go back to step 1. Until the agent finds that property, the verdict is `pending`. Do
   not loosen the tolerance to pass.

**Phase 2: propose a spec change and its implementation.** Write one proposal for each new or changed
contract unit (one section). The intake links to each proposal. The proposal template
(`specs/sidecar/templates/change-proposal.md`) has eight parts:

1. **Gap.** The property, its upstream evidence, and why the nearest section is wrong. Show it with a
   number where possible, for example "letterbox instead of `fit`: input maximum absolute difference
   81 at 320×240 (OpenMMLab-Exporter 0020)".
2. **Spec change.** The exact normative text: the new or changed section files, the fields table,
   the behaviour (forward and inverse), the validation rules with new rule IDs, the selectors, the
   legacy behaviour and the version effect, and the changelog row.
3. **Reference implementation.** The smallest functions that implement exactly the proposed text,
   with only NumPy, OpenCV and the Python standard library. One function for each algorithm. The docstring cites the proposed
   section ID. The file goes to `specs/sidecar/reference/<section_module>.py`.
4. **Vectors.** The reference implementation makes them. They are verified against the exporter's
   host implementation.
5. **Parity evidence.** The real model, with the reference implementation in place of the missing
   spec feature, compared with the upstream library: the number, the script and the commit. The
   script is committed in the exporter repo, so that the commit can be cited. A script that exists
   only in a local `plans/` folder is not evidence.
6. **skellytracker implementation proposal.** The implementation stage builds it, not the spec-build
   stage. It gives the module and function for the code, the dispatch point, the validator changes in
   `skellytracker/core/sidecar/model.py` with their rule IDs, the tests (the vectors and a golden
   parity test) and the existing code that the change touches (the `impact` output). When the
   proposal is accepted, this text becomes the section's implementer guidance and an "Open work"
   item.
7. **Exporter impact.** Which exporters must write new fields or regenerate their sidecars, and the
   change to the proposing exporter's host decoder.
8. **Alternatives considered,** with the near-miss and the reason to reject it.

**Phase 3: accept and land.** A skellytracker session does this phase. The user decides.

1. **A model with the final verdict `describes`:** one non-spec PR (documentation only) with the
   example, its provenance record in `specs/sidecar/inventory.yaml` and any new guidance from the
   intake. The procedure is in
   [`specs/sidecar-implementation-plan.md`, "Reference examples"](../../../../specs/sidecar-implementation-plan.md#reference-examples).
2. **A proposal:** it becomes a decision entry with the status `proposed`. The user accepts or
   rejects it. After acceptance:
   - A content PR has the normative text, the changelog row, the entry status `accepted` (unless the
     entry was accepted earlier), the vectors and the reference implementation. The vectors and the
     reference go with the text, because together they define its meaning.
   - A non-spec PR (documentation only) has the guidance, the implementation proposal as implementer
     guidance and an "Open work" item, the example and its provenance record. It removes the `proposed` inventory entry, if
     there is one.
   - In the implementation stage, an implementation PR follows.
3. The exporter then writes the sidecar with the new fields and finishes phase 1 for the model.
4. New content PRs go on top of the PR stack, never inside a move or rewording PR
   ([0015](../../../../notes/decisions/0015-review-discipline.md)). If the rewording PR for that section is already lower in the
   stack, a follow-up rewording PR covers the new text.

### Reference implementations from exporters

- There is no reference implementation yet. An accepted proposal adds one (phase 2, part 3).
- An exporter that implements a section on its host side must contribute the reference implementation
  of that section, unless `specs/sidecar/reference/` already has one. The exporter's plan includes a
  step that does this:
  1. Write the clean, minimal form of the exporter's code: only NumPy, OpenCV and the Python
     standard library, no import from the exporter, one function for each algorithm. The docstring cites the section ID and the exporter
     commit that the code came from.
  2. Run it against the section's vectors. It must pass. If the vectors are `unverified`, run them
     through the exporter's host code too, and record both results.
  3. Run it in place of the exporter's host code in the exporter's parity check. Record that the
     result does not change.
  4. Write it to `plans/sidecar-reference-<section_module>.py` in the exporter repo, with a short
     note: the source commit, the vector results and the parity result. Stop.
- A skellytracker session lands it as a non-spec PR on top of the stack: the file in
  `specs/sidecar/reference/`, the `verified_against` of the vector file and the `external_impl` of
  the section.
- If an exporter's host code and an existing reference disagree, the exporter writes a proposal. It
  does not write a second reference.

### Independence

- A reference made from an exporter's code is not independent of that exporter. In the
  `verified_against` list of a vector file, the reference and its source exporter count as one
  implementation.
- A vector is fully verified when at least two independent implementations agree: two exporters, or
  an exporter and skellytracker.
- A vector that comes only from Claude's reading of the text is not verified.

### Who writes what

- Claude is the only writer of this repo for now. There is no spec freeze.
- An agent in an exporter repo writes these files in that repo's local `plans/` folder:
  - `plans/sidecar-intake-<model>.md`;
  - one `plans/sidecar-proposal-<slug>.md` for each gap;
  - one `plans/sidecar-reference-<section_module>.py` for each section that it implemented on its
    host side. `<section_module>` is the section ID with each dot replaced by an underscore.

  Then the agent stops.
- A skellytracker session finds these files with a scan of `../../*-Exporter/plans/sidecar-*`. It
  records each proposal as an entry with the status `proposed`, and it runs phase 3.
- A skellytracker session does not change an exporter repo. It can read exporter repos. The rules
  for exporters are in skellytracker (`specs/sidecar/exporter-guide.md`), and the exporters adopt them
  when they are overhauled.
- Exporter agents read the spec, the skills and the templates from the read-only worktree of
  [0015](../../../../notes/decisions/0015-review-discipline.md).

## Reason

- **The stages need different docs.** During the spec-build stage, the exporters change and test the
  spec. The implementation stage needs a backlog and worked cases that the spec-build stage already
  made. The steady state needs both in one cycle.
- **One revision collects the changes until the first release.** No release has shipped the spec, so
  a release version for each change would name versions that do not exist. One row for each change
  gives a reviewer one list of what changed.
- **A `vNEXT` sidecar fails in every release.** A user who downloads one gets an error. So it stays
  out of shared and remote folders until the release step gives it a real version.
- **One content PR for the release step** changes the spec, the examples and the vectors together,
  so they agree with one another.
- **The implementation stage must load `vNEXT`** to implement and test the sections before the
  release. A development build gives that, and a release stays safe.
- **The spec changes often during the spec-build stage,** through exporter proposals. Code written
  now would have to change with each proposal. The implementation stage starts from a spec with
  vectors and reference implementations, so each section is implemented once.
- **A near-miss hides an error.** A near-miss can give the same result on some inputs and a
  different result on others (see "Evidence"). Only an exact description, proved by parity, is safe.
- **An `exact` verdict can be wrong.** Parity with the upstream library checks the verdicts. A loose
  tolerance would hide the missed property.
- **A proposal brings its implementation plan.** The spec text, the reference implementation, the
  vectors and the parity evidence together prove that the text describes a real model. The
  implementation proposal tells skellytracker where the code goes before anybody writes it.
- **Exporters already write the code.** An exporter needs each section for its own host decoder, so
  its code is the best source for a reference implementation. The parity check proves that code.
- **A copy is not a second opinion.** A reference made from an exporter repeats that exporter's
  reading of the text. If the two agree, that proves nothing new.
- **One writer avoids conflicting edits** in this repo. The exporters are about to be overhauled, so
  skellytracker sessions do not change them. The exporter guide in skellytracker holds the rules for
  the overhaul to adopt.

## Evidence

- `SidecarModel._check_schema_version_pattern` in `skellytracker/core/sidecar/model.py` calls
  `parse_skellytracker_version` in `skellytracker/core/sidecar/versioning.py`. Its pattern
  `_VERSION_RE` is `^v(\d{4})\.(\d{2})\.(\d+)(?:-([A-Za-z0-9.]+))?$`. `"vNEXT"` does not match it, so
  `load_sidecar` in `skellytracker/core/sidecar/loader.py` raises `SidecarValidationError`.
- `require_stable_version` in `skellytracker/core/sidecar/versioning.py` rejects a sidecar
  `schema_version` with a pre-release tag. `SidecarModel._check_schema_version_pattern` calls it too.
  Thus a tagged version such as `v2026.10.1-dev` cannot replace `vNEXT` either. The installed version
  is `__version__ = "v2024.09.1019"` in `skellytracker/__init__.py`.
- The spec's reviewer note in
  [Changes in this revision (`vNEXT`)](../../../../specs/sidecar/changelog.md#changes-in-this-revision-vnext)
  says "replace it with the skellytracker release that ships this revision before merging".
- **A near-miss that looked correct.** On four test images, a `center` letterbox matches RTMO's
  upstream `BottomupResize` only at scale 1. At other scales the keypoints move by up to 17.89 px,
  and `fit` is bit-exact (`input_max_abs_diff: 0`). The measurements are in
  [0012](../../../../notes/decisions/0012-fit-resize-for-rtmo.md) and OpenMMLab-Exporter 0020.

## Alternatives rejected

- **A release version for each spec change during the spec-build stage.** No release ships the spec
  yet.
- **Publish `vNEXT` sidecars now.** No release can load them.
- **Implement the sections in skellytracker now.** The spec still changes through exporter
  proposals, and there are no reference implementations to implement against.
- **Exporter agents edit skellytracker directly.** Claude is the only writer of this repo. An
  exporter agent writes its intake, proposal and reference files in its own `plans/` folder.
- **Accept a near-miss with a tolerance.** It hides a difference that shows on other inputs.

## Not repeated

- Do not loosen a tolerance to make parity pass.
- Do not describe a property with the nearest section when it is a near-miss. Write a proposal.
- Do not describe an ROI refiner as a pose estimator with two fake keypoints. It is a `gap`.
- Do not publish a `vNEXT` sidecar to a shared or remote folder.
- Do not write a second reference implementation when an exporter disagrees with the existing one.
  Write a proposal.
- Do not count a reference implementation and its source exporter as two implementations.
- Do not change an exporter repo from a skellytracker session.
- Do not cite a parity script that exists only in a local `plans/` folder.
