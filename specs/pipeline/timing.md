---
id: pipeline.timing
title: Timing
kind: pipeline
vectors: null
status: {spec: draft}
---

# Timing

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A run can measure the time of fixed spans of each node. Each measured span gives one event. The run writes the events as JSONL, after a header line. A benchmark run takes a COCO file as input. This section gives the timing spans, the events, the header, the canonical JSON of a hash and the COCO input form ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) items 1 to 4 and 6; [ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instrumentation.timing_spans` | array of strings | no | The timing spans that are on: `<node>.<span>`, `pipeline.run`, `frame.decode` or `frame.upload`. Default: empty, no span is on ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3). |

The timing spans of each node type ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1; [ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3):

| Node type | Spans |
|-----------|-------|
| `onnx_model` | `preprocess`, `inference`, `postprocess`, with the boundaries of OpenMMLab-Exporter ADR-W9RE |
| each other type | `run` |
| the reserved id `pipeline` | `run`: one span for each frame call |
| the reserved source `frame` | `decode`: the decode of the JPEG buffers of a call, inside the span `pipeline.run`. The turn of each decoded frame by its `rotation_deg` is a part of the `decode` span. `images` gives the frames that the event decodes. A call with no JPEG buffer gives no `decode` event. `upload`: the copy of frames from CPU memory to GPU memory in a call, inside the span `pipeline.run`. `images` gives the frames that the event copies. A call in which no frame goes to GPU memory gives no `upload` event ([Running](running.md#behaviour) item 13; [ADR-P245](decisions/entries/P245-jpeg-frame-input.md)) |

The events of the reserved source `frame` for each frame that goes to GPU memory ([ADR-P245](decisions/entries/P245-jpeg-frame-input.md)):

- A decoded array gives an `upload` event and no `decode` event. The turn of a decoded array by its `rotation_deg` is in no `frame` span: it is inside the span `pipeline.run` only.
- A JPEG buffer that the run decodes on the CPU, in each fallback of [Running](running.md#behaviour) item 13, gives a `decode` event and then an `upload` event.
- A JPEG buffer that the GPU decoder decodes gives a `decode` event and no `upload` event. The GPU decoder copies the data to GPU memory itself, so that copy is a part of the `decode` span.

`upload` is the copy of the source frame to GPU memory, before the first node. The copy of the model input batch to the device stays in the spans of the `onnx_model` node, as OpenMMLab-Exporter ADR-W9RE item 2 gives (`preprocess`). On the GPU path the model input is already in GPU memory, so no span counts one copy two times.

The fields of an event ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 2; [ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3):

| Field | Description |
|-------|-------------|
| `images` | One item `{frame_index, camera_id}` for each image of the call. A field of an item is never null. |
| `node_id` | The node id, `pipeline` or `frame`. |
| `span` | The span name. |
| `batch_size` | The length of `images`. |
| `start_ns` | The start, in nanoseconds of a monotonic clock (`perf_counter_ns`). |
| `end_ns` | The end, on the same clock. |

The fields of the header line ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3; [ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3):

| Field | Description |
|-------|-------------|
| `schema` | `skellytracker.timing/1`. |
| `run_id` | The id of the run. |
| `skellytracker_version` | The version of skellytracker that made the file. |
| `clock` | `{name, implementation, resolution_ns}`. `name` is `perf_counter_ns`. `implementation` and `resolution_ns` come from `time.get_clock_info("perf_counter")`. `implementation` is information only. |
| `anchor` | `{perf_counter_ns, unix_ns}`: one reading of the event clock and of the Unix clock, read together. |
| `running_mode` | `image`, `video` or `live` ([Running](running.md#behaviour)). |
| `warmup_passes` | The number of warm-up runs of each inference session before frame 0: 1 for a run with an ONNX session, else 0. |
| `image_list_sha256` | The hash of the image list of the COCO input form, or null ([Behaviour](#behaviour) item 6). |
| `camera_ids` | The camera ids of the run. |
| `pipeline_sha256` | The SHA-256 of the canonical JSON of the config ([Behaviour](#behaviour) item 5). |
| `spans_on` | The timing spans that are on. |
| `nodes` | One item for each node. |

The fields of a node item: `id`, `type`, `batching`, `inputs` (each with a `prev` flag), `key`, `sidecar_sha256`, `artifact_sha256`, `size`, `precision`, `execution`, `stage_providers` and `shared_with`. `shared_with` lists the ids of the other nodes of the run that use the same session ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6). `execution` is null for a node with no session. Else it holds exactly `requested_ep`, `used_ep`, `device` (the device key of the GPU), `gpu_uuid`, `ep_device_id`, `ep_options` (a mapping of the EP options of the session), `cpu_nodes`, `cpu_op_types` and `cpu_threads`. `cpu_nodes` is the count of the nodes of the session on the CPU EP, and `cpu_op_types` holds their op types ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5; [ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md)). `cpu_threads` is the intra-op thread count of a session on the CPU EP `cpu`, and null for a session on another EP ([Running](running.md#behaviour) item 7; [ADR-HB8Z](../../decisions/entries/HB8Z-cpu-threads-run-parameter.md)).

Each item of `inputs` has `name` (the input name, or null for an item of a list input), `port` (`<node>.<port>`, with no `@prev`) and `prev` (a boolean) ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md)).

`stage_providers` is null, or a mapping with exactly `preprocess`, `inference` and `postprocess`. `inference` is the provider name of the session. The run writes the header before the first call, so `preprocess` gives the preprocess of the node at the start of the run. When the node starts with its preprocess as a graph on the EP `cuda` or `trt-rtx` ([Resize limit](../model-sidecar/pre/interpolation.md#resize-limit)), `preprocess` is the provider name of that graph. Else `preprocess` is null, because the preprocess runs on the host. A node whose combination the graph refuses at start thus has null. When a node uses the CPU preprocess later in the run, the run gives the warning `preprocessed_on_cpu` ([Running](running.md#behaviour) item 8). The header does not change, and the run writes no new header line for it ([Behaviour](#behaviour) item 3). `postprocess` is null, because it runs on the host ([ADR-P245](decisions/entries/P245-jpeg-frame-input.md)). The item of a node with no session has `stage_providers: null` ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md)).

When a node has a session on each of two or more GPUs, the times of the node are the times of all its sessions together. The timing has no part for each GPU. `batching`, `execution`, `stage_providers` and `shared_with` of the node item are those of the session of the first GPU ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 2).

## Behaviour

1. `instrumentation.timing_spans` selects the spans. The run parameter timing off turns each span off. The run parameter of the destination gives where the events go ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1; [ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3).
2. A node that does not run gives no event. A warm-up pass gives no event ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 2).
3. The first line of a JSONL file is a header, one for each run and process. Each other line is an event or a header. When a session changes during a run, the run writes a new header line. A header applies to the events after it, until the next header ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3).
4. Derived values come from helpers outside the hot path. The events do not hold them ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4):
   - `task_id` is `{frame_index}:{camera_id}:{node_id}:{span}`, one for each item of `images`.
   - `duration_ms` is (`end_ns` − `start_ns`) / 1e6.
5. **Canonical JSON.** A hash of a config is the SHA-256 of its canonical JSON. The canonical JSON is UTF-8 bytes, with sorted keys, the separators `,` and `:`, no whitespace and no escape of non-ASCII characters: `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.
   - `pipeline_sha256` hashes the mapping of `schema_version`, `nodes` and `outputs` of the config. The keys `pipeline_id`, `description`, `source` and `instrumentation` are not in it. The `description` of a node is not in a hash, because the run does not read it ([ADR-2RWC](../../decisions/entries/2RWC-one-boxes-port-type-and-node-descriptions.md)). The config is first validated by the reference model, with the defaults of the spec: `PipelineConfig.model_dump(mode="json")`. It holds no value from a sidecar and no EP ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3).
   - `upstream_sha256` of a tap uses the same bytes ([Taps](taps.md#fields)).
6. **COCO input form.** A benchmark run takes a COCO annotations file and an image folder. It has one camera. The `image_id` of each image comes from the COCO file. `image_list_sha256` is the SHA-256 of the UTF-8 bytes of the `image_id` values, in ascending order, each as a decimal integer, joined with `\n`, with no line feed at the end ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6). A run with no COCO input has `image_list_sha256: null`.

## Validation rules

- [ ] `V-pipeline.timing-1` Each timing span must name a node of the file and a span of the type of that node, or be `pipeline.run`, `frame.decode` or `frame.upload` ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3; [ADR-P245](decisions/entries/P245-jpeg-frame-input.md)).

## Implementer guidance

- The reference model checks `V-pipeline.timing-1` in `check_structure`. The `timing_spans` of each node class give the spans. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- The public helper `core/pipelines/timing.py` aggregates the events to the skellybench timing record. `stages_ms_per_image` is the sum of the model span times divided by the sum of `batch_size`. The model spans are the spans of each `onnx_model` node and the `run` span of each `mediapipe_tasks` node ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 3). The `run` span of a `mediapipe_tasks` node counts as the stage `inference` ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 4). The `run` time of the glue nodes goes to `excluded_ms_per_image` under the key `glue`: the sum of the times divided by the count of the images of the run ([ADR-0WTV](../../decisions/entries/0WTV-system-metrics-and-pipeline-timing-helper.md) item 2; [ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md)). The stages and `excluded_ms_per_image` do not include the events of the reserved source `frame`. Their time is a part of `pipeline.run` ([ADR-P245](decisions/entries/P245-jpeg-frame-input.md)).
- An event has no field for its parents, and no helper gives them. A tool can find the parents of an event from `inputs` of the node items ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 6).
- skellybench runs `python -m skellytracker run --pipeline … --coco <annotations.json> --images <dir> --out … [--ep <key>] [--ep-option <name>=<value> …] [--device <key> …] [--cpu-threads <n>] [--timing on] [--taps <dir>]` as a subprocess. The timing files and the tap files are the contract ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6). The EP flags are in [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 2. The flag `--device` is repeatable. It is in [ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1. The flag `--cpu-threads` gives the CPU threads of the run ([Running](running.md#fields); [ADR-HB8Z](../../decisions/entries/HB8Z-cpu-threads-run-parameter.md)). The flag `--taps` gives the tap folder ([Taps](taps.md#behaviour) item 1; [`V-pipeline.taps-2`](taps.md#validation-rules); [ADR-Y753](../../decisions/entries/Y753-pipeline-templates-glue-vectors-and-taps-flag.md) item 3). `--out` takes a `.jsonl` file or a folder. For a folder, the run writes the timing file `timing.jsonl` in that folder ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md)).
- On the GPU path, the run binds the output of the preprocess graph to the input of the model session in GPU memory. The header has no field `mode` for this binding, and no other field reports it ([ADR-P245](decisions/entries/P245-jpeg-frame-input.md)).

## Authoring guidance

- The stage `inference` of the skellybench timing record holds the `run` span of each `mediapipe_tasks` node. That `inference` value includes the preprocessing and the postprocessing of MediaPipe ([ADR-75K2](../../decisions/entries/75K2-unclear-places-of-the-pipeline-spec.md) item 4).
- Until skellybench has stages of several nodes, measure one inference node at a time. Replay its upstream outputs ([Taps](taps.md); [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).

## Examples

```yaml
instrumentation:
  timing_spans: [pipeline.run, wholebody.preprocess, wholebody.inference, wholebody.postprocess]
```
