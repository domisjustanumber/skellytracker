# 5NZ4 — With `auto`, the GPU preprocess runs only for the frames of the GPU JPEG decoder

**Status:** absorbed into [`running.md#behaviour`](../../running.md#behaviour), [`timing.md#fields`](../../timing.md#fields), 2026-11-23 (absorb at landing; PR: pending).

## Decision

This entry writes items 2 and 3 of
[ADR-S4MT](../../../../decisions/entries/S4MT-two-preprocess-paths.md) into the pipeline spec, and
it decides the cases that those items leave open.

1. **The rule.** With the preprocess place `auto`, an `onnx_model` node on `cuda` or `trt-rtx` uses
   the GPU preprocess for the frames of a call only when the GPU decoder decoded at least one frame
   of that call on the device of the node.
2. **Decoded arrays.** In a call where each frame of the device is in CPU memory, the node uses the
   CPU preprocess. The run uploads no frame and gives no warning.
3. **A mixed call.** When the GPU decoder decoded some frames of the device and other frames are in
   CPU memory, the run uploads the other frames, and the node uses the GPU preprocess for each frame
   of the device. The graph has one fixed input for each camera of the device, so one call cannot
   use two paths.
4. **No GPU decoder.** When the GPU decoder of a device does not open, or a stored `fail` of the
   quick check `jpeg-decode` stops it, each JPEG buffer decodes on the CPU. The frames are then in
   CPU memory, so item 2 applies. Before, the run uploaded these frames and used the GPU preprocess.
   The warning `jpeg_decoded_on_cpu` does not change.
5. **`gpu` and `cpu`.** The preprocess place `gpu` still uploads each frame and uses the GPU
   preprocess on each EP with the wiring, also for decoded arrays. A certification run and a
   benchmark can thus measure the graph with arrays. `cpu` does not change.
6. **The header.** `stage_providers.preprocess` of the timing header still gives the provider of the
   graph when the node starts with a graph. With `auto`, this is the place for a JPEG buffer. The
   field does not tell which path a call used. A call on the graph path has the span `preprocess`
   on the GPU, and a call with an upload has the event `frame.upload`.

## Reason

- The user decided the rule on 2026-11-23 (ADR-S4MT, Reason).
- Items 3 and 4 follow from the measurement of
  [ADR-4JFP](../../../../decisions/entries/4JFP-preprocess-paths-timing.md): for decoded arrays, the
  upload with the graph was equal to the CPU preprocess with the reused batch within 1.3 ms for the
  two package models. Thus the simplest rule for a frame in CPU memory is the CPU preprocess.
- Item 3 keeps the graph for a camera whose buffer the GPU decoder refuses in each call, while the
  other cameras of the device decode on the GPU.

## Evidence

- `skellytracker/tests/pipelines/test_gpu_preprocess.py`: a run with `auto` and decoded arrays on an
  EP with the graph gives the results of the preprocess place `cpu`, with no upload, no bound graph
  run and no warning.
- `skellytracker/tests/pipelines/test_executor.py`: a call with two JPEG buffers and one decoded
  array uploads only the array. A stored `fail` of `jpeg-decode` gives no upload.

## Alternatives rejected

- **The CPU preprocess for the whole device in a mixed call.** A frame of the GPU decoder then
  copies to CPU memory in each call.
- **A new header field for the preprocess place of each call.** The run writes the header before the
  first call, and a call can have either form of frame.

## Open work

- No run measured JPEG buffers with the reused batch of the CPU preprocess against the GPU path.
