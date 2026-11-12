# 6JWJ — A MediaPipe VIDEO-mode landmarker finds a person again after a gap; `mediapipe_tasks` has no reset

**Status:** evidence, 2026-11-11 (measured in the spec-build session).

## Decision

1. The node `mediapipe_tasks` has no reset and no back-off. It does not close and build a
   landmarker again after frames with no person.
2. Run the scripts again when the package moves to MediaPipe 1.2.2
   ([ADR-MSH0](../../../../decisions/entries/MSH0-supported-platforms-v2.md)). If a landmarker then
   stays empty while a person is visible, write a new entry with the evidence.

## Reason

- Today's package resets a detector after a number of frames with no keypoints
  (`KeypointResetPolicyConfig` in `skellytracker/core/temporal_processing/temporal_processing_config.py`).
  Its docstring says that a VIDEO-mode landmarker "can get stuck silently returning empty results
  even when the subject is clearly visible". No test or issue supports this.
- From outside, a stuck tracker and an empty room give the same empty result. So the policy also
  closes and builds the landmarker again when nobody is in the frame. The build runs in the frame
  call and stops the frame loop. The back-off only spaces out these builds.
- The reset never helped the failure of Python 3.11 and 3.12 on Windows. That failure is an
  exception (`ValueError: Input timestamp must be monotonically increasing`) before the reset code
  runs. The pipeline spec removes its cause: the caller gives a `timestamp_ms` that increases.

## Evidence

- Tool: `mediapipe` 0.10.33 (the version that `pyproject.toml` pins), Windows, CPU. Models: the
  pose landmarker `heavy` (the package default) and the hand landmarker, with the package options
  (detection and presence 0.5; `min_tracking_confidence` 0.5 and 0.9). Timestamps `i * 33`, which
  increase. Media: the skellysamples test recording (camera 1, frames 0 to 89) and one test image.
- Scripts: [`stuck_test.py`](../scripts/stuck_test.py) (the recording) and
  [`static_test.py`](../scripts/static_test.py) (the image). Each sequence has 30 frames with the
  person, a gap, then the person again. The gaps are 30 black frames, 30 background frames and 30
  blurred frames. A jump shifts the image by 40 % or scales it by 0.5. Each sequence is compared
  with a new landmarker and with IMAGE mode.
- Result: after each gap and each jump, the reused landmarker found the person on the same frame as
  the new landmarker, or one frame later. The pose was found on 60 of 60 frames after each gap.
  No run stopped or raised an error.
- One related fault reproduced: after a blur gap, the pose landmarker gave a wrong pose that was not
  empty, outside the image, for about 22 frames, and then recovered by itself. A reset that counts
  empty results cannot see this fault.
- Not tested: the `lite` and `full` pose models, `num_poses` above 1, gaps longer than 30 frames,
  real frame timing, and MediaPipe 1.2.2.

## Not repeated

- The scripts read the models from `~/.freemocap/skellytracker-models` and the media from the cache
  that `skellytracker/tests/conftest.py` fills. A run writes `results_*.json` beside the script. Do
  not commit that file.
