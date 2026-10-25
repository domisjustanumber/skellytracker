---
slug: pose-decode-flip-test
section: post.pose.flip_test
exporter: OpenMMLab-Exporter
decision: "0045"
state: recorded
---

# Change proposal: pose-decode-flip-test

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `pose-decode-flip-test`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. The `python` code block at the end of part 3 is the OpenMMLab-Exporter reference file of the proposal, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | Flip test for the decode of a top-down pose estimator |
| Slug | `pose-decode-flip-test` |
| Date | 2026-10-23; updated 2026-10-24 (checks at exporter `f3aeb47` and skellytracker `dom/18-agents-adr-bootstrap-kit`); updated 2026-10-25 (pin moved to skellytracker `dom/21-move-sidecar-guide`; repo names before decision numbers; parity image IDs chosen) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed: OpenMMLab-Exporter decision 0050; OpenMMLab-Exporter decision 0042 is commit `1dfec48`; `git status --porcelain` is empty; first written at `cce619d`, checked at `d0f4343`). The exporter lines that this proposal cites were checked again at `f3aeb47` on 2026-10-24. `rtmw/identity.py`, `mmdeploy-convert/model_cfgs/rtmw-*.py`, `notes/decisions/migration-decisions.md` and OpenMMLab-Exporter decision 0007 are the same as at `d0f4343`. `pipeline/ARTIFACT_CONTRACT.md` changed (OpenMMLab-Exporter decisions 0042 and 0050), but its cited lines 12-23 and 27-29 have the same text. |
| Model, and its intake file | `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)); the RTMPose Halpe26 family `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts); plan T14; `specs/sidecar/proposals/model-id-suffix/proposal.md`); `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts); plan T11. The ViTAE eval pipeline is chosen, plan T3); the 25-point ViTPose family `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts); plan T14). The pipeline of `vitpose-coco25` is B2 (plan T9): non-UDP, flip test with `shift_heatmap=True`. The created 25-joint test config is in plan 4.4 (not written yet, plan step 5.5). Part 1 gives its measured result. The current family `rtmw-wholebody133` has the same property (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), row K4a, line 188, `gap`). |
| Intake rows with the verdict `near-miss` or `gap` | Row K4a (flip test, `gap`) of each intake above: the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) |
| Kind | `new section` |
| Proposed section ID | `post.pose.flip_test` |
| Section file | `specs/sidecar/post/pose-flip-test.md` (proposed) |
| Depends on | none |
| Needed by | `specs/sidecar/proposals/heatmap-decode-refinement/proposal.md` (slug `heatmap-decode-refinement`; its header row "Depends on" names this proposal). It uses `shift_heatmap: true` of this section for `vitposepp-wholebody133`, because plan T3 chose the ViTAE eval pipeline, and for the 25-point model `vitpose-coco25`, because plan T9 chose B2. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide` (checked 2026-10-25). From `dom/12-single-working-branch` to `dom/21-move-sidecar-guide`, no file of this list changed. `format/versioning.md:74` (the legacy row "Not available."): `heatmap-decode-refinement`, `keypoint-visibility`, `roi-transform-and-source` (MediaPipe-Exporter), `roi-refiner-role` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `pre/resize-affine-person-crop.md:70-74` ("Implementer guidance": the flip-test bullet at `:72`, new bullets): `affine-crop-arithmetic`; `post/pose-schema.md:89-95` (the `pose.decode` fields table and "Method-specific fields"): `heatmap-decode-refinement`, `keypoint-visibility`, `landmark-depth-divisor` (MediaPipe-Exporter); `post/pose-schema.md:117-127` ("Validation rules": `-1` and `-2` owned by `roi-transform-and-source`, `-7`, `-9`, the "See also" line): `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter), `keypoint-visibility`; `post/pose-decode-simcc.md:38` (the "Behaviour" bullet: one proposal replaces it, two add a sentence): `simcc-score-rule`, `keypoint-visibility`; `post/pose-decode-heatmap.md:24` (the "Behaviour" bullet): `heatmap-decode-refinement`; `specs/sidecar/README.md` (the section-map row and the validation-index link after "Coordinate decode", `:93`, `:121`): `keypoint-visibility`, `landmark-extra-outputs` (MediaPipe-Exporter). All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | none. The implementer guidance of `pre.resize.affine_person_crop` names the property ("Compare a host with mmpose at `flip_test=False` ... The effect of the flip test is not measured"). It is not a decision entry. |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (`git status --porcelain` lists one untracked file that this proposal did not read; no tracked file changed). First read at `dom/12-single-working-branch`; pinned at `dom/18-agents-adr-bootstrap-kit` on 2026-10-24. The cited `specs/`, `tools/` and `skellytracker/` lines were checked again at `dom/21-move-sidecar-guide` on 2026-10-25. Between `dom/18-agents-adr-bootstrap-kit` and `dom/21-move-sidecar-guide`, skellytracker moved the guide to `specs/exporter-guide/sidecars/` (skellytracker decisions 0033 and 0034), added skellytracker decision entries 0032 to 0034, and changed only link text under `specs/sidecar/` (`common/identity.md`, `common/sizes-and-artifacts.md`, `format/file-layout.md`, `post/selection-nms.md`, `post/selection-top-k.md`, `TRACEABILITY.md:107-108`, `inventory.yaml` and the two templates). No line that this proposal cites changed: `TRACEABILITY.md:3` has the same text, and the other cited files did not change. Guide citations point to the skellytracker decision 0034 layout (`specs/exporter-guide/sidecars/`). The spec text did not change after the first pin (only link repairs). |

## 1. Gap

| Item | Value |
|---|---|
| Property | The upstream test pipeline runs the model two times on each crop: on the crop and on its horizontal mirror image. It maps the outputs of the mirror pass back to the crop (it reverses the x axis and swaps the left and right keypoints). It averages the two outputs before the decode. The ONNX graph is one forward pass. The sidecar has no field that tells the host to do the second pass. |
| Upstream evidence | **mmpose v1.3.2 (SimCC: RTMPose Halpe26, DWPose, RTMW):** `configs/body_2d_keypoint/rtmpose/body8/rtmpose-m_8xb512-700e_body8-halpe26-256x192.py:103` (`test_cfg=dict(flip_test=True)`); `configs/wholebody_2d_keypoint/rtmpose/ubody/rtmpose-m_8xb64-270e_coco-ubody-wholebody-256x192.py:99` (the DWPose student config, `flip_test=True`); `mmpose/models/pose_estimators/topdown.py:102-105` (`inputs.flip(-1)`, the second feature pass); `mmpose/models/heads/coord_cls_heads/rtmcc_head.py:193-208` (`flip_vectors`, then `(pred + pred_flip) * 0.5` for x and y; RTMW uses `RTMWHead`, `mmpose/models/heads/coord_cls_heads/rtmw_head.py:227-242`, with the same steps); `mmpose/models/utils/tta.py:85-86` (`x_labels[:, flip_indices].flip(-1)`, `y_labels[:, flip_indices]`); `mmpose/datasets/datasets/utils.py:157-161` (`flip_indices` from the `swap` name of each keypoint). **ViTAE-Transformer/ViTPose `c050ed2` (heatmap: ViTPose++):** `README.md:171-178` (the "WholeBody dataset" table links the published WholeBody AP of ViTPose++-S, B, L and H to `configs/wholebody/2d_kpt_sview_rgb_img/topdown_heatmap/coco-wholebody/ViTPose_<size>_wholebody_256x192.py`; the B link at line 176 has the typo `cconfigs/`); `configs/wholebody/2d_kpt_sview_rgb_img/topdown_heatmap/coco-wholebody/ViTPose_small_wholebody_256x192.py:55-59` (the measured S size: `flip_test=True`, `post_process='default'`, `shift_heatmap=True`, no `use_udp`; file fetched from raw.githubusercontent.com at `c050ed2`) and `ViTPose_base_wholebody_256x192.py:55-59` (the same `test_cfg`). Other upstream configs set `shift_heatmap=False` with `use_udp=True`: the ViTAE `c050ed2` COCO body configs `configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/ViTPose_<size>_coco_256x192.py` (all four sizes; `test_cfg` with `flip_test=True`, `post_process='default'`, `shift_heatmap=False`, `use_udp=True` at lines 69-75; `TopDownAffine(use_udp=True)` at lines 103 and 125), which are the base of the 25-point configs (plan 4.3, 4.4; plan O2 option (a), not chosen: plan T9 chose B2); `configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/vitPose+_base_coco+aic+mpii+ap10k+apt36k+wholebody_256x192_udp.py:158-164` (ViTAE `c050ed2`, the ViTPose++ multi-task training config; `README.md:81` links it with the wrong name `ViTPose++_base_..._udp.py`) and easy_ViTPose `bb98603` `easy_ViTPose/configs/ViTPose_common.py:90-96`. This proposal uses the per-dataset eval config, because the README links the published WholeBody AP to it (plan T3). The UDP configs use `shift_heatmap=False`, so the field must have both values. Code: `mmpose/models/detectors/top_down.py:179-188` (`img.flip(3)`, average `* 0.5`); `mmpose/models/heads/topdown_heatmap_simple_head.py:217-224` (`flip_back`, then `output_heatmap[:, :, :, 1:] = output_heatmap[:, :, :, :-1]`); `mmpose/core/post_processing/post_transforms.py:129-146` (`flip_back`: swap the pairs, then reverse the W axis). **This exporter:** `mmdeploy-convert/model_cfgs/rtmw-*.py` (line 117 in the 256x192 configs and line 119 in the 384x288 configs, `flip_test=True`). |
| Nearest section ID | `post.pose.decode.simcc` and `post.pose.decode.heatmap` (via `post.pose.schema`, `pose.decode`) |
| Why the nearest section is wrong | `pose.decode` has `method`, `is_3d`, `depth_unit`, `depth_range` and `coordinate_scale`. No field says that the host runs a second pass, which keypoints change places in a mirror image, or that the host shifts a flipped heatmap. A host that follows the current text runs one pass. Its keypoints differ from the upstream test pipeline. |
| Measured difference (number, image and script) | COCO val2017, all 6352 non-crowd GT person instances with keypoints, GT boxes, body OKS AP on the first 17 keypoints, ONNX Runtime CUDA. The SimCC script calls the mmpose v1.3.2 functions `bbox_xyxy2cs`, `get_warp_matrix` and `get_simcc_maximum` from the downloaded files. It copies the other steps inline from the upstream call sites: the crop aspect fix (`topdown_transforms.py:56-70`), the flip-back (`flip_vectors`, `tta.py:85-86`) and the average (`rtmcc_head.py:207-208`). It does not run mmpose `flip_vectors`, because that function needs torch (see part 4). The ViTPose script calls the ViTAE `c050ed2` functions `get_affine_transform`, `keypoints_from_heatmaps` and `flip_back`. It copies the shift line and the average inline (`topdown_heatmap_simple_head.py:223-224`, `top_down.py:187-188`). (Scratch scripts `simcc_flip.py` and `vitpose_pipelines.py`, not committed, so not evidence; part 5 gives the committed parity plan.) **DWPose-m** (mmpose SDK `end2end.onnx` of `rtmpose-m_simcc-ucoco_dw-ucoco_270e-256x192-c8b76419_20230728`): AP 0.7207 without the flip test, 0.7303 with it (+0.0096); AR 0.7483 / 0.7577. **RTMPose-m Halpe26** (SDK `end2end.onnx` of `rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605`): AP 0.7648 / 0.7726 (+0.0078); AR 0.7915 / 0.7969. The flip test moves the median keypoint by 0.72 px (DWPose-m) and 0.75 px (Halpe26-m). The 95th percentile moves 18.8 px and 59.6 px. **ViTPose++-S wholebody** (easy_ViTPose `vitpose-s-wholebody.onnx`, ViTAE crop and `default` decode, `shift_heatmap=True`): see the ViTPose row below. |
| ViTPose++-S, flip test with `shift_heatmap` | Same image set and metric. easy_ViTPose `vitpose-s-wholebody.onnx` (HF `JunkyByte/easy_ViTPose` `e838052`, SHA-256 `ccac893a8ad6da7d43f9655047acf48e482e66922db7f4273a3b615cea989127`), ViTAE non-UDP crop, `post_process='default'`, flip pairs from the `swap` names of ViTAE `configs/_base_/datasets/coco_wholebody.py`: AP 0.7513 without the flip test, 0.7572 with it and `shift_heatmap=True` (+0.0059); AR 0.7817 / 0.7869. Median keypoint move 0.87 px, 95th percentile 18.7 px. (Scratch script `vitpose_pipelines.py`, variants A and B; not committed, so not evidence.) |
| ViTPose-S 25 points, flip test with `shift_heatmap=False` and `shift_heatmap=True` | Same image set and metric. The model has 25 points; the script maps its 17 body points to COCO-17. easy_ViTPose `vitpose-s-coco_25.onnx` (HF `JunkyByte/easy_ViTPose`, SHA-256 `7c9afc0351b3183c1d71f0b48d52e8be453bc817f0a8ccbe1e43987510b0b05b`), ViTAE non-UDP crop, `post_process='default'`, flip pairs from the `left_`/`right_` names (no upstream pair list exists for this model), `shift_heatmap=False` (the value of the easy_ViTPose config, `ViTPose_common.py:93`): AP 0.7257 without the flip test, 0.7165 with it (-0.0092); AR 0.7610 / 0.7525. Median keypoint move 2.01 px, 95th percentile 30.8 px. (Scratch script `vitpose_pipelines.py`, variants A and B; not committed, so not evidence.) The run of 2026-10-23 (log `full3.log`, plan appendix A.2) adds three variants. B2 (the same non-UDP crop and `default` decode, flip test with `shift_heatmap=True`): AP 0.7385, AR 0.7697 (+0.0128 AP against A, +0.0220 AP against B); median keypoint move against A 1.48 px, 95th percentile 30.56 px. F (ViTAE UDP crop `get_warp_matrix`, DARK-UDP decode, no flip test): AP 0.7061, AR 0.7445. G (as F, flip test with `shift_heatmap=False`, the pipeline of the ViTAE COCO body config): AP 0.7403, AR 0.7730 (+0.0342 AP against F). (Scratch script `vitpose_pipelines.py`, variants B2, F and G; not committed, so not evidence.) |
| Row in "Considered and deliberately not added", and the evidence that a model needs it now | none. The table has no flip-test row. |

On the models whose upstream test config sets the flip test (the two SimCC models, and ViTPose++ with
`shift_heatmap=True`), the flip test adds about 0.006 to 0.010 AP. That is near the size of the fp16
gate of this exporter (0.01, OpenMMLab-Exporter D5). A host that follows the sidecar cannot reproduce the published
accuracy of these models without the flip test.

On the 25-point ViTPose model, with the non-UDP crop, `shift_heatmap=False` and pairs from the names
(variant B), the flip test lowers AP by 0.009. The missing shift causes this drop: B2, the same
pipeline with `shift_heatmap=True`, gives +0.0220 AP against B (plan appendix A.2). The easy_ViTPose
config and the ViTAE COCO body configs set `shift_heatmap=False` only with `use_udp=True`
(`ViTPose_common.py:90-96`; `ViTPose_<size>_coco_256x192.py:69-75`). With the matching pipeline, the
flip test adds +0.0128 AP (B2 against A, non-UDP) or +0.0342 AP (G against F, UDP). Thus the correct
`shift_heatmap` value depends on the crop and decode pipeline. The sign of the effect depends on the
settings. The `shift_heatmap` and `flip_pairs` values of a sidecar must come from a measured upstream
pipeline, not from the default. For the 25-point model, plan T9 (pipeline B2) sets `shift_heatmap: true`.

## 2. Spec change

### 2.1 Sections

New section `post.pose.flip_test`, title "Flip test", file `specs/sidecar/post/pose-flip-test.md`.

Front matter:

```yaml
id: post.pose.flip_test
title: Flip test
kind: postprocessor
since: vNEXT
changed_in: []
selectors:
  - pose.decode.flip_test
implemented_by:
  validate: missing
  decode: missing
external_impl: []
tests: []
vectors: vectors/post.pose.flip_test.yaml
status: {spec: draft, validate: missing, decode: missing}
```

The spec state is `draft`, because the doc tests allow only `stable` or `draft`
(skellytracker `tools/tests/test_traceability.py:47, 190-198`). `proposed` is the status of a decision
entry, not of a section.

Row in the section map (`specs/sidecar/README.md`, after `post.pose.decode.coordinate`):

```text
| `post.pose.flip_test` | [post/pose-flip-test.md](post/pose-flip-test.md) | Flip test |
```

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `post.pose.schema` (`post/pose-schema.md`) | `pose.decode` fields table | Add the row `pose.decode.flip_test` (object, no): "When present, the host runs the flip test before the decode. See Flip test (`pose-flip-test.md#fields`)." Add the link "Flip test" to the list of decode methods: "The flip test applies before each method." |
| `post.pose.schema` | "Validation rules" | No rule changes. Add "See also Flip test (`pose-flip-test.md#validation-rules`)." |
| `post.pose.decode.simcc` (`post/pose-decode-simcc.md`) | "Behaviour" | Add one sentence at the start: "When `pose.decode.flip_test` is present, the host decodes the averaged outputs of the Flip test (`pose-flip-test.md#behaviour`)." |
| `post.pose.decode.heatmap` (`post/pose-decode-heatmap.md`) | "Behaviour" | Add the same sentence. |
| `pre.resize.affine_person_crop` (`pre/resize-affine-person-crop.md`) | "Implementer guidance", first bullet (line 72) | Replace the bullet "Compare a host with mmpose at `flip_test=False` ... The effect of the flip test is not measured" with a link to Flip test (`../post/pose-flip-test.md`) and the measured effect (part 1). This also removes the statement "The sidecar has no field for the flip test", which the new field makes false. Keep the bullet at line 73: it records a parity result at `flip_test=False` on both sides and stays true. The SimCC section gets no guidance edit: it has no flip-test bullet, and its "Behaviour" sentence (row above) links it to the new section. |
| `specs/sidecar/README.md` | Section map; "Validation rules" (the validation index) | Add the section row. Add the link to the rules of `post.pose.flip_test`. |
| `specs/sidecar-spec.md` | The permanent index | No edit. The index keeps only the headings of the old single-file spec (skellytracker decision 0013, `notes/decisions/0013-spec-structure.md:18-20`; `specs/exporter-guide/sidecars/where-to-read.md:24`). The section map row gives the link to the new section. |
| `specs/sidecar/TRACEABILITY.md` | Generated matrix | Do not edit it by hand (`TRACEABILITY.md:3`). After the section file and its front matter are in place, run `python tools/sidecar_trace.py matrix`. This adds the `post.pose.flip_test` row. `tools/tests/test_traceability.py::test_traceability_equals_a_fresh_generation` (line 468) must pass. |
| `format.versioning` (`format/versioning.md`) | "Legacy behaviour" table (lines 72-74) | Add `pose.decode.flip_test` to the existing row "`boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`" ("Not available." / "Available."). Do not add a link to the "Version-aware compatibility" list: the field has no legacy meaning to describe, and `stretch` and `fit` are not in that list either. See 2.6. |
| `specs/sidecar/changelog.md` | "Summary of changes", `schema_version` history | Add the summary row of 2.7. Append the history sentence of 2.7 to the existing `vNEXT` row (line 68). |
| `common.outputs`, `common.identity`, `format.file_layout`, `post.unprojection` | | No edit. The flip test adds no output semantic, no role, no path and no coordinate change. |

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `pose.decode.flip_test` | object | no | When this field is present, the host runs the flip test. When it is absent, the host runs one forward pass for each crop. |
| `pose.decode.flip_test.flip_pairs` | array[[name, name]] or `$ref` | yes, in `flip_test` | The pairs of `pose.tracked_points` names that change places in a horizontal mirror image, for example `[left_eye, right_eye]`. A name that is in no pair is its own partner, for example `nose`. The order of the two names in a pair has no effect. |
| `pose.decode.flip_test.shift_heatmap` | bool | no | Only for `pose.decode.method: heatmap`. The default is `false`. When the value is `true`, the host moves the flipped-back heatmap one column to the right before the average. The default is not a measured value for a heatmap model. The author writes the value of the upstream test config. A wrong `shift_heatmap` or wrong `flip_pairs` can make the flip test lower the AP (part 1, 25-point row). |

### 2.3 Behaviour

The host runs the flip test after the preprocessing (after the normalization) and before the decode
of `pose.decode.method`. The flip test does not change the unprojection: the keypoints of the decode
are in the model-input pixels of the crop, as before.

```text
x       = the preprocessed batch, shape (N, 3, T_h, T_w), after the normalization
x_flip  = x with the width axis reversed: x_flip[n, c, r, w] = x[n, c, r, T_w - 1 - w]
y       = the outputs of the model for x
y_flip  = the outputs of the same artifact for x_flip

perm[i] = j   when [tracked_points[i], tracked_points[j]] is a pair in flip_pairs (in either order)
perm[i] = i   when tracked_points[i] is in no pair

method simcc:
    simcc_x_back[n, k, b] = simcc_x_flip[n, perm[k], X_bins - 1 - b]
    simcc_y_back[n, k, b] = simcc_y_flip[n, perm[k], b]
method heatmap:
    heatmap_back[n, k, r, w] = heatmap_flip[n, perm[k], r, W - 1 - w]
    if shift_heatmap:
        heatmap_back[n, k, r, w] = heatmap_back[n, k, r, w - 1]   for w = W - 1 down to 1
        (column 0 keeps its value)

average, for each output, in float32, in this order:
    out = (y + y_back) * 0.5

decode out with pose.decode.method
```

- The host can run `x` and `x_flip` in one batch or in two batches. The batch of each run must agree
  with the input shape of the artifact: a static-batch artifact takes exactly its declared batch. The
  choice does not change the algorithm. The outputs can differ only by the numeric noise of the
  runtime, for example a different kernel choice on a GPU execution provider (see
  Batching (`../common/batching.md#implementer-guidance`)). A conformance test must not require
  bit-identical outputs between the two choices. The upstream runs two separate forward passes
  (mmpose v1.3.2 `topdown.py:103-104`; ViTAE `top_down.py:172, 181`).
- The keypoint scores of the decode come from the averaged outputs.
- The flip test applies to the outputs of the model. It does not apply to the decoded keypoints.

**Inverse.** None. The flip test does not change a coordinate system.

### 2.4 Validation rules

- [ ] `V-post.pose.flip_test-1` **(vNEXT)** If `pose.decode.flip_test` is present, `pose.estimator_type`
  must be `top_down_single_person` or `top_down_multi_person`. `pose.decode.method` must be `simcc` or
  `heatmap`. `pose.decode.is_3d` must be `false`.
- [ ] `V-post.pose.flip_test-2` **(vNEXT)** If `pose.decode.flip_test` is present, it must have
  `flip_pairs`. Each entry of `flip_pairs` must have exactly two different names. Each name must be in
  `pose.tracked_points`. A name must be in one pair at most.
- [ ] `V-post.pose.flip_test-3` **(vNEXT)** `pose.decode.flip_test.shift_heatmap` is valid only when
  `pose.decode.method` is `heatmap`. If it is present, it must be a boolean.

Existing rules that name a value of this change: none. `V-post.pose.schema-7` (the outputs of each
decode method) does not change: the flip test adds no output. `V-pre.resize.affine_person_crop-2` does
not change.

Follow-up, not in this proposal: a flip test for `coordinate` and for 3D SimCC (`simcc_z`). No model
in scope needs it. Rule 1 rejects these cases.

### 2.5 Selectors

`pose.decode.flip_test` (present).

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` does not use `pose.decode.flip_test`. Such a sidecar runs
  one forward pass. Its meaning does not change.
- The change goes into the `vNEXT` revision.
- `pose.decode.flip_test` is not available when `schema_version < vNEXT`. Add it to the "Not
  available" row of the "Legacy behaviour" table in `format.versioning` (`format/versioning.md:72-74`),
  as `stretch`, `fit` and `packed_keypoints` are. Rules `V-post.pose.flip_test-1` to `-3` apply only
  at `vNEXT`.
- The new section file has a "Legacy behaviour" heading with the text of `pre/resize-stretch.md:46`
  and `pre/resize-fit.md:59`: "Availability before `vNEXT`: Schema
  versioning (`../format/versioning.md#legacy-behaviour`)."
- The validator: the spec has no rule that rejects a vNEXT-only field in a legacy sidecar. The
  validator model accepts `stretch` and `fit` with no check of `schema_version`
  (`skellytracker/core/sidecar/model.py:79`; the only `schema_version` checks in `model.py` are at
  lines 477-483, the pattern and the stable version). This proposal adds no such rule for `pose.decode.flip_test`. If the
  skellytracker review wants a check, the rule is: "`pose.decode.flip_test` must be absent when
  `schema_version < vNEXT`" (with no **(vNEXT)** mark).

### 2.7 Changelog row

`schema_version` history: do not add a row. The table has one `vNEXT` row (`changelog.md:68`).
Append this sentence to the end of its cell, in its "Added ..." style:

```text
Added `pose.decode.flip_test` (`flip_pairs`, `shift_heatmap`): the host runs the flip test of a top-down pose estimator before the decode.
```

Summary of changes (the five columns of `changelog.md:16`: #, Area, Change, Driven by, Section):

```text
| N | Pose | New `pose.decode.flip_test` (`flip_pairs`, `shift_heatmap`). A top-down SimCC or heatmap sidecar tells the host to run the model on the crop and on its mirror image, map the mirror outputs back with `flip_pairs`, and average the outputs before the decode. | RTMPose Halpe26, DWPose, RTMW, ViTPose++, ViTPose 25 points (upstream test pipelines use `flip_test=True`) | [Flip test](post/pose-flip-test.md) |
```

`N` is the next free number when this proposal merges. Rows 1 to 19 exist (`changelog.md:18-36`).
13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order. Do not fix `N` before
the merge.

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/sidecar/proposals/pose-decode-flip-test/proposal.md` |
| Target file in skellytracker | `specs/sidecar/reference/post_pose_flip_test.py` |
| Functions (one for each algorithm) | `flip_permutation` (perm from `tracked_points` and `flip_pairs`), `flip_input` (reverse the width axis), `flip_back_simcc` (reorder, reverse the X bins), `flip_back_heatmap` (reorder, reverse W, optional shift), `flip_average` (`(y + y_back) * 0.5` in float32), `flip_test` (the full step with a `run` function) |

Source commit: none (no host code). This exporter has no pose decode on its host side yet. The
functions come from the text of part 2.

```python
"""Reference implementation of the proposed section post.pose.flip_test.

This file uses ASD-STE100 Simplified Technical English.

- Section ID: post.pose.flip_test (proposed; OpenMMLab-Exporter proposal pose-decode-flip-test,
  specs/sidecar/proposals/pose-decode-flip-test/proposal.md).
- Source commit: none (no host code). The functions come from the text of part 2 of the proposal.
- Vectors: this file makes the vectors of part 4. They are unverified: no host implementation.
  All 8 cases of part 4 pass against this file (run of 2026-10-23, recorded in part 4). Each input
  key of a case is an argument of the function. A runner gives numeric lists as float32 arrays.
- Parity result: to run.

The functions use only NumPy and the Python standard library. Each function implements one step of
the behaviour in part 2.3 of the proposal.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def flip_permutation(tracked_points: Sequence[str], flip_pairs: Sequence[Sequence[str]]) -> list[int]:
    """post.pose.flip_test: return perm, where perm[i] is the index of the mirror partner of keypoint i.

    A keypoint that is not in a pair is its own partner.
    """
    index = {name: i for i, name in enumerate(tracked_points)}
    perm = list(range(len(tracked_points)))
    for first, second in flip_pairs:
        perm[index[first]] = index[second]
        perm[index[second]] = index[first]
    return perm


def flip_input(x: np.ndarray) -> np.ndarray:
    """post.pose.flip_test: reverse the width axis of the preprocessed batch (N, 3, T_h, T_w)."""
    return np.ascontiguousarray(x[..., ::-1])


def flip_back_simcc(simcc_x_flip: np.ndarray, simcc_y_flip: np.ndarray,
                    perm: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.flip_test: map the SimCC outputs of the flipped pass back to the original crop.

    simcc_x: reorder the keypoints with perm, then reverse the X_bins axis.
    simcc_y: reorder the keypoints with perm.
    """
    perm = list(perm)
    return (np.ascontiguousarray(simcc_x_flip[:, perm, ::-1]),
            np.ascontiguousarray(simcc_y_flip[:, perm, :]))


def flip_back_heatmap(heatmap_flip: np.ndarray, perm: Sequence[int], shift_heatmap: bool = False) -> np.ndarray:
    """post.pose.flip_test: map the heatmap output of the flipped pass back to the original crop.

    Reorder the keypoints with perm, then reverse the W axis. When shift_heatmap is true, move each
    row one column to the right: column c + 1 gets the value of column c, and column 0 keeps its value.
    """
    back = np.array(heatmap_flip[:, list(perm), :, ::-1])
    if shift_heatmap:
        back[:, :, :, 1:] = back[:, :, :, :-1].copy()
    return back


def flip_average(output: np.ndarray, output_back: np.ndarray) -> np.ndarray:
    """post.pose.flip_test: (output + output_back) * 0.5, in float32, in this order."""
    total = output.astype(np.float32) + output_back.astype(np.float32)
    return (total * np.float32(0.5)).astype(np.float32)


def flip_test(run, x: np.ndarray, method: str, perm: Sequence[int], shift_heatmap: bool = False):
    """post.pose.flip_test: the full step. run(x) returns the raw outputs of one forward pass.

    method "simcc": run returns (simcc_x, simcc_y). method "heatmap": run returns heatmap.
    The return value has the same form. The decode of pose.decode.method then reads it.
    """
    output = run(x)
    output_flip = run(flip_input(x))
    if method == "simcc":
        back_x, back_y = flip_back_simcc(output_flip[0], output_flip[1], perm)
        return flip_average(output[0], back_x), flip_average(output[1], back_y)
    if method == "heatmap":
        return flip_average(output, flip_back_heatmap(output_flip, perm, shift_heatmap))
    raise ValueError(f"post.pose.flip_test does not apply to pose.decode.method {method!r}")


__all__ = [
    "flip_average",
    "flip_back_heatmap",
    "flip_back_simcc",
    "flip_input",
    "flip_permutation",
    "flip_test",
]
```

## 4. Vectors

The heatmap cases also ran through the upstream ViTAE `flip_back` (`post_transforms.py:129-146`) and
the shift line of `topdown_heatmap_simple_head.py:223-224`. They gave the same arrays. The SimCC cases
did not run through mmpose `flip_vectors`, because it needs torch.

Run of 2026-10-23: all 8 cases below pass against the part 3 code of `specs/sidecar/proposals/pose-decode-flip-test/proposal.md`.
The runner reads the YAML block of this part, loads the reference file with
`importlib.util.spec_from_file_location`, converts each numeric list of `input` to a float32 NumPy
array, calls `function(**input, **params)`, and requires each array result to be float32 and equal
to `expect` (exact). Command: `uv run --project <exporter repo> python -I run_part4_vectors.py
<this file> <reference file>` (scratch script, not committed). Output: `8/8 pass`.

```yaml
section: post.pose.flip_test
spec_revision: vNEXT
generated_by: the part 3 code of `specs/sidecar/proposals/pose-decode-flip-test/proposal.md`
unverified: no host implementation in an exporter or in skellytracker
# The heatmap cases agree with ViTAE-Transformer/ViTPose c050ed2 flip_back + shift_heatmap (upstream
# code, not an implementation of the spec).
# A runner converts each list in input to a float32 NumPy array. flip_average casts its inputs to
# float32. Each input key is an argument of the function.
cases:
  - id: perm-one-pair
    function: flip_permutation
    params: {}
    input: {tracked_points: [nose, left_eye, right_eye], flip_pairs: [[left_eye, right_eye]]}
    expect: {perm: [0, 2, 1]}
  - id: perm-pair-order-reversed
    function: flip_permutation
    params: {}
    input: {tracked_points: [nose, left_eye, right_eye], flip_pairs: [[right_eye, left_eye]]}
    expect: {perm: [0, 2, 1]}
  - id: perm-no-pairs
    function: flip_permutation
    params: {}
    input: {tracked_points: [nose, left_eye, right_eye], flip_pairs: []}
    expect: {perm: [0, 1, 2]}
  - id: input-width-reversed
    function: flip_input
    params: {}
    input: {x: [[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]]]}
    expect: {x_flip: [[[[3.0, 2.0, 1.0], [6.0, 5.0, 4.0]]]]}
  - id: simcc-back
    function: flip_back_simcc
    params: {perm: [0, 2, 1]}
    input:
      simcc_x_flip: [[[0.0, 1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0], [8.0, 9.0, 10.0, 11.0]]]
      simcc_y_flip: [[[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]]]
    expect:
      simcc_x_back: [[[3.0, 2.0, 1.0, 0.0], [11.0, 10.0, 9.0, 8.0], [7.0, 6.0, 5.0, 4.0]]]
      simcc_y_back: [[[0.0, 1.0], [4.0, 5.0], [2.0, 3.0]]]
  - id: heatmap-back-shift-false
    function: flip_back_heatmap
    params: {perm: [1, 0], shift_heatmap: false}
    input: {heatmap_flip: [[[[1.0, 2.0, 3.0]], [[4.0, 5.0, 6.0]]]]}
    expect: {heatmap_back: [[[[6.0, 5.0, 4.0]], [[3.0, 2.0, 1.0]]]]}
  - id: heatmap-back-shift-true
    function: flip_back_heatmap
    params: {perm: [1, 0], shift_heatmap: true}
    input: {heatmap_flip: [[[[1.0, 2.0, 3.0]], [[4.0, 5.0, 6.0]]]]}
    expect: {heatmap_back: [[[[6.0, 6.0, 5.0]], [[3.0, 3.0, 2.0]]]]}
  - id: average-float32
    function: flip_average
    params: {}
    input: {output: [1.0, 0.1], output_back: [2.0, 0.2]}
    expect: {average: [1.5, 0.15000000596046448]}
```

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | Compare against the upstream library on the same boxes, with the flip test on both sides. (1) Unit: model-input (crop) pixels. The script maps both keypoint sets to crop pixels with the inverse of the crop-to-source mapping of each crop (`crop = (source - center + 0.5 * scale) * input_size / scale`, for each axis; mmpose v1.3.2 gives `scale` in pixels, ViTAE gives it in units of 200 px, so use `scale * 200` there). (2) SimCC families (RTMPose Halpe26, `dwpose-wholebody133-ubody`): per-point difference at most the "Export error" row of this table plus `1 / simcc_split_ratio` crop px, which is 0.5 crop px for `simcc_split_ratio=2.0` (one bin; skellytracker `post/pose-decode-simcc.md:57`; the codec of each config). (3) Heatmap families (`vitposepp-wholebody133`, the ViTAE eval pipeline, plan T3; `vitpose-coco25`, pipeline B2, plan T9, with the created config of plan 4.4): per-point difference at most the "Export error" row plus one heatmap cell, `input_width / heatmap_width` = 192 / 48 = 4 crop px (`ViTPose_small_wholebody_256x192.py:62-63`, `image_size=[192, 256]`, `heatmap_size=[48, 64]`; `test_cfg` `post_process='default'`, `shift_heatmap=True`, lines 55-59). The 25-point model has the same sizes: the base config `ViTPose_small_coco_256x192.py` lines 78-79, which the created config keeps (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), secondary). Its created config sets `use_udp=False` and `shift_heatmap=True` (plan T9, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). (4) Flat peaks: a flat SimCC or heatmap peak can change bin. Keypoints with an upstream score of 0.2 or less are not in the per-point gate (0.2 is the default `keypoint_score_thr` of mmpose v1.3.2 `mmpose/evaluation/metrics/coco_metric.py:101` and the `vis_thr` of `ViTPose_small_wholebody_256x192.py:71`). The script counts and records these points. Secondary evidence for the rule: `pre/resize-affine-person-crop.md:73` (2.9 px on one crop with mean score 0.10, where a flat SimCC peak changed bin; max 2.4 px on confident crops; an RTMPose hand model at `flip_test=False`, so it does not measure the flip test). (5) The aggregate gate: body OKS AP on the parity image set, the difference at most 0.005 (the fp32 gate of this exporter, OpenMMLab-Exporter D5). For `vitpose-coco25`, gate (5) uses only the 17 COCO points with the COCO sigmas, because `neck` and mid `hip` have no OKS sigma (plan O8 and step 6, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The score limit of (4) is the choice of the proposer, set before the run. |
| Test images, and the branch that each image runs | COCO val2017 images with GT person boxes. Each image runs both passes. Include: a crop that touches the image border (the mirror pass then sees the zero border on the other side); a portrait box and a box wider than 192:256 (both aspect branches of `affine_person_crop`); a crowded image (left/right swaps of near persons). COCO val2017 image IDs (annotation IDs): 311394 (448609, border crop: the 1.25x crop window fitted to 192:256 reaches x = -56.8 and y = -82.5 in a 480 by 640 image), 173830 (521392, portrait box: h/w = 1.668, window inside the image), 80932 (188312, a box wider than 192:256: h/w = 1.069, window inside the image), 413552 (2203726, 2203727, crowded: two person boxes that overlap). Chosen on 2026-10-25 from `../_datasets/coco_data/coco_val2017/coco/annotations/person_keypoints_val2017.json` before the run, with a scratch script (not committed): non-crowd person annotations with 10 or more labelled keypoints; the crop window is the `affine_person_crop` arithmetic (mmpose v1.3.2 `bbox_xyxy2cs`, padding 1.25, aspect fix to 192:256); for each branch the annotation with the largest area; for the crowded case the overlapping pair with the largest area sum. |
| Upstream reference | mmpose v1.3.2 in the Docker image of this exporter, `inference_topdown` with `test_cfg.flip_test=True` (the config default), for RTMPose Halpe26 and `dwpose-wholebody133-ubody`. ViTAE-Transformer/ViTPose `c050ed2` (mmpose 0.x) in the `/opt/vitae` environment of the exporter image (plan T12; no second image), for `vitposepp-wholebody133` (the ViTAE eval pipeline, plan T3; config `ViTPose_<size>_wholebody_256x192.py`) and for `vitpose-coco25` (pipeline B2, plan T9; the created config `ViTPose_<size>_coco25_256x192.py` of plan 4.4, not written yet, plan step 5.5). |
| Export error | to run |
| Preprocessed input | to run (expect 0 for the mirror input: a reversal of an array) |
| Row count for each image | to run (one pose for each box on both sides) |
| Final outputs in source-image coordinates | to run |
| Result | to run |
| Script path in the exporter repo | `notes/decisions/scripts/pose_flip_test_parity.py` (planned, not written) |
| Exporter commit of the script | unknown (the script is not written yet) |
| Command | `uv run python notes/decisions/scripts/pose_flip_test_parity.py --family <family> --size m` (planned) |

The script will use the reference file of part 3 for the flip test, and the host implementation of
`pre.resize.affine_person_crop`, `pre.normalize`, `post.pose.decode.simcc` (the SimCC families) and
`post.pose.decode.heatmap` (the heatmap families `vitposepp-wholebody133` and `vitpose-coco25`, plan step 5c.1) for the other
steps.
The upstream side runs in the container (torch is not on the host). The script compares the two
keypoint sets and the two OKS AP values.

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | A new module `skellytracker/core/detectors/processing/flip_test.py` with the functions of part 3: `flip_permutation`, `flip_input`, `flip_back_simcc`, `flip_back_heatmap`, `flip_average`. |
| Dispatch point | The keypoint detectors run one session call in `detect` and decode in `postprocess` (for example `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`, `detect` at lines 108-120 (session call at line 118) and `postprocess` at lines 81-106 (`simcc_pose_decode` call from line 88)). When `pose.decode.flip_test` is present, `detect` runs the session a second time on `flip_input(inp)`, and the outputs go through `flip_back_*` and `flip_average` before `simcc_pose_decode`. A generic top-down detector is for the implementer: today each family has its own detector class. |
| Validator changes (`model.py`, with rule IDs) | Add `FlipTestSpec` (`flip_pairs: list[tuple[str, str]]`, `shift_heatmap: bool = False`) and the field `flip_test: FlipTestSpec | None = None` to `PoseDecodeSpec` (`skellytracker/core/sidecar/model.py:259-278`). Check `V-post.pose.flip_test-3` in `PoseDecodeSpec._check_decode`. Check `V-post.pose.flip_test-1` and `V-post.pose.flip_test-2` in `SidecarModel`, because they need `pose.estimator_type` and `pose.tracked_points`. |
| Tests | The vectors of part 4 (`specs/sidecar/vectors/post.pose.flip_test.yaml`). A golden parity test for one SimCC model with the flip test (the tests in `skellytracker/tests/sidecar/test_rtmw_sidecar.py` show the pattern). |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py` (`PoseDecodeSpec`, `SidecarModel`); the `detect` method of each top-down keypoint detector (`rtmpose/body`, `rtmpose/face`, `rtmpose/hand`, `rtmw/wholebody`); `skellytracker/core/detectors/processing/simcc_decode.py` (`simcc_pose_decode` reads the averaged outputs, no change to its code). |

## 7. Exporter impact

| Exporter | Affected sidecars | Change | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` (all five configs have `flip_test=True`), and the new families `rtmpose-halpe26`, `dwpose-wholebody133-ubody` and `vitposepp-wholebody133`; the new 25-point ViTPose family `vitpose-coco25` (plan T14) | New fields: write `pose.decode.flip_test` with `flip_pairs` from the `swap` names of the upstream dataset metainfo. For `vitpose-coco25`, write `pose.decode.flip_test` with `flip_pairs` derived from the `left_`/`right_` names (no upstream list; plan 4.4, row "25-point dataset info"). Its `shift_heatmap` is `true` (plan T9). Regenerate `rtmw-wholebody133.yaml` (`rtmw/identity.py:35`, `SIDECAR_FILENAME`, T14 change of `d0f4343`). OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no RTMW sidecar until the RTMW intake is `describes`, so the regeneration happens at that later round. | The host has no pose decode yet. The parity script of part 5 uses the reference file. |
| Roboflow-Exporter | none (no top-down pose model) | none | none |
| Ultralytics-Exporter | none (YOLO26-pose is bottom-up) | none | none |
| Qualcomm-Exporter | MediaPipe landmark models: unknown (for the implementer: the MediaPipe pipeline has no flip test, to check) | none expected | none |
| MediaPipe-Exporter | as Qualcomm-Exporter | none expected | none |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-hand`, `rtmpose-face`, `rtmw-wholebody` (`v2024.09.1019`) | none. Their legacy meaning does not change: one forward pass. | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change: the host runs one pass (the near-miss of today) | A host cannot reproduce the upstream test accuracy. The difference is about 0.006 to 0.010 AP on the measured models whose upstream test config sets the flip test. On the 25-point ViTPose model with a matching pipeline, it is 0.0128 (pipeline B2, chosen by plan T9) or 0.0342 (pipeline G, the ViTAE COCO body config, not chosen) AP. | Part 1 |
| Put the flip and the average into the ONNX graph (a two-branch export) | The graph would do two passes always, also for a host that wants speed. The exported graph is the single forward pass of the upstream model. A two-branch graph needs either an edit to the upstream config, which OpenMMLab-Exporter decision 0007 does not allow, or a new graph-edit creation step after the mmdeploy export in every family. The batch of the artifact would then mean two crops for each person. The sidecar also cannot tell the host that the graph contains the flip. (The one-pass point is the argument of the proposer. No contract of this exporter states a rule of one pass for each crop.) | OpenMMLab-Exporter decision 0007 (`notes/decisions/0007-upstream-configs-only.md`, upstream configs unchanged); `pipeline/ARTIFACT_CONTRACT.md:12-23` (the creation chain of a raw export) and `:27-29` (the published fp32 is a byte-identical copy of the raw export; do not edit a published fp32 graph); OpenMMLab-Exporter D9 (`notes/decisions/migration-decisions.md:63`, the raw export chain) |
| Derive the pairs from the names (`left_*` and `right_*`) | COCO-WholeBody face points have pairs with no side in the name (`face-0` and `face-16`). Halpe26 and COCO-WholeBody give the pairs as `swap` names in the dataset metainfo, not as a name rule. | mmpose v1.3.2 `configs/_base_/datasets/coco_wholebody.py` (`swap` of the face points); `mmpose/datasets/datasets/utils.py:157-161` |
| A boolean `flip_test: true` with the pairs in a shared file that the host finds by `landmark_schema` | `landmark_schema` is optional and has no closed set. The host would need a pair table for each schema. A `$ref` to a shared pair file gives the same reuse with an explicit file. | `post.pose.schema` (`landmark_schema` is an optional string) |
| An index form (`flip_indices: [0, 2, 1, ...]`, the mmpose form) | It repeats the order of `tracked_points` and breaks silently when the order changes. Name pairs follow the rule that `tracked_points` names are the keys of the pose block. | skellytracker decision 0003 (`tracked_points` in native order) |
| A general test-time-augmentation block (scales, flips) | No model in scope uses another augmentation. Add it later as a non-breaking change if a model needs it. | none |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. (All four intakes give the file name in row K4a and in "Proposals and reference files": the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts); the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts). The RTMW intake also links it: the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts).)
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plan folder of OpenMMLab-Exporter (plan facts).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a (no pixel case)
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo. n/a (`to run`)
- [x] No file in skellytracker changed.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal. The skellytracker
session wrote this list. It is not part of the exporter proposal.

**Parts**

- [ ] Run the parity test of part 5. The export error, the preprocessed input, the row count, the
  final outputs and the result are `to run`. The script
  `notes/decisions/scripts/pose_flip_test_parity.py` of OpenMMLab-Exporter is not written. Commit it,
  and give its commit in part 5.
- [ ] Add the front-matter edit `changed_in: [vNEXT]` of `post/pose-decode-simcc.md` and
  `post/pose-decode-heatmap.md` to part 2.1. Both files have `changed_in: []`. The new "Behaviour"
  sentence changes their meaning.
- [ ] Correct the `post.pose.schema` edit text of part 2.1: "The flip test applies before each
  method." Rule `V-post.pose.flip_test-1` allows only `simcc` and `heatmap`.
- [ ] Give the width axis for each `input.layout` in part 2.3, or make rule `V-post.pose.flip_test-1`
  require `input.layout: NCHW`. `common.input` allows `NHWC`. Part 2.3 reverses the last axis of
  `(N, 3, T_h, T_w)`. For an `NHWC` input, `flip_input` (`x[..., ::-1]`) reverses the colour channels,
  not the width.
- [ ] Make the text "average, for each output" of part 2.3 exact. Part 2.3 maps back only `simcc_x`,
  `simcc_y` and `heatmap`. Say that the average applies only to these pose outputs, or say what the
  host does with the other outputs.
- [ ] State the `keypoint_axis` that part 2.3 requires. Part 2.3 puts the keypoints on axis 1.
  `post.pose.schema` makes `keypoint_axis` an output field with the default `1`.
- [ ] Give the `$ref` form of `flip_pairs` in part 2.2. At `vNEXT`, a `$ref` mapping has exactly the
  keys `$ref` and `sha256` (`format.composition`). `format.file_layout` puts shared fragments under
  `detectors/shared/`. Name the subfolder for the pair fragments.
- [ ] Update the header row "Exporter commit". It says that the branch is not pushed. Commit
  `f3aeb47` is now on `origin/main` of OpenMMLab-Exporter.

**Evidence**

- [ ] Commit the scripts of the part 1 measurements, and give their commit. The AP numbers of part 1
  come from scripts that are not committed. They are not evidence.
- [ ] Mark each plan fact in part 1 `(secondary)`, as the template requires. Part 1 cites the plan
  items T3, T9, 4.3, 4.4, O2 and appendix A.2 with no mark. Part 5 marks its plan facts.
- [ ] Give a primary source for `shift_heatmap: true` of `vitpose-coco25`. Only a user decision of the
  untracked pose-models plan of OpenMMLab-Exporter (plan T9) gives the value. The created 25-point test
  config is not written.
- [ ] Give the source of the `flip_pairs` of `vitpose-coco25`. No upstream pair list exists. The pairs
  come from the `left_` and `right_` names. Part 8 rejects names as a spec rule. The authoring
  guidance must say when an author can derive pairs from names.
- [ ] Verify the vectors against a host implementation. Part 4 is `unverified`. The SimCC cases did not
  run through mmpose `flip_vectors`. The result "8/8 pass" comes from a runner that is not committed.
- [ ] Check the line numbers of the ViTAE shift line (`topdown_heatmap_simple_head.py:223-224`). An
  approximate count found the line near 224-225.
- [ ] Give the full SHA of each upstream source for its permalink: mmpose v1.3.2,
  ViTAE-Transformer/ViTPose `c050ed2` and easy_ViTPose `bb98603`. Each SHA must be on the default
  branch of its repo.

**Template checklist**

- [ ] "Part 2.1 lists each place that the change edits" is ticked. Part 2.1 does not list the
  `changed_in` edits (see **Parts**) and the `tools/` edits (see **Vectors and tooling**).
- [ ] "Part 1 cites primary evidence" is ticked. The part 1 numbers have no committed script, and the
  plan facts of part 1 have no `(secondary)` mark.
- [ ] "Part 4 gives `verified_against`, or `unverified: <reason>`" is met. The part 4 YAML does not
  agree with `tools/tests/test_vectors.py` (see **Vectors and tooling**).
- [ ] "Part 5 gives the numbers ... or says `to run`" is met with `to run`. The template says that such
  a proposal is not ready for the user to accept.
- [ ] Add a case for each branch of `flip_test`, as the template requires: `simcc`, `heatmap` and the
  `ValueError` for a different method. Add a case with `N > 1` and with two pairs.

**Vectors and tooling**

- [ ] Generate the vector file with `tools/make_vectors.py`. `generated_by` must be
  `tools/make_vectors.py`. The case key `function` is not in `CASE_KEYS`. Add the builder to the
  `BUILDERS` dict.
- [ ] Give a `tolerance` to each case whose `expect` holds a float, or make the generator write
  integers. Five cases need it: `input-width-reversed`, `simcc-back`, `heatmap-back-shift-false`,
  `heatmap-back-shift-true` and `average-float32`. Part 4 requires exact equality.
- [ ] Define how a builder maps a tuple result to the named `expect` keys, for example
  `simcc_x_back` and `simcc_y_back` of `flip_back_simcc`.
- [ ] Add a test in `tools/tests/` that runs the reference functions against the vectors (skill
  `change-sidecar-spec`, Procedure B). No such test exists. Decide how the tools import
  `specs/sidecar/reference/`. This reference is a first file in that folder, and CI then runs `ruff`
  on it.
- [ ] Regenerate `TRACEABILITY.md` with `tools/sidecar_trace.py matrix`. Put the section-map row in the
  order that `tools/tests/test_traceability.py` checks.
- [ ] Keep "**Inverse.** None." as bold text. An `Inverse` heading in a `postprocessor` section fails
  `tools/tests/test_traceability.py`.

**Decisions for the user**

- [ ] Confirm the user decisions that only the untracked pose-models plan of OpenMMLab-Exporter
  records: T3 (the ViTAE eval pipeline for ViTPose++), T9 (pipeline B2 for `vitpose-coco25`), T11
  (the family `vitposepp-wholebody133`), T12 (no second image) and T14 (the family IDs). The proposal
  cites them as plan facts.
- [ ] Is `flip_pairs: []` valid? The vector `perm-no-pairs` uses it. Rule `V-post.pose.flip_test-2`
  does not say.
- [ ] Must a rule reject `pose.decode.flip_test` when `schema_version < vNEXT`? Part 2.6 leaves this
  to review. The proposals use different policies. Decide one policy for all proposals.
- [ ] Must the new "Legacy behaviour" heading get a link in "Version-aware compatibility"? The skill
  `change-sidecar-spec` requires it. The proposal follows `stretch` and `fit`, which have no link.
- [ ] Is `pose.decode.flip_test` a row of the `pose.decode` fields table, or only a link in
  "Method-specific fields"? The new section also defines the field (one owner for each rule, decision
  0013).
- [ ] Does the static-batch sentence of part 2.3 belong to `common.batching`?
- [ ] Is the edit of the "Implementer guidance" of `pre.resize.affine_person_crop` a content edit or a
  non-spec edit? It adds the measured effect of part 1, which has no committed source.
- [ ] The template says that a change to a section with no reference implementation must implement the
  full section. Does this rule apply to the edits of `post.pose.decode.simcc`,
  `post.pose.decode.heatmap` and `post.pose.schema`?
- [ ] Decide the vector case form for all proposals: change the tools, or convert the cases and
  correct the template.
- [ ] The reference example `rtmw-wholebody.yaml` stays valid, but it does not agree with the upstream
  test pipeline. OpenMMLab-Exporter writes no RTMW sidecar until the RTMW intake is `describes`
  (OpenMMLab-Exporter 0050). Keep the example until then?
- [ ] Add `proposed` rows to `inventory.yaml` for the new OpenMMLab-Exporter families? This is
  optional.
- [ ] The accepted entries 0013 and 0014 say that there is no reference implementation yet. This
  reference can be the first file in `specs/sidecar/reference/`. Their bodies cannot change. Add a
  new entry or an open-work item?

**Merge points**

- [ ] This proposal must land before `heatmap-decode-refinement` (0038). That proposal links the
  anchors of `post/pose-flip-test.md` and names `V-post.pose.flip_test-3`.
- [ ] Part 7 uses the family IDs `rtmpose-halpe26` and `dwpose-wholebody133-ubody` of
  `model-id-suffix` (0025). Land that proposal first, or use the current names.
- [ ] `post/pose-decode-heatmap.md`, "Behaviour": this proposal puts its sentence at the start of the
  bullet. `heatmap-decode-refinement` (0038) puts the same sentence in the middle. Decide the position.
- [ ] `post/pose-decode-simcc.md`, "Behaviour" and `changed_in`: `simcc-score-rule` (0024) replaces
  the bullet. `keypoint-visibility` (0039) adds a sentence.
- [ ] `format/versioning.md`, the legacy row "Not available.": `heatmap-decode-refinement` (0038),
  `keypoint-visibility` (0039), `roi-transform-and-source` (0020), `roi-refiner-role` (0047),
  `landmark-extra-outputs` (0021) and `landmark-depth-divisor` (0022).
- [ ] `post/pose-schema.md`: the `pose.decode` fields table and "Method-specific fields" (0038, 0039,
  0022); "Validation rules" and "See also" (0020, 0021, 0022, 0039).
- [ ] `pre/resize-affine-person-crop.md`, "Implementer guidance": `affine-crop-arithmetic` (0037).
- [ ] `specs/sidecar/README.md`, the section map and the validation index: `keypoint-visibility`
  (0039) and `landmark-extra-outputs` (0021).
- [ ] `changelog.md`, the summary row `N` and the `vNEXT` row: all 13 spec proposals.
- [ ] `landmark-extra-outputs` (0021) adds presence and handedness outputs. An average of a handedness
  after a mirror pass is wrong. Rule `V-post.pose.flip_test-1` excludes `coordinate` today. Keep this
  limit if a later change extends the flip test.
