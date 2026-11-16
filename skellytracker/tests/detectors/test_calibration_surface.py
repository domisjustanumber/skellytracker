"""The calibration names and calls of freemocap (ref sfn26), through the public surface only.

This file imports `skellytracker.core.detectors` and `skellytracker.core.detectors.calibration`,
and no module of the calibration detectors.
"""
from __future__ import annotations

import pickle
from collections.abc import Iterator

import numpy as np
import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from skellytracker.core.detectors import create_detector
from skellytracker.core.detectors.calibration import (
    ARUCO_MARKER_TAGS,
    CHARUCO_BOARD_MAPPING,
    CHARUCO_CORNER_TAGS,
    CHARUCO_GRID_TAGS,
    CharucoAnnotator,
    CharucoAnnotatorConfig,
    CharucoBoardDefinition,
    CharucoBoardSelectionError,
    CharucoBoardSelector,
    compute_board_pose,
    to_anipose_camera_row,
    transform_to_camera_coordinates,
)

BLANK = np.full((480, 640, 3), 255, np.uint8)


class CallerConfig(BaseModel):
    """A config of a caller, with the board as a field with an alias."""

    model_config = ConfigDict(populate_by_name=True)
    charuco_board: CharucoBoardDefinition = Field(default_factory=CharucoBoardDefinition.create_letter_size_5x3, alias="charucoBoard")


def test_the_board_model_is_public_data() -> None:
    board = CharucoBoardDefinition(squares_x=7, squares_y=5, square_length_mm=1.0, marker_length_ratio=0.8, aruco_dictionary_enum=2)
    board.squares_x, board.squares_y, board.square_length_mm = 5, 3, 54.0  # the model is not frozen
    assert board == CharucoBoardDefinition.create_letter_size_5x3() != CharucoBoardDefinition.create_test_data_7x5()
    with pytest.raises(ValidationError):
        CharucoBoardDefinition(squares_x=5, squares_y=3, square_length_mm=54.0, squares=5)  # extra="forbid"

    assert {"squares_x", "squares_y", "square_length_mm", "aruco_dictionary_enum"} <= set(CharucoBoardDefinition.model_fields)
    saved = {name: value for name, value in board.model_dump(round_trip=True).items() if name in CharucoBoardDefinition.model_fields}
    assert CharucoBoardDefinition.model_validate(saved) == board
    assert board.model_copy(deep=True) == board == pickle.loads(pickle.dumps(board))  # noqa: S301
    assert board.model_copy(update={"square_length_mm": 50.0}).square_length_mm == 50.0
    assert CallerConfig.model_validate({"charucoBoard": saved}).charuco_board == CallerConfig().charuco_board == board

    assert board.n_corners == 8 and board.corner_positions_board_frame.shape == (8, 3)
    assert board.charuco_corner_names == tuple(f"CharucoCorner-{i}" for i in range(8))
    assert all(name.startswith("ArucoMarkerCorner-") for name in board.aruco_corner_names)
    assert board.all_point_names == board.charuco_corner_names + board.aruco_corner_names
    assert set(board.normalized_point_positions) == set(board.all_point_names)
    connected = {name for pair in board.charuco_grid_connections + board.aruco_marker_connections for name in pair}
    assert connected == set(board.all_point_names)
    assert board.cv2_board.generateImage((600, 360), marginSize=30).shape == (360, 600)


def test_the_calibration_calls_of_freemocap(charuco_test_image: np.ndarray) -> None:
    # The board search of a recording. The selector reads the images only on a search frame.
    read: list[int] = []

    def images(frame_number: int, *found: np.ndarray) -> Iterator[np.ndarray]:
        read.append(frame_number)
        yield from found

    selector = CharucoBoardSelector()
    assert selector.maximum_skipped_frames == 30
    assert selector.search_frame(frame_number=0, images=images(0, BLANK)) is None  # a miss
    assert selector.search_frame(frame_number=1, images=images(1, charuco_test_image)) is None  # a skipped frame
    board = selector.search_frame(frame_number=2, images=images(2, BLANK, charuco_test_image))
    assert read == [0, 2] and board == CharucoBoardDefinition.create_test_data_7x5()
    with pytest.raises(ValueError, match="strictly increasing"):
        selector.search_frame(frame_number=2, images=images(2, BLANK))
    assert CharucoBoardSelector().observe_image(image=BLANK) is None
    assert CharucoBoardSelector().observe_image(image=charuco_test_image) == board
    assert issubclass(CharucoBoardSelectionError, ValueError)  # the caller raises it

    # The factory takes the board model, and also a mapping of its fields. The detector gives the board back.
    detector = create_detector("charuco@skellytracker", board=board)
    assert detector.board == board == create_detector("charuco@skellytracker", board=board.model_dump(round_trip=True)).board

    # The result contract: the corner names first and in order, then the marker corners.
    keypoints = detector.detect(charuco_test_image)
    assert keypoints.names == board.all_point_names
    assert keypoints.names[: board.n_corners] == tuple(f"CharucoCorner-{i}" for i in range(board.n_corners))
    assert all(name.startswith("ArucoMarkerCorner-") for name in keypoints.names[board.n_corners :])
    assert keypoints.has_name("CharucoCorner-0") and keypoints.index_of("CharucoCorner-3") == 3
    assert keypoints.xyz.shape == (len(board.all_point_names), 3) and keypoints.visibility.shape == (len(board.all_point_names),)
    assert np.any(keypoints.visibility > 0.0)
    missing = detector.detect(BLANK)
    assert missing.names == board.all_point_names and np.all(np.isnan(missing.xyz)) and np.all(missing.visibility == 0.0)

    row = to_anipose_camera_row(keypoints=keypoints, board_def=board, frame_number=5)
    assert set(row) == {"framenum", "corners", "ids", "filled"} and row["framenum"][1] == 5
    assert row["filled"].shape == (board.n_corners, 1, 2) and len(row["ids"]) == len(row["corners"]) > 0

    camera_matrix = np.array([[1000.0, 0.0, 320.0], [0.0, 1000.0, 240.0], [0.0, 0.0, 1.0]])
    rvec, tvec = compute_board_pose(keypoints, board, camera_matrix, np.zeros(5))
    assert transform_to_camera_coordinates(board.corner_positions_board_frame, rvec, tvec).shape == (board.n_corners, 3)

    # The caller makes the annotator and gives it to the old annotation code.
    assert CharucoAnnotator(config=CharucoAnnotatorConfig(), board_def=board).board_def == board

    assert (CHARUCO_CORNER_TAGS, CHARUCO_GRID_TAGS, ARUCO_MARKER_TAGS) == (("charuco_corner",), ("charuco_grid", "charuco_corner"), ("aruco_marker",))
    assert CHARUCO_BOARD_MAPPING.is_file()
    detector.close()
