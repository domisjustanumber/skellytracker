# Change proposal: normalize-custom-defaults

This file uses ASD-STE100 Simplified Technical English.

## Header

| Field | Value |
|---|---|
| Title | An absent `custom` key has a value (`scale: 1`, `mean: [0, 0, 0]`, `std: [1, 1, 1]`); the `none` row names YOLOX as a model whose upstream does not normalize |
| Slug | `normalize-custom-defaults` |
| Date | 2026-11-06 |
| Exporter repo | OpenMMLab-Exporter |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `ecee56e1ea1b4d3901c76a73b713ed0256675e78` |
| Model, and its `model` bundle ID | `yolox-person` (`model-yolox-person@openmmlab-exporter`) for the `none` row. No model in scope uses a `custom` object. No model needs a value that this proposal adds. |
| Intake rows with the verdict `near-miss` or `gap` | none. The rows G8 (normalization inside the graph) and T10 (normalization) of the `yolox-person` intake are `exact`. The note of row T10 and the item (3) of "Spec defects that you found and did not propose" of that intake name the `none` row. The `custom` defaults come from the reference step of `pre.normalize` (part 1). |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `pre.normalize` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/normalization.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | `proposal-normalize-input-dtype@openmmlab-exporter`. The part 3 file of this proposal is the part 3 file of that bundle with one change, and the vector cases use its `dtype` parameter and its cast. |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | skellytracker ADR-XH1J records version 1 of `proposal-normalize-input-dtype@openmmlab-exporter`. That version holds the changes of this proposal. The response r2 to that bundle asks to send them as a separate bundle, and version 2 of that bundle removes them. Thus this proposal does not compete with ADR-XH1J. It builds on it. The other entries of the Proposed table of the spec log are skellytracker ADR-3S5G, ADR-52NQ and ADR-03PH. None of them covers `pre.normalize`. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (branch `dom/sidecar-implementation`) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `8fed6f34eb22643e0b6cc38a7c6b80014bfe1d75` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

**Section owner.** `proposal-normalize-input-dtype@openmmlab-exporter` owns `pre.normalize`: its
decision entry skellytracker ADR-XH1J has the status `proposed`. `intake_bundle.py list` at
`8fed6f34` gives the owner `openmmlab-exporter`. The contributor of this bundle is the same
contributor. "Section owner" in `specs/model-sidecar/model-addition-workflow/hand-over.md` says that
only the owner writes parts 2, 3 and 6 of a new proposal for the section. Thus this bundle can write
them.

**Proposal form.** This bundle is a new proposal ("Proposal forms" in
`specs/model-sidecar/model-addition-workflow/hand-over.md`):

- A contribution (`contributes_to`) does not apply. A contribution is for a section with a recorded
  owner that is not you, and for the same change. The owner is this contributor, and the change is
  not the change of the owner bundle. A contribution also holds no part 2.
- A follow-up (`base`) does not apply. A follow-up changes an open proposal: it can change parts 2
  and 3 of its base, and the base and the follow-up then make one contract unit. The user decided
  that these changes are not one contract unit with the dtype rules (response r2 to
  `proposal-normalize-input-dtype@openmmlab-exporter`). They get their own decision.
- Thus the form is a new proposal, with `related` set to
  `proposal-normalize-input-dtype@openmmlab-exporter`, as the response r2 asks. The same bundle is
  also in `depends_on`, because the part 3 file and the vectors of this proposal build on the part 3
  file of that bundle ("Full section" in
  `specs/model-sidecar/model-addition-workflow/reference-implementations.md`: when the reference
  file exists, part 3 gives that file with the change).

## 1. Gap

| Item | Value |
|---|---|
| Property | (e) The value of an absent key of a `custom` normalization object: `scale: 1`, `mean: [0, 0, 0]` and `std: [1, 1, 1]`. `V-pre.normalize-1` allows each of these keys to be absent. The text gives the default of `scale` only in a comment of the custom-mode YAML, and no value for `mean` and `std`. (f) The "Typical use" of the mode `none`. The mode table names YOLOX as a graph that normalizes internally. The YOLOX upstream does not normalize, and the YOLOX graph has no normalization. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | (1) The spec text: `V-pre.normalize-1` ("If `mean` or `std` is present, it must have length 3. If `scale` is present, it must be positive.") and the custom-mode YAML of Behaviour (`scale: ... # optional; default 1.0`, no comment for `mean` and `std`). (2) The OpenMMLab-Exporter host gives the defaults `scale` 1 ([`onnx_runtime/preprocess.py:154`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L154)) and `mean` `[0, 0, 0]` and `std` `[1, 1, 1]` ([`:158-159`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L158-L159)). (3) The skellytracker package gives the same defaults: `CustomNormalization` has `scale: float = 1.0`, `mean: list[float] \| None = None` and `std: list[float] \| None = None` (`skellytracker/core/sidecar/model.py`), and `build_normalization_fn` uses `mode.mean or [0.0, 0.0, 0.0]` and `mode.std or [1.0, 1.0, 1.0]` (`skellytracker/core/detectors/processing/image_preprocessing.py`). (4) YOLOX: the data preprocessor of the HumanArt YOLOX configs has no `mean` and no `std`, so the model takes raw 0-255 BGR pixels: mmpose `5408bc76f5b848cf925a0d1857899011d8c5b497` (tag `v1.3.2`), [`projects/rtmpose/yolox/humanart/yolox_s_8xb8-300e_humanart.py:11-20`](https://github.com/open-mmlab/mmpose/blob/5408bc76f5b848cf925a0d1857899011d8c5b497/projects/rtmpose/yolox/humanart/yolox_s_8xb8-300e_humanart.py#L11-L20). Without `mean` and `std`, mmengine sets `_enable_normalize = False`, and the only arithmetic is the cast to float: mmengine `02f80e8bdd38f6713e04a872304861b02157905a` (tag `v0.10.3`), [`mmengine/model/base_model/data_preprocessor.py:231-232`](https://github.com/open-mmlab/mmengine/blob/02f80e8bdd38f6713e04a872304861b02157905a/mmengine/model/base_model/data_preprocessor.py#L231-L232) and [`:266`](https://github.com/open-mmlab/mmengine/blob/02f80e8bdd38f6713e04a872304861b02157905a/mmengine/model/base_model/data_preprocessor.py#L266). (5) The YOLOX graph: the only consumers of the input `input` are the space-to-depth `Reshape` of the Focus stem and its `Shape` node. The graph has no `Sub`, `Div` or `Mul` node on the pixels near the input (the intake of `model-yolox-person@openmmlab-exporter`, row G8; a graph read of `exports/detectors/object_detectors/yolox-person/*.onnx`, untracked output). (6) RTMO: the Authoring guidance of `pre.normalize` gives `mean=[0, 0, 0]`, `std=[1, 1, 1]` and `normalization: none` for RTMO. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | The user decided on 2026-11-06 that the `custom` defaults and the correction of the `none` row are not one contract unit with the dtype rules of `proposal-normalize-input-dtype@openmmlab-exporter`. They go in a separate proposal bundle with a new slug, with `related` set to that bundle (skellytracker response r2 to that bundle, skellytracker ADR-XH1J). |
| Nearest section ID (the `id` in the section file's front matter) | `pre.normalize` |
| Why the nearest section is wrong | For (e): `V-pre.normalize-1` allows a `custom` object with no `mean` or no `std`, but the formula `(pixel * scale - mean) / std` needs both. The text gives no value, so a host cannot compute the result of a valid sidecar. The part 3 file of `proposal-normalize-input-dtype@openmmlab-exporter` (version 2) follows the current text: it accepts such an object in its rule checks, and its `normalize` refuses it with no rule ID. The OpenMMLab-Exporter host and the skellytracker package give values. Thus the implementations do not agree on a valid sidecar. The default of `scale` is only in a YAML comment of an example. For (f): the "Typical use" tells a reader that the YOLOX graph has the normalization inside. A reader can then write `none` for a YOLOX export only after a search for normalization nodes, or write a different mode for a YOLOX export that the reader thinks has no such nodes. The upstream and the graph show that YOLOX takes raw pixels because its upstream does not normalize. |
| Measured difference (number, image and script) | (e): on the 4 vector pixels with `{mode: custom, scale: 0.5}` and `color_format: rgb`, the OpenMMLab-Exporter host gives `[[0, 0, 0], [127.5, 127.5, 127.5], [125, 64, 5], [25, 50, 100]]` (case `custom-mean-and-std-defaults`, part 4). The part 3 file of version 2 of `proposal-normalize-input-dtype@openmmlab-exporter` gives no values: it raises `ValueError`. (f): no number. The evidence is the config and the graph read. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | no. This proposal does not change a value of a model. `yolox-person` writes `normalization: none` with and without this change. |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none |

**Primary evidence.** The spec text, the committed host code of OpenMMLab-Exporter at
`7bc72b45137faa4b211d05a38f58812ffae5a109`, the skellytracker package code at `8fed6f34`, and the
upstream configs and code of mmpose `v1.3.2` and mmengine `v0.10.3`. The graph read of (5) is
secondary: the ONNX files are untracked output.

## 2. Spec change

The relative links of the proposed text resolve from the record path
`specs/model-sidecar/proposals/<slug>/`. At landing, the session changes them to the path of the
section file (an editorial fix).

This proposal changes the text after `proposal-normalize-input-dtype@openmmlab-exporter` lands
(`depends_on`). Each edit below names a text that is in the section today or that that bundle
writes.

### 2.1 Sections

Changed section `pre.normalize`, title "Normalization", file
`specs/model-sidecar/pre/normalization.md`. The section ID, the title, the kind and the selectors do
not change. No section-map row changes.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.normalize` | front matter | No edit. |
| `pre.normalize` | Behaviour, the mode table | Replace the rows `none` and `custom` with the rows of 2.3. The row `none` changes only in the column "Typical use". The row `custom` changes only in the column "Host behavior". |
| `pre.normalize` | Behaviour, the custom-mode YAML | The comments of 2.3. |
| `pre.normalize` | Validation rules | No edit (2.4). |
| `pre.normalize` | Implementer guidance | Add the sentence of 2.3 to the bullet that starts "That host supports the modes `none`, `unit_float`, `imagenet` and `custom`" (the third bullet, as `proposal-normalize-input-dtype@openmmlab-exporter` writes it). |
| `specs/model-sidecar/changelog.md` | Summary of changes | The row of 2.6. |
| `specs/model-sidecar/vectors/pre.normalize.yaml` | cases | The 2 new cases of part 4. |
| `specs/model-sidecar/reference/pre_normalize.py` | | The file of part 3. It replaces the file of `proposal-normalize-input-dtype@openmmlab-exporter`. |
| `specs/model-sidecar/TRACEABILITY.md` | generated | Run the generator after the content commit. |
| `specs/model-sidecar/README.md` | Overview, section map, validation index | No edit. |
| `specs/model-sidecar/examples/` | | No edit (part 7). |

### 2.2 Fields table

No change.

### 2.3 Behaviour

**The mode table of `pre.normalize`.** Replace the rows `none` and `custom`. The rows `unit_float`
and `imagenet` do not change.

| Mode | Host behavior | Typical use |
|------|---------------|-------------|
| `none` | Pass pixel values (0–255) unchanged, cast to `input.dtype`. Channel order from `input.color_format`. | Graphs that take raw 0–255 pixels: graphs that normalize internally, and models whose upstream does not normalize, for example YOLOX (no `mean` and no `std`) and RTMO (`mean` `[0, 0, 0]` and `std` `[1, 1, 1]`) |
| `custom` | `(pixel * scale - mean) / std` on 0–255 channel values. `mean` and `std` are in the channel order of `input.color_format`. Each key other than `mode` is optional. When a key is absent, its value is `scale: 1`, `mean: [0, 0, 0]` or `std: [1, 1, 1]`. | Rare exports that match no named mode |

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

**Implementer guidance of `pre.normalize`.** In the bullet that starts "That host supports the
modes `none`, `unit_float`, `imagenet` and `custom`", add this sentence before "Its function has no
`input.resize.compute_dtype`.":

> Its `custom` defaults are `scale: 1`, `mean: [0, 0, 0]` and `std: [1, 1, 1]`.

The link of that bullet (`onnx_runtime/preprocess.py:142-211` at
`7bc72b45137faa4b211d05a38f58812ffae5a109`) covers the defaults (lines 154 and 158-159).

The change has no inverse. The section has no Inverse.

### 2.4 Validation rules

No new rule. No changed rule.

Unchanged rules that name a value of the change:

- `V-pre.normalize-1`: unchanged. It allows an absent `scale`, `mean` or `std`. Its sentences "If
  `mean` or `std` is present, it must have length 3." and "If `scale` is present, it must be
  positive." stay. Behaviour now gives the value of an absent key.
- `V-pre.normalize-2`: unchanged. A `custom` object is not a valid override, so the defaults apply
  only to the top-level `input.normalization`.

### 2.5 Selectors

No change: `input.normalization.mode=custom` and `input.normalization=none` keep their meaning.

### 2.6 Changelog row

| # | Area | Change | Driven by | Section |
|---|------|--------|-----------|---------|
| (next) | Input | An absent key of a `custom` normalization has the value `scale: 1`, `mean: [0, 0, 0]` or `std: [1, 1, 1]`. The `none` row names YOLOX and RTMO as models whose upstream does not normalize. | user decision 2026-11-06: `V-pre.normalize-1` allowed an absent `mean` or `std` with no value, and the `none` row said that YOLOX normalizes internally (the decision entry of this proposal) | [Normalization](../../pre/normalization.md#behaviour) |

## 3. Reference implementation

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/pre_normalize.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_normalize.py` (the file of `proposal-normalize-input-dtype@openmmlab-exporter`, after that bundle lands) |
| Functions (one for each algorithm) | The functions of the part 3 file of `proposal-normalize-input-dtype@openmmlab-exporter`, with the same names: `custom_parameters` (the `custom` check and the defaults), `check_top_level`, `check_overrides`, `resolve_normalization`, `input_dtype`, `check_uint8`, `source_pixels`, `tensor_order`, `normalize_none`, `normalize_unit_float`, `normalize_imagenet`, `normalize_custom`, `cast_to_input_dtype`, `normalize`, `check_rules`; `run` for the cases; helpers `is_number` and `mode_name` |

**Base file.** "Full section" in
`specs/model-sidecar/model-addition-workflow/reference-implementations.md` says: if the reference
file of the section exists, part 3 gives that file with the change. When this proposal lands, the
file of `proposal-normalize-input-dtype@openmmlab-exporter` exists (`depends_on`). Thus the part 3
file is version 2 of that file (SHA-256
`88cf2d1fc83103d14f442593c561731ea52ec23ff96e1f8353f42fe03b59e559`) with this change:

- The constant `DEFAULT_SCALE` (1.0) is now `CUSTOM_DEFAULTS` (`scale` 1.0, `mean`
  `(0.0, 0.0, 0.0)`, `std` `(1.0, 1.0, 1.0)`).
- `custom_parameters` returns the value of `CUSTOM_DEFAULTS` for an absent key. The base file
  returns `None` for an absent `mean` or `std`.
- `normalize` does not refuse a `custom` object with an absent `mean` or `std`.
- The module docstring.

No other definition changes. The other behaviour of the base file stays: the cast, the rules
`V-pre.normalize-1` to `-3`, and the refusals of `V-common.input-2`, `V-common.input-5` and
`V-pre.resize.interpolation-1`.

**Equal code.** The code of the part 3 file, without the docstrings, is equal to the code of
version 1 of the part 3 file of `proposal-normalize-input-dtype@openmmlab-exporter` (SHA-256
`a08587221f792e0c37c69d18015ccd2547c9957b61afef682227035706770c75`). A scratch `ast` comparison
found no difference in a definition or a constant. That version 1 held these defaults. Part 5
uses this fact.

**Source.** The `custom` check of OpenMMLab-Exporter `onnx_runtime/preprocess.py`, lines 154 and
158-159 at `7bc72b45137faa4b211d05a38f58812ffae5a109` (equal at
`c82f2f1138faa5dd82a45639215e9411245e19cb`). `reference_problems` of skellytracker
`tools/intake_bundle.py` (at `8fed6f34`) finds no problem in the file.

**Imports.** The file imports `pre_resize_interpolation` (the landed module of
`pre.resize.interpolation`), as the base file does. It has no fixture.

## 4. Vectors

| Item | Value |
|---|---|
| Vector files in the proposal bundle | `vectors/pre.normalize.yaml` |
| Target files in skellytracker | `specs/model-sidecar/vectors/pre.normalize.yaml` (existing file) |
| `verified_against` | The file keeps `unverified` ("The independent implementations ran only some cases. ..."). Both cases list `{OpenMMLab-Exporter: onnx_runtime/preprocess.py::make_normalizer}` in their `verified_against`. |
| Replaced case ids (`--replaces`) | none |

**The file.** It holds only the 2 new cases. `land` keeps the current cases and adds these at the
end:

- `custom-mean-and-std-defaults`: `{mode: custom, scale: 0.5}`. `mean` and `std` are absent. The
  result is `pixel * 0.5`;
- `custom-all-defaults`: `{mode: custom}`. All three keys are absent. The result equals `none`.

The current case `custom-scale-defaults-to-one` already tests an absent `scale`. The two cases came
from version 1 of `proposal-normalize-input-dtype@openmmlab-exporter`, unchanged. The notes and the
tolerance are the notes and the tolerance of the vector file of that bundle. `land` keeps the file
keys of the current file. No case has `compare`. No case is a pixel case.

**`fill`.** `fill` of skellytracker `tools/make_vectors.py` (at `8fed6f34`), run with `python -B`
on a copy of the payload with its `reference/` folder, printed "fill: no problems" and changed no
byte of the file. A second scratch run gave `fill` one file with the 24 cases of the vector file of
`proposal-normalize-input-dtype@openmmlab-exporter` and these 2 cases, with the part 3 file of this
proposal: "fill: no problems", and no byte changed. Thus the part 3 file gives the `expect` of each
case of that bundle. `vector_problems` of `tools/intake_bundle.py` finds no problem in the file (a
scratch run).

**Host run.** Both cases ran through the OpenMMLab-Exporter host
`onnx_runtime/preprocess.py::make_normalizer` at `c82f2f1138faa5dd82a45639215e9411245e19cb`, with
`normalize_case` of `pipeline/handover.py` and the comparison of `agrees` of skellytracker
`tools/vector_form.py`, with the file tolerance. Result: 2 of 2 pass. The host gives `float32`.

## 5. Parity evidence

No model in scope uses a `custom` object: `yolox-person` and RTMO use `none`, RTMW and RTMDet use
`imagenet`, the YOLO26 models use `unit_float` (the five spec examples and the two model bundles).
Thus no parity run can run the changed branch on a real model. The change of the `none` row is
guidance: it changes no computation.

The code of the part 3 file is equal to the code of the file that ran in the `yolox-person` parity
check of [OpenMMLab-Exporter ADR-YR3X](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/33e657d957872999aa04eb46d977eea1634be365/decisions/entries/YR3X-normalize-reference-swap.md)
(part 3, Equal code). That run gives the branches `none` and `imagenet` of this code. The vectors
and the host run of part 4 give the changed branch.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | The gates of OpenMMLab-Exporter ADR-YR3X (the verdict rule of `decisions/scripts/yolox_person_reference_swap.py` at `53a48480d0b715f9b726963bce002ddb503b050b`). Part 5 of `proposal-normalize-input-dtype@openmmlab-exporter` gives them in full. |
| Test images (paths or dataset IDs), and the branch that each image runs | The images of the baseline run of OpenMMLab-Exporter ADR-3NNK. Branch: `none`, `bgr`, `float32`, and the `imagenet` controls. No image runs `custom`: no model in scope uses it. |
| Upstream reference: library, version, config and command | As OpenMMLab-Exporter ADR-YR3X: mmdet and mmpose in the published exporter image, the HumanArt YOLOX configs. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | 155 of 155 gate and control pass/fail values equal to the baseline (OpenMMLab-Exporter ADR-YR3X). |
| Preprocessed input: maximum absolute difference for each image | 0 (540 of 540 sidecar normalizer tensors equal to the host, OpenMMLab-Exporter ADR-YR3X). |
| Row count for each image: sidecar path and upstream | Equal to the run of OpenMMLab-Exporter ADR-3NNK (OpenMMLab-Exporter ADR-YR3X). |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | `object_detector`: no row, score or class difference (OpenMMLab-Exporter ADR-YR3X). |
| Result (`pass`, `fail` or `to run`) | `pass` for the code of the part 3 file on the `yolox-person` path (OpenMMLab-Exporter ADR-YR3X, with a file of equal code). The changed branch has no parity run, because no model in scope uses `custom`. |
| Script path in the exporter repo | `decisions/scripts/yolox_person_reference_swap.py` |
| Exporter commit of the script | [`53a48480d0b715f9b726963bce002ddb503b050b`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/53a48480d0b715f9b726963bce002ddb503b050b/decisions/scripts/yolox_person_reference_swap.py) |
| Command | As part 5 of `proposal-normalize-input-dtype@openmmlab-exporter`. The run of OpenMMLab-Exporter ADR-YR3X used version 1 of its `reference/pre_normalize.py`, whose code is equal to the part 3 file of this proposal. |

## 6. skellytracker implementation proposal

| Item | Value |
|---|---|
| Module and function | No change. `build_normalization_fn` of `skellytracker/core/detectors/processing/image_preprocessing.py` already uses `mode.mean or [0.0, 0.0, 0.0]` and `mode.std or [1.0, 1.0, 1.0]`. `CustomNormalization.scale` already defaults to `1.0`. |
| Dispatch point | No change. |
| Validator changes (`model.py`, with rule IDs) | none. `CustomNormalization` already allows an absent `scale`, `mean` and `std` (`V-pre.normalize-1`). |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | Run the two cases of part 4 through `build_normalization_fn`, with the test of the numeric cases that `proposal-normalize-input-dtype@openmmlab-exporter` proposes. No golden parity test: no model uses `custom`. |
| Existing code that the change touches | none (tests only) |

## 7. Exporter impact

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `rtmdet-person`, `yolox-person`, `rtmw-wholebody133`, `rtmo-coco17-body7`, `rtmpose-halpe26`, `dwpose-wholebody133-ubody` | none. No writer writes a `custom` object. `yolox-person` and `rtmo-coco17-body7` keep `normalization: none`. | none. `make_normalizer` already gives the defaults ([`onnx_runtime/preprocess.py:154`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L154), [`:158-159`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/7bc72b45137faa4b211d05a38f58812ffae5a109/onnx_runtime/preprocess.py#L158-L159)). |
| Ultralytics-Exporter | YOLO26 detection and YOLO26 pose | none. The writer writes `unit_float`. | none |
| Roboflow-Exporter | RF-DETR (no spec example) | none. The writer writes `imagenet_rgb`. | none |
| Qualcomm-Exporter | MediaPipe person detector (out of scope of this revision) | none. The writer writes `unit_float`. | none |
| MediaPipe-Exporter | none | none. It has no sidecar writer. | none |

The skellytracker package sidecars are outside the spec until the package migrates. They are not
listed.

**Reference examples that the change makes invalid.** none. The change adds no rule. No example has
a `custom` object: `rtmdet-person` (`imagenet`), `rtmo-body7` (`none`), `rtmw-wholebody`
(`imagenet`), `yolo26` and `yolo26-body` (`unit_float`). The section row of `pre.normalize` in
`specs/model-sidecar/TRACEABILITY.md` lists these five examples.

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
| The near-miss: keep the text. A `custom` object with no `mean` or `std` has no value. | A valid sidecar then has no defined result. The part 3 file of `proposal-normalize-input-dtype@openmmlab-exporter` refuses it, and the host and the package give values. | Part 1, Measured difference |
| A rule that requires `mean` and `std`. | `V-pre.normalize-1` allows an absent key today, so the rule would make valid sidecars invalid. The host and the package already use the identity values. | Part 1, Upstream evidence (1) to (3) |
| Give the values of `mean` and `std` only, and keep the default of `scale` only in the YAML comment. | The values of the three keys then are in two places. The `custom` row gives all three in one sentence, and the YAML comments repeat them. | 2.3 |
| Keep these changes in `proposal-normalize-input-dtype@openmmlab-exporter` (its version 1). | The user does not accept them as one contract unit with the dtype rules. | Part 1, plan decisions |
| Send this bundle as a follow-up (`base`) of `proposal-normalize-input-dtype@openmmlab-exporter`. | A follow-up changes its base and makes one contract unit with it. The user wants a separate decision. | Header, Proposal form |
| Send this bundle as a contribution (`contributes_to`). | A contribution is for a section with an owner that is not you and for the same change. It has no part 2. | Header, Proposal form |
| The `none` row: remove YOLOX, and name no model. | The row then gives no example of a model whose upstream does not normalize. YOLOX and RTMO are two such models of OpenMMLab-Exporter. | Part 1, Upstream evidence (4) to (6) |
| The `none` row of version 1 of `proposal-normalize-input-dtype@openmmlab-exporter`: "models with no upstream `mean` and `std`, for example YOLOX and RTMO". | RTMO has an upstream `mean` and `std` (`[0, 0, 0]` and `[1, 1, 1]`). The new text names the values of each model. | Part 1, Upstream evidence (6) |

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [ ] The intake names the bundle ID of this proposal. To do: the next version of the intake of
      `model-yolox-person@openmmlab-exporter` names
      `proposal-normalize-custom-defaults@openmmlab-exporter` for the `none` row (row T10).
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
      repo. Committed at `53a48480d0b715f9b726963bce002ddb503b050b`.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
