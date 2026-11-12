# NZK1 — EP option measurements: option checks, TF32 and the options of the CUDA and TensorRT RTX packs

**Status:** evidence; used by [246B](246B-ep-catalog-store-and-install.md), 2026-11-12 (measurements of the hardware and EP track; PR: pending).

## Decision

1. **Option checks.** This item corrects the Reason of
   [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) ("with no message"). The decision of 9NW0 stays.
   - CUDA plugin, unknown option name: the plugin ignores it with no log line.
   - CUDA plugin, invalid value of a core option: ORT logs the WARNING `Failed to parse session config
     for key 'ep.cuda.<key>'. ... Using default value.` (`cuda_ep_factory.cc:559`). The session uses
     the default, so `use_tf32=banana` runs with TF32 on. Measured for `use_tf32`,
     `cudnn_conv_use_max_workspace` and `cudnn_conv_algo_search`.
   - CUDA plugin, invalid `arena.*` value: the session is not created (read in the source). An
     invalid `enable_gemm_auto_tune` value: the session is not created (measured).
   - TensorRT RTX: an unknown name stops the EP (measured). An invalid value also stops it (read in
     the source). Booleans accept only `0`, `1`, `false`, `true`, `False` and `True`. `nv_target_sm`
     accepts only `sm86`, `sm89`, `sm120` and `sm121`.
   - The first harness did not show the WARNING. It did not decode the UTF-16 log. It kept only the
     last 1,500 characters (750 characters of text), and it searched the text with the NUL bytes.
     The full logs hold the WARNING.
2. **TF32 (CUDA, fp32).** The default (TF32 on) gives RTMW a relative difference of 1.1e-2 from the
   CPU EP, with 4 (batch 1) and 12 (batch 3) SimCC argmax flips of 0.5 px. `use_tf32=0` gives 6e-6
   and 0 flips, at 20.2 ms against 14.2 ms (batch 1). On YOLOX, TF32 changes no detection, and boxes
   move 0.04 px to 0.24 px. With `use_tf32=0` at batch 3 or more, cuDNN selects a YOLOX Conv
   algorithm with a 4,985,339,904-byte workspace: 6 times slower at batch 3, 45 times at batch 6,
   about 5 GB of VRAM. No option changes this choice. TensorRT RTX has no TF32 option.
3. **CUDA plugin options.**
   - `prefer_nhwc=1`: faster in fp16 only (RTMW batch 3 13.6 ms against 17.2 ms, YOLOX batch 3
     14.9 ms against 18.4 ms). In fp32 with `use_tf32=0` it is slower (RTMW batch 3 50.2 ms against
     35.5 ms). In fp32 it uses about 1.8 times the VRAM.
   - `cudnn_conv_algo_search`: `HEURISTIC` and `EXHAUSTIVE` are equal to the default. `DEFAULT` is 13
     to 26 times slower. `cudnn_conv_use_max_workspace=0` has no effect.
   - `fuse_conv_bias=1`: wrong outputs. With `use_tf32=0`: RTMW relative difference 0.35, 221 flips;
     YOLOX box error 58 px. In fp32 the outputs change from run to run. In fp16 each run takes
     3,000 ms to 4,000 ms of CPU time.
   - `enable_cuda_graph=1`: 6% to 9% faster at batch 1, about 2% at batch 3. It needs I/O binding.
     It fails the session when a node is on the CPU EP. A plain `session.run()` returns an empty list
     with no error.
   - `enable_gemm_auto_tune=1`: the plugin reads it, but it gives no gain on 8 RTMW configurations
     (-0.3% to +1.9% on x-384). The outputs are bit-identical.
   - `use_deterministic_compute`: the default sessions were already bit-identical over 10 new
     processes. The attribute changed no output and no time.
4. **TensorRT RTX options.** `enable_cuda_graph` is on by default. The header doc says `0`, but the
   option struct holds `1`. Off is 12% to 21% slower at batch 1 and 4% to 16% slower at batch 3.
   `nv_runtime_cache_path` decreases a warm build to 1.0 s to 2.2 s (cold 2.6 s to 4.8 s).
   EPContext works only as session config entries. No configuration put a node on the CPU EP. The
   factory lists a device only for CC 8.6, 8.9 and 12.0 or higher (read in the source).
5. **Session options.** From Python, `add_session_config_entry` with a setter-alias key (for
   example `session.intra_op_num_threads`, `session.use_deterministic_compute`) has no effect (read
   in the source). Use the `SessionOptions` attributes. `ORT_ENABLE_ALL` is 2 to 5 times faster than the lower
   levels. `session.intra_op.allow_spinning=0` decreases the CPU time by 16% to
   24%. Only the value `1` turns spinning on.
6. **CPU nodes.** The v4 `rtmw-wholebody133` artifacts (opset 17) put 0 nodes on the CPU EP with the
   CUDA plugin, in fp32 and in fp16.

## Reason

- The body of 9NW0 cannot change. This entry records the correct facts for the option checks.
- The allow-lists of the EP catalog and the performance defaults need measured values.

## Evidence

- Host: RTX 3070 (CC 8.6, 8 GB), driver 610.88, Intel Core i7-14700K, Windows 11 build 10.0.26300,
  CPython 3.12.13. Packs: `onnxruntime` 1.31.0, `numpy` 2.5.4, `onnxruntime-ep-cuda13` 0.3.0 with
  `nvidia-cublas` 13.8.0.4 and `nvidia-cudnn-cu13` 9.27.0.42, `onnxruntime-ep-nv-tensorrt-rtx-cu13`
  0.5.0 (TensorRT RTX 1.7).
- Models: OpenMMLab-Exporter commit `dd8a72d9730aea0cfff088da7f7b034f6d4717d2`,
  `yolox-person-m` and `rtmw-wholebody133-x-384`, batch 1, 3 and 6, fp32 and fp16 (sha256 in the
  README). The gemm and deterministic parts of item 3, and item 6: the v4 `rtmw-wholebody133` m and
  x-384 artifacts, batch 1 and 3, with the sha256 of the v4 intake.
- Method: one new process for each configuration, one GPU process at a time. 5 warm-up runs, then
  the median of 30 runs. Reference: the CPU EP in fp32. One test image of the EP device check suite.
- Scripts in [`decisions/scripts/ep_options/`](../scripts/ep_options/README.md):
  `scripts/run_matrix.py`, `scripts/child.py`, `scripts/make_inputs.py` and `scripts/summarize.py`
  (items 1 to 5), `gemm-v4/scripts/` (`enable_gemm_auto_tune` and deterministic compute). Results:
  `results/tables.md`, `results/log-excerpts.txt`, `gemm-v4/RESULTS.md`, `suite-reports/`.
- Source facts: read at the tags `plugin-ep-cuda/v0.3.0` (= ORT `v1.31.0`) and
  NVIDIA/TensorRT-RTX-EP-ABI `v0.5.0`. [Source lines](../scripts/ep_options/README.md#source-lines)
  gives the files and the lines.

## Not repeated

- A test of `use_deterministic_compute` through `add_session_config_entry` is void (item 5).
