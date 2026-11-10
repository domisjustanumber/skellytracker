# CN15 — The spec README is the only entry point of the spec

**Status:** accepted, 2026-11-03 (user; PR: pending).

## Decision

This entry supersedes no entry. The non-spec workflow commit of
[ADR-0QKK](0QKK-no-legacy-layer.md) item 6 accepts it.

1. **One entry point.** [`specs/model-sidecar/README.md`](../../specs/model-sidecar/README.md) is
   the only entry point of the spec. Its [Section map](../../specs/model-sidecar/README.md#section-map)
   gives each section ID and its file. A person and an agent start there.
2. **The frozen index.** `specs/model-sidecar/sidecar-spec.md` is frozen. Do not add a heading to
   it. Do not add a stub for a removed heading. A commit changes it only to repair a link.
3. **The deletion.** Stage M11 of the
   [implementation plan](../../specs/sidecar-implementation-plan.md) deletes the file. The same work
   does these steps:
   - Each citation of the file in the package code becomes the section ID of its section file, for
     example `pre.normalize`. A whole-file citation cites the README.
   - The citation tests of `tools/tests/test_traceability.py` read the section-ID form and check
     that each cited ID exists (`section_ids()`). `INDEX_PATH` and the heading comparison go.
   - Another file defines the top-level keys, for example `batching`. Only then does the path of
     the file go from `defined_keys()` of `tools/tests/test_examples.py`.
   - The [Checks](../../.claude/skills/change-sidecar-spec/SKILL.md#checks) and the Spec structure
     of the `change-sidecar-spec` skill state the new test and drop the frozen-file rule.
   - Each link to the file goes to `specs/model-sidecar/README.md` or to a section file. A decided
     entry gets its link repairs and a link-repair `_Edited` line ([Rules](../README.md#rules)). A
     plain-text path in a decided entry stays, because it is history. The user first changes the
     two links in the draft exporter guide (item 4).
   - The bullet "Single source of truth" of the [Overview](../../specs/model-sidecar/README.md#overview)
     names the section files, not "this document".
   - A new entry supersedes [ADR-D9VT](D9VT-decision-log-move.md) in full. Its item 4 maps
     `specs/sidecar-spec.md` to `specs/model-sidecar/README.md`.
4. **The workflow commit.** The commit that accepts this entry makes these edits:
   - In [Spec structure](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#spec-structure) of the
     `change-sidecar-spec` skill, items 1 to 3 replace the rule "`sidecar-spec.md` is the permanent
     entry point". The changed rule cites this entry.
   - `reading-the-spec.md` names `README.md` as the entry point. An exporter cites
     `specs/model-sidecar/README.md` or a section file, not `sidecar-spec.md`. Its statements about
     `vNEXT` go ([ADR-SS2E](SS2E-spec-owned-version.md)).
   - The links and paths to the file in `model-addition-workflow/README.md`, `templates/model-intake.md` and
     the [README](../../specs/model-sidecar/decisions/README.md) of the spec log go to `README.md`.
   - The root [README](../../README.md) gets one line that links `specs/model-sidecar/README.md`.
   - The commit names the two links to the file in `specs/draft/exporter-guide/sidecars/README.md`.
     It does not change them, because the user owns that folder ([ADR-x64y](x64y-draft-exporter-guide-folder.md)).
5. **Other entries.** [ADR-0013](0013-spec-structure.md) made the file the permanent entry point.
   [ADR-TA0G](TA0G-vector-cases-and-reference-modules.md) superseded ADR-0013.
   [ADR-8DSW](8DSW-vector-files-are-the-case-source.md) item 7 keeps the rule by a link to
   [Rules for each spec edit](../../.claude/skills/change-sidecar-spec/SKILL.md#rules-for-each-spec-edit).
   This entry changes the text under that heading. Thus it does not supersede ADR-8DSW
   ([ADR-Z05A](Z05A-essential-decision-log-rules.md)). After the deletion, the words "and the
   permanent index" of ADR-x64y item 2 have no case. The spec overview still links the workflow.
   This entry changes no other rule of these entries.

## Reason

- The user chose this structure on 2026-11-03. The two goals of the user, in words: "1 to have the
  spec as public-facing documentation of the spec, and 2 - for LLMs to be able to read and follow
  the spec for exporter implementation."
- Two entry points give two places to start. The README has the overview, the conventions, the
  section map and the validation index. The index has only a link to the section map and
  "Moved to" lines.
- A section file is small. An agent reads the section map, then only the sections of its task.
- The promise of a permanent path is already broken. The exporters cite `specs/sidecar-spec.md`, a
  path that the working branch does not have.
- The code citations name headings of the index. Thus the index cannot go while the code cites
  it. A section ID does not change
  ([Rule IDs and section IDs](../../.claude/skills/change-sidecar-spec/spec-edit-rules.md#rule-ids-and-section-ids)).

## Consequences

- After M11, a link to the file from outside this repository does not resolve. No exporter cites
  that path today.

## Evidence

- `git grep -n "sidecar-spec.md" -- skellytracker/` gives 11 citations in 10 files (2026-11-03).
- Markdown links to the file: four in decided entries (0008, 0011, 0013 and k6dz), two in working
  files of the spec folder and two in the draft exporter guide. Code-span paths are in the skill,
  `reading-the-spec.md` and `templates/model-intake.md`.
- On the default branch of the four exporter repositories, each spec citation names
  `specs/sidecar-spec.md`, mostly as a URL of an old branch (checked 2026-11-03).

## Alternatives rejected

- **A generated single-file spec.** Each rule is then in two places. A search and an agent find the
  copy. A repeated heading gets an anchor that moves. Each commit must generate the file again.
- **An `llms.txt` map.** The section map already is that map.
- **Keep the index.** It is a second entry point, and each heading change needs a stub edit.
