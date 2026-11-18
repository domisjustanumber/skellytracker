"""The CPU decode of one JPEG buffer, and the turn of the decoded frame.

Implements: pipeline.running
"""
from __future__ import annotations

import cv2
import numpy as np

# rotation_deg (clockwise) -> the `cv2.rotate` code, or None for no turn.
ROTATIONS = {0: None, 90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}


def decode_jpeg(buffer: bytes | bytearray, rotation_deg: int = 0) -> np.ndarray:
    """Decode one JPEG buffer to a BGR `uint8` frame `(H, W, 3)`, then turn it clockwise by `rotation_deg`.

    Implements: pipeline.running

    The decode ignores the EXIF orientation. `rotation_deg` is a key of `ROTATIONS`. Raise
    `ValueError` for a buffer that is not a JPEG image that OpenCV can read.
    """
    # The SOI check also refuses an empty buffer, for which `cv2.imdecode` raises an assertion error.
    if not buffer.startswith(b"\xff\xd8"):
        raise ValueError("the buffer is not a JPEG image: it does not start with the JPEG SOI marker")
    try:
        image = cv2.imdecode(np.frombuffer(buffer, np.uint8), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
    except cv2.error as exc:
        raise ValueError(f"OpenCV cannot read the JPEG buffer: {exc}") from exc
    if image is None:
        raise ValueError("OpenCV cannot read the JPEG buffer")
    turn = ROTATIONS[rotation_deg]
    return image if turn is None else cv2.rotate(image, turn)
