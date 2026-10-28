# Reference implementations

If `../freemocap/skellytracker/specs/model-sidecar/reference/` does not exist, no reference
implementation exists yet. Two things add a reference implementation:

1. an accepted proposal (phase 2, part 3);
2. an exporter that implements a section on its host side.

[Independence](sidecar-files.md#independence) gives the implementations that count in
`verified_against`.

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

**Module names.** For `<section_module>`, use the section ID from the front matter of the section file
(`id`), with each dot replaced by an underscore. For example, `pre.resize.letterbox` gives
`pre_resize_letterbox`. The section map `../freemocap/skellytracker/specs/model-sidecar/README.md`
lists each section ID. For a new section, propose an ID in the same scheme
(`<format|common|pre|post>.<area>[.<name>]`). In a proposal, make `<section_module>` from the
proposed section ID.

- A resize method and its unprojection are one module, because the section file of the method gives
  the inverse with the forward algorithm (the heading "Inverse"). Do not put two sections together in
  one module.
- Write the section ID in the note at the top of the file.
- The folder `specs/model-sidecar/reference/` is not a Python package, and its path has a hyphen.
  Load a reference file by its path with `importlib.util.spec_from_file_location`, or run it as a
  script. In skellytracker, `load_reference` of `tools/make_vectors.py` does this.
- The heading "Reference mappings in skellytracker" in
  `../freemocap/skellytracker/specs/model-sidecar/post/canonical-mapping.md` (the old spec heading
  "Reference implementations" under `pose.canonical_mapping`) is about the canonical mapping files of
  the package. It is not about these files.

The step (the skill `author-sidecar` includes it):

1. Write the clean, minimal form of your host code. Use only NumPy, OpenCV and the Python standard
   library. Do not import from your repo or from skellytracker. Write one function for each
   algorithm. In each docstring, cite the section ID and the commit of your repo that the code comes
   from.
2. Run the functions against the vectors of the section (see [Vectors](reading-the-spec.md#vectors)).
   They must pass. If the vector file says `unverified`, also run the vectors through your host
   code, and record both results. If the section has no vector file yet, record that.
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
