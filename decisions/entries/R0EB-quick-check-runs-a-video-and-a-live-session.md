# R0EB — The quick check runs a `video` session and a `live` session, with one CPU reference for the run

**Status:** accepted, 2026-11-20 (user).

## Decision

This entry replaces the image run of item 1 of
[ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) and "the L3 probe and the image run" of its
item 2. Each other rule of that entry stays.

1. **The two sessions.** For each EP on each GPU, `certify()` runs the L3 probe, then the check
   `<label>:video`, then the check `<label>:live`. Each check runs the certification pipeline on one
   camera on 3 frames, in its own `spawn` child. The frames are the test image, repeated.
   `<label>:video` uses the running mode `video`, which a post-hoc session uses. `<label>:live` uses
   the running mode `live`, which a realtime session uses, with a `timestamp_ms` that increases.
   The check `<label>:image` goes.
2. **One CPU reference.** One child runs the two modes on the CPU EP, one time for the run. It gives
   the checks `cpu:video` and `cpu:live`, at the two levels. `cpu:video` passes when each frame has
   a person. `cpu:live` passes when its outputs are finite. The rows are there only when one EP of
   the selection can run.
3. **The comparison.** `<label>:video` compares each frame of the EP with the frame of the CPU
   reference with the same index, with the thresholds of the EP catalog. The first frame that fails
   gives the reason. Its `numbers` hold the worst value over the frames. With no CPU reference, the
   check is `not-run` with `cpu-reference-missing`.
4. **The smoke run.** `<label>:live` compares nothing. It fails on an error, on an output that is
   not finite (`not-finite`) and on a frame with no person (`no-person`). It is `not-run` with
   `video-not-passed` when `<label>:video` did not pass.
5. **The EP check.** `<label>` passes when `<label>:probe` and `<label>:video` pass. `<label>:live`
   never changes it, as the JPEG checks do not. The stored quick result and the check rule do not
   change.
6. **The gate reason.** `video-not-passed` replaces `image-not-passed`.

## Reason

- The format of `skellycertify` says that the level `quick` must show that a realtime session and
  a post-hoc session start and run (section 2.7, skellycertify ADR-M8J1). The running mode `image`
  is neither. It also does not use the state that the built-in pipeline keeps between frames.
- The user said that the level `quick` shows whether things work at all, and that the level `full`
  gets the performance data.
- The run of today ran the CPU EP again for each EP on each GPU. One reference is enough.

## Consequences

- A quick report now has a `summary` item of the CPU EP.
- `eps.certify()` keeps its image run. `certify()` does not use it.
- The frames of `<label>:live` are decoded frames, so this check does not use the GPU JPEG decode.
  The JPEG checks cover that path.

## Open work

- One run on one Windows host (2026-11-20, `directml` on an RTX 3070 and on a UHD 770): 17.5 s for
  the whole run; 4.2 s for the CPU reference, 1.1 to 1.4 s for a probe and about 3 s for each
  session check, with the start of the child. The estimates are not calibrated to these times.
- In that run, `directml` on the RTX 3070 failed `<label>:video` with `keypoints-differ` on frame 1:
  0.0155 of the box against the limit 0.01. Frame 0 gave 0.0071 and frame 2 gave 0.0063. Frame 0 is
  equal to the result of the old image run. Frame 1 is the first frame that the pipeline crops from
  the keypoints of the frame before. The UHD 770 gave 0.0074 on frame 1. The rule for the frames
  after frame 0 is not decided.
- Not decided: a time limit for the whole run, the pairs with a reviewed row, the source of the test
  image, and if a failed `<label>:live` must fail the EP check.
- The format of `skellycertify` names `<label>:image` in its example of section 3.6.
