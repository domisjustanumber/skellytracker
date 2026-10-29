# Validation and publishing

These rules apply to each contributor that writes a sidecar.

## Validation

- The validation rules are in the section files. Each section file has a "Validation rules" heading,
  and each rule there has a rule ID (`V-<section-id>-<n>`). The validation index is the heading
  "Validation rules" in `../freemocap/skellytracker/specs/model-sidecar/README.md`. It links to the
  rules of each section, and it gives the meaning of **(vNEXT)**: a rule marked **(vNEXT)** applies
  only when `schema_version >= vNEXT`.
- Walk the "Validation rules" of every section that the sidecar uses.
- A `vNEXT` sidecar must pass every rule, also each rule marked **(vNEXT)**, except the two rules in
  the next bullet.
- `V-format.versioning-1` (the version pattern) and `V-format.versioning-2` (the support by the
  installed release), in `../freemocap/skellytracker/specs/model-sidecar/format/versioning.md`,
  cannot pass for `vNEXT`. Record them as `n/a at vNEXT`. They apply after the release step (see
  "Publishing").
- Check the "Legacy behaviour" heading of each section that the sidecar uses, if the section has one.
  "Version-aware compatibility" in
  `../freemocap/skellytracker/specs/model-sidecar/format/versioning.md` indexes each "Legacy
  behaviour" heading that gives a legacy difference. The availability of a new feature is in the
  "Legacy behaviour" table of Schema versioning. A change in "Every-version changes" of the same file
  applies also to a sidecar with an older `schema_version`
  ([ADR-KDBD](../../../decisions/KDBD-change-classes-and-spec-forced-edits.md)). A `vNEXT` sidecar must not
  use a legacy-only form: `requires_nms` without `selection`, `may_include_non_person_classes`, or
  `letterbox` with `preserve_aspect_ratio: false`.
- Record the rule ID (`V-<section-id>-<n>`) of each rule that you checked in the intake.
- If a row of the intake is blocking ([Phase 1](phase-1-intake.md), step 3), do not walk the
  checklist. Write `skipped`.
- If a row is `unverified` and no row is blocking, walk the checklist on the draft. Mark
  each result that depends on an `unverified` row as provisional.
- Run the checks of your repo. Use a skellytracker sidecar checker only if the spec or this section
  names it.
- Do not use the skellytracker `load_sidecar` to check a `vNEXT` sidecar. It rejects `vNEXT` (see
  "Publishing").

## Publishing

- Do not publish a `vNEXT` sidecar to a shared or remote folder, for example a Hugging Face repo. Keep
  it in your repo and in the spec examples. One exception: in the implementation stage,
  skellytracker can use a private Hugging Face test repo.
- The reason: `vNEXT` is not a version. It does not match the `schema_version` pattern
  `vYYYY.0M.BUILD[-TAG]`, so no skellytracker release can load it. (`load_sidecar` validates the
  sidecar with `SidecarModel`, which checks `schema_version` with `parse_skellytracker_version` in
  `skellytracker/core/sidecar/versioning.py`.)
- In the spec-build stage, each spec change goes into `vNEXT` and adds one row to the `vNEXT` summary
  of changes. From the first release that ships the spec, each change sets `schema_version` to the
  release that ships it and adds a changelog row.
- The release step: skellytracker cuts the first release that ships the spec. One content PR then
  replaces `vNEXT` with that release version in the spec, the changelog, every example and the
  `spec_revision` of every vector file. This step replaces the instruction "before merging" in the
  reviewer note of the spec changelog.
- After the release step, regenerate your sidecars. Set `schema_version` to the skellytracker release
  that is current at export time (the exporter obligation under the heading "Semantics" in
  `../freemocap/skellytracker/specs/model-sidecar/format/versioning.md`). Then you can publish them.
- A development build of skellytracker will load `vNEXT` sidecars. A release will not (skellytracker
  decision 0016). A development build has a `__version__` with a pre-release tag, or an explicit
  opt-in setting. The code does not do this yet. The trace tool only resolves sidecars. It does not
  validate them, so it works with `vNEXT`.
- The batch artifacts. A sidecar uses one batch form for every size and every precision: b3, b1 or
  `dynamic` ([Batch forms](../common/sizes-and-artifacts.md#batch-forms);
  [ADR-JB5J](../../../decisions/JB5J-one-batch-form-for-each-sidecar.md)). You publish one batch
  artifact for each size and precision, in that form.
  - b3 is the goal. `sizes.<size>.onnx.batch_artifacts` has only the key `"3"`. The sidecar has
    `batching.batch_conversion: {profile_id: static-batch-v1, source_batch_size: 3}`. b3 needs the
    verdict `converts` of the [batch-conversion check](hand-over.md#batch-conversion-check). Thus
    `external` lists the verification batches 1, 2, 3 and 4 of each size and precision.
  - b1 and `dynamic` are the fallbacks. `batch_artifacts` has only the key `"1"`, or only the key
    `dynamic`. The sidecar has no `batch_conversion`. A fallback is allowed with the verdict
    `does not convert`. It is also allowed when the person who runs the exporter forces it.
  - The batch-conversion check runs by default. To force a fallback, write `batch_forced` (`1` or
    `dynamic`) and `batch_forced_reason` in the manifest ([Manifest](hand-over.md#manifest)). Write
    the same choice and reason in the intake. Then you can skip the check. A skipped check has the
    verdict `not applicable`. With `batch_forced`, publish only that form.
  - `dynamic` also needs a passed dynamic check of the batch-conversion check (V6). If it fails, do
    not publish the `dynamic` export.
  - With the verdict `to run`, mark as `published` the files of the form that you plan. The session
    verdict then decides ([The session run](hand-over.md#the-session-run)). b3 needs the session
    verdict `converts`.
  - The other files of the check (for example b2 and b4, and b1 of a b3 family) have
    `published: false` in `external` of the bundle manifest. Do not publish them.
  - No validation rule checks the publication. `intake_bundle.py verify` checks this rule for each
    verdict. `V-common.sizes_and_artifacts-13` checks the batch form of the sidecar.

## `source` and hashes

A `vNEXT` sidecar has a top-level `source`. It also has a `sha256` on every `$ref`, every `base` and
every `filename` artifact (skellytracker decision 0016). The spec text is in these section files:

- `source`: section `common.identity`, in
  `../freemocap/skellytracker/specs/model-sidecar/common/identity.md` (rules `V-common.identity-4`
  to `V-common.identity-6`).
- The hashes of `$ref` and `base`, and the rules for the bytes of a file: section
  `format.composition`, in `../freemocap/skellytracker/specs/model-sidecar/format/composition.md`
  (the heading "Reference hashes").
- The hash of an artifact and the reserved placeholder: section `common.sizes_and_artifacts`, in
  `../freemocap/skellytracker/specs/model-sidecar/common/sizes-and-artifacts.md` (the heading
  `sizes.<size>.onnx.batch_artifacts`).

Rules:

- Write a top-level `source` with exactly two fields. `name` is the package name of your repo, for
  example the exporter package `openmmlab-exporter`. `version` is the released version of that
  package, for example `0.1.0`. Write `name` in the form that rule `V-common.identity-6` gives.
- Do not write `source.name: skellytracker`. That name is reserved for the sidecars of the
  skellytracker package.
- Write each sidecar and each fragment as UTF-8 without a BOM, with LF line endings. A file with CRLF
  line endings fails the check. On Windows, `Path.write_text` writes CRLF when you do not give
  `newline="\n"`.
- Fill in the hashes with the skellytracker tool. First put the ONNX files in the folder of the
  sidecar. Then run this command from the root of your repo:
  `python ../freemocap/skellytracker/tools/sidecar_refs.py --write <sidecar>`.
  - The tool needs only the standard library and PyYAML. It does not import `skellytracker`. Thus the
    Python of your repo can run it.
  - The tool adds or updates only the `sha256` entries in the files of the sidecar tree. It also
    changes a `base` path string to the form `{$ref, sha256}`. It keeps all other bytes. It does not
    change line endings: on a CRLF file or a file with a BOM, it stops with an error and changes no
    file.
- Then check the hashes:
  `python ../freemocap/skellytracker/tools/sidecar_refs.py --check <sidecar>`. The check must
  pass. It fails on a hash that does not match, on a missing hash, on a CRLF file and on a BOM.
- Never write the placeholder hash (64 zeros). It is valid only in the spec's own examples. Thus do
  not use the option `--placeholder`.
- Publish a sidecar to a shared folder or a Hugging Face repo only after the release step
  (see "Publishing").
