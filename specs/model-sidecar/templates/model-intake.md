# Model intake template

This template is phase 1 of the new-model workflow. Phase 1 answers one question: can the current
sidecar spec describe this model exactly? The full workflow is the model addition workflow
(`specs/model-sidecar/model-addition-workflow/README.md` of the skellytracker repo). It is the same
for an exporter and for a human contributor. Where this template says "the exporter", a contributor
that is not an exporter reads "you". The workflow
README gives the stages and the phases. Phase 2 is the change proposal template (`specs/model-sidecar/templates/change-proposal.md`). You
need phase 2 only when phase 1 finds a `near-miss` or a `gap`.

This template has relative links only in the section column of the property tables. Each link goes to
the "Authoring guidance" heading of a section file. The links work in the skellytracker repo. They do
not work in your copy of the template. In your copy, find the section file with the section map in
`specs/model-sidecar/README.md`. The template names each other skellytracker file by its path in a code
span, each spec section by its section ID, and each spec heading by its text and the section file
that holds it. Read the skellytracker files in the skellytracker checkout (read-only)
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
4. Read the spec. Its entry point is `specs/model-sidecar/sidecar-spec.md`. The section map
   `specs/model-sidecar/README.md` lists each section ID and its section file. The spec is normative.
5. Do not approximate a property. If the spec does not describe a property exactly, the verdict is
   `near-miss` or `gap`.
6. Group the `near-miss` and `gap` rows by the part of the spec that they change. Write one change
   proposal for each new or changed part. Then write the final verdict. Do the
   reference-implementation step. Then stop.
7. Do not change a file in skellytracker. The only exception: `pack` writes the new version folder of
   your bundle in `intakes/`.

**Section IDs.** The spec is split into section files under `specs/model-sidecar/`. Each section file has a
section ID: the `id` in its front matter, for example `pre.resize.letterbox`. Write the section ID in
the section column. Each pre-filled row names the section ID that usually applies.
`pre.resize.<method>` is the section of the resize method, for example `pre.resize.letterbox`.
`post.det.selection.<selection>` and `post.pose.decode.<method>` have the same form. If a different
section describes the property, change it.

In the property tables, each section ID links to the "Authoring guidance" heading of its section. That
guidance gives the mapping from upstream config keys to sidecar fields, and what to check. Read it
before you fill in the row. A row with a placeholder (`<method>` or `<selection>`) links to all the
sections that the placeholder can name. If you change the section ID of a row, change its link.

**The steps of phase 1.**

1. List every property of the runtime contract of the model. Use three sources:
   - the ONNX graph: each input and each output;
   - the upstream preprocessing pipeline: each transform step, in order;
   - the upstream postprocessing: each decode step, in order.
2. For each row, write the property, the upstream evidence, the section ID, the sidecar value and the
   verdict.
3. A blocking row is a `near-miss` or `gap` row other than row G6b. Row G6b with the verdict `gap`
   (`does not convert`) only leaves `batching.batch_conversion` out of the sidecar. It also sends a
   new-profile proposal to phase 2. If no row is blocking, the sidecar writer of the exporter writes
   the sidecar. Then walk the validation checklist and prove parity. If a row is `unverified`, these
   results are provisional.
4. If a row is blocking, write a change proposal for it. Do this also when other rows are
   `unverified`. A blocking row comes before an `unverified` row. If row G6b is `gap`, also write
   the new-profile proposal.
5. Write the final verdict.

An upstream step that does nothing for this model is also a row. The row gives the evidence that the
step does nothing.

## Inputs before you start

Get these inputs before you fill in the property table.

| Input | Path, URL or command | Status (`found` or `missing`) |
|---|---|---|
| The ONNX files: every size and precision, at the verification batches 1, 2, 3 and 4 (not needed for a forced fallback form). The `dynamic` export, if you plan to publish it | | |
| Input B of the batch-conversion check: `batch/inputs/<size>.npy` for each size, with 4 different preprocessed images (not needed for `batch_forced: 1`; a forced `dynamic` form needs it for the dynamic check) | | |
| The upstream inference config (the test pipeline, not the training pipeline) | | |
| The upstream preprocessing code | | |
| The upstream postprocessing code | | |
| One reference output of the upstream library on a known image | | |

If an input is missing, do not stop. Write `missing` in its row. Use the best secondary source for the
rows that need the input, and give each of these rows the verdict `unverified`. A `near-miss` row or a
`gap` row can rest on a secondary source (see "Evidence" in [Verdicts](#verdicts)). When you stop,
tell the user which inputs are missing.

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
| Date | |

**ONNX files.** Write one row for each file. Fill in the SHA-256 now, for example with
`sha256sum <file>`. It identifies the file that you read. It is not the artifact field `sha256` of
the sidecar (`common.sizes_and_artifacts`, heading "Authoring guidance").

| File | Size | Batch key | Precision | `published` or `verification-only` | SHA-256 |
|---|---|---|---|---|---|
| | | | | | |

## Verdicts

| Verdict | Meaning |
|---|---|
| `exact` | A section of the spec describes the property with these values. |
| `near-miss` | The spec has a section and a field for the property, but no value describes the property exactly. A detail differs: the rounding, the pixel centres, the arithmetic precision, the order of steps, the threshold comparison, or a similar detail. A detail that the spec does not define is also a near-miss when it changes the output for some input. A near-miss is a gap. |
| `gap` | The spec has no section and no field for the property. A property that the spec calls out of scope, or that the spec lists in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), is also a gap. |
| `unverified` | You do not have the evidence for a verdict, for example because an input is missing or the evidence is only secondary. "Evidence" below gives two exceptions. Name the missing evidence in the last column. If you expect a verdict, write it there too. |
| `out of scope` | The step is before or after the runtime contract of this model. The contract starts at the inputs of the model: the source image, and the box for `affine_person_crop`. It ends at the decoded outputs in source-image coordinates. |

**Near-miss or gap.** Use this test, so that two agents give the same verdict:

1. Find the section and the field that hold the property.
2. If no section and no field hold it, the verdict is `gap`. Examples: a rotated crop, a border mode,
   a model that gives a crop region.
3. If a field holds it, but none of its values describes the upstream, the verdict is `near-miss`.
   Example: the upstream code rounds the letterbox size with `floor`, and the letterbox `rounding` has
   only `half_even` and `half_up` (section `pre.resize.letterbox`,
   `specs/model-sidecar/pre/resize-letterbox.md`).
4. A row for a name or a path is never a `near-miss`. A name or a path changes no tensor and no
   decoded output.

**Evidence.** In the evidence column, give the upstream file and line, the config key, or the command
that read the graph with the node or tensor name. A plan, a paper, a README, the notes of an exporter
and a spec reference example are secondary sources. Write a secondary citation with `(secondary)`, for
example `the untracked letterbox plan of OpenMMLab-Exporter (secondary)`. Do not give the path of an
untracked file (heading "Sources" in `specs/model-sidecar/model-addition-workflow/rules.md`). A row
with only a secondary source is `unverified`.
There are two exceptions:

- A `near-miss` or a `gap` compares the property with the spec text. If only a secondary source shows
  the property, still give the row its `near-miss` or `gap` verdict. Name the missing primary
  evidence in the last column. The proposal of the row names it in part 1. Before the user accepts
  the proposal, part 1 must cite the primary evidence.
- A value that the exporter chooses has no upstream evidence (see the next paragraph).

Do not copy a value from a spec reference example (`specs/model-sidecar/examples/README.md`). After you fill
in every row, compare your values with the example of the same family (see
[The sidecar](#the-sidecar)).

**Values that the exporter chooses.** Some rows have no upstream source, because the exporter chooses
the value. These rows are F1, F5 and F6, the size name in F3, the YAML rows Y1 to Y7 and the path
rows L1 and L2. For these rows:

- Judge the verdict against the spec only. The sidecar value is what the spec requires.
- In the evidence column, cite the exporter code that writes the value. If no such code exists,
  write `none yet (no code)`. If you cannot read the code, write `not read (<reason>)`.
- Such a row is not `unverified` only because the exporter code does not exist or you cannot read it.
  In that case, write `not checked` in the last column.
- If the exporter writes a different value today, the verdict stays `exact`. Write the exporter
  defect in the last column.
- Such a row is a `gap` only when the spec has no rule for the role of the model (a new role), for
  example no `model_id` rule or no branch of the storage layout. The proposal of the role covers the
  row. Row F1 gives one more `gap`: the current text has no `model_id` for a second model of one
  family and one part.

For each row that is not `exact`, write what differs or what is missing in the last column. For each
`near-miss` row and each `gap` row, link its proposal in
[Proposals and reference files](#proposals-and-reference-files).

**Near-misses seen so far.**

- **A letterbox where the upstream code warps to a fractional size.** The upstream code warps the
  full frame with `cv2.warpAffine` to a scaled size that is not rounded. If you map it to `letterbox`,
  the verdict is `near-miss`: `letterbox` rounds the scaled size and uses a resize plus padding. Read
  the section `pre.resize.fit` (`specs/model-sidecar/pre/resize-fit.md`) and compare it with the upstream
  code (skellytracker decision 0012; OpenMMLab-Exporter 0020).
- **A letterbox where the upstream code cuts the scaled size with `int()` or `floor`.** The
  `rounding` field has no value for a cut. The verdict is `near-miss`.
- **An ROI refiner described as a pose estimator with two fake keypoints.** An ROI refiner is a model
  that gives a region of interest to the next model, for example a hand re-crop model. Its verdict is
  `gap`. Do not describe it as `role: [pose_estimator]` with two points such as `crop_center` and
  `crop_scale`. The spec has no role for a model that gives a crop region, and a host reads the
  outputs of a pose estimator as keypoints.

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
| G1 | Input name | | [`common.input`](../common/input.md#authoring-guidance) | | | |
| G2 | Input dtype | | [`common.input`](../common/input.md#authoring-guidance) | | | |
| G3 | Input layout (`NCHW` or `NHWC`) | | [`common.input`](../common/input.md#authoring-guidance) | | | |
| G4 | Input dims (batch, channels, height, width): static or dynamic, for each size | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance), [`common.input`](../common/input.md#authoring-guidance) (`supports_dynamic_size`) | | | |
| G5 | Output: name, dtype and shape. Add one row for each output. | | [`common.outputs`](../common/outputs.md#authoring-guidance) | | | |
| G6 | Batch of each file: a static `N`, or dynamic | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) (`sizes.<size>.onnx.batch_artifacts`) | | | |
| G6a | Batch axis (`batching.batch_axis`; the spec allows only `0`) | | [`common.batching`](../common/batching.md#authoring-guidance) | | | |
| G6b | Batch conversion: the verdict of the batch-conversion check (`converts`: `exact`; `does not convert`: `gap`; `not applicable`: `out of scope`; `to run`: `unverified`). See "Batch conversion check" below. | | [`common.batch_conversion`](../common/batch-conversion.md#authoring-guidance) | `batching.batch_conversion`, or `not used` | | |
| G7 | I/O dtype for each precision: the input and every output | | [`common.input`](../common/input.md#authoring-guidance), [`common.outputs`](../common/outputs.md#authoring-guidance) | | | |
| G8 | Normalization inside the graph (Sub, Div or Mul near the input) | | [`pre.normalize`](../pre/normalization.md#authoring-guidance) | | | |
| G9 | NMS or TopK inside the graph (near the outputs) | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance) (Selection behaviour) | | | |
| G9a | Parameters of the NMS inside the graph: IoU threshold, score threshold and row caps, compared with the upstream test config. The sidecar does not declare them. A value that differs from the upstream is an export defect: write it in the last column. | | [`post.det.selection.none`](../post/selection-none.md#authoring-guidance) | `not used` | | |

### Family

One family has one preprocessing contract and one post-processing contract. If two sizes differ in a
field that is not a per-size field, they are two families. Write one intake for each family.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| F1 | `model_id`. An object detector uses the family (`yolo26`). A keypoint detector uses `{family}-{part}` (`rtmw-wholebody`). The spec has no rule yet for a suffix after the part (the spec example `rtmo-body7`), or for two models of one family and one part. Until a spec change adds such a rule, write `{family}-{part}`: the verdict is `exact`. If the exporter or the spec example uses an id with a suffix, write that id in the last column. A name is never a `near-miss`. If another model of the same family and part also needs `{family}-{part}`, the row is a `gap`. A new role with no `model_id` rule is a `gap`. | | [`common.identity`](../common/identity.md#authoring-guidance) | | | |
| F2 | `role`: `object_detector`, `pose_estimator`, or both | | [`common.identity`](../common/identity.md#authoring-guidance) | | | |
| F3 | Sizes, and what differs between them. A size sets only `input.shape`, `input.resize.target_size` and `onnx`. Use the upstream size name, also for a family with one size. If the upstream has no size name, choose a lowercase token and give the reason. | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) | | | |
| F4 | One contract for all sizes: channel order, normalization, resize method, output semantics, selection mode, NMS parameters, class mapping | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) (family invariant) | | | |
| F5 | ONNX file names: `{model_id}-{size}_{batch}_{precision}.onnx`, or `{model_id}-{size}_{precision}.onnx` for a dynamic batch | | [`format.file_layout`](../format/file-layout.md#authoring-guidance) | | | |
| F6 | `display_name` (required) | | [`common.identity`](../common/identity.md#authoring-guidance) | | | |

### Preprocessing

Source: the upstream inference pipeline and the code of each transform.

- Every upstream step must have a row. The pre-filled rows are in the order of the spec. Add a row for
  each upstream step that the list does not have.
- Record the upstream line behind each value.
- Write the upstream order of all steps in row T12. The spec normalizes after the resize. If the
  upstream order is different, write the difference in row T12.
- The resizes of the spec are not antialiased. Check the upstream resize call.
- `cv2.resize` uses half-pixel centres. `cv2.warpAffine` puts the pixel centres at integer
  coordinates. The spec names the OpenCV call for each method. Check that the upstream uses the same
  call, or the same convention.
- In OpenCV, a scalar `borderValue` fills only the first channel of a 3-channel image. Record the
  border value of each upstream warp for each channel.
- For `fit` and `affine_person_crop`, write one value for each channel, for example
  `[114, 114, 114]`. The spec does not say yet what a scalar fills for these methods. That is a known
  spec defect. The array form is `exact` under the current text. A scalar `0` gives the same border
  in both readings. A scalar is correct for `letterbox`, because the `letterbox` pseudocode fills
  every channel.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| T1 | Channel order of the source image that the upstream pipeline reads (BGR or RGB). The spec has no field for it: it is the evidence for T9. Write `not used` as the sidecar value. | | [`common.input`](../common/input.md#authoring-guidance) | `not used` | | |
| T2 | Resize method (`letterbox`, `stretch`, `fit`, `affine_person_crop` or `none`) | | [`common.input`](../common/input.md#authoring-guidance) (`input.resize`), `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)) | | | |
| T3 | Target size `[height, width]` for each size | | [`common.input`](../common/input.md#authoring-guidance) (`input.resize`), [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) | | | |
| T4 | Scale factor: its formula, for example `min(T_w / src_w, T_h / src_h)` | | `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)) | | | |
| T4a | Rounding of the scaled size (`rounding`, `letterbox` only) | | [`pre.resize.letterbox`](../pre/resize-letterbox.md#authoring-guidance) | | | |
| T4b | Arithmetic of the scale, the scaled size and the offsets: float32 or float64, and the order of the operations. In float64, `77 * (640 / 77)` is `639.9999999999999`. | | `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)) | | | |
| T5 | Position of the image on the canvas (`pad_position`, `letterbox` only) | | [`pre.resize.letterbox`](../pre/resize-letterbox.md#authoring-guidance) | | | |
| T5a | `fit` geometry: a scale that is not rounded, offsets `left` and `top` that are centred and fractional, and one warp matrix `M` (`fit` only) | | [`pre.resize.fit`](../pre/resize-fit.md#authoring-guidance) | | | |
| T6 | Pad value or border value (`pad_value`, or `crop_policy.pad_value` for `affine_person_crop`), for each channel. An array of three values for `fit` and `affine_person_crop`. | | [`common.input`](../common/input.md#authoring-guidance) (`pad_value`), [`pre.resize.affine_person_crop`](../pre/resize-affine-person-crop.md#authoring-guidance) (`crop_policy.pad_value`) | | | |
| T7 | Interpolation filter, and no antialias | | [`pre.resize.interpolation`](../pre/interpolation.md#authoring-guidance) | | | |
| T7a | Resize call and its pixel-centre convention (`cv2.resize` or `cv2.warpAffine`, or another library) | | `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)), [`pre.resize.interpolation`](../pre/interpolation.md#authoring-guidance) | | | |
| T7b | Dtype of the image when the upstream resizes it (for example uint8, before the cast) | | `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)), [`pre.normalize`](../pre/normalization.md#authoring-guidance) | | | |
| T8 | Crop policy: expand ratio and aspect ratio (`crop_policy`, `affine_person_crop` only) | | [`pre.resize.affine_person_crop`](../pre/resize-affine-person-crop.md#authoring-guidance) | | | |
| T9 | Channel order of the tensor that the model consumes (`input.color_format`) | | [`common.input`](../common/input.md#authoring-guidance), [`pre.normalize`](../pre/normalization.md#authoring-guidance) | | | |
| T10 | Normalization for each precision: mean, std and scale, and its arithmetic (for example a float32 division by 255, or a multiplication by `1/255`) | | [`pre.normalize`](../pre/normalization.md#authoring-guidance) | | | |
| T11 | Layout change (HWC to CHW) and cast to `input.dtype` | | [`common.input`](../common/input.md#authoring-guidance) | | | |
| T12 | Order of the steps: the upstream order compared with the order of the spec | | [`pre.normalize`](../pre/normalization.md#authoring-guidance) | | | |

### Outputs and decode

Source: the upstream postprocessing code and the upstream test config.

- Write one row for each decode step, in the upstream order.
- Take the thresholds from the upstream test config. Do not take them from library defaults.
- If the model has no `object_detector` role, write `not used` in rows D2 to D10 and in row D12.
  Row D11 also applies to the keypoints of a pose estimator. Fill it in for every model.
- `clamp_boxes` has the default `true`. A sidecar without the field clamps the boxes. Check the
  upstream before you omit the field.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| D1 | Semantic of each output (`detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints` or `poses`). Add one row for each output. | | [`common.outputs`](../common/outputs.md#authoring-guidance), [`post.det.outputs`](../post/detection-outputs.md#authoring-guidance) | | | |
| D2 | Fields of a detection row (`fields`) and box format (`box_format`) | | [`post.det.outputs`](../post/detection-outputs.md#authoring-guidance), [`post.det.decode`](../post/detection-decode.md#authoring-guidance) | | | |
| D3 | Box scale: model-input pixels or normalized (`box_scale`) | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance), [`post.unprojection`](../post/unprojection.md#authoring-guidance) | | | |
| D4 | Selection: graph-final rows (`none`), top-k over logits (`top_k`), or host NMS (`nms`) | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance) (`selection`), `post.det.selection.<selection>` ([none](../post/selection-none.md#authoring-guidance), [top_k](../post/selection-top-k.md#authoring-guidance), [nms](../post/selection-nms.md#authoring-guidance)) | | | |
| D5 | Score activation: sigmoid inside the graph or on the host (`score_activation`) | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance), [`post.det.selection.top_k`](../post/selection-top-k.md#authoring-guidance) (`score_activation`) | | | |
| D6 | Score source and class source (`score_field`, `scores_output`, `class_field`, `class_logits_output`) | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance), [`post.det.selection.top_k`](../post/selection-top-k.md#authoring-guidance) (`class_logits_output`) | | | |
| D7 | Thresholds from the upstream test config: NMS IoU, NMS score, final confidence | | [`post.det.selection.nms`](../post/selection-nms.md#authoring-guidance) (`nms`), [`post.det.decode`](../post/detection-decode.md#authoring-guidance) (`confidence_threshold_default`) | | | |
| D8 | Threshold comparison (`>` or `>=`), the dtype of the comparison, and the tie order | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance) (Selection behaviour) | | | |
| D9 | Row limits: graph-final row count (`max_detections`), `top_k`, `nms.post_nms_top_k` | | [`post.det.selection.none`](../post/selection-none.md#authoring-guidance), [`post.det.selection.top_k`](../post/selection-top-k.md#authoring-guidance), [`post.det.selection.nms`](../post/selection-nms.md#authoring-guidance) | | | |
| D10 | Class IDs: `class_id_base`, `class_id_map`, `is_person_only`, `person_class_id` | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance) | | | |
| D11 | Unprojection of boxes and keypoints to the source image (the inverse of the resize method) | | [`post.unprojection`](../post/unprojection.md#authoring-guidance), `pre.resize.<method>` ([letterbox](../pre/resize-letterbox.md#authoring-guidance), [stretch](../pre/resize-stretch.md#authoring-guidance), [fit](../pre/resize-fit.md#authoring-guidance), [none](../pre/resize-none.md#authoring-guidance), [affine_person_crop](../pre/resize-affine-person-crop.md#authoring-guidance)) (Inverse), `post.pose.decode.<method>` ([simcc](../post/pose-decode-simcc.md#authoring-guidance), [heatmap](../post/pose-decode-heatmap.md#authoring-guidance), [coordinate](../post/pose-decode-coordinate.md#authoring-guidance)) | | | |
| D12 | Box clamp to the source image (`clamp_boxes`, default `true`): the clamp bounds, and what the upstream does with a box that has no area after the clamp | | [`post.det.decode`](../post/detection-decode.md#authoring-guidance) | | | |

### Pose

- Write `tracked_points` in the native output order of the model: the i-th name is the i-th keypoint
  that the model gives. Do not reorder the names.
- If the model has no `pose_estimator` role, write `not used` in every row.

| # | Property | Upstream evidence (file and line, or config key) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| K1 | Estimator type and `requires_object_detector` | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) | | | |
| K2 | `tracked_points` in native output order | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) (`pose.tracked_points`) | | | |
| K3 | Connections: named skeletons and their edges | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) (`pose.connections`) | | | |
| K4 | Decode method (`simcc`, `heatmap` or `coordinate`) and its parameters (`coordinate_scale`, `is_3d`, `depth_unit`, `depth_range`) | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) (`pose.decode`), `post.pose.decode.<method>` ([simcc](../post/pose-decode-simcc.md#authoring-guidance), [heatmap](../post/pose-decode-heatmap.md#authoring-guidance), [coordinate](../post/pose-decode-coordinate.md#authoring-guidance)) | | | |
| K5 | Keypoint axis and keypoint count of each pose output | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) (`keypoint_axis`, `keypoint_count`) | | | |
| K6 | Bottom-up row alignment: pose row `q` belongs to detection row `q` | | [`post.pose.bottom_up`](../post/pose-bottom-up.md#authoring-guidance) | | | |
| K7 | Keypoints packed into the detection row (`packed_keypoints`) | | [`post.pose.bottom_up`](../post/pose-bottom-up.md#authoring-guidance) | | | |
| K8 | Keypoint score: its source, and its activation. The spec says that a packed keypoint `score` is already activated. The spec has no field for a keypoint-score activation: if the host must activate the scores, the verdict is `gap`. | | `post.pose.decode.<method>` ([simcc](../post/pose-decode-simcc.md#authoring-guidance), [heatmap](../post/pose-decode-heatmap.md#authoring-guidance), [coordinate](../post/pose-decode-coordinate.md#authoring-guidance)), [`post.pose.bottom_up`](../post/pose-bottom-up.md#authoring-guidance) | | | |
| K9 | Canonical mapping (optional) | | [`post.pose.canonical_mapping`](../post/canonical-mapping.md#authoring-guidance) | | | |
| K10 | Overlay (optional) | | [`post.overlay`](../post/overlay.md#authoring-guidance) | | | |
| K11 | Landmark schema (`pose.landmark_schema`, optional) | | [`post.pose.schema`](../post/pose-schema.md#authoring-guidance) | | | |

### YAML

These rows are rules for the sidecar file. In the evidence column, cite the exporter code that writes
the value. The sidecar value is what the sidecar must contain. If the exporter writes something else
today, the verdict stays `exact`. Write the exporter defect in the last column. If no exporter code
writes the value yet, or you cannot read it, follow "Values that the exporter chooses" in
[Verdicts](#verdicts). The verdict stays `exact`.

| # | Property | Evidence (exporter code that writes the value) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| Y1 | Batch keys are quoted strings (`"1"`, not `1`) | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) (`sizes.<size>.onnx.batch_artifacts`) | | | |
| Y2 | `schema_version` is the string `vNEXT` until skellytracker releases the spec. YAML reads `vNEXT` and `"vNEXT"` as the same string. | | [`format.versioning`](../format/versioning.md#authoring-guidance) | | | |
| Y3 | Each size contains only `input.shape`, `input.resize.target_size` and `onnx` | | [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) | | | |
| Y4 | No `null` values. In the spec, `null` only deletes an inherited key in a merge. | | [`format.composition`](../format/composition.md#authoring-guidance) (`base`) | | | |
| Y5 | Each `$ref` and `base` path resolves and stays inside `{sidecar_root}` | | [`format.composition`](../format/composition.md#authoring-guidance) | | | |
| Y6 | No legacy-only form: `requires_nms` without `selection`, `may_include_non_person_classes`, or `letterbox` with `preserve_aspect_ratio: false` | | The "Legacy behaviour" heading of [`post.det.decode`](../post/detection-decode.md#authoring-guidance) and [`pre.resize.letterbox`](../pre/resize-letterbox.md#authoring-guidance); the index is "Version-aware compatibility" in [`format.versioning`](../format/versioning.md#authoring-guidance) | | | |
| Y7 | A top-level `source`; a `sha256` on every `$ref`, `base` and `filename` artifact; UTF-8 without BOM; LF line endings | | [`common.identity`](../common/identity.md#authoring-guidance) (`source`), [`format.composition`](../format/composition.md#authoring-guidance) (Reference hashes), [`common.sizes_and_artifacts`](../common/sizes-and-artifacts.md#authoring-guidance) (`sha256`) | | | |

Row Y7: a `vNEXT` sidecar must have these fields, UTF-8 without a BOM and LF line endings. If the
exporter does not write them yet, the verdict stays `exact`. Write the exporter defect in the last
column. This row does not stop the intake. The exporter must write the fields and regenerate its
`vNEXT` sidecars.

Do not publish a `vNEXT` sidecar to a shared or remote folder. No skellytracker release can load it.

### Path in the storage layout

The storage layout of the spec starts at `{sidecar_root}`. In an exporter, the export root has that
role. Write the path under the export root.

| # | Property | Evidence (exporter code that writes the file) | Section ID (the `id` in the section file's front matter) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| L1 | Sidecar path: `<export root>/detectors/object_detectors/{family}/{model_id}.yaml`, where `{family}` is the `model_id`; or `<export root>/detectors/keypoint_detectors/{family}/{part}/{model_id}.yaml`, where `{part}` is `hand`, `face`, `body` or `wholebody` | | [`format.file_layout`](../format/file-layout.md#authoring-guidance) (Storage layout) | | | |
| L2 | The ONNX files are in the same folder as the sidecar | | [`format.file_layout`](../format/file-layout.md#authoring-guidance) (File pairing rules) | | | |

A model-specific folder, for example `body7`, does not conform. If the exporter writes to such a
folder, the sidecar value is still the spec path. Write the path of the exporter in the last column
as an exporter defect. The verdict of row L1 stays `exact`.

If the storage layout has no branch for the role of the model (a new role), the verdict of row L1 is
`gap`. The proposal that adds the role also adds the branch (`format.file_layout`, heading "Storage
layout").

### Steps outside the model contract

Write one row for each upstream step before or after the runtime contract of this model. Examples: a
step that makes the box from the outputs of another model, a gate that decides if the model runs, or
a choice that uses an earlier frame. Their verdict is `out of scope`. They need no proposal. Tell the
user about each row when you stop. If the upstream has no such step, write `none` in row X1.

| # | Property | Upstream evidence (file and line, or config key) | Section | Sidecar value | Verdict | What the step does |
|---|---|---|---|---|---|---|
| X1 | | | none | `not used` | `out of scope` | |

## The sidecar

Fill in this section when no row is blocking (step 3 of phase 1). If a row is `unverified`, use the
value that you expect for that row, and name the row in the table below. The draft is then
provisional.

If a row is blocking, write `skipped` in each cell, with the row, for example
`skipped (row T4a is near-miss)`. Write `none` in the draft block. The proposal of the row holds the
YAML excerpts (part 2) and the parity plan (part 5).

The sidecar writer code of the exporter writes the sidecar. Do not write it by hand. The file goes to
`<export root>/detectors/...` (row L1).

| Item | Value |
|---|---|
| Sidecar file in the exporter repo (`<export root>/detectors/...`) | |
| Exporter code that writes it (file and function) | |
| Is the file tracked in git? (`yes` or `no`) | |
| Export command | |
| Differences from the spec reference example of the same family (or `no example`) | |
| Rows that are `unverified`: the draft uses the value that you expect (or `none`) | |

**Draft.** If you cannot change the writer code yet, write the exact YAML of the sidecar in the block
below. It is a draft. A skellytracker session does not use a draft as a spec example. If the writer
code writes the sidecar, write `none` in the block.

```yaml
```

## Validation checklist

If a row of the property table is blocking, write `skipped` in the Result column of each group row.
Then go to [Parity proof](#parity-proof).

If a row is `unverified` and no row is blocking, walk the checklist on the draft. Add
`(provisional: row <#>)` to each result that depends on an `unverified` row.

Walk the validation rules of every section that the sidecar uses. Each section file has a
"Validation rules" heading, and each rule there has a rule ID (`V-<section-id>-<n>`, for example
`V-pre.resize.letterbox-1`). The validation index (`specs/model-sidecar/README.md` heading "Validation
rules") links to the rules of each section. It also gives the meaning of **(vNEXT)**: a rule marked
**(vNEXT)** applies only when `schema_version >= vNEXT`. Also check the "Legacy behaviour" heading of
each section that the sidecar uses, if the section has one. The index of these headings is
"Version-aware compatibility" (`specs/model-sidecar/format/versioning.md`). A `vNEXT` sidecar must not use
a legacy-only form. Then run the checks of the exporter.

- A `vNEXT` sidecar must pass every rule, also each rule marked **(vNEXT)**, except the two rules in
  the next bullet.
- `V-format.versioning-1` (the version pattern) and `V-format.versioning-2` (the support by the
  installed release) cannot pass for `vNEXT`. Write `n/a at vNEXT` as their result. They apply after
  the release step.

skellytracker cannot check a `vNEXT` sidecar yet:

- `SidecarModel` (`skellytracker/core/sidecar/model.py`) rejects `schema_version: "vNEXT"`. The value
  does not match the version pattern of `parse_skellytracker_version`
  (`skellytracker/core/sidecar/versioning.py`).
- `SidecarModel` forbids unknown keys, and it does not have all the `vNEXT` fields yet. For example,
  `DetectionDecodeSpec` has no `selection`.

So walk the checklist by hand where the checks of the exporter do not cover a rule.

The pre-filled rows are group headers. Under each group, add one row for each rule that you checked.
Write its rule ID (`V-<section-id>-<n>`). Write `not used` for a group that the sidecar does not use.

| Group | Rule ID (`V-<section-id>-<n>`) | Result (`pass`, `fail`, `not used`, `n/a at vNEXT` or `skipped`) | How checked (script and commit, or by hand) |
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
  result of each section in `vector-runs.yaml` of the `model` bundle (heading "Payload" in
  `specs/model-sidecar/model-addition-workflow/hand-over.md`). An `error` case and a `failed` case
  are not host runs.
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

Do the batch-conversion check in step 1b of phase 1. It runs by default. The rules are in
`specs/model-sidecar/model-addition-workflow/hand-over.md`, heading "Batch-conversion check". The
publish rule is in `specs/model-sidecar/model-addition-workflow/validation-and-publishing.md`,
heading "Publishing". Put the output folder in the bundle as `batch/`.

| Item | Value |
|---|---|
| Verdict (`converts`, `does not convert`, `not applicable` or `to run`; `not applicable` only with a forced fallback form) | |
| Forced fallback form (`batch_forced`: `1`, `dynamic` or `null`) and the reason of the person who runs the exporter | |
| Reason, for `to run` (`missing-verification-batch`, `host-runtime-cannot-load` or `no-signal`) | |
| Failed (size, precision, `N`) tuples, for `does not convert` | |
| Published batch form: b3 (needs `converts`), b1 or `dynamic` (one form for the whole family) | |
| Dynamic check (V6) of each `dynamic` file: `pass`, `fail`, `to run` or `not used` | |
| Command, skellytracker commit, and the onnx and onnxruntime versions of `report.json` | |

## Final verdict

The rule:

- `describes`: every row is `exact` or `out of scope`, **and** parity passes. Row G6b can also be
  `gap`: then leave `batching.batch_conversion` out, publish a fallback form (b1 or `dynamic`) and
  write a proposal for a new profile.
- `does not describe`: a row is blocking (step 3 of phase 1), also when other rows are
  `unverified`. Write one proposal for each new or changed part of the spec. Do not write a sidecar
  that approximates the model.
- `pending`: no row is blocking, but a row is `unverified`, or the parity result is `to run`.
- If parity fails, you missed or misjudged a property. Go back to step 1 of phase 1 and find it. Until
  you find it, the verdict is `pending`.
- Never loosen the tolerance to make parity pass.

| Item | Value |
|---|---|
| Verdict (`describes`, `does not describe` or `pending`) | |
| Batch conversion (`batch_conversion` of the manifest, and its reason for `to run`) | |
| Reason (one sentence) | |
| Missing evidence and runs: each `unverified` row and the evidence that it needs, and each result that is `to run` (or `none`) | |
| `out of scope` rows to tell the user | |
| Spec defects that you found and did not propose (or `none`) | |

Then do the reference-implementation step in
[Proposals and reference files](#proposals-and-reference-files). Do it for every verdict. Then stop.
If the verdict is `describes`, a skellytracker session can add the sidecar as a spec example (under
`specs/model-sidecar/examples/`, with its provenance in `specs/model-sidecar/inventory.yaml`). The procedure is
"Reference examples" in `specs/model-sidecar/model-addition-workflow/reference-examples.md`.

## Proposals and reference files

**Proposals.** Write one row for each proposal. Write each proposal with the change proposal template
(`specs/model-sidecar/templates/change-proposal.md`).

| Intake rows | Proposal bundle ID (`proposal-<slug>@<contributor>`) | Proposed section ID (the `id` in the section file's front matter) | New or changed section | Depends on (bundle IDs, or `none`) |
|---|---|---|---|---|
| | | | | |

**Reference implementations.** If the exporter implements a section on its host side, write a
reference implementation of that section. Do it for every verdict.

- Skip it if `specs/model-sidecar/reference/<section_module>.py` exists in skellytracker.
- Skip it if one of your proposals changes the section. The part 3 file of the proposal is the
  reference implementation.
- A part of the spec without an algorithm needs no reference implementation, for example
  `input.layout`, `input.dtype` or `input.resize.method: none`.
- Do it from committed host code. If the host code is not committed yet, or if it exists only in a
  plan, write `to run` in the table. Do the step after the commit.
- `<section_module>` is the section ID from the front matter of the section file (`id`), with each
  dot replaced by an underscore (`pre.resize.letterbox` gives `pre_resize_letterbox`). Write the
  section ID in the note at the top of the file.
- Write the clean, minimal form of the host code. Follow
  "Imports of other sections" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`.
  Write one function for each algorithm.
- In each docstring, cite the section ID and the exporter commit that the code comes from.
- Run the functions against the vectors of the section. They must pass. If the vector file says
  `unverified`, also run the numeric cases through the host code, and record both results in
  `vector-runs.yaml`. If the
  section has no vector file yet, record that. An `error` case and a `failed` case run only against
  the reference implementation.
- Run the functions in place of the host code in the parity check of the exporter. Record that the
  result does not change.
- Write the functions to `reference/<section_module>.py` of the `model` bundle. Put a short note at
  the top of the file: the section ID, the source commit, the vector results and the parity result.
  Then pack the bundle and stop.
- If the host code and an existing reference implementation do not agree, you found a spec defect or a
  bug. Write a proposal. Do not write a second reference implementation.

| Section ID (the `id` in the section file's front matter) | Host code (file, function and commit) | Reference file in the bundle (`reference/<section_module>.py`) | Vector result | Parity result unchanged (`yes`, `no` or `to run`) |
|---|---|---|---|---|
| | | | | |
