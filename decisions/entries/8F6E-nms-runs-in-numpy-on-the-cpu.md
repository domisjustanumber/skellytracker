# 8F6E — NMS runs in NumPy on the CPU; a detector node has no NMS session

**Status:** absorbed into [`onnx_model`: Implementer guidance](../../specs/pipeline/nodes/onnx_model.md#implementer-guidance), 2026-11-23 (user; PR: pending). It was `accepted` on 2026-11-23.

## Decision

1. The NMS of a detector node runs in NumPy on the CPU, in
   `core/detectors/processing/post/object_selection_nms.py`. The node builds no ONNX
   `NonMaxSuppression` session. The raw outputs of the model go to host memory first.
2. This replaces the ONNX `NonMaxSuppression` graph of
   [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 9,
   [ADR-9NW0](9NW0-ep-keys-options-and-failures.md) item 7 and
   [ADR-D8DH](D8DH-sessions-errors-and-the-ready-rule.md) item 4. The other rules of
   [ADR-7NY2](7NY2-pipeline-form-graph-and-nodes.md) item 9 stay: NMS is in the postprocess of the
   node, `post_nms_top_k` applies to the final rows, and the gate is the vector file of
   `post.object.selection.nms`.

## Reason

- The user, on 2026-11-23: "keep the nms as standard cpu-bound python for now". The package must
  support 1 person today and at most about 5 people later.
- The package code has done NMS in NumPy from stage 1.5 of the implementation plan. The texts that
  named an NMS session did not describe the code.

## Evidence

Measured on 2026-11-23 on one Windows system with an NVIDIA GPU, ONNX Runtime 1.30.0 and onnx
1.22.0. The system was not quiet, so each time is a guide only.

- **Raw output.** For a batch of 3: 212,940 bytes for size `n` (3549 rows) and 504,000 bytes for
  size `m` (8400 rows). The row count follows the input size of the model.
- **Copy to host memory.** 0.06 ms to 0.10 ms (median of 200) on `cuda` and on `trt-rtx`, for
  `n` and for `m`. A call with its outputs in host memory and a call with its outputs in GPU memory
  took the same time, within the noise.
- **The operator on a GPU.** On `cuda`, the `NonMaxSuppression` node runs on the EP. On `trt-rtx`
  (pack `trt-rtx-cu13` 0.5.0), no session builds: the EP has no implementation of the node. This
  was the result for opsets 11, 13 and 17, for a box limit of 100 and of `2**31-1`, and for fixed
  and dynamic row counts.
- **Real frames.** 108 images of COCO val2017 with 2 to 5 people, each with a licence that permits
  reuse: the NMS of `yolox-person` got a median of 26 to 91 candidates and at most 209. The NumPy
  NMS took a median of 0.5 ms to 1.6 ms and at most 3.8 ms. Its kept rows were equal to the rows of
  the ONNX operator on the CPU EP in each of the 216 calls.

## Alternatives rejected

- **The ONNX operator in a session on the CPU.** It keeps the same rows. It adds a second session
  to each detector node.
- **The threshold and the NMS on the GPU.** It can save only the copy, about 0.1 ms, and it does
  not build on `trt-rtx`.
- **One loop pass for each kept box.** Not built. Do it when a measurement shows that the NMS time
  is a problem.
