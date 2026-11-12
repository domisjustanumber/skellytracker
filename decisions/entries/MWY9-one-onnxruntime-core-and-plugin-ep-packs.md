# MWY9 — Exact pins; one ONNX Runtime 1.31 core with plugin EP packs; CUDA 13 only; Python 3.11 to 3.13, MediaPipe 1.2.2, no Intel Mac

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-B4QR](B4QR-exact-pins-and-cuda-13.md) in full. Items 1, 4, 5, 6 and 8
restate B4QR items 1, 3, 4, 5 and 7. Items 2, 3 and 7 replace B4QR items 2 and 6.

1. **Exact pins.** Each dependency of `pyproject.toml`, in `dependencies` and in each extra, has an
   exact pin (`==`). An environment marker limits a pin to a platform when the platform needs it.
   `uv.lock` holds the versions of the other packages. freemocap and each exporter use the same
   versions.
2. **One ONNX Runtime core.** `onnxruntime` with one exact 1.31 release is a base dependency, not an
   extra. `pip install skellytracker` and a plain `uv sync` give the CPU core. These go: the extras
   `onnx-cpu`, `onnx-cuda`, `onnx-trt` and `onnx-directml`, the `all-*` and `recommended-*` extras
   that name them, and the packages `onnxruntime-gpu`, `onnxruntime-directml`, `tensorrt` and
   `nvidia-*-cu12`.
3. **GPU EPs are plugin packs.** A GPU EP comes only as a plugin EP pack in the user EP store. The
   EP tool `skellytracker-eps install` installs it. It is never a dependency in `pyproject.toml`.
   v2 has the packs `cuda` (`onnxruntime-ep-cuda13`) and `trt-rtx`
   (`onnxruntime-ep-nv-tensorrt-rtx-cu13`). The EP catalog in `core/eps/` pins each pack version
   and the sha256 of each wheel. The packs use CUDA 13 only: there is no CUDA 12 pack, and NVIDIA
   GPUs older than Turing are not supported. Classic TensorRT and DirectML are not in v2.
4. **Python.** v2.0.0 supports Python 3.11, 3.12 and 3.13: `requires-python = ">=3.11,<3.14"`.
   CI runs 3.13.
5. **MediaPipe.** The `mediapipe` extra is `mediapipe==1.2.2`.
6. **Intel Mac.** macOS on x86_64 is not supported. The uv environment for macOS is
   `sys_platform == 'darwin' and platform_machine == 'arm64'`, with `required-environments`, so that
   a missing wheel fails at lock time. The README says so.
7. **When.** The dependency stage is the first stage of phase 1
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md)). It does items 1, 2, 4, 5 and 6. Each
   item is one commit group.
   - In the commit group of item 2, the old ONNX detectors become CPU only. The commit group removes
     the TensorRT, DirectML and CUDA library loading paths of the old `core/sessions/` code, because
     no environment can use them.
   - The gate of the MediaPipe change is the MediaPipe tests. A change of their expected values goes
     in one commit, before a parity baseline.
   - The gate of the Python change is the full suite on 3.13, with no hang in the MediaPipe tests.
   - Item 3 is in the hardware and EP stage. Its gate is a local run on an NVIDIA host:
     `eps.build_session()` builds a session on the `cuda` pack and on the `trt-rtx` pack, and the
     node assignment shows each session on the requested EP, not a fallback to the CPU.
8. **Timestamps.** The fix of the timestamp fallback of the MediaPipe detectors stays, for 3.11 and
   3.12.

## Reason

- The user selected the plugin packs over the GPU extras of B4QR item 2 on 2026-11-12. The user
  also accepted the method of the hardware and EP track: one plain ONNX Runtime core, plugin EP
  packs, a user EP store outside the environment and the app, and the session build in `core/eps/`.
- One core gives each user the same ONNX Runtime build, on the CPU and on a GPU. This is the reason
  of B4QR item 2. One core meets it with no second ONNX Runtime package.
- The TensorRT RTX plugin EP is the fastest EP measured (Evidence). It builds the re-exported
  `yolox-person` and `rtmw-wholebody133` models with no node on the CPU. Classic TensorRT needs a
  separate `tensorrt` package and the `onnxruntime-gpu` build.
- A plugin pack installs at run time, also in a frozen app.
- The user, for B4QR: "Pinned means exact pins and I'll need to go fix freemocap to match." and
  "Bump to ORT 1.31 and CUDA 13". Items 1 and 4 to 6 keep the reasons of B4QR.

## Consequences

- The old ONNX detectors run on the CPU from the dependency stage until their deletion. No release
  between the dependency stage and v2.0.0 runs the old detectors on a GPU.
- freemocap gets GPU inference only through the pipeline API and `eps`, as part of its move to v2.
- A GPU user runs one more command after the install: `skellytracker-eps install`.
- A GPU older than Turing (for example Pascal) uses the CPU. The EP tool offers a driver update when
  a newer driver supports the GPU.
- The exporters that build the RTMPose replacements use the pins of the pre-release and the packs of
  its EP catalog.

## Evidence

- Measured on 2026-11-12 on an RTX 3070 (CC 8.6, driver 610.88, Windows 11) with `onnxruntime`
  1.31.0, `onnxruntime-ep-cuda13` 0.3.0 and `onnxruntime-ep-nv-tensorrt-rtx-cu13` 0.5.0. fp32 and
  fp16, batch 1 and 3, the median of 30 runs, the node assignment from
  `get_provider_graph_assignment_info()`:
  - `yolox-person-m` b3 fp16: TensorRT RTX 9.2 ms, CUDA 18.4 ms. `rtmw-wholebody133-x-384` b3 fp16:
    TensorRT RTX 8.7 ms, CUDA 17.2 ms. TensorRT RTX put no node on the CPU EP for each artifact.
  - The CUDA plugin put no node on the CPU EP for the fp32 artifacts, and 3 `Clip` nodes for the
    fp16 RTMW artifact.
- The evidence of B4QR for `onnxruntime-gpu` 1.31.1 and `tensorrt` 11.4.0.106 (PyPI JSON API,
  2026-11-12).

## Alternatives rejected

- **The GPU extras of B4QR item 2** (`onnxruntime-gpu` with CUDA 13, and a `tensorrt` extra). They
  give two ONNX Runtime packages that must not be in one environment, no TensorRT RTX, and no GPU
  install in a frozen app.
- **The GPU extras until the hardware and EP stage, then the packs.** Two packaging changes in one
  release cycle.
- **`onnxruntime` in an optional extra.** A plain install then cannot run the v2 ONNX built-ins.
- **CUDA 12 packs for Pascal.** B4QR moved v2 to CUDA 13.

## Open work

See [open-work.md](../open-work.md).
