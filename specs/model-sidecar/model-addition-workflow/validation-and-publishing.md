# Validation and publishing

These rules apply to each contributor that writes a sidecar.

## Validation

- The validation rules are in the section files. Each section file has a "Validation rules" heading,
  and each rule there has a rule ID (`V-<section-id>-<n>`). The validation index is the heading
  "Validation rules" in `../freemocap/skellytracker/specs/model-sidecar/README.md`. It links to the
  rules of each section.
- Walk the "Validation rules" of every section that the sidecar uses.
- Each rule applies to every sidecar. Each sidecar has one reading: the current spec text. A key
  that the spec does not define is invalid (`V-format.composition-5`;
  [ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
- Record `V-format.versioning-1` (the valid `schema_version` values) as `pass` or `fail`. Until
  `2.0.0` ships, only `"2.0.0"` and its recorded pre-releases pass. Record `V-format.versioning-2`
  (a host rejects a version that it does not implement) as
  `n/a until a final release loads the target`. For the open target `2.0.0`, that release is
  skellytracker `2.0.0`. Both rules are in
  `../freemocap/skellytracker/specs/model-sidecar/format/versioning.md`
  ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md);
  [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- Record the rule ID (`V-<section-id>-<n>`) of each rule that you checked in the intake.
- If a row of the intake is blocking ([Blocking rows](phase-1-intake.md#blocking-rows)), do not
  walk the checklist. Write `skipped`.
- If a row is `unverified` and no row is blocking, walk the checklist on the draft. Mark
  each result that depends on an `unverified` row as provisional.
- Run the checks of your repo. Use a skellytracker sidecar checker only if the spec or this section
  names it.
- Do not use the skellytracker `load_sidecar` to check a sidecar. The package code is frozen until
  it migrates, and it rejects `schema_version: "2.0.0"` (see "Publishing").

## Publishing

- The publish ban. Do not publish a sidecar to a shared or remote sidecar root, for example a
  Hugging Face repo, until a final skellytracker release loads its `schema_version`. The ban applies
  to each target. A pre-release does not end it. Keep the sidecar in your repo and in the spec
  examples. One exception: in the implementation stage, skellytracker can use a private Hugging
  Face test repo ([Authoring guidance](../format/versioning.md#authoring-guidance) of
  `format.versioning`; [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- skellytracker `2.0.0` ships the SemVer loader, so its release ends the ban for `"2.0.0"`. The
  package code before it is frozen: `SidecarModel` requires a CalVer string and rejects `"2.0.0"`.
- A sidecar with a pre-release `schema_version`, for example `"2.0.0-rc.1"`, is a test sidecar. Put
  it only in the private test repo. Only that skellytracker pre-release loads it. After the final
  release, export the sidecar again.
- Each spec change and each proposal targets the open target. Until the user bumps skellytracker,
  the open target is `2.0.0`. A content commit adds its rows to the summary of changes and appends
  one ``- Row N: `<fingerprint>`.`` line under the open target in
  [Revisions](../changelog.md#revisions). No commit bumps the version.
- The release has no step that replaces a version in the spec
  ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)). The session of the
  skellytracker release of the open target sets `- Released: yes.` under its version heading, in
  the release PR. A released version does not change. After a release, the next spec change adds
  the heading of the version that the user bumps skellytracker to on `development`. When the release
  ships the open target under another number, the release PR renames the unreleased heading and
  changes the examples. The pre-release values of the old number then become invalid
  ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- The session of a skellytracker pre-release appends one ``- Pre-release X.Y.Z-<tag>: row N.`` line
  under the open target.
- The `2.0.0` release stops when a section is `draft`. The user then graduates the section or
  removes its fields from the release. The release also stops when an example or a package sidecar
  has `batching.batch_conversion` and the `validate` or `load` status of `common.batch_conversion`
  is not `implemented`. The skill `change-sidecar-spec` gives both stops
  ([ADR-QMKS](../../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)).
- After a final release loads the `schema_version` of your sidecars, you can publish them.
- The batch artifacts. A sidecar has one `batching.batch` for every size and every precision: b3,
  b1 or `dynamic` ([Batch forms](../common/sizes-and-artifacts.md#batch-forms);
  [ADR-JAA4](../../../decisions/entries/JAA4-one-batch-field.md)). You publish one artifact for each size
  and precision, in that form.
  - b3 is the goal. The sidecar has `batching.batch: 3` and
    `batching.batch_conversion: {profile_id: static-batch-v1}`. b3 needs the
    verdict `converts` of the [batch-conversion check](batch-conversion-check.md#batch-conversion-check). Thus
    `external` lists the verification batches 1, 2, 3 and 6 of each size and precision.
  - b1 and `dynamic` are the fallbacks. The sidecar has `batching.batch: 1` or
    `batching.batch: dynamic`, and no `batch_conversion`. A fallback is allowed with the verdict
    `does not convert`. It is also allowed when the person who runs the exporter forces it.
  - A model that cannot export a static graph publishes `dynamic`. Write why in
    `no_static_reason` of the manifest, and in the intake. Then the family does not need
    `batch_forced`, and V0 gives `not applicable` for it. If the model can export a static graph,
    run the check, or force `dynamic`.
  - The batch-conversion check runs by default. To force a fallback, write `batch_forced` (`1` or
    `dynamic`) and `batch_forced_reason` in the manifest ([Manifest](hand-over.md#manifest)). Write
    the same choice and reason in the intake. With `batch_forced: 1`, you can skip the run of
    `batch`. With `batch_forced: dynamic`, or with `no_static_reason`, skip only the verification
    exports. Then run `batch` for the dynamic check (V6). A skipped check has the verdict
    `not applicable`. With `batch_forced`, publish only that form.
  - `dynamic` needs a passed dynamic check of the batch-conversion check (V6). If it fails, do not
    publish the `dynamic` export.
  - With the verdict `to run`, mark as `published` the files of the form that you plan. The session
    verdict then decides ([The session run](hand-over.md#the-session-run)). b3 needs the session
    verdict `converts`. The reason `missing-verification-batch` allows no form: export the
    verification batches, force a fallback form, or, if the model cannot export a static graph,
    give `no_static_reason` ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).
  - The other files of the check (for example b2 and b6, and b1 of a b3 family) have
    `published: false` in `external` of the bundle manifest. Do not publish them.
  - No validation rule checks the publication. `intake_bundle.py verify` checks this rule for each
    verdict. `V-common.sizes_and_artifacts-12` checks the batch form of the sidecar.

## `source` and hashes

Each sidecar has a top-level `source`. It also has a `sha256` on every `$ref` and every `filename`
artifact ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). The spec text is in these
section files:

- `source`: section `common.identity`, in
  `../freemocap/skellytracker/specs/model-sidecar/common/identity.md` (rules `V-common.identity-4`
  to `V-common.identity-6`).
- The hashes of `$ref`, and the rules for the bytes of a file: section
  `format.composition`, in `../freemocap/skellytracker/specs/model-sidecar/format/composition.md`
  (the heading "Reference hashes").
- The hash of an artifact and the reserved placeholder: section `common.sizes_and_artifacts`, in
  `../freemocap/skellytracker/specs/model-sidecar/common/sizes-and-artifacts.md` (the heading
  `sizes.<size>.onnx`).

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
  - The tool adds or updates only the `sha256` entries in the files of the sidecar tree. It keeps
    all other bytes. It does not change line endings: on a CRLF file or a file with a BOM, it stops
    with an error and changes no file.
- Then check the hashes:
  `python ../freemocap/skellytracker/tools/sidecar_refs.py --check <sidecar>`. The check must
  pass. It fails on a hash that does not match, on a missing hash, on a CRLF file and on a BOM.
- Never write the placeholder hash (64 zeros). It is valid only in the spec's own examples. Thus do
  not use the option `--placeholder`.
- Publish a sidecar to a shared folder or a Hugging Face repo only when the publish ban allows it
  (see "Publishing").
