# Change proposal: simcc-score-map

This proposal uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | A logistic score map in each size gives a SimCC keypoint score in `[0, 1]` |
| Slug | `simcc-score-map` |
| Date | 2026-11-16 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `3ca1a596ea71c0969fc8ea960f4c2a41a27777d6` |
| Model, and its `model` bundle ID | RTMW WholeBody, five sizes (`rtmw-wholebody133`): `model-rtmw-wholebody133@openmmlab-exporter` (current version 5) |
| Intake rows with the verdict `near-miss` or `gap` | none: the intake of version 5 has the verdict `describes`. This is a new requirement of the user (2026-11-16), not a row of the intake. |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `new section` (it also changes `common.sizes_and_artifacts`, `post.keypoint.decode.simcc` and `post.keypoint.schema`) |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `post.keypoint.score_map` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `post/keypoint/score-map.md` (new) |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `afd4813040f2b3de3d3345393493918d7e4840f6` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | The SimCC keypoint score has no fixed range. The decode score is `min(peak_x, peak_y)` of the raw output values, with no softmax ("Score range" in `post.keypoint.decode.simcc`). Its scale changes with the size of the same family: on COCO-WholeBody val, the raw score that has a 50 % chance to be a correct point is 0.51 to 0.53 at 256x192 and 2.85 (l-384) and 5.20 (x-384) at 384x288 (part 5). Thus one threshold cannot serve all sizes. The user decided on 2026-11-16 that the keypoint score of the skellytracker result must be a normalised value in `[0, 1]`, defined in the sidecar spec. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | mmpose `mmpose/codecs/utils/post_processing.py` `get_simcc_maximum` applies no softmax, sigmoid or clip to the score (`apply_softmax=False` is the default of `SimCCLabel.decode`), commit `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`); this is the landed evidence of skellytracker ADR-03PH. The dataset sigmas of the target come from mmpose `configs/_base_/datasets/coco_wholebody.py` lines 1139 to 1154 at the same commit ([permalink](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/_base_/datasets/coco_wholebody.py#L1139-L1154)). OpenMMLab-Exporter ADR-0041 measured that the score scale differs by size (its "Thresholds" table: `t_recall` 0.256 at m, 2.974 at x-384) ([permalink](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/efbe0273a6095eac0393824ea0267089c6513a08/decisions/entries/0041-rtmw-wrist-gate.md)). |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided these items on 2026-11-16 (relayed by the skellytracker supervisor session): the score in the result is a normalised value in `[0, 1]`, defined in the sidecar spec and computed by skellytracker; the map is logistic, `score = 1 / (1 + exp(-(a * raw + b)))`, with an optional pair for each keypoint group; the raw score of `post.keypoint.decode.simcc` does not change; the missing rule runs on the raw score before the map; the raw score stays in the result as a second field. User question Z1 of 2026-11-16: the map is a new permitted key of each size, `sizes.<size>.score_map`. User decision of 2026-11-16 on the license: no change to the `license` block ("this is a re-export of an existing model"). |
| Nearest section ID (the `id` in the section file's front matter) | `post.keypoint.decode.simcc` |
| Why the nearest section is wrong | The decode gives the raw score. It has no field for a calibration, and its range is open. A fixed transform in the decode (for example a softmax peak) cannot serve: the upstream visibility softmax saturates (OpenMMLab-Exporter ADR-0041, S7), and the scale differs by size. The pair is a property of the weights of one size, so it cannot be a top-level field: `common.sizes_and_artifacts` allows no other key in a size entry, and the family invariant forbids a size-level override. |
| Measured difference (number, image and script) | With one pair for all five sizes (the pooled fit), the check-split ECE is 0.126 to 0.184 (pair (0.2173, 0.9216)). With one pair for each size and the group rule, it is 0.006 to 0.023 (part 5; COCO-WholeBody v1.0 val, 6352 persons; `decisions/scripts/simcc_score_map_fit.py`). |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes (RTMW WholeBody) |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none |

## 2. Spec change

### 2.1 Sections

New section `post.keypoint.score_map`, file `post/keypoint/score-map.md`. Front matter:

```yaml
---
id: post.keypoint.score_map
title: Keypoint score map
kind: postprocessor
selectors:
  - keypoint.decode.method=simcc
implemented_by:
  validate: skellytracker/core/model_spec/rules.py::check_sidecar
  map: skellytracker/core/detectors/processing/post/keypoint_score_map.py::map_scores
external_impl: []
tests: []
vectors: vectors/post.keypoint.score_map.yaml
status: {spec: draft, validate: planned, map: planned}
---
```

Section map row (`specs/model-sidecar/README.md`, the keypoint table, after `post.keypoint.decode.simcc`):

```text
| `post.keypoint.score_map` | [post/keypoint/score-map.md](post/keypoint/score-map.md) | Keypoint score map |
```

The full text of the new section file is in 2.2 to 2.4 below (headings "Fields", "Behaviour", "Fit procedure", "Validation rules" and "Implementer guidance").

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `common.sizes_and_artifacts` (`common/sizes-and-artifacts.md`) | "Fields", table `sizes` | Add the row: `` `sizes.<name>.score_map` `` \| object \| required by `V-post.keypoint.score_map-1` \| The keypoint score map of one size (Keypoint score map (`post/keypoint/score-map.md`, heading "Fields")). It is a calibration of the weights of the size, not a contract item. |
| `common.sizes_and_artifacts` | "Fields", the paragraph after the table | Replace the first sentence with: "A size entry can contain only `input.shape`, `input.resize.target_size`, `onnx` (with the sub-fields above) and `score_map` (Keypoint score map (`post/keypoint/score-map.md`, heading "Fields"))." Keep the rest of the paragraph. |
| `common.sizes_and_artifacts` | "Fields", **Family invariant** | After "Do not add a size-level override. Make a new family instead (ADR-90CE).", add: "The score map of a size (`sizes.<size>.score_map`) is not an override and not a contract item. It is a calibration of the weights of that size, like its artifacts, so it can differ between the sizes of one family (Keypoint score map (`post/keypoint/score-map.md`, heading "Behaviour"); ADR-<new>)." |
| `common.sizes_and_artifacts` | "Fields", the table "Contract part / Where it lives" | Add `score_map` to the per-size row: `` `input.shape`, `input.resize.target_size`, `onnx.precision_artifacts`, `onnx.output_shapes`, `score_map` `` \| per size (`sizes.<size>`). |
| `common.sizes_and_artifacts` | "Validation rules", `V-common.sizes_and_artifacts-3` | Change to: "A size entry must contain only `input.shape`, `input.resize.target_size`, `onnx` and `score_map`." |
| `post.keypoint.decode.simcc` (`post/keypoint/decode-simcc.md`) | "Behaviour", the item "Score range" | Add the sentence: "The host maps the raw score to `[0, 1]` with the score map of the size (Keypoint score map (`post/keypoint/score-map.md`, heading "Behaviour")). The decode output keeps the raw score." |
| `post.keypoint.schema` (`post/keypoint/schema.md`) | "Decoded keypoints" | After "A host compares the keypoint scores with its thresholds after this rule", add: "When the size has a `score_map`, the host maps the score of each keypoint that is not missing after this rule (Keypoint score map (`post/keypoint/score-map.md`, heading "Behaviour")). A missing keypoint keeps the score `0`. The host compares the mapped score with its thresholds. The raw score stays available. The score of a derived point is the minimum of the mapped scores of its sources." |
| `specs/model-sidecar/README.md` | Section map, keypoint table; validation index | Add the section row (above) and the line `- [Keypoint score map](post/keypoint/score-map.md#validation-rules)` after the SimCC decode line. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" | Add row 52 (2.6). |
| ADR-90CE (skellytracker root log) | Decision, the family invariant and the size-entry rule | A new skellytracker entry changes the rule of ADR-90CE: a size entry also allows `score_map`, and the score map is not a size-level override. The entry that lands this proposal is that new entry. |

Not changed: the `role` values, the `semantic` values, the resize methods, the storage layout (`format.file_layout`) and the landmark schema registry. `common.license` does not change (user decision of 2026-11-16).

### 2.2 Fields table

#### `sizes.<size>.score_map`

| Field | Type | Required | Description |
|---|---|---|---|
| `sizes.<size>.score_map` | object | yes, in each size, when `keypoint.decode.method` is `simcc` (`V-post.keypoint.score_map-1`); not allowed otherwise (`V-post.keypoint.score_map-6`) | The map of the raw keypoint score of this size to `[0, 1]`. |
| `sizes.<size>.score_map.method` | enum | yes | `logistic`. |
| `sizes.<size>.score_map.a` | number | yes | The slope. A finite number `> 0`. |
| `sizes.<size>.score_map.b` | number | yes | The offset. A finite number. |
| `sizes.<size>.score_map.groups` | object | no | A pair for some groups of the landmark schema: `groups.<group>: {a, b}`. Each key is a group name of the schema that `keypoint.landmark_schema` names. A keypoint of a group that is not in `groups` uses `a` and `b` of the size. |
| `sizes.<size>.score_map.fit` | object | no | Traceability of the numbers: `dataset`, `split` and `recipe`, each a non-empty string. `recipe` names the version of the fit procedure, for example `score-map-fit-v1`. The host does not read it. |

Example (YAML excerpt of one size):

```yaml
sizes:
  m:
    input: {...}
    onnx: {...}
    score_map:
      method: logistic
      a: 8.1176
      b: -4.1208
      groups:
        face: {a: 11.74, b: -7.617}
      fit: {dataset: COCO-WholeBody v1.0, split: val, recipe: score-map-fit-v1}
```

### 2.3 Behaviour

```text
For each crop n and each keypoint k of a size with a score_map:
  raw    = the decode score of k (post.keypoint.decode.simcc), as float32
  g      = the landmark-schema group of k
  (a, b) = score_map.groups[g]          when groups has the key g
           (score_map.a, score_map.b)   otherwise
  missing = raw is NaN or raw <= 0      (the rule of "Decoded keypoints" in post.keypoint.schema)
  score  = 0                            when missing
           1 / (1 + exp(-(a * raw + b)))  otherwise, in float64, then stored as float32
```

- The map is the last step of the keypoint decode. It runs after the unprojection and after the missing rule. It does not change which keypoints are missing, and it does not change a position.
- The host keeps the raw score of each keypoint with the mapped score.
- The map is monotonic: `a > 0`, so a higher raw score gives a mapped score that is higher or equal.
- Range: the mapped score is in the closed range `[0, 1]`. The logistic function gives this range, so the host applies no clamp. In float32 a score can round to exactly `0.0` or `1.0`. Both values are valid.
- A missing keypoint has the score `0.0` exactly. The map does not run on it. This is the current rule of "Decoded keypoints" (`post.keypoint.schema`): a missing keypoint gets the score `0`. The rule does not change.
- NaN: a NaN raw score is missing, so its score is `0`. inf: `raw = +inf` gives `1`. `raw = -inf` is `<= 0`, so it is missing. Overflow: the host must compute the map without overflow, for example as `0.5 * (1 + tanh(z / 2))`, or with `z` limited before `exp`. A very large `z = a * raw + b` gives `1.0` and a very small `z` gives `0.0`, never NaN or inf, and never a value that depends on a floating-point warning. Tie: out of scope (the map has no comparison except `raw <= 0`). Empty input: a crop count of 0 gives an empty result.
- The score map of a size applies to each precision of that size. A writer must check that the pair of the fp32 artifact also serves the fp16 artifact ("Fit procedure", step 9).
- The mapped score estimates the probability that the keypoint is within the "correct" radius of the fit procedure (an OKS term `>= 0.5`). Two sidecars that use the same recipe give comparable scores.

#### Fit procedure

A writer must make the numbers with this procedure. `fit.recipe` names its version. This text is version `score-map-fit-v1`.

1. Data. Use a labelled validation set of the landmark schema that the weights did not train on. Use the dataset sigmas of the schema (for `COCO_WholeBody`: mmpose v1.3.2 `configs/_base_/datasets/coco_wholebody.py`, `sigmas`). Use each person with `iscrowd` 0, at least one labelled keypoint, and a box with width `> 1` and height `> 1`.
2. Crop. Use the ground-truth person box, the sidecar input path of the size (the resize, the normalization), the fp32 artifact, and the decode and unprojection of the sidecar. Use no flip test.
3. Fit set. A keypoint is in the fit set when its raw score is finite and `> 0`, and its part is labelled for the person. For `COCO_WholeBody`: the `body` points always; the `feet`, `face`, `left_hand` and `right_hand` points only when `foot_valid`, `face_valid`, `lefthand_valid` and `righthand_valid` are true.
4. Target. A point of the fit set is positive when its ground-truth visibility `v > 0` and its OKS term `exp(-d^2 / (2 * area * (2 * sigma_k)^2)) >= 0.5`. `d` is the distance in source pixels between the decoded point and the ground-truth point, and `area` is the annotation area. Each other point of the fit set is negative.
5. Split. The persons of the images with an even `image_id` are the fit split. The persons of the images with an odd `image_id` are the check split.
6. Fit. Fit `p = 1 / (1 + exp(-(a * raw + b)))` by maximum likelihood, with no regularisation, on the fit split: first on all points of the fit set (the size pair), then on each group (the group pairs). A writer can pool groups that are mirror images (for example `left_hand` and `right_hand`) and give the same pair to each. Round `a` and `b` to 4 decimal places.
7. ECE. Compute the expected calibration error on the check split with the rounded numbers: 15 bins of equal width on `[0, 1]`; the bin of `p` is `min(floor(15 * p), 14)`; `ECE = sum over the bins of (n_bin / n) * |mean(y) - mean(p)|`.
8. Groups. A group gets its own pair in `groups` when the ECE of the size pair on the check split of that group is `> 0.02`. A group with no point in the fit split uses the size pair.
9. fp16. Apply the fp32 map to the raw scores of the fp16 artifact. The check-split ECE of fp16 must be within 0.005 of the fp32 value, and the 99th percentile of `|p_fp16 - p_fp32|` over the points that are in the fit set of both must be `<= 0.02`. If a size fails, the writer must not publish the map for that size: the fit procedure has no second pair for a precision.
10. Batch. A batch variant of an artifact needs no check: it is the same graph with a fixed batch axis (`common.batch_conversion`).

### 2.4 Validation rules

- [ ] `V-post.keypoint.score_map-1` When `keypoint.decode.method` is `simcc`, each size must have `score_map`.
- [ ] `V-post.keypoint.score_map-2` `score_map` must have `method`, `a` and `b`, and can have `groups` and `fit`. It must have no other key. `method` must be `logistic`.
- [ ] `V-post.keypoint.score_map-3` `a` must be a finite number `> 0`. `b` must be a finite number. This applies to the size pair and to each pair in `groups`. A boolean is not a number.
- [ ] `V-post.keypoint.score_map-4` `groups` must be a non-empty mapping. Each key must be a group name of the landmark schema that `keypoint.landmark_schema` names. Each value must have exactly the keys `a` and `b`.
- [ ] `V-post.keypoint.score_map-5` `fit` must have exactly the keys `dataset`, `split` and `recipe`. Each value must be a non-empty string.
- [ ] `V-post.keypoint.score_map-6` A size must not have `score_map` unless `keypoint.decode.method` is `simcc`.

Changed rule: `V-common.sizes_and_artifacts-3` (2.1). Unchanged rules: `V-post.keypoint.decode.simcc` has no rule of its own; `V-post.keypoint.schema-1` to `-11` do not read the size entry.

### 2.5 Selectors

`keypoint.decode.method=simcc` (the size entry gives the map; the section applies to each size).

### 2.6 Changelog row

```text
| 52 | Keypoint schema, sizes | New section `post.keypoint.score_map`: each size of a `simcc` model has `sizes.<size>.score_map`, a logistic map `1 / (1 + exp(-(a * raw + b)))` of the raw decode score to `[0, 1]`, with an optional pair for each landmark-schema group and an optional `fit` record. A missing keypoint keeps the score 0. A size entry allows `score_map`; it is a calibration of the weights of the size, not an override. The fit procedure `score-map-fit-v1` gives the numbers. | user decisions 2026-11-16 (logistic map; Z1: per size): RTMW (OpenMMLab-Exporter ADR-Q7GS) | [Keypoint score map](post/keypoint/score-map.md#behaviour) |
```

#### Implementer guidance (text of the new section)

- The landmark schema gives the group of each keypoint: the group `k` holds the points from the sum of the counts of groups 0 to `k - 1` ("Landmark schema", `post.keypoint.landmark_schema`).
- Compute `1 / (1 + exp(-z))` in a form that does not overflow, for example `0.5 * (1 + tanh(z / 2))`.
- The result field names of the mapped score and of the raw score are a matter of the pipeline spec (`specs/pipeline/outputs.md`, the keypoint `score` field). Today it says "the decoded score of the sidecar, with no mapping". A pipeline follow-up must change it (part 7).

### 2.7 Known limits and items for the user

- At l-384, the logistic map in raw does not fit the `body` group well. Its check ECE is 0.070 with the size pair and 0.048 with its own pair. The size-level ECE with groups is 0.023. The same recipe with `a * ln(raw) + b` gives 0.029 for that group and 0.010 at size level, but it is worse at 256x192 (0.012 to 0.016 against 0.006 to 0.009). `evidence.md` has the table. The proposal keeps the decided map (logistic in raw).
- For the user to confirm at the landing: `roi_source.score_gate` (the refiner proposal of MediaPipe-Exporter) reads the mapped score, so each threshold in a sidecar is a mapped value. The ADR-0041 wrist thresholds as mapped values are in `evidence.md`.
- The fit uses ground-truth boxes. A person detector changes the crops, so the score of a detector crop can be less well calibrated.

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/post_keypoint_score_map.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_keypoint_score_map.py` |
| Functions (one for each algorithm) | `check_pair` (rule `-3` of a pair), `point_pairs` (the pair of each keypoint), `logistic`, `map_scores` (the missing rule and the map), `run` (one vector case) |

`common.sizes_and_artifacts`, `post.keypoint.decode.simcc` and `post.keypoint.schema` change only by a field row, a rule that names the new key and sentences that tell where the map applies. No algorithm of these sections changes, so this bundle has no module for them ("Full section" in `reference-implementations.md`; the Payload table of `hand-over.md`). The module has no `inverse`: the map changes no coordinate.

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/post.keypoint.score_map.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/post.keypoint.score_map.yaml` (new) |
| `verified_against` | `unverified`: the OpenMMLab-Exporter host function `onnx_runtime/score_map.py::map_scores` gives the same result for each of the 10 numeric cases (`tests/test_score_map.py::test_map_scores_vectors`, at the commit of the header), but the same exporter wrote both, so it is not independent. |
| Cases that replace a current case | none (new file) |

The file has 10 numeric run-time cases (the size pair, one and two group pairs, the strict `raw > 0`, a negative raw, NaN, `+inf` and `-inf`, saturation, the float32 cast of raw, two crops), one refused run-time case (`no-rule`: no `point_groups` for a map with groups) and 10 data-only validator cases (`function: none`) for the rules `-1` to `-6`.

## 5. Parity evidence

The map is a new host step with no upstream counterpart: mmpose gives the raw score (ADR-03PH). Thus the parity of this proposal has two parts: (a) the raw score of the sidecar path is the landed SimCC parity (OpenMMLab-Exporter ADR-VB67 and ADR-P94S; the ONNX files are byte-identical to the files of `model-rtmw-wholebody133` version 5), and (b) the fit procedure of 2.3 runs on the real model and its gates pass. Part (b) is in `evidence.md` with the tables of each size.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | Pass gates, set in the fit script before the run: the group rule (ECE of the size pair `> 0.02` on a group: own pair), the fp16 check (ECE within 0.005, p99 `<= 0.02`). Control (the supervisor session, 2026-11-16): stop and report when a size has an ECE `> 0.03` at size level and with groups. |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO-WholeBody v1.0 val (`coco_wholebody_val_v1.0.json`, SHA-256 `f8272e9c12f3a42457033ebc75da1167546edf1be5e2ffaf586d6ee97541ff6e`) on COCO val2017: 6352 persons (fit split 3232, check split 3120). Branches: the size pair, the group pairs, the missing rule (`raw <= 0`: 0 (no valid point has a raw score `<= 0`; the vectors cover the branch) fit-set candidates at m). |
| Upstream reference: library, version, config and command | mmpose v1.3.2 raw score (ADR-VB67: 0 of 11160240 decode values differ). The map has no upstream. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | ADR-VB67 and ADR-P94S (the same ONNX files). |
| Preprocessed input: maximum absolute difference for each image | ADR-P94S (path A of `decisions/scripts/rtmw_parity_vocabulary.py`; the fit uses the same host functions). |
| Row count for each image: sidecar path and upstream | 1 crop for each GT person (top-down). |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | The mapped keypoint score: check-split ECE for each size and each group, before and after the group rule, and the fp16 check (`evidence.md`). |
| Result (`pass`, `fail` or `to run`) | `pass`: each size has its map; each size passes the fp16 check; no size trips the control (size-level ECE with groups: 0.0063, 0.0071, 0.0091, 0.0230, 0.0118) |
| Script path in the exporter repo | `decisions/scripts/simcc_score_map_measure.py` (GPU, the sidecar path) and `decisions/scripts/simcc_score_map_fit.py` (the fit procedure) |
| Exporter commit of the script | `3ca1a596ea71c0969fc8ea960f4c2a41a27777d6` |
| Command | `uv run python decisions/scripts/simcc_score_map_measure.py --out <work> --sidecar <v5 sidecar> --wholebody-ann ../_datasets/coco_wholebody/annotations/coco_wholebody_val_v1.0.json --images ../_datasets/coco_data/coco_val2017/coco/images/val2017`, then `uv run python decisions/scripts/simcc_score_map_fit.py --work <work> --out <work>/fit.json` |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | New module `skellytracker/core/detectors/processing/post/keypoint_score_map.py::map_scores(raw, score_map, point_groups)`, the port of the reference module. |
| Dispatch point | `skellytracker/core/detectors/generic/keypoint_detector.py`, the `detect` method: after `mark_missing(source, decoded["scores"])` and before `derived_points(...)`, map `scores` with `self.sidecar.sizes[self.size].score_map` and the groups of `keypoint.landmark_schema`. Keep the raw scores beside the mapped scores in `KeypointDetections`. `derived_points` then takes the mapped scores. |
| Validator changes (`model.py`, with rule IDs) | `skellytracker/core/model_spec/model.py`: `SizeSpec` gets `score_map: ScoreMapSpec | None` (`method`, `a`, `b`, `groups`, `fit`; rules `-2`, `-3`, `-5`). `skellytracker/core/model_spec/rules.py::check_sidecar`: rules `-1` and `-6` (the decode method against each size), `-4` (the group names against the landmark schema registry `skellytracker/core/model_zoo/landmark_schemas/`), and the changed `V-common.sizes_and_artifacts-3`. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | The vectors of part 4; `skellytracker/tests/sidecar/test_rtmw_sidecar.py`: the landed RTMW example validates with `score_map` in each size, and a mapped score of a golden crop. |
| Existing code that the change touches | `keypoint_detector.py` (`detect`, `KeypointDetections`), `model.py` (`SizeSpec`), `rules.py` (`check_sidecar`), the result API of the pipeline (`specs/pipeline/outputs.md` follow-up, part 7). |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` (5 sizes) | new fields: `sizes.<size>.score_map` in each size (the numbers of `evidence.md`); `source.version` becomes `0.4.0`; the ONNX files and every other field stay byte-identical to version 5 | `onnx_runtime/score_map.py::map_scores` (new); `pipeline/sidecar.py::check_sidecar_score_map` (rules `-1`, `-2`, `-3`, `-5`, `-6`) |
| OpenMMLab-Exporter | `rtmpose-halpe26`, `dwpose-wholebody133-ubody` (no sidecar yet, ADR-0050) | they need a fit before their sidecars can land (`V-post.keypoint.score_map-1`) | the same host step |
| skellytracker pipeline spec | `specs/pipeline/outputs.md`, keypoint `score` | follow-up: `score` becomes the mapped score; a new field (proposed name `raw_score`, `(I, P)`) keeps the raw decode score, so MMPose parity stays testable | not an exporter change |

**Reference examples that the change makes invalid.**

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit`, `needs-export` or `removed (user ruling)`) | Edit text |
|---|---|---|---|
| `detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml` | `V-post.keypoint.score_map-1` | `needs-export` | The numbers come from a fit on the model, not from the change or the graph. The candidate example of this bundle has them. |

No other example uses `keypoint.decode.method: simcc` (a search of `specs/model-sidecar/examples/` at the commit of the header).

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | `example/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml` |
| Writer code (file, function and commit) | `rtmw/sidecar.py::build_sidecar` with `rtmw/score_map.py::score_map_block`, through `pipeline/handover.py`, at `3ca1a596ea71c0969fc8ea960f4c2a41a27777d6` |
| `sidecar_refs.py --check` result | `ok` |

Difference of the candidate against the example of `model-rtmw-wholebody133` version 5: the five `sizes.<size>.score_map` blocks are new, and `source.version` is `0.4.0` in place of `0.3.0` (OpenMMLab-Exporter ADR-C102). Each other line is the same (`evidence.md`, "What changed against `model-rtmw-wholebody133` version 5").

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep `post.keypoint.decode.simcc` as it is (raw score, no range) | The user requires a normalised score. One raw threshold cannot serve the sizes of one family. | part 1; OpenMMLab-Exporter ADR-0041 "Thresholds" |
| `keypoint.decode.score_map.sizes.<size>` at the top level, keyed by size name (option 2) | Rejected by the user (question Z1, 2026-11-16). It puts per-weights numbers in the shared contract and needs a cross-check of the size names. Its cost if the user changes the choice at landing: move the same block (`method`, `a`, `b`, `groups`, `fit`) under `keypoint.decode.score_map.sizes`, and change rules `-1` and `-6`. | user, question Z1 of 2026-11-16 |
| One family for each size | The contract of the sizes is the same. Five families would repeat every other field. | `common.sizes_and_artifacts`, Family invariant |
| One pair for all sizes of the family | The check-split ECE is 0.126 to 0.184 (pair (0.2173, 0.9216)), against 0.006 to 0.023 with a pair for each size. | `evidence.md` |
| A softmax of the SimCC output (the upstream visibility) | It saturates and ranks worse than the raw score. | OpenMMLab-Exporter ADR-0041, S4 and S7 |
| Isotonic regression or a lookup table | More numbers in each size, and no closed form. The logistic map meets the ECE gate (part 5). | `evidence.md` |
| Detector boxes in the fit | The result then depends on the detector, and two exporters cannot compare. | 2.3, Fit procedure step 2 |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal. n/a: the current intake (version 5) has the verdict `describes`. The next version of `model-rtmw-wholebody133` names this bundle in `related`.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 2 gives the behaviour of each new step on NaN, on inf, on a tie and on an empty input, or `out of scope`.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Each case with a partial input in part 4 names in its `note` the rules that it checks.
- [x] Part 5 gives the numbers, the script path and the commit.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] Each citation of upstream code or of the code of another repo is a permalink with a full 40-character SHA.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
