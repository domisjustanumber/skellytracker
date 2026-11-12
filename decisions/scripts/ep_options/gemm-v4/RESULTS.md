# CUDA plugin: `enable_gemm_auto_tune` and deterministic compute on rtmw-wholebody133 v4 (opset 17)

Date: 2026-11-12. Measured on one RTX 3070. `models.json` is next to this file. The raw data is not in git:
`results.jsonl` (one line for each child process: 193 jobs), `summary.json` and `results/` (job files,
decoded logs, saved outputs). They hold local paths. The tables below are their summary. The scripts are
in `scripts/` (`run.py`, `child.py`, `make_inputs.py`, `make_tiny.py`, `summarize.py`, `check_models.py`).

## Environment

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3070, 8 GB, CC 8.6 |
| Driver | 610.88 |
| OS | Windows 11, build 10.0.26300 |
| Python | CPython 3.12.13 (uv 0.13.7, own env in `env/`) |
| onnxruntime | 1.31.0 (PyPI) |
| Plugin | onnxruntime-ep-cuda13 0.3.0 (Azure feed `onnxruntime-cuda-13`), EP name `CUDAExecutionProvider` |
| CUDA wheels | nvidia-cublas 13.8.0.4, nvidia-cudnn-cu13 9.27.0.42, nvidia-cuda-nvrtc 13.5.37 |
| Other | numpy 2.5.4, onnx 1.23.2 (model checks only) |

The pins are the `cuda-cu13` row of the ep_device_checks suite. The child adds the NVIDIA wheel DLL folders
to the front of `PATH`, calls `register_execution_provider_library`, picks the device from `get_ep_devices()`
(EP name and vendor 0x10DE), and uses `add_provider_for_devices` and
`session.record_ep_graph_assignment_info=1`. There is one fresh process for each job, and the jobs run
one at a time.

## Models

The files are `rtmw-wholebody133-{m,x-384}_b{1,3}_{fp32,fp16}.onnx` in the OpenMMLab-Exporter export folder.
- The sha256 of all 8 files matches the v4 intake `manifest.yaml`. The v4 intake folder holds no ONNX file.
- `opset_import` is `ai.onnx: 17` for all 8 files.
- I/O is fp32 in the fp16 files too.
- The outputs are `simcc_x` and `simcc_y` (SimCC split ratio 2).
- Each file has 8 MatMul and 0 Gemm.

## Method

- **Input.** There is one fixed random input for each (size, batch). It uses `default_rng(seed).standard_normal`,
  float32, with seeds m b1 1001, m b3 1003, x-384 b1 2001 and x-384 b3 2003. All runs use the same input.
- **Timing.** Each job does 5 warm-up runs, then 30 timed runs of `session.run`. The tables give the median, p95 and min.
- **VRAM.** The VRAM figure is the device-wide NVML peak during the child process, minus the use before the
  child started (the desktop used about 2 GB).
- **Parity.** Each output is compared with the baseline output of the same file. The tables give the max abs
  diff, the max element-wise rel diff and bit identity. The decoded check takes the SimCC argmax for each
  keypoint and counts the argmax flips and the max pixel shift (argmax diff / 2).
- **Assignment.** All jobs had 0 nodes on CPUExecutionProvider: m 394/401 and x-384 512/519 nodes on CUDA
  (fp32/fp16).
- **Run order.** Single passes ran in this order: base, then gemm and det, then base2. The GPU time drifted
  down during the session: base and base2 differ by up to 6% on the m configurations. For this reason, a
  second set ran base, gemm and det interleaved, in rotated order, for 3 rounds. The two noisy m fp16
  configurations got 5 more rounds. Use the interleaved tables for the verdicts.

## 1. Baseline (no provider options)

| Config | median ms | p95 ms | min ms | first run ms | build ms | VRAM MB | CPU nodes |
|---|---|---|---|---|---|---|---|
| m b1 fp32 | 5.85 | 7.72 | 5.33 | 389 | 265 | 419 | 0 |
| m b1 fp16 | 5.22 | 6.52 | 4.94 | 1345 | 201 | 276 | 0 |
| m b3 fp32 | 7.46 | 8.59 | 7.01 | 368 | 248 | 412 | 0 |
| m b3 fp16 | 5.67 | 7.09 | 5.35 | 766 | 203 | 284 | 0 |
| x-384 b1 fp32 | 14.87 | 15.34 | 13.97 | 397 | 407 | 661 | 0 |
| x-384 b1 fp16 | 10.49 | 11.67 | 9.74 | 935 | 284 | 422 | 0 |
| x-384 b3 fp32 | 29.40 | 30.24 | 28.23 | 389 | 394 | 673 | 0 |
| x-384 b3 fp16 | 17.48 | 18.29 | 16.58 | 906 | 341 | 404 | 0 |

This was the first pass of the session, so it is the slowest one. The interleaved baseline is in the
section [Interleaved comparison](#interleaved-comparison-the-numbers-for-the-verdicts): x-384 fp16 b1 9.87 ms
and b3 16.34 ms, x-384 fp32 b1 13.64 ms and b3 27.85 ms. The earlier harness README gives 10.3, 17.2, 14.2
and 28.8 ms for the older files. The new opset-17 files are 3-5% faster. These runs were done in a different
session, so this difference is not a controlled comparison.

## 2. `enable_gemm_auto_tune=1` (provider option)

| Config | median ms | p95 ms | min ms | first run ms | VRAM MB | CPU nodes | max abs vs base | max rel vs base | flips | max px |
|---|---|---|---|---|---|---|---|---|---|---|
| m b1 fp32 | 5.55 | 6.92 | 5.26 | 378 | 417 | 0 | 0 | 0 | 0/133 | 0 |
| m b1 fp16 | 5.02 | 5.87 | 4.72 | 810 | 280 | 0 | 0 | 0 | 0/133 | 0 |
| m b3 fp32 | 7.18 | 8.12 | 7.02 | 351 | 403 | 0 | 0 | 0 | 0/399 | 0 |
| m b3 fp16 | 5.34 | 6.07 | 5.19 | 723 | 302 | 0 | 0 | 0 | 0/399 | 0 |
| x-384 b1 fp32 | 13.82 | 14.50 | 13.49 | 374 | 663 | 0 | 0 | 0 | 0/133 | 0 |
| x-384 b1 fp16 | 9.85 | 10.93 | 9.31 | 863 | 404 | 0 | 0 | 0 | 0/133 | 0 |
| x-384 b3 fp32 | 27.65 | 28.93 | 27.50 | 383 | 665 | 0 | 0 | 0 | 0/399 | 0 |
| x-384 b3 fp16 | 16.21 | 17.41 | 16.04 | 861 | 411 | 0 | 0 | 0 | 0/399 | 0 |

All outputs are bit-identical to the baseline. The first-run time shows no extra tuning cost.

**Did the plugin read the option?** Yes. The evidence:

- The verbose session log (severity 0) prints `config_options: { ... ep.cuda.device_id: 0  ep.cuda.enable_gemm_auto_tune: 1 }`.
  ORT stores the provider option under the prefix `ep.cuda.`.
- With the value `banana`, the session build fails in the plugin: `gemm_auto_tuner.cc:108
  onnxruntime::cuda::ParseGemmOnOffOption Invalid value 'banana' for ep.cuda.enable_gemm_auto_tune: expected 0 or 1.`
  Three forms give this same plugin error: the provider option `enable_gemm_auto_tune`, the provider option
  `ep.cuda.enable_gemm_auto_tune` and the session config entry `ep.cuda.enable_gemm_auto_tune`. The env var
  `ORT_CUDA_GEMM_AUTO_TUNE=banana` gives the same error, with that env var name in it.
- The MatMul kernel parses the option. A tiny opset-17 model with only Relu accepts `banana`. A MatMul-only
  model ([1,133,256] x [256,512]) rejects it, in fp32 and in fp16.
- The verbose log has no line from the tuner itself: no candidate, timing or pick message. The plugin
  binary names the candidates `cublas`, `small_n_gemv` and `tinygemm2`. For every MatMul in these models and
  in the tiny models, the outputs with the tuner on are bit-identical to the outputs with it off. This
  agrees with the tuner keeping the cuBLAS path for these shapes. This is an inference: no log line shows
  the pick.

## 3. Deterministic compute (`so.use_deterministic_compute = True`, SessionOptions attribute)

The verbose session log shows `use_deterministic_compute:1`, and the attribute reads back `True`.

| Config | median ms | p95 ms | min ms | first run ms | VRAM MB | CPU nodes | max abs vs base | max rel vs base | flips | max px |
|---|---|---|---|---|---|---|---|---|---|---|
| m b1 fp32 | 5.26 | 5.83 | 5.13 | 360 | 404 | 0 | 0 | 0 | 0/133 | 0 |
| m b1 fp16 | 4.51 | 5.09 | 4.40 | 795 | 297 | 0 | 0 | 0 | 0/133 | 0 |
| m b3 fp32 | 7.00 | 7.12 | 6.90 | 351 | 403 | 0 | 0 | 0 | 0/399 | 0 |
| m b3 fp16 | 5.64 | 5.86 | 5.08 | 759 | 310 | 0 | 0 | 0 | 0/399 | 0 |
| x-384 b1 fp32 | 14.35 | 14.97 | 13.57 | 395 | 668 | 0 | 0 | 0 | 0/133 | 0 |
| x-384 b1 fp16 | 10.12 | 10.64 | 9.48 | 912 | 403 | 0 | 0 | 0 | 0/133 | 0 |
| x-384 b3 fp32 | 27.80 | 28.89 | 27.61 | 392 | 666 | 0 | 0 | 0 | 0/399 | 0 |
| x-384 b3 fp16 | 16.33 | 17.42 | 16.01 | 893 | 416 | 0 | 0 | 0 | 0/399 | 0 |

### Session-to-session determinism (fp32 b3, 10 fresh processes each)

Each session was built in a new process and ran the same input once.

| Size | Mode | sessions | unique output hashes | max abs vs session 0 | same as baseline output |
|---|---|---|---|---|---|
| m | default | 10 | 1 | 0 | yes |
| m | deterministic | 10 | 1 | 0 | yes |
| x-384 | default | 10 | 1 | 0 | yes |
| x-384 | deterministic | 10 | 1 | 0 | yes |

The deterministic outputs are also bit-identical to the default outputs. In each timed job, the output
after the 30 timed runs was bit-identical to the first output (`repeat_identical_after_timed`).

## Interleaved comparison (the numbers for the verdicts)

Each value is the median of the run medians (3 rounds, rotated order; 30 runs each). The "min" columns give
the min of the mins.

| Config | base | gemm | det | gemm vs base | det vs base | base min | gemm min | det min | bit-identical |
|---|---|---|---|---|---|---|---|---|---|
| m b1 fp32 | 5.39 | 5.38 | 5.47 | -0.1% | +1.4% | 5.17 | 5.23 | 5.16 | yes |
| m b1 fp16 (8 rounds) | 4.87 | 4.78 | 4.74 | -1.7% | -2.6% | 4.38 | 4.43 | 4.37 | yes |
| m b3 fp32 | 7.12 | 7.26 | 7.06 | +2.1% | -0.8% | 6.96 | 6.96 | 6.94 | yes |
| m b3 fp16 (8 rounds) | 5.61 | 5.36 | 5.24 | -4.5% | -6.7% | 5.10 | 5.10 | 5.09 | yes |
| x-384 b1 fp32 | 13.64 | 13.67 | 13.66 | +0.2% | +0.1% | 13.51 | 13.44 | 13.49 | yes |
| x-384 b1 fp16 | 9.87 | 10.05 | 9.87 | +1.9% | +0.0% | 9.37 | 9.24 | 9.26 | yes |
| x-384 b3 fp32 | 27.85 | 27.76 | 27.99 | -0.3% | +0.5% | 27.49 | 27.59 | 27.56 | yes |
| x-384 b3 fp16 | 16.34 | 16.33 | 16.34 | -0.1% | +0.0% | 16.13 | 16.16 | 16.18 | yes |

- On m b3 fp16, the base median is higher only because of 3 slow base runs (8.14, 8.13, 6.53 ms). The other 5
  base rounds are 5.21-5.63 ms, the same range as gemm and det, and the min of mins is the same (5.09-5.10 ms).
- The outputs are bit-identical, so the kernels are very likely the same.
- The m models run for about 5 ms, so a GPU clock-state change has a large effect on them.
- The gaps on x-384 are within ±0.5%, except x-384 b1 fp16 gemm at +1.9%, which is one slow round (10.80 ms).

VRAM is the same for the three arms (m fp32 about 400-420 MB, m fp16 about 275-310 MB, x-384 fp32 about
660-700 MB, x-384 fp16 about 400-430 MB).

## Verdicts

- **`enable_gemm_auto_tune=1`.** The plugin reads it (proved by the log and by the parse error), and the
  MatMul kernel parses it. It is not faster: no change beyond noise on any of the 8 configurations (x-384
  -0.3% to +1.9%, m within run-to-run noise). It is exact: all outputs are bit-identical to the baseline,
  with 0 argmax flips. It gives no benefit for rtmw-wholebody133, so leave it off.
- **Deterministic compute (`use_deterministic_compute=True`).** It is not needed on this GPU, plugin and
  model set. The default sessions were already bit-identical across 10 fresh processes for each size (fp32
  b3) and across every timed job. It costs nothing measurable: the time is the same within noise, the
  build time and VRAM are the same, and the output is bit-identical to the default. It is safe to turn on
  as insurance, but it has no effect here. This result covers one GPU (RTX 3070, CC 8.6) only. The cuDNN
  algorithm choice can differ on other GPUs or drivers.
