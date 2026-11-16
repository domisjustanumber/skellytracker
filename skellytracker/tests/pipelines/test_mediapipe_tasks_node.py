"""Tests for the node type ``mediapipe_tasks`` (stage 1.10 of the implementation plan)."""
from __future__ import annotations

import subprocess
import sys
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from skellytracker.core.pipelines._runtime import mediapipe_tasks as node
from skellytracker.core.pipelines.config import MediapipeTasksParams

_COUNTS = {"body": 33, "hand": 21, "face": 478, "holistic": 553}


def _params(variant: str, **kwargs) -> MediapipeTasksParams:
    return MediapipeTasksParams(variant=variant, **kwargs)


@pytest.mark.parametrize("variant", ["body", "hand", "face", "holistic"])
def test_output_info(variant: str):
    outputs, warnings = node.output_info("mp", _params(variant), {})
    info = outputs["keypoints"]
    assert warnings == [] and list(outputs) == ["keypoints"]
    assert (info.port_type, info.geometry, info.depth_unit) == ("keypoints", "3d", "pixel")
    assert (info.max_instances, info.instance_source, info.tracked) == (1, "mp", False)
    assert len(info.point_names) == _COUNTS[variant] == len(set(info.point_names))
    assert all(group.landmark_schema is None for group in info.groups)
    if variant == "holistic":
        assert [(g.name, g.start, g.count) for g in info.groups] == [
            ("body", 0, 33), ("right_hand", 33, 21), ("left_hand", 54, 21), ("face", 75, 478),
        ]
        assert [info.point_names[i] for i in (0, 33, 54, 75, 552)] == [
            "body/nose", "right_hand/wrist", "left_hand/wrist", "face/face_0000", "face/face_0477",
        ]
    else:
        assert [(g.name, g.start, g.count) for g in info.groups] == [("mp", 0, _COUNTS[variant])]
        assert all(name.startswith("mp/") for name in info.point_names)
    if variant == "face":
        assert info.point_names == tuple(f"mp/face_{i:04d}" for i in range(478))
    assert info.edges and all(a in info.point_names and b in info.point_names for a, b in info.edges)
    for group in info.groups:  # each group has edges, and no edge joins two groups
        assert any(a.startswith(group.name + "/") for a, _ in info.edges)
    assert all(a.split("/")[0] == b.split("/")[0] for a, b in info.edges)


def test_output_info_gives_max_instances():
    assert node.output_info("pose", _params("body", max_instances=3), {})[0]["keypoints"].max_instances == 3


def test_module_constants():
    assert node.READS_EMPTY == frozenset()
    assert node.TEMPORAL_IN == ("video", "live")
    assert node.EXTRA == "mediapipe"
    assert node.missing_extra() is None  # the test environment has the extra


_NO_MEDIAPIPE_AT_LOAD = """
import sys
from skellytracker.core.pipelines._runtime import mediapipe_tasks as node
from skellytracker.core.pipelines.config import MediapipeTasksParams
for variant in ("body", "hand", "face", "holistic"):
    node.output_info("mp", MediapipeTasksParams(variant=variant), {})
node.missing_extra()
loaded = sorted(m for m in sys.modules if m.split(".")[0] in ("mediapipe", "onnxruntime") or "mediapipe_holistic" in m)
print("LOADED", loaded, flush=True)
"""


def test_load_functions_load_no_mediapipe():
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _NO_MEDIAPIPE_AT_LOAD], capture_output=True, text=True, timeout=120,
    )
    assert result.stdout.strip().splitlines()[-1] == "LOADED []", result.stderr[-2000:]


@pytest.mark.parametrize(
    ("variant", "max_instances", "must_find"), [("body", 2, True), ("hand", 2, False), ("face", 1, False), ("holistic", 1, True)],
)
def test_image_mode(test_image, variant: str, max_instances: int, must_find: bool):
    params = _params(variant, max_instances=max_instances)
    info = node.output_info("mp", params, {})[0]["keypoints"]
    state = node.make_state(params, "image", "mp")
    try:
        outputs, same = node.run(params, {"image": test_image}, state, SimpleNamespace(timestamp_ms=None), None)
    finally:
        node.close_state(state)
    value = outputs["keypoints"]
    count = _COUNTS[variant]
    h, w = test_image.shape[:2]
    assert same is state
    assert value.point_names == info.point_names
    assert value.xyz.shape == (max_instances, count, 3) and value.score.shape == (max_instances, count)
    assert value.present.shape == value.instance_score.shape == value.track_ids.shape == (max_instances,)
    assert (value.track_ids == -1).all()
    assert value.instance_score.tolist() == [1.0 if p else 0.0 for p in value.present]
    assert value.present.tolist() == sorted(value.present.tolist(), reverse=True)  # the padding rows are last
    assert ((value.score >= 0) & (value.score <= 1)).all()
    for row, present in enumerate(value.present):
        if not present:
            assert np.isnan(value.xyz[row]).all() and (value.score[row] == 0).all()
        elif variant != "holistic":
            assert np.isfinite(value.xyz[row]).all()
            assert -w < np.median(value.xyz[row, :, 0]) < 2 * w and -h < np.median(value.xyz[row, :, 1]) < 2 * h
    if must_find:
        assert value.present[0] and np.isfinite(value.xyz[0, :33]).all()


def test_runner_without_node_id_names_the_group_by_the_variant():
    runner = node.MediapipeTasksRunner(_params("hand"), "image")
    try:
        assert runner.point_names[0] == "hand/wrist"
        value = runner.run(np.zeros((120, 160, 3), np.uint8))
    finally:
        runner.close()
    assert not value.present.any() and np.isnan(value.xyz).all() and (value.instance_score == 0).all()


@pytest.mark.parametrize(("variant", "running_mode"), [("body", "video"), ("holistic", "live")])
def test_video_timestamps_must_increase(test_image, variant: str, running_mode: str):
    runner = node.MediapipeTasksRunner(_params(variant), running_mode)
    try:
        runner.run(test_image, 0.0)
        runner.run(test_image, 0.5)  # less than 1 ms later: MediaPipe still gets an increasing integer
        for bad in (0.5, 0.2, None):
            with pytest.raises(ValueError, match="V-node.smooth_keypoints-3: timestamp_ms must increase"):
                runner.run(test_image, bad)
        assert runner.run(test_image, 1.0).present[0]  # a refused call changes no state
    finally:
        runner.close()


@pytest.mark.parametrize("variant", ["body", "holistic"])
def test_close_twice_and_run_after_close(test_image, variant: str):
    runner = node.MediapipeTasksRunner(_params(variant), "image")
    runner.close()
    runner.close()
    with pytest.raises(RuntimeError, match="closed"):
        runner.run(test_image)


def _run_frames(runner: node.MediapipeTasksRunner, image: np.ndarray, frames: int, found: list, errors: list) -> None:
    try:
        found.extend(bool(runner.run(image, index * 33.3).present[0]) for index in range(frames))
    except BaseException as error:  # noqa: BLE001 (the test thread reports each error)
        errors.append(error)


def test_two_holistic_runners_on_two_threads(test_image):
    runners = [node.MediapipeTasksRunner(_params("holistic"), "video") for _ in range(2)]
    found: list[list[bool]] = [[], []]
    errors: list[BaseException] = []
    threads = [
        threading.Thread(target=_run_frames, args=(runner, test_image, 20, rows, errors), daemon=True)
        for runner, rows in zip(runners, found, strict=True)
    ]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(240)
        assert not any(thread.is_alive() for thread in threads)
    finally:
        for runner in runners:
            runner.close()
    assert errors == []
    assert found == [[True] * 20, [True] * 20]


@pytest.mark.parametrize("variant", ["body", "holistic"])
def test_runner_made_on_the_main_thread_runs_on_a_worker_thread(test_image, variant: str):
    runner = node.MediapipeTasksRunner(_params(variant), "video")
    found: list[bool] = []
    errors: list[BaseException] = []
    thread = threading.Thread(target=_run_frames, args=(runner, test_image, 5, found, errors), daemon=True)
    try:
        thread.start()
        thread.join(240)
        assert not thread.is_alive()
        runner.run(test_image, 1000.0)  # and again on the main thread
    finally:
        runner.close()
    assert errors == []
    assert found == [True] * 5
