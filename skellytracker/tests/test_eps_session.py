"""`ensure_registered()`, `build_session()` and `verify()`: fakes for the GPU EPs, and real CPU sessions on generated models."""

import dataclasses
import logging
import pickle
import types

import numpy as np
import onnxruntime
import pytest

from skellytracker.core import eps
from skellytracker.core.eps import _verify_child, recommendation, registration, session, state, store, verification
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.errors import EpRequestError, EpUnavailableError, SessionCreationError, VRAMExhaustionError
from skellytracker.tests import child_fakes
from skellytracker.tests.hw_fakes import GIB, fake_pack, gpu, host, reviewed_rows_for_each_gpu

CUDA, TRT, CPU = "CUDAExecutionProvider", "NvTensorRTRTXExecutionProvider", "CPUExecutionProvider"
SMALL = gpu(vram=8 * GIB, bus="0000:01:00.0")
LARGE = gpu(vram=24 * GIB, bus="0000:02:00.0", device_id=0x2684, name="RTX 4090")


def model_bytes() -> bytes:
    """A generated model: `y = Relu(x + 1)` on a 2x3 float input."""
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    graph = helper.make_graph(
        [helper.make_node("Add", ["x", "one"], ["s"]), helper.make_node("Relu", ["s"], ["y"])], "g",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 3])], [helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 3])],
        [numpy_helper.from_array(np.ones((2, 3), dtype=np.float32), "one")])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    return model.SerializeToString()


class FakeOptions:
    """Records what `open_session()` sets on the `SessionOptions`."""

    def __init__(self):
        self.entries, self.devices, self.provider_options = {}, None, None

    def add_session_config_entry(self, name, value):
        self.entries[name] = value

    def add_provider_for_devices(self, devices, options):
        self.devices, self.provider_options = devices, dict(options)


class FakeSession:
    """A session of a fake GPU EP. The class attributes set what it does."""

    created: list = []
    build_error: Exception | None = None
    run_error: Exception | None = None
    providers = [CUDA, CPU]
    nodes = {CUDA: ["Conv", "Relu", "Conv", "Resize", "Sigmoid"], CPU: ["Clip", "Clip", "Slice"]}

    def __init__(self, model, sess_options=None, providers=None, **kwargs):
        FakeSession.created.append((sess_options, providers, kwargs))
        if FakeSession.build_error is not None:
            raise FakeSession.build_error

    def get_inputs(self):
        return [types.SimpleNamespace(name="x", shape=["batch", 3, None, 4], type="tensor(float16)")]

    def run(self, outputs, feed):
        assert feed["x"].shape == (1, 3, 1, 4) and feed["x"].dtype == np.float16
        if FakeSession.run_error is not None:
            raise FakeSession.run_error

    def get_providers(self):
        return FakeSession.providers

    def get_provider_graph_assignment_info(self):
        return [types.SimpleNamespace(ep_name=name, get_nodes=lambda ops=ops: [types.SimpleNamespace(op_type=op) for op in ops])
                for name, ops in FakeSession.nodes.items()]


def fake_device(ep_name, info, luid=None):
    hardware = types.SimpleNamespace(vendor_id=info.pci_vendor_id, device_id=info.pci_device_id, metadata={"LUID": str(luid)} if luid else {})
    return types.SimpleNamespace(ep_name=ep_name, device=hardware, ep_options={"device_id": "0"})


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "eps"))
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    monkeypatch.setattr(registration, "_registered", {})
    monkeypatch.setattr(registration, "_groups", {})
    monkeypatch.setattr(store, "_warned", set())
    monkeypatch.setattr(store, "cache_root", lambda: tmp_path / "ep-cache")
    monkeypatch.setattr(registration, "core_mismatch", lambda catalog: None)
    reviewed_rows_for_each_gpu(monkeypatch)  # these tests are not about the check rule; `test_the_check_rule_*` are


@pytest.fixture
def gpu_host(monkeypatch):
    """A host with two NVIDIA GPUs, the two packs in the store, and a fake ONNX Runtime for the GPU EPs."""
    for module in (session, verification):
        monkeypatch.setattr(module, "probe_host", lambda: host(SMALL, LARGE))
    fake_pack("cuda")
    fake_pack("trt-rtx")
    calls = []
    monkeypatch.setattr(onnxruntime, "register_execution_provider_library", lambda name, path: calls.append((name, path)))
    devices = [fake_device(name, info) for name in (CUDA, TRT) for info in (SMALL, LARGE)]
    monkeypatch.setattr(onnxruntime, "get_ep_devices", lambda: devices)
    monkeypatch.setattr(onnxruntime, "SessionOptions", FakeOptions)
    monkeypatch.setattr(onnxruntime, "InferenceSession", FakeSession)
    for name, value in {"created": [], "build_error": None, "run_error": None, "providers": [CUDA, CPU],
                        "nodes": {CUDA: ["Conv", "Relu", "Conv", "Resize", "Sigmoid"], CPU: ["Clip", "Clip", "Slice"]}}.items():
        monkeypatch.setattr(FakeSession, name, value)
    return calls


def test_a_missing_pack_raises_with_the_install_command():
    with pytest.raises(EpUnavailableError, match="skellytracker-eps install cuda") as caught:
        eps.ensure_registered("cuda")
    assert caught.value.hint == "Run `skellytracker-eps install cuda`."
    for key in ("openvino", "tensorrt"):
        with pytest.raises(EpRequestError):
            eps.ensure_registered(key)
    assert eps.ensure_registered("cpu") == eps.RegisteredEp("cpu", CPU)


def test_registration_is_done_one_time_by_the_library_path(gpu_host):
    first = eps.ensure_registered("cuda")
    assert eps.ensure_registered("cuda") is first and len(gpu_host) == 1
    name, path = gpu_host[0]
    assert name == CUDA and path == str(store.pack_dir("cuda-cu13", "0.2.0") / "plugin.dll")
    assert first == eps.RegisteredEp("cuda", CUDA, "cuda-cu13", "0.2.0", "plugin.dll")
    assert "cuda-cu13/0.2.0" in store.read_verdicts()["last_used"]


def test_a_pack_that_lists_no_device_and_a_second_pack_of_one_group_are_refused(gpu_host, monkeypatch):
    catalog = eps.load_catalog()
    monkeypatch.setattr(onnxruntime, "get_ep_devices", lambda: [fake_device("OtherExecutionProvider", SMALL)])
    with pytest.raises(EpUnavailableError, match="lists no device.*these devices: OtherExecutionProvider on device 10de:2484"):
        eps.ensure_registered("cuda")
    monkeypatch.setattr(onnxruntime, "get_ep_devices", lambda: [fake_device(CUDA, SMALL)])
    eps.ensure_registered("cuda")
    second = dict(catalog.pack("cuda"), id="cuda-other")
    store.write_json(store.pack_dir("cuda-other", "0.2.0") / "pack.json", {"library": "plugin.dll", "files": []})
    with pytest.raises(EpUnavailableError, match="of the same EP"):
        registration.register_pack("cuda", second)


def test_windows_dll_folders_go_first_in_path(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "first")
    for _ in range(2):
        registration.prepare_libraries(tmp_path, {"path_dirs": ["nvidia/cudnn/bin"]}, platform="win32")
    assert registration.os.environ["PATH"].split(registration.os.pathsep) == [str(tmp_path / "nvidia/cudnn/bin"), "first"]


@pytest.mark.parametrize(("key", "options"), [
    ("cuda", {"device_id": "0"}), ("cuda", {"use_tf32": "banana"}), ("cuda", {"enable_cuda_graph": "1"}), ("trt-rtx", {"bogus_key": "1"}),
    ("cpu", {"device_id": "0"}), ("directml", {"device_id": "1"}), ("qnn", None), ("openvino", None), ("tensorrt", None),
])
def test_a_bad_request_raises_before_onnxruntime(monkeypatch, key, options):
    def not_reached(*args, **kwargs):
        raise AssertionError("the request reached the host probe or ONNX Runtime")

    monkeypatch.setattr(session, "probe_host", not_reached)
    monkeypatch.setattr(registration, "ensure_registered", not_reached)
    monkeypatch.setattr(onnxruntime, "InferenceSession", not_reached)
    with pytest.raises(EpRequestError) as caught:
        eps.build_session(b"model", execution_provider=key, ep_options=options)
    assert isinstance(caught.value, ValueError)


def test_cpu_session_from_bytes_and_from_a_path(tmp_path, monkeypatch):
    monkeypatch.setattr(session, "probe_host", lambda: pytest.fail("a cpu session must not read the host"))
    path = tmp_path / "model.onnx"
    path.write_bytes(model_bytes())
    ref = eps.ModelRef("test-model", "ab" * 32, ("fp32",), 2)
    for model in (model_bytes(), path, str(path)):
        built, report = eps.build_session(model, execution_provider="cpu", model_ref=ref)
        (output,) = built.run(None, {"x": np.full((2, 3), -3.0, dtype=np.float32)})
        assert output.tolist() == [[0.0] * 3] * 2 and built.get_providers() == [CPU]
        assert (report.requested_ep, report.used_ep, report.ep_name, report.device_kind) == ("cpu", "cpu", CPU, "cpu")
        assert report.nodes_by_ep == ((CPU, 2),) and report.cpu_nodes == 2 and report.cpu_op_types == ("Add", "Relu")
        assert (report.precision, report.artifact_sha256, report.pack_id, report.device_key) == ("fp32", "ab" * 32, None, None)
        assert report.ort_version == onnxruntime.__version__ and report.build_ns > 0 and report.warmup_ns > 0
        assert pickle.loads(pickle.dumps(report)) == report and hash(report)  # noqa: S301
    with pytest.raises(EpRequestError, match="device key"):
        eps.build_session(model_bytes(), execution_provider="cpu", device_key="gpu:10de:2484:0")


@pytest.mark.parametrize(("physical", "logical", "expected"), [(8, 16, 4), (1, 2, 1), (None, 6, 3), (None, None, 1)])
def test_the_default_cpu_threads_is_half_of_the_physical_cores_at_least_1(monkeypatch, physical, logical, expected):
    monkeypatch.setattr(session, "physical_cores", lambda: physical)
    monkeypatch.setattr(session.os, "cpu_count", lambda: logical)  # used only when the OS gives no physical cores
    assert session.cpu_thread_count() == session.cpu_thread_count(None) == expected
    assert session.cpu_thread_count(5) == 5


def test_a_cpu_session_gets_the_cpu_threads_as_intra_op_threads_and_reports_them(monkeypatch):
    real, seen = onnxruntime.InferenceSession, []

    def recording(model, sess_options=None, **kwargs):
        seen.append((sess_options.intra_op_num_threads, sess_options.inter_op_num_threads))
        return real(model, sess_options=sess_options, **kwargs)

    monkeypatch.setattr(onnxruntime, "InferenceSession", recording)
    monkeypatch.setattr(session, "physical_cores", lambda: 8)
    _, given = eps.build_session(model_bytes(), execution_provider="cpu", cpu_threads=3)
    _, default = eps.build_session(model_bytes(), execution_provider="cpu")
    assert seen == [(3, 1), (4, 1)] and (given.cpu_threads, default.cpu_threads) == (3, 4)


@pytest.mark.parametrize("value", [0, -1, True])
def test_a_cpu_threads_that_is_not_a_positive_integer_raises_before_onnxruntime(monkeypatch, value):
    monkeypatch.setattr(onnxruntime, "InferenceSession", lambda *args, **kwargs: pytest.fail("the request reached ONNX Runtime"))
    for key in ("cpu", "cuda"):  # the same check for each EP
        with pytest.raises(EpRequestError, match="cpu_threads must be a positive integer"):
            eps.build_session(b"model", execution_provider=key, cpu_threads=value)


def test_a_model_that_does_not_load_raises_session_creation_error():
    with pytest.raises(SessionCreationError) as caught:
        eps.build_session(b"not a model", execution_provider="cpu")
    assert (caught.value.report.requested_ep, caught.value.report.used_ep) == ("cpu", None)
    assert pickle.loads(pickle.dumps(caught.value)).report == caught.value.report  # noqa: S301


def test_gpu_session_settings_and_report(gpu_host, tmp_path, caplog):
    with caplog.at_level(logging.WARNING):
        _, report = eps.build_session(b"model", execution_provider="cuda", ep_options={"prefer_nhwc": "1"}, cpu_threads=6)
        eps.build_session(b"model", execution_provider="cuda")
    assert [record.message for record in caplog.records] == ["The EP 'cuda' is in the state installed_unverified: no trial session ran yet."]
    (options, providers, kwargs), _ = FakeSession.created
    assert (options.intra_op_num_threads, options.inter_op_num_threads) == (1, 1)  # attributes, not config entries; `cpu_threads` 6 is ignored
    assert report.cpu_threads is None
    assert options.entries == {"session.record_ep_graph_assignment_info": "1"}
    assert providers is None and kwargs == {"enable_fallback": 0}
    assert options.provider_options == {"prefer_nhwc": "1"} and len(options.devices) == 1
    assert options.devices[0].device.device_id == LARGE.pci_device_id  # no device key: the GPU with the most VRAM
    assert (report.device_key, report.gpu_key, report.device_name, report.gpu_uuid) == ("gpu:10de:2684:0", "0000:02:00.0", "RTX 4090", "GPU-0000:02:00.0")
    assert (report.used_ep, report.pack_id, report.pack_version, report.ep_device_id) == ("cuda", "cuda-cu13", "0.2.0", "0")
    assert report.nodes_by_ep == ((CPU, 3), (CUDA, 5)) and report.cpu_nodes == 3 and report.cpu_op_types == ("Clip", "Slice")
    assert report.ep_options == (("prefer_nhwc", "1"),) and report.device_kind == "gpu"
    _, small = eps.build_session(b"model", execution_provider="cuda", device_key="gpu:10de:2484:0")
    assert small.device_key == "gpu:10de:2484:0" and FakeSession.created[-1][0].devices[0].device.device_id == SMALL.pci_device_id
    with pytest.raises(EpUnavailableError, match="not a GPU"):
        eps.build_session(b"model", execution_provider="cuda", device_key="gpu:10de:ffff:0")


def test_trt_rtx_gets_the_catalog_cache_path_and_the_report_holds_no_path(gpu_host, tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(FakeSession, "providers", [TRT, CPU])
    monkeypatch.setattr(FakeSession, "nodes", {TRT: ["Conv"]})
    monkeypatch.setattr(type(eps.load_catalog()), "ort_untested", lambda self, pack, ort_version=None: True)
    with caplog.at_level(logging.WARNING):
        _, report = eps.build_session(b"model", execution_provider="trt-rtx", ep_options={"enable_cuda_graph": "0"})
    assert "untested-ort" in caplog.text
    options = FakeSession.created[0][0].provider_options
    assert options == {"enable_cuda_graph": "0", "nv_runtime_cache_path": str(tmp_path / "ep-cache" / "trt-rtx" / "0.5.0" / "610.88")}
    assert report.ep_options == (("enable_cuda_graph", "0"),) and str(tmp_path) not in repr(report)
    assert (report.cpu_nodes, report.cpu_op_types, report.used_ep) == (0, (), "trt-rtx")


def test_an_ep_that_does_not_start_raises_and_no_session_is_built_on_the_cpu(gpu_host, monkeypatch):
    monkeypatch.setattr(FakeSession, "build_error", RuntimeError("EP failed to start: Unknown provider option"))
    with pytest.raises(SessionCreationError, match="Unknown provider option") as caught:
        eps.build_session(b"model", execution_provider="cuda")
    assert len(FakeSession.created) == 1 and caught.value.report.used_ep is None and caught.value.report.requested_ep == "cuda"


@pytest.mark.parametrize(("providers", "nodes"), [([CPU], {CPU: ["Conv", "Relu"]}), ([CUDA, CPU], {CPU: ["Conv"]}), ([CUDA, CPU], {})])
def test_a_session_that_is_not_on_the_requested_ep_raises(gpu_host, monkeypatch, providers, nodes):
    monkeypatch.setattr(FakeSession, "providers", providers)
    monkeypatch.setattr(FakeSession, "nodes", nodes)
    with pytest.raises(SessionCreationError, match="did not start on the EP 'cuda'") as caught:
        eps.build_session(b"model", execution_provider="cuda")
    report = caught.value.report
    assert report.requested_ep == "cuda" and report.used_ep == ("cpu" if providers == [CPU] else "cuda")
    assert dict(report.nodes_by_ep).get(CUDA, 0) == 0 and len(FakeSession.created) == 1


@pytest.mark.parametrize("stage", ["build_error", "run_error"])
def test_exhausted_gpu_memory_raises_a_memory_error_and_no_other_ep_is_tried(gpu_host, monkeypatch, stage):
    monkeypatch.setattr(FakeSession, stage, RuntimeError("CUDA failure 2: out of memory ; BFCArena::AllocateRawInternal"))
    with pytest.raises(VRAMExhaustionError) as caught:
        eps.build_session(b"model", execution_provider="cuda")
    assert isinstance(caught.value, MemoryError) and caught.value.report.requested_ep == "cuda"
    assert len(FakeSession.created) == 1


def test_run_session_maps_an_out_of_memory_error_and_passes_each_other_error_through():
    class Failing:
        def __init__(self, error):
            self.error = error

        def run(self, output_names, inputs):
            raise self.error

    with pytest.raises(VRAMExhaustionError, match="during a call") as raised:
        session.run_session(Failing(RuntimeError("CUDA failure 2: out of memory ; BFCArena::AllocateRawInternal")), None, {})
    assert isinstance(raised.value, MemoryError) and raised.value.report is None and raised.value.exit_code == 5
    other = RuntimeError("Invalid rank for input: images")
    with pytest.raises(RuntimeError) as raised:
        session.run_session(Failing(other), None, {})
    assert raised.value is other


def test_judge_of_the_trial_session():
    assert _verify_child.judge({CUDA: {"Conv", "Relu"}}, CUDA, 1e-6, 1e-3) is None
    assert _verify_child.judge({CUDA: {"FusedConv"}}, CUDA, 1e-6, 1e-3) is None
    assert "CPUExecutionProvider" in _verify_child.judge({CPU: {"Conv", "Relu"}}, CUDA, 0.0, 1e-3)  # each node on the CPU
    assert "Conv" in _verify_child.judge({CUDA: {"Transpose"}}, CUDA, 0.0, 1e-3)  # only Transpose nodes
    assert "limit" in _verify_child.judge({CUDA: {"Conv", "Relu"}}, CUDA, 0.5, 1e-3)
    assert "limit" in _verify_child.judge({CUDA: {"Conv", "Relu"}}, CUDA, None, 1e-3)
    assert "127" in verification.child_failure_reason(127) and "did not end" in verification.child_failure_reason(None)


def test_verify_stores_the_result_and_a_new_driver_runs_it_again(gpu_host, monkeypatch):
    jobs = []

    def run_child(job, cancel=None):
        jobs.append(job)
        return {"level": job["level"], "ok": True, "reason": None, "max_abs_diff": 1e-6}

    monkeypatch.setattr(verification, "run_child", run_child)
    (first,) = eps.verify(["cuda"])
    assert (first.ep_key, first.level, first.ok, first.pack_id, first.max_abs_diff) == ("cuda", "L3", True, "cuda-cu13", 1e-6)
    assert jobs[0]["device_key"] == "gpu:10de:2684:0" and jobs[0]["atol"] == 1.5e-2
    assert eps.verify(["cuda"]) == (first,) and len(jobs) == 1  # the stored result
    assert eps.recommend("performance", host(LARGE)).skipped == ()
    eps.verify(["cuda"], force=True)
    assert len(jobs) == 2
    newer = gpu(vram=24 * GIB, bus="0000:02:00.0", device_id=0x2684, driver="620.10")
    monkeypatch.setattr(verification, "probe_host", lambda: host(newer))
    (second,) = eps.verify(["cuda"])
    assert len(jobs) == 3 and second.key != first.key
    assert [verdict.ep_key for verdict in eps.verify()] == ["trt-rtx", "cuda", "cpu"]  # `directml` has no opt-in: skipped


def test_verify_refuses_a_pack_that_is_not_installed(monkeypatch):
    monkeypatch.setattr(verification, "probe_host", lambda: host(SMALL))
    with pytest.raises(EpUnavailableError, match="not installed"):
        eps.verify(["cuda"])
    with pytest.raises(EpRequestError):
        eps.verify(["qnn"])
    with pytest.raises(EpUnavailableError, match="field test.*--field-test"):  # ADR-Z5X7: no opt-in in the store
        eps.verify(["directml"])
    with pytest.raises(ValueError, match="level"):
        eps.verify(["cpu"], level="L4")


def test_verify_of_the_cpu_ep_in_a_real_child_process(monkeypatch):
    monkeypatch.setattr(verification, "probe_host", lambda: host())
    (verdict,) = eps.verify(["cpu"])
    assert (verdict.level, verdict.ok, verdict.reason, verdict.max_abs_diff) == ("L3", True, None, 0.0)


def test_a_child_that_ends_with_no_result_gives_the_reason(monkeypatch):
    monkeypatch.setattr(_verify_child, "main", exit_with_127)
    result = verification.run_child({"level": "L2"})
    assert result["ok"] is False and "127" in result["reason"]


def test_a_child_that_hangs_after_its_result_keeps_the_result(monkeypatch):
    monkeypatch.setattr(_verify_child, "main", child_fakes.verify_result_then_hang)
    result = verification.run_child({"level": "L3"}, grace=0.5)
    assert result == {"level": "L3", "ok": True, "reason": None, "max_abs_diff": 0.0, "exit_reason_code": "hung-at-exit"}
    monkeypatch.setattr(_verify_child, "main", child_fakes.hang)
    result = verification.run_child({"level": "L3"}, timeout=1.0)
    assert result["ok"] is False and result["exit_reason_code"] is None and "did not end in 1 s" in result["reason"]


def exit_with_127(job, connection):
    import os

    os._exit(127)


DML = "DmlExecutionProvider"
RTX_DXGI = dataclasses.replace(SMALL, luid=78921)
INTEL_DXGI = dataclasses.replace(gpu("intel", cc=None, driver="32.0.101.7088", vram=128 * 2**20, bus="0000:00:02.0", device_id=0xA780,
                                     name="UHD 770"), luid=86127)


def dml_device(info, luid: int, adapter: str):
    """A DirectML EP device: `device_id` is the DXGI adapter index, which is not the order of the GPUs."""
    hardware = types.SimpleNamespace(vendor_id=info.pci_vendor_id, device_id=info.pci_device_id, metadata={"LUID": str(luid)})
    return types.SimpleNamespace(ep_name=DML, device=hardware, ep_options={"device_id": adapter})


@pytest.fixture
def dml_host(monkeypatch):
    """ADR-Z5X7: a Windows host with an NVIDIA GPU and an Intel GPU. DirectML lists the NVIDIA GPU two times, under two LUIDs."""
    for module in (session, verification, state, recommendation):  # `check_start()` and `run_devices()` read the host too
        monkeypatch.setattr(module, "probe_host", lambda: host(RTX_DXGI, INTEL_DXGI))
    devices = [dml_device(RTX_DXGI, 126958, "2"), dml_device(RTX_DXGI, 78921, "0"), dml_device(INTEL_DXGI, 86127, "1")]
    monkeypatch.setattr(onnxruntime, "get_ep_devices", lambda: devices)
    monkeypatch.setattr(onnxruntime, "get_available_providers", lambda: [DML, CPU])
    monkeypatch.setattr(onnxruntime, "SessionOptions", FakeOptions)
    monkeypatch.setattr(onnxruntime, "InferenceSession", FakeSession)
    for name, value in {"created": [], "build_error": None, "run_error": None, "providers": [DML, CPU], "nodes": {DML: ["Conv", "Relu"]}}.items():
        monkeypatch.setattr(FakeSession, name, value)


def test_directml_needs_the_field_test_opt_in(dml_host):
    with pytest.raises(EpUnavailableError, match="field test") as caught:
        eps.build_session(b"model", execution_provider="directml")
    assert caught.value.hint == "Run `skellytracker-eps install directml --field-test`." and FakeSession.created == []
    with pytest.raises(EpUnavailableError, match="field test"):
        eps.check_start("directml")


def test_directml_selects_the_ort_device_of_the_requested_gpu(dml_host):
    """The session takes the EP device of the GPU (PCI ids, then LUID), never `device_id`: here index 2 is the NVIDIA GPU again."""
    store.opt_in_field_test("directml")
    assert [d.device_key for d in eps.check_start("directml")] == ["gpu:10de:2484:0", "gpu:8086:a780:0"]  # the most VRAM first
    _, report = eps.build_session(b"model", execution_provider="directml", cpu_threads=6)
    options = FakeSession.created[-1][0]
    assert dict(options.devices[0].device.metadata)["LUID"] == "78921" and options.provider_options == {}
    assert (options.intra_op_num_threads, options.inter_op_num_threads) == (1, 1) and FakeSession.created[-1][1] is None
    assert (report.used_ep, report.pack_id, report.device_key, report.ep_device_id, report.cpu_threads) == (
        "directml", None, "gpu:10de:2484:0", "0", None)
    _, intel = eps.build_session(b"model", execution_provider="directml", device_key="gpu:8086:a780:0")
    assert FakeSession.created[-1][0].devices[0].device.vendor_id == 0x8086 and (intel.device_key, intel.ep_device_id) == ("gpu:8086:a780:0", "1")
    with pytest.raises(EpUnavailableError, match="not a GPU"):
        eps.build_session(b"model", execution_provider="directml", device_key="gpu:10de:ffff:0")


def test_verify_of_directml_runs_on_the_chosen_gpu(dml_host, monkeypatch):
    jobs = []
    monkeypatch.setattr(verification, "run_child", lambda job, cancel=None: jobs.append(job) or {"level": job["level"], "ok": True, "max_abs_diff": 0.0})
    store.opt_in_field_test("directml")
    (verdict,) = eps.verify(["directml"], level="L2", device_key="gpu:8086:a780:0")
    assert verdict.ok and verdict.pack_id is None and jobs[0]["gpu"] == INTEL_DXGI and jobs[0]["pack"] is None
    assert jobs[0]["device_key"] == "gpu:8086:a780:0" and jobs[0]["atol"] == 1.5e-2


def test_the_check_rule_refuses_a_run_and_a_session_and_the_certification_code_passes_it(dml_host, monkeypatch):
    """ADR-ER5X: no reviewed row and no local pass = no run. The rule must never stop the check that lifts it."""
    from skellytracker.core.eps import _verify_child, certification, evidence, gate

    monkeypatch.setattr(evidence, "certified", lambda key, gpu, os_name: False)  # no reviewed row: this test is about the rule
    store.opt_in_field_test("directml")
    catalog = eps.load_catalog()
    for call in (lambda: eps.check_start("directml"), lambda: eps.check_start("directml", device="gpu:8086:a780:0"),
                 lambda: eps.build_session(b"model", execution_provider="directml")):
        with pytest.raises(EpUnavailableError, match="skellytracker-eps certify directml --quick") as refusal:
            call()
        assert (refusal.value.execution_provider, refusal.value.reason_code) == ("directml", "quick-check-needed")
        assert refusal.value.device_key is not None and refusal.value.device_key.startswith("gpu:")
    assert FakeSession.created == []
    assert {check.reason_code for row in eps.status().eps if row.key == "directml" for check in row.checks} == {"quick-check-needed"}
    with gate.certification_run():  # the certification code: the rule is off, also for a nested use
        with gate.certification_run():
            eps.build_session(b"model", execution_provider="directml")
        assert [d.device_key for d in eps.check_start("directml")] == ["gpu:10de:2484:0", "gpu:8086:a780:0"]
    with pytest.raises(EpUnavailableError):
        eps.build_session(b"model", execution_provider="directml")  # the rule is back after the block
    seen = []
    monkeypatch.setattr(_verify_child, "run", lambda job: seen.append(gate.rule_passes(catalog, "directml", INTEL_DXGI, "Windows")) or {})
    _verify_child.main({}, types.SimpleNamespace(send=lambda result: None, close=lambda: None))
    assert seen == [True]  # the child of the probe runs with the rule off
    path = store.store_root() / "quick-checks.json"
    store.write_json(path, {certification.pair_key(catalog, "directml", INTEL_DXGI, "Windows"): {"result": "passed"}})
    assert [d.device_key for d in eps.check_start("directml")] == ["gpu:8086:a780:0"]  # only the GPU with a local pass
    _, report = eps.build_session(b"model", execution_provider="directml")
    assert report.device_key == "gpu:8086:a780:0"  # the default GPU is the first GPU that the rule lets run
    with pytest.raises(EpUnavailableError, match="no quick check passed"):
        eps.check_start("directml", device="gpu:10de:2484:0")
    store.write_json(path, {certification.pair_key(catalog, "directml", INTEL_DXGI, "Windows"): {"result": "failed"}})
    with pytest.raises(EpUnavailableError, match="its last quick check failed"):
        eps.build_session(b"model", execution_provider="directml", device_key="gpu:8086:a780:0")
