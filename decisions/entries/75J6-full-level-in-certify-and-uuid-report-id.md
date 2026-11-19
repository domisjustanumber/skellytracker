# 75J6 — The level `full` in `certify()`, the report id as a UUID and the pack version in the report

**Status:** absorbed into [`certification.py`](../../skellytracker/certification.py), 2026-11-19 (user; PR: pending).

## Decision

Built today: each item. One run of the level `full` on `directml` on one Windows host is the only run on
hardware.

1. **One layout.** The level `full` of `skellytracker.certify()` writes the layout of the level `quick`:
   a flat list of checks with no sections, the same `details.eps` and the same `details.versions`.
2. **Checks in the package.** The level `full` runs only checks that need no checkout. It installs
   nothing and builds no environment. For each EP on each GPU of the selection, it runs the probe and
   the image check of the level `quick`, the pipeline timing at 1, 3 and 6 cameras
   (`<ep>:pipeline-<n>`), and the JPEG certification of `core/decode/certification.py` (`<ep>:jpeg`,
   and `<ep>:jpeg:<name>` for each of its checks). It first runs the timings and the JPEG certification
   of the CPU EP (`cpu:pipeline-<n>`, `cpu:jpeg`).
3. **Results.** A timing is `record-only`. The JPEG checks never change the EP check. The EP check
   `<ep>` passes when the probe and the image check pass, as in the level `quick`. The run stores the
   same local result as a quick check.
4. **Selection.** With no EP named, the level `full` also takes an EP on a GPU that has a reviewed
   row. The level `quick` does not.
5. **Suite.** `tools/certify_platform.py` keeps the checks that need a checkout: the versions against
   `uv.lock`, the hardware probe against the tools of the OS, and the install of each pack. It must
   call `certify("full")` and add its checks to the same report. This part is not built
   ([open work](../open-work.md)). The timing code is in the package, and the suite calls it.
6. **Pack version.** `details.eps.<ep>.pack_version` holds the version of the pack of the EP, the
   package version of its Windows ML record, or `builtin`.
7. **Report id.** The id of a report is a version 4 UUID. It is the key `id` of the report, the name
   of the report file and the id of the hand-in list. The schema is `skellycertify.report/1.1.0`. The
   package writes the id after the scrub of private words.
8. **Older reports.** A report of the schema `1.0.0` with a time in its file name stays in the hand-in
   list with its old id. It has no key `id`. The package does not change it and does not delete it.
9. **Pruning.** The package never deletes a report of the level `full`.

## Reason

- User rulings, 2026-11-19: items 1, 2, 5 and 6. The session of the repository `skellycertify` gave
  item 7 as a ruling of the user of the same day, with the schema version.
- An installed application has no checkout and no `uv.lock`. A check that cannot run there gives no
  evidence there.
- No report was handed in before item 7. Thus the old ids need no migration.

## Consequences

- A report of the level `full` holds about 150 JPEG checks for the CPU EP, and the same number for
  each EP with a JPEG certification.
- The time estimates of the level `full` are not calibrated.
- Until item 5 is built, the report of `tools/certify_platform.py` has its old format.
