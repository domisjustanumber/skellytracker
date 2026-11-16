"""The one public factory of the `detectors` entry point: from a catalog key to an object that detects.

    detector = create_detector("yolox-person@openmmlab-exporter", execution_provider="cpu")
    detector = create_detector("charuco@skellytracker", board={"squares_x": 7, "squares_y": 5, "square_length_mm": 58.0})
    keypoints = detector.detect(frame)
    detector.close()

`create_detector` uses the `category` of the catalog entry:

- `onnx`: it calls `skellytracker.core.detectors.generic.create_detector` with the same arguments,
  and it returns the same generic detector.
- `calibration`: it makes the calibration detector with its options. The options are plain values.
  The result has `detect(image)` and `close()`. `detect` takes one BGR or grey `uint8` image and
  returns a `Keypoints` (`names`, `xyz`, `visibility`). The names of charuco are the names
  `CharucoCorner-<i>` of each board corner, in order, then the names `ArucoMarkerCorner-<id>-<j>`.
  A point that is not found has NaN coordinates and the visibility 0.
- `mediapipe`: it raises `DetectorUnavailableError`. The pipeline node `mediapipe_tasks` runs
  MediaPipe.

The options of `charuco@skellytracker`:

- `board`: a `CharucoBoardDefinition` of `skellytracker.core.detectors.calibration`, or a mapping
  of its fields: the keys `squares_x`, `squares_y` and `square_length_mm`, and the optional keys
  `marker_length_ratio` (default 0.8) and `aruco_dictionary_enum` (an OpenCV dictionary number,
  default `cv2.aruco.DICT_4X4_250`). The model checks a mapping. With no `board`, the board is
  the 5x3 board with 54 mm squares. `detector.board` is the `CharucoBoardDefinition` of the
  detector.

The options of `aruco@skellytracker`:

- `aruco_ids`: the marker IDs to find, default `(0, 1, 2, 3)`.
- `aruco_dictionary_enum`: an OpenCV dictionary number, default `cv2.aruco.DICT_4X4_50`.

An option with a different name raises `TypeError`. A wrong value raises the Pydantic
`ValidationError`, which names the field. An unknown key raises `DetectorNotFoundError`. An entry
that is not available raises `DetectorUnavailableError` with the reason.

The caller imports no detector class, no config class of a detector, no session and no module of
`calibration_detectors`. The board model `CharucoBoardDefinition` is public data. It and the
calibration helpers that are not detectors are in `skellytracker.core.detectors.calibration`. This module imports each detector module in the body
of `create_detector`, so `import skellytracker.core.detectors` loads no generic detector, no
calibration detector, no ONNX Runtime and no MediaPipe. The signature of `create_detector` and the
methods `detect(image)` and `close()` stay when the calibration classes change.
"""
from __future__ import annotations

from typing import Any

from skellytracker.core.detectors.catalog import DetectorUnavailableError, _select, _static_entries, split_key

CALIBRATION_OPTIONS: dict[str, tuple[str, ...]] = {
    "charuco@skellytracker": ("board",),
    "aruco@skellytracker": ("aruco_ids", "aruco_dictionary_enum"),
}


def create_detector(key: str, **options: Any) -> Any:
    """Return the detector of the catalog entry `<key>` or `<key>==<version>`. The module docstring gives the options."""
    static = _static_entries()
    if split_key(key)[0] not in {entry.key for entry in static}:
        from skellytracker.core.detectors.generic.session import create_detector as create_generic_detector

        return create_generic_detector(key, **options)
    entry = _select(key, static)
    if not entry.available:
        raise DetectorUnavailableError(f"{entry.key} is unavailable: {entry.unavailable_reason}")
    if entry.category != "calibration":
        raise DetectorUnavailableError(
            f"{entry.key} is unavailable in `create_detector`: the pipeline node `mediapipe_tasks` runs MediaPipe"
        )
    allowed = CALIBRATION_OPTIONS[entry.key]
    if unknown := sorted(set(options) - set(allowed)):
        raise TypeError(f"{entry.key} takes the options {list(allowed)}; it does not take {unknown}")

    # The calibration classes use the old CPU session until stage 2.4 of the implementation plan.
    from skellytracker.core.sessions.cpu_session import CpuSession

    if entry.key == "charuco@skellytracker":
        from skellytracker.core.detectors.calibration_detectors.charuco.charuco_detector import CharucoDetector
        from skellytracker.core.detectors.calibration_detectors.charuco.charuco_detector_config import CharucoDetectorConfig

        return CharucoDetector.create(CharucoDetectorConfig(**options), CpuSession())
    from skellytracker.core.detectors.calibration_detectors.aruco.aruco_detector import ArucoDetector
    from skellytracker.core.detectors.calibration_detectors.aruco.aruco_detector_config import ArucoDetectorConfig

    return ArucoDetector.create(ArucoDetectorConfig(**options), CpuSession())
