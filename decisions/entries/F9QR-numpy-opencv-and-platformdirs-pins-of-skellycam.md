# F9QR — The pins of `numpy`, `opencv-contrib-python` and `platformdirs` move to the versions of skellycam

**Status:** done, 2026-11-19 (user; PR: pending).

## Decision

1. `pyproject.toml` pins `numpy==2.5.5` (before: 2.4.6), `opencv-contrib-python==5.1.0.95` (before:
   5.0.0.93) and `platformdirs==4.14.7` (before: 4.14.5). `uv.lock` follows.
2. The static check of `tools/intake_bundle.py` refuses two more OpenCV names in `CV2_FILE_PREFIX`:
   `XFeat` and the module `viz3d`.

## Reason

- User, 2026-11-19: "bump any dependencies you need to match skellycam - looks like opencv and numpy".
  freemocap installs skellycam and skellytracker in one environment, and each of them pins exactly
  ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 1). Two different exact pins of
  one package do not resolve.
- The skellycam session gave its pins on 2026-11-19, from its branch `dom/native-jpeg`: Python
  3.13.18, `numpy` 2.5.5, `opencv-contrib-python` 5.1.0.95. Its lock resolves `platformdirs` to
  4.14.7. Each other package that the two projects share already had the same version.
- Item 2: `test_no_unreviewed_cv2_name_takes_a_path_or_a_model` failed on OpenCV 5.1.0 with four new
  names. `XFeat_create(modelPath, ...)`, `XFeat_createFromMemory(bufferModel, ...)` and
  `XFeat.create(modelPath, ...)` load a model. `viz3d.setSun(win_name, ...)` is in a module that
  draws in a window. The check refuses such names.

## Consequences

- **macOS.** The macOS wheel of `opencv-contrib-python` 5.1.0.95 has the tag `macosx_15_0_arm64`. The
  wheel of 5.0.0.93 had `macosx_13_0_arm64`. An install on macOS 13 or 14 thus finds no wheel.
- `platformdirs` is not a direct dependency of skellycam. Its version there can change with a new
  lock of skellycam.
- The older entries and records keep the versions of their measurements.

## Evidence

- `uv lock` resolves the three environments of `[tool.uv]` with the new pins (2026-11-19).
- The wheel tags are from `uv.lock` before and after the change.
- `tools/run_checks.py` on one Windows host with the new pins, 2026-11-19: exit 0. The doc tests gave
  3419 passed and 2 skipped, and the package tests gave 2186 passed and 4 skipped, with no change of
  an expected value or of a vector file. Not run: the GPU tests, the video tests, and each test on
  Linux and macOS.
