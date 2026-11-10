# 4KW6 — onnxruntime 1.31 or later for the CPU environment

**Status:** absorbed into [`model-addition-workflow/batch-conversion-check.md#run-the-tool`](../../specs/model-sidecar/model-addition-workflow/batch-conversion-check.md#run-the-tool), 2026-11-10 (user; PR: pending).

## Decision

- The extra `onnx-cpu` requires `onnxruntime>=1.31`. `uv.lock` holds onnxruntime 1.31.1, the latest
  release on 2026-11-09.
- The `onnxruntime-gpu<1.27` cap of the extras `onnx-cuda` and `onnx-trt` does not change. It is
  about the CUDA 12 wheels. onnxruntime-directml stays at 1.24.4, its latest release.
- onnx stays at 1.22.0. The user asked only for the onnxruntime change.

## Reason

The batch-conversion check runs `tools/intake_bundle.py batch` in the CPU environment of this
checkout. onnxruntime 1.27.0 CPU gives different fp16 outputs in different fresh sessions for the
same file and input. Thus V5 can fail at random and give a false `does not convert`. This is the
open question of [ADR-50BW](../../specs/model-sidecar/decisions/entries/50BW-verification-batches.md).
A newer onnxruntime removes the noise.

## Evidence

- OpenMMLab-Exporter note of 2026-11-06 to the user (local file, not in git; secondary): 100 fresh
  CPU sessions of the `yolox-person` l fp16 converted and native b4 on input B differ in 3 of 100
  runs on 1.27.0 (maximum 0.5) and in 0 of 100 runs on 1.31.0 and 1.31.1. The V5 failure of the
  control tuple is in OpenMMLab-Exporter ADR-TB5R.
- The session `batch` run of `model-yolox-person@openmmlab-exporter` v2 (48 files) gives
  `converts` on 1.31.1, as on 1.27.0.

## Open work

See [open-work.md](../open-work.md).
