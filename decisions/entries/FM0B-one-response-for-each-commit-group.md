# FM0B — One response for each commit group, the order of a round and the drift exceptions

**Status:** superseded by [BQZ9](BQZ9-intake-process-consolidation.md), 2026-11-10 (user; PR: pending).

## Decision

1. **One response for each commit group.** At the end of each commit group, after the decisions of
   the user, the session writes one response for each bundle that the group changed. The response
   gives the subject of each commit. A proposal can go from `recorded` to `landed` in one session
   when part 7 has no `needs-export` row. With such a row, the `accepted` response stays: it is the
   trigger of the re-export ([ADR-C0YD](C0YD-the-part-7-row-is-the-re-export-request.md) item 2).
2. **Append-only responses.** The session does not change a response file. A correction is a new
   `r<n>`. A `model` bundle gets a `waiting` response only when its `waiting_on` changes.
3. **The form of a request.** A rebase request is the finding
   `set spec_commit at or after the commit "<subject>"`, never a SHA. The last finding of a
   `needs-contributor` response is the "Next version" list. The response schema does not change.
4. **The order of a round.** The session lands each rule or tool change of the round that changes
   what `verify` or the intake requires before it asks for a new version or a rebase. It lands each
   proposal of a contributor that the user accepted in this round before it answers the `model`
   bundles of that contributor. A `model` bundle whose `waiting_on` blocks its verdict packs its next
   version one time, after each bundle of `waiting_on` is landed.
5. **Named waits.** Each wait names the bundle, its owner and the trigger that ends it.
6. **Drift exceptions.** A drift finding or a `vectors_sha256` mismatch is not `needs-contributor`
   when a landed bundle in `related` or `waiting_on`, or an edit of guidance only, caused it, and the
   example validates at HEAD. The session decides this, and the response says so. A new check that
   tests only the workflow form gives a note for a version packed before its commit. An
   [ADR-AD33](AD33-bundles-are-untrusted-input.md) check never gets this exception. The session
   never changes a record at copy time
   ([Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)).
7. **Tool.** `list` marks a `waiting` model bundle with `waiting_on no longer open` when a bundle of
   its `waiting_on` is finished. The docstring of `list_lines` is the home of this rule. `verify`
   gives no `spec_commit` or version-heading finding when the latest response state is finished.
8. **Changed rule.** Item 7 narrows the `spec_commit` and version-heading findings of
   [ADR-ZXD7](ZXD7-bundle-process.md) item 2 to bundles that are not finished.

Steps 2 and 6 of [Session steps](../../specs/model-sidecar/model-addition-workflow/hand-over.md#session-steps),
[States](../../specs/model-sidecar/model-addition-workflow/hand-over.md#states),
[Responses](../../specs/model-sidecar/model-addition-workflow/hand-over.md#responses) and
[Deferral](../../specs/model-sidecar/model-addition-workflow/hand-over.md#deferral) state items 1 to 6.

## Reason

The YOLOX and RTMW intake sessions of 2026-11-06 to 2026-11-09 wrote 43 responses for 19 bundle
versions:

- The session wrote a response after each commit. Six bundles got `accepted` and `landed` on one
  day. `model-rtmw-wholebody133@openmmlab-exporter` r1 to r3 were all `waiting`.
- `model-yolox-person@openmmlab-exporter` r4 named the SHA of a commit. When later commits of the
  same round landed, the session changed r4 in place to name a newer commit, while the exporter
  rebased on the first SHA. The exporter stopped its workflow and started it again.
- Rules of the same round landed after version 1 of the simcc and model-id-suffix proposal bundles
  was packed. model-id-suffix r2 gives the subject of the
  [ADR-730P](730P-anchor-check-of-bundle-links.md) anchor check. simcc r2 asks for a rebase on the
  [ADR-9HBB](9HBB-simcc-decode-is-2d-only.md) text.
- A handoff review, not the session, found that the
  [ADR-50BW](../../specs/model-sidecar/decisions/entries/50BW-verification-batches.md) commit would
  make the requested repacks fail `verify`.
- The wait on the [ADR-52NQ](../../specs/model-sidecar/decisions/entries/52NQ-model-id-suffix.md)
  and [ADR-SE3Y](../../specs/model-sidecar/decisions/entries/SE3Y-license-and-training-data.md)
  bundles lasted from 2026-11-06 to 2026-11-09. It depended on a contributor with no sidecar commit
  since 2026-10-06.
- yolox r3 said that the `pre.normalize` change needs no new version. r4 asked for version 3 under
  the drift rule. Two of the four drift findings of r4 came only from guidance or comment edits of
  other landed commits. `verify` also gave a drift finding for a bundle after its own landing.

## Consequences

- An excused drift finding is still a `verify` finding. The session run of `batch` stays blocked by
  [ADR-AD33](AD33-bundles-are-untrusted-input.md) item 4.
- A long commit group delays the notice to the contributor.

## Alternatives rejected

- **A `rebase_on` key with a SHA.** A rebase changes SHAs. It also changes the response schema.
- **A fix at copy time, for example to remove `__pycache__`.** A record is a byte copy.
- **Land all open proposals of a contributor first.** A deferred proposal then blocks each model
  answer.
- **A wait rule in `decisions/template.md` or a new open-work heading.** A workflow rule has one home
  ([ADR-ESP4](ESP4-one-home-for-each-workflow-rule.md)).

## Open work

See [open-work.md](../open-work.md).
