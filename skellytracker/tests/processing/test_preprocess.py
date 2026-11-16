"""The spec preprocessing modules of `processing/pre/`: each resize method, the normalization and the dispatcher.

`tools/tests/test_vectors.py` runs the numeric vector cases of each section. These tests cover the
image functions, the dispatcher and the cases that the vector test does not run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
import yaml

from skellytracker.core.detectors.processing.pre import resize_affine_crop, resize_fit, resize_letterbox, resize_stretch
from skellytracker.core.detectors.processing.pre.normalize import normalize
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image, resize_geometry, resize_image
from skellytracker.core.detectors.processing.pre.resize_interpolation import border_values, to_compute_dtype
from skellytracker.core.model_spec.model import ResizeSpec, SidecarModel
from skellytracker.tests.model_spec import sidecars

VECTORS = Path(__file__).resolve().parents[3] / "specs" / "model-sidecar" / "vectors"
needs_vectors = pytest.mark.skipif(not VECTORS.is_dir(), reason="the vector files are not in an installed package")


def vector_cases(section: str, *ids: str) -> list[Any]:
    if not VECTORS.is_dir():
        return []
    cases = yaml.safe_load((VECTORS / f"{section}.yaml").read_text(encoding="utf-8"))["cases"]
    return [pytest.param(case, id=case["id"]) for case in cases if case.get("function") != "none" and (not ids or case["id"] in ids)]


def frame(height: int = 48, width: int = 64) -> np.ndarray:
    """A BGR frame with a different gradient in each channel."""
    rows, columns = np.mgrid[0:height, 0:width]
    return np.stack([rows * 3 % 256, columns * 2 % 256, (rows + columns) % 256], axis=-1).astype(np.uint8)


def model(base: str, changes: dict[str, Any]) -> SidecarModel:
    return SidecarModel.model_validate(sidecars.changed(sidecars.BASES[base](), changes))


# ---------------------------------------------------------------------------
# Each resize method
# ---------------------------------------------------------------------------


def test_letterbox_pads_each_channel_and_handles_a_source_1_pixel_wide() -> None:
    canvas, geometry = resize_letterbox.letterbox(frame(40, 1), [64, 64], "center", "half_even", (1.0, 2.0, 3.0), cv2.INTER_LINEAR)
    assert geometry == {"n_w": 2, "n_h": 64, "left": 31, "top": 0}
    assert canvas.shape == (64, 64, 3) and canvas.dtype == np.uint8
    assert canvas[0, 0].tolist() == [1, 2, 3] and canvas[63, 63].tolist() == [1, 2, 3]


@needs_vectors
@pytest.mark.parametrize("case", vector_cases("pre.resize.stretch"))
def test_stretch_agrees_with_each_numeric_vector_case(case: dict[str, Any]) -> None:
    """The stretch vector file is a fixture of `tools/tests/test_land_fill.py`, so its cases list no entry."""
    params, given = case["params"], case["input"]
    if case.get("function") == "inverse":
        result = resize_stretch.inverse_points(given["model_xy"], params["target_size"], given["src_w"], given["src_h"])
        assert result.tolist() == pytest.approx(case["expect"]["source_xy"], abs=1e-4)
    else:
        image = np.zeros((given["src_h"], given["src_w"], 3), dtype=np.uint8)
        resized, geometry = resize_stretch.stretch(image, params["target_size"], cv2.INTER_LINEAR)
        assert resized.shape[:2] == tuple(params["target_size"])
        assert geometry == pytest.approx(case["expect"], abs=1e-4)


def test_fit_fills_each_channel_of_the_border_and_has_no_default_pad() -> None:
    canvas, geometry = resize_fit.fit(frame(), [64, 64], border_values(114), cv2.INTER_LINEAR)
    assert geometry == {"scale": 1.0, "left": 0.0, "top": 8.0}
    assert canvas[0, 0].tolist() == [114, 114, 114]
    assert border_values([1, 2, 3]) == (1.0, 2.0, 3.0)
    with pytest.raises(TypeError):
        resize_fit.fit(frame(), [64, 64], interpolation=cv2.INTER_LINEAR)  # type: ignore[call-arg]


@needs_vectors
@pytest.mark.parametrize(
    "case",
    vector_cases(
        "pre.resize.affine_crop",
        "coco-tall-box-float32-steps",
        "coco-wide-box-float32-steps",
        "coco-box-target-384x288-float32-steps",
    ),
)
def test_the_affine_crop_matrix_of_the_three_coco_cases_is_the_mmpose_matrix(case: dict[str, Any]) -> None:
    """The golden test of ADR-3S5G: `M` agrees within 1e-6 with the float32 steps of mmpose v1.3.2."""
    params = case["params"]
    geometry = resize_affine_crop.crop_geometry(
        resize_affine_crop.roi_from_box(case["input"]["bbox_xyxy"]),
        params["target_size"],
        float(params["expand_ratio"]),
        params["maintain_aspect_ratio"],
    )
    assert geometry["matrix"].dtype == np.float64
    assert geometry["matrix"].tolist() == [pytest.approx(row, abs=1e-6) for row in case["expect"]["matrix"]]


def test_the_second_warp_point_is_left_of_the_centre_and_a_rotation_turns_it() -> None:
    size = resize_affine_crop.crop_size(resize_affine_crop.roi_values([100, 100, 40, 40, 0]), [64, 64], 1.0, True)
    src, _ = resize_affine_crop.warp_points(size, 0.0, [64, 64], True)
    assert src[1].tolist() == [80.0, 100.0]
    src, _ = resize_affine_crop.warp_points(size, np.pi / 2, [64, 64], True)
    assert src[1].tolist() == pytest.approx([100.0, 80.0])


def test_an_affine_crop_round_trip_through_unproject() -> None:
    geometry = resize_affine_crop.crop_geometry([32.0, 24.0, 20.0, 30.0, 0.3], [64, 48], 1.25, False)
    corners = np.array([[0.0, 0.0], [48.0, 64.0], [24.0, 32.0]])
    source = resize_affine_crop.unproject(corners, geometry["matrix"])
    assert source[2].tolist() == pytest.approx([32.0, 24.0])
    back = source @ geometry["matrix"][:, :2].T + geometry["matrix"][:, 2]
    assert back == pytest.approx(corners)


# ---------------------------------------------------------------------------
# The compute dtype and the normalization
# ---------------------------------------------------------------------------


def test_a_float32_resize_keeps_the_fractions_and_a_uint8_resize_rounds() -> None:
    image = frame(4, 4)
    as_float, _ = resize_stretch.stretch(to_compute_dtype(image, "float32"), [6, 6], cv2.INTER_LINEAR)
    as_uint8, _ = resize_stretch.stretch(to_compute_dtype(image, "uint8"), [6, 6], cv2.INTER_LINEAR)
    assert as_float.dtype == np.float32 and as_uint8.dtype == np.uint8
    assert np.any(as_float != np.round(as_float))
    assert np.abs(as_float - as_uint8).max() < 1.0  # the 8-bit filter of OpenCV rounds each pixel
    with pytest.raises(ValueError, match="uint8"):
        to_compute_dtype(image.astype(np.float32), "uint8")


@pytest.mark.parametrize("dtype", ["float32", "float16", "uint8"])
def test_each_mode_casts_to_the_input_dtype_as_the_last_step(dtype: str) -> None:
    pixels = frame(2, 2)
    mode = "none" if dtype == "uint8" else "imagenet"
    result = normalize(pixels, mode, "rgb", dtype)
    assert result.dtype == np.dtype(dtype)
    assert np.array_equal(result, normalize(pixels, mode, "rgb", None).astype(dtype))
    assert np.array_equal(normalize(pixels, "none", "rgb", "uint8"), pixels[..., ::-1])


def test_imagenet_uses_the_statistics_of_the_colour_in_each_channel_order() -> None:
    mean_bgr = np.array([[103.53, 116.28, 123.675]], dtype=np.float32)
    assert normalize(mean_bgr, "imagenet", "bgr", "float32") == pytest.approx(0, abs=1e-6)
    assert normalize(mean_bgr, "imagenet", "rgb", "float32") == pytest.approx(0, abs=1e-6)


# ---------------------------------------------------------------------------
# The dispatcher
# ---------------------------------------------------------------------------


def test_the_dispatcher_runs_the_method_of_the_sidecar() -> None:
    image = frame()
    letterbox = ResizeSpec(method="letterbox", pad_position="top_left", rounding="half_up")
    resized, geometry = resize_image(image, letterbox, [32, 32], "bgr")
    assert geometry.method == "letterbox" and geometry.input_size == (32, 32)
    assert geometry.values == {"n_w": 32, "n_h": 24, "left": 0, "top": 0}
    assert resized[31, 0].tolist() == [114, 114, 114]

    resized, geometry = resize_image(image, ResizeSpec(method="stretch"), [32, 16], "bgr")
    assert resized.shape == (32, 16, 3) and (geometry.src_w, geometry.src_h) == (64, 48)

    resized, geometry = resize_image(image, ResizeSpec(method="fit", pad_value=7), [64, 64], "bgr")
    assert resized[0, 0].tolist() == [7, 7, 7] and geometry.values["top"] == 8.0

    resized, geometry = resize_image(image, ResizeSpec(method="none"), None, "bgr")
    assert resized is image and geometry.input_size == (48, 64)

    crop = ResizeSpec(method="affine_crop", crop_policy={"pad_value": 9})
    resized, geometry = resize_image(image, crop, [32, 24], "bgr", roi=resize_affine_crop.roi_from_box([-40, -40, 0, 0]))
    assert resized.shape == (32, 24, 3) and geometry.values["matrix"].shape == (2, 3)
    assert resized[0, 0].tolist() == [9, 9, 9]


def test_an_array_pad_is_in_the_order_of_color_format() -> None:
    """The image stays BGR until the normalization, so the dispatcher reverses the pad for rgb."""
    resize = ResizeSpec(method="letterbox", pad_position="top_left", rounding="half_up", pad_value=[10, 20, 30])
    for color_format, bgr_pad in (("bgr", [10, 20, 30]), ("rgb", [30, 20, 10])):
        resized, _ = resize_image(frame(), resize, [32, 32], color_format)
        assert resized[31, 0].tolist() == bgr_pad
        assert normalize(resized, "none", color_format, "uint8")[31, 0].tolist() == [10, 20, 30]


def test_an_roi_goes_with_affine_crop_only() -> None:
    with pytest.raises(ValueError, match="ROI"):
        resize_geometry(ResizeSpec(method="affine_crop"), [32, 24], 64, 48)
    with pytest.raises(ValueError, match="ROI"):
        resize_geometry(ResizeSpec(method="stretch"), [32, 24], 64, 48, roi=[1.0, 1.0, 2.0, 2.0, 0.0])


def test_preprocess_image_gives_the_chw_tensor_in_the_input_dtype_of_the_precision() -> None:
    sidecar = model("nms", {"input.dtype": {"fp32": "float32", "fp16": "float16"}, "input.normalization": "unit_float",
                            "sizes.n.onnx.precision_artifacts.fp16": {"filename": "demo-n-fp16.onnx", "sha256": sidecars.SHA}})
    image = frame()
    tensor, geometry = preprocess_image(image, sidecar, "n", "fp32")
    assert tensor.shape == (3, 416, 416) and tensor.dtype == np.float32 and tensor.flags.c_contiguous
    assert geometry.values == {"n_w": 416, "n_h": 312, "left": 0, "top": 0}
    assert tensor[:, 415, 0].tolist() == pytest.approx([114 / 255] * 3)
    half, _ = preprocess_image(image, sidecar, "n", "fp16")
    assert half.dtype == np.float16 and np.array_equal(half, tensor.astype(np.float16))
    with pytest.raises(ValueError, match="no size"):
        preprocess_image(image, sidecar, "x", "fp32")


def test_preprocess_image_crops_an_roi_and_puts_the_channels_in_rgb_order() -> None:
    sidecar = model("simcc", {"input.normalization": "none"})
    image = frame()
    tensor, geometry = preprocess_image(image, sidecar, "m", "fp32", roi=[32.0, 24.0, 12.0, 16.0, 0.0])
    assert tensor.shape == (3, 256, 192) and geometry.method == "affine_crop"
    # The centre of the ROI goes to the centre of the crop: pixel (96, 128) holds the R, G, B of the source.
    assert tensor[:, 128, 96].tolist() == pytest.approx(image[24, 32, ::-1].tolist(), abs=1.0)
