# Model intake template

This template is phase 1 of the new-model workflow. Phase 1 answers one question: can the current
sidecar spec describe this model exactly? The full workflow is the model addition workflow
(`specs/model-sidecar/model-addition-workflow/README.md` of the skellytracker repo). It is the same
for an exporter and for a human contributor. Where this template says "the exporter", a contributor
that is not an exporter reads "you". The workflow
README gives the stages and the phases. Phase 2 is the change proposal template (`specs/model-sidecar/templates/change-proposal.md`). You
need phase 2 only when phase 1 finds a `near-miss` or a `gap`.

This template has no relative links to other files, so its references stay correct after you copy it.
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. It names each workflow rule by its
heading and the workflow file that holds it, for example "Blocking rows" in
`specs/model-sidecar/model-addition-workflow/phase-1-intake.md`. Read the rule there
(skellytracker ADR-ESP4). Read the skellytracker files in the skellytracker checkout (read-only)
`../freemocap/skellytracker`.

## How to use this template

1. Copy this file to `intake.md` of a `model` bundle. Write one intake for each family. Its bundle ID
   is `model-<model>@<contributor>`, and `<model>` is the `model_id` of the family. The hand-over
   rules give the layout, the manifest and the `pack` command
   (`specs/model-sidecar/model-addition-workflow/hand-over.md`).
2. Change the title to `# Model intake: <model>`.
3. Fill in every slot. Do not delete a pre-filled row. Do not leave a cell empty. If a value does not
   apply or is not known, write `not used`, `missing`, `unknown`, `to run`, `skipped` or `none`, with
   the reason.
4. Read the spec. Its only entry point is `specs/model-sidecar/README.md` (skellytracker ADR-CN15).
   Its section map lists each section ID and its section file. The spec is normative.
5. Do not approximate a property. If the spec does not describe a property exactly, the verdict is
   `near-miss` or `gap`.
6. Group the `near-miss` and `gap` rows by the part of the spec that they change. Write one change
   proposal for each new or changed part. Then do the reference-implementation step. Then write the
   final verdict and stop. The skill `author-sidecar` gives this order.
7. Do not change a file in skellytracker. The only exception: `pack` writes the new version folder of
   your bundle in `intakes/`.

**Section IDs.** "Section IDs" in `specs/model-sidecar/model-addition-workflow/reading-the-spec.md`
tells what a section ID is. Write the section ID in the section column. Each pre-filled row names the
section ID that usually applies. `pre.resize.<method>` is the section of the resize method, for
example `pre.resize.letterbox`. `post.det.selection.<selection>` and `post.pose.decode.<method>` have
the same form. A row with a placeholder lists the values that the placeholder can take. If a
different section describes the property, change it.

Before you fill in a row, read the "Authoring guidance" heading of each section that the row names.
That guidance gives the mapping from upstream config keys to sidecar fields, and what to check. The
section map in `specs/model-sidecar/README.md` gives the file of each section ID.

**The steps of phase 1.** Follow the steps of
`specs/model-sidecar/model-addition-workflow/phase-1-intake.md`. This template uses its step numbers.
"Blocking rows" in the same file tells which row is blocking.

## Inputs before you start

Get these inputs before you fill in the property table.

| Input | Path, URL or command | Status (`found` or `missing`) |
|---|---|---|
| The ONNX files: every size and precision, at the verification batches 1, 2, 3 and 4. The `dynamic` export, if you plan to publish it. "Publishing" in `specs/model-sidecar/model-addition-workflow/validation-and-publishing.md` gives the exceptions | | |
| Input B of the batch-conversion check: `batch/inputs/<size>.npy` for each size, with 4 different preprocessed images. "Publishing" in `specs/model-sidecar/model-addition-workflow/validation-and-publishing.md` tells when the check does not run | | |
| The upstream inference config (the test pipeline, not the training pipeline) | | |
| The upstream preprocessing code | | |
| The upstream postprocessing code | | |
| One reference output of the upstream library on a known image | | |

If an input is missing, do not stop. Write `missing` in its row. Use the best secondary source for the
rows that need the input, and give each of these rows the verdict `unverified`. A `near-miss` row or a
`gap` row can rest on a secondary source ("Rules" in
`specs/model-sidecar/model-addition-workflow/rules.md`). When you stop, tell the user which inputs are
missing.

## Header

| Field | Value |
|---|---|
| Model (`model_id`) | |
| Sizes | |
| Exporter repo | |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | |
| Upstream library and version | |
| Upstream config (file path, and upstream commit or release) | |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | |
| Spec version that you read: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | |
| Date | |

**ONNX files.** Write one row for each file. Fill in the SHA-256 now, for example with
`sha256sum <file>`. It identifies the file that you read. It is not the artifact field `sha256` of
the sidecar (`common.sizes_and_artifacts`, heading "Authoring guidance").

| File | Size | Batch (`3`, `1`, `dynamic`, or a verification batch) | Precision | `published` or `verification-only` | SHA-256 |
|---|---|---|---|---|---|
| | | | | | |

## Verdicts

The verdicts are `exact`, `near-miss`, `gap`, `unverified` and `out of scope`. "Verdicts" in
`specs/model-sidecar/model-addition-workflow/phase-1-intake.md` gives their meaning and the test
between `near-miss` and `gap`. Examples of that test:

- No section and no field hold the property, so the verdict is `gap`: a rotated crop, a border mode,
  a model that gives a crop region.
- A field holds the property, but none of its values describes the upstream, so the verdict is
  `near-miss`: the upstream code rounds the letterbox size with `floor`, and the letterbox `rounding`
  has only `half_even` and `half_up` (section `pre.resize.letterbox`,
  `specs/model-sidecar/pre/resize-letterbox.md`).

**Evidence.** Fill in the evidence column as "Rules" and "Sources" in
`specs/model-sidecar/model-addition-workflow/rules.md` say. They give the primary and the secondary
sources, and the two exceptions to `unverified`. For a `near-miss` or a `gap` row on a secondary
source, name the missing primary evidence in the last column.

Do not copy a value from a spec reference example (`specs/model-sidecar/examples/README.md`). After you fill
in every row, compare your values with the example of the same family (see
[The sidecar](#the-sidecar)).

**Values that the exporter chooses.** Some rows have no upstream source, because the exporter chooses
the value. These rows are F1, F5 and F6, the size name in F3, the YAML rows Y1 to Y7 and the path
rows L1 and L2. "Rules" in `specs/model-sidecar/model-addition-workflow/rules.md` gives their
verdict, their evidence and the slot words for these rows. The sidecar value is what the spec
requires. Write an exporter defect in the last column.

For each row that is not `exact`, write what differs or what is missing in the last column. For each
`near-miss` row and each `gap` row, link its proposal in
[Proposals and reference files](#proposals-and-reference-files).

**Near-misses seen so far.** Read "Near-misses seen so far" in
`specs/model-sidecar/model-addition-workflow/mapping-hints.md`.

## Property table

Rules for the rows:

- Write one row for each property. Add rows where the model has more steps or more outputs.
- In the evidence column, give the upstream file and line, or the config key. For a graph row, give
  the command or script that read the graph, and the node or tensor name.
- A row that does not apply to this model still needs evidence. Write `not used` as the sidecar value.
  The verdict is `exact` when the spec also does not use the field for this model. Example: a model
  with only the `pose_estimator` role has no detection `decode`.
- A step inside the graph is also a row. Its sidecar value is the host setting that does not do the
  step again. Example: the graph normalizes the input, so the host uses `normalization: none`.
- The verdicts are `exact`, `near-miss`, `gap`, `unverified` and `out of scope` (see
  [Verdicts](#verdicts)).

### Graph

Source: the ONNX graph of each file.

- Look at the nodes near the input. Sub, Div or Mul nodes there are normalization inside the graph.
- Look at the nodes near the outputs. NonMaxSuppression or TopK nodes there are selection inside the
  graph.
- Read the I/O dtype from each file. Do not assume it from the precision name. An fp16 file can keep
  float32 inputs and outputs.
- Read the static or dynamic dims from the graph. A config name or a file name (for example
  "dynamic") is not evidence of the dims.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| G1 | Input name | | `common.input` | | | |
| G2 | Input dtype | | `common.input` | | | |
| G3 | Input layout. The spec input is NCHW only, and the sidecar has no layout field. Convert a TFLite or MediaPipe model with an NHWC input with `tf2onnx --inputs-as-nchw` before the intake. Write the conversion command in the evidence column. If you cannot convert the input to NCHW, the verdict is `gap` (skellytracker ADR-90CE item 2). | | `common.input` | `not used` | | |
| G4 | Input dims (batch, channels, height, width) for each size. The channels and the spatial dims must be static. | | `common.sizes_and_artifacts`, `common.input` | | | |
| G5 | Output: name, dtype and shape. Add one row for each output. | | `common.outputs` | | | |
| G6 | Batch of each file: a static `N`, or dynamic. The sidecar has one `batching.batch` for each size and each precision: `3`, `1` or `dynamic`. | | `common.batching` (`batching.batch`), `common.sizes_and_artifacts` (Batch forms) | | | |
| G6a | Batch axis: dim 0 of each input and each output. The spec has no field for it. If the batch is on another axis, the verdict is `gap`. | | `common.batching` | `not used` | | |
| G6b | Batch conversion: the verdict of the batch-conversion check (`converts`: `exact`; `does not convert`: `gap`; `not applicable`: `out of scope`; `to run`: `unverified`). See "Batch conversion check" below. | | `common.batch_conversion` | `batching.batch_conversion`, or `not used` | | |
| G7 | I/O dtype for each precision: the input and every output | | `common.input`, `common.outputs` | | | |
| G8 | Normalization inside the graph (Sub, Div or Mul near the input) | | `pre.normalize` | | | |
| G9 | NMS or TopK inside the graph (near the outputs) | | `post.det.decode` (Selection behaviour) | | | |
| G9a | Parameters of the NMS inside the graph: IoU threshold, score threshold and row caps, compared with the upstream test config. The sidecar does not declare them. A value that differs from the upstream is an export defect: write it in the last column. | | `post.det.selection.none` | `not used` | | |

### Family

One family has one preprocessing contract and one post-processing contract. If two sizes differ in a
field that is not a per-size field, they are two families. Write one intake for each family.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| F1 | `model_id`. An object detector uses the family (`yolo26`). A keypoint detector uses `{family}-{part}` (`rtmw-wholebody`). The spec has no rule yet for a suffix after the part (the spec example `rtmo-body7`), or for two models of one family and one part. Until a spec change adds such a rule, write `{family}-{part}`: the verdict is `exact`. If the exporter or the spec example uses an id with a suffix, write that id in the last column. A name is never a `near-miss`. If another model of the same family and part also needs `{family}-{part}`, the row is a `gap`. A new role with no `model_id` rule is a `gap`. | | `common.identity` | | | |
| F2 | `role`: `object_detector`, `pose_estimator`, or both | | `common.identity` | | | |
| F3 | Sizes, and what differs between them. A size sets only `input.shape`, `input.resize.target_size` and `onnx`. Use the upstream size name, also for a family with one size. If the upstream has no size name, choose a lowercase token and give the reason. | | `common.sizes_and_artifacts` | | | |
| F4 | One contract for all sizes: channel order, normalization, resize method, output semantics, selection mode, NMS parameters, class mapping | | `common.sizes_and_artifacts` (family invariant) | | | |
| F5 | ONNX file names: `{model_id}-{size}_b{batch}_{precision}.onnx`, where `{batch}` is `batching.batch`, or `{model_id}-{size}_{precision}.onnx` for the batch `dynamic` | | `format.file_layout` | | | |
| F6 | `display_name` (required) | | `common.identity` | | | |

### Preprocessing

Source: the upstream inference pipeline and the code of each transform.

- Every upstream step must have a row. The pre-filled rows are in the order of the spec. Add a row for
  each upstream step that the list does not have.
- Record the upstream line behind each value.
- Write the upstream order of all steps in row T12. The spec normalizes after the resize. If the
  upstream order is different, write the difference in row T12.
- The resizes of the spec are not antialiased. Check the upstream resize call.
- `cv2.resize` uses half-pixel centres for `linear`, `cubic` and `area`. `cv2.INTER_NEAREST` takes
  the source pixel `floor(x * src_n / dst_n)`. `cv2.warpAffine` puts the pixel centres at integer
  coordinates. The spec uses `cv2.resize` for `letterbox` and `stretch`, and `cv2.warpAffine` for
  `fit` and `affine_person_crop`. The inverse uses the same convention (the heading "Pixel centres"
  of `pre.resize.interpolation`; skellytracker ADR-G79P). Check that the upstream uses the same
  call, or the same convention, also in its inverse.
- In OpenCV, a scalar `borderValue` fills only the first channel of a 3-channel image. Record the
  border value of each upstream warp for each channel.
- In the spec, a scalar `pad_value` `s` means `[s, s, s]` for each method. A scalar is `exact` when
  the upstream border has the same value in each channel. Otherwise, write an array.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| T1 | Channel order of the source image that the upstream pipeline reads (BGR or RGB). The spec has no field for it: it is the evidence for T9. Write `not used` as the sidecar value. | | `common.input` | `not used` | | |
| T2 | Resize method (`letterbox`, `stretch`, `fit`, `affine_person_crop` or `none`) | | `common.input` (`input.resize`), `pre.resize.<method>` (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop`) | | | |
| T3 | Target size `[height, width]` for each size | | `common.input` (`input.resize`), `common.sizes_and_artifacts` | | | |
| T4 | Scale factor: its formula, for example `min(T_w / src_w, T_h / src_h)` | | `pre.resize.<method>` (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop`) | | | |
| T4a | Rounding of the scaled size (`rounding`, `letterbox` only) | | `pre.resize.letterbox` | | | |
| T4b | Arithmetic of the scale, the scaled size and the offsets: float32 or float64, and the order of the operations. In float64, `77 * (640 / 77)` is `639.9999999999999`. | | `pre.resize.<method>` (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop`) | | | |
| T5 | Position of the image on the canvas (`pad_position`, `letterbox` only) | | `pre.resize.letterbox` | | | |
| T5a | `fit` geometry: a scale that is not rounded, offsets `left` and `top` that are centred and fractional, and one warp matrix `M` (`fit` only) | | `pre.resize.fit` | | | |
| T6 | Pad value or border value (`pad_value`, or `crop_policy.pad_value` for `affine_person_crop`), for each channel. A scalar `s` means `[s, s, s]`. | | `common.input` (`pad_value`), `pre.resize.affine_person_crop` (`crop_policy.pad_value`) | | | |
| T7 | Interpolation filter, and no antialias | | `pre.resize.interpolation` | | | |
| T7a | Resize call and its pixel-centre convention (`cv2.resize` or `cv2.warpAffine`, or another library) | | `pre.resize.<method>` (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop`), `pre.resize.interpolation` | | | |
| T7b | Dtype of the image when the upstream resizes and pads it (`input.resize.compute_dtype`: `uint8` for an 8-bit image, `float32` for a float image) | | `pre.resize.interpolation` | | | |
| T8 | Crop policy: expand ratio and aspect ratio (`crop_policy`, `affine_person_crop` only) | | `pre.resize.affine_person_crop` | | | |
| T9 | Channel order of the tensor that the model consumes (`input.color_format`, required for each normalization mode). The mode `imagenet` and the mode `custom` apply their values in this channel order. | | `common.input`, `pre.normalize` | | | |
| T10 | Normalization for each precision (`input.normalization`, required, with no default): mean, std and scale, and its arithmetic (for example a float32 division by 255, or a multiplication by `1/255`) | | `pre.normalize` | | | |
| T11 | Layout change (HWC to CHW) and cast to `input.dtype` | | `common.input` | | | |
| T12 | Order of the steps: the upstream order compared with the order of the spec | | `pre.normalize` | | | |

### Outputs and decode

Source: the upstream postprocessing code and the upstream test config.

- Write one row for each decode step, in the upstream order.
- Take the thresholds from the upstream test config. Do not take them from library defaults.
- If the model has no `object_detector` role, write `not used` in rows D2 to D10 and in row D12.
  Row D11 also applies to the keypoints of a pose estimator. Fill it in for every model.
- `clamp_boxes` has the default `true`. A sidecar without the field clamps the boxes. Check the
  upstream before you omit the field.
- `min_box_size` has no default. A sidecar without the field drops no box for its size, and a box
  with zero area stays. Check the upstream for an area filter, for example mmdet `min_bbox_size`.
  If the upstream has one, write `decode.min_box_size`. If the upstream keeps each box, omit the
  field.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| D1 | Semantic of each output (`detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `keypoints` or `poses`). Add one row for each output. | | `common.outputs`, `post.det.outputs` | | | |
| D2 | Fields of a detection row (`fields`) and box format (`box_format`) | | `post.det.outputs`, `post.det.decode` | | | |
| D3 | Box scale: model-input pixels or normalized (`box_scale`) | | `post.det.decode`, `post.unprojection` | | | |
| D4 | Selection: graph-final rows (`none`), top-k over logits (`top_k`), or host NMS (`nms`) | | `post.det.decode` (`selection`), `post.det.selection.<selection>` (`none`, `top_k`, `nms`) | | | |
| D5 | Score activation: sigmoid inside the graph or on the host (`score_activation`) | | `post.det.decode`, `post.det.selection.top_k` (`score_activation`) | | | |
| D6 | Score source and class source (`score_field`, `scores_output`, `class_field`, `class_logits_output`) | | `post.det.decode`, `post.det.selection.top_k` (`class_logits_output`) | | | |
| D7 | Thresholds from the upstream test config: NMS IoU, NMS score and the box-size filter (mmdet `min_bbox_size`), final confidence | | `post.det.selection.nms` (`nms`), `post.det.decode` (`min_box_size`, `confidence_threshold_default`) | | | |
| D8 | Threshold comparison (`>` or `>=`), the dtype of the comparison, and the tie order | | `post.det.decode` (Selection behaviour) | | | |
| D9 | Row limits: graph-final row count (`max_detections`), `top_k`, `nms.post_nms_top_k` | | `post.det.selection.none`, `post.det.selection.top_k`, `post.det.selection.nms` | | | |
| D10 | Class IDs: `class_id_base`, `class_id_map`, `is_person_only`, `person_class_id`. The host assigns `person_class_id` only through `is_person_only`. A model with no class source (no `class_field` and no `class_logits_output`) must set `is_person_only: true` (`V-post.det.decode-9`). A one-class model of something other than people is a `gap`. | | `post.det.decode` | | | |
| D11 | Unprojection of boxes and keypoints to the source image (the inverse of the resize method) | | `post.unprojection`, `pre.resize.<method>` (`letterbox`, `stretch`, `fit`, `none`, `affine_person_crop`) (Inverse), `post.pose.decode.<method>` (`simcc`, `coordinate`) | | | |
| D12 | Box clamp to the source image (`clamp_boxes`, default `true`) and the box-size filter (`min_box_size`, no default). The spec clamps each `x` to `[0, W]` and each `y` to `[0, H]` of the source image: compare the upstream bounds. Write what the upstream does with a box that has no area or a small area. An upstream area filter maps to `min_box_size`. | | `post.det.decode` | | | |

### Pose

- Write `tracked_points` in the native output order of the model: the i-th name is the i-th keypoint
  that the model gives. Do not reorder the names.
- If the model has no `pose_estimator` role, write `not used` in every row.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| K1 | Estimator type and `requires_object_detector` | | `post.pose.schema` | | | |
| K2 | `tracked_points` in native output order | | `post.pose.schema` (`pose.tracked_points`) | | | |
| K3 | Connections: named skeletons and their edges | | `post.pose.schema` (`pose.connections`) | | | |
| K4 | Output geometry (`pose.geometry`: `2d` or `3d`, required), decode method (`simcc` or `coordinate`) and its parameters (`coordinate_scale`, `depth_unit`, `depth_range`) | | `post.pose.schema` (`pose.geometry`, `pose.decode`), `post.pose.decode.<method>` (`simcc`, `coordinate`) | | | |
| K5 | Keypoint axis and keypoint count of each pose output | | `post.pose.schema` (`keypoint_axis`, `keypoint_count`) | | | |
| K6 | Bottom-up row alignment: pose row `q` belongs to detection row `q` | | `post.pose.bottom_up` | | | |
| K7 | Keypoints packed into the detection row (`packed_keypoints`) | | `post.pose.bottom_up` | | | |
| K8 | Keypoint score: its source, and its activation. The spec says that a packed keypoint `score` is already activated. The spec has no field for a keypoint-score activation: if the host must activate the scores, the verdict is `gap`. | | `post.pose.decode.<method>` (`simcc`, `coordinate`), `post.pose.bottom_up` | | | |
| K9 | Canonical mapping (optional) | | `post.pose.canonical_mapping` | | | |
| K10 | Overlay (optional) | | `post.overlay` | | | |
| K11 | Landmark schema (`pose.landmark_schema`, optional) | | `post.pose.schema` | | | |

### YAML

These rows are rules for the sidecar file. In the evidence column, cite the exporter code that writes
the value. The sidecar value is what the sidecar must contain. Follow "Values that the exporter
chooses" in [Verdicts](#verdicts).

| # | Property | Evidence (exporter code that writes the value) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| Y1 | `batching.batch` is the int `3`, the int `1` or the string `dynamic`, once for the sidecar (`V-common.sizes_and_artifacts-12`). Each size has `onnx.precision_artifacts` and `onnx.output_shapes`. | | `common.batching` (`batching.batch`), `common.sizes_and_artifacts` (`sizes.<size>.onnx`) | | | |
| Y2 | `schema_version` is the open target as a quoted string, for example `"2.0.0"` (`V-format.versioning-1`). Without the quotes, YAML can read the value as a number. | | `format.versioning` | | | |
| Y3 | Each size contains only `input.shape`, `input.resize.target_size` and `onnx` | | `common.sizes_and_artifacts` | | | |
| Y4 | No `null` values. A sidecar omits an optional field that has no value (heading "Behaviour" of `format.composition`). | | `format.composition` | | | |
| Y5 | Each `$ref` path resolves and stays inside `{sidecar_root}`. The sidecar has no `base`. | | `format.composition` | | | |
| Y6 | Each key is a key that the spec defines (`V-format.composition-5`). A key that the spec does not define is invalid, for example the removed keys `requires_nms`, `preserve_aspect_ratio`, `may_include_non_person_classes`, `input.layout`, `base` and `batch_artifacts`. | | `format.composition` | | | |
| Y7 | A top-level `source`; a `sha256` on every `$ref` and every `filename` artifact; UTF-8 without BOM; LF line endings | | `common.identity` (`source`), `format.composition` (Reference hashes), `common.sizes_and_artifacts` (`sha256`) | | | |

Row Y7: a sidecar must have these fields, UTF-8 without a BOM and LF line endings. If the
exporter does not write them yet, the verdict stays `exact`. Write the exporter defect in the last
column. This row does not stop the intake. The exporter must write the fields and regenerate its
sidecars.

Publish a sidecar only when "Publishing" in
`specs/model-sidecar/model-addition-workflow/validation-and-publishing.md` allows it.

### Path in the storage layout

The storage layout of the spec starts at `{sidecar_root}`. In an exporter, the export root has that
role. Write the path under the export root.

| # | Property | Evidence (exporter code that writes the file) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| L1 | Sidecar path: `<export root>/detectors/object_detectors/{family}/{model_id}.yaml`, where `{family}` is the `model_id`; or `<export root>/detectors/keypoint_detectors/{family}/{part}/{model_id}.yaml`, where `{part}` is `hand`, `face`, `body` or `wholebody` | | `format.file_layout` (Storage layout) | | | |
| L2 | The ONNX files are in the same folder as the sidecar | | `format.file_layout` (File pairing rules) | | | |

A model-specific folder, for example `body7`, does not conform. If the exporter writes to such a
folder, the sidecar value is still the spec path. Write the path of the exporter in the last column
as an exporter defect. The verdict of row L1 stays `exact`.

If the storage layout has no branch for the role of the model (a new role), the verdict of row L1 is
`gap`. The proposal that adds the role also adds the branch (`format.file_layout`, heading "Storage
layout").

### Steps outside the model contract

Write one row for each upstream step before or after the runtime contract of this model. Phase 1
(`specs/model-sidecar/model-addition-workflow/phase-1-intake.md`) gives the verdict `out of scope`,
examples and what to do with such a row. If the upstream has no such step, write `none` in row X1.

| # | Property | Upstream evidence (file and line, or config key) | Section | Sidecar value | Verdict | What the step does |
|---|---|---|---|---|---|---|
| X1 | | | none | `not used` | `out of scope` | |

## The sidecar

Fill in this section when no row is blocking (step 5 of phase 1). Step 5 gives the rules for the
sidecar and for an `unverified` row. Name each `unverified` row in the table below.

If a row is blocking, write `skipped` in each cell, with the row, for example
`skipped (row T4a is near-miss)`. Write `none` in the draft block. The proposal of the row holds the
YAML excerpts (part 2) and the parity plan (part 5).

| Item | Value |
|---|---|
| Sidecar file in the exporter repo (`<export root>/detectors/...`) | |
| Exporter code that writes it (file and function) | |
| Is the file tracked in git? (`yes` or `no`) | |
| Export command | |
| Differences from the spec reference example of the same family (or `no example`) | |
| Rows that are `unverified`: the draft uses the value that you expect (or `none`) | |

**Draft.** If you cannot change the writer code yet, write the exact YAML of the draft in the block
below (step 5 of phase 1). If the writer code writes the sidecar, write `none` in the block.

```yaml
```

## Validation checklist

If a row of the property table is blocking, write `skipped` in the Result column of each group row.
Then go to [Parity proof](#parity-proof).

If a row is `unverified` and no row is blocking, walk the checklist on the draft. Add
`(provisional: row <#>)` to each result that depends on an `unverified` row.

Walk the validation rules as "Validation" in
`specs/model-sidecar/model-addition-workflow/validation-and-publishing.md` says. It also gives the
result of `V-format.versioning-1` and of `V-format.versioning-2`. For `V-format.versioning-1`, check
the value against the version headings under "Revisions" in `specs/model-sidecar/changelog.md`. Then
run the checks of the exporter.

The skellytracker package cannot check a sidecar of the open target yet:

- `SidecarModel` (`skellytracker/core/sidecar/model.py`) rejects `schema_version: "2.0.0"`. The value
  does not match the version pattern of `parse_skellytracker_version`
  (`skellytracker/core/sidecar/versioning.py`).
- `SidecarModel` forbids undeclared keys, and it does not declare all the fields of the current
  text. For example, `DetectionDecodeSpec` has no `selection`.

So walk the checklist by hand where the checks of the exporter do not cover a rule.

The pre-filled rows are group headers. Under each group, add one row for each rule that you checked.
Write its rule ID (`V-<section-id>-<n>`). Write `not used` for a group that the sidecar does not use.

| Group | Rule ID (`V-<section-id>-<n>`) | Result (`pass`, `fail`, `not used`, `n/a until a final release loads the target` or `skipped`) | How checked (script and commit, or by hand) |
|---|---|---|---|
| Identity and composition (`format.versioning`, `format.composition`, `common.identity`) | | | |
| Sizes and artifacts (`common.sizes_and_artifacts`, `common.batching`) | | | |
| Input, resize, normalization (`common.input`, `pre.*`) | | | |
| Outputs (common) (`common.outputs`) | | | |
| Detection (`object_detector`: `post.det.*`) | | | |
| Pose (`pose_estimator`: `post.pose.*`) | | | |
| Overlay (`post.overlay`) | | | |

**Checks of the exporter.**

| Check | Script or command (path and commit) | Result |
|---|---|---|
| | | |

## Parity proof

This proof is for the sidecar of this intake. The full rules are in the model addition workflow
(`specs/model-sidecar/model-addition-workflow/parity.md`, heading "Parity").

- If a row of the property table is blocking, write `skipped` in each cell of the tables below. Each
  proposal has its own parity evidence in its part 5.
- If a row is `unverified` and no row is blocking, fill in the tables for the draft. Mark
  each result that depends on an `unverified` row as provisional.
- If you cannot run the check, write `to run` as the result, and give the reason. Fill in each cell
  that does not need a number: the gates, the test images, the upstream reference, the script and the
  command. Write `to run` in each cell that needs a number.
- If you do not know the path or the commit of the script, write `unknown (<reason>)` in its cell.

Run the ONNX model. Do the preprocessing and the decode exactly as the sidecar declares. Compare the
result with the upstream library.

- The code that applies the sidecar is the host implementation of each section in the exporter.
  Write it from the spec text.
- If a section has test vectors (`specs/model-sidecar/vectors/`), the host implementation must pass them
  first. Run the numeric cases of each section that the model uses through the host code. Record the
  result of each section in `vector-runs.yaml` of the `model` bundle, as "Payload" in
  `specs/model-sidecar/model-addition-workflow/hand-over.md` says (skellytracker ADR-ESP4).
- If a reference implementation of a section exists (`specs/model-sidecar/reference/`), use it or match it.
- If no reference implementation of a section exists, add the reference-implementation step to your
  plan (see [Proposals and reference files](#proposals-and-reference-files)).
- Set each gate before the run.
- Use more than one test image. Each branch of each section that the sidecar uses must run on at
  least one image.
- Commit the parity script in the exporter repo. A script that is only in a local plan folder is not
  evidence.

**Host implementation of each section.**

| Section ID (the `id` in the section file's front matter) | Host code (file and function) | Vectors (`pass`, `fail` or `no vectors`) | Reference implementation (`used`, `matched` or `none exists`) |
|---|---|---|---|
| | | | |

**Parity result.**

Commit the parity script in the exporter repo before you run it. A result counts only with the path and
the commit of a committed script. A script that is only in an untracked file is not evidence. If the exporter already has a
parity script for this model, name it and its commit, and record what it does not compare.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | |
| Test images (paths or dataset IDs), and the branch that each image runs | |
| Upstream reference: library, version, config and command | |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | |
| Preprocessed input: maximum absolute difference for each image (expect 0; if not 0, the cause) | |
| Row count for each image: sidecar path and upstream | |
| Boxes, scores and classes in source-image coordinates (`object_detector` role): metric and value | |
| Keypoints and keypoint scores in source-image coordinates (`pose_estimator` role): metric and value | |
| Final outputs of another role (Parity, step 5): output, metric and value | |
| Result (`pass`, `fail`, `to run` or `skipped`) | |
| Script path in the exporter repo | |
| Exporter commit of the script | |
| Command | |

## Batch conversion check

Do the batch-conversion check in step 1b of phase 1. Follow "Batch-conversion check" in
`specs/model-sidecar/model-addition-workflow/batch-conversion-check.md`. Choose the published batch
form as "Publishing" in `specs/model-sidecar/model-addition-workflow/validation-and-publishing.md`
says. "Manifest" in `specs/model-sidecar/model-addition-workflow/hand-over.md` gives the meaning of
each field. Put the output folder in the bundle as `batch/`.

| Item | Value |
|---|---|
| Verdict (`converts`, `does not convert`, `not applicable` or `to run`) | |
| Forced fallback form (`batch_forced`: `1`, `dynamic` or `null`) and the reason of the person who runs the exporter | |
| No static graph (`no_static_reason`): why the model cannot export a static graph, or `null` | |
| Reason, for `to run` (`missing-verification-batch`, `host-runtime-cannot-load` or `no-signal`) | |
| Failed (size, precision, `N`) tuples, for `does not convert` | |
| Published batch form (b3, b1 or `dynamic`) | |
| Dynamic check (V6) of each `dynamic` file: `pass`, `fail`, `to run` or `not used` | |
| Command, skellytracker commit, and the onnx and onnxruntime versions of `report.json` | |

## Proposals and reference files

**Proposals.** Write one row for each proposal. Write each proposal with the change proposal template
(`specs/model-sidecar/templates/change-proposal.md`).

| Intake rows | Proposal bundle ID (`proposal-<slug>@<contributor>`) | Proposed section ID (the `id` in the section file's front matter) | New or changed section | Depends on (bundle IDs, or `none`) |
|---|---|---|---|---|
| | | | | |

**Reference implementations.** Do the reference-implementation step before the final verdict. Do it
for every verdict. Skip a section as "When to do the step" in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md` says. For each other
section, do "The step" in the same file. Write one row for each section in the table below. If the
host code is not committed yet, write `to run` in the table (skellytracker ADR-ESP4).

| Section ID (the `id` in the section file's front matter) | Host code (file, function and commit) | Reference file in the bundle (`reference/<section_module>.py`) | Vector result | Parity result unchanged (`yes`, `no` or `to run`) |
|---|---|---|---|---|
| | | | | |

## Final verdict

Write the final verdict as "Final verdict" in
`specs/model-sidecar/model-addition-workflow/phase-1-intake.md` says. "Blocking rows" in the same file
tells which row is blocking.

| Item | Value |
|---|---|
| Verdict (`describes`, `does not describe` or `pending`) | |
| Batch conversion (`batch_conversion` of the manifest, and its reason for `to run`) | |
| Reason (one sentence) | |
| Missing evidence and runs: each `unverified` row and the evidence that it needs, and each result that is `to run` (or `none`) | |
| `out of scope` rows to tell the user | |
| Spec defects that you found and did not propose (or `none`) | |

Then pack the bundle and stop. If the verdict is `describes`, a skellytracker session can add the
sidecar as a spec example (under `specs/model-sidecar/examples/`, with its provenance in
`specs/model-sidecar/inventory.yaml`). The procedure is "Reference examples" in
`specs/model-sidecar/model-addition-workflow/reference-examples.md`.
