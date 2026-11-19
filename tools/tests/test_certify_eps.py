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


@pytest.fixture(autouse=True)
def no_windows_ml_catalog(monkeypatch):
    monkeypatch.setattr(cp, "windows_ml_offer", list)  # the consent text calls no hardware probe and no catalog


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


def fake_eps(monkeypatch, rows, vendor="nvidia", probe_result="pass", gpus=None, verify_ok=None, catalog_eps=None,
             probe_reason="probe-l3-failed"):
    calls = {"install": [], "certify": [], "verify": [], "fallback": []}
    monkeypatch.setattr(ce, "windows_ml_eps", lambda catalog, host: dict(catalog_eps or {}))
    monkeypatch.setattr(ce, "run_fallback", lambda work, *args: calls["fallback"].append(args) or {
        "result": "pass", "reason_code": None, "ort_version": "1.29.0", "ort_fallback": True, "certifies_version_set": False})
    gpus = gpus or ((RADEON,) if vendor == "amd" else (RTX,))
    status = SimpleNamespace(eps=rows, host=host(*gpus),
                             performance=SimpleNamespace(hardware_class="amd-windows" if vendor == "amd" else "nvidia-cc80-r580"))
    monkeypatch.setattr(eps, "status", lambda: status)
    monkeypatch.setattr(eps, "plan_install", lambda keys: SimpleNamespace(
        packs=[SimpleNamespace(pack_id=f"{keys[0]}-pack", version="1.0", download_bytes=5)]))

    def install(plan, from_dir=None):
        calls["install"].append(from_dir)
        return SimpleNamespace(ok=(plan.packs[0].pack_id.removesuffix("-pack"),), failed=())

    def certify(key, out=None):
        calls["certify"].append(out)
        failed = probe_result != "pass"
        report = {"result": probe_result, "reason_code": probe_reason if failed else None,
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
    assert results == {"trt-rtx": ("pass", None), "cuda": ("not-run", "cc"), "coreml": ("not-run", "os"), "amdgpu": ("not-run", "os"),
                       "migraphx": ("not-run", "os"), "directml": ("not-run", "os"),
                       "cpu": ("pass", None)}  # `status()` gave no `directml` row: an other platform
    assert found["result"] == "pass" and calls["install"] == [Path("wheels")] and calls["certify"] == [work / "certify-trt-rtx.json"]
    trt = found["details"]["eps"]["trt-rtx"]
    assert trt["probe"]["max_abs_diff"] == 0.004 and trt["wheels"] == [{"filename": "a.whl", "sha256": "ab" * 32}]
    assert trt["gpu"]["id"] == "10de:2484" and trt["install"] == "ok"


def test_section_3_fails_on_a_failed_probe(work, monkeypatch):
    fake_eps(monkeypatch, NVIDIA_ROWS, probe_result="fail")
    found = ce.section_eps(work)
    assert (found["result"], found["reason_code"]) == ("fail", "probe-l3-failed")


def test_section_3_on_an_amd_host_tests_each_offered_windows_ml_ep(work, monkeypatch):
    """ADR-XSE7: an EP that the catalog does not offer is not run."""
    rows = [row("trt-rtx", "unsupported", "vendor"), row("cuda", "unsupported", "vendor"),
            row("migraphx", "installed_unverified", devices=(device("gpu:1002:73bf:0"),)), row("cpu", "builtin")]
    catalog_eps = {"amdgpu": {"result": "not-run", "reason_code": "not-offered"},
                   "migraphx": {"catalog_state": "NotReady", "package_version": "1.8.65.0", "was_present": True}}
    calls = fake_eps(monkeypatch, rows, vendor="amd", catalog_eps=catalog_eps)
    found = ce.section_eps(work)
    results = {c["name"]: (c["result"], c["reason_code"]) for c in found["checks"]}
    assert results["amdgpu"] == ("not-run", "not-offered") and results["migraphx@gpu:1002:73bf:0"] == ("pass", None)
    assert found["details"]["hardware_class"] == "amd-windows" and found["result"] == "pass" and "amd-eps" not in results
    migraphx = found["details"]["eps"]["migraphx@gpu:1002:73bf:0"]
    assert (migraphx["was_present"], migraphx["counts"], migraphx["ort_version"]) == (True, True, ce.ort_version())
    assert ("migraphx", "gpu:1002:73bf:0") in calls["verify"] and calls["fallback"] == []
    assert {"key": "migraphx", "device_key": "gpu:1002:73bf:0", "counts": True} in found["details"]["pipeline_targets"]


def test_section_3_runs_migraphx_on_the_second_environment_only_after_a_load_failure(work, monkeypatch):
    """ADR-XSE7: a failure of the numbers does not start the second environment; a failure of the load does."""
    rows = [row("migraphx", "untested-ort", pack_id="migraphx-rocm10.2"), row("cpu", "builtin")]
    calls = fake_eps(monkeypatch, rows, vendor="amd", probe_result="fail")
    assert {c["name"] for c in ce.section_eps(work)["checks"]} >= {"migraphx"} and calls["fallback"] == []
    calls = fake_eps(monkeypatch, rows, vendor="amd", probe_result="fail", probe_reason="probe-l2-failed")
    found = ce.section_eps(work)
    results = {c["name"]: (c["result"], c["reason_code"]) for c in found["checks"]}
    assert results["migraphx"] == ("fail", "probe-l2-failed") and results["migraphx@ort-1.29.0"] == ("pass", None)
    assert calls["fallback"] == [("eps", "migraphx")] and found["result"] == "fail"  # a pass on 1.29 certifies nothing
    assert found["details"]["eps"]["migraphx@ort-1.29.0"]["certifies_version_set"] is False
    assert {"key": "migraphx", "device_key": None, "counts": True, "ort_fallback": True} in found["details"]["pipeline_targets"]
    assert found["details"]["eps"]["migraphx"]["ort_version"] == ce.ort_version()


def test_needs_fallback_only_for_a_load_failure_of_a_fallback_ep():
    catalog = eps.load_catalog()
    assert ce.needs_fallback(catalog, "migraphx", {"result": "fail", "reason_code": "probe-l2-failed"})
    assert ce.needs_fallback(catalog, "migraphx", {"result": "fail", "reason_code": "EpUnavailableError"})
    assert not ce.needs_fallback(catalog, "migraphx", {"result": "fail", "reason_code": "probe-l3-failed"})
    assert not ce.needs_fallback(catalog, "migraphx", {"result": "fail", "reason_code": "install-offline"})
    assert not ce.needs_fallback(catalog, "migraphx", {"result": "pass", "reason_code": None})
    assert not ce.needs_fallback(catalog, "trt-rtx", {"result": "fail", "reason_code": "probe-l2-failed"})


def test_windows_ml_eps_installs_each_offered_package(monkeypatch):
    from skellytracker.core.eps import windows_ml
    from skellytracker.core.eps import catalog as catalog_module

    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "win_amd64")
    installed = []
    monkeypatch.setattr(windows_ml, "find_eps", lambda: {"MIGraphXExecutionProvider": "NotReady"})
    monkeypatch.setattr(windows_ml, "install", lambda key: installed.append(key) or {
        "version": "1.8.65.0", "was_present": key == "migraphx", "package_family_name": "F_8wekyb3d8bbwe",
        "packages_installed": [] if key == "migraphx" else ["F_1.0.0.0_x64__8wekyb3d8bbwe"]})
    found = ce.windows_ml_eps(eps.load_catalog(), host(RADEON))
    assert found == {"amdgpu": {"result": "not-run", "reason_code": "not-offered"},
                     "migraphx": {"catalog_state": "NotReady", "package_version": "1.8.65.0", "was_present": True,
                                  "package_family_name": "F_8wekyb3d8bbwe", "packages_installed": []}}
    assert installed == ["migraphx"]
    monkeypatch.setattr(windows_ml, "find_eps", lambda: {"AMDGPUExecutionProvider": "NotPresent"})
    found = ce.windows_ml_eps(eps.load_catalog(), host(RADEON))["amdgpu"]
    assert (found["was_present"], found["packages_installed"]) == (False, ["F_1.0.0.0_x64__8wekyb3d8bbwe"])
    assert installed == ["migraphx", "amdgpu"]  # ADR-XSE7: the suite installs a missing package, and the frame removes it
    assert ce.windows_ml_eps(eps.load_catalog(), host(RTX)) == {}  # no AMD GPU: no catalog call


def test_the_second_environment_pins_the_fallback_ort_and_installs_the_checkout(tmp_path, monkeypatch):
    """ADR-XSE7: `uv export` of the lock with the one ONNX Runtime pin changed; no file of the checkout changes."""
    commands = []

    def run(args, **kwargs):
        commands.append(args[1:])
        out = ("numpy==2.3.1 \\\n    --hash=sha256:" + "1" * 64 + "\n"
               "onnxruntime==1.30.0 ; sys_platform == 'linux' \\\n    --hash=sha256:" + "2" * 64 + " \\\n    --hash=sha256:" + "3" * 64 + "\n"
               "    # via skellytracker\n"
               "onnxruntime-windowsml==1.30.0.1 ; sys_platform == 'win32' \\\n    --hash=sha256:" + "4" * 64 + "\n")
        return SimpleNamespace(returncode=0, stdout=out if args[1] == "export" else "")

    monkeypatch.setattr(ce.subprocess, "run", run)
    monkeypatch.setenv("UV", "uv-fake")
    fallback = eps.load_catalog().data["certification"]["ort_fallback"]
    python = ce.build_fallback_env(tmp_path, fallback)
    assert python.parent.parent == tmp_path / "ort-1.29.0" and [c[0] for c in commands] == ["export", "venv", "pip", "pip"]
    pinned = (tmp_path / "fallback-requirements.txt").read_text(encoding="utf-8")
    assert (f"\nonnxruntime==1.29.0 ; sys_platform == 'linux' \\\n    --hash=sha256:{fallback['sha256']}\n    # via skellytracker\n"
            in pinned and "onnxruntime-windowsml==1.30.0.1" in pinned and "1.30.0 ;" not in pinned)
    assert "2" * 64 not in pinned and "3" * 64 not in pinned and "1" * 64 in pinned and "4" * 64 in pinned
    assert "--no-hashes" not in commands[0] and "--frozen" in commands[0] and "--require-hashes" in commands[2]
    assert commands[-1][-2:] == ["-e", str(ce.REPO_ROOT)] and "--no-deps" in commands[-1]  # uv refuses `-e` with --require-hashes
    build = commands[-1][commands[-1].index("--build-constraints") + 1]
    assert Path(build).read_text(encoding="utf-8") == f"flit-core==3.12.0 --hash=sha256:{fallback['build_backend']['sha256']}\n"
    monkeypatch.delenv("UV")
    monkeypatch.setattr(ce.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="no-uv"):
        ce.build_fallback_env(tmp_path / "other", fallback)


@pytest.mark.parametrize(("stage", "error", "expected"), [
    ("build", ce.subprocess.TimeoutExpired("uv", 900), ("not-run", "build-timed-out")),
    ("build", OSError("disk full"), ("not-run", "build-failed")),
    ("run", ce.subprocess.TimeoutExpired("python", 1800), ("fail", "timed-out")),
    ("run", OSError("no python"), ("fail", "not-started"))])
def test_a_timeout_or_an_os_error_of_the_second_environment_is_a_code_of_its_one_check(tmp_path, monkeypatch, stage, error, expected):
    def raise_error(*args, **kwargs):
        raise error

    monkeypatch.setattr(ce, "build_fallback_env", raise_error if stage == "build" else lambda work, fallback: tmp_path / "python")
    monkeypatch.setattr(ce.subprocess, "run", raise_error)
    assert ce.run_fallback(tmp_path, "eps", "migraphx") == {"result": expected[0], "reason_code": expected[1], "ort_version": "1.29.0"}


def test_core_mismatch_accepts_the_fallback_ort_only_in_the_second_environment(monkeypatch):
    from skellytracker.core.eps import installer

    catalog = eps.load_catalog()
    monkeypatch.setattr(installer, "installed_ort", lambda: ("onnxruntime", "1.29.0"))
    monkeypatch.delenv(store.FALLBACK_VARIABLE, raising=False)
    assert "1.29.0" in installer.core_mismatch(catalog)
    monkeypatch.setenv(store.FALLBACK_VARIABLE, "1.29.0")
    assert installer.core_mismatch(catalog) is None
    monkeypatch.setattr(installer, "installed_ort", lambda: ("onnxruntime", "1.28.0"))
    monkeypatch.setenv(store.FALLBACK_VARIABLE, "1.28.0")  # only the version of the catalog
    assert installer.core_mismatch(catalog) is not None


def test_section_4_runs_a_target_of_the_second_environment_in_a_child(work, monkeypatch):
    (work / "section-3.json").write_text(json.dumps({"details": {"pipeline_targets": [
        {"key": "migraphx", "device_key": None, "counts": True, "ort_fallback": True}]}}))
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: SimpleNamespace(available=True))
    monkeypatch.setattr(ce, "fetch_models", lambda models, root, work: [])
    monkeypatch.setattr(ce, "test_image", lambda settings: np.zeros((8, 8, 3), np.uint8))
    monkeypatch.setattr(ce, "time_run", lambda pipeline, key, cameras, frame, device: {"median_ms": 1.0})
    agreement = {"name": "agreement-migraphx@ort-1.29.0", "result": "pass", "reason_code": None}
    calls = []
    monkeypatch.setattr(ce, "run_fallback", lambda work, *args: calls.append(args) or {
        "result": "pass", "reason_code": None, "ort_version": "1.29.0", "found": {"ort_version": "1.29.0"}, "checks": [agreement]})
    found = ce.section_pipeline(work)
    assert calls == [("pipeline", "migraphx")] and agreement in found["checks"] and found["result"] == "pass"
    assert found["details"]["eps"]["migraphx@ort-1.29.0"] == {"ort_version": "1.29.0"}
    assert found["details"]["eps"]["cpu"]["ort_version"] == ce.ort_version()


def test_the_consent_lists_the_fallback_wheel_when_migraphx_can_run(monkeypatch):
    from skellytracker.core.eps import catalog as catalog_module
    from skellytracker.core.eps import recommendation
    from skellytracker.core.system import host as host_module

    monkeypatch.setattr(catalog_module, "platform_tag", lambda: "manylinux_x86_64")
    monkeypatch.setattr(host_module, "rocm_version", lambda: "10.2")
    monkeypatch.setattr(host_module, "probe_host", lambda: host(RADEON, os_name="Linux"))
    monkeypatch.setattr(recommendation, "ep_gpus", lambda catalog, key, h: [("gpu:1002:73bf:0", RADEON)] if key == "migraphx" else [])
    listed = dict(ce.eps_downloads({}))
    assert listed["migraphx_libs-2.19.0+rocm10.2.0-py3-none-manylinux_2_28_x86_64.whl"] == 83770284
    assert listed["onnxruntime 1.29.0 for a second environment, only when migraphx does not load"] == 23136817


def test_the_consent_names_the_windows_ml_packages_on_windows(tmp_path):
    offer = lambda: ["AMDGPUExecutionProvider"]  # noqa: E731
    text = cp.plan_text((), {3}, tmp_path / "r.md", os_platform="win32", windows_eps=offer)
    assert ("Windows downloads and installs the Windows ML package of the AMD execution provider AMDGPUExecutionProvider" in text
            and "The suite removes that package at the end." in text and "Apart from that" in text)
    assert "Windows ML" not in cp.plan_text((), {3}, tmp_path / "r.md", os_platform="linux", windows_eps=offer)
    assert "Windows ML" not in cp.plan_text((), {1}, tmp_path / "r.md", os_platform="win32", windows_eps=offer)
    assert "installs no system software and needs no" in cp.plan_text((), {3}, tmp_path / "r.md", os_platform="win32",
                                                                         windows_eps=list)


def test_the_frame_removes_the_package_of_section_3_also_after_a_crash(tmp_path, monkeypatch):
    """ADR-XSE7: the child records the install, then crashes; the frame removes only the package that the install added."""
    from skellytracker.core.eps import windows_ml

    added, kept = "AMD.WinML.EP_1.8.65.0_x64__8wekyb3d8bbwe", "Other.App_1.0.0.0_x64__8wekyb3d8bbwe"
    packages = {added: "AMD.WinML.EP_8wekyb3d8bbwe", kept: "Other.App_8wekyb3d8bbwe"}
    removed = []
    monkeypatch.setattr(windows_ml, "installed_packages", lambda: dict(packages))
    monkeypatch.setattr(windows_ml, "_catalog_family", lambda ep_name: None)  # no Windows ML catalog: the family of the record
    monkeypatch.setattr(windows_ml, "_remove_appx", lambda name: removed.append(name) or packages.pop(name) is not None)
    monkeypatch.setattr(cp, "windows_ml_offer", lambda: ["AMDGPUExecutionProvider"])
    record = {"amdgpu": {"ep_name": "AMDGPUExecutionProvider", "version": "1.8.65.0", "package_family_name": "AMD.WinML.EP_8wekyb3d8bbwe",
                         "was_present": False, "packages_installed": [added]}}
    crash = ("import json, os, sys; s = os.environ['SKELLYTRACKER_EP_STORE']; os.makedirs(s);"
             f" open(s + '/windows-ml.json', 'w').write({json.dumps(json.dumps(record))}); sys.exit(3)")
    out, work = tmp_path / "r.md", tmp_path / "w"
    fakes = (cp.Section(3, "fake 3", 1, 60, cp.not_built),)
    cp.run_suite(fakes, {3}, out, yes=True, work=work, interactive=False, command=lambda section, _work: [sys.executable, "-c", crash])
    section = cp.report_data(out.read_text(encoding="utf-8"))["sections"][0]
    assert removed == [added] and kept in packages and not work.exists()
    assert section["reason_code"] == "crashed" and section["checks"] == [cp.check(f"remove-{added}", "pass")]


def test_a_package_that_stays_fails_section_3(tmp_path):
    results = [{"number": 3, "result": "pass", "reason_code": None, "checks": []}]
    cp.add_cleanup(results, [{"key": "amdgpu", "package": "P_1.0.0.0_x64__8wekyb3d8bbwe", "result": "fail",
                              "reason_code": "package-not-removed"}])
    assert results[0]["result"] == "fail" and results[0]["reason_code"] == "package-not-removed"
    assert results[0]["checks"][0]["name"] == "remove-P_1.0.0.0_x64__8wekyb3d8bbwe"


DML_ROWS = [row("trt-rtx", "unsupported", "vendor"), row("cuda", "unsupported", "vendor"),
            row("directml", "builtin", devices=(device("gpu:10de:2484:0"), device("gpu:8086:a780:0"))), row("cpu", "builtin")]


def test_section_3_opts_in_and_records_directml_on_each_gpu_as_record_only_off_amd(work, monkeypatch):
    """ADR-Z5X7 and ADR-Y14H item 11: the probe runs on each GPU; on a GPU that is not AMD it does not count, also when it fails."""
    calls = fake_eps(monkeypatch, DML_ROWS, gpus=(RTX, INTEL), verify_ok={"gpu:8086:a780:0": False})
    found = ce.section_eps(work)
    assert set(store.field_test_opt_ins()) == {"amdgpu", "migraphx", "directml"} and str(store.store_root()).startswith(str(work))
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
    monkeypatch.setattr(ce, "fetch_models", lambda models, root, work: [{"path": "m.onnx", "state": "failed"}])
    found = ce.section_pipeline(work)
    assert (found["result"], found["reason_code"], found["details"]["models"]) == ("not-run", "models-missing",
                                                                                 [{"path": "m.onnx", "state": "failed"}])


def test_section_4_reads_the_section_3_result_and_runs_each_passed_gpu_ep(work, monkeypatch):
    (work / "section-3.json").write_text(json.dumps({"details": {"pipeline_targets": [
        {"key": "trt-rtx", "device_key": None, "counts": True}, {"key": "directml", "device_key": "gpu:8086:a780:0", "counts": False}]}}))
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: SimpleNamespace(available=True))
    monkeypatch.setattr(ce, "fetch_models", lambda models, root, work: [])
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
    assert cp.remove_listed(work, root) == []
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
    assert cp.remove_listed(work, root) == []
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
