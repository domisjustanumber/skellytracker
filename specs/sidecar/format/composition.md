---
id: format.composition
title: File composition
kind: format
since: v2024.09.1019
changed_in: [vNEXT]
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/resolution.py::_resolve_refs  # partial. The module checks the legacy $ref form, missing targets, cycles and paths outside the root (cache_dir in the code). It refuses the vNEXT form {$ref, sha256}. Nothing checks a hash, the encoding or the line endings (V-format.composition-3 to V-format.composition-5). Nothing checks that a derived file overrides schema_version.
  load: skellytracker/core/sidecar/resolution.py::resolve_sidecar_composition  # partial. Resolves only the legacy forms. It refuses sha256 next to $ref and a base that is not a string.
external_impl: []
tests: [skellytracker/tests/sidecar/test_resolution.py]
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# File composition

## Behaviour

Two directives provide reuse without duplication:

| Directive | Scope | Semantics |
|-----------|-------|-----------|
| `$ref` | any value, any depth | The directive **replaces** the value with the entire parsed content of the referenced file. The directive is recursive. |
| `base` | top-level only | The file **inherits** from another sidecar. The resolver **deep-merges** the keys of the current file **over** the base file. The current file wins. The directive is recursive. |

### `$ref` — reference another file for any value

A `$ref` directive is a YAML mapping. Its key `$ref` holds a file path. In a legacy sidecar, the mapping has **exactly one key**, `$ref`:

```yaml
decode: {$ref: shared/yolo26_decode.yaml}
```

At `vNEXT`, the mapping has **exactly two keys**: `$ref` and `sha256` (see [Reference hashes](#reference-hashes)):

```yaml
decode: {$ref: shared/yolo26_decode.yaml, sha256: "<sha256>"}
```

In the illustrative examples of this section, `<sha256>` stands for the hash of the target file. In an artifact, it stands for the hash of the ONNX file that `filename` names.

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
source:
  name: openmmlab-exporter
  version: 0.1.0
model_id: rtmw-wholebody
display_name: RTMW WholeBody
role: [pose_estimator]
pose:
  estimator_type: top_down_single_person
  requires_object_detector: true
  tracked_points: {$ref: ../../../shared/skeletons/coco133_tracked_points.yaml, sha256: "b59afc21868c1b4b0cac9bf0ae8a6398666d0b8a5da64a13d88079732d60441c"}
  connections: {$ref: ../../../shared/skeletons/coco133_skeletons.yaml, sha256: "bdc310c077f571a1a7d73d74f4fe6d1124b360c006512ea0d7ffb2a671f1709a"}
```

Rules:

- **Path resolution** — The resolver resolves a `$ref` path relative to the directory of the file that contains the directive. It does not resolve the path relative to the top-level sidecar. The path can point anywhere under `{sidecar_root}`. It must not escape above `{sidecar_root}`. `{sidecar_root}` is the root of the file that contains the directive (see [Sidecar roots](file-layout.md#sidecar-roots)). The resolver reads the target from that same root.
- **Recursion** — An included file can contain `$ref` directives. The resolver resolves them relative to that included file.
- **Cycle detection** — If the resolver visits a path that is already in the resolution stack, this is an error. The error names the cycle.
- **Strict form** — A mapping that contains `$ref` is a directive. In a legacy sidecar, the directive must have only the key `$ref`. At `vNEXT`, the directive must have exactly the keys `$ref` and `sha256`. Any other key is an error, for example `{$ref: x, other: y}`.
- **No schema on fragments** — Fragments do not carry `schema_version`. Only the top-level sidecar has a version and goes through validation.
- **Reserved** — `$ref` is reserved. The resolver strips it during resolution. A validated field must not have the name `$ref`.

### `base` — inherit from another sidecar and override

To start from an existing sidecar and override only what it changes, a sidecar can declare `base` at the top level:

```yaml
# detectors/object_detectors/yolo26-int8/yolo26-int8.yaml — a separately published int8 build of the family
# (illustrative: no current exporter writes derived files; this shows the mechanism)
---
schema_version: "vNEXT"
base: {$ref: ../yolo26/yolo26.yaml, sha256: "<sha256>"}
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
              sha256: "<sha256>"
```

Everything that the example does not list comes from `yolo26.yaml` unchanged. This includes `input`, `batching`, `outputs`, `decode`, the other sizes and the other precisions under `sizes.nano`.

At `vNEXT`, the merge keeps the `sha256` of a base artifact when the derived file does not override it. Thus a derived file that changes the `filename` of an artifact must also give the `sha256` of the new file (see [`sizes.<size>.onnx.batch_artifacts`](../common/sizes-and-artifacts.md#sizessizeonnxbatch_artifacts)).

At `vNEXT`, `base` is a mapping with exactly two keys: `$ref` and `sha256` (see [Reference hashes](#reference-hashes)). The `$ref` key holds the path of the base file. A legacy sidecar writes the path as a string, for example `base: ../yolo26/yolo26.yaml`. The resolver does not replace the `base` mapping with the content of the base file. It merges the current file over the base file, as for the string form.

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
- **Path resolution** — The resolver resolves a `base` path relative to the directory of the file that declares it. The path can point anywhere under `{sidecar_root}`. It must not escape above `{sidecar_root}`. `{sidecar_root}` is the root of the file that declares `base`. The resolver reads the base file from that same root.
- **Chainable** — A base file can itself declare `base`. The resolver resolves the chain depth-first before it merges the files.
- **Versioning** — After the merge, the `schema_version` of the derived file governs validation.
- **Reserved** — `base` is reserved at the top level. The resolver strips it during resolution.

### Reference hashes

These rules apply when the top-level sidecar has `schema_version >= vNEXT`. A tool can write the hashes, for example `tools/sidecar_refs.py --write`.

- **Form** — A `$ref` mapping must hold exactly two keys: `$ref` and `sha256`. A `base` must have the same form: `base: {$ref: <path>, sha256: <hash>}`.
- **Hash** — `sha256` is the SHA-256 of the exact bytes of the target file. Its value is a string of 64 lowercase hexadecimal characters. Write the value in quotes. YAML reads a value with digits only as a number.
- **Check before parse** — The resolver must read the bytes of the target file. It must compare the SHA-256 of these bytes with `sha256` before it parses the file. A different value is an error. The error names the file and the directive.
- **Bytes** — The top-level sidecar and each file in its tree must be UTF-8 without a byte order mark (BOM). These files must have LF line endings. A file with CRLF line endings is an error. The error must say that the file has CRLF line endings. A file with a BOM is an error.
- **Full tree** — The `schema_version` of the top-level sidecar sets the form of each directive in its tree. This includes the directives in fragments and in base files. Thus a fragment that refers to a different fragment also holds the hash of that fragment. The bytes of the top-level sidecar then pin the full tree. Also, a `vNEXT` sidecar can use only a base file whose directives have the `vNEXT` form. A legacy sidecar can use only a base file whose directives have the legacy form.
- **Every root** — These rules apply in every sidecar root, also in the package root.
- **Stripped** — The resolver removes `sha256` when it replaces or removes its directive. Validation never sees the `sha256` of a directive.

A legacy sidecar has no hashes (see [Legacy behaviour](#legacy-behaviour)).

### Resolution pipeline

The resolver resolves composition **before** validation. Validation never sees `$ref` / `base`:

```text
parse_sidecar_file(path)            # yaml.safe_load → raw dict
  → resolve_sidecar_composition()   # resolve $ref includes + base inheritance → flat dict
  → SidecarModel.model_validate()   # typed model
```

The resolver reads the bytes of the top-level sidecar. When the sidecar has `schema_version >= vNEXT`, a BOM or a CRLF line ending in these bytes is an error. At `vNEXT`, the resolver checks the bytes and the `sha256` of each target file before it parses that file (see [Reference hashes](#reference-hashes)).

Resolution errors are recoverable catalog errors. Each error names the file and the directive that cause it (missing file, parse failure in a fragment, cycle, `$ref` with a sibling key that its form does not allow, a hash that does not match, CRLF line endings, a BOM).

## Validation rules

- [ ] `V-format.composition-1` Each `$ref` directive must resolve to an existing file. It must terminate (no cycles). In a legacy sidecar, the directive must contain only the `$ref` key. At `vNEXT`, the directive must contain exactly the keys `$ref` and `sha256`.
- [ ] `V-format.composition-2` Each `base` directive must resolve and merge, with `null`-delete. The derived file must override `model_id` and `schema_version`.
- [ ] `V-format.composition-3` **(vNEXT)** Each `base` directive must be a mapping with exactly the keys `$ref` and `sha256`. Its `$ref` key must hold the path of the base file.
- [ ] `V-format.composition-4` **(vNEXT)** The `sha256` of each `$ref` directive and of each `base` directive must be a string of 64 lowercase hexadecimal characters. It must equal the SHA-256 of the exact bytes of the target file.
- [ ] `V-format.composition-5` **(vNEXT)** The top-level sidecar and each file in its tree must be UTF-8 without a BOM. These files must not have CRLF line endings.
- [ ] `V-format.composition-6` The target of each `$ref` directive and of each `base` directive must stay inside the `{sidecar_root}` of the file that refers to it.

For rules marked **(vNEXT)**, see [Validation rules](../README.md#validation-rules).

## Legacy behaviour

| Behaviour | `schema_version < vNEXT` (legacy) | `schema_version >= vNEXT` |
|-----------|-----------------------------------|---------------------------|
| Form of a `$ref` directive | Only the key `$ref` (the strict one-key form). No hash. | Exactly the keys `$ref` and `sha256`. |
| Form of `base` | A file path string. No hash. | A mapping with exactly the keys `$ref` and `sha256`. |
| Encoding and line endings of the files in the tree | No rule. | UTF-8 without a BOM, with LF line endings. |

The sidecars of the skellytracker package are legacy. They have no hashes. They get hashes only when they move to a release `schema_version`.

## Implementer guidance

No exporter evidence yet.

skellytracker (decision 0016):

- The resolver verifies the `sha256` of each `$ref` target and of each `base` target before it parses the target. The package resolver does not do this yet. `_resolve_refs` refuses a `$ref` mapping with a key other than `$ref`, and `_load_and_resolve` refuses a `base` that is not a string. Until the implementation stage adds the hash checks to `resolution.py`, the function `resolve` of `tools/sidecar_refs.py` is the temporary stand-in. It verifies the hashes, removes them from a copy of the tree and calls the unchanged `resolve_sidecar_composition` on the copy. Delete that function when `resolution.py` checks the hashes. Take each hash from the bytes of the file, not from a text-mode read. `parse_sidecar_file` opens the file in text mode, so it does not see a CR character. (skellytracker `skellytracker/core/sidecar/resolution.py` (`_resolve_refs`, `_load_and_resolve`, `parse_sidecar_file`); decision [0016](../../../notes/decisions/0016-sidecar-catalogs.md#reference-hashes), [Tools and line endings](../../../notes/decisions/0016-sidecar-catalogs.md#tools-and-line-endings)) (implementation stage)

## Authoring guidance

- No exporter writes `base`. The sidecar writers of the four exporters have no `base` key. (OpenMMLab-Exporter cce619d, Roboflow-Exporter c64fd2a, Ultralytics-Exporter 2e0280e, Qualcomm-Exporter 4ca4586; searched the Python sources outside the tests at each HEAD)
- Roboflow-Exporter is the only exporter that writes `$ref` today. `decode.class_id_map` is `{$ref: ../../shared/class_ids/coco91.yaml}`. The path is relative to the family directory `detectors/object_detectors/rfdetr/`. A test checks that the path resolves to `<root>/detectors/shared/class_ids/coco91.yaml`. (Roboflow-Exporter `rf_detr/sidecar.py:36-37` and `tests/test_sidecar.py:280-284`, b34e351)
- The fragment `coco91.yaml` is a bare YAML sequence of 91 integers. It starts with `---` and has no `schema_version`. Each `-1` slot has a comment ("unused" or "COCO id gap"). (Roboflow-Exporter `rf_detr/sidecar.py:331-344`, b34e351; local export `exports/detectors/shared/class_ids/coco91.yaml`, not in git)
- Qualcomm-Exporter wrote `pose.tracked_points` and `pose.connections` as `$ref` to `../../../shared/skeletons/{name}.yaml`. It removed the landmark models in 4ca4586. A test resolved each ref with `(path.parent / reference).resolve()` and checked `is_file()`. (Qualcomm-Exporter `qai_sidecar.py:123-142, 233-250` and `tests/test_qai_sidecar.py:63-91`, c7b9132)
- OpenMMLab-Exporter and Ultralytics-Exporter write `tracked_points` and `connections` in the sidecar. RTMW has 133 points and 65 edges. YOLO26 uses the COCO-17 constants. Both write every size in full. (OpenMMLab-Exporter `rtmw/sidecar.py:154-163`, eed3361; Ultralytics-Exporter `yolo_sidecar.py:38-76, 515-528`, f52ef68)
