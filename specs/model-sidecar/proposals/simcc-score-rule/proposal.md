---
slug: simcc-score-rule
section: post.pose.decode.simcc
exporter: OpenMMLab-Exporter
decision: "0024"
state: recorded
---

# Change proposal: simcc-score-rule

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `simcc-score-rule`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. The `python` code block at the end of part 3 is the reference file of the proposal, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`. It builds on the skellytracker gap record 0024 and gives the parts that skellytracker 0024
does not have.

## Header

| Field | Value |
|---|---|
| Title | SimCC keypoint score rule, the location of a keypoint with a score `<= 0`, and the `simcc_z` depth |
| Slug | `simcc-score-rule` (the slug of skellytracker decision 0024) |
| Date | 2026-10-23 (checked again 2026-10-24; updated 2026-10-25: the pin is skellytracker `dom/21-move-sidecar-guide`, and the mmdeploy evidence of part 1 is primary) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed: OpenMMLab-Exporter decision 0050; OpenMMLab-Exporter decision 0042 is commit `1dfec48`; `git status --porcelain` is empty; first written at `cce619d`, checked at `d0f4343`). The exporter lines that this proposal cites were checked again at `f3aeb47` on 2026-10-24. The lines of `rtmw/sidecar.py` move by +2 from `d0f4343` (OpenMMLab-Exporter decision 0042), and this file cites the line at `f3aeb47`. `rtmw/adapter.py:136` of the earlier check is now `:137` (OpenMMLab-Exporter decision 0050 adds one docstring line), with the same text. `rtmw/contract.py`, `mmdeploy-convert/*` and `notes/decisions/migration-decisions.md` are the same as at `d0f4343`. |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)). The RTMPose Halpe26 family `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)). Its `model_id` is `rtmpose-halpe26` (plan T14: one `halpe26` model, so no training token; `specs/model-sidecar/proposals/model-id-suffix/proposal.md` 2.3). The current family `rtmw-wholebody133` has the same property (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), row K8, line 192, `near-miss`). Its `vNEXT` sidecar writer writes `pose.decode: {method: simcc}` (`rtmw/sidecar.py:164` at `f3aeb47`, the same at `1dfec48`; line 162 at `d0f4343`). OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMW sidecar until the RTMW intake is `describes`; the writer stays. |
| Intake rows with the verdict `near-miss` or `gap` | Row K8 (keypoint score, `near-miss`) of the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts) (line 137), of the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts) (line 157) and of the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (line 192). |
| Kind (`new section` or `changed section`) | `changed section` |
| Proposed section ID (the `id` in the section file's front matter) | `post.pose.decode.simcc` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/post/pose-decode-simcc.md` |
| Depends on (proposal files that must land first, or `none`) | none |
| Needed by (proposal files that depend on this one, or `none`) | none. `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` adds one sentence to the same "Behaviour" heading (the host decodes the averaged outputs of the flip test). The two edits do not conflict. They can land in either order. With the flip test, the score of this proposal comes from the averaged outputs. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit` (checked 2026-10-24). From `dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`, no file of this list changed. From `dom/18-agents-adr-bootstrap-kit` to `dom/21-move-sidecar-guide`, no file of this list changed (checked 2026-10-25), so the same lines hold at `dom/21-move-sidecar-guide`. `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `heatmap-decode-refinement`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`, `roi-transform-and-source` (MediaPipe-Exporter); `post/pose-schema.md:108-110` ("Shape key"): `heatmap-decode-refinement`; `post/pose-decode-simcc.md:38` (the "Behaviour" bullet: one proposal replaces it, two add a sentence): `pose-decode-flip-test`, `keypoint-visibility`; `post/pose-decode-simcc.md` "Authoring guidance" (the `decode_visibility` bullet at `:58`): `keypoint-visibility`; `changelog.md:55-59` ("Compatibility impact"): `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | skellytracker decision 0024 "SimCC keypoint score rule" (`notes/decisions/0024-simcc-score-rule.md`, a gap record). This proposal uses its slug and builds on it. It does not compete with it. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `dom/21-move-sidecar-guide` (checked 2026-10-25; `git status --porcelain` lists only `grep.exe.stackdump`, an untracked crash dump, not a file that this proposal read). First read at `dom/12-single-working-branch`, then at `dom/18-agents-adr-bootstrap-kit`. `git log dom/18-agents-adr-bootstrap-kit..dom/21-move-sidecar-guide` has four commits (skellytracker 0032, 0033 and 0034). Of the files that this proposal cites, four changed and no cited line moved: `specs/model-sidecar/templates/change-proposal.md` (line 7 only: the guide path of the skellytracker 0034 layout), `specs/model-sidecar/TRACEABILITY.md` (lines 107-108 of the inventory table; line 90 is the same), `notes/decisions/open-work.md` (lines 102 and 115-119, below the cited line 97, which is the same) and `.claude/skills/propose-sidecar-change/SKILL.md` (its links point to the skellytracker 0034 layout; item 12 cites skellytracker 0032 in place of skellytracker 0028; no rule text changed). `notes/decisions/README.md` (the index, not cited in this file) also changed; its skellytracker 0024 row is line 43. `notes/decisions/0024-simcc-score-rule.md`, the cited `specs/model-sidecar/` section files, `changelog.md`, `tools/` and `skellytracker/` files did not change. Guide citations point to the skellytracker 0034 layout (`specs/exporter-guide/sidecars/`) at skellytracker `dom/21-move-sidecar-guide`. The cited `specs/`, `tools/` and `skellytracker/` lines were checked again at `dom/18-agents-adr-bootstrap-kit` on 2026-10-24: none of these files changed (the template `templates/change-proposal.md` changed one line, and its lines 251-260 have the same text). The cited "Open work" line moved to `notes/decisions/open-work.md` (part 6). |

**What this proposal adds to skellytracker 0024.** skellytracker 0024 gives the min rule on the raw outputs and the direction of
the change. It says that the full proposal must give the rule for `simcc_z` when `is_3d: true`, the
`vNEXT` and legacy rows, the reference implementation and the vectors. This proposal gives these
parts. It also adds three items that skellytracker 0024 does not have:

- the rule for a score `<= 0` (`locs[vals <= 0.] = -1`, `post_processing.py:99`);
- the tie order of the argmax (the lowest bin);
- the exact bin-to-depth formula of `simcc_z` (`b / Z_bins`, not `b / (Z_bins - 1)`).

The change of skellytracker 0024 does not change. Part 8 gives the reasons for the three additions.

## 1. Gap

| Item | Value |
|---|---|
| Property | The SimCC decode of the mmpose models. (1) The location of each axis is the argmax bin of the raw output. A tie selects the lowest bin. (2) The keypoint score is the smaller of the two raw peaks of `simcc_x` and `simcc_y`. No softmax comes first. (3) When the score is `<= 0`, every axis of the keypoint gets the bin -1. (4) The bin-to-pixel scale is `1 / simcc_split_ratio`, with no half-bin offset. (5) 3D (RTMW3D): the `z` bin is the argmax of `simcc_z`. The peak of `simcc_z` does not change the score. The -1 rule also sets the `z` bin. The depth is `(z_bin / simcc_split_ratio / (D / 2) - 1) * z_range`, thus `b / Z_bins` on the range `[-z_range, z_range]`. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **mmpose v1.3.2** (the tag of the exporter image: `mmpose==1.3.2`, repo clone at commit `5408bc76f5b848cf925a0d1857899011d8c5b497`, `mmdeploy-convert/Dockerfile.exporter:34, 42-44`). **2D:** `mmpose/codecs/utils/post_processing.py:41-105` (`get_simcc_maximum`): `apply_softmax: bool = False` (line 43); the softmax runs only when it is requested (lines 83-88); `np.argmax` on each axis (lines 90-92); `np.amax` (lines 93-94); `mask = max_val_x > max_val_y; max_val_x[mask] = max_val_y[mask]` (lines 96-98, the min); `locs[vals <= 0.] = -1` (line 99, on the bins, before the scale). `mmpose/codecs/simcc_label.py:174` (`get_simcc_maximum(simcc_x, simcc_y)`, no softmax) and `:191` (`keypoints /= self.simcc_split_ratio`). `simcc_label.py:193-198`: `decode_visibility=True` applies a softmax only for a second value (the visibility). `mmpose/models/heads/base_head.py:81-86, 91-93`: the first value stays `keypoint_scores`, the second becomes `keypoints_visible`. The encode maps pixel `p` to bin `around(p * simcc_split_ratio)` (`simcc_label.py:202-210`), thus bin `b` stands for pixel `b / simcc_split_ratio`. **Configs** (all `SimCCLabel`, `simcc_split_ratio=2.0`, `normalize=False`, `use_dark=False`): Halpe26 `configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py:48-53`; DWPose `configs/wholebody_2d_keypoint/rtmpose/ubody/rtmpose-m_8xb64-270e_coco-ubody-wholebody-256x192.py:44-49`; RTMW `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py:48-53` and `rtmw-x_8xb320-270e_cocktail14-384x288.py:49-55` (also `decode_visibility=True`). **3D (RTMW3D):** `projects/rtmpose3d/rtmpose3d/utils.py:6-76` (`get_simcc_maximum(simcc_x, simcc_y, simcc_z)`): `z_locs = np.argmax(simcc_z)` (line 62); the min uses only `max_val_x` and `max_val_y` (lines 64-69); `locs[vals <= 0.] = -1` sets x, y and z (line 70). `projects/rtmpose3d/rtmpose3d/simcc_3d_label.py:187` (`keypoints /= self.simcc_split_ratio`, also z) and `:191-192` (`(keypoints_z / (self.input_size[-1] / 2) - 1) * self.z_range`); `z_range` default `2.1744869` (line 100); the encode is root-relative (lines 114-117). `projects/rtmpose3d/configs/rtmw3d-l_8xb64_cocktail14-384x288.py:49-56` (`SimCC3DLabel`, `input_size=(288, 384, 288)`, `simcc_split_ratio=2.0`, no `z_range`). The exporter image has the `projects/` folder in its repo clone (`Dockerfile.exporter:43`). **Other hosts:** rtmlib `rtmlib/tools/pose_estimation/post_processings.py:39-42` at `9f51b34` (the min is commented out; `vals = 0.5 * (max_val_x + max_val_y)`; the same -1 rule). skellytracker `skellytracker/core/detectors/processing/simcc_decode.py:28-69` (softmax on each axis at lines 53-54, `0.5 * (max_px + max_py)` at line 63, `locs[vals <= 0.0] = -1` at line 64; a softmax peak is `> 0`, so line 64 never applies). mmdeploy `bc75c9d6` `mmdeploy/codebase/mmpose/codecs/post_processing.py:5-33` (`get_simcc_maximum`, read in the local checkout `../mmdeploy` on 2026-10-25): line 30 takes the min of the two raw maxima (`torch.cat([max_val_x, max_val_y], dim=1).min(dim=1)`); the function has no `-1` rule (no line sets `locs` to -1). It is the export-time rewrite of `SimCCHead.forward` and `RTMCCHead.forward` (`mmdeploy/codebase/mmpose/models/heads/simcc_head.py:7-8, 20-28`), used only when the codebase config sets `export_postprocess: True`; the default returns the raw `simcc_x` and `simcc_y`, as the graphs of this exporter do. |
| Nearest section ID (the `id` in the section file's front matter) | `post.pose.decode.simcc` |
| Why the nearest section is wrong | The section says "The location of each keypoint is the argmax bin. Its score is the max value." (`post/pose-decode-simcc.md:38`). (1) SimCC has two peaks for each keypoint. The text does not say how they combine, or if a softmax comes first. Three hosts use three rules (skellytracker 0024). (2) The text has no rule for a score `<= 0`. (3) It does not give the tie order of the argmax. (4) "the `z` axis maps `Z_bins` linearly onto `depth_range`" does not say if bin `b` maps with `b / Z_bins` or `b / (Z_bins - 1)`. It does not say if the `simcc_z` peak changes the score or the -1 rule. A host that follows the current text cannot reproduce the upstream keypoint scores. A keypoint threshold does not transfer from one host to another. |
| Measured difference (number, image and script) | COCO val2017, all 6352 non-crowd GT person instances with keypoints, GT boxes, flip test off, ONNX Runtime CUDA, the mmpose SDK `end2end.onnx` graphs of DWPose-m (`rtmpose-m_simcc-ucoco_dw-ucoco_270e-256x192-c8b76419_20230728`), RTMPose-m Halpe26 (`rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605`) and RTMW-m (`rtmw-dw-l-m_simcc-cocktail14_270e-256x192_20231122`). Body OKS AP on the first 17 keypoints. The instance score is the mean of the body keypoint scores `> 0.2`, as mmpose `CocoMetric` does with `score_mode='bbox_keypoint'` and the default `keypoint_score_thr=0.2` (`mmpose/evaluation/metrics/coco_metric.py:101, 465-475`). **Min of the raw peaks (mmpose):** AP 0.7216 (DWPose-m), 0.7647 (Halpe26-m), 0.7477 (RTMW-m). **Mean of the raw peaks (rtmlib):** 0.7199, 0.7635, 0.7462. **Mean of the softmax peaks (skellytracker today):** 0.6239, 0.6809, 0.6559. AR is the same for the three rules within 0.0001, because the locations are the same argmax. The AP loss of the softmax rule comes from the threshold: its score has p5 / p50 / p95 of 0.0027 to 0.0028 / 0.0045 to 0.0048 / 0.0059 to 0.0063, so no keypoint passes 0.2. The min score has p50 0.59 to 0.69 and p95 0.95 to 1.05 (a raw score can be above 1). The skellytracker threshold `confidence_threshold: 0.004` removes 32 % to 38 % of the keypoints with the softmax score, and none with the min score. **The -1 rule** applied to 3 of 165152 Halpe26-m keypoints (raw `x` peaks -0.0043 to -0.0000): image 67315, annotation 2205356, keypoints 13 and 15; image 108026, annotation 458854, keypoint 16. Both boxes cover most of the image. It applied to no DWPose-m or RTMW-m keypoint. **Ties:** the Halpe26-m outputs have an argmax tie in 6 `simcc_x` rows and 4 `simcc_y` rows. The score came from `simcc_x` for 121557 keypoints and from `simcc_y` for 43595. Scratch scripts `simcc_score_rules.py` and `simcc_low_score_ids.py` (not committed, so not evidence). They run no upstream code: the crop is an own copy of the rotation-0 warp, and the decode is the reference file of part 3. Check: the min-rule AP of DWPose-m and Halpe26-m agrees within 0.0009 with the flip-test run that used the mmpose crop functions (0.7207 and 0.7648, `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` part 1). Secondary: a host with the min rule matched mmpose with a maximum score difference of 0.0033 (the untracked hand-models plan of OpenMMLab-Exporter (plan facts) part 3.3, row "Pose: score `min(max_x, max_y)` of the raw outputs"). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The row `score_activation: softmax` (`changelog.md:46`) is about detection scores, not about the SimCC keypoint score. |

All the evidence of rows (1) to (5) is primary (upstream file and line). The rtmlib lines and the mmdeploy lines are primary (local checkouts `../rtmlib` at `9f51b34` and
`../mmdeploy` at `bc75c9d6`, read on 2026-10-25).

Missing primary evidence: the unit of the RTMW3D depth. The upstream files that this proposal read
give no unit: `simcc_3d_label.py` gives only `z_range` (line 100, default `2.1744869`) and the
root-relative encode (lines 114-117); `utils.py`, the RTMW3D config and `projects/rtmpose3d/README.md`
also give no unit. The only source is the spec (`specs/model-sidecar/post/pose-schema.md:93`, "`m`
(RTMW3D)", secondary). The authoring guidance of 2.1 cites that line. This proposal does not change
`depth_unit`. The rule of this proposal does not need the unit: the depth formula maps bins onto
`depth_range` in `depth_unit`, whatever the unit is. A future RTMW3D intake must find the primary
source (for example the depth unit of the 3D training annotations).

## 2. Spec change

### 2.1 Sections

Changed section `post.pose.decode.simcc`, title "SimCC decode", file
`specs/model-sidecar/post/pose-decode-simcc.md`. The section ID, the title, the kind and the selectors do
not change.

Changed front matter (the other keys do not change):

```yaml
changed_in: [vNEXT]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode
  decode: skellytracker/core/detectors/processing/simcc_decode.py::simcc_pose_decode  # partial: no 3D (it raises); the split ratio is fixed at 2.0, not read from the bin counts; the score is the legacy rule (the mean of the two softmax peaks) for every schema_version
vectors: vectors/post.pose.decode.simcc.yaml
status: {spec: stable, validate: implemented, decode: partial}
```

The spec state stays `stable`, as for `pre.normalize`, which also has `changed_in: [vNEXT]` and a
legacy row (`pre/normalization.md:6, 20`). `proposed` is the status of a decision entry, not a spec
state (`tools/tests/test_traceability.py:47`).

No row in the section map changes: the section exists (`specs/model-sidecar/README.md:91`).

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `post.pose.decode.simcc` (`post/pose-decode-simcc.md`) | front matter | The edit above. |
| `post.pose.decode.simcc` | "Fields" | Change the description of `pose.decode.depth_range` (2.2). |
| `post.pose.decode.simcc` | "Behaviour" | Replace the bullet at line 38 with the text of 2.3. Keep the line "Shape key (`pose-schema.md#shape-key`)". |
| `post.pose.decode.simcc` | "Legacy behaviour" (new heading, after "Validation rules", as `pre/normalization.md:110`) | Add the table of 2.6. |
| `post.pose.decode.simcc` | "Implementer guidance" | Replace the first bullet (line 52, "The spec says that the SimCC score is the max value. ...") with: "skellytracker implements only the legacy score (the mean of the two softmax peaks), also for a `vNEXT` sidecar. The detectors drop a keypoint below `confidence_threshold: 0.004`. That value fits only the legacy score: the `vNEXT` score is a raw value, and it has no fixed range. skellytracker decision 0024 records the rule." Keep the fp16 bullet (line 53). |
| `post.pose.decode.simcc` | "Authoring guidance" | Add: "RTMPose Halpe26 and DWPose: the configs set the same codec as RTMW (`SimCCLabel`, `simcc_split_ratio=2.0`, `normalize=False`, `use_dark=False`). `decode_visibility=True` (the two 384x288 RTMW configs) does not change the keypoint score: the head keeps the first value as `keypoint_scores` (mmpose v1.3.2 `mmpose/models/heads/base_head.py:81-86`). RTMW3D: `depth_range: [-2.1744869, 2.1744869]` (`SimCC3DLabel` `z_range` default, `projects/rtmpose3d/rtmpose3d/simcc_3d_label.py:100`; the config sets no `z_range`). `depth_unit: m` (the value that `post/pose-schema.md:93` gives for RTMW3D; no upstream file gives the unit)." The `depth_unit` value has secondary evidence only (part 1, "Missing primary evidence"). |
| `post.pose.schema` (`post/pose-schema.md`) | "Shape key" (lines 109-110) | No change of meaning. Add "The decode of the bins is in SimCC decode (`pose-decode-simcc.md#behaviour`)." after the `Z_bins` bullet, so that the exact formulas have one place. |
| `format.versioning` (`format/versioning.md`) | "Version-aware compatibility" (the list at lines 53-63) | Add the link `- [SimCC decode](../post/pose-decode-simcc.md#legacy-behaviour)` before "Bottom-up pose". |
| `format.versioning` | "Legacy behaviour" (lines 72-74) | No edit. That table gives the availability of new fields. This change adds no field. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" | Add the summary row of 2.7. |
| `specs/model-sidecar/changelog.md` | "`schema_version` history" | Append the sentence of 2.7 to the end of the existing `vNEXT` row (`changelog.md:68`). Do not add a second `vNEXT` row. |
| `specs/model-sidecar/changelog.md` | "Compatibility impact" (lines 55-59) | Add the bullet of 2.7. |
| `specs/model-sidecar/vectors/post.pose.decode.simcc.yaml` | new file | The vectors of part 4, in the form of `tools/make_vectors.py` (see the two rows below and part 4). Do not copy the part 4 YAML by hand: `tools/tests/test_vectors.py:110-111` requires that every file in `specs/model-sidecar/vectors/` comes from `make_vectors.py::generate`, and `:115-116` requires that the file text equals the generator output. |
| `tools/make_vectors.py` | `BUILDERS` (line 2411) | Add a builder `build_simcc_decode` for `post.pose.decode.simcc`, so that the generator writes the file. The file then has `generated_by: tools/make_vectors.py` (`GENERATED_BY`, line 38; checked at `test_vectors.py:141`). The generator rounds `expect` to 6 decimals (`ROUND_DIGITS`, line 62), and it writes one file tolerance on each case with a fractional number (`Case.data`, lines 124-134). Thus the file tolerance must be at least `1e-6`: it must cover the rounding (up to 5e-7) and the float32 form of the upstream depth (up to 1.9e-7, part 4). A new key in `TOLERANCE` (line 65) gives the value. The legacy cases can list `verified_against: [skellytracker/core/detectors/processing/simcc_decode.py::get_simcc_maximum]`, with a test that runs that function (as the tests at `test_vectors.py:755-789` do for the resize functions). |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (lines 32-40); "Hand-computed anchors" | The part 4 cases have a `function` key and a `compare` key. `CASE_KEYS` has neither, so `test_cases_have_the_documented_shape` (lines 169-180) fails on them. It also requires a `tolerance` key on each case with a fractional `expect` (line 180), for example `score-x-smaller` (0.4). For the skellytracker session, one of two: (a) add `function` to `CASE_KEYS` (and to `Case` in `make_vectors.py`), and convert each `compare: {<field>: {atol: <n>}}` to the case `tolerance`; or (b) keep `CASE_KEYS`, drop the `function` key, let the prefix of the case `id` select the function (the part 4 ids already have one prefix for each function: `peak-`, `score-`, `low-score-`, `pixel-`, `depth-`, `legacy-score-`, `decode-`), and convert `compare` in the same way. Optional: add a `test_simcc_decode_anchors` with hand values from the section text, as the other sections have (lines 193-401). After the change, `tools/tests/test_vectors.py` must pass, as `test_traceability.py` must. |
| `specs/model-sidecar/reference/post_pose_decode_simcc.py` | new file | The reference file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated matrix | Do not edit it by hand. After the section file changes, run `python tools/sidecar_trace.py matrix`. The status row of `post.pose.decode.simcc` then names the vector file (it says "none" at `TRACEABILITY.md:90`). `tools/tests/test_traceability.py::test_traceability_equals_a_fresh_generation` must pass. |
| `tools/sidecar_trace.py` | matrix cell text | Optional, for the skellytracker session: a `(legacy)` flag in the `post.pose.decode.simcc` cells of the legacy sidecars, as `tools/sidecar_trace.py:510-511` does for `imagenet_bgr`. If it is added, `EXPECTED_CELLS` of `tools/tests/test_traceability.py` changes too. |
| `specs/model-sidecar/README.md` | Section map; "Validation rules" (the validation index) | No edit. The section row and its rules link exist (`README.md:91, 119`). |
| `specs/model-sidecar/sidecar-spec.md` | The permanent index | No edit. The index keeps the old headings only (skellytracker decision 0013). |
| `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` | example | No edit. The example is `vNEXT` (line 2) with `method: simcc` (line 46). Its meaning changes: the score is the min rule. |
| `post.unprojection`, `pre.resize.affine_person_crop`, `common.outputs`, `common.identity`, `format.file_layout` | | No edit. The decode output stays in the model-input pixels of the crop. A keypoint at bin -1 goes through the same unprojection. The change adds no output semantic, no role and no path. |

### 2.2 Fields table

No new field. The description of the existing field changes:

| Field | Type | Required | Description |
|---|---|---|---|
| `pose.decode.depth_range` | array[2] | required when `is_3d: true` and `method: simcc` | The `[min, max]` root-relative depth (in `depth_unit`) that `Z_bins` span. Bin `b` of `simcc_z` maps to `min + b * (max - min) / Z_bins` (see Behaviour (`#behaviour`)). |

### 2.3 Behaviour

Replace the bullet of the heading "Behaviour" with this text:

- `simcc` — one `simcc_x` `(N, K, X_bins)` output and one `simcc_y` `(N, K, Y_bins)` output. When `is_3d: true`, there is also a `simcc_z` `(N, K, Z_bins)` output. The host reads the bin counts from the output tensors. For each crop `n` and each keypoint `k`, the host does the steps below. The steps use the raw output values. The host does not apply a softmax.

```text
bin_x  = argmax over b of simcc_x[n, k, b]      (on a tie, the lowest b)
bin_y  = argmax over b of simcc_y[n, k, b]      (on a tie, the lowest b)
peak_x = simcc_x[n, k, bin_x]
peak_y = simcc_y[n, k, bin_y]
score  = peak_y   when peak_x > peak_y
         peak_x   otherwise                     (thus min(peak_x, peak_y))
when is_3d: true:
    bin_z = argmax over b of simcc_z[n, k, b]   (on a tie, the lowest b)
when score <= 0:
    bin_x = -1, bin_y = -1, and bin_z = -1 when is_3d: true
x = bin_x * input_width / X_bins
y = bin_y * input_height / Y_bins
z = depth_range[0] + bin_z * (depth_range[1] - depth_range[0]) / Z_bins     (is_3d: true)
```

- The score is a raw output value. It has no fixed range: it can be negative, and it can be above 1. The host compares `score <= 0` in the dtype of the outputs.
- The peak of `simcc_z` does not change the score or the -1 rule.
- A keypoint with `score <= 0` keeps its place in the output. Its location is bin -1 on each axis. The host unprojects it like every other keypoint.
- `x` and `y` are in the model-input pixels of the crop (cropped image space). The host unprojects them to the source image (see Unprojection (`unprojection.md`)). `z` is the root-relative depth in `depth_unit`. The unprojection does not change `z`.
- The reference arithmetic is float64. A host can use float32. When `X_bins = 2 * input_width` and `Y_bins = 2 * input_height`, `x` and `y` are the same in float32 and float64. `z` can then differ by one float32 rounding step.
- `schema_version < vNEXT`: the score has the legacy rule (see Legacy behaviour (`#legacy-behaviour`)). The other steps do not change.

**Inverse.** None. The decode maps bins to crop pixels. No step of the contract maps pixels back to
bins. The inverse of the crop is `post.unprojection`.

### 2.4 Validation rules

No new rule. The score rule, the -1 rule and the bin formulas are decode behaviour. They have no field
that a validator can check.

Existing rules that name a value of this change:

- `V-post.pose.decode.simcc-1` (`depth_range` with `is_3d: true`): unchanged. It already requires the
  field that the `z` formula uses.
- `V-post.pose.schema-7` (`simcc_z` if and only if `is_3d: true`): unchanged.
- `V-post.pose.schema-9` (`depth_unit`, `depth_range` only with `is_3d: true`): unchanged.

Follow-up, not in this proposal: a rule `depth_range[0] < depth_range[1]`. No model in scope needs it.

### 2.5 Selectors

Unchanged: `pose.decode.method=simcc`, `outputs[].semantic=simcc_x`, `outputs[].semantic=simcc_y`,
`outputs[].semantic=simcc_z`.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` keeps the score rule of the skellytracker host: the mean of
  the two softmax peaks. The four package sidecars (`rtmpose-body`, `rtmpose-hand`, `rtmpose-face`,
  `rtmw-wholebody`, all `v2024.09.1019`) and their threshold `confidence_threshold: 0.004` use this
  scale. Their meaning does not change.
- The location, the tie order, the bin-to-pixel scale and the depth formula are the same for the two
  versions. They make the old text exact, and they agree with the skellytracker host for every legacy
  sidecar. No package sidecar is 3D. The -1 rule has no effect on a legacy sidecar, because a softmax
  peak is `> 0`.
- The change goes into the `vNEXT` revision.
- New heading "Legacy behaviour" in `post/pose-decode-simcc.md`:

```text
## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| SimCC keypoint score | The mean of the two softmax peaks: `0.5 * (max(softmax(simcc_x[n, k])) + max(softmax(simcc_y[n, k])))`. The softmax subtracts the maximum of each distribution first. The score is in `(0, 1]`, so the -1 rule never applies. This is the rule of the skellytracker host for the package RTMPose and RTMW sidecars. | The smaller of the two raw peaks, with no softmax. A score `<= 0` puts the keypoint at bin -1 (see [Behaviour](#behaviour)). |

See also [Version-aware compatibility](../format/versioning.md#version-aware-compatibility).
```

### 2.7 Changelog row

Summary of changes (`changelog.md:16`, five columns). `N` is the next free number at merge time. Rows 1 to 19 exist (`changelog.md:18-36`).
13 open proposals add a summary row (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter; `omitted-upstream-output` adds none), for example `pose-decode-flip-test`, `model-id-suffix` and `simcc-score-rule`. Thus the number depends on the merge order.

```text
| N | Pose | The SimCC keypoint score is the smaller of the two raw peaks, `min(max(simcc_x), max(simcc_y))`, with no softmax. A keypoint with a score `<= 0` gets bin -1 on each axis. The argmax takes the lowest bin on a tie. Bin `b` maps to `b * input_width / X_bins` and `b * input_height / Y_bins`. A `simcc_z` bin maps to `depth_range[0] + b * (depth_range[1] - depth_range[0]) / Z_bins`, and the `simcc_z` peak does not change the score. **Behaviour change:** legacy sidecars keep the mean of the two softmax peaks. | RTMPose Halpe26, DWPose, RTMW (mmpose `get_simcc_maximum`); RTMW3D (`simcc_z`); skellytracker decision 0024 | [SimCC decode](post/pose-decode-simcc.md#behaviour) |
```

Sentence to append to the end of the existing `vNEXT` row of the `schema_version` history
(`changelog.md:68`):

```text
The SimCC keypoint score is the smaller of the two raw peaks (no softmax); a score `<= 0` puts the keypoint at bin -1; `simcc_z` bin `b` maps to `depth_range[0] + b * (depth_range[1] - depth_range[0]) / Z_bins` (legacy sidecars keep the mean of the two softmax peaks).
```

Bullet for "Compatibility impact" (`changelog.md:55-59`):

```text
- A `vNEXT` sidecar with `pose.decode.method: simcc` has the SimCC score of mmpose: the smaller of the two raw peaks. It has another scale than the legacy score (the mean of the two softmax peaks). A keypoint threshold for one score does not apply to the other.
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/model-sidecar/proposals/<slug>/proposal.md`) | the part 3 code of `specs/model-sidecar/proposals/simcc-score-rule/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_pose_decode_simcc.py` |
| Functions (one for each algorithm) | `simcc_peak` (argmax bin and raw peak of one axis, lowest bin on a tie), `simcc_score` (`vNEXT`: the smaller raw peak), `simcc_score_legacy` (legacy row: the mean of the two softmax peaks), `mark_low_score` (the -1 rule on every axis), `bin_to_pixel` (`bin * input_extent / bin_count`), `bin_to_depth` (`depth_min + bin * (depth_max - depth_min) / Z_bins`), `simcc_decode` (the full section; `legacy=True` selects the legacy score) |

Source commit: none (no host code). This exporter has no SimCC decode on its host side yet
(`rtmw/adapter.py:137` at `f3aeb47`, `:136` before OpenMMLab-Exporter decision 0050: "`onnx_runtime` has no such decoder"). The functions come from the text of
part 2. The section has no reference implementation yet (`specs/model-sidecar/reference/` does not exist in
the checkout). Thus this file implements the full section as changed, and it is also the
reference-implementation step of the section. The file does not implement the unprojection: that is
`post.unprojection`.

```python
"""Reference implementation of the section post.pose.decode.simcc, as the proposal changes it.

Section ID: post.pose.decode.simcc (section file specs/model-sidecar/post/pose-decode-simcc.md).
Proposal: specs/model-sidecar/proposals/simcc-score-rule/proposal.md (OpenMMLab-Exporter), slug simcc-score-rule.
A skellytracker session adds the proposal to the gap record 0024
(skellytracker specs/exporter-guide/sidecars/workflow/phase-2-proposal.md:23, `dom/21-move-sidecar-guide`).
Target file in skellytracker: specs/model-sidecar/reference/post_pose_decode_simcc.py.

source commit: none (no host code). OpenMMLab-Exporter has no SimCC decode on its host side yet.
The functions come from the text of part 2 of the proposal.

Vector results: the 20 vectors of part 4 of the proposal pass (20 of 20, 2026-10-23). They are
unverified: no host implementation in an exporter or in skellytracker gives the vNEXT rule yet.
Parity result: to run (part 5 of the proposal).

The file implements the full section as changed: the argmax location, the score rule (vNEXT and
legacy), the -1 rule, the bin-to-pixel scale and the simcc_z depth. The keypoints that it returns
are in the model-input pixels of the crop. The unprojection to the source image is the section
post.unprojection (inverse of pre.resize.affine_person_crop). It is not in this file.

Uses only NumPy and the Python standard library.
"""

from __future__ import annotations

import numpy as np


def simcc_peak(simcc: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.decode.simcc: the peak bin and the peak value of each 1-D distribution.

    `simcc` has the shape (N, K, bins). The function reads the raw output values. It applies no
    softmax. The bin is the first index of the maximum value on the last axis (np.argmax: a tie
    selects the lowest bin). Returns (bin, peak), each of shape (N, K). `bin` is int64. `peak` has
    the dtype of `simcc`.
    """
    simcc = np.asarray(simcc)
    return np.argmax(simcc, axis=-1), np.max(simcc, axis=-1)


def simcc_score(peak_x: np.ndarray, peak_y: np.ndarray) -> np.ndarray:
    """post.pose.decode.simcc, schema_version >= vNEXT: the keypoint score.

    The score is the smaller of the two raw peaks: peak_y where peak_x > peak_y, else peak_x.
    This is min(peak_x, peak_y) for finite values. The simcc_z peak does not change the score.
    """
    peak_x = np.asarray(peak_x)
    peak_y = np.asarray(peak_y)
    return np.where(peak_x > peak_y, peak_y, peak_x)


def simcc_score_legacy(simcc_x: np.ndarray, simcc_y: np.ndarray) -> np.ndarray:
    """post.pose.decode.simcc, schema_version < vNEXT (legacy row): the keypoint score.

    The score is the mean of the two softmax peaks:
    0.5 * (max(softmax(simcc_x[n, k])) + max(softmax(simcc_y[n, k]))).
    The softmax subtracts the maximum of each distribution first. The result is in (0, 1].
    """

    def softmax_peak(simcc: np.ndarray) -> np.ndarray:
        simcc = np.asarray(simcc)
        e = np.exp(simcc - np.max(simcc, axis=-1, keepdims=True))
        return np.max(e / np.sum(e, axis=-1, keepdims=True), axis=-1)

    return 0.5 * (softmax_peak(simcc_x) + softmax_peak(simcc_y))


def mark_low_score(bins: np.ndarray, score: np.ndarray) -> np.ndarray:
    """post.pose.decode.simcc: the -1 rule.

    `bins` has the shape (N, K, D): the peak bin of each axis (D is 2, or 3 with simcc_z).
    Where score <= 0, every axis of the keypoint gets the bin -1. The comparison is not strict:
    a score of exactly 0 gets the bin -1. Returns float64 bins.
    """
    bins = np.array(bins, dtype=np.float64)
    bins[np.asarray(score) <= 0] = -1.0
    return bins


def bin_to_pixel(bin_index: np.ndarray, input_extent: int, bin_count: int) -> np.ndarray:
    """post.pose.decode.simcc: the bin-to-pixel scale of one axis (Shape key).

    pixel = bin * input_extent / bin_count, in float64. `input_extent` is input_width for
    simcc_x (bin_count X_bins) and input_height for simcc_y (bin_count Y_bins). The bin is not
    moved to its centre: bin 0 gives pixel 0.
    """
    return np.asarray(bin_index, dtype=np.float64) * input_extent / bin_count


def bin_to_depth(
    bin_index: np.ndarray, depth_range: tuple[float, float], bin_count: int
) -> np.ndarray:
    """post.pose.decode.simcc: the depth of a simcc_z bin (is_3d: true).

    depth = depth_min + bin * (depth_max - depth_min) / Z_bins, in float64, in depth_unit.
    Bin 0 gives depth_min. Bin Z_bins (one past the last bin) would give depth_max.
    """
    depth_min, depth_max = depth_range
    return depth_min + np.asarray(bin_index, dtype=np.float64) * (depth_max - depth_min) / bin_count


def simcc_decode(
    simcc_x: np.ndarray,
    simcc_y: np.ndarray,
    input_width: int,
    input_height: int,
    simcc_z: np.ndarray | None = None,
    depth_range: tuple[float, float] | None = None,
    legacy: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.decode.simcc: the full decode of one batch of crops.

    simcc_x (N, K, X_bins), simcc_y (N, K, Y_bins) and, when is_3d: true, simcc_z (N, K, Z_bins)
    with depth_range. `legacy` selects the score of the legacy row (schema_version < vNEXT).
    Returns (keypoints, score). keypoints has the shape (N, K, 2), or (N, K, 3) with simcc_z:
    x and y in the model-input pixels of the crop, z in depth_unit. score has the shape (N, K).
    """
    bin_x, peak_x = simcc_peak(simcc_x)
    bin_y, peak_y = simcc_peak(simcc_y)
    if legacy:
        score = simcc_score_legacy(simcc_x, simcc_y)
    else:
        score = simcc_score(peak_x, peak_y)
    axes = [bin_x, bin_y]
    if simcc_z is not None:
        if depth_range is None:
            raise ValueError("depth_range is required with simcc_z (V-post.pose.decode.simcc-1)")
        bin_z, _ = simcc_peak(simcc_z)
        axes.append(bin_z)
    bins = mark_low_score(np.stack(axes, axis=-1), score)
    columns = [
        bin_to_pixel(bins[..., 0], input_width, np.shape(simcc_x)[-1]),
        bin_to_pixel(bins[..., 1], input_height, np.shape(simcc_y)[-1]),
    ]
    if simcc_z is not None:
        columns.append(bin_to_depth(bins[..., 2], depth_range, np.shape(simcc_z)[-1]))
    return np.stack(columns, axis=-1), score
```

## 4. Vectors

The vectors come from the reference file (scratch generator `simcc_score_vectors.py`, not committed).
The generator checks each case against a value written by hand. All 20 cases pass. A runner gives
each numeric list of `input` as a float64 NumPy array (the flip-test vectors use float32). With
float32 inputs, 13 of 20 cases pass at the case tolerances.

- The two legacy cases (`legacy-score-softmax-mean`, `decode-legacy-negative-peak`) also ran through
  the skellytracker function `get_simcc_maximum` (`skellytracker/core/detectors/processing/simcc_decode.py:28-69`,
  `dom/12-single-working-branch`; the file is the same at `dom/18-agents-adr-bootstrap-kit` and at `dom/21-move-sidecar-guide`). It gave the same scores (within 1e-12) and the same locations.
- The two `vNEXT` 2D decode cases (`decode-2d`, `decode-2d-equal-peaks-and-zero`) give another score
  in that function, as expected: it has only the legacy rule.
- The cases did not run through upstream code. The upstream files are read-only data for this
  proposal. The 2D expected values follow `post_processing.py:90-99` and `simcc_label.py:191`. The
  `depth-rtmw3d` hand values follow the form of `simcc_3d_label.py:187, 191-192` in float64. Over the
  bins -1 to 575, this form in float32 differs from `bin_to_depth` by at most 1.9e-7 (thus the
  `atol` of 1e-6).
- On an axis of 256 pixels and 512 bins, `bin_to_pixel` gives exactly the float32 values of
  `locs / 2.0` (the form of `simcc_label.py:191`) for each bin from -1 to 511.

Because the vNEXT cases have no implementation, the file is `unverified`.

The YAML below uses the form of the template (`specs/model-sidecar/templates/change-proposal.md:251-260`:
`generated_by: <reference file>`, a `function` key and an optional `compare` key on each case). The
skellytracker vector tooling uses another form, and `tools/tests/test_vectors.py` fails on this text
as it is (2.1, rows `tools/make_vectors.py` and `tools/tests/test_vectors.py`). The skellytracker
session converts the cases to the form of `make_vectors.py`: `generated_by: tools/make_vectors.py`,
the case `tolerance` in place of `compare`, a `tolerance` on each case with a fractional number
(also `score-x-smaller` and the other cases with no `compare`), and the `function` key handled as
2.1 says. The ids and the inputs do not change. The generator rounds the expected values to 6
decimals (`make_vectors.py:62`), so the file tolerance must be at least `1e-6` (2.1).

```yaml
section: post.pose.decode.simcc
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/simcc-score-rule/proposal.md`
unverified: "No exporter has a SimCC host decode yet, and skellytracker has only the legacy score. The
  legacy cases (legacy-score-softmax-mean, decode-legacy-negative-peak) agree with skellytracker
  simcc_decode.py::get_simcc_maximum at `dom/12-single-working-branch`."
# The 2D expected values follow mmpose v1.3.2 mmpose/codecs/utils/post_processing.py:90-99 and
# mmpose/codecs/simcc_label.py:191; the 3D values follow projects/rtmpose3d/rtmpose3d/utils.py:60-70
# and simcc_3d_label.py:187, 191-192 (upstream code read, not run; not an implementation).
cases:
  - id: peak-tie-lowest-bin  # two bins share the maximum: the lower bin wins
    function: simcc_peak
    params: {}
    input:
      simcc: [[[1.0, 3.0, 3.0, 0.0]]]
    expect:
      bin: [[1]]
      peak: [[3.0]]
  - id: peak-raw-negative  # raw values, no softmax; a negative peak stays negative
    function: simcc_peak
    params: {}
    input:
      simcc: [[[-5.0, -2.0, -3.0], [0.25, 0.75, 0.5]]]
    expect:
      bin: [[1, 1]]
      peak: [[-2.0, 0.75]]
  - id: score-x-smaller
    function: simcc_score
    params: {}
    input:
      peak_x: [[0.4]]
      peak_y: [[0.7]]
    expect:
      score: [[0.4]]
  - id: score-y-smaller
    function: simcc_score
    params: {}
    input:
      peak_x: [[0.9]]
      peak_y: [[0.3]]
    expect:
      score: [[0.3]]
  - id: score-x-equals-y  # equal peaks: the score is that value
    function: simcc_score
    params: {}
    input:
      peak_x: [[0.5]]
      peak_y: [[0.5]]
    expect:
      score: [[0.5]]
  - id: score-negative  # the min keeps a negative peak
    function: simcc_score
    params: {}
    input:
      peak_x: [[-0.25]]
      peak_y: [[0.6]]
    expect:
      score: [[-0.25]]
  - id: score-both-negative
    function: simcc_score
    params: {}
    input:
      peak_x: [[-0.5]]
      peak_y: [[-0.125]]
    expect:
      score: [[-0.5]]
  - id: low-score-zero  # score exactly 0: <= 0, so the bins become -1
    function: mark_low_score
    params: {}
    input:
      bins: [[[3, 5]]]
      score: [[0.0]]
    expect:
      bins: [[[-1.0, -1.0]]]
  - id: low-score-negative
    function: mark_low_score
    params: {}
    input:
      bins: [[[3, 5]]]
      score: [[-0.125]]
    expect:
      bins: [[[-1.0, -1.0]]]
  - id: low-score-small-positive  # score > 0: the bins stay
    function: mark_low_score
    params: {}
    input:
      bins: [[[3, 5]]]
      score: [[0.0001]]
    expect:
      bins: [[[3.0, 5.0]]]
  - id: low-score-3d  # with simcc_z, the z bin also becomes -1
    function: mark_low_score
    params: {}
    input:
      bins: [[[3, 5, 7]]]
      score: [[0.0]]
    expect:
      bins: [[[-1.0, -1.0, -1.0]]]
  - id: pixel-ratio-2  # X_bins = 2 * input_width (simcc_split_ratio 2.0, all models in scope); exact
    function: bin_to_pixel
    params:
      input_extent: 192
      bin_count: 384
    input:
      bin_index: [0, 1, 383, -1]
    expect:
      pixel: [0.0, 0.5, 191.5, -0.5]
  - id: pixel-ratio-1.5  # the scale comes from the bin count, not from a fixed ratio 2.0
    function: bin_to_pixel
    params:
      input_extent: 192
      bin_count: 288
    input:
      bin_index: [0, 1, 287]
    expect:
      pixel: [0.0, 0.6666666666666666, 191.33333333333334]
    compare:
      pixel:
        atol: 1.0e-09
  - id: depth-rtmw3d  # mmpose v1.3.2 SimCC3DLabel.decode form: (bin / 2 / (288 / 2) - 1) * z_range
    function: bin_to_depth
    params:
      depth_range: [-2.1744869, 2.1744869]
      bin_count: 576
    input:
      bin_index: [0, 288, 575, -1]
    expect:
      depth: [-2.1744869, 0.0, 2.166936598263889, -2.1820372017361107]
    compare:
      depth:
        atol: 1.0e-06
  - id: legacy-score-softmax-mean  # legacy row; a negative raw peak still gives a positive score
    function: simcc_score_legacy
    params: {}
    input:
      simcc_x: [[[0.0, 2.0, 1.0], [-3.0, -1.0, -2.0]]]
      simcc_y: [[[1.0, 1.0, 0.0], [-4.0, -4.0, -4.0]]]
    expect:
      score: [[0.54377987701317, 0.4992871445540775]]
    compare:
      score:
        atol: 1.0e-09
  - id: decode-2d  # k0: x tie at bins 1 and 2 (bin 1 wins), score min(0.9, 0.8); k1: score 0.3, y bin 3; k2: x peak negative, so the score is -0.1 <= 0 and both bins become -1
    function: simcc_decode
    params:
      input_width: 2
      input_height: 2
    input:
      simcc_x: [[[0.1, 0.9, 0.9, 0.2], [0.3, 0.2, 0.1, 0.0], [-0.5, -0.1, -0.3, -0.2]]]
      simcc_y: [[[0.0, 0.0, 0.8, 0.1], [0.0, 0.0, 0.0, 0.3], [0.2, 0.1, 0.0, 0.0]]]
    expect:
      keypoints: [[[0.5, 1.0], [0.0, 1.5], [-0.5, -0.5]]]
      score: [[0.8, 0.3, -0.1]]
  - id: decode-2d-equal-peaks-and-zero  # k0: x and y peaks equal (0.5); k1: all x values 0, so the score is exactly 0 and the bins become -1
    function: simcc_decode
    params:
      input_width: 3
      input_height: 3
    input:
      simcc_x: [[[0.0, 0.5, 0.25], [0.0, 0.0, 0.0]]]
      simcc_y: [[[0.5, 0.0, 0.0], [0.0, 0.5, 0.0]]]
    expect:
      keypoints: [[[1.0, 0.0], [-1.0, -1.0]]]
      score: [[0.5, 0.0]]
  - id: decode-3d  # the z peak 0.9 does not change the score; z bin 2 of 4 on [-1, 1] gives 0
    function: simcc_decode
    params:
      input_width: 2
      input_height: 2
      depth_range: [-1.0, 1.0]
    input:
      simcc_x: [[[0.0, 0.7, 0.1, 0.0]]]
      simcc_y: [[[0.2, 0.6, 0.0, 0.0]]]
      simcc_z: [[[0.0, 0.0, 0.9, 0.1]]]
    expect:
      keypoints: [[[0.5, 0.5, 0.0]]]
      score: [[0.6]]
  - id: decode-3d-low-score  # score <= 0: the x, y and z bins become -1; z = -1 + (-1) * 2 / 4
    function: simcc_decode
    params:
      input_width: 2
      input_height: 2
      depth_range: [-1.0, 1.0]
    input:
      simcc_x: [[[0.0, 0.7, 0.1, 0.0]]]
      simcc_y: [[[-0.2, -0.6, -0.4, -0.3]]]
      simcc_z: [[[0.0, 0.0, 0.9, 0.1]]]
    expect:
      keypoints: [[[-0.5, -0.5, -1.5]]]
      score: [[-0.2]]
  - id: decode-legacy-negative-peak  # the same outputs as k2 of decode-2d: the legacy score is > 0, so the bins stay
    function: simcc_decode
    params:
      input_width: 2
      input_height: 2
      legacy: true
    input:
      simcc_x: [[[-0.5, -0.1, -0.3, -0.2]]]
      simcc_y: [[[0.2, 0.1, 0.0, 0.0]]]
    expect:
      keypoints: [[[0.5, 0.0]]]
      score: [[0.2884749223417268]]
    compare:
      score:
        atol: 1.0e-09
```

Each key of `params` and `input` is a parameter of the function that the case names. The generator
checks this with `inspect.signature`. No case is a pixel case. The `compare` tolerances are for
float64 division order (`pixel-ratio-1.5`, `legacy-score-softmax-mean`,
`decode-legacy-negative-peak`) and for the float32 form of the upstream depth (`depth-rtmw3d`).

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | (1) Preprocessed input: maximum absolute difference 0 (exporter guide, "Parity", step 4). (2) Export error `E` of each crop: the maximum absolute difference of `simcc_x` and `simcc_y` between the ONNX file and the mmpose head on the same tensor. It is recorded, not gated. (3) Score: `abs(score_host - score_upstream) <= E` of the crop. Source: a max over bins and a min of two values change by at most the largest change of their inputs. (4) Bins: where the upstream peak exceeds the second value of its row by more than `2 * E`, the host bin equals the upstream bin. Other bin changes are allowed, counted and listed. (5) Keypoints with equal bins: per-point difference in source-image pixels at most 1e-3 px (float32 noise of the mmpose unprojection, `mmpose/models/pose_estimators/topdown.py:154-156`; the float32 step of a 640 px coordinate is 6.1e-5 px). (6) The -1 rule: each keypoint with an upstream score `<= 0` has a host score `<= 0`, unless `abs(score_upstream) <= E`. Its location meets gate (5). (7) Body OKS AP on the full image set: `abs(AP_host - AP_upstream) <= 0.005` (the fp32 gate of this exporter, OpenMMLab-Exporter D5 in `notes/decisions/migration-decisions.md:55`). |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO val2017, GT person boxes (`annotations/person_keypoints_val2017.json`). The -1 rule: image 67315 (annotation 2205356) and image 108026 (annotation 458854). The scratch run of part 1 found a score `<= 0` there for Halpe26-m. The parity script must confirm it with the upstream crop. Argmax ties: the crops with a tie in a `simcc_x` or `simcc_y` row (Halpe26-m: 6 and 4 rows in the scratch run). The script lists them. The two branches of the min (score from `x` and score from `y`): every image runs both. A portrait box and a landscape box (the two aspect branches of the crop). Both input sizes: 256x192 (384 and 512 bins) and 384x288 (576 and 768 bins). The full set of 6352 instances for gate (7). |
| Upstream reference: library, version, config and command | mmpose v1.3.2 in the exporter Docker image (`mmdeploy-convert/Dockerfile.exporter:34, 42-44`). `mmpose.apis.init_model(config, checkpoint)`, `cfg.model.test_cfg.flip_test = False` (this proposal compares the decode only; the flip-test proposal covers the second pass), then `mmpose.apis.inference_topdown(model, img, bboxes, bbox_format='xyxy')`. The worker saves the `keypoints`, the `keypoint_scores`, the preprocessed tensor (the output of `data_preprocessor`) and the raw head outputs `pred_x`, `pred_y`. The results of `inference_topdown` do not hold the raw outputs. The worker gets them in one of two ways: (a) forward hooks on `model.head.cls_x` and `model.head.cls_y`, the two last `nn.Linear` layers of the head forward (`RTMCCHead` for Halpe26 and DWPose: `mmpose/models/heads/coord_cls_heads/rtmcc_head.py:131-132, 158-160`; `RTMWHead` for RTMW: `rtmw_head.py:156-157, 192-195`); or (b) a second call `model.head.forward(model.extract_feat(inputs))` on the tensor from `data_preprocessor`. A forward hook on `model.head` does not work: `predict` calls `self.forward(feats)` directly (`rtmcc_head.py:210`, `rtmw_head.py:244`), so the hooks of `model.head` do not run. The worker must not use `test_cfg.output_heatmaps=True`: that option normalizes `pred_x` and `pred_y` with `get_simcc_normalized` before it outputs them (`rtmcc_head.py:214-224`, with the warning at lines 217-220; `rtmw_head.py:248-258`). Gates (2) and (3) need the raw values that the decode uses (`rtmcc_head.py:210-212`, `rtmw_head.py:244-246`). Configs: Halpe26 `configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py` and one 384x288 size; DWPose `configs/wholebody_2d_keypoint/rtmpose/ubody/rtmpose-m_8xb64-270e_coco-ubody-wholebody-256x192.py` and `rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py`; RTMW `mmdeploy-convert/model_cfgs/rtmw-m_8xb1024-270e_cocktail14-256x192.py` and `rtmw-x_8xb320-270e_cocktail14-384x288.py` (`decode_visibility=True`). The RTMW checkpoints are in the image (`mmdeploy-convert/download_files.py:36-40`). The DWPose and Halpe26 checkpoints are not in the manifest yet: they need a manifest change and a new image. The publication of an image needs the approval of the user (`AGENTS.md`, section 6). RTMW3D: no run. This exporter has no RTMW3D family. The `simcc_z` rule rests on the code reading of part 1 and the vectors `depth-rtmw3d`, `decode-3d` and `decode-3d-low-score`. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (`E` for each crop; report the maximum and the 99th percentile) |
| Preprocessed input: maximum absolute difference for each image | to run (expect 0; a non-zero value makes rows T4b or T10 of the intake a `near-miss`) |
| Row count for each image: sidecar path and upstream | to run (one pose for each box on both sides) |
| Final outputs in source-image coordinates: metric and value for each role | to run (`pose_estimator`: gates 3 to 7) |
| Result (`pass`, `fail` or `to run`) | to run |
| Script path in the exporter repo | `notes/decisions/scripts/simcc_decode_parity.py` (host side: ONNX Runtime CUDA, the exporter preprocessing, the reference file of part 3, the unprojection, the gates) and `notes/decisions/scripts/simcc_decode_parity_worker.py` (container side: mmpose). Planned, not written. The flip-test proposal plans `notes/decisions/scripts/pose_flip_test_parity.py`. The two scripts can share the container worker: the flip-test run then sets `flip_test = True`. |
| Exporter commit of the script | unknown (the script is not written yet) |
| Command | `uv run python notes/decisions/scripts/simcc_decode_parity.py --family dwpose-wholebody133-ubody --size m` (planned). The script starts the worker in the published image `<user>/openmmlab-exporter:df-<sha>`. |

The host side keeps torch out of the host process (`AGENTS.md`, section 4). Only the worker in the
container imports mmpose. The host side uses the reference file of part 3 in place of the missing
spec feature. It uses the host implementation of `pre.resize.affine_person_crop` and `pre.normalize`
for the other steps, after that code is committed.

## 6. skellytracker implementation proposal

skellytracker does not build this now. The implementer checks this part.

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/simcc_decode.py`. `get_simcc_maximum` (lines 28-69) gets the `vNEXT` rule (the functions `simcc_peak`, `simcc_score` and `mark_low_score` of part 3) and keeps the softmax mean for the legacy rule (`simcc_score_legacy`). `decode_simcc` (lines 72-99) takes the scale from the bin counts (`input_width / X_bins`), not from `simcc_split_ratio` (today `_SIMCC_SPLIT_RATIO = 2.0`, line 102). A 3D branch adds `simcc_z` and `bin_to_depth`. Today `simcc_pose_decode` raises for `is_3d` (lines 127-128). |
| Dispatch point | `simcc_pose_decode` (lines 105-139) selects the rule by the `schema_version` of the sidecar. Today it receives only `PoseDecodeSpec`, which has no version. For the implementer: pass the version or a resolved legacy flag from the detector (the callers are `postprocess` in `rtmw/wholebody/rtmw_wholebody_detector.py:88`, `rtmpose/body/rtmpose_body_detector.py:92`, `rtmpose/face/rtmpose_face_detector.py:92` and `rtmpose/hand/rtmpose_hand_detector.py:94`). |
| Validator changes (`model.py`, with rule IDs) | none. Part 2.4 adds no rule. `PoseDecodeSpec` (`skellytracker/core/sidecar/model.py:259-278`) does not change. |
| Tests | The vectors of part 4 (`specs/model-sidecar/vectors/post.pose.decode.simcc.yaml`), with `legacy` mapped to the version flag. A test that the four package sidecars keep their scores (the legacy rule). A golden parity test for one `vNEXT` SimCC sidecar (the pattern of `skellytracker/tests/sidecar/test_rtmw_sidecar.py`). |
| Existing code that the change touches | `simcc_decode.py` (`get_simcc_maximum`, `decode_simcc`, `simcc_pose_decode`). The threshold `confidence_threshold: 0.004` and its use in `postprocess` (`rtmw_wholebody_detector.py:45, 100-104`; `rtmpose_body_detector.py:49, 104-108`; `rtmpose_face_detector.py:49, 104-108`; `rtmpose_hand_detector.py:51, 106-110`). It fits only the legacy score. A `vNEXT` sidecar needs another value: for the implementer (the part 1 numbers show the two scales). A second copy of the legacy `get_simcc_maximum` in `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py` (line 26; `rtmpose_letterbox_postprocess` calls it at line 230). No Python file imports that module. skellytracker already lists it as an unused module (`notes/decisions/open-work.md:97`; skellytracker decision 0007, line 70). For the implementer: remove it, or make it call `simcc_decode.py`. The module docstring of `simcc_decode.py` (lines 6-9) says that the math is vendored from rtmlib, but rtmlib has no softmax (`post_processings.py:31-42`). |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` (`vNEXT`, `pose.decode: {method: simcc}`, `rtmw/sidecar.py:164` at `f3aeb47`); the planned families `dwpose-wholebody133-ubody` and `rtmpose-halpe26` | none. No new field and no regenerate. The meaning of the `vNEXT` sidecars changes to the mmpose rule, which is the upstream rule of these models. OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMW sidecar until the RTMW intake is `describes`, so the next RTMW sidecar comes at that later round. | The host has no SimCC decode yet (`rtmw/adapter.py:137` at `f3aeb47`). A future host decode implements part 3. The parity script of part 5 uses the reference file. |
| Roboflow-Exporter | none (no SimCC model) | none | none |
| Ultralytics-Exporter | none (YOLO26-pose uses the `coordinate` decode) | none | none |
| Qualcomm-Exporter | none (the MediaPipe landmark models use `keypoints` outputs, `post/pose-schema.md:141`) | none | none |
| MediaPipe-Exporter | none (as Qualcomm-Exporter) | none | none |
| The proposing exporter, if it is not in this table | n/a (OpenMMLab-Exporter is in the table) | | |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-hand`, `rtmpose-face`, `rtmw-wholebody` (all `v2024.09.1019`) | none. They keep the legacy score (the row of 2.6). | none |

The spec example `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml`
is `vNEXT`. It needs no edit. Its scores change scale with the new rule.

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change: "Its score is the max value" (the near-miss of today) | The text does not say how the two peaks combine or if a softmax comes first. Three hosts read it in three ways. At the median, the min score is 130 to 145 times the softmax score. | Part 1; skellytracker 0024 "Reason" |
| The mean of the softmax peaks at `vNEXT` (skellytracker today) | It is not the upstream rule. Its scores are near `1 / bins` (p50 0.0045 to 0.0048), so the upstream rescoring threshold 0.2 removes every keypoint. Body AP 0.6239 / 0.6809 / 0.6559 in place of 0.7216 / 0.7647 / 0.7477. It stays the legacy rule, because the package sidecars and their threshold 0.004 depend on it. | Part 1; `simcc_decode.py:53-63` |
| The mean of the raw peaks (rtmlib) | It is not the upstream rule. rtmlib comments out the min. Its AP is 0.0012 to 0.0017 lower than the min rule on the three models, and its scores are higher (more keypoints pass 0.2: 90.9 % to 93.7 % in place of 82.5 % to 87.7 %). | Part 1; rtmlib `post_processings.py:39-41`, `9f51b34` |
| A field that selects the rule (`pose.decode.score_rule`) | skellytracker 0024 rejects it: the SimCC models in scope come from mmpose, so one rule is sufficient. A field adds a host branch that no model needs. The legacy row keeps the old host rule without a field. | skellytracker 0024 "Alternatives rejected" |
| No -1 rule (keep the argmax location for a score `<= 0`) | It differs from the upstream location of these keypoints (3 of 165152 Halpe26-m keypoints in part 1). The OKS of COCO uses every keypoint location, also with a low score. | `post_processing.py:99`; part 1 |
| Mark a keypoint with a score `<= 0` as missing (no location, or NaN) | The upstream gives a location. A host can still drop the keypoint with a score threshold. The sidecar has no "missing" value for a keypoint location. | `post_processing.py:99`; `simcc_label.py:191`; `topdown.py:154-156` |
| A bin centre offset (`(b + 0.5) * input_width / X_bins`) | The upstream divides the bin by `simcc_split_ratio` with no offset. The encode puts pixel `p` in bin `around(p * simcc_split_ratio)`. A 0.5-bin offset moves every keypoint by 0.25 px at ratio 2. | `simcc_label.py:191, 202-210` |
| The depth with `b / (Z_bins - 1)` (bin `Z_bins - 1` at `depth_range[1]`) | The upstream maps bin `b` to `(b / 2 / (D / 2) - 1) * z_range`, which is `b / Z_bins` on `[-z_range, z_range]`. | `simcc_3d_label.py:187, 191-192` |
| The score as the min of three peaks (with `simcc_z`) | The upstream 3D score uses only the `x` and `y` peaks. | `projects/rtmpose3d/rtmpose3d/utils.py:64-69` |
| Put the decode into the ONNX graph (a `keypoints` output with the `coordinate` decode) | It changes the graph of every SimCC family. The RTMW contract of this exporter has the two raw outputs `simcc_x` and `simcc_y`, and the package sidecars use them. The score rule would then be hidden in the graph. | `rtmw/contract.py:10-15` |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. (Both intakes name this file in row K8 and in "Proposals and
      reference files", and record the part 4 result (20 of 20, unverified):
      the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts);
      the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts). The RTMW intake also links it: the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts).)
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry (skellytracker 0024). It does not compete with it.
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

This proposal has `to run` in part 5. It is ready for a skellytracker session to record. It is not
ready for the user to accept.

## Before acceptance

The user cannot accept this proposal before this work is done.

**Parts**

- [ ] Part 5: get the parity numbers. The export error, the preprocessed input, the row count, the final outputs and the result are all `to run`.
- [ ] Part 5: write and commit the parity scripts `notes/decisions/scripts/simcc_decode_parity.py` and `notes/decisions/scripts/simcc_decode_parity_worker.py` in OpenMMLab-Exporter. Record their commit. Today the scripts are planned, not written, and the commit is unknown.
- [ ] Part 5: add the DWPose and Halpe26 checkpoints to the manifest of the exporter image, and publish a new image. The publication of an image needs the approval of the user.
- [ ] Part 5: name the 384x288 config of Halpe26. Today the row gives only "one 384x288 size".
- [ ] Part 8: add an alternative row for the tie order (the lowest bin). The header says that part 8 gives the reasons for the three additions, but part 8 has no row for the tie order.
- [ ] Part 2.6: say that `confidence_threshold: 0.004` is a default of the detector config in the package code. It is not a field of the four package sidecars.
- [ ] The replacement text of "Implementer guidance" (part 2.1) says "The detectors drop a keypoint below `confidence_threshold: 0.004`". The detectors keep the keypoint: they set its coordinates to NaN and its visibility to 0.0 (`rtmw_wholebody_detector.py:100-104`). The text also gives no source for its statements.
- [ ] Each statement of guidance must have a source: a repo, a file and a commit. The "Authoring guidance" text (part 2.1) cites mmpose v1.3.2 with no commit, `simcc_3d_label.py:100` with no version, and no file for "the configs set the same codec as RTMW".
- [ ] The guidance texts and the changelog summary row cite "skellytracker decision 0024" as plain text. A spec file must link the entry (`../../notes/decisions/0024-simcc-score-rule.md` from `specs/model-sidecar/changelog.md`).

**Evidence**

- [ ] Find a primary source for the unit of the RTMW3D depth (`depth_unit: m`). No upstream file gives the unit. The only source is the spec (`post/pose-schema.md:93`), which is secondary.
- [ ] Commit the scripts that give the numbers of part 1: the body OKS AP of each score rule, the score percentiles, the 3 keypoints of 165152 that the -1 rule changes, and the tie counts. The scratch scripts are not committed, so these numbers are not evidence.
- [ ] Give full-SHA permalinks for the upstream code: rtmlib `9f51b34` and mmdeploy `bc75c9d6` are short SHAs. Make sure that mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (v1.3.2) is on the default branch of mmpose.
- [ ] Give full-SHA permalinks for the exporter citations (`rtmw/sidecar.py:164`, `rtmw/adapter.py:137`, `rtmw/contract.py:10-15`, `mmdeploy-convert/Dockerfile.exporter`, `mmdeploy-convert/download_files.py:36-40`, `notes/decisions/migration-decisions.md:55`). Commit `f3aeb47` is on the default branch of OpenMMLab-Exporter.
- [ ] Update the header row "Exporter commit". It says that `f3aeb47` is not pushed, but `f3aeb47` is on the default branch of OpenMMLab-Exporter now.
- [ ] Part 1: correct the name of the RTMW-m checkpoint. The proposal writes `rtmw-dw-l-m_simcc-cocktail14_270e-256x192_20231122`. The exporter manifest (`mmdeploy-convert/download_files.py:36`) writes `rtmw-dw-l-m_simcc-cocktail14_270e-256x192-20231122`.

**Template checklist**

Each box of "Before you stop" is ticked, and each tick has a reason. No box fails.

**Vectors and tooling**

- [ ] Decide one case form for the vectors of all proposals. The form of the template (`function`, `compare`, `generated_by: <reference file>`) does not agree with `tools/tests/test_vectors.py` (`CASE_KEYS`, `generated_by: tools/make_vectors.py`, a `tolerance` on each case with a fractional `expect`). The template and the exporter guide (`specs/exporter-guide/sidecars/workflow/phase-2-proposal.md`) prescribe the form that the tests reject.
- [ ] Give the vector file a tolerance of `1e-6` or more. `make_vectors.py` rounds to 6 decimals. Four cases (`pixel-ratio-1.5`, `depth-rtmw3d`, `legacy-score-softmax-mean`, `decode-legacy-negative-peak`) have more than 6 decimals, so their `atol` of `1e-9` cannot stay.
- [ ] Add a way for `tools/make_vectors.py` and the tests to import `specs/model-sidecar/reference/post_pose_decode_simcc.py`. The folder is not a package, and the tests put only `tools/` on `sys.path`. This is the first reference implementation, so no mechanism exists.
- [ ] Add to the landing plan the test in `tools/tests/` that runs the reference functions against the vectors. Part 2.1 does not list it (decision [0013](../../../../notes/decisions/0013-spec-structure.md) and the skill `change-sidecar-spec`, Procedure B step 7).
- [ ] Part 2.1 proposes a builder `build_simcc_decode` in `tools/make_vectors.py` with its own copy of the formulas. When a section has a reference implementation, the generator must call it (decision 0013, and Procedure B step 8). Change the row.
- [ ] Verify the vNEXT cases against a host implementation. Today they are `unverified`: no host has the vNEXT rule. Only the two legacy cases agree with `skellytracker/core/detectors/processing/simcc_decode.py::get_simcc_maximum`.

**Decisions for the user**

- [ ] Accept or reject the normative `simcc_z` depth formula and the 3D -1 rule. No RTMW3D model is in scope, and no 3D parity run exists.
- [ ] Accept or reject the "Authoring guidance" value `depth_unit: m` for RTMW3D. Its only source is the spec.
- [ ] Decide if the legacy values that this proposal defines are a clarification or a change of legacy meaning: the tie order, the bin-to-pixel scale and the depth formula `b / Z_bins` for `schema_version < vNEXT`. The skellytracker host takes the argmax of the float32 softmax, not of the raw values (`simcc_decode.py:53-57`). Thus the tie order of the host can differ in rare float cases.
- [ ] Decide if the "Implementer guidance" and "Authoring guidance" edits go in the content PR or in a separate non-spec PR.
- [ ] Decide the policy for upstream permalinks of repos that are not exporters (mmpose, rtmlib, mmdeploy).
- [ ] Decide if the optional `(legacy)` flag goes in `tools/sidecar_trace.py`. If it does, `EXPECTED_CELLS` of `tools/tests/test_traceability.py` also changes.
- [ ] Decide how to handle the accepted entries [0013](../../../../notes/decisions/0013-spec-structure.md) (line 149) and [0014](../../../../notes/decisions/0014-spec-lifecycle.md) (line 171). They say "There is no reference implementation yet". This becomes false when the first reference implementation lands.
- [ ] Decide if `specs/sidecar-implementation-plan.md` (line 190) also lists the vNEXT score rule and the scale from the bin counts as package gaps of `simcc_decode.py`.
- [ ] Decide if the title of [0024](../../../../notes/decisions/0024-simcc-score-rule.md) stays "SimCC keypoint score rule" or takes the longer title of the header.

**Merge points**

- [ ] `post/pose-decode-simcc.md` "Behaviour" (line 38): this proposal replaces the bullet, and `pose-decode-flip-test` adds a sentence. The second PR keeps both edits.
- [ ] `post/pose-decode-simcc.md` "Authoring guidance": this proposal adds a bullet about `decode_visibility=True`. `keypoint-visibility` changes the `decode_visibility` bullet (line 58), and `omitted-upstream-output` can name its verdict there. The three texts overlap in meaning. Reconcile them.
- [ ] `post/pose-schema.md` "Shape key": `heatmap-decode-refinement` edits line 108, this proposal adds a sentence after line 110, and `keypoint-visibility` edits line 111 and adds a bullet.
- [ ] `format/versioning.md` "Version-aware compatibility" (lines 53-63): this proposal adds a link. Some proposals with a new "Legacy behaviour" heading add a link, and some do not. Decide one rule for all.
- [ ] `specs/model-sidecar/changelog.md`: the summary row number `N`, the `vNEXT` row (line 68) and "Compatibility impact" (lines 55-59) depend on the merge order.
- [ ] `heatmap-decode-refinement` rejects "No -1 rule" in its part 8 because this proposal adds the same rule. If the user rejects or changes this proposal, that reason is not true.
- [ ] The merge points of the header are stale for `keypoint-visibility`. The header says that it edits the "Behaviour" bullet of `post/pose-decode-simcc.md:38`, but `keypoint-visibility` makes no edit there. The header does not say that `keypoint-visibility` edits the "Shape key" list of `post/pose-schema.md` (line 111) and the `decode_visibility` bullet of "Authoring guidance" (line 58).
