# KZ9J — Spec change: model-id-suffix-rtmo-removed

**Status:** done, 2026-11-09 (user; PR: pending).

## Decision

The user accepted the follow-up on 2026-11-09. The record is
[`proposal.md`](../../proposals/model-id-suffix-rtmo-removed/proposal.md)
(proposal-model-id-suffix-rtmo-removed@openmmlab-exporter@v1).

- Kind: a follow-up of `proposal-model-id-suffix@openmmlab-exporter`
  ([ADR-52NQ](52NQ-model-id-suffix.md)). The session lands both in one content commit.
- Sections: [`common.identity`](../../common/identity.md) and
  [`format.file_layout`](../../format/file-layout.md), as the base.
- Change: two rows of part 2.1 and one row of part 7 of the base. The Authoring guidance sentence
  about older ids names only `rtmw-wholebody`. The Re-export row drops `rtmo-body7`. The part 7 row
  of `rtmo-body7` is a removal under
  [ADR-YS4C](../../../../decisions/entries/YS4C-example-removal-by-a-user-ruling.md), not
  `needs-export`, and it is not a request.
- Target spec version: `2.0.0`.
- Supersedes on acceptance: none.

## Reason

The user ruled on 2026-11-09 that `rtmo-body7` gets no rebuild (ADR-YS4C item 7). The base text says
that the re-export request rebuilds it. Response r6 of the base asked for this follow-up, because the
session can make editorial fixes only.

## Evidence

Parity: none. A name changes no tensor. The follow-up has no reference file and no vector case.

## Open work

See [open-work.md](../open-work.md).

