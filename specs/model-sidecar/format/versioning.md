---
id: format.versioning
title: Schema versioning
kind: format
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::SidecarModel._check_schema_version_pattern  # partial. Checks the pattern and the stable-only rule. load_sidecar rejects a too-new version.
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
- **Implemented versions only** — A host loads only the `schema_version` values that it implements. Each sidecar has one reading: the current text of the spec. The spec has no legacy reading of an older `schema_version` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
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

Removed. The spec has no legacy reading of an older `schema_version` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).

## Validation rules

- [ ] `V-format.versioning-1` `schema_version` must be a string that matches the skellytracker version pattern. The string must not have a pre-release tag.
- [ ] `V-format.versioning-2` The installed skellytracker release must support `schema_version` (`installed >= schema_version`).

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
  - `vNEXT` does not match the version pattern (`V-format.versioning-1`). The [implementation plan](../../sidecar-implementation-plan.md) records the release step that replaces `vNEXT`. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:28-30`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmdet_person/sidecar.py#L28-L30), [`rtmw/sidecar.py:29-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L29-L31) and [`rtmo/sidecar.py:29-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmo/sidecar.py#L29-L31); Roboflow-Exporter [`rf_detr/sidecar.py:30-32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L30-L32) and [`README.md:561-563`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/README.md#L561-L563))
- A validation claim needs a committed check.
  - The message of the Ultralytics-Exporter [commit](https://github.com/domisjustanumber/Ultralytics-Exporter/commit/f52ef687a7a651447ff289d0e40a7856c2b7d50c) says that the sidecars passed `load_sidecar` on a skellytracker branch. The test that repeats the check skips itself through `pytest.importorskip`, because skellytracker is not a dependency of the exporter. (Ultralytics-Exporter commit message and [`tests/test_yolo_sidecar.py:568-579`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L568-L579); Ultralytics-Exporter [`pyproject.toml`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/pyproject.toml))
  - The Qualcomm-Exporter README says that the sidecar passed `load_sidecar()`, but no test or script in that repo calls it. (Qualcomm-Exporter [`README.md:108-113`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/README.md#L108-L113))
