"""The GPU preprocess of an `onnx_model` node (pipeline.running, Implementer guidance; ADR-W4NW), on the CPU EP.

The graph path runs on `cuda` and `trt-rtx` only (`onnx_model.GRAPH_EPS`). The fixture `graph_on`
adds `cpu` to it, so the whole wiring runs here on the CPU EP with `OrtValue`s in host memory. The
tests with the marker `gpu` run the same path on each NVIDIA EP pack. The images are synthetic.

Tolerance: the graph and the CPU preprocess agree within one `uint8` step on each pixel (the resize
limit of `pre.resize.interpolation`). The object model of `pipeline_models.py` gives each score as a
constant times the mean of its input tensor, so one step on each pixel moves a score by at most the
constant: `SCORE_TOLERANCE`. The boxes and the keypoints of the models are constants: they come back
through the geometry of `resize_geometry`, which is the same host code on both paths, so they agree
to float rounding.
"""
from __future__ import annotations

import dataclasses
import gc
import weakref
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime
import pytest

from skellytracker.core.detectors.generic import inference
from skellytracker.core.detectors.processing.pre.normalize import IMAGENET_STD_RGB
from skellytracker.core.detectors.processing.pre.preprocess import preprocess_image
from skellytracker.core.eps import session as eps_session
from skellytracker.core.errors import SessionCreationError, VRAMExhaustionError
from skellytracker.core.pipelines import Frame, load_pipeline, start_pipeline
from skellytracker.core.pipelines._runtime import onnx_model
from skellytracker.tests.detectors.onnx_models import SCORES, keypoint_model, object_model
from skellytracker.tests.pipelines.pipeline_models import (
    detector_pipeline,
    isolate,
    keypoint_sidecar,
    object_sidecar,
    port_values,
    write_models,
    write_sidecar,
)

SCORE_TOLERANCE = float(SCORES.max()) * 1.0
"""One `uint8` step on each pixel moves the mean of the input by at most 1, so a score by at most its constant."""
GPU_EPS = [pytest.param(ep, marks=pytest.mark.gpu) for ep in ("cuda", "trt-rtx")]


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


@pytest.fixture
def graph_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the graph path on the CPU EP too."""
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})


@pytest.fixture
def bound_runs(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Count the calls of the bound preprocess graph and model (`run_bound`)."""
    calls: list[int] = []
    real = inference.run_bound
    monkeypatch.setattr(inference, "run_bound", lambda *args: (calls.append(1), real(*args))[1])
    return calls


@pytest.fixture
def uploads(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Count the uploads of the frames: the host array of each call of `upload_frame`."""
    found: list[Any] = []
    real = eps_session.upload_frame
    monkeypatch.setattr(eps_session, "upload_frame", lambda image, device_id, **kw: (found.append(image), real(image, device_id, **kw))[1])
    return found


def noise(height: int, width: int, seed: int) -> np.ndarray:
    """A synthetic BGR frame of random pixels: the resize of the two paths differs on it, unlike on a plain frame."""
    return np.random.default_rng(seed).integers(0, 256, (height, width, 3), dtype=np.uint8)


def on_ep(data: dict[str, Any], execution_provider: str) -> dict[str, Any]:
    for node in data["nodes"]:
        if node["type"] == "onnx_model":
            node["params"]["execution_provider"] = execution_provider
    return data


def start(root: Path, data: dict[str, Any] | None = None, **parameters: Any) -> Any:
    parameters.setdefault("camera_ids", ["a", "b"])
    parameters.setdefault("running_mode", "video")
    return start_pipeline(load_pipeline(data or detector_pipeline(), user_root=root), user_root=root, **parameters)


def run_calls(root: Path, calls: list[dict[Any, Frame]], data: dict[str, Any] | None = None, **parameters: Any) -> tuple[list[dict], Any]:
    """Run each call in one run. Return the results and the run, which is closed."""
    with start(root, data, **parameters) as run:
        results = [run.process_batch(frames) for frames in calls]
    return results, run


def two_camera_calls(sizes: dict[str, tuple[int, int]], count: int = 2) -> list[dict[str, Frame]]:
    return [{camera: Frame(noise(*size, seed=10 * index + n), index) for n, (camera, size) in enumerate(sizes.items())} for index in range(count)]


def assert_agree(graph: list[dict], cpu: list[dict], score_tolerance: float = SCORE_TOLERANCE) -> None:
    """The results of the graph path and of the CPU path agree within the tolerance of the module docstring."""
    assert len(graph) == len(cpu)
    for graph_call, cpu_call in zip(graph, cpu, strict=True):
        assert list(graph_call) == list(cpu_call)
        for camera, expected in cpu_call.items():
            found = graph_call[camera]
            np.testing.assert_array_equal(found["boxes"].present, expected["boxes"].present)
            np.testing.assert_allclose(found["boxes"].xyxy, expected["boxes"].xyxy, rtol=0, atol=1e-9)
            np.testing.assert_allclose(found["boxes"].score, expected["boxes"].score, rtol=0, atol=score_tolerance)
            np.testing.assert_array_equal(found["wholebody"].present, expected["wholebody"].present)
            np.testing.assert_allclose(found["wholebody"].xy, expected["wholebody"].xy, rtol=0, atol=1e-9)
            assert found["node_ran"] == expected["node_ran"]


def cpu_warnings(run: Any) -> list[Any]:
    return [warning for warning in run.warnings if warning.code == onnx_model.PREPROCESSED_ON_CPU]


# ---------------------------------------------------------------------------------------------
# The graph path agrees with the CPU path
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sizes", [{"a": (40, 48), "b": (40, 48)}, {"a": (40, 48), "b": (36, 64)}], ids=["one_size", "two_sizes"])
def test_the_graph_path_gives_the_results_of_the_cpu_path_for_a_detector_and_a_top_down_node(
    root: Path, monkeypatch: pytest.MonkeyPatch, bound_runs: list[int], sizes: dict[str, tuple[int, int]],
) -> None:
    calls = two_camera_calls(sizes)
    cpu, _ = run_calls(root, calls)
    assert bound_runs == []
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    graph, run = run_calls(root, calls)
    assert len(bound_runs) == 2 * len(calls)  # each node of each call ran its preprocess graph
    assert cpu_warnings(run) == []
    assert all(result["boxes"].present.any() and result["wholebody"].present.any() for call in graph for result in call.values())
    assert_agree(graph, cpu)


def test_each_camera_frame_uploads_one_time_for_each_call_and_the_cpu_path_uploads_none(root: Path, monkeypatch: pytest.MonkeyPatch, uploads: list[Any]) -> None:
    calls = two_camera_calls({"a": (32, 32), "b": (32, 48)}, count=3)
    run_calls(root, calls)
    assert uploads == []
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    with start(root) as run:
        for frames in calls:
            before = len(uploads)
            run.process_batch(frames)
            assert len(uploads) - before == 2  # the detector and the top-down node share the upload of each camera
            assert {id(image) for image in uploads[before:]} == {id(frame.image) for frame in frames.values()}


def test_the_model_input_is_the_graph_output_in_device_memory_with_no_host_copy(root: Path, graph_on: None, monkeypatch: pytest.MonkeyPatch) -> None:
    bound, read = spy_bindings(monkeypatch)
    with start(root) as run:
        run.process_batch(two_camera_calls({"a": (40, 48), "b": (36, 64)}, count=1)[0])
    assert len(bound) == 2 and all(value.device_name() == "cpu" for value in bound)  # one model input for each node
    assert not {id(value) for value in bound} & read


def spy_bindings(monkeypatch: pytest.MonkeyPatch) -> tuple[list[Any], set[int]]:
    """Return the `OrtValue`s that a model binding took as its input `input`, and the ids of each `OrtValue` that `numpy()` read."""
    bound: list[Any] = []
    read: set[int] = set()
    outputs: set[int] = set()
    binding, value = onnxruntime.IOBinding, onnxruntime.OrtValue
    real_bind, real_outputs, real_numpy = binding.bind_ortvalue_input, binding.get_outputs, value.numpy

    def bind(self: Any, name: str, ortvalue: Any) -> None:
        if name == "input":
            assert id(ortvalue) in outputs  # the object that the graph binding gave
            bound.append(ortvalue)
        real_bind(self, name, ortvalue)

    def get_outputs(self: Any) -> Any:
        found = real_outputs(self)
        outputs.update(id(item) for item in found)
        return found

    monkeypatch.setattr(binding, "bind_ortvalue_input", bind)
    monkeypatch.setattr(binding, "get_outputs", get_outputs)
    monkeypatch.setattr(value, "numpy", lambda self: (read.add(id(self)), real_numpy(self))[1])
    return bound, read


class FakeBinding:
    def __init__(self, outputs: list[Any], log: list[tuple]) -> None:
        self.outputs, self.log = outputs, log

    def bind_ortvalue_input(self, name: str, value: Any) -> None:
        self.log.append(("input", name, value))

    def bind_cpu_input(self, name: str, value: np.ndarray) -> None:
        self.log.append(("cpu_input", name, value))

    def bind_output(self, name: str, *device: Any) -> None:
        self.log.append(("output", name, device))

    def synchronize_outputs(self) -> None:
        pass

    def get_outputs(self) -> list[Any]:
        return self.outputs

    def copy_outputs_to_cpu(self) -> list[Any]:
        return self.outputs


class FakeSession:
    def __init__(self, binding: FakeBinding, error: Exception | None = None) -> None:
        self.binding, self.error = binding, error

    def io_binding(self) -> FakeBinding:
        return self.binding

    def run_with_iobinding(self, binding: FakeBinding) -> None:
        if self.error is not None:
            raise self.error


class GraphOutput:
    """The `OrtValue` of the graph output `tensor`: a host copy of it would call `numpy()`."""

    def numpy(self) -> None:
        raise AssertionError("the graph output was copied to the host")


def test_run_preprocess_and_run_bound_bind_the_graph_output_as_the_model_input_and_map_an_out_of_memory_error() -> None:
    tensor, log = GraphOutput(), []
    pre, model = FakeSession(FakeBinding([tensor], log)), FakeSession(FakeBinding([np.ones(2, np.float32)], log))
    assert eps_session.run_preprocess(pre, ["frame0", "frame1"], np.array([1, 0]), None, "cuda", 2) is tensor
    found = eps_session.run_bound(model, "input", ["out"], tensor)
    assert found[0].tolist() == [1.0, 1.0]
    assert [entry[:2] for entry in log] == [
        ("input", "frame_0"), ("input", "frame_1"), ("cpu_input", "index"), ("output", "tensor"), ("input", "input"), ("output", "out"),
    ]
    assert log[3][2] == ("cuda", 2) and log[4][2] is tensor and log[5][2] == ()  # the model outputs go to the host
    for failing in (
        lambda: eps_session.run_preprocess(FakeSession(FakeBinding([], []), RuntimeError("CUDA failure: out of memory")), ["f"], np.array([0]), np.zeros((1, 2, 3))),
        lambda: eps_session.run_bound(FakeSession(FakeBinding([], []), RuntimeError("cudaMalloc failed")), "input", ["out"], tensor),
    ):
        with pytest.raises(VRAMExhaustionError):
            failing()


# ---------------------------------------------------------------------------------------------
# The cameras of a call
# ---------------------------------------------------------------------------------------------


def test_a_camera_that_is_not_in_the_call_and_a_frame_with_no_box_keep_the_graph_and_the_cpu_results(
    root: Path, monkeypatch: pytest.MonkeyPatch, bound_runs: list[int],
) -> None:
    blank = np.zeros((32, 32, 3), np.uint8)  # no pad and a mean of 0: the detector finds no box, so `body` does not run for it
    calls = [
        {"a": Frame(blank, 0, 0.0), "b": Frame(noise(32, 32, 1), 0, 0.0)},
        {"b": Frame(noise(32, 32, 2), 1, 40.0)},  # `a` is not ready in `live`
        {"a": Frame(noise(32, 32, 3), 2, 80.0), "b": Frame(noise(32, 32, 4), 2, 80.0)},
    ]
    cpu, _ = run_calls(root, calls, running_mode="live")
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    graph, run = run_calls(root, calls, running_mode="live")
    assert graph[0]["a"]["node_ran"] == {"person": True, "body": False}
    assert_agree(graph, cpu)
    assert len(bound_runs) == 6 and cpu_warnings(run) == []


def test_each_camera_has_a_fixed_slot_so_the_frame_sizes_change_only_with_a_real_size_change(root: Path, graph_on: None, uploads: list[Any]) -> None:
    """4 cameras of 2 sizes, 20 calls with other ready cameras and cameras with no box: one preprocess session for each node.

    The square frames have no letterbox pad, so a blank frame has the mean 0 and the detector finds no box in it.
    """
    sizes = {"a": (32, 32), "b": (64, 64), "c": (32, 32), "d": (64, 64)}
    rng = np.random.default_rng(7)
    with start(root, camera_ids=list(sizes), running_mode="live") as run:
        for index in range(20):
            cameras = list(sizes) if index == 0 else [camera for camera in sizes if rng.random() < 0.6] or ["c"]
            run.process_batch({
                camera: Frame(noise(*sizes[camera], seed=index) if rng.random() < 0.7 else np.zeros((*sizes[camera], 3), np.uint8), index, 40.0 * index)
                for camera in cameras
            })
        keys = list(run._executor.sessions.preprocess)  # noqa: SLF001
        assert len(keys) == 2 and {key[3] for key in keys} == {((32, 32), (64, 64), (32, 32), (64, 64))} and cpu_warnings(run) == []
        assert len(run._executor.zero_frames) == 2  # noqa: SLF001 - one zero frame for each size
        run.process_batch({"a": Frame(noise(48, 48, 1), 20, 800.0)})  # a real size change of one camera
        keys = list(run._executor.sessions.preprocess)  # noqa: SLF001
        assert len(keys) == 4 and ((48, 48), (64, 64), (32, 32), (64, 64)) in {key[3] for key in keys}
        assert cpu_warnings(run) == []


def test_a_camera_before_its_first_frame_takes_the_size_of_a_frame_of_its_device(root: Path, graph_on: None) -> None:
    with start(root, running_mode="live") as run:
        run.process_batch({"b": Frame(noise(40, 48, 1), 0, 0.0)})
        run.process_batch({"b": Frame(noise(40, 48, 2), 1, 40.0)})
        assert {key[3] for key in run._executor.sessions.preprocess} == {((48, 40), (48, 40))}  # noqa: SLF001
        run.process_batch({"a": Frame(noise(32, 32, 3), 2, 80.0)})  # the first frame of `a`: its real size
        assert {key[3] for key in run._executor.sessions.preprocess} == {((48, 40), (48, 40)), ((32, 32), (48, 40))}  # noqa: SLF001


# ---------------------------------------------------------------------------------------------
# The CPU preprocess and the warning preprocessed_on_cpu
# ---------------------------------------------------------------------------------------------


def three_calls() -> list[dict[str, Frame]]:
    return two_camera_calls({"a": (40, 48), "b": (40, 48)}, count=3)


def check_one_warning_for_each_node(run: Any, nodes: list[str], reason: str, frame_sizes: list[list[int]], cause: str = "") -> None:
    warnings = cpu_warnings(run)
    assert [warning.node_ids for warning in warnings] == [(node,) for node in nodes]
    assert [{**warning.details, "cause": None} for warning in warnings] == [
        {"node": node, "reason": reason, "frame_sizes": frame_sizes, "cause": None} for node in nodes
    ]
    assert all(cause in warning.details["cause"] for warning in warnings)


def area_models(root: Path) -> Path:
    """The models with `interpolation: area` for the detector: the graph refuses it (the resize limit)."""
    sidecar = object_sidecar()
    sidecar["input"]["resize"]["interpolation"] = "area"
    write_sidecar(root, sidecar, object_model())
    write_sidecar(root, keypoint_sidecar(), keypoint_model())
    return root


def test_a_combination_that_the_graph_refuses_gives_one_warning_and_the_cpu_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = area_models(tmp_path / "area")
    cpu, _ = run_calls(root, three_calls())
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    received: list[Any] = []
    with start(root, on_warning=received.append) as run:
        assert cpu_warnings(run) == []  # the warning comes at the first call that uses the CPU preprocess
        graph = [run.process_batch(frames) for frames in three_calls()]
    check_one_warning_for_each_node(run, ["person"], "graph_refused", [[48, 40], [48, 40]], cause="'area'")
    assert "area" in cpu_warnings(run)[0].message and cpu_warnings(run) == [item for item in received if item.code == "preprocessed_on_cpu"]
    assert_agree(graph, cpu)


@pytest.mark.parametrize("failure", ["error", "cpu_nodes"])
def test_a_graph_session_that_does_not_build_gives_one_warning_and_no_second_build(
    root: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    builds: list[int] = []
    real = eps_session.build_session

    def build(*args: Any, **kwargs: Any) -> Any:
        builds.append(1)
        if failure == "error":
            raise SessionCreationError("the session on the EP 'cpu' failed at its build: test")
        session, report = real(*args, **kwargs)
        return session, dataclasses.replace(report, cpu_nodes=3, ep_name="CUDAExecutionProvider")  # a node on the CPU EP of a GPU EP

    cpu, _ = run_calls(root, three_calls())
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    monkeypatch.setattr(eps_session, "build_session", build)  # the preprocess sessions only: the model sessions are built through `open_session`
    graph, run = run_calls(root, three_calls())
    assert len(builds) == 2  # one build for each node, at the first call; no build again for that set of frame sizes
    check_one_warning_for_each_node(run, ["person", "body"], "session_not_built", [[48, 40], [48, 40]])
    assert_agree(graph, cpu)


def test_a_fifth_set_of_frame_sizes_gives_one_warning_and_the_cpu_results(root: Path, monkeypatch: pytest.MonkeyPatch, bound_runs: list[int]) -> None:
    sizes = [(32, 32), (32, 40), (40, 32), (48, 48), (36, 52), (32, 32)]  # 5 sets, then the first set again
    calls = [{0: Frame(noise(*size, seed=index), index)} for index, size in enumerate(sizes)]
    cpu, _ = run_calls(root, calls, camera_ids=[0], running_mode="image")
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    graph = []
    with start(root, camera_ids=[0], running_mode="image") as run:
        for index, frames in enumerate(calls):
            graph.append(run.process_batch(frames))
            assert len(cpu_warnings(run)) == (2 if index >= 4 else 0)
            if index == 3:
                assert len(run._executor.sessions.preprocess) == 8  # noqa: SLF001 - 4 sets for each node
        assert len(run._executor.sessions.preprocess) == 8  # noqa: SLF001
    assert len(bound_runs) == 2 * 5  # the calls 0 to 3 and 5 on the graph; the call 4 on the CPU
    check_one_warning_for_each_node(run, ["person", "body"], "frame_size_cap", [[52, 36]])
    assert_agree(graph, cpu)


def test_a_run_on_the_cpu_ep_gives_no_warning_preprocessed_on_cpu(root: Path, bound_runs: list[int]) -> None:
    _, run = run_calls(root, three_calls())
    assert run.warnings == () and bound_runs == []


# ---------------------------------------------------------------------------------------------
# The timing header and the close
# ---------------------------------------------------------------------------------------------


def preprocess_providers(root: Path) -> dict[str, Any]:
    lines: list[dict] = []
    with start(root, timing_sink=lines.append):
        pass
    return {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]}


def test_stage_providers_preprocess_is_the_provider_of_the_graph_at_the_start_else_null(root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert preprocess_providers(root) == {"person": None, "body": None}  # an EP with no graph path
    monkeypatch.setattr(onnx_model, "GRAPH_EPS", onnx_model.GRAPH_EPS | {"cpu"})
    assert preprocess_providers(root) == {"person": "CPUExecutionProvider", "body": "CPUExecutionProvider"}
    assert preprocess_providers(area_models(tmp_path / "area")) == {"person": None, "body": "CPUExecutionProvider"}


def none_models(root: Path) -> Path:
    """The models with `method: none` for the detector: the graph refuses frames of two sizes."""
    sidecar = object_sidecar()
    sidecar["input"]["resize"] = {"method": "none"}
    del sidecar["sizes"]["n"]["input"]["resize"]
    write_sidecar(root, sidecar, object_model())
    write_sidecar(root, keypoint_sidecar(), keypoint_model())
    return root


def test_method_none_with_two_camera_slots_is_refused_at_the_start_and_the_warning_gives_the_refusal(tmp_path: Path, graph_on: None) -> None:
    root = none_models(tmp_path / "none")
    lines: list[dict] = []
    with start(root, camera_ids=[0], timing_sink=lines.append):
        pass
    assert {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]}["person"] == "CPUExecutionProvider"  # one slot
    lines.clear()
    with start(root, timing_sink=lines.append) as run:
        assert {item["id"]: item["stage_providers"]["preprocess"] for item in lines[0]["nodes"]}["person"] is None
        run.process_batch({"a": Frame(noise(32, 32, 1), 0), "b": Frame(noise(32, 32, 2), 0)})
    check_one_warning_for_each_node(run, ["person"], "graph_refused", [[32, 32], [32, 32]], cause="different source sizes")


def test_the_preprocess_session_has_no_output_pixels(root: Path, graph_on: None) -> None:
    with start(root) as run:
        run.process_batch(three_calls()[0])
        found = [[output.name for output in session.get_outputs()] for session, _, _ in run._executor.sessions.preprocess.values()]  # noqa: SLF001
    assert found == [["tensor"], ["tensor"]]


def test_close_frees_the_device_frames_then_the_preprocess_sessions_and_the_model_sessions(root: Path, graph_on: None, monkeypatch: pytest.MonkeyPatch) -> None:
    uploaded: list[Any] = []
    real = eps_session.upload_frame
    monkeypatch.setattr(eps_session, "upload_frame", lambda *args, **kw: (uploaded.append(weakref.ref(value := real(*args, **kw))), value)[1])
    with start(root, running_mode="live") as run:
        run.process_batch({"a": Frame(noise(32, 32, 1), 0, 0.0), "b": Frame(noise(32, 32, 2), 0, 0.0)})
        run.process_batch({"b": Frame(noise(32, 32, 3), 1, 40.0)})  # a zero frame for `a`
        executor = run._executor  # noqa: SLF001
        sessions = executor.sessions
        held = [weakref.ref(session) for session, _, _ in sessions.preprocess.values()]
        held += [weakref.ref(item.session) for item in sessions.opened.values()]
        assert len(uploaded) == 4 and len(executor.zero_frames) == 1
    assert len(held) == 4 and sessions.preprocess == {} and sessions.opened == {}
    assert executor.port_values == {} and executor.zero_frames == {} and executor.call_slots == {}
    gc.collect()
    assert [ref() for ref in held + uploaded] == [None] * 8  # no device frame and no session is left


# ---------------------------------------------------------------------------------------------
# The model input of each item: the tensor of `preprocess_image` of its own frame and ROI
# ---------------------------------------------------------------------------------------------


def spy_model_inputs(monkeypatch: pytest.MonkeyPatch) -> list[np.ndarray]:
    """Keep a host copy of each model input batch at the binding seam (`run_bound`). Only these tests copy it."""
    seen: list[np.ndarray] = []
    real = inference.run_bound
    monkeypatch.setattr(inference, "run_bound", lambda session, name, names, tensor: (seen.append(tensor.numpy().copy()), real(session, name, names, tensor))[1])
    return seen


def check_model_inputs(run: Any, frames: dict[Any, Frame], seen: list[np.ndarray]) -> int:
    """Each item of each model gets the tensor of its own frame (and ROI) within one `uint8` step. Return the batch count of `body`."""
    nodes = run._executor.resolved.nodes  # noqa: SLF001
    person, body = nodes["person"].model, nodes["body"].model
    detector = np.concatenate([batch for batch in seen if batch.shape[2:] == (32, 32)])
    expected = np.stack([preprocess_image(frame.image, person.sidecar, person.size, "fp32")[0] for frame in frames.values()])
    np.testing.assert_allclose(detector[: len(expected)], expected, rtol=0, atol=1.0 + 1e-4)  # normalization none: 0-255
    boxes = {camera: port_values(run, camera)["person.boxes"] for camera in frames}
    items = [(camera, boxes[camera].boxes[row].tolist()) for camera in frames for row in np.flatnonzero(boxes[camera].present)]
    batches = [batch for batch in seen if batch.shape[2:] == (16, 12)]
    if items:
        crops = np.concatenate(batches)
        expected = np.stack([preprocess_image(frames[camera].image, body.sidecar, body.size, "fp32", roi)[0] for camera, roi in items])
        np.testing.assert_allclose(crops[: len(expected)], expected, rtol=0, atol=1.0 / min(IMAGENET_STD_RGB) + 1e-4)  # imagenet: 1 step / std
    seen.clear()
    return len(batches)


def bright(height: int, width: int, seed: int, offset: int) -> np.ndarray:
    """Random pixels with a brightness offset for each camera: a frame in the wrong slot gives another tensor."""
    return (noise(height, width, seed) // 2 + offset).astype(np.uint8)


def test_each_item_gets_the_tensor_of_its_own_frame_and_roi_on_two_cameras_of_two_sizes(root: Path, graph_on: None, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = spy_model_inputs(monkeypatch)
    with start(root, detector_pipeline(max_instances=2)) as run:
        for index in range(2):
            frames = {"a": Frame(bright(40, 48, index, 0), index), "b": Frame(bright(36, 64, 10 + index, 120), index)}
            run.process_batch(frames)
            assert all(port_values(run, camera)["person.boxes"].present.sum() == 2 for camera in frames)  # several boxes on each camera
            check_model_inputs(run, frames, seen)


def test_each_item_gets_its_own_frame_with_a_camera_missing_from_the_call_and_mixed_sizes(root: Path, graph_on: None, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = spy_model_inputs(monkeypatch)
    sizes = {"a": (40, 48), "b": (36, 64), "c": (32, 32)}
    with start(root, detector_pipeline(max_instances=2), camera_ids=list(sizes), running_mode="live") as run:
        for index, cameras in enumerate([["a", "b", "c"], ["b", "c"], ["c", "a"], ["b"]]):
            frames = {camera: Frame(bright(*sizes[camera], index, 60 * n), index, 40.0 * index) for n, camera in enumerate(sizes) if camera in cameras}
            run.process_batch(frames)
            check_model_inputs(run, frames, seen)
        assert len(run._executor.sessions.preprocess) == 2  # noqa: SLF001 - the fixed slots keep one set of frame sizes


def test_each_item_gets_its_own_frame_in_the_padded_last_group(root: Path, graph_on: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """The batch of `body` is 3 cameras x 2 rows = 6. A camera with no box leaves 4 crops: the group has 2 padding items.

    A sidecar batch of 3 is valid only with a conversion profile, so the demo models give no run with two groups.
    """
    seen = spy_model_inputs(monkeypatch)
    with start(root, detector_pipeline(max_instances=2), camera_ids=["a", "b", "c"]) as run:
        frames = {"a": Frame(np.zeros((32, 32, 3), np.uint8), 0), "b": Frame(bright(40, 48, 1, 0), 0), "c": Frame(bright(36, 64, 2, 120), 0)}
        run.process_batch(frames)
        assert [batch.shape[0] for batch in seen if batch.shape[2:] == (16, 12)] == [6]
        assert check_model_inputs(run, frames, seen) == 1


# ---------------------------------------------------------------------------------------------
# The GPU EPs (`-m gpu`)
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("execution_provider", GPU_EPS)
def test_the_graph_path_on_a_gpu_ep_gives_the_results_of_the_cpu_ep(root: Path, execution_provider: str, bound_runs: list[int]) -> None:
    calls = two_camera_calls({"a": (720, 1280), "b": (480, 640)})
    cpu, _ = run_calls(root, calls)
    graph, run = run_calls(root, calls, on_ep(detector_pipeline(), execution_provider))
    assert len(bound_runs) == 2 * len(calls) and cpu_warnings(run) == []
    assert_agree(graph, cpu)


@pytest.mark.parametrize("execution_provider", GPU_EPS)
def test_the_model_input_on_a_gpu_ep_is_the_graph_output_in_gpu_memory(root: Path, execution_provider: str, monkeypatch: pytest.MonkeyPatch) -> None:
    bound, read = spy_bindings(monkeypatch)
    with start(root, on_ep(detector_pipeline(), execution_provider)) as run:
        run.process_batch(two_camera_calls({"a": (720, 1280), "b": (480, 640)}, count=1)[0])
    assert len(bound) == 2 and all(value.device_name() == "cuda" for value in bound)
    assert not {id(value) for value in bound} & read


# The GPU JPEG decoder in the frame stage. Tolerance: nvJPEG and `cv2.imdecode` differ by at most 3 `uint8`
# steps on each pixel (pipeline.running, Implementer guidance), and the graph preprocess by at most 1 more, so
# a score moves by at most 4 x `SCORE_TOLERANCE`. The boxes and the keypoints are constants of the models.

JPEG_SCORE_TOLERANCE = 4 * SCORE_TOLERANCE
JPEG_SPANS = ["frame.decode", "frame.upload", "pipeline.run"]


def without_huffman_tables(data: bytes) -> bytes:
    """Remove each DHT segment of a baseline JPEG: OpenCV then uses the standard tables (as for MJPEG), and nvJPEG refuses it."""
    out, i = bytearray(data[:2]), 2
    while data[i + 1] != 0xDA:  # the segments before the start of scan
        end = i + 2 + int.from_bytes(data[i + 2 : i + 4], "big")
        if data[i + 1] != 0xC4:
            out += data[i:end]
        i = end
    return bytes(out + data[i:])


def jpeg_camera_calls(count: int, refused: bool = False) -> list[dict[str, Frame]]:
    """Two JPEG cameras of two sizes with rotation_deg 0 and 90, and an array camera. `refused`: camera `b` has no Huffman tables."""
    from skellytracker.tests.test_decode_nvidia import jpeg, picture

    calls = []
    for index in range(count):
        b = jpeg(picture(640, 480, 10 * index + 2), "422")
        calls.append({
            "a": Frame(jpeg(picture(1280, 720, 10 * index + 1)), index),
            "b": Frame(without_huffman_tables(b) if refused else b, index, rotation_deg=90),
            "c": Frame(noise(360, 480, 10 * index + 3), index),
        })
    return calls


def gpu_decoder_or_skip(execution_provider: str) -> None:
    from skellytracker.core.eps import registration

    if registration.prepare_jpeg_decoder(execution_provider) is None:
        pytest.skip(f"{execution_provider} has no usable GPU JPEG decoder component")


@pytest.mark.parametrize("execution_provider", GPU_EPS)
def test_jpeg_frames_on_a_gpu_ep_decode_on_the_gpu_with_no_upload_and_give_the_results_of_the_cpu_path(
    root: Path, execution_provider: str, uploads: list[Any],
) -> None:
    gpu_decoder_or_skip(execution_provider)
    calls = jpeg_camera_calls(3)
    cpu, _ = run_calls(root, calls, camera_ids=["a", "b", "c"])
    data = on_ep(detector_pipeline(), execution_provider)
    data["instrumentation"] = {"timing_spans": JPEG_SPANS}
    lines: list[dict] = []
    uploads.clear()
    with start(root, data, camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        gpu = []
        for frames in calls:
            gpu.append(run.process_batch(frames))
            for camera in "ab":
                frame = port_values(run, camera)["frame.image"]
                assert frame.pixels is None and frame.device.device_name() == "cuda"
        warnings = [warning for warning in run.warnings if warning.code == "jpeg_decoded_on_cpu"]
    assert warnings == [] and [id(image) for image in uploads] == [id(frames["c"].image) for frames in calls]  # only the array camera uploads
    assert [(event["span"], [image["camera_id"] for image in event["images"]]) for event in lines[1:] if event["node_id"] == "frame"] == [
        ("decode", ["a", "b"]), ("upload", ["c"])] * len(calls)
    assert_agree(gpu, cpu, JPEG_SCORE_TOLERANCE)


@pytest.mark.parametrize("execution_provider", GPU_EPS)
def test_a_jpeg_that_the_gpu_decoder_refuses_decodes_on_the_cpu_with_one_warning_on_a_gpu_ep(root: Path, execution_provider: str) -> None:
    gpu_decoder_or_skip(execution_provider)
    calls = jpeg_camera_calls(2, refused=True)
    cpu, _ = run_calls(root, calls, camera_ids=["a", "b", "c"])
    data = on_ep(detector_pipeline(), execution_provider)
    data["instrumentation"] = {"timing_spans": JPEG_SPANS}
    lines: list[dict] = []
    with start(root, data, camera_ids=["a", "b", "c"], timing_sink=lines.append) as run:
        gpu = [run.process_batch(frames) for frames in calls]
        assert port_values(run, "a")["frame.image"].pixels is None and port_values(run, "b")["frame.image"].pixels is not None
        warnings = [warning for warning in run.warnings if warning.code == "jpeg_decoded_on_cpu"]
    assert [dict(warning.details) for warning in warnings] == [{"reason": "decoder_refused", "camera_id": "b"}]
    assert [(event["span"], [image["camera_id"] for image in event["images"]]) for event in lines[1:] if event["node_id"] == "frame"] == [
        ("decode", ["a", "b"]), ("upload", ["b", "c"])] * len(calls)
    assert_agree(gpu, cpu, JPEG_SCORE_TOLERANCE)
