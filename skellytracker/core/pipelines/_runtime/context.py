"""The facts of one frame of one camera that a node gets at each call."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameContext:
    """One frame of one camera."""

    frame_index: int
    timestamp_ms: float | None
    """The timestamp of the frame, in milliseconds. ``None`` in the running mode ``image``."""
    image_size: tuple[int, int]
    """``(width, height)`` of the source image, in pixels."""
    running_mode: str
    """``image``, ``video`` or ``live``."""
