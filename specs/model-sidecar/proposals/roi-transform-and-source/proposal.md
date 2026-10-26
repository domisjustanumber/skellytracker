---
slug: roi-transform-and-source
section: pre.resize.rotated_roi_crop
exporter: MediaPipe-Exporter
decision: "0020"
state: recorded
---
# Change proposal: roi-transform-and-source

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The MediaPipe-Exporter file of the proposal `roi-transform-and-source`, and its reference file, which is the `python` code block of part 3. Commit `none (no git repo)`. Copied on 2026-10-25. MediaPipe-Exporter has no git repo. Its paths in this file are not pinned. The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It is a local working note of
MediaPipe-Exporter (decision 0001). Git does not track it. It is the full phase 2 proposal of the
skellytracker gap record 0020. It gives the eight parts that 0020 does not have.

Labels in this file:

- **User decision (2026-10-23)** and **user decision (2026-10-24)** mark a decision of the user. Do
  not change it without the user. The decisions of 2026-10-24 are T22, T23 and T24 of
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (section 2.1, secondary), and the decision
  Q7 = (c) of the same day. T28 (H6) of the same plan gives one parity script to the four MediaPipe proposals (part 5).
- **Proposal choice** marks a choice of this proposal. On 2026-10-24 the user decided every open
  question. "Open questions for the user" lists each decision.

Line numbers of skellytracker files are at commit `dom/21-move-sidecar-guide` (re-pinned on 2026-10-25 from `dom/18-agents-adr-bootstrap-kit`;
first pinned at `dom/12-single-working-branch`). Between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide` the files under `specs/model-sidecar/` changed
only in link text, and no cited spec line moved. Guide citations use the 0034 layout
(`specs/exporter-guide/sidecars/`). The files that moved lines after `dom/18-agents-adr-bootstrap-kit` are
`notes/decisions/README.md`, `notes/decisions/open-work.md` and `tools/check_decision_log.py`; their
citations are at `dom/21-move-sidecar-guide`. History: at the re-pin of 2026-10-24 (`dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`), the cited
spec files had no change except `specs/model-sidecar/templates/change-proposal.md:62` (one line changed) and
the old guide file `specs/model-sidecar/exporter-guide.md` (one line less after line 445); skellytracker 0034
later moved that guide to `specs/exporter-guide/sidecars/`. The "Open work" of the decision-log
index moved to `notes/decisions/open-work.md`; the citations of both files are at `dom/21-move-sidecar-guide`. Line numbers of `docs/mediapipe-whole-body.md` are in
MediaPipe-Exporter, on 2026-10-23. Line numbers of this file and of the refiner proposal changed on
2026-10-24. A citation of the form "(0020 proposal `:N`)" in the refiner proposal names a line of
2026-10-24.

## Header

| Field | Value |
|---|---|
| Title | A rotated ROI crop for a top-down model whose ROI does not come from a detector box: the ROI, the ROI transform, the crop and its inverse |
| Slug | `roi-transform-and-source`. This is the slug of the skellytracker gap record 0020 (`notes/decisions/0020-roi-transform-and-source.md`; index row at `notes/decisions/README.md:39`). The exporter guide says: use the slug of a `proposed` entry that covers your rows (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:13-20`). |
| Date | 2026-10-23; updated 2026-10-24 (user decisions T22, T23, T24 and Q7 = c); updated 2026-10-25 (re-pinned to skellytracker `dom/21-move-sidecar-guide`; citation repairs of the decision-log lines; repo names on decision numbers) |
| Exporter repo | MediaPipe-Exporter |
| Exporter commit | none (no git repo) |
| Model, and its intake file | Two inputs of the MediaPipe Holistic hand branch: (1) the hand landmark model `hand_landmark_full` (224², ONNX `model_cache/onnx/hand_landmark_full.onnx`, input `input_1` float32 `[1, 3, 224, 224]`); its `model_id` is `mediapipe-hand21` by the T14 format `{family}-{keypoints}` (the current rule `{family}-{part}` gives `mediapipe-hand`; the inventory key today is `mediapipe-hand-landmark@mediapipe-exporter`, `specs/model-sidecar/inventory.yaml:115-121`; skellytracker 0025); (2) the input crop of the hand ROI refinement model `mediapipe-hand-roi` (256², input `input_1` float32 `[1, 3, 256, 256]`), the subject of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`. Intake files (written 2026-10-24): the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts) (the hand landmark model) and the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) (the hand ROI refinement model). |
| Intake rows with the verdict `near-miss` or `gap` | the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts) (2026-10-24): T2 resize method (`gap`); T2a the ROI that the crop receives, the start of the runtime contract (`gap`); T4 scale factor (`gap`); T4b arithmetic (`gap`); T6 border value, `BORDER_REPLICATE` (`gap`); T7a resize call and pixel centres (`gap`); T7b image dtype at the resize (`gap`); T8 crop policy, no `keep_aspect_ratio` and no transform (`gap`); D11 unprojection, the inverse of a rotated crop (`gap`); K1 estimator type and `requires_object_detector` (`near-miss`: the field exists, but no value fits a top-down model without a detector box; by user decision T22 (1) this proposal removes the field, part 2.1). the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) (2026-10-24): T2, T2a, T4, T4b, T6, T7a, T7b (`gap`); T8 crop policy, the loose-ROI transform and `keep_aspect_ratio` (`gap`); D11 the inverse of the input crop (`gap`, with the refiner proposal). Row T10 of both intakes is `unverified`; it is not a row of this proposal. Also the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked blazepose plan of MediaPipe-Exporter (plan facts), the BlazePose pose landmark model, a 256 x 256 crop): T2, T2a, T4, T4b, T6, T7a, T7b, T8 and D11 (`gap`) and K1 (`near-miss`). They are the same properties as in the hand landmark model. The section needs no new value for them. |
| Kind | `new section` (with edits to `common.input`, `common.sizes_and_artifacts`, `common.outputs` (an example), `pre.resize.interpolation`, `pre.normalize`, `pre.resize.affine_person_crop`, `post.pose.schema`, `post.pose.canonical_mapping` (guidance), `post.unprojection`, `format.composition` (an example), `format.versioning`, the templates, the exporter guide and the changelog). By user decision T22 (1) (2026-10-24), the change also removes the field `pose.requires_object_detector` from the spec (part 2.1, heading "Removal of `pose.requires_object_detector`"). |
| Proposed section ID | `pre.resize.rotated_roi_crop` (user decision T23, Q1 = a, 2026-10-24) |
| Section file | `specs/model-sidecar/pre/resize-rotated-roi-crop.md` |
| Depends on | none. 0020 names two dependencies (`0020-roi-transform-and-source.md:21-22`). (1) Rotated crops (the changelog row `crop_policy.border_mode, rotated crops`, `specs/model-sidecar/changelog.md:45`): this proposal contains them. The new method is the rotated crop, and it has `crop_policy.border_mode`. (2) The ROI refiner gap: **user decision (2026-10-23)**: this proposal lands before the ROI refiner proposal, and the refiner proposal depends on this one. This section does not need the refiner, because this section does not say how the host makes the ROI (part 2.3, heading "ROI source"). The refiner proposal declares the loose-ROI rule in the refiner sidecar (user decision T24, 2026-10-24). That is a field of `post.roi_refiner`, not of this section. **Related (not a dependency):** the OpenMMLab-Exporter proposal `affine-crop-arithmetic` (OpenMMLab-Exporter `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`, read only). Its "Depends on" is `none`, and either proposal can land first. Two places overlap, and the content PR that lands second must rebase on the first. (1) "Behaviour" of `pre.resize.affine_person_crop`: this proposal changes the sentence "Rotated crops are out of scope." (part 2.1, the row of `resize-affine-person-crop.md:41`). That proposal replaces "Behaviour" with the text of its 2.3, which has the same sentence. The second PR keeps the text of this proposal for this sentence. (2) `V-common.input-4`: this proposal makes the keys of an `affine_person_crop` `crop_policy` a closed set, `expand_ratio`, `maintain_aspect_ratio` and `pad_value` (part 2.4). That proposal adds `crop_policy.arithmetic`. If both land, the set must also contain `arithmetic`. The content PR that lands second does this edit. (That proposal gives the same notes in its header row "Depends on" and in its 2.1 row `common.input`.) |
| Needed by | `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`: its header "Depends on" (1), its Behaviour steps 2, 4 and 5, its fields `roi_decode.transform`, its rule `V-post.roi_refiner-8`, and its reference file, the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`. That file loads `roi_is_valid`, `transform_roi`, `unproject_points` and `validate_crop_policy` of the reference file of this proposal. It has no copy of them (the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`). Its earlier PROVISIONAL functions `crop_points_to_source` and `transform_roi` are deleted (refiner proposal part 3, `:880-883`). Part 7 lists what the refiner proposal had to change. The refiner proposal applied items 1 to 16 (its "Before you stop", `:4098-4100`). Also the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (the spec proposal "rotated ROI (with skellytracker 0020)"). `specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md` (the full proposal of skellytracker 0021): its header "Depends on" names this proposal; its Behaviour step 4 rotates the world keypoints by the rotation of the crop ROI `Rc` of `rotated_roi_crop`. `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md` (the full proposal of skellytracker 0022): its header "Depends on" names this proposal; its factor `k` of `rotated_roi_crop` uses the crop ROI `Rc` and the input of part 7 ("Input for skellytracker 0022"). **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide`, as in the rest of this file. No spec line that this row cites moved between `dom/12-single-working-branch` and `dom/21-move-sidecar-guide`. `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter), `roi-refiner-role`, `landmark-extra-outputs`, `landmark-depth-divisor`; `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `simcc-score-rule` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `affine-crop-arithmetic` (OpenMMLab-Exporter), `model-id-suffix` (OpenMMLab-Exporter), `size-codes` (OpenMMLab-Exporter); `common/input.md:61` (`V-common.input-4`: `arithmetic` joins the closed `crop_policy` key set): `affine-crop-arithmetic` (OpenMMLab-Exporter); `pre/resize-affine-person-crop.md:39-53` and `:63-68` ("Behaviour" with the sentence "Rotated crops are out of scope." at `:41`; "Validation rules" `-2` and `-3`; `roi-transform-and-source` owns `V-pre.resize.affine_person_crop-2`): `affine-crop-arithmetic` (OpenMMLab-Exporter); `pre/resize-affine-person-crop.md:76-81` ("Authoring guidance"): `affine-crop-arithmetic` (OpenMMLab-Exporter); `pre/normalization.md:47-53` ("Behaviour"): `normalize-arithmetic` (OpenMMLab-Exporter); `post/pose-schema.md:117-127` ("Validation rules": `-1` and `-2` owned by `roi-transform-and-source`, `-7`, `-9`, the "See also" line): `landmark-extra-outputs`, `landmark-depth-divisor`, `pose-decode-flip-test` (OpenMMLab-Exporter), `keypoint-visibility` (OpenMMLab-Exporter); `post/pose-schema.md:137-144` ("Authoring guidance"): `landmark-extra-outputs`; `post/unprojection.md:21-36` ("Behaviour" and the list of inverses): `roi-refiner-role`, `landmark-depth-divisor`; `post/unprojection.md:51-66` ("Implementer guidance", next bullets): `nms-clamp-order` (OpenMMLab-Exporter); `format/composition.md:63-74` (the RTMW excerpt): `model-id-suffix` (OpenMMLab-Exporter); `exporter-guide/sidecars/workflow/phase-1-intake.md:14-16, 30-32` (phase 1 step 1, the verdict `gap`): `roi-refiner-role`; `templates/model-intake.md:113, 118-119` (verdicts): `roi-refiner-role`; `templates/model-intake.md:264` (row T4b): `affine-crop-arithmetic` (OpenMMLab-Exporter); `templates/model-intake.md:300` (row D11): `landmark-depth-divisor`; `inventory.yaml:98-129` (the `proposed` entries): `model-id-suffix` (OpenMMLab-Exporter), `roi-refiner-role`, `landmark-extra-outputs`; the reference examples under `examples/detectors/keypoint_detectors/` (`rtmo`, `rtmw`, `yolo26`): `model-id-suffix` (OpenMMLab-Exporter), `size-codes` (OpenMMLab-Exporter); `changelog.md` "Considered and deliberately not added": `nms-clamp-order` (OpenMMLab-Exporter); `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule` (OpenMMLab-Exporter), `heatmap-decode-refinement` (OpenMMLab-Exporter), `normalize-arithmetic` (OpenMMLab-Exporter), `affine-crop-arithmetic` (OpenMMLab-Exporter), `model-id-suffix` (OpenMMLab-Exporter), `landmark-extra-outputs`, `landmark-depth-divisor`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). **Merge point of the decision log (user decisions T34 (N2) and T35, 2026-10-24):** skellytracker `notes/decisions/0008-vnext-scope.md` (the scope list `:8-15`, the "not added" groups `:21` and `:24`): `nms-clamp-order` (OpenMMLab-Exporter). By T35, each of the two proposals puts its scope change into a small scope entry that holds only scope rules: entry B (`SSSS-vnext-scope-nms-filters.md`) of `nms-clamp-order`, and the scope entry `RRRR` of this proposal (heading "Scope entry (user decision T35)"). The feature rules stay in the other entries: the NMS entry A of `nms-clamp-order` supersedes only 0011, and the main entry of this proposal (0020) supersedes no entry. Thus only the two scope entries meet. The scope change that lands second supersedes the scope entry in force (0008, or the scope entry of the first proposal) and restates its scope rules with its own change. If entry B lands first, the scope entry of this proposal supersedes entry B and restates its NMS change: `nms.pre_nms_top_k` and `nms.min_bbox_size` are not in the "not added" list (heading "Scope entry (user decision T35)", the variant). If the scope entry of this proposal lands first, entry B supersedes it and restates MediaPipe-Exporter in the scope and the resize change of this proposal. Neither proposal restates the feature rules of the other. |
| skellytracker decision entries with the status `proposed` that cover the same property | **0020** (gap record, `0020-roi-transform-and-source.md:8-9`). This file is its full proposal. It does not compete with 0020. Part 8 says where it differs from the direction of 0020 (`:11-19`), with the reasons. **0021** (gap record): the extra outputs of the hand landmark model. Not covered here. Its full proposal is `specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md` (section `post.pose.extra_outputs`). **0022** (gap record): the depth divisor. It must also say how the host unprojects a `pixel` depth (`0022-landmark-depth-divisor.md:15-16`). Part 2.3 and part 7 give the input that this section gives to 0022. Its full proposal is `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md` (section `post.pose.decode.coordinate`, heading "Depth"). **0025** (gap record): the `model_id` of the hand landmark model. Not covered here. Its full proposal is the OpenMMLab-Exporter proposal `model-id-suffix` (OpenMMLab-Exporter `specs/model-sidecar/proposals/model-id-suffix/proposal.md`, read only). **0019** (proposed): the batch axis of `outputs[].shape`. Not covered here. |
| Evidence basis | **User decision (2026-10-23): the user designated `docs/mediapipe-whole-body.md` as checked primary evidence.** The exporter guide classes the notes of an exporter as secondary (`specs/exporter-guide/sidecars/rules.md:9-13`). This document is an exception by that decision: each of its claims has a source check at MediaPipe commit `e9794ef55e2509c09aa8b6ba1764b797db8eb200` and at `v1.1.1` (`docs/mediapipe-whole-body.md:14-29`; MediaPipe-Exporter 0021 and 0029). This proposal cites it with `path:line` as primary evidence. It does not check its facts again upstream. Part 1 names the other sources, each for a fact that the document does not cover. |
| User decisions (2026-10-23) | (1) Keep this proposal separate from the ROI refiner role proposal. (2) This proposal goes into `vNEXT`. (3) It lands before the ROI refiner proposal, because the refiner proposal depends on it. (4) `vNEXT` also needs MediaPipe-Exporter in the scope of skellytracker 0008 (accepted). A small scope entry supersedes in full the scope entry in force at merge time, with that change (part 2.1; user decisions T34 (N2) and T35 of 2026-10-24 revise the earlier form "a new entry extends that scope"). (5) `docs/mediapipe-whole-body.md` is checked primary evidence (row above). (6) In the refiner proposal (its Q5 = a): an ROI whose width or height is 0 or less gives "no ROI". This answers the `w` and `h` part of Q9 of this proposal. |
| User decisions (2026-10-24) | T22 (1): remove the field `pose.requires_object_detector` from the spec (Q3; part 2.1, heading "Removal of `pose.requires_object_detector`"). T22 (2): one `scale` (Q5). T23: Q1 (a), Q2 (a), Q4 (required, no default), Q6 (the exact inverse), Q8 (pose estimators only), Q9 (an ROI with a NaN or infinite value gives "no ROI"), Q10 (a), Q11 (`linear` only), Q12 (a). T24: the refiner sidecar declares how the host makes the loose ROI from the body pose (refiner proposal). Q7 = (c): the spec states no arithmetic precision, and the vectors give the tolerances. T35: the scope change goes into a small scope entry that holds only scope rules (part 2.1; Q10; heading "Scope entry (user decision T35)"). "Open questions for the user" lists each decision. No question of this proposal stays open. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (`git status --porcelain` lists no file that this proposal read; re-pinned on 2026-10-25 from `dom/18-agents-adr-bootstrap-kit`). History: re-pinned on 2026-10-24 at `dom/18-agents-adr-bootstrap-kit` (`git status --porcelain` was empty). First read at `dom/12-single-working-branch`. Re-read on 2026-10-24 at `dom/14-decision-log-growth`: the cited spec files have no change except the two lines named at the top of this file. At that re-read, `git status --porcelain` listed `AGENTS.md`, `notes/decisions/0026-decision-log-size.md`, `notes/decisions/README.md` and a new `notes/decisions/0029-decision-log-read-path.md`. `git diff --stat dom/14-decision-log-growth dom/18-agents-adr-bootstrap-kit -- specs/model-sidecar` is empty, and this file cites no `.claude` line. This file cites `notes/decisions/README.md`, `notes/decisions/open-work.md` and `tools/check_decision_log.py` at `dom/21-move-sidecar-guide`. Guide citations point to the 0034 layout at skellytracker `dom/21-move-sidecar-guide`. Between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide` the spec text under `specs/model-sidecar/` changed only in link text (`git diff --stat dom/18-agents-adr-bootstrap-kit dom/21-move-sidecar-guide -- specs/model-sidecar`: `TRACEABILITY.md`, `common/identity.md`, `common/sizes-and-artifacts.md`, `format/file-layout.md`, `inventory.yaml`, `post/selection-nms.md`, `post/selection-top-k.md`, the two templates, and the removed `exporter-guide.md`); no cited spec line moved. |

## 1. Gap

This part cites skellytracker 0020 (gap record, `notes/decisions/0020-roi-transform-and-source.md`).
0020 gives the gap and the direction: a top-down crop whose ROI does not come from a detector box
(`:11-16`), the `RectTransformation` fields `shift_x`, `shift_y`, `square_long` and `scale`
(`:16-17`), and a spec definition of the ROI (`:17-18`). The rule that makes the ROI from keypoints
stays outside the sidecar (`:18-19`). This section keeps that line: it does not say how the host
makes the ROI. By **user decision (2026-10-24, T24)**, the refiner sidecar declares the rule that
makes the loose hand ROI from the body pose. That is a field of `post.roi_refiner` (refiner proposal,
part 2.3, heading "ROI source"). It differs from 0020 `:18-19` (part 8). 0020 depends on rotated
crops (`:21-22`). This proposal gives
the eight parts that 0020 does not have (`:8-9, 19-21`).

**Evidence basis.** **User decision (2026-10-23):** `docs/mediapipe-whole-body.md` is checked
primary evidence. This part cites it as primary, and it does not check its facts again upstream.

| Item | Value |
|---|---|
| Property | The MediaPipe Holistic hand branch crops the input of each hand model from a rotated ROI. The ROI does not come from a detector box. The host makes it from three pose keypoints (the loose ROI of the refiner), or the refiner makes it (the ROI of the hand landmark model), or the previous landmarks make it (tracking). An ROI is `(cx, cy, w, h, rotation)`, rotation clockwise in radians. Before the crop, MediaPipe changes the ROI with `RectTransformation`: a shift along the axes of the ROI, then `square_long`, then a scale. The crop maps the rotated ROI onto the corners of the model input, with bilinear sampling and a border mode (`BORDER_REPLICATE` for both hand models). With `keep_aspect_ratio`, MediaPipe first enlarges the ROI to the aspect ratio of the input. The host maps the model outputs back with the inverse of the crop. |
| Upstream evidence | **Primary** (`docs/mediapipe-whole-body.md`, user designation): `:58-61` (a rect is `(x_center, y_center, width, height, rotation)`; rotation clockwise, in radians; the rect calculators compute in pixels); `:81-87` (`RectTransformation`: shift along the rect's own axes by `shift_x · width` and `shift_y · height`, then `square_long` in pixels, then scale); `:94-101` (the rotated crop: `cv::boxPoints`, `getPerspectiveTransform` onto the tensor corners, `warpPerspective`, `INTER_LINEAR`, border `BORDER_ZERO` or `BORDER_REPLICATE` with `BORDER_REPLICATE` as the default, `keep_aspect_ratio` off by default); `:106-116` (the crop matrix; the hand ROI refinement graph maps its points with it; the landmark projection uses the rect); `:147-149` (the landmark projection rotates by the rect rotation, scales by the rect size and adds the centre); `:199-200` (hand landmark 224², hand ROI refinement 256², both [0, 1]); `:371-379` (the branch diagram); `:387-389` (the loose ROI: `shift_y` −0.1, `square_long`, scale 2.7); `:390-394` (the refiner crop: 256², `keep_aspect_ratio`, `BORDER_REPLICATE`; the refined ROI: `shift_y` −0.1, `square_long`, scale 1.0); `:395-399` (the tracking ROI: `shift_y` −0.1, `square_long`, scale 2.0); `:404-406` (the hand landmark crop: 224², `BORDER_REPLICATE`); `:347-349` and `:350-351` (the standalone HandLandmarker: palm ROI with scale 2.6, `shift_y` −0.5, `square_long`; landmark crop with `BORDER_REPLICATE`). **Other sources, for facts that the document does not cover:** (a) MediaPipe source at commit `e9794ef55e2509c09aa8b6ba1764b797db8eb200`, read from the cached copies in `model_cache/sources/e9794ef55e2509c09aa8b6ba1764b797db8eb200/`: `calculators/tensor/image_to_tensor_converter_opencv.cc:135-158` (the order of the tensor corners: `{0, H}, {0, 0}, {W, 0}, {W, H}`, thus the corners of the ROI map onto `[0, W] x [0, H]`; the ROI is `float`); `calculators/util/landmark_projection_calculator.cc:78-102` (the projection with `NORM_RECT` alone logs "only supported for the square ROI") and `:103-127` (with `IMAGE_DIMENSIONS`, the projection uses the exact sub-rect matrix); `calculators/util/rect_transformation_calculator.cc:206-245` (float32 arithmetic; `square_short` and separate `scale_x`, `scale_y` exist); `tasks/cc/vision/hand_landmarker/hand_landmarks_detector_graph.cc:254-264, 346-349` (the hand landmark crop sets no `keep_aspect_ratio` and no border; the projection takes `NORM_RECT` without `IMAGE_DIMENSIONS`); `tasks/cc/vision/hand_landmarker/hand_roi_refinement_graph.cc:89-91` (`keep_aspect_ratio` true, `BORDER_REPLICATE`); `tasks/cc/vision/face_landmarker/face_landmarks_detector_graph.cc:337-340` (the face projection takes `IMAGE_DIMENSIONS`). (b) MediaPipe source at the same commit, `calculators/tensor/image_to_tensor_utils.cc`, fetched from `raw.githubusercontent.com` on 2026-10-23 into a scratch folder (sha256 `ce3bc5b8669181c987e01d6aebae131995a2c62946453bbff4fd0b3553033e9f`; not in the cache): `:38-52` (`GetRoi`: the normalized rect times the image size), `:54-90` (`PadRoi`: with `keep_aspect_ratio`, the ROI grows along one axis to the tensor aspect ratio; centre and rotation stay), `:92-102` (`ValidateRoi`: a NaN value, or `width <= 0` or `height <= 0`, is an error), `:116-199` (`GetRotatedSubRectToRectTransformMatrix`: the exact matrix from the crop to the image). (c) The ONNX graphs, read with `onnx` by a scratch script of this session: `hand_landmark_full.onnx` (sha256 `5c7c9fcbba12039ef6a28f676272b5fbfc19693c12f099722a44554fb2623c17`, opset 17, 96 nodes, input `input_1` float32 `[1, 3, 224, 224]`, outputs `[1, 63]`, `[1, 1]`, `[1, 1]`, `[1, 63]`) and `hand_roi_refinement.onnx` (sha256 `1e6f0cb8d2101bbe39572f3d56f608be37882afa1fc05455d31afa4794a5e1ab`, opset 17, 77 nodes, input `input_1` float32 `[1, 3, 256, 256]`). (d) MediaPipe-Exporter 0006 (end-to-end parity of this geometry against `HolisticLandmarker`). |
| Nearest section ID | `pre.resize.affine_person_crop`, with `post.pose.schema` (rule `V-post.pose.schema-2`) |
| Why the nearest section is wrong | (1) The rotation of `affine_person_crop` is always 0: "Rotated crops are out of scope" (`specs/model-sidecar/pre/resize-affine-person-crop.md:41`). (2) Its border is always constant (`:35, :50`). The hand crops use `BORDER_REPLICATE` (`docs/mediapipe-whole-body.md:390, 404-406`). (3) `crop_policy` has only `expand_ratio`, `maintain_aspect_ratio` and `pad_value` (`resize-affine-person-crop.md:31-35`). It has no shift along the ROI axes and no `square_long` (0020 `:35-36`). (4) Its input is a person box from an upstream detector (`:29`; `post/pose-schema.md:37`). `V-post.pose.schema-2` requires `requires_object_detector: true` for `top_down_*` (`post/pose-schema.md:118`), and `V-pre.resize.affine_person_crop-2` then requires `affine_person_crop` (`resize-affine-person-crop.md:66`). Thus the spec has no valid sidecar for a top-down model that gets its ROI from another model. (5) The inverse of `affine_person_crop` has no rotation (`:57-61`), and `post.unprojection` lists no rotated inverse (`specs/model-sidecar/post/unprojection.md:30-36`). |
| Measured difference | Geometry with the reference file of part 3 (scratch script of this session; no image; not evidence until a commit exists). The Holistic loose hand ROI with the raw rect `(300, 200, 40, 40, 0.5 rad)` gives the crop ROI `(301.918, 196.490, 108, 108, 0.5)`. `affine_person_crop` on the axis-aligned box with `expand_ratio: 2.7` (no rotation, no shift) maps the input corners up to **41.3 px** away from the rotated crop (38.2 % of the ROI size). The input centre moves by 4.0 px, because the shift is missing. The historical Qualcomm-Exporter approximation (`expand_ratio: 1.0`, 0020 `:61-62`) gives up to 56.8 px. Real images: MediaPipe-Exporter 0006 shows that the ROI rules matter end to end. With this geometry the per-hand maximum landmark error against `HolisticLandmarker` has the median 0.33 px (image) and 0.18 px (video); a wrong ROI rule gives a maximum of 40.6 px (`notes/decisions/0006-holistic-end-to-end-parity.md:40-45, 56-59`). No image run of `affine_person_crop` against the rotated crop exists (part 5). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now | `crop_policy.border_mode`, rotated crops (`specs/model-sidecar/changelog.md:45`: "Only constant borders and zero rotation are used"). The evidence that a model needs it now: both hand models of the Holistic hand branch use a rotated crop with `BORDER_REPLICATE` (`docs/mediapipe-whole-body.md:390-394, 404-406`). **User decision (2026-10-23):** the change goes into `vNEXT`, and `vNEXT` adds MediaPipe-Exporter to the scope of skellytracker 0008 (`notes/decisions/0008-vnext-scope.md:8-15`, whose list does not include MediaPipe-Exporter; its resize bullet `:21` names `crop_policy.border_mode` and rotated crops as not added). The table has no row for a shift along the ROI axes, `square_long`, or an ROI that does not come from a detector (0020 `:37-40`). |

**Missing primary evidence.** These facts have no primary source yet:

- No upstream tensor of a hand crop exists. `HolisticLandmarker` does not output its input tensors.
  Thus the preprocessed input cannot be compared with the upstream tensor (part 5).
- No upstream ROI output exists. `HolisticLandmarker` gives the landmarks, not the ROI. Parity can
  compare the crop and the inverse only through the landmarks (part 5).
- The arithmetic precision. MediaPipe computes the ROI, the transform and the corners in float32
  (other source (a) and (b) above). **User decision (2026-10-24, Q7 = c):** the spec states no
  precision, and the vectors give the tolerances in `compare` (part 4). A scratch measurement of
  2026-10-24 (secondary: no commit; `q7-precision\out\tables.md` in the session scratchpad, not committed,
  script `q7_precision.py` beside it; OpenCV 5.0.0, onnxruntime 1.31.0, mediapipe 1.1.1; the image
  and video sets of MediaPipe-Exporter 0006 and 600 random ROIs) compared float32 with float64 for
  the steps of this section. The geometry differs by at most 1.2e-4 px and 1.2e-7 rad. The crop
  differs by at most 1 grey level, in at most 0.21 % of the values. The inverse alone differs by at
  most 2.2e-4 px. The hand landmarks after the inverse differ by a median of about 0.005 px. A
  float32 transcription of the MediaPipe path (a control, not upstream) differs from both precisions
  by the same amount. Thus neither precision reproduces MediaPipe exactly. With the same matrix,
  `warpAffine` and `warpPerspective` give the same pixels (0 for the 224² crop; at most 0.06 % of
  the values with a 1-level difference for the 256² crop). Thus the 1-level difference that
  MediaPipe-Exporter 0006 saw between its probe crop and its transcription of the upstream crop
  (`notes/decisions/0006-holistic-end-to-end-parity.md:61-66`) comes from the float32 geometry, not
  from the warp function. (The probe `crop` makes its corner points in float32,
  `notes/decisions/scripts/hand_roi_reference.py:55-66`.)
- No model in this pipeline uses a constant border, a non-square ROI, or an aspect step that changes
  the ROI. These branches have vectors, but no real-image run.

## 2. Spec change

### 2.1 Sections

**New section.** `pre.resize.rotated_roi_crop`, title "Rotated ROI crop", file
`specs/model-sidecar/pre/resize-rotated-roi-crop.md`. **User decision (2026-10-24, T23, Q1 = a):** a new resize method, not an
extension of `affine_person_crop` (Q1, part 8).

```yaml
---
id: pre.resize.rotated_roi_crop
title: Rotated ROI crop
kind: preprocessor
since: vNEXT
changed_in: []
selectors: [input.resize.method=rotated_roi_crop]
implemented_by:
  validate: missing
  forward: missing
  inverse: missing
external_impl: []
tests: []
vectors: vectors/pre.resize.rotated_roi_crop.yaml
status: {spec: draft, validate: missing, forward: missing, inverse: missing}
---
```

Row of the section map (`specs/model-sidecar/README.md:59-69`, heading "Pre-processing"), after the row of
`pre.resize.affine_person_crop` (`:67`):

```markdown
| `pre.resize.rotated_roi_crop` | [pre/resize-rotated-roi-crop.md](pre/resize-rotated-roi-crop.md) | Rotated ROI crop |
```

**The `vNEXT` scope (user decision, 2026-10-23).** The change goes into `vNEXT`. `vNEXT` must also
describe the MediaPipe-Exporter models of the Holistic hand branch. Skellytracker 0008 (accepted)
lists the exporters of the `vNEXT` scope, and MediaPipe-Exporter is not in the list
(`notes/decisions/0008-vnext-scope.md:8-15`). The rules of the skellytracker decision log do not
allow a rewrite of the body of an accepted entry (`notes/decisions/README.md:80-84`). The log has no
"extends" relation: an entry that changes rules of another entry restates the rules that stay and
supersedes it in full (skellytracker decision 0032, which supersedes 0028 in full and restates its item 3; `notes/decisions/README.md:86-87`). **User decision
(2026-10-24, T35; it revises T34 (N2) and T23 Q10):** the scope change of this proposal goes into a
small scope entry `RRRR` that holds only scope rules (heading "Scope entry (user decision T35)"). It
supersedes in full the scope entry in force at merge time: 0008, or the scope entry (entry B, `SSSS`)
of the OpenMMLab-Exporter proposal `nms-clamp-order` if that entry lands first. It restates the scope
rules of that entry with the change of this proposal: MediaPipe-Exporter (the hand landmark model
and the hand ROI refinement model) in the scope list, and `crop_policy.border_mode` and rotated crops out of the "not added" Resize group of 0008 (`:21`) for `rotated_roi_crop`. The rules of `rotated_roi_crop` stay in the main entry of this proposal (0020, the gap record that this proposal completes). The main entry does not supersede 0008 or any scope entry. The body of 0008 does not change; its status line becomes `superseded by RRRR` (or `superseded by SSSS`, if entry B lands first). The scope entry lands with this proposal, before the refiner proposal. The refiner proposal then cites that entry. The merge point with `nms-clamp-order` is in the Header ("Related").

**Places that the change edits.** Line numbers are at skellytracker `dom/21-move-sidecar-guide`. "Content PR" and
"non-spec PR" follow the template ("What happens next", `specs/model-sidecar/templates/change-proposal.md:56-71`).

| Place | Heading | Edit |
|---|---|---|
| `specs/model-sidecar/README.md:59-69` | Section map, "Pre-processing" | Add the row above after `:67`. |
| `specs/model-sidecar/README.md:97-123` | Validation rules (the index) | Add `- [Rotated ROI crop](pre/resize-rotated-roi-crop.md#validation-rules)` after "Affine person crop" (`:110`). |
| `specs/model-sidecar/common/input.md:43` | `input.resize`, field `method` | Add: "`rotated_roi_crop` is for a top-down model whose ROI the host gives: a rotated ROI with a transform and a border mode." Add (user decision T22 (1)): "The method gives the input that the model needs. `affine_person_crop` needs a box from an object detector. `rotated_roi_crop` needs an ROI from an earlier stage. `letterbox`, `stretch`, `fit` and `none` use the full image." (T22 names `letterbox`, `fit` and `none`. `stretch` is also a full-image method, `common/input.md:43`.) |
| `specs/model-sidecar/common/input.md:44` | `input.resize`, field `target_size` | Add `rotated_roi_crop` to the methods that require `target_size`. |
| `specs/model-sidecar/common/input.md:46` | `input.resize`, field `pad_value` | No change. The new method uses `crop_policy.pad_value`, as `affine_person_crop` does. |
| `specs/model-sidecar/common/input.md:48` | Method-specific fields | `crop_policy` links to both sections: `affine_person_crop` and `rotated_roi_crop`. |
| `specs/model-sidecar/common/input.md:50` | `supports_dynamic_size` text | Add: "It also applies to `rotated_roi_crop`. The host warps the crop to the runtime-accepted size." Add `rotated_roi_crop` to the list in the last sentence. |
| `specs/model-sidecar/common/input.md:52` | The list of method sections | Add `rotated_roi_crop` (`../pre/resize-rotated-roi-crop.md`). |
| `specs/model-sidecar/common/input.md:60` | `V-common.input-3` | Changed (part 2.4). |
| `specs/model-sidecar/common/input.md:61` | `V-common.input-4` | Changed (part 2.4). |
| `specs/model-sidecar/common/sizes-and-artifacts.md:30` | Field `sizes.<name>.input` | Add `rotated_roi_crop` to the list of methods that require `resize.target_size`. |
| `specs/model-sidecar/common/sizes-and-artifacts.md:112` | `V-common.sizes_and_artifacts-4` | Changed (part 2.4). |
| `specs/model-sidecar/pre/interpolation.md:7-11` | Front matter `selectors` | Add `input.resize.method=rotated_roi_crop`. |
| `specs/model-sidecar/pre/interpolation.md:27` | Fields, `interpolation` | Add `rotated_roi_crop` to the methods. Add: "For `rotated_roi_crop`, the value must be `linear` (`V-pre.resize.rotated_roi_crop-5` (`resize-rotated-roi-crop.md#validation-rules`))." (User decision T23, Q11.) `cv2.warpAffine` has no area resampling. With `cv2.INTER_AREA` it gives the `linear` result (scratch run of this session, OpenCV 5.0.0: maximum difference 0 on a 64 × 64 crop to 8 × 8; `cubic` 57, `nearest` 118). Thus `area` (`:40`, "Downscale with area resampling") cannot keep its meaning for this method. |
| `specs/model-sidecar/pre/interpolation.md:33` | Behaviour, the sentence "(`cv2.resize` / `cv2.warpAffine`, half-pixel centres)" | This sentence is a known defect: `cv2.warpAffine` puts the pixel centres at integer coordinates (skellytracker `notes/decisions/open-work.md:137-140`). Add: "For `rotated_roi_crop`, step 5 of Rotated ROI crop (`resize-rotated-roi-crop.md#behaviour`) states the pixel centres. That step is normative." The fix of the defect for the other methods is not in this proposal. It is a dependency on the open item of `open-work.md:137-140`. |
| `specs/model-sidecar/pre/normalization.md:49` | Behaviour | Add: "For `rotated_roi_crop`, it applies normalization after the warp." |
| `specs/model-sidecar/pre/resize-affine-person-crop.md:41` | Behaviour | Replace "Rotated crops are out of scope." with "Rotated crops are out of scope for this method. Use `rotated_roi_crop` (`resize-rotated-roi-crop.md`) for a rotated ROI." The OpenMMLab-Exporter proposal `affine-crop-arithmetic` replaces "Behaviour" with the text of its 2.3, which has the same sentence "Rotated crops are out of scope." The content PR that lands second keeps the text of this proposal for this sentence (header row "Depends on", "Related"). |
| `specs/model-sidecar/pre/resize-affine-person-crop.md:80-81` | Authoring guidance (non-spec PR) | Point the two bullets on rotated ROIs and on the Qualcomm-Exporter approximation to `rotated_roi_crop`. Cite the accepted decision. |
| `specs/model-sidecar/pre/resize-affine-person-crop.md:66` | `V-pre.resize.affine_person_crop-2` | Changed (part 2.4; user decision T22 (1)): the rule names `pose.estimator_type`, not the removed field. |
| `specs/model-sidecar/pre/resize-affine-person-crop.md:29` | Fields, the sentence on the person box | No change. It already says that the host warps a person bounding box. |
| `specs/model-sidecar/post/pose-schema.md:37` | Fields, `pose.requires_object_detector` | Delete the row (user decision T22 (1)). Add after the table: "The sidecar does not declare whether the model needs an object detector. `input.resize.method` gives the input that the model needs (Input (`../common/input.md#inputresize`)): `affine_person_crop` a box from an object detector, `rotated_roi_crop` an ROI from an earlier stage (Rotated ROI crop (`../pre/resize-rotated-roi-crop.md#roi-source`)), `letterbox`, `stretch`, `fit` and `none` the full image." |
| `specs/model-sidecar/post/pose-schema.md:117` | `V-post.pose.schema-1` | Changed (part 2.4): `requires_object_detector` leaves the list of required fields. |
| `specs/model-sidecar/post/pose-schema.md:118` | `V-post.pose.schema-2` | Changed (part 2.4): at `vNEXT` the field must not be present. |
| `specs/model-sidecar/post/pose-schema.md`, a new heading "Legacy behaviour" after "Validation rules" | Legacy behaviour | New (part 2.6): the legacy meaning of the field and of the two rules. |
| `specs/model-sidecar/post/pose-schema.md:137, 138, 139, 141` | Authoring guidance (non-spec PR) | Delete the `requires_object_detector` value from the RTMW, RTMO, YOLO26-pose and MediaPipe bullets. Keep the other values. |
| `specs/model-sidecar/post/pose-schema.md:144` | Authoring guidance (non-spec PR) | Replace the 0020 gap bullet with the mapping of the MediaPipe hand landmark model: `top_down_single_person`, `rotated_roi_crop`, no `requires_object_detector`. |
| `specs/model-sidecar/post/pose-schema.md:151` | Examples | Delete the line `requires_object_detector: true`. |
| `specs/model-sidecar/post/canonical-mapping.md:99` | Authoring guidance (non-spec PR) | Delete `requires_object_detector` from the list of the keys of the `pose` blocks of the exporters, when the exporters write the sidecars again. |
| `specs/model-sidecar/common/outputs.md:106` | Examples (YAML) | Delete the line `requires_object_detector: false`. |
| `specs/model-sidecar/format/composition.md:74` | Examples (YAML) | Delete the line `requires_object_detector: true`. |
| `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml:49`, `.../rtmw/wholebody/rtmw-wholebody.yaml:40`, `.../yolo26/body/yolo26-body.yaml:45` (non-spec PR) | Reference examples | No hand edit. Each file declares `schema_version: vNEXT` (`:2`), so after this change each file breaks `V-post.pose.schema-2`. The procedure "Reference examples" copies an exporter sidecar byte for byte, and nobody corrects an example by hand (`specs/exporter-guide/sidecars/workflow/phase-3-skellytracker.md:11-12`). Thus the non-spec PR replaces the three files from the sidecars that the exporters write again (part 7). Until then the examples have a known defect. |
| `specs/model-sidecar/templates/model-intake.md:311` | Row K1 | New property text: "Estimator type". The section column does not change. The input that the model needs is row T2 (the resize method). |
| `specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:48-49` | Phase 2, the example of a rule that names a value | Replace the example with the changed rule: "`V-pre.resize.affine_person_crop-2`: a top-down sidecar declares `input.resize.method: affine_person_crop` or `rotated_roi_crop`". |
| `specs/model-sidecar/templates/change-proposal.md:164-167` | 2.4 Validation rules, the example | The same edit as the exporter guide. |
| `specs/model-sidecar/post/unprojection.md:30-36` | Behaviour, the list of inverses | Add `- rotated_roi_crop: [Rotated ROI crop](../pre/resize-rotated-roi-crop.md#inverse)`. |
| `specs/model-sidecar/post/unprojection.md:61, 64-66` | Implementer guidance (non-spec PR) | Replace the bullets on the missing rotated inverse with a pointer to the new section. |
| `specs/model-sidecar/format/versioning.md:72-74` | Legacy behaviour | Add `rotated_roi_crop` (with `crop_policy.transform` and `crop_policy.border_mode`) to the first column of the existing row (part 2.6). |
| `specs/model-sidecar/format/versioning.md:51-63` | Version-aware compatibility | No link for the new section: it has a "Legacy behaviour" heading that points to `format.versioning`, as `pre.resize.fit` does (`specs/model-sidecar/pre/resize-fit.md:57-59`). Add the link `- [Pose schema](../post/pose-schema.md#legacy-behaviour)` for the new legacy row of `pose.requires_object_detector` (user decision T22 (1), part 2.6). |
| `specs/model-sidecar/changelog.md:5-10` | Changes in this revision, the note "For reviewers" | Add MediaPipe-Exporter (the Holistic hand branch: the hand landmark model and the hand ROI refinement model) to the exporters whose models the revision must describe. |
| `specs/model-sidecar/changelog.md:14-36` | Summary of changes | New row N, the next free number at merge time (part 2.7). 13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order. |
| `specs/model-sidecar/changelog.md:45` | Considered and deliberately not added | Change the row (part 2.7). Add a row for the `RectTransformation` options that this proposal does not add. |
| `specs/model-sidecar/changelog.md:55-59` | Compatibility impact | Add: "A `rotated_roi_crop` must declare `crop_policy` with `maintain_aspect_ratio` and `border_mode`, and `pad_value` with `border_mode: constant`. Its `interpolation` must be `linear`. **(vNEXT)** The keys of an `affine_person_crop` `crop_policy` must be a subset of `expand_ratio`, `maintain_aspect_ratio` and `pad_value`. A `vNEXT` sidecar must not declare `pose.requires_object_detector`. A top-down model must declare `affine_person_crop` or `rotated_roi_crop`." (The last two sentences: user decision T22 (1).) |
| `specs/model-sidecar/changelog.md:68` | `schema_version` history, row `vNEXT` | Add text (part 2.7). |
| `specs/exporter-guide/sidecars/workflow/phase-1-intake.md:14-16` | Phase 1, step 1 (the start of the runtime contract) | "the source image, and the box for `affine_person_crop`" becomes "the source image, and the box for `affine_person_crop` or the ROI for `rotated_roi_crop`". |
| `specs/exporter-guide/sidecars/workflow/phase-1-intake.md:30-32` | Phase 1, the verdict `gap` | Remove "a rotated crop, a border mode" from the examples. |
| `specs/model-sidecar/templates/model-intake.md:113, 118-119` | Verdicts | The same two edits as in the exporter guide. |
| `specs/model-sidecar/templates/model-intake.md:260, 262, 264, 269, 270, 300` | Rows T2, T4, T4b, T7a, T7b, D11 | Add `rotated_roi_crop` and its section link to the method lists. |
| `specs/model-sidecar/templates/model-intake.md:267, 271` | Rows T6, T8 | T6: add `crop_policy.border_mode` and `crop_policy.pad_value` for `rotated_roi_crop`. T8: add the fields of the `rotated_roi_crop` crop policy (`transform`, `maintain_aspect_ratio`, `border_mode`). |
| `specs/model-sidecar/TRACEABILITY.md:26-31, 76-80` | Section tables | Regenerated with the new section. |
| `specs/model-sidecar/inventory.yaml:115-121` | `proposed`, `mediapipe-hand-landmark@mediapipe-exporter` (non-spec PR) | The notes name `rotated_roi_crop`. |
| `tools/tests/test_vectors.py:530-535` | `UNPROJECTION_SECTIONS` | Add `pre.resize.rotated_roi_crop` if the test can read its `unproject_points` cases. For the implementer. |
| `tools/tests/test_traceability.py:585-589, 712-720` | Resize applicability | Add the new section. For the implementer. |
| `tools/make_vectors.py:2411-2415` | `BUILDERS` | The vectors of this section come from the reference file of part 3, not from a builder. The content PR commits the YAML of part 4, or adds a builder that imports `specs/model-sidecar/reference/pre_resize_rotated_roi_crop.py`. For the implementer. |
| skellytracker `notes/decisions/0008-vnext-scope.md:8-15, 21` (accepted) | Decision | A new scope entry `RRRR-vnext-scope-mediapipe-rotated-crops.md` (status `proposed`) supersedes in full the scope entry in force at merge time: 0008, or entry B (`SSSS-vnext-scope-nms-filters.md`) of the OpenMMLab-Exporter proposal `nms-clamp-order` if that entry lands first. It restates the scope rules of that entry with the change of this proposal: MediaPipe-Exporter in the scope list, and `crop_policy.border_mode` and rotated crops out of the "not added" Resize group (`:21`). It holds only scope rules. Its text is under the heading "Scope entry (user decision T35)": the base text, or the variant if entry B lands first. Add its Active index row in the same PR. When the user accepts it, the scope entry that it supersedes becomes `superseded by RRRR`, and its row moves to "Historical". The body of 0008 does not change. The main entry of this proposal (0020) does not supersede 0008 or any scope entry (user decisions T34 (N2) and T35; Q10, revised). |
| skellytracker `notes/decisions/README.md:39` | Index row of 0020 | When the user decides the new entry, the status line of 0020 changes in the same PR (`notes/decisions/README.md:88-91, 142-145`). |

`specs/model-sidecar/sidecar-spec.md` (the permanent index) needs no edit. It keeps old headings, and this section
has no old heading.

### 2.2 Fields table

These fields apply when `input.resize.method` is `rotated_roi_crop`.

| Field | Type | Required | Description |
|---|---|---|---|
| `input.resize.method` | enum | yes | The new value `rotated_roi_crop`. |
| `input.resize.crop_policy` | object | yes (`rotated_roi_crop`) | How the host changes the ROI and how it fills the border. Its keys are `transform`, `maintain_aspect_ratio`, `border_mode` and `pad_value`. |
| `input.resize.crop_policy.transform` | object | no | An ROI transform (heading "ROI transform"). Without the field, the ROI does not change. A nested object, not flat fields in `crop_policy` as the 0020 direction writes them (user decision T23, Q1 part 2). |
| `input.resize.crop_policy.transform.shift_x` | float | no | The shift of the centre along the x axis of the ROI, as a fraction of `w`. The default is `0.0`. |
| `input.resize.crop_policy.transform.shift_y` | float | no | The shift of the centre along the y axis of the ROI, as a fraction of `h`. A negative value moves the centre to the top of the crop. The default is `0.0`. |
| `input.resize.crop_policy.transform.square_long` | bool | no | When `true`, the host makes the ROI square with its longer side. The default is `false`. |
| `input.resize.crop_policy.transform.scale` | float | no | The factor for `w` and `h`. It must be a finite number `> 0`. The default is `1.0`. One `scale` for both axes (user decision T22 (2), Q5). A later proposal can add `scale_x` and `scale_y` when a model needs them. |
| `input.resize.crop_policy.maintain_aspect_ratio` | bool | yes (`rotated_roi_crop`) | When `true`, the host enlarges the ROI along its shorter side to the aspect ratio `T_w / T_h` of the model input (the formula of `affine_person_crop`). When `false`, the host warps the ROI directly, and the x and y scales can differ. No default (user decision T23, Q4). |
| `input.resize.crop_policy.border_mode` | enum | yes (`rotated_roi_crop`) | `constant` or `replicate`. `constant` fills each pixel outside the source image with `pad_value`. `replicate` repeats the nearest edge pixel of the source image (`cv2.BORDER_REPLICATE`). No default (user decision T23, Q4). |
| `input.resize.crop_policy.pad_value` | int, float, or array[3] | `constant`: yes; `replicate`: must not be present | A raw pixel value (before normalization). An array gives one value for each channel, in the order of `input.color_format`. A scalar fills every channel. |
| `input.resize.interpolation` | enum | no | As in Interpolation (`interpolation.md`). The default is `linear`. For `rotated_roi_crop`, the value must be `linear` (`V-pre.resize.rotated_roi_crop-5`; user decision T23, Q11). MediaPipe uses only `INTER_LINEAR` (`docs/mediapipe-whole-body.md:96-97`). |
| `sizes.<size>.input.resize.target_size` | array[2] | yes, unless `supports_dynamic_size` | `[T_h, T_w]`, as for the other methods. |

The ROI is not a sidecar field. The host gives one ROI for each batch item at run time (heading
"ROI source").

**Removal of `pose.requires_object_detector`** (user decision T22 (1), 2026-10-24). The field leaves
the spec at `vNEXT`. The premise of the decision: no sidecar is deployed, and all sidecars will be
made again. `input.resize.method` gives the input that a model needs: `affine_person_crop` a box
from an object detector, `rotated_roi_crop` an ROI from an earlier stage, and `letterbox`,
`stretch`, `fit` and `none` the full image. Thus the field holds no information that the method
does not give. At `vNEXT`, the `pose` block must not declare the field (changed
`V-post.pose.schema-1` and `-2`, part 2.4). The changed `V-pre.resize.affine_person_crop-2` names
`pose.estimator_type` in place of the field. A sidecar with `schema_version < vNEXT` keeps the legacy
meaning (part 2.6): the skellytracker package sidecars declare the field (for example
`skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose-body.yaml:39`), and their
legacy meaning must not change (`specs/model-sidecar/templates/change-proposal.md:177, 363-364` at
`dom/12-single-working-branch`). For a legacy sidecar the field is redundant: `V-post.pose.schema-2` ties it to
`estimator_type`, and `V-pre.resize.affine_person_crop-2` ties `true` to `affine_person_crop`.

YAML excerpt 1 (the Holistic hand landmark model, `hand_landmark_full`; the other blocks are in the full proposals of
skellytracker 0021 (`specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md`), 0022 (`specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md`) and 0025 (OpenMMLab-Exporter `specs/model-sidecar/proposals/model-id-suffix/proposal.md`)):

```yaml
input:
  name: input_1
  layout: NCHW
  resize:
    method: rotated_roi_crop
    interpolation: linear
    crop_policy:
      maintain_aspect_ratio: false   # the graph sets no keep_aspect_ratio
      border_mode: replicate         # docs/mediapipe-whole-body.md:404-406
pose:
  estimator_type: top_down_single_person   # no requires_object_detector (removed, T22 (1))
```

The hand landmark model has no `crop_policy.transform`. Its ROI comes from two sources with
different transforms: the refiner (scale 1.0) and the previous landmarks (scale 2.0)
(`docs/mediapipe-whole-body.md:390-399`). Each source applies its own transform (user decision T23,
Q2 part 2). Thus the ROI that the host gives is final (heading "ROI source").

YAML excerpt 2 (the input crop of the hand ROI refinement model; **user decision T23**, Q2 = a):

```yaml
input:
  name: input_1
  layout: NCHW
  resize:
    method: rotated_roi_crop
    interpolation: linear
    crop_policy:
      transform: {shift_y: -0.1, square_long: true, scale: 2.7}   # docs/mediapipe-whole-body.md:387-389
      maintain_aspect_ratio: true                                 # docs/mediapipe-whole-body.md:390
      border_mode: replicate                                      # docs/mediapipe-whole-body.md:390
```

With excerpt 2, the host gives the raw loose rect: centre `middle`, size `2 · |middle − wrist|`,
rotation from the wrist to `middle` with target 90° (`docs/mediapipe-whole-body.md:387-389`). This
section does not hold that rule. By user decision T24 (2026-10-24), the refiner sidecar holds it, in
its block `roi_source` (refiner proposal, part 2.2 and part 2.3, heading "ROI source"). This
section holds the transform.

### 2.3 Behaviour

Normative text of `pre.resize.rotated_roi_crop`:

```text
## ROI

An ROI is (cx, cy, w, h, rotation) in source-image pixels. The origin is the top-left corner of the
source image. x grows to the right and y grows down.

- (cx, cy) is the centre of the ROI.
- w is the size along the x axis of the ROI. h is the size along the y axis of the ROI.
- rotation is in radians. A positive rotation turns the ROI clockwise on the image. The x axis of the
  ROI is (cos(rotation), sin(rotation)). The y axis of the ROI is (-sin(rotation), cos(rotation)).
  With rotation 0, the ROI is the box [cx - w/2, cx + w/2] x [cy - h/2, cy + h/2].
- This section does not limit the range of rotation. The crop and the inverse use only its cosine
  and its sine. A section that computes a rotation states the range of its result.

An ROI is valid only when its five values are finite, w > 0 and h > 0 (strict).

## ROI source

The host gives one ROI for each batch item. This section does not say how the host makes the ROI.
The ROI can come from the output of another model (for example a pose model or an ROI refiner),
from an earlier frame, or from a rule of the host. The rule that makes the ROI is outside this
section. A model with rotated_roi_crop needs no box from an object detector.

If a model gets its ROI from two or more sources with different transforms, each source applies
its own transform, and the sidecar of the model declares no crop_policy.transform.

## ROI transform

An ROI transform has the fields shift_x, shift_y, square_long and scale. For an ROI
(cx, cy, w, h, rotation), the host does these steps in this order:

1. Shift. c = cos(rotation), s = sin(rotation).
     cx = cx + w * shift_x * c - h * shift_y * s
     cy = cy + w * shift_x * s + h * shift_y * c
   The shift uses w and h before step 2.
2. Square. If square_long is true: w = h = max(w, h).
3. Scale. w = w * scale. h = h * scale.

The rotation does not change. With the defaults (0.0, 0.0, false, 1.0), the ROI does not change.

## Behaviour

For each batch item, with the ROI R that the host gives, and the model input size [T_h, T_w]:

1. Transform. If a value of R is not finite, the item has no crop. Else apply the ROI transform of
   crop_policy.transform to R. The result is R1. Without crop_policy.transform, R1 = R.
2. Check. If R1 is not valid, the item has no crop. The host makes no input tensor for this item,
   and the item has no output.
3. Aspect ratio. If maintain_aspect_ratio is true:
     if w1 > h1 * (T_w / T_h): h1 = w1 * (T_h / T_w)
     else:                     w1 = h1 * (T_w / T_h)
   The centre and the rotation do not change. The result is the crop ROI
   Rc = (cx, cy, wc, hc, rotation).
4. Matrix. sx = T_w / wc, sy = T_h / hc, c = cos(rotation), s = sin(rotation).
     M = [[ sx * c,  sx * s,  T_w / 2 - sx * ( c * cx + s * cy)],
          [-sy * s,  sy * c,  T_h / 2 - sy * (-s * cx + c * cy)]]
   M maps the top-left corner of Rc to (0, 0), its top-right corner to (T_w, 0) and its
   bottom-left corner to (0, T_h). (Corner convention: the corners of Rc map onto the corners of
   [0, T_w] x [0, T_h].)
5. Warp.
     dst = warpAffine(src, M, (T_w, T_h), INTER_LINEAR, borderMode, borderValue)
   Output pixel (i, j) (column i, row j) takes the source value at M^-1 . (i, j). The pixel centres
   are at integer coordinates. This step states the pixel centres of rotated_roi_crop. The sentence
   on half-pixel centres in Interpolation does not apply to this method. interpolation must be
   linear. border_mode: replicate gives BORDER_REPLICATE. border_mode: constant gives
   BORDER_CONSTANT with borderValue = pad_value. A scalar pad_value fills every channel. An array
   pad_value has one value for each channel.

The host warps the source image in its source dtype (for example uint8).

## Inverse

The host applies the inverse as part of Unprojection. For a point (x, y) in model-input pixels,
with the crop ROI Rc of step 3:

  u = (x / T_w - 0.5) * wc
  v = (y / T_h - 0.5) * hc
  x_src = cx + c * u - s * v
  y_src = cy + s * u + c * v

This is the exact inverse of M. It uses Rc, not the ROI R that the host gave.
```

Which upstream rule each part describes:

| Part | Upstream rule (primary: `docs/mediapipe-whole-body.md`; other sources as named in part 1) |
|---|---|
| ROI | `NormalizedRect` times the image size: `(x_center, y_center, width, height, rotation)`, clockwise radians, in pixels (`:58-61`; `GetRoi`, `image_to_tensor_utils.cc:38-52`) |
| ROI validity | `ValidateRoi` tests NaN only (`std::isnan`), then `width <= 0` or `height <= 0` (`image_to_tensor_utils.cc:92-102`). The test of this section also rejects an infinite value. That is stricter than upstream (user decision T23, Q9). |
| ROI source | No upstream rule for the sidecar. MediaPipe applies the transform of each ROI source in the graph of that source (`:387-399`). "Each source applies its own transform" is a user decision (T23, Q2 part 2 = a). |
| ROI transform | `RectTransformationCalculator`: shift along the rect axes, then `square_long`, then scale (`:81-87`) |
| Step 2 | `ValidateRoi`: NaN, `width <= 0` or `height <= 0` is an error (`image_to_tensor_utils.cc:92-102`). MediaPipe makes no tensor for such an ROI. "No crop" is the host form of that error. For `w <= 0` or `h <= 0`, this is a **user decision** (2026-10-23, refiner proposal Q5 = a; see Q9). For a value that is not finite, it is a user decision too (T23, Q9). |
| Step 3 | `keep_aspect_ratio` (`:101`); `PadRoi`: the ROI grows along one axis to the tensor aspect ratio, and the centre and the rotation stay (`image_to_tensor_utils.cc:54-90`). The formula is the same as `affine_person_crop` (`resize-affine-person-crop.md:46-48`). |
| Steps 4 and 5 | `boxPoints` of the rect onto the tensor corners `{0, H}, {0, 0}, {W, 0}, {W, H}`, `warpPerspective`, `INTER_LINEAR`, border mode (`:94-100`; `image_to_tensor_converter_opencv.cc:135-158`). For a rectangle, this perspective map is the affine map `M`. |
| Inverse | The crop matrix that the refinement graph uses (`:106-112`; `GetRotatedSubRectToRectTransformMatrix`, `image_to_tensor_utils.cc:116-199`), and `LandmarkProjectionCalculator` for a square ROI (`:147-149`) |

Notes, not normative:

- The landmark projection of the hand landmark graph uses the rect alone (`NORM_RECT` without
  `IMAGE_DIMENSIONS`, `hand_landmarks_detector_graph.cc:346-349`). That path computes
  `cx + w · (c · X − s · Y)`, `cy + h · (s · X + c · Y)` with `X = x / T_w − 0.5`,
  `Y = y / T_h − 0.5`. It logs "only supported for the square ROI"
  (`landmark_projection_calculator.cc:78-96`). For a square ROI, or for rotation 0, it equals the
  inverse above. Every hand ROI is square (`square_long`, `docs/mediapipe-whole-body.md:387-399`).
  The face graph uses the exact matrix (`face_landmarks_detector_graph.cc:337-340`). The vector
  `unproject-non-square-rotated` shows the difference for a non-square rotated ROI (user decision
  T23, Q6: the exact inverse).
- The section states no arithmetic precision (user decision Q7 = c, 2026-10-24). The vectors give
  the tolerances in `compare` (part 4): `1e-3` px for ROI values, for the corners that `M` maps
  and for the inverse; `1e-6` rad for a rotation; 1 grey level for each crop value.
- MediaPipe makes the crop with `warpPerspective` and a float32 matrix. This section uses
  `warpAffine`. With the same matrix, the two functions give the same pixels (0 different values
  for the 224² crop, at most 0.06 % of the values with a 1-level difference for the 256² crop). The
  float32 and the float64 geometry give crops that differ by at most 1 grey level in at most 0.21 %
  of the values. Thus the 1-level difference that MediaPipe-Exporter 0006 saw between its probe crop
  and its transcription of the upstream crop (a control, not upstream;
  `notes/decisions/0006-holistic-end-to-end-parity.md:61-66`) comes from the float32 geometry, not
  from the warp function. (Scratch measurement of 2026-10-24, secondary, part 1.)
- With `maintain_aspect_ratio`, MediaPipe also outputs the letterbox padding, and the landmark graph
  removes it before the projection (`hand_landmarks_detector_graph.cc:333-342`). The inverse above
  uses the enlarged ROI `Rc` directly. The two results are the same for a square ROI or for
  rotation 0. For a non-square rotated ROI, the `NORM_RECT` projection after the letterbox removal is
  not exact (first note; vector `unproject-non-square-rotated`).
- The inverse maps `x` and `y` only. A depth `z` in input pixels maps to source pixels with the factor
  `wc / T_w` (MediaPipe multiplies `z` by the rect width, `docs/mediapipe-whole-body.md:147-149`).
  Skellytracker 0022 owns the depth rule. Part 7 gives this input to 0022. The full proposal of 0022, `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md` (heading "Depth"), uses this factor.
- World landmarks rotate by the ROI rotation (`docs/mediapipe-whole-body.md:149-150`). Skellytracker
  0021 owns world landmarks. The full proposal of 0021, `specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md` (its Behaviour step 4), gives that rotation.

### 2.4 Validation rules

New rules of `pre.resize.rotated_roi_crop`:

- [ ] `V-pre.resize.rotated_roi_crop-1` **(vNEXT)** If `input.resize.method` is `rotated_roi_crop`,
  `role` must be `[pose_estimator]`. `pose.estimator_type` must be `top_down_single_person` or
  `top_down_multi_person`.
- [ ] `V-pre.resize.rotated_roi_crop-2` **(vNEXT)** A `rotated_roi_crop` resize must declare
  `crop_policy`. The keys of `crop_policy` must be a subset of `transform`, `maintain_aspect_ratio`,
  `border_mode` and `pad_value`. `maintain_aspect_ratio` must be present, and it must be a boolean.
  `border_mode` must be present, and it must be `constant` or `replicate`.
- [ ] `V-pre.resize.rotated_roi_crop-3` **(vNEXT)** If `crop_policy.border_mode` is `constant`,
  `crop_policy.pad_value` must be present. If `crop_policy.border_mode` is `replicate`,
  `crop_policy.pad_value` must not be present.
- [ ] `V-pre.resize.rotated_roi_crop-4` **(vNEXT)** If `crop_policy.transform` is present, its keys
  must be a subset of `shift_x`, `shift_y`, `square_long` and `scale`. `shift_x` and `shift_y` must
  be finite numbers. `square_long` must be a boolean. `scale` must be a finite number `> 0`.
- [ ] `V-pre.resize.rotated_roi_crop-5` **(vNEXT)** If `input.resize.method` is `rotated_roi_crop`
  and `input.resize.interpolation` is present, it must be `linear`. (User decision T23, Q11.
  `cv2.warpAffine` has no area resampling, so `area` cannot keep its meaning. No model in scope uses
  `cubic` or `nearest`.)

Changed rules:

- `V-common.input-3` (`specs/model-sidecar/common/input.md:60`), new text: "`input.resize.method` must be
  `letterbox`, `stretch`, `fit`, `affine_person_crop`, `rotated_roi_crop` or `none`. The values
  `stretch`, `fit` and `rotated_roi_crop` are marked **(vNEXT)**. `input.resize.interpolation` must
  be `linear`, `area`, `cubic` or `nearest`."
- `V-common.input-4` (`specs/model-sidecar/common/input.md:61`), new text of the last sentence:
  "`crop_policy` must not be present unless `method` is `affine_person_crop` or `rotated_roi_crop`.
  **(vNEXT)** For `affine_person_crop`, the keys of `crop_policy` must be a subset of
  `expand_ratio`, `maintain_aspect_ratio` and `pad_value`." (The keys of the new method are in
  `V-pre.resize.rotated_roi_crop-2`.) **Overlap:** the OpenMMLab-Exporter proposal
  `affine-crop-arithmetic` adds `crop_policy.arithmetic`. If both land, the set must also contain
  `arithmetic`. Otherwise each `vNEXT` sidecar with `arithmetic` fails `V-common.input-4`. The
  content PR that lands second does this edit (header row "Depends on", "Related"). **User decision T23 (Q12 = a):** the closed key set for
  `affine_person_crop` is new. Today `V-common.input-4` has no key set for `crop_policy`
  (`common/input.md:61`). The reason: without it, `transform` or `border_mode` on an
  `affine_person_crop` passes the rules, and the host ignores it. The crop is then wrong with no
  error. The validator already rejects unknown keys: `CropPolicySpec` is a `_StrictModel` with
  `extra="forbid"` (`skellytracker/core/sidecar/model.py:33, 67-75`). Thus the rule changes no
  result of the package validator for these keys. (`CropPolicySpec` also has no `pad_value` field
  today. That is a separate gap of the validator, not of this proposal.) The rule is marked
  **(vNEXT)**, so a legacy sidecar keeps its meaning. The changelog row and the Compatibility impact
  text name it (parts 2.1 and 2.7).
- `V-common.sizes_and_artifacts-4` (`specs/model-sidecar/common/sizes-and-artifacts.md:112`): add
  `rotated_roi_crop` to the list of methods.
- `V-post.pose.schema-1` (`specs/model-sidecar/post/pose-schema.md:117`), new text (user decision T22
  (1)): "The sidecar must declare `pose` (with `estimator_type`), `pose.decode`,
  `pose.tracked_points` and `pose.connections`." The legacy text (`pose` with `estimator_type` and
  `requires_object_detector`) goes to the heading "Legacy behaviour" of `post.pose.schema` (part
  2.6).
- `V-post.pose.schema-2` (`specs/model-sidecar/post/pose-schema.md:118`), new text (user decision T22
  (1)): "**(vNEXT)** `pose` must not declare `requires_object_detector`. `input.resize.method` gives
  the input that the model needs (`V-pre.resize.affine_person_crop-2`)." The legacy text (a
  boolean, `true` for `top_down_*`, `false` for `bottom_up`) goes to the heading "Legacy behaviour"
  of `post.pose.schema`.
- `V-pre.resize.affine_person_crop-2` (`specs/model-sidecar/pre/resize-affine-person-crop.md:66`), new
  text (user decision T22 (1)): "**(vNEXT)** If `pose.estimator_type` is `top_down_single_person` or
  `top_down_multi_person`, `input.resize.method` must be `affine_person_crop` or
  `rotated_roi_crop`. If `pose.estimator_type` is `bottom_up`, `input.resize.method` must not be
  `affine_person_crop` or `rotated_roi_crop`." The legacy text ("If a sidecar has
  `pose.requires_object_detector: true`, it must declare `input.resize.method: affine_person_crop`")
  goes to the heading "Legacy behaviour" of `post.pose.schema`. The new text keeps the legacy
  pairing: at legacy, `true` is the same as `top_down_*` (legacy `V-post.pose.schema-2`), and
  `false` is the same as `bottom_up`. A legacy `bottom_up` sidecar with `affine_person_crop` passed
  the legacy rules. The new second sentence rejects it at `vNEXT`, because a bottom-up model uses the
  full image (T22 (1)).

Existing rules that name a changed value, and the effect:

| Rule | Effect |
|---|---|
| `V-pre.resize.affine_person_crop-2` (`resize-affine-person-crop.md:66`) | changed (above). 0020 names it (`0020-roi-transform-and-source.md:13-16`). The rule names `pose.estimator_type` in place of the removed field, and it allows `rotated_roi_crop` for a top-down model. |
| `V-pre.resize.affine_person_crop-1` (`:65`) | unchanged. It checks only the form of `expand_ratio` and `maintain_aspect_ratio`. It checks no key set. The key set is in the changed `V-common.input-4`. |
| `V-common.input-5` (`common/input.md:62`) | unchanged. It checks the form of `crop_policy.pad_value` of the new method too. |
| `V-common.input-6` (`common/input.md:63`) | unchanged. |
| `V-post.pose.schema-3`, `-7` (`post/pose-schema.md:119, 123`) | unchanged. The hand landmark model uses `coordinate` with one `keypoints` output. Its extra outputs are the scope of skellytracker 0021. `V-post.pose.schema-1` is changed (above). |
| `V-post.det.*`, `V-common.identity-*` | unchanged. No other rule names `requires_object_detector` (a search of `specs/model-sidecar/` at `dom/14-decision-log-growth`). |
| `V-common.identity-2` (`common/identity.md:37`) | unchanged. Follow-up: the refiner proposal adds the role `roi_refiner`, and it must extend `V-pre.resize.rotated_roi_crop-1` to allow `role: [roi_refiner]` (part 7). |
| `V-format.versioning-1`, `-2` | unchanged. `n/a at vNEXT` (`specs/exporter-guide/sidecars/validation-and-publishing.md:13-16`). |

### 2.5 Selectors

`input.resize.method=rotated_roi_crop`. The section `pre.resize.interpolation` also gets this
selector. `post.unprojection` keeps its selectors (`role=pose_estimator` already matches,
`specs/model-sidecar/post/unprojection.md:7`).

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` cannot declare `rotated_roi_crop`, `crop_policy.transform`
  or `crop_policy.border_mode`. The legacy meaning of every other field does not change. The closed
  key set of an `affine_person_crop` `crop_policy` (changed `V-common.input-4`) is marked
  **(vNEXT)**. It does not apply to a legacy sidecar.
- **User decision (2026-10-24, T22 (1)):** `pose.requires_object_detector` leaves the spec at
  `vNEXT`. A legacy sidecar keeps the field and the legacy text of `V-post.pose.schema-1` and `-2`
  and of `V-pre.resize.affine_person_crop-2`. The new heading "Legacy behaviour" of
  `post.pose.schema` holds that text (below). The index "Version-aware compatibility"
  (`format/versioning.md:51-63`) gets the link `- [Pose schema](../post/pose-schema.md#legacy-behaviour)`.
  The skellytracker package sidecars (`v2024.09.1019`) thus keep their meaning. A `vNEXT` sidecar
  with the field fails the changed `V-post.pose.schema-2`.
- **User decision (2026-10-23):** the change goes into the `vNEXT` revision. It adds no new
  `schema_version` value, because `vNEXT` is not released yet (skellytracker 0014).
- The `vNEXT` scope of skellytracker 0008 must add MediaPipe-Exporter (user decision; part 2.1). The scope entry of this proposal makes that change (T35).
- The new section has the heading "Legacy behaviour" with one sentence: "Availability before
  `vNEXT`: Schema versioning (`../format/versioning.md#legacy-behaviour`)." (the form of
  `specs/model-sidecar/pre/resize-fit.md:57-59`).

Changed row of the "Legacy behaviour" table of `format.versioning`
(`specs/model-sidecar/format/versioning.md:74`):

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`, `rotated_roi_crop` (with `crop_policy.transform` and `crop_policy.border_mode`) | Not available. | Available. |

New heading "Legacy behaviour" of `post.pose.schema` (`specs/model-sidecar/post/pose-schema.md`, after
"Validation rules"; user decision T22 (1)):

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| `pose.requires_object_detector` | Required (`V-post.pose.schema-1`). It must be a boolean, `true` for `top_down_single_person` and `top_down_multi_person`, and `false` for `bottom_up` (`V-post.pose.schema-2`). If it is `true`, `input.resize.method` must be `affine_person_crop` (`V-pre.resize.affine_person_crop-2`). | Removed. `pose` must not declare it. `input.resize.method` gives the input that the model needs (`V-pre.resize.affine_person_crop-2`). |

### 2.7 Changelog row

Summary of changes (`specs/model-sidecar/changelog.md:14-36`), row N (the next free number at merge time):

```markdown
| N | Resize | New `input.resize.method: rotated_roi_crop` for a top-down model whose ROI the host gives (not a detector box). An ROI is `(cx, cy, w, h, rotation)` in source pixels, rotation clockwise. `crop_policy` has an ROI transform (`shift_x`, `shift_y` along the ROI axes, `square_long`, `scale`), a required `maintain_aspect_ratio` and a required `border_mode` (`constant` with `pad_value`, or `replicate`). `interpolation` must be `linear`. The corners of the ROI map onto the model input; the inverse is exact. The section states no arithmetic precision; the vectors give the tolerances. `pose.requires_object_detector` is removed: `input.resize.method` gives the input that a model needs, and a top-down model declares `affine_person_crop` or `rotated_roi_crop` (`V-pre.resize.affine_person_crop-2`). The keys of an `affine_person_crop` `crop_policy` are now a closed set (`expand_ratio`, `maintain_aspect_ratio`, `pad_value`). | MediaPipe Holistic hand branch (hand landmark model, hand ROI refinement input) | [`input.resize`](pre/resize-rotated-roi-crop.md) |
```

Changed row of "Considered and deliberately not added" (`specs/model-sidecar/changelog.md:45`):

```markdown
| `affine_person_crop` with a rotation or a border mode other than constant | No `affine_person_crop` model needs it. A rotated ROI uses `rotated_roi_crop`, which has `crop_policy.border_mode`. |
| `RectTransformation` options `square_short`, separate `scale_x` and `scale_y`, and a rotation offset, in `crop_policy.transform` | No model in scope uses them. Every MediaPipe transform in scope has one scale and `square_long` or nothing. |
```

`schema_version` history (`specs/model-sidecar/changelog.md:68`), text to add to the `vNEXT` row: "Added
`input.resize.method: rotated_roi_crop` (an ROI that the host gives, an ROI transform, a required
aspect step and border mode, `linear` interpolation only, the corner-convention warp and its exact
inverse, no arithmetic precision in the text); removed `pose.requires_object_detector` (the resize
method gives the input that a model needs); the keys of an `affine_person_crop` `crop_policy` are a
closed set."

The note "For reviewers" (`specs/model-sidecar/changelog.md:5-10`) names MediaPipe-Exporter with the other
exporters (part 2.1).

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md` (exists) |
| Target file in skellytracker | `specs/model-sidecar/reference/pre_resize_rotated_roi_crop.py` |
| Functions (one for each algorithm) | `roi_is_valid`: heading "ROI", the validity test. `validate_crop_policy`: the rules `-2` to `-5` and `V-common.input-5`. `transform_roi`: heading "ROI transform". `fit_roi_aspect`: step 3. `crop_roi`: steps 1 to 3, the crop ROI. `crop_matrix`: step 4. `project_points`: step 4, the map of source points with `M` (the vectors check the corner convention with it). `rotated_roi_crop`: steps 1 to 5 for one batch item. `unproject_points`: heading "Inverse". |

- The note at the top of the file says `source commit: none (no host code)`. MediaPipe-Exporter has
  no git repo and no exporter code. The functions come from the text of part 2.
- The file uses NumPy, OpenCV and the Python standard library only. It does not import from an
  exporter or from skellytracker.
- This is a new section, so the file implements the full section: forward, inverse and every value
  of each field.
- `validate_crop_policy` checks the rules `-2` to `-5` completely: unknown keys, booleans, finite
  numbers, the border mode, `pad_value`, and `interpolation`. A boolean is not a number. `crop_roi`
  and `rotated_roi_crop` call it first. Thus a typo such as `shfit_y`, or the string `'false'` for
  `square_long`, is an error. It is not ignored. Rule `-1` needs the full sidecar (`role`, `pose`).
  The validator checks it, not this file.
- An ROI that does not have five values is an error of the host in `crop_roi`. `roi_is_valid` returns
  `false` for it.
- The refiner reference file, the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, loads this file. It has no
  copy of its functions. Its deleted PROVISIONAL copies gave the same results (part 4, a past result).
- `rotated_roi_crop` passes `pad_value` to `cv2.warpAffine` as one value for each channel. A scalar
  `borderValue` of OpenCV fills only channel 0 (`specs/exporter-guide/sidecars/workflow/mapping-hints.md:46-50`).
- The file computes in float64. The section states no precision (user decision Q7 = c), so float64
  is a choice of the file. A float32 host stays inside the tolerances of part 4 (part 1, the
  precision bullet).

```python
"""Reference implementation of the proposed section ``pre.resize.rotated_roi_crop`` (rotated ROI crop).

Note:
- Section ID: ``pre.resize.rotated_roi_crop`` (proposed). Proposal:
  ``specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`` (the full proposal of skellytracker 0020).
- Target file in skellytracker: ``specs/model-sidecar/reference/pre_resize_rotated_roi_crop.py``.
- source commit: none (no host code). MediaPipe-Exporter has no git repo and no exporter code. The
  functions come from the text of part 2 of the proposal.
- Vector results: the 78 vectors of part 4 pass against this file (78 of 78, 2026-10-24, after the
  Q7 = (c) change of the ``compare`` tolerances and of the matrix cases). They are
  ``unverified: no host implementation``. The probe geometry
  ``notes/decisions/scripts/hand_roi_reference.py`` (no commit) gives the same results for the square
  cases that it can run. It is not an independent implementation.
- Parity result: to run (MediaPipe-Exporter has no git repo).
- The proposal ``roi-refiner-role`` (section ``post.roi_refiner``) uses ``roi_is_valid``,
  ``transform_roi``, ``unproject_points`` and ``validate_crop_policy`` of this file. Its reference
  file loads this file and has no copy of them. Its earlier PROVISIONAL copies ``transform_roi`` and
  ``crop_points_to_source`` are deleted. Before the deletion, they gave the same results (part 4 of
  this proposal, a past result).
- ``validate_crop_policy`` checks the rules ``V-pre.resize.rotated_roi_crop-2`` to ``-5`` and the
  form of ``pad_value`` (``V-common.input-5``) completely. ``crop_roi`` and ``rotated_roi_crop`` call
  it first. A wrong key or a wrong type is an error. It is not ignored.
- ``interpolation`` must be ``linear`` (proposal choice, Q11). ``cv2.warpAffine`` has no area
  resampling: with ``cv2.INTER_AREA`` it gives the ``linear`` result.

- Precision (user decision Q7 = (c), 2026-10-24): the section states no arithmetic precision. The
  vectors give the tolerances in ``compare``. This file computes in float64. That is a choice of
  this file, not a rule of the section.
- ``project_points`` maps source points with ``M`` (step 4). The ``project_points`` vectors check the
  corner convention of ``M`` within the tolerance of the vectors.

Conventions: all geometry is in float64 pixels of the source image, with a top-left origin, ``x`` to
the right and ``y`` down. An ROI is ``(cx, cy, w, h, rotation)``. The rotation is in radians,
clockwise on the image. ``target_hw`` is ``[T_h, T_w]``.

Only NumPy, OpenCV and the Python standard library are used.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

ROI = tuple[float, float, float, float, float]

BORDER_MODES = {"constant": cv2.BORDER_CONSTANT, "replicate": cv2.BORDER_REPLICATE}
INTERPOLATIONS = {"linear": cv2.INTER_LINEAR}
CROP_POLICY_KEYS = ("transform", "maintain_aspect_ratio", "border_mode", "pad_value")
TRANSFORM_KEYS = ("shift_x", "shift_y", "square_long", "scale")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def roi_is_valid(roi: Sequence[float]) -> bool:
    """``pre.resize.rotated_roi_crop``, heading "ROI": the validity test.

    An ROI is valid only when it has five values, they are finite, ``w > 0`` and ``h > 0`` (strict).
    """
    values = [float(v) for v in roi]
    if len(values) != 5 or not all(math.isfinite(v) for v in values):
        return False
    return values[2] > 0.0 and values[3] > 0.0


def validate_crop_policy(crop_policy: Any, interpolation: Any = "linear") -> bool:
    """``pre.resize.rotated_roi_crop``, rules ``-2`` to ``-5``, and ``V-common.input-5``.

    Raises ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass.
    """
    if not isinstance(crop_policy, Mapping):
        raise ValueError("crop_policy must be a mapping")
    unknown = sorted(set(crop_policy) - set(CROP_POLICY_KEYS))
    if unknown:
        raise ValueError(f"unknown crop_policy key(s): {unknown}")
    if "maintain_aspect_ratio" not in crop_policy:
        raise ValueError("crop_policy.maintain_aspect_ratio is required")
    if not isinstance(crop_policy["maintain_aspect_ratio"], bool):
        raise ValueError("crop_policy.maintain_aspect_ratio must be a boolean")
    if "border_mode" not in crop_policy:
        raise ValueError("crop_policy.border_mode is required")
    mode = crop_policy["border_mode"]
    if mode not in BORDER_MODES:
        raise ValueError(f"unknown border_mode {mode!r}")
    if mode == "constant" and "pad_value" not in crop_policy:
        raise ValueError("border_mode constant needs pad_value")
    if mode == "replicate" and "pad_value" in crop_policy:
        raise ValueError("border_mode replicate must not have pad_value")
    if "pad_value" in crop_policy:
        pad = crop_policy["pad_value"]
        is_array = isinstance(pad, (list, tuple)) and len(pad) == 3 and all(_is_number(v) for v in pad)
        if not (_is_number(pad) or is_array):
            raise ValueError("crop_policy.pad_value must be a number or an array of 3 numbers")
    if "transform" in crop_policy:
        t = crop_policy["transform"]
        if not isinstance(t, Mapping):
            raise ValueError("crop_policy.transform must be a mapping")
        unknown = sorted(set(t) - set(TRANSFORM_KEYS))
        if unknown:
            raise ValueError(f"unknown crop_policy.transform key(s): {unknown}")
        for key in ("shift_x", "shift_y"):
            if key in t and not (_is_number(t[key]) and math.isfinite(t[key])):
                raise ValueError(f"crop_policy.transform.{key} must be a finite number")
        if "square_long" in t and not isinstance(t["square_long"], bool):
            raise ValueError("crop_policy.transform.square_long must be a boolean")
        if "scale" in t and not (_is_number(t["scale"]) and math.isfinite(t["scale"]) and t["scale"] > 0):
            raise ValueError("crop_policy.transform.scale must be a finite number > 0")
    if interpolation not in INTERPOLATIONS:
        raise ValueError("interpolation must be linear for rotated_roi_crop")
    return True


def transform_roi(
    roi: Sequence[float],
    shift_x: float = 0.0,
    shift_y: float = 0.0,
    square_long: bool = False,
    scale: float = 1.0,
) -> ROI:
    """``pre.resize.rotated_roi_crop``, heading "ROI transform".

    In this order: move the centre along the axes of the ROI by ``shift_x * w`` and ``shift_y * h``
    (``w`` and ``h`` before the next step), then make the ROI square with its longer side if
    ``square_long``, then multiply ``w`` and ``h`` by ``scale``. The rotation does not change.
    """
    if not (math.isfinite(scale) and scale > 0.0):
        raise ValueError("scale must be a finite number > 0")
    if not (math.isfinite(shift_x) and math.isfinite(shift_y)):
        raise ValueError("shift_x and shift_y must be finite numbers")
    cx, cy, w, h, rot = (float(v) for v in roi)
    c, s = math.cos(rot), math.sin(rot)
    cx = cx + w * shift_x * c - h * shift_y * s
    cy = cy + w * shift_x * s + h * shift_y * c
    if square_long:
        side = max(w, h)
        w = h = side
    return (cx, cy, w * scale, h * scale, rot)


def fit_roi_aspect(roi: Sequence[float], target_hw: Sequence[int]) -> ROI:
    """``pre.resize.rotated_roi_crop``, Behaviour step 3 (``maintain_aspect_ratio: true``).

    Enlarge the ROI along one axis to the aspect ratio ``T_w / T_h`` of the model input. The centre
    and the rotation do not change. The comparison is strict, as in ``affine_person_crop``.
    """
    cx, cy, w, h, rot = (float(v) for v in roi)
    t_h, t_w = float(target_hw[0]), float(target_hw[1])
    if w > h * (t_w / t_h):
        h = w * (t_h / t_w)
    else:
        w = h * (t_w / t_h)
    return (cx, cy, w, h, rot)


def crop_roi(roi: Sequence[float], crop_policy: dict, target_hw: Sequence[int]) -> ROI | None:
    """``pre.resize.rotated_roi_crop``, Behaviour steps 1 to 3: the crop ROI of one batch item.

    It validates ``crop_policy`` first. An ROI that does not have five values is an error of the
    host. Step 1 returns ``None`` (no crop) when a value of the ROI is not finite. Then it applies
    ``crop_policy.transform``. Step 2 returns ``None`` when the transformed ROI is not valid. Step 3
    applies ``maintain_aspect_ratio``.
    """
    validate_crop_policy(crop_policy)
    if len(roi) != 5:
        raise ValueError("roi must have 5 values")
    if not all(math.isfinite(float(v)) for v in roi):
        return None
    t = crop_policy.get("transform", {})
    roi1 = transform_roi(
        roi,
        shift_x=float(t.get("shift_x", 0.0)),
        shift_y=float(t.get("shift_y", 0.0)),
        square_long=t.get("square_long", False),
        scale=float(t.get("scale", 1.0)),
    )
    if not roi_is_valid(roi1):
        return None
    if crop_policy["maintain_aspect_ratio"]:
        return fit_roi_aspect(roi1, target_hw)
    return roi1


def crop_matrix(roi: Sequence[float], target_hw: Sequence[int]) -> np.ndarray:
    """``pre.resize.rotated_roi_crop``, Behaviour step 4: the 2x3 affine matrix ``M``.

    ``M`` maps the crop ROI onto ``[0, T_w] x [0, T_h]``: its top-left corner to ``(0, 0)``, its
    top-right corner to ``(T_w, 0)`` and its bottom-left corner to ``(0, T_h)``.
    """
    cx, cy, w, h, rot = (float(v) for v in roi)
    t_h, t_w = float(target_hw[0]), float(target_hw[1])
    sx, sy = t_w / w, t_h / h
    c, s = math.cos(rot), math.sin(rot)
    return np.array(
        [
            [sx * c, sx * s, t_w / 2.0 - sx * (c * cx + s * cy)],
            [-sy * s, sy * c, t_h / 2.0 - sy * (-s * cx + c * cy)],
        ],
        dtype=np.float64,
    )


def project_points(points: np.ndarray, roi: Sequence[float], target_hw: Sequence[int]) -> np.ndarray:
    """``pre.resize.rotated_roi_crop``, Behaviour step 4: map source points with ``M``.

    ``roi`` is the crop ROI. The vectors map the corners of the crop ROI with this function. The
    corner convention says that they go to the corners of ``[0, T_w] x [0, T_h]``.
    """
    m = crop_matrix(roi, target_hw)
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    return pts @ m[:, :2].T + m[:, 2]


def rotated_roi_crop(
    image: np.ndarray,
    roi: Sequence[float],
    crop_policy: dict,
    target_hw: Sequence[int],
    interpolation: str = "linear",
) -> tuple[np.ndarray, ROI] | None:
    """``pre.resize.rotated_roi_crop``, Behaviour steps 1 to 5: crop one batch item.

    Returns the crop (``[T_h, T_w, C]``, or ``[T_h, T_w]`` for a 2-D image) in the dtype of
    ``image`` and the crop ROI, or ``None`` when the ROI is not valid. Output pixel ``(i, j)`` takes
    the source value at ``M^-1 . (i, j)`` (``cv2.warpAffine``: pixel centres at integer
    coordinates). A scalar ``pad_value`` fills every channel. An array ``pad_value`` must have one
    value for each channel of the image.
    """
    validate_crop_policy(crop_policy, interpolation)
    mode = crop_policy["border_mode"]
    roi_c = crop_roi(roi, crop_policy, target_hw)
    if roi_c is None:
        return None
    m = crop_matrix(roi_c, target_hw)
    t_h, t_w = int(target_hw[0]), int(target_hw[1])
    channels = 1 if image.ndim == 2 else image.shape[2]
    border_value: tuple[float, ...] = (0.0,) * 4
    if mode == "constant":
        pad = np.asarray(crop_policy["pad_value"], dtype=np.float64).reshape(-1)
        if pad.size == 1:
            pad = np.full(channels, pad[0])
        if pad.size != channels:
            raise ValueError("pad_value must be a scalar or one value for each channel")
        border_value = tuple(float(v) for v in pad) + (0.0,) * (4 - channels)
    dst = cv2.warpAffine(
        image,
        m,
        (t_w, t_h),
        flags=INTERPOLATIONS[interpolation],
        borderMode=BORDER_MODES[mode],
        borderValue=border_value,
    )
    return dst, roi_c


def unproject_points(points: np.ndarray, roi: Sequence[float], target_hw: Sequence[int]) -> np.ndarray:
    """``pre.resize.rotated_roi_crop``, heading "Inverse": model-input pixels to source pixels.

    ``roi`` is the crop ROI (the result of ``crop_roi``). The inverse of a model-input point
    ``(x, y)`` is ``c + R(rotation) . ((x / T_w - 0.5) * w, (y / T_h - 0.5) * h)``. It is the exact
    inverse of ``M``.
    """
    cx, cy, w, h, rot = (float(v) for v in roi)
    t_h, t_w = float(target_hw[0]), float(target_hw[1])
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    u = (pts[:, 0] / t_w - 0.5) * w
    v = (pts[:, 1] / t_h - 0.5) * h
    c, s = math.cos(rot), math.sin(rot)
    return np.stack([cx + c * u - s * v, cy + s * u + c * v], axis=1)


if __name__ == "__main__":
    loose = (300.0, 200.0, 40.0, 40.0, 0.5)
    policy = {
        "transform": {"shift_y": -0.1, "square_long": True, "scale": 2.7},
        "maintain_aspect_ratio": True,
        "border_mode": "replicate",
    }
    roi_c = crop_roi(loose, policy, (256, 256))
    print("crop ROI", roi_c)
    print("M", crop_matrix(roi_c, (256, 256)))
    print("centre back", unproject_points([[128.0, 128.0]], roi_c, (256, 256)))
```

## 4. Vectors

The reference file made the first 59 vectors (scratch generator of an earlier session). The review
fix added 19 cases for the branches that had no case, and `border_mode: replicate` to the `crop_roi`
cases (`crop_roi` now validates the full policy).

**The tolerances (user decision Q7 = c, 2026-10-24).** The section states no arithmetic precision.
Thus each case whose result depends on the precision has its tolerance in `compare`: `1e-3` px for
an ROI value (`roi`: `cx`, `cy`, `w`, `h`), for a mapped corner and for an inverse point (`points`);
`1e-6` rad for a rotation (`rotation`); 1 grey level for each crop value (`image`). The bounds are
above the measured float32-against-float64 differences (part 1: at most 1.2e-4 px, 1.2e-7 rad and
1 grey level). On 2026-10-24 the cases changed in three ways. (1) The output ROI of each case is two
fields, `roi` (`cx`, `cy`, `w`, `h`) and `rotation`, because one `atol` applies to one field. The
input ROI keeps its five values. (2) The 8 `crop_matrix` cases became `project_points` cases. Each
maps the four corners of the crop ROI with `M`, and expects the corners of `[0, T_w] x [0, T_h]`
within `1e-3` px. A YAML comment keeps the matrix of the case. A tolerance on the matrix entries
does not bound the error of a mapped corner, because a translation entry is up to 719 here. (3) The
`atol` values went from `1e-9` (and `0` for the integer-sample pixel cases) to the bounds above. A
pure validation case keeps its form.

A scratch runner of this session (`mp-proposals\run_vectors.py` in the session scratchpad, not committed)
read this YAML block back from this file and ran each case through the reference file (loaded with
`importlib.util.spec_from_file_location`). Result on 2026-10-24: **78 of 78 pass** (`roi_is_valid` 8,
`transform_roi` 16, `fit_roi_aspect` 5, `crop_roi` 9, `validate_crop_policy` 11, `project_points` 8,
`unproject_points` 6, `rotated_roi_crop` 15). Before the change: 78 of 78 (with `crop_matrix` 8). A
mutation check changed one expected value: exactly one case failed (heading "Before you stop").
Environment: the `uv` environment of OpenMMLab-Exporter (Python 3.14.2, NumPy 2.5.4, OpenCV 5.0.0,
PyYAML 6.0.3). The cross-checks below are results of 2026-10-23. This session did not run them
again.

Cross-checks (none of them is an independent implementation):

- **Upstream converter logic (8 of 8 pass, 2026-10-23).** For each matrix case (now `project_points`), `cv2.boxPoints` of the
  ROI and `cv2.getPerspectiveTransform` onto the corners `{0, T_h}, {0, 0}, {T_w, 0}, {T_w, T_h}`
  (the steps of `image_to_tensor_converter_opencv.cc:135-153`) give `M` within `1e-3` relative (the
  corners are float32), and the third row is `[0, 0, 1]` within `1e-6`. This is a check against the
  upstream algorithm, run in OpenCV. It is not the upstream library.
- **Probe geometry (11 of 11 pass).** `notes/decisions/scripts/hand_roi_reference.py` (MediaPipe-Exporter
  0006; no commit) gives the same transform for the 5 `transform_roi` cases that it can run (square
  output, no `shift_x`, `w > 0`), the same crop inverse as `cv2.invertAffineTransform(M)` for 3
  square ROIs (`crop`, within `1e-3`), and the same projection for 3 square ROIs
  (`project_landmarks` against `unproject_points`, within `1e-9`). The probe is in the same
  exporter, and it has no commit. Thus the vectors stay `unverified`.
- **The refiner provisional copies (a past result: 18 of 18, and 10 of 10).** An earlier run of
  2026-10-23 passed the 12 `transform_roi` cases with a result and the 6 `unproject_points` cases of
  this section through the PROVISIONAL functions `transform_roi` and `crop_points_to_source` of the
  refiner reference file, and its 10 `provisional: skellytracker 0020` cases through this file. The
  refiner proposal then deleted those functions and cases. Its file now loads this file, so no
  second copy remains to compare (refiner proposal part 3).
- **Pixel cases.** A direct-index check (integer sample points, the border rule by hand) gives the
  same images for the 6 exact pixel cases of the earlier session. The bilinear case agrees with the
  ramp values within 1. The new 2-D case is channel 0 of `crop-constant-scalar-fills-every-channel`
  (checked by hand).

Coverage: the validity test (positive, `w = 0` and `h = 0` at the strict limit, negative, tiny
positive, NaN, infinity, four values); each transform field, the shift along a rotated axis (0, π/2,
π, π/6), the shift before `square_long`, `square_long` on `w`, on `h` and at the tie `w == h`, the
scale with and without `square_long`, the Holistic loose hand transform, a zero width that
`square_long` repairs, three scale errors (0, −1, infinity) and a NaN shift; the aspect step for a
wide and a tall ROI, at the tie (strict `>`), and on a non-square input; the order of the transform
and the aspect step, the check after the transform, NaN and infinity, the missing
`maintain_aspect_ratio`, and an ROI with four values (an error); the validation of rules `-2` to
`-5`: a full valid policy, an unknown `crop_policy` key, a string for `maintain_aspect_ratio`, no
`border_mode`, two pad values, an unknown transform key (`shfit_y`), the string `'false'` for
`square_long`, a NaN shift, an infinite scale, and `area` and `cubic`; the matrix (through the mapped corners) at rotation 0 (one and two
scales), ±π/2, the tie π and −π, 3π (no range limit), and a rotated non-square ROI on a non-square
input; the inverse at the centre, at the corners (corner convention), at π/2, for a non-square
rotated ROI (the MediaPipe `NORM_RECT`-only value in the comment) and on a non-square input, and a
round trip; the pixel cases for `replicate`, a scalar `pad_value` on a 3-channel input, a
per-channel `pad_value`, a quarter turn, a downscale with no antialias, an aspect step that changes
the crop, a bilinear upscale (`atol: 1`), no crop for an ROI that is not valid, three border
errors, a 2-D image with a scalar `pad_value`, three pad values on a 2-D image (an error), two pad
values on a 3-channel image (an error), and `nearest` (an error). `linear` is the only allowed
interpolation (Q11), and every pixel case uses it.

Pixel cases use 3 × 3 and 4 × 4 images. Each has its tolerance in `compare`: `atol: 1` (one grey
level, Q7 = c). Before 2026-10-24 the integer-sample cases had `atol: 0`. A wrong border or a wrong
scalar fill still fails: those values differ by more than 1 (for example `[7, 0, 0]` against
`[7, 7, 7]`).
The target file is `specs/model-sidecar/vectors/pre.resize.rotated_roi_crop.yaml`.

```yaml
section: pre.resize.rotated_roi_crop
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`
unverified: no host implementation. MediaPipe-Exporter has no git repo and no exporter code. The probe
  geometry notes/decisions/scripts/hand_roi_reference.py (no commit) gives the same results for the
  square cases that it can run.
cases:
  # five finite values, w > 0 and h > 0
  - id: valid-positive
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, 30.0, 40.0, 0.5]
    expect: {valid: true}
  # w = 0 fails the strict test
  - id: invalid-w-zero
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, 0.0, 40.0, 0.0]
    expect: {valid: false}
  # h = 0 fails the strict test
  - id: invalid-h-zero
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, 30.0, 0.0, 0.0]
    expect: {valid: false}
  # a negative size fails
  - id: invalid-w-negative
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, -1.0, 40.0, 0.0]
    expect: {valid: false}
  # any positive size passes
  - id: valid-tiny
    function: roi_is_valid
    params: {}
    input:
      roi: [0.0, 0.0, 1.0e-12, 1.0e-12, 0.0]
    expect: {valid: true}
  # a NaN value fails
  - id: invalid-nan-centre
    function: roi_is_valid
    params: {}
    input:
      roi: [.nan, 20.0, 30.0, 40.0, 0.0]
    expect: {valid: false}
  # an infinite value fails
  - id: invalid-inf-rotation
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, 30.0, 40.0, .inf]
    expect: {valid: false}
  # an ROI must have five values
  - id: invalid-length-4
    function: roi_is_valid
    params: {}
    input:
      roi: [10.0, 20.0, 30.0, 40.0]
    expect: {valid: false}
  # the defaults change nothing
  - id: transform-defaults-identity
    function: transform_roi
    params: {}
    input:
      roi: [10.0, 20.0, 30.0, 40.0, 1.0]
    expect:
      roi: [10.0, 20.0, 30.0, 40.0]
      rotation: 1.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # cy + 60 * -0.1 = 94
  - id: transform-shift-y-rotation-0
    function: transform_roi
    params: {shift_y: -0.1}
    input:
      roi: [100.0, 100.0, 80.0, 60.0, 0.0]
    expect:
      roi: [100.0, 94.0, 80.0, 60.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the shift is along the ROI y axis: cx - 60 * -0.1 * sin(pi/2) = 106
  - id: transform-shift-y-rotation-half-pi
    function: transform_roi
    params: {shift_y: -0.1}
    input:
      roi: [100.0, 100.0, 80.0, 60.0, 1.5707963267948966]
    expect:
      roi: [106.0, 100.0, 80.0, 60.0]
      rotation: 1.570796326795
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the ROI x axis points to -x: cx - 80 * 0.25 = 80
  - id: transform-shift-x-rotation-pi
    function: transform_roi
    params: {shift_x: 0.25}
    input:
      roi: [100.0, 100.0, 80.0, 60.0, 3.141592653589793]
    expect:
      roi: [80.0, 100.0, 80.0, 60.0]
      rotation: 3.14159265359
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # both shifts; the same case as the roi-refiner-role vector
  - id: transform-shift-x-and-y-rotation-pi-6
    function: transform_roi
    params: {shift_x: 0.2, shift_y: 0.4}
    input:
      roi: [0.0, 0.0, 100.0, 50.0, 0.5235987755982988]
    expect:
      roi: [7.320508075689, 27.320508075689, 100.0, 50.0]
      rotation: 0.523598775598
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the shift uses h = 60, then square_long makes 80 x 80
  - id: transform-shift-uses-size-before-square
    function: transform_roi
    params: {shift_y: -0.1, square_long: true}
    input:
      roi: [100.0, 100.0, 80.0, 60.0, 0.0]
    expect:
      roi: [100.0, 94.0, 80.0, 80.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # w > h: the side is 50
  - id: transform-square-long-takes-w
    function: transform_roi
    params: {square_long: true}
    input:
      roi: [10.0, 20.0, 50.0, 30.0, 0.0]
    expect:
      roi: [10.0, 20.0, 50.0, 50.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # h > w: the side is 40
  - id: transform-square-long-takes-h
    function: transform_roi
    params: {square_long: true}
    input:
      roi: [10.0, 20.0, 30.0, 40.0, 0.0]
    expect:
      roi: [10.0, 20.0, 40.0, 40.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # w == h: the side is 30, then 45
  - id: transform-square-long-tie
    function: transform_roi
    params: {square_long: true, scale: 1.5}
    input:
      roi: [10.0, 20.0, 30.0, 30.0, 0.0]
    expect:
      roi: [10.0, 20.0, 45.0, 45.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # no square_long: 60 x 80
  - id: transform-scale-keeps-aspect
    function: transform_roi
    params: {scale: 2.0}
    input:
      roi: [10.0, 20.0, 30.0, 40.0, 0.0]
    expect:
      roi: [10.0, 20.0, 60.0, 80.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the Holistic loose hand ROI transform (docs/mediapipe-whole-body.md:387-389)
  - id: transform-hand-loose-roi
    function: transform_roi
    params: {shift_y: -0.1, square_long: true, scale: 2.7}
    input:
      roi: [300.0, 200.0, 40.0, 40.0, 0.5]
    expect:
      roi: [301.917702154417, 196.489669752439, 108.0, 108.0]
      rotation: 0.5
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # w = 0 becomes 5: the check comes after the transform
  - id: transform-square-long-repairs-zero-width
    function: transform_roi
    params: {square_long: true}
    input:
      roi: [10.0, 20.0, 0.0, 5.0, 0.0]
    expect:
      roi: [10.0, 20.0, 5.0, 5.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # scale must be > 0
  - id: transform-error-scale-zero
    function: transform_roi
    params: {scale: 0.0}
    input:
      roi: [0.0, 0.0, 1.0, 1.0, 0.0]
    expect: {error: scale must be a finite number > 0}
  # scale must be > 0
  - id: transform-error-scale-negative
    function: transform_roi
    params: {scale: -1.0}
    input:
      roi: [0.0, 0.0, 1.0, 1.0, 0.0]
    expect: {error: scale must be a finite number > 0}
  # scale must be finite
  - id: transform-error-scale-inf
    function: transform_roi
    params: {scale: .inf}
    input:
      roi: [0.0, 0.0, 1.0, 1.0, 0.0]
    expect: {error: scale must be a finite number > 0}
  # a shift must be finite
  - id: transform-error-shift-y-nan
    function: transform_roi
    params: {shift_y: .nan}
    input:
      roi: [0.0, 0.0, 1.0, 1.0, 0.0]
    expect: {error: shift_x and shift_y must be finite numbers}
  # 100 > 40: h becomes 100
  - id: aspect-wide-roi-square-input
    function: fit_roi_aspect
    params:
      target_size: [256, 256]
    input:
      roi: [50.0, 60.0, 100.0, 40.0, 0.3]
    expect:
      roi: [50.0, 60.0, 100.0, 100.0]
      rotation: 0.3
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # 40 < 100: w becomes 100
  - id: aspect-tall-roi-square-input
    function: fit_roi_aspect
    params:
      target_size: [256, 256]
    input:
      roi: [50.0, 60.0, 40.0, 100.0, 0.3]
    expect:
      roi: [50.0, 60.0, 100.0, 100.0]
      rotation: 0.3
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # 75 > 100 * 0.75 is false (strict): w = 100 * 0.75 = 75, no change
  - id: aspect-tie-unchanged
    function: fit_roi_aspect
    params:
      target_size: [256, 192]
    input:
      roi: [0.0, 0.0, 75.0, 100.0, 0.0]
    expect:
      roi: [0.0, 0.0, 75.0, 100.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # 150 > 75: h = 150 * 256 / 192 = 200
  - id: aspect-non-square-input-wide
    function: fit_roi_aspect
    params:
      target_size: [256, 192]
    input:
      roi: [0.0, 0.0, 150.0, 100.0, 0.0]
    expect:
      roi: [0.0, 0.0, 150.0, 200.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # 30 < 75: w = 75; rotation kept
  - id: aspect-non-square-input-tall
    function: fit_roi_aspect
    params:
      target_size: [256, 192]
    input:
      roi: [0.0, 0.0, 30.0, 100.0, -1.0]
    expect:
      roi: [0.0, 0.0, 75.0, 100.0]
      rotation: -1.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # cy = 0 + 20 * 0.5 = 10 first; then h = 40. The other order gives cy = 20
  - id: crop-roi-shift-before-aspect
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy:
        transform: {shift_y: 0.5}
        maintain_aspect_ratio: true
        border_mode: replicate
    input:
      roi: [0.0, 0.0, 40.0, 20.0, 0.0]
    expect:
      roi: [0.0, 10.0, 40.0, 40.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # 60 x 40, then 60 x 60
  - id: crop-roi-scale-then-aspect
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy:
        transform: {scale: 2.0}
        maintain_aspect_ratio: true
        border_mode: replicate
    input:
      roi: [10.0, 10.0, 30.0, 20.0, 0.0]
    expect:
      roi: [10.0, 10.0, 60.0, 60.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # no transform, no aspect step
  - id: crop-roi-no-aspect
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
    input:
      roi: [0.0, 0.0, 40.0, 20.0, 0.0]
    expect:
      roi: [0.0, 0.0, 40.0, 20.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # w = 0: no crop
  - id: crop-roi-invalid-gives-none
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
    input:
      roi: [0.0, 0.0, 0.0, 20.0, 0.0]
    expect: {roi: null}
  # the check is after the transform: 20 x 20
  - id: crop-roi-square-long-makes-valid
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy:
        transform: {square_long: true}
        maintain_aspect_ratio: false
        border_mode: replicate
    input:
      roi: [0.0, 0.0, 0.0, 20.0, 0.0]
    expect:
      roi: [0.0, 0.0, 20.0, 20.0]
      rotation: 0.0
    compare:
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # a NaN value: no crop
  - id: crop-roi-nan-gives-none
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {maintain_aspect_ratio: true, border_mode: replicate}
    input:
      roi: [.nan, 0.0, 10.0, 10.0, 0.0]
    expect: {roi: null}
  # an infinite rotation: no crop
  - id: crop-roi-inf-rotation-gives-none
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {maintain_aspect_ratio: true, border_mode: replicate}
    input:
      roi: [0.0, 0.0, 10.0, 10.0, .inf]
    expect: {roi: null}
  # maintain_aspect_ratio is required
  - id: crop-roi-error-no-maintain-aspect-ratio
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {border_mode: replicate}
    input:
      roi: [0.0, 0.0, 1.0, 1.0, 0.0]
    expect: {error: crop_policy.maintain_aspect_ratio is required}
  # an ROI with four values is an error of the host, not "no crop"
  - id: crop-roi-error-length-4
    function: crop_roi
    params:
      target_size: [256, 256]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
    input:
      roi: [0.0, 0.0, 1.0, 1.0]
    expect: {error: roi must have 5 values}
  # every key and type of rules -2 to -5, with constant and a per-channel pad_value
  - id: validate-full-policy
    function: validate_crop_policy
    params:
      crop_policy:
        transform: {shift_x: 0.0, shift_y: -0.1, square_long: true, scale: 2.7}
        maintain_aspect_ratio: true
        border_mode: constant
        pad_value: [0, 0, 0]
      interpolation: linear
    input: {}
    expect: {valid: true}
  # V-pre.resize.rotated_roi_crop-2: the key set is closed (expand_ratio is an affine_person_crop key)
  - id: validate-error-unknown-key
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate, expand_ratio: 1.25}
      interpolation: linear
    input: {}
    expect: {error: 'unknown crop_policy key(s): [''expand_ratio'']'}
  # V-pre.resize.rotated_roi_crop-2: a string is not a boolean
  - id: validate-error-maintain-aspect-ratio-string
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: 'no', border_mode: replicate}
      interpolation: linear
    input: {}
    expect: {error: crop_policy.maintain_aspect_ratio must be a boolean}
  # V-pre.resize.rotated_roi_crop-2: border_mode is required
  - id: validate-error-no-border-mode
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: false}
      interpolation: linear
    input: {}
    expect: {error: crop_policy.border_mode is required}
  # V-common.input-5: a number or an array of 3 numbers
  - id: validate-error-pad-value-length-2
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant, pad_value: [1, 2]}
      interpolation: linear
    input: {}
    expect: {error: crop_policy.pad_value must be a number or an array of 3 numbers}
  # V-pre.resize.rotated_roi_crop-4: a typo is an error, not an ignored key
  - id: validate-error-transform-unknown-key
    function: validate_crop_policy
    params:
      crop_policy:
        transform: {shfit_y: 0.5}
        maintain_aspect_ratio: false
        border_mode: replicate
      interpolation: linear
    input: {}
    expect: {error: 'unknown crop_policy.transform key(s): [''shfit_y'']'}
  # V-pre.resize.rotated_roi_crop-4: the string 'false' is not a boolean
  - id: validate-error-square-long-string
    function: validate_crop_policy
    params:
      crop_policy:
        transform: {square_long: 'false'}
        maintain_aspect_ratio: false
        border_mode: replicate
      interpolation: linear
    input: {}
    expect: {error: crop_policy.transform.square_long must be a boolean}
  # V-pre.resize.rotated_roi_crop-4: a shift must be finite
  - id: validate-error-shift-y-nan
    function: validate_crop_policy
    params:
      crop_policy:
        transform: {shift_y: .nan}
        maintain_aspect_ratio: false
        border_mode: replicate
      interpolation: linear
    input: {}
    expect: {error: crop_policy.transform.shift_y must be a finite number}
  # V-pre.resize.rotated_roi_crop-4: scale must be finite
  - id: validate-error-scale-inf
    function: validate_crop_policy
    params:
      crop_policy:
        transform: {scale: .inf}
        maintain_aspect_ratio: false
        border_mode: replicate
      interpolation: linear
    input: {}
    expect: {error: crop_policy.transform.scale must be a finite number > 0}
  # V-pre.resize.rotated_roi_crop-5: warpAffine has no area resampling (area gives the linear result)
  - id: validate-error-interpolation-area
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: area
    input: {}
    expect: {error: interpolation must be linear for rotated_roi_crop}
  # V-pre.resize.rotated_roi_crop-5: cubic and nearest are not added at vNEXT (Q11)
  - id: validate-error-interpolation-cubic
    function: validate_crop_policy
    params:
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: cubic
    input: {}
    expect: {error: interpolation must be linear for rotated_roi_crop}
  # the ROI [0, 4] x [0, 4] maps onto the input: identity
  # M = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]] (the reference value; not compared)
  - id: matrix-axis-aligned-unit-scale
    function: project_points
    params:
      target_size: [4, 4]
    input:
      points: [[0.0, 0.0], [4.0, 0.0], [0.0, 4.0], [4.0, 4.0]]
      roi: [2.0, 2.0, 4.0, 4.0, 0.0]
    expect:
      points: [[0.0, 0.0], [4.0, 0.0], [0.0, 4.0], [4.0, 4.0]]
    compare:
      points: {atol: 1.0e-03}
  # sx = 50 / 100, sy = 10 / 40: maintain_aspect_ratio false allows two scales
  # M = [[0.5, 0.0, 0.0], [0.0, 0.25, -5.0]] (the reference value; not compared)
  - id: matrix-axis-aligned-anisotropic
    function: project_points
    params:
      target_size: [10, 50]
    input:
      points: [[0.0, 20.0], [100.0, 20.0], [0.0, 60.0], [100.0, 60.0]]
      roi: [50.0, 40.0, 100.0, 40.0, 0.0]
    expect:
      points: [[0.0, 0.0], [50.0, 0.0], [0.0, 10.0], [50.0, 10.0]]
    compare:
      points: {atol: 1.0e-03}
  # clockwise quarter turn: the ROI x axis points down the image
  # M = [[0.0, 2.0, -150.0], [-2.0, 0.0, 250.0]] (the reference value; not compared)
  - id: matrix-rotation-half-pi
    function: project_points
    params:
      target_size: [100, 100]
    input:
      points: [[125.0, 75.0], [125.0, 125.0], [75.0, 75.0], [75.0, 125.0]]
      roi: [100.0, 100.0, 50.0, 50.0, 1.5707963267948966]
    expect:
      points: [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]]
    compare:
      points: {atol: 1.0e-03}
  # counter-clockwise quarter turn
  # M = [[0.0, -2.0, 250.0], [2.0, 0.0, -150.0]] (the reference value; not compared)
  - id: matrix-rotation-minus-half-pi
    function: project_points
    params:
      target_size: [100, 100]
    input:
      points: [[75.0, 125.0], [75.0, 75.0], [125.0, 125.0], [125.0, 75.0]]
      roi: [100.0, 100.0, 50.0, 50.0, -1.5707963267948966]
    expect:
      points: [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]]
    compare:
      points: {atol: 1.0e-03}
  # half turn
  # M = [[-2.0, 0.0, 250.0], [0.0, -2.0, 250.0]] (the reference value; not compared)
  - id: matrix-rotation-pi
    function: project_points
    params:
      target_size: [100, 100]
    input:
      points: [[125.0, 125.0], [75.0, 125.0], [125.0, 75.0], [75.0, 75.0]]
      roi: [100.0, 100.0, 50.0, 50.0, 3.141592653589793]
    expect:
      points: [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]]
    compare:
      points: {atol: 1.0e-03}
  # -pi gives the matrix of +pi
  # M = [[-2.0, 0.0, 250.0], [0.0, -2.0, 250.0]] (the reference value; not compared)
  - id: matrix-rotation-minus-pi-tie
    function: project_points
    params:
      target_size: [100, 100]
    input:
      points: [[125.0, 125.0], [75.0, 125.0], [125.0, 75.0], [75.0, 75.0]]
      roi: [100.0, 100.0, 50.0, 50.0, -3.141592653589793]
    expect:
      points: [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]]
    compare:
      points: {atol: 1.0e-03}
  # the spec does not limit the range: 3pi gives the matrix of pi
  # M = [[-2.0, 0.0, 250.0], [0.0, -2.0, 250.0]] (the reference value; not compared)
  - id: matrix-rotation-3pi-no-range-limit
    function: project_points
    params:
      target_size: [100, 100]
    input:
      points: [[125.00000000000001, 124.99999999999999], [75.00000000000001, 125.00000000000001], [124.99999999999999, 74.99999999999999], [74.99999999999999, 75.00000000000001]]
      roi: [100.0, 100.0, 50.0, 50.0, 9.42477796076938]
    expect:
      points: [[0.0, 0.0], [100.0, 0.0], [0.0, 100.0], [100.0, 100.0]]
    compare:
      points: {atol: 1.0e-03}
  # a rotated non-square ROI and a non-square input
  # M = [[1.847520861407, 1.066666666667, -719.206675650177], [-1.066666666667, 1.847520861407, -6.071673404299]] (the reference value; not compared)
  - id: matrix-rotation-pi-6-non-square
    function: project_points
    params:
      target_size: [192, 256]
    input:
      points: [[290.5384757729337, 171.02885682970026], [394.4615242270663, 231.02885682970026], [245.53847577293368, 248.97114317029974], [349.4615242270663, 308.97114317029974]]
      roi: [320.0, 240.0, 120.0, 90.0, 0.5235987755982988]
    expect:
      points: [[0.0, 0.0], [256.0, 0.0], [0.0, 192.0], [256.0, 192.0]]
    compare:
      points: {atol: 1.0e-03}
  # the input centre is the ROI centre at every rotation
  - id: unproject-centre
    function: unproject_points
    params:
      target_size: [256, 256]
    input:
      points: [[128.0, 128.0]]
      roi: [500.0, 400.0, 200.0, 100.0, 0.7]
    expect:
      points: [[500.0, 400.0]]
    compare:
      points: {atol: 1.0e-03}
  # corner convention: (0, 0) is the top-left ROI corner, (T_w, T_h) the bottom-right corner
  - id: unproject-corner-convention
    function: unproject_points
    params:
      target_size: [256, 256]
    input:
      points: [[0.0, 0.0], [256.0, 256.0], [256.0, 0.0]]
      roi: [500.0, 400.0, 200.0, 100.0, 0.0]
    expect:
      points: [[400.0, 350.0], [600.0, 450.0], [600.0, 350.0]]
    compare:
      points: {atol: 1.0e-03}
  # the right edge of the input maps below the centre; the same case as the roi-refiner-role vector
  - id: unproject-rotation-half-pi
    function: unproject_points
    params:
      target_size: [256, 256]
    input:
      points: [[256.0, 128.0]]
      roi: [500.0, 400.0, 200.0, 200.0, 1.5707963267948966]
    expect:
      points: [[500.0, 500.0]]
    compare:
      points: {atol: 1.0e-03}
  # exact inverse. The MediaPipe NORM_RECT-only projection gives (154.641016, 92.679492) here;
  # MediaPipe supports that path only for a square ROI (landmark_projection_calculator.cc:78-81)
  - id: unproject-non-square-rotated
    function: unproject_points
    params:
      target_size: [224, 224]
    input:
      points: [[224.0, 0.0]]
      roi: [100.0, 100.0, 80.0, 40.0, 0.5235987755982988]
    expect:
      points: [[144.641016151378, 102.679491924311]]
    compare:
      points: {atol: 1.0e-03}
  # T_w = 256, T_h = 192: bottom-left and top-right input corners
  - id: unproject-non-square-input
    function: unproject_points
    params:
      target_size: [192, 256]
    input:
      points: [[0.0, 192.0], [256.0, 0.0]]
      roi: [320.0, 240.0, 120.0, 90.0, 0.5235987755982988]
    expect:
      points: [[245.538475772934, 248.9711431703], [394.461524227066, 231.0288568297]]
    compare:
      points: {atol: 1.0e-03}
  # model-input points made by M from the source points (300, 250) and (355.5, 199.25) map back to
  # them
  - id: unproject-round-trip
    function: unproject_points
    params:
      target_size: [192, 256]
    input:
      points: [[174.94953333755353, 104.44374768343414], [15.299545121808308, 120.32179459807378]]
      roi: [320.0, 240.0, 120.0, 90.0, 2.5]
    expect:
      points: [[300.0, 250.0], [355.5, 199.25]]
    compare:
      points: {atol: 1.0e-03}
  # integer sample points x = i - 1, y = j - 1: row 0 and column 0 repeat the edge
  - id: crop-replicate-left-top-border
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect:
      image: [[[1, 2, 3], [1, 2, 3], [11, 12, 13], [21, 22, 23]], [[1, 2, 3], [1, 2, 3], [11, 12, 13], [
            21, 22, 23]], [[31, 32, 33], [31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61, 62, 63], [61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # a scalar pad_value on a 3-channel input gives [7, 7, 7], not [7, 0, 0]
  - id: crop-constant-scalar-fills-every-channel
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant, pad_value: 7}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect:
      image: [[[7, 7, 7], [7, 7, 7], [7, 7, 7], [7, 7, 7]], [[7, 7, 7], [1, 2, 3], [11, 12, 13], [21, 22,
            23]], [[7, 7, 7], [31, 32, 33], [41, 42, 43], [51, 52, 53]], [[7, 7, 7], [61, 62, 63], [71,
            72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # one pad value for each channel
  - id: crop-constant-per-channel
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy:
        maintain_aspect_ratio: false
        border_mode: constant
        pad_value: [1, 2, 3]
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect:
      image: [[[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]], [[1, 2, 3], [1, 2, 3], [11, 12, 13], [21, 22,
            23]], [[1, 2, 3], [31, 32, 33], [41, 42, 43], [51, 52, 53]], [[1, 2, 3], [61, 62, 63], [71,
            72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # output (i, j) takes source x = 3 - j, y = i - 1 (clockwise quarter turn)
  - id: crop-rotation-half-pi
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[0, 4, 8], [8, 12, 16], [16, 20, 24], [24, 28, 32]], [[32, 36, 40], [40, 44, 48], [48, 52,
            56], [56, 60, 64]], [[64, 68, 72], [72, 76, 80], [80, 84, 88], [88, 92, 96]], [[96, 100, 104],
          [104, 108, 112], [112, 116, 120], [120, 124, 128]]]
      roi: [1.0, 1.0, 4.0, 4.0, 1.5707963267948966]
    expect:
      image: [[[24, 28, 32], [24, 28, 32], [56, 60, 64], [88, 92, 96]], [[16, 20, 24], [16, 20, 24], [48,
            52, 56], [80, 84, 88]], [[8, 12, 16], [8, 12, 16], [40, 44, 48], [72, 76, 80]], [[0, 4, 8],
          [0, 4, 8], [32, 36, 40], [64, 68, 72]]]
      roi: [1.0, 1.0, 4.0, 4.0]
      rotation: 1.570796326795
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # sample points x = 2i, y = 2j: no antialias, the other pixels do not count
  - id: crop-downscale-no-antialias
    function: rotated_roi_crop
    params:
      target_size: [2, 2]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[0, 4, 8], [8, 12, 16], [16, 20, 24], [24, 28, 32]], [[32, 36, 40], [40, 44, 48], [48, 52,
            56], [56, 60, 64]], [[64, 68, 72], [72, 76, 80], [80, 84, 88], [88, 92, 96]], [[96, 100, 104],
          [104, 108, 112], [112, 116, 120], [120, 124, 128]]]
      roi: [2.0, 2.0, 4.0, 4.0, 0.0]
    expect:
      image: [[[0, 4, 8], [16, 20, 24]], [[64, 68, 72], [80, 84, 88]]]
      roi: [2.0, 2.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # the 4 x 2 ROI grows to 4 x 4 around its centre: the crop is the image
  - id: crop-maintain-aspect-ratio-enlarges
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: true, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[0, 4, 8], [8, 12, 16], [16, 20, 24], [24, 28, 32]], [[32, 36, 40], [40, 44, 48], [48, 52,
            56], [56, 60, 64]], [[64, 68, 72], [72, 76, 80], [80, 84, 88], [88, 92, 96]], [[96, 100, 104],
          [104, 108, 112], [112, 116, 120], [120, 124, 128]]]
      roi: [2.0, 2.0, 4.0, 2.0, 0.0]
    expect:
      image: [[[0, 4, 8], [8, 12, 16], [16, 20, 24], [24, 28, 32]], [[32, 36, 40], [40, 44, 48], [48, 52,
            56], [56, 60, 64]], [[64, 68, 72], [72, 76, 80], [80, 84, 88], [88, 92, 96]], [[96, 100, 104],
          [104, 108, 112], [112, 116, 120], [120, 124, 128]]]
      roi: [2.0, 2.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # sample points x = i / 2, y = j / 2 on a linear ramp: bilinear gives the ramp value; atol 1 for
  # the fixed-point arithmetic of OpenCV
  - id: crop-upscale-linear-half-way
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[0, 4, 8], [8, 12, 16], [16, 20, 24], [24, 28, 32]], [[32, 36, 40], [40, 44, 48], [48, 52,
            56], [56, 60, 64]], [[64, 68, 72], [72, 76, 80], [80, 84, 88], [88, 92, 96]], [[96, 100, 104],
          [104, 108, 112], [112, 116, 120], [120, 124, 128]]]
      roi: [1.0, 1.0, 2.0, 2.0, 0.0]
    expect:
      image: [[[0, 4, 8], [4, 8, 12], [8, 12, 16], [12, 16, 20]], [[16, 20, 24], [20, 24, 28], [24, 28,
            32], [28, 32, 36]], [[32, 36, 40], [36, 40, 44], [40, 44, 48], [44, 48, 52]], [[48, 52, 56],
          [52, 56, 60], [56, 60, 64], [60, 64, 68]]]
      roi: [1.0, 1.0, 2.0, 2.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # w = 0: no crop and no input for this item
  - id: crop-invalid-roi-no-crop
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: true, border_mode: replicate}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 0.0, 4.0, 0.0]
    expect: {image: null}
  # pad_value only with constant
  - id: crop-error-replicate-with-pad-value
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate, pad_value: 0}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: border_mode replicate must not have pad_value}
  # constant needs pad_value
  - id: crop-error-constant-without-pad-value
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: border_mode constant needs pad_value}
  # the set is closed
  - id: crop-error-unknown-border-mode
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: reflect}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: unknown border_mode 'reflect'}
  # a 2-D (single-channel) image: a scalar pad_value fills its one channel
  - id: crop-2d-image-scalar-pad-value
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant, pad_value: 7}
      interpolation: linear
    input:
      image: [[1, 11, 21], [31, 41, 51], [61, 71, 81]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect:
      image: [[7, 7, 7, 7], [7, 1, 11, 21], [7, 31, 41, 51], [7, 61, 71, 81]]
      roi: [1.0, 1.0, 4.0, 4.0]
      rotation: 0.0
    compare:
      image: {atol: 1}
      roi: {atol: 1.0e-03}
      rotation: {atol: 1.0e-06}
  # a 2-D image has one channel: an array of 3 pad values does not fit
  - id: crop-error-2d-image-pad-value-array
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant, pad_value: [1, 2, 3]}
      interpolation: linear
    input:
      image: [[1, 11, 21], [31, 41, 51], [61, 71, 81]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: pad_value must be a scalar or one value for each channel}
  # two pad values on a 3-channel image fail V-common.input-5 before the warp
  - id: crop-error-pad-value-length-2
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: constant, pad_value: [1, 2]}
      interpolation: linear
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: crop_policy.pad_value must be a number or an array of 3 numbers}
  # rotated_roi_crop applies V-pre.resize.rotated_roi_crop-5 too
  - id: crop-error-interpolation-nearest
    function: rotated_roi_crop
    params:
      target_size: [4, 4]
      crop_policy: {maintain_aspect_ratio: false, border_mode: replicate}
      interpolation: nearest
    input:
      image: [[[1, 2, 3], [11, 12, 13], [21, 22, 23]], [[31, 32, 33], [41, 42, 43], [51, 52, 53]], [[61,
            62, 63], [71, 72, 73], [81, 82, 83]]]
      roi: [1.0, 1.0, 4.0, 4.0, 0.0]
    expect: {error: interpolation must be linear for rotated_roi_crop}
```

## 5. Parity evidence

One parity script serves the four MediaPipe proposals (user decision T28 (H6), 2026-10-24): this proposal, `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`,
`specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md` and `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md` (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:24-26`). Each proposal names it in its part 5 and keeps its
gates. This proposal adds gates for the two crops and the inverse.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Set on 2026-10-24, before the run of the parity script. (1) Preprocessed input. Compare the crop of the reference file with the upstream input tensor of each hand model (256² refiner, 224² landmark). The exporter guide expects 0 and asks for the cause of a difference ("Parity" step 4, `specs/exporter-guide/sidecars/workflow/parity.md:28-32`). Gate: at most 1 grey level (`1/255` in [0, 1]) for each value, the tolerance of the pixel cases of part 4 (user decision Q7 = c). Record the share of the values that differ. The known cause of a 1-level difference is the arithmetic precision of the geometry, which this section does not state: MediaPipe computes it in float32 (part 1). It is not the warp function: with the same matrix, `warpAffine` and `warpPerspective` give the same pixels (0 different values for the 224² crop, at most 0.06 % for the 256² crop; scratch measurement of 2026-10-24, secondary, `q7-precision\out\tables.md` in the session scratchpad, not committed). Float32 against float64 geometry gives at most 1 grey level in at most 0.21 % of the values (same source). (2) The crop ROI of each hand. Compare the reference file with the probe geometry of MediaPipe-Exporter 0006 on the same raw ROI. Gate: `<= 1e-3` px for `cx`, `cy`, `w`, `h` and `<= 1e-6` rad for the rotation modulo 2π (the tolerances of part 4). Measured (same source): 0 for the loose crop ROI of every hand of both sets. (3) Final outputs (user decision 2026-10-24: a median and a p95 with a margin, and a count of outliers; no maximum). The error of a hand (image) or of a hand-frame (video) is the largest distance in source-image pixels over its 21 landmarks against `HolisticLandmarker` (the metric `xy_err_px` of MediaPipe-Exporter 0006), for the hands that both give. An outlier is a hand or a hand-frame whose error is above 10 % of the size of its hand-landmark ROI. Image set: median `<= 0.37` px, p95 `<= 1.92` px, 0 outliers, 0 presence disagreements of 116. Video set: median `<= 0.21` px, p95 `<= 1.79` px, at most 2 outliers, at most 5 presence disagreements of 438. Source of the numbers (the same scratch measurement; paths: A this proposal in float64, B float32, C a float32 transcription of the MediaPipe path, E the 0006 probe crop): image median 0.335 / 0.316 / 0.319 / 0.327 px, p95 1.722 / 1.734 / 1.709 / 1.738 px, largest error 4.1 % of the ROI or less in each path, 0 presence disagreements; video median 0.185 / 0.177 / 0.173 / 0.181 px, p95 1.486 / 1.620 / 1.326 / 1.514 px, presence disagreements 4 / 2 / 4 / 4. The median and p95 gates are 1.1 times the largest of the four values, rounded up to 0.01 px. The video maximum is not a gate. Path A has one outlier: frame 35, right hand, 16.99 px (19.0 % of the ROI). There A keeps the ROI from the previous landmarks and E takes the re-crop ROI (the keep decision differs in 1 of 438 hand-frames between A and E). C has the same outlier (17.01 px), and 0006 saw the same 17.0 px outlier with `--crop perspective` (`notes/decisions/0006-holistic-end-to-end-parity.md:61-66`). A 1-level change of a crop can change such a threshold decision. Every other hand-frame of A has at most 5.05 px. The allowed counts are the measured count plus 1 (outliers: 1 + 1; presence disagreements: 4 + 1). Thus the old gate "not above the numbers of 0006, the maximum included" is replaced: the path of this proposal fails it (image median 0.335 against 0.327, image maximum 4.91 against 4.83, video maximum 16.99 against 5.05; the 0006 values from `model_cache/probes/holistic_parity.json`). (4) Export error. `hand_landmark_full.onnx` against LiteRT must be `<= 2.6e-4` px (MediaPipe-Exporter 0003, cited in `0006-holistic-end-to-end-parity.md:66-67`). (5) The loose ROI from the body pose: the refiner proposal adds this gate (its part 5, gate (3)). |
| Test images (paths or dataset IDs), and the branch that each image runs | The sets of MediaPipe-Exporter 0006 (`notes/decisions/0006-holistic-end-to-end-parity.md:31-35`). Image set: the 60 largest single-person COCO val2017 images with a visible wrist (IMAGE mode, a new landmarker for each image). Video set: the first 300 frames of `sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4` (VIDEO mode). Branches that run: the rotation in all directions (left and right hands in many poses). `replicate` at the image border (ROIs near the border; the loose ROI is 2.7 times the hand). `maintain_aspect_ratio: true` (refiner) and `false` (landmark). A transform that is not the identity (the refiner input, excerpt 2). No transform (the landmark input, excerpt 1). Not run on a real image: `border_mode: constant`, a non-square ROI, and an aspect step that changes the ROI (every hand ROI is square). The check of step 2 also does not run (MediaPipe-Exporter 0006 saw no ROI without area). The vectors cover these branches. |
| Upstream reference: library, version, config and command | `mediapipe` 1.1.1, `HolisticLandmarker` with `holistic_landmarker.task` `float16/1` (MediaPipe-Exporter 0016). The upstream does not output the input tensors or the ROIs. Gate (1) needs a build of MediaPipe that writes the tensor of `ImageToTensorCalculator` (`docs/mediapipe-whole-body.md:94-106`). It does not exist. Until it exists, gate (1) is `to run`. A transcription of the upstream crop (`crop_perspective` of the probe) is a control only, not the reference (`specs/exporter-guide/sidecars/workflow/parity.md:51-54`). |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (MediaPipe-Exporter 0003 gives 2.6e-4 px from an uncommitted probe) |
| Preprocessed input: maximum absolute difference for each image | to run |
| Row count for each image: sidecar path and upstream | to run (one crop or no crop for each hand; compared with the presence of the upstream hand) |
| Final outputs in source-image coordinates: metric and value for each role | to run. `pose_estimator`: the per-hand maximum landmark error in px and in % of the ROI size against `HolisticLandmarker` (gate 3), after the inverse of this section. |
| Result (`pass`, `fail` or `to run`) | to run (MediaPipe-Exporter has no git repo, so a script cannot be committed) |
| Script path in the exporter repo | `notes/decisions/scripts/hand_chain_parity.py` (to write; user decision T28 (H6): one script for the four MediaPipe proposals, also named in part 5 of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, `specs/model-sidecar/proposals/landmark-extra-outputs/proposal.md` and `specs/model-sidecar/proposals/landmark-depth-divisor/proposal.md`). It copies `holistic_parity.py` (MediaPipe-Exporter 0006). It replaces the crops `crop` and `crop_perspective` and the projection `project_landmarks` with `rotated_roi_crop` and `unproject_points` of this reference file, for both hand models. It makes the raw loose rect with `roi_from_keypoints` of the refiner reference file (the `roi_source` of the refiner sidecar, user decision T24) from the pose landmarks of `HolisticLandmarker` (the input of the probe of MediaPipe-Exporter 0006), and gives it to the refiner crop with the transform of excerpt 2. It writes `model_cache/probes/hand_chain_parity.json`. |
| Exporter commit of the script | none (no git repo) |
| Command | `uv run --script notes/decisions/scripts/hand_chain_parity.py --n-images 60 --n-frames 300` (to run) |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | New module `skellytracker/core/detectors/processing/rotated_roi_crop.py` with the functions of the reference file: `roi_is_valid`, `validate_crop_policy`, `transform_roi`, `fit_roi_aspect`, `crop_roi`, `crop_matrix`, `rotated_roi_crop` and `unproject_points`. A new data primitive for the ROI, for example `RotatedRoi(cx, cy, w, h, rotation)` in `skellytracker/core/data_primitives/`, because `BoundingBox` has no rotation (`skellytracker/core/data_primitives/bounding_box.py:10`). |
| Dispatch point | (1) `preprocess_image` (`skellytracker/core/detectors/processing/image_preprocessing.py:158-244`). Add a branch `elif resize.method == "rotated_roi_crop"` next to the `affine_person_crop` branch (`:217-233`). The branch needs a new argument, the ROI of the item (the analog of `bbox_xyxy`, `:163`). It raises when the ROI is missing. `resize_meta` is the crop ROI `Rc`, for the inverse. (2) The keypoint decoders apply `unproject_points` with `Rc`, in place of the translation by the box corner. (3) The stage. `DetectionStage.run` crops an axis-aligned `BoundingBox` with `crop_bbox.to_crop(image)`. It translates the keypoints by `crop_bbox.x1`, `crop_bbox.y1` (`skellytracker/core/tracker/detection_stage.py:141-147, 215-235`). `DetectionStageConfig` has an optional `object_detector`, `keypoint_detectors` and `children` (`skellytracker/core/config/detection_stage_config.py:18-26`). (4) The current ROI source. skellytracker already has a keypoint-derived ROI source for a child stage: the object detector `KeypointBoundingBoxDetector` (`skellytracker/core/detectors/object_detectors/keypoint_bbox/keypoint_bbox_detector.py:1-11, 74`). Its `detect` takes the `parent_keypoints` of `ObjectDetector.detect` (`detector_base_classes.py:32-38`; `keypoint_bbox_detector.py:90-105`). `DetectionStage.run` calls it with the parent keypoints (`detection_stage.py:122`). It returns an axis-aligned square `BoundingBox` with no rotation (`BoundingBox.from_center_size(cx, cy, size, size)`, `keypoint_bbox_detector.py:105`). The MediaPipe demo uses it for the hand child stage (`skellytracker/core/detectors/keypoint_detectors/mediapipe/run_demo.py:96`). For a rotated ROI, this source needs a change. It must give a `RotatedRoi`, not a `BoundingBox`, and the stage must pass that ROI to the crop of the keypoint detector. Two forms are possible: a rotated output of the same detector, or a separate ROI-source slot. With the removal of `pose.requires_object_detector` (user decision T22 (1)), the sidecar of a top-down model no longer says "object detector": `input.resize.method` says what the model needs (`affine_person_crop` a box, `rotated_roi_crop` an ROI). Thus the stage can take the ROI of a `rotated_roi_crop` model from any ROI source (for the implementer: the slot form). (5) For the implementer: other ROI sources are an ROI refiner and an earlier frame. The refiner proposal proposes a `roi_refiner` slot. The refiner sidecar declares the rule that makes its own loose ROI from the parent keypoints (refiner proposal, `roi_source`; user decision T24). This section has no such rule (0020 `:18-19`). |
| Validator changes (`model.py`, with rule IDs) | `ResizeSpec.method` (`skellytracker/core/sidecar/model.py:79`): add `"rotated_roi_crop"` (`V-common.input-3`). `ResizeSpec.crop_policy` (`:87`) and `CropPolicySpec` (`:67-75`): a second policy model for the new method (for example `RoiCropPolicySpec` with `transform`, `maintain_aspect_ratio`, `border_mode`, `pad_value`, all without defaults where part 2.2 says so). `CropPolicySpec` has the defaults `expand_ratio: 1.25` and `maintain_aspect_ratio: true`, so one model for both methods fills wrong defaults. Select the model by `method` (`V-pre.resize.rotated_roi_crop-2` to `-4`). `ResizeSpec.interpolation` (`:86`): allow only `linear` with the new method (`V-pre.resize.rotated_roi_crop-5`). `_check_method_specific_fields` (`:94-95`): allow `crop_policy` with both methods (`V-common.input-4`). `SizedInputSpec._check_shape` (`:156`): add the method to `needs_target` (`V-common.sizes_and_artifacts-4`). The removal of `pose.requires_object_detector` (user decision T22 (1)): `PoseSpec.requires_object_detector` (`:283`) becomes optional, and a `SidecarModel` validator rejects it at `schema_version >= vNEXT` and requires it below (`V-post.pose.schema-1`, `-2`; the legacy row of part 2.6). `PoseSpec._check_pose` (`:303-309`) keeps its consistency check for a legacy sidecar only. `_check_pose_requires_affine_crop` (`:514-521`) keeps its legacy check, and at `vNEXT` it checks `pose.estimator_type` against `input.resize.method` (changed `V-pre.resize.affine_person_crop-2`). `V-pre.resize.rotated_roi_crop-1` goes in the same `SidecarModel` validator, because it needs `role`, `pose` and `input.resize.method`. Gate every new rule on `schema_version >= vNEXT`. |
| Tests | The vectors `specs/model-sidecar/vectors/pre.resize.rotated_roi_crop.yaml` against `rotated_roi_crop.py`. The runner compares each field with the `atol` of its `compare` (user decision Q7 = c). Validation tests in `skellytracker/tests/sidecar/test_model_validation.py` for each new and changed rule. The three tests of `requires_object_detector` (`skellytracker/tests/sidecar/test_model_validation.py:155-172`, and the fixture field at `:77`) become legacy tests at `schema_version < vNEXT`, and new tests check that a `vNEXT` sidecar with the field fails and that a top-down `vNEXT` sidecar with `letterbox` fails. Preprocessing tests in `skellytracker/tests/test_image_preprocessing.py` for the new branch. A golden parity test: one hand image, one ROI, the 224² crop tensor and the landmarks of the ONNX model after the inverse, as the tests in `skellytracker/tests/sidecar/` do for the detectors. |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py`: `ResizeSpec`, `CropPolicySpec`, `SizedInputSpec`, `PoseSpec` (with `requires_object_detector`, `:283`), the `SidecarModel` validators (with `_check_pose_requires_affine_crop`, `:514-521`). The package sidecars that declare `requires_object_detector: true` (`skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose-body.yaml:39`, `rtmpose/face/rtmpose-face.yaml:39`, `rtmpose/hand/rtmpose-hand.yaml:39`, `rtmw/wholebody/rtmw-wholebody.yaml:39`): no change, they are legacy (`v2024.09.1019`). No other package code reads the field (a search of `skellytracker/` at `dom/14-decision-log-growth`). `skellytracker/core/detectors/processing/image_preprocessing.py`: `preprocess_image`. `skellytracker/core/detectors/processing/affine_crop.py`: no change. Its `get_warp_matrix` (`:33`), `bbox_xyxy2cs` (`:68`) and `top_down_affine` (`:88`) stay for `affine_person_crop`. `skellytracker/core/tracker/detection_stage.py`: `DetectionStage.run`, `_detect_and_translate`. `skellytracker/core/config/detection_stage_config.py`: `DetectionStageConfig`. `skellytracker/core/detectors/object_detectors/keypoint_bbox/keypoint_bbox_detector.py`: `KeypointBoundingBoxDetector` (axis-aligned square boxes; the current keypoint-derived ROI source). `skellytracker/core/detectors/detector_base_classes.py`: `ObjectDetector.detect` returns `list[BoundingBox]`. `skellytracker/core/data_primitives/bounding_box.py`: no rotation. `tools/sidecar_normalize.py`: the selector `input.resize.method=rotated_roi_crop` matches with no code change. |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` and `rtmo-coco17-body7` (the two pose writers; `rtmdet-person` has no `pose` block) | Regenerate (user decision T22 (1)): the writers must stop writing `pose.requires_object_detector`. Writers: `rtmw/sidecar.py:158` (`True`) and `rtmo/sidecar.py:158` (`False`), commit `d0f4343`. Also at `d0f4343`: the test `tests/test_rtmw.py:373`, the probe `notes/decisions/scripts/rtmo_sidecar_probe.py:135` (its check `no_upstream_detector` reads the field), and the text `Readme.md:459` and `rtmw/README.md:40`. The decision entry OpenMMLab-Exporter 0020 (`notes/decisions/0020-rtmo-sidecar-contract.md:17`; the user decision T26 (1) of the OpenMMLab-Exporter plan changes its NMS part, and the new entry for that change is pending) and the frozen sidecar copies `notes/decisions/rtmo-body7.yaml:55` and `rtmo-coco17-body7.yaml:55` record the past state; the decision-log rules of that repo apply to them. (A read-only `git grep` at `d0f4343`; this session changed nothing there.) By OpenMMLab-Exporter 0050 (accepted 2026-10-24), no family writes a sidecar while its intake is not `describes`; the writers keep the field at `f3aeb47` (`rtmw/sidecar.py:160`, `rtmo/sidecar.py:158`). The writers drop the field when a later decision sets `sidecar` True again (OpenMMLab-Exporter 0050, item 8). | none |
| Roboflow-Exporter | none (no tracked file names the field; `git grep` at `c64fd2a`) | none | none |
| Ultralytics-Exporter | the YOLO26-pose sidecar (`yolo26-body` in the spec example; `yolo26-coco17` by user decision T23, M1) | Regenerate (user decision T22 (1)): `yolo_sidecar.py:518` writes `"requires_object_detector": False`, and `tests/test_yolo_sidecar.py:332` asserts it (`git grep` at `2e0280e`). | none |
| Qualcomm-Exporter | The historical MediaPipe hand and face landmark sidecars (`affine_person_crop` with `expand_ratio: 1.0`, 0020 `:59-62`) and the planned hand sidecars (untracked plan, 0020 `:56-58`) | Out of the `vNEXT` scope (skellytracker 0008 `:15`). No tracked file at `4ca4586` names `requires_object_detector` (`git grep`). The historical code wrote `true` (`specs/model-sidecar/post/pose-schema.md:141`). If it writes the sidecars again, it writes `rotated_roi_crop` with no `requires_object_detector`, and the ROI constants that its pipeline manifests hold move into `crop_policy.transform` where they apply to one ROI source. | none (no host decoder today) |
| MediaPipe-Exporter (proposing) | The hand landmark sidecar (`full`, `lite`) and the hand ROI refinement sidecar | New fields: excerpt 1 for the hand landmark model, excerpt 2 for the refiner input (Q2). The plan values change: the landmark crop has `keep_aspect_ratio: true` in the plan manifest (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)), but the graph sets no `keep_aspect_ratio` (part 1, other source (a)); with a square ROI on a square input the two give the same crop. The pipeline manifest keeps only the steps outside the sidecars: the raw loose rect from pose, the tracking ROI and its choice, and the gates (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)). Its `recrop.crop` and `landmark.crop` (`:330, :343`) and the `transform` of `roi_from_pose` (`:327`, Q2) move into the sidecars. | The host crop and inverse are `rotated_roi_crop` and `unproject_points` of the reference file. The probe `hand_roi_reference.py` gives the same results for square ROIs (part 4). The depth `z` stays with skellytracker 0022. |
| skellytracker package sidecars | none | none. They have `schema_version: "v2024.09.1019"`, and their legacy meaning does not change. The four that declare `requires_object_detector: true` keep it (legacy row, part 2.6). | none |
| skellytracker spec examples | `rtmo-body7.yaml`, `rtmw-wholebody.yaml`, `yolo26-body.yaml` (`vNEXT`) | Replaced from the regenerated exporter sidecars (part 2.1). | none |

**What the refiner proposal had to change** (`specs/model-sidecar/proposals/roi-refiner-role/proposal.md`). It applied
items 1 to 16 (its "Before you stop", `:3401-3403`; lines of 2026-10-24 after T26 (6) and T27). The line numbers below are of its earlier draft:

1. **Header, "Depends on" (1)** (`:20`): name this file and the section
   `pre.resize.rotated_roi_crop`. The method name is `rotated_roi_crop`. Say that this proposal lands
   first (user decision, 2026-10-23).
2. **Open question Q4** (`:910-912`): decided by the user on 2026-10-23: keep the two proposals
   separate. This is its option (a) without the words "with dependencies both ways". The user
   decision makes the dependency one-way: the refiner proposal depends on this proposal, and this
   proposal does not depend on the refiner proposal (this Header, "Depends on"). Move Q4 to
   "Decided" with that text. Its part 8 row "One proposal with 0020" (`:883`) gets the user
   decision as its reason.
3. **Behaviour, the ROI definition** (`:216-218`): cite the heading "ROI" of
   `pre.resize.rotated_roi_crop` in place of "(The 0020 proposal owns this definition.)". That
   definition does not limit the range of the rotation. Keep "in [-pi, pi)" as a statement of the
   refiner output only (its step 3 normalizes the rotation).
4. **Step 2** (`:229-234`): the inverse is `unproject_points` with the crop ROI `Rc` of the input
   crop (after `crop_policy.transform` and `maintain_aspect_ratio`), not with `R_in[b]`. With
   excerpt 2, `R_in[b]` is the raw loose rect, so the difference is large. Its vectors `decode-hand-*`
   (`:787-837`) stay correct when `input_roi` reads as the crop ROI and the sidecar has no
   `crop_policy.transform`. State that, or add `crop_policy` to `decode_roi`.
5. **Step 4 and `roi_decode.transform`** (`:184, :245-250`): the transform is the "ROI transform" of
   `pre.resize.rotated_roi_crop`: the same four fields, defaults and order. Its rule
   `V-post.roi_refiner-7` (`:303-305`) can cite `V-pre.resize.rotated_roi_crop-4`. The field name
   `transform` matches `crop_policy.transform`.
6. **Step 5 and Q5** (`:252-254, :913-914`): it can use `roi_is_valid` of this section (it adds the
   test for finite values). New upstream evidence for Q5 option (a): `ValidateRoi` rejects NaN,
   `width <= 0` and `height <= 0` at the crop (`image_to_tensor_utils.cc:92-102`, part 1, other
   source (b)).
7. **`V-post.roi_refiner-8`** (`:306-307`): "`input.resize.method` must be `rotated_roi_crop`". Add
   to its changed rules: `V-pre.resize.rotated_roi_crop-1` also allows `role: [roi_refiner]` (with
   no `pose` block). Its rule `V-common.input-3` row (`:327`) and `V-common.input-4` row (`:328`)
   change: this proposal adds the method and `crop_policy.border_mode`. Its row for
   `V-post.pose.schema-2` and `V-pre.resize.affine_person_crop-2` (`:331`) changes: this proposal
   changes `V-post.pose.schema-2` for the consumer.
8. **Part 2.2, the YAML excerpt** (`:190-206`): add the `input` block of excerpt 2 of this file (or
   the identity form, if the user chooses Q2 option b).
9. **Part 2.1 and 2.7** (`:154-155, :167-168, :362-371`): this proposal adds its row of the summary
   of changes first (row N, the next free number at merge time). The refiner row comes after it. The scope entry of this proposal (it supersedes the scope entry in force in full and holds only scope rules, T34 (N2) and T35) and the edit of the
   note "For reviewers" come with this proposal. The refiner proposal adds only its model to them.
10. **Part 3 and the reference file** (`:379-391`; the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`): delete the PROVISIONAL functions `crop_points_to_source` and `transform_roi`.
    Import `transform_roi`, `unproject_points` and `roi_is_valid` (and `crop_roi` for step 2) from
    `pre_resize_rotated_roi_crop`. Its 10 vectors with `provisional: skellytracker 0020` (`:532-578,
    :682-751`) then move to this section: the same cases are here (part 4) or pass through this file
    (10 of 10). The note "The 0020 proposal must define the letterbox case" (`:388-391`) is done:
    `maintain_aspect_ratio` enlarges the ROI, and the inverse uses the enlarged ROI.
11. **Part 6** (`:860-861`): the crop inverse and the transform come from the module
    `rotated_roi_crop.py` of this part 6.
12. **Header, "Needed by"** (`:21`): remove the item "The full proposal of skellytracker 0020: its
    consumer ROI can come from a refiner". This proposal does not need the refiner (user decision
    (3); this Header, "Depends on": none). The other items of that row (`model-id-suffix` and
    the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts)) stay.
13. **Header, the row of `proposed` entries** (`:22`): the sentence "This proposal is a separate role
    proposal that 0020 depends on." becomes "This proposal is a separate role proposal. It depends
    on the full proposal of 0020 (`specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`), which lands
    first (user decision, 2026-10-23)."
14. **Part 2.2, the input of a refiner** (`:186-188`): "The crop method is the rotated ROI crop of the
    0020 proposal (`input.resize.method`; its name is not set yet)" becomes "The crop method is
    `input.resize.method: rotated_roi_crop`
    (Rotated ROI crop (`../pre/resize-rotated-roi-crop.md`)). Its inverse is the heading
    Inverse (`../pre/resize-rotated-roi-crop.md#inverse`)."
15. **Part 8, the row "Extend 0020 only"** (`:882`): the last sentence "0020 itself names 'the ROI
    refiner gap' as a dependency" stays as a fact of the gap record. Add: "By user decision
    (2026-10-23), the full proposal of 0020 lands first and does not depend on the refiner."
16. **Part 5** (`:844, :852`): the parity script (now `notes/decisions/scripts/hand_chain_parity.py`, T28 (H6)) is
    shared with this proposal (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:24-26`). Its row "Script path"
    (`:852`) must cite this proposal. Its gates (`:844`) must add, or cite, the crop gates (1)
    (preprocessed input) and (2) (crop ROI) of part 5 of this proposal. The script uses
    `rotated_roi_crop` and `unproject_points` of this reference file for both hand crops.

**Input for skellytracker 0022 (depth divisor).** 0022 must say how the host unprojects a `pixel`
depth (`0022-landmark-depth-divisor.md:15-16`). For `rotated_roi_crop`, the factor from input pixels
to source pixels along `x` is `wc / T_w` (MediaPipe multiplies `z` by the rect width,
`docs/mediapipe-whole-body.md:147-149`; the hand uses `z / 224 / 0.4 · roi_size`, `:405-406`).

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **The near-miss: `affine_person_crop` with `expand_ratio`** (the historical Qualcomm-Exporter approximation, `expand_ratio: 1.0`) | No rotation, no shift, no `square_long`, a constant border only, and an input that must be a detector box. On the Holistic loose hand ROI, `expand_ratio: 2.7` without rotation and shift maps the input corners up to 41.3 px away (38.2 % of the ROI size); `expand_ratio: 1.0` gives up to 56.8 px. | Part 1; `resize-affine-person-crop.md:29-51`; 0020 `:59-62, 68-69` |
| **Extend `affine_person_crop`** with a rotation, the transform fields and a border mode (a changed section; the direction "`crop_policy` gets the fields" of 0020 `:16-17`) | `affine_person_crop` is `stable`, and its input is a detector box with the mmpose centre and scale (`resize-affine-person-crop.md:18, 29, 53`). Its `crop_policy` has defaults (`expand_ratio: 1.25`, `maintain_aspect_ratio: true`) that are wrong for MediaPipe (`keep_aspect_ratio` off by default, `docs/mediapipe-whole-body.md:101`). With this extension, its selector covers two ROI sources, and `V-pre.resize.affine_person_crop-2` needs an exception. A new method keeps the legacy meaning and the existing vectors unchanged. This proposal keeps the 0020 direction in form: the fields are under `crop_policy`, nested in `crop_policy.transform`, so the refiner can use the same object (`roi_decode.transform`). (User decision T23, Q1.) | `specs/model-sidecar/pre/resize-affine-person-crop.md:1-18, 31-35`; `skellytracker/core/sidecar/model.py:67-69` |
| **Keep the ROI rule and the transform in a pipeline manifest** (both exporter plans) | The host then needs a second contract to make the input, and the spec cannot check it (0020 `:41-42, 66-67`). This proposal keeps only the rule that makes the raw ROI outside (0020 `:18-19`). | the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (secondary) |
| **Put the rule that makes the ROI from keypoints into this section** (for example the wrist, pinky and index rule in `crop_policy`) | This section serves every ROI source of a `rotated_roi_crop` model: a refiner, an earlier frame or a host rule. The hand landmark model gets its ROI from two sources (heading "ROI source"). A keypoint rule in this section fits only one of them. By user decision T24 (2026-10-24), the rule that makes the loose hand ROI from the body pose is in the refiner sidecar (`roi_source` of `post.roi_refiner`), the consumer of that ROI. Thus the sidecar set is enough to run the model, and this section stays general. The first form of this row ("keep the rule outside every sidecar", 0020 `:18-19`) is rejected by T24. | `docs/mediapipe-whole-body.md:381-389`; refiner proposal part 8 |
| **Keep `pose.requires_object_detector`**, with the value `false` for `rotated_roi_crop` (the first form of this proposal, Q3 option a), any value with no meaning (Q3 b), or a new field `pose.roi_source` (Q3 c) | Rejected by user decision T22 (1) (2026-10-24): the field leaves the spec. No sidecar is deployed, and all sidecars will be made again. `input.resize.method` already gives the input that a model needs, so the field repeats it. With option (a), skellytracker would model a keypoint-derived ROI source as "not an object detector" for one rule, but as an object detector in the stage (`KeypointBoundingBoxDetector`, part 6). | `specs/model-sidecar/post/pose-schema.md:37, 117-118`; `specs/model-sidecar/pre/resize-affine-person-crop.md:66` |
| **(a) State float64 for steps 1 to 4** (the first form of this proposal) | Rejected by user decision Q7 = (c) (2026-10-24). MediaPipe computes in float32, so float64 does not reproduce it. Float32 against float64 differs by at most 1.2e-4 px and 1.2e-7 rad in the geometry, and by at most 1 grey level in at most 0.21 % of the crop values. A float32 transcription of the MediaPipe path differs from both precisions by the same amount. A precision rule would make a float32 host fail a rule with no effect on the outputs (landmarks after the inverse: median about 0.005 px). | scratch measurement of 2026-10-24 (secondary), `q7-precision\out\tables.md` in the session scratchpad (not committed) |
| **(b) State float32, as MediaPipe** | Rejected by user decision Q7 = (c). A float32 host of this text is still not the MediaPipe path (other order of operations, `warpPerspective`, the `NORM_RECT` projection): path B against the transcription C differs about as much as A against C. The float32 path also had the largest video errors in the measurement (24.45 px maximum, from threshold decisions). | the same source |
| **One transform on the consumer for every source** (the hand landmark sidecar declares scale 1.0 or 2.0) | The hand landmark model gets its ROI from the refiner (scale 1.0) and from the previous landmarks (scale 2.0). One `crop_policy.transform` cannot hold both. Thus each source applies its own transform, and the consumer has none (heading "ROI source"). | `docs/mediapipe-whole-body.md:390-403` |
| **Flat fields in `crop_policy`** (`crop_policy.shift_x` and so on, as 0020 `:16-17` writes them) | A nested `transform` object is one type with one rule (`V-pre.resize.rotated_roi_crop-4`). The refiner uses the same object in `roi_decode.transform`. Flat fields need two copies of the rule. (User decision T23, Q1 part 2.) | `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` |
| **Defaults for `border_mode` and `maintain_aspect_ratio`** (the MediaPipe defaults `replicate` and `false`) | The defaults differ between the two crop methods (`affine_person_crop` has `maintain_aspect_ratio: true`), and between MediaPipe graphs (the detector graphs set `BORDER_ZERO` and `keep_aspect_ratio`). A required field removes a wrong default (the lesson of `fit` `pad_value`, skellytracker 0012). (User decision T23, Q4.) | `docs/mediapipe-whole-body.md:99-101`; MediaPipe source at `e9794ef` (cached copy, other source (a)): `tasks/cc/vision/pose_detector/pose_detector_graph.cc:253-255`, `tasks/cc/vision/hand_detector/hand_detector_graph.cc:238-240` and `tasks/cc/vision/face_detector/face_detector_graph.cc:360-362` (`keep_aspect_ratio` true, `BORDER_ZERO`); `hand_roi_refinement_graph.cc:89-91` (`keep_aspect_ratio` true, `BORDER_REPLICATE`); `hand_landmarks_detector_graph.cc:254-264` (neither set) |
| **`scale_x` and `scale_y`**, and the `RectTransformationCalculator` options `square_short` and rotation | No graph in scope uses them: each transform in `docs/mediapipe-whole-body.md` has one scale and `square_long` or nothing (`:289-293, 347-349, 354-356, 387-399, 432-433, 456-466`). A later revision can add them. (User decision T22 (2), Q5.) | `rect_transformation_calculator.cc:206-245` (other source (a)) |
| **The MediaPipe `NORM_RECT`-only projection as the inverse** | It is not the inverse of the crop for a non-square rotated ROI, and MediaPipe itself supports it only for a square ROI. For every ROI in scope (square) the two agree. The exact inverse is one formula for every ROI. (User decision T23, Q6.) | `landmark_projection_calculator.cc:78-96`; vector `unproject-non-square-rotated` |
| **`warpPerspective` with the four box corners, as MediaPipe does** | For a rectangle the map is affine. `warpAffine` keeps the form of `affine_person_crop` and `fit`. On real hands, the probe `warpAffine` crop and a transcription of the upstream crop (a control, not upstream) differ by at most 1 grey level. | `notes/decisions/0006-holistic-end-to-end-parity.md:61-66` |
| **All four `interpolation` values for `rotated_roi_crop`** | `cv2.warpAffine` has no area resampling. With `cv2.INTER_AREA` it gives the `linear` result, so `area` cannot keep its meaning (`pre/interpolation.md:40`). MediaPipe uses only `INTER_LINEAR`. No model in scope needs `cubic` or `nearest`, and skellytracker 0008 adds only what a model needs (`0008-vnext-scope.md:17`). (User decision T23, Q11.) | `docs/mediapipe-whole-body.md:96-97`; scratch run of this session (part 2.1) |
| **Allow `rotated_roi_crop` for an `object_detector`** (the Holistic face detector runs in a rotated loose face ROI, `docs/mediapipe-whole-body.md:446-461`) | The boxes of a rotated crop are rotated boxes in the source image. The spec has no rotated box. The face detector also needs keypoints on detections and weighted NMS, which are other gaps. (User decision T23, Q8.) | `docs/mediapipe-whole-body.md:106-109, 120-134` |

Where this proposal differs from 0020, and why:

- 0020 changes `V-post.pose.schema-2` **and** `V-pre.resize.affine_person_crop-2` (`:13-16`). This
  proposal changes both, and `V-post.pose.schema-1`, because it removes the field
  `pose.requires_object_detector` (user decision T22 (1), 2026-10-24). The changed
  `V-pre.resize.affine_person_crop-2` names `pose.estimator_type` and `input.resize.method`.
- 0020 says "The rule that computes the ROI from the keypoints stays outside the sidecar"
  (`:18-19`). This section keeps that rule out of `rotated_roi_crop`. But by user decision T24
  (2026-10-24), the refiner sidecar declares the rule that makes the loose hand ROI from the body
  pose (refiner proposal, `roi_source`). The reason: without it, the sidecars are not enough to run
  the hand branch. The tracking ROI and the ROI choice stay outside the sidecars (refiner proposal,
  part 8).
- 0020 puts the fields into `crop_policy` (`:16-17`). This proposal puts them into
  `crop_policy.transform` of a new method (rows "Extend `affine_person_crop`" and "Flat fields").
- 0020 does not name the border mode and the aspect step. This proposal adds them, because the hand
  crops need `BORDER_REPLICATE` and the refiner crop has `keep_aspect_ratio`
  (`docs/mediapipe-whole-body.md:390`).
- 0020 says that the change depends on the ROI refiner gap (`:21-22`). By user decision
  (2026-10-23) the order is the reverse: this proposal lands first.

## Open questions for the user

Decided by the user on 2026-10-23: keep this proposal separate from the ROI refiner role proposal;
`vNEXT`; this proposal lands before the refiner; extend the scope of skellytracker 0008 with MediaPipe-Exporter (the form is revised by T34 (N2) and T35: a small scope entry supersedes the scope entry in force in full; see Q10);
`docs/mediapipe-whole-body.md` is checked primary evidence.

Decided by the user on 2026-10-24 (T22 and T23 of the untracked pose-models plan of OpenMMLab-Exporter (plan facts), and Q7 = c). The text of
this file follows each decision.

- **Q1. Form and name of the method.** Decided (user, 2026-10-24, T23): (a) a new method
  `rotated_roi_crop`, section `pre.resize.rotated_roi_crop`, with a nested `crop_policy.transform`.
  This was the proposal choice.
- **Q2. Where the loose-ROI transform of the refiner goes.** Decided (user, 2026-10-24, T23): (a)
  in the refiner sidecar, `crop_policy.transform` (excerpt 2). For a model with two or more ROI
  sources, each source applies its own transform, and the consumer sidecar has no
  `crop_policy.transform`. This was the proposal choice.
- **Q3. `requires_object_detector` with `rotated_roi_crop`.** Decided (user, 2026-10-24, T22 (1)):
  remove the field `pose.requires_object_detector` from the spec. This differs from the earlier
  proposal choice (a) ("it must be `false`"). The premise: no sidecar is deployed, and all sidecars
  will be made again. `input.resize.method` gives the input that a model needs. Applied in part 2.1
  (heading "Removal of `pose.requires_object_detector`" and the table), part 2.4 (changed
  `V-post.pose.schema-1`, `-2`, `V-pre.resize.affine_person_crop-2`, `V-pre.resize.rotated_roi_crop-1`),
  part 2.6 (the legacy row), part 2.7, part 6 and part 7 (the writers that must stop).
- **Q4. Defaults of `border_mode` and `maintain_aspect_ratio`.** Decided (user, 2026-10-24, T23):
  required, with no default. This was the proposal choice.
- **Q5. The scale.** Decided (user, 2026-10-24, T22 (2)): one `scale`. A later proposal adds
  `scale_x` and `scale_y` only if a model needs them. This was the proposal choice.
- **Q6. The inverse.** Decided (user, 2026-10-24, T23): the exact inverse of the crop. This was the
  proposal choice.
- **Q7. The arithmetic.** Decided (user, 2026-10-24): (c) no precision in the text, with a tolerance
  in the vectors. This differs from the earlier proposal choice (a) (float64). Applied: the sentence
  "The host computes steps 1 to 4 in float64" is removed from part 2.3; the vectors of part 4 have
  the tolerances `1e-3` px, `1e-6` rad and 1 grey level; part 1, part 5 (gates (1) to (3)) and part
  8 (rows (a) float64 and (b) float32) give the measurement.
- **Q8. An object detector with this method.** Decided (user, 2026-10-24, T23): `pose_estimator`
  only at `vNEXT`. This was the proposal choice. (The refiner proposal adds `roi_refiner`.)
- **Q9. ROI validity and its result.** Decided (user, 2026-10-24, T23): an ROI with a NaN or an
  infinite value gives "no ROI" (no crop), as an ROI with `w <= 0` or `h <= 0` does (user decision
  of 2026-10-23, refiner Q5 = a). This was the proposal choice (a).
- **Q10. The entry that changes the `vNEXT` scope of skellytracker 0008.** Decided (user, 2026-10-24, T23): (a)
  the entry of this proposal makes the change and cites 0008. This was the proposal choice.
  **Revised by user decision T34 (N2), 2026-10-24:** the skellytracker log has no "extends" relation. The entry of this proposal supersedes in full the entry that holds the `vNEXT` scope at merge time (0008, or the entry of `nms-clamp-order` if that lands first), and it restates the rules of that entry with its own change (MediaPipe-Exporter in the scope; `crop_policy.border_mode` and rotated crops out of the "not added" groups of 0008). The status line of 0008 becomes `superseded by NNNN`. The first text ("the status line of 0008 does not change") is superseded. **Revised again by user decision T35, 2026-10-24:** the scope change goes into a small scope entry `RRRR` that holds only scope rules (heading "Scope entry (user decision T35)"). It supersedes in full the scope entry in force at merge time (0008, or entry B of `nms-clamp-order` if that lands first), and it restates the scope rules of that entry with the change of this proposal (MediaPipe-Exporter in the scope; `crop_policy.border_mode` and rotated crops out of the "not added" Resize group). The main entry of this proposal (0020) holds the rules of `rotated_roi_crop`. It does not supersede 0008 or any scope entry. Thus the feature rules of `nms-clamp-order` and of this proposal never couple.
- **Q11. `interpolation` for `rotated_roi_crop`.** Decided (user, 2026-10-24, T23): `linear` only
  (`V-pre.resize.rotated_roi_crop-5`). This was the proposal choice.
- **Q12. A closed key set for an `affine_person_crop` `crop_policy`.** Decided (user, 2026-10-24,
  T23): (a) add it to `V-common.input-4`, marked **(vNEXT)**. This was the proposal choice.

Still open: none. (The refiner proposal has its own questions.)

## Scope entry (user decision T35)

User decision T35 (2026-10-24) puts the scope change of this proposal into a small skellytracker
entry that holds only scope rules. The rules of `rotated_roi_crop` stay in the main entry of this
proposal: 0020, the gap record that this proposal completes. The main entry does not supersede 0008
or any scope entry. A skellytracker session writes the scope entry when it records this proposal.
This proposal only describes it. No skellytracker file changes in this work.

| Item | Value |
|---|---|
| Entry file | `notes/decisions/RRRR-vnext-scope-mediapipe-rotated-crops.md`. `RRRR` is the number that `uv run python tools/check_decision_log.py --next` gives when the entry lands (skellytracker 0032; `notes/decisions/README.md:109-114`). At skellytracker `dom/21-move-sidecar-guide` the highest number in the index is 0034; the checker run of 2026-10-24 (below) used `dom/18-agents-adr-bootstrap-kit`, where it was 0031. |
| Title | The heading line of the text below. The Decision cell of its index row has the same words (100 characters; limit 160, `tools/check_decision_log.py:64`). |
| Supersedes (in full) | The scope entry in force at merge time: 0008, or entry B (`SSSS-vnext-scope-nms-filters.md`) of the OpenMMLab-Exporter proposal `nms-clamp-order` if that entry lands first. |
| Status | `proposed`, with an Active index row in the same PR. At acceptance: `accepted`. In the same PR, the scope entry that it supersedes becomes `superseded by RRRR`, and its row moves to "Historical". |
| Size (after CRLF to LF) | 4,468 characters (74% of 6,000; limit `ENTRY_LIMIT`, `tools/check_decision_log.py:60`). The variant below has 4,622 characters with the real file names. |
| Checker | The session of 2026-10-24 ran `tools/check_decision_log.py` on a scratch copy of the skellytracker log at `dom/18-agents-adr-bootstrap-kit` (the OpenMMLab-Exporter proposal `nms-clamp-order`, "Effect on skellytracker decisions 0011 and 0008", "Checker run"). Both merge orders pass: this entry as 0032 before the two `nms-clamp-order` entries (read path 216,855 of 220,000), and its variant as 0034 after them (read path 216,627). The numbers 0032 and 0034 in that run are placeholders of the scratch copy at `dom/18-agents-adr-bootstrap-kit`; at `dom/21-move-sidecar-guide` they are taken (skellytracker 0032 to 0034), and the entry takes the number of `--next` when it lands. The read-path figures move by the size of the entries that landed since; the skellytracker session runs the checker again. |

**Text, when this entry supersedes 0008** (it restates 0008 at skellytracker `dom/21-move-sidecar-guide` almost word for
word; 0008 did not change between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide`):

```markdown
# RRRR — `vNEXT` scope and the features not added; MediaPipe-Exporter joins, and rotated crops leave the list

**Status:** proposed, 2026-10-24 (MediaPipe-Exporter proposal `roi-transform-and-source`).

## Decision

This entry supersedes [0008](0008-vnext-scope.md) in full. It restates each rule of 0008 that stays.
It holds only scope rules. [0020](0020-roi-transform-and-source.md) holds the rules of
`rotated_roi_crop`.

The `vNEXT` revision of [the sidecar spec](../../specs/model-sidecar/sidecar-spec.md) must let a sidecar describe
every model that these exporters produce:

- OpenMMLab-Exporter: RTMDet (person-only family), RTMW and RTMO body7.
- Ultralytics-Exporter: YOLO26 detection and YOLO26 pose.
- Roboflow-Exporter: RF-DETR.
- MediaPipe-Exporter: the hand landmark model and the hand ROI refinement model. Changed: 0008
  does not list this exporter.

Qualcomm-Exporter is out of scope until that library is complete.

`vNEXT` adds only the features that these models need. The spec lists the other features in
[Considered and deliberately not added](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added).
This entry groups them:

- Resize: `resize.antialias` and `resize.size_divisor`.
- NMS: `nms.pre_nms_top_k` (see [0011](0011-rtmdet-host-nms.md)) and `nms.min_bbox_size`.
- Scores and classes: `score_activation: softmax`, `class_id_map_before_selection`, and
  `class_logits` with `selection: nms`.
- Graph and pose descriptions: `graph_candidate_limit` and `pose.decode.instance_count`.
- Soft-NMS, per-class IoU, masks, multi-input models and quantized outputs.

Changed: `crop_policy.border_mode` and rotated crops leave the Resize group of 0008. `vNEXT` adds
them in `rotated_roi_crop` ([0020](0020-roi-transform-and-source.md)).

A later revision can add each listed feature as a non-breaking schema bump when a model needs it.

The spec has no RF-DETR reference example. The example returns when Roboflow-Exporter is
overhauled and writes `vNEXT` sidecars. The rules that RF-DETR motivated stay in the spec. These
rules include:

- the `stretch` resize;
- the `boxes`, `scores` and `class_logits` output semantics, with `class_axis`;
- `selection: top_k`, with `class_id_map`.

`vNEXT` is a placeholder name for this revision. [0014](0014-spec-lifecycle.md) holds the rule for
when a release version replaces it.

## Reason

- No model in scope needs most of the listed features. Each row of the
  [spec table](../../specs/model-sidecar/changelog.md#considered-and-deliberately-not-added) gives its own reason.
- Some rows give another reason:
  - For `score_activation: softmax`, the behaviour over gap and background slots is unresolved.
  - For `nms.pre_nms_top_k`, a flat candidate list cannot express the per-level `nms_pre` cap of mmdet.
  - `graph_candidate_limit` is informational only. The host cannot act on it.
  - `pose.decode.instance_count` is not needed. The count comes from the detection row axis.
- Changed: `vNEXT` must also describe the MediaPipe Holistic hand branch (user). Its crop is a
  rotated ROI with a replicated border. No resize method of the spec describes it.
- The RF-DETR example had drifted from the output of Roboflow-Exporter, and that exporter will be
  overhauled. An example that does not match a real export misleads exporter authors. The rules stay
  because RF-DETR still needs them.

## Evidence

The spec records one measurement behind the `class_logits` with `selection: nms` row. The test model
is the NMS-free RTMDet-tiny. Each (row, class) pair above the score threshold becomes a candidate.
Per-class NMS follows. This method reproduced the PyTorch AP (0.4114 against 0.4112). A method that
keeps only the best class for each row lost 0.0051 AP and 0.031 AR.

No family in scope needs this feature, because the COCO-80 RTMDet family was dropped. A later
revision can add the feature if a multi-class NMS-free family appears.

## Alternatives rejected

- Adopt the whole Roboflow-Exporter draft that
  [the exporter coverage plan](../sidecar-exporter-coverage.md) starts from.
  The draft has fields that no exported model uses. The coverage plan trims them.

## Not repeated

- Do not read the list of features as a ban. A feature leaves the list when a model needs it.
- Do not remove an RF-DETR rule because the spec has no RF-DETR example.
- Do not put a feature rule into a scope entry. A later scope change supersedes only the scope entry
  in force, and it restates only scope rules.
```

**Variant: entry B of `nms-clamp-order` lands first.** `SSSS` is the number of entry B, and `NNNN` is
the number of the NMS entry A of that proposal (`NNNN-rtmdet-host-nms-filters.md`). The text changes
in four places:

1. The supersedes sentence: "This entry supersedes SSSS (`SSSS-vnext-scope-nms-filters.md`) in full.
   It restates each rule of SSSS that stays." (0008 is then `superseded by SSSS`.) In the MediaPipe
   bullet of the scope list, "Changed: 0008 does not list this exporter." becomes "Changed: SSSS does
   not list this exporter."
2. The bullet "NMS: `nms.pre_nms_top_k` (see 0011 (`0011-rtmdet-host-nms.md`)) and
   `nms.min_bbox_size`." is removed.
3. Before "Changed: `crop_policy.border_mode` ...", a new paragraph: "`nms.pre_nms_top_k` and
   `nms.min_bbox_size` are not in the list. `vNEXT` adds both fields for `rtmdet-person`
   (NNNN (`NNNN-rtmdet-host-nms-filters.md`))." In the paragraph "Changed: ...", "the Resize group of
   0008" becomes "the Resize group of SSSS".
4. In "Reason", the sub-bullet "For `nms.pre_nms_top_k`, ..." is removed. Before the bullet "Changed:
   `vNEXT` must also describe ...", a new bullet: "The spec must fully describe the models in scope
   (user). The mmdet decode of `rtmdet-person` has a per-level cap and a box-size filter.
   `nms.level_strides` expresses the levels."

In each merge order, the last scope entry has the same scope rules. The proposal `nms-clamp-order`
gives entry B and its variant for the other order ("Effect on skellytracker decisions 0011 and 0008",
"Variant of entry B").

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. Done on 2026-10-24:
      the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts) and the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts)
      link it in their tables "Proposals and reference files".
- [x] The header gives the dependencies, or `none` (none; the refiner proposal depends on this one).
- [x] The header names each `proposed` skellytracker decision entry that covers the same property
      (0020; also 0019, 0021, 0022 and 0025 for the other gaps of the same models). This proposal
      builds on 0020. It does not compete with it.
- [x] Part 1 cites primary evidence (`docs/mediapipe-whole-body.md`, by user designation; the other
      sources are named), and it names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits, with the places of the removal of
      `pose.requires_object_detector` (T22 (1)): `V-post.pose.schema-1` and `-2`,
      `V-pre.resize.affine_person_crop-2`, intake row K1, the pose-schema authoring notes and
      example, the examples in `common/outputs.md`, `format/composition.md` and
      `specs/model-sidecar/examples/`, the exporter guide and the change-proposal template, the
      canonical-mapping guidance, the legacy row with its link in `format/versioning.md`, and the
      changelog.
- [x] Part 3 names the reference file, and the file exists in the untracked plans of MediaPipe-Exporter (plan facts).
- [x] Part 4 gives `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare` (1 grey level, Q7 = c).
- [x] The user decisions T22, T23 and Q7 = c (2026-10-24) are applied in the header, parts 1 to 8
      and "Open questions for the user". No question stays open. T24 (the loose ROI from the body
      pose) is applied in the refiner proposal; this file states the boundary (parts 1, 2.2, 2.3
      and 8).
- [x] The vectors were run again on 2026-10-24 after the change: 78 of 78 pass (78 of 78 before).
      Mutation check: a copy of this file with one changed expected value (`cy` of
      `transform-shift-y-rotation-0`, 94.0 to 94.01) gave 77 of 78 (exit 1), and only that case
      failed. The file itself is unchanged by the check.
- [x] Part 5 says `to run` and describes the script. The gates are set before the run (2026-10-24):
      the crop within 1 grey level, the crop ROI within `1e-3` px and `1e-6` rad, the landmark
      median and p95 with a margin and a count of outliers, the export error, and the loose-ROI gate
      of the refiner proposal. One script serves the four MediaPipe proposals (T28 (H6)).
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed. n/a: the result is
      `to run`.
- [x] User decision T35 (2026-10-24) is applied. The scope change is in a small scope entry (heading
      "Scope entry (user decision T35)": the file name, the title, the text, the variant, the size
      and the checker result). The Header merge-point note, part 2.1 and Q10 say so. The main entry
      (0020) does not supersede 0008 or any scope entry. The vectors did not change: 78 of 78 pass
      after the change. The lines up to Q10 keep their numbers, so the citations of the refiner
      proposal stay correct.
- [x] No file in skellytracker changed.
- [x] Re-pinned on 2026-10-25 to skellytracker `dom/21-move-sidecar-guide` (audit of the proposals). The citations of
      `notes/decisions/README.md`, `notes/decisions/open-work.md` and `tools/check_decision_log.py`
      have their `dom/21-move-sidecar-guide` numbers. No cited spec line moved. The reference file,
      the part 3 code of `specs/model-sidecar/proposals/roi-transform-and-source/proposal.md`, runs unchanged (exit 0) on 2026-10-25.
      The vectors did not change.

This proposal has `to run` in part 5. A skellytracker session can record it: it completes the gap
record 0020 and adds the scope entry. It is not ready for the user to accept.

## Before acceptance

The user cannot accept this proposal until this work is done.

**Parts**

- [ ] Part 5 is `to run`. MediaPipe-Exporter must write the parity script
  `notes/decisions/scripts/hand_chain_parity.py`, run it on the image set and the video set of
  MediaPipe-Exporter 0006, and record the result against gates (1) to (5). The one script serves
  the four MediaPipe-Exporter proposals.
- [ ] MediaPipe-Exporter has no git repo. Thus the parity script, the reference file and the
  exporter decisions have no commit. A commit must exist before the user can accept the proposal.
- [ ] Part 2.1 does not list all the places that the change edits. The field row of `crop_policy` in
  `specs/model-sidecar/pre/resize-affine-person-crop.md` says "This field applies to
  `affine_person_crop` only." That sentence becomes false. The comment on `implemented_by.validate`
  in the front matter of the same file names `V-pre.resize.affine_person_crop-2`. That rule changes.
  The exporter must add both places.
- [ ] Part 2.1 names the open-work spec defect of the half-pixel centres. It does not name the
  open-work spec defect of the scalar `pad_value`, which the new section solves only for
  `rotated_roi_crop`. The exporter must name it.
- [ ] The non-spec PR can also update this guidance, which part 2.1 does not list: the pixel centres
  and the scalar `pad_value` in `specs/exporter-guide/sidecars/workflow/mapping-hints.md`, the pad
  hint of `specs/model-sidecar/templates/model-intake.md`, and the "See also" line of
  `specs/model-sidecar/common/input.md`. These texts name only `fit` and `affine_person_crop`. They stay
  true.
- [ ] Part 6 lists 8 module functions. It does not list `project_points`, which part 3 gives as the
  ninth function. The exporter must make the two lists agree.
- [ ] The docstring of the part 3 code calls Q11 a "proposal choice". Q11 is a user decision (T23).
  The exporter must correct the reference file before it goes to `specs/model-sidecar/reference/`.
- [ ] Part 2.1 (the row of "Summary of changes") and the header row "Needed by" say that 13 open
  proposals add a changelog row. There are now 14. OpenMMLab-Exporter also has the proposal
  `omitted-upstream-output`.
- [ ] The header row "Needed by" and part 7 give two different lines for the "Before you stop" of the
  refiner proposal. Only the line of the header row agrees with the exporter file of the refiner
  proposal on 2026-10-25. The exporter must correct part 7.

**Evidence**

- [ ] The measured numbers come from scratch scripts that are not committed: the 41.3 px corner
  distance of part 1, the float32 against float64 measurement of Q7, the `warpAffine` against
  `warpPerspective` comparison, and the numbers behind the gates of part 5. They are not evidence.
  The committed parity script must give them again.
- [ ] Missing primary evidence: no upstream input tensor of either hand crop exists, and no upstream
  ROI output exists. `HolisticLandmarker` gives only the landmarks. Gate (1) needs a MediaPipe build
  that writes the tensor of `ImageToTensorCalculator`.
- [ ] No real-image run covers `border_mode: constant`, a non-square ROI, an aspect step that changes
  the ROI, or the "no crop" result of step 2. Only the vectors cover them.
- [ ] The main evidence is the MediaPipe-Exporter document `docs/mediapipe-whole-body.md`. It is
  primary only by a user decision in MediaPipe-Exporter. The exporter guide classes the notes of an
  exporter as secondary.
- [ ] The MediaPipe source file `image_to_tensor_utils.cc` comes from a scratch download, not from
  the cached copy. Part 1 gives its sha256.
- [ ] The upstream MediaPipe citations must become GitHub permalinks at
  `e9794ef55e2509c09aa8b6ba1764b797db8eb200`. Make sure that this commit is on the default branch of
  the MediaPipe repo.
- [ ] The cross-checks of part 4 use the probe of MediaPipe-Exporter 0006. The probe has no commit,
  and it is in the same exporter. Thus the vectors stay `unverified`.

**Template checklist**

- [ ] "How to use this template", item 1, asks for one contract unit in each proposal. This proposal
  has three units: the new section, the removal of `pose.requires_object_detector` (T22 (1)), and
  the closed key set of an `affine_person_crop` `crop_policy` (T23, Q12). Its "Before you stop"
  does not test this item.
- [ ] "Part 2.1 lists each place that the change edits" is ticked. The places that **Parts** names
  are missing.
- [ ] "Part 1 cites primary evidence" is ticked. It is true only through the user designation of
  `docs/mediapipe-whole-body.md`.
- [ ] "Each pixel case in part 4 has its tolerance in `compare`" is ticked. The case form does not
  pass the current `tools/tests/test_vectors.py` (see **Vectors and tooling**).
- [ ] Part 5 is `to run`. The proposal itself says that it is not ready for the user to accept.

**Vectors and tooling**

- [ ] The case form of part 4 does not agree with `tools/tests/test_vectors.py`. The keys `function`
  and `compare` are not in `CASE_KEYS`. The tests expect one scalar `tolerance` for each case and
  exact integers, but the pixel cases have `atol: 1`. `generated_by` must be
  `tools/make_vectors.py`. A vector file must be smaller than 16 KiB, and the YAML block of part 4
  has about 33.8 KB. The template `change-proposal.md` documents `function` and `compare`, so the
  template and the tests do not agree. The form must be decided one time for all proposals.
- [ ] The skill `change-sidecar-spec` requires that `tools/make_vectors.py` writes the vectors. Part
  2.1 gives the builder only as an option ("or adds a builder"). A generated file loses the YAML
  comments of part 4: the matrix of each `project_points` case and the `NORM_RECT` value of
  `unproject-non-square-rotated`. That comment cites `landmark_projection_calculator.cc:78-81`. Part
  2.3 cites `:78-96`, and part 1 cites `:78-102`.
- [ ] The tests must handle the NaN and infinity cases (`.nan`, `.inf`).
- [ ] `tools/make_vectors.py` and the tests must import
  `specs/model-sidecar/reference/pre_resize_rotated_roi_crop.py`. That folder does not exist yet. The
  refiner reference code loads this file as a sibling, so its function names are a shared API.
- [ ] `tools/tests/test_traceability.py` needs the new section in `EXPECTED_APPLICABILITY` and in the
  resize set of `test_every_sidecar_matches_a_resize_section`. `UNPROJECTION_SECTIONS` of
  `tools/tests/test_vectors.py` is optional.
- [ ] The checker results in the heading "Scope entry (user decision T35)" come from an older copy of
  the decision log. Run `uv run python tools/check_decision_log.py` again with 0048 in the index.
- [ ] The front matter of the new section has `status: {spec: draft, ...}`. Decision 0013 does not
  define `draft`, and each current section is `stable`. The value for a new section must be decided.

**Decisions for the user**

- [ ] Accept or reject `docs/mediapipe-whole-body.md` of MediaPipe-Exporter as primary evidence.
  Decide how a tracked file cites the documents, decisions and scripts of MediaPipe-Exporter. It has
  no git repo and no permalinks.
- [ ] Confirm the user decisions that this proposal applies. T22, T23, T24, T25 (Q7 = c), T28, T34
  and T35 are only in the untracked pose-models plan of OpenMMLab-Exporter (plan facts). The
  decisions of 2026-10-23 and the refiner answer Q5 = a are only in the MediaPipe-Exporter
  proposals.
- [ ] Keep the three contract units in this proposal, or split the removal of
  `pose.requires_object_detector` and the closed `crop_policy` key set into separate proposals.
- [ ] Confirm that the scope entry 0048 is a separate decision beside the completed gap record 0020.
  The decision-log rules say: "Do not add a second entry for the same gap."
- [ ] Choose the order of the two scope entries: 0048 and entry B (0042) of `nms-clamp-order`. Both
  supersede 0008 in full. Choose the text to record: the base text of 0048 (it supersedes 0008) or
  the variant in this file (it supersedes 0042).
- [ ] The proposal says that 0048 restates 0008 "almost word for word". 0048 puts the NMS group
  before the group "Scores and classes", and it changes "each feature" to "each listed feature".
  Accept these changes, or ask the exporter to restate 0008 exactly where a rule stays.
- [ ] 0048 adds the hand landmark model and the hand ROI refinement model to the `vNEXT` scope. The
  refinement model also needs `roi-refiner-role`. The hand landmark model also needs 0021, 0022 and
  0025. Decide if the scope names only what this proposal makes describable. The BlazePose model,
  which `keypoint-visibility` needs, stays out of the scope.
- [ ] Rule ownership (decision 0013): part 2.6 puts the legacy text of
  `V-pre.resize.affine_person_crop-2` under a new "Legacy behaviour" heading of `post.pose.schema`,
  not in the section that owns the rule. The skill `change-sidecar-spec` says that each legacy
  difference goes in the "Legacy behaviour" heading of its section. The changed
  `V-pre.resize.affine_person_crop-2` also repeats `V-pre.resize.rotated_roi_crop-1`. The new text of
  `V-post.pose.schema-1` has no **(vNEXT)** mark. Accept this, or ask the exporter to revise it.
- [ ] Decide one rule for the "Version-aware compatibility" links. This proposal adds a link for the
  new heading of `post.pose.schema`, but no link for the new section (the precedent of
  `pre.resize.fit`). Other proposals do this in a different way.
- [ ] After the change, the reference examples `rtmo-body7.yaml`, `rtmw-wholebody.yaml` and
  `yolo26-body.yaml` fail the changed `V-post.pose.schema-2`. Part 7 needs regenerated exporter
  sidecars. OpenMMLab-Exporter 0050 stops the RTMW and RTMO writers, and T29 removes RTMO from this
  round. Decide if the content PR can land with examples that are known to be invalid.
- [ ] Gap record 0020 says: "The rule that computes the ROI from the keypoints stays outside the
  sidecar." By T24, `roi-refiner-role` puts that rule in the refiner sidecar. Confirm that the
  completed record can change this direction.
- [ ] The new section states the pixel centres and the scalar `pad_value` fill only for
  `rotated_roi_crop`. Confirm that the two open-work spec defects stay open for the other methods.
- [ ] The removal of `pose.requires_object_detector` makes the example of a joining rule in decision
  0013 historical. Decide if this needs an open-work note.
- [ ] Part 5 names the video file of the public skellysamples test recording (release
  `test_data_v06_09_25`). The file name has initials. Confirm that a tracked file can name it.

**Merge points**

- [ ] `affine-crop-arithmetic` (0037). Either proposal can land first. Both edit "Behaviour" of
  `pre.resize.affine_person_crop` (the sentence "Rotated crops are out of scope."), its validation
  rules, its "Authoring guidance", its front matter, row T4b of the intake template and
  `V-common.input-4`. The second content PR keeps the sentence of this proposal and adds
  `arithmetic` to the closed key set. That proposal adds a "Legacy behaviour" heading to the owning
  section. This proposal puts its legacy text in `post.pose.schema`.
- [ ] `nms-clamp-order` (0041 and 0042). The two scope entries, the rows of "Considered and
  deliberately not added", the "Implementer guidance" of `post.unprojection`, and the rows D11 and
  D12 of the intake template.
- [ ] `normalize-arithmetic` (0043). "Behaviour" of `pre.normalize`.
- [ ] `size-codes` (0046). `specs/model-sidecar/common/sizes-and-artifacts.md`: the field
  `sizes.<name>.input` and `V-common.sizes_and_artifacts-4`. The "Related" note of the header row
  "Needed by" does not list this merge point.
- [ ] `omitted-upstream-output` (0044). Phase 1 of the exporter guide, next to the edit of the `gap`
  examples, and the verdict rows of the intake template. The "Related" note of the header row
  "Needed by" does not list this proposal.
- [ ] `roi-refiner-role` (0047), `landmark-extra-outputs` (0021), `landmark-depth-divisor` (0022),
  `pose-decode-flip-test` (0045), `heatmap-decode-refinement` (0038) and `keypoint-visibility`
  (0039). The legacy row "Not available." of `format.versioning`, the validation rules of
  `post.pose.schema`, and "Behaviour" of `post.unprojection`.
- [ ] `model-id-suffix` (0025) and `size-codes` (0046). The reference examples, `inventory.yaml` and
  the RTMW excerpt of `format.composition`.
- [ ] All proposals add a row to "Summary of changes" and text to the `vNEXT` row of the changelog.
- [ ] `keypoint-visibility` (0039), `pose-decode-flip-test` (0045), `landmark-extra-outputs` (0021),
  `size-codes` (0046) and `roi-refiner-role` (0047). The section map and the index of the validation
  rules in `specs/model-sidecar/README.md`. `tools/tests/test_traceability.py` checks their order. The
  header row "Needed by" does not list this merge point.
- [ ] `simcc-score-rule` (0024), `heatmap-decode-refinement` (0038), `normalize-arithmetic` (0043),
  `affine-crop-arithmetic` (0037), `model-id-suffix` (0025), `landmark-extra-outputs` (0021) and
  `landmark-depth-divisor` (0022). "Compatibility impact" of the changelog. `landmark-extra-outputs`
  also adds a row to "Considered and deliberately not added".
- [ ] The non-spec PR that edits the `proposed` rows of `inventory.yaml` must also repair the path of
  the MediaPipe-Exporter hand pipeline plan. MediaPipe-Exporter moved that plan to an archive
  folder. Other spec files cite the same old path.
- [ ] Landing order: this proposal and 0048 land before `roi-refiner-role`,
  `landmark-extra-outputs` and `landmark-depth-divisor`.
