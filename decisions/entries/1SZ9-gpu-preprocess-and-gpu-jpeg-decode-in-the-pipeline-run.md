# 1SZ9 — The GPU preprocess and the GPU JPEG decode in the pipeline run, measured end to end

**Status:** evidence; used by [W4NW](W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md), 2026-11-23 (PR: pending). It was `evidence` from 2026-11-19 (measurement of 2026-11-18, step S8 of the native JPEG input).

## Decision

The numbers are medians of the wall time of one call with 3 cameras, unless a line says otherwise.
"CPU path" is array input with the CPU preprocess. "GPU path" is JPEG input with the GPU decode and
the GPU preprocess ([ADR-W4NW](W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md);
[ADR-88ZB](88ZB-gpu-jpeg-decoder-component-of-the-ep-catalog.md)).

1. **Detector call.** With the built-in config, a call runs the detector and never the keypoint
   model, because the frames hold no person. CPU path against GPU path: `cuda` 35.34 to 22.49 ms
   (-36 %) at 1280x720 and 38.15 to 24.90 ms (-35 %) at 1920x1080; `trt-rtx` 27.27 to 12.10 ms
   (-56 %) and 28.67 to 13.32 ms (-54 %).
2. **Detector preprocess.** The span `person.preprocess` in the same order: `cuda` 12.71 to 1.60 ms
   and 13.67 to 2.64 ms; `trt-rtx` 12.64 to 0.50 ms and 12.76 to 0.61 ms. JPEG input adds the span
   `frame.decode` of 2.19 to 2.33 ms for 3 frames.
3. **Keypoint-only call.** A config variant with a detector score floor runs the keypoint model at
   each call. On `cuda` at 1920x1080, the call took 9.48 ms on the CPU path and 13.54 ms on the GPU
   path (+43 %). The span `wholebody.preprocess` was 2.04 ms on the CPU and 3.79 ms with the
   `affine_crop` graph (array input), and `frame.upload` added 1.58 ms. At 1280x720 the medians
   were 9.62 and 11.13 ms (+16 %). The same GPU-path configuration gave 12.75 and 13.55 ms in the two
   runs without the option of [ADR-BP5Y](BP5Y-gpu-huffman-decode-threshold.md). The +16 % is thus
   inside the variation between runs, and it is not a finding. On `trt-rtx` the call was about
   equal: 6.25 to 6.71 ms at 1280x720 and 6.03 to 5.79 ms at 1920x1080. Against JPEG input with the
   CPU decode and the CPU preprocess (1280x720 only), the GPU path took 19.19 to 11.13 ms on `cuda`
   and 14.90 to 6.71 ms on `trt-rtx`.
4. **Memory and start.** Process GPU memory at the end, detector call, 1280x720: `cuda` 549 MiB on
   the CPU path and 773 MiB on the GPU path; `trt-rtx` 367 and 421 MiB. The first call: `cuda` 47.9
   and 99.2 ms; `trt-rtx` 39.8 and 138.2 ms. With an empty TensorRT RTX cache, the start took 7.72 s
   and the first call 488.1 ms. With a warm cache, they took 2.50 s and 256.0 ms.
5. **Keypoint agreement.** These frames cannot show it: they hold no person, and keypoints on such
   content move far for a small change of the input. With a detector call at each call, keypoints
   with a score above 0.4 moved by at most 2.8 px (array input with the GPU preprocess) and 3.5 to
   4.9 px (GPU path) at 1280x720. [ADR-FBV5](FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md)
   measures the agreement on a recording with people.
6. **Exit hang.** 1 of the 95 processes of the main plan (`cuda`, array input with the GPU
   preprocess, 1920x1080, 6 cameras) saved its results and then did not end. It ran into the timeout
   of 1200 s. [ADR-C6A5](C6A5-exit-hang-of-the-cuda-ep-plugin.md) gives the study of this hang.

## Evidence

- Conditions: Windows 11, one RTX 3070, a desktop CPU with 28 logical cores, Python 3.13.18,
  ONNX Runtime 1.31.1, `cuda-cu13` 0.3.0, `trt-rtx-cu13` 0.5.0, nvImageCodec 0.10.0.9, OpenCV
  5.0.0.93. The built-in pipeline `yolox-rtmw-wholebody` (`yolox-person` 0.1.0 and
  `rtmw-wholebody133` 0.4.0, size `m`, fp16). Real camera JPEG frames at 1280x720 and 1920x1080,
  still frames in a cycle, 3 and 6 cameras. The script read the frames in place, and the repository
  does not hold them. 30 warm-up calls and 300 measured calls in one process for each
  configuration, one process for each configuration, 95 processes, one at a time after a check for
  an idle GPU.
- The numbers come from ONNX Runtime 1.31.1 and `cuda-cu13` 0.3.0, before the move to 1.30.0 and
  0.2.0. A repeat on the pinned versions is open work.
- Not established: a spread (one run for each configuration), another GPU, frames with people, and
  the keypoint preprocess with several boxes for each frame.
- The scripts are in [`1sz9_pipeline_measure/`](../scripts/1sz9_pipeline_measure/): `measure.py`
  (one configuration), `driver.py` (the plan, with the timeout of 1200 s), `analyze.py` and
  `extra.py` (the tables), `inspect_frames.py` and `probe_people.py` (the frame check), the plans
  `plan_main.txt` and `plan_smoke.txt`. `results.md` holds all tables, also the cadence with a
  detector call at each call (P1d) and the equality tables. `driver_plan_main.txt` holds the exit of
  each process. Not kept: the JSON and `.npz` output of each run, because it holds keypoint arrays
  from camera frames.

## Open work

See [open-work.md](../open-work.md).
