"""The start check, `status()` and the CLI `skellytracker-eps` with each exit code."""

import importlib.metadata
import json
import os
import subprocess
import sys

import pytest

from skellytracker.core import eps, errors
from skellytracker.core.eps import cli, installer, recommendation, state
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps.records import InstallResult
from skellytracker.core.errors import EpRequestError, EpUnavailableError, SessionCreationError, VRAMExhaustionError
from skellytracker.tests import hw_fakes
from skellytracker.tests.hw_fakes import GIB, gpu, host
from skellytracker.tests.test_eps_store import ep_store, fake_pack, server  # noqa: F401 - fixtures

RTX = gpu()
OLD = gpu(cc="6.1", vram=11 * GIB, bus="0000:03:00.0", device_id=0x1B06, name="GTX 1080 Ti")


def set_host(monkeypatch, fake_host):
    for module in (state, recommendation, installer, cli.state):
        monkeypatch.setattr(module, "probe_host", lambda: fake_host)


@pytest.fixture
def rtx_host(monkeypatch, ep_store):  # noqa: F811
    set_host(monkeypatch, host(RTX, OLD))


def test_start_check(rtx_host):
    with pytest.raises(EpUnavailableError, match="skellytracker-eps install cuda"):
        eps.check_start("cuda")
    hw_fakes.fake_pack("cuda")
    (device,) = eps.check_start("cuda", {"prefer_nhwc": "1"})  # no trial session yet: ready, with a warning at the build
    assert device.device_key == "gpu:10de:2484:0" and eps.check_start("cuda", device="gpu:10de:2484:0") == (device,)
    assert eps.check_start("cpu") == ()
    for key, options in (("cuda", {"device_id": "0"}), ("cuda", {"use_tf32": "2"}), ("openvino", None), ("gpu", None)):
        with pytest.raises(EpRequestError):
            eps.check_start(key, options)
    for key, device_key in (("cuda", "gpu:10de:1b06:0"), ("trt-rtx", None), ("cpu", "gpu:10de:2484:0"), ("coreml", None)):
        with pytest.raises(EpUnavailableError):
            eps.check_start(key, device=device_key)


TURING = gpu(cc="7.5", vram=6 * GIB, device_id=0x2184, name="GTX 1660")  # passes the `cuda` floors, not the `trt-rtx` floors
INTEL = gpu(vendor="intel", cc=None, device_id=0x9A49, name="Intel Iris Xe")
OLD_DRIVER = gpu(driver="566.36")  # an RTX 3070 with a driver before R580


@pytest.mark.parametrize(("gpus", "installed", "saved", "expected"), [
    ((RTX, OLD), (), "trt", "trt-rtx"), ((RTX, OLD), (), "cuda", "trt-rtx"),  # supported, not installed
    ((RTX, OLD), ("trt-rtx", "cuda"), "trt", "trt-rtx"), ((RTX, OLD), ("cuda",), "cuda", "trt-rtx"),
    ((TURING,), (), "trt", "cuda"), ((TURING,), (), "cuda", "cuda"),
    ((INTEL,), (), "trt", None), ((INTEL,), (), "cuda", None), ((), (), "cuda", None),
    ((OLD_DRIVER,), (), "trt", None), ((OLD_DRIVER,), (), "cuda", None),  # `status().performance` offers the driver update
    ((RTX, OLD), ("trt-rtx", "cuda"), "directml", None), ((RTX, OLD), (), "cpu", "cpu"),
    ((RTX, OLD), (), "coreml", None),  # this platform has no `coreml`
    ((RTX, OLD), (), "trt-rtx", "trt-rtx"), ((TURING,), (), "trt-rtx", None),  # a key of this release has no successor
    ((RTX, OLD), ("trt-rtx", "cuda"), "tensorrt", None), ((RTX, OLD), ("trt-rtx", "cuda"), "openvino", None),
    ((RTX, OLD), ("trt-rtx", "cuda"), "", None), ((RTX, OLD), ("trt-rtx", "cuda"), "CUDA", None),
])
def test_suggest_execution_provider_for_a_key_of_an_older_release(monkeypatch, ep_store, gpus, installed, saved,  # noqa: F811
                                                                   expected):
    set_host(monkeypatch, host(*gpus))
    for key in installed:
        hw_fakes.fake_pack(key)
    assert eps.suggest_execution_provider(saved) == expected


def test_a_suggested_ep_that_is_not_installed_gives_the_install_hint(rtx_host):
    assert eps.suggest_execution_provider("cuda") == "trt-rtx"
    (row,) = [row for row in eps.status().eps if row.key == "trt-rtx"]
    assert not row.usable and row.install_hint == "Run `skellytracker-eps install trt-rtx`."
    with pytest.raises(EpUnavailableError) as raised:
        eps.check_start("trt-rtx")
    assert raised.value.hint == row.install_hint


def test_the_legacy_keys_do_not_change_a_request(rtx_host):
    hw_fakes.fake_pack("trt-rtx")
    hw_fakes.fake_pack("cuda")
    assert eps.suggest_execution_provider("cuda") == "trt-rtx"
    assert [device.device_key for device in eps.check_start("cuda")] == ["gpu:10de:2484:0"]  # a request for `cuda` runs on `cuda`
    for key in ("trt", "directml"):
        with pytest.raises(EpRequestError, match="reserved"):
            eps.check_start(key)


def test_status_json(rtx_host, capsys):
    hw_fakes.fake_pack("cuda")
    assert cli.main(["status", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == "skellytracker.eps.status/1" and set(data) == {"schema", "core", "host", "recommended", "eps", "warnings"}
    assert data["core"]["ort_version"] == importlib.metadata.version("onnxruntime") and data["core"]["core_matches_pin"] is True
    assert [row["key"] for row in data["eps"]] == ["trt-rtx", "cuda", "cpu"]
    assert [(row["state"], row["reason_code"]) for row in data["eps"]] == [("not_installed", None), ("installed_unverified", None), ("builtin", None)]
    assert [(row["usable"], row["install_hint"], row["uses_gpu"]) for row in data["eps"]] == [
        (False, "Run `skellytracker-eps install trt-rtx`.", True), (True, None, True), (True, None, False)]
    assert [[device["device_key"] for device in row["devices"]] for row in data["eps"]] == [[], ["gpu:10de:2484:0"], []]
    assert data["eps"][1]["devices"][0] == {"device_key": "gpu:10de:2484:0", "gpu_key": "0000:01:00.0", "name": "NVIDIA GeForce RTX 3070",
                                            "pci_bus_id": "0000:01:00.0", "vram_total_bytes": 8 * GIB}
    assert all(row["description"].startswith("Runs on ") and len(row["description"]) <= 120 for row in data["eps"])
    assert data["eps"][0]["download_bytes"] > 100_000_000 and data["eps"][1]["source"] == "azure" and data["eps"][0]["licences"][0]["url"]
    performance = data["recommended"]["performance"]
    assert (performance["key"], performance["device_key"], performance["skipped"][0]["key"]) == ("cuda", "gpu:10de:2484:0", "trt-rtx")
    assert performance["source"] == {"kind": "hardware-table", "catalog_revision": data["core"]["catalog_revision"],
                                     "row": "nvidia-cc80-r580", "ranking_evidence": "MWY9"}
    assert data["recommended"]["accuracy"]["key"] == "cpu" and data["host"]["gpus"][0]["vram_mb"] == 8192
    assert "decision" not in json.dumps(data) and "accept" not in json.dumps(data)


def test_the_order_of_status_eps_is_the_catalog_order_and_each_hardware_class_keeps_it(rtx_host, monkeypatch):
    catalog = catalog_module.load_catalog()
    assert catalog.keys() == ("trt-rtx", "cuda", "coreml", "cpu")
    assert [row.key for row in eps.status().eps] == ["trt-rtx", "cuda", "cpu"]  # this platform has no `coreml`
    for row in catalog.data["hardware_classes"]:
        assert row["candidates"] == sorted(row["candidates"], key=catalog.keys().index), row["id"]
    large = gpu(vram=24 * GIB, bus="0000:02:00.0", device_id=0x2684, name="RTX 4090")
    set_host(monkeypatch, host(RTX, large, OLD))
    hw_fakes.fake_pack("cuda")
    cuda = eps.status().eps[1]
    assert cuda.devices == eps.run_devices("cuda") and [d.device_key for d in cuda.devices] == ["gpu:10de:2684:0", "gpu:10de:2484:0"]


def test_status_reasons_and_no_gpu(monkeypatch, ep_store, capsys):  # noqa: F811
    set_host(monkeypatch, host(OLD))
    rows = {row.key: row for row in eps.status().eps}
    assert (rows["cuda"].state, rows["cuda"].reason_code) == ("unsupported", "cc-too-low")
    assert (rows["cuda"].usable, rows["cuda"].install_hint, rows["cuda"].devices) == (False, None, ())  # an install does not help
    set_host(monkeypatch, host(gpu(driver="576.88")))
    assert eps.status().eps[0].reason_code == "driver-too-old"
    set_host(monkeypatch, host())
    assert cli.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Performance EP: cpu" in out and "trt-rtx: unsupported" in out and "single-ep" in out
    set_host(monkeypatch, host(gpu(cc="7.5")))
    assert cli.main(["recommend"]) == 0 and "none: order not measured" in capsys.readouterr().out
    assert cli.main(["recommend", "--form", "accuracy", "--json"]) == 0 and json.loads(capsys.readouterr().out)["key"] == "cpu"


def test_status_ini_is_utf16_with_a_bom(rtx_host, tmp_path):
    out = tmp_path / "status.ini"
    assert cli.main(["status", "--format", "ini", "--out", str(out)]) == 0
    raw = out.read_bytes()
    assert raw[:2] == b"\xff\xfe"
    lines = raw[2:].decode("utf-16-le").split("\r\n")
    assert lines[0] == "[status]" and "schema=skellytracker.eps.status/1" in lines and "count=3" in lines
    assert "recommended=trt-rtx" in lines and "recommended_download_mb=106" in lines and "recommended_row=nvidia-cc80-r580" in lines
    assert [line for line in lines if line.startswith("[ep.")] == ["[ep.0]", "[ep.1]", "[ep.2]"]
    assert lines[lines.index("[ep.2]") + 1] == "key=cpu" and "builtin=1" in lines[lines.index("[ep.2]"):]
    assert all(len(line.partition("=")[2]) < 1024 for line in lines)


def test_status_in_a_new_process_imports_no_onnxruntime(tmp_path):
    code = ("import sys\nfrom skellytracker.core.eps.cli import main\ncode = main(['status', '--json'])\n"
            "sys.exit(code or (9 if 'onnxruntime' in sys.modules else 0))")
    run = subprocess.run([sys.executable, "-c", code], env=dict(os.environ, SKELLYTRACKER_EP_STORE=str(tmp_path)),  # noqa: S603
                         capture_output=True, text=True, check=False)
    assert run.returncode == 0 and json.loads(run.stdout)["schema"] == "skellytracker.eps.status/1"


def test_usage_errors_exit_2(rtx_host, ep_store, capsys):  # noqa: F811
    for argv in (["install", "openvino", "--dry-run"], ["install", "tensorrt"], ["no-such-command"], ["remove"], ["status", "--format", "xml"],
                 ["install", "cuda"], ["install", "--cuda", "--progress", "jsonl"], ["install", "--recommended", "--cpu-only"]):
        assert cli.main(argv) == errors.EXIT_USAGE, argv
    assert "EpRequestError" in capsys.readouterr().err
    assert cli.main(["install", "--cpu-only"]) == 0
    assert cli.main(["install", "--trt-rtx", "--dry-run"]) == 0 and "trt-rtx-cu13" in capsys.readouterr().out
    assert not ep_store.exists()  # a dry run writes nothing


@pytest.mark.parametrize(("error", "code"), [
    (EpRequestError("refused"), 2), (EpUnavailableError("no pack.", "Run `skellytracker-eps install cuda`."), 3),
    (SessionCreationError("no node"), 4), (VRAMExhaustionError("out of memory"), 5), (RuntimeError("defect"), 1),
])
def test_each_error_class_has_its_exit_code_and_one_stderr_line(monkeypatch, capsys, error, code):
    def fail():
        raise error

    monkeypatch.setattr(state, "status", fail)
    assert cli.main(["status"]) == code
    assert capsys.readouterr().err.count("\n") == 1


def lock_urls_to(server, monkeypatch):  # noqa: F811
    for row in catalog_module.load_catalog().lock["packs"]["cuda-cu13"]["win_amd64"]["wheels"]:
        monkeypatch.setitem(row, "url", server.url + row["filename"])


def test_install_with_progress_events(fake_pack, server, monkeypatch, capsys):  # noqa: F811
    lock_urls_to(server, monkeypatch)
    monkeypatch.setattr(installer, "_verify", lambda key, progress: None)
    assert cli.main(["install", "cuda", "--yes", "--progress", "jsonl"]) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [event["event"] for event in events][0] == "plan" and events[-1] == {
        "event": "summary", "ok": ["cuda"], "failed": [], "cancelled": [], "needs_worker_restart": False}
    assert events[-2] == {"event": "done", "key": "cuda", "result": "ok", "error_code": None, "message": ""}
    progress = [event for event in events if event["event"] == "progress"]
    assert {event["phase"] for event in progress} == {"download", "unpack"} and set(progress[0]) == {"event", "key", "phase", "bytes_done", "bytes_total", "fraction"}
    assert progress[0]["key"] == "cuda" and events[0]["download_bytes"] > 0


def test_install_with_no_answer_at_the_prompt_asks_for_yes(fake_pack, server, monkeypatch, capsys):  # noqa: F811
    lock_urls_to(server, monkeypatch)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True, raising=False)  # a stdin that reports a terminal and gives EOF
    monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(EOFError()))
    assert cli.main(["install", "cuda"]) == errors.EXIT_USAGE
    assert "use --yes" in capsys.readouterr().err


def test_install_failure_exits_1_and_cancel_exits_6(fake_pack, server, monkeypatch, tmp_path, capsys):  # noqa: F811
    lock_urls_to(server, monkeypatch)
    monkeypatch.setattr(installer, "_verify", lambda key, progress: "the EP lists no device")
    assert cli.main(["install", "cuda", "--yes"]) == errors.EXIT_FAILURE
    assert "verify-failed" in capsys.readouterr().out
    cancel_file = tmp_path / "cancel"
    cancel_file.write_text("", encoding="utf-8")

    def install_until_cancel(plan, *, progress=None, cancel=None, from_dir=None):
        assert cancel.wait(10), "the cancel file did not set the cancel event"
        return InstallResult(cancelled=("cuda",))

    monkeypatch.setattr(installer, "install", install_until_cancel)
    assert cli.main(["install", "cuda", "--yes", "--cancel-file", str(cancel_file)]) == errors.EXIT_CANCELLED


def test_gc_remove_and_the_console_script(rtx_host, ep_store, capsys):  # noqa: F811
    assert cli.main(["gc", "--force"]) == 0 and "Removed packs: none" in capsys.readouterr().out
    assert cli.main(["remove", "--consumer", "environment"]) == 0 and not list((ep_store / "refs").glob("*.json"))
    scripts = importlib.metadata.entry_points(group="console_scripts")
    assert scripts["skellytracker-eps"].value == "skellytracker.core.eps.cli:main"
