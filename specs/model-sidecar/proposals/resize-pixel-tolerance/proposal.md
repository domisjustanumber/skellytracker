# Change proposal: resize-pixel-tolerance

This file follows the change proposal template (`specs/model-sidecar/templates/change-proposal.md`).
It names each skellytracker file by its path in a code span, each spec section by its section ID, and
each spec heading by its text and the section file that holds it. It has no relative links.

## Changes in this version

This is version 2 of the bundle `proposal-resize-pixel-tolerance@skellytracker`. Version 1 is
recorded as the `proposed` entry J1HK. The changes:

- User decisions after version 1: the `uint8` integer rule stays; the limit covers the whole result,
  with the pad and the border; the check compares in float64; `tools/vector_form.py` stays
  unchanged, and its integer match goes on the spec-defect list at the landing (part 1, part 2).
- Part 2.3: one sentence for the whole result, one sentence for the float64 comparison, and a note
  on its effect.
- Part 2.1: the spec-defect item of `specs/model-sidecar/decisions/open-work.md` is a new place.
- Part 3 and part 4: the reference module states the float64 comparison. One new case
  (`limit-float32-float32-of-0.05-is-over-the-limit`): 13 cases. The stale status note of the module
  is corrected.
- Part 1: the primary sources of the causes, pinned. The source shows that the cause of the
  `affine_crop` difference is different for `linear` and for `cubic`.
- Part 5: a new run with the gates G1 and G2 as constants in the script before the run, for all
  four methods, 42 configurations on each EP. The first run (version 1) stays valid as the first
  run. G4 is a control with no gate.
- Part 6: the measured CPU-path cases. Part 7: only measured or cited claims about other hosts.
- Header: the new evidence commit and the new checkout commit.

## Header

| Field | Value |
|---|---|
| Title | A resize implementation can differ from the reference by at most 1 `uint8` step |
| Slug | `resize-pixel-tolerance` |
| Date | 2026-11-17 |
| Exporter repo | none. The contributor is skellytracker (contributor name `skellytracker`). The evidence scripts are in the skellytracker repository. |
| Exporter commit (`git rev-parse HEAD` in the exporter repo, or `none (no git repo)`) | `bea4007ef19474c8da66613dcf08f68fa418373a`, branch `dom/native-jpeg` of the skellytracker repository, commit subject "Add the fit and stretch graphs and the gates to the evidence scripts of the GPU preprocess path". The commit is local. It is not on the default branch, so it is a secondary source, and it has no permalink yet. |
| Model, and its `model` bundle ID | `yolox-person` (`model-yolox-person@openmmlab-exporter`) and `rtmw-wholebody133` (`model-rtmw-wholebody133@openmmlab-exporter`). Both are landed. The rule is for each model that resizes. It does not come from an intake. |
| Intake rows with the verdict `near-miss` or `gap` | none. No model intake has a row for this property. The gap is a host property: the spec gives no limit for a different implementation of the resize step. |
| Kind (`new section`, `changed section`, `contribution` or `follow-up`) | `changed section` |
| Base bundle of a follow-up (`base`, or `none`) | none |
| Proposed section ID (the `id` in the section file's front matter) | `pre.resize.interpolation` |
| Section file (the file of the changed section, or the proposed path of the new section file under `specs/model-sidecar/`) | `specs/model-sidecar/pre/interpolation.md` |
| Depends on (`depends_on`: bundle IDs that must land first, or `none`) | none |
| skellytracker decision entries with the status `proposed` that cover the same property (or `none`) | J1HK, the entry of version 1 of this bundle. No other entry. |
| skellytracker folder that you read (normally `../freemocap/skellytracker`) | `../freemocap/skellytracker` (the main checkout) |
| skellytracker commit of the spec text that you read (`git -C <folder> rev-parse HEAD`; add `+ uncommitted changes` if `git -C <folder> status --porcelain` lists a file that you read) | `e85c247262d9d892c82840f001f4e1038ea7d2f1` |
| Target spec version: the newest version heading under "Revisions" in `specs/model-sidecar/changelog.md`, today the open target `2.0.0`. `pack` writes it to the manifest as `spec_version`. | `2.0.0` |

## 1. Gap

The package gets a second implementation of the resize step: ONNX nodes that run on the GPU (a
"preprocess graph") for the NVIDIA execution providers `cuda` and `trt-rtx`. The CPU code stays the
normative reference. The spec defines each resize result as the output of one OpenCV call. It gives
no limit for a different implementation, so a host must give the OpenCV output bit for bit. The
ONNX nodes cannot do this for each method and each filter.

The probable causes of the differences:

- The ONNX `Round` node rounds a `.5` tie half to even. The `uint8` filters of OpenCV round half up.
  With `Round`, 6.6% of the `letterbox` values differed by 1 step at 720x1280 in the first run, all
  at exact ties. The graph now rounds with `Floor(x + 0.5)`, and the `uint8` `linear` `letterbox`
  difference is 0.
- OpenCV computes some weights and source positions in fixed point or in float32. The ONNX nodes
  compute them in their own floating point. The source shows two different paths for a `uint8`
  warp: `linear` uses a new kernel that converts `M` to float32, and `cubic` uses fixed-point source
  positions with 1/32-pixel steps. Both give at most 1 step on about 0.01% of the `affine_crop`
  values. The causes are read from the source. They are not measured separately.

The decode of an encoded image (for example a JPEG file) to the host frame is out of scope. The spec
starts at the host frame: the paragraph "Host frame" under the heading "Fields" of `common.input`
(`specs/model-sidecar/common/input.md`) says "The host gets each frame as an 8-bit, 3-channel BGR
image in HWC layout". The limit compares two resize results of the same host frame.

| Item | Value |
|---|---|
| Property | The largest difference between the resize result of a host and the output of the OpenCV call of the method, for each value of the whole result, on the 0-255 scale, before the normalization. |
| Upstream evidence (file and line, or config key; full upstream SHA, then the tag) | This is a host property, not a property of an upstream model. The spec text: heading "Behaviour" of `pre.resize.interpolation` says "If a host uses another library, it must reproduce that behaviour and the pixel centres of the call". Heading "Compute dtype" says that a `uint8` result "is the 8-bit output of the OpenCV filter". The sources of the causes are in the table "Sources of the causes" below. They only explain the numbers. The limit does not need them. |
| Plan decisions about the spec that this proposal uses, in words (or `none`) (heading "User decisions" in `specs/model-sidecar/model-addition-workflow/rules.md`) | (1) The package gets a second implementation of the resize step as ONNX nodes for the NVIDIA execution providers. The CPU code stays the normative reference. (2) With `compute_dtype: uint8`, a resize implementation can differ from the reference by at most 1 `uint8` step, on the 0-255 scale, before the normalization. Each value of the result is an integer from 0 to 255. (3) With `compute_dtype: float32`, the limit is 0.05 on the 0-255 scale. The check converts both results to float64. (4) The limit covers the whole result, with the pad of `letterbox` and the border of the warp. (5) The limit applies to each host implementation. The spec gets no list of excluded methods or filters. The package uses the GPU graph only where the graph meets the limit (part 6). (6) The decode of an encoded image to the host frame is out of scope. (7) On landing, the item "Cost of the detector preprocess" of `decisions/open-work.md` gets one more sentence (part 2.1). (8) `tools/vector_form.py` stays unchanged. Its integer match goes on the spec-defect list of `specs/model-sidecar/decisions/open-work.md` at the landing (part 2.1). |
| Nearest section ID (the `id` in the section file's front matter) | `pre.resize.interpolation` |
| Why the nearest section is wrong | The section names one OpenCV call for each method and says that another library "must reproduce" it. It gives no limit. A GPU graph with a 1-step difference on 0.01% of the values does not reproduce the call, but the detections of `yolox-person` do not change for `letterbox` (part 5). |
| Measured difference (number, image and script) | Part 5. Summary of the run with the gates, graph only (the graph against the CPU reference on the same decoded pixels), on both EPs: each `uint8` configuration has a max of 0 or 1 step, and each `float32` configuration a max of at most 0.0333, except `nearest` with `affine_crop` (max 41 on `cuda` and 14 on `trt-rtx`). Script: `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py` at `bea4007ef19474c8da66613dcf08f68fa418373a`. |
| Model in "Scope of this revision" (`specs/model-sidecar/changelog.md`): yes, or no (it joins the list on acceptance; do not write a scope entry) | yes: OpenMMLab-Exporter RTMW and YOLOX (person). |
| Row in "Considered and deliberately not added" (`specs/model-sidecar/changelog.md`), and the evidence that a model needs it now (or `none`) | none. The nearest row is `resize.antialias`. This proposal adds no antialias. The resize stays non-antialiased. |

**Sources of the causes.** Each line below was read in the raw file at the pinned commit on
2026-11-17.

| Cause | Source | Line |
|---|---|---|
| ONNX `Round` rounds half to even | [onnx `docs/Operators.md` L38154](https://github.com/onnx/onnx/blob/fb7487d6bf8d79c0dea5b421d09a54a58056fdf3/docs/Operators.md?plain=1#L38154) (default branch `main`) | "In case of halves, the rule is to round them to the nearest even integer." The installed version 1.22.0 has the same sentence at line 32959 of the same file at `2bb50465112feca9003e1ed654d77f01ff1415ca`, tag `v1.22.0`. That commit is on the branch `rel-1.22.0`, not on `main` (secondary). |
| OpenCV fixed-point positions: 1/32 pixel | [opencv `modules/imgproc/include/opencv2/imgproc.hpp` L287-L289](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/include/opencv2/imgproc.hpp#L287-L289), tag `5.0.0` | `INTER_BITS = 5,` and `INTER_TAB_SIZE = 1 << INTER_BITS,` |
| `uint8` `cubic` warp: fixed-point source positions | [opencv `modules/imgproc/src/imgwarp.cpp` L1997](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/imgwarp.cpp#L1997) and [L2437](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/imgwarp.cpp#L2437), tag `5.0.0` | `const int AB_BITS = MAX(10, (int)INTER_BITS);` and `int X = (X0 + adelta[x1]) >> (AB_BITS - INTER_BITS);`. This path runs only when no new kernel takes the call. 5.0.0 has new kernels for `nearest` and `linear` (next row), not for `cubic`. |
| `uint8` `linear` warp: a new kernel in float32 | [opencv `modules/imgproc/src/imgwarp.cpp` L2304](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/imgwarp.cpp#L2304) and [`modules/imgproc/src/warp_kernels.simd.hpp` L3167](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/warp_kernels.simd.hpp#L3167) and [L3260](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/warp_kernels.simd.hpp#L3260), tag `5.0.0` | `CV_CPU_DISPATCH(warpAffineLinearInvoker_8UC3, ...)`; the kernel converts `M` to float32 (`M[i] = static_cast<float>(dM[i]);`) and computes `float sx = x*M[0] + y*M[1] + M[2];`. `CV_CPU_DISPATCH` returns, so a `uint8` `linear` warp does not reach L1997 and L2437. |
| `uint8` `linear` resize: fixed-point weights that round half up | [opencv `modules/imgproc/src/resize.cpp` L962](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/resize.cpp#L962) and [L1018-L1020](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/resize.cpp#L1018-L1020), tag `5.0.0` | `const int INTER_RESIZE_COEF_BITS=11;`; `DELTA = 1 << (bits-1)` and `saturate_cast<DT>((val + DELTA)>>SHIFT);`. At an exact scale of 1/2 on both axes, `linear` takes the area path instead ([L4019-L4020](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/resize.cpp#L4019-L4020)). |
| Caveat for `cv2.resize` | [opencv `modules/imgproc/src/resize.cpp` L3856](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/imgproc/src/resize.cpp#L3856), tag `5.0.0` | `CV_IPP_RUN_FAST(ipp_resize(...))` runs before these paths. Nobody checked whether IPP takes the call in the installed wheel (opencv-contrib-python 5.0.0.93). Thus the cause stays probable for `cv2.resize`. |

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
| `specs/model-sidecar/decisions/open-work.md` (spec log; a non-spec edit) | "Spec defects" | A new item: "A pixel case cannot state a limit on integer values. `agrees` of `tools/vector_form.py` makes two integers match exactly, also with `compare.atol`. Part 4 of the change proposal template says that a pixel case states its tolerance in `compare`. The vector cases of `pre.resize.interpolation` test the check of the resize limit, not two images." |

The template lists only places of the spec. The last two rows are non-spec edits of the landing.
Part 6 also names them.

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
- The limit applies to each value of the whole result, also to the pad of `letterbox` and to the border of the warp.
- With `compute_dtype: uint8`, each value of the result must be an integer from 0 to 255. It can differ from the value at the same position of the reference result by at most 1. This is 1 step of `uint8`.
- With `compute_dtype: float32`, each value of the result must be finite. The check converts both results to float64. Then it compares the absolute difference of each value with `0.05`, on the 0-255 scale.
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
- float64 comparison: a difference is measured on the float64 values of the float32 results. The
  value 0.05 has no exact float32 value. Thus a float32 result that is `float32(0.05)` against a
  reference value of 0 differs by 0.05000000074505806, and it is over the limit.
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
| 53 | Resize | `pre.resize.interpolation` gets a resize limit: each implementation of the resize step can differ from the output of the OpenCV call of the method, before the normalization, by at most 1 step of `uint8` (`compute_dtype: uint8`, each value an integer from 0 to 255) or `0.05` on the 0-255 scale, compared in float64 (`compute_dtype: float32`). The limit covers the whole result, with the pad and the border. The geometry does not change. The decode of an encoded image to the host frame is not a part of the spec. | the skellytracker preprocess graph on the NVIDIA execution providers (user decisions 2026-11-17) | [Interpolation](pre/interpolation.md#resize-limit) |
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
| Functions (one for each algorithm) | New: `resize_limit` (the limit of the compute dtype), `resize_difference` (the check of a result against the reference result, in float64) and `check_resize` (the case function of `resize_difference`). Unchanged: `interpolation_flag`, `compute_dtype`, `to_compute_dtype`, `pixel_centre`, `failed_rules`, `run`. |

## 4. Vectors

| Item | Value |
|---|---|
| Vector file in the proposal bundle | `vectors/pre.resize.interpolation.yaml` |
| Target file in skellytracker | `specs/model-sidecar/vectors/pre.resize.interpolation.yaml` |
| `verified_against` | `unverified: no host implementation: the package has no check of the resize limit yet. The evidence scripts measure the limit, but they have no function for these cases` |
| Cases with the `id` of a current case (`--replaces`) | none. The 4 current cases stay. |
| `fill` | `fill` wrote `expect` of each case with the file of part 3. It printed no problems. |

The 13 cases call `check_resize`. Each case gives two small HWC arrays: the reference result and the
result of a host. The cases cover each branch: equal results; the `.5` tie that a half-to-even
`Round` gives (a difference of 1, equal to the `uint8` limit); 2 steps; a fractional value and the
value 256 with `uint8`; with `float32`, a difference of 0.046875 (in the limit), 0.0625, 1 and
`float32(0.05)` against 0 (over the limit, because the check compares in float64); `cubic` values
below 0 and above 255 with `float32`; a NaN value; an infinite value; and a shape that is not the
reference shape (`error: no-rule`, because the input is an image, not a sidecar value). Each case
with a partial `input.resize` block says in its `note` that it checks only the resize limit and no
`V-` rule.

No case compares two integer images with a tolerance: the cases test the check of the limit. The
vector comparison `agrees` of `tools/vector_form.py` makes two integers match exactly, also with
`compare.atol`. That file stays unchanged. Part 2.1 puts this point on the spec-defect list at the
landing.

## 5. Parity evidence

The scripts are in the skellytracker repository at `bea4007ef19474c8da66613dcf08f68fa418373a`
(branch `dom/native-jpeg`, local, no permalink yet):

- `specs/model-sidecar/decisions/scripts/gpu_preprocess_graphs.py`: the preprocess graphs. It is
  not a script to run.
- `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py`: the parity run. The gates are
  constants of the script: `G1_MAX_ABS_UINT8 = 1.0` and `G2_MAX_ABS_FLOAT32 = 0.05`. A configuration
  gets `PASS` when its max is at most the limit and it has 0 bad values. A bad value is a non-finite
  value, and with `uint8` also a non-integer or a value outside 0..255. "Graph only" is the graph
  output against the package CPU resize of the same decoded pixels, over the whole result, with the
  pad and the border.
- `specs/model-sidecar/decisions/scripts/gpu_preprocess_race.py`: a race test of the hand-over from
  the decode to the graph and from the graph to the model. It is evidence for the package (part 6),
  not for the limit: the decode is outside the spec.

Versions: onnxruntime 1.31.1, onnx 1.22.0, opencv-contrib-python 5.0.0.93, numpy 2.4.6,
nvidia-nvimgcodec-cu13 0.10.0.9, nvidia-nvjpeg 13.3.2.43. EP packs `cuda` (`cuda-cu13` 0.3.0) and
`trt-rtx` (`trt-rtx-cu13` 0.5.0, state `untested-ort`: not tested with ONNX Runtime 1.31.1). One
NVIDIA GeForce RTX 3070. Run of 2026-11-17.

**Two runs.** The first run (version 1 of this bundle) measured `letterbox` and `affine_crop` with a
`float32` gate of 1.0. Its numbers stay valid as the first run. The run below set the gates G1 and G2
as constants before the run. It closes the `to run` item of the `float32` gate 0.05 of version 1.

**Coverage.** 42 configurations on each EP: the four methods, `uint8` and `float32`, `linear`,
`cubic` and `nearest`, with the default pad (`letterbox` 114, `fit` 114, `affine_crop` 0), and
`letterbox`, `fit` and `affine_crop` again with the pad or border value `10,128,240`. Not measured:
`area` and the normalizations other than `none` and `imagenet`. The graphs refuse them. The
normalization is after the resize, outside the limit.

| Item | Value |
|---|---|
| Gates, set before the run, their source, and pass gate or control | G1, pass gate: `compute_dtype: uint8`, each value an integer from 0 to 255 and max at most 1. G2, pass gate: `compute_dtype: float32`, each value finite and max at most 0.05, in float64. Source: plan decisions 2 and 3 of part 1, set as constants of the script before the run. G3, control: the share of the values over 0.5 and over 0.01. G4, control with no gate: the final outputs of the models on the graph output against the CPU path. |
| Test images (paths or dataset IDs), and the branch that each image runs | 37 frames: 12 frames spread over each of the 3 camera videos of the freemocap test recording (`synchronized_videos` of the package test data) and one photo of the package test images, all 720x1280 (W x H). Each frame is also upscaled with `INTER_CUBIC` to 1080x1920. Each size is encoded at JPEG quality 90 with 4:2:2 and 4:2:0 chroma: 148 frame variants, and 136 with a person for `affine_crop`. 720x1280 to 640 is an exact 1/2 scale (the `.5` ties of `letterbox`, and the area path of `cv2.resize`). 1080x1920 to 640 is a 1/3 scale. The ROIs of `affine_crop` are the `yolox-person` boxes of the CPU path: they run downscales and upscales. `nearest` with `fit` gives 0 here, but the scales of the sample are exactly 1/2 and 1/3: this is not evidence for other scales (inferred by the measurer). Not in the sample: a portrait frame, an odd pad gap, a `letterbox` upscale. |
| Upstream reference: library, version, config and command | Not an upstream library. The reference is the package CPU resize of the spec (`skellytracker/core/detectors/processing/pre/preprocess.py`) with OpenCV 5.0.0.93. A configuration `<method>:<compute_dtype>:<interpolation>:<pad>` sets `input.resize` of a landed sidecar in memory: `letterbox`, `stretch` and `fit` in front of `yolox-person`, `affine_crop` in front of `rtmw-wholebody133`; size `m`, fp32, batch 3. |
| Export error: the ONNX file on the upstream tensor, compared with the upstream model (metric and value) | not applicable. The ONNX files of the models do not change. |
| Preprocessed input: maximum absolute difference for each image | The script prints one `IMAGE` line with the graph-only max of each image (6072 lines on each EP). The full list for each image is the script output. In the limit: 6064 of 6072 on `cuda` and 6068 of 6072 on `trt-rtx`. The others are `nearest` with `affine_crop`: on `cuda` 2 images (40 and 41 steps), on `trt-rtx` 1 image (14 steps), in each of the 4 such configurations. The table "GATE lines" below gives the max of each configuration. |
| Row count for each image: sidecar path and upstream | `yolox-person` on the graph output against the CPU path: 140 of 140 persons match (`letterbox`), 136 of 136 (`stretch`, `fit`), no person only on one path. `rtmw-wholebody133`: the same 140 ROIs on each path. |
| Final outputs of each role (Parity, step 5): the compared output, metric and value | G4, control with no gate. `object_detector` (`yolox-person`), box corner distance and score difference: `letterbox` `uint8` `linear` 0 and 0; `letterbox` `uint8` `cubic` max 3.580 px (`cuda`) and 3.531 px (`trt-rtx`); `stretch` `uint8` `linear` max 6.505 px and 6.304 px, p99 0.326 px and 0.330 px; `fit` `float32` `linear` max 0.490 px and 0.488 px. `keypoint_detector` (`rtmw-wholebody133`), keypoints with a score above 0.5, distance in source pixels: `uint8` `linear` max 4.457 px (`cuda`) and 4.002 px (`trt-rtx`), p99 0 px; `float32` `linear` max 4.388 px and 3.727 px, p99 0 px. |
| Result (`pass`, `fail` or `to run`) | `pass` for 38 of 42 configurations on each EP. `fail` for the 4 configurations of `nearest` with `affine_crop` (2 compute dtypes, 2 border values): the package does not use the graph there (part 6). Bad values: 0 in each configuration. Nodes on the CPU: 0 in each graph session on both EPs. |
| Script path in the exporter repo | `specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py` (with `gpu_preprocess_graphs.py`) in the skellytracker repository |
| Exporter commit of the script | `bea4007ef19474c8da66613dcf08f68fa418373a` (branch `dom/native-jpeg`, not on the default branch, no permalink yet) |
| Command | `uv run --no-sync python -B specs/model-sidecar/decisions/scripts/gpu_preprocess_parity.py --frames <videos folder> <photo> --ep cuda`, and the same with `--ep trt-rtx`. With no `--configs`, the script runs its default list: the 42 configurations above. The folder and the photo are the local test data. |

**GATE lines** (quoted from the script output; the columns after the max are cut):

| Configuration | `cuda` | `trt-rtx` |
|---|---|---|
| `letterbox:uint8:linear:default` | `PASS (G1 <= 1.0) max 0.0000 >0.5 0.0000%` | `PASS (G1 <= 1.0) max 0.0000 >0.5 0.0000%` |
| `letterbox:uint8:cubic:default` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0858%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0858%` |
| `letterbox:uint8:nearest:default` | `PASS (G1 <= 1.0) max 0.0000` | `PASS (G1 <= 1.0) max 0.0000` |
| `letterbox:float32:{linear,cubic,nearest}:default` | `PASS (G2 <= 0.05) max 0.0000` (each) | `PASS (G2 <= 0.05) max 0.0000` (each) |
| `stretch:uint8:linear:default` | `PASS (G1 <= 1.0) max 1.0000 >0.5 2.6104%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 2.6104%` |
| `stretch:uint8:cubic:default` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0540%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0540%` |
| `stretch:uint8:nearest:default` | `PASS (G1 <= 1.0) max 0.0000` | `PASS (G1 <= 1.0) max 0.0000` |
| `stretch:float32:linear:default` | `PASS (G2 <= 0.05) max 0.0000` | `PASS (G2 <= 0.05) max 0.0000` |
| `stretch:float32:cubic:default` | `PASS (G2 <= 0.05) max 0.0001` | `PASS (G2 <= 0.05) max 0.0001` |
| `stretch:float32:nearest:default` | `PASS (G2 <= 0.05) max 0.0000` | `PASS (G2 <= 0.05) max 0.0000` |
| `fit:uint8:{linear,cubic,nearest}:default` | `PASS (G1 <= 1.0) max 0.0000` (each) | `PASS (G1 <= 1.0) max 0.0000` (each) |
| `fit:float32:linear:default` | `PASS (G2 <= 0.05) max 0.0128` | `PASS (G2 <= 0.05) max 0.0128` |
| `fit:float32:cubic:default` | `PASS (G2 <= 0.05) max 0.0139` | `PASS (G2 <= 0.05) max 0.0139` |
| `fit:float32:nearest:default` | `PASS (G2 <= 0.05) max 0.0000` | `PASS (G2 <= 0.05) max 0.0000` |
| `affine_crop:uint8:linear:default` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0102%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0099%` |
| `affine_crop:uint8:cubic:default` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0112%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0112%` |
| `affine_crop:uint8:nearest:default` | `FAIL (G1 <= 1.0) max 41.0000 >0.5 0.0036%` | `FAIL (G1 <= 1.0) max 14.0000 >0.5 0.0015%` |
| `affine_crop:float32:linear:default` | `PASS (G2 <= 0.05) max 0.0298` | `PASS (G2 <= 0.05) max 0.0283` |
| `affine_crop:float32:cubic:default` | `PASS (G2 <= 0.05) max 0.0293` | `PASS (G2 <= 0.05) max 0.0333` |
| `affine_crop:float32:nearest:default` | `FAIL (G2 <= 0.05) max 41.0000` | `FAIL (G2 <= 0.05) max 14.0000` |
| `letterbox:*:*:10,128,240` (6 configurations) | `PASS`, the same max as the default pad | `PASS`, the same max as the default pad |
| `fit:*:*:10,128,240` (6 configurations) | `PASS`, the same max as the default pad | `PASS`, the same max as the default pad |
| `affine_crop:uint8:linear:10,128,240` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0107%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0102%` |
| `affine_crop:uint8:cubic:10,128,240` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0116%` | `PASS (G1 <= 1.0) max 1.0000 >0.5 0.0115%` |
| `affine_crop:float32:linear:10,128,240` | `PASS (G2 <= 0.05) max 0.0298` | `PASS (G2 <= 0.05) max 0.0313` |
| `affine_crop:float32:cubic:10,128,240` | `PASS (G2 <= 0.05) max 0.0293` | `PASS (G2 <= 0.05) max 0.0333` |
| `affine_crop:{uint8,float32}:nearest:10,128,240` | `FAIL`, max 41.0000 (each) | `FAIL`, max 14.0000 (each) |

**Race test** (`gpu_preprocess_race.py`, evidence for part 6): both paths, both EPs, 0 wrong of 1000
with the wait for the decode stream. Open observation, not a result of the limit: one later run of
the race script hung at the exit of the process after it printed all results, while another GPU
process used the same card. One run again with a watchdog finished normally.

## 6. skellytracker implementation proposal

This part is advisory. The implementer checks it.

The package uses the GPU graph only where the graph meets the limit. For each other case, it runs the
CPU reference path and gives one warning when the session opens:

- `interpolation: area`: ONNX has no operator for it. The graphs refuse it.
- `interpolation: nearest` with `method: affine_crop`: the graph takes a different source pixel
  (max 41 steps on `cuda` and 14 on `trt-rtx`, part 5).
- `method: none` has no resize step.
- A normalization other than `none` and `imagenet`: the graphs refuse it. The normalization is not
  a part of the limit.
- `nearest` with `fit` at a scale that is not 1/2 or 1/3: not measured. The implementer measures it
  before the package uses the graph for it (inferred from "only where the graph meets the limit").

| Item | Value |
|---|---|
| Module and function | A new module under `skellytracker/core/detectors/processing/pre/`, for example `resize_graph.py`, from `gpu_preprocess_graphs.py` of part 5. It builds the preprocess graph for one sidecar, one size and one precision: `letterbox` and `stretch` with `Resize` (`linear`: `coordinate_transformation_mode: half_pixel`; `nearest`: `asymmetric` with `nearest_mode: floor`; `cubic`: `cubic_coeff_a: -0.75`), and `Pad` for `letterbox`; `fit` and `affine_crop` with a sampling grid from the inverse of `M` and `GridSample` (`align_corners=0`). With `compute_dtype: uint8`, the graph rounds with `Floor(x + 0.5)` and clips to 0..255. The normalization of `pre.normalize` follows in the same graph. A check `within_resize_limit` in `skellytracker/core/detectors/processing/pre/resize_interpolation.py` implements `resize_difference` of part 3. |
| Dispatch point | `preprocess_image` of `skellytracker/core/detectors/processing/pre/preprocess.py` stays the CPU reference path. The generic detectors call it (`skellytracker/core/detectors/generic/object_detector.py`, `skellytracker/core/detectors/generic/keypoint_detector.py`). The choice of the graph for `cuda` and `trt-rtx`, its session from `eps.build_session()`, and the transfer of the tensor on the device with IO binding: for the implementer. The hand-over from the decode stream to the graph needs a wait for the decode stream (`gpu_preprocess_race.py`). |
| Validator changes (`model.py`, with rule IDs) | none. The change has no new rule. |
| Tests (the vectors of part 4, and a golden parity test, for example in `skellytracker/tests/sidecar/`) | The 13 cases of part 4 through `within_resize_limit`, in `skellytracker/tests/processing/test_preprocess.py`. The graph also runs on the CPU EP, so a test without a GPU can compare it with `resize_image` within the limit. A test with the marker `gpu` runs the same comparison on each installed NVIDIA EP pack. A test checks the one warning of each CPU-path case above. |
| Existing code that the change touches | `skellytracker/core/detectors/processing/pre/preprocess.py`, `skellytracker/core/detectors/processing/pre/resize_interpolation.py`, the generic detectors, `skellytracker/core/eps/` (`build_session`) and the `onnx_model` node of `skellytracker/core/pipelines/_runtime/`. Outside the package, on landing: the sentence of part 2.1 in the item "Cost of the detector preprocess" of `decisions/open-work.md`, and the spec-defect item of part 2.1 in `specs/model-sidecar/decisions/open-work.md`. The evidence scripts of part 5 need a decision entry that names them, because they are in `specs/model-sidecar/decisions/scripts/`. |

## 7. Exporter impact

No sidecar changes. The change adds no field and no rule. The limit applies to each host, also the
host of an exporter. This proposal measured no exporter host. The Implementer guidance of
`pre.resize.interpolation` gives these facts:

- The OpenMMLab-Exporter host calls `cv2.resize` and `cv2.warpAffine`, the calls of the section.
  No measurement compares it with the OpenCV version of the reference.
- A text copy of the Roboflow-Exporter host resizes in float32 with float32 source coordinates. On
  a 1080x1920 noise image, it differs from `cv2.resize` in float32 by up to 2.19e-2 (0-255). This
  value is in the `float32` limit 0.05. It is a measurement of a copy on noise, not of the host on
  real images.
- The evaluation host of Qualcomm-Exporter resizes with PIL `Image.BILINEAR`. The section says that
  PIL `BILINEAR` does not reproduce the OpenCV filter. No measurement exists.

No example of Roboflow-Exporter or Qualcomm-Exporter is landed. The table lists the sidecar groups
of the section rows of `specs/model-sidecar/TRACEABILITY.md`.

| Owner repo | Inventory key or model | Change (`none`, new fields, or regenerate) | Host decoder change |
|---|---|---|---|
| OpenMMLab-Exporter | `yolox-person` | none | none known. Not measured against the limit. |
| OpenMMLab-Exporter | `rtmw-wholebody133` | none | none known. Not measured against the limit. |

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
| The near-miss: the current text of `pre.resize.interpolation` ("must reproduce" the OpenCV call, with no limit) | A host must then give the OpenCV output bit for bit. The graphs differ by 1 step for `stretch`, `affine_crop` and `cubic`. | Part 5 |
| A limit of 0 for `uint8` | With `Floor(x + 0.5)`, `letterbox` `linear` and `fit` give 0, but `stretch`, `affine_crop` and `cubic` still give 1 step. | Part 5 |
| A `float32` limit of 1.0, the same as `uint8` | A `float32` resize has no rounding step. 1.0 allows a difference of a full `uint8` step. The measured max is 0.0333. | Part 5; plan decision 3 |
| A `float32` comparison in float32 | 0.05 has no exact float32 value, so the result of the check would depend on the order of the casts. The check converts both results to float64 and compares once. | Plan decision 3 |
| An exact pad and border | The pad is a part of the image that the normalization takes. One limit for the whole result is simpler. The pad value `10,128,240` gave the same max as the default pad. | Part 5; plan decision 4 |
| A list of excluded methods or filters in the spec (for example `area`, or `nearest` with `affine_crop`) | The limit applies to each host implementation. The choice of the CPU path is a property of the package, so it is implementer guidance (part 6). | Plan decision 5 |
| The rule in each section `pre.resize.<method>` | Four copies of one rule. A rule has one place, and the other sections link to it. `pre.resize.affine_crop` has an owner, so a new proposal by this contributor cannot change it. | Heading "Section owner" of `specs/model-sidecar/model-addition-workflow/hand-over.md`; `intake_bundle.py list` at the commit of the header |
| The rule in `common.input` | `common.input` defines the host frame, not the filter. It has an owner, so a new proposal by this contributor cannot change it. | Same as above |
| A sidecar field, for example `input.resize.tolerance` | The limit is a property of the host, not of the model. Each sidecar would need a value. | none |
| The limit after the normalization (on the model input) | The effect of 1 step then depends on `mean` and `std` and on `input.dtype`. The limit is before the normalization. | Plan decision 2 |
| A limit on the mean or on a percentile, in addition to the maximum | The maximum is enough for the measured paths. The share of the values over 0.5 is at most 2.61% (`stretch` `uint8` `linear`). | Part 5 |
| A pixel case with `compare.atol` for `uint8` | `agrees` of `tools/vector_form.py` makes two integers match exactly. That file stays unchanged. The cases test the check of the limit. | Plan decision 8 |
| Include the decode of an encoded image in the limit | The spec starts at the host frame. A GPU decoder can differ from the CPU decoder. That difference is not a part of the resize step. | Paragraph "Host frame" of `common.input`; plan decision 6 |

The spec defect of `cv2.warpAffine` with `cv2.INTER_AREA` (it runs as `cv2.INTER_LINEAR`, OpenCV
4.13.0; heading "Spec defects" of `specs/model-sidecar/decisions/open-work.md`) does not change. The
reference result stays the output of the call.

## Before you stop

- [x] All eight parts are filled in, or say `none` with a reason.
- [x] The intake names the bundle ID of this proposal. n/a: no model intake. The change does not
      come from an intake row.
- [x] The header gives the dependencies, or `none`.
- [x] The header names each `proposed` skellytracker decision entry that covers the same property, or
      `none`. This proposal builds on such an entry. It does not compete with it. J1HK is the entry
      of version 1 of this bundle.
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
      The ONNX and OpenCV lines of part 1 are permalinks on the default branch. The evidence scripts
      are in the repository of this contributor: part 5 gives the full SHA, the branch and the
      paths. Their permalink is missing until the branch is pushed.
- [x] No file in skellytracker changed, except the version folder that `pack` wrote in `intakes/`.
      `pack` wrote version 1. For version 2, `pack` writes only the folder `v2/` of this bundle.
