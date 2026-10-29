# 5WKW — Implementation work in the plan

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

This entry supersedes [ADR-B9FM](b9fm-finished-sidecar-plans.md) in full. Items 3 and 4 change rules
of that entry. Item 5 restates its rules that stay.

1. **One list.** The stages M7 to M12 of
   [`specs/sidecar-implementation-plan.md`](../../specs/sidecar-implementation-plan.md) hold the
   implementation-stage work. They take the 18 items of the heading "Implementation stage" of
   [`open-work.md`](../open-work.md), with their text. Their links and entry IDs change to the form
   of the plan. That heading keeps one sentence that points to the plan.
2. **Append only.** The merge adds the stages after M6. It does not change M1 to M6, except M6
   Part B: one sentence now names M8 as the list of the known package gaps, and its link to the old
   open-work heading is gone.
3. **A new item.** A new implementation-stage item, for example part 6 of an accepted proposal,
   goes in the not-started stage that it belongs to. If no stage fits, a new stage goes before the
   release stage. The PR that does an item deletes its bullet and adds one line to the status of its
   stage. This replaces "Delete an open-work item when the work is done" for these items.
4. **The plan stays** until the user decides to delete it. This replaces "until M6 is done".
5. **The rules of the old entry that stay.**
   - The heading "Reference examples" of the plan stays as a "Moved to" stub, because entries,
     proposals and code comments link to it.
   - `notes/sidecar-exporter-coverage.md` is frozen evidence. Only its status lines change, each in
     place.
   - Retire that note at the end of the spec-build stage. Before that, copy its unique measurements
     to an evidence entry. The condition on the entries 0041 and 0042 is gone:
     [ADR-SR1E](SR1E-reset-of-the-spec-build-proposals.md) deleted them.
   The other rules of the old entry were one-off moves. They are complete.
6. **The sources.** [`AGENTS.md`](../../AGENTS.md#1-purpose) section 1, the skills
   `change-sidecar-spec`, `implement-sidecar-section` and `propose-sidecar-change`, phases 2 and 3 of
   the model addition workflow, the change-proposal template and `format.versioning` point to the
   plan.

## Reason

- The user decided on 2026-10-29: the implementation-stage work goes into the plan, and the merge
  only appends stages.
- Two lists of one backlog drift. `open-work.md` is on the read path, and the plan is not. The read
  path gets about 10,000 characters smaller.

## Consequences

- An agent that implements a section reads the plan, not the open work.

## Alternatives rejected

- **Put the items into M6 and M4c.** The user asked to change no existing stage.
- **Keep the items in `open-work.md`.** Two lists stay.
