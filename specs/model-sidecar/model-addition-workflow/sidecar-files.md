# Sidecar files

These rules apply to each contributor that writes a sidecar or a vector file.

## Independence

- A reference implementation made from the code of an exporter is not independent of that exporter.
- In the `verified_against` list of a vector file, the reference implementation and its source
  exporter count as one implementation.
- Only exporters and skellytracker count as implementations in `verified_against`. Do not list the
  upstream library. The spec describes the upstream library, but the library does not implement the
  spec. If you ran a case through upstream code, write that in the `note` of the case.
- List an implementation in `verified_against` only when it gives the same results
  ([ADR-ESP4](../../../decisions/entries/ESP4-one-home-for-each-workflow-rule.md)).
- A vector file without a verified implementation has `unverified: <reason>` in place of
  `verified_against`. For example, the host code does not exist or is not committed.
- A vector is fully verified only when at least two independent implementations agree: two exporters,
  or an exporter and skellytracker.
- A vector made only from a reading of the spec text is not verified.

## Sidecar YAML

- Write `batching.batch` as the integer `3` or `1`, or as the string `dynamic`
  (`V-common.sizes_and_artifacts-12`). Do not quote `3` or `1`.
- Set `schema_version` to the quoted string `"2.0.0"`, the open target. Write the quotes: YAML reads
  an unquoted `2.0` as a number, and a number is not a valid `schema_version`
  (`V-format.versioning-1`; [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
  Write a pre-release value only in a test sidecar (see
  [Publishing](validation-and-publishing.md#publishing)).
- A size entry contains only `input.shape`, `input.resize.target_size` and `onnx`. All other fields
  are shared at the top level (the family invariant under the `sizes` heading in
  `../freemocap/skellytracker/specs/model-sidecar/common/sizes-and-artifacts.md`, rule
  `V-common.sizes_and_artifacts-3`).
- Each size has `onnx.output_shapes`. `outputs[].shape` stays optional. For example, the RTMW SimCC
  outputs have no `shape` (the heading "Authoring guidance" in
  `../freemocap/skellytracker/specs/model-sidecar/common/outputs.md`).
- Do not write `null` values. Omit an optional field. No field has the value `null` (the heading
  "Behaviour" in `../freemocap/skellytracker/specs/model-sidecar/format/composition.md`).

## Path

Put the sidecar at its path in the storage layout of the spec (the heading "Storage layout" in
`../freemocap/skellytracker/specs/model-sidecar/format/file-layout.md`). In the spec, the layout
starts at `{sidecar_root}`. In your repo, the export root (the folder that holds your exported
files) has that role. Thus the sidecar goes to `<export root>/detectors/...`. For example, the
export root of OpenMMLab-Exporter is `exports/`.

- `object_detectors/{family}/{model_id}.yaml` for an object detector. `{family}` is the `model_id`.
- `keypoint_detectors/{family}/{group}/{model_id}.yaml` for a pose estimator. `{group}` is `hand`,
  `face`, `body` or `wholebody`, or a keypoint set with its keypoint count, for example
  `wholebody133` (`V-common.identity-8`; [ADR-1TR6](../../../decisions/entries/1TR6-workflow-copies-of-the-keypoint-detector-id.md)).

The spec does not say where a sidecar with both roles goes. The one-stage pose exporters write it
under `keypoint_detectors/` ([Spec defects](../decisions/open-work.md#spec-defects)).

If the storage layout has no branch for the role of the model (a new role), row L1 of the intake is
a `gap`. The proposal that adds the role also adds the branch (`format.file_layout`).

A folder that is not a group, such as `body7`, does not conform (`V-common.identity-8`).
