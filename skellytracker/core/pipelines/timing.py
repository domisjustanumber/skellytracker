"""The timing of a pipeline run: the events, the header, the hashes, the JSONL writer and the helpers.

Implements: pipeline.timing

An event is one measured span of one node on one call. A timing file is JSONL: a header line, then
one line for each event. The helpers `task_ids`, `duration_ms` and `skellybench_timing` are for use
outside the hot path.

The form of an event::

    {"images": [{"frame_index": int, "camera_id": int | str}, ...], "node_id": str, "span": str,
     "batch_size": int, "start_ns": int, "end_ns": int}

The form of a header is in `make_header`. The form of a node item is in `make_node_item`.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from skellytracker.core.pipelines.config import FRAME, PORT_REF, RESERVED_NODE_ID, PipelineConfig, input_items

TIMING_SCHEMA = "skellytracker.timing/1"
EVENT_FIELDS = ("images", "node_id", "span", "batch_size", "start_ns", "end_ns")
HEADER_FIELDS = (
    "schema", "run_id", "skellytracker_version", "clock", "anchor", "running_mode", "warmup_passes",
    "image_list_sha256", "camera_ids", "pipeline_sha256", "spans_on", "jpeg_decode", "nodes",
)
JPEG_DECODE_PLACES = ("gpu", "cpu", "mixed")
NODE_ITEM_FIELDS = (
    "id", "type", "batching", "inputs", "key", "sidecar_sha256", "artifact_sha256", "size", "precision",
    "execution", "stage_providers", "shared_with",
)
EXECUTION_FIELDS = ("requested_ep", "used_ep", "device", "gpu_uuid", "ep_device_id", "ep_options", "cpu_nodes", "cpu_op_types", "cpu_threads")
# The stages of the skellybench timing record.
STAGES = ("preprocess", "inference", "postprocess")
# The key of the glue time in `excluded_ms_per_image`.
GLUE_STAGE = "glue"
# The node types whose spans are model spans. Each other node type is a glue node.
MODEL_NODE_TYPES = ("onnx_model", "mediapipe_tasks")

TimingSink = str | Path | io.TextIOBase | Callable[[dict], None]


def canonical_json(value: Any) -> bytes:
    """Return the canonical JSON of `value`: UTF-8, sorted keys, no whitespace, no ASCII escape."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def pipeline_sha256(config: PipelineConfig) -> str:
    """Return the hash of `schema_version`, `nodes` and `outputs` of the config, with the defaults and with no node `description`."""
    dump = config.model_dump(mode="json", exclude={"nodes": {"__all__": {"description"}}})
    return _sha256({key: dump[key] for key in ("schema_version", "nodes", "outputs")})


def upstream_sha256(config: PipelineConfig, node_id: str) -> str:
    """Return the hash of the configs of `node_id` and of each node upstream of it, sorted by node id.

    An `@prev` input also counts as upstream. A node `description` is not in the hash.
    """
    nodes = {node["id"]: node for node in config.model_dump(mode="json", exclude={"nodes": {"__all__": {"description"}}})["nodes"]}
    if node_id not in nodes:
        raise ValueError(f"{node_id!r} names no node")
    found: set[str] = set()
    todo = [node_id]
    while todo:
        current = todo.pop()
        if current in found:
            continue
        found.add(current)
        inputs = nodes[current]["inputs"]
        refs = inputs if isinstance(inputs, list) else inputs.values()
        todo += [source for ref in refs if (source := ref.split(".")[0]) != FRAME]
    return _sha256([nodes[current] for current in sorted(found)])


def image_list_sha256(image_ids: Iterable[int]) -> str:
    """Return the hash of the `image_id` values of the COCO input form.

    The bytes are the values in ascending order, each as a decimal integer, joined with a line feed.
    """
    return hashlib.sha256("\n".join(str(int(image_id)) for image_id in sorted(image_ids)).encode("utf-8")).hexdigest()


def make_event(images: Sequence[tuple[int, int | str]], node_id: str, span: str, start_ns: int, end_ns: int) -> dict[str, Any]:
    """Return one event. `images` holds one `(frame_index, camera_id)` for each image of the call."""
    return {
        "images": [{"frame_index": frame_index, "camera_id": camera_id} for frame_index, camera_id in images],
        "node_id": node_id, "span": span, "batch_size": len(images), "start_ns": start_ns, "end_ns": end_ns,
    }


def make_node_item(
    node: Any,
    *,
    batching: Any = None,
    sidecar_sha256: str | None = None,
    artifact_sha256: str | None = None,
    precision: str | None = None,
    execution: Mapping[str, Any] | None = None,
    stage_providers: Mapping[str, str | None] | None = None,
    shared_with: Sequence[str] = (),
) -> dict[str, Any]:
    """Return the node item of one node config, for `nodes` of the header and of `tap.json`.

    `node` is a node of `PipelineConfig.nodes`. The item has exactly `NODE_ITEM_FIELDS`:

    - `id`, `type`: from the node.
    - `inputs`: one `{"name", "port", "prev"}` for each input. `name` is the input name, or null for
      an item of a variadic node. `port` is `<node>.<port>`. `prev` is true for an `@prev` input.
    - `key`, `size`: the params of the node, or null.
    - `sidecar_sha256`, `precision`: the resolved value that the caller gives, else the param, or null.
    - `artifact_sha256`: the SHA-256 of the ONNX file, or null.
    - `batching`: the batch of the session. The spec does not fix its form.
    - `execution`: null, or a mapping with exactly `EXECUTION_FIELDS`.
    - `stage_providers`: null, or `{preprocess, inference, postprocess}`, each an EP name or null.
    - `shared_with`: the ids of the other nodes of the run that use the same session.
    """
    if execution is not None and set(execution) != set(EXECUTION_FIELDS):
        raise ValueError(f"execution must have exactly the keys {list(EXECUTION_FIELDS)}")
    if stage_providers is not None and set(stage_providers) != set(STAGES):
        raise ValueError(f"stage_providers must have exactly the keys {list(STAGES)}")
    params = node.params.model_dump(mode="json")
    inputs = [
        {"name": None if isinstance(node.inputs, list) else name, "port": ref.removesuffix("@prev"), "prev": PORT_REF.match(ref)["prev"] is not None}
        for name, ref in input_items(node)
    ]
    return {
        "id": node.id, "type": node.type, "batching": batching, "inputs": inputs, "key": params.get("key"),
        "sidecar_sha256": sidecar_sha256 or params.get("sidecar_sha256"), "artifact_sha256": artifact_sha256,
        "size": params.get("size"), "precision": precision or params.get("precision"),
        "execution": None if execution is None else dict(execution),
        "stage_providers": None if stage_providers is None else dict(stage_providers),
        "shared_with": list(shared_with),
    }


def make_header(
    config: PipelineConfig,
    *,
    run_id: str,
    running_mode: str,
    warmup_passes: int,
    camera_ids: Sequence[int | str],
    nodes: Sequence[Mapping[str, Any]],
    image_list_sha256: str | None = None,
    spans_on: Sequence[str] | None = None,
    jpeg_decode: str = "cpu",
) -> dict[str, Any]:
    """Return the header line of a timing file, with exactly `HEADER_FIELDS`.

    `nodes` holds one node item for each node (`make_node_item`). `spans_on` is the list of the
    timing spans that are on. Its default is `instrumentation.timing_spans` of the config. The
    function reads the event clock and the Unix clock for `anchor`. `jpeg_decode` is the place of
    the JPEG decode at the start of the run, one of `JPEG_DECODE_PLACES`.
    """
    if jpeg_decode not in JPEG_DECODE_PLACES:
        raise ValueError(f"jpeg_decode must be one of {list(JPEG_DECODE_PLACES)}, not {jpeg_decode!r}")
    for item in nodes:
        if set(item) != set(NODE_ITEM_FIELDS):
            raise ValueError(f"a node item must have exactly the keys {list(NODE_ITEM_FIELDS)}")
    clock = time.get_clock_info("perf_counter")
    return {
        "schema": TIMING_SCHEMA,
        "run_id": run_id,
        "skellytracker_version": importlib.metadata.version("skellytracker"),
        "clock": {"name": "perf_counter_ns", "implementation": clock.implementation, "resolution_ns": round(clock.resolution * 1e9)},
        "anchor": {"perf_counter_ns": time.perf_counter_ns(), "unix_ns": time.time_ns()},
        "running_mode": running_mode,
        "warmup_passes": warmup_passes,
        "image_list_sha256": image_list_sha256,
        "camera_ids": list(camera_ids),
        "pipeline_sha256": pipeline_sha256(config),
        "spans_on": list(config.instrumentation.timing_spans if spans_on is None else spans_on),
        "jpeg_decode": jpeg_decode,
        "nodes": [dict(item) for item in nodes],
    }


class TimingWriter:
    """Write the header lines and the events of a run to a timing sink.

    The sink is a path, an open text file or a callable. A path gets a new JSONL file. A callable
    gets each header and each event as a dict.
    """

    def __init__(self, sink: TimingSink) -> None:
        self._file: Any = None
        self._owned = isinstance(sink, (str, Path))
        if self._owned:
            self._file = open(sink, "w", encoding="utf-8", newline="\n")  # noqa: SIM115 (`close` closes it)
        elif isinstance(sink, io.TextIOBase):
            self._file = sink
        self._send: Callable[[dict], None] = self._write_line if self._file is not None else sink  # type: ignore[assignment]

    def _write_line(self, record: dict) -> None:
        self._file.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")

    def write_header(self, header: dict) -> None:
        """Write a header. It applies to the events after it, until the next header."""
        self._send(header)

    def write_event(self, event: dict) -> None:
        """Write one event."""
        self._send(event)

    def close(self) -> None:
        """Close the file of a path sink. Flush an open text file."""
        if self._owned:
            self._file.close()
        elif self._file is not None:
            self._file.flush()


def read_timing(path: str | Path) -> list[dict[str, Any]]:
    """Return the headers and the events of a timing JSONL file, in file order."""
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def task_ids(event: Mapping[str, Any]) -> list[str]:
    """Return `{frame_index}:{camera_id}:{node_id}:{span}` for each image of the event."""
    return [f"{image['frame_index']}:{image['camera_id']}:{event['node_id']}:{event['span']}" for image in event["images"]]


def duration_ms(event: Mapping[str, Any]) -> float:
    """Return the duration of the event in milliseconds."""
    return (event["end_ns"] - event["start_ns"]) / 1e6


def skellybench_timing(records: str | Path | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate the headers and the events of a run to the skellybench timing record.

    `records` is the path of a timing JSONL file, or the headers and the events in file order.

    - `stages_ms_per_image`: for each stage, the sum of the model span times divided by the sum of
      `batch_size` of those events, or null when no event has the stage. The model spans are the
      spans of each `onnx_model` node and the `run` span of each `mediapipe_tasks` node.
    - `excluded_ms_per_image`: the `run` time of the glue nodes for each image, under `GLUE_STAGE`.
    - The events of the reserved source `frame` (`decode`, `upload`) are in no stage and not in
      `excluded_ms_per_image`: their time is a part of `pipeline.run`.
    - `ms_per_image`: the time of the span `pipeline.run` for each image, when that span is on.
    - `images_per_second`: from `ms_per_image`, else from the sum of the stages.
    - `stage_providers`: from the node item, when the run has one model node that gives it.
    """
    if isinstance(records, (str, Path)):
        records = read_timing(records)
    nodes: dict[str, Mapping[str, Any]] = {}
    time_ms = dict.fromkeys(STAGES, 0.0)
    count = dict.fromkeys(STAGES, 0)
    glue_ms = run_ms = 0.0
    run_images = 0
    images: set[tuple[Any, Any]] = set()
    for record in records:
        if "schema" in record:
            if record["schema"] != TIMING_SCHEMA:
                raise ValueError(f"the timing schema {record['schema']!r} is not {TIMING_SCHEMA!r}")
            nodes.update({item["id"]: item for item in record["nodes"]})
            continue
        images.update((image["frame_index"], image["camera_id"]) for image in record["images"])
        if record["node_id"] == RESERVED_NODE_ID:
            run_ms += duration_ms(record)
            run_images += record["batch_size"]
            continue
        if record["node_id"] == FRAME:  # `frame.decode` and `frame.upload` are a part of `pipeline.run`, not of a stage
            continue
        if record["node_id"] not in nodes:
            raise ValueError(f"no header before the event gives the node {record['node_id']!r}")
        node_type = nodes[record["node_id"]]["type"]
        if node_type not in MODEL_NODE_TYPES:
            glue_ms += duration_ms(record)
            continue
        # the `run` span of a `mediapipe_tasks` node counts as the stage `inference` (pipeline.timing, Implementer guidance)
        stage = record["span"] if node_type == "onnx_model" else "inference"
        time_ms[stage] += duration_ms(record)
        count[stage] += record["batch_size"]
    stages = {stage: time_ms[stage] / count[stage] if count[stage] else None for stage in STAGES}
    total = run_ms / run_images if run_images else sum(value for value in stages.values() if value is not None)
    if total <= 0:
        raise ValueError("the events hold no time of a model span or of pipeline.run")
    timing: dict[str, Any] = {"images_per_second": 1000.0 / total, "stages_ms_per_image": stages}
    if run_images:
        timing["ms_per_image"] = total
    providers = [item["stage_providers"] for item in nodes.values() if item["type"] in MODEL_NODE_TYPES and item["stage_providers"]]
    if len(providers) == 1:
        timing["stage_providers"] = dict(providers[0])
    if glue_ms:
        timing["excluded_ms_per_image"] = {GLUE_STAGE: glue_ms / len(images)}
    return timing
