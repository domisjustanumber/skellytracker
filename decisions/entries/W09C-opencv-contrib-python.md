# W09C — `opencv-contrib-python` is the OpenCV package

**Status:** accepted, 2026-11-12 (user).

## Decision

1. The OpenCV dependency of skellytracker is `opencv-contrib-python`, with an exact pin
   ([ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md) item 1).
2. skellytracker does not use a headless OpenCV package (`opencv-python-headless` or
   `opencv-contrib-python-headless`).
3. `exclude-dependencies = ["opencv-python"]` in `[tool.uv]` of `pyproject.toml` stays.

## Reason

- The `mediapipe` extra installs `opencv-contrib-python` in all cases. `mediapipe` 0.10.33 and
  1.2.2 require it. With a headless pin, an install with the `mediapipe` extra holds two OpenCV
  packages. Both write the `cv2` module, and one overwrites the files of the other.
- freemocap and skellycam use `opencv-contrib-python`. One package gives one `cv2` in their
  environments.
- The webcam demo (`python -m skellytracker`) calls `cv2.namedWindow` and `cv2.imshow`. A headless
  package does not have them.

## Evidence

- The `cv2.aruco` symbols of the package (`ArucoDetector`, `CharucoDetector`, `CharucoBoard`,
  `getPredefinedDictionary`, `DetectorParameters`, `Dictionary`, `generateImageMarker`) are in the
  main OpenCV build from 4.7. They do not need contrib. Checked with `opencv-contrib-python`
  4.13.0.92 and 5.0.0.93 on 2026-11-12.
- The checks of `tools/run_checks.py` pass with `opencv-contrib-python` 5.0.0.93, with no change of
  expected values (2026-11-12).
- Only `skellytracker/core/io/demo_manager.py` calls the OpenCV GUI functions.
- The `requires_dist` of `mediapipe` 1.2.2 on PyPI names `opencv-contrib-python`, read on
  2026-11-12.

## Alternatives rejected

- **A headless package.** It is smaller and has no GUI libraries. It does not remove
  `opencv-contrib-python` from an install with the `mediapipe` extra, and it breaks the webcam
  demo.
