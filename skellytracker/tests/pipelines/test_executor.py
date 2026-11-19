"""The executor of a pipeline run (`_runtime/executor.py`), on generated ONNX models on the CPU EP."""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from beartype.roar import BeartypeCallHintParamViolation

from skellytracker.core.eps.session import cpu_thread_count  # noqa: E402
from skellytracker.core.errors import CallRefusedError  # noqa: E402
from skellytracker.core.pipelines import Frame, load_pipeline, start_pipeline, timing  # noqa: E402
from skellytracker.core.pipelines._runtime import node_smooth_keypoints  # noqa: E402
from skellytracker.core.pipelines._runtime.executor import Executor  # noqa: E402
from skellytracker.core.pipelines._runtime.resolve import resolve  # noqa: E402
from skellytracker.core.pipelines.config import PipelineConfig  # noqa: E402
from skellytracker.core.pipelines.values import is_empty  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import (  # noqa: E402
    detector_pipeline,
    image,
    isolate,
    port_values,
    tracking_pipeline,
    write_models,
)


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


def prev_pipeline() -> dict[str, Any]:
    """`detector_pipeline` with a box from the keypoints of the previous frame, and a keypoint filter: an `@prev` value and a node state.

    The outputs are `wholebody` (the port `smooth.keypoints`) and `boxes` (the port `prev_box.boxes`).
    """
    data = detector_pipeline()
    data["nodes"] += [
        {"id": "prev_box", "type": "boxes_from_points", "inputs": {"keypoints": "body.keypoints@prev"}},
        {"id": "smooth", "type": "smooth_keypoints", "inputs": {"keypoints": "body.keypoints"}},
    ]
    data["outputs"] = {"wholebody": "smooth.keypoints", "boxes": "prev_box.boxes"}
    return data


def batch(run: Any, frames: dict[str, Frame]) -> tuple[dict, dict]:
    """Run one call. Return the result and the port values of each camera of the call."""
    results = run.process_batch(frames)
    return results, {camera: port_values(run, camera) for camera in results}


def xyxy(box: list[float]) -> list[float]:
    """Return `(x1, y1, x2, y2)` of a box `(cx, cy, w, h)`."""
    cx, cy, w, h = box
    return [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]


def start(root: Path, data: dict[str, Any], **parameters: Any):
    parameters.setdefault("camera_ids", [0])
    parameters.setdefault("running_mode", "video")
    return start_pipeline(load_pipeline(data, user_root=root), user_root=root, **parameters)


def points_box(keypoints: Any) -> list[float]:
    """Return `(cx, cy, w, h)` of the box around the present points of row 0: the box of `boxes_from_points` with its defaults."""
    points = keypoints.xy[0]
    points = points[~np.isnan(points).any(axis=1)]
    low, high = points.min(axis=0), points.max(axis=0)
    return [*((low + high) / 2), *(high - low)]


# ---------------------------------------------------------------------------------------------
# Each node type in one pipeline
# ---------------------------------------------------------------------------------------------


def test_each_node_type_runs_in_one_pipeline_on_generated_models(root: Path) -> None:
    results, ports = [], []
    with start(root, tracking_pipeline()) as run:
        assert set(run.output_schema) == {"wholebody", "boxes"}
        for index in range(4):
            results.append(run.process(Frame(image(1), index)))
            ports.append(port_values(run))
    # `redetect_trigger`: the detector runs on the first frame, then each 3 frames. The keypoint models run on each frame.
    assert [result["node_ran"] for result in results] == [
        {"person": ran, "body": True, "hand": True} for ran in (True, False, False, True)
    ]
    first, second = ports[0], ports[1]
    np.testing.assert_allclose(first["crop.boxes"].boxes, [[6, 6, 8, 8, 0]])  # `first_of`, `hold_boxes` and `smooth_boxes` pass the detector box
    assert first["person.boxes"].present.tolist() == [True] and second["person.boxes"].present.tolist() == [False]
    # Frame 1: `boxes_from_points` and `gate` carry the box of the points of frame 0, and `smooth_boxes` (ema, 0.5) blends it.
    carried = np.array(points_box(first["body.keypoints"])) * [1, 1, 1.2, 1.2]
    np.testing.assert_allclose(second["crop.boxes"].boxes[0, :4], (carried + [6, 6, 8, 8]) / 2)
    merged = ("body/a", "body/b", "body/c", "left_hand/a", "left_hand/b", "left_hand/c")
    # `merge` with `format: wholebody`: body and left_hand of `merged`, then feet, face and right_hand of COCO_WholeBody, all missing.
    layout = [group.name for group in run._executor.resolved.port_info("both", "keypoints").groups]
    assert layout == ["body", "feet", "face", "left_hand", "right_hand"]
    for index, (result, port) in enumerate(zip(results, ports, strict=True)):
        assert port["body.keypoints"].present.tolist() == [True] and result["frame_index"] == index
        assert port["merged.keypoints"].point_names == merged  # `assign_keypoints` adds a group
        np.testing.assert_array_equal(port["merged.keypoints"].xy[0, 3], port["body.keypoints"].xy[0, 0])
        both = port["both.keypoints"]
        assert both.point_names[:3] == merged[:3] and both.point_names[77:80] == merged[3:] and both.xy.shape == (1, 101, 2)
        np.testing.assert_array_equal(both.xy[:, :3], port["body.keypoints"].xy)
        np.testing.assert_array_equal(both.xy[:, 77:80], port["merged.keypoints"].xy[:, 3:])
        assert np.isnan(both.xy[0, 3:77]).all() and np.isnan(both.xy[0, 80:]).all()  # the groups of the layout with no source
        assert port["smooth.keypoints"].present.tolist() == [True] and port["smooth.keypoints"].xy.shape == (1, 101, 2)  # `smooth_keypoints`
        assert (result["image_width"], result["image_height"]) == (32, 32)
        # The delivered values: the canonical form of `smooth` and the upright crop box.
        np.testing.assert_array_equal(result["wholebody"].xy[:, :3], port["smooth.keypoints"].xy[:, :3])
        assert result["wholebody"].point_names[:3] == merged[:3]
        np.testing.assert_allclose(result["boxes"].xyxy[0], xyxy(port["crop.boxes"].boxes[0, :4]))
        assert result["boxes"].detector_ran.tolist() == [result["node_ran"]["person"]]


class FrameSpy:
    """The `run` of one `OnnxModelRunner`: it keeps each image that the node gets, then calls the real `run`."""

    def __init__(self, run: Any) -> None:
        self.run, self.images = run, []

    def __call__(self, index: int, images: list[Any], boxes: Any, timer: Any) -> Any:
        self.images += images
        return self.run(index, images, boxes, timer)


def test_each_model_node_gets_the_frame_object_of_the_host_with_no_copy(root: Path) -> None:
    """The plumbing passes the frame by reference: each model node gets the object that the host gave (ADR-9HTX item 4)."""
    given = image(1)
    with start(root, tracking_pipeline()) as run:
        spies = {}
        for node_id, runner in run._executor.models.items():  # noqa: SLF001
            spies[node_id] = runner.run = FrameSpy(runner.run)
        for index in range(4):
            run.process(Frame(given, index))
    assert {node_id: len(spy.images) for node_id, spy in spies.items()} == {"person": 2, "body": 4, "hand": 4}
    assert all(item is given for spy in spies.values() for item in spy.images)


# Each boxes and keypoints port of each node type of `tracking_pipeline`.
EACH_PORT = (
    "person.boxes", "detected_box.value", "points_box.boxes", "carried_box.value", "box.value", "hold.boxes", "crop.boxes",
    "body.keypoints", "hand.keypoints", "both.keypoints", "merged.keypoints", "smooth.keypoints",
)


def test_each_boxes_and_keypoints_output_of_each_node_is_in_source_image_pixels(root: Path) -> None:
    """A frame of twice the size gives each box and each point at twice the place (pipeline.graph, Behaviour item 3).

    The model inputs have fixed sizes (32 x 32 and 16 x 12), and the frames are plain, so the models
    give the same values for both frames. A node that gave a box or a point in the space of a model
    input or of a crop would not scale with the frame.
    """
    results: dict[int, list[dict]] = {32: [], 64: []}
    for size in (32, 64):
        with start(root, tracking_pipeline()) as run:
            for index in range(4):
                run.process(Frame(image(1, size, size), index))
                results[size].append(port_values(run))
    for small, large in zip(results[32], results[64], strict=True):
        for name in EACH_PORT:
            a, b = small[name], large[name]
            np.testing.assert_array_equal(a.present, b.present, err_msg=name)
            if hasattr(a, "boxes"):
                np.testing.assert_allclose(b.boxes[:, :4], 2 * a.boxes[:, :4], rtol=1e-6, atol=1e-5, err_msg=name)
                np.testing.assert_array_equal(b.boxes[:, 4], a.boxes[:, 4], err_msg=name)
            else:
                np.testing.assert_allclose(b.xy, 2 * a.xy, rtol=1e-6, atol=1e-5, err_msg=name)
    assert all(results[64][0][name].present.any() for name in EACH_PORT if not name.startswith(("points_box", "carried_box")))


# ---------------------------------------------------------------------------------------------
# The empty-input rule
# ---------------------------------------------------------------------------------------------

STOPS = {  # (node, the one input that is empty): the node stops
    ("body", "boxes"): True, ("body", "image"): True,  # the `boxes` input of a top-down model is required
    ("person", "run_if"): True,  # a false `run_if` stops the node
    ("trigger", "previous_keypoints"): False, ("trigger", "previous_boxes"): False,  # optional inputs
    ("points_box", "keypoints"): True, ("points_box", "previous_boxes"): False, ("points_box", "reference_boxes"): False,
    ("carried_box", "value"): True, ("carried_box", "condition"): False,  # `gate` reads a false flag `condition`
    ("hold", "current"): True, ("hold", "previous"): False,  # `hold_boxes` reads an empty `previous`
    ("merged", "target"): True, ("merged", "source"): False,  # `assign_keypoints` reads an empty `source`
    ("both", "body"): True,  # an empty `body` stops `merge`
    ("crop", "boxes"): False, ("smooth", "keypoints"): False,  # the filters read their empty input
}


def test_an_empty_required_input_stops_a_node_and_an_empty_optional_or_read_input_does_not(root: Path) -> None:
    resolved = resolve(PipelineConfig.model_validate(tracking_pipeline()), root)

    def inputs_of(node, empty: str | None) -> Any:
        found = []
        for item in node.inputs:
            value = image(1) if item.node == "frame" else True if item.node == "trigger" else resolved.port_info(item.node, item.port).empty()
            if item.name == empty or empty == "*":
                value = None if item.node == "frame" else False if item.node == "trigger" else value
            elif hasattr(value, "present"):
                value.present[0] = True
            found.append((item.name, value))
        return [value for _, value in found] if isinstance(node.inputs_info, list) else dict(found)

    for (node_id, name), stops in STOPS.items():
        node = resolved.nodes[node_id]
        assert not Executor._stops(node, inputs_of(node, None)), node_id
        assert Executor._stops(node, inputs_of(node, name)) is stops, (node_id, name)
    for node_id in ("box", "detected_box"):  # `first_of` runs with each input empty
        assert all(is_empty(value) for value in inputs_of(resolved.nodes[node_id], "*"))
        assert not Executor._stops(resolved.nodes[node_id], inputs_of(resolved.nodes[node_id], "*"))


def test_a_node_that_an_empty_input_stops_gives_empty_outputs_and_the_nodes_that_read_an_empty_input_run(root: Path) -> None:
    with start(root, tracking_pipeline()) as run:
        dark = run.process(Frame(image(0), 0))  # the detector runs and finds nobody
        dark_ports = port_values(run)
        again = run.process(Frame(image(1), 1))
        again_ports = port_values(run)
    assert dark["node_ran"] == {"person": True, "body": False, "hand": False}
    for name in ("person.boxes", "crop.boxes", "body.keypoints", "merged.keypoints", "smooth.keypoints"):
        assert is_empty(dark_ports[name]) and len(dark_ports[name].present) == 1, name  # an empty value still has its I rows
    assert is_empty(dark["wholebody"]) and is_empty(dark["boxes"]) and np.isnan(dark["boxes"].xyxy).all()
    # An empty `body` stops `merge`: its output is empty, with the columns of its layout.
    both = dark_ports["both.keypoints"]
    assert is_empty(both) and both.xy.shape == (1, 101, 2) and (both.score == 0).all()
    # The check `box_missing` asks for a detection on the frame after a frame with no box.
    assert again["node_ran"] == {"person": True, "body": True, "hand": True} and again_ports["body.keypoints"].present.tolist() == [True]


# ---------------------------------------------------------------------------------------------
# `@prev`
# ---------------------------------------------------------------------------------------------


def frames_of(index: int, sizes: dict[str, int], **more: Any) -> dict[str, Frame]:
    return {camera: Frame(image(1, size, size), index, **more) for camera, size in sizes.items()}


def test_prev_is_empty_on_the_first_frame_and_then_gives_the_value_of_the_previous_frame_of_the_same_camera(root: Path) -> None:
    sizes = {"a": 32, "b": 64}  # the points of the two cameras differ, because the test models follow the image size
    with start(root, prev_pipeline(), camera_ids=["a", "b"]) as run:
        first, first_ports = batch(run, frames_of(0, sizes))
        second = run.process_batch(frames_of(1, sizes))
    assert is_empty(first["a"]["boxes"]) and is_empty(first["b"]["boxes"])
    body = {camera: first_ports[camera]["body.keypoints"] for camera in sizes}
    assert not np.allclose(points_box(body["a"]), points_box(body["b"]))
    for camera in sizes:
        np.testing.assert_allclose(second[camera]["boxes"].xyxy[0], xyxy(points_box(body[camera])))
        np.testing.assert_array_equal(second[camera]["boxes"].score, body[camera].instance_score)


def test_each_prev_value_is_empty_in_the_running_mode_image(root: Path) -> None:
    with start(root, prev_pipeline(), running_mode="image") as run:
        results = [run.process(Frame(image(1), index)) for index in range(3)]
    assert all(is_empty(result["boxes"]) and result["wholebody"].present[0] for result in results)
    assert [result["timestamp_ms"] for result in results] == [None, None, None]


def test_in_live_a_camera_that_a_call_does_not_hold_keeps_its_prev_value_and_its_state(root: Path) -> None:
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        _, first = batch(run, frames_of(0, {"a": 32, "b": 64}, timestamp_ms=0.0))
        state = run._executor.states[("b", "smooth")]
        only_a, only_a_ports = batch(run, frames_of(1, {"a": 48}, timestamp_ms=10.0))
        assert list(only_a) == ["a"] and run._executor.states[("b", "smooth")] is state
        only_b = run.process_batch(frames_of(5, {"b": 64}, timestamp_ms=20.0))
    np.testing.assert_allclose(only_a["a"]["boxes"].xyxy[0], xyxy(points_box(first["a"]["body.keypoints"])))
    # The previous frame of `b` is its frame of the first call, not the frame of `a` of the second call.
    np.testing.assert_allclose(only_b["b"]["boxes"].xyxy[0], xyxy(points_box(first["b"]["body.keypoints"])))
    assert not np.allclose(points_box(first["b"]["body.keypoints"]), points_box(only_a_ports["a"]["body.keypoints"]))


# ---------------------------------------------------------------------------------------------
# Stateful pipelines
# ---------------------------------------------------------------------------------------------


def test_a_stateful_pipeline_in_video_gets_one_log_line_and_the_warning_batch_limited_by_state(root: Path, caplog: pytest.LogCaptureFixture) -> None:
    received = []
    with caplog.at_level(logging.WARNING, logger="skellytracker.core.pipelines"):
        with start(root, prev_pipeline(), camera_ids=["a", "b"], on_warning=received.append) as run:
            (warning,) = run.warnings
            batches = [item.batch for item in run._executor.sessions.opened.values()]
    assert warning.code == "batch_limited_by_state" and warning.node_ids == ("prev_box",) and warning.details == {"batch": 2}
    assert received == [warning] and batches == [2, 2]  # batch = camera count
    lines = [record.getMessage() for record in caplog.records if "batch_limited_by_state" in record.getMessage()]
    assert len(lines) == 1 and "prev_box" in lines[0] and warning.message in lines[0]


@pytest.mark.parametrize(("data", "mode"), [(detector_pipeline, "video"), (prev_pipeline, "live"), (prev_pipeline, "image")])
def test_a_pipeline_that_is_not_stateful_or_not_in_video_gets_no_batch_limited_by_state_warning(root: Path, data: Any, mode: str) -> None:
    with start(root, data(), running_mode=mode) as run:
        assert run.warnings == ()


# ---------------------------------------------------------------------------------------------
# A refused call
# ---------------------------------------------------------------------------------------------


def snapshot(run: Any) -> tuple[dict, dict, dict, dict, int]:
    executor = run._executor
    return (
        dict(executor.states), {camera: dict(values) for camera, values in executor.prev.items()},
        dict(executor.last_timestamp), dict(executor.gives_timestamp), executor.calls,
    )


def same(before: tuple, after: tuple) -> bool:
    """Return true when the two snapshots hold the same objects: no state and no `@prev` value changed."""
    states = before[0].keys() == after[0].keys() and all(before[0][key] is after[0][key] for key in before[0])
    prev = all(before[1][camera][port] is after[1][camera][port] for camera in before[1] for port in before[1][camera])
    return states and prev and before[1].keys() == after[1].keys() and before[2:] == after[2:]


def test_v_pipeline_running_6_a_live_frame_with_no_timestamp_refuses_the_call_and_changes_no_state_of_any_camera(root: Path) -> None:
    sizes = {"a": 32, "b": 64}
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        _, first = batch(run, frames_of(0, sizes, timestamp_ms=0.0))
        before = snapshot(run)
        bad = {"a": Frame(image(1), 1, 1000.0), "b": Frame(image(1, 64, 64), 1)}  # `a` is good, `b` has no timestamp_ms
        with pytest.raises(CallRefusedError, match="V-pipeline.running-6") as error:
            run.process_batch(bad)
        assert error.value.rule == "V-pipeline.running-6" and same(before, snapshot(run))
        # The run accepts the next call. 10 is after 0 and before 1000: the refused call did not move the time of `a`.
        after = run.process_batch(frames_of(1, sizes, timestamp_ms=10.0))
    for camera in sizes:
        np.testing.assert_allclose(after[camera]["boxes"].xyxy[0], xyxy(points_box(first[camera]["body.keypoints"])))


def test_v_pipeline_running_7_a_video_camera_that_stops_to_give_timestamps_refuses_the_call_and_changes_no_state(root: Path) -> None:
    sizes = {"a": 32, "b": 64}
    with start(root, prev_pipeline(), camera_ids=["a", "b"], fps=50.0) as run:
        run.process_batch({"a": Frame(image(1), 0, 5.0), "b": Frame(image(1, 64, 64), 0)})  # `a` gives timestamps, `b` gives none
        before = snapshot(run)
        for bad in ({"a": Frame(image(1), 1), "b": Frame(image(1), 1)}, {"a": Frame(image(1), 1, 9.0), "b": Frame(image(1), 1, 9.0)}):
            with pytest.raises(CallRefusedError, match="V-pipeline.running-7") as error:
                run.process_batch(bad)
            assert error.value.rule == "V-pipeline.running-7" and same(before, snapshot(run))
        after = run.process_batch({"a": Frame(image(1), 1, 6.0), "b": Frame(image(1, 64, 64), 1)})
    # The camera with no timestamp_ms gets frame_index x 1000 / fps.
    assert (after["a"]["timestamp_ms"], after["b"]["timestamp_ms"]) == (6.0, 20.0)
    assert set(sizes) == set(after)


@pytest.mark.parametrize("mode", ["video", "live"])
def test_v_node_smooth_keypoints_3_a_timestamp_that_does_not_increase_refuses_the_call_and_changes_no_state(root: Path, mode: str) -> None:
    sizes = {"a": 32, "b": 64}
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode=mode) as run:
        run.process_batch(frames_of(0, sizes, timestamp_ms=100.0))
        before = snapshot(run)
        for late in (100.0, 50.0):  # `a` is good, `b` does not increase
            with pytest.raises(CallRefusedError, match="V-node.smooth_keypoints-3") as error:
                run.process_batch({"a": Frame(image(1), 1, 5000.0), "b": Frame(image(1, 64, 64), 1, late)})
            assert error.value.rule == "V-node.smooth_keypoints-3" and same(before, snapshot(run))
        after = run.process_batch(frames_of(1, sizes, timestamp_ms=101.0))
    assert after["a"]["timestamp_ms"] == 101.0 and not is_empty(after["b"]["boxes"])


def test_a_video_camera_with_no_timestamps_must_give_a_frame_index_that_increases(root: Path) -> None:
    with start(root, prev_pipeline()) as run:
        run.process(Frame(image(1), 3))
        with pytest.raises(CallRefusedError, match="V-node.smooth_keypoints-3"):
            run.process(Frame(image(1), 3))  # frame_index x 1000 / fps does not increase
        assert run.process(Frame(image(1), 4))["timestamp_ms"] == pytest.approx(4000 / 30)


def test_a_node_that_refuses_a_timestamp_after_other_nodes_ran_refuses_the_call_and_no_state_and_no_prev_value_changes(
    root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sizes = {"a": 32, "b": 64}
    real, refuse = node_smooth_keypoints.run, []

    def run_node(params, inputs, state, frame, infos):
        if refuse and (frame.image_width, frame.image_height) == (64, 64):  # the last node of the order, for the second camera
            raise ValueError("V-node.smooth_keypoints-3: timestamp_ms must increase")
        return real(params, inputs, state, frame, infos)

    monkeypatch.setattr(node_smooth_keypoints, "run", run_node)
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        _, first = batch(run, frames_of(0, sizes, timestamp_ms=0.0))
        before = snapshot(run)
        refuse.append(True)
        with pytest.raises(CallRefusedError, match="smooth: camera 'b': V-node.smooth_keypoints-3") as error:
            run.process_batch(frames_of(1, {"a": 48, "b": 64}, timestamp_ms=1000.0))  # each model ran before the refusal
        assert error.value.rule == "V-node.smooth_keypoints-3" and same(before, snapshot(run))
        refuse.clear()
        after = run.process_batch(frames_of(1, sizes, timestamp_ms=10.0))
    for camera in sizes:  # `@prev` is still the value of the first call, also for camera `a`, whose nodes all ran in the refused call
        np.testing.assert_allclose(after[camera]["boxes"].xyxy[0], xyxy(points_box(first[camera]["body.keypoints"])))


# ---------------------------------------------------------------------------------------------
# node_ran
# ---------------------------------------------------------------------------------------------


def test_node_ran_is_true_when_the_detector_ran_and_found_nobody_and_false_for_an_empty_required_input(root: Path) -> None:
    with start(root, detector_pipeline()) as run:
        result = run.process(Frame(image(0), 0))
    assert result["node_ran"] == {"person": True, "body": False}
    assert is_empty(result["boxes"]) and is_empty(result["wholebody"])
    assert result["boxes"].detector_ran.tolist() == [True]  # the detector ran and found nobody


def test_node_ran_is_present_with_timing_off_and_the_sink_gets_no_line(root: Path, tmp_path: Path) -> None:
    lines: list[dict] = []
    data = detector_pipeline()
    data["instrumentation"] = {"timing_spans": ["pipeline.run", "person.inference"]}
    with start(root, data, timing="off", timing_sink=lines.append) as run:
        assert run.process(Frame(image(1), 0))["node_ran"] == {"person": True, "body": True}
    assert lines == []
    start(root, data, timing="off", timing_sink=tmp_path / "timing.jsonl").close()
    assert not (tmp_path / "timing.jsonl").exists()


def test_a_padded_batch_item_is_not_a_run_a_live_call_gives_a_result_and_event_images_only_for_its_cameras(root: Path) -> None:
    lines: list[dict] = []
    data = detector_pipeline(max_instances=3)
    data["instrumentation"] = {"timing_spans": ["person.inference", "body.inference", "pipeline.run"]}
    with start(root, data, camera_ids=["a", "b"], running_mode="live", timing_sink=lines.append) as run:
        # Sessions of batch 2 and 6: the item of camera `b` and four crop slots are padded items.
        assert sorted(item.batch for item in run._executor.sessions.opened.values()) == [2, 6]
        results = run.process_batch({"a": Frame(image(1), 7, 1.5)})
    assert list(results) == ["a"] and results["a"]["node_ran"] == {"person": True, "body": True}
    assert results["a"]["wholebody"].present.tolist() == [True, True, False]  # the padding box row is not a run
    for event in lines[1:]:
        assert event["images"] == [{"frame_index": 7, "camera_id": "a"}] and event["batch_size"] == 1


# ---------------------------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------------------------

SPANS = [
    "pipeline.run", "trigger.run", "crop.run", "person.preprocess", "person.inference", "person.postprocess",
    "body.preprocess", "body.inference", "body.postprocess",
]


def timed_run(root: Path, sink: Any, values: tuple[int, ...] = (1, 1)) -> list[dict]:
    data = tracking_pipeline()
    data["instrumentation"] = {"timing_spans": SPANS}
    with start(root, data, timing_sink=sink) as run:
        return [run.process(Frame(image(value), index)) for index, value in enumerate(values)]


def test_the_timing_file_starts_with_the_header_and_holds_one_event_for_each_span_that_is_on_and_ran(root: Path, tmp_path: Path) -> None:
    path = tmp_path / "timing.jsonl"
    timed_run(root, path)
    header, *events = timing.read_timing(path)
    assert tuple(header) == timing.HEADER_FIELDS and header["schema"] == "skellytracker.timing/1"
    assert (header["running_mode"], header["camera_ids"], header["image_list_sha256"], header["spans_on"]) == ("video", [0], None, SPANS)
    assert header["warmup_passes"] == 1
    nodes = {item["id"]: item for item in header["nodes"]}
    assert list(nodes) == [node["id"] for node in tracking_pipeline()["nodes"]]  # one item for each node
    person = nodes["person"]
    assert (person["key"], person["size"], person["precision"], person["batching"]) == ("demo@demo-exporter", "n", "fp32", 1)
    assert len(person["sidecar_sha256"]) == 64 and len(person["artifact_sha256"]) == 64
    assert tuple(person["execution"]) == timing.EXECUTION_FIELDS
    assert (person["execution"]["requested_ep"], person["execution"]["used_ep"]) == ("cpu", "cpu")
    assert person["execution"]["cpu_nodes"] > 0 and person["execution"]["cpu_op_types"]
    assert person["execution"]["cpu_threads"] == cpu_thread_count() >= 1  # the applied count of the CPU session: the default
    assert (nodes["body"]["shared_with"], nodes["hand"]["shared_with"], person["shared_with"]) == (["hand"], ["body"], [])
    assert nodes["crop"]["execution"] is None and nodes["crop"]["artifact_sha256"] is None

    def spans(frame_index: int) -> list[str]:
        return [f"{event['node_id']}.{event['span']}" for event in events if event["images"][0]["frame_index"] == frame_index]

    model = ["preprocess", "inference", "postprocess"]
    # Frame 0: each span that is on, in node order, and `pipeline.run` last. No event of `hand` or `smooth`: their spans are off.
    assert spans(0) == ["trigger.run", *(f"person.{span}" for span in model), "crop.run", *(f"body.{span}" for span in model), "pipeline.run"]
    # Frame 1: the detector did not run, so it gives no event.
    assert spans(1) == ["trigger.run", "crop.run", *(f"body.{span}" for span in model), "pipeline.run"]
    for event in events:
        assert tuple(event) == timing.EVENT_FIELDS and event["batch_size"] == 1 and event["start_ns"] <= event["end_ns"]
        assert event["images"][0]["camera_id"] == 0
    whole = [event for event in events if event["node_id"] == "pipeline"]
    for index, call in enumerate(whole):  # the span of the call holds the spans of its nodes
        inner = [event for event in events if event["images"][0]["frame_index"] == index and event is not call]
        assert all(call["start_ns"] <= event["start_ns"] and event["end_ns"] <= call["end_ns"] for event in inner)
    assert [timing.task_ids(event) for event in events[:1]] == [["0:0:trigger:run"]]


def test_a_node_that_an_empty_input_stops_gives_no_timing_event(root: Path) -> None:
    lines: list[dict] = []
    timed_run(root, lines.append, values=(0,))
    assert "schema" in lines[0]
    # The detector ran and found nobody. `smooth_boxes` reads its empty input, so it ran. The keypoint model did not run.
    assert [f"{event['node_id']}.{event['span']}" for event in lines[1:]] == [
        "trigger.run", "person.preprocess", "person.inference", "person.postprocess", "crop.run", "pipeline.run",
    ]


def test_the_aggregator_gives_the_skellybench_timing_record_of_a_timing_file_of_a_run(root: Path, tmp_path: Path) -> None:
    path = tmp_path / "timing.jsonl"
    timed_run(root, path, values=(1, 1, 1, 1))
    record = timing.skellybench_timing(path)
    assert set(record["stages_ms_per_image"]) == set(timing.STAGES) and all(value > 0 for value in record["stages_ms_per_image"].values())
    assert record["ms_per_image"] > 0 and record["images_per_second"] == pytest.approx(1000 / record["ms_per_image"])
    assert record["excluded_ms_per_image"][timing.GLUE_STAGE] > 0  # the `run` spans of `trigger` and `crop`
    assert sum(record["stages_ms_per_image"].values()) < record["ms_per_image"] * 4  # the same clock and the same unit


def test_the_aggregator_output_of_a_run_passes_the_skellybench_schema(root: Path, tmp_path: Path) -> None:
    schema = pytest.importorskip("skellybench.schema")
    path = tmp_path / "timing.jsonl"
    timed_run(root, path)
    stages = dict.fromkeys((*timing.STAGES, timing.GLUE_STAGE), "text")
    schema.validate_timing(timing.skellybench_timing(path), mode="host", protocol={"excluded_stages": [timing.GLUE_STAGE], "stage_definitions": {"host": stages}})


def test_one_model_node_gives_its_stage_providers_to_the_aggregator(root: Path) -> None:
    lines: list[dict] = []
    data = detector_pipeline()
    data["outputs"] = {"boxes": "person.boxes"}  # `body` is not used, so it does not run
    data["instrumentation"] = {"timing_spans": ["person.preprocess", "person.inference", "person.postprocess"]}
    with start(root, data, timing_sink=lines.append) as run:
        assert run.process(Frame(image(1), 0))["node_ran"] == {"person": True, "body": False}
    nodes = {item["id"]: item for item in lines[0]["nodes"]}
    assert nodes["body"]["execution"] is None and nodes["body"]["artifact_sha256"] is not None
    assert timing.skellybench_timing(lines)["stage_providers"] == {"preprocess": None, "inference": "CPUExecutionProvider", "postprocess": None}


# ---------------------------------------------------------------------------------------------
# The outputs block
# ---------------------------------------------------------------------------------------------

ROTATED = {"id": "turned", "type": "boxes_from_points", "inputs": {"keypoints": "body.keypoints@prev"},
           "params": {"size_rule": "alignment", "alignment_start": "body/a", "alignment_end": "body/b", "target_rotation_deg": 90}}


@pytest.mark.parametrize(
    ("outputs", "nodes", "rule"),
    [
        ({"wholebody": "trigger.redetect"}, [], "V-pipeline.outputs-4: the output wholebody must name a keypoints port"),
        ({"boxes": "body.keypoints"}, [], "V-pipeline.outputs-4: the output boxes must name a boxes port"),
        ({"crop_box": "crop.boxes"}, [], "V-pipeline.outputs-1: the output key 'crop_box'"),
        ({"boxes": "turned.boxes"}, [ROTATED], "V-pipeline.outputs-5: .* turned"),
        # A rotated box that a node passes, also through `@prev`, is refused.
        ({"boxes": "pick.value"}, [ROTATED, {"id": "pick", "type": "first_of", "inputs": ["person.boxes", "late.boxes@prev"]},
                                   {"id": "late", "type": "smooth_boxes", "inputs": {"boxes": "turned.boxes"}}], "V-pipeline.outputs-5: .* turned"),
    ],
    ids=["flag", "keypoints-as-boxes", "unknown-key", "rotated", "rotated-through-prev"],
)
def test_the_load_refuses_an_output_that_is_not_a_delivered_form(root: Path, outputs: dict, nodes: list, rule: str) -> None:
    data = tracking_pipeline()
    data["nodes"] += nodes
    data["outputs"] = outputs
    with pytest.raises(ValueError, match=rule):
        load_pipeline(data, user_root=root)


def test_a_rotated_box_that_is_not_an_output_and_the_upright_input_of_boxes_from_points_load(root: Path) -> None:
    data = tracking_pipeline()
    data["nodes"].append(ROTATED)  # `turned` feeds no output
    data["outputs"]["wholebody"] = "body.keypoints"
    load_pipeline(data, user_root=root)
    # The keypoints of `points_box` come from a node that reads a rotated box: only the params of `boxes_from_points` rotate its box.
    data["nodes"].append({"id": "turned_points", "type": "onnx_model", "inputs": {"image": "frame.image", "boxes": "turned.boxes"},
                          "params": {"key": "demo-body@demo-exporter", "size": "m", "execution_provider": "cpu"}})
    next(node for node in data["nodes"] if node["id"] == "points_box")["inputs"]["keypoints"] = "turned_points.keypoints@prev"
    load_pipeline(data, user_root=root)
    # The condition of `gate` does not reach its output: an upright value with a rotated-box condition loads.
    data["nodes"].append({"id": "keep", "type": "gate", "inputs": {"value": "person.boxes", "condition": "turned.boxes"}, "params": {"mode": "is_present"}})
    data["outputs"]["boxes"] = "keep.value"
    load_pipeline(data, user_root=root)


def test_the_output_wholebody_needs_a_group_body_and_holistic_the_four_holistic_groups(root: Path) -> None:
    data = detector_pipeline()
    data["outputs"] = {"wholebody": "body.keypoints", "holistic": "body.keypoints"}
    with pytest.raises(ValueError, match=r"V-pipeline.outputs-4: the output holistic \(body.keypoints\) must have exactly the groups"):
        load_pipeline(data, user_root=root)
    data["nodes"][1]["id"] = "torso"  # a schema with one group gives the group the id of the node
    data["outputs"] = {"wholebody": "torso.keypoints"}
    with pytest.raises(ValueError, match=r"V-pipeline.outputs-4: the output wholebody \(torso.keypoints\) must have a group body; it has the groups \['torso'\]"):
        load_pipeline(data, user_root=root)


def test_flag_when_on_the_previous_keypoints_runs_the_detector_only_when_the_person_is_lost(root: Path) -> None:
    """The form "detect when lost" of node.flag_when: on frame 0 the `@prev` value is empty, so the detector runs."""
    data = detector_pipeline()
    data["nodes"].insert(0, {"id": "lost", "type": "flag_when", "inputs": {"value": "body.keypoints@prev"}, "params": {"mode": "is_empty"}})
    data["nodes"][1]["inputs"]["run_if"] = "lost.flag"
    flags = []
    with start(root, data) as run:
        results = []
        for index in range(4):
            results.append(run.process(Frame(image(1), index)))
            flags.append(port_values(run)["lost.flag"])
    # Frame 1 has the keypoints of frame 0, so the detector does not run, the body model gets no box and the person is lost again.
    assert flags == [True, False, True, False]
    assert [result["node_ran"] for result in results] == [{"person": ran, "body": ran} for ran in (True, False, True, False)]
    with start(root, data, running_mode="image") as run:  # each `@prev` value is empty: the detector runs on each image
        assert [run.process(Frame(image(1), index))["node_ran"]["person"] for index in range(2)] == [True, True]


def test_detector_ran_is_the_node_ran_of_the_instance_source_of_the_output_boxes(root: Path) -> None:
    with start(root, tracking_pipeline()) as run:
        assert run.output_schema["boxes"]["instance_source"] == "person"
        results = [run.process(Frame(image(1), index)) for index in range(4)]
    assert [result["boxes"].detector_ran.tolist() for result in results] == [[True], [False], [False], [True]]
    assert [result["node_ran"]["person"] for result in results] == [True, False, False, True]


# ---------------------------------------------------------------------------------------------
# JPEG frames (pipeline.running, Behaviour item 13)
# ---------------------------------------------------------------------------------------------


def jpeg(frame: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".jpg", frame)
    assert ok
    return encoded.tobytes()


def decoded(data: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)


def test_a_jpeg_frame_gives_the_result_of_its_decoded_array_and_each_reader_gets_the_one_decoded_frame(root: Path) -> None:
    data = [jpeg(image(1)) for _ in range(4)]
    results: dict[str, list[dict]] = {"jpeg": [], "array": []}
    for form in results:
        with start(root, tracking_pipeline()) as run:
            spies = {node_id: FrameSpy(runner.run) for node_id, runner in run._executor.models.items()}  # noqa: SLF001
            for node_id, spy in spies.items():
                run._executor.models[node_id].run = spy  # noqa: SLF001
            for index, buffer in enumerate(data):
                results[form].append(run.process(Frame(buffer if form == "jpeg" else decoded(buffer), index)))
                frames = [item for spy in spies.values() for item in spy.images]
                assert all(item is frames[0] for item in frames)  # one decode for each call: each node gets the same object
                for spy in spies.values():
                    spy.images.clear()
    for a, b in zip(results["jpeg"], results["array"], strict=True):
        np.testing.assert_array_equal(a["wholebody"].xy, b["wholebody"].xy)
        np.testing.assert_array_equal(a["boxes"].xyxy, b["boxes"].xyxy)
        assert (a["node_ran"], a["image_width"], a["image_height"]) == (b["node_ran"], 32, 32)
    assert results["jpeg"][0]["node_ran"]["person"] and results["jpeg"][0]["boxes"].xyxy.shape == (1, 4)


@pytest.mark.parametrize(("rotation_deg", "code"), [
    (None, None), (0, None), (90, cv2.ROTATE_90_CLOCKWISE), (180, cv2.ROTATE_180), (270, cv2.ROTATE_90_COUNTERCLOCKWISE),
])
def test_rotation_deg_turns_the_decoded_jpeg_frame_and_90_and_270_swap_the_frame_size(root: Path, rotation_deg: int | None, code: int | None) -> None:
    frame = image(1, 32, 48)
    frame[:, :8] = 200  # a bright band at the left edge shows the turn
    data = jpeg(frame)
    expected = decoded(data) if code is None else cv2.rotate(decoded(data), code)
    with start(root, detector_pipeline()) as run:
        spy = run._executor.models["person"].run = FrameSpy(run._executor.models["person"].run)  # noqa: SLF001
        result = run.process(Frame(data, 0, rotation_deg=rotation_deg))
    turned = rotation_deg in (90, 270)
    assert (result["image_width"], result["image_height"]) == ((32, 48) if turned else (48, 32))
    np.testing.assert_array_equal(spy.images[0], expected)


@pytest.mark.parametrize("rotation_deg", [None, 0, 90, 180, 270])
def test_rotation_deg_turns_a_decoded_array_like_a_jpeg_frame_and_the_array_of_the_caller_does_not_change(root: Path, rotation_deg: int | None) -> None:
    frame = image(1, 32, 48)
    frame[:, :8] = 200
    given = frame.copy()
    codes = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    expected = frame if not rotation_deg else np.rot90(frame, k=-(rotation_deg // 90))  # np.rot90 turns counterclockwise
    assert not rotation_deg or np.array_equal(expected, cv2.rotate(frame, codes[rotation_deg]))
    with start(root, detector_pipeline()) as run:
        spy = run._executor.models["person"].run = FrameSpy(run._executor.models["person"].run)  # noqa: SLF001
        result = run.process(Frame(frame, 0, rotation_deg=rotation_deg))
    assert (result["image_width"], result["image_height"]) == ((32, 48) if rotation_deg in (90, 270) else (48, 32))
    np.testing.assert_array_equal(spy.images[0], expected)
    np.testing.assert_array_equal(frame, given)
    assert (spy.images[0] is frame) == (not rotation_deg)  # no copy for 0 or None


def test_a_call_takes_an_array_camera_and_a_jpeg_camera_with_a_rotation_deg_each(root: Path) -> None:
    with start(root, detector_pipeline(), camera_ids=["a", "b"]) as run:
        results = run.process_batch({"a": Frame(image(1, 32, 48), 0, rotation_deg=90), "b": Frame(jpeg(image(1, 32, 48)), 0, rotation_deg=270)})
    assert {camera: (result["image_width"], result["image_height"]) for camera, result in results.items()} == {"a": (32, 48), "b": (32, 48)}


BAD_FRAMES = {  # the frame of camera `b`: (image, rotation_deg) -> the rule that it breaks
    "an empty buffer": ("empty", None, "V-pipeline.running-12"),
    "junk bytes": ("junk", None, "V-pipeline.running-12"),
    "a JPEG start with junk bytes": ("soi-junk", None, "V-pipeline.running-12"),
    "rotation_deg 45": ("jpeg", 45, "V-pipeline.running-13"),
    "rotation_deg 90.0": ("jpeg", 90.0, "V-pipeline.running-13"),
    "rotation_deg True": ("jpeg", True, "V-pipeline.running-13"),
    "a decoded array with rotation_deg 45": ("array", 45, "V-pipeline.running-13"),
    "a decoded array with rotation_deg 90.0": ("array", 90.0, "V-pipeline.running-13"),
    "a decoded array with rotation_deg True": ("array", True, "V-pipeline.running-13"),
}


@pytest.mark.parametrize(("form", "rotation_deg", "rule"), BAD_FRAMES.values(), ids=BAD_FRAMES.keys())
def test_v_pipeline_running_12_and_13_a_bad_frame_of_one_camera_refuses_the_call_and_changes_no_state_of_any_camera(
    root: Path, form: str, rotation_deg: Any, rule: str,
) -> None:
    sizes = {"a": 32, "b": 64}
    given = {
        "empty": b"", "junk": bytes(range(256)), "soi-junk": b"\xff\xd8" + b"junk" * 16,
        "jpeg": jpeg(image(1, 64, 64)), "array": image(1, 64, 64),
    }[form]
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        _, first = batch(run, frames_of(0, sizes, timestamp_ms=0.0))
        before = snapshot(run)
        bad = {"a": Frame(jpeg(image(1)), 1, 1000.0), "b": Frame(given, 1, 1000.0, rotation_deg)}  # `a` is a good JPEG frame
        with pytest.raises(CallRefusedError, match=f"{rule}: camera 'b'") as error:
            run.process_batch(bad)
        assert error.value.rule == rule and same(before, snapshot(run))
        # The run accepts the next call. 10 is after 0 and before 1000: the refused call did not move the time of `a`.
        after = run.process_batch(frames_of(1, sizes, timestamp_ms=10.0))
    for camera in sizes:
        np.testing.assert_allclose(after[camera]["boxes"].xyxy[0], xyxy(points_box(first[camera]["body.keypoints"])))


def test_frame_image_is_a_decoded_frame_that_uploads_at_most_one_time_for_each_call(root: Path) -> None:
    """The seam of the GPU preprocess: no node asks for the device frame yet, so the test asks for it, with a fake upload."""
    uploads: list[Any] = []

    def upload(pixels: np.ndarray, device_id: Any) -> int:
        uploads.append(pixels)
        return len(uploads)

    with start(root, detector_pipeline()) as run:
        spy = run._executor.models["person"].run = FrameSpy(run._executor.models["person"].run)  # noqa: SLF001
        for call in range(2):  # a new call makes a new frame, so it uploads again
            run.process(Frame(jpeg(image(1, 32, 48)), call))
            frame = port_values(run)["frame.image"]
            assert (frame.width, frame.height) == (48, 32) and frame.host is spy.images[-1]  # the model node got the host pixels
            assert frame.on_device(0, upload) == frame.on_device(0, upload) == call + 1 and uploads[-1] is frame.host
    assert len(uploads) == 2


def test_a_memoryview_is_not_a_frame_image() -> None:
    """The type check of `Frame` refuses a `memoryview` before the call: only `bytes` and `bytearray` are JPEG buffers."""
    with pytest.raises(BeartypeCallHintParamViolation):
        Frame(memoryview(jpeg(image(1))), 0)


# The CPU decode of two or more JPEG buffers of a call in the thread pool of the run (pipeline.running, Fields: CPU threads).

SIZES = [(32, 48), (64, 64), (48, 32), (40, 56), (32, 32), (56, 40)]


def jpeg_batch(count: int, bad: tuple[int, ...] = (), index: int = 0, timestamp_ms: float | None = None) -> dict[str, Frame]:
    """`count` JPEG cameras `c0`, `c1`, ... of mixed sizes with rotation_deg 0, 90, 180 and 270 in turn. The cameras of `bad` give junk after the SOI marker."""
    def data(i: int) -> bytes:
        return b"\xff\xd8" + b"junk" * 16 if i in bad else jpeg(np.random.default_rng(i).integers(0, 256, (*SIZES[i % 6], 3), np.uint8))
    return {f"c{i}": Frame(data(i), index, timestamp_ms, (0, 90, 180, 270)[i % 4]) for i in range(count)}


def decode_threads(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch `cpu.decode_jpeg` to record the name of the thread of each decode. Return the list of names."""
    from skellytracker.core.decode import cpu

    names: list[str] = []
    real = cpu.decode_jpeg
    monkeypatch.setattr(cpu, "decode_jpeg", lambda *args: (names.append(threading.current_thread().name), real(*args))[1])
    return names


def pool_threads() -> list[str]:
    return [thread.name for thread in threading.enumerate() if thread.name.startswith("skellytracker-jpeg")]


@pytest.mark.parametrize("count", [3, 6])
def test_the_cpu_decode_in_the_thread_pool_gives_the_frames_of_the_decode_in_a_row_bit_for_bit(root: Path, monkeypatch: pytest.MonkeyPatch, count: int) -> None:
    names = decode_threads(monkeypatch)
    frames, found = jpeg_batch(count), {}
    for threads in (1, 4):
        names.clear()
        with start(root, detector_pipeline(), camera_ids=list(frames), cpu_threads=threads) as run:
            run.process_batch(frames)
            found[threads] = {camera: port_values(run, camera)["frame.image"].host for camera in frames}
            assert (run._executor.decode_pool is None) == (threads == 1)  # noqa: SLF001
        assert len(names) == count and all(name.startswith("skellytracker-jpeg") == (threads > 1) for name in names)
    for camera in frames:
        np.testing.assert_array_equal(found[1][camera], found[4][camera])


def test_v_pipeline_running_12_two_bad_buffers_in_the_thread_pool_refuse_the_call_with_the_first_bad_camera_each_time(root: Path) -> None:
    good = jpeg_batch(5, timestamp_ms=0.0)
    with start(root, prev_pipeline(), camera_ids=list(good), running_mode="live", cpu_threads=4) as run:
        run.process_batch(good)
        before = snapshot(run)
        for _ in range(20):
            with pytest.raises(CallRefusedError, match="V-pipeline.running-12: camera 'c2': OpenCV cannot read") as error:
                run.process_batch(jpeg_batch(5, bad=(2, 4), index=1, timestamp_ms=1000.0))
            assert error.value.rule == "V-pipeline.running-12" and same(before, snapshot(run))
        assert set(run.process_batch(jpeg_batch(5, index=1, timestamp_ms=10.0))) == set(good)  # 10 < 1000: no time moved


def test_one_jpeg_buffer_in_a_call_or_no_jpeg_in_the_run_decodes_in_a_row_with_no_pool(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    names = decode_threads(monkeypatch)
    with start(root, detector_pipeline(), camera_ids=["a", "b"], cpu_threads=4) as run:
        run.process_batch({"a": Frame(image(1), 0), "b": Frame(image(1), 0)})
        assert run._executor.decode_pool is None and names == []  # noqa: SLF001
        run.process_batch({"a": Frame(jpeg_batch(1)["c0"].image, 1), "b": Frame(image(1), 1)})
        assert run._executor.decode_pool is None and names == [threading.current_thread().name]  # noqa: SLF001


def test_close_stops_each_decode_thread_and_a_second_close_does_nothing(root: Path) -> None:
    frames = jpeg_batch(3)
    run = start(root, detector_pipeline(), camera_ids=list(frames), cpu_threads=2)
    run.process_batch(frames)
    assert 1 <= len(pool_threads()) <= 2  # at most min(cpu_threads, cameras of the run); the pool starts a thread only when none is idle
    run.close()
    run.close()
    assert pool_threads() == []


def test_a_decode_error_that_is_not_a_value_error_raises_from_the_thread_pool_as_it_is(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skellytracker.core.decode import cpu

    def fail(buffer: bytes, rotation_deg: int) -> np.ndarray:
        raise MemoryError("no memory for the frame")

    monkeypatch.setattr(cpu, "decode_jpeg", fail)
    frames = jpeg_batch(3)
    with start(root, detector_pipeline(), camera_ids=list(frames), cpu_threads=4) as run:
        with pytest.raises(MemoryError, match="no memory for the frame"):
            run.process_batch(frames)
        assert run._executor.decode_pool is not None  # noqa: SLF001


# The GPU JPEG decoder in the frame stage, with a fake decoder on the CPU EP: the graph path runs on `cpu`
# (`onnx_model.GRAPH_DEFAULT_EPS`), and the fake gives each frame as an `OrtValue` in host memory, as the real
# decoder gives it in GPU memory.


class HostReads:
    """A device value that counts its copies to the host (`numpy()`). The graph path cannot bind it."""

    def __init__(self, value: Any, reads: list[int]) -> None:
        self.value, self.reads = value, reads

    def numpy(self) -> np.ndarray:
        self.reads.append(1)
        return self.value.numpy()


class FakeJpegDecoder:
    """Decode with OpenCV and give device frames, with the settings of the fixture `gpu_decode`. `log` gets each decode and the close."""

    def __init__(self, found: dict[str, Any]) -> None:
        self.found, self.log = found, found["log"]

    def decode(self, buffers: list[bytes], rotations: list[int]) -> list[Any]:
        import onnxruntime

        from skellytracker.core.decode import cpu
        from skellytracker.core.decode.frame import DecodedFrame

        self.log.append(("decode", len(buffers), list(rotations)))
        if self.found["fail"] is not None:
            raise self.found["fail"]
        frames = []
        for buffer, rotation in zip(buffers, rotations, strict=True):
            pixels = None if buffer in self.found["refused"] else cv2.imdecode(np.frombuffer(buffer, np.uint8), cv2.IMREAD_COLOR)
            if pixels is None:
                frames.append(None)
                continue
            value = onnxruntime.OrtValue.ortvalue_from_numpy(np.ascontiguousarray(cpu.turn(pixels, rotation)))
            height, width = value.shape()[:2]
            frames.append(DecodedFrame(width, height, device=value if self.found["host_reads"] is None else HostReads(value, self.found["host_reads"])))
        return frames

    def close(self) -> None:
        self.log.append("close")


@pytest.fixture
def gpu_decode(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Run the graph path and the GPU JPEG decode on the CPU EP. `found["log"]` records the opens, the decodes and the closes; `found["uploads"]` the uploads.

    Set `found["decoder"]` to False for a decoder that does not open, or to an error that the open raises.
    `found["refused"]` holds the buffers that the decoder refuses, `found["fail"]` an error that `decode` raises,
    and `found["host_reads"]` a list that counts the host copies of each frame of the decoder.
    """
    from skellytracker.core.eps import session as eps_session
    from skellytracker.core.pipelines._runtime import executor, onnx_model

    found: dict[str, Any] = {"log": [], "uploads": [], "refused": (), "decoder": True, "fail": None, "host_reads": None}
    monkeypatch.setattr(onnx_model, "GRAPH_DEFAULT_EPS", onnx_model.GRAPH_DEFAULT_EPS | {"cpu"})
    monkeypatch.setattr(executor, "JPEG_DECODER_EPS", executor.JPEG_DECODER_EPS | {"cpu"})

    def opened(execution_provider: str, device_key: Any, ep_device_id: Any) -> Any:
        found["log"].append(("open", execution_provider))
        if isinstance(found["decoder"], Exception):
            raise found["decoder"]
        return FakeJpegDecoder(found) if found["decoder"] else None

    monkeypatch.setattr(executor, "open_jpeg_decoder", opened)
    real = eps_session.upload_frame
    monkeypatch.setattr(eps_session, "upload_frame", lambda pixels, device_id, **kw: (found["uploads"].append(pixels), real(pixels, device_id, **kw))[1])
    return found


def jpeg_calls(count: int = 2) -> list[dict[str, Frame]]:
    """Two JPEG cameras of two sizes with rotation_deg 0 and 90, and an array camera."""
    return [{
        "a": Frame(jpeg(image(1 + index, 40, 48)), index),
        "b": Frame(jpeg(image(2, 36, 64)), index, rotation_deg=90),
        "c": Frame(image(1, 32, 32), index),
    } for index in range(count)]


def jpeg_warnings(run: Any) -> list[Any]:
    return [warning for warning in run.warnings if warning.code == "jpeg_decoded_on_cpu"]


def frame_spans(lines: list[dict]) -> list[tuple[str, list]]:
    return [(event["span"], [image["camera_id"] for image in event["images"]]) for event in lines[1:] if event["node_id"] == "frame"]


def test_gpu_decoded_frames_go_to_the_graph_path_with_no_upload_and_one_batch_for_each_call(root: Path, gpu_decode: dict[str, Any]) -> None:
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        results = []
        for frames in jpeg_calls():
            before = len(gpu_decode["uploads"])
            results.append(run.process_batch(frames))
            assert len(gpu_decode["uploads"]) - before == 1 and gpu_decode["uploads"][-1] is frames["c"].image  # only the array camera uploads
            assert port_values(run, "a")["frame.image"].pixels is None and port_values(run, "b")["frame.image"].pixels is None
            assert (port_values(run, "b")["frame.image"].width, port_values(run, "b")["frame.image"].height) == (36, 64)
        assert jpeg_warnings(run) == []
    assert gpu_decode["log"] == [("open", "cpu"), ("decode", 2, [0, 90]), ("decode", 2, [0, 90]), "close"]
    gpu_decode["decoder"] = False  # the same calls with the CPU decode: OpenCV in both, so the results are equal
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        expected = [run.process_batch(frames) for frames in jpeg_calls()]
    for found, wanted in zip(results, expected, strict=True):
        for camera in wanted:
            np.testing.assert_array_equal(found[camera]["wholebody"].xy, wanted[camera]["wholebody"].xy)
            np.testing.assert_array_equal(found[camera]["boxes"].xyxy, wanted[camera]["boxes"].xyxy)


def test_a_buffer_that_the_gpu_decoder_refuses_decodes_on_the_cpu_with_one_warning_for_each_camera(root: Path, gpu_decode: dict[str, Any]) -> None:
    calls = jpeg_calls(3)
    gpu_decode["refused"] = tuple(frames["b"].image for frames in calls)
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        for frames in calls:
            before = len(gpu_decode["uploads"])
            result = run.process_batch(frames)
            assert port_values(run, "a")["frame.image"].pixels is None  # the other camera keeps its GPU frame
            turned = port_values(run, "b")["frame.image"]
            np.testing.assert_array_equal(turned.pixels, cv2.rotate(decoded(frames["b"].image), cv2.ROTATE_90_CLOCKWISE))
            assert len(gpu_decode["uploads"]) - before == 2 and (result["b"]["image_width"], result["b"]["image_height"]) == (36, 64)
        (warning,) = jpeg_warnings(run)
    assert (warning.node_ids, dict(warning.details)) == ((), {"reason": "decoder_refused", "camera_id": "b"})


def test_a_decoder_that_does_not_open_gives_the_cpu_decode_and_one_warning_at_the_first_jpeg_call(root: Path, gpu_decode: dict[str, Any]) -> None:
    gpu_decode["decoder"] = False
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        run.process_batch({camera: Frame(image(1, 32, 32), 0) for camera in "abc"})
        assert gpu_decode["log"] == [] and jpeg_warnings(run) == []  # only decoded arrays: no open and no warning
        for frames in jpeg_calls(3)[1:]:
            run.process_batch(frames)
            assert port_values(run, "a")["frame.image"].pixels is not None
        (warning,) = jpeg_warnings(run)
    assert gpu_decode["log"] == [("open", "cpu")]  # no second open
    assert warning.node_ids == () and dict(warning.details) == {
        "reason": "decoder_unavailable", "package": None, "jpeg_decoder": None, "install_hint": None, "cause": None,
    }


def test_the_warning_of_a_decoder_that_does_not_open_names_the_package_and_the_install_hint_or_the_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    from skellytracker.core.eps import store
    from skellytracker.core.pipelines._runtime import executor

    monkeypatch.setattr(store, "component_state", lambda catalog, key: "missing")
    warning = executor.decoder_missing_warning("cuda")
    assert warning.code == "jpeg_decoded_on_cpu" and warning.node_ids == ()
    assert dict(warning.details) == {
        "reason": "decoder_unavailable", "package": "gpu-jpeg-cu13", "jpeg_decoder": "missing", "install_hint": "Run `skellytracker-eps install cuda`.",
        "cause": None,
    }
    assert warning.message.startswith("the GPU JPEG decoder gpu-jpeg-cu13 of 'cuda' is missing; the run decodes")
    monkeypatch.setattr(store, "component_state", lambda catalog, key: "installed")
    warning = executor.decoder_missing_warning("cuda", "RuntimeError: boom")
    assert warning.message == "the GPU JPEG decoder gpu-jpeg-cu13 of 'cuda' did not open: RuntimeError: boom; the run decodes each JPEG buffer on the CPU"
    assert (warning.details["install_hint"], warning.details["cause"]) == (None, "RuntimeError: boom")


def test_an_open_that_raises_gives_the_cpu_decode_one_warning_with_the_cause_and_no_second_open(root: Path, gpu_decode: dict[str, Any]) -> None:
    gpu_decode["decoder"] = RuntimeError("cudaStreamCreateWithFlags returned the CUDA error 2")
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        for frames in jpeg_calls(3):
            run.process_batch(frames)
            assert port_values(run, "a")["frame.image"].pixels is not None
        (warning,) = jpeg_warnings(run)
    assert gpu_decode["log"] == [("open", "cpu")]
    assert warning.details["reason"] == "decoder_unavailable"
    assert warning.details["cause"] == "RuntimeError: cudaStreamCreateWithFlags returned the CUDA error 2"


def test_an_error_of_a_decode_raises_and_changes_no_state_and_gives_no_warning(root: Path, gpu_decode: dict[str, Any]) -> None:
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        run.process_batch({"a": Frame(image(1), 0, 0.0), "b": Frame(image(1), 0, 0.0)})
        before = snapshot(run)
        gpu_decode["fail"] = RuntimeError("cudaStreamSynchronize returned the CUDA error 700")
        with pytest.raises(RuntimeError, match="error 700") as error:
            run.process_batch({"a": Frame(jpeg(image(1)), 1, 1000.0), "b": Frame(jpeg(image(2)), 1, 1000.0)})
        assert not isinstance(error.value, CallRefusedError) and same(before, snapshot(run)) and jpeg_warnings(run) == []
        gpu_decode["fail"] = None
        run.process_batch({"a": Frame(jpeg(image(1)), 1, 10.0), "b": Frame(image(1), 1, 10.0)})


@pytest.mark.parametrize("kind", ["decoder_unavailable", "decoder_refused"])
def test_a_warning_held_back_in_a_refused_call_comes_at_the_next_good_call(root: Path, gpu_decode: dict[str, Any], kind: str) -> None:
    good = jpeg(image(2))
    if kind == "decoder_unavailable":
        gpu_decode["decoder"] = False
    else:
        gpu_decode["refused"] = (good,)
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], running_mode="live") as run:
        with pytest.raises(CallRefusedError, match="V-pipeline.running-12: camera 'c'"):
            run.process_batch({"a": Frame(jpeg(image(1)), 0, 0.0), "b": Frame(good, 0, 0.0), "c": Frame(b"\xff\xd8junk", 0, 0.0)})
        assert jpeg_warnings(run) == []
        run.process_batch({"a": Frame(jpeg(image(1)), 1, 10.0), "b": Frame(good, 1, 10.0)})
        assert [warning.details["reason"] for warning in jpeg_warnings(run)] == [kind]
        if kind == "decoder_refused":
            assert jpeg_warnings(run)[0].details["camera_id"] == "b"


def test_two_host_readers_of_a_gpu_decoded_frame_get_one_host_copy_for_each_call_and_the_same_pixels(
    root: Path, gpu_decode: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no graph session allowed, both model nodes use the CPU preprocess and read the host pixels of the GPU frame."""
    from skellytracker.core.pipelines._runtime import onnx_model

    monkeypatch.setattr(onnx_model, "SIZE_SETS", 0)
    gpu_decode["host_reads"] = reads = []
    calls = jpeg_calls(2)
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        seen: dict[str, list[Any]] = {}
        for node_id, runner in run._executor.models.items():  # noqa: SLF001
            seen[node_id] = []
            runner.run = lambda *args, real=runner.run, images=seen[node_id]: (images.extend(args[1]), real(*args))[1]
        found = []
        for frames in calls:
            before = len(reads)
            found.append(run.process_batch(frames))
            assert len(reads) - before == 2  # one host copy for each GPU-decoded camera (a, b), for both nodes
            frame = port_values(run, "a")["frame.image"]
            assert frame.pixels is None and seen["person"][-3] is seen["body"][-3] is frame  # each reader gets the one frame
        assert {warning.code for warning in run.warnings} >= {"preprocessed_on_cpu"} and jpeg_warnings(run) == []
    gpu_decode["decoder"], gpu_decode["host_reads"] = False, None
    monkeypatch.setattr(onnx_model, "SIZE_SETS", 4)
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        expected = [run.process_batch(frames) for frames in calls]
    for result, wanted in zip(found, expected, strict=True):
        for camera in wanted:
            np.testing.assert_array_equal(result[camera]["wholebody"].xy, wanted[camera]["wholebody"].xy)
            np.testing.assert_array_equal(result[camera]["boxes"].xyxy, wanted[camera]["boxes"].xyxy)


def test_close_runs_each_close_when_one_raises_and_then_raises_the_first_error(root: Path, gpu_decode: dict[str, Any]) -> None:
    log = gpu_decode["log"]

    class Closing:
        def __init__(self, name: str, fails: bool) -> None:
            self.name, self.fails = name, fails

        def close(self) -> None:
            log.append(self.name)
            if self.fails:
                raise RuntimeError(self.name)

    run = start(root, detector_pipeline(), camera_ids=["a", "b", "c"])
    run.process_batch(jpeg_calls(1)[0])
    executor = run._executor  # noqa: SLF001
    real_sessions = executor.sessions.close

    def sessions_close() -> None:
        log.append("sessions")
        real_sessions()
        raise RuntimeError("sessions")

    executor.sessions.close = sessions_close
    executor.decoders = {0: Closing("decoder 0", True), 1: Closing("decoder 1", False)}
    with pytest.raises(RuntimeError, match="^sessions$"):
        run.close()
    assert log[-3:] == ["sessions", "decoder 0", "decoder 1"] and executor.sessions.opened == {}


def test_v_pipeline_running_12_a_buffer_that_no_decoder_reads_refuses_the_call_with_no_warning_and_the_decoder_stays(root: Path, gpu_decode: dict[str, Any]) -> None:
    with start(root, prev_pipeline(), camera_ids=["a", "b"], running_mode="live") as run:
        run.process_batch({"a": Frame(jpeg(image(1)), 0, 0.0), "b": Frame(jpeg(image(1, 64, 64)), 0, 0.0)})
        before = snapshot(run)
        with pytest.raises(CallRefusedError, match="V-pipeline.running-12: camera 'b'"):
            run.process_batch({"a": Frame(jpeg(image(1)), 1, 1000.0), "b": Frame(b"\xff\xd8" + b"junk" * 16, 1, 1000.0)})
        assert same(before, snapshot(run)) and jpeg_warnings(run) == []  # the refused buffer of `b` gives no warning
        run.process_batch({"a": Frame(jpeg(image(1)), 1, 10.0), "b": Frame(jpeg(image(1, 64, 64)), 1, 10.0)})
        assert port_values(run, "b")["frame.image"].pixels is None
    assert gpu_decode["log"] == [("open", "cpu"), *[("decode", 2, [0, 0])] * 3, "close"]


def test_the_frame_events_of_each_frame_form_are_inside_pipeline_run_and_the_aggregator_leaves_them_out(root: Path, gpu_decode: dict[str, Any]) -> None:
    data = detector_pipeline()
    data["instrumentation"] = {"timing_spans": ["frame.decode", "frame.upload", "pipeline.run", "person.inference"]}
    calls = jpeg_calls(1)
    gpu_decode["refused"] = (calls[0]["b"].image,)
    lines: list[dict] = []
    with start(root, data, camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        run.process_batch(calls[0])
    # `a` GPU-decoded: decode, no upload. `b` refused, CPU-decoded: decode, then upload. `c` an array: upload only.
    assert frame_spans(lines) == [("decode", ["a", "b"]), ("upload", ["b", "c"])]
    events = lines[1:]
    call = next(event for event in events if event["node_id"] == "pipeline")
    decode, upload = (event for event in events if event["node_id"] == "frame")
    assert call["start_ns"] <= decode["start_ns"] <= decode["end_ns"] <= upload["start_ns"] <= upload["end_ns"] <= call["end_ns"]
    assert all(tuple(event) == timing.EVENT_FIELDS and event["batch_size"] == len(event["images"]) for event in events)
    without = [line for line in lines if line.get("node_id") != "frame"]
    assert timing.skellybench_timing(lines) == timing.skellybench_timing(without)


def test_the_frame_spans_off_give_no_frame_event(root: Path, gpu_decode: dict[str, Any]) -> None:
    data = detector_pipeline()
    data["instrumentation"] = {"timing_spans": ["pipeline.run"]}
    lines: list[dict] = []
    with start(root, data, camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        run.process_batch(jpeg_calls(1)[0])
    assert [event["node_id"] for event in lines[1:]] == ["pipeline"]


def test_close_frees_the_decoded_frames_then_the_sessions_then_the_decoder_and_a_second_close_does_nothing(root: Path, gpu_decode: dict[str, Any]) -> None:
    log = gpu_decode["log"]
    run = start(root, detector_pipeline(), camera_ids=["a", "b", "c"])
    run.process_batch(jpeg_calls(1)[0])
    executor = run._executor  # noqa: SLF001
    for node_id, runner in executor.models.items():
        runner.close = lambda node_id=node_id, real=runner.close: (log.append((node_id, executor.port_values, executor.call_slots)), real())[1]
    real_sessions = executor.sessions.close
    executor.sessions.close = lambda: (log.append("sessions"), real_sessions())[1]
    run.close()
    run.close()
    assert log[-4:] == [("person", {}, {}), ("body", {}, {}), "sessions", "close"]  # the frames are gone before the sessions
    assert executor.decoders == {}


# A stored `fail` of a JPEG check of the quick check (pipeline.running, Behaviour item 13). The fixture `gpu_decode` runs
# the GPU frame path on the CPU EP; `stored` patches the read of `quick-checks.json`, and the tests of
# `stored_jpeg_checks` read a file of a private EP store.


@pytest.fixture
def stored(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """`found["checks"]` is the stored result of each device; `found["reads"]` records the `(EP, device key)` of each read."""
    from skellytracker.core.pipelines._runtime import executor

    found: dict[str, Any] = {"checks": {}, "reads": []}
    monkeypatch.setattr(executor, "stored_jpeg_checks", lambda ep, key: (found["reads"].append((ep, key)), dict(found["checks"]))[1])
    return found


def preprocess_warnings(run: Any) -> list[Any]:
    return [warning for warning in run.warnings if warning.code == "preprocessed_on_cpu"]


def test_a_stored_jpeg_decode_fail_decodes_on_the_cpu_keeps_the_gpu_preprocess_and_warns_one_time(
    root: Path, gpu_decode: dict[str, Any], stored: dict[str, Any],
) -> None:
    stored["checks"] = {"jpeg-decode": "fail", "jpeg-preprocess": "pass"}
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"]) as run:
        assert run.warnings == ()  # the decode warning comes at the first JPEG call
        for frames in jpeg_calls(3):
            before = len(gpu_decode["uploads"])
            run.process_batch(frames)
            assert len(gpu_decode["uploads"]) - before == 3  # the CPU frames of a and b upload for the GPU preprocess, as c does
            assert port_values(run, "a")["frame.image"].pixels is not None
        assert run._executor.models["person"].graph_on_at_start  # noqa: SLF001
    assert gpu_decode["log"] == [] and preprocess_warnings(run) == []  # no GPU decoder opens
    (warning,) = jpeg_warnings(run)
    assert (warning.node_ids, dict(warning.details)) == ((), {"reason": "quick_check_failed"})


def test_a_stored_jpeg_preprocess_fail_uses_the_cpu_preprocess_and_the_cpu_decode_with_the_warnings(
    root: Path, gpu_decode: dict[str, Any], stored: dict[str, Any],
) -> None:
    expected_calls = jpeg_calls(2)
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], preprocess="cpu") as run:
        expected = [run.process_batch(frames) for frames in expected_calls]
    stored["checks"] = {"jpeg-decode": "pass", "jpeg-preprocess": "fail"}
    lines: list[dict] = []
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        assert [(w.node_ids, dict(w.details)["reason"], dict(w.details)["frame_sizes"]) for w in run.warnings] == [
            (("person",), "quick_check_failed", None), (("body",), "quick_check_failed", None)]  # at the start, one for each node
        results = [run.process_batch(frames) for frames in jpeg_calls(2)]
        assert run._executor.models["person"].graph is None and run._executor.upload_devices == {}  # noqa: SLF001
    assert gpu_decode["log"] == [] and gpu_decode["uploads"] == []  # no GPU decoder opens and no frame uploads
    assert [dict(warning.details) for warning in jpeg_warnings(run)] == [{"reason": "quick_check_failed"}]
    assert {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]} == {"person": None, "body": None}
    for found, wanted in zip(results, expected, strict=True):  # the CPU path of `preprocess="cpu"`
        for camera in wanted:
            np.testing.assert_array_equal(found[camera]["wholebody"].xy, wanted[camera]["wholebody"].xy)
            np.testing.assert_array_equal(found[camera]["boxes"].xyxy, wanted[camera]["boxes"].xyxy)


@pytest.mark.parametrize("checks", [
    {"jpeg-decode": "pass", "jpeg-preprocess": "pass"}, {"jpeg-decode": "not-run", "jpeg-preprocess": "not-run"}, {},
], ids=["pass", "not-run", "no_stored_result"])
def test_a_stored_pass_not_run_or_no_stored_result_keeps_the_gpu_frame_path(
    root: Path, gpu_decode: dict[str, Any], stored: dict[str, Any], checks: dict[str, str],
) -> None:
    stored["checks"] = checks
    lines: list[dict] = []
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        for frames in jpeg_calls():
            run.process_batch(frames)
            assert port_values(run, "a")["frame.image"].pixels is None  # a frame of the GPU decoder
    assert stored["reads"] == [("cpu", None)] * 2 and run.warnings == ()  # one read for each node and device, at the start
    assert gpu_decode["log"][0] == ("open", "cpu")
    assert {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]} == {"person": "CPUExecutionProvider", "body": "CPUExecutionProvider"}


@pytest.mark.parametrize("preprocess", ["gpu", "cpu"])
def test_preprocess_gpu_and_cpu_do_not_read_the_stored_result(
    root: Path, gpu_decode: dict[str, Any], stored: dict[str, Any], monkeypatch: pytest.MonkeyPatch, preprocess: str,
) -> None:
    from skellytracker.core.pipelines._runtime import onnx_model

    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    stored["checks"] = {"jpeg-decode": "fail", "jpeg-preprocess": "fail"}
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], preprocess=preprocess) as run:
        for frames in jpeg_calls():
            run.process_batch(frames)
    assert stored["reads"] == [] and run.warnings == ()
    assert gpu_decode["log"][:1] == ([("open", "cpu")] if preprocess == "gpu" else [])  # `gpu` runs the GPU frame path


@pytest.mark.parametrize("failed", [0, 1])
def test_a_stored_jpeg_preprocess_fail_switches_off_only_its_own_gpu(
    root: Path, gpu_decode: dict[str, Any], stored: dict[str, Any], monkeypatch: pytest.MonkeyPatch, failed: int,
) -> None:
    """Two GPUs, each with one JPEG camera. The header gives the preprocess of the first GPU (pipeline.timing, Fields)."""
    from skellytracker.core.eps.records import RunDevice
    from skellytracker.core.pipelines._runtime import executor, sessions

    gpus = (RunDevice("gpu:0", "0000:01:00.0"), RunDevice("gpu:1", "0000:02:00.0"))
    monkeypatch.setattr(sessions, "run_gpus", lambda plans, device: gpus)
    monkeypatch.setattr(sessions, "free_vram", lambda key: None)
    monkeypatch.setattr(executor, "stored_jpeg_checks", lambda ep, key: {"jpeg-preprocess": "fail"} if key == f"gpu:{failed}" else {})
    calls = [{"a": Frame(jpeg(image(1 + index, 40, 48)), index), "b": Frame(jpeg(image(2, 36, 64)), index)} for index in range(2)]
    lines: list[dict] = []
    with start(root, detector_pipeline(), camera_ids=["a", "b"], timing_sink=lines.append) as run:
        assert run._executor.device_of == {"a": 0, "b": 1}  # noqa: SLF001
        for frames in calls:
            run.process_batch(frames)
            on_gpu = {camera: port_values(run, camera)["frame.image"].pixels is None for camera in "ab"}
            assert on_gpu == {"a": failed == 1, "b": failed == 0}  # a frame of the GPU decoder only on the GPU that passed
        assert set(run._executor.upload_devices) == {1 - failed}  # noqa: SLF001
    assert [dict(warning.details)["reason"] for warning in preprocess_warnings(run)] == ["quick_check_failed"] * 2
    assert [dict(warning.details) for warning in jpeg_warnings(run)] == [{"reason": "quick_check_failed"}]
    assert gpu_decode["log"].count(("open", "cpu")) == 1
    provider = None if failed == 0 else "CPUExecutionProvider"
    assert {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]} == {"person": provider, "body": provider}


def write_quick_checks(folder: Path, rows: Any) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "quick-checks.json").write_text(rows if isinstance(rows, str) else json.dumps(rows), encoding="utf-8")


def test_stored_jpeg_checks_reads_the_row_of_the_pair_and_gives_no_stored_result_on_each_fault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skellytracker.core.eps import certification, store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.pipelines._runtime.executor import stored_jpeg_checks
    from skellytracker.core.system import host as host_module
    from skellytracker.tests.hw_fakes import gpu, host

    folder = tmp_path / "eps"
    monkeypatch.setenv(store.STORE_VARIABLE, str(folder))
    fake = host(gpu())
    monkeypatch.setattr(host_module, "probe_host", lambda: fake)
    device_key = "gpu:10de:2484:0"
    pair = certification.pair_key(load_catalog(), "cuda", gpu(), "Windows")
    jpeg = {"jpeg-decode": "fail", "jpeg-preprocess": "pass"}

    assert stored_jpeg_checks("cuda", device_key) == {} and not folder.exists()  # no file: no stored result, and the read writes nothing
    write_quick_checks(folder, {pair: {"result": "passed", "jpeg": jpeg}})
    assert stored_jpeg_checks("cuda", device_key) == jpeg
    assert stored_jpeg_checks("trt-rtx", device_key) == {}  # no row of the pair
    assert stored_jpeg_checks("cuda", None) == {} and stored_jpeg_checks("cuda", "gpu:10de:2204:0") == {}  # no GPU of the host
    for rows in ({pair: {"result": "passed"}}, {pair: "passed"}, [pair], "{not json", {pair: {"jpeg": ["fail"]}}):  # no `jpeg`, or damaged
        write_quick_checks(folder, rows)
        assert stored_jpeg_checks("cuda", device_key) == {}
    write_quick_checks(folder, {pair: {"jpeg": {"jpeg-decode": 1}}})  # a damaged value comes back, and it is not `fail`
    assert stored_jpeg_checks("cuda", device_key) == {"jpeg-decode": 1}
    assert sorted(path.name for path in folder.iterdir()) == ["quick-checks.json"]  # no lock file


def test_a_run_on_the_cpu_ep_opens_no_decoder_gives_no_jpeg_warning_and_a_jpeg_frame_gives_only_a_decode_event(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from skellytracker.core.pipelines._runtime import executor

    monkeypatch.setattr(executor, "open_jpeg_decoder", lambda *args: pytest.fail("no decoder on the CPU EP"))
    data = detector_pipeline()
    data["instrumentation"] = {"timing_spans": ["frame.decode", "frame.upload"]}
    lines: list[dict] = []
    with start(root, data, camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        run.process_batch(jpeg_calls(1)[0])
        assert jpeg_warnings(run) == [] and port_values(run, "a")["frame.image"].pixels is not None
    assert frame_spans(lines) == [("decode", ["a", "b"])]  # no frame goes to GPU memory: no upload event


def test_preprocess_cpu_decodes_each_jpeg_in_the_cpu_pool_opens_no_decoder_and_gives_no_jpeg_warning(
    root: Path, gpu_decode: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    names = decode_threads(monkeypatch)
    gpu_decode["decoder"] = False  # with `auto`, a decoder that does not open warns
    with start(root, detector_pipeline(), camera_ids=["a", "b", "c"], cpu_threads=4, preprocess="cpu") as run:
        for frames in jpeg_calls():
            run.process_batch(frames)
            assert all(port_values(run, camera)["frame.image"].device is None for camera in frames)  # each frame stays in CPU memory
        assert run._executor.decoder_places == {}  # noqa: SLF001
    assert gpu_decode["log"] == [] and gpu_decode["uploads"] == [] and run.warnings == ()
    assert len(names) == 4 and all(name.startswith("skellytracker-jpeg") for name in names)  # 2 JPEG cameras in each of 2 calls
