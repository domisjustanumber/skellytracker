---
id: node.smooth_keypoints
title: Smooth keypoints
kind: node
vectors: vectors/node.smooth_keypoints.yaml
status: {spec: draft}
---

# Smooth keypoints

> This section is a draft. Its fields and rules can change before the section becomes `stable`.

The node `smooth_keypoints` filters the points of each instance row over time. It uses a one-euro
filter or a constant-velocity Kalman filter. It can hold a missing point for some time, refuse a
point that moves too fast, and reset the filter state of a row after a time with no point
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). The node
uses time units: the time step comes from `timestamp_ms`, a rate is per second and a duration is in
milliseconds. A `smooth_keypoints` node with no detector node downstream does not make a pipeline
stateful ([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 5).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `filter` | `Literal['one_euro', 'kalman']` |  | `"one_euro"` | no | The filter. | KeypointSmoothingConfig.kind |
| `min_cutoff` | `float` | > 0.0 | `1.0` | yes | one_euro: the minimum cutoff frequency, in Hz. | KeypointSmoothingConfig |
| `beta` | `float` | >= 0.0 | `0.0` | yes | one_euro: the speed coefficient, in Hz per px/s. | KeypointSmoothingConfig |
| `d_cutoff` | `float` | > 0.0 | `1.0` | yes | one_euro: the cutoff frequency of the derivative, in Hz. | KeypointSmoothingConfig |
| `process_noise_pos` | `float` | > 0.0 | `30.0` | yes | kalman: the process noise of the position, in px² per second. | KalmanKeypointSmoothingConfig (1 px² per frame at 30 fps) |
| `process_noise_vel` | `float` | > 0.0 | `2700.0` | yes | kalman: the process noise of the velocity, in (px/s)² per second. | KalmanKeypointSmoothingConfig (0.1 (px/frame)² per frame at 30 fps) |
| `measurement_noise` | `float` | > 0.0 | `10.0` | yes | kalman: the measurement noise, in px². | KalmanKeypointSmoothingConfig |
| `max_gap_ms` | `float \| None` | > 0.0 | `null` | no | Hold the last value of a missing point for this many milliseconds after its last detection. Empty: no hold. | KeypointSmoothingConfig.max_gap_frames |
| `max_velocity` | `float \| None` | > 0.0 | `null` | yes | Refuse a point that moves faster than this many pixels per second since its last detection. Empty: accept each point. | KeypointSmoothingConfig |
| `reset_after_ms` | `float \| None` | > 0.0 | `null` | no | Clear the filter state of a row after this many milliseconds with no valid point. Empty: no reset. | KeypointResetPolicyConfig |
<!-- /node-table:params -->

<!-- node-table:ports -->
| Port | Direction | Type |
|---|---|---|
| `keypoints` | input | `keypoints` |
| `keypoints` | output | `keypoints` |
<!-- /node-table:ports -->

- The filter `one_euro` uses `min_cutoff`, `beta` and `d_cutoff`. The filter `kalman` uses
  `process_noise_pos`, `process_noise_vel` and `measurement_noise`. A file must not write a param
  of the other filter (`V-node.smooth_keypoints-1`).
- The units: `min_cutoff` and `d_cutoff` are in Hz. `max_velocity` is in pixels per second.
  `process_noise_pos` is in px² per second, `process_noise_vel` in (px/s)² per second and
  `measurement_noise` in px². `max_gap_ms` and `reset_after_ms` are in milliseconds.
- The defaults of the filter `kalman` are the frame-unit defaults of today at 30 fps: 1 px² and
  0.1 (px/frame)² per frame give 30 px²/s and 2700 (px/s)²/s.
- The output `keypoints` has the names, the rows and the shapes of the input. The node changes only
  x and y. The score, z, `instance_score` and `track_ids` of each point and row pass through
  unchanged. An output row
  is present when it has a point whose x and y are not NaN.

## Behaviour

1. **Running mode.** In the running mode `image`, the output is the input, and the node keeps no
   state ([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 2). The
   steps that follow apply to `video` and `live`.
2. **Empty input.** Before the first input that is not empty, the node does not run, and its output
   is empty. After it, an empty `keypoints` input does not stop the node. The node runs on rows in
   which each point is missing, with the shapes of the last input. This is a rule of the node, as
   [Graph](../graph.md#behaviour) item 6 allows: an empty input is a miss for the gap hold and for
   the reset.
3. **Time.** `t` is the `timestamp_ms` of the frame ([Running](../running.md#behaviour)). The time
   step, in seconds, is:

   ```text
   dt = (t - previous t) / 1000
   ```

   The previous `t` is that of the last frame that the node ran on. `timestamp_ms` must increase
   from frame to frame, in `video` and in `live` (`V-node.smooth_keypoints-3`).
4. **State.** Each row `i` has its own state, with one state for each point `j`. A point is valid
   when its x and its y are not NaN. The state of a row is empty at the start and after a reset
   (step 9).
5. **First frame of a row.** When the state of row `i` is empty, row `i` of the output is row `i` of
   the input. The state of each point is then:
   - `est = (x, y)` when the point is valid, else NaN;
   - the one-euro derivative `d = 0` and the Kalman velocity `v = 0`, for each axis;
   - `cov = cov_init = diag(10 · measurement_noise, 9000)` for each axis. The velocity variance
     9000 (px/s)² is a constant: 10 (px/frame)² at 30 fps;
   - `t_detected = t` when the point is valid, else empty. `t_detected` is the time of the last
     detection of the point.

   The row also keeps `t_valid = t`, the time of the last frame on which the input row had a valid
   point, or the time of the frame that made the state.
6. **Next frames.** For each point of a row with a state:
   1. `has_est` is true when `est` is not NaN.
   2. `detected` is true when the point is valid. When `detected` and `has_est` are true and
      `max_velocity` is set, the node refuses a point that moves too far since its last detection:

      ```text
      distance = sqrt((x - est_x)² + (y - est_y)²)
      detected = distance <= max_velocity · (t - t_detected) / 1000
      ```

   3. When `detected`, `t_detected = t`.
   4. `hold` is true when the point is not `detected`, `has_est` is true, `max_gap_ms` is set and
      `t - t_detected <= max_gap_ms`.
   5. The filter of step 7 or step 8 gives the output point and the new state.
7. **Filter `one_euro`.** Each axis has its own values. `z` is the measurement of the axis (x or y),
   `est` its estimate and `d` its derivative, in pixels per second.

   ```text
   alpha(f, dt) = 1 / (1 + 1 / (2π · f · dt))
   ```

   - `detected` and `has_est`:

     ```text
     a_d = alpha(d_cutoff, dt)
     d   = a_d · (z - est) / dt + (1 - a_d) · d
     a   = alpha(min_cutoff + beta · |d|, dt)
     est = a · z + (1 - a) · est
     ```

     The output is `est`.
   - `detected` and not `has_est`: `est = z`. The output is `z`. `d` does not change.
   - `hold`: the output is `est`. The state does not change.
   - Else: the output is NaN, and `est = NaN`. `d` does not change.
8. **Filter `kalman`.** Each axis has its own state `[position, velocity]` = `[est, v]`, with `v` in
   pixels per second, and its own covariance `cov` (2 × 2). The process noise grows with `dt`:

   ```text
   F     = [[1, dt], [0, 1]]
   noise = diag(process_noise_pos, process_noise_vel) · dt
   H     = [1, 0]
   ```

   - Not `has_est`: `v = 0` and `cov = cov_init`. When `detected`, `est = z` and the output is `z`.
     Else `est = NaN` and the output is NaN.
   - `has_est`: first the prediction:

     ```text
     est⁻ = est + v · dt
     cov⁻ = F · cov · Fᵀ + noise
     ```

     - `detected`:

       ```text
       s    = cov⁻[0][0] + measurement_noise
       gain = (cov⁻[0][0] / s, cov⁻[1][0] / s)
       est  = est⁻ + gain[0] · (z - est⁻)
       v    = v + gain[1] · (z - est⁻)
       cov  = (I₂ - gain · H) · cov⁻
       ```

       `I₂` is the 2 × 2 identity matrix. The output is `est`.
     - `hold`: `est = est⁻` and `cov = cov⁻`. `v` does not change. The output is `est⁻`.
     - Else: `est = NaN`, `v = 0` and `cov = cov⁻`. The output is NaN.
9. **Reset.** After the filter step of each frame, the node examines each row with a state. When
   the input row has a valid point, `t_valid = t`. Else, when `reset_after_ms` is set and
   `t - t_valid >= reset_after_ms`, the state of the row becomes empty. The next frame of the row is
   a first frame (step 5). A miss is a frame where the input row has no valid point, before
   step 6.2.
10. **Rows.** Row `i` of the input gives row `i` of the output. Without an `associate` node, the
    rows have no track identity, so row `i` of two frames can be two persons
    ([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 1).

## Validation rules

- [ ] `V-node.smooth_keypoints-1` A file must not write a param of the filter that `filter` does not select. With `one_euro`, it must not write `process_noise_pos`, `process_noise_vel` or `measurement_noise`. With `kalman`, it must not write `min_cutoff`, `beta` or `d_cutoff`.
- [ ] `V-node.smooth_keypoints-3` In the running modes `video` and `live`, the `timestamp_ms` of each frame must be greater than the `timestamp_ms` of the frame before. The host refuses the frame at run time.

## Implementer guidance

- The Behaviour follows skellytracker/core/temporal_processing/keypoint_filtering.py
  (`apply_one_euro_filter`, `apply_kalman_filter`) and
  skellytracker/core/temporal_processing/keypoint_reset_policy.py (`KeypointResetPolicy.should_reset`).
  Today's code uses frame units: skellytracker/core/tracker/detection_stage.py
  (`_dt_from_context`) always gives `dt = 1.0`. At 1000 ms per frame, the time-unit params have the
  numbers of the frame-unit params, and most cases of the vector file use this rate. The notes of
  the vector file give the comparison.
- Today the velocity test compares the distance with `max_velocity` for each frame. This section
  compares it with `max_velocity` times the time since the last detection. The two are the same at
  1000 ms per frame for a point that was detected on the frame before.
- Today's reset policy counts misses, with a back-off (`max_consecutive_misses`,
  `backoff_multiplier`, `max_backoff_misses`), and calls `reset_temporal_state()` of a detector
  (skellytracker/core/tracker/detection_stage.py (`DetectionStage._apply_reset_policy`)), to free a
  stuck MediaPipe VIDEO-mode tracker. In this section, the reset clears the filter state of the node
  after a time with no valid point, with no back-off. A pipeline file cannot call a detector. The
  node `mediapipe_tasks` has no reset: a VIDEO-mode landmarker finds a person again after a gap
  ([ADR-6JWJ](../decisions/entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md)).
- The one-euro derivative `d` keeps its value while a point is missing, and also when the point
  starts again without a reset. Today's code does the same.
- A held point keeps the score of the input, which is 0 for a missing point
  ([Decoded keypoints](../../model-sidecar/post/keypoint/schema.md#decoded-keypoints)). Today's code
  does the same. A node that filters on the score drops a held point.
- On the first frame of a row, the output is the input. The velocity test does not apply.

## Authoring guidance

- At 30 fps with the default cutoff of 1 Hz, `alpha(1, 1/30) ≈ 0.17`, so the smoothing is strong.
  A smaller `min_cutoff` gives more smoothing and more lag. A larger `beta` gives less lag when a
  point moves fast.
- The params do not depend on the frame rate. The same file gives the same filter at 30 fps and at
  60 fps, and in `live` with dropped frames.
- Use `max_velocity` together with `max_gap_ms`. Then a refused point holds its last estimate and
  does not become NaN.
- With the filter `kalman`, a held point moves on with its velocity. With `one_euro`, it stays at
  its last estimate.
- Use `reset_after_ms` to stop a long hold, and to clear the old derivative or covariance of a row
  after the person leaves the image.
- To smooth the final keypoints, put the node after the last detector. Then it does not limit the
  batch ([ADR-0WJB](../../../decisions/entries/0WJB-pipeline-outputs-running-no-session-sharing.md) item 5).

## Examples

The vector file [`node.smooth_keypoints.yaml`](../vectors/node.smooth_keypoints.yaml) holds the
worked cases.

The frame-unit params `min_cutoff: 0.5`, `beta: 0.05`, `max_gap_frames: 3` and
`max_velocity: 80.0` at 30 fps become these time-unit params:

```yaml
- id: smooth
  type: smooth_keypoints
  inputs: {keypoints: body.keypoints}
  params: {min_cutoff: 15.0, beta: 0.05, max_gap_ms: 100, max_velocity: 2400.0}
```
