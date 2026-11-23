# Decision log: evidence entries

These entries are `evidence`: measurements. They are not in the read path. Scan these rows before
you make a measurement, and read the entries that apply ([Rules](README.md#rules)). An entry that an
accepted entry uses, or that a later measurement replaces, is in [historical.md](historical.md).

### Evidence

| # | Decision | Status |
|---|----------|--------|
| [Z0CC](entries/Z0CC-exporter-coverage-measurements.md) | Exporter coverage measurements of 2026-10: RF-DETR graph checks, RTMDet AP of resize and NMS, COCO id and in-graph cap defects | evidence |
| [X6S9](entries/X6S9-mediapipe-close-from-the-garbage-collector.md) | A MediaPipe landmarker closed by the garbage collector on its own worker thread hangs; the runner and the old detectors close on a new thread | evidence |
| [73Q4](entries/73Q4-local-gpu-gate-of-the-ep-api.md) | Local GPU gate on an RTX 3070: L3 and sessions pass on `cuda` and `trt-rtx`; fp16 files have 0 CPU nodes, except 5 stale opset 11 RTMW files; frozen install ok | evidence |
| [GPW6](entries/GPW6-model-gate-of-the-first-models.md) | Model gate of `yolox-person` and `rtmw-wholebody133` at the detector level: parity passes on the CPU EP, `cuda` and `trt-rtx`; batch conversion 0.01 s to 1.02 s | evidence |
| [7E4Z](entries/7E4Z-box-parity-of-the-built-in-with-sfn26.md) | Box parity of `yolox-rtmw-wholebody` with the tracker of `sfn26`: recording script and fixture; test A passes on 200 frames; report B on the CPU EP and `cuda` | evidence |
| [ZGF5](entries/ZGF5-certify-measurements-of-2026-11-18.md) | Certify reports of 2026-11-18/19: source reports, 2 px failure, spread of 10 suite reports, rehearsal clone; XSE7 rehearsal stale | evidence |
| [FBV5](entries/FBV5-gpu-path-agreement-on-the-freemocap-sample-data.md) | GPU against CPU path on the freemocap sample data: keypoint median / p99 1.18 / 7.55 px, as large as between two EPs | evidence |
| [BP5Y](entries/BP5Y-gpu-huffman-decode-threshold.md) | nvJPEG GPU Huffman threshold 500000 halves `frame.decode` at 1280x720, equal pixels; 0 slows small frames; the exit text | evidence |
| [975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md) | nvImageCodec 0.10.0.9 one-image decode hangs with fewer CUDA streams than threads: 19 of 62 cells; workaround, self-test | evidence |
| [71YY](entries/71YY-intel-qsv-jpeg-decode-against-the-cpu-thread-pool.md) | Intel QSV JPEG decode (PyAV, UHD 770): slower than the CPU thread pool to BGR at 2, 4 and 28 CPUs; 4:2:2 loses chroma; not built | evidence |
| [C6A5](entries/C6A5-exit-hang-of-the-cuda-ep-plugin.md) | Exit hang of `cuda-cu13` 0.3.0 on Windows: 9 of 192 long runs; hard end 0 of 60; 1DS telemetry client in the DLL; switch not tested | evidence |
| [C9ME](entries/C9ME-exit-hang-rate-with-the-telemetry-switch.md) | Exit hang of the minimal reproducer, `cuda-cu13` 0.3.0: 0 of 120 with `ORT_DISABLE_TELEMETRY=1`, 1 of 120 without; not separated (p = 1.0) | evidence |
| [J9KX](entries/J9KX-exit-hang-of-the-full-run-with-the-telemetry-switch.md) | Exit hang of the full run, `cuda-cu13` 0.3.0: 0 of 240 with `ORT_DISABLE_TELEMETRY=1`, 28 of 120 without | evidence |
