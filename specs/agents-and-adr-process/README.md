# Bootstrap a new repo: `AGENTS.md` and the decision log

This guide is for a coding agent that creates a new repo, or adds agent instructions and a decision
log to a repo that has none. It gives a procedure, the rules and their reasons, and a kit of files
to copy. The kit is in [`bootstrap/`](bootstrap/). Its folders have the layout of the new repo, so
each file goes to the same relative path.

The rules come from the skellytracker decision log:
[ADR-GN3D](../../decisions/GN3D-module-decision-logs.md),
[ADR-Z934](../../decisions/z934-decision-log-index-and-read-path.md),
[ADR-JW9N](../../decisions/JW9N-restate-a-kept-rule-by-a-link.md),
[ADR-FDTD](../../decisions/FDTD-evidence-sources-and-exporter-permalinks.md),
[ADR-P3N3](../../decisions/p3n3-ai-attribution-warning.md) and
[ADR-EY8R](../../decisions/EY8R-tools-and-scripts.md). The kit has their final form. It does
not have their history.

## What the kit gives

| Kit file | Copy to | Action |
|---|---|---|
| [`AGENTS.md`](bootstrap/AGENTS.md) | `AGENTS.md` | Fill in each `{{...}}` |
| [`CLAUDE.md`](bootstrap/CLAUDE.md) | `CLAUDE.md` | Copy. Its only content is `@AGENTS.md`. |
| [`decisions/README.md`](bootstrap/decisions/README.md) | the same path | Fill in each `{{...}}` |
| [`decisions/historical.md`](bootstrap/decisions/historical.md), [`decisions/template.md`](bootstrap/decisions/template.md) | the same paths | Copy |
| [`decisions/open-work.md`](bootstrap/decisions/open-work.md) | the same path | Replace the example item, or delete it |
| [`decisions/0001-…`](bootstrap/decisions/0001-decision-log-agents-md-and-private-data.md) | the same path | Fill in the date |
| `tools/check_decision_log.py`, `tools/check_links.py`, `tools/check_private_data.py`, `tools/check_ai_attribution.py` | the same paths | Copy. Add the public contact address of the project to `ALLOWED_EMAILS`. |
| `tools/tests/conftest.py` and the four `test_*.py` files | the same paths | Copy |
| `.pre-commit-config.yaml`, `.gitleaks.toml` | the same paths | Copy |
| `.github/workflows/secrets.yml`, `.github/workflows/doc-checks.yml` | the same paths | Copy. In `secrets.yml`, change `branches: [main]` if PRs target a different branch. |
| [`gitignore-additions.txt`](bootstrap/gitignore-additions.txt) | `.gitignore` | Append the lines. Do not copy the file as `.gitignore`. |
| [`module/`](module/AGENTS.md): `AGENTS.md`, `CLAUDE.md`, `decisions/README.md`, `decisions/historical.md`, `decisions/open-work.md` | each module folder, for example `freemocap/` | Only for a repo with modules ([Modules and logs](#modules-and-logs)). Fill in each `{{...}}`. In `decisions/open-work.md`, replace the example item, or delete it. |

The module template is in [`module/`](module/), not in `bootstrap/`, because it goes into a module
folder, not into the repo root.

The four tools use only the Python standard library and the git CLI. They count the decision log,
check the links, scan the tracked files and check the commit message for AI attribution. Their tests
run with `pytest`.

## Procedure

### Step 1: Ask the user

Ask these questions before you copy a file. Stop until the user answers. Use the default only when
the user tells you to.

1. Is the repo public now, or can it become public? Default: yes. The private-data rule applies in
   both cases.
2. Which branch do PRs target? Default: `main`. The kit calls it `{{DEFAULT_BRANCH}}`.
3. Which kinds of change go in separate PRs? Default: code, docs and CI.
4. Which documents are normative, in addition to `AGENTS.md` and the skills? Examples: a spec, a
   contract file, an API reference. An entry is absorbed only when a normative document states all
   of its rules.
5. Does a sibling repo use the same decision-log rules? If yes, keep the mirror rule. If no, delete
   it.
6. Must the docs use ASD-STE100 Simplified Technical English? Default: yes. If no, delete the STE
   rule from `AGENTS.md` and from the index rules.
7. May the agent push to a remote without asking each time? Default: no.
8. Does the repo have modules, for example `freemocap/` and `freemocap-ui/`? Default: no. A module is
   a folder with its own `AGENTS.md`. The kit also gives each module a decision log. A yes is the
   approval of the user for each of these module logs ([Modules and logs](#modules-and-logs)).

### Step 2: Copy the files

Copy each file of the table above. Keep the dot files: `.pre-commit-config.yaml`, `.gitleaks.toml`
and `.github/`. With a local checkout of skellytracker, for example:

```sh
KIT=../skellytracker/specs/agents-and-adr-process/bootstrap
cp -r "$KIT"/. .
rm gitignore-additions.txt
cat "$KIT/gitignore-additions.txt" >> .gitignore
```

Read each copied file before you change it.

If the repo has modules (question 8), do these steps for each module, for example `freemocap/`:

1. Copy the module template into the module folder. `cp -n` keeps a file that is already there.

   ```sh
   cp -rn "$KIT/../module/." freemocap/
   ```

2. Change each code span that holds `{{ROOT}}` to a relative link, so that `tools/check_links.py`
   checks it. Then replace `{{ROOT}}` with the relative path from the module folder to the repo
   root, for example `../`. Use the same value in all module files: the files in `decisions/`
   already have one more `../`. Then replace `{{MODULE}}` with the folder name. For example, in
   `freemocap/AGENTS.md`, `` `{{ROOT}}decisions/README.md#rules` `` becomes
   `[root Rules](../decisions/README.md#rules)`.
3. Replace `{{MODULE_RULES}}` with the rules that apply only to the module. Move these rules out of
   the root `AGENTS.md`.
4. If the module already had an `AGENTS.md`, merge the kit text into it by hand. The `CLAUDE.md` of
   the module must contain only `@AGENTS.md`.
5. Add the folder of the module log to `LOG_DIRS` in `tools/check_decision_log.py`, for example
   `LOG_DIRS = (LOG_DIR, Path("freemocap/decisions"), Path("freemocap-ui/decisions"))`.
6. Fill in the `{{MODULE}}/` row of the table in section 1 of the root `AGENTS.md`, with one row for
   each module.

If the repo has no modules, delete the `{{MODULE}}/` row of that table.

### Step 3: Fill in the placeholders

Each `{{NAME}}` is a placeholder. Replace it with the answer of the user or with project facts. When
a placeholder is a rule that does not apply, delete the full line. Then run:

```sh
grep -rn "{{" AGENTS.md CLAUDE.md decisions/ tools/
```

For a repo with modules, add the `AGENTS.md`, the `CLAUDE.md` and the `decisions/` folder of each
module to the command, for example:

```sh
grep -rn "{{" AGENTS.md CLAUDE.md decisions/ tools/ \
  freemocap/AGENTS.md freemocap/CLAUDE.md freemocap/decisions/ \
  freemocap-ui/AGENTS.md freemocap-ui/CLAUDE.md freemocap-ui/decisions/
```

The command must find nothing.

Then set `TARGET_BRANCH` in `tools/check_decision_log.py` to the branch that PRs target
(question 2). `--new` uses it to rank entry IDs.

### Step 4: Add the tools to the project

For a Python project with `uv`, add this to `pyproject.toml`, and run `uv sync`:

```toml
[dependency-groups]
dev = ["pytest", "pre-commit==<version>"]

[tool.pytest.ini_options]
testpaths = ["tools/tests"]   # add the other test folders of the project
```

Pin `pre-commit` to a release that is at least 14 days old. Check the date on PyPI. For a project
that does not use Python, install Python 3.10 or later and `pytest` for the doc checks only. Then
change each `uv run` command in `AGENTS.md`, `.pre-commit-config.yaml` and `doc-checks.yml`.

### Step 5: Check

Run each command. Each one must pass.

```sh
uv run pytest tools/tests
uv run python tools/check_decision_log.py
uv run python tools/check_decision_log.py --new
uv run python tools/check_private_data.py
uv run pre-commit install
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
git check-ignore -v plans/x .private-terms .claude/settings.local.json
```

The first `pre-commit` run downloads Go to build `gitleaks`. This can take some minutes.

### Step 6: Tell the user about the GitHub settings

These settings are outside the repo. Tell the user. Change them only with the approval of the user.

- **Secret scanning and push protection.** Repo, Settings, Advanced Security. They are free for a
  public repo. A private repo does not get them free. Turn them on the day the repo becomes public.
  An organization repo needs an organization admin.
- **A private commit email.** GitHub, Settings, Emails: "Keep my email addresses private". Then set
  `git config --global user.email` to the `noreply` address that the page shows.
- **"Block command line pushes that expose my email".** Turn it on only after each open branch is
  merged. A rebase makes new commits that keep the old author email, and GitHub then rejects the
  force-push.
- **Optional: required checks on up-to-date branches.** A branch rule on `{{DEFAULT_BRANCH}}` can
  require the doc checks, and require each branch to be up to date before the merge. This needs a
  public repo or a paid plan. Without it, three things find a duplicate entry number: the conflict
  in the index, the PR check after the conflict is resolved, and the push check on
  `{{DEFAULT_BRANCH}}`.
  Use a merge queue only in a repo that an organization owns. `doc-checks.yml` has a `merge_group:`
  trigger for it.

### Step 7: Commit and stop

Put the kit in one commit, in one docs PR. Do not push without the approval of the user.

## How to write `AGENTS.md`

- **One file.** The root `AGENTS.md` is the instructions file for all agents. A module adds its own
  `AGENTS.md` ([Modules and logs](#modules-and-logs)). Each `CLAUDE.md` only imports the `AGENTS.md`
  in its folder. Two instruction files for one folder go out of date in different ways and then
  disagree.
- **Instructions only.** Write what an agent must do. Do not write a dated status ("On 2026-10-22,
  the workflow fails"). Put a dated fact in `open-work.md` or in an entry.
- **Short reasons.** Give the reason of a rule in its decision entry. Link to the entry from
  `AGENTS.md`.
- **One instruction in each sentence.** Use "must" for a requirement.
- **Sections.** Keep the eight sections of the root template. Add project sections after section 4.
  Do not renumber a section: other files link to its anchor.
- **Skills.** Put a long procedure in a skill (`.claude/skills/<skill>/SKILL.md`). An agent loads it
  only for its task. `AGENTS.md` lists each skill and when to use it.
- **Permission summaries.** Before a tool call that needs permission, the agent writes one line that
  tells what the call does and what it changes.

## How to run the decision log

### When to write an entry

- Write one entry for each decision or measurement that code, a document or a later task depends
  on.
- Write it in the same PR as the change that applies it.
- Do not write an entry for a fact that the code or the git history already shows.

### Status and tables

The index (`README.md`) has the Active and Proposed tables. `historical.md` has the Historical
table, and `template.md` has the entry template. An agent reads the index, `open-work.md` and the
Active entries that apply to its task. These files are the read path. It reads a Proposed entry only
for work in its section, and a Historical entry only to find the reason for a decision.

| Table | File | Status forms |
|---|---|---|
| Active | `README.md` | `accepted`, `evidence` |
| Proposed | `README.md` | `proposed`. The row also has a Section cell: an ID in backticks, or `none`. |
| Historical | `historical.md` | `evidence; used by XXXX`, `rejected`, `superseded by XXXX`, `absorbed into <path>#<anchor>`, `done` |

`done` is for an accepted entry that records a one-off action, with no rule that stays.

In skellytracker, the `proposed` entries held more than a third of the read path. One batch of
proposals added about 76,000 characters. A `proposed` entry is not a rule yet, so it is off the read
path. A table of old proposals ("Deferred") is not necessary when no proposal is on the read path.

The Status cell has only the status form. Free text in that cell grows. In OpenMMLab-Exporter, one
cell named five other entries.

### Edits

- A `proposed` entry can change until the user decides it.
- When the source of a `proposed` entry changes, edit the same entry, and add
  `recorded again <YYYY-MM-DD> (<source>)` to its status line. The source can be a new version of
  the proposal. A second entry for one proposal makes a chain of entries for one decision
  ([ADR-FADS](../../decisions/FADS-hand-over-bundles-in-intakes.md)).
- The body of a decided entry changes only for a link repair, a typo fix, a redaction, or a change of
  ID with the repair of its citations. Each edit adds a dated `_Edited_` line.
- A status line can change. Write the date and the PR. An absorbed entry can also change to
  `superseded by XXXX` when a new entry changes one of its rules
  ([ADR-JW9N](../../decisions/JW9N-restate-a-kept-rule-by-a-link.md)).

### IDs and parallel work

Two branches or worktrees can read the same index and take the same next number. The file names
differ, so git shows no conflict. In OpenMMLab-Exporter, two different entries had the number 0040,
and three entries had the number 0041. A renumber then moved seven entries. So an entry gets a
random ID, not the next number.

- An ID has 4 characters from `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (Crockford base32, upper case). The
  first character is a letter. An upper-case ID does not look like a word in prose, in `git log` or in
  a PR title. The tool compares IDs without case. The kit entry 0001 keeps its number. Do not make a new all-digit ID.
- Before you add an entry, run `git fetch` when you can. Then run
  `uv run python tools/check_decision_log.py --new`. It prints `new: XXXX`, a random ID that is not
  in this tree, in another worktree or on a local or remote-tracking branch. Give the entry that ID.
  Create its file immediately.
- Put the index row at the end of the table for its status. Then two parallel entries make a git
  conflict in the index. The index order is the order of addition.
- The pre-push hook runs `--collisions` before each push. `--collisions` is `--new` without the
  `new:` line. It prints `keep:` or `re-ID:` for each entry of this tree whose ID a different file
  has. Both sides get the same verdict: an entry on `TARGET_BRANCH` wins,
  then an entry on a remote-tracking branch, then the entry whose first commit has the earlier author
  date, then the file name that sorts first. An uncommitted file loses. The command exits 1 when it
  prints a `re-ID:` line, and the hook then stops the push.
  `.pre-commit-config.yaml` sets `default_install_hook_types: [pre-commit, commit-msg, pre-push]`
  and `default_stages: [pre-commit]`. Without `default_stages`, the commit hooks also run on each
  push.
- Refs that are merged into `HEAD`, the upstream and push refs of the current branch, and local
  branches under `backup/` are not collisions. A file whose slug an entry of this tree has under a
  different ID is an old name of that entry, not a collision.
- A change of ID is the fourth allowed edit. The entry gets `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._`
  when it is already on the target branch. Each repaired entry on the target branch gets a
  `citation repair` line. An ID that an entry had on the target branch never goes to a different
  entry.
- `--new` runs 5 git processes for any number of refs, and one more when it finds a collision. The
  normal check reads only the files. It fails on a file name with an ID that is not valid, on two
  files or two index rows with one ID, on a link text that does not match its file, on a heading that
  does not match its file name, and on a `superseded by XXXX` cell that does not match the link in the
  status line.

### Supersession and consolidation

- A new entry that changes an old decision restates each rule that stays. Then it supersedes the old
  entry in full.
- A link to a heading of a normative document can restate a rule, when that heading states the rule.
  Some absorbed entries are larger than the entry limit, so a full restatement cannot pass the check.
  A later entry can change the text under that heading. It cites itself at the heading, and it does
  not supersede the linking entry. A later entry that changes a rule that the linking entry states in
  its own text supersedes the linking entry in full
  ([ADR-JW9N](../../decisions/JW9N-restate-a-kept-rule-by-a-link.md)).
- Do not supersede a part of an entry. OpenMMLab-Exporter had nine partly superseded entries. It
  needed six consolidation entries to repair them.
- A consolidation entry states the rules that stay from a group of entries and supersedes them. It
  changes no decision. Write one when the read-path limit fails.

### Absorption

An accepted entry is absorbed when a normative document states all of its rules. The entry then goes
to Historical, and the document is the source of the rules. Decide at the start which documents are
normative (Step 1, question 4). In the first review in skellytracker, only 2 of 15 entries were
absorbed, because many rules were only in a guide that was not normative. The Rules of the log
`README.md` and `template.md` are also normative, so an entry about the log rules can be absorbed
into them.

### Limits

`tools/check_decision_log.py` checks these limits and prints a warning at 80%.

| Limit | Characters |
|---|---|
| Index (`README.md`) | 14,000 |
| `open-work.md` | 20,000 |
| Each entry | 6,000 |
| Read path | 220,000 |

About 4 characters make one token. Put long evidence in a tracked file next to the entry, and link
to it. Put the script that produced a measurement in `scripts/` of the log that holds its entry.
Name the script in the Evidence section. Then a reader can run the measurement again. A PR that
raises a limit must add an entry. To start the log in a repo that already has long entries, set
`LAST_UNLIMITED_ENTRY` to the highest old entry number.

### Citations

- Link a tracked file with a relative link.
- Cite a commit, or the code of another repo, with a GitHub permalink that pins a full SHA on the
  default branch of that repo. A short SHA can become ambiguous. A force-push can remove a commit
  that is not on a default branch.
- Do not cite or link `plans/`.
- Cite an entry as `ADR-<ID>`, with the prefix in the link text. Write the repo name before the
  entry ID of another repo, for example "skellytracker ADR-0028". A bare 4-character ID is not clear
  in plain text, and `git log` shows no links. Commit subjects end with `(ADR-<ID>)`.

### Modules and logs

A repo can have modules, for example a server in `freemocap/` and a UI in `freemocap-ui/`. Each
module has its own `AGENTS.md` and its own decision log in `<module>/decisions/`. The root log in
`decisions/` holds the Rules, the template and each decision that is not for one module only
([ADR-GN3D](../../decisions/GN3D-module-decision-logs.md)).

- **Reason.** A task in one module does not load the decisions of the other modules. A UI task does
  not load the server decisions. The agent reads the root log and the log of its module.
- **Placement.** An entry goes in the log of a module only when each file that its Decision section
  names or changes is in that module. All other entries go in the root log. When you cannot decide,
  use the root log.
- **A fixed list.** `LOG_DIRS` in `tools/check_decision_log.py` lists each log. The tool does not
  search for logs, so a test copy of a log does not become a log. A new module log needs the
  approval of the user. The PR that adds a module log adds its folder to `LOG_DIRS`.
- **One ID space.** An ID is unique in all logs of the repo. A citation needs no module name, and an
  entry can move to a different log with no change of ID.
- **Limits.** The limits of the index, the open work and an entry apply to each file. The read-path
  limit applies to the total of all logs.
- **Tools and scripts.** A tool is code that the repo runs in its normal work. Each tool is in the
  root `tools/`. This also applies when only one module uses it. A script made the evidence for an
  entry, or did a one-off job that the entry records. It is in `scripts/` of the log that holds its
  entry ([ADR-EY8R](../../decisions/EY8R-tools-and-scripts.md)).
- **Packages.** A module that is also a package can ship its `decisions/` folder in the wheel or the
  package. Check the build config. Exclude the folder when the package must not contain it.
- **Older kit copies.** A repo that copied an older kit keeps its log where it is. This guide does
  not migrate it. A move of that log needs an entry and a PR in that repo.

### Repos that share the rules

Each repo keeps its own copy of the rules and of the tools. Do not import a file, a test or a tool
from another repo: a change in one repo then makes a test of the other repo fail. A change of the
rules needs one PR in each repo. Each entry names its mirror entry in plain text.

## Private data

The rule is in section 8 of [`AGENTS.md`](bootstrap/AGENTS.md#8-private-data). Three tools enforce
it:

- `tools/check_private_data.py` finds user-folder paths, email addresses, private IP addresses,
  tokens and the terms of the untracked file `.private-terms`. It skips lock files, because they
  hold four-part versions that look like IP addresses.
- The `gitleaks` pre-commit hook scans each commit before it is made.
- The `secrets.yml` workflow scans the history on each push. It downloads the pinned `gitleaks`
  binary and checks its SHA-256. Do not use `gitleaks-action`: it needs a license key for an
  organization repo.

Before a private repo becomes public, scan all of its history:

```sh
gitleaks git --log-opts="--all" --redact .
```

## When to add a test

Each test checks one named claim. Add a test in these cases:

- a bug fix, or a review finding that shows a defect: write the regression test first;
- a validation rule of a spec or a contract: one test for each rule ID that checks the rejection;
- a new component, model or config file: the tests that its kind needs, in the same PR;
- a new tool or check: its tests in the same PR;
- a known defect that waits for later work: a strict `xfail` test, if the rules of the project allow
  it, so that the fix makes the test pass;
- a decision rule or a "Not repeated" pitfall: only when code or a tool can check it.

Do not use a coverage percentage as a trigger or a gate. Report it. Give each CI job a
`timeout-minutes`, so that a hang does not run for hours.

## Lessons from skellytracker and OpenMMLab-Exporter

These pitfalls are already found. Do not repeat them.

- Git ignores `plans/` only from the commit that adds the rule. Files that were committed before
  that stay in the history. Add the ignore rule in the first commit.
- Agents paste command output into entries. The output can hold user paths, host names and
  environment values. The private-data check finds most of them.
- A tracked list of private terms publishes the terms. Keep `.private-terms` untracked.
- A per-entry warning at 80% is noise. A decided entry cannot become shorter. The tool warns only for
  the index, the open work and the read path.
- An index limit of 10,000 characters was too small: an index with about 30 rows, its rules and its
  template already has 10,000. The limit is 14,000. The Historical rows and the template are now in
  their own files, off the read path.
- A dated status line in `AGENTS.md` said that a PR was open after it was merged.
- A rule for a "gap record" that a later proposal extends with a second entry made chains of
  entries. The kit lets a `proposed` entry change instead.
- The newest release of a tool can be too new to trust. Pin versions that are at least 14 days old.

## Keep the kit current

This section is for the maintainers of skellytracker
([0031](../../decisions/0031-bootstrap-kit.md)). The tool and config files in `bootstrap/` are
copies of the live files of skellytracker, with exact text edits that remove the parts that belong
only to skellytracker. [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py) holds the
list of copies and edits. When you change a live tool or config:

1. Run `uv run python tools/sync_bootstrap_kit.py --write`.
2. Commit the live file and the copy in the same PR.

`uv run pytest tools/tests` runs `--check`. It also runs the copied decision-log check on the kit,
so the kit log must stay valid. A second test copies `module/` into the kit as two modules, fills in
`{{ROOT}}` and `{{MODULE}}`, and runs the kit checks on the result. The other kit files
(`AGENTS.md`, `CLAUDE.md`, the decision log, `gitignore-additions.txt`, `doc-checks.yml` and the
files in `module/`) are templates. Change them by hand when a rule of the skellytracker log changes.
