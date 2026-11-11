---
id: pipeline.timing
title: Timing
kind: pipeline
vectors: null
status: {spec: draft}
---

# Timing

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A run can measure the time of fixed points of each node. Each measured point gives one event. The run writes the events as JSONL, after one header line. A benchmark run takes a COCO file as input. This section gives the timing points, the events, the header and the COCO input form ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) items 1 to 4 and 6).

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
| `frame_number` | The frame number. |
| `camera_id` | The camera id. `null` for one call over the camera batch. |
| `node_id` | The node id, or `pipeline`. |
| `point` | The point name. |
| `batch_size` | The batch of the call. 1 for a glue node. |
| `start_ns` | The start, in nanoseconds of a monotonic clock (`perf_counter_ns`). |
| `end_ns` | The end, on the same clock. |

The fields of the header line ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3):

| Field | Description |
|-------|-------------|
| `schema` | `skellytracker.timing/1`. |
| `run_id` | The id of the run. |
| the version, the clock and one anchor | The skellytracker version, the clock of the events and one anchor of that clock. This draft does not fix their field names. |
| `mode` | The mode of the run. This draft does not fix its values. |
| `running_mode` | `image`, `video` or `live` ([Running](running.md#behaviour)). |
| `warmup_passes` | The number of warm-up passes. |
| `image_list_sha256` | The hash of the image list ([Behaviour](#behaviour)). |
| `camera_ids` | The camera ids of the run. |
| `pipeline_sha256` | The SHA-256 of the pipeline config. This draft does not fix the bytes that it hashes. |
| `points_on` | The timing points that are on. |
| `nodes` | One item for each node. |

The fields of a node item: `id`, `type`, `batching`, `inputs` (each with a `prev` flag), `key`, `sidecar_sha256`, `size`, `precision`, `execution`, `stage_providers` and `shared_with`. `execution` holds `requested_ep`, `used_ep`, the device, `gpu_uuid`, `ep_device_id` and the EP options that change the numbers.

## Behaviour

1. `instrumentation.timing_points` selects the points. The run parameter timing off turns each point off. The run parameter of the destination gives where the events go ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 1).
2. A node that does not run gives no event. A warm-up pass gives no event ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 2).
3. The first line of a JSONL file is the header, one for each run and process. Each other line is one event. When a session changes during a run, the run writes a new header ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 3).
4. Derived values come from helpers outside the hot path. The events do not hold them ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4):
   - `task_id` is `{frame}:{camera_id or "batch"}:{node_id}:{point}`.
   - `duration_ms` is (`end_ns` − `start_ns`) / 1e6.
5. **COCO input form.** A benchmark run takes a COCO annotations file and an image folder. It has one camera. The `image_id` of each image comes from the COCO file. `image_list_sha256` is the SHA-256 of the sorted `image_id` values joined with `\n` ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6).

## Validation rules

- [ ] `V-pipeline.timing-1` Each timing point must name a node of the file and a point of the type of that node, or be `pipeline.run`.

## Implementer guidance

- The reference model checks `V-pipeline.timing-1` in `check_structure`. The `timing_points` of each node class give the points. (skellytracker `specs/pipeline/reference/pipeline_config.py`)
- A helper in `core/metrics/` aggregates the events to the skellybench timing record. `stages_ms_per_image` is the sum of the detector point times divided by the sum of `batch_size`. The `run` time of a glue node goes to `excluded_ms_per_image` ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).
- skellybench runs `python -m skellytracker run --pipeline … --coco <annotations.json> --images <dir> --out … [--ep …] [--timing on]` as a subprocess. The timing files and the tap files are the contract ([ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 6).

## Authoring guidance

- Until skellybench has stages of several nodes, measure one detector node at a time. Replay its upstream outputs ([Taps](taps.md); [ADR-Q59W](../../decisions/entries/Q59W-pipeline-timing-and-taps.md) item 4).

## Examples

```yaml
instrumentation:
  timing_points: [pipeline.run, wholebody.preprocess, wholebody.inference, wholebody.postprocess]
```
