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

Validation and decode depend on the `schema_version` of the sidecar. `vNEXT` requirements never apply retroactively. The only exceptions are the changes in [Every-version changes](#every-version-changes). For a sidecar with `schema_version < vNEXT`, validation and decode use the legacy meaning below.

This list indexes each "Legacy behaviour" heading that gives a legacy difference. A legacy difference is a rule, a value or a behaviour that is different for an older `schema_version`. A new field, value or section that is not available before `vNEXT` is not a legacy difference. Its availability is in the table of [Legacy behaviour](#legacy-behaviour) of this section.

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

#### Clarifications

A clarification is not a `vNEXT` requirement. A clarification applies to every `schema_version`. A spec change is a clarification only if all of these conditions are true:

- The change defines a result that the text of the older `schema_version` did not define. Examples are the arithmetic precision, the rounding, the tie order and the scale.
- The change keeps each result that the text of the older `schema_version` defined in exact math.
- The change adds no field to an older `schema_version`.
- A new validation rule rejects only a sidecar for which the text of its `schema_version` defined no result.

If one of these conditions is false, the change is a `vNEXT` requirement. Then the rule must have the **(vNEXT)** mark, or the section must give the old meaning in its "Legacy behaviour" heading.

A clarification has no **(vNEXT)** mark. A clarification has no row in a "Legacy behaviour" table. The row of a clarification in the [summary of changes](../changelog.md#summary-of-changes) must say "(every `schema_version`)".

A clarification never changes the meaning of a sidecar. A clarification can make a host non-conforming. A host conforms only if it follows the current text of each section for each `schema_version` that it loads.

#### Every-version changes

Each change in this list applies at every `schema_version`. It can make a sidecar with an older `schema_version` invalid. It is not a clarification. When a change is added to this list, its row in the [summary of changes](../changelog.md#summary-of-changes) must say "(breaking, every `schema_version`)".

- The precision key `int8` is invalid at every `schema_version` ([V-common.sizes_and_artifacts-6](../common/sizes-and-artifacts.md#validation-rules)). A legacy sidecar that lists `int8` is invalid. The current Ultralytics-Exporter sidecars list `int8`.

## Validation rules

- [ ] `V-format.versioning-1` `schema_version` must be a string that matches the skellytracker version pattern. The string must not have a pre-release tag.
- [ ] `V-format.versioning-2` The installed skellytracker release must support `schema_version` (`installed >= schema_version`).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`, `top_k`, `batching.batch_conversion` | Not available. | Available. |

## Implementer guidance

No exporter evidence yet.

skellytracker (decision 0016):

- The capability check: the catalog lists a sidecar as unavailable, with the reason, when the sidecar uses a spec section that skellytracker does not implement. It also lists a sidecar as unavailable when its `schema_version` is newer than the installed release. An attempt to load an unavailable sidecar is an error. The error names the section or the version. Thus a user sees why a model is not available before a run starts. (Decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md#capability-check)) (implementation stage)
- The capability check uses the functions that normalize a resolved sidecar and match it to spec sections: `normalize`, `matches` and `applies` in `tools/sidecar_normalize.py`. They are pure functions. The implementation stage moves them into `skellytracker/core/sidecar/` without changes. Then the trace tool imports them from the package. Do not write these rules again in the check. (`tools/sidecar_normalize.py`; decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md#capability-check)) (implementation stage)
- Map a catalog entry to detector code by its role and its spec sections. Do not select the code by a hand-chosen registry key. Today each detector module loads one sidecar from a fixed path at import, and it registers its class under a hand-chosen key, for example `KEYPOINT_DETECTOR_REGISTRY["rtmpose"]`. (skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`; decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
- Keep the current `detector_type` keys of the sidecar detectors as aliases of `<model_id>@skellytracker`. For example, `rtmpose` is an alias of `rtmw-wholebody@skellytracker`, and `yolox_person` is an alias of `yolox@skellytracker`. (Decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
- A hand-written detector can claim a catalog key. The generic path never handles a claimed key. A claimed key skips the section check, and it is available exactly when its detector is installed. YOLOX claims `yolox@skellytracker`. Its code does things that its sidecar and the spec do not describe. Without the claim, the generic path silently runs a different detector. Remove the claim after a re-export of YOLOX to a contract that the spec describes passes a parity check. (Decisions [0006](../../../decisions/entries/0006-yolox-native-contract.md) and [0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
  - `yolox.yaml` describes the `dets` output of the published OpenMMLab YOLOX file. It does not describe the graph that the detector runs. The values in `yolox.yaml` come from the published file. The tensor names do not: the detector reads the outputs by position.
  - `prepare_yolox_onnx` makes the batch axis dynamic and removes the NMS subgraph. No sidecar field describes this change. Thus `requires_nms: false` does not mean that the detector runs no NMS.
  - `yolox_detection_decode` selects the decode from the output shapes of the loaded graph. No sidecar field describes this selection. (skellytracker `skellytracker/core/detectors/object_detectors/yolox/_yolox_dynamic_batch.py` (`prepare_yolox_onnx`) and `yolox_decode.py` (`yolox_detection_decode`); decision [0006](../../../decisions/entries/0006-yolox-native-contract.md))
- Take the sizes from the `sizes` of the sidecar. An unknown size name is an error, not a silent fallback. Today `RTMWWholebodyDetectorConfig.input_size` returns `(256, 192)` when `model_name` is not a key of the sidecar's `sizes`. `RTMWWholebodyDetector.model_spec` raises `ValueError` for the same name. The `input_size` of `RTMPoseBodyDetectorConfig`, `RTMPoseHandDetectorConfig`, `RTMPoseFaceDetectorConfig` and `YoloxPersonDetectorConfig` has the same fallback, with its own value. (skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py` (`RTMWWholebodyDetectorConfig.input_size`, `RTMWWholebodyDetector.model_spec`); decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)

## Authoring guidance

- Do not publish a `vNEXT` sidecar to a shared or remote sidecar root. No release can load it. After the release step replaces `vNEXT`, regenerate the sidecar with the release version. (Decision [0016](../../../decisions/entries/0016-sidecar-catalogs.md))
- OpenMMLab-Exporter (all three family writers) and Roboflow-Exporter write the placeholder `schema_version: vNEXT`. They never write a release string.
  - `vNEXT` does not match the version pattern (`V-format.versioning-1`). The [decision log](../../../decisions/README.md#open-work) records the release step that replaces `vNEXT`. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:28-30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L28-L30), [`rtmw/sidecar.py:29-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L29-L31) and [`rtmo/sidecar.py:29-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L29-L31); Roboflow-Exporter [`rf_detr/sidecar.py:30-32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L30-L32) and [`README.md:561-563`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/README.md#L561-L563))
- Ultralytics-Exporter and Qualcomm-Exporter write `schema_version: v2024.09.1019`.
  - Their files use `requires_nms`, `may_include_non_person_classes` and `max_detections`. They have no `decode.selection`, `pad_position`, `rounding` or `color_format`. Thus they are valid only under the legacy rules of [Version-aware compatibility](#version-aware-compatibility). (Ultralytics-Exporter [`yolo_sidecar.py:19`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L19), [`yolo_sidecar.py:498-512`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L498-L512), [`yolo_sidecar.py:589-601`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L589-L601); Qualcomm-Exporter [`qai_sidecar.py:12`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L12), [`qai_sidecar.py:124-154`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L124-L154))
  - A move to `vNEXT` needs more than a new version string:
    - `decode.selection` and `decode.nms` replace the legacy keys (`V-post.det.decode-4`, `V-post.det.selection.nms-1`). (Ultralytics-Exporter [`yolo_sidecar.py:467-478`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L467-L478); Qualcomm-Exporter [`qai_sidecar.py:124-133`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L124-L133))
    - A letterbox needs `pad_position` and `rounding` (`V-pre.resize.letterbox-1`). (Ultralytics-Exporter [`yolo_sidecar.py:384-389`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L384-L389); Qualcomm-Exporter [`qai_sidecar.py:144-149`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L144-L149))
    - A `unit_float` input needs `input.color_format` (`V-common.input-6`). (Ultralytics-Exporter [`yolo_sidecar.py:379-390`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L379-L390); Qualcomm-Exporter [`qai_sidecar.py:139-150`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L139-L150))
  - The [changelog](../changelog.md#compatibility-impact) lists what a `vNEXT` sidecar must declare. [Scope of this revision](../changelog.md#scope-of-this-revision) puts Qualcomm-Exporter out of scope until that library is complete.
- A validation claim needs a committed check.
  - The message of the Ultralytics-Exporter [commit](https://github.com/domisjustanumber/Ultralytics-Exporter/commit/f52ef687a7a651447ff289d0e40a7856c2b7d50c) says that the sidecars passed `load_sidecar` on a skellytracker branch. The test that repeats the check skips itself through `pytest.importorskip`, because skellytracker is not a dependency of the exporter. (Ultralytics-Exporter commit message and [`tests/test_yolo_sidecar.py:568-579`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L568-L579); Ultralytics-Exporter [`pyproject.toml`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/pyproject.toml))
  - The Qualcomm-Exporter README says that the sidecar passed `load_sidecar()`, but no test or script in that repo calls it. (Qualcomm-Exporter [`README.md:108-113`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/README.md#L108-L113))
