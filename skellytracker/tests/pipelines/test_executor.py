"""The executor of a pipeline run (`_runtime/executor.py`), on generated ONNX models on the CPU EP."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytest.importorskip("onnx", reason="onnx not installed")

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
    merged = ("body/a", "body/b", "body/c", "extra/a", "extra/b", "extra/c")
    for index, (result, port) in enumerate(zip(results, ports, strict=True)):
        assert port["body.keypoints"].present.tolist() == [True] and result["frame_index"] == index
        assert port["merged.keypoints"].point_names == merged  # `merge` adds a group
        np.testing.assert_array_equal(port["merged.keypoints"].xy[0, 3], port["body.keypoints"].xy[0, 0])
        assert port["both.keypoints"].point_names == (*merged, "hand/a", "hand/b", "hand/c")  # `concat`
        np.testing.assert_array_equal(port["both.keypoints"].xy[:, :3], port["body.keypoints"].xy)
        assert port["smooth.keypoints"].present.tolist() == [True] and port["smooth.keypoints"].xy.shape == (1, 9, 2)  # `smooth_keypoints`
        assert (result["image_width"], result["image_height"]) == (32, 32)
        # The delivered values: the canonical form of `smooth` (each group passes through) and the upright crop box.
        np.testing.assert_array_equal(result["wholebody"].xy, port["smooth.keypoints"].xy)
        assert result["wholebody"].point_names == port["smooth.keypoints"].point_names
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
    ("merged", "target"): True, ("merged", "source"): False,  # `merge` reads an empty `source`
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
    for node_id in ("both", "box", "detected_box"):  # `concat` and `first_of` run with each input empty
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
    # `concat` runs with its empty inputs: each column is a missing point.
    both = dark_ports["both.keypoints"]
    assert is_empty(both) and both.xy.shape == (1, 9, 2) and (both.score == 0).all()
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


def test_the_output_wholebody_needs_a_group_body_and_holistic_the_four_holistic_groups(root: Path) -> None:
    data = detector_pipeline()
    data["outputs"] = {"wholebody": "body.keypoints", "holistic": "body.keypoints"}
    with pytest.raises(ValueError, match=r"V-pipeline.outputs-4: the output holistic \(body.keypoints\) must have exactly the groups"):
        load_pipeline(data, user_root=root)
    data["nodes"][1]["id"] = "torso"  # a schema with one group gives the group the id of the node
    data["outputs"] = {"wholebody": "torso.keypoints"}
    with pytest.raises(ValueError, match=r"V-pipeline.outputs-4: the output wholebody \(torso.keypoints\) must have a group body; it has the groups \['torso'\]"):
        load_pipeline(data, user_root=root)


def test_detector_ran_is_the_node_ran_of_the_instance_source_of_the_output_boxes(root: Path) -> None:
    with start(root, tracking_pipeline()) as run:
        assert run.output_schema["boxes"]["instance_source"] == "person"
        results = [run.process(Frame(image(1), index)) for index in range(4)]
    assert [result["boxes"].detector_ran.tolist() for result in results] == [[True], [False], [False], [True]]
    assert [result["node_ran"]["person"] for result in results] == [True, False, False, True]
