# GPW6 — Model gate of `yolox-person` and `rtmw-wholebody133` at the detector level; batch conversion and start times

**Status:** evidence, 2026-11-16 (measurement of stage 1.9 of the implementation plan; PR: pending).

## Decision

1. **What ran.** The model gate of the
   [acceptance gate](../../.claude/skills/implement-sidecar-section/proposal-gate.md) (step 5) ran
   on the Windows test host for the two package sidecars of `core/model_zoo/`. The script
   [`gpw6_first_models_gate.py`](../scripts/gpw6_first_models_gate.py) ran the generic detectors on
   the 22 published b3 ONNX files and compared them with the upstream reference output of the
   parity workers of OpenMMLab-Exporter. Its docstring gives each gate. The gates were set before
   the first run.
2. **Load.** The spec loader loads each sidecar with no `V-` rule failure. Each of the 22 files has
   the `sha256` of its sidecar.
3. **`yolox-person`, the package code alone.** For each of the 6 sizes, on 18 images: the tensor of
   `preprocess_image` equals the upstream canvas (difference 0, gate Y1). `decode_nms` on the
   upstream anchor rows gives the upstream person detections: the same anchors, scores that are
   equal bit for bit, and boxes within 1.1e-4 px (gate Y4). The row totals equal the totals of the exporter.
4. **`yolox-person`, the detector.** `detect()` equals the decode of the session rows bit for bit
   (gate Y5a), and that decode agrees with the upstream person detections within the export error
   of the same session (gate Y5c), for each size: fp32 and fp16 on the CPU EP, and fp16 on `cuda`
   and `trt-rtx`. 66 of 66 gates pass on the CPU EP, and 66 of 66 on the GPU EPs. With the sidecar
   `min_score`, the largest box difference is 0.14 px (fp32, CPU), 0.59 px (fp16, CPU) and 0.96 px
   (fp16, GPU). Each anchor that only one side keeps has a cause in the export error.
5. **`rtmw-wholebody133`, the package code alone.** For each of the 5 sizes, on 49 persons of 10
   images: the matrix `M` equals the upstream `M` bit for bit (gate R1). `normalize` on the
   upstream crop equals the upstream tensor (difference 0, gate R1b). `decode_simcc` on the
   upstream raw rows equals the mmpose decode: each score bit for bit, each coordinate within
   1 float32 spacing (gate R4). `resize_inverse` agrees with the upstream final keypoints within 0.08
   of the bound `B` (gate R4b).
6. **`rtmw-wholebody133`, the detector.** The upstream tensors through the session, the decode and
   the unprojection agree with the upstream final output within the export error (gate R5).
   `detect()` on the decoded images and the upstream boxes passes the measured gate of the exporter
   (gate R7, median outlier fraction at most 0.15): 0.015 to 0.038 on the CPU EP, 0.030 to 0.045 on
   `cuda` and 0.045 to 0.083 on `trt-rtx`. 40 of 40 gates pass on the CPU EP (fp32 and fp16), and
   40 of 40 on the GPU EPs (fp16).
7. **fp16 placement.** Each of the 11 fp16 files has 0 nodes on the CPU EP on `cuda` and on
   `trt-rtx`, at the published batch 3
   ([ADR-EY4F](EY4F-acceptance-gate-checks-fp16-gpu-placement.md)).
8. **Export error on `trt-rtx`.** The largest difference of a raw SimCC value from the upstream
   output is larger on `trt-rtx` than on `cuda`, for each size (fp16): 0.039 against 0.011 for `m`,
   0.32 against 0.061 for `l-384`, and 1.47 against 0.45 for `x-384`. On the CPU EP it is 0.0032 to
   0.37 (fp32).
9. **Batch conversion time.** `model_batch_convert` from batch 3 to batch 1 takes 0.01 s to 1.02 s
   (median of 3 runs for each of the 22 files). The time follows the file size: about 0.25 s for
   each 100 MB.
10. **Start time.** `create_detector` with the batch of the sidecar takes 0.27 s to 1.74 s on the
    CPU EP, 0.33 s to 0.87 s on `cuda` and 0.96 s to 2.63 s on `trt-rtx` (median of 3 runs, with
    the hash check cache and the runtime cache of `trt-rtx` filled). With batch 1, it takes 0.27 s
    to 2.06 s, 0.33 s to 1.68 s and 1.01 s to 4.75 s. The first `trt-rtx` session of a file in the
    gate run took 4.3 s to 8.7 s.

## Reason

- Stage 1.9 of the implementation plan runs steps 5 to 7 of the acceptance gate for the two first
  models, at the detector level
  ([ADR-NHM3](NHM3-phases-to-the-exporter-checkpoint.md) item 3;
  [ADR-6J8E](6J8E-exporters-run-released-skellytracker.md) item 6).
- Items 3 and 5 are the two golden tests that stage 1.5 gave to this stage: the host tensor of
  `yolox-person`, and the mmpose scores of RTMW crops.
- Stage 1.7 needs item 9 for the decision on a cache of generated artifacts.

## Evidence

- Host: NVIDIA RTX 3070 (8 GB), Windows 11, CPython 3.13.18, `onnxruntime` 1.31.1, `onnx` 1.22.0,
  NumPy 2.4.6, `opencv-contrib-python` 5.0.0.93, the EP packs `cuda-cu13` 0.3.0 and `trt-rtx-cu13`
  0.5.0.
- Script: [`gpw6_first_models_gate.py`](../scripts/gpw6_first_models_gate.py), with the commands
  `yolox`, `rtmw` (each one time with `--eps cpu` and one time with
  `--eps cuda trt-rtx --precisions fp16`) and `timing --eps cpu cuda trt-rtx --runs 3`.
- Models: the 22 b3 files of `exports/` of a local checkout of OpenMMLab-Exporter, copied to
  `core/model_zoo/`. The sidecars give their SHA-256. Git tracks no ONNX file.
- Reference output: the worker files `decoded.npz` and `upstream_<size>.npz` of the parity runs of
  OpenMMLab-Exporter (mmdet 3.3.0 for `yolox-person`, mmpose 1.3.2 for `rtmw-wholebody133`, flip
  test off). The exporter does not track them. The intake of each `model` bundle (version 4)
  records their SHA-256, and the script checks each hash before it reads a file. The script reads
  the files as data. It runs no exporter code
  ([ADR-AD33](AD33-bundles-are-untrusted-input.md)).
- The reference output is not in the bundles: no bundle has a `parity/` folder. The acceptance gate
  names the `parity/` output of the bundle.
- Gate R7 is a measured gate of the exporter. Its three negative controls did not run again here.
- Not measured: Linux, macOS, the CoreML EP, a first session start with an empty operating-system
  file cache, and a conversion to a batch other than 1.
