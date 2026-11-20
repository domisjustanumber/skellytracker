# Q7VQ — Certify rulings of 2026-11-20: validation in freemocap builds, the passive record, the suite report layout

**Status:** accepted, 2026-11-20 (user).

## Decision

1. **Validation in freemocap builds.** From 2026-11-20, each validation of a system, a platform,
   hardware or an EP is done through the certify process in a freemocap build: freemocap calls
   `certify()` of each package, and the person hands in the report file. A run on Linux, on macOS
   or on other hardware is such a run. No run of this kind waits for a clone of this repository.
2. **Passive record.** The passive record of
   [ADR-21BK](21BK-quick-check-local-pass-and-hand-in.md) item 4 is a part of the 2.0.0
   pre-release. It does not wait for a later release.
3. **Layout of the suite report file.** `tools/certify_platform.py` writes the Markdown layout of
   section 4.2 of the format `skellycertify.report/1.2.0`: the header line, the system list, the GPU
   table from the `summary` items, the camera line, the failed checks, the note and `## Data`. The
   Markdown has no sections part, no EP checks part, no cleanup table, no answers part and no
   telemetry line. The JSON block keeps each of these facts. The last item of the Consequences of
   [ADR-2S52](2S52-summary-items-in-the-certify-report.md) does not apply from this entry.
4. **Wording.** A new text for a person says "system", not "machine". `CERTIFY.md` uses this word.

## Reason

- The user decided items 1 and 2 in this session. A freemocap build is what a person installs, so its
  run tests the files that the person uses.
- The user decided the format in the session of `skellycertify`
  ([skellycertify ADR-F1KN](https://github.com/domisjustanumber/skellycertify/blob/be69a9b230a9d6e64fbea7b5882e27561ef85e56/decisions/entries/F1KN-format-1-2-0-markdown-layout-revised.md)),
  and confirmed item 3 for this repository. The file of the suite then has the same layout as the
  file of freemocap.

## Consequences

- A failed cleanup step is not in the Markdown part. The terminal tells it, and the list `cleanup` of
  the JSON block holds it.
- A module with no `sections` list gives one row for each failed check. A failed check of a failed
  suite section then has its own row.
- A report with no `summary`, for example a file of the format 1.1.0, gives the row `not checked`
  for each GPU.

## Open work

- The format of `skellycertify` does not define the fields of a `passive` record. A writer must not
  write `"kind": "passive"` until it does. The definition is work of `skellycertify`.
- It is not decided if `tools/certify_platform.py` and `CERTIFY.md` stay after item 1.
- The [certification build list](../open-work.md#certification-build-list) holds the runs and the
  build of the passive record.
