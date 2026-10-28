# k6dz — The sidecar spec folder is `specs/model-sidecar/`

**Status:** superseded by [D9VT](D9VT-decision-log-move.md), 2026-10-28 (user; PR: pending).

## Decision

1. **New name.** The sidecar spec folder moves from `specs/sidecar/` to
   [`specs/model-sidecar/`](../../specs/model-sidecar/README.md). The permanent entry point moves
   from `specs/sidecar-spec.md` into the folder:
   [`specs/model-sidecar/sidecar-spec.md`](../../specs/model-sidecar/sidecar-spec.md). It keeps each
   old heading as an anchor. No stub stays at an old path.
2. **A move only.** The move changes no rule. The section files change only their paths to the
   folder. The section IDs, the rule IDs, the anchors and the `schema_version` values do not change.
   The changelog gets no row, because no sidecar changes.
3. **References.** Each link and each path to the old folder or to the old entry point goes to the
   new path. This applies to `AGENTS.md`, the skills, the exporter guide, the templates, the spec
   files, the proposals, the vectors, the tools, CI and the `proposed` entries. A decided entry gets only its link repairs and
   a link-repair `_Edited_` line. A plain-text mention of the old path in a decided entry stays,
   because it is history ([0034](0034-sidecar-guide-folder.md)). A text that quotes a path in an
   exporter repo keeps that path.
4. **Proposal copies.** A recorded proposal changes each path under `specs/sidecar/` to the same path
   under `specs/model-sidecar/`, and `specs/sidecar-spec.md` to
   `specs/model-sidecar/sidecar-spec.md`. A new copy of a changed exporter proposal makes the same
   change. Step 3 of the skill `propose-sidecar-change` gives this copy rule.
5. **Code citations.** The spec citations in the docstrings and comments of the package code change
   to `specs/model-sidecar/sidecar-spec.md, "<heading>"`. This is an exception to the rule that the
   code does not change in the spec-build stage ([0014](0014-spec-lifecycle.md)). The user decided
   it on 2026-10-26. The exception allows only these path changes. The citation test of
   `tools/tests/test_traceability.py` reads the new path.
6. **The split checker.** `tools/check_split_verbatim.py`, `tools/split_manifest.yaml` and
   `tools/tests/test_check_split_verbatim.py` keep the old path. They check the split of
   `specs/sidecar-spec.md` into the old folder, and that split is history.

## Reason

- The name "sidecar" does not tell what a sidecar describes. The package also has
  `skellytracker/core/sidecar/` (the loader) and `skellytracker/tests/sidecar/`. The name
  `model-sidecar` tells that the folder holds the spec of the model sidecars.
- A move with no change of rule can be checked with `git diff -M`. A rewording in the same PR cannot.

## Consequences

- The exporter repos cite the old folder in their agent files and notes, for example
  `../freemocap/skellytracker/specs/sidecar/`. These paths do not resolve after the move. This
  repository does not change an exporter repo. The [open work](open-work.md) has the item.
- A link to `specs/sidecar-spec.md#<anchor>` from outside this repository does not resolve after the
  move. The same anchor resolves in the new entry point.

## Alternatives rejected

- **Keep a stub at the old path.** An agent can read the stub as the spec. Two folders also make each
  search for the spec path give two results.
- **Rename only the title of the spec.** The folder name stays the same as the code folders
  `core/sidecar/` and `tests/sidecar/`.
