# 6GE2 — Spec version follows the skellytracker version

**Status:** absorbed into [`README.md`](../../specs/model-sidecar/README.md), [`change-sidecar-spec/SKILL.md`](../../.claude/skills/change-sidecar-spec/SKILL.md), [`model-addition-workflow/validation-and-publishing.md#publishing`](../../specs/model-sidecar/model-addition-workflow/validation-and-publishing.md#publishing), [`tools/tests/test_changelog_revision.py`](../../tools/tests/test_changelog_revision.py), 2026-11-10 (user; PR: pending).

## Decision

This entry supersedes [ADR-SS2E](SS2E-spec-owned-version.md) in full. Items 1 to 5 replace SS2E
items 1, 2, 3 and 5. Item 6 restates the rules that stay by links
([ADR-Z05A](Z05A-essential-decision-log-rules.md)). Its own content commit accepts it, before the
workflow commit of [ADR-0QKK](0QKK-no-legacy-layer.md) item 6.

1. **The version.** A spec version is the skellytracker version, in SemVer, that first releases a
   spec change. A release with no spec change makes no spec version. Each spec change and each
   proposal targets the next skellytracker release until it is released. Until the user bumps
   skellytracker, the open target is `2.0.0`. The user makes the bump and the `bumpver` change
   elsewhere. A spec-owned version, the revision `1.N` and CalVer go.
2. **`schema_version`.** `schema_version` is a quoted string: the version that the sidecar
   follows. Its pattern is `MAJOR.MINOR.PATCH` with an optional SemVer pre-release tag (item 7).
   `V-format.versioning-1`: `schema_version` must be a version heading of the changelog or a
   recorded pre-release of the open target. Until `2.0.0` ships, only `"2.0.0"` and its
   pre-releases are valid. Each release lists the versions that it implements.
   `V-format.versioning-2` does not change: a host rejects a `schema_version` that it does not
   implement. The version comparison, the CalVer pre-release rule, the too-new rule and the
   exporter obligation stay removed.
3. **Rule IDs.** A `V-` rule ID has no version part. It never shifts (item 6).
4. **The changelog.** The heading `## Revisions` stays. The revision `1.0` becomes the version
   heading `### 2.0.0`. Its first line is `- Released: no.` Each content commit appends one line
   ``- Row N: `<fingerprint>`.`` under the open target, with no version bump. `N` is the highest
   row of the summary of changes, and the fingerprint is the doc-test value. An earlier line does
   not change. The content commit of this entry turns the `Last row` and `Fingerprint` lines of
   `1.0` into the row 30 line, appends its own row line and rewords no row. The release sets
   `- Released: yes.` A released version does not change. After a release, the next change adds
   the heading of the version that the user bumps skellytracker to on `development`. When a
   release ships under another number, the release PR renames the unreleased heading and changes
   the examples. Pre-release values of the old number become invalid. In the spec, "this
   revision" and "the current revision" mean the open target. The publish ban: a sidecar goes to
   a shared or remote sidecar root only after a final release loads its `schema_version`. The
   private test repo of the implementation stage is the one exception. skellytracker `2.0.0`
   ships the SemVer loader, so its release ends the ban for `"2.0.0"`.
5. **The re-export request.** The
   [Re-export requests](../../specs/model-sidecar/decisions/open-work.md#re-export-requests) item
   targets `2.0.0`. It adds this entry to its prerequisite changes.
6. **The rules that stay.**
   - SS2E item 2: [Revisions](../../specs/model-sidecar/changelog.md#revisions), and the docstring
     of `tools/tests/test_changelog_revision.py`.
   - SS2E item 3: the
     [`change-sidecar-spec` skill](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#changelogmd).
   - SS2E item 4: [Behaviour](../../specs/model-sidecar/format/versioning.md#behaviour) and
     [Authoring guidance](../../specs/model-sidecar/format/versioning.md#authoring-guidance), with
     the ban of item 4. The workflow commit of [ADR-0QKK](0QKK-no-legacy-layer.md) item 6
     replaces the intake result "n/a at `vNEXT`".
   - SS2E item 6:
     [Scope of this revision](../../specs/model-sidecar/changelog.md#scope-of-this-revision). The
     workflow commit makes part 7 of the proposal template cite entries, not that heading.

   Each heading above states its rule at the content commit of this entry, which creates the
   anchor `changelog.md#200`.
7. **Pre-releases.** A pre-release value names the open target at that skellytracker pre-release.
   The changelog records each pre-release under its target with its last row, for example
   `- Pre-release 2.0.0-rc.1: row 31.` A pre-release host lists its own value and the
   open target. No other host implements a pre-release value. So `2.0.0` does not load a
   `2.0.0-rc.1` sidecar, and the exporter exports again after the release.
   A pre-release sidecar is a test sidecar: the private test repo only (item 4).

## Reason

- The user, in words: "The spec version number must be the same version format as skellytracker
  [...] and will follow that version". Then: "Switch to SemVer"; "One target per release"; "Do
  not bump skellytracker here, [...] For now assume 2.0.0"; for
  `schema_version`, "The target: "2.0.0""; for rule IDs, "Independent, IDs never shift"; "Spec
  versions = changelog headings"; "2.0.0 must ship the loader"; "Allow pre-release tags"; for an
  rc host, "Yes, also the open target"; for the publish ban, "A"; for the next heading, "The
  bumped dev version".
- One number tells a user which skellytracker release loads a sidecar.
- One target for each release gives a proposal a version to cite.
- A row line for each content commit keeps the check that each change adds a summary row.

## Consequences

- Each example and each exporter writes `schema_version: "2.0.0"`. The frozen package rejects
  it. The `2.0.0` release needs an implementation-plan item: `versioning.py` and `loader.py` drop
  the release comparison and accept the values that the host implements.
- `tools/tests/test_changelog_revision.py` reads SemVer headings and checks the lines of item 4.

## Alternatives rejected

- **The spec-owned `"1"` with revision `1.N`.** Two numbers for one contract.
- **Renumber the rules until the first release.** An exporter intake would cite a rule that moved.
