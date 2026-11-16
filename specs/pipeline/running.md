---
id: pipeline.running
title: Running
kind: pipeline
vectors: null
status: {spec: draft}
---

# Running

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

A run starts a pipeline with run parameters. The same file runs in each running mode. This section gives the run parameters, the frame time, the running modes, the batch, the stateful pipelines, the session sharing, the warnings, the start checks and the param changes during a run ([ADR-N5BM](../../decisions/entries/N5BM-set-during-run-and-set-params.md); [ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) items 2 to 7; [ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) items 1, 6 and 7; [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 2, 4 and 5).

## Fields

A pipeline file has no field of this section. A run takes these parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| camera ids | yes | The ids of the cameras of the run. |
| running mode | yes | `image`, `video` or `live`. |
| execution provider | only when an `onnx_model` node has no `execution_provider` ([Behaviour](#behaviour) item 7) | A key of the EP catalog, for example `cuda`, `trt-rtx` or `cpu`. |
| EP options | no | A mapping of option names to values, all strings. The EP catalog lists the allowed names and values of each EP. Default: empty. |
| device | no | One GPU key or a list of GPU keys. The run uses exactly those GPUs. Default: each GPU that qualifies ([ADR-P1F3](../../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md)). |
| VRAM reserve | no | The bytes of VRAM that the run leaves free on each GPU that it uses, for example for a camera app and a player. Default: 1 GiB ([Behaviour](#behaviour) item 4; [ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1). |
| `fps` | no | A float. Default: 30.0. Only in `video`, for a camera that gives no `timestamp_ms` ([Behaviour](#behaviour) item 2). |
| timing | no | On or off, and the destination of the events ([Timing](timing.md)). |
| tap folder | no | The folder of the taps ([Taps](taps.md)). |
| user root | no | The user root of the model and pipeline files ([Pipeline file](file.md#behaviour)). |
| warning receiver | no | A receiver that gets each new warning. |

Each call gives, for each camera of the call, one frame with its `frame_index`. In `live`, each frame also has its `timestamp_ms` (a float, in milliseconds). In `video`, the frames of a camera have a `timestamp_ms` when the camera gives one ([Behaviour](#behaviour) item 2).

A warning has these fields ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 6):

| Field | Description |
|-------|-------------|
| `code` | `batch_limited_by_state`, `ep_partial_placement`, `merge_unfilled_points` or `missing_dependency`. |
| `message` | A text for people. The log line uses the same text. |
| `node_ids` | The ids of the nodes that the warning is about. |
| `details` | A mapping with more facts. |

## Behaviour

1. **Running modes.** The run sets the running mode. The file is the same in each mode ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2):
   - `image`: each `@prev` value is empty. The frame size can change from call to call. The run has one camera.
   - `video`: the run gets each frame in order.
   - `live`: `frame_index` can skip. The caller drops frames. The run drops no frame.
2. **Frame time.** The temporal nodes use `timestamp_ms` ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 2):
   - `live`: each frame must have a `timestamp_ms` (`V-pipeline.running-6`). There is no fallback.
   - `video`: each camera gives `timestamp_ms` on all its frames or on none (`V-pipeline.running-7`). For a camera that gives none, the run uses `timestamp_ms = frame_index × 1000 / fps` ([ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 8).
   - `image`: the run uses no `timestamp_ms`.
   - The `timestamp_ms` of a camera must increase from frame to frame ([`V-node.smooth_keypoints-3`](nodes/smooth_keypoints.md#validation-rules)).
   - A call that breaks `V-pipeline.running-6`, `V-pipeline.running-7` or [`V-node.smooth_keypoints-3`](nodes/smooth_keypoints.md#validation-rules) raises one typed error. The call changes no state of any of its cameras, also no `@prev` value. The run accepts the next call. Stage 1.10 of the [implementation plan](../sidecar-implementation-plan.md#110-the-pipeline-api-was-p) names the error ([ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 9).
3. **Cameras.** In `video` and `image`, each call gives one frame for each camera id of the run. In `live`, a call can hold a subset of the camera ids of the run ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 3). A run with two or more GPUs splits its cameras over the GPUs. Each GPU runs the whole pipeline for its cameras ([ADR-P1F3](../../decisions/entries/P1F3-hardware-probe-devices-and-multi-gpu.md) item 7). The split is fixed at start ([ADR-AMF7](../../decisions/entries/AMF7-camera-split-by-vram.md)):
   - The GPUs are in the order of the GPUs of the run: the GPU with the most VRAM first. On a tie, the GPU with the lowest PCI bus id is first.
   - The weight of a GPU is the VRAM that the run can use on it: the free VRAM at start minus the VRAM reserve, with a floor of 0. When the host cannot read the free VRAM of each GPU of the run, the weight is the total VRAM minus the VRAM reserve, with a floor of 0. When the host cannot read the total VRAM of each GPU of the run, or each weight is 0, all weights are equal.
   - With `n` cameras and the weights `w_i`, the quota of GPU `i` is `w_i × n / Σw`. Each GPU gets the integer part of its quota. The cameras that remain go one each to the GPUs with the largest fractional parts. On a tie, the earlier GPU gets the camera. The run uses exact arithmetic for the quotas. Thus GPUs with equal weights get equal counts, and the extra cameras go to the first GPUs.
   - Each GPU that the run uses gets one camera or more. Each GPU with the count 0, in GPU order, takes one camera from the GPU with the largest count. On a tie, it takes the camera from the earlier GPU.
   - A run with fewer cameras than GPUs uses only the first GPUs, with one camera each.
   - The run gives the cameras to the GPUs in the order of the camera ids: the first cameras to the first GPU, the next cameras to the second GPU, and so on.
4. **Batch.** The run chooses the batch at start ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 4):
   - In `video` and `image`, the batch is k × camera count. The run chooses k for each GPU that it uses, from the free VRAM of that GPU minus the VRAM reserve, and counts the `I` of each node that takes ROIs. k is 1 until the host can measure the free VRAM ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 1).
   - In `live`, the batch is the camera count.
   - In `video`, the batch of a stateful pipeline is the camera count (Behaviour item 5).
   - A node that takes ROIs batches to that batch × the `I` of the instance source of its ROI input. The run converts the batch at start.
   - The run converts each artifact with `batching.batch: 3` to its batch at start ([Batch conversion](../model-sidecar/common/batch-conversion.md)).
   - The run pads a missed frame. It gives a blank crop to each empty crop slot, for example the slot of a padding ROI row. It drops the result of each padded item.
5. **Stateful pipelines.** A pipeline is stateful when it has an `@prev` input, or a temporal node upstream of an `onnx_model` node. The temporal nodes are `smooth_roi`, `smooth_keypoints`, `redetect_trigger`, and `mediapipe_tasks` in the landmarker mode `VIDEO`. A temporal node with no `onnx_model` node downstream does not make a pipeline stateful. `roi_hold` keeps no state, so it is not a temporal node. Each temporal node keeps a separate state for each camera. The node section gives the state of one camera. In `live`, a camera that a call does not hold keeps its state ([ADR-97X9](../../decisions/entries/97X9-pipeline-instance-rows-prev-types-and-refused-calls.md) item 7). In `video`, a stateful pipeline runs at batch = camera count. There is no switch to turn this off. The run writes one log line that names the stateful nodes, and gives the warning `batch_limited_by_state` ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 5).
6. **Session sharing only inside one run.** A run owns its inference sessions. In one run, the nodes with the same artifact SHA-256, batch, EP key, EP options and device share one inference session. The file does not control this. No session is shared between runs: two runs are two sets of sessions. `close()` frees the sessions of the run ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 6).
7. **Execution provider.** The EP key and the EP options are parameters of the run. The EP catalog in `core/eps/` owns the EP keys and lists the allowed options of each EP ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 1 and 2). An `onnx_model` node can give its own EP in `execution_provider` and its own options in `ep_options`. The EP of the run applies to each `onnx_model` node that has no `execution_provider`. A run must give an EP when such a node exists (`V-pipeline.running-8`). A run of a pipeline with no `onnx_model` node must not give an EP (`V-pipeline.running-9`). A `mediapipe_tasks` node never uses an EP. One pipeline can hold `onnx_model` nodes and `mediapipe_tasks` nodes ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4). There is no EP policy such as `recommended:latency`. The caller resolves a recommended form to an EP key and its options ([ADR-7NY2](../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 12; [ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 3).
   - A run never uses another EP than the requested EP. An EP that is not available or does not start stops the start of the run before frame 0 ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 4).
   - An out-of-memory error of a session during a call raises `VRAMExhaustionError`, the error of an out-of-memory error at start. The run does not do the call again, and it does not change the batch. The run is then closed: each later call raises an error ([ADR-2V7Q](../../decisions/entries/2V7Q-out-of-memory-during-a-call.md)).
   - A session can have nodes on the CPU EP. The run reports them ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
8. **Warnings.** The run gives a warning for each of these conditions ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) items 6 and 7):
   - `batch_limited_by_state`: the pipeline is stateful and the running mode is `video` (Behaviour item 5).
   - `ep_partial_placement`: a session of the node has nodes on the CPU EP. `details` gives the node count of each EP and the CPU op types. The run gives it one time for each session ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) item 5).
   - `merge_unfilled_points`: a slot of a `merge` node replaces a group, and one or more points of that group are unfilled and no key of `map` names them. A load gives this warning. `details` lists the points ([Node: merge](nodes/merge.md#behaviour) item 5; [ADR-KW76](../../decisions/entries/KW76-merge-replace-add-and-hungarian-match.md) item 2).
   - `missing_dependency`: a node needs an optional extra that is not installed, or an ONNX file that is absent or whose hash does not agree. A load gives this warning. A start fails before frame 0 ([Validation rules](#validation-rules)).
   - The load result holds the warnings that are known before start. The run holds the full list. The run gives each new warning to the warning receiver one time, also during the run, from the thread that makes the call.
9. **Replayed and unused ports.** A port is used when it is an output, an input of a node that runs, or the port of a `record` tap. A node whose outputs are all replayed or not used does not run. The upstream nodes of a replayed port do not run when nothing else uses them ([Taps](taps.md#behaviour)).
10. **Start checks.** The run does these checks before frame 0 ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 7): `V-pipeline.running-3`, `V-pipeline.running-4`, `V-pipeline.running-5`, `V-pipeline.running-8`, `V-pipeline.running-9`, [`V-pipeline.taps-2`](taps.md#validation-rules), [`V-pipeline.taps-3`](taps.md#validation-rules), [`V-pipeline.taps-4`](taps.md#validation-rules), [`V-pipeline.taps-5`](taps.md#validation-rules), [`V-pipeline.taps-6`](taps.md#validation-rules) and [`V-pipeline.taps-7`](taps.md#validation-rules).
11. **Params during a run.** `PipelineRun.set_params(node_id, params)` sets params of one node ([ADR-N5BM](../../decisions/entries/N5BM-set-during-run-and-set-params.md)):
    - Only a param that the node table marks `yes` in the column "Set during run" can change. The run checks each value against the type and the range of the param, as the load does.
    - The run accepts the call in each running mode before the first `process` or `process_batch` call. After that call, it accepts the call only in `live`, and only when the run has no `record` tap ([Taps](taps.md#behaviour)).
    - A change applies from the next `process` or `process_batch` call, to each camera. It does not reset the state of a node. A param whose change would need a reset is marked `no`.
    - A call that breaks `V-pipeline.running-10` raises the error `SetParamsRefused`. It changes no param.

## Validation rules

- [ ] `V-pipeline.running-1` The camera ids must be a non-empty list of unique ids. In the running mode `image`, the list must hold exactly one id.
- [ ] `V-pipeline.running-2` In `video` and `image`, each call must give a frame for each camera id of the run, and no frame for another id. In `live`, each call must give a frame for one or more camera ids of the run, and no frame for another id.
- [ ] `V-pipeline.running-3` Each ONNX artifact of each node that runs must be present, with the SHA-256 that its sidecar gives. Each optional extra that a node that runs needs must be installed. Else the start must fail before frame 0 with an error that names the extra or the file, and the nodes.
- [ ] `V-pipeline.running-4` The EP of each `onnx_model` node that runs must be a key of the EP catalog that is not reserved and is ready on the host. Its EP options must be names and values that the catalog allows for that EP ([ADR-9NW0](../../decisions/entries/9NW0-ep-keys-options-and-failures.md) items 1, 2 and 4).
- [ ] `V-pipeline.running-5` A node that runs must have no replayed output port.
- [ ] `V-pipeline.running-6` In the running mode `live`, each frame must have a `timestamp_ms`.
- [ ] `V-pipeline.running-7` In the running mode `video`, each camera must give a `timestamp_ms` on each of its frames or on none of its frames.
- [ ] `V-pipeline.running-8` When the pipeline has an `onnx_model` node with no `execution_provider`, the run must give an EP ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4).
- [ ] `V-pipeline.running-9` When the pipeline has no `onnx_model` node, the run must not give an EP ([ADR-9PDQ](../../decisions/entries/9PDQ-pipeline-renames-and-the-run-ep.md) item 4).
- [ ] `V-pipeline.running-10` A `set_params` call must name a node of the run. Each param must be a param of that node type, marked `yes` in the column "Set during run", with a value of its type and range. After the first `process` or `process_batch` call, the running mode must be `live` and the run must have no `record` tap ([ADR-N5BM](../../decisions/entries/N5BM-set-during-run-and-set-params.md)).

## Implementer guidance

- The runtime builds each ONNX session with `eps.build_session()`. The `execution` facts of the timing header come from that build ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 5).
- The availability of an extra comes from `importlib.util.find_spec` with a literal name, the presence of each ONNX file and its hash ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 7).
- The warnings do not use the Python `warnings` module ([ADR-V7GZ](../../decisions/entries/V7GZ-pipeline-api-device-and-vram-reserve.md) item 6).
- The run parameter "frame interval" of the first draft is removed. The temporal nodes use `timestamp_ms` in each mode that keeps state.

## Authoring guidance

- A previous-frame input lowers the batch in `video`. A `smooth_keypoints` node after the last `onnx_model` node does not, because it runs on the host, frame by frame, after the batched pass ([ADR-ZYS9](../../decisions/entries/ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 5).
- A live caller must give a `timestamp_ms` that increases, for example from the capture clock of the camera.
- The pipeline file is the same in each running mode. The caller gives a value for each mode, in the config before the start or with `set_params` before the first frame. For example, a caller sets `redetect_interval` of a `redetect_trigger` node to 10 in `live` and to 1 in `video` ([ADR-N5BM](../../decisions/entries/N5BM-set-during-run-and-set-params.md) item 5).

## Examples

None yet.
