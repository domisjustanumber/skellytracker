# M2C6 — Exact pins, also for Python; one ONNX Runtime core and plugin EP packs

**Status:** accepted, 2026-11-12 (user).

## Decision

This entry supersedes [ADR-MWY9](MWY9-one-onnxruntime-core-and-plugin-ep-packs.md) in full. It
keeps the item numbers of MWY9. Items 1 to 3 and 5 to 7 restate MWY9 items 1 to 3 and 5 to 7. Item 4
replaces MWY9 item 4. Item 8 restates MWY9 item 8 for one Python. MWY9 keeps the reasons and the
evidence of the items that stay.

1. **Exact pins.** Each dependency of `pyproject.toml`, in `dependencies` and in each extra, has an
   exact pin (`==`), with no range. An environment marker limits a pin to a platform when the
   platform needs it. `uv.lock` holds the versions of the other packages. freemocap and each
   exporter use the same versions.
2. **One ONNX Runtime core.** `onnxruntime` with one exact 1.31 release is a base dependency, not an
   extra. These go: the extras `onnx-cpu`, `onnx-cuda`, `onnx-trt` and `onnx-directml`, the `all-*`
   and `recommended-*` extras that name them, and the packages `onnxruntime-gpu`,
   `onnxruntime-directml`, `tensorrt` and `nvidia-*-cu12`.
3. **GPU EPs are plugin packs.** A GPU EP comes only as a plugin EP pack in the user EP store, which
   `skellytracker-eps install` installs. It is never a dependency in `pyproject.toml`. v2 has the
   packs `cuda` (`onnxruntime-ep-cuda13`) and `trt-rtx` (`onnxruntime-ep-nv-tensorrt-rtx-cu13`). The
   EP catalog in `core/eps/` pins each pack version and the sha256 of each wheel. The packs use
   CUDA 13 only. NVIDIA GPUs older than Turing are not supported. Classic TensorRT and DirectML are
   not in v2.
4. **Python.** v2.0.0 supports one Python release: 3.13.18. `requires-python = "==3.13.18"`, and
   `.python-version` holds `3.13.18`. CI runs 3.13.18. freemocap and each exporter use the same
   Python. A new Python patch release needs a new skellytracker release.
5. **MediaPipe.** The `mediapipe` extra is `mediapipe==1.2.2`.
6. **Intel Mac.** macOS on x86_64 is not supported. The uv environment for macOS is
   `sys_platform == 'darwin' and platform_machine == 'arm64'`, with `required-environments`, so that
   a missing wheel fails at lock time. The README says so.
7. **When.** The dependency stage is the first stage of phase 1
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md)). It does items 1, 2, 4, 5 and 6. Each
   item is one commit group.
   - In the commit group of item 2, the old ONNX detectors become CPU only. The commit group removes
     the TensorRT, DirectML and CUDA library loading paths of the old `core/sessions/` code.
   - The gate of the MediaPipe change is the MediaPipe tests. A change of their expected values goes
     in one commit, before a parity baseline.
   - The gate of the Python change is the full suite on 3.13.18, with no hang in the MediaPipe
     tests. Each dependency must have a wheel for 3.13 on each supported platform.
   - Item 3 is in the hardware and EP stage. Its gate is a local run on an NVIDIA host:
     `eps.build_session()` builds a session on the `cuda` pack and on the `trt-rtx` pack, and the
     node assignment shows each session on the requested EP, not a fallback to the CPU.
8. **Timestamps.** The fix of the timestamp fallback of the MediaPipe detectors stays
   ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md) item 9). No supported Python has the
   coarse Windows clock of 3.11 and 3.12, so the fix is a guard.

## Reason

- The user, on 2026-11-12: "all dependencies must be exact pins, no ranges." The user then chose
  that this rule covers Python, with an exact patch release, not a minor release with any patch.
- One exact Python gives each environment the same interpreter, as item 1 gives the same packages.
- 3.13.18 is the newest 3.13 release that uv 0.13.7 lists on 2026-11-12. 3.13 is the newest minor
  release of the range of MWY9, and CI already ran it.

## Consequences

- freemocap must move to Python 3.13.18 before it moves to v2.
- Each Python security patch needs a skellytracker release, and freemocap and each exporter move
  with it.
- An exporter on Python 3.14 moves down to 3.13.18 when it pins the pre-release. On 2026-10-28,
  two exporters required Python 3.14 or later ([open work](../open-work.md)).
- A wheel built for 3.13 serves each 3.13 patch release, so item 4 changes no package pin.

## Alternatives rejected

- **The range of MWY9, `>=3.11,<3.14`.** It is a range.
- **One minor release, `==3.13.*`.** The user chose an exact patch release.
