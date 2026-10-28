# b1c0 — The `ADR-` prefix in citations and commit subjects

**Status:** accepted, 2026-10-26 (user); superseded by [HJNP](HJNP-upper-case-entry-ids.md), 2026-10-28 (user; PR: pending).

## Decision

This entry supersedes [gtwq](gtwq-random-entry-ids.md) and [vac0](vac0-record-a-changed-proposal.md)
in full. Items 1 and 2 are new. Items 3 to 6 restate gtwq, and item 7 restates vac0. These entries
and [0032](0032-entry-numbers-and-edits.md) keep the reasons.

1. **The prefix.** In new text, cite an entry of this log as `ADR-<id>`, for example ADR-x64y. Put
   the prefix before the link: `ADR-[x64y](x64y-draft-exporter-guide-folder.md)`. Cite an entry of
   another repo with the repo name and the prefix, for example "OpenMMLab-Exporter ADR-0020". A bare
   ID in older text stays valid, and it is an entry of this log. Do not edit a decided entry only to
   add the prefix.
2. **No prefix.** Do not use the prefix in a file name, an entry heading, an index row, a status line
   or a YAML value. End each commit subject that adds or changes an entry with `(ADR-<id>)`.
3. **Allowed edits.** The body of an entry that is not `proposed` does not change, except for four
   edits: a link or anchor repair, a typo fix that keeps the meaning, the redaction of private data,
   and a change of ID with the repair of its citations. Each edit adds
   `_Edited YYYY-MM-DD (#PR): <kind>._` at the end of the entry. `<kind>` is `link repair`, `typo`,
   `redaction`, `re-ID from XXXX` or `citation repair`. An old `renumber from NNNN` line stays.
4. **Entries.** A `proposed` entry can change until the user decides it. A proposal that completes a
   gap record edits the gap record. An entry that changes a part of an older entry restates each rule
   that stays, and supersedes the older entry in full. The template has an optional
   `## Consequences` section after `## Reason`. An entry that waits for a decision of another repo
   has the line `**Depends on:** <repo> XXXX (<status> on YYYY-MM-DD), <permalink>` under its status
   line.
5. **Sources.** Cite a commit, or the code of another repo, with a GitHub permalink that pins a full
   40-character SHA on the default branch of that repo. Cite a commit of this repo that is not on
   `development` by its PR number and file path. Links inside this repo stay relative. Put a dated
   fact in [open-work.md](open-work.md) or in an entry, not in `AGENTS.md`. Put the script of a
   measurement in `notes/decisions/scripts/`. The Evidence section names it. The log rules of this
   repo do not follow another repo. Do not import a file, a test or a tool from another repo. The kit
   keeps its optional mirror rule.
6. **Entry IDs.**
   - An ID has 4 characters from `0123456789abcdefghjkmnpqrstvwxyz`. The first character of a new ID
     is a letter. The file is `<id>-<slug>.md`. The heading is `# <id> — <title>`. The entries 0001
     to 0048 keep their numbers. Do not make a new all-digit ID. Write an ID in YAML in quotes, for
     example `decision: "gtwq"`.
   - After `git fetch --all` when you can, use the `new:` ID of
     `uv run python tools/check_decision_log.py --new`. No tree, worktree or branch has it.
   - An ID changes only for a collision. `--new` and `--collisions` print `keep:` or `re-ID:` for each
     entry of this tree whose ID a different file has. Both sides get the same verdict. The rank: on
     `development`, then on a remote-tracking branch, then the earlier author date of the first
     commit, then the file name that sorts first. An uncommitted file loses to a committed file. Refs
     merged into `HEAD`, the upstream and push refs of the branch, `backup/` branches and an old file
     name of an entry are not collisions.
   - On a `re-ID:` line, run `--new`. Rename the file, its heading and its index row. Repair each
     citation. Ask the user before you change a PR title or a PR body. If the entry is on
     `development`, add `_Edited YYYY-MM-DD (#PR): re-ID from XXXX._`.
   - Do not give an ID that an entry had on `development` to a different entry. The index keeps its
     rows in the order of addition.
7. **A changed exporter proposal.** When the exporter file of a `state: recorded` proposal changes,
   record it again in the same entry. Until then, Procedure B step 4 of `change-sidecar-spec` stops
   a landing. After `state: accepted`, the copy does not change. The ID, slug, file names, front
   matter and status stay. Replace each exporter file in full ([faac](faac-proposal-records.md)
   item 3). The source note gives the exporter commit and the dates of both copies. In "Before
   acceptance", keep the old items in order. Tick a closed item with its reason. Mark a changed item
   `(changed <YYYY-MM-DD>)` and a new item, last in its group, `(new <YYYY-MM-DD>)`. Change the
   Decision, Reason and Evidence only where the new version changes them. Add
   `recorded again <YYYY-MM-DD> (<source>)` to the status line, and change the index row if a cell
   changes. It is a non-spec PR. An exporter session that changes a recorded proposal tells the
   user.
8. **The kit.** The bootstrap kit takes items 1 and 2, and item 7 in a general form: when the source
   of a `proposed` entry changes, edit the same entry and add `recorded again`.

## Reason

- A bare ID is not clear in plain text: `0020` can be a number, and `keep` a word. `git log` and PR
  titles show no links. The user chose `ADR-`, a known term.
- Before the link, the prefix keeps the link text that the tool checks.
- gtwq item 8 and vac0 item 6 give the commit-subject rule, so this entry restates both.

## Alternatives rejected

- **The prefix in prose only.** No supersession, but `git log` keeps bare IDs.
- **A prefix for each kind of entry.** A status changes, but an ID does not.
- **A rewrite of the existing citations.** A large diff, and not an allowed edit.
