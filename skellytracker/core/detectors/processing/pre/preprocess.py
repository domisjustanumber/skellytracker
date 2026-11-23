"""The preprocessing of one host frame from a loaded sidecar: the resize dispatcher and the input tensor.

`resize_image` calls the module of the resize method of the sidecar. `preprocess_image` also
normalizes the result and gives the tensor of one image in CHW layout. `BatchPreprocessor` gives
the tensors of N images as one batch, in an array that it uses again at each call.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from skellytracker.core.detectors.processing.pre import (
    resize_affine_crop,
    resize_fit,
    resize_letterbox,
    resize_stretch,
)
from skellytracker.core.detectors.processing.pre.normalize import (
    IMAGENET_MEAN_RGB,
    IMAGENET_STD_RGB,
    INPUT_DTYPES,
    normalize,
)
from skellytracker.core.detectors.processing.pre.resize_interpolation import (
    COMPUTE_DTYPES,
    border_values,
    interpolation_flag,
    to_compute_dtype,
)
from skellytracker.core.model_spec.model import CustomNormalization, ResizeSpec, SidecarModel


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


class BatchPreprocessor:
    """The input batch of one model input: the tensors of `preprocess_image`, stacked, in an array that each call uses again.

    Implements: common.input

    One object serves one sidecar, one size and one precision. `preprocess` writes the tensor of
    each item into its slot of one `(N, 3, H, W)` array, in the `input.dtype` of the precision, and
    returns that array. Each value is the value of `preprocess_image`: each step is the same
    operation in the same dtype and in the same order. The next call writes into the same array.
    A caller that keeps the batch after its model call must copy it. For `letterbox`, the pad of a
    slot gets its value one time, and it stays while the geometry of that slot does not change.
    The object is not thread-safe.
    """

    def __init__(self, sidecar: SidecarModel, size: str, precision: str) -> None:
        spec = sidecar.input
        if precision not in spec.dtype:
            raise ValueError(f"no precision {precision!r}; input.dtype has {list(spec.dtype)}")
        resize = spec.resize
        self.resize, self.target_size = resize, sidecar.size(size).target_size
        self.method, self.rgb = resize.method, spec.color_format == "rgb"
        self.dtype = INPUT_DTYPES[spec.dtype[precision]]
        normalization = spec.normalization_for(precision)
        # One pixel of the pad through `normalize`: the pad values of letterbox, and the errors of `normalize` now.
        self.flag = self.border = None
        compute = np.uint8
        if self.method != "none":
            compute = COMPUTE_DTYPES[str(resize.compute_dtype)]
            self.flag = interpolation_flag(str(resize.interpolation))
            pad = resize.crop_policy.pad_value if self.method == "affine_crop" else resize.pad_value
            if self.method != "stretch":
                self.border = _bgr_border(pad, spec.color_format)
        pixel = np.asarray(self.border or (0.0, 0.0, 0.0), np.float64).astype(compute).reshape(1, 1, 3)
        self.pad = normalize(pixel, normalization, spec.color_format, spec.dtype[precision]).reshape(3, 1, 1)
        # The constants of each output channel, as float32, in the order of `color_format`.
        self.mode = "custom" if isinstance(normalization, CustomNormalization) else normalization
        self.scale = self.mean = self.std = None
        if isinstance(normalization, CustomNormalization):
            self.scale, self.mean, self.std = np.float32(normalization.scale), normalization.mean, normalization.std
        elif normalization == "imagenet":
            order = slice(None) if self.rgb else slice(None, None, -1)
            self.mean, self.std = IMAGENET_MEAN_RGB[order], IMAGENET_STD_RGB[order]
        if self.mean is not None:
            self.mean, self.std = [np.float32(value) for value in self.mean], [np.float32(value) for value in self.std]
        self.batch: np.ndarray | None = None
        self.regions: list[tuple[int, int, int, int] | None] = []  # letterbox: the content region with a valid pad, by slot
        self.resized: list[np.ndarray | None] = []  # letterbox: the resize buffer of each slot
        self.canvas: np.ndarray | None = None  # the warp or stretch buffer of the other methods
        self.work = np.empty(0, np.float32)  # the float32 plane of an output in float16 or uint8

    def preprocess(
        self, images: Sequence[np.ndarray], rois: Sequence[Sequence[Any]] | None = None
    ) -> tuple[np.ndarray, list[ResizeGeometry]]:
        """Return the batch of the images and the geometry of each image, as `preprocess_image` gives them.

        Implements: common.input

        `rois[i]` is the ROI of `images[i]` for `affine_crop`. The batch is a view of the array of
        the object: the next call changes it. The errors are the errors of `preprocess_image` and
        of `np.stack` for the same input.
        """
        if rois is not None and len(rois) != len(images):
            raise ValueError(f"images and rois need one length: {len(images)} and {len(rois)}")
        geometries, sources = [], []
        for index, image in enumerate(images):
            src_h, src_w = image.shape[:2]
            geometries.append(resize_geometry(self.resize, self.target_size, src_w, src_h, None if rois is None else rois[index]))
            if self.method == "none":
                if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                    raise ValueError(f"the frame must be uint8 with the shape (H, W, 3), not {image.dtype} {image.shape}")
                sources.append(np.ascontiguousarray(image))
            else:
                sources.append(to_compute_dtype(image, str(self.resize.compute_dtype)))
        if not geometries:
            raise ValueError("need at least one array to stack")
        shape = (3, *geometries[0].input_size)
        if any(geometry.input_size != geometries[0].input_size for geometry in geometries):
            raise ValueError("all input arrays must have the same shape")
        batch = self._batch(len(images), shape)
        if batch.size:
            for slot, (source, geometry) in enumerate(zip(sources, geometries, strict=True)):
                self._write(slot, source, geometry)
        return batch, geometries

    def _batch(self, count: int, shape: tuple[int, int, int]) -> np.ndarray:
        if self.batch is None or self.batch.shape[1:] != shape or len(self.batch) < count:
            self.batch = np.empty((count, *shape), self.dtype)
            self.regions, self.resized = [None] * count, [None] * count
        return self.batch[:count]

    def _write(self, slot: int, source: np.ndarray, geometry: ResizeGeometry) -> None:
        out, (t_h, t_w), values = self.batch[slot], geometry.input_size, geometry.values
        if self.method == "letterbox":
            n_w, n_h, left, top = values["n_w"], values["n_h"], values["left"], values["top"]
            if self.regions[slot] != (top, left, n_h, n_w):
                out[...] = self.pad
                self.regions[slot] = (top, left, n_h, n_w)
            buffer = self.resized[slot]
            if buffer is None or buffer.shape != (n_h, n_w, 3) or buffer.dtype != source.dtype:
                buffer = self.resized[slot] = np.empty((n_h, n_w, 3), source.dtype)
            content = cv2.resize(source, (n_w, n_h), dst=buffer, interpolation=self.flag)
            out = out[:, top : top + n_h, left : left + n_w]
        elif self.method == "none":
            content = source
        else:
            if self.canvas is None or self.canvas.dtype != source.dtype:
                self.canvas = np.empty((t_h, t_w, 3), source.dtype)
            if self.method == "stretch":
                content = cv2.resize(source, (t_w, t_h), dst=self.canvas, interpolation=self.flag)
            else:
                if self.method == "fit":
                    matrix = np.array([[values["scale"], 0.0, values["left"]], [0.0, values["scale"], values["top"]]], dtype=np.float64)
                else:
                    matrix = values["matrix"]
                content = cv2.warpAffine(
                    source, matrix, (t_w, t_h), dst=self.canvas, flags=self.flag, borderMode=cv2.BORDER_CONSTANT, borderValue=self.border
                )
        planes = cv2.split(content)
        for channel in range(3):
            self._write_plane(planes[2 - channel] if self.rgb else planes[channel], out[channel], channel)

    def _write_plane(self, plane: np.ndarray, out: np.ndarray, channel: int) -> None:
        """Normalize one BGR plane into one output channel, with the float32 steps of `normalize`."""
        if self.mode == "none":
            out[...] = plane  # the 0-255 values are exact in float16 too, so the float32 step of `normalize` changes nothing
            return
        work = out
        if self.dtype != np.float32:
            if self.work.size < plane.size:
                self.work = np.empty(plane.size, np.float32)
            work = self.work[: plane.size].reshape(plane.shape)
        if self.mode == "unit_float":
            np.divide(plane, np.float32(255.0), out=work, dtype=np.float32)
        elif self.mode == "imagenet":
            np.subtract(plane, self.mean[channel], out=work, dtype=np.float32)
            np.divide(work, self.std[channel], out=work)
        else:
            np.multiply(plane, self.scale, out=work, dtype=np.float32)
            np.subtract(work, self.mean[channel], out=work)
            np.divide(work, self.std[channel], out=work)
        if work is not out:
            out[...] = work
