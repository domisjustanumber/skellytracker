# D9VT — Move the decision log to `decisions/` and `specs/model-sidecar/decisions/`

**Status:** accepted, 2026-10-28 (user).

## Decision

This entry supersedes [ADR-K6DZ](k6dz-model-sidecar-folder.md) in full. It restates only the rules
of K6DZ that stay: items 2 to 4 below. Item 6 below replaces K6DZ item 6.

1. **The move.** The log moves from `notes/decisions/` to `decisions/`. The entries 0008 to 0012,
   0017 to 0025 and 0037 to 0048 apply only to the sidecar spec. These 26 entries move to
   [`specs/model-sidecar/decisions/`](../../specs/model-sidecar/decisions/README.md) with their index
   rows and their open work ([ADR-GN3D](GN3D-module-decision-logs.md)). The other entries move to
   `decisions/`. The kit log moves from `specs/agents-and-adr-process/bootstrap/notes/decisions/` to
   `specs/agents-and-adr-process/bootstrap/decisions/`. IDs, file names and statuses do not change.
   So an old path `notes/decisions/<file>` is now `decisions/<file>` or
   `specs/model-sidecar/decisions/<file>`. The old `README.md`, `historical.md` and `open-work.md`
   are split into the files of the two logs. This item is complete when the PR of this entry
   merges.
2. **No stub.** No stub stays at an old path (K6DZ item 1).
3. **References.** Each link and each path in this repo to an old path goes to the new path. A
   decided entry gets only its link repairs and one link-repair `_Edited_` line. A plain-text old
   path in a decided entry stays, because it is history. It means the same file in its new log. The
   same applies to an old path in a tool string and in a comment that a tool writes in a vector file:
   the `notes/decisions/` paths in `tools/make_vectors.py` and in the vector files that it writes
   stay. A text that quotes a path in an exporter repo keeps that path. An exporter repo has its own
   `notes/decisions/`. The same rules apply to the old paths `specs/sidecar/` and
   `specs/sidecar-spec.md` of the spec folder move (K6DZ item 3).
4. **Proposal copies.** A recorded proposal changes each path under `specs/sidecar/` to the same path
   under `specs/model-sidecar/`, and `specs/sidecar-spec.md` to
   `specs/model-sidecar/sidecar-spec.md`. It also changes the path of each file that this move moved
   with no split: the entries, the split checker files and `next_number_timing.py`. A citation of
   the old `notes/decisions/README.md` or `open-work.md` with line numbers stays as written, because
   these files are split. A link gets a link repair only. A new copy of a changed exporter proposal
   makes the same changes. Step 3 of the skill `propose-sidecar-change` gives this copy rule.
5. **Complete items.** K6DZ items 1 and 2 (the move of the spec folder) are complete. K6DZ item 5 (the
   code-citation exception) is complete, and it does not apply again.
   [`tools/tests/test_traceability.py`](../../tools/tests/test_traceability.py) checks the spec path in
   the package code. This move needs no code exception, because no package code file cites the log.
   This entry does not restate these items.
6. **The split checker.** The split checker, its manifest and its test are in
   [`decisions/scripts/`](../scripts/) ([ADR-EY8R](EY8R-tools-and-scripts.md)).
   A moved script runs only at the commit that its entry names:
   [`next_number_timing.py`](../scripts/next_number_timing.py) at the commit of
   [ADR-0032](0032-entry-numbers-and-edits.md), and the split checker at the spec split of
   [ADR-0013](0013-spec-structure.md).

## Reason

- The sidecar spec entries are next to the spec. A task outside the spec does not load them.
- Each log folder has the name `decisions/`, in the root and in a module. So an agent and
  `tools/check_links.py` find each log by one name.
- A move with no change of text can be checked with `git diff -M`. A rewording in the same commit
  cannot.

## Evidence

- [`check_split_verbatim.py`](../scripts/check_split_verbatim.py),
  [`split_manifest.yaml`](../scripts/split_manifest.yaml) and
  [`tests/test_check_split_verbatim.py`](../scripts/tests/test_check_split_verbatim.py) in
  `decisions/scripts/` are the check of the spec split of ADR-0013. They came in the commit "Split
  the sidecar spec into section files". No PR has that commit yet. So this entry cites the commit
  subject and the file paths, not a SHA ([ADR-HJNP](HJNP-upper-case-entry-ids.md) item 6).
- The move commit "Move the decision log to decisions/ and the spec entries to the spec folder" has
  only renames: `git diff -M --stat` (git 2.43.0) shows 76 files changed, 0 insertions and 0
  deletions.

## Alternatives rejected

- **Keep a stub at the old path.** An agent can read the stub as the log. Two folders also make each
  search for an entry give two results.
- **Keep the split checker in `tools/`.** It is a script, not a tool
  ([ADR-EY8R](EY8R-tools-and-scripts.md)).

_Edited 2026-10-29 (this PR): link repair._
