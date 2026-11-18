"""The CLI commands `run`, `validate` and `nodes` (`core/pipelines/cli.py`), and the webcam demo of a pipeline."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import cv2
import numpy as np
import pytest

import skellytracker.__main__ as entry  # noqa: E402
from skellytracker.core import eps, errors  # noqa: E402
from skellytracker.core.detectors import catalog  # noqa: E402
from skellytracker.core.pipelines import cli, timing  # noqa: E402
from skellytracker.core.pipelines.config import NODE_TYPES  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import detector_pipeline, image, isolate, write_models  # noqa: E402
from skellytracker.tests.pipelines.test_sessions import MEDIAPIPE  # noqa: E402

IMAGES = {11: 1, 5: 3, 7: 2}  # image id -> the value of the image
RECORD = {"action": "record", "port": "person.boxes", "name": "boxes"}
REPLAY = {"action": "replay", "port": "person.boxes", "name": "boxes"}


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


@pytest.fixture
def no_recommend(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(form: str) -> None:
        raise AssertionError("eps.recommend must not be called")

    monkeypatch.setattr(eps, "recommend", fail)


def pipeline_file(tmp_path: Path, name: str = "pipeline", *, node_ep: bool = False, taps: list[dict] | None = None, data: dict | None = None) -> str:
    """Write a pipeline as a JSON file and return its path. Without `node_ep`, no node gives an EP, so the run must give one."""
    data = data or detector_pipeline(max_instances=2)
    if not node_ep:
        for node in data["nodes"]:
            node.get("params", {}).pop("execution_provider", None)
    if data is not MEDIAPIPE:
        data["instrumentation"] = {"timing_spans": ["pipeline.run", "person.inference"], "taps": taps or []}
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def coco(tmp_path: Path) -> list[str]:
    """The arguments `--coco` and `--images` of three images. The image list of the file is not in `image_id` order."""
    folder = tmp_path / "images"
    folder.mkdir()
    records = []
    for image_id, value in IMAGES.items():
        assert cv2.imwrite(str(folder / f"{image_id}.png"), image(value, 24 + image_id, 40))  # each image has another size
        records.append({"id": image_id, "file_name": f"{image_id}.png"})
    (tmp_path / "coco.json").write_text(json.dumps({"images": records, "annotations": []}), encoding="utf-8")
    return ["--coco", str(tmp_path / "coco.json"), "--images", str(folder)]


def run_args(tmp_path: Path, root: Path, coco: list[str], pipeline: str | None = None, out: str = "out") -> list[str]:
    return ["run", "--pipeline", pipeline or pipeline_file(tmp_path), *coco, "--out", str(tmp_path / out), "--user-root", str(root)]


def lines_of(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class FakeRun:
    """A run that does nothing. It is the result of a patched start."""

    output_schema: dict = {}

    def __init__(self) -> None:
        self.closed, self.frames = False, []

    def process(self, frame: Any) -> dict:
        self.frames.append(frame)
        return {}

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> FakeRun:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def spy_start(monkeypatch: pytest.MonkeyPatch, name: str = "_start", error: Exception | None = None) -> dict[str, Any]:
    """Patch the start of a run. Return the mapping that gets its keyword arguments and its `FakeRun`."""
    seen: dict[str, Any] = {}

    def start(source: Any, **parameters: Any) -> FakeRun:
        seen.update(parameters, run=FakeRun())
        if error is not None:
            raise error
        return seen["run"]

    monkeypatch.setattr(cli, name, start)
    return seen


# ---------------------------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------------------------


def test_run_writes_the_timing_file_of_the_coco_input_form_with_the_header_first(
    tmp_path: Path, root: Path, coco: list[str], no_recommend: None, capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([*run_args(tmp_path, root, coco), "--ep", "cpu"]) == 0
    assert [path.name for path in (tmp_path / "out").iterdir()] == ["timing.jsonl"]  # `--out` gets no other file
    header, *events = lines_of(tmp_path / "out" / "timing.jsonl")
    assert (header["schema"], header["running_mode"], header["camera_ids"]) == ("skellytracker.timing/1", "image", [0])
    assert header["image_list_sha256"] == timing.image_list_sha256(list(IMAGES))
    assert [node["execution"]["used_ep"] for node in header["nodes"]] == ["cpu", "cpu"]
    runs = [event for event in events if (event["node_id"], event["span"]) == ("pipeline", "run")]
    assert [event["images"] for event in runs] == [[{"frame_index": index, "camera_id": 0}] for index in range(3)]
    assert sum(event["node_id"] == "person" for event in events) == 3
    assert capsys.readouterr().out == ""  # the EP is not a default, so the command prints no EP


def test_run_takes_a_jsonl_file_for_out_and_writes_no_file_with_timing_off(tmp_path: Path, root: Path, coco: list[str]) -> None:
    assert cli.main([*run_args(tmp_path, root, coco, out="deep/run.jsonl"), "--ep", "cpu", "--timing", "on"]) == 0
    assert lines_of(tmp_path / "deep" / "run.jsonl")[0]["schema"] == "skellytracker.timing/1"
    assert cli.main([*run_args(tmp_path, root, coco, out="none"), "--ep", "cpu", "--timing", "off"]) == 0
    assert not (tmp_path / "none").exists()


def test_run_records_a_tap_in_ascending_image_id_order_and_a_second_run_replays_it(tmp_path: Path, root: Path, coco: list[str]) -> None:
    taps = ["--ep", "cpu", "--taps", str(tmp_path / "taps")]
    assert cli.main([*run_args(tmp_path, root, coco, pipeline_file(tmp_path, taps=[RECORD])), *taps]) == 0
    manifest = json.loads((tmp_path / "taps" / "boxes" / "tap.json").read_text(encoding="utf-8"))
    assert (manifest["image_list_sha256"], manifest["running_mode"]) == (timing.image_list_sha256(list(IMAGES)), "image")
    rows = lines_of(tmp_path / "taps" / "boxes" / "boxes.jsonl")
    assert [(row["image_id"], row["frame_index"], row["row"]) for row in rows] == [(5, 0, 0), (5, 0, 1), (7, 1, 0), (7, 1, 1), (11, 2, 0), (11, 2, 1)]
    assert cli.main([*run_args(tmp_path, root, coco, pipeline_file(tmp_path, "replay", taps=[REPLAY]), out="replay"), *taps]) == 0
    header, *events = lines_of(tmp_path / "replay" / "timing.jsonl")
    assert not any(event["node_id"] == "person" for event in events)  # the replayed node does not run


def test_v_pipeline_taps_2_run_of_a_file_with_a_tap_and_no_taps_flag_exits_with_2(
    tmp_path: Path, root: Path, coco: list[str], capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([*run_args(tmp_path, root, coco, pipeline_file(tmp_path, taps=[RECORD])), "--ep", "cpu"]) == 2
    assert "V-pipeline.taps-2" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------------
# The exit codes
# ---------------------------------------------------------------------------------------------


def test_a_usage_error_exits_with_2(tmp_path: Path, root: Path, coco: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["run", "--pipeline", "x"]) == 2  # argparse: a required argument is absent
    assert cli.main([*run_args(tmp_path, root, coco), "--ep", "cpu", "--timing", "maybe"]) == 2
    assert cli.main(["no-such-command"]) == 2
    assert cli.main(["nodes", "--help"]) == 0
    capsys.readouterr()
    absent = ["--coco", str(tmp_path / "absent.json"), "--images", str(tmp_path)]
    assert cli.main([*run_args(tmp_path, root, absent), "--ep", "cpu"]) == 2
    assert "cannot read the images of the COCO file absent.json" in capsys.readouterr().err


@pytest.mark.parametrize(("flags", "text"), [
    (["--ep", "no-such-ep"], "'no-such-ep' is not an EP key"),
    (["--ep", "trt"], "trt"),  # a reserved key
    (["--ep", "cpu", "--ep-option", "no_equals_sign"], "--ep-option must be <name>=<value>"),
    (["--ep", "cpu", "--ep-option", "no_such_option=1"], "no_such_option"),
])
def test_an_ep_request_error_exits_with_2(tmp_path: Path, root: Path, coco: list[str], capsys: pytest.CaptureFixture[str], flags: list[str], text: str) -> None:
    assert cli.main([*run_args(tmp_path, root, coco), *flags]) == errors.EXIT_USAGE == 2
    stderr = capsys.readouterr().err
    assert stderr.startswith("EpRequestError: ") and text in stderr and "Traceback" not in stderr and len(stderr.splitlines()) == 1


@pytest.mark.parametrize(("error", "code"), [
    (errors.EpUnavailableError("The EP 'cuda' is not installed.", "Run `skellytracker-eps install cuda`."), 3),
    (errors.SessionCreationError("The EP 'cuda' did not start."), 4),
    (errors.VRAMExhaustionError("The GPU memory is exhausted."), 5),
    (errors.MissingDependencyError("mediapipe", ["holistic"]), 1),
    (errors.MissingDependencyError(None, ["person"], ["demo-n_b3_fp32.onnx"], "the file is absent"), 1),
    (RuntimeError("an error with no class in the table"), 1),
])
def test_a_typed_error_of_the_start_gives_its_exit_code_and_one_line_on_stderr(
    tmp_path: Path, root: Path, coco: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], error: Exception, code: int,
) -> None:
    spy_start(monkeypatch, error=error)
    assert cli.main([*run_args(tmp_path, root, coco), "--ep", "cpu"]) == code
    stderr = capsys.readouterr().err
    assert stderr == f"{type(error).__name__}: {error}\n"  # the same message as the API, and no traceback
    if isinstance(error, errors.MissingDependencyError):
        assert "V-pipeline.running-3" in stderr


def test_an_onnx_file_that_is_absent_exits_with_1_and_names_the_file(tmp_path: Path, coco: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    root = write_models(tmp_path / "bare", files=False)
    assert cli.main([*run_args(tmp_path, root, coco), "--ep", "cpu"]) == 1
    stderr = capsys.readouterr().err
    assert stderr.startswith("MissingDependencyError: V-pipeline.running-3") and "demo-n_b3_fp32.onnx" in stderr


def test_a_bad_pipeline_file_or_an_unknown_key_exits_with_2(tmp_path: Path, root: Path, coco: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    data = detector_pipeline()
    data["nodes"][0]["params"]["sidecar_sha256"] = "0" * 64
    assert cli.main([*run_args(tmp_path, root, coco, pipeline_file(tmp_path, data=data)), "--ep", "cpu"]) == 2
    assert "V-node.onnx_model-1" in capsys.readouterr().err
    assert cli.main([*run_args(tmp_path, root, coco, "nothing@nowhere"), "--ep", "cpu"]) == 2
    stderr = capsys.readouterr().err
    assert stderr.startswith("PipelineNotFoundError: ") and "nothing@nowhere" in stderr and "Traceback" not in stderr


# ---------------------------------------------------------------------------------------------
# The default EP
# ---------------------------------------------------------------------------------------------


def recommend_cpu(monkeypatch: pytest.MonkeyPatch, options: tuple = ()) -> list[str]:
    forms: list[str] = []

    def recommend(form: str) -> SimpleNamespace:
        forms.append(form)
        return SimpleNamespace(chosen=SimpleNamespace(ep_key="cpu"), options=options)

    monkeypatch.setattr(eps, "recommend", recommend)
    return forms


def test_run_with_no_ep_uses_the_recommended_performance_ep_and_prints_it_and_its_options(
    tmp_path: Path, root: Path, coco: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    forms = recommend_cpu(monkeypatch)
    assert cli.main(run_args(tmp_path, root, coco)) == 0
    assert forms == ["performance"]
    assert capsys.readouterr().out == "Execution provider: cpu (recommended for performance), options: {}\n"
    assert lines_of(tmp_path / "out" / "timing.jsonl")[0]["nodes"][0]["execution"]["requested_ep"] == "cpu"


def test_the_start_gets_the_recommended_ep_with_its_options_and_an_ep_option_of_the_user_wins(
    tmp_path: Path, root: Path, coco: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    # `V-pipeline.running-8` cannot occur through the CLI: a pipeline that needs an EP always gets the recommended EP.
    recommend_cpu(monkeypatch, options=(("a", "1"), ("b", "2")))
    seen = spy_start(monkeypatch)
    assert cli.main([*run_args(tmp_path, root, coco), "--ep-option", "b=3", "--device", "gpu:0", "--device", "gpu:1", "--cpu-threads", "2"]) == 0
    assert (seen["execution_provider"], seen["ep_options"], seen["device"]) == ("cpu", {"a": "1", "b": "3"}, ["gpu:0", "gpu:1"])
    assert seen["cpu_threads"] == 2
    assert (seen["camera_ids"], seen["running_mode"], seen["image_ids"]) == ([0], "image", [5, 7, 11])
    assert [frame.frame_index for frame in seen["run"].frames] == [0, 1, 2] and seen["run"].closed
    assert [frame.image.shape for frame in seen["run"].frames] == [(29, 40, 3), (31, 40, 3), (35, 40, 3)]  # ascending `image_id`
    assert "options: {'a': '1', 'b': '3'}" in capsys.readouterr().out


def test_run_asks_for_no_recommended_ep_when_each_onnx_model_node_gives_its_ep(
    tmp_path: Path, root: Path, coco: list[str], monkeypatch: pytest.MonkeyPatch, no_recommend: None,
) -> None:
    seen = spy_start(monkeypatch)
    assert cli.main(run_args(tmp_path, root, coco, pipeline_file(tmp_path, node_ep=True))) == 0
    assert seen["execution_provider"] is None


def test_a_pipeline_with_no_onnx_model_node_gets_no_ep_and_v_pipeline_running_9_refuses_the_ep_flag(
    tmp_path: Path, root: Path, coco: list[str], monkeypatch: pytest.MonkeyPatch, no_recommend: None, capsys: pytest.CaptureFixture[str],
) -> None:
    mediapipe = pipeline_file(tmp_path, "mediapipe", data=MEDIAPIPE)
    assert cli.main([*run_args(tmp_path, root, coco, mediapipe), "--ep", "cpu"]) == 2  # the real start check
    assert "V-pipeline.running-9" in capsys.readouterr().err
    seen = spy_start(monkeypatch)
    assert cli.main(run_args(tmp_path, root, coco, mediapipe)) == 0
    assert seen["execution_provider"] is None and capsys.readouterr().out == ""


# ---------------------------------------------------------------------------------------------
# validate and nodes
# ---------------------------------------------------------------------------------------------


def test_validate_prints_the_warnings_of_a_valid_file_and_exits_with_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = write_models(tmp_path / "bare", files=False)  # no ONNX file: the warning `missing_dependency`
    assert cli.main(["validate", pipeline_file(tmp_path), "--user-root", str(root)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3 and all(line.startswith("warning: missing_dependency: ") for line in lines[:2])
    assert lines[2] == "demo-models@demo-source: valid"


def test_validate_prints_the_rule_id_of_a_file_that_is_not_valid_and_exits_with_2(tmp_path: Path, root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = detector_pipeline()
    data["nodes"][0]["params"]["sidecar_sha256"] = "0" * 64
    assert cli.main(["validate", pipeline_file(tmp_path, data=data), "--user-root", str(root)]) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("ValueError: V-node.onnx_model-1: person: sidecar_sha256 is") and captured.out == ""
    data = detector_pipeline()
    data["outputs"]["holistic"] = "nobody.keypoints"
    assert cli.main(["validate", pipeline_file(tmp_path, data=data), "--user-root", str(root)]) == 2
    assert "V-pipeline." in capsys.readouterr().err


def test_validate_takes_a_key_of_the_catalog(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["validate", "mediapipe-holistic-tasks@skellytracker"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "mediapipe-holistic-tasks@skellytracker: valid"


def test_nodes_lists_the_12_node_types_as_text_and_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    names = [node.type for node in NODE_TYPES]
    assert len(names) == 12
    assert cli.main(["nodes"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line.split()[0] for line in lines if not line.startswith(" ")] == names
    assert "onnx_model  (image: image, boxes: boxes (optional), run_if: flag (optional)) -> (boxes: boxes, keypoints: keypoints)  spans: preprocess, inference, postprocess" in lines
    assert "redetect_trigger  (previous_keypoints: keypoints (optional), previous_boxes: boxes (optional)) -> (redetect: flag)  spans: run" in lines
    assert "flag_when  (value: boxes|keypoints) -> (flag: flag)  spans: run" in lines
    assert "merge  (body: keypoints, left_hand: keypoints (optional), right_hand: keypoints (optional), face: keypoints (optional)) -> (keypoints: keypoints)  spans: run" in lines
    assert "  param max_instances: int, default 1" in lines
    assert cli.main(["nodes", "--json"]) == 0
    nodes = json.loads(capsys.readouterr().out)
    assert [node["type"] for node in nodes] == names
    assert set(nodes[0]) == {"type", "section", "inputs", "outputs", "any_from", "timing_spans", "params", "params_schema"}
    for node in nodes:
        assert list(node["params_schema"]["properties"]) == [param["name"] for param in node["params"]]
        assert node["params_schema"]["additionalProperties"] is False
    assert {node["type"]: node["any_from"] for node in nodes if node["any_from"]} == {"gate": ["value"], "first_of": ["*"]}
    smooth_boxes = next(node for node in nodes if node["type"] == "smooth_boxes")
    assert smooth_boxes["params_schema"]["properties"]["filter"]["enum"] == ["ema", "one_euro"]


# ---------------------------------------------------------------------------------------------
# `python -m skellytracker`
# ---------------------------------------------------------------------------------------------


def test_main_gives_run_validate_and_nodes_to_the_pipeline_cli(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    for arguments, code in ((["nodes", "--json"], 0), (["validate", "nothing@nowhere"], 2), (["run"], 2)):
        monkeypatch.setattr(sys, "argv", ["skellytracker", *arguments])
        with pytest.raises(SystemExit) as stop:
            entry.cli_main()
        assert stop.value.code == code
    capsys.readouterr()


def test_main_with_pipeline_runs_the_pipeline_demo_and_without_it_keeps_the_old_demo(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seen: dict[str, Any] = {}
    monkeypatch.setattr(cli, "demo_main", lambda pipeline, **options: seen.update(options, pipeline=pipeline) or 0)
    monkeypatch.setattr(sys, "argv", ["skellytracker", "--pipeline", "a@b", "--camera", "2", "--rotate", "90", "--ep", "cpu", "--ep-option", "x=y", "--device", "gpu:0",
                                      "--cpu-threads", "3"])
    with pytest.raises(SystemExit) as stop:
        entry.cli_main()
    assert stop.value.code == 0
    assert seen == {"pipeline": "a@b", "camera": 2, "rotation": 90, "ep": "cpu", "ep_option": ["x=y"], "device": ["gpu:0"], "cpu_threads": 3}

    built: list[tuple] = []
    old_demo = SimpleNamespace(run_webcam=lambda **options: built.append(("webcam", options)))
    monkeypatch.setattr(entry, "_build_demo", lambda tracker: built.append(("build", tracker)) or old_demo)
    monkeypatch.setattr(sys, "argv", ["skellytracker"])
    entry.cli_main()
    assert built == [("build", "mediapipe"), ("webcam", {"camera_index": 0, "rotation": 0})]
    monkeypatch.setattr(sys, "argv", ["skellytracker", "--list"])
    entry.cli_main()
    assert capsys.readouterr().out.split() == ["mediapipe", "rtmpose", "aruco", "charuco"]
    monkeypatch.setattr(sys, "argv", ["skellytracker", "--ep", "cpu"])  # an EP flag is only for a pipeline
    with pytest.raises(SystemExit) as stop:
        entry.cli_main()
    assert stop.value.code == 2 and "need --pipeline" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------------
# The webcam demo of a pipeline
# ---------------------------------------------------------------------------------------------


class FakeCapture:
    """A camera that gives the same frame. The patched `cv2.waitKey` ends the loop."""

    opened = True
    frame: np.ndarray | None = None
    made: list[FakeCapture] = []

    def __init__(self, index: int) -> None:
        self.index, self.released, self.reads = index, False, 0
        FakeCapture.made.append(self)

    def isOpened(self) -> bool:  # noqa: N802 (the name of cv2)
        return self.opened

    def set(self, name: int, value: float) -> bool:
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        self.reads += 1
        return self.frame is not None, self.frame

    def release(self) -> None:
        self.released = True


@pytest.fixture
def window(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Patch the camera and the window of cv2. The key q comes at the third `waitKey` call."""
    seen: dict[str, Any] = {"shown": [], "keys": [-1, -1, ord("q")], "destroyed": 0}
    FakeCapture.made, FakeCapture.opened, FakeCapture.frame = [], True, np.zeros((24, 32, 3), np.uint8)
    monkeypatch.setattr(cv2, "VideoCapture", FakeCapture)
    monkeypatch.setattr(cv2, "imshow", lambda title, shown: seen["shown"].append(shown))
    monkeypatch.setattr(cv2, "waitKey", lambda delay: seen["keys"].pop(0))
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda: seen.update(destroyed=seen["destroyed"] + 1))
    return seen


def test_the_demo_runs_the_built_in_mediapipe_pipeline_in_live_mode_until_the_key_q(
    test_image: np.ndarray, window: dict[str, Any], monkeypatch: pytest.MonkeyPatch, no_recommend: None,
) -> None:
    pytest.importorskip("mediapipe", reason="mediapipe not installed")
    FakeCapture.frame = test_image
    runs, frames = [], []
    real_start = cli.start_pipeline

    def start(config: Any, **parameters: Any) -> Any:
        runs.append((real_start(config, **parameters), parameters))
        real_process = runs[0][0].process
        monkeypatch.setattr(runs[0][0], "process", lambda frame: frames.append(frame) or real_process(frame))
        return runs[0][0]

    monkeypatch.setattr(cli, "start_pipeline", start)
    assert cli.demo_main("mediapipe-holistic-tasks@skellytracker", camera=3, rotation=0, ep=None, ep_option=None, device=None) == 0
    ((run, parameters),) = runs
    assert (parameters["camera_ids"], parameters["running_mode"], parameters["execution_provider"]) == ([3], "live", None)
    assert [frame.frame_index for frame in frames] == [0, 1, 2]
    times = [frame.timestamp_ms for frame in frames]
    assert all(isinstance(value, float) for value in times) and times[0] < times[1] < times[2]
    assert len(window["shown"]) == 3 and window["shown"][0].shape == test_image.shape
    assert (window["shown"][0] != test_image).any()  # the generic annotator drew the points
    (capture,) = FakeCapture.made
    assert (capture.index, capture.released, window["destroyed"]) == (3, True, 1) and run._executor.closed


def test_the_demo_rotates_the_frame_uses_the_recommended_ep_and_stops_when_the_camera_gives_no_frame(
    tmp_path: Path, root: Path, window: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(catalog.USER_ROOT_VARIABLE, str(root))  # the demo CLI has no user root flag
    forms = recommend_cpu(monkeypatch)
    seen = spy_start(monkeypatch, "start_pipeline")
    window["keys"] = [-1] * 9
    real_read = FakeCapture.read
    monkeypatch.setattr(FakeCapture, "read", lambda self: real_read(self) if self.reads < 2 else (False, None))
    assert cli.demo_main(pipeline_file(tmp_path), camera=0, rotation=90, ep=None, ep_option=["a=1"], device=["gpu:0"]) == 0
    assert forms == ["performance"] and "Execution provider: cpu" in capsys.readouterr().out
    assert (seen["execution_provider"], seen["ep_options"], seen["device"], seen["running_mode"]) == ("cpu", {"a": "1"}, ["gpu:0"], "live")
    assert [frame.image.shape for frame in seen["run"].frames] == [(32, 24, 3)] * 2  # 24 x 32 turned by 90 degrees
    assert seen["run"].closed and FakeCapture.made[0].released


def test_the_demo_closes_the_run_and_exits_with_the_code_of_the_error(window: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    FakeCapture.opened = False
    seen = spy_start(monkeypatch, "start_pipeline")
    assert cli.demo_main("mediapipe-holistic-tasks@skellytracker", camera=7, rotation=0, ep=None, ep_option=None, device=None) == 1
    assert "Could not open camera at index 7" in capsys.readouterr().err
    assert seen["run"].closed and FakeCapture.made[0].released and window["destroyed"] == 1
    spy_start(monkeypatch, "start_pipeline", error=errors.EpUnavailableError("The EP is not installed."))
    assert cli.demo_main("mediapipe-holistic-tasks@skellytracker", camera=0, rotation=0, ep=None, ep_option=None, device=None) == 3
    assert len(FakeCapture.made) == 1  # the start failed, so the demo opened no camera
    assert cli.demo_main("mediapipe-holistic-tasks@skellytracker", camera=0, rotation=0, ep=None, ep_option=["bad"], device=None) == 2
