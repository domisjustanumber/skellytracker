---
slug: normalize-arithmetic
section: pre.normalize
exporter: OpenMMLab-Exporter
decision: "0043"
state: recorded
---
# Change proposal: normalize-arithmetic

This file is informative. It is not part of the normative spec until a content PR lands its text
in the section files (decision [0036](../../../../decisions/0036-spec-proposals-folder.md)).

**Source.** The OpenMMLab-Exporter file of the proposal `normalize-arithmetic`, at
OpenMMLab-Exporter commit
[`f3aeb47`](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/f3aeb473d3396ee79c4394646a34ed9ef419ecf1),
copied on 2026-10-25. Part 3 also holds the code of the OpenMMLab-Exporter reference file of part 3, copied on the same
date (decision 0036, item 2). The copy changes only the items of decision 0036, item 3. The session wrote
no part.

This file uses ASD-STE100 Simplified Technical English. It follows the change proposal template
(`specs/model-sidecar/templates/change-proposal.md` of the skellytracker repo) and the skill
`propose-sidecar-change`. No skellytracker decision entry covers this property.

## Header

| Field | Value |
|---|---|
| Title | Normalization arithmetic: the reference value, the accuracy rule and the cast to `input.dtype` |
| Slug | `normalize-arithmetic` |
| Date | 2026-10-25 (first written 2026-10-23; changed 2026-10-24 for N1 and the audit, and 2026-10-25 for the recheck at skellytracker `dom/21-move-sidecar-guide`) |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `f3aeb473d3396ee79c4394646a34ed9ef419ecf1` (branch `rtmo-model-id-variant`, not pushed: OpenMMLab-Exporter decision 0050; OpenMMLab-Exporter decision 0042 is commit `1dfec48`; `git status --porcelain` is empty). First written at `d0f4343`, which has the T14 change. Checked again at `f3aeb47` on 2026-10-24: from `d0f4343`, the cited lines of `rtmw/sidecar.py` and `rtmdet_person/sidecar.py` move by +1 (OpenMMLab-Exporter decision 0042), and this file cites the lines at `f3aeb47`. `onnx_runtime/preprocess.py` (unchanged since `eed3361`), `rtmo/sidecar.py`, `onnx_convert/FP16_CONTRACT.md` and `exporter/worker/collect_env.py` are the same at `d0f4343`, at `01d9b3d` and at `f3aeb47`. The first check used `git show d0f4343:<path>`. |
| Model, and its intake file (the untracked intake of `<model>` of OpenMMLab-Exporter (plan facts)) | `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts)), `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)), `rtmw-wholebody133` (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts)), `dwpose-wholebody133-ubody` (the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts)) and `rtmpose-halpe26` (the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)). The five intakes link this proposal: row T10 and the proposal and reference rows (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts); the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts); the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts); the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts); the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)). Both ViTPose families use the ViTAE eval normalization (plan T3, T9; the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; the plan line numbers in this file are as of 2026-10-25). The three mmpose 1.x families use the mmengine float32 form (part 1, row "Upstream evidence"). |
| Intake rows with the verdict `near-miss` or `gap` | Row T10 (normalization) of the five intakes, all `near-miss`. The ViTPose rows (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)) are `near-miss` under the user decision T2 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; plan step 1, item 3, the untracked pose-models plan of OpenMMLab-Exporter (plan facts)). The rows of RTMW, DWPose and Halpe26 (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)) are `near-miss` under the same rule (intake correction of 2026-10-24, secondary): the mmengine float32 form differs from "float64, then one cast to float32" by up to 2.4e-7 (part 1). That form meets the proposed accuracy rule, so these three rows become `exact` after acceptance. |
| Kind (`new section` or `changed section`) | `changed section` |
| Proposed section ID (the `id` in the section file's front matter) | `pre.normalize` |
| Section file | `specs/model-sidecar/pre/normalization.md` |
| Depends on (proposal files that must land first, or `none`) | none |
| Needed by (proposal files that depend on this one, or `none`) | none. Related: `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md` (slug `heatmap-decode-refinement`, reference file: the part 3 code of `specs/model-sidecar/proposals/heatmap-decode-refinement/proposal.md`) and `specs/model-sidecar/proposals/pose-decode-flip-test/proposal.md`. They change other sections. Their parity runs can share the ViTAE container worker of part 5. `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md` (slug `affine-crop-arithmetic`) edits the same sentence of `format/versioning.md:51`. The two proposals share one exception sentence (2.1, row `format.versioning`, in both files). The skellytracker session adds it one time. **Related (merge points; review-readiness audit 2, 2026-10-24).** Other proposals edit the same spec text as this proposal. The content PR that lands second rebases on the first and keeps the edits of both. Line numbers are at skellytracker `dom/21-move-sidecar-guide` (checked 2026-10-25; the cited `specs/` and `tools/` lines are the same as at `dom/18-agents-adr-bootstrap-kit`). From `dom/12-single-working-branch` to `dom/18-agents-adr-bootstrap-kit`, no file of this list under `specs/` or `tools/` changed. The "Open work" list moved from `notes/decisions/README.md` to `notes/decisions/open-work.md` (`dom/14-decision-log-growth`), so the old `README.md:199` is now `open-work.md:168` (line 163 at `dom/18-agents-adr-bootstrap-kit`). `format/versioning.md:51` (the shared exception sentence; add it one time): `affine-crop-arithmetic`; `pre/normalization.md:47-53` ("Behaviour"): `roi-transform-and-source` (MediaPipe-Exporter); skellytracker `notes/decisions/open-work.md:168` ("Spec defects"): `affine-crop-arithmetic`; `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule`, `heatmap-decode-refinement`, `affine-crop-arithmetic`, `model-id-suffix`, `roi-transform-and-source` (MediaPipe-Exporter), `landmark-extra-outputs` (MediaPipe-Exporter), `landmark-depth-divisor` (MediaPipe-Exporter); `tools/make_vectors.py` `BUILDERS` and `tools/tests/test_vectors.py` `CASE_KEYS` (the `function` and `compare` keys; decide the case form one time): `simcc-score-rule`, `heatmap-decode-refinement`, `affine-crop-arithmetic`, `model-id-suffix`, `size-codes`, `keypoint-visibility`. All 13 proposals add a row to "Summary of changes" (row `N`, the next free number at merge time) and a sentence to the `vNEXT` row of the `schema_version` history (`changelog.md:68`). |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The index lists skellytracker decisions 0017 to 0025 with the status `proposed` (`notes/decisions/README.md:36-44`). None of them is about normalization. skellytracker decision 0009 (`imagenet_bgr` meaning) is related. It was accepted, and since 2026-10-24 its status is "absorbed into `pre/normalization.md#legacy-behaviour`". This proposal does not change it. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read | `dom/21-move-sidecar-guide` (checked 2026-10-25; `git status --porcelain` lists only the untracked file `grep.exe.stackdump`, no tracked change). History: first read at `dom/12-single-working-branch`; pinned at `dom/18-agents-adr-bootstrap-kit` on 2026-10-24 (`git status --porcelain` was empty). From `dom/18-agents-adr-bootstrap-kit` to `dom/21-move-sidecar-guide`: the cited spec, tool and package lines are unchanged (`git diff --stat dom/18-agents-adr-bootstrap-kit dom/21-move-sidecar-guide` lists none of `pre/normalization.md`, `common/input.md`, `format/versioning.md`, `specs/model-sidecar/README.md`, `changelog.md`, `vectors/pre.normalize.yaml`, `0009-imagenet-bgr-meaning.md`, `tools/make_vectors.py`, `tools/tests/test_vectors.py`, `image_preprocessing.py` or `model.py`); `notes/decisions/open-work.md` moved by +5 lines from old line 115 (the citations in this file give the `dom/21-move-sidecar-guide` lines); `TRACEABILITY.md` rows 32 and 82 and `templates/model-intake.md` row T10 (line 273) are unchanged. The cited `specs/` lines were checked again at `dom/18-agents-adr-bootstrap-kit` on 2026-10-24: only `exporter-guide.md` changed (one line less after line 445). The cited decision-log lines moved to `notes/decisions/open-work.md`, and `0009-imagenet-bgr-meaning.md` has one more line at its top. Guide citations point to the layout of skellytracker decision 0034 at skellytracker `dom/21-move-sidecar-guide`. The spec text did not change after the pin (only link repairs). |

**Decision of this proposal.** The question was: a normative arithmetic statement, a tolerance, or a
new mode. This proposal gives a normative statement that has two parts: (1) one reference value for
each formula (float64, then one rounding to float32); (2) an accuracy rule (a tolerance) for the
value of a host. It adds no new mode. Part 8 gives the reasons and the numbers. In short:

- a bit-exact rule in float32 cannot describe ViTAE and the exporter host at the same time
  (they differ by up to 4.8e-7);
- a new mode for each upstream order of operations is not necessary, because the effect on the
  model outputs is below the noise of the execution provider (part 1);
- all float32 forms in use agree with the reference value within 0.31 of the proposed bound. float16
  arithmetic is far above it: up to 1011 times the bound in the host order `(p - mean) / std`, and
  up to 1697 times in the ViTAE order `(p / 255 - m) / s`.

**The version scope: every `schema_version` (option B, user decision T21 (3), 2026-10-23; N1,
user decision T23, 2026-10-24).** The heading "Arithmetic" and the rule `V-pre.normalize-3` apply
to every `schema_version`. The reason: no sidecar is deployed yet, and all sidecars will be made
again (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The spec says that `vNEXT` requirements never
apply retroactively (skellytracker `specs/model-sidecar/format/versioning.md:51`; skellytracker decision 0009,
`specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md:15, 39`). The heading adds host requirements, for
example the accuracy rule and "do not calculate in float16". The rule adds a validation
requirement. Thus this proposal adds an exception sentence to `versioning.md:51` (2.1, row
`format.versioning`). The sentence names the heading and the rule. The proposal
`affine-crop-arithmetic` has the same scope and shares the same sentence. The rule
`V-pre.normalize-3` has no **(vNEXT)** mark, because a marked rule applies only at `vNEXT`
(skellytracker `specs/model-sidecar/README.md:99`; 2.4, 2.6). Option A (the heading only at `vNEXT`) and
the rule only at `vNEXT` are rejected alternatives (part 8).

**Decided items (user, plan T23, 2026-10-24).** The version scope is decided (option B). The user
decided N1 to N3 as this proposal recommends:

- N1. `V-pre.normalize-3` applies to every `schema_version`, as the heading "Arithmetic". The
  other choice was the rule only at `vNEXT`. No current sidecar fails the rule at its own
  `schema_version` (part 7, "Check of N1": 23 sidecar files of skellytracker, Ultralytics-Exporter,
  OpenMMLab-Exporter, Roboflow-Exporter and Qualcomm-Exporter). For example, all five skellytracker
  package sidecars declare `dtype: {fp32: float32}` (skellytracker
  `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose-body.yaml:9-10`; the same
  lines in `rtmpose-face.yaml`, `rtmpose-hand.yaml`, `rtmw-wholebody.yaml` and
  `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml`). With the rule at every version,
  the heading defines the cast of every valid sidecar (2.3).
- N2. The bound `1e-6 * max(1, abs(r))` is accepted (part 8, row "A larger bound or a smaller
  one").
- N3. The rule `V-pre.normalize-3` and the correction of the default note stay in this proposal
  (part 8).

The proposal also corrects the note "the RTMPose convention" for the default `imagenet_bgr`
(skellytracker `notes/decisions/open-work.md:125-127`). That note is in the same section. The
correction changes no value. The user keeps it in this proposal (N3).

## 1. Gap

| Item | Value |
|---|---|
| Property | The arithmetic of the ImageNet normalization of ViTPose and ViTPose++. The input is RGB uint8. The upstream divides by 255, then subtracts `mean = [0.485, 0.456, 0.406]` and divides by `std = [0.229, 0.224, 0.225]`. ViTAE does this in float32. easy_ViTPose does it in float64 and then casts to float32. In real numbers this is `imagenet_rgb`, because `0.485 * 255 = 123.675`, `0.456 * 255 = 116.28`, `0.406 * 255 = 103.53`, `0.229 * 255 = 58.395`, `0.224 * 255 = 57.12` and `0.225 * 255 = 57.375` exactly. In float32 the values are not the same. |
| Upstream evidence (file and line, or config key; upstream commit or release) | **ViTAE-Transformer/ViTPose `c050ed29112da7704797cc1a65af0234b525010d`** (the ViTPose++ eval pipeline, plan T3; the base of the 25-point pipeline B2, plan T9): `configs/wholebody/2d_kpt_sview_rgb_img/topdown_heatmap/coco-wholebody/ViTPose_base_wholebody_256x192.py:103-110` (`val_pipeline`: `LoadImageFromFile`, `TopDownAffine`, `ToTensor`, `NormalizeTensor` with `mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`); `ViTPose_small_wholebody_256x192.py:104-110` (the same steps); `configs/body/2d_kpt_sview_rgb_img/topdown_heatmap/coco/ViTPose_small_coco_256x192.py:123-130` (the COCO base of the 25-point configs: the same `ToTensor` and `NormalizeTensor`). `mmpose/datasets/pipelines/loading.py:29, 31, 41-42` (`to_float32=False`, `channel_order='rgb'`: the image stays uint8 RGB). `mmpose/datasets/pipelines/shared_transform.py:21-36` (`ToTensor`: `F.to_tensor(results['img'])`, line 34) and `:40-64` (`NormalizeTensor`: `F.normalize(results['img'], mean=self.mean, std=self.std)`, lines 61-62); `F` is `torchvision.transforms.functional` (line 10). **torchvision v0.10.0** (the release of torch 1.9.0; ViTAE `requirements/runtime.txt:10` gives no version): `torchvision/transforms/functional.py:107, 114-117` (`img.to(dtype=default_float_dtype).div(255)` for a uint8 array: float32 `p / 255`) and `:326-328, 335` (`mean` and `std` become tensors of the dtype of the image, float32; then `tensor.sub_(mean).div_(std)`). **easy_ViTPose `bb98603`** (the inference of the HF models): `easy_ViTPose/inference.py:32-33` (`MEAN`, `STD` as Python lists), `:316` (`cv2.resize(...) / 255`: float64), `:317` (`((img_input - MEAN) / STD)...astype(np.float32)`: float64, then one cast to float32); `:226` (the input is RGB). **mmpose v1.3.2 and mmengine** (the arithmetic of RTMW, DWPose, RTMPose and RTMDet, for comparison): mmpose `mmpose/models/data_preprocessors/data_preprocessor.py:14, 89` (`PoseDataPreprocessor` calls `ImgDataPreprocessor.forward`); mmengine v0.10.3 `mmengine/model/base_model/data_preprocessor.py:227-230` (`mean` and `std` are `torch.tensor(...)` buffers, float32), `:266` (`_batch_input.float()`), `:275` (`(_batch_input - self.mean) / self.std`). v0.10.3 is the mmengine of the exporter image: the source accuracy reports record it (key `environment.packages.mmengine` = `"0.10.3"` in `exports/detectors/object_detectors/rtmdet-person/benchmarks/rtmdet-person-medium_source/rtmdet-person-medium_source.accuracy.torch-cuda.b1.20261021T231118Z-<host>.json`, where `<host>` is the host-name suffix of the run ID (not written here); written by `exporter/worker/collect_env.py:21`; `exports/` is not tracked). The Dockerfile does not pin it (`mmdeploy-convert/Dockerfile.exporter:28-29`: it comes with the base image). v0.10.4 differs from v0.10.3 in this file only in a docstring (line 238). |
| Nearest section ID (the `id` in the section file's front matter) | `pre.normalize` |
| Why the nearest section is wrong | The section gives each mode as a formula: `(pixel - mean) / std` on 0-255 pixels (`pre/normalization.md:43-44`), `pixel / 255.0` (line 42) and `(pixel * scale - mean) / std` (line 45). It does not give the dtype of the arithmetic, the order of the operations, or the dtype of the result (only `none` casts to `input.dtype`, line 41). Thus the section has no exact value for a pixel. A host cannot know if the ViTAE float32 values are `imagenet_rgb`. The exporter guide asks for this detail (`specs/exporter-guide/sidecars/workflow/mapping-hints.md:39-40`), and parity step 4 expects a difference of 0 (`exporter-guide/sidecars/workflow/parity.md:28-32`). The skellytracker decision log lists "the arithmetic precision of the geometry and of the pixel math" as a spec defect (`notes/decisions/open-work.md:161, 168`). Under the user rule T2, a difference that is not 0 makes the row a `near-miss` (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). |
| Measured difference (number, image and script) | **Input values, all 256 byte values for each channel** (scratch script `norm_forms.py`, NumPy 2.5.4 float32 emulation of the upstream steps; torch did not run). The reference value `r` is the exact rational value of the formula, rounded one time to float32. For every byte and every channel it is equal to "float64, then one cast to float32". Against `r`: the exporter host and mmengine form `(float32(p) - float32(mean)) / float32(std)`: max 2.4e-7, at 165 / 103 / 99 bytes (R / G / B). ViTAE `float32(p) / 255`, then `(x - 0.485) / 0.229` in float32: max 4.8e-7, at 133 / 161 / 197 bytes. easy_ViTPose (float64, then float32): 0 at every byte. Spec `custom` with `scale: 0.00392156862745098` in float32: max 7.2e-7. ViTAE against the exporter host form: max 4.8e-7, at 128 / 160 / 195 bytes. easy_ViTPose against the host form: max 2.4e-7, at 165 / 103 / 99 bytes. These numbers agree with plan appendix A.3 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary), which used the host form as the baseline. The emulation assumes that torch divides by 255 with a true division. A CPU-scalar reciprocal (`p * (1/255)`) changes 105 G bytes and gives at most 0.31 of the bound (`norm_forms2.py`). After a cast to float16, all float32 forms give the same float16 value at every byte. float16 arithmetic gives up to 2.2e-3. **Effect on the outputs** (scratch script `norm_sensitivity.py`: the HF ONNX files `vitpose-s-wholebody.onnx` and `vitpose-s-coco_25.onnx`, HF `JunkyByte/easy_ViTPose` `e838052`, not the own export; the first 200 non-crowd COCO val2017 person instances with keypoints; GT boxes; a non-UDP affine crop x 1.25 to 192 x 256; ONNX Runtime 1.31.0 CPU): the ViTAE form against `r` changes the heatmaps by at most 2.8e-6 (wholebody) and 2.1e-6 (25 points). The host form changes them by at most 3.5e-6 and 1.9e-6. No argmax cell changes (0 of 26600 and 0 of 5000). No keypoint of the `default` decode moves. A repeat run of the same input gives 0. **Noise floor of the execution provider** (`norm_provider_noise.py`, the same 200 crops and the same input): CPU against CUDA with TF32 off: 7.2e-6 and 5.4e-6, 0 argmax changes; CPU against CUDA with TF32 on (the evaluation setting of this exporter, `AGENTS.md` section 6): 1.6e-3 and 1.5e-3, 40 and 10 argmax changes. For comparison: the HF ONNX against the ViTAE model on 3 inputs: max 6.0e-7 (the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). The scripts are in the session scratchpad. They are not committed, so the numbers are not evidence. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The table (`changelog.md:38-53`) has no row about normalization or arithmetic precision. |

**Missing primary evidence.** (1) No ONNX file of the two families exists in this exporter yet
(input `missing`, plan section 1). The output numbers above use the HF ONNX files of the same
weights (plan T7 check, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary). (2) The upstream steps were
emulated with NumPy, not run with torch. The torchvision version of the ViTAE environment is not
pinned. Part 5 runs `ToTensor` and `NormalizeTensor` in the ViTAE environment of the exporter image
(plan T12) on every byte value. (3) The Dockerfile does not pin the mmengine version. The untracked
source accuracy reports record it (0.10.3, part 1 row "Upstream evidence"). The mmengine lines above
are from v0.10.3.

## 2. Spec change

### 2.1 Sections

Changed section `pre.normalize`, title "Normalization", file `specs/model-sidecar/pre/normalization.md`.
The section ID, the title, the kind and the selectors do not change. No new field.

Changed front matter (the other keys do not change):

```yaml
changed_in: [vNEXT]
implemented_by:
  validate: skellytracker/core/sidecar/model.py::CustomNormalization  # partial. Nothing checks input.color_format against the normalization mode. Nothing checks V-pre.normalize-3.
  forward: skellytracker/core/detectors/processing/image_preprocessing.py::build_normalization_fn  # partial. imagenet_bgr has only the legacy meaning (specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md). No code reads color_format. The result is float32 for every input.dtype (preprocess_image). The float32 arithmetic meets the accuracy rule.
vectors: vectors/pre.normalize.yaml
status: {spec: stable, validate: partial, forward: partial}
```

No row in the section map changes: the section exists (`specs/model-sidecar/README.md:69`).

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.normalize` (`pre/normalization.md`) | front matter (lines 13-15) | The edit above. |
| `pre.normalize` | "Fields" (line 30) | Replace "The default is `imagenet_bgr` (the RTMPose convention)." with "The default is `imagenet_bgr`. See Behaviour (`#behaviour`)." |
| `pre.normalize` | "Behaviour", the sentence after the mode table (line 47) | Add after it: "Thus `(pixel / 255 - 0.485) / 0.229` is the same formula as `(pixel - 123.675) / 58.395`. The statistics are exact decimal products: `0.485 x 255 = 123.675`." |
| `pre.normalize` | "Behaviour", new sub-heading "Arithmetic" (after line 53, before "**Named mode (preferred):**") | The text of 2.3. |
| `pre.normalize` | "Behaviour", the warning (line 93) | Replace with the warning of 2.3. |
| `pre.normalize` | "Validation rules" (lines 103-108) | Add `V-pre.normalize-3` (2.4). In `V-pre.normalize-1` (line 105), replace "it must have length 3" with "it must be a list of three finite numbers" (2.4). |
| `pre.normalize` | "Legacy behaviour" (lines 110-116) | Add the two rows of 2.6 ("Arithmetic" and `V-pre.normalize-3`). The row `normalization: imagenet_bgr` does not change. |
| `pre.normalize` | "Implementer guidance" (lines 118-125) | Add the bullets of 2.3, "Guidance". |
| `pre.normalize` | "Authoring guidance" (lines 127-142) | Add the bullets of 2.3, "Guidance". |
| `common.input` (`common/input.md`) | "Fields" (line 26, `dtype`) and "Validation rules" (lines 57-63) | No edit. `V-common.input-2` (line 58) still allows `uint8` and `int8`. The new rule limits them to `none`. The "See also" line (line 65) already links the section. |
| `format.versioning` (`format/versioning.md`) | "Version-aware compatibility" (lines 49-63) | Line 51 says "`vNEXT` requirements never apply retroactively". Add this sentence after it: "Exception: the heading "Arithmetic" and the rule `V-pre.normalize-3` of Normalization (`../pre/normalization.md#arithmetic`) and the headings "Arithmetic" and "Inverse" of Affine person crop (`../pre/resize-affine-person-crop.md#arithmetic`) apply to every `schema_version`." This proposal and `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md` (2.1, row `format.versioning`) share this one sentence, with the same text. Add it one time. If only one of the two proposals lands, remove the part of the other. The sentence names `V-pre.normalize-3`, because the rule is new at `vNEXT` and applies to every `schema_version` (N1). The sentence does not cover a field or a rule that has the **(vNEXT)** mark. The link to the legacy table of `pre.normalize` exists (line 59). |
| `specs/model-sidecar/README.md` | Section map (line 69); validation index (line 111) | No edit. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" (lines 16-36) | Add the row of 2.7. |
| `specs/model-sidecar/changelog.md` | "`schema_version` history" (line 68) | Append the sentence of 2.7 to the `vNEXT` row. Do not add a second `vNEXT` row. |
| `specs/model-sidecar/changelog.md` | "Compatibility impact" (lines 55-59) | Add the bullet of 2.7. |
| `specs/model-sidecar/vectors/pre.normalize.yaml` | existing file | Add the cases of part 4. The 16 existing cases do not change. Do not edit the file by hand: it comes from `tools/make_vectors.py` (header line 2). |
| `tools/make_vectors.py` | `normalize_pixels` (lines 1070-1106), `build_normalize` (line 1109), `ROUND_DIGITS` (line 62), `TOLERANCE` (line 65) | For the skellytracker session. `normalize_pixels` calculates in float64 and does not round to float32. The new `arith-*` cases need the float32 rounding and at least 9 significant digits: a rounding to 6 decimals (`ROUND_DIGITS`) can use up to 5e-7 of the bound of 1e-6. Add the `conforms` and `check_rules` cases with their own expect keys (`result`, `failed`). The old cases keep `TOLERANCE["normalize"] = 1e-5`. |
| `tools/tests/test_vectors.py` | `CASE_KEYS` (lines 32-40) | The part 4 cases have `function` and `compare`. `CASE_KEYS` has neither. Convert them as the SimCC proposal says for its cases (`specs/model-sidecar/proposals/simcc-score-rule/proposal.md`, part 2.1, row `tools/tests/test_vectors.py`): either add `function`, or select the function by the prefix of the id (`arith-`, `none-`, `conforms-`, `rule`). Map `compare.values.atol` to the case `tolerance`. Keep the file-level `unverified` (a file has exactly one of the two keys: `test_vectors.py:132`, `make_vectors.py:155-156`). The four `arith-imagenet-*` cases have a case-level `verified_against` (allowed: `make_vectors.py:9-12`, `test_vectors.py:39`). Its entry names an exporter function, but `resolve_function` (`test_vectors.py:86-93`) needs a file in the skellytracker repo, so `test_vectors.py:160-166` fails on it. Write the exporter entry as a comment on the case. List a skellytracker function there only after a test runs it (`make_vectors.py:11-12`). The anchor test `test_normalize_anchors_come_from_the_published_imagenet_statistics` (lines 312-339) does not change. |
| `specs/model-sidecar/reference/pre_normalize.py` | new file | The reference file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated matrix (rows at lines 32, 82) | Do not edit by hand. Run `python tools/sidecar_trace.py matrix` after the section file changes. |
| `specs/exporter-guide/sidecars/workflow/parity.md` | "Parity", step 4 (lines 28-32) | Non-spec PR. Add: "For the normalization, the host value and the upstream value can differ within the accuracy rule of `pre.normalize` (`pre/normalization.md#arithmetic`). Such a difference is not a defect. Give its maximum. A difference above the rule is a defect." |
| `specs/exporter-guide/sidecars/workflow/mapping-hints.md` | "Mapping hints for phase 1", "Preprocessing" (lines 39-40) | Non-spec PR. Append: "The heading "Arithmetic" of `pre.normalize` gives the accuracy rule. A different order of operations in float32 or float64 meets it. float16 arithmetic does not." |
| `specs/model-sidecar/templates/model-intake.md` | row T10 (line 273) | Non-spec PR. Append to the property: "Compare the arithmetic with the accuracy rule of `pre.normalize`." |
| `notes/decisions/open-work.md` | "Spec defects" (lines 125-127 and line 168, at `dom/21-move-sidecar-guide`) | Non-spec PR. After the content PR, remove the item about the `imagenet_bgr` default note. Change "the arithmetic precision of the geometry and of the pixel math" to "the arithmetic precision of the geometry" (the normalization part is then in the spec). |
| `specs/model-sidecar/examples/` | all examples | No edit. No example has an integer `input.dtype` with a mode other than `none`. |
| `post.*`, `pre.resize.*`, `common.identity`, `format.file_layout` | | No edit. The change adds no role, no path and no output semantic. |

### 2.2 Fields table

No new field. The description of `normalization` changes (line 30):

| Field | Type | Required | Description |
|---|---|---|---|
| `normalization` | string or object | no | See Normalization modes (`normalization.md`). The default is `imagenet_bgr`. See Behaviour (`#behaviour`). |

### 2.3 Behaviour

Add this sub-heading under "Behaviour", after the paragraph on `custom.color_format` (line 53):

```text
### Arithmetic

The formulas of the modes are real-number formulas. This heading gives the values that a host must
give for them. This heading applies to every `schema_version` (the exception in
[Version-aware compatibility](../format/versioning.md#version-aware-compatibility)).

- `p` is the value of one channel of one pixel after the resize. The resize section of the sidecar
  gives `p`.
- `mean`, `std` and `scale` are the decimal numbers of the mode table, or the numbers of the
  `custom` object.
- `none`: the host value `t` must be equal to `p`.
- Other modes: calculate the formula of the mode in float64. Do the operations in the order of
  the formula. Round the result one time to float32 (round to nearest, ties to even). This value
  is the reference value `r`.
- For `unit_float`, `imagenet_bgr` and `imagenet_rgb`, and for each integer `p` from 0 to 255,
  `r` is also the exact value of the formula, rounded one time to float32.
- The host can calculate the formula in a different order of operations. Examples:
  `(p / 255 - 0.485) / 0.229`, or `p * a + b` with `a = 1 / std` and `b = -mean / std`.
  The host must calculate in float32 or in a type with more precision. The host must not
  calculate the formula in float16.
- Each host value `t` must agree with its reference value:
  `abs(t - r) <= 1e-6 * max(1, abs(r))`.
- Then the host casts `t` to the `input.dtype` of the precision. For `float32`, the value does not
  change. For `float16`, the cast rounds to nearest, ties to even. The accuracy rule applies to `t`
  before the cast. When `t` is near a float16 rounding boundary, the result can be the other
  float16 value next to `t`.
- An integer `input.dtype` (`uint8` or `int8`) is valid only with `none` (`V-pre.normalize-3`).
  This applies to every `schema_version`. Thus a mode other than `none` always casts to `float32`
  or `float16`.

Two hosts that obey this rule can give different float32 values. Do not expect bit-exact
equality between two hosts. Compare the preprocessed input with this rule.
```

Replace the warning (line 93) with:

```text
> ⚠️ Declare `normalization` explicitly. The default `imagenet_bgr` has two meanings. In a `vNEXT`
> sidecar, it uses BGR-ordered statistics on a BGR tensor: this is the mmdet convention of RTMDet.
> In a legacy sidecar, it is the rtmlib convention of the package RTMPose and RTMW sidecars (see
> [Legacy behaviour](#legacy-behaviour)). An mmpose model with `bgr_to_rgb=True` (RTMPose, RTMW,
> DWPose) is `imagenet_rgb` in a `vNEXT` sidecar. For most detectors and pose models, the default
> gives incorrect normalization.
```

**Guidance.** Add to "Implementer guidance":

- The OpenMMLab-Exporter host calculates `(float32(p) - float32(mean)) / float32(std)`. Over the 256
  byte values, it differs from `r` by at most 2.4e-7, which is 0.12 of the bound. (OpenMMLab-Exporter
  `onnx_runtime/preprocess.py:144-149`, eed3361; scratch measurement of this proposal)
- The skellytracker `build_normalization_fn` uses the same float32 arithmetic for `unit_float`, the
  `imagenet_*` modes and `custom`. It meets the accuracy rule. `preprocess_image` returns float32
  for every `input.dtype`. (`skellytracker/core/detectors/processing/image_preprocessing.py:74, 77-90, 244`)
- A float16 graph input needs the cast at the end. Do the arithmetic in float32, then cast.
  float16 arithmetic differs from `r` by up to 2.2e-3 over the 256 byte values. In the order
  `(p - mean) / std`, this is up to 1011 times the bound. In the order `(p / 255 - m) / s`, it is up
  to 1697 times the bound.

Add to "Authoring guidance":

- ViTPose and ViTPose++ (ViTAE-Transformer/ViTPose `c050ed2`): `LoadImageFromFile` keeps uint8 RGB,
  `ToTensor` divides by 255 in float32, and `NormalizeTensor` applies `mean=[0.485, 0.456, 0.406]`
  and `std=[0.229, 0.224, 0.225]` in float32. This maps to `normalization: imagenet_rgb` and
  `color_format: rgb`. The arithmetic differs from `r` by at most 4.8e-7 (0.24 of the bound). It
  meets the accuracy rule. (ViTAE `mmpose/datasets/pipelines/loading.py:29, 31`,
  `mmpose/datasets/pipelines/shared_transform.py:21-64`; torchvision v0.10.0
  `transforms/functional.py:114-117, 326-335`)
- easy_ViTPose calculates the same formula in float64 and casts to float32. It gives `r` exactly.
  (easy_ViTPose `bb98603` `easy_ViTPose/inference.py:316-317`)
- mmpose 1.x and mmdet use the mmengine `ImgDataPreprocessor`: `(float32(p) - mean) / std` with
  float32 `mean` and `std`. This is the arithmetic of the OpenMMLab-Exporter host. (mmengine v0.10.3
  `mmengine/model/base_model/data_preprocessor.py:227-230, 266, 275`)

### 2.4 Validation rules

New rule, after `V-pre.normalize-2`:

- [ ] `V-pre.normalize-3` If a declared precision (a key of `input.dtype`) resolves to a mode other
  than `none`, the `input.dtype` of that precision must be `float32` or `float16`. This rule
  applies to every `schema_version` (see
  Version-aware compatibility (`../format/versioning.md#version-aware-compatibility`)).

The rule has no **(vNEXT)** mark. A marked rule applies only when `schema_version >= vNEXT`
(skellytracker `specs/model-sidecar/README.md:99`). The user decided that the rule applies to every
`schema_version` (N1, plan T23, 2026-10-24). The exception sentence of 2.1 (row
`format.versioning`) names the rule.

A validator checks rule 3 for each precision that resolves to a valid mode. It does this also when
rule 1 or rule 2 fails for another value. A precision that resolves to a mode that is not valid has
no rule 3 result: rule 1 or rule 2 reports it. (Case `rule2-and-rule3` of part 4.)

Existing rules that name a value of this change:

- `V-pre.normalize-1` (valid mode): one clarification. The text "If `mean` or `std` is present, it
  must have length 3" (`pre/normalization.md:105`) also accepts a 3-character string such as
  `"abc"`. Replace it with "If `mean` or `std` is present, it must be a list of three finite
  numbers". `scale` already must be a positive number. (Case `rule1-custom-mean-string` of part 4.)
- `V-pre.normalize-2` (the override values): unchanged.
- `V-common.input-2` (`common/input.md:58`, the dtype values `float32`, `float16`, `uint8`, `int8`):
  unchanged. The new rule limits `uint8` and `int8` to `none` for each precision.
- `V-common.input-6` (`common/input.md:63`, `color_format`): unchanged.

Follow-up, not in this proposal: `none` with `input.dtype: int8`. The values 128 to 255 do not fit
`int8`. No model in scope uses it.

### 2.5 Selectors

Unchanged: `input.normalization=none`, `=unit_float`, `=imagenet_bgr`, `=imagenet_rgb`,
`input.normalization.mode=custom` (`pre/normalization.md:7-12`).

### 2.6 Legacy behaviour and version effect

- The spec rule: "`vNEXT` requirements never apply retroactively"
  (`format/versioning.md:51`). The skellytracker decision 0009 repeats it: "The spec never applies `vNEXT`
  requirements to a legacy sidecar" (`specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md:15`, also
  `:39`). The heading "Arithmetic" adds host requirements: the accuracy rule, "The host must not
  calculate the formula in float16", and the cast to `input.dtype`. The rule `V-pre.normalize-3`
  adds a validation requirement.
- **Scope: every `schema_version`** (option B; user decision T21 (3), 2026-10-23,
  the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary; for the rule, N1, user decision T23, 2026-10-24). The
  reason: no sidecar is deployed yet, and all sidecars will be made again. The heading
  "Arithmetic" and the rule `V-pre.normalize-3` are thus `vNEXT` requirements that apply
  retroactively. `format/versioning.md:51` gets the exception sentence of 2.1 (row
  `format.versioning`). The proposal `affine-crop-arithmetic` shares this sentence.
- The legacy meaning does not change. Each mode keeps its formula and its statistics. The legacy
  `imagenet_bgr` keeps the RGB-ordered tuple on the B, G, R channels. The heading gives only the
  arithmetic of these formulas. The skellytracker float32 values for the package sidecars meet the
  accuracy rule (2.3, "Guidance"). Thus no legacy value of skellytracker changes.
- A legacy host that calculates in float16, or that differs from `r` by more than the bound, does
  not conform. Part 7 found no such host.
- `V-pre.normalize-3` has no **(vNEXT)** mark. It applies to a legacy sidecar too (N1). A legacy
  sidecar with an integer `input.dtype` and a mode other than `none` does not load. Part 7 found no
  such sidecar: each of the 23 sidecar files that part 7 lists passes the rule at its own
  `schema_version`.
- The reference file of part 3 follows this scope. `reference_values` and `conforms` take no
  `schema_version`: a caller applies `conforms` to every sidecar. `check_rules` applies
  `V-pre.normalize-3` to every `schema_version`.
- The legacy table (`pre/normalization.md:112-114`) gets two new rows:

  ```text
  | [Arithmetic](#arithmetic) | Applies (the exception in [Version-aware compatibility](../format/versioning.md#version-aware-compatibility)). The legacy `imagenet_bgr` formula uses the statistics of the row above. | Applies. |
  | `V-pre.normalize-3` (a float `input.dtype` for a mode other than `none`) | Applies (the exception in [Version-aware compatibility](../format/versioning.md#version-aware-compatibility)). | Applies. |
  ```

- The change goes into the `vNEXT` revision.

### 2.7 Changelog row

Summary of changes (`changelog.md:16`, five columns). `N` is the next free number at merge time
(rows 1 to 19 exist, `changelog.md:18-36`; other proposals of this exporter also add rows).

```text
| N | Input | `pre.normalize` defines its arithmetic for every `schema_version`. The reference value of a formula is the float64 result, rounded one time to float32. A host value `t` must meet `abs(t - r) <= 1e-6 * max(1, abs(r))`, with float32 or wider arithmetic. `none` is exact. The host casts the result to `input.dtype` at the end. A mode other than `none` needs a float `input.dtype` (every `schema_version`). The note on the default `imagenet_bgr` names the mmdet convention at `vNEXT`. A `custom` `mean` or `std` must be a list of three finite numbers. | ViTPose (ViTAE: `/255`, then the ImageNet statistics in float32); RTMW, RTMDet (mmengine float32) | [Normalization](pre/normalization.md#arithmetic) |
```

Sentence to append to the `vNEXT` row of the `schema_version` history (`changelog.md:68`):

```text
`pre.normalize` defines its arithmetic (at every `schema_version`): a float32 reference value, the accuracy rule `abs(t - r) <= 1e-6 * max(1, abs(r))` and the cast to `input.dtype`; every mode other than `none` needs a float `input.dtype` (at every `schema_version`).
```

Bullet for "Compatibility impact" (`changelog.md:55-59`):

```text
- `pre.normalize` hosts do not have to give bit-exact normalized values. Each value must meet the accuracy rule of [Normalization](pre/normalization.md#arithmetic), for every `schema_version`. This is an exception to the rule that `vNEXT` requirements do not apply retroactively. The formulas keep their meaning. A sidecar with a mode other than `none` must declare a float `input.dtype` for each precision, for every `schema_version` (`V-pre.normalize-3`, the same exception).
```

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the exporter repo (the part 3 code of `specs/model-sidecar/proposals/<slug>/proposal.md`) | the part 3 code of `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_normalize.py` |
| Functions (one for each algorithm) | `is_legacy` (the version split), `resolve_mode` (the resolution order), `channel_order` (the tensor order of each mode), `reference_values` (the reference value `r`: float64 in the order of the formula, then one rounding to float32; the legacy `imagenet_bgr`), `accuracy_bound` (`1e-6 * max(1, abs(r))`), `conforms` (the accuracy rule; `none` exact), `cast_to_dtype` (the cast to `input.dtype`), `normalize` (the full section), `check_rules` (`V-pre.normalize-1` to `-3`) |

Source commit: `d0f4343` (the file is the same at `01d9b3d` and at `f3aeb47`, the last checked
commit: on 2026-10-25, `git diff --stat 01d9b3d f3aeb47 -- onnx_runtime/preprocess.py` and
`git diff --stat d0f4343 f3aeb47 -- onnx_runtime/preprocess.py` listed no change). The host code of `imagenet_bgr`, `imagenet_rgb` and `none` is
`onnx_runtime/preprocess.py` (`make_normalizer`, lines 120-151, last changed in `eed3361`). That
code gives the float32 form. The reference file gives the reference value and the rule. The host
form meets the rule. The host has no `unit_float`, no `custom`, no legacy `imagenet_bgr` and no cast
to `input.dtype` (`preprocess.py:42, 131-132, 149`). Those parts come from the text of part 2. The
section has no reference implementation yet (`specs/model-sidecar/reference/` does not exist in the
checkout). Thus the file implements the full section as changed. It is also the
reference-implementation step of the section (`exporter-guide/sidecars/reference-implementations.md:15-16`).

```python
"""Reference implementation of the section pre.normalize, as the proposal changes it.

Section ID: pre.normalize (section file specs/model-sidecar/pre/normalization.md).
Proposal: specs/model-sidecar/proposals/normalize-arithmetic/proposal.md (OpenMMLab-Exporter), slug
normalize-arithmetic. No skellytracker decision entry covers it.
Target file in skellytracker: specs/model-sidecar/reference/pre_normalize.py.

source commit: d0f4343 (OpenMMLab-Exporter). The host file is the same at 01d9b3d and at
f3aeb47, the last checked commit. On 2026-10-25, git diff --stat 01d9b3d f3aeb47 and
git diff --stat d0f4343 f3aeb47 (both -- onnx_runtime/preprocess.py) listed no change.
The host code of the named modes imagenet_bgr,
imagenet_rgb and none is onnx_runtime/preprocess.py (make_normalizer, lines 120-151, last changed
in eed3361). That host computes (float32(p) - float32(mean)) / float32(std). This file gives the
reference value of the proposed heading "Arithmetic" (float64, then one rounding to float32) and
the accuracy rule. The host form meets the rule. The host has no unit_float, no custom, no legacy
imagenet_bgr and no cast to input.dtype: these parts come from the text of part 2 only.

Vector results (run of 2026-10-23): the 16 cases of specs/model-sidecar/vectors/pre.normalize.yaml
(skellytracker dom/12-single-working-branch; the file is the same at dom/18-agents-adr-bootstrap-kit and at dom/21-move-sidecar-guide) pass at their tolerance (1e-5, or exact for a case with no tolerance).
The 30 new cases of part 4 pass. The host make_normalizer (d0f4343) meets 10 cases (part 4 gives
the list). Run again after the option B edit: the same counts. Run again on 2026-10-24 after the
N1 edit (rule 3 at every schema_version; the case rule3-legacy-not-applied is now
rule3-legacy-applies): 30 of 30 new cases and 16 of 16 existing cases pass.
Parity result: to run (part 5 of the proposal).

The file implements the full section as changed: the mode resolution, the channel order, the five
modes with the legacy imagenet_bgr, the reference arithmetic, the accuracy rule, the cast to
input.dtype and the validation rules V-pre.normalize-1 to -3.

Version scope (part 2.6 of the proposal): the heading "Arithmetic" and the rule V-pre.normalize-3
apply to every schema_version (option B, OpenMMLab-Exporter plan T21 (3), 2026-10-23; N1, plan
T23, 2026-10-24). This is an exception to specs/model-sidecar/format/versioning.md:51. The proposal
affine-crop-arithmetic shares the exception sentence. The functions reference_values and conforms
thus take no schema_version: a caller applies conforms to every sidecar. reference_values also
gives r for the legacy imagenet_bgr formula. check_rules applies V-pre.normalize-3 to every
schema_version, because the rule has no (vNEXT) mark.

Uses only NumPy and the Python standard library.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

NAMED_MODES = ("none", "unit_float", "imagenet_bgr", "imagenet_rgb")
PRECISIONS = ("fp32", "fp16", "int8")
FLOAT_DTYPES = ("float32", "float16")

# Per-colour ImageNet statistics on 0-255 pixels, in R, G, B order (0.485/0.456/0.406 and
# 0.229/0.224/0.225 x 255).
IMAGENET_MEAN_RGB = (123.675, 116.28, 103.53)
IMAGENET_STD_RGB = (58.395, 57.12, 57.375)

ACCURACY = 1e-6
"""pre.normalize, heading "Arithmetic": the factor of the accuracy rule."""


def is_legacy(schema_version: str = "vNEXT") -> bool:
    """pre.normalize, heading "Legacy behaviour": True for schema_version < vNEXT.

    The vectors write a legacy version as "< vNEXT". A release string such as "v2024.09.1019"
    is also legacy: every release up to now is older than vNEXT.
    """
    return schema_version != "vNEXT"


def resolve_mode(
    normalization: Any = None,
    normalization_by_precision: Mapping[str, str] | None = None,
    precision: str = "fp32",
) -> Any:
    """pre.normalize: the resolution order for a selected precision.

    normalization_by_precision[precision], then the top-level normalization, then the default
    imagenet_bgr.
    """
    if normalization_by_precision and precision in normalization_by_precision:
        return normalization_by_precision[precision]
    if normalization is not None:
        return normalization
    return "imagenet_bgr"


def channel_order(mode: Any, color_format: str | None = None) -> str:
    """pre.normalize: the channel order of the tensor ("rgb" or "bgr").

    none and unit_float take input.color_format, which must be present. imagenet_rgb is rgb and
    imagenet_bgr is bgr. custom takes custom.color_format, then input.color_format, then rgb.
    """
    if isinstance(mode, Mapping):
        return mode.get("color_format") or color_format or "rgb"
    if mode in ("none", "unit_float"):
        if color_format not in ("rgb", "bgr"):
            raise ValueError(f"{mode} needs input.color_format rgb or bgr")
        return color_format
    if mode == "imagenet_rgb":
        return "rgb"
    if mode == "imagenet_bgr":
        return "bgr"
    raise ValueError(f"unknown normalization mode: {mode!r}")


def reference_values(
    pixels: np.ndarray, mode: Any, order: str, legacy: bool = False
) -> np.ndarray:
    """pre.normalize, heading "Arithmetic": the reference value r of each channel.

    `pixels` has the shape (..., 3), in the channel order `order` of the tensor. The function
    evaluates the formula of the mode in float64, with the operations in the order of the
    formula. Then it rounds the result one time to float32 (round to nearest, ties to even).
    For none, the value is the pixel value, with no arithmetic.
    """
    p = np.asarray(pixels, dtype=np.float64)
    if isinstance(mode, Mapping):
        scale = float(mode.get("scale", 1.0))
        mean = np.asarray(mode.get("mean", [0.0, 0.0, 0.0]), dtype=np.float64)
        std = np.asarray(mode.get("std", [1.0, 1.0, 1.0]), dtype=np.float64)
        return ((p * scale - mean) / std).astype(np.float32)
    if mode == "none":
        return p
    if mode == "unit_float":
        return (p / 255.0).astype(np.float32)
    mean = np.asarray(IMAGENET_MEAN_RGB, dtype=np.float64)
    std = np.asarray(IMAGENET_STD_RGB, dtype=np.float64)
    if order == "bgr" and not (legacy and mode == "imagenet_bgr"):
        # vNEXT imagenet_bgr: BGR-ordered statistics. Legacy imagenet_bgr keeps the RGB tuple.
        mean, std = mean[::-1], std[::-1]
    return ((p - mean) / std).astype(np.float32)


def accuracy_bound(reference: np.ndarray) -> np.ndarray:
    """pre.normalize, heading "Arithmetic": the largest allowed difference for each value.

    bound = 1e-6 * max(1, abs(r)), in float64.
    """
    r = np.asarray(reference, dtype=np.float64)
    return ACCURACY * np.maximum(1.0, np.abs(r))


def conforms(host_values: Any, reference: Any, mode: Any = "imagenet_rgb") -> bool:
    """pre.normalize, heading "Arithmetic": True when the host values meet the accuracy rule.

    For each value t of the host and its reference value r: abs(t - r) <= 1e-6 * max(1, abs(r)),
    compared in float64. For none, t must be equal to r (the pixel value).
    """
    t = np.asarray(host_values, dtype=np.float64)
    r = np.asarray(reference, dtype=np.float64)
    if t.shape != r.shape:
        return False
    if mode == "none":
        return bool(np.array_equal(t, r))
    return bool(np.all(np.abs(t - r) <= accuracy_bound(r)))


def cast_to_dtype(values: np.ndarray, dtype: str) -> np.ndarray:
    """pre.normalize, heading "Arithmetic": the cast of the result to input.dtype.

    float32 keeps the value. float16 rounds the float32 value to nearest, ties to even. A host
    that casts a wider value t can get the other float16 value next to it when t is near a
    rounding boundary. The section allows this (one float16 step). uint8 and int8 are valid only
    for none (rule V-pre.normalize-3), and the value must fit the type.
    """
    v = np.asarray(values)
    if dtype in FLOAT_DTYPES:
        return v.astype(np.float32).astype(dtype)
    if dtype in ("uint8", "int8"):
        info = np.iinfo(dtype)
        if not np.all(np.equal(np.mod(v, 1), 0)) or v.min() < info.min or v.max() > info.max:
            raise ValueError(f"values do not fit input.dtype {dtype}")
        return v.astype(dtype)
    raise ValueError(f"unknown input.dtype: {dtype!r}")


def normalize(
    pixels_bgr: Sequence[Sequence[float]],
    normalization: Any = None,
    normalization_by_precision: Mapping[str, str] | None = None,
    precision: str = "fp32",
    color_format: str | None = None,
    dtype: str = "float32",
    schema_version: str = "vNEXT",
) -> dict[str, Any]:
    """pre.normalize: the full section for the pixels of the resized frame.

    `pixels_bgr` are pixel values in the BGR source order, shape (..., 3). The function resolves
    the mode, puts the channels in the order of the tensor, gives the reference values and casts
    them to input.dtype. Returns {resolved_mode, channel_order, values}. `values` are in the
    channel order of the tensor.
    """
    mode = resolve_mode(normalization, normalization_by_precision, precision)
    order = channel_order(mode, color_format)
    bgr = np.asarray(pixels_bgr, dtype=np.float64)
    pixels = bgr if order == "bgr" else bgr[..., ::-1]
    values = reference_values(pixels, mode, order, legacy=is_legacy(schema_version))
    resolved = "custom" if isinstance(mode, Mapping) else mode
    return {
        "resolved_mode": resolved,
        "channel_order": order,
        "values": cast_to_dtype(values, dtype),
    }


def check_rules(input_block: Mapping[str, Any], schema_version: str = "vNEXT") -> list[str]:
    """pre.normalize, heading "Validation rules": the IDs of the rules that the input block fails.

    V-pre.normalize-1: a valid mode. V-pre.normalize-2: the keys and the values of
    normalization_by_precision. V-pre.normalize-3 (every schema_version): a precision that
    resolves to a mode other than none must have input.dtype float32 or float16. The function
    checks rule 3 for each key of input.dtype whose mode resolves to a valid mode, also when rule 1
    or rule 2 fails. A precision whose mode is not valid has no rule 3 result: rule 1 or rule 2
    reports it. The color_format rule is V-common.input-6. It is not in this function.
    No rule of this function depends on schema_version. The parameter stays, so that a caller
    can give the same arguments for every section.
    """
    failed: list[str] = []
    norm = input_block.get("normalization")
    if norm is not None and not _valid_mode(norm):
        failed.append("V-pre.normalize-1")
    by_precision = input_block.get("normalization_by_precision") or {}
    if any(k not in PRECISIONS for k in by_precision) or any(
        not isinstance(v, str) or v not in NAMED_MODES for v in by_precision.values()
    ):
        failed.append("V-pre.normalize-2")
    dtype = input_block.get("dtype") or {}
    for precision, element_type in dtype.items():
        mode = resolve_mode(norm, by_precision, precision)
        if not _valid_mode(mode):
            continue
        if mode != "none" and element_type not in FLOAT_DTYPES:
            failed.append("V-pre.normalize-3")
            break
    return failed


def _is_real(value: Any) -> bool:
    """pre.normalize, rule V-pre.normalize-1: a finite real number that is not a bool."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _valid_mode(norm: Any) -> bool:
    """pre.normalize, rule V-pre.normalize-1: True when norm is a valid mode. A valid mode is a mode string of the mode table, or a custom object whose mean and std (when present) are lists of three finite numbers, whose scale (when present) is a positive finite number, and whose color_format (when present) is rgb or bgr."""
    if isinstance(norm, str):
        return norm in NAMED_MODES
    if not isinstance(norm, Mapping) or norm.get("mode") != "custom":
        return False
    for key in ("mean", "std"):
        if key not in norm:
            continue
        values = norm[key]
        if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
            return False
        if len(values) != 3 or not all(_is_real(v) for v in values):
            return False
    if "scale" in norm:
        scale = norm["scale"]
        if not _is_real(scale) or scale <= 0:
            return False
    if "color_format" in norm and norm["color_format"] not in ("rgb", "bgr"):
        return False
    return True
```

## 4. Vectors

Run of 2026-10-23 (first run: scratch `norm_vectors.py` and `run_cases.py`; run again after the
review fixes: scratch `run_vectors.py`, which reads the YAML block below from this file; each file
loaded from its path; `uv run --project <exporter repo> python -I -B`, NumPy 2.5.4, PyYAML 6.0.3).
Run again on 2026-10-23 after the option B edit of the text and the commit edit (`d0f4343`): the
same counts. The values of the cases did not change. Run again on 2026-10-24 after the N1 edit
(rule 3 at every `schema_version`; the case `rule3-legacy-not-applied` is replaced by
`rule3-legacy-applies`): 30 of 30 new cases and 16 of 16 existing cases pass (scratch
`omm-proposals/run_all.py`, the same command). The host check ran on the file
`onnx_runtime/preprocess.py` at `d0f4343` (`git show d0f4343:onnx_runtime/preprocess.py`):

- **The 16 existing cases** of `specs/model-sidecar/vectors/pre.normalize.yaml` (skellytracker `dom/12-single-working-branch`; the file is the same at `dom/18-agents-adr-bootstrap-kit` and at `dom/21-move-sidecar-guide`)
  pass against `normalize` of the reference file, at their tolerance (1e-5, or exact). They do not
  change.
- **The 30 new cases below** pass against the reference file. The generator also checks each `arith-*`
  value against the exact rational value of the formula, rounded to float32 (Python `fractions`), and
  each `conforms-*` and `rule*` result against a value written by hand.
- **Host check.** The exporter host `make_normalizer` (`onnx_runtime/preprocess.py:120-151`, d0f4343)
  meets 10 cases: the existing `none-rgb`, `none-bgr`, `imagenet-bgr`, `imagenet-rgb`,
  `imagenet-rgb-with-color-format`, `default-is-imagenet-bgr`, and the new
  `arith-imagenet-rgb-near-mean`, `arith-imagenet-rgb-extremes`, `arith-imagenet-bgr-near-mean`,
  `arith-imagenet-bgr-extremes` (each value within the `compare` tolerance and within the rule). The
  host gives the values of `conforms-exporter-host-float32` exactly. The other cases did not run on
  the host: it has no `unit_float`, no `custom`, no `normalization_by_precision`, no legacy meaning
  and no cast to `input.dtype`.
- **Mutants.** The run tested ten changes of the reference file. Eight fail at least one case: `<`
  in place of `<=`, an absolute bound only, a relative bound only, no BGR order of the statistics,
  no legacy branch (fails the existing case `imagenet-bgr-legacy`), rule 3 for legacy sidecars,
  rule 3 only when rules 1 and 2 pass (fails `rule2-and-rule3`), and a length-only check of `mean`
  (fails `rule1-custom-mean-string`). Two pass, as they must: a float32 calculation of `r`, and
  `p * float32(1/255)` for `unit_float`. They are valid hosts under the rule. After N1 the mutant
  "rule 3 for legacy sidecars" is the correct rule. The inverse mutant, rule 3 only at `vNEXT`
  (the reference file before N1), fails exactly one case, `rule3-legacy-applies` (run of
  2026-10-24).
- The upstream code did not run. The `conforms-vitae-float32` and `conforms-easy-vitpose-float64` host
  values come from a NumPy emulation of ViTAE `shared_transform.py:34, 61-62` with torchvision
  v0.10.0 `functional.py:117, 335`, and of easy_ViTPose `inference.py:316-317`. They are not an
  implementation.

The host verifies the four `arith-imagenet-*` cases. A file has exactly one of `verified_against`
and `unverified` (skellytracker `tools/tests/test_vectors.py:132`, `tools/make_vectors.py:155-156`).
Thus the file has `unverified`, and each of the four cases has its own `verified_against`
(`make_vectors.py:11`, `test_vectors.py:39`). 2.1 (row `tools/tests/test_vectors.py`) tells how the
skellytracker session converts that entry.

`compare.values.atol` of each float32 `arith-*` case is the bound of the smallest value of the case.
Thus it is never larger than the rule for a value of the case. The float16 case
`arith-imagenet-rgb-float16` has `atol: 2^-9`. That is one float16 step for its values in [2, 4).
For its one value in [1, 2), `-1.8046875`, the float16 step is 2^-10, so the atol allows two steps
there. A runner reads each number as float64. The
`expect` values have the shortest text that gives the same float32 value. `conforms` compares in
float64.

The YAML uses the form of the template (`function` and `compare` on each case). The skellytracker
vector tooling uses another form. 2.1 (rows `tools/make_vectors.py` and `tools/tests/test_vectors.py`)
gives the conversion.

```yaml
section: pre.normalize
spec_revision: vNEXT
generated_by: the part 3 code of `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md`
unverified: "Only the four arith-imagenet-* cases ran on an exporter host (each has its own
  verified_against). No exporter host has unit_float, custom, the cast to input.dtype, the accuracy
  check or the rule V-pre.normalize-3. skellytracker has the float32 arithmetic but no vNEXT
  imagenet_bgr and no color_format."
# The conforms-vitae-float32 and conforms-easy-vitpose-float64 host values emulate
# ViTAE-Transformer/ViTPose c050ed2 shared_transform.py:34, 61-62 (torchvision v0.10.0
# functional.py:117, 335) and easy_ViTPose bb98603 inference.py:316-317 with NumPy (not run).
cases:
- id: arith-imagenet-rgb-near-mean  # |r| <= 1: the bound is 1e-6. Bytes where the float32 forms differ from r.
  function: normalize
  verified_against:
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer  # exporter commit d0f4343
  params: {normalization: imagenet_rgb}
  input:
    pixels_bgr:
    - [73, 70, 81]
    - [76, 83, 93]
    - [70, 103, 100]
    - [104, 116, 124]
  expect:
    resolved_mode: imagenet_rgb
    channel_order: rgb
    values:
    - [-0.73079884, -0.8102241, -0.5321133]
    - [-0.5253018, -0.5826331, -0.4798257]
    - [-0.40542856, -0.232493, -0.5844009]
    - [0.005565545, -0.004901961, 0.0081917215]
  compare:
    values: {atol: 1.0e-06}
- id: arith-imagenet-rgb-extremes  # 0, 255 and the byte with the largest ViTAE difference in each channel
  function: normalize
  verified_against:
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer  # exporter commit d0f4343
  params: {normalization: imagenet_rgb}
  input:
    pixels_bgr:
    - [0, 0, 0]
    - [255, 255, 255]
    - [234, 0, 6]
    - [254, 254, 254]
  expect:
    resolved_mode: imagenet_rgb
    channel_order: rgb
    values:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  compare:
    values: {atol: 1.804e-06}
- id: arith-imagenet-bgr-near-mean  # the same pixels: the same per-colour values in B, G, R order
  function: normalize
  verified_against:
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer  # exporter commit d0f4343
  params: {normalization: imagenet_bgr}
  input:
    pixels_bgr:
    - [73, 70, 81]
    - [76, 83, 93]
    - [70, 103, 100]
    - [104, 116, 124]
  expect:
    resolved_mode: imagenet_bgr
    channel_order: bgr
    values:
    - [-0.5321133, -0.8102241, -0.73079884]
    - [-0.4798257, -0.5826331, -0.5253018]
    - [-0.5844009, -0.232493, -0.40542856]
    - [0.0081917215, -0.004901961, 0.005565545]
  compare:
    values: {atol: 1.0e-06}
- id: arith-imagenet-bgr-extremes
  function: normalize
  verified_against:
  - OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer  # exporter commit d0f4343
  params: {normalization: imagenet_bgr}
  input:
    pixels_bgr:
    - [0, 0, 0]
    - [255, 255, 255]
    - [234, 0, 6]
    - [254, 254, 254]
  expect:
    resolved_mode: imagenet_bgr
    channel_order: bgr
    values:
    - [-1.8044444, -2.0357144, -2.117904]
    - [2.64, 2.4285715, 2.2489083]
    - [2.2739868, -2.0357144, -2.0151553]
    - [2.6225708, 2.4110644, 2.2317836]
  compare:
    values: {atol: 1.804e-06}
- id: arith-unit-float  # bytes where float32 p / 255 and p * float32(1/255) differ
  function: normalize
  params: {normalization: unit_float, color_format: rgb}
  input:
    pixels_bgr:
    - [3, 6, 7]
    - [12, 13, 14]
    - [15, 24, 25]
    - [0, 255, 128]
  expect:
    resolved_mode: unit_float
    channel_order: rgb
    values:
    - [0.02745098, 0.023529412, 0.011764706]
    - [0.05490196, 0.050980393, 0.047058824]
    - [0.09803922, 0.09411765, 0.05882353]
    - [0.5019608, 1.0, 0.0]
  compare:
    values: {atol: 1.0e-06}
- id: arith-custom-large-values  # |r| > 1: the bound is relative, 1e-6 * |r|
  function: normalize
  params:
    normalization:
      mode: custom
      color_format: rgb
      scale: 1.0
      mean: [0.5, 0.5, 0.5]
      std: [0.3, 0.3, 0.3]
  input:
    pixels_bgr:
    - [255, 200, 128]
    - [129, 254, 255]
  expect:
    resolved_mode: custom
    channel_order: rgb
    values:
    - [425.0, 665.0, 848.3333]
    - [848.3333, 845.0, 428.33334]
  compare:
    values: {atol: 0.000425}
- id: arith-imagenet-rgb-float16  # float32 arithmetic, then the cast. atol 2^-9 is one float16 step of the values in [2, 4); for -1.8046875 in [1, 2) it is two steps
  function: normalize
  params: {normalization: imagenet_rgb, dtype: float16}
  input:
    pixels_bgr:
    - [0, 0, 0]
    - [255, 255, 255]
    - [234, 0, 6]
    - [254, 254, 254]
  expect:
    resolved_mode: imagenet_rgb
    channel_order: rgb
    values:
    - [-2.1171875, -2.03515625, -1.8046875]
    - [2.248046875, 2.427734375, 2.640625]
    - [-2.015625, -2.03515625, 2.2734375]
    - [2.232421875, 2.41015625, 2.623046875]
  compare:
    values: {atol: 0.001953125}
- id: none-float16  # none is exact; 0 to 255 are exact in float16
  function: normalize
  params: {normalization: none, color_format: rgb, dtype: float16}
  input:
    pixels_bgr:
    - [0, 128, 255]
    - [1, 2, 254]
  expect:
    resolved_mode: none
    channel_order: rgb
    values:
    - [255, 128, 0]
    - [254, 2, 1]
- id: conforms-exporter-host-float32  # (float32(p) - float32(mean)) / float32(std); 3 of 12 values differ from r
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151556, -2.0357144, 2.273987]
    - [2.2317834, 2.4110644, 2.6225708]
    reference:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  expect: {result: true}
- id: conforms-vitae-float32  # float32 p / 255, then (x - 0.485) / 0.229; 7 of 12 values differ, max 4.8e-7
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values:
    - [-2.117904, -2.0357141, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151556, -2.0357141, 2.2739873]
    - [2.2317834, 2.4110641, 2.622571]
    reference:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  expect: {result: true}
- id: conforms-easy-vitpose-float64  # float64, then float32: equal to r
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
    reference:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  expect: {result: true}
- id: conforms-custom-decimal-scale-float32  # custom scale 0.00392156862745098, mean 0.485.., std 0.229.., float32
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values:
    - [-2.117904, -2.0357141, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151556, -2.0357141, 2.2739873]
    - [2.2317836, 2.4110649, 2.622571]
    reference:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  expect: {result: true}
- id: conforms-float16-arithmetic  # (p - mean) / std in float16: up to 1.4e-3 from r on these 12 values, 617 times the bound
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values:
    - [-2.1171875, -2.0351562, -1.8037109]
    - [2.2480469, 2.4296875, 2.640625]
    - [-2.015625, -2.0351562, 2.2753906]
    - [2.2304688, 2.4121094, 2.6230469]
    reference:
    - [-2.117904, -2.0357144, -1.8044444]
    - [2.2489083, 2.4285715, 2.64]
    - [-2.0151553, -2.0357144, 2.2739868]
    - [2.2317836, 2.4110644, 2.6225708]
  expect: {result: false}
- id: conforms-zero-at-bound  # |r| < 1: the bound is 1e-6; equal to the bound passes (<=)
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values: [1.0e-06]
    reference: [0.0]
  expect: {result: true}
- id: conforms-small-above-bound
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values: [0.5000015]
    reference: [0.5]
  expect: {result: false}
- id: conforms-relative-large  # r = 2: the bound is 2e-6; 2^-19 = 1.9e-6 passes (an absolute 1e-6 bound fails)
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values: [2.000001907348633]
    reference: [2.0]
  expect: {result: true}
- id: conforms-relative-above  # 2^-18 = 3.8e-6 is above 2e-6
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values: [2.0000038146972656]
    reference: [2.0]
  expect: {result: false}
- id: conforms-none-exact
  function: conforms
  params: {mode: none}
  input:
    host_values: [128.0]
    reference: [128.0]
  expect: {result: true}
- id: conforms-none-not-exact  # none has no tolerance
  function: conforms
  params: {mode: none}
  input:
    host_values: [128.00001]
    reference: [128.0]
  expect: {result: false}
- id: conforms-shape-differs
  function: conforms
  params: {mode: imagenet_rgb}
  input:
    host_values: [0.0, 0.0]
    reference: [0.0]
  expect: {result: false}
- id: rule3-unit-float-uint8
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: uint8}
      normalization: unit_float
      color_format: rgb
  expect:
    failed: [V-pre.normalize-3]
- id: rule3-default-mode-int8  # normalization is absent: the default imagenet_bgr needs a float dtype
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32, int8: int8}
  expect:
    failed: [V-pre.normalize-3]
- id: rule3-override-none-uint8  # the per-precision example of the section: int8 resolves to none
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32, fp16: float32, int8: uint8}
      normalization: unit_float
      normalization_by_precision: {int8: none}
      color_format: rgb
  expect:
    failed: []
- id: rule3-float16-input
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32, fp16: float16}
      normalization: imagenet_rgb
  expect:
    failed: []
- id: rule3-legacy-applies  # the rule has no (vNEXT) mark: it applies to every schema_version (N1)
  function: check_rules
  params: {schema_version: "< vNEXT"}
  input:
    input_block:
      dtype: {fp32: uint8}
      normalization: unit_float
  expect:
    failed: [V-pre.normalize-3]
- id: rule1-unknown-mode
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32}
      normalization: imagenet
  expect:
    failed: [V-pre.normalize-1]
- id: rule1-custom-scale-zero
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32}
      normalization: {mode: custom, scale: 0}
  expect:
    failed: [V-pre.normalize-1]
- id: rule2-custom-override
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32}
      normalization: unit_float
      normalization_by_precision:
        fp16: {mode: custom}
      color_format: rgb
  expect:
    failed: [V-pre.normalize-2]
- id: rule2-and-rule3  # an unknown override key fails rule 2; fp32 still resolves to unit_float on uint8
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: uint8}
      normalization: unit_float
      normalization_by_precision: {int4: none}
      color_format: rgb
  expect:
    failed: [V-pre.normalize-2, V-pre.normalize-3]
- id: rule1-custom-mean-string  # a 3-character string is not a list of three numbers
  function: check_rules
  params: {schema_version: vNEXT}
  input:
    input_block:
      dtype: {fp32: float32}
      normalization: {mode: custom, mean: abc}
  expect:
    failed: [V-pre.normalize-1]
```

Each key of `params` and `input` is a parameter of the function that the case names. The
`arith-*` cases are pixel-value cases on 4 pixels, not image cases. Each has its tolerance in
`compare`.

## 5. Parity evidence

| Item | Value |
|---|---|
| Gates, set before the run, and their source | (1) **Arithmetic sweep:** the upstream `ToTensor` and `NormalizeTensor` (ViTAE) and `pre_img` (easy_ViTPose) on an image that has each byte value 0 to 255 in each channel. Each value must meet the accuracy rule against `r` (part 2.3). Record the maximum (expected: 4.8e-7 for ViTAE, 0 for easy_ViTPose, from the emulation of part 1). (2) **Preprocessed input** (exporter guide, "Parity", step 4): the host tensor and the upstream tensor each meet the rule against `r`, so `abs(t_host - t_upstream) <= 2e-6 * max(1, abs(r))`. Record the maximum for each image. Source: part 2.3. (3) **Export error** `E`: the maximum heatmap difference between the own ONNX file and the ViTAE model on the upstream tensor. Recorded, not gated. (4) **Outputs:** the heatmap difference of the host path and the upstream path. Record it, and compare it with `E`. Count the argmax changes and the changes of the sign of the `default` refinement. List each one with its two neighbour values. For a keypoint with no such change: the per-point difference in source-image pixels is at most 1e-3 px (float32 noise of the unprojection). (5) Body OKS AP on the full set: `abs(AP_host - AP_upstream) <= 0.005` (the fp32 gate of this exporter, OpenMMLab-Exporter decision D5, `notes/decisions/migration-decisions.md:55`). |
| Test images (paths or dataset IDs), and the branch that each image runs | The sweep image (gate 1): a 16 x 16 x 3 uint8 array with the 256 byte values in each channel, in a different order in each channel. It runs every byte of every channel. COCO val2017 GT person boxes (`annotations/person_keypoints_val2017.json`): a box near the image border (the zero border of the crop gives `p = 0`), a crop of a bright region (`p = 255`), a portrait box and a landscape box. The full set of 6352 instances for gate (5). The normalization has no other branch: the mode is fixed (`imagenet_rgb`) for both families. |
| Upstream reference: library, version, config and command | ViTAE-Transformer/ViTPose `c050ed2` (mmpose 0.x, torch 1.9, mmcv 1.3.9) in the second Python environment `/opt/vitae` of the exporter image (plan T12, step 5.1; not built yet). Configs: `ViTPose_<size>_wholebody_256x192.py` unchanged (ViTPose++, plan T3) and the created 25-point config of plan 4.4 (pipeline B2, plan T9). The worker builds the `val_pipeline` and saves the tensor after `NormalizeTensor` and the heatmaps of the model. For the sweep, it calls `ToTensor()` and `NormalizeTensor(mean, std)` from `mmpose.datasets.pipelines.shared_transform` directly on the sweep image, on the CPU, as the data loader does. easy_ViTPose `bb98603`: `pre_img` only (no model), on the sweep image. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | to run (no own ONNX file yet; the HF ONNX of the same weights gave 6.0e-7 on 3 inputs, the untracked pose-models plan of OpenMMLab-Exporter (plan facts), secondary) |
| Preprocessed input: maximum absolute difference for each image | to run (expected at most 4.8e-7: the ViTAE form against the host form, part 1) |
| Row count for each image: sidecar path and upstream | to run (one pose for each box on both sides) |
| Final outputs in source-image coordinates: metric and value for each role | to run (`pose_estimator`: gates 4 and 5) |
| Result (`pass`, `fail` or `to run`) | to run |
| Script path in the exporter repo | `notes/decisions/scripts/vitpose_normalize_parity.py` (host side: ONNX Runtime, the exporter `make_normalizer`, the reference file of part 3 for `r` and the rule, the gates) and a ViTAE worker under `exporter/worker/` (container side). Planned, not written. The heatmap-decode and flip-test parity runs of the ViTPose families can use the same worker and the same saved tensors. |
| Exporter commit of the script | unknown (the script is not written yet) |
| Command | `uv run python notes/decisions/scripts/vitpose_normalize_parity.py --family vitposepp-wholebody133 --size s` and `--family vitpose-coco25 --size s` (planned). The script starts the worker in the published image `<user>/openmmlab-exporter:df-<sha>`. |

The host side keeps torch out of the host process (`AGENTS.md`, section 4). Only the worker in the
container imports ViTAE mmpose and torch. The crop of the host side is the host implementation of
`pre.resize.affine_person_crop` (plan step 5c), after its commit.

## 6. skellytracker implementation proposal

skellytracker does not build this now. The implementer checks this part.

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/image_preprocessing.py`. `build_normalization_fn` (lines 62-92) already uses float32 arithmetic for `unit_float` (line 74), the `imagenet_*` modes (lines 77-84) and `custom` (lines 86-90). That arithmetic meets the rule. No arithmetic change is necessary. Add the cast to `input.dtype`: `preprocess_image` (line 158) casts every tensor to float32 (line 244). For a `float16` input dtype, cast the float32 result to float16 there. For `none` with `uint8`, keep uint8. |
| Dispatch point | `preprocess_image`, after `normalize(padded)` (lines 238-244). The precision of the call selects the dtype from `input_spec.dtype`. |
| Validator changes (`model.py`, with rule IDs) | `V-pre.normalize-3`: for each key of `InputSpec.dtype` (`skellytracker/core/sidecar/model.py:122-134`), resolve the mode (the order of `resolve_normalization_mode`, `image_preprocessing.py:48`). A mode other than `none` needs `float32` or `float16`. The rule applies to every `schema_version` (N1), so the check needs no `schema_version`. `InputSpec` has no `schema_version` (skellytracker decision 0009, "Evidence"), but it has `dtype` and the normalization fields, so the check can be on `InputSpec`. |
| Tests | The vectors of part 4 (`specs/model-sidecar/vectors/pre.normalize.yaml`), with a runner that calls `build_normalization_fn` and compares with `conforms`. A test that a `float16` input dtype gives a float16 tensor. A rejection test of `V-pre.normalize-3` in `skellytracker/tests/sidecar/test_model_validation.py`. The existing tests in `skellytracker/tests/test_image_preprocessing.py` (class `TestNormalizationDispatch`, line 101) keep their values. |
| Existing code that the change touches | `preprocess_image` (the final cast); the sidecar validator (rule 3). Not this proposal: the `vNEXT` `imagenet_bgr` and `color_format` (skellytracker decision 0009 and the front matter of the section). |

## 7. Exporter impact

| Exporter | Affected sidecars | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmdet-person` (`imagenet_bgr`), `rtmw-wholebody133` (`imagenet_rgb`), `rtmo-coco17-body7` (`none`): `rtmdet_person/sidecar.py:106`, `rtmw/sidecar.py:104`, `rtmo/sidecar.py:105` (at `f3aeb47`). OpenMMLab-Exporter decision 0050 (`f3aeb47`) writes no sidecar of these three families until the intake of the family is `describes`. The writers stay, and they write the next sidecars at that later round. The planned families `vitposepp-wholebody133` (the untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts)) and `vitpose-coco25` (the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts)), both `imagenet_rgb` with `color_format: rgb`. The planned `dwpose-wholebody133-ubody` and `rtmpose-halpe26` (`imagenet_rgb`). | none. All input dtypes are float32: the sidecar writers read the dtype from the graph (`rtmw/sidecar.py:78, 101`, at `f3aeb47`), and fp16 artifacts keep float32 graph inputs (`onnx_convert/FP16_CONTRACT.md:16`). Thus `V-pre.normalize-3` passes. After acceptance, row T10 of both ViTPose intakes becomes `exact`. Row T10 of the RTMW, DWPose and Halpe26 intakes (the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts), the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts), the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts)) is `near-miss` (intake correction of 2026-10-24). The mmengine float32 form meets the rule, so these rows become `exact` after acceptance, when parity step 4 gives 0 for the mmengine form against the host form: mmengine and the host use the same float32 arithmetic. Row T10 of the RTMDet intake (the untracked intake of `rtmdet-person` of OpenMMLab-Exporter (plan facts)) is `unverified` (expected `exact`). | none. `make_normalizer` (`onnx_runtime/preprocess.py:120-151`) meets the rule. The ViTPose families reuse it (plan step 5c). The parity scripts compare the input with the rule, not with 0. |
| Roboflow-Exporter | `rfdetr` (`imagenet_rgb`) | none | none for this change. Its host divides by 255 in float32 and applies `(x - mean) / std` in float32 (`onnx_runtime/preprocess.py:75, 85`, d0559b9): the ViTAE order. It resizes the float image after the division. That is the separate resize-dtype defect (skellytracker `notes/decisions/open-work.md:162-163`), not this proposal. |
| Ultralytics-Exporter | `yolo26` (`unit_float`; `normalization_by_precision: {p: none}` only for a `uint8` or `int8` input, `yolo_sidecar.py:383, 391-393`, 2e0280e) | none. `V-pre.normalize-3` passes at every `schema_version`: the override gives `none` for an integer dtype. The two current legacy files declare `float32` for `fp32`, `fp16` and `int8` and pass (part 7, "Check of N1"). | unknown (not read): a GPU fp16 export has a float16 input (`common/input.md:78`). Its host must do the arithmetic in float32 and cast at the end. This applies also to its current legacy sidecars (`schema_version` `v2024.09.1019`, `exporter-guide/sidecars/known-open-items.md:12`), because the heading applies to every `schema_version` (2.6). |
| Qualcomm-Exporter | the MediaPipe models (`unit_float`) | none. Every precision has a float32 input (`qai_sidecar.py:74-76`, 4ca4586). | none |
| MediaPipe-Exporter | the planned `mediapipe-hand21` (`unit_float`). Its row T10 is `unverified`, and it may need this proposal: its proposals row names this proposal "only if parity step 4 is not 0" (the untracked intake of `mediapipe-hand21` of MediaPipe-Exporter (plan facts), read 2026-10-24). MediaPipe multiplies by a float32 `1 / 255` in OpenCV `convertTo` (the same row; the intake did not read the `convertTo` code). | none now (no sidecar file) | not read. The part 4 mutant `p * float32(1/255)` meets the accuracy rule. |
| The proposing exporter, if it is not in this table | n/a (OpenMMLab-Exporter is in the table) | | |
| skellytracker package sidecars | `rtmpose-body`, `rtmpose-hand`, `rtmpose-face`, `rtmw-wholebody` (legacy `imagenet_bgr`), `yolox` (`none`), all `v2024.09.1019` | none. The heading "Arithmetic" and rule 3 apply to them (2.6, N1). The accuracy rule accepts the current skellytracker float32 values (2.3, "Guidance"). Each of them declares `dtype: {fp32: float32}` (`rtmpose-body.yaml:9-10` and the same lines in the others), so each passes rule 3 (part 7, "Check of N1"). | none |

**Check of N1 (2026-10-24, read only).** The scratch script `omm-proposals/n1_check.py` loads each
sidecar file below. It applies `check_rules` of the reference file with rule 3 at every
`schema_version`. Each file passes (no failed rule). No file declares `normalization_by_precision`.

| Repo (HEAD) | Sidecar file | `schema_version` | `input.dtype` | `normalization` |
|---|---|---|---|---|
| skellytracker (HEAD `dom/14-decision-log-growth` at the check, `dom/14-decision-log-growth` at the end of the session; `git diff dom/12-single-working-branch dom/14-decision-log-growth` changes no file under `skellytracker/core/detectors/` or `specs/model-sidecar/examples/`, and not `specs/model-sidecar/README.md` or `specs/model-sidecar/format/versioning.md`; the five package sidecars and the five example sidecars are the same at `dom/21-move-sidecar-guide` (checked 2026-10-25; `git diff dom/14-decision-log-growth dom/21-move-sidecar-guide` changes no file under `skellytracker/core/detectors/` or `specs/model-sidecar/examples/`)) | `skellytracker/core/detectors/keypoint_detectors/rtmpose/body/rtmpose-body.yaml`, `rtmpose/face/rtmpose-face.yaml`, `rtmpose/hand/rtmpose-hand.yaml`, `rtmw/wholebody/rtmw-wholebody.yaml` | `v2024.09.1019` | `{fp32: float32}` | `imagenet_bgr` |
| skellytracker | `skellytracker/core/detectors/object_detectors/yolox/yolox.yaml` | `v2024.09.1019` | `{fp32: float32}` | `none` |
| skellytracker | `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmo/body/rtmo-body7.yaml` | `vNEXT` | `{fp32: float32}` | `none` |
| skellytracker | `specs/model-sidecar/examples/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` | `vNEXT` | `{fp32: float32, fp16: float32}` | `imagenet_rgb` |
| skellytracker | `specs/model-sidecar/examples/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml`, `specs/model-sidecar/examples/detectors/object_detectors/yolo26/yolo26.yaml` | `vNEXT` | `{fp32: float32, fp16: float32, int8: float32}` | `unit_float` |
| skellytracker | `specs/model-sidecar/examples/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml` | `vNEXT` | `{fp32: float32, fp16: float32}` | `imagenet_bgr` |
| Ultralytics-Exporter (`2e0280e`) | `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body.yaml`, `exports/detectors/object_detectors/yolo26/yolo26.yaml` | `v2024.09.1019` | `{fp32: float32, fp16: float32, int8: float32}` | `unit_float` |
| OpenMMLab-Exporter (`d0f4343`; `exports/` is not tracked and has the ids before T14) | `exports/detectors/keypoint_detectors/rtmo/body7/rtmo-body7.yaml` | `vNEXT` | `{fp16: float32, fp32: float32}` | `none` |
| OpenMMLab-Exporter | `exports/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml` | `vNEXT` | `{fp16: float32, fp32: float32}` | `imagenet_rgb` |
| OpenMMLab-Exporter | `exports/detectors/object_detectors/rtmdet-person/rtmdet-person.yaml` | `vNEXT` | `{fp16: float32, fp32: float32}` | `imagenet_bgr` |
| OpenMMLab-Exporter | `notes/decisions/rtmo-body7.yaml`, `notes/decisions/rtmo-coco17-body7.yaml` | `vNEXT` | `{fp32: float32}` | `none` |
| Roboflow-Exporter (`c64fd2a`) | `exports/detectors/object_detectors/rfdetr/rfdetr.yaml` | `vNEXT` | `{fp32: float32, fp16: float32}` | `imagenet_rgb` |
| Qualcomm-Exporter (`4ca4586`) | `exports/detectors/keypoint_detectors/mediapipe/face/mediapipe-face.yaml`, `.../mediapipe/hand/mediapipe-hand.yaml`, `exports/detectors/object_detectors/mediapipe-face-detector/mediapipe-face-detector.yaml`, `.../mediapipe-hand-detector/mediapipe-hand-detector.yaml`, `.../mediapipe-person-detector/mediapipe-person-detector.yaml` | `v2024.09.1019` | `{fp16: float32, fp32: float32}` | `unit_float` |

The 23 files are all the YAML files with `schema_version` and `input` in these folders. The
MediaPipe files under skellytracker `keypoint_detectors/mediapipe/` have no `input` block, so they
are not sidecars of this kind. The 7 scratch copies under OpenMMLab-Exporter `temp/` (not
tracked; `vNEXT`, float32 inputs) also pass. They are not in the count. The writers of OpenMMLab-Exporter read the dtype from the graph
(`rtmdet_person/sidecar.py:103`, `rtmw/sidecar.py:101`, `rtmo/sidecar.py:102`; at `f3aeb47`). The
Ultralytics-Exporter writer adds `normalization_by_precision: {<p>: none}` for each `uint8` or
`int8` input (`yolo_sidecar.py:391-393`) and writes `schema_version` `v2024.09.1019`
(`yolo_sidecar.py:19`). Thus a future quantized legacy Ultralytics sidecar also passes.
MediaPipe-Exporter has no sidecar file (no YAML file with `schema_version`).

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| No change (the near-miss of today: `imagenet_rgb` with no arithmetic) | The text has no value for a pixel. Under T2 the ViTPose rows stay `near-miss`. Parity step 4 expects 0, but no host other than a copy of the ViTAE torch steps can give 0. | Part 1; `pre/normalization.md:41-45`; `exporter-guide/sidecars/workflow/parity.md:28-32` |
| A bit-exact normative form in float32, `(float32(p) - float32(mean)) / float32(std)` (the mmengine and exporter host order) | The exporter host, skellytracker and mmengine meet it. ViTAE (4.8e-7), easy_ViTPose (2.4e-7), the Roboflow host order, the RF-DETR in-graph scale and bias form, and the `custom` form do not. The ViTPose rows stay `near-miss`. The rule fixes the order of operations, but the order has no measured effect on the outputs. | Part 1 (`norm_forms.py`); mmengine `data_preprocessor.py:275` |
| A bit-exact correctly rounded value (float64, then float32) | Only easy_ViTPose meets it. The exporter host, skellytracker, mmengine and ViTAE do not: each host must change. This proposal uses this value as the reference `r`, but not as a requirement. | Part 1 |
| A new mode for the ViTAE order (for example `imagenet_rgb_unit`, or a `custom` field that divides first) | It describes ViTAE only if torch divides with a true division. easy_ViTPose would need a further mode, and each framework one more. The effect is below the noise of the execution provider: the arithmetic changes the heatmaps by at most 3.5e-6 with 0 argmax changes, CPU against CUDA (TF32 off) by 7.2e-6, and CPU against CUDA (TF32 on) by 1.6e-3 with 40 argmax changes. A host cannot select its provider from the sidecar. | Part 1 (`norm_sensitivity.py`, `norm_provider_noise.py`) |
| `custom` with `scale: 0.00392156862745098`, `mean: [0.485, 0.456, 0.406]`, `std: [0.229, 0.224, 0.225]` (an existing mapping) | It is not the ViTAE arithmetic either (`p * scale`, not `p / 255`; it differs from `r` by 7.2e-7 and from ViTAE at most bytes). Under the current text it is also a near-miss. The section prefers a named mode (`pre/normalization.md:55`). | Part 1; plan A.3 |
| A tolerance only in the parity rules of the exporter guide | The spec is normative, and the guide is not. The value of a host would still be undefined, and the vectors would have no tolerance to test. This proposal changes the guide too, but as a result of the spec text. | `exporter-guide/sidecars/rules.md:3`; 2.1 |
| A bound in float32 units in the last place (ULP) | It fails near zero. For `p` near the mean, the value is near 0, and a float32 form that meets the rule is up to 310 ULP from `r`. | `norm_forms.py` (the "ulp" column) |
| A larger bound (for example 1e-4) or a smaller one (for example 2.5e-7) | 1e-6 gives a margin of 3.3 over the worst float32 form in use (0.31 of the bound), and it rejects float16 arithmetic (over all bytes, up to 1011 times the bound in the host order and up to 1697 times in the ViTAE order). A bound of 1e-4 would still reject float16 arithmetic, but it would accept a defect of the statistics in the fourth decimal. A bound near one float32 step rejects valid float32 hosts. The user accepts the bound 1e-6 (N2, plan T23, 2026-10-24). | `norm_forms2.py`; part 4 `conforms-float16-arithmetic` |
| Option A: the heading "Arithmetic" only at `vNEXT` (a **(vNEXT)** mark on the heading, a legacy row "the formulas only", no edit of `format/versioning.md:51`) | The user selected option B (T21 (3), 2026-10-23): no sidecar is deployed yet, and all sidecars will be made again. Option A keeps the rule that `vNEXT` requirements never apply retroactively, but then a legacy sidecar has no defined value for a pixel, and a host needs two texts for one formula. Option B changes no legacy value: the formulas stay, and the skellytracker float32 values meet the rule. The cost of option B is the exception sentence in `versioning.md:51`, which `affine-crop-arithmetic` shares. | the untracked pose-models plan of OpenMMLab-Exporter (plan facts) (secondary); `format/versioning.md:51`; skellytracker decision 0009 (`specs/model-sidecar/decisions/0009-imagenet-bgr-meaning.md:15, 39`); 2.6 |
| No rule `V-pre.normalize-3` | Then the cast of a negative value to `uint8` has no defined result. The rule is small, and no current sidecar fails it. The user keeps it in this proposal (N3, plan T23, 2026-10-24). | 2.4; part 7 |
| `V-pre.normalize-3` only at `vNEXT` (the rule with the **(vNEXT)** mark) | The user chose every `schema_version` (N1, plan T23, 2026-10-24), as for the heading "Arithmetic". With the mark, the heading defines no cast for a legacy sidecar with an integer `input.dtype` and a mode other than `none`. No current sidecar fails the rule at its own `schema_version`. The cost: the exception sentence of 2.1 also names the rule. | 2.3, 2.4, 2.6; part 7, "Check of N1"; skellytracker `specs/model-sidecar/README.md:99` |
| The default-note correction as a separate proposal | It is in the same section and changes no value. It is a known defect (`notes/decisions/open-work.md:125-127`). The user keeps it in this proposal (N3, plan T23, 2026-10-24). | 2.1 |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake links to this proposal. The untracked intake of `vitposepp-wholebody133` of OpenMMLab-Exporter (plan facts) (row T10,
      line 120; proposal row, line 273; reference row, line 289),
      the untracked intake of `vitpose-coco25` of OpenMMLab-Exporter (plan facts) (row T10, line 133; lines 283 and 295), the untracked intake of `rtmw-wholebody133` of OpenMMLab-Exporter (plan facts) (lines 158, 314, 329), the untracked intake of `dwpose-wholebody133-ubody` of OpenMMLab-Exporter (plan facts) (lines 103, 253, 266) and the untracked intake of `rtmpose-halpe26` of OpenMMLab-Exporter (plan facts) (lines 123, 274, 288) name this file
      and the part 3 code of `specs/model-sidecar/proposals/normalize-arithmetic/proposal.md`.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. (none)
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the untracked plans folder of OpenMMLab-Exporter (plan facts).
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. n/a (`to run`)
- [x] No file in skellytracker changed.

- [x] The version scope follows the user decision T21 (3) (option B) in the header, 2.1, 2.3, 2.6,
      2.7, part 7 and part 8. The exception sentence of 2.1 (row `format.versioning`) has the same
      text in `specs/model-sidecar/proposals/affine-crop-arithmetic/proposal.md`.
- [x] The user decides N1 to N3 (plan T23, 2026-10-24). N1: `V-pre.normalize-3` applies to every
      `schema_version`, in the header, 2.1, 2.3, 2.4, 2.6, 2.7, part 3, part 4 (case
      `rule3-legacy-applies`), part 6, part 7 and part 8. N2: the bound `1e-6 * max(1, abs(r))`.
      N3: the rule and the default-note correction stay in this proposal.

This proposal has `to run` in part 5. The version scope is decided (option B). The user decided N1
to N3 (header; plan T23, 2026-10-24). It is ready for a skellytracker session to record. It is not
ready for the user to accept.

## Before acceptance

This list gives the work that must be done before the user can accept this proposal. The skellytracker
session checked each item against the proposal text and against the working branch on 2026-10-25.

**Parts**

- [ ] In the docstring of the reference file, remove the path of the proposal in the untracked plans
      folder, the citations of the plan items T21 (3) and T23, and the skellytracker commits that are
      not on `development`. Remove the
      sentence "No skellytracker decision entry covers it": decision 0043 now records the proposal.
- [ ] `is_legacy` of the reference file returns `True` for each `schema_version` that is not
      `vNEXT`. Define the version comparison for the time after the release of `vNEXT`.
- [ ] Part 2.1 does not list the sub-heading "Mode validation" (`pre/normalization.md:95-101`). Its
      line 99 says "a sequence of length 3", the text that 2.4 changes in `V-pre.normalize-1`. The
      sub-heading does not name `V-pre.normalize-3`. Add the place to 2.1, or remove the duplicate
      text (one owner for each rule, decision 0013).
- [ ] Part 2.1 does not list `changelog.md:30` (summary row 13) and `changelog.md:57` ("Compatibility
      impact"). Both say that a sidecar older than `vNEXT` keeps loading with its old meaning. With
      `V-pre.normalize-3` at every `schema_version`, a legacy sidecar with an integer `input.dtype`
      and a mode other than `none` does not load. Add an edit of these lines, or give the reason why
      no edit is necessary.
- [ ] The proposed text for `specs/exporter-guide/sidecars/workflow/parity.md` (2.1) has the link
      target `pre/normalization.md#arithmetic`. From that folder, the target does not resolve, and
      `tools/tests/test_links.py` fails on it. Correct the target.
- [ ] 2.3 ("Guidance") and part 6 say that the skellytracker float32 arithmetic of `custom` meets the
      accuracy rule. That is not true for all parameters. A scratch check of the skellytracker session
      (not evidence) found
      a plain float32 host at 9.4 times the bound for `mean` 123.675 and `std` 0.01, and at 0.094
      times the bound for `mean` 100.0 and `std` 0.001. The cause is the float32 error of a mean that
      is not exact, divided by a small `std`. Limit the claim, or require wider arithmetic for
      `custom`.
- [ ] 2.3 ("Guidance") and part 6 say that `build_normalization_fn` meets the rule for the
      `imagenet_*` modes. The arithmetic meets it. But the `imagenet_rgb` branch
      (`image_preprocessing.py:81-84`) is the same code as the `imagenet_bgr` branch (lines 76-79),
      and no code in the file changes the channel order. Thus the skellytracker `imagenet_rgb` values
      are not the `vNEXT` reference values. Say that the claim is about the arithmetic only, or name
      this defect in the new `implemented_by` comment.
- [ ] Part 7 names only the MediaPipe-Exporter model `mediapipe-hand21`. The MediaPipe-Exporter
      intakes of `mediapipe-hand-roi` and `mediapipe-pose39`, and its BlazePose plan, also name this
      proposal for row T10. Add them to part 7.
- [ ] The header says that OpenMMLab-Exporter commit `f3aeb47` is "not pushed". It is now on
      `origin/main` of OpenMMLab-Exporter. Correct the header.
- [ ] 2.1 and 2.4 cite `V-common.input-2` at `common/input.md:58`. On the working branch, the rule is
      at line 59. Correct the citation.

**Evidence**

- [ ] Part 5 is `to run` in each result cell. Build the ViTAE environment `/opt/vitae` of the
      exporter image. Write and commit the parity script
      `notes/decisions/scripts/vitpose_normalize_parity.py` and the ViTAE worker in
      OpenMMLab-Exporter. Run gates 1 to 5. Give the results and the exporter commit of the script.
- [ ] Export the ONNX files of `vitposepp-wholebody133` and `vitpose-coco25` in OpenMMLab-Exporter.
      The output numbers of part 1 use the HF ONNX files of `JunkyByte/easy_ViTPose` (`e838052`).
- [ ] Run the ViTAE `ToTensor` and `NormalizeTensor` with torch on each byte value. Part 1 has only a
      NumPy emulation. Pin the torchvision version of the ViTAE environment.
- [ ] Pin the mmengine version in the exporter image. Only the untracked source accuracy reports
      record v0.10.3.
- [ ] Commit the measurement scripts of parts 1, 4 and 7 (`norm_forms.py`, `norm_forms2.py`,
      `norm_sensitivity.py`, `norm_provider_noise.py`, `run_vectors.py`, `run_all.py` and
      `n1_check.py`). Until then, their numbers are not evidence.
- [ ] Read the MediaPipe `convertTo` code (part 7, row MediaPipe-Exporter) and the fp16 host of
      Ultralytics-Exporter (part 7: "unknown (not read)").

**Template checklist**

- [ ] "Part 2.1 lists each place that the change edits" is ticked. But 2.1 does not list "Mode
      validation" and `changelog.md:30, 57` (see **Parts**). It also does not name the reference test
      and the generator change of `change-sidecar-spec`, Procedure B, steps 7 and 8 (see **Vectors
      and tooling**).

**Vectors and tooling**

- [ ] Convert the 30 cases of part 4 to the case form of the skellytracker tools. `CASE_KEYS` of
      `tools/tests/test_vectors.py` has no `function` and no `compare`. The test requires
      `generated_by: tools/make_vectors.py` (line 141). The user decides the case form one time for
      all proposals.
- [ ] The four `arith-imagenet-*` cases have a case-level `verified_against` with an OpenMMLab-Exporter
      function. `resolve_function` of `test_vectors.py` cannot import it. The user decides if the
      tests accept an exporter function.
- [ ] `change-sidecar-spec`, Procedure B, step 8, makes `tools/make_vectors.py` call the reference
      implementation and removes the formula version of the section. The row `tools/make_vectors.py`
      of 2.1 changes `normalize_pixels` instead. Select one method.
- [ ] Add a test in `tools/tests` that runs the reference functions against the vectors (Procedure B,
      step 7). Decide how the tests import `specs/model-sidecar/reference/`.
- [ ] A regeneration of the 16 existing cases from `normalize` of the reference file, rounded to 6
      decimals (`ROUND_DIGITS`), changes the text of 6 cases: `imagenet-bgr`, `imagenet-rgb`,
      `imagenet-rgb-with-color-format`, `custom-rgb`, `custom-bgr` and `default-is-imagenet-bgr`.
      Each value changes by 1.0e-6 or less, inside the tolerance 1e-5. Part 4 says that the 16 cases
      do not change. This is a stop point of `change-sidecar-spec`. The user accepts or rejects the
      change of these values.

**Decisions for the user**

- [ ] The version scope. The heading "Arithmetic" and `V-pre.normalize-3` apply to every
      `schema_version`. The user decisions T21 (3) and T23 (N1 to N3) are only in the untracked
      pose-models plan of OpenMMLab-Exporter (plan facts). Confirm them in skellytracker. The scope is
      an exception to `format/versioning.md:51` ("`vNEXT` requirements never apply retroactively").
      It also conflicts with `AGENTS.md` section 4 ("The meaning of an older `schema_version` never
      changes"), with the same rule in `change-sidecar-spec`, with `changelog.md:30, 57` and with
      decision [0009](../../decisions/0009-imagenet-bgr-meaning.md) (lines 15 and 39).
      Decide if a new entry must supersede 0009 in full.
- [ ] The place of the exception sentence. `format/versioning.md:51` has three sentences. 2.1 says
      "Add this sentence after it" about the second sentence ("`vNEXT` requirements never apply
      retroactively"). Decide if the new sentence goes directly after the second sentence or at the
      end of the line.
- [ ] The `custom` defaults. The reference file uses `mean: [0, 0, 0]` and `std: [1, 1, 1]` when the
      keys are absent. skellytracker uses the same defaults (`image_preprocessing.py:87-88`). The spec
      text gives no default. Decide if the spec states them.
- [ ] The `dtype` example of `common/input.md:26`, `{fp32: float32, fp16: float16, int8: uint8}`, is
      not valid under `V-pre.normalize-3` when the mode of `int8` is not `none`. The proposal makes no
      edit in `common.input`. Decide if the example changes.
- [ ] `external_impl` stays `[]`, but the OpenMMLab-Exporter host `make_normalizer` meets four new
      cases. Decide if the front matter lists it.
- [ ] Upstream citations. easy_ViTPose `bb98603` and `JunkyByte/easy_ViTPose` `e838052` have no full
      SHA in this file. Decide the citation rule for upstream repositories that are not exporters.
- [ ] Decide if the "Implementer guidance" and "Authoring guidance" bullets of 2.3 go in the content
      PR or in the non-spec PR.

**Merge points**

- [ ] `format/versioning.md:51`: `affine-crop-arithmetic` (0037) has the same exception sentence. Add
      it one time. Its part links `../pre/resize-affine-person-crop.md#arithmetic`, and that anchor
      exists only after `affine-crop-arithmetic` lands. If this proposal lands first, remove that part,
      or land the two proposals in one PR.
- [ ] `pre/normalization.md:47-53` ("Behaviour"): `roi-transform-and-source` (0020) adds a sentence at
      line 49. This proposal adds a sentence after line 47 and the heading "Arithmetic".
- [ ] `notes/decisions/open-work.md:168` ("Spec defects"): `affine-crop-arithmetic` (0037) also
      changes this item.
- [ ] `changelog.md:55-59` ("Compatibility impact"): `simcc-score-rule` (0024),
      `heatmap-decode-refinement` (0038), `affine-crop-arithmetic` (0037), `model-id-suffix` (0025),
      `roi-transform-and-source` (0020), `landmark-extra-outputs` (0021) and `landmark-depth-divisor`
      (0022) also add bullets. All proposals add a row to "Summary of changes" and a sentence to the
      `vNEXT` row (`changelog.md:68`).
- [ ] `BUILDERS` of `tools/make_vectors.py` and `CASE_KEYS` of `tools/tests/test_vectors.py`:
      `simcc-score-rule` (0024), `heatmap-decode-refinement` (0038), `affine-crop-arithmetic` (0037),
      `model-id-suffix` (0025), `size-codes` (0046) and `keypoint-visibility` (0039).
- [ ] `specs/exporter-guide/sidecars/workflow/mapping-hints.md`, the bullet "Preprocessing":
      `affine-crop-arithmetic` (0037) and `roi-transform-and-source` (0020) also edit it.
- [ ] Part 5: the parity runs of `heatmap-decode-refinement` (0038) and `pose-decode-flip-test` (0045)
      can use the same ViTAE container worker.
