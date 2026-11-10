# P3NK — The bootstrap kit moves to freemocap/project; the sync tool stays here

**Status:** absorbed into [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log), [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py), [`tools/tests/test_bootstrap_kit.py`](../../tools/tests/test_bootstrap_kit.py), [`decisions/README.md#rules`](../README.md#rules), 2026-11-10 (user; PR: pending).

## Decision

1. **Kit location.** The bootstrap kit is in `agents-and-adr-process/` of the
   [freemocap/project](https://github.com/freemocap/project) repository. Its `README.md` is the
   guide, `bootstrap/` is the kit for a new repo and `module/` is the module template. The folder
   `specs/agents-and-adr-process/` of this repo is deleted.
2. **Sync tool.** [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py) stays in this
   repo. It is the reference implementation of the kit sync. It finds the kit in the checkout
   `../project`. When this repo is in the `repos/` folder of that checkout, it finds the kit two
   folders up.
3. **No checkout.** When the kit is not there, `--check` prints a note and passes, and `--write`
   fails. The test of the copies skips. The CI of this repo has no project checkout. Thus only a
   local run finds a copy that differs.
4. **Two PRs.** A change of a copied live file or a block runs `--write` in this repo. The changed
   kit files go in a PR to freemocap/project. The PR of this repo links that PR.
5. **Kit tests.** `tests/test_agents_and_adr_kit.py` of freemocap/project holds the three tests that
   read only the kit: the kit decision log, the kit with two module logs, and no placeholders in the
   kit tools. A workflow of that repo runs them on each push and PR.
   [`tools/tests/test_bootstrap_kit.py`](../../tools/tests/test_bootstrap_kit.py) keeps the tests
   of the sync mechanics and of the copies.
6. **Links.** Each decided entry that links to the old folder gets a link repair to a full-SHA
   permalink in freemocap/project. A plain-text path in an older entry stays.

[Section 5](../../AGENTS.md#5-decision-log) states items 1 to 4. The docstring of
`sync_bootstrap_kit.py` states items 2 and 3.

## Reason

- The user, in words: "I would also like to move specs/agents-and-adr-process/ up to
  https://github.com/freemocap/project" and "I'd still like the sync script to exist in
  skellytracker for now, as it's the working reference implementation".
- The kit is guidance for each freemocap repo. It is not a part of skellytracker. freemocap/project
  is the workspace repo of the freemocap repos.
- The sync tool reads the live files of this repo, so it stays next to them.
- On 2026-11-10, the user chose a root folder in freemocap/project, both checkout layouts, the kit
  tests with a workflow in freemocap/project, and a branch and a PR there.

## Consequences

- A change of a copied live file needs one PR in each repo.
- The CI of this repo does not find a kit copy that differs. The doc tests find it in a local run
  when the project checkout is present.
- The kit tests in freemocap/project need no checkout of this repo.
- The permalinks pin a commit of the PR branch in freemocap/project. If the merge gives a different
  SHA, a link repair pins the merged commit.

## Alternatives rejected

- **Move the sync tool with the kit.** In freemocap/project, the tool would need a checkout of this
  repo to read the live files. The user wants the reference implementation to stay here.
- **Clone freemocap/project in the CI of this repo.** Each PR here that changes a live file would
  then fail until the PR in freemocap/project merges.
- **`agent-guidance/` of freemocap/project.** The user chose a root folder.
