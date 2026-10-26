# Sidecar files

## Independence

- A reference implementation made from the code of an exporter is not independent of that exporter.
- In the `verified_against` list of a vector file, the reference implementation and its source
  exporter count as one implementation.
- Only exporters and skellytracker count as implementations in `verified_against`. Do not list the
  upstream library. The spec describes the upstream library, but the library does not implement the
  spec. If you ran a case through upstream code, write that in a comment in the vector file.
- A vector file without a verified implementation has `unverified: <reason>` in place of
  `verified_against`.
- A vector is fully verified only when at least two independent implementations agree: two exporters,
  or an exporter and skellytracker.
- A vector made only from a reading of the spec text is not verified.

## Sidecar YAML

- Quote the integer batch keys: write `"1":`, not `1:`. An unquoted key is a YAML integer, and schema
  validation rejects it.
- Set `schema_version` to the string `vNEXT` until the release step (see "Publishing"). YAML reads
  `vNEXT` and `"vNEXT"` as the same string, so both forms are correct. The spec examples use both
  forms.
- A size entry contains only `input.shape`, `input.resize.target_size` and `onnx`. All other fields
  are shared at the top level (the family invariant under the `sizes` heading in
  `../freemocap/skellytracker/specs/model-sidecar/common/sizes-and-artifacts.md`, rule
  `V-common.sizes_and_artifacts-3`).
- Do not write `null` values. Omit an optional field. In the spec, `null` only deletes an inherited key
  in a `base` merge or a `sizes` merge.

## Path

Put the sidecar at its path in the storage layout of the spec (the heading "Storage layout" in
`../freemocap/skellytracker/specs/model-sidecar/format/file-layout.md`). In the spec, the layout
starts at `{sidecar_root}`. In an exporter, the export root has that role. Thus the
sidecar goes to `<export root>/detectors/...` (the export root of OpenMMLab-Exporter is `exports/`).

- `object_detectors/{family}/{model_id}.yaml` for an object detector. `{family}` is the `model_id`.
- `keypoint_detectors/{family}/{part}/{model_id}.yaml` for a pose estimator. `{part}` is `hand`,
  `face`, `body` or `wholebody`.

The spec does not say where a sidecar with both roles goes. The RTMO body7 reference example uses
`keypoint_detectors/`.

If the storage layout has no branch for the role of the model (a new role), row L1 of the intake is
a `gap`. The proposal that adds the role also adds the branch (`format.file_layout`).

A model-specific folder, such as `body7`, does not conform. For example, the RTMO body7 reference
example has the path `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` under
`../freemocap/skellytracker/specs/model-sidecar/examples/`.
