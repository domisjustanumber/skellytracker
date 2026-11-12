# V9NK — EP device check suite: GTX 1650 driver runs, route floors and device lists

**Status:** evidence; used by [P1F3](P1F3-hardware-probe-devices-and-multi-gpu.md), 2026-11-12 (GTX 1650 runs of the hardware and EP track, 2026-11-03; PR: pending).

## Decision

1. **What ran.** The EP device check suite ran quick runs (L2 registration and L3 probe, fp32 and
   fp16, 20 runs) on a GTX 1650 with five drivers: 566.36 (R565), 572.16 (R570), 576.88 (R575),
   580.88 (R580) and 621.01 (R620). Each run had five routes: `cpu`, `cuda-cu13`, `cuda-cu12`,
   `trt-rtx-cu13` and `trt-rtx-cu12`. The runs have no L4 (real model) results and no timings.
2. **`cpu`.** It passed on each driver.
3. **`cuda-cu13`.** Below R580, the plugin registers and lists no device at L2. There is no crash
   and no silent CPU fallback. On 580.88 and 621.01 it passes L2 and L3 (L3 largest difference
   2.86e-6 from the CPU EP).
4. **`cuda-cu12`.** It passes L2 and L3 on each driver, also on 566.36, below the old R570 floor.
   This result set its floor to R525, the minimum of CUDA 12.x minor version compatibility.
5. **TensorRT RTX.** Both routes register and list no device on each driver, also on R580 and
   newer. This result set the floor of the suite to CC 8.0. The TensorRT RTX 0.5.0 factory lists a
   device only for CC 8.6, 8.9 and 12.0 or higher ([ADR-NZK1](NZK1-ep-options-evidence.md) item 4).
6. **Verdict key.** After each driver change, the field `driver_version` of the verdict key of each
   route changed.
7. **Rules table of the reports.** The reports came from the rules table before these results:
   scenario A was below R570, and `trt-rtx-cu13` on CC 7.5 was `experimental` in scenario C. Thus
   the 566.36 report has one finding: `cuda-cu12` predicted `update-driver`, observed pass. The
   tracked `run_checks.py` holds the floors of items 4 and 5.
8. **History under [ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md).** v2 has CUDA 13
   plugin packs only, and no NVIDIA GPU older than Turing. Thus these parts of the suite are history:
   the `cuda-cu12` and `trt-rtx-cu12` routes, the R525 floor and the other CUDA 12 floors, and the
   Pascal (CC 6.1) part. No Pascal run was done. The runs used CPython 3.12.13, not the v2 Python
   3.13.18. Items 3 and 5 are facts of the same pack versions. No run tested them on 3.13.18.
9. **Suite versions.** The suite files do not change. A later suite version, for example one with
   CUDA 13 routes only on Python 3.13.18, gets its own entry.

## Reason

- [ADR-2XW6](2XW6-process-entries-consolidation.md) item 1: a script made the evidence for an entry, and that
  entry names it. No entry named this suite.
- The driver floors and the device lists of the EP catalog need measured facts for Turing.

## Evidence

- Host: GTX 1650 (Turing, CC 7.5, 4 GB, PCI `10de:1f91`), Windows 11 build 10.0.26300, CPython
  3.12.13. Each route also has `onnxruntime` 1.31.0 and `numpy` 2.5.4.
- Packs (exact pins): `onnxruntime-ep-cuda13` 0.3.0 with `nvidia-cublas` 13.8.0.4 and
  `nvidia-cudnn-cu13` 9.27.0.42; `onnxruntime-ep-cuda12` 0.3.0 with `nvidia-cublas-cu12` 12.9.2.10,
  `nvidia-cuda-runtime-cu12` 12.9.79 and `nvidia-cudnn-cu12` 9.27.0.42;
  `onnxruntime-ep-nv-tensorrt-rtx-cu13` 0.5.0; `onnxruntime-ep-nv-tensorrt-rtx-cu12` 0.5.0.
- Method: each route has its own uv environment and its own processes. L2 registers the plugin with
  `register_execution_provider_library` and finds the device in `get_ep_devices()` by EP name and
  NVIDIA vendor id. L3 runs a Conv and Relu model (1x3x64x64, opset 17) with
  `session.disable_cpu_ep_fallback=1` and compares the output with the CPU EP. Each run used
  `--redact-check`.
- Scripts in [`decisions/scripts/ep_device_checks/`](../scripts/ep_device_checks/README.md):
  `run_checks.py` (rules table, plan, environments, report, `compare`; standard library only),
  `route_check.py` (one L2, L3 or L4 job in the environment of a route), `prep_assets.py` (probe
  model, inputs, CPU references, fp16 copies) and `test_commands.txt` (the five commands). Test:
  [`test_ep_device_checks.py`](../scripts/tests/test_ep_device_checks.py) (the rules table with fake
  GPU facts, and `compare`).
- Reports: [`reports/gtx-1650/`](../scripts/ep_device_checks/reports/gtx-1650/), one folder for each
  driver with `report.json` and `report.md`.
- The same suite made the RTX 3070 TF32 reports of [ADR-NZK1](NZK1-ep-options-evidence.md).
