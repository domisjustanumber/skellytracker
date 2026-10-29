"""Each proposal record is a byte copy of one bundle version.

The rules are in `specs/model-sidecar/model-addition-workflow/hand-over.md`. A record folder holds
the `manifest.yaml` of its bundle version. Each file that the manifest lists keeps its SHA-256,
except a file that `redactions.yaml` lists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROPOSALS = REPO_ROOT / "specs" / "model-sidecar" / "proposals"
VECTOR_LIMIT = 256 * 1024

MANIFESTS = sorted(PROPOSALS.rglob("manifest.yaml"))


def test_each_record_folder_has_a_manifest() -> None:
    folders = {p.name for p in PROPOSALS.iterdir() if p.is_dir()}
    without = {f for f in folders if not (PROPOSALS / f / "manifest.yaml").is_file()}
    assert without == set()


@pytest.mark.parametrize("manifest_path", MANIFESTS, ids=lambda p: p.parent.relative_to(PROPOSALS).as_posix())
def test_record_files_match_their_manifest(manifest_path: Path) -> None:
    folder = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    redactions_path = folder / "redactions.yaml"
    redacted = set()
    if redactions_path.is_file():
        redacted = {r["path"] for r in yaml.safe_load(redactions_path.read_text(encoding="utf-8"))}
    on_disk = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    on_disk -= {"manifest.yaml", "redactions.yaml"}
    on_disk = {p for p in on_disk if not p.startswith("contributions/")}
    assert on_disk == {f["path"] for f in manifest["files"]}, "a record holds only its bundle files"
    for item in manifest["files"]:
        if item["path"] in redacted:
            continue
        data = (folder / item["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]


def test_record_vector_files_are_256_kib_or_smaller() -> None:
    large = [
        p.relative_to(PROPOSALS).as_posix()
        for p in PROPOSALS.rglob("*.yaml")
        if p.parent.name == "vectors" and p.stat().st_size > VECTOR_LIMIT
    ]
    assert large == []
