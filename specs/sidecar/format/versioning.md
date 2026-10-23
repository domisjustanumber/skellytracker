---
id: format.versioning
title: Schema versioning
kind: format
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_schema_version_pattern  # partial. Checks the pattern and the stable-only rule. load_sidecar rejects a too-new version. No code applies the legacy rules.
  load: skellytracker/core/sidecar/versioning.py::parse_skellytracker_version  # partial. The parser needs the leading v. The section says the v is optional.
external_impl: []
tests: [skellytracker/tests/sidecar/test_model_validation.py]
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# Schema versioning

## Behaviour

`schema_version` is a **string**. It matches the skellytracker release version that introduced a change to the sidecar contract or last required a change to it.

| Aspect | Rule |
|--------|------|
| Field | `schema_version` |
| Type | string |
| Value | The exact skellytracker release version, for example `"v2024.09.1019"` |
| Pattern | `vYYYY.0M.BUILD[-TAG]` |

See also [`schema_version` history](../changelog.md#schema_version-history).

### Semantics

- **`schema_version` on a sidecar** is the skellytracker version that defined the contract. The author wrote the sidecar to follow that contract.
- **Minimum consumer** — When `S >= V`, skellytracker release `S` loads a sidecar with `schema_version` `V`. A newer skellytracker release still supports an older sidecar (lower `schema_version`), unless a release note says otherwise. An older skellytracker release rejects a newer sidecar (higher `schema_version`).
- **Too-new sidecar** — If `sidecar.schema_version > installed_skellytracker_version`, reject the sidecar with a recoverable error. The error names both versions and gives an upgrade hint.
- **Exporter obligation** — Set `schema_version` to the skellytracker version that the documentation names as current at the time of the export.
- **Stable versions only** — A sidecar must not use a pre-release tag (`-TAG` suffix).

### Version comparison

`parse_skellytracker_version(version) -> (year, month, build, tag)`:

1. Strip an optional leading `v`.
2. Split on `-` into `core` and an optional `tag`.
3. Parse `core` as `YYYY.MM.BUILD`. This format has three integers with a dot between them.
4. Compare `(year, month, build, tag)` lexicographically. `tag=None` sorts **after** a tagged pre-release of the same core (stable > pre-release).

### Version-aware compatibility

Validation and decode depend on the `schema_version` of the sidecar. `vNEXT` requirements never apply retroactively. For a sidecar with `schema_version < vNEXT`, validation and decode use the legacy meaning below.

- [File composition](composition.md#legacy-behaviour)
- [Schema versioning](versioning.md#legacy-behaviour)
- [Identity](../common/identity.md#legacy-behaviour)
- [Sizes and artifacts](../common/sizes-and-artifacts.md#legacy-behaviour)
- [Input](../common/input.md#legacy-behaviour)
- [Letterbox resize](../pre/resize-letterbox.md#legacy-behaviour)
- [Normalization](../pre/normalization.md#legacy-behaviour)
- [Detection decode](../post/detection-decode.md#legacy-behaviour)
- [Selection: none](../post/selection-none.md#legacy-behaviour)
- [Selection: NMS](../post/selection-nms.md#legacy-behaviour)
- [Bottom-up pose](../post/pose-bottom-up.md#legacy-behaviour)

## Validation rules

- [ ] `V-format.versioning-1` `schema_version` must be a string that matches the skellytracker version pattern. The string must not have a pre-release tag.
- [ ] `V-format.versioning-2` The installed skellytracker release must support `schema_version` (`installed >= schema_version`).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map` | Not available. | Available. |

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- OpenMMLab-Exporter (all three family writers) and Roboflow-Exporter write the placeholder `schema_version: vNEXT`. They never write a release string.
  - `vNEXT` does not match the version pattern (`V-format.versioning-1`). The [decision log](../../../notes/decisions/README.md#open-work) records the release step that replaces `vNEXT`. (OpenMMLab-Exporter `rtmdet_person/sidecar.py:28-30`, `rtmw/sidecar.py:29-31` and `rtmo/sidecar.py:29-31`, eed3361; Roboflow-Exporter `rf_detr/sidecar.py:30-32` and `README.md:561-563`, b34e351)
- Ultralytics-Exporter and Qualcomm-Exporter write `schema_version: v2024.09.1019`.
  - Their files use `requires_nms`, `may_include_non_person_classes` and `max_detections`. They have no `decode.selection`, `pad_position`, `rounding` or `color_format`. Thus they are valid only under the legacy rules of [Version-aware compatibility](#version-aware-compatibility). (Ultralytics-Exporter `yolo_sidecar.py:19, 498-512, 589-601`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:12, 124-154`, 4ca4586)
  - A move to `vNEXT` needs more than a new version string:
    - `decode.selection` and `decode.nms` replace the legacy keys (`V-post.det.decode-4`, `V-post.det.selection.nms-1`). (Ultralytics-Exporter `yolo_sidecar.py:467-478`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:124-133`, 4ca4586)
    - A letterbox needs `pad_position` and `rounding` (`V-pre.resize.letterbox-1`). (Ultralytics-Exporter `yolo_sidecar.py:384-389`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:144-149`, 4ca4586)
    - A `unit_float` input needs `input.color_format` (`V-common.input-6`). (Ultralytics-Exporter `yolo_sidecar.py:379-390`, f52ef68; Qualcomm-Exporter `qai_sidecar.py:139-150`, 4ca4586)
  - The [changelog](../changelog.md#compatibility-impact) lists what a `vNEXT` sidecar must declare. [Decision 0008](../../../notes/decisions/0008-vnext-scope.md) puts Qualcomm-Exporter out of scope until that library is complete.
- A validation claim needs a committed check.
  - The message of Ultralytics-Exporter commit f52ef68 says that the sidecars passed `load_sidecar` on a skellytracker branch. The test that repeats the check skips itself through `pytest.importorskip`, because skellytracker is not a dependency of the exporter. (Ultralytics-Exporter commit message and `tests/test_yolo_sidecar.py:568-579`, f52ef68; Ultralytics-Exporter `pyproject.toml`, f52ef68)
  - The Qualcomm-Exporter README says that the sidecar passed `load_sidecar()`, but no test or script in that repo calls it. (Qualcomm-Exporter `README.md:108-113`, 4ca4586)
