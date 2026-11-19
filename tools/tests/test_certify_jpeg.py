"""Tests of section 5 of the certify suite (`tools/certify_jpeg.py`) with a fake entry point: no GPU, no JPEG branch."""

import json
import sys
from pathlib import Path
from types import ModuleType

import certify_jpeg as cj
import certify_platform as cp
import pytest


def item(name, result, reason, **numbers):
    return {"name": name, "result": result, "reason": reason, "numbers": numbers, "warnings": [], "detail": f"text of {name}"}


def fake_module(monkeypatch, checks_of, gpu_frame_eps=("cuda", "trt-rtx"), facts=None):
    """A fake `certification` module: `checks_of(ep_key)` gives the checks of one call. It records each `ep_key`."""
    module, calls = ModuleType(cj.ENTRY), []

    def run_jpeg_certification(ep_key=None, *, progress=None):
        calls.append(ep_key)
        return {"schema": 1, "ep_key": ep_key, "facts": facts or {"versions": {"python": "3.13"}}, "checks": checks_of(ep_key)}

    module.run_jpeg_certification = run_jpeg_certification
    if gpu_frame_eps is not None:
        module.GPU_FRAME_EPS = gpu_frame_eps
    monkeypatch.setitem(sys.modules, cj.ENTRY, module)
    return calls


def section_3(work: Path, *targets) -> None:
    keys = [{"key": key, "device_key": device, "counts": True} for key, device in targets]
    (work / "section-3.json").write_text(json.dumps({"details": {"pipeline_targets": keys}}), encoding="utf-8")


def test_the_section_is_not_run_when_the_entry_point_is_not_in_the_checkout(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, cj.ENTRY, None)  # the import then raises ModuleNotFoundError
    found = cj.section_jpeg(tmp_path)
    assert (found["result"], found["reason_code"], found["checks"]) == ("not-run", "not-in-this-checkout", [])


def test_the_section_runs_after_section_4_so_the_model_files_are_still_there():
    numbers = [section.number for section in cp.SECTIONS]
    assert numbers == sorted(numbers) and cp.SECTIONS[numbers.index(5)].run is cp.section_jpeg


def test_a_mixed_result_passes_and_each_check_carries_its_ep(tmp_path, monkeypatch):
    section_3(tmp_path, ("cuda", None), ("directml", "gpu0"), ("trt-rtx", None))
    calls = fake_module(monkeypatch, lambda ep: [item("cpu_decode.baseline_420", "pass", "ok", max_abs_diff=1),
                                                 item("cpu_decode.truncated", "record-only", "recorded"),
                                                 item("gpu_decode.batch_3", "not-run" if ep is None else "pass",
                                                      "ep_not_present" if ep is None else "ok")])
    found = cj.section_jpeg(tmp_path)
    assert calls == [None, "cuda", "trt-rtx"]  # `directml` is not in GPU_FRAME_EPS
    assert found["result"] == "pass" and found["reason_code"] is None
    assert [c["name"] for c in found["checks"]][:3] == ["cpu:cpu_decode.baseline_420", "cpu:cpu_decode.truncated", "cpu:gpu_decode.batch_3"]
    first = found["checks"][0]
    assert first == {"name": "cpu:cpu_decode.baseline_420", "result": "pass", "reason_code": "ok", "numbers": {"max_abs_diff": 1},
                     "warnings": []}  # no `detail` text
    assert found["details"]["runs"]["cuda"]["counts"] == {"pass": 2, "record-only": 1}
    assert found["summary"].startswith("cpu: 1 not-run, 1 pass, 1 record-only; cuda: 2 pass")


def test_a_failing_check_or_a_call_that_raises_fails_the_section(tmp_path, monkeypatch):
    section_3(tmp_path, ("cuda", None))

    def checks_of(ep):
        if ep == "cuda":
            raise RuntimeError("no device")
        return [item("cpu_decode.size_640x480", "fail", "over_limit", mean_abs_diff=4.2), item("cpu_decode.no_dht", "pass", "ok")]

    fake_module(monkeypatch, checks_of)
    found = cj.section_jpeg(tmp_path)
    assert (found["result"], found["reason_code"]) == ("fail", "over_limit")
    assert {"name": "cuda:run", "result": "fail", "reason_code": "RuntimeError"} in found["checks"]


def test_everything_not_run_is_a_not_run_section_and_with_no_list_each_passed_ep_is_asked(tmp_path, monkeypatch):
    section_3(tmp_path, ("directml", "gpu0"), ("directml", "gpu1"), ("migraphx", None))
    calls = fake_module(monkeypatch, lambda ep: [item("pipeline.repeat_equal", "not-run", "models_not_available")], gpu_frame_eps=None)
    found = cj.section_jpeg(tmp_path)
    assert calls == [None, "directml", "migraphx"]
    assert (found["result"], found["reason_code"]) == ("not-run", None)


def test_the_suite_scrub_runs_over_the_result(tmp_path, monkeypatch):
    home = str(Path.home())
    fake_module(monkeypatch, lambda ep: [item("cpu_decode.grayscale", "pass", "ok")],
                facts={"host": {"cpu_name": f"cpu in {home}", "note": f"{Path.home().name} was here"}})
    text = json.dumps(cj.section_jpeg(tmp_path))
    assert home.replace("\\", "\\\\") not in text and Path.home().name not in text
    assert "<path>" in text and "<private>" in text


def test_a_missing_dependency_of_the_module_is_not_hidden(tmp_path, monkeypatch):
    def broken(name):
        raise ModuleNotFoundError("No module named 'cv2'", name="cv2")

    monkeypatch.setattr(cj.importlib, "import_module", broken)
    with pytest.raises(ModuleNotFoundError):
        cj.section_jpeg(tmp_path)
