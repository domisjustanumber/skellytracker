# VV8B — Each example fragment has an inventory entry

**Status:** absorbed into [`reference-examples.md#how-to-provide-or-replace-an-example`](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#how-to-provide-or-replace-an-example), [`reference-examples.md#when-a-spec-change-makes-an-example-invalid`](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid), [`inventory.yaml`](../../specs/model-sidecar/inventory.yaml), [`test_examples.py`](../../tools/tests/test_examples.py), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-yve0](yve0-example-fragments.md). It restates yve0 items 1, 3, 5 and 6.
It replaces yve0 items 2 and 4 and the package-copy sentence of
[ADR-C0YD](C0YD-the-part-7-row-is-the-re-export-request.md) item 4. The rest of C0YD stays.

1. **Fragments.** A YAML file under `specs/model-sidecar/examples/` is a sidecar when it has
   `schema_version` and a `model_id` equal to its file name. Each other YAML file there is a
   fragment. A fragment is in `shared/` or next to a sidecar.
2. **One source.** Each fragment has an entry in `fragments` of `specs/model-sidecar/inventory.yaml`,
   keyed by its path under the examples. A package copy is not a source. The package sidecars stay
   outside the spec until they migrate (C0YD item 1).
3. **Entry keys.** An entry has the keys `exporter`, `exporter_path`, `tracked`, `commit` and
   `notes`. It has no `kind` and no `edits`, because a fragment is always copied unchanged.
4. **Cleanup.** A fragment that no example reaches through `$ref` or `base` is stale. Delete it and
   its entry.
5. **Collisions.** An example fragment at the same path with different bytes stops the example
   procedure. The second exporter uses the bytes of the first copy, or a different file name.
6. **Forced edits.** A fragment is always copied unchanged, so a forced edit of a fragment is
   `needs-export`.
7. **Tests.** `tools/tests/test_examples.py` checks items 1 to 4.

[How to provide or replace an example](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#how-to-provide-or-replace-an-example)
states items 1 to 5. [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
states item 6. The header of `inventory.yaml` gives the keys.

## Reason

The user decided on 2026-11-10 to end the package-copy clause. C0YD item 1 keeps the package
sidecars outside the spec until they migrate. A package file then is not the provenance of a spec
example. With one source, each fragment has its exporter, path and commit, as each example has.
No current example has a fragment (`fragments: {}`), so no file needs a new entry.

## Consequences

- A fragment that equals a package file also gets an entry.
- The test `test_fragment_has_one_source` becomes `test_fragment_has_an_entry`. The package path
  `PACKAGE_DETECTORS` goes from the test.
