# 7E4Z — Box parity of `yolox-rtmw-wholebody` with the tracker of `sfn26`: the recording, test A and report B

**Status:** evidence, 2026-11-16 (measurement of stage 1.10 of the implementation plan; PR: pending).

## Decision

1. **The recording.** The script
   [`record_sfn26_box_parity.py`](../scripts/record_sfn26_box_parity.py) made the fixture
   `skellytracker/tests/pipelines/data/sfn26_box_parity.npz`. It makes a clone of this repository
   outside the checkout at the commit 2d356a6c (branch `sfn26`). It applies
   [`sfn26_early_redetect.patch`](../scripts/sfn26_early_redetect.patch), the early redetect of the
   commit 03b9c1dc, ported by hand. It runs `human_tracker_config(preset="rtmpose", video_fps=30.0)`
   on 200 frames of one camera of the test recording. Its docstring gives each array of the fixture
   ([ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md)).
2. **What the fixture holds.** The script makes the frames 160 to 169 black, because each frame of
   the recording holds a person. The detector ran on the frames 0, 150 and 161 to 170. It found a
   person on the frames 0, 150 and 170. The frames 161 to 169 have no box. Thus the fixture holds
   the first frame, one periodic redetect, a lost person, the early redetect and the carried box
   after it. A size floor changed the carried box on 185 of the 187 carried frames.
3. **Timestamps.** The old tracker refuses a `timestamp_ms` that is not an integer. The fixture
   thus has `timestamp_ms = int(frame_index / 30 × 1000)`, the formula of the old video runner, and
   not `frame_index × 1000 / 30`. Test A reads the timestamps from the fixture.
4. **Test A, the box logic.** `skellytracker/tests/pipelines/test_box_parity.py` runs the graph of
   the built-in through `start_pipeline`, with the model call of the two `onnx_model` nodes replaced
   by the recorded YOLOX boxes and keypoints. On each of the 200 frames, `node_ran` of `person` is
   equal to `detector_ran`, `person_roi` agrees with the smoothed box before the clip within
   1e-6 px, and the clip to whole pixels gives the integers of `bounding_boxes[0]`. The largest
   difference of `person_roi` is about 2e-13 px.
5. **Report B, end to end.** The script
   [`report_box_parity_end_to_end.py`](../scripts/report_box_parity_end_to_end.py) ran the built-in
   with the real models, in fp32, on the same frames and timestamps:

   | Value | CPU EP | `cuda` |
   |---|---|---|
   | Frames where `node_ran` of `person` is not `detector_ran` | 0 | 0 |
   | Frames where only one side has a box | 0 | 0 |
   | IoU of `person_roi` and the smoothed box, 191 frames: minimum, median, mean | 0.8522, 0.9823, 0.9721 | 0.8530, 0.9823, 0.9714 |
   | Points with a score of 0.4 or more on both sides | 25018 | 25046 |
   | Distance of these points: median, 95th percentile, maximum | 2.354 px, 11.192 px, 243.660 px | 2.380 px, 11.211 px, 240.855 px |

   Report B has no pass limit ([ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md), Consequences).

## Reason

The working branch has neither the One Euro box filter nor the early redetect of the old tracker.
Only a run of the old code gives the values that the new graph must give
([ADR-RA0E](RA0E-built-in-box-behaviour-of-sfn26.md)).

## Evidence

- Host: Windows 11, an RTX 3070. The recording: Python 3.12.13, NumPy 2.4.6, onnxruntime 1.30.0,
  OpenCV 5.0.0, the CPU provider. A second run of the recording gave the same bytes.
- Test A and report B: Python 3.13, NumPy 2.4.6, onnxruntime 1.31.1, the EP packs `cuda` and
  `trt-rtx` of the EP store.
- The clip rule of the old code: clamp x to `[0, width]` and y to `[0, height]`, then `int()`.

## Not repeated

- The old tracker keeps a point with a score of 0.4 or more. `roi_from_points` keeps a point with a
  score greater than `score_threshold`. The fixture has no point with a score equal to 0.4, so test
  A does not show this difference.
- No smoothed box of the fixture leaves the image. The fixture has no second periodic redetect
  after the lost person, no time step of more than 500 ms and no point set on one line.
- The largest point distance of report B, about 240 px, was not examined.
