# Reference implementations

If `../freemocap/skellytracker/specs/model-sidecar/reference/` does not exist, no reference
implementation exists yet. Two things add a reference implementation:

1. an accepted proposal (phase 2, part 3);
2. an exporter that implements a section on its host side.

[Independence](sidecar-files.md#independence) gives the implementations that count in
`verified_against`. The headings from [Full section](#full-section) to
[Run a module that imports another module](#run-a-module-that-imports-another-module) state the rules
for reference modules ([ADR-TA0G](../../../decisions/TA0G-vector-cases-and-reference-modules.md)).
Part 4 of the change proposal template gives the form of a vector case.

**Rule.** Your plan can implement a sidecar section on the host side. Then the plan must
include a step that gives the reference implementation of that section to skellytracker. The rule
applies for every verdict of the intake.

- Skip the step if `../freemocap/skellytracker/specs/model-sidecar/reference/<section_module>.py`
  exists.
- Skip the step if one of your proposals changes the section. The part 3 file of the proposal is the
  reference implementation. If the user rejects the proposal, do the step for the current text.
- A part of the spec without an algorithm needs no reference implementation, for example
  `input.layout`, `input.dtype` or `input.resize.method: none`.
- Do the step from committed host code. If the host code is not committed yet, or if it exists only
  in a plan, write `to run` in the intake. Do the step after the commit. This bullet is for a section
  of the current spec. For part 3 of a proposal, see phase 2.

## Full section

A proposal can change a section that has no reference implementation. Then part 3 of the proposal
must implement the full section as changed. The file implements the forward step, the inverse step
and every value. It must not implement only the change. This file is also the
reference-implementation step of the section.

- The rule applies only when the proposal changes an algorithm, the meaning of a value or a
  validation rule of the section
  ([ADR-TA0G](../../../decisions/TA0G-vector-cases-and-reference-modules.md)).
- These edits do not change a section for this rule: a link, a field row that points to another
  section, a sentence that tells where the algorithm of another section applies, and guidance.
- Write one file for each changed section. Do not put two sections in one file.
- If `specs/model-sidecar/reference/<section_module>.py` exists, part 3 gives that file with your
  change. Do not write a new file.
- A follow-up copies the file of its base and adds its change
  ([Proposal forms](hand-over.md#proposal-forms)).

## Module names

For `<section_module>`, use the section ID from the front matter of the section file
(`id`), with each dot replaced by an underscore. For example, `pre.resize.letterbox` gives
`pre_resize_letterbox`. The section map `../freemocap/skellytracker/specs/model-sidecar/README.md`
lists each section ID. For a new section, propose an ID in the same scheme
(`<format|common|pre|post>.<area>[.<name>]`). In a proposal, make `<section_module>` from the
proposed section ID.

- A resize method and its unprojection are one module, because the section file of the method gives
  the inverse with the forward algorithm (the heading "Inverse"). Do not put two sections together in
  one module.
- Write the section ID in the note at the top of the file.
- To load or run a reference file, follow
  [Run a module that imports another module](#run-a-module-that-imports-another-module).
- The heading "Reference mappings in skellytracker" in
  `../freemocap/skellytracker/specs/model-sidecar/post/canonical-mapping.md` (the old spec heading
  "Reference implementations" under `pose.canonical_mapping`) is about the canonical mapping files of
  the package. It is not about these files.

## Imports of other sections

- Use only NumPy, OpenCV, the Python standard library and the reference modules of other sections
  ([ADR-TA0G](../../../decisions/TA0G-vector-cases-and-reference-modules.md)).
- One exception: part 3 of a proposal for a new profile of `common.batch_conversion` is a standalone
  module that uses onnx and NumPy. It has the signature of `model_batch_convert` in
  `skellytracker/core/sessions/batch_conversion.py`. The implementation stage ports it
  ([ADR-JC4T](../../../decisions/JC4T-parity-gates-and-batch-conversion-check.md)).
- Do not import from your repo. Do not import from the package code of skellytracker.
- To use a function or a value of another section, import the module of that section by its module
  name. For example, write `import pre_resize_rotated_roi_crop`.
- Call the function with the module name. For example, write
  `pre_resize_rotated_roi_crop.transform_roi(roi, transform)`.
- Do not use `from <section_module> import`. Do not give a function of another module a name in your
  module.
- Do not write loader code in a reference module. Do not change `sys.path` in a reference module.
- Do not copy a function or a value of another section.
- The module that you import must be in one of these places: `specs/model-sidecar/reference/`, the
  same bundle, or the `reference/` folder of the `base` bundle or of a `depends_on` bundle.
- Write the section ID of each module that you import in the note at the top of the file.

## A proposal that changes more than one section

- If your proposal changes the text of a second section, write the code of that section in a second
  module in the same bundle. Give it the name of that section.
- Your first module imports the second module by its name.
- The manifest `sections` lists each changed section. The first one is the section of the decision
  entry.

## When the other section has no module

- If no place of [Imports of other sections](#imports-of-other-sections) has a module of the other
  section, write the function or the value in your module. It is then a fixture.
- Start the docstring of a fixture function with `Fixture of <section ID>.`
- Put the comment `# Fixture of <section ID>.` on the line above a fixture value.
- Write the section ID of each fixture in the note at the top of the file.
- A fixture is temporary. It is not a second reference implementation. When the module of its
  section lands, skellytracker replaces the fixture with an import and a call.

## Code for the cases

- A function that only makes or wraps a vector case is not a reference function. Do not put it in a
  reference module.
- Keep your case code outside the `reference/` folder.
- The `function` of a case names a function that the module of the case section defines.
  `tools/tests/test_vectors.py` checks this.

## Run a module that imports another module

- The folder `specs/model-sidecar/reference/` is not a Python package, and its path has a hyphen.
  Load a reference file by its path with `importlib.util.spec_from_file_location`.
- In skellytracker, `load_reference` of `tools/make_vectors.py` loads the file. The builders and the
  tests use it. It puts the folder of the file on `sys.path` while the file runs. It registers the
  module under its file name.
- In your repo, put the folder of your module and the folder of each imported module first on
  `sys.path` in your runner. Then load your module.
- Do not run such a module as a script with `python -I`. The `-I` option keeps the folder of the
  script off `sys.path`.

## The step

The skill `author-sidecar` includes this step.

1. Write the clean, minimal form of your host code. Follow
   [Imports of other sections](#imports-of-other-sections). Write one function for each
   algorithm. In each docstring, cite the section ID and the commit of your repo that the code comes
   from.
2. Run the functions against the vectors of the section (see [Vectors](reading-the-spec.md#vectors)).
   They must pass. If the vector file says `unverified`, also run the numeric cases through your
   host code, and record both results in `vector-runs.yaml` ([Payload](hand-over.md#payload)). If
   the section has no vector file yet, record that. Your
   host code runs only the numeric cases. An `error` case and a `failed` case run only against a
   reference module.
3. Run the functions in place of your host code in your parity check. Record that the
   result does not change. If you cannot run the parity check yet, write `to run`.
4. Write the functions to `reference/<section_module>.py` of your `model` bundle
   ([Payload](hand-over.md#payload)). Put a short note at the top of the file: the section ID, the
   source commit, the vector results and the parity result. The reference implementation of a
   proposal is in its proposal bundle instead (phase 2, part 3).
5. Pack the bundle and stop. A skellytracker session lands the file. It adds `specs/model-sidecar/reference/<section_module>.py`,
   adds the implementation to `verified_against` in the vector file of the section, and adds the
   exporter function to `external_impl` of the section.

If your host code and an existing reference implementation do not agree, you found a spec defect or a
bug. Write a proposal (phase 2). Do not write a second reference implementation. Two exporters can
write a file for the same section before skellytracker lands one. When skellytracker lands one of
them, this rule applies to the other exporter.
