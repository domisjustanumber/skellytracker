# faac — Spec change proposals: the proposal folder, with no open-work line for each proposal

**Status:** absorbed into [`propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder`](../../.claude/skills/propose-sidecar-change/SKILL.md#step-3-copy-the-proposal-into-the-spec-folder), 2026-10-25 (user; the absorption review); superseded by [FADS](FADS-hand-over-bundles-in-intakes.md), 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [0036](0036-spec-proposals-folder.md) in full. It restates items 1 to 9 and 11
of 0036. It replaces item 10. 0036 keeps the reasons for the rules that stay.

1. **Proposal folder.** A skellytracker session records each exporter spec change proposal in
   `specs/sidecar/proposals/<slug>/proposal.md`. `<slug>` is the slug of the proposal. The file is
   informative. It is not normative until a content PR lands its text in the section files.
2. **Content.** `proposal.md` holds the header and all eight parts of the proposal in full. The code
   of part 3 is a `python` code block. The YAML of part 4 is a `yaml` code block. The front matter
   has `slug`, `section`, `exporter`, `decision` and `state`. `state` is `recorded`, `accepted`,
   `landed` or `rejected`.
3. **Copy rules.** A note at the top of the file gives the source: the exporter repo, its commit and
   the date of the copy. The copy changes only these items:
   - a `plans/` path becomes "the untracked <topic> plan of <repo> (plan facts)";
   - private data is redacted;
   - a skellytracker commit that is not on `development` becomes its PR or branch and the file path;
   - a path of an exporter with no git repo stays as it is. The source note says one time that the
     exporter has no git repo and that its paths are not pinned;
   - a relative link that does not resolve in skellytracker becomes a code span.

   The session does not write a missing part. It does not correct the text of a part.
4. **Before acceptance.** The last heading of `proposal.md` is "Before acceptance". It lists the work
   that must be done before the user can accept the proposal: each failed item of the template
   checklist "Before you stop", the missing primary evidence, each `to run` result and each open
   question of the session.
5. **Other files.** The folder can also hold long text that belongs to the proposal: draft text of
   an entry that the proposal supersedes on acceptance, when the entry limit cannot hold it
   (`supersedes-<id>.md`), and long evidence (`evidence.md`).
6. **Proposal index.** [`specs/model-sidecar/proposals/README.md`](../../specs/model-sidecar/proposals/README.md)
   has one row for each proposal: the proposal, the section, the exporter, the decision entry and the
   state.
7. **The decision record.** Each proposed spec change has a short decision entry with the status
   `proposed`. Its title is "<id> — Spec change: <slug>". Its file is `<id>-<slug>.md`. Its Decision
   section starts with "**Proposed, not decided.**" and a link to `proposal.md`. Then it gives the
   section, the change, the version, the models, the entries that it supersedes on acceptance, and
   the related proposals. Its Reason gives the gap. Its Evidence gives the parity state. The entry
   limit applies ([z934](z934-decision-log-index-and-read-path.md)).
8. **Gap records.** A proposal that completes a gap record does not get a new entry. The gap record
   gets the summary and the link of item 7. Its original text moves under Reason. Its status line
   adds `completed <YYYY-MM-DD> (<source>)`.
9. **Supersessions.** If a proposal supersedes an accepted entry on acceptance, the superseding entry
   is also a `proposed` entry now. When its restated rules do not fit the entry limit, the entry
   links to `supersedes-<id>.md` in the proposal folder.
10. **No open-work line.** `open-work.md` has no line for each recorded proposal. The proposal index
    is the list of the proposals: a proposal with `state: recorded` waits for the user. Its
    "Before acceptance" heading lists its open work. When the content PR lands part 6 of a proposal,
    the implementer guidance gets an open-work item, as before.
11. **Acceptance.** The content PR takes the text, the code and the vectors from `proposal.md`. It
    sets the decision entry to `accepted`, and `state` to `accepted`. The last PR of the proposal
    sets `state` to `landed`. A rejected proposal gets `state: rejected`. Its folder stays.

This entry changes the skills `propose-sidecar-change` and `change-sidecar-spec`, the proposal index
and `open-work.md`. Rule 2 of the phase 3 workflow of [0014](0014-spec-lifecycle.md) does not change:
a proposal becomes a decision entry with the status `proposed`.

## Reason

- On 2026-10-25, `open-work.md` was 18,272 of 20,000 characters (91%). The section "Proposals before
  acceptance" held 14 lines, about 2,700 characters. Each later batch of proposals adds one line for
  each proposal, so the next batch would fail the limit.
- Each line repeats the proposal index: the slug, the decision entry and a link to `proposal.md`. The
  index already has the `state`, and `proposal.md` has the "Before acceptance" heading.

## Alternatives rejected

- **A higher limit for `open-work.md`.** It moves the failure to a later batch.
- **One line for all proposals.** It is a pointer to the proposal index, which the skills already
  name.

_Edited 2026-10-26 (this PR): link repair._

_Edited 2026-10-28 (this PR): link repair._

_Edited 2026-10-29 (this PR): link repair._
