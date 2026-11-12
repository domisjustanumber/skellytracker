---
id: pipeline.running
title: Running
kind: pipeline
vectors: null
status: {spec: draft}
---

# Running

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A run starts a pipeline with run parameters. The same file runs in each running mode. This section gives the run parameters, the frame time, the running modes, the batch, the stateful pipelines, the sessions, the warnings and the start checks ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) items 2 to 7; [ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) items 6 and 7; [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 2, 4 and 5).

## Fields

A pipeline file has no field of this section. A run takes these parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| camera ids | yes | The ids of the cameras of the run. |
| running mode | yes | `image`, `video` or `live`. |
| execution provider | yes | A key of the EP catalog, for example `cuda`, `trt-rtx` or `cpu`. |
| EP options | no | A mapping of option names to values, all strings. The EP catalog lists the allowed names and values of each EP. Default: empty. |
| `fps` | no | A float. Default: 30.0. Only in `video`, for a frame with no `timestamp_ms` ([Behaviour](#behaviour) item 2). |
| timing | no | On or off, and the destination of the events ([Timing](timing.md)). |
| tap folder | no | The folder of the taps ([Taps](taps.md)). |
| user root | no | The user root of the model and pipeline files ([Pipeline file](file.md#behaviour)). |
| warning receiver | no | A receiver that gets each new warning. |

Each call gives, for each camera of the call, one frame with its `frame_index` and, in `video` and `live`, its `timestamp_ms` (a float, in milliseconds).

A warning has these fields ([ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 6):

| Field | Description |
|-------|-------------|
| `code` | `batch_limited_by_state`, `ep_partial_placement` or `missing_dependency`. |
| `message` | A text for people. The log line uses the same text. |
| `node_ids` | The ids of the nodes that the warning is about. |
| `details` | A mapping with more facts. |

## Behaviour

1. **Running modes.** The run sets the running mode. The file is the same in each mode ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 2):
   - `image`: each `@prev` value is empty. The frame size can change from call to call. The run has one camera.
   - `video`: the run gets each frame in order.
   - `live`: `frame_index` can skip. The caller drops frames. The run drops no frame.
2. **Frame time.** The temporal nodes use `timestamp_ms` ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 2):
   - `live`: each frame must have a `timestamp_ms` (`V-pipeline.running-6`). There is no fallback.
   - `video`: the caller can give `timestamp_ms`. A caller timestamp wins. For a frame with no `timestamp_ms`, the run uses `timestamp_ms = frame_index × 1000 / fps`.
   - `image`: the run uses no `timestamp_ms`.
   - The `timestamp_ms` of a camera must increase from frame to frame ([`V-node.smooth_keypoints-3`](nodes/smooth_keypoints.md#validation-rules)).
3. **Cameras.** In `video` and `image`, each call gives one frame for each camera id of the run. In `live`, a call can hold a subset of the camera ids of the run ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 3).
4. **Batch.** The run chooses the batch at start ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 4):
   - In `video` and `image`, the batch is k × camera count. The run chooses k from the free VRAM, and counts the `I` of each node that takes ROIs. k is 1 until the host can measure the free VRAM.
   - In `live`, the batch is the camera count.
   - In `video`, the batch of a stateful pipeline is the camera count (Behaviour item 5).
   - A node that takes ROIs batches to that batch × the `I` of the instance source of its ROI input. The run converts the batch at start.
   - The run converts each artifact with `batching.batch: 3` to its batch at start ([Batch conversion](../model-sidecar/common/batch-conversion.md)).
   - The run pads a missed frame. It gives a blank crop to each empty crop slot, for example the slot of a padding ROI row. It drops the result of each padded item.
5. **Stateful pipelines.** A pipeline is stateful when it has an `@prev` input, or a temporal node upstream of a detector node. The temporal nodes are `smooth_roi`, `smooth_keypoints`, `redetect`, and `mediapipe_tasks` in the landmarker mode `VIDEO`. A temporal node with no detector node downstream does not make a pipeline stateful. `roi_tracking` keeps no state, so it is not a temporal node. In `video`, a stateful pipeline runs at batch = camera count. There is no switch to turn this off. The run writes one log line that names the stateful nodes, and gives the warning `batch_limited_by_state` ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 5).
6. **No session sharing.** A run owns its inference sessions. Each node builds its own sessions. No session is shared between nodes or between runs. `close()` frees the sessions of the run ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 6).
7. **Execution provider.** The EP key and the EP options are parameters of the run. The EP catalog in `core/eps/` owns the EP keys and lists the allowed options of each EP ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 1 and 2). A detector node can give its own EP in `execution_provider` and its own options in `ep_options`. There is no EP policy such as `recommended:latency`. The caller resolves a recommended form to an EP key and its options ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 12; [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 3).
   - A run never uses another EP than the requested EP. An EP that is not available or does not start stops the start of the run before frame 0 ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 4).
   - A session can have nodes on the CPU EP. The run reports them ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
8. **Warnings.** The run gives a warning for each of these conditions ([ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) items 6 and 7):
   - `batch_limited_by_state`: the pipeline is stateful and the running mode is `video` (Behaviour item 5).
   - `ep_partial_placement`: a session of the node has nodes on the CPU EP. `details` gives the node count of each EP and the CPU op types. The run gives it one time for each session ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
   - `missing_dependency`: a node needs an optional extra that is not installed, or an ONNX file that is absent or whose hash does not agree. A load gives this warning. A start fails before frame 0 ([Validation rules](#validation-rules)).
   - The load result holds the warnings that are known before start. The run holds the full list. The run gives each new warning to the warning receiver one time, also during the run, from the thread that makes the call.
9. **Replayed and unused ports.** A port is used when it is an output, an input of a node that runs, or the port of a `record` tap. A node whose outputs are all replayed or not used does not run. The upstream nodes of a replayed port do not run when nothing else uses them ([Taps](taps.md#behaviour)).
10. **Start checks.** The run does these checks before frame 0 ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 7): `V-pipeline.running-3`, `V-pipeline.running-4`, `V-pipeline.running-5`, [`V-pipeline.taps-2`](taps.md#validation-rules), [`V-pipeline.taps-3`](taps.md#validation-rules), [`V-pipeline.taps-4`](taps.md#validation-rules), [`V-pipeline.taps-5`](taps.md#validation-rules), [`V-pipeline.taps-6`](taps.md#validation-rules) and [`V-pipeline.taps-7`](taps.md#validation-rules).

## Validation rules

- [ ] `V-pipeline.running-1` The camera ids must be a non-empty list of unique ids. In the running mode `image`, the list must hold exactly one id.
- [ ] `V-pipeline.running-2` In `video` and `image`, each call must give a frame for each camera id of the run, and no frame for another id. In `live`, each call must give a frame for one or more camera ids of the run, and no frame for another id.
- [ ] `V-pipeline.running-3` Each ONNX artifact of each node that runs must be present, with the SHA-256 that its sidecar gives. Each optional extra that a node that runs needs must be installed. Else the start must fail before frame 0 with an error that names the extra or the file, and the nodes.
- [ ] `V-pipeline.running-4` The EP of each node that runs must be a key of the EP catalog that is not reserved and is ready on the host. Its EP options must be names and values that the catalog allows for that EP ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 1, 2 and 4).
- [ ] `V-pipeline.running-5` A node that runs must have no replayed output port.
- [ ] `V-pipeline.running-6` In the running mode `live`, each frame must have a `timestamp_ms`.

## Implementer guidance

- The runtime builds each ONNX session with `eps.build_session()`. The `execution` facts of the timing header come from that build ([ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 5).
- The availability of an extra comes from `importlib.util.find_spec` with a literal name, the presence of each ONNX file and its hash ([ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 7).
- The warnings do not use the Python `warnings` module ([ADR-48PG](../../decisions/entries/48PG-pipeline-api-ep-options-and-warnings.md) item 6).
- The run parameter "frame interval" of the first draft is removed. The temporal nodes use `timestamp_ms` in each mode that keeps state.

## Authoring guidance

- A previous-frame input lowers the batch in `video`. A `smooth_keypoints` node after the last detector node does not, because it runs on the host, frame by frame, after the batched pass ([ADR-0WJB](../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 5).
- A live caller must give a `timestamp_ms` that increases, for example from the capture clock of the camera.

## Examples

None yet.
