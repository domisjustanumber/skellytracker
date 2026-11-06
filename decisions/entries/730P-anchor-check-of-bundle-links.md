# 730P — Anchor check of bundle links

**Status:** accepted, 2026-11-06 (user; PR: pending).

## Decision

The user approved a fix: `pack` and `verify` check the `#anchor` of each link of a proposal.

1. **Rule.** Each relative link of a `.md` file of a proposal bundle must resolve from the record
   path: its file is a file of the bundle or of skellytracker, and its `#anchor` is a heading of
   that Markdown file. A same-file link `#x` also counts. A link in a fenced block or in inline code
   is not a link. [Pack a version](../../specs/model-sidecar/model-addition-workflow/hand-over.md#pack-a-version)
   states it.
2. **Check.** `link_findings` of `tools/intake_bundle.py` gives one text for each link that fails.
   `pack` refuses the bundle, and `verify` gives a finding. It uses `check_links.links` and
   `check_links.anchors`, the code of the link test.

## Reason

A record is a byte copy of a bundle version, and `tools/tests/test_links.py` checks its links with
their anchors. `verify` checked only the file part of a link, and it skipped same-file links.
`pack` checked no link. Thus `proposal-model-id-suffix@openmmlab-exporter` v1 passed `verify`, and
its record failed the link test: three links name the heading "Keypoint detector id", which only
the proposed text adds. The session cannot edit a record, so the bundle got `needs-contributor`
after the copy. Exporter agents run `pack` and not `verify`, so only a check in `pack` tells them
before the hand-over.

## Consequences

- A proposal cannot link to a heading that it adds. It writes the heading name as text, or it quotes
  the new text in a fenced block.
- A heading that changes after `pack` can make a link fail at `verify`. Then the response is
  `needs-contributor`, because the record would fail the link test.
