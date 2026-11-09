# YS4C — Example removal by a user ruling

**Status:** superseded by [C0YD](C0YD-the-part-7-row-is-the-re-export-request.md), 2026-11-09 (user; PR: pending).

## Decision

This entry supersedes [ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) in full.
Items 1 to 5 restate the NB5F rules that stay. Item 2 changes when the item closes. Items 6 and 7 are
new.

1. **No change classes.** A spec change has no class. A spec change applies to each sidecar from the
   commit that lands it. No older spec text has a meaning to keep. The package sidecars are legacy
   sidecars: no spec change applies to them until the package migrates. The class sentence of
   [ADR-QMKS](QMKS-draft-sections-and-coverage-columns.md) item 1 has no case. The transition rules of
   NB5F item 1 are complete: the content change of
   [ADR-0QKK](0QKK-no-legacy-layer.md) removed the legacy text.
2. **One re-export request.** The heading
   [Re-export requests](../../specs/model-sidecar/decisions/open-work.md#re-export-requests) holds
   one item. It asks each exporter to rebuild each of its examples on one spec revision. It names its
   prerequisite changes. It opens when it names that revision and each change that it names is
   accepted. It closes when each example that stays is an export copy at that revision. No session
   adds a bullet for one example. An exporter does not start a rebuild before the item opens.
3. **Values read from an export graph.** NB5F item 3 stays: step 3 of
   [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   states it.
4. **`needs-export`.** NB5F item 4 stays: step 4 of the same heading states it. Item 6 gives the
   exception.
5. **The KDBD rules that stay.**
   - KDBD items 5 and 6 (the spec-forced edits, the package-copy clause, the impact run and the
     part 7 table):
     [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
     and [7. Exporter impact](../../specs/model-sidecar/templates/change-proposal.md#7-exporter-impact).
   - The 0009 rules of KDBD item 7:
     [Behaviour](../../specs/model-sidecar/pre/normalization.md#behaviour).
6. **Removal by a user ruling.** The user can rule that an example gets no rebuild. A decision entry
   records the ruling and names each example. Then each content commit that makes such an example
   invalid removes it, in place of the wait of item 4. Step 12 of
   [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
   gives the steps: the file, its provenance and its fragments go, its linked heading stays with one
   line, the links and the matrix are repaired, the Re-export item drops it, and a part 7 row of it is
   not a request. Its models stay in scope until an entry removes them.
7. **The ruling of 2026-11-09.** The user rules that these examples get no rebuild:
   - `rtmdet-person` and `rtmo-body7`. OpenMMLab-Exporter
     [ADR-8QD0](https://github.com/domisjustanumber/OpenMMLab-Exporter/blob/b513d2e31ebef95e2dde5d8561ef731614854167/decisions/entries/8QD0-yolox-and-rtmw-only-0039-ids-in-sidecar.md)
     defers both families with no trigger.
   - `yolo26` and `yolo26-body`. Ultralytics-Exporter has no sidecar work in sight.

   The models of these examples stay in scope. The content commit of 52NQ removes `rtmo-body7`. The
   content commit of the entry that supersedes
   [ADR-SE3Y](../../specs/model-sidecar/decisions/entries/SE3Y-license-and-training-data.md) removes
   the other three.

## Reason

- The user wants RTMW to land now. Under NB5F item 4, the SE3Y content commit waits for a rebuild of
  each of the five examples, and the 52NQ content commit waits for the `rtmo-body7` rebuild. The
  rebuilds of `rtmdet-person` and `rtmo-body7` will not come (OpenMMLab-Exporter ADR-8QD0). Thus no
  content commit could land, and the RTMW and YOLOX examples had no route.
- The user delegated the decision about the Ultralytics examples. Both are `kind: forecast`, and no
  exporter ever wrote them. Ultralytics-Exporter has no sidecar commit after 2026-10-06. Its writer
  still writes `schema_version` `v2024.09.1019` and no `license` block
  ([`yolo_sidecar.py:19`](https://github.com/domisjustanumber/Ultralytics-Exporter/blob/2e0280e050fb2bb16bf7f9a1ba89af5f18db67d4/yolo_sidecar.py#L19)).
- A ruling that names each example is an objective test. A test of the state of an exporter is not.
- KDBD rejected the removal of an invalid example because it breaks links and the traceability
  matrix. Item 6 repairs the links in the same commit, keeps each linked heading and regenerates the
  matrix.

## Consequences

- After both content commits, the examples are `rtmw-wholebody133` and `yolox-person`. These
  sections and values then have no example: `pre.resize.fit`, the `unit_float` normalization,
  `post.det.selection.none`, `post.pose.decode.coordinate`, `post.pose.bottom_up` and a sidecar with
  both roles. Each of these sections is `stable`, so no graduation gate and no release rule changes.
- `yolox-person` keeps the export example of `post.det.selection.nms`.

## Alternatives rejected

- **Keep the wait.** The rebuilds of four examples have no date, so RTMW and YOLOX do not land.
- **A `license` block from the session.** The SE3Y alternatives reject values from a skellytracker
  session. The ONNX metadata of YOLO26 holds only a license string, with no training data.
- **An optional `license` block until the rebuild.** The user asked for a mandatory license.
- **Known-invalid examples until the rebuild.** The spec then contradicts its examples.
- **A trigger "the exporter defers the rebuild".** Ultralytics-Exporter records no deferral.
