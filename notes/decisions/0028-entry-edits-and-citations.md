# 0028 — Edits to entries, complete supersession, permalinks and the same rules in each repo

**Status:** accepted, 2026-10-24 (user).

## Decision

1. **Allowed edits to the body of an entry.** The body of an entry that is not `proposed` does not
   change, except for these edits:
   - the repair of a link or an anchor after a file or a heading moves;
   - the correction of a typo that does not change the meaning;
   - the redaction of private data.

   Each edit adds a line at the end of the entry: `_Edited YYYY-MM-DD (#PR): <kind>._`. `<kind>` is
   `link repair`, `typo` or `redaction`. Do not use these edits to change a decision, a reason or a
   measurement.
2. **Proposed entries.** A `proposed` entry can change until the user decides it. Its body is frozen
   at `accepted` or `rejected`. A proposal that completes a gap record edits the gap record. It adds
   the parts that the gap record does not have. The status line adds the date and the source, for
   example `completed 2026-11-02 (OpenMMLab-Exporter proposal)`. Do not write a second entry for the
   same gap.
3. **Complete supersession.** An entry that changes a part of an older entry restates each rule of
   the older entry that stays. Then it supersedes the older entry in full. `superseded by NNNN`
   always applies to the full entry. Do not supersede, amend or correct a part of an entry.
4. **Permalinks.** Cite a commit, or the code of another repo, with a GitHub permalink. The permalink
   pins a full 40-character SHA that is on the default branch of that repo:
   `https://github.com/<owner>/<repo>/blob/<sha>/<path>#L<n>`. A range is `#L<n>-L<m>`. A commit of
   this repo that is not on `development` keeps the citation by PR number and file path
   ([0027](0027-single-working-branch.md)). Links inside this repo stay relative.
   `tools/check_links.py` rejects a GitHub `blob`, `tree` or `commit` link in `AGENTS.md`, `notes/`
   and `.claude/skills/` that does not pin a full SHA.
5. **Dependencies on another repo.** An entry that waits for a decision of another repo has a line
   under its status line: `**Depends on:** <repo> NNNN (<status> on YYYY-MM-DD), <permalink>`. No
   tool reads the other repo. When the other decision changes, the user or an agent updates the line.
6. **The same rules in each repo.** skellytracker and OpenMMLab-Exporter use the same decision-log
   rules. Each repo keeps its own copy of the rules and of `check_decision_log.py`. No file, test or
   tool of one repo imports from the other repo. A change of the rules in one repo needs a matching
   PR in the other repo. The entry names its mirror entry in plain text. Mirror: OpenMMLab-Exporter
   0040 (planned).
7. **Consequences.** The entry template has an optional section `## Consequences` after
   `## Reason`. It tells what becomes harder, what must change later and what the decision costs.
8. **No dated status in `AGENTS.md`.** `AGENTS.md` gives instructions. Put a dated fact in the
   [Open work](README.md#open-work) list or in an entry.

## Reason

- The link check fails when a file or a heading moves. The old rule "do not rewrite the body" gave no
  fix for this. OpenMMLab-Exporter repaired a dead link in the body of its entry 0021 with no rule for
  it
  ([commit](https://github.com/domisjustanumber/OpenMMLab-Exporter/commit/6b6a5c57580bdbce34088ebc54a7ba0f130d318c)).
- The repos are public. When an entry contains private data, the current file must not show it. Git
  history keeps the data, so a redaction is not a full fix. But it stops new copies.
- A proposal is a draft. A second entry for each later part makes a chain of entries that a reader
  must join.
- In OpenMMLab-Exporter, nine index rows say that a part of an entry is superseded or amended (0004,
  0006, 0011, 0014, 0018, 0019, 0020, 0025, 0028). To find the current rule, a reader must read two or
  three entries and compare them.
- A short SHA can become ambiguous. A force-push can remove a commit that is not on a default branch.
  A file path and a line number change with each commit. A permalink keeps the commit, the file and
  the line together.
- The two logs started with the same rules ([0001](0001-decision-log-and-agents-md.md),
  OpenMMLab-Exporter 0038). Then they changed separately: OpenMMLab-Exporter has no Active and
  Historical tables, no size limits and no check tool. With an import between the repos, a change in
  one repo can make a test of the other repo fail. Also, an exporter clone can be at a different
  commit.
- Agents read `AGENTS.md` in each session. A dated status line in it goes out of date.

## Consequences

- Old entries keep their citations by short SHA. Only new text uses permalinks.
- A permalink to a private repo does not resolve for a public reader. On 2026-10-24,
  OpenMMLab-Exporter and Roboflow-Exporter are private.
- Each change of the rules costs one PR in each repo.
- No tool finds a `Depends on` line that is out of date.

## Alternatives rejected

- **A new entry for each link repair.** Each moved file adds entries that record no decision.
- **One rules file in skellytracker that OpenMMLab-Exporter links to or imports.** The user rejected
  imports and dependencies between the repos on 2026-10-24.
- **A test that reads the sibling checkout to check the `Depends on` lines.** The same reason.
- **A short SHA with the repo name.** It does not resolve to a file and a line, and it can become
  ambiguous.
