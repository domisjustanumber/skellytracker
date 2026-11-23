# N6E8 — ONNX Runtime 1.30.0 on each OS, with the Windows ML build on Windows

**Status:** absorbed into [Package: ONNX Runtime](../../skellytracker/AGENTS.md#onnx-runtime), [`tools/tests/test_dependency_pins.py`](../../tools/tests/test_dependency_pins.py), [`pyproject.toml`](../../pyproject.toml), [`tools/ep_catalog.py`](../../tools/ep_catalog.py), [`tools/onnx_stack.py`](../../tools/onnx_stack.py), [`core/eps/ep_catalog.yaml`](../../skellytracker/core/eps/ep_catalog.yaml), [`tests/test_mediapipe_landmarker_lifetime.py`](../../skellytracker/tests/test_mediapipe_landmarker_lifetime.py), 2026-11-23 (absorb pass of 2026-11-23; PR: pending). It was `accepted` from 2026-11-18 (user).

## Decision

This entry supersedes [ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) in full. It keeps
the item numbers of M2C6. Items 2 and 3 replace M2C6 items 2 and 3. Item 9 is new. M2C6 keeps the
reasons and the evidence of the items that stay.

1. **Exact pins.** Each dependency of `pyproject.toml` has an exact pin (`==`), with no range. An
   environment marker limits a pin to a platform. freemocap and each exporter use the same versions.
2. **One ONNX Runtime release on each OS.** ONNX Runtime 1.30.0 is a base dependency, not an extra.
   Linux and macOS have `onnxruntime==1.30.0`. Windows has
   `onnxruntime-windowsml==1.30.0.202609102321` and `windowsml[with-ort]==2.6.74rc0`. `ort_core` of
   the EP catalog holds the two distributions. `tools/ep_catalog.py --check` compares them with
   `pyproject.toml` and `uv.lock`, and the EP store compares the installed distribution with the
   catalog. The extras and packages that M2C6 item 2 removed stay removed.
3. **GPU EPs are plugin packs.** A GPU EP comes only as a plugin EP pack in the user EP store, or on
   Windows as a package of the Windows ML catalog ([ADR-XSE7](XSE7-amd-eps-in-the-field-test.md)). It
   is never a dependency in `pyproject.toml`. The EP catalog pins each pack version and the sha256 of
   each wheel. The packs use CUDA 13 only, with the same versions on each OS.
   - `cuda`: `onnxruntime-ep-cuda13==0.2.0`, `nvidia-cublas==13.8.0.4` and
     `nvidia-cudnn-cu13==9.27.0.42`. Linux also has `nvidia-cuda-runtime==13.4.92`. On Windows the
     NVIDIA driver gives the CUDA runtime.
   - `trt-rtx`: the PyPI wheel `onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0`, not the EP of the
     Windows ML catalog. On Linux the EP store loads `libcudart`, `libtensorrt_rtx` and
     `libtensorrt_onnxparser_rtx` of the wheel before the EP library. The driver floor is R580 on
     Windows and R590 on Linux.
   - No pack holds NVRTC. Classic TensorRT is a reserved key. `migraphx` is a field-test EP
     (XSE7). `directml` is not a pack: it is built in on Windows
     ([ADR-Z5X7](Z5X7-field-test-state-and-directml.md)).
4. **Python.** One release: 3.13.18, in `requires-python`, `.python-version` and CI.
5. **MediaPipe.** The `mediapipe` extra is `mediapipe==1.2.2`.
6. **Intel Mac.** macOS on x86_64 is not supported. `required-environments` fails the lock when a
   wheel is missing.
7. **When.** The gates of M2C6 item 7 stay.
8. **Timestamps.** The timestamp guard of the MediaPipe detectors stays
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md) item 9).
9. **Linux gate.** Items 2 and 3 land only after `scripts/n6e8_ort_1_30/linux_ep_gate.sh` passes on
   bare-metal Ubuntu 24.04 with an NVIDIA driver of 590.48.01 or later. WSL2 is not a valid host.

## Reason

- The user wants the same ONNX Runtime release and the same pack versions on Linux and on Windows,
  and a later route to AMD GPUs. On Windows that route is the Windows ML catalog, which needs the
  Windows ML build.
- On 2026-11-18, `onnxruntime` and `onnxruntime-windowsml` share only 1.23.2, 1.24.4, 1.27.0, 1.28.0
  and 1.30.0 (PyPI). `windowsml` 2.6.74rc0 pins the 1.30.0 build.
- The `trt-rtx` wheel is the same on each OS and has a pin. Windows updates the catalog EP.

## Consequences

- skellytracker moves down from 1.31.1. It does not have the fixes of 1.30.1 and 1.31.
- `windowsml` 2.6.74rc0 is a release candidate.
- The Windows ML build prints `Init provider bridge failed.` at each import of `onnxruntime`.
- The `trt-rtx` pack is no longer `untested-ort`: NVIDIA tested it with ONNX Runtime 1.30.
- The fp16 difference of [ADR-4KW6](4KW6-onnxruntime-1-31-for-the-cpu-check.md) is not measured on
  1.30.0. If check V5 fails at random, try a fixed thread count for that check first.
- No Linux host ran the preload lists before the gate of item 9.

## Evidence

Host: one RTX 3070 on Windows 11, NVIDIA driver 610.88, 2026-11-18.

- **TRT-RTX on the Windows ML build.** `scripts/n6e8_ort_1_30/trt_rtx_driver.py`: five package
  models, each with a new and a cached engine, on the Windows ML build and on `onnxruntime` 1.30.0.
  20 of 20 GPU runs pass, each node is on the EP, and the outputs of the two builds are
  bit-identical.
- **The wheel and the catalog EP.** The same run, with the catalog TRT-RTX package 2.30.51.0
  installed: ONNX Runtime lists no TRT-RTX device before the registration of the wheel and one
  device after it. Each TensorRT library of the process comes from the wheel.
- **CUDA on the Windows ML build.** A scratch run (not in git) with the `cuda` pack of item 3: 68 of
  68 GPU runs pass, with bit-identical outputs with and without NVRTC.
- **Linux link tables.** `scripts/n6e8_ort_1_30/sonames.py` (pyelftools): the CUDA EP library needs
  `libcudart.so.13`, and no wheel of the old pack holds it. The `trt-rtx` wheel holds the three
  libraries of item 3 under full version names, with the right SONAME. No EP library has a RUNPATH.
- **Tests on Windows.** `tools/tests` with the `eps`, `system` and import-rule tests: 3415 passed.
  The package tests without MediaPipe and video: 1576 passed, 4 skipped.
- **The fp16 difference is not determinable.** The procedure of the exporter note of ADR-4KW6 gives
  0 runs that differ in 496 repeats on a new environment with `onnxruntime` 1.27.0. The note gives 3
  of 100, on an environment that is not available. A count of 0 on 1.30.0 would thus prove nothing.
- **Linux gate.** Not run yet.

## Alternatives rejected

- **Stay on 1.31.1.** `onnxruntime-windowsml` has no 1.31 release.
- **`windowsml` 2.5.96, the stable release.** It pins ONNX Runtime 1.28.3. `onnxruntime` has none.
- **The catalog TRT-RTX EP on Windows.** It has no pin, and Linux has no catalog.
- **WSL2 as the Linux gate.** The `trt-rtx` wheel lists no device there.

## Open work

See [open-work.md](../open-work.md).
