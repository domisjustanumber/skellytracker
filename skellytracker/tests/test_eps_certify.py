"""Tests of the helpers and the children of the session checks of `certify()`, and of the CLI question. They use fakes and need no GPU."""

import types

import numpy as np
import pytest

from skellytracker.core import eps, pipelines
from skellytracker.core.eps import certification, cli, evidence, installer, recommendation, state, verification
from skellytracker.tests import hw_fakes
from skellytracker.tests.hw_fakes import gpu, host
from skellytracker.tests.test_eps_store import ep_store  # noqa: F401 - fixture

THRESHOLDS = {"box_iou_min": 0.9, "keypoint_box_fraction_max": 0.01, "score_min": 0.4}


def test_certified_needs_a_reviewed_row_of_the_version_set_of_this_release(monkeypatch, ep_store):  # noqa: F811
    fake_host = host(gpu())
    for module in (state, recommendation, installer, verification):
        monkeypatch.setattr(module, "probe_host", lambda: fake_host)
    monkeypatch.setattr(evidence, "load_evidence", lambda: ())
    hw_fakes.fake_pack("trt-rtx")
    status = eps.status()
    assert {row.key: row.certified for row in status.eps} == {"trt-rtx": False, "cuda": False, "amdgpu": None, "migraphx": None, "directml": None, "cpu": None}
    row = {"ep": "trt-rtx", "os": "Windows", "gpu": "10de:2484", "set": "s", "source": "maintainer", "result": "pass"}
    monkeypatch.setattr(evidence, "load_evidence", lambda: (row,))  # a row of an other version set is not reviewed
    assert eps.status().eps[0].certified is False and not evidence.certified("trt-rtx", gpu(), "Windows")
    monkeypatch.setattr(evidence, "load_evidence", lambda: ({**row, "set": evidence.set_hash(eps.load_catalog())},))
    assert eps.status().eps[0].certified is True
    monkeypatch.setattr(evidence, "load_evidence", lambda: ("not a row", {"ep": "trt-rtx"}, {**row, "gpu": None}))
    assert not evidence.certified("trt-rtx", gpu(device_id=None), "Windows")  # no crash on a malformed row


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


def in_process(target, args, *, progress=None, **limits):
    """`verification.spawn_child()` in this process, so that the monkeypatches of a test reach the target."""
    sent = []
    target(*args, types.SimpleNamespace(send=lambda message: progress(message) if isinstance(message, str) else sent.append(message),
                                        close=lambda: None))
    return sent[-1], None, 0


def test_the_speed_against_the_cpu_is_similar_within_20_percent():
    assert [certification.speed_against_cpu(ep, 20.0) for ep in (10.0, 16.0, 24.0, 38.0)] == ["faster", "similar", "similar", "slower"]


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


def test_session_frames_run_each_test_frame_in_order_with_a_rising_time_in_live(monkeypatch):
    import pickle

    frames, starts = [], []
    monkeypatch.setattr(pipelines, "load_pipeline", lambda key: "config")
    monkeypatch.setattr(pipelines, "Frame", lambda image, frame_index, timestamp_ms: frames.append((frame_index, timestamp_ms)) or image)
    monkeypatch.setattr(pipelines, "start_pipeline", lambda config, running_mode, execution_provider, device=None, **k:
                        starts.append((running_mode, execution_provider, device)) or FakeRun(execution_provider, []))
    found = certification.session_frames("p", "trt-rtx", ["image"] * 3, "live", "gpu:10de:2484:0")
    assert frames == [(0, 0.0), (1, 33.0), (2, 66.0)] and starts == [("live", "trt-rtx", "gpu:10de:2484:0")]
    assert len(found["frames"]) == 3 and found["ms"] >= 0 and found["warnings"] == []
    assert found["models"][0]["precision"] == "fp16" and certification.compare_results(found["frames"][0], result(), THRESHOLDS)["ok"]
    assert pickle.loads(pickle.dumps(found))["frames"][2]["wholebody"].score.tolist() == [[0.9, 0.8, 0.1]]  # noqa: S301 - a child sends it; the test made the bytes
    frames.clear()
    certification.session_frames("p", "cpu", ["image"] * 3, "video")
    assert frames == [(0, None), (1, None), (2, None)] and starts[-1] == ("video", "cpu", None)


def test_a_session_child_keeps_the_error_of_each_mode(monkeypatch):
    def session_frames(pipeline, key, image, mode, device):
        if mode == "live":
            raise RuntimeError("the folder secretdir")
        return {"frames": [], "image": image}

    monkeypatch.setattr(certification, "quick_frames", lambda settings: "image")
    monkeypatch.setattr(certification, "session_frames", session_frames)
    monkeypatch.setattr(verification, "spawn_child", in_process)
    steps = []
    found, _, _ = certification.session_run("cpu", {"pipeline": "p"}, ("video", "live"), progress=steps.append)
    assert found == {"video": {"frames": [], "image": "image"}, "live": {"error": "RuntimeError"}} and steps == ["video", "live"]
    monkeypatch.setattr(certification, "quick_frames", lambda settings: (_ for _ in ()).throw(certification.FramesUnavailableError("absent")))
    assert certification.session_run("cpu", {"pipeline": "p"}, ("video",), progress=steps.append)[0] == {"error": "FramesUnavailableError"}


def test_ask_needs_a_terminal_on_stdin_and_on_stdout(monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False, raising=False)
    monkeypatch.setattr("builtins.input", lambda question: pytest.fail("no question goes into a redirected output"))
    assert cli.ask("Test it? ") is None
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda question: " Y ")
    assert cli.ask("Test it? ") == "y"
    monkeypatch.setattr("builtins.input", lambda question: (_ for _ in ()).throw(EOFError()))
    assert cli.ask("Test it? ") is None  # a stdin can report a terminal and still have no input
