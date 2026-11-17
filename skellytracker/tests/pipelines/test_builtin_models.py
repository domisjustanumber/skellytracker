"""The built-in `yolox-rtmw-wholebody` with the real models of `core/model_zoo/`, through `start_pipeline`.

Git does not track the ONNX files. A test skips when an ONNX file of its run is not present. The
tests with the marker `gpu` are opt-in (`pytest -m gpu`): they need an NVIDIA GPU and the EP packs
`cuda` and `trt-rtx` in the EP store.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest

from skellytracker.core.detectors import catalog
from skellytracker.core.errors import MissingDependencyError
from skellytracker.core.model_spec import artifacts
from skellytracker.core.pipelines import Frame, annotate, load_pipeline, start_pipeline, to_canonical

BUILT_IN = "yolox-rtmw-wholebody@skellytracker"
FRAMES = 3


@pytest.fixture(autouse=True)
def private_folders(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    # One hash cache for the test run: the catalog hashes each present ONNX file one time.
    cache = tmp_path_factory.getbasetemp() / "model-zoo-hash-cache.json"
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: cache)
    monkeypatch.delenv(catalog.USER_ROOT_VARIABLE, raising=False)


def start_or_skip(running_mode: str, execution_provider: str):  # noqa: ANN201
    try:
        return start_pipeline(load_pipeline(BUILT_IN), camera_ids=[0], running_mode=running_mode, execution_provider=execution_provider)
    except MissingDependencyError as error:  # only an absent ONNX file: each other start error is a failure
        pytest.skip(f"an ONNX file is not in core/model_zoo/: {error}")


def read_frames(path: Path, count: int) -> list[np.ndarray]:
    capture = cv2.VideoCapture(str(path))
    frames = [capture.read()[1] for _ in range(count)]
    capture.release()
    assert all(frame is not None for frame in frames)
    return frames


def check_result(run: Any, result: dict[str, Any], image: np.ndarray) -> None:
    """Check one result with a person: the shapes, the finite points, the box, the canonical form and the annotator."""
    height, width = image.shape[:2]
    schema = run.output_schema["wholebody"]
    points, box, crop = result["wholebody"], result["detector_box"], result["crop_box"]
    assert (result["image_width"], result["image_height"]) == (width, height)
    assert points.xy.shape == (1, 133, 2) and points.z is None and points.geometry == "2d" and points.score.shape == (1, 133) and list(points.point_names) == schema["point_names"]
    assert points.present.tolist() == [True] and np.isfinite(points.xy[0]).all() and (points.score[0] > 0.4).sum() > 60
    assert points.raw_score.shape == (1, 133) and points.raw_score.dtype == np.float64 and (points.raw_score[0] > 0).all()  # the decode scores before the map
    assert ((points.score >= 0) & (points.score <= 1)).all()  # the mapped scores
    assert box.boxes.shape == (1, 5) and crop.boxes.shape == (1, 5) and crop.present.tolist() == [True]
    cx, cy, w, h, rotation = crop.boxes[0]
    assert 0 < cx < width and 0 < cy < height and 40 < w <= 2 * width and 40 < h <= 2 * height and rotation == 0
    good = points.xy[0, points.score[0] > 0.4]  # the crop box holds the points of the person
    assert (np.abs(good - [cx, cy]) <= [w / 2, h / 2]).all(axis=1).mean() > 0.9
    canonical = to_canonical(points, schema)
    assert len(canonical.point_names) == 137 and canonical.xy.shape == (1, 137, 2) and canonical.z is None and list(canonical.point_names) == schema["canonical_names"]
    drawn = annotate(image, result, run.output_schema)
    assert drawn.shape == image.shape and drawn.dtype == np.uint8 and (drawn != image).any()


def check_schema(run: Any) -> None:
    schema = run.output_schema
    assert set(schema) == {"wholebody", "detector_box", "crop_box"}
    assert [schema[name]["port_type"] for name in ("wholebody", "detector_box", "crop_box")] == ["keypoints", "boxes", "boxes"]
    assert len(schema["wholebody"]["point_names"]) == 133 and len(schema["wholebody"]["canonical_names"]) == 137
    assert all(item["max_instances"] == 1 for item in schema.values())
    assert set(run.models) == {"person", "wholebody"}


def video_run(test_video_path: Path, execution_provider: str, precision: str) -> None:
    frames = read_frames(test_video_path, FRAMES)
    with start_or_skip("video", execution_provider) as run:
        check_schema(run)
        plans = run._executor.plans  # noqa: SLF001
        codes = [warning.code for warning in run.warnings]
        print(f"\n{execution_provider}: precision {({key: plan.precision for key, plan in plans.items()})}, warnings {codes}")
        for warning in run.warnings:
            print(f"  {warning.code}: {warning.message}")
        assert {plan.precision for plan in plans.values()} == {precision}
        assert "batch_limited_by_state" in codes  # the built-in is stateful
        results = [run.process(Frame(frame, index)) for index, frame in enumerate(frames)]
    # The detector runs on the first frame. Then the box comes from the points of the previous frame.
    assert [result["node_ran"] for result in results] == [{"person": index == 0, "wholebody": True} for index in range(FRAMES)]
    assert results[0]["detector_box"].present.tolist() == [True] and results[1]["detector_box"].present.tolist() == [False]
    assert [result["timestamp_ms"] for result in results] == [index * 1000.0 / 30.0 for index in range(FRAMES)]
    for frame, result in zip(frames, results, strict=True):
        check_result(run, result, frame)


def test_the_built_in_runs_one_image_on_the_cpu_ep(test_image: np.ndarray) -> None:
    with start_or_skip("image", "cpu") as run:
        check_schema(run)
        first, second = run.process(Frame(test_image, 0)), run.process(Frame(test_image, 1))
    for result in (first, second):  # `image` has no `@prev` value: the detector runs on each image
        assert result["node_ran"] == {"person": True, "wholebody": True} and result["timestamp_ms"] is None
        assert result["detector_box"].present.tolist() == [True] and result["detector_box"].class_index.tolist() == [0]
        check_result(run, result, test_image)
    np.testing.assert_array_equal(first["wholebody"].xy, second["wholebody"].xy)  # no state in `image`


def test_the_built_in_runs_a_video_on_the_cpu_ep(test_video_path: Path) -> None:
    video_run(test_video_path, "cpu", "fp32")


@pytest.mark.gpu
@pytest.mark.parametrize("execution_provider", ["cuda", "trt-rtx"])
def test_the_built_in_runs_a_video_on_a_gpu_ep(test_video_path: Path, execution_provider: str) -> None:
    video_run(test_video_path, execution_provider, "fp16")  # with no `precision`, a GPU EP takes the fp16 artifact
