"""The path of the mapping file of a charuco board. This module imports no detector module."""
from pathlib import Path

CHARUCO_BOARD_MAPPING = Path(__file__).parent / "charuco_board_to_landmark_mapping.yaml"
