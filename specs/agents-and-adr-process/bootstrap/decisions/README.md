# Decision log

This log records the technical decisions of {{PROJECT}}, with their reasons and evidence. Read this
file and [open-work.md](open-work.md) before you change {{AREAS}} or the agent instructions. Then read
the Active entries that apply to your task. Then you do not repeat a settled question or a completed
measurement. Read a Proposed entry only for work in its section, or when a skill tells you to. Read
an entry of [historical.md](historical.md) only to find the reason for a decision
([0001](0001-decision-log-agents-md-and-private-data.md)).

Each entry gives the decision, its reason, the evidence (when there is evidence), the alternatives
rejected and a "Not repeated" section for pitfalls already found. When a decision changes, add a new
entry that supersedes the old entry in full. The body of a decided entry changes only by the edits
that the [Rules](#rules) allow. To write an entry, use [template.md](template.md).

## Index

### Active

These entries are `accepted` or `evidence`.

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-decision-log-agents-md-and-private-data.md) | Decision log and its rules; `AGENTS.md` files hold the instructions; `plans/` is local; no private data | accepted |

### Proposed

These entries wait for a decision of the user. Section is the section or area of the change, or
`none`.

| # | Decision | Section | Status |
|---|----------|---------|--------|

The entries that are `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
`evidence; used by XXXX` or `done` are in [historical.md](historical.md).

## Open work

The open work is in [open-work.md](open-work.md).

## Rules

- Write one entry for each decision or measurement. Use [template.md](template.md).
- This repo has a root log in `decisions/`. A module can also have a log in `<module>/decisions/`. A
  module is a folder with its own `AGENTS.md`. Each log is in `LOG_DIRS` of
  `tools/check_decision_log.py`. A new module log needs the approval of the user. The PR that adds
  the log also adds its folder to `LOG_DIRS`. These Rules and `template.md` are only in the root log.
  They apply to each log ([ADR-0001](0001-decision-log-agents-md-and-private-data.md)).
- Each module log has three files: `README.md` (an Active table, a Proposed table and
  `## Open work`), `historical.md` and `open-work.md`. The `AGENTS.md` of the module links to its
  log.
- Put an entry in the log of a module only when the module has a log in `LOG_DIRS` and each file that
  its Decision section names or changes is in that module. Put all other entries in the root log
  `decisions/`: an
  entry for two or more modules, for `tools/`, the skills, the root `AGENTS.md`, CI or the repo
  process, and each case that you cannot decide.
- All logs have one ID space. IDs that differ only in case are one ID. "This log" in these Rules
  means all logs of this repo.
- The read path is this file, `open-work.md` and the Active entries that apply to your task. For a
  task in a module, the `README.md`, the `open-work.md` and the Active entries of the module log are
  also in the read path.
- When the scope of a module entry later includes more than one module, a new entry in the root log
  supersedes it.
- Cite an entry of a different log with a relative link and the usual `ADR-<ID>` text. Do not add a
  module name to the ID. A `superseded by XXXX` status can name an entry of a different log. Its
  status line then links to that entry with a relative path.
- The body of an entry that is not `proposed` does not change, except for four edits: a link or
  anchor repair, a typo that does not change the meaning, the redaction of private data, and a
  change of ID with the repair of its citations. Each edit adds `_Edited YYYY-MM-DD (#PR): <kind>._`
  at the end of the entry. `<kind>` is `link repair`, `typo`, `redaction`, `re-ID from XXXX` or
  `citation repair`.
- A `proposed` entry can change until the user decides it.
- When the source of a `proposed` entry changes (for example, another repo changes the proposal that
  the entry records), edit the same entry. Do not add a second entry. Its status line adds
  `recorded again <YYYY-MM-DD> (<source>)`.
- To change a decision, add a new entry. It restates each rule of the old entry that stays, and it
  supersedes the old entry in full. Do not supersede, amend or correct a part of an entry. A link can
  restate a rule. The link must go to a heading of a normative document of the absorb rule below, and
  that heading must state the rule. Then that document is the only source of the rule. The commit
  that changes the text under such a heading cites its own entry next to the changed rule.
- An entry can restate a rule by a link to a heading of a normative document. A later entry can
  change the text under that heading. The later entry cites itself at the heading. It does not
  supersede the linking entry. A later entry that changes a rule that the linking entry states in its
  own text supersedes the linking entry in full.
- The status line of an entry can change. These changes are allowed: `proposed` to `accepted` or
  `rejected`, `accepted` to `superseded by XXXX`, `accepted` to `absorbed into <path>#<anchor>`,
  `absorbed into <path>#<anchor>` to `superseded by XXXX`, `accepted` to `done`, and `evidence` to
  `evidence; used by XXXX`. Each change adds its date and the PR that made it. An absorbed entry is
  superseded when a new entry changes one of its rules. In the same PR, change the status in the
  index and move the row to the table for the new status.
- The tables and their status forms: Active (`accepted`, `evidence`) and Proposed (`proposed`) in this
  file, and Historical (`rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`,
  `evidence; used by XXXX`, `done`) in [historical.md](historical.md). The Status cell has only a
  status form of its table. The Decision cell has 160 characters or fewer.
- A Proposed row has a Section cell: the section or area of the change as an ID in backticks, or
  `none`.
- An `evidence` entry gets `evidence; used by XXXX` when an accepted entry cites it for its decision.
- An accepted entry is absorbed when a normative document states all of its rules. The normative
  documents are the root `AGENTS.md`, the `AGENTS.md` of each module, the skills, the Rules of this
  file with [template.md](template.md), and {{NORMATIVE_DOCS, for example the spec or the contract
  files}}. Then that document is the source of the rules.
- An accepted entry that records a one-off action, with no rule that stays, is `done` when the action
  is complete.
- A consolidation entry states the rules that stay from a group of entries, and it supersedes each
  entry of the group. It changes no decision. Write one when the read-path limit fails.
- Delete an open-work item when the work is done.
- Keep the log inside its limits: 14,000 characters for this file, 20,000 for `open-work.md`, 6,000
  for each entry, and 220,000 for the read path: this file, `open-work.md` and the Active entries.
  The limits of the index, the open work and an entry apply to each file of each log. The read-path
  limit applies to the total of all logs. Proposed and Historical entries are not in the read path.
  Put long evidence in a tracked file next to the entry, and link to it. Run
  `uv run python tools/check_decision_log.py` to see the read-path size and the warnings at 80% of a
  limit. `uv run pytest tools/tests` runs the same check.
- An entry ID has 4 characters from `0123456789ABCDEFGHJKMNPQRSTVWXYZ`. The first character is a
  letter. Write an ID in upper case in each file name, heading, index row and citation. Entry 0001 keeps its number. Do not make a new all-digit ID.
- Before you add an entry, run `git fetch` when you can. Then run
  `uv run python tools/check_decision_log.py --new`. Give the entry the ID of the `new:` line. Create
  its file immediately. Add its index row at the end of the table for its status, in the same PR. The
  index order is the order of addition.
- The pre-push hook runs `--collisions`, the same check without the `new:` line. A `re-ID:` line
  names an entry of this tree whose ID a different file has on another branch or worktree. Both sides
  get the same verdict: an entry on `{{DEFAULT_BRANCH}}` wins, then an entry on a remote-tracking
  branch, then the entry whose first commit has the earlier author date, then the file name that sorts
  first. An ID does not change for a different reason.
- To change an ID, run `--new`. Rename the file to the new ID. Change the ID in its heading and in its
  index row. Find the citations with `git grep -n -E "\bXXXX\b|XXXX-"`, and repair each one. Ask the
  user before you change a PR title or a PR body. If the entry is on `{{DEFAULT_BRANCH}}`, add
  `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._` to it, and a `citation repair` line to each entry on
  `{{DEFAULT_BRANCH}}` that you repair.
- Do not give an ID that an entry had on `{{DEFAULT_BRANCH}}` to a different entry. Do not keep two
  index rows with one ID.
- A tool is code that the repo runs in its normal work: a test, a hook, a CI job, a skill or a
  workflow step calls it, or it writes a tracked file. Each tool is in the root `tools/`. This also
  applies when only one module uses it. A tool has tests.
- A script made the evidence for an entry, or did a one-off job that an entry records, and that entry
  names it. No test, hook, CI job, skill or workflow step runs it on the files of the repo. A script
  does not change after its entry is decided. It is in `scripts/` of the log that holds its entry.
  Its own tests are in `scripts/tests/`. When a later step starts to run a script, move it to
  `tools/` and add a test.
- Cite a tracked file with a relative link. Cite a commit, or the code of another repo, with a GitHub
  permalink that pins a full SHA on the default branch of that repo. Do not cite or link `plans/`.
- Cite an entry of this log as `ADR-<ID>`. Put the prefix in the link text. Write the ID of another
  repo's entry with the repo name and the prefix, for example "{{OTHER_REPO}} ADR-0020". A bare ID is
  always an entry of this log. Do not use the prefix in a file name, a heading, an index row, a
  status line or a YAML value. End each commit subject that adds or changes an entry with
  `(ADR-<ID>)`. Write an ID in YAML front matter in quotes. Cite a provisional
  entry of another repo by the repo name, the PR number and the slug.
- An entry that waits for a decision of another repo has a `**Depends on:**` line under its status
  line.
- {{MIRROR_RULE, or delete this rule: "{{OTHER_REPO}} uses the same rules. Each repo keeps its own
  copy. A change of these rules needs a matching PR in the other repo. No file of one repo imports
  from the other repo."}}
- Write entries in ASD-STE100 Simplified Technical English. Use short sentences, the active voice and
  one instruction in each sentence. "must" is the requirement word. Technical names, field names,
  values, formulas, code and YAML stay unchanged.
