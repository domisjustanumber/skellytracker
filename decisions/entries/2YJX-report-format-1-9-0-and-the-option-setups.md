# 2YJX — Certify reports in format 1.9.0; `certify()` and `certify_plan()` take `setups`

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), 2026-11-23 (absorb at landing; PR: pending). It was `accepted` on 2026-11-23.

## Decision

1. `certify()` and the certify suite write reports in the format `skellycertify.report/1.9.0`. This
   changes the number of item 1 of [ADR-G2ZQ](G2ZQ-report-format-1-7-0.md). Each other rule of that
   entry stays.
2. `certify()` and `certify_plan()` take the keyword-only option `setups`: the `id` of each setup
   that the person accepted. The plan has the list `setups`.
3. This package has no setup check. The `setups` list of the plan is always empty, and the option
   changes no check and no report.

## Reason

- The owner of the format released 1.8.0 and 1.9.0 (skellycertify ADR-974S, ADR-TWK1 and
  ADR-T3BD) and asked each package to write the newest schema id and to accept `setups`.
- 1.9.0 adds the `skipped` reason `declined` for an item whose checks all need a declined setup.
  No item of this package can have it.

## Consequences

- None for an application. The relay accepts each 1.x schema id.

## Open work

[open-work.md](../open-work.md)
