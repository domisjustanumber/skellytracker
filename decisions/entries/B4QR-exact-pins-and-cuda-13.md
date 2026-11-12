# B4QR — Exact dependency pins; ONNX Runtime 1.31 with CUDA 13; Python 3.11 to 3.13, MediaPipe 1.2.2, no Intel Mac

**Status:** superseded by [MWY9](MWY9-one-onnxruntime-core-and-plugin-ep-packs.md), 2026-11-12 (user; PR: pending).

## Decision

This entry supersedes [ADR-MSH0](MSH0-supported-platforms-v2.md) in full. Items 3, 4, 5 and 7
restate MSH0 items 1, 2, 3 and 5. Items 1, 2 and 6 are new. Item 6 replaces MSH0 item 4.

1. **Exact pins.** Each dependency of `pyproject.toml`, in `dependencies` and in each extra, has an
   exact pin (`==`). An environment marker limits a pin to a platform when the platform needs it.
   `uv.lock` holds the versions of the other packages. freemocap and each exporter use the same
   versions.
2. **ONNX Runtime and CUDA.** The CPU extra and the GPU extras pin the same ONNX Runtime 1.31
   release. The GPU extras use `onnxruntime-gpu` with CUDA 13 and the cuDNN 9 build for CUDA 13.
   The cap `onnxruntime-gpu<1.27` and the CUDA 12 packages go. The TensorRT extra pins the TensorRT
   release that the TensorRT EP of that ONNX Runtime release loads. The dependency stage finds that
   release before it writes the pin.
3. **Python.** v2.0.0 supports Python 3.11, 3.12 and 3.13: `requires-python = ">=3.11,<3.14"`.
   CI runs 3.13.
4. **MediaPipe.** The `mediapipe` extra is `mediapipe==1.2.2`.
5. **Intel Mac.** macOS on x86_64 is not supported. The uv environment for macOS is
   `sys_platform == 'darwin' and platform_machine == 'arm64'`, with `required-environments`, so that
   a missing wheel fails at lock time. The README says so.
6. **When.** The dependency stage is the first stage of phase 1
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md)). The pins, ONNX Runtime with CUDA,
   Python, MediaPipe and Intel Mac are each one commit group. The gate of the MediaPipe change is the
   MediaPipe tests. A change of their expected values goes in one commit, before a parity baseline.
   The gate of the Python change is the full suite on 3.13, with no hang in the MediaPipe tests. The
   gate of the CUDA change is a local run on an NVIDIA host that shows that the session uses the CUDA
   EP, not a fallback to the CPU.
7. **Timestamps.** The fix of the timestamp fallback of the MediaPipe detectors stays, for 3.11 and
   3.12.

## Reason

- The user, in words: "Pinned means exact pins and I'll need to go fix freemocap to match." and
  "Bump to ORT 1.31 and CUDA 13".
- An exporter runs a pinned skellytracker release as its ONNX host
  ([ADR-6J8E](6J8E-exporters-run-released-skellytracker.md)). With the same versions, the parity run
  of the exporter and the package run give the same numbers.
- Today the CPU extra has ONNX Runtime 1.31 and the GPU extras have 1.26 or older. A GPU user thus
  runs a different ONNX Runtime than the CPU check of
  [ADR-4KW6](4KW6-onnxruntime-1-31-for-the-cpu-check.md).
- ONNX Runtime 1.27 and later on PyPI use CUDA 13. The cap kept the GPU extras on CUDA 12.
- Items 3 to 5 and 7 keep the reasons of MSH0: on Python 3.13 the MediaPipe tests do not hang;
  MediaPipe 1.2.2 changes no test result; MediaPipe and ONNX Runtime have no Intel Mac wheel.

## Consequences

- CUDA 13 does not support NVIDIA GPUs older than Turing, and it needs a newer driver.
- freemocap pins `mediapipe==0.10.33` in a uv override. The user changes freemocap to the pins of
  this entry.
- An exporter with `requires-python >=3.14` cannot take skellytracker as a dependency. The exporters
  that agents build again use the pins of the pre-release.
- Each change of a dependency version is a change of the pins, and thus of the release that the
  exporters pin.
- The `hw-and-ep-work` branch sets CUDA 12 floors and plans a Pascal test. Its plan changes to
  CUDA 13 when it merges.

## Evidence

- PyPI JSON API, 2026-11-12: `onnxruntime-gpu` 1.31.1 is the latest release. Its extra `cuda` needs
  `nvidia-cuda-runtime~=13.0` and `nvidia-cuda-nvrtc~=13.0`. Its extra `cudnn` needs
  `nvidia-cudnn-cu13~=9.0`. It has wheels for CPython 3.11 to 3.14 on Linux x86_64 and aarch64 and
  on Windows x86_64, and none for macOS. `tensorrt` 11.4.0.106 is the latest release and needs
  `tensorrt_cu13`.
- `pyproject.toml` on 2026-11-12: `onnx-cpu` has `onnxruntime>=1.31`. `onnx-cuda` and `onnx-trt`
  have `onnxruntime-gpu<1.27` with the `-cu12` packages, and `tensorrt>=10,<11`.
  `opencv-contrib-python`, `onnx`, `polars` and `scipy` have no version.
- The evidence of items 3 to 5 and 7 is the Evidence of [ADR-MSH0](MSH0-supported-platforms-v2.md).

## Alternatives rejected

- **Version ranges in `pyproject.toml` and exact versions only in `uv.lock`.** A consumer does not
  get the lock. The user selected exact pins.
- **Stay on CUDA 12 with `onnxruntime-gpu<1.27`.** GPU users then run a different ONNX Runtime than
  the CPU check.

## Open work

See [open-work.md](../open-work.md).
