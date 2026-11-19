"""The certification entry point `run_jpeg_certification` (`core/decode/certification.py`).

The tests with no marker run with no EP and need no GPU. A test with the marker `gpu` runs on each
installed NVIDIA EP pack. `NAMES` is the frozen list of the check names: a rename must break a test,
because a certify suite reads the names. A new check adds its name at the end of its group.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import socket
import subprocess
import sys

import pytest

from skellytracker.core.decode import certification
from skellytracker.core.decode.certification import REASONS, RESULTS, run_jpeg_certification

NAMES = [
    "cpu_decode.baseline_420", "cpu_decode.baseline_422", "cpu_decode.baseline_444", "cpu_decode.progressive", "cpu_decode.grayscale",
    "cpu_decode.no_dht",
    "cpu_decode.rotation_0", "cpu_decode.rotation_90", "cpu_decode.rotation_180", "cpu_decode.rotation_270",
    "cpu_decode.size_320x240", "cpu_decode.size_640x480", "cpu_decode.size_1280x720", "cpu_decode.size_1920x1080", "cpu_decode.size_720x1280",
    "cpu_decode.no_soi_refused", "cpu_decode.truncated",
    "gpu_decode.baseline_420", "gpu_decode.baseline_422", "gpu_decode.baseline_444", "gpu_decode.progressive", "gpu_decode.grayscale",
    "gpu_decode.rotation_0", "gpu_decode.rotation_90", "gpu_decode.rotation_180", "gpu_decode.rotation_270",
    "gpu_decode.size_320x240", "gpu_decode.size_640x480", "gpu_decode.size_1280x720", "gpu_decode.size_1920x1080", "gpu_decode.size_720x1280",
    "gpu_decode.batch_1", "gpu_decode.batch_3", "gpu_decode.batch_6",
    "gpu_decode.no_dht_refused", "gpu_decode.no_soi_refused", "gpu_decode.truncated_420", "gpu_decode.truncated_422",
    "preprocess_graph.yolox_person", "preprocess_graph.yolox_person_mixed_sizes",
    "preprocess_graph.rtmw_wholebody133", "preprocess_graph.rtmw_wholebody133_mixed_sizes",
    "preprocess_graph_ep.yolox_person", "preprocess_graph_ep.yolox_person_mixed_sizes",
    "preprocess_graph_ep.rtmw_wholebody133", "preprocess_graph_ep.rtmw_wholebody133_mixed_sizes",
    "preprocess_graph_ep.node_placement", "preprocess_graph_ep.device_handover",
    "pipeline.cpu_preprocess_no_frame_warning", "pipeline.cpu_ep_auto_no_frame_warning", "pipeline.gpu_auto_vs_cpu", "pipeline.repeat_equal",
]
RECORD_ONLY = {"cpu_decode.truncated", "gpu_decode.truncated_420", "gpu_decode.truncated_422", "preprocess_graph_ep.node_placement",
               "pipeline.gpu_auto_vs_cpu"}
GPU_CHECKS = {name for name in NAMES if name.startswith(("gpu_decode.", "preprocess_graph_ep."))} | {"pipeline.gpu_auto_vs_cpu"}
PIPELINE_CHECKS = {name for name in NAMES if name.startswith("pipeline.")} - GPU_CHECKS


@pytest.fixture(scope="module")
def run_without_ep() -> tuple[dict, list[str]]:
    called: list[str] = []
    return run_jpeg_certification(progress=called.append), called


def test_the_result_is_json_with_the_schema_keys_and_the_frozen_names(run_without_ep: tuple[dict, list[str]]) -> None:
    result, called = run_without_ep
    json.dumps(result, allow_nan=False)
    assert set(result) == {"schema", "ep_key", "facts", "checks"}
    assert result["schema"] == 1 and result["ep_key"] is None
    assert [check["name"] for check in result["checks"]] == NAMES == called
    for check in result["checks"]:
        assert set(check) == {"name", "result", "reason", "numbers", "warnings", "detail"}
        assert check["result"] in RESULTS and check["reason"] in REASONS, check
        assert all(isinstance(value, int | float) and not isinstance(value, bool) for value in check["numbers"].values()), check
        assert all(set(warning) == {"code", "reason"} for warning in check["warnings"]), check
        assert isinstance(check["detail"], str)


def test_with_no_ep_the_cpu_checks_pass_and_the_gpu_checks_do_not_run(run_without_ep: tuple[dict, list[str]]) -> None:
    by_name = {check["name"]: check for check in run_without_ep[0]["checks"]}
    for name, check in by_name.items():
        if name in GPU_CHECKS:
            assert (check["result"], check["reason"]) == ("not-run", "ep_not_present"), check
        elif name in PIPELINE_CHECKS:  # the ONNX files of the built-in pipeline are not in git
            assert check["result"] == "pass" or (check["result"], check["reason"]) == ("not-run", "models_not_available"), check
        elif name in RECORD_ONLY:
            assert (check["result"], check["reason"]) == ("record-only", "recorded"), check
        else:
            assert (check["result"], check["reason"]) == ("pass", "ok"), check


def test_the_result_holds_no_home_folder_no_user_name_and_no_host_name(run_without_ep: tuple[dict, list[str]]) -> None:
    text = json.dumps(run_without_ep[0])
    home = os.path.expanduser("~")
    for form in {home, home.replace("\\", "/"), json.dumps(home)[1:-1]}:
        assert form.lower() not in text.lower()
    for word in (getpass.getuser(), socket.gethostname()):
        assert not re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text, re.IGNORECASE), word


def test_a_check_that_raises_fails_with_no_path_and_the_next_checks_run(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise OSError(f"cannot read {os.path.join(os.path.expanduser('~'), 'frame.jpg')} or C:\\data\\frame.jpg")

    monkeypatch.setattr(certification, "PIPELINE_KEY", "no-such-pipeline@skellytracker")  # fast: the pipeline checks raise at once
    monkeypatch.setattr("skellytracker.core.decode.cpu.decode_jpeg", broken)
    by_name = {check["name"]: check for check in run_jpeg_certification()["checks"]}
    failed = by_name["cpu_decode.baseline_420"]
    assert (failed["result"], failed["reason"]) == ("fail", "raised")
    assert failed["detail"] == "OSError: cannot read <path> or <path>"
    assert by_name["preprocess_graph.yolox_person"]["result"] == "pass"


def test_the_reasons_are_a_closed_set() -> None:
    assert REASONS == ("ok", "over_limit", "mismatch", "refused", "not_refused", "warning_given", "decoder_not_opened", "ep_not_present",
                       "no_gpu_decode_on_ep", "component_not_installed", "sidecar_not_available", "models_not_available", "raised", "recorded")


def test_an_ep_with_no_gpu_frame_path_runs_no_gpu_check_and_has_no_gpu_decode_by_design(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(certification, "PIPELINE_KEY", "no-such-pipeline@skellytracker")  # fast: no pipeline check is a GPU check here
    by_name = {check["name"]: check for check in run_jpeg_certification("cpu")["checks"]}
    for name in GPU_CHECKS:
        reason = "no_gpu_decode_on_ep" if name.startswith("gpu_decode.") else "ep_not_present"
        assert (by_name[name]["result"], by_name[name]["reason"]) == ("not-run", reason), by_name[name]


def test_the_import_loads_no_onnxruntime_no_onnx_and_no_nvidia_module() -> None:
    code = ("import sys; import skellytracker.core.decode.certification; "
            "print(sorted(m for m in ('onnxruntime', 'onnx', 'nvidia') if m in sys.modules))")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=True)  # noqa: S603
    assert done.stdout.strip() == "[]"


@pytest.mark.gpu
@pytest.mark.parametrize("ep_key", ["cuda", "trt-rtx"])
def test_on_each_nvidia_ep_no_check_fails(ep_key: str) -> None:
    result = run_jpeg_certification(ep_key)
    if all(check["reason"] == "ep_not_present" for check in result["checks"] if check["name"] in GPU_CHECKS):
        pytest.skip(f"{ep_key} is not installed")
    assert [check for check in result["checks"] if check["result"] == "fail"] == []
