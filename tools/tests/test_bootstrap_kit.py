"""The bootstrap kit matches its live files, and its own decision log is valid (decision 0031)."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest
import sync_bootstrap_kit as kit

REPO_ROOT = Path(kit.__file__).resolve().parents[1]
KIT_ROOT = REPO_ROOT / kit.KIT
MODULE_ROOT = KIT_ROOT.parent / "module"


def load(path: Path, name: str) -> ModuleType:
    """Import a kit tool from its file, under a name that does not hide the live tool."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_copies_match_their_live_files() -> None:
    assert kit.check(REPO_ROOT) == []


def test_kit_decision_log_passes_the_kit_check() -> None:
    cdl = load(KIT_ROOT / "tools" / "check_decision_log.py", "kit_check_decision_log")
    assert cdl.check(KIT_ROOT) == []


def test_kit_with_two_module_logs_passes_the_kit_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A repo made from the kit with the module template in server/ and ui/ passes (ADR-GN3D)."""
    shutil.copytree(KIT_ROOT, tmp_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    for module in ("server", "ui"):
        shutil.copytree(MODULE_ROOT, tmp_path / module)
    cdl = load(tmp_path / "tools" / "check_decision_log.py", "kit_check_decision_log_modules")
    links = load(tmp_path / "tools" / "check_links.py", "kit_check_links_modules")
    logs = (cdl.LOG_DIR, Path("server/decisions"), Path("ui/decisions"))
    monkeypatch.setattr(cdl, "LOG_DIRS", logs)
    assert cdl.present_logs(tmp_path) == list(logs)
    assert cdl.check(tmp_path) == []
    files = links.markdown_files(tmp_path)
    assert tmp_path / "server" / "decisions" / "README.md" in files
    assert [e for f in files for e in links.check_file(f, tmp_path)] == []


def test_kit_tools_have_no_placeholders() -> None:
    tools = sorted((KIT_ROOT / "tools").rglob("*.py"))
    assert tools
    for path in tools:
        assert "{{" not in path.read_text(encoding="utf-8"), path


def test_every_kit_copy_has_a_live_file() -> None:
    for copy in kit.COPIES:
        assert (REPO_ROOT / copy.source).is_file(), copy.source
