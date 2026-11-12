# EP accuracy and EP option measurements on an RTX 3070 test host

Measured 2026-11-12. This document uses ASD-STE100 Simplified Technical English. It is evidence for
a later decision entry of the hardware and EP track. It contains no private data: each local path
is a placeholder (`<work>`, `<epdc>`, `<repos>`).

## Why this document exists

The user decided on 2026-11-12: the recommended EP for **accuracy** is `cpu` on each host. The
recommended EP for **performance** is the fastest EP of the host.

This document keeps the measurements that a more granular accuracy recommendation can use later.
For example, a later decision can recommend a GPU EP with special options for one model role. Read
[A granular accuracy recommendation](#a-granular-accuracy-recommendation) before you change the
decision.

## Summary

1. TF32 is the cause of most of the difference between a GPU EP and the CPU EP in fp32.
2. The CUDA EP with `use_tf32=0` gives results at the level of the CPU EP: relative difference
   1e-6 to 1e-5, and 0 SimCC argmax flips on RTMW.
3. The CUDA EP with `use_tf32=0` is not usable for `yolox-person-m` at batch 3 or more. cuDNN then
   selects one convolution algorithm with a workspace of about 5 GB. The run is 6 times slower at
   batch 3 and 45 times slower at batch 6. `cudnn_conv_use_max_workspace=0` does not change this.
4. TF32 has no visible effect on the decoded YOLOX output: the same detections, and boxes within
   0.04 px to 0.24 px. TF32 has a visible effect on RTMW: 4 to 13 argmax flips for each batch.
5. TensorRT RTX has no TF32 option. The environment variable `NVIDIA_TF32_OVERRIDE=0` works on
   TensorRT RTX, but it applies to the full process. With it, RTMW is at relative difference 2.7e-4
   with 0 flips, at 2.2 to 2.4 times the latency.
6. TensorRT RTX is the fastest EP on this host. It builds the fixed-batch `yolox-person-m`, which
   has no TopK and no NonMaxSuppression node. The `TopK K > 3840` failure applies only to the old
   OpenMMLab SDK graph.
7. An EP option key that an EP does not know has three different results. Thus the catalog must
   hold a list of the allowed keys and the allowed values for each EP. See
   [Option key validation](#option-key-validation).

## Test host and versions

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3070, CC 8.6, 8 GB |
| Driver | 610.88 (branch R610) |
| Integrated GPU | Intel UHD Graphics 770 |
| CPU | Intel Core i7-14700K (20 cores, 28 threads) |
| OS | Windows 11 |
| Python | 3.12 |
| ONNX Runtime | `onnxruntime==1.31.0` |
| NumPy | 2.5.4 |
| CUDA EP | `onnxruntime-ep-cuda13==0.3.0`, `nvidia-cublas` 13.8.0.4, `nvidia-cudnn-cu13==9.27.0.42` |
| TensorRT RTX EP | `onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0` |
| OpenVINO EP | `onnxruntime-ep-openvino==1.8.1` (OpenVINO 2026.4.1) |

## Models

The main matrix uses the shipped fixed-batch artifacts of OpenMMLab-Exporter, commit
`dd8a72d9730aea0cfff088da7f7b034f6d4717d2` (folder `exports/`, which git ignores in that repo).

| Artifact | sha256 |
|---|---|
| `yolox-person-m_b1_fp32.onnx` | `a03c054a61ceb1e8ee1a2e704ef9af9198acdf578222f39fec23348d06cccf97` |
| `yolox-person-m_b3_fp32.onnx` | `957ee80507633b2cf7f72fea1730a78a22767808f1b1989da637eb61d050e1c3` |
| `yolox-person-m_b6_fp32.onnx` | `5009a6ec060363d3bea8747fc8d1b9b2548a4b500db10e6ca5c1f9bee940e23e` |
| `yolox-person-m_b1_fp16.onnx` | `5ff8c36b8d0947249c4cfe8b296ef8c7400059b7dabe7c59a3c4dd2fe7c188a7` |
| `yolox-person-m_b3_fp16.onnx` | `1852e6d014c4183973dd575b094a597e97a2b2f50c980597abc4e97185eebf41` |
| `rtmw-wholebody133-x-384_b1_fp32.onnx` | `2e31eff71186672b72a1d55be10da68861076e25626ab6d0752610b8167c608b` |
| `rtmw-wholebody133-x-384_b1_fp16.onnx` | `c16af246d21e00ca996aa1efb6cf55cb8d8628de1209d32f6669c936952864a7` |
| `rtmw-wholebody133-x-384_b3_fp32.onnx` | `10effcbe6135659f9b79452e8beafe542178dfb298acedeb7276dd2d54d3f1b7` |
| `rtmw-wholebody133-x-384_b3_fp16.onnx` | `f0daa384ce548c92b1162f5a1b8c449d1173db4c80583191d31e2881cac1e239` |

- YOLOX: input `[B,3,640,640]` float32; outputs `boxes [B,8400,4]` and `scores [B,8400]`. The host
  does the NMS.
- RTMW: input `[B,3,384,288]` float32; outputs `simcc_x [B,133,576]` and `simcc_y [B,133,768]`
  (SimCC split ratio 2.0).
- The fp16 artifacts have float32 inputs and outputs.

The first TF32 run (see [TF32](#tf32)) used the models of the EP device check suite: the OpenMMLab
SDK exports of RTMPose-m, RTMO-s, YOLOX-m (Human-Art) and RTMW-x 384x288, with dynamic batch.

## Method

- One test image: `single_images_v07_12_26` of the freemocap skellysamples releases (the image of
  the EP device check suite).
- YOLOX input: BGR, letterbox to 640x640, pad value 114 at the top left, no normalisation.
- RTMW input: RGB, a 288x384 crop around the person box (60, 40, 560, 860), ImageNet mean and
  standard deviation.
- Batch 3 holds three different images: the original, a horizontal flip and a shifted crop. Batch 6
  adds a flip with a shift, a zoomed crop and a rotation of 5 degrees.
- Reference: the CPU EP, the fp32 artifact, `ORT_ENABLE_ALL`, default threads. An fp16 artifact is
  compared with the fp32 reference of the same model and batch.
- Each configuration runs in its own new process. Only one GPU process runs at a time.
- Each configuration records:
  - the session build time and the first run time;
  - the median and p95 of 30 runs, after 5 warm-up runs;
  - the largest absolute difference from the reference, and the relative difference (the largest
    absolute difference divided by the largest absolute reference value);
  - the NaN and Inf counts;
  - the node count of each EP, from `session.record_ep_graph_assignment_info=1` and
    `get_provider_graph_assignment_info()`;
  - the peak VRAM (NVML, the full device, so it includes the CUDA context);
  - the process CPU time for each run.
- Decoded effect:
  - RTMW: the SimCC argmax of each keypoint. The flip count compares with the reference, for all
    keypoints and for the top half by reference score. The largest keypoint error in input pixels
    is the argmax difference divided by 2.
  - YOLOX: the count of anchors with score > 0.3, and the largest box coordinate difference in
    pixels over those anchors.

## TF32

### CUDA and TensorRT RTX on the SDK models (EP device check suite, fp32, batch 1)

Run with default settings, then with `NVIDIA_TF32_OVERRIDE=0`. Reports: `suite-reports/`.

| Model | CUDA, TF32 on | CUDA, TF32 off | TRT-RTX, TF32 on | TRT-RTX, TF32 off |
|---|---|---|---|---|
| L3 probe (one Conv) | 2.86e-6 | 2.86e-6 | 8.47e-3 | 1.24e-5 |
| RTMPose-m | 2.5 ms, rel 2.9e-3 | 2.7 ms, rel 2.0e-6 | 1.5 ms, rel 1.8e-3 | 2.5 ms, rel 2.0e-4 |
| RTMO-s | 7.8 ms, rel 1.2e-4 | 7.7 ms, rel 1.9e-7 | build fails (NMS) | build fails |
| YOLOX-m (SDK) | 20.6 ms, rel 8.0e-5 | 20.3 ms, rel 1.9e-8 | build fails (TopK K > 3840) | build fails |
| RTMW-x 384 (SDK) | 10.0 ms, rel 1.1e-3 | 14.8 ms, rel 1.0e-5 | 6.9 ms, rel 1.2e-3 | 12.4 ms, rel 1.3e-4 |

The small probe does not show TF32 on CUDA: cuDNN selects a kernel with no tensor cores for an
input with 3 channels. Use real models to measure TF32.

### CUDA and TensorRT RTX on the exporter models

| Configuration | Model, batch, precision | Median ms | Relative difference | Decoded effect | VRAM MB |
|---|---|---|---|---|---|
| CUDA defaults (TF32 on) | rtmw b1 fp32 | 14.2 | 1.1e-2 | 4 flips, 0.5 px | 661 |
| CUDA `use_tf32=0` | rtmw b1 fp32 | 20.2 | 6e-6 | 0 flips | – |
| CUDA defaults | rtmw b3 fp32 | 28.8 | 1.1e-2 | 12 flips, 0.5 px | 665 |
| CUDA `use_tf32=0` | rtmw b3 fp32 | 35.5 | 6.0e-6 | 0 flips | 661 |
| CUDA defaults | yolox b3 fp32 | 29.5 | 7.7e-4 | 27 to 27 detections, 0.04 px | 661 |
| CUDA `use_tf32=0` | yolox b1 fp32 | 12.4 | 1.9e-6 | 9 to 9 | 402 |
| CUDA `use_tf32=0` | yolox b3 fp32 | 184.0 | 1.7e-6 | 27 to 27 | 5073 |
| CUDA defaults | yolox b6 fp32 | 58.0 | 1.3e-3 | 54 to 54, 0.24 px | 659 |
| CUDA `use_tf32=0` | yolox b6 fp32 | 2638 | 2.1e-6 | 54 to 54 | 5988 |
| TRT-RTX defaults | rtmw b3 fp32 | 20.1 | 8.3e-3 | 13 flips, 0.5 px | 575 |
| TRT-RTX `NVIDIA_TF32_OVERRIDE=0` | rtmw b3 fp32 | 47.8 | 2.7e-4 | 0 flips | 545 |
| TRT-RTX `NVIDIA_TF32_OVERRIDE=0` | yolox b3 fp32 | 45.1 | 1.5e-4 | – | – |

The CPU EP reference: yolox b1 61.5 ms, yolox b3 199.7 ms, yolox b6 452 ms, rtmw b1 51.4 ms,
rtmw b3 153.9 ms.

### The YOLOX workspace problem with TF32 off

- With `use_tf32=0` and batch 3 or more, cuDNN selects one algorithm for the node
  `/bbox_head/multi_level_cls_convs.0/multi_level_cls_convs.0.0/conv/Conv` (the first
  classification Conv of the 80x80 level). This algorithm asks for a workspace of 4,985,339,904
  bytes. The plugin log shows only the arena request:
  `Extending arena for Cuda. bin_num:20 (requested) num_bytes: 4985339904`.
- These options do not change the choice: `cudnn_conv_use_max_workspace=0`,
  `cudnn_conv_algo_search=HEURISTIC`, `prefer_nhwc=1`.
- With `arena.max_mem=1073741824`, the run fails with a memory allocation error. The EP does not
  select a smaller algorithm.
- A GPU with 4 GB of VRAM cannot run this configuration.

## CUDA EP options (plugin 0.3.0)

| Option | Result | Verdict |
|---|---|---|
| `use_tf32=0` | See [TF32](#tf32) | Exact. Not usable for YOLOX at batch 3 or more |
| `prefer_nhwc=1` | fp16: rtmw b3 13.6 ms against 17.2 ms; yolox b3 14.9 ms against 18.4 ms. With `use_tf32=0`: rtmw b3 50.2 ms against 35.5 ms. VRAM in fp32 about 1.8 times | Useful for performance with fp16 only |
| `cudnn_conv_algo_search` | HEURISTIC and EXHAUSTIVE give the same result as the default. DEFAULT is 13 to 26 times slower (rtmw b3 369 ms) | Do not change |
| `cudnn_conv_use_max_workspace=0` | No effect on any tested configuration | Do not use |
| `fuse_conv_bias=1` | fp32: outputs change from run to run. With `use_tf32=0`: wrong outputs (rtmw rel 0.35, 221 flips, 3.5 px; yolox box error 58 px). fp16: 3,000 to 4,000 ms CPU time for each run | Do not use |
| `enable_cuda_graph=1` | Needs I/O binding with `OrtValue.ortvalue_from_shape_and_type(..., memory_info=ep_device.memory_info(OrtDeviceMemoryType.DEFAULT))`. 6% to 9% faster at batch 1, about 2% at batch 3. Session creation fails when a node is on the CPU EP (rtmw fp16 has 3 Clip nodes on CPU). A plain `session.run()` on a graph session returns an empty list with no error | Useful for performance. Needs I/O binding in the runtime |
| `arena.max_mem` | The limit is enforced. A larger request fails the run | Use only as a hard limit |
| `arena.extend_strategy=1` | VRAM 563 MB against 661 MB on yolox b3; 755 MB against 665 MB on rtmw b3 | No conclusion |
| `session.use_deterministic_compute=1` | 10 new sessions gave identical outputs (bit for bit) with and without this key (rtmw b3 fp32, `use_tf32=0`). **VOID (verification 2026-11-12):** the key was set with `add_session_config_entry`, which ORT does not read for this key; re-run with `so.use_deterministic_compute = True` | No result |

## TensorRT RTX EP options (EP-ABI 0.5.0)

No configuration put a node on the CPU EP.

| Configuration | yolox b1 fp32 / fp16 | yolox b3 fp32 / fp16 | rtmw b1 fp32 / fp16 | rtmw b3 fp32 / fp16 |
|---|---|---|---|---|
| Defaults: median ms | 7.16 / 3.33 | 19.95 / 9.24 | 8.32 / 3.65 | 20.06 / 8.73 |
| Defaults: build ms (no cache) | 4898 / 3070 | 2329 / 2910 | 4217 / 4952 | 4577 / 5403 |
| `nv_runtime_cache_path`: build ms cold to warm | 4154 to 1102 / 2764 to 991 | 2591 to 2231 / 2923 to 971 | 3935 to 1891 / 4840 to 1625 | 4105 to 1849 / 4818 to 1566 |

- Each runtime cache is one file of about 4 MB.
- EPContext works only as session config entries (`ep.context_enable`, `ep.context_file_path`,
  `ep.context_embed_mode`). As provider options, the keys are accepted, but no file is written.
- EPContext load time in a new process: yolox fp32 1628 ms (embed 0) and 1753 ms (embed 1); rtmw
  fp32 2870 ms and 3112 ms. With a warm runtime cache: yolox fp32 494 ms, yolox fp16 353 ms, rtmw
  fp32 1051 ms, rtmw fp16 664 ms.
- Embed mode 1 writes one `.onnx` file of 54 MB to 373 MB. Embed mode 0 writes a small `.onnx` file
  and an engine file of about 100 MB with a generic name
  (`NvTensorRTRTXExecutionProvider_..._0_0.engine`). The generic name can cause a collision.
- `session.fail_on_suboptimal_compiled_model=1` loads the context model with no change.
- `nv_persistent_context_memory=1`: no change in latency (rtmw b3 20.9 ms against 20.1 ms).
- `enable_cuda_graph=0`: 12% to 21% slower at batch 1 and 4% to 16% slower at batch 3. Thus the
  default is on.

## CPU EP and session options

| Option | Result | Verdict |
|---|---|---|
| `ORT_ENABLE_EXTENDED`, `ORT_ENABLE_BASIC` | 2 to 5 times slower than `ORT_ENABLE_ALL` (yolox b3 1078 ms against 200 ms). Difference about 1e-6 | Keep `ORT_ENABLE_ALL` |
| `session.dynamic_block_base=4` | 61.5 to 65.8, 199.7 to 193.7, 51.4 to 55.9, 153.9 to 152.4 ms | Do not use |
| `intra_op_num_threads` | The default is the same as 20. 8 threads: 1.3 to 1.4 times slower at half the CPU time. 1 thread: 7.7 times slower | Keep the default for a CPU session |
| `session.intra_op.allow_spinning=0` | CPU time 16% to 24% lower; latency 6% lower to 13% higher | Useful to decrease CPU load |

Multi-camera simulation: 3 threads, each with its own CUDA session (rtmw fp32 b1, `use_tf32=0`),
100 frames each. 78 to 83 frames per second for all combinations of thread count (default or 1)
and spinning (on or off), at 16 to 18 ms CPU time for each frame. One batch 3 session gives about
84 frames per second.

## OpenVINO EP (deferred)

The user deferred the OpenVINO EP on 2026-11-12. It is for discrete Intel GPUs only, and no test
host has one. These facts come from the Intel UHD 770 integrated GPU:

- The UHD 770 is slower than the CPU EP for both models (rtmw b1 75.7 ms against 51.4 ms).
- `load_config` must use the resolved device name, for example `{"GPU.0": {...}}`. Under the key
  `"GPU"`, each setting is ignored with no message.
- `INFERENCE_PRECISION_HINT=f32` or `EXECUTION_MODE_HINT=ACCURACY` gives relative difference 4e-6,
  at 1.6 to 1.8 times the latency. The default GPU precision is f16 (rtmw rel 4.2e-2, 35 flips).
- The default GPU queue waits busy: CPU time is equal to the wall time. `GPU_QUEUE_THROTTLE=LOW`
  decreases the CPU time by 98%, at 1.5% more latency.
- `CACHE_DIR` decreases a warm build to 356 ms to 960 ms. The first compile ever is 5 s to 8 s.
- `PERFORMANCE_HINT`, `NUM_STREAMS` and `MODEL_PRIORITY` had no effect with one synchronous caller.
- `session.disable_cpu_ep_fallback=1`: the session builds, and all nodes are on OpenVINO.

## Option key validation

| EP | Unknown key (`bogus_key=1`) | Invalid value | Other |
|---|---|---|---|
| CUDA plugin 0.3.0 | Ignored, no message | Default used: `use_tf32=banana` acts as TF32 on. **Correction (verification 2026-11-12):** the source logs a WARNING `Failed to parse session config for key ...`; the first harness kept the last 1,500 characters of the log text with its NUL bytes (750 characters of text), and it searched the text before the decode, so the message was not seen. `results/log-excerpts.txt` holds the lines. An invalid `arena.*` value fails the session | `gpu_mem_limit` is ignored with no effect |
| TensorRT RTX 0.5.0 | The EP fails to start. ONNX Runtime logs `Unknown provider option: "bogus_key"` and then runs **all nodes on the CPU EP** (388 nodes, 60 ms) with no error | – | `device_id` gives the same result |
| OpenVINO 1.8.1 | – | – | `precision` and `cache_dir` as provider options: a warning, and no effect |

Thus:
- the session builder must check the node assignment of each session build, and refuse a session
  that has nodes on an EP that it did not request;
- the EP catalog must list the allowed keys and the allowed values of each EP.

## Node-to-EP statistics

`session.record_ep_graph_assignment_info=1` and `get_provider_graph_assignment_info()` give the EP
of each node, also for EPs that compile a partition. They need no profiling option and cost no time
during a run. They cannot show work that an EP does inside its own partition: OpenVINO can move a
partition to its CPU device, and CoreML selects the Neural Engine, the GPU or the CPU for each
operator.

## A granular accuracy recommendation

The measurements support this granular form. The user did not select it (2026-11-12).

| Model role | Accuracy EP | Reason |
|---|---|---|
| Keypoint model (RTMW; RTMPose to be measured) | CUDA with `use_tf32=0` | 0 flips; 23% to 42% slower than TF32 on, and 4 times faster than the CPU EP |
| Object detector (YOLOX) | CUDA with defaults (TF32 on) | The same detections and boxes within 0.24 px. TF32 off needs about 5 GB VRAM at batch 3 or more |

Before a decision uses this form, measure:

- the same matrix on the GTX 1650 (CC 7.5, no TF32) and on a GPU with 4 GB of VRAM;
- RTMPose body, hand and face, and RTMO, when their fixed-batch exports exist;
- the decoded effect on a video sequence, not on one image;
- a newer CUDA plugin or cuDNN version, for the workspace choice of YOLOX with TF32 off.

## Limits

- One test host and one test image.
- VRAM is the change of the full device, measured by NVML. It includes the CUDA context.
- The TensorRT RTX and OpenVINO builds are on Windows only. Linux is not measured.
- CoreML, the OpenVINO NPU and the Windows ML catalog EPs are not measured.

## Files

| File | Content |
|---|---|
| `scripts/make_inputs.py` | Makes the input arrays from the test image (`--b6` for batch 6) |
| `scripts/child.py` | Runs one configuration in its own process and writes one result |
| `scripts/run_matrix.py` | Holds the matrix and runs the rows (`run_matrix.py ROW ...`) |
| `scripts/summarize.py` | Makes `results/tables.md` from `results/results.jsonl` |
| `results/tables.md` | All rows as tables |
| `results/log-excerpts.txt` | The WARNING and error lines of the option key validation, copied from the raw logs |
| `suite-reports/tf32-default/report.md`, `suite-reports/tf32-override/report.md` | The EP device check suite reports of the first TF32 run |
| `gemm-v4/` | `enable_gemm_auto_tune` and deterministic compute on the v4 `rtmw-wholebody133` artifacts: `RESULTS.md`, `models.json` and `scripts/` |

These files are not in git, because they are raw data and hold local paths: `results/results.jsonl`
(one line for each configuration; `summarize.py` reads it), the job files and the logs of each run,
`gemm-v4/results.jsonl`, `gemm-v4/summary.json` and the `report.json` of each suite report.

## Source lines

The source facts were read at the tags `plugin-ep-cuda/v0.3.0` (the same commit as ONNX Runtime
`v1.31.0`) and NVIDIA/TensorRT-RTX-EP-ABI `v0.5.0`.

| Fact | Source |
|---|---|
| CUDA plugin: an unknown name is ignored; an invalid core value logs a WARNING and uses the default | `cuda_ep_factory.cc` L549-564 |
| CUDA plugin: an invalid `arena.*` value fails the session | `cuda_arena.h` L107-198; `cuda_ep_factory.cc` L697-704, L777-782 |
| TensorRT RTX: an unknown name or an invalid value stops the EP; the boolean values | `src/utils/provider_options_utils.h` L313-323; `src/utils/parse_string.h` L65-79 |
| TensorRT RTX: the values of `nv_target_sm` | `src/tensorrt_rtx_provider_options.h` L337-342 |
| TensorRT RTX: a device only for CC 8.6, 8.9 and 12.0 or higher | `src/tensorrt_rtx_provider_options.h` L351-359; `src/tensorrt_rtx_provider_factory.cc` L1156, L1196 |
| Python: a setter-alias key of `add_session_config_entry` has no effect | `abi_session_options.cc` L317-331, L422-511; `onnxruntime_pybind_state.cc` L2731-2737 |
| Python: `InferenceSession` builds a CPU session again after an EP error | `onnxruntime_inference_collection.py` L682-698, L756 |

The scripts use these placeholders for local folders: `<epdc>` (the environments of the EP device
check suite), `<repos>` (the folder of the repositories) and `<work>` (a work folder). Before a run,
change them to real paths.
