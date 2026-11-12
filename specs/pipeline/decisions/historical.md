# Decision log of the pipeline spec: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries. The
[Rules](../../../decisions/README.md#rules) are in the root log.

### Historical

| # | Decision | Status |
|---|----------|--------|
| [6DKT](entries/6DKT-instance-rows-carry-class-and-score.md) | Instance rows carry `class_index` and `instance_score`; tap lines carry `row` and the class name; `concat` fills an empty input | absorbed into [`graph.md#behaviour`](../graph.md#behaviour), [`outputs.md#fields`](../outputs.md#fields), [`outputs.md#behaviour`](../outputs.md#behaviour), [`taps.md#fields`](../taps.md#fields), [`taps.md#behaviour`](../taps.md#behaviour), [`taps.md#validation-rules`](../taps.md#validation-rules), [`detector.md#behaviour`](../nodes/detector.md#behaviour), [`merge.md#behaviour`](../nodes/merge.md#behaviour), [`mediapipe_tasks.md#behaviour`](../nodes/mediapipe_tasks.md#behaviour), [`concat.md#behaviour`](../nodes/concat.md#behaviour) |
