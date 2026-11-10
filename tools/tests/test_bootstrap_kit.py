"""The bootstrap kit matches its live files (decisions 0031 and P3NK).

The kit is in the freemocap/project checkout. Its own tests are there. The copy test skips when
the checkout is not present, for example in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import sync_bootstrap_kit as kit

REPO_ROOT = Path(kit.__file__).resolve().parents[1]


@pytest.mark.skipif(not (REPO_ROOT / kit.KIT).is_dir(), reason=kit.NO_KIT)
def test_copies_match_their_live_files() -> None:
    assert kit.check(REPO_ROOT) == []


def test_every_kit_copy_has_a_live_file() -> None:
    for copy in kit.COPIES:
        assert (REPO_ROOT / copy.source).is_file(), copy.source


def test_every_block_has_its_live_file() -> None:
    for block in kit.BLOCKS:
        assert (REPO_ROOT / block.live).is_file(), block.live


LIVE = """# Live

## Rules

- Keep it ([ADR-JW9N](JW9N-restate.md)) on `development`.
- See ([Spec](spec.md)).

## Other

<!-- kit:one -->
- Shared (ADR-[0027](decisions/0027-x.md)).
  <!-- /kit -->
- Live only.
"""


def blocks_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kit_text: str) -> None:
    (tmp_path / "live.md").write_text(LIVE, encoding="utf-8")
    (tmp_path / "kit.md").write_text(kit_text, encoding="utf-8")
    monkeypatch.setattr(
        kit,
        "BLOCKS",
        (
            kit.Block("live.md", "kit.md", "## Rules", (("`development`", "`main`"),)),
            kit.Block("live.md", "kit.md", "one"),
        ),
    )


KIT_TEXT = "# Kit\n\n## Rules\n\nold\n\n## Other\n\n<!-- kit:one -->\nold\n<!-- /kit -->\n- Kit only.\n"


def test_write_then_check_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocks_repo(tmp_path, monkeypatch, KIT_TEXT)
    assert len(kit.block_errors(tmp_path)) == 2
    kit.write_blocks(tmp_path)
    assert kit.block_errors(tmp_path) == []
    text = (tmp_path / "kit.md").read_text(encoding="utf-8")
    # Citations of single entries go, other links stay, edits apply, text outside the blocks stays.
    assert "- Keep it on `main`.\n- See ([Spec](spec.md)).\n" in text
    assert "<!-- kit:one -->\n- Shared.\n<!-- /kit -->\n- Kit only.\n" in text
    kit.write_blocks(tmp_path)
    assert (tmp_path / "kit.md").read_text(encoding="utf-8") == text


@pytest.mark.parametrize(
    ("kit_text", "message"),
    [
        ("## Rules\n\n<!-- kit:one -->\n", "kit.md:3: kit:one has no <!-- /kit -->"),
        ("## Rules\n\n<!-- /kit -->\n", "kit.md:3: <!-- /kit --> closes no block"),
        ("## Rules\n<!-- kit:one -->\n<!-- kit:two -->\n<!-- /kit -->\n", "kit.md:3: kit:two starts inside kit:one"),
        ("## Rules\n<!-- kit:one -->\n<!-- /kit -->\n<!-- kit:one -->\n<!-- /kit -->\n", "kit.md:4: a second block kit:one"),
        ("## Rules\n", "kit.md: no block one"),
        ("## Rules\n<!-- kit:one -->\n<!-- /kit -->\n<!-- kit:new -->\n<!-- /kit -->\n", "kit.md: kit:new is not in BLOCKS"),
    ],
)
def test_marker_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kit_text: str, message: str) -> None:
    blocks_repo(tmp_path, monkeypatch, kit_text)
    assert any(message in e for e in kit.block_errors(tmp_path)), kit.block_errors(tmp_path)
    with pytest.raises(SystemExit):
        kit.write_blocks(tmp_path)
    assert (tmp_path / "kit.md").read_text(encoding="utf-8") == kit_text


def test_overlapping_blocks_are_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A marker block inside a section block would make --write delete kit lines, so it is an error."""
    kit_text = "## Other\n\n<!-- kit:one -->\nold\nold\nold\n<!-- /kit -->\n\n## Kept\n\nkit only\n"
    blocks_repo(tmp_path, monkeypatch, kit_text)
    monkeypatch.setattr(
        kit, "BLOCKS", (kit.Block("live.md", "kit.md", "## Other"), kit.Block("live.md", "kit.md", "one"))
    )
    assert "kit.md: one overlaps ## Other; blocks do not overlap" in kit.block_errors(tmp_path)
    with pytest.raises(SystemExit):
        kit.write_blocks(tmp_path)
    assert (tmp_path / "kit.md").read_text(encoding="utf-8") == kit_text


@pytest.mark.parametrize(
    ("text", "after"),
    [
        ("a ([ADR-JW9N](JW9N-x.md)).", "a."),
        ("a ([z934](z934-x.md)).", "a."),
        ("a (ADR-[0027](decisions/0027-x.md)).", "a."),
        ("a ([Spec](spec.md)).", "a ([Spec](spec.md))."),
        ("a ([ADR-AB12](https://github.com/o/r/blob/0123/decisions/AB12-x.md)).", "a ([ADR-AB12](https://github.com/o/r/blob/0123/decisions/AB12-x.md))."),
        ("a ([ADR-AB12](AB12-x.md); see [Rules](README.md#rules)).", "a ([ADR-AB12](AB12-x.md); see [Rules](README.md#rules))."),
    ],
)
def test_citation_filter(text: str, after: str) -> None:
    assert kit.CITATION.sub("", text) == after
