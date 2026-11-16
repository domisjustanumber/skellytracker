"""The public calibration helpers that are not detectors. A caller imports them from this module.

    from skellytracker.core.detectors import create_detector
    from skellytracker.core.detectors.calibration import CharucoBoardSelector, to_anipose_camera_row

    board = CharucoBoardSelector().observe_image(image=frame)  # a CharucoBoardDefinition, or None
    detector = create_detector("charuco@skellytracker", board=board)
    row = to_anipose_camera_row(keypoints=detector.detect(frame), board_def=board, frame_number=0)

`create_detector` makes the charuco and the aruco detector. A caller does not import
`skellytracker.core.detectors.calibration_detectors`. `import skellytracker.core.detectors` does
not import this module.

- `CharucoBoardDefinition`: the board model. It is public data: a Pydantic model that is not
  frozen, with the fields `squares_x`, `squares_y`, `square_length_mm`, `marker_length_ratio` and
  `aruco_dictionary_enum`, and with the point names, the positions and the connections of the
  board. It is the `board` of `create_detector`, the result of the selector and the `board_def`
  of the helpers. `detector.board` gives it back.
- `CharucoBoardSelector`, `StandardCharucoBoard`, `CharucoBoardSelectionError`: find which
  standard board is in the images (`observe_image`, `search_frame`, `from_images`).
- `to_anipose_camera_row`: one anipose camera row from the `Keypoints` of the charuco detector.
- `compute_board_pose`, `transform_to_camera_coordinates`: the pose of the board in one camera, and
  board points in the coordinates of that camera.
- `CharucoAnnotator`, `CharucoAnnotatorConfig`: draw the `Keypoints` of the charuco detector.
  They are old annotation code.
- `CHARUCO_CORNER_TAGS`, `CHARUCO_GRID_TAGS`, `ARUCO_MARKER_TAGS`: the tags of the board parts.
- `CHARUCO_BOARD_MAPPING`: the path of the mapping file of a charuco board.
"""
from skellytracker.core.detectors.calibration_detectors.charuco.anipose_export import to_anipose_camera_row
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_annotator import (
    CharucoAnnotator,
    CharucoAnnotatorConfig,
)
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_board_definition import (
    ARUCO_MARKER_TAGS,
    CHARUCO_CORNER_TAGS,
    CHARUCO_GRID_TAGS,
    CharucoBoardDefinition,
)
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_board_mapping import CHARUCO_BOARD_MAPPING
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_board_pose import (
    compute_board_pose,
    transform_to_camera_coordinates,
)
from skellytracker.core.detectors.calibration_detectors.charuco.charuco_board_selection import (
    CharucoBoardSelectionError,
    CharucoBoardSelector,
    StandardCharucoBoard,
)

__all__ = [
    "ARUCO_MARKER_TAGS",
    "CHARUCO_BOARD_MAPPING",
    "CHARUCO_CORNER_TAGS",
    "CHARUCO_GRID_TAGS",
    "CharucoAnnotator",
    "CharucoAnnotatorConfig",
    "CharucoBoardDefinition",
    "CharucoBoardSelectionError",
    "CharucoBoardSelector",
    "StandardCharucoBoard",
    "compute_board_pose",
    "to_anipose_camera_row",
    "transform_to_camera_coordinates",
]
