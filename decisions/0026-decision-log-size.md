# 0026 — Size limits for the decision log

**Status:** superseded by [0029](0029-decision-log-read-path.md), 2026-10-24 (user).

## Decision

An agent reads a small part of the log for each task. The other entries are history. An agent reads
history only to find the reason for a decision.

1. **Read path.** The index in [`README.md`](README.md) has two tables: Active and Historical.
   Active has the entries with the status `proposed`, `accepted` or `evidence`. Historical has the
   entries with the status `rejected`, `superseded by NNNN` or `absorbed into <path>#<anchor>`. An
   agent reads `README.md`. Then it reads the Active entries that apply to its task. It reads a
   Historical entry only to find the reason for a decision.
2. **Absorbed status.** An accepted entry is absorbed when a normative document states all of its
   rules. The normative documents are the spec, `AGENTS.md` and the skills. Change the status line
   from `accepted` to `absorbed into <path>#<anchor>`, and write the date and the PR. Do not change
   the body. That document is then the source of the rules. The entry is the record of the reasons.
   Move the index row to Historical.
3. **Consolidation entries.** A consolidation entry states the rules that stay from a group of
   entries. It supersedes each entry of the group. It does not change a decision. It links to the old
   entries for the reasons. Write a consolidation entry at the end of the spec-build stage
   ([0014](0014-spec-lifecycle.md)). Write one also when the read-path limit (item 5) fails.
4. **Open work.** When an open-work item is done, delete it from the list. When the content PR of a
   spec defect lands, delete the defect from the list. The PR that closes an item records the result.
5. **Limits.** [`tools/check_decision_log.py`](../../tools/check_decision_log.py) counts characters
   after it changes CRLF to LF. About 4 characters make one token.

   | Limit | Characters | Applies to |
   |---|---|---|
   | Index | 24,000 | `README.md` |
   | Entry | 6,000 | each entry after 0025 |
   | Read path | 220,000 | `README.md` and all Active entries |

   Entries 0001 to 0025 keep their length, because the body of an old entry does not change. Put long
   evidence in a tracked file next to the entry, and link to it. A PR can lower a limit. A PR that
   raises a limit must add a decision entry. After the first consolidation, lower the read-path limit
   to 160,000 characters.
6. **Index checks.** The tool also checks that each entry file has one index row, that each row links
   to an entry file, and that each row is in the table for its status.
   [`tools/tests/test_decision_log.py`](../../tools/tests/test_decision_log.py) runs the tool in the
   doc tests.
7. **First review.** Examine the accepted entries 0001 to 0016. Mark each entry that
   a normative document states in full as absorbed.

## Reason

- On 2026-10-23, the log has 26 files and 197,278 characters, about 49,000 tokens. An agent that
  reads all of it before a change uses much of its context before the task starts.
- Four entries (0013 to 0016) have 81,828 characters, 41% of the log. The open-work list has 13,917
  of the 20,089 characters of `README.md`.
- An accepted rule stays in its entry after the rule moves into the spec. Thus the entries that
  agents read grow, but the number of rules does not. For example, the implementer guidance of
  [`format.versioning`](../../specs/model-sidecar/format/versioning.md#implementer-guidance) states rules
  of [0016](0016-sidecar-catalogs.md).
- The rule that the body of an entry does not change stays. Absorption and consolidation change only
  status lines, and they add entries.
- A test makes each limit a rule that CI checks. A written guideline alone does not stop the growth.

## Alternatives rejected

- **Move old entries to an `archive/` folder.** The links to the entries from the spec, the exporter
  repos and the PR descriptions break. The status and the index tables give the same filter with no
  move.
- **Delete superseded entries.** The reasons and the "Not repeated" pitfalls are lost. Then agents
  repeat settled questions.
- **Make long entries shorter.** This changes the body of an old entry, and it can change the record
  of a decision.
- **YAML front matter with the status in each entry.** This changes the body of each old entry. The
  index row already gives the status.
- **A token limit.** The token count is different for each model, and a tokenizer library is not in
  the doc tests. A character count does not change.

_Edited 2026-10-26 (this PR): link repair._
