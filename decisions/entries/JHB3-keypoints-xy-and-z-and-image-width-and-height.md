# JHB3 — A keypoints value has `xy` and an optional `z`; no `by_track()`; `image_width` and `image_height`

**Status:** absorbed into [`outputs.md#fields`](../../specs/pipeline/outputs.md#fields), [`outputs.md#behaviour`](../../specs/pipeline/outputs.md#behaviour), [`outputs.md#validation-rules`](../../specs/pipeline/outputs.md#validation-rules), [`outputs.md#authoring-guidance`](../../specs/pipeline/outputs.md#authoring-guidance), [`merge.md#validation-rules`](../../specs/pipeline/nodes/merge.md#validation-rules), [`assign_keypoints.md#validation-rules`](../../specs/pipeline/nodes/assign_keypoints.md#validation-rules), [`values.py`](../../skellytracker/core/pipelines/values.py), [`canonical.py`](../../skellytracker/core/pipelines/canonical.py), [`run.py`](../../skellytracker/core/pipelines/run.py), 2026-11-17 (absorb pass, user; PR: pending).

## Decision

1. **`xy` and an optional `z`.**
   - A `keypoints` value holds `xy`, with the shape `(I, P, 2)` and the type float64: x and y of
     each point, in source-image pixels. A missing point is NaN in `xy`.
   - A `keypoints` value holds `z`, with the shape `(I, P)` and the type float64, only for a `3d`
     output: the root-relative depth of each point in `depth_unit`. A `2d` output has no `z`. In
     the Python API, `z` is then `None`. For a `3d` output, z of a missing point is NaN.
   - The value has `geometry`, `"2d"` or `"3d"`. A consumer then needs no output schema to know if
     the value has `z`. The output schema keeps `geometry` and `depth_unit`.
   - No value has an `xyz` field. The package has no `xyz` property and no alias.
   - The canonical form (`CanonicalKeypoints`) has the same fields `xy`, `z` and `geometry`.
     `instance()` and `single()` give the keys `xy` and `z`.
   - `concat` and `merge` still refuse a mix of `2d` and `3d` inputs (`V-node.concat-3`,
     `V-node.merge-3`).
2. **No `by_track()`.**
   - `InstanceKeypoints` has no method `by_track()`. `instance()` and `single()` stay. `track_ids`
     and `tracked` do not change.
   - A consumer reads the one person of this version from row 0. It checks `present[0]` first.
   - An accessor by track id comes back with the `associate` node.
3. **`image_width` and `image_height`.**
   - The result of one camera for one call has `image_width` and `image_height`: ints, in pixels.
     It has no `image_size` and no alias.
   - `V-pipeline.outputs-3` keeps its ID. The reserved output names are `frame_index`,
     `image_width`, `image_height`, `timestamp_ms` and `node_ran`.

This entry refines two texts. The first is the `InstanceKeypoints` text of
[ADR-W5QD](W5QD-pipeline-entries-consolidation.md) item 2: the names `instance(i)` and `single()`
stay, and `by_track()` goes. The second is item 5 of
[ADR-Q5BN](Q5BN-node-ran-in-the-camera-result.md): `image_width` and `image_height` replace
`image_size` in the list of names. This entry supersedes neither of the two entries, and their
other rules stay.

## Reason

- No text gave a reason for the NaN padding of z. A consumer that tests three finite coordinates
  drops each 2D point. freemocap has such a test in its mapping code. The ONNX path wrote NaN z
  for each model.
- `by_track()` had no caller, no test and no spec text. It returns an empty dict in each run of
  this version, because no `associate` node exists
  ([ADR-TH8E](TH8E-one-person-in-v2.md)).
- No text decided the order of `image_size`. The branch `sfn26` had `(height, width)`. The sidecar
  `target_size` is `[height, width]`. ROIs and boxes are width first. A caller cannot exchange two
  named fields by mistake.
- Version 2.0.0 is not released, and the project has no backward-compatibility layer
  ([ADR-0QKK](0QKK-no-legacy-layer.md)).

## Consequences

- A consumer of the pipeline API, for example freemocap, must read `xy`, `z`, `image_width` and
  `image_height`.
- The tap files do not change. A `keypoints.jsonl` line holds x, y and the score of each point, and
  a tap still refuses a `3d` keypoints port.
- The frozen script `decisions/scripts/report_box_parity_end_to_end.py` keeps the old name `xyz`.
  It does not run on the new API without a change.

## Alternatives rejected

- Keep `xyz` with the rule "a point is missing when x or y is NaN". The trap stays for each consumer
  that tests three coordinates.
- One array with the shape `(I, P, D)`. Each consumer must then branch on the shape.
- Keep the tuple `image_size` with a documented order. A caller can still read it in the wrong
  order.
- A tuple `(height, width)`. It has the same defect, and it does not agree with the ROIs and the
  boxes.
