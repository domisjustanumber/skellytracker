# gtwq — Random entry IDs, allowed edits and evidence scripts

**Status:** absorbed into [`decisions/README.md#rules`](README.md#rules), 2026-10-25 (user).

## Decision

This entry supersedes [0032](0032-entry-numbers-and-edits.md) in full. It restates items 1 to 7, 9
and 10 of 0032. It replaces item 8, the entry numbers, with random IDs. 0032 keeps the reasons for
the rules that stay.

1. **Allowed edits.** The body of an entry that is not `proposed` does not change, except for four
   edits: a link or anchor repair, a typo fix that keeps the meaning, the redaction of private data,
   and a change of ID with the repair of its citations. Each edit adds
   `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the entry. `<kind>` is `link repair`, `typo`,
   `redaction`, `re-ID from XXXX` or `citation repair`. An old `renumber from NNNN` line stays.
2. **Proposed entries.** A `proposed` entry can change until the user decides it. A proposal that
   completes a gap record edits the gap record.
3. **Complete supersession.** An entry that changes a part of an older entry restates each rule that
   stays, and supersedes the older entry in full.
4. **Permalinks.** Cite a commit, or the code of another repo, with a GitHub permalink that pins a
   full 40-character SHA on the default branch of that repo. Cite a commit of this repo that is not on
   `development` by its PR number and file path. Links inside this repo stay relative.
5. **Dependencies.** An entry that waits for a decision of another repo has the line
   `**Depends on:** <repo> XXXX (<status> on YYYY-MM-DD), <permalink>` under its status line.
6. **Consequences.** The entry template has an optional `## Consequences` section after `## Reason`.
7. **No dated status in `AGENTS.md`.** Put a dated fact in [open-work.md](open-work.md) or in an
   entry.
8. **Entry IDs.**
   - An ID has 4 characters from `0123456789abcdefghjkmnpqrstvwxyz` (Crockford base32, lower case).
     The first character of a new ID is a letter. The file is `<id>-<slug>.md`. The heading is
     `# <id> — <title>`.
   - The entries 0001 to 0048 keep their numbers. Each all-digit ID belongs only to an entry that had
     it before this entry. Do not make a new all-digit ID.
   - Before you add an entry, run `uv run python tools/check_decision_log.py --new`. Use the ID of its
     `new:` line. It is random, and it is not in this tree, in another worktree or on a local or
     remote-tracking branch. Run `git fetch --all` first when you can.
   - An ID does not change, except for a collision. `--new` prints `keep:` or `re-ID:` for each entry
     of this tree whose ID a different file has. Both sides get the same verdict. The rank: on
     `development`, then on a remote-tracking branch, then the earlier author date of the first
     commit, then the file name that sorts first. An uncommitted file loses to a committed file. It
     exits 1 on a `re-ID:` line. Run it again before each push.
   - These are not collisions: refs merged into `HEAD`, the upstream and push refs of the current
     branch, local branches under `backup/`, and a file whose slug an entry of this tree has under a
     different ID (an old name).
   - On a `re-ID:` line, run `--new`. Rename the file, its heading and its index row. Repair each
     citation. Ask the user before you change a PR title or a PR body. If the entry is on
     `development`, add `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._`.
   - Do not give an ID that an entry had on `development` to a different entry. The index keeps its
     rows in the order of addition. The order of the IDs means nothing.
   - Write another repo's entry with the repo name, for example "OpenMMLab-Exporter 0020". A bare ID
     is an entry of this log. Commit subjects end with `(<id>)`.
   - Write an ID in YAML front matter in quotes, for example `decision: "gtwq"`.
9. **Evidence scripts.** Put the script that produced a measurement in `notes/decisions/scripts/`.
   The Evidence section names it.
10. **No mirror rule.** The log rules of this repo do not follow OpenMMLab-Exporter. Do not import a
    file, a test or a tool from another repo. The kit keeps its optional mirror rule.

## Reason

- A sequential number needs one place that gives the numbers in order. `development` has no
  `notes/` folder, and a clone cannot see unpushed work on another machine. So two branches take the
  same next number, and the check finds the collision only after a fetch.
- A random ID makes a collision rare without coordination. The expected number of collisions is
  about N × u / S. N is the number of entries, u is the number of entries that you cannot see when
  you add one, and S = 22 × 32 × 32 × 32 = 720,896. For N = 1,000 and u = 10, it is about 0.014.
- An ID with a first letter sorts after the old numbers. YAML and spreadsheets do not read it as a
  number, for example `0e12`.
- 4 characters keep citations as short as before.
- A rebase keeps the author date, but it changes the commit date.
- The old tie-break, the file name, let a stale branch move a live entry.

## Consequences

- File names no longer sort by date. The index order is the order of addition.

## Evidence

- On 2026-10-25, the branches of OpenMMLab-Exporter show a renumber cascade. `main` took 0040 to
  0042, so seven entries of another branch moved from 0040–0046 to 0043–0049. Local `backup/*`
  branches kept the old names. The commits are not on its default branch, so no permalink is given.

## Alternatives rejected

- **Sequential numbers with a better check (0032).** A check finds a collision only after the two
  sides can see each other. A renumber can cascade.
- **A claim ref on `origin` for each number.** It needs a push for each entry and a network.
- **Numbers given at merge only.** An entry has no number for weeks while the PR stack is open.
- **The slug as the ID.** Citations become long.
- **Upper case.** Windows and macOS do not separate upper and lower case in file names.
