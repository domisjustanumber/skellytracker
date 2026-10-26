# yve0 — Example fragments without a package copy

**Status:** accepted, 2026-10-26 (user).

## Decision

1. **Fragments.** A YAML file under `specs/model-sidecar/examples/` is a sidecar when it has
   `schema_version` and a `model_id` equal to its file name. This is the rule of
   `tools/sidecar_trace.py`. Each other YAML file there is a fragment. A fragment is in `shared/` or
   next to a sidecar, for example a `canonical_mapping` file.
2. **One source.** Each fragment has exactly one source:
   - a package copy at the same path under `skellytracker/core/detectors/`, with the same bytes; or
   - an entry in `fragments` of `specs/model-sidecar/inventory.yaml`, keyed by its path under the
     examples.
3. **Entry keys.** A `fragments` entry has the keys `exporter`, `exporter_path`, `tracked`, `commit`
   and `notes`. It has no `kind` and no `edits`, because a fragment is always copied unchanged. Its
   `sha256` in the sidecar pins its bytes.
4. **Cleanup.** When the package gets a copy of the fragment, delete the entry. A fragment that no
   example reaches through `$ref` or `base` is stale. Delete it and its entry.
5. **Collisions.** A fragment at a package path with different bytes stops the example procedure. An
   example fragment at the same path with different bytes also stops it. The second exporter uses the
   bytes of the first copy, or a different file name.
6. **Tests.** `tools/tests/test_examples.py` checks rules 1 to 4. `tools/sidecar_refs.py` gets the
   function `files`, which lists the YAML files of a sidecar tree.

## Reason

- Before this entry, `test_shared_fragment_equals_its_package_copy` read the package copy of each
  file under `examples/detectors/shared/` with no existence check. A new fragment of an exporter
  failed with an error. In the spec-build stage, no file under `skellytracker/` can change, so the
  package cannot get the copy.
- The procedure "How to provide or replace an example" said: copy such a fragment "with its own
  provenance". `inventory.yaml` had no key for it, and `test_every_example_has_one_provenance_entry`
  refused a fragment entry under `examples`.
- `example_paths()` took each YAML file outside `shared/` as an example. Package sidecars name local
  fragments, for example `canonical_mapping: {$ref: rtmpose_hand_to_canonical_mapping.yaml}` in
  `skellytracker/core/detectors/keypoint_detectors/rtmpose/hand/rtmpose-hand.yaml`. A copy of such a
  file next to an example failed the `model_id` check and the provenance check.
- The models of the two MediaPipe hand exporters will probably name the same 21-point lists. The
  collision rule gives one copy.

## Evidence

- `tools/tests/test_examples.py`. A run of 2026-10-26 with a temporary fragment
  `shared/skeletons/new21_tracked_points.yaml`: with no entry, `test_fragment_has_one_source` and
  `test_every_fragment_is_used_by_an_example` failed. With an entry, only the second test failed.
  The fragment and the entry were then removed.

## Alternatives rejected

- **Add the fragment to the package.** No file under `skellytracker/` changes in the spec-build
  stage (ADR-[0014](0014-spec-lifecycle.md)).
- **Inline the fragment in the example.** The example is then not a byte-for-byte copy, and the
  `$ref` hash of the exporter is lost.
- **Skip a fragment with no package copy.** Then the example has a file with no provenance.
