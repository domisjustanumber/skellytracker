---
name: Streaming Pipeline Implementation
overview: Split streaming pipeline execution into phases: first a behavior-preserving RTMPose batch graph inside skellytracker, then a freemocap-facing realtime scheduler with packet metadata, zero-copy ring buffers, and CPU/GPU overlap, with sidecar-backed generic model nodes deferred until graph parity is proven.
todos:
  - id: graph-primitives
    content: "Phase 1: Add minimal internal `skellytracker/pipeline/` graph primitives for synchronous batch execution: packets, node protocol, static graph validation, and timing collection."
    status: pending
  - id: rtmpose-node-refactor
    content: "Phase 1: Refactor RTMPose detector, pose crop, inference, and postprocess stages into graph node classes without changing output behavior."
    status: pending
  - id: session-adapter
    content: "Phase 1: Make `RTMPoseSession.predict_batch()` and `predict_pose_from_bboxes()` execute the batch graph while preserving their existing return shapes and timing attributes."
    status: pending
  - id: sidecar-node-support
    content: "Future phase: Add sidecar-backed detector node construction so YOLO26-style models can plug into the graph without hardcoded tensor layouts after RTMPose graph parity is proven."
    status: pending
  - id: realtime-executor
    content: "Phase 2: Add a freemocap-facing bounded zero-copy realtime graph executor with camera/frame packet APIs, suitably-sized ring buffers, CPU/GPU worker lanes, output resequencing, and latency/backpressure metrics."
    status: pending
  - id: freemocap-integration
    content: "Phase 2: Add freemocap config, API, UI, skeleton-node, aggregator, restart-policy, and tests for skellytracker `use_streaming_pipeline` with `buffer_size_frames`."
    status: pending
  - id: validation
    content: Add graph, RTMPose parity, bypass, empty-detection, batch-size, and realtime scheduler tests; run targeted and full test suites.
    status: pending
isProject: false
---

# Streaming Pipeline Implementation

## Prerequisite Plans

Complete the numbered realtime sequence before Phase 2 freemocap integration:

- [**10 — Remove EP fallback**](10_remove_ep_fallback.plan.md) — strict ORT sessions; graph nodes inherit `RTMPoseSession.create()`.
- [**20 — Single global realtime pipeline**](20_single_global_realtime_pipeline.plan.md) — singleton manager, apply recreate policy, error UX.
- [**30 — Realtime batch size config**](30_realtime_batch_size.plan.md) — **authority for batch semantics**; full-batch gating and `batch_size=len(camera_ids)`.
- [**50 — YOLO26 nano detection**](50_yolo26_nano_detection.plan.md) — required before the future sidecar-backed graph node phase (Phase 1 can start after **30**).

Phase 1 (skellytracker-only RTMPose batch graph) may begin once plan **30** lands. Phase 2 (freemocap streaming scheduler) should wait until plan **50** and Phase 1 parity tests pass.

## Plan sequence

| Order | Plan |
|-------|------|
| **10**–**50** | Numbered realtime plans (see [30_realtime_batch_size.plan.md](30_realtime_batch_size.plan.md) implementation-order table) |
| **future** (this) | Streaming pipeline graph + freemocap scheduler |
| future | [future_hand_and_face_detection.plan.md](future_hand_and_face_detection.plan.md) — independent exploration |

## Phase Split

This work should be implemented as two separate phases, because they have different risk profiles and validation needs.

**Phase 1: Behavior-Preserving RTMPose Batch Graph**

Phase 1 stays entirely inside `skellytracker`. It refactors the current hardcoded `RTMPoseSession.predict_batch()` flow into explicit graph nodes, but keeps the same public API, same return shapes, same timing attributes, and same synchronous behavior. This phase is primarily about modularity, observability, and future model-plug-in support. It should not claim realtime speedups yet.

**Phase 2: Freemocap Realtime Scheduler Integration**

Phase 2 adds the actual streaming runtime behavior: required packet metadata, bounded queues, zero-copy ring buffers, CPU/GPU overlap, full-batch streaming, input-frame dropping under backpressure, and output resequencing. This phase depends on freemocap runtime behavior outside this repo, so it should begin only after Phase 1 parity tests pass and the freemocap integration contract is agreed.

**Future Phase: Sidecar-Backed Generic Model Nodes**

Sidecar-backed node construction is valuable, especially for YOLO26, but it should not be part of the initial graph proof. Add it only after the explicit YOLOX/RTMPose graph has parity with the legacy `RTMPoseSession` path. This keeps Phase 1 focused on graph correctness rather than model-family generalization.

## Phase 1 Scope

Build the first graph execution model inside `skellytracker`, with `RTMPoseSession` as the initial consumer. Preserve the existing synchronous contracts in [`skellytracker/trackers/base_tracker/base_tracker_abcs.py`](skellytracker/trackers/base_tracker/base_tracker_abcs.py): `BaseTracker.process_image()` still calls `BaseDetector.detect()` and returns a `BaseObservation`, and annotation/recording remain caller-controlled.

The first implementation should target [`skellytracker/trackers/rtmpose_tracker/rtmpose_session.py`](skellytracker/trackers/rtmpose_tracker/rtmpose_session.py), whose current `predict_batch()` is already a hardcoded two-stage graph:

```mermaid
flowchart LR
  images[ImagesBatch] --> detPre[DetectorPreprocess]
  detPre --> detInfer[DetectorInfer]
  detInfer --> detPost[DetectorPostprocess]
  detPost --> posePre[PoseCropPreprocess]
  images --> posePre
  posePre --> poseInfer[PoseInfer]
  poseInfer --> posePost[PosePostprocess]
  posePost --> output[PerImageKeypointsScores]
```

## Phase 1 Design

Add a small internal graph runtime under a new module such as [`skellytracker/pipeline/`](skellytracker/pipeline/). Keep it deliberately smaller than MediaPipe and limited to synchronous batch execution:

- `Packet`: typed value plus optional metadata such as `frame_number`, `camera_id`, `timestamp_ns`, and timing fields. Phase 1 may use metadata when useful, but only Phase 2 requires camera/frame metadata round-trip.
- `Node`: a calculator-style protocol with named inputs, named outputs, and a synchronous `run()` method.
- `Graph`: a static DAG of nodes and edges, validated at construction.
- `GraphExecutor`: topological batch executor for MVP, with stage timing and packet inspection.

Do not implement `RealtimeGraphExecutor` in Phase 1. That belongs to Phase 2.

Do not change the public tracker ABCs at first. Instead, expose the graph through session-level methods:

- `RTMPoseSession.predict_batch(images)` runs the full graph and returns the same `list[tuple[keypoints, scores]]` shape it returns today.
- `RTMPoseSession.predict_pose_from_bboxes(images, bboxes_per_image)` runs the pose subgraph only.
- `RTMPoseDetector.detect()` can remain a thin sync adapter around `predict_single()`.

Define the future packet API shape during Phase 1, but implement it only if it is useful for parity testing. Realtime-facing APIs belong to Phase 2:

- `RTMPoseSession.submit_frames(frames: Sequence[RealtimeFramePacket]) -> Sequence[RealtimePosePacket]` for synchronous batch-style use with explicit metadata.
- `RTMPoseSession.start_realtime_graph(...)`, `submit_frame(packet)`, and `poll_results()` or equivalent names for an async queued executor.
- Every output packet must preserve the input `camera_id`, `frame_number`, and timestamp metadata, plus include the same `(keypoints, scores)` data produced by `predict_batch()`.
- `predict_batch(images)` should remain a thin compatibility adapter that creates synthetic packet metadata internally and returns only the legacy data shape.
- The opt-in session config flag should be named `use_streaming_pipeline`, not `use_graph_pipeline`, because the user-facing behavior is streaming execution with bounded buffering rather than just graph-shaped internals.
- At session creation, if `use_streaming_pipeline=True`, skellytracker must expose the selected streaming buffer size back to freemocap so freemocap knows the maximum buffering depth or delay budget. Use one authoritative value, `buffer_size_frames`, in a structured startup/status object such as `StreamingPipelineInfo(buffer_size_frames=...)` attached to or returned alongside the created session.

## RTMPose Nodes

Refactor the current private stage methods in [`rtmpose_session.py`](skellytracker/trackers/rtmpose_tracker/rtmpose_session.py) into node implementations without changing behavior:

- `YoloXPreprocessNode`: wraps `yolox_letterbox_preprocess`, returns batched tensor plus per-image ratios.
- `YoloXInferNode`: owns the detector ORT call, including the existing prenms batch path and per-image fallback.
- `DetectionPostprocessNode`: wraps current NMS and bbox remapping logic, returns `bboxes_per_image`.
- `ExternalBboxesInputNode`: lets `predict_pose_from_bboxes()` bypass detector nodes.
- `PoseCropPreprocessNode`: wraps `rtmpose_letterbox_preprocess`, emits crops plus provenance ranges.
- `PoseInferNode`: owns the RTMPose ORT call over the flattened crop batch.
- `PosePostprocessNode`: wraps SIMCC decode and crop-to-image coordinate remap.
- `RTMPoseOutputNode`: groups crop results back into one `(keypoints, scores)` tuple per source image.

Keep existing timing fields like `last_human_detection_preprocess_ms`, `last_pose_estimation_ms`, and `last_pose_estimation_postprocess_ms` populated from graph node timings so current realtime telemetry does not break.

## Phase 1 Acceptance Criteria

Phase 1 is complete when:

- `RTMPoseSession.predict_batch(images)` returns the same results as the legacy implementation on fixed test inputs.
- `RTMPoseSession.predict_pose_from_bboxes(images, bboxes_per_image)` still bypasses detector inference and returns the same pose results.
- Existing timing attributes remain populated with equivalent stage meanings.
- Empty input, empty detections, one camera, multiple cameras, and mixed person counts behave as before.
- No new realtime queues, threads, ring buffers, or freemocap dependencies are required to use the batch graph.

## Phase 2 Scope

Phase 2 adds the freemocap-facing realtime scheduler on top of the validated batch graph. This is the phase that should deliver streaming throughput gains by overlapping capture, CPU preprocessing, GPU inference, CPU postprocessing, and output delivery.

`use_streaming_pipeline` should be the config switch that selects this path at session creation. When false, skellytracker uses the legacy synchronous/batch-compatible path. When true, skellytracker creates the streaming executor, allocates zero-copy ring buffers, and reports the chosen `buffer_size_frames` value to freemocap during startup.

## Realtime Scheduling

After Phase 1 passes, add the streaming scheduling layer for realtime use:

- Use bounded full-batch queues keyed by batch `frame_number`, with default `buffer_size_frames = 3`. Freemocap owns per-camera buffering and submits only complete batches to skellytracker.
- Batch together one frame per active camera for detector/pose inference.
- Run CPU-heavy preprocess and postprocess nodes in a small thread pool where safe.
- Serialize ORT inference nodes through the owning `RTMPoseSession` to keep one CUDA/TensorRT context per worker.
- Preserve output order by `(camera_id, frame_number)` before handing results back to freemocap.
- Add counters for dropped frames, queue depth, per-node latency, batch size, and end-to-end latency.
- Define the batching policy explicitly: always wait indefinitely for a full batch with one admitted frame from each active camera. Do not form deadline-based partial batches. Incomplete batches and slow cameras are handled by freemocap.
- Define the backpressure policy explicitly: freemocap drops newly arrived camera frames when its per-camera buffer has no free slot. Skellytracker receives only complete batches and must not re-process any previous batch.
- The full-batch wait must be cancellable for session stop, active-camera reconfiguration, and freemocap pipeline restart. Cancellation should release admitted buffer slots without producing duplicate or partial outputs.

The steady-state realtime flow should look like this:

```mermaid
flowchart LR
  camFrames[CameraFrames] --> ingress[IngressQueue]
  ingress --> batcher[FrameBatcher]
  batcher --> cpuPre[CPUPreprocessLane]
  cpuPre --> gpuInfer[GPUInferenceLane]
  gpuInfer --> cpuPost[CPUPostprocessLane]
  cpuPost --> resequence[OutputResequencer]
  resequence --> sink[RealtimeSkeletonSink]
```

## Zero-Copy Ring Buffers

Design packets as lightweight metadata wrappers around frame-buffer references, not owners of copied image arrays. Freemocap owns raw per-camera ring buffers; skellytracker owns reusable model tensor buffers after a complete batch is submitted:

- Raw camera frames: one freemocap-owned ring per camera, storing references to frames supplied by the capture layer when ownership/lifetime is guaranteed, or storing frames in preallocated shared-memory slots when freemocap owns the memory.
- Preprocessed detector tensors: one reusable batch tensor sized for `batch_size x C x H x W`, plus double or triple buffering only if CPU preprocess and GPU inference run concurrently.
- Pose crop tensors: a separate reusable crop tensor pool sized by `max_persons_per_batch x C x H_pose x W_pose`, because crop count can exceed camera count.
- Postprocess outputs: lightweight arrays/views where possible, copying only when data must outlive the backing ORT output or cross a thread/process boundary.

Node inputs and outputs should pass buffer handles, views, slices, and metadata. A node may copy only at explicit ownership boundaries: camera capture into a skellytracker-owned slot, image layout conversion into an ORT-contiguous tensor, ORT output retention beyond the current graph tick, or serialization across process boundaries.

The default streaming buffer size is `buffer_size_frames = 3`. Advanced tuning may derive a different value from measured latency and frame period:

```text
required_slots_per_camera = ceil(max_pipeline_latency_ms / frame_period_ms) + safety_margin
```

For 30 FPS, the frame period is about 33 ms. The default `buffer_size_frames = 3` gives freemocap a budget of up to roughly 100 ms of admitted buffering per camera. Systems that need fewer dropped input frames can opt into a larger advanced value, accepting the higher latency budget.

Recommended defaults:

- Use `buffer_size_frames = 3` as the default maximum admitted buffering depth for low-latency realtime streaming.
- Allow `buffer_size_frames = 5` or `6` only as an advanced tuning option for systems that prefer fewer dropped inputs over lower latency.
- Cap `buffer_size_frames` to prevent latency creep; when full, drop the newly arrived input frame rather than blocking capture or overwriting an admitted frame.
- Expose `buffer_size_frames` as an advanced config or derive it from `target_fps`, `latency_budget_ms`, and `safety_margin`.
- Track `dropped_frames` and `max_queue_age_ms` so sizing can be tuned from real runs.

## Backpressure And Drop Policy

The streaming pipeline should prioritize freshness and bounded latency over processing every frame. Freemocap owns per-camera buffering; skellytracker owns full-batch processing after freemocap submits a complete batch. The default policy is:

- Each active camera gets a freemocap-owned fixed-size ring buffer with `buffer_size_frames = 3`.
- A camera frame is admitted to freemocap's per-camera buffer only if a free slot is available.
- If no slot is available when a new camera frame arrives, freemocap drops the newly arrived input frame.
- Once a camera frame is admitted, freemocap does not overwrite it with a newer frame while it is waiting to become part of a full batch or while skellytracker still holds a pinned reference.
- Freemocap submits only complete batches containing exactly one frame from each active camera.
- Skellytracker never receives partial batches and does not re-process previously submitted batches to compensate for dropped inputs.
- Skellytracker's batcher must always wait indefinitely for a submitted complete batch. Freemocap owns slow-camera detection, active-camera changes, and pipeline restart/reconfiguration.
- The wait for a full batch must be interruptible by session stop/restart so freemocap can recover from slow cameras or active-camera changes without leaving worker threads blocked.
- Every admitted frame is processed at most once and produces at most one output packet.
- Dropped frames should be counted and surfaced by `camera_id` and `frame_number` range where practical.

This makes the runtime behavior predictable: freemocap can expect at most the advertised buffer depth, and overload shows up as dropped input frames rather than unbounded delay or duplicate skeleton results.

The value returned to freemocap should be a single variable:

- `buffer_size_frames`: total freemocap-owned ring-buffer slots per camera and maximum admitted buffering depth before the input-frame drop policy activates. Default `3`.

For example, the default `buffer_size_frames = 3` means up to 3 frame slots are available per camera before new input frames are dropped, and freemocap should budget for up to 3 frames of buffering delay.

## Phase 2 Acceptance Criteria

Phase 2 is complete when:

- New realtime APIs accept input packets containing `camera_id`, `frame_number`, timestamp metadata, and frame-buffer references.
- Output packets preserve the original `camera_id`, `frame_number`, and timestamp metadata while carrying the same `(keypoints, scores)` data shape as `predict_batch()`.
- `use_streaming_pipeline=True` at session creation enables the streaming executor and reports `buffer_size_frames` startup metadata to freemocap.
- The scheduler always waits indefinitely for full batches and relies on freemocap to handle incomplete batches, slow cameras, active-camera changes, and pipeline restart/reconfiguration.
- Full-batch waits can be cancelled cleanly during session stop/reconfiguration, releasing admitted buffer slots and shutting down worker threads without producing partial or duplicate outputs.
- Freemocap-owned ring buffers default to 3 slots per camera, are bounded, optionally configurable for advanced tuning, and are instrumented with drop/age metrics.
- Freemocap backpressure drops newly arrived input frames when no buffer slot is available; admitted frames are never overwritten while pinned by skellytracker, duplicated, or re-processed.
- Copies are limited to documented ownership/layout boundaries, with tests or instrumentation confirming that packet-to-packet node boundaries do not copy frame arrays unnecessarily.
- Freemocap integration uses the packet API without changing `BaseTracker`, `BaseDetector`, or `BaseObservation`.

## Freemocap Integration Scope

Add the required Phase 2 freemocap work in the sibling checkout at [`C:/Users/Dom/GitHub/freemocap/freemocap`](C:/Users/Dom/GitHub/freemocap/freemocap). Freemocap owns camera selection, pipeline lifecycle, incomplete-batch handling, and user-facing configuration. Skellytracker owns RTMPose session execution and reports the selected `buffer_size_frames` when `use_streaming_pipeline=True`.

Key freemocap files to update:

- [`freemocap/core/pipeline/realtime/realtime_skeleton_inference_node_config.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_skeleton_inference_node_config.py): add `use_streaming_pipeline`, `buffer_size_frames`, and batch-size config needed by skellytracker session creation.
- [`freemocap/core/pipeline/realtime/realtime_skeleton_inference_node.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_skeleton_inference_node.py): pass the new config into `RTMPoseSessionConfig`, store returned streaming startup metadata, and replace partial-batch inference behavior when streaming mode is enabled.
- [`freemocap/core/pipeline/realtime/realtime_pipeline_config.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_pipeline_config.py): include the streaming fields in the top-level realtime config flow.
- [`freemocap/core/pipeline/realtime/realtime_pipeline.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_pipeline.py) and [`freemocap/core/pipeline/realtime/realtime_pipeline_manager.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_pipeline_manager.py): ensure changes to active camera IDs, batch size, `use_streaming_pipeline`, `buffer_size_frames`, execution provider, or RTMPose model selection stop and recreate the pipeline rather than hot-updating an incompatible session.
- [`freemocap/core/pipeline/realtime/realtime_aggregator_node.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/core/pipeline/realtime/realtime_aggregator_node.py): adjust centralized RTMPose synchronization so full-batch streaming results are handled cleanly and incomplete/slow cameras remain freemocap's responsibility.
- [`freemocap/api/http/realtime/realtime_router.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/api/http/realtime/realtime_router.py): derive/validate batch size from `realtimeCameraIds` when needed and surface recoverable skellytracker streaming startup errors to the UI.
- [`freemocap-ui/src/store/slices/realtime/realtime-types.ts`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap-ui/src/store/slices/realtime/realtime-types.ts), [`freemocap-ui/src/store/slices/realtime/realtime-slice.ts`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap-ui/src/store/slices/realtime/realtime-slice.ts), and [`freemocap-ui/src/store/slices/realtime/realtime-thunks.ts`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap-ui/src/store/slices/realtime/realtime-thunks.ts): preserve or send `buffer_size_frames` if the backend API requires it. Do not expose `use_streaming_pipeline` as a normal UI setting in the first implementation.
- [`freemocap-ui/src/components/control-panels/realtime-panel/RtmposeModelConfigPanel.tsx`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap-ui/src/components/control-panels/realtime-panel/RtmposeModelConfigPanel.tsx) and related realtime panels: display startup/status information for `buffer_size_frames` if useful, without coupling it to execution-provider-only controls.

## Freemocap Config And Startup Contract

Freemocap should send these skellytracker-facing values when centralized RTMPose inference is enabled:

- `use_streaming_pipeline`: hard-coded freemocap code toggle for the Phase 2 streaming executor. This should not be a normal UI setting in the first implementation; use a single backend constant or feature flag so support and test coverage stay bounded.
- `buffer_size_frames`: single authoritative buffering variable, default `3`.
- `batch_size`: number of active realtime cameras selected for the pipeline.
- Existing RTMPose model and execution-provider settings.

On startup, skellytracker should return or expose `StreamingPipelineInfo(buffer_size_frames=...)`. Freemocap should persist this on the running realtime pipeline state and use it for UI/status messaging, logging, and expected buffering-delay budgeting.

Freemocap should validate active realtime camera count before startup. If skellytracker enforces a maximum supported camera count, freemocap should surface that as a recoverable configuration error instead of starting a partially compatible pipeline.

`batch_size` and `buffer_size_frames` are independent and must be validated separately:

- `batch_size` controls full-batch width, active camera count, and ORT session/profile shape.
- `buffer_size_frames` controls freemocap's per-camera queue depth and maximum admitted buffering depth before new input frames are dropped.
- Changing `batch_size` requires session teardown/recreation because it can change ORT/TensorRT profile assumptions.
- Changing `buffer_size_frames` requires freemocap buffer reallocation and streaming session restart, but does not change model tensor semantics except for pipeline queue capacity.

## Freemocap Full-Batch Behavior

Freemocap must align the streaming input contract with skellytracker's full-batch-only scheduler:

- When `use_streaming_pipeline=True`, `RealtimeSkeletonInferenceNode` must submit frames with explicit `camera_id`, `frame_number`, timestamp metadata, and frame-buffer references.
- It must not call skellytracker inference with a partial list of images in streaming mode.
- It must not substitute stale camera frames to complete a batch.
- It must wait until one admitted frame is available for every active realtime camera before submitting a full batch.
- Streaming results are indexed by the submitted batch `frame_number`; the aggregator should consume only skeleton results whose `frame_number` exactly matches the aggregation frame being processed.
- If a camera is slow, disconnected, or unable to provide aligned frames, freemocap owns the policy: wait, mark the camera inactive, stop/reconfigure the pipeline, or surface an error. Skellytracker does not form partial batches.
- On pipeline stop/reconfiguration, freemocap must call the skellytracker streaming shutdown path so any indefinite full-batch wait is cancelled cleanly.

## Freemocap Shared-Memory Ownership

Use a concrete pin/release contract for zero-copy frame references crossing from freemocap shared memory into skellytracker:

- Freemocap camera buffers own raw frame memory and expose frame slots by `(camera_id, frame_number, slot_id)`.
- When freemocap submits a full batch to skellytracker, it pins every referenced camera frame slot before submission.
- A pinned slot must not be overwritten by the camera/capture side until skellytracker releases it.
- Skellytracker treats incoming frame references as borrowed, read-only views and releases each slot exactly once after preprocessing has copied/converted the data into skellytracker-owned ORT-contiguous model tensors, or after the batch is cancelled.
- If freemocap cannot pin a slot safely, it must either drop the new input frame before batch admission or use an explicit copy-on-admission fallback for that frame. The fallback should be counted so zero-copy regressions are visible.
- Stop/reconfiguration must release all pinned slots even when a full-batch wait or in-flight preprocess is cancelled.

This keeps zero-copy safe without making skellytracker responsible for freemocap's camera ring-buffer lifecycle.

## Freemocap Backpressure Responsibilities

Skellytracker drops newly arrived input frames when its `buffer_size_frames` capacity is full, but freemocap should make overload visible and recoverable:

- Track and log per-camera dropped-input counts reported by skellytracker.
- Surface blocked or waiting full-batch state in backend logs and, if useful, UI status.
- Restart the streaming session when active camera IDs, `batch_size`, hard-coded streaming flag, `buffer_size_frames`, provider, or RTMPose model changes.
- Avoid repeatedly submitting the same `camera_id`/`frame_number` packet; every submitted frame should be unique and should be processed at most once.
- Ensure freemocap's own shared-memory camera buffers use the pin/release contract so skellytracker's borrowed zero-copy references remain valid until release.

## Freemocap Tests

Add tests in [`freemocap/tests/test_system_gpu_and_rtmpose_config.py`](C:/Users/Dom/GitHub/freemocap/freemocap/freemocap/tests/test_system_gpu_and_rtmpose_config.py) and new focused realtime tests as needed:

- `_build_session()` passes `use_streaming_pipeline`, `buffer_size_frames`, and camera-derived `batch_size` into `RTMPoseSessionConfig`.
- Session startup captures and exposes `StreamingPipelineInfo(buffer_size_frames=...)`.
- Streaming mode does not call skellytracker inference when only a partial camera batch is available.
- Streaming mode submits exactly one packet per active camera for each full batch, preserving `camera_id` and `frame_number`.
- Pipeline manager recreates the pipeline when active camera IDs, batch size, `use_streaming_pipeline`, `buffer_size_frames`, provider, or model selection changes.
- Stop/reconfiguration cancels the skellytracker streaming wait and releases admitted buffers.
- Frontend realtime config preserves `buffer_size_frames` when needed, with default `buffer_size_frames = 3`; `use_streaming_pipeline` is controlled by a hard-coded freemocap backend toggle rather than a normal UI setting.

## Future Phase: Sidecar Integration

After Phase 1 graph parity is proven, use [`specs/sidecar-spec.md`](specs/sidecar-spec.md) as the declarative contract for detector and pose node construction, especially for YOLO26 work already described in [`50_yolo26_nano_detection.plan.md`](50_yolo26_nano_detection.plan.md). The graph should not hardcode tensor names, output field order, class IDs, batch behavior, or NMS requirements for sidecar-backed models.

For Phase 1, keep the existing YOLOX and RTMPose node implementations explicit. In the future sidecar phase, add sidecar-backed detector nodes so YOLO26 can replace YOLOX without expanding `RTMPoseSession.predict_batch()` conditionals.

## Compatibility And Migration

Keep this migration incremental:

Phase 1:

1. Add graph primitives and unit tests with fake nodes.
2. Wrap the existing RTMPose batch stages as graph nodes while preserving exact outputs.
3. Make `predict_batch()` call the graph by default after parity is proven. During validation, compare against a private legacy helper or an internal-only `use_batch_graph_pipeline` flag; do not confuse this with the Phase 2 `use_streaming_pipeline` config.
4. Route `predict_pose_from_bboxes()` through the pose subgraph.

Phase 2:

5. Add packet-based realtime APIs that preserve `camera_id`, `frame_number`, and timestamp metadata through the graph.
6. Add `use_streaming_pipeline` session config, streaming startup metadata, and zero-copy ring-buffer execution for freemocap once the batch graph and packet API are stable.
7. Add freemocap backend config/API/session startup integration.
8. Add freemocap full-batch-only skeleton-node and aggregator changes.
9. Add freemocap UI config preservation and startup/status display for `buffer_size_frames` if the backend API exposes it.
10. Add freemocap integration and realtime soak tests.

Future sidecar phase:

11. Add sidecar-backed detector node construction only after YOLOX/RTMPose graph parity is stable.
12. Validate YOLO26 or other sidecar-backed detectors against the same graph executor without broadening Phase 1.
13. Remove the legacy imperative path after parity tests and realtime soak testing pass.

Do not introduce async return types into `BaseTracker`, `BaseDetector`, or `BaseObservation`. If async APIs become useful later, add new methods rather than changing existing signatures.

## Tests And Validation

Add focused tests in the RTMPose test area and a new pipeline test module, grouped by phase.

Phase 1 tests:

- Graph executor tests for DAG validation, missing inputs, node timing, and deterministic output order.
- RTMPose parity tests comparing legacy `predict_batch()` output to graph `predict_batch()` on fixed inputs.
- `predict_pose_from_bboxes()` tests proving detector nodes are skipped.
- Empty-detection and no-crop tests.
- Batch-size tests for 1 camera, multiple cameras, and mixed person counts per image.

Phase 2 tests:

- Packet metadata round-trip tests proving `camera_id`, `frame_number`, and timestamps survive full-batch processing and output resequencing.
- Session creation tests proving the hard-coded `use_streaming_pipeline` path reports `buffer_size_frames`, while the disabled path preserves legacy behavior.
- Zero-copy tests or instrumentation proving packets carry references/views through node boundaries and copies happen only at documented ownership/layout boundaries.
- Ring-buffer tests for default `buffer_size_frames = 3`, input-frame drop behavior when full, and configurable buffer length.
- Backpressure tests proving admitted frames are processed at most once and previously processed frames are never reused to fill later batches.
- Realtime scheduler tests with fake slow nodes to verify backpressure, ordered outputs, bounded queues, and cancellable full-batch waits during stop/reconfiguration.

Use `pytest skellytracker/tests` for full validation, plus targeted RTMPose/pipeline tests during development. If GPU/TensorRT is unavailable locally, keep CPU/fake-node tests mandatory and document GPU validation as a separate manual check.

## Related Plans

- [20_single_global_realtime_pipeline.plan.md](20_single_global_realtime_pipeline.plan.md) — singleton pipeline and apply recreate; Phase 2 must not bypass manager lifecycle.
- [10_remove_ep_fallback.plan.md](10_remove_ep_fallback.plan.md) — graph infer nodes use strict sessions from `RTMPoseSession.create()`.
- [30_realtime_batch_size.plan.md](30_realtime_batch_size.plan.md) — **authority for `batch_size`** and ring-buffer partial-read gating; do not redefine batch semantics here.
- [40_sidecar_spec_updates.plan.md](40_sidecar_spec_updates.plan.md) — sidecar contract for future generic detector nodes.
- [50_yolo26_nano_detection.plan.md](50_yolo26_nano_detection.plan.md) — sidecar-backed detector path must be stable before the future sidecar graph phase.
- [future_hand_and_face_detection.plan.md](future_hand_and_face_detection.plan.md) — parallel future work; no dependency either way.
