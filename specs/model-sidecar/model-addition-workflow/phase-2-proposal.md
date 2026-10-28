# Phase 2: propose a spec change and its implementation

Write one proposal for each new or changed contract unit (one section). Fill
`../freemocap/skellytracker/specs/model-sidecar/templates/change-proposal.md`. Each proposal is
a `proposal` bundle, with the files that [Hand-over bundles](hand-over.md#payload) gives. Choose its
form first ([Proposal forms](hand-over.md#proposal-forms)). The skill `propose-sidecar-change` gives
the order of the steps. The intake names each proposal bundle. Then stop.

Before you write a proposal:

- Read the table "Considered and deliberately not added" of the spec
  (`../freemocap/skellytracker/specs/model-sidecar/changelog.md`). If your gap is in it, cite the
  row in part 1. Give the evidence that a model needs the feature now.
- Find the `proposed` entries of the skellytracker decision log that cover your rows. Read the index
  in `../freemocap/skellytracker/specs/model-sidecar/decisions/README.md`. Also read each `proposed` entry
  that the guidance of your sections cites. If an entry covers your rows, do not write a competing
  proposal:
  - Cite the entry in the header and in part 1.
  - Add your evidence, your vectors and your parity plan in a contribution
    ([Proposal forms](hand-over.md#proposal-forms)).
  - If your rows need a different change, write a follow-up. Say where your proposal differs. Give
    the reason in part 8.
- If a proposal needs another proposal (for example, a decode that uses the unprojection of a new
  crop), write its bundle ID in the header and in `depends_on` of the manifest. One parity script can serve several
  proposals. Cite it in part 5 of each.

A proposal has eight parts:

1. **Gap.** Give the property, its upstream evidence, and the reason why the nearest section is wrong.
   Show it with a number where possible. Example: a `center` letterbox in place of `fit` gives an
   input max abs diff of 35 on a 333×500 image (OpenMMLab-Exporter 0020).
2. **Spec change.** Write the exact normative text as it will appear in the spec:
   - the new or changed sections;
   - the fields table;
   - the behaviour, forward and inverse;
   - the validation rules, with new rule IDs;
   - the selectors;
   - the legacy behaviour and the effect on `schema_version`;
   - the changelog row.

   Also find each place that the change must edit. Search the spec for each closed set or list that
   the change extends, for example the `role` values, the `semantic` values, the resize methods, the
   storage layout (`format.file_layout`), the Overview, the section map and the validation index
   (`../freemocap/skellytracker/specs/model-sidecar/README.md`), and the "Legacy behaviour" heading
   of each changed section with its index "Version-aware compatibility" (`format.versioning`). Also
   find each rule that names one of these values, for example the rule
   `V-pre.resize.affine_person_crop-2`: a sidecar with `pose.requires_object_detector: true` declares
   `input.resize.method: affine_person_crop`. List each place in the proposal. These edits are part
   of the same contract unit: a new role, with its enum and path edits, is one proposal. The
   proposed text can contain YAML excerpts. Do not put a full sidecar in the proposed text. A
   candidate example of the model is a separate file (part 7).
3. **Reference implementation.** Write the smallest functions that implement exactly the proposed
   text. Follow [Imports of other sections](reference-implementations.md#imports-of-other-sections).
   Write one function for each algorithm. Each docstring cites the proposed section ID. Write the
   code to `reference/<section_module>.py` in the proposal folder. Make `<section_module>` from the
   proposed section ID. If the proposal changes a section, follow
   [Full section](reference-implementations.md#full-section). Name the file in the proposal. On acceptance, skellytracker adds it as
   `specs/model-sidecar/reference/<section_module>.py`. It is informative spec code, not package code. It is
   the single executable meaning of the new text. Your host decoder needs this behaviour, so the
   reference implementation is the clean, minimal form of your host code. If no host code exists
   yet, write the functions from the text of part 2. Write `source commit: none (no host code)` in
   the note at the top of the file. Part 4 is then `unverified: no host implementation`.
4. **Vectors.** A test vector is a small worked case: concrete inputs to the algorithm of one section,
   and the exact expected output. Use geometry and small arrays. Do not use images or ONNX files. Make
   the vectors with the reference implementation. Then verify them against your host implementation.
   Include a case for each branch, each tie and each strict comparison. If a parameter can be a scalar
   or one value for each channel (for example `pad_value`), include a case with a scalar value on a
   3-channel input. Pixel-exact resize output is out of scope. If you need a pixel case, state its
   tolerance in `compare`. Write the vectors to `vectors/<section ID>.yaml` in the proposal folder,
   in the case form that part 4 of the template gives (skellytracker ADR-a33q). Name the file in
   part 4. On acceptance, the skellytracker generator writes
   `specs/model-sidecar/vectors/<section ID>.yaml` from the reference implementation. It must hold
   each of your cases.
5. **Parity evidence.** Run the real model, with the reference implementation in place of the missing
   spec feature. Follow [Parity](parity.md#parity). Give the numbers, the script and the commit. If you cannot run the
   check yet, write `to run` and describe the script. A skellytracker session can record a proposal
   with `to run` as `proposed`. Before the user accepts the proposal, part 5 must give the numbers,
   the script and the commit.
6. **skellytracker implementation proposal.** skellytracker does not build it now. It builds it when
   it implements the spec. Write:
   - where the code goes: a module and a function under `skellytracker/core/detectors/processing/`,
     or a new module;
   - the dispatch point, for example a branch in `preprocess_image`
     (`skellytracker/core/detectors/processing/image_preprocessing.py`);
   - the validator changes in `skellytracker/core/sidecar/model.py`, with rule IDs;
   - the tests: the vectors, and a golden parity test;
   - the existing skellytracker code that the change touches.

   Read the package code in `../freemocap/skellytracker/skellytracker/`. The template lists the
   code for each contract part. This part is advisory: the implementer checks it. If you cannot find
   a call site, write `for the implementer` and say what is not known. On acceptance, this text
   becomes the implementer guidance of the section and an open-work item.
7. **Exporter impact.** Name the exporters that must write new fields or regenerate sidecars. Describe
   the change to your own host decoder.

   A candidate example is optional. Write it only after your host code implements the proposed text.
   Your sidecar writer code writes it, with the proposed fields. Do not write it by hand. Put it in
   `example/detectors/...` of the proposal folder, in the storage layout, with each fragment that it
   names. Write `example/provenance.yaml` with an `examples` entry and a `fragments` entry for each
   fragment that has no package copy, with the keys of `specs/model-sidecar/inventory.yaml`. Run
   `python ../freemocap/skellytracker/tools/sidecar_refs.py --check <sidecar>` on it. The candidate
   shows the reviewer the full sidecar. It is not a spec example. After acceptance, the procedure
   [Reference examples](reference-examples.md) copies your real export.
8. **Alternatives considered.** Include the near-miss, and the reason why you rejected it.
