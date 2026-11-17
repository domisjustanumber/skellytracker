# Change proposal: resize-pixel-tolerance

This file follows the change proposal template (`specs/model-sidecar/templates/change-proposal.md`).
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. It has no relative links.

## Header

| Field | Value |
|---|---|
| Title | A resize implementation can differ from the reference by at most 1 `uint8` step |
| Slug | `resize-pixel-tolerance` |
| Date | 2026-11-17 |
| Exporter repo | none. The contributor is skellytracker (contributor name `skellytracker`). The evidence scripts are in the skellytracker repository. |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `a50c759177a5bff5c5bc5b3a6ed16e40bdab133b`, branch `dom/native-jpeg` of the skellytracker repository. The commit is local. It is not on the default branch, so it is a secondary source, and it has no permalink yet. |
| Model, and its `model` bundle ID | `yolox-person` (`model-yolox-person@openmmlab-exporter`) and `rtmw-wholebody133` (`model-rtmw-wholebody133@openmmlab-exporter`). Both are landed. The rule is for each model that resizes. It does not come from an intake. |
| Intake rows with the verdict `near-miss` or `gap` | none. No model intake has a row for this property. The gap is a host property: the spec gives no limit for a different implementation of the resize step. |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `pre.resize.interpolation` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/interpolation.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | none. The Proposed table of `specs/model-sidecar/decisions/README.md` is empty. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (the main checkout) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `93d7c9e0840a231abe844325a42d4fb7440c77e4` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

The package gets a second implementation of the resize step: ONNX nodes that run on the GPU (a
"preprocess graph") for the NVIDIA execution providers `cuda` and `trt-rtx`. The CPU code stays the
normative reference. The spec defines each resize result as the output of one OpenCV call. It gives
no limit for a different implementation, so a host must give the OpenCV output bit for bit. The
ONNX nodes cannot do this for each method and each filter.

Two causes are known:

- At an exact `.5` tie, the uint8 resize of OpenCV rounds up. The ONNX `Round` node rounds half to
  even. With `Round`, 6.6% of the letterbox values differed by 1 step at 720x1280, all at exact
  ties. The graph now rounds with `Floor(x + 0.5)`, and the letterbox difference is 0.
- The `affine_crop` graph still differs by 1 step on about 0.01% of the values. These values are
  not ties. The cause is inferred, not measured: `cv2.warpAffine` computes the source positions in
  fixed point, with 1/32-pixel steps. `GridSample` computes them in floating point.

The decode of an encoded image (for example a JPEG file) to the host frame is out of scope. The spec
starts at the host frame: the paragraph "Host frame" under the heading "Fields" of `common.input`
(`specs/model-sidecar/common/input.md`) says "The host gets each frame as an 8-bit, 3-channel BGR
image in HWC layout". The limit compares two resize results of the same host frame.

| Item | Value |
|---|---|
| Property | The largest difference between the resize result of a host and the output of the OpenCV call of the method, for each value, on the 0-255 scale, before the normalization. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | none. This is a host property, not a property of an upstream model. The spec text: heading "Behaviour" of `pre.resize.interpolation` says "If a host uses another library, it must reproduce that behaviour and the pixel centres of the call". Heading "Compute dtype" says that a `uint8` result "is the 8-bit output of the OpenCV filter". Missing primary evidence for the two causes: (1) the rounding of the `Round` operator in the ONNX operator documentation (`docs/Operators.md`, heading `Round`, of the onnx/onnx repo at a pinned SHA); (2) the fixed-point positions of `cv2.warpAffine` (`modules/imgproc/src/imgwarp.cpp` of the opencv/opencv repo at a pinned SHA). The causes only explain the numbers. The limit does not need them. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | (1) The package gets a second implementation of the resize step as ONNX nodes for the NVIDIA execution providers. The CPU code stays the normative reference. (2) With `compute_dtype: uint8`, a resize implementation can differ from the reference by at most 1 `uint8` step, on the 0-255 scale, before the normalization. (3) With `compute_dtype: float32`, the limit is 0.05 on the 0-255 scale. (4) The limit applies to each host implementation. The spec gets no list of excluded methods or filters. The package uses the GPU graph only where the graph meets the limit (part 6). (5) The decode of an encoded image to the host frame is out of scope. (6) On landing, the item "Cost of the detector preprocess" of `decisions/open-work.md` gets one more sentence (part 2.1). |
| Nearest section ID (the `id` in the section file's front matter) | `pre.resize.interpolation` |
| Why the nearest section is wrong | The section names one OpenCV call for each method and says that another library "must reproduce" it. It gives no limit. A GPU graph with a 1-step difference on 0.01% of the values does not reproduce the call, but the detections of `yolox-person` do not change (part 5). |
| Measured difference (number, image and script) | Part 5. Summary, graph only (the graph against the CPU reference on the same decoded pixels), both EPs: `letterbox` max 0 steps (`uint8`, `linear`); `affine_crop` max 1 step on about 0.01% of the values (`uint8`, `linear`); `affine_crop` max 0.035 (`float32`, `linear`). Script: `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py` at `a50c759177a5bff5c5bc5b3a6ed16e40bdab133b`. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes: OpenMMLab-Exporter RTMW and YOLOX (person). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The nearest row is `resize.antialias`. This proposal adds no antialias. The resize stays non-antialiased. |

## 2. Spec change

### 2.1 Sections

One section changes: `pre.resize.interpolation`, title "Interpolation", file
`specs/model-sidecar/pre/interpolation.md`. Its front matter does not change. The section is the one
place of the rule. Its selectors cover each method that resizes the image: `letterbox`, `stretch`,
`fit` and `affine_crop`. Its heading "Pixel centres" names the OpenCV call of each method.

**Places that the change edits.**

| Place | Heading | Edit |
|---|---|---|
| `pre.resize.interpolation` | "Behaviour", first paragraph | The sentence "If a host uses another library, it must reproduce that behaviour and the pixel centres of the call." gets the end ", within the resize limit", with a link to the new heading "Resize limit". |
| `pre.resize.interpolation` | new heading "Resize limit" under "Behaviour", after "Precision" | The new text of 2.3. |
| `specs/model-sidecar/changelog.md` | "Summary of changes" | The row of 2.6. |
| `decisions/open-work.md` (root log; outside the spec folder, a non-spec edit) | item "Cost of the detector preprocess" | The sentence "A change of this code must keep each output tensor equal." becomes "A change of this code must keep each output tensor equal. A second implementation on the GPU must agree with this code within the resize limit of `pre.resize.interpolation`." |

The template lists only places of the spec. The last row is outside the spec folder, so part 6 also
names it.

**Places that the change does not edit, and the reason:**

- `common.input`: the paragraph "Host frame" stays. It is the start of the spec. The limit starts
  at that frame.
- `pre.resize.letterbox`, `pre.resize.stretch`, `pre.resize.fit`, `pre.resize.affine_crop`: no edit.
  Each section names its call and links to "Pixel centres" of `pre.resize.interpolation`. The rule
  has one place.
- `pre.resize.none`: no edit. A `none` resize has no resize step.
- `pre.normalize`: no edit. The normalization takes the result of the resize step as before.
- `post.unprojection` and `common.sizes_and_artifacts`: no edit. The geometry does not change.
- `specs/model-sidecar/README.md`: no new section, no new rule, no new value. The section map and the
  validation index do not change.
- The closed sets (`role`, `semantic`, the resize methods, the interpolation values, the storage
  layout): no change.

### 2.2 Fields table

none. The change adds no field. A sidecar cannot change the limit: the limit is a property of the
host, not of the model.

| Field | Type | Required | Description |
|---|---|---|---|
| none | | | |

### 2.3 Behaviour

The new text, as it will appear in `specs/model-sidecar/pre/interpolation.md`. The links are
relative to that file.

```markdown
### Resize limit

A host can implement the resize step with code other than the OpenCV call of [Pixel centres](#pixel-centres), for example with ONNX nodes on a GPU. The reference result is the output of that OpenCV call. The call gets the same host frame, the same `interpolation`, the same `compute_dtype`, the same geometry and the same pad value or border value as the host. The result of the resize step is the image that the [normalization](normalization.md#behaviour) takes: the canvas with its pad for `letterbox`, the resized image for `stretch`, and the output of the warp with its border for `fit` and `affine_crop`.

Each implementation of the resize step must agree with the reference result within the resize limit:

- The result must have the shape and the channel order of the reference result.
- With `compute_dtype: uint8`, each value of the result must be an integer from 0 to 255. It can differ from the value at the same position of the reference result by at most 1. This is 1 step of `uint8`.
- With `compute_dtype: float32`, each value of the result must be finite. It can differ from the value at the same position of the reference result by at most `0.05` on the 0-255 scale.
- A difference that is equal to the limit is in the limit.

The limit applies only to the values of the image. It does not apply to the geometry. The host computes the scaled size, the offsets and the warp matrix `M` as [Precision](#precision) and the section of the method give. The host must use the filter of the [Behaviour](#behaviour) table and the pixel centres of the call of the method.

A `none` resize has no resize step. The host gives the host frame unchanged.

The spec starts at the host frame of [Input](../common/input.md#fields). The decode of an encoded image, for example a JPEG file, to the host frame is not a part of the spec. The limit compares two results of the same host frame.
```

The step has no inverse. It changes no coordinate.

Behaviour of the new step:

- NaN: a NaN value of the result is not in the limit. With `uint8`, it is not an integer. With
  `float32`, it is not finite. The reference result has no NaN, because the host frame is 8-bit.
- inf: an infinite value of the result is not in the limit (not finite).
- tie: a difference equal to the limit is in the limit. A `.5` tie of the filter can round up or
  down in a `uint8` result: both values are in the limit of 1 step.
- empty input: out of scope. Each method that resizes gives an image of at least 1x1 pixel, and
  the text defines no empty host frame. The reference implementation refuses an empty image.

### 2.4 Validation rules

No new rule. The limit is a rule for a host. A sidecar has no field for it, so a sidecar cannot fail
it.

The existing rules that name a value of this section do not change:

- `V-pre.resize.interpolation-1`: the values of `compute_dtype` stay `uint8` and `float32`.
- `V-pre.resize.interpolation-2`: a `uint8` pad value stays an integer from 0 to 255. The pad is a
  value of the result, so the limit also applies to it.
- `V-common.input-3`: the interpolation values stay `linear`, `area`, `cubic` and `nearest`. The
  limit applies to each value.

### 2.5 Selectors

No change: `input.resize.method=letterbox`, `input.resize.method=stretch`,
`input.resize.method=fit` and `input.resize.method=affine_crop`.

### 2.6 Changelog row

The number is the next free row when the change lands (53 at the commit of the header).

```markdown
| 53 | Resize | `pre.resize.interpolation` gets a resize limit: each implementation of the resize step can differ from the output of the OpenCV call of the method, before the normalization, by at most 1 step of `uint8` (`compute_dtype: uint8`) or `0.05` on the 0-255 scale (`compute_dtype: float32`). The geometry does not change. The decode of an encoded image to the host frame is not a part of the spec. | the skellytracker preprocess graph on the NVIDIA execution providers (user decisions 2026-11-17) | [Interpolation](pre/interpolation.md#resize-limit) |
```

## 3. Reference implementation

The section has a reference module, so this part gives that file with the change (heading "Full
section" of `specs/model-sidecar/model-addition-workflow/reference-implementations.md`). The
functions of the current text do not change. The new functions come from the text of part 2. The
package has no host code for them, so the note at the top of the file gives `none (no host code)` as
their source commit. The file imports no other section module and has no fixture.

| Item | Value |
|---|---|
| Reference file in the proposal bundle (`reference/<section_module>.py`) | `reference/pre_resize_interpolation.py` |
| Target file in skellytracker (`specs/model-sidecar/reference/<section_module>.py`) | `specs/model-sidecar/reference/pre_resize_interpolation.py` |
| Functions (one for each algorithm) | New: `resize_limit` (the limit of the compute dtype), `resize_difference` (the check of a result against the reference result) and `check_resize` (the case function of `resize_difference`). Unchanged: `interpolation_flag`, `compute_dtype`, `to_compute_dtype`, `pixel_centre`, `failed_rules`, `run`. |

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/pre.resize.interpolation.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/pre.resize.interpolation.yaml` |
| `verified_against` | `unverified: no host implementation: the package has no check of the resize limit yet. The evidence scripts measure the limit, but they have no function for these cases` |
| Cases with the `id` of a current case (`--replaces`) | none. The 4 current cases stay. |
| `fill` | `fill` wrote `expect` of each case with the file of part 3. It printed no problems. |

The 12 cases call `check_resize`. Each case gives two small HWC arrays: the reference result and the
result of a host. The cases cover each branch: equal results; the `.5` tie that a half-to-even
`Round` gives (a difference of 1, equal to the `uint8` limit); 2 steps; a fractional value and the
value 256 with `uint8`; a difference of 0.046875 (in the limit), 0.0625 and 1 (over the limit) with
`float32`; `cubic` values below 0 and above 255 with `float32`; a NaN value; an infinite value; and a
shape that is not the reference shape (`error: no-rule`, because the input is an image, not a sidecar
value). The value 0.05 has no exact float32 value, so no `float32` case gives a difference that is
equal to the limit. Each case with a partial `input.resize` block says in its `note` that it checks
only the resize limit and no `V-` rule.

No case is a pixel case: `expect` holds the largest difference and a boolean. A pixel case cannot
state the limit of `uint8` today. The vector comparison `agrees` of `tools/vector_form.py` makes
two integers match exactly, also with `compare.atol`.

## 5. Parity evidence

The scripts are in the skellytracker repository at `a50c759177a5bff5c5bc5b3a6ed16e40bdab133b`
(branch `dom/native-jpeg`, local, no permalink yet):

- `specs/model-sidecar/decisions/scripts/gpu_preprocess_graphs.py`: the preprocess graphs. It is
  not a script to run. `letterbox`: `Resize`, then `Pad` with `pad_value`. `affine_crop`:
  `GridSample` with the map of the warp matrix `M` of each ROI. `compute_dtype: uint8` adds
  `Floor(x + 0.5)` and `Clip(0, 255)`. `compute_dtype: float32` has no rounding and no clip.
- `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py`: the parity run. Three paths for
  each frame: `ref` (`cv2.imdecode`, the package CPU preprocess, the model session, the package
  decode), `dec` (the nvJPEG pixels copied to the host, then the same CPU path) and `gpu` (the nvJPEG
  pixels in VRAM, the preprocess graph, the same session with IO binding, the package decode).
  "Graph only" is `gpu` against `dec`: the graph against the CPU reference on the same decoded
  pixels. The differences are in `uint8` steps on the 0-255 scale, before the normalization.
- `specs/model-sidecar/decisions/scripts/gpu_preprocess_race.py`: a race test of the hand-over from
  the decode to the graph and from the graph to the model. It is evidence for the package (part 6),
  not for the limit: the decode is outside the spec.

Versions: onnxruntime 1.31.1, onnx 1.22.0, opencv-contrib-python 5.0.0.93, numpy 2.4.6,
nvidia-nvimgcodec-cu13 0.10.0.9, nvidia-nvjpeg 13.3.2.43. EP packs `cuda` (`cuda-cu13` 0.3.0) and
`trt-rtx` (`trt-rtx-cu13` 0.5.0, outside the ONNX Runtime range that NVIDIA tested). One NVIDIA
GeForce RTX 3070.

**Coverage.** The rule applies to all four methods that resize. Measured: `letterbox` and
`affine_crop`, with `linear`, `cubic` and `nearest`, `uint8` and `float32` (`nearest`: `uint8`
only). Not measured: `fit` and `stretch` (no graph was built), `area` (no ONNX operator), a
`pad_value` array, an `affine_crop` pad value other than 0, and the normalizations other than `none`
and `imagenet`.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | G1, pass gate: each value of the graph result is in the `uint8` limit of 1 step, for each image, on each EP. Source: plan decision 2 of part 1, set before the run. G2, gate for `float32`: before the run, the gate was 1.0 (the first draft of this proposal). After the run, the user decision 3 replaced it with 0.05, the value of part 2.3 (parity step 1: the old gate, the measurement and the reason are in this row and in the result). 0.05 is thus not a gate of this run. G3, control: the mean, the p99.9 and the share of the values that differ. G4, control: the final outputs of both models against the CPU path. No pass gate for the final outputs was set before the run. |
| Test images (paths or dataset IDs), and the branch that each image runs | 37 frames: 12 frames spread over each of the 3 camera videos of the freemocap test recording (`synchronized_videos` of the package test data) and one photo of the package test images, all 720x1280 (W x H). Each frame is also upscaled with `INTER_CUBIC` to 1080x1920. Each size is encoded at JPEG quality 90 with 4:2:2 and 4:2:0 chroma: 148 frame variants. 720x1280 to 640 (`letterbox`) is an exact 1/2 scale: it runs the `.5` ties. 1080x1920 to 640 is a 1/3 scale. The ROIs of `affine_crop` are the boxes of the `ref` path (140 persons): they run downscales and upscales. Not in the sample: a portrait frame, an odd pad gap, a `letterbox` upscale. |
| Upstream reference: library, version, config and command | Not an upstream library. The reference is the CPU path of the spec: `preprocess_image` of `skellytracker/core/detectors/processing/pre/preprocess.py` with OpenCV 5.0.0.93. A config `<compute_dtype>:<interpolation>` of the script sets `input.resize` of both sidecars in memory. Models: `yolox-person` (`letterbox`) and `rtmw-wholebody133` (`affine_crop`), size `m`, fp32, batch 3. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | not applicable. The ONNX files of the models do not change. |
| Preprocessed input: maximum absolute difference for each image | Graph only, both sizes, both EPs. `uint8` `linear`: `letterbox` max 0 (0% of the values differ); `affine_crop` max 1, p99.9 at most 0.001, mean 0.0001, 0.0092% to 0.0110% of the values differ. `float32` `linear`: `letterbox` max 0.000; `affine_crop` max 0.026 (`cuda`) and 0.035 (`trt-rtx`), p99.9 at most 0.006, mean 0.0001. `uint8` `cubic`: `letterbox` max 1 (0.17% at 720x1280, 0% at 1080x1920); `affine_crop` max 1 (about 0.011%). `float32` `cubic`: `letterbox` 0; `affine_crop` max 0.034 (`cuda`) and 0.032 (`trt-rtx`). `nearest`: `letterbox` max 0; `affine_crop` max 36 (`cuda`) and 11 (`trt-rtx`), about 0.002% of the values: a different source pixel. The script gives the values for all images of a size and a chroma, not for each image. |
| Row count for each image: sidecar path and upstream | `yolox-person`: 140 of 140 persons match on both EPs. `rtmw-wholebody133`: the same ROIs on each path. |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | Graph only, `uint8` `linear`. `object_detector` (`yolox-person`): boxes and scores, per-row differences: exactly 0 on both EPs. `keypoint_detector` (`rtmw-wholebody133`): keypoints with a score above 0.5, per-point distance in source pixels: max 4.46 px (`cuda`) and 4.00 px (`trt-rtx`), 99th percentile 0 px. |
| Result (`pass`, `fail` or `to run`) | `pass` for G1: `letterbox` and `affine_crop`, `linear` and `cubic`, both EPs. `float32`: the run passes the gate 1.0 that was set before the run. The max 0.035 is also in 0.05, but a run with the gate 0.05 set before the run is `to run`. `nearest` with `affine_crop`: `fail` (max 36 and 11): the package does not use the graph there (part 6). `fit` and `stretch`: not measured. |
| Script path in the exporter repo | `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py` (with `gpu_preprocess_graphs.py`) in the skellytracker repository |
| Exporter commit of the script | `a50c759177a5bff5c5bc5b3a6ed16e40bdab133b` (branch `dom/native-jpeg`, not on the default branch, no permalink yet) |
| Command | `uv run --no-sync python -B specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py --frames <videos folder> <photo> --configs uint8:linear float32:linear uint8:cubic float32:cubic uint8:nearest --ep cuda trt-rtx` (the form of the docstring of the script; the folder and the photo are local test data) |

## 6. skellytracker implementation proposal

This part is advisory. The implementer checks it.

The package uses the GPU graph only where the graph meets the limit. For each other case, it runs the
CPU reference path and gives one warning when the session opens:

- `interpolation: area`: ONNX has no operator for it.
- `interpolation: nearest` with `method: affine_crop`: the graph takes a different source pixel
  (measured 11 to 36 steps, part 5).
- `method: none` has no resize step.
- `fit`, `stretch`, a `pad_value` array and an `affine_crop` pad value other than 0 have no
  measurement yet (part 5). The implementer measures each one before the package uses the graph
  for it (inferred from "only where the graph meets the limit").

| Item | Value |
|---|---|
| Module and function | A new module under `skellytracker/core/detectors/processing/pre/`, for example `resize_graph.py`, from `gpu_preprocess_graphs.py` of part 5. It builds the preprocess graph for one sidecar, one size and one precision: `letterbox` with `Resize` (`linear`: `coordinate_transformation_mode: half_pixel`; `nearest`: `asymmetric` with `nearest_mode: floor`; `cubic`: `cubic_coeff_a: -0.75`) and `Pad`; `affine_crop` with a sampling grid from the inverse of `M` and `GridSample` (`align_corners=0`). With `compute_dtype: uint8`, the graph rounds with `Floor(x + 0.5)` and clips to 0..255. The normalization of `pre.normalize` follows in the same graph. A check `within_resize_limit` in `skellytracker/core/detectors/processing/pre/resize_interpolation.py` implements `resize_difference` of part 3. |
| Dispatch point | `preprocess_image` of `skellytracker/core/detectors/processing/pre/preprocess.py` stays the CPU reference path. The generic detectors call it (`skellytracker/core/detectors/generic/object_detector.py`, `skellytracker/core/detectors/generic/keypoint_detector.py`). The choice of the graph for `cuda` and `trt-rtx`, its session from `eps.build_session()`, and the transfer of the tensor on the device with IO binding: for the implementer. The hand-over from the decode stream to the graph needs a wait for the decode stream (`gpu_preprocess_race.py`). |
| Validator changes (`model.py`, with rule IDs) | none. The change has no new rule. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | The 12 cases of part 4 through `within_resize_limit`, in `skellytracker/tests/processing/test_preprocess.py`. The graph also runs on the CPU EP, so a test without a GPU can compare it with `resize_image` within the limit. A test with the marker `gpu` runs the same comparison on each installed NVIDIA EP pack. A test checks the one warning of each CPU-path case above. |
| Existing code that the change touches | `skellytracker/core/detectors/processing/pre/preprocess.py`, `skellytracker/core/detectors/processing/pre/resize_interpolation.py`, the generic detectors, `skellytracker/core/eps/` (`build_session`) and the `onnx_model` node of `skellytracker/core/pipelines/_runtime/`. Outside the package: the item "Cost of the detector preprocess" of `decisions/open-work.md` gets the sentence of part 2.1 on landing. The evidence scripts of part 5 need a decision entry that names them, because they are in `specs/model-sidecar/decisions/scripts/`. |

## 7. Exporter impact

No sidecar changes. The change adds no field and no rule. The CPU hosts of the exporters give the
output of the OpenCV call: their difference is 0, so they are in the limit with no change.

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `yolox-person` | none | none |
| OpenMMLab-Exporter | `rtmw-wholebody133` | none | none |

**Reference examples that the change makes invalid.** none. The change adds no rule and changes no
rule, so no example breaks a rule.

| Example (`inventory.yaml` key) | Rule ID | Impact (`forced-edit`, `needs-export` or `removed (user ruling)`) | Edit text |
|---|---|---|---|
| none | | | |

| Item | Value |
|---|---|
| Candidate example in the proposal bundle (`example/detectors/...`, or `none`) | none. No sidecar changes. |
| Writer code (file, function and commit) | none |
| `sidecar_refs.py --check` result | not applicable |

## 8. Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| The near-miss: the current text of `pre.resize.interpolation` ("must reproduce" the OpenCV call, with no limit) | A host must then give the OpenCV output bit for bit. The `affine_crop` graph differs by 1 step on about 0.01% of the values. | Part 5 |
| A limit of 0 for `uint8` | With `Floor(x + 0.5)`, `letterbox` gives 0, but `affine_crop` still gives 1 step. | Part 5 |
| A `float32` limit of 1.0, the same as `uint8` | A `float32` resize has no rounding step. 1.0 allows a difference of a full `uint8` step. The measured max is 0.035. | Part 5; plan decision 3 |
| A list of excluded methods or filters in the spec (for example `area`, or `nearest` with `affine_crop`) | The limit applies to each host implementation. The choice of the CPU path is a property of the package, so it is implementer guidance (part 6). | Plan decision 4 |
| The rule in each section `pre.resize.<method>` | Four copies of one rule. A rule has one place, and the other sections link to it. `pre.resize.affine_crop` has an owner, so a new proposal by this contributor cannot change it. | Heading "Section owner" of `specs/model-sidecar/model-addition-workflow/hand-over.md`; `intake_bundle.py list` at the commit of the header |
| The rule in `common.input` | `common.input` defines the host frame, not the filter. It has an owner, so a new proposal by this contributor cannot change it. | Same as above |
| A sidecar field, for example `input.resize.tolerance` | The limit is a property of the host, not of the model. Each sidecar would need a value. | none |
| The limit after the normalization (on the model input) | The effect of 1 step then depends on `mean` and `std` and on `input.dtype`. The limit is before the normalization. | Plan decision 2 |
| A limit on the mean or on a percentile, in addition to the maximum | The maximum is enough for the measured paths. The mean is 0.0001 steps for `affine_crop` and 0 for `letterbox`. | Part 5 |
| Include the decode of an encoded image in the limit | The spec starts at the host frame. A GPU decoder can differ from the CPU decoder. That difference is not a part of the resize step. | Paragraph "Host frame" of `common.input`; plan decision 5 |

The spec defect of `cv2.warpAffine` with `cv2.INTER_AREA` (it runs as `cv2.INTER_LINEAR`, OpenCV
4.13.0; heading "Spec defects" of `specs/model-sidecar/decisions/open-work.md`) does not change. The
reference result stays the output of the call.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal. n/a: no model intake. The change does not
      come from an intake row.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it.
- [x] Part 1 cites primary evidence, or names the primary evidence that is missing.
- [x] Part 1 gives each plan decision about the spec in words, with no item number, or `none`.
- [x] Part 2.1 lists each place that the change edits.
- [x] Part 2 gives the behaviour of each new step on NaN, on inf, on a tie and on an empty input, or
      `out of scope`, as part 2 of "The parts of a proposal" in
      `specs/model-sidecar/model-addition-workflow/phase-2-proposal.md` says.
- [x] Part 3 names the reference file, and the file exists in the proposal bundle.
- [x] Part 4 names the vector file, and the file exists in the proposal bundle. `fill` wrote its `expect`.
- [x] Part 4 gives `verified_against`, or `unverified: <reason>`.
- [x] Each pixel case in part 4 has its tolerance in `compare`. n/a: no pixel case.
- [x] Each case with a partial input in part 4 names in its `note` the rules that it checks, as part 4
      of "The parts of a proposal" in the same file says.
- [x] Part 5 gives the numbers, the script path and the commit, or says `to run` and describes the
      script. Tick this box also for `to run` with a description of the script.
- [x] If the result of part 5 is `pass` or `fail`, the parity script is committed in the exporter
      repo. The script is committed in the skellytracker repository, the repository of this
      contributor.
- [x] Part 7 lists each example that the change makes invalid, or says `none` with the reason.
- [x] Each citation of a spec text, a base file or a record names a heading or a case `id`, not a
      line number of a copy.
- [x] Each citation of upstream code or of the code of another repo is a permalink with a full
      40-character SHA, as "Sources" in `specs/model-sidecar/model-addition-workflow/rules.md` says.
      This proposal cites no upstream line. The scripts are in the repository of this contributor:
      part 5 gives the full SHA, the branch and the paths. A permalink is missing until the branch
      is pushed.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
      `pack` did not run yet.
