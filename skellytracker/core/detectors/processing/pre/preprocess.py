"""The preprocessing of one host frame from a loaded sidecar: the resize dispatcher and the input tensor.

`resize_image` calls the module of the resize method of the sidecar. `preprocess_image` also
normalizes the result and gives the tensor of one image in CHW layout.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from skellytracker.core.detectors.processing.pre import (
    resize_affine_crop,
    resize_fit,
    resize_letterbox,
    resize_stretch,
)
from skellytracker.core.detectors.processing.pre.normalize import normalize
from skellytracker.core.detectors.processing.pre.resize_interpolation import (
    border_values,
    interpolation_flag,
    to_compute_dtype,
)
from skellytracker.core.model_spec.model import ResizeSpec, SidecarModel


@dataclass(frozen=True)
class ResizeGeometry:
    """The geometry of one resize. The unprojection needs it for the Inverse of the method.

    `input_size` is `(height, width)` of the model input. `values` holds the geometry of the
    method: `n_w`, `n_h`, `left` and `top` for `letterbox`; `scale`, `left` and `top` for `fit`;
    `matrix` (with `center`, `crop_w` and `crop_h`) for `affine_crop`. It is empty for `stretch`
    and `none`.
    """

    method: str
    src_w: int
    src_h: int
    input_size: tuple[int, int]
    values: dict[str, Any]


def resize_geometry(
    resize: ResizeSpec,
    target_size: Sequence[int] | None,
    src_w: int,
    src_h: int,
    roi: Sequence[Any] | None = None,
) -> ResizeGeometry:
    """Return the geometry of the resize of one source image, without the image.

    Implements: common.input

    `target_size` is `[height, width]` of the size entry. It is `None` for `method: none`: the
    model input is then the source image. `roi` is `(c_x, c_y, w, h, rotation)` in source pixels.
    `affine_crop` needs it, and no other method takes it.
    """
    method = resize.method
    if (roi is not None) != (method == "affine_crop"):
        raise ValueError(f"an ROI is necessary for affine_crop and for no other method; the method is {method!r}")
    if method == "none":
        return ResizeGeometry(method, src_w, src_h, (src_h, src_w), {})
    if target_size is None:
        raise ValueError(f"the resize method {method!r} needs target_size")
    values: dict[str, Any] = {}
    if method == "letterbox":
        values = resize_letterbox.letterbox_geometry(src_w, src_h, target_size, str(resize.pad_position), str(resize.rounding))
    elif method == "fit":
        values = resize_fit.fit_geometry(src_w, src_h, target_size)
    elif method == "stretch":
        resize_stretch.stretch_geometry(src_w, src_h, target_size)
    else:
        policy = resize.crop_policy
        values = resize_affine_crop.crop_geometry(roi, target_size, policy.expand_ratio, policy.maintain_aspect_ratio)
    return ResizeGeometry(method, src_w, src_h, (int(target_size[0]), int(target_size[1])), values)


def resize_image(
    image: np.ndarray,
    resize: ResizeSpec,
    target_size: Sequence[int] | None,
    color_format: str,
    roi: Sequence[Any] | None = None,
) -> tuple[np.ndarray, ResizeGeometry]:
    """Resize one host frame with the method of `input.resize`. Return the image and the geometry.

    Implements: common.input
    Implements: pre.resize.none

    `image` is the host frame: 8-bit, 3 channels, BGR, in HWC layout. The result is BGR too, in
    `input.resize.compute_dtype`. `method: none` returns the frame unchanged. An array `pad_value`
    is in the order of `color_format`, so the function reverses it for `rgb`: the channels of the
    image change order only in the normalization.
    """
    src_h, src_w = image.shape[:2]
    geometry = resize_geometry(resize, target_size, src_w, src_h, roi)
    if resize.method == "none":
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"the frame must be uint8 with the shape (H, W, 3), not {image.dtype} {image.shape}")
        return image, geometry
    pixels = to_compute_dtype(image, str(resize.compute_dtype))
    flag = interpolation_flag(str(resize.interpolation))

    if resize.method == "letterbox":
        resized, _ = resize_letterbox.letterbox(
            pixels, target_size, str(resize.pad_position), str(resize.rounding), _bgr_border(resize.pad_value, color_format), flag
        )
    elif resize.method == "stretch":
        resized, _ = resize_stretch.stretch(pixels, target_size, flag)
    elif resize.method == "fit":
        resized, _ = resize_fit.fit(pixels, target_size, _bgr_border(resize.pad_value, color_format), flag)
    else:
        policy = resize.crop_policy
        resized, _ = resize_affine_crop.affine_crop(
            pixels, roi, target_size, policy.expand_ratio, policy.maintain_aspect_ratio, _bgr_border(policy.pad_value, color_format), flag
        )
    return resized, geometry


# At module level: beartype decorates a nested function again on each call of its outer function.
def _bgr_border(pad_value: Any, color_format: str) -> tuple[float, ...]:
    border = border_values(pad_value)
    return border[::-1] if color_format == "rgb" else border


def preprocess_image(
    image: np.ndarray,
    sidecar: SidecarModel,
    size: str,
    precision: str,
    roi: Sequence[Any] | None = None,
) -> tuple[np.ndarray, ResizeGeometry]:
    """Return the input tensor of one host frame, in CHW layout, and the geometry of its resize.

    Implements: common.input

    The steps are the resize of the size entry, the normalization of the precision and the cast to
    the `input.dtype` entry of the precision. The tensor has no batch axis. `roi` is the ROI of an
    `affine_crop` resize.
    """
    spec = sidecar.input
    if precision not in spec.dtype:
        raise ValueError(f"no precision {precision!r}; input.dtype has {list(spec.dtype)}")
    resized, geometry = resize_image(image, spec.resize, sidecar.size(size).target_size, spec.color_format, roi)
    values = normalize(resized, spec.normalization_for(precision), spec.color_format, spec.dtype[precision])
    return np.ascontiguousarray(values.transpose(2, 0, 1)), geometry
