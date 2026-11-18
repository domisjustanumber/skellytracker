"""The frame in host memory or in GPU memory (`core/decode/frame.py`), with a fake upload and a fake device frame: no GPU."""
from __future__ import annotations

import numpy as np
import pytest

from skellytracker.core.decode.frame import DecodedFrame


class Upload:
    """A fake `upload_frame`: it counts the calls and gives a token for each."""

    def __init__(self) -> None:
        self.calls: list[tuple[np.ndarray, int]] = []

    def __call__(self, image: np.ndarray, device_id: int) -> tuple[str, int]:
        self.calls.append((image, device_id))
        return ("device", len(self.calls))


class FakeOrtValue:
    """A device frame: `numpy()` copies to the host."""

    def __init__(self, pixels: np.ndarray) -> None:
        self.pixels, self.copies = pixels, 0

    def numpy(self) -> np.ndarray:
        self.copies += 1
        return self.pixels.copy()


def test_a_host_frame_keeps_the_array_and_uploads_one_time_for_each_device() -> None:
    pixels = np.zeros((4, 6, 3), np.uint8)
    frame, upload = DecodedFrame.from_host(pixels), Upload()
    assert (frame.width, frame.height) == (6, 4) and frame.host is pixels  # no copy
    first = frame.on_device(0, upload)
    assert frame.on_device(0, upload) is first and len(upload.calls) == 1 and upload.calls[0][0] is pixels
    assert frame.on_device(1, upload) != first and len(upload.calls) == 2


def test_a_device_frame_comes_back_as_it_is_and_copies_to_the_host_one_time() -> None:
    device, upload = FakeOrtValue(np.full((4, 6, 3), 7, np.uint8)), Upload()
    frame = DecodedFrame(6, 4, device=device)
    assert frame.on_device(0, upload) is device and not upload.calls
    assert frame.host is frame.host and device.copies == 1
    np.testing.assert_array_equal(frame.host, device.pixels)


@pytest.mark.parametrize("given", [{}, {"pixels": np.zeros((1, 1, 3), np.uint8), "device": object()}])
def test_a_frame_takes_exactly_one_of_host_pixels_and_a_device_frame(given: dict) -> None:
    with pytest.raises(ValueError, match="exactly one"):
        DecodedFrame(1, 1, **given)
