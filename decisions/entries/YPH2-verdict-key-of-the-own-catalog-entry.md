# YPH2 — The key of a stored verification verdict holds the catalog entry of its own EP

**Status:** accepted, 2026-11-19 (user).

## Decision

1. **Key.** The key of a stored verification result in `verdicts.json` of the EP store holds these
   parts: the ONNX Runtime distribution version of the platform, the pack id, the pack version, the
   driver version, the PCI ids of the GPU, the device key, the OS build and the digest of the
   catalog entry of the EP. In the second environment of the certify suite, the ONNX Runtime part
   is the version of that environment ([ADR-XSE7](XSE7-amd-eps-in-the-field-test.md)).
2. **Catalog entry.** The digest is the sha256 of three parts: the EP row with no `packs` and no
   `test_packs`, the row of the pack, and the lock row of the pack for the platform. A built-in EP
   and an EP of the Windows ML catalog have no pack row and no lock row. Their entry is the EP row.
3. **Invalidation.** A stored verdict stops matching only when its own EP row, its own pack row or
   its own lock row changes (for example a wheel sha256 or the pack version), or when the GPU, the
   driver, the device, the OS build or the ONNX Runtime distribution changes. A YAML comment, the row
   of an other EP, an other pack of the same EP and the other blocks of the catalog (for example
   `certification` or `hardware_classes`) keep it.
4. **Old verdicts.** A verdict stored with the old key, which held the whole-catalog revision, does
   not match the new key. Each installed pack is `installed_unverified` one last time, until its next
   `verify()`. There is no migration.

`store.verdict_key()` and `store.entry_digest()` hold the rule.

## Reason

- The user decision of 2026-11-19. Before, the key held `catalog.revision`, the sha256 of the whole
  catalog text. Each edit of `ep_catalog.yaml`, also a comment, then made each installed pack of each
  user `installed_unverified`, with a warning line, until the next `verify()`.
- The probe of a pack depends on the EP row (`ep_name`, the options, `l3_atol`), on the pack row and
  on the wheels. It does not depend on the rest of the catalog.
- The old key held `catalog.ort_version`, and the revision also changed when the Windows ML build of
  `ort_core.windows` changed. The distribution version keeps that invalidation without the revision.

## Consequences

- The Consequences of [ADR-Z5X7](Z5X7-field-test-state-and-directml.md) say that a catalog change
  gives each stored L3 verdict an other key. The Consequences of
  [ADR-1GGP](1GGP-ep-api-gives-an-application-each-ep-fact.md) and
  [ADR-4CB1](4CB1-suggested-ep-for-a-saved-key-of-an-older-release.md) say the same. That statement
  no longer holds. It is not a decision of those entries, so this entry supersedes none of them.
- An edit of a text field of the own EP row, for example `description`, also gives a new key. A list
  of the fields that change behaviour would miss a new field and keep a stale verdict.
- The other readers and writers of the store do not change. `last_used` in `verdicts.json` has the
  key `<pack_id>/<pack_version>`. The answer key of `certify.json` (`certification.pair_key()`) holds
  the EP key, the pack version, the OS and the GPU, and no catalog revision. `catalog_revision` in a
  pack manifest, a ref file, `status()` and a certification report is a record only.

## Evidence

Code facts: `verdict_key()` and `entry_digest()` in `core/eps/store.py`; `verify()` in
`core/eps/verification.py`; the test
`test_a_verdict_key_changes_only_with_the_catalog_entry_of_its_own_ep` in
`skellytracker/tests/test_eps_store.py`.

## Alternatives rejected

- **The whole-catalog revision.** Each catalog edit invalidates each verdict of each user.
- **Only the fields that change behaviour.** A new field that the list does not name keeps a stale
  verdict.
- **The whole EP row with its pack list.** An edit of an other pack of the same EP, for example the
  pack of an other ROCm release, invalidates the verdict.
- **A migration of the old keys.** One last `verify()` is enough.
