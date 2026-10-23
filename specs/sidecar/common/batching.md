---
id: common.batching
title: Batching
kind: common
since: v2024.09.1019
changed_in: []
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/model.py::BatchingSpec._check_batch_axis
  load: skellytracker/core/sidecar/model.py::OnnxSpec.supports_dynamic_batch
external_impl: []
tests: [skellytracker/tests/sidecar/test_model_validation.py]
vectors: null
status: {spec: stable, validate: implemented, load: implemented}
---

# Batching

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batch_axis` | int | no | The axis of the batch dimension. The default is `0`. Non-zero batch axes are out of scope. |
| `supports_dynamic_batch` | bool | derived | The value is `true` when `batch_artifacts` contains a `dynamic` key. The host derives it at load time. The author does not write it. |

> `batching.batch_conversion` is **not part of this spec**. It is reserved for a future change set.

`batch_artifacts`: [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

## Validation rules

- [ ] `V-common.batching-1` If `batching.batch_axis` is present, it must be `0`.

## Implementer guidance

- Every published artifact of the exporters that have code has a static batch. Thus `batch_artifacts` has quoted integer keys and never `dynamic`, and `batching` is `{batch_axis: 0}`.
  - OpenMMLab-Exporter `specialize_batch` pins dim 0 of every graph input and output. Its re-export uses batch 1, 2 and 3. (OpenMMLab-Exporter `onnx_convert/batch.py:28-50`, ed59f00; OpenMMLab-Exporter 0035 `notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:30-33`, c85abf7)
  - Roboflow-Exporter exports with `dynamic_batch=False` (opset 17) and requires that the leading dim of every input and output equals N. (Roboflow-Exporter `rf_detr/export.py:41-50` (16852ca), `onnx_runtime/contract.py:79-94` (16852ca) and `pipeline/artifacts.py:115, 146-154` (4ae67c0))
  - Ultralytics-Exporter never exports a dynamic batch. The ONNX metadata `args` has `dynamic: False`. (Ultralytics-Exporter `export_all.py:50-57, 138-158`, 69499e7; local file `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, not in git)
  - Qualcomm-Exporter traces a `torch.zeros((batch, 3, H, W))` dummy with no `dynamic_axes`. Only batch 1 artifacts exist on disk. (Qualcomm-Exporter `qai_export.py:22-60` (8d8e05a) and `export_all.py:92-98` (4ca4586))
- A static-batch artifact takes exactly N frames.
  - The Ultralytics-Exporter batch 2 files have the input `[2, 3, 640, 640]` and the output `[2, 300, 6]` (pose: `[2, 300, 57]`). (Ultralytics-Exporter local files `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx` and `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, not in git)
  - The batch is also in `int64` constants of the graph. The detector has `/model.23/Constant_output_0 = [2, 4, -1]`. The pose model has `/model.23/Constant_18_output_0 = [2, 17, 3, -1]`. (Ultralytics-Exporter `yolo_sidecar.py:114-124` (f52ef68) and the same local files)
  - The runners of the exporters do not pad. They drop the last incomplete batch (4,998 of 5,000 val2017 images at batch 3). They raise an error when fewer images than one batch exist. (OpenMMLab-Exporter `pipeline/coco_dataset.py:155-160`, ba0c087; Roboflow-Exporter `pipeline/accuracy.py:76-93` (4ae67c0) and `README.md:627-631` (b46b98f); Ultralytics-Exporter `yolo_validation.py:98-114, 258-299`, f52ef68)
- The native batch does not change the accuracy of fp32.
  - On CPU, the output at batch N is bit-identical to batch 1. On CUDA with TF32 on, batch 2 differs from batch 1 by up to 4.7e-3 in score and 1.6 px in box (score above 0.3). With TF32 off, the differences are 7.6e-6 and 0.0007 px. The AP does not change (0.4114 against 0.4113). The test used RTMDet-tiny and 40 COCO images. (OpenMMLab-Exporter 0012 `notes/decisions/0012-tf32-left-on.md:19-33`, c955162)
  - The Ultralytics-Exporter fp32 detector AP is 0.3971 (nano) and 0.5635 (xlarge) at batch 1, 2 and 3. The fp32 pose AP is 0.5598 (nano) and 0.6886 (large) at all three. The fp16 nano AP is 0.3969, 0.3969 and 0.3968. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b<N>_<precision>.report.json` and `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-<size>_b<N>_<precision>.report.json`, fields `performance.converted.metrics_detail`, not in git, HEAD 2e0280e)
- The int8 AP varies more across batches than the fp32 AP.
  - Each batch artifact is a separate export, so each has its own calibration run. (Ultralytics-Exporter `export_all.py:138-158, 191-220`, 69499e7)
  - Examples: nano detector 0.3344, 0.3329 and 0.3326; xlarge pose OKS AP 0.5002, 0.5006 and 0.5024. (Ultralytics-Exporter local reports, same files as above)

## Authoring guidance
