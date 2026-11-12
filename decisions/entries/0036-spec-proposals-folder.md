# 0036 — The spec keeps its change proposals in `specs/sidecar/proposals/`

**Status:** superseded by [faac](faac-proposal-records.md), 2026-10-25 (user).

## Decision

1. **Proposal folder.** A skellytracker session records each exporter spec change proposal in
   `specs/sidecar/proposals/<slug>/proposal.md`. `<slug>` is the slug of the proposal. The file is
   informative. It is not normative until a content PR lands its text in the section files.
2. **Content.** `proposal.md` holds the header and all eight parts of the proposal in full. The code
   of part 3 is a `python` code block. The YAML of part 4 is a `yaml` code block. The front matter
   has `slug`, `section`, `exporter`, `decision` and `state`. `state` is `recorded`, `accepted`,
   `landed` or `rejected`.
3. **Copy rules.** A note at the top of the file gives the source: the exporter repo, its commit and
   the date of the copy. The copy changes only these items:
   - a `plans/` path becomes "the untracked <topic> plan of <repo> (plan facts)"
     ([0001](0001-decision-log-and-agents-md.md));
   - private data is redacted ([0030](0030-no-private-data.md));
   - a skellytracker commit that is not on `development` becomes its PR or branch and the file path
     ([0027](0027-single-working-branch.md));
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
   (`supersedes-NNNN.md`), and long evidence (`evidence.md`).
6. **Proposal index.** `specs/sidecar/proposals/README.md` has one row for each proposal: the
   proposal, the section, the exporter, the decision entry and the state.
7. **The decision record.** Each proposed spec change has a short decision entry with the status
   `proposed`. Its title is "NNNN — Spec change: <slug>". Its file is `NNNN-<slug>.md`. Its Decision
   section starts with "**Proposed, not decided.**" and a link to `proposal.md`. Then it gives the
   section, the change, the version, the models, the entries that it supersedes on acceptance, and
   the related proposals. Its Reason gives the gap. Its Evidence gives the parity state. The entry
   limit applies ([0035](0035-decision-log-limits.md)).
8. **Gap records.** A proposal that completes a gap record does not get a new entry. The gap record
   gets the summary and the link of item 7. Its original text moves under Reason. Its status line
   adds `completed <YYYY-MM-DD> (<source>)`.
9. **Supersessions.** If a proposal supersedes an accepted entry on acceptance, the superseding entry
   is also a `proposed` entry now. When its restated rules do not fit the entry limit, the entry
   links to `supersedes-NNNN.md` in the proposal folder.
10. **Open work.** `open-work.md` has one line for each recorded proposal, with a link to its
    "Before acceptance" heading.
11. **Acceptance.** The content PR takes the text, the code and the vectors from `proposal.md`. It
    sets the decision entry to `accepted`, and `state` to `accepted`. The last PR of the proposal
    sets `state` to `landed`. A rejected proposal gets `state: rejected`. Its folder stays.

This entry changes the skills `propose-sidecar-change` and `change-sidecar-spec`, the change proposal
template, phase 3 of the exporter guide and `AGENTS.md`. Rule 2 of the phase 3 workflow of
[0014](0014-spec-lifecycle.md) does not change: a proposal becomes a decision entry with the status
`proposed`.

## Reason

- The skill `propose-sidecar-change` copied all parts of a proposal into the decision entry. The 14
  proposals of OpenMMLab-Exporter and MediaPipe-Exporter (2026-10-25) have 40 KB to 311 KB each. An
  entry after 0025 has a limit of 6,000 characters.
- The exporter files are in `plans/`. Git does not track them, and they change. A tracked copy keeps
  the proposal that the user accepts or rejects.
- The spec owns its change process. The decision log stays a short record of each decision.

## Alternatives rejected

- **A companion folder in `notes/decisions/`.** It mixes the long spec text with the decision log.
- **A summary only.** The landing session then depends on an untracked exporter file.
- **A separate index of `proposed` entries in the log, off the read path.** It changes the read
  path of every agent.
