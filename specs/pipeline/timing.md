---
id: pipeline.timing
title: Timing
kind: pipeline
vectors: null
status: {spec: draft}
---

# Timing

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A run can measure the time of fixed points of each node. Each measured point gives one event. The run writes the events as JSONL, after a header line. A benchmark run takes a COCO file as input. This section gives the timing points, the events, the header, the canonical JSON of a hash and the COCO input form ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) items 1 to 4 and 6).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentation.timing_points` | array of strings | no | The timing points that are on: `<node>.<point>` or `pipeline.run`. Default: empty, no point is on. |

The timing points of each node type ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1):

| Node type | Points |
|-----------|--------|
| `detector` | `preprocess`, `inference`, `postprocess`, with the boundaries of OpenMMLab-Exporter ADR-W9RE |
| each other type | `run` |
| the reserved id `pipeline` | `run`: one point for each frame call |

The fields of an event ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 2):

| Field | Description |
|-------|-------------|
| `images` | One item `{frame_index, camera_id}` for each image of the call. A field of an item is never null. |
| `node_id` | The node id, or `pipeline`. |
| `point` | The point name. |
| `batch_size` | The length of `images`. |
| `start_ns` | The start, in nanoseconds of a monotonic clock (`perf_counter_ns`). |
| `end_ns` | The end, on the same clock. |

The fields of the header line ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3):

| Field | Description |
|-------|-------------|
| `schema` | `skellytracker.timing/1`. |
| `run_id` | The id of the run. |
| `skellytracker_version` | The version of skellytracker that made the file. |
| `clock` | `{name, implementation, resolution_ns}`. `name` is `perf_counter_ns`. `implementation` and `resolution_ns` come from `time.get_clock_info("perf_counter")`. `implementation` is information only. |
| `anchor` | `{perf_counter_ns, unix_ns}`: one reading of the event clock and of the Unix clock, read together. |
| `running_mode` | `image`, `video` or `live` ([Running](running.md#behaviour)). |
| `warmup_passes` | The number of warm-up passes. |
| `image_list_sha256` | The hash of the image list of the COCO input form, or null ([Behaviour](#behaviour) item 6). |
| `camera_ids` | The camera ids of the run. |
| `pipeline_sha256` | The SHA-256 of the canonical JSON of the config ([Behaviour](#behaviour) item 5). |
| `points_on` | The timing points that are on. |
| `nodes` | One item for each node. |

The fields of a node item: `id`, `type`, `batching`, `inputs` (each with a `prev` flag), `key`, `sidecar_sha256`, `artifact_sha256`, `size`, `precision`, `execution` and `stage_providers`. A node item has no `shared_with`, because no session is shared ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 6). `execution` holds `requested_ep`, `used_ep`, the device, `gpu_uuid`, `ep_device_id`, the EP options that change the numbers, `cpu_nodes` (the count of the nodes of the session on the CPU EP) and `cpu_op_types` (their op types) ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).

## Behaviour

1. `instrumentation.timing_points` selects the points. The run parameter timing off turns each point off. The run parameter of the destination gives where the events go ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).
2. A node that does not run gives no event. A warm-up pass gives no event ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 2).
3. The first line of a JSONL file is a header, one for each run and process. Each other line is an event or a header. When a session changes during a run, the run writes a new header line. A header applies to the events after it, until the next header ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3).
4. Derived values come from helpers outside the hot path. The events do not hold them ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4):
   - `task_id` is `{frame_index}:{camera_id}:{node_id}:{point}`, one for each item of `images`.
   - `duration_ms` is (`end_ns` − `start_ns`) / 1e6.
5. **Canonical JSON.** A hash of a config is the SHA-256 of its canonical JSON. The canonical JSON is UTF-8 bytes, with sorted keys, the separators `,` and `:`, no whitespace and no escape of non-ASCII characters: `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.
   - `pipeline_sha256` hashes the mapping of `schema_version`, `nodes` and `outputs` of the config. The keys `pipeline_id`, `description`, `source` and `instrumentation` are not in it. The config is first validated by the reference model, with the defaults of the spec: `PipelineConfig.model_dump(mode="json")`. It holds no value from a sidecar and no EP ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3).
   - `upstream_sha256` of a tap uses the same bytes ([Taps](taps.md#fields)).
6. **COCO input form.** A benchmark run takes a COCO annotations file and an image folder. It has one camera. The `image_id` of each image comes from the COCO file. `image_list_sha256` is the SHA-256 of the UTF-8 bytes of the `image_id` values, in ascending order, each as a decimal integer, joined with `\n`, with no line feed at the end ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6). A run with no COCO input has `image_list_sha256: null`.

## Validation rules

- [ ] `V-pipeline.timing-1` Each timing point must name a node of the file and a point of the type of that node, or be `pipeline.run`.

## Implementer guidance

- The reference model checks `V-pipeline.timing-1` in `check_structure`. The `timing_points` of each node class give the points. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The public helper `core/pipelines/timing.py` aggregates the events to the skellybench timing record. `stages_ms_per_image` is the sum of the model point times divided by the sum of `batch_size`. The model points are the points of each detector node and the `run` point of each `mediapipe_tasks` node. The `run` time of a glue node goes to `excluded_ms_per_image` ([ADR-0WTV](../../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) item 2).
- skellybench runs `python -m skellytracker run --pipeline … --coco <annotations.json> --images <dir> --out … [--ep <key>] [--ep-option <name>=<value> …] [--timing on]` as a subprocess. The timing files and the tap files are the contract ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6). The EP flags are in [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 2.
- The header has no field `mode`: skellytracker has no IO binding to report.

## Authoring guidance

- Until skellybench has stages of several nodes, measure one detector node at a time. Replay its upstream outputs ([Taps](taps.md); [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).

## Examples

```yaml
instrumentation:
  timing_points: [pipeline.run, wholebody.preprocess, wholebody.inference, wholebody.postprocess]
```
