# Change proposal: simcc-score-rule

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | The SimCC keypoint score, the tie rule and the rule for a score `<= 0` (2D) |
| Slug | `simcc-score-rule` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `c2e610e91fee0a961032e12737ff9147697a7e53` |
| Model, and its `model` bundle ID | `rtmw-wholebody133`, `model-rtmw-wholebody133@openmmlab-exporter` |
| Intake rows with the verdict `near-miss` or `gap` | K8 (keypoint score), `near-miss` |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `post.pose.decode.simcc` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/post/pose-decode-simcc.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of the spec log has two entries, skellytracker ADR-3S5G (`pre.resize.affine_person_crop`) and skellytracker ADR-50BW (`common.batch_conversion`). Neither covers `post.pose.decode.simcc`. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `b065f6e6850686b65bcd08ca944116d739aa62de` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | The SimCC decode of mmpose v1.3.2. (1) The bin of each axis is the argmax of the raw output; a tie gives the lowest bin. (2) The score is the smaller of the two raw peaks of `simcc_x` and `simcc_y`. No softmax comes first. (3) When the score is `<= 0`, each axis of the keypoint gets the bin `-1`, before the scale. (4) The pixel of bin `b` is `b / simcc_split_ratio`, with no half-bin offset. The section is 2D only (skellytracker ADR-9HBB), so these four steps are the full section. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`). (1) to (3): [`mmpose/codecs/utils/post_processing.py:41-44`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L41-L44) (`apply_softmax: bool = False`), [`:90-99`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/utils/post_processing.py#L90-L99) (`np.argmax`, `np.amax`, `mask = max_val_x > max_val_y`, `locs[vals <= 0.] = -1`); [`mmpose/codecs/simcc_label.py:174`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/simcc_label.py#L174) (no softmax). (4): [`mmpose/codecs/simcc_label.py:191`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/codecs/simcc_label.py#L191) (`keypoints /= self.simcc_split_ratio`, after the `-1`); RTMW codec [`configs/wholebody_2d_keypoint/rtmpose/cocktail14/rtmw-m_8xb1024-270e_cocktail14-256x192.py:47-53`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/configs/wholebody_2d_keypoint/rtmpose/cocktail14/rtmw-m_8xb1024-270e_cocktail14-256x192.py#L47-L53) (`simcc_split_ratio=2.0`, `use_dark=False`). The `decode_visibility` branch keeps the first value as the score: [`mmpose/models/heads/base_head.py:81-86`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/mmpose/models/heads/base_head.py#L81-L86). |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided on 2026-11-06 that row K8 of the RTMW intake needs this proposal. The user decided on 2026-11-06 that the proposal covers only the 2D decode: no model of this exporter has a `simcc_z` output. skellytracker ADR-9HBB then made the section 2D only, so this decision agrees with the spec. |
| Nearest section ID (the `id` in the section file's front matter) | `post.pose.decode.simcc` |
| Why the nearest section is wrong | Behaviour says "The location of each keypoint is the argmax bin. Its score is the max value." SimCC has two peaks for each keypoint. The text does not say how the two peaks combine, or if a softmax comes first. It has no tie rule and no rule for a score `<= 0`. The spec itself names this defect ("Spec defects", the SimCC item, in `specs/model-sidecar/decisions/open-work.md`). The skellytracker host takes the mean of the two softmax peaks, so a keypoint threshold does not transfer between hosts. |
| Measured difference (number, image and script) | COCO val2017, all 6352 non-crowd GT persons with keypoints, GT boxes, flip test off, body OKS AP (17 points). RTMW-m 256x192: upstream 0.7477; min of the raw peaks (this proposal) 0.7477; mean of the raw peaks (rtmlib) 0.7461; mean of the softmax peaks (skellytracker today) 0.6560. RTMW-x 384x288: 0.7953, 0.7952, 0.7951, 0.7218. The AR of the four rules is the same within 0.0003, because the bins are the same. Script: OpenMMLab-Exporter `notes/decisions/scripts/simcc_score_rule_parity.py` at [`16b06c10986d2010989b101a13d56cbfebbd6748`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/16b06c10986d2010989b101a13d56cbfebbd6748/notes/decisions/scripts/simcc_score_rule_parity.py) ([OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/d9704753a22792c32a1d3018a0c9e9ea2d279d71/decisions/entries/0053-pose-sidecar-parity-runs.md)). `evidence.md` gives the files and their hashes. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes (OpenMMLab-Exporter: RTMW) |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The row `score_activation: softmax` is about detection scores. The row of the 3D SimCC decode (change 36, skellytracker ADR-9HBB) is about a 3D model. This proposal does not add a 3D decode. |

## 2. Spec change

The relative links of the proposed text resolve from the record path `specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the section file (an editorial fix).

### 2.1 Sections

Changed section `post.pose.decode.simcc`, title "SimCC decode", file
`specs/model-sidecar/post/pose-decode-simcc.md`. The section ID, the title, the kind and the
selectors do not change. No section-map row changes.

Front matter: `vectors: vectors/post.pose.decode.simcc.yaml`. The other keys do not change. The
comment of `implemented_by.decode` stays: the package score is still the mean of the two softmax
peaks until the implementation stage.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `post.pose.decode.simcc` | front matter | `vectors` (above). |
| `post.pose.decode.simcc` | Behaviour | Replace the first bullet (the `simcc` bullet) with the text of 2.3. Keep the second bullet ("The SimCC decode is 2D only. ...") unchanged, after the new text. Keep the line `[Shape key](pose-schema.md#shape-key)`. |
| `post.pose.decode.simcc` | Implementer guidance | Replace the first bullet ("The spec says that the SimCC score is the max value. ...") with the bullet of 2.3, "Guidance". Keep the fp16 bullet. |
| `specs/model-sidecar/changelog.md` | Summary of changes | The row of 2.6. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the SimCC item (the item that starts with "SimCC decode says "Its score is the max value"") | The content commit removes the item. |
| `specs/model-sidecar/vectors/post.pose.decode.simcc.yaml` | new file | The cases of part 4. |
| `specs/model-sidecar/reference/post_pose_decode_simcc.py` | new file | The file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `post.unprojection`, `pre.resize.affine_person_crop`, `common.outputs` | | No edit. A keypoint with the bin `-1` goes through the same unprojection. |
| `post.pose.decode.simcc` Fields and Validation rules, `post.pose.schema` | | No edit. The section has no field and no rule of its own. `V-post.pose.schema-7` requires `pose.geometry: 2d` with `method: simcc` (skellytracker ADR-9HBB). |

### 2.2 Fields table

No change. The section has no field of its own.

### 2.3 Behaviour

Replace the first bullet of Behaviour (the `simcc` bullet) with the text below, from the `simcc`
bullet to the bullet of the unprojection. The second bullet of the current text ("The SimCC decode
is 2D only. ...") stays unchanged. It comes after the new text. The text below shows it last.

- `simcc` — one `simcc_x` `(N, K, X_bins)` output and one `simcc_y` `(N, K, Y_bins)` output. The
  host reads the bin counts from the output tensors. For each crop `n` and each keypoint `k`, the
  host does the steps below on the raw values of `simcc_x` and `simcc_y`. The host does not apply a
  softmax.

```text
bin_x  = argmax over b of simcc_x[n, k, b]       (on a tie, the lowest b)
bin_y  = argmax over b of simcc_y[n, k, b]       (on a tie, the lowest b)
peak_x = simcc_x[n, k, bin_x]
peak_y = simcc_y[n, k, bin_y]
score  = peak_y   when peak_x > peak_y
         peak_x   otherwise                      (thus min(peak_x, peak_y))
when score <= 0:
    bin_x = -1, bin_y = -1
x = bin_x * input_width / X_bins
y = bin_y * input_height / Y_bins
```

- The score is a raw output value. It has no fixed range: it can be negative or more than 1.
- A keypoint with a score `<= 0` keeps its score. Its position is `x = -input_width / X_bins` and
  `y = -input_height / Y_bins`. The host unprojects it as each other keypoint.
- Bin `0` gives the position `0`. The decode adds no half-bin offset.
- The decoded keypoints are in the model-input pixels of the crop. The host unprojects them to the
  source image ([Unprojection](../../post/unprojection.md)).
- The SimCC decode is 2D only. `V-post.pose.schema-7` requires `pose.geometry: 2d` with `method: simcc`. A 3D SimCC model adds a new section with its own contract ([ADR-9HBB](../../../../decisions/entries/9HBB-simcc-decode-is-2d-only.md)).

**Guidance** (the new first bullet of Implementer guidance):

- The score is the score of mmpose v1.3.2 `get_simcc_maximum` with `apply_softmax=False`. The
  skellytracker function `get_simcc_maximum` takes the mean of the two softmax peaks. The rtmlib
  function takes the mean of the two raw peaks. On COCO val2017 (6352 GT persons, flip test off),
  RTMW-m gave the body AP 0.7477 with the rule of this section, 0.7461 with the raw mean and 0.6560
  with the softmax mean. The detectors of skellytracker drop a keypoint below
  `confidence_threshold: 0.004`. That value fits only the softmax score. (OpenMMLab-Exporter
  `notes/decisions/scripts/simcc_score_rule_parity.py` at
  `16b06c10986d2010989b101a13d56cbfebbd6748`, OpenMMLab-Exporter ADR-0053; skellytracker
  `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`) and
  `skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py`
  (`confidence_threshold`))

The change has no inverse. The unprojection is the Inverse of the resize method.

### 2.4 Validation rules

No new rule. The section has no rule of its own (skellytracker ADR-9HBB). The rule
`V-post.pose.schema-7` requires `pose.geometry: 2d` with `method: simcc`. It does not change. No
other rule names a value that the change adds or changes.

### 2.5 Selectors

No change: `pose.decode.method=simcc`, `outputs[].semantic=simcc_x` and
`outputs[].semantic=simcc_y`.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Pose | The SimCC decode gives its steps: the argmax of each axis on the raw values (a tie takes the lowest bin), the score `min(peak_x, peak_y)` with no softmax, the bin `-1` on each axis for a score `<= 0`, and the bin scale with no offset (2D). | RTMW (mmpose `get_simcc_maximum`) | [SimCC decode](../../post/pose-decode-simcc.md#behaviour) |

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/post_pose_decode_simcc.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_pose_decode_simcc.py` |
| Functions (one for each algorithm) | `peak` (argmax and peak), `keypoint_score`, `mark_low_scores`, `bin_to_pixel`, `decode`; `run` for the cases |

The file implements the full section. The section is 2D only (skellytracker ADR-9HBB). It imports
no other section. `source commit: none (no host code)`: OpenMMLab-Exporter has no committed host
SimCC decode. The parity run of part 5 loaded version 1 of this file. Version 2 changes only
docstring lines (part 5).

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/post.pose.decode.simcc.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/post.pose.decode.simcc.yaml` (new file) |
| `verified_against` | `unverified`: no exporter and no skellytracker code implements the proposed rule. |
| Replaced case ids (`--replaces`) | none (new file) |

The cases cover: the score from each axis, equal peaks (the strict `>`), raw values above 1, the tie
of each axis, a score of exactly 0, one negative peak, a small positive score, the bin scale with
bin 0, the bin counts from the tensors, two crops with two keypoints and a tensor refusal
(`no-rule`). All 12 cases are `pose.geometry: 2d`. The tolerance is `1e-6`. `fill` of
skellytracker `tools/make_vectors.py` (at `8351b7f8`) wrote `expect` with the reference file of
part 3 and found no problems. Version 2 changes only one note of the file. The cases and their
`expect` values are byte-identical to version 1.

## 5. Parity evidence

The run of 2026-11-06 with the reference file of version 1 of this bundle ([OpenMMLab-Exporter ADR-VB67](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/18320f4e51660fe0cb9c546441eb9be09d53f339/decisions/entries/VB67-simcc-score-rule-bundle-rerun.md)). It repeats the run of
2026-10-25 and 2026-10-26 ([OpenMMLab-Exporter ADR-0053](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/18320f4e51660fe0cb9c546441eb9be09d53f339/decisions/entries/0053-pose-sidecar-parity-runs.md)), which loaded an earlier draft of the reference file with the
same rule. The gates were written to `gates.json` before the run (2026-11-06T17:23:17Z). They equal
the gates of the first run. `evidence.md` gives the files.

The reference file of version 2 differs from the measured file only in docstring lines. The
measured file (version 1) has the SHA-256
`45f24b0dcabb4ba0f7d17e1325d5989e17f09c0a6d632077bbe221d462777879`. The file of version 2 has the
SHA-256 `ff3c99bf7327e259c024d2483718125f58619fd31d7c34ed0fdf949813d6ca14`. The decode code is
identical: `ast.dump` of the two modules, with the docstrings removed, gives the same text. Thus the
result of OpenMMLab-Exporter ADR-VB67 applies to version 2. No new run was made.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | G1 preprocessed input: max abs difference 0 (parity step 4; pass gate). G2 export error `E` of each crop: recorded, not gated. G3 score: `abs(score_host - score_upstream) <= E` of the crop (a max and a min change by at most the largest change of their inputs; pass gate). G4 bins: where the upstream peak is more than `2 * E` above the second value of its row, the host bin equals the upstream bin (pass gate). G5 position: for equal bins, at most 1e-3 px in source pixels (pass gate). G6 the rule for a score `<= 0`: each upstream keypoint with a score `<= 0` is `-1` on the host, except when `abs(score) <= E` (pass gate). G7 body OKS AP: `abs(AP_host - AP_upstream) <= 0.005` (exporter accuracy gate; pass gate). Decode-only check: the reference decode of the upstream raw outputs equals the upstream decode (pass gate). |
| Test images (paths or dataset IDs), and the branch that each image runs | COCO val2017 person instances (2346 images, 6352 GT persons) and 18 synthetic boxes (the committed box set `decisions/scripts/pose_parity_boxes.json`). The rule for a score `<= 0` ran on RTMPose Halpe26 (3 keypoints at 256x192, 1 at 384x288). The RTMW runs had no keypoint with a score `<= 0`. The tie branch did not occur on real outputs; the vectors cover it. |
| Upstream reference: library, version, config and command | mmpose v1.3.2, mmengine 0.10.3, torch 2.0.0, in the published exporter image with the tag `df-dcab32049439` ([OpenMMLab-Exporter ADR-F5VE](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/18320f4e51660fe0cb9c546441eb9be09d53f339/decisions/entries/F5VE-docker-image.md)); the upstream RTMW, RTMPose Halpe26 and DWPose configs; `test_cfg.flip_test = False`. Command: the `dump` subcommand (`--device cuda --threads 4`). |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | Max abs difference of `simcc_x` and `simcc_y`, ONNX Runtime 1.31.1 CUDA with TF32 on: RTMW-m 0.0229, RTMW-x-384 3.909. With TF32 off, below 3.6e-3 (first run). |
| Preprocessed input: maximum absolute difference for each image | 0 on each crop of the `reference_crop` path (6370 of 6370 crops bit-equal, each run). The `host_warp` path differs up to 0.1225 because the host OpenCV 5.0.0 and the container OpenCV 4.5.4 warp the same `M` differently. The container reference crop equals the upstream crop in 6370 of 6370 crops. |
| Row count for each image: sidecar path and upstream | 6370 rows on both sides, each run (one row for each box). |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | Keypoints and scores in source pixels. Decode-only: 0 of 11160240 values differ (2541630 for each RTMW and DWPose run, 496860 for each Halpe26 run). G3, G4, G5 and G6: 0 violations on each of the 6 runs. G7: RTMW-m delta AP +3.2e-5, RTMW-x-384 -7.1e-5; all 6 runs within 7.9e-4 on both host paths. |
| Result (`pass`, `fail` or `to run`) | `pass` (6 of 6 runs), with `reference/post_pose_decode_simcc.py` of version 1 of this bundle (SHA-256 `45f24b0dcabb4ba0f7d17e1325d5989e17f09c0a6d632077bbe221d462777879`). |
| Script path in the exporter repo | `decisions/scripts/simcc_score_rule_bundle_rerun.py`. It runs the unchanged scripts of the first run (`simcc_score_rule_parity.py`, `simcc_score_rule_worker.py`, `simcc_score_rule_ap_worker.py`, `pose_parity.py`, `pose_parity_common.py`, `pose_parity_mmpose_worker.py`, `pose_parity_boxes.py`) with an adapter of the bundle file. The other four reference files are those of the first run. |
| Exporter commit of the script | [`438138208691a522f54320961f058e61b60d54a3`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/438138208691a522f54320961f058e61b60d54a3/decisions/scripts/simcc_score_rule_bundle_rerun.py). The run recorded each script as `committed` at this commit. |
| Command | `uv run python decisions/scripts/simcc_score_rule_bundle_rerun.py --reference <bundle file> --references-dir <reference files of the first run> -- gates`, then `dump`, `analyze`, `ap` and `summary` (the usage of the script docstring). Run it with `python -B`, so that no `__pycache__/` folder goes into the payload. |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/simcc_decode.py`: change `get_simcc_maximum` to the steps of 2.3 (no softmax; `np.where(max_x > max_y, max_y, max_x)`; the `-1` rule stays). `decode_simcc` must read the bin scale from the bin counts (`input_width / X_bins`), not from `_SIMCC_SPLIT_RATIO`. This proposal does not change the 3D branch of `simcc_pose_decode` (`is_3d`). Stage M8 of `specs/sidecar-implementation-plan.md` removes the 3D SimCC code of the package (skellytracker ADR-9HBB). |
| Dispatch point | `simcc_pose_decode` (`pose.decode.method: simcc`). No new dispatch. |
| Validator changes (`model.py`, with rule IDs) | none. The change adds no rule. The check of `V-post.pose.schema-7` (`pose.geometry: 2d` with `method: simcc`) is in stage M8 of `specs/sidecar-implementation-plan.md` (skellytracker ADR-9HBB). |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | A test that runs the numeric cases of `vectors/post.pose.decode.simcc.yaml` through `get_simcc_maximum` and `decode_simcc`. A golden test on one RTMW crop with mmpose scores. |
| Existing code that the change touches | `skellytracker/core/detectors/processing/simcc_decode.py` (`get_simcc_maximum`, `decode_simcc`, `simcc_pose_decode`); `skellytracker/core/detectors/keypoint_detectors/rtmpose/rtmpose_preprocessing.py` (a second call of `get_simcc_maximum`); the `confidence_threshold: 0.004` defaults of the RTMPose body, face and hand detectors and of the RTMW detector (a raw score needs another default). |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmw-wholebody133` | none. The sidecar has no new field (`pose.decode: {method: simcc}`). | The host decoder of a later RTMW accuracy pass must use the rule of 2.3. The exporter has no host SimCC decode yet. |
| OpenMMLab-Exporter | `rtmpose-halpe26`, `dwpose-wholebody133-ubody` (no sidecar yet) | none | same as above |

**Reference examples that the change makes invalid.** none. The change adds no field and no rule.
The example `detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` has
`pose.decode: {method: simcc}`. It stays valid. Its scores now have the meaning of 2.3.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| none | | | |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none |
| Writer code (file, function and commit) | none (the sidecar does not change) |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: "Its score is the max value", with the host free to choose. | Three hosts use three rules. The body AP of RTMW-m moves from 0.7477 to 0.6560 with the softmax mean. | Part 1 |
| The mean of the two softmax peaks (skellytracker today). | It is not the upstream score. Its scale is different, so the mmpose keypoint threshold 0.2 of the instance score does not transfer. | Part 1, AP 0.6560 and 0.7218 |
| The mean of the two raw peaks (rtmlib). | It is not the upstream score. AP 0.7461 against 0.7477. | Part 1 |
| `min(peak_x, peak_y)` with no rule for a score `<= 0`. | mmpose sets the bin `-1`. A host without the rule gives another position for those keypoints (3 keypoints in the Halpe26 run). | Part 5, G6 |
| Also set the 3D steps (`simcc_z`) in this proposal. | skellytracker ADR-9HBB made the section 2D only. A 3D SimCC model adds a new section with its own contract. No model of this exporter has a `simcc_z` output, so no parity run can test 3D steps. | Part 1; skellytracker ADR-9HBB |
| The visibility of `decode_visibility=True` as the score. | The head keeps the first value as the score. The visibility is a separate output, out of scope of this proposal. | `base_head.py:81-86` |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal: the RTMW intake (`payload/intake.md` of `model-rtmw-wholebody133@openmmlab-exporter`) names `proposal-simcc-score-rule@openmmlab-exporter` in row K8 and in its proposals table.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter repo.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
