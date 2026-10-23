# Model intake template

This template is phase 1 of the new-model workflow. Phase 1 answers one question: can the current
sidecar spec describe this model exactly? The full workflow is in the exporter guide
(`specs/sidecar/exporter-guide.md` of the skellytracker repo, section "Sidecars"). The decision behind
it is skellytracker decision 0014 (`notes/decisions/0014-spec-lifecycle.md` of the skellytracker
repo). Phase 2 is the change proposal template (`specs/sidecar/templates/change-proposal.md`). You
need phase 2 only when phase 1 finds a `near-miss` or a `gap`.

This template has no relative links to other files, so its references stay correct after you copy it.
It names each skellytracker file by its path in a code span, and each spec heading by its text. Read
the skellytracker files in the read-only worktree `../freemocap/skellytracker-latest`.

## How to use this template

1. Copy this file to `plans/sidecar-intake-<model>.md` in the exporter repo. `<model>` is the
   `model_id` of the family.
2. Change the title to `# Model intake: <model>`.
3. Fill in every slot. Do not delete a pre-filled row. Do not leave a cell empty. If a value does not
   apply, write `not used`, `missing`, `to run`, `skipped` or `none`, with the reason.
4. Read the spec: `specs/sidecar-spec.md`. The spec is normative.
5. Do not approximate a property. If the spec does not describe a property exactly, the verdict is
   `near-miss` or `gap`.
6. Group the `near-miss` and `gap` rows by the part of the spec that they change. Write one change
   proposal for each new or changed part. Then stop.
7. Do not change a file in skellytracker.

**Section IDs.** Today the spec is one file. It will be split into section files. Each section file
will have a section ID, for example `pre.resize.letterbox`. Until that split, write the heading of
`specs/sidecar-spec.md` in the section column. Each pre-filled row names the heading that usually
applies. If a different heading describes the property, change it.

**The steps of phase 1.**

1. List every property of the runtime contract of the model. Use three sources:
   - the ONNX graph: each input and each output;
   - the upstream preprocessing pipeline: each transform step, in order;
   - the upstream postprocessing: each decode step, in order.
2. For each row, write the property, the upstream evidence, the section, the sidecar value and the
   verdict.
3. If every row is `exact` or `out of scope`, the sidecar writer of the exporter writes the sidecar.
   Then walk the validation checklist and prove parity.
4. Write the final verdict.

An upstream step that does nothing for this model is also a row. The row gives the evidence that the
step does nothing.

## Inputs before you start

Get these inputs before you fill in the property table.

| Input | Path, URL or command | Status (`found` or `missing`) |
|---|---|---|
| The ONNX files: every size, batch and precision | | |
| The upstream inference config (the test pipeline, not the training pipeline) | | |
| The upstream preprocessing code | | |
| The upstream postprocessing code | | |
| One reference output of the upstream library on a known image | | |

If an input is missing, do not stop. Write `missing` in its row. Use the best secondary source for the
rows that need the input, and give each of these rows the verdict `unverified`. When you stop, tell
the user which inputs are missing.

## Header

| Field | Value |
|---|---|
| Model (`model_id`) | |
| Sizes | |
| Exporter repo | |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | |
| Upstream library and version | |
| Upstream config (file path, and upstream commit or release) | |
| skellytracker folder that you read (normally `../freemocap/skellytracker-latest`) | |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | |
| Date | |

**ONNX files.** Write one row for each file. Fill in the SHA-256 now, for example with
`sha256sum <file>`. It identifies the file that you read. It is not the sidecar field `sha256` that
skellytracker decision 0016 adds later.

| File | Size | Batch key | Precision | SHA-256 |
|---|---|---|---|---|
| | | | | |

## Verdicts

| Verdict | Meaning |
|---|---|
| `exact` | A section of the spec describes the property with these values. |
| `near-miss` | The spec has a section and a field for the property, but no value describes the property exactly. A detail differs: the rounding, the pixel centres, the arithmetic precision, the order of steps, the threshold comparison, or a similar detail. A detail that the spec does not define is also a near-miss when it changes the output for some input. A near-miss is a gap. |
| `gap` | The spec has no section and no field for the property. A property that the spec calls out of scope, or that the spec lists in "Considered and deliberately not added", is also a gap. |
| `unverified` | You do not have the evidence for a verdict, for example because an input is missing or the evidence is secondary. Name the missing evidence in the last column. If you expect a verdict, write it there too. |
| `out of scope` | The step is before or after the runtime contract of this model. The contract starts at the inputs of the model: the source image, and the box for `affine_person_crop`. It ends at the decoded outputs in source-image coordinates. |

**Near-miss or gap.** Use this test, so that two agents give the same verdict:

1. Find the section and the field that hold the property.
2. If no section and no field hold it, the verdict is `gap`. Examples: a rotated crop, a border mode,
   a model that gives a crop region.
3. If a field holds it, but none of its values describes the upstream, the verdict is `near-miss`.
   Example: the upstream code rounds the letterbox size with `floor`, and the letterbox `rounding` has
   only `half_even` and `half_up` (`specs/sidecar-spec.md` heading `input.resize`).

**Evidence.** In the evidence column, give the upstream file and line, the config key, or the command
that read the graph with the node or tensor name. A plan, a paper, a README, the notes of an exporter
and a spec reference example are secondary sources. Write a secondary citation with `(secondary)`, for
example `plans/<file>.md:101-104 (secondary)`. A row with only a secondary source is `unverified`.
Do not copy a value from a spec reference example. After you fill in every row, compare your values
with the example of the same family (see [The sidecar](#the-sidecar)).

For each row that is not `exact`, write what differs or what is missing in the last column. For each
`near-miss` row and each `gap` row, link its proposal in
[Proposals and reference files](#proposals-and-reference-files).

**Near-misses seen so far.**

- **A letterbox where the upstream code warps to a fractional size.** The upstream code warps the
  full frame with `cv2.warpAffine` to a scaled size that is not rounded. If you map it to `letterbox`,
  the verdict is `near-miss`: `letterbox` rounds the scaled size and uses a resize plus padding. Read
  the `fit` method of the spec and compare it with the upstream code (skellytracker decision 0012;
  OpenMMLab-Exporter 0020).
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

| # | Property | Upstream evidence (file and line, or config key) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| G1 | Input name | | `input` | | | |
| G2 | Input dtype | | `input` | | | |
| G3 | Input layout (`NCHW` or `NHWC`) | | `input` | | | |
| G4 | Input dims (batch, channels, height, width): static or dynamic, for each size | | `sizes`, `input.resize` (`supports_dynamic_size`) | | | |
| G5 | Output: name, dtype and shape. Add one row for each output. | | `outputs` (common) | | | |
| G6 | Batch of each file: a static `N`, or dynamic | | `sizes.<size>.onnx.batch_artifacts` | | | |
| G6a | Batch axis (`batching.batch_axis`; the spec allows only `0`) | | `batching` | | | |
| G7 | I/O dtype for each precision: the input and every output | | `input`, `outputs` (common) | | | |
| G8 | Normalization inside the graph (Sub, Div or Mul near the input) | | Normalization modes | | | |
| G9 | NMS or TopK inside the graph (near the outputs) | | Selection behaviour | | | |
| G9a | Parameters of the NMS inside the graph: IoU threshold, score threshold and row caps, compared with the upstream test config. The sidecar does not declare them. A value that differs from the upstream is an export defect: write it in the last column. | | Selection behaviour (`selection: none`) | `not used` | | |

### Family

One family has one preprocessing contract and one post-processing contract. If two sizes differ in a
field that is not a per-size field, they are two families. Write one intake for each family.

| # | Property | Upstream evidence (file and line, or config key) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| F1 | `model_id`. An object detector uses the family (`yolo26`). A keypoint detector uses `{family}-{part}` (`rtmw-wholebody`). The spec has no rule yet for a suffix after the part (the spec example `rtmo-body7`), or for two models of one family and one part. If your model needs such a name, the verdict is `near-miss`. | | Identity | | | |
| F2 | `role`: `object_detector`, `pose_estimator`, or both | | Identity | | | |
| F3 | Sizes, and what differs between them. A size sets only `input.shape`, `input.resize.target_size` and `onnx`. Use the upstream size name, also for a family with one size. If the upstream has no size name, choose a lowercase token and give the reason. | | `sizes` | | | |
| F4 | One contract for all sizes: channel order, normalization, resize method, output semantics, selection mode, NMS parameters, class mapping | | `sizes` (family invariant) | | | |
| F5 | ONNX file names: `{model_id}-{size}_{batch}_{precision}.onnx`, or `{model_id}-{size}_{precision}.onnx` for a dynamic batch | | File extension and naming | | | |
| F6 | `display_name` (required) | | Identity | | | |

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

| # | Property | Upstream evidence (file and line, or config key) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| T1 | Channel order of the source image that the upstream pipeline reads (BGR or RGB). The spec has no field for it: it is the evidence for T9. Write `not used` as the sidecar value. | | `input` | `not used` | | |
| T2 | Resize method (`letterbox`, `stretch`, `fit`, `affine_person_crop` or `none`) | | `input.resize` | | | |
| T3 | Target size `[height, width]` for each size | | `input.resize`, `sizes` | | | |
| T4 | Scale factor: its formula, for example `min(T_w / src_w, T_h / src_h)` | | `input.resize` | | | |
| T4a | Rounding of the scaled size (`rounding`, `letterbox` only) | | `input.resize` | | | |
| T4b | Arithmetic of the scale, the scaled size and the offsets: float32 or float64, and the order of the operations. In float64, `77 * (640 / 77)` is `639.9999999999999`. | | `input.resize` | | | |
| T5 | Position of the image on the canvas (`pad_position`, `letterbox` only) | | `input.resize` | | | |
| T5a | `fit` geometry: a scale that is not rounded, offsets `left` and `top` that are centred and fractional, and one warp matrix `M` (`fit` only) | | `input.resize` | | | |
| T6 | Pad value or border value (`pad_value`, or `crop_policy.pad_value` for `affine_person_crop`), for each channel | | `input.resize` | | | |
| T7 | Interpolation filter, and no antialias | | `input.resize` | | | |
| T7a | Resize call and its pixel-centre convention (`cv2.resize` or `cv2.warpAffine`, or another library) | | `input.resize` | | | |
| T7b | Dtype of the image when the upstream resizes it (for example uint8, before the cast) | | `input.resize`, Normalization modes | | | |
| T8 | Crop policy: expand ratio and aspect ratio (`crop_policy`, `affine_person_crop` only) | | `input.resize` | | | |
| T9 | Channel order of the tensor that the model consumes (`input.color_format`) | | `input`, Normalization modes | | | |
| T10 | Normalization for each precision: mean, std and scale, and its arithmetic (for example a float32 division by 255, or a multiplication by `1/255`) | | Normalization modes | | | |
| T11 | Layout change (HWC to CHW) and cast to `input.dtype` | | `input` | | | |
| T12 | Order of the steps: the upstream order compared with the order of the spec | | Normalization modes | | | |

### Outputs and decode

Source: the upstream postprocessing code and the upstream test config.

- Write one row for each decode step, in the upstream order.
- Take the thresholds from the upstream test config. Do not take them from library defaults.
- If the model has no `object_detector` role, write `not used` in rows D2 to D10 and in row D12.
  Row D11 also applies to the keypoints of a pose estimator. Fill it in for every model.
- `clamp_boxes` has the default `true`. A sidecar without the field clamps the boxes. Check the
  upstream before you omit the field.

| # | Property | Upstream evidence (file and line, or config key) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| D1 | Semantic of each output (`detections`, `boxes`, `scores`, `class_logits`, `simcc_x`, `simcc_y`, `simcc_z`, `heatmap`, `keypoints` or `poses`). Add one row for each output. | | `outputs` (common), Detection output semantics | | | |
| D2 | Fields of a detection row (`fields`) and box format (`box_format`) | | `outputs` (detection), `decode` (detection) | | | |
| D3 | Box scale: model-input pixels or normalized (`box_scale`) | | `decode` (detection), Unprojection | | | |
| D4 | Selection: graph-final rows (`none`), top-k over logits (`top_k`), or host NMS (`nms`) | | Selection behaviour | | | |
| D5 | Score activation: sigmoid inside the graph or on the host (`score_activation`) | | `decode` (detection) | | | |
| D6 | Score source and class source (`score_field`, `scores_output`, `class_field`, `class_logits_output`) | | `decode` (detection) | | | |
| D7 | Thresholds from the upstream test config: NMS IoU, NMS score, final confidence | | `decode` (detection) | | | |
| D8 | Threshold comparison (`>` or `>=`), the dtype of the comparison, and the tie order | | Selection behaviour | | | |
| D9 | Row limits: graph-final row count (`max_detections`), `top_k`, `nms.post_nms_top_k` | | `decode` (detection) | | | |
| D10 | Class IDs: `class_id_base`, `class_id_map`, `is_person_only`, `person_class_id` | | `decode` (detection) | | | |
| D11 | Unprojection of boxes and keypoints to the source image (the inverse of the resize method) | | Unprojection, `pose.decode` | | | |
| D12 | Box clamp to the source image (`clamp_boxes`, default `true`): the clamp bounds, and what the upstream does with a box that has no area after the clamp | | `decode` (detection) | | | |

### Pose

- Write `tracked_points` in the native output order of the model: the i-th name is the i-th keypoint
  that the model gives. Do not reorder the names.
- If the model has no `pose_estimator` role, write `not used` in every row.

| # | Property | Upstream evidence (file and line, or config key) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| K1 | Estimator type and `requires_object_detector` | | `pose` (pose estimator) | | | |
| K2 | `tracked_points` in native output order | | `pose.tracked_points` | | | |
| K3 | Connections: named skeletons and their edges | | `pose.connections` | | | |
| K4 | Decode method (`simcc`, `heatmap` or `coordinate`) and its parameters (`coordinate_scale`, `is_3d`, `depth_unit`, `depth_range`) | | `pose.decode` | | | |
| K5 | Keypoint axis and keypoint count of each pose output | | `outputs` (pose) | | | |
| K6 | Bottom-up row alignment: pose row `q` belongs to detection row `q` | | Bottom-up decode | | | |
| K7 | Keypoints packed into the detection row (`packed_keypoints`) | | `packed_keypoints` (bottom-up packed rows) | | | |
| K8 | Keypoint score: its source, and its activation. The spec says that a packed keypoint `score` is already activated. The spec has no field for a keypoint-score activation: if the host must activate the scores, the verdict is `gap`. | | `pose.decode`, `packed_keypoints` (bottom-up packed rows) | | | |
| K9 | Canonical mapping (optional) | | `pose.canonical_mapping` | | | |
| K10 | Overlay (optional) | | `overlay` (visualization, pose estimator) | | | |
| K11 | Landmark schema (`pose.landmark_schema`, optional) | | `pose` (pose estimator) | | | |

### YAML

These rows are rules for the sidecar file. In the evidence column, cite the exporter code that writes
the value. The sidecar value is what the sidecar must contain. If the exporter writes something else
today, the verdict stays `exact`. Write the exporter defect in the last column.

| # | Property | Evidence (exporter code that writes the value) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| Y1 | Batch keys are quoted strings (`"1"`, not `1`) | | `sizes.<size>.onnx.batch_artifacts` | | | |
| Y2 | `schema_version` is the string `vNEXT` until skellytracker releases the spec. YAML reads `vNEXT` and `"vNEXT"` as the same string. | | Schema versioning | | | |
| Y3 | Each size contains only `input.shape`, `input.resize.target_size` and `onnx` | | `sizes` | | | |
| Y4 | No `null` values. In the spec, `null` only deletes an inherited key in a merge. | | `base` — inherit from another sidecar and override | | | |
| Y5 | Each `$ref` and `base` path resolves and stays inside `{cache_dir}` | | File composition: `$ref` includes and `base` inheritance | | | |
| Y6 | No legacy-only form: `requires_nms` without `selection`, `may_include_non_person_classes`, or `letterbox` with `preserve_aspect_ratio: false` | | Version-aware compatibility | | | |
| Y7 | A top-level `source`; a `sha256` on every `$ref`, `base` and `filename` artifact; UTF-8 without BOM; LF line endings | | Not in the spec yet (skellytracker decision 0016) | | | |

Row Y7: skellytracker decision 0016 adds these fields to the spec. Until the spec defines `source`, a
`vNEXT` sidecar without these fields is valid. Until then, write `not used` as the sidecar value and
`exact` as the verdict for row Y7. Write `not in the spec yet` in the last column. This row does not
stop the intake. After the spec text lands, the exporter must write the fields and regenerate its
`vNEXT` sidecars.

Do not publish a `vNEXT` sidecar to a shared or remote folder. No skellytracker release can load it.

### Path in the storage layout

The storage layout of the spec starts at `{cache_dir}`. In an exporter, the export root has that
role. Write the path under the export root.

| # | Property | Evidence (exporter code that writes the file) | Section (until the split: the heading in `specs/sidecar-spec.md`) | Sidecar value | Verdict | What differs or what is missing |
|---|---|---|---|---|---|---|
| L1 | Sidecar path: `<export root>/detectors/object_detectors/{family}/{model_id}.yaml`, where `{family}` is the `model_id`; or `<export root>/detectors/keypoint_detectors/{family}/{part}/{model_id}.yaml`, where `{part}` is `hand`, `face`, `body` or `wholebody` | | Storage layout | | | |
| L2 | The ONNX files are in the same folder as the sidecar | | File pairing rules | | | |

A model-specific folder, for example `body7`, does not conform. If the exporter writes to such a
folder, the sidecar value is still the spec path. Write the path of the exporter in the last column
as an exporter defect. The verdict of row L1 stays `exact`.

### Steps outside the model contract

Write one row for each upstream step before or after the runtime contract of this model. Examples: a
step that makes the box from the outputs of another model, a gate that decides if the model runs, or
a choice that uses an earlier frame. Their verdict is `out of scope`. They need no proposal. Tell the
user about each row when you stop. If the upstream has no such step, write `none` in row X1.

| # | Property | Upstream evidence (file and line, or config key) | Section | Sidecar value | Verdict | What the step does |
|---|---|---|---|---|---|---|
| X1 | | | none | `not used` | `out of scope` | |

## The sidecar

Fill in this section only when every row is `exact` or `out of scope`. Otherwise write `skipped` in
each cell.

The sidecar writer code of the exporter writes the sidecar. Do not write it by hand. The file goes to
`<export root>/detectors/...` (row L1).

| Item | Value |
|---|---|
| Sidecar file in the exporter repo (`<export root>/detectors/...`) | |
| Exporter code that writes it (file and function) | |
| Is the file tracked in git? (`yes` or `no`) | |
| Export command | |
| Differences from the spec reference example of the same family (or `no example`) | |

**Draft.** If you cannot change the writer code yet, write the exact YAML of the sidecar in the block
below. It is a draft. A skellytracker session does not use a draft as a spec example. If the writer
code writes the sidecar, write `none` in the block.

```yaml
```

## Validation checklist

If a row of the property table is `near-miss`, `gap` or `unverified`, write `skipped` in the Result
column of each group row. Then go to [Parity proof](#parity-proof).

Walk the validation rules (`specs/sidecar-spec.md` heading "Validation rules") of every part of the
spec that the sidecar uses. Also check the version-aware compatibility table
(`specs/sidecar-spec.md` heading "Version-aware compatibility"). A `vNEXT` sidecar must not use a
legacy-only form. Then run the checks of the exporter.

- A `vNEXT` sidecar must pass every rule, also each rule marked **(vNEXT)**, except the two items
  in the next bullet.
- The first two items of "Identity and composition" (the version pattern, and the support by the
  installed release) cannot pass for `vNEXT`. Write `n/a at vNEXT` as their result. They apply after
  the release step.

skellytracker cannot check a `vNEXT` sidecar yet:

- `SidecarModel` (`skellytracker/core/sidecar/model.py`) rejects `schema_version: "vNEXT"`. The value
  does not match the version pattern of `parse_skellytracker_version`
  (`skellytracker/core/sidecar/versioning.py`).
- `SidecarModel` forbids unknown keys, and it does not have all the `vNEXT` fields yet. For example,
  `DetectionDecodeSpec` has no `selection`.

So walk the checklist by hand where the checks of the exporter do not cover an item.

The pre-filled rows are group headers. Under each group, add one row for each checklist item. Until
the spec gives rule IDs, identify each item by its text. When the spec has rule IDs, write the rule ID.
Write `not used` for a group that the sidecar does not use.

| Group | Checklist item (text, or rule ID) | Result (`pass`, `fail`, `not used`, `n/a at vNEXT` or `skipped`) | How checked (script and commit, or by hand) |
|---|---|---|---|
| Identity and composition | | | |
| Sizes and artifacts | | | |
| Input, resize, normalization | | | |
| Outputs (common) | | | |
| Detection (`object_detector`) | | | |
| Pose (`pose_estimator`) | | | |
| Overlay | | | |

**Checks of the exporter.**

| Check | Script or command (path and commit) | Result |
|---|---|---|
| | | |

## Parity proof

This proof is for the sidecar of this intake. The full rules are in the exporter guide, section
"Sidecars", heading "Parity".

- If a row of the property table is `near-miss`, `gap` or `unverified`, write `skipped` in each cell
  of the tables below. Each proposal has its own parity evidence in its part 5.
- If you cannot run the check, write `to run` as the result, and give the reason. Describe the script
  and its gates.

Run the ONNX model. Do the preprocessing and the decode exactly as the sidecar declares. Compare the
result with the upstream library.

- The code that applies the sidecar is the host implementation of each section in the exporter.
  Write it from the spec text.
- If a section has test vectors (`specs/sidecar/vectors/`), the host implementation must pass them
  first.
- If a reference implementation of a section exists (`specs/sidecar/reference/`), use it or match it.
- If no reference implementation of a section exists, add the reference-implementation step to your
  plan (see [Proposals and reference files](#proposals-and-reference-files)).
- Set each gate before the run.
- Use more than one test image. Each branch of each section that the sidecar uses must run on at
  least one image.
- Commit the parity script in the exporter repo. A script that is only in a local `plans/` folder is
  not evidence.

**Host implementation of each section.**

| Section (ID or heading) | Host code (file and function) | Vectors (`pass`, `fail` or `no vectors`) | Reference implementation (`used`, `matched` or `none exists`) |
|---|---|---|---|
| | | | |

**Parity result.**

| Item | Value |
|---|---|
| Gates, set before the run, and their source | |
| Test images (paths or dataset IDs), and the branch that each image runs | |
| Upstream reference: library, version, config and command | |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | |
| Preprocessed input: maximum absolute difference for each image (expect 0; if not 0, the cause) | |
| Row count for each image: sidecar path and upstream | |
| Boxes, scores and classes in source-image coordinates (`object_detector` role): metric and value | |
| Keypoints and keypoint scores in source-image coordinates (`pose_estimator` role): metric and value | |
| Result (`pass`, `fail`, `to run` or `skipped`) | |
| Script path in the exporter repo | |
| Exporter commit of the script | |
| Command | |

## Final verdict

The rule:

- `describes`: every row is `exact` or `out of scope`, **and** parity passes.
- `does not describe`: a row is `near-miss` or `gap`. Write one proposal for each new or changed part
  of the spec. Do not write a sidecar that approximates the model.
- `pending`: no row is `near-miss` or `gap`, but a row is `unverified`, or the parity result is
  `to run`.
- If parity fails, you missed or misjudged a property. Go back to step 1 of phase 1 and find it. Until
  you find it, the verdict is `pending`.
- Never loosen the tolerance to make parity pass.

| Item | Value |
|---|---|
| Verdict (`describes`, `does not describe` or `pending`) | |
| Reason (one sentence) | |
| Missing evidence and runs (for `pending`) | |
| `out of scope` rows to tell the user | |

Then do the reference-implementation step in
[Proposals and reference files](#proposals-and-reference-files). Do it for every verdict. Then stop.
If the verdict is `describes`, a skellytracker session can add the sidecar as a spec example. The
procedure is "Reference examples" in `specs/sidecar-implementation-plan.md`.

## Proposals and reference files

**Proposals.** Write one row for each proposal. Write each proposal with the change proposal template
(`specs/sidecar/templates/change-proposal.md`).

| Intake rows | Proposal file (`plans/sidecar-proposal-<slug>.md`) | Proposed section ID, and the heading | New or changed section | Depends on (proposal files, or `none`) |
|---|---|---|---|---|
| | | | | |

**Reference implementations.** If the exporter implements a section on its host side, write a
reference implementation of that section. Do it for every verdict.

- Skip it if `specs/sidecar/reference/<section_module>.py` exists in skellytracker.
- Skip it if one of your proposals changes the section. The part 3 file of the proposal is the
  reference implementation.
- A part of the spec without an algorithm needs no reference implementation, for example
  `input.layout`, `input.dtype` or `input.resize.method: none`.
- Do it from committed host code. If the host code is not committed yet, or if it exists only in a
  plan, write `to run` in the table. Do the step after the commit.
- `<section_module>` is the section ID with each dot replaced by an underscore (`pre.resize.letterbox`
  gives `pre_resize_letterbox`). Until the split, take it from the table "Module names" in the
  exporter guide (section "Sidecars", heading "Reference implementations"), for example
  `input_resize_letterbox`. Write the heading in the note at the top of the file.
- Python cannot import `plans/sidecar-reference-<section_module>.py` by its name, because the name has
  hyphens. Load it with `importlib.util.spec_from_file_location`, or run it as a script.
- Write the clean, minimal form of the host code. Use only NumPy, OpenCV and the Python standard
  library. Do not import from the exporter or from skellytracker. Write one function for each
  algorithm.
- In each docstring, cite the section ID (until the split, the heading) and the exporter commit that
  the code comes from.
- Run the functions against the vectors of the section. They must pass. If the vector file says
  `unverified`, also run the vectors through the host code, and record both results. If the section
  has no vector file yet, record that.
- Run the functions in place of the host code in the parity check of the exporter. Record that the
  result does not change.
- Write the functions to `plans/sidecar-reference-<section_module>.py` in the exporter repo. Put a short
  note at the top of the file: the heading, the source commit, the vector results and the parity
  result. Then stop.
- If the host code and an existing reference implementation do not agree, you found a spec defect or a
  bug. Write a proposal. Do not write a second reference implementation.

| Section (ID or heading) | Host code (file, function and commit) | Reference file (`plans/sidecar-reference-<section_module>.py`) | Vector result | Parity result unchanged (`yes`, `no` or `to run`) |
|---|---|---|---|---|
| | | | | |
