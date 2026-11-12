# Evidence: affine-crop-matrix

This file uses ASD-STE100 Simplified Technical English.

## Upstream code

mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`). The published exporter image with
the tag `df-dcab32049439` ([OpenMMLab-Exporter ADR-F5VE](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/F5VE-docker-image.md))
holds this commit. Its environment: Python 3.8.10, NumPy 1.24.4, OpenCV 4.5.4, mmengine 0.10.3,
mmcv 2.1.0, torch 2.0.0 (the `environment` record of the upstream dumps). The installed files equal
the files of the clone at that commit, and the files at the links below (SHA-256 of each file):

- [`mmpose/structures/bbox/transforms.py`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py)
  (`f08047f2`): `bbox_xyxy2cs` [lines 44-73](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L44-L73),
  `get_warp_matrix` [lines 372-435](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L372-L435),
  `_rotate_point` and `_get_3rd_point` [lines 493-525](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/structures/bbox/transforms.py#L493-L525).
- [`mmpose/datasets/transforms/topdown_transforms.py`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py)
  (`e7beb8e6`): `TopdownAffine._fix_aspect_ratio` and `transform` [lines 55-137](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/topdown_transforms.py#L55-L137).
- [`mmpose/datasets/transforms/common_transforms.py`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/common_transforms.py)
  (`a1596938`): `GetBBoxCenterScale` [lines 31-82](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/datasets/transforms/common_transforms.py#L31-L82).
- [`mmpose/apis/inference.py`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/apis/inference.py)
  (`37e7c59a`): `inference_topdown`, the box dtype [lines 160-176](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/apis/inference.py#L160-L176).
- [`mmpose/models/pose_estimators/topdown.py`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/topdown.py)
  (`f954aab7`): the closed-form inverse [lines 150-156](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/pose_estimators/topdown.py#L150-L156)
  (row D11; the proposal does not change the Inverse).

## Exporter code

- The current text, in exact math: OpenMMLab-Exporter `onnx_runtime/preprocess.py::affine_crop_geometry`
  and `AffineCropMeta.matrix` at [`a37a47d29f227365661eae59ab9b2f8da665c18d`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/onnx_runtime/preprocess.py).
  At that commit, the file had not changed since commit `5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278`
  ([OpenMMLab-Exporter ADR-H1EF](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/H1EF-host-code-passes-all-section-vectors.md)).
  The later commit `7bc72b45137faa4b211d05a38f58812ffae5a109` changes only the normalization check
  of the file. The affine functions are the same at the exporter commit of this version.
  Its docstring says: "The crop follows the spec text. It does not copy the float32
  `cv2.getAffineTransform` of mmpose." Record R0 of the parity run confirms it: the host crop is the
  warp with the exact-math `M`.
- The intake rulings: [OpenMMLab-Exporter ADR-W2Y4](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/W2Y4-intake-rulings-yolox-rtmw.md)
  (item 5: row T4b is a `near-miss`; rows T10 and D11 are `exact`).
- The parity run: [OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md)
  (the section "Parity" below).

## Inputs of the parity run (part 5)

- The upstream dumps of the simcc-score-rule rerun of 2026-11-06
  ([OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md)).
  Six runs: RTMW m (256x192) and x-384 (384x288), RTMPose Halpe26 m-256 and m-384, DWPose m and
  l-384. Each run has 6370 persons (6352 COCO val2017 GT persons and 18 synthetic boxes), the box
  rule `f32_xyxy`, the mode `noflip` and the save level `standard`. The worker is
  [`decisions/scripts/pose_parity_mmpose_worker.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/scripts/pose_parity_mmpose_worker.py)
  (SHA-256 `ed2744e8`). Git does not track the dumps.
- The box set of the dumps: `pose-parity-full.json`, SHA-256
  `7a36a2eea15a9209bab71596b7e640317339488755e869312c7048532de2fd68`. The committed 318-person set
  [`decisions/scripts/pose_parity_boxes.json`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/scripts/pose_parity_boxes.json)
  (SHA-256 `b74c6aa0e86ecec7116f642683a2a11516e7c0d16a5ce39dfc601b250ddd3871`) is a subset: each of
  its 318 persons is in the dumps.
- The dump arrays that the check reads: `crop_reference` (the reference crop with the OpenCV of the
  container), `crop_sha256` (the SHA-256 of the upstream `TopdownAffine` crop), `noflip.kpt_crop` and
  `noflip.kpt_src`. `dump.json` holds the upstream `M` (`warp.matrix`), `input_center` and
  `input_scale` of each person.
- The ADR-VB67 run recorded the geometry of the earlier float32 reference file (pre-split, SHA-256
  prefix `26ccb39f`) with no gate: on each of the 6 runs, 6370 of 6370 persons had an `M` equal to the
  upstream `M` (max abs difference 0.0), and the container reference crop equalled the upstream
  crop in 6370 of 6370 crops. The host tensor made from the container reference crop equalled the
  upstream tensor bit for bit in 6370 of 6370 crops (max abs difference 0.0). Body OKS AP, host on
  the reference crop against upstream: RTMW m-256 0.74769 against 0.74766, RTMW x-384 0.79523
  against 0.79530; at most 7.9e-4 on each path (fields `geometry`,
  `step4_preprocessed_input.reference_crop` and gate 7 of the ADR-VB67 run files).
- The target sizes of all 6 runs are 256x192 and 384x288, so `T_w / T_h = 0.75`. That value is exact
  in float32. Thus no run tests the rounding `a = f32(T_w / T_h)` for a ratio that is not exact. That
  rounding comes from the code reading of `TopdownAffine._fix_aspect_ratio` (in NumPy 1.24.4, a
  float32 array times a Python float gives a float32 loop) and from the vector case
  `aspect-fix-divides-by-a` only.

## Uncommitted checks of this draft (secondary)

These checks ran on the host (NumPy 2.5.4, OpenCV 5.0.0; skellytracker env NumPy 2.4.6, OpenCV
4.13.0). They are not evidence. The gated run of the section "Parity" replaces each of them, except
the check of the skellytracker form.

- The skellytracker `get_warp_matrix` with the mmpose aspect fix, on the 318 persons of
  `pose_parity_boxes.json` at 256x192: its `M` differs from the `M` of the reference file on 317 of
  318 persons with a float32 box (max 1.0e-3). It also differs on 317 of 318 persons when the
  float32 box (`bbox_input_xyxy_f32` of the dump) is cast to float64 first (max 3.5e-3). Part 8 of
  the proposal uses this check only for the alternative "The skellytracker form". The gated run does
  not test it.
- The `M` of the three COCO vector cases equals the upstream `M` of the dumps for the same box (the
  persons `a187477` and `a1708970` of RTMW m, `a1224758` of RTMW x-384). The gate G1 also covers
  these three persons.
- Historic notes. The gated run replaces three earlier checks, and their numbers are not evidence.
  (1) The deleted scratch check of the user ruling (cited first in row T4b of the RTMW intake): the
  float32 `M` differed from the exact-math `M` by up to 3e-3, and the crops differed by 1 grey level
  on 289 of 318 boxes. The gated run gives 292 (256x192) and 293 (384x288) of 318. (2) An
  uncommitted run of the draft check on the full dumps. Its G1 and G2 values equal those of the
  gated run. (3) A smoke test of the draft script on the first 20 persons of the two RTMW runs.

## Vectors

- `vectors/pre.resize.affine_person_crop.yaml`: 9 new cases. `fill` of skellytracker
  `tools/make_vectors.py` at `8351b7f8c20c8db74eb3e547478970e4dceb0308` wrote `expect` and found no
  problems. A second `fill` on a scratch copy, after the final edits of the proposal text, changed
  no byte.
- Version 2: `fill` of skellytracker `tools/make_vectors.py` at
  `8fed6f34eb22643e0b6cc38a7c6b80014bfe1d75` (NumPy 2.4.6, OpenCV 4.13.0) ran again on the payload
  file with the reference file of version 2. It found no problems and changed no byte.
- The 20 current cases of `specs/model-sidecar/vectors/pre.resize.affine_person_crop.yaml` at
  `8fed6f34` agree with the reference file at the tolerance 1e-4 (`fill` on a scratch copy of the
  current file and the 9 new cases; one value changed inside the tolerance). `check_rules` gives the
  `expect` of each of the 5 data-only cases. Since `8351b7f8`, the current file lists the
  OpenMMLab-Exporter host in `verified_against` of its 15 numeric cases. No `expect` changed.
- The OpenMMLab-Exporter host (`onnx_runtime/preprocess.py::affine_crop_geometry` and
  `unproject_affine`, NumPy 2.5.4, OpenCV 5.0.0) implements the current text. On the 9 new cases, the
  7 forward cases fail at `atol` 1e-6 (the maximum difference is 2.8e-3), and the 2 Inverse cases pass
  at the tolerance 1e-4 (the maximum difference is 6.8e-5). The host passes each of the 15 numeric
  current cases. This is the result of part 7 of the proposal.
- The reference file of the bundle: `reference/pre_resize_affine_person_crop.py`. Version 1 has the
  SHA-256 `62bd8750eb82b0f8c5204900e646b6e412d1d6b9eda9a8f34baed9fbb5883219`. The gated run used this
  file. Version 2 has the SHA-256
  `dd06867f3e4aaea0d2a2a06dd4ea1556d95f6e3103aab722535dda8f37e8b302`. It changes only lines of the
  module docstring. With the docstrings removed, `ast.dump` gives the same result for the two files.
  The manifest of `pack` gives the final hash.

## Parity

[OpenMMLab-Exporter ADR-6A8S](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/a37a47d29f227365661eae59ab9b2f8da665c18d/decisions/entries/6A8S-affine-crop-matrix-evidence.md).
Result `pass` on each of the 6 runs.

- Script: [`decisions/scripts/affine_crop_matrix_check.py`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/0d07c982fb6915fee6fa0b8ccac35873c77c4db2/decisions/scripts/affine_crop_matrix_check.py)
  at commit `0d07c982fb6915fee6fa0b8ccac35873c77c4db2` (SHA-256
  `87f07b9bfaf296c4cb3682f9f4d42247e0fcbc0e1952e1daf9600db42f7f6205`), format
  `affine-crop-matrix-check-2`. The run recorded each repository file of the check as `committed`,
  also `onnx_runtime/preprocess.py` (SHA-256 `7deabae6` of the CRLF checkout that the run read; the
  committed file has `f11ccc43`) and
  `decisions/scripts/pose_parity_common.py` (SHA-256 `e12d6755`). Host CPU: Python 3.14.2, NumPy
  2.5.4, OpenCV 5.0.0.
- Gates: written to `gates.json` at 2026-11-06T19:44:54Z, before the measurement. The measurement
  wrote `summary.json` at 2026-11-06T19:46:32Z.
- Settings of the gates: `expand_ratio` 1.25, `maintain_aspect_ratio` true, `interpolation` linear,
  `pad_value` 0, box rule `f32_xyxy`, vector atol 1e-6.
- G0 and G1 pass on each run. Each run has 1827 persons in the branch `h` (`w > h * a`) and 4543
  persons in the branch `w` (else). The 318-person box set has 110 and 208. G1: 6370 of 6370 persons
  on each run, max abs difference of `M` 0.0.
- R0: 0 crops differ on each run. R3: 0 crops differ on each run (max 0).

Values of each run (all persons; the 318-person box set in brackets):

| Run | Target `[T_h, T_w]` | G2 persons above 1e-6 | G2 max | G3 crops that differ (max 1 grey level) | R1 crops equal, max grey levels | R2 max px, reference `M` | R2 max px, exact-math `M` |
|---|---|---|---|---|---|---|---|
| `rtmw-wholebody133-m-full-noflip` | `[256, 192]` | 6226 (295) | 2.396e-3 (1.797e-3) | 5992 (292) | 0, 7 (0, 6) | 8.73e-5 | 6.48e-5 |
| `rtmw-wholebody133-x-384-full-noflip` | `[384, 288]` | 6245 (297) | 3.594e-3 (2.696e-3) | 6047 (293) | 0, 7 (0, 6) | 9.55e-5 | 7.30e-5 |
| `rtmpose-halpe26-m-256-full-noflip` | `[256, 192]` | 6226 (295) | 2.396e-3 (1.797e-3) | 5992 (292) | 0, 7 (0, 6) | 8.30e-5 | 6.54e-5 |
| `rtmpose-halpe26-m-384-full-noflip` | `[384, 288]` | 6245 (297) | 3.594e-3 (2.696e-3) | 6047 (293) | 0, 7 (0, 6) | 7.99e-5 | 6.51e-5 |
| `dwpose-wholebody133-ubody-m-full-noflip` | `[256, 192]` | 6226 (295) | 2.396e-3 (1.797e-3) | 5992 (292) | 0, 7 (0, 6) | 8.73e-5 | 6.71e-5 |
| `dwpose-wholebody133-ubody-l-384-full-noflip` | `[384, 288]` | 6245 (297) | 3.594e-3 (2.696e-3) | 6047 (293) | 0, 7 (0, 6) | 8.12e-5 | 7.08e-5 |

- G2 counts only the persons above 1e-6. All 6370 persons of each 256x192 run, and 6369 of 6370
  persons of each 384x288 run, differ by some amount. Below 1e-6 the difference is float64 noise.
- R1: the SHA-256 of the host crop with the reference `M` equals the SHA-256 of the upstream crop in
  0 of 6370 crops of each run. The `M` is the same (G1). Thus the OpenCV build (5.0.0 on the host,
  4.5.4 in the container) causes the R1 difference.
- R2 points: 847210 on each RTMW and DWPose run (133 keypoints), 165620 on each Halpe26 run (26
  keypoints).

Result files (not tracked; the script writes them outside the repository):

| File | SHA-256 |
|---|---|
| `gates.json` | `d54ac0533802dfc124c4a59fc67a3f305f9df7add7565a73892ad67f0584567c` |
| `summary.json` | `36325668ed52ecf16877f9970067623ff725af95e14a80b8943e667856981264` |
| `rtmw-wholebody133-m-full-noflip.json` | `009ee40f5f4f858ab7a395e858e1f61df42aa1e3241bd6acf8fafed7ef88c108` |
| `rtmw-wholebody133-x-384-full-noflip.json` | `cac785e37fb4486c0d9c759238a7749ef70f5daee7c711159af04cceff3ffb4f` |
| `rtmpose-halpe26-m-256-full-noflip.json` | `07de6c0e73e219b97e39f167f975e8ba1d1d6d30cec2c2e42daf3319fbb1dcb8` |
| `rtmpose-halpe26-m-384-full-noflip.json` | `301b15610cd1eb136179c1238b8e588d350da56f7fcb51ec3c58b9727688f4d8` |
| `dwpose-wholebody133-ubody-m-full-noflip.json` | `33f92c9aef0b8a680ab611a5af9d453048888d8a24cfdd703c15c9858ee9f265` |
| `dwpose-wholebody133-ubody-l-384-full-noflip.json` | `15efff4e6358773a3895215266333f680900513ef973850e3e211ccb88037acf` |
