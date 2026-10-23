---
id: format.composition
title: File composition
kind: format
---

# File composition

## Behaviour

Two directives cover reuse without duplication:

| Directive | Scope | Semantics |
|-----------|-------|-----------|
| `$ref` | any value, any depth | The value is **replaced** by the entire parsed content of the referenced file. Recursive. |
| `base` | top-level only | The file **inherits** from another sidecar; the current file's keys are **deep-merged over** it (current wins). Recursive. |

### `$ref` — reference another file for any value

A `$ref` directive is a YAML mapping with **exactly one key** named `$ref`, whose value is a file path:

```yaml
decode: {$ref: shared/yolo26_decode.yaml}
```

The resolver loads the referenced file and replaces the whole directive node with its parsed content, regardless of whether that content is a scalar, sequence, or mapping.

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

- **Path resolution** — a `$ref` path resolves relative to the directory of the file that contains the directive (not the root sidecar). It may point anywhere under `{cache_dir}`, but must never escape above `{cache_dir}`.
- **Recursion** — an included file may itself contain `$ref` directives; they resolve relative to that file.
- **Cycle detection** — revisiting a path already in the resolution stack is an error naming the cycle.
- **Strict form** — a mapping containing `$ref` must have only `$ref`. `{$ref: x, other: y}` is an error.
- **No schema on fragments** — fragments do not carry `schema_version`; only the top-level sidecar is versioned and validated.
- **Reserved** — `$ref` is reserved and stripped during resolution; no validated field may be named `$ref`.

### `base` — inherit from another sidecar and override

A sidecar may declare `base` at the top level to start from an existing sidecar and override only what it changes:

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

Everything not listed above (`input`, `batching`, `outputs`, `decode`, the other sizes, and the other precisions under `sizes.nano`) comes from `yolo26.yaml` unchanged.

**Merge semantics (deep merge, current wins):**

| Node type | Rule |
|-----------|------|
| mapping + mapping | Merge key-by-key; nested mappings recurse. Keys only in the base are kept; child keys replace base values. |
| mapping + sequence/scalar | Child replaces the base value entirely. |
| sequence + anything | Child replaces the base sequence entirely (sequences are **not** concatenated). |
| scalar + anything | Child replaces. |
| key absent in base | Child key is added. |
| key mapped to `null` | The key is removed from the merged result (delete). |

A child key mapped to `null` deletes that key from the merged result (JSON Merge Patch, RFC 7386) — the only way to remove an inherited key. `null` is reserved for deletion: no field uses `null` as a value; optional fields are omitted, never `null`. `null`-delete applies to `base` and `sizes` deep-merges, not to `$ref` (a node replacement).

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

- **Top-level only** — `base` is recognized only at the document root.
- **Path resolution** — a `base` path resolves relative to the directory of the file that declares it; it may point anywhere under `{cache_dir}` and must never escape above `{cache_dir}`.
- **Chainable** — a base file may itself declare `base`; the chain resolves depth-first before merging.
- **Versioning** — after merging, the derived file's `schema_version` governs validation.
- **Reserved** — `base` is reserved at the top level and stripped during resolution.

### Resolution pipeline

Composition resolves **before** validation, so validation never sees `$ref` / `base`:

```text
parse_sidecar_file(path)            # yaml.safe_load → raw dict
  → resolve_sidecar_composition()   # resolve $ref includes + base inheritance → flat dict
  → SidecarModel.model_validate()   # typed model
```

Resolution errors are recoverable catalog errors naming the offending file and directive (missing file, parse failure in a fragment, cycle, `$ref` with sibling keys).

## Validation rules

- [ ] `V-format.composition-1` `$ref` directives resolve to existing files, contain only the `$ref` key, and terminate (no cycles).
- [ ] `V-format.composition-2` `base` directives resolve and merge (with `null`-delete), and the derived file overrides `model_id` and `schema_version`.

## Implementer guidance

## Authoring guidance
