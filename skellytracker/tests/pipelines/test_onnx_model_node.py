"""The node type `onnx_model` in a run, on ONNX models that `onnx.helper` makes, on the CPU EP."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("onnx", reason="onnx not installed")

from skellytracker.core.detectors.generic import create_detector  # noqa: E402
from skellytracker.core.pipelines import Frame, load_pipeline, start_pipeline  # noqa: E402
from skellytracker.core.pipelines._runtime.onnx_model import OnnxModelRunner  # noqa: E402
from skellytracker.core.pipelines._runtime.resolve import resolve  # noqa: E402
from skellytracker.core.pipelines.config import PipelineConfig  # noqa: E402
from skellytracker.core.pipelines.values import InstanceBoxes  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import (  # noqa: E402
    KEYPOINT_KEY,
    KEYPOINT_RAW_SCORES,
    KEYPOINT_SCORES,
    OBJECT_KEY,
    detector_pipeline,
    image,
    isolate,
    port_values,
    write_models,
)


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


def one_frame(root: Path, value: int = 1, **person_params) -> dict:
    """Run one frame of `detector_pipeline`. Return the port values: `person.boxes` and `body.keypoints`."""
    config = load_pipeline(detector_pipeline(**person_params), user_root=root)
    with start_pipeline(config, camera_ids=[0], running_mode="image", user_root=root) as run:
        run.process(Frame(image(value), 0))
        return port_values(run)


def test_an_object_detector_gives_the_present_rows_first_in_score_order_with_class_index_and_padding_rows_last(root: Path) -> None:
    result = one_frame(root, max_instances=3)
    boxes = result["person.boxes"]
    assert boxes.present.tolist() == [True, True, False]
    # Each box is `(cx, cy, w, h, rotation)` with the rotation 0, and the instance score is the detection score of the row.
    np.testing.assert_allclose(boxes.boxes[:2], [[6, 6, 8, 8, 0], [25, 25, 10, 10, 0]])
    np.testing.assert_allclose(boxes.instance_score, [0.9, 0.75, 0.0], rtol=1e-6)
    assert boxes.class_index.tolist() == [0, 0, -1] and boxes.track_ids.tolist() == [-1, -1, -1]
    assert np.isnan(boxes.boxes[2]).all()  # the padding values of pipeline.outputs


def test_max_instances_keeps_the_rows_with_the_highest_scores(root: Path) -> None:
    boxes = one_frame(root, max_instances=1)["person.boxes"]
    assert boxes.boxes.shape == (1, 5) and boxes.present.tolist() == [True]
    np.testing.assert_allclose(boxes.instance_score, [0.9], rtol=1e-6)


def test_a_top_down_model_gives_row_i_from_box_row_i_with_the_instance_score_of_the_box_and_no_score_threshold(root: Path) -> None:
    result = one_frame(root, max_instances=3)
    body = result["body.keypoints"]
    assert body.point_names == ("body/a", "body/b", "body/c")  # the names of the port facts: `<group>/<point>`
    assert body.present.tolist() == [True, True, False] and body.track_ids.tolist() == [-1, -1, -1]
    np.testing.assert_array_equal(body.instance_score, result["person.boxes"].instance_score)
    # Point `a` is the centre of each crop. Point `c` is missing: NaN and the score 0. The node sets no low score to NaN.
    np.testing.assert_allclose(body.xy[:2, 0], [[6, 6], [25, 25]])
    np.testing.assert_allclose(body.score, [KEYPOINT_SCORES, KEYPOINT_SCORES, [0, 0, 0]], rtol=1e-6)  # the mapped scores
    # raw_score: the decode scores before the map. The missing point `c` and the padding row have 0 (pipeline.outputs item 9).
    assert body.raw_score.shape == (3, 3) and body.raw_score.dtype == np.float64
    np.testing.assert_allclose(body.raw_score, [KEYPOINT_RAW_SCORES, KEYPOINT_RAW_SCORES, [0, 0, 0]], rtol=1e-6)
    assert np.isnan(body.xy[:2, 2]).all() and np.isnan(body.xy[2]).all()
    assert body.z is None and body.geometry == "2d"  # a `2d` model gives no z


def test_a_boxes_value_with_a_padding_row_before_a_present_row_keeps_its_rows_and_a_padded_crop_gives_no_row(root: Path) -> None:
    resolved = resolve(PipelineConfig.model_validate(detector_pipeline(max_instances=2)), root)
    detector = create_detector(KEYPOINT_KEY, execution_provider="cpu", user_root=root)  # a batch-3 session: one crop, two padded items
    runner = OnnxModelRunner(resolved.nodes["body"], "fp32", [detector.session])
    boxes = InstanceBoxes.empty(2)
    boxes.boxes[1], boxes.instance_score[1], boxes.present[1] = (25, 25, 10, 10, 0), 0.4, True
    spans: list[str] = []
    (outputs,) = runner.run(0, [image(1)], [boxes], lambda span, start, end: spans.append(span))
    value = outputs["keypoints"]
    assert value.present.tolist() == [False, True] and value.instance_score.tolist() == [0.0, 0.4]
    np.testing.assert_allclose(value.xy[1, 0], [25, 25])
    assert np.isnan(value.xy[0]).all() and spans == ["preprocess", "inference", "postprocess"]


def test_the_timer_of_a_generic_detector_gets_three_spans_in_order_and_changes_no_result(root: Path) -> None:
    detector = create_detector(OBJECT_KEY, execution_provider="cpu", user_root=root)
    spans: list[tuple[str, int, int]] = []
    (timed,), (plain,) = detector.detect([image(1)], timer=lambda *span: spans.append(span)), detector.detect([image(1)])
    np.testing.assert_array_equal(timed.boxes, plain.boxes)
    assert [span[0] for span in spans] == ["preprocess", "inference", "postprocess"]
    assert all(start <= end for _, start, end in spans) and spans[0][2] == spans[1][1] and spans[1][2] == spans[2][1]
    assert detector.detect([], timer=lambda *span: pytest.fail("no model run, no span")) == []
