"""The taps of a run (`_runtime/taps.py`): a record, then a replay in the COCO input form, on generated ONNX models."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

pytest.importorskip("onnx", reason="onnx not installed")

from skellytracker.core.pipelines import Frame, load_pipeline, timing  # noqa: E402
from skellytracker.core.pipelines.run import _start  # noqa: E402
from skellytracker.tests.pipelines.pipeline_models import detector_pipeline, image, isolate, tracking_pipeline, write_models  # noqa: E402
from skellytracker.tests.pipelines.test_sessions import MEDIAPIPE  # noqa: E402

IMAGE_IDS = [11, 5, 7]
VALUES = (1, 0, 2)  # the second image is dark: the detector finds nobody
RECORDS = [
    {"action": "record", "port": "person.rois", "name": "rois"},
    {"action": "record", "port": "person.detections", "name": "boxes"},
    {"action": "record", "port": "body.keypoints", "name": "points"},
]


@pytest.fixture(autouse=True)
def private_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    isolate(monkeypatch, tmp_path)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return write_models(tmp_path / "user", graphs=True)


def start(root: Path, data: dict[str, Any], **parameters: Any):
    parameters.setdefault("camera_ids", [0])
    parameters.setdefault("running_mode", "video")
    return _start(load_pipeline(data, user_root=root), user_root=root, **parameters)


def run_frames(run: Any) -> list[dict]:
    with run:
        return [run.process(Frame(image(value), index)) for index, value in enumerate(VALUES)]


def record_config(**person_params: Any) -> dict[str, Any]:
    return {**detector_pipeline(max_instances=2, **person_params), "instrumentation": {"taps": RECORDS}}


def replay_config(port: str = "person.rois", name: str = "rois", **person_params: Any) -> dict[str, Any]:
    """Return a config that replays one port of `person`. Its outputs need no port of `person` that is not replayed."""
    data = detector_pipeline(max_instances=2, **person_params)
    data["outputs"] = {"body": "body.keypoints", "person_roi": "person.rois"} if port == "person.rois" else {"person_box": "person.detections"}
    data["instrumentation"] = {"taps": [{"action": "replay", "port": port, "name": name}]}
    return data


@pytest.fixture
def taps(root: Path, tmp_path: Path) -> Path:
    """A tap folder with the three record taps of a run in the COCO input form."""
    run_frames(start(root, record_config(), image_ids=IMAGE_IDS, tap_dir=tmp_path / "taps"))
    return tmp_path / "taps"


def lines_of(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_lines(path: Path, lines: list[dict]) -> None:
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


def edit_manifest(folder: Path, change: Any) -> None:
    manifest = json.loads((folder / "tap.json").read_text(encoding="utf-8"))
    change(manifest)
    (folder / "tap.json").write_text(json.dumps(manifest), encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------------------------


def test_a_record_tap_writes_one_line_for_each_present_row_with_image_id_frame_index_camera_id_and_row(root: Path, taps: Path) -> None:
    rois = lines_of(taps / "rois" / "roi.jsonl")
    # The images 11 and 7 have two rows each. The dark image 5 has no line.
    assert [(line["image_id"], line["frame_index"], line["camera_id"], line["row"]) for line in rois] == [(11, 0, 0, 0), (11, 0, 0, 1), (7, 2, 0, 0), (7, 2, 0, 1)]
    assert rois[0]["roi"] == [6.0, 6.0, 8.0, 8.0, 0.0] and rois[0]["score"] == pytest.approx(0.9)  # `score` is the instance score
    boxes = lines_of(taps / "boxes" / "detections.jsonl")
    assert set(boxes[0]) == {"image_id", "frame_index", "camera_id", "row", "class", "bbox", "score"}
    assert (boxes[0]["class"], boxes[0]["bbox"]) == ("person", [2.0, 2.0, 8.0, 8.0])  # `class` in place of `category_id`; bbox is x, y, w, h
    assert [line["score"] for line in boxes] == pytest.approx([0.9, 0.75, 1.8, 1.5])
    points = lines_of(taps / "points" / "keypoints.jsonl")
    assert len(points) == 4 and points[1]["score"] == pytest.approx(0.75)  # the instance score of the row, with no rescoring
    assert points[0]["keypoints"][:3] == pytest.approx([6.0, 6.0, 3.0]) and points[0]["keypoints"][6:] == [None, None, 0.0]  # a missing point


def test_tap_json_has_each_field_of_the_spec_and_is_written_last_through_a_rename(root: Path, tmp_path: Path) -> None:
    run = start(root, record_config(), image_ids=IMAGE_IDS, tap_dir=tmp_path / "taps")
    run.process(Frame(image(1), 0))
    folder = tmp_path / "taps" / "boxes"
    assert [path.name for path in folder.iterdir()] == ["detections.jsonl"]  # no `tap.json`: a partial record
    run.close()
    assert sorted(path.name for path in folder.iterdir()) == ["detections.jsonl", "tap.json"]
    manifest = json.loads((folder / "tap.json").read_text(encoding="utf-8"))
    config = load_pipeline(record_config(), user_root=root)
    assert list(manifest) == [
        "schema", "skellytracker_version", "run_id", "port", "port_type", "point_names", "class_names", "geometry", "upstream_sha256",
        "nodes", "image_list_sha256", "camera_ids", "running_mode", "pipeline_sha256", "record_count",
    ]
    assert (manifest["schema"], manifest["port"], manifest["port_type"]) == ("skellytracker.tap/1", "person.detections", "detections")
    assert (manifest["class_names"], manifest["point_names"], manifest["geometry"]) == (["person"], None, None)
    assert manifest["upstream_sha256"] == timing.upstream_sha256(config, "person") and manifest["pipeline_sha256"] == timing.pipeline_sha256(config)
    assert manifest["image_list_sha256"] == timing.image_list_sha256(IMAGE_IDS)
    assert (manifest["camera_ids"], manifest["running_mode"], manifest["record_count"]) == ([0], "video", 2)
    (item,) = manifest["nodes"]  # the tapped node and its upstream nodes, as in the timing header
    assert tuple(item) == timing.NODE_ITEM_FIELDS and item["id"] == "person" and len(item["artifact_sha256"]) == 64 and item["execution"]["used_ep"] == "cpu"
    points = json.loads((tmp_path / "taps" / "points" / "tap.json").read_text(encoding="utf-8"))
    assert (points["point_names"], points["geometry"], points["class_names"]) == (["body/a", "body/b", "body/c"], "2d", None)
    assert [node["id"] for node in points["nodes"]] == ["body", "person"] and points["upstream_sha256"] == timing.upstream_sha256(config, "body")


def test_the_image_id_of_a_video_record_is_frame_index_times_the_camera_count_plus_the_camera_index(root: Path, tmp_path: Path) -> None:
    with start(root, record_config(), camera_ids=["a", "b"], tap_dir=tmp_path / "taps") as run:
        for index in (0, 3):
            run.process_batch({"a": Frame(image(1), index), "b": Frame(image(1), index)})
    lines = lines_of(tmp_path / "taps" / "rois" / "roi.jsonl")
    assert [(line["frame_index"], line["camera_id"], line["image_id"]) for line in lines if line["row"] == 0] == [(0, "a", 0), (0, "b", 1), (3, "a", 6), (3, "b", 7)]
    assert json.loads((tmp_path / "taps" / "rois" / "tap.json").read_text(encoding="utf-8"))["image_list_sha256"] is None


def test_v_pipeline_taps_2_a_run_of_a_file_with_a_tap_must_have_a_tap_folder(root: Path) -> None:
    with pytest.raises(ValueError, match="V-pipeline.taps-2"):
        start(root, record_config())


def test_v_pipeline_taps_5_a_record_tap_refuses_a_folder_that_is_not_empty(root: Path, taps: Path) -> None:
    with pytest.raises(ValueError, match="V-pipeline.taps-5.*rois"):
        start(root, record_config(), image_ids=IMAGE_IDS, tap_dir=taps)
    (taps / "empty" / "rois").mkdir(parents=True)  # a folder that exists and is empty is good
    start(root, record_config(), image_ids=IMAGE_IDS, tap_dir=taps / "empty").close()


@pytest.mark.parametrize(("data", "port", "match"), [
    (tracking_pipeline(), "trigger.image", "of the type image"),
    (MEDIAPIPE, "holistic.keypoints", "3d keypoints port"),
])
def test_a_start_refuses_a_tap_of_a_port_whose_file_form_no_text_fixes(root: Path, tmp_path: Path, data: dict, port: str, match: str) -> None:
    data = {**data, "instrumentation": {"taps": [{"action": "record", "port": port, "name": "tap"}]}}
    with pytest.raises(ValueError, match=match):
        start(root, data, tap_dir=tmp_path / "taps", running_mode="video")


# ---------------------------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------------------------


def test_a_replay_puts_each_line_in_its_row_and_the_replayed_node_does_not_run(root: Path, tmp_path: Path) -> None:
    recorded = run_frames(start(root, record_config(), image_ids=IMAGE_IDS, tap_dir=tmp_path / "taps"))
    run = start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=tmp_path / "taps")
    assert "person" not in run._executor.models and len(run._executor.sessions.opened) == 1  # no session for the replayed node
    replayed = run_frames(run)
    for before, after in zip(recorded, replayed, strict=True):
        # `node_ran` is false for the replayed node. `body` runs on the replayed ROIs, and not on the image with no row.
        assert after["node_ran"] == {"person": False, "body": before["node_ran"]["body"]}
        np.testing.assert_array_equal(after["person_roi"].rois, before["person_roi"].rois)
        np.testing.assert_array_equal(after["person_roi"].instance_score, before["person_roi"].instance_score)
        np.testing.assert_array_equal(after["person_roi"].present, before["person_roi"].present)
        np.testing.assert_array_equal(after["body"].xy, before["body"].xy)
        np.testing.assert_array_equal(after["body"].instance_score, before["body"].instance_score)
    assert [result["node_ran"]["body"] for result in replayed] == [True, False, True]


def test_a_replay_of_detections_gets_the_class_index_from_the_class_name_and_a_keypoints_replay_gives_the_points(root: Path, taps: Path) -> None:
    (first, dark, _) = run_frames(start(root, replay_config("person.detections", "boxes"), image_ids=IMAGE_IDS, tap_dir=taps))
    assert first["person_box"].class_index.tolist() == [0, 0] and first["person_box"].present.tolist() == [True, True]
    np.testing.assert_allclose(first["person_box"].xyxy, [[2, 2, 10, 10], [20, 20, 30, 30]])
    np.testing.assert_allclose(first["person_box"].score, [0.9, 0.75], rtol=1e-6)
    assert first["node_ran"] == {"person": False, "body": False} and not dark["person_box"].present.any()
    data = detector_pipeline(max_instances=2)
    data["outputs"] = {"body": "body.keypoints"}
    data["instrumentation"] = {"taps": [{"action": "replay", "port": "body.keypoints", "name": "points"}]}
    run = start(root, data, image_ids=IMAGE_IDS, tap_dir=taps)
    assert run._executor.sessions.opened == {}  # the upstream nodes of the replayed port do not run
    (points, _, _) = run_frames(run)
    np.testing.assert_allclose(points["body"].xy[:, 0], [[6, 6], [25, 25]])
    assert np.isnan(points["body"].xy[:, 2]).all() and points["body"].score.tolist() == [[3, 2, 0], [3, 2, 0]]
    assert points["node_ran"] == {"person": False, "body": False}


def test_v_pipeline_running_5_a_node_that_runs_must_have_no_replayed_output_port(root: Path, taps: Path) -> None:
    data = replay_config()
    data["outputs"]["person_box"] = "person.detections"  # `person` must run for this output, and its port `rois` is replayed
    with pytest.raises(ValueError, match="V-pipeline.running-5: the node person runs, but its output port person.rois is replayed"):
        start(root, data, image_ids=IMAGE_IDS, tap_dir=taps)


def test_v_pipeline_taps_3_a_replay_refuses_a_tap_with_no_tap_json_and_a_tap_with_a_null_image_list(root: Path, tmp_path: Path, taps: Path) -> None:
    (taps / "rois" / "tap.json").rename(taps / "rois" / "tap.json.away")
    with pytest.raises(ValueError, match="V-pipeline.taps-3.*has no tap.json"):
        start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps)
    with pytest.raises(ValueError, match="V-pipeline.taps-3.*has no tap.json"):
        start(root, replay_config(name="absent"), image_ids=IMAGE_IDS, tap_dir=taps)
    run_frames(start(root, record_config(), tap_dir=tmp_path / "video"))  # a record with no COCO input
    for image_ids in (IMAGE_IDS, None):
        with pytest.raises(ValueError, match="V-pipeline.taps-3.*image_list_sha256: null"):
            start(root, replay_config(), image_ids=image_ids, tap_dir=tmp_path / "video")


@pytest.mark.parametrize(("parameters", "person_params", "field"), [
    ({"image_ids": [11, 5, 8]}, {}, "image_list_sha256"),
    ({"image_ids": None}, {}, "image_list_sha256"),
    ({"camera_ids": [1]}, {}, "camera_ids"),
    ({"running_mode": "image"}, {}, "running_mode"),
    ({}, {"object_decode": {"min_score": 0.5}}, "upstream_sha256"),
])
def test_v_pipeline_taps_3_a_replay_refuses_a_tap_that_does_not_agree_with_the_run(
    root: Path, taps: Path, parameters: dict, person_params: dict, field: str,
) -> None:
    with pytest.raises(ValueError, match=f"V-pipeline.taps-3.*does not agree with the run in `{field}`"):
        start(root, replay_config(**person_params), **{"image_ids": IMAGE_IDS, "tap_dir": taps, **parameters})


@pytest.mark.parametrize(("change", "field"), [
    (lambda manifest: manifest.update(schema="skellytracker.tap/0"), "schema"),
    (lambda manifest: manifest.update(port="person.detections"), "port"),
    (lambda manifest: manifest.update(port_type="detections"), "port_type"),
    (lambda manifest: manifest["nodes"][0].update(sidecar_sha256="0" * 64), "sidecar_sha256` of the node person"),
    (lambda manifest: manifest["nodes"][0].update(artifact_sha256="0" * 64), "artifact_sha256` of the node person"),
    (lambda manifest: manifest["nodes"][0]["execution"].update(used_ep="cuda"), "used_ep` of the node person"),
])
def test_v_pipeline_taps_3_a_replay_compares_each_match_field_of_tap_json(root: Path, taps: Path, change: Any, field: str) -> None:
    edit_manifest(taps / "rois", change)
    with pytest.raises(ValueError, match=f"V-pipeline.taps-3.*does not agree with the run in `{field}"):
        start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps)


def test_a_replay_takes_a_tap_whose_information_fields_differ(root: Path, taps: Path) -> None:
    def change(manifest: dict) -> None:
        manifest.update(pipeline_sha256="0" * 64, run_id="other", skellytracker_version="0.0.0")
        manifest["nodes"][0]["execution"].update(device="gpu:7", gpu_uuid="GPU-x")

    edit_manifest(taps / "rois", change)
    start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps).close()


@pytest.mark.parametrize("change", [{"frame_index": 9}, {"camera_id": 1}, {"image_id": 5}])
def test_v_pipeline_taps_4_a_replay_refuses_a_line_of_an_image_that_is_not_an_image_of_the_run(root: Path, taps: Path, change: dict) -> None:
    lines = lines_of(taps / "rois" / "roi.jsonl")
    lines[-1].update(change)
    write_lines(taps / "rois" / "roi.jsonl", lines)
    with pytest.raises(ValueError, match="V-pipeline.taps-4.*line 4"):
        start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps)
    (taps / "rois" / "roi.jsonl").unlink()
    with pytest.raises(ValueError, match="V-pipeline.taps-4.*no file roi.jsonl"):
        start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps)


@pytest.mark.parametrize(("edit", "match"), [
    (lambda lines: lines[0].update(row=2), r"line 1: `row` is 2; it must be an integer in \[0, 2\)"),
    (lambda lines: lines[0].update(row=-1), "line 1: `row` is -1"),
    (lambda lines: lines[0].update(row="0"), "line 1: `row` is '0'"),
    (lambda lines: lines[0].update(row=True), "line 1: `row` is True"),
    (lambda lines: lines[1].update(row=0), "line 2: the row 0 occurs twice"),
    (lambda lines: lines.pop(0), "the rows of the frame 0 of the camera 0 are not 0 to 0; the node person is an instance source"),
])
def test_v_pipeline_taps_6_a_replay_refuses_a_bad_row(root: Path, taps: Path, edit: Any, match: str) -> None:
    lines = lines_of(taps / "rois" / "roi.jsonl")
    edit(lines)
    write_lines(taps / "rois" / "roi.jsonl", lines)
    with pytest.raises(ValueError, match="V-pipeline.taps-6.*" + match):
        start(root, replay_config(), image_ids=IMAGE_IDS, tap_dir=taps)


def test_v_pipeline_taps_6_a_port_of_a_fan_out_child_can_have_a_padding_row_before_a_present_row(root: Path, taps: Path) -> None:
    lines = lines_of(taps / "points" / "keypoints.jsonl")
    write_lines(taps / "points" / "keypoints.jsonl", lines[1:])  # image 11 keeps only its row 1; `body` is not an instance source
    data = detector_pipeline(max_instances=2)
    data["outputs"] = {"body": "body.keypoints"}
    data["instrumentation"] = {"taps": [{"action": "replay", "port": "body.keypoints", "name": "points"}]}
    (first, _, _) = run_frames(start(root, data, image_ids=IMAGE_IDS, tap_dir=taps))
    assert first["body"].present.tolist() == [False, True] and first["body"].instance_score.tolist() == pytest.approx([0.0, 0.75])


@pytest.mark.parametrize("name", ["cat", None])
def test_v_pipeline_taps_7_a_replay_refuses_a_detections_line_with_an_unknown_class(root: Path, taps: Path, name: Any) -> None:
    lines = lines_of(taps / "boxes" / "detections.jsonl")
    lines[2]["class"] = name
    write_lines(taps / "boxes" / "detections.jsonl", lines)
    with pytest.raises(ValueError, match=r"V-pipeline.taps-7.*line 3: the class .* is not a name of the class names \['person'\]"):
        start(root, replay_config("person.detections", "boxes"), image_ids=IMAGE_IDS, tap_dir=taps)
