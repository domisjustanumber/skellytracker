# Decision log of the pipeline spec: historical entries

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX`, `evidence; replaced by XXXX` or `done`. They are not in the read path. Read an entry here only to find
the reason for a decision. The [index](README.md) has the Active and Proposed entries. The
[Rules](../../../decisions/README.md#rules) are in the root log.

### Historical

| # | Decision | Status |
|---|----------|--------|
| [6DKT](entries/6DKT-instance-rows-carry-class-and-score.md) | Instance rows carry `class_index` and `instance_score`; tap lines carry `row` and the class name; `concat` fills an empty input | absorbed into [`graph.md#behaviour`](../graph.md#behaviour), [`outputs.md#fields`](../outputs.md#fields), [`outputs.md#behaviour`](../outputs.md#behaviour), [`taps.md#fields`](../taps.md#fields), [`taps.md#behaviour`](../taps.md#behaviour), [`taps.md#validation-rules`](../taps.md#validation-rules), [`detector.md#behaviour`](../nodes/onnx_model.md#behaviour), [`assign_keypoints.md#behaviour`](../nodes/assign_keypoints.md#behaviour), [`mediapipe_tasks.md#behaviour`](../nodes/mediapipe_tasks.md#behaviour), [`merge.md#behaviour`](../nodes/merge.md#behaviour) |
| [P245](entries/P245-jpeg-frame-input.md) | A run takes a JPEG buffer or a decoded array for each frame, and decodes a JPEG to `frame.image` before the first node; spans `frame.decode` and `frame.upload` | absorbed into [`running.md#fields`](../running.md#fields), [`running.md#behaviour`](../running.md#behaviour), [`running.md#validation-rules`](../running.md#validation-rules), [`running.md#implementer-guidance`](../running.md#implementer-guidance), [`running.md#authoring-guidance`](../running.md#authoring-guidance), [`timing.md#fields`](../timing.md#fields), [`timing.md#validation-rules`](../timing.md#validation-rules), [`graph.md#fields`](../graph.md#fields) |
| [S1TG](entries/S1TG-cpu-jpeg-decode-threads.md) | The run decodes 2 or more JPEG buffers of a call on the CPU in a thread pool with at most `cpu_threads` threads; a refused call names the first bad camera | absorbed into [`running.md#fields`](../running.md#fields), [`running.md#behaviour`](../running.md#behaviour), [`running.md#implementer-guidance`](../running.md#implementer-guidance), [`timing.md#implementer-guidance`](../timing.md#implementer-guidance) |
| [Y7C3](entries/Y7C3-mediapipe-score-without-visibility-and-holistic-present-row.md) | A `mediapipe_tasks` point with no visibility has the score 1.0; a `holistic` row is present when MediaPipe finds one or more parts | absorbed into [`mediapipe_tasks.md#behaviour`](../nodes/mediapipe_tasks.md#behaviour) |
| [M31J](entries/M31J-jpeg-decode-place-in-the-timing-header.md) | The timing header gives the place of the JPEG decode at the start of the run: `jpeg_decode` is `gpu`, `cpu` or `mixed` | absorbed into [`timing.md#fields`](../timing.md#fields) |
| [5NZ4](entries/5NZ4-auto-uses-the-graph-only-for-frames-of-the-gpu-decoder.md) | With `auto`, the GPU preprocess runs only in a call with a frame of the GPU JPEG decoder; a frame in CPU memory takes the CPU preprocess | absorbed into [`running.md#behaviour`](../running.md#behaviour), [`timing.md#fields`](../timing.md#fields) |
