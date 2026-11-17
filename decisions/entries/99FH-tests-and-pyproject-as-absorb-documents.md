# 99FH — A package test is a tool, and `pyproject.toml` is an absorb document beside a test

**Status:** absorbed into [`README.md#rules`](../README.md#rules), [`tools/check_decision_log.py`](../../tools/check_decision_log.py), 2026-11-17 (user, "yes to all" on question L3 of 2026-11-17; PR: pending).

## Decision

1. **Package tests.** A test in `tools/tests/` or in `skellytracker/tests/` is a tool for the absorb
   rule. Its docstring states the rules that it checks. Before, only a test in `tools/tests/` was a
   tool ([ADR-5EVP](5EVP-absorb-across-documents.md) item 4).
2. **`pyproject.toml`.** `pyproject.toml` is an absorb document for a rule that a test checks. The
   `absorbed into` status that links `pyproject.toml` also links the test file that checks the rule.
3. **The check.** `tools/check_decision_log.py` reports an `absorbed into` status that links
   `pyproject.toml` with no link or code span to a test file `tests/test_*.py`. A rule in
   `pyproject.toml` with no test is then not a hole in the limit.
4. **The test of the pins.** `tools/tests/test_dependency_pins.py` checks the rules of
   [ADR-M2C6](M2C6-exact-pins-and-one-python-patch-release.md),
   [ADR-W09C](W09C-opencv-contrib-python.md) and
   [ADR-D3VP](D3VP-ruff-0-17-with-the-old-rule-set.md) that `pyproject.toml` and the files beside
   it hold. Its docstring states them.
5. **The absorbs.** ADR-W09C and ADR-D3VP are absorbed into `pyproject.toml` and the test of the
   pins. The open work of ADR-D3VP is the ruff rule review of stage 2.5 of the implementation plan.
   [ADR-8YXH](8YXH-aruco-marker-threshold-and-charuco-corner-position.md) is absorbed into the
   docstrings of its tests in `skellytracker/tests/`. ADR-M2C6 stays `accepted`: no test or
   absorb document states that freemocap uses the same versions and the same Python, or that a new
   Python patch release needs a new skellytracker release.
6. An absorbed entry keeps its file, with its Evidence section.

## Reason

- On 2026-11-17 the read path was 140,579 of 160,000 characters (88%). It grew by about 10,000
  characters each day for five days. The entries whose rule lived only in code or in
  `pyproject.toml` held about 16,700 characters.
- A test that checks a rule is a better home than prose: a change that breaks the rule fails the
  test.
- A rule in `pyproject.toml` with no test can change with no notice. The test link keeps the rule
  checked.
- The user, on 2026-11-17: "yes to all" on the four questions of the read-path review. The user's
  example: ADR-M2C6 is absorbed once a test checks that each dependency has `==`.

## Alternatives rejected

- **A higher `READ_PATH_LIMIT`.** [ADR-5EVP](5EVP-absorb-across-documents.md),
  [ADR-2XW6](2XW6-process-entries-consolidation.md) and
  [ADR-Z05A](Z05A-essential-decision-log-rules.md) rejected it before. The causes stay, and the read
  path grows to the new limit.
- **A read path for each module.** It adds rules and checks for a small gain
  ([ADR-5EVP](5EVP-absorb-across-documents.md)).
- **A digest of each entry in the index.** The digest must stay in sync with its entry.
- **A new status, for example `implemented`.** It changes the allowed status changes and each status
  form. The rule then has no home that a check reads.
- **More consolidation entries.** A consolidation copies the rules into a new entry that stays on the
  read path.
- **Each config file as an absorb document.** Only `pyproject.toml` holds rules today. A new file
  needs its own decision.
