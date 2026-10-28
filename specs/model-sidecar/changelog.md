# Changelog

## Changes in this revision (`vNEXT`)

> **For reviewers.** This revision extends the contract so that every model produced by
> `Roboflow-Exporter` (RF-DETR), `OpenMMLab-Exporter` (RTMDet, RTMW) and `Ultralytics-Exporter`
> (YOLO26 detection and pose) can be described. The evidence behind each change, and the per-repo
> findings, are in [`sidecar-exporter-coverage.md`](../../notes/sidecar-exporter-coverage.md).
> `vNEXT` is a placeholder: replace it with the skellytracker release that ships this revision before
> merging. It appears in the examples, the changelog and the compatibility table.

Compatibility rows: [Version-aware compatibility](format/versioning.md#version-aware-compatibility).

### Summary of changes

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| 1 | Resize | New `input.resize.method: stretch` (independent x/y resize, no pad). | RF-DETR | [`input.resize`](pre/resize-stretch.md) |
| 2 | Resize | New `input.resize.method: fit` (full-frame affine fit with centered fractional padding and a constant border value). | RTMO Body7 | [`input.resize`](pre/resize-fit.md) |
| 3 | Resize | Letterbox gains **required** `pad_position` (`top_left` \| `center`) and `rounding` (`half_even` \| `half_up`), with normative centre offsets and an exact-inverse unprojection. `pad_value` accepts a scalar or a per-channel array. | YOLO26 (centre, half-even), RTMDet (top-left, half-up) | [`input.resize`](pre/resize-letterbox.md) |
| 4 | Resize | Normative unprojection for each method. All resizes are defined as **non-antialiased**. | all | [Unprojection](post/unprojection.md) |
| 5 | Resize | `affine_person_crop` defines `maintain_aspect_ratio` and adds `crop_policy.pad_value`. | RTMW | [`input.resize`](pre/resize-affine-person-crop.md) |
| 6 | Input | New `input.color_format` (`rgb` \| `bgr`), required when normalization is channel-agnostic (`none`/`unit_float`). `none` now means "pixels unchanged in `input.dtype`" (not only uint8). The `imagenet_*` channel order is spelled out. **Behaviour change:** at `vNEXT`, `imagenet_bgr` applies BGR-ordered statistics (B mean `103.53`). Legacy sidecars keep the old meaning (the RGB-ordered tuple on BGR pixels, as rtmlib does). | YOLO26, RF-DETR, RTMDet | [`input`](common/input.md), [Normalization modes](pre/normalization.md) |
| 7 | Outputs | New detection semantics `boxes`, `scores` and `class_logits`, with `class_axis`. Output names must be unique. | RF-DETR (`dets` + `labels` logits), RTMDet (`boxes` + `scores`) | [Detection output semantics](post/detection-outputs.md#detection-output-semantics) |
| 8 | Decode | Detection `decode` is rebuilt around a required `selection` (`none` \| `top_k` \| `nms`), output bindings (`boxes_output`, `scores_output`, `class_logits_output`), `box_scale`, `score_activation`, `class_id_map`, `clamp_boxes` and an `nms` block (`iou_threshold`, `score_threshold`, `class_agnostic`, `post_nms_top_k`). Stage order is normative, and score thresholds are strict (`>`). | RF-DETR (query×class top-k), RTMDet (host NMS), YOLO26 (graph-final rows) | [`decode`](post/detection-decode.md#decode-detection), [Selection behaviour](post/detection-decode.md#selection-behaviour) |
| 9 | Decode | `max_detections` no longer defaults to `300`. It now only declares the graph's fixed final row count, and is valid only with `selection: none`. `requires_nms` becomes a legacy alias of `selection`. `may_include_non_person_classes` is replaced by `is_person_only` (the old field inverted). | all detectors | [`decode`](post/detection-decode.md#decode-detection) |
| 10 | Pose | New `packed_keypoints` on a `detections` output, for one-stage models that pack keypoints into the detection row. | YOLO26 pose (`[N,300,57]`) | [`packed_keypoints`](post/pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows) |
| 11 | Pose | Bottom-up instance count is no longer overloaded onto `max_detections`. Pose rows are row-aligned with detection rows and gathered by the surviving detection indices. | YOLO26 pose, RTMO | [Bottom-up decode](post/pose-bottom-up.md#bottom-up-decode) |
| 12 | Sizes | **Family invariant:** a size entry may set only `input.shape`, `input.resize.target_size` and `onnx`. Sizes that differ in channel order, normalization or post-processing must be separate families. This resolves the earlier contradiction between "a size is a partial document deep-merged over the top level" and "sizes share the output contract". | RTMDet person-only vs 80-class families (different NMS contracts and class counts) | [`sizes`](common/sizes-and-artifacts.md#sizes) |
| 13 | Versioning | Explicit version-aware rules so that sidecars older than `vNEXT` keep loading with their old meaning. | existing YOLOX/RTMPose sidecars | [Version-aware compatibility](format/versioning.md#version-aware-compatibility) |
| 14 | Examples | Reference examples rewritten for this revision. RTMDet person, RTMW and RTMO body7 come from real `vNEXT` exports of OpenMMLab-Exporter; RTMDet uses its person-only family. YOLO26 detection and YOLO26 pose are written from Ultralytics-Exporter's code and will be replaced when it emits `vNEXT`. There is no RF-DETR example until Roboflow-Exporter is overhauled. All batch keys are quoted, and the YOLO26 int8 input dtype is corrected to `float32`. | all | [Reference examples](examples/README.md) |
| 15 | Identity | New top-level `source` mapping with `name` (the package name of the library that wrote the sidecar) and `version` (the version of that library). It is required. A legacy sidecar has no `source`. Its default is `{name: skellytracker, version: <schema_version>}`. | sidecar catalogs: `model_id` is not unique across sources (decision [0016](../../decisions/0016-sidecar-catalogs.md)) | [`source`](common/identity.md#fields) |
| 16 | Composition | A `$ref` mapping holds exactly `$ref` and `sha256`. `base` has the same `{$ref, sha256}` form. `sha256` is the SHA-256 of the exact bytes of the target file. The resolver checks it before it parses the file. Sidecars and fragments are UTF-8 without a BOM, with LF line endings. Legacy sidecars keep the one-key form without hashes. | sidecar catalogs: each root holds its own fragments (decision [0016](../../decisions/0016-sidecar-catalogs.md)) | [Reference hashes](format/composition.md#reference-hashes) |
| 17 | Artifacts | New artifact field `sha256` with `filename`: the SHA-256 of the file that `filename` names. It is required on every artifact. `url_sha256` stays with `url`. A 64-zero placeholder is valid only in the spec's examples. | ONNX files next to a sidecar have no hash (decision [0016](../../decisions/0016-sidecar-catalogs.md)) | [`sizes.<size>.onnx.batch_artifacts`](common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) |
| 18 | Layout | `{cache_dir}` has the new name `{sidecar_root}`. A sidecar root is the package root, a local folder that a user adds or a Hugging Face repo snapshot. Each root follows the storage layout. A discovery rule tells a sidecar from the other YAML files. | sidecar catalogs: "cache dir" names two folders, and nothing defines which YAML files are sidecars (decision [0016](../../decisions/0016-sidecar-catalogs.md)) | [Sidecar roots](format/file-layout.md#sidecar-roots), [Discovery](format/file-layout.md#discovery) |
| 19 | Examples | Every reference example has `source` and all hashes. The `$ref` hashes are real. The ONNX artifacts have the placeholder. | all (decision [0016](../../decisions/0016-sidecar-catalogs.md)) | [Reference examples](examples/README.md) |
| 20 | Batching | New draft `batching.batch_conversion` (`profile_id`, `source_batch_size`) and profile `static-batch-v1`. | YOLO26 (static-batch exports) | [Batch conversion](common/batch-conversion.md) |

### Considered and deliberately not added

Each of these can be added later as a non-breaking schema bump when a model needs it.

| Field / feature | Reason |
|-----------------|--------|
| `resize.antialias`, `resize.size_divisor` | No in-scope model antialiases or has dynamic spatial dims. Resizes are normatively non-antialiased. |
| `crop_policy.border_mode`, rotated crops | Only constant borders and zero rotation are used. |
| `score_activation: softmax` | No model uses it, and how it behaves over gap/background slots is unresolved. |
| `class_id_map_before_selection` | No model maps classes before top-k. "Map after selection" is normative. |
| `class_logits` with `selection: nms` (each (row, class) pair above the score threshold becomes a candidate, followed by per-class NMS) | No in-scope family needs it after the COCO-80 RTMDet family was dropped. On NMS-free RTMDet-tiny it reproduced PyTorch AP (0.4114 vs 0.4112), while best-class-per-row `scores` + `class_ids` lost 0.0051 AP / 0.031 AR. Add it as a non-breaking bump if a multi-class NMS-free family appears. |
| `nms.pre_nms_top_k` | A flat candidate list cannot express mmdet's per-level `nms_pre` cap without a `level_strides` field. It had no measured AP effect on person-medium (0.6255 with or without it) or RTMDet-tiny (0.4114 vs 0.4113); it only reduces host NMS time at near-zero score thresholds. |
| `nms.min_bbox_size` | No in-scope model uses it; the value is `0` everywhere. |
| `graph_candidate_limit` | Informational only; the host can't act on it. NMS-free exports have no graph-side candidate cap to describe; detection outputs are normatively the complete candidate set. |
| `pose.decode.instance_count` | The count is derivable from the detection row axis (change 11). |
| Soft-NMS / per-class IoU, masks, multi-input models, quantized outputs | Out of scope. No in-scope model needs them. |

### Compatibility impact

- Sidecars with `schema_version < vNEXT` (e.g. the in-repo YOLOX and RTMPose sidecars) keep loading unchanged under the [legacy rules](format/versioning.md#version-aware-compatibility).
- Sidecars authored at `vNEXT` must declare `decode.selection`, letterbox `pad_position`/`rounding`, `fit` `pad_value`, and `color_format` where required. They must not use `requires_nms` alone, `may_include_non_person_classes`, `letterbox` + `preserve_aspect_ratio: false`, or size-level overrides other than `input.shape`, `input.resize.target_size` and `onnx`.
- Sidecars authored at `vNEXT` must also declare `source`. They must declare `sha256` on each `$ref`, each `base` and each artifact. The sidecar and each file in its tree must be UTF-8 without a BOM, with LF line endings.

## `schema_version` history

Every future contract change must bump `schema_version` to the skellytracker release that ships it and add a changelog row below.

| `schema_version` | Changes |
|------------------|---------|
| `v2024.09.1019` | Initial YAML sidecar spec: one `{model_id}.yaml` per family with a `sizes` map (size × batch × precision via `sizes.<size>.onnx.batch_artifacts`, incl. `dynamic` batch); `role` arrays (`object_detector` / `pose_estimator`, both for one-stage models); `input.normalization` modes (`none`, `unit_float`, `imagenet_bgr`, `imagenet_rgb`, `custom`) with per-precision overrides; `input.resize` (`letterbox` + `affine_person_crop` with `crop_policy`, `none`, interpolation); file composition (`$ref` includes + `base` inheritance with `null`-delete); `schema_version` as skellytracker version string; pose output contract (`tracked_points`, named `connections`, `derived_points`, `canonical_mapping` with `prefixes`, `overlay.groups`, `requires_object_detector`, and `decode` incl. `simcc`/`heatmap`/`coordinate` with 3D via `is_3d`/`depth_unit`/`depth_range`); VRM 1.0 canonical skeleton with current→VRM name-migration note; `detectors/` storage layout; per-precision `url` with mandatory `url_sha256`. |
| `vNEXT` | Added `input.resize.method: stretch`; added `input.resize.method: fit` (full-frame affine fit with unrounded scale and centred fractional offsets; `pad_value` required) and its unprojection; letterbox `pad_position` and `rounding` (required), normative letterbox/centre-offset algorithm, per-method unprojection, non-antialiased resizes, scalar/array `pad_value`; `affine_person_crop` warp definition with `crop_policy.pad_value`. Added `input.color_format` (required for `none`/`unit_float`); `none` passes pixels in `input.dtype`; explicit `imagenet_*` channel order (`imagenet_bgr` now uses BGR-ordered statistics; legacy meaning retained for older sidecars). Added detection semantics `boxes`, `scores` and `class_logits` (with `class_axis`); output names must be unique. Rebuilt detection `decode` around required `selection` (`none`/`top_k`/`nms`) with output bindings, `box_scale`, `score_activation`, `class_id_map`, `top_k`, `nms` (`iou_threshold`, `score_threshold`, `class_agnostic`, `post_nms_top_k`), `clamp_boxes`, `is_person_only`; normative stage order and strict thresholds. `max_detections` has no default and only declares a graph-final row count; `requires_nms` and `may_include_non_person_classes` are legacy. Added `packed_keypoints` for bottom-up packed rows; bottom-up pose rows follow surviving detection rows. Size entries limited to `input.shape`, `input.resize.target_size`, `onnx` (family invariant). Added version-aware compatibility rules. Added the required top-level `source` (`name`, `version`). A legacy sidecar has the default `{name: skellytracker, version: <schema_version>}`. Each `$ref` and each `base` holds the `sha256` of its target file, in the form `{$ref, sha256}`. Sidecars and fragments are UTF-8 without a BOM, with LF line endings. Each artifact holds the `sha256` of the file that `filename` names. `{cache_dir}` has the new name `{sidecar_root}`. Added the sidecar roots and the discovery rule. Added the draft `batching.batch_conversion` (`profile_id`, `source_batch_size`) and the profile `static-batch-v1`. |
