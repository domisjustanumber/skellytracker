"""The preprocess graph of `processing/pre/graph.py` against the CPU reference path.

Each built configuration runs on the CPU EP. Its `pixels` output must agree with `resize_image`
within the resize limit of `pre.resize.interpolation` (`within_resize_limit`), and its `tensor`
output must be the normalization of `preprocess_image` of those pixels. The test with the marker
`gpu` does the same on each installed NVIDIA EP pack, with no CPU node. The images are synthetic
noise.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import onnx
import pytest

from skellytracker.core.detectors.processing.pre.graph import PreprocessGraphRefusedError, build_preprocess_graph
from skellytracker.core.detectors.processing.pre.normalize import normalize
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image, resize_image
from skellytracker.core.detectors.processing.pre.resize_interpolation import within_resize_limit
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.eps import build_session
from skellytracker.core.model_spec.model import SidecarModel
from skellytracker.tests.model_spec import sidecars

# (W, H): a downscale, an upscale and a portrait source (a left and a right pad) to 416 x 416. At
# 640 -> 416, cv2.INTER_NEAREST does not take the column floor(x * src_n / dst_n) at 16 of 416 columns.
SOURCES = [(640, 480), (150, 100), (333, 517)]
BATCH = 2
FP16 = {"sizes.n.onnx.precision_artifacts.fp16": {"filename": "demo-n-fp16.onnx", "sha256": sidecars.SHA}}
CONFIGS = [
    pytest.param(method, interpolation, compute, normalization, color, id=f"{method}-{interpolation}-{compute}-{normalization}-{color}")
    for method in ("letterbox", "stretch")
    for interpolation in ("linear", "cubic", "nearest")
    for compute in ("uint8", "float32")
    for normalization in ("none", "imagenet")
    for color in ("bgr", "rgb")
]


def sidecar_of(method: str, interpolation: str, compute: str, normalization: Any = "none", color: str = "bgr", **changes: Any) -> SidecarModel:
    resize: dict[str, Any] = {"method": method, "interpolation": interpolation, "compute_dtype": compute}
    if method == "letterbox":  # each color format also takes one of the two values of each letterbox field
        resize |= ({"pad_position": "center", "rounding": "half_up", "pad_value": [10, 128, 240]} if color == "bgr"
                   else {"pad_position": "top_left", "rounding": "half_even", "pad_value": 114})
    data = {"input.resize": resize, "input.normalization": normalization, "input.color_format": color,
            "input.dtype": {"fp32": "float32", "fp16": "float16"}, **FP16, **changes}
    return SidecarModel.model_validate(sidecars.changed(sidecars.nms_detector(), data))


def frames(src_w: int, src_h: int) -> np.ndarray:
    return np.random.default_rng(src_w).integers(0, 256, (BATCH, src_h, src_w, 3), dtype=np.uint8)


def check_graph(sidecar: SidecarModel, precision: str, src_w: int, src_h: int, execution_provider: str) -> float:
    """Run the graph on one EP and check it against the CPU reference path. Return the max difference."""
    graph = build_preprocess_graph(sidecar, "n", precision, src_w, src_h, BATCH)
    onnx.checker.check_model(graph)
    session, report = build_session(graph.SerializeToString(), execution_provider=execution_provider)
    assert report.cpu_nodes == 0 or execution_provider == "cpu"
    images = frames(src_w, src_h)
    tensor, pixels = session.run(["tensor", "pixels"], {"frames": images})
    spec, worst = sidecar.input, 0.0
    for k, image in enumerate(images):
        reference, _ = resize_image(image, spec.resize, sidecar.size("n").target_size, spec.color_format)
        reference = (reference[..., ::-1] if spec.color_format == "rgb" else reference).transpose(2, 0, 1)
        difference, within = within_resize_limit(reference, pixels[k], str(spec.resize.compute_dtype))
        assert within, difference
        worst = max(worst, difference)
        expected, _ = preprocess_image(image, sidecar, "n", precision)
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
    worst = check_graph(sidecar, "fp32", src_w, src_h, "cpu")
    print(f"max difference {worst:.6f}")
    if interpolation == "nearest":  # the index tables come from the OpenCV call of the CPU path
        assert worst == 0.0


def test_the_graph_gives_the_input_dtype_of_the_precision() -> None:
    check_graph(sidecar_of("letterbox", "linear", "uint8", "imagenet"), "fp16", 640, 480, "cpu")


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        pytest.param({"input.resize": {"method": "letterbox", "interpolation": "area"}}, "interpolation 'area'", id="area"),
        pytest.param({"input.resize": {"method": "fit", "pad_value": 114}}, "method 'fit'", id="fit"),
        pytest.param({"input.normalization": "unit_float"}, "normalization 'unit_float'", id="unit_float"),
        pytest.param({"input.normalization": {"mode": "custom", "scale": 2.0}}, "normalization", id="custom"),
        pytest.param({"input.dtype": {"fp32": "uint8"}}, "input dtype 'uint8'", id="uint8-input"),
    ],
)
def test_the_graph_refuses_each_configuration_that_it_does_not_build(changes: dict[str, Any], match: str) -> None:
    sidecar = SidecarModel.model_validate(sidecars.changed(sidecars.nms_detector(), changes))
    with pytest.raises(PreprocessGraphRefusedError, match=match):
        build_preprocess_graph(sidecar, "n", "fp32", 640, 480, BATCH)


def test_the_graph_refuses_affine_crop() -> None:
    sidecar = SidecarModel.model_validate(sidecars.simcc_keypoint_detector())
    with pytest.raises(PreprocessGraphRefusedError, match="method 'affine_crop'"):
        build_preprocess_graph(sidecar, "m", "fp32", 640, 480, BATCH)


@pytest.mark.gpu
@pytest.mark.parametrize("execution_provider", ["cuda", "trt-rtx"])
@pytest.mark.parametrize(("method", "interpolation", "compute", "normalization", "color"), CONFIGS)
def test_the_graph_on_each_nvidia_ep_is_within_the_resize_limit(method, interpolation, compute, normalization, color, execution_provider) -> None:
    sidecar = sidecar_of(method, interpolation, compute, normalization, color)
    for src_w, src_h in SOURCES:
        try:
            worst = check_graph(sidecar, "fp32", src_w, src_h, execution_provider)
        except EpUnavailableError as error:
            pytest.skip(f"{execution_provider} is not installed: {error}")
        print(f"{execution_provider} {src_w}x{src_h} max difference {worst:.6f}")
        assert interpolation != "nearest" or worst == 0.0
