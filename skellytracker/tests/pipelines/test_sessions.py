"""The sessions of a run and the start checks that need the EP catalog (`_runtime/sessions.py`), on generated ONNX models."""
from __future__ import annotations

import dataclasses
import hashlib
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytest.importorskip("onnx", reason="onnx not installed")

from skellytracker.core.detectors.catalog import get_detector, load_detector_sidecar  # noqa: E402
from skellytracker.core.detectors.generic import download, ensure_artifact  # noqa: E402
from skellytracker.core.detectors.generic import session as generic_session  # noqa: E402
from skellytracker.core.eps.records import RunDevice  # noqa: E402
from skellytracker.core.errors import EpRequestError, EpUnavailableError, MissingDependencyError, VRAMExhaustionError  # noqa: E402
from skellytracker.core.pipelines import Frame, check_pipeline, load_pipeline, start_pipeline  # noqa: E402
from skellytracker.core.pipelines._runtime import mediapipe_tasks, sessions  # noqa: E402
from skellytracker.core.pipelines._runtime.resolve import resolve  # noqa: E402
from skellytracker.core.pipelines.config import PipelineConfig  # noqa: E402
from skellytracker.tests.detectors.onnx_models import object_model  # noqa: E402
from skellytracker.tests.detectors.test_generic_download import fake_fetch  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import (  # noqa: E402
    OBJECT_KEY,
    detector_pipeline,
    image,
    isolate,
    object_sidecar,
    write_models,
    write_sidecar,
)

MEDIAPIPE = {
    "schema_version": "2.0.0", "pipeline_id": "demo-mediapipe", "source": {"name": "demo-source", "version": "1.0.0"},
    "nodes": [{"id": "holistic", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "holistic"}}],
    "outputs": {"holistic": "holistic.keypoints"},
}


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


def pipeline(*node_eps: str | None, **person_params: Any) -> dict[str, Any]:
    """Return `detector_pipeline` with the `execution_provider` of each node: `person`, then `body`. None gives no param."""
    data = detector_pipeline(**person_params)
    for node, ep in zip(data["nodes"], node_eps or (None, None), strict=True):
        del node["params"]["execution_provider"]
        if ep is not None:
            node["params"]["execution_provider"] = ep
    return data


def start(root: Path, data: dict[str, Any], **parameters: Any):
    parameters.setdefault("camera_ids", [0])
    parameters.setdefault("running_mode", "video")
    return start_pipeline(load_pipeline(data, user_root=root), user_root=root, **parameters)


def spy_open_session(monkeypatch: pytest.MonkeyPatch, change=None) -> list[dict[str, Any]]:
    """Record each `open_session` call of the generic detectors. `change(call, session, report)` can replace the result."""
    real, calls = generic_session.open_session, []

    def open_session(entry, sidecar, size, precision, **options):
        calls.append({"key": entry.key, "precision": precision, **options})
        session, report = real(entry, sidecar, size, precision, **{**options, "execution_provider": "cpu", "device_key": None})
        return change(len(calls), session, report) if change else (session, report)

    monkeypatch.setattr(generic_session, "open_session", open_session)
    return calls


# ---------------------------------------------------------------------------------------------
# V-pipeline.running-8 and V-pipeline.running-9
# ---------------------------------------------------------------------------------------------


def test_v_pipeline_running_8_a_run_must_give_an_ep_when_a_node_has_none(root: Path) -> None:
    with pytest.raises(ValueError, match=r"V-pipeline.running-8.*\['person', 'body'\]"):
        start(root, pipeline())
    with pytest.raises(ValueError, match=r"V-pipeline.running-8.*\['body'\]"):
        start(root, pipeline("cpu", None))  # one node has its own EP, and the other has none
    start(root, pipeline(), execution_provider="cpu").close()  # with the EP of the run
    start(root, pipeline("cpu", None), execution_provider="cpu").close()
    start(root, pipeline("cpu", "cpu")).close()  # each node has its own EP: the run needs none


def test_v_pipeline_running_9_a_run_of_a_pipeline_with_no_onnx_model_node_must_not_give_an_ep(root: Path) -> None:
    config = load_pipeline(MEDIAPIPE, user_root=root)
    assert not check_pipeline(config, user_root=root).needs_execution_provider
    with pytest.raises(ValueError, match="V-pipeline.running-9"):
        start_pipeline(config, camera_ids=[0], running_mode="image", execution_provider="cpu", user_root=root)


# ---------------------------------------------------------------------------------------------
# V-pipeline.running-3 and V-pipeline.running-4
# ---------------------------------------------------------------------------------------------


def test_v_pipeline_running_3_an_absent_onnx_file_fails_the_start_with_missing_dependency_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = write_models(tmp_path / "bare", files=False)
    config = load_pipeline(detector_pipeline(), user_root=root)  # the load only warns
    assert [warning.code for warning in check_pipeline(config, user_root=root).warnings] == ["missing_dependency"] * 2
    calls = spy_open_session(monkeypatch)
    with pytest.raises(MissingDependencyError, match="V-pipeline.running-3.*person, body.*demo-body-m_b3_fp32.onnx, demo-n_b3_fp32.onnx") as error:
        start_pipeline(config, camera_ids=[0], running_mode="video", user_root=root)
    assert error.value.extra is None and error.value.node_ids == ("person", "body") and calls == []


def test_v_pipeline_running_3_a_missing_extra_fails_the_start_with_missing_dependency_error(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mediapipe_tasks, "missing_extra", lambda: "mediapipe")
    monkeypatch.setattr(mediapipe_tasks, "make_state", lambda *args: pytest.fail("the start must fail before it makes a runner"))
    config = load_pipeline(MEDIAPIPE, user_root=root)
    with pytest.raises(MissingDependencyError, match="V-pipeline.running-3.*holistic.*`mediapipe`") as error:
        start_pipeline(config, camera_ids=[0], running_mode="image", user_root=root)
    assert error.value.extra == "mediapipe" and error.value.node_ids == ("holistic",)


def test_v_pipeline_running_4_the_ep_must_be_a_catalog_key_that_is_not_reserved_with_allowed_options(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = spy_open_session(monkeypatch)
    with pytest.raises(EpRequestError, match="'nope' is not an EP key"):
        start(root, pipeline(), execution_provider="nope")
    with pytest.raises(EpRequestError, match="'trt' is reserved"):
        start(root, pipeline("cpu", "trt"))  # the EP of a node
    with pytest.raises(EpRequestError, match="has no option 'threads'"):
        start(root, pipeline(), execution_provider="cpu", ep_options={"threads": "2"})
    with pytest.raises(EpRequestError, match="takes no device"):
        start(root, pipeline(), execution_provider="cpu", device="gpu:0")
    assert calls == []  # each check is before the first session


def test_v_pipeline_running_4_an_ep_that_is_not_ready_fails_the_start_with_the_error_of_eps(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = spy_open_session(monkeypatch)
    checked = []

    def check_start(ep, options, device):
        checked.append((ep, options, device))
        raise EpUnavailableError("The EP 'cuda' is not available: not installed.", "Run `skellytracker-eps install cuda`.")

    monkeypatch.setattr(sessions, "check_start", check_start)
    with pytest.raises(EpUnavailableError, match="skellytracker-eps install cuda"):
        start(root, pipeline(), execution_provider="cuda", ep_options={}, device=["gpu:1"])
    assert checked == [("cuda", {}, ["gpu:1"])] and calls == []


# ---------------------------------------------------------------------------------------------
# The EP, the EP options and the precision of a node
# ---------------------------------------------------------------------------------------------


def test_a_node_uses_its_own_ep_and_options_else_those_of_the_run(root: Path) -> None:
    data = pipeline("cpu", None)
    data["nodes"][0]["params"]["ep_options"] = {"a": "1"}
    resolved = resolve(PipelineConfig.model_validate(data), root)
    own = sessions.node_plan(resolved.nodes["person"], "cuda", {"b": "2"})
    assert (own.execution_provider, own.ep_options, own.gpu) == ("cpu", (("a", "1"),), False)
    of_run = sessions.node_plan(resolved.nodes["body"], "cuda", {"b": "2"})
    assert (of_run.execution_provider, of_run.ep_options, of_run.gpu) == ("cuda", (("b", "2"),), True)
    # A node with its own EP and no options does not take the options of the run.
    data["nodes"][0]["params"]["ep_options"] = {}
    resolved = resolve(PipelineConfig.model_validate(data), root)
    assert sessions.node_plan(resolved.nodes["person"], "cuda", {"b": "2"}).ep_options == ()


def test_the_default_precision_is_fp16_on_a_gpu_ep_and_fp32_on_cpu_and_fp32_when_the_size_has_no_fp16(root: Path) -> None:
    node = resolve(PipelineConfig.model_validate(pipeline()), root).nodes["person"]
    assert node.model.precisions == ("fp32",)
    assert sessions.node_plan(node, "cuda", None).precision == "fp32"  # the size has no fp16 artifact
    entry = node.model.entry
    half = dataclasses.replace(entry.artifacts[0], precision="fp16", filename="demo-n_b3_fp16.onnx")
    model = dataclasses.replace(node.model, precisions=("fp32", "fp16"), entry=dataclasses.replace(entry, artifacts=(*entry.artifacts, half)))
    both = dataclasses.replace(node, model=model)
    assert sessions.node_plan(both, "cuda", None).precision == "fp16"
    assert sessions.node_plan(both, "cuda", None).filename == "demo-n_b3_fp16.onnx"
    assert sessions.node_plan(both, "cpu", None).precision == "fp32"


# ---------------------------------------------------------------------------------------------
# Session sharing, the batch and the warning ep_partial_placement
# ---------------------------------------------------------------------------------------------


def two_detectors() -> dict[str, Any]:
    data = detector_pipeline()
    data["nodes"].append({**data["nodes"][0], "id": "again"})
    data["outputs"]["again_box"] = "again.detections"
    return data


def test_two_nodes_with_the_same_artifact_share_one_session_in_a_run_and_two_runs_share_no_session(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = spy_open_session(monkeypatch)
    headers: list[dict] = []
    first = start(root, two_detectors(), camera_ids=["a", "b"], timing_sink=headers.append)
    # One session for `person` and `again`, one for `body`. The batch conversion gives the batch of the run: 2 cameras.
    assert [(call["key"], call["batch"]) for call in calls] == [(OBJECT_KEY, 2), ("demo-body@demo-exporter", 2)]
    opened = first._executor.sessions.opened
    assert sorted(item.node_ids for item in opened.values()) == [["body"], ["person", "again"]]
    assert first._executor.models["person"].detectors[0].session is first._executor.models["again"].detectors[0].session
    shared = {item["id"]: item["shared_with"] for item in headers[0]["nodes"]}
    assert shared == {"person": ["again"], "body": [], "again": ["person"]}
    assert {item["id"]: item["batching"] for item in headers[0]["nodes"]} == {"person": 2, "body": 2, "again": 2}

    second = start(root, two_detectors(), camera_ids=["a", "b"])
    assert len(calls) == 4  # the second run builds its own sessions
    ours = {id(item.session) for item in opened.values()}
    assert ours.isdisjoint({id(item.session) for item in second._executor.sessions.opened.values()})
    first.close()
    assert opened == {}  # `close()` frees the sessions of the run
    result = second.process_batch({"a": Frame(image(1), 0), "b": Frame(image(1), 0)})  # the other run still runs
    assert result["a"]["again_box"].present.tolist() == [True]
    second.close()


def test_a_host_with_no_onnx_extra_runs_the_artifact_at_its_own_batch_and_the_run_pads(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(sessions, "importlib", SimpleNamespace(util=SimpleNamespace(find_spec=lambda name: None)))
    calls = spy_open_session(monkeypatch)
    with start(root, detector_pipeline()) as run:
        assert [call["batch"] for call in calls] == [None, None]  # no batch conversion: the sessions of the artifacts, batch 3
        assert [item.batch for item in run._executor.sessions.opened.values()] == [3, 3]
        result = run.process(Frame(image(1), 0))  # one image in a batch-3 session: `run_batches` pads and drops
        assert result["person_box"].present.tolist() == [True] and result["node_ran"] == {"person": True, "body": True}


def test_ep_partial_placement_gives_one_warning_for_each_session_with_nodes_on_the_cpu_ep(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def on_gpu(call, session, report):
        placed = (("CPUExecutionProvider", 2), ("CUDAExecutionProvider", 5)) if call == 1 else (("CUDAExecutionProvider", 7),)
        cpu = {"cpu_nodes": 2, "cpu_op_types": ("NonMaxSuppression", "TopK")} if call == 1 else {"cpu_nodes": 0, "cpu_op_types": ()}
        return session, dataclasses.replace(report, requested_ep="cuda", ep_name="CUDAExecutionProvider", nodes_by_ep=placed, **cpu)

    spy_open_session(monkeypatch, on_gpu)
    received = []
    with start(root, two_detectors(), on_warning=received.append) as run:
        (warning,) = run.warnings
    assert received == [warning] and warning.code == "ep_partial_placement"
    assert warning.node_ids == ("person", "again")  # the nodes that use the session: one warning, not two
    assert warning.details == {"nodes_by_ep": {"CPUExecutionProvider": 2, "CUDAExecutionProvider": 5}, "cpu_op_types": ["NonMaxSuppression", "TopK"]}


def test_a_session_on_the_cpu_ep_gives_no_ep_partial_placement_warning(root: Path) -> None:
    with start(root, detector_pipeline()) as run:
        assert run.warnings == ()
        assert all(item.report.cpu_nodes > 0 for item in run._executor.sessions.opened.values())


# ---------------------------------------------------------------------------------------------
# A start that fails
# ---------------------------------------------------------------------------------------------


def test_vram_exhaustion_error_passes_through_start_pipeline_and_the_sessions_made_before_it_are_freed(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def second_fails(call, session, report):
        if call == 2:
            raise VRAMExhaustionError("The GPU memory is exhausted at the build of the session on 'cuda': out of memory", report)
        return session, report

    spy_open_session(monkeypatch, second_fails)
    freed: list[tuple[sessions.RunSessions, int]] = []
    close = sessions.RunSessions.close
    monkeypatch.setattr(sessions.RunSessions, "close", lambda self: (freed.append((self, len(self.opened))), close(self))[1])
    with pytest.raises(VRAMExhaustionError, match="out of memory") as error:
        start(root, detector_pipeline())
    assert isinstance(error.value, MemoryError) and error.value.exit_code == 5
    ((run_sessions, held),) = freed
    assert held == 1 and run_sessions.opened == {}  # the session of `person` existed, and the start freed it


# ---------------------------------------------------------------------------------------------
# The devices of a run
# ---------------------------------------------------------------------------------------------


def test_the_cameras_split_across_two_gpus_and_each_gpu_has_its_own_sessions_at_the_batch_of_its_cameras(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gpus = (RunDevice("gpu:0", "0000:01:00.0"), RunDevice("gpu:1", "0000:02:00.0"))
    asked = []
    monkeypatch.setattr(sessions, "check_start", lambda ep, options, device: (asked.append((ep, device)), gpus)[1])
    monkeypatch.setattr(sessions, "free_vram", lambda key: None)
    calls = spy_open_session(monkeypatch)
    cameras = ["a", "b", "c"]
    with start(root, pipeline(max_instances=2), execution_provider="cuda", camera_ids=cameras) as run:
        assert asked == [("cuda", None)]
        assert run._executor.device_of == {"a": 0, "b": 0, "c": 1}  # no VRAM value: equal weights, in blocks of camera order
        # `person`: batch = the cameras of the device. `body`: that batch x I, with I = 2.
        assert [(call["key"].split("@")[0], call["device_key"], call["batch"], call["execution_provider"]) for call in calls] == [
            ("demo", "gpu:0", 2, "cuda"), ("demo", "gpu:1", 1, "cuda"), ("demo-body", "gpu:0", 4, "cuda"), ("demo-body", "gpu:1", 2, "cuda"),
        ]
        assert len(run._executor.sessions.opened) == 4  # the sharing key holds the device
        results = run.process_batch({camera: Frame(image(1 + index), 0) for index, camera in enumerate(cameras)})
        assert list(results) == cameras
        for index, camera in enumerate(cameras):  # the scores of the test model follow the image of the camera
            np.testing.assert_allclose(results[camera]["person_box"].score, np.array([0.9, 0.75]) * (1 + index), rtol=1e-6)
            assert results[camera]["body"].present.tolist() == [True, True]


def test_a_run_with_more_gpus_than_cameras_uses_one_gpu_for_each_camera(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gpus = (RunDevice("gpu:0", "0000:01:00.0"), RunDevice("gpu:1", "0000:02:00.0"))
    monkeypatch.setattr(sessions, "check_start", lambda ep, options, device: gpus)
    calls = spy_open_session(monkeypatch)
    with start(root, pipeline(), execution_provider="cuda", vram_reserve_bytes=2**20) as run:
        assert run._executor.devices == ("gpu:0",) and {call["device_key"] for call in calls} == {"gpu:0"}
        assert run._executor.vram_reserve_bytes == 2**20 and run._executor.batch_k == 1  # k is 1: no text gives its formula


GIB = 2**30


@pytest.mark.parametrize(("weights", "cameras", "counts"), [
    ([8 * GIB, 8 * GIB], 6, [3, 3]),
    ([8 * GIB, 8 * GIB], 5, [3, 2]),  # equal weights: the extra camera goes to the first GPU
    ([24 * GIB, 8 * GIB], 6, [5, 1]),  # quotas 4.5 and 1.5: the tie of the remainders goes to the earlier GPU
    ([24 * GIB, 8 * GIB], 4, [3, 1]),
    ([24 * GIB, 8 * GIB], 3, [2, 1]),  # quotas 2.25 and 0.75
    ([24 * GIB, 8 * GIB], 2, [1, 1]),  # quotas 1.5 and 0.5: the second GPU takes one camera from the first
    ([24 * GIB, 8 * GIB], 1, [1, 0]),  # fewer cameras than GPUs: only the first GPU
    ([24 * GIB, 12 * GIB, 12 * GIB], 8, [4, 2, 2]),
    ([24 * GIB, 1 * GIB], 6, [5, 1]),  # quotas 5.76 and 0.24 round to 6 and 0: the small GPU takes one camera
    ([24 * GIB, 1 * GIB, 1 * GIB], 4, [2, 1, 1]),
    ([None, 8 * GIB], 5, [3, 2]),  # an unknown weight: equal weights
    ([0, 0], 5, [3, 2]),  # all zero: equal weights
    ([24 * GIB], 3, [3]),
    ([24 * GIB, 8 * GIB], 0, [0, 0]),
])
def test_the_cameras_split_over_the_gpus_in_proportion_to_the_weights_in_blocks_of_camera_order(weights, cameras, counts) -> None:
    camera_ids = [f"cam{index}" for index in range(cameras)]
    split = sessions.split_cameras(camera_ids, weights)
    assert list(split) == camera_ids
    assert list(split.values()) == [index for index, count in enumerate(counts) for _ in range(count)]


def test_the_weight_of_a_gpu_is_its_free_vram_minus_the_reserve_else_its_total_vram_minus_the_reserve(monkeypatch: pytest.MonkeyPatch) -> None:
    gpus = (RunDevice("gpu:0", "0000:01:00.0", vram_total_bytes=24 * GIB), RunDevice("gpu:1", "0000:02:00.0", vram_total_bytes=8 * GIB))
    free = {"gpu:0": 10 * GIB, "gpu:1": GIB // 2}
    monkeypatch.setattr(sessions, "free_vram", lambda key: free[key])
    assert sessions.gpu_weights(gpus, GIB) == [9 * GIB, 0]  # the floor is 0
    free["gpu:1"] = None  # one GPU with no free value: each GPU uses its total
    assert sessions.gpu_weights(gpus, GIB) == [23 * GIB, 7 * GIB]
    assert sessions.gpu_weights((gpus[0], RunDevice("gpu:1", "0000:02:00.0")), GIB) == [23 * GIB, None]


def test_a_run_on_two_gpus_gives_the_gpu_with_more_free_vram_more_cameras(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gpus = (RunDevice("gpu:0", "0000:01:00.0", vram_total_bytes=24 * GIB), RunDevice("gpu:1", "0000:02:00.0", vram_total_bytes=8 * GIB))
    monkeypatch.setattr(sessions, "check_start", lambda ep, options, device: gpus)
    monkeypatch.setattr(sessions, "free_vram", lambda key: {"gpu:0": 7 * GIB, "gpu:1": 3 * GIB}[key])
    spy_open_session(monkeypatch)
    cameras = ["a", "b", "c", "d"]
    with start(root, pipeline(max_instances=2), execution_provider="cuda", camera_ids=cameras, vram_reserve_bytes=GIB) as run:
        assert run._executor.device_of == {"a": 0, "b": 0, "c": 0, "d": 1}  # weights 6 GiB and 2 GiB
        # The sharing key holds the batch and the device: `person` at the cameras of each GPU, `body` at that count x I, with I = 2.
        assert [(key[4], key[1]) for key in run._executor.sessions.opened] == [("gpu:0", 3), ("gpu:1", 1), ("gpu:0", 6), ("gpu:1", 2)]
        assert list(run.process_batch({camera: Frame(image(1), 0) for camera in cameras})) == cameras


# ---------------------------------------------------------------------------------------------
# Two downloads of one artifact
# ---------------------------------------------------------------------------------------------


def test_two_threads_that_need_one_url_artifact_download_it_one_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    model, root = object_model(), tmp_path / "remote"
    sidecar = object_sidecar()
    sidecar["sizes"]["n"]["onnx"]["precision_artifacts"]["fp32"].update(url="https://example.org/demo.bin", url_sha256=hashlib.sha256(model).hexdigest())
    write_sidecar(root, sidecar, model, files=False)
    calls: list[str] = []
    fetch = fake_fetch(model, calls)

    def slow_fetch(url, sha256, part, *, opener=None):
        time.sleep(0.3)  # the second thread must wait at the lock in this time
        return fetch(url, sha256, part, opener=opener)

    monkeypatch.setattr(download, "fetch", slow_fetch)
    entry, loaded = get_detector(OBJECT_KEY, root), load_detector_sidecar(OBJECT_KEY, root)
    assert not entry.artifact("n", "fp32").downloaded
    found: list[Path] = []
    errors: list[BaseException] = []

    def work() -> None:
        try:
            found.append(ensure_artifact(entry, loaded, "n", "fp32"))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert errors == [] and len(found) == 2 and found[0] == found[1]
    assert calls == ["https://example.org/demo.bin"] and found[0].read_bytes() == model
