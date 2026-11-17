# J9QT — An Evidence table for each log, off the read path

**Status:** absorbed into [`README.md#rules`](../README.md#rules), [`AGENTS.md#5-decision-log`](../../AGENTS.md#5-decision-log), [`tools/check_decision_log.py`](../../tools/check_decision_log.py), 2026-11-17 (user, "yes to all" on question L2 of 2026-11-17; PR: pending).

## Decision

1. **The table.** The `README.md` of each log has an Evidence table after the Active table. Each
   entry with the status `evidence` has a one-line row in it. The Active table holds only the
   `accepted` entries. An entry with the status `evidence; used by XXXX` stays in `historical.md`.
2. **The read path.** `read_path_size` of `tools/check_decision_log.py` does not count the entries
   of the Evidence table. It counts their rows, because the rows are in `README.md`.
3. **When to read it.** The [Rules](../README.md#rules) tell an agent to scan the Evidence rows of
   each log before it makes a measurement, and to read the entries that apply. Then the agent does
   not repeat a measurement. An agent reads the Evidence table on demand, as it reads the Proposed
   table.
4. **The check.** `tools/check_decision_log.py` reports an `evidence` entry in the Active table and
   an entry that is not `evidence` in the Evidence table.
5. **The move.** The rows of ADR-Z0CC, ADR-X6S9, ADR-0YYY, ADR-73Q4, ADR-GPW6 and ADR-7E4Z (root
   log) and ADR-6JWJ (pipeline log) move from the Active table to the Evidence table. Their status
   does not change. The open item of ADR-6JWJ, the run again on MediaPipe 1.2.2, is done:
   Implementer guidance of
   [`mediapipe_tasks.md`](../../specs/pipeline/nodes/mediapipe_tasks.md#implementer-guidance) gives
   its result. So `open-work.md` of the pipeline log needs no item for it.

## Reason

- On 2026-11-17 the read path was 140,579 of 160,000 characters (88%). It grew by about 10,000
  characters each day for five days.
- The 7 `evidence` entries held 26,974 characters of it. An agent read them before each package
  change, also when the task made no measurement. For example, ADR-GPW6 holds 6,093 characters of
  gate numbers.
- A measurement entry has no rule to absorb. It stays `evidence` until an accepted entry uses it, so
  the absorb rules cannot take it off the read path.
- The user, on 2026-11-17: "yes to all" on the four questions of the read-path review.

## Evidence

- `read_path_size` of `tools/check_decision_log.py` on 2026-11-17, before this entry: 140,579
  characters. The sizes of the 7 `evidence` entries come from `size` of the same tool, in a
  read-only review of 2026-11-17.

## Alternatives rejected

- **A higher `READ_PATH_LIMIT`.** [ADR-5EVP](5EVP-absorb-across-documents.md),
  [ADR-2XW6](2XW6-process-entries-consolidation.md) and
  [ADR-Z05A](Z05A-essential-decision-log-rules.md) rejected it before. The causes stay, and the read
  path grows to the new limit.
- **A read path for each module.** It adds rules and checks for a small gain
  ([ADR-5EVP](5EVP-absorb-across-documents.md)). The evidence entries are in the root log, so it
  does not remove them.
- **A digest of each evidence entry in the index.** The digest must stay in sync with its entry, and
  a short digest loses the numbers that stop a repeated measurement.
- **A new status, for example `implemented`.** It changes the allowed status changes and each status
  form, and an `evidence` entry is not a decision that a stage implements.
- **More consolidation entries.** A consolidation copies text into a new entry that stays on the
  read path, and a measurement has no rule to consolidate.
