# Evidence: simcc-score-rule

This file uses ASD-STE100 Simplified Technical English.

## Upstream code

mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`), read in
the published exporter image with the tag `df-dcab32049439` ([OpenMMLab-Exporter ADR-F5VE](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/F5VE-docker-image.md)) (the clone at that commit; the installed package has
the same `post_processing.py`):

- [`mmpose/codecs/utils/post_processing.py:41-105`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L41-L105) (`get_simcc_maximum`)
- [`mmpose/codecs/simcc_label.py:174-200`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/simcc_label.py#L174-L200) (`SimCCLabel.decode`)
- [`mmpose/models/heads/base_head.py:78-94`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/heads/base_head.py#L78-L94) (the first value is `keypoint_scores`)
- [`configs/wholebody_2d_keypoint/rtmpose/cocktail14/rtmw-m_8xb1024-270e_cocktail14-256x192.py:47-53`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/wholebody_2d_keypoint/rtmpose/cocktail14/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L47-L53) (the RTMW codec)

## Parity run (OpenMMLab-Exporter ADR-0053)

- Scripts: OpenMMLab-Exporter commit `16b06c10986d2010989b101a13d56cbfebbd6748` (on `main`), folder
  `notes/decisions/scripts/`: [`simcc_score_rule_parity.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/16b06c10986d2010989b101a13d56cbfebbd6748/notes/decisions/scripts/simcc_score_rule_parity.py),
  `simcc_score_rule_worker.py`, `simcc_score_rule_ap_worker.py`, `pose_parity.py`,
  `pose_parity_common.py`, `pose_parity_mmpose_worker.py`, `pose_parity_boxes.py` and the box set
  `pose_parity_boxes.json`. The run recorded the SHA-256 of each script. Each value equals the SHA-256
  of the file at `16b06c10986d2010989b101a13d56cbfebbd6748`. At
  `d9704753a22792c32a1d3018a0c9e9ea2d279d71` the files are in `decisions/scripts/`.
- Decision entry: [OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0053-pose-sidecar-parity-runs.md).
- Result files. Git does not track them. The scripts above made them:
  - `gates.json`, written 2026-10-25T21:45:29Z, SHA-256
    `4620ecbd20dcbd631b88923714d1aa843dde8e186723851d313d4baa7d3c9686`;
  - `summary.json`, SHA-256 `881a2fec6cb3562531132142ab601e275757660dfe2695cd5ffa26b5466fdbd5`
    (result `pass`, no missing run);
  - `ap.json`, SHA-256 `d472fd3ff9b03bb8f2672e4b360ae168a0f76566a147ee7918b8bafe7633a77e`
    (pycocotools 2.0.7 and xtcocotools 1.14.3 in the exporter image).
- Reference file of the run: an earlier draft of `reference/post_pose_decode_simcc.py`, SHA-256
  `14305a21074db1e29bd1649d9648b957be2c1b1a4959f88a6075c5b1b3faef25`. It is not in git. It had the
  same rule. It also had a legacy score function (the softmax mean), which the current spec does
  not have (no legacy layer).

## Rerun with the reference file of version 1 of this bundle (OpenMMLab-Exporter ADR-VB67)

- Script: OpenMMLab-Exporter commit `438138208691a522f54320961f058e61b60d54a3`,
  [`decisions/scripts/simcc_score_rule_bundle_rerun.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/438138208691a522f54320961f058e61b60d54a3/decisions/scripts/simcc_score_rule_bundle_rerun.py).
  It runs the unchanged scripts of the first run with an adapter of
  `reference/post_pose_decode_simcc.py` of version 1 of this bundle (SHA-256
  `45f24b0dcabb4ba0f7d17e1325d5989e17f09c0a6d632077bbe221d462777879`). The other four reference files
  are the files of the first run (SHA-256 prefixes: affine `26ccb39f`, normalize `2d19f610`, heatmap
  `84b1d337`, flip test `179e766a`). The run recorded each script as `committed` at that commit.
- Decision entry: [OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/18320f4e51660fe0cb9c546441eb9be09d53f339/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md).
- New upstream dumps with the same command and box set (the large arrays of the first run were not
  kept). Host: ONNX Runtime 1.31.1 CUDA, TF32 on.
- Result files. Git does not track them:
  - `gates.json`, written 2026-11-06T17:23:17Z, SHA-256
    `44c3e26fa3d9c996554e241544fc2ddb54925f4d3b5e9270094360aa7b8495fc`. The gates equal those of
    the first run; one source path changed (`notes/decisions/` to `decisions/`);
  - `summary.json`, SHA-256 `626b0fd78339ebcbe7468fa78dba666769423e2089fac65837dfe6dcf2d68615`
    (result `pass`, no missing run);
  - `ap.json`, SHA-256 `30141bcc0cfc1d573000fa4130467d731b9a6d7fbfac30e9a6df5a775fd0879c`.
- Result: the same numbers as the first run (the table below).

## Numbers (RTMW runs; the first run and the rerun give the same values)

| Quantity | RTMW-m 256x192 | RTMW-x 384x288 |
|---|---|---|
| Persons (GT + synthetic) | 6352 + 18 | 6352 + 18 |
| Bins `X_bins`, `Y_bins` | 384, 512 | 576, 768 |
| Export error `E`, max | 0.0229 | 3.909 (TF32) |
| Preprocessed input, `reference_crop` path | 6370 of 6370 bit-equal | 6370 of 6370 bit-equal |
| Decode-only: values that differ | 0 of 2541630 | 0 of 2541630 |
| G3 score violations | 0 of 847210 | 0 of 847210 |
| G4 bin violations | 0 of 1694420 rows | 0 of 1694420 rows |
| G6 keypoints with an upstream score `<= 0` | 0 | 0 |
| AP upstream | 0.74766 | 0.79530 |
| AP host, min rule | 0.74769 | 0.79523 |
| AP, mean of the raw peaks | 0.74612 | 0.79507 |
| AP, mean of the softmax peaks | 0.65602 | 0.72182 |

The other four runs (RTMPose Halpe26 m-256 and m-384, DWPose m and l-384) also passed each gate. The
rule for a score `<= 0` ran on Halpe26: 3 keypoints (m-256) and 1 keypoint (m-384), 0 violations.
