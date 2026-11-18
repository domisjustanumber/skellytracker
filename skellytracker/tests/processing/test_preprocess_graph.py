"""The preprocess graph of `processing/pre/graph.py` against the CPU reference path.

Each built configuration runs on the CPU EP. Its `pixels` output must agree with `resize_image`
within the resize limit of `pre.resize.interpolation` (`within_resize_limit`), and its `tensor`
output must be the normalization of `preprocess_image` of those pixels. Each item is compared with
its own frame, also in one graph with camera slots of different sizes. The tests with the marker
`gpu` do the same on each installed NVIDIA EP pack, with no CPU node. The images are synthetic
noise.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import onnx
import pytest

from skellytracker.core.detectors.processing.pre.graph import (
    PreprocessGraphRefusedError,
    affine_crop_theta,
    build_preprocess_graph,
)
from skellytracker.core.detectors.processing.pre.normalize import normalize
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image, resize_image
from skellytracker.core.detectors.processing.pre.resize_interpolation import within_resize_limit
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.eps import build_session
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.tests.model_spec import sidecars

# (W, H): a downscale, an upscale and a portrait source (a left and a right pad) to 416 x 416. At
# 640 -> 416, cv2.INTER_NEAREST does not take the column floor(x * src_n / dst_n) at 16 of 416 columns.
# The fit scales are 0.65, 2.77 and 0.80. The affine_crop crops are larger and smaller than 256 x 192.
# 1920 x 1080: the float32 positions of an ONNX sampler lose accuracy on a large frame.
SOURCES = [(640, 480), (150, 100), (333, 517), (1920, 1080)]
BATCH = 2
SIZES = {"affine_crop": "m"}  # the size of the base sidecar of the method; "n" for the other methods
BASES = {"affine_crop": sidecars.simcc_keypoint_detector, "none": sidecars.packed_pose_detector}
CONFIGS = [
    pytest.param(method, interpolation, compute, normalization, color, id=f"{method}-{interpolation}-{compute}-{normalization}-{color}")
    for method in ("letterbox", "stretch", "fit", "affine_crop")
    for interpolation in ("linear", "cubic", "nearest")
    for compute in ("uint8", "float32")
    for normalization in ("none", "imagenet")
    for color in ("bgr", "rgb")
    if (method, interpolation) != ("affine_crop", "nearest")  # refused
    and (compute, interpolation) not in (("float32", "linear"), ("float32", "cubic"))  # refused
] + [
    pytest.param("none", None, None, normalization, color, id=f"none-{normalization}-{color}")
    for normalization in ("none", "imagenet")
    for color in ("bgr", "rgb")
]


def sidecar_of(method: str, interpolation: Any, compute: Any, normalization: Any = "none", color: str = "bgr", **changes: Any) -> SidecarModel:
    """A test sidecar with the method. Each color format also takes one value of each other field of the method."""
    size = SIZES.get(method, "n")
    resize: dict[str, Any] = {"method": method, "interpolation": interpolation, "compute_dtype": compute}
    if method == "letterbox":
        resize |= ({"pad_position": "center", "rounding": "half_up", "pad_value": [10, 128, 240]} if color == "bgr"
                   else {"pad_position": "top_left", "rounding": "half_even", "pad_value": 114})
    elif method == "fit":
        resize["pad_value"] = [10, 128, 240] if color == "bgr" else 114
    elif method == "affine_crop":
        resize["crop_policy"] = ({"expand_ratio": 1.25, "maintain_aspect_ratio": True, "pad_value": [10, 128, 240]} if color == "bgr"
                                 else {"expand_ratio": 1.0, "maintain_aspect_ratio": False, "pad_value": 114})
    data = {"input.normalization": normalization, "input.color_format": color, "input.dtype": {"fp32": "float32", "fp16": "float16"},
            f"sizes.{size}.onnx.precision_artifacts.fp16": {"filename": f"demo-{size}-fp16.onnx", "sha256": sidecars.SHA}}
    if method != "none":  # an absent resize is `method: none`
        data["input.resize"] = resize
    return SidecarModel.model_validate(sidecars.changed(BASES.get(method, sidecars.nms_detector)(), data | changes))


def rois_of(src_w: int, src_h: int) -> list[tuple[float, ...]]:
    """Three ROIs on one source: one in the image, one that leaves the image (border) and one that turns."""
    return [
        (0.5 * src_w, 0.5 * src_h, 0.4 * src_w, 0.5 * src_h, 0.0),
        (0.9 * src_w, 0.1 * src_h, 0.5 * src_w, 0.6 * src_h, 0.0),
        (0.3 * src_w, 0.6 * src_h, 0.3 * src_w, 0.3 * src_h, 0.4),
    ]


def mixed_rois(src_w: int, src_h: int) -> dict[str, tuple[float, ...]]:
    """ROIs that leave the image on each side: at the bottom and the right, the canvas pad starts."""
    return {
        "inside": (0.5 * src_w, 0.5 * src_h, 0.4 * src_w, 0.5 * src_h, 0.0),
        "top_left": (0.05 * src_w, 0.08 * src_h, 0.5 * src_w, 0.6 * src_h, 0.0),
        "bottom_right": (0.95 * src_w, 0.92 * src_h, 0.4 * src_w, 0.5 * src_h, 0.0),
        "rotated": (0.85 * src_w, 0.8 * src_h, 0.3 * src_w, 0.4 * src_h, 0.7),
        "tiny": (0.97 * src_w, 0.5 * src_h, 4.0, 3.0, 0.0),
    }


# Slots of different sizes, a portrait and a landscape slot among them. Slot 2 has no item; slots 0
# and 4 have more than one; the items are not in slot order.
MIXED = [(1280, 720), (480, 640), (97, 61), (640, 480), (1920, 1080)]
MIXED_INDEX = [4, 0, 3, 4, 1, 0]
MIXED_ITEMS = [(4, "bottom_right"), (1, "inside"), (0, "top_left"), (3, "bottom_right"), (1, "rotated"), (4, "tiny"),
               (0, "bottom_right"), (3, "rotated"), (1, "bottom_right"), (4, "top_left")]  # affine_crop: (slot, ROI)


MIXED_CONFIGS = [(method, interpolation) for method in ("letterbox", "stretch", "fit", "affine_crop")
                 for interpolation in ("linear", "cubic", "nearest") if (method, interpolation) != ("affine_crop", "nearest")]


def mixed_case(method: str) -> tuple[list[tuple[int, int]], list[int], list[Any]]:
    if method != "affine_crop":
        return MIXED, MIXED_INDEX, [None] * len(MIXED_INDEX)
    return MIXED, [slot for slot, _ in MIXED_ITEMS], [mixed_rois(*MIXED[slot])[name] for slot, name in MIXED_ITEMS]


def same_size_case(method: str, src_w: int, src_h: int) -> tuple[list[tuple[int, int]], list[int], list[Any]]:
    """Two slots of one size: for `affine_crop` the ROIs of `rois_of`, else one item for each slot."""
    if method != "affine_crop":
        return [(src_w, src_h)] * 2, [1, 0], [None] * BATCH
    return [(src_w, src_h)] * 2, [1, 0, 1], rois_of(src_w, src_h)


def frames(sources: list[tuple[int, int]]) -> list[np.ndarray]:
    return [np.random.default_rng((w, h, i)).integers(0, 256, (h, w, 3), dtype=np.uint8) for i, (w, h) in enumerate(sources)]


def check_graph(sidecar: SidecarModel, precision: str, sources: list[tuple[int, int]], index: list[int], rois: list[Any],
                execution_provider: str) -> float:
    """Run the graph on one EP and check it against the CPU reference path. Return the max difference.

    Item `k` is the frame of the slot `index[k]`, for `affine_crop` with `rois[k]` and the input
    `theta` from `affine_crop_theta`. Each item is compared with `preprocess_image` of its own frame.
    A slot with no item gets other content in a second run, which must give the same outputs.
    """
    spec = sidecar.input
    size = SIZES.get(spec.resize.method, "n")
    graph = build_preprocess_graph(sidecar, size, precision, sources, len(index))
    onnx.checker.check_model(graph)
    session, report = build_session(graph.SerializeToString(), execution_provider=execution_provider)
    assert report.cpu_nodes == 0 or execution_provider == "cpu"
    images = frames(sources)
    feeds: dict[str, np.ndarray] = {f"frame_{i}": image for i, image in enumerate(images)} | {"index": np.array(index, np.int64)}
    if spec.resize.method == "affine_crop":
        feeds["theta"] = affine_crop_theta(sidecar, size, sources, rois)
    tensor, pixels = session.run(["tensor", "pixels"], feeds)
    unused = [i for i in range(len(sources)) if i not in index]
    if unused:
        changed = feeds | {f"frame_{i}": 255 - images[i] for i in unused}
        for before, after in zip((tensor, pixels), session.run(["tensor", "pixels"], changed), strict=True):
            np.testing.assert_array_equal(before, after)
    compute, worst = str(spec.resize.compute_dtype or "uint8"), 0.0  # `none` gives the uint8 host frame
    for k, (slot, roi) in enumerate(zip(index, rois, strict=True)):
        image = images[slot]
        reference, _ = resize_image(image, spec.resize, sidecar.size(size).target_size, spec.color_format, roi)
        reference = (reference[..., ::-1] if spec.color_format == "rgb" else reference).transpose(2, 0, 1)
        difference, within = within_resize_limit(reference, pixels[k], compute)
        assert within, difference
        worst = max(worst, difference)
        expected, _ = preprocess_image(image, sidecar, size, precision, roi)
        assert tensor[k].shape == expected.shape and tensor[k].dtype == expected.dtype
        bgr = pixels[k].transpose(1, 2, 0)
        bgr = bgr[..., ::-1] if spec.color_format == "rgb" else bgr
        normalized = normalize(np.ascontiguousarray(bgr), spec.normalization_for(precision), spec.color_format, spec.dtype[precision])
        np.testing.assert_allclose(tensor[k].astype(np.float32), normalized.transpose(2, 0, 1).astype(np.float32), rtol=1e-6, atol=1e-5)
    return worst


@pytest.mark.parametrize("src_w, src_h", SOURCES)
@pytest.mark.parametrize(("method", "interpolation", "compute", "normalization", "color"), CONFIGS)
def test_the_graph_on_the_cpu_ep_is_within_the_resize_limit(method, interpolation, compute, normalization, color, src_w, src_h) -> None:
    sidecar = sidecar_of(method, interpolation, compute, normalization, color)
    worst = check_graph(sidecar, "fp32", *same_size_case(method, src_w, src_h), "cpu")
    print(f"max difference {worst:.6f}")
    if interpolation in ("nearest", None):  # the index tables come from the OpenCV call of the CPU path; none: no resize
        assert worst == 0.0


@pytest.mark.parametrize("color", ["bgr", "rgb"])
@pytest.mark.parametrize(("method", "interpolation"), MIXED_CONFIGS)
def test_one_graph_takes_slots_of_different_sizes_within_the_resize_limit(method: str, interpolation: str, color: str) -> None:
    worst = check_graph(sidecar_of(method, interpolation, "uint8", "imagenet", color), "fp32", *mixed_case(method), "cpu")
    print(f"max difference {worst:.6f}")
    assert interpolation != "nearest" or worst == 0.0


def test_the_graph_refuses_none_with_slots_of_different_sizes() -> None:
    with pytest.raises(PreprocessGraphRefusedError, match="'none' with different source sizes"):
        build_preprocess_graph(sidecar_of("none", None, None), "n", "fp32", [(640, 480), (480, 640)], BATCH)


@pytest.mark.parametrize("src_w, src_h", [(1280, 720), (97, 61), (416, 416), (500, 375), (277, 999)])
@pytest.mark.parametrize("compute", ["uint8", "float32"])
def test_nearest_fit_takes_the_pixels_of_the_cpu_path_at_more_scales(compute: str, src_w: int, src_h: int) -> None:
    assert check_graph(sidecar_of("fit", "nearest", compute), "fp32", *same_size_case("fit", src_w, src_h), "cpu") == 0.0


def test_the_graph_gives_the_input_dtype_of_the_precision() -> None:
    check_graph(sidecar_of("letterbox", "linear", "uint8", "imagenet"), "fp16", *same_size_case("letterbox", 640, 480), "cpu")


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        pytest.param({"input.resize": {"method": "letterbox", "interpolation": "area"}}, "interpolation 'area'", id="area"),
        pytest.param({"input.normalization": "unit_float"}, "normalization 'unit_float'", id="unit_float"),
        pytest.param({"input.normalization": {"mode": "custom", "scale": 2.0}}, "normalization", id="custom"),
        pytest.param({"input.dtype": {"fp32": "uint8"}}, "input dtype 'uint8'", id="uint8-input"),
    ],
)
def test_the_graph_refuses_each_configuration_that_it_does_not_build(changes: dict[str, Any], match: str) -> None:
    sidecar = SidecarModel.model_validate(sidecars.changed(sidecars.nms_detector(), changes))
    with pytest.raises(PreprocessGraphRefusedError, match=match):
        build_preprocess_graph(sidecar, "n", "fp32", [(640, 480)], BATCH)


def test_the_graph_refuses_nearest_with_affine_crop() -> None:
    with pytest.raises(PreprocessGraphRefusedError, match="'nearest' with the method 'affine_crop'"):
        build_preprocess_graph(sidecar_of("affine_crop", "nearest", "uint8"), "m", "fp32", [(640, 480)], BATCH)


@pytest.mark.parametrize("interpolation", ["linear", "cubic"])
@pytest.mark.parametrize("method", ["letterbox", "stretch", "fit", "affine_crop"])
def test_the_graph_refuses_float32_with_linear_or_cubic(method: str, interpolation: str) -> None:
    with pytest.raises(PreprocessGraphRefusedError, match=f"compute dtype 'float32' with the interpolation '{interpolation}'"):
        build_preprocess_graph(sidecar_of(method, interpolation, "float32"), SIZES.get(method, "n"), "fp32", [(640, 480)], BATCH)


@pytest.mark.gpu
@pytest.mark.parametrize("execution_provider", ["cuda", "trt-rtx"])
@pytest.mark.parametrize(("method", "interpolation", "compute"), [
    ("letterbox", "linear", "uint8"), ("stretch", "linear", "uint8"), ("fit", "linear", "uint8"),
    ("affine_crop", "linear", "uint8"), ("letterbox", "nearest", "uint8"), ("fit", "nearest", "uint8"), ("none", None, None),
])
def test_the_graph_on_each_nvidia_ep_is_within_the_resize_limit_on_a_4k_frame(method, interpolation, compute, execution_provider) -> None:
    try:
        worst = check_graph(sidecar_of(method, interpolation, compute), "fp32", *same_size_case(method, 3840, 2160), execution_provider)
    except EpUnavailableError as error:
        pytest.skip(f"{execution_provider} is not installed: {error}")
    print(f"{execution_provider} 3840x2160 max difference {worst:.6f}")
    assert interpolation not in ("nearest", None) or worst == 0.0


@pytest.mark.gpu
@pytest.mark.parametrize("execution_provider", ["cuda", "trt-rtx"])
@pytest.mark.parametrize("color", ["bgr", "rgb"])
@pytest.mark.parametrize(("method", "interpolation"), MIXED_CONFIGS)
def test_one_graph_on_each_nvidia_ep_takes_slots_of_different_sizes(method, interpolation, color, execution_provider) -> None:
    try:
        worst = check_graph(sidecar_of(method, interpolation, "uint8", "imagenet", color), "fp32", *mixed_case(method), execution_provider)
    except EpUnavailableError as error:
        pytest.skip(f"{execution_provider} is not installed: {error}")
    print(f"{execution_provider} mixed slots max difference {worst:.6f}")
    assert interpolation != "nearest" or worst == 0.0


@pytest.mark.gpu
@pytest.mark.parametrize("execution_provider", ["cuda", "trt-rtx"])
@pytest.mark.parametrize(("method", "interpolation", "compute", "normalization", "color"), CONFIGS)
def test_the_graph_on_each_nvidia_ep_is_within_the_resize_limit(method, interpolation, compute, normalization, color, execution_provider) -> None:
    sidecar = sidecar_of(method, interpolation, compute, normalization, color)
    for src_w, src_h in SOURCES:
        try:
            worst = check_graph(sidecar, "fp32", *same_size_case(method, src_w, src_h), execution_provider)
        except EpUnavailableError as error:
            pytest.skip(f"{execution_provider} is not installed: {error}")
        print(f"{execution_provider} {src_w}x{src_h} max difference {worst:.6f}")
        assert interpolation not in ("nearest", None) or worst == 0.0
