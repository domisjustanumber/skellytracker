# vac0 — Record a changed exporter proposal again: a new copy and the same entry

**Status:** superseded by [b1c0](b1c0-adr-citation-prefix.md), 2026-10-26 (user; PR: pending).

## Decision

When an exporter changes a spec change proposal after skellytracker recorded it, a skellytracker
session records it again with these rules:

1. **When.** The exporter file of a proposal with `state: recorded` changed after the copy that the
   source note of `proposal.md` gives. Procedure B step 4 of `change-sidecar-spec` stops a landing
   until the new record exists. After `state: accepted`, the copy does not change. The exporter
   writes a new proposal for a new change.
2. **The same entry.** Do not add a second entry. The ID, the slug, the file names and the status
   `proposed` stay.
3. **A new copy.** Replace `proposal.md` in full with a copy of the new exporter file. Replace the
   other exporter files of the folder (for example `evidence.md`) in the same way. The copy rules of
   [faac](faac-proposal-records.md) item 3 apply. The front matter stays. The new source note gives
   the exporter repo, its commit, the date of the new copy and the date of the first copy.
4. **Before acceptance.** Keep each item of the old list, in its order. Tick each item that the new
   version closes, and give the reason after it. Rewrite each item that the new version changes,
   and mark it `(changed <YYYY-MM-DD>)`. Add each new item at the end of its group, and mark it
   `(new <YYYY-MM-DD>)`.
5. **The entry.** Change its Decision, Reason and Evidence only where the new version changes them.
   Add `recorded again <YYYY-MM-DD> (<source>)` to its status line. If the Decision cell or the
   Section cell changes, change the index row in the same PR.
6. **The PR.** A record again is a non-spec PR. The commit subject ends with `(<id>)` of the entry.
7. **The exporter side.** An exporter session that changes a recorded proposal tells the user. A
   skellytracker session then records it again.

The skill `propose-sidecar-change` ("Record a changed proposal"), the exporter guide
(`workflow/phase-3-skellytracker.md`, item 2) and the [Rules](README.md#rules) state these rules.
The bootstrap kit takes the status-line rule in a general form: when the source of a `proposed`
entry changes, edit the same entry and add `recorded again <YYYY-MM-DD> (<source>)`.

## Reason

- On 2026-10-25, MediaPipe-Exporter changed `landmark-extra-outputs` at 13:48, after the record at
  12:24 (0021, `specs/model-sidecar/decisions/0021-landmark-extra-outputs.md`, PR: pending). Procedure B step 4 said "record the new version
  first", but no skill step said how. The skill `propose-sidecar-change` (Step 1 item 3) forbids a
  second entry.
- Each of the 14 recorded proposals has "Before acceptance" items that only the exporter can close.
  Thus each proposal can need a new record before acceptance.
- A full new copy keeps the copy rule "the copy changes only the listed items". Git keeps the old
  copy, so the diff of the PR shows the change of the exporter.
- The ticked and marked items show the reviewer which work is done. A rebuilt list hides it.
- The status-line clause shows the new record in the entry. The index has no other place for it.

## Alternatives rejected

- **A dated second copy next to the first.** Two copies can disagree, and the content PR must take
  the text from one file ([faac](faac-proposal-records.md) item 11).
- **A list of changes after the first copy.** It is not the exporter text, so the copy rules break.
- **A new entry for each version.** It makes chains of entries for one decision. The Rules forbid a
  second entry for the same gap.
- **A rebuilt "Before acceptance" list.** It is shorter, but it loses the record of the closed items.

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._
