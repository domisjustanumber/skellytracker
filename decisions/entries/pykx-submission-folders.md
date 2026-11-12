# pykx — A submission folder for each model and each proposal in `plans/sidecar/`

**Status:** accepted, 2026-10-26 (user); superseded by [FADS](FADS-hand-over-bundles-in-intakes.md), 2026-10-28 (user; PR: pending).

## Decision

1. **Layout.** A contributor writes the files of a submission in `plans/sidecar/` of its repo:
   - `models/<model_id>/intake.md`: the model intake, one for each family;
   - `proposals/<slug>/`: one folder for each contract unit, with `proposal.md`,
     `reference/<section_module>.py` (part 3), `vectors/<section ID>.yaml` (part 4), and the
     optional `evidence.md` and `example/`;
   - `reference/<section_module>.py`: a reference implementation of the current spec text.
2. **Target names.** Each file name in a proposal folder is the name of its target file in
   skellytracker. When skellytracker records a proposal, it copies the folder to
   `specs/model-sidecar/proposals/<slug>/`, with the copy rules of
   ADR-[faac](faac-proposal-records.md). Part 3 and part 4 of `proposal.md` name the files. They do not
   repeat the code and the cases.
3. **No copy into a model folder.** A proposal folder serves each model that needs it. The intake
   links to it.
4. **Candidate example.** This rule replaces the phase 2 rule "Do not write a sidecar file of the model
   with the proposed fields". A proposal folder can hold a candidate example in `example/`: the
   sidecar and its fragments in the storage layout, and `example/provenance.yaml` with its
   `inventory.yaml` entries. The writer code writes it after the host code implements the proposed
   text. The candidate is not a spec example. After acceptance, the procedure "Reference examples"
   copies the real export.
5. **Complete folders.** skellytracker shows when it landed each file. A model folder is complete when
   its example is in `inventory.yaml` and each proposal folder that it links to is complete. A
   proposal folder is complete when its proposal has `state: landed` or `state: rejected`. A file in
   `plans/sidecar/reference/` is complete when its skellytracker reference file exists and its
   function is in `external_impl`. The contributor tells the user. The user deletes the folder.
6. **Old names.** A contributor moves each file with an old name (`plans/sidecar-intake-<model>.md`,
   `plans/sidecar-proposal-<slug>.md`, `plans/sidecar-reference-<section_module>.py`) to its new path.
   A skellytracker scan also reads the old names. It tells the user when it finds one. An older
   record keeps part 3 and part 4 in `proposal.md`.
7. **Source.** The model addition workflow, heading "Files in `plans/`", gives the layout. The
   templates and the skills link to it.

## Reason

- The user asked for one folder for each model, kept in the exporter until skellytracker has
  incorporated its changes.
- A proposal belongs to one section, not to one model. One proposal can serve several models, for
  example the hand models of Qualcomm-Exporter and MediaPipe-Exporter. A folder for each proposal
  keeps one copy.
- A proposal produces files of different kinds: text, Python code, a vector file and a candidate
  sidecar. In one Markdown file, the code and the cases cannot be checked by a tool. With target
  names, the landing is a copy, and the vector check of ADR-[a33q](a33q-vector-case-form.md) compares
  two files.
- `reference/<section_module>.py` has no hyphen in its name. The old name
  `plans/sidecar-reference-<section_module>.py` had hyphens, so Python could not import it by its
  name.
- The completion state is in skellytracker files: `inventory.yaml`, the proposal index and
  `external_impl`. So the folder needs no landing record, and skellytracker does not write to an
  exporter repo.

## Consequences

- The skills `author-sidecar`, `propose-sidecar-change`, `change-sidecar-spec` and
  `implement-sidecar-section`, both templates, phases 1 to 3 and "Reference implementations" name the
  new paths.
- The exporters that have files with old names move them. The 14 recorded proposals keep their
  inline part 3 and part 4 until they are recorded again.

## Alternatives rejected

- **A manifest file in each model folder.** The intake already gives the commits, the sidecar path,
  the proposals and the reference files. skellytracker gives the completion state.
- **Proposals in the model folder.** A proposal that serves two models then has two copies.
- **One folder for the model with all of its files.** The same reason.
