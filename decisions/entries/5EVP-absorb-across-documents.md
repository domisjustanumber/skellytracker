# 5EVP — Absorb an entry across the absorb documents

**Status:** accepted, 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes no entry. It changes the absorb rules of the [Rules](../README.md#rules).

1. **Absorb across documents.** An accepted entry is absorbed when the absorb documents together
   state all of its rules. Before, one absorb document had to state all of them.
2. **The status.** `absorbed into` has one link for each absorb document that states a rule of the
   entry, to the heading that holds those rules or to the file. A comma and a space separate the
   links. [`check_decision_log.py`](../../tools/check_decision_log.py) accepts the list.
   `STATUS_EXEMPTION_LIMIT` goes from 1,000 to 2,000, so that a long list does not make the entry
   too long.
3. **Open work.** Open work of an entry does not stop the absorb when `open-work.md` or the
   [implementation plan](../../specs/sidecar-implementation-plan.md) states that work in full. A
   link to the entry is not enough. `open-work.md` and the plan do not become absorb documents.
4. **Tests and vector notes.** A test in `tools/tests/` is a tool for the absorb rule: its
   docstring states the rules that it checks. The spec includes the `notes` of its vector files.
5. **At 90% of the read path.** First absorb each entry whose rules the absorb documents state.
   Then write each rule that no absorb document states in the absorb document where it belongs, and
   absorb its entry. A consolidation entry is not a step of this rule. Write one only at the end of
   the spec-build stage.
6. **Two rules move.** The read order of the entries and the rule that a change of the text under a
   linked heading does not supersede the entry move from the introduction of
   [`README.md`](../README.md) into the Rules. Their meaning does not change.
7. **The kit.** The kit Rules take items 1 to 6 without the spec, the plan and the spec-build stage.
   The introduction of the kit `README.md` loses the two rules of item 6.

## Reason

- The user, 2026-11-10: "yes" to the audit of the Active entries, then on the open work: "no it
  does not block". The user agreed to count tests and vector notes and to move the two rules.
- The read path was 139,496 of 160,000 characters (87%). From 2026-10-29 it stayed between 128,000
  and 159,000 characters, with 19 to 30 Active entries. Absorbs and consolidations made it shorter,
  and new entries made it longer again.
- Most Active entries set rules in two or more absorb documents, for example the spec, the workflow
  and a tool docstring. With the one-document rule, such an entry stayed on the read path also when
  each of its rules was stated.
- A consolidation entry spans many documents, so it could not be absorbed.
  [ADR-2XW6](2XW6-process-entries-consolidation.md) and
  [ADR-BQZ9](BQZ9-intake-process-consolidation.md) held 11,000 characters of the read path.
- The open work of [ADR-0QKK](0QKK-no-legacy-layer.md),
  [ADR-6GE2](6GE2-spec-version-follows-skellytracker.md) and [ADR-JAA4](JAA4-one-batch-field.md) is
  a package migration that plan stage M8 states in full. It kept 18,000 characters on the read path
  for the whole spec-build stage.

## Evidence

- A review of 2026-11-10 at commit 6a59bad mapped each rule of the 26 Active entries to the heading
  that states it. Under this entry, 13 entries (54,580 characters) can be absorbed now. 7 entries
  (30,192 characters) can be absorbed after about 28 rules get a home. 6 entries (26,688
  characters) have open work of their own and stay. The sizes come from `read_path_size` of
  `tools/check_decision_log.py`.

## Alternatives rejected

- **A higher `READ_PATH_LIMIT`.** The causes stay, and the read path grows to the new limit.
- **Count only the Decision section.** The number gets smaller, but an agent reads the same text.
- **A read-path budget for each module, or task tags.** These add rules and checks for a small
  gain.
- **One absorb document, with a consolidation at 90%.** A consolidation copies the rules that have
  no home into a new entry that cannot be absorbed.
