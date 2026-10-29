# Reference examples

This file gives the procedure that adds a reference example to the spec or replaces one. A
skellytracker session does it in [phase 3](phase-3-skellytracker.md), for a model with the verdict
`describes`. This procedure was the section "Reference examples" of
[`specs/sidecar-implementation-plan.md`](../../sidecar-implementation-plan.md#reference-examples)
(decision [b9fm](../../../decisions/entries/b9fm-finished-sidecar-plans.md)).

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
- `SidecarModel` does not accept a `vNEXT` sidecar yet. The loader rejects `"vNEXT"`, and the model
  forbids the `source` and `sha256` keys. When the package accepts them, the examples can be
  validated with `SidecarModel`. They are never run.

## State of the examples

The `kind` and the `notes` of each entry in `inventory.yaml` give the state of the example:

- `kind: forecast` is an example that is written from exporter code. Replace it when its exporter
  writes `vNEXT`.
- A note "Drifted" is an example that is not equal to the copy of its exporter. Replace it now.
- An item `spec change <ID>: <edit>` in `edits` is a spec-forced edit
  ([When a spec change makes an example invalid](#when-a-spec-change-makes-an-example-invalid);
  [ADR-KDBD](../../../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md)).
  Replace the example when the copy of its exporter obeys each rule.

The [introduction to the examples](../examples/README.md) tells which examples come from real
exports and which examples are forecasts.

## How to provide or replace an example

1. **Preconditions.**
   - The writer code of the exporter writes the sidecar. A sidecar that is written by hand is not
     a candidate.
   - The sidecar has `schema_version: "vNEXT"` and no legacy-only fields. An export with an older
     `schema_version` is not a candidate.
   - The checks of the exporter pass.
   - The parity check against the upstream library passes for at least one size: first the
     preprocessed input, then the final outputs.
2. **Copy. Do not edit.** Copy the sidecar of the exporter byte for byte. The source is `example/`
   of the current version of the `model` bundle ([Payload](hand-over.md#payload)). Only these
   changes are allowed:
   1. Remove the sizes after the first size. Replace them with the comment
      `# <sizes>: identical to <first> except input.shape, input.resize.target_size and filenames`.
      Before you write the comment, make sure that it is true for the export.
   2. Add comment lines that explain a field. Remove the header comment block of the exporter.
      Record "header comment removed" in the provenance.
   3. If the exporter does not write `source` and the `sha256` hashes, add them with
      `uv run python tools/sidecar_refs.py --write --placeholder --source <exporter package>==<version>`.
      Record "source and hashes added" in the provenance. When the exporter writes these fields,
      the copy is byte for byte again.

   If the sidecar breaks a spec rule, the exporter must change, or a spec change proposal is
   necessary. Never correct the example by hand. If the real export shows a contract that the spec
   cannot describe, that is a gap. Propose the spec change first. Replace the example in the same
   cycle. A spec-forced edit is not a correction
   ([When a spec change makes an example invalid](#when-a-spec-change-makes-an-example-invalid);
   [ADR-KDBD](../../../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md)).
3. **Path.** The path of the example follows the
   [storage layout](../format/file-layout.md#storage-layout), also when the path of the exporter does
   not. For example, OpenMMLab-Exporter writes RTMO body7 under `keypoint_detectors/rtmo/body7/`.
   The part folders of the spec are `hand`, `face`, `body` and `wholebody`, so the example is under
   `rtmo/body/`. Record the path of the exporter in the provenance as a defect for the exporter to
   fix.

   **Fragments.** A fragment is a file that a `$ref` of the sidecar names: a file under
   `detectors/shared/` (a skeleton or a class-id map), or a file next to the sidecar (for example a
   `canonical_mapping` file). The example uses the same relative path. Copy each fragment unchanged
   (ADR-[yve0](../../../decisions/entries/yve0-example-fragments.md)):
   - If the package has a fragment at the same path with the same bytes, copy it. It has no
     provenance entry.
   - If the package has a fragment at the same path with different bytes, stop. The exporter and the
     package do not agree. Fix one of them first.
   - If the package has no fragment at that path, copy the fragment of the exporter. Write its
     provenance in `fragments` of `specs/model-sidecar/inventory.yaml` (step 4).
   - If an example fragment exists at that path with different bytes, stop. Two exporters do not
     agree. The second exporter uses the bytes of the first copy, or a different file name.
   - Use a package fragment when it has the same content. Do not add a copy of it under a new name.
4. **Provenance.** Write the entry of the example in `specs/model-sidecar/inventory.yaml`. Record
   these items:
   - the exporter repo;
   - the path of the copy of the exporter;
   - whether git tracks that copy (most exports are in untracked `exports/` folders, so a commit
     alone does not identify the file);
   - the exporter commit of the code that wrote the copy;
   - the export command;
   - the date;
   - each allowed edit from step 2;
   - the bundle ID and its version, as `bundle: <bundle id>@v<k>`.

   The entries come from `example/provenance.yaml` of the bundle. Check each entry against the bundle
   manifest. Drop `source`: it is not an inventory key. It is the `<exporter package>==<version>`
   value of the `sidecar_refs.py --source` call of step 2. Add `edits` (a list, which can be empty),
   `notes` (required) and `bundle`.

   In the same commit, delete each bullet under
   [Re-export requests](../decisions/open-work.md#re-export-requests) that this `model` bundle
   answers. Match it by the owner repo and the `model_id`. If the bullet has other targets, delete
   only the answered target.

   For each fragment with no package copy, write an entry in `fragments`, keyed by its path under
   `specs/model-sidecar/examples/`. Its keys are `exporter`, `exporter_path`, `tracked`, `commit`
   and `notes`. When the package gets a copy of the fragment, delete the entry.

   If a replaced example was the last example that uses `$ref` to a fragment copy, delete that copy
   and its entry in the same PR.
5. **Hashes.** The `$ref` and `base` hashes of an example are real. They must agree with the fragment
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
   ([ADR-KDBD](../../../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md)).
   Do not put a change of spec text in that PR. Put one example in each commit, so that a reviewer can examine and revert each
   replacement alone. This rule does not apply to a spec-forced edit. The commit message names the exporter commit. Follow the git rules of the
   skellytracker `AGENTS.md`, section 6.
8. **Keep it current.** When an exporter changes what it writes, replace the example again with the
   same steps. `tools/sidecar_trace.py examples` shows when an example and the copy of its exporter
   are not equal.

Example: the RTMO body7 example comes from the tracked copy `notes/decisions/rtmo-body7.yaml` of
OpenMMLab-Exporter at commit
[`38ed76f`](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/38ed76f1221d68987e1d56b84daa99559d97588c/notes/decisions/rtmo-body7.yaml).
That copy is equal to its export, plus header comments.

## When a spec change makes an example invalid

The examples must obey the spec at each commit. An accepted spec change can make an example break a
new or changed rule. Then the content commit of that change also edits the example. This edit is a
spec-forced edit ([ADR-KDBD](../../../decisions/entries/KDBD-change-classes-and-spec-forced-edits.md)). It
is not a correction of the example, and it is not a new copy. Steps 1, 2 and 7 of
[How to provide or replace an example](#how-to-provide-or-replace-an-example) do not apply to it.

1. Find each example that the change makes invalid. Part 7 of the accepted proposal names each
   example, its rule ID, its impact (`forced-edit` or `needs-export`) and its edit. Run
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
   - After an edit of a fragment, update each `sha256` of a `$ref` or `base` with
     `uv run python tools/sidecar_refs.py --write <example path>`. Do not use `--placeholder`.
3. Do not add a value that the change does not give.
4. `needs-export`: the example needs a value that only an export can give. Do not edit the example.
   The content commit waits for the re-export bundle, in this order:
   1. When the user accepts the proposal, a non-spec commit adds a bullet for the example under
      [Re-export requests](../decisions/open-work.md#re-export-requests).
   2. The exporter packs a new version of its `model` bundle, with `related` set to the proposal
      bundle. Its verdict `describes` uses the current spec text plus the accepted part 2 of that
      proposal. `verify` and the session check it against that text.
   3. The content commit of the proposal lands that bundle as the replacement of the example. The
      `inventory.yaml` entry gets `bundle: <bundle id>@v<k>`. The same commit deletes the bullet.

   A forced edit of a fragment that equals a package copy
   (ADR-[yve0](../../../decisions/entries/yve0-example-fragments.md)) is also `needs-export`. The package
   code does not change in the spec-build stage, and a copy under a new name is not allowed.
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
    example and its `spec change` items.
