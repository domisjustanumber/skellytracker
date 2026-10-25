# Decision log

This log records the technical decisions of {{PROJECT}}, with their reasons and evidence. Read this
file and [open-work.md](open-work.md) before you change {{AREAS}} or the agent instructions. Then read
the Active entries that apply to your task. Then you do not repeat a settled question or a completed
measurement. Read a Deferred entry only for work in its area. Read a Historical entry only to find
the reason for a decision ([0001](0001-decision-log-agents-md-and-private-data.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. When a decision changes, add a new
entry that supersedes the old entry in full. The body of a decided entry changes only by the edits
that the [Rules](#rules) allow.

## Index

### Active

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-decision-log-agents-md-and-private-data.md) | Decision log and its rules; `AGENTS.md` is the single instructions file; `plans/` is local; no private data | accepted |

### Deferred

These entries are `proposed`. The latest date in their status line is more than 183 days old.

| # | Decision | Status |
|---|----------|--------|

### Historical

These entries are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>` or
`evidence; used by XXXX`.

| # | Decision | Status |
|---|----------|--------|

## Open work

The open work is in [open-work.md](open-work.md).

## Rules

- Write one entry for each decision or measurement.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  change of ID with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._`
  at the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `re-ID from XXXX` or
  `citation repair`.
- A `proposed` entry can change until the user decides it.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede, amend or correct a part of an entry.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`, and
  `evidence` to `evidence; used by XXXX`. Each change adds its date and the PR that made it. In the
  same PR, change the status in the index and move the row to the table for the new status.
- The Status cell of an index row has only a status form of its table. The Decision cell has 160
  characters or fewer.
- Move a `proposed` row to Deferred when the latest date in its status line is more than 183 days
  old.
- An `evidence` entry gets `evidence; used by XXXX` when an accepted entry cites it for its decision.
- An accepted entry is absorbed when a normative document states all of its rules. The normative
  documents are `AGENTS.md`, the skills and {{NORMATIVE_DOCS, for example the spec or the contract
  files}}. Then that document is the source of the rules.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one when the read-path limit fails.
- Delete an open-work item when the work is done.
- Keep the log inside its limits: 14,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry, and 220,000 for this file, `open-work.md` and all Active entries together. Put long
  evidence in a tracked file next to the entry, and link to it. Put the script that produced a
  measurement in `notes/decisions/scripts/`. The Evidence section names it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. `uv run pytest tools/tests` runs the same check.
- An entry ID has 4 characters from `0123456789abcdefghjkmnpqrstvwxyz`. The first character is a
  letter. Entry 0001 keeps its number. Do not make a new all-digit ID.
- Before you add an entry, run `git fetch` when you can. Then run
  `uv run python tools/check_decision_log.py --new`. Give the entry the ID of the `new:` line. Create
  its file immediately. Add its index row at the end of the table for its status, in the same PR. The
  index order is the order of addition.
- Run `--new` again before each push. A `re-ID:` line names an entry of this tree whose ID a different
  file has on another branch or worktree. Both sides get the same verdict: an entry on
  `{{DEFAULT_BRANCH}}` wins, then an entry on a remote-tracking branch, then the entry whose first
  commit has the earlier author date, then the file name that sorts first. An ID does not change for a
  different reason.
- To change an ID, run `--new`. Rename the file to the new ID. Change the ID in its heading and in its
  index row. Find the citations with `git grep -n -E "\bXXXX\b|XXXX-"`, and repair each one. Ask the
  user before you change a PR title or a PR body. If the entry is on `{{DEFAULT_BRANCH}}`, add
  `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._` to it, and a `citation repair` line to each entry on
  `{{DEFAULT_BRANCH}}` that you repair.
- Do not give an ID that an entry had on `{{DEFAULT_BRANCH}}` to a different entry. Do not keep two
  index rows with one ID.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo. Do not cite or link `plans/`.
- Write the ID of another repo's entry with the repo name, for example "{{OTHER_REPO}} 0020". A
  bare ID is always an entry of this log. Write an ID in YAML front matter in quotes. Cite a provisional entry of another repo by the repo
  name, the PR number and the slug.
- An entry that waits for a decision of another repo has a `**Depends on:**` line under its status
  line.
- {{MIRROR_RULE, or delete this rule: "{{OTHER_REPO}} uses the same rules. Each repo keeps its own
  copy. A change of these rules needs a matching PR in the other repo. No file of one repo imports
  from the other repo."}}
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names,
  values, formulas, code and YAML stay unchanged.

## Entry template

The file name is `<id>-<short-slug>.md`. Get `<id>` from `--new`.

```markdown
# <id> — <title>

**Status:** <proposed | accepted | evidence>, <YYYY-MM-DD> (<source>).
**Depends on:** <repo> XXXX (<status> on YYYY-MM-DD), <permalink>

## Decision

## Reason

## Consequences

## Evidence

## Alternatives rejected

## Not repeated
```

- **Status.** `accepted` is a decision. `evidence` is a measurement. `proposed` waits for a decision.
  The source says who decided, for example "user".
- **Depends on.** Optional. Write it only when the entry waits for a decision of another repo.
- **Decision.** What is decided, written so that a reader can apply it.
- **Reason.** Why. Each entry gives its own reasons.
- **Consequences.** Optional. What becomes harder, what must change later and what the decision
  costs.
- **Evidence.** Write it only when there is evidence: measurements with their tool, its version and
  the script in `notes/decisions/scripts/`, or code facts with their file and function.
- **Alternatives rejected.** The options that were examined and not used, with the reason for each.
- **Not repeated.** Pitfalls already found.
- Omit an optional section when it has no items. Put open-work items in
  [open-work.md](open-work.md), not in an entry.
