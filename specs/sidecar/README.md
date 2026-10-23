# Model Sidecar Specification

## Overview

A **sidecar** is a YAML file that sits beside one or more ONNX model files and describes the runtime I/O contract a host must satisfy to load and run them correctly: input tensor, normalization, resize, batching, output semantics, and decode.

Sidecars support two model **roles**:

| Role | Purpose |
|------|---------|
| `object_detector` | Object detection (e.g. YOLO26, RF-DETR, RTMDet) — emits boxes, scores, and class information. |
| `pose_estimator` | Pose estimation (e.g. RTMW, RTMPose) — emits keypoint coordinates. |

A sidecar may declare **both** roles — e.g. a one-stage model such as RTMO or YOLO26-pose that emits boxes and keypoints in the same pass. In that case `role` lists both values, and `outputs` mixes detection and pose tensors (or packs keypoints into the detection rows; see [`packed_keypoints`](post/pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows)).

### Core properties

- **One sidecar per model family.** A single `{model_id}.yaml` file lists every size of the model, and within each size every native batch size and precision variant, via `sizes.<size>.onnx.batch_artifacts`.
- **Multiple sizes per sidecar.** A family ships several sizes (e.g. `nano`, `small`, `medium`) in one file. All sizes share one preprocessing and output contract and differ only in input size and ONNX artifacts (see [`sizes`](common/sizes-and-artifacts.md#sizes)).
- **Traceable compatibility.** A sidecar's `schema_version` identifies the minimum skellytracker release required to consume it.
- **Single source of truth.** This document is the canonical, human-readable contract. It is **not parsed at runtime**; skellytracker mirrors it with Pydantic `BaseModel` subclasses (the `SidecarModel` hierarchy), and documentation and validators must stay aligned.
- **Composable.** A sidecar may `$ref` shared YAML fragments and may `base` another sidecar to inherit and override values.

This specification is split into section files; see the [Section map](#section-map).

Also: [Changelog](changelog.md) and [Reference examples](examples/README.md).

## Section map

### Format

| Section ID | File | Title |
|------------|------|-------|
| `format.file_layout` | [format/file-layout.md](format/file-layout.md) | File layout |
| `format.composition` | [format/composition.md](format/composition.md) | File composition |
| `format.versioning` | [format/versioning.md](format/versioning.md) | Schema versioning |

### Common fields

Fields shared by every sidecar regardless of `role`.

| Section ID | File | Title |
|------------|------|-------|
| `common.identity` | [common/identity.md](common/identity.md) | Identity |
| `common.sizes_and_artifacts` | [common/sizes-and-artifacts.md](common/sizes-and-artifacts.md) | Sizes and artifacts |
| `common.batching` | [common/batching.md](common/batching.md) | Batching |
| `common.input` | [common/input.md](common/input.md) | Input |
| `common.outputs` | [common/outputs.md](common/outputs.md) | Outputs |
| `post.unprojection` | [post/unprojection.md](post/unprojection.md) | Unprojection |

### Pre-processing

| Section ID | File | Title |
|------------|------|-------|
| `pre.resize.letterbox` | [pre/resize-letterbox.md](pre/resize-letterbox.md) | Letterbox resize |
| `pre.resize.stretch` | [pre/resize-stretch.md](pre/resize-stretch.md) | Stretch resize |
| `pre.resize.fit` | [pre/resize-fit.md](pre/resize-fit.md) | Fit resize |
| `pre.resize.none` | [pre/resize-none.md](pre/resize-none.md) | No resize |
| `pre.resize.affine_person_crop` | [pre/resize-affine-person-crop.md](pre/resize-affine-person-crop.md) | Affine person crop |
| `pre.resize.interpolation` | [pre/interpolation.md](pre/interpolation.md) | Interpolation |
| `pre.normalize` | [pre/normalization.md](pre/normalization.md) | Normalization |

### Detection fields (`object_detector` role)

Fields that apply when `role` includes `object_detector`.

| Section ID | File | Title |
|------------|------|-------|
| `post.det.outputs` | [post/detection-outputs.md](post/detection-outputs.md) | Detection outputs |
| `post.det.decode` | [post/detection-decode.md](post/detection-decode.md) | Detection decode |
| `post.det.selection.none` | [post/selection-none.md](post/selection-none.md) | Selection: none |
| `post.det.selection.top_k` | [post/selection-top-k.md](post/selection-top-k.md) | Selection: top-k |
| `post.det.selection.nms` | [post/selection-nms.md](post/selection-nms.md) | Selection: NMS |

### Pose-estimation fields (`pose_estimator` role)

Fields that apply when `role` includes `pose_estimator`.

| Section ID | File | Title |
|------------|------|-------|
| `post.pose.schema` | [post/pose-schema.md](post/pose-schema.md) | Pose schema |
| `post.pose.canonical_mapping` | [post/canonical-mapping.md](post/canonical-mapping.md) | Canonical mapping |
| `post.pose.decode.simcc` | [post/pose-decode-simcc.md](post/pose-decode-simcc.md) | SimCC decode |
| `post.pose.decode.heatmap` | [post/pose-decode-heatmap.md](post/pose-decode-heatmap.md) | Heatmap decode |
| `post.pose.decode.coordinate` | [post/pose-decode-coordinate.md](post/pose-decode-coordinate.md) | Coordinate decode |
| `post.pose.bottom_up` | [post/pose-bottom-up.md](post/pose-bottom-up.md) | Bottom-up pose |
| `post.overlay` | [post/overlay.md](post/overlay.md) | Overlay |

## Validation rules

A sidecar is valid when all of the following hold. Rules marked **(vNEXT)** apply only when `schema_version >= vNEXT`; legacy sidecars follow [Version-aware compatibility](format/versioning.md#version-aware-compatibility).

- [File composition](format/composition.md#validation-rules)
- [Schema versioning](format/versioning.md#validation-rules)
- [Identity](common/identity.md#validation-rules)
- [Sizes and artifacts](common/sizes-and-artifacts.md#validation-rules)
- [Batching](common/batching.md#validation-rules)
- [Input](common/input.md#validation-rules)
- [Outputs](common/outputs.md#validation-rules)
- [Letterbox resize](pre/resize-letterbox.md#validation-rules)
- [Fit resize](pre/resize-fit.md#validation-rules)
- [Affine person crop](pre/resize-affine-person-crop.md#validation-rules)
- [Normalization](pre/normalization.md#validation-rules)
- [Detection outputs](post/detection-outputs.md#validation-rules)
- [Detection decode](post/detection-decode.md#validation-rules)
- [Selection: none](post/selection-none.md#validation-rules)
- [Selection: top-k](post/selection-top-k.md#validation-rules)
- [Selection: NMS](post/selection-nms.md#validation-rules)
- [Pose schema](post/pose-schema.md#validation-rules)
- [Canonical mapping](post/canonical-mapping.md#validation-rules)
- [SimCC decode](post/pose-decode-simcc.md#validation-rules)
- [Heatmap decode](post/pose-decode-heatmap.md#validation-rules)
- [Coordinate decode](post/pose-decode-coordinate.md#validation-rules)
- [Bottom-up pose](post/pose-bottom-up.md#validation-rules)
- [Overlay](post/overlay.md#validation-rules)
