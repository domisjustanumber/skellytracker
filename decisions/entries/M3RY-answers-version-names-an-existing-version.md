# M3RY — `answers_version` names an existing version

**Status:** absorbed into [`model-addition-workflow/hand-over.md#responses`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses), 2026-11-09 (user; PR: pending).

## Decision

- The `answers_version` of a response is the number of the bundle version that the response
  answers. It is not the next version.
- `verify` gives a finding when the `answers_version` of the latest response is lower than 1 or
  higher than the current version of the bundle.
- After the session writes a response, it runs `verify` on the bundle again (step 6 of
  [Session steps](../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps)).
- [Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses) states these
  rules.

## Reason

`list` marks a bundle `(new version)` when its current version is not the `answers_version` of its
latest response. The responses of 2026-11-06 gave `answers_version: 2` when they answered v1. Some
bundles had no v2 then. When the contributor packed v2, `list` showed no mark, and a session could
miss the new version. The contributor reported this. `verify` checked only that the value is an
integer. The key block of Responses showed `answers_version: 2` with no meaning.

## Consequences

- The check reads only the latest response. Older responses of finished bundles keep their wrong
  numbers, and `verify` does not report them.
- The check finds a wrong number only before the contributor packs the next version. Thus the
  session runs `verify` right after it writes a response.

## Open work

See [open-work.md](../open-work.md).
