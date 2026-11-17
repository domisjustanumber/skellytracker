# 8TQT — Stages 6 and 7 of the pipeline redesign come before the 2.0.0 pre-release

**Status:** done, 2026-11-17 (user; PR: pending).

## Decision

1. On 2026-11-17 the user said: "redesign stages 6 to 8 can come now".
2. Stages 6 and 7 of the build order of
   [`node-and-port-redesign.md`](../../specs/pipeline/proposals/node-and-port-redesign.md#10-build-order)
   were built before the 2.0.0 pre-release: the new `merge`, `assign_keypoints`, the end of
   `concat`, `flag_when` and the tap form `flag.jsonl`.
3. Item 20 of [ADR-9HTX](9HTX-pipeline-node-and-port-redesign.md), and its Consequences sentence
   about a pre-release file with `concat` or the old `merge`, state the earlier schedule. That
   schedule no longer holds. No rule of ADR-9HTX changes.
4. Stage 8, the pipeline editor, is freemocap work.

## Reason

The entry records a change of schedule. It is a one-off action with no rule that stays, so its
status is `done`.
