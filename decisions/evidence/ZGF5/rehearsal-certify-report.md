> **Rehearsal record, not evidence for a platform** ([ADR-ZGF5](../../entries/ZGF5-certify-measurements-of-2026-11-18.md)).
> The tag `certify-v1` existed only in a throw-away clone at commit 2f5efac2. No certification tag
> exists. The line "Valid as evidence" below is not true for a platform. The report below this note
> is unchanged.

# skellytracker certify report

Schema `skellytracker.certify-suite/1`, suite version 1, created 2026-11-19T13:24:14Z (UTC).

**Valid as evidence:** clean checkout of the tag `certify-v1`, all sections run.

| Section | Result | Reason |
|---|---|---|
| 1. Checkout and versions | pass | tag certify-v1, tree clean; Python 3.13.18; 0 package(s) differ from uv.lock |
| 2. Hardware probe | record-only | 2 GPU(s); 4 of 4 OS methods ran; 1 difference(s) flagged in 17 comparisons |
| 3. EPs: install, verify and certify | pass | trt-rtx pass, cuda pass, directml@gpu:10de:2484:0 record-only, directml@gpu:8086:a780:0 record-only, cpu pass; 3 not run |
| 4. Pipeline on each EP against the CPU EP | pass | trt-rtx IoU 0.999, keypoints max 0.0041; cuda IoU 0.989, keypoints max 0.0056; directml@gpu:10de:2484:0 IoU 0.988, keypoints max 0.0056; directml@gpu:8086:a780:0 IoU 0.989, keypoints max 0.0057 |
| 5. JPEG decode and preprocess | not-run | the JPEG certification entry point is not in this checkout |
| 6. Cameras | not-run | not built in this suite version |
| 7. JPEG encode and decode speed | not-run | not built in this suite version |

## 1. Checkout and versions

Result: **pass**, 1.1 s.

| Check | Result | Reason |
|---|---|---|
| checkout | pass |  |
| python | pass |  |
| packages | pass |  |
| onnx-stack | record-only |  |

- checkout: tag: certify-v1, commit: 2f5efac2a3c36b35b472497f45834044cce8e31c, clean: true, changed_files: 0
- os: system: Windows, release: 11, version: 10.0.26300, machine: AMD64
- packages:
  - required: 57
  - extras_only: 21
  - mismatched: none
  - missing: none
  - extras_not_installed: absl-py, altgraph, cffi, contourpy, cycler, fonttools, kiwisolver, matplotlib, mediapipe, ml-dtypes, onnx, pefile, pillow, pycparser, pyinstaller, pyinstaller-hooks-contrib, pyparsing, python-dateutil, pywin32-ctypes, sounddevice, tzdata
- python: implementation: CPython, version: 3.13.18, requires: ==3.13.18
- onnx_stack:
  - skellytracker: v2024.09.1019
  - ort_distributions: onnxruntime-windowsml: 1.30.0.202609102321
  - ort_version: 1.30.0
  - windowsml: 2.6.74rc0
  - ep_names: DmlExecutionProvider, CPUExecutionProvider
  - catalog_revision: d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792
  - set_hash: 4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302
  - probe_errors: none

## 2. Hardware probe

Result: **record-only**, reason `differences-flagged`, 3.0 s.

| Check | Result | Reason |
|---|---|---|
| probe-host | pass |  |
| eps-state | pass |  |
| cim-video-controller | record-only |  |
| cim-processor | record-only |  |
| cim-operating-system | record-only |  |
| nvidia-smi | record-only |  |

- skellytracker:
  - host:
    - os_name: Windows
    - os_release: 11
    - os_version: 10.0.26300
    - arch: AMD64
    - memory_total_bytes: 68388003840
    - os_platform: Windows-11-10.0.26300-SP0
    - os_build: 26300
    - os_label: Windows 11 Home 26H2
    - native_arch: AMD64
    - cpu_name: Intel(R) Core(TM) i7-14700K
    - cpu_physical_cores: 20
    - cpu_logical_cores: 28
    - cpu_max_frequency_hz: 3418000000
    - gpus:
      -
        - vendor: intel
        - name: Intel(R) UHD Graphics 770
        - pci_vendor_id: 32902
        - pci_device_id: 42880
        - pci_subsys_id: 2290225219
        - is_integrated: none
        - is_software: false
        - driver_version: 32.0.101.7088
        - vram_total_bytes: 134217728
        - nvidia: none
      -
        - vendor: nvidia
        - name: NVIDIA GeForce RTX 3070
        - pci_vendor_id: 4318
        - pci_device_id: 9348
        - pci_subsys_id: 928331842
        - is_integrated: none
        - is_software: false
        - driver_version: 610.88
        - vram_total_bytes: 8589934592
        - nvidia: compute_capability: 8.6, brand: geforce
    - virtualization: is_wsl: false, is_vm: false, hypervisor: none
    - container: none
    - probe_errors: none
  - environment:
    - python: implementation: CPython, version: 3.13.18, build: main, Oct 26 2026 14:10:48, compiler: MSC v.1944 64 bit (AMD64)
    - frozen: false
    - package_count: 58
    - probe_errors: none
  - eps:
    - eps:
      -
        - key: trt-rtx
        - state: not_installed
        - reason_code: none
        - usable: false
        - uses_gpu: true
        - certified: true
        - pack_version: 0.5.0
        - catalog_status: ready
        - devices: none
      -
        - key: cuda
        - state: not_installed
        - reason_code: none
        - usable: false
        - uses_gpu: true
        - certified: true
        - pack_version: 0.2.0
        - catalog_status: ready
        - devices: none
      -
        - key: amdgpu
        - state: unsupported
        - reason_code: no-device
        - usable: false
        - uses_gpu: true
        - certified: none
        - pack_version: none
        - catalog_status: field-test
        - devices: none
      -
        - key: migraphx
        - state: unsupported
        - reason_code: no-device
        - usable: false
        - uses_gpu: true
        - certified: none
        - pack_version: none
        - catalog_status: field-test
        - devices: none
      -
        - key: directml
        - state: field_test
        - reason_code: field-test
        - usable: false
        - uses_gpu: true
        - certified: none
        - pack_version: none
        - catalog_status: field-test
        - devices: none
      -
        - key: cpu
        - state: builtin
        - reason_code: none
        - usable: true
        - uses_gpu: false
        - certified: none
        - pack_version: none
        - catalog_status: ready
        - devices: none
    - gpus:
      -
        - device_key: gpu:8086:a780:0
        - name: Intel(R) UHD Graphics 770
        - usable_eps: none
        - recommended: none
      -
        - device_key: gpu:10de:2484:0
        - name: NVIDIA GeForce RTX 3070
        - usable_eps: none
        - recommended: none
    - performance:
      - ep: cpu
      - device_key: none
      - state: ready
      - precision: fp32
      - hardware_class: nvidia-cc80-r580
      - skipped:
        - ep: trt-rtx, state: not_installed
        - ep: cuda, state: not_installed
      - offers: add-pack, add-pack
    - accuracy: ep: cpu, precision: fp32
    - certify_offers: none
    - warning_count: 0
    - core_matches_pin: true
- os_methods:
  -
    - method: cim-video-controller
    - result: record-only
    - reason_code: none
    - seconds: 0.26
    - facts:
      - gpus:
        - vendor_id: 8086, device_id: a780, name: Intel(R) UHD Graphics 770, driver_version: 32.0.101.7088, vram_mib: 2047
        - vendor_id: 10de, device_id: 2484, name: NVIDIA GeForce RTX 3070, driver_version: 32.0.16.1088, vram_mib: none, vram_note: adapter-ram-capped
      - non_pci_adapters: Parsec Virtual Display Adapter
  -
    - method: cim-processor
    - result: record-only
    - reason_code: none
    - seconds: 1.24
    - facts: cpu_name: Intel(R) Core(TM) i7-14700K, cpu_physical_cores: 20, cpu_logical_cores: 28, max_clock_mhz: 3400
  -
    - method: cim-operating-system
    - result: record-only
    - reason_code: none
    - seconds: 0.41
    - facts: os_label: Microsoft Windows 11 Home, os_version: 10.0.26300, os_build: 26300, memory_mib: 65219, os_architecture: 64-bit
  -
    - method: nvidia-smi
    - result: record-only
    - reason_code: none
    - seconds: 0.07
    - facts:
      - scope_vendor_id: 10de
      - gpus:
        - vendor_id: 10de, device_id: 2484, name: NVIDIA GeForce RTX 3070, driver_version: 610.88, vram_mib: 8192
- comparison:
  - method: cim-video-controller, field: gpu_count, gpu: none, skellytracker: 2, os: 2, status: same
  - method: cim-video-controller, field: name, gpu: Intel(R) UHD Graphics 770, skellytracker: Intel(R) UHD Graphics 770, os: Intel(R) UHD Graphics 770, status: same
  - method: cim-video-controller, field: driver_version, gpu: Intel(R) UHD Graphics 770, skellytracker: 32.0.101.7088, os: 32.0.101.7088, status: same
  - method: cim-video-controller, field: vram_mib, gpu: Intel(R) UHD Graphics 770, skellytracker: 128, os: 2047, status: differs
  - method: cim-video-controller, field: name, gpu: NVIDIA GeForce RTX 3070, skellytracker: NVIDIA GeForce RTX 3070, os: NVIDIA GeForce RTX 3070, status: same
  - method: cim-video-controller, field: driver_version, gpu: NVIDIA GeForce RTX 3070, skellytracker: 610.88, os: 32.0.16.1088, status: same
  - method: cim-processor, field: cpu_name, gpu: none, skellytracker: Intel(R) Core(TM) i7-14700K, os: Intel(R) Core(TM) i7-14700K, status: same
  - method: cim-processor, field: cpu_physical_cores, gpu: none, skellytracker: 20, os: 20, status: same
  - method: cim-processor, field: cpu_logical_cores, gpu: none, skellytracker: 28, os: 28, status: same
  - method: cim-operating-system, field: os_label, gpu: none, skellytracker: Windows 11 Home 26H2, os: Microsoft Windows 11 Home, status: same
  - method: cim-operating-system, field: os_version, gpu: none, skellytracker: 10.0.26300, os: 10.0.26300, status: same
  - method: cim-operating-system, field: os_build, gpu: none, skellytracker: 26300, os: 26300, status: same
  - method: cim-operating-system, field: memory_mib, gpu: none, skellytracker: 65219, os: 65219, status: same
  - method: nvidia-smi, field: gpu_count, gpu: none, skellytracker: 1, os: 1, status: same
  - method: nvidia-smi, field: name, gpu: NVIDIA GeForce RTX 3070, skellytracker: NVIDIA GeForce RTX 3070, os: NVIDIA GeForce RTX 3070, status: same
  - method: nvidia-smi, field: driver_version, gpu: NVIDIA GeForce RTX 3070, skellytracker: 610.88, os: 610.88, status: same
  - method: nvidia-smi, field: vram_mib, gpu: NVIDIA GeForce RTX 3070, skellytracker: 8192, os: 8192, status: same
- flagged:
  - method: cim-video-controller, field: vram_mib, gpu: Intel(R) UHD Graphics 770, skellytracker: 128, os: 2047, status: differs

## 3. EPs: install, verify and certify

Result: **pass**, 26.1 s.

| Check | Result | Reason |
|---|---|---|
| trt-rtx | pass |  |
| cuda | pass |  |
| coreml | not-run | os |
| amdgpu | not-run | no-device |
| migraphx | not-run | no-device |
| directml@gpu:10de:2484:0 | record-only |  |
| directml@gpu:8086:a780:0 | record-only |  |
| cpu | pass |  |

- hardware_class: nvidia-cc80-r580
- store: isolated
- eps:
  - trt-rtx:
    - pack_id: trt-rtx-cu13
    - pack_version: 0.5.0
    - download_bytes: 110875664
    - source: network
    - install: ok
    - wheels:
      - filename: onnxruntime_ep_nv_tensorrt_rtx_cu13-0.5.0-py3-none-win_amd64.whl, sha256: 609b19f7236c8522ef005a9f763003a78f492e5d871afad39fe1b247760eb3c7
    - certify_result: pass
    - probe: ok: true, level: L3, max_abs_diff: 0.005252361297607422, reason_code: none
    - gpu: vendor: nvidia, name: NVIDIA GeForce RTX 3070, id: 10de:2484, driver_version: 610.88, compute_capability: 8.6
    - versions: skellytracker: v2024.09.1019, ort_distribution: onnxruntime-windowsml, ort_version: 1.30.0.202609102321, windowsml: 2.6.74rc0, catalog_revision: d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792, set_hash: 4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302
    - result: pass
    - reason_code: none
    - seconds: 5.1
    - ort_version: 1.30.0.202609102321
  - cuda:
    - pack_id: cuda-cu13
    - pack_version: 0.2.0
    - download_bytes: 1009139129
    - source: network
    - install: ok
    - wheels:
      - filename: onnxruntime_ep_cuda13-0.2.0-py3-none-win_amd64.whl, sha256: 607649d2d1b65a080e8df635a9adcab05aa014042ecb60c68352c8ee1aa2e694
      - filename: nvidia_cublas-13.8.0.4-py3-none-win_amd64.whl, sha256: 8c5494423bb8a46822cb6b0cb95d7fa4be2d7b96a31155dff083839ec8297910
      - filename: nvidia_cudnn_cu13-9.27.0.42-py3-none-win_amd64.whl, sha256: 7d96f634adafd55c72231eb0500ca77ab109ec8ebff7b33000b76e081bc4558e
    - certify_result: pass
    - probe: ok: true, level: L3, max_abs_diff: 9.5367431640625e-07, reason_code: none
    - gpu: vendor: nvidia, name: NVIDIA GeForce RTX 3070, id: 10de:2484, driver_version: 610.88, compute_capability: 8.6
    - versions: skellytracker: v2024.09.1019, ort_distribution: onnxruntime-windowsml, ort_version: 1.30.0.202609102321, windowsml: 2.6.74rc0, catalog_revision: d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792, set_hash: 4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302
    - result: pass
    - reason_code: none
    - seconds: 16.6
    - ort_version: 1.30.0.202609102321
  - coreml: state: unsupported, reason_code: os
  - amdgpu: state: unsupported, reason_code: no-device
  - migraphx: state: unsupported, reason_code: no-device
  - directml@gpu:10de:2484:0:
    - result: pass
    - reason_code: none
    - probe: ok: true, level: L3, max_abs_diff: 9.5367431640625e-07
    - vendor: nvidia
    - counts: false
    - seconds: 1.2
    - ort_version: 1.30.0.202609102321
  - directml@gpu:8086:a780:0:
    - result: pass
    - reason_code: none
    - probe: ok: true, level: L3, max_abs_diff: 9.5367431640625e-07
    - vendor: intel
    - counts: false
    - seconds: 1.1
    - ort_version: 1.30.0.202609102321
  - cpu:
    - result: pass
    - reason_code: none
    - probe: ok: true, level: L3, max_abs_diff: 0.0
    - seconds: 1.0
    - ort_version: 1.30.0.202609102321
- pipeline_targets:
  - key: trt-rtx, device_key: none, counts: true
  - key: cuda, device_key: none, counts: true
  - key: directml, device_key: gpu:10de:2484:0, counts: false
  - key: directml, device_key: gpu:8086:a780:0, counts: false
- rocm_version: none

## 4. Pipeline on each EP against the CPU EP

Result: **pass**, 104.9 s.

| Check | Result | Reason |
|---|---|---|
| timing-cpu-1 | record-only |  |
| timing-trt-rtx-1 | record-only |  |
| timing-trt-rtx-3 | record-only |  |
| timing-trt-rtx-6 | record-only |  |
| agreement-trt-rtx | pass |  |
| timing-cuda-1 | record-only |  |
| timing-cuda-3 | record-only |  |
| timing-cuda-6 | record-only |  |
| agreement-cuda | pass |  |
| timing-directml@gpu:10de:2484:0-1 | record-only |  |
| timing-directml@gpu:10de:2484:0-3 | record-only |  |
| timing-directml@gpu:10de:2484:0-6 | record-only |  |
| agreement-directml@gpu:10de:2484:0 | record-only |  |
| timing-directml@gpu:8086:a780:0-1 | record-only |  |
| timing-directml@gpu:8086:a780:0-3 | record-only |  |
| timing-directml@gpu:8086:a780:0-6 | record-only |  |
| agreement-directml@gpu:8086:a780:0 | record-only |  |

- models:
  - path: detectors/object_detectors/yolox-person/yolox-person-m_b3_fp32.onnx, bytes: 101334831, state: downloaded, reason_code: none
  - path: detectors/object_detectors/yolox-person/yolox-person-m_b3_fp16.onnx, bytes: 50726485, state: downloaded, reason_code: none
  - path: detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133-m_b3_fp32.onnx, bytes: 129051749, state: downloaded, reason_code: none
  - path: detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133-m_b3_fp16.onnx, bytes: 64580211, state: downloaded, reason_code: none
- pipeline: yolox-rtmw-wholebody@skellytracker
- calls: warmup: 10, timed: 100, running_mode: video
- eps:
  - cpu:
    - timing:
      - 1: cameras: 1, start_seconds: 0.97, first_call_ms: 392.1, calls: 100, median_ms: 45.9, p95_ms: 48.21, vram_before_mib: 0, peak_vram_mib: 0
    - device_key: none
    - counts: true
    - ort_version: 1.30.0.202609102321
    - libraries_new: none
  - trt-rtx:
    - timing:
      - 1: cameras: 1, start_seconds: 7.18, first_call_ms: 28.1, calls: 100, median_ms: 4.62, p95_ms: 5.3, vram_before_mib: 0, peak_vram_mib: 373
      - 3: cameras: 3, start_seconds: 2.12, first_call_ms: 43.1, calls: 100, median_ms: 7.64, p95_ms: 8.81, vram_before_mib: 243, peak_vram_mib: 377
      - 6: cameras: 6, start_seconds: 2.14, first_call_ms: 75.5, calls: 100, median_ms: 14.65, p95_ms: 16.0, vram_before_mib: 247, peak_vram_mib: 377
    - device_key: none
    - counts: true
    - ort_version: 1.30.0.202609102321
    - libraries_new:
      - name: tensorrt_rtx_1_7.dll, version: 1.7.1.116
    - agreement:
      - people_cpu: 1
      - people_ep: 1
      - box_iou_min: 0.9985001011719705
      - keypoint_px_max: 4.492969925441043
      - keypoint_box_fraction_max: 0.00412249352341009
      - keypoint_box_fraction_median: 0.00028979096826728233
      - keypoint_box_fraction_p99: 0.0030451374638164304
      - points_compared: 137
      - ok: true
      - reason_code: none
      - ran: true
      - pipeline: yolox-rtmw-wholebody@skellytracker
      - image_sha256: 5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d
      - warnings: none
      - models:
        - key: yolox-person@openmmlab-exporter, version: 0.1.0, size: m, precision: fp16, execution_provider: trt-rtx, device: gpu:10de:2484:0
        - key: rtmw-wholebody133@openmmlab-exporter, version: 0.4.0, size: m, precision: fp16, execution_provider: trt-rtx, device: gpu:10de:2484:0
      - thresholds: box_iou_min: 0.9, keypoint_box_fraction_max: 0.01, score_min: 0.4
      - seconds: 3.9
  - cuda:
    - timing:
      - 1: cameras: 1, start_seconds: 1.4, first_call_ms: 37.0, calls: 100, median_ms: 8.02, p95_ms: 9.72, vram_before_mib: 247, peak_vram_mib: 661
      - 3: cameras: 3, start_seconds: 0.61, first_call_ms: 47.1, calls: 100, median_ms: 10.66, p95_ms: 12.02, vram_before_mib: 255, peak_vram_mib: 657
      - 6: cameras: 6, start_seconds: 0.62, first_call_ms: 96.0, calls: 100, median_ms: 20.34, p95_ms: 22.23, vram_before_mib: 255, peak_vram_mib: 659
    - device_key: none
    - counts: true
    - ort_version: 1.30.0.202609102321
    - libraries_new:
      - name: cublas64_13.dll, version: 6.14.11.1380
      - name: cublaslt64_13.dll, version: 6.14.11.1380
      - name: cudnn64_9.dll, version: 9.27.0.42
      - name: cudnn_engines_precompiled64_9.dll, version: 9.27.0.42
      - name: cudnn_engines_runtime_compiled64_9.dll, version: 9.27.0.42
      - name: cudnn_engines_tensor_ir64_9.dll, version: none
      - name: cudnn_graph64_9.dll, version: none
      - name: cudnn_heuristic64_9.dll, version: none
      - name: cudnn_ops64_9.dll, version: 9.27.0.42
    - agreement:
      - people_cpu: 1
      - people_ep: 1
      - box_iou_min: 0.9889630241042078
      - keypoint_px_max: 6.139147647960331
      - keypoint_box_fraction_max: 0.005632932523021593
      - keypoint_box_fraction_median: 0.001535175212239598
      - keypoint_box_fraction_p99: 0.003763240727733195
      - points_compared: 137
      - ok: true
      - reason_code: none
      - ran: true
      - pipeline: yolox-rtmw-wholebody@skellytracker
      - image_sha256: 5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d
      - warnings: none
      - models:
        - key: yolox-person@openmmlab-exporter, version: 0.1.0, size: m, precision: fp16, execution_provider: cuda, device: gpu:10de:2484:0
        - key: rtmw-wholebody133@openmmlab-exporter, version: 0.4.0, size: m, precision: fp16, execution_provider: cuda, device: gpu:10de:2484:0
      - thresholds: box_iou_min: 0.9, keypoint_box_fraction_max: 0.01, score_min: 0.4
      - seconds: 2.2
  - directml@gpu:10de:2484:0:
    - timing:
      - 1: cameras: 1, start_seconds: 1.05, first_call_ms: 27.1, calls: 100, median_ms: 5.34, p95_ms: 6.8, vram_before_mib: 255, peak_vram_mib: 761
      - 3: cameras: 3, start_seconds: 0.98, first_call_ms: 34.9, calls: 100, median_ms: 7.45, p95_ms: 8.68, vram_before_mib: 255, peak_vram_mib: 761
      - 6: cameras: 6, start_seconds: 1.0, first_call_ms: 71.7, calls: 100, median_ms: 15.05, p95_ms: 16.71, vram_before_mib: 255, peak_vram_mib: 761
    - device_key: gpu:10de:2484:0
    - counts: false
    - ort_version: 1.30.0.202609102321
    - libraries_new: none
    - agreement:
      - people_cpu: 1
      - people_ep: 1
      - box_iou_min: 0.9882320906138826
      - keypoint_px_max: 6.102489953751133
      - keypoint_box_fraction_max: 0.005599297508884316
      - keypoint_box_fraction_median: 0.0015407393205613587
      - keypoint_box_fraction_p99: 0.0044470779489972495
      - points_compared: 137
      - ok: true
      - reason_code: none
      - ran: true
      - pipeline: yolox-rtmw-wholebody@skellytracker
      - image_sha256: 5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d
      - warnings: none
      - models:
        - key: yolox-person@openmmlab-exporter, version: 0.1.0, size: m, precision: fp16, execution_provider: directml, device: gpu:10de:2484:0
        - key: rtmw-wholebody133@openmmlab-exporter, version: 0.4.0, size: m, precision: fp16, execution_provider: directml, device: gpu:10de:2484:0
      - thresholds: box_iou_min: 0.9, keypoint_box_fraction_max: 0.01, score_min: 0.4
      - seconds: 2.6
  - directml@gpu:8086:a780:0:
    - timing:
      - 1: cameras: 1, start_seconds: 1.06, first_call_ms: 539.5, calls: 100, median_ms: 87.81, p95_ms: 90.38, vram_before_mib: 255, peak_vram_mib: 255
      - 3: cameras: 3, start_seconds: 1.0, first_call_ms: 550.5, calls: 100, median_ms: 90.09, p95_ms: 93.35, vram_before_mib: 255, peak_vram_mib: 255
      - 6: cameras: 6, start_seconds: 1.01, first_call_ms: 1097.2, calls: 100, median_ms: 179.04, p95_ms: 182.16, vram_before_mib: 255, peak_vram_mib: 255
    - device_key: gpu:8086:a780:0
    - counts: false
    - ort_version: 1.30.0.202609102321
    - libraries_new: none
    - agreement:
      - people_cpu: 1
      - people_ep: 1
      - box_iou_min: 0.9887077931100148
      - keypoint_px_max: 6.177560794040782
      - keypoint_box_fraction_max: 0.005668178239898926
      - keypoint_box_fraction_median: 0.0015472017101151527
      - keypoint_box_fraction_p99: 0.004167902643430854
      - points_compared: 137
      - ok: true
      - reason_code: none
      - ran: true
      - pipeline: yolox-rtmw-wholebody@skellytracker
      - image_sha256: 5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d
      - warnings: none
      - models:
        - key: yolox-person@openmmlab-exporter, version: 0.1.0, size: m, precision: fp16, execution_provider: directml, device: gpu:8086:a780:0
        - key: rtmw-wholebody133@openmmlab-exporter, version: 0.4.0, size: m, precision: fp16, execution_provider: directml, device: gpu:8086:a780:0
      - thresholds: box_iou_min: 0.9, keypoint_box_fraction_max: 0.01, score_min: 0.4
      - seconds: 3.2
- eps_from_section_3: trt-rtx, cuda, directml@gpu:10de:2484:0, directml@gpu:8086:a780:0

## 5. JPEG decode and preprocess

Result: **not-run**, reason `not-in-this-checkout`, 0.7 s.

## 6. Cameras

Result: **not-run**, reason `not-built`, 0.1 s.

## 7. JPEG encode and decode speed

Result: **not-run**, reason `not-built`, 0.1 s.

## Data

```json
{
 "schema": "skellytracker.certify-suite/1",
 "suite_version": 1,
 "created_utc": "2026-11-19T13:24:14Z",
 "selected": [
  1,
  2,
  3,
  4,
  5,
  6,
  7
 ],
 "evidence": {
  "valid": true,
  "reasons": [],
  "tag": "certify-v1",
  "commit": "2f5efac2a3c36b35b472497f45834044cce8e31c"
 },
 "sections": [
  {
   "number": 1,
   "name": "Checkout and versions",
   "result": "pass",
   "reason_code": null,
   "summary": "tag certify-v1, tree clean; Python 3.13.18; 0 package(s) differ from uv.lock",
   "seconds": 1.1,
   "exit_code": 0,
   "checks": [
    {
     "name": "checkout",
     "result": "pass",
     "reason_code": null,
     "reasons": []
    },
    {
     "name": "python",
     "result": "pass",
     "reason_code": null
    },
    {
     "name": "packages",
     "result": "pass",
     "reason_code": null,
     "differ": 0,
     "pinned": 78
    },
    {
     "name": "onnx-stack",
     "result": "record-only",
     "reason_code": null
    }
   ],
   "details": {
    "checkout": {
     "tag": "certify-v1",
     "commit": "2f5efac2a3c36b35b472497f45834044cce8e31c",
     "clean": true,
     "changed_files": 0
    },
    "os": {
     "system": "Windows",
     "release": "11",
     "version": "10.0.26300",
     "machine": "AMD64"
    },
    "packages": {
     "required": 57,
     "extras_only": 21,
     "mismatched": [],
     "missing": [],
     "extras_not_installed": [
      "absl-py",
      "altgraph",
      "cffi",
      "contourpy",
      "cycler",
      "fonttools",
      "kiwisolver",
      "matplotlib",
      "mediapipe",
      "ml-dtypes",
      "onnx",
      "pefile",
      "pillow",
      "pycparser",
      "pyinstaller",
      "pyinstaller-hooks-contrib",
      "pyparsing",
      "python-dateutil",
      "pywin32-ctypes",
      "sounddevice",
      "tzdata"
     ]
    },
    "python": {
     "implementation": "CPython",
     "version": "3.13.18",
     "requires": "==3.13.18"
    },
    "onnx_stack": {
     "skellytracker": "v2024.09.1019",
     "ort_distributions": {
      "onnxruntime-windowsml": "1.30.0.202609102321"
     },
     "ort_version": "1.30.0",
     "windowsml": "2.6.74rc0",
     "ep_names": [
      "DmlExecutionProvider",
      "CPUExecutionProvider"
     ],
     "catalog_revision": "d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792",
     "set_hash": "4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302",
     "probe_errors": []
    }
   },
   "questions": []
  },
  {
   "number": 2,
   "name": "Hardware probe",
   "result": "record-only",
   "reason_code": "differences-flagged",
   "summary": "2 GPU(s); 4 of 4 OS methods ran; 1 difference(s) flagged in 17 comparisons",
   "seconds": 3.0,
   "exit_code": 0,
   "checks": [
    {
     "name": "probe-host",
     "result": "pass",
     "reason_code": null,
     "probe_errors": 0
    },
    {
     "name": "eps-state",
     "result": "pass",
     "reason_code": null
    },
    {
     "name": "cim-video-controller",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "cim-processor",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "cim-operating-system",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "nvidia-smi",
     "result": "record-only",
     "reason_code": null
    }
   ],
   "details": {
    "skellytracker": {
     "host": {
      "os_name": "Windows",
      "os_release": "11",
      "os_version": "10.0.26300",
      "arch": "AMD64",
      "memory_total_bytes": 68388003840,
      "os_platform": "Windows-11-10.0.26300-SP0",
      "os_build": 26300,
      "os_label": "Windows 11 Home 26H2",
      "native_arch": "AMD64",
      "cpu_name": "Intel(R) Core(TM) i7-14700K",
      "cpu_physical_cores": 20,
      "cpu_logical_cores": 28,
      "cpu_max_frequency_hz": 3418000000,
      "gpus": [
       {
        "vendor": "intel",
        "name": "Intel(R) UHD Graphics 770",
        "pci_vendor_id": 32902,
        "pci_device_id": 42880,
        "pci_subsys_id": 2290225219,
        "is_integrated": null,
        "is_software": false,
        "driver_version": "32.0.101.7088",
        "vram_total_bytes": 134217728,
        "nvidia": null
       },
       {
        "vendor": "nvidia",
        "name": "NVIDIA GeForce RTX 3070",
        "pci_vendor_id": 4318,
        "pci_device_id": 9348,
        "pci_subsys_id": 928331842,
        "is_integrated": null,
        "is_software": false,
        "driver_version": "610.88",
        "vram_total_bytes": 8589934592,
        "nvidia": {
         "compute_capability": "8.6",
         "brand": "geforce"
        }
       }
      ],
      "virtualization": {
       "is_wsl": false,
       "is_vm": false,
       "hypervisor": null
      },
      "container": null,
      "probe_errors": []
     },
     "environment": {
      "python": {
       "implementation": "CPython",
       "version": "3.13.18",
       "build": "main, Oct 26 2026 14:10:48",
       "compiler": "MSC v.1944 64 bit (AMD64)"
      },
      "frozen": false,
      "package_count": 58,
      "probe_errors": []
     },
     "eps": {
      "eps": [
       {
        "key": "trt-rtx",
        "state": "not_installed",
        "reason_code": null,
        "usable": false,
        "uses_gpu": true,
        "certified": true,
        "pack_version": "0.5.0",
        "catalog_status": "ready",
        "devices": []
       },
       {
        "key": "cuda",
        "state": "not_installed",
        "reason_code": null,
        "usable": false,
        "uses_gpu": true,
        "certified": true,
        "pack_version": "0.2.0",
        "catalog_status": "ready",
        "devices": []
       },
       {
        "key": "amdgpu",
        "state": "unsupported",
        "reason_code": "no-device",
        "usable": false,
        "uses_gpu": true,
        "certified": null,
        "pack_version": null,
        "catalog_status": "field-test",
        "devices": []
       },
       {
        "key": "migraphx",
        "state": "unsupported",
        "reason_code": "no-device",
        "usable": false,
        "uses_gpu": true,
        "certified": null,
        "pack_version": null,
        "catalog_status": "field-test",
        "devices": []
       },
       {
        "key": "directml",
        "state": "field_test",
        "reason_code": "field-test",
        "usable": false,
        "uses_gpu": true,
        "certified": null,
        "pack_version": null,
        "catalog_status": "field-test",
        "devices": []
       },
       {
        "key": "cpu",
        "state": "builtin",
        "reason_code": null,
        "usable": true,
        "uses_gpu": false,
        "certified": null,
        "pack_version": null,
        "catalog_status": "ready",
        "devices": []
       }
      ],
      "gpus": [
       {
        "device_key": "gpu:8086:a780:0",
        "name": "Intel(R) UHD Graphics 770",
        "usable_eps": [],
        "recommended": null
       },
       {
        "device_key": "gpu:10de:2484:0",
        "name": "NVIDIA GeForce RTX 3070",
        "usable_eps": [],
        "recommended": null
       }
      ],
      "performance": {
       "ep": "cpu",
       "device_key": null,
       "state": "ready",
       "precision": "fp32",
       "hardware_class": "nvidia-cc80-r580",
       "skipped": [
        {
         "ep": "trt-rtx",
         "state": "not_installed"
        },
        {
         "ep": "cuda",
         "state": "not_installed"
        }
       ],
       "offers": [
        "add-pack",
        "add-pack"
       ]
      },
      "accuracy": {
       "ep": "cpu",
       "precision": "fp32"
      },
      "certify_offers": [],
      "warning_count": 0,
      "core_matches_pin": true
     }
    },
    "os_methods": [
     {
      "method": "cim-video-controller",
      "result": "record-only",
      "reason_code": null,
      "seconds": 0.26,
      "facts": {
       "gpus": [
        {
         "vendor_id": "8086",
         "device_id": "a780",
         "name": "Intel(R) UHD Graphics 770",
         "driver_version": "32.0.101.7088",
         "vram_mib": 2047
        },
        {
         "vendor_id": "10de",
         "device_id": "2484",
         "name": "NVIDIA GeForce RTX 3070",
         "driver_version": "32.0.16.1088",
         "vram_mib": null,
         "vram_note": "adapter-ram-capped"
        }
       ],
       "non_pci_adapters": [
        "Parsec Virtual Display Adapter"
       ]
      }
     },
     {
      "method": "cim-processor",
      "result": "record-only",
      "reason_code": null,
      "seconds": 1.24,
      "facts": {
       "cpu_name": "Intel(R) Core(TM) i7-14700K",
       "cpu_physical_cores": 20,
       "cpu_logical_cores": 28,
       "max_clock_mhz": 3400
      }
     },
     {
      "method": "cim-operating-system",
      "result": "record-only",
      "reason_code": null,
      "seconds": 0.41,
      "facts": {
       "os_label": "Microsoft Windows 11 Home",
       "os_version": "10.0.26300",
       "os_build": "26300",
       "memory_mib": 65219,
       "os_architecture": "64-bit"
      }
     },
     {
      "method": "nvidia-smi",
      "result": "record-only",
      "reason_code": null,
      "seconds": 0.07,
      "facts": {
       "scope_vendor_id": "10de",
       "gpus": [
        {
         "vendor_id": "10de",
         "device_id": "2484",
         "name": "NVIDIA GeForce RTX 3070",
         "driver_version": "610.88",
         "vram_mib": 8192
        }
       ]
      }
     }
    ],
    "comparison": [
     {
      "method": "cim-video-controller",
      "field": "gpu_count",
      "gpu": null,
      "skellytracker": 2,
      "os": 2,
      "status": "same"
     },
     {
      "method": "cim-video-controller",
      "field": "name",
      "gpu": "Intel(R) UHD Graphics 770",
      "skellytracker": "Intel(R) UHD Graphics 770",
      "os": "Intel(R) UHD Graphics 770",
      "status": "same"
     },
     {
      "method": "cim-video-controller",
      "field": "driver_version",
      "gpu": "Intel(R) UHD Graphics 770",
      "skellytracker": "32.0.101.7088",
      "os": "32.0.101.7088",
      "status": "same"
     },
     {
      "method": "cim-video-controller",
      "field": "vram_mib",
      "gpu": "Intel(R) UHD Graphics 770",
      "skellytracker": 128,
      "os": 2047,
      "status": "differs"
     },
     {
      "method": "cim-video-controller",
      "field": "name",
      "gpu": "NVIDIA GeForce RTX 3070",
      "skellytracker": "NVIDIA GeForce RTX 3070",
      "os": "NVIDIA GeForce RTX 3070",
      "status": "same"
     },
     {
      "method": "cim-video-controller",
      "field": "driver_version",
      "gpu": "NVIDIA GeForce RTX 3070",
      "skellytracker": "610.88",
      "os": "32.0.16.1088",
      "status": "same"
     },
     {
      "method": "cim-processor",
      "field": "cpu_name",
      "gpu": null,
      "skellytracker": "Intel(R) Core(TM) i7-14700K",
      "os": "Intel(R) Core(TM) i7-14700K",
      "status": "same"
     },
     {
      "method": "cim-processor",
      "field": "cpu_physical_cores",
      "gpu": null,
      "skellytracker": 20,
      "os": 20,
      "status": "same"
     },
     {
      "method": "cim-processor",
      "field": "cpu_logical_cores",
      "gpu": null,
      "skellytracker": 28,
      "os": 28,
      "status": "same"
     },
     {
      "method": "cim-operating-system",
      "field": "os_label",
      "gpu": null,
      "skellytracker": "Windows 11 Home 26H2",
      "os": "Microsoft Windows 11 Home",
      "status": "same"
     },
     {
      "method": "cim-operating-system",
      "field": "os_version",
      "gpu": null,
      "skellytracker": "10.0.26300",
      "os": "10.0.26300",
      "status": "same"
     },
     {
      "method": "cim-operating-system",
      "field": "os_build",
      "gpu": null,
      "skellytracker": "26300",
      "os": "26300",
      "status": "same"
     },
     {
      "method": "cim-operating-system",
      "field": "memory_mib",
      "gpu": null,
      "skellytracker": 65219,
      "os": 65219,
      "status": "same"
     },
     {
      "method": "nvidia-smi",
      "field": "gpu_count",
      "gpu": null,
      "skellytracker": 1,
      "os": 1,
      "status": "same"
     },
     {
      "method": "nvidia-smi",
      "field": "name",
      "gpu": "NVIDIA GeForce RTX 3070",
      "skellytracker": "NVIDIA GeForce RTX 3070",
      "os": "NVIDIA GeForce RTX 3070",
      "status": "same"
     },
     {
      "method": "nvidia-smi",
      "field": "driver_version",
      "gpu": "NVIDIA GeForce RTX 3070",
      "skellytracker": "610.88",
      "os": "610.88",
      "status": "same"
     },
     {
      "method": "nvidia-smi",
      "field": "vram_mib",
      "gpu": "NVIDIA GeForce RTX 3070",
      "skellytracker": 8192,
      "os": 8192,
      "status": "same"
     }
    ],
    "flagged": [
     {
      "method": "cim-video-controller",
      "field": "vram_mib",
      "gpu": "Intel(R) UHD Graphics 770",
      "skellytracker": 128,
      "os": 2047,
      "status": "differs"
     }
    ]
   },
   "questions": []
  },
  {
   "number": 3,
   "name": "EPs: install, verify and certify",
   "result": "pass",
   "reason_code": null,
   "summary": "trt-rtx pass, cuda pass, directml@gpu:10de:2484:0 record-only, directml@gpu:8086:a780:0 record-only, cpu pass; 3 not run",
   "seconds": 26.1,
   "exit_code": 0,
   "checks": [
    {
     "name": "trt-rtx",
     "result": "pass",
     "reason_code": null
    },
    {
     "name": "cuda",
     "result": "pass",
     "reason_code": null
    },
    {
     "name": "coreml",
     "result": "not-run",
     "reason_code": "os"
    },
    {
     "name": "amdgpu",
     "result": "not-run",
     "reason_code": "no-device"
    },
    {
     "name": "migraphx",
     "result": "not-run",
     "reason_code": "no-device"
    },
    {
     "name": "directml@gpu:10de:2484:0",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "directml@gpu:8086:a780:0",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "cpu",
     "result": "pass",
     "reason_code": null
    }
   ],
   "details": {
    "hardware_class": "nvidia-cc80-r580",
    "store": "isolated",
    "eps": {
     "trt-rtx": {
      "pack_id": "trt-rtx-cu13",
      "pack_version": "0.5.0",
      "download_bytes": 110875664,
      "source": "network",
      "install": "ok",
      "wheels": [
       {
        "filename": "onnxruntime_ep_nv_tensorrt_rtx_cu13-0.5.0-py3-none-win_amd64.whl",
        "sha256": "609b19f7236c8522ef005a9f763003a78f492e5d871afad39fe1b247760eb3c7"
       }
      ],
      "certify_result": "pass",
      "probe": {
       "ok": true,
       "level": "L3",
       "max_abs_diff": 0.005252361297607422,
       "reason_code": null
      },
      "gpu": {
       "vendor": "nvidia",
       "name": "NVIDIA GeForce RTX 3070",
       "id": "10de:2484",
       "driver_version": "610.88",
       "compute_capability": "8.6"
      },
      "versions": {
       "skellytracker": "v2024.09.1019",
       "ort_distribution": "onnxruntime-windowsml",
       "ort_version": "1.30.0.202609102321",
       "windowsml": "2.6.74rc0",
       "catalog_revision": "d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792",
       "set_hash": "4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302"
      },
      "result": "pass",
      "reason_code": null,
      "seconds": 5.1,
      "ort_version": "1.30.0.202609102321"
     },
     "cuda": {
      "pack_id": "cuda-cu13",
      "pack_version": "0.2.0",
      "download_bytes": 1009139129,
      "source": "network",
      "install": "ok",
      "wheels": [
       {
        "filename": "onnxruntime_ep_cuda13-0.2.0-py3-none-win_amd64.whl",
        "sha256": "607649d2d1b65a080e8df635a9adcab05aa014042ecb60c68352c8ee1aa2e694"
       },
       {
        "filename": "nvidia_cublas-13.8.0.4-py3-none-win_amd64.whl",
        "sha256": "8c5494423bb8a46822cb6b0cb95d7fa4be2d7b96a31155dff083839ec8297910"
       },
       {
        "filename": "nvidia_cudnn_cu13-9.27.0.42-py3-none-win_amd64.whl",
        "sha256": "7d96f634adafd55c72231eb0500ca77ab109ec8ebff7b33000b76e081bc4558e"
       }
      ],
      "certify_result": "pass",
      "probe": {
       "ok": true,
       "level": "L3",
       "max_abs_diff": 9.5367431640625e-07,
       "reason_code": null
      },
      "gpu": {
       "vendor": "nvidia",
       "name": "NVIDIA GeForce RTX 3070",
       "id": "10de:2484",
       "driver_version": "610.88",
       "compute_capability": "8.6"
      },
      "versions": {
       "skellytracker": "v2024.09.1019",
       "ort_distribution": "onnxruntime-windowsml",
       "ort_version": "1.30.0.202609102321",
       "windowsml": "2.6.74rc0",
       "catalog_revision": "d91fc18cebbbce2c763435376c986ecbcd72ce79b76e05f133d2207d95aa8792",
       "set_hash": "4abfaa7678817ed4a8ccb5f3e355ba28672589e8a3468bb6805e491dfe03a302"
      },
      "result": "pass",
      "reason_code": null,
      "seconds": 16.6,
      "ort_version": "1.30.0.202609102321"
     },
     "coreml": {
      "state": "unsupported",
      "reason_code": "os"
     },
     "amdgpu": {
      "state": "unsupported",
      "reason_code": "no-device"
     },
     "migraphx": {
      "state": "unsupported",
      "reason_code": "no-device"
     },
     "directml@gpu:10de:2484:0": {
      "result": "pass",
      "reason_code": null,
      "probe": {
       "ok": true,
       "level": "L3",
       "max_abs_diff": 9.5367431640625e-07
      },
      "vendor": "nvidia",
      "counts": false,
      "seconds": 1.2,
      "ort_version": "1.30.0.202609102321"
     },
     "directml@gpu:8086:a780:0": {
      "result": "pass",
      "reason_code": null,
      "probe": {
       "ok": true,
       "level": "L3",
       "max_abs_diff": 9.5367431640625e-07
      },
      "vendor": "intel",
      "counts": false,
      "seconds": 1.1,
      "ort_version": "1.30.0.202609102321"
     },
     "cpu": {
      "result": "pass",
      "reason_code": null,
      "probe": {
       "ok": true,
       "level": "L3",
       "max_abs_diff": 0.0
      },
      "seconds": 1.0,
      "ort_version": "1.30.0.202609102321"
     }
    },
    "pipeline_targets": [
     {
      "key": "trt-rtx",
      "device_key": null,
      "counts": true
     },
     {
      "key": "cuda",
      "device_key": null,
      "counts": true
     },
     {
      "key": "directml",
      "device_key": "gpu:10de:2484:0",
      "counts": false
     },
     {
      "key": "directml",
      "device_key": "gpu:8086:a780:0",
      "counts": false
     }
    ],
    "rocm_version": null
   },
   "questions": []
  },
  {
   "number": 4,
   "name": "Pipeline on each EP against the CPU EP",
   "result": "pass",
   "reason_code": null,
   "summary": "trt-rtx IoU 0.999, keypoints max 0.0041; cuda IoU 0.989, keypoints max 0.0056; directml@gpu:10de:2484:0 IoU 0.988, keypoints max 0.0056; directml@gpu:8086:a780:0 IoU 0.989, keypoints max 0.0057",
   "seconds": 104.9,
   "exit_code": 0,
   "checks": [
    {
     "name": "timing-cpu-1",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-trt-rtx-1",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-trt-rtx-3",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-trt-rtx-6",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "agreement-trt-rtx",
     "result": "pass",
     "reason_code": null,
     "box_iou_min": 0.9985001011719705,
     "keypoint_box_fraction_max": 0.00412249352341009,
     "keypoint_box_fraction_median": 0.00028979096826728233,
     "keypoint_box_fraction_p99": 0.0030451374638164304,
     "points_compared": 137
    },
    {
     "name": "timing-cuda-1",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-cuda-3",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-cuda-6",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "agreement-cuda",
     "result": "pass",
     "reason_code": null,
     "box_iou_min": 0.9889630241042078,
     "keypoint_box_fraction_max": 0.005632932523021593,
     "keypoint_box_fraction_median": 0.001535175212239598,
     "keypoint_box_fraction_p99": 0.003763240727733195,
     "points_compared": 137
    },
    {
     "name": "timing-directml@gpu:10de:2484:0-1",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-directml@gpu:10de:2484:0-3",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-directml@gpu:10de:2484:0-6",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "agreement-directml@gpu:10de:2484:0",
     "result": "record-only",
     "reason_code": null,
     "box_iou_min": 0.9882320906138826,
     "keypoint_box_fraction_max": 0.005599297508884316,
     "keypoint_box_fraction_median": 0.0015407393205613587,
     "keypoint_box_fraction_p99": 0.0044470779489972495,
     "points_compared": 137
    },
    {
     "name": "timing-directml@gpu:8086:a780:0-1",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-directml@gpu:8086:a780:0-3",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "timing-directml@gpu:8086:a780:0-6",
     "result": "record-only",
     "reason_code": null
    },
    {
     "name": "agreement-directml@gpu:8086:a780:0",
     "result": "record-only",
     "reason_code": null,
     "box_iou_min": 0.9887077931100148,
     "keypoint_box_fraction_max": 0.005668178239898926,
     "keypoint_box_fraction_median": 0.0015472017101151527,
     "keypoint_box_fraction_p99": 0.004167902643430854,
     "points_compared": 137
    }
   ],
   "details": {
    "models": [
     {
      "path": "detectors/object_detectors/yolox-person/yolox-person-m_b3_fp32.onnx",
      "bytes": 101334831,
      "state": "downloaded",
      "reason_code": null
     },
     {
      "path": "detectors/object_detectors/yolox-person/yolox-person-m_b3_fp16.onnx",
      "bytes": 50726485,
      "state": "downloaded",
      "reason_code": null
     },
     {
      "path": "detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133-m_b3_fp32.onnx",
      "bytes": 129051749,
      "state": "downloaded",
      "reason_code": null
     },
     {
      "path": "detectors/keypoint_detectors/rtmw/wholebody133/rtmw-wholebody133-m_b3_fp16.onnx",
      "bytes": 64580211,
      "state": "downloaded",
      "reason_code": null
     }
    ],
    "pipeline": "yolox-rtmw-wholebody@skellytracker",
    "calls": {
     "warmup": 10,
     "timed": 100,
     "running_mode": "video"
    },
    "eps": {
     "cpu": {
      "timing": {
       "1": {
        "cameras": 1,
        "start_seconds": 0.97,
        "first_call_ms": 392.1,
        "calls": 100,
        "median_ms": 45.9,
        "p95_ms": 48.21,
        "vram_before_mib": 0,
        "peak_vram_mib": 0
       }
      },
      "device_key": null,
      "counts": true,
      "ort_version": "1.30.0.202609102321",
      "libraries_new": []
     },
     "trt-rtx": {
      "timing": {
       "1": {
        "cameras": 1,
        "start_seconds": 7.18,
        "first_call_ms": 28.1,
        "calls": 100,
        "median_ms": 4.62,
        "p95_ms": 5.3,
        "vram_before_mib": 0,
        "peak_vram_mib": 373
       },
       "3": {
        "cameras": 3,
        "start_seconds": 2.12,
        "first_call_ms": 43.1,
        "calls": 100,
        "median_ms": 7.64,
        "p95_ms": 8.81,
        "vram_before_mib": 243,
        "peak_vram_mib": 377
       },
       "6": {
        "cameras": 6,
        "start_seconds": 2.14,
        "first_call_ms": 75.5,
        "calls": 100,
        "median_ms": 14.65,
        "p95_ms": 16.0,
        "vram_before_mib": 247,
        "peak_vram_mib": 377
       }
      },
      "device_key": null,
      "counts": true,
      "ort_version": "1.30.0.202609102321",
      "libraries_new": [
       {
        "name": "tensorrt_rtx_1_7.dll",
        "version": "1.7.1.116"
       }
      ],
      "agreement": {
       "people_cpu": 1,
       "people_ep": 1,
       "box_iou_min": 0.9985001011719705,
       "keypoint_px_max": 4.492969925441043,
       "keypoint_box_fraction_max": 0.00412249352341009,
       "keypoint_box_fraction_median": 0.00028979096826728233,
       "keypoint_box_fraction_p99": 0.0030451374638164304,
       "points_compared": 137,
       "ok": true,
       "reason_code": null,
       "ran": true,
       "pipeline": "yolox-rtmw-wholebody@skellytracker",
       "image_sha256": "5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d",
       "warnings": [],
       "models": [
        {
         "key": "yolox-person@openmmlab-exporter",
         "version": "0.1.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "trt-rtx",
         "device": "gpu:10de:2484:0"
        },
        {
         "key": "rtmw-wholebody133@openmmlab-exporter",
         "version": "0.4.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "trt-rtx",
         "device": "gpu:10de:2484:0"
        }
       ],
       "thresholds": {
        "box_iou_min": 0.9,
        "keypoint_box_fraction_max": 0.01,
        "score_min": 0.4
       },
       "seconds": 3.9
      }
     },
     "cuda": {
      "timing": {
       "1": {
        "cameras": 1,
        "start_seconds": 1.4,
        "first_call_ms": 37.0,
        "calls": 100,
        "median_ms": 8.02,
        "p95_ms": 9.72,
        "vram_before_mib": 247,
        "peak_vram_mib": 661
       },
       "3": {
        "cameras": 3,
        "start_seconds": 0.61,
        "first_call_ms": 47.1,
        "calls": 100,
        "median_ms": 10.66,
        "p95_ms": 12.02,
        "vram_before_mib": 255,
        "peak_vram_mib": 657
       },
       "6": {
        "cameras": 6,
        "start_seconds": 0.62,
        "first_call_ms": 96.0,
        "calls": 100,
        "median_ms": 20.34,
        "p95_ms": 22.23,
        "vram_before_mib": 255,
        "peak_vram_mib": 659
       }
      },
      "device_key": null,
      "counts": true,
      "ort_version": "1.30.0.202609102321",
      "libraries_new": [
       {
        "name": "cublas64_13.dll",
        "version": "6.14.11.1380"
       },
       {
        "name": "cublaslt64_13.dll",
        "version": "6.14.11.1380"
       },
       {
        "name": "cudnn64_9.dll",
        "version": "9.27.0.42"
       },
       {
        "name": "cudnn_engines_precompiled64_9.dll",
        "version": "9.27.0.42"
       },
       {
        "name": "cudnn_engines_runtime_compiled64_9.dll",
        "version": "9.27.0.42"
       },
       {
        "name": "cudnn_engines_tensor_ir64_9.dll",
        "version": null
       },
       {
        "name": "cudnn_graph64_9.dll",
        "version": null
       },
       {
        "name": "cudnn_heuristic64_9.dll",
        "version": null
       },
       {
        "name": "cudnn_ops64_9.dll",
        "version": "9.27.0.42"
       }
      ],
      "agreement": {
       "people_cpu": 1,
       "people_ep": 1,
       "box_iou_min": 0.9889630241042078,
       "keypoint_px_max": 6.139147647960331,
       "keypoint_box_fraction_max": 0.005632932523021593,
       "keypoint_box_fraction_median": 0.001535175212239598,
       "keypoint_box_fraction_p99": 0.003763240727733195,
       "points_compared": 137,
       "ok": true,
       "reason_code": null,
       "ran": true,
       "pipeline": "yolox-rtmw-wholebody@skellytracker",
       "image_sha256": "5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d",
       "warnings": [],
       "models": [
        {
         "key": "yolox-person@openmmlab-exporter",
         "version": "0.1.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "cuda",
         "device": "gpu:10de:2484:0"
        },
        {
         "key": "rtmw-wholebody133@openmmlab-exporter",
         "version": "0.4.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "cuda",
         "device": "gpu:10de:2484:0"
        }
       ],
       "thresholds": {
        "box_iou_min": 0.9,
        "keypoint_box_fraction_max": 0.01,
        "score_min": 0.4
       },
       "seconds": 2.2
      }
     },
     "directml@gpu:10de:2484:0": {
      "timing": {
       "1": {
        "cameras": 1,
        "start_seconds": 1.05,
        "first_call_ms": 27.1,
        "calls": 100,
        "median_ms": 5.34,
        "p95_ms": 6.8,
        "vram_before_mib": 255,
        "peak_vram_mib": 761
       },
       "3": {
        "cameras": 3,
        "start_seconds": 0.98,
        "first_call_ms": 34.9,
        "calls": 100,
        "median_ms": 7.45,
        "p95_ms": 8.68,
        "vram_before_mib": 255,
        "peak_vram_mib": 761
       },
       "6": {
        "cameras": 6,
        "start_seconds": 1.0,
        "first_call_ms": 71.7,
        "calls": 100,
        "median_ms": 15.05,
        "p95_ms": 16.71,
        "vram_before_mib": 255,
        "peak_vram_mib": 761
       }
      },
      "device_key": "gpu:10de:2484:0",
      "counts": false,
      "ort_version": "1.30.0.202609102321",
      "libraries_new": [],
      "agreement": {
       "people_cpu": 1,
       "people_ep": 1,
       "box_iou_min": 0.9882320906138826,
       "keypoint_px_max": 6.102489953751133,
       "keypoint_box_fraction_max": 0.005599297508884316,
       "keypoint_box_fraction_median": 0.0015407393205613587,
       "keypoint_box_fraction_p99": 0.0044470779489972495,
       "points_compared": 137,
       "ok": true,
       "reason_code": null,
       "ran": true,
       "pipeline": "yolox-rtmw-wholebody@skellytracker",
       "image_sha256": "5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d",
       "warnings": [],
       "models": [
        {
         "key": "yolox-person@openmmlab-exporter",
         "version": "0.1.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "directml",
         "device": "gpu:10de:2484:0"
        },
        {
         "key": "rtmw-wholebody133@openmmlab-exporter",
         "version": "0.4.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "directml",
         "device": "gpu:10de:2484:0"
        }
       ],
       "thresholds": {
        "box_iou_min": 0.9,
        "keypoint_box_fraction_max": 0.01,
        "score_min": 0.4
       },
       "seconds": 2.6
      }
     },
     "directml@gpu:8086:a780:0": {
      "timing": {
       "1": {
        "cameras": 1,
        "start_seconds": 1.06,
        "first_call_ms": 539.5,
        "calls": 100,
        "median_ms": 87.81,
        "p95_ms": 90.38,
        "vram_before_mib": 255,
        "peak_vram_mib": 255
       },
       "3": {
        "cameras": 3,
        "start_seconds": 1.0,
        "first_call_ms": 550.5,
        "calls": 100,
        "median_ms": 90.09,
        "p95_ms": 93.35,
        "vram_before_mib": 255,
        "peak_vram_mib": 255
       },
       "6": {
        "cameras": 6,
        "start_seconds": 1.01,
        "first_call_ms": 1097.2,
        "calls": 100,
        "median_ms": 179.04,
        "p95_ms": 182.16,
        "vram_before_mib": 255,
        "peak_vram_mib": 255
       }
      },
      "device_key": "gpu:8086:a780:0",
      "counts": false,
      "ort_version": "1.30.0.202609102321",
      "libraries_new": [],
      "agreement": {
       "people_cpu": 1,
       "people_ep": 1,
       "box_iou_min": 0.9887077931100148,
       "keypoint_px_max": 6.177560794040782,
       "keypoint_box_fraction_max": 0.005668178239898926,
       "keypoint_box_fraction_median": 0.0015472017101151527,
       "keypoint_box_fraction_p99": 0.004167902643430854,
       "points_compared": 137,
       "ok": true,
       "reason_code": null,
       "ran": true,
       "pipeline": "yolox-rtmw-wholebody@skellytracker",
       "image_sha256": "5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d",
       "warnings": [],
       "models": [
        {
         "key": "yolox-person@openmmlab-exporter",
         "version": "0.1.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "directml",
         "device": "gpu:8086:a780:0"
        },
        {
         "key": "rtmw-wholebody133@openmmlab-exporter",
         "version": "0.4.0",
         "size": "m",
         "precision": "fp16",
         "execution_provider": "directml",
         "device": "gpu:8086:a780:0"
        }
       ],
       "thresholds": {
        "box_iou_min": 0.9,
        "keypoint_box_fraction_max": 0.01,
        "score_min": 0.4
       },
       "seconds": 3.2
      }
     }
    },
    "eps_from_section_3": [
     "trt-rtx",
     "cuda",
     "directml@gpu:10de:2484:0",
     "directml@gpu:8086:a780:0"
    ]
   },
   "questions": []
  },
  {
   "number": 5,
   "name": "JPEG decode and preprocess",
   "result": "not-run",
   "reason_code": "not-in-this-checkout",
   "summary": "the JPEG certification entry point is not in this checkout",
   "seconds": 0.7,
   "exit_code": 0,
   "checks": [],
   "details": {},
   "questions": []
  },
  {
   "number": 6,
   "name": "Cameras",
   "result": "not-run",
   "reason_code": "not-built",
   "summary": "not built in this suite version",
   "seconds": 0.1,
   "exit_code": 0,
   "checks": [],
   "details": {},
   "questions": []
  },
  {
   "number": 7,
   "name": "JPEG encode and decode speed",
   "result": "not-run",
   "reason_code": "not-built",
   "summary": "not built in this suite version",
   "seconds": 0.1,
   "exit_code": 0,
   "checks": [],
   "details": {},
   "questions": []
  }
 ],
 "cleanup": [],
 "answers": [],
 "notes": null,
 "scrub": {
  "exempted_terms": 0
 }
}
```
