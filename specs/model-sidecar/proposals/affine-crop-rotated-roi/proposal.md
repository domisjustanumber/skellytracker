# Change proposal: affine-crop-rotated-roi

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | The affine crop takes an ROI with a rotation |
| Slug | `affine-crop-rotated-roi` |
| Date | 2026-11-12 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `2c554cb817ec1cce82af0c97f46e96eef15e3cb6` |
| Model, and its `model` bundle ID | none. No model of OpenMMLab-Exporter needs a rotation. The pipeline spec needs the rotated crop for the MediaPipe Holistic hand chain (the decomposed MediaPipe example, item "Rotated crop" of `specs/pipeline/decisions/open-work.md`). That model has no `model` bundle. |
| Intake rows with the verdict `near-miss` or `gap` | none (no intake). The proposal closes two spec defects of `specs/model-sidecar/decisions/open-work.md`, heading "Spec defects": the sub-item "the box format and the coordinate space of the person box that `affine_person_crop` warps", and the rotated-ROI part of the item "No resize method crops a rotated ROI". |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `follow-up` |
| Base bundle of a follow-up (`base`, or `none`) | `proposal-affine-crop-matrix@openmmlab-exporter` (version 2, landed; skellytracker ADR-3S5G; record `specs/model-sidecar/proposals/affine-crop-matrix/proposal.md`) |
| Proposed section ID (the `id` in the section file's front matter) | `pre.resize.affine_crop`. The current ID is `pre.resize.affine_person_crop`. |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/resize-affine-crop.md`. The current file is `specs/model-sidecar/pre/resize-affine-person-crop.md`. |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of the spec log and the Proposed table of the root log are empty. The base entry skellytracker ADR-3S5G is landed. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `924c9773e48432a7ef7162b26942f69692615fbe`. The request named `efc5ee1`. The one later commit changes only decision-log files of the root log. The uncommitted changes of the checkout are in files that this proposal does not cite. |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | A top-down crop of a region of interest (ROI) with a rotation. The ROI is `(c_x, c_y, w, h, rotation)` in source-image pixels. The crop warps the ROI so that the ROI x axis becomes the x axis of the model input. A box is an ROI with rotation 0. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | (1) The rotated warp of mmpose. mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`): `TopdownAffine.transform` reads the optional `bbox_rotation` in degrees and gives it to `get_warp_matrix` ([`mmpose/datasets/transforms/topdown_transforms.py:99-108`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L99-L108)). `get_warp_matrix` turns the second point with `_rotate_point(np.array([src_w * -0.5, 0.]), rot_rad)` and, for `fix_aspect_ratio=False`, the third point with `_rotate_point(np.array([0., src_h * -0.5]), rot_rad)` ([`mmpose/structures/bbox/transforms.py:410-428`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L410-L428)). `_rotate_point` multiplies by `[[cs, -sn], [sn, cs]]` in float64 ([`mmpose/structures/bbox/transforms.py:493-506`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L493-L506)). `_get_3rd_point` turns `a - b` by 90 degrees around `b` ([`mmpose/structures/bbox/transforms.py:509-525`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L509-L525)). Thus the ROI x axis of an mmpose crop is `(cos r, sin r)`. (2) The rotated ROI of MediaPipe. mediapipe `c85dfbc2506b65ebc9a76340dc1234513b18c215` (branch `master`): "Rotation angle is clockwise in radians" ([`mediapipe/framework/formats/rect.proto:22-34`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/framework/formats/rect.proto#L22-L34)). The crop matrix turns the ROI with `{c, -d; d, c}`, `c = cos(rotation)`, `d = sin(rotation)` ([`mediapipe/calculators/tensor/image_to_tensor_utils.cc:116-175`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/calculators/tensor/image_to_tensor_utils.cc#L116-L175)). The Holistic hand chain gets the rotation from the wrist and the middle of the hand keypoints of the body pose, `target_angle - atan2(...)` with `target_angle = pi / 2` ([`mediapipe/modules/holistic_landmark/calculators/hand_detections_from_pose_to_rects_calculator.cc:124-151`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/modules/holistic_landmark/calculators/hand_detections_from_pose_to_rects_calculator.cc#L124-L151)). Then it scales and shifts the ROI along its own axes (`scale_x: 2.7`, `shift_y: -0.1`, `square_long: true`; [`mediapipe/modules/holistic_landmark/hand_landmarks_from_pose_to_recrop_roi.pbtxt:33-43`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/modules/holistic_landmark/hand_landmarks_from_pose_to_recrop_roi.pbtxt#L33-L43)). The hand landmark model gets the crop from `ImageToTensorCalculator` ([`mediapipe/modules/hand_landmark/hand_landmark_cpu.pbtxt:36-55`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/modules/hand_landmark/hand_landmark_cpu.pbtxt#L36-L55)). Both sources use the axis convention of the pipeline spec. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The skellytracker spec session passed on these rulings of the user (2026-11-12). They are not decisions of the user in this session. The user must confirm or refuse each one before acceptance. (a) The affine crop takes each ROI `(c_x, c_y, w, h, rotation)` in source-image pixels, not only an axis-aligned box. A box is an ROI with rotation 0. (b) The rotation convention is that of the pipeline spec: radians in `[-π, π)`, a positive rotation turns the ROI clockwise in the image, the ROI x axis is `(cos r, sin r)` and the ROI y axis is `(-sin r, cos r)` (heading "Behaviour" of `specs/pipeline/graph.md`, item 3; skellytracker ADR-7NY2 item 8). (c) The section file `pre/resize-affine-person-crop.md` becomes `pre/resize-affine-crop.md`. (d) The pipeline makes the ROI first. Then, right before the warp, the detector node applies `crop_policy`. The two growth factors multiply (heading "Behaviour" of `specs/pipeline/nodes/detector.md`, item "Crop"; skellytracker ADR-7NY2 item 8). This proposal adds one choice of its own, in part 2: the method value, the section ID and the rule IDs follow the new file name. |
| Nearest section ID (the `id` in the section file's front matter) | `pre.resize.affine_person_crop` |
| Why the nearest section is wrong | Behaviour says: "The rotation of the warp is always `0`. Rotated crops are out of scope." The steps take only `bbox_xyxy`. Authoring guidance calls a rotated ROI, and an ROI that does not come from a detector box, a `gap`. The pipeline spec gives the `rois` port the type `roi` with a rotation, and "Rotated ROI" in `specs/pipeline/nodes/detector.md` waits for this proposal. The section also does not define the box format and the coordinate space of the box that it warps (the spec defect above). The name `affine_person_crop` is wrong for a hand ROI or a face ROI. |
| Measured difference (number, image and script) | A crop with rotation 0 of an ROI with rotation `r` turns the content by `r`. Example: for the ROI `[200, 250, 200, 400, π/2]` at 256x192, the middle of the right edge of the model input maps to `(200, 437.5)` with this proposal (vector case `roi-quarter-turn-inverse`). It maps to `(387.5, 250)` with rotation 0. That is 265.2 px apart. Secondary (an uncommitted check of this draft, NumPy and OpenCV of the skellytracker environment): (1) for rotation 0, the reference file of part 3 gives the `M`, the centre and the crop size of the current reference file bit for bit, on the 24 numeric cases of the current vector file and on 20000 random boxes in four target sizes; (2) on 20000 random rotated ROIs (rotation uniform in `[-π, π)`, both values of `maintain_aspect_ratio`), the `M` of part 3 equals the `M` of the mmpose v1.3.2 `get_warp_matrix` form with `rot = degrees(r)` bit for bit. Part 5 gives the committed check that must replace these numbers. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | no. The MediaPipe Holistic hand landmark model (MediaPipe-Exporter) is not in the list. It joins the list on acceptance, if the user decides so. That model also needs other changes (see part 8, the row "A border mode"). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | The row "`crop_policy.border_mode`, rotated crops" ("Only constant borders and zero rotation are used."). The pipeline spec now needs the rotated crop: its `roi` type has a rotation (skellytracker ADR-7NY2 item 8), and its decomposed MediaPipe example waits for this proposal (item "Rotated crop" of `specs/pipeline/decisions/open-work.md`). The MediaPipe Holistic hand chain uses a rotated ROI (upstream evidence (2)). This proposal adds only the rotated crop. The border mode stays in the row. |

**Primary evidence.** The upstream lines of mmpose and MediaPipe above. The numbers of the row
"Measured difference" are secondary until the check of part 5 is committed and run.

## 2. Spec change

The relative links of the proposed text resolve from the record path
`specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the
section file (an editorial fix). A heading of the new text is quoted as text.

### 2.1 Sections

Changed section, renamed: `pre.resize.affine_person_crop` becomes `pre.resize.affine_crop`. The
title "Affine person crop" becomes "Affine crop". The file
`specs/model-sidecar/pre/resize-affine-person-crop.md` becomes
`specs/model-sidecar/pre/resize-affine-crop.md` (one `git mv`). The kind stays `preprocessor`.

**The rename.** The method value, the section ID, the title, each rule ID, the vector file and the
reference module follow the new file name, as skellytracker ADR-88WQ item 2 does for its renames:

| Old | New |
|---|---|
| `input.resize.method: affine_person_crop` | `input.resize.method: affine_crop` |
| `pre.resize.affine_person_crop` | `pre.resize.affine_crop` |
| `V-pre.resize.affine_person_crop-1`, `-2`, `-3` | `V-pre.resize.affine_crop-1`, `-2`, `-3` |
| `pre/resize-affine-person-crop.md` | `pre/resize-affine-crop.md` |
| `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml` | `specs/model-sidecar/vectors/pre.resize.affine_crop.yaml` |
| `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` | `specs/model-sidecar/reference/pre_resize_affine_crop.py` |
| `tools/vector_formulas/pre_resize_affine_person_crop.py` | `tools/vector_formulas/pre_resize_affine_crop.py` |

There is no alias. Spec version `2.0.0` is not released (skellytracker ADR-88WQ). Decided entries and
frozen proposal records keep the old names. A citation of an exporter function, for example
OpenMMLab-Exporter `onnx_runtime/preprocess.py::affine_person_crop`, keeps the name of that function.

Front matter of the new file:

```yaml
id: pre.resize.affine_crop
title: Affine crop
kind: preprocessor
selectors: [input.resize.method=affine_crop]
vectors: vectors/pre.resize.affine_crop.yaml
```

The keys `implemented_by`, `external_impl` and `tests` stay. The comment of `implemented_by.forward`
gets this sentence at its end: "No rotation: `top_down_affine` takes a box only, and
`get_warp_matrix` turns the second point above the centre." The `status` stays
`{spec: stable, validate: partial, forward: partial, inverse: partial}`.

**Section map.** In `specs/model-sidecar/README.md`, the row of `pre.resize.affine_person_crop` gets the ID `pre.resize.affine_crop`, the file
`pre/resize-affine-crop.md` as its link text and link target, and the title "Affine crop".

**The other sections.** The other sections change only by the rename of a name or a link. Their
behaviour and their vector `expect` values do not change. Thus they are not in the manifest
`sections` ("Full section" in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md`: a link or a sentence that
tells where the algorithm of another section applies does not change a section). The manifest
`sections` lists the new ID first and the old ID second, so that `verify` finds a later change of the
current section file.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.resize.affine_crop` (new file) | front matter | The front matter above. |
| `pre.resize.affine_crop` | title and the paragraph under "Fields" | The text of 2.2. |
| `pre.resize.affine_crop` | Behaviour | Replace the text from "The rotation of the warp is always `0`." to the sentence that starts "For a float32 box and `maintain_aspect_ratio: true`" with the text of 2.3. |
| `pre.resize.affine_crop` | Inverse | The table row `affine_person_crop` becomes `affine_crop`. No other edit. "Apply the inverse of the affine warp `M`" now names the `M` of 2.3. |
| `pre.resize.affine_crop` | Validation rules | The text of 2.4. |
| `pre.resize.affine_crop` | Implementer guidance | Add the bullets of 2.3, "Guidance", at the end. In the current bullets, change the method name only where a bullet names the method of this section. A bullet that quotes a result or a file keeps its words. |
| `pre.resize.affine_crop` | Authoring guidance | Replace the bullet that starts "Do not describe a rotated ROI with `affine_person_crop`." with the authoring bullet of 2.3. In the first bullet, `method: affine_person_crop` becomes `method: affine_crop`. The Qualcomm-Exporter bullet keeps its quote of the Qualcomm-Exporter README. Its first `affine_person_crop` names a value that Qualcomm-Exporter wrote, so it stays. |
| `common.input` (`common/input.md`) | Fields, the row `method` | "`affine_person_crop` is for top-down pose." becomes "`affine_crop` is the top-down crop of an ROI." |
| `common.input` | the line "Method-specific fields" and the line "Each `method` has its own section" | The link text and the target become `affine_crop` and `../pre/resize-affine-crop.md`. |
| `common.input` | Validation rules, `V-common.input-3` | `affine_person_crop` becomes `affine_crop`. |
| `post.unprojection` (`post/unprojection.md`) | Behaviour | "For `fit` and `affine_person_crop`" and "an `affine_person_crop` model gets the box of a detector" use `affine_crop`. The list item becomes `affine_crop`, with the link text "Affine crop" and the target `../pre/resize-affine-crop.md#inverse`. |
| `post.unprojection` | Implementer guidance | "No exporter has an inverse for `fit`, `none` or `affine_person_crop`" uses `affine_crop`. |
| `specs/model-sidecar/reference/post_unprojection.py` | the import, `RESIZE_METHODS`, `resize_inverse` and the docstrings | `import pre_resize_affine_person_crop` becomes `import pre_resize_affine_crop`, and each call follows. The method string becomes `affine_crop`. The rule ID in the docstring becomes `V-pre.resize.affine_crop-1`. In `resize_inverse`, the line `required(input, ("bbox_xyxy",), ...)` becomes a check that the input has `bbox_xyxy` or `roi`, so that an ROI case can run. No other change. |
| `specs/model-sidecar/vectors/post.unprojection.yaml` | cases `pixel-affine-person-crop` and `normalized-11-affine-person-crop` | `method: affine_person_crop` becomes `method: affine_crop`. The `expect` values do not change. The case IDs stay. |
| `pre.resize.interpolation` (`pre/interpolation.md`) | front matter `selectors`; Fields, the rows `interpolation` and `compute_dtype`; Pixel centres, the row `fit`, `affine_person_crop` | `affine_person_crop` becomes `affine_crop`. The comment of `implemented_by.forward` and the `external_impl` entry `OpenMMLab-Exporter: onnx_runtime/preprocess.py::affine_person_crop` keep the function names. |
| `specs/model-sidecar/reference/pre_resize_interpolation.py` | the key `"affine_person_crop"` of the method-to-call map, and the docstring that lists the methods | The key becomes `"affine_crop"`. The citations of `onnx_runtime/preprocess.py::affine_person_crop` keep the function name. |
| `pre.normalize` (`pre/normalization.md`) | Behaviour | "For `affine_person_crop`" becomes "For `affine_crop`". |
| `post.keypoint.schema` (`post/keypoint/schema.md`) | Fields, the row `keypoint.estimator_type` | "with `affine_person_crop` from a box or an ROI of an upstream node" becomes "with `affine_crop` from a box or an ROI of an upstream node". |
| `post.keypoint.schema` | the line "See also" under Validation rules | The link becomes `[Affine crop](../../pre/resize-affine-crop.md#validation-rules)`. |
| `post.keypoint.schema` | Implementer guidance, the bullet "The MediaPipe hand landmark model is top-down, but its crop does not come from a detector box." | Replace its second and third sentences with: "The pipeline builds a rotated ROI from the wrist, index and pinky keypoints of a body pose. `affine_crop` crops that ROI. The border of its crop is constant." The source of the bullet stays. |
| `post.keypoint.bottom_up` (`post/keypoint/bottom-up.md`) | the bullet that names three wrong choices | "`affine_person_crop` (no upstream person box)" becomes "`affine_crop` (no upstream box or ROI)". |
| `specs/model-sidecar/README.md` | section map; validation index | The section-map row above. The index line becomes `- [Affine crop](pre/resize-affine-crop.md#validation-rules)`. |
| `specs/model-sidecar/changelog.md` | Summary of changes | The row of 2.6. Apply the rename table to the text and the links of the earlier rows of the open target (rows 5, 32, 33, 34, 38 and 47), as skellytracker ADR-88WQ did. Only the new row names the old IDs. |
| `specs/model-sidecar/changelog.md` | Considered and deliberately not added | The row "`crop_policy.border_mode`, rotated crops" becomes "`crop_policy.border_mode`" with the reason "Only constant borders are used." |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item "The test vectors found these points that the spec does not define" | Delete the sub-item "the box format and the coordinate space of the person box that `affine_person_crop` warps". 2.3 gives the box format and the ROI. `post.unprojection` already gives the coordinate space. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item "No resize method crops a rotated ROI" | Replace the item with an item about the border only: "`affine_crop` fills the border with a constant. The MediaPipe Holistic hand chain fills the border with the edge pixels." Keep the MediaPipe-Exporter and Qualcomm-Exporter sources of the old item. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the sub-item "the arithmetic precision of the geometry (except the warp matrix `M` of `affine_person_crop`)" | `affine_person_crop` becomes `affine_crop`. |
| `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml` | `input.resize.method` | Part 7: `affine_person_crop` becomes `affine_crop` (forced edit). |
| `specs/model-sidecar/vectors/pre.resize.affine_crop.yaml` | the renamed file | `git mv` the current file. Then `land` replaces the 5 validator cases of part 4 and adds the 12 other cases of part 4. `land` keeps the file keys of the current file, so the session also edits them: the first note names the new section file; the second note says that a case gives `roi` or `bbox_xyxy` (the second note of the part 4 file); the third note of the part 4 file replaces the third note; the `unverified` text gets the sentence "The cases with a `roi` input list no implementation." The `section` key becomes `pre.resize.affine_crop`. |
| `specs/model-sidecar/reference/pre_resize_affine_crop.py` | new file | The file of part 3. Delete `specs/model-sidecar/reference/pre_resize_affine_person_crop.py`. |
| `tools/vector_formulas/pre_resize_affine_crop.py` | the renamed formula module | `git mv` the current module. `run`, `inverse` and `border` must read the new text: the ROI input, `roi_from_box` and the turned points. Keep `CHECKS`. Else the cross-check of `land` fails on the rotated cases. |
| `tools/make_vectors.py`, `tools/vector_formulas/post_unprojection.py`, `tools/vector_formulas/post_object_decode.py`, `tools/tests/test_vectors.py`, `tools/tests/test_traceability.py` | the module name, the section ID and the method string | Apply the rename table. |
| `tools/intake_bundle.py` | `RENAMED_SECTIONS` | Add `"pre.resize.affine_person_crop": "pre.resize.affine_crop"`. |
| `specs/model-sidecar/model-addition-workflow/mapping-hints.md`, `phase-1-intake.md`, `phase-2-proposal.md`, `specs/model-sidecar/templates/change-proposal.md`, `specs/model-sidecar/templates/model-intake.md` | each line that names the method or the rule `V-pre.resize.affine_person_crop-2` | Apply the rename table. These edits follow the rename only. They change no workflow rule. The session decides whether they need the procedure "Workflow changes" of `specs/model-sidecar/model-addition-workflow/hand-over.md`. |
| `specs/pipeline/nodes/detector.md` | Behaviour, the item "Crop", step 2 | The link becomes `[Affine crop](../../model-sidecar/pre/resize-affine-crop.md#behaviour)`. |
| `specs/pipeline/nodes/detector.md` | Behaviour, the item "Rotated ROI" | Replace the item with: "**Rotated ROI.** The sidecar crop takes the ROI with its rotation (link text "Affine crop", target `../../model-sidecar/pre/resize-affine-crop.md#behaviour`). A box is an ROI with rotation 0." The pipeline spec is not a section of this proposal. Its owner session decides the words. |
| `specs/pipeline/decisions/open-work.md` | Draft spec, the item "Rotated crop" | The pipeline session closes the item when this proposal lands. |
| `specs/sidecar-implementation-plan.md` | N2, the module list | `pre/resize_affine_person_crop.py` becomes `pre/resize_affine_crop.py` (part 6). |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `skellytracker/` package code, `specs/model-sidecar/decisions/entries/`, `specs/model-sidecar/proposals/`, `decisions/scripts/` | all | No edit. The old package code reads the old names until it is replaced (skellytracker ADR-AMJ8; skellytracker ADR-88WQ, Consequences). Decided entries, records and decided scripts keep the old names. |

### 2.2 Fields table

Title: `# Affine crop`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crop_policy` | object | no | This field applies to `affine_crop` only. See below. |

This resize is the top-down crop. The host warps a region of interest (ROI) of the source image to
`target_size` with an affine transform. The ROI has a centre, a size and a rotation. A box is an
ROI with rotation 0. The host does not pad a full frame. Top-down models such as RTMW and RTMW3D use
this resize. `crop_policy` controls how the host grows the ROI along its own axes before the warp:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input.resize.crop_policy.expand_ratio` | float | no | This factor multiplies the width and the height of the ROI before the affine warp. The default is `1.25`. |
| `input.resize.crop_policy.maintain_aspect_ratio` | bool | no | The default is `true`. When the value is `true`, the host enlarges the expanded ROI along its shorter side to the target aspect ratio `T_w / T_h`. When the value is `false`, the host warps the expanded ROI directly. This distorts the aspect ratio. |
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | no | No change: the current description. |

The paragraph under the table does not change.

### 2.3 Behaviour

Replace the current text with this text. The heading "Inverse" and its text follow it, with the
table row of 2.1.

````markdown
## Behaviour

The host gives the crop one ROI `(c_x, c_y, w, h, rotation)` for each instance:

- `c_x` and `c_y` are the centre, and `w` and `h` are the size, in source-image pixels. The
  positions follow [Unprojection](../../post/unprojection.md#behaviour). The crop uses the values as
  given. It adds no `0.5` offset and removes none.
- `rotation` is in radians. A positive rotation turns the ROI clockwise in the image, because the
  image y axis points down. The ROI x axis is `(cos(rotation), sin(rotation))` and the ROI y axis is
  `(-sin(rotation), cos(rotation))`, in image pixels. `w` is the size along the ROI x axis and `h`
  is the size along the ROI y axis.
- A box `bbox_xyxy = [x1, y1, x2, y2]` (left, top, right, bottom, in source-image pixels) gives the
  ROI with rotation 0 of the first block of the steps.

The normative steps are:

```text
# A box gives the ROI. float32: each value is float32, and the host rounds the result of each
# operation to float32.
x1, y1, x2, y2 = f32(bbox_xyxy)
roi = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, x2 - x1, y2 - y1, 0)

# The crop size, float32.
c_x, c_y, w, h = f32(roi.c_x), f32(roi.c_y), f32(roi.w), f32(roi.h)
e   = f32(expand_ratio)
w   = w * e                          # along the ROI x axis
h   = h * e                          # along the ROI y axis
if maintain_aspect_ratio:
    a = f32(T_w / T_h)
    if w > h * a: h = w / a
    else:         w = h * a

# Three point pairs: P in source pixels, Q in model-input pixels. Each P and Q is float32.
# cs, sn and each expression in f32(...) are float64. f32(...) rounds its result once.
cs = cos(f64(roi.rotation))
sn = sin(f64(roi.rotation))
P0 = (c_x, c_y)                                                 Q0 = (T_w / 2, T_h / 2)
P1 = (f32(c_x - (w * 0.5) * cs), f32(c_y - (w * 0.5) * sn))     Q1 = (0, T_h / 2)
if maintain_aspect_ratio:
    # float32
    P2 = (P1.x - (P0.y - P1.y), P1.y + (P0.x - P1.x))           Q2 = (0, T_h / 2 + T_w / 2)
else:
    P2 = (f32(c_x + (h * 0.5) * sn), f32(c_y - (h * 0.5) * cs)) Q2 = (T_w / 2, 0)

M        = the affine map that takes P0, P1, P2 onto Q0, Q1, Q2, solved in float64
pad      = crop_policy.pad_value
border   = [pad] * 3 if pad is a scalar else pad
dst      = warpAffine(src, M, (T_w, T_h), <interpolation>, borderMode=constant, borderValue=border)
```

- `f32(v)` rounds one value to float32 (IEEE 754 binary32, round to nearest, ties to even).
  `T_w / T_h` is a float64 division of the two integers, then one rounding. `w * 0.5` and
  `h * 0.5` are float32 and exact.
- `w > h * a` is a strict comparison of two float32 values. When `w` equals `h * a`, `h` does not
  change.
- `P1` is half the crop width from the centre, against the ROI x axis. With
  `maintain_aspect_ratio: true`, `P2` turns `P0 - P1` by 90 degrees around `P1`, so `M` uses `c`
  and `w` only, not `h`. The branch `h = w / a` and the strict `>` set only `h`: the crop height
  that mmpose returns as `input_scale`. The y scale of `M` comes from the float32 points. It can
  differ from the x scale and from `T_h / h`. Do not make `M` from `T_w / w` and `T_h / h`.
- With `maintain_aspect_ratio: false`, `P2` is half the crop height from the centre, against the
  ROI y axis.
- For rotation 0, `cs` is 1 and `sn` is 0. Then `P1 = (c_x - w * 0.5, c_y)`, and `P2` is
  `(P1.x, P1.y + (P0.x - P1.x))` or `(c_x, c_y - h * 0.5)`. The float64 expression, rounded once,
  equals the float32 operation, because double rounding from binary64 to binary32 is exact for `+`
  and `-`.
- `cos` and `sin` are float64 functions. Two math libraries can give a different last bit. A
  rotation that is not 0 can thus change a point by one float32 step.
- The crop uses the rotation as given. It does not wrap the rotation into `[-π, π)`.
- Each ROI value must be finite. After the aspect step, `w > 0` and `h > 0` must be true. The host
  must refuse an ROI that does not meet these conditions. This section gives no crop for such an
  ROI. NaN and inf are not finite.
- `cv2.getAffineTransform(src, dst)` with the float32 arrays `src = [P0, P1, P2]` and
  `dst = [Q0, Q1, Q2]` gives `M`.

`warpAffine` is `cv2.warpAffine`. Its pixel centres are at integer coordinates
([Pixel centres](../../pre/interpolation.md#pixel-centres)). For a float32 box and
`maintain_aspect_ratio: true`, `M` is the matrix of mmpose `GetBBoxCenterScale(padding=expand_ratio)`
+ `TopdownAffine`. For an ROI with rotation `r`, the points have the form of mmpose
`get_warp_matrix` with `rot` = `r` in degrees (`TopdownAffine` with `bbox_rotation`).
````

**Guidance** (bullets for Implementer guidance):

- A rotated ROI uses the form of mmpose `get_warp_matrix`: `_rotate_point` turns the second point,
  and for `fix_aspect_ratio=False` the third point, in float64. Then the float32 array rounds each
  point once. `_get_3rd_point` turns `P0 - P1` in float32. mmpose takes the rotation in degrees
  (`np.deg2rad(rot)`). For a parity run with mmpose, give `rot = degrees(r)` in float64. (mmpose
  [`mmpose/structures/bbox/transforms.py:410-428`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L410-L428),
  [`mmpose/structures/bbox/transforms.py:493-525`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L493-L525)
  and [`mmpose/datasets/transforms/topdown_transforms.py:99-108`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L99-L108))
- MediaPipe makes its crop matrix in float32 (`const float c = std::cos(sub_rect.rotation)`), and it
  maps the ROI to the tensor by its corners. The spec does not claim that a MediaPipe crop and an
  `affine_crop` crop give the same pixels. (mediapipe
  [`mediapipe/calculators/tensor/image_to_tensor_utils.cc:116-175`](https://github.com/google-ai-edge/mediapipe/blob/c85dfbc2506b65ebc9a76340dc1234513b18c215/mediapipe/calculators/tensor/image_to_tensor_utils.cc#L116-L175))
- The pipeline grows the ROI first (`roi_from_points`). Then `crop_policy` grows it again along the
  ROI axes. The two factors multiply (heading "Behaviour" of `specs/pipeline/nodes/detector.md`,
  item "Crop"). The vector case `roi-expand-along-roi-axes` shows the growth along the ROI axes.

**Authoring guidance** (replaces the bullet "Do not describe a rotated ROI with
`affine_person_crop`."):

- A top-down model whose upstream crops a rotated ROI uses `affine_crop`. The ROI rules (the shift,
  the square and the scale of the ROI) are pipeline rules (`roi_from_points`), not `crop_policy`.
  Write in `crop_policy.expand_ratio` only the growth of the preprocessing of the model itself.
  The border of `affine_crop` is constant (`crop_policy.pad_value`). A model whose upstream fills the
  border with the edge pixels does not map exactly to this section: that is a `near-miss`.

Behaviour on NaN, on inf, on a tie and on an empty input, for each new step:

| Step | NaN | inf | Tie | Empty input |
|---|---|---|---|---|
| The ROI of a box | The ROI value is NaN. The host refuses the ROI (finite rule). | The same as NaN. | none (no comparison) | A box with `x2 = x1` gives `w = 0`. The aspect step can make the crop size positive again. When `w` or `h` stays `<= 0`, the host refuses the ROI. |
| The crop size | Refused by the finite rule. | Refused by the finite rule. | The strict `>` of the aspect step (current text, no change). | `w <= 0` or `h <= 0` after the aspect step: refused. |
| The turned points | `cs` and `sn` of a finite rotation are finite. | A finite rotation only. | none | none |

### 2.4 Validation rules

The rules are renamed. Their text changes only in the method value.

- [ ] `V-pre.resize.affine_crop-1` If `input.resize.crop_policy.expand_ratio` is present, it must be a positive float. If `crop_policy.maintain_aspect_ratio` is present, it must be a boolean.
- [ ] `V-pre.resize.affine_crop-2` If `keypoint.estimator_type` is `top_down_single_person` or `top_down_multi_person`, the sidecar must declare `input.resize.method: affine_crop`.
- [ ] `V-pre.resize.affine_crop-3` Each size must declare `input.resize.target_size`. An `affine_crop` resize must not declare `pad_value`, `pad_position` or `rounding` (skellytracker ADR-90CE).

The old IDs `V-pre.resize.affine_person_crop-1` to `-3` go with the rename, as the IDs of
skellytracker ADR-88WQ did. No rule is new and no rule is deleted.

Other rules that name a changed value:

- `V-common.input-3`: the method value `affine_person_crop` becomes `affine_crop` (2.1). Changed.
- `V-node.detector-2` (pipeline spec): it names `keypoint.estimator_type`, not the method. Unchanged.
- No rule checks the ROI. The ROI is a host value, not a sidecar value.

### 2.5 Selectors

`input.resize.method=affine_crop`. It replaces `input.resize.method=affine_person_crop`. The selector
of `pre.resize.interpolation` changes in the same way (2.1).

### 2.6 Changelog row

The session that lands the change gives the row its number (the next row is 48 today).

```markdown
| 48 | Resize | `affine_person_crop` becomes `affine_crop`, and it crops an ROI `(c_x, c_y, w, h, rotation)` in source-image pixels. The rotation is in radians; a positive rotation turns the ROI clockwise in the image. A box `[x1, y1, x2, y2]` gives the ROI with rotation 0, in float32. `crop_policy` grows the ROI along its own axes. The second warp point, and for `maintain_aspect_ratio: false` the third, turn with the rotation, in float64, with one rounding to float32. For rotation 0, `M` does not change. Section ID `pre.resize.affine_person_crop` → `pre.resize.affine_crop`, file `pre/resize-affine-person-crop.md` → `pre/resize-affine-crop.md`; each rule ID, vector file and reference module follows (`V-pre.resize.affine_person_crop-2` becomes `V-pre.resize.affine_crop-2`). No alias. | the pipeline `roi` type ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 8); user decision 2026-11-12 ([ADR-<ID>](decisions/entries/<ID>-affine-crop-rotated-roi.md)) | [Affine crop](pre/resize-affine-crop.md#behaviour) |
```

## 3. Reference implementation

The follow-up rule gives "the base file plus the change, under the base module name"
("Proposal forms" in `specs/model-sidecar/model-addition-workflow/hand-over.md`). This file starts
from the landed file `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` ("Full
section" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`: the landed
file with the change). The landed file is the base file with the import of
`pre_resize_interpolation`. The module name follows the rename of 2.1, so the file is not under the
base module name. Part 8 gives the reason.

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/pre_resize_affine_crop.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_resize_affine_crop.py`. It replaces `specs/model-sidecar/reference/pre_resize_affine_person_crop.py`. |
| Functions (one for each algorithm) | `roi_from_box` (the ROI of a box), `roi_values` (the ROI values and the finite rule), `crop_size` (the expansion and the aspect step along the ROI axes), `warp_points` (the turned point pairs), `warp_matrix` (`M`), `policy_values`, `crop_geometry`, `border_value`, `warp_image`, `affine_crop` (the full forward step), `unproject` (the Inverse, no change), `check_rules` (the renamed rules -1, -2 and -3). Case functions: `run`, `inverse`, `border`, with `case_policy` and `case_roi`. |

Imports of other sections: `pre.resize.interpolation` (`pre_resize_interpolation`), as in the landed
file. The old function `affine_person_crop(image, bbox_xyxy, resize)` becomes
`affine_crop(image, roi, resize)`. A caller with a box gives `roi_from_box(bbox_xyxy)`.

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/pre.resize.affine_crop.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/pre.resize.affine_crop.yaml` (the renamed current file; 2.1) |
| `verified_against` | `unverified`: no host implementation of a rotated ROI exists. The case `roi-rotation-0-equals-box` gives the values of the current case `tall-box-grows-width`, which the OpenMMLab-Exporter host verifies. |
| `fill` | `fill` of `tools/make_vectors.py` at skellytracker `924c9773e48432a7ef7162b26942f69692615fbe` wrote `expect` with the file of part 3. |

The file holds only the new and the changed cases ("Proposal forms" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`).

New cases (12), each at the end of the landed file:

- `roi-rotation-0-equals-box`: an ROI with rotation 0. It gives the `expect` of `tall-box-grows-width`.
- `roi-quarter-turn` and `roi-quarter-turn-inverse`: rotation π/2.
- `roi-negative-rotation` and `roi-negative-rotation-inverse`: rotation -π/6, the branch `h = w / a`.
- `roi-rotation-aspect-ratio-not-kept` and `roi-rotation-aspect-ratio-not-kept-inverse`: rotation 1
  with `maintain_aspect_ratio: false`, the turned third point.
- `roi-half-turn` and `roi-half-turn-inverse`: rotation -π, the lower limit.
- `roi-expand-along-roi-axes`: growth along the ROI axes, rotation π/4.
- `roi-rotation-not-finite` and `roi-empty-crop`: `{error: no-rule}`. The ROI is a host value, not a
  sidecar value.

Changed cases (5). `land` gets them as `--replaces`. The reason for each one: the rename of the
method value and of the rule ID. The other keys do not change.

- `affine-crop-needs-target-size`
- `affine-crop-has-no-pad-position`
- `affine-crop-expand-ratio-is-positive`
- `affine-crop-maintain-aspect-ratio-is-boolean`
- `top-down-needs-affine-crop`

The 24 numeric cases of the current file do not change. Their `bbox_xyxy` input is still valid: a
box gives the ROI with rotation 0, and the file of part 3 gives their `expect` bit for bit (part 1,
"Measured difference", item (1), secondary). The rotated cases use the file tolerance `1e-4`,
because `cos` and `sin` can differ in the last bit between math libraries. No rotated case has a
pixel output.

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | G1 (pass gate): for rotation 0, the `M`, the centre and the crop size of part 3 equal those of the landed reference file bit for bit, on the boxes of the run of OpenMMLab-Exporter ADR-6A8S. Source: 2.3, the note "For rotation 0". G2 (pass gate): on each box of G1 with 8 rotations (`-π`, `-3π/4`, ..., `3π/4`) and with both values of `maintain_aspect_ratio`, the `M` of part 3 equals the `M` of mmpose v1.3.2 `get_warp_matrix` with `rot = degrees(r)`, bit for bit. Source: 2.3, the last paragraph of Behaviour. G3 (pass gate): on the same OpenCV build, the crop of part 3 equals the crop of mmpose `TopdownAffine` with `bbox_rotation`, max abs diff 0. Source: the same `M` and the same `cv2.warpAffine` call. G4 (control): the final RTMW keypoints of the sidecar path on rotated crops, compared with mmpose `TopdownAffine` with `bbox_rotation` and the same model, with the gate G5 of the RTMW parity run (OpenMMLab-Exporter ADR-0053). |
| Test images (paths or dataset IDs), and the branch that each image runs | The 10 COCO val2017 images and the 49 persons of the RTMW parity run (OpenMMLab-Exporter `decisions/scripts/rtmw_parity.py`). Each person runs each rotation of G2 and both aspect branches. |
| Upstream reference: library, version, config and command | mmpose 1.3.2 in the published exporter Docker image of OpenMMLab-Exporter, the RTMW configs of `mmdeploy-convert/model_cfgs/`, `TopdownAffine` with `bbox_rotation` in the data sample. The command is to be written. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run. The rotation does not change the graph. The export error of the RTMW parity run applies (OpenMMLab-Exporter ADR-0053). |
| Preprocessed input: maximum absolute difference for each image | to run (G3) |
| Row count for each image: sidecar path and upstream | to run |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | to run (G4: the RTMW keypoints and scores) |
| Result (`pass`, `fail` or `to run`) | `to run`. For rotation 0, the text gives the current `M` bit for bit, so the current parity of the RTMW sidecar path stays valid (Implementer guidance of the current section, the bullet on the committed parity script). |
| Script path in the exporter repo | `decisions/scripts/affine_crop_rotated_check.py` (planned; not written) |
| Exporter commit of the script | unknown (the script is not written) |
| Command | to run |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | The N2 module of the implementation plan (`specs/sidecar-implementation-plan.md`, N2), renamed: `skellytracker/core/detectors/processing/pre/resize_affine_crop.py` in place of `pre/resize_affine_person_crop.py`. Port it from `specs/model-sidecar/reference/pre_resize_affine_crop.py`: `roi_from_box`, `crop_size`, `warp_points`, `warp_matrix`, `affine_crop` and `unproject`. |
| Dispatch point | The resize dispatcher of N2, on `input.resize.method: affine_crop`. The pipeline `detector` node gives each present row of its `rois` input as `(c_x, c_y, w, h, rotation)`. The exact call site in the pipeline runner is for the implementer: the pipeline API is in work at the commit that this proposal read. |
| Validator changes (`model.py`, with rule IDs) | The new spec model of N1: the enum value `affine_crop` in `V-common.input-3`; the rules `V-pre.resize.affine_crop-1`, `-2` and `-3` with the new IDs. No new rule. The old loader `skellytracker/core/sidecar/model.py` (`CropPolicySpec`, `SidecarModel._check_pose_requires_affine_crop`) does not change: it is replaced (skellytracker ADR-AMJ8). |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | Add the new module to `PACKAGE_RUNNERS` in `tools/tests/test_vectors.py` for `pre.resize.affine_crop`: the numeric cases, with `bbox_xyxy` and `roi` inputs. The golden test of the base proposal (the three COCO cases) stays. |
| Existing code that the change touches | None of the old code. `skellytracker/core/detectors/processing/affine_crop.py::get_warp_matrix` has a `rot` argument, but it turns `[0, src_w * -0.5]`, a point above the centre (the rtmlib form), and `top_down_affine` always gives `0.0`. Do not reuse it for the rotated crop. `skellytracker/core/detectors/processing/image_preprocessing.py::preprocess_image` keeps its `affine_person_crop` branch for the old package sidecars until N2 replaces it. |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` | regenerate: `input.resize.method: affine_crop`. The next export already regenerates for the names of skellytracker ADR-88WQ and ADR-GKD1. | The method string and the rule ID: [`rtmw/sidecar.py:135`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/rtmw/sidecar.py#L135), [`rtmw/preprocess.py:32`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/rtmw/preprocess.py#L32), [`rtmw/adapter.py:48`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/rtmw/adapter.py#L48), [`onnx_runtime/preprocess.py:449-463`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/onnx_runtime/preprocess.py#L449-L463), [`onnx_runtime/unprojection.py:55`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/onnx_runtime/unprojection.py#L55) and the vector runner [`pipeline/handover.py:839`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/pipeline/handover.py#L839). The RTMW boxes have rotation 0, so the host does not need the rotation. The host can add the ROI input later. |
| OpenMMLab-Exporter | `rtmpose-halpe26`, `dwpose-wholebody133-ubody` | none now. Their sidecar spec is pending, and they write no sidecar. Their declared values change to `affine_crop` with the next sidecar work ([`rtmpose/preprocess.py:32`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/rtmpose/preprocess.py#L32), [`dwpose/preprocess.py:32`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/2c554cb817ec1cce82af0c97f46e96eef15e3cb6/dwpose/preprocess.py#L32)). | none |
| MediaPipe-Exporter | the Holistic hand landmark model | new fields later: it can declare `affine_crop` for its rotated ROI. It still needs the border change (part 8). Not in the spec scope today. | none (no sidecar writer for this model) |
| Ultralytics-Exporter, Roboflow-Exporter | all | none. They write no top-down crop. | none |

**Reference examples that the change makes invalid.**

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit`, `needs-export` or `removed (user ruling)`) | Edit text |
|---|---|---|---|
| `detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml` | `V-common.input-3`, `V-pre.resize.affine_crop-2` | `forced-edit` | `input.resize.method: affine_person_crop` becomes `input.resize.method: affine_crop`. The change gives the value. |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none. No host code writes the proposed value yet. |
| Writer code (file, function and commit) | none |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep `affine_person_crop` with rotation 0, and give the pipeline a box around the rotated ROI | The crop then holds the content turned by the ROI rotation, and the model sees a turned hand. The keypoints change by up to the ROI size (265.2 px in part 1). The box around a turned ROI is also larger, so the model scale changes. | Part 1, "Measured difference" |
| Rename only the file, and keep the section ID and the method value | A file `resize-affine-crop.md` with the ID `pre.resize.affine_person_crop` gives one concept two names. skellytracker ADR-88WQ item 2 makes the IDs, the rule IDs and the vector and reference file names follow the layout, and it rejects "New titles with the old IDs and file names". The section ID of each other resize method equals its method value. `person` is wrong for a hand ROI or a face ROI. | skellytracker ADR-88WQ |
| A second method, for example `affine_roi_crop`, beside `affine_person_crop` | Two methods with one algorithm. A box is an ROI with rotation 0 (skellytracker ADR-7NY2 item 8). `V-pre.resize.affine_crop-2` would need two values. | skellytracker ADR-7NY2 item 8 |
| A sidecar field for the rotation (`crop_policy.rotation`) | The rotation is a property of each ROI, not of the model. | Pipeline `roi` type, heading "Behaviour" of `specs/pipeline/graph.md`, item 3 |
| The rotation in degrees, as mmpose | The pipeline spec and MediaPipe use radians. | Part 1, upstream evidence (2); skellytracker ADR-7NY2 item 8 |
| The turned points in float32 (the MediaPipe form), or a closed-form `M` from the scale and the angle | For rotation 0, neither form keeps the current `M` bit for bit for each box, so the current vectors and the RTMW parity would need a new check. The float64 form of mmpose keeps them, and it gives the mmpose `M` for a rotated ROI. The MediaPipe crop also maps the ROI by its corners, so its pixels differ for another reason. | Part 1, "Measured difference" (secondary); 2.3, Guidance |
| `crop_policy` grows the box around the turned ROI in image axes | The pipeline order needs the growth along the ROI axes, so that the two factors multiply. mmpose scales along the ROI axes. | `specs/pipeline/nodes/detector.md`, item "Crop"; mmpose `get_warp_matrix` |
| A border mode with edge pixels (`crop_policy.border_mode`) in this proposal | It is a separate contract unit: the user can accept the rotated crop without it ("Proposal forms" in `specs/model-sidecar/model-addition-workflow/hand-over.md`). No model in the spec scope needs it. Its evidence is secondary only (MediaPipe-Exporter docs). The spec defect stays open (2.1). | `specs/model-sidecar/decisions/open-work.md`, "Spec defects" |
| The reference file under the base module name `pre_resize_affine_person_crop` (the follow-up rule) | The module name must follow the new section ID ("Module names" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`; skellytracker ADR-88WQ item 2). A file under the old name would land as a second module for one section. | 2.1, the rename table |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal. n/a: no `model` bundle. The request came from the skellytracker spec session for the pipeline spec.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 2 gives the behaviour of each new step on NaN, on inf, on a tie and on an empty input.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Each case with a partial input in part 4 names in its `note` the rules that it checks.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. n/a: `to run`.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] Each citation of upstream code or of the code of another repo is a permalink with a full 40-character SHA.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
