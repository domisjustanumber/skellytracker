# G2ZQ — Certify reports in format 1.7.0

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), 2026-11-21 (absorb at landing; PR: pending).

## Decision

1. `certify()` and the certify suite write reports in the format `skellycertify.report/1.7.0`. This
   changes the number of item 1 of
   [ADR-P47E](P47E-report-format-1-6-0-and-a-windows-ml-package-in-use.md). Each other rule of that
   entry stays.
2. A report of an older 1.x version stays in the hand-in list.

## Reason

- The owner of the format released 1.7.0 (skellycertify ADR-Q02Y). It changes one rule: the `name`
  of a `test_media` item can end in an image or video extension. No content of a report of this
  package changes: the name of its frames file is `quick_frames.zip`.
- The owner asked each package to write the newest schema id.

## Consequences

- None for an application. The relay accepts each 1.x schema id.

## Open work

- No real run made a report in the format 1.6.0 or 1.7.0 yet.
