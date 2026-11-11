# 99MH — Pipeline outputs with an instance dimension; running modes; batch k × cameras, and camera count for stateful pipelines; session sharing; load checks

**Status:** accepted, 2026-11-11 (user).

## Decision

1. **Output format.** One format with an instance dimension. `I = max_instances` is fixed for the
   run (default 1). Each frame has the same shapes.
   - `InstanceKeypoints`: `point_names` (prefixed, for example `body.nose`), `xyz` `(I, P, 3)` (z
     NaN for a 2D model), `score` `(I, P)`, `present` `(I,)`, `track_ids` `(I,)`, with
     `instance(i)`, `single()` and `by_track()`.
   - `InstanceBoxes`: `xyxy` `(I, 4)`, `score`, `present`, `track_ids`.
   - The `outputs:` block maps public names to ports. `process_batch` returns, for each camera, a
     dict of output name to value, with `frame_index`, `image_size` and `timestamp_ms`.
   - `output_schema` gives `port_type`, `point_names`, `geometry`, `depth_unit`, `max_instances`,
     `tracked`, `instance_source` and `edges` for each output, before frame 0. The edges come from
     the sidecar overlay or the MediaPipe YAML files.
   - The node that makes the instances has `max_instances` (default 1). Present rows come first, by
     descending score; padding comes last. A missing point is NaN with score 0. No row and no
     point is dropped. A node that takes ROIs runs once for each present row. `concat` joins row i to
     row i and must not mix instance sources. A fan-out child adds point columns to the row of its
     person.
   - Without an `associate` node, `track_ids` is -1, and a row has no identity across frames. The
     cameras stay separate. I > 1 is allowed. No adapter to the old `Observation`.
2. **Running modes.** `running_mode` is `image`, `video` or `live`, set by the run. The file is the
   same in each mode. `image`: `@prev` is always empty, the frame size can change, one camera.
   `video`: each frame in order. `live`: `frame_index` can skip, and the caller drops frames. The
   temporal nodes use `timestamp_ms`. A `video` run with no timestamps uses
   `frame_index × 1000 / fps` (run parameter `fps`, default 30).
3. **Cameras.** `start_pipeline` takes `camera_ids`, required. In `video`, `process_batch` must get
   exactly those keys. In `live`, a call can hold a subset of them.
4. **Batch.** `video` and `image` batch to k × cameras, with k chosen at start from the free VRAM
   (k is 1 until the hardware track gives the free VRAM). `live` batches to the camera count. A node
   that takes ROIs batches to that batch × the `I` of its instance source. Each artifact is
   converted to its batch at start. A missed frame or crop is padded, and its result is dropped.
5. **Stateful pipelines.** A pipeline is stateful when it has an explicit `@prev` input, or a
   temporal node upstream of a detector node: `smooth_roi`, `smooth_keypoints`, `redetect`, or
   `mediapipe_tasks` in VIDEO mode. A temporal node with no detector downstream does not count. In
   `video` mode a stateful pipeline runs at batch = camera count. There is no user toggle. The run
   logs one line that names the nodes, and gives the warning `batch_limited_by_state`
   ([ADR-8NVD](8NVD-pipeline-api-warnings-and-catalog.md)).
6. **Session sharing.** In one process, nodes with the same artifact `sha256`, batch and execution
   share one inference session. The file says nothing about it.
7. **Load checks.** Unique ids and output names; each input refers to a port that exists; port types
   match (`image`, `roi`, `keypoints`, `detections`, `tensor`); the graph is acyclic except through
   `@prev`; param names, types and ranges; each sidecar hash; each model role matches its use; each
   tap names a port; no output or tap is `@prev` or the frame; point names do not collide;
   `max_instances` limits and instance sources. Start checks: each
   artifact is available, the EP is supported, the replay files cover the frames.

## Reason

- Fixed shapes for each frame make the output easy to stack and to store.
- A detector whose input depends on the previous frame cannot take k frames of one camera in a row.
  The smoothed ROI is the next crop, so `smooth_roi` blocks it too. A temporal node with no detector
  downstream runs on the host, frame by frame, after the batched pass.
- A toggle that drops the previous-frame logic changes the keypoints, and k depends on the machine.
- Conversion at start is slow, so the cameras must be known then. A fixed set of keys finds a camera
  that drops out.

## Alternatives rejected

- A separate `tracks` output kind, and string lineage keys such as `A/left`.
- Infer the cameras from the first frame.
- A toggle that turns the previous-frame logic off for bigger batches.
- Batch sizes that fill VRAM in `live`; frame dropping inside the run in v1.

## Open work

See [open-work.md](../open-work.md).
