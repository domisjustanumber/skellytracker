"""The docs site names each exported name, and its pages have a title, live links and the word "system"."""

from __future__ import annotations

import subprocess
from pathlib import Path

import check_docs_site as cds
import pytest

REPO_ROOT = Path(cds.__file__).resolve().parents[1]

PAGE = """---
title: API
---

| Signature | Result |
|-----------|--------|
| `start_pipeline(config)` | A run. |
| `old_call(x)` | Gone. |

| Member | Description |
|--------|-------------|
| `close()` | A method. |

```python
from skellytracker.core.pipelines import Frame
```
"""


def test_repository_docs_site_has_no_findings() -> None:
    assert cds.check(REPO_ROOT) == []


def test_exported_names_read_all_or_the_package_imports(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('from x import y\n__all__ = ["y", "z"]\n', encoding="utf-8")
    (tmp_path / "b.py").write_text(
        "import os\nfrom beartype.claw import f\nfrom skellytracker.m import a, b as c\n", encoding="utf-8"
    )
    assert cds.exported_names(tmp_path / "a.py") == ["y", "z"]
    assert cds.exported_names(tmp_path / "b.py") == ["a", "c"]
    (tmp_path / "c.py").write_text("import os\n\n\ndef shown():\n    pass\n\n\ndef _hidden():\n    pass\n", encoding="utf-8")
    assert cds.exported_names(tmp_path / "c.py") == ["shown"]


def test_a_name_counts_only_in_code() -> None:
    page = PAGE + "\nThe text names PipelineRun, but not in code.\n"
    assert cds.missing_names(page, ["Frame", "start_pipeline", "PipelineRun", "run"]) == ["PipelineRun", "run"]


def test_a_signature_that_no_module_exports_is_dead() -> None:
    assert cds.dead_names(PAGE, {"start_pipeline"}) == ["old_call"]


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_page_rules(tmp_path: Path) -> None:
    write(tmp_path, "docs/a/target.mdx", "---\ntitle: T\n---\n")
    write(tmp_path, "docs/dev/index.mdx", "---\ntitle: D\n---\n")
    page = write(
        tmp_path,
        "docs/a/page.mdx",
        "---\ntitle: P\n---\n"
        "[ok](./target#x) [ok](../dev) [ok](/abs) [ok](https://x.org) [bad](./gone)\n"
        "Run it on your machine or PC.\n"
        "`a machine and [code](./gone)` in a span pass.\n"
        "```\nmachine PC [x](./gone)\n```\n"
        "Machine learning, a PCB and PCs.\n",
    )
    assert cds.page_findings(page, tmp_path) == [
        "docs/a/page.mdx:4: the link ./gone goes to no page file",
        'docs/a/page.mdx:5: use "system", not "machine"',
        'docs/a/page.mdx:5: use "system", not "PC"',
        'docs/a/page.mdx:10: use "system", not "Machine"',
        'docs/a/page.mdx:10: use "system", not "PCs"',
    ]


def test_a_page_with_no_title_is_reported(tmp_path: Path) -> None:
    for name, text in {"none.mdx": "# Page\n", "empty.mdx": "---\nsidebar_position: 1\n---\n"}.items():
        assert cds.page_findings(write(tmp_path, name, text), tmp_path) == [
            f"{name}:1: the page has no front matter with title"
        ]


def test_staged_reminder() -> None:
    assert cds.staged_reminder(["skellytracker/core/model_zoo/pipelines/new.pipeline.yaml", "README.md"]) == (
        "docs site: the commit changes skellytracker/core/model_zoo/pipelines/new.pipeline.yaml and no file under"
        " skellytracker-docs/. If a page states a changed fact, load the skill update-docs-site"
        " (.claude/skills/update-docs-site/SKILL.md)."
    )
    assert cds.staged_reminder(["pyproject.toml", "skellytracker-docs/docs/intro.mdx"]) is None
    assert cds.staged_reminder(["skellytracker/core/pipelines/run.py"]) is None


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)  # noqa: S603, S607


def test_staged_mode_always_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    assert cds.main(["check_docs_site.py", "--staged"]) == 0
    assert capsys.readouterr().out.startswith("docs site: the staged files are not available")
    git(tmp_path, "init", "-q")
    write(tmp_path, "pyproject.toml", "[project]\n")
    git(tmp_path, "add", "pyproject.toml")
    assert cds.main(["check_docs_site.py", "--staged"]) == 0
    assert capsys.readouterr().out.startswith("docs site: the commit changes pyproject.toml and no file")
