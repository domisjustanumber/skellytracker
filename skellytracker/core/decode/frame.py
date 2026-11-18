"""`DecodedFrame`: the value of the port `frame.image`, in host memory or in GPU memory.

Implements: pipeline.running

This module imports no `onnxruntime`: a device frame is an `onnxruntime.OrtValue` that the caller
gives, and the upload function comes from the caller (`core.eps.session.upload_frame`).
"""
from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class DecodedFrame:
    """One turned frame of one camera in one call. Exactly one of `pixels` and `device` is given.

    `pixels` is the host frame: BGR, `uint8`, `(H, W, 3)`. `device` is an `onnxruntime.OrtValue`
    in GPU memory with the same layout (typed `Any`: beartype checks each hint at run time, and
    this module must not import `onnxruntime`). A new call makes a new `DecodedFrame`, so each
    cache of the frame lives for one call.
    """

    width: int
    height: int
    pixels: np.ndarray | None = None
    device: Any = None
    _uploads: dict[Any, Any] = field(default_factory=dict, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (self.pixels is None) == (self.device is None):
            raise ValueError("a DecodedFrame takes exactly one of `pixels` and `device`")

    @classmethod
    def from_host(cls, pixels: np.ndarray) -> DecodedFrame:
        """Wrap a host frame `(H, W, 3)`. The frame keeps the array object: no copy."""
        height, width = pixels.shape[:2]
        return cls(int(width), int(height), pixels=pixels)

    @functools.cached_property
    def host(self) -> np.ndarray:
        """The host pixels. A device frame copies to the host at the first read, and keeps the copy."""
        return self.pixels if self.pixels is not None else self.device.numpy()

    def on_device(self, device_id: Any, upload: Callable[[np.ndarray, Any], Any]) -> Any:
        """The frame in GPU memory of `device_id`. A host frame calls `upload(host, device_id)` one time for each device id.

        A device frame comes back as it is, with no upload.
        """
        if self.device is not None:
            return self.device
        if device_id not in self._uploads:
            self._uploads[device_id] = upload(self.pixels, device_id)
        return self._uploads[device_id]
