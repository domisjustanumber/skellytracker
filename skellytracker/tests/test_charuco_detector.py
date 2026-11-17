from __future__ import annotations

import cv2
import numpy as np
import pytest

from skellytracker.core.data_primitives import Keypoints
from skellytracker.core.detectors.calibration_detectors.charuco import (
    CharucoAnnotator,
    CharucoAnnotatorConfig,
    CharucoBoardDefinition,
    CharucoDetector,
    CharucoDetectorConfig,
    compute_board_pose,
    to_anipose_camera_row,
)
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_detector import (
    _squeeze_aruco,
    _squeeze_charuco,
)
from skellytracker.core.detectors.metadata import EmptyMetadata
from skellytracker.core.sessions.cpu_session import CpuSession, CpuSessionConfig


@pytest.fixture(scope="module")
def board_def() -> CharucoBoardDefinition:
    return CharucoBoardDefinition.create_test_data_7x5()


@pytest.fixture(scope="module")
def cpu_session() -> CpuSession:
    session = CpuSession.create(CpuSessionConfig())
    yield session
    session.close()


@pytest.fixture(scope="module")
def detector(board_def, cpu_session) -> CharucoDetector:
    config = CharucoDetectorConfig(board=board_def)
    return CharucoDetector.create(config, cpu_session)


class TestCharucoDetector:
    def test_detect_returns_correct_shape(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        expected_n_aruco = len(detector._aruco_ids) * 4
        expected_total = board_def.n_corners + expected_n_aruco
        assert kpts.xyz.shape == (expected_total, 3)
        assert kpts.visibility.shape == (expected_total,)
        assert len(kpts.names) == expected_total

    def test_detect_finds_corners(self, detector, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        assert kpts.n_valid > 0

    def test_detect_charuco_corner_names(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        for i in range(board_def.n_corners):
            assert kpts.names[i] == f"CharucoCorner-{i}"

    def test_detect_aruco_corner_names(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        n_charuco = board_def.n_corners
        for _offset, name in enumerate(kpts.names[n_charuco:]):
            assert name.startswith("ArucoMarkerCorner-")
            parts = name.split("-")
            assert len(parts) == 3
            assert parts[2].isdigit()
            assert int(parts[2]) in range(4)

    def test_detect_empty_on_blank_image(self, detector):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        kpts = detector.detect(blank)
        assert np.all(np.isnan(kpts.xyz))
        assert np.all(kpts.visibility == 0.0)

    def test_detect_visibility_in_range(self, detector, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        assert np.all(kpts.visibility >= 0.0)
        assert np.all(kpts.visibility <= 1.0)

    def test_detect_z_is_zero_for_detected(self, detector, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        detected_mask = kpts.visibility > 0.0
        assert np.all(kpts.xyz[detected_mask, 2] == 0.0)

    def test_connections_is_empty(self):
        assert CharucoDetector.connections() == ()


class TestComputeBoardPose:
    def test_returns_none_without_enough_corners(self, detector, board_def):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        kpts = detector.detect(blank)
        fake_camera_matrix = np.eye(3, dtype=np.float64)
        result = compute_board_pose(kpts, board_def, fake_camera_matrix, np.zeros(5))
        assert result is None

    def test_returns_rvec_tvec_shape(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        if kpts.n_valid < 6:
            pytest.skip("Not enough corners detected for pose estimation")
        fake_camera_matrix = np.array(
            [[1000, 0, 320], [0, 1000, 240], [0, 0, 1]], dtype=np.float64
        )
        result = compute_board_pose(kpts, board_def, fake_camera_matrix, np.zeros(5))
        if result is not None:
            rvec, tvec = result
            assert rvec.shape == (3,)
            assert tvec.shape == (3,)


CAMERA = np.array([[1000.0, 0.0, 320.0], [0.0, 1000.0, 240.0], [0.0, 0.0, 1.0]])
RVEC = np.array([0.1, -0.2, 0.05])
TVEC = np.array([-100.0, -60.0, 1000.0])
SIX_CORNERS = [0, 5, 7, 12, 18, 23]  # not on one line


def projected_keypoints(board_def: CharucoBoardDefinition, corners: list[int]) -> Keypoints:
    """The board corners in `corners` at the known pose `RVEC`, `TVEC`. The other points are not detected."""
    image, _ = cv2.projectPoints(board_def.corner_positions_board_frame.astype(np.float64), RVEC, TVEC, CAMERA, np.zeros(5))
    names = tuple(board_def.all_point_names)
    xyz = np.full((len(names), 3), np.nan)
    visibility = np.zeros(len(names))
    xyz[corners, :2] = image.reshape(-1, 2)[corners]
    xyz[corners, 2] = 0.0
    visibility[corners] = 1.0
    return Keypoints(names=names, xyz=xyz, visibility=visibility)


def test_compute_board_pose_gives_the_known_pose(board_def):
    for corners in (list(range(board_def.n_corners)), SIX_CORNERS):
        rvec, tvec = compute_board_pose(projected_keypoints(board_def, corners), board_def, CAMERA, np.zeros(5))
        assert rvec == pytest.approx(RVEC, rel=1e-4, abs=1e-4)
        assert tvec == pytest.approx(TVEC, rel=1e-4, abs=1e-4)


@pytest.mark.parametrize(("column", "value"), [(0, np.inf), (1, np.nan)], ids=["inf-x", "nan-y"])
def test_compute_board_pose_drops_a_point_that_is_not_finite(board_def, column, value):
    # OpenCV 5 solvePnP returns success with a zero pose for such input; OpenCV 4.12 returned NaN.
    keypoints = projected_keypoints(board_def, SIX_CORNERS)
    keypoints.xyz[SIX_CORNERS[0], column] = value
    assert compute_board_pose(keypoints, board_def, CAMERA, np.zeros(5)) is None
    keypoints = projected_keypoints(board_def, list(range(board_def.n_corners)))
    keypoints.xyz[0, column] = value
    rvec, tvec = compute_board_pose(keypoints, board_def, CAMERA, np.zeros(5))
    assert rvec == pytest.approx(RVEC, rel=1e-4, abs=1e-4)
    assert tvec == pytest.approx(TVEC, rel=1e-4, abs=1e-4)


@pytest.mark.parametrize(
    ("camera", "distortion"),
    [(np.where(np.eye(3) > 0, np.nan, CAMERA), np.zeros(5)), (CAMERA, np.array([np.nan, 0.0, 0.0, 0.0, 0.0]))],
    ids=["nan-camera-matrix", "nan-distortion"],
)
def test_compute_board_pose_refuses_camera_values_that_are_not_finite(board_def, camera, distortion):
    keypoints = projected_keypoints(board_def, list(range(board_def.n_corners)))
    assert compute_board_pose(keypoints, board_def, camera, distortion) is None


class TestCharucoAnnotator:
    def test_annotate_returns_different_image(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        annotator = CharucoAnnotator(
            config=CharucoAnnotatorConfig(), board_def=board_def
        )
        annotated = annotator.annotate(charuco_test_image, kpts)
        assert not np.array_equal(annotated, charuco_test_image)

    def test_annotate_preserves_shape(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        annotator = CharucoAnnotator(
            config=CharucoAnnotatorConfig(), board_def=board_def
        )
        annotated = annotator.annotate(charuco_test_image, kpts)
        assert annotated.shape == charuco_test_image.shape

    def test_annotate_blank_does_not_crash(self, detector, board_def):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        kpts = detector.detect(blank)
        annotator = CharucoAnnotator(
            config=CharucoAnnotatorConfig(), board_def=board_def
        )
        annotated = annotator.annotate(blank, kpts)
        assert annotated.shape == blank.shape


class TestAniposeExport:
    def test_anipose_row_keys(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        row = to_anipose_camera_row(kpts, board_def, frame_number=0)
        assert set(row.keys()) == {"framenum", "corners", "ids", "filled"}

    def test_anipose_filled_shape(self, detector, board_def, charuco_test_image):
        kpts = detector.detect(charuco_test_image)
        row = to_anipose_camera_row(kpts, board_def, frame_number=5)
        assert row["filled"].shape == (board_def.n_corners, 1, 2)
        assert row["framenum"] == (0, 5)

    def test_anipose_blank_has_all_nan_filled(self, detector, board_def):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        kpts = detector.detect(blank)
        row = to_anipose_camera_row(kpts, board_def, frame_number=0)
        assert np.all(np.isnan(row["filled"]))


class TestSqueezeHelpers:
    def test_squeeze_charuco_handles_shape_1(self):
        # OpenCV can return already-1D (N,) ids/corners instead of (N,1);
        # for a single detected corner that used to squeeze to a 0-d array.
        ids = np.array([5])
        corners = np.array([[[100.0, 200.0]]])
        squeezed_ids, squeezed_corners = _squeeze_charuco(ids, corners)
        assert squeezed_ids.ndim == 1
        assert list(squeezed_ids) == [5]
        assert squeezed_corners.shape == (1, 2)

    def test_squeeze_aruco_handles_shape_1(self):
        ids = np.array([7])
        corners = [np.array([[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]])]
        squeezed_ids, squeezed_corners = _squeeze_aruco(ids, corners, valid_ids=(7,))
        assert squeezed_ids.ndim == 1
        assert list(squeezed_ids) == [7]
        assert squeezed_corners.shape == (1, 4, 2)


@pytest.mark.parametrize("n", [1, 3])
def test_postprocess_gives_the_same_keypoints_for_the_opencv_4_and_5_shapes(detector, n):
    """OpenCV 4 gives ids (N, 1) and charuco corners (N, 1, 2). OpenCV 5 gives ids (N,) and corners (N, 2)."""
    rng = np.random.default_rng(7)
    corner_ids = np.array([0, 4, 9][:n], dtype=np.int32)
    corners = rng.uniform(0, 640, (n, 2)).astype(np.float32)
    marker_ids = np.array(detector._aruco_ids[:n], dtype=np.int32)
    markers = tuple(rng.uniform(0, 640, (1, 4, 2)).astype(np.float32) for _ in range(n))
    old = detector.postprocess((corners[:, None, :], corner_ids[:, None], markers, marker_ids[:, None]), EmptyMetadata())
    new = detector.postprocess((corners, corner_ids, markers, marker_ids), EmptyMetadata())
    np.testing.assert_array_equal(old.xyz, new.xyz)
    np.testing.assert_array_equal(old.visibility, new.visibility)
    assert np.count_nonzero(new.visibility) == n + 4 * n
    assert new.xyz[corner_ids, :2] == pytest.approx(corners)
