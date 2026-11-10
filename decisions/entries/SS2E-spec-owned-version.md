# SS2E — Spec-owned version

**Status:** accepted, 2026-11-02 (user; PR: pending); superseded by [6GE2](6GE2-spec-version-follows-skellytracker.md), 2026-11-03 (user; PR: pending).

## Decision

This entry supersedes
[ADR-YNX0](../../specs/model-sidecar/decisions/entries/YNX0-vnext-scope-list.md) in full. Items 1
to 5 are new. Item 6 restates the rules that stay by a link
([ADR-Z05A](Z05A-essential-decision-log-rules.md)).

1. **The version of a sidecar.** Each sidecar has `schema_version: "1"`, a quoted string. The spec
   owns the version. A skellytracker release does not set it. The pattern `vYYYY.0M.BUILD` goes.
   `V-format.versioning-1`: `schema_version` must be the string `"1"`. `V-format.versioning-2`: a
   host must reject a `schema_version` that it does not implement, with an error that names the
   version. The capability check lists such a sidecar as unavailable. The version comparison, the
   pre-release rule, the exporter obligation and the release form of the too-new rule go.
2. **The revision of the spec.** The spec revision is `1.N`. It is the heading of a changelog
   entry. Each content commit increments `N` and adds a changelog row. A doc test checks that a
   changed normative heading or `V-` rule comes with a new revision and a changelog row. The
   docstring of the test defines its baseline. From `1.0` on, a change that deletes a `V-` rule
   leaves its number unused, and no commit renumbers a rule. The rule IDs of a section can then
   have gaps. How a bundle records the revision is for the bundle-process entry that follows.
3. **The `1.0` reset.** The content commit of this entry sets the revision `1.0`. It replaces the
   `schema_version` history of the changelog. It edits each row of the summary of changes that
   names `vNEXT`, a `schema_version` or a change class. This is one exception to the rule "Do not
   reword the existing rows" of the
   [`change-sidecar-spec` skill](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#changelogmd).
   The rows keep their numbers. After `1.0`, no commit rewords an existing row.
4. **No `vNEXT`.** `vNEXT` goes from the spec, the examples, `inventory.yaml` and the tools and
   tests that the checks need. In the heading
   [Scope of this revision](../../specs/model-sidecar/changelog.md#scope-of-this-revision), "the
   spec" replaces `vNEXT`. The heading keeps its name and its rules, and it cites this entry. Do not
   publish a sidecar to a shared or remote sidecar root until a skellytracker release loads
   `schema_version: "1"`. The development-build rule for `vNEXT` goes. The private Hugging Face test
   repo of the implementation stage stays the one exception to that ban. The workflow commit of
   [ADR-0QKK](0QKK-no-legacy-layer.md) item 6 replaces the intake result "n/a at `vNEXT`".
5. **The re-export request.** The item of
   [Re-export requests](../../specs/model-sidecar/decisions/open-work.md#re-export-requests) names
   its target revision `1.0` and links [ADR-0QKK](0QKK-no-legacy-layer.md),
   [ADR-JAA4](JAA4-one-batch-field.md), [ADR-90CE](90CE-minimal-sidecar-contract.md) and
   [ADR-17KN](17KN-one-selection-pipeline.md)
   ([ADR-NB5F](NB5F-no-change-classes-and-one-re-export-request.md) item 2). The content commits
   of these four entries come before the content commit of this entry. Thus `1.0` holds each
   prerequisite of the item.
6. **The rules that stay.** YNX0 items 1 to 6 (the scope list, the two join events, a new
   batch-conversion profile, a proposal gives only the text of the current revision, a proposal
   that the user has not decided stays `proposed`, the table of features not added, the RF-DETR
   rules and "not the intake verdict"):
   [Scope of this revision](../../specs/model-sidecar/changelog.md#scope-of-this-revision). The
   placeholder name `vNEXT` and the citation of the release step go with item 4. The rule of YNX0
   item 4 that the template cites the heading of the list and not an entry ID goes: part 7 of the
   proposal template cites entries.

## Reason

- The user, in words: "Spec-owned for now. Future step is to have the skellytracker version that a
  spec change was introduced in be the spec version as well, but that requires proper skellytracker
  version control to be implemented first."
- `vNEXT` is not a version. `load_sidecar` rejects it, and no release can load a `vNEXT` sidecar.
  The release step had to replace it in each example, each tool and the changelog.
- A version that the spec owns can be set now. It does not wait for a skellytracker release.
- A revision for each content commit lets an exporter name the exact text that it implements.
- No release cites a row. The history names `v2024.09.1019`, a release that had no sidecar spec,
  and `vNEXT`, which never shipped. Its rows describe legacy readings that
  [ADR-0QKK](0QKK-no-legacy-layer.md) removes.

## Consequences

- Each example and each exporter writes `schema_version: "1"`. The frozen package rejects it until
  the package migrates. The implementation plan gets an item for that work.
- Each content commit after `1.0` edits the changelog. The doc test stops a commit that forgets it.
- The frozen evidence file `notes/sidecar-exporter-coverage.md` and the implementation plan keep
  the word `vNEXT`.

## Alternatives rejected

- **Keep `vNEXT` until the first release.** The release step then edits each file that names it,
  and no sidecar can load before the release.
- **The skellytracker release version now.** It needs proper skellytracker version control first.
- **Keep the history rows.** They state legacy readings that no longer exist.
