"""The AMD EPs in their field test (ADR-XSE7): the ROCm packs of `migraphx` on Linux and the Windows ML catalog on Windows.

Fakes only: no GPU, no network, no `windowsml` call and no ONNX Runtime session.
"""

import json
import sys
import threading
import types

import pytest

from skellytracker.core import eps
from skellytracker.core.eps import _download, cli, evidence, registration, store, windows_ml
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system import host as host_module
from skellytracker.tests import hw_fakes
from skellytracker.tests.hw_fakes import GIB, gpu, host
from skellytracker.tests.test_eps_cli import set_host
from skellytracker.tests.test_eps_store import ep_store  # noqa: F401 - fixture

RADEON = gpu("amd", cc=None, vram=16 * GIB, bus="0000:03:00.0", device_id=0x744C, name="Radeon RX 7900 XTX")
RTX = gpu()


def on(monkeypatch, tag: str, fake_host, rocm: str | None = None) -> None:
    monkeypatch.setattr(catalog_module, "platform_tag", lambda: tag)
    monkeypatch.setattr(host_module, "rocm_version", lambda: rocm)
    set_host(monkeypatch, fake_host)


def migraphx_row():
    return next(row for row in eps.status().eps if row.key == "migraphx")


@pytest.mark.parametrize(("rocm", "pack_id", "state", "code"), [
    ("10.2", "migraphx-rocm10.2", "field_test", "field-test"), ("10.1", "migraphx-rocm10.1", "field_test", "field-test"),
    ("10.0", "migraphx-rocm10.0", "field_test", "field-test"), (None, "migraphx-rocm10.2", "unsupported", "rocm-missing"),
    ("6.4", "migraphx-rocm10.2", "unsupported", "rocm-version")])
def test_linux_takes_the_pack_of_the_rocm_release_of_the_host(monkeypatch, ep_store, rocm, pack_id, state, code):  # noqa: F811
    on(monkeypatch, "manylinux_x86_64", host(RADEON, os_name="Linux"), rocm)
    catalog = eps.load_catalog()
    assert catalog.pack("migraphx")["id"] == pack_id and not catalog.windows_ml("migraphx")
    row = migraphx_row()
    assert (row.pack_id, row.state, row.reason_code, row.source, row.usable) == (pack_id, state, code, "amd", False)
    assert "amdgpu" not in {r.key for r in eps.status().eps}  # a Windows ML EP only
    assert eps.recommend("performance").chosen.ep_key == "cpu"


def test_an_opted_in_rocm_pack_is_untested_ort_and_usable_but_never_recommended(monkeypatch, ep_store):  # noqa: F811
    hw_fakes.reviewed_rows_for_each_gpu(monkeypatch)  # the subject is not the check rule of `gate.py`
    from skellytracker.tests.hw_fakes import fake_pack

    on(monkeypatch, "manylinux_x86_64", host(RADEON, os_name="Linux"), "10.2")
    store.opt_in_field_test("migraphx")
    assert migraphx_row().state == "not_installed"
    assert migraphx_row().install_hint == "Run `skellytracker-eps install migraphx --field-test`."
    fake_pack("migraphx")
    row = migraphx_row()
    assert (row.state, row.reason_code, row.usable) == ("untested-ort", "untested-ort", True)  # AMD tested ONNX Runtime 1.29 only
    result = eps.recommend("performance")
    assert (result.hardware_class, result.chosen.ep_key, result.skipped) == ("amd-linux", "cpu", ())


def test_windows_takes_migraphx_and_amdgpu_from_the_windows_ml_catalog(monkeypatch, ep_store):  # noqa: F811
    hw_fakes.reviewed_rows_for_each_gpu(monkeypatch)  # the subject is not the check rule of `gate.py`
    on(monkeypatch, "win_amd64", host(RADEON))
    catalog = eps.load_catalog()
    assert catalog.windows_ml("migraphx") and catalog.pack("migraphx") is None and catalog.device_row("amdgpu")["ep_name"] == "AMDGPUExecutionProvider"
    rows = {row.key: row for row in eps.status().eps}
    assert [(rows[k].state, rows[k].source, rows[k].catalog_status) for k in ("amdgpu", "migraphx")] == [
        ("field_test", "windows-ml", "field-test")] * 2
    store.opt_in_field_test("amdgpu")
    row = next(r for r in eps.status().eps if r.key == "amdgpu")
    assert (row.state, row.install_hint) == ("not_installed", "Run `skellytracker-eps install amdgpu --field-test`.")
    store.write_json(store.store_root() / "windows-ml.json", {"amdgpu": {"version": "1.2.3.0", "was_present": False}})
    row = next(r for r in eps.status().eps if r.key == "amdgpu")
    assert (row.state, row.usable, [d.device_key for d in row.devices]) == ("installed_unverified", True, ["gpu:1002:744c:0"])
    result = eps.recommend("performance")
    assert (result.hardware_class, result.chosen.ep_key) == ("amd-windows", "cpu")
    on(monkeypatch, "win_amd64", host(RTX))
    row = next(r for r in eps.status().eps if r.key == "amdgpu")
    assert (row.state, row.reason_code) == ("unsupported", "no-device")


PUBLISHER = "8wekyb3d8bbwe"
PACKAGES: dict[str, str] = {}  # the fake `Get-AppxPackage`: full name -> family
REMOVED: list[str] = []  # each full name of the fake `Remove-AppxPackage`


class FakeProvider:
    """A provider of the catalog. As in Windows ML, the family and the version are empty until `ensure_ready`."""

    def __init__(self, name, state, version="1.8.65.0"):
        self.name, self.library_path, self.ensured, self._version = name, "C:/fake/ep.dll", 0, version
        self.family = f"Fake.WinML.{name}_{PUBLISHER}"
        self.full_name = f"Fake.WinML.{name}_{version or '1.0.0.0'}_x64__{PUBLISHER}"
        self.ready_state = types.SimpleNamespace(name=state)
        self.version = self.package_family_name = ""
        if state != "NotPresent":
            PACKAGES[self.full_name] = self.family

    def ensure_ready(self):
        self.ensured += 1
        self.ready_state = types.SimpleNamespace(name="Ready")
        PACKAGES[self.full_name] = self.family
        self.version, self.package_family_name = self._version, self.family

    def ensure_ready_async(self, on_complete=None, on_progress=None):
        return FakeOperation(self.ensure_ready, on_complete, on_progress)


class FakeOperation:
    """`windowsml.AsyncOperation`: it runs `work` on a native thread, then calls `on_complete`. `wait()` raises its `OSError`."""

    def __init__(self, work, on_complete, on_progress, values=(50.0, 100.0)):
        self.error, self.cancelled, self.closed = None, False, False

        def run():
            try:
                for value in values:
                    on_progress(value)
                work()
            except OSError as error:
                self.error = error
            on_complete()

        self.thread = threading.Thread(target=run)
        self.thread.start()

    def cancel(self):
        self.cancelled = True

    def wait(self):
        self.thread.join()
        if self.error is not None:
            raise self.error

    def close(self):
        self.thread.join()
        self.closed = True


@pytest.fixture
def fake_windowsml(monkeypatch):
    providers = {}
    PACKAGES.clear()
    PACKAGES["Other.App_1.0.0.0_x64__" + PUBLISHER] = "Other.App_" + PUBLISHER
    REMOVED.clear()
    module = types.ModuleType("windowsml")
    module.EpCatalog = lambda: types.SimpleNamespace(find_all_providers=lambda: list(providers.values()))
    monkeypatch.setitem(sys.modules, "windowsml", module)
    monkeypatch.setattr(windows_ml, "_catalog", None)
    monkeypatch.setattr(windows_ml, "_registered", {})
    monkeypatch.setattr(windows_ml, "installed_packages", lambda: dict(PACKAGES))
    monkeypatch.setattr(windows_ml, "_remove_appx", lambda name: REMOVED.append(name) or PACKAGES.pop(name, None) is not None)
    return providers


def test_windows_ml_install_records_whether_the_package_was_on_the_pc(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    fake_windowsml["m"] = FakeProvider("MIGraphXExecutionProvider", "NotReady")
    fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent", "")
    assert windows_ml.find_eps() == {"MIGraphXExecutionProvider": "NotReady", "AMDGPUExecutionProvider": "NotPresent"}
    assert windows_ml.install("migraphx")["was_present"] is True
    assert windows_ml.install("amdgpu")["was_present"] is False and fake_windowsml["a"].ensured == 1
    assert set(store.windows_ml_installs()) == {"migraphx", "amdgpu"}
    fake_windowsml.clear()
    with pytest.raises(EpUnavailableError, match="offers no EP"):
        windows_ml.install("migraphx")


def test_windows_ml_removes_only_the_package_that_the_install_added(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    """ADR-XSE7: a package that was on the PC stays; a package that the install added goes; an other package is never touched."""
    on(monkeypatch, "win_amd64", host(RADEON))
    present = fake_windowsml["m"] = FakeProvider("MIGraphXExecutionProvider", "NotReady")
    added = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    assert {row.key: row.installed for row in eps.status().eps if row.key in ("amdgpu", "migraphx")} == {"amdgpu": False, "migraphx": False}
    kept = windows_ml.install("migraphx")
    assert (kept["was_present"], kept["packages_installed"], kept["package_family_name"]) == (True, [], present.family)
    assert kept["version"] == "1.8.65.0"  # from the new enumeration, not from the provider object of the call
    record = windows_ml.install("amdgpu")
    assert (record["was_present"], record["packages_installed"]) == (False, [added.full_name])
    rows = {row.key: row for row in eps.status().eps}  # no opt-in: the state hides the install, `installed` gives it
    assert (rows["amdgpu"].state, rows["amdgpu"].installed, rows["migraphx"].installed) == ("field_test", True, True)
    assert rows["directml"].installed is None and rows["cpu"].installed is None  # an EP that needs no pack
    assert windows_ml.install("amdgpu") == record  # a second install keeps the record: `remove` still takes the package away
    assert windows_ml.remove_installed(kept) == [] and present.full_name in PACKAGES
    assert windows_ml.remove_installed(record) == [{"package": added.full_name, "result": "pass", "reason_code": None}]
    assert REMOVED == [added.full_name] and added.full_name not in PACKAGES and present.full_name in PACKAGES
    assert windows_ml.remove_installed(record)[0]["result"] == "pass" and REMOVED == [added.full_name]  # gone: no second call


def test_windows_ml_records_a_removal_that_fails_and_refuses_an_other_family(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    added = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    record = windows_ml.install("amdgpu")
    monkeypatch.setattr(windows_ml, "_remove_appx", lambda name: REMOVED.append(name) or False)  # for example a package in use
    assert windows_ml.remove_installed(record) == [{"package": added.full_name, "result": "fail", "reason_code": "package-not-removed"}]
    assert REMOVED == [added.full_name] and added.full_name in PACKAGES  # one try, no loop
    other = "Other.App_1.0.0.0_x64__" + PUBLISHER
    wrong = {**record, "packages_installed": [other]}  # a name that is not of the family that the catalog reported
    assert windows_ml.remove_installed(wrong) == [{"package": other, "result": "fail", "reason_code": "package-name-mismatch"}]
    assert windows_ml.remove_package("Bad Name", added.family) == "package-name-mismatch"
    assert windows_ml.remove_package(added.full_name, "") == "package-name-mismatch" and REMOVED == [added.full_name]
    assert other in PACKAGES


def test_an_install_that_did_not_end_removes_nothing_and_is_not_installed(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    provider = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")

    def crash():
        PACKAGES[provider.full_name] = provider.family
        raise OSError("the deployment stopped")

    provider.ensure_ready = crash
    store.opt_in_field_test("amdgpu")
    with pytest.raises(EpUnavailableError, match="did not install"):
        windows_ml.install("amdgpu")
    record = store.windows_ml_installs()["amdgpu"]
    assert record["pending"] is True and windows_ml.remove_installed(record) == [  # the catalog gives no family yet
        {"package": None, "result": "fail", "reason_code": "package-unknown"}]
    assert REMOVED == [] and next(r for r in eps.status().eps if r.key == "amdgpu").state == "not_installed"
    provider.package_family_name = provider.family  # Windows finished the deployment: a new enumeration gives the family
    assert windows_ml.remove_installed(record) == [{"package": provider.full_name, "result": "pass", "reason_code": None}]
    assert REMOVED == [provider.full_name] and "Other.App_1.0.0.0_x64__" + PUBLISHER in PACKAGES
    assert windows_ml.remove_installed({**record, "packages_before": None}) == [
        {"package": None, "result": "fail", "reason_code": "package-unknown"}]  # a record with no list from before


def test_a_package_of_a_family_that_was_on_the_pc_is_never_removed(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    """User rule (ADR-XSE7): an update of a present package by `ensure_ready` and a pending record of it remove nothing."""
    on(monkeypatch, "win_amd64", host(RADEON))
    present = fake_windowsml["m"] = FakeProvider("MIGraphXExecutionProvider", "NotReady", "1.8.65.0")
    newer = present.full_name.replace("1.8.65.0", "1.9.0.0")
    present.ensure_ready = lambda: (PACKAGES.pop(present.full_name), PACKAGES.__setitem__(newer, present.family),
                                    setattr(present, "package_family_name", present.family))
    record = windows_ml.install("migraphx")
    assert (record["was_present"], record["packages_installed"]) == (True, [])
    assert windows_ml.remove_installed(record) == [] and newer in PACKAGES and REMOVED == []
    assert windows_ml.remove_installed({**record, "pending": True, "packages_before": []}) == []  # no `package-unknown` row
    hidden = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent", "2.0.0.0")
    PACKAGES[hidden.full_name.replace("2.0.0.0", "1.0.0.0")] = hidden.family  # the catalog said NotPresent, but the family is here
    record = windows_ml.install("amdgpu")
    assert (record["was_present"], record["packages_installed"]) == (True, [])
    assert windows_ml.remove_installed(record) == [] and hidden.full_name in PACKAGES and REMOVED == []


def test_a_record_of_an_ep_that_is_not_a_windows_ml_ep_is_refused(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    other = "Other.App_1.0.0.0_x64__" + PUBLISHER
    record = {"ep_name": "CUDAExecutionProvider", "was_present": False, "package_family_name": "Other.App_" + PUBLISHER,
              "packages_installed": [other]}
    assert windows_ml.remove_installed(record) == [{"package": None, "result": "fail", "reason_code": "record-refused"}]
    assert other in PACKAGES and REMOVED == []


def test_windows_ml_register_never_downloads(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    with pytest.raises(EpUnavailableError, match="not on this PC"):
        registration.ensure_registered("amdgpu")
    assert fake_windowsml["a"].ensured == 0
    registered = []
    fake_ort = types.ModuleType("onnxruntime")
    fake_ort.register_execution_provider_library = lambda name, path: registered.append((name, path))
    fake_ort.get_ep_devices = lambda: [types.SimpleNamespace(ep_name=name) for name, _ in registered]
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_ort)
    fake_windowsml["a"].ready_state = types.SimpleNamespace(name="NotReady")
    assert registration.ensure_registered("amdgpu").ep_name == "AMDGPUExecutionProvider"
    assert registered == [("AMDGPUExecutionProvider", "C:/fake/ep.dll")] and registration.ensure_registered("amdgpu") is not None
    assert len(registered) == 1  # one time for each process


def test_cli_install_of_a_windows_ml_ep_opts_in_and_installs(monkeypatch, ep_store, fake_windowsml, capsys):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    provider = fake_windowsml["m"] = FakeProvider("MIGraphXExecutionProvider", "NotReady")
    assert cli.main(["install", "migraphx"]) == 3  # no opt-in, no --field-test: refused before any change
    assert provider.ensured == 0 and "migraphx" not in store.field_test_opt_ins()
    assert cli.main(["install", "migraphx", "--field-test", "--yes"]) == 0
    assert provider.ensured == 1 and "migraphx" in store.field_test_opt_ins()
    assert "Windows ML package 1.8.65.0, already on this PC" in capsys.readouterr().out
    assert cli.main(["install", "migraphx", "--yes", "--progress", "jsonl"]) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    progress = [event for event in events if event["event"] == "progress"]
    assert progress[0]["fraction"] is None and progress[-1]["fraction"] == 1.0  # Windows ML gives a fraction and no bytes
    assert {event["key"]: event["result"] for event in events if event["event"] == "done"} == {"migraphx": "ok"}


def test_eps_install_of_a_windows_ml_ep_reports_the_fraction_and_cancels_before_the_start(monkeypatch, ep_store,  # noqa: F811
                                                                                          fake_windowsml):
    on(monkeypatch, "win_amd64", host(RADEON))
    store.opt_in_field_test("amdgpu")
    provider = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    plan = eps.plan_install(["amdgpu"])
    assert (plan.windows_ml_keys, plan.packs) == (("amdgpu",), ())
    cancel = threading.Event()
    cancel.set()
    assert eps.install(plan, cancel=cancel) == eps.InstallResult(cancelled=("amdgpu",))
    with pytest.raises(_download.CancelledError):
        windows_ml.install("amdgpu", cancel=cancel)
    assert provider.ensured == 0 and store.windows_ml_installs() == {}  # no start, no record
    events = []
    assert eps.install(plan, progress=events.append) == eps.InstallResult(ok=("amdgpu",))
    assert provider.ensured == 1 and store.windows_ml_installs()["amdgpu"]["packages_installed"] == [provider.full_name]
    assert {event.phase for event in events} == {"download"} and {(event.bytes_done, event.bytes_total) for event in events} == {(0, 0)}
    assert events[0].fraction is None and events[-1].fraction == 1.0


def test_a_cancel_during_a_windows_ml_install_asks_windows_ml_to_stop(monkeypatch, ep_store, fake_windowsml):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RADEON))
    provider = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    operations = []

    def stop_on_cancel(on_complete=None, on_progress=None):
        gate = threading.Event()

        def work():
            PACKAGES[provider.full_name] = provider.family  # a part of the deployment is on the PC
            gate.wait(10)
            raise OSError("the operation was cancelled")

        operation = FakeOperation(work, on_complete, on_progress, values=(25.0,))
        operation.cancel = lambda: (setattr(operation, "cancelled", True), gate.set())
        operations.append(operation)
        return operation

    provider.ensure_ready_async = stop_on_cancel
    cancel = threading.Event()

    def progress(event):
        if event.fraction == 0.25:
            cancel.set()

    plan = eps.plan_install(["amdgpu"], field_test=True)
    assert eps.install(plan, progress=progress, cancel=cancel) == eps.InstallResult(cancelled=("amdgpu",))
    assert operations[0].cancelled and operations[0].closed
    assert store.windows_ml_installs()["amdgpu"]["pending"] is True  # the trace for the removal
    provider.package_family_name = provider.family  # Windows ended the deployment: a new enumeration gives the family
    assert eps.remove(execution_provider="amdgpu") == eps.RemoveResult(removed=(provider.full_name,))
    assert REMOVED == [provider.full_name] and store.windows_ml_installs() == {}


def test_cli_remove_of_a_windows_ml_ep_removes_only_the_package_that_the_install_added(monkeypatch, ep_store,  # noqa: F811
                                                                                       fake_windowsml, capsys):
    on(monkeypatch, "win_amd64", host(RADEON))
    present = fake_windowsml["m"] = FakeProvider("MIGraphXExecutionProvider", "NotReady")
    added = fake_windowsml["a"] = FakeProvider("AMDGPUExecutionProvider", "NotPresent")
    windows_ml.install("migraphx")
    windows_ml.install("amdgpu")
    monkeypatch.setattr(windows_ml, "_remove_appx", lambda name: REMOVED.append(name) or False)  # for example a package in use
    assert cli.main(["remove", "--windows-ml", "amdgpu"]) == 1
    assert f"amdgpu: not removed {added.full_name} (package-not-removed)" in capsys.readouterr().err
    assert "amdgpu" in store.windows_ml_installs()  # the record stays for a later try
    monkeypatch.setattr(windows_ml, "_remove_appx", lambda name: REMOVED.append(name) or PACKAGES.pop(name, None) is not None)
    assert cli.main(["remove", "--windows-ml", "amdgpu"]) == 0
    assert cli.main(["remove", "--windows-ml", "migraphx"]) == 0
    out = capsys.readouterr().out
    assert f"amdgpu: removed {added.full_name}" in out and "migraphx: the Windows ML package was on this PC before" in out
    assert REMOVED == [added.full_name] * 2 and present.full_name in PACKAGES and "Other.App_1.0.0.0_x64__" + PUBLISHER in PACKAGES
    assert store.windows_ml_installs() == {}
    assert cli.main(["remove", "--windows-ml", "amdgpu"]) == 1
    assert "amdgpu: not removed (no-record)" in capsys.readouterr().err
    other = "Other.App_1.0.0.0_x64__" + PUBLISHER
    store.write_json(store.store_root() / "windows-ml.json", {"amdgpu": {
        "ep_name": "CUDAExecutionProvider", "was_present": False, "packages_installed": [other]}})
    assert eps.remove(execution_provider="amdgpu") == eps.RemoveResult(failed=((None, "record-refused"),))
    assert other in PACKAGES and "amdgpu" in store.windows_ml_installs()


def test_doctor_checks_each_index_also_an_index_of_dependency_wheels_only(monkeypatch, ep_store, capsys):  # noqa: F811
    on(monkeypatch, "win_amd64", host(RTX))
    pages = []

    def opener(*args):
        def open_page(url, timeout):
            pages.append(url)
            raise OSError("offline")
        return types.SimpleNamespace(open=open_page)

    monkeypatch.setattr(cli.urllib.request, "build_opener", opener)
    assert cli.main(["doctor"]) == 1
    assert pages[-2:] == ["https://stable.repo.amd.com/rocm/onnxruntime/whl-next/onnxruntime-ep-migraphx/",
                          "https://stable.repo.amd.com/rocm/migraphx/whl-next/migraphx-libs/"]
    assert "Index amd-migraphx: not reachable" in capsys.readouterr().out


def test_a_field_test_pack_is_not_in_the_set_hash():
    catalog = eps.load_catalog()
    current = evidence.set_hash(catalog)
    data = {**catalog.data, "eps": {**catalog.data["eps"]}}
    migraphx = data["eps"]["migraphx"]
    ready = {**migraphx, "packs": [{**pack, "status": "ready"} for pack in migraphx["packs"]]}
    assert evidence.set_hash(catalog_module.EpCatalog(data, catalog.lock, catalog.revision)) == current
    data["eps"]["migraphx"] = ready
    assert evidence.set_hash(catalog_module.EpCatalog(data, catalog.lock, catalog.revision)) != current


def test_rocm_version_reads_major_and_minor(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    (tmp_path / "version").write_text("10.2.0-15\n", encoding="utf-8")
    (tmp_path / "bad").write_text("unknown\n", encoding="utf-8")
    host_module.rocm_version.cache_clear()
    assert host_module.rocm_version(str(tmp_path / "version")) == "10.2"
    assert host_module.rocm_version(str(tmp_path / "bad")) is None
    assert host_module.rocm_version(str(tmp_path / "missing")) is None
    monkeypatch.setattr(sys, "platform", "win32")
    host_module.rocm_version.cache_clear()
    assert host_module.rocm_version(str(tmp_path / "version")) is None
    host_module.rocm_version.cache_clear()


def test_the_rocm_10_0_pack_loads_the_ort_core_first(tmp_path, monkeypatch):
    capi = tmp_path / "onnxruntime" / "capi"
    capi.mkdir(parents=True)
    (capi / "libonnxruntime.so.1.30.0").write_bytes(b"")
    fake_ort = types.ModuleType("onnxruntime")
    fake_ort.__file__ = str(tmp_path / "onnxruntime" / "__init__.py")
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_ort)
    loaded = []
    monkeypatch.setattr(registration.ctypes, "CDLL", lambda path, mode=0: loaded.append(path.replace("\\", "/").rsplit("/", 2)[-2:]))
    monkeypatch.setattr(registration.ctypes, "RTLD_GLOBAL", 256, raising=False)
    manifest = {"preload": ["migraphx_libs/libmigraphx_c.so.3"], "preload_ort_core": True}
    registration.prepare_libraries(tmp_path / "pack", manifest, platform="linux")
    assert loaded == [["capi", "libonnxruntime.so.1.30.0"], ["migraphx_libs", "libmigraphx_c.so.3"]]
    loaded.clear()
    registration.prepare_libraries(tmp_path / "pack", {"preload": []}, platform="linux")  # ROCm 10.1 and 10.2: RUNPATH only
    assert loaded == []
