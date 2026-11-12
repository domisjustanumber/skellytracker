"""The sidecar spec does not use a name that decision 88WQ retires.

Spec version 2.0.0 keeps no alias for an old name. The frozen texts keep their old names: the
proposal records, the decision logs, the changelog with its old-to-new ID map and the frozen
``sidecar-spec.md``. This list holds only the old names that no current text uses for another
meaning.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# shortcut: the pipeline spec adopts the 88WQ names in a later commit group; add specs/pipeline then.
SPECS = (ROOT / "specs" / "model-sidecar",)
FROZEN = ("proposals/", "decisions/", "changelog.md", "sidecar-spec.md")
SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py"}
RETIRED = {
    "pose_estimator": r"\bpose_estimator\b",
    "post.pose.*": r"\bpost\.pose\.",
    "post.det.*": r"\bpost\.det\.",
    "pose: block": r"^\s*pose:",
    "tracked_points": r"\btracked_points\b",
    "class_id": r"\bclass_id\b",
    "class_id_base": r"\bclass_id_base\b",
    "class_id_map": r"\bclass_id_map\b",
    "is_person_only": r"\bis_person_only\b",
    "person_class_id": r"\bperson_class_id\b",
    "confidence_threshold_default": r"\bconfidence_threshold_default\b",
    "box_scale": r"\bbox_scale\b",
    "coordinate_scale": r"\bcoordinate_scale\b",
    "overlay.groups": r"\boverlay\.groups\b",
    "connections": r"`connections`|\bconnections:",
    "expansion_ratio": r"\bexpansion_ratio\b",
}


def live_files() -> list[Path]:
    files = []
    for spec in SPECS:
        for path in sorted(spec.rglob("*")):
            rel = path.relative_to(spec).as_posix()
            if path.suffix in SUFFIXES and path.is_file() and not any(part in rel for part in FROZEN):
                files.append(path)
    return files


@pytest.mark.parametrize("name", RETIRED)
def test_no_live_spec_file_uses_a_retired_name(name: str) -> None:
    pattern = re.compile(RETIRED[name], re.MULTILINE)
    hits = [
        f"{path.relative_to(ROOT).as_posix()}:{number}"
        for path in live_files()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if pattern.search(line)
    ]
    assert not hits, f"{name} is retired by 88WQ: " + ", ".join(hits)


def test_the_frozen_texts_are_skipped() -> None:
    rels = {path.relative_to(ROOT).as_posix() for path in live_files()}
    assert not any("/proposals/" in rel or rel.endswith("/changelog.md") for rel in rels)
    assert "specs/model-sidecar/README.md" in rels
