---
slug: heatmap-decode-refinement
section: post.pose.decode.heatmap
exporter: OpenMMLab-Exporter
decision: "0038"
state: recorded
---

# Change proposal: heatmap-decode-refinement

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `heatmap-decode-refinement`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. Part 3 also holds the code of the OpenMMLab-Exporter reference file of part 3, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`.

## Header

| Field | Value |
|---|---|
| Title | Heatmap decode: the peak, the score, the -1 rule, the quarter-offset refinement and the cell-to-pixel scale |
| Slug | `heatmap-decode-refinement` |
| Date | 2026-10-23; updated 2026-10-25 (re-pinned to skellytracker `dom/21-move-sidecar-guide`; the template labels and the checklist text restored; the plan line numbers refreshed) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed; `git status --porcelain` is empty). It holds OpenMMLab-Exporter decision 0042 (commit `1dfec48`: sidecar `source` and artifact hashes) and OpenMMLab-Exporter decision 0050 (commit `f3aeb47`: no family writes a sidecar while its intake is not `describes`). This proposal does not use them. First written at `cce619d`, then checked at `d0f4343` (the T14 change in `rtmo/` and `rtmw/`; this proposal does not use it). The exporter lines that this proposal cites (`notes/decisions/migration-decisions.md:55`; `AGENTS.md` section 4) are the same at `f3aeb47` (checked again on 2026-10-24) |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts); plan T3, T11) and `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts); plan T9). Another workflow wrote the two intakes at the same time as this proposal. Both families use one pipeline: the non-UDP affine crop, `post_process='default'`, the flip test with `shift_heatmap=True` (plan T3, T9; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). |
| Intake rows with the verdict `near-miss` or `gap` | Rows K4 (decode method) and K8 (keypoint score) of the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) and of the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts). Both intakes give the file name in rows K4 and K8 and in "Proposals and reference files" with the slug `heatmap-decode-refinement` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). Plan step 1.3 expects the same verdict ("heatmap decode: `near-miss`", the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). |
| Kind (`new section` or `changed section`) | `changed section` |
| Proposed section ID (the `id` in the section file's front matter) | `post.pose.decode.heatmap` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/post/pose-decode-heatmap.md` |
| Depends on (proposal files that must land first, or `none`) | `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` (new section `post.pose.flip_test`). The Behaviour text of 2.3 links to it, and the two ViTPose families need `pose.decode.flip_test.shift_heatmap: true` from it. |
| Needed by (proposal files that depend on this one, or `none`) | none. `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` names this proposal by its file name in its "Needed by" row. That proposal also adds one sentence to the same "Behaviour" heading. 2.3 below contains that sentence, so the two edits give the same text. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/18-agents-adr-bootstrap-kit` and unchanged at `dom/21-move-sidecar-guide` (checked on 2026-10-25). `format/versioning.md:74` (the legacy row "Not available."): `pose-decode-flip-test`, `keypoint-visibility`, `roi-transform-and-source` (MediaPipe-Exporter), `roi-refiner-role` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `simcc-score-rule`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`, `roi-transform-and-source` (MediaPipe-Exporter); `post/pose-schema.md:89-95` (the `pose.decode` fields table and "Method-specific fields"): `pose-decode-flip-test`, `keypoint-visibility`, `landmark-depth-divisor` (MediaPipe-Exporter); `post/pose-schema.md:108-110` ("Shape key"): `simcc-score-rule`; `post/pose-decode-heatmap.md:24` (the "Behaviour" bullet): `pose-decode-flip-test`; `templates/model-intake.md:314` (row K4): `landmark-depth-divisor` (MediaPipe-Exporter); `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index of the decision log (`notes/decisions/README.md:23-68` at `dom/18-agents-adr-bootstrap-kit`; the index at `dom/21-move-sidecar-guide`, lines 23-51, also has no heatmap entry) has no heatmap entry. A search of `notes/decisions/*.md` for "heatmap" finds no file (also at `dom/18-agents-adr-bootstrap-kit`, with `open-work.md`). The section has no guidance that cites an entry (`post/pose-decode-heatmap.md:36-42`: "No exporter evidence yet."). |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `dom/21-move-sidecar-guide` (`git status --porcelain` lists only the untracked file `grep.exe.stackdump`, which is not a file that this proposal read, so no `+ uncommitted changes`; checked on 2026-10-25). Read before at `dom/18-agents-adr-bootstrap-kit` (checked again on 2026-10-24). First read at `dom/12-single-working-branch`. From `dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`, no cited spec, tool or package file changes. The decision-log index moved (row above). From `dom/18-agents-adr-bootstrap-kit` to `dom/21-move-sidecar-guide`, no cited spec section file, tool file or package file changes. `specs/model-sidecar/TRACEABILITY.md` changes 4 lines (107-108); its row for `post.pose.decode.heatmap` stays at line 91. The templates change only their header paragraph (the guide path); `templates/model-intake.md:314` and `templates/change-proposal.md:248-261` are unchanged. The decision-log index changes its layout; it still has no heatmap entry. Guide citations point to the skellytracker 0034 layout at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). |

## 1. Gap

| Item | Value |
|---|---|
| Property | The heatmap decode of the ViTAE-Transformer/ViTPose test pipeline, `post_process='default'` with `use_udp=False`. For each keypoint channel `(H, W)`: (1) the peak is the first maximum in row-major order; (2) the score is that maximum value, with no activation; (3) when the score is `<= 0`, both cells become -1; (4) when `1 < px < W - 1` and `1 < py < H - 1`, each axis moves 0.25 cell toward the higher of its two neighbours (no step for equal neighbours, and no step on either axis when one condition is false); (5) the cell maps to the crop with the scale `T_w / W` and `T_h / H`, with no half-cell offset. With the flip test, the decode reads the averaged heatmap. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **ViTAE-Transformer/ViTPose `c050ed2`** (the commit of plan 4.3). **Config:** `configs/wholebody/2d_kpt_sview_rgb_img/topdown_heatmap/coco-wholebody/ViTPose_small_wholebody_256x192.py:55-59` (`test_cfg`: `flip_test=True`, `post_process='default'`, `shift_heatmap=True`, `modulate_kernel=11`, no `use_udp`), `:62-63` (`image_size=[192, 256]`, `heatmap_size=[48, 64]`), `:87, :105` (`TopDownAffine` with no `use_udp`); `ViTPose_base_wholebody_256x192.py:57-58, 87, 105` (the same values). **Decode:** `mmpose/models/heads/topdown_heatmap_base_head.py:40-100` (`decode`; file fetched from raw.githubusercontent.com at `c050ed2`): `c` and `s` are float32 (lines 61-62); `keypoints_from_heatmaps` with `post_process=self.test_cfg.get('post_process', 'default')` and `use_udp=self.test_cfg.get('use_udp', False)` (lines 75-85); the keypoint score is `maxvals` (lines 87-90). `mmpose/core/evaluation/top_down_eval.py:63-95` (`_get_max_preds`): `np.argmax` and `np.amax` on the flattened `H * W` channel (lines 86-88); `x = idx % W`, `y = idx // W` (lines 91-92); `np.where(maxvals > 0.0, preds, -1)` (line 94). `top_down_eval.py:474-622` (`keypoints_from_heatmaps`): the non-UDP branch (lines 589-612) calls `_get_max_preds` (line 590); for `post_process` not None and not `'unbiased'` (line 598) it tests `1 < px < W - 1 and 1 < py < H - 1` (line 605), takes `heatmap[py][px + 1] - heatmap[py][px - 1]` and `heatmap[py + 1][px] - heatmap[py - 1][px]` (lines 606-609) and adds `np.sign(diff) * .25` (line 610); then `transform_preds(preds[i], center[i], scale[i], [W, H], use_udp=use_udp)` (lines 615-617). `mmpose/core/post_processing/post_transforms.py:150-194` (`transform_preds`): `scale = scale * 200.0` (line 181); non-UDP `scale_x = scale[0] / output_size[0]` (lines 186-188); `x = coords * scale_x + center[0] - scale[0] * 0.5` (lines 191-192). **Order with the flip test:** `mmpose/models/detectors/top_down.py:176-177` (first pass), `:179-188` (mirror pass, then `(output_heatmap + output_flipped_heatmap) * 0.5`), `:190-192` (`decode` of the averaged heatmap); `mmpose/models/heads/topdown_heatmap_simple_head.py:217-224` (`flip_back`, then the shift when `shift_heatmap`). **The box:** `mmpose/apis/inference.py:85-112` (`_box2cs`: center `x + w * 0.5`, the aspect fix, `scale = [w / 200, h / 200] * 1.25`, float32; file fetched at `c050ed2`). **25 points:** no upstream config has the B2 pipeline. The ViTAE COCO body base config sets `post_process='default'` with `use_udp=True` (`configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/ViTPose_small_coco_256x192.py:69-75`, `TopDownAffine(use_udp=True)` at lines 103 and 125; file fetched at `c050ed2`), as does easy_ViTPose `bb98603` `easy_ViTPose/configs/ViTPose_common.py:90-96`. With `use_udp=True`, `keypoints_from_heatmaps` runs DARK-UDP whatever `post_process` is (`top_down_eval.py:567-570`). The 25-point B2 pipeline is the choice of this exporter (plan T9, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), and the created config of plan 4.4, in the same plan, both secondary): `use_udp=False` with `post_process='default'`, the same decode as ViTPose++. **A second upstream form of the same step:** mmpose v1.3.2 `mmpose/codecs/utils/refinement.py:9-46` (`refine_keypoints`) tests each axis alone: `1 < x < W - 1 and 0 < y < H` for x (line 34), `1 < y < H - 1 and 0 < x < W` for y (line 39). `mmpose/codecs/msra_heatmap.py:137, 148, 151` (v1.3.2) calls `get_heatmap_maximum`, then `refine_keypoints`, then `keypoints * self.scale_factor` (`input_size / heatmap_size`, line 74). `mmpose/codecs/utils/post_processing.py:188-192` (`get_heatmap_maximum`: the same row-major argmax and `locs[vals <= 0.] = -1`). |
| Nearest section ID (the `id` in the section file's front matter) | `post.pose.decode.heatmap` |
| Why the nearest section is wrong | The whole Behaviour of the section is one sentence: "The host decodes the peak of each keypoint to a location in cropped image space. Then the host unprojects the location to the source image." (`post/pose-decode-heatmap.md:24`). (1) It has no refinement: a host that follows it gives the integer cell, and the upstream moves 0.25 cell on each axis for most keypoints. (2) It gives no scale from a cell to a crop pixel. The Shape key gives a scale for SimCC bins only (`post/pose-schema.md:109`), not for `H` and `W` (`:108`). (3) It gives no score. (4) It gives no tie order of the argmax. (5) It has no rule for a keypoint with a maximum `<= 0`. (6) It does not say how the decode composes with the flip test or with the unprojection. Two upstream forms of the quarter step (ViTAE and mmpose v1.3.2) give different keypoints for a peak in row 1 or column 1, so "decodes the peak" with a refinement is not exact either. |
| Measured difference (number, image and script) | **Location.** The quarter step moves a keypoint by 0.25 cell on each axis. For the ViTPose input 256x192 and heatmap 64x48 (`ViTPose_small_wholebody_256x192.py:62-63`), that is `0.25 * 192 / 48 = 1` crop pixel on each axis. In the source image it is `0.25 * crop_size / W`: for a box 300 px high, the crop height is `300 * 1.25 = 375` px, so the step is `0.25 * 375 / 64 = 1.46` px (formula of `post_transforms.py:181, 188, 192`). **Border rule.** Vector `quarter-y-border-blocks-x` (part 4): a peak at cell (2, 1) of a 5x5 channel with a higher right neighbour. ViTAE `keypoints_from_heatmaps` gives x 2.0 (no step). mmpose v1.3.2 `refine_keypoints` gives x 2.25. **Composition.** The reference file of part 3 with the spec affine inverse (`pre/resize-affine-person-crop.md:43-51`, `:55-61`), against ViTAE `keypoints_from_heatmaps` with the ViTAE `_box2cs` center and scale: 4 boxes x 133 seeded random channels (64x48, 5 channels with maximum `<= 0`, 5 channels with coarse values for ties), 908 of 1064 coordinates moved by the step. Crop pixels: equal (max difference 0). Scores: equal. Source pixels: max difference 1.2e-4 px (float32 upstream, float64 reference). Scratch scripts `make_heatmap_vectors.py` and `compose_check.py`, not committed, so not evidence. They run the downloaded upstream files with a stub in place of `torch` (the decode functions do not use it). **AP effect** of the step, the -1 rule and the border rule on the ViTPose models: not measured. Plan appendix A.2 measures only `default` and DARK-UDP decodes, not a decode without the step. Part 5 measures the keypoints against the upstream. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The table (`changelog.md:38-53`) has no heatmap row. |

Missing primary evidence: the ONNX files of the two families (no ViTPose ONNX file of this exporter
exists yet; plan T7 exports them from the HF `.pth` files in the ViTAE environment of plan T12). The
decode does not depend on the graph, except for the output shape `(N, K, 64, 48)`. That shape is the
`heatmap_size` of the configs (`ViTPose_small_wholebody_256x192.py:63`). The intakes record the graph
row as `unverified`. The 25-point pipeline B2 has no upstream config (above). Its decode values come
from the created config of plan 4.4, which is a choice of this exporter.

## 2. Spec change

### 2.1 Sections

Changed section `post.pose.decode.heatmap`, title "Heatmap decode", file
`specs/model-sidecar/post/pose-decode-heatmap.md`. The section ID, the title, the kind and the selectors do
not change.

Changed front matter (the other keys do not change):

```yaml
changed_in: [vNEXT]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::PoseDecodeSpec._check_decode  # partial: no pose.decode.refinement field; V-post.pose.decode.heatmap-2 and -3 are not checked
  decode: missing
vectors: vectors/post.pose.decode.heatmap.yaml
status: {spec: stable, validate: partial, decode: missing}
```

The spec state stays `stable`, as for `pre.normalize` (`pre/normalization.md:6, 110`), which also has
`changed_in: [vNEXT]` and a "Legacy behaviour" heading. `validate` becomes `partial`, because the validator does not
check the two new rules (part 6).

No row in the section map changes: the section exists (`specs/model-sidecar/README.md:92`).

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `post.pose.decode.heatmap` (`post/pose-decode-heatmap.md`) | front matter | The edit above. |
| `post.pose.decode.heatmap` | "Fields" (new heading, before "Behaviour", as `post/pose-decode-simcc.md:28-34`) | Add the fields table of 2.2 and the sentence "`pose.decode.refinement` is a field of `pose.decode` (`pose-schema.md#posedecode`). That section defines the other `pose.decode` fields." |
| `post.pose.decode.heatmap` | "Behaviour" | Replace the bullet at line 24 with the text of 2.3. Keep the line "Shape key (`pose-schema.md#shape-key`)". |
| `post.pose.decode.heatmap` | "Validation rules" | Keep `V-post.pose.decode.heatmap-1` (line 32). Add `-2` and `-3` of 2.4. |
| `post.pose.decode.heatmap` | "Legacy behaviour" (new heading, after "Validation rules", as `pre/resize-letterbox.md:65-70`) | Add the table of 2.6. |
| `post.pose.decode.heatmap` | "Implementer guidance" | Replace "No exporter evidence yet." (line 38) with: "The border test of `quarter_offset` is not symmetric. Columns 0, 1 and `W - 1` and rows 0, 1 and `H - 1` give no step, and one axis in that band stops the step on both axes. This is the ViTAE-Transformer/ViTPose `keypoints_from_heatmaps` test `1 < px < W - 1 and 1 < py < H - 1` (`mmpose/core/evaluation/top_down_eval.py:605`, `c050ed2`). The mmpose v1.3.2 function `refine_keypoints` tests each axis alone (`mmpose/codecs/utils/refinement.py:34, 39`), so it moves x for a peak in row 1. Do not use it for `quarter_offset`." and: "The decode returns crop pixels. The unprojection of `affine_person_crop` then gives `x_src = x_cell * crop_w / W + cx - crop_w / 2`, the one-step form of ViTAE `transform_preds` (`mmpose/core/post_processing/post_transforms.py:181, 187, 191`). A host can use the one-step form. The two forms differ only by float rounding." |
| `post.pose.decode.heatmap` | "Authoring guidance" | Replace "No exporter evidence yet." (line 42) with: "ViTAE-Transformer/ViTPose (mmpose 0.x) `TopdownHeatmapSimpleHead`: `test_cfg` `post_process='default'` with no `use_udp`, or `use_udp=False`, maps to `refinement: quarter_offset`. `post_process=None` maps to `refinement: none`. `post_process='unbiased'` (DARK), `post_process='megvii'` and `use_udp=True` (DARK-UDP for every `post_process`) have no value: the intake row is a `near-miss` (`mmpose/core/evaluation/top_down_eval.py:563-612`, `c050ed2`). mmpose 1.x `MSRAHeatmap` with `unbiased=False` calls `refine_keypoints` (`mmpose/codecs/msra_heatmap.py:148`, v1.3.2), which is not `quarter_offset` (see Implementer guidance): the row is a `near-miss`. The `flip_test` and `shift_heatmap` keys of the same `test_cfg` map to Flip test (`pose-flip-test.md#fields`)." |
| `post.pose.schema` (`post/pose-schema.md`) | `pose.decode`, "Method-specific fields" (line 95) | Add the link `pose.decode.refinement` (`pose-decode-heatmap.md#fields`). |
| `post.pose.schema` | "Shape key" (line 108) | No change of meaning. After the `H`, `W` bullet, add: "For a `heatmap` output, the cell→pixel scale is `input_width / W` and `input_height / H`. The decode of the cells is in Heatmap decode (`pose-decode-heatmap.md#behaviour`)." |
| `post.pose.schema` | "Validation rules" | No rule changes. `V-post.pose.schema-3` (line 119) and `V-post.pose.schema-7` (line 123) do not name `refinement`. |
| `format.versioning` (`format/versioning.md`) | "Version-aware compatibility" (the list at lines 53-63) | Add the link `- [Heatmap decode](../post/pose-decode-heatmap.md#legacy-behaviour)` before "Bottom-up pose" (line 63). |
| `format.versioning` | "Legacy behaviour" (lines 72-74) | Add `pose.decode.refinement` to the row "`boxes`/`scores`/`class_logits` semantics, `packed_keypoints`, `stretch`, `fit`, `class_id_map`" ("Not available." / "Available."). If `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` lands first, the row also has `pose.decode.flip_test`. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" (`changelog.md:16-36`) | Add the summary row of 2.7. |
| `specs/model-sidecar/changelog.md` | "`schema_version` history" (`changelog.md:68`) | Append the sentence of 2.7 to the end of the existing `vNEXT` row. Do not add a second `vNEXT` row. |
| `specs/model-sidecar/changelog.md` | "Compatibility impact" (`changelog.md:58`) | Add "`pose.decode.refinement` for `pose.decode.method: heatmap`" to the list of fields that a `vNEXT` sidecar must declare. |
| `specs/model-sidecar/templates/model-intake.md` | row K4 (line 314) | Add `refinement` to the list of decode parameters (`coordinate_scale`, `is_3d`, `depth_unit`, `depth_range`). |
| `specs/model-sidecar/vectors/post.pose.decode.heatmap.yaml` | new file | The vectors of part 4, in the form of `tools/make_vectors.py` (the next two rows). `tools/tests/test_vectors.py:110-116` requires that every file in `specs/model-sidecar/vectors/` comes from `make_vectors.py` and equals its output. |
| `tools/make_vectors.py` | `BUILDERS` (line 2411) | Add a builder for `post.pose.decode.heatmap`. The file then has `generated_by: tools/make_vectors.py` (`GENERATED_BY`, line 38). The generator rounds `expect` to 6 decimals (`ROUND_DIGITS`, line 62). Every expected value of part 4 is exact with 6 decimals (the smallest step is 0.125 px: `4.375`), so any tolerance in `TOLERANCE` (line 65) is sufficient. |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (lines 32-40); `test_cases_have_the_documented_shape` (lines 169-180) | The part 4 cases have a `function` key, which `CASE_KEYS` does not have. Line 180 requires a `tolerance` key on each case where `has_fraction(expect)` is true. `has_fraction` is true for every Python float (`tools/make_vectors.py:97-100`), so every part 4 case needs a `tolerance` (each case has at least one float in `expect`, for example `score: [[0.5]]` or `cell_x: [[-1.0]]`), or integer expected values where the value is an integer. The skellytracker session converts the cases as it does for `specs/model-sidecar/proposals/simcc-score-rule/proposal.md` (its 2.1, rows `tools/make_vectors.py` and `tools/tests/test_vectors.py`): (a) add `function` to `CASE_KEYS`, or (b) select the function by the case-ID prefix (`peak-`, `low-score-`, `quarter-`, `pixel-`, `decode-`: one prefix for each function); and add the case `tolerance`. |
| `specs/model-sidecar/reference/post_pose_decode_heatmap.py` | new file | The reference file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated matrix | Do not edit it by hand (`TRACEABILITY.md:3`). After the section file changes, run `python tools/sidecar_trace.py matrix`. The status row of `post.pose.decode.heatmap` (`TRACEABILITY.md:91`) then names the vector file. `tools/tests/test_traceability.py::test_traceability_equals_a_fresh_generation` must pass. |
| `specs/model-sidecar/README.md` | Section map; "Validation rules" (the validation index) | No edit. The section row and its rules link exist (`README.md:92, 120`). |
| `specs/model-sidecar/sidecar-spec.md` | The permanent index | No edit. The index keeps the old headings only (skellytracker decision 0013). |
| `post.pose.flip_test` (proposed, `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` 2.3) | "Behaviour" | No edit. It ends with "decode out with pose.decode.method". This proposal defines that decode for `heatmap`. |
| `post.unprojection`, `pre.resize.affine_person_crop`, `common.outputs`, `common.identity`, `format.file_layout` | | No edit. The decode output stays in the model-input pixels of the crop (`post/unprojection.md:23-36`). A keypoint at cell -1 goes through the same unprojection. The change adds no output semantic, no role and no path. |
| `specs/model-sidecar/examples/` | examples | No edit. No example has `method: heatmap` (a search of the checkout for `method: heatmap` in YAML files finds no file). |

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| `pose.decode.refinement` | enum | required when `pose.decode.method: heatmap` (`vNEXT`) | The value is `none` or `quarter_offset`. It sets how the host moves the peak cell of a heatmap before the scale (see Behaviour (`#behaviour`)). `none`: the location is the peak cell. `quarter_offset`: the location moves 0.25 cell toward the higher neighbour on each axis. The author writes the value of the upstream test config (see Authoring guidance (`#authoring-guidance`)). The field has no default. |

### 2.3 Behaviour

Replace the bullet of the heading "Behaviour" with this text:

- `heatmap` — one output with `semantic: heatmap` and shape `(N, K, H, W)`. This method supports only 2D heatmaps. When `pose.decode.flip_test` is present, the host decodes the averaged outputs of the Flip test (`pose-flip-test.md#behaviour`). The host reads `H` and `W` from the output tensor. For each crop `n` and each keypoint `k`, the host does the steps below on the raw output values. The host does not apply an activation.

```text
c       = heatmap[n, k]                 (H rows, W columns)
i       = the index of the first maximum of c in row-major order
          (row 0 first; in one row, column 0 first)
cell_x  = i mod W
cell_y  = floor(i / W)
score   = c[cell_y, cell_x]             (the maximum value)

when score <= 0:
    cell_x = -1, cell_y = -1

x = cell_x, y = cell_y
refinement quarter_offset:
    when 1 < cell_x < W - 1 and 1 < cell_y < H - 1:      (both conditions, strict)
        x = cell_x + 0.25 * sign(c[cell_y, cell_x + 1] - c[cell_y, cell_x - 1])
        y = cell_y + 0.25 * sign(c[cell_y + 1, cell_x] - c[cell_y - 1, cell_x])
refinement none:
    no change

x_crop = x * input_width / W
y_crop = y * input_height / H
```

- `sign(d)` is `+1` for `d > 0`, `-1` for `d < 0` and `0` for `d = 0`. Thus equal neighbours give no step on that axis. A host can compare the two neighbours in place of the subtraction.
- When one of the two conditions is false, neither axis moves. Columns 0, 1 and `W - 1` and rows 0, 1 and `H - 1` give no step. A cell of -1 never moves.
- The score is a raw output value. It has no fixed range: it can be negative, and it can be above 1. The host compares `score <= 0` in the dtype of the output. With the flip test, the score comes from the averaged outputs.
- A keypoint with `score <= 0` keeps its place in the output. Its location is cell -1 on each axis, thus `(-input_width / W, -input_height / H)` in the crop. The host unprojects it like every other keypoint.
- `x_crop` and `y_crop` are in the model-input pixels of the crop (cropped image space). The cell is not moved to its centre: cell 0 maps to pixel 0. The host unprojects the location to the source image (see Unprojection (`unprojection.md`)). For `affine_person_crop`, the result is `x_src = x * crop_w / W + center_x - crop_w / 2` (and the same form for `y`). `crop_w` is the width of the crop box in source pixels (`w` of Affine person crop (`../pre/resize-affine-person-crop.md#behaviour`)).
- The reference arithmetic is float64, in the order of the formulas. A host can use float32. When `input_width / W` and `input_height / H` are integers, `x_crop` and `y_crop` are the same in float32 and float64.
- `schema_version < vNEXT`: see Legacy behaviour (`#legacy-behaviour`). The host does not apply the -1 rule or a refinement.

**Inverse.** None. The decode maps cells to crop pixels. No step of the contract maps pixels back to
cells. The inverse of the crop is `post.unprojection`.

### 2.4 Validation rules

- [ ] `V-post.pose.decode.heatmap-1` unchanged.
- [ ] `V-post.pose.decode.heatmap-2` **(vNEXT)** A sidecar with `pose.decode.method: heatmap` must declare `pose.decode.refinement`. Its value must be `none` or `quarter_offset`.
- [ ] `V-post.pose.decode.heatmap-3` **(vNEXT)** `pose.decode.refinement` is valid only when `pose.decode.method` is `heatmap`.

Existing rules that name a value of this change:

- `V-post.pose.decode.heatmap-1` (no 3D heatmap): unchanged. The decode is 2D.
- `V-post.pose.schema-3` (the decode methods) and `V-post.pose.schema-7` (one `heatmap` output for the
  `heatmap` method): unchanged.
- `V-post.pose.flip_test-3` (proposed: `shift_heatmap` only with `method: heatmap`): unchanged.

Follow-up, not in this proposal: a value for the per-axis border test of mmpose v1.3.2
`refine_keypoints`, and values for DARK and DARK-UDP. No model in scope needs them (plan T9: no
DARK-UDP decode).

### 2.5 Selectors

Unchanged: `pose.decode.method=heatmap`, `outputs[].semantic=heatmap`.

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` does not use `pose.decode.refinement`. Its decode is the
  peak cell with the scale, with no -1 rule and no refinement. This makes the old text "decodes the
  peak of each keypoint to a location in cropped image space" exact. The tie order, the score and the
  scale are the same for the two versions.
- No sidecar in the checkout has `method: heatmap` (a search of the YAML files finds no file), and no
  host decodes heatmaps (front matter `decode: missing`, `post/pose-decode-heatmap.md:12`). Thus no
  current behaviour changes.
- The change goes into the `vNEXT` revision.
- New heading "Legacy behaviour" in `post/pose-decode-heatmap.md`:

```text
## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| Heatmap decode | The location is the peak cell (the first maximum in row-major order), scaled by `input_width / W` and `input_height / H`. The score is the maximum value. There is no -1 rule and no refinement. `pose.decode.refinement` is not available. | `pose.decode.refinement` is required. A score `<= 0` puts the keypoint at cell -1. The declared refinement applies (see [Behaviour](#behaviour)). |

See also [Version-aware compatibility](../format/versioning.md#version-aware-compatibility).
```

- The validator: the spec has no rule that rejects a `vNEXT`-only field in a legacy sidecar
  (`specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` 2.6 gives the same point for
  `pose.decode.flip_test`). This proposal adds no such rule.

### 2.7 Changelog row

Summary of changes (`changelog.md:16`, five columns). `N` is the next free number when this proposal
merges. Rows 1 to 19 exist (`changelog.md:18-36`). Other open proposals of this exporter also add rows
(pose-decode-flip-test, simcc-score-rule, model-id-suffix, size-codes).

```text
| N | Pose | The heatmap decode is normative: the first maximum in row-major order, the maximum value as the score, cell -1 for a score `<= 0`, and the cell→pixel scale `input_width / W`, `input_height / H` with no half-cell offset. New required `pose.decode.refinement` (`none` \| `quarter_offset`): `quarter_offset` moves the peak 0.25 cell toward the higher neighbour on each axis when `1 < x < W - 1` and `1 < y < H - 1`. Legacy sidecars decode the peak cell. | ViTPose++ wholebody, ViTPose 25 points (ViTAE `post_process='default'`) | [Heatmap decode](post/pose-decode-heatmap.md#behaviour) |
```

Sentence to append to the end of the existing `vNEXT` row of the `schema_version` history
(`changelog.md:68`):

```text
The heatmap decode is normative (row-major first maximum, maximum value as the score, cell -1 for a score `<= 0`, scale `input_width / W`); added the required `pose.decode.refinement` (`none`, `quarter_offset`) for `method: heatmap` (legacy sidecars decode the peak cell).
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the untracked reference plan of OpenMMLab-Exporter (plan facts)) | the part 3 code of `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_pose_decode_heatmap.py` |
| Functions (one for each algorithm) | `heatmap_peak` (the row-major first maximum and the score), `mark_low_score` (the -1 rule), `quarter_offset` (the refinement), `cell_to_pixel` (`cell * input_extent / cell_count`), `heatmap_decode` (the full section; `refinement` selects `none` or `quarter_offset`; `legacy=True` selects the legacy row). `REFINEMENTS` is the closed set of values. |

Source commit: none (no host code). This exporter has no heatmap decode on its host side yet (plan
step 5c, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The functions come from the text of part 2.
The section has no reference implementation yet (`specs/model-sidecar/reference/` does not exist in the
checkout). Thus this file implements the full section as changed, and it is also the
reference-implementation step of the section. The file does not implement the flip test
(`post.pose.flip_test`) or the unprojection (`post.unprojection`).

```python
"""Reference implementation of the section post.pose.decode.heatmap, as the proposal changes it.

This file uses ASD-STE100 Simplified Technical English.

- Section ID: post.pose.decode.heatmap (section file specs/model-sidecar/post/pose-decode-heatmap.md).
- Proposal: specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md (OpenMMLab-Exporter), slug
  heatmap-decode-refinement. It depends on specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md.
- Target file in skellytracker: specs/model-sidecar/reference/post_pose_decode_heatmap.py.
- source commit: none (no host code). OpenMMLab-Exporter has no heatmap decode on its host side yet.
  The functions come from the text of part 2 of the proposal.
- Vector results: all 24 cases of part 4 of the proposal pass against this file, exactly, with
  float32 inputs (run of 2026-10-23, recorded in part 4). They are unverified: no host
  implementation in an exporter or in skellytracker decodes heatmaps yet. The refined decode cases
  and the quarter_offset cases also agree with ViTAE-Transformer/ViTPose c050ed2
  keypoints_from_heatmaps (upstream code, not an implementation of the spec).
- Parity result: to run (part 5 of the proposal).

The section had no reference implementation (specs/model-sidecar/reference/ does not exist in the checkout).
Thus this file implements the full section as changed: the argmax cell, the score, the -1 rule
(schema_version >= vNEXT), the refinement values `none` and `quarter_offset`, the cell-to-pixel scale,
and the legacy row. The keypoints that it returns are in the model-input pixels of the crop. The
flip test (proposed section post.pose.flip_test) runs before this decode, on the raw outputs. The
unprojection to the source image (section post.unprojection, the Inverse of
pre.resize.affine_person_crop) runs after it. Neither is in this file.

Uses only NumPy and the Python standard library.
"""

from __future__ import annotations

import numpy as np

REFINEMENTS = ("none", "quarter_offset")


def heatmap_peak(heatmap: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """post.pose.decode.heatmap: the peak cell and the score of each keypoint channel.

    `heatmap` has the shape (N, K, H, W). The function reads the raw output values. It applies no
    activation. The peak is the first maximum in row-major order of the H x W channel (np.argmax on
    the flattened channel): on a tie, the lowest row wins, then the lowest column in that row.
    Returns (cell_x, cell_y, score), each of shape (N, K). cell_x and cell_y are int64. score is the
    maximum value, in the dtype of `heatmap`.
    """
    heatmap = np.asarray(heatmap)
    if heatmap.ndim != 4:
        raise ValueError("post.pose.decode.heatmap: the heatmap must have the shape (N, K, H, W)")
    n, k, h, w = heatmap.shape
    flat = heatmap.reshape(n, k, h * w)
    index = np.argmax(flat, axis=-1)
    return index % w, index // w, np.max(flat, axis=-1)


def mark_low_score(cell_x: np.ndarray, cell_y: np.ndarray,
                   score: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.decode.heatmap, schema_version >= vNEXT: the -1 rule.

    Where score <= 0, both cells of the keypoint become -1. The comparison is not strict: a score of
    exactly 0 gives the cell -1. Returns float64 cells of the same shape.
    """
    low = np.asarray(score) <= 0
    cell_x = np.array(cell_x, dtype=np.float64)
    cell_y = np.array(cell_y, dtype=np.float64)
    cell_x[low] = -1.0
    cell_y[low] = -1.0
    return cell_x, cell_y


def _step(higher_side: float, lower_side: float) -> float:
    """+0.25 when the value on the higher-index side is larger, -0.25 when it is smaller, else 0."""
    if higher_side > lower_side:
        return 0.25
    if higher_side < lower_side:
        return -0.25
    return 0.0


def quarter_offset(heatmap: np.ndarray, cell_x: np.ndarray,
                   cell_y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.decode.heatmap, refinement: quarter_offset.

    For each keypoint, let px = int(cell_x) and py = int(cell_y). Only when
    1 < px < W - 1 and 1 < py < H - 1 (both conditions, strict), the cell moves by 0.25 toward the
    higher of its two neighbours on each axis:
        x = px + 0.25 * sign(heatmap[py, px + 1] - heatmap[py, px - 1])
        y = py + 0.25 * sign(heatmap[py + 1, px] - heatmap[py - 1, px])
    sign is 0 for equal neighbours. When one condition is false, neither axis moves. A cell of -1
    (the -1 rule) never moves. Returns float64 (x, y) in heatmap cells, of shape (N, K).
    """
    heatmap = np.asarray(heatmap)
    _, _, h, w = heatmap.shape
    x = np.array(cell_x, dtype=np.float64)
    y = np.array(cell_y, dtype=np.float64)
    for n, k in np.ndindex(x.shape):
        px = int(x[n, k])
        py = int(y[n, k])
        if 1 < px < w - 1 and 1 < py < h - 1:
            channel = heatmap[n, k]
            x[n, k] = px + _step(channel[py, px + 1], channel[py, px - 1])
            y[n, k] = py + _step(channel[py + 1, px], channel[py - 1, px])
    return x, y


def cell_to_pixel(cell: np.ndarray, input_extent: int, cell_count: int) -> np.ndarray:
    """post.pose.decode.heatmap: the cell-to-pixel scale of one axis (Shape key).

    pixel = cell * input_extent / cell_count, in float64, in this order. `input_extent` is
    input_width for x (cell_count W) and input_height for y (cell_count H). The cell is not moved to
    its centre: cell 0 gives pixel 0, and cell -1 gives -input_extent / cell_count.
    """
    return np.asarray(cell, dtype=np.float64) * input_extent / cell_count


def heatmap_decode(
    heatmap: np.ndarray,
    input_width: int,
    input_height: int,
    refinement: str | None = None,
    legacy: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """post.pose.decode.heatmap: the full decode of one batch of crops.

    heatmap (N, K, H, W), after the flip test when pose.decode.flip_test is present.
    input_width and input_height are T_w and T_h of the model input.
    schema_version >= vNEXT (legacy false): `refinement` must be `none` or `quarter_offset`
    (V-post.pose.decode.heatmap-2). The steps are: the peak, the -1 rule, the refinement, the scale.
    schema_version < vNEXT (legacy true): the field is not available, so `refinement` must be None.
    The steps are: the peak and the scale. There is no -1 rule and no refinement.
    Returns (keypoints, score). keypoints has the shape (N, K, 2): x and y in the model-input pixels
    of the crop, float64. score has the shape (N, K) and the dtype of `heatmap`.
    """
    heatmap = np.asarray(heatmap)
    if legacy:
        if refinement is not None:
            raise ValueError("pose.decode.refinement is not available when schema_version < vNEXT")
    elif refinement not in REFINEMENTS:
        raise ValueError(
            f"pose.decode.refinement must be one of {REFINEMENTS} (V-post.pose.decode.heatmap-2)"
        )
    cell_x, cell_y, score = heatmap_peak(heatmap)
    if legacy:
        x = np.asarray(cell_x, dtype=np.float64)
        y = np.asarray(cell_y, dtype=np.float64)
    else:
        x, y = mark_low_score(cell_x, cell_y, score)
        if refinement == "quarter_offset":
            x, y = quarter_offset(heatmap, x, y)
    _, _, h, w = heatmap.shape
    keypoints = np.stack(
        [cell_to_pixel(x, input_width, w), cell_to_pixel(y, input_height, h)], axis=-1
    )
    return keypoints, score


__all__ = [
    "REFINEMENTS",
    "cell_to_pixel",
    "heatmap_decode",
    "heatmap_peak",
    "mark_low_score",
    "quarter_offset",
]
```

## 4. Vectors

The vectors come from the reference file (scratch generator `make_heatmap_vectors.py`, not
committed). The generator checks each case against a value written by hand.

Run of 2026-10-23: all 24 cases below pass against the part 3 code of `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md`.
The runner reads the YAML block of this part, loads the reference file with
`importlib.util.spec_from_file_location`, gives each numeric list of `input` as a float32 NumPy array,
calls `function(**params, **input)`, and requires each result to equal `expect` exactly. An exception
counts as a failed case. Command:
`uv run --project <exporter repo> python -I run_part4_vectors.py <this file> <reference file>`
(scratch script, not committed). Output: `24/24 pass`.

Mutant check of the same run (the runner loads a changed copy of the reference file): each strict
bound of the border test changed by one cell (`0 <` or `2 <` for the lower bound, `< W`, `< W - 2`,
`< H` or `< H - 2` for the upper bound, on each axis), `or` in place of `and`, two swaps of the scale
arguments (`input_width` with `input_height`, and `W` with `H`), `< 0` in place of `<= 0` in the -1 rule, and `>=` in place of `>` in the step. Each of the 13
mutants fails at least one case.

Upstream cross-check (upstream code, not an implementation of the spec, so not in
`verified_against`):

- The 5 `heatmap_decode` cases with a `refinement` and the 9 `quarter_offset` cases with a cell
  `>= 0` ran through ViTAE `c050ed2` `keypoints_from_heatmaps` (`post_process='default'` for
  `quarter_offset`, `None` for `none`; `use_udp=False`). The center `(T_w / 2, T_h / 2)` and the scale
  `(T_w / 200, T_h / 200)` make its output crop pixels. It gave the same keypoints and scores (max
  difference 0).
- `decode-legacy` has no upstream form: the upstream always applies the -1 rule.
- `quarter-y-border-blocks-x` through mmpose v1.3.2 `refine_keypoints` gives x 2.25, not 2.0 (part 1).

The YAML below uses the form of the template (`specs/model-sidecar/templates/change-proposal.md:248-261`).
The skellytracker session converts it to the form of `tools/make_vectors.py` (2.1, rows
`tools/make_vectors.py` and `tools/tests/test_vectors.py`). The ids and the inputs do not change. No
case is a pixel case, and every value is exact in float32, so no case needs `compare`.

```yaml
section: post.pose.decode.heatmap
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md`
unverified: "No exporter has a heatmap host decode yet, and skellytracker has none (decode: missing)."
# The refined decode cases and the quarter_offset cases with a cell >= 0 agree with
# ViTAE-Transformer/ViTPose c050ed2 mmpose/core/evaluation/top_down_eval.py::keypoints_from_heatmaps
# (use_udp=False; upstream code, not an implementation of the spec).
# A runner gives each numeric list of input as a float32 NumPy array. Each key of params and input is
# an argument of the function. heatmap is (N, K, H, W).
cases:
  - id: peak-tie-row-major  # k0: equal maxima at (3, 1) and (1, 2): the lower row wins; k1: equal maxima in row 0 at x 1 and 2: the lower column wins
    function: heatmap_peak
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0],
                  [0.0, 1.0, 0.0, 0.0]],
                 [[0.5, 0.75, 0.75, 0.5],
                  [0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5]]]]
    expect: {cell_x: [[3, 1]], cell_y: [[1, 0]], score: [[1.0, 0.75]]}
  - id: peak-raw-negative  # raw values, no activation: a negative maximum stays negative
    function: heatmap_peak
    params: {}
    input:
      heatmap: [[[[-1.0, -1.0, -1.0, -1.0],
                  [-1.0, -1.0, -0.25, -1.0],
                  [-1.0, -1.0, -1.0, -1.0]]]]
    expect: {cell_x: [[2]], cell_y: [[1]], score: [[-0.25]]}
  - id: peak-flat  # a flat channel: every cell ties, so cell (0, 0) wins
    function: heatmap_peak
    params: {}
    input:
      heatmap: [[[[0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5]]]]
    expect: {cell_x: [[0]], cell_y: [[0]], score: [[0.5]]}
  - id: low-score-zero  # score exactly 0: <= 0, so both cells become -1
    function: mark_low_score
    params: {}
    input: {cell_x: [[3]], cell_y: [[2]], score: [[0.0]]}
    expect: {cell_x: [[-1.0]], cell_y: [[-1.0]]}
  - id: low-score-negative  # negative score: both cells become -1
    function: mark_low_score
    params: {}
    input: {cell_x: [[3]], cell_y: [[2]], score: [[-0.5]]}
    expect: {cell_x: [[-1.0]], cell_y: [[-1.0]]}
  - id: low-score-small-positive  # score > 0: the cells stay
    function: mark_low_score
    params: {}
    input: {cell_x: [[3]], cell_y: [[2]], score: [[0.0001]]}
    expect: {cell_x: [[3.0]], cell_y: [[2.0]]}
  - id: quarter-interior-right-down  # right > left and down > up: +0.25 on both axes
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.25, 1.0, 0.5, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[2]]
    expect: {x: [[2.25]], y: [[2.25]]}
  - id: quarter-interior-left-up  # left > right and up > down: -0.25 on both axes
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.25, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[2]]
    expect: {x: [[1.75]], y: [[1.75]]}
  - id: quarter-equal-x-neighbours  # equal x neighbours: no x step; up > down: -0.25 on y
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.5, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[2]]
    expect: {x: [[2.0]], y: [[1.75]]}
  - id: quarter-cell-1-no-step  # cell_x 1: 1 < 1 is false, so neither axis moves, though cell 0 exists
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.25, 0.0, 0.0, 0.0],
                  [0.25, 1.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[1]]
      cell_y: [[2]]
    expect: {x: [[1.0]], y: [[2.0]]}
  - id: quarter-cell-w-minus-2-steps  # cell_x 3 = W - 2: inside, so both axes move
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.5, 0.0],
                  [0.0, 0.0, 0.25, 1.0, 0.5],
                  [0.0, 0.0, 0.0, 0.25, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[3]]
      cell_y: [[2]]
    expect: {x: [[3.25]], y: [[1.75]]}
  - id: quarter-cell-w-minus-1-no-step  # cell_x 4 = W - 1: outside, so neither axis moves
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.25],
                  [0.0, 0.0, 0.0, 0.5, 1.0],
                  [0.0, 0.0, 0.0, 0.0, 0.5],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[4]]
      cell_y: [[2]]
    expect: {x: [[4.0]], y: [[2.0]]}
  - id: quarter-y-border-blocks-x  # cell_y 1 is outside, so x does not move either (mmpose v1.3.2 refine_keypoints moves x to 2.25 here)
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.25, 1.0, 0.5, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[1]]
    expect: {x: [[2.0]], y: [[1.0]]}
  - id: quarter-cell-h-minus-2-steps  # a channel that is not square (H 6, W 5): cell_y 4 = H - 2 is inside, so both axes move
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.25, 1.0, 0.5, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[4]]
    expect: {x: [[2.25]], y: [[4.25]]}
  - id: quarter-cell-h-minus-1-no-step  # H 6, W 5: cell_y 5 = H - 1 is outside, so neither axis moves, though the x neighbours differ
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.25, 1.0, 0.5, 0.0]]]]
      cell_x: [[2]]
      cell_y: [[5]]
    expect: {x: [[2.0]], y: [[5.0]]}
  - id: quarter-minus-one  # a cell of -1 (the -1 rule) never moves
    function: quarter_offset
    params: {}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
      cell_x: [[-1]]
      cell_y: [[-1]]
    expect: {x: [[-1.0]], y: [[-1.0]]}
  - id: pixel-vitpose-ratio-4  # ViTPose 256x192 input, 64x48 heatmap: T_w / W = 4; cell 2.25 gives 9 px; cell -1 gives -4 px
    function: cell_to_pixel
    params: {input_extent: 192, cell_count: 48}
    input: {cell: [0, 1, 2.25, 47, -1]}
    expect: {pixel: [0.0, 4.0, 9.0, 188.0, -4.0]}
  - id: pixel-ratio-2.5  # the scale comes from input_extent / cell_count, not from a fixed ratio; no half-cell offset
    function: cell_to_pixel
    params: {input_extent: 10, cell_count: 4}
    input: {cell: [0, 1.75, 3]}
    expect: {pixel: [0.0, 4.375, 7.5]}
  - id: decode-quarter-offset  # k0: peak (2, 3), right > left, up > down: (2.25, 2.75) x 4; k1: max -0.25 <= 0: cells -1, -4 px, the score stays; k2: peak on the left border (0, 4): no step
    function: heatmap_decode
    params: {input_width: 20, input_height: 24, refinement: quarter_offset}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.75, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]],
                 [[-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.25, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5]],
                 [[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.75, 0.5, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
    expect: {keypoints: [[[9.0, 11.0], [-4.0, -4.0], [0.0, 16.0]]], score: [[1.0, -0.25, 0.75]]}
  - id: decode-none  # the same outputs with refinement none: the cells x 4; the -1 rule still applies
    function: heatmap_decode
    params: {input_width: 20, input_height: 24, refinement: none}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.75, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]],
                 [[-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.25, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5]],
                 [[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.75, 0.5, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
    expect: {keypoints: [[[8.0, 12.0], [-4.0, -4.0], [0.0, 16.0]]], score: [[1.0, -0.25, 0.75]]}
  - id: decode-axis-ratios-differ  # input 20 x 18, heatmap W 5, H 6: x scale 4, y scale 3, so a swap of the scale axes fails; k0: (2.25, 2.75) gives (9, 8.25); k1: cell -1 gives (-4, -3)
    function: heatmap_decode
    params: {input_width: 20, input_height: 18, refinement: quarter_offset}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.75, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]],
                 [[-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.25, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5]]]]
    expect: {keypoints: [[[9.0, 8.25], [-4.0, -3.0]]], score: [[1.0, -0.25]]}
  - id: decode-legacy  # schema_version < vNEXT: no -1 rule and no refinement; k1 keeps its argmax cell (3, 2)
    function: heatmap_decode
    params: {input_width: 20, input_height: 24, legacy: true}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.5, 1.0, 0.75, 0.0],
                  [0.0, 0.0, 0.25, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]],
                 [[-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.25, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5],
                  [-0.5, -0.5, -0.5, -0.5, -0.5]],
                 [[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.75, 0.5, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
    expect: {keypoints: [[[8.0, 12.0], [12.0, 8.0], [0.0, 16.0]]], score: [[1.0, -0.25, 0.75]]}
  - id: decode-flat-zero  # a flat channel of 0: the peak is cell (0, 0), the score 0 is <= 0, so the cells become -1
    function: heatmap_decode
    params: {input_width: 20, input_height: 24, refinement: quarter_offset}
    input:
      heatmap: [[[[0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0, 0.0]]]]
    expect: {keypoints: [[[-4.0, -4.0]]], score: [[0.0]]}
  - id: decode-flat-positive  # a flat channel of 0.5: the peak is cell (0, 0), on the border, so no step
    function: heatmap_decode
    params: {input_width: 20, input_height: 24, refinement: quarter_offset}
    input:
      heatmap: [[[[0.5, 0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5, 0.5],
                  [0.5, 0.5, 0.5, 0.5, 0.5]]]]
    expect: {keypoints: [[[0.0, 0.0]]], score: [[0.5]]}
```

Branch coverage. Peak: a tie across rows and a tie in one row (`peak-tie-row-major`), a negative
maximum (`peak-raw-negative`), a flat channel (`peak-flat`). -1 rule: a score of exactly 0 (the
non-strict `<=`), a negative score, a small positive score. Refinement: both signs on both axes, equal
neighbours, both sides of each strict border bound on x (cells 1, 2 in the 5-wide cases, and cells
`W - 2`, `W - 1`), both sides of each strict border bound on y (cell 1 in `quarter-y-border-blocks-x`,
cell 2 in the interior cases, and cells `H - 2`, `H - 1` on a channel that is not square: `H = 6`,
`W = 5`), a y cell in the band that stops the x step, a cell of -1. Full decode: a heatmap that is not
square (`H = 6`, `W = 5`, so a swap of `H` and `W` fails), two different scale ratios on the two axes
(`decode-axis-ratios-differ`: `20 / 5 = 4` and `18 / 6 = 3`, so a swap of the scale axes fails),
`quarter_offset`, `none`, the legacy row, a peak on the border, a flat channel of 0 and a flat channel
of 0.5. The `pixel-` cases have one integer and one non-integer scale.

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | (1) Preprocessed input: record the maximum absolute difference. It is not 0 for these families: the normalization row is a `near-miss` (plan T2; plan appendix A.3: 4.8e-7 for the ViTAE float32 form, secondary), with its own proposal (`specs/model-sidecar/proposals/normalize-arithmetic/proposal.md`, slug `normalize-arithmetic`). (2) Export error `E` of each crop: the maximum absolute difference of the heatmap between the ONNX file and the ViTAE model on the same tensor. It is recorded, not gated. (3) Decode only (this section alone): the upstream averaged heatmap (`output_heatmap`) goes into the reference decode of part 3 and the host unprojection, with the host box of the box rule (row "Upstream reference"), so that the host crop and the upstream crop are the same box. Against the upstream `preds`: per-point difference in source pixels at most 1e-3 px (float32 noise of `transform_preds`, `post_transforms.py:190-192`, which writes into a float32 array; the scratch check of part 1 gives 1.2e-4 px), and the score difference 0 (the same maximum of the same array). (4) Full path (the ONNX file, the host flip test of `post.pose.flip_test`, this decode): where the upstream peak exceeds the second-largest value of its channel by more than `2 * E`, the host cell equals the upstream cell. Where also each neighbour difference that the step reads is larger than `2 * E` in absolute value, the host step equals the upstream step, and gate (3) applies to the point. Other changes are allowed, counted and listed. Score: `abs(score_host - score_upstream) <= E` of the crop (a maximum changes by at most the largest change of its inputs). (5) Body OKS AP on the 17 COCO points of the full image set: `abs(AP_host - AP_upstream) <= 0.005` (the fp32 gate of this exporter, D5 in `notes/decisions/migration-decisions.md:55`). The 25-point family has no OKS sigmas for `neck` and mid `hip`, so gates (3) and (4) are per-point differences (plan O8 and step 6.5, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO val2017 with GT person boxes: `annotations/person_keypoints_val2017.json` (`vitpose-coco25`, its 17 COCO points) and the COCO-WholeBody val annotations (`vitposepp-wholebody133`). The script records, for each branch, the crops that run it: a step on both axes (most keypoints); equal neighbours (a step of 0 on one axis); a peak in the border band (columns 0, 1, `W - 1` or rows 0, 1, `H - 1`: a keypoint at or outside the crop edge, for example a person at the image edge, or a box that cuts a limb); a peak in row 1 or column 1 (where ViTAE and mmpose v1.3.2 differ); a maximum `<= 0` (the -1 rule); an argmax tie. A portrait box and a landscape box (the two aspect branches of the crop). **Image choice before the gated run.** Each branch must run on at least one image (`specs/exporter-guide/sidecars/workflow/parity.md:20-21`). The model output sets the -1 rule branch and the tie branch, so the spec formulas cannot select those images before a model exists. The script thus has a selection pass with the upstream model on the two annotation sets. It names, for each branch, at least one COCO image ID and annotation ID that run it. These IDs go into this row before the gated run, as the SimCC proposal names its -1 images (`specs/model-sidecar/proposals/simcc-score-rule/proposal.md`). Image IDs now: to run (the selection pass needs the upstream model in the `/opt/vitae` environment of plan T12, which is not built yet; see the row "Result"). If no crop of the two sets has a maximum `<= 0`, or no crop has a tie, this row records a deviation from `exporter-guide/sidecars/workflow/parity.md:20-21` for that branch. The vectors of part 4 do not replace an image for the parity rule. |
| Upstream reference: library, version, config and command | ViTAE-Transformer/ViTPose `c050ed2` (mmpose 0.x) in the `/opt/vitae` environment of the exporter image (plan T12, not built yet). `mmpose.apis.init_pose_model(config, checkpoint)`, then `inference_top_down_pose_model(model, img, person_results, format='xywh', return_heatmap=True)` (`mmpose/apis/inference.py:21, 295-302`, `c050ed2`). **Box rule.** `person_results` holds the COCO `bbox` `(x, y, w, h)` of each annotation, unchanged. The host gets the box `(x1, y1, x2, y2) = (x, y, x + w, y + h)`. Do not use `format='xyxy'`: that path converts the box with `w = x2 - x1 + 1` and `h = y2 - y1 + 1` (`inference.py:62-63`, called at `:386-388`), and `_box2cs` then uses that `w` and `h` (`:98-112`). The skellytracker crop uses `center = (x1 + x2) / 2` and `scale = (x2 - x1) * padding` (`skellytracker/core/detectors/processing/affine_crop.py:78-79`). With `format='xywh'`, `_box2cs` gives `center = x + w / 2 = (x1 + x2) / 2` (`inference.py:101`), so the two crops are the same box. With `format='xyxy'`, the two crops differ by 1 px of box width: for the box xyxy `(100, 50, 250, 450)` at 192x256, the upstream `x_src` minus the host `x_src` is 0.031 px at `x_crop` 0 and 0.969 px at `x_crop` 192 (review calculation), which is far above gate (3). With `return_heatmap=True`, the result holds `output_heatmap`, the averaged heatmap that `decode` reads (`top_down.py:187-188, 190-192, 198`). Two runs: the config `test_cfg` (flip test on, `shift_heatmap=True`), and `test_cfg.flip_test=False` (the decode without the flip test). Configs: `ViTPose_{small,base,large}_wholebody_256x192.py` (plan 4.3) and the created `ViTPose_{small,base,large}_coco25_256x192.py` (plan 4.4, B2). Checkpoints: HF `JunkyByte/easy_ViTPose` `e838052` (plan T7). |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (`E` for each crop; report the maximum and the 99th percentile) |
| Preprocessed input: maximum absolute difference for each image | to run (expect about 4.8e-7, gate 1) |
| Row count for each image: sidecar path and upstream | to run (one pose for each box on both sides) |
| Final outputs in source-image coordinates: metric and value for each role | to run (`pose_estimator`: gates 3 to 5) |
| Result (`pass`, `fail` or `to run`) | to run. Missing inputs: the ONNX files of both families, the `/opt/vitae` environment, the committed host code of plan step 5c. |
| Script path in the exporter repo | `notes/decisions/scripts/heatmap_decode_parity.py` (host side: ONNX Runtime CUDA, the host preprocessing, the reference file of part 3, the host flip test, the host unprojection, the gates) and `notes/decisions/scripts/heatmap_decode_parity_worker.py` (container side: ViTAE). Planned, not written. The flip-test proposal plans `notes/decisions/scripts/pose_flip_test_parity.py`. The two scripts can share one ViTAE worker. |
| Exporter commit of the script | unknown (the script is not written yet) |
| Command | `uv run python notes/decisions/scripts/heatmap_decode_parity.py --family vitposepp-wholebody133 --size s` (planned). The script starts the worker in the published image `<user>/openmmlab-exporter:df-<sha>`. |

The host side keeps torch out of the host process (`AGENTS.md`, section 4). Only the worker in the
container imports the ViTAE mmpose. The host side uses the reference file of part 3 in place of the
missing spec feature. It uses the host implementation of `pre.resize.affine_person_crop`,
`pre.normalize`, `post.pose.flip_test` and `post.unprojection` for the other steps, after that code is
committed (plan step 5c).

## 6. skellytracker implementation proposal

skellytracker does not build this now. The implementer checks this part.

| Item | Value |
|---|---|
| Module and function | A new module `skellytracker/core/detectors/processing/heatmap_decode.py` with the functions of part 3 (`heatmap_peak`, `mark_low_score`, `quarter_offset`, `cell_to_pixel`, `heatmap_decode`), and `heatmap_pose_decode(raw, center, scale, model_input_size, decode_spec)` with the signature of `simcc_pose_decode` (`skellytracker/core/detectors/processing/simcc_decode.py:105-111`). It returns source-image keypoints `(K, 2)` and scores `(K,)`, as `simcc_pose_decode` does (`:118-121`). |
| Dispatch point | Today `simcc_pose_decode` raises `NotImplementedError` for every method other than `simcc` (`simcc_decode.py:122-126`). The callers are the `postprocess` methods of the four SimCC detectors (`keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:88`, `rtmpose/body/rtmpose_body_detector.py:92`, `rtmpose/face/rtmpose_face_detector.py:92`, `rtmpose/hand/rtmpose_hand_detector.py:94`). No detector has a heatmap model. For the implementer: a dispatch on `pose.decode.method` in the generic keypoint detector of milestone M6 (`specs/sidecar-implementation-plan.md:191`; no such class exists yet, `:238`). The unprojection: `decode_simcc` applies the affine inverse itself (`simcc_decode.py:97-98`, `keypoints / model_input_size * scale + center - scale / 2`). Move that line to one shared function, and call it from both decoders. The decode needs the `schema_version` of the sidecar for the legacy row. `PoseDecodeSpec` has no version: pass a resolved legacy flag from the detector (as in `specs/model-sidecar/proposals/simcc-score-rule/proposal.md` part 6). |
| Validator changes (`model.py`, with rule IDs) | `PoseDecodeSpec` (`skellytracker/core/sidecar/model.py:259-264`): add `refinement: Literal["none", "quarter_offset"] \| None = None`. `_check_decode` (`:266-278`): add `V-post.pose.decode.heatmap-3` (`refinement` only with `method: heatmap`), next to the check of `V-post.pose.decode.heatmap-1` (`:270-271`). `V-post.pose.decode.heatmap-2` (required at `vNEXT`) needs the `schema_version`, so it goes in `SidecarModel` (`:463`), as a check of `pose.decode`. |
| Tests | The vectors of part 4 (`specs/model-sidecar/vectors/post.pose.decode.heatmap.yaml`), with `legacy` mapped to the version flag. Validation tests for rules -2 and -3 next to `test_heatmap_3d_is_rejected` (`skellytracker/tests/sidecar/test_model_validation.py:225-227`). A golden parity test for one ViTPose sidecar (the pattern of `skellytracker/tests/sidecar/test_rtmw_sidecar.py`), after an exporter publishes one. |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py` (`PoseDecodeSpec`, `SidecarModel`); `skellytracker/core/detectors/processing/simcc_decode.py` (`simcc_pose_decode`, the shared affine inverse of `decode_simcc`). No package sidecar uses `method: heatmap`, so no detector changes. |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | The planned `vitposepp-wholebody133` (intake the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), rows K4 and K8) and `vitpose-coco25` (intake the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), rows K4 and K8). No sidecar exists yet (plan T5: the new sidecars wait for the accepted proposals). `rtmw-wholebody133`, `rtmo-coco17-body7`, and the planned `rtmpose-halpe26` and `dwpose-wholebody133-ubody` use `simcc` or `coordinate`: no change. | New field: `pose.decode: {method: heatmap, refinement: quarter_offset, flip_test: {..., shift_heatmap: true}}` for both families (plan T3, T9). | The host has no heatmap decode yet. Plan step 5c writes it from part 3 in the committed parity scripts of `notes/decisions/scripts/`, or in `onnx_runtime/` after the user allows it (generic, NumPy only, no adapter import; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The parity script of part 5 uses the reference file. |
| Roboflow-Exporter | none (no pose model) | none | none |
| Ultralytics-Exporter | none (YOLO26-pose uses the `coordinate` decode) | none | none |
| Qualcomm-Exporter | none (the MediaPipe landmark sidecars have a `keypoints` output, `post/pose-schema.md:141`) | none | none |
| MediaPipe-Exporter | none (as Qualcomm-Exporter) | none | none |
| The proposing exporter, if it is not in this table | n/a (OpenMMLab-Exporter is in the table) | | |
| skellytracker package sidecars | none. No package sidecar has `method: heatmap`. | none | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change: "The host decodes the peak of each keypoint to a location" (the near-miss of today) | It gives no refinement, no scale, no score, no tie order and no rule for a maximum `<= 0`. A host that follows it gives the integer cell, up to 1 crop pixel (0.25 cell) from the upstream on each axis. | Part 1; `post/pose-decode-heatmap.md:24` |
| Always apply the quarter step at `vNEXT`, with no field | It hides a choice that the upstream configs make (`post_process`). A model with `post_process=None` then has no description. The legacy meaning is the peak cell, so the spec needs the `none` behaviour anyway. A required field with no default follows the letterbox `rounding` and `pad_position` (`V-pre.resize.letterbox-1`, `pre/resize-letterbox.md:61`). | `top_down_eval.py:598`; `pre/resize-letterbox.md:61, 70` |
| A default value (`quarter_offset` or `none`) in place of a required field | A default is not measured for a model. The field is new, so no `vNEXT` sidecar must change. | `changelog.md:58` (the required `vNEXT` fields) |
| The per-axis border test of mmpose v1.3.2 `refine_keypoints` as the meaning of `quarter_offset` | It is not the decode of the ViTAE configs that give the published ViTPose++ AP. It moves x for a peak in row 1 (vector `quarter-y-border-blocks-x`: 2.25 against 2.0). Add it later as a second value if an mmpose 1.x heatmap model needs it. | `refinement.py:34, 39`; `top_down_eval.py:605` |
| A symmetric border band (`0 < x < W - 1`) | It is not the upstream test. It moves a peak in column 1 or row 1. | `top_down_eval.py:605` |
| DARK (`post_process='unbiased'`) or DARK-UDP values now | No model in scope uses them. Plan T9 chose B2 for the 25-point model: no DARK-UDP decode. Add them as new values when a model needs them. | Plan T9 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary); `top_down_eval.py:567-597` |
| A half-cell offset in the scale (`(x + 0.5) * input_width / W - 0.5`, pixel centres) | The upstream non-UDP scale has no offset: `x * scale / W` (ViTAE `post_transforms.py:187, 191`) and `keypoints * scale_factor` (mmpose v1.3.2 `msra_heatmap.py:151`). An offset of 0.5 cell moves every keypoint by 2 crop pixels at `T_w / W = 4`. | `post_transforms.py:187, 191`; `msra_heatmap.py:74, 151` |
| The UDP scale `x * input_width / (W - 1)` | It belongs to the UDP crop (`use_udp=True`, `post_transforms.py:183-185`). The crop of both families is non-UDP (plan T3, T9). | `post_transforms.py:183-188` |
| No -1 rule (keep the peak cell for a maximum `<= 0`) at `vNEXT` | It differs from the upstream location of these keypoints. ViTAE and mmpose v1.3.2 both apply the rule. The SimCC proposal adds the same rule to `post.pose.decode.simcc`, so the two decode methods agree. | `top_down_eval.py:94`; `post_processing.py:192`; `specs/model-sidecar/proposals/simcc-score-rule/proposal.md` 2.3 |
| Apply the -1 rule also to a legacy sidecar | It changes the meaning of the old text for a keypoint with a maximum `<= 0`. No legacy heatmap sidecar exists, so the legacy row costs nothing. | 2.6 |
| An activation of the score (sigmoid, softmax) | The upstream score is the raw maximum (`maxvals`). The ViTAE eval thresholds the raw value (`vis_thr=0.2`, `ViTPose_small_wholebody_256x192.py:71`). | `topdown_heatmap_base_head.py:90`; `top_down_eval.py:88` |
| Put the decode into the ONNX graph (a `keypoints` output with the `coordinate` decode) | The flip test averages the raw heatmaps before the decode (`top_down.py:187-192`). A graph with the decode inside cannot give the averaged result from two passes. Also, the graph is the single forward pass of the upstream model (`specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md` part 8, row "Put the flip and the average into the ONNX graph"). | `top_down.py:179-192` |
| A field name `pose.decode.heatmap_refinement` | The other method-specific fields have no method prefix (`coordinate_scale`, `depth_range`; `post/pose-schema.md:95`). Rule -3 limits `refinement` to `heatmap`. A later SimCC refinement (mmpose `use_dark`) can add values to the same field. The skellytracker review can choose the prefixed name: the text changes only in the name. | `post/pose-schema.md:95` |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. (Both ViTPose intakes give the file name in rows K4 and K8
      (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)) and in "Proposals and reference files" with the slug `heatmap-decode-refinement`
      (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). The
      section rows of the same tables name the reference file
      (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). Lines checked again on 2026-10-24.)
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it. (`none`. The two
      sentences on an entry: n/a. No `proposed` entry covers the heatmap decode.)
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plan folder of OpenMMLab-Exporter (plan facts).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a (no pixel case)
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script. (`to run`; part 5
      describes the script and its gates.)
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. n/a (`to run`)
- [x] No file in skellytracker changed.

This proposal has `to run` in part 5. It is ready for a skellytracker session to record. It is not
ready for the user to accept.

## Before acceptance

This list gives the work that must be done before the user can accept the proposal.

**Parts**

- [ ] Part 4 is `unverified`. No host implementation in an exporter or in skellytracker decodes
      heatmaps. An implementation of the spec must pass the 24 cases before `verified_against` can
      name it.
- [ ] Part 5 is `to run`. Get each number of part 5: the export error `E`, the difference of the
      preprocessed input, the row counts and the final outputs for gates 3 to 5.
- [ ] Write and commit the parity scripts `notes/decisions/scripts/heatmap_decode_parity.py` and
      `notes/decisions/scripts/heatmap_decode_parity_worker.py` in OpenMMLab-Exporter. Record their
      commit in part 5.
- [ ] Run the selection pass with the upstream model. Before the gated run, write in part 5 at least
      one COCO image ID and one annotation ID for each branch. If no crop has a maximum `<= 0` or a
      tie, record the deviation from the parity rule for that branch.

**Evidence**

- [ ] Export the ONNX files of `vitposepp-wholebody133` and `vitpose-coco25`. Build the ViTAE
      environment of the exporter image. These are missing primary evidence.
- [ ] The 25-point pipeline B2 has no upstream config. Its decode values come only from a config that
      the exporter creates. That config is not committed.
- [ ] The part 1 numbers for the composition (crop pixels equal, scores equal, source pixels within
      1.2e-4 px) come from scratch scripts that are not committed. They are not evidence. Commit the
      scripts, or use only the part 5 result.
- [ ] Nobody measured the AP effect of the quarter step, the -1 rule and the border rule.
- [ ] Give full-SHA permalinks on the default branch for the upstream sources. The proposal cites
      ViTAE-Transformer/ViTPose `c050ed2`, easy_ViTPose `bb98603` and the Hugging Face checkpoint
      `e838052` by short SHA. It cites mmpose v1.3.2 by tag only. The proposed Authoring guidance
      also cites mmpose by tag.
- [ ] The header says that the exporter commit `f3aeb47` is not pushed. That text is out of date:
      `origin/main` of OpenMMLab-Exporter contains `f3aeb47` (merge `7763f72`). The exporter must
      correct the header.

**Template checklist**

- [ ] The item "Part 2.1 lists each place that the change edits" is not fully true. 2.1 does not list
      the `tools/tests` test that runs each reference function against the vectors of its section
      (decision [0013](../../../../notes/decisions/0013-spec-structure.md)). 2.1 does not list the
      change that makes `tools/make_vectors.py` call the reference file in place of a copy of the
      formulas.
- [ ] 2.1 does not say if `specs/model-sidecar/inventory.yaml` gets `proposed` rows for
      `vitposepp-wholebody133` and `vitpose-coco25`. The inventory has no row for them now.

**Vectors and tooling**

- [ ] Convert the 24 cases to the form of `tools/make_vectors.py`. `CASE_KEYS` in
      `tools/tests/test_vectors.py` has no `function` key. Decide one form for all proposals: add
      `function` to `CASE_KEYS`, or select the function by the prefix of the case ID.
- [ ] The tolerance text of 2.1 (row `tools/tests/test_vectors.py`) is not correct.
      `test_cases_have_the_documented_shape` requires a `tolerance` only when `has_fraction` is
      true, and forbids it when `has_fraction` is false. `clean()` writes each whole float as an
      integer. After the conversion, 14 cases need a `tolerance`. These 10 cases must not have one:
      `low-score-zero`, `low-score-negative`, `low-score-small-positive`, `quarter-cell-1-no-step`,
      `quarter-cell-w-minus-1-no-step`, `quarter-y-border-blocks-x`,
      `quarter-cell-h-minus-1-no-step`, `quarter-minus-one`, `pixel-vitpose-ratio-4` and
      `decode-flat-zero`.
- [ ] Add a key to `TOLERANCE` in `tools/make_vectors.py`, and choose its value. The keys now are
      `resize`, `unprojection`, `normalize` and `selection`.
- [ ] `clean()` also writes the whole-float inputs as integers, for example the all-zero heatmap of
      `decode-flat-zero`. The generator and the reference test must cast each `heatmap` input to
      float32, as the runner of part 4 did. If they do not, the score dtype and the `<= 0` compare
      use integer arrays.
- [ ] Define how the tuple results of the reference functions map to the `expect` names (`cell_x`,
      `cell_y`, `score`, `x`, `y`, `pixel`, `keypoints`). The reference file does not define this
      map.
- [ ] Decide how `tools/make_vectors.py` and the tests import
      `specs/model-sidecar/reference/post_pose_decode_heatmap.py`. That folder is not a Python package, and
      it does not exist yet.
- [ ] The docstring of the reference file has text that is stale in skellytracker, for example
      "specs/model-sidecar/reference/ does not exist in the checkout". Decide who changes the docstring
      before the file goes into `specs/model-sidecar/reference/`.
- [ ] Put the vector file, the `vectors:` key of the front matter and the `BUILDERS` entry in one
      PR. `tools/tests/test_traceability.py` and `tools/tests/test_vectors.py` fail if one of them
      is missing.

**Decisions for the user**

- [ ] Accept or reject the proposal. Part 5 is `to run`, so the proposal is not ready to accept.
- [ ] Choose the field name: `pose.decode.refinement` or `pose.decode.heatmap_refinement`. Part 8
      gives this choice to the skellytracker review.
- [ ] The legacy row of 2.6 gives the tie order, the raw-maximum score and the scale for
      `schema_version < vNEXT`. The old text does not give them. Decide if this is a clarification
      or a change of the legacy meaning. `AGENTS.md` section 4 forbids a change of the legacy meaning.
- [ ] 2.6 says that no rule rejects `pose.decode.refinement` in a legacy sidecar. The reference
      function `heatmap_decode` raises `ValueError` for `legacy=True` with a refinement. Other
      proposals use a validation rule or the legacy row only. Decide one policy for all proposals.
- [ ] 2.1 adds a link to "Version-aware compatibility" in `format/versioning.md`. Some other
      proposals with a new "Legacy behaviour" heading do not add the link. Decide one rule for all.
- [ ] The Shape key sentence of 2.1 gives the cell-to-pixel scale. The Behaviour text of 2.3 also
      gives it. Decide if the sentence duplicates a rule that one section must own (decision
      [0013](../../../../notes/decisions/0013-spec-structure.md)).
- [ ] 2.1 puts new Implementer guidance and Authoring guidance text in the content change. The skill
      `change-sidecar-spec` puts guidance in a later non-spec PR. Decide the PR for this text.
- [ ] Decision 0013 says "There is no reference implementation yet." This text becomes stale when the
      first reference file lands. Decide how to record this.
- [ ] Plan T3, T5, T7, T9, T11, T12 and O8, and the B2 pipeline choice, are only in the untracked
      pose-models plan of OpenMMLab-Exporter. Confirm that these plan facts are a sufficient source.
- [ ] The copy replaced the Docker Hub user name of the exporter image in part 5 with `<user>`.
      Confirm this redaction.

**Merge points**

- [ ] `pose-decode-flip-test` must land first. 2.3 links `pose-flip-test.md#behaviour`. The
      Authoring guidance links `pose-flip-test.md#fields`. 2.4 names `V-post.pose.flip_test-3`, and
      `tools/tests/test_traceability.py` fails when a section file names a rule ID that no section
      defines.
- [ ] This proposal and `pose-decode-flip-test` add the same sentence ("the host decodes the averaged
      outputs") to the Behaviour bullet of `post/pose-decode-heatmap.md`. `pose-decode-flip-test`
      puts it at the start of the bullet. This proposal puts it after the second sentence. Decide
      the position.
- [ ] `simcc-score-rule` adds the same -1 rule to `post.pose.decode.simcc`. Part 8 uses that rule as a
      reason against "No -1 rule". If the user rejects `simcc-score-rule`, examine that reason again.
- [ ] Other proposals edit the same text: the legacy row and the list "Version-aware compatibility"
      of `format/versioning.md`, the `pose.decode` fields and the Shape key of
      `post/pose-schema.md`, row K4 of `templates/model-intake.md`, "Compatibility impact",
      "Summary of changes" and the `vNEXT` row of `changelog.md`, and the vector tooling. The header
      row "Needed by" gives the proposals for each place. The content PR that lands second rebases
      on the first and keeps the edits of both.
