"""Each proposal record is a byte copy of one bundle version.

The rules are in `specs/model-sidecar/model-addition-workflow/hand-over.md`. A record folder holds
the `manifest.yaml` of its bundle version. Each file that the manifest lists keeps its SHA-256,
except a file that `redactions.yaml` lists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import intake_bundle as ib
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


def record_vector_problems(proposals: Path) -> list[str]:
    """Run the vector form check of `verify` on each record vector file.

    A contribution record in `<slug>/contributions/<contributor>/` also uses the reference and
    part 2.4 of its owner record `<slug>/`.
    """
    found = []
    for path in sorted(proposals.rglob("vectors/*.yaml")):
        folders = list(dict.fromkeys([path.parent.parent, proposals / path.relative_to(proposals).parts[0]]))
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        rel = path.relative_to(proposals).as_posix()
        found += [f"{rel}: {p}" for p in ib.vector_problems(data, path.stem, folders)]
    return found


def test_record_vector_files_have_the_vector_form() -> None:
    assert record_vector_problems(PROPOSALS) == []


def test_the_record_vector_check_finds_a_form_problem(tmp_path: Path) -> None:
    landed = yaml.safe_load((REPO_ROOT / "specs/model-sidecar/vectors/post.det.selection.nms.yaml").read_text(encoding="utf-8"))
    good = {**landed, "cases": landed["cases"][:1]}
    bad = {**good, "tolerance": -1}
    for rel, data in (("slug/vectors", good), ("slug/contributions/c/vectors", bad)):
        (tmp_path / rel).mkdir(parents=True)
        (tmp_path / rel / "post.det.selection.nms.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    assert record_vector_problems(tmp_path) == [
        "slug/contributions/c/vectors/post.det.selection.nms.yaml: "
        "post.det.selection.nms: tolerance must be a number of 0 or more"
    ]


def test_record_vector_files_are_256_kib_or_smaller() -> None:
    large = [
        p.relative_to(PROPOSALS).as_posix()
        for p in PROPOSALS.rglob("*.yaml")
        if p.parent.name == "vectors" and p.stat().st_size > VECTOR_LIMIT
    ]
    assert large == []
