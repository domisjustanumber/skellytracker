---
id: format.composition
title: File composition
kind: format
since: v2024.09.1019
changed_in: []
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/resolution.py::_resolve_refs  # partial. The module checks the $ref form, missing targets, cycles and paths outside cache_dir. Nothing checks that a derived file overrides schema_version.
  load: skellytracker/core/sidecar/resolution.py::resolve_sidecar_composition
external_impl: []
tests: [skellytracker/tests/sidecar/test_resolution.py]
vectors: null
status: {spec: stable, validate: partial, load: implemented}
---

# File composition

## Behaviour

Two directives provide reuse without duplication:

| Directive | Scope | Semantics |
|-----------|-------|-----------|
| `$ref` | any value, any depth | The directive **replaces** the value with the entire parsed content of the referenced file. The directive is recursive. |
| `base` | top-level only | The file **inherits** from another sidecar. The resolver **deep-merges** the keys of the current file **over** the base file. The current file wins. The directive is recursive. |

### `$ref` — reference another file for any value

A `$ref` directive is a YAML mapping with **exactly one key**. The name of the key is `$ref`. The value of the key is a file path:

```yaml
decode: {$ref: shared/yolo26_decode.yaml}
```

The resolver loads the referenced file. It replaces the whole directive node with the parsed content of the file. This is true for content of any type: a scalar, a sequence or a mapping.

```yaml
# detectors/shared/skeletons/coco133_tracked_points.yaml  (a plain sequence)
- nose
- left_eye
- right_eye
# ... 133 names

# detectors/shared/skeletons/coco133_skeletons.yaml  (a plain sequence of named skeletons)
- name: rtmpose_skeleton
  edges:
    - [nose, left_eye]
    - [nose, right_eye]
- name: openpose_skeleton
  edges:
    - [nose, neck]
    - [neck, left_shoulder]

# detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml  (excerpt — see the full RTMW reference example)
---
schema_version: "vNEXT"
model_id: rtmw-wholebody
display_name: RTMW WholeBody
role: [pose_estimator]
pose:
  estimator_type: top_down_single_person
  requires_object_detector: true
  tracked_points: {$ref: ../../../shared/skeletons/coco133_tracked_points.yaml}
  connections: {$ref: ../../../shared/skeletons/coco133_skeletons.yaml}
```

Rules:

- **Path resolution** — The resolver resolves a `$ref` path relative to the directory of the file that contains the directive. It does not resolve the path relative to the root sidecar. The path can point anywhere under `{cache_dir}`. It must not escape above `{cache_dir}`.
- **Recursion** — An included file can contain `$ref` directives. The resolver resolves them relative to that included file.
- **Cycle detection** — If the resolver visits a path that is already in the resolution stack, this is an error. The error names the cycle.
- **Strict form** — If a mapping contains `$ref`, it must have only `$ref`. The mapping `{$ref: x, other: y}` is an error.
- **No schema on fragments** — Fragments do not carry `schema_version`. Only the top-level sidecar has a version and goes through validation.
- **Reserved** — `$ref` is reserved. The resolver strips it during resolution. A validated field must not have the name `$ref`.

### `base` — inherit from another sidecar and override

To start from an existing sidecar and override only what it changes, a sidecar can declare `base` at the top level:

```yaml
# detectors/object_detectors/yolo26-int8/yolo26-int8.yaml — a separately published int8 build of the family
# (illustrative: no current exporter writes derived files; this shows the mechanism)
---
schema_version: "vNEXT"
base: ../yolo26/yolo26.yaml
model_id: yolo26-int8
display_name: YOLO26 (int8)
sizes:
  nano:
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            int8:
              filename: yolo26-int8-nano_b1_int8.onnx
```

Everything that the example does not list comes from `yolo26.yaml` unchanged. This includes `input`, `batching`, `outputs`, `decode`, the other sizes and the other precisions under `sizes.nano`.

**Merge semantics (deep merge, current wins):**

| Node type | Rule |
|-----------|------|
| mapping + mapping | The merge works key by key. Nested mappings recurse. The merge keeps keys that are only in the base. Child keys replace base values. |
| mapping + sequence/scalar | The child replaces the base value entirely. |
| sequence + anything | The child replaces the base sequence entirely. The merge does **not** concatenate sequences. |
| scalar + anything | The child replaces the base value. |
| key absent in base | The merge adds the child key. |
| key mapped to `null` | The merge removes the key from the merged result (delete). |

A child key that maps to `null` deletes that key from the merged result. This follows JSON Merge Patch (RFC 7386). It is the only way to remove an inherited key. `null` is reserved for deletion. No field uses `null` as a value. When an optional field has no value, the sidecar omits the field. It never sets the field to `null`. The `null`-delete applies to the `base` and `sizes` deep-merges. It does not apply to `$ref`, which is a node replacement.

```yaml
# Drop the int8 precision inherited from the base:
sizes:
  nano:
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            int8: null
```

Rules:

- **Top-level only** — The resolver recognizes `base` only at the document root.
- **Path resolution** — The resolver resolves a `base` path relative to the directory of the file that declares it. The path can point anywhere under `{cache_dir}`. It must not escape above `{cache_dir}`.
- **Chainable** — A base file can itself declare `base`. The resolver resolves the chain depth-first before it merges the files.
- **Versioning** — After the merge, the `schema_version` of the derived file governs validation.
- **Reserved** — `base` is reserved at the top level. The resolver strips it during resolution.

### Resolution pipeline

The resolver resolves composition **before** validation. Validation never sees `$ref` / `base`:

```text
parse_sidecar_file(path)            # yaml.safe_load → raw dict
  → resolve_sidecar_composition()   # resolve $ref includes + base inheritance → flat dict
  → SidecarModel.model_validate()   # typed model
```

Resolution errors are recoverable catalog errors. Each error names the file and the directive that cause it (missing file, parse failure in a fragment, cycle, `$ref` with sibling keys).

## Validation rules

- [ ] `V-format.composition-1` Each `$ref` directive must resolve to an existing file. It must contain only the `$ref` key. It must terminate (no cycles).
- [ ] `V-format.composition-2` Each `base` directive must resolve and merge, with `null`-delete. The derived file must override `model_id` and `schema_version`.

## Implementer guidance

No exporter evidence yet.

## Authoring guidance

- No exporter writes `base`. The sidecar writers of the four exporters have no `base` key. (OpenMMLab-Exporter cce619d, Roboflow-Exporter c64fd2a, Ultralytics-Exporter 2e0280e, Qualcomm-Exporter 4ca4586; searched the Python sources outside the tests at each HEAD)
- Roboflow-Exporter is the only exporter that writes `$ref` today. `decode.class_id_map` is `{$ref: ../../shared/class_ids/coco91.yaml}`. The path is relative to the family directory `detectors/object_detectors/rfdetr/`. A test checks that the path resolves to `<root>/detectors/shared/class_ids/coco91.yaml`. (Roboflow-Exporter `rf_detr/sidecar.py:36-37` and `tests/test_sidecar.py:280-284`, b34e351)
- The fragment `coco91.yaml` is a bare YAML sequence of 91 integers. It starts with `---` and has no `schema_version`. Each `-1` slot has a comment ("unused" or "COCO id gap"). (Roboflow-Exporter `rf_detr/sidecar.py:331-344`, b34e351; local export `exports/detectors/shared/class_ids/coco91.yaml`, not in git)
- Qualcomm-Exporter wrote `pose.tracked_points` and `pose.connections` as `$ref` to `../../../shared/skeletons/{name}.yaml`. It removed the landmark models in 4ca4586. A test resolved each ref with `(path.parent / reference).resolve()` and checked `is_file()`. (Qualcomm-Exporter `qai_sidecar.py:123-142, 233-250` and `tests/test_qai_sidecar.py:63-91`, c7b9132)
- OpenMMLab-Exporter and Ultralytics-Exporter write `tracked_points` and `connections` in the sidecar. RTMW has 133 points and 65 edges. YOLO26 uses the COCO-17 constants. Both write every size in full. (OpenMMLab-Exporter `rtmw/sidecar.py:154-163`, eed3361; Ultralytics-Exporter `yolo_sidecar.py:38-76, 515-528`, f52ef68)
