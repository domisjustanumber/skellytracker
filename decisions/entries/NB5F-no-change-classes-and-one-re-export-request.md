# NB5F — No change classes and one re-export request

**Status:** accepted, 2026-11-02 (user; PR: pending).

## Decision

This entry supersedes [ADR-KDBD](KDBD-change-classes-and-spec-forced-edits.md) in full. Items 1 to
4 are new. Item 5 restates by links the rules of KDBD that stay
([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

1. **No change classes.** A spec change has no class. The classes `vnext`, `clarification` and
   `breaking` go, with the manifest key `change_class` and part 2.6 (Legacy behaviour and version
   effect) of the change proposal. The class rules of the skills and the workflow go. A spec change
   applies to each sidecar from the commit that lands it. No older spec text has a meaning to keep.
   The package sidecars are legacy sidecars: no spec change applies to them until the package
   migrates. The class wording of the changelog and the other legacy text of the spec stay until
   the content change that removes them. Until that change, no other content change lands. The
   `vNEXT`-text bullet of part 2.6
   ([ADR-YNX0](../../specs/model-sidecar/decisions/entries/YNX0-vnext-scope-list.md) item 4) moves
   to part 7 of the template. The class sentences of
   [ADR-QMKS](QMKS-draft-sections-and-coverage-columns.md) item 1,
   [ADR-JB5J](JB5J-one-batch-form-for-each-sidecar.md) item 1 and
   [ADR-CRV0](../../specs/model-sidecar/decisions/entries/CRV0-output-shapes-in-each-batch-group.md)
   have no case. This entry changes no other rule of them.
2. **One re-export request.** The heading
   [Re-export requests](../../specs/model-sidecar/decisions/open-work.md#re-export-requests) holds
   one item. It replaces the current requests. It asks each exporter to rebuild each of its examples
   on one spec revision. It names its prerequisite changes. It opens when it names that revision and
   each change that it names is accepted. It closes when each example is an export copy at that
   revision. No session adds a bullet for one example. An exporter does not start a rebuild before
   the item opens.
3. **Values read from an export graph.** A spec-forced edit can add a value that the session reads
   from the graph of an ONNX file of the exporter of the example. The session reads only the graph,
   with `onnx.load(path, load_external_data=False)`. It does not run the file
   ([ADR-AD33](AD33-bundles-are-untrusted-input.md)). The `edits` item of the `inventory.yaml` entry
   names the value, the file by its path in the exporter repo and its SHA-256. The next export copy
   of the example replaces the value. The entry that supersedes ADR-CRV0 can use this rule for the
   `output_shapes` of `rtmo-body7` and `rtmw-wholebody`.
4. **`needs-export`.** An example needs an export when it needs a value that the change does not
   give and that item 3 cannot give. The session does not edit it. While the item of item 2 is open,
   the content commit of the change waits for the rebuild bundle of that example. After the item
   closes, the part 7 row of the accepted proposal is the request. The exporter packs its `model`
   bundle with `related` set to the proposal bundle when the proposal is accepted, not when it
   lands.
5. **The rules that stay.**
   - KDBD items 5 and 6 (the spec-forced edits, the package-copy clause, the impact run and the
     part 7 table):
     [When a spec change makes an example invalid](../../specs/model-sidecar/model-addition-workflow/reference-examples.md#when-a-spec-change-makes-an-example-invalid)
     and [7. Exporter impact](../../specs/model-sidecar/templates/change-proposal.md#7-exporter-impact).
     Items 3 and 4 change both.
   - The 0009 rules of KDBD item 7:
     [Behaviour](../../specs/model-sidecar/pre/normalization.md#behaviour).
   - KDBD items 1 to 4, the clarification part of item 7 and the legacy rules of 0009 go with
     item 1.

## Reason

- The user, in words (2026-10-30): "I agree with 1 and do not want to keep or maintain any
  backwards compatibility. Nothing has shipped yet, and all exporters will be rebuilt on the new
  spec process once it is finalised here."
- A change class only tells how a change acts on an older spec text. With no older text to keep,
  each class question has one answer.
- The user decided that the re-export requests become one item, and that the CRV0 content lands
  with the `output_shapes` that the current export graphs give. The rebuilt bundles replace them.
- The per-example requests asked exporters to export again while the spec still changes. The
  open-work file of the spec log had 19,797 of 20,000 characters (`check_decision_log.py`).

## Consequences

- Until the rebuild, an example can hold a value that a session read, not one that an exporter
  wrote. Its `edits` item shows it.
- No `model` bundle lands from this entry to the content change that removes the legacy text.
- `intake_bundle.py` refuses a manifest with `change_class`. A packed bundle with it needs a new
  version.

## Alternatives rejected

- **Keep the classes with one class.** The key and part 2.6 then carry no information.
- **Known-invalid examples until the rebuild.** The spec then contradicts its examples.
- **A per-example request with a revision.** Each content commit then edits the open-work file.
