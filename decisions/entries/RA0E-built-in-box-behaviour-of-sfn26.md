# RA0E — The built-in `yolox-rtmw-wholebody` follows the box behaviour of `sfn26` with the early redetect

**Status:** absorbed into [`roi_from_points.md#fields`](../../specs/pipeline/nodes/roi_from_points.md#fields), [`roi_from_points.md#behaviour`](../../specs/pipeline/nodes/roi_from_points.md#behaviour), [`roi_from_points.md#validation-rules`](../../specs/pipeline/nodes/roi_from_points.md#validation-rules), [`redetect_trigger.md#behaviour`](../../specs/pipeline/nodes/redetect_trigger.md#behaviour), [`redetect_trigger.md#validation-rules`](../../specs/pipeline/nodes/redetect_trigger.md#validation-rules), [`redetect_trigger.md#implementer-guidance`](../../specs/pipeline/nodes/redetect_trigger.md#implementer-guidance), [`redetect_trigger.md#authoring-guidance`](../../specs/pipeline/nodes/redetect_trigger.md#authoring-guidance), [`smooth_roi.md#fields`](../../specs/pipeline/nodes/smooth_roi.md#fields), [`smooth_roi.md#behaviour`](../../specs/pipeline/nodes/smooth_roi.md#behaviour), [`smooth_roi.md#validation-rules`](../../specs/pipeline/nodes/smooth_roi.md#validation-rules), [`smooth_roi.md#authoring-guidance`](../../specs/pipeline/nodes/smooth_roi.md#authoring-guidance), [`onnx_model.md#authoring-guidance`](../../specs/pipeline/nodes/onnx_model.md#authoring-guidance), [`sidecar-implementation-plan.md#110-the-pipeline-api-was-p`](../../specs/sidecar-implementation-plan.md#110-the-pipeline-api-was-p), 2026-11-16 (user, questions H1 and G2; PR: pending).

## Decision

1. **The built-in.** `yolox-rtmw-wholebody` follows the box behaviour of the skellytracker branch
   `sfn26` (2d356a6c), with the early redetect of 03b9c1dc: a detection each 150 frames, a
   detection on the frame after a lost person, a box from the points of the previous frame on each
   other frame, three size floors and a One Euro filter on the box.
2. **Points.** `roi_from_points.points` can be empty. The node then uses each present point of the
   input, and no point is required.
3. **Floors.** `roi_from_points` has the optional inputs `previous_rois` and `reference_rois`, and
   the params `min_previous_ratio`, `min_reference_ratio` and `min_size_px`
   (`V-node.roi_from_points-6` and `-7`).
4. **Trigger.** `redetect_trigger` has the check `roi_missing` (`V-node.redetect_trigger-2`).
5. **Filter.** `smooth_roi` has the param `filter` (`ema` or `one_euro`) and the params
   `min_cutoff`, `beta`, `d_cutoff` and `reset_after_ms` (`V-node.smooth_roi-1`). The filter
   `one_euro` acts on the two corners, uses the formula of `smooth_keypoints`, clears its state on a
   row that is not present, and does not change the rotation.
6. **Drawn box.** The built-in gives the smoothed crop ROI as the output `person_roi`. The
   pipeline does not clip it. A caller clips it to whole pixels.
7. **Cameras.** The trigger stays separate for each camera. One camera does not make the other
   cameras redetect.
8. **Points and crop.** The pipeline does not set a low-score point to NaN. The crop takes its
   margin from the full frame.
9. **Older text.** This changes the text "`yolox-rtmw-wholebody` (YOLOX with `post_nms_top_k: 1`,
   then RTMW)" of [ADR-W5QD](W5QD-pipeline-entries-consolidation.md) item 3: the built-in is now a
   stateful pipeline.

Each new default keeps the old behaviour of a node. Each other example file stays unchanged.
Stage 1.10 of the implementation plan implements the params, and its gate proves the match.

## Reason

- The user chose the reference on 2026-11-16 (question H1): `sfn26`, with the early redetect of
  03b9c1dc. The user accepted this design, with the differences below (question G2).
- freemocap uses this box behaviour. The first built-in ran the detector on each frame.
- Params on three node types need less text than a new node type, and the reference code agrees
  with each of them.

## Consequences

The built-in differs from the reference in five points:

1. `sfn26` makes each camera redetect when one camera needs it. The built-in decides for each
   camera, so the timers of the cameras can differ after an early redetect.
2. The RTMW detector of `sfn26` sets each point with a score below 0.4 to NaN. The built-in gives
   each point with its score. A caller applies the threshold.
3. `sfn26` cuts the crop at whole pixels, and the 1.25 margin of the model input is border fill.
   The built-in crops the float ROI from the full frame. Thus the keypoints are not equal.
4. A carried box of `sfn26` has the confidence 1.0. A carried ROI of the built-in has the score of
   the last detection.
5. `sfn26` starts the box filter again for a timestamp that does not increase. The new run
   refuses that call.

Also: the built-in is stateful, so in `video` it runs at batch = camera count with the warning
`batch_limited_by_state`. In `video` with no timestamps, the run parameter `fps` sets the filter
time. The `pipeline_sha256` of each pipeline with a `roi_from_points` or a `smooth_roi` node
changes, because the hash holds the defaults.

## Evidence

[RA0E-sfn26-box-behaviour.md](../evidence/RA0E-sfn26-box-behaviour.md) gives the code lines of
both commits and the comparison of the One Euro reference with `one_euro_step` of `sfn26`
(script [`ra0e_one_euro_compare.py`](../scripts/ra0e_one_euro_compare.py)).

## Alternatives rejected

- **A trigger that joins the cameras.** The cameras stay separate in each output, and a `live`
  call can hold a subset of them.
- **A clip param.** The crop does not clip, so a clipped output is not the ROI of the model. No
  glue node gets the image size.
- **A full-image crop when the detector finds no box.** `sfn26` does not run the keypoint model
  there.
- **A keypoint threshold param.** It is model processing, so it is a sidecar proposal.
- **A separate floor node type.** It needs a section, a reference module and a vector file for
  three `max` steps.
- **One Euro on the centre and the size.** With `beta` above 0, each corner has its own cutoff, so
  the result differs from `sfn26`.
