"""Every relative link in `AGENTS.md`, `specs/` and `notes/` resolves."""

from pathlib import Path

import pytest
from check_links import anchors, check_file, github_slug, links, markdown_files

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "path",
    markdown_files(REPO_ROOT),
    ids=lambda p: p.relative_to(REPO_ROOT).as_posix(),
)
def test_relative_links_resolve(path: Path) -> None:
    assert check_file(path, REPO_ROOT) == []


@pytest.mark.parametrize(
    ("heading", "slug"),
    [
        ("`input.resize`", "inputresize"),
        (
            "`base` — inherit from another sidecar and override",
            "base--inherit-from-another-sidecar-and-override",
        ),
        (
            "`packed_keypoints` (bottom-up packed rows)",
            "packed_keypoints-bottom-up-packed-rows",
        ),
        ("Changes in this revision (`vNEXT`)", "changes-in-this-revision-vnext"),
        ("`sizes.<size>.onnx.batch_artifacts`", "sizessizeonnxbatch_artifacts"),
        ("Text <em>tag</em> here", "text-tag-here"),
    ],
)
def test_github_slug(heading: str, slug: str) -> None:
    assert github_slug(heading) == slug


def test_repeated_headings_get_suffixes(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Notes\n\n## Notes\n\n## Notes\n", encoding="utf-8")
    assert anchors(doc) == {"notes", "notes-1", "notes-2"}


def test_links_in_code_are_skipped(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(
        "See [real](other.md).\n\n```yaml\nx: [a](missing.md)\n```\n\n`[b](missing.md)`\n",
        encoding="utf-8",
    )
    assert links(doc) == [(1, "other.md")]


def test_broken_file_and_anchor_are_reported(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Present\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    doc.write_text(
        "[ok](target.md#present) [bad](target.md#absent) [gone](none.md) [web](https://example.com)\n",
        encoding="utf-8",
    )
    errors = check_file(doc, tmp_path)
    assert errors == [
        "doc.md:1: missing anchor target.md#absent",
        "doc.md:1: missing file none.md",
    ]
