# FJG4 — The Evidence table in its own file, two more exits for evidence, and a skill for log changes

**Status:** absorbed into [Rules](../README.md#rules), [`change-decision-log`: Steps](../../.claude/skills/change-decision-log/SKILL.md#steps), [`change-decision-log`: Rules](../../.claude/skills/change-decision-log/SKILL.md#rules), [Decision Log](../../AGENTS.md#5-decision-log), [`tools/check_decision_log.py`](../../tools/check_decision_log.py), 2026-11-23 (user, "Q55 yes, and include changes 2 and 3. Also make a skill out of rules with an appropriate hook."; absorb at landing; PR: pending).

This entry supersedes [ADR-J9QT](J9QT-evidence-table-off-the-read-path.md).

## Decision

1. **The file.** Each log has the file `evidence.md` with the Evidence table. Each entry with the
   status `evidence` has a one-line row in it. The `README.md` of a log has no Evidence table.
   `tools/check_decision_log.py` reports an Evidence table in another file, an `evidence` entry in
   the Active table and an entry that is not `evidence` in the Evidence table.
2. **The read path.** `evidence.md` and its entries are not in the read path. `evidence.md` has no
   size limit.
3. **When to read it.** Before an agent makes a measurement, it scans the rows of `evidence.md` of
   each log and reads the entries that apply. This rule of ADR-J9QT stays.
4. **`used by`.** An `evidence` entry changes to `evidence; used by XXXX` when entry XXXX is or was
   `accepted` and cites it for its decision. Before, entry XXXX had to be `accepted` at the time of
   the change.
5. **`replaced by`.** The new status `evidence; replaced by XXXX` is for an `evidence` entry when
   the `evidence` entry XXXX repeats the measurement and its numbers replace the old numbers. The
   row moves to `historical.md`. The status line links entry XXXX.
6. **The trigger.** The absorb pass starts when the read path or an index is at 90% of its limit or
   more. Before, only the read path started it.
7. **The skill.** The skill `change-decision-log` holds the rules for a change to a log: the allowed
   edits, the absorb rules, the status changes, the ID rules and the citation rules for a commit
   that is not on the target branch. The Rules of the index keep the rules for reading a log, the
   rule that a decision must be in an entry and the open-work rule. The words of the moved rules do
   not change, except for items 4 to 6.
8. **The hook.** The pre-commit hook `decision-log` runs `tools/check_decision_log.py --staged`.
   It prints one line that names the skill when the commit holds an entry, a `README.md`, an
   `evidence.md` or a `historical.md` of a log. It does not stop the commit.
9. **The moves.** ADR-4JFP is `evidence; used by S4MT`. ADR-58F5 is `evidence; used by 889R`.
   ADR-1SZ9 is `evidence; used by W4NW`. ADR-0YYY is `evidence; used by Q4BF`. ADR-B5Z0 is
   `evidence; replaced by 4JFP`. The status line of each absorbed entry that linked the Rules of the
   index for a moved rule now links the Rules of the skill. This is a link repair.

## Reason

- On 2026-11-23 the root index held 17,992 of 18,000 characters. The Rules held 8,302 of them, the
  Evidence table 3,907 and the Active table 3,752.
- The Evidence table was the part that grew: 6 rows on 2026-11-17 and 18 rows on 2026-11-23. Its
  rows were not on the read path, but they counted against the limit of a file that is.
- Only 1 of the 18 rows could leave. For 4 rows, the entry that cites the row was already absorbed.
  For 1 row, a later measurement on a quiet system gave new numbers.
- An agent needs most of the Rules only when it changes a log. Each agent read them for each task.
- A full index started no absorb pass, because the trigger named only the read path.
- After this change the root index holds about 7,200 characters.

## Evidence

- The sizes are from `size` of `tools/check_decision_log.py` and a count of the characters of each
  section of `decisions/README.md` at commit `5157d1ba`.
- A search of each log for `ADR-<ID>` of each of the 18 Evidence entries gave the entries that cite
  them.

## Alternatives rejected

- **A higher `INDEX_LIMIT`.** The causes stay, and the index grows to the new limit.
- **A shorter Decision cell.** It saves about 1,500 characters, and 36 rows need new text.
- **A harness hook that loads the skill before an edit in `decisions/`.** Git ignores `.claude/`
  except the skills, and such a hook serves one agent tool only.
- **A new anchor in place of `#rules`.** 45 files link that heading. The heading stays, so each
  link in a decided entry body stays valid.

## Not repeated

- ADR-Z0CC, ADR-7E4Z and ADR-C9ME did not move. The entries that cite them do not clearly use them
  for a decision or repeat their measurement. Examine each one before a move.

## Open work

- No agent examined which of the Active entries the absorb documents now state in full.
