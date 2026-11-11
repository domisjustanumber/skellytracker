# MSH0 — Supported platforms of v2.0.0: Python 3.11 to 3.13, MediaPipe 1.2.2, no Intel Mac

**Status:** accepted, 2026-11-11 (user).

## Decision

1. **Python.** v2.0.0 supports Python 3.11, 3.12 and 3.13: `requires-python = ">=3.11,<3.14"`.
   CI runs 3.13.
2. **MediaPipe.** The `mediapipe` extra moves from 0.10.33 to 1.2.2.
3. **Intel Mac.** macOS on x86_64 is not supported. The uv environment for macOS becomes
   `sys_platform == 'darwin' and platform_machine == 'arm64'`, with `required-environments`, so that
   a missing wheel fails at lock time and not at install time. The README says so.
4. **When.** Each change is its own commit group in the layout stage of the implementation stage
   ([ADR-EM74](EM74-stage-order-and-ci-models.md)). The gate of the MediaPipe change is the
   MediaPipe tests. A change of their expected values goes in one commit, before a parity baseline.
   The gate of the Python change is the full suite on 3.13, with no hang in the MediaPipe tests.
5. **Timestamps.** The fix of the timestamp fallback of the MediaPipe detectors stays, for 3.11 and
   3.12.

## Reason

- On Python 3.13 the MediaPipe tests do not hang (Evidence). skellybench needs Python 3.13 or later.
- MediaPipe 1.2.2 changes no test result and breaks no API that the package uses (Evidence).
- Intel Mac has no working install today. MediaPipe 0.10.30 and later and ONNX Runtime 1.24 and
  later have no Intel Mac wheel. The package already needs `onnxruntime>=1.31`. A MediaPipe fallback
  to 0.10.21 needs `numpy<2`, which conflicts with `numpy==2.4.6`. A MediaPipe maintainer wrote on
  2025-12-22 in google-ai-edge/mediapipe issue 6112: "On Mac, we only support arm64 going forward."
  Rosetta 2 runs x86_64 code on Apple silicon only, not arm64 code on Intel. Apple stated that macOS
  26 is the last release for Intel Macs. freemocap builds no Intel Mac installer.

## Consequences

- freemocap pins `mediapipe==0.10.33` in a uv override. An override wins over a requirement, so
  freemocap keeps 0.10.33 until it changes that pin.
- The range `<3.14` does not let an exporter with `requires-python >=3.14` take skellytracker as a
  dependency ([open-work.md](../open-work.md)).

## Evidence

- PyPI JSON API, 2026-11-11: each MediaPipe release from 0.10.30 to 1.2.2 has only `py3-none` wheels
  for `macosx_11_0_arm64`, `manylinux_2_28` x86_64 and aarch64, `win_amd64` and `win_arm64`. The last
  release with a macOS x86_64 wheel is 0.10.21 (2025-02-06, cp39 to cp312), which requires
  `numpy<2`. The last ONNX Runtime with a macOS x86_64 wheel is 1.23.2.
- Wheel contents, 2026-11-11: 0.10.21, 0.10.33 and 1.2.2 have
  `mediapipe/tasks/python/vision/holistic_landmarker.py`. 1.2.2 has no `mediapipe/python/solutions/`.
  The package code uses no `mp.solutions`.
- MediaPipe tests on Windows, 2026-11-11, with pytest 9.1.0 and uv 0.11.8 (plain
  `python -m pytest <file> -o faulthandler_timeout=300` runs; no script). Each test file that uses
  MediaPipe ran 3 times in each environment. The project environment was Python 3.12.13 with MediaPipe 0.10.33. Scratch
  environments had 3.12.13 with 1.2.2 (from `uv sync --frozen`), and 3.13.13 with 1.2.2 and with
  0.10.33 (from a freeze of the project environment, because `requires-python` excludes 3.13).
  - On 3.12, 1.2.2 gives the same result as 0.10.33 in each file, with the same warnings.
    `test_mediapipe_detectors.py` takes about 4 to 7 s on 1.2.2 and about 1.8 s on 0.10.33.
  - On 3.12, each failure is `ValueError: Input timestamp must be monotonically increasing`. There
    were 16 hangs, each at exit in a run with that error. py-spy shows `gc_collect_harder` →
    `PoseLandmarker.__del__` → `close()` → a MediaPipe dispatcher future that does not complete.
  - On 3.13, each test passes on both MediaPipe versions, with no hang.
  - `time.monotonic()` uses `GetTickCount64()` on 3.12 (steps of 15.625 ms) and
    `QueryPerformanceCounter()` on 3.13. The detectors make the timestamp from
    `int(time.monotonic() * 1000)`.
- The 3.13 environments came from a freeze, not from `uv.lock`. A lock on 3.13 for each platform is
  not checked yet.

## Alternatives rejected

- **A MediaPipe 0.10.21 fallback for Intel Mac by environment markers.** It needs `numpy<2`, and ONNX
  Runtime has no Intel Mac wheel either.
- **Exclude only MediaPipe on Intel Mac.** ONNX Runtime is missing there too, so no detector works.
- **Build MediaPipe and ONNX Runtime from source for Intel Mac.** Several hours for each release,
  with no upstream CI.
- **Stay on Python `<3.13`.** The timer hang stays on each supported version.
- **Python 3.13 only.** It drops users on 3.11 and 3.12 with no need.

## Not repeated

- The Windows hang is a Python timer defect, not a MediaPipe defect. A MediaPipe version does not
  change it.

## Open work

See [open-work.md](../open-work.md).
