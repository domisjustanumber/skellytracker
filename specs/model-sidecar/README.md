# Model Sidecar Specification

## Overview

A **sidecar** is a YAML file. It sits beside one or more ONNX model files. It describes the runtime I/O contract that a host must satisfy to load and run the models correctly. The contract has these parts: input tensor, normalization, resize, batching, output semantics and decode.

Sidecars support two model **roles**:

| Role | Purpose |
|------|---------|
| `object_detector` | Object detection, for example YOLO26, RF-DETR and RTMDet. The model outputs boxes, scores and class information. |
| `keypoint_detector` | Keypoint detection, for example RTMW and RTMPose. The model outputs keypoint coordinates. |

A sidecar can declare **both** roles. An example is a one-stage model such as RTMO or YOLO26-pose, which outputs boxes and keypoints in the same pass. In that case, `role` lists both values. `outputs` mixes detection and keypoint tensors, or packs keypoints into the detection rows (see [`packed_keypoints`](post/keypoint/bottom-up.md#packed_keypoints-bottom-up-packed-rows)).

### Core properties

- **One sidecar for each model family.** A single `{model_id}.yaml` file lists every size of the model. Within each size, the file lists every precision variant in `sizes.<size>.onnx.precision_artifacts`. One `batching.batch` gives the batch of every size and every precision ([batch form](common/sizes-and-artifacts.md#batch-forms); [ADR-JAA4](../../decisions/entries/JAA4-one-batch-field.md)).
- **Multiple sizes in each sidecar.** A family ships several sizes in one file, for example `nano`, `small` and `medium`. All sizes share one preprocessing and output contract. They differ only in input size and ONNX artifacts (see [`sizes`](common/sizes-and-artifacts.md#sizes)).
- **Traceable version.** The `schema_version` of a sidecar names the spec version that it follows. The spec version is the skellytracker version, in SemVer, that first releases a spec change. The open target is `2.0.0`, so a sidecar has `schema_version: "2.0.0"`. The [changelog](changelog.md) gives the versions and the open target ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). A host loads only the versions that it implements. The spec has no legacy reading ([ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md)).
- **Single source of truth.** This document is the canonical, human-readable contract. **No software parses it at runtime.** skellytracker has Pydantic `BaseModel` subclasses (the `SidecarModel` hierarchy) that follow this document. The documentation and the validators must stay aligned.
- **Composable.** A sidecar can include shared YAML fragments with `$ref`. `$ref` is the only directive that reuses a file ([ADR-90CE](../../decisions/entries/90CE-minimal-sidecar-contract.md)).

This specification is in separate section files. See the [Section map](#section-map).

Also: [Changelog](changelog.md) and [Reference examples](examples/README.md).

To add a model or to request a change to this specification, follow the [model addition workflow](model-addition-workflow/README.md). The workflow is the same for each contributor. It is not a section of the specification.

## Conventions

- "must" marks a requirement.
- "must not" marks a prohibition.
- "can" marks a permitted option.
- A rule ID `V-<section-id>-<n>` names one checklist rule.
- The section ID is the `id` in the front matter of a section file.

## Section status

The field `status.spec` in the front matter of a section file gives the status of the section: `stable` or `draft`. The front matter is the authority.

1. A `draft` section is normative. A writer can write its fields ([ADR-QMKS](../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)).
2. A content change can change a `draft` section. A spec change has no class ([ADR-C0YD](../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 1).
3. The first body line of a `draft` section, after its title, is the banner "This section is a draft. ...". A `stable` section has no banner.
4. A new section starts as `draft`. A changed `stable` section stays `stable`.
5. A `draft` section becomes `stable` when all of these conditions are true. The Gate column of the [Implementation status](TRACEABILITY.md#implementation-status) table shows the conditions that the files show.
   - A decision entry that is `accepted` or `absorbed into` exists for the section ([ADR-3AM0](../../decisions/entries/3AM0-absorb-at-landing-and-landed-copies.md)).
   - A reference example with `kind: export` uses the section, or the user records "no model" with a reason in `no_model` of [`inventory.yaml`](inventory.yaml).
   - Each algorithm of the section has vectors with verified cases. When vectors cannot hold the input of the algorithm, for example an ONNX file, a named test checks the algorithm.
   - Each `V-` rule of the section has a vector case in the vector file of the section that names it: a validator case (`failed`) or a reference refusal case (`error`). An `error` case and a `failed` case need no `verified_against`.
6. The change to `stable` is a content change. It changes `status.spec`, removes the banner and adds a row to the [summary of changes](changelog.md#summary-of-changes).
7. The release step stops when a section is `draft`. The user makes the section `stable`, or removes its fields from the release.

## Section map

### Format

| Section ID | File | Title |
|------------|------|-------|
| `format.file_layout` | [format/file-layout.md](format/file-layout.md) | File layout |
| `format.composition` | [format/composition.md](format/composition.md) | File composition |
| `format.versioning` | [format/versioning.md](format/versioning.md) | Schema versioning |

### Common fields

These fields apply to every sidecar, regardless of `role`.

| Section ID | File | Title |
|------------|------|-------|
| `common.identity` | [common/identity.md](common/identity.md) | Identity |
| `common.sizes_and_artifacts` | [common/sizes-and-artifacts.md](common/sizes-and-artifacts.md) | Sizes and artifacts |
| `common.batching` | [common/batching.md](common/batching.md) | Batching |
| `common.batch_conversion` | [common/batch-conversion.md](common/batch-conversion.md) | Batch conversion |
| `common.input` | [common/input.md](common/input.md) | Input |
| `common.outputs` | [common/outputs.md](common/outputs.md) | Outputs |
| `common.license` | [common/license.md](common/license.md) | License and training data |

### Pre-processing

| Section ID | File | Title |
|------------|------|-------|
| `pre.resize.letterbox` | [pre/resize-letterbox.md](pre/resize-letterbox.md) | Letterbox resize |
| `pre.resize.stretch` | [pre/resize-stretch.md](pre/resize-stretch.md) | Stretch resize |
| `pre.resize.fit` | [pre/resize-fit.md](pre/resize-fit.md) | Fit resize |
| `pre.resize.none` | [pre/resize-none.md](pre/resize-none.md) | No resize |
| `pre.resize.affine_crop` | [pre/resize-affine-crop.md](pre/resize-affine-crop.md) | Affine crop |
| `pre.resize.interpolation` | [pre/interpolation.md](pre/interpolation.md) | Interpolation |
| `pre.normalize` | [pre/normalization.md](pre/normalization.md) | Normalization |

### Object fields (`object_detector` role)

These fields apply when `role` includes `object_detector`.

| Section ID | File | Title |
|------------|------|-------|
| `post.object.outputs` | [post/object/outputs.md](post/object/outputs.md) | Object outputs |
| `post.object.decode` | [post/object/decode.md](post/object/decode.md) | Object decode |
| `post.object.selection.none` | [post/object/selection-none.md](post/object/selection-none.md) | Selection: none |
| `post.object.selection.top_k` | [post/object/selection-top-k.md](post/object/selection-top-k.md) | Selection: top-k |
| `post.object.selection.nms` | [post/object/selection-nms.md](post/object/selection-nms.md) | Selection: NMS |

### Keypoint fields (`keypoint_detector` role)

These fields apply when `role` includes `keypoint_detector`.

| Section ID | File | Title |
|------------|------|-------|
| `post.keypoint.schema` | [post/keypoint/schema.md](post/keypoint/schema.md) | Keypoint schema |
| `post.keypoint.canonical_mapping` | [post/keypoint/canonical-mapping.md](post/keypoint/canonical-mapping.md) | Canonical mapping |
| `post.keypoint.decode.simcc` | [post/keypoint/decode-simcc.md](post/keypoint/decode-simcc.md) | SimCC decode |
| `post.keypoint.decode.coordinate` | [post/keypoint/decode-coordinate.md](post/keypoint/decode-coordinate.md) | Coordinate decode |
| `post.keypoint.bottom_up` | [post/keypoint/bottom-up.md](post/keypoint/bottom-up.md) | Bottom-up keypoints |
| `post.keypoint.overlay` | [post/keypoint/overlay.md](post/keypoint/overlay.md) | Overlay |

### Post-processing

| Section ID | File | Title |
|------------|------|-------|
| `post.unprojection` | [post/unprojection.md](post/unprojection.md) | Unprojection |

## Validation rules

A sidecar is valid when all of the following rules hold. Each rule applies to every sidecar ([ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md)).

- [File composition](format/composition.md#validation-rules)
- [Schema versioning](format/versioning.md#validation-rules)
- [Identity](common/identity.md#validation-rules)
- [Sizes and artifacts](common/sizes-and-artifacts.md#validation-rules)
- [Batching](common/batching.md#validation-rules)
- [Batch conversion](common/batch-conversion.md#validation-rules)
- [Input](common/input.md#validation-rules)
- [Outputs](common/outputs.md#validation-rules)
- [License and training data](common/license.md#validation-rules)
- [Letterbox resize](pre/resize-letterbox.md#validation-rules)
- [Stretch resize](pre/resize-stretch.md#validation-rules)
- [Fit resize](pre/resize-fit.md#validation-rules)
- [No resize](pre/resize-none.md#validation-rules)
- [Affine crop](pre/resize-affine-crop.md#validation-rules)
- [Interpolation](pre/interpolation.md#validation-rules)
- [Normalization](pre/normalization.md#validation-rules)
- [Object outputs](post/object/outputs.md#validation-rules)
- [Object decode](post/object/decode.md#validation-rules)
- [Selection: none](post/object/selection-none.md#validation-rules)
- [Selection: top-k](post/object/selection-top-k.md#validation-rules)
- [Selection: NMS](post/object/selection-nms.md#validation-rules)
- [Keypoint schema](post/keypoint/schema.md#validation-rules)
- [Canonical mapping](post/keypoint/canonical-mapping.md#validation-rules)
- [SimCC decode](post/keypoint/decode-simcc.md#validation-rules)
- [Coordinate decode](post/keypoint/decode-coordinate.md#validation-rules)
- [Bottom-up keypoints](post/keypoint/bottom-up.md#validation-rules)
- [Overlay](post/keypoint/overlay.md#validation-rules)
