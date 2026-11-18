"""Tests of sections 3 and 4 of the certify suite (`tools/certify_eps.py`) with fakes: no GPU, no network."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import certify_eps as ce
import certify_platform as cp
import cv2
import numpy as np
import pytest

from skellytracker.core import eps, pipelines
from skellytracker.core.eps import _download, certification, store
from skellytracker.tests.hw_fakes import GIB, gpu, host

DATA = b"model bytes" * 100
SHA = hashlib.sha256(DATA).hexdigest()


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.setenv(store.STORE_VARIABLE, str(tmp_path / "work" / "eps"))
    monkeypatch.setenv(store.CACHE_VARIABLE, str(tmp_path / "work" / "ep-cache"))
    (tmp_path / "work").mkdir()
    return tmp_path / "work"


RTX = gpu()
INTEL = gpu("intel", cc=None, vram=128 * 2**20, bus="0000:00:02.0", device_id=0xA780, name="UHD 770")
RADEON = gpu("amd", cc=None, vram=16 * GIB, bus="0000:03:00.0", device_id=0x73BF, name="Radeon RX 6800")


def row(key, state, reason_code=None, pack_id=None, devices=()):
    return SimpleNamespace(key=key, state=state, reason_code=reason_code, pack_id=pack_id, devices=devices)


def device(device_key):
    return SimpleNamespace(device_key=device_key)


def fake_eps(monkeypatch, rows, vendor="nvidia", probe_result="pass", gpus=None, verify_ok=None):
    calls = {"install": [], "certify": [], "verify": []}
    gpus = gpus or ((RADEON,) if vendor == "amd" else (RTX,))
    status = SimpleNamespace(eps=rows, host=host(*gpus),
                             performance=SimpleNamespace(hardware_class="amd-windows" if vendor == "amd" else "nvidia-cc80-r580"))
    monkeypatch.setattr(eps, "status", lambda: status)
    monkeypatch.setattr(eps, "plan_install", lambda keys: SimpleNamespace(
        packs=[SimpleNamespace(pack_id=f"{keys[0]}-pack", version="1.0", download_bytes=5)]))

    def install(plan, from_dir=None):
        calls["install"].append(from_dir)
        return SimpleNamespace(ok=("trt-rtx",), failed=())

    def certify(key, out=None):
        calls["certify"].append(out)
        failed = probe_result != "pass"
        report = {"result": probe_result, "reason_code": "probe-l3-failed" if failed else None,
                  "probe": {"ok": not failed, "level": "L3", "max_abs_diff": 0.004, "reason_code": None},
                  "gpu": {"vendor": "nvidia", "name": "Fake RTX", "id": "10de:2484", "driver_version": "610.88"},
                  "versions": {"ort_version": "1.30.0"}}
        return SimpleNamespace(report_json=json.dumps(report))

    monkeypatch.setattr(eps, "install", install)
    monkeypatch.setattr(eps, "certify", certify)
    def verify(keys, level, force, device_key=None):
        calls["verify"].append((keys[0], device_key))
        ok = (verify_ok or {}).get(device_key, True)
        return (SimpleNamespace(ok=ok, level="L3", max_abs_diff=0.0 if ok else 0.5),)

    monkeypatch.setattr(eps, "verify", verify)
    monkeypatch.setattr(store, "read_manifest", lambda pack_id, version: {"wheels": [["a.whl", "ab" * 32]]})
    return calls


NVIDIA_ROWS = [row("trt-rtx", "not_installed", pack_id="trt-rtx-cu13"), row("cuda", "unsupported", "cc"), row("cpu", "builtin")]


def test_section_3_tests_each_usable_ep_and_lists_the_others(work, monkeypatch):
    calls = fake_eps(monkeypatch, NVIDIA_ROWS)
    (work / "options.json").write_text(json.dumps({"wheel_dir": "wheels"}))
    found = ce.section_eps(work)
    results = {c["name"]: (c["result"], c["reason_code"]) for c in found["checks"]}
    assert results == {"trt-rtx": ("pass", None), "cuda": ("not-run", "cc"), "coreml": ("not-run", "os"), "directml": ("not-run", "os"),
                       "cpu": ("pass", None)}  # `status()` gave no `directml` row: an other platform
    assert found["result"] == "pass" and calls["install"] == [Path("wheels")] and calls["certify"] == [work / "certify-trt-rtx.json"]
    trt = found["details"]["eps"]["trt-rtx"]
    assert trt["probe"]["max_abs_diff"] == 0.004 and trt["wheels"] == [{"filename": "a.whl", "sha256": "ab" * 32}]
    assert trt["gpu"]["id"] == "10de:2484" and trt["install"] == "ok"


def test_section_3_fails_on_a_failed_probe(work, monkeypatch):
    fake_eps(monkeypatch, NVIDIA_ROWS, probe_result="fail")
    found = ce.section_eps(work)
    assert (found["result"], found["reason_code"]) == ("fail", "probe-l3-failed")


def test_section_3_on_an_amd_host_records_the_class_and_amd_eps_not_built(work, monkeypatch):
    fake_eps(monkeypatch, [row("trt-rtx", "unsupported", "vendor"), row("cuda", "unsupported", "vendor"), row("cpu", "builtin")],
             vendor="amd")
    found = ce.section_eps(work)
    assert found["details"]["hardware_class"] == "amd-windows" and found["result"] == "pass"
    assert {"name": "amd-eps", "result": "not-run", "reason_code": "not-built", "eps": ["migraphx", "windows-ml-amd"]} in found["checks"]


DML_ROWS = [row("trt-rtx", "unsupported", "vendor"), row("cuda", "unsupported", "vendor"),
            row("directml", "builtin", devices=(device("gpu:10de:2484:0"), device("gpu:8086:a780:0"))), row("cpu", "builtin")]


def test_section_3_opts_in_and_records_directml_on_each_gpu_as_record_only_off_amd(work, monkeypatch):
    """ADR-Z5X7 and ADR-Y14H item 11: the probe runs on each GPU; on a GPU that is not AMD it does not count, also when it fails."""
    calls = fake_eps(monkeypatch, DML_ROWS, gpus=(RTX, INTEL), verify_ok={"gpu:8086:a780:0": False})
    found = ce.section_eps(work)
    assert set(store.field_test_opt_ins()) == {"directml"} and str(store.store_root()).startswith(str(work))
    results = {c["name"]: c["result"] for c in found["checks"]}
    assert results["directml@gpu:10de:2484:0"] == results["directml@gpu:8086:a780:0"] == "record-only" and found["result"] == "pass"
    assert ("directml", "gpu:8086:a780:0") in calls["verify"] and found["details"]["eps"]["directml@gpu:8086:a780:0"]["result"] == "fail"
    assert found["details"]["pipeline_targets"] == [{"key": "directml", "device_key": "gpu:10de:2484:0", "counts": False}]


def test_section_3_counts_directml_on_an_amd_gpu(work, monkeypatch):
    rows = [*DML_ROWS[:2], row("directml", "builtin", devices=(device("gpu:1002:73bf:0"),)), row("cpu", "builtin")]
    fake_eps(monkeypatch, rows, vendor="amd", verify_ok={"gpu:1002:73bf:0": False})
    found = ce.section_eps(work)
    assert {c["name"]: c["result"] for c in found["checks"]}["directml@gpu:1002:73bf:0"] == "fail" and found["result"] == "fail"
    fake_eps(monkeypatch, rows, vendor="amd")
    found = ce.section_eps(work)
    assert found["result"] == "pass" and found["details"]["pipeline_targets"] == [{"key": "directml", "device_key": "gpu:1002:73bf:0", "counts": True}]


def test_sections_3_and_4_refuse_to_run_without_the_isolated_store(tmp_path, monkeypatch):
    monkeypatch.delenv(store.STORE_VARIABLE, raising=False)
    assert ce.section_eps(tmp_path)["reason_code"] == ce.section_pipeline(tmp_path)["reason_code"] == "no-isolated-store"


def test_section_4_without_the_model_files_is_not_run(work, monkeypatch):
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: SimpleNamespace(available=False))
    found = ce.section_pipeline(work)
    assert (found["result"], found["reason_code"], found["details"]["models"]) == ("not-run", "models-missing", [])


def test_section_4_reads_the_section_3_result_and_runs_each_passed_gpu_ep(work, monkeypatch):
    (work / "section-3.json").write_text(json.dumps({"details": {"pipeline_targets": [
        {"key": "trt-rtx", "device_key": None, "counts": True}, {"key": "directml", "device_key": "gpu:8086:a780:0", "counts": False}]}}))
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: SimpleNamespace(available=True))
    image = cv2.imencode(".jpg", np.zeros((8, 8, 3), np.uint8))[1].tobytes()

    def fetch(url, sha256, part, **kwargs):
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_bytes(image)
        return part

    timed, compared = [], []
    monkeypatch.setattr(_download, "fetch", fetch)
    monkeypatch.setattr(ce, "time_run", lambda pipeline, key, cameras, frame, device: timed.append((key, cameras, device)) or {"median_ms": 1.0})
    monkeypatch.setattr(certification, "_wide_run", lambda key, settings, progress, device: compared.append((key, device)) or {
        "ran": True, "ok": key != "directml", "reason_code": "keypoints-differ" if key == "directml" else None, "box_iou_min": 0.99,
        "keypoint_box_fraction_max": 0.005, "keypoint_box_fraction_median": 0.001, "keypoint_box_fraction_p99": 0.004, "points_compared": 100})
    found = ce.section_pipeline(work)
    intel = "gpu:8086:a780:0"
    assert timed == [("cpu", 1, None), ("trt-rtx", 1, None), ("trt-rtx", 3, None), ("trt-rtx", 6, None),
                     ("directml", 1, intel), ("directml", 3, intel), ("directml", 6, intel)]
    assert compared == [("trt-rtx", None), ("directml", intel)]
    agreement = next(c for c in found["checks"] if c["name"] == "agreement-trt-rtx")
    assert found["result"] == "pass" and agreement["keypoint_box_fraction_p99"] == 0.004
    dml = next(c for c in found["checks"] if c["name"] == f"agreement-directml@{intel}")
    assert (dml["result"], dml["reason_code"]) == ("record-only", "keypoints-differ")  # a failure off AMD does not fail the section
    assert str(store.cache_root()).startswith(str(work))  # the test image is cached in the work folder


def fake_fetch(monkeypatch, data: bytes):
    def fetch(url, sha256, part, **kwargs):
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_bytes(data)
        return part

    monkeypatch.setattr(_download, "fetch", fetch)


def test_a_downloaded_model_with_the_right_hash_is_placed_and_removed_at_the_end(work, tmp_path, monkeypatch):
    fake_fetch(monkeypatch, DATA)
    root = tmp_path / "zoo"
    found = ce.fetch_models([{"path": "detectors/m.onnx", "url": "https://example.invalid/m.onnx", "sha256": SHA, "bytes": len(DATA)}],
                            root, work)
    assert found[0]["state"] == "downloaded" and (root / "detectors" / "m.onnx").read_bytes() == DATA
    cp.remove_listed(work)
    assert not (root / "detectors" / "m.onnx").exists()


def test_a_downloaded_model_with_a_bad_hash_is_refused_and_deleted(work, tmp_path, monkeypatch):
    fake_fetch(monkeypatch, b"other bytes")
    root = tmp_path / "zoo"
    found = ce.fetch_models([{"path": "m.onnx", "url": "https://example.invalid/m.onnx", "sha256": SHA, "bytes": 1}], root, work)
    assert (found[0]["state"], found[0]["reason_code"]) == ("failed", "hash-mismatch")
    assert not (root / "m.onnx").exists() and not list((work / "partial").iterdir())


def test_a_model_already_present_is_kept_and_a_wrong_file_is_not_touched(work, tmp_path, monkeypatch):
    monkeypatch.setattr(_download, "fetch", lambda *args, **kwargs: pytest.fail("no download for a present file"))
    root = tmp_path / "zoo"
    root.mkdir()
    (root / "good.onnx").write_bytes(DATA)
    (root / "wrong.onnx").write_bytes(b"mine")
    models = [{"path": name, "url": "https://example.invalid/x", "sha256": SHA, "bytes": 1} for name in ("good.onnx", "wrong.onnx")]
    models.append({"path": "../escape.onnx", "url": "https://example.invalid/x", "sha256": SHA, "bytes": 1})
    found = ce.fetch_models(models, root, work)
    assert [f["state"] for f in found] == ["present", "wrong-file", "refused"]
    cp.remove_listed(work)
    assert (root / "good.onnx").read_bytes() == DATA and (root / "wrong.onnx").read_bytes() == b"mine"


def test_the_frame_hands_the_options_the_store_and_each_result_to_the_next_section(tmp_path):
    reader = ("import json, os, sys; w = sys.argv[1]; s1 = json.load(open(w + '/section-1.json')); o = json.load(open(w + '/options.json'));"
              " print(json.dumps({'result': 'record-only', 'details': {'s1': s1['result'], 'wheel': o['wheel_dir'],"
              " 'store': os.environ['SKELLYTRACKER_EP_STORE'].startswith(w), 'cache': os.environ['SKELLYTRACKER_EP_CACHE'].startswith(w)}}))")
    out, work = tmp_path / "r.md", tmp_path / "w"
    fakes = tuple(cp.Section(n, f"fake {n}", 1, 60, cp.not_built) for n in (1, 2))
    commands = {1: [sys.executable, "-c", "print('{\"result\": \"pass\"}')"], 2: [sys.executable, "-c", reader, str(work)]}
    cp.run_suite(fakes, {1, 2}, out, yes=True, work=work, interactive=False, options={"wheel_dir": "wheels"},
                 command=lambda section, _work: commands[section.number])
    second = cp.report_data(out.read_text(encoding="utf-8"))["sections"][1]
    assert second["details"] == {"s1": "pass", "wheel": "wheels", "store": True, "cache": True} and not work.exists()
    env = cp.child_env(work)
    assert set(env) >= {store.STORE_VARIABLE, store.CACHE_VARIABLE, "SKELLYTRACKER_MODEL_CACHE"}
    assert env["SKELLYTRACKER_MODEL_CACHE"] == str(work / "model-cache") and env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_the_consent_lists_no_wheel_with_a_wheel_dir_and_survives_a_failing_list(tmp_path):
    assert ce.eps_downloads({"wheel_dir": "wheels"}) == ()

    def broken(options):
        raise OSError

    text = cp.plan_text((cp.Section(3, "s", 1, 60, cp.not_built, broken),), {3}, tmp_path / "r.md")
    assert "section 3 (size unknown)" in text
