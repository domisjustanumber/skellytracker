# Reference implementations

Two things add a reference implementation:

1. an accepted proposal (phase 2, part 3);
2. an exporter that implements a section on its host side.

[Independence](sidecar-files.md#independence) gives the implementations that count in
`verified_against`. The headings from [Full section](#full-section) to
[Run a module that imports another module](#run-a-module-that-imports-another-module) state the rules
for reference modules ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
Part 4 of the change proposal template gives the form of a vector case.

## When to do the step

Your plan can implement a sidecar section on the host side. Then the plan must
include a step that gives the reference implementation of that section to skellytracker. The rule
applies for every verdict of the intake. These skip rules apply to each section
([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)):

- Skip the step if `../freemocap/skellytracker/specs/model-sidecar/reference/<section_module>.py`
  exists. If your host code and that file do not agree, follow the last paragraph of
  [The step](#the-step).
- Skip the step if one of your proposals changes the section. The part 3 file of the proposal is the
  reference implementation. If the user rejects the proposal, do the step for the current text.
- A part of the spec without an algorithm needs no reference implementation, for example
  `common.identity`, `input.dtype` or `input.resize.method: none`.
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
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
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

- Use only NumPy, OpenCV, the standard-library modules of `REFERENCE_STDLIB` in
  [`tools/intake_bundle.py`](../../../tools/intake_bundle.py) and the reference modules of other
  sections ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md);
  [ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)). To use one more
  standard-library module, ask for it in your proposal.
- Do not read or write a file. Do not use the network, a process, the environment or the
  interpreter. For example, do not call `np.load`, `np.save`, `cv2.imread` or `cv2.imwrite`
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- Do not use a name of `FORBIDDEN_NAMES` in `tools/intake_bundle.py`, for example `open`, `eval`,
  `exec`, `compile`, `__import__`, `breakpoint`, `globals`, `locals`, `vars`, `__builtins__` or
  `get_type_hints`. Do not call `input`. Give the name of a `getattr`, `setattr`, `delattr`,
  `operator.attrgetter` or `operator.methodcaller` only as a string literal
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- At module level, write only the docstring, imports, constants and definitions (`def`, `class`).
  A constant has no call. Define each function with `def`
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- The header of a `def` or a `class` and a class body also run at import. Do not put a call in a
  default value, an annotation, a base or a class keyword. A decorator can be a name, or one call
  with arguments that have no call, for example `@dataclass(frozen=True)`. In a class body, the
  only call is `field(...)` or `dataclasses.field(...)` with arguments that have no call
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- Do not use an attribute that `verify` refuses, on any object. Do not use a string that holds
  such a name. `verify` refuses these attribute names
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)):
  - a name that starts with `_`, except `__name__`, `__doc__`, `__init__`, `__post_init__`,
    `__all__` and `__main__`;
  - a name that starts with `load`, `save`, `read`, `write`, `dump`, `imread` or `imwrite`, in
    upper or lower case, and a name that contains `_load` or `_save`;
  - the names of `FORBIDDEN_NAMES`, `SYSTEM_NAMES` and `FILE_NAMES`, and the OpenCV names of
    `CV2_FILE_PREFIX` in `tools/intake_bundle.py`, for example `os`, `sys`, `environ`, `testing`
    and `dnn`.
- Import a section module only when its section is in the spec or in the manifest `sections` of your
  bundle, its owner, its `base` or a `depends_on` bundle. A file in a `reference/` folder must be
  `reference/<section_module>.py` of a section of the manifest
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- `verify` reads your module as text, with `ast`. It never runs your module. It gives a finding for
  many breaks of these rules, but it cannot find all of them. The review of a skellytracker session
  is the gate ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
- One exception: part 3 of a proposal for a new profile of `common.batch_conversion` is a standalone
  module that uses onnx and NumPy. It has the signature of `model_batch_convert` in
  `skellytracker/core/sessions/batch_conversion.py`. The implementation stage ports it
  ([ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). This module
  reads its source model and writes its target model only through onnx. The static check allows
  only that file access, and only in `common_batch_conversion.py`
  ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
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
- A reference module has `run(params, input)`. If the section has an inverse, the module also has
  `inverse(params, input)`. Each function returns a mapping with the keys of `expect`. It refuses an
  input only with `ValueError`
  ([ADR-8DSW](../../../decisions/entries/8DSW-vector-files-are-the-case-source.md)).
- A case without `function` calls `run`. Each other `function` of a case names a function that the
  module of the case section defines. `tools/tests/test_vectors.py` checks this. The only exception
  is `function: none`: it marks a data-only validator case.
- Host code compares its result with `expect` as `agrees` of `tools/vector_form.py` does. An integer
  must match exactly. A fractional number can differ from `expect` by the `tolerance` of the file or
  less. `compare.<field>` replaces `tolerance` for its field. NaN is equal to NaN.

## Run a module that imports another module

- The folder `specs/model-sidecar/reference/` is not a Python package, and its path has a hyphen.
  Load a reference file by its path with `importlib.util.spec_from_file_location`.
- In skellytracker, `load_reference` of `tools/make_vectors.py` loads the file. The generator and the
  tests use it. It puts the folder of the file on `sys.path` while the file runs. It registers the
  module under its file name.
- In your repo, put the folder of your module and the folder of each imported module first on
  `sys.path` in your runner. Then load your module.
- Do not run such a module as a script with `python -I`. The `-I` option keeps the folder of the
  script off `sys.path`.

## The step

The skill `author-sidecar` includes this step.

1. Implement the current section text. Start from your host code. Where your host code departs
   from the text, follow the text. List each departure in the row of the section in the reference
   table of the intake, or write a proposal in the same pack
   ([ADR-Q6P7](../../../decisions/entries/Q6P7-reference-module-notes-and-unused-cases.md)). Follow
   [Imports of other sections](#imports-of-other-sections). Write one function for each
   algorithm. In each docstring, cite the section ID and the commit of your repo that the code comes
   from. One section has one module across all of your bundles. If more than one of your bundles
   holds the file of a section, the files must be the same.
2. Run the functions against the vectors of the section (see [Vectors](reading-the-spec.md#vectors)).
   They must pass. If the vector file says `unverified`, also run the numeric cases through your
   host code, and record both results in `vector-runs.yaml`. If the section has no vector file yet,
   record that. [Payload](hand-over.md#payload) gives the cases that are host runs
   ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).
3. Run the functions in place of your host code in your parity check. Record that the
   result does not change. If you cannot run the parity check yet, write `to run`.
4. Write the functions to `reference/<section_module>.py` of your `model` bundle
   ([Payload](hand-over.md#payload)). Put a short note at the top of the file. It holds only the
   section ID, the source commit, the section ID of each module that it imports and the section ID
   of each fixture. Do not put the vector results
   or the parity result in the note. They go in `vector-runs.yaml` and in the reference table of the
   intake. The reference implementation of a proposal is in its proposal bundle instead (phase 2,
   part 3). Its results go in parts 4 and 5 of the proposal.
5. Write the final verdict ([Final verdict](phase-1-intake.md#final-verdict)). Then pack the bundle
   and stop ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)). A skellytracker session lands the file. It adds `specs/model-sidecar/reference/<section_module>.py`,
   adds the implementation to `verified_against` in the vector file of the section, and adds the
   exporter function to `external_impl` of the section.

If your host code and an existing reference implementation do not agree, you found a spec defect or a
bug. Write a proposal (phase 2). Do not write a second reference implementation. Two exporters can
write a file for the same section before skellytracker lands one. When skellytracker lands one of
them, this rule applies to the other exporter.
