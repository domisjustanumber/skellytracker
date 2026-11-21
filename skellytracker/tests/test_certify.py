"""Tests of `skellytracker.certify()` and `skellytracker.certify_plan()`: the format `skellycertify.report/1.4.0`.

They use the fakes of `hw_fakes.py` and need no GPU. The cancel tests start real `spawn` children with the targets of
`child_fakes.py`.
"""

import dataclasses
import json
import re
import sys
import threading
import time
import types

import numpy as np
import pytest

import skellytracker
from skellytracker import certification as package_certification
from skellytracker.core.eps import _download, certification, cli, evidence, installer, recommendation, state, store, verification
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.records import Verdict
from skellytracker.core.system import host as host_module
from skellytracker.tests import child_fakes, hw_fakes
from skellytracker.tests.hw_fakes import gpu, host
from skellytracker.tests.test_eps_store import ep_store  # noqa: F401 - fixture

COMMIT = "0123456789abcdef0123456789abcdef01234567"
UUID4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
MODELS = [{"key": "rtmw", "version": "1", "size": "m", "precision": "fp16", "execution_provider": "trt-rtx", "device": None}]
REAL_SESSION_RUN = certification.session_run

# The field rules of sections 3, 5.2 and 6 of the contract, as a test can check them.
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$")
REASON = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
PRIVATE = [re.compile(pattern) for pattern in (
    r"(?:\b[A-Za-z]:[\\/]|\\\\[^\\\s]|/(?:home|Users|root)/|~[\\/])",
    r"\b(?:[0-9a-fA-F]{4}:)?[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]\b",
    r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}",
    r"Traceback \(most recent call last\)")]
BAD_KEYS = {"hostname", "host_name", "node", "user", "username", "user_name", "email", "serial", "serial_number", "uuid", "mac",
            "mac_address", "bus_id", "pci_bus_id", "luid", "ip", "ip_address"}
MEDIA = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".mp4", ".avi", ".mkv", ".mov", ".webm", ".wav", ".mp3", ".flac")


def problems_of(report: dict) -> list[str]:
    """Each rule of the contract that the module report breaks."""
    found = [f"no field {name}" for name in ("schema", "package", "kind", "created_utc", "host", "checks", "evidence")
             if name not in report]
    found += [] if report.get("schema") == "skellycertify.report/1.4.0" else ["schema"]
    found += [] if UUID4.match(str(report.get("id"))) else ["id"]
    found += [] if report.get("kind") in ("quick", "full") else ["kind"]
    found += [] if re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", report.get("created_utc", "")) else ["created_utc"]
    package = report.get("package", {})
    found += [f"package.{name}" for name in ("name", "version", "commit", "tree_modified") if name not in package]
    found += [] if package.get("commit") is None or re.fullmatch(r"[0-9a-f]{40}", package["commit"]) else ["package.commit"]
    seen = set()
    for check in [*report.get("checks", []), *report.get("cleanup", [])]:
        found += [] if NAME.match(check.get("name", "")) else [f"check name {check.get('name')!r}"]
        found += [] if check.get("result") in ("pass", "fail", "not-run", "record-only") else [f"result of {check.get('name')}"]
        if check.get("result") in ("fail", "not-run") and check.get("reason") is None:
            found.append(f"no reason for {check['name']}")
        if check.get("reason") is not None and not REASON.match(check["reason"]):
            found.append(f"reason {check['reason']!r}")
        for value in check.get("numbers", {}).values():
            if not (value is None or isinstance(value, bool | int | float) or (isinstance(value, str) and REASON.match(value))):
                found.append(f"number {value!r} of {check['name']}")
    for check in report.get("checks", []):
        found += [f"duplicate {check['name']}"] if check["name"] in seen else []
        seen.add(check["name"])
        key = check["name"].split("@")[0].split(":")[0]  # a check of the suite of `tools/certify_platform.py` has no module
        # the name of the summary item of the EP; `mediapipe:smoke` is not an EP
        expected = {"suite": None, "mediapipe": "MediaPipe"}[key] if key in ("suite", "mediapipe") else package_certification.SUMMARY_NAMES[key]
        found += [] if check.get("module") == expected else [f"module of {check['name']}"]
    evidence = report.get("evidence", {})
    found += [] if evidence.get("valid") is (not evidence.get("reasons")) else ["evidence.valid"]
    found += [f"evidence reason {code!r}" for code in evidence.get("reasons", []) if not REASON.match(code)]

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                found.extend([f"key {key}"] if key in BAD_KEYS else [])
                walk(key)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            found.extend(f"string {value[:40]!r}" for pattern in PRIVATE if pattern.search(value))
            found.extend([f"long string {value[:40]!r}"] if len(value) > 2000 else [])
            found.extend([f"media name {value!r}"] if value.lower().endswith(MEDIA) else [])

    walk(report)
    return found


@pytest.fixture
def quick_host(monkeypatch, ep_store, tmp_path):  # noqa: F811
    """A Windows host with an RTX 3070 and the `trt-rtx` pack, no evidence row of an EP, a clean commit and a fake pipeline.

    It has a reviewed row of MediaPipe, so a run of the default selection has no `mediapipe:smoke` (see `mediapipe_due()`).
    """
    fake_host = dataclasses.replace(host(gpu()), os_label="Windows 11 Home 26H2")
    for module in (state, recommendation, installer, verification, host_module):
        monkeypatch.setattr(module, "probe_host", lambda: fake_host)
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())
    monkeypatch.setattr(evidence, "mediapipe_reviewed", lambda version, python, os_name_key: True)
    monkeypatch.setenv(store.CACHE_VARIABLE, str(tmp_path / "cache"))
    monkeypatch.setattr(package_certification, "_commit", lambda: (COMMIT, False))
    monkeypatch.setattr(package_certification, "_pipeline", lambda catalog, pipeline: ({}, "yolox-rtmw-wholebody@skellytracker", None))
    hw_fakes.fake_pack("trt-rtx")
    fake_jpeg(monkeypatch)
    fake_sessions(monkeypatch)
    return ep_store


def frame(people: int = 1, shift: float = 0.0, box: float = 0.0, nan: bool = False) -> dict:
    """One frame of `session_frames()`: one person or none, a keypoint moved by `shift` px, the box moved by `box` px."""
    boxes = types.SimpleNamespace(xyxy=np.array([[10.0 + box, 10.0, 110.0 + box, 210.0]]), present=np.array([people == 1]))
    points = np.array([[[50.0 + shift, 60.0], [70.0, 80.0], [np.nan if nan else 1.0, 1.0]]])
    return {"boxes": boxes, "wholebody": types.SimpleNamespace(xy=points, score=np.array([[0.9, 0.8, 0.1]]), present=np.array([people == 1]))}


def session_found(key: str, modes: tuple, **changes) -> dict:
    """The result of a child of `session_run()`: three same frames for each mode. `changes` changes each mode."""
    return {mode: {"frames": [frame()] * 3, "ms": 19.0 if key == "cpu" else 6.0, "warnings": [], "models": MODELS, **changes} for mode in modes}


def fake_sessions(monkeypatch, **changes) -> list:
    """Fake `session_run()`. For the child `cpu`, `video` or `live`, `changes` gives the changes of each mode as a dict, or a
    callable with the arguments of `session_run()` that gives `(result, problem, exit_code)`. It gives the calls."""
    calls = []

    def session_run(key, settings, modes, device_key=None, cancel=None, progress=None, timeout=None):
        calls.append((key, modes, device_key))
        change = changes.get("cpu" if key == "cpu" else modes[0], {})
        if callable(change):
            return change(key, settings, modes, device_key, cancel=cancel, progress=progress, timeout=timeout)
        for mode in modes:
            if progress is not None:
                progress(mode)
        return session_found(key, modes, **change), None, 0

    monkeypatch.setattr(certification, "session_run", session_run)
    return calls


def fake_jpeg(monkeypatch, found=None, problem=None, exit_code=0, **changes):
    """Fake the child of the two JPEG checks. `changes` gives the result and the reason of a check by its name."""
    checks = [{"name": name, "result": "pass", "reason": "ok", "numbers": {"max_abs_diff": 0.0, "shape": [1, 2]}, "warnings": [],
               "detail": "C:\\secretdir\\x", **dict(zip(("result", "reason"), changes.get(name.replace("-", "_"), ()), strict=False))}
              for name in package_certification.JPEG_CHECKS]
    monkeypatch.setattr(package_certification, "_jpeg_spawn",
                        lambda key, device_key, cancel, timeout=None: ({"checks": checks} if found is None else found, problem, exit_code))


def fake_probe(monkeypatch, ok=True, code=None):
    calls = []

    def verify(keys, device_key=None, force=False, cancel=None, timeout=None):
        calls.append((keys, device_key))
        return (Verdict(keys[0], "L3", ok, "k", reason=None if ok else "the folder secretdir failed", max_abs_diff=0.001,
                        reason_code=code, exit_code=3 if code == "crashed" else None),)

    monkeypatch.setattr(verification, "verify", verify)
    return calls


def reviewed(ep: str, gpu_id: str = "10de:2484", **changes) -> dict:
    """A reviewed pass of `ep_evidence.yaml` for the version set of this release."""
    return {"ep": ep, "os": "Windows", "gpu": gpu_id, "set": evidence.set_hash(load_catalog()), "source": "maintainer",
            "result": "pass", "os_label": "Windows 11 Home 26H2", **changes}


BAD_VIDEO = {"frames": [frame(box=50.0)] * 3}  # each frame gives `box-differs`
CPU_ROWS = {"cpu:video": ("pass", None), "cpu:live": ("pass", None)}


def local_results() -> dict:
    """The local result of each pair in `quick-checks.json` of the EP store."""
    return store.read_json(store.store_root() / "quick-checks.json") or {}


def results(report: dict, jpeg: bool = False) -> dict:
    """The result and the reason of each check, without the JPEG checks unless `jpeg`."""
    return {check["name"]: (check["result"], check["reason"]) for check in report["checks"] if jpeg or ":jpeg-" not in check["name"]}


def test_a_bad_level_and_a_string_of_eps_raise_value_error(quick_host):
    for call in (skellytracker.certify, skellytracker.certify_plan):
        with pytest.raises(ValueError, match="quick"):
            call("medium")
    with pytest.raises(ValueError, match="list"):
        skellytracker.certify("quick", execution_providers="cuda")
    with pytest.raises(ValueError):  # `EpRequestError` for an unknown key
        skellytracker.certify_plan("quick", execution_providers=["nope"])


def test_a_quick_pass_gives_a_valid_report_and_records_the_local_pass(quick_host, monkeypatch):
    calls = fake_probe(monkeypatch)
    report = skellytracker.certify("quick")  # the default: the usable pack EP `trt-rtx` and `directml`, with no reviewed row
    assert problems_of(report) == []
    assert results(report) == {**CPU_ROWS, **{f"{ep}@10de-2484-0{part}": ("pass", None) for ep in ("trt-rtx", "directml")
                                              for part in (":probe", ":video", ":live", "")}}
    assert calls == [(["trt-rtx"], "gpu:10de:2484:0"), (["directml"], "gpu:10de:2484:0")]
    assert report["details"]["eps"]["trt-rtx@10de-2484-0"]["device"] == "gpu:10de:2484:0"
    assert report["details"]["eps"]["trt-rtx@10de-2484-0"]["pack_version"] == load_catalog().pack("trt-rtx")["version"]
    facts = store.installed_pack_facts(load_catalog(), "trt-rtx")  # the fake pack: a manifest with no wheel
    assert facts == {"installed_pack_version": load_catalog().pack("trt-rtx")["version"], "wheels_match_lock": False}
    assert facts.items() <= report["details"]["eps"]["trt-rtx@10de-2484-0"].items()
    assert "wheels_match_lock" not in report["details"]["eps"]["directml@10de-2484-0"]  # a built-in EP has no pack
    pack = load_catalog().pack("trt-rtx")
    wheels = load_catalog().pack_lock(pack["id"])["wheels"]
    store.write_json(store.pack_dir(pack["id"], pack["version"]) / "pack.json",
                     {**store.read_manifest(pack["id"], pack["version"]), "wheels": [[wheel["filename"], wheel["sha256"]] for wheel in wheels]})
    assert store.installed_pack_facts(load_catalog(), "trt-rtx")["wheels_match_lock"] is True
    assert report["evidence"] == {"valid": True, "reasons": []} and report["kind"] == "quick"
    assert report["summary"] == [*({"group": group, "name": name, "device": "10de:2484", "result": "pass"} for group, name in (
        ("ep", "TensorRT RTX"), ("gpu-jpeg", "TensorRT RTX"), ("ep", "DirectML"))),  # `directml` has no GPU JPEG decode
        {"group": "ep", "name": "CPU", "device": None, "result": "record-only"}]  # the CPU reference ran
    assert report["package"] == {"name": "skellytracker", "version": package_certification._package()[0]["version"],
                                 "commit": COMMIT, "tree_modified": False}
    assert report["host"]["os"]["arch"] == "x86_64" and report["host"]["gpus"][0]["id"] == "10de:2484"
    video = next(check for check in report["checks"] if check["name"] == "trt-rtx@10de-2484-0:video")
    modules = {check["name"]: check["module"] for check in report["checks"]}
    assert (modules["cpu:live"], modules["trt-rtx@10de-2484-0:jpeg-decode"], modules["directml@10de-2484-0"]) == ("CPU", "TensorRT RTX", "DirectML")
    assert video["numbers"]["box_iou_min"] == 1.0 and video["numbers"]["points_compared"] == 2 and video["numbers"]["frames"] == 3
    assert (video["numbers"]["ep_ms"], video["numbers"]["cpu_ms"], video["numbers"]["speed_against_cpu"]) == (6.0, 19.0, "faster")
    assert report["details"]["eps"]["trt-rtx@10de-2484-0"]["models"][0]["precision"] == "fp16"
    assert report["details"]["versions"]["set_hash"] == evidence.set_hash(load_catalog())
    (path,) = certification.reports_dir().glob("*.json")
    assert json.loads(path.read_text(encoding="utf-8")) == report
    pair = certification.pair_key(load_catalog(), "trt-rtx", gpu(), "Windows")
    assert len(local_results()) == 2
    local = local_results()[pair]
    assert local["result"] == "passed" and local["precisions"] == {"rtmw": "fp16"} and local["pipeline"].startswith("yolox")


def test_the_cpu_reference_runs_one_time_for_two_pairs(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    calls = fake_sessions(monkeypatch)
    skellytracker.certify("quick")
    device = "gpu:10de:2484:0"
    assert calls == [("cpu", ("video", "live"), None), ("trt-rtx", ("video",), device), ("trt-rtx", ("live",), device),
                     ("directml", ("video",), device), ("directml", ("live",), device)]


def test_a_probe_failure_skips_the_video_and_live_runs_and_records_the_failure(quick_host, monkeypatch):
    fake_probe(monkeypatch, ok=False)
    calls = fake_sessions(monkeypatch)
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    assert problems_of(report) == [] and "secretdir" not in json.dumps(report)
    assert results(report) == {**CPU_ROWS, "trt-rtx@10de-2484-0:probe": ("fail", "probe-l3-failed"),
                               "trt-rtx@10de-2484-0:video": ("not-run", "probe-not-passed"),
                               "trt-rtx@10de-2484-0:live": ("not-run", "video-not-passed"), "trt-rtx@10de-2484-0": ("fail", "probe-l3-failed")}
    assert [key for key, *_ in calls] == ["cpu"] and [row["result"] for row in local_results().values()] == ["failed"]
    fake_probe(monkeypatch, ok=False, code="crashed")
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    probe = next(check for check in report["checks"] if check["name"] == "trt-rtx@10de-2484-0:probe")
    assert (probe["result"], probe["reason"], probe["numbers"]["exit_code"]) == ("fail", "crashed", 3)


def test_frame_0_has_each_threshold_and_a_later_frame_fails_only_on_the_people_the_finite_outputs_and_the_box(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    video = "trt-rtx@10de-2484-0:video"
    frames = [frame(), frame(shift=3.0), frame()]  # frame 1 is over the keypoint limit (3 px on a box of 224 px): a record only
    fake_sessions(monkeypatch, video={"frames": frames})
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    assert results(report)[video] == ("pass", None) and results(report)["trt-rtx@10de-2484-0"] == ("pass", None)
    numbers = next(check["numbers"] for check in report["checks"] if check["name"] == video)
    assert (numbers["keypoint_px_max"], numbers["keypoint_box_fraction_max"], numbers["frames"]) == (0.0, 0.0, 3)  # frame 0
    assert numbers["later_keypoint_box_fraction_max"] == pytest.approx(3.0 / np.hypot(100.0, 200.0))
    fake_sessions(monkeypatch, video={"frames": [frame(shift=3.0), frame(), frame()]})  # frame 0 has each threshold
    assert results(skellytracker.certify("quick", execution_providers=["trt-rtx"]))[video] == ("fail", "keypoints-differ")
    for later, reason in ((frame(box=50.0), "box-differs"), (frame(people=0), "people-differ"), (frame(nan=True), "not-finite")):
        fake_sessions(monkeypatch, video={"frames": [frame(), later, frame()]})
        assert results(skellytracker.certify("quick", execution_providers=["trt-rtx"]))[video] == ("fail", reason)


def test_the_first_frame_that_differs_fails_the_video_check_and_a_hang_at_exit_adds_the_exit_check(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    frames = [frame(), frame(shift=3.0), frame(people=0)]  # the second frame is a record only, the third gives `people-differ`
    fake_sessions(monkeypatch, video=lambda key, settings, modes, *a, **k: (session_found(key, modes, frames=frames), "hung-at-exit", 0))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    assert problems_of(report) == []
    assert results(report) == {**CPU_ROWS, "trt-rtx@10de-2484-0:probe": ("pass", None), "trt-rtx@10de-2484-0:video": ("fail", "people-differ"),
                               "trt-rtx@10de-2484-0:video:exit": ("record-only", "hung-at-exit"),
                               "trt-rtx@10de-2484-0:live": ("not-run", "video-not-passed"), "trt-rtx@10de-2484-0": ("fail", "people-differ")}


def test_a_failed_live_check_fails_the_roll_up_check_and_is_stored(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    pair = certification.pair_key(load_catalog(), "trt-rtx", gpu(), "Windows")
    for live, reason in (({"frames": [frame(nan=True)] * 3}, "not-finite"), ({"frames": [frame(people=0)] * 3}, "no-person"),
                         (lambda *a, **k: (None, "crashed", 5), "crashed"), ({"error": "RuntimeError"}, "RuntimeError")):
        fake_sessions(monkeypatch, live=live)
        report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
        found = results(report)
        assert found["trt-rtx@10de-2484-0:live"] == found["trt-rtx@10de-2484-0"] == ("fail", reason) and problems_of(report) == []
        assert store.read_json(store.store_root() / "quick-checks.json")[pair]["result"] == "failed"


def test_with_no_cpu_reference_the_video_check_is_not_run(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch, cpu={"frames": [frame(people=0)] * 3})
    found = results(skellytracker.certify("quick", execution_providers=["trt-rtx"]))
    assert found["cpu:video"] == ("fail", "no-person-on-cpu") and found["cpu:live"] == ("pass", None)
    assert found["trt-rtx@10de-2484-0:video"] == found["trt-rtx@10de-2484-0"] == ("not-run", "cpu-reference-missing")
    assert found["trt-rtx@10de-2484-0:live"] == ("not-run", "video-not-passed")
    monkeypatch.setattr(certification, "session_run", REAL_SESSION_RUN)
    monkeypatch.setattr(certification, "_session_child", child_fakes.crash)  # a real child: os._exit(5)
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    cpu = [next(c for c in report["checks"] if c["name"] == name) for name in package_certification.CPU_CHECKS]
    assert [(row["result"], row["reason"], row["numbers"]["exit_code"]) for row in cpu] == [("fail", "crashed", 5)] * 2
    assert results(report)["trt-rtx@10de-2484-0:video"] == ("not-run", "cpu-reference-missing") and problems_of(report) == []
    assert report["summary"][-1] == {"group": "ep", "name": "CPU", "device": None, "result": "fail"}


def test_a_child_that_crashes_in_the_video_run_is_a_failure_with_its_exit_code(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch, video=lambda *a, **k: (None, "crashed", 5))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    video = next(c for c in report["checks"] if c["name"] == "trt-rtx@10de-2484-0:video")
    assert (video["result"], video["reason"], video["numbers"]["exit_code"]) == ("fail", "crashed", 5) and problems_of(report) == []


def test_missing_models_and_an_ep_that_cannot_run_are_not_run_and_record_nothing(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    calls = fake_sessions(monkeypatch)
    monkeypatch.setattr(package_certification, "_pipeline", lambda catalog, pipeline: ({}, "p@s", "models-missing"))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "cuda", "cpu"])
    assert problems_of(report) == [] and report["evidence"]["valid"] and calls == []  # a part of the EPs is not `partial-run`
    assert results(report) == {
        "cpu:video": ("not-run", "models-missing"), "cpu:live": ("not-run", "models-missing"),
        "trt-rtx@10de-2484-0:probe": ("pass", None), "trt-rtx@10de-2484-0:video": ("not-run", "models-missing"),
        "trt-rtx@10de-2484-0:live": ("not-run", "video-not-passed"), "trt-rtx@10de-2484-0": ("not-run", "models-missing"),
        **{f"cuda@10de-2484-0{part}": ("not-run", "ep-not-installed") for part in (":probe", ":video", ":live", "")},
        "cpu:probe": ("not-run", "not-gpu-ep"), "cpu": ("not-run", "not-gpu-ep")}
    assert local_results() == {}


def test_the_pipeline_check_gives_models_missing_or_outputs_not_comparable(monkeypatch):
    from skellytracker.core import pipelines

    config = types.SimpleNamespace(pipeline_id="mine", source=types.SimpleNamespace(name="me"))
    catalog = types.SimpleNamespace(data={"certification": {"pipeline": "default@skellytracker"}})
    loaded = []
    monkeypatch.setattr(pipelines, "load_pipeline", lambda source: loaded.append(source) or config)
    monkeypatch.setattr(pipelines, "export_pipeline", lambda config: {"pipeline_id": "mine"})
    for warnings, outputs, reason in (([types.SimpleNamespace(code="missing_dependency")], {"boxes": {}, "wholebody": {}}, "models-missing"),
                                      ([], {"holistic": {}}, "outputs-not-comparable"), ([], {"boxes": {}, "wholebody": {}}, None)):
        monkeypatch.setattr(pipelines, "check_pipeline", lambda config, w=warnings, o=outputs: types.SimpleNamespace(warnings=w, output_schema=o))
        assert package_certification._pipeline(catalog, None) == ({"pipeline_id": "mine"}, "mine@me", reason)
    assert loaded[0] == "default@skellytracker" and package_certification._pipeline(catalog, "my.pipeline.yaml")[1] == "mine@me"
    assert loaded[-1] == "my.pipeline.yaml"


def cancel_after(seconds: float) -> tuple[threading.Event, list[float]]:
    cancel, set_at = threading.Event(), []
    threading.Timer(seconds, lambda: (set_at.append(time.monotonic()), cancel.set())).start()
    return cancel, set_at


def test_a_cancel_stops_the_probe_child_and_stores_no_verdict(quick_host, monkeypatch):
    monkeypatch.setattr(verification._verify_child, "main", child_fakes.hang)  # a real child that never answers
    cancel, set_at = cancel_after(1.0)
    report = skellytracker.certify("quick", cancel=cancel, execution_providers=["trt-rtx"])
    assert time.monotonic() - set_at[0] < 3
    assert set(results(report).values()) - set(CPU_ROWS.values()) == {("not-run", "cancelled")} and "cancelled" in report["evidence"]["reasons"]
    assert problems_of(report) == [] and store.read_verdicts() == {} and local_results() == {}


def test_a_cancel_stops_the_cpu_reference_child_and_the_video_child(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    monkeypatch.setattr(certification, "_session_child", child_fakes.hang)  # a real child that never answers
    fake_sessions(monkeypatch, video=REAL_SESSION_RUN)
    cancel, set_at = cancel_after(1.0)
    report = skellytracker.certify("quick", cancel=cancel, execution_providers=["trt-rtx"])
    assert time.monotonic() - set_at[0] < 3
    assert results(report) == {**CPU_ROWS, "trt-rtx@10de-2484-0:probe": ("pass", None), "trt-rtx@10de-2484-0:video": ("not-run", "cancelled"),
                               "trt-rtx@10de-2484-0:live": ("not-run", "cancelled"), "trt-rtx@10de-2484-0": ("not-run", "cancelled")}
    assert report["evidence"]["valid"] is False and local_results() == {}
    fake_sessions(monkeypatch, cpu=REAL_SESSION_RUN)
    cancel, set_at = cancel_after(1.0)
    report = skellytracker.certify("quick", cancel=cancel, execution_providers=["trt-rtx"])
    assert time.monotonic() - set_at[0] < 3 and set(results(report).values()) == {("not-run", "cancelled")}


def test_each_new_check_names_its_row_in_a_progress_message_before_its_child_starts(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    messages, seen = [], []
    fake = certification.session_run  # the fake of `quick_host`: it sends each mode to `progress`

    def session_run(*args, **kwargs):
        seen.append(messages[-1]["step"]["name"])  # before the child starts
        found = fake(*args, **kwargs)
        seen.append(messages[-1]["step"]["name"])  # after the child
        return found

    monkeypatch.setattr(certification, "session_run", session_run)
    skellytracker.certify("quick", messages.append, execution_providers=["trt-rtx"])
    ep = "trt-rtx@10de-2484-0"
    assert seen == ["cpu:video", "cpu:live", f"{ep}:video", f"{ep}:video", f"{ep}:live", f"{ep}:live"]  # `cpu:live` when its mode starts


def test_each_progress_message_is_the_complete_state_and_a_raising_callback_is_dropped(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    messages, times = [], []
    skellytracker.certify("quick", lambda message: (messages.append(json.loads(json.dumps(message))), times.append(time.monotonic())),
                          execution_providers=["trt-rtx"])
    assert [m["state"] for m in messages][0] == "starting" and [m["state"] for m in messages][-2:] == ["cleaning-up", "done"]
    assert messages[0]["checks"] == [{"name": name, "result": None} for name in (
        "cpu:video", "cpu:live", "trt-rtx@10de-2484-0:probe", "trt-rtx@10de-2484-0:video", "trt-rtx@10de-2484-0:live",
        "trt-rtx@10de-2484-0:jpeg-decode", "trt-rtx@10de-2484-0:jpeg-preprocess", "trt-rtx@10de-2484-0")]
    assert messages[0]["total"] == 8 and messages[0]["done"] == 0 and messages[0]["seconds_left"] == (
        package_certification.CPU_REFERENCE_SECONDS + package_certification.PROBE_SECONDS + 15 + package_certification.LIVE_SECONDS
        + package_certification.JPEG_SECONDS)
    running = [m for m in messages if m["step"] == {"name": "trt-rtx@10de-2484-0:video"}]
    assert running[0]["checks"][:4] == [{"name": "cpu:video", "result": "pass"}, {"name": "cpu:live", "result": "pass"},
                                        {"name": "trt-rtx@10de-2484-0:probe", "result": "pass"}, {"name": "trt-rtx@10de-2484-0:video", "result": None}]
    assert messages[-1]["done"] == 8 and messages[-1]["seconds_left"] == 0
    assert all(later - earlier >= 0.09 for earlier, later in zip(times, times[1:], strict=False))
    calls = []

    def broken(message):
        calls.append(message)
        raise RuntimeError("the interface is gone")

    assert results(skellytracker.certify("quick", broken))["trt-rtx@10de-2484-0"] == ("pass", None) and len(calls) == 1


def test_the_plan_gives_the_time_the_total_and_each_ep_that_will_not_run_and_downloads_nothing(quick_host, monkeypatch):
    pc = package_certification
    plan = skellytracker.certify_plan("quick", execution_providers=["directml", "cuda"])
    assert plan["seconds_estimate"] == pc.CPU_REFERENCE_SECONDS + pc.PROBE_SECONDS + pc.VIDEO_SECONDS + pc.LIVE_SECONDS
    assert plan["total"] == 2 + 4 and plan["risks"] == [] and plan["downloads"] == []  # the CPU reference and the 4 checks of `directml`
    assert plan["details"] == {"execution_providers": ["directml", "cuda"], "checks": ["directml@10de-2484-0", "cuda@10de-2484-0"],
                               "not_run": {"cuda@10de-2484-0": "ep-not-installed"}, "os_known": False}
    assert skellytracker.certify_plan("quick")["details"]["execution_providers"] == ["trt-rtx", "directml"]  # the default
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pc, "QUICK_BUDGET_SECONDS", 10)
        assert skellytracker.certify_plan("quick")["seconds_estimate"] == 10  # at most the budget
    assert plan["system_changes"] == [] and plan["questions"] == [] and plan["kind"] == "quick"
    nothing = skellytracker.certify_plan("quick", execution_providers=["cuda"])
    assert (nothing["total"], nothing["seconds_estimate"]) == (0, 0)  # no check can run
    old_set = reviewed("trt-rtx", set="0" * 64)  # a row of an other version set is not reviewed: it still gives `os_known`
    monkeypatch.setattr(evidence, "load_evidence", lambda: (old_set,))
    plan = skellytracker.certify_plan("quick")
    assert plan["details"]["execution_providers"] == ["trt-rtx", "directml"] and plan["details"]["os_known"] is True
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"),))
    assert skellytracker.certify_plan("quick")["details"]["execution_providers"] == ["directml"]
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx", os_label="Windows 10 Pro"), reviewed("directml")))
    plan = skellytracker.certify_plan("quick")
    assert plan["details"]["execution_providers"] == [] and (plan["total"], plan["seconds_estimate"]) == (0, 0)  # each pair is reviewed
    report = skellytracker.certify("quick")
    assert report["checks"] == [] and report["evidence"] == {"valid": False, "reasons": ["no-check"]} and problems_of(report) == []
    assert report["details"]["skipped"] == {"trt-rtx@10de-2484-0": "reviewed", "directml@10de-2484-0": "reviewed",
                                            "mediapipe:smoke": "reviewed"}  # the reviewed MediaPipe row of `quick_host`
    assert not certification.reports_dir().exists()
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx", os_label="Windows 10 Pro", result="fail"),))
    assert skellytracker.certify_plan("quick")["details"]["os_known"] is False  # a failure, and an other OS key
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"), reviewed("directml")))
    full = skellytracker.certify_plan("full")  # the level `full` also takes an EP with a reviewed row, and the CPU EP checks
    assert full["details"]["checks"] == ["trt-rtx@10de-2484-0", "directml@10de-2484-0"] and full["kind"] == "full"
    assert full["downloads"] == [] and full["risks"] == [] and full["total"] == 6 + 2 * 8  # `<ep>:jpeg` counts as one check
    cpu = (len(pc.CAMERA_COUNTS) * pc.PIPELINE_SECONDS + pc.JPEG_FULL_SECONDS)
    assert full["seconds_estimate"] == 3 * cpu + pc.CPU_REFERENCE_SECONDS + 2 * (pc.PROBE_SECONDS + pc.LIVE_SECONDS) + sum(
        load_catalog().data["certification"]["seconds"].get(key, pc.VIDEO_SECONDS) for key in ("trt-rtx", "directml"))


def test_the_os_key_is_the_name_and_the_release_of_the_os():
    assert [evidence.os_key(label) for label in ("Windows 11 Home 26H2", "Ubuntu 24.04.1 LTS", "macOS 15.1", "macOS 15", None, "")] == [
        "Windows 11", "Ubuntu 24.04", "macOS 15", "macOS 15", None, None]


def test_a_reviewed_pair_is_skipped_also_when_the_caller_names_it_and_has_a_summary_item(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    calls = fake_sessions(monkeypatch)
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"),))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "directml"], device="gpu:10de:2484:0")
    assert problems_of(report) == [] and report["details"]["skipped"] == {"trt-rtx@10de-2484-0": "reviewed"}
    assert not [name for name in results(report, jpeg=True) if name.startswith("trt-rtx")] and ("trt-rtx", ("video",), "gpu:10de:2484:0") not in calls
    assert report["summary"] == [{"group": "ep", "name": "DirectML", "device": "10de:2484", "result": "pass"},
                                 {"group": "ep", "name": "TensorRT RTX", "device": "10de:2484", "result": "skipped", "reason": "reviewed"},
                                 {"group": "ep", "name": "CPU", "device": None, "result": "record-only"}]
    fake_full(monkeypatch)
    full = skellytracker.certify("full", execution_providers=["trt-rtx"])
    assert results(full)["trt-rtx@10de-2484-0"] == ("pass", None) and full["details"]["skipped"] == {}  # the level `full` checks it


def test_a_check_that_does_not_fit_in_the_budget_is_not_run_and_stores_nothing(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    ep = "trt-rtx@10de-2484-0"
    clock = [1000.0]
    monkeypatch.setattr(package_certification.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(package_certification, "PROGRESS_INTERVAL", 0.0)

    def slow_cpu(key, settings, modes, *args, **kwargs):  # the CPU reference takes 73 s: 2 s are left, less than a probe
        clock[0] += 73.0
        return session_found(key, modes), None, 0

    fake_sessions(monkeypatch, cpu=slow_cpu)
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "directml"])  # two EPs: the estimates decide
    found = results(report)
    assert found["cpu:video"] == ("pass", None) and found[f"{ep}:probe"] == ("not-run", "over-budget")
    assert found[f"{ep}:video"] == ("not-run", "probe-not-passed") and found[ep] == ("not-run", "over-budget")
    assert found["directml@10de-2484-0"] == ("not-run", "over-budget") and problems_of(report) == []
    assert local_results() == {}
    timeouts = []

    def cut(key, settings, modes, *args, timeout=None, **kwargs):  # the child runs to the end of the budget
        timeouts.append(timeout)
        return None, "timed-out", None

    fake_sessions(monkeypatch, cpu=slow_cpu, video=cut)
    clock[0] = 1000.0
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])  # one EP: the whole budget, no skip on an estimate
    found = results(report)
    assert found[f"{ep}:probe"] == ("pass", None) and found[f"{ep}:video"] == found[ep] == ("not-run", "over-budget")
    assert timeouts == [2.0] and store.read_json(store.store_root() / "quick-checks.json") is None  # 75 s - 73 s
    fake_sessions(monkeypatch, video=lambda *a, **k: (None, "timed-out", None))
    clock[0] = 1000.0
    found = results(skellytracker.certify("quick", execution_providers=["trt-rtx"]))
    assert found[f"{ep}:video"] == ("not-run", "over-budget")  # the clock stands still: the time limit is the budget
    monkeypatch.setattr(package_certification, "QUICK_BUDGET_SECONDS", 1000)
    clock[0] = 1000.0
    found = results(skellytracker.certify("quick", execution_providers=["trt-rtx"]))
    assert found[f"{ep}:video"] == ("fail", "timed-out")  # the child limit, not the budget: a real failure
    clock[0] = 1000.0
    fake_full(monkeypatch)
    found = results(skellytracker.certify("full", execution_providers=["trt-rtx"]))
    assert found[f"{ep}:video"] == ("fail", "timed-out")  # the level `full` has no budget


def test_a_cancel_object_of_an_other_class_with_is_set_is_accepted(quick_host, monkeypatch):
    import multiprocessing

    seen = []
    monkeypatch.setattr(verification, "spawn_child", lambda target, args, **options: seen.append(options["cancel"]) or ({"ran": False}, None, 0))
    cancel = multiprocessing.get_context("spawn").Event()
    certification.timing_run("trt-rtx", {}, 1, cancel=cancel)
    REAL_SESSION_RUN("trt-rtx", {}, ("video",), cancel=cancel)
    assert seen == [cancel, cancel]  # beartype checks each call


def test_with_no_valid_test_frames_the_session_checks_are_not_run_and_nothing_is_downloaded(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    calls = fake_sessions(monkeypatch)
    monkeypatch.setattr(_download, "fetch", lambda *a, **k: pytest.fail("certify() downloads nothing"))
    settings = {"frames": {**certification.frames_record(), "sha256": "0" * 64}}
    with pytest.raises(certification.FramesUnavailableError):
        certification.quick_frames(settings)
    with pytest.raises(certification.FramesUnavailableError):
        certification.frames_file({"frames": {**settings["frames"], "path": "test_media/none.zip"}})
    real = certification.frames_file
    monkeypatch.setattr(certification, "frames_file", lambda found: real({**found, **settings}))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    ep = "trt-rtx@10de-2484-0"
    assert results(report) == {"cpu:video": ("not-run", "test-media-missing"), "cpu:live": ("not-run", "test-media-missing"),
                               f"{ep}:probe": ("pass", None), f"{ep}:video": ("not-run", "test-media-missing"),
                               f"{ep}:live": ("not-run", "test-media-missing"), ep: ("not-run", "test-media-missing")}
    assert calls == [] and problems_of(report) == [] and store.read_json(store.store_root() / "quick-checks.json") is None
    fake_full(monkeypatch)
    found = results(skellytracker.certify("full", execution_providers=["trt-rtx"]))
    assert found["cpu:video"] == found[f"{ep}:live"] == found["cpu:pipeline-1"] == ("not-run", "test-media-missing")


def test_the_test_frames_are_a_file_of_the_package_with_the_sha256_and_the_count_of_the_catalog():
    import importlib.resources
    import zipfile

    settings = {"frames": certification.frames_record()}
    data = (importlib.resources.files("skellytracker.core") / "model_zoo" / settings["frames"]["path"]).read_bytes()
    assert len(data) == settings["frames"]["bytes"] and certification.frames_file(settings) == data
    with zipfile.ZipFile(certification.io.BytesIO(data)) as archive:
        assert sorted(archive.namelist()) == [f"frame_{index:02d}.jpg" for index in range(settings["frames"]["count"])]
    assert settings["frames"]["count"] == certification.FRAMES
    frames = certification.quick_frames(settings)
    assert len(frames) == certification.FRAMES and frames[0].shape == (1280, 720, 3) and frames[0].dtype == np.uint8


def fake_full(monkeypatch, timing=None, jpeg=None):
    """Fake the children of the level `full`: the pipeline timing and the JPEG certification. Give the calls."""
    calls = []

    def timing_run(key, settings, cameras, device_key=None, cancel=None):
        calls.append(("timing", key, cameras, device_key))
        found = {"cameras": cameras, "start_seconds": 1.5, "first_call_ms": 40.0, "calls": 100, "p95_ms": 9.0, "peak_vram_mib": None,
                 "vram_before_mib": 10, "median_ms": 20.0 * cameras if key == "cpu" else 5.0 * cameras}
        return timing(key, cameras, found) if timing else (found, None, 0)

    def jpeg_spawn(key, device_key, cancel):
        calls.append(("jpeg", key, device_key))
        checks = [{"name": "cpu_decode.baseline_420", "result": "pass", "reason": "ok", "numbers": {"max_abs_diff": 1}, "detail": "C:\\secretdir"},
                  {"name": "gpu_decode.baseline_422", "result": "pass" if key else "not-run", "reason": "ok" if key else "ep_not_present"},
                  {"name": "preprocess_graph_ep.yolox_person", "result": "fail" if key else "not-run", "reason": "over_limit"}]
        return jpeg(key) if jpeg else ({"checks": checks, "quick": {"gpu_decode.baseline_422": "jpeg-decode",
                                                                   "preprocess_graph_ep.yolox_person": "jpeg-preprocess"}}, None, 0)

    monkeypatch.setattr(certification, "timing_run", timing_run)
    monkeypatch.setattr(package_certification, "_jpeg_full_spawn", jpeg_spawn)
    return calls


def test_the_full_level_times_the_pipeline_and_runs_the_jpeg_certification_on_the_cpu_ep_and_on_each_ep(quick_host, monkeypatch):
    from skellytracker.core.decode import certification as decode_certification

    assert package_certification.JPEG_FULL_EPS == (*decode_certification.GPU_FRAME_EPS, *decode_certification.AMD_EPS)
    fake_probe(monkeypatch)
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"),))  # a reviewed row: the level `full` still checks the EP
    assert skellytracker.certify_plan("quick")["details"]["checks"] == ["directml@10de-2484-0"]
    calls = fake_full(monkeypatch, timing=lambda key, cameras, found: (
        ({"error": "RuntimeError"}, None, 0) if (key, cameras) == ("trt-rtx", 6) else (found, "hung-at-exit" if cameras == 3 and key != "cpu" else None, 0)))
    report = skellytracker.certify("full", execution_providers=["trt-rtx"])
    ep = "trt-rtx@10de-2484-0"
    assert problems_of(report) == [] and report["kind"] == "full" and report["evidence"] == {"valid": True, "reasons": []}
    assert [check["name"] for check in report["checks"]] == [
        "cpu:video", "cpu:live", "cpu:pipeline-1", "cpu:pipeline-3", "cpu:pipeline-6", "cpu:jpeg", "cpu:jpeg:cpu_decode.baseline_420",
        "cpu:jpeg:gpu_decode.baseline_422", "cpu:jpeg:preprocess_graph_ep.yolox_person",
        f"{ep}:probe", f"{ep}:video", f"{ep}:live", f"{ep}:pipeline-1", f"{ep}:pipeline-3", f"{ep}:pipeline-3:exit", f"{ep}:pipeline-6",
        f"{ep}:jpeg", f"{ep}:jpeg:cpu_decode.baseline_420", f"{ep}:jpeg:gpu_decode.baseline_422",
        f"{ep}:jpeg:preprocess_graph_ep.yolox_person", ep]
    found = results(report, jpeg=True)
    assert found["cpu:jpeg"] == ("pass", None) and found["cpu:jpeg:gpu_decode.baseline_422"] == ("not-run", "ep_not_present")
    assert found[f"{ep}:pipeline-1"] == ("record-only", None) and found[f"{ep}:pipeline-6"] == ("not-run", "RuntimeError")
    assert found[f"{ep}:jpeg"] == ("fail", "over_limit") and found[ep] == ("pass", None)  # a JPEG failure never changes the EP check
    numbers = next(check["numbers"] for check in report["checks"] if check["name"] == f"{ep}:pipeline-1")
    assert (numbers["median_ms"], numbers["against_cpu"], numbers["speed_against_cpu"], numbers["peak_vram_mib"]) == (5.0, 0.25, "faster", None)
    assert "against_cpu" not in next(check["numbers"] for check in report["checks"] if check["name"] == "cpu:pipeline-1")
    assert [item for item in report["summary"] if item["group"] == "benchmark"] == [  # no item for `pipeline-6` of the EP: it did not run
        {"group": "benchmark", "name": name, "device": device, "stage": f"pipeline-{cameras}", "ms_per_frame": ms, "fps": fps}
        for name, device, cameras, ms, fps in (("CPU", None, 1, 20.0, 50.0), ("CPU", None, 3, 60.0, 16.7), ("CPU", None, 6, 120.0, 8.3),
                                               ("TensorRT RTX", "10de:2484", 1, 5.0, 200.0), ("TensorRT RTX", "10de:2484", 3, 15.0, 66.7))]
    assert next(check for check in report["checks"] if check["name"] == f"{ep}:jpeg:gpu_decode.baseline_422")["module"] == "TensorRT RTX"
    assert calls == [*(("timing", "cpu", cameras, None) for cameras in (1, 3, 6)), ("jpeg", None, None),
                     *(("timing", "trt-rtx", cameras, "gpu:10de:2484:0") for cameras in (1, 3, 6)), ("jpeg", "trt-rtx", "gpu:10de:2484:0")]
    assert report["details"]["full"]["camera_counts"] == [1, 3, 6] and report["details"]["eps"][ep]["pack_version"]
    (path,) = certification.reports_dir().glob("*.json")
    assert path.stem == report["id"] and json.loads(path.read_text(encoding="utf-8")) == report
    pair = certification.pair_key(load_catalog(), "trt-rtx", gpu(), "Windows")
    local = store.read_json(store.store_root() / "quick-checks.json")[pair]
    assert (local["result"], local["jpeg"]) == ("passed", {"jpeg-decode": "pass", "jpeg-preprocess": "fail"})
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())  # the level `quick` never checks a reviewed pair
    skellytracker.certify("quick", execution_providers=["trt-rtx"])  # a newer quick pass does not delete the report of the level `full`
    assert path.exists() and len(list(certification.reports_dir().glob("*.json"))) == 2


def test_the_full_level_keeps_the_ep_checks_when_a_child_ends_or_the_video_check_does_not_pass(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    fake_full(monkeypatch, timing=lambda key, cameras, found: (None, "crashed", 5), jpeg=lambda key: (None, "timed-out", None))
    report = skellytracker.certify("full", execution_providers=["trt-rtx", "cpu"])
    ep, found = "trt-rtx@10de-2484-0", results(report, jpeg=True)
    assert problems_of(report) == []
    assert found["cpu:pipeline-1"] == ("fail", "crashed") and found["cpu:jpeg"] == ("fail", "timed-out")
    assert found[f"{ep}:pipeline-1"] == ("not-run", "video-not-passed") and found[f"{ep}:jpeg"] == ("fail", "timed-out")
    assert found[ep] == ("fail", "box-differs") and found["cpu"] == ("not-run", "not-gpu-ep")  # a named `cpu` adds no second timing
    assert [name for name in found if name.startswith("cpu")] == ["cpu:video", "cpu:live", "cpu:pipeline-1", "cpu:pipeline-3",
                                                                  "cpu:pipeline-6", "cpu:jpeg", "cpu:probe", "cpu"]


def test_a_version_that_is_not_semver_gives_no_version(monkeypatch):
    monkeypatch.setattr(package_certification, "_commit", lambda: (COMMIT, False))
    for version, reasons in (("2.0.0", []), ("2.0.0-rc.1", []), ("v2024.09.1019", ["no-version"]), ("2.0.0rc1", ["no-version"])):
        monkeypatch.setattr(package_certification.importlib.metadata, "version", lambda name, v=version: v)
        package, found = package_certification._package()
        assert package["version"] == version and found == reasons


def test_the_commit_comes_from_the_build_info_then_git_else_none(monkeypatch):
    monkeypatch.setitem(sys.modules, "skellytracker._build_info", types.SimpleNamespace(COMMIT=COMMIT, TREE_MODIFIED=False))
    monkeypatch.setattr(skellytracker, "_build_info", sys.modules["skellytracker._build_info"], raising=False)
    assert package_certification._commit() == (COMMIT, False)
    assert package_certification._package()[1] in ([], ["no-version"])
    monkeypatch.delitem(sys.modules, "skellytracker._build_info")
    monkeypatch.delattr(skellytracker, "_build_info")
    monkeypatch.setattr(package_certification.shutil, "which", lambda name: None)  # no git, as in a frozen application
    assert package_certification._commit() == (None, None)
    reasons = package_certification._package()[1]
    assert "no-commit" in reasons and "modified-tree" in reasons


def test_a_checkout_with_git_gives_its_commit(monkeypatch):
    if package_certification.shutil.which("git") is None or not (package_certification.Path(package_certification.__file__).parents[1] / ".git").exists():
        pytest.skip("not a git checkout")
    commit, modified = package_certification._commit()
    assert re.fullmatch(r"[0-9a-f]{40}", commit) and isinstance(modified, bool)


def test_a_field_test_ep_keeps_its_opt_in_only_after_a_pass(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    seen = []
    fake_sessions(monkeypatch, video=lambda key, settings, modes, *a, **k: seen.append(dict(store.field_test_opt_ins())) or
                  (session_found(key, modes, **BAD_VIDEO), None, 0))
    report = skellytracker.certify("quick", execution_providers=["directml"])
    assert results(report)["directml@10de-2484-0"] == ("fail", "box-differs") and "directml" in seen[0]  # opted in during the check
    assert store.field_test_opt_ins() == {} and report["cleanup"] == []
    fake_sessions(monkeypatch)
    assert results(skellytracker.certify("quick", execution_providers=["directml"]))["directml@10de-2484-0"] == ("pass", None)
    assert list(store.field_test_opt_ins()) == ["directml"]
    pair = certification.pair_key(load_catalog(), "directml", gpu(), "Windows")
    assert pair.startswith("directml|builtin|") and local_results()[pair]["result"] == "passed"
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    skellytracker.certify("quick", execution_providers=["directml"])
    assert list(store.field_test_opt_ins()) == ["directml"]  # an opt-in from before the run stays


def test_the_check_runs_on_each_gpu_of_the_ep_or_on_the_gpus_of_the_option_device(quick_host, monkeypatch):
    intel = gpu(vendor="intel", cc=None, vram=2 * 1024**3, bus="0000:00:02.0", device_id=0x4680, name="Intel(R) UHD Graphics 770")
    two = host(gpu(), intel)
    for module in (state, recommendation, installer, verification, host_module):
        monkeypatch.setattr(module, "probe_host", lambda: two)
    calls = fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    names = [name for name in results(skellytracker.certify("quick", execution_providers=["directml"])) if ":" not in name]
    assert names == ["directml@10de-2484-0", "directml@8086-4680-0"]  # the GPU with the most VRAM first
    assert [device for _, device in calls] == ["gpu:10de:2484:0", "gpu:8086:4680:0"]
    assert len(local_results()) == 2  # one stored result for each GPU model
    plan = skellytracker.certify_plan("quick", device="gpu:8086:4680:0")
    assert plan["details"]["checks"] == ["directml@8086-4680-0"]  # the default selection, on that GPU only
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "directml"], device=["gpu:8086:4680:0"])
    assert results(report)["trt-rtx"] == ("not-run", "gpu-not-usable") and results(report)["directml@8086-4680-0"] == ("pass", None)
    with pytest.raises(ValueError, match="device key"):
        skellytracker.certify_plan("quick", device="gpu:1234:5678:0")


def test_the_jpeg_checks_never_change_the_ep_check_and_their_results_are_stored(quick_host, monkeypatch):
    from skellytracker.core.decode import certification as decode_certification

    assert package_certification.JPEG_EPS == decode_certification.GPU_FRAME_EPS
    assert package_certification.JPEG_CHECKS == tuple(decode_certification.QUICK_CHECKS.values())
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    fake_jpeg(monkeypatch, jpeg_decode=("not-run", "component_not_installed"), jpeg_preprocess=("fail", "over_limit"))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "directml"])
    found = results(report, jpeg=True)
    assert problems_of(report) == [] and "secretdir" not in json.dumps(report)
    assert found["trt-rtx@10de-2484-0:jpeg-decode"] == ("not-run", "component_not_installed")
    assert found["trt-rtx@10de-2484-0:jpeg-preprocess"] == ("fail", "over_limit") and found["trt-rtx@10de-2484-0"] == ("pass", None)
    assert not [name for name in found if name.startswith("directml") and "jpeg" in name]  # only `cuda` and `trt-rtx`
    assert next(c for c in report["checks"] if c["name"] == "trt-rtx@10de-2484-0:jpeg-decode")["numbers"] == {"max_abs_diff": 0.0}
    stored = store.read_json(store.store_root() / "quick-checks.json")
    pair = certification.pair_key(load_catalog(), "trt-rtx", gpu(), "Windows")
    assert stored[pair]["result"] == "passed" and stored[pair]["jpeg"] == {"jpeg-decode": "not-run", "jpeg-preprocess": "fail"}
    assert all("jpeg" not in row for key, row in stored.items() if key.startswith("directml"))
    fake_jpeg(monkeypatch, found={}, problem="hung-at-exit")  # a child that gave no check, and then did not exit
    found = results(skellytracker.certify("quick", execution_providers=["trt-rtx"]), jpeg=True)
    assert found["trt-rtx@10de-2484-0:jpeg-decode"] == ("fail", "no-result") and found["trt-rtx@10de-2484-0:jpeg-preprocess:exit"] == ("record-only", "hung-at-exit")
    monkeypatch.setattr(package_certification, "_jpeg_spawn", lambda key, device_key, cancel, timeout=None: (None, "crashed", 5))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    row = next(c for c in report["checks"] if c["name"] == "trt-rtx@10de-2484-0:jpeg-decode")
    assert (row["result"], row["reason"], row["numbers"]) == ("fail", "crashed", {"exit_code": 5}) and results(report)["trt-rtx@10de-2484-0"] == ("pass", None)
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    found = results(skellytracker.certify("quick", execution_providers=["trt-rtx"]), jpeg=True)
    assert found["trt-rtx@10de-2484-0:jpeg-decode"] == found["trt-rtx@10de-2484-0:jpeg-preprocess"] == ("not-run", "video-not-passed")


def test_the_hand_in_list_holds_each_report_with_a_check_that_ran_and_keeps_its_state(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    assert skellytracker.pending_reports() == []
    passed = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    skellytracker.certify("quick", execution_providers=["cuda"])  # not installed: no check ran, so it is not in the list
    monkeypatch.setattr(package_certification.time, "gmtime", lambda: time.struct_time((2030, 1, 1, 0, 0, 0, 0, 1, 0)))
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    skellytracker.certify("quick", execution_providers=["trt-rtx"])
    first, second = skellytracker.pending_reports()
    assert first == {"report_id": first["report_id"], "kind": "quick", "created_utc": passed["created_utc"], "has_failure": False,
                     "evidence_valid": True, "state": "pending", "reference": None}
    assert second["has_failure"] and second["created_utc"] == "2030-01-01T00:00:00Z" and UUID4.match(first["report_id"]) and passed["id"] == first["report_id"]
    assert skellytracker.read_report(first["report_id"]) == passed
    ids = [first["report_id"], second["report_id"]]
    skellytracker.mark_reports(ids, "covered", reference="https://example.invalid/issues/7")
    assert skellytracker.pending_reports() == []
    assert [(row["state"], row["reference"]) for row in skellytracker.pending_reports(include_handed_in=True)] == [
        ("covered", "https://example.invalid/issues/7")] * 2
    skellytracker.mark_reports(ids[:1], "opened")
    skellytracker.mark_reports(ids[1:], "pending")
    assert [(row["report_id"], row["state"], row["reference"]) for row in skellytracker.pending_reports(include_handed_in=True)] == [
        (ids[0], "opened", None), (ids[1], "pending", None)]
    for call in (lambda: skellytracker.mark_reports(ids, "sent"), lambda: skellytracker.mark_reports([ids[0], "quick-nope"], "covered"),
                 lambda: skellytracker.mark_reports("quick-x", "covered"), lambda: skellytracker.mark_reports(ids, "pending", reference="x"),
                 lambda: skellytracker.read_report("../certify")):
        with pytest.raises(ValueError):
            call()
    assert [row["state"] for row in skellytracker.pending_reports(include_handed_in=True)] == ["opened", "pending"]  # no change


def test_a_new_report_removes_an_older_pass_that_it_repeats_and_keeps_a_failure_and_a_handed_in_report(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    clock = iter(range(1, 60))
    monkeypatch.setattr(package_certification.time, "gmtime", lambda: time.struct_time((2030, 1, 1, 0, 0, next(clock), 0, 1, 0)))

    def run(*keys):
        skellytracker.certify("quick", execution_providers=list(keys))
        return [row["report_id"] for row in skellytracker.pending_reports(include_handed_in=True)]

    (both,) = run("trt-rtx", "directml")
    first = run("trt-rtx")
    assert first[0] == both and len(first) == 2  # `both` stays: it is the newest pass of `directml`
    second = run("trt-rtx")
    assert second[0] == both and len(second) == 2 and second[1] != first[1]  # the older pass of `trt-rtx` alone is gone
    handed_in = second[1]
    skellytracker.mark_reports([handed_in], "opened")
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    failure = run("trt-rtx")[-1]
    fake_sessions(monkeypatch)
    after = run("trt-rtx", "directml")  # it repeats the pass of `both`; the handed-in report and the failure stay
    assert after == [handed_in, failure, after[-1]] and both not in after
    assert len(list(certification.reports_dir().glob("*.json"))) == 3


def test_the_scrub_removes_a_private_name_and_counts_a_public_one(monkeypatch):
    monkeypatch.setattr(package_certification, "_private_words", lambda: ["secretname", "Windows"])
    report = {"host": {"os": {"name": "Windows"}}, "checks": [{"name": "trt-rtx", "reason": None}],
              "details": {"pipeline": "mine@secretname", "where": "C:\\data\\x", "secretname": 1}}
    clean = package_certification._scrub(report)
    assert clean["details"] == {"pipeline": "mine@<private>", "where": "<path>", "<private>": 1, "scrub": {"exempted_terms": 1}}
    assert clean["host"]["os"]["name"] == "Windows"


def test_the_cli_runs_the_quick_level_of_one_ep(quick_host, monkeypatch, capsys):
    fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    assert cli.main(["certify", "trt-rtx", "--json"]) == 0
    out = capsys.readouterr().out
    assert problems_of(json.loads(out)) == []
    assert cli.main(["certify", "cuda"]) == 3  # the pack is not installed
    assert "cuda@10de-2484-0: not-run (ep-not-installed)" in capsys.readouterr().out
    fake_sessions(monkeypatch, video=BAD_VIDEO)
    assert cli.main(["certify", "trt-rtx"]) == 1


def test_coreml_on_a_mac_needs_its_quick_check_and_its_result_has_the_key_of_the_chip(quick_host, monkeypatch):
    """ADR-ER5X item 6: `coreml` runs on the chip of the Mac and selects no GPU. The check rule applies to it."""
    import dataclasses

    from skellytracker.core import eps
    from skellytracker.core.eps import catalog as catalog_module
    from skellytracker.core.eps import gate, session
    from skellytracker.core.errors import EpUnavailableError

    mac = dataclasses.replace(host(os_name="Darwin", arch="arm64"), cpu_name="Apple M2 Pro")
    for module in (state, recommendation, installer, verification, host_module, session):
        monkeypatch.setattr(module, "probe_host", lambda: mac)
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "macosx_arm64")
    catalog = load_catalog()
    chip = gate.chip_of(catalog, "coreml", mac)
    assert (chip.name, chip.chip_id) == ("Apple M2 Pro", "chip:apple-m2-pro") and gate.chip_of(catalog, "cpu", mac) is None
    row = next(row for row in eps.status().eps if row.key == "coreml")
    assert (row.state, row.usable, row.reason_code) == ("builtin", False, "quick-check-needed")
    assert [(c.device_key, c.name, c.certified, c.local_result, c.usable) for c in row.checks] == [
        ("chip:apple-m2-pro", "Apple M2 Pro", False, None, False)]
    best = eps.recommend("performance", mac)
    assert best.chosen.ep_key == "cpu" and [(c.ep_key, c.needs_check) for c in best.skipped] == [("coreml", True)]
    for call in (lambda: eps.check_start("coreml"), lambda: eps.build_session(b"model", execution_provider="coreml")):
        with pytest.raises(EpUnavailableError, match="skellytracker-eps certify coreml`"):
            call()
    assert skellytracker.certify_plan("quick")["details"]["checks"] == ["coreml"]  # the default selection of a Mac
    calls = fake_probe(monkeypatch)
    fake_sessions(monkeypatch)
    report = skellytracker.certify("quick")
    assert results(report) == {**CPU_ROWS, **{f"coreml{part}": ("pass", None) for part in (":probe", ":video", ":live", "")}}
    assert calls == [(["coreml"], None)] and report["details"]["eps"]["coreml"] == {
        "gpu": "chip:apple-m2-pro", "device": None, "pack_version": "builtin", "models": MODELS, "warnings": []}
    assert problems_of(report) == []
    (pair,) = store.read_json(store.store_root() / "quick-checks.json")
    assert pair == "coreml|builtin|Darwin|chip:apple-m2-pro"
    row = next(row for row in eps.status().eps if row.key == "coreml")
    assert row.usable and row.checks[0].local_result == "passed" and eps.check_start("coreml") == ()
    assert eps.recommend("performance", mac).chosen.ep_key == "coreml"
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("coreml", "chip:apple-m2-pro", os="macOS", os_label="macOS 15.1"),))
    assert skellytracker.certify_plan("quick")["details"]["checks"] == []  # a reviewed row of the chip: no check
    assert skellytracker.certify("quick")["details"]["skipped"] == {"coreml": "reviewed", "mediapipe:smoke": "reviewed"}


def test_the_summary_lists_each_ep_that_ran_with_its_gpu_jpeg_result_and_the_cpu_ep_last():
    eps = {"cuda@10de-2484-0": {"gpu": "10de:2484"}, "trt-rtx@10de-2484-0": {"gpu": "10de:2484"}, "directml@8086-a780-0": {"gpu": "8086:a780"}}
    full = {"details": {"eps": eps}, "checks": [
        {"name": "cpu:pipeline-1", "result": "record-only"}, {"name": "cpu:jpeg", "result": "pass"},
        {"name": "cuda@10de-2484-0", "result": "pass"}, {"name": "cuda@10de-2484-0:jpeg:gpu_decode.a", "result": "pass"},
        {"name": "cuda@10de-2484-0:jpeg:gpu_decode.b", "result": "fail"},
        {"name": "trt-rtx@10de-2484-0", "result": "not-run"},  # an EP that did not run has no item
        {"name": "directml@8086-a780-0", "result": "fail"}, {"name": "directml@8086-a780-0:jpeg:gpu_decode.a", "result": "not-run"}]}
    assert package_certification._summary(full) == [
        {"group": "ep", "name": "CUDA", "device": "10de:2484", "result": "pass"},
        {"group": "gpu-jpeg", "name": "CUDA", "device": "10de:2484", "result": "fail"},
        {"group": "ep", "name": "DirectML", "device": "8086:a780", "result": "fail"},
        {"group": "ep", "name": "CPU", "device": None, "result": "record-only"}]
    quick = {"details": {"eps": eps}, "checks": [{"name": "cuda@10de-2484-0", "result": "pass"},
                                                 {"name": "cuda@10de-2484-0:jpeg-decode", "result": "pass"}]}
    assert [item["group"] for item in package_certification._summary(quick)] == ["ep", "gpu-jpeg"]  # no CPU row ran: no CPU item
    assert package_certification._summary({"details": {}, "checks": []}) == []


def test_the_full_level_runs_the_unreviewed_pairs_of_the_recommended_gpu_before_the_cpu_timings(quick_host, monkeypatch):
    """ADR-X7WD item 10: the CPU reference, the unreviewed pairs of the GPU with the most VRAM, the CPU timings, the rest."""
    intel = gpu(vendor="intel", cc=None, vram=2 * 1024**3, bus="0000:00:02.0", device_id=0x4680, name="Intel(R) UHD Graphics 770")
    two = host(gpu(), intel)
    for module in (state, recommendation, installer, verification, host_module):
        monkeypatch.setattr(module, "probe_host", lambda: two)
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"),))
    fake_probe(monkeypatch)
    calls = fake_full(monkeypatch)
    wanted = ["directml", "trt-rtx"]
    report = skellytracker.certify("full", execution_providers=wanted)
    order = [check["name"] for check in report["checks"] if check["name"] in ("cpu:video", "cpu:pipeline-1") or ":" not in check["name"]]
    assert order == ["cpu:video", "directml@10de-2484-0", "cpu:pipeline-1", "directml@8086-4680-0", "trt-rtx@10de-2484-0"]
    assert [(key, device) for kind, key, cameras, *device in calls if kind == "timing" and cameras == 1] == [
        ("directml", ["gpu:10de:2484:0"]), ("cpu", [None]), ("directml", ["gpu:8086:4680:0"]), ("trt-rtx", ["gpu:10de:2484:0"])]
    timing = next(check for check in report["checks"] if check["name"] == "directml@10de-2484-0:pipeline-1")
    assert timing["numbers"]["against_cpu"] == 0.25 and problems_of(report) == []  # added after the CPU timings
    assert skellytracker.certify_plan("full", execution_providers=wanted)["details"]["checks"] == [
        "directml@10de-2484-0", "directml@8086-4680-0", "trt-rtx@10de-2484-0"]


def test_certify_frames_gives_the_jpeg_bytes_from_the_package_or_from_the_test_media_folder(tmp_path):
    frames = package_certification.certify_frames()
    assert len(frames) == certification.FRAMES and all(isinstance(data, bytes) and data[:2] == b"\xff\xd8" for data in frames)
    record = certification.frames_record()
    stored = tmp_path / f"{record['sha256']}.zip"  # the name rule of the test media folder: the sha256 and the extension
    with pytest.raises(certification.FramesUnavailableError):
        package_certification.certify_frames(tmp_path)
    stored.write_bytes(b"not the frames")
    with pytest.raises(certification.FramesUnavailableError):
        package_certification.certify_frames(str(tmp_path))
    stored.write_bytes(certification.frames_file({"frames": record}))
    assert package_certification.certify_frames(tmp_path) == frames


def test_certify_reads_the_test_frames_from_the_test_media_folder_and_never_writes_its_path(quick_host, monkeypatch, tmp_path):
    fake_probe(monkeypatch)
    folders = []
    fake_sessions(monkeypatch, cpu=lambda key, settings, modes, *a, **k: (folders.append(settings["frames"]["dir"]), (session_found(key, modes), None, 0))[1])
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"], test_media_dir=tmp_path)  # no frames file there
    assert results(report)["cpu:video"] == ("not-run", "test-media-missing") and folders == []
    record = certification.frames_record()
    (tmp_path / f"{record['sha256']}.zip").write_bytes(certification.frames_file({"frames": record}))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"], test_media_dir=tmp_path)
    assert results(report)["trt-rtx@10de-2484-0"] == ("pass", None) and folders == [str(tmp_path)]
    assert str(tmp_path) not in json.dumps(report) and problems_of(report) == []
    assert skellytracker.certify_plan("quick", test_media_dir=tmp_path)["downloads"] == []


def mediapipe_due(monkeypatch, version: str | None = "1.2.2") -> list:
    """No reviewed row of MediaPipe, and `version` of MediaPipe installed, or no MediaPipe with None. Give the lookups of a row."""
    real, seen = package_certification.importlib.metadata.version, []

    def version_of(name):
        if name != "mediapipe":
            return real(name)
        if version is None:
            raise package_certification.importlib.metadata.PackageNotFoundError(name)
        return version

    monkeypatch.setattr(package_certification.importlib.metadata, "version", version_of)
    monkeypatch.setattr(evidence, "mediapipe_reviewed", lambda *args: seen.append(args) or False)
    return seen


def holistic(present=True, xy=(1.0, 1.0), score=0.5) -> types.SimpleNamespace:
    """One frame of `mediapipe_frames()`: point 1 is missing (NaN, score 0), which is normal; point 2 has `xy` and `score`."""
    return types.SimpleNamespace(present=np.array([present]), score=np.array([[0.9, 0.0, score]]),
                                 xy=np.array([[[50.0, 60.0], [np.nan, np.nan], list(xy)]]))


def fake_mediapipe(monkeypatch, *answer) -> list:
    """Fake `mediapipe_run()`: it gives `answer` (`(result, problem, exit_code)`), or 3 good frames. It gives the time limits."""
    calls = []

    def mediapipe_run(settings, cancel=None, timeout=None):
        calls.append(timeout)
        return answer or ({"live": {"frames": [holistic()] * 3}}, None, 0)

    monkeypatch.setattr(certification, "mediapipe_run", mediapipe_run)
    return calls


def test_the_quick_level_runs_the_mediapipe_smoke_run_last_when_no_row_records_a_pass(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    seen, calls = mediapipe_due(monkeypatch), fake_mediapipe(monkeypatch)
    report = skellytracker.certify("quick")
    assert problems_of(report) == [] and report["checks"][-1]["name"] == "mediapipe:smoke"  # after each EP check
    assert results(report)["mediapipe:smoke"] == ("pass", None) and results(report)["trt-rtx@10de-2484-0"] == ("pass", None)
    assert report["checks"][-1]["module"] == "MediaPipe" and report["checks"][-1]["numbers"]["frames"] == 3 and len(calls) == 1
    assert seen[-1] == ("1.2.2", f"{sys.version_info.major}.{sys.version_info.minor}", "Windows 11")
    assert [item["name"] for item in report["summary"]] == ["TensorRT RTX", "TensorRT RTX", "DirectML", "CPU"]  # no summary item
    assert report["details"]["skipped"] == {} and len(local_results()) == 2  # it stores nothing
    for answer, expected in (((None, "crashed", 5), ("fail", "crashed")), (({"live": {"error": "RuntimeError"}}, None, 0), ("fail", "RuntimeError")),
                             (({"error": "models-missing"}, None, 0), ("not-run", "models-missing")),  # no model file in the cache
                             (({"live": {"frames": [holistic(), holistic(present=False)]}}, None, 0), ("fail", "no-person")),
                             (({"live": {"frames": [holistic(xy=(np.inf, 1.0))]}}, None, 0), ("fail", "not-finite")),
                             (({"live": {"frames": [holistic(xy=(1.0, np.nan))]}}, None, 0), ("fail", "not-finite")),
                             (({"live": {"frames": [holistic(score=np.nan)]}}, None, 0), ("fail", "not-finite")),
                             (({"live": {"frames": [holistic()]}}, "hung-at-exit", 0), ("pass", None))):
        fake_mediapipe(monkeypatch, *answer)
        report = skellytracker.certify("quick")
        assert results(report)["mediapipe:smoke"] == expected and problems_of(report) == []
    assert results(report)["mediapipe:smoke:exit"] == ("record-only", "hung-at-exit")  # its module is `MediaPipe` too
    assert "mediapipe:smoke" not in results(skellytracker.certify("quick", execution_providers=["trt-rtx", "directml"]))
    assert "mediapipe:smoke" not in results(skellytracker.certify("quick", device="gpu:10de:2484:0"))
    calls = fake_mediapipe(monkeypatch)
    monkeypatch.setattr(evidence, "mediapipe_reviewed", lambda *args: True)  # a reviewed row: no check
    report = skellytracker.certify("quick")
    assert "mediapipe:smoke" not in results(report) and report["details"]["skipped"] == {"mediapipe:smoke": "reviewed"} and calls == []


def test_the_mediapipe_smoke_run_is_not_run_with_no_mediapipe_no_test_frames_or_no_time_left(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    calls = fake_mediapipe(monkeypatch)
    mediapipe_due(monkeypatch, version=None)
    report = skellytracker.certify("quick")
    assert results(report)["mediapipe:smoke"] == ("not-run", "models-missing") and calls == [] and problems_of(report) == []
    mediapipe_due(monkeypatch)
    monkeypatch.setattr(package_certification, "MEDIAPIPE_SECONDS", 1000)  # more than the budget
    assert results(skellytracker.certify("quick"))["mediapipe:smoke"] == ("not-run", "over-budget") and calls == []
    monkeypatch.setattr(package_certification, "MEDIAPIPE_SECONDS", 6)
    calls = fake_mediapipe(monkeypatch, None, "timed-out", None)  # the end of the budget stops the child
    assert results(skellytracker.certify("quick"))["mediapipe:smoke"] == ("not-run", "over-budget")
    assert 0 < calls[0] <= package_certification.QUICK_BUDGET_SECONDS
    calls = fake_mediapipe(monkeypatch)
    real = certification.frames_file
    monkeypatch.setattr(certification, "frames_file", lambda found: real({**found, "frames": {**found["frames"], "sha256": "0" * 64}}))
    assert results(skellytracker.certify("quick"))["mediapipe:smoke"] == ("not-run", "test-media-missing") and calls == []


def test_the_plan_counts_the_mediapipe_smoke_run_only_when_it_will_run(quick_host, monkeypatch):
    pc = package_certification
    reviewed_plan, named = skellytracker.certify_plan("quick"), skellytracker.certify_plan("quick", execution_providers=["trt-rtx", "directml"])
    assert reviewed_plan["total"] == named["total"] and reviewed_plan["seconds_estimate"] == named["seconds_estimate"]
    full = skellytracker.certify_plan("full")
    mediapipe_due(monkeypatch)
    plan = skellytracker.certify_plan("quick")
    assert plan["total"] == reviewed_plan["total"] + 1
    assert plan["seconds_estimate"] == min(reviewed_plan["seconds_estimate"] + pc.MEDIAPIPE_SECONDS, pc.QUICK_BUDGET_SECONDS)
    assert skellytracker.certify_plan("quick", execution_providers=["trt-rtx", "directml"])["total"] == named["total"]
    assert skellytracker.certify_plan("full")["total"] == full["total"]  # the level `full` has no MediaPipe smoke run
    monkeypatch.setattr(evidence, "load_evidence", lambda: (reviewed("trt-rtx"), reviewed("directml")))
    assert (skellytracker.certify_plan("quick")["total"], skellytracker.certify_plan("quick")["seconds_estimate"]) == (1, pc.MEDIAPIPE_SECONDS)
    mediapipe_due(monkeypatch, version=None)
    assert skellytracker.certify_plan("quick")["total"] == 0  # no MediaPipe: the check is `not-run`


def test_a_mediapipe_row_is_reviewed_only_for_a_pass_of_the_same_version_python_and_os(monkeypatch):
    row = {"version": "1.2.2", "python": "3.13", "os": "Windows 11", "source": "maintainer", "result": "pass"}
    assert evidence.mediapipe_reviewed("1.2.2", "3.13", "Windows 11") is False  # the file has no row
    monkeypatch.setattr(evidence, "yaml", types.SimpleNamespace(safe_load=lambda text: {"mediapipe": ["not a row", row]}))
    assert evidence.mediapipe_reviewed("1.2.2", "3.13", "Windows 11") is True
    for args in (("1.2.3", "3.13", "Windows 11"), ("1.2.2", "3.12", "Windows 11"), ("1.2.2", "3.13", "Windows 10"), (None, "3.13", "Windows 11"),
                 ("1.2.2", "3.13", None)):
        assert evidence.mediapipe_reviewed(*args) is False
    monkeypatch.setattr(evidence, "yaml", types.SimpleNamespace(safe_load=lambda text: {"mediapipe": [{**row, "result": "fail"}]}))
    assert evidence.mediapipe_reviewed("1.2.2", "3.13", "Windows 11") is False
