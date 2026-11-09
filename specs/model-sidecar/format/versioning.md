---
id: format.versioning
title: Schema versioning
kind: format
selectors: []
implemented_by:
  validate: missing  # SidecarModel._check_schema_version_pattern (skellytracker/core/sidecar/model.py) requires a CalVer release string vYYYY.0M.BUILD and rejects "2.0.0" (decisions/entries/6GE2-spec-version-follows-skellytracker.md).
  load: missing  # load_sidecar compares CalVer release versions with parse_skellytracker_version (skellytracker/core/sidecar/versioning.py) and rejects "2.0.0" (decisions/entries/6GE2-spec-version-follows-skellytracker.md).
external_impl: []
tests: [skellytracker/tests/sidecar/test_model_validation.py]
vectors: null
status: {spec: stable, validate: missing, load: missing}
---

# Schema versioning

## Behaviour

`schema_version` is a **string**. The spec version is the skellytracker version, in SemVer, that first releases a spec change. A skellytracker release with no spec change makes no spec version ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

| Aspect | Rule |
|--------|------|
| Field | `schema_version` |
| Type | string |
| Value | `"2.0.0"` |
| Pattern | SemVer `MAJOR.MINOR.PATCH`, with an optional SemVer pre-release tag, for example `"2.0.0-rc.1"` |

Write the value in quotes. An unquoted value can load as a number: YAML reads an unquoted `2.0` as a float. A number is not a valid `schema_version` (`V-format.versioning-1`; [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

See also [`schema_version` history](../changelog.md#schema_version-history).

### Semantics

- **`schema_version` on a sidecar** names the spec version that the sidecar follows. The current version is the open target `"2.0.0"`. Each spec change targets the next skellytracker release until that release ships ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- **Implemented versions only** — A host loads only the `schema_version` values that it implements. Each skellytracker release lists the versions that it implements. It is not necessary for a release to implement an older version ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). Each sidecar has one reading: the current text of the spec. The spec has no legacy reading of an older `schema_version` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
- **Pre-release version** — A pre-release value names the open target at that skellytracker pre-release. A pre-release host lists its own pre-release value and the open target. No other host implements a pre-release value. Thus the final `2.0.0` does not load a `"2.0.0-rc.1"` sidecar ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- **Unknown version** — A host rejects a sidecar with a `schema_version` that it does not implement. The error names the version ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

### Version-aware compatibility

Removed. The spec has no legacy reading of an older `schema_version` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).

## Validation rules

- [ ] `V-format.versioning-1` `schema_version` must be a string that is a version heading of the [changelog](../changelog.md#revisions) or a recorded pre-release of the open target. Until `2.0.0` ships, only `"2.0.0"` and its recorded pre-releases are valid ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- [ ] `V-format.versioning-2` A host must reject a `schema_version` that it does not implement, with an error that names the version ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

## Implementer guidance

No exporter evidence yet.

skellytracker ([ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md)):

- The capability check: the catalog lists a sidecar as unavailable, with the reason, when the sidecar uses a spec section that skellytracker does not implement. It also lists a sidecar as unavailable when skellytracker does not implement its `schema_version` ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). An attempt to load an unavailable sidecar is an error. The error names the section or the version. Thus a user sees why a model is not available before a run starts. ([ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#capability-check)) (implementation stage)
- A host lists an older spec version only while its current text still reads that version the same way. When a later version changes the meaning of a field, a host stops listing the older version. Do not add a legacy reading for an older `schema_version` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md); [ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). (implementation stage)
- The capability check uses the functions that normalize a resolved sidecar and match it to spec sections: `normalize`, `matches` and `applies` in `tools/sidecar_normalize.py`. They are pure functions. The implementation stage moves them into `skellytracker/core/sidecar/` without changes. Then the trace tool imports them from the package. Do not write these rules again in the check. (`tools/sidecar_normalize.py`; [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#capability-check)) (implementation stage)
- Map a catalog entry to detector code by its role and its spec sections. Do not select the code by a hand-chosen registry key. Today each detector module loads one sidecar from a fixed path at import, and it registers its class under a hand-chosen key, for example `KEYPOINT_DETECTOR_REGISTRY["rtmpose"]`. (skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`; [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
- Keep the current `detector_type` keys of the sidecar detectors as aliases of `<model_id>@skellytracker`. For example, `rtmpose` is an alias of `rtmw-wholebody@skellytracker`, and `yolox_person` is an alias of `yolox@skellytracker`. ([ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
- A hand-written detector can claim a catalog key. The generic path never handles a claimed key. A claimed key skips the section check, and it is available exactly when its detector is installed. YOLOX claims `yolox@skellytracker`. Its code does things that its sidecar and the spec do not describe. Without the claim, the generic path silently runs a different detector. Remove the claim after a re-export of YOLOX to a contract that the spec describes passes a parity check. ([ADR-0006](../../../decisions/entries/0006-yolox-native-contract.md) and [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)
  - `yolox.yaml` describes the `dets` output of the published OpenMMLab YOLOX file. It does not describe the graph that the detector runs. The values in `yolox.yaml` come from the published file. The tensor names do not: the detector reads the outputs by position.
  - `prepare_yolox_onnx` makes the batch axis dynamic and removes the NMS subgraph. No sidecar field describes this change. Thus `requires_nms: false` does not mean that the detector runs no NMS.
  - `yolox_detection_decode` selects the decode from the output shapes of the loaded graph. No sidecar field describes this selection. (skellytracker `skellytracker/core/detectors/object_detectors/yolox/_yolox_dynamic_batch.py` (`prepare_yolox_onnx`) and `yolox_decode.py` (`yolox_detection_decode`); [ADR-0006](../../../decisions/entries/0006-yolox-native-contract.md))
- Take the sizes from the `sizes` of the sidecar. An unknown size name is an error, not a silent fallback. Today `RTMWWholebodyDetectorConfig.input_size` returns `(256, 192)` when `model_name` is not a key of the sidecar's `sizes`. `RTMWWholebodyDetector.model_spec` raises `ValueError` for the same name. The `input_size` of `RTMPoseBodyDetectorConfig`, `RTMPoseHandDetectorConfig`, `RTMPoseFaceDetectorConfig` and `YoloxPersonDetectorConfig` has the same fallback, with its own value. (skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py` (`RTMWWholebodyDetectorConfig.input_size`, `RTMWWholebodyDetector.model_spec`); [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#detector-dispatch)) (implementation stage)

## Authoring guidance

- Do not publish a sidecar to a shared or remote sidecar root until a final skellytracker release loads its `schema_version`. A pre-release does not end this ban. The private Hugging Face test repo of the implementation stage is the one exception. skellytracker `2.0.0` ships the SemVer loader, so its release ends the ban for `"2.0.0"` ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md); [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md)).
- A sidecar with a pre-release value, for example `"2.0.0-rc.1"`, is a test sidecar. Put it only in the private test repo. After the final release, export the sidecar again ([ADR-6GE2](../../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- The OpenMMLab-Exporter draft writers of `rtmdet-person` and RTMO and Roboflow-Exporter write a placeholder `schema_version`, not the string `"2.0.0"`.
  - The OpenMMLab-Exporter rtmw writer follows spec 2.0.0. The pipeline adds `schema_version: "2.0.0"` to its document. The run never calls a draft writer. (OpenMMLab-Exporter [`pipeline/sidecar.py:50-51`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L50-L51), [`pipeline/sidecar.py:196`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/sidecar.py#L196) and [`pipeline/family.py:34-38`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/pipeline/family.py#L34-L38))
  - The placeholder fails `V-format.versioning-1`. The [re-export request](../decisions/open-work.md#re-export-requests) asks for the change. (OpenMMLab-Exporter [`rtmdet_person/sidecar.py:29-31`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/sidecar.py#L29-L31), [`rtmo/sidecar.py:30-32`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/sidecar.py#L30-L32), [`rtmdet_person/adapter.py:11-12`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmdet_person/adapter.py#L11-L12) and [`rtmo/adapter.py:17-19`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/3e326df00726df8110773ed62cf38d02948a71a5/rtmo/adapter.py#L17-L19); Roboflow-Exporter [`rf_detr/sidecar.py:30-32`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L30-L32) and [`README.md:561-563`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/README.md#L561-L563))
  - Ultralytics-Exporter writes the release string `v2024.09.1019`. It also fails `V-format.versioning-1`. (Ultralytics-Exporter [`yolo_sidecar.py:19`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/yolo_sidecar.py#L19))
- A validation claim needs a committed check.
  - The message of the Ultralytics-Exporter [commit](https://github.com/domisjustanumber/Ultralytics-Exporter/commit/f52ef687a7a651447ff289d0e40a7856c2b7d50c) says that the sidecars passed `load_sidecar` on a skellytracker branch. The test that repeats the check skips itself through `pytest.importorskip`, because skellytracker is not a dependency of the exporter. (Ultralytics-Exporter commit message and [`tests/test_yolo_sidecar.py:568-579`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L568-L579); Ultralytics-Exporter [`pyproject.toml`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/pyproject.toml))
  - The Qualcomm-Exporter README says that the sidecar passed `load_sidecar()`, but no test or script in that repo calls it. (Qualcomm-Exporter [`README.md:108-113`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/README.md#L108-L113))
