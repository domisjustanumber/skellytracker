# C0YD — The part 7 row is the re-export request

**Status:** superseded by [BQZ9](BQZ9-intake-process-consolidation.md), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-YS4C](YS4C-example-removal-by-a-user-ruling.md) in full. Items 1, 3, 4,
5 and 6 restate YS4C items 1, 3, 5, 6 and 7. Item 2 replaces YS4C items 2 and 4. Item 7 is new.

1. **No change classes.** A spec change has no class. It applies to each sidecar from the commit that
   lands it. No older spec text has a meaning to keep. The package sidecars are legacy sidecars: no
   spec change applies to them until the package migrates. The class sentence of
   [ADR-QMKS](QMKS-draft-sections-and-coverage-columns.md) item 1 has no case.
2. **The part 7 row is the request.** No re-export item is open. The part 7 `needs-export` row of an
   accepted proposal is the request for a new export of the example. Step 4 of
   [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   states it. If the user opens a re-export item, the heading Re-export requests of the spec
   `open-work.md` holds one item, and the exporter follows it.
   [Re-export requests](../../specs/model-sidecar/model-addition-workflow/hand-over.md#re-export-requests)
   states it.
3. **Values read from an export graph.** Step 3 of
   [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   states this rule.
4. **The rules of KDBD and 0009 that stay.**
   - The spec-forced edits, the package-copy clause of
     [ADR-yve0](yve0-example-fragments.md) fragments, the impact run and the part 7 table:
     [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
     and [7. Exporter impact](../../specs/model-sidecar/templates/change-proposal.md#7-exporter-impact).
     The package-copy clause stays: a forced edit of a fragment that equals a package copy is
     `needs-export`. Thus its part 7 row is the request of item 2.
   - The 0009 rules: [Behaviour](../../specs/model-sidecar/pre/normalization.md#behaviour).
5. **Removal by a user ruling.** A decision entry can record a user ruling that names an example with
   no rebuild. Each content commit that makes such an example invalid removes it. Step 12 of
   [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   gives the steps. Part 7 gives such an example the impact `removed (user ruling)`. Its row is not a
   request. Its models stay in scope until an entry removes them.
6. **The ruling of 2026-11-09.** The user ruled that `rtmdet-person`, `rtmo-body7`, `yolo26` and
   `yolo26-body` get no rebuild. The content commits of
   [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md) and
   [ADR-NBG2](../../specs/model-sidecar/decisions/entries/NBG2-license-and-training-data-without-the-deferred-examples.md)
   removed them. Their models stay in scope.
7. **No pre-bundle and no forecast examples.** Each example entry of
   `specs/model-sidecar/inventory.yaml` has `bundle` and `kind: export`. `tools/intake_bundle.py` has
   no `NO_BUNDLE_EXAMPLES` and no `OPTIONAL_INVENTORY_KEYS`.

## Reason

- The re-export item closed when the NBG2 content commit landed `rtmw-wholebody133`. Each example
  that stays is an export copy with a bundle. `NO_BUNDLE_EXAMPLES` is empty, `fragments` is `{}`, and
  no example uses `$ref`. Each "until the item closes" branch of the workflow is thus dead text that
  each exporter and each lander reads.
- The retrospective of the YOLOX and RTMW intakes (2026-11-06 to 2026-11-09) found these branches as
  reading cost with no case.
- The graph read of step 3 is not dead. It is the forced-edit route of a future spec change that makes
  an export example invalid, and it saves an exporter round trip.
- The fragment rules of yve0 and the package-copy clause are not dead. Their tests skip only because
  no current example has a fragment. They apply again when an example uses `$ref`.

## Alternatives rejected

- **Delete step 3 and the fragment rules.** They are live rules. No case shows that they cost a reader time.
- **Keep the closed-item branches.** Each reader must decide again that they do not apply.
