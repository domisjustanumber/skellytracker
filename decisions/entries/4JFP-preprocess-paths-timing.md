# 4JFP — Timing of each preprocess path, for each resize method, on a quiet system

**Status:** evidence; used by [S4MT](S4MT-two-preprocess-paths.md), 2026-11-23 (PR: pending). It was `evidence` from 2026-11-23 (measurement of 2026-11-23).

## Decision

The question: can the package have one preprocess method? The run timed the CPU code, a scratch CPU
form with a reused output batch, and the preprocess graph on each EP, for each resize method. All
times are median wall time in ms for one call. "CPU code" is `preprocess_image` for each frame and
then `np.stack`, at the package state of the commit before the reused batch.

1. **The preprocess alone, 3 cameras of 1280x720.** The GPU columns include the upload of the
   frames, and their output stays in GPU memory. The CPU columns leave the output in host memory.

   | Resize method | CPU code | Reused batch | Graph, CPU EP | Graph, `cuda` | Graph, `trt-rtx` | Graph, `directml` RTX 3070 | Graph, `directml` UHD 770 |
   |---|---|---|---|---|---|---|---|
   | `letterbox` (`yolox-person`) | 12.24 | 1.01 | 7.04 | 2.24 | 1.10 | 1.89 | 21.50 |
   | `affine_crop` (`rtmw-wholebody133`) | 1.97 | 0.53 | 9.36 | 2.74 | 1.04 | 2.09 | 25.73 |
   | `stretch` (test sidecar) | 21.90 | 2.48 | 7.51 | 2.54 | 1.10 | 2.15 | 25.86 |
   | `fit` (test sidecar) | 9.83 | 1.80 | 31.67 | 2.57 | 0.97 | 2.21 | 26.65 |
   | `none` (test sidecar) | 47.61 | 6.41 | 8.37 | 2.68 | 1.09 | 2.15 | 29.87 |

2. **The reused batch is equal.** Its output has a max abs diff of 0.0 against the CPU code in each
   of 53 configurations. Each graph output is inside `RESIZE_LIMITS`.
3. **Six cameras of 1280x720, reused batch / `trt-rtx` / `cuda`.** `letterbox` 2.11 / 2.21 / 4.45.
   `affine_crop` 1.04 / 1.93 / 5.33. `stretch` 5.78 / 2.15 / 4.99. `fit` 3.86 / 1.91 / 5.11. `none`
   13.06 / 2.19 / 5.19.
4. **Preprocess and model, 3 cameras, fp32 models with a fixed batch of 3.**

   | Model, EP | CPU code | Reused batch, then upload | Graph | Graph and model in one session |
   |---|---|---|---|---|
   | `yolox-person` m, `cuda` | 42.09 | 29.92 | 29.97 | 29.42 |
   | `yolox-person` m, `trt-rtx` | 34.43 | 22.76 | 21.50 | 21.13 |
   | `rtmw-wholebody133` m, `cuda` | 9.55 | 8.51 | 10.38 | 9.62 |
   | `rtmw-wholebody133` m, `trt-rtx` | 7.29 | 5.93 | 6.03 | 5.66 |

5. **The built-in pipeline, running mode `live`, preprocess place `auto` against `cpu`.** The
   detector ran on the first call only. Values for 1 / 3 / 6 cameras.

   | EP, input | `auto` | `cpu` |
   |---|---|---|
   | `cuda`, arrays | 6.62 / 10.00 / 16.47 | 6.35 / 9.40 / 15.05 |
   | `cuda`, JPEG | 7.45 / 10.72 / 17.00 | 10.44 / 14.31 / 21.05 |
   | `trt-rtx`, arrays | 2.45 / 5.62 / 9.56 | 4.43 / 7.44 / 12.45 |
   | `trt-rtx`, JPEG | 5.90 / 6.33 / 10.59 | 9.38 / 15.46 / 19.26 |
   | `cpu`, arrays | not run | 16.88 / 38.79 / 67.69 |
   | `cpu`, JPEG | not run | 20.41 / 42.34 / 72.42 |

   - With JPEG input, `frame.decode` took 0.98 to 2.33 ms with `auto` and 2.93 to 4.04 ms with `cpu`.
   - `trt-rtx`, JPEG, 3 cameras, `cpu`: the span `wholebody.inference` took 7.56 ms. With 6 cameras
     it took 6.88 ms. The value at 3 cameras is possibly an outlier. No run repeated it.
   - With the detector on each call, 3 cameras, arrays: `cuda` 29.61 against 42.26, `trt-rtx` 15.28
     against 32.99.
   - `directml` on the RTX 3070, arrays, place `gpu` against `cpu`: 4.10 / 7.18 / 13.19 against
     3.46 / 7.18 / 13.80.
6. **Changed graphs.** A graph with fewer steps was 8 to 37 % faster on `cuda` and 10 to 50 % faster
   on `directml`. On `trt-rtx` it gave no gain. A graph with a `uint8` resize did not build on
   `trt-rtx`, and it was outside the limit on `cuda`.
7. **Cubic interpolation.** The graph took 937.9 ms on the CPU EP. On `directml`, 3 `Resize` nodes
   ran on the CPU EP: 965.7 ms on the RTX 3070. On `cuda` it took 2.25 ms, on `trt-rtx` 1.07 ms, and
   the reused batch 2.63 ms.
8. **The OpenVINO EP on the UHD 770.** A `letterbox` graph call took 5.47 ms with no gap before it.
   With an idle gap of 250 ms before each call, 28 of 30 calls took more than 50 ms, and the median
   was 461.1 ms. With a gap of 500 ms, each of 30 calls did, median 224.2 ms. With a gap of 100 ms or
   less, no call did. In a detector call with the model on the CPU EP, the preprocess part took
   495.3 ms. The cause is not known. This repeats item 6 of
   [ADR-B5Z0](B5Z0-yolox-preprocess-timing-on-an-intel-igpu-system.md) on a quiet system.

## Evidence

- One Windows 11 system: Intel Core i7-14700K, RTX 3070, Intel UHD 770. ONNX Runtime 1.30.0,
  the EP packs of the EP catalog (the run did not print their versions), OpenCV 5.1.0, numpy 2.5.5, the OpenVINO EP package of the
  Windows ML catalog 2.1080.97.0.
- 2026-11-23, 53 minutes. The CPU load of the system was 7.9 to 13.3 % at each of seven samples.
  Three other sessions on the system stated that they ran no test, no camera and no GPU run in that
  time.
- Items 1 to 3 and 6: first call, 10 warm-up calls, then 3 runs of 15 to 100 calls. Items 4 and 5:
  3 runs of 20 calls, and 120 calls after 20 warm-up calls.
- Each GPU session came from `eps.build_session()` with an isolated EP store. The OpenVINO sessions
  were built by hand.
- Limits: the frames of items 1 to 4 and 6 to 8 are copies of the test frames of the package at a
  new size. The ROIs are fixed boxes. The `stretch`, `fit` and `none` rows use sidecars of the
  tests. The TensorRT RTX cache was empty at the start. The models of item 4 are fp32 with a batch
  of 3, and the pipeline of item 5 uses fp16 models.
- The scripts are scratch scripts (not in git).

## Open work

See [open-work.md](../open-work.md).
