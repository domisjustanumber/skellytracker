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

> `batching.batch_conversion` **(vNEXT, draft)** names a profile that tells the host how to make a fixed-batch artifact for a batch that `batch_artifacts` does not list. See [Batch conversion](batch-conversion.md).

`batch_artifacts`: [Sizes and artifacts](sizes-and-artifacts.md#sizessizeonnxbatch_artifacts).

## Validation rules

- [ ] `V-common.batching-1` If `batching.batch_axis` is present, it must be `0`.

## Implementer guidance

- Every published artifact of the exporters that have code has a static batch. Thus `batch_artifacts` has quoted integer keys and never `dynamic`, and `batching` is `{batch_axis: 0}`.
  - OpenMMLab-Exporter `specialize_batch` pins dim 0 of every graph input and output. Its re-export uses batch 1, 2 and 3. (OpenMMLab-Exporter [`onnx_convert/batch.py:28-50`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ed59f0019d6a392b6de651c4e6f334f379b8ee64/onnx_convert/batch.py#L28-L50); OpenMMLab-Exporter 0035 [`notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md:30-33`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c85abf7da34d1e4da7c129f3382173f7153f60fa/notes/decisions/0035-published-artifact-reuse-and-p8-reexport.md#L30-L33))
  - Roboflow-Exporter exports with `dynamic_batch=False` (opset 17) and requires that the leading dim of every input and output equals N. (Roboflow-Exporter [`rf_detr/export.py:41-50`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/rf_detr/export.py#L41-L50), [`onnx_runtime/contract.py:79-94`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/16852ca3f7e63e61fda1086ecf07491dc788581a/onnx_runtime/contract.py#L79-L94) and [`pipeline/artifacts.py:115`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L115), [`pipeline/artifacts.py:146-154`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/artifacts.py#L146-L154))
  - Ultralytics-Exporter never exports a dynamic batch. The ONNX metadata `args` has `dynamic: False`. (Ultralytics-Exporter [`export_all.py:50-57`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L50-L57), [`export_all.py:138-158`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/69499e7d292e6f3583ab9429c45a334af3377097/export_all.py#L138-L158); local file `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx`, not in git)
  - Qualcomm-Exporter traces a `torch.zeros((batch, 3, H, W))` dummy with no `dynamic_axes`. Only batch 1 artifacts exist on disk. (Qualcomm-Exporter [`qai_export.py:22-60`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/8d8e05a1c210dda5c2a1c4110bd7e4db860844fd/qai_export.py#L22-L60) and [`export_all.py:92-98`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/4ca45868431b67350c3c7ed900d5b3ff9f409905/export_all.py#L92-L98))
- A static-batch artifact takes exactly N frames.
  - The Ultralytics-Exporter batch 2 files have the input `[2, 3, 640, 640]` and the output `[2, 300, 6]` (pose: `[2, 300, 57]`). (Ultralytics-Exporter local files `exports/detectors/object_detectors/yolo26/yolo26-nano_b2_fp32.onnx` and `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-nano_b2_fp32.onnx`, not in git)
  - The batch is also in `int64` constants of the graph. The detector has `/model.23/Constant_output_0 = [2, 4, -1]`. The pose model has `/model.23/Constant_18_output_0 = [2, 17, 3, -1]`. (Ultralytics-Exporter [`yolo_sidecar.py:114-124`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L114-L124) and the same local files)
  - The runners of the exporters do not pad. They drop the last incomplete batch (4,998 of 5,000 val2017 images at batch 3). They raise an error when fewer images than one batch exist. (OpenMMLab-Exporter [`pipeline/coco_dataset.py:155-160`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/ba0c0876b58650ed472559f1a77780e5da13d370/pipeline/coco_dataset.py#L155-L160); Roboflow-Exporter [`pipeline/accuracy.py:76-93`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/4ae67c0f99a45a81a0e788e6abbda82db7811e32/pipeline/accuracy.py#L76-L93) and [`README.md:627-631`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b46b98fa826ffdef46fdfba66c1f8b189a68f8c6/README.md#L627-L631); Ultralytics-Exporter [`yolo_validation.py:98-114`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_validation.py#L98-L114), [`yolo_validation.py:258-299`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_validation.py#L258-L299))
- The native batch does not change the accuracy of fp32.
  - On CPU, the output at batch N is bit-identical to batch 1. On CUDA with TF32 on, batch 2 differs from batch 1 by up to 4.7e-3 in score and 1.6 px in box (score above 0.3). With TF32 off, the differences are 7.6e-6 and 0.0007 px. The AP does not change (0.4114 against 0.4113). The test used RTMDet-tiny and 40 COCO images. (OpenMMLab-Exporter 0012 [`notes/decisions/0012-tf32-left-on.md:19-33`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/c955162d91998b94fc52d932ab6623a9f2a89a1f/notes/decisions/0012-tf32-left-on.md#L19-L33))
  - The Ultralytics-Exporter fp32 detector AP is 0.3971 (nano) and 0.5635 (xlarge) at batch 1, 2 and 3. The fp32 pose AP is 0.5598 (nano) and 0.6886 (large) at all three. The fp16 nano AP is 0.3969, 0.3969 and 0.3968. (Ultralytics-Exporter local reports `exports/detectors/object_detectors/yolo26/yolo26-<size>_b<N>_<precision>.report.json` and `exports/detectors/keypoint_detectors/yolo26/body/yolo26-body-<size>_b<N>_<precision>.report.json`, fields `performance.converted.metrics_detail`, not in git, HEAD 2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4)

## Authoring guidance

- Run the graph at more than one batch before you write a `dynamic` key. A graph can fix the batch in constants inside the graph and not only in the I/O dims. The Ultralytics-Exporter batch 2 graphs hold the batch in `int64` `Reshape` constants. (Ultralytics-Exporter [`yolo_sidecar.py:114-124`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L114-L124), [`yolo_sidecar.py:668-701`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L668-L701))
- Verify a `dynamic` export at the batches 1, 2 and 3 against the static exports when they exist, and always against its own batch 1 runs. Use the dynamic check of [Batch-conversion check](../model-addition-workflow/hand-over.md#batch-conversion-check). If it fails, do not publish the `dynamic` export ([Publishing](../model-addition-workflow/validation-and-publishing.md#publishing)).
