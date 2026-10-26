---
slug: affine-crop-arithmetic
section: pre.resize.affine_person_crop
exporter: OpenMMLab-Exporter
decision: "0037"
state: recorded
---
# Change proposal: affine-crop-arithmetic

This file is informative. It is not part of the normative spec until a content PR lands its text
in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `affine-crop-arithmetic`, at
OpenMMLab-Exporter commit
[`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1),
copied on 2026-10-25. Part 3 also holds the code of the OpenMMLab-Exporter reference file of part 3, copied on the same
date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote
no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`. No skellytracker decision entry covers this property.

## Header

| Field | Value |
|---|---|
| Title | Affine person crop arithmetic: the order of the operations, the float32 values, the warp points, the Inverse, and a mode for the ViTAE / mmpose 0.x `_xywh2cs` arithmetic |
| Slug | `affine-crop-arithmetic` |
| Date | 2026-10-23; updated 2026-10-25 (re-pinned to skellytracker `dom/21-move-sidecar-guide`; the `open-work.md` lines; rule -3 fails only for `maintain_aspect_ratio: false`, in the code and in each sentence; one new `check_rules` case; repo names on each decision number) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed: OpenMMLab-Exporter decision 0050; OpenMMLab-Exporter decision 0042 is commit `1dfec48`; `git status --porcelain` is empty). First written at `d0f4343`. `rtmw/preprocess.py` is the same at `d0f4343`, at `01d9b3d`, at `1dfec48` and at `f3aeb47` (checked again on 2026-10-24). This proposal cites no host code of the exporter, because no host code for this section exists (`rtmw/preprocess.py:12, 32-34` only declares the values). |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)), `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)), `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts)) and `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). The user decision T21 (2) asks for this proposal for the T4b rows of these four intakes (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The intake correction of 2026-10-24 also links it from row D11 (the Inverse) of these four intakes and from rows T4b and D11 of `rtmw-wholebody133` (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)). |
| Intake rows with the verdict `near-miss` or `gap` | Row T4b (arithmetic) of the four intakes: the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts). All four rows are `near-miss`. The DWPose and Halpe26 rows were `unverified`, with the gates of parity step 4 and step 5. Part 1 gives the numbers that make them `near-miss`: the current text gives other crop pixels than mmpose in 1911 of 2000 crops. The T21 follow-up applied this verdict in both intakes (part 7; checked by the review-readiness audit of 2026-10-23). Row D11 (unprojection, the Inverse) of each intake is `near-miss` (secondary; intake correction of 2026-10-24): `dwpose:122`, `halpe26:142`, `vitposepp:138`, `coco25:151`. The reason: the current Inverse is the inverse of `M`, but mmpose and ViTAE use a closed form, and the inverse of `M` differs from the mmpose closed form by up to 7.3e-5 px (part 1 (3)). Also rows T4b and D11 (both `near-miss`) of the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (lines 149 and 177; intake written 2026-10-24): the RTMW family uses the default `direct`, so it needs no new field, but the section text changes for it (part 7). |
| Kind (`new section` or `changed section`) | `changed section` |
| Proposed section ID (the `id` in the section file's front matter) | `pre.resize.affine_person_crop` |
| Section file | `specs/model-sidecar/pre/resize-affine-person-crop.md` |
| Depends on (proposal files that must land first, or `none`) | none. **Related (not a dependency):** the MediaPipe-Exporter proposal `roi-transform-and-source` (MediaPipe-Exporter `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`, the full proposal of skellytracker 0020, updated 2026-10-24). By user decision T22 (1) (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), section 2.1, secondary) it removes `pose.requires_object_detector` from the spec. It gives the new text of `V-pre.resize.affine_person_crop-2`: "**(vNEXT)** If `pose.estimator_type` is `top_down_single_person` or `top_down_multi_person`, `input.resize.method` must be `affine_person_crop` or `rotated_roi_crop`. If `pose.estimator_type` is `bottom_up`, `input.resize.method` must not be `affine_person_crop` or `rotated_roi_crop`." (its part 2.4, lines 485-495). The legacy text of the rule goes to the new heading "Legacy behaviour" of `post.pose.schema` (its part 2.6, lines 543-548). This proposal does not change rule -2, and it does not restate it (2.4). Its `check_rules` checks only `-1` and `-3` (part 3). Why it is not a dependency: no rule, function or vector of this proposal reads `pose` or names `rotated_roi_crop`. Thus either proposal can land first. Three places overlap, and the content PR that lands second must rebase on the first: (1) "Validation rules" of the section file: that proposal changes line 66 (`-2`), and this proposal adds `-3` after it. (2) "Behaviour": that proposal changes the sentence "Rotated crops are out of scope." (line 41, its 2.1 row at line 173). This proposal replaces "Behaviour" with the text of 2.3, which has the same sentence. The second PR keeps the text of that proposal for this sentence. (3) `V-common.input-4`: that proposal makes the keys of an `affine_person_crop` `crop_policy` a closed set, `expand_ratio`, `maintain_aspect_ratio` and `pad_value` (**(vNEXT)**; its part 2.4, lines 456-459). This proposal adds `crop_policy.arithmetic`. If both land, the set must also contain `arithmetic`. Otherwise each `vNEXT` sidecar with `arithmetic` fails `V-common.input-4` (2.1, row `common.input`). Line numbers into that file are of 2026-10-24 11:25 (file time); another session edits it. |
| Needed by (proposal files that depend on this one, or `none`) | none. Related: `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md` (slug `normalize-arithmetic`) edits the same sentence of `format/versioning.md:51`. The two proposals share one exception sentence (2.1, row `format.versioning`, in both files). The skellytracker session adds it one time. `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md` maps heatmap cells to model-input pixels; this proposal gives the next step (the Inverse). One parity script can serve the three proposals (part 5). **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide` (checked 2026-10-25). From `dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`, no file of this list under `specs/` or `tools/` changed. From `dom/18-agents-adr-bootstrap-kit` to `dom/21-move-sidecar-guide`, two files of this list changed: `templates/model-intake.md` (one link in the header paragraph, line 5; the line count is the same; row T4b stays at line 264) and `notes/decisions/open-work.md` (five lines added above "Spec defects"; the item at the old line 163 is at line 168, the item at the old line 166 is at line 171, and the scalar `pad_value` item is at lines 141-147). `tools/make_vectors.py` and `tools/tests/test_vectors.py` did not change. The "Open work" list moved from `notes/decisions/README.md` to `notes/decisions/open-work.md` (`dom/14-decision-log-growth`), so the old `README.md:199` was `open-work.md:163` at `dom/18-agents-adr-bootstrap-kit` and is `open-work.md:168` at `dom/21-move-sidecar-guide`. `format/versioning.md:51` (the shared exception sentence; add it one time): `normalize-arithmetic`; `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `simcc-score-rule`, `heatmap-decode-refinement`, `model-id-suffix`, `size-codes`, `roi-transform-and-source` (MediaPipe-Exporter); `common/input.md:61` (`V-common.input-4`: `arithmetic` joins the closed `crop_policy` key set): `roi-transform-and-source` (MediaPipe-Exporter); `pre/resize-affine-person-crop.md:39-53` and `:63-68` ("Behaviour" with the sentence "Rotated crops are out of scope." at `:41`; "Validation rules" `-2` and `-3`; `roi-transform-and-source` owns `V-pre.resize.affine_person_crop-2`): `roi-transform-and-source` (MediaPipe-Exporter); `pre/resize-affine-person-crop.md:70-74` ("Implementer guidance": the flip-test bullet at `:72`, new bullets): `pose-decode-flip-test`; `pre/resize-affine-person-crop.md:76-81` ("Authoring guidance"): `roi-transform-and-source` (MediaPipe-Exporter); `templates/model-intake.md:264` (row T4b): `roi-transform-and-source` (MediaPipe-Exporter); skellytracker `notes/decisions/open-work.md:168` ("Spec defects"): `normalize-arithmetic`; `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `model-id-suffix`, `size-codes`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index lists the `proposed` entries 0017 to 0025 (skellytracker `notes/decisions/README.md:36-44`). 0020 (ROI transform) is about rotated crops and crops that do not come from a detector box. It does not cover the arithmetic. The open-work file (`notes/decisions/open-work.md`, "Spec defects") names three related items. Item 1 is "the arithmetic precision of the geometry and of the pixel math" (`open-work.md:168`). Item 2 is the scalar `pad_value` of `affine_person_crop` (`:141-147`). Item 3 is "the box format and the coordinate space of the person box that `affine_person_crop` warps" (`:171`). (Lines at `dom/21-move-sidecar-guide`; at `dom/18-agents-adr-bootstrap-kit` they were 163, 136-142 and 166.) This proposal closes items 1 and 2 for this section. It does not close item 3. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (`git status --porcelain` lists only an untracked `grep.exe.stackdump`, a crash dump that this proposal did not read). First read at `dom/12-single-working-branch`, then pinned at `dom/18-agents-adr-bootstrap-kit` (at `dom/18-agents-adr-bootstrap-kit` on 2026-10-24: only `exporter-guide.md` had changed, one line less after line 445, and the cited decision-log lines had moved to `notes/decisions/open-work.md`). The cited `specs/`, `tools/` and `skellytracker/` lines were checked again at `dom/21-move-sidecar-guide` on 2026-10-25: no cited line changed. Between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide` the guide moved to `specs/exporter-guide/sidecars/` (skellytracker decisions 0033 and 0034), only link text changed under `specs/model-sidecar/`, and the cited items of `notes/decisions/open-work.md` moved by 5 lines (the header rows above and 2.1 give the new lines). Guide citations point to the 0034 layout. |

**Decision of this proposal.** The section gets a normative heading "Arithmetic". It gives the order
of the operations and the float32 value of each step. The steps are the centre, the crop size, the
three warp point pairs and `M`. With these steps a host gives the same crop pixels as mmpose 1.x (measured: 0 of
2000 crops differ, part 1). The Inverse uses a closed form with the crop width and the crop height.
It does not use the inverse of `M`. A new field `crop_policy.arithmetic` selects between two
arithmetic forms: `direct` (the default, mmpose 1.x: RTMPose, RTMW, DWPose) and `pixel_std_200`
(the ViTAE / mmpose 0.x `_xywh2cs` arithmetic: ViTAE ViTPose and ViTPose++). One text cannot
describe both. The later mmpose 0.x step `TopDownGetBboxCenterScale` (`bbox_xywh2cs`) matches
neither value (2.3, "Guidance"; decided item A4). The ViTAE crop differs from
the `direct` crop in 1280 of 2000 crops. With `pixel_std_200` it differs in 0 of 2000 crops.

**Version scope: every `schema_version`.** The user decided for the sibling proposal
`normalize-arithmetic` that its arithmetic rule applies to every `schema_version` (option B). The
reason: no sidecar is deployed yet, and all sidecars will be made again (user decision T21 (3),
2026-10-23, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). This proposal follows that user decision
with the same reason. The heading "Arithmetic" and the Inverse apply to every `schema_version`. Only
the new field `crop_policy.arithmetic` is `vNEXT`. Rule -3 rejects it in a legacy sidecar (2.4,
2.6; decided item A3). The proposal `normalize-arithmetic` has the same scope. The two proposals
share one exception sentence for `format/versioning.md:51` (2.1, row `format.versioning`).

**Decided items (user, plan T23, 2026-10-24).** The numbers A1 to A4 are the numbers of the plan
(the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; T23 at the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The user
decided each item as this proposal recommends. Thus the normative text of part 2 does not change:

- A1: add the field `crop_policy.arithmetic` with the values `direct` and `pixel_std_200`.
- A2: keep the single-`pad_value` rule ("A scalar `pad_value` fills every channel") in this
  proposal.
- A3: option 1. Reject the field below `vNEXT`.
- A4: option 1. No value for the mmpose 0.x form `bbox_xywh2cs` now.

The text below is the record of the items and their options, as the user saw them.

- A1. The new field `crop_policy.arithmetic` with the value `pixel_std_200`. This proposal adds it,
  because parity step 4 expects 0 (`exporter-guide/sidecars/workflow/parity.md:28-32`) and the guide does not allow a
  larger tolerance (`exporter-guide/sidecars/workflow/phase-1-intake.md:67`). The alternative is one text for all models: then the
  two ViTPose rows T4b stay `near-miss` (part 8, row 3). The effect of the 1-level pixel
  differences on the ViTPose heatmaps is not measured.
- A2. The sentence "A scalar `pad_value` fills every channel" (2.3). The reference implementation
  needs one meaning for a scalar, and the decision log says that the spec must state it
  (skellytracker `notes/decisions/open-work.md:141-147`). It changes only this section. `fit` keeps the
  defect. The other choice was to split it into its own change. The user keeps it here (A2).
- A3. The rule `V-pre.resize.affine_person_crop-3` rejects `crop_policy.arithmetic` in a sidecar
  with `schema_version < vNEXT`. It also rejects the value `direct` there (part 4, case
  `rule3-legacy-sidecar-must-not-have-arithmetic`). This is the form of `V-common.input-3`, which
  marks single values as **(vNEXT)** (`common/input.md:60`).
  - Option 1 (this proposal): reject the field below `vNEXT`. A valid legacy sidecar has no field,
    so `direct` applies, and the forward step and the Inverse need no `schema_version` (2.4). A
    legacy sidecar that has the field does not load.
  - Option 2: ignore the field below `vNEXT`, and use `direct`. Rule -3 then has the
    **(vNEXT)** mark and checks the value only at `vNEXT`. The forward step must then read
    `schema_version`. A legacy sidecar with `arithmetic: pixel_std_200` loads, but it gets the
    `direct` crop with no error (1280 of 2000 crops differ, part 1).
- A4. No value for the mmpose 0.x form `bbox_xywh2cs` of the step `TopDownGetBboxCenterScale`. It
  calculates `f32(w) / 200`, and `pixel_std_200` calculates `f32(w / 200)` (2.3, "Guidance"; mmpose
  v0.29.0 `mmpose/core/bbox/transforms.py:64`). The crop size differs in 235 and 250 of 2000 boxes,
  and the crop pixels in 183 and 200 of 2000 boxes (256 x 192 and 384 x 288). No model in scope uses
  this step: the four intakes use mmpose 1.x or the ViTAE `_xywh2cs` (part 1).
  - Option 1 (this proposal): no value now. A model with this step is a `near-miss` (2.3,
    "Guidance"). A later proposal adds a third value when a model needs it. The case
    `pixel-std-200-is-not-the-mmpose-029-scale` of part 4 already separates the two forms.
  - Option 2: add a third value now (for example `pixel_std_200_box_f32`), with its own steps in
    2.3, its own vectors and an upstream run of mmpose 0.x. No exporter writes it yet.

## 1. Gap

| Item | Value |
|---|---|
| Property | The arithmetic of the top-down affine crop and of its inverse: (a) the order of the operations and the dtype of the centre, the crop size and the warp points; (b) which of `w` and `h` the forward warp uses; (c) how the inverse uses `h`. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **mmpose v1.3.2** (RTMPose, RTMW, DWPose; fetched from `raw.githubusercontent.com/open-mmlab/mmpose/v1.3.2/`). `mmpose/structures/bbox/transforms.py:66-67` (`bbox_xyxy2cs`: `scale = (x2y2 - x1y1) * padding`, `center = (x2y2 + x1y1) * 0.5`, no cast: the dtype of the box). `mmpose/datasets/transforms/common_transforms.py:52, 76-80` (`GetBBoxCenterScale`, `padding=1.25`). `mmpose/datasets/transforms/topdown_transforms.py:67-70` (`_fix_aspect_ratio`: `np.where(w > h * aspect_ratio, [w, w / aspect_ratio], [h * aspect_ratio, h])`), `:85-90` (`aspect_ratio=w / h` of `input_size`, a Python float), `:108` (`get_warp_matrix(center, scale, rot, output_size=(w, h))`), `:117-118` (`cv2.warpAffine(..., flags=cv2.INTER_LINEAR)`), `:133-135` (metainfo `input_size`, `input_center`, `input_scale`). `mmpose/structures/bbox/transforms.py:406-424` (`get_warp_matrix`: `src_dir = _rotate_point([src_w * -0.5, 0.])` in float64 (line 411); `src` and `dst` are float32 arrays (lines 414, 418); `src[1] = center + src_dir` (line 416); the third points come from `_get_3rd_point` (lines 422-424, 509-525) when `fix_aspect_ratio=True`; the `fix_aspect_ratio=False` branch uses `src_h` (lines 425-429)), `:431-434` (`cv2.getAffineTransform(np.float32(src), np.float32(dst))`). The forward warp uses only `scale[0]` (`src_w`, lines 407, 411). `mmpose/models/pose_estimators/topdown.py:150-156` (the inverse: `keypoints / input_size * input_scale + input_center - 0.5 * input_scale`, with `w` and `h` of the scale). `mmpose/codecs/utils/post_processing.py:92` (the SimCC keypoints are float32, so line 154 of `topdown.py` stores the float64 result as float32). The box dtype: float32 for the GT boxes (`mmpose/datasets/datasets/base/base_coco_style_dataset.py:290`) and the detection boxes (`:453-455`); `np.array(bboxes)` of the caller in `inference_topdown` (`mmpose/apis/inference.py:169-170`). **ViTAE-Transformer/ViTPose `c050ed29112da7704797cc1a65af0234b525010d`** (mmpose 0.x; the ViTPose and ViTPose++ eval pipelines; fetched from `raw.githubusercontent.com`, and the copy of the intakes is equal). `mmpose/datasets/datasets/top_down/topdown_coco_dataset.py:204, 210` (the detection box `[x, y, w, h]` from the JSON file, Python floats, into `_xywh2cs`). `mmpose/datasets/datasets/base/kpt_2d_sview_rgb_img_top_down_dataset.py:143-145` (`aspect_ratio = image_size[0] / image_size[1]`; `center` float32 from `x + w * 0.5`), `:150-153` (the aspect fix on the box before the expansion, float64, with strict `>` and strict `<`), `:156` (`scale = np.array([w / 200.0, h / 200.0], dtype=np.float32)`), `:158` (`scale * padding`, float32). `mmpose/core/post_processing/post_transforms.py:226` (`scale_tmp = scale * 200.0`, float32), `:229` (`src_w = scale_tmp[0]`), `:234-235` (`src_dir = rotate_point([0., src_w * -0.5])`: the second point is above the centre), `:237-245` (float32 `src` and `dst`), `:250` (`cv2.getAffineTransform`), `:288` (`_get_3rd_point` in float32), `:180-192` (`transform_preds`: `scale * 200.0`, `scale_x = scale[0] / W`, `x * scale_x + center[0] - scale[0] * 0.5`). `mmpose/datasets/pipelines/top_down_transform.py:230-236` (the non-UDP `TopDownAffine`: `get_affine_transform`, then `cv2.warpAffine(..., flags=cv2.INTER_LINEAR)`). |
| Nearest section ID (the `id` in the section file's front matter) | `pre.resize.affine_person_crop` |
| Why the nearest section is wrong | The pseudocode (`specs/model-sidecar/pre/resize-affine-person-crop.md:44-50`) is exact math. It gives no dtype. Its aspect fix multiplies, `h = w * (T_h / T_w)` (line 47); mmpose divides, `h = w / (T_w / T_h)`. It defines `M` as "the affine map taking the (w, h) box around center onto [0, T_w] x [0, T_h]" (line 49). Thus `M` uses `h`. mmpose builds `M` from three float32 points that use only `w`. The Inverse is "the inverse of the affine warp `M`" (line 61). mmpose uses a closed form with `h` (`topdown.py:154-156`). The section also claims "This matches mmpose `GetBBoxCenterScale(padding=1.25)` + `TopdownAffine`" (line 53). That holds in exact math only. The section has no form for the ViTAE / mmpose 0.x `_xywh2cs` arithmetic. A detail that the spec does not define, and that changes the output for some input, is a `near-miss` (`exporter-guide/sidecars/workflow/phase-1-intake.md:26-29`; `templates/model-intake.md:110, 264`). |
| Measured difference (number, image and script) | **(1) The aspect fix, 1 ulp** (scratch `ulp_count.py`, NumPy 2.5.4). The values are `w = 0.37 * k`, `k = 1 ... 200000`. `w * (T_h / T_w)` and `w / (T_w / T_h)` differ by 1 ulp for 66665 values in float32 and 66658 values in float64. That is for `T = 256 x 192` and `384 x 288`; for `256 x 256` the count is 0. Example: `w = 5.55` gives 7.4000006 and 7.4 in float32. These are the numbers of the DWPose intake (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)). **(2) The crop pixels** (scratch `compare_forms.py`, NumPy 2.5.4, OpenCV 5.0.0). The script uses copies of the upstream lines cited at the left. It uses 2000 random float32 boxes (seed 0, 1163 wide and 837 tall), a random uint8 image 480 x 640 and `INTER_LINEAR`. The current text in float64 against mmpose: a pixel differs in 1911 of 2000 crops (256 x 192) and in 1910 of 2000 crops (384 x 288). The difference is at most 1. `M` differs by up to 0.0041 and 0.0062. The current text in float32: 1897 and 1895 crops. The proposed `direct` text against mmpose: 0 of 2000 crops, `M` equal (difference 0), the centre, the crop size and the six points equal. The proposed `direct` text with `maintain_aspect_ratio: false` against mmpose `get_warp_matrix(fix_aspect_ratio=False)`: 0 of 2000. ViTAE against the `direct` text: 1280 and 1278 crops, `M` up to 0.0031 and 0.0047. The proposed `pixel_std_200` text against ViTAE: 0 of 2000, `M` equal. The skellytracker code (a copy of `affine_crop.py:21-109`) against the `direct` text: 1092 crops with a float32 box and 1516 crops with a float64 box. In that code the second point is above the centre, as in rtmlib. `M` solved with `numpy.linalg.solve` in place of `cv2.getAffineTransform`: `M` differs by up to 1.8e-11, and 4 and 5 of 2000 crops differ by 1 in a pixel. In 1704 of 2000 crops the x scale and the y scale of the mmpose `M` differ, because the float32 points round. **(3) The Inverse**: the closed form of 2.3 against mmpose `topdown.py:154-156` on 17 random points per crop: 0 of 68000 float32 values differ. The closed form against the inverse of `M`: up to 7.3e-5 px. The `pixel_std_200` closed form against ViTAE `transform_preds` (NumPy 2.5.4, heatmap cells x 4): up to 1.6e-4 px. ViTAE calculates in float32 there. The part 5 gate for this difference is in ulp at the intermediate values, not at the result. The scratch scripts are in the session scratchpad. They are not committed, so the numbers are not evidence (secondary). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The row `crop_policy.border_mode`, rotated crops (`changelog.md:45`) is about other features. This proposal adds no border mode and no rotation. |

**Missing primary evidence.** (1) The upstream code did not run. The numbers come from copies of the
upstream lines in NumPy 2.5.4. The mmpose 1.x lines do array operations and explicit float32 arrays,
so NumPy 1.x gives the same dtypes. That is a reading, not a run. Part 5 runs mmpose v1.3.2 in the
exporter image and ViTAE in `/opt/vitae` (plan T12). (2) No ONNX file of the four families exists in
this exporter yet. The effect on keypoints is not measured. (3) The ViTAE inverse dtype depends on the
NumPy version (scalar operations at `post_transforms.py:186-192`). The measured 1.6e-4 px uses
NumPy 2.5.4.

## 2. Spec change

### 2.1 Sections

Changed section `pre.resize.affine_person_crop`, title "Affine person crop", file
`specs/model-sidecar/pre/resize-affine-person-crop.md`. The section ID, the title, the kind and the
selectors do not change. One new field: `input.resize.crop_policy.arithmetic`.

Changed front matter (the other keys do not change):

```yaml
changed_in: [vNEXT]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CropPolicySpec  # partial. No crop_policy.pad_value and no crop_policy.arithmetic field. SidecarModel._check_pose_requires_affine_crop checks V-pre.resize.affine_person_crop-2.
  forward: skellytracker/core/detectors/processing/affine_crop.py::top_down_affine  # partial. Always uses cv2.INTER_LINEAR and no pad_value. preprocess_image raises when maintain_aspect_ratio is false. The arithmetic takes the dtype of the box, and the second warp point is above the centre (the rtmlib form), so the direct arithmetic is not met. No pixel_std_200.
  inverse: skellytracker/core/detectors/processing/simcc_decode.py::decode_simcc  # partial. Applies the closed form of the Inverse to SimCC keypoints only.
```

No row in the section map changes (`specs/model-sidecar/README.md:67`).

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.resize.affine_person_crop` | front matter (lines 1-19) | The edit above. |
| `pre.resize.affine_person_crop` | "Fields" (lines 31-35) | Add the row `crop_policy.arithmetic` of 2.2. In the row `crop_policy.pad_value` (line 35), add "A scalar fills every channel." |
| `pre.resize.affine_person_crop` | "Behaviour" (lines 39-53) | Replace with the text of 2.3. Line 53 ("This matches mmpose ...") becomes the last paragraph of 2.3. |
| `pre.resize.affine_person_crop` | "Inverse" (lines 55-61) | Replace with the Inverse of 2.3. |
| `pre.resize.affine_person_crop` | "Validation rules" (lines 63-68) | Add `V-pre.resize.affine_person_crop-3` (2.4). No edit of `-2` (line 66) by this proposal. The proposal `roi-transform-and-source` changes it (header, row "Depends on"). |
| `pre.resize.affine_person_crop` | new heading "Legacy behaviour", after "Validation rules" | The table of 2.6. The section has no such heading now. |
| `pre.resize.affine_person_crop` | "Implementer guidance" (lines 70-74) | Add the bullets of 2.3, "Guidance". |
| `pre.resize.affine_person_crop` | "Authoring guidance" (lines 76-81) | Add the bullets of 2.3, "Guidance". |
| `post.unprojection` (`post/unprojection.md`) | "Behaviour" (line 36) | No edit. The link to the Inverse stays. |
| `common.input` (`common/input.md`) | "Fields" (line 48), "Validation rules" (lines 61-62) | No edit. `V-common.input-4` keeps `crop_policy` to `affine_person_crop`. `V-common.input-5` already checks the shape of `crop_policy.pad_value`. If the proposal `roi-transform-and-source` lands, its changed `V-common.input-4` has a closed key set for an `affine_person_crop` `crop_policy` (`expand_ratio`, `maintain_aspect_ratio`, `pad_value`). Then add `arithmetic` to that set. The content PR that lands second does this edit. |
| `format.versioning` (`format/versioning.md`) | "Version-aware compatibility" (lines 49-63) | Line 51 says "`vNEXT` requirements never apply retroactively". Add this sentence after it: "Exception: the heading "Arithmetic" and the rule `V-pre.normalize-3` of Normalization (`../pre/normalization.md#arithmetic`) and the headings "Arithmetic" and "Inverse" of Affine person crop (`../pre/resize-affine-person-crop.md#arithmetic`) apply to every `schema_version`." This proposal and `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md` (2.1, row `format.versioning`) share this one sentence, with the same text. Add it one time. If only one of the two proposals lands, remove the part of the other. The sentence does not cover a field or a rule that has the **(vNEXT)** mark, for example `crop_policy.arithmetic` (rule -3). Add the link `- [Affine person crop](../pre/resize-affine-person-crop.md#legacy-behaviour)` to the list (lines 53-63). |
| `specs/model-sidecar/README.md` | section map (line 67); validation index (line 110) | No edit. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" (lines 16-36) | Add the row of 2.7. |
| `specs/model-sidecar/changelog.md` | "`schema_version` history", `vNEXT` row (line 68) | Append the sentence of 2.7. Do not add a second `vNEXT` row. |
| `specs/model-sidecar/changelog.md` | "Compatibility impact" (lines 55-59) | Add the bullet of 2.7. |
| `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml` | existing file | Add the 28 new cases of part 4 (27 before 2026-10-25). Do not add the 15 transcribed cases: they are the existing cases in the template form. The 7 existing cases keep their values: they pass at their tolerance 1e-4 (part 4). Do not edit the file by hand: it comes from `tools/make_vectors.py` (header line 2). |
| `specs/model-sidecar/vectors/post.unprojection.yaml` | existing file, cases `pixel-affine-person-crop` (line 185) and `normalized-11-affine-person-crop` (line 198) | No value changes. The file comes from the generator. |
| `tools/make_vectors.py` | `affine_crop` (lines 911-933), `affine_unproject` (lines 936-940), `build_affine_person_crop` (lines 943-1047), the `affine_person_crop` branch of the unprojection (lines 2030-2037), `ROUND_DIGITS` (line 62) | For the skellytracker session. `affine_crop` must use the float32 steps and the points of 2.3. `affine_unproject` must use the closed form with `crop_w` and `crop_h`, not the inverse of `M`. The new cases need the exact float32 values: a rounding to 6 decimals (`ROUND_DIGITS`) removes the 1-ulp differences that the cases test. Write each value with the shortest text that gives the same float64 value. Add the `check_rules` and `affine_person_crop` cases with their own expect keys (`failed`, `image`). |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (lines 32-40) | The part 4 cases have `function` and `compare`. `CASE_KEYS` has neither. Convert them as the SimCC proposal says for its cases (`specs/model-sidecar/proposals/simcc-score-rule/proposal.md`, part 2.1, row `tools/tests/test_vectors.py`). Add `function`, or select the function by the prefix of the id. Map each `compare.<field>.atol` to a tolerance for that field. |
| `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` | new file | The reference file of part 3. It holds the forward warp and the Inverse (`exporter-guide/sidecars/reference-implementations.md:30-32`). |
| `specs/model-sidecar/TRACEABILITY.md` | generated matrix (rows at lines 30, 80) | Do not edit by hand. Run `python tools/sidecar_trace.py matrix` after the section file changes. |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | "Mapping hints for phase 1", "Preprocessing" (lines 36-38) | Non-spec PR. Append: "For `affine_person_crop`, the heading "Arithmetic" of the section gives the float32 steps. An mmpose 0.x pipeline with `_xywh2cs` and `get_affine_transform` (ViTAE) is `crop_policy.arithmetic: pixel_std_200`. A pipeline with `TopDownGetBboxCenterScale` (`bbox_xywh2cs`) is not: it is a `near-miss`." |
| `specs/model-sidecar/templates/model-intake.md` | row T4b (line 264) | Non-spec PR. Append to the section column: "`affine_person_crop`: compare with the heading "Arithmetic"". |
| `notes/decisions/open-work.md` | "Spec defects" (lines 141-147, 168; at `dom/21-move-sidecar-guide`) | Non-spec PR. Line 168: change "the arithmetic precision of the geometry and of the pixel math" so that it excludes `affine_person_crop` (and `pre.normalize` if `normalize-arithmetic` lands). Lines 141-147: the scalar `pad_value` item stays for `fit` only. |
| `specs/model-sidecar/examples/` | all examples | No edit. The RTMW example omits `crop_policy.arithmetic`, so `direct` applies. That is correct for mmpose 1.x. |
| `post.*` (other sections), `common.identity`, `format.file_layout` | | No edit. The change adds no role, no path and no output semantic. |

### 2.2 Fields table

New row in the second table of "Fields" (after `input.resize.crop_policy.pad_value`), and the changed
`pad_value` row:

| Field | Type | Required | Description |
|---|---|---|---|
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | no | This is the constant border value for pixels outside the source image. The default is `0`. A scalar fills every channel. An array gives one value for each channel, in the channel order of `input.color_format`. |
| `input.resize.crop_policy.arithmetic` | enum | no | The arithmetic of the crop geometry: `direct` or `pixel_std_200`. The default is `direct`. See Arithmetic (`#arithmetic`). **(vNEXT)** |

### 2.3 Behaviour

Replace "Behaviour" (lines 39-53) with this text:

````text
## Behaviour

The rotation of the warp is always `0`. Rotated crops are out of scope. The host warps a person box
to `target_size` = `[T_h, T_w]`. `bbox_xyxy` is the person box `[x1, y1, x2, y2]` in source pixels.

### Arithmetic

The pseudocode of this heading is normative. It gives the order of the operations and the dtype of
each value. A host must give the same float32 values for the centre, the crop size and the six warp
points. This heading applies to every `schema_version`.

- `f32(v)` rounds one value to float32 (IEEE 754 binary32, round to nearest, ties to even).
- In a block marked `float32`, each operand is float32, and the host rounds the result of each
  operation to float32.
- In a block marked `float64`, each operation is float64. The host rounds to float32 only where
  the text says `f32`.
- `T_h` and `T_w` are integers.

`crop_policy.arithmetic: direct` (the default):

```text
# float32
x1, y1, x2, y2 = f32(bbox_xyxy)
e   = f32(expand_ratio)
c_x = (x1 + x2) * 0.5
c_y = (y1 + y2) * 0.5
w   = (x2 - x1) * e
h   = (y2 - y1) * e
if maintain_aspect_ratio:
    a = f32(T_w / T_h)                  # T_w / T_h in float64, then one rounding
    if w > h * a: h = w / a             # divide by a. Do not multiply by T_h / T_w.
    else:         w = h * a
```

`crop_policy.arithmetic: pixel_std_200` (`maintain_aspect_ratio` must not be `false`; rule -3):

```text
# float64
x1, y1, x2, y2 = bbox_xyxy              # float64. Do not round the box to float32.
bw  = x2 - x1
bh  = y2 - y1
c_x = f32(x1 + bw * 0.5)
c_y = f32(y1 + bh * 0.5)
a   = T_w / T_h
if   bw > a * bh: bh = bw * 1.0 / a     # strict >
elif bw < a * bh: bw = bh * a           # strict <; when equal, no change
# float32
e   = f32(expand_ratio)
w   = (f32(bw / 200) * e) * 200
h   = (f32(bh / 200) * e) * 200
```

The warp points. `src` holds three float32 points in source pixels. `dst` holds three float32 points
in model-input pixels.

```text
P0 = (c_x, c_y)                                     Q0 = (T_w / 2, T_h / 2)

direct, maintain_aspect_ratio true:
P1 = (f32(c_x - w / 2), c_y)                        Q1 = (0, T_h / 2)
d  = P0.x - P1.x                     # float32
P2 = (P1.x, P1.y + d)                # float32      Q2 = (0, T_h / 2 + T_w / 2)

direct, maintain_aspect_ratio false:
P1 = (f32(c_x - w / 2), c_y)                        Q1 = (0, T_h / 2)
P2 = (c_x, f32(c_y - h / 2))                        Q2 = (T_w / 2, 0)

pixel_std_200:
P1 = (c_x, f32(c_y - w / 2))                        Q1 = (T_w / 2, T_h / 2 - T_w / 2)
d  = P0.y - P1.y                     # float32
P2 = (P1.x - d, P1.y)                # float32      Q2 = (0, T_h / 2 - T_w / 2)

# f32(c - w / 2) and f32(c - h / 2): the subtraction is float64, then one rounding.
M   = the affine map that takes P0, P1, P2 onto Q0, Q1, Q2, solved in float64
      (cv2.getAffineTransform(src, dst))
dst = warpAffine(src_image, M, (T_w, T_h), <interpolation>, borderMode=constant,
                 borderValue=pad_value)
```

- With `maintain_aspect_ratio: true`, `M` uses `w` and not `h`. The y scale of `M` comes from the
  float32 points. It can differ from the x scale. Do not build `M` from `T_w / w` and `T_h / h`.
- The host warps the source image in its own dtype (for example uint8).
- A scalar `pad_value` fills every channel. An array gives one value for each channel.

With `arithmetic: direct` and a float32 box, the crop is the crop of mmpose 1.x
`GetBBoxCenterScale` + `TopdownAffine`. With `arithmetic: pixel_std_200` and a float64 box, the crop
is the crop of the ViTAE / mmpose 0.x `_xywh2cs` + non-UDP `TopDownAffine` (`padding=1.25`).

### Inverse

The host applies the inverse as part of [Unprojection](../post/unprojection.md). It uses the float32
values `c_x`, `c_y`, `w` and `h` of the forward step. It does not invert `M`. It calculates in
float64, in this order:

```text
x_src = x / T_w * w + c_x - 0.5 * w
y_src = y / T_h * h + c_y - 0.5 * h
```

`(x, y)` is a position in model-input pixels. The y axis uses `h`. A host that keeps the result in
float32 rounds `x_src` and `y_src` one time, at the end. The Inverse applies to every
`schema_version`.

| Method | Unprojection (model-input pixels → source pixels) |
|--------|---------------------------------------------------|
| `affine_person_crop` | The closed form above, with `w` and `h` of the forward step. |
````

**Guidance.** Add to "Implementer guidance":

- The `direct` text gives the crop of mmpose v1.3.2 bit for bit. Measured on 2000 random float32
  boxes in 256 x 192 and 384 x 288 (NumPy 2.5.4, OpenCV 5.0.0): 0 crops differ, `M` is equal. The
  current text in float64 gave a different pixel (by 1) in 1911 of 2000 crops. (scratch measurement
  of this proposal; mmpose `structures/bbox/transforms.py:66-67, 406-434`,
  `datasets/transforms/topdown_transforms.py:67-70, 85-118`)
- mmpose `inference_topdown` keeps the dtype of the boxes of the caller (`apis/inference.py:169-170`).
  A float64 box gives float64 arithmetic in mmpose. For parity, give mmpose float32 boxes.
- `M` from `numpy.linalg.solve` differs from `cv2.getAffineTransform` by up to 1.8e-11. This changed
  1 pixel by 1 in 4 and 5 of 2000 crops. Use `cv2.getAffineTransform`, or give the cause and the
  maximum in parity step 4 (`exporter-guide/sidecars/workflow/parity.md:28-32`).
- The closed form of the Inverse is the mmpose inverse (`models/pose_estimators/topdown.py:154-156`).
  After the float32 store of mmpose, 0 of 68000 values differed. The inverse of `M` differs from it
  by up to 7.3e-5 px, because the y scale of `M` comes from float32 points.
- skellytracker `affine_crop.py` puts the second point above the centre (the rtmlib form) and takes
  the dtype of the box. Its crop differs from the `direct` crop in 1092 of 2000 crops with a float32
  box. (skellytracker `skellytracker/core/detectors/processing/affine_crop.py:42-58, 68-85`)

Add to "Authoring guidance":

- mmpose 1.x configs (`GetBBoxCenterScale`, `TopdownAffine` with `use_udp=False`): omit
  `crop_policy.arithmetic`, or write `direct`. (mmpose v1.3.2
  `mmpose/datasets/transforms/topdown_transforms.py:104-108`)
- mmpose 0.x configs (ViTAE ViTPose and ViTPose++, `TopDownAffine` with `use_udp=False`, the box
  through `_xywh2cs`): write `crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true,
  arithmetic: pixel_std_200}`. (ViTAE `c050ed2`
  `mmpose/datasets/datasets/base/kpt_2d_sview_rgb_img_top_down_dataset.py:132-160`,
  `mmpose/core/post_processing/post_transforms.py:226-250`)
- mmpose 0.x configs with `TopDownGetBboxCenterScale` (for example mmpose v0.29.0
  `configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/hrnet_w32_coco_256x192.py:124-125`): this
  step calls `bbox_xywh2cs`, and `bbox_xywh2cs` calculates `f32(w) / 200` (mmpose v0.29.0
  `mmpose/core/bbox/transforms.py:64`). `pixel_std_200` calculates `f32(w / 200)`. Thus neither value
  describes this step. It is a `near-miss`. Add a third value only when a model needs it. Measured on
  2000 random float32 boxes: the crop size differs in 235 boxes (256 x 192) and 250 boxes
  (384 x 288). The crop pixels differ in 183 and 200 boxes. The `get_affine_transform` of v0.29.0
  (`mmpose/core/post_processing/post_transforms.py:197`) has the same code as ViTAE. The case
  `pixel-std-200-is-not-the-mmpose-029-scale` of part 4 separates the two forms.
- `TopDownAffine(use_udp=True)` and `TopdownAffine(use_udp=True)` use another warp
  (`get_warp_matrix` of the UDP paper, `input_size - 1`). Neither arithmetic describes it. It is a
  `gap`.
- The mmpose 0.x inference API converts an `xyxy` box with `w = x2 - x1 + 1` and
  `h = y2 - y1 + 1` (ViTAE `mmpose/apis/inference.py:62-63`). The eval pipeline reads `[x, y, w, h]`
  from the detection file with no `+ 1` (`topdown_coco_dataset.py:204, 210`). `pixel_std_200`
  describes the eval pipeline. The spec does not define the box format of the person box (skellytracker
  `notes/decisions/open-work.md:171`).

### 2.4 Validation rules

New rule, after `V-pre.resize.affine_person_crop-2`:

- [ ] `V-pre.resize.affine_person_crop-3` The field `input.resize.crop_policy.arithmetic` is marked
  **(vNEXT)**. A sidecar with `schema_version < vNEXT` must not contain it. If the field is present,
  it must be `direct` or `pixel_std_200`. If it is `pixel_std_200`,
  `crop_policy.maintain_aspect_ratio` must not be `false`.

The rule has the form of `V-common.input-3` (`common/input.md:60`), which marks single values as
**(vNEXT)**. The rule applies to every sidecar. Thus a valid legacy sidecar has no `arithmetic`
field, and the forward step uses `direct`. The forward step and the Inverse need no
`schema_version`. The other choice was to ignore the field below `vNEXT`. The user chose this
rule (A3, option 1; plan T23, 2026-10-24).

Existing rules that name a value of this change:

- `V-pre.resize.affine_person_crop-1` (line 65): unchanged.
- `V-pre.resize.affine_person_crop-2` (line 66): this proposal does not change it. The change adds
  no resize method. The proposal `roi-transform-and-source` changes its text (user decision T22 (1),
  2026-10-24; header, row "Depends on"). The new text names `pose.estimator_type`, because that
  proposal removes `pose.requires_object_detector`. This proposal does not restate the rule, and its
  `check_rules` does not check it (part 3). Rule -3 reads only `input.resize`. Thus rule -3 does not
  depend on the text of rule -2. A legacy sidecar keeps `pose.requires_object_detector` and the
  legacy text of rule -2 (that proposal, part 2.6). Rule -3 and the forward step do not read the
  field.
- `V-common.input-4` and `V-common.input-5` (`common/input.md:61-62`): unchanged. `crop_policy`
  stays an `affine_person_crop` field, and `pad_value` keeps its shapes.

### 2.5 Selectors

Unchanged: `input.resize.method=affine_person_crop` (front matter line 7).

### 2.6 Legacy behaviour and version effect

- The spec rule: "`vNEXT` requirements never apply retroactively" (`format/versioning.md:51`).
- **Scope (this proposal): every `schema_version`.** It follows the user decision T21 (3) of
  2026-10-23 for `normalize-arithmetic` (option B). The reason is the same: no sidecar is deployed
  yet, and all sidecars will be made again (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The heading
  "Arithmetic" (the `direct` steps) and the Inverse apply to every `schema_version`. A legacy
  sidecar must not contain `crop_policy.arithmetic` (rule -3), so `direct` applies to it.
- The legacy meaning of the fields does not change: the values of `expand_ratio`,
  `maintain_aspect_ratio` and `pad_value` mean the same. In exact math the crop is the same. A
  legacy host can give other crop pixels (by 1) and other keypoints (by float32 rounding). Under
  this scope, such a host does not conform. skellytracker is such a host (part 6).
- `format/versioning.md:51` needs the exception sentence of 2.1 (row `format.versioning`). The
  proposal `normalize-arithmetic` has the same sentence, with the same text (its 2.1, row
  `format.versioning`). The two proposals share it.
- `crop_policy.arithmetic` is `vNEXT` only. `V-pre.resize.affine_person_crop-3` applies to every
  sidecar: it rejects the field in a legacy sidecar.
- New heading "Legacy behaviour" for the section:

  ```text
  ## Legacy behaviour

  | Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
  |-----------|-----------------------------------|---------------------------|
  | `crop_policy.arithmetic` | Not available. A legacy sidecar must not contain it (`V-pre.resize.affine_person_crop-3`). The `direct` arithmetic applies. | Available. The default is `direct`. |
  | [Arithmetic](#arithmetic) and the [Inverse](#inverse) | Apply (the exception in [Version-aware compatibility](../format/versioning.md#version-aware-compatibility)). | Apply. |
  ```

- The change goes into the `vNEXT` revision.

### 2.7 Changelog row

Summary of changes (`changelog.md:16`, five columns). `N` is the next free number at merge time (rows
1 to 19 exist, `changelog.md:18-36`; other proposals of this exporter also add rows).

```text
| N | Resize | `affine_person_crop` defines its arithmetic for every `schema_version`: float32 steps in a fixed order (expand, then fix the aspect with `h = w / a`), three float32 warp points that use `w` only, `M` from these points, and an Inverse in closed form with `w` and `h`. A scalar `crop_policy.pad_value` fills every channel. New `crop_policy.arithmetic` (`direct` \| `pixel_std_200`) for the ViTAE / mmpose 0.x `_xywh2cs` arithmetic (vNEXT). | RTMPose, RTMW, DWPose (mmpose 1.x); ViTPose, ViTPose++ (mmpose 0.x) | [`input.resize`](pre/resize-affine-person-crop.md#arithmetic) |
```

Sentence to append to the `vNEXT` row of the `schema_version` history (`changelog.md:68`):

```text
`affine_person_crop` defines the float32 arithmetic of the crop and the closed-form Inverse (at every `schema_version`), and adds `crop_policy.arithmetic` (`direct` | `pixel_std_200`).
```

Bullet for "Compatibility impact" (`changelog.md:55-59`):

```text
- `affine_person_crop` hosts must follow the heading "Arithmetic" and the closed-form Inverse for every `schema_version`. This is an exception to the rule that `vNEXT` requirements do not apply retroactively. The legacy fields keep their meaning; the crop pixels and the keypoints can change by float32 rounding.
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/model-sidecar/proposals/<slug>/proposal.md`) | the part 3 code of `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_resize_affine_person_crop.py` |
| Functions (one for each algorithm) | `direct_center_and_size` (the `direct` steps), `pixel_std_200_center_and_size` (the `pixel_std_200` steps), `warp_points` (the three point pairs), `warp_matrix` (`M` from the points), `crop_geometry` (the full geometry: centre, crop size, points, `M`), `border_value` (scalar or per-channel `pad_value`), `warp_image` (the warp), `affine_person_crop` (the full forward step), `unproject` (the Inverse), `check_rules` (`V-pre.resize.affine_person_crop-1` and `-3`) |

Source commit: none (no host code). No exporter has host code for this section. The functions come
from the text of part 2. Part 2 comes from the upstream lines of part 1. The section has no reference
implementation yet (`specs/model-sidecar/reference/` does not exist in the checkout). Thus the file
implements the full section as changed: both arithmetic values, the warp, the border value, the
Inverse and the rules -1 and -3. It is also the reference-implementation step of the section and of the
`affine_person_crop` Inverse of `post.unprojection` (`exporter-guide/sidecars/reference-implementations.md:15-16, 30-32`). The file
uses only NumPy, OpenCV and the Python standard library. Load it with
`importlib.util.spec_from_file_location`.

**Rule -2 is not in the file (2026-10-24).** This proposal does not change
`V-pre.resize.affine_person_crop-2`. The proposal `roi-transform-and-source` gives its new text
(header, row "Depends on"). The new text reads `pose.estimator_type`, and it names
`rotated_roi_crop`, a method that only that proposal adds. `check_rules` takes `resize` and
`schema_version`. It reads only `input.resize`. That proposal does the same for a rule that needs
the `pose` block: "Rule `-1` needs the full sidecar (`role`, `pose`). The validator checks it, not
this file." (its part 3, lines 592-593). Its part 6 puts the check of the changed rule -2 into the
validator `_check_pose_requires_affine_crop` (its line 1660). A legacy sidecar still has
`pose.requires_object_detector`. `check_rules` does not read `pose`, so the field does not change
its result. The earlier file had the argument `requires_object_detector` and a check of the legacy
text of rule -2. That check is removed.

```python
"""Reference implementation of the section pre.resize.affine_person_crop, as the proposal changes it.

Section ID: pre.resize.affine_person_crop (section file specs/model-sidecar/pre/resize-affine-person-crop.md).
Proposal: specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md (OpenMMLab-Exporter), slug
affine-crop-arithmetic. No skellytracker decision entry covers it.
Target file in skellytracker: specs/model-sidecar/reference/pre_resize_affine_person_crop.py.

source commit: none (no host code). No exporter has host code for this section yet. The functions
come from the text of part 2 of the proposal. The proposal took that text from mmpose v1.3.2
(crop_policy.arithmetic: direct) and from ViTAE-Transformer/ViTPose c050ed2 (mmpose 0.x,
crop_policy.arithmetic: pixel_std_200). The file does not import mmpose or ViTAE.

One module holds the forward warp and its Inverse. A resize method and its unprojection are one
module (skellytracker specs/exporter-guide/sidecars/reference-implementations.md, "Reference implementations"). The section has
no reference implementation yet, so this file implements the full section as changed: the crop
geometry of both arithmetic values, the warp, the scalar or per-channel pad value, the Inverse and
the validation rules V-pre.resize.affine_person_crop-1 and -3.

Rule V-pre.resize.affine_person_crop-2 is not in this file. This proposal does not change it. The
MediaPipe-Exporter proposal roi-transform-and-source (the full proposal of skellytracker 0020) gives
its new text (user decision T22 (1), 2026-10-24): the rule names pose.estimator_type, because that
proposal removes pose.requires_object_detector. The rule reads the pose block, not input.resize, so
the validator checks it (as that proposal does for its rule V-pre.resize.rotated_roi_crop-1).
check_rules reads only input.resize. A legacy sidecar still has pose.requires_object_detector, but
the field does not change the result of check_rules.

Version scope: the user decision of 2026-10-23 for normalize-arithmetic (option B) also applies
here. The arithmetic applies to every schema_version, so the forward and the Inverse take no
schema_version. Only the new field crop_policy.arithmetic is vNEXT: rule -3 rejects it in a legacy
sidecar, so a valid legacy sidecar always uses direct.

Vector results (run of 2026-10-23, NumPy 2.5.4, OpenCV 5.0.0): the 7 cases of
specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml pass at their tolerance 1e-4, and the 2
affine_person_crop cases of specs/model-sidecar/vectors/post.unprojection.yaml pass exactly (skellytracker
dom/12-single-working-branch; both files are the same at dom/18-agents-adr-bootstrap-kit and at dom/21-move-sidecar-guide). The 43 cases of part 4 of the proposal (28 of them new) pass in the template form: exact,
or with the atol of compare (run of 2026-10-24 with 42 cases, after the removal of rule -2 from check_rules; run again on
2026-10-25 with 43 cases, after rule -3 changed from "is not True" to "is False" for maintain_aspect_ratio and the case
rule3-pixel-std-200-with-non-boolean-aspect was added: 43 of 43, and the existing 7 of 7 and 2 of 2). The 20 crop_geometry cases also equal copies of the upstream lines
(mmpose v1.3.2 for direct, ViTAE c050ed2 for pixel_std_200). The 13 unproject cases equal the
mmpose inverse in float64. A copy is not an implementation, so the vectors stay unverified (no host
implementation).
Parity result: to run (part 5 of the proposal).

Uses only NumPy, OpenCV and the Python standard library.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import cv2
import numpy as np

SECTION_ID = "pre.resize.affine_person_crop"
ARITHMETIC_VALUES = ("direct", "pixel_std_200")
DEFAULT_EXPAND_RATIO = 1.25
INTERPOLATION_FLAGS = {
    "linear": cv2.INTER_LINEAR,
    "area": cv2.INTER_AREA,
    "cubic": cv2.INTER_CUBIC,
    "nearest": cv2.INTER_NEAREST,
}

F32 = np.float32


def _round32(value: float) -> np.float32:
    """Round one float64 value one time to float32 (round to nearest, ties to even)."""
    return F32(value)


def direct_center_and_size(
    bbox_xyxy: Sequence[float],
    target_size: Sequence[int],
    expand_ratio: float = DEFAULT_EXPAND_RATIO,
    maintain_aspect_ratio: bool = True,
) -> tuple[np.float32, np.float32, np.float32, np.float32]:
    """pre.resize.affine_person_crop, Behaviour, crop_policy.arithmetic: direct.

    Every operation is float32. Order: expand, then fix the aspect ratio. The h branch divides by the
    aspect ratio a = T_w / T_h. It does not multiply by T_h / T_w. Returns (c_x, c_y, w, h).
    """
    x1, y1, x2, y2 = (_round32(float(v)) for v in bbox_xyxy)
    t_h, t_w = target_size
    e = _round32(float(expand_ratio))
    half = F32(0.5)
    c_x = (x1 + x2) * half
    c_y = (y1 + y2) * half
    w = (x2 - x1) * e
    h = (y2 - y1) * e
    if maintain_aspect_ratio:
        a = _round32(t_w / t_h)
        if w > h * a:
            h = w / a
        else:
            w = h * a
    return c_x, c_y, w, h


def pixel_std_200_center_and_size(
    bbox_xyxy: Sequence[float],
    target_size: Sequence[int],
    expand_ratio: float = DEFAULT_EXPAND_RATIO,
) -> tuple[np.float32, np.float32, np.float32, np.float32]:
    """pre.resize.affine_person_crop, Behaviour, crop_policy.arithmetic: pixel_std_200.

    The mmpose 0.x order: the aspect fix on the box before the expansion, in float64; then the scale
    in float32 units of 200 pixels; then the expansion and the product with 200 in float32.
    maintain_aspect_ratio must be true (V-pre.resize.affine_person_crop-3). Returns (c_x, c_y, w, h).
    The box values are float64. They are not rounded to float32 first (ViTAE reads them as Python
    floats from the detection file).
    """
    x1, y1, x2, y2 = (float(v) for v in bbox_xyxy)  # float64: no float32 rounding of the box
    t_h, t_w = target_size
    box_w = x2 - x1
    box_h = y2 - y1
    c_x = _round32(x1 + box_w * 0.5)
    c_y = _round32(y1 + box_h * 0.5)
    a = t_w / t_h
    if box_w > a * box_h:
        box_h = box_w * 1.0 / a
    elif box_w < a * box_h:
        box_w = box_h * a
    s_w = _round32(box_w / 200.0) * _round32(float(expand_ratio))
    s_h = _round32(box_h / 200.0) * _round32(float(expand_ratio))
    w = s_w * F32(200.0)
    h = s_h * F32(200.0)
    return c_x, c_y, w, h


def warp_points(
    center_and_size: tuple[np.float32, np.float32, np.float32, np.float32],
    target_size: Sequence[int],
    maintain_aspect_ratio: bool = True,
    arithmetic: str = "direct",
) -> tuple[np.ndarray, np.ndarray]:
    """pre.resize.affine_person_crop, Behaviour: the three float32 point pairs that define M.

    With maintain_aspect_ratio true, the forward warp uses w and not h. The third point comes from a
    90-degree turn of the first two points, in float32.
    direct: the second point is left of the centre. pixel_std_200: the second point is above it.
    With maintain_aspect_ratio false (direct only), the third point uses h.
    Returns (src, dst), each a float32 array of shape (3, 2).
    """
    c_x, c_y, w, h = center_and_size
    t_h, t_w = target_size
    src = np.zeros((3, 2), dtype=np.float32)
    dst = np.zeros((3, 2), dtype=np.float32)
    src[0] = (c_x, c_y)
    dst[0] = (t_w * 0.5, t_h * 0.5)
    if arithmetic == "direct":
        src[1] = (_round32(float(c_x) - float(w) * 0.5), c_y)
        dst[1] = (0.0, t_h * 0.5)
        if maintain_aspect_ratio:
            d = src[0, 0] - src[1, 0]
            src[2] = (src[1, 0], src[1, 1] + d)
            dst[2] = (0.0, t_h * 0.5 + t_w * 0.5)
        else:
            src[2] = (c_x, _round32(float(c_y) - float(h) * 0.5))
            dst[2] = (t_w * 0.5, 0.0)
    elif arithmetic == "pixel_std_200":
        if not maintain_aspect_ratio:
            raise ValueError("pixel_std_200 needs maintain_aspect_ratio: true")
        src[1] = (c_x, _round32(float(c_y) - float(w) * 0.5))
        dst[1] = (t_w * 0.5, t_h * 0.5 - t_w * 0.5)
        d = src[0, 1] - src[1, 1]
        src[2] = (src[1, 0] - d, src[1, 1])
        dst[2] = (0.0, t_h * 0.5 - t_w * 0.5)
    else:
        raise ValueError(f"unknown crop_policy.arithmetic {arithmetic!r}")
    return src, dst


def warp_matrix(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """pre.resize.affine_person_crop, Behaviour: M is the affine map that takes src onto dst.

    The solution is in float64. cv2.getAffineTransform solves it.
    """
    return cv2.getAffineTransform(np.asarray(src, np.float32), np.asarray(dst, np.float32))


def crop_geometry(
    bbox_xyxy: Sequence[float],
    target_size: Sequence[int],
    expand_ratio: float = DEFAULT_EXPAND_RATIO,
    maintain_aspect_ratio: bool = True,
    arithmetic: str = "direct",
) -> dict[str, Any]:
    """pre.resize.affine_person_crop, Behaviour: the centre, the crop size, the points and M.

    The rotation is always 0. target_size is [T_h, T_w]. bbox_xyxy is [x1, y1, x2, y2] in source
    pixels.
    """
    if arithmetic == "direct":
        cs = direct_center_and_size(bbox_xyxy, target_size, expand_ratio, maintain_aspect_ratio)
    elif arithmetic == "pixel_std_200":
        if not maintain_aspect_ratio:
            raise ValueError("pixel_std_200 needs maintain_aspect_ratio: true")
        cs = pixel_std_200_center_and_size(bbox_xyxy, target_size, expand_ratio)
    else:
        raise ValueError(f"unknown crop_policy.arithmetic {arithmetic!r}")
    src, dst = warp_points(cs, target_size, maintain_aspect_ratio, arithmetic)
    c_x, c_y, w, h = cs
    return {
        "center": [float(c_x), float(c_y)],
        "crop_w": float(w),
        "crop_h": float(h),
        "src_points": src.astype(np.float64).tolist(),
        "dst_points": dst.astype(np.float64).tolist(),
        "matrix": warp_matrix(src, dst).tolist(),
    }


def border_value(pad_value: float | Sequence[float], channels: int) -> tuple[float, ...]:
    """pre.resize.affine_person_crop, Behaviour: the border value of each channel.

    A scalar pad_value fills every channel. An array gives one value for each channel.
    """
    if isinstance(pad_value, (int, float)) and not isinstance(pad_value, bool):
        values = [float(pad_value)] * channels
    else:
        values = [float(v) for v in pad_value]
        if len(values) != channels:
            raise ValueError("pad_value array length must equal the number of channels")
    return tuple(values) + (0.0,) * (4 - len(values))


def warp_image(
    image: np.ndarray,
    matrix: Sequence[Sequence[float]],
    target_size: Sequence[int],
    interpolation: str = "linear",
    pad_value: float | Sequence[float] = 0,
) -> np.ndarray:
    """pre.resize.affine_person_crop, Behaviour: warp the source image with M to (T_w, T_h).

    The source dtype stays (for example uint8). The border mode is constant.
    """
    t_h, t_w = target_size
    channels = 1 if image.ndim == 2 else image.shape[2]
    return cv2.warpAffine(
        image,
        np.asarray(matrix, dtype=np.float64),
        (int(t_w), int(t_h)),
        flags=INTERPOLATION_FLAGS[interpolation],
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value(pad_value, channels),
    )


def affine_person_crop(
    image: np.ndarray,
    bbox_xyxy: Sequence[float],
    target_size: Sequence[int],
    crop_policy: Mapping[str, Any] | None = None,
    interpolation: str = "linear",
) -> tuple[np.ndarray, dict[str, Any]]:
    """pre.resize.affine_person_crop, Behaviour: the full forward step for one person box.

    Returns the warped image and the crop geometry. The Inverse uses the geometry.
    """
    policy = dict(crop_policy or {})
    geometry = crop_geometry(
        bbox_xyxy,
        target_size,
        policy.get("expand_ratio", DEFAULT_EXPAND_RATIO),
        policy.get("maintain_aspect_ratio", True),
        policy.get("arithmetic", "direct"),
    )
    crop = warp_image(image, geometry["matrix"], target_size, interpolation, policy.get("pad_value", 0))
    return crop, geometry


def unproject(
    model_xy: Sequence[float],
    center: Sequence[float],
    crop_w: float,
    crop_h: float,
    target_size: Sequence[int],
) -> list[float]:
    """pre.resize.affine_person_crop, Inverse: model-input pixels to source pixels.

    Closed form on each axis, in float64, in this order:
    x_src = x / T_w * w + c_x - 0.5 * w and y_src = y / T_h * h + c_y - 0.5 * h.
    The y axis uses h, not the y scale of M. center, crop_w and crop_h are the float32 values of the
    forward step.
    """
    t_h, t_w = target_size
    x, y = (float(v) for v in model_xy)
    c_x, c_y = (float(v) for v in center)
    w = float(crop_w)
    h = float(crop_h)
    return [x / t_w * w + c_x - 0.5 * w, y / t_h * h + c_y - 0.5 * h]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_rules(
    resize: Mapping[str, Any] | None,
    schema_version: str = "vNEXT",
) -> list[str]:
    """pre.resize.affine_person_crop, Validation rules -1 and -3: the IDs of the rules that fail.

    -1: expand_ratio is a positive number; maintain_aspect_ratio is a boolean.
    -2: not checked here. It reads pose.estimator_type, and the proposal roi-transform-and-source
    gives its text (see the module docstring).
    -3: crop_policy.arithmetic is marked (vNEXT). A legacy sidecar must not contain it. At vNEXT,
    arithmetic is direct or pixel_std_200, and pixel_std_200 must not have maintain_aspect_ratio
    false. A non-boolean maintain_aspect_ratio fails rule -1 only.
    schema_version is "vNEXT" or a legacy release string (for example "v2024.09.1019").
    A sidecar that passes rule -3 at a legacy version has no arithmetic field, so the forward step
    uses direct. The forward step and the Inverse thus need no schema_version.
    """
    failed: list[str] = []
    resize = dict(resize or {})
    policy = resize.get("crop_policy") or {}
    if "expand_ratio" in policy and not (_is_number(policy["expand_ratio"]) and policy["expand_ratio"] > 0):
        failed.append(f"V-{SECTION_ID}-1")
    elif "maintain_aspect_ratio" in policy and not isinstance(policy["maintain_aspect_ratio"], bool):
        failed.append(f"V-{SECTION_ID}-1")
    if "arithmetic" in policy:
        value = policy["arithmetic"]
        if schema_version != "vNEXT":
            failed.append(f"V-{SECTION_ID}-3")
        elif value not in ARITHMETIC_VALUES:
            failed.append(f"V-{SECTION_ID}-3")
        elif value == "pixel_std_200" and policy.get("maintain_aspect_ratio", True) is False:
            failed.append(f"V-{SECTION_ID}-3")
    return failed
```

## 4. Vectors

Run of 2026-10-23. The scratch runner `runv.py` reads the YAML block below from this file. It
accepts only the keys of the template (`id`, `function`, `params`, `input`, `expect`, `compare`).
It compares each value exactly, or with the `atol` of `compare`. It also runs the existing vectors
of skellytracker in their own form, and the mutants. The scratch script `upcheck.py` runs the cases
through copies of the upstream lines. Both use `uv run --project <exporter repo> python -I -B`,
NumPy 2.5.4, OpenCV 5.0.0 and PyYAML 6.0.3.

- **The 7 existing cases** of `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml`
  (skellytracker `dom/12-single-working-branch`; the file is the same at `dom/18-agents-adr-bootstrap-kit`) pass in their own form (`tolerance` 1e-4 and an `unproject`
  sub-block): 7 of 7. That file does not change. The block below has them in the template form.
  Each `tolerance` is now a `compare.atol` of 1e-4. Each `unproject` sub-block is now its own
  `unproject` case (`<id>-unproject`). The input of such a case is the float32 forward values of
  the reference. For `wide-box-grows-height` these values are `crop_h` 666.6666870117188 and
  `source_xy` y -233.33334350585938. They differ from the rounded values of the file by at most
  2.0e-5, which is in the tolerance 1e-4.
- **The 2 `affine_person_crop` cases** of `specs/model-sidecar/vectors/post.unprojection.yaml`
  (`pixel-affine-person-crop`, line 185; `normalized-11-affine-person-crop`, line 198) pass: 2 of 2,
  exact. The runner does the scale step of `post.unprojection` and then calls `unproject`. The other
  21 of the 23 cases of that file use other resize methods. They do not apply. After the scale step
  the two cases are the same `unproject` case. Thus the block below has one of them
  (`unprojection-pixel-affine-person-crop`). The `normalized_11` scale step belongs to
  `post.unprojection`, and this file does not test it.
- **The block** has 43 cases: 15 from the skellytracker files and 28 new cases (42 and 27 before
  2026-10-25). 43 of 43 pass (run of 2026-10-25, below). Before 2026-10-25 the file recorded 42 of
  42 (the run of 2026-10-24 after the T22 (1) removal, below).
  Run again on 2026-10-24 after the A1 to A4 edit and the change of the shared exception sentence
  (no case and no reference function changed; scratch `omm-proposals/run_all.py`): 43 of 43, and
  the existing 7 of 7 and 2 of 2.
  Changed on 2026-10-24 for user decision T22 (1) (part 3, "Rule -2 is not in the file"): the case
  `rule2-top-down-needs-affine-crop` is removed, because it tested the legacy text of rule -2, which
  this proposal does not change. The other `check_rules` cases lose the parameter
  `requires_object_detector: false`. It had no effect on them. No other case and no expected value
  changed. Run after the change (scratch `omm-proposals/run_all.py`): 42 of 42, and the existing
  7 of 7 and 2 of 2.
  Changed on 2026-10-25 (review finding F4): `check_rules` now fails rule -3 for `pixel_std_200`
  only when `maintain_aspect_ratio` is `false` (`is False`). The earlier code tested `is not True`,
  so it also failed rule -3 for a non-boolean value, which the rule text assigns to rule -1 only.
  The sentences of 2.3, part 6 and the reference docstring now say "must not be `false`", as rule
  -3 does. New case `rule3-pixel-std-200-with-non-boolean-aspect`. No other case and no expected
  value changed. Run after the change (scratch `affine-fix/runv.py`, NumPy 2.5.4, OpenCV 5.0.0,
  skellytracker `dom/21-move-sidecar-guide`): 43 of 43, and the existing 7 of 7 and 2 of 2.
  The cases are 20 `crop_geometry`, 13 `unproject`, 2 `affine_person_crop` and 8 `check_rules`
  (7 before 2026-10-25).
  Each `check_rules` case tests rule -1 or rule -3.
- **Separation.** Each case below fails for one wrong reading:
  - `w / a` against `w * f32(T_h / T_w)` (1 ulp): `direct-h-branch-divides-by-aspect` and
    `direct-target-384x288-h-branch`.
  - The strict `>` against `>=`: `direct-tie-strict-greater-keeps-h`. Here `w` equals `h * a` in
    float32, but `w / a` is not `h`.
  - The float32 comparison against a float64 comparison: `direct-float32-product-decides-the-branch`.
    Here `h * a` rounds up to `w` in float32, but the exact product is below `w`.
  - The decimal reading of the box against `f32(bbox_xyxy)`:
    `direct-float32-comparison-decides-the-branch`.
  - The float64 box of `pixel_std_200` against an `f32` box: `pixel-std-200-float64-box`.
  - `f32(bh / 200)` (ViTAE `_xywh2cs`) against `f32(bh) / 200` (mmpose v0.29.0 `bbox_xywh2cs`):
    `pixel-std-200-is-not-the-mmpose-029-scale`.
  - The Inverse order `x / T_w * w` against `x * w / T_w` (float64): `unproject-order-x-over-t-first`.
  - Rule -3 `is False` against `is not True` for `maintain_aspect_ratio` (a non-boolean value fails
    rule -1 only): `rule3-pixel-std-200-with-non-boolean-aspect` (added 2026-10-25).
  - Each arithmetic has a case for the h branch, the w branch and the equal aspect. In the two
    equal-aspect cases both branches give the same values.
  - 13 cases test the Inverse.
- **Upstream copies.** The 20 `crop_geometry` cases give the same values as copies of mmpose v1.3.2
  and of ViTAE `c050ed2`. The centre, the crop size, the points and `M` are equal bit for bit. The
  `direct` cases use mmpose
  v1.3.2, with `fix_aspect_ratio=False` for the two `maintain_aspect_ratio: false` cases. The
  `pixel_std_200` cases use ViTAE `c050ed2`. The 13 `unproject` cases give the same float64 values
  as the mmpose inverse (`topdown.py:154-156`) before its float32 store. The copies are not an
  implementation (`exporter-guide/sidecars/sidecar-files.md:8-10`).
- **Mutants.** The run tested 20 changes of the reference file. 15 of them fail at least one case
  (one more mutant on 2026-10-25, below: 21 changes, 16 fail):
  - `h = w * f32(T_h / T_w)` (2 cases fail); `>=` in place of `>` (2); a float64 comparison (1);
    `a` not rounded, with a float64 aspect fix (1); the centre as `x1 + (x2 - x1) / 2` (2).
  - The second point above the centre for `direct`, the rtmlib and skellytracker form (15).
  - `pixel_std_200` with an `f32` box (2); without the float32 round trip through 200 (3); with the
    mmpose v0.29.0 scale (1).
  - The Inverse with `x * w / T_w` (1); with `w` on the y axis (5); as the inverse of `M` (6).
  - A scalar `pad_value` that fills only channel 0, the OpenCV meaning of a scalar (1).
  - Rule -3 without the `maintain_aspect_ratio` condition (1).
  - Rule -3 not applied to a legacy sidecar (1). The first version of the reference file did this.
  - Rule -3 with `is not True` in place of `is False` for `maintain_aspect_ratio` (1; added
    2026-10-25). The reference file did this until 2026-10-25.
- **Mutants that no case finds.** Five changes give the same values on every case:
  - `h = f32(w * (T_h / T_w))` with a float64 product. This rounds the exact `w * 4 / 3` one time,
    as `w / a` does.
  - `P1.x` as a float32 subtraction. A float64 subtraction of two float32 values is exact here, so
    one rounding gives the same value.
  - `pixel_std_200` with `bw * (T_h / T_w)`. The float32 rounding of `bh / 200` hides the 1-ulp
    float64 difference. The search found no h-branch box that changes (random boxes with 2
    decimals, from 200000 draws).
  - `pixel_std_200` with `>=`. It changes a value only when `bw = a * bh` exactly in float64 and
    `f32(bw / a / 200)` is not `f32(bh / 200)`. The search found no such box (boxes
    `[0, 0, 0.75 * bh, bh]` with `bh` from 0.01 to 19.99).
  - `M` from `numpy.linalg.solve`. `compare.matrix.atol` accepts it by design (below).

`compare.matrix.atol` is 1e-9 for each new `crop_geometry` case. `M` comes from a float64 solution.
Another LU solution can differ in the last bits. 1e-9 is far below the differences that the cases
test (5.1e-6 and more). Every other new value must match exactly. Each number has the shortest
text that gives the same float64 value, so a float32 value is exact in the text. The transcribed
existing cases use `compare.atol` 1e-4, the `tolerance` of their file.

The YAML uses the form of the template (`function` on each case, and `compare` where a value needs
a tolerance). The skellytracker vector tooling uses another form. 2.1 (rows `tools/make_vectors.py`
and `tools/tests/test_vectors.py`) gives the conversion.

```yaml
section: pre.resize.affine_person_crop
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`
unverified: "no host implementation. No exporter and no skellytracker code implements the changed
  text yet. skellytracker affine_crop.py uses another warp point and the dtype of the box."
# Upstream runs (not implementations): the crop_geometry cases equal copies of mmpose v1.3.2
# structures/bbox/transforms.py:44-73, 372-435 and datasets/transforms/topdown_transforms.py:56-71
# (direct), and of ViTAE c050ed2 kpt_2d_sview_rgb_img_top_down_dataset.py:132-160 and
# post_transforms.py:197-290 (pixel_std_200). The unproject cases equal mmpose
# models/pose_estimators/topdown.py:154-156 in float64.
cases:
- id: tall-box-grows-width  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [100, 50, 300, 450]
  expect:
    center: [200, 250]
    crop_w: 375
    crop_h: 500
    matrix:
    - [0.512, 0, -6.4]
    - [0, 0.512, 0]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: wide-box-grows-height  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [0, 0, 400, 200]
  expect:
    center: [200, 100]
    crop_w: 500
    crop_h: 666.666667
    matrix:
    - [0.384, 0, 19.2]
    - [0, 0.384, 89.6]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: no-expansion  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [10, 20, 110, 220]
  expect:
    center: [60, 120]
    crop_w: 150
    crop_h: 200
    matrix:
    - [1.28, 0, 19.2]
    - [0, 1.28, -25.6]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: aspect-ratio-not-kept  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: false
  input:
    bbox_xyxy: [100, 50, 300, 450]
  expect:
    center: [200, 250]
    crop_w: 250
    crop_h: 500
    matrix:
    - [0.768, 0, -57.6]
    - [0, 0.512, 0]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: box-outside-the-image  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [-50, -20, 150, 380]
  expect:
    center: [50, 180]
    crop_w: 375
    crop_h: 500
    matrix:
    - [0.512, 0, 70.4]
    - [0, 0.512, 35.84]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: square-target  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [288, 288]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [0, 0, 100, 100]
  expect:
    center: [50, 50]
    crop_w: 125
    crop_h: 125
    matrix:
    - [2.304, 0, 28.8]
    - [0, 2.304, 28.8]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: target-384x288  # existing case of vectors/pre.resize.affine_person_crop.yaml: same values; tolerance 0.0001 is now compare.atol
  function: crop_geometry
  params:
    target_size: [384, 288]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [320, 100, 520, 600]
  expect:
    center: [420, 350]
    crop_w: 468.75
    crop_h: 625
    matrix:
    - [0.6144, 0, -114.048]
    - [0, 0.6144, -23.04]
  compare:
    center: {atol: 1.0e-04}
    crop_w: {atol: 1.0e-04}
    crop_h: {atol: 1.0e-04}
    matrix: {atol: 1.0e-04}
- id: tall-box-grows-width-unproject  # the unproject sub-block of the existing case tall-box-grows-width; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [96, 128]
    center: [200.0, 250.0]
    crop_w: 375.0
    crop_h: 500.0
  expect:
    source_xy: [200, 250]
  compare:
    source_xy: {atol: 1.0e-04}
- id: wide-box-grows-height-unproject  # the unproject sub-block of the existing case wide-box-grows-height; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [0, 0]
    center: [200.0, 100.0]
    crop_w: 500.0
    crop_h: 666.6666870117188
  expect:
    source_xy: [-50, -233.333333]
  compare:
    source_xy: {atol: 1.0e-04}
- id: no-expansion-unproject  # the unproject sub-block of the existing case no-expansion; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [192, 256]
    center: [60.0, 120.0]
    crop_w: 150.0
    crop_h: 200.0
  expect:
    source_xy: [135, 220]
  compare:
    source_xy: {atol: 1.0e-04}
- id: aspect-ratio-not-kept-unproject  # the unproject sub-block of the existing case aspect-ratio-not-kept; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [192, 256]
    center: [200.0, 250.0]
    crop_w: 250.0
    crop_h: 500.0
  expect:
    source_xy: [325, 500]
  compare:
    source_xy: {atol: 1.0e-04}
- id: box-outside-the-image-unproject  # the unproject sub-block of the existing case box-outside-the-image; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [96, 128]
    center: [50.0, 180.0]
    crop_w: 375.0
    crop_h: 500.0
  expect:
    source_xy: [50, 180]
  compare:
    source_xy: {atol: 1.0e-04}
- id: square-target-unproject  # the unproject sub-block of the existing case square-target; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [288, 288]
  input:
    model_xy: [288, 288]
    center: [50.0, 50.0]
    crop_w: 125.0
    crop_h: 125.0
  expect:
    source_xy: [112.5, 112.5]
  compare:
    source_xy: {atol: 1.0e-04}
- id: target-384x288-unproject  # the unproject sub-block of the existing case target-384x288; input: the float32 forward values of the reference
  function: unproject
  params:
    target_size: [384, 288]
  input:
    model_xy: [144, 192]
    center: [420.0, 350.0]
    crop_w: 468.75
    crop_h: 625.0
  expect:
    source_xy: [420, 350]
  compare:
    source_xy: {atol: 1.0e-04}
- id: unprojection-pixel-affine-person-crop  # from vectors/post.unprojection.yaml case pixel-affine-person-crop. Its sibling normalized-11-affine-person-crop gives the same model_xy after the scale step of post.unprojection, so it adds no case here
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [96, 128]
    center: [148.0, 264.0]
    crop_w: 96.0
    crop_h: 128.0
  expect:
    source_xy: [148, 264]
- id: direct-h-branch-divides-by-aspect  # wide box: w > h * a, so h = w / a = 375.125 / 0.75 in float32. The current text h = w * (256 / 192) gives 500.16668701171875, 1 ulp more
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [120, 80, 420.1, 280]
  expect:
    center: [270.04998779296875, 180.0]
    crop_w: 375.125
    crop_h: 500.1666564941406
    src_points:
    - [270.04998779296875, 180.0]
    - [82.48748779296875, 180.0]
    - [82.48748779296875, 367.5625]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [0.5118293902032656, -1.1365737018769012e-17, -42.2195205764745]
    - [5.2623052610898914e-17, 0.5118293902032656, 35.87070976341218]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-w-branch-float32-points  # tall box: w = h * a. P1.x = float32(c_x - w / 2) rounds, so d = c_x - P1.x is not w / 2 and M[1][1] differs from M[0][0]
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [37.3, 41.9, 189.0, 463.3]
  expect:
    center: [113.1500015258789, 252.59999084472656]
    crop_w: 395.0625
    crop_h: 526.75
    src_points:
    - [113.1500015258789, 252.59999084472656]
    - [-84.3812484741211, 252.59999084472656]
    - [-84.3812484741211, 450.1312255859375]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [0.48599905078310396, 0.0, 41.00920666231609]
    - [1.0204435970299861e-16, 0.4859990883253033, 5.236634738482922]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-equal-aspect-takes-the-w-branch  # w = 187.5 = h * a exactly, and w / a = h exactly. Both branches give the same values here, so this case does not test the strict >. direct-tie-strict-greater-keeps-h tests it
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [0, 0, 150, 200]
  expect:
    center: [75.0, 100.0]
    crop_w: 187.5
    crop_h: 250.0
    src_points:
    - [75.0, 100.0]
    - [-18.75, 100.0]
    - [-18.75, 193.75]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [1.024, -1.624097681737372e-17, 19.200000000000003]
    - [3.315866100213801e-16, 1.024, 25.59999999999997]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-float32-comparison-decides-the-branch  # decimal numbers of the box: w = h * a (w branch). After f32(bbox_xyxy): w = 93.7593765258789 > h * a = 93.75936889648438, so the h branch runs. A float64 comparison of the same float32 values also takes the h branch. direct-float32-product-decides-the-branch tests the float32 comparison
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [50, 60, 125.0075, 160.01]
  expect:
    center: [87.50375366210938, 110.00499725341797]
    crop_w: 93.7593765258789
    crop_h: 125.01250457763672
    src_points:
    - [87.50375366210938, 110.00499725341797]
    - [40.62406539916992, 110.00499725341797]
    - [40.62406539916992, 156.8846893310547]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [2.047795187151285, 0.0, -83.18976560693922]
    - [-3.248056025133822e-16, 2.047795020517966, -97.2676856076418]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-tie-strict-greater-keeps-h  # float32: w = 145.48541259765625 = h * a, so the strict > is false and h stays 193.98056030273438. A >= takes the h branch and gives h = w / a = 193.9805450439453
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.0
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [0, 0, 145.48541259765625, 193.98056030273438]
  expect:
    center: [72.74270629882812, 96.99028015136719]
    crop_w: 145.48541259765625
    crop_h: 193.98056030273438
    src_points:
    - [72.74270629882812, 96.99028015136719]
    - [0.0, 96.99028015136719]
    - [0.0, 169.7329864501953]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [1.3197199401082298, 0.0, 0.0]
    - [3.0172766800396685e-17, 1.31971994010823, -6.7124427709252465e-06]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-float32-product-decides-the-branch  # h * a rounds up to w in float32 (373.7584228515625). The exact product 373.75840759277344 is below w. The float32 comparison takes the w branch and h stays 498.34454345703125. A float64 comparison takes the h branch and gives 498.3445739746094
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.0
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [0, 0, 373.7584228515625, 498.34454345703125]
  expect:
    center: [186.87921142578125, 249.17227172851562]
    crop_w: 373.7584228515625
    crop_h: 498.34454345703125
    src_points:
    - [186.87921142578125, 249.17227172851562]
    - [0.0, 249.17227172851562]
    - [0.0, 436.0514831542969]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [0.0, 224.0]
    matrix:
    - [0.5137007977911242, 0.0, 0.0]
    - [-1.0809729788900114e-16, 0.513700797791124, 5.225634814415922e-06]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-aspect-ratio-not-kept-uses-h  # maintain_aspect_ratio false: P2 = (c_x, float32(c_y - h / 2)) maps to (T_w / 2, 0); the y scale comes from h
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: false
  input:
    bbox_xyxy: [37.3, 41.9, 189.0, 463.3]
  expect:
    center: [113.1500015258789, 252.59999084472656]
    crop_w: 189.625
    crop_h: 526.75
    src_points:
    - [113.1500015258789, 252.59999084472656]
    - [18.337501525878906, 252.59999084472656]
    - [113.1500015258789, -10.775009155273438]
    dst_points:
    - [96.0, 128.0]
    - [0.0, 128.0]
    - [96.0, 0.0]
    matrix:
    - [1.012524719841793, -6.178348392197439e-17, -18.567173595088974]
    - [7.849566130999892e-18, 0.4859990507831039, 5.236644221642151]
  compare:
    matrix: {atol: 1.0e-09}
- id: direct-target-384x288-h-branch  # the same wide box in a 288 x 384 target: a = 0.75 again, so crop_w and crop_h are as in direct-h-branch-divides-by-aspect
  function: crop_geometry
  params:
    target_size: [384, 288]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
  input:
    bbox_xyxy: [120, 80, 420.1, 280]
  expect:
    center: [270.04998779296875, 180.0]
    crop_w: 375.125
    crop_h: 500.1666564941406
    src_points:
    - [270.04998779296875, 180.0]
    - [82.48748779296875, 180.0]
    - [82.48748779296875, 367.5625]
    dst_points:
    - [144.0, 192.0]
    - [0.0, 192.0]
    - [0.0, 336.0]
    matrix:
    - [0.7677440853048983, 0.0, -63.32928086471176]
    - [2.6311526305449457e-17, 0.7677440853048986, 53.80606464511825]
  compare:
    matrix: {atol: 1.0e-09}
- id: pixel-std-200-h-branch  # wide box: float64 aspect fix on the box, then float32(w / 200) * 1.25 * 200. direct gives crop_w 375.75 and crop_h 501.0
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
    arithmetic: pixel_std_200
  input:
    bbox_xyxy: [120, 80, 420.6, 280]
  expect:
    center: [270.29998779296875, 180.0]
    crop_w: 375.7500305175781
    crop_h: 500.9999694824219
    src_points:
    - [270.29998779296875, 180.0]
    - [270.29998779296875, -7.8750152587890625]
    - [82.42497253417969, -7.8750152587890625]
    dst_points:
    - [96.0, 128.0]
    - [96.0, 32.0]
    - [0.0, 32.0]
    matrix:
    - [0.5109780024116805, -0.0, -42.11734781435276]
    - [0.0, 0.5109780024116803, 36.023959565897535]
  compare:
    matrix: {atol: 1.0e-09}
- id: pixel-std-200-w-branch  # tall box: direct gives crop_h 500.125. The second point is above the centre
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
    arithmetic: pixel_std_200
  input:
    bbox_xyxy: [37, 41, 237, 441.1]
  expect:
    center: [137.0, 241.0500030517578]
    crop_w: 375.09375
    crop_h: 500.1249694824219
    src_points:
    - [137.0, 241.0500030517578]
    - [137.0, 53.50312805175781]
    - [-50.546875, 53.50312805175781]
    dst_points:
    - [96.0, 128.0]
    - [96.0, 32.0]
    - [0.0, 32.0]
    matrix:
    - [0.511872031992002, -0.0, 25.87353161709573]
    - [-5.1864433267160596e-17, 0.511872031992002, 4.613245126218452]
  compare:
    matrix: {atol: 1.0e-09}
- id: pixel-std-200-equal-aspect  # w = h * a exactly: neither branch runs (strict > and strict <)
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
    arithmetic: pixel_std_200
  input:
    bbox_xyxy: [0, 0, 150, 200]
  expect:
    center: [75.0, 100.0]
    crop_w: 187.5
    crop_h: 250.0
    src_points:
    - [75.0, 100.0]
    - [75.0, 6.25]
    - [-18.75, 6.25]
    dst_points:
    - [96.0, 128.0]
    - [96.0, 32.0]
    - [0.0, 32.0]
    matrix:
    - [1.024, -0.0, 19.2]
    - [0.0, 1.024, 25.6]
  compare:
    matrix: {atol: 1.0e-09}
- id: pixel-std-200-float64-box  # the box values are float64 and are not rounded to float32 first. A host that uses f32(bbox_xyxy) gives c_y 387.47998046875 and crop_w 205.36245727539062
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
    arithmetic: pixel_std_200
  input:
    bbox_xyxy: [483.0, 323.18, 647.29, 451.78]
  expect:
    center: [565.14501953125, 387.4800109863281]
    crop_w: 205.36251831054688
    crop_h: 273.8166809082031
    src_points:
    - [565.14501953125, 387.4800109863281]
    - [565.14501953125, 284.79876708984375]
    - [462.4637756347656, 284.79876708984375]
    dst_points:
    - [96.0, 128.0]
    - [96.0, 32.0]
    - [0.0, 32.0]
    matrix:
    - [0.9349321877789103, -0.0, -432.3722695227065]
    - [-1.0058200443481892e-16, 0.9349321877789102, -234.26753439204384]
  compare:
    matrix: {atol: 1.0e-09}
- id: pixel-std-200-is-not-the-mmpose-029-scale  # h branch. f32(bh / 200) gives crop_h 205.53334045410156 (ViTAE _xywh2cs). The mmpose v0.29.0 bbox_xywh2cs form f32(bh) / 200 gives 205.53330993652344
  function: crop_geometry
  params:
    target_size: [256, 192]
    expand_ratio: 1.25
    maintain_aspect_ratio: true
    arithmetic: pixel_std_200
  input:
    bbox_xyxy: [379.33, 186.57, 502.65, 349.76]
  expect:
    center: [440.989990234375, 268.1650085449219]
    crop_w: 154.14999389648438
    crop_h: 205.53334045410156
    src_points:
    - [440.989990234375, 268.1650085449219]
    - [440.989990234375, 191.0900115966797]
    - [363.91497802734375, 191.0900115966797]
    dst_points:
    - [96.0, 128.0]
    - [96.0, 32.0]
    - [0.0, 32.0]
    matrix:
    - [1.2455398611178203, -0.0, -453.27061119087233]
    - [1.2889956715479455e-16, 1.2455401077014174, -206.01027362479357]
  compare:
    matrix: {atol: 1.0e-09}
- id: unproject-order-x-over-t-first  # float64, in the order x / T_w * w: 178.22251383463538. The order x * w / T_w gives 178.22251383463544
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [49, 0]
    center: [270.04998779296875, 180.0]
    crop_w: 375.125
    crop_h: 500.1666564941406
  expect:
    source_xy: [178.22251383463538, -70.08332824707031]
- id: unproject-h-branch-uses-h  # y uses h = 500.1666564941406. The inverse of M gives y = 430.0833333333333 (5.1e-6 more)
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [192, 256]
    center: [270.04998779296875, 180.0]
    crop_w: 375.125
    crop_h: 500.1666564941406
  expect:
    source_xy: [457.61248779296875, 430.0833282470703]
- id: unproject-w-branch-uses-h  # y uses crop_h = 526.75. The inverse of M gives y = -10.774988810221336 (2.0e-5 more), because M[1][1] != M[0][0]
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [0, 0]
    center: [113.1500015258789, 252.59999084472656]
    crop_w: 395.0625
    crop_h: 526.75
  expect:
    source_xy: [-84.3812484741211, -10.775009155273438]
- id: unproject-aspect-ratio-not-kept  # x uses crop_w and y uses crop_h of direct-aspect-ratio-not-kept-uses-h
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [192, 256]
    center: [113.1500015258789, 252.59999084472656]
    crop_w: 189.625
    crop_h: 526.75
  expect:
    source_xy: [207.9625015258789, 515.9749908447266]
- id: unproject-pixel-std-200  # the same closed form with the pixel_std_200 values of pixel-std-200-h-branch
  function: unproject
  params:
    target_size: [256, 192]
  input:
    model_xy: [12.5, 200.25]
    center: [270.29998779296875, 180.0]
    crop_w: 375.7500305175781
    crop_h: 500.9999694824219
  expect:
    source_xy: [106.88786514600116, 321.39549919962883]
- id: pad-scalar-fills-every-channel  # the box is outside the 2 x 2 image: every output pixel is the border. A scalar fills all three channels
  function: affine_person_crop
  params:
    target_size: [4, 3]
    crop_policy: {pad_value: 7}
    interpolation: linear
  input:
    image:
    - - [0, 1, 2]
      - [3, 4, 5]
    - - [6, 7, 8]
      - [9, 10, 11]
    bbox_xyxy: [100, 100, 110, 120]
  compare:
    image: {atol: 0}
  expect:
    image:
    - - [7, 7, 7]
      - [7, 7, 7]
      - [7, 7, 7]
    - - [7, 7, 7]
      - [7, 7, 7]
      - [7, 7, 7]
    - - [7, 7, 7]
      - [7, 7, 7]
      - [7, 7, 7]
    - - [7, 7, 7]
      - [7, 7, 7]
      - [7, 7, 7]
- id: pad-array-per-channel  # one value for each channel, in the channel order of the image
  function: affine_person_crop
  params:
    target_size: [4, 3]
    crop_policy:
      pad_value: [1, 2, 3]
    interpolation: linear
  input:
    image:
    - - [0, 1, 2]
      - [3, 4, 5]
    - - [6, 7, 8]
      - [9, 10, 11]
    bbox_xyxy: [100, 100, 110, 120]
  compare:
    image: {atol: 0}
  expect:
    image:
    - - [1, 2, 3]
      - [1, 2, 3]
      - [1, 2, 3]
    - - [1, 2, 3]
      - [1, 2, 3]
      - [1, 2, 3]
    - - [1, 2, 3]
      - [1, 2, 3]
      - [1, 2, 3]
    - - [1, 2, 3]
      - [1, 2, 3]
      - [1, 2, 3]
- id: rule3-unknown-arithmetic
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: float64}
  expect:
    failed: [V-pre.resize.affine_person_crop-3]
- id: rule3-pixel-std-200-needs-maintain-aspect-ratio
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: pixel_std_200, maintain_aspect_ratio: false}
  expect:
    failed: [V-pre.resize.affine_person_crop-3]
- id: rule3-direct-is-valid
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: direct, maintain_aspect_ratio: false}
  expect:
    failed: []
- id: rule3-pixel-std-200-is-valid  # maintain_aspect_ratio is absent: the default true applies
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: pixel_std_200}
  expect:
    failed: []
- id: rule3-pixel-std-200-with-non-boolean-aspect  # maintain_aspect_ratio 1 is not a boolean: rule -1 fails. It is not false, so rule -3 passes. A check with "is not True" also fails rule -3
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: pixel_std_200, maintain_aspect_ratio: 1}
  expect:
    failed: [V-pre.resize.affine_person_crop-1]
- id: rule3-legacy-sidecar-must-not-have-arithmetic  # the field is marked (vNEXT). A legacy sidecar must not contain it, also with the value direct
  function: check_rules
  params: {schema_version: v2024.09.1019}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {arithmetic: direct}
  expect:
    failed: [V-pre.resize.affine_person_crop-3]
- id: rule3-legacy-sidecar-without-arithmetic  # no arithmetic field: rule -3 passes, and direct applies
  function: check_rules
  params: {schema_version: v2024.09.1019}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {expand_ratio: 1.25, maintain_aspect_ratio: true}
  expect:
    failed: []
- id: rule1-expand-ratio-not-positive
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    resize:
      method: affine_person_crop
      crop_policy: {expand_ratio: 0}
  expect:
    failed: [V-pre.resize.affine_person_crop-1]
```

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Step 4 (preprocessed input): for each image, the maximum absolute difference must be 0. This applies to the warped uint8 crop and to the normalized float32 tensor (`exporter-guide/sidecars/workflow/parity.md:28-32`; the user rule T2, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). Step 5 (keypoints after the unprojection): the difference must not be above the export error of step 3 (`exporter-guide/sidecars/workflow/parity.md:33-42`). Exact check without ONNX, for `direct`: run the mmpose inverse (`topdown.py:154-156`) and `unproject` of the reference file. Use the same decoded keypoints and the same metainfo. After the float32 store of mmpose, 0 float32 values must differ. For `pixel_std_200`: ViTAE `transform_preds` on heatmap cells `x_cell` against `unproject` on `4 x` the cells. `W` is the heatmap width. Each difference must be at most 3 ulp of float32 at `m = abs(x_cell * w / W) + abs(c_x) + w / 2`. The y axis uses `y_cell`, `h`, `H` and `c_y` in the same way. Source: the float32 noise of `transform_preds` (`post_transforms.py:180-192`; "the numeric floor of the upstream", `exporter-guide/sidecars/workflow/parity.md:17-19`). The bound: `w` and `c_x` are the same float32 values in both paths. `transform_preds` rounds `scale_x = w / W`, the product, the sum and the difference in float32. The error of `scale_x` times `x_cell` is at most 1 ulp at `m`. Each of the other three roundings is at most 0.5 ulp at `m`. The total is at most 2.5 ulp at `m`. The bound also holds when NumPy calculates in float64. Measured with scratch `gate.py` (NumPy 2.5.4): at most 1.47 ulp at `m`. The run used 2000 random boxes and 2000 boxes near the top-left image corner, each in 256 x 192 and 384 x 288. A gate at the value of the result is not sound. Near the image edge the result is near 0, and the difference was up to 262144 ulp at the result (at most 1.3e-4 px). |
| Test images (paths or dataset IDs), and the branch that each image runs | to run. Rule for the choice (`exporter-guide/sidecars/workflow/parity.md:20-25`). Use COCO val2017 person instances. Give the GT box as a float32 `xyxy` box. Use at least one wide box (h branch). Use at least one tall box (w branch). Use one box partly outside the image (border pixels). Use one box smaller than the target (upscale) and one larger (downscale). Use a portrait image and a landscape image. Add synthetic boxes on one of these images. Add a box with `bw = 0.75 bh` exactly (equal aspect). Add the box `[50, 60, 125.0075, 160.01]` (the float32 box decides the branch). Add the boxes of `direct-tie-strict-greater-keeps-h` and `direct-float32-product-decides-the-branch` (part 4). Add boxes near the left and the top image edge for the `pixel_std_200` Inverse gate. The run records the image IDs and the reason for each. For `pixel_std_200`, ViTAE gets `[x1, y1, x2 - x1, y2 - y1]` in float64 from the same float32 box, as its eval pipeline reads a detection file. |
| Upstream reference: library, version, config and command | `direct`: mmpose v1.3.2 in the exporter image (`mmdeploy-convert/CONFIG_SOURCES.md`). Use the `val_pipeline` of the DWPose config `configs/wholebody_2d_keypoint/rtmpose/ubody/rtmpose-m_8xb64-270e_coco-ubody-wholebody-256x192.py` and of the Halpe26 config of the intake. It runs `GetBBoxCenterScale` and `TopdownAffine`. Then run `inference_topdown` with float32 boxes. `pixel_std_200`: ViTAE `c050ed2` in `/opt/vitae` (plan T12): `_xywh2cs` and the non-UDP `TopDownAffine` of the ViTPose++ wholebody config and of the 25-point config of the intake. The command: to run. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run. No ONNX file of the four families exists in this exporter yet. |
| Preprocessed input: maximum absolute difference for each image | to run |
| Row count for each image: sidecar path and upstream | to run (one row for each box: a top-down model gives one pose for each box) |
| Final outputs in source-image coordinates: metric and value for each role | to run (`pose_estimator`: the maximum keypoint difference in pixels and the OKS; the exact check without ONNX of the gates row) |
| Result (`pass`, `fail` or `to run`) | to run |
| Script path in the exporter repo | unknown (the script does not exist yet). Suggested: `notes/decisions/scripts/affine_crop_parity.py`. It loads the reference file with `importlib.util.spec_from_file_location`. It runs the upstream pipeline in the container (no torch on the host, `AGENTS.md` section 4). It writes the crops, the tensors and the keypoints of both paths, and it compares them on the host. The parity runs of `normalize-arithmetic` and `heatmap-decode-refinement` can use the same ViTAE worker. |
| Exporter commit of the script | unknown (the script does not exist yet) |
| Command | to run |

The four T4b rows name the same gates (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts),
the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)). The ViTPose rows name step 4 against the pipeline in
`/opt/vitae` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). The D11 rows name step 5 (`dwpose:122`, `halpe26:142`, `vitposepp:138`, `coco25:151`).

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/affine_crop.py`. `bbox_xyxy2cs` (lines 68-85): cast the box to float32 first, and calculate in float32. `top_down_affine` (lines 88-109): do the aspect fix in float32 with `a = float32(T_w / T_h)` and `h = w / a`. Lines 98-104 now use the dtype of the input. Pass `interpolation` and a per-channel `pad_value` to `cv2.warpAffine` (line 107). A scalar fills every channel. `get_warp_matrix` (lines 33-65): for `direct`, put the second point left of the centre (`[src_w * -0.5, 0]`). Line 47 now puts it above the centre (`[0, src_w * -0.5]`, the rtmlib form). Keep that axis for `pixel_std_200`. Add `pixel_std_200_center_and_size` (new function). |
| Dispatch point | `preprocess_image`, branch `affine_person_crop` (`skellytracker/core/detectors/processing/image_preprocessing.py:217-231`): read `crop_policy.arithmetic`; replace the float64 default box (line 228) with a float32 box; return the float32 `(center, (w, h))` as `resize_meta`. |
| Validator changes (`model.py`, with rule IDs) | `CropPolicySpec` (`skellytracker/core/sidecar/model.py:67-75`): add `arithmetic: Literal["direct", "pixel_std_200"] = "direct"` and `pad_value`; check `V-pre.resize.affine_person_crop-3`: a legacy sidecar must not contain `arithmetic`; at `vNEXT`, `pixel_std_200` must not have `maintain_aspect_ratio` `false`. |
| Tests | The vectors of part 4 against `affine_crop.py` and `decode_simcc`. A golden parity test against mmpose output on real crops. The golden fixtures of `skellytracker/tests/sidecar/test_rtmpose_body_sidecar.py` (lines 30, 70) can change by float32 rounding: the change applies to the legacy package sidecars too (2.6). Regenerate them only after a check against mmpose. `test_full_image_bbox_matches_manual_affine_crop` (`skellytracker/tests/test_image_preprocessing.py:177`) must use the new points. |
| Existing code that the change touches | `affine_crop.py` (all functions); `image_preprocessing.py:217-231`; `simcc_decode.py:97-98` (`decode_simcc`: the closed form is already the Inverse; it must get the float32 `center` and `(w, h)` of the forward step and calculate in float64). For the implementer: the docstring of `decode_simcc` says `model_input_size : (H, W)` (line 87), but line 97 divides `(x, y)` by it and `simcc_pose_decode` says `(W, H)` (line 116). Check the order. |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` (writes `affine_person_crop`, `rtmw/preprocess.py:32-34`); planned `dwpose-wholebody133-ubody`, `rtmpose-halpe26` (mmpose 1.x); planned `vitposepp-wholebody133`, `vitpose-coco25` (ViTAE) | `rtmw-wholebody133`, DWPose and Halpe26: none (the default `direct` applies; no new field). OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMW sidecar until the RTMW intake is `describes`; the RTMW writer keeps `affine_person_crop` for that later round. `vitposepp-wholebody133` and `vitpose-coco25`: new field `crop_policy.arithmetic: pixel_std_200` when the user accepts the proposal (plan T5: do not write the new sidecars before that). | No host code exists. Plan step 5c: write the host crop and its Inverse from the reference file of part 3, and commit them. |
| Roboflow-Exporter | none (no `affine_person_crop`) | none | none |
| Ultralytics-Exporter | none (no `affine_person_crop`) | none | none |
| Qualcomm-Exporter | the MediaPipe face and hand landmark sidecars with `affine_person_crop` and `expand_ratio: 1.0` (section guidance, `resize-affine-person-crop.md:81`) | none in the files (`direct` applies) | for the implementer: its host must follow the `direct` steps. Its upstream (MediaPipe) uses a rotated ROI, which the spec does not describe (skellytracker decision 0020). |
| MediaPipe-Exporter | none (plans only; rotated crops) | none | none |
| The proposing exporter, if it is not in this table | (in the table) | | |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-face`, `rtmpose-hand`, `rtmw-wholebody`, all `v2024.09.1019` with `affine_person_crop` | none in the files. The scope of 2.6 applies the arithmetic to them. | `affine_crop.py` and `image_preprocessing.py` change (part 6). The crop pixels change by at most 1 in some crops. |

**Intake rows that this proposal closes.** Each row must link this file
(`specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`) and the reference file
(the part 3 code of `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`). This proposal does not change the
intakes. The T21 follow-up of the plan links them (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary).

| Intake | T4b row | D11 row | Spec defect text | Rows of "Proposals and reference files" |
|---|---|---|---|---|
| the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts) | line 94 | line 122 (`near-miss`) | line 243 (it says that the defect of T4b is now proposed) | row T4b, D11 (line 252; T4b row added 2026-10-23); the rows `pre.resize.affine_person_crop` (line 264) and `post.unprojection` (line 265) name the part 3 file |
| the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts) | line 114 | line 142 (`near-miss`) | line 264 (the same) | row T4b, D11 (line 273; T4b row added 2026-10-23); rows at lines 286-287 |
| the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) | line 111 | line 138 (`near-miss`) | none | line 274 links this file (2026-10-23); rows at lines 290-291 |
| the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts) | line 124 | line 151 (`near-miss`) | none | line 284 links this file (2026-10-23); rows at lines 296-297 |
| the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) | line 149 | line 177 (`near-miss`) | none | row T4b, D11 (line 313); reference row at line 328 |

With this proposal, the DWPose and Halpe26 T4b rows change from `unverified` to `near-miss`. The
reason: the measured crop of the current text differs from mmpose (part 1). Since the intake correction of 2026-10-24, the D11 rows of the four intakes (and of the RTMW intake, line 177) are `near-miss` (secondary): the current Inverse is the inverse of `M` (part 1 (3)).
Parity step 5 gives the primary evidence. With the proposed text they expect `exact`.

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep the current text (exact math, `h = w * (T_h / T_w)`, `M` from the `(w, h)` box, the Inverse as the inverse of `M`) | It gives other crop pixels than mmpose in 1911 of 2000 crops and other keypoints than the mmpose inverse (up to 7.3e-5 px). Parity step 4 expects 0, and the guide does not allow a larger tolerance. | part 1 (2) and (3); `exporter-guide/sidecars/workflow/phase-1-intake.md:67`, `exporter-guide/sidecars/workflow/parity.md:28-32` |
| Change only the aspect fix to `h = w / (T_w / T_h)`, with no dtype | The forward warp of mmpose does not use `h`. The 1-ulp fix alone changes no crop pixel. The float32 points cause the pixel differences. | part 1 (2): the float32 reading of the current text still differs in 1897 of 2000 crops |
| One text for all models: `direct` only, and ViTPose stays `near-miss` | The ViTAE crop differs from `direct` in 1280 of 2000 crops. The ViTPose T4b rows would stay `near-miss`, and the guide asks for a proposal for each near-miss. The user decided against this (A1, plan T23, 2026-10-24). | part 1 (2); `exporter-guide/sidecars/workflow/phase-1-intake.md:45-48` |
| An accuracy rule for `M` (a tolerance, as `normalize-arithmetic` does for its values) | The crop is uint8. A small difference in `M` changes a pixel by 1 (4 of 2000 crops for a difference of 1.8e-11). No tolerance on `M` gives 0 in step 4. The normalize values are float32 values with a tolerance of their own; the crop pixels are integers. | part 1 (2), the `numpy.linalg.solve` row |
| A tolerance for the preprocessed input (the intakes name it as an option) | The guide says: "Do not make the tolerance larger to pass" (`exporter-guide/sidecars/workflow/phase-1-intake.md:67`). The exact text exists and costs no new code path for mmpose 1.x. | the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) |
| A float64 text (exact math in float64) | It matches neither upstream: 1911 of 2000 crops against mmpose. | part 1 (2) |
| `crop_policy.arithmetic` as a number (`scale_unit: 200`) | `pixel_std_200` changes more than a unit. It also changes the order (the aspect fix before the expansion), the float64 steps, the float32 round trip and the axis of the second point. A number suggests other values that no upstream uses. | part 2.3; ViTAE `kpt_2d_sview_rgb_img_top_down_dataset.py:150-158`, `post_transforms.py:234` |
| The Inverse as the inverse of `M` (the current text) with the new `M` | mmpose and ViTAE use the closed form with `h`. The inverse of the float32-point `M` differs by up to 7.3e-5 px. | part 1 (3) |
| Scope option A: the heading "Arithmetic" only for `vNEXT` sidecars | The user chose option B for the sibling `normalize-arithmetic`, because no sidecar is deployed yet and all sidecars will be made again. The same reason applies here. Option A keeps `versioning.md:51` unchanged and lets a legacy host keep its arithmetic. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (T21 (3)), secondary |
| Ignore `crop_policy.arithmetic` below `vNEXT` (rule -3 only at `vNEXT`) | A legacy sidecar with `pixel_std_200` would load and get the `direct` crop with no error (1280 of 2000 crops differ). The forward step would need `schema_version`. The rejection has the form of `V-common.input-3`. The user decided against this (A3, option 1; plan T23, 2026-10-24). | part 1 (2); `common/input.md:60`; part 4, case `rule3-legacy-sidecar-must-not-have-arithmetic` |
| A third value now for the mmpose 0.x `bbox_xywh2cs` form (`TopDownGetBboxCenterScale`, `f32(w) / 200`) | No model in scope uses this step, and no exporter writes it. It needs its own steps, vectors and an upstream run. A model with this step is a `near-miss` until a proposal adds the value. The user decided against this (A4, option 1; plan T23, 2026-10-24). | 2.3, "Guidance"; mmpose v0.29.0 `mmpose/core/bbox/transforms.py:64`; part 4, case `pixel-std-200-is-not-the-mmpose-029-scale` |
| A third value for the rtmlib form (second point above the centre, dtype of the box) | No exporter writes it, and the upstream of the package RTMPose sidecars is mmpose 1.x. skellytracker changes its code (part 6). | skellytracker `affine_crop.py:47` |
| Restate the new text of `V-pre.resize.affine_person_crop-2` of the proposal `roi-transform-and-source` here, and key `check_rules` on `pose.estimator_type` in place of `requires_object_detector` | The new text names `rotated_roi_crop`, which only that proposal adds, and it follows from the removal of `pose.requires_object_detector` in that proposal (user decision T22 (1)). A copy of the text would make this proposal depend on that proposal, and two copies of one rule can drift. This proposal does not change rule -2, and its vectors need no `pose` block. Thus this proposal leaves rule -2 to that proposal, and `check_rules` checks only `-1` and `-3` (part 3). The removed vector `rule2-top-down-needs-affine-crop` tested only the legacy text of rule -2. | MediaPipe-Exporter `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`, part 2.4 (lines 485-495), part 3 (lines 592-593), part 6 (line 1660); lines checked again on 2026-10-24 by the review-readiness audit 2 |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. The four intakes link it in "Proposals and reference
      files" (part 7 gives the lines; completeness review of 2026-10-23). The DWPose and Halpe26 rows
      T4b have the verdict `near-miss` (the T21 follow-up; checked again on 2026-10-24). The RTMW intake (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)) (row T4b, line 149, `near-miss`; row D11, line 177, `near-miss`; proposals row, line 313; reference row, line 328) links it too. The D11 rows of the four intakes link it too (part 7).
- [x] The header gives the dependencies, or `none`. It names the related proposal
      `roi-transform-and-source` (rule -2, `V-common.input-4` and the sentence on rotated crops).
      This proposal does not use `pose.requires_object_detector` (user decision T22 (1),
      2026-10-24): `check_rules` checks rules -1 and -3 only.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it. (none)
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plans folder of OpenMMLab-Exporter (plan facts).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. The two pad cases have
      `compare: {image: {atol: 0}}`. Every output pixel is a border pixel, so the interpolation does
      not change it.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [x] n/a: If the result of part 5 is `pass` or `fail`, the parity script is committed in the
      exporter repo. (`to run`)
- [x] No file in skellytracker changed.
- [x] The exception sentence of 2.1 (row `format.versioning`) has the same text in
      `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md`. It names `V-pre.normalize-3` since the
      user decision N1 of normalize-arithmetic (plan T23, 2026-10-24).
- [x] The user decides A1 to A4 (plan T23, 2026-10-24): A1, the field `crop_policy.arithmetic`
      (`direct`, `pixel_std_200`); A2, the single-`pad_value` rule stays here; A3, option 1 (reject
      the field below `vNEXT`); A4, option 1 (no value for mmpose 0.x). These are the choices of
      the proposal, so the normative text of part 2 does not change.

This proposal has `to run` in part 5. The user decided A1 to A4 (header; plan T23, 2026-10-24). It is ready for a
skellytracker session to record. It is not ready for the user to accept.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal. The list is of
2026-10-25. Line numbers are on the working branch `dom/sidecar-implementation`.

**Parts**

- [ ] The docstring of the reference code cites an untracked plan path, the plan decision T22 (1)
  and skellytracker commits that are not on `development`. Remove these citations before the code
  goes into `specs/model-sidecar/reference/`.
- [ ] Part 2.1 does not list each place that the change edits. Add these places:
  - `tools/tests/test_vectors.py`: `test_file_has_the_documented_top_level_keys` (lines 128-141,
    `generated_by` must be `tools/make_vectors.py`), the rule that a case has `tolerance` only when
    a value has a fraction (lines 169-180), the 16 KiB limit of `test_file_is_small` (lines
    184-185), `test_affine_person_crop_anchors` (line 244), `_forward_matrix` and
    `test_unprojection_inverts_the_forward_map` (lines 512-556), `forward_matrix` and
    `test_the_unprojection_inverts_the_resize_of_the_case` (lines 587-609 and 653-657). The last
    four functions use the inverse of `M`.
  - A doc test in `tools/tests` that runs each reference function against the vectors of its
    section ([0013](../../../../notes/decisions/0013-spec-structure.md), line 152). No such test
    exists.
  - `specs/model-sidecar/templates/model-intake.md`, lines 249-255 and row T6 (line 267). After A2, the
    text "The spec does not say yet what a scalar fills" is false.
  - `specs/exporter-guide/sidecars/workflow/mapping-hints.md`, lines 46-54: the same scalar
    `pad_value` text.
  - `specs/model-sidecar/changelog.md`, line 57: "Sidecars with `schema_version < vNEXT` ... keep loading
    unchanged under the legacy rules". The new "Compatibility impact" bullet of 2.7 contradicts it.
  - `notes/decisions/open-work.md`, line 162 ("the resizes run on the source dtype"). The 2.3
    sentence "The host warps the source image in its own dtype" closes this item for
    `affine_person_crop`.
- [ ] Part 2.1, row `tools/make_vectors.py`, says that `affine_crop` and `affine_unproject` of the
  generator must use the float32 steps. Decision 0013 (lines 165-166) and the skill
  `change-sidecar-spec` (step 8 of the procedure for an accepted proposal) say that the generator
  calls the reference implementation of the section. Correct the row.
- [ ] Part 2.1 says that the 7 existing vector cases keep their values. Part 4 says that the vector
  file does not change, and 2.1 adds 28 cases to it. A generator that uses the float32 steps gives
  other printed values for the existing cases at `ROUND_DIGITS` 6. For example, `crop_h` of
  `wide-box-grows-height` changes from 666.666667 to 666.666687. Make the three statements agree.
- [ ] Part 2.6 says that `pad_value` has the same meaning in a legacy sidecar. The sentence "A
  scalar `pad_value` fills every channel" is in the heading "Arithmetic", and that heading applies to
  every `schema_version`. Thus the scalar rule also applies to a legacy sidecar. State this in 2.6
  and in the "Compatibility impact" bullet of 2.7.
- [ ] Part 2.1, row `tools/tests/test_vectors.py`, takes the conversion of the case form from the
  proposal `simcc-score-rule`. The header gives "Depends on: none". State the dependency, or give
  the conversion in this proposal.
- [ ] The header row "Exporter commit" says that `f3aeb47` is "not pushed". The commit is on
  `origin/main` of OpenMMLab-Exporter. Correct the note.

**Evidence**

- [ ] Part 5 is `to run`. Write the parity script, and commit it in OpenMMLab-Exporter. Run mmpose
  v1.3.2 for `direct` and ViTAE `c050ed2` for `pixel_std_200`. Record the images, the numbers, the
  script commit and the command.
- [ ] The upstream code did not run. The numbers of part 1 and of 2.3 "Guidance" (for example 1911
  of 2000 crops and 7.3e-5 px) come from NumPy copies of the upstream lines in scripts that are not
  committed. They are not evidence. Commit the scripts, or replace the numbers with the results of
  the parity run.
- [ ] No ONNX file of the four families exists. The effect on the keypoints is not measured.
- [ ] The dtype of the ViTAE Inverse depends on the NumPy version. The value 1.6e-4 px is for NumPy
  2.5.4 only.
- [ ] No host implementation exists, so the vectors of part 4 are `unverified`. A read-only check of
  2026-10-25 ran the 43 cases against the reference code (NumPy 2.4.6, OpenCV 4.13.0): 43 of 43
  pass. That check is not a host implementation.
- [ ] Part 1 cites mmpose v1.3.2 by its tag through `raw.githubusercontent.com`. The decision-log
  rules require a GitHub permalink with a full SHA on the default branch. Get the SHA of the tag.
  The user must also decide the citation rule for upstream repositories that are not exporters.

**Template checklist**

- [ ] The item "Part 2.1 lists each place that the change edits" is ticked, but it fails. See
  **Parts**.
- [ ] The item "Part 3 names the reference file, and the file exists" is ticked. The code is not in
  this file. See **Parts**.
- [ ] The template says "In each docstring, cite the proposed section ID". In the reference code,
  the docstring of `_round32` does not cite the section ID, and `_is_number` has no docstring.

**Vectors and tooling**

- [ ] The cases of part 4 use the template form: `function`, `compare`, and `generated_by` that
  names the reference code. `tools/tests/test_vectors.py` rejects this form. Decide the case form
  one time for all proposals with vectors. Do it in a non-spec tools PR before the content PRs.
- [ ] The vector file with the new cases is about 17.6 KB (an estimate). `test_file_is_small` allows
  less than 16 KiB. Raise the limit, split the file, or remove cases.
- [ ] The new cases need exact float32 values, but `ROUND_DIGITS` is 6. Decide the number format for
  this section, or for all sections.
- [ ] `specs/model-sidecar/reference/` does not exist. This reference code can be the first file in it.
  Decide how `tools/make_vectors.py` and the tests import it.
- [ ] `check_rules` of the reference code treats each `schema_version` that is not the literal
  `vNEXT` as legacy. When a release replaces `vNEXT`, a sidecar at that release fails rule -3.
  Decide how the reference code compares versions.

**Decisions for the user**

- [ ] Retroactive scope. The heading "Arithmetic", the closed-form Inverse and the scalar
  `pad_value` rule apply to every `schema_version`. This contradicts `AGENTS.md` section 4 ("The
  meaning of an older `schema_version` never changes"), `format/versioning.md` line 51, the
  change proposal template (lines 178 and 364), the heading "Legacy behaviour" of the skill
  `change-sidecar-spec`, `changelog.md` lines 30 and 57, and decision
  [0009](../../../../notes/decisions/0009-imagenet-bgr-meaning.md). The output of the four package
  sidecars changes by float32 rounding, and some crop pixels change by 1. The exporter plan decision
  T21 (3) is for `normalize-arithmetic` only. This proposal applies it by analogy. Accept or reject
  this exception. Decide if decision 0009 needs a new entry that supersedes it.
- [ ] Confirm the user decisions that exist only in the untracked pose-models plan of
  OpenMMLab-Exporter: T2, T5, T12, T21 (2), T21 (3), T22 (1) and T23 (A1 to A4).
- [ ] Decide if `cv2.getAffineTransform` is normative for `M`. 2.3 names it. The guidance allows
  `numpy.linalg.solve` with a stated cause, but that solver changes 1 pixel by 1 in 4 and 5 of 2000
  crops. Then parity step 4 is not 0.
- [ ] Legacy policy. Rule -3 rejects a `vNEXT` field in a legacy sidecar. Other proposals use a
  legacy row only, or an error at decode. Decide one policy for all proposals.
- [ ] Version-aware compatibility. This proposal adds a link to its new "Legacy behaviour" heading in
  `format/versioning.md`. Some proposals do not add a link, and `resize-fit.md` and
  `resize-stretch.md` have no link now. The skill `change-sidecar-spec` requires the link for a new
  "Legacy behaviour" heading. Decide one rule.
- [ ] Pixel centres. The heading "Arithmetic" gives the mmpose crop bit for bit through
  `cv2.warpAffine`. `cv2.warpAffine` puts the pixel centres at integer coordinates.
  `pre/interpolation.md` says "half-pixel centres" for `cv2.warpAffine`. The open-work items at
  lines 137-140 and line 176 stay open. Decide if the text can stand.
- [ ] Decisions [0013](../../../../notes/decisions/0013-spec-structure.md) (line 149) and
  [0014](../../../../notes/decisions/0014-spec-lifecycle.md) (line 171) say "There is no reference
  implementation yet". This becomes false when the first reference file lands. Decide how to record
  it.
- [ ] Decide if the landing session can remove the plan paths and the commits from the reference
  docstring, or if the exporter must do it first.

**Merge points**

- [ ] `normalize-arithmetic`
  ([0043](../../../../notes/decisions/0043-normalize-arithmetic.md)). The two proposals share one
  exception sentence after `format/versioning.md` line 51. Add it one time. If
  `normalize-arithmetic` lands alone, remove the part of this proposal. Its link to
  `../pre/resize-affine-person-crop.md#arithmetic` fails the link test until this proposal lands.
  Both proposals also edit `open-work.md` line 168 and the "Compatibility impact" list.
- [ ] `roi-transform-and-source` (MediaPipe-Exporter,
  [0020](../../../../notes/decisions/0020-roi-transform-and-source.md)). Both proposals edit the
  front matter, "Behaviour" line 41, the "Validation rules" (rule -2 there, rule -3 here),
  "Authoring guidance" lines 76-81 of the section file, `V-common.input-4` (add `arithmetic` to its
  closed key set) and row T4b of `model-intake.md`. Either can land first. The content PR that lands
  second rebases. That proposal puts the legacy text of rule -2 in `post.pose.schema`. This proposal
  adds a "Legacy behaviour" heading to this section. The skill `change-sidecar-spec` puts each
  legacy difference in the "Legacy behaviour" heading of its section. Decide where the legacy text
  of rule -2 goes.
- [ ] `pose-decode-flip-test`
  ([0045](../../../../notes/decisions/0045-pose-decode-flip-test.md)) edits "Implementer guidance"
  line 72 of the section file.
- [ ] `heatmap-decode-refinement`
  ([0038](../../../../notes/decisions/0038-heatmap-decode-refinement.md)) maps the heatmap cells to
  model-input pixels before this Inverse. One parity script and one ViTAE worker can serve both.
- [ ] `simcc-score-rule` ([0024](../../../../notes/decisions/0024-simcc-score-rule.md)),
  `heatmap-decode-refinement`, `model-id-suffix`
  ([0025](../../../../notes/decisions/0025-model-id-suffix.md)), `size-codes`
  ([0046](../../../../notes/decisions/0046-size-codes.md)) and `keypoint-visibility`
  ([0039](../../../../notes/decisions/0039-keypoint-visibility.md)) also edit the list of
  `format/versioning.md` lines 53-63, the `changelog.md` rows, `BUILDERS` of
  `tools/make_vectors.py` and `CASE_KEYS` of `tools/tests/test_vectors.py`.
- [ ] All 13 spec proposals add a row to "Summary of changes" and a sentence to the `vNEXT` row of
  `changelog.md`.
- [ ] Landing order: the non-spec tools PR for the vector form, then `normalize-arithmetic`, then
  this proposal. This proposal and `roi-transform-and-source` can change places. Confirm the order.
