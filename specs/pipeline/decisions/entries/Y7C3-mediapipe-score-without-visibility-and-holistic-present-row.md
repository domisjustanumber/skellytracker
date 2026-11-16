# Y7C3 — A MediaPipe point with no visibility has the score 1.0; a Holistic row is present when one part is found

**Status:** absorbed into [`mediapipe_tasks.md#behaviour`](../../nodes/mediapipe_tasks.md#behaviour), 2026-11-16 (user, question S1; PR: pending).

## Decision

1. **Score.** The score of a point of a `mediapipe_tasks` node is the landmark visibility of
   MediaPipe. A found point with no visibility value has the score 1.0.
2. **Present row.** For the variant `holistic`, the row is present when MediaPipe finds one or more
   of its parts: the body, the right hand, the left hand or the face.

## Reason

- MediaPipe 1.2.2 `HolisticLandmarker` gives `visibility=None` and `presence=None` for each hand
  point and each face point. The pose points have a visibility. A probe of stage 1.8 on the
  skellysamples test image showed this.
- A score of 0 is the score of a missing point
  ([Outputs](../../outputs.md#fields)). With 0, a found hand or face point looks missing.
- The node already gives 1.0 as the `instance_score` of a present row, because the Tasks results
  have no instance score ([MediaPipe Tasks](../../nodes/mediapipe_tasks.md#behaviour)).
- The old package face detector also uses 1.0 when MediaPipe gives no value
  (`MediapipeFaceKeypointDetector`, `lm.presence if lm.presence is not None else 1.0`).
- The spec did not say when the Holistic row is present. A row with a face and no body still holds
  found points, and no row and no point is dropped ([Graph](../../graph.md#behaviour) item 8).

## Alternatives rejected

- Score 0 for a point with no visibility: a found point then looks like a missing point.
- Score NaN: a score is a number from 0 up, and a threshold on NaN is always false.
- A present row only when the body is found: it drops the found hands and face of a frame with no
  body.
