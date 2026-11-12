# Decision log of the pipeline spec

This log records the decisions that apply only to the pipeline spec (`specs/pipeline/`). It is the
log of the pipeline spec module
([ADR-3SF2](../../../decisions/entries/3SF2-pipeline-spec-and-node-workflow.md)). The
[Rules](../../../decisions/README.md#rules) of the root log apply to this log. To write an entry, use
the root [template.md](../../../decisions/template.md). Read this file and
[open-work.md](open-work.md) before you change the pipeline spec. Read an entry of
[historical.md](historical.md) only to find the reason for a decision.

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [6JWJ](entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) | A MediaPipe VIDEO-mode landmarker finds a person again after a gap; `mediapipe_tasks` has no reset; run again on MediaPipe 1.2.2 | evidence |

### Proposed

These entries are spec change proposals that wait for a decision of the user. Section is the spec
section of the change, or `none` when the change has no one section.

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work of the pipeline spec is in [open-work.md](open-work.md).
