# 0034 — One folder for the exporter guide

**Status:** absorbed into [`AGENTS.md#1-purpose`](../../AGENTS.md#1-purpose), 2026-10-25 (user; the absorption review).

## Decision

1. **One folder.** The guidance for exporters is in one folder, `specs/exporter-guide/`. The sidecar
   guide moves from `specs/sidecar/exporter-guide.md` to
   [`specs/exporter-guide/sidecars/`](../../specs/exporter-guide/sidecars/README.md). No stub stays at
   the old path.
2. **Small files.** The sidecar guide is split at its headings into 13 files. The largest file is
   about 7,000 characters. The headings move up, so that each file starts with one `#` title. The
   text does not change. `sidecars/README.md` and `sidecars/workflow/README.md` get a list of links
   to their files.
3. **A move only.** The move changes no rule. Each link to the old file goes to the new file and
   anchor. A decided entry with such a link gets a link-repair `_Edited_` line. A plain-text mention
   of the old path in a decided entry stays, because it is history.
4. **Later work.** A later rewording PR removes the exporter repository names from `sidecars/` and
   the open items that do not apply to a new exporter.

## Reason

- The name "exporter guide" named two things: this file and the new guide for building an exporter.
  One folder is one place to read.
- An agent reads a small file with more care. A sub-agent brief can include a complete file.
- A move with no change of text can be checked line by line. A rewording in the same PR cannot.

## Evidence

- A scratch script compared the old file with the 13 new files. Each of the 683 non-blank old lines
  is in exactly one new file, after the heading-level change and the link rewrite. The new files add
  only the two titles and the two link lists. `uv run pytest tools/tests` passed, with all links and
  anchors resolved.

## Alternatives rejected

- **Keep both names.** Agents confuse the two guides.
- **Move as one file, then split.** Each link would change twice, and each decided entry would get
  two `_Edited_` lines.
- **Keep a stub at the old path.** No exporter needs the old path: each exporter is implemented again
  from the new guide.
