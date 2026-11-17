"""Tests of the timing module (pipeline.timing; `upstream_sha256` of pipeline.taps)."""
import copy
import hashlib
import io
import json

import pytest

from skellytracker.core.pipelines import timing
from skellytracker.core.pipelines.config import PipelineConfig

CONFIG = {
    "schema_version": "2.0.0",
    "pipeline_id": "test",
    "source": {"name": "test", "version": "1"},
    "nodes": [
        {"id": "trigger", "type": "redetect_trigger", "inputs": {"image": "frame.image", "previous_keypoints": "wholebody.keypoints@prev"}},
        {"id": "person", "type": "onnx_model", "inputs": {"image": "trigger.image"}, "params": {"key": "yolox-person@x", "size": "m"}},
        {"id": "crop", "type": "smooth_boxes", "inputs": {"boxes": "person.boxes"}},
        {"id": "wholebody", "type": "onnx_model", "inputs": {"image": "frame.image", "boxes": "crop.boxes"}, "params": {"key": "rtmw@x", "size": "m"}},
        {"id": "hands", "type": "mediapipe_tasks", "inputs": {"image": "frame.image"}, "params": {"variant": "hand"}},
        {"id": "both", "type": "concat", "inputs": ["wholebody.keypoints", "hands.keypoints"]},
    ],
    "outputs": {"wholebody": "wholebody.keypoints", "hands": "hands.keypoints"},
    "instrumentation": {"timing_spans": ["pipeline.run", "wholebody.inference"]},
}
EXECUTION = {
    "requested_ep": "cuda", "used_ep": "cuda", "device": "gpu0", "gpu_uuid": "GPU-1", "ep_device_id": "0",
    "ep_options": {}, "cpu_nodes": 2, "cpu_op_types": ["Resize"],
}


def config(**changes) -> PipelineConfig:
    data = copy.deepcopy(CONFIG)
    data.update(changes)
    return PipelineConfig.model_validate(data)


def node_items(cfg: PipelineConfig) -> list[dict]:
    return [timing.make_node_item(node) for node in cfg.nodes]


def test_canonical_json_bytes():
    assert timing.canonical_json({"b": [1, 2.5, None, True], "a": "é"}) == '{"a":"é","b":[1,2.5,null,true]}'.encode()


def test_pipeline_sha256_hashes_only_schema_version_nodes_and_outputs():
    cfg = config()
    dump = cfg.model_dump(mode="json", exclude={"nodes": {"__all__": {"description"}}})
    expected = hashlib.sha256(timing.canonical_json({key: dump[key] for key in ("schema_version", "nodes", "outputs")})).hexdigest()
    assert timing.pipeline_sha256(cfg) == expected
    same = config(pipeline_id="other", description="text", source={"name": "other", "version": "2"}, instrumentation={})
    assert timing.pipeline_sha256(same) == expected
    assert timing.pipeline_sha256(config(outputs={"wholebody": "wholebody.keypoints"})) != expected
    described = copy.deepcopy(CONFIG)
    described["nodes"][0]["description"] = "Text for people.\nThe run does not read it."
    assert timing.pipeline_sha256(PipelineConfig.model_validate(described)) == expected  # a node description is not in a hash


def test_pipeline_sha256_uses_the_defaults_of_the_spec():
    written = copy.deepcopy(CONFIG)
    written["nodes"][2]["params"] = {"filter": "ema"}  # the default, written
    assert timing.pipeline_sha256(PipelineConfig.model_validate(written)) == timing.pipeline_sha256(config())


def test_upstream_sha256_holds_the_upstream_nodes_also_through_prev():
    cfg = config()
    nodes = {node["id"]: node for node in cfg.model_dump(mode="json", exclude={"nodes": {"__all__": {"description"}}})["nodes"]}
    upstream = [nodes[node_id] for node_id in ("crop", "person", "trigger", "wholebody")]  # sorted by node id
    expected = hashlib.sha256(timing.canonical_json(upstream)).hexdigest()
    # `person` reads `trigger`, and `trigger` reads `wholebody` through `@prev`.
    assert timing.upstream_sha256(cfg, "person") == timing.upstream_sha256(cfg, "wholebody") == expected
    assert timing.upstream_sha256(cfg, "hands") == hashlib.sha256(timing.canonical_json([nodes["hands"]])).hexdigest()
    changed = copy.deepcopy(CONFIG)
    changed["nodes"][4]["params"]["max_instances"] = 2  # `hands` is not upstream of `person`
    assert timing.upstream_sha256(PipelineConfig.model_validate(changed), "person") == expected
    changed["nodes"][0]["description"] = "a new text"
    assert timing.upstream_sha256(PipelineConfig.model_validate(changed), "person") == expected
    with pytest.raises(ValueError, match="names no node"):
        timing.upstream_sha256(cfg, "frame")


def test_image_list_sha256():
    assert timing.image_list_sha256([10, 9, 139]) == hashlib.sha256(b"9\n10\n139").hexdigest()


def test_event_fields_and_derive_helpers():
    event = timing.make_event([(3, "cam0"), (3, "cam1")], "wholebody", "inference", 1_000_000, 3_500_000)
    assert tuple(event) == timing.EVENT_FIELDS
    assert event["images"] == [{"frame_index": 3, "camera_id": "cam0"}, {"frame_index": 3, "camera_id": "cam1"}]
    assert event["batch_size"] == 2
    assert timing.task_ids(event) == ["3:cam0:wholebody:inference", "3:cam1:wholebody:inference"]
    assert timing.duration_ms(event) == 2.5


def test_node_item_fields():
    cfg = config()
    item = timing.make_node_item(
        cfg.nodes[3], batching={"batch": 3}, sidecar_sha256="a" * 64, artifact_sha256="b" * 64, precision="fp16",
        execution=EXECUTION, stage_providers={"preprocess": None, "inference": "cuda", "postprocess": None}, shared_with=["other"],
    )
    assert tuple(item) == timing.NODE_ITEM_FIELDS
    assert (item["id"], item["type"], item["key"], item["size"], item["precision"]) == ("wholebody", "onnx_model", "rtmw@x", "m", "fp16")
    assert item["inputs"] == [{"name": "image", "port": "frame.image", "prev": False}, {"name": "boxes", "port": "crop.boxes", "prev": False}]
    assert tuple(item["execution"]) == timing.EXECUTION_FIELDS
    trigger = timing.make_node_item(cfg.nodes[0])
    assert trigger["inputs"][1] == {"name": "previous_keypoints", "port": "wholebody.keypoints", "prev": True}
    assert (trigger["key"], trigger["execution"], trigger["shared_with"]) == (None, None, [])
    assert timing.make_node_item(cfg.nodes[5])["inputs"][0] == {"name": None, "port": "wholebody.keypoints", "prev": False}
    with pytest.raises(ValueError, match="execution"):
        timing.make_node_item(cfg.nodes[3], execution={"used_ep": "cuda"})


def test_header_fields():
    cfg = config()
    header = timing.make_header(cfg, run_id="run-1", running_mode="video", warmup_passes=2, camera_ids=["cam0"], nodes=node_items(cfg))
    assert tuple(header) == timing.HEADER_FIELDS
    assert header["schema"] == "skellytracker.timing/1"
    assert header["clock"]["name"] == "perf_counter_ns"
    assert set(header["clock"]) == {"name", "implementation", "resolution_ns"}
    assert isinstance(header["clock"]["resolution_ns"], int)
    assert set(header["anchor"]) == {"perf_counter_ns", "unix_ns"}
    assert header["image_list_sha256"] is None
    assert header["pipeline_sha256"] == timing.pipeline_sha256(cfg)
    assert header["spans_on"] == ["pipeline.run", "wholebody.inference"]
    assert [item["id"] for item in header["nodes"]] == [node.id for node in cfg.nodes]
    assert "mode" not in header
    json.dumps(header)
    off = timing.make_header(cfg, run_id="r", running_mode="image", warmup_passes=0, camera_ids=[0], nodes=node_items(cfg), spans_on=[])
    assert off["spans_on"] == []
    with pytest.raises(ValueError, match="node item"):
        timing.make_header(cfg, run_id="r", running_mode="image", warmup_passes=0, camera_ids=[0], nodes=[{"id": "x"}])


def run_records() -> list[dict]:
    """Two frames of one camera: the pipeline span, the spans of `wholebody`, `hands` and one glue node."""
    cfg = config()
    records = [timing.make_header(cfg, run_id="r", running_mode="image", warmup_passes=1, camera_ids=[0], nodes=node_items(cfg))]
    for frame in (0, 1):
        images = [(frame, 0)]
        records += [
            timing.make_event(images, "wholebody", "preprocess", 0, 1_000_000),
            timing.make_event(images, "wholebody", "inference", 0, 4_000_000),
            timing.make_event(images, "wholebody", "postprocess", 0, 2_000_000),
            timing.make_event(images, "crop", "run", 0, 500_000),
            timing.make_event(images, "pipeline", "run", 0, 10_000_000),
        ]
    return records


def test_writer_writes_the_header_first_then_one_line_for_each_event(tmp_path):
    records = run_records()
    path = tmp_path / "timing.jsonl"
    received: list[dict] = []
    text = io.StringIO()
    for sink in (path, received.append, text):
        writer = timing.TimingWriter(sink)
        writer.write_header(records[0])
        for event in records[1:]:
            writer.write_event(event)
        writer.close()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(records)
    assert json.loads(lines[0])["schema"] == "skellytracker.timing/1"
    assert timing.read_timing(path) == received == records
    assert text.getvalue() == path.read_text(encoding="utf-8")
    assert timing.skellybench_timing(path) == timing.skellybench_timing(records)


def test_skellybench_timing_record():
    record = timing.skellybench_timing(run_records())
    assert record["stages_ms_per_image"] == {"preprocess": 1.0, "inference": 4.0, "postprocess": 2.0}
    assert record["excluded_ms_per_image"] == {"glue": 0.5}
    assert record["ms_per_image"] == 10.0
    assert record["images_per_second"] == 100.0
    assert "stage_providers" not in record


def test_skellybench_timing_divides_by_the_sum_of_batch_size():
    cfg = config()
    header = timing.make_header(cfg, run_id="r", running_mode="video", warmup_passes=0, camera_ids=[0, 1], nodes=node_items(cfg))
    batch = timing.make_event([(0, 0), (0, 1), (1, 0)], "hands", "run", 0, 6_000_000)
    record = timing.skellybench_timing([header, batch])
    # The `run` span of a `mediapipe_tasks` node is a model span.
    assert record["stages_ms_per_image"] == {"preprocess": None, "inference": 2.0, "postprocess": None}
    assert record["images_per_second"] == 500.0
    assert "ms_per_image" not in record and "excluded_ms_per_image" not in record
    with pytest.raises(ValueError, match="no time"):
        timing.skellybench_timing([header])


def test_the_times_of_a_node_with_a_session_on_each_of_two_gpus_are_the_times_of_all_its_sessions_together():
    cfg = config()
    header = timing.make_header(cfg, run_id="r", running_mode="video", warmup_passes=1, camera_ids=[0, 1, 2], nodes=node_items(cfg))
    # One call: the session of the first GPU runs two cameras, and the session of the second GPU runs one camera.
    first = timing.make_event([(0, 0), (0, 1)], "wholebody", "inference", 0, 8_000_000)
    second = timing.make_event([(0, 2)], "wholebody", "inference", 8_000_000, 12_000_000)
    record = timing.skellybench_timing([header, first, second])
    assert record["stages_ms_per_image"]["inference"] == 4.0  # (8 ms + 4 ms) / 3 images: no part for each GPU


def test_skellybench_timing_passes_the_skellybench_schema():
    schema = pytest.importorskip("skellybench.schema")
    record = timing.skellybench_timing(run_records())
    stages = dict.fromkeys((*timing.STAGES, timing.GLUE_STAGE), "text")
    protocol = {"excluded_stages": [timing.GLUE_STAGE], "stage_definitions": {"host": stages}}
    schema.validate_timing(record, mode="host", protocol=protocol)
