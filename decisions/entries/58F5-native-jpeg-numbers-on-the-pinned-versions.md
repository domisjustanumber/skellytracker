# 58F5 — The native JPEG numbers repeated on ONNX Runtime 1.30.0 and `cuda-cu13` 0.2.0

**Status:** evidence, 2026-11-21 (measurement of 2026-11-21; PR: pending).

## Decision

The run repeats the cases of [ADR-1SZ9](1SZ9-gpu-preprocess-and-gpu-jpeg-decode-in-the-pipeline-run.md),
[ADR-BP5Y](BP5Y-gpu-huffman-decode-threshold.md),
[ADR-FBV5](FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md) and
[ADR-S1TG](../../specs/pipeline/decisions/entries/S1TG-cpu-jpeg-decode-threads.md). A value is the
median in ms of 3 process values, with their range. The paths are as in ADR-1SZ9.

1. **Pipeline call.** The span is `person.preprocess` (detector call) or `wholebody.preprocess`
   (keypoint-only call). ADR-1SZ9 is in parentheses.

   | EP | frames | call | `wall`, CPU → GPU path | change | span, CPU → GPU path |
   |---|---|---|---|---|---|
   | `cuda` | 1280x720 x3 | detector | 35.71 (35.66–36.27) → 21.31 (21.30–21.47) | -40 % (-36 %) | 13.32 (13.23–13.65) → 1.60 (1.60–1.62) |
   | `cuda` | 1280x720 x3 | keypoint | 9.09 (8.78–9.19) → 10.42 (10.23–10.67) | +15 % (+16 %) | 1.71 (1.66–1.74) → 2.02 (2.00–2.07) |
   | `cuda` | 1920x1080 x3 | detector | 37.40 (36.91–37.40) → 24.29 (24.13–24.49) | -35 % (-35 %) | 13.72 (13.48–13.83) → 2.62 (2.58–2.62) |
   | `cuda` | 1920x1080 x3 | keypoint | 9.21 (9.07–9.34) → 13.24 (13.03–13.24) | +44 % (+43 %) | 1.77 (1.76–1.79) → 3.82 (3.78–3.83) |
   | `cuda` | 1920x1080 x6 | detector | 71.50 (71.15–72.14) → 44.64 (44.52–45.00) | -38 % | 27.50 (27.18–27.59) → 5.03 (5.02–5.07) |
   | `cuda` | 1920x1080 x6 | keypoint | 14.59 (14.56–14.63) → 21.39 (21.31–21.41) | +47 % | 3.60 (3.55–3.63) → 7.36 (7.34–7.37) |
   | `trt-rtx` | 1280x720 x3 | detector | 29.09 (28.60–29.70) → 11.40 (11.23–11.41) | -61 % (-56 %) | 14.01 (13.43–14.02) → 0.53 (0.49–0.54) |
   | `trt-rtx` | 1280x720 x3 | keypoint | 5.73 (5.73–5.94) → 5.25 (5.10–5.31) | -8 % | 1.64 (1.64–1.68) → 0.36 (0.35–0.40) |
   | `trt-rtx` | 1920x1080 x3 | detector | 31.19 (30.39–31.19) → 13.31 (13.30–13.37) | -57 % (-54 %) | 13.84 (13.70–14.21) → 0.62 (0.62–0.62) |
   | `trt-rtx` | 1920x1080 x3 | keypoint | 5.71 (5.65–5.96) → 5.94 (5.74–6.00) | +4 % | 1.65 (1.63–1.73) → 0.43 (0.37–0.44) |
   | `trt-rtx` | 1920x1080 x6 | detector | 63.38 (61.79–65.33) → 23.65 (23.59–23.92) | -63 % | 28.26 (27.50–28.36) → 1.05 (1.04–1.10) |
   | `trt-rtx` | 1920x1080 x6 | keypoint | 10.66 (10.54–10.80) → 10.29 (9.97–10.42) | -3 % | 3.37 (3.30–3.40) → 0.59 (0.53–0.63) |

2. **Keypoint-only call on `cuda`.** On `cuda`, a call with no detector run is slower on the GPU
   path at each size. The ranges do not overlap. On `trt-rtx`: -8 % to +4 %.
3. **Decode.** `frame.decode` on the GPU path: 1.30 to 1.37 ms at 1280x720 x3, 1.85 to 2.27 ms at
   1920x1080 x3, 2.83 to 3.08 ms at x6.
4. **Huffman threshold.** 1280x720 x3, keypoint-only call, `frame.decode` with 1000000 against
   500000: `cuda` 2.35 (2.34–2.37) to 1.33 (1.31–1.37), `trt-rtx` 2.31 (2.31–2.31) to 1.33
   (1.29–1.36). Pixels and outputs were equal.
5. **CPU decode threads.** Wall time of one batch.

   | frames | size | in a row | thread pool | pool + upload | nvJPEG | nvJPEG p95, max |
   |---|---|---|---|---|---|---|
   | 3 | 1280 x 720 | 8.50 (8.45–8.51) | 3.64 (3.61–3.69) | 5.38 (5.35–5.49) | 2.44 (2.43–2.89) | 5.5, 9.6 |
   | 6 | 1280 x 720 | 16.91 (16.70–17.21) | 4.28 (4.24–4.33) | 7.62 (7.59–7.63) | 2.69 (2.68–2.72) | 5.4, 10.8 |
   | 3 | 1920 x 1080 | 15.66 (15.64–15.85) | 6.62 (6.61–6.66) | 10.03 (10.02–10.11) | 2.22 (2.19–2.24) | 7.9, 20.1 |
   | 6 | 1920 x 1080 | 31.68 (31.67–32.13) | 7.98 (7.88–8.08) | 14.16 (12.63–14.28) | 3.11 (3.09–3.20) | 11.8, 26.9 |

6. **Agreement.** 1108 frames, quality 90, two runs equal bit for bit. Median / p99 / max px:
   GPU against CPU path `cuda` 1.22 / 7.83 / 316.0, `trt-rtx` 1.29 / 8.21 / 325.9; yardstick
   `cuda` against `cpu` 1.18 / 8.05 / 325.7, `cuda` against `trt-rtx` 1.30 / 8.22 / 311.5.
7. **Counts.** `pytest -m gpu`: 239 passed, 6 skipped. `run_jpeg_certification`, `cuda` and
   `trt-rtx`: 47 pass, 0 fail, 14 not run, 5 record-only, of 66 checks.
8. **Against the old entries.** The repeat confirms the direction of each change in items 1 and 2
   of ADR-1SZ9 and of the `cuda` changes in its item 3, item 6 of ADR-BP5Y, items 1 and 3
   of ADR-FBV5 and the order of the ADR-S1TG table. It does not confirm (old, new):
   - ADR-1SZ9 item 3: +16 % on `cuda` at 1280x720 is "inside the variation between runs". The
     repeat gives +15 %, with 8.78–9.19 against 10.23–10.67 ms.
   - ADR-1SZ9 item 3, `trt-rtx`: 6.25 to 6.71 and 6.03 to 5.79 ms; now 5.73 to 5.25 and 5.71 to
     5.94 ms. The direction changes.
   - ADR-1SZ9 item 3, `cuda` CPU `wholebody.preprocess` at 1920x1080: 2.04 and 1.77 ms.
   - ADR-1SZ9 item 1, CPU path on `trt-rtx`: 27.27 and 29.09 ms, 28.67 and 31.19 ms.
   - ADR-BP5Y item 2: 3.02 ms on `cuda`; now 2.34–2.37 ms.
   - ADR-FBV5 item 2: p99 7.55 and 7.92; now 7.83 and 8.21. Item 7: yardstick max 281–323; now 325.7.
   - ADR-S1TG: pool + upload 3 x 1280 x 720, 6.4 and 5.38. nvJPEG max 1920 x 1080, 11.5 and 20.1,
     15.7 and 26.9. nvJPEG p95 6 x 1920 x 1080, 8.0 and 11.8.

## Evidence

- 2026-11-21, 00:02 to 00:50, package code at a2a6f20e. Windows 11, one RTX 3070.
  Python 3.13.18, ONNX Runtime 1.30.0 (`onnxruntime-windowsml`), `cuda-cu13` 0.2.0,
  `trt-rtx-cu13` 0.5.0, `gpu-jpeg-cu13` (nvImageCodec 0.10.0), `opencv-contrib-python` 5.1.0.95,
  numpy 2.5.5, as each process printed them.
- A process value is the median of 300 calls after 30 warm-up calls (decode threads: 5 rounds of
  200 batches). Camera JPEG frames, read in place. No other session ran a test or a GPU job.
- The scripts are adapted copies of the scripts of the four entries, with a wrapper. They are
  scratch scripts (not in git). Sources: [`1sz9_pipeline_measure/`](../scripts/1sz9_pipeline_measure/),
  [`fbv5_sample_data_agreement/`](../scripts/fbv5_sample_data_agreement/),
  [`s1tg_decode_threads/`](../../specs/pipeline/decisions/scripts/s1tg_decode_threads/).

## Open work

See [open-work.md](../open-work.md).
