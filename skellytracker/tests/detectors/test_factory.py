"""The public factory `skellytracker.core.detectors.create_detector`."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from skellytracker.core.detectors import DetectorNotFoundError, DetectorUnavailableError, catalog, create_detector
from skellytracker.core.model_spec import artifacts

BOARD_7X5 = {"squares_x": 7, "squares_y": 5, "square_length_mm": 58.0}


def test_the_import_of_the_entry_point_loads_no_detector_module() -> None:
    code = (
        "import sys, skellytracker.core.detectors as d; assert callable(d.create_detector); "
        "bad = [m for m in sys.modules if m.split('.')[0] in ('onnxruntime', 'mediapipe') "
        "or m.startswith(('skellytracker.core.detectors.calibration', 'skellytracker.core.detectors.generic'))]; "
        "print(bad); sys.exit(1 if bad else 0)"
    )
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0  # noqa: S603


def test_charuco_detects_the_board_of_its_options(charuco_test_image: np.ndarray) -> None:
    detector = create_detector("charuco@skellytracker", board=BOARD_7X5)
    keypoints = detector.detect(charuco_test_image)
    n_corners = 6 * 4
    assert keypoints.xyz.shape == (n_corners + len(detector._aruco_ids) * 4, 3)
    assert keypoints.names[:n_corners] == tuple(f"CharucoCorner-{i}" for i in range(n_corners))
    assert keypoints.n_valid > 0 and np.all(keypoints.xyz[keypoints.visibility > 0.0, 2] == 0.0)
    assert detector.board.square_length_mm == 58.0
    detector.close()


def test_charuco_with_no_board_has_the_5x3_board() -> None:
    board = create_detector("charuco@skellytracker").board
    assert (board.squares_x, board.squares_y, board.square_length_mm) == (5, 3, 54.0)


@pytest.mark.parametrize("board", [{"squares_x": 7, "squares_y": 5}, {**BOARD_7X5, "squares": 7}, {**BOARD_7X5, "squares_y": 1}])
def test_a_wrong_board_option_gives_the_pydantic_error_with_the_field(board: dict) -> None:
    with pytest.raises(ValidationError, match="board"):
        create_detector("charuco@skellytracker", board=board)


def test_an_option_that_the_entry_does_not_have_is_an_error() -> None:
    with pytest.raises(TypeError, match="execution_provider"):
        create_detector("charuco@skellytracker", execution_provider="cpu")
    with pytest.raises(TypeError, match="board"):
        create_detector("aruco@skellytracker", board=BOARD_7X5)


def test_aruco_detects_the_markers_of_its_options() -> None:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    image = np.full((480, 640), 255, np.uint8)
    image[140:340, 220:420] = cv2.aruco.generateImageMarker(dictionary, 0, 200)
    detector = create_detector("aruco@skellytracker", aruco_ids=(0, 1))
    keypoints = detector.detect(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))
    assert keypoints.names[0] == "ArucoMarker-0-corner-0" and keypoints.xyz.shape == (8, 3)
    assert keypoints.visibility.tolist() == [1.0] * 4 + [0.0] * 4
    detector.close()


def test_a_mediapipe_key_names_the_pipeline_node() -> None:
    if not catalog.get_detector("mediapipe_pose@skellytracker").available:
        pytest.skip("mediapipe not installed")
    with pytest.raises(DetectorUnavailableError, match="mediapipe_tasks"):
        create_detector("mediapipe_pose@skellytracker")


def test_an_unknown_key_and_a_pin_of_an_entry_with_no_version_are_not_found(tmp_path: Path) -> None:
    with pytest.raises(DetectorNotFoundError, match="no-model@nowhere"):
        create_detector("no-model@nowhere", execution_provider="cpu", user_root=tmp_path)
    with pytest.raises(DetectorNotFoundError, match="version"):
        create_detector("charuco@skellytracker==1.0")


def test_an_entry_that_is_not_available_gives_its_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalog, "find_spec", lambda name: None)
    with pytest.raises(DetectorUnavailableError, match="opencv-contrib-python"):
        create_detector("charuco@skellytracker")


def test_an_onnx_key_goes_to_the_generic_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skellytracker.core.detectors.generic import GenericObjectDetector
    from skellytracker.tests.detectors.onnx_models import object_model
    from skellytracker.tests.detectors.test_generic_detectors import OBJECT_KEY, frame, object_sidecar, put

    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")
    monkeypatch.setattr(artifacts, "download_root", lambda: tmp_path / "cache" / "models")
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)
    put(tmp_path / "user", object_sidecar(), object_model())
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=tmp_path / "user")
    assert isinstance(detector, GenericObjectDetector)
    np.testing.assert_allclose(detector.detect([frame(1)])[0].boxes, [[2, 2, 10, 10], [20, 20, 30, 30]])
