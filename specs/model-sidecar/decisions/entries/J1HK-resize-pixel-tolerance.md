# J1HK — Spec change: resize-pixel-tolerance

**Status:** proposed, 2026-11-17 (proposal-resize-pixel-tolerance@skellytracker@v1).

## Decision

**Proposed, not decided.** The record is
[`proposal.md`](../../proposals/resize-pixel-tolerance/proposal.md)
(proposal-resize-pixel-tolerance@skellytracker@v1).

- Section: [`pre.resize.interpolation`](../../pre/interpolation.md).
- Change: a new heading "Resize limit" under "Behaviour". Each implementation of the resize step
  must agree with the output of the OpenCV call of the method, before the normalization. With
  `compute_dtype: uint8`, each value is an integer from 0 to 255 and differs by at most 1. With
  `compute_dtype: float32`, each value is finite and differs by at most `0.05` on the 0-255 scale.
  The geometry does not change. The decode to the host frame is not a part of the spec. The
  reference module gets `resize_limit`, `resize_difference` and `check_resize`, with 12 new vector
  cases. No field and no rule changes.
- Target spec version: `2.0.0`.
- Models: each model that resizes. Part 7 gives no sidecar change for `yolox-person` and
  `rtmw-wholebody133`.
- Supersedes: none.
- Related: none. The contributor is skellytracker. The source is the GPU preprocess graph of the
  package for the EPs `cuda` and `trt-rtx`.
- While this entry is `proposed`, the contributor `skellytracker` owns `pre.resize.interpolation`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).

## Reason

The section names one OpenCV call for each method. Another library "must reproduce" it, with no
limit, so a host must give the OpenCV output bit for bit. The GPU graph cannot do this for each
method and filter. The ONNX `Round` node rounds a `.5` tie half to even: 6.6% of the `letterbox`
values differed by 1 step at 720x1280. With `Floor(x + 0.5)`, the difference is 0. The
`affine_crop` graph still differs by 1 step on about 0.01% of the values. The cause is inferred:
fixed-point source positions in `cv2.warpAffine`.

## Evidence

Parity: `pass` for gate G1 (1 step of `uint8`): `letterbox` and `affine_crop`, `linear` and
`cubic`, on `cuda` and `trt-rtx`. The graph runs against the CPU path on the same decoded pixels,
on 148 variants of 37 frames. `float32` `affine_crop`: max 0.035. `nearest` with `affine_crop`:
`fail` (max 36 and 11 steps), so the package keeps the CPU path there. The `yolox-person` boxes and
scores are equal. The `rtmw-wholebody133` keypoints move by at most 4.46 px. The scripts are
[`gpu_preprocess_graphs.py`](../scripts/gpu_preprocess_graphs.py),
[`gpu_preprocess_parity.py`](../scripts/gpu_preprocess_parity.py) and
[`gpu_preprocess_race.py`](../scripts/gpu_preprocess_race.py), from the commit "Add the evidence
scripts of the GPU preprocess path against the CPU reference" (branch `dom/native-jpeg`, PR: none
yet). Versions: onnxruntime 1.31.1, OpenCV 5.0.0.93, one RTX 3070. The vector cases are
`unverified`: the package has no check of the limit.

## Open work

See [open-work.md](../open-work.md).

## Before acceptance

- `fit` and `stretch` are not measured: no graph exists for them. Also not measured: `area`, a
  `pad_value` array, an `affine_crop` pad value other than 0, and the normalizations other than
  `none` and `imagenet`.
- `to run`: the `float32` limit 0.05 was set after the run. The gate before the run was 1.0. A run
  with the gate 0.05 set before the run is to do
  ([Parity](../../model-addition-workflow/parity.md#parity) step 1). Confirm that the gate 1.0
  existed before the run.
- The evidence commit has no permalink, because the branch is not pushed. It is a secondary source
  until then.
- Workflow finding: `agrees` of `tools/vector_form.py` makes two integers match exactly, also with
  `compare.atol`. Thus no pixel case can state the `uint8` limit. Part 4 of the template says that a
  pixel case states its tolerance in `compare`.
- Missing primary evidence for the two causes: the ONNX `Round` operator and the fixed-point
  positions of `cv2.warpAffine` in OpenCV, each at a pinned SHA. The limit does not need them.
- The integer rule for `uint8` (an integer from 0 to 255) goes beyond the decided wording "at most
  1 `uint8` step". The user must confirm or refuse it.
- Open question: does the limit cover the pad of `letterbox` and the border of the warp, or must
  they be exact?
- Open question: the precision of the `float32` comparison. 0.05 has no exact float32 value. The
  reference module compares in float64, so a float32 result that is 0.05 from the reference value
  can be over the limit (for example `float32(0.05)` against 0).
- Plan decisions of part 1 to confirm or refuse: a second resize implementation as ONNX nodes for
  the NVIDIA EPs, with the CPU code as the reference; the `uint8` limit of 1 step before the
  normalization; the `float32` limit 0.05; no list of excluded methods or filters in the spec; the
  decode out of scope; one sentence for "Cost of the detector preprocess" of the root
  `open-work.md`.
- That `open-work.md` edit is a non-spec edit. It goes in a non-spec commit.
- Part 7 says that the CPU hosts of the exporters differ by 0. The Implementer guidance of the
  section gives up to 2.19e-2 for the Roboflow-Exporter float32 resize, and a PIL host for
  Qualcomm-Exporter. No example of these hosts is landed.
- Part 5 gives the values for each size and chroma, not for each image. G4 (final outputs) is a
  control. Decide if the 4.46 px keypoint move needs a gate. Confirm the configs of the command.
- [Parity](../../model-addition-workflow/parity.md#parity) step 4 says "Expect 0". Decide if it
  needs a note for a second implementation.
- The sections `pre.resize.<method>` get no link to "Resize limit". Decide if the landing adds one.
- The module docstring "Vector results" says 2 cases and no numeric case. The file will have 16
  cases. The last box of "Before you stop" says that `pack` did not run. Both are stale.
- The contributor and the session are the same project. The user decides as for each proposal.
