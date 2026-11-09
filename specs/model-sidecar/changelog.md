# Changelog

## Changes in this revision

The evidence for each change, and the findings for each repository, are in
[`sidecar-exporter-coverage.md`](../../notes/sidecar-exporter-coverage.md).

### Scope of this revision

This list names the models that the spec must describe
([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)):

- OpenMMLab-Exporter: RTMDet (person-only family), RTMW and RTMO body7.
- Ultralytics-Exporter: YOLO26 detection and YOLO26 pose.
- Roboflow-Exporter: RF-DETR.

The rules of this list:

- Qualcomm-Exporter is out of scope until that library is complete.
- This list is a process list. It does not change the meaning of a sidecar. A change of this list is
  a non-spec change.
- Two events add a model to this list:
  - The user accepts a change proposal that the model needs. The non-spec PR of that proposal adds
    the model.
  - skellytracker lands the model with the verdict `describes`. The PR of its example adds the model.
- These two edits apply the rule. They need no decision entry. To remove a model from this list,
  write a new decision entry.
- A new batch-conversion profile joins the spec in the same way: the user accepts a change proposal
  for the profile, and each model that needs it joins this list.
- The spec adds only the features that a model in this list needs.
  [Considered and deliberately not added](#considered-and-deliberately-not-added) lists the other
  features. That table is not a ban. The content PR that adds a feature of the table removes its row.
- In this spec, "this revision" and "the current revision" mean the open target: the next
  skellytracker release that includes a spec change. The open target is `2.0.0`. Each spec change
  and each proposal targets the open target
  ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
- In the spec-build stage, each accepted spec change goes into the spec. A proposal must give only
  the text of the current revision. A proposal must not give a second text for a later revision. A
  proposal that the user has not decided keeps the status `proposed`. The user never accepts a
  proposal for a later revision. A proposal that the user rejects becomes `rejected`
  ([Responses](model-addition-workflow/hand-over.md#responses)).
- The spec has no RF-DETR reference example. The example returns when Roboflow-Exporter writes
  sidecars with `schema_version: "2.0.0"`
  ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)). The rules
  that RF-DETR motivated stay in the spec:
  - the `stretch` resize;
  - the `boxes`, `scores` and `class_logits` output semantics, with `class_axis`;
  - `selection: top_k`, with `class_id_map`;
  - `input.resize.compute_dtype: float32`.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.
- This list is not the verdict `out of scope` of an intake row.

### Summary of changes

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| 1 | Resize | New `input.resize.method: stretch` (independent x/y resize, no pad). | RF-DETR | [`input.resize`](pre/resize-stretch.md) |
| 2 | Resize | New `input.resize.method: fit` (full-frame affine fit with centered fractional padding and a constant border value). | RTMO Body7 | [`input.resize`](pre/resize-fit.md) |
| 3 | Resize | Letterbox gains **required** `pad_position` (`top_left` \| `center`) and `rounding` (`half_even` \| `half_up`), with normative centre offsets and an exact-inverse unprojection. `pad_value` accepts a scalar or a per-channel array. | YOLO26 (centre, half-even), RTMDet (top-left, half-up) | [`input.resize`](pre/resize-letterbox.md) |
| 4 | Resize | Normative unprojection for each method. All resizes are defined as **non-antialiased**. | all | [Unprojection](post/unprojection.md) |
| 5 | Resize | `affine_person_crop` defines `maintain_aspect_ratio` and adds `crop_policy.pad_value`. | RTMW | [`input.resize`](pre/resize-affine-person-crop.md) |
| 6 | Input | New `input.color_format` (`rgb` \| `bgr`), required when normalization is channel-agnostic (`none`/`unit_float`). `none` now means "pixels unchanged in `input.dtype`" (not only uint8). The `imagenet_*` channel order is spelled out. `imagenet_bgr` applies BGR-ordered statistics (B mean `103.53`). | YOLO26, RF-DETR, RTMDet | [`input`](common/input.md), [Normalization modes](pre/normalization.md) |
| 7 | Outputs | New detection semantics `boxes`, `scores` and `class_logits`, with `class_axis`. Output names must be unique. | RF-DETR (`dets` + `labels` logits), RTMDet (`boxes` + `scores`) | [Detection output semantics](post/detection-outputs.md#detection-output-semantics) |
| 8 | Decode | Detection `decode` is rebuilt around a required `selection` (`none` \| `top_k` \| `nms`), output bindings (`boxes_output`, `scores_output`, `class_logits_output`), `box_scale`, `score_activation`, `class_id_map`, `clamp_boxes` and an `nms` block (`iou_threshold`, `score_threshold`, `class_agnostic`, `post_nms_top_k`). Stage order is normative, and score thresholds are strict (`>`). | RF-DETR (query×class top-k), RTMDet (host NMS), YOLO26 (graph-final rows) | [`decode`](post/detection-decode.md#decode-detection), [Selection behaviour](post/detection-decode.md#selection-behaviour) |
| 9 | Decode | `max_detections` no longer defaults to `300`. It now only declares the graph's fixed final row count, and is valid only with `selection: none`. `selection` replaces `requires_nms`. `is_person_only` replaces `may_include_non_person_classes` (the old field inverted). The two old keys are removed. | all detectors; [ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md) | [`decode`](post/detection-decode.md#decode-detection) |
| 10 | Pose | New `packed_keypoints` on a `detections` output, for one-stage models that pack keypoints into the detection row. | YOLO26 pose (`[N,300,57]`) | [`packed_keypoints`](post/pose-bottom-up.md#packed_keypoints-bottom-up-packed-rows) |
| 11 | Pose | Bottom-up instance count is no longer overloaded onto `max_detections`. Pose rows are row-aligned with detection rows and gathered by the surviving detection indices. | YOLO26 pose, RTMO | [Bottom-up decode](post/pose-bottom-up.md#bottom-up-decode) |
| 12 | Sizes | **Family invariant:** a size entry may set only `input.shape`, `input.resize.target_size` and `onnx`. Sizes that differ in channel order, normalization or post-processing must be separate families. This resolves the earlier contradiction between "a size is a partial document deep-merged over the top level" and "sizes share the output contract". | RTMDet person-only vs 80-class families (different NMS contracts and class counts) | [`sizes`](common/sizes-and-artifacts.md#sizes) |
| 14 | Examples | Reference examples rewritten for this revision. RTMDet person, RTMW and RTMO body7 come from real exports of OpenMMLab-Exporter; RTMDet uses its person-only family. YOLO26 detection and YOLO26 pose are written from Ultralytics-Exporter's code and will be replaced when it emits sidecars of this spec. There is no RF-DETR example until Roboflow-Exporter is overhauled. All batch keys are quoted. | all | [Reference examples](examples/README.md) |
| 15 | Identity | New top-level `source` mapping with `name` (the package name of the library that wrote the sidecar) and `version` (the version of that library). It is required. | sidecar catalogs: `model_id` is not unique across sources (decision [0016](../../decisions/entries/0016-sidecar-catalogs.md)) | [`source`](common/identity.md#fields) |
| 16 | Composition | A `$ref` mapping holds exactly `$ref` and `sha256`. `base` has the same `{$ref, sha256}` form. `sha256` is the SHA-256 of the exact bytes of the target file. The resolver checks it before it parses the file. Sidecars and fragments are UTF-8 without a BOM, with LF line endings. | sidecar catalogs: each root holds its own fragments (decision [0016](../../decisions/entries/0016-sidecar-catalogs.md)) | [Reference hashes](format/composition.md#reference-hashes) |
| 17 | Artifacts | New artifact field `sha256` with `filename`: the SHA-256 of the file that `filename` names. It is required on every artifact. `url_sha256` stays with `url`. A 64-zero placeholder is valid only in the spec's examples. | ONNX files next to a sidecar have no hash (decision [0016](../../decisions/entries/0016-sidecar-catalogs.md)) | [`sizes.<size>.onnx.batch_artifacts`](common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) |
| 18 | Layout | `{cache_dir}` has the new name `{sidecar_root}`. A sidecar root is the package root, a local folder that a user adds or a Hugging Face repo snapshot. Each root follows the storage layout. A discovery rule tells a sidecar from the other YAML files. | sidecar catalogs: "cache dir" names two folders, and nothing defines which YAML files are sidecars (decision [0016](../../decisions/entries/0016-sidecar-catalogs.md)) | [Sidecar roots](format/file-layout.md#sidecar-roots), [Discovery](format/file-layout.md#discovery) |
| 19 | Examples | Every reference example has `source` and all hashes. The `$ref` hashes are real. The ONNX artifacts have the placeholder. | all (decision [0016](../../decisions/entries/0016-sidecar-catalogs.md)) | [Reference examples](examples/README.md) |
| 20 | Batching | New draft `batching.batch_conversion` (`profile_id`, `source_batch_size`) and profile `static-batch-v1`. | YOLO26 (static-batch exports) | [Batch conversion](common/batch-conversion.md) |
| 21 | Artifacts | The precision keys are `fp32` and `fp16`. The key `int8` is removed. | int8 AP loss (YOLO26, RF-DETR) | [`batch_artifacts`](common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts) |
| 23 | Batching | The `static-batch-v1` condition on external data applies to each tensor, not only to the initializers. The profile names the tensors that its steps do not change. Limits names the 1-D shape constants `[S, ...]` in which the first value is not the batch. | `model_batch_convert` checks each tensor; `S = 3` ([ADR-JC4T](../../decisions/entries/JC4T-parity-gates-and-batch-conversion-check.md)) | [`static-batch-v1`](common/batch-conversion.md#static-batch-v1) |
| 24 | Status | A `draft` section is normative. It has a banner. A new section starts as `draft`. It becomes `stable` in a content change when it has an accepted entry, a `kind: export` example or a "no model" reason, verified vectors and a case for each `V-` rule. The release step stops on a `draft` section. | `common.batch_conversion` was `draft` with no rule for the status ([ADR-QMKS](../../decisions/entries/QMKS-draft-sections-and-coverage-columns.md)) | [Section status](README.md#section-status) |
| 25 | Batching | A sidecar uses one batch form for every size and every precision: only the key `"3"` with `batching.batch_conversion`, only the key `"1"`, or only the key `dynamic`. Any other key set is invalid. | user decision 2026-10-29: other batch sizes are not practical to run in production ([ADR-JB5J](../../decisions/entries/JB5J-one-batch-form-for-each-sidecar.md)) | [Batch forms](common/sizes-and-artifacts.md#batch-forms), [Batch conversion](common/batch-conversion.md#validation-rules) |
| 26 | Versioning | The spec has no legacy layer. Each sidecar has one reading: the current text. A host loads only the versions that it implements. This change removes the version marks of the rules, the "Legacy behaviour" headings, the version-aware compatibility rules, the clarification rule and the list of every-version changes. It also removes the one-key `$ref` form, the string `base` form, the default `source` and the load from the package root only. `input.normalization` is required and has no default. It removes the keys `requires_nms`, `preserve_aspect_ratio` and `may_include_non_person_classes`. A key that the spec does not define is invalid. Until revision `1.0`, a change that removes a rule numbers the other rules of its section again from 1. | user decision 2026-10-30: no backward compatibility; nothing has shipped ([ADR-0QKK](../../decisions/entries/0QKK-no-legacy-layer.md)) | [Schema versioning](format/versioning.md#semantics), [File composition](format/composition.md#reference-hashes), [unknown keys](format/composition.md#validation-rules), [Identity](common/identity.md#fields), [Normalization](pre/normalization.md) |
| 27 | Batching | Each sidecar has one `batching.batch`: `3`, `1` or `dynamic`. It applies to each size and each precision. `batching.batch_conversion` has only `profile_id`, and it is present if and only if `batch` is `3`. This change removes `source_batch_size`, `batching.batch_axis`, the derived `native_batch_sizes` and `sizes.<size>.onnx.batch_artifacts`. Dim 0 is the batch axis. Each size has `onnx.precision_artifacts` and `onnx.output_shapes`. `output_shapes` has one entry for each output of `outputs`, in the same order. Each fixed dim of `outputs[].shape` is equal in the entry or `-1`. An axis that the graph leaves symbolic stays `-1`. Dim 0 of each entry equals `batch`, or is `-1` for `dynamic`. A `dynamic` file name has no batch segment. | user decision 2026-11-02: `source_batch_size` and `batch_axis` had one valid value each; without `output_shapes`, a host cannot get the RTMDet row count `A` ([ADR-JAA4](../../decisions/entries/JAA4-one-batch-field.md)) | [`sizes.<size>.onnx`](common/sizes-and-artifacts.md#sizessizeonnx), [Batching](common/batching.md#fields), [Batch conversion](common/batch-conversion.md#validation-rules) |
| 28 | Contract | `sizes.<size>.onnx.precision_artifacts.<precision>.input_dtype`, `outputs[].rank`, `input.resize.supports_dynamic_size`, `input.layout` and the `base` directive go. The input is NCHW. `$ref` is the only directive that reuses a file. A size entry holds `input.shape`, `input.resize.target_size` and `onnx`. The host does not merge a size entry over the top level. The section of each resize method holds the presence rules of its fields. The required `pose.geometry` (`2d` \| `3d`) replaces `pose.decode.is_3d`. Packed keypoints use the `decode.box_scale` of the detection decode, and `pose.decode.coordinate_scale` must not be present with `packed_keypoints`. One `imagenet` mode applies the ImageNet statistics in the channel order of `input.color_format`. It replaces `imagenet_bgr` and `imagenet_rgb`. `input.color_format` is required for each normalization mode, and `custom` uses it (`custom.color_format` goes). | user decision 2026-11-02: these fields gave no information, or two fields stated one fact ([ADR-90CE](../../decisions/entries/90CE-minimal-sidecar-contract.md)) | [`sizes`](common/sizes-and-artifacts.md#sizes), [`input`](common/input.md), [File composition](format/composition.md), [Pose schema](post/pose-schema.md), [Normalization](pre/normalization.md#behaviour) |
| 29 | Decode | Selection behaviour states once the steps that the three selection modes share: the class mapping, the box conversion, the unprojection, the clamp, the size filter and the confidence threshold. `clamp_boxes` applies in each mode. The clamp sets each `x` to `[0, W]` and each `y` to `[0, H]` of the source image. New optional `decode.min_box_size` in source-image pixels: the host keeps a box only when its width and its height are both more than the value. When it is absent, the host drops no box for its size. The host assigns `person_class_id` only through `is_person_only`. A sidecar with no `class_field` and no `class_logits_output` must set `decode.is_person_only: true`. | user decision 2026-11-02: the three mode files did not agree, the clamp had no bounds, and mmdet drops small boxes (`min_bbox_size`) ([ADR-17KN](../../decisions/entries/17KN-one-selection-pipeline.md)) | [Selection behaviour](post/detection-decode.md#selection-behaviour), [`decode`](post/detection-decode.md#decode-detection), [Validation rules](post/detection-decode.md#validation-rules) |
| 30 | Versioning | Each sidecar has `schema_version: "1"`, a quoted string. The spec owns the version. A skellytracker release does not set it. The pattern `vYYYY.0M.BUILD` goes. A host must reject a `schema_version` that it does not implement, with an error that names the version. The capability check lists such a sidecar as unavailable. The version comparison, the too-new rule, the pre-release rule and the exporter obligation go. The spec revision is `1.N`, the heading of an entry in [Revisions](#revisions). Each content commit increments `N` and adds a row to this table. From `1.0` on, a change that deletes a `V-` rule leaves its number unused. Do not publish a sidecar to a shared or remote sidecar root until a skellytracker release loads `schema_version: "1"`. | user decision 2026-11-02: the spec owns the version, and the placeholder was not a version ([ADR-SS2E](../../decisions/entries/SS2E-spec-owned-version.md)) | [Schema versioning](format/versioning.md), [Revisions](#revisions) |
| 31 | Versioning | A spec version is the skellytracker version, in SemVer, that first releases a spec change. A release with no spec change makes no spec version. Each spec change and each proposal targets the next skellytracker release, the open target, with no version bump. The open target is `2.0.0`. Each sidecar has `schema_version: "2.0.0"`, a quoted string. `V-format.versioning-1`: `schema_version` must be a version heading of [Revisions](#revisions) or a recorded pre-release of the open target. A value can have a SemVer pre-release tag, for example `"2.0.0-rc.1"`. A pre-release host implements its own value and the open target. No other host implements a pre-release value. Each release lists the versions that it implements. A sidecar goes to a shared or remote sidecar root only after a final release loads its `schema_version`. A `V-` rule ID has no version part and never shifts. The revision `1.N` goes: each version heading has a `Released` line, and each content commit appends a `Row` line under the open target. | user decision 2026-11-03: one version number tells a user which skellytracker release loads a sidecar ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)) | [Schema versioning](format/versioning.md), [Revisions](#revisions) |
| 32 | Resize | A scalar `pad_value` or `crop_policy.pad_value` `s` means `[s, s, s]`. It fills each channel. The `fit` and `affine_person_crop` pseudocode expands a scalar to one value for each channel before `warpAffine`. | user decision 2026-11-04: OpenCV fills only channel 0 for a scalar `borderValue`, and RTMO body7 writes the scalar `114` ([ADR-BJF9](../../decisions/entries/BJF9-scalar-pad-value-fills-every-channel.md)) | [`input.resize`](common/input.md#inputresize), [`fit`](pre/resize-fit.md), [`affine_person_crop`](pre/resize-affine-person-crop.md) |
| 33 | Resize | Each resize method that resizes the image has one pixel-centre convention. `letterbox` and `stretch` use the image plane of `cv2.resize`: pixel `i` covers `[i, i + 1)`. `cv2.resize` samples at half-pixel centres for `linear`, `cubic` and `area`. `nearest` is `cv2.INTER_NEAREST`: the destination pixel `x` takes the source pixel `floor(x * src_n / dst_n)`. `fit` and `affine_person_crop` use the integer pixel centres of `cv2.warpAffine`: the destination pixel `(x, y)` samples the source at `M^-1 · (x, y, 1)`. Each Inverse and the unprojection use the convention of the method. No step adds or removes a `0.5` offset. The host does not convert a box between the two conventions. The formulas do not change. | mmpose `TopdownAffine` and `BottomupResize` warp with `cv2.warpAffine` and invert with `M^-1`; ultralytics `LetterBox` resizes with `cv2.resize` and inverts with `(x - pad) / gain`; user decision 2026-11-04 ([ADR-G79P](decisions/entries/G79P-pixel-centres-per-resize-method.md)) | [Pixel centres](pre/interpolation.md#pixel-centres), [`letterbox`](pre/resize-letterbox.md), [`stretch`](pre/resize-stretch.md), [`fit`](pre/resize-fit.md), [`affine_person_crop`](pre/resize-affine-person-crop.md), [Unprojection](post/unprojection.md#behaviour) |
| 34 | Resize | New optional `input.resize.compute_dtype`: `uint8` or `float32`. The default is `uint8`. It applies to `letterbox`, `stretch`, `fit` and `affine_person_crop`. With `uint8`, the host resizes and pads the 8-bit image, and the result is 8-bit. With `float32`, the host casts the image to float32 first, and it does not round or clamp the result. The normalization and the cast to `input.dtype` come after the resize. `V-pre.resize.interpolation-1`: the value must be `uint8` or `float32`. `V-pre.resize.none-1`: a `none` resize must not declare `compute_dtype`. | user decision 2026-11-04: RF-DETR resizes the float image, and no field stated the dtype of the resize ([ADR-PHJ3](decisions/entries/PHJ3-resize-compute-dtype.md)) | [Compute dtype](pre/interpolation.md#compute-dtype), [No resize](pre/resize-none.md#validation-rules) |
| 35 | Pose | The heatmap decode goes. `pose.decode.method` is `simcc` or `coordinate`. `outputs[].semantic` has no value `heatmap`. The section `post.pose.decode.heatmap` and its rule `V-post.pose.decode.heatmap-1` go. The rule number stays unused. | user decision 2026-11-04: no sidecar uses it. A host could not implement the section, because it had no tie rule, no refinement, no scale to the model input, no score definition and no vectors ([ADR-9MJ6](../../decisions/entries/9MJ6-remove-the-heatmap-decode.md)) | [`pose.decode`](post/pose-schema.md#posedecode), [Outputs](common/outputs.md#validation-rules) |
| 36 | Pose | The SimCC decode is 2D only. `outputs[].semantic` has no value `simcc_z`, and `pose.decode` has no field `depth_range`. `V-post.pose.schema-7`: a `simcc` decoder must have `pose.geometry: 2d`. The rule `V-post.pose.decode.simcc-1` goes. Its number stays unused. `pose.geometry: 3d` stays for the `coordinate` decode. | user decision 2026-11-06: no model in scope has a `simcc_z` output, and a host could not implement the 3D text, because it had no score rule for three peaks and no exact depth formula ([ADR-9HBB](../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)) | [SimCC decode](post/pose-decode-simcc.md#behaviour), [Pose schema](post/pose-schema.md#validation-rules), [Outputs](common/outputs.md#validation-rules) |
| 37 | Batching | The verification batches of the parity check of `static-batch-v1` are 1, 2, 3 and 6. Batch 6 replaces batch 4 as the conversion to a larger batch. Input B holds 6 different preprocessed images of each size. `S`, the profile and the tolerance do not change. | user decision 2026-11-06: b1, b2, b3 and b6 are more representative of end-user batch sizes, so the verification files are also benchmark values ([ADR-50BW](decisions/entries/50BW-verification-batches.md)) | [Batch conversion](common/batch-conversion.md#authoring-guidance) |
| 38 | Resize | `affine_person_crop` gives the steps of its warp matrix `M` in float32: the box rounds to float32; the centre, the crop size and the aspect fix with `a = f32(T_w / T_h)` are float32; `M` comes from three float32 point pairs that use `c` and `w` only. The branch `h = w / a` and the strict `>` set only the crop height (mmpose `input_scale`), not `M`. The Inverse stays the inverse of `M`. | user decision 2026-11-09: RTMW (mmpose `TopdownAffine`) ([ADR-3S5G](decisions/entries/3S5G-affine-crop-matrix.md)) | [Affine person crop](pre/resize-affine-person-crop.md#behaviour) |
| 39 | Pose | The SimCC decode gives its steps: the argmax of each axis on the raw values (a tie takes the lowest bin), the score `min(peak_x, peak_y)` with no softmax, the bin `-1` on each axis for a score `<= 0`, the rule for a NaN raw value (the bin of the first NaN, and a comparison with a NaN is false), and the bin scale with no offset (2D). | user decision 2026-11-09: RTMW (mmpose `get_simcc_maximum`) ([ADR-03PH](decisions/entries/03PH-simcc-score-rule.md)) | [SimCC decode](post/pose-decode-simcc.md#behaviour) |
| 40 | Input | Each normalization mode casts its result to the `input.dtype` entry of the selected precision. `V-pre.normalize-3`: a `uint8` input needs the resolved normalization `none` and `input.resize.compute_dtype` absent or `uint8`. `V-common.input-2`: the input dtypes are `float32`, `float16` and `uint8`. `int8` goes. The output dtypes keep `int8`. | user decision 2026-11-06: the mode table stated the cast only for `none`, the cast of a fractional value to `uint8` was not defined, and no mode gives a defined `int8` input ([ADR-XH1J](decisions/entries/XH1J-normalize-input-dtype.md)) | [Normalization](pre/normalization.md#behaviour), [Input](common/input.md#validation-rules) |
| 41 | Input | An absent key of a `custom` normalization has the value `scale: 1`, `mean: [0, 0, 0]` or `std: [1, 1, 1]`. The `none` row names YOLOX and RTMO as models whose upstream does not normalize. | user decision 2026-11-09: `V-pre.normalize-1` allowed an absent `mean` or `std` with no value, and the `none` row said that YOLOX normalizes internally ([ADR-1V57](decisions/entries/1V57-normalize-custom-defaults.md)) | [Normalization](pre/normalization.md#behaviour) |
| 42 | Identity | The `model_id` of a keypoint detector is `{family}-{group}` or `{family}-{group}-{variant}`. `{group}` is a body region or a keypoint set with its keypoint count (`wholebody133`). The folder is `keypoint_detectors/{family}/{group}/`. New rules `V-common.identity-7` and `V-common.identity-8`. | RTMW (`rtmw-wholebody133`), RTMO body7 (`rtmo-coco17-body7`); user decision 2026-11-06 ([ADR-52NQ](decisions/entries/52NQ-model-id-suffix.md), [ADR-KZ9J](decisions/entries/KZ9J-model-id-suffix-rtmo-removed.md)) | [Identity](common/identity.md#keypoint-detector-id) |

### Considered and deliberately not added

A content change can add each of these later when a model needs it.

| Field / feature | Reason |
|-----------------|--------|
| `resize.antialias`, `resize.size_divisor` | No in-scope model antialiases or has dynamic spatial dims. Resizes are normatively non-antialiased. |
| `crop_policy.border_mode`, rotated crops | Only constant borders and zero rotation are used. |
| `score_activation: softmax` | No model uses it, and how it behaves over gap/background slots is unresolved. |
| `class_id_map_before_selection` | No model maps classes before top-k. "Map after selection" is normative. |
| `class_logits` with `selection: nms` (each (row, class) pair above the score threshold becomes a candidate, followed by per-class NMS) | No in-scope family needs it after the COCO-80 RTMDet family was dropped. On NMS-free RTMDet-tiny it reproduced PyTorch AP (0.4114 vs 0.4112), while best-class-per-row `scores` + `class_ids` lost 0.0051 AP / 0.031 AR. Add it in a content change if a multi-class NMS-free family appears. |
| `nms.pre_nms_top_k` | A flat candidate list cannot express mmdet's per-level `nms_pre` cap without a `level_strides` field. It had no measured AP effect on person-medium (0.6255 with or without it) or RTMDet-tiny (0.4114 vs 0.4113); it only reduces host NMS time at near-zero score thresholds. |
| `graph_candidate_limit` | Informational only; the host can't act on it. NMS-free exports have no graph-side candidate cap to describe; detection outputs are normatively the complete candidate set. |
| `pose.decode.instance_count` | The count is derivable from the detection row axis (change 11). |
| Soft-NMS / per-class IoU, masks, multi-input models, quantized outputs | Out of scope. No in-scope model needs them. |
| `pose.decode.method: heatmap` and `semantic: heatmap` | No sidecar uses them (change 35). A heatmap model adds them again with a full contract: the tie rule, the refinement, the scale to the model input, the score and vectors. |
| 3D SimCC decode: `semantic: simcc_z` and `pose.decode.depth_range` | No model in scope has a `simcc_z` output (change 36). A 3D SimCC model adds a new section with its own contract: the score rule for three peaks, the exact map from a depth bin to `depth_range`, vectors and a reference module. That change also removes the `pose.geometry: 2d` condition of `V-post.pose.schema-7`. |

### Compatibility impact

- Each sidecar must declare `decode.selection`, `input.normalization`, letterbox `pad_position`/`rounding`, `fit` `pad_value`, `input.color_format` and, for a pose sidecar, `pose.geometry`. A size entry holds only `input.shape`, `input.resize.target_size` and `onnx`.
- Each sidecar must also declare `source`. It must declare `sha256` on each `$ref` and each artifact. The sidecar and each file in its tree must be UTF-8 without a BOM, with LF line endings.

## `schema_version` history

The valid `schema_version` values are in [Schema versioning](format/versioning.md)
(`V-format.versioning-1`). The value is the skellytracker version, in SemVer, that first releases
a spec change ([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

| `schema_version` | From version |
|------------------|--------------|
| `"2.0.0"` | `2.0.0` |

## Revisions

A spec version is the skellytracker version, in SemVer, that first releases a spec change. A
release with no spec change makes no spec version. Each heading below is one spec version. The
open target is the next skellytracker release that includes a spec change. Each spec change and
each proposal targets the open target until its release
([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).

Each version heading has these lines:

- `- Released: no.` or `- Released: yes.`: the first line. The open target has `no`.
- ``- Row N: `<fingerprint>`.``: each content commit appends one such line under the open target,
  with no version bump. `N` is the highest row number of the
  [summary of changes](#summary-of-changes). The fingerprint is the SHA-256 of the headings and the
  `V-` rule lines of the section files. `tools/tests/test_changelog_revision.py` defines it. When
  the value is not current, that test fails and gives the new value. The test sees only these
  lines. A content commit that changes other normative text or `status.spec` must still add a
  summary row and a `Row` line. Review checks it. A rewording of normative text is also a content
  commit for this rule.
- `- Pre-release X.Y.Z-<tag>: row N.`: the session of a skellytracker pre-release appends this
  line under its target. `N` is the last row that the pre-release holds. A pre-release value names
  the open target at that pre-release.

The rules of the versions
([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)):

- Do not change an earlier line.
- Only the last heading can have `- Released: no.`.
- The release sets `- Released: yes.`. A released version does not change.
- After a release, the next change adds the heading of the version that the user bumps
  skellytracker to on `development`.
- When a release ships under another number, the release PR renames the unreleased heading and
  changes the examples. The pre-release values of the old number become invalid.
- A change that deletes a `V-` rule leaves its number unused. No commit renumbers a rule.

### 2.0.0

- Released: no.
- Row 30: `9e0a04b72d3df453a263f3ac4bdf418b1412e1757722fe648a57bdf772e6b0ac`.
- Row 31: `4a5c08c2af251af63318fd8b8647a2f6e572e61fc38ebcf20840bd24f4a39a5a`.
- Row 32: `4a5c08c2af251af63318fd8b8647a2f6e572e61fc38ebcf20840bd24f4a39a5a`.
- Row 33: `bfa5d2ae55d4b0a709f659d4bd23ca20d273596d2161a8c88ce7446f56f7d808`.
- Row 34: `990009b0154349819ea9b863c5437e1f13f452f7e9fcfab7cd759f784304aed9`.
- Row 35: `7a9c42a3f0d213b2f4ca71601294f485e403b6322503371fe5fad40c8ee3a5bf`.
- Row 36: `3dfdaea4409b04e537993deed4b2ec0d127cc68acbc086c9a4a6388dd637235d`.
- Row 37: `3dfdaea4409b04e537993deed4b2ec0d127cc68acbc086c9a4a6388dd637235d`.
- Row 38: `3dfdaea4409b04e537993deed4b2ec0d127cc68acbc086c9a4a6388dd637235d`.
- Row 39: `3dfdaea4409b04e537993deed4b2ec0d127cc68acbc086c9a4a6388dd637235d`.
- Row 40: `85a85089fa3ff1a21579b41d3361e724062abd06ccbea7de8ad913838f79d01f`.
- Row 41: `85a85089fa3ff1a21579b41d3361e724062abd06ccbea7de8ad913838f79d01f`.
- Row 42: `2122b815a8c7100aac5a246ec0563df5714de6684baebdf92a4aab09f19891cc`.

Version `2.0.0` is the first version. It replaces the revision `1.0` and the `schema_version`
history before it. No release shipped a sidecar of that history
([ADR-6GE2](../../decisions/entries/6GE2-spec-version-follows-skellytracker.md)).
