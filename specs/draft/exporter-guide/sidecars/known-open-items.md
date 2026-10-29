# Known open items for the exporter overhaul

Each item names a reference implementation or a reference example that an exporter owes. The
overhaul plan of each exporter must handle them.

| Exporter | Item |
|---|---|
| OpenMMLab-Exporter | It implements these sections on its host side: the `letterbox` resize and the normalization (`onnx_runtime/preprocess.py`: `letterbox`, `make_normalizer`), `selection: nms` with the letterbox unprojection and the box clamp (`onnx_runtime/decode_nms.py`: `NmsDecoder`), and the `fit` resize (`notes/decisions/scripts/rtmo_sidecar_probe.py`: `fit_resize`, the parity probe of OpenMMLab-Exporter 0020). No reference implementation exists for these sections. The overhaul plan must include the [reference-implementation step](../../../model-sidecar/model-addition-workflow/reference-implementations.md#reference-implementations) for each. |
| Roboflow-Exporter | It implements `selection: top_k` on its host side (`onnx_runtime/convert_rf_detr_coco.py`: `_select_topk_multiclass`), and the `stretch` resize (`onnx_runtime/preprocess.py`: `preprocess_to_nchw`). No reference implementation exists for these sections. The overhaul plan must include the reference-implementation step for each. |
| Roboflow-Exporter | The spec has no RF-DETR example. The `stretch`, `top_k` and `class_logits` rules have no example. The overhauled Roboflow-Exporter provides that example through the procedure "How to provide or replace an example" in [Reference examples](../../../model-sidecar/model-addition-workflow/reference-examples.md#how-to-provide-or-replace-an-example). |
| Ultralytics-Exporter | It writes `schema_version` `v2024.09.1019` (`yolo_sidecar.py`: `SCHEMA_VERSION`). So the YOLO26 [reference examples](../../../model-sidecar/examples/README.md) are written from its code, not copied from its exports (`kind: forecast` in [`inventory.yaml`](../../../model-sidecar/inventory.yaml)). They are replaced when it writes `vNEXT` sidecars. |
