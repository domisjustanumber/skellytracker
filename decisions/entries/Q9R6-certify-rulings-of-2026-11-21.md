# Q9R6 — Certify rulings of 2026-11-21: a 65 s quick limit, `abandon`, the passive record in phase 2, the media record

**Status:** absorbed into [Layout](../../skellytracker/AGENTS.md#layout), [`certification.py`](../../skellytracker/certification.py), 2026-11-21 (absorb at landing; PR: pending).

## Decision

1. **The limit of quick.** A quick run of skellytracker has a hard limit of 65 seconds. freemocap gets
   25 seconds and skellycam keeps 30 seconds: the total stays 2 minutes. This changes the number of
   item 5 of [ADR-X7WD](X7WD-certify-levels-rulings-of-2026-11-20.md). Each other rule of that item
   stays.
2. **`abandon`.** `certify()` takes `abandon`, keyword-only with the default None: an object with
   `is_set()`, as `cancel`. A set abandon stops the running child as a set cancel does, and the
   clean-up runs. From the time it is set, the run stores no local result. It writes no report file
   and deletes no older report. The returned report has the reason `abandoned` in `evidence.reasons`
   and on each check that a stop ended or that did not end. With no `abandon`, `certify()` does not
   change.
3. **The passive record in phase 2.** The passive record of
   [ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 4, its shadow comparison and the
   calibration of its limit are work of phase 2, not of the 2.0.0 pre-release. This changes item 2
   of [ADR-Q7VQ](Q7VQ-certify-rulings-of-2026-11-20.md).
4. **The media record.** Each report records the test media that its checks ran on: the name, the
   sha256 and the source, `package` or `test_media_dir`. A `test_media_dir` with no `<sha256>.zip`
   falls back to the file of the package. A file with a wrong sha256 still gives
   `test-media-missing`. This waits for the field in the format of `skellycertify`.

## Reason

- The user decided each item in this session. Item 3, in the user's words: "Passive record work can
  go into Phase 2".
- Item 1 makes room for the checks of freemocap in the limit of 2 minutes.
- Item 2: when the backend of the app dies, its crash record already says "interrupted". The orphaned
  certify child must not write a second report, and must not store a pass over the failure that the
  crash record stored.

## Consequences

- freemocap no longer needs the private `_label` and `_record`: `check_label()` and
  `record_failed_pair()` of `skellytracker/certification.py` are public. They need no entry.
- A pair that ended before the abandon keeps its stored result.

## Open work

- The [certification build list](../open-work.md#certification-build-list) holds the passive record
  and the media record.
