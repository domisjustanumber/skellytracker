"""The bootstrap kit matches its live files, and its own decision log is valid (decision 0031)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import sync_bootstrap_kit as kit

REPO_ROOT = Path(kit.__file__).resolve().parents[1]
KIT_ROOT = REPO_ROOT / kit.KIT


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


def test_kit_tools_have_no_placeholders() -> None:
    tools = sorted((KIT_ROOT / "tools").rglob("*.py"))
    assert tools
    for path in tools:
        assert "{{" not in path.read_text(encoding="utf-8"), path


def test_every_kit_copy_has_a_live_file() -> None:
    for copy in kit.COPIES:
        assert (REPO_ROOT / copy.source).is_file(), copy.source
