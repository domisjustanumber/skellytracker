# Reference examples

This file gives the procedure that adds a reference example to the spec or replaces one. A
skellytracker session does it in [phase 3](phase-3-skellytracker.md), for a model with the verdict
`describes`.

## What the examples are

- The reference examples are in [`specs/model-sidecar/examples/`](../examples/README.md). Their
  provenance is in `specs/model-sidecar/inventory.yaml`.
- They are documentation. They show the rules of the spec in complete sidecars.
- They are not the package sidecars under `skellytracker/core/detectors/` (`yolox.yaml`,
  `rtmpose-*.yaml`, `rtmw-wholebody.yaml`). The detectors load the package sidecars at import time.
- `load_sidecar` never loads an example. An example has no ONNX file. Nothing runs inference with
  an example.
- An example is never a test input for package code. A test of a decode path uses a real export: a
  sidecar, its ONNX file and an upstream reference output from the exporter.

## Where the examples are used

- Each example is a file under `specs/model-sidecar/examples/detectors/`. Its path follows the
  `detectors/` layout of the package, so that each `$ref` path resolves.
- Package code does not read the examples. The tools under `tools/` read them:
  - `tools/tests/test_examples.py` checks that each example parses, resolves and has a provenance
    entry.
  - `uv run python tools/sidecar_trace.py matrix` writes
    [`TRACEABILITY.md`](../TRACEABILITY.md). It maps each example to the sections that it uses.
  - `uv run python tools/sidecar_trace.py examples --exporters-root <dir>` compares each example
    with the copy of its exporter.
- The package `SidecarModel` does not accept an example yet. It rejects `schema_version: "2.0.0"`,
  and it forbids the `source` and `sha256` keys. When the package accepts them, the examples can be
  validated with `SidecarModel`. They are never run.

## State of the examples

An item `spec change <ID>: <edit>` in `edits` of the entry in `inventory.yaml` is a spec-forced edit
([When a spec change makes an example invalid](#when-a-spec-change-makes-an-example-invalid);
[ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4).
Replace the example when the copy of its exporter obeys each rule
([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)).

## How to provide or replace an example

1. **Preconditions.**
   - The writer code of the exporter writes the sidecar. A sidecar that is written by hand is not
     a candidate.
   - The sidecar has `schema_version: "2.0.0"`, the open target, and only the keys that the spec
     defines. An export with another `schema_version` is not a candidate.
   - The checks of the exporter pass.
   - The parity check against the upstream library passes for at least one size: first the
     preprocessed input, then the final outputs.
2. **Copy. Do not edit.** Copy the sidecar of the exporter byte for byte. The source is `example/`
   of the current version of the `model` bundle ([Payload](hand-over.md#payload)). Only these
   changes are allowed:
   1. Remove the sizes after the first size. Replace them with the comment
      `# <sizes>: identical to <first> except input.shape, input.resize.target_size, output_shapes and filenames`.
      Before you write the comment, make sure that it is true for the export.
   2. Add comment lines that explain a field. Remove the header comment block of the exporter.
      Record "header comment removed" in the provenance.
   3. If the exporter does not write the `sha256` hashes, add them with
      `uv run python tools/sidecar_refs.py --write --placeholder`. Record "hashes added" in the
      provenance. When the exporter writes the hashes, the copy is byte for byte again. A sidecar
      with no `source` is not a candidate: `source` is required (`V-common.identity-4`).

   If the sidecar breaks a spec rule, the exporter must change, or a spec change proposal is
   necessary. Never correct the example by hand. If the real export shows a contract that the spec
   cannot describe, that is a gap. Propose the spec change first. Replace the example in the same
   cycle. A spec-forced edit is not a correction
   ([When a spec change makes an example invalid](#when-a-spec-change-makes-an-example-invalid);
   [ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4).
3. **Path.** The path of the example follows the
   [storage layout](../format/file-layout.md#storage-layout), also when the path of the exporter does
   not. For example, a sidecar in a folder that is not a group, such as `rtmo/body7/`, goes under
   the group folder that the layout gives. Record the path of the exporter in the provenance
   as a defect for the exporter to fix.

   **Fragments.** A fragment is a file that a `$ref` of the sidecar names: a file under
   `detectors/shared/` (a skeleton or a class-id map), or a file next to the sidecar (for example a
   `canonical_mapping` file). The example uses the same relative path. Copy each fragment of the
   exporter unchanged ([ADR-VV8B](../../../decisions/entries/VV8B-fragments-have-an-inventory-entry.md)):
   - Write its provenance in `fragments` of `specs/model-sidecar/inventory.yaml` (step 4). A package
     copy is not a source. The package sidecars stay outside the spec until they migrate.
   - If an example fragment exists at that path with different bytes, stop. Two exporters do not
     agree. The second exporter uses the bytes of the first copy, or a different file name.
4. **Provenance.** Write the entry of the example in `specs/model-sidecar/inventory.yaml`. Its
   header gives the keys and their meaning. Record each allowed edit from step 2 in `edits`, and the
   bundle ID and its version as `bundle: <bundle id>@v<k>`. Each new entry must have `bundle`.

   The entries come from `example/provenance.yaml` of the bundle. Check each entry against the bundle
   manifest. An entry has no `source`: the example sidecar holds it
   ([ADR-ZXD7](../../../decisions/entries/ZXD7-bundle-process.md)). Add `edits` (a list, which can be
   empty), `notes` (required) and `bundle`.

   For each fragment, write an entry in `fragments`, keyed by its path under
   `specs/model-sidecar/examples/`. Its keys are `exporter`, `exporter_path`, `tracked`, `commit`
   and `notes`. When no example reaches the fragment through `$ref` or `base`, delete the fragment
   and its entry.

   If a replaced example was the last example that uses `$ref` to a fragment copy, delete that copy
   and its entry in the same PR.
5. **Hashes.** The `$ref` hashes of an example are real. They must agree with the fragment
   files of the example, so copy each fragment unchanged from the exporter (step 3). Keep an ONNX
   `sha256` that the exporter wrote, also when the ONNX file is not in this repo.
   `tools/sidecar_refs.py --check` verifies an ONNX hash only when the file is present. If the
   exporter wrote no ONNX hash, use the reserved placeholder of 64 zeros. The placeholder is valid
   only in the examples of the spec.
6. **Check.** Apply the validation rules of each section that the sidecar uses (the
   [index of validation rules](../README.md)). Make sure that each `$ref` resolves. Run
   `uv run pytest tools/tests`. `tools/tests/test_examples.py` checks that the example resolves.
7. **Land it.** A new or replaced example changes no normative text. Thus it goes in a non-spec PR
   with its provenance ([`specs/model-sidecar/AGENTS.md`](../AGENTS.md)). A spec-forced edit goes in
   the content commit of its change
   ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4).
   Do not put a change of spec text in that PR. Put one example in each commit, so that a reviewer can examine and revert each
   replacement alone. This rule does not apply to a spec-forced edit. The commit message names the exporter commit. Follow the git rules of the
   skellytracker `AGENTS.md`, section 6.
8. **Keep it current.** When an exporter changes what it writes, replace the example again with the
   same steps. `tools/sidecar_trace.py examples` shows when an example and the copy of its exporter
   are not equal.

## When a spec change makes an example invalid

The examples must obey the spec at each commit. An accepted spec change can make an example break a
new or changed rule. Then the content commit of that change also edits the example. This edit is a
spec-forced edit ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 4). It
is not a correction of the example, and it is not a new copy. Steps 1, 2 and 7 of
[How to provide or replace an example](#how-to-provide-or-replace-an-example) do not apply to it.

1. Find each example that the change makes invalid. Part 7 of the accepted proposal names each
   example, its rule ID, its impact (`forced-edit`, `needs-export` or `removed (user ruling)`) and its
   edit ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)). Run
   `uv run python tools/sidecar_trace.py impact <range>` on the range of the content commit. Compare
   its report with part 7. The report is the cross-check, not the authority. If the change makes an
   example invalid and part 7 does not list it, stop. The proposal is already `accepted`, so the
   response gives the state `needs-contributor` with a finding: send a follow-up bundle
   (`base: <bundle id>`) with the missing part 7 row. The session lands the base and the follow-up in
   one content commit ([States](hand-over.md#states)).
2. `forced-edit`: make only the edit that the change gives. These edits are allowed:
   - Remove a field or a value.
   - Rename a key or an enum value.
   - Change `model_id`. Change each file name that contains `model_id` or a size key.
   - Move the file to the folder that the rule gives. The file name must be `{model_id}.yaml`.
   - Change a comment line that names an old value.
   - After an edit of a fragment, update each `sha256` of a `$ref` with
     `uv run python tools/sidecar_refs.py --write <example path>`. Do not use `--placeholder`.
3. Do not add a value that the change does not give. The only exception is a value that the
   session reads from the graph of an ONNX file of the exporter of the example
   ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md) item 3):
   - Read only the graph, with `onnx.load(path, load_external_data=False)`. Do not run the file
     ([ADR-AD33](../../../decisions/entries/AD33-bundles-are-untrusted-input.md)).
   - The `edits` item of step 7 names the value, the file by its path in the exporter repo and its
     SHA-256.
   - The next export copy of the example replaces the value.
4. `needs-export`: the example needs a value that the change does not give and that step 3 cannot
   give. Do not edit the example. The part 7 row of the accepted proposal is the request
   ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)).
   When the proposal is `accepted`, the exporter packs a new version of its `model` bundle, with
   `related` set to the proposal bundle. Its verdict `describes` uses the current spec text plus the
   accepted part 2 of that proposal. The content commit of the proposal lands that bundle as the
   replacement of the example. Step 12 gives the exception.

   A fragment is always a copy with no change, so a forced edit of a fragment is also
   `needs-export` ([ADR-VV8B](../../../decisions/entries/VV8B-fragments-have-an-inventory-entry.md)).
5. Keep the placeholder hash of 64 zeros for an ONNX file. `uv run python tools/sidecar_refs.py --check <example path>`
   must pass for each example that the commit changes. `uv run pytest tools/tests/test_examples.py`
   runs this check on each example.
6. Keep `kind`, `exporter`, `exporter_path`, `tracked` and `commit` of the entry. If the file moves,
   change the key of the entry. If `exporter_path` then does not follow the storage layout, set
   `exporter_layout_path`.
7. Add one item to `edits` for each spec-forced edit: `"spec change <ID>: <edit>"`. `<ID>` is the
   bare ID of the decision entry of the change, with no `ADR-` prefix. Keep the items of earlier
   changes. Change each note of the entry that names an old value.
8. If a doc test checks the old rule, change the test in the same content commit.
9. If an example moves, run `uv run python tools/sidecar_trace.py matrix` in the same content commit.
10. Put each spec-forced edit of one change in its content commit. The message of the content commit
    names each edited example and the rule ID of each edit.
11. Replace the example with steps 1 to 8 of
    [How to provide or replace an example](#how-to-provide-or-replace-an-example) only when the copy
    of the exporter obeys each rule. This clears the `spec change` items. Until then, keep the
    example and its `spec change` items, except when step 12 removes it.
12. **Removal by a user ruling.** A decision entry can record a user ruling that names an example
    that gets no rebuild. A content commit that makes such an example invalid removes it. It does not
    wait for a rebuild bundle ([ADR-C0YD](../../../decisions/entries/C0YD-the-part-7-row-is-the-re-export-request.md)):
    - Delete the example file and its entry in `specs/model-sidecar/inventory.yaml`. Delete each
      fragment that only this example used.
    - Keep the heading of the example in the
      [introduction to the examples](../examples/README.md), because other files link its anchor.
      Replace its text with one line that tells that the example is removed and cites the ruling.
    - Repair each link to the file and each text that names the example as a current fact.
    - Regenerate the matrix with `uv run python tools/sidecar_trace.py matrix`.
    - A part 7 row of the removed example has the impact `removed (user ruling)`. It is not a
      request. If an item under [Re-export requests](../decisions/open-work.md#re-export-requests)
      is open, remove the example from it.
    - The models of the example stay in "Scope of this revision" of the
      [changelog](../changelog.md) until a decision entry removes them.
    - The example comes back only with
      [How to provide or replace an example](#how-to-provide-or-replace-an-example), from a new
      `model` bundle.
