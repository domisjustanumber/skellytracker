# BP5Y — The GPU Huffman option of the nvJPEG decoder and the threshold 500000

**Status:** evidence, 2026-11-19 (measurement of 2026-11-18; PR: pending).

## Decision

The option is `nvjpeg_cuda_decoder:hybrid_huffman_threshold`. Above the threshold in pixels, nvJPEG
does the Huffman decode on the GPU. The library default is 1000000. The package uses 500000
([Running](../../specs/pipeline/running.md#implementer-guidance)).

1. **Pipeline.** JPEG input with the GPU decode and the GPU preprocess, 3 cameras at 1280x720, the
   threshold 0 against the default, 2 runs of each. Median of `frame.decode` in ms: `trt-rtx` 2.36
   and 2.40 to 1.38 and 1.41; `cuda` 2.46 and 3.02 to 1.54 and 1.43. The process GPU memory changed by at
   most 6 MiB, and the pipeline outputs were equal bit for bit.
2. **The outlier.** The second `cuda` run without the option had a median of 3.02 ms, a p95 of
   5.02 ms and a maximum of 32.07 ms. The mean of the two medians, 2.74 ms, includes it. The other
   run gave 2.46 ms.
3. **Other sizes.** With 6 cameras at 1280x720: `trt-rtx` 2.73 and 2.63 to 2.50 and 2.34 ms; `cuda`
   3.17 and 2.50 to 2.09 and 2.02 ms. With 3 cameras at 1920x1080 there is no change (`trt-rtx`
   1.88 to 1.87 ms, `cuda` 2.33 to 2.26 ms, means of the medians): the default already does the
   Huffman decode on the GPU at that size.
4. **Decoder alone.** On the `cuda` device, 2 runs of 1000 batches. Mean of the 2 wall medians in
   ms, for the default / 500000 / 0: 320x240 x6 0.55 / 0.55 / 1.20; 640x480 x6 1.10 / 1.10 / 1.45;
   1280x720 x3 2.29 / 1.27 / 1.28; 1280x720 x6 2.50 / 1.80 / 1.78; 1920x1080 x3 2.12 / 2.11 / 2.13.
   The CPU time of a batch of 1280x720 x3 went from 4.6 to 2.6 ms with 500000. The threshold 0 makes
   small frames slower, so the package does not use 0.
5. **Pixels.** The default, 500000 and 0 give identical pixels (maximum absolute difference 0) at
   each size, and for a grayscale JPEG and a progressive JPEG.
6. **The package value.** With 500000 in the package code, the pipeline run of item 1 gave a median
   `frame.decode` of 1.35 ms on `cuda` and 1.32 and 1.30 ms on `trt-rtx`.
7. **Exit text.** With the threshold 0, each `trt-rtx` pipeline process (6 of 6) printed
   `cuDevicePrimaryCtxRelease failed: 4` five times at its exit, with the exit code 0 and no hang.
   The `cuda` pipeline processes with the threshold 0 (6) and all pipeline processes with the
   default (12) did not print it. With 500000 in the package code, 2 `trt-rtx` processes and 1
   `cuda` process did not print it. Each process of the decoder alone printed it five times. Each
   such process opened decoders with the default and with the threshold 0 in one process, so no run
   shows a process with only the default threshold. A reading of the nvImageCodec source, not a
   measurement: the text comes from the teardown order of static objects
   (`src/imgproc/device_guard.h`, since 0.9.0), it is harmless, and its count follows the loaded
   libraries, not the Huffman option.

## Evidence

- Conditions: 2026-11-18, Windows 11, one RTX 3070, ONNX Runtime 1.31.1, `cuda-cu13` 0.3.0,
  `trt-rtx-cu13` 0.5.0, nvImageCodec 0.10.0.9, the built-in pipeline `yolox-rtmw-wholebody` with
  the config variant of item 3 of
  [ADR-1SZ9](1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md). 30 warm-up calls and
  300 measured calls for each pipeline run. Real camera JPEG frames, read in place and not stored.
  The decoder alone makes its 320x240 and 640x480 JPEG images in memory from these frames. One
  batch of the decoder alone is the wall time of one decode, with the wait for the stream. These
  numbers come from 1.31.1 and 0.3.0, before the move to 1.30.0 and 0.2.0. A repeat on the pinned
  versions with at least 3 runs is open work: 2 runs cannot show the spread.
- The scripts are in [`bp5y_huffman_threshold/`](../scripts/bp5y_huffman_threshold/):
  `measure.py`, `driver.py`, `analyze.py`, `decoder_alone.py` and the plans (default against 0);
  `decoder_alone_500k.py`, `exit_check.py` and the `plan_500k*.txt` files (500000). The outputs are
  `tables.md` (default against 0) and `rows_500k.txt` (500000). Not kept: the run logs (they hold
  local paths) and the JSON and `.npz` output of each run.

## Open work

See [open-work.md](../open-work.md).
