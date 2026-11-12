# 1HKJ — The link check skips the frozen proposal records

**Status:** absorbed into [`check_links.py`](../../tools/check_links.py), [`hand-over.md#tracked-records`](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records), 2026-11-12 (absorb sweep, user; PR: pending).

## Decision

1. `tools/check_links.py` does not check the links of the files in the folders of
   `specs/model-sidecar/proposals/`. It checks `specs/model-sidecar/proposals/README.md`.
2. A record stays a byte copy of its bundle version. Its links can name a file, an anchor or an ID
   that a later commit moved or renamed. Do not repair them.
3. A reader resolves an old ID with the old-to-new map of the changelog row of the rename.

## Reason

- A record is a byte copy, and only a redaction can change it
  ([Tracked records](../../specs/model-sidecar/model-addition-workflow/hand-over.md#tracked-records)).
- A record is evidence of what a contributor sent, as a decided entry is evidence of a decision.
  A decided entry keeps its old IDs. A record keeps its old links.
- The move of the `post/` sections into `post/object/` and `post/keypoint/`
  ([ADR-88WQ](88WQ-sidecar-vocabulary.md)) broke a link in the record `simcc-score-rule`. Each later
  move or rename of a spec section can break more.

## Alternatives rejected

- A "Moved to" stub file at each old path: it adds files to `post/` for each record link.
- A link repair in the record: it breaks the byte copy and the hashes of the manifest.

## Open work

[open-work.md](../open-work.md)
