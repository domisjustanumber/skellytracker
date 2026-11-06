# Change proposal: normalize-input-dtype

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | Each normalization mode casts its result to `input.dtype`; a `uint8` input needs `none` and an 8-bit resize; `int8` is not an input dtype; the `custom` defaults |
| Slug | `normalize-input-dtype` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `33e657d957872999aa04eb46d977eea1634be365` |
| Model, and its `model` bundle ID | `yolox-person` (`model-yolox-person@openmmlab-exporter`) and `rtmw-wholebody133` (`model-rtmw-wholebody133@openmmlab-exporter`). Both use `pre.normalize` with a `float32` input. Neither model needs a value that this proposal adds or removes. |
| Intake rows with the verdict `near-miss` or `gap` | none. The rows T10 (normalization) and T11 (cast to `input.dtype`) of both intakes are `exact`. The proposal comes from the reference step of `pre.normalize`: the skellytracker response of 2026-11-06 to `model-yolox-person@openmmlab-exporter` found that the reference module of that bundle does not implement the current text (part 1). |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `pre.normalize` (primary). The proposal also changes `common.input` (rule `V-common.input-2`). |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/normalization.md`; also `specs/model-sidecar/common/input.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of the spec log holds ADR-3S5G (`pre.resize.affine_person_crop`) and ADR-50BW (`common.batch_conversion`) only. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `b065f6e6850686b65bcd08ca944116d739aa62de` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

**Section owner.** No bundle in `intakes/` and no record in `specs/model-sidecar/proposals/` owns
`pre.normalize` or `common.input`. `intake_bundle.py list` at `b065f6e6` gives the owners
`common.batch_conversion` and `pre.resize.affine_person_crop` only. Thus this is a new proposal
("Proposal forms" and "Section owner" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`).

## 1. Gap

| Item | Value |
|---|---|
| Property | The dtype rules of the normalization step. (a) Each mode casts its result to the `input.dtype` entry of the selected precision. The mode table states the cast only for `none`. (b) A `uint8` input is valid only with the resolved normalization `none` and an 8-bit resize. No rule states this. (c) `int8` is not an input dtype. `V-common.input-2` allows it. (d) The check of the top-level `input.normalization` applies also when `normalization_by_precision` covers the precision. The current rule states this. Only the reference module and the host must follow it. (e) A `custom` object with no `scale`, `mean` or `std` uses `scale: 1`, `mean: [0, 0, 0]` and `std: [1, 1, 1]`. The text gives the default of `scale` only in a YAML comment, and no default for `mean` and `std`. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | The gap is in the spec text. No upstream model needs a new value. The evidence is the spec text, the hosts and the writers. (1) The cast of every mode: skellytracker ADR-PHJ3 (accepted 2026-11-04), Decision item 2: "The normalization then takes the result and casts it to `input.dtype`." The heading "Compute dtype" in `specs/model-sidecar/pre/interpolation.md` says the same. ONNX Runtime refuses a tensor whose dtype is not the dtype of the graph input (part 1, Measured difference). (2) The OpenMMLab-Exporter host casts every mode ([`onnx_runtime/preprocess.py:264-265`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L264-L265)), refuses `uint8` with a mode other than `none` ([`:261-262`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L261-L262)), has no `int8` ([`:63`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L63)), gives the `custom` defaults ([`:158-160`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L158-L160)) and checks the top-level value also with an override ([`:168-179`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L168-L179), [`:198`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L198)). (3) The skellytracker package gives the same `custom` defaults: `CustomNormalization` has `scale: float = 1.0` (`skellytracker/core/sidecar/model.py`), and `build_normalization_fn` uses `mode.mean or [0.0, 0.0, 0.0]` and `mode.std or [1.0, 1.0, 1.0]` (`skellytracker/core/detectors/processing/image_preprocessing.py`). (4) The Ultralytics-Exporter writer reads the input dtype from the graph. It names `TensorProto.INT8` `int8` ([`yolo_sidecar.py:83-86`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L83-L86)). It writes the override `none` for a precision whose input dtype is `uint8` or `int8` ([`yolo_sidecar.py:391-393`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L391-L393)). (5) The mode table names YOLOX as a graph that normalizes internally. The YOLOX data preprocessor of the HumanArt configs has no `mean` and no `std`, so the model takes raw 0-255 BGR pixels, and the graph does not normalize: mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`), [`projects/rtmpose/yolox/humanart/yolox_s_8xb8-300e_humanart.py:11-20`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/projects/rtmpose/yolox/humanart/yolox_s_8xb8-300e_humanart.py#L11-L20). |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided on 2026-11-06 to write this proposal for the dtype rules, in place of a reference module that implements only the current text. The part 3 module of this proposal becomes the reference implementation of `pre.normalize`. Thus the bundles `model-yolox-person@openmmlab-exporter` and `model-rtmw-wholebody133@openmmlab-exporter` skip the reference step for this section (the second skip rule of "When to do the step" in `specs/model-sidecar/model-addition-workflow/reference-implementations.md`). The user decided on 2026-11-06 to remove `int8` from the values of `input.dtype` (`V-common.input-2`). The values of `outputs[].dtype` (`V-common.outputs-2`) keep `int8`. |
| Nearest section ID (the `id` in the section file's front matter) | `pre.normalize`; for `int8`, `common.input` |
| Why the nearest section is wrong | The skellytracker response of 2026-11-06 to `model-yolox-person@openmmlab-exporter` lists four differences between the reference module of that bundle and the current text: (a) the module casts the result of each mode to `input.dtype`, but the mode table states the cast only for `none`; (b) the module refuses `uint8` with a mode other than `none`, but no rule refuses that sidecar; (c) the module refuses `int8`, which `V-common.input-2` allows; (d) the module accepted a missing top-level `input.normalization` when the override covers the precision, but `V-pre.normalize-1` requires it. For (a), the text of `pre.normalize` disagrees with ADR-PHJ3 and with `pre.resize.interpolation`, which say that the normalization casts to `input.dtype`. A host that follows only the mode table gives a `float32` tensor to a `float16` graph input, and ONNX Runtime refuses it. For (b), a mode other than `none` gives fractional values, and a `float32` resize gives fractional values. The cast of a fractional value to `uint8` is not defined. The spec log names this open case: "the cast of a `float32` resize to an integer `input.dtype`" ("Spec defects" in `specs/model-sidecar/decisions/open-work.md`). For (c), no mode gives a defined `int8` value: with `none`, the pixels 128 to 255 do not fit, and the other modes give fractional values. For (d), the rule is clear. The module and the host now follow it, so the text does not change. For (e), `V-pre.normalize-1` allows a `custom` object with no `mean` or `std` ("If `mean` or `std` is present ..."), but the text gives no value for them. |
| Measured difference (number, image and script) | An uncommitted check of this draft (secondary; NumPy 2.5.4, ONNX 1.23.2, ONNX Runtime 1.31.1 on the CPU, a one-node `Identity` graph). (1) A `float32` tensor for a `float16` graph input: ONNX Runtime raises `INVALID_ARGUMENT : Unexpected input data type. Actual: (tensor(float)) , expected: (tensor(float16))`. (2) The cast to `float16` changes the `unit_float` values of the 4 vector pixels by up to 1.3e-4, and the `imagenet` values by up to 8.6e-4. The cases `unit-float-float16` and `imagenet-float16` of part 4 hold these values. Both are more than the vector tolerance 1e-5. (3) The `imagenet` values of the 4 vector pixels, cast to `uint8`, give `[255, 254, 254]`, `[2, 2, 2]`, `[255, 0, 2]` and `[1, 0, 255]`, with no warning. (4) `float32` resize values cast to `uint8`: `127.5` gives `127` (a truncation, not a rounding), `-63.66` gives `193` and `314.37` gives `58`, with no warning. A `cubic` resize in `float32` gives values from -63.66 to 314.37 on noise (skellytracker ADR-PHJ3, Evidence). (5) The `none` pixels cast to `int8`: `200` gives `-56` and `255` gives `-1`. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes for `rtmw-wholebody133` (OpenMMLab-Exporter: RTMW). `yolox-person`: no. This proposal does not change a value of that model, so it does not add the model to the list. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The row "Soft-NMS / per-class IoU, masks, multi-input models, quantized outputs" is about outputs. This proposal keeps `int8` in the output dtypes. |

**Primary evidence.** The spec text (skellytracker ADR-PHJ3 and the heading "Compute dtype" of
`pre.resize.interpolation`), the committed host code of OpenMMLab-Exporter at
`7bc72b45137faa4b211d05a38f58812ffae5a109` and the committed writer of Ultralytics-Exporter at
`f52ef687a7a651447ff289d0e40a7856c2b7d50c`. The numbers of "Measured difference" are secondary.
The vector cases of part 4 hold the cast numbers (2).

## 2. Spec change

The relative links of the proposed text resolve from the record path
`specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the
section file (an editorial fix). The new rule ID and the new heading names are text, not links.

### 2.1 Sections

Changed section `pre.normalize`, title "Normalization", file
`specs/model-sidecar/pre/normalization.md`. The section ID, the title, the kind and the selectors do
not change. Changed section `common.input`, title "Input", file `specs/model-sidecar/common/input.md`.
The section ID, the title, the kind and the selectors do not change. No section-map row changes.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.normalize` | front matter, `implemented_by.validate` | Replace the comment with: `# partial. NamedNormalizationMode has imagenet_bgr and imagenet_rgb, not imagenet. CustomNormalization has a color_format field. Nothing checks that input.color_format is present. InputSpec defaults input.normalization to imagenet_bgr (V-pre.normalize-1). Nothing checks V-pre.normalize-3.` |
| `pre.normalize` | front matter, `implemented_by.forward` | Replace the last sentence "none and unit_float return float32, not input.dtype." with "No mode casts to input.dtype: build_normalization_fn returns float32, and preprocess_image casts the tensor to float32." The code casts each mode to `float32` (`build_normalization_fn`) and casts the tensor to `float32` again (`preprocess_image`, its last line). |
| `pre.normalize` | front matter, `vectors` | No change (`vectors/pre.normalize.yaml`). |
| `pre.normalize` | Behaviour, the mode table | The rows `none` and `custom` of 2.3. |
| `pre.normalize` | Behaviour, after the mode table | The new paragraph "Cast to `input.dtype`" of 2.3. |
| `pre.normalize` | Behaviour, the custom-mode YAML | The comments of 2.3. |
| `pre.normalize` | Behaviour, the per-precision YAML | The comment of 2.3. |
| `pre.normalize` | Validation rules | Add `V-pre.normalize-3` (2.4). |
| `pre.normalize` | Implementer guidance | Replace the first bullet and the third bullet (the OpenMMLab-Exporter host) with the two bullets of 2.3. Replace the bullet that starts "The Ultralytics-Exporter writes `normalization_by_precision`" with the bullet of 2.3. |
| `common.input` | front matter, `implemented_by.validate` | Add to the comment: `OnnxDtype of InputSpec.dtype allows int8 (V-common.input-2).` |
| `common.input` | front matter, `vectors` | `vectors: vectors/common.input.yaml` (a new data-only file, part 4). |
| `common.input` | Fields, the row `dtype` | Add the sentence of 2.2. |
| `common.input` | Validation rules | Change `V-common.input-2` (2.4). |
| `common.input` | Authoring guidance, the bullet "Write `input.dtype` from the graph for each precision." | Add the sub-bullet of 2.3. |
| `specs/model-sidecar/decisions/open-work.md` | Spec defects, the item "the arithmetic precision of the geometry and of the pixel math" | Change "Two cases of ADR-PHJ3 are open: a fractional `pad_value` with `compute_dtype: uint8`, and the cast of a `float32` resize to an integer `input.dtype`;" to "One case of ADR-PHJ3 is open: a fractional `pad_value` with `compute_dtype: uint8`;". `V-pre.normalize-3` and the removal of `int8` close the second case: no valid sidecar casts a `float32` resize to an integer input. |
| `specs/model-sidecar/changelog.md` | Summary of changes | The row of 2.6. |
| `specs/model-sidecar/vectors/pre.normalize.yaml` | notes | Add the two notes of the part 4 file that start "`dtype` is the entry of `input.dtype`" and "A validator case". `land` keeps the file keys of the current file, so the session adds them. |
| `specs/model-sidecar/vectors/pre.normalize.yaml` | cases | The new cases of part 4. |
| `specs/model-sidecar/vectors/common.input.yaml` | new file | The 2 data-only cases of part 4. |
| `specs/model-sidecar/reference/pre_normalize.py` | new file | The file of part 3. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `pre.resize.interpolation`, `pre.resize.none` | | No edit. "Compute dtype" already says that the normalization casts to `input.dtype`. `V-pre.resize.none-1` already forbids `compute_dtype` for `none`. |
| `common.outputs` | | No edit. `V-common.outputs-2` keeps `int8`. |
| `specs/model-sidecar/README.md` | Overview, section map, validation index | No edit. The validation index links to the Validation rules of each section and does not repeat a rule. |
| `specs/model-sidecar/examples/` | | No edit (part 7). |

### 2.2 Fields table

`pre.normalize`: no change.

`common.input`, the row `dtype`: add one sentence at the end of the Description:

| Field | Type | Required | Description |
|---|---|---|---|
| `dtype` | object | yes | (current text, unchanged) Each value is `float32`, `float16` or `uint8` (`V-common.input-2`). |

### 2.3 Behaviour

**The mode table of `pre.normalize`.** Replace the rows `none` and `custom`. The rows `unit_float`
and `imagenet` do not change.

| Mode | Host behavior | Typical use |
|------|---------------|-------------|
| `none` | Pass pixel values (0–255) unchanged. Channel order from `input.color_format`. | Graphs that take raw 0–255 pixels: graphs that normalize internally, and models with no upstream `mean` and `std`, for example YOLOX and RTMO |
| `custom` | `(pixel * scale - mean) / std` on 0–255 channel values. `mean` and `std` are in the channel order of `input.color_format`. Each key other than `mode` is optional. When a key is absent, its value is `scale: 1`, `mean: [0, 0, 0]` or `std: [1, 1, 1]`. | Rare exports that match no named mode |

**New paragraph after the mode table:**

> **Cast to `input.dtype`.** Each mode casts its result to the `input.dtype` entry of the selected
> precision ([Input](../../common/input.md#fields)). The cast is the last step of this section. The
> `pixel` of each formula is the value that the resize gives, in `input.resize.compute_dtype`
> ([Compute dtype](../../pre/interpolation.md#compute-dtype)). For `method: none`, it is the 8-bit
> source pixel. A `float16` input rounds each result to `float16`. A `uint8` input is valid only
> with `none` and with an 8-bit resize (`V-pre.normalize-3`), so its cast keeps each value.

**The custom-mode YAML.** Change the comments of `mean` and `std`:

```yaml
input:
  color_format: rgb              # required; the order of mean and std
  normalization:
    mode: custom
    scale: 0.00392156862745098   # optional; default 1.0
    mean: [0.0, 0.0, 0.0]        # optional; default [0.0, 0.0, 0.0]
    std: [1.0, 1.0, 1.0]         # optional; default [1.0, 1.0, 1.0]
```

**The per-precision YAML.** Change the comment. The YAML does not change.

```yaml
# For an artifact whose graph takes raw uint8 pixels. A uint8 input needs the resolved
# normalization none and an 8-bit resize (V-pre.normalize-3). The Ultralytics exporter writes
# this override for a precision whose input dtype is uint8. The current YOLO26 exports take
# float32 input, so they need no override.
input:
  dtype: {fp32: float32, fp16: uint8}
  color_format: rgb
  normalization: unit_float
  normalization_by_precision:
    fp16: none
```

**Implementer guidance of `pre.normalize`.** Replace the first bullet with:

- The OpenMMLab-Exporter host takes BGR frames. Its mode `imagenet_bgr` (`imagenet` with
  `color_format: bgr`) applies the statistics directly to the BGR canvas. Its mode `imagenet_rgb`
  (`imagenet` with `color_format: rgb`) flips the channels to RGB first. It computes each mode in
  float32 and then casts the result to the input dtype: `float32`, `float16` or `uint8`. It refuses
  `uint8` with a mode other than `none`. It has no `int8`. (OpenMMLab-Exporter
  [`onnx_runtime/preprocess.py:63`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L63),
  [`onnx_runtime/preprocess.py:214-305`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L214-L305))

Replace the third bullet with:

- That host supports the modes `none`, `unit_float`, `imagenet` and `custom`, and the host names
  `imagenet_bgr` and `imagenet_rgb` at the top level. It checks the top-level
  `input.normalization` also when `normalization_by_precision` covers the precision. Its `custom`
  defaults are `scale: 1`, `mean: [0, 0, 0]` and `std: [1, 1, 1]`. Its function has no
  `input.resize.compute_dtype`. (OpenMMLab-Exporter
  [`onnx_runtime/preprocess.py:142-211`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L142-L211))

Replace the bullet that starts "The Ultralytics-Exporter writes `normalization_by_precision`" with:

- The Ultralytics-Exporter writes `normalization_by_precision: {p: none}` only for a precision whose
  graph input dtype is `uint8` or `int8`. For `uint8`, the override meets `V-pre.normalize-3`. An
  `int8` graph input has no valid `input.dtype` (`V-common.input-2`). A test uses a `uint8` fixture.
  No real YOLO26 export triggers it, because every YOLO26 artifact takes float32 input.
  (Ultralytics-Exporter [`yolo_sidecar.py:391-393`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L391-L393);
  Ultralytics-Exporter [`tests/test_yolo_sidecar.py:274-284`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/tests/test_yolo_sidecar.py#L274-L284);
  Ultralytics-Exporter `exports/detectors/object_detectors/yolo26/yolo26.yaml:7`, untracked output)

**Authoring guidance of `common.input`.** Add this sub-bullet under "Write `input.dtype` from the
graph for each precision.":

  - An `int8` graph input has no valid `input.dtype` (`V-common.input-2`). With `none`, the pixels
    128 to 255 do not fit in `int8`: `200` becomes `-56` and `255` becomes `-1` (NumPy 2.5.4). The
    other modes give fractional values. Export the graph with a `uint8` or a float input.

The change has no inverse. The section has no Inverse.

### 2.4 Validation rules

New rule of `pre.normalize`:

- [ ] `V-pre.normalize-3` If the `input.dtype` entry of a precision is `uint8`, the resolved normalization of that precision must be `none`. Then `input.resize.compute_dtype` must be absent or `uint8`. The other modes and a `float32` resize give fractional values, and the cast of a fractional value to `uint8` is not defined.

Changed rule of `common.input` (only the last sentence changes; `int8` goes):

- [ ] `V-common.input-2` `input.dtype` must be present. Its keys must be precision keys ([V-common.sizes_and_artifacts-6](../../common/sizes-and-artifacts.md#validation-rules)). The keys must cover the precisions that `precision_artifacts` declares ([ADR-JAA4](../../../../decisions/entries/JAA4-one-batch-field.md)). Its values must be `float32`, `float16` or `uint8` ([ADR-90CE](../../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

The session adds the link of the decision entry of this proposal to both rules.

Unchanged rules that name a value of the change:

- `V-pre.normalize-1`: unchanged. It requires `input.normalization` with no condition, so (d)
  needs no text change. Its sentence "If `mean` or `std` is present, it must have length 3." stays.
  Behaviour now gives the values for an absent key (e).
- `V-pre.normalize-2`: unchanged. An override is a named mode string. `V-pre.normalize-3` reads the
  resolved mode, so an override `none` can make a `uint8` precision valid.
- `V-common.outputs-2`: unchanged. The output dtypes keep `int8` (plan decision of part 1).
- `V-pre.resize.interpolation-1`: unchanged. It gives the values of `compute_dtype`.
  `V-pre.normalize-3` only limits the value for a `uint8` input.
- `V-pre.resize.none-1`: unchanged. A `none` resize has no `compute_dtype`, so a `uint8` input with
  `method: none` meets the second sentence of `V-pre.normalize-3`.
- `V-common.sizes_and_artifacts-6`: unchanged. The precision keys are `fp32` and `fp16`.

### 2.5 Selectors

No change: `input.normalization=none`, `input.normalization=unit_float`,
`input.normalization=imagenet` and `input.normalization.mode=custom`. `common.input` has no
selectors.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Input | Each normalization mode casts its result to the `input.dtype` entry of the selected precision. A `custom` object gives the defaults `scale: 1`, `mean: [0, 0, 0]` and `std: [1, 1, 1]`. `V-pre.normalize-3`: a `uint8` input needs the resolved normalization `none` and `input.resize.compute_dtype` absent or `uint8`. `V-common.input-2`: the input dtypes are `float32`, `float16` and `uint8`. `int8` goes. The output dtypes keep `int8`. | user decision 2026-11-06: the mode table stated the cast only for `none`, the cast of a fractional value to `uint8` was not defined, and no mode gives a defined `int8` input (the decision entry of this proposal) | [Normalization](../../pre/normalization.md#behaviour), [Input](../../common/input.md#validation-rules) |

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/pre_normalize.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_normalize.py` (new file) |
| Functions (one for each algorithm) | `custom_parameters` (the `custom` check and defaults), `check_top_level` (`V-pre.normalize-1`), `check_overrides` (`V-pre.normalize-2`), `resolve_normalization` (the resolution order), `input_dtype` (the values of `input.dtype`), `check_uint8` (`V-pre.normalize-3`), `source_pixels` (the pixels in the compute dtype), `tensor_order` (the channel order), `normalize_none`, `normalize_unit_float`, `normalize_imagenet`, `normalize_custom`, `cast_to_input_dtype` (the cast), `normalize` (the full step), `check_rules` (rules -1, -2 and -3 of one `input` block); `run` for the cases; helpers `is_number` and `mode_name` |

**Full section.** skellytracker has no reference implementation of `pre.normalize`. Thus the file
implements the full section as changed: the resolution, the channel order, the four modes, the cast
and the rules `V-pre.normalize-1`, `-2` and `-3` ("Full section" in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md`). The section has no
Inverse.

**`common.input` has no module.** The proposal changes a validation rule of `common.input`, but
"Full section" does not apply to it. `common.input` has no algorithm. "When to do the step" names
`input.dtype` as a part of the spec without an algorithm that needs no reference implementation, and
the Payload table of `specs/model-sidecar/model-addition-workflow/hand-over.md` asks for a reference
file only for a changed section that has an algorithm. The cast of `pre.normalize` needs the set of
values of `input.dtype`. Thus `input_dtype` of the part 3 file refuses a value outside the set with
the rule ID `V-common.input-2`. The data-only validator cases of that rule are in the vector file of
`common.input` (part 4), because a validator case goes in the vector file of the section that owns
the rule.

**Imports.** The file imports `pre_resize_interpolation` (the landed module of
`pre.resize.interpolation`). It calls `pre_resize_interpolation.compute_dtype` for the dtype of
`input.resize.compute_dtype` and for the rule `V-pre.resize.interpolation-1`. It has no fixture.

**Source.** OpenMMLab-Exporter `onnx_runtime/preprocess.py::make_normalizer`, with
`resolve_normalization` and its two check helpers, at `7bc72b45137faa4b211d05a38f58812ffae5a109`
(the commit "Check the top-level normalization when an override applies"). It is equal at
`c2e610e91fee0a961032e12737ff9147697a7e53`. The host function has no `compute_dtype`, so the
`compute_dtype` part of `V-pre.normalize-3` and `source_pixels` come from the text of part 2. The
file computes in float64 and then casts. `reference_problems` of skellytracker
`tools/intake_bundle.py` (at `b065f6e6`) finds no problem in the file. `check_rules` gives the
expected result of each of the 8 data-only validator cases of the `pre.normalize` vector file of
part 4 (a scratch run). With `dtype` absent, `normalize` gives the values before the cast. Only the
vector cases use that form.

**Changes from the module of `model-yolox-person@openmmlab-exporter` v1.** The cast of each mode
stays. The `uint8` refusal now has the rule ID `V-pre.normalize-3` and also refuses a `float32`
`compute_dtype`. The `int8` refusal now has the rule ID `V-common.input-2`. The top-level value is
checked also when the override applies (d). The `custom` defaults are now the text of 2.3 (e).

## 4. Vectors

| Item | Value |
|---|---|
| Vector files in the proposal bundle | `vectors/pre.normalize.yaml`; `vectors/common.input.yaml` |
| Target files in skellytracker | `specs/model-sidecar/vectors/pre.normalize.yaml` (existing file); `specs/model-sidecar/vectors/common.input.yaml` (new file) |
| `verified_against` | `pre.normalize`: the file keeps `unverified` ("The independent implementations ran only some cases. ..."). The 16 numeric cases that the host can express list `{OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer}` in their `verified_against`: the 12 current numeric cases and 4 new ones. `common.input`: `unverified` (data-only validator cases). |
| Replaced case ids (`--replaces`) | `pre.normalize`: the 15 current ids `none-rgb`, `none-bgr`, `none-uint8`, `unit-float-rgb`, `unit-float-bgr`, `imagenet-bgr`, `imagenet-rgb`, `custom-rgb`, `custom-bgr`, `custom-scale-defaults-to-one`, `color-format-is-required`, `custom-has-no-color-format`, `normalization-is-required`, `precision-override` and `precision-without-override`. Reason: the part 4 file is the full file of the section as changed. Each of these cases is a copy of the current case. No key changes. `fill` wrote the same `expect`. `common.input`: none (new file). |

**The `pre.normalize` file.** The 15 current cases and 11 new cases. The new cases:

- the cast to `float16`: `unit-float-float16` and `imagenet-float16`. The expected values are
  `float16` values. A result with no cast differs by up to 1.3e-4 and 8.6e-4, more than the
  tolerance 1e-5. Thus these cases fail a host that does not cast;
- the `custom` defaults: `custom-mean-and-std-defaults` (`scale` only) and `custom-all-defaults`
  (`mode` only; equal to `none`);
- the pixels of a `float32` resize: `float32-resize-pixels` (fractional pixels, also below 0 and
  above 255, with `resize: {compute_dtype: float32}`);
- a `no-rule` refusal: `uint8-resize-pixels-are-integers` (a fractional pixel without a `float32`
  resize; the pixels are a tensor, not a sidecar value);
- data-only validator cases: `uint8-needs-normalization-none` and `uint8-needs-an-8-bit-resize`
  (`V-pre.normalize-3`), `uint8-with-override-none-is-valid` (no failed rule),
  `top-level-is-required-with-an-override` and `top-level-is-checked-with-an-override`
  (`V-pre.normalize-1`, item (d)).

The file adds two notes: the meaning of `dtype` and `resize` in `params`, and the scope of a
validator case. `params.resize` is `input.resize`. Only its `compute_dtype` is read. The tolerance
stays 1e-5. No case has `compare`. No case is a pixel case of a resize.

**The `common.input` file.** Two data-only validator cases: `uint8-is-an-input-dtype` (no failed
rule) and `int8-is-not-an-input-dtype` (`V-common.input-2`).

**`fill`.** `fill` of skellytracker `tools/make_vectors.py` (at `b065f6e6`), run with `python -B`
on both files with the `reference/` folder of this payload, printed "fill: no problems" for each
file. It kept the `expect` of each of the 15 current cases. `vector_problems` of
`tools/intake_bundle.py` finds no problem in either file (a scratch run).

**Host run.** The numeric cases ran through the OpenMMLab-Exporter host
`onnx_runtime/preprocess.py::make_normalizer` at `c2e610e91fee0a961032e12737ff9147697a7e53` (the
function is equal at `7bc72b45137faa4b211d05a38f58812ffae5a109`). The run used
`normalize_case` of `pipeline/handover.py` and the comparison of `agrees` of skellytracker
`tools/vector_form.py`, with the file tolerance. Result: 16 of 17 numeric cases pass. The host gives
`float16` for the two `float16` cases and `uint8` for `none-uint8` and `precision-override`. The
host cannot express `float32-resize-pixels`, because its function takes an 8-bit canvas and has no
`compute_dtype`. That case has no `verified_against`. The `error` case and the `failed` cases are
not host runs.

## 5. Parity evidence

The check is step 3 of "The step" (the reference swap) for `yolox-person`, with the part 3 file in
place of the host normalizer. It reran the committed script of OpenMMLab-Exporter ADR-3NNK,
unchanged, on 2026-11-06. The part 3 file of the run has the SHA-256
`a08587221f792e0c37c69d18015ccd2547c9957b61afef682227035706770c75`, the file of this bundle. The
record is
[OpenMMLab-Exporter ADR-YR3X](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/33e657d957872999aa04eb46d977eea1634be365/decisions/entries/YR3X-normalize-reference-swap.md).

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | The verdict rule of the script, set before the run (the script docstring at `53a48480d0b715f9b726963bce002ddb503b050b`): the gates and the controls of the parity script have the same pass or fail as the baseline run (pass gate); the parity exit code is 0 (pass gate); the gate data is equal to the baseline, also the G1 data; only `max_box_diff_px` can change (pass gate); each sidecar letterbox call and each sidecar normalizer call is equal to the host bit for bit (pass gate); no sidecar decoder call has a row, score or class difference (pass gate); control decoder differences and environment differences are reported only (control). One known difference: the script also requires each host file to be equal to the file at the baseline commit. `onnx_runtime/preprocess.py` changed after the baseline commit (`7bc72b45137faa4b211d05a38f58812ffae5a109` adds the top-level check). Thus `host_and_parity_files_not_equal_to_baseline_commit` lists that file, and `result_does_not_change` is false for that reason only. The same file is the only environment difference. The proposal reads the result from the other verdict fields. That change has no effect on the sidecar value `normalization: none`. |
| Test images (paths or dataset IDs), and the branch that each image runs | The images of the baseline run of OpenMMLab-Exporter ADR-3NNK (the `images.json` of that run; COCO val2017 images and the synthetic images of the parity script). Branch: `none` with `color_format: bgr` and a `float32` input for each image. The `imagenet` controls of the parity script run the `imagenet` branch. No image runs `unit_float`, `custom`, `float16` or `uint8`. The vectors of part 4 cover those branches. |
| Upstream reference: library, version, config and command | The upstream data of the baseline run: mmdet and mmpose in the published exporter image, the HumanArt YOLOX configs (OpenMMLab-Exporter ADR-3NNK). The script copies the container output of the baseline run. It does not run the container again. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | Equal to the baseline run: 155 of 155 gate and control pass/fail values are the same (6 sizes, fp32 and fp16), and the gate data has no difference that the rule does not allow. |
| Preprocessed input: maximum absolute difference for each image | 0. The G1 data is equal to the baseline. The sidecar normalizer gives 540 of 540 tensors equal to the host (mode `none`, `bgr`, `float32`). The letterbox canvas and its geometry are equal in 324 of 324 calls. |
| Row count for each image: sidecar path and upstream | Equal to the run of OpenMMLab-Exporter ADR-3NNK: the decode totals of the two runs are the same (12296 rows on 432 image entries on the sidecar path). |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | `object_detector` on the sidecar path, compared with the host on the same inputs: no decoder call has a row, score or class difference. The boxes differ by at most 1.22e-4 px, the same values as in the run of ADR-3NNK (the decode modules compute in float64). |
| Result (`pass`, `fail` or `to run`) | `pass`. The result does not change: each verdict value of the script passes, except the host-file rule, for the reason in the Gates row. |
| Script path in the exporter repo | `decisions/scripts/yolox_person_reference_swap.py` (it runs `decisions/scripts/yolox_person_parity.py` unchanged) |
| Exporter commit of the script | [`53a48480d0b715f9b726963bce002ddb503b050b`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/53a48480d0b715f9b726963bce002ddb503b050b/decisions/scripts/yolox_person_reference_swap.py) |
| Command | `uv run python decisions/scripts/yolox_person_reference_swap.py --out <new folder> --reference-dir <scratch folder>`. The scratch folder holds the five landed modules of `specs/model-sidecar/reference/` at `b065f6e6` (`pre_resize_letterbox.py`, `pre_resize_interpolation.py`, `post_det_decode.py`, `post_det_selection_nms.py`, `post_unprojection.py`) and `reference/pre_normalize.py` of this bundle. The run needs the host GPU and the baseline inputs. |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | `skellytracker/core/detectors/processing/image_preprocessing.py`: `build_normalization_fn` gets the input dtype of the precision (`input_spec.dtype[precision]`) and casts the result of each mode to it as the last step. `preprocess_image` must not cast the tensor to `float32` again; it keeps the dtype of the normalization. The `custom` branch keeps its defaults. |
| Dispatch point | `preprocess_image` (the call of `build_normalization_fn`). No new dispatch. |
| Validator changes (`model.py`, with rule IDs) | `skellytracker/core/sidecar/model.py`: a new type for the input dtypes (`float32`, `float16`, `uint8`) for `InputSpec.dtype` (`V-common.input-2`). `OutputSpec.dtype` keeps `OnnxDtype` with `int8` (`V-common.outputs-2`). A validator of the resolved sidecar for `V-pre.normalize-3`: for each precision whose input dtype is `uint8`, the resolved mode is `none`, and `input.resize.compute_dtype` is absent or `uint8` (`ResizeSpec` has no `compute_dtype` field yet; skellytracker ADR-PHJ3). `V-pre.normalize-1`: no default for `normalization`, also with an override. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | A test that runs the numeric cases of `vectors/pre.normalize.yaml` through `build_normalization_fn` and compares the dtype and the values. A validator test with the data-only cases of both vector files. A golden test: one image of the `yolox-person` parity set through `preprocess_image` with the sidecar, compared with the host tensor. |
| Existing code that the change touches | `skellytracker/core/detectors/processing/image_preprocessing.py` (`build_normalization_fn`, `preprocess_image`, `resolve_normalization_mode`); `skellytracker/core/sidecar/model.py` (`OnnxDtype`, `InputSpec`, `CustomNormalization`, `PrecisionArtifact.input_dtype`); the ONNX session feed of the detectors, which today takes a `float32` tensor for each input. |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmdet-person`, `yolox-person`, `rtmw-wholebody133`, `rtmo-coco17-body7`, `rtmpose-halpe26`, `dwpose-wholebody133-ubody` | none. Each family has a `float32` input for each precision (`onnx_convert/FP16_CONTRACT.md`, `keep_io_types=True`). No writer writes `normalization_by_precision`. | none. `make_normalizer` already casts each mode, refuses `uint8` with a mode other than `none`, has no `int8` and checks the top-level value with an override ([`onnx_runtime/preprocess.py:142-305`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L142-L305)). Writer follow-up: the RTMW writer names a `TensorProto.INT8` graph input `int8` for the input and the outputs ([`rtmw/sidecar.py:72-86`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c2e610e91fee0a961032e12737ff9147697a7e53/rtmw/sidecar.py#L72-L86)). It must refuse an `int8` input. No published graph has one, so no sidecar changes. |
| Ultralytics-Exporter | YOLO26 detection and YOLO26 pose | none for the published artifacts: each takes a `float32` input. A graph with a `uint8` input gets the override `none` and no `compute_dtype`, which meets `V-pre.normalize-3`. A graph with an `int8` input breaks `V-common.input-2`. The writer must refuse it: [`yolo_sidecar.py:83-86`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L83-L86) and [`yolo_sidecar.py:391-393`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L391-L393) (the file is equal at the Ultralytics-Exporter HEAD `2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4`). The writer still writes sidecars of an earlier spec, so it changes anyway for `2.0.0`. | for the owner |
| Roboflow-Exporter | RF-DETR (no spec example) | none for the published artifacts: the writer checks that each published artifact has `float32` I/O ([`pipeline/artifacts.py:125-130`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L125-L130)). Its input check allows `uint8` and `int8` with `imagenet_rgb` ([`rf_detr/sidecar.py:52`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L52), [`rf_detr/sidecar.py:240-251`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L240-L251)). That set must become `float32` and `float16`, or `uint8` only with `none`. | for the owner |
| Qualcomm-Exporter | MediaPipe person detector (out of scope of this revision) | none. Its writer writes `unit_float` with a float input. | none |
| MediaPipe-Exporter | none | none. It has no sidecar writer. | none |

The skellytracker package sidecars are outside the spec until the package migrates. They are not
listed.

**Reference examples that the change makes invalid.** none. Each example has a `float32` input for
each precision, no `normalization_by_precision`, no `compute_dtype` and no `custom` object:
`rtmdet-person` (`imagenet`), `rtmo-body7` (`none`), `rtmw-wholebody` (`imagenet`), `yolo26` and
`yolo26-body` (`unit_float`). The cast of a `float32` input does not change a value. The section rows
of `specs/model-sidecar/TRACEABILITY.md` (`common.input` and `pre.normalize`) list these five
examples.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit` or `needs-export`) | Edit text |
|---|---|---|---|
| none | | | |

**Candidate example.**

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none |
| Writer code (file, function and commit) | none (no sidecar changes) |
| `sidecar_refs.py --check` result | none |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: keep the text, and write a module that casts only for `none` (the current mode table). | The text then disagrees with skellytracker ADR-PHJ3 and with "Compute dtype". A host gives a `float32` tensor to a `float16` graph input, and ONNX Runtime refuses it. | Part 1, (1) |
| A module of the current text, with no proposal (the other choice of the skellytracker response). | The user chose this proposal on 2026-11-06. The current text has no rule for a `uint8` input with `imagenet`, so a module of the current text must cast fractional values to `uint8`, which is not defined. | Part 1, (3) and (4) |
| Round, clamp and then cast a fractional value to `uint8`, in place of a rule. | No model in scope needs it. It adds a rounding rule and a clamp that no upstream states. The Ultralytics-Exporter writer already writes `none` for a `uint8` input. | Part 1, Upstream evidence (4) |
| Keep `int8`, and define its cast (for example `pixel - 128` with `none`). | No exporter writes an `int8` input for a published artifact. No upstream states such an offset. The user decided on 2026-11-06 to remove `int8` from the input dtypes. | Part 1, (5) |
| Also remove `int8` from the output dtypes (`V-common.outputs-2`). | The user decided on 2026-11-06 that the output dtypes keep `int8`. An output is not cast by the host. | Part 1, plan decisions |
| Put the `compute_dtype` part of `V-pre.normalize-3` in `pre.resize.interpolation` as a second rule. | One rule then reads the resolved mode and the other reads the resize, for one cast. The cast is a step of `pre.normalize`, so its rule goes there. A sidecar that breaks the rule fails one rule ID. | 2.4 |
| No `custom` defaults: require `mean` and `std`. | `V-pre.normalize-1` already allows an absent key ("If `mean` or `std` is present ..."). The OpenMMLab-Exporter host and the skellytracker package already use the identity defaults. A required key would make valid sidecars invalid. | Part 1, Upstream evidence (2) and (3) |
| A rule that refuses `std` with a zero value. | Not in this proposal. No model needs it, and the change is not a dtype rule. | none |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [ ] The intake names the bundle ID of this proposal. To do: the next versions of the intakes of
      `model-yolox-person@openmmlab-exporter` and `model-rtmw-wholebody133@openmmlab-exporter`
      name `proposal-normalize-input-dtype@openmmlab-exporter` for `pre.normalize`.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. Committed at `53a48480d0b715f9b726963bce002ddb503b050b`, unchanged at the run.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [ ] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
      Not packed yet: this is a draft. No file in skellytracker changed.
