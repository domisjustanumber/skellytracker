---
id: format.composition
title: File composition
kind: format
selectors: []
implemented_by:
  validate: skellytracker/core/sidecar/resolution.py::_resolve_refs  # partial. The module checks the one-key $ref form, missing targets, cycles and paths outside the root (cache_dir in the code). It refuses the form {$ref, sha256}. Nothing checks a hash, the encoding or the line endings (V-format.composition-2 and V-format.composition-3). Nothing checks V-format.composition-5: SidecarModel forbids undeclared keys, but it declares preserve_aspect_ratio, requires_nms and may_include_non_person_classes.
  load: skellytracker/core/sidecar/resolution.py::resolve_sidecar_composition  # partial. Resolves only the one-key $ref form and the string base form. It refuses sha256 next to $ref and a base that is not a string.
external_impl: []
tests: [skellytracker/tests/sidecar/test_resolution.py]
vectors: null
status: {spec: stable, validate: partial, load: partial}
---

# File composition

## Behaviour

One directive provides reuse without duplication: `$ref`. It can be at any value, at any depth. The directive **replaces** the value with the entire parsed content of the referenced file. The directive is recursive. `$ref` is the only directive that reuses a file. The spec has no `base` directive ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

No field has the value `null`. A sidecar omits an optional field that has no value ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).

A mapping has no duplicate key. This applies to the top-level sidecar and to each file in its tree. The loader refuses a file with a duplicate key. It does not keep the first or the last value ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md)).

### `$ref` — reference another file for any value

A `$ref` directive is a YAML mapping with **exactly two keys**: `$ref` and `sha256` (see [Reference hashes](#reference-hashes)). The key `$ref` holds a file path ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)):

```yaml
object: {$ref: shared/yolo26_object.yaml, sha256: "<sha256>"}
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

# detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml  (an illustrative excerpt; the fragments are the package copies)
---
schema_version: "2.0.0"
source:
  name: openmmlab-exporter
  version: 0.1.0
model_id: rtmw-wholebody
display_name: RTMW WholeBody
role: [keypoint_detector]
keypoint:
  estimator_type: top_down_single_person
  requires_object_detector: true
  point_names: {$ref: ../../../shared/skeletons/coco133_tracked_points.yaml, sha256: "b59afc21868c1b4b0cac9bf0ae8a6398666d0b8a5da64a13d88079732d60441c"}
  skeletons: {$ref: ../../../shared/skeletons/coco133_skeletons.yaml, sha256: "bdc310c077f571a1a7d73d74f4fe6d1124b360c006512ea0d7ffb2a671f1709a"}
```

Rules:

- **Path resolution** — The resolver resolves a `$ref` path relative to the directory of the file that contains the directive. It does not resolve the path relative to the top-level sidecar. The path can point anywhere under `{sidecar_root}`. It must not escape above `{sidecar_root}`. `{sidecar_root}` is the root of the file that contains the directive (see [Sidecar roots](file-layout.md#sidecar-roots)). The resolver reads the target from that same root.
- **Recursion** — An included file can contain `$ref` directives. The resolver resolves them relative to that included file.
- **Cycle detection** — If the resolver visits a path that is already in the resolution stack, this is an error. The error names the cycle.
- **Strict form** — A mapping that contains `$ref` is a directive. The directive must have exactly the keys `$ref` and `sha256` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). Any other key is an error, for example `{$ref: x, other: y}`.
- **No schema on fragments** — Fragments do not carry `schema_version`. Only the top-level sidecar has a version and goes through validation.
- **Reserved** — `$ref` is reserved. The resolver strips it during resolution. A validated field must not have the name `$ref`.

### Reference hashes

These rules apply to every sidecar ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). A tool can write the hashes, for example `tools/sidecar_refs.py --write`.

- **Form** — A `$ref` mapping must hold exactly two keys: `$ref` and `sha256`.
- **Hash** — `sha256` is the SHA-256 of the exact bytes of the target file. Its value is a string of 64 lowercase hexadecimal characters. Write the value in quotes. YAML reads a value with digits only as a number.
- **Check before parse** — The resolver must read the bytes of the target file. It must compare the SHA-256 of these bytes with `sha256` before it parses the file. A different value is an error. The error names the file and the directive.
- **Bytes** — The top-level sidecar and each file in its tree must be UTF-8 without a byte order mark (BOM). These files must have LF line endings. A file with CRLF line endings is an error. The error must say that the file has CRLF line endings. A file with a BOM is an error.
- **Full tree** — Each directive in the tree of the top-level sidecar has this form. This includes the directives in fragments. Thus a fragment that refers to a different fragment also holds the hash of that fragment. The bytes of the top-level sidecar then pin the full tree ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
- **Every root** — These rules apply in every sidecar root, also in the package root.
- **Stripped** — The resolver removes `sha256` when it replaces or removes its directive. Validation never sees the `sha256` of a directive.

### Resolution pipeline

The resolver resolves composition **before** validation. Validation never sees `$ref`:

```text
parse_sidecar_file(path)            # yaml.safe_load → raw dict
  → resolve_sidecar_composition()   # resolve $ref includes → flat dict
  → SidecarModel.model_validate()   # typed model
```

The resolver reads the bytes of the top-level sidecar. A BOM or a CRLF line ending in these bytes is an error. The resolver checks the bytes and the `sha256` of each target file before it parses that file (see [Reference hashes](#reference-hashes)).

Resolution errors are recoverable catalog errors. Each error names the file and the directive that cause it (missing file, parse failure in a fragment, duplicate key, cycle, `$ref` with a sibling key that its form does not allow, a hash that does not match, CRLF line endings, a BOM).

## Validation rules

- [ ] `V-format.composition-1` Each `$ref` directive must resolve to an existing file. It must terminate (no cycles). The directive must contain exactly the keys `$ref` and `sha256` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
- [ ] `V-format.composition-2` The `sha256` of each `$ref` directive must be a string of 64 lowercase hexadecimal characters. It must equal the SHA-256 of the exact bytes of the target file ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-format.composition-3` The top-level sidecar and each file in its tree must be UTF-8 without a BOM. These files must not have CRLF line endings.
- [ ] `V-format.composition-4` The target of each `$ref` directive must stay inside the `{sidecar_root}` of the file that refers to it ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)).
- [ ] `V-format.composition-5` Each key of the resolved sidecar must be a key that the spec defines. A key that the spec does not define is invalid. This rule does not apply to the keys of a map whose keys are names, for example the size names of `sizes` ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)).
- [ ] `V-format.composition-6` A mapping in the top-level sidecar or in a file in its tree must not have a duplicate key ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md)).

## Implementer guidance

No exporter evidence yet.

skellytracker ([ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md)):

- The resolver verifies the `sha256` of each `$ref` target before it parses the target. The package resolver does not do this yet. `_resolve_refs` refuses a `$ref` mapping with a key other than `$ref`. `_load_and_resolve` still resolves a string `base`, which the spec does not define ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). Until the implementation stage adds the hash checks to `resolution.py`, the function `resolve` of `tools/sidecar_refs.py` is the temporary stand-in. It verifies the hashes, removes them from a copy of the tree and calls the unchanged `resolve_sidecar_composition` on the copy. Delete that function when `resolution.py` checks the hashes. Take each hash from the bytes of the file, not from a text-mode read. `parse_sidecar_file` opens the file in text mode, so it does not see a CR character. (skellytracker `skellytracker/core/sidecar/resolution.py` (`_resolve_refs`, `_load_and_resolve`, `parse_sidecar_file`); [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#reference-hashes), [Tools and line endings](../../../decisions/entries/0016-sidecar-catalogs.md#tools-and-line-endings)) (implementation stage)
- The doc test `test_example_has_only_keys_that_the_spec_defines` of `tools/tests/test_examples.py` checks V-format.composition-5 on each reference example. The package `SidecarModel` refuses a key that it does not declare (`extra="forbid"`). It declares `preserve_aspect_ratio`, `requires_nms` and `may_include_non_person_classes`, so it does not check V-format.composition-5. (skellytracker `skellytracker/core/sidecar/model.py`; [ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)) (implementation stage)
- The sidecars of the skellytracker package have no hashes. They stay outside the spec until they migrate ([ADR-0QKK](../../../decisions/entries/0QKK-no-legacy-layer.md)). (implementation stage)
- `tools/sidecar_refs.py` writes and checks the hashes. (skellytracker `tools/sidecar_refs.py`; [ADR-0016](../../../decisions/entries/0016-sidecar-catalogs.md#tools-and-line-endings))
  - `--write` works depth first. It writes the hashes inside a fragment before it takes the hash of that fragment.
  - `--write` writes the `sha256` of an artifact only when the ONNX file is present.
  - `--write --placeholder` writes the placeholder on an artifact that has no `sha256`. It never replaces a real hash.
  - `--write --source <name>==<version>` adds `source` when the file has none. It never changes an existing `source`.
  - `--write` edits only the `sha256` entries and the `source` block as text. It keeps all other bytes. It never loads the YAML and writes it out again.
  - `--check` verifies each `$ref` hash. It verifies an ONNX hash only when the ONNX file is present. It reports a CRLF file and a BOM as separate errors. It accepts the placeholder only under `specs/model-sidecar/examples/`.
  - The tool uses only the standard library and PyYAML. It does not import `skellytracker`.
  - The implementation stage moves `--write` and `--check` into the package as a command, with a thin wrapper in `tools/`. (implementation stage)

## Authoring guidance

- Do not write `base`. The spec has no `base` directive ([ADR-90CE](../../../decisions/entries/90CE-minimal-sidecar-contract.md)). No exporter writes `base`. The sidecar writers of the four exporters have no `base` key. ([OpenMMLab-Exporter](https://github.com/domisjustanumber/OpenMMLab-Exporter/tree/cce619dcfb8acae4ed66c59db935ac8cc0aa5b5b), [Roboflow-Exporter](https://github.com/domisjustanumber/Roboflow-Exporter/tree/c64fd2a32a51e29cdbf9b1b31473c8e441839d07), [Ultralytics-Exporter](https://github.com/domisjustanumber/Ultralytics-Exporter/tree/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4), [Qualcomm-Exporter](https://github.com/domisjustanumber/Qualcomm-Exporter/tree/4ca45868431b67350c3c7ed900d5b3ff9f409905); searched the Python sources outside the tests at each of these commits)
- Roboflow-Exporter is the only exporter that writes `$ref` today. It writes its class list as a `$ref` relative to the family directory `detectors/object_detectors/rfdetr/`, and a test checks that the path resolves. Its folder is `shared/class_ids/`. In the spec layout, the folder is `shared/classes/`: `object.classes` is `{$ref: ../../shared/classes/coco91.yaml, sha256: "<sha256>"}` ([Storage layout](file-layout.md#storage-layout)). (Roboflow-Exporter [`rf_detr/sidecar.py:36-37`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L36-L37) and [`tests/test_sidecar.py:280-284`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/tests/test_sidecar.py#L280-L284))
- The fragment `coco91.yaml` of the exporter is a bare YAML sequence of 91 integers. It starts with `---` and has no `schema_version`. Each `-1` slot has a comment ("unused" or "COCO id gap"). As `object.classes`, the fragment holds 91 class names, with `null` for each of these slots ([ADR-88WQ](../../../decisions/entries/88WQ-sidecar-vocabulary.md)). (Roboflow-Exporter [`rf_detr/sidecar.py:331-344`](https://github.com/domisjustanumber/Roboflow-Exporter/blob/b34e351000d325014ec275432082c6a3a9380157/rf_detr/sidecar.py#L331-L344); local export `exports/detectors/shared/class_ids/coco91.yaml`, not in git)
- Qualcomm-Exporter wrote `keypoint.point_names` and `keypoint.skeletons` as `$ref` to `../../../shared/skeletons/{name}.yaml`. It removed the landmark models in [a later commit](https://github.com/domisjustanumber/Qualcomm-Exporter/commit/4ca45868431b67350c3c7ed900d5b3ff9f409905). A test resolved each ref with `(path.parent / reference).resolve()` and checked `is_file()`. (Qualcomm-Exporter [`qai_sidecar.py:123-142`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L123-L142), [`qai_sidecar.py:233-250`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/qai_sidecar.py#L233-L250) and [`tests/test_qai_sidecar.py:63-91`](https://github.com/domisjustanumber/Qualcomm-Exporter/blob/c7b91329e70963b38e14c8429bc2cb26d449478e/tests/test_qai_sidecar.py#L63-L91))
- OpenMMLab-Exporter and Ultralytics-Exporter write `point_names` and `skeletons` in the sidecar. RTMW has 133 points and 65 edges. YOLO26 uses the COCO-17 constants. Both write every size in full. (OpenMMLab-Exporter [`rtmw/sidecar.py:154-163`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/eed3361aa31e02df160c33a18a3db9ba182b5551/rtmw/sidecar.py#L154-L163); Ultralytics-Exporter [`yolo_sidecar.py:38-76`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L38-L76), [`yolo_sidecar.py:515-528`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/f52ef687a7a651447ff289d0e40a7856c2b7d50c/yolo_sidecar.py#L515-L528))
