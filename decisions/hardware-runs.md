# Hardware runs

This file is the checklist of the runs that wait for hardware or for an OS that this project does
not have at hand. It is not on the read path: read it when you have such a system, or when your task
changes one of these runs. The other open work is in [open-work.md](open-work.md)
([ADR-8ACK](entries/8ACK-hardware-runs-checklist.md)).

- An open-work item that waits for such hardware is stated in full here. A link to the entry is not
  enough.
- Each run is a certify run in a freemocap build, and the person hands in the report file
  ([ADR-Q7VQ](entries/Q7VQ-certify-rulings-of-2026-11-20.md) item 1). An item marked
  **Measurement** is not a certify run: its result goes in an evidence entry.
- An item leaves this file when the reviewed report exists. Delete the item, and write the result in
  an entry.
- "Item N of the certification build list" names a numbered item of the
  [certification build list](open-work.md#certification-build-list). The item keeps its number
  there.

Sections 3 and 4 of the certify suite
([ADR-SP4Z](entries/SP4Z-certify-suite-calls-the-full-level.md)) ran on one Windows system with an
NVIDIA GPU and an Intel iGPU only. No run on Linux, on macOS (`coreml`), on a system with an AMD GPU
or on a laptop with two GPUs.

## AMD GPUs

The AMD EPs (item 11 of [ADR-Y14H](entries/Y14H-certify-suite.md)) are built
([ADR-XSE7](entries/XSE7-amd-eps-in-the-field-test.md)), and only tests with fakes prove them. The
field-test state and DirectML are built ([ADR-Z5X7](entries/Z5X7-field-test-state-and-directml.md)).
No EP has a result on an AMD GPU yet. A reviewed passing report for the OS moves an EP to `ready`,
and changes the note of its hardware class (`amd-windows` or `amd-linux`).

### An AMD GPU on Windows

- [ ] Windows with an AMD GPU: the EPs that the catalog offers for the GPU
  (`AMDGPUExecutionProvider` needs Windows ML 2.5.96 and an AMD driver 24.12.1 or later),
  `ensure_ready()` of a package that is on the system and of a package that is not, `library_path`,
  the registration, the EP device of the GPU, and the removal at the end.
- [ ] The removal of an AMD package that the suite installs (item 5 of
  [ADR-XSE7](entries/XSE7-amd-eps-in-the-field-test.md)). The command that removes a package that
  `install KEY --field-test` installed is item 4 of the certification build list.
- [ ] Item 4 of the certification build list: `install()` and `remove()` with a catalog key of an
  AMD EP did not run.
- [ ] **DirectML GPU preprocess.** A reviewed report from an AMD GPU on Windows moves `directml`
  into `GRAPH_DEFAULT_EPS`
  ([ADR-W4NW](entries/W4NW-gpu-preprocess-of-a-model-node-and-its-cpu-warning.md) items 1 and 6).
  The report must show no `fail` in `preprocess_graph_amd_ep.*` and `pipeline_amd_ep.*` of
  `run_jpeg_certification("directml")`, the numbers of `frame_upload` and `gpu_vs_cpu_preprocess`,
  and the time of the span `person.preprocess` with `gpu` and with `cpu`.

### An AMD GPU on Linux with ROCm

- [ ] Linux with an AMD GPU and ROCm 10.0, 10.1 or 10.2: the pack choice, the install, the
  registration with the RUNPATH of 10.1 and 10.2, the preload of 10.0 (the second ONNX Runtime
  core), the probe on ONNX Runtime 1.30.0, and the second environment on 1.29.0 (`uv export`, the
  install in hash-checking mode, the editable install with the build constraint, the child run, the
  sizes). A system with no ROCm: `rocm-missing` and the CPU only.
- [ ] **Measurement.** AMD JPEG decode with rocJPEG: the measurement before a build of the research
  note [gpu-jpeg-decode-amd-rocjpeg.md](../research/gpu-jpeg-decode-amd-rocjpeg.md).

## Linux with an NVIDIA GPU

- [ ] **Linux gate of ONNX Runtime 1.30.0.** [ADR-N6E8](entries/N6E8-onnxruntime-1-30-on-each-os.md)
  item 9: run the level `full` of certify in a freemocap build on bare-metal Ubuntu 24.04 with an
  NVIDIA driver of 590.48.01 or later. Linux is tested only through the certify process, not with a
  run of the certify suite in a clone
  ([ADR-4JAW](entries/4JAW-rulings-of-2026-11-23-on-sessions-the-certify-prompt-and-linux.md) item 4).
  The change of the items 2 and 3 of N6E8 lands
  only after this run passes. Then write the result in the Evidence section of N6E8.
- [ ] **EP certification** ([ADR-MF2R](entries/MF2R-ep-store-install-and-certification.md)): write
  the `maintainer` rows of `ep_evidence.yaml` for the current set hash on Linux. The two Windows rows
  are written. Until then, `tools/onnx_stack.py check` fails for each NVIDIA pack on Linux (item 18
  of MF2R).
- [ ] **ONNX Runtime telemetry**
  ([ADR-BZ7X](entries/BZ7X-onnx-runtime-telemetry-switch-and-scan.md)): the Ubuntu run of the
  certify suite must record the telemetry folder and the exit time, with and without the variable of
  the switch. Then write `switch_verified` in the two Linux rows of `ep_evidence.yaml`. The Linux
  folder path is read from strings, not measured.
- [ ] Item 1 of the certification build list: a run of the level `full` on Linux and on macOS. One
  Windows system ran it for `trt-rtx`, `cuda` and `directml` on an RTX 3070 and for `directml` on a
  UHD 770: each EP check passed. Then calibrate its time estimates and the time estimates of the
  level `quick`.
- [ ] Item 2 of the certification build list: a run of the sections `packs` and `full` of
  `tools/certify_platform.py` on Linux and on macOS. One Windows system ran the four sections
  ([ADR-SP4Z](entries/SP4Z-certify-suite-calls-the-full-level.md)): 384 checks, no `fail`, 47 s for
  `packs` and 316 s for `full`.
- [ ] Item 5 of the certification build list: a run of the PyInstaller hook of ONNX Runtime on Linux
  and on macOS. The hook is built (`skellytracker/_pyinstaller/hook-onnxruntime.py`), and the freeze
  test ran on Windows only.
- [ ] **Measurement.** nvImageCodec hang of a one-image decode
  ([ADR-975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md)): a run on Linux.

## macOS (`coreml`)

- [ ] Item 3 of the certification build list: a run of the quick check of `coreml` on a Mac. No Mac
  ran it ([ADR-ER5X](entries/ER5X-check-rule-unclean-exits-and-coreml.md) item 6).
- [ ] Items 1, 2 and 5 of the certification build list on macOS: see
  [Linux with an NVIDIA GPU](#linux-with-an-nvidia-gpu).

## A laptop with two GPUs

- [ ] A run of sections 3 and 4 of the certify suite on a laptop with two GPUs.

## An Intel-only system

- [ ] **Measurement.** The timing of the yolox preprocess of
  [ADR-B5Z0](entries/B5Z0-yolox-preprocess-timing-on-an-intel-igpu-system.md) on a system with only
  an Intel iGPU (the open work of that entry).

## A system with an NVIDIA GPU and few CPU cores

- [ ] **Measurement.** nvImageCodec hang of a one-image decode
  ([ADR-975Z](entries/975Z-nvimagecodec-one-image-decode-hang.md)): a run on a system with few CPU
  cores.
