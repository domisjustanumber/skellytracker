---
id: post.keypoint.score_map
title: Keypoint score map
kind: postprocessor
selectors:
  - keypoint.decode.method=simcc
implemented_by:
  validate: skellytracker/core/model_spec/rules.py::check_sidecar
  decode: skellytracker/core/detectors/processing/post/keypoint_score_map.py::map_scores
external_impl: []
tests:
  - skellytracker/tests/model_spec/test_model_validation.py
  - skellytracker/tests/processing/test_postprocess.py
  - skellytracker/tests/detectors/test_generic_detectors.py
vectors: vectors/post.keypoint.score_map.yaml
status: {spec: draft, validate: implemented, decode: implemented}
---

# Keypoint score map

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The score map changes the raw score of a SimCC keypoint to a normalised score in `[0, 1]`. The raw score has no fixed range, and its scale changes with the size of one family ([SimCC decode](decode-simcc.md#behaviour)). The map is a calibration of the weights of one size. Thus each size has its own map ([ADR-F067](../../decisions/entries/F067-simcc-score-map.md)).

## Fields

#### `sizes.<size>.score_map`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sizes.<size>.score_map` | object | yes, in each size, when `keypoint.decode.method` is `simcc` (`V-post.keypoint.score_map-1`); not allowed otherwise (`V-post.keypoint.score_map-6`) | The map of the raw keypoint score of this size to `[0, 1]`. |
| `sizes.<size>.score_map.method` | enum | yes | `logistic`. |
| `sizes.<size>.score_map.a` | number | yes | The slope. A finite number `> 0`. |
| `sizes.<size>.score_map.b` | number | yes | The offset. A finite number. |
| `sizes.<size>.score_map.groups` | object | no | A pair for some groups of the landmark schema: `groups.<group>: {a, b}`. Each key is a group name of the schema that `keypoint.landmark_schema` names ([Landmark schema](landmark-schema.md#fields)). A keypoint of a group that is not in `groups` uses `a` and `b` of the size. |
| `sizes.<size>.score_map.fit` | object | no | Traceability of the numbers: `dataset`, `split` and `recipe`, each a non-empty string. `recipe` names the version of the fit procedure, for example `score-map-fit-v1`. The host does not read it. |
| `sizes.<size>.score_map.fit.dataset` | string | yes, in `fit` | The labelled dataset of the fit. |
| `sizes.<size>.score_map.fit.split` | string | yes, in `fit` | The split of the dataset. |
| `sizes.<size>.score_map.fit.recipe` | string | yes, in `fit` | The version of the fit procedure. |

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

## Behaviour

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
- A missing keypoint has the score `0.0` exactly. The map does not run on it. This is the rule of [Decoded keypoints](schema.md#decoded-keypoints): a missing keypoint gets the score `0`. The rule does not change.
- NaN: a NaN raw score is missing, so its score is `0`. inf: `raw = +inf` gives `1`. `raw = -inf` is `<= 0`, so it is missing. Overflow: the host must compute the map without overflow, for example as `0.5 * (1 + tanh(z / 2))`, or with `z` limited before `exp`. A very large `z = a * raw + b` gives `1.0` and a very small `z` gives `0.0`, never NaN or inf, and never a value that depends on a floating-point warning. Tie: out of scope (the map has no comparison except `raw <= 0`). Empty input: a crop count of 0 gives an empty result.
- The score map of a size applies to each precision of that size. A writer must check that the pair of the fp32 artifact also serves the fp16 artifact ("Fit procedure", step 9).
- The mapped score estimates the probability that the keypoint is within the "correct" radius of the fit procedure (an OKS term `>= 0.5`). Two sidecars that use the same recipe give comparable scores.
- A threshold in a sidecar that reads a keypoint score reads the mapped score ([ADR-F067](../../decisions/entries/F067-simcc-score-map.md)).

### Fit procedure

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
10. Batch. A batch variant of an artifact needs no check: it is the same graph with a fixed batch axis ([Batch conversion](../../common/batch-conversion.md#behaviour)).

## Validation rules

- [ ] `V-post.keypoint.score_map-1` When `keypoint.decode.method` is `simcc`, each size must have `score_map`.
- [ ] `V-post.keypoint.score_map-2` `score_map` must have `method`, `a` and `b`, and can have `groups` and `fit`. It must have no other key. `method` must be `logistic`.
- [ ] `V-post.keypoint.score_map-3` `a` must be a finite number `> 0`. `b` must be a finite number. This applies to the size pair and to each pair in `groups`. A boolean is not a number.
- [ ] `V-post.keypoint.score_map-4` `groups` must be a non-empty mapping. Each key must be a group name of the landmark schema that `keypoint.landmark_schema` names. Each value must have exactly the keys `a` and `b`.
- [ ] `V-post.keypoint.score_map-5` `fit` must have exactly the keys `dataset`, `split` and `recipe`. Each value must be a non-empty string.
- [ ] `V-post.keypoint.score_map-6` A size must not have `score_map` unless `keypoint.decode.method` is `simcc`.

## Implementer guidance

- The landmark schema gives the group of each keypoint: the group `k` holds the points from the sum of the counts of groups 0 to `k - 1` ([Landmark schema](landmark-schema.md#fields)).
- Compute `1 / (1 + exp(-z))` in a form that does not overflow, for example `0.5 * (1 + tanh(z / 2))`.
- The names of the mapped score and of the raw score in the result of a pipeline are a matter of the pipeline spec ([Outputs](../../../pipeline/outputs.md)).
- skellytracker: `map_scores` of `skellytracker/core/detectors/processing/post/keypoint_score_map.py` is a port of the reference module. The generic keypoint detector maps the scores after `mark_missing` and before `derived_points`. `KeypointDetections.scores` holds the mapped scores, and `KeypointDetections.raw_scores` holds the decode scores, so that a parity test with mmpose reads `raw_scores`. `load_sidecar` gives the group of each keypoint from the landmark schema registry (`SidecarModel.point_groups`). A derived point takes its presence from the raw scores, because the mapped score of a present keypoint can be `0.0` in float32. ([`proposal.md`](../../proposals/simcc-score-map/proposal.md#6-skellytracker-implementation-proposal) of the proposal `simcc-score-map`, part 6 (secondary))

## Authoring guidance

- On COCO-WholeBody v1.0 val (6352 persons, ground-truth boxes, no flip test), the raw score with a 50 % chance to be a correct point is 0.51 to 0.53 at 256x192, 2.85 at l-384 and 5.20 at x-384. The check-split ECE of the RTMW sizes is 0.0063 to 0.0230 with one pair for each size and the group rule, and 0.126 to 0.184 with one pair for all five sizes. Each size passes the fp16 check. ([`evidence.md`](../../proposals/simcc-score-map/evidence.md) of the proposal `simcc-score-map` (secondary); OpenMMLab-Exporter `decisions/scripts/simcc_score_map_fit.py` at `3ca1a596ea71c0969fc8ea960f4c2a41a27777d6`)
- At l-384, the logistic map in `raw` does not fit the group `body` well: the check ECE is 0.048 with its own pair. A map in `ln(raw)` gives 0.029 there, and it is worse at 256x192. The spec keeps the logistic map in `raw`. ([`evidence.md`](../../proposals/simcc-score-map/evidence.md) (secondary))
- The fit uses ground-truth boxes. The crops of a person detector can give a score that is less well calibrated. ([`proposal.md`](../../proposals/simcc-score-map/proposal.md#27-known-limits-and-items-for-the-user) of the proposal `simcc-score-map`, part 2.7 (secondary))

## Examples

The example [`rtmw-wholebody133.yaml`](../../examples/detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133.yaml) has a `score_map` in each of its five sizes, with pairs for some groups of `COCO_WholeBody` and a `fit` record.
