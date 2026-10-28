# Decision log: entry template

Use this template for a new entry. The [Rules](README.md#rules) of the index apply. This file is not
in the read path: read it when you write an entry.

The file name is `<ID>-<short-slug>.md`. Get `<ID>` from
`uv run python tools/check_decision_log.py --new`. The ID is in upper case.

```markdown
# <ID> — <title>

**Status:** <proposed | accepted | evidence>, <YYYY-MM-DD> (<source>).
**Depends on:** <repo> XXXX (<status> on YYYY-MM-DD), <permalink>

## Decision

## Reason

## Consequences

## Evidence

## Alternatives rejected

## Not repeated
```

- **Status.** `accepted` is a decision. `evidence` is a measurement. `proposed` waits for a decision.
  The source says who decided, for example "user".
- **Depends on.** Optional. Write it only when the entry waits for a decision of another repo.
- **Decision.** What is decided, written so that a reader can apply it.
- **Reason.** Why. Each entry gives its own reasons.
- **Consequences.** Optional. What becomes harder, what must change later and what the decision
  costs.
- **Evidence.** Write it only when there is evidence: measurements with their tool, its version and
  the script in `scripts/` of the log that holds the entry, or code facts with their file and
  function.
- **Alternatives rejected.** The options that were examined and not used, with the reason for each.
- **Not repeated.** Pitfalls already found.
- Omit an optional section when it has no items. Put open-work items in
  [open-work.md](open-work.md), not in an entry.
