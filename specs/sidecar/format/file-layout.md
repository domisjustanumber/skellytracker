---
id: format.file_layout
title: File layout
kind: format
---

# File layout

## Behaviour

### File extension and naming

Sidecars use the `.yaml` extension. The filename is **`{model_id}.yaml`** — the `model_id` field inside the file matches the basename.

| Artifact | Example |
|----------|---------|
| Sidecar (one per family) | `yolo26.yaml` |
| ONNX models (any size × batch × precision) | `yolo26-nano_b2_fp16.onnx`, `yolo26-small_b4_fp32.onnx` |

ONNX filenames encode size, batch, and precision: `{model_id}-{size}_{batch}_{precision}.onnx` (e.g. `yolo26-nano_b2_fp32.onnx`, where `{batch}` is `b2`). For a `dynamic` batch, the batch component is omitted: `{model_id}-{size}_{precision}.onnx` (e.g. `rtmw-wholebody-l-m_fp32.onnx`).

### Style conventions

- Document marker `---` at the top of file.
- `#` prefix for comments.
- YAML mappings and sequences — no trailing commas, no quotes on bare strings.
- Flat top-level keys; nested objects use indentation.
- String values quoted only when necessary.

### Storage layout

Sidecars and their ONNX files live under a model cache directory (`{cache_dir}`), which defaults to `skellytracker/core`. The layout mirrors the detector taxonomy:

```text
{cache_dir}/
  detectors/
    calibration_detectors/          # calibration targets (e.g. Charuco boards) — hard-coded, not sidecar-defined
    object_detectors/
      {family}/                     # role: object_detector
        {model_id}.yaml
        {model_id}-{size}_{batch}_{precision}.onnx
    keypoint_detectors/
      {family}/                     # role: pose_estimator
        hand/
          {model_id}.yaml
          {model_id}-{size}_{batch}_{precision}.onnx
        face/
          {model_id}.yaml
          ...
        body/
          {model_id}.yaml
          ...
        wholebody/
          {model_id}.yaml
          {model_id}-{size}_{batch}_{precision}.onnx
    shared/                         # optional $ref fragments (no schema_version)
      skeletons/                    # tracked-point lists and skeletons
      class_ids/                    # class_id_map fragments (e.g. coco91.yaml)
```

| Branch | Role | Contents |
|--------|------|----------|
| `detectors/calibration_detectors/` | calibration | Calibration detectors (e.g. Charuco boards). Hard-coded in skellytracker — **not** specified via sidecars. |
| `detectors/object_detectors/{family}/` | `object_detector` | One sidecar per family, e.g. `yolo26/`. |
| `detectors/keypoint_detectors/{family}/{part}/` | `pose_estimator` | Keypoint models per body region — `hand`, `face`, `body`, `wholebody`. |
| `detectors/shared/` | — | Shared `$ref` fragments. Optional; carry no `schema_version`. |

```text
detectors/object_detectors/yolo26/
  yolo26.yaml
  yolo26-nano_b2_fp32.onnx
  yolo26-nano_b2_fp16.onnx
  yolo26-small_b2_fp32.onnx

detectors/keypoint_detectors/rtmw/wholebody/
  rtmw-wholebody.yaml
  rtmw-wholebody-l-m_fp32.onnx
  rtmw-wholebody-x-l_fp32.onnx
```

### File pairing rules

- A sidecar and its ONNX files live together in the leaf model directory (see [Storage layout](#storage-layout)).
- **Fragment files** (shared sections pulled in via `$ref`) are plain YAML values — a mapping, sequence, or scalar — and carry **no** `schema_version`. Convention: keep them under `detectors/shared/`.
- **Base files** referenced by `base` are ordinary sidecars (`{model_id}.yaml`). A derived file that declares `base` is itself another `{model_id}.yaml` and must override `model_id` (and `schema_version`) so its basename matches its own `model_id`.

## Validation rules

See [Identity](../common/identity.md#validation-rules) and [File composition](composition.md#validation-rules).

## Implementer guidance

## Authoring guidance
