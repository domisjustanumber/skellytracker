# J1HK — Spec change: resize-pixel-tolerance

**Status:** proposed, 2026-11-17 (proposal-resize-pixel-tolerance@skellytracker@v1); recorded again 2026-11-17 (proposal-resize-pixel-tolerance@skellytracker@v2).

## Decision

**Proposed, not decided.** The record is
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
- While this entry is `proposed`, the contributor `skellytracker` owns `pre.resize.interpolation`
  ([Section owner](../../model-addition-workflow/hand-over.md#section-owner)).

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

## Before acceptance

- [ ] Not in the graphs: `area` and the normalizations other than `none` and `imagenet`. The
  normalization is outside the limit. (changed 2026-11-17)
- [x] The `float32` gate. Version 2 ran with the gate 0.05 set first. The gate before the first run
  was 1.0.
- [ ] The evidence commits have no permalink, because the branch is not pushed. They are secondary
  sources until then. (changed 2026-11-17)
- [ ] `tools/vector_form.py` stays unchanged (user decision 2026-11-17). Its integer match goes on
  the spec-defect list of the spec `open-work.md` at the landing (part 2.1). (changed 2026-11-17)
- [x] Primary evidence for the causes. Version 2 cites pinned lines. The `cv2.resize` cause stays
  probable, because nobody checked the IPP path. The two `imgwarp.cpp` lines explain only `cubic`.
- [x] The integer rule for `uint8`. The user confirmed it on 2026-11-17.
- [x] The pad and the border. The user decided on 2026-11-17 that the limit covers the whole result.
- [x] The precision of the `float32` comparison. The user decided float64. Version 2 states it.
- [x] The plan decisions of part 1. The user decided each one on 2026-11-17.
- [ ] The two `open-work.md` edits of part 2.1 are non-spec edits. They go in a non-spec commit.
  (changed 2026-11-17)
- [x] The exporter hosts. Part 7 now gives only cited facts.
- [ ] G4 is a control with no gate. Decide if the box and keypoint moves need a gate.
  (changed 2026-11-17)
- [ ] [Parity](../../model-addition-workflow/parity.md#parity) step 4 says "Expect 0". Decide if it
  needs a note for a second implementation.
- [ ] The sections `pre.resize.<method>` get no link to "Resize limit". Decide if the landing adds one.
- [x] The two stale texts. Version 2 corrects them.
- [ ] The contributor and the session are the same project. The user decides as for each proposal.
- [ ] `nearest` with `fit` is exact only at the 1/2 and 1/3 scales of the sample. (new 2026-11-17)
- [ ] The `trt-rtx` pack is outside the ONNX Runtime range that NVIDIA tested. (new 2026-11-17)
- [ ] One run of the race script hung at the process exit after it printed all results. One rerun
  did not hang. (new 2026-11-17)
- [ ] The session did not open the ONNX and OpenCV permalinks of part 1. (new 2026-11-17)
- [ ] The `spec_commit` of version 2 is on `dom/sidecar-implementation`, not on `dom/native-jpeg`.
  The text of the section is the same on both. (new 2026-11-17)
