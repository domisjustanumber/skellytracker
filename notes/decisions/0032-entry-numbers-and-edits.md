# 0032 — Entry numbers on parallel branches, allowed edits and evidence scripts

**Status:** accepted, 2026-10-24 (user).

## Decision

This entry supersedes [0028](0028-entry-edits-and-citations.md) in full. It restates items 1 to 5, 7
and 8 of 0028, with a fourth edit in item 1. It drops item 6, the mirror rule. It adds rules for
entry numbers and evidence scripts.

1. **Allowed edits.** The body of an entry that is not `proposed` does not change, except for four
   edits: a link or anchor repair, a typo fix that keeps the meaning, the redaction of private data,
   and a renumber with the repair of its citations. Each edit adds
   `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the entry. `<kind>` is `link repair`, `typo`,
   `redaction`, `renumber from NNNN` or `citation repair`. These edits never change a decision, a
   reason or a measurement.
2. **Proposed entries.** A `proposed` entry can change until the user decides it. A proposal that
   completes a gap record edits the gap record.
3. **Complete supersession.** An entry that changes a part of an older entry restates each rule that
   stays, and supersedes the older entry in full. Do not supersede a part of an entry.
4. **Permalinks.** Cite a commit, or the code of another repo, with a GitHub permalink that pins a
   full 40-character SHA on the default branch of that repo. Cite a commit of this repo that is not on
   `development` by its PR number and file path ([0027](0027-single-working-branch.md)). Links inside
   this repo stay relative.
5. **Dependencies.** An entry that waits for a decision of another repo has the line
   `**Depends on:** <repo> NNNN (<status> on YYYY-MM-DD), <permalink>` under its status line.
6. **Consequences.** The entry template has an optional `## Consequences` section after `## Reason`.
7. **No dated status in `AGENTS.md`.** Put a dated fact in [open-work.md](open-work.md) or in an
   entry.
8. **Entry numbers.**
   - Before you add an entry, run `git fetch --all` and
     `uv run python tools/check_decision_log.py --next`. Use the number of its `next:` line. Create
     the file immediately. Put the index row at the end of the table for its status.
   - `--next` reads this tree, the other worktrees and each local and remote-tracking branch. For each
     entry of this tree whose number a different file has, it prints `keep:` or `renumber:`. The rank:
     on `development` (`TARGET_BRANCH`), then on a remote-tracking branch, then the file name that
     sorts first. Both sides get the same verdict. Refs merged into `HEAD`, and the upstream and push
     refs of the current branch, are not collisions, except on `development`. It exits 1 on a
     `renumber:` line. Run it again before each push.
   - A number is provisional until its entry is on `development`, also while its PR is open. It
     changes only for a `renumber:` line, or when `development` already has the number. This change
     is not an edit. Another repo cites a provisional entry by the repo name, the PR number and the
     slug.
   - If `development` has two entries with one number, renumber the one that merged later, in a new
     PR. The [Rules](README.md#rules) give the `git log` command and the citation search.
   - Gaps are allowed. A number that an entry had on `development` never goes to a different entry.
     A commit message that names an old number can go stale.
   - The check fails on one number in two files or two index rows, on a link text or a `# NNNN`
     heading that is not the file number, and on a `superseded by NNNN` or `used by NNNN` that the
     status line does not link. `renumber from NNNN` keeps the size exemption of NNNN.
9. **Evidence scripts.** Put the script that produced a measurement in `notes/decisions/scripts/`.
   The Evidence section names it.
10. **No mirror rule.** The log rules of this repo do not follow OpenMMLab-Exporter. Do not import a
    file, a test or a tool from another repo. The kit keeps its optional mirror rule.

## Reason

- 0028 gives the reasons for items 1 to 7.
- Two branches or worktrees can take one number. The file names differ, so git shows no conflict.
  The old check keyed entries by file name, so a duplicate passed.
- If both sides get a warning, both take the same new number and collide again. A rank that both
  sides compute gives one `keep:` and one `renumber:`.
- `upstream/development` has no `notes/` folder yet. Without the limit in item 8, each entry could
  move.
- A measurement with its script can be run again.
- This work does not change OpenMMLab-Exporter, so the mirror rule cannot be kept.

## Evidence

- Timing of `--next` (median of 5; git 2.43, Python 3.12, Windows), with
  [`scripts/next_number_timing.py`](scripts/next_number_timing.py):

  | Design | git processes | 104 refs (here) | 302 refs (scratch) |
  |---|---|---|---|
  | One `git ls-tree` for each ref | 2 + refs | 1,333 ms | 3,700 ms |
  | One `git cat-file --batch` (the tool) | 5 | 82 ms | 105 ms |

  A full run of the tool, with the start-up of Python, takes 0.12 to 0.19 s.
- On 2026-10-24, OpenMMLab-Exporter had two different 0040 entries on two branches, and a three-way
  0041 collision: two uncommitted entries in two worktrees and one committed entry on two branches.

## Alternatives rejected

- **Renumber at merge only.** It is silent offline, and a merged duplicate has no repair.
- **Number ranges for each branch.** They need a registry, and the order is lost.
- **A claim commit or a shared `NEXT` file.** Each push needs approval. Identical changes do not
  conflict.
- **Collision-free IDs.** They break `Repo NNNN` citations and the `\d{4}` patterns.

## Not repeated

- `git ls-tree` cannot read several trees: git reads the extra arguments as paths.
- On Windows, decode git output from bytes as UTF-8. Set `GIT_NO_LAZY_FETCH=1`.
- The git tests isolate git from the user config. They count git processes, not wall time.
