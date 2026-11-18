"""Tests of `certify()`, the certification offers and the CLI prompt. They use fakes and need no GPU."""

import copy
import json
import socket
import types

import numpy as np
import pytest

from skellytracker.core import eps, errors, pipelines
from skellytracker.core.eps import certification, cli, evidence, installer, recommendation, state, verification
from skellytracker.core.eps._download import DownloadError
from skellytracker.core.eps.catalog import EpCatalog
from skellytracker.core.eps.records import InstallPlan, InstallResult, PlannedPack, Verdict
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.runtime import probe_runtime
from skellytracker.tests import hw_fakes
from skellytracker.tests.hw_fakes import gpu, host
from skellytracker.tests.test_eps_store import ep_store  # noqa: F401 - fixture

THRESHOLDS = {"box_iou_min": 0.9, "keypoint_box_fraction_max": 0.01, "score_min": 0.4}


@pytest.fixture
def rtx_host(monkeypatch, ep_store):  # noqa: F811
    fake_host = host(gpu())
    for module in (state, recommendation, installer, certification, verification):
        monkeypatch.setattr(module, "probe_host", lambda: fake_host)
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())
    hw_fakes.fake_pack("trt-rtx")
    return ep_store


def probe(monkeypatch, ok=True, error=None):
    def verify(keys, force=False):
        if error is not None:
            raise error
        return (Verdict(keys[0], "L3", ok, "k", reason=None if ok else "the folder secretdir failed", max_abs_diff=0.001),)

    monkeypatch.setattr(verification, "verify", verify)


def result(shift=0.0, people=1):
    boxes = types.SimpleNamespace(xyxy=np.array([[10.0, 10.0, 110.0, 210.0]]), present=np.array([people == 1]))
    points = np.array([[[50.0 + shift, 60.0], [70.0, 80.0], [1.0, 1.0]]])
    wholebody = types.SimpleNamespace(xy=points, score=np.array([[0.9, 0.8, 0.1]]), present=np.array([people == 1]))
    return {"boxes": boxes, "wholebody": wholebody}


def test_compare_results_applies_the_pixel_rule():
    same = certification.compare_results(result(), result(), THRESHOLDS)
    assert same["ok"] and same["box_iou_min"] == 1.0 and same["keypoint_px_max"] == 0.0 and same["points_compared"] == 2
    moved = certification.compare_results(result(), result(shift=3.0), THRESHOLDS)
    assert not moved["ok"] and moved["reason_code"] == "keypoints-differ" and moved["keypoint_px_max"] == 3.0
    assert moved["keypoint_box_fraction_median"] == pytest.approx(1.5 / np.hypot(100, 200))  # one point moved, one did not
    assert moved["keypoint_box_fraction_p99"] == pytest.approx(0.99 * 3.0 / np.hypot(100, 200))
    assert certification.compare_results(result(), result(people=0), THRESHOLDS)["reason_code"] == "people-differ"
    assert certification.compare_results(result(people=0), result(people=0), THRESHOLDS)["reason_code"] == "no-person-on-cpu"
    other = result()
    other["boxes"].xyxy = np.array([[10.0, 10.0, 60.0, 210.0]])
    assert certification.compare_results(result(), other, THRESHOLDS)["reason_code"] == "box-differs"


def test_an_uncertified_usable_ep_has_an_offer_until_evidence_or_an_answer(rtx_host, monkeypatch):
    status = eps.status()
    (offer,) = status.certify_offers
    assert (offer.ep_key, offer.device_key, offer.prompt, offer.seconds) == ("trt-rtx", "gpu:10de:2484:0", True, 60)
    assert {row.key: row.certified for row in status.eps} == {"trt-rtx": False, "cuda": False, "directml": None, "cpu": None}
    eps.dismiss_certification("trt-rtx")
    assert [o.prompt for o in eps.status().certify_offers] == [False]
    row = {"ep": "trt-rtx", "os": "Windows", "gpu": "10de:2484", "set": "s", "source": "maintainer", "result": "pass"}
    monkeypatch.setattr(evidence, "load_evidence", lambda: (row,))
    status = eps.status()
    assert status.certify_offers == () and status.eps[0].certified is True


def test_certify_writes_a_report_with_no_path_and_no_hostname(rtx_host, monkeypatch):
    probe(monkeypatch)
    steps = []
    done = eps.certify("trt-rtx", progress=steps.append)
    report = json.loads(done.report_json)
    assert done.ok and done.probe_ok and done.wide_ok is None and steps == ["probe", "report"]
    assert report["schema"] == certification.REPORT_SCHEMA and report["result"] == "pass" and report["wide"] == {"ran": False}
    assert report["gpu"] == {"vendor": "nvidia", "name": "NVIDIA GeForce RTX 3070", "id": "10de:2484", "driver_version": "610.88",
                             "compute_capability": "8.6"}
    assert report["versions"]["set_hash"] == evidence.set_hash(eps.load_catalog())
    runtime = probe_runtime()
    assert report["versions"]["ort_distribution"] in runtime.ort_packages and report["versions"]["windowsml"] == runtime.windowsml_version
    assert report["versions"]["ort_version"] in runtime.ort_package_versions
    assert report["host"]["os_release"] == certification.probe_host().os_release
    assert report["host"]["os_version"] == certification.probe_host().os_version
    assert report["host"]["os_label"] == certification.probe_host().os_label
    path = certification.reports_dir() / done.report_path.replace("\\", "/").rsplit("/", 1)[1]
    assert path.read_text(encoding="utf-8") == done.report_json + "\n"
    assert str(rtx_host.parent) not in done.report_json and socket.gethostname() not in done.report_json
    assert [offer.prompt for offer in eps.status().certify_offers] == [False]  # a run on this host ends the prompt


def test_a_failure_is_a_reason_code_and_never_an_error_text(rtx_host, monkeypatch, tmp_path):
    probe(monkeypatch, ok=False)
    failed = eps.certify("trt-rtx", wide=True, out=tmp_path / "r.json")
    assert not failed.ok and failed.reason_code == "probe-l3-failed" and "secretdir" not in failed.report_json
    assert json.loads(failed.report_json)["wide"] == {"ran": False}  # the wider run needs a probe pass
    probe(monkeypatch, error=EpUnavailableError("the folder secretdir does not register"))
    raised = eps.certify("trt-rtx", out=tmp_path / "r.json")
    assert raised.reason_code == "EpUnavailableError" and "secretdir" not in raised.report_json
    with pytest.raises(EpUnavailableError):
        eps.certify("cpu")


def test_a_setup_failure_is_not_run_and_keeps_the_prompt(rtx_host, monkeypatch, tmp_path, capsys):
    probe(monkeypatch, error=EpUnavailableError("the pack is not installed"))
    done = eps.certify("trt-rtx", out=tmp_path / "r.json")
    assert not done.ok and json.loads(done.report_json)["result"] == "not-run"
    assert [offer.prompt for offer in eps.status().certify_offers] == [True]
    assert cli.main(["certify", "trt-rtx", "--out", str(tmp_path / "r.json")]) == errors.EXIT_EP_UNAVAILABLE
    assert "skellytracker-eps install trt-rtx" in capsys.readouterr().out
    probe(monkeypatch)

    def no_network(*args, **kwargs):
        raise DownloadError("offline", "no network")

    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: types.SimpleNamespace(available=True))
    monkeypatch.setattr(certification._download, "fetch", no_network)
    monkeypatch.setattr(certification.store, "cache_root", lambda: tmp_path / "cache")
    done = eps.certify("trt-rtx", wide=True, out=tmp_path / "r.json")
    assert not done.ok and done.reason_code == "DownloadError" and json.loads(done.report_json)["result"] == "not-run"
    assert done.wide_ok is None and [offer.prompt for offer in eps.status().certify_offers] == [True]
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: types.SimpleNamespace(available=False))
    done = eps.certify("trt-rtx", wide=True, out=tmp_path / "r.json")  # a normal install has no ONNX file
    report = json.loads(done.report_json)
    assert done.ok and report["result"] == "pass" and report["wide"] == {"ran": False, "reason_code": "models-missing"}
    assert [offer.prompt for offer in eps.status().certify_offers] == [False]


def test_a_stored_answer_ends_with_a_pack_upgrade(rtx_host, monkeypatch):
    eps.dismiss_certification("trt-rtx")
    catalog = eps.load_catalog()
    (stored,) = certification.read_answers()
    assert stored == f"trt-rtx|{catalog.pack('trt-rtx')['version']}|Windows|10de:2484"
    data = copy.deepcopy(catalog.data)
    data["eps"]["trt-rtx"]["packs"][0]["version"] = "99.0"
    newer = EpCatalog(data=data, lock=catalog.lock, revision="r")
    assert certification.pair_key(newer, "trt-rtx", gpu(), "Windows") != stored


def test_a_gpu_with_no_pci_ids_and_a_malformed_row_match_nothing(rtx_host, monkeypatch):
    monkeypatch.setattr(evidence, "load_evidence", lambda: ("not a row", {"ep": "trt-rtx"}, {"ep": "trt-rtx", "os": "Windows",
                                                                                             "gpu": None, "result": "pass"}))
    assert not evidence.certified("trt-rtx", gpu(device_id=None), "Windows")
    assert [offer.prompt for offer in eps.status().certify_offers] == [True]  # no crash on a malformed row
    no_ids = host(gpu(device_id=None))
    for module in (state, recommendation, installer, certification, verification):
        monkeypatch.setattr(module, "probe_host", lambda: no_ids)
    # `ep_gpus()` gives no GPU with no PCI ids, so two such GPUs never share a pair
    assert certification.certify_offers(eps.load_catalog(), no_ids) == ()
    with pytest.raises(EpUnavailableError):
        eps.certify("trt-rtx")


def test_compare_results_fails_a_lost_or_low_ep_score():
    lost = result()
    lost["wholebody"].score = np.array([[0.9, np.nan, 0.1]])
    assert certification.compare_results(result(), lost, THRESHOLDS)["reason_code"] == "not-finite"
    moved = result()
    moved["wholebody"].xy = moved["wholebody"].xy.copy()
    moved["wholebody"].xy[0, 2] = np.nan  # a point under `score_min` also must stay finite
    assert certification.compare_results(result(), moved, THRESHOLDS)["reason_code"] == "not-finite"
    low = result()
    low["wholebody"].score = np.array([[0.9, 0.2, 0.1]])
    assert certification.compare_results(result(), low, THRESHOLDS)["reason_code"] == "scores-differ"
    near = result()
    near["wholebody"].score = np.array([[0.9, 0.35, 0.1]])  # fp16 noise near `score_min` is not a failure
    assert certification.compare_results(result(), near, THRESHOLDS)["ok"]


class FakeRun:
    def __init__(self, ep_key, codes):
        self.ep_key, self.codes = ep_key, codes

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def process(self, frame):
        return result()

    @property
    def models(self):
        return {"pose": {"key": "rtmw", "version": "1", "size": "m", "precision": "fp16", "execution_provider": self.ep_key,
                         "device": None, "sidecar_sha256": "0" * 64}}

    @property
    def warnings(self):
        return tuple(types.SimpleNamespace(code=code) for code in self.codes)


def test_wide_run_with_fakes(rtx_host, monkeypatch, tmp_path):
    import cv2

    settings = eps.load_catalog().data["certification"]
    path = tmp_path / "certify" / f"{settings['image']['sha256']}.jpg"
    path.parent.mkdir()
    path.write_bytes(cv2.imencode(".jpg", np.zeros((8, 8, 3), np.uint8))[1].tobytes())
    monkeypatch.setattr(certification.store, "cache_root", lambda: tmp_path)
    monkeypatch.setattr(certification._download, "sha256_of", lambda p: settings["image"]["sha256"])
    monkeypatch.setattr(certification._download, "fetch", lambda *a, **k: pytest.fail("a cached image is not downloaded again"))
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: types.SimpleNamespace(available=True))
    monkeypatch.setattr(pipelines, "load_pipeline", lambda key: "config")
    monkeypatch.setattr(pipelines, "Frame", lambda frame, frame_index: frame)
    codes = []
    monkeypatch.setattr(pipelines, "start_pipeline", lambda config, execution_provider, **k: FakeRun(execution_provider, codes))
    steps = []
    found = certification._wide_run("trt-rtx", settings, steps.append)
    assert found["ok"] and found["ran"] and steps == ["download", "cpu", "ep"] and found["warnings"] == []
    assert found["models"] == [{"key": "rtmw", "version": "1", "size": "m", "precision": "fp16", "execution_provider": "trt-rtx", "device": None}]
    codes.append(certification.PARTIAL_PLACEMENT)
    found = certification._wide_run("trt-rtx", settings, steps.append)
    assert not found["ok"] and found["reason_code"] == "partial-placement" and found["warnings"] == ["ep_partial_placement"]
    devices = []  # the device key goes to the EP run only, not to the CPU EP run (ADR-Z5X7)
    monkeypatch.setattr(pipelines, "start_pipeline",
                        lambda config, execution_provider, device=None, **k: devices.append(device) or FakeRun(execution_provider, []))
    assert certification._wide_run("directml", settings, steps.append, "gpu:8086:a780:0")["ok"] and devices == [None, "gpu:8086:a780:0"]
    monkeypatch.setattr(pipelines, "get_pipeline", lambda key: types.SimpleNamespace(available=False))
    assert certification._wide_run("trt-rtx", settings, steps.append) == {"ran": False, "reason_code": "models-missing"}


def test_the_cli_asks_only_a_person_at_a_terminal(rtx_host, monkeypatch, capsys):
    probe(monkeypatch)
    monkeypatch.setattr(cli, "show_folder", lambda folder: pytest.fail("no folder opens with no person"))
    assert cli.main(["status"]) == 0 and cli.main(["certify", "trt-rtx", "--json"]) == 0  # no terminal: no question, probe only
    out = capsys.readouterr().out
    assert json.loads(out[out.index("{"):])["wide"] == {"ran": False}
    eps.dismiss_certification("trt-rtx")
    answers = iter(["d"])
    monkeypatch.setattr(certification, "read_answers", lambda: {})
    monkeypatch.setattr(cli, "ask", lambda question: next(answers))
    dismissed = []
    monkeypatch.setattr(certification, "dismiss_certification", dismissed.append)
    assert cli.main(["status"]) == 0 and dismissed == ["trt-rtx"]


def test_ask_needs_a_terminal_on_stdin_and_on_stdout(rtx_host, monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False, raising=False)
    monkeypatch.setattr("builtins.input", lambda question: pytest.fail("no question goes into a redirected output"))
    assert cli.ask("Test it? ") is None
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda question: " Y ")
    assert cli.ask("Test it? ") == "y"
    monkeypatch.setattr("builtins.input", lambda question: (_ for _ in ()).throw(EOFError()))
    assert cli.ask("Test it? ") is None  # a stdin can report a terminal and still have no input
    probe(monkeypatch)
    monkeypatch.setattr(cli, "show_folder", lambda folder: None)
    monkeypatch.setattr(cli, "ask", lambda question: pytest.fail("--json and --out ask nothing"))
    assert cli.main(["certify", "trt-rtx", "--json"]) == 0 and cli.main(["certify", "trt-rtx", "--out", str(tmp_path / "r.json")]) == 0


def test_a_failed_certification_prompt_keeps_the_install_exit_code(rtx_host, monkeypatch, capsys):
    plan = InstallPlan(packs=(PlannedPack("trt-rtx", "p", "1", (), 1, 1),), download_bytes=1, disk_bytes=1)
    monkeypatch.setattr(installer, "plan_install", lambda selection, **kwargs: plan)
    monkeypatch.setattr(installer, "install", lambda plan, **kwargs: InstallResult(ok=("trt-rtx",)))
    monkeypatch.setattr(cli, "ask", lambda question: "y")
    for error in (KeyboardInterrupt(), RuntimeError("the folder secretdir")):
        monkeypatch.setattr(cli, "certify_prompt", lambda status, error=error: (_ for _ in ()).throw(error))
        assert cli.main(["install", "trt-rtx"]) == errors.EXIT_OK
        assert "certification prompt stopped" in capsys.readouterr().err
