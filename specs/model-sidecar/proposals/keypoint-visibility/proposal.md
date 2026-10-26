---
slug: keypoint-visibility
section: post.pose.visibility
exporter: OpenMMLab-Exporter
decision: "0039"
state: recorded
---

# Change proposal: keypoint-visibility

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `keypoint-visibility`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. Part 3 also holds the code of the OpenMMLab-Exporter reference file of part 3, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`. It is the proposal of plan T26 (2) (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), user
decision of 2026-10-24): one per-point visibility value in the pose decode. The first scope was
RTMW `decode_visibility=True` (intake row K8a) and the BlazePose parent of the score gate of the
ROI refiner. With option E (below), the scope is the BlazePose parent only.

**User decisions.** T33 (2026-10-24, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) makes `score_gate.value` of
the refiner a runtime input with a sidecar default (part 2.8). Its V1 = A1 (the visibility only in
the two RTMW 384x288 size entries, with a size-level exception to skellytracker 0010) was the
interim state until the COCO-WholeBody measurement (T34, question Qe and rule S7 of the
wrist-gate study, recorded in OpenMMLab-Exporter decision 0041: one rule for the whole family). **Option E** (2026-10-24,
OpenMMLab-Exporter decision `notes/decisions/0041-rtmw-wrist-gate.md`, evidence, commit `9deff61`)
replaces A1: no RTMW size declares `pose.decode.visibility`, and BlazePose is the only consumer of
this proposal. An RTMW parent of the refiner uses `score_gate.value: score` at every size.

**Rewritten for E on 2026-10-24.** The section has one source, `keypoints_channel`. The rewrite
removes the `simcc_softmax` source (with `beta` and `sigma`), the heading "Sizes", the size-level
rule, the change to `V-common.sizes_and_artifacts-3` and the decision entry that superseded
skellytracker 0010 (skellytracker 0010 stays as it is). The rules are `V-post.pose.visibility-1` to `-4`. All 31
vectors of part 4 pass against the reference file. (History note, 2026-10-25: the rewrite for E had
30 vectors. A review of 2026-10-25 added the case `validate-error-mapping-without-source`.)

## Header

| Field | Value |
|---|---|
| Title | A visibility value for each keypoint in the pose decode (`pose.decode.visibility`) |
| Slug | `keypoint-visibility` |
| Date | 2026-10-24; updated 2026-10-25 (re-pinned to skellytracker `dom/21-move-sidecar-guide`; part 1 verifies the two MediaPipe calculators from GitHub; part 5 in the 11 template rows; the line numbers of part 2.8, the plan row and the checklist checked again) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed: OpenMMLab-Exporter decision 0050). The commits before it: `32ab848` (the merge of OpenMMLab-Exporter decision 0041, commit `9deff61`) and `1dfec48` (OpenMMLab-Exporter decision 0042). `git status --porcelain` is empty. First written at `d0f4343812cc582b4b0020e5b532c83572d11fd2`. Checked again at `f3aeb47` on 2026-10-24: `rtmw/sidecar.py:156-165` (`pose_block`, `"decode": {"method": "simcc"}` at `:164`; the same at `32ab848`), `rtmw/adapter.py:137` (`:136` at `32ab848`: OpenMMLab-Exporter decision 0050 adds one docstring line), and lines 51 and 55 of the two 384x288 configs and line 50 of the 256x192 config `rtmw-m_8xb1024-270e_cocktail14-256x192.py` under `mmdeploy-convert/model_cfgs/`. OpenMMLab-Exporter decision 0050 sets `capabilities["sidecar"]` of RTMW to False (`rtmw/adapter.py:41`): the pipeline writes no RTMW sidecar until the RTMW intake is `describes`. The writer stays. |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | Main model (option E): the BlazePose pose landmark model of MediaPipe (lite, full and heavy), the parent pose model of the score gate of the MediaPipe hand ROI refiner (`specs/model-sidecar/proposals/roi-refiner-role/proposal.md`, read only). BlazePose has no intake yet. `rtmw-wholebody133` (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)) raised the gap (row K8a). With option E it declares no visibility at any size (OpenMMLab-Exporter decision 0041). |
| Intake rows with the verdict `near-miss` or `gap` | Row R2 (the per-point value of the parent, `gap`) of the untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts) (line 189; it links this proposal at line 312; added by the review-readiness audit 2, 2026-10-24). Row K8a (keypoint visibility of the 384x288 sizes) of the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (line 193): `gap` until this rewrite. User decision T36 (2026-10-24, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) gives row K8a the verdict `out of scope (0041)`; the exporter guide lets the user decide such a row. The phase 2 proposal `specs/model-sidecar/proposals/omitted-upstream-output/proposal.md` (slug `omitted-upstream-output`) covers it: it asks skellytracker for a guide rule for an upstream output that the exporter deliberately leaves out, with the evidence that no consumer uses it. This file does not edit the intake. Rows K8a (the visibility, channel 3, `gap`) and K5 (the five-channel layout `[B, 39, 5]`, `near-miss`) of the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked BlazePose plan of MediaPipe-Exporter (plan facts), the BlazePose pose landmark model) link this proposal. That intake keeps row K8b (the per-point presence, channel 4) as a gap with no proposal (Q2). BlazePose is deferred (user, 2026-10-24, OpenMMLab-Exporter plan T41). This proposal stays in the current round. The BlazePose notes of this file stay as records. |
| Kind (`new section` or `changed section`) | `new section` (with edits to `post.pose.schema`, `post.pose.decode.simcc` (authoring guidance only), `post.pose.decode.coordinate`, `format.versioning`, `specs/model-sidecar/README.md`, the changelog, the exporter guide and the intake template, part 2.1) |
| Proposed section ID (the `id` in the section file's front matter) | `post.pose.visibility` |
| Section file | `specs/model-sidecar/post/pose-visibility.md` (proposed) |
| Depends on (proposal files that must land first, or `none`) | none. **Related (no order):** `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` and `specs/model-sidecar/proposals/simcc-score-rule/proposal.md` share spec text with this proposal (the merge points below). With option E they have no behaviour relation: the visibility has no SimCC source, and the flip test has no `coordinate` form (the flip-test proposal, its follow-up). Each of the three can land first. |
| Needed by (proposal files that depend on this one, or `none`) | MediaPipe-Exporter `specs/model-sidecar/proposals/roi-refiner-role/proposal.md` (section `post.roi_refiner`, proposed). Its `roi_source.score_gate` reads the visibility of the BlazePose wrist. Its text says that no BlazePose parent can pass its parent check until a proposal adds a per-point score (part 1, the bullet "The per-point score of the parent", now "The per-point value of the parent", `:119-129`). This proposal is that proposal. Part 2.8 lists the edits that the refiner proposal needed (all applied by the refiner session, 2026-10-24). This file does not edit it. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit` (checked again on 2026-10-24; the cited lines are the same as at `dom/12-single-working-branch`). `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test`, `heatmap-decode-refinement`, `roi-transform-and-source` (MediaPipe-Exporter), `roi-refiner-role` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `post/pose-schema.md:89-95` (the `pose.decode` fields table, with the row `pose.decode.is_3d` at `:92`, and "Method-specific fields"): `pose-decode-flip-test`, `heatmap-decode-refinement`, `landmark-depth-divisor` (MediaPipe-Exporter); `post/pose-schema.md:103-111` ("Shape key"): `heatmap-decode-refinement` (`:108`), `simcc-score-rule` (`:109-110`); `post/pose-visibility.md` heading "Per-point values" (the heatmap score): `heatmap-decode-refinement`; `post/pose-schema.md:117-127` ("Validation rules": `-1` and `-2` owned by `roi-transform-and-source`, `-7`, `-9`, the "See also" line): `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter), `pose-decode-flip-test`; `post/pose-decode-simcc.md:38` (the "Behaviour" bullet): no longer a merge point of this proposal (option E: no edit there); `post/pose-decode-simcc.md` "Authoring guidance" (the `decode_visibility` bullet at `:58`): `simcc-score-rule`; `post/pose-decode-coordinate.md:33` (the single-person form): `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `post/pose-decode-coordinate.md:55-56` ("Authoring guidance"): `landmark-depth-divisor` (MediaPipe-Exporter); `specs/model-sidecar/README.md` (the section-map row and the validation-index link after "Coordinate decode", `:93`, `:121`): `pose-decode-flip-test`, `landmark-extra-outputs` (MediaPipe-Exporter); `exporter-guide/sidecars/workflow/mapping-hints.md:55-65` ("Mapping hints", Outputs and decode, Pose): `landmark-extra-outputs` (MediaPipe-Exporter), `nms-clamp-order`, `omitted-upstream-output` (place G8); `templates/model-intake.md:318` (row K8 and the new row K8a after it): `landmark-extra-outputs` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). With option E, this proposal edits no place of `common/sizes-and-artifacts.md`, the **Family** hint and the "Sidecar YAML" text of `exporter-guide/sidecars/workflow/mapping-hints.md` and `exporter-guide/sidecars/sidecar-files.md`, rows F3 and F4 of `templates/model-intake.md`, `changelog.md:29` and `:58`, or `specs/model-sidecar/README.md:19`. The merge points of user decision T33 at those places are thus not merge points of this proposal. |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index (`notes/decisions/README.md:23-68` at `dom/18-agents-adr-bootstrap-kit`) has no entry for a per-point visibility. Two `proposed` gap records are near: skellytracker **0021** (pose outputs beside the landmarks) covers an instance presence score, a class probability and world keypoints, one value for each crop, not one for each keypoint (`0021-landmark-extra-outputs.md:11-26`). skellytracker **0024** (SimCC score rule) covers the keypoint score, not a second value (`0024-simcc-score-rule.md:11-17`). This proposal does not compete with them. Part 8 tells why it is a separate unit. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `dom/18-agents-adr-bootstrap-kit` (checked again for the rewrite for E on 2026-10-24). `git status --porcelain -- specs/model-sidecar` is empty. Other files have uncommitted changes of another session (`AGENTS.md`, `notes/decisions/0028-entry-edits-and-citations.md`, `notes/decisions/README.md`, `open-work.md`, a new `0032-entry-numbers-and-edits.md`, files under `tools/` and `specs/agents-and-adr-process/`). This file cites none of them in the working-tree form: its decision citations are at `dom/18-agents-adr-bootstrap-kit`. First read at `dom/16-private-data`. `git diff --stat dom/16-private-data dom/18-agents-adr-bootstrap-kit -- specs notes` lists only `notes/decisions/0031-bootstrap-kit.md`, `notes/decisions/README.md` and new files under `specs/agents-and-adr-process/`. Thus the spec lines that this file cites are the same at both commits. Guide citations point to the skellytracker 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). **Re-pinned on 2026-10-25 to `dom/21-move-sidecar-guide`** (branch `dom/sidecar-implementation`): `git status --porcelain` lists no tracked file (only an untracked `grep.exe.stackdump`, not a file of the spec); the uncommitted files named above are committed as skellytracker 0032 to 0034. `git diff --stat dom/18-agents-adr-bootstrap-kit dom/21-move-sidecar-guide -- specs/model-sidecar` lists only link-text edits (`common/identity.md`, `common/sizes-and-artifacts.md`, `format/file-layout.md`, `post/selection-nms.md`, `post/selection-top-k.md`, both templates, `TRACEABILITY.md`, `inventory.yaml`) and the removal of `specs/model-sidecar/exporter-guide.md` (skellytracker 0034). Each spec, guide, decision and code line that this file cites was read again at `dom/21-move-sidecar-guide` on 2026-10-25 and is the same. |

**Upstream copies.** The session that wrote this paragraph had no network. The mmpose v1.3.2 lines below are lines of the
copies that an earlier session downloaded into
the folder `upstream\` of the local temporary scratch folder of session `f8d98dba` (not in a repo)
("copy B" of the RTMW intake, the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)):
`mmpose-v1.3.2/mmpose/codecs/simcc_label.py`, `mmpose-v1.3.2/mmpose/codecs/utils/post_processing.py`,
`mmpose-v1.3.2/mmpose/models/pose_estimators/topdown.py`,
`mmpose-v1.3.2-rtmwhead/mmpose/models/heads/coord_cls_heads/rtmw_head.py`,
`mmpose-v1.3.2-simcc-extra/mmpose/models/heads/base_head.py` and
`mmpose-v1.3.2-simcc-extra/mmpose/evaluation/metrics/coco_metric.py`. I did not download them, and I
cannot check their origin again. The MediaPipe lines are lines of the cached source tree
`MediaPipe-Exporter/model_cache/sources/e9794ef55e2509c09aa8b6ba1764b797db8eb200/`
(MediaPipe commit `e9794ef`, read only). MediaPipe-Exporter has no git repo. The session of
2026-10-25 had network access: it downloaded the two calculator sources and the proto of the
"Verified items" bullet of part 1 from GitHub at `e9794ef` and counted their lines.

**Scratch files of this proposal** (not committed, so not evidence):
`...\scratchpad\visibility\`
with `read_io.py` (the graph read), `ophist.py` (the operator counts), `measure_rtmw_visibility.py`
and its log `measure_300.log` (part 1), `fp16_grid.py` (part 1), `gen_vectors.py` and
`run_vectors.py` (part 4). The visibility investigation of every RTMW size (plan row "V-check")
is in `...\scratchpad\visibility-sizes\` (`REPORT.txt`, `measure.py`, `analyse.py` with its log
`analyse.log`, `make_fp16_variants.py`, `fix_block.py`, `sigma_formula.py`). The edits of T33 are
in `...\scratchpad\v1-gate\`. `...` is the local temporary folder of session `3bd420c5` (not in a
repo). The runner of part 4 for option E (`run_vectors.py`) and its YAML copy (`vectors.yaml`) are in
`scratchpad\fu-visibility\` of the local temporary folder of session `1ffa39f8` (not in a repo).

## 1. Gap

| Item | Value |
|---|---|
| Property | **BlazePose.** The pose landmark model gives five values for each of its 39 points: `x, y, z`, a visibility logit and a presence logit. MediaPipe applies a sigmoid to the visibility on the host. The Holistic hand branch gates on the wrist visibility (`> 0.1`). The score gate of the refiner needs this value, and the spec has no field for it. **RTMW (out of scope, option E).** The test pipeline of the two 384x288 RTMW configs gives a second value for each keypoint, `keypoints_visible`: the softmax peak of the raw SimCC output at the temperature `decode_beta * sigma`. The graph does not hold it. OpenMMLab-Exporter decision 0041 measured it and drops it for all five sizes (row "Measured difference"). Thus this proposal adds no SimCC source, and row K8a closes with no field: its verdict is `out of scope (0041)` (user decision T36). `specs/model-sidecar/proposals/omitted-upstream-output/proposal.md` covers the guide rule for such a row. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **BlazePose, MediaPipe `e9794ef`:** `tasks/cc/vision/pose_landmarker/pose_landmarks_detector_graph.cc:94-95` (`kModelOutputTensorSplitNum = 5`, `kLandmarksNum = 39`), `:142-160` (`ConfigureTensorsToLandmarksCalculator` sets `visibility_activation` and `presence_activation` to `SIGMOID` when `sigmoid_activation` is true), `:411-413` (the landmark tensor: `sigmoid_activation= true`), `:449-451` (the world landmarks: `false`). `calculators/tensor/tensors_to_landmarks_calculator.cc:27` (`Sigmoid(float value) { return 1.0f / (1.0f + std::exp(-value)); }`), `:29-38` (`ApplyActivation`), `:144` (`num_dimensions = num_values / num_landmarks_`), `:153` (`offset = ld * num_dimensions`), `:172-178` (`num_dimensions > 3`: visibility from value `offset + 3`; `> 4`: presence from value `offset + 4`), `:193-198` (the normalized landmarks keep both values). `calculators/tensor/tensors_to_landmarks_calculator.proto:60-64` (both activations default to `NONE`). `tasks/cc/vision/holistic_landmarker/holistic_hand_tracking.cc:80-91` (`GetPosePalmVisibility`: the wrist, `LandmarkVisibilityCalculator`, `IsOverThreshold(score, 0.1)`); `calculators/util/thresholding_calculator.cc:123-124` (`static_cast<double>(...) > threshold_`). **The BlazePose graph** (read with `onnx`, scratch `read_io.py`): `MediaPipe-Exporter/model_cache/onnx/all/ad6cfd3c903e.onnx` and `1150dc68a713.onnx` (199 nodes, the node count of the pose landmark lite row of MediaPipe-Exporter `notes/decisions/0017-all-models-inventory.md:32`; SHA-256 `408ccde02fba0eae89d38f5753cc4dc043c2088bcb0d744a7a76f30d63f4ef64` and `60f8fec51feb819c071655951b8e5ae74e38388973c7e052a707009d16174ccf`), and the full (218 nodes) and heavy (459 nodes) files of the same folder: input `input_1` float32 `[1, 3, 256, 256]`; output `Identity` float32 `[1, 195]` (`Reshape` of `Conv` `model_1/model/convld_3d`, no `Sigmoid` after it), then `Identity_1` `[1, 1]`, `Identity_2` `[1, 256, 256, 1]`, `Identity_3` `[1, 64, 64, 39]` and `Identity_4` `[1, 117]`. `195 = 39 * 5`. Thus the visibility value in the graph is a logit, and the host applies the sigmoid. Secondary: MediaPipe-Exporter `docs/mediapipe-whole-body.md:144-145, 197, 301-307, 384-386` (the user designated this document as primary evidence for the refiner proposal; this proposal cites the code lines above). **RTMW, mmpose v1.3.2** (the record of row K8a; not the basis of a field): the exporter image has `mmpose==1.3.2` (`mmdeploy-convert/Dockerfile.exporter:34, 42-44`). The configs `mmdeploy-convert/model_cfgs/rtmw-l_8xb320-270e_cocktail14-384x288.py` and `rtmw-x_8xb320-270e_cocktail14-384x288.py` set `sigma=(6., 6.93)` (line 51) and `decode_visibility=True` (line 55); the three 256x192 configs set `sigma=(4.9, 5.66)` (line 50) and no `decode_visibility`. Codec (`mmpose/codecs/simcc_label.py`): `decode_beta: float = 150.0` (line 77); lines 193-198 compute the visibility with `get_simcc_maximum(..., apply_softmax=True)` and return `keypoints, (scores, visibility)`. `add_pred_to_datasample` (`topdown.py:157-159`) sets `keypoints_visible = keypoint_scores` when the codec gives no visibility. The COCO-WholeBody metric reads `keypoint_scores`, not `keypoints_visible` (`coco_metric.py:210-219, 450-469`). The ONNX graph gives only `simcc_x` and `simcc_y` (intake row K8a). These are lines of the local copies of the upstream files that the paragraph "Upstream copies" names. |
| Nearest section ID (the `id` in the section file's front matter) | `post.pose.decode.coordinate` (BlazePose), through `post.pose.schema` (`pose.decode`). For RTMW: `post.pose.decode.simcc`, which keeps its one score. |
| Why the nearest section is wrong | `pose.decode` has `method`, `is_3d`, `depth_unit`, `depth_range` and `coordinate_scale` (`post/pose-schema.md:87-95`). No field asks for a second value for each keypoint. The single-person coordinate decode gives `(N, K, 2)` or `(N, K, 3)` and no score at all (`post/pose-decode-coordinate.md:33`). A BlazePose tensor has 5 values for each point. No field says which value is the visibility, or that the host must apply a sigmoid to it. The exporter guide calls a host activation of a keypoint score a gap (`exporter-guide/sidecars/workflow/mapping-hints.md:64-65`). The output `semantic` set is closed and has no visibility value (`common/outputs.md:29`). |
| Measured difference (number, image and script) | **BlazePose:** no measurement in this session. The gap is a missing field, not a number: without a field, a host has no visibility for the gate of the refiner, and the parent check of `V-post.roi_refiner-15` refuses every BlazePose parent that the gate reads with `visibility`. **RTMW (the reason for option E):** OpenMMLab-Exporter decision `notes/decisions/0041-rtmw-wrist-gate.md` (evidence, commit `9deff61`; COCO-WholeBody v1.0 val, 6352 persons, 12704 hands, GT boxes, flip test off; its scripts are in `notes/decisions/scripts/`). Rule S7 (one verdict for the family) fails at every size: (1) on the hands that Holistic can track, the visibility `vis_w` ranks valid hands worse than the raw wrist score `s_w` (`AUC(vis_w) - AUC(s_w)` −0.046 to −0.094; the 95 % lower bounds −0.056 to −0.106 against the limit −0.02); (3) at 256x192 the visibility saturates on wrists that are not labelled (95 % to 96 % of the wrists with `vis_w >= 0.995` have `v = 0`); (4) four of the five sizes fail the fp16 test (gate change 3.31 % to 3.95 % at 256x192; AUC −0.051 for x-384). At 384x288 one visibility threshold opens almost every hand. The raw score `s_w` passes S1 to S3 at every size, so an RTMW parent of the refiner gates on `score`. The earlier scratch numbers of this file (300 COCO persons of x-384, and the plan row "V-check") point the same way; OpenMMLab-Exporter 0041 replaces them as evidence. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The table (`changelog.md:42-53`) has no row for a keypoint visibility. The row `score_activation: softmax` (`:46`) is about detection scores. A row for the SimCC visibility of RTMW is not proposed: row K8a and OpenMMLab-Exporter decision 0041 record it in the exporter. |

All the evidence above is primary (upstream file and line, a read of the ONNX graph, or the committed
OpenMMLab-Exporter 0041), except the lines of `docs/mediapipe-whole-body.md` (secondary here).

Missing primary evidence: none. Verified items:

- BlazePose: verified on 2026-10-25 from GitHub at MediaPipe `e9794ef` (the two calculator sources
  are not in the local cache; the line numbers are counts of the raw files that this session
  downloaded). `calculators/util/refine_landmarks_from_heatmap_calculator.cc` copies the input list
  (`mediapipe::NormalizedLandmarkList out_lms = in_lms;`, line 121) and sets only `x` and `y`
  (`set_x`, `set_y`, lines 162-163, inside the block at lines 161-164). It changes the presence
  only when `refine_presence` is true (lines 165-172, `std::min(presence, max_confidence_value)`)
  and the visibility only when `refine_visibility` is true (lines 173-182,
  `std::min(visibility, max_confidence_value)`). `refine_landmarks_from_heatmap_calculator.proto`
  defaults `refine_presence` and `refine_visibility` to `false` (lines 27-28; `kernel_size` at 25,
  `min_confidence_to_refine` at 26). The pose graph sets only `kernel_size(7)`
  (`tasks/cc/vision/pose_landmarker/pose_landmarks_detector_graph.cc:169-174`, node at `:421-431`,
  local cache). `calculators/util/landmark_visibility_calculator.cc` requires one landmark
  (`RET_CHECK_EQ(landmarks.landmark_size(), 1);`, line 75), reads
  `landmarks.landmark(0).visibility()` (line 76) and emits it unchanged on `VISIBILITY` (lines
  78-80). Thus the heatmap refinement keeps the visibility of `TensorsToLandmarksCalculator`, and
  the gate reads it unchanged.
  `LandmarkProjectionCalculator` starts each output landmark as a copy of the input landmark
  (`calculators/util/landmark_projection_calculator.cc:98, 124, 136`). The Holistic gate reads the
  smoothed pose landmarks (`docs/mediapipe-whole-body.md:380-382`, secondary). The refiner proposal
  keeps the smoothing outside the sidecar as host tracking policy.

## 2. Spec change

### 2.1 Sections

New section `post.pose.visibility`, title "Keypoint visibility", file
`specs/model-sidecar/post/pose-visibility.md`.

Front matter:

```yaml
id: post.pose.visibility
title: Keypoint visibility
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - pose.decode.visibility
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.pose.visibility.yaml
status: {spec: draft, validate: missing, decode: missing}
```

The spec state is `draft`, as in the flip-test proposal (`specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md`
part 2.1): the doc tests allow only `stable` or `draft`.

Row in the section map (`specs/model-sidecar/README.md`, after `post.pose.decode.coordinate`, line 93; if the
flip-test row is there, after that row):

```text
| `post.pose.visibility` | [post/pose-visibility.md](post/pose-visibility.md) | Keypoint visibility |
```

**Places that the change edits.** The change adds two closed sets: `pose.decode.visibility.source`
(one value, `keypoints_channel`) and `pose.decode.visibility.activation` (`none`, `sigmoid`). It
extends no existing closed set: the `semantic` set, the `pose.decode.method` set and the size-entry
key list stay as they are. Option E (OpenMMLab-Exporter decision 0041) removes every place of the
size-level form of user decision T33.

| Place | Heading | Edit |
|---|---|---|
| `post.pose.visibility` (`post/pose-visibility.md`) | new file | The front matter above and the text of 2.2 to 2.6. |
| `post.pose.schema` (`post/pose-schema.md`) | `pose.decode` fields table (lines 89-93) | Add the row `pose.decode.visibility` (object, no): "When present, the decode gives a visibility value for each keypoint. See Keypoint visibility (`pose-visibility.md#fields`)." Add the link to the line "Method-specific fields" (line 95): "The visibility applies to the single-person `coordinate` decode: `pose.decode.visibility` (`pose-visibility.md#fields`)." |
| `post.pose.schema` | `pose.decode` fields table, row `pose.decode.is_3d` (line 92), and "Shape key" (lines 103-111) | In line 92, replace "`(N, K, 3)` coordinates (`coordinate`)" with "`(N, K, C)` coordinates with `z` in channel 2 (`coordinate`, C >= 3)". In line 111, replace "for 3D single-person keypoints, `(N, K, 3)` is `x, y, z`" with "for 3D single-person keypoints, channels 0 to 2 of `(N, K, C)` are `x, y, z`". Add the Shape key bullet "`C` — the channel count of a single-person `keypoints` output (at least 2, or 3 when `is_3d: true`)." Reason: the changed coordinate form of this table (row `post.pose.decode.coordinate`) links to the Shape key, and a 3D BlazePose sidecar (`(N, K, 5)`) must not contradict the `is_3d` row. |
| `post.pose.schema` | "Validation rules" (line 127) | No rule changes. Add "Keypoint visibility (`pose-visibility.md#validation-rules`)" to the "See also" line. |
| `post.pose.schema` | "Implementer guidance" | Add: "A pose decode gives named per-point values: `score` and, when declared, `visibility` (Per-point values (`pose-visibility.md#per-point-values`)). Keep them apart. Do not put one value in the place of the other." |
| `post.pose.decode.simcc` (`post/pose-decode-simcc.md`) | "Behaviour" (line 38) | No edit. With option E, the SimCC decode gives no visibility. |
| `post.pose.decode.simcc` | "Authoring guidance" (line 58) | In the bullet "The two 384x288 RTMW configs (l and x) add `decode_visibility=True` to the codec. The sidecar has no field for it. ...", replace "The sidecar has no field for it." with: "The sidecar declares no visibility for them: `pose.decode.visibility` has no SimCC source. On COCO-WholeBody, the RTMW visibility ranks valid hands worse than the raw score at every size (OpenMMLab-Exporter `notes/decisions/0041-rtmw-wrist-gate.md`)." Keep the other sentences and the evidence citation of the bullet. The recording session writes the OpenMMLab-Exporter 0041 citation as a GitHub permalink (skellytracker decision 0028, item 4). Proposal choice: without this edit, the sentence "The sidecar has no field for it" reads as if `pose.decode.visibility` applied to RTMW. |
| `post.pose.decode.coordinate` (`post/pose-decode-coordinate.md`) | "Behaviour" (line 33) | Replace the single-person form with: "single-person — one output with `semantic: keypoints` and the shape `(N, K, C)`. Channels 0 and 1 are `x` and `y`. When `is_3d: true`, channel 2 is `z`, the root-relative depth (in `depth_unit`). `C` is at least 2, or at least 3 when `is_3d: true`. The host reads no other channel, unless `pose.decode.visibility` names it (Keypoint visibility (`pose-visibility.md#behaviour`))." The `(N, K, 2)` and `(N, K, 3)` tensors of today keep their meaning. |
| `post.pose.decode.coordinate` | "Authoring guidance" | Add: "BlazePose (MediaPipe pose landmark model): 39 points with five values each (`x, y, z`, a visibility logit, a presence logit). The visibility is channel 3 with `activation: sigmoid`. The presence (channel 4) has no field at `vNEXT`. The graph gives the values as one flat `[1, 195]` tensor; see the follow-up in 2.4." With the citations of part 1. |
| `post.pose.bottom_up` (`post/pose-bottom-up.md`) | | No edit. A bottom-up model cannot declare a visibility at `vNEXT` (rule `-2`). Its `score` stays the per-point value of a `poses` tensor and of `packed_keypoints`. |
| `common.outputs` (`common/outputs.md`) | | No edit. The change adds no output semantic: the visibility comes from the `keypoints` output that the sidecar already declares. |
| `common.sizes_and_artifacts` (`common/sizes-and-artifacts.md`) | | No edit. The field is a `pose` field, so a size entry cannot set it (`V-common.sizes_and_artifacts-3`, unchanged). All sizes of a family share it (skellytracker decision 0010, unchanged). |
| `format.versioning` (`format/versioning.md`) | "Legacy behaviour" table (lines 72-74) | Add `pose.decode.visibility` to the row "`boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`" ("Not available." / "Available."). The flip-test proposal adds `pose.decode.flip_test` to the same row. The two edits do not conflict. |
| `specs/model-sidecar/README.md` | Section map; "Validation rules" (the validation index, line 121) | Add the section row. Add "- Keypoint visibility (`post/pose-visibility.md#validation-rules`)" after "Coordinate decode". |
| `specs/model-sidecar/changelog.md` | "Summary of changes"; "`schema_version` history" (line 68) | Add the summary row of 2.7. Append the sentence of 2.7 to the existing `vNEXT` row. |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | "Mapping hints for phase 1", "Pose" (lines 62-65) | Add: "Record each value for each keypoint that the upstream decode gives beside the location and the score, for example a visibility or a presence. The spec declares a visibility that is a channel of the single-person `keypoints` output with `pose.decode.visibility`. Another value, or a value that the host must compute from other outputs, is a gap." Merge point: `specs/model-sidecar/proposals/omitted-upstream-output/proposal.md` (place G8) appends ", unless each condition of `omitted` is true (Phase 1, step 3)"; the PR that lands second keeps both. |
| `specs/model-sidecar/templates/model-intake.md` | Property table, after row K8 (line 318) | Add a row "K8a Keypoint visibility: the channel of the `keypoints` output that holds it and its activation, or the upstream computation when no output holds it" with the section `post.pose.visibility`. |
| `specs/model-sidecar/vectors/post.pose.visibility.yaml` | new file | The vectors of part 4. The skellytracker vector tooling (`tools/make_vectors.py`, `tools/tests/test_vectors.py`) needs a builder and the case form of that tooling. The simcc-score-rule proposal describes the same conversion (`specs/model-sidecar/proposals/simcc-score-rule/proposal.md`, part 2.1, rows `tools/make_vectors.py` and `tools/tests/test_vectors.py`). It applies here in the same way. |
| `specs/model-sidecar/reference/post_pose_visibility.py` | new file | The reference file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated matrix | Do not edit it by hand. Run `python tools/sidecar_trace.py matrix` after the section file is in place. |
| `specs/model-sidecar/sidecar-spec.md` | the permanent index | No edit (skellytracker decision 0013). |
| `notes/decisions/` (skellytracker) | | No new entry. Option E needs no change of skellytracker 0010. |
| `post.roi_refiner` (proposed, MediaPipe-Exporter) | | Not a file of skellytracker yet. Part 2.8 lists the edits for that proposal. |

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `pose.decode.visibility` | object | no | When this field is present, the decode gives a visibility value for each keypoint. When it is absent, the decode gives no visibility. It is a top-level field: all sizes of a family share it (a size entry cannot set it, `V-common.sizes_and_artifacts-3`). |
| `pose.decode.visibility.source` | enum | yes, in `visibility` | `keypoints_channel`. The set is closed. It is for the single-person `coordinate` decode. |
| `pose.decode.visibility.channel` | int | yes, in `visibility` | The channel of the `keypoints` output that holds the visibility value. It is at least 2, or at least 3 when `is_3d: true`. |
| `pose.decode.visibility.activation` | enum | yes, in `visibility` | `none` (the graph gives the activated value) or `sigmoid` (the host applies `1 / (1 + exp(-v))`). There is no default. |

```yaml
# BlazePose pose landmark model (x, y, z, visibility logit, presence logit for each point)
pose:
  decode:
    method: coordinate
    is_3d: true
    depth_unit: pixel
    visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}

# RTMW (every size; OpenMMLab-Exporter decision 0041): no visibility
pose:
  decode:
    method: simcc
```

### 2.3 Behaviour

Normative text of `post.pose.visibility`:

```text
## Per-point values

The pose decode gives named values for each keypoint, in the order of pose.tracked_points:

- score: the keypoint score of the decode method. SimCC decode gives it. A bottom_up poses tensor
  gives it, and packed_keypoints with the component score gives it. At vNEXT, the single-person
  coordinate decode gives no score. The heatmap decode gives the score that its section states.
- visibility: the value of this section. The decode gives it only when the sidecar declares
  pose.decode.visibility. At vNEXT, only the single-person coordinate decode can declare it.

A consumer of the pose output names the value that it reads. An example is roi_source.score_gate
of an ROI refiner. The host must not give one value in the place of the other.

## Behaviour

The host computes the visibility from the keypoints output, before the unprojection. The visibility
does not change the location of a keypoint, and the location does not change the visibility. The
unprojection does not change the visibility.

source: keypoints_channel (pose.decode.method: coordinate, single person). The keypoints output
has the shape (N, K, C). For each crop n and each keypoint k:

    v = keypoints[n, k, channel]
    visibility[n, k] = v                    when activation: none
                       1 / (1 + exp(-v))    when activation: sigmoid

- A sigmoid visibility is in [0, 1].
- The reference arithmetic is float64. The section states no precision. A float32 host can differ
  from it. Compare a host with the vectors within the tolerances of the vector file.
- The visibility has no fixed relation to a score. Do not use a threshold of one for the other.

Inverse: none. The visibility is not a coordinate.
```

Notes, not normative:

- **Option E (OpenMMLab-Exporter decision 0041).** The section has no SimCC source. mmpose decodes
  `keypoints_visible` for the two RTMW 384x288 configs (part 1). OpenMMLab-Exporter decision 0041 measured that value for
  all five RTMW sizes and drops it (part 1, "Measured difference"). A later model that needs a
  visibility that the host computes from other outputs needs a new proposal with a new `source`
  value.
- **One `source` value (proposal choice).** The block keeps the key `source` with the one value
  `keypoints_channel`. A later source can then be added, and the existing blocks do not change. The
  refiner proposal cites the block in this form
  (`{source: keypoints_channel, channel: 3, activation: sigmoid}`).
- **The precision.** The section states no precision, as user decision T25 (1) for
  `rotated_roi_crop` (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) and the simcc-score-rule text ("The reference
  arithmetic is float64. A host can use float32."). The MediaPipe sigmoid is float32
  (`tensors_to_landmarks_calculator.cc:27`). On the vectors of part 4, a float32 form differs from the
  float64 reference by at most 4.9e-8. Question Q3 asks the user.
- **No fallback.** mmpose sets `keypoints_visible = keypoint_scores` when the codec gives no
  visibility (`topdown.py:157-159`). The spec does not copy this: a host without
  `pose.decode.visibility` gives no visibility. The two values have other scales (OpenMMLab-Exporter decision 0041,
  part 1), and a consumer must know which value it reads.

### 2.4 Validation rules

New rules of `post.pose.visibility`:

- [ ] `V-post.pose.visibility-1` **(vNEXT)** If `pose.decode.visibility` is present, it must be a
  mapping with a `source`. `source` must be `keypoints_channel`.
- [ ] `V-post.pose.visibility-2` **(vNEXT)** With `source: keypoints_channel`, `pose.decode.method` must
  be `coordinate`, and `pose.estimator_type` must not be `bottom_up`. The block must have exactly the
  keys `source`, `channel` and `activation`. `channel` must be an integer `>= 2`, or `>= 3` when
  `is_3d: true`. A boolean is not an integer. `activation` must be `none` or `sigmoid`.
- [ ] `V-post.pose.visibility-3` **(vNEXT)** With `source: keypoints_channel`, when the `keypoints`
  output declares a `shape` with a concrete last dimension `C`, `channel` must be less than `C`.
- [ ] `V-post.pose.visibility-4` A sidecar with `schema_version < vNEXT` must not contain
  `pose.decode.visibility`, at the top level or in a size entry.

Rule `-4` has the form of `V-pre.resize.affine_person_crop-3` of the affine-crop proposal (user
decision A3, option 1, plan T23, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)): a legacy sidecar with the field fails, so the
host never ignores it without an error. A legacy sidecar deep-merges every key of its size entries
(`common/sizes-and-artifacts.md:128`), so the rule also names the size entries.

The rewrite for E renumbers the rules. The A1 text had `-1` to `-6`: its `-2` (`simcc_softmax`)
and `-6` (the size-level block) are removed; its `-3`, `-4` and `-5` are now `-2`, `-3` and `-4`. No
other plan file of the two exporter repos cites a rule of this section by its number, except
the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (the row of this proposal). It cites the new range `-1` to `-4`.
Row K8a of the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (`:193`; `out of scope (0041)`, user decision
T36) no longer cites a rule of this section.

Existing rules that name a value of this change:

- `V-post.pose.schema-3` (the `method` values): unchanged.
- `V-post.pose.schema-7` (exactly one `keypoints` output for a single-person `coordinate` decode):
  unchanged. The visibility channel is in that output.
- `V-post.pose.schema-9` (`depth_unit` with `is_3d`): unchanged. Rule `-2` reads `is_3d` for the first
  free channel.
- `V-post.pose.decode.coordinate-1` (`coordinate_scale`): unchanged.
- `V-post.pose.bottom_up-2` (`packed_keypoints.components` from `x`, `y`, `z` and `score`): unchanged.
- `V-common.outputs-4` (the closed `semantic` set): unchanged. No new semantic.
- `V-common.sizes_and_artifacts-3` (a size entry holds only `input.shape`, `input.resize.target_size`
  and `onnx`): unchanged. A size entry thus cannot hold `pose.decode.visibility` at `vNEXT`. (User
  decision T33 changed this rule in the A1 text. Option E removes that change.)

Follow-ups, not in this proposal:

- A flat keypoints tensor. The BlazePose graph gives `[1, 195]`, not `[1, 39, 5]` (part 1). The
  coordinate decode (current and changed text) describes `(N, K, C)`. A BlazePose sidecar needs either
  a `Reshape` in the exported graph (an exporter choice of MediaPipe-Exporter) or a spec rule for a
  flat `(N, K * C)` tensor. The BlazePose intake (the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts), 2026-10-24) records it: the exporter plan reshapes the tensor to `[B, 39, 5]`, and a flat layout is a conditional gap with no proposal (rows G5a, G5e and K5). This proposal does not add the rule, because
  it is a layout of the coordinate decode, not a visibility rule.
- A per-point presence (BlazePose channel 4, sigmoid, `tensors_to_landmarks_calculator.cc:176-178`).
  No consumer in scope reads it (question Q2).
- A visibility for a bottom-up model, for example a `visibility` component of `packed_keypoints`. No
  model in scope needs it.
- A SimCC visibility (the mmpose `decode_visibility=True`). Not added (option E, OpenMMLab-Exporter decision 0041). No
  model in scope needs it.

### 2.5 Selectors

`pose.decode.visibility` (present), at the top level, with `pose.decode.method=coordinate`.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` cannot declare `pose.decode.visibility` (rule `-4`). Its decode
  gives no visibility. The package sidecars (`rtmpose-body`, `rtmpose-hand`, `rtmpose-face`,
  `rtmw-wholebody`, all `v2024.09.1019`) keep their meaning.
- The change to the single-person coordinate shape (`(N, K, C)` with `C` at least 2 or 3) adds no
  meaning to an existing tensor: `(N, K, 2)` and `(N, K, 3)` read as before. It needs no legacy row.
- The change goes into the `vNEXT` revision.
- The "Legacy behaviour" table of `format/versioning.md` gets the edit of 2.1. The new section needs no
  "Legacy behaviour" heading of its own: the field has no legacy meaning.

### 2.7 Changelog row

Summary of changes (`changelog.md:16`, five columns). `N` is the next free number in the merge order
of the open proposals (rows 1 to 19 exist).

```text
| N | Pose | New optional `pose.decode.visibility`: a visibility value for each keypoint of the single-person coordinate decode. `source: keypoints_channel` reads one channel of the `keypoints` output, with `activation` `none` or `sigmoid`. The single-person `keypoints` output can have more channels than `x, y(, z)`. The decode names its per-point values `score` and `visibility`. | BlazePose (visibility logit) and the wrist gate of the hand ROI refiner | [Keypoint visibility](post/pose-visibility.md) |
```

Sentence to append to the end of the existing `vNEXT` row of the `schema_version` history
(`changelog.md:68`):

```text
Added the optional `pose.decode.visibility` (`source: keypoints_channel` with `channel` and `activation`): a visibility value for each keypoint of the single-person coordinate decode; the single-person `keypoints` output can carry more channels than `x, y(, z)`.
```

### 2.8 Edits that the refiner proposal needs (MediaPipe-Exporter, not made here)

The refiner proposal is `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`
with its reference file in the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`. This proposal does not edit them.
A session of MediaPipe-Exporter, or a session that the user permits, makes these edits. Line numbers
in brackets are those of the current files (checked again on 2026-10-24 for the rewrite for E, and
again after the refiner edits of items 11 to 13, and again on 2026-10-25).

**Status.** Items 1 to 13 are applied: the refiner proposal records this (its lines 14-17). Its
fields, rules `-14` to `-16`, vectors and reference file have the named gate value. User decision
T33 (2026-10-24) made the gate value a runtime input of the host or the user, with the sidecar
default `score_gate.value_default` (Holistic: `visibility`), and the threshold range follows the
value in effect. That stays: it is a need of the refiner, and an RTMW parent now uses the value
`score` at every size (OpenMMLab-Exporter decision 0041). User decision T34: when the parent gives no value for the
gate value in effect, the host refuses the parent; it never skips the gate. Items 1 to 10 keep their
first text for the record: "There is no default" (item 3) and "no `value` (refused)" (item 9) are
superseded by T33, and the key `value` is now `value_default`.

**The per-size parent check (option E).** Under A1, an RTMW 256x192 size gave only `score` and an
RTMW 384x288 size gave `score` and `visibility`. Thus the A1 text of this part asked for a parent
check at the parent size in use, only because of A1. Under option E, no size of a family differs
from another in its per-point values: `pose.decode.visibility` is a top-level field (2.2), and every
RTMW size gives only `score`. Thus this proposal does not need a per-size check. The refiner
proposal holds the check at the parent size in use as normative text (heading "ROI source",
`:501-516`; rule `V-post.roi_refiner-15`, `:751-758`). Under E, that check gives the same result at
each size of a parent, so it does not conflict with this proposal. This file does not ask to remove
it. The dependency is in items 11 to 13.

1. **Header, row "Depends on"** (`:56`): add this proposal
   (`specs/model-sidecar/proposals/keypoint-visibility/proposal.md`, section
   `post.pose.visibility`). A refiner sidecar with a gate on the visibility needs it. The refiner
   section can land first. Until this proposal lands, a gate can name only `value: score`.
2. **Part 1, the bullet "The per-point score of the parent"** (now "The per-point value of the
   parent", `:119-129`): replace "until a proposal for the BlazePose pose landmark model adds a
   per-point score" with a citation of this proposal. The BlazePose parent declares
   `pose.decode.visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}`. The
   BlazePose intake is the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts) (2026-10-24; deferred: the untracked BlazePose plan of MediaPipe-Exporter (plan facts)). Its rows K5 and K8a link this proposal. The flat `[1, 195]` output is a conditional gap there (2.4 of this file).
3. **Fields table, row `roi_source.score_gate`**: `{point, value, score_threshold_default}`. Add the
   row `roi_source.score_gate.value` (enum, yes in `score_gate`): "The per-point value of the parent
   that the gate reads: `score` or `visibility` (heading "Per-point values" of
   `post.pose.visibility`). There is no default." In the row text, "the per-point score of the parent
   point" becomes "the per-point value `value` of the parent point".
4. **The range of the threshold** (rules `V-post.roi_refiner-14` and `-16`, now `:746-765`, and
   the note on the ranges after them): `0 <= t < 1` for `value: visibility` (in `[0, 1]`); any finite number for
   `value: score`. A SimCC score has no fixed range: OpenMMLab-Exporter decision 0041 gives two RTMW thresholds for
   each size (user decision T37). `t_recall` is the default recommendation: it matches the recall of
   the Holistic gate (for example 2.974 for x-384). `t_J` (Youden) is the selective option (for
   example 7.198 for x-384). Neither threshold goes into the sidecar (U4). The runtime override of
   T26 (6) uses the same range.
5. **Normative text, heading "ROI source"**: the parent check names the gate value; the paragraph on
   the per-point score becomes a link to the heading "Per-point values" of `post.pose.visibility`;
   step 1 reads the per-point value of the gate.
6. **The YAML excerpt of the hand model** (the `score_gate:` block, now `:425`): add the gate value
   (now `value_default: visibility`).
7. **Rules** `V-post.roi_refiner-14` (the key set and the range of item 4) and
   `V-post.roi_refiner-15` (the parent gives the gate value).
8. **Reference file** (the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`): `check_parent` takes the set of the
   per-point value names of the parent (for example `{"visibility"}` for BlazePose and `{"score"}`
   for RTMW at every size) in place of `has_point_scores: bool`; `roi_from_keypoints` takes the
   values of the kind that the gate value names (the output of `point_values` of
   the part 3 code of `specs/model-sidecar/proposals/keypoint-visibility/proposal.md`, or the same map).
9. **Vectors** of part 4 of the refiner proposal: each `score_gate` block gets the gate value. New
   cases: an unknown value (refused); a parent that gives only `score` and a gate on `visibility`
   (refused by `check_parent`); `value: score` with a threshold of `5.0` (accepted, item 4).
10. **Part 6, rows "Module and function" and "Dispatch point"**: today `Keypoints.visibility` of
    skellytracker holds the keypoint score ("confidence scores 0.0–1.0",
    `skellytracker/core/data_primitives/keypoints.py:19`; the RTMW detector fills it from
    `kpt_scores`, `rtmw_wholebody_detector.py:103-106`). With this proposal, the parent check looks at
    the decode method and at `pose.decode.visibility` of the parent, and `roi_from_keypoints` reads
    the named per-point value (part 6 of this file, the name conflict).

**Edits that option E needed in the refiner proposal** (2026-10-24; applied by the refiner session,
not made here; first text kept for the record). Items 11 to 13 are applied (the refiner proposal
records this at its lines 14-17 and 4077). The line numbers in brackets now point at the edited
text (checked again on 2026-10-25). Some places already showed E before these edits (now
`:150-151`, `:613-614`, `:916-918`).

11. **The heading "Sizes" of `post.pose.visibility`.** Under E, this section has no heading
    "Sizes". The refiner cites it at `:528-529` and `:536` (heading "ROI source": "headings "Per-point values" and
    "Sizes"") and `:756` (rule `V-post.roi_refiner-15`). Cite the heading "Per-point values" only. The
    parent size in use can stay in the check (see above).
12. **The A1 examples.** Replace each example in which an RTMW 384x288 size gives `score` and
    `visibility` with the E state (an RTMW parent gives only `score` at every size, OpenMMLab-Exporter decision 0041):
    the header (`:21-23`), part 1 (`:135-136`), the heading "ROI source" (`:528-529`), part 4
    (`:918`, `:1058`), part 8 (`:3878`, the row "A gate value from the decode method": the reason
    "RTMW 384x288 gives `score` and `visibility`" no longer has a model in scope), the user-decision
    record (`:3975`), and the docstring of `check_parent` in the reference file
    (the part 3 code of `specs/model-sidecar/proposals/roi-refiner-role/proposal.md`).
13. **The vector `parent-wholebody-names-accepted`** (`:2442-2446`). Its comment said that the
    parent gives `score` and `visibility` ("RTMW 384x288 with pose.decode.visibility"). Under E, an
    RTMW parent gives `[score]`. The refiner session chooses: give the case `[score]`, or keep both
    values and name it a generic parent, not RTMW 384x288. The case count of the refiner then
    changes only if a case is added or removed.

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/model-sidecar/proposals/<slug>/proposal.md`) | the part 3 code of `specs/model-sidecar/proposals/keypoint-visibility/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_pose_visibility.py` |
| Functions (one for each algorithm) | `validate_visibility` (rules `-1` to `-4`), `activate` (`none` or `sigmoid`), `channel_visibility` (`source: keypoints_channel`), `decode_visibility` (the full step: the block selects the source, or no visibility), `point_values` (the heading "Per-point values": the named values `score` and `visibility`) |

Source commit: none (no host code). This exporter has no SimCC decode and no coordinate decode on its
host side (`rtmw/adapter.py:136` at `32ab848`, cited by `specs/model-sidecar/proposals/simcc-score-rule/proposal.md`
part 3). The functions come from the text of part 2. The section is new, so this file implements the
full section. It does not implement the location of the coordinate decode, the SimCC decode
(`post.pose.decode.simcc`, with its own reference file in the part 3 code of `specs/model-sidecar/proposals/simcc-score-rule/proposal.md`)
or the unprojection. The arithmetic is float64. The note at the top of the file gives the source
commit, the pins (skellytracker `dom/18-agents-adr-bootstrap-kit`, exporter `32ab848`; checked again at skellytracker
`dom/21-move-sidecar-guide` and exporter `f3aeb47` on 2026-10-25, no cited line changed) and the vector result. The
rewrite for E removed the functions `visibility_for_size`, `scaled_softmax_peak` and
`simcc_visibility`.

```python
"""Reference implementation of the proposed section post.pose.visibility.

This file uses ASD-STE100 Simplified Technical English.

- Section ID: post.pose.visibility (proposed; OpenMMLab-Exporter proposal keypoint-visibility,
  specs/model-sidecar/proposals/keypoint-visibility/proposal.md).
- Source commit: none (no host code). The functions come from the text of part 2 of the proposal.
- Spec text read at skellytracker `dom/18-agents-adr-bootstrap-kit`. Exporter commit 32ab848 (OpenMMLab-Exporter decisions
  0041 and 0042 committed). Checked again at exporter f3aeb47 and skellytracker `dom/21-move-sidecar-guide` on
  2026-10-25: no cited line changed.
- Vectors: this file makes the vectors of part 4. They are unverified: no host implementation.
  All 31 cases of part 4 pass against this file (run of 2026-10-25, option E, recorded in part 4).
  The run of 2026-10-24 had 30 cases. The case validate-error-mapping-without-source is new.
  Each `params` key and each `input` key of a case is an argument of the function. A runner gives
  each numeric list of `input` as a float64 NumPy array.
- Option E (OpenMMLab-Exporter decision 0041, 2026-10-24): no RTMW size declares
  pose.decode.visibility. The only source is keypoints_channel (BlazePose). This file has no
  SimCC visibility and no size-level block.
- Parity result: to run.

The functions use only NumPy and the Python standard library. The arithmetic is float64. The section
states no precision (part 2.3 of the proposal). Each function implements one step of part 2.3.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

SOURCES = ("keypoints_channel",)
KEYPOINTS_CHANNEL_KEYS = ("source", "channel", "activation")
ACTIVATIONS = ("none", "sigmoid")
POINT_VALUES = ("score", "visibility")


def validate_visibility(visibility: Any, method: str, estimator_type: str, is_3d: bool = False,
                        keypoints_channels: int | None = None, schema_is_vnext: bool = True) -> bool:
    """post.pose.visibility: rules V-post.pose.visibility-1 to -4 for the block pose.decode.visibility.

    ``method`` is ``pose.decode.method``. ``estimator_type`` is ``pose.estimator_type``.
    ``keypoints_channels`` is the last dimension of the ``keypoints`` output when the sidecar gives a
    concrete one, else ``None``. ``schema_is_vnext`` is true when ``schema_version >= vNEXT``.
    Raises ``ValueError`` at the first rule that fails. Returns ``True`` when all rules pass.
    """
    # rule -4: not available below vNEXT
    if not schema_is_vnext:
        raise ValueError("pose.decode.visibility needs schema_version >= vNEXT")
    # rule -1: a mapping with a known source
    if not isinstance(visibility, Mapping):
        raise ValueError("pose.decode.visibility must be a mapping")
    if visibility.get("source") not in SOURCES:
        raise ValueError("pose.decode.visibility.source must be keypoints_channel")
    # rule -2
    if method != "coordinate" or estimator_type == "bottom_up":
        raise ValueError("source keypoints_channel needs pose.decode.method: coordinate and a "
                         "single-person estimator_type")
    if set(visibility) != set(KEYPOINTS_CHANNEL_KEYS):
        raise ValueError("source keypoints_channel must have exactly the keys source, channel and activation")
    channel = visibility["channel"]
    first_free = 3 if is_3d else 2
    if not (isinstance(channel, int) and not isinstance(channel, bool) and channel >= first_free):
        raise ValueError(f"pose.decode.visibility.channel must be an integer >= {first_free}")
    if visibility["activation"] not in ACTIVATIONS:
        raise ValueError("pose.decode.visibility.activation must be none or sigmoid")
    # rule -3
    if keypoints_channels is not None and channel >= keypoints_channels:
        raise ValueError("pose.decode.visibility.channel must be less than the last dimension of the "
                         "keypoints output")
    return True


def activate(values: np.ndarray, activation: str) -> np.ndarray:
    """post.pose.visibility, source keypoints_channel: the activation of the channel values.

    ``none`` returns the values. ``sigmoid`` returns ``1 / (1 + exp(-v))``. A large negative ``v``
    gives 0 and a large positive ``v`` gives 1.
    """
    v = np.asarray(values, dtype=np.float64)
    if activation == "none":
        return v.copy()
    if activation == "sigmoid":
        with np.errstate(over="ignore"):
            return 1.0 / (1.0 + np.exp(-v))
    raise ValueError(f"unknown activation {activation!r}")


def channel_visibility(keypoints: np.ndarray, channel: int, activation: str) -> np.ndarray:
    """post.pose.visibility, source keypoints_channel: the visibility (N, K) of each keypoint.

    ``keypoints`` is the single-person ``keypoints`` output (N, K, C). The value is
    ``activate(keypoints[:, :, channel], activation)``.
    """
    kp = np.asarray(keypoints, dtype=np.float64)
    return activate(kp[:, :, int(channel)], activation)


def decode_visibility(visibility: Mapping[str, Any] | None,
                      keypoints: np.ndarray | None = None) -> np.ndarray | None:
    """post.pose.visibility: the full step. Returns the visibility (N, K), or ``None``.

    ``visibility`` is the block ``pose.decode.visibility``, or ``None`` when the sidecar does not
    declare it. Then the decode gives no visibility. ``keypoints`` is the single-person
    ``keypoints`` output (N, K, C). The function expects a block that ``validate_visibility``
    accepts: it does not check the keys or the channel bound, so another block can raise
    ``KeyError`` or ``IndexError``.
    """
    if visibility is None:
        return None
    if visibility["source"] == "keypoints_channel":
        return channel_visibility(keypoints, visibility["channel"], visibility["activation"])
    raise ValueError(f"unknown source {visibility['source']!r}")


def point_values(score: np.ndarray | None, visibility: np.ndarray | None) -> dict[str, np.ndarray]:
    """post.pose.visibility, heading "Per-point values": the named values that the decode gives.

    The key ``score`` is present when the decode gives a keypoint score. The key ``visibility`` is
    present when the sidecar declares ``pose.decode.visibility``. A consumer, for example
    ``roi_source.score_gate`` of an ROI refiner, reads one value by its name.
    """
    values: dict[str, np.ndarray] = {}
    if score is not None:
        values["score"] = np.asarray(score)
    if visibility is not None:
        values["visibility"] = np.asarray(visibility)
    return values


__all__ = [
    "activate",
    "channel_visibility",
    "decode_visibility",
    "point_values",
    "validate_visibility",
]
```

## 4. Vectors

**Option E (OpenMMLab-Exporter decision 0041).** The rewrite removed the cases of the removed paths:
`validate-rtmw-384`, `validate-error-simcc-softmax-on-coordinate`, `validate-error-simcc-softmax-3d`,
`validate-error-simcc-softmax-extra-key`, `validate-error-beta-zero`, `validate-error-beta-bool`,
`validate-error-sigma-one-value`, the seven `size-*` cases, the five `peak-*` cases, the five `vis-*`
cases and `decode-simcc-softmax` (25 of the 46 A1 cases; 21 stay). It checked again the cases that stay:
`validate-error-legacy` now has a `keypoints_channel` block; `validate-error-unknown-source` has the
message of the one-value set; `channel-2d-none` is now `channel-2d-none-batch` (N = 2); the comments
of the `values-*` cases name the E state. New cases (8): `validate-channel-no-concrete-shape`, `validate-error-simcc-softmax-source` (rule `-1`
refuses the A1 block), `validate-error-channel-extra-key`, `validate-error-channel-no-activation`,
`validate-error-channel-bool`, `validate-error-channel-float`, `decode-error-simcc-softmax` and
`values-none`. A review of 2026-10-24 added `act-error-unknown` (the error branch of `activate`).
A review of 2026-10-25 added `validate-error-mapping-without-source` (rule `-1`: a mapping without
the key `source`; no case had this block before). The rule numbers in the comments are the new numbers.

The vectors come from the reference file. The runner checks each sigmoid case against a value that
it computes with its own formula (`1 / (1 + math.exp(-v))`) for `act-sigmoid`,
`channel-blazepose-layout` and `decode-keypoints-channel`. Each error case must raise `ValueError`.
Its expected message is the message of the reference file.

- **Result:** 31 of 31 cases pass against the reference file (run of 2026-10-25, option E, after the
  case `validate-error-mapping-without-source` was added). The runner is `kv-f7\run_vectors.py` in
  the local temporary scratch folder of the session of 2026-10-25 (not in a repo), a copy of the
  runner `kv-run\run_vectors.py` below. Command: `uv run python -B kv-f7\run_vectors.py .` from the
  exporter root. Output: "31 of 31 cases pass; hand sigmoid check max diff 0.0e+00". The same runner
  gave 30 of 30 before the edit. History note: 30 of 30 cases passed in the run of 2026-10-24
  (option E, after the case `act-error-unknown` was added; before it: 29 of 29; A1 after T33: 46 of
  46; before T33: 39 of 39). The runner is `scratchpad\fu-visibility\run_vectors.py` of
  session `1ffa39f8` (header, "Scratch files"). It reads the YAML block of this file, gives each
  numeric list of `input` as a float64 NumPy array and each `params` value as it is, and runs with
  `python -B` (no `__pycache__`). The three hand checks agree to 1e-15. Run again on 2026-10-25
  with a new runner of the same form (`kv-run\run_vectors.py` in the local temporary scratch folder
  of that session, not in a repo; `uv run python -B`): 30 of 30 pass, and the hand checks agree.
- **Branches, ties and strict comparisons.** Rule `-1`: no mapping, an unknown source, the removed
  source `simcc_softmax`, a mapping without the key `source`. Rule `-2`: each method that is not `coordinate` (`simcc`, `heatmap`),
  `bottom_up`, an extra key, a missing key, a boolean, a float, an unknown activation, and the bound
  `>=`: channel 2 passes in 2D and fails in 3D, channel 3 passes in 3D. Rule `-3` (strict `<`):
  channel 2 with `C = 3` passes, channel 5 with `C = 5` fails, and no concrete `C` gives no bound.
  Rule `-4`: a legacy sidecar. `activate`: `v = 0` gives exactly 0.5, saturation at ±800 (0 and 1
  exactly), `none`, an unknown activation (error). `decode_visibility`: no block, the channel source, a refused source.
  `point_values`: each of the four combinations of `score` and `visibility`.
- **Mutation check:** the expected value `[0][1]` of `channel-blazepose-layout` plus 1e-6 makes
  exactly 1 case fail (that case). The expected value of `validate-error-channel-out-of-range` set to
  `{valid: true}` makes exactly 1 case fail (that case). `keypoints_channels: 2` in
  `validate-channel-2-in-2d` makes exactly 1 case fail (that case). This file is unchanged by the
  check.
- **float32:** with float32 inputs and a float32 form of `activate`, 25 of 31 cases pass at the case
  tolerances (run of 2026-10-25, scratch `kv-f7\run_f32.py`; the same run before the new case gave
  24 of 30, as the first text of this bullet). The other 6 differ by at most 4.9e-8 (`act-sigmoid`, `channel-blazepose-layout`); the
  exact cases differ by the float32 rounding of their inputs (at most 2.9e-8).
- **Cases by function:** `validate_visibility` 18, `activate` 4, `channel_visibility` 2,
  `decode_visibility` 3, `point_values` 4.
- No case ran through upstream code. The upstream files are read-only data for this proposal.
- No case is a pixel case. The `compare` tolerances (`1.0e-09`) are for the float64 order of the
  transcendental functions.

The YAML uses the form of the template (`generated_by: <reference file>`, a `function` key and an
optional `compare` key on each case). The skellytracker tooling needs the conversion of 2.1 (row
`specs/model-sidecar/vectors/post.pose.visibility.yaml`).

```yaml
section: post.pose.visibility
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/keypoint-visibility/proposal.md`
unverified: "No exporter has a host implementation of post.pose.visibility, and skellytracker has
  none. The cases come from the reference file and from the hand values of the runner."
# Upstream code read, not run: MediaPipe e9794ef calculators/tensor/tensors_to_landmarks_calculator.cc:27-38,
# 172-178 (keypoints_channel). Option E (OpenMMLab-Exporter decision 0041): no SimCC source.
cases:
  # BlazePose (x, y, z, visibility, presence): channel 3, sigmoid (tensors_to_landmarks_calculator.cc:172-174)
  - id: validate-blazepose-channel
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
      keypoints_channels: 5
    input: {}
    expect: {valid: true}
  # 2D: channel 2 is the first channel after x and y (the bound of rule -2); 2 < C = 3 (the bound of rule -3)
  - id: validate-channel-2-in-2d
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 2, activation: none}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: false
      keypoints_channels: 3
    input: {}
    expect: {valid: true}
  # rule -3: no concrete last dimension, so no upper bound for the channel
  - id: validate-channel-no-concrete-shape
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 9, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
      keypoints_channels: null
    input: {}
    expect: {valid: true}
  # rule -4: not available below vNEXT
  - id: validate-error-legacy
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
      schema_is_vnext: false
    input: {}
    expect: {error: pose.decode.visibility needs schema_version >= vNEXT}
  # rule -1
  - id: validate-error-not-a-mapping
    function: validate_visibility
    params: {visibility: keypoints_channel, method: coordinate, estimator_type: top_down_single_person}
    input: {}
    expect: {error: pose.decode.visibility must be a mapping}
  # rule -1: the source set is closed
  - id: validate-error-unknown-source
    function: validate_visibility
    params:
      visibility: {source: channel, channel: 3, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: pose.decode.visibility.source must be keypoints_channel}
  # rule -1: a mapping must have the key source (a block without it is not a keypoints_channel block)
  - id: validate-error-mapping-without-source
    function: validate_visibility
    params:
      visibility: {channel: 3, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: pose.decode.visibility.source must be keypoints_channel}
  # rule -1, option E (OpenMMLab-Exporter decision 0041): no SimCC source, also with the SimCC decode
  - id: validate-error-simcc-softmax-source
    function: validate_visibility
    params:
      visibility:
        source: simcc_softmax
        beta: 150.0
        sigma: [6.0, 6.93]
      method: simcc
      estimator_type: top_down_single_person
    input: {}
    expect: {error: pose.decode.visibility.source must be keypoints_channel}
  # rule -2: no SimCC form
  - id: validate-error-channel-on-simcc
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
      method: simcc
      estimator_type: top_down_single_person
    input: {}
    expect: {error: 'source keypoints_channel needs pose.decode.method: coordinate and a single-person estimator_type'}
  # rule -2: no heatmap form
  - id: validate-error-channel-on-heatmap
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
      method: heatmap
      estimator_type: top_down_single_person
    input: {}
    expect: {error: 'source keypoints_channel needs pose.decode.method: coordinate and a single-person estimator_type'}
  # rule -2: no bottom-up form
  - id: validate-error-channel-bottom-up
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
      method: coordinate
      estimator_type: bottom_up
      is_3d: true
    input: {}
    expect: {error: 'source keypoints_channel needs pose.decode.method: coordinate and a single-person estimator_type'}
  # rule -2: closed key set (an extra key)
  - id: validate-error-channel-extra-key
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid, beta: 150.0}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: 'source keypoints_channel must have exactly the keys source, channel and activation'}
  # rule -2: closed key set (no activation; there is no default)
  - id: validate-error-channel-no-activation
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: 'source keypoints_channel must have exactly the keys source, channel and activation'}
  # rule -2: channel 2 is z when is_3d is true
  - id: validate-error-channel-overlaps-z
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 2, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: pose.decode.visibility.channel must be an integer >= 3}
  # rule -2: a boolean is not an integer
  - id: validate-error-channel-bool
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: true, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: false
    input: {}
    expect: {error: pose.decode.visibility.channel must be an integer >= 2}
  # rule -2: a float is not an integer
  - id: validate-error-channel-float
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3.0, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: pose.decode.visibility.channel must be an integer >= 3}
  # rule -2
  - id: validate-error-activation-unknown
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: softmax}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
    input: {}
    expect: {error: pose.decode.visibility.activation must be none or sigmoid}
  # rule -3: the channels are 0 to 4, so channel 5 (= C) fails
  - id: validate-error-channel-out-of-range
    function: validate_visibility
    params:
      visibility: {source: keypoints_channel, channel: 5, activation: sigmoid}
      method: coordinate
      estimator_type: top_down_single_person
      is_3d: true
      keypoints_channels: 5
    input: {}
    expect: {error: pose.decode.visibility.channel must be less than the last dimension of the keypoints output}
  # 1 / (1 + exp(-v)); v = 0 gives exactly 0.5
  - id: act-sigmoid
    function: activate
    params: {activation: sigmoid}
    input:
      values: [0.0, 2.0, -2.0]
    expect:
      activated: [0.5, 0.8807970779778823, 0.11920292202211755]
    compare:
      activated: {atol: 1.0e-09}
  # exp(800) is above the float64 range: 1 / inf = 0
  - id: act-sigmoid-saturates
    function: activate
    params: {activation: sigmoid}
    input:
      values: [-800.0, 800.0]
    expect:
      activated: [0.0, 1.0]
  # the graph gives an activated value
  - id: act-none
    function: activate
    params: {activation: none}
    input:
      values: [-1.5, 0.25, 3.0]
    expect:
      activated: [-1.5, 0.25, 3.0]
  # an activation that is not none or sigmoid has no form (validation refuses it, rule -2)
  - id: act-error-unknown
    function: activate
    params: {activation: softmax}
    input:
      values: [0.0]
    expect: {error: "unknown activation 'softmax'"}
  # (x, y, z, visibility, presence): the host reads channel 3 only; channel 4 does not change the value
  - id: channel-blazepose-layout
    function: channel_visibility
    params: {channel: 3, activation: sigmoid}
    input:
      keypoints: [[[10.0, 20.0, -1.0, 0.0, 3.0], [30.0, 40.0, 0.5, 2.0, -1.0]]]
    expect:
      visibility: [[0.5, 0.8807970779778823]]
    compare:
      visibility: {atol: 1.0e-09}
  # 2D, one channel after x and y, already activated; N = 2 crops
  - id: channel-2d-none-batch
    function: channel_visibility
    params: {channel: 2, activation: none}
    input:
      keypoints: [[[10.0, 20.0, 0.9], [30.0, 40.0, 0.1]], [[5.0, 6.0, 0.0], [7.0, 8.0, 1.0]]]
    expect:
      visibility: [[0.9, 0.1], [0.0, 1.0]]
  # no pose.decode.visibility: the decode gives no visibility (every RTMW size, OpenMMLab-Exporter decision 0041)
  - id: decode-absent
    function: decode_visibility
    params: {visibility: null}
    input:
      keypoints: [[[1.0, 2.0, 3.0, 0.0, 9.0]]]
    expect: {visibility: null}
  # the block selects channel_visibility
  - id: decode-keypoints-channel
    function: decode_visibility
    params:
      visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}
    input:
      keypoints: [[[1.0, 2.0, 3.0, 0.0, 9.0]]]
    expect:
      visibility: [[0.5]]
  # a source that validation refuses (rule -1) has no decode
  - id: decode-error-simcc-softmax
    function: decode_visibility
    params:
      visibility:
        source: simcc_softmax
        beta: 150.0
        sigma: [6.0, 6.93]
    input:
      keypoints: [[[1.0, 2.0, 3.0, 0.0, 9.0]]]
    expect: {error: "unknown source 'simcc_softmax'"}
  # BlazePose: the coordinate decode gives no score
  - id: values-visibility-only
    function: point_values
    params: {}
    input:
      score: null
      visibility: [[0.5, 0.88]]
    expect:
      values:
        visibility: [[0.5, 0.88]]
  # RTMW at every size (OpenMMLab-Exporter decision 0041): the SimCC decode gives the score and no visibility
  - id: values-score-only
    function: point_values
    params: {}
    input:
      score: [[0.6, 0.3]]
      visibility: null
    expect:
      values:
        score: [[0.6, 0.3]]
  # the two names stay apart (no decode in scope gives both at vNEXT)
  - id: values-score-and-visibility
    function: point_values
    params: {}
    input:
      score: [[7.5, 0.4]]
      visibility: [[0.97, 0.2]]
    expect:
      values:
        score: [[7.5, 0.4]]
        visibility: [[0.97, 0.2]]
  # neither value: for example a coordinate decode with no pose.decode.visibility
  - id: values-none
    function: point_values
    params: {}
    input:
      score: null
      visibility: null
    expect:
      values: {}
```

Each key of `params` and `input` is a parameter of the function that the case names.

## 5. Parity evidence

**RTMW** (this exporter): none. With option E (OpenMMLab-Exporter decision 0041), no RTMW sidecar declares
`pose.decode.visibility`, so this exporter has no parity run for this section. The A1 text
planned a parity script `notes/decisions/scripts/pose_visibility_parity.py` for `l-384` and
`x-384`; it is not needed and not written. OpenMMLab-Exporter decision 0041 measured the RTMW visibility and the RTMW
score as gate values (part 1). That is evidence for option E, not a parity run of this section.

**BlazePose** (MediaPipe-Exporter, no git repo; thus `to run`, exporter guide "An exporter with no
git repo"):

| Item | Value |
|---|---|
| Gates, set before the run, and their source | (1) Export error `E3` of channel 3 for each crop: the ONNX file against the TFLite model under the reference interpreter of MediaPipe-Exporter, on the same input tensor. (2) Visibility: `abs(vis_host - vis_upstream) <= 0.25 * E3 + 1e-6` (the sigmoid has a slope of at most 1/4; 1e-6 for the float32 sigmoid of `tensors_to_landmarks_calculator.cc:27`). (3) The gate of the refiner: the decision `visibility > 0.1` of the host equals the decision of Holistic for each wrist, except where `abs(vis_upstream - 0.1) <= 0.25 * E3`. |
| Test images, and the branch that each image runs | The image and video sets of MediaPipe-Exporter decision 0006, with wrists above and below the gate. IMAGE mode, so that no smoothing applies. |
| Upstream reference | `mediapipe` 1.1.1 `PoseLandmarker` (IMAGE mode, lite), landmark `visibility`; the ROI of each frame from the same run. Config: `PoseLandmarkerOptions(running_mode=IMAGE, num_poses=1)` with the lite model. Command: the script of the row "Command" below. Part 1 verifies from source that the heatmap refinement keeps the visibility; the run confirms it. |
| Export error | to run |
| Preprocessed input | to run |
| Row count | to run |
| Final outputs | to run (the visibility of each of the 39 points and the wrist gate decision; no box comparison: the model has the `pose_estimator` role only) |
| Result | to run |
| Script path in the exporter repo | unknown (MediaPipe-Exporter has no git repo; the BlazePose intake (the untracked intake of `mediapipe-pose39` of MediaPipe-Exporter (plan facts)) has parity `to run`, and BlazePose is deferred, user decision T41) |
| Exporter commit of the script | none (no git repo) |
| Command | to write: a script in MediaPipe-Exporter that runs `PoseLandmarker` (IMAGE mode) and the ONNX file on the sets of MediaPipe-Exporter decision 0006, applies `channel_visibility(keypoints, 3, 'sigmoid')` of the reference file, and reports the gates (1) to (3) |

## 6. skellytracker implementation proposal

skellytracker does not build this now. The implementer checks this part.

| Item | Value |
|---|---|
| Module and function | A new module `skellytracker/core/detectors/processing/pose_visibility.py` with `decode_visibility`, `activate` and `channel_visibility` from part 3. The coordinate decode has no code yet (`post/pose-decode-coordinate.md` front matter: `decode: missing`): for the implementer, `channel_visibility` goes into that decoder when it exists. `simcc_decode.py` does not change (option E). |
| Dispatch point | The single-person coordinate decoder (not written yet) returns the visibility as a third value when `PoseDecodeSpec.visibility` is set, and `None` otherwise. `simcc_pose_decode` (`simcc_decode.py:105-139`) does not change: with option E, the SimCC decode gives no visibility, and the RTMW detector (`rtmw_wholebody_detector.py:88-93`) passes no visibility. |
| Validator changes (`model.py`, with rule IDs) | `PoseDecodeSpec` (`skellytracker/core/sidecar/model.py:259-278`) gets `visibility: KeypointsChannelVisibility \| None = None`, with `source`, `channel` and `activation` and no other key (rules `-1` and `-2`). `_check_decode` (lines 266-278) adds the method check and the `is_3d` check of rule `-2`. The `estimator_type` check of `-2` needs `PoseSpec` (lines 281-289). Rule `-3` needs the `keypoints` `OutputSpec` (lines 187-209): a check at `SidecarModel` level. Rule `-4` needs `schema_version`: a check at `SidecarModel` level. No change of the size checks: `V-common.sizes_and_artifacts-3` stays as it is. |
| Tests | The vectors of part 4 (`specs/model-sidecar/vectors/post.pose.visibility.yaml`). Validation tests for rules `-1` to `-4`, with a `simcc_softmax` block (refused by rule `-1`). A test that the package sidecars give no visibility. A golden test for a BlazePose sidecar when the BlazePose intake gives one. |
| Existing code that the change touches | **A name conflict:** the data primitive `Keypoints` has a field `visibility` (`skellytracker/core/data_primitives/keypoints.py:17-19`, "confidence scores 0.0–1.0"). The RTMW detector fills it with the keypoint score and sets it to 0 below the threshold (`rtmw_wholebody_detector.py:103-106`). The spec value `visibility` of this proposal is another value. For the implementer: do not put the spec visibility into `Keypoints.visibility` and do not put the score into a field that the spec calls `visibility` without a decision. A map of named per-point values (the heading "Per-point values") or a rename of the field are two choices. The refiner proposal reads `Keypoints.visibility` as the per-point score today (part 2.8, item 10). |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` (all five sizes) | none (option E, OpenMMLab-Exporter decision 0041). No RTMW size declares `pose.decode.visibility`. The writer `pose_block` (`rtmw/sidecar.py:156-165` at `f3aeb47`, the same at `32ab848`) writes `"decode": {"method": "simcc"}` (`:164`) and no visibility, and it does not change. OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMW sidecar until the RTMW intake is `describes`; this proposal needs no regeneration at that later round. The planned families `rtmpose-halpe26` (`rtmpose-x_8xb256-700e_body8-halpe26-384x288.py`) and `dwpose-wholebody133-ubody` (`rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py`) set no `decode_visibility` (copy B, `sigma=(6., 6.93)` at lines 50 and 46, no flag): none. | none |
| Roboflow-Exporter | none (no pose model) | none | none |
| Ultralytics-Exporter | none (YOLO26-pose is bottom-up with a packed `score`) | none | none |
| Qualcomm-Exporter | none (its landmark wrapper gives `[B, K, 3]` only, `post/pose-schema.md:141`) | none | none |
| MediaPipe-Exporter | The BlazePose pose landmark sidecars (none yet), and the refiner sidecar of the hand ROI refiner | New fields: `pose.decode.visibility: {source: keypoints_channel, channel: 3, activation: sigmoid}` in the BlazePose sidecar; `score_gate.value_default: visibility` in the refiner sidecar (part 2.8; user decision T33). The flat `[1, 195]` output needs a decision (2.4, follow-ups). | The BlazePose decode reads channel 3 and applies the sigmoid. |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-hand`, `rtmpose-face`, `rtmw-wholebody` (all `v2024.09.1019`) | none. They cannot declare the field (rule `-4`). | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change (the coordinate decode with no per-point value) | A host cannot read the BlazePose visibility channel or know its activation. No BlazePose parent can pass the gate of the refiner with the value `visibility`. | Part 1; refiner proposal, part 1 |
| Use the keypoint score as the visibility (the mmpose fallback `keypoints_visible = keypoint_scores`, `topdown.py:157-159`) | BlazePose gives no score at all. For RTMW, the score and the visibility have other scales and other ranks (OpenMMLab-Exporter decision 0041), and a consumer reads `score` by its name. | Part 1; OpenMMLab-Exporter 0041 |
| A new output `semantic` (for example `keypoint_visibility`) | No model in scope has a visibility tensor. BlazePose has the value inside the landmark tensor. A semantic would need an exporter to add a graph branch. | Part 1 (the graphs) |
| Put the visibility into a separate ONNX output (an exporter graph change) | BlazePose already gives it in the landmark tensor. For RTMW (the A1 history), it would change the graph that the exporter exports from the unchanged upstream config (OpenMMLab-Exporter decision 0007), and the fp16 graph gives the value on the float16 grid. | Part 1; `AGENTS.md` section 6 |
| A SimCC source (`simcc_softmax` with `beta` and `sigma`) with a size-level block (A1, user decision T33), and its variants: one field for `beta * sigma`, `sigma` from the input size (`round(sqrt(axis_px / 8), 2)`), one exporter-chosen `sigma` for all sizes, only `sigma` in a size entry, a size-level block for every decode value | Superseded by option E (OpenMMLab-Exporter decision 0041). No RTMW size declares the visibility, so the section needs no SimCC source and no size-level form, and skellytracker 0010 stays as it is. The A1 text gave the reasons between the variants; they no longer apply. | Q1; OpenMMLab-Exporter 0041 |
| Two RTMW families (256x192 and 384x288; the earlier recommendation of Q1 (a)) | Rejected by user decision T33. Two sidecars and two `model_id`s for one model family, only for two codec values. The `model_id` grammar `{family}-{keypoints}[-{training}]` has no input-size token, and both are `cocktail14` models. | Q1 |
| One RTMW sidecar without a visibility (Q1 (b)) | **Chosen (option E, 2026-10-24).** First rejected by user decision T33 (the 384x288 sizes then do not give the upstream `keypoints_visible`, and row K8a stays a gap). OpenMMLab-Exporter decision 0041 measured that the RTMW visibility ranks valid hands worse than the score at every size, saturates at 256x192 and fails the fp16 test at four sizes. Row K8a closes with OpenMMLab-Exporter 0041 as its reason. | Q1; OpenMMLab-Exporter 0041 |
| Enable the visibility for all five RTMW sizes (option A2 of question Qe) | Rule S7 of the study plan fails at every size (OpenMMLab-Exporter decision 0041). | OpenMMLab-Exporter 0041, "S7" |
| Two separate units: one SimCC visibility proposal and one coordinate channel proposal | With option E there is no SimCC source. The consumer (the refiner gate, and a host) needs one named value with one meaning, and the heading "Per-point values" names `score` and `visibility` for every decode in one place. | Plan T26 (2); part 2.3 |
| Remove the key `source` (the block is then `{channel, activation}`) | Proposal choice: keep `source` with one value. A later source can then be added, and the existing blocks do not change. The refiner proposal cites the block with `source`. | Part 2.3, notes |
| Extend skellytracker 0021 (pose outputs beside the landmarks) | skellytracker 0021 covers values for each crop (presence, handedness, world keypoints) with new output semantics. This change is a value for each keypoint with no new output. The two can land in any order. | `0021-landmark-extra-outputs.md:11-26` |
| Extend skellytracker 0024 (SimCC score rule) | skellytracker 0024 changes the one score of SimCC. The visibility is a second value of the coordinate decode. | `0024-simcc-score-rule.md:11-17` |
| A default `activation` (`none`) for `keypoints_channel` | BlazePose needs `sigmoid`; a missing value would give a logit with no error. The refiner proposal and T23 Q4 use required fields with no default for such values. | `tensors_to_landmarks_calculator.proto:60-64` (the MediaPipe default is `NONE`, and the pose graph sets `SIGMOID`) |
| `presence` as a second per-point value now | No consumer in scope reads it. The channel stays unread at `vNEXT` (question Q2). | `tensors_to_landmarks_calculator.cc:176-178` |
| A normative float32 precision | The section states no precision (question Q3). On the vectors of part 4, a float32 form differs from the float64 reference by at most 4.9e-8. | Part 4 |

## Open questions for the user

- **Q1. RTMW: one family or two, and the visibility. Decided: E** (OpenMMLab-Exporter decision 0041,
  2026-10-24; question Qe and rule S7 of the wrist-gate study, which OpenMMLab-Exporter 0041 records). One RTMW sidecar with the
  five sizes and no visibility (the old option (b)). Row K8a records OpenMMLab-Exporter 0041: its verdict is
  `out of scope (0041)` (user decision T36), and `specs/model-sidecar/proposals/omitted-upstream-output/proposal.md`
  covers the guide rule for such a row. The interim decision T33
  (A1: the visibility only in the size entries of `l-384` and `x-384`, with the size-level exception
  and an entry that superseded skellytracker 0010) is replaced. The options of the first text were:
  (a) two RTMW sidecars (256x192 and 384x288); (b) one sidecar without the visibility. Part 8 gives
  why each other option is rejected.
- **Q2. BlazePose presence.** Add `presence` as a second per-point value now (the same
  `keypoints_channel` form), or later. Recommended: later.
- **Q3. Precision.** (a) The section states no precision, and the vectors give tolerances (as T25 (1)).
  (b) float32 is normative (the MediaPipe sigmoid is float32, `tensors_to_landmarks_calculator.cc:27`).
  Recommended: (a).
- **Q4. fp16.** With option E, the question has no RTMW object: no RTMW sidecar declares the
  visibility. OpenMMLab-Exporter decision 0041 also measured the fp16 test of the RTMW visibility (four of the five sizes
  fail). For the record: the scratch investigation of T33 measured a maximum fp16 error of the RTMW
  visibility of about 0.85 in both input sizes (p99 0.11 at 256x192, 0.46 to 0.50 at 384x288), and a
  converter bug (onnxconverter-common 1.16.0, `keep_io_types=True`, a blocked node that writes a graph
  output: that output is declared float16). A BlazePose fp16 gate, if one is needed, is a question for
  the BlazePose intake.
- **Q5. `score_gate.value`. Decided (user decision T33):** the gate value is a runtime input of the
  host or the user, with the sidecar default `score_gate.value_default` (Holistic: `visibility`).
  The refiner proposal holds the field, its rules and its vectors (part 2.8). An RTMW parent uses the
  value `score` at every size (OpenMMLab-Exporter decision 0041).

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. (The untracked intake of `mediapipe-hand-roi` of MediaPipe-Exporter (plan facts)
      links it for row R2 (row line 189) at lines 302, 312 and 332. The untracked intake of `mediapipe-pose39` of
      MediaPipe-Exporter (plan facts) links it for rows K5 and K8a at line 365, and its
      reference-file table names the reference file of part 3 at line 379. The untracked
      intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) names it in row K8a (`:193`) and in the table
      "Proposals and reference files" (`:316`) only to record that it no longer covers K8a; K8a links
      `specs/model-sidecar/proposals/omitted-upstream-output/proposal.md`. Checked on 2026-10-25.)
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. None covers it; skellytracker 0021 and 0024 are near (part 8).
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plan folder of OpenMMLab-Exporter (plan facts).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a (no pixel case)
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. n/a (`to run`)
- [x] No file in skellytracker changed.
- [x] Option E (OpenMMLab-Exporter decision 0041) is applied (2026-10-24): one source `keypoints_channel`; no heading
      "Sizes"; no size-level rule; `V-common.sizes_and_artifacts-3` and skellytracker 0010 unchanged;
      no decision entry; rules `-1` to `-4`; parts 1 to 8 and Q1 to Q5. The vectors were run again:
      31 of 31 (2026-10-25, with `validate-error-mapping-without-source`; before it 30 of 30 with
      `act-error-unknown`; before that 29 of 29; A1: 46 of 46; before T33: 39 of 39).
      Each of the three mutations makes exactly one case fail.

Outside this file: the untracked pose-models plan of OpenMMLab-Exporter (plan facts) cites rules `-1` to `-4` and 30 of 30 (option
E). On 2026-10-25 this file has 31 of 31; the plan row must follow. Row K8a of the RTMW intake (`out of scope (0041)`, user decision T36) no longer cites a rule of
this section. The refiner proposal records that the
edits 11 to 13 of part 2.8 are applied (its lines 14-17 and 4077). This file did not make these
edits.

This proposal has `to run` in part 5. It is ready for a skellytracker session to record. It is not
ready for the user to accept.

## Before acceptance

The user cannot accept this proposal until this work is done.

**Parts**

- [ ] Part 5 (BlazePose parity) is `to run`. MediaPipe-Exporter must write the parity script and
      run it. It must record the export error, the preprocessed input, the row count, the final
      outputs and the result. MediaPipe-Exporter has no git repo, so the script has no commit.
- [ ] Part 5 compares only the visibility and the wrist gate decision. It must also compare the
      keypoints in source-image coordinates, or give the reason that it does not.
- [ ] The header row "Model, and its intake file" says "BlazePose has no intake yet". The header row
      "Intake rows" cites the BlazePose intake `mediapipe-pose39` of MediaPipe-Exporter. The two
      rows must agree.
- [ ] The part 2.1 row `notes/decisions/` says "No new entry". This proposal has the decision entry
      0039. Acceptance also needs a scope entry for BlazePose (see **Decisions for the user**). The
      row must be correct.
- [ ] The part 2.1 row `post.pose.decode.simcc` cites "skellytracker decision 0028, item 4" for the
      permalink rule. Decision 0032 supersedes 0028. The row must cite 0032.
- [ ] The header says that OpenMMLab-Exporter commit `f3aeb47` is "not pushed". The commit is now on
      `origin/main` of OpenMMLab-Exporter. The header must be correct.

**Evidence**

- [ ] The BlazePose graph facts of part 1 (the output `Identity` `[1, 195]`, no `Sigmoid` after the
      `Conv`, the node counts and the SHA-256 values) come from a script that no repo holds and from
      the model cache of an exporter with no git repo. They are not evidence. Commit the script in an
      exporter repo, or mark the facts as unverified.
- [ ] Each MediaPipe line of part 1 is at MediaPipe commit
      `e9794ef55e2509c09aa8b6ba1764b797db8eb200`. Make sure that this commit is on the default branch
      of `google/mediapipe`. Then cite the lines with permalinks.
- [ ] The mmpose v1.3.2 lines of part 1 come from local copies. The author cannot check their origin
      again. They support only the RTMW record. Cite them with permalinks at the mmpose commit
      `5408bc76f5b848cf925a0d1857899011d8c5b497` (the commit that
      `mmdeploy-convert/Dockerfile.exporter:44` of OpenMMLab-Exporter checks), or mark them as
      unverified.
- [ ] The lines of `docs/mediapipe-whole-body.md` of MediaPipe-Exporter are secondary evidence. They
      have no permalink, because MediaPipe-Exporter has no git repo.

**Template checklist**

- [ ] The item "The header gives the dependencies" is ticked with `none`. The only consumer of the
      change is BlazePose, a MediaPipe-Exporter model. Decision 0008 does not put MediaPipe-Exporter
      in the `vNEXT` scope. The header must name the scope entry that the change needs.
- [ ] The item "Part 2.1 lists each place that the change edits" is only partly true. Part 2.1 gives
      the edits of `tools/make_vectors.py` and `tools/tests/test_vectors.py` only by a reference to
      the proposal `simcc-score-rule`. Part 2.1 must list them. Part 2.1 also does not list the
      item of `notes/decisions/open-work.md` that part 6 needs after acceptance: the coordinate
      decode, `PoseDecodeSpec.visibility` and the name conflict of `Keypoints.visibility`.

**Vectors and tooling**

- [ ] The YAML of part 4 does not have the form of the skellytracker vector tooling.
      `tools/tests/test_vectors.py` needs `generated_by: tools/make_vectors.py`. It has no `function`
      key and no `compare` key. It uses a scalar `tolerance` key, and a case must have `tolerance`
      exactly when its `expect` has a fraction. `tools/make_vectors.py` rounds each `expect` to 6
      digits. The tooling has no form for an error case, and 17 of the 31 cases expect an error.
      Decide the case form one time for all proposals that add vectors.
- [ ] The builder in `tools/make_vectors.py` must call the reference implementation
      `specs/model-sidecar/reference/post_pose_visibility.py`. It must not keep a second form of the
      formulas. A new test in `tools/tests/` must run the reference functions against the vectors.
- [ ] Rule `V-post.pose.visibility-4` also refuses the field in a size entry. `validate_visibility`
      of part 3 has no input for a size entry, and no case covers a size entry. Add the input and
      the cases: a legacy size entry, and a `vNEXT` size entry that `V-common.sizes_and_artifacts-3`
      refuses.
- [ ] The docstring of the part 3 code says "Each function implements one step of part 2.3".
      `validate_visibility` implements part 2.4. The docstring also pins old commits. Correct the
      sentence and pin the file again when it lands.
- [ ] `post_pose_visibility.py` is the first file in `specs/model-sidecar/reference/`. Then
      `.github/workflows/lint.yml` runs `ruff` on that folder. Run `uv run ruff check` on the file
      before the push.
- [ ] Part 2.1 says "Run `python tools/sidecar_trace.py matrix`". Use `uv run` (`AGENTS.md`,
      section 3). Before the push, run `uv run python tools/make_vectors.py --check` and
      `uv run python tools/sidecar_trace.py matrix --check`.
- [ ] The section file needs the heading "Implementer guidance" (from part 6) and the heading
      "Authoring guidance". Keep "Inverse: none" as a sentence, not as a heading. A postprocessor
      has no inverse step.

**Decisions for the user**

- [ ] The `vNEXT` scope. Decision 0008 does not put MediaPipe-Exporter in the `vNEXT` scope. The
      proposed scope entry 0048 (`vnext-scope-mediapipe-rotated-crops`) adds only the hand landmark
      model and the hand ROI refinement model. After 0042 and 0048, BlazePose is still out of scope.
      Choose one: a third scope entry, a change to 0048, or no `vNEXT` change for this proposal. The
      paragraph "For reviewers" of `specs/model-sidecar/changelog.md` names only Roboflow-Exporter,
      OpenMMLab-Exporter and Ultralytics-Exporter. A scope change must also change that paragraph.
- [ ] Decide if this proposal lands in `vNEXT`. BlazePose is deferred (exporter-plan user decision
      T41). Its intake has many `gap` rows, no verdict and no parity. Decide also if MediaPipe-Exporter
      must own the proposal. The parity of part 5 is a task of MediaPipe-Exporter.
- [ ] The flat output. The BlazePose graph gives `[1, 195]`, not `[1, 39, 5]`. Accept that a
      BlazePose sidecar needs a `Reshape` in the exported graph, or ask for a proposal for a flat
      `(N, K * C)` layout first.
- [ ] Q2: add the BlazePose presence (channel 4) now or later. The proposal recommends later.
- [ ] Q3: (a) the section states no precision and the vectors give tolerances, or (b) float32 is
      normative. The proposal recommends (a).
- [ ] Rule `V-post.pose.visibility-2` refuses only `bottom_up`. Thus it accepts
      `top_down_multi_person`, but its error message says "a single-person estimator_type". Decide
      if `top_down_multi_person` is allowed.
- [ ] Rule `V-post.pose.visibility-3` reads the last dimension `C` only from the `shape` of the
      `keypoints` output. A sidecar can give a concrete shape in
      `sizes.<size>.onnx.batch_artifacts.<N>.output_shapes`. Decide if the rule also reads that
      place.
- [ ] One contract unit. The change makes the single-person `keypoints` output `(N, K, C)`. That
      answers the BlazePose row K5 (`near-miss`), not the visibility. Decide if that part stays in
      this proposal or becomes a separate proposal.
- [ ] The rule owner. The normative heading "Per-point values" of `post.pose.visibility` states
      facts about the SimCC, bottom-up and heatmap scores. Decide if `post.pose.visibility` or
      `post.pose.schema` owns that heading (decision 0013).
- [ ] The legacy policy. Rule `-4` refuses `pose.decode.visibility` below `vNEXT`. Other proposals
      use only the legacy row or an error at decode. Decide one policy for all fields that are new in
      `vNEXT`.
- [ ] The decision entry waits on MediaPipe-Exporter: BlazePose and the refiner proposal. A
      `**Depends on:**` line needs a permalink, and MediaPipe-Exporter has no git repo. Decide how to
      write that line.
- [ ] Accept the exporter-plan user decisions that the proposal cites as plan facts: T26 (2), T33,
      T34, T36, T37, T41, T25 (1) and T23 (A3, option 1). Accept OpenMMLab-Exporter 0041 (status
      `evidence`) as the basis of option E.
- [ ] The PR split. Decide if the guidance edits go in the content PR or in a later non-spec PR:
      the `decode_visibility` bullet of `post/pose-decode-simcc.md`, the "Authoring guidance" of
      `post/pose-decode-coordinate.md`, the "Implementer guidance" of `post/pose-schema.md`, the
      mapping hint and the intake template row K8a.

**Merge points**

- [ ] This proposal must land before `roi-refiner-role` (0047). The normative text of that proposal
      uses the heading "Per-point values" and the default `value_default: visibility`.
- [ ] `post/pose-decode-coordinate.md:33` (the single-person form). `landmark-depth-divisor` (0022)
      changes a phrase of the old text, and its reference code and vectors accept only `(N, K, 2)`
      and `(N, K, 3)`. `landmark-extra-outputs` (0021) adds a sentence. If `(N, K, C)` is normative,
      the code and the vectors of `landmark-depth-divisor` must follow it.
- [ ] `post/pose-decode-simcc.md:58` (the `decode_visibility` bullet of "Authoring guidance"). This
      proposal replaces a sentence. `simcc-score-rule` (0024) adds a bullet. `omitted-upstream-output`
      (0044) can name the verdict `omitted` there. The three texts must agree.
- [ ] `simcc-score-rule` and `pose-decode-flip-test` (0045) still name this proposal as a merge point
      at `post/pose-decode-simcc.md:38`. Option E removed that edit. `heatmap-decode-refinement`
      (0038) does not name the merge point at the heading "Per-point values". The exporter sessions
      must correct those proposals.
- [ ] The mapping hint "Pose" of `specs/exporter-guide/sidecars/workflow/mapping-hints.md`.
      `omitted-upstream-output` (place G8) appends text to the sentence of this proposal. Thus this
      proposal lands first. `landmark-extra-outputs` and `nms-clamp-order` (0040) also change that
      heading.
- [ ] Other shared places: the legacy row of `format/versioning.md:74` (0038, 0045, 0020, 0047,
      0021, 0022), the `pose.decode` fields table and the "Shape key" of `post/pose-schema.md`
      (0038, 0045, 0022, 0024), the validation rules and the "See also" line of `post/pose-schema.md`
      (0020, 0021, 0022, 0045), the section map and the validation index of `specs/model-sidecar/README.md`
      (0045, 0021), and row K8 of `templates/model-intake.md` (0021). The PR that lands second keeps
      the edits of both.
