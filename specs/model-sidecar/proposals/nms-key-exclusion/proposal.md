# Change proposal: nms-key-exclusion

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | The reference module of `post.det.selection.nms` refuses `class_logits_output`, `top_k` and `max_detections`, as `V-post.det.selection.nms-1` says |
| Slug | `nms-key-exclusion` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `c2e610e91fee0a961032e12737ff9147697a7e53` |
| Model, and its `model` bundle ID | `yolox-person`, `model-yolox-person@openmmlab-exporter`. The sidecar of the model does not change. The skellytracker session notice of 2026-11-06 for `model-yolox-person@openmmlab-exporter` v1 asked for this proposal (secondary). |
| Intake rows with the verdict `near-miss` or `gap` | none. The defect is in the landed reference module, not in a model property. |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section`. The change is in the reference module and in the vector file only. The normative text does not change. |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `post.det.selection.nms` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/post/selection-nms.md` (no text edit) |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of the spec log has only skellytracker ADR-3S5G (`pre.resize.affine_person_crop`) and skellytracker ADR-50BW (`common.batch_conversion`). `intake_bundle.py list` gives no owner of `post.det.selection.nms`. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `b065f6e6850686b65bcd08ca944116d739aa62de`. `git status --porcelain` listed no file when I read the files. |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

| Item | Value |
|---|---|
| Property | `V-post.det.selection.nms-1` says: "The sidecar must not have `class_logits_output`, `top_k` or `max_detections`." The landed module `specs/model-sidecar/reference/post_det_selection_nms.py` does not check this sentence. `nms_settings` gets only the `nms` object. `decode_image` and `run` read the other `decode` fields, but they do not refuse the three fields. A decode block with one of the three fields thus decodes with no error. The module is the single executable meaning of the section, so a host that follows the module accepts a sidecar that the rule refuses. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | none needed: the property is a rule of the current spec text, not a property of a model. The evidence is the rule text (`post.det.selection.nms`, heading "Validation rules") and the landed module (the functions `nms_settings`, `decode_image` and `run` of `specs/model-sidecar/reference/post_det_selection_nms.py` at `b065f6e6850686b65bcd08ca944116d739aa62de`, SHA-256 `1e88d98b456b3b5ddbd289635b6edfa0c2f5f7837b5c5d2462c110e685b2f373`). |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided on 2026-11-06: the proposal is small. The module refuses all three fields exactly as the current text of `V-post.det.selection.nms-1` says. The proposal does not change the normative text. The user decided on 2026-11-06: the proposal notes the gap of `class_logits_output` with `selection: nms` (per-class NMS over per-class scores) in part 8. It does not propose a change for it. |
| Nearest section ID (the `id` in the section file's front matter) | `post.det.selection.nms` |
| Why the nearest section is wrong | The text is correct. The reference module of the section does not implement one sentence of the rule. The skellytracker session notice above says: "No vector case shows it." The vector file has no validator case for `V-post.det.selection.nms-1`. |
| Measured difference (number, image and script) | The case `suppress-overlap-and-threshold` with one more param: with `max_detections: 100`, `top_k: 1000` or `class_logits_output: logits`, the landed module returns `kept_rows` `[0, 2]`. The module of part 3 refuses each one with `ValueError` `V-post.det.selection.nms-1: ...`. No image is necessary. A reader can repeat the run with the function `run` of each file. No script is committed for this run (see "Open questions" in part 8). |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | no. `yolox-person` is not in the list. The proposal does not change the sidecar of the model. The model joins the list when skellytracker lands it with the verdict `describes`. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | Two rows are near the three fields: "`class_logits` with `selection: nms`" and "`nms.pre_nms_top_k`". This proposal does not add them. It refuses the fields that an author can use by mistake for them. No model of this exporter needs either feature now: each detector of this exporter is person-only. Part 8 gives the upstream pattern of the first row. |

**Context.** The facts below show why the refusal matters now. Each one is a reason, not a change of
this proposal.

- The package model of skellytracker keeps the old meaning of `max_detections` as a cap with the
  default `300`: `skellytracker/core/sidecar/model.py:223` (`max_detections: int = 300` in
  `DetectionDecodeSpec`) and `:234-235` (it checks only `> 0`), at skellytracker
  `b065f6e6850686b65bcd08ca944116d739aa62de` (branch `dom/sidecar-implementation`, secondary). This
  model is the pre-2.0.0 model: it has `requires_nms`, it forbids unknown keys
  (`model_config = ConfigDict(extra="forbid")`, `:32-33`), and it has no `selection` and no `nms`.
  So it cannot load a sidecar of the open target. No package code reads `decode.max_detections`.
  Change 9 of the summary of changes says that `max_detections` "no longer defaults to `300`" and is
  "valid only with `selection: none`".
- The package YOLOX person detector cuts its result after NMS with a caller value:
  `skellytracker/core/detectors/object_detectors/yolox/yolox_person_detector.py:144-145`
  (`result = result[: self.config.max_detections]`). This value is
  `YoloxPersonDetectorConfig.max_detections` (default `1`, `:73`). It is not the sidecar field. A
  port of the package to the open target can map the old sidecar cap to this caller cap by
  mistake. The refusal of the reference module stops a sidecar with `selection: nms` and
  `max_detections` before such a host reads it as a cap.
- Two pre-2.0.0 writers write `max_detections` with `requires_nms: true`. `requires_nms: true`
  becomes `selection: nms` at the migration to the open target. A direct migration of the decode
  block then fails `V-post.det.selection.nms-1`:
  - Qualcomm-Exporter writes `max_detections` equal to the anchor count (`896`) with
    `requires_nms: True` for the MediaPipe person detector
    ([`qai_sidecar.py:124-132`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_sidecar.py#L124-L132),
    [`qai_catalog.py:58`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/qai_catalog.py#L58)).
    Qualcomm-Exporter is out of scope of this revision.
  - Ultralytics-Exporter `_detection_decode` always writes `max_detections` and passes
    `requires_nms` through
    ([`yolo_sidecar.py:467-478`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_sidecar.py#L467-L478)).
    `build_yolo26_sidecar` and `build_yolo26_pose_sidecar` have the parameter
    `requires_nms: bool = False`
    ([`yolo_sidecar.py:490`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_sidecar.py#L490),
    [`yolo_sidecar.py:552`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_sidecar.py#L552)).
    No caller passes `True` at this commit
    ([`yolo_sidecar.py:627-629`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_sidecar.py#L627-L629)),
    so the path exists only as a parameter.
- The host of this exporter does not check the exclusion either. `NmsDecoder` checks
  `selection: nms`
  ([`onnx_runtime/decode_nms.py:226-227`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/onnx_runtime/decode_nms.py#L226-L227)).
  It reads `class_logits_output` as the name of its scores output
  ([`onnx_runtime/decode_nms.py:282`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/onnx_runtime/decode_nms.py#L282),
  [`pipeline/decoders.py:41`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/pipeline/decoders.py#L41)).
  It never reads `top_k` or `max_detections`. The host code is unchanged since
  `5dd5c93ac6555ac907ae2ebfbc27dc6de5e3c278`, the source commit of the landed module. The note of
  the module of part 3 says this.

## 2. Spec change

No normative text changes. The proposal changes only the reference module and the vector file of
the section. The single behaviour difference of part 3 comes from the existing rule of 2.4.

### 2.1 Sections

Changed section `post.det.selection.nms`, title "Selection: NMS", file
`specs/model-sidecar/post/selection-nms.md`. The section ID, the title, the kind, the selectors,
the front matter and the text do not change. No section-map row changes.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `specs/model-sidecar/reference/post_det_selection_nms.py` | whole file | Replace with the file of part 3. The diff with the landed file adds only the constant `EXCLUDED_FIELDS`, the function `check_excluded_fields`, its call in `decode_image` and note lines. |
| `specs/model-sidecar/vectors/post.det.selection.nms.yaml` | `cases` | Add the 3 validator cases of part 4 at the end. The other lines do not change. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the landing. |
| `specs/model-sidecar/post/selection-nms.md` | Implementer guidance, the bullet that starts "The OpenMMLab-Exporter host `onnx_runtime/decode_nms.py::NmsDecoder` passes each case of the vector file" | Optional, for the session. The bullet stays true. The session can add: "The host does not refuse `class_logits_output`, `top_k` or `max_detections`." |
| `specs/model-sidecar/changelog.md` | Summary of changes | none (2.6). |
| `post.det.selection.none`, `post.det.selection.top_k`, `post.det.outputs`, `post.det.decode` | | No edit. Their rules already agree with the exclusion (2.4). |

### 2.2 Fields table

No change.

### 2.3 Behaviour

No change. The forward steps 1 to 7 and the inverse do not change. A decode block with one of the
three fields is invalid, so it never reaches step 1.

### 2.4 Validation rules

No new rule and no changed rule. The module of part 3 implements the second sentence of the
existing rule:

- [ ] `V-post.det.selection.nms-1` A sidecar with `selection: nms` must have `nms` with `iou_threshold` and `score_threshold`. Each of these fields must be a float in `[0, 1]`. The sidecar must not have `class_logits_output`, `top_k` or `max_detections`. If `nms.class_agnostic` is present, it must be a boolean. If `nms.post_nms_top_k` is present, it must be a positive integer.

The rules that name one of the three fields do not change. They agree with the exclusion:

- `V-post.det.selection.none-1`: a sidecar with `selection: none` must not have `top_k`, `nms` or
  `class_logits_output`. `max_detections` is valid only there.
- `V-post.det.selection.top_k-1`: a sidecar with `selection: top_k` must have
  `class_logits_output` and `top_k`. It must not have `nms` or `max_detections`.
- `V-post.det.decode-1`, `V-post.det.decode-2`, `V-post.det.decode-3` and `V-post.det.decode-9`
  name `class_logits_output` as an output binding and a class source. They do not depend on the
  selection.
- The text of `post.det.outputs` (heading "Detection output semantics") says: "Use `class_logits`
  only with a `boxes` primary output and `decode.selection: top_k`." No `V-` rule holds this
  sentence. This proposal does not change it.

### 2.5 Selectors

No change: `decode.selection=nms`.

### 2.6 Changelog row

none. The proposal changes no normative text, no heading and no `V-` line, so the fingerprint of
the open target does not change. The reference module and the vector file are informative. A
skellytracker session can decide that a row is necessary (see "Open questions" in part 8).

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/post_det_selection_nms.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/post_det_selection_nms.py` (it exists; "Full section" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`: part 3 gives that file with the change) |
| Functions (one for each algorithm) | New: `check_excluded_fields` (the exclusion of `V-post.det.selection.nms-1`) and the constant `EXCLUDED_FIELDS`. Unchanged: `float_array`, `nms_settings`, `box_iou`, `hard_nms`, `select_nms`, `decode_image`, `run`. |

The file is the landed file at `b065f6e6850686b65bcd08ca944116d739aa62de` with the change. It
imports the same modules (`post_det_decode`, `post_unprojection`). It has no fixture.

- `check_excluded_fields(decode)` refuses each of the three keys that is present in the decode
  block. The check is for the key, as the rule text says "must not have". A key with any value
  fails. Each message starts with `V-post.det.selection.nms-1:` and tells where the intent of the
  author belongs:
  - `max_detections`: valid only with `selection: none`, as the fixed row count of the graph. A cap
    after the NMS is `nms.post_nms_top_k`.
  - `top_k`: the pair count of `selection: top_k`. A candidate limit before the NMS (mmdet
    `nms_pre`) has no field ("Authoring guidance" of `post.det.selection.nms`).
  - `class_logits_output`: valid only with `selection: top_k`.
- `decode_image` calls `check_excluded_fields(decode)` first, before `nms_settings`. This is the
  place where the module has the full decode block. `nms_settings` gets only the `nms` object.
  `run` builds the decode block from `params` and calls `decode_image`, so a case with one of the
  three fields in `params` also gets the refusal. `post_det_decode` refuses the values of the
  fields that its functions read in the same way.
- The source of the check is the rule text, not the host: the host does not check the exclusion
  (part 1). The note at the top of the file and the docstring of `check_excluded_fields` say this.
  The bullet list "Differences from the host code" of the note has one new bullet.

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/post.det.selection.nms.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/post.det.selection.nms.yaml` (it exists) |
| `verified_against` | The file-level entry of the current file does not change: `{OpenMMLab-Exporter: onnx_runtime/decode_nms.py::NmsDecoder}`. It covers the numeric cases only (skellytracker ADR-ESP4). The 24 numeric cases do not change. The host test `tests/test_decode_nms_vectors.py` passes at `c2e610e91fee0a961032e12737ff9147697a7e53` (55 tests). The 3 new cases are data-only validator cases. No validator ran them: the host has no validator, and the `validate` step of the section is `missing` in skellytracker. |
| Replaced case ids (`--replaces`) | The 24 current ids. The payload holds the full current file, so `land` sees each current id. Each of these cases is a byte copy: no key changes. The ids: `suppress-overlap-and-threshold`, `iou-equal-to-threshold-is-kept`, `iou-above-threshold-is-suppressed`, `box-area-adds-nothing`, `score-equal-to-score-threshold-is-dropped`, `confidence-threshold-is-strict`, `default-confidence-threshold`, `equal-scores-lower-row-wins`, `output-is-sorted-by-score`, `per-class-nms-keeps-both`, `class-agnostic-suppresses-across-classes`, `post-nms-top-k-keeps-the-highest`, `post-nms-top-k-counts-survivors`, `post-nms-top-k-larger-than-the-survivors`, `class-id-map-drop-comes-before-nms`, `is-person-only-drop-comes-before-nms`, `no-class-source-uses-person-class-id`, `class-id-base`, `box-format-cxcywh`, `no-candidate-passes`, `size-filter-comes-after-nms`, `size-filter-comes-after-post-nms-top-k`, `nms-comes-before-the-clamp`, `size-filter-uses-source-pixels`. |

The new cases, one for each field, at the end of the file:

- `nms-has-no-max-detections`: `max_detections: 100` with `selection: nms`.
- `nms-has-no-top-k`: `top_k: 1000` with `selection: nms`.
- `nms-has-no-class-logits-output`: `class_logits_output: logits` with `selection: nms`, and a
  `class_logits` output `[-1, -1, 80]`. The class logits are the class source, so the sidecar does
  not set `is_person_only` (`V-post.det.decode-9`).

Each case has `function: none` and `expect: {failed: [V-post.det.selection.nms-1]}`, in the form
of the validator cases of `specs/model-sidecar/vectors/post.det.decode.yaml`. Each sidecar shows
only its `outputs` and `decode` blocks and fails only this rule of the section.

**Why no numeric case runs the check.** Part 4 of the change proposal template says: "Do not give a
run-time function a sidecar value that a validation rule refuses. Write a validator case for that
rule." So an `{error: V-post.det.selection.nms-1}` case through `run` is not allowed. The template
asks for a numeric case for each branch of the algorithm. The algorithm does not change, so the 24
current cases still cover each branch. The refusal is a check of the decode block, not a branch of
the algorithm. Part 1 gives the run that shows the refusal.

**Runs on the payload.**

- `fill` of `tools/make_vectors.py` (skellytracker `b065f6e6850686b65bcd08ca944116d739aa62de`,
  `python -B`, `--reference <payload>/reference`) stops with `TypeError: 'NoneType' object is not
  callable`. The file-level `checks: [float32-stable]` applies to each case.
  `make_vectors.run_checks` runs it on a `function: none` case, with no function. No current
  vector file has both a file-level `checks` and a `function: none` case. This is a defect of the
  tool, not of the author keys: a case cannot opt out of a file-level check, and a case-level copy
  of `float32-stable` fails `land`, which keeps the file-level keys of the current file. See "Open
  questions" in part 8.
- `fill` with a local shim that skips the checks of a `function: none` case (the shim changes no
  skellytracker file) prints no problem. It changes no `expect` and no key of the 24 numeric cases.
  It only rewraps the `note` text of two new cases (the emitter of skellytracker). The payload file
  holds that output. The first 429 lines of the payload file are a byte copy of the current file.
- The module of part 3 and the landed module give equal outputs on each of the 24 numeric cases.
- The decode block of the `rtmdet-person` reference example and the decode block of the
  `yolox-person` sidecar pass `check_excluded_fields`. On 200 random candidate sets with the
  `yolox-person` decode block, the two modules give equal rows, scores, class ids and boxes.

## 5. Parity evidence

No new run. The change refuses only an invalid decode block. For a decode block without the three
fields, `check_excluded_fields` returns, and `decode_image` runs the same statements as the landed
file. The parity of the landed file thus stays the parity of this file.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | The gates and the controls of the yolox-person reference swap ([OpenMMLab-Exporter ADR-3NNK](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/decisions/entries/3NNK-yolox-reference-swap.md)). No new gate. |
| Test images (paths or dataset IDs), and the branch that each image runs | The images of ADR-3NNK (432 image entries, 6 sizes, fp32 and fp16). The refusal branch has no image: the sidecar of the model has none of the three fields. |
| Upstream reference: library, version, config and command | As in ADR-3NNK. No new run. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | As in ADR-3NNK. No new run. |
| Preprocessed input: maximum absolute difference for each image | As in ADR-3NNK. No new run. |
| Row count for each image: sidecar path and upstream | As in ADR-3NNK (12296 rows on 432 image entries). No new run. |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | As in ADR-3NNK. The module of part 3 and the landed module give equal outputs on the 24 numeric cases and on 200 random candidate sets with the `yolox-person` decode block (part 4). |
| Result (`pass`, `fail` or `to run`) | `pass`, from the ADR-3NNK run of the landed file and the equal code path of part 3. The ADR-3NNK run did not load this file. |
| Script path in the exporter repo | `decisions/scripts/yolox_person_reference_swap.py` (the ADR-3NNK run) |
| Exporter commit of the script | [`53a48480d0b715f9b726963bce002ddb503b050b`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/53a48480d0b715f9b726963bce002ddb503b050b/decisions/scripts/yolox_person_reference_swap.py) |
| Command | none (no new run) |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | No decode change. The validator of the open target gets the check. |
| Dispatch point | The sidecar load (`skellytracker/core/sidecar/model.py`, the detection `decode` block). |
| Validator changes (`model.py`, with rule IDs) | `V-post.det.selection.nms-1`: when `DetectionDecodeSpec` gets `selection` and `nms`, a model validator refuses `class_logits_output`, `top_k` and `max_detections` with `selection: nms`. Remove the default `max_detections: int = 300` (`model.py:223`): the field has no default (change 9). Keep `YoloxPersonDetectorConfig.max_detections` as a caller cap. Do not read it from the sidecar. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | A test that loads the 3 validator cases of part 4 and expects each one to fail with `V-post.det.selection.nms-1`, for example in `skellytracker/tests/sidecar/test_model_validation.py`. No golden parity test: the decode does not change. |
| Existing code that the change touches | `skellytracker/core/sidecar/model.py` (`DetectionDecodeSpec`, `:217-235`); `skellytracker/tests/sidecar/test_model_validation.py` (`test_max_detections_must_be_positive`, `:293`); `skellytracker/core/detectors/object_detectors/yolox/yolox_person_detector.py:144-145` (the caller cap; for the implementer: keep it separate from the sidecar). |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `yolox-person` | none. The writer `_decode_block` writes none of the three fields ([`yolox_person/sidecar.py:97-118`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/yolox_person/sidecar.py#L97-L118)). | none required. `NmsDecoder` does not refuse the three fields, and it reads `class_logits_output` as its scores output (part 1). No sidecar of this exporter uses that path. A later exporter change can refuse the three fields. This proposal does not change the host. |
| OpenMMLab-Exporter | `rtmdet-person` | none. The decode block has none of the three fields. | as above |
| OpenMMLab-Exporter | `rtmo-body7` | none (`selection: none`) | none |
| Ultralytics-Exporter | `yolo26`, `yolo26-body` | none (`selection: none` with `max_detections: 300`) | none. A future `requires_nms=True` path of `_detection_decode` must not write `max_detections` with `selection: nms` (part 1). |
| Roboflow-Exporter | RF-DETR (no example) | none (`selection: top_k`, the guidance of `post.det.selection.top_k`) | none |
| Qualcomm-Exporter | MediaPipe person detector (out of scope of this revision) | none now. At the migration, the decode block must not keep `max_detections` (`896`) with `selection: nms`. The guidance of `post.det.selection.nms` gives `post_nms_top_k: 1` for the upstream app. | none |

**Reference examples that the change makes invalid.** none. The rule does not change, and no
example breaks the second sentence of `V-post.det.selection.nms-1`. `rtmdet-person` is the only
example with `selection: nms`, and its decode block has none of the three fields. `yolo26`,
`yolo26-body` and `rtmo-body7` use `selection: none`. `rtmw-wholebody` has no detection decode
block. There is no RF-DETR example.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| none | | | |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none (no sidecar changes) |
| Writer code (file, function and commit) | none |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep the landed module, which does not check the second sentence of the rule. | The module is the executable meaning of the section. A host that follows it accepts a sidecar that the rule refuses, and an old writer that keeps `max_detections` as a cap gets an uncapped result with no error. | Part 1 |
| Change the text: allow `max_detections` with `selection: nms` as a host cap. | The user decided on 2026-11-06 not to change the normative text. Change 9 removed the cap meaning. `nms.post_nms_top_k` is the cap after NMS. | Part 1, change 9 |
| Change the text: allow `top_k` as a candidate limit before NMS (mmdet `nms_pre`). | No field by design: the row "`nms.pre_nms_top_k`" of "Considered and deliberately not added", and the "Authoring guidance" of `post.det.selection.nms` ("`nms_pre=1000` has no field"). | changelog |
| Put the check in `nms_settings`. | `nms_settings` gets only the `nms` object. It cannot see the other `decode` fields. | Part 3 |
| Put the check in `run` only. | `run` is the wrapper of the vector cases. A host follows `decode_image`. | Part 3 |
| An `{error: V-post.det.selection.nms-1}` case through `run`. | The template does not allow a refused sidecar value in a run-time function. The validator case is the allowed form. | Part 4 |
| A full validator function in the module (`failed` for all rules of the section). | It is larger than the defect. No reference module of the spec has a validator function. The data-only case form exists for this. | none |
| Also allow `class_logits_output` with `selection: nms` (per-class NMS over per-class scores). | Not proposed. See "Goal not met: per-class NMS over per-class scores" below. | below |

**Goal not met: per-class NMS over per-class scores.** This is a note for a later content change.
It is not a change of this proposal.

- The pattern is real upstream. A multi-class detector gives one score for each row and each class,
  and the NMS runs for each class over the scores of that class:
  - mmdet 3.3.0, multi-class RTMDet: `BaseDenseHead._predict_by_feat_single` calls
    `filter_scores_and_topk` on the score of each (row, class) pair
    ([`mmdet/models/dense_heads/base_dense_head.py:391-395`](https://github.com/open-mmlab/mmdetection/blob/44ebd17b145c2372c4b700bfb9cb20dbd28ab64a/mmdet/models/dense_heads/base_dense_head.py#L391-L395);
    secondary here: this proposal did not read mmdet, skellytracker ADR-Q6W6 cites these lines).
    The NMS that follows runs for each class.
  - mmdeploy exports its multi-class NMS as the ONNX `NonMaxSuppression` operator: the scores are
    `(N, num_boxes, num_classes)`, and `_multiclass_nms` permutes them to `[N, C, Q]` (mmdeploy
    [`mmdeploy/mmcv/ops/nms.py:267-300`](https://github.com/open-mmlab/mmdeploy/blob/bc75c9d6c8940aa03d0e1e5b5962bd930478ba77/mmdeploy/mmcv/ops/nms.py#L267-L300),
    `bc75c9d6c8940aa03d0e1e5b5962bd930478ba77`, tag `v1.3.1`).
  - Ultralytics `non_max_suppression` on a raw YOLOv8 or YOLO11 head: with `multi_label`, each
    (row, class) pair above `conf_thres` becomes a candidate, and the validator sets
    `multi_label=True` (ultralytics 8.4.184 `utils/nms.py:117-127` and
    `models/yolo/detect/val.py:174`, installed copy in the Ultralytics-Exporter `.venv`). Without
    `multi_label`, it keeps the best class of each row.
  - The ONNX `NonMaxSuppression` operator, which `post.det.selection.nms` names as its model, takes
    `scores` `[num_batches, num_classes, spatial_dimension]` (onnx 1.23.2
    `onnx/defs/object_detection/defs.cc:113`, installed copy in the OpenMMLab-Exporter `.venv`).
- The `nms` mode of the spec takes one score for each row: `scores_output` `[B, Q]`, or
  `score_field` with `class_field`. An exporter of a multi-class model must thus reduce the scores
  to the best class of each row in the graph (argmax), and the host then runs NMS for each class.
  This is not per-class NMS over per-class scores. With per-class NMS, one box can stay as two
  classes. With argmax first, it stays as one class only, and a class with a lower score on that
  box can lose a detection.
- The row "`class_logits` with `selection: nms`" of "Considered and deliberately not added" already
  records this. It gives the RTMDet-tiny numbers: AP 0.4114 with the pairs against 0.4112 for
  PyTorch, and a loss of 0.0051 AP and 0.031 AR for the best class of each row.
- No model of this exporter needs it now: each detector of this exporter is person-only
  (`rtmdet-person`, `yolox-person`). The host of this exporter already reads `[B, Q, C]` scores
  (part 1), so a later proposal can use it as host code.
- When a multi-class model comes into the scope of a revision, a new proposal can let
  `class_logits_output` (or `scores_output` with `class_axis`) feed the `nms` mode, with a rule for
  each (row, class) pair. That proposal changes `V-post.det.selection.nms-1` and the
  `post.det.outputs` sentence of 2.4.

**Open questions for the skellytracker session.**

1. `fill` and `land` cannot accept a `function: none` case in a file with a file-level `checks`
   (part 4). The tool or the vector form needs a change (for example, `run_checks` skips the
   checks of a `function: none` case). This is a workflow and tool change, so this bundle does not
   hold it.
2. The kind `changed section` with no text change: is a proposal the correct form, or does the
   session land the module and the cases in a non-spec commit ("an exporter reference
   implementation of the current text, tools and vectors")? The session notice asked for a
   proposal. Procedure B step 6 needs each behaviour difference to come from part 2: here it comes
   from the unchanged rule of 2.4.
3. Changelog row: none (2.6). The session can add one.
4. Part 5 has no new run. The session can ask for a run of
   `decisions/scripts/yolox_person_reference_swap.py` with this file.
5. Part 1 cites a run with no committed script. The exporter can commit a small comparison script
   with a decision entry if the session needs it.
6. The 3 new cases give `V-post.det.selection.nms-1` its first case. The generated Gate column can
   change. This proposal does not claim a Gate item.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [ ] The intake names the bundle ID of this proposal. Not yet: `intake.md` of
      `model-yolox-person@openmmlab-exporter` v1 does not name it. The next version of that bundle
      must name it.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [ ] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its
      `expect`. Partly: the file exists. `fill` stops on the tool defect of part 4. `fill` with a
      local shim wrote the file and changed no `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
      `pack` did not run.
