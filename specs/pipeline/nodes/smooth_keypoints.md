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
filter or a constant-velocity Kalman filter. It can hold a missing point for some frames, refuse a
point that moves too fast, and reset the filter state of a row after a number of misses
([ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6). A
`smooth_keypoints` node after the last detector does not make a pipeline stateful
([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 5).

## Fields

<!-- node-table:params -->
| Param | Type | Range | Default | Live | Description | Source |
|---|---|---|---|---|---|---|
| `filter` | `Literal['one_euro', 'kalman']` |  | `"one_euro"` | no | The filter. | KeypointSmoothingConfig.kind |
| `min_cutoff` | `float` | > 0.0 | `1.0` | yes | one_euro: the minimum cutoff frequency. | KeypointSmoothingConfig |
| `beta` | `float` | >= 0.0 | `0.0` | yes | one_euro: the speed coefficient. | KeypointSmoothingConfig |
| `d_cutoff` | `float` | > 0.0 | `1.0` | yes | one_euro: the cutoff frequency of the derivative. | KeypointSmoothingConfig |
| `process_noise_pos` | `float` | > 0.0 | `1.0` | yes | kalman: the process noise of the position (pixels² per frame). | KalmanKeypointSmoothingConfig |
| `process_noise_vel` | `float` | > 0.0 | `0.1` | yes | kalman: the process noise of the velocity. | KalmanKeypointSmoothingConfig |
| `measurement_noise` | `float` | > 0.0 | `10.0` | yes | kalman: the measurement noise (pixels²). | KalmanKeypointSmoothingConfig |
| `max_gap_frames` | `int \| None` | >= 1 | `null` | no | Hold the last value of a missing point for this many frames. Empty: no hold. | KeypointSmoothingConfig |
| `max_velocity` | `float \| None` | > 0.0 | `null` | yes | Refuse a point that moves more than this many pixels per frame. Empty: accept each point. | KeypointSmoothingConfig |
| `max_consecutive_misses` | `int \| None` | >= 1 | `null` | no | Reset the filter state after this many frames with no point. Empty: no reset. | KeypointResetPolicyConfig |
| `backoff_multiplier` | `float` | >= 1.0 | `2.0` | no | Multiply the miss limit by this value after a reset with no detection between. | KeypointResetPolicyConfig |
| `max_backoff_misses` | `int \| None` | >= 1 | `null` | no | The largest miss limit after back-off. Empty: no limit. | KeypointResetPolicyConfig |
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
- `backoff_multiplier` and `max_backoff_misses` have an effect only with `max_consecutive_misses`
  (`V-node.smooth_keypoints-2`).
- The unit of time is one frame. `max_velocity` is in pixels per frame. `min_cutoff` and `d_cutoff`
  are in cycles per frame. `max_gap_frames`, `max_consecutive_misses` and `max_backoff_misses` count
  the frames that the node runs on.
- The output `keypoints` has the names, the rows and the shapes of the input. The node changes only
  x and y. The visibility, z and `track_ids` of each point and row pass through unchanged. An output
  row is present when it has a point whose x and y are not NaN.

## Behaviour

1. **Running mode.** In the running mode `image`, the output is the input, and the node keeps no
   state ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 2). The
   steps that follow apply to `video` and `live`.
2. **Empty input.** Before the first input that is not empty, the node does not run, and its output
   is empty. After it, an empty `keypoints` input does not stop the node. The node runs on rows in
   which each point is missing, with the shapes of the last input. This is an exception to the
   empty-input rule of
   [ADR-7NY2](../../../decisions/entries/7NY2-pipeline-form-graph-and-nodes.md) item 6, because an
   empty input is a miss for the gap hold and for the reset.
3. **dt.** In `video`, `dt = 1`. In `live`:

   ```text
   dt = (timestamp_ms - previous timestamp_ms) / frame_interval_ms
   ```

   The previous `timestamp_ms` is that of the last frame that the node ran on. `frame_interval_ms`
   is the nominal frame interval of the camera, 1000 / the nominal frame rate. `timestamp_ms` must
   increase from frame to frame (`V-node.smooth_keypoints-3`).
4. **State.** Each row `i` has its own state, with one state for each point `j`. A point is valid
   when its x and its y are not NaN. The state of a row is empty at the start and after a reset
   (step 9).
5. **First frame of a row.** When the state of row `i` is empty, row `i` of the output is row `i` of
   the input. The state of each point is then:
   - `est = (x, y)` when the point is valid, else NaN;
   - the one-euro derivative `d = 0` and the Kalman velocity `v = 0`, for each axis;
   - `P = P_init = diag(10 · measurement_noise, 100 · process_noise_vel)` for each axis;
   - the gap counter `missed = 0` when the point is valid, else 1.
6. **Next frames.** For each point of a row with a state:
   1. `has_est` is true when `est` is not NaN.
   2. `detected` is true when the point is valid. When `detected`, `has_est` and `max_velocity` are
      all true or set, the node refuses a point that moves too far:

      ```text
      distance = sqrt((x - est_x)² + (y - est_y)²)
      detected = distance <= max_velocity · dt
      ```

   3. `missed = 0` when `detected`, else `missed + 1`.
   4. `hold` is true when the point is not `detected`, `has_est` is true, `max_gap_frames` is set
      and `missed <= max_gap_frames`.
   5. The filter of step 7 or step 8 gives the output point and the new state.
7. **Filter `one_euro`.** Each axis has its own values. `z` is the measurement of the axis (x or y),
   `est` its estimate and `d` its derivative.

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
8. **Filter `kalman`.** Each axis has its own state `[position, velocity]` = `[est, v]` and its own
   covariance `P` (2 × 2). `F = [[1, dt], [0, 1]]`, `Q = diag(process_noise_pos, process_noise_vel)`,
   `H = [1, 0]` and `R = measurement_noise`. `Q` does not change with `dt`.
   - Not `has_est`: `v = 0` and `P = P_init`. When `detected`, `est = z` and the output is `z`. Else
     `est = NaN` and the output is NaN.
   - `has_est`: first the prediction:

     ```text
     est⁻ = est + v · dt
     P⁻   = F · P · Fᵀ + Q
     ```

     - `detected`:

       ```text
       S   = P⁻[0][0] + R
       K   = (P⁻[0][0] / S, P⁻[1][0] / S)
       est = est⁻ + K[0] · (z - est⁻)
       v   = v + K[1] · (z - est⁻)
       P   = (I - K · H) · P⁻
       ```

       The output is `est`.
     - `hold`: `est = est⁻` and `P = P⁻`. `v` does not change. The output is `est⁻`.
     - Else: `est = NaN`, `v = 0` and `P = P⁻`. The output is NaN.
9. **Reset.** After the filter step of each frame, the node counts the misses of each row. A miss is
   a frame where the input row has no valid point, before step 6.2. Each row has the counters
   `misses` and `resets`. They start at 0, and a reset of the state does not clear them.
   - When the input row has a valid point, `misses = 0` and `resets = 0`. Else `misses = misses + 1`.
   - When `max_consecutive_misses` is set:

     ```text
     limit = max_consecutive_misses · backoff_multiplier^resets
     limit = min(limit, max_backoff_misses)     (only when max_backoff_misses is set)
     ```

     When `misses >= limit`, the state of the row becomes empty, `misses = 0` and
     `resets = resets + 1`. The next frame of the row is a first frame (step 5).
10. **Rows.** Row `i` of the input gives row `i` of the output. Without an `associate` node, the
    rows have no track identity, so row `i` of two frames can be two persons
    ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1).

## Validation rules

- [ ] `V-node.smooth_keypoints-1` A file must not write a param of the filter that `filter` does not select. With `one_euro`, it must not write `process_noise_pos`, `process_noise_vel` or `measurement_noise`. With `kalman`, it must not write `min_cutoff`, `beta` or `d_cutoff`.
- [ ] `V-node.smooth_keypoints-2` A file that writes `backoff_multiplier` or `max_backoff_misses` must also write `max_consecutive_misses`.
- [ ] `V-node.smooth_keypoints-3` In the running mode `live`, the `timestamp_ms` of each frame must be greater than the `timestamp_ms` of the frame before. The host checks this at run time.

## Implementer guidance

- The Behaviour follows skellytracker/core/temporal_processing/keypoint_filtering.py
  (`apply_one_euro_filter`, `apply_kalman_filter`) and
  skellytracker/core/temporal_processing/keypoint_reset_policy.py (`KeypointResetPolicy.should_reset`).
  With `dt = 1`, the reference gives the same results as that code. The notes of the vector file
  give the comparison.
- Today skellytracker/core/tracker/detection_stage.py (`_dt_from_context`) always gives `dt = 1.0`,
  so the params are in frame units. This section keeps frame units, and uses `timestamp_ms` only in
  `live`. The section `pipeline.running` gives `frame_interval_ms` as the run parameter "frame interval".
- Today the velocity test compares the distance with `max_velocity`. This section compares it with
  `max_velocity · dt`. The two are the same when `dt = 1`.
- The reset is different from today. Today the policy calls `reset_temporal_state()` of a detector
  (skellytracker/core/tracker/detection_stage.py (`DetectionStage._apply_reset_policy`)), to free a
  stuck MediaPipe VIDEO-mode tracker. In this section, the reset clears the filter state of the
  node. A pipeline file cannot call a detector. Today a miss is a raw detector output with no valid
  point. In this section, a miss is an input row with no valid point.
- The one-euro derivative `d` keeps its value while a point is missing, and also when the point
  starts again without a reset. Today's code does the same.
- A held point keeps the visibility of the input, which is 0 for a missing point
  ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 1). Today's code
  does the same. A node that filters on visibility drops a held point.
- On the first frame of a row, the output is the input. The velocity test does not apply.

## Authoring guidance

- With the defaults, `alpha(1, 1) ≈ 0.863`, so the smoothing is light. A smaller `min_cutoff` gives
  more smoothing and more lag. A larger `beta` gives less lag when a point moves fast.
- Use `max_velocity` together with `max_gap_frames`. Then a refused point holds its last estimate
  and does not become NaN.
- With the filter `kalman`, a held point moves on with its velocity. With `one_euro`, it stays at
  its last estimate.
- Use `max_consecutive_misses` to stop a long hold, and to clear the old derivative or covariance
  of a row after the person leaves the image.
- To smooth the final keypoints, put the node after the last detector. Then it does not limit the
  batch ([ADR-99MH](../../../decisions/entries/99MH-pipeline-outputs-and-running.md) item 5).

## Examples

The vector file [`node.smooth_keypoints.yaml`](../vectors/node.smooth_keypoints.yaml) holds the
worked cases.

```yaml
- id: smooth
  type: smooth_keypoints
  inputs: {keypoints: pose.keypoints}
  params: {min_cutoff: 0.5, beta: 0.05, max_gap_frames: 3, max_velocity: 80.0}
```
