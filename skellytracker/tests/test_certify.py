"""Tests of `skellytracker.certify()` and `skellytracker.certify_plan()`: the format `skellycertify.report/1.0.0`.

They use the fakes of `hw_fakes.py` and need no GPU. The cancel tests start real `spawn` children with the targets of
`child_fakes.py`.
"""

import json
import re
import sys
import threading
import time
import types

import pytest

import skellytracker
from skellytracker import certification as package_certification
from skellytracker.core.eps import certification, cli, evidence, installer, recommendation, state, store, verification
from skellytracker.core.eps.records import Verdict
from skellytracker.core.system import host as host_module
from skellytracker.tests import child_fakes, hw_fakes
from skellytracker.tests.hw_fakes import gpu, host
from skellytracker.tests.test_eps_store import ep_store  # noqa: F401 - fixture

COMMIT = "0123456789abcdef0123456789abcdef01234567"
FOUND = {"ran": True, "ok": True, "reason_code": None, "people_cpu": 1, "people_ep": 1, "box_iou_min": 0.99,
         "keypoint_px_max": 2.0, "keypoint_box_fraction_max": 0.004, "keypoint_box_fraction_median": 0.001,
         "keypoint_box_fraction_p99": 0.003, "points_compared": 120, "seconds": 3.2, "warnings": [], "exit_reason_code": None,
         "models": [{"key": "rtmw", "version": "1", "size": "m", "precision": "fp16", "execution_provider": "trt-rtx", "device": None}]}

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
    found += [] if report.get("schema") == "skellycertify.report/1.0.0" else ["schema"]
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
    """A Windows host with an RTX 3070 and the `trt-rtx` pack, no evidence row, a clean commit and a fake pipeline."""
    fake_host = host(gpu())
    for module in (state, recommendation, installer, certification, verification, host_module):
        monkeypatch.setattr(module, "probe_host", lambda: fake_host)
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())
    monkeypatch.setenv(store.CACHE_VARIABLE, str(tmp_path / "cache"))
    monkeypatch.setattr(package_certification, "_commit", lambda: (COMMIT, False))
    monkeypatch.setattr(package_certification, "_pipeline", lambda catalog, pipeline: ({}, "yolox-rtmw-wholebody@skellytracker", None))
    hw_fakes.fake_pack("trt-rtx")
    return ep_store


def fake_probe(monkeypatch, ok=True, code=None):
    calls = []

    def verify(keys, device_key=None, force=False, cancel=None):
        calls.append((keys, device_key))
        return (Verdict(keys[0], "L3", ok, "k", reason=None if ok else "the folder secretdir failed", max_abs_diff=0.001,
                        reason_code=code, exit_code=3 if code == "crashed" else None),)

    monkeypatch.setattr(verification, "verify", verify)
    return calls


def fake_image(monkeypatch, **changes):
    monkeypatch.setattr(certification, "_wide_run", lambda key, settings, progress, device_key=None, **k: {**FOUND, **changes})


def results(report: dict) -> dict:
    return {check["name"]: (check["result"], check["reason"]) for check in report["checks"]}


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
    fake_image(monkeypatch)
    report = skellytracker.certify("quick")  # the default: the uncertified usable EP `trt-rtx`
    assert problems_of(report) == []
    assert results(report) == {"trt-rtx:probe": ("pass", None), "trt-rtx:image": ("pass", None), "trt-rtx": ("pass", None)}
    assert calls == [(["trt-rtx"], "gpu:10de:2484:0")]
    assert report["evidence"] == {"valid": True, "reasons": []} and report["kind"] == "quick"
    assert report["package"] == {"name": "skellytracker", "version": package_certification._package()[0]["version"],
                                 "commit": COMMIT, "tree_modified": False}
    assert report["host"]["os"]["arch"] == "x86_64" and report["host"]["gpus"][0]["id"] == "10de:2484"
    image = next(check for check in report["checks"] if check["name"] == "trt-rtx:image")
    assert image["numbers"]["box_iou_min"] == 0.99 and image["numbers"]["points_compared"] == 120
    assert report["details"]["eps"]["trt-rtx"]["models"][0]["precision"] == "fp16"
    assert report["details"]["versions"]["set_hash"] == evidence.set_hash(certification.load_catalog())
    (path,) = certification.reports_dir().glob("quick-*.json")
    assert json.loads(path.read_text(encoding="utf-8")) == report
    pair = certification.pair_key(certification.load_catalog(), "trt-rtx", gpu(), "Windows")
    assert certification.read_answers() == {pair: "passed"}
    local = store.read_json(store.store_root() / "quick-checks.json")[pair]
    assert local["result"] == "passed" and local["precisions"] == {"rtmw": "fp16"} and local["pipeline"].startswith("yolox")


def test_a_probe_failure_skips_the_image_run_and_records_the_failure(quick_host, monkeypatch):
    fake_probe(monkeypatch, ok=False)
    monkeypatch.setattr(certification, "_wide_run", lambda *a, **k: pytest.fail("no image run after a failed probe"))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    assert problems_of(report) == [] and "secretdir" not in json.dumps(report)
    assert results(report) == {"trt-rtx:probe": ("fail", "probe-l3-failed"), "trt-rtx:image": ("not-run", "probe-not-passed"),
                               "trt-rtx": ("fail", "probe-l3-failed")}
    assert list(certification.read_answers().values()) == ["failed"]
    fake_probe(monkeypatch, ok=False, code="crashed")
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    probe = report["checks"][0]
    assert (probe["result"], probe["reason"], probe["numbers"]["exit_code"]) == ("fail", "crashed", 3)


def test_an_image_failure_fails_the_ep_and_a_hang_at_exit_adds_the_exit_check(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_image(monkeypatch, ok=False, reason_code="keypoints-differ", exit_reason_code="hung-at-exit")
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    assert problems_of(report) == []
    assert results(report) == {"trt-rtx:probe": ("pass", None), "trt-rtx:image": ("fail", "keypoints-differ"),
                               "trt-rtx:image:exit": ("record-only", "hung-at-exit"), "trt-rtx": ("fail", "keypoints-differ")}


def test_a_child_that_crashes_in_the_image_run_is_a_failure_with_its_exit_code(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    monkeypatch.setattr(certification, "_wide_child", child_fakes.crash_in_the_ep_step)  # a real child: os._exit(5)
    report = skellytracker.certify("quick", execution_providers=["trt-rtx"])
    image = report["checks"][1]
    assert (image["result"], image["reason"], image["numbers"]["exit_code"]) == ("fail", "crashed", 5) and problems_of(report) == []


def test_missing_models_and_an_ep_that_cannot_run_are_not_run_and_record_nothing(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    monkeypatch.setattr(package_certification, "_pipeline", lambda catalog, pipeline: ({}, "p@s", "models-missing"))
    report = skellytracker.certify("quick", execution_providers=["trt-rtx", "cuda", "cpu"])
    assert problems_of(report) == [] and report["evidence"]["valid"]  # a part of the EPs is not `partial-run`
    assert results(report) == {
        "trt-rtx:probe": ("pass", None), "trt-rtx:image": ("not-run", "models-missing"), "trt-rtx": ("not-run", "models-missing"),
        "cuda:probe": ("not-run", "ep-not-installed"), "cuda:image": ("not-run", "ep-not-installed"), "cuda": ("not-run", "ep-not-installed"),
        "cpu:probe": ("not-run", "not-gpu-ep"), "cpu:image": ("not-run", "not-gpu-ep"), "cpu": ("not-run", "not-gpu-ep")}
    assert certification.read_answers() == {} and store.read_json(store.store_root() / "quick-checks.json") is None


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
    assert set(results(report).values()) == {("not-run", "cancelled")} and "cancelled" in report["evidence"]["reasons"]
    assert problems_of(report) == [] and store.read_verdicts() == {} and certification.read_answers() == {}


def test_a_cancel_stops_the_image_child(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    monkeypatch.setattr(certification, "_wide_child", child_fakes.hang)
    cancel, set_at = cancel_after(1.0)
    report = skellytracker.certify("quick", cancel=cancel, execution_providers=["trt-rtx"])
    assert time.monotonic() - set_at[0] < 3
    assert results(report) == {"trt-rtx:probe": ("pass", None), "trt-rtx:image": ("not-run", "cancelled"),
                               "trt-rtx": ("not-run", "cancelled")}
    assert report["evidence"]["valid"] is False and certification.read_answers() == {}


def test_each_progress_message_is_the_complete_state_and_a_raising_callback_is_dropped(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    fake_image(monkeypatch)
    messages, times = [], []
    skellytracker.certify("quick", lambda message: (messages.append(json.loads(json.dumps(message))), times.append(time.monotonic())))
    assert [m["state"] for m in messages][0] == "starting" and [m["state"] for m in messages][-2:] == ["cleaning-up", "done"]
    assert messages[0]["checks"] == [{"name": name, "result": None} for name in ("trt-rtx:probe", "trt-rtx:image", "trt-rtx")]
    assert messages[0]["total"] == 3 and messages[0]["done"] == 0 and messages[0]["seconds_left"] == 15 + 60
    running = [m for m in messages if m["step"] == {"name": "trt-rtx:image"}]
    assert running[0]["checks"][:2] == [{"name": "trt-rtx:probe", "result": "pass"}, {"name": "trt-rtx:image", "result": None}]
    assert messages[-1]["done"] == 3 and messages[-1]["seconds_left"] == 0
    assert all(later - earlier >= 0.09 for earlier, later in zip(times, times[1:], strict=False))
    calls = []

    def broken(message):
        calls.append(message)
        raise RuntimeError("the interface is gone")

    assert results(skellytracker.certify("quick", broken))["trt-rtx"] == ("pass", None) and len(calls) == 1


def test_the_plan_names_the_test_image_the_time_and_each_ep_that_will_not_run(quick_host, monkeypatch):
    plan = skellytracker.certify_plan("quick", execution_providers=["trt-rtx", "cuda"])
    settings = certification.load_catalog().data["certification"]
    assert plan["seconds_estimate"] == 15 + settings["seconds"]["trt-rtx"]
    assert plan["downloads"] == [{"name": "sample_recording_a_pose_image.jpg", "bytes": settings["image"]["bytes"]}]
    assert plan["details"] == {"execution_providers": ["trt-rtx", "cuda"], "not_run": {"cuda": "ep-not-installed"}}
    assert plan["system_changes"] == [] and plan["questions"] == [] and plan["kind"] == "quick"
    image = package_certification._image_path(store, settings)
    image.parent.mkdir(parents=True)
    image.write_bytes(b"x")
    assert skellytracker.certify_plan("quick")["downloads"] == []
    row = {"ep": "trt-rtx", "os": "Windows", "gpu": "10de:2484", "set": "s", "source": "maintainer", "result": "pass"}
    monkeypatch.setattr(evidence, "load_evidence", lambda: (row,))
    assert skellytracker.certify_plan("quick")["details"]["execution_providers"] == []  # a reviewed row: nothing by default
    report = skellytracker.certify("quick")
    assert report["checks"] == [] and report["evidence"] == {"valid": False, "reasons": ["no-check"]}
    assert not certification.reports_dir().exists()
    assert skellytracker.certify_plan("full") == {"package": "skellytracker", "kind": "full", "seconds_estimate": 0, "downloads": [],
                                                  "system_changes": [], "questions": []}


def test_the_run_deletes_the_test_image_that_it_downloaded(quick_host, monkeypatch):
    fake_probe(monkeypatch)
    image = package_certification._image_path(store, certification.load_catalog().data["certification"])

    def download(*args, **kwargs):
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"x")
        return FOUND

    monkeypatch.setattr(certification, "_wide_run", download)
    report = skellytracker.certify("quick")
    assert not image.exists() and report["cleanup"] == []


def test_the_full_level_is_not_built(quick_host):
    report = skellytracker.certify("full")
    assert problems_of(report) == [] and report["kind"] == "full"
    assert results(report) == {"full": ("not-run", "not-built")} and report["evidence"] == {"valid": False, "reasons": ["not-built"]}


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
    fake_image(monkeypatch, ok=False, reason_code="box-differs")
    seen = []
    monkeypatch.setattr(certification, "_wide_run", lambda *a, **k: seen.append(dict(store.field_test_opt_ins())) or
                        {**FOUND, "ok": False, "reason_code": "box-differs"})
    report = skellytracker.certify("quick", execution_providers=["directml"])
    assert results(report)["directml"] == ("fail", "box-differs") and "directml" in seen[0]  # opted in during the check
    assert store.field_test_opt_ins() == {} and report["cleanup"] == []
    fake_image(monkeypatch)
    assert results(skellytracker.certify("quick", execution_providers=["directml"]))["directml"] == ("pass", None)
    assert list(store.field_test_opt_ins()) == ["directml"]
    pair = certification.pair_key(certification.load_catalog(), "directml", gpu(), "Windows")
    assert pair.startswith("directml|builtin|") and certification.read_answers()[pair] == "passed"
    fake_image(monkeypatch, ok=False, reason_code="box-differs")
    skellytracker.certify("quick", execution_providers=["directml"])
    assert list(store.field_test_opt_ins()) == ["directml"]  # an opt-in from before the run stays


def test_the_scrub_removes_a_private_name_and_counts_a_public_one(monkeypatch):
    monkeypatch.setattr(package_certification, "_private_words", lambda: ["secretname", "Windows"])
    report = {"host": {"os": {"name": "Windows"}}, "checks": [{"name": "trt-rtx", "reason": None}],
              "details": {"pipeline": "mine@secretname", "where": "C:\\data\\x", "secretname": 1}}
    clean = package_certification._scrub(report)
    assert clean["details"] == {"pipeline": "mine@<private>", "where": "<path>", "<private>": 1, "scrub": {"exempted_terms": 1}}
    assert clean["host"]["os"]["name"] == "Windows"


def test_the_cli_runs_the_quick_level_of_one_ep(quick_host, monkeypatch, capsys):
    fake_probe(monkeypatch)
    fake_image(monkeypatch)
    assert cli.main(["certify", "trt-rtx", "--quick", "--json"]) == 0
    out = capsys.readouterr().out
    assert problems_of(json.loads(out)) == []
    assert cli.main(["certify", "cuda", "--quick"]) == 3  # the pack is not installed
    assert "cuda: not-run (ep-not-installed)" in capsys.readouterr().out
    fake_image(monkeypatch, ok=False, reason_code="box-differs")
    assert cli.main(["certify", "trt-rtx", "--quick"]) == 1
