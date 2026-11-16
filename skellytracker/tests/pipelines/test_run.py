"""The public run API (`core/pipelines/run.py`): `start_pipeline`, `PipelineRun`, `set_params` and the thread rules."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytest.importorskip("onnx", reason="onnx not installed")

import skellytracker.core.pipelines as pipelines  # noqa: E402
from skellytracker.core.errors import CallRefused, RunClosedError, SetParamsRefused  # noqa: E402
from skellytracker.core.pipelines import Frame, PipelineRun, load_pipeline, start_pipeline  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import KEYPOINT_KEY, OBJECT_KEY, detector_pipeline, image, isolate, write_models  # noqa: E402


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


def start(root: Path, data: dict[str, Any] | None = None, **parameters: Any) -> PipelineRun:
    parameters.setdefault("camera_ids", [0])
    parameters.setdefault("running_mode", "video")
    return start_pipeline(load_pipeline(data or detector_pipeline(), user_root=root), user_root=root, **parameters)


def in_thread(target: Any) -> tuple[threading.Thread, list]:
    """Start `target` on a new thread. Return the thread and the list that gets its result or its error."""
    found: list = []

    def work() -> None:
        try:
            found.append(target())
        except BaseException as exc:  # noqa: BLE001
            found.append(exc)

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    return thread, found


# ---------------------------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------------------------


def test_a_run_gives_the_output_schema_before_frame_0_the_run_metadata_and_the_result_fields(root: Path) -> None:
    with start(root, camera_ids=["cam"]) as run:
        assert run.output_schema["body"]["point_names"] == ["body/a", "body/b", "body/c"] and run.output_schema["person_box"]["class_names"] == ["person"]
        assert (run.camera_ids, run.running_mode, run.warnings) == (("cam",), "video", ())
        models = run.models
        assert set(models) == {"person", "body"} and set(models["person"]) == {"key", "version", "sidecar_sha256"}
        assert (models["person"]["key"], models["body"]["key"], models["person"]["version"]) == (OBJECT_KEY, KEYPOINT_KEY, "0.1.0")
        assert len(models["person"]["sidecar_sha256"]) == 64
        result = run.process(Frame(image(1, 24, 40), 4))
    assert set(result) == {"body", "person_box", "person_roi", "frame_index", "image_size", "timestamp_ms", "node_ran"}
    assert (result["frame_index"], result["image_size"], result["node_ran"]) == (4, (40, 24), {"person": True, "body": True})
    assert result["timestamp_ms"] == pytest.approx(4 * 1000 / 30)  # the `video` fallback with the default fps


def test_process_is_for_a_run_with_one_camera(root: Path) -> None:
    with start(root, camera_ids=[0, 1]) as run:
        with pytest.raises(ValueError, match="one camera"):
            run.process(Frame(image(1), 0))
        assert list(run.process_batch({1: Frame(image(1), 0), 0: Frame(image(1), 0)})) == [0, 1]  # the order of the run


@pytest.mark.parametrize(("camera_ids", "mode"), [([], "video"), (["a", "a"], "live"), ([0, 1], "image")])
def test_v_pipeline_running_1_the_camera_ids_are_unique_and_not_empty_and_image_has_one(root: Path, camera_ids: list, mode: str) -> None:
    with pytest.raises(ValueError, match="V-pipeline.running-1"):
        start(root, camera_ids=camera_ids, running_mode=mode)


@pytest.mark.parametrize("mode", ["video", "image"])
def test_v_pipeline_running_2_a_video_or_image_call_gives_a_frame_for_each_camera_and_no_other(root: Path, mode: str) -> None:
    cameras = ["a", "b"] if mode == "video" else ["a"]
    good = {camera: Frame(image(1), 0) for camera in cameras}
    with start(root, camera_ids=cameras, running_mode=mode) as run:
        for bad in ({}, {**good, "x": Frame(image(1), 0)}, {"x": Frame(image(1), 0)}, *([{"a": Frame(image(1), 0)}] if mode == "video" else [])):
            with pytest.raises(CallRefused, match="V-pipeline.running-2") as error:
                run.process_batch(bad)
            assert error.value.rule == "V-pipeline.running-2"
        assert list(run.process_batch(good)) == cameras  # the run accepts the next call
        assert run._executor.calls == 1


def test_v_pipeline_running_2_a_live_call_gives_a_frame_for_one_or_more_cameras_of_the_run(root: Path) -> None:
    with start(root, camera_ids=["a", "b"], running_mode="live") as run:
        for bad in ({}, {"x": Frame(image(1), 0, 0.0)}, {"a": Frame(image(1), 0, 0.0), "x": Frame(image(1), 0, 0.0)}):
            with pytest.raises(CallRefused, match="V-pipeline.running-2"):
                run.process_batch(bad)
        assert list(run.process_batch({"b": Frame(image(1), 0, 0.0)})) == ["b"]


def test_live_takes_a_subset_of_the_cameras_one_float_timestamp_for_each_camera_and_a_frame_index_that_skips(root: Path) -> None:
    with start(root, camera_ids=["a", "b", "c"], running_mode="live") as run:
        first = run.process_batch({"a": Frame(image(1), 0, 1000.25), "b": Frame(image(1), 0, 7.5), "c": Frame(image(1), 0, 99.0)})
        second = run.process_batch({"c": Frame(image(1), 41, 99.5), "a": Frame(image(1), 9, 1033.6)})  # `b` dropped a frame
        third = run.process_batch({"b": Frame(image(1), 3, 8.0)})
    assert {camera: result["timestamp_ms"] for camera, result in first.items()} == {"a": 1000.25, "b": 7.5, "c": 99.0}
    assert list(second) == ["a", "c"] and (second["a"]["frame_index"], second["c"]["frame_index"]) == (9, 41)
    assert (second["a"]["timestamp_ms"], second["c"]["timestamp_ms"]) == (1033.6, 99.5)
    assert list(third) == ["b"] and third["b"]["frame_index"] == 3 and third["b"]["body"].present.tolist() == [True]


def test_a_run_is_a_context_manager_a_second_close_does_nothing_and_a_later_call_raises_run_closed_error(root: Path) -> None:
    with start(root) as run:
        run.process(Frame(image(1), 0))
    run.close()
    for call in (lambda: run.process(Frame(image(1), 1)), lambda: run.process_batch({0: Frame(image(1), 1)}), lambda: run.set_params("person", {})):
        with pytest.raises(RunClosedError):
            call()
    assert run._executor.sessions.opened == {} and run._executor.models == {}


# ---------------------------------------------------------------------------------------------
# V-pipeline.running-10: set_params
# ---------------------------------------------------------------------------------------------


def params_pipeline(tap: bool = False) -> dict[str, Any]:
    """`detector_pipeline` with an ROI from the keypoints (`expand_ratio` can change) and an `ema` filter with a state."""
    data = detector_pipeline()
    data["nodes"] += [
        {"id": "box", "type": "roi_from_points", "inputs": {"keypoints": "body.keypoints"}},
        {"id": "crop", "type": "smooth_roi", "inputs": {"rois": "box.rois"}},
    ]
    data["outputs"].update(box="box.rois", crop="crop.rois")
    if tap:
        data["instrumentation"] = {"taps": [{"action": "record", "port": "box.rois", "name": "box"}]}
    return data


@pytest.mark.parametrize(("node_id", "params", "match"), [
    ("nope", {"expand_ratio": 2.0}, "'nope' is not a node of the run"),
    ("box", {"zoom": 2.0}, "'zoom' is not a param of the node box"),
    ("box", {"points": ["body/a"]}, "the param 'points' of the node box cannot change during a run"),
    ("crop", {"filter": "one_euro"}, "the param 'filter' of the node crop cannot change"),
    ("person", {"max_instances": 1}, "the param 'max_instances' of the node person cannot change"),
    ("box", {"expand_ratio": "wide"}, "box: .*expand_ratio"),  # a value that is not of the type
    ("box", {"min_previous_ratio": 2.0}, "box: .*min_previous_ratio"),  # a value outside the range
    ("box", {"expand_ratio": 2.0, "min_previous_ratio": 2.0}, "min_previous_ratio"),  # one bad value refuses the whole call
])
def test_v_pipeline_running_10_set_params_refuses_a_bad_node_a_bad_param_and_a_bad_value_and_changes_no_param(
    root: Path, node_id: str, params: dict, match: str,
) -> None:
    with start(root, params_pipeline()) as run:
        before = dict(run._executor.params)
        with pytest.raises(SetParamsRefused, match="(?s)V-pipeline.running-10: .*" + match):
            run.set_params(node_id, params)
        assert all(run._executor.params[key] is value for key, value in before.items())
        np.testing.assert_allclose(run.process(Frame(image(1), 0))["box"].rois[0, 2:4], [5, 20 / 3])  # the box with expand_ratio 1.0


def test_v_pipeline_running_10_set_params_is_refused_after_the_first_call_in_video_and_image(root: Path) -> None:
    for mode in ("video", "image"):
        with start(root, params_pipeline(), running_mode=mode) as run:
            run.set_params("box", {"expand_ratio": 2.0})  # before the first call: each mode takes it
            run.process(Frame(image(1), 0))
            with pytest.raises(SetParamsRefused, match=f"V-pipeline.running-10: after the first call.*`{mode}`"):
                run.set_params("box", {"expand_ratio": 3.0})
            assert run._executor.params["box"].expand_ratio == 2.0


def test_v_pipeline_running_10_set_params_is_refused_after_the_first_call_in_live_with_a_record_tap(root: Path, tmp_path: Path) -> None:
    with start(root, params_pipeline(tap=True), running_mode="live", tap_dir=tmp_path / "taps") as run:
        run.set_params("box", {"expand_ratio": 2.0})  # before the first frame, also with a record tap
        run.process(Frame(image(1), 0, 0.0))
        with pytest.raises(SetParamsRefused, match="V-pipeline.running-10: after the first call.*1 record taps"):
            run.set_params("box", {"expand_ratio": 3.0})
        assert run._executor.params["box"].expand_ratio == 2.0


def test_a_param_change_applies_from_the_next_call_to_each_camera_and_resets_no_node_state(root: Path) -> None:
    cameras = ["a", "b"]
    with start(root, params_pipeline(), camera_ids=cameras, running_mode="live") as run:
        first = run.process_batch({camera: Frame(image(1), 0, 0.0) for camera in cameras})
        states = {camera: run._executor.states[(camera, "crop")] for camera in cameras}
        run.set_params("box", {"expand_ratio": 2.0, "shift_x": 0.0})
        assert all(run._executor.states[(camera, "crop")] is states[camera] for camera in cameras)
        second = run.process_batch({camera: Frame(image(1), 1, 33.0) for camera in cameras})
        run.set_params("crop", {"previous_weight": 0.0})  # a second change keeps the first change
        third = run.process_batch({camera: Frame(image(1), 2, 66.0) for camera in cameras})
    for camera in cameras:
        size = first[camera]["box"].rois[0, 2:4]
        np.testing.assert_allclose(second[camera]["box"].rois[0, 2:4], 2 * size)
        # The `ema` filter still has the ROI of the first frame: new = 0.5 x previous + 0.5 x input.
        np.testing.assert_allclose(second[camera]["crop"].rois[0, 2:4], 1.5 * size)
        np.testing.assert_allclose(third[camera]["crop"].rois[0, 2:4], 2 * size)
        np.testing.assert_allclose(third[camera]["box"].rois[0, 2:4], 2 * size)


# ---------------------------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------------------------


def test_a_run_that_start_pipeline_made_on_one_thread_processes_on_another_thread(root: Path) -> None:
    thread, started = in_thread(lambda: start(root))
    thread.join(60)
    (run,) = started
    assert isinstance(run, PipelineRun)
    worker, found = in_thread(lambda: [run.process(Frame(image(1), index))["body"].present.tolist() for index in range(3)])
    worker.join(60)
    assert found == [[[True]] * 3]
    assert run.process(Frame(image(1), 3))["node_ran"] == {"person": True, "body": True}  # and again on the main thread
    run.close()


def test_two_runs_in_one_process_call_at_the_same_time_on_two_threads(root: Path) -> None:
    runs = [start(root, detector_pipeline(max_instances=2)), start(root, detector_pipeline(max_instances=2))]
    barrier = threading.Barrier(2)

    def work(run: PipelineRun, value: int) -> list[list[float]]:
        barrier.wait(30)
        return [run.process(Frame(image(value), index))["person_box"].score.tolist() for index in range(25)]

    threads = [in_thread(lambda run=run, value=value: work(run, value)) for run, value in zip(runs, (1, 2), strict=True)]
    for thread, _ in threads:
        thread.join(120)
    for (_, found), value in zip(threads, (1, 2), strict=True):  # each run gives the scores of its own images on each frame
        np.testing.assert_allclose(found[0], [[0.9 * value, 0.75 * value]] * 25, rtol=1e-6)
    for run in runs:
        run.close()


def test_close_from_another_thread_waits_for_the_call_that_runs_and_a_later_call_raises_run_closed_error(root: Path) -> None:
    run = start(root)
    runner = run._executor.models["person"]
    real, in_call, release = runner.run, threading.Event(), threading.Event()

    def slow(*args: Any, **kwargs: Any) -> Any:
        in_call.set()
        assert release.wait(60)
        return real(*args, **kwargs)

    runner.run = slow
    caller, result = in_thread(lambda: run.process(Frame(image(1), 0)))
    assert in_call.wait(60)
    closer, closed = in_thread(run.close)
    closer.join(0.5)
    assert closer.is_alive() and not run._executor.closed and len(run._executor.sessions.opened) == 2  # `close()` waits; nothing is freed
    release.set()
    caller.join(60)
    closer.join(60)
    assert not caller.is_alive() and not closer.is_alive() and closed == [None]
    assert result[0]["node_ran"] == {"person": True, "body": True}  # the call that ran ended normally
    assert run._executor.closed and run._executor.sessions.opened == {}
    with pytest.raises(RunClosedError):
        run.process(Frame(image(1), 1))
    run.close()  # a second `close()` does nothing


def test_two_calls_on_one_run_from_two_threads_are_serial(root: Path) -> None:
    run = start(root, camera_ids=["a", "b"], running_mode="live")
    runner = run._executor.models["person"]
    real, active, most = runner.run, [0], [0]

    def counted(*args: Any, **kwargs: Any) -> Any:
        active[0] += 1
        most[0] = max(most[0], active[0])
        try:
            return real(*args, **kwargs)
        finally:
            active[0] -= 1

    runner.run = counted
    threads = [
        in_thread(lambda camera=camera: [run.process_batch({camera: Frame(image(1), index, float(index))})[camera]["frame_index"] for index in range(20)])
        for camera in ("a", "b")
    ]
    for thread, _ in threads:
        thread.join(120)
    assert [found for _, found in threads] == [[list(range(20))]] * 2 and most == [1]
    run.close()


# ---------------------------------------------------------------------------------------------
# MediaPipe in a pipeline
# ---------------------------------------------------------------------------------------------


def test_the_built_in_mediapipe_holistic_tasks_runs_through_start_pipeline_and_gives_the_expected_point_sets(test_image: np.ndarray) -> None:
    pytest.importorskip("mediapipe", reason="mediapipe not installed")
    config = load_pipeline("mediapipe-holistic-tasks@skellytracker")
    with start_pipeline(config, camera_ids=[0], running_mode="image") as run:
        schema = run.output_schema["holistic"]
        assert [(group["name"], group["start"], group["count"]) for group in schema["groups"]] == [
            ("body", 0, 33), ("right_hand", 33, 21), ("left_hand", 54, 21), ("face", 75, 478),
        ]
        assert (schema["max_instances"], schema["geometry"], schema["depth_unit"], schema["instance_source"]) == (1, "3d", "pixel", "holistic")
        assert run.models == {} and run.warnings == ()
        result = run.process(Frame(test_image, 0))
    value = result["holistic"]
    height, width = test_image.shape[:2]
    assert len(value.point_names) == 553 and list(value.point_names) == schema["point_names"]
    assert value.xyz.shape == (1, 553, 3) and value.score.shape == (1, 553)
    assert value.present.tolist() == [True] and value.instance_score.tolist() == [1.0] and np.isfinite(value.xyz[0, :33]).all()
    assert (result["node_ran"], result["image_size"], result["timestamp_ms"]) == ({"holistic": True}, (width, height), None)


def test_two_runs_with_mediapipe_call_at_the_same_time_on_two_threads(test_image: np.ndarray) -> None:
    pytest.importorskip("mediapipe", reason="mediapipe not installed")
    config = load_pipeline("mediapipe-holistic-tasks@skellytracker")
    runs = [start_pipeline(config, camera_ids=[0], running_mode="video") for _ in range(2)]
    barrier = threading.Barrier(2)

    def work(run: PipelineRun) -> list[bool]:
        barrier.wait(60)
        return [bool(run.process(Frame(test_image, index))["holistic"].present[0]) for index in range(8)]

    try:
        threads = [in_thread(lambda run=run: work(run)) for run in runs]
        for thread, _ in threads:
            thread.join(240)
        assert [found for _, found in threads] == [[[True] * 8]] * 2
        assert all(run.warnings == () for run in runs)  # one mediapipe node with no onnx_model node downstream is not stateful
    finally:
        for run in runs:
            run.close()


# ---------------------------------------------------------------------------------------------
# The package
# ---------------------------------------------------------------------------------------------


def test_the_package_exports_the_public_api() -> None:
    names = {
        "list_pipelines", "find_pipeline", "load_pipeline", "check_pipeline", "export_pipeline", "list_node_types", "start_pipeline",
        "PipelineRun", "Frame", "PipelineEntry", "PipelineWarning", "PipelineCheck", "PipelineConfig", "InstanceKeypoints", "InstanceBoxes",
        "InstanceRois", "to_canonical", "CanonicalKeypoints", "annotate", "MissingDependencyError", "CallRefused", "SetParamsRefused",
        "RunClosedError",
    }
    assert names <= set(pipelines.__all__) and all(hasattr(pipelines, name) for name in pipelines.__all__)
