# 0RNH — One check runner, a dry pack and a record command

**Status:** accepted, 2026-11-09 (user; PR: pending).

## Decision

1. `tools/run_checks.py` runs the checks before each commit and stops at the first failure. Its
   docstring is the list. [Checks](../../.claude/skills/change-sidecar-spec/SKILL.md#checks) names it.
2. `intake_bundle.py pack --dry-run` packs in a temporary folder with the real external paths, runs
   `verify` and writes nothing.
3. `intake_bundle.py record <bundle>` replaces the tracked record with a byte copy of the current
   version and checks each hash. It never imports or runs a bundle file
   ([ADR-AD33](AD33-bundles-are-untrusted-input.md)).
4. Pack the proposal bundles before the `model` bundles that name them.

[Pack a version](../../specs/model-sidecar/model-addition-workflow/hand-over.md#pack-a-version)
and [Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)
state items 2 to 4.

## Reason

In the YOLOX and RTMW intakes of 2026-11-06 to 2026-11-09, a pipe hid the exit code of a check.
An exporter needed a Windows junction for its dry pack. A safety rule denied `rm -rf` on a record
folder, which cost one more call. `verify` of a `model` bundle reads the proposal bundles that it
names, so a `model` bundle packed first gets findings for a missing proposal.

## Alternatives rejected

- **A `respond` command.** [ADR-M3RY](M3RY-answers-version-names-an-existing-version.md) already
  makes `verify` find a wrong `answers_version`.
- **Allow rules for the tools.** The settings are local, so only the user can add them. A rule that
  matches `fill` or `batch` removes a gate of [ADR-AD33](AD33-bundles-are-untrusted-input.md).
- **`land` takes an equal case as unchanged.** This changes item 5 of
  [ADR-8DSW](8DSW-vector-files-are-the-case-source.md). The `land` refusal cost only one more
  tool call.
