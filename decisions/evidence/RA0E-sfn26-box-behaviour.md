# Evidence for RA0E: the box behaviour of `sfn26` and the early redetect of 03b9c1dc

This file is the evidence of
[ADR-RA0E](../entries/RA0E-built-in-box-behaviour-of-sfn26.md). It lists the code lines that the
design follows. The code is in the repository freemocap/skellytracker. Neither commit is on the
default branch of that repository, so this file gives the repository, the ref and the path, and no
permalink.

- `sfn26`: the branch `sfn26` at 2d356a6c41f831484251677050fafb2576193060.
- `03b9`: the branch `development-streaming` at 03b9c1dc10dfa14fd49ca15b35d17ac71c569345.

The two commits are not ancestors of each other. Each path below starts at `skellytracker/core/`.

## The policy values (`sfn26`)

| Fact | Line |
|---|---|
| A detection each 5 seconds | `tracker/tracker_presets.py:17` `_REDETECT_SECONDS = 5.0`; `:177` `redetect_interval = max(1, round(_REDETECT_SECONDS * video_fps))` |
| The default frame rate 30 and the expansion 0.05 | `tracker/tracker_presets.py:99` `video_fps: float = 30.0, keypoint_bbox_expansion: float = 0.05,` |
| No fitness check, two floors | `tracker/tracker_presets.py:207-209` `fitness_checks=[],` `min_shrink_ratio_per_frame=0.995,` `min_bbox_size_px=80.0,` |
| The third floor | `temporal_processing/temporal_processing_config.py:81` `min_detected_bbox_ratio: float \| None = 0.5` |
| The box filter with its defaults | `tracker/tracker_presets.py:211` `bbox_smoothing=BBoxSmoothingConfig(),`; `temporal_processing/temporal_processing_config.py:92-95` `min_cutoff` 3.0, `beta` 0.02, `d_cutoff` 1.0, `reset_after_seconds` 0.5 |
| YOLOX keeps one box with a score of 0.7 or more | `detectors/object_detectors/yolox/yolox_person_detector.py:79-81` `score_threshold: float = 0.7`, `max_detections: int \| None = 1` |
| RTMW sets a point below 0.4 to NaN | `detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:87` `confidence_threshold: float = 0.4`; `:133-134` `unavailable = scores < self.config.confidence_threshold`, `xyz[unavailable] = np.nan` |

## The trigger

| Fact | Line |
|---|---|
| The interval rule (`sfn26`) | `temporal_processing/bbox_policy.py:153-159` `should_redetect`: `last is None`, then `(frame_number - last) >= self.redetect_interval`, then the checks |
| The detector sets the frame of the last detection (`sfn26`) | `tracker/detection_stage.py:125-131` |
| All cameras redetect together (`sfn26`) | `tracker/detection_stage.py:448-449` `any_needs_redetect = onnx_object_detector is not None and any(` |
| The early redetect (`03b9`) | `temporal_processing/bbox_policy.py:153-174` `needs_recovery`: `:160` `if not bboxes:`, `:170` `if not mask.any():`, `:173` `return bool(np.any(np.ptp(points.xy[mask], axis=0) <= 0))` |
| The trigger reads it (`03b9`) | `temporal_processing/bbox_policy.py:178` `if last is None or stage_state.needs_redetection:`; `tracker/tracker_state.py:82`; `tracker/detection_stage.py:180`, `:385`, `:736` |

## The carried box and its floors (`sfn26`)

| Fact | Line |
|---|---|
| The box around the valid points, with the first expansion | `temporal_processing/bbox_policy.py:88-124` `predict_bbox_from_keypoints`; `:119` `x1=x1 - w * expansion_ratio,`; `:123` `confidence=1.0,` |
| The second expansion | `temporal_processing/bbox_policy.py:197` `candidate = tracked.scaled(1.0 + 2.0 * self.keypoint_bbox_expansion)` |
| The three floors, each around the centre | `temporal_processing/bbox_policy.py:200-211`, `:214-225` and `:227-235` |
| The box comes from the keypoints of each frame | `tracker/detection_stage.py:158-165` |

With the expansion 0.05, the two expansions give `1.1 × 1.1 = 1.21` times the box around the
points.

## The box filter (`sfn26`)

| Fact | Line |
|---|---|
| The filter on the two corners | `temporal_processing/bbox_smoothing.py:38-64` `apply_bbox_one_euro` |
| A missing box clears the state | `temporal_processing/bbox_smoothing.py:41-42` |
| The start from the raw box | `temporal_processing/bbox_smoothing.py:45` `reset = work is None or dt is None or dt > config.reset_after_seconds` |
| The sort of the corners | `temporal_processing/bbox_smoothing.py:60` `work.filtered_values.sort(axis=0)` |
| The filter step | `temporal_processing/one_euro_array.py:35-49` |
| The time step, and no time step for a timestamp that does not increase | `tracker/detection_stage.py:835-845` `_dt_from_context` |
| The filter runs on each frame | `tracker/detection_stage.py:143` |

## The crop and the drawn box (`sfn26`)

| Fact | Line |
|---|---|
| The crop box has whole-pixel edges, and no box gives an empty crop | `tracker/detection_stage.py:147-148` `crop_bbox = smoothed_bbox.clipped_pixels(h, w)`, `else image[:0, :0]`; `data_primitives/bounding_box.py:114-117` |
| The drawn box is the crop box | `tracker/detection_stage.py:173` `bounding_boxes=[crop_bbox] if crop_bbox is not None else [],` |
| RTMW gets only the cut crop | `detectors/keypoint_detectors/rtmw/wholebody/rtmw_wholebody_detector.py:107-113` |
| The 1.25 margin is around the cut crop | `detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml:13-18` `method: affine_person_crop`, `expand_ratio: 1.25`; `detectors/processing/image_preprocessing.py:261-273` |

## The One Euro comparison

The script [`ra0e_one_euro_compare.py`](../scripts/ra0e_one_euro_compare.py) ran the reference
`specs/pipeline/reference/node_smooth_roi.py` (filter `one_euro`) and `one_euro_step` of
`temporal_processing/one_euro_array.py` at `sfn26`, with a copy of the steps of
`apply_bbox_one_euro`. It used 3000 random `video` sequences with rotation 0, with gaps on both
sides of 500 ms, missing boxes, and random values of `min_cutoff`, `beta` and `d_cutoff`. The
corners agreed within 1e-9: the largest difference was 1.7e-12 px. Tools: Python 3.13.18 and
NumPy 2.4.6. Stage 1.10 of the implementation plan makes the recording script for the full
tracker.

## Not measured

No tool ran the `sfn26` tracker on a video for this entry. The facts above are from a reading of
the code. The point test of the new nodes is strict (`score > 0.4`), and `sfn26` keeps a score
equal to 0.4. The two tests give the same points for float32 scores. This assumption is not
measured.
