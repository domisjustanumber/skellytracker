# Evidence: simcc-score-map

This file uses ASD-STE100 Simplified Technical English.

The source is OpenMMLab-Exporter ADR-Q7GS (`decisions/entries/Q7GS-simcc-score-map-fit.md`) at
commit `3ca1a596ea71c0969fc8ea960f4c2a41a27777d6`. The scripts are
`decisions/scripts/simcc_score_map_measure.py` and `decisions/scripts/simcc_score_map_fit.py` at the
same commit.

## What changed against `model-rtmw-wholebody133` version 5

The candidate example of this bundle is the v5 sidecar with these changes only:

- `source.version`: `0.3.0` becomes `0.4.0` (OpenMMLab-Exporter ADR-C102: new sidecar bytes need a
  new package version).
- Each of the five sizes has a new `score_map` block after `onnx` (81 new lines).

Each other key and value is the same as in version 5. A parse of both files with the `source` key and
the `score_map` blocks removed gives two equal documents. The `license` block is byte for byte the
same.

The ONNX files do not change. Each SHA-256 below is in the v5 sidecar, in the candidate sidecar, and
is the hash of the file on disk at the run:

| Published file (b3) | SHA-256 | Same as v5 |
|---|---|---|
| `rtmw-wholebody133-m_b3_fp32.onnx` | `77fb20ae9d7b1bf3021029d482b24c3d5f5994bf0cc895debfc052382c4c14db` | yes |
| `rtmw-wholebody133-m_b3_fp16.onnx` | `c9e01ef287f2c18e75828153167af21d10f9f4fd5119cbef61e34c15e4a90179` | yes |
| `rtmw-wholebody133-l-256_b3_fp32.onnx` | `b1e3296d35441eb8445fe1c9bac1e97a07bd7d87e97639e054d187ce6ffb9a39` | yes |
| `rtmw-wholebody133-l-256_b3_fp16.onnx` | `5a024db8ec53240ca6785e328560fb3fd3fb3c1cbfde3be0597204b16828e25a` | yes |
| `rtmw-wholebody133-x-256_b3_fp32.onnx` | `1437f4614bc04a351573a90e939e3289cee92c0bc9c0ee88ca5e8fe734cd5676` | yes |
| `rtmw-wholebody133-x-256_b3_fp16.onnx` | `a23f019ea6e9abd032879cc9b39362a4b27ae68784157f5473c8ae5259677c31` | yes |
| `rtmw-wholebody133-l-384_b3_fp32.onnx` | `f0b6a798acb6efb0a4092842d3a6affd43f8410b3d80c55fd08c589486dbd848` | yes |
| `rtmw-wholebody133-l-384_b3_fp16.onnx` | `8b97bcaed8d242b5af124e9388a01d40b28d8389f247813016740c5ea5f62612` | yes |
| `rtmw-wholebody133-x-384_b3_fp32.onnx` | `ed5b7b2b1d82b323ad753979bf67dbff537e2b43cdf5458aeb3d2f8920b2cf73` | yes |
| `rtmw-wholebody133-x-384_b3_fp16.onnx` | `322657d54a3a057e674eac8cbc0701329852d958cdc3d6483e28bfa58fd958d1` | yes |

The verification batches (b1, b2, b4, b6) of version 5 are not made again. The batch-conversion
verdict of version 5 (`converts`) stays valid: the graphs are the same.

## Run

- Persons: 6352 COCO-WholeBody v1.0 val persons (`coco_wholebody_val_v1.0.json`, SHA-256
  `f8272e9c12f3a42457033ebc75da1167546edf1be5e2ffaf586d6ee97541ff6e`), the GT box, no flip test.
  Fit split (even `image_id`): 3232 persons. Check split (odd): 3120 persons.
- Sidecar path: the v5 sidecar and the exporter host functions (`affine_person_crop`,
  `make_normalizer`, `decode_simcc`, `unproject_points`), ONNX Runtime 1.31.1 CUDA (TF32 on),
  NumPy 2.5.4, OpenCV 5.0.0, RTX 3070. 30 to 83 s for each artifact.
- Sigmas: mmpose v1.3.2 `configs/_base_/datasets/coco_wholebody.py` lines 1139 to 1154
  ([permalink](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/_base_/datasets/coco_wholebody.py#L1139-L1154)).
- The fit set has no point with a raw score `<= 0`, so the missing branch runs only in the vectors.

## Pairs

| Size | Size pair `(a, b)` | Raw at `p = 0.5` | 95 % interval of `a`, `b` | Own groups `(a, b)` |
|---|---|---|---|---|
| m | (8.1176, −4.1208) | 0.508 | [7.881, 8.369], [−4.263, −3.984] | body (8.6158, −4.3577), feet (8.7918, −3.9831) |
| l-256 | (8.2948, −4.3772) | 0.528 | [8.019, 8.562], [−4.533, −4.212] | body (8.6926, −4.5592), feet (9.1933, −4.3199) |
| x-256 | (8.0613, −4.2109) | 0.522 | [7.823, 8.270], [−4.349, −4.077] | body (7.9494, −4.0804), feet (7.857, −3.8762) |
| l-384 | (1.111, −3.161) | 2.845 | [1.058, 1.169], [−3.339, −2.993] | body (1.4181, −4.0784), feet (1.3327, −3.8127) |
| x-384 | (0.8944, −4.653) | 5.202 | [0.867, 0.922], [−4.805, −4.486] | body (0.8629, −4.4277), feet (1.0674, −5.2791), left_hand and right_hand (1.0031, −5.623) |

The intervals come from 500 image resamples of the fit split (seed 0).

## ECE on the check split, before and after the group rule

Each cell is "size pair → final map". A cell with one value is a group that keeps the size pair.

| Size | Size level | body | feet | face | hands |
|---|---|---|---|---|---|
| m | 0.0089 → 0.0063 | 0.0212 → 0.0186 | 0.0960 → 0.0241 | 0.0078 | 0.0093 |
| l-256 | 0.0099 → 0.0071 | 0.0221 → 0.0193 | 0.1036 → 0.0197 | 0.0110 | 0.0148 |
| x-256 | 0.0098 → 0.0091 | 0.0272 → 0.0241 | 0.0447 → 0.0195 | 0.0063 | 0.0164 |
| l-384 | 0.0306 → 0.0230 | 0.0695 → 0.0479 | 0.0446 → 0.0237 | 0.0123 | 0.0188 |
| x-384 | 0.0129 → 0.0118 | 0.0304 → 0.0274 | 0.0706 → 0.0197 | 0.0107 | 0.0239 → 0.0119 |

Precision and recall at `p = 0.5` (final map): m 0.903 / 0.963, l-256 0.906 / 0.970, x-256 0.905 /
0.968, l-384 0.914 / 0.967, x-384 0.915 / 0.971.

## fp16 check

The fp32 map on the fp16 raw scores. Limits: ECE difference within 0.005, p99 `<= 0.02`.

| Size | ECE fp32 | ECE fp16 | p99 \|p16 − p32\| | max | Missing-state changes | Result |
|---|---|---|---|---|---|---|
| m | 0.0063 | 0.0062 | 0.0041 | 0.027 | 0 | pass |
| l-256 | 0.0071 | 0.0069 | 0.0034 | 0.033 | 0 | pass |
| x-256 | 0.0091 | 0.0088 | 0.0040 | 0.051 | 0 | pass |
| l-384 | 0.0230 | 0.0230 | 0.0037 | 0.041 | 0 | pass |
| x-384 | 0.0118 | 0.0119 | 0.0086 | 0.112 | 0 | pass |

## One pair for more than one size (information only)

- One pair for all five sizes ((0.2173, 0.9216), no groups): check ECE m 0.184, l-256 0.180, x-256
  0.181, l-384 0.126, x-384 0.129.
- One pair for the three 256x192 sizes ((8.1422, −4.2236), no groups): check ECE m 0.0131, l-256
  0.0088, x-256 0.0109.

## The map in ln(raw) (information only, not proposed)

The same recipe with `p = 1 / (1 + exp(-(a * ln(raw) + b)))` (defined on the fit set, where
`raw > 0`; no bootstrap):

| Size | Size pair | Size level, size pair → final | body | Own groups | Precision / recall | fp16 |
|---|---|---|---|---|---|---|
| m | (4.5708, 3.3636) | 0.0151 → 0.0139 | 0.0141 | feet, hands | 0.899 / 0.969 | pass |
| l-256 | (4.8895, 3.3706) | 0.0141 → 0.0123 | 0.0151 | feet, hands | 0.903 / 0.973 | pass |
| x-256 | (4.6856, 3.3063) | 0.0187 → 0.0156 | 0.0159 | feet, hands | 0.903 / 0.971 | pass |
| l-384 | (4.126, −4.1774) | 0.0100 → 0.0099 | 0.0292 | body, feet | 0.908 / 0.974 | pass |
| x-384 | (5.2188, −8.3773) | 0.0210 → 0.0088 | 0.0135 | body, feet, face, hands | 0.911 / 0.976 | pass |

One ln pair for the three 256x192 sizes ((4.7006, 3.344)): check ECE 0.0134, 0.0167, 0.0192. The ln
map is better at 384x288 and worse at 256x192. Groups with an own pair: 12 (ln) against 11 (raw).

## The ADR-0041 wrist thresholds as mapped values

The raw thresholds of OpenMMLab-Exporter ADR-0041 ("Thresholds") through the body pair of each size:

| Size | `t_recall` | `t_J` | `t_agree` |
|---|---|---|---|
| m | 0.104 | 0.825 | 0.481 |
| l-256 | 0.115 | 0.850 | 0.475 |
| x-256 | 0.132 | 0.844 | 0.312 |
| l-384 | 0.203 | 0.763 | 0.400 |
| x-384 | 0.135 | 0.856 | 0.415 |

The raw `t_J` goes from 0.686 to 7.198. The mapped `t_J` goes from 0.763 to 0.856.

## Host run of the vectors

`onnx_runtime/score_map.py::map_scores` at the commit above gives each `expect` of the 10 numeric
cases of `vectors/post.keypoint.score_map.yaml` within 1e-6. `pipeline/sidecar.py::check_sidecar_score_map`
refuses each invalid map of the validator cases except rule `-4` (the pipeline has no landmark schema;
the rtmw tests check the group names). `tests/test_score_map.py` and `tests/test_rtmw.py` hold these
checks.
