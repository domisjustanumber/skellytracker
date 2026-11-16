# TH8E — v2.0.0 tracks one person: a temporal node and an `@prev` input need `I` = 1

**Status:** absorbed into [`graph.md#behaviour`](../../specs/pipeline/graph.md#behaviour), [`graph.md#validation-rules`](../../specs/pipeline/graph.md#validation-rules), 2026-11-16 (user, 2026-11-16; PR: pending).

## Decision

1. **One person.** v2.0.0 tracks one person. Each `track_ids` value stays -1. This version has no
   `associate` node type.
2. **Load rule.** Each input of `smooth_roi`, `smooth_keypoints` and `redetect_trigger`, and each
   `@prev` input, must have `I` = 1 (`V-pipeline.graph-11`). `I` is the `max_instances` of the
   instance source, so the host checks the rule at load. A `merge` output has the `I` of its
   `target`, so a hand detector with `max_instances: 2` can feed a smoothed body through `merge`.
3. **Not covered.** `mediapipe_tasks` in the landmarker mode `VIDEO` is a temporal node, but the rule
   does not apply to it. MediaPipe tracks its own rows.
4. **Later.** A later `associate` node type gives the rows an identity and removes the limit.

This changes the text "`I` can be more than 1" of
[ADR-ZYS9](ZYS9-pipeline-outputs-running-sharing-inside-one-run.md) item 1 for the inputs of item 2
only. Each other node can still have `I` > 1.

## Reason

- The user decided that v2.0.0 is single-person only, and approved the load rule (2026-11-16).
- Without an identity, a temporal node filters row `i`, and row `i` can be another person on the
  next frame. A One Euro filter or a Kalman filter downstream then mixes two persons with no error.
  The load rule makes that pipeline fail at load, not in the output.
- The examples in `specs/pipeline/examples/` meet the rule: each temporal node and each `@prev`
  input there has the body as its instance source.

## Consequences

- With `I` = 1, row 0 can still change from one person to the other between frames when the
  instance source sees two persons. The rule does not stop that.

## Alternatives rejected

- **A statement in the spec only, with no load rule.** A temporal node on rows with `I` > 1 then
  mixes persons silently.

## Open work

See [open-work.md](../../specs/pipeline/decisions/open-work.md), "Multi-person identity".
