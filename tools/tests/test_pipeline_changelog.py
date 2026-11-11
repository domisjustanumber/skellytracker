"""Each change of a normative heading or a `V-` rule of the pipeline spec comes with a `Row` line.

ADR-3SF2 item 5: `specs/pipeline/changelog.md` starts with the first content commit. Each content
change adds a summary row and a `Row` line with the normative fingerprint of the pipeline sections.
The form of the changelog and the fingerprint are those of the sidecar changelog
(`test_changelog_revision.py`): this test calls its `assert_last_row`.

The pipeline section files are each `specs/pipeline/*.md` with front matter and each
`specs/pipeline/nodes/*.md`. `README.md`, `changelog.md`, `AGENTS.md`, `CLAUDE.md` and
`decisions/` are not section files. A node file must have front matter.

The test skips when `specs/pipeline/changelog.md` does not exist.
"""

from pathlib import Path

import pytest
from test_changelog_revision import assert_last_row

PIPELINE_DIR = Path(__file__).resolve().parents[2] / "specs" / "pipeline"
CHANGELOG = PIPELINE_DIR / "changelog.md"
NOT_SECTIONS = {"README.md", "changelog.md", "AGENTS.md", "CLAUDE.md"}


def section_files(base: Path = PIPELINE_DIR) -> list[Path]:
    """Return the pipeline section files, sorted by folder and name."""
    top = [
        path
        for path in sorted(base.glob("*.md"))
        if path.name not in NOT_SECTIONS and path.read_text(encoding="utf-8").startswith("---\n")
    ]
    return [*top, *sorted((base / "nodes").glob("*.md"))]


@pytest.mark.skipif(not CHANGELOG.is_file(), reason="specs/pipeline/changelog.md does not exist yet")
def test_the_last_row_line_holds_the_last_row_and_the_fingerprint() -> None:
    assert_last_row(CHANGELOG, section_files())


def test_the_section_files_are_the_front_matter_files_and_the_node_files(tmp_path: Path) -> None:
    for name, text in {
        "README.md": "---\nid: x\n---\n",
        "changelog.md": "---\nid: x\n---\n",
        "graph.md": "---\nid: pipeline.graph\n---\n# Graph\n",
        "notes.md": "# Notes without front matter\n",
        "nodes/gate.md": "---\nid: node.gate\n---\n# Gate\n",
        "decisions/README.md": "---\nid: x\n---\n",
    }.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    found = [path.relative_to(tmp_path).as_posix() for path in section_files(tmp_path)]
    assert found == ["graph.md", "nodes/gate.md"]
