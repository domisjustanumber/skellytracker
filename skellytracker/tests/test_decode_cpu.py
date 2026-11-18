"""The CPU decode of a JPEG frame (`core/decode/cpu.py`), on JPEG bytes that the test makes."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from skellytracker.core.decode.cpu import decode_jpeg

FLAGS = cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION


def jpeg(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes()


def noise(height: int = 24, width: int = 40) -> np.ndarray:
    return np.random.default_rng(0).integers(0, 256, (height, width, 3), np.uint8)


def with_exif_orientation(data: bytes, orientation: int) -> bytes:
    """Return `data` with an APP1 Exif segment after the SOI marker: one IFD entry, the tag Orientation (0x0112)."""
    tiff = b"MM\x00\x2a\x00\x00\x00\x08" + b"\x00\x01" + b"\x01\x12\x00\x03\x00\x00\x00\x01" + bytes([0, orientation, 0, 0]) + b"\x00\x00\x00\x00"
    payload = b"Exif\x00\x00" + tiff
    return data[:2] + b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload + data[2:]


def test_the_decode_equals_cv2_imdecode_of_the_same_bytes_for_bytes_and_bytearray() -> None:
    data = jpeg(noise())
    expected = cv2.imdecode(np.frombuffer(data, np.uint8), FLAGS)
    for buffer in (data, bytearray(data)):
        found = decode_jpeg(buffer)
        assert found.dtype == np.uint8 and found.shape == (24, 40, 3)
        np.testing.assert_array_equal(found, expected)


@pytest.mark.parametrize(("rotation_deg", "code", "shape"), [
    (90, cv2.ROTATE_90_CLOCKWISE, (40, 24, 3)), (180, cv2.ROTATE_180, (24, 40, 3)), (270, cv2.ROTATE_90_COUNTERCLOCKWISE, (40, 24, 3)),
])
def test_each_rotation_deg_equals_the_matching_cv2_rotate(rotation_deg: int, code: int, shape: tuple[int, int, int]) -> None:
    data = jpeg(noise())
    found = decode_jpeg(data, rotation_deg)
    assert found.shape == shape
    np.testing.assert_array_equal(found, cv2.rotate(decode_jpeg(data), code))


def test_the_decode_ignores_an_exif_orientation_tag() -> None:
    data = with_exif_orientation(jpeg(noise()), 6)  # 6: turn 90 degrees clockwise to view
    assert cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR).shape == (40, 24, 3)  # the tag is valid: OpenCV applies it with no flag
    found = decode_jpeg(data)
    assert found.shape == (24, 40, 3)
    np.testing.assert_array_equal(found, decode_jpeg(jpeg(noise())))


@pytest.mark.parametrize("buffer", [b"", bytearray(), b"\x00" * 16, bytes(np.random.default_rng(1).integers(0, 256, 256, np.uint8)), b"\xff\xd8" + b"junk" * 16])
def test_an_empty_buffer_and_bytes_that_are_not_a_jpeg_raise_value_error(buffer: bytes | bytearray) -> None:
    with pytest.raises(ValueError, match="JPEG"):
        decode_jpeg(buffer)


def test_a_png_buffer_is_not_a_jpeg() -> None:
    ok, encoded = cv2.imencode(".png", noise())
    assert ok
    with pytest.raises(ValueError, match="SOI"):
        decode_jpeg(encoded.tobytes())


def test_a_grayscale_jpeg_gives_three_channels() -> None:
    found = decode_jpeg(jpeg(noise()[:, :, 0]))
    assert found.shape == (24, 40, 3) and found.dtype == np.uint8
