# J1HK — Spec change: resize-pixel-tolerance

**Status:** accepted, 2026-11-17 (user; PR: pending).

## Decision

The user accepted the proposal on 2026-11-17. The record is
[`proposal.md`](../../proposals/resize-pixel-tolerance/proposal.md)
(proposal-resize-pixel-tolerance@skellytracker@v2).

- Section: [`pre.resize.interpolation`](../../pre/interpolation.md).
- Change: a new heading "Resize limit" under "Behaviour". Each implementation of the resize step
  must agree with the output of the OpenCV call of the method, before the normalization. The limit
  applies to each value of the whole result, also the pad and the border. With
  `compute_dtype: uint8`, each value is an integer from 0 to 255 and differs by at most 1. With
  `compute_dtype: float32`, each value is finite. The check converts both results to float64 and
  compares each difference with `0.05` on the 0-255 scale. The geometry does not change. The decode
  to the host frame is not a part of the spec. The reference module gets `resize_limit`,
  `resize_difference` and `check_resize`, with 13 new vector cases. No field and no rule changes.
- Target spec version: `2.0.0`.
- Models: each model that resizes. Part 7 gives no sidecar change for `yolox-person` and
  `rtmw-wholebody133`.
- Supersedes: none.
- Related: none. The contributor is skellytracker. The source is the GPU preprocess graph of the
  package for the EPs `cuda` and `trt-rtx`.
- The user confirmed these plan decisions on 2026-11-17:
  - The package gets a second implementation of the resize step as ONNX nodes for the NVIDIA
    execution providers. The CPU code stays the normative reference.
  - The limit is 1 `uint8` step with `compute_dtype: uint8` and `0.05` with `float32`, on the
    0-255 scale, before the normalization.
  - The spec gets no list of excluded methods or filters. The package uses the GPU graph only where
    the graph meets the limit. `interpolation: area`, and `nearest` with `affine_crop`, run on the
    CPU reference path with one warning when the session opens.
  - The decode of an encoded image to the host frame is not a part of the spec.
- The user also decided these items at the acceptance on 2026-11-17:
  - The final outputs of the models on the graph output stay a control with no gate. Step 4
    ("Expect 0") of [Parity](../../model-addition-workflow/parity.md#parity) does not change.
  - Each section `pre.resize.<method>` that resizes (`letterbox`, `stretch`, `fit`, `affine_crop`)
    gets one link to "Resize limit". The rule stays in one place.
  - `tools/vector_form.py` does not change. Its integer match goes on the spec-defect list of the
    spec [open-work.md](../open-work.md#spec-defects).
  - The item "Cost of the detector preprocess" of the root
    [open-work.md](../../../../decisions/open-work.md) gets one sentence for a second
    implementation on the GPU.

## Reason

The section names one OpenCV call for each method. Another library "must reproduce" it, with no
limit, so a host must give the OpenCV output bit for bit. The GPU graph cannot do this for each
method and filter. The ONNX `Round` node rounds a `.5` tie half to even, and the `uint8` filters of
OpenCV round half up: 6.6% of the `letterbox` values differed by 1 step at 720x1280. With
`Floor(x + 0.5)`, the difference is 0. OpenCV computes some weights and source positions in fixed
point or in float32, so `stretch`, `affine_crop` and `cubic` still differ by 1 step on a small share
of the values. Part 1 cites the OpenCV 5.0.0 and ONNX source lines.

## Evidence

Parity: the gates G1 (`uint8`: 1 step) and G2 (`float32`: 0.05, in float64) are constants of the
script, set before the run. 42 configurations on each of `cuda` and `trt-rtx`: the four methods,
both compute dtypes, `linear`, `cubic` and `nearest`, and a pad value `10,128,240`. 38 pass on each
EP. The 4 `nearest` configurations of `affine_crop` fail (max 41 and 14 steps), so the package keeps
the CPU path there. Each `uint8` max is 0 or 1. Each `float32` max is at most 0.0333. The graph
runs against the CPU path on the same decoded pixels, on 148 variants of 37 frames. G4 (a control):
the `yolox-person` boxes move by at most 6.5 px (`stretch`), and the `rtmw-wholebody133` keypoints by
at most 4.46 px. The scripts are
[`gpu_preprocess_graphs.py`](../scripts/gpu_preprocess_graphs.py),
[`gpu_preprocess_parity.py`](../scripts/gpu_preprocess_parity.py) and
[`gpu_preprocess_race.py`](../scripts/gpu_preprocess_race.py), from the commit "Add the fit and
stretch graphs and the gates to the evidence scripts of the GPU preprocess path" (branch
`dom/native-jpeg`, PR: none yet). Versions: onnxruntime 1.31.1, OpenCV 5.0.0.93, one RTX 3070. The
vector cases are `unverified`: the package has no check of the limit.

## Open work

See [open-work.md](../open-work.md).

## Notes at acceptance

- Not in the graphs: `area` and the normalizations other than `none` and `imagenet`. The
  normalization is outside the limit.
- The evidence commits have no permalink, because the branch is not pushed. They are secondary
  sources until then.
- `nearest` with `fit` is exact only at the 1/2 and 1/3 scales of the sample.
- The `trt-rtx` pack is outside the ONNX Runtime range that NVIDIA tested.
- One run of the race script hung at the process exit after it printed all results. One rerun did
  not hang.
- No session opened the ONNX and OpenCV permalinks of part 1.
- The `spec_commit` of version 2 is on `dom/sidecar-implementation`, not on `dom/native-jpeg`. The
  landing checked that the section files of `pre/` are the same on both.
- The reference module reads only `collections.abc`, `typing`, `cv2` and `numpy`. The safety review
  found no file, network, process, environment or dynamic-code access.
