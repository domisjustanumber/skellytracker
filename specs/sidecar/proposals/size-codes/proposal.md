---
slug: size-codes
section: common.sizes
exporter: OpenMMLab-Exporter
decision: "0046"
state: recorded
---

# Change proposal: size-codes

This file is informative. It is not part of the normative spec until a content PR lands its text in the section files (decision [0036](../../../../notes/decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `size-codes`, at OpenMMLab-Exporter commit [`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1), copied on 2026-10-25. The `python` code block at the end of part 3 is the OpenMMLab-Exporter reference file of the proposal, copied on the same date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote no part.

This file uses ASD-STE100 Simplified Technical English.

**Status of this file.** The user decided the questions S1 to S9 on 2026-10-23
(the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). This version applies them. Each value has its source: "user
decision" (T13, T16, T17, S1 to S9, and the model-id decision Q2) or "proposal choice" (a choice of
this proposal that the user can change at review). The reserved key `default`, its rule
`V-common.sizes-4` (valid only when `sizes` has one key) and the filter guidance "a size filter never
selects it" (2.3) are user decision S2. The user approved this spec form on 2026-10-23
(the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). This closes the open question L1.

## Header

| Field | Value |
|---|---|
| Title | Size keys: an alias map of size codes, and the forms of a size key |
| Slug | `size-codes` |
| Date | 2026-10-23 (first version; updated the same day with the user decisions S1 to S9); updated 2026-10-24 (exporter commit `f3aeb47`, merge points) and 2026-10-25 (skellytracker pin `dom/21-move-sidecar-guide`, plan line numbers, secondary marks) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed; `git status --porcelain` is empty). It holds OpenMMLab-Exporter decision 0042 (commit `1dfec48`: the pipeline writes `source`, and the RTMDet and RTMW writers write `{filename, sha256}`) and OpenMMLab-Exporter decision 0050 (commit `f3aeb47`: no family writes a sidecar while its intake is not `describes`). First written at `d0f4343812cc582b4b0020e5b532c83572d11fd2` ("Use the {family}-{keypoints}[-{training}] model_id for RTMO and RTMW (0039)"), which holds the T14 edits of `rtmw/identity.py` and `rtmo/identity.py`. Checked again at `f3aeb47` on 2026-10-24: the cited lines of `rtmw/identity.py`, `rtmo/identity.py`, `rtmdet_person/identity.py`, `export_all.py` and `mmdeploy-convert/CONFIG_SOURCES.md` do not change. From `d0f4343` (OpenMMLab-Exporter decision 0042), `rtmdet_person/sidecar.py:30` is now `:31`, `rtmdet_person/sidecar.py:135` is now `:136`, and `pipeline/sidecar.py:82` is now `:118`; 2.6 and part 7 cite the lines at `f3aeb47`. `plans/` is not in git, and another session edits the untracked pose-models plan of OpenMMLab-Exporter (plan facts) at the same time. Its line numbers in this proposal are of the read of 2026-10-24 20:39:29 (file time). They hold at the file of 2026-10-25 08:10:09 (file time; checked on 2026-10-25). The row IDs (T13, T16, T17, S1 to S9, step 3.6) also identify the text. |
| Model, and its intake file | Every family of this exporter. Shipped: `rtmdet-person` (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts)), `rtmw-wholebody133` (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)), `rtmo-coco17-body7` (the untracked intake of `rtmo-coco17-body7` of OpenMMLab-Exporter (plan facts)); row F3 of each intake. Planned: `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts), row F3), `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), row F3), `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), row F3) and `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), row F3). The other exporters of part 7 use the same keys. |
| Intake rows with the verdict `near-miss` or `gap` | none. The current text allows any lowercase token (`common/sizes-and-artifacts.md:33`), so each size row is `exact` (for example DWPose row F3, the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts); Halpe26 row F3, the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)). The driver is the user decision T17 of 2026-10-23 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)): one code table for every exporter. The user decisions S1 to S9 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) set its form. |
| Kind | `new section` |
| Proposed section ID | `common.sizes` (title "Size keys"). The skellytracker session sets the final ID (`specs/sidecar/templates/change-proposal.md:53-54`). Part 8 gives the other choice: a change to `common.sizes_and_artifacts`. |
| Section file | `specs/sidecar/common/size-keys.md` (proposed) |
| Depends on | `specs/sidecar/proposals/model-id-suffix/proposal.md`, because the examples use the T14 ids of that proposal. (1) The `vNEXT` example names of the `format.file_layout` edits (2.1) use the keypoint `model_id` form `{family}-{keypoints}[-{training}]` and its folder form (`rtmw-wholebody133-m_fp32.onnx`, `rtmw/wholebody133/`). The current text has `{family}-{part}` in a part folder (`format/file-layout.md:75`; `common/identity.md:80`). (2) The note on `V-common.identity-8` in 2.4 uses the proposed `V-common.identity-8` of that proposal. The alias map, the grammar and `V-common.sizes-1` to `-4` do not depend on that proposal. If this proposal lands first, use current-format names in the file-layout examples (for example `rtmw-wholebody-m_fp32.onnx`) and leave out the note of 2.4. |
| Needed by | OpenMMLab-Exporter plan step 3.6 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)): the rtmdet-person rename and a test that checks each identity `size_key` against the table (`:600-602`). `specs/sidecar/proposals/model-id-suffix/proposal.md` does not need this proposal, but the two proposals touch each other in four places. Another session can change that file, so this row gives the heading and the case ID with each line number (lines checked again on 2026-10-24). (1) Both proposals edit `format/file-layout.md:30` and the examples at `format/file-layout.md:85-88`. That proposal keeps the example `rtmw-wholebody-l-m_fp32.onnx` as a legacy file (part 2.1, row `format.file_layout`, `specs/sidecar/proposals/model-id-suffix/proposal.md`; its header, `:20`). This proposal replaces it with `rtmw-wholebody133-m_fp32.onnx` (user decision S6). The second content PR must rebase on the first. (2) Its bullet "Sizes and training tokens" (part 2.3, `:316-331`) says that `V-common.identity-7` cannot detect a size name as a training token, because a size name can be any lowercase token. That stays true with this proposal: a free word is a valid size key (user decision S1). (3) Its collision vectors `artifacts-size-like-training-collision` (size `m-l`) and `artifacts-training-like-size-collision` (size `body7-m`) (`:321-326`) use keys that `V-common.sizes-1` rejects (part 4, cases `key-m-l` and `key-training-like`). A collision with valid keys exists (2.4: `body7-256` and `256`). Thus its `V-common.identity-8` is necessary also for `vNEXT` keys. (4) Its user decision Q2 ("User decisions after T14", `:238`, bullet Q2, `:255-256`): two models with the same keypoint output and the same training set are two sizes of one sidecar when the family invariant holds. The MediaPipe face landmark models are such a case. The user decision S3 gives their size keys: `192` and `256`. The option "two `model_id`s" of the earlier open question Q3 of this proposal is ruled out. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide` (checked on 2026-10-25). `format/versioning.md:53-63` (the list "Version-aware compatibility": new links): `simcc-score-rule`, `heatmap-decode-refinement`, `affine-crop-arithmetic`, `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter); `common/sizes-and-artifacts.md:101`: `model-id-suffix`; `format/file-layout.md:27-30` (file naming): `model-id-suffix`; `format/file-layout.md:44-89` (the storage tree, the branch table, the examples): `model-id-suffix`, `roi-refiner-role` (MediaPipe-Exporter); `specs/sidecar/README.md:18-19` ("Core properties"): `model-id-suffix`; `exporter-guide/sidecars/workflow/mapping-hints.md:13-32` ("Mapping hints", Identity and Family): `model-id-suffix`, `roi-refiner-role` (MediaPipe-Exporter); the reference examples under `examples/detectors/keypoint_detectors/` (`rtmo`, `rtmw`, `yolo26`): `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`, `affine-crop-arithmetic`, `model-id-suffix`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property | none. The index lists no entry for size names (`notes/decisions/README.md:23-71` at `dom/21-move-sidecar-guide`; the `proposed` rows are `:36-44`). Related, not the same property: skellytracker decision 0025 (`model_id` suffix, `notes/decisions/README.md:44`) and the accepted skellytracker decision 0016 (an unknown size name is an error, `specs/sidecar/format/versioning.md:87`). |
| skellytracker folder that you read | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (branch `dom/sidecar-implementation`; checked on 2026-10-25; `git status --porcelain` lists only one untracked `grep.exe.stackdump`, a Windows crash file, not a file that this proposal reads). Earlier reads: `dom/12-single-working-branch`, then `dom/18-agents-adr-bootstrap-kit`. From `dom/18-agents-adr-bootstrap-kit` to `dom/21-move-sidecar-guide`, the guide moved to `specs/exporter-guide/sidecars/` (skellytracker decisions 0033 and 0034), only link text changed under `specs/sidecar/` (no line moved), and the decision index gained rows. Every cited spec, template, tool, example and package line holds at `dom/21-move-sidecar-guide`. Guide citations point to the 0034 layout. |

## 1. Gap

| Item | Value |
|---|---|
| Property | A size key names one size of a model in a family. The spec gives no spelling for a size. Two exporters can spell one size two ways (`medium` and `m`). Thus a reader, a file name and an exporter CLI cannot find one size in the families of two exporters with one key. The spec also gives no form for a key that holds an input size, and its hyphen examples are not sizes of the end model. |
| Upstream evidence | Upstream names a size with a letter or with a word. **Letters:** Ultralytics weights `yolo26n.pt`, `yolo26s.pt`, `yolo26m.pt`, `yolo26l.pt`, `yolo26x.pt` (Ultralytics-Exporter `yolo_sidecar.py:176-180`, `2e0280e`). mmpose v1.3.2 RTMO `rtmo-t`, `rtmo-s`, `rtmo-m`, `rtmo-l` (OpenMMLab-Exporter `mmdeploy-convert/CONFIG_SOURCES.md:28-31`); RTMW `rtmw-m`, `rtmw-x`, `rtmw-l` (`CONFIG_SOURCES.md:23-27`); RTMPose Halpe26 `rtmpose-t` to `rtmpose-x` (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; primary: the mmpose v1.3.2 config names `configs/body_2d_keypoint/rtmpose/body8/rtmpose-{t,s,m,l,x}_8xb*-700e_body8-halpe26-{256x192,384x288}.py`, which that table lists; the Halpe26 intake row F3, the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)); RTMDet person `rtmdet_m` (`CONFIG_SOURCES.md:21`). easy_ViTPose `s`, `b`, `l`, `h` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts), row F3, which cites `easy_ViTPose/inference.py:58-60`). The installed Ultralytics also lists `yolov9{t,s,m,c,e}.pt` and `yolov10{n,s,m,b,l,x}.pt` (`ultralytics/utils/downloads.py:37, 39`). No exporter ships them. RF-DETR segmentation URLs `rf-detr-seg-n-ft.pth` to `rf-detr-seg-2xl-ft.pth` (Roboflow-Exporter `.venv/Lib/site-packages/rfdetr/assets/model_weights.py:244-269`, rfdetr 1.11.2). **Words:** RTMDet `rtmdet_nano` (`CONFIG_SOURCES.md:22`) and `rtmdet_tiny` (the removed COCO-80 shims, OpenMMLab-Exporter `notes/decisions/0017-person-detectors-only.md:13`); ViTAE `configs/wholebody/2d_kpt_sview_rgb_img/topdown_heatmap/coco-wholebody/ViTPose_{small,base,large,huge}_wholebody_256x192.py` at ViTAE `c050ed2` (primary: the config file names; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; the ViTPose++ intake row F3, the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts)); the backbone `cspnext-tiny` of RTMPose `t` (primary: the `init_cfg` checkpoint `cspnext-tiny_udp-body7_210e-256x192-a3775292_20230504.pth` in the mmpose v1.3.2 config `rtmpose-t_8xb1024-700e_body8-halpe26-256x192.py:74-78`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary); the RF-DETR classes `RFDETRBase` (`rfdetr/variants.py:64`), `RFDETRSegXLarge` and `RFDETRSeg2XLarge` (`rfdetr/variants.py:219, 230`) and the file names `rf-detr-seg-xlarge.pt` and `rf-detr-seg-xxlarge.pt` (`model_weights.py:263, 268`); MediaPipe `lite`, `full`, `heavy` (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary, no git repo). **Input sizes:** MediaPipe face landmark `holistic` at 192x192 and `landmarker` at 256x256 (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). |
| Nearest section ID | `common.sizes_and_artifacts` |
| Why the nearest section is wrong | (1) "Size names are lowercase tokens such as `nano`, `small` and `medium`. A size name can contain hyphens, for example `l-m` and `x-l`." (`common/sizes-and-artifacts.md:33`). The text gives no spelling for a size. The exporter guide tells the exporter to use the upstream size name (`exporter-guide/sidecars/workflow/mapping-hints.md:30-32`; intake row F3, `templates/model-intake.md:231`). Upstream uses letters and words (row above), so the keys of one size differ. (2) The hyphen examples are not sizes of the end model. `l-m` and `x-l` come from the upstream distilled checkpoints `rtmw-dw-l-m` (teacher `l`, student `m`) and `rtmw-dw-x-l` (teacher `x`, student `l`) (user decision S6, the untracked pose-models plan of OpenMMLab-Exporter (plan facts); skellytracker `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml:74, 87`). OpenMMLab-Exporter exports `rtmw-dw-l-m` as the size `m` (`rtmw/identity.py:97, 102`) and `rtmw-dw-x-l` as `l-256` and `l-384` (`rtmw/identity.py:108, 113`, `:130, 135`; OpenMMLab-Exporter decision 0032, `notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:12-15`). (3) The text gives no form for a key with an input size. OpenMMLab-Exporter writes `l-256` and `l-384` (`rtmw/identity.py:108, 130`). The skellytracker package writes `rtmw-x-l_384x288` (`rtmw-wholebody.yaml:89`). |
| Measured difference (number, image and script) | No tensor changes, so the difference is a count of keys. Six shipped families have a medium size: `rtmdet-person` (`medium`, OpenMMLab-Exporter `rtmdet_person/identity.py:127`), `rtmw-wholebody133` (`m`, `rtmw/identity.py:97`), `rtmo-coco17-body7` (`m`, `rtmo/identity.py:134`), `yolo26` and `yolo26-body` (`medium`, Ultralytics-Exporter `yolo_sidecar.py:178, 186`) and `rfdetr` (`medium`, Roboflow-Exporter `rf_detr/identity.py:11`, `c64fd2a`). They use two spellings: `medium` in 4 of 6 and `m` in 2 of 6. After the renames of part 7, 6 of 6 use `m`. An exporter CLI that filters by key shows the effect: in OpenMMLab-Exporter, `--sizes m` selects 2 of its 3 medium-size families today (`export_all.py:261`; T16, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The part 4 cases `select-m-legacy-rtmdet-person` and `select-m-renamed-rtmdet-person` show this. |
| Row in "Considered and deliberately not added", and the evidence that a model needs it now | none. The table has no size-name row (`specs/sidecar/changelog.md:42-53`). |

The shipped keys for one size today:

| Size | Keys in shipped sidecars | Source |
|---|---|---|
| nano | `nano` | Ultralytics-Exporter `yolo_sidecar.py:176, 184`; Roboflow-Exporter `rf_detr/identity.py:11`; OpenMMLab-Exporter `rtmdet_person/identity.py:115` |
| tiny | `t`, `yolox-tiny` | OpenMMLab-Exporter `rtmo/identity.py:110`; skellytracker `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml:37` (legacy) |
| small | `small`, `s`, `rtmpose-s_256x192` | Ultralytics-Exporter `yolo_sidecar.py:177`; Roboflow-Exporter `rf_detr/identity.py:11`; OpenMMLab-Exporter `rtmo/identity.py:122`; skellytracker `rtmpose/body/rtmpose-body.yaml:51` (legacy) |
| medium | `medium`, `m`, `yolox-m`, `rtmpose-m_256x192`, `rtmw-l-m_256x192` | the medium row above; skellytracker `yolox/yolox.yaml:50`, `rtmpose/body/rtmpose-body.yaml:64`, `rtmw/wholebody/rtmw-wholebody.yaml:63` (legacy) |
| large | `large`, `l`, `l-256`, `l-384`, `rtmw-x-l_256x192`, `rtmw-x-l_384x288` | Ultralytics-Exporter `yolo_sidecar.py:179`; Roboflow-Exporter `rf_detr/identity.py:11`; OpenMMLab-Exporter `rtmo/identity.py:146`, `rtmw/identity.py:108, 130`; skellytracker `rtmw/wholebody/rtmw-wholebody.yaml:76, 89` (legacy) |
| xlarge | `xlarge`, `x-256`, `x-384` | Ultralytics-Exporter `yolo_sidecar.py:180`; OpenMMLab-Exporter `rtmw/identity.py:119, 141` |
| one size, no size name | `default` | Qualcomm-Exporter `qai_catalog.py:39`, `qai_sidecar.py:156-157` (`4ca4586`) |

## 2. Spec change

### 2.1 Sections

New section `common.sizes`, title "Size keys", file `specs/sidecar/common/size-keys.md`.

Front matter:

```yaml
id: common.sizes
title: Size keys
kind: common
since: vNEXT
changed_in: []
selectors: []
implemented_by:
  validate: missing
  load: missing
external_impl: []
tests: []
vectors: vectors/common.sizes.yaml
status: {spec: draft, validate: missing, load: missing}
```

`selectors: []`: the section applies to every sidecar, as `common.sizes_and_artifacts` does
(`common/sizes-and-artifacts.md:7`). The spec state is `draft`, as for each new section of a
proposal (`specs/sidecar/proposals/pose-decode-flip-test/proposal.md`, part 2.1).

Row in the section map (`specs/sidecar/README.md`, after the row of `common.sizes_and_artifacts` at
line 53):

```text
| `common.sizes` | [common/size-keys.md](common/size-keys.md) | Size keys |
```

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `common.sizes_and_artifacts` (`common/sizes-and-artifacts.md`) | "Fields", `sizes` (line 33) | Replace the last two sentences ("Size names are lowercase tokens such as `nano`, `small` and `medium`. A size name can contain hyphens, for example `l-m` and `x-l`.") with: "Each key of `sizes` is a size key. See Size keys (`size-keys.md#fields`)." |
| `common.sizes_and_artifacts` | "Fields", `sizes` (line 47) | No edit. The first size stays the default, and the writer chooses the order (user decision S5). Host selection stays out of scope (user decision S8). |
| `common.sizes_and_artifacts` | "Behaviour", "Model sizes within a family" (line 101) | Change "`yolo26` ships `nano`, `small` and `medium`" to "`yolo26` ships `n`, `s` and `m`". |
| `common.sizes_and_artifacts` | "Validation rules" (line 122) | Add "See also Size keys (`size-keys.md#validation-rules`)." |
| `common.sizes_and_artifacts` | "Authoring guidance" (lines 153-199) | Add one bullet: "Write the upstream size name as its size key. See Size keys (`size-keys.md#authoring-guidance`)." Do not edit the evidence bullets (lines 158, 160, 162-164). They cite the keys of named exporter commits, and those keys stay true for those commits. |
| `common.sizes_and_artifacts` | "Examples" (lines 203-232) | Change the keys `nano` and `small` to `n` and `s`, and the filenames to `yolo26-n_b1_fp32.onnx` and so on. Change the comment at line 205 from "medium/large/xlarge" to "m/l/x". |
| `common.identity` (`common/identity.md`) | "Fields", `sizes` row (line 32) | Change "A map of size name → size definition" to "A map of size key → size definition. See Size keys (`size-keys.md`)." |
| `format.file_layout` (`format/file-layout.md`) | "File extension and naming" (lines 28, 30) | Change `yolo26-nano_b2_fp16.onnx`, `yolo26-small_b4_fp32.onnx` and `yolo26-nano_b2_fp32.onnx` to `yolo26-n_b2_fp16.onnx`, `yolo26-s_b4_fp32.onnx` and `yolo26-n_b2_fp32.onnx`. Replace the dynamic-batch example `rtmw-wholebody-l-m_fp32.onnx` with `rtmw-wholebody133-m_fp32.onnx` (user decision S6: `l-m` is the RTMW student `m`). The model-id proposal keeps the old example (see the Header). |
| `format.file_layout` | "Storage layout", examples (lines 78-89) | Change `yolo26-nano_*` and `yolo26-small_*` (lines 81-83) to `yolo26-n_*` and `yolo26-s_*`. Replace the folder `rtmw/wholebody/` and the files `rtmw-wholebody.yaml`, `rtmw-wholebody-l-m_fp32.onnx` and `rtmw-wholebody-x-l_fp32.onnx` (lines 85-88) with the folder `rtmw/wholebody133/` and the files `rtmw-wholebody133.yaml`, `rtmw-wholebody133-m_fp32.onnx` and `rtmw-wholebody133-l-256_fp32.onnx` (the folder form of the model-id proposal). The size of `x-l` is `l` (user decision S6). The choice of `l-256` and not `l-384` is a proposal choice: the 256x192 checkpoint `rtmw-dw-x-l_..._256x192` is the size `l-256` (`rtmw/identity.py:108, 113`). |
| `format.file_layout` | "Authoring guidance" (lines 141-149) | No edit. The bullets cite the file names of named exporter commits. |
| `format.composition` (`format/composition.md`) | Examples (lines 101, 107, 111, 133) | Change `sizes.nano` and `nano:` to `sizes.n` and `"n":`, and `yolo26-int8-nano_b1_int8.onnx` to `yolo26-int8-n_b1_int8.onnx`. |
| `specs/sidecar/README.md` | "Core properties" (line 19) | Change "for example `nano`, `small` and `medium`" to "for example `n`, `s` and `m` (see Size keys (`common/size-keys.md`))". |
| `specs/sidecar/README.md` | Section map (line 53); "Validation rules" (lines 97-109) | Add the section row. Add the link "Size keys (`common/size-keys.md#validation-rules`)" after "Sizes and artifacts" (line 104). |
| `format.versioning` (`format/versioning.md`) | "Version-aware compatibility" list (lines 53-63) | Add "Size keys (`../common/size-keys.md#legacy-behaviour`)" after "Sizes and artifacts" (line 56). The section has a legacy meaning: any lowercase token (2.6). |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | "Mapping hints for phase 1", **Family** (lines 30-32) | Replace "The spec allows any lowercase token as a size name. Use the size name of the upstream, also for a family with one size. If the upstream has no size name, choose a token and write the reason in the intake." with: "Write the upstream size name as its size key (`common.sizes`, `../freemocap/skellytracker/specs/sidecar/common/size-keys.md`). If the name is in the alias table, write its code. If it is not in the table, write the upstream word. Add the input height only when the family has one word at two input heights, and the width only when the height does not separate two sizes. If the family has one size and the upstream gives it no size name, write `default`." |
| `specs/sidecar/templates/model-intake.md` | Row F3 (line 231) | Replace "Use the upstream size name, also for a family with one size. If the upstream has no size name, choose a lowercase token and give the reason." with "Write the upstream size name as its size key (`common.sizes`). Give the upstream name and the key." Add the link to `common.sizes` in the spec-section column. Line 144 (F3 takes its value from the spec) does not change. |
| `specs/sidecar/examples/` | `detectors/object_detectors/rtmdet-person/rtmdet-person.yaml` (lines 50, 59-60, 66-67, 71, 80-81 and the other artifact lines of `medium`) | Copy the file again from an OpenMMLab-Exporter export after the rename of part 7 (`nano` > `n`, `medium` > `m`). Do not edit it by hand: the procedure copies the exporter file byte for byte (`exporter-guide/sidecars/workflow/phase-3-skellytracker.md:9-12`). |
| `specs/sidecar/examples/` | `detectors/object_detectors/yolo26/yolo26.yaml` (lines 41, 50-66, 69) and `detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml` (lines 86, 95 and the other artifact lines) | Change `nano` to `"n"` and the filenames to `yolo26-n_*` and `yolo26-body-n_*`. The code of Ultralytics-Exporter is the source of these examples (`changelog.md:31`), so the content PR can edit them. Change the comment at `yolo26.yaml:69` to "s, m, l, x". |
| `specs/sidecar/examples/` | `detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` (`m`, `l-384`, lines 64, 75) and `detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` (`m`, line 102) | No edit. The keys are valid. `l-384` has `input.shape: [-1, 3, 384, 288]` (`rtmw-wholebody.yaml:77`), so it passes `V-common.sizes-2`. |
| `specs/sidecar/inventory.yaml` | Notes of the rtmdet-person example (lines 65-67) | Change "nano" and "medium" to "n" and "m" when the example is copied again. |
| `specs/sidecar/changelog.md` | "Summary of changes", `schema_version` history | Add the rows of 2.7. |
| `tools/make_vectors.py` | The vector builders | Add a builder for `common.sizes` that writes the cases of part 4. The test requires that `vectors/` holds exactly the files that this script writes, that each file is equal to the script output, and that each file has `generated_by: tools/make_vectors.py` (`tools/tests/test_vectors.py:110-116, 141`). The script already writes `n` in quotes (`tools/make_vectors.py:172-173`). |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (lines 32-40) and the case check (line 175) | Each case of part 4 has the key `function`, as the template asks (`templates/change-proposal.md:242, 256`). `CASE_KEYS` does not allow `function`. Add `function` to `CASE_KEYS`, or let the builder leave it out. The template and the test do not agree on `function` and on `generated_by` (`templates/change-proposal.md:251`). This conflict is not special to this proposal. The skellytracker session decides it. |
| `specs/sidecar/TRACEABILITY.md` | Generated matrix | Do not edit it by hand. Run `python tools/sidecar_trace.py matrix` after the section file is in place. |
| `specs/sidecar-spec.md` | The permanent index | No edit. The index keeps only the headings of the old single-file spec (skellytracker decision 0013). |
| Evidence prose: `common/batching.md:47, 50`, `post/selection-none.md:65`, `post/pose-bottom-up.md:85`, `post/selection-nms.md:80`, `post/selection-top-k.md:61`, `post/detection-outputs.md:82`, `pre/resize-letterbox.md:88`, `pre/interpolation.md:51` | Implementer and authoring guidance | No edit. These bullets name sizes by words in measured evidence, and some cite report paths (`yolo26-<size>_b<N>_fp16.report.json`, `common/sizes-and-artifacts.md:140`). A rename would break the citation. |

### 2.2 Fields table

| Field | Type | Required | Description |
|---|---|---|---|
| key of `sizes` (`sizes.<key>`) | string | yes (one or more keys, `V-common.sizes_and_artifacts-1`) | A size key. Its forms are a word, a word with input dims (`<word>-<height>` or `<word>-<height>x<width>`), input dims alone (`<height>` or `<height>x<width>`), or the reserved key `default`. A word is a code of the alias table or a free word. The source of each form is in 2.3 ("Grammar"): some forms are user decisions (S1, S2, S3, S8), and the others are proposal choices. Examples: `n`, `m`, `lite`, `l-256`, `m-256x256`, `192`, `default`. See 2.3. |

The section adds no field. It sets the form of the keys of the existing `sizes` map.

### 2.3 Behaviour

The normative text of the section "Behaviour":

**Alias table.** The table joins the spellings of one size into one code. A sidecar writes the
code. The table is not a closed list: a word that is not in the table is a free word, and it is
valid as it is (user decision S1). The table is not a size order. The spec defines no order between
two codes or two words (user decisions S1, S5 and S7). The name is the written form of the code in
prose and in a `display_name`.

| Code | Name | Aliases (write the code) | Source of the choice |
|---|---|---|---|
| `n` | nano | `nano` | user decision T17 |
| `t` | tiny | `tiny` | user decision T17 |
| `s` | small | `small` | proposal choice |
| `m` | medium | `medium`, `med` | user decision T17 (`medium`); user decision S1 (`med`) |
| `b` | balanced | `balanced`, `base` | user decision S7 |
| `l` | large | `large` | proposal choice |
| `x` | xlarge | `xlarge`, `xl` | proposal choice |
| `2xl` | 2xlarge | `2xlarge`, `xxlarge`, `xxl` | user decision S4 (`2xl`, `2xlarge`, `xxl`); proposal choice (`xxlarge`) |
| `h` | huge | `huge` | proposal choice |

A size name gives the size of the end model. It does not give the size of a teacher model (user
decisions S6 and S7).

The evidence for each choice:

- `s` = small (proposal choice). Ultralytics `yolo26s.pt` and the key `small` (Ultralytics-Exporter
  `yolo_sidecar.py:177`); RTMO `rtmo-s` (OpenMMLab-Exporter `CONFIG_SOURCES.md:29`); RTMPose Halpe26
  `rtmpose-s` (the mmpose v1.3.2 config name `rtmpose-s_8xb1024-700e_body8-halpe26-256x192.py`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary); ViTAE `ViTPose_small` (the config name `ViTPose_small_wholebody_256x192.py` at ViTAE `c050ed2`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary);
  RF-DETR `small` (Roboflow-Exporter `rf_detr/identity.py:11`) and `rf-detr-seg-s` (`model_weights.py:249`).
- `l` = large (proposal choice). Ultralytics `yolo26l.pt` and the key `large` (`yolo_sidecar.py:179`);
  RTMO `rtmo-l`, RTMW `rtmw-l` (`CONFIG_SOURCES.md:26-27, 31`); ViTAE `ViTPose_large` (ViT-L: `embed_dim=1024`, `depth=24`,
  `ViTPose_large_coco_256x192.py:50-51` at ViTAE `c050ed2`; the config name
  `ViTPose_large_wholebody_256x192.py`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary); RF-DETR `large` (`rf_detr/identity.py:11`).
- `x` = xlarge, with the alias `xl` (proposal choice). Ultralytics `yolo26x.pt` with the key `xlarge`
  and the display name "YOLO26 XLarge" (`yolo_sidecar.py:180`); RTMW `rtmw-x` (`CONFIG_SOURCES.md:24-25`);
  RTMPose `rtmpose-x` (the mmpose v1.3.2 config name `rtmpose-x_8xb256-700e_body8-halpe26-384x288.py`;
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary); the removed COCO-80 RTMDet `rtmdet_x` with
  the name "xlarge" (OpenMMLab-Exporter `notes/decisions/0017-person-detectors-only.md:7, 13`); the
  RF-DETR class `RFDETRSegXLarge` (`rfdetr/variants.py:219`). RF-DETR writes the same model as `xl` in
  its URL and as `xlarge` in its file name (`rf-detr-seg-xl-ft.pth`, `rf-detr-seg-xlarge.pt`,
  `model_weights.py:263-264`). Thus `xl` is an alias of `x`.
- `b` = balanced, with the alias `base` (user decision S7). ViTAE `ViTPose_base` (ViT-B) is between
  `s` and `l` of the end model: about 90 M parameters, against about 24 M for `s` and about 309 M for
  `l` (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary: the plan's own measurement, the fp32 `.pth`
  size divided by 4; primary evidence missing: a parameter count of the loaded checkpoints, `to run`;
  the backbone sizes come from `embed_dim` and `depth` in `ViTPose_{large,huge}_coco_256x192.py:50-51`
  at ViTAE `c050ed2`). easy_ViTPose names it `b`
  (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)). The planned `vitpose-coco25` and
  `vitposepp-wholebody133` need it (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). Two other uses of the letter
  or the word agree with the meaning "a size between two other sizes", because the table has no
  order. (1) The Ultralytics YOLOv10 family has `n`, `s`, `m`, `b`, `l` and `x`
  (`ultralytics/utils/downloads.py:39`). Its scale rows are `m: [0.67, 0.75, 768]`,
  `b: [0.67, 1.00, 512]` and `l: [1.00, 1.00, 512]` (`cfg/models/v10/yolov10m.yaml:11`,
  `yolov10b.yaml:11`, `yolov10l.yaml:11`). No exporter ships YOLOv10. (2) The RF-DETR class
  `RFDETRBase` (`rfdetr/variants.py:64`, deprecated in rfdetr 1.7.0, `variants.py:59-63`) uses the
  encoder `dinov2_windowed_small` at the resolution 560 (`rfdetr/config.py:988, 991, 1004`). No
  exporter exports it. The installed Ultralytics has no text that names `b` "balanced"; the meaning
  is the user decision.
- `2xl` = 2xlarge (user decision S4). RF-DETR `RFDETRSeg2XLarge` (`rfdetr/variants.py:230`), the URL
  `rf-detr-seg-2xl-ft.pth` and the file name `rf-detr-seg-xxlarge.pt` (`model_weights.py:268-269`;
  `rfdetr/config.py:1190`). The user named the spellings `2xlarge` and `xxl`. The alias `xxlarge`
  is a proposal choice from the RF-DETR file name. No exporter ships the model now. The code starts
  with a digit. A free word cannot start with a digit (grammar below), so the code is not ambiguous.
- `h` = huge (proposal choice). ViTAE `ViTPose_huge` (ViT-H: `embed_dim=1280`, `depth=32`,
  `ViTPose_huge_coco_256x192.py:50-51` at ViTAE `c050ed2`; the config name
  `ViTPose_huge_wholebody_256x192.py`; about 637 M parameters, the untracked pose-models plan of OpenMMLab-Exporter (plan facts),
  secondary: the plan's own measurement from the fp32 `.pth` size; primary count `to run`). No
  exporter exports it now (user decision T13, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The code reserves the spelling for a later export.
- `n` and `t` are two codes (user decision T17). RTMDet has both sizes as different models:
  `rtmdet_nano` (`CONFIG_SOURCES.md:22`) and `rtmdet_tiny` (`0017-person-detectors-only.md:13`).
- Free words (user decision S1). MediaPipe `lite`, `full` and `heavy` are valid as they are
  (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts), secondary). The YOLOv9 letters
  `c` and `e` (`ultralytics/utils/downloads.py:37`) are also valid free words.

**Grammar.**

```text
size_key  = word [ "-" dims ] | dims | "default"
word      = code | free_word
code      = "n" | "t" | "s" | "m" | "b" | "l" | "x" | "2xl" | "h"
free_word = lower { lower | digit }      ; not an alias of the table, and not "default"
dims      = height [ "x" width ]
height    = nonzero_digit { digit }       ; no leading zero
width     = nonzero_digit { digit }       ; no leading zero
lower     = "a" ... "z"                   ; ASCII only
digit     = "0" ... "9"                   ; ASCII only
```

- The match is exact. A size key has no uppercase letter, no space, no underscore and no second
  hyphen.
- An alias of the table is not a word. A key of `vNEXT` writes the code: `m`, not `medium`; `m-256`,
  not `medium-256` (user decision S1).
- `height` is the input height of the size in pixels: the height axis of `sizes.<key>.input.shape`
  (`shape[2]` for `NCHW`, `shape[1]` for `NHWC`). `width` is the input width: `shape[3]` for `NCHW`,
  `shape[2]` for `NHWC`. The height comes first, as in the OpenMMLab names: `256x192` is height 256
  and width 192 (user decision S8; OpenMMLab-Exporter decision 0003,
  `notes/decisions/0003-rtmw-height-width.md`).
- The source of each form:

  | Form | Example | Source |
  |---|---|---|
  | `<code>` | `m` | user decisions T17 and S1 |
  | `<free_word>` | `lite` | user decision S1 |
  | `<code>-<height>` | `l-256` | user decision S3 ("a code with a height", the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) |
  | `<code>-<height>x<width>` | `m-256x256` | user decision S8 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) |
  | `<height>` | `192` | user decision S3 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) |
  | `<height>x<width>` | `256x192` | proposal choice |
  | `<free_word>-<height>`, `<free_word>-<height>x<width>` | `lite-256` | proposal choice |
  | `default` | `default` | user decision S2 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) |

- The form `<height>x<width>` with no word is a proposal choice (part 8). It is the same escape as
  for a code, when the height alone does not separate two sizes. A free word starts with a letter,
  so a key of dims alone never matches the word rule.
- The dims on a free word (`<free_word>-<height>`, `<free_word>-<height>x<width>`) are a proposal
  choice. S3 and S8 give the dims only on a code. The proposal uses one `word` rule for a code and a
  free word, so that a free word with two input heights also has a key, and the grammar has one
  `dims` rule. No family needs it today: each planned free word (`lite`, `full`, `heavy`) has one
  input size. The other choice is `size_key = code [ "-" dims ] | free_word | dims | "default"`.
- The reserved key `default` is user decision S2. The user approved this spec form on 2026-10-23:
  "a reserved key, for example `default`, valid only when `sizes` has one key, and no size filter
  matches it" (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). It takes no dims (`default-256` is not a size key).
  This detail of the grammar is a proposal choice: the key names a family with one size, so it has
  no second input size to separate.

**Form of a key.** The form is a property of the upstream sizes of the family, not of the sizes in
one sidecar. This rule is a proposal choice. Its sources: the shipped RTMW keys (`m`, `l-256`,
`l-384`; OpenMMLab-Exporter `rtmw/identity.py:97, 108, 130`), the planned keys of the plan families
table (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary), and the condition of S8 "when the height alone does not
separate two sizes" (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The user decisions give the forms. They do
not give the rule "no key of that word is bare":

- A word with one input size in the family is bare: `m`.
- A word with two or more input heights in the family takes the height on each of its keys:
  `l-256`, `l-384`. No key of that word is bare.
- A word with two sizes at one input height takes the height and the width on each of its keys:
  `m-256x192`, `m-256x256` (the form is user decision S8).
- Sizes with no upstream size name, which their input sizes separate, take dims alone: `192`, `256`
  (the keys are user decision S3).
- A family with one size and no upstream size name takes the key `default` (user decision S2).

Examples (OpenMMLab-Exporter `rtmw/identity.py:97, 108, 119, 130, 141`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary):

| Family | Size keys | Source |
|---|---|---|
| `rtmw-wholebody133` | `m` (256x192 only); `l-256`, `l-384`; `x-256`, `x-384` | `rtmw/identity.py` |
| `rtmpose-halpe26` (planned) | `t`, `s` (256x192 only); `m-256`, `m-384`; `l-256`, `l-384`; `x` (384x288 only) | the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts) |
| `dwpose-wholebody133-ubody` (planned) | `t`, `s`, `m` (256x192 only); `l-256`, `l-384` | the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts) |
| `vitpose-coco25`, `vitposepp-wholebody133` (planned) | `s`, `b`, `l` (256x192 only; no `h`, user decision T13) | the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) |
| MediaPipe pose landmark (planned) | `lite`, `full`, `heavy` (user decision S1) | the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (secondary) |
| MediaPipe face landmark (planned; one sidecar, model-id user decision Q2) | `192`, `256` (user decision S3) | the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts) (secondary) |
| Qualcomm `mediapipe-person-detector` | `default` (user decision S2) | Qualcomm-Exporter `qai_sidecar.py:156-157` |

A sidecar from a partial run can hold `l-256` and no `l-384`. It keeps the key `l-256`. Thus a size
key, a file name and a size id (`<model_id>-<size>`, user decision T14) do not change when a run
adds or removes a size. `V-common.sizes-3` checks only the part that one sidecar can show: one word
has one form in one sidecar.

**Default size.** No change: when no request names a size, the first key is the default
(`common/sizes-and-artifacts.md:47`). The writer chooses the order of the keys (user decision S5).
The table gives no order.

**Inverse.** none: no coordinates.

The proposed "Authoring guidance" of the section:

- Write the upstream size name as its size key. An upstream letter that is a code is the code:
  Ultralytics `yolo26n.pt` gives `n` (Ultralytics-Exporter `yolo_sidecar.py:176`); mmpose `rtmo-t`
  gives `t` (OpenMMLab-Exporter `CONFIG_SOURCES.md:28`). An upstream word in the alias table gives
  its code: RTMDet `rtmdet_nano` gives `n` (`CONFIG_SOURCES.md:22`); ViTAE `ViTPose_base` gives `b`
  (the config name `ViTPose_base_wholebody_256x192.py` at ViTAE `c050ed2`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). Any other upstream word is a free word: MediaPipe `lite` stays
  `lite`.
- A free word must match the grammar. Write it in lowercase, and remove the characters that the
  grammar does not allow (proposal choice, the same method as the keypoint token of the model-id
  proposal). For example, an upstream `Lite` gives `lite`.
- A size name gives the size of the end model, not of the teacher (user decisions S6 and S7). The
  upstream distilled checkpoint `rtmw-dw-l-m` (teacher `l`, student `m`) is the RTMW size `m`.
  `rtmw-dw-x-l` (teacher `x`, student `l`) is the sizes `l-256` and `l-384` (OpenMMLab-Exporter
  `rtmw/identity.py:97, 102, 108, 113, 130, 135`; OpenMMLab-Exporter decision 0032,
  `notes/decisions/0032-rtmw-l-config-pairing-and-backbones.md:12-15`).
- A backbone token or a head token is not a dims part. A backbone with another channel order is a new
  family (OpenMMLab-Exporter decision 0004, `common/sizes-and-artifacts.md:178`), for example the
  RTMDet `l-swin-b` (skellytracker `notes/sidecar-exporter-coverage.md:16`). A larger input of the
  same code is a height: the RTMDet `x-p6` (1280) would be `x-1280` beside `x-640`, if one family
  held both (not exported, OpenMMLab-Exporter decision 0017).
- Write a `display_name` with the name of the table for a code, for example "YOLO26 Nano" for `n`
  (Ultralytics-Exporter `yolo_sidecar.py:176`). The rule for `display_name` does not change.
- Write the size key `n` in quotes in a sidecar: `"n":`, not `n:` (user decision S9). The facts
  (checked on 2026-10-23, PyYAML 6.0.3): PyYAML `yaml.safe_load` reads a bare `n` as the string
  `"n"` (skellytracker reads sidecars with `yaml.safe_load`,
  `skellytracker/core/sidecar/resolution.py:24-27`), and `yaml.safe_dump` writes it with no quotes.
  Only a strict YAML 1.1 parser reads a bare `n` as the boolean false. `tools/make_vectors.py:173`
  quotes `n` for this reason. This is guidance, not a validation rule (user decision S9).
- Write each size key of the YAML reserved set in quotes: `y`, `n`, `yes`, `no`, `on`, `off`,
  `true`, `false`, `null` (proposal choice: S9 names only `n`; the set is the set of
  `tools/make_vectors.py:173`). Each of these words is a valid free word (user decision S1). The
  facts (checked on 2026-10-23, PyYAML 6.0.3): `yaml.safe_load` reads a bare `yes`, `on` or `true`
  as the boolean true, a bare `no`, `off` or `false` as the boolean false, and a bare `null` as
  `None`. The key is then not a str, and `V-common.sizes-1` rejects it. The error does not give the
  reason. `yaml.safe_load` reads a bare `y` as the string `"y"`, but a strict YAML 1.1 parser reads it
  as true, as for `n`. `yaml.safe_dump` writes `yes`, `no`, `on`, `off`, `true`, `false` and `null`
  with quotes, and `y` and `n` with no quotes. The proposal does not remove these words from
  `free_word`, because S1 makes each unknown lowercase word valid.
- Write a key of dims alone in quotes: `"192":`, not `192:`. A bare `192` is a YAML integer, as a
  bare batch key is (`exporter-guide/sidecars/sidecar-files.md:19`), and `V-common.sizes-1` rejects it. PyYAML
  `yaml.safe_dump` writes the string `"192"` with quotes (checked on 2026-10-23).
- Size filters of an exporter CLI (informative; user decision S8). The spec has no rule for a host
  that selects sizes (`common/sizes-and-artifacts.md:47`). An exporter CLI that filters its exports by
  size can use the rule of the OpenMMLab-Exporter CLI (user decision T16,
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts)), in this form:

  ```text
  matches(selector, key) = key != "default"
                           and ((key == selector)
                                or (key is a size key and key starts with selector + "-"))
  selected(no filter, sizes) = every key of sizes
  selected(selectors, sizes) = the keys of sizes, in YAML order, for which matches(s, key) is true
                               for one or more s in selectors; each key one time
  ```

  - With no filter, the CLI selects every size, also `default`. A filter never selects `default`.
    Thus the CLI selects a model with no size only when it gets no filter (user decision S2, for
    the key `default` and for this filter behaviour).
  - A code selects its bare key and each key of that code with dims: `m` selects `m`, `m-256`,
    `m-384` and `m-256x256`. A full key selects only itself: `m-256` selects `m-256`, not `m`, not
    `m-384` and not `m-256x192`.
  - A name does not select a code: `medium` does not select `m`. The comparison is exact and
    case-sensitive.
  - The prefix part applies only to a size key (proposal choice). Thus `l` does not select the
    legacy key `l-m`, and `rtmw` does not select `rtmw-l-m_256x192`.
  - The CLI decides what a selector that selects no key does. OpenMMLab-Exporter exits with code 2
    (`export_all.py:263-265, 316-318`).

### 2.4 Validation rules

- [ ] `V-common.sizes-1` **(vNEXT)** Each key of `sizes` must be a size key of the grammar: a word,
  a word with `-` and dims, dims alone, or `default`. A word must be a code of the alias table or a
  free word. An alias of the table is not a valid word. Each number of the dims must be ASCII digits
  with no leading zero.
- [ ] `V-common.sizes-2` **(vNEXT)** If a size key has a height, the height axis of
  `sizes.<key>.input.shape` must be equal to that height. If the key also has a width, the width
  axis must be equal to that width. The axes are `shape[2]` and `shape[3]` for `NCHW`, and `shape[1]`
  and `shape[2]` for `NHWC` (`input.layout`). A key that gives a dim is invalid when that axis is `-1`.
- [ ] `V-common.sizes-3` **(vNEXT)** In one sidecar, all keys of one word must have the same form:
  bare, `-<height>` or `-<height>x<width>`. All keys with no word must also have the same form:
  `<height>` or `<height>x<width>`.
- [ ] `V-common.sizes-4` **(vNEXT)** The key `default` is valid only when it is the only key of
  `sizes`.

Rule 4 is user decision S2: the user approved "a reserved key, for example `default`, valid only when
`sizes` has one key" on 2026-10-23 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). Rule 2 and rule 3 are proposal
choices. Rule 2 makes the dims of a key true: S3 and S8 say that the number is the input height and
the width (height first), but they do not ask for a check.
Rule 3 extends the earlier rule "a code is not bare and with a height in one sidecar" to the width
form of user decision S8, and it applies the "Form of a key" rule (proposal choice, 2.3) to one
sidecar. Rule 1 applies the grammar. The grammar has user-decision forms and proposal-choice forms
(2.3, "Grammar").

Existing rules that name a value of this change:

- `V-common.sizes_and_artifacts-1` to `-12`: unchanged. They do not read the key text.
- `V-common.sizes_and_artifacts-4` (the spatial dims equal `target_size`): unchanged. With it,
  `V-common.sizes-2` also fixes the dims of `target_size`.
- `V-common.identity-1` (the basename): unchanged.
- The proposed `V-common.identity-7` and `V-common.identity-8` (`specs/sidecar/proposals/model-id-suffix/proposal.md`,
  part 2.4): unchanged by this proposal. `V-common.identity-7` cannot reject a training token that
  is a size key, because every free word is a size key (user decision S1).

A note for `V-common.identity-8`. A file name is `{model_id}-{size}_{batch}_{precision}.onnx`
(`format/file-layout.md:30`). Take two sidecars of one folder with the ids `a` and
`b = a + "-" + w`, a size `ka` of `a` and a size `kb` of `b`. They name the same file when
`ka = w + "-" + kb`. A size key has one hyphen at most, so `w` is the word of `ka`, and `kb` is the
dims of `ka`. Dims alone are a valid size key (user decision S3). Thus two `vNEXT` sidecars with
valid size keys can name the same file. Example: a sidecar `rtmo-coco17` with the size `body7-256`
and a sidecar `rtmo-coco17-body7` with the size `256` both give
`rtmo-coco17-body7-256_b1_fp32.onnx`. `V-common.sizes-1` to `-4` read one sidecar, so they cannot
see this. `V-common.identity-8` is necessary for `vNEXT` keys, not only for legacy keys. Follow-up
for the model-id proposal: add a collision vector with these two valid keys.

### 2.5 Selectors

none. The section applies to every sidecar (`selectors: []`). The rules apply only at `vNEXT` (2.6).

### 2.6 Legacy behaviour and version effect

- A sidecar with `schema_version < vNEXT` keeps the old rule: a size key is a lowercase token, and it
  can contain hyphens (`common/sizes-and-artifacts.md:33`). Examples: `nano`, `default`, `yolox-tiny`,
  `rtmpose-m_256x192`, `rtmw-x-l_384x288`. `V-common.sizes-1` to `-4` do not apply. The meaning of
  a legacy sidecar does not change.
- The change goes into the `vNEXT` revision.
- The new section file has a "Legacy behaviour" heading with this table:

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|---|---|---|
| Key of `sizes` | Any lowercase token. A hyphen is allowed. No alias table. | A code or a free word, with optional dims; dims alone; or `default` (`V-common.sizes-1` to `-4`). An alias of the table is invalid: write its code. |

- Add the link to this heading to "Version-aware compatibility" (`format/versioning.md:53-63`).
- A `vNEXT` sidecar with an alias key (`nano`, `small`, `medium`, `large`, `xlarge`) is invalid
  after this change. Three writers make such sidecars at `vNEXT` today: OpenMMLab-Exporter
  `rtmdet-person` (`rtmdet_person/sidecar.py:31` at `f3aeb47`; OpenMMLab-Exporter decision 0050 writes no file until the
  intake is `describes`, and the writer stays at `vNEXT`), Roboflow-Exporter `rfdetr` (`rf_detr/sidecar.py:32`)
  and the spec examples (`examples/.../rtmdet-person.yaml:2`, `examples/.../yolo26.yaml:2`,
  `examples/.../yolo26-body.yaml:2`, key `nano` at `:86`). `vNEXT`
  is not released, so no released sidecar breaks. Part 7 gives the renames.

### 2.7 Changelog row

`schema_version` history: do not add a row. The table has one `vNEXT` row (`changelog.md:68`).
Append this sentence to the end of its cell, in its "Added ..." style:

```text
Added size keys: an alias table that joins the spellings of one size into one code (`n`, `t`, `s`, `m`, `b`, `l`, `x`, `2xl`, `h`), free words outside the table, optional input dims (`-<height>` or `-<height>x<width>`), keys of dims alone, and the reserved key `default` for one size with no name.
```

Summary of changes (the five columns of `changelog.md:16`: #, Area, Change, Driven by, Section):

```text
| N | Sizes | New alias table for the keys of `sizes`: `n` nano, `t` tiny, `s` small, `m` medium (also `med`), `b` balanced (also `base`), `l` large, `x` xlarge (also `xl`), `2xl` 2xlarge (also `xxlarge`, `xxl`), `h` huge. A key writes the code, not the alias. A word that is not in the table stays valid (`lite`, `full`). A key can add input dims (`l-256`, `m-256x256`) or be dims alone (`192`). `default` is the key of a family with one size and no name. The hyphen examples `l-m` and `x-l` are legacy keys. | one key for one size across exporters: `medium` (Ultralytics, Roboflow, RTMDet person) and `m` (RTMW, RTMO) | [Size keys](common/size-keys.md) |
```

`N` is the next free number when this proposal merges. Rows 1 to 19 exist (`changelog.md:18-36`).
13 open proposals (9 of OpenMMLab-Exporter, 4 of MediaPipe-Exporter) add a summary row, so the numbers depend on the merge order.
Do not fix `N` before the merge.

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo | the part 3 code of `specs/sidecar/proposals/size-codes/proposal.md` |
| Target file in skellytracker | `specs/sidecar/reference/common_sizes.py` |
| Functions (one for each algorithm) | `check_size_key` (`V-common.sizes-1`), `check_size_dims` (`V-common.sizes-2`), `mixed_word_forms` (`V-common.sizes-3`), `check_default_key` (`V-common.sizes-4`), `size_word`, `size_height` and `size_width` (the parts of a key), `size_name` (code to name), `alias_code` (alias to code, for the authoring guidance), `normalize_size_key` (an upstream spelling with optional dims to its size key, for the authoring guidance). Informative (user decision S8): `matches_size` and `select_sizes` (the size filter of an exporter CLI). The constants `SIZE_CODES` (code to name) and `SIZE_ALIASES` (alias to code) are the table. |

Source commit: none (no host code). This exporter has no code that checks a size key. Its CLI
selects by an exact key today (`export_all.py:255-266`). Plan step 3.6 adds the prefix rule
(the untracked pose-models plan of OpenMMLab-Exporter (plan facts)) and a check of each identity `size_key` (`:600-602`). The
functions come from the text of part 2. The file uses only the Python standard library.

```python
"""Reference implementation of the proposed section common.sizes (Size keys).

This file uses ASD-STE100 Simplified Technical English.

- Section ID: common.sizes (proposed, new; OpenMMLab-Exporter proposal size-codes,
  specs/sidecar/proposals/size-codes/proposal.md).
- User decisions (2026-10-23; the untracked pose-models plan of OpenMMLab-Exporter (plan facts) for T17 and :183-193 for S1 to S9):
  - T17: one code table for every exporter (nano > n, tiny > t, medium > m).
  - S1: the table is an alias map. It joins the spellings of one size into one code (medium, med
    and m all become m). A word that is not in the table stays valid as it is (for example lite,
    full, heavy). The table is not a closed list and not a size order.
  - S2: an exporter CLI treats a size list as a filter. The CLI selects a model with no size only
    when it gets no filter. The approved spec form (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)): the reserved
    key "default" is valid only when sizes has one key (V-common.sizes-4, check_default_key), and
    a size filter never selects it (matches_size, select_sizes).
  - S3: a size key can be a code with an input height (l-256), or an input height alone (192,
    256).
  - S4: the code 2xl, with the spellings 2xlarge and xxl. S7: the code b means balanced; base is
    an alias.
  - S5: the exporter chooses the default size (the first key). The table has no order.
  - S8: host selection is out of scope. matches_size and select_sizes are informative guidance
    for an exporter CLI. They implement no validation rule. A size key can also give the width:
    <code>-<height>x<width>, height first.
- Proposal choices (not user decisions): the form <height>x<width> with no word; the dims on a
  free word (<free_word>-<height>, <free_word>-<height>x<width>); V-common.sizes-2 (the dims agree
  with input.shape); V-common.sizes-3 (one form for each word); the aliases xl and xxlarge; the
  codes s, l, x, h and their names; the character rule of a free word; no dims on the key
  "default" (default-256 is not a size key).
- Source commit: none (no host code). The functions come from the text of part 2 of the proposal.
- Vectors: the writer of the proposal wrote the cases of part 4 by hand from the text of part 2.
  This file does not write them. Part 4 records the run of the cases against this file (191 of 191
  pass, 2026-10-23). They are unverified: no host implementation.
- Parity result: none (a size key changes no tensor and no decoded output).

skellytracker has no specs/sidecar/reference/common_sizes.py. The section is new, so this file
implements the full section. There is one function for each rule and for each step of the
behaviour:

- check_size_key: V-common.sizes-1 (vNEXT).
- check_size_dims: V-common.sizes-2 (vNEXT).
- mixed_word_forms: V-common.sizes-3 (vNEXT).
- check_default_key: V-common.sizes-4 (vNEXT).
- size_word, size_height, size_width: the parts of a size key (behaviour).
- size_name: the name of a code of the table (behaviour).
- alias_code: the code of an alias of the table (authoring guidance).
- normalize_size_key: an upstream spelling, with optional dims, written as a size key (authoring
  guidance). For example, medium gives m, and medium-256 gives m-256.
- matches_size: the size filter of an exporter CLI, for one selector and one key (informative).
- select_sizes: the size filter of an exporter CLI, for the keys of one sidecar (informative).

Each function returns False, None or an empty list for a value of the wrong type, and does not
raise. The exception is the list arguments keys and selectors of select_sizes, mixed_word_forms
and check_default_key. These functions raise TypeError when a list argument is one str, because a
str is also a sequence of str and the function would read its characters. They also raise
TypeError when a list argument is not a sequence (for example None). The one exception is
selectors=None in select_sizes, which means "no filter".

The functions do not compare schema versions. The caller applies the rules marked vNEXT only when
schema_version >= vNEXT (format.versioning). The functions do not read files. The functions use
only the Python standard library.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

# The codes of common.sizes, part 2.3, with the name of each code. The order of this table is not
# a size order.
SIZE_CODES: dict[str, str] = {
    "n": "nano",
    "t": "tiny",
    "s": "small",
    "m": "medium",
    "b": "balanced",
    "l": "large",
    "x": "xlarge",
    "2xl": "2xlarge",
    "h": "huge",
}

# The alias table of common.sizes, part 2.3: each known spelling of a size, and its code.
# A key of vNEXT must be the code, not the alias.
SIZE_ALIASES: dict[str, str] = {
    "nano": "n",
    "tiny": "t",
    "small": "s",
    "medium": "m",
    "med": "m",
    "balanced": "b",
    "base": "b",
    "large": "l",
    "xlarge": "x",
    "xl": "x",
    "2xlarge": "2xl",
    "xxlarge": "2xl",
    "xxl": "2xl",
    "huge": "h",
}

# The reserved key of a family with one size and no size name (user decision S2, V-common.sizes-4).
# It takes no dims (proposal choice).
DEFAULT_KEY = "default"

# dims: an input height, with an optional "x" and an input width. Each number is ASCII digits
# with no leading zero. The patterns use [0-9], not \d: \d also matches digits that are not ASCII.
_DIMS = r"(?P<height>[1-9][0-9]*)(?:x(?P<width>[1-9][0-9]*))?"
_DIMS_RE = re.compile(_DIMS)
# The form with a word: a token of ASCII lowercase letters and digits, with an optional "-" and dims.
_WORD_RE = re.compile(r"(?P<word>[a-z0-9]+)(?:-" + _DIMS + r")?")
# A free word (a word that is not a code) starts with an ASCII lowercase letter.
_FREE_WORD_RE = re.compile(r"[a-z][a-z0-9]*")

# The axes of the height and the width in input.shape, for each input.layout.
_DIM_AXES = {"NCHW": (2, 3), "NHWC": (1, 2)}


def _require_list(name: str, value: object) -> None:
    """Raise TypeError when value is one str, or is not a sequence, in place of a sequence of str."""
    if isinstance(value, str):
        raise TypeError(f"{name} must be a sequence of str, not one str")
    if not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of str, not {type(value).__name__}")


def _is_word(word: str) -> bool:
    """Return True when word is a code, or a free word that is not an alias and not "default"."""
    if word in SIZE_CODES:
        return True
    return (
        _FREE_WORD_RE.fullmatch(word) is not None
        and word not in SIZE_ALIASES
        and word != DEFAULT_KEY
    )


def _as_int(text: str | None) -> int | None:
    return int(text) if text is not None else None


def _parts(key: object) -> tuple[str | None, int | None, int | None] | None:
    """Return (word, height, width) of a size key, or None when key is not a size key.

    A key with no word gives (None, height, width). The key "default" gives ("default", None, None).
    """
    if not isinstance(key, str):
        return None
    if key == DEFAULT_KEY:
        return DEFAULT_KEY, None, None
    match = _DIMS_RE.fullmatch(key)
    if match is not None:
        return None, int(match.group("height")), _as_int(match.group("width"))
    match = _WORD_RE.fullmatch(key)
    if match is None or not _is_word(match.group("word")):
        return None
    return match.group("word"), _as_int(match.group("height")), _as_int(match.group("width"))


def _form(parts: tuple[str | None, int | None, int | None]) -> str:
    """Return the form of a parsed key: "bare", "height" or "height-width"."""
    if parts[1] is None:
        return "bare"
    return "height" if parts[2] is None else "height-width"


def check_size_key(key: str) -> bool:
    """V-common.sizes-1: return True when key is a size key of the grammar.

    A size key is one of: <word>, <word>-<height>, <word>-<height>x<width>, <height>,
    <height>x<width>, or the reserved key "default". A word is a code of the table, or a free word:
    ASCII lowercase letters and digits that start with a letter. An alias of the table is not a
    word: write its code. "default" is not a word. Each number has no leading zero. The match is
    exact: no case change, no strip.
    """
    return _parts(key) is not None


def size_word(key: str) -> str | None:
    """common.sizes: return the word of a size key.

    Return None for a key with no word, and when key is not a size key. The key "default" gives
    "default".
    """
    parts = _parts(key)
    return parts[0] if parts is not None else None


def size_height(key: str) -> int | None:
    """common.sizes: return the input height of a size key as an int.

    Return None when the key has no height, or when key is not a size key.
    """
    parts = _parts(key)
    return parts[1] if parts is not None else None


def size_width(key: str) -> int | None:
    """common.sizes: return the input width of a size key as an int.

    Return None when the key has no width, or when key is not a size key.
    """
    parts = _parts(key)
    return parts[2] if parts is not None else None


def size_name(code: str) -> str | None:
    """common.sizes: return the name of a code of the table, or None for another value."""
    return SIZE_CODES.get(code) if isinstance(code, str) else None


def alias_code(word: str) -> str | None:
    """common.sizes authoring guidance: return the code of an alias of the table.

    Return None when word is not an alias. A code is not an alias of itself. The match is exact.
    """
    return SIZE_ALIASES.get(word) if isinstance(word, str) else None


def normalize_size_key(name: str) -> str | None:
    """common.sizes authoring guidance: return the size key for an upstream name.

    The name has the form of a size key, but its word can be an alias. An alias becomes its code
    (medium gives m, medium-256 gives m-256, medium-256x192 gives m-256x192). A code, a free word,
    dims and "default" stay as they are. Return None when the result is not a size key (for example
    Medium, l-m or default-256). The function does not change the case and does not strip.
    """
    if not isinstance(name, str):
        return None
    match = _WORD_RE.fullmatch(name)
    if match is not None and match.group("word") in SIZE_ALIASES:
        name = SIZE_ALIASES[match.group("word")] + name[len(match.group("word")):]
    return name if check_size_key(name) else None


def check_size_dims(key: str, input_shape: Sequence[int], layout: str = "NCHW") -> bool:
    """V-common.sizes-2: return True when the dims of key agree with input.shape of the size.

    A key with no dims passes. A key with a height passes only when the height axis of input_shape
    is that height. A key with a width also needs the width axis to be that width. The axes are
    shape[2] and shape[3] for NCHW, and shape[1] and shape[2] for NHWC. NCHW is the default of
    input.layout. A dynamic dim (-1) fails when the key gives that dim. A key that is not a size key
    fails. An input_shape that is not a sequence fails.
    """
    parts = _parts(key)
    if parts is None:
        return False
    _, height, width = parts
    if height is None:
        return True
    axes = _DIM_AXES.get(layout) if isinstance(layout, str) else None
    if axes is None or not isinstance(input_shape, Sequence) or isinstance(input_shape, str):
        return False
    for axis, value in zip(axes, (height, width)):
        if value is None:
            continue
        if len(input_shape) <= axis:
            return False
        dim = input_shape[axis]
        if type(dim) is not int or dim != value:
            return False
    return True


def mixed_word_forms(keys: Sequence[str]) -> list[str | None]:
    """V-common.sizes-3: return each word whose keys have more than one form.

    The forms are bare (<word>), with a height (<word>-<height>) and with a height and a width
    (<word>-<height>x<width>). The keys with no word are one more group, reported as None. Their
    forms are <height> and <height>x<width>. The sidecar passes the rule when the list is empty.
    The list is in the order of the first key of each group in keys. The function ignores the key
    "default" and a key that is not a size key (V-common.sizes-1 reports it). Raise TypeError when
    keys is one str or is not a sequence.
    """
    _require_list("keys", keys)
    forms: dict[str | None, set[str]] = {}
    for key in keys:
        parts = _parts(key)
        if parts is None or parts[0] == DEFAULT_KEY:
            continue
        forms.setdefault(parts[0], set()).add(_form(parts))
    return [word for word, found in forms.items() if len(found) > 1]


def check_default_key(keys: Sequence[str]) -> bool:
    """V-common.sizes-4: return True when the key "default" is absent, or is the only key.

    Raise TypeError when keys is one str or is not a sequence.
    """
    _require_list("keys", keys)
    keys = list(keys)
    return DEFAULT_KEY not in keys or keys == [DEFAULT_KEY]


def matches_size(selector: str, key: str) -> bool:
    """common.sizes, informative: return True when the size filter selector selects key.

    This is guidance for an exporter CLI, not a rule for hosts. A selector selects the key that is
    equal to it. A selector also selects each size key whose text starts with the selector and a
    hyphen ("l" selects "l-256", "l-384" and "l-256x192"). The prefix part applies only when key is
    a size key (V-common.sizes-1). Thus a selector selects a legacy key only when the two strings
    are equal. No selector selects the key "default". The comparison is exact and case-sensitive.
    A selector or a key that is not a str selects nothing.
    """
    if not isinstance(selector, str) or not isinstance(key, str):
        return False
    if key == DEFAULT_KEY:
        return False
    if selector == key:
        return True
    return check_size_key(key) and key.startswith(selector + "-")


def select_sizes(selectors: Sequence[str] | None, keys: Sequence[str]) -> list[str]:
    """common.sizes, informative: return the keys that a size filter selects.

    This is guidance for an exporter CLI, not a rule for hosts. selectors None means "no filter":
    the result is every key, also "default". With a filter, the result is each key that one or
    more selectors select (matches_size). An empty filter selects no key. The result keeps the
    order of keys (the YAML order of sizes) and has each key one time. A selector that selects no
    key of this sidecar is not an error here. The CLI decides what a selector with no match in all
    selected sidecars does. Raise TypeError when selectors or keys is one str or is not a sequence
    (selectors None is allowed).
    """
    if selectors is not None:
        _require_list("selectors", selectors)
    _require_list("keys", keys)
    result: list[str] = []
    for key in keys:
        if key in result:
            continue
        if selectors is None or any(matches_size(selector, key) for selector in selectors):
            result.append(key)
    return result
```

## 4. Vectors

The writer of this proposal wrote the cases by hand from the text of part 2. Then the writer ran them
against the reference file. The reference file does not write them. The block uses the form of the template
(`function` in each case, `generated_by: <reference file>`, `templates/change-proposal.md:242,
251, 256`). At landing, the skellytracker session moves the cases into `tools/make_vectors.py` (part
2.1), and `generated_by` becomes `tools/make_vectors.py`. The cases of `matches_size` and
`select_sizes` test informative guidance (user decision S8). The skellytracker session can keep them
with the guidance or leave them out.

Run of 2026-10-23 (after the user decisions S1 to S9, again after the review fixes of the same day,
and again after the S2 label update of the same day, with a new scratch runner): all 191 cases below
pass against
the part 3 code of `specs/sidecar/proposals/size-codes/proposal.md` (`check_size_key` 65, `size_word` 7, `size_height` 6,
`size_width` 3, `size_name` 5, `alias_code` 14, `normalize_size_key` 11, `check_size_dims` 19,
`mixed_word_forms` 13, `check_default_key` 4, `matches_size` 26, `select_sizes` 18). The runner
reads the YAML block of this part with PyYAML, loads the reference file with
`importlib.util.spec_from_file_location`, calls `function(**input, **params)` and requires the result
to be equal to the one value of `expect`, with the same Python type. Command:
`uv run --project <exporter repo> python -I -B run_size_vectors.py <this file> <reference file>`
(scratch script, not committed). Output: `191/191 pass`. Run again on 2026-10-25 with a new scratch
runner of the same method: `191/191 pass`. Control runs with changed copies of the
reference file (each control must fail one or more cases):

- The number pattern `[0-9]+` in place of `[1-9][0-9]*` fails 5 cases (`key-leading-zero`,
  `key-height-zero`, `key-height-only-leading-zero`, `key-width-leading-zero`,
  `height-leading-zero`).
- An alias accepted as a word (no S1 check) fails 16 cases: 14 of the 15 `key-alias-*` cases,
  `word-of-alias` and `dims-invalid-key`. The case `key-alias-2xlarge` still passes, because the
  digit-first rule of a free word also rejects `2xlarge`.
- A free word that can start with a digit fails 2 cases (`key-height-only-leading-zero`,
  `key-word-starts-with-digit`).
- No check of the width fails 2 cases (`dims-width-other`, `dims-dynamic-width`).
- `mixed_word_forms` that returns the words in sorted order fails 1 case (`forms-order-of-first-key`).
- `matches_size` with no check of the types fails 3 cases (`match-int-equal` gives true;
  `match-null-selector` and `select-null-selector` raise `TypeError`).
- A filter that can select `default` fails 2 cases (`match-default-never`,
  `select-filter-default-word`).

The same run checks one behaviour that a case cannot show, because `expect` holds a value and not an
error: `select_sizes`, `mixed_word_forms` and `check_default_key` raise `TypeError` when a list
argument is one `str` (4 of 4 calls), or is not a sequence, for example `None` (3 of 3 calls:
`mixed_word_forms(None)`, `check_default_key(None)`, `select_sizes(["m"], None)`). Without the str
check, the function reads the selector `"m-256"` as the characters `m`, `-`, `2`, `5`, `6`, and `m`
selects `m` and `m-384` in silence.

```yaml
section: common.sizes
spec_revision: vNEXT
generated_by: the part 3 code of `specs/sidecar/proposals/size-codes/proposal.md`
unverified: no host implementation in an exporter or in skellytracker
# Each input key is an argument of the function. expect has one key: the result of the function.
# null is Python None. The strings are exact: the runner does not strip them. The keys "n" and the
# keys of dims alone have quotes, so that each YAML parser reads them as strings.
cases:
  # V-common.sizes-1: each code of the table
  - {id: key-code-n, function: check_size_key, params: {}, input: {key: "n"}, expect: {valid: true}}
  - {id: key-code-t, function: check_size_key, params: {}, input: {key: t}, expect: {valid: true}}
  - {id: key-code-s, function: check_size_key, params: {}, input: {key: s}, expect: {valid: true}}
  - {id: key-code-m, function: check_size_key, params: {}, input: {key: m}, expect: {valid: true}}
  - {id: key-code-b, function: check_size_key, params: {}, input: {key: b}, expect: {valid: true}}
  - {id: key-code-l, function: check_size_key, params: {}, input: {key: l}, expect: {valid: true}}
  - {id: key-code-x, function: check_size_key, params: {}, input: {key: x}, expect: {valid: true}}
  - {id: key-code-2xl, function: check_size_key, params: {}, input: {key: "2xl"}, expect: {valid: true}}
  - {id: key-code-h, function: check_size_key, params: {}, input: {key: h}, expect: {valid: true}}
  # V-common.sizes-1: free words (S1)
  - {id: key-free-lite, function: check_size_key, params: {}, input: {key: lite}, expect: {valid: true}}
  - {id: key-free-full, function: check_size_key, params: {}, input: {key: full}, expect: {valid: true}}
  - {id: key-free-heavy, function: check_size_key, params: {}, input: {key: heavy}, expect: {valid: true}}
  - {id: key-free-with-digit, function: check_size_key, params: {}, input: {key: body7}, expect: {valid: true}}
  - {id: key-free-letter-c, function: check_size_key, params: {}, input: {key: c}, expect: {valid: true}}
  # V-common.sizes-1: a word and a height (a code: S3; a free word: proposal choice)
  - {id: key-height-l-256, function: check_size_key, params: {}, input: {key: l-256}, expect: {valid: true}}
  - {id: key-height-x-384, function: check_size_key, params: {}, input: {key: x-384}, expect: {valid: true}}
  - {id: key-height-one-digit, function: check_size_key, params: {}, input: {key: s-1}, expect: {valid: true}}
  - {id: key-height-2xl, function: check_size_key, params: {}, input: {key: 2xl-640}, expect: {valid: true}}
  - {id: key-height-free-word, function: check_size_key, params: {}, input: {key: lite-256}, expect: {valid: true}}
  # V-common.sizes-1: a word, a height and a width (S8)
  - {id: key-dims-m-256x256, function: check_size_key, params: {}, input: {key: m-256x256}, expect: {valid: true}}
  - {id: key-dims-l-384x288, function: check_size_key, params: {}, input: {key: l-384x288}, expect: {valid: true}}
  # V-common.sizes-1: dims alone (S3, and the proposal choice <height>x<width>)
  - {id: key-height-only-192, function: check_size_key, params: {}, input: {key: "192"}, expect: {valid: true}}
  - {id: key-height-only-256, function: check_size_key, params: {}, input: {key: "256"}, expect: {valid: true}}
  - {id: key-dims-only, function: check_size_key, params: {}, input: {key: 256x192}, expect: {valid: true}}
  # V-common.sizes-1: the reserved key (user decision S2; no dims on it: proposal choice)
  - {id: key-default, function: check_size_key, params: {}, input: {key: default}, expect: {valid: true}}
  - {id: key-default-with-height, function: check_size_key, params: {}, input: {key: default-256}, expect: {valid: false}}
  # V-common.sizes-1: an alias is not a word (S1: write the code)
  - {id: key-alias-nano, function: check_size_key, params: {}, input: {key: nano}, expect: {valid: false}}
  - {id: key-alias-tiny, function: check_size_key, params: {}, input: {key: tiny}, expect: {valid: false}}
  - {id: key-alias-small, function: check_size_key, params: {}, input: {key: small}, expect: {valid: false}}
  - {id: key-alias-medium, function: check_size_key, params: {}, input: {key: medium}, expect: {valid: false}}
  - {id: key-alias-med, function: check_size_key, params: {}, input: {key: med}, expect: {valid: false}}
  - {id: key-alias-balanced, function: check_size_key, params: {}, input: {key: balanced}, expect: {valid: false}}
  - {id: key-alias-base, function: check_size_key, params: {}, input: {key: base}, expect: {valid: false}}
  - {id: key-alias-large, function: check_size_key, params: {}, input: {key: large}, expect: {valid: false}}
  - {id: key-alias-xlarge, function: check_size_key, params: {}, input: {key: xlarge}, expect: {valid: false}}
  - {id: key-alias-xl, function: check_size_key, params: {}, input: {key: xl}, expect: {valid: false}}
  - {id: key-alias-2xlarge, function: check_size_key, params: {}, input: {key: 2xlarge}, expect: {valid: false}}
  - {id: key-alias-xxlarge, function: check_size_key, params: {}, input: {key: xxlarge}, expect: {valid: false}}
  - {id: key-alias-xxl, function: check_size_key, params: {}, input: {key: xxl}, expect: {valid: false}}
  - {id: key-alias-huge, function: check_size_key, params: {}, input: {key: huge}, expect: {valid: false}}
  - {id: key-alias-with-height, function: check_size_key, params: {}, input: {key: medium-256}, expect: {valid: false}}
  # V-common.sizes-1: invalid forms
  - {id: key-uppercase, function: check_size_key, params: {}, input: {key: M}, expect: {valid: false}}
  - {id: key-uppercase-free-word, function: check_size_key, params: {}, input: {key: Lite}, expect: {valid: false}}
  - {id: key-underscore, function: check_size_key, params: {}, input: {key: m_256}, expect: {valid: false}}
  - {id: key-empty, function: check_size_key, params: {}, input: {key: ""}, expect: {valid: false}}
  - {id: key-leading-zero, function: check_size_key, params: {}, input: {key: m-0256}, expect: {valid: false}}
  - {id: key-height-zero, function: check_size_key, params: {}, input: {key: m-0}, expect: {valid: false}}
  - {id: key-height-only-leading-zero, function: check_size_key, params: {}, input: {key: "0192"}, expect: {valid: false}}
  - {id: key-width-leading-zero, function: check_size_key, params: {}, input: {key: m-256x0192}, expect: {valid: false}}
  - {id: key-two-heights, function: check_size_key, params: {}, input: {key: l-256-192}, expect: {valid: false}}
  - {id: key-trailing-x, function: check_size_key, params: {}, input: {key: l-256x}, expect: {valid: false}}
  - {id: key-trailing-hyphen, function: check_size_key, params: {}, input: {key: l-}, expect: {valid: false}}
  - {id: key-no-word, function: check_size_key, params: {}, input: {key: "-256"}, expect: {valid: false}}
  - {id: key-word-starts-with-digit, function: check_size_key, params: {}, input: {key: 7body}, expect: {valid: false}}
  - {id: key-legacy-pair-l-m, function: check_size_key, params: {}, input: {key: l-m}, expect: {valid: false}}
  - {id: key-legacy-package, function: check_size_key, params: {}, input: {key: rtmpose-m_256x192}, expect: {valid: false}}
  - {id: key-legacy-yolox, function: check_size_key, params: {}, input: {key: yolox-tiny}, expect: {valid: false}}
  - {id: key-m-l, function: check_size_key, params: {}, input: {key: m-l}, expect: {valid: false}}
  - {id: key-training-like, function: check_size_key, params: {}, input: {key: body7-m}, expect: {valid: false}}
  - {id: key-trailing-newline, function: check_size_key, params: {}, input: {key: "m\n"}, expect: {valid: false}}
  - {id: key-leading-space, function: check_size_key, params: {}, input: {key: " m"}, expect: {valid: false}}
  - {id: key-non-ascii-digits, function: check_size_key, params: {}, input: {key: "m-\u0662\u0665\u0666"}, expect: {valid: false}}
  - {id: key-non-ascii-letter, function: check_size_key, params: {}, input: {key: "lit\u00e9"}, expect: {valid: false}}
  - {id: key-yaml-integer, function: check_size_key, params: {}, input: {key: 192}, expect: {valid: false}}
  - {id: key-null, function: check_size_key, params: {}, input: {key: null}, expect: {valid: false}}
  # the parts of a key
  - {id: word-of-height-key, function: size_word, params: {}, input: {key: l-256}, expect: {word: l}}
  - {id: word-of-bare-key, function: size_word, params: {}, input: {key: m}, expect: {word: m}}
  - {id: word-of-free-word-key, function: size_word, params: {}, input: {key: lite-256}, expect: {word: lite}}
  - {id: word-of-dims-key, function: size_word, params: {}, input: {key: m-256x192}, expect: {word: m}}
  - {id: word-of-height-only, function: size_word, params: {}, input: {key: "192"}, expect: {word: null}}
  - {id: word-of-default, function: size_word, params: {}, input: {key: default}, expect: {word: default}}
  - {id: word-of-alias, function: size_word, params: {}, input: {key: medium}, expect: {word: null}}
  - {id: height-of-height-key, function: size_height, params: {}, input: {key: l-256}, expect: {height: 256}}
  - {id: height-of-bare-key, function: size_height, params: {}, input: {key: m}, expect: {height: null}}
  - {id: height-of-height-only, function: size_height, params: {}, input: {key: "192"}, expect: {height: 192}}
  - {id: height-of-dims-key, function: size_height, params: {}, input: {key: m-256x192}, expect: {height: 256}}
  - {id: height-leading-zero, function: size_height, params: {}, input: {key: m-0256}, expect: {height: null}}
  - {id: height-of-legacy-pair, function: size_height, params: {}, input: {key: x-l}, expect: {height: null}}
  - {id: width-of-dims-key, function: size_width, params: {}, input: {key: m-256x192}, expect: {width: 192}}
  - {id: width-of-height-key, function: size_width, params: {}, input: {key: l-256}, expect: {width: null}}
  - {id: width-of-dims-only, function: size_width, params: {}, input: {key: 256x192}, expect: {width: 192}}
  # the table: code to name
  - {id: name-of-x, function: size_name, params: {}, input: {code: x}, expect: {name: xlarge}}
  - {id: name-of-b, function: size_name, params: {}, input: {code: b}, expect: {name: balanced}}
  - {id: name-of-2xl, function: size_name, params: {}, input: {code: "2xl"}, expect: {name: 2xlarge}}
  - {id: name-of-unknown, function: size_name, params: {}, input: {code: q}, expect: {name: null}}
  - {id: name-of-alias, function: size_name, params: {}, input: {code: medium}, expect: {name: null}}
  # the table: alias to code
  - {id: alias-nano, function: alias_code, params: {}, input: {word: nano}, expect: {code: "n"}}
  - {id: alias-tiny, function: alias_code, params: {}, input: {word: tiny}, expect: {code: t}}
  - {id: alias-medium, function: alias_code, params: {}, input: {word: medium}, expect: {code: m}}
  - {id: alias-med, function: alias_code, params: {}, input: {word: med}, expect: {code: m}}
  - {id: alias-base, function: alias_code, params: {}, input: {word: base}, expect: {code: b}}
  - {id: alias-balanced, function: alias_code, params: {}, input: {word: balanced}, expect: {code: b}}
  - {id: alias-xl, function: alias_code, params: {}, input: {word: xl}, expect: {code: x}}
  - {id: alias-xxl, function: alias_code, params: {}, input: {word: xxl}, expect: {code: "2xl"}}
  - {id: alias-xxlarge, function: alias_code, params: {}, input: {word: xxlarge}, expect: {code: "2xl"}}
  - {id: alias-2xlarge, function: alias_code, params: {}, input: {word: 2xlarge}, expect: {code: "2xl"}}
  - {id: alias-code-is-not-alias, function: alias_code, params: {}, input: {word: m}, expect: {code: null}}
  - {id: alias-free-word, function: alias_code, params: {}, input: {word: lite}, expect: {code: null}}
  - {id: alias-capital, function: alias_code, params: {}, input: {word: Medium}, expect: {code: null}}
  - {id: alias-extra-large, function: alias_code, params: {}, input: {word: extra-large}, expect: {code: null}}
  # authoring guidance: an upstream spelling to its size key
  - {id: normalize-medium, function: normalize_size_key, params: {}, input: {name: medium}, expect: {key: m}}
  - {id: normalize-medium-height, function: normalize_size_key, params: {}, input: {name: medium-256}, expect: {key: m-256}}
  - {id: normalize-base-dims, function: normalize_size_key, params: {}, input: {name: base-256x192}, expect: {key: b-256x192}}
  - {id: normalize-xxl-height, function: normalize_size_key, params: {}, input: {name: xxl-640}, expect: {key: 2xl-640}}
  - {id: normalize-code, function: normalize_size_key, params: {}, input: {name: m}, expect: {key: m}}
  - {id: normalize-free-word, function: normalize_size_key, params: {}, input: {name: lite}, expect: {key: lite}}
  - {id: normalize-height-only, function: normalize_size_key, params: {}, input: {name: "192"}, expect: {key: "192"}}
  - {id: normalize-default, function: normalize_size_key, params: {}, input: {name: default}, expect: {key: default}}
  - {id: normalize-capital, function: normalize_size_key, params: {}, input: {name: Medium}, expect: {key: null}}
  - {id: normalize-legacy-pair, function: normalize_size_key, params: {}, input: {name: l-m}, expect: {key: null}}
  - {id: normalize-default-height, function: normalize_size_key, params: {}, input: {name: default-256}, expect: {key: null}}
  # V-common.sizes-2
  - {id: dims-bare-key, function: check_size_dims, params: {layout: NCHW}, input: {key: m, input_shape: [-1, 3, 256, 192]}, expect: {valid: true}}
  - {id: dims-height-equal-nchw, function: check_size_dims, params: {layout: NCHW}, input: {key: l-256, input_shape: [-1, 3, 256, 192]}, expect: {valid: true}}
  - {id: dims-height-other, function: check_size_dims, params: {layout: NCHW}, input: {key: l-384, input_shape: [-1, 3, 256, 192]}, expect: {valid: false}}
  - {id: dims-height-is-width, function: check_size_dims, params: {layout: NCHW}, input: {key: m-192, input_shape: [-1, 3, 256, 192]}, expect: {valid: false}}
  - {id: dims-height-equal-nhwc, function: check_size_dims, params: {layout: NHWC}, input: {key: l-384, input_shape: [-1, 384, 288, 3]}, expect: {valid: true}}
  - {id: dims-nhwc-reads-axis-1, function: check_size_dims, params: {layout: NHWC}, input: {key: l-384, input_shape: [-1, 3, 384, 288]}, expect: {valid: false}}
  - {id: dims-default-layout, function: check_size_dims, params: {}, input: {key: x-384, input_shape: [-1, 3, 384, 288]}, expect: {valid: true}}
  - {id: dims-dynamic-height, function: check_size_dims, params: {layout: NCHW}, input: {key: l-256, input_shape: [-1, 3, -1, -1]}, expect: {valid: false}}
  - {id: dims-dynamic-bare-key, function: check_size_dims, params: {layout: NCHW}, input: {key: m, input_shape: [-1, 3, -1, -1]}, expect: {valid: true}}
  - {id: dims-width-equal-nchw, function: check_size_dims, params: {layout: NCHW}, input: {key: m-256x192, input_shape: [-1, 3, 256, 192]}, expect: {valid: true}}
  - {id: dims-width-other, function: check_size_dims, params: {layout: NCHW}, input: {key: m-256x256, input_shape: [-1, 3, 256, 192]}, expect: {valid: false}}
  - {id: dims-width-equal-nhwc, function: check_size_dims, params: {layout: NHWC}, input: {key: m-256x192, input_shape: [-1, 256, 192, 3]}, expect: {valid: true}}
  - {id: dims-dynamic-width, function: check_size_dims, params: {layout: NCHW}, input: {key: m-256x192, input_shape: [-1, 3, 256, -1]}, expect: {valid: false}}
  - {id: dims-height-only-nhwc, function: check_size_dims, params: {layout: NHWC}, input: {key: "192", input_shape: [-1, 192, 192, 3]}, expect: {valid: true}}
  - {id: dims-only-nchw, function: check_size_dims, params: {layout: NCHW}, input: {key: 256x192, input_shape: [-1, 3, 256, 192]}, expect: {valid: true}}
  - {id: dims-default-key, function: check_size_dims, params: {layout: NCHW}, input: {key: default, input_shape: [-1, 3, 128, 128]}, expect: {valid: true}}
  - {id: dims-invalid-key, function: check_size_dims, params: {layout: NCHW}, input: {key: medium, input_shape: [-1, 3, 640, 640]}, expect: {valid: false}}
  - {id: dims-unknown-layout, function: check_size_dims, params: {layout: CHW}, input: {key: l-256, input_shape: [3, 256, 192]}, expect: {valid: false}}
  - {id: dims-no-shape, function: check_size_dims, params: {layout: NCHW}, input: {key: l-256, input_shape: null}, expect: {valid: false}}
  # V-common.sizes-3 (None stands for the keys with no word)
  - {id: forms-rtmw, function: mixed_word_forms, params: {}, input: {keys: [l-256, l-384, m, x-256, x-384]}, expect: {words: []}}
  - {id: forms-halpe26, function: mixed_word_forms, params: {}, input: {keys: [t, s, m-256, l-256, m-384, l-384, x]}, expect: {words: []}}
  - {id: forms-free-words, function: mixed_word_forms, params: {}, input: {keys: [lite, full, heavy]}, expect: {words: []}}
  - {id: forms-bare-and-height, function: mixed_word_forms, params: {}, input: {keys: [l, l-384]}, expect: {words: [l]}}
  - {id: forms-height-and-dims, function: mixed_word_forms, params: {}, input: {keys: [m-256, m-256x256]}, expect: {words: [m]}}
  - {id: forms-all-dims, function: mixed_word_forms, params: {}, input: {keys: [m-256x192, m-256x256, m-384x288]}, expect: {words: []}}
  - {id: forms-two-words-mixed, function: mixed_word_forms, params: {}, input: {keys: [m-256, x, m, x-384, s]}, expect: {words: [m, x]}}
  - {id: forms-order-of-first-key, function: mixed_word_forms, params: {}, input: {keys: [x-384, m, x, m-256]}, expect: {words: [x, m]}}
  - {id: forms-partial-run, function: mixed_word_forms, params: {}, input: {keys: [l-256]}, expect: {words: []}}
  - {id: forms-ignore-invalid-key, function: mixed_word_forms, params: {}, input: {keys: [medium, m-256]}, expect: {words: []}}
  - {id: forms-no-word-same, function: mixed_word_forms, params: {}, input: {keys: ["192", "256"]}, expect: {words: []}}
  - {id: forms-no-word-mixed, function: mixed_word_forms, params: {}, input: {keys: ["256", 256x192]}, expect: {words: [null]}}
  - {id: forms-ignore-default, function: mixed_word_forms, params: {}, input: {keys: [default]}, expect: {words: []}}
  # V-common.sizes-4 (user decision S2)
  - {id: default-only, function: check_default_key, params: {}, input: {keys: [default]}, expect: {valid: true}}
  - {id: default-with-other, function: check_default_key, params: {}, input: {keys: [default, m]}, expect: {valid: false}}
  - {id: default-absent, function: check_default_key, params: {}, input: {keys: [m, "n"]}, expect: {valid: true}}
  - {id: default-empty, function: check_default_key, params: {}, input: {keys: []}, expect: {valid: true}}
  # informative (S8): the size filter of an exporter CLI, one selector and one key (T16)
  - {id: match-equal, function: matches_size, params: {}, input: {selector: m, key: m}, expect: {matches: true}}
  - {id: match-code-selects-height-256, function: matches_size, params: {}, input: {selector: m, key: m-256}, expect: {matches: true}}
  - {id: match-code-selects-height-384, function: matches_size, params: {}, input: {selector: m, key: m-384}, expect: {matches: true}}
  - {id: match-code-selects-dims, function: matches_size, params: {}, input: {selector: m, key: m-256x192}, expect: {matches: true}}
  # a free word with a height is a proposal choice (2.3, "Grammar")
  - {id: match-free-word-selects-height, function: matches_size, params: {}, input: {selector: lite, key: lite-256}, expect: {matches: true}}
  - {id: match-code-not-name, function: matches_size, params: {}, input: {selector: m, key: medium}, expect: {matches: false}}
  - {id: match-name-not-code, function: matches_size, params: {}, input: {selector: medium, key: m}, expect: {matches: false}}
  - {id: match-full-key, function: matches_size, params: {}, input: {selector: m-256, key: m-256}, expect: {matches: true}}
  - {id: match-full-key-not-bare, function: matches_size, params: {}, input: {selector: m-256, key: m}, expect: {matches: false}}
  - {id: match-full-key-not-other-height, function: matches_size, params: {}, input: {selector: m-256, key: m-384}, expect: {matches: false}}
  - {id: match-height-not-dims, function: matches_size, params: {}, input: {selector: m-256, key: m-256x192}, expect: {matches: false}}
  - {id: match-part-of-height, function: matches_size, params: {}, input: {selector: l-2, key: l-256}, expect: {matches: false}}
  - {id: match-selector-with-hyphen, function: matches_size, params: {}, input: {selector: l-, key: l-256}, expect: {matches: false}}
  - {id: match-empty-selector, function: matches_size, params: {}, input: {selector: "", key: m}, expect: {matches: false}}
  - {id: match-uppercase-selector, function: matches_size, params: {}, input: {selector: M, key: m}, expect: {matches: false}}
  - {id: match-other-code, function: matches_size, params: {}, input: {selector: l, key: m-256}, expect: {matches: false}}
  - {id: match-height-only, function: matches_size, params: {}, input: {selector: "192", key: "192"}, expect: {matches: true}}
  - {id: match-height-only-not-dims, function: matches_size, params: {}, input: {selector: "256", key: 256x192}, expect: {matches: false}}
  - {id: match-default-never, function: matches_size, params: {}, input: {selector: default, key: default}, expect: {matches: false}}
  - {id: match-legacy-pair-l, function: matches_size, params: {}, input: {selector: l, key: l-m}, expect: {matches: false}}
  - {id: match-legacy-pair-x, function: matches_size, params: {}, input: {selector: x, key: x-l}, expect: {matches: false}}
  - {id: match-legacy-equal, function: matches_size, params: {}, input: {selector: l-m, key: l-m}, expect: {matches: true}}
  - {id: match-legacy-package-prefix, function: matches_size, params: {}, input: {selector: rtmw, key: rtmw-l-m_256x192}, expect: {matches: false}}
  - {id: match-null-selector, function: matches_size, params: {}, input: {selector: null, key: m}, expect: {matches: false}}
  - {id: match-null-key, function: matches_size, params: {}, input: {selector: m, key: null}, expect: {matches: false}}
  - {id: match-int-equal, function: matches_size, params: {}, input: {selector: 1, key: 1}, expect: {matches: false}}
  # informative (S8): the size filter over the keys of one sidecar (T16, S2)
  - {id: select-m-halpe26, function: select_sizes, params: {}, input: {selectors: [m], keys: [t, s, m-256, l-256, m-384, l-384, x]}, expect: {selected: [m-256, m-384]}}
  - {id: select-m-legacy-rtmdet-person, function: select_sizes, params: {}, input: {selectors: [m], keys: [medium, nano]}, expect: {selected: []}}
  - {id: select-m-renamed-rtmdet-person, function: select_sizes, params: {}, input: {selectors: [m], keys: [m, "n"]}, expect: {selected: [m]}}
  - {id: select-l-rtmw-yaml-order, function: select_sizes, params: {}, input: {selectors: [l], keys: [l-256, l-384, m, x-256, x-384]}, expect: {selected: [l-256, l-384]}}
  - {id: select-b-vitpose, function: select_sizes, params: {}, input: {selectors: [b], keys: [s, b, l]}, expect: {selected: [b]}}
  - {id: select-free-word, function: select_sizes, params: {}, input: {selectors: [full], keys: [lite, full, heavy]}, expect: {selected: [full]}}
  - {id: select-height-only, function: select_sizes, params: {}, input: {selectors: ["192"], keys: ["192", "256"]}, expect: {selected: ["192"]}}
  - {id: select-dims-by-code, function: select_sizes, params: {}, input: {selectors: [m], keys: [m-256x192, m-256x256, l]}, expect: {selected: [m-256x192, m-256x256]}}
  - {id: select-overlap-no-repeat, function: select_sizes, params: {}, input: {selectors: [m-384, m], keys: [m-256, m-384]}, expect: {selected: [m-256, m-384]}}
  - {id: select-repeated-key, function: select_sizes, params: {}, input: {selectors: [m], keys: [m, m]}, expect: {selected: [m]}}
  - {id: select-x-legacy-package-rtmw, function: select_sizes, params: {}, input: {selectors: [x], keys: [rtmw-l-m_256x192, rtmw-x-l_256x192, rtmw-x-l_384x288]}, expect: {selected: []}}
  - {id: select-null-selector, function: select_sizes, params: {}, input: {selectors: [null], keys: [m]}, expect: {selected: []}}
  - {id: select-empty-filter, function: select_sizes, params: {}, input: {selectors: [], keys: [m, "n"]}, expect: {selected: []}}
  - {id: select-no-filter, function: select_sizes, params: {}, input: {selectors: null, keys: [m, "n"]}, expect: {selected: [m, "n"]}}
  - {id: select-no-filter-default, function: select_sizes, params: {}, input: {selectors: null, keys: [default]}, expect: {selected: [default]}}
  - {id: select-filter-skips-default, function: select_sizes, params: {}, input: {selectors: [m], keys: [default]}, expect: {selected: []}}
  - {id: select-filter-default-word, function: select_sizes, params: {}, input: {selectors: [default], keys: [default]}, expect: {selected: []}}
  - {id: select-no-filter-legacy, function: select_sizes, params: {}, input: {selectors: null, keys: [rtmw-l-m_256x192]}, expect: {selected: [rtmw-l-m_256x192]}}
```

The case `key-m-l` is the size of the model-id vector `artifacts-size-like-training-collision`, and
the case `key-training-like` is the size of the model-id vector
`artifacts-training-like-size-collision` (Header). The cases `key-free-with-digit` and
`key-height-only-192` show that the keys `body7-256` and `256` of the collision in 2.4 are valid.
The cases `match-legacy-pair-l` and `match-legacy-pair-x` show the defect of the old examples: under
a prefix rule with free keys, `l` would select the RTMW M model (`l-m`). The cases `forms-partial-run`
and `select-m-renamed-rtmdet-person` show the partial-run rule and the rename of part 7. The cases
`select-no-filter-default` and `select-filter-skips-default` show user decision S2.

## 5. Parity evidence

none. A size key changes no tensor, no preprocessing and no decoded output. The rules check text and
the input shape that the sidecar already declares. Thus no model run can show a difference.

| Item | Value |
|---|---|
| Gates, set before the run, and their source | n/a (no tensor changes) |
| Test images, and the branch that each image runs | n/a |
| Upstream reference | n/a |
| Export error | n/a |
| Preprocessed input | n/a |
| Row count for each image | n/a |
| Final outputs in source-image coordinates | n/a |
| Result | n/a: no model output depends on the key. An exporter check applies instead: plan step 3.6 adds a test that checks each identity `size_key` of this exporter against the table (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). |
| Script path in the exporter repo | n/a. The planned test is in `tests/` (step 3.6). It does not exist yet. |
| Exporter commit of the script | n/a |
| Command | n/a (planned: `uv run pytest`) |

A scratch check (not committed, so not evidence) ran the four rules on the local sidecars of this
exporter (`exports/`, not in git; the sidecars of the full `--force` run of 2026-10-21), in the same
run as part 4. Result: `rtmdet-person.yaml` (keys `medium`, `nano`) fails `V-common.sizes-1` for both
keys; `normalize_size_key` gives `m` and `n`. `rtmw-wholebody.yaml` (keys `l-256`, `l-384`, `m`,
`x-256`, `x-384`) and `rtmo-body7.yaml` (keys `l`, `m`, `s`, `t`) pass all four rules.

## 6. skellytracker implementation proposal

The selection of sizes by a host is out of scope (user decision S8). This part gives only the
validation of the key form.

| Item | Value |
|---|---|
| Module and function | A new module `skellytracker/core/sidecar/sizes.py` with `SIZE_CODES`, `SIZE_ALIASES` and the check functions of part 3 (`check_size_key`, `check_size_dims`, `mixed_word_forms`, `check_default_key`). The informative filter functions are not package code. |
| Dispatch point | none. No decode and no host selection uses the key form. `sidecar_model_spec(size=...)` (`skellytracker/core/sidecar/runtime.py:30-56`) takes one exact key. It does not change. |
| Validator changes (`model.py`, with rule IDs) | `sizes` is `dict[str, dict[str, Any]]` (`skellytracker/core/sidecar/model.py:474`). `SidecarModel._check_sizes` checks only a non-empty map (`model.py:497-500`). Add `V-common.sizes-1` to `-4` there, only when `schema_version >= vNEXT`. `V-common.sizes-2` reads `self.input.layout` and `self.sizes[key]["input"]["shape"]`. For the implementer: `model.py` has no comparison with `vNEXT` today. The only `schema_version` checks are the pattern and the stable version (`model.py:477-486`). The unused `_MODEL_ID_RE` (`model.py:29`) is not related. |
| Tests | The normative vectors of part 4 (`specs/sidecar/vectors/common.sizes.yaml`). A test that a `vNEXT` synthetic sidecar with the key `nano` fails, and one with `n` or `lite` passes. The synthetic sidecars of `skellytracker/tests/sidecar/test_model_validation.py` use `nano` (line 44) at `v2024.09.1019` (lines 18, 61), so they stay valid. Golden parity test: none. A size key changes no tensor and no decoded output (part 5). |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py` (`SidecarModel._check_sizes`). The package sidecars stay legacy, so their keys do not change now. For the implementer: when a package sidecar moves to `vNEXT`, its keys change (for example `rtmw-l-m_256x192` to `m`). Its keys are also the public `model_name` of the detector configs (`skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:44, 49-51`; `README.md:101-102, 151`). That move is a separate change. |

## 7. Exporter impact

Each rename changes the size key, the per-size id (`<model_id>-<size>`) and each artifact file name
(`{model_id}-{size}_{batch}_{precision}.onnx`, `format/file-layout.md:30`).

| Exporter | Affected sidecars | Change | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmdet-person`: `nano` > `n`, `medium` > `m` (`rtmdet_person/identity.py:115, 127`); the per-size ids `rtmdet-person-nano` and `rtmdet-person-medium` (`:116, 128`) become `rtmdet-person-n` and `rtmdet-person-m`. `rtmw-wholebody133`, `rtmo-coco17-body7` and the four planned families: none (their keys are valid, part 4). | Regenerate `rtmdet-person.yaml`. OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no `rtmdet-person` sidecar until the `rtmdet-person` intake is `describes`, so the regeneration happens at that later round. Cost: 12 new artifact file names (2 sizes, batches 1 to 3, fp32 and fp16; local `exports/detectors/object_detectors/rtmdet-person/`, not in git). The new stems need new raw exports, source passes, accuracy passes and performance passes, and new reports. The old JSON reports stay (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The exporter chooses the default size (user decision S5): its alphabetical order (`rtmdet_person/sidecar.py:136` at `f3aeb47`) puts `m` before `n`, so the default stays the medium size. Plan step 3.6 does the rename and adds a test of each `size_key` against the table (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The sidecar writer uses `yaml.safe_dump` (`pipeline/sidecar.py:118`, the same state), which writes `n:` with no quotes. To follow the quote guidance of 2.3 (user decision S9), the writer needs a representer that quotes `n`. | none. The CLI `--sizes` gets the filter rule of 2.3 (user decision T16; step 3.6, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). Under user decision S8, that rule is a rule of this CLI, not a spec rule. |
| Roboflow-Exporter | `rfdetr`: `nano`, `small`, `medium`, `large` > `n`, `s`, `m`, `l` (`rf_detr/identity.py:11`, `c64fd2a`) | It writes `vNEXT` (`rf_detr/sidecar.py:32`), so its sidecar fails `V-common.sizes-1` after this change. Regenerate. Cost: new names for every artifact (`rfdetr-nano_b1_fp32.onnx` > `rfdetr-n_b1_fp32.onnx`), the per-size `model_id` (`rf_detr/identity.py:34`), the artifact pattern (`pipeline/sidecar.py:39`) and the `--sizes` values (`README.md:186`). Its writer uses `yaml.dump` (`rf_detr/sidecar.py:316`): the quote guidance of `n` applies. | none |
| Ultralytics-Exporter | `yolo26`, `yolo26-body`: `nano`, `small`, `medium`, `large`, `xlarge` > `n`, `s`, `m`, `l`, `x` (`yolo_sidecar.py:36, 175-189`, `2e0280e`) | none now: it writes `v2024.09.1019` (`yolo_sidecar.py:19`), and the legacy rule keeps its keys valid. When it moves to `vNEXT`, it renames. Cost then: every artifact name (`yolo26-nano_b2_fp16.onnx` > `yolo26-n_b2_fp16.onnx`), `SIZE_ORDER`, the CLI tests (`tests/test_export_all_cli.py:34, 42, 48`) and the README. The upstream weights already use the codes (`yolo26n.pt`, `yolo_sidecar.py:176`). Its writer uses `yaml.safe_dump` (`yolo_sidecar.py:605`). | none |
| Qualcomm-Exporter | `mediapipe-person-detector`: `default` (`qai_catalog.py:39`, `qai_sidecar.py:156-157`, `4ca4586`). Planned (secondary: the folder `plans/` is not in git): the hand components in `FAMILIES["hand"]` (the untracked hand pose export plan of Qualcomm-Exporter (plan facts)), also with `default`. | none now: it writes `v2024.09.1019` (`qai_sidecar.py:12`), and skellytracker decision 0008 puts it out of scope until that library is complete (`format/versioning.md:99`). At `vNEXT`, the key `default` stays valid for a family with one size (user decision S2, `V-common.sizes-4`). | none |
| MediaPipe-Exporter | planned: `mediapipe-pose-landmark` (`lite`, `full`, `heavy`), `mediapipe-hand-landmark` and `mediapipe-palm-detector` (`full`, `lite`), the face landmark models holistic (192) and landmarker (256), and the one-size models (the untracked ONNX conversion plan of MediaPipe-Exporter (plan facts); no git repo) | No code yet. `lite`, `full` and `heavy` are valid free words (user decision S1). The two face landmark models are one sidecar `mediapipe-<set>478` (model-id user decision Q2) with the size keys `192` and `256` (user decision S3); write them in quotes. Its plan section 3.8 "Naming question" (`:255-268`) then has its answer for the size keys. A one-size model with no size name takes `default` (user decision S2). MediaPipe-Exporter entry 0010 is proposed, not decided (`notes/decisions/0010-family-sidecar-layout.md:7-8, 17-18`). | none |
| YOLO-Exporter | none (the folder holds only `weights/yolo26n.pt`; no sidecar) | none | none |
| skellytracker package sidecars | `yolox` (`yolox-tiny`, `yolox-m`), `rtmpose-body`, `rtmpose-face`, `rtmpose-hand` (`rtmpose-s_256x192`, `rtmpose-m_256x192`, `rtmpose-m_256x256`), `rtmw-wholebody` (`rtmw-l-m_256x192`, `rtmw-x-l_256x192`, `rtmw-x-l_384x288`) at `v2024.09.1019` | none. Their legacy meaning does not change (2.6). | none |
| Spec examples | `rtmdet-person.yaml`, `yolo26.yaml`, `yolo26-body.yaml`, the composition example | Copy `rtmdet-person.yaml` again from the exporter after its rename. Edit the YOLO26 examples (part 2.1). | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change: any lowercase token (the near-miss of today) | One size has two or more spellings (`medium` in 4 of 6 shipped medium families, `m` in 2 of 6). The hyphen examples `l-m` and `x-l` name teacher-student checkpoints, not sizes of the end model. | `common/sizes-and-artifacts.md:33`; part 1; user decision S6 |
| A closed code table: a key must be a code (the first form of this proposal) | The user decided that the table is an alias map, not a closed list. `lite`, `full` and `heavy` stay valid (user decision S1). A closed table also made each new upstream word a spec change. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| Full words as the codes (`nano`, `small`, `medium`, ...) | The user chose codes (T17: `medium` > `m`, `nano` > `n`, `tiny` > `t`). Most upstream libraries use the letters (Ultralytics, RTMO, RTMW, RTMPose, easy_ViTPose). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); part 1 |
| An alias as a valid key (`medium` and `m` both valid) | Two keys for one size give two file names and two size ids for one model. The table joins the spellings into one code (user decision S1). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| A size order in the table | The user decided no order (S1, S5, S7). The exporter chooses the default size. `b` sits between `s` and `l` in ViTPose and between `m` and `l` in YOLOv10, so one order does not fit both. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); 2.3 |
| `xl` as the code of the extra-large size | Ultralytics, RTMW, RTMPose and RTMDet use `x` (`yolo26x.pt`; `rtmw-x`; `rtmpose-x`; `rtmdet_x`). RF-DETR uses `xl` in its URLs and `xlarge` in its file names. Thus `x` is the code and `xl` is an alias (proposal choice). | `yolo_sidecar.py:180`; `CONFIG_SOURCES.md:24-25`; the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (secondary); `0017-person-detectors-only.md:13`; `rfdetr/assets/model_weights.py:263-264` |
| The name "extra-large" for `x` | The written name in use is `xlarge`: the Ultralytics key and display name, the RF-DETR class names and the removed RTMDet family. | `yolo_sidecar.py:180`; `rfdetr/variants.py:219`; `0017-person-detectors-only.md:7` |
| `b` = base (ViT-B only) | The user decided `b` = balanced, with `base` as an alias (S7). A size name gives the size of the end model, so the ViT-B backbone name is not the reason. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| Leave out `h` (huge) | ViT-H exists upstream (ViTAE `ViTPose_huge`). T13 leaves it out of this export, as a later option. Without the code, that export would write the free word `huge` or `h` with no table entry (proposal choice to keep it). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| The legacy package form `<code>_<height>x<width>` (`rtmpose-m_256x192`) | `_` separates the batch in a file name (`format/file-layout.md:30`). The width form of a key is `<word>-<height>x<width>` (user decision S8). | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| Width first (`m-192x256`) | The user decided height first, as the OpenMMLab names and OpenMMLab-Exporter decision 0003. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); `notes/decisions/0003-rtmw-height-width.md` |
| No form `<height>x<width>` with no word (proposal choice to allow it) | Two sizes with no name and one input height then have no key. The form uses the same `dims` rule as the word form, so the grammar stays one rule. A free word starts with a letter, so the form cannot be read as a word. No family needs it today. | 2.3 |
| A height on every key (`m-256` also when `m` has one height) | The plan and the shipped RTMW keys add the height only for one word at two heights. RTMW already ships `m`. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (secondary); `rtmw/identity.py:97` |
| Any token after the hyphen (`x-p6`, `l-swin-b`, `l-m`) | The token is then a checkpoint, a head or a backbone, not an input size. A backbone with another channel order is a new family. | skellytracker `notes/sidecar-exporter-coverage.md:16`; `common/sizes-and-artifacts.md:178` |
| Two forms of one word in one sidecar (`l` and `l-384`, or `m-256` and `m-256x256`) | A partial run writes only the sizes on disk. The key `l-256` would then change to `l` and back, with new file names and size ids. Rule 3 (proposal choice) prevents a mixed form in one sidecar. | `common/sizes-and-artifacts.md:169, 172` |
| A family with one size takes a code, or a file name with no size part | The user asked for a form where a size filter never selects a model with no size (S2). A code would be selected by a filter. A file name with no size part changes `format.file_layout` and the `sizes` map. The user approved the reserved key `default`, valid only when `sizes` has one key (user decision S2). Qualcomm-Exporter already writes it. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); `qai_catalog.py:39` |
| Two `model_id`s for the MediaPipe face landmark models | The model-id user decision Q2 makes them two sizes of one sidecar when the family invariant holds. Their keys are `192` and `256` (user decision S3). | `specs/sidecar/proposals/model-id-suffix/proposal.md`, part 2.3, "User decisions after T14", Q2; the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| A normative selection rule for every host (the earlier text of 2.3) | The user decided that host selection is out of scope and that the skellytracker implementation of a selection is out of scope (S8). The rule is informative guidance for an exporter CLI. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); `common/sizes-and-artifacts.md:47` |
| The plain T16 prefix rule for every key, also legacy keys | `l` would select the legacy key `l-m` (an RTMW M model), and `x` would select `x-l` (an L model). The informative guidance applies the prefix only to a size key (proposal choice). For the keys of this exporter after the rename, the two rules give the same result. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts); part 1 |
| A case-insensitive selector | The keys are lowercase (`V-common.sizes-1`). An exact match is simpler. The exporter plan tests case sensitivity. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| A validation rule for the quotes of `n` | The user decided guidance only (S9). PyYAML reads a bare `n` as a string. A rule would need a check of the raw text, not of the parsed map. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) |
| A change to `common.sizes_and_artifacts` in place of a new section | Possible. The alias table, the grammar and the checks have their own functions and vectors. The template puts one contract unit in one section with one reference module. The skellytracker session can merge the text into `common.sizes_and_artifacts` (the module then is `common_sizes_and_artifacts.py`). | `specs/sidecar/templates/change-proposal.md:3-5, 205-209` |

## Open questions for the user

The user decided S1 to S9 on 2026-10-23 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The earlier
questions Q1 to Q9 of this proposal are closed: Q1 by S1, Q2 by S2, Q3 by S3 (and the model-id user
decision Q2), Q4 by S4, Q5 by S5, Q6 by S6, Q7 by S7, Q8 by S8 and Q9 by S9.

The label question L1 is closed. The user decided on 2026-10-23 that the reserved key `default` with
`V-common.sizes-4` is a user decision (S2), not a proposal choice. The plan records the approved spec
form: "a reserved key, for example `default`, valid only when `sizes` has one key, and no size filter
matches it" (the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). Part 2, part 4 and part 7 mark it "user decision S2".
No question for the user stays open.

These proposal choices stay open to change at review. Each is marked "proposal choice" in part 2:

- the form `<height>x<width>` with no word;
- the dims on a free word: `<free_word>-<height>` and `<free_word>-<height>x<width>` (S3 and S8 give
  the dims only on a code);
- the "Form of a key" rule of 2.3 (the form is a property of the family; no key of a word with two
  heights is bare);
- `V-common.sizes-2`: the dims of a key must agree with `input.shape`;
- `V-common.sizes-3`: one form for each word in one sidecar;
- the quote guidance for the YAML reserved set (`y`, `yes`, `no`, `on`, `off`, `true`, `false`,
  `null`; S9 names only `n`);
- the codes `s`, `l`, `x`, `h`, and the aliases `xl` and `xxlarge`;
- the character rule of a free word (ASCII lowercase letters and digits, first a letter), and the
  guidance to write an upstream word in lowercase;
- the file-layout example `rtmw-wholebody133-l-256_fp32.onnx` for the legacy `x-l` example;
- in the informative filter: the prefix part only for a size key;
- a detail of the grammar for the key `default` (user decision S2): it takes no dims
  (`default-256` is not a size key).

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. All four intakes name this proposal by its file name in
      prose under "Proposals and reference files", not in the table of that section: Halpe26
      (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)), DWPose
      (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)), ViTPose
      (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)) and ViTPose++
      (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts)). The two ViTPose paragraphs were added
      by the review-readiness audit of 2026-10-23. The ViTPose intakes also name it in row F3 (`:110`,
      `:97`). This proposal closes no intake row (header row "Intake rows"), so no intake table row is
      necessary. The three intakes of the current families (written 2026-10-24) also name it: the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts), and the untracked intake of `rtmo-coco17-body7` of OpenMMLab-Exporter (plan facts) ("the size-code proposal", not by its file name). Checked by the review-readiness audit 2 (2026-10-24); the lines of the first six intakes checked again on 2026-10-24.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing. The MediaPipe
      rows (no git repo) and the plan rows for Halpe26, ViTAE and the ViTPose parameter counts are
      secondary; each names its primary file, or `to run` (the parameter counts; checked on
      2026-10-25).
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in `plans/`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a (no pixel case)
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. n/a (no tensor changes; part 5 gives the reason)
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. n/a
- [x] No file in skellytracker changed.

## Before acceptance

These items must be done before the user can accept this proposal.

**Parts**

- [ ] Add the missing edit places to part 2.1: the "Compatibility impact" bullets of
      `specs/sidecar/changelog.md` (a `vNEXT` sidecar must write a code, not an alias), the
      `inventory.yaml` records of the two YOLO26 forecasts, and the comment
      "small, medium, large, xlarge" at `yolo26-body.yaml:114`.
- [ ] Add to the no-edit list of part 2.1 the other evidence prose that names a size word:
      `common/batching.md:39, 42`, `common/input.md:77`, `post/detection-decode.md:115`,
      `pre/resize-stretch.md:57`, `post/selection-top-k.md:66`, `common/identity.md:77`,
      `common/sizes-and-artifacts.md:134, 139, 141, 144, 167`, `format/file-layout.md:145` and
      `changelog.md:48-49`.
- [ ] Decide if `templates/model-intake.md:144` changes. It says "the size name in F3". The new
      term is "size key".
- [ ] Correct the Header row "Exporter commit". OpenMMLab-Exporter commit `f3aeb47` is on
      `origin/main`, so "not pushed" is false.
- [ ] Add the section ID to the docstrings of the helpers `_require_list`, `_is_word`, `_parts` and
      `_form` in the part 3 code. Add a docstring to `_as_int`. The template asks for the section
      ID in each docstring.
- [ ] Remove the citations of exporter plan lines from the module docstring of the part 3 code
      before it goes into `specs/sidecar/reference/common_sizes.py`.

**Evidence**

- [ ] Write and commit the OpenMMLab-Exporter test that checks each identity `size_key` against the
      alias table (plan step 3.6). Part 5 names it as the check. It does not exist yet.
- [ ] Replace the uncommitted scratch runner of part 4 with a committed check. The result
      `191/191 pass` and the scratch check of local exports in part 5 are not evidence.
- [ ] Give the primary source, or write `to run`, for each fact that has no pinned source: the
      Ultralytics version of `ultralytics/utils/downloads.py` and `cfg/models/v10/*.yaml`, an
      upstream commit of `easy_ViTPose/inference.py`, the rfdetr 1.11.2 release file in place of a
      local `.venv` path, and the MediaPipe size names and input sizes. The MediaPipe facts are
      secondary only, because MediaPipe-Exporter has no git repo.
- [ ] Cite each exporter commit of the landed text with a GitHub permalink that pins a full SHA on
      the default branch of its repository: `f3aeb47`, `1dfec48` and `d0f4343` (OpenMMLab-Exporter),
      `2e0280e` (Ultralytics-Exporter), `c64fd2a` (Roboflow-Exporter) and `4ca4586`
      (Qualcomm-Exporter). The proposal gives short SHAs only.
- [ ] Measure the parameter counts of the ViTPose `s`, `b`, `l` and `h` checkpoints (`to run`). The
      counts now come from the file sizes in an untracked plan. The choice `b` = balanced uses them.

**Template checklist**

- [ ] "Part 1 cites primary evidence, or names the primary evidence that is missing": the box is
      ticked, but part 1 does not name the missing sources of the Evidence items above.
- [ ] "The intake links to this proposal": the intakes name the proposal only in prose. The RTMO
      intake names it only as "the size-code proposal".
- [ ] "The header gives the dependencies": "Depends on" names `model-id-suffix`, but the same cell
      says that this proposal can land first. Write it as a soft dependency. "Needed by" names a
      plan step, not a proposal.
- [ ] "Part 2.1 lists each place that the change edits": see **Parts**.

**Vectors and tooling**

- [ ] Make the 191 cases fit the limit of `tools/tests/test_vectors.py:185` (a vector file must be
      smaller than 16 KiB). In the form of `tools/make_vectors.py`, the cases are about 20.2 KB (a
      scratch measurement of the audit, not evidence). Cut, split or move the cases, or change the
      limit.
- [ ] Decide the case form for all proposals: `CASE_KEYS` in `tools/tests/test_vectors.py` has no
      `function`, and `generated_by` must be `tools/make_vectors.py`.
- [ ] Make the cases with the reference code at landing. Decision 0013 says that the generator
      computes the vectors or calls the reference. The writer of this proposal wrote the cases by
      hand.
- [ ] Decide if decision 0013 ("a file holds numbers only") allows cases with strings and
      booleans.
- [ ] Add the runner test and the generator hook for `specs/sidecar/reference/` in a non-spec
      tooling PR first. This would be the first file in that folder.

**Decisions for the user**

- [ ] Choose the final section ID: `common.sizes`, `common.size_keys`, or a merge into
      `common.sizes_and_artifacts` (part 8). The choice changes the rule IDs, the vector file name
      and the reference module name.
- [ ] Keep or remove the informative filter guidance (user decision S8) and `matches_size` and
      `select_sizes` in the normative section.
- [ ] Decide if `normalize_size_key` changes the case. The authoring guidance says that an
      upstream `Lite` gives `lite`. The case `normalize-capital` expects `null`.
- [ ] Accept or reject each proposal choice in "Open questions for the user".
- [ ] Decide how `V-common.sizes-1` to `-4` apply under `base` composition: to the resolved
      sidecar or to the file. An example is a `vNEXT` derived sidecar with a legacy base that has
      `nano`.
- [ ] Confirm the source of S6. The exporter plan does not mark S6 as a user decision, and its
      bracketed default is `rtmw-wholebody133-l-384`. The proposal uses
      `rtmw-wholebody133-m_fp32.onnx` and calls it "user decision S6".
- [ ] Confirm the source of the spelling `default`. The exporter plan records "a reserved key, for
      example `default`". The proposal calls the spelling user decision S2.
- [ ] Decide if the normative text cites the exporter plan decisions (S1 to S9, T13, T14, T16, T17,
      Q2), for example in the column "Source of the choice" of the alias table. Tracked files must
      not cite the untracked exporter plans.
- [ ] Decide what happens to the reference examples. After landing, the keys `nano` and `medium` of
      `rtmdet-person.yaml` and the key `nano` of the YOLO26 forecasts fail `V-common.sizes-1`. The
      re-copy of `rtmdet-person.yaml` waits for OpenMMLab-Exporter 0050. The hand edit of the
      YOLO26 forecasts in part 2.1 conflicts with `phase-3-skellytracker.md` ("Nobody corrects the
      example by hand") and with the allowed `edits` of `inventory.yaml`.
- [ ] Decide if the guidance edits (`mapping-hints.md`, row F3 of `model-intake.md`, and a quote
      rule in `sidecar-files.md:19`) go in the content PR or in a separate non-spec PR.
- [ ] Decide one rule for all proposals for the link of a new "Legacy behaviour" heading in
      "Version-aware compatibility" of `format/versioning.md`.

**Merge points**

- [ ] `model-id-suffix` (0025) lands first (soft order). Both edit `format/file-layout.md:27-30`
      and `:44-89`, `common/sizes-and-artifacts.md:101`, `specs/sidecar/README.md:18-19`,
      `mapping-hints.md:13-32`, `common/identity.md` and the examples under
      `examples/detectors/keypoint_detectors/`.
- [ ] `roi-transform-and-source` (0020) edits `common/sizes-and-artifacts.md:30` and `:112`
      (`V-common.sizes_and_artifacts-4`, which `V-common.sizes-2` works with). This proposal does
      not list these lines.
- [ ] `roi-refiner-role` (0047) edits the table "Contract part | Where it lives" at
      `common/sizes-and-artifacts.md:49-54`, the storage tree of `format/file-layout.md` and
      `mapping-hints.md`. This proposal does not list the table.
- [ ] `simcc-score-rule` (0024), `heatmap-decode-refinement` (0038), `affine-crop-arithmetic`
      (0037), `model-id-suffix` (0025) and `roi-transform-and-source` (0020) also edit
      "Version-aware compatibility" (`format/versioning.md:53-63`).
- [ ] `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic` (0043),
      `affine-crop-arithmetic`, `model-id-suffix` and `keypoint-visibility` (0039) also edit
      `BUILDERS` of `tools/make_vectors.py` and `CASE_KEYS` of `tools/tests/test_vectors.py`.
- [ ] `keypoint-visibility` (0039) also edits the "Family" hint and the "Sidecar YAML" text of the
      exporter guide.
- [ ] `keypoint-visibility` (0039), `pose-decode-flip-test` (0045), `landmark-extra-outputs` (0021),
      `roi-transform-and-source` (0020) and `roi-refiner-role` (0047) also add rows to the section
      map and the validation index of `specs/sidecar/README.md`.
      `tools/tests/test_traceability.py` checks the order of the section-map rows.
- [ ] `roi-refiner-role` (0047) also edits `common/identity.md`, with its "Authoring guidance"
      (`:76-81`). This proposal edits `common/identity.md:32`.
- [ ] The 13 spec proposals add a row to "Summary of changes" and a sentence to the `vNEXT` row of
      `changelog.md:68`. `omitted-upstream-output` (0044) adds no changelog row. The row number `N`
      is set at merge time. `simcc-score-rule`, `heatmap-decode-refinement`, `normalize-arithmetic`,
      `affine-crop-arithmetic`, `model-id-suffix`, `roi-transform-and-source`,
      `landmark-extra-outputs` and `landmark-depth-divisor` (0022) also edit "Compatibility impact"
      (`changelog.md:55-59`). This proposal must add a bullet there too (see **Parts**).
