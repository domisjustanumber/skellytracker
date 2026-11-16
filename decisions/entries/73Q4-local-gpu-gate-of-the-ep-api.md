# 73Q4 — Local GPU gate of the hardware and EP API on an RTX 3070

**Status:** evidence, 2026-11-16 (measurement of stage 1.3 of the implementation plan; PR: pending).

## Decision

1. **What ran.** The local GPU gate of stage 1.3 ran on the Windows test host:
   `uv run pytest -m "gpu and not pyinstaller" skellytracker/tests/test_eps_gpu_gate.py` and
   `uv run pytest -m "gpu and pyinstaller" skellytracker/tests/test_eps_gpu_gate.py`. The EP store
   held the packs `cuda-cu13` 0.3.0 and `trt-rtx-cu13` 0.5.0, installed with `install()` from the
   wheels of `ep_lock.yaml`.
2. **L3.** The trial session passes for `cuda` and for `trt-rtx`. The largest difference from the
   CPU EP on the probe model is 9.5e-7 for `cuda` and 5.25e-3 for `trt-rtx`. The limit `l3_atol` of
   the catalog is 1.5e-2 for each. With probe weights of standard deviation 1.0, the `trt-rtx`
   difference was 2.1e-2. Thus the probe model has weights of standard deviation 0.25.
3. **Session build.** `eps.build_session()` builds a session on each pack, with no `device_key` and
   with the device key of the one GPU (`gpu:10de:2484:0`). The first provider is the requested EP.
   Each node of the probe model is on the requested EP. `run_devices()` gives that one GPU for each
   pack.
4. **fp16 placement, `trt-rtx`.** Each of the 55 local fp16 files of `yolox-person` (30) and
   `rtmw-wholebody133` (25) has 0 nodes on the CPU EP.
5. **fp16 placement, `cuda`.** 50 of the 55 files have 0 nodes on the CPU EP, with the option
   `prefer_nhwc=1`. The 5 files `rtmw-wholebody133-<size>_b4_fp16.onnx` have 3 `Clip` nodes on the
   CPU EP. These 5 files have opset 11 and the date 2026-11-04. The 20 other `rtmw-wholebody133`
   files have opset 17 and the date 2026-11-12, and they have 0 nodes on the CPU EP. The 5 files are
   the known defect of the first export
   ([ADR-9NW0](9NW0-ep-keys-options-and-failures.md), Evidence). The re-export did not replace them
   in the local export folder.
6. **Frozen application.** A PyInstaller onedir application installed `trt-rtx` into a new store
   with a download from PyPI, passed the verification in its child process and built a session. The
   first provider of the session was `NvTensorRTRTXExecutionProvider`.
7. **Registration time.** In a new process, the first registration took 3.3 s for `cuda` and 1.0 s
   for `trt-rtx`. `install()` from a local folder took 8.0 s for the two packs.
8. **Device facts.** ONNX Runtime gives the LUID of the GPU in the metadata of each EP device. It
   is equal to the LUID of `probe_host()`. The `cuda` EP device has the EP option `device_id`. The
   `trt-rtx` EP device has no such option.

## Reason

- Step 17 of stage 1.3 needs an evidence entry for the local GPU gate
  ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 7).
- [ADR-EY4F](EY4F-acceptance-gate-checks-fp16-gpu-placement.md) needs the CPU node count of each
  fp16 file. Item 5 shows that `SessionReport.cpu_nodes` and `cpu_op_types` find the defect.

## Evidence

- Host: NVIDIA RTX 3070 (CC 8.6, 8 GB), driver 610.88, Windows 11 build 26300, CPython 3.13.18,
  `onnxruntime` 1.31.1, PyInstaller 6.22.3.
- Test: [`test_eps_gpu_gate.py`](../../skellytracker/tests/test_eps_gpu_gate.py). Result of the
  first command: 4 passed, 1 failed (item 5). Result of the second command: 1 passed.
- Models: the folder `exports/` of a local checkout of OpenMMLab-Exporter. The checkout had no
  commit for these files, so no permalink is given.
- Not measured: a host with two GPUs, a GPU with CC 7.5 on Python 3.13.18, Linux, and macOS.
