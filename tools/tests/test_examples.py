"""The spec's reference examples parse, resolve and have provenance.

The examples under `specs/sidecar/examples/` follow the package's `detectors/`
layout, so their `$ref` paths resolve with that folder as the cache dir. They
are not validated against `SidecarModel`: it does not load `vNEXT` sidecars yet.
"""

from pathlib import Path

import pytest
import yaml

from skellytracker.core.sidecar.resolution import resolve_sidecar_composition

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "specs" / "sidecar" / "examples"
INVENTORY_PATH = REPO_ROOT / "specs" / "sidecar" / "inventory.yaml"
SHARED_DIR = EXAMPLES_ROOT / "detectors" / "shared"
PACKAGE_SHARED_DIR = REPO_ROOT / "skellytracker" / "core" / "detectors" / "shared"

PROVENANCE_KEYS = {
    "source",
    "exporter",
    "exporter_path",
    "kind",
    "exporter_layout_path",
    "tracked",
    "commit",
    "edits",
    "notes",
}


def example_paths() -> list[Path]:
    """Every example sidecar: a YAML file outside `shared/`."""
    return sorted(
        p
        for p in (EXAMPLES_ROOT / "detectors").rglob("*.yaml")
        if SHARED_DIR not in p.parents
    )


def inventory() -> dict:
    return yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))


def example_key(path: Path) -> str:
    return path.relative_to(EXAMPLES_ROOT).as_posix()


def test_there_are_examples() -> None:
    assert example_paths()


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_resolves(path: Path) -> None:
    resolved = resolve_sidecar_composition(path, EXAMPLES_ROOT)
    assert resolved["model_id"] == path.stem
    assert resolved["schema_version"] == "vNEXT"


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_follows_the_storage_layout(path: Path) -> None:
    parts = path.relative_to(EXAMPLES_ROOT / "detectors").parts
    if parts[0] == "object_detectors":
        assert len(parts) == 3, parts
    else:
        assert parts[0] == "keypoint_detectors"
        assert len(parts) == 4, parts
        assert parts[2] in {"hand", "face", "body", "wholebody"}, parts


def test_every_example_has_one_provenance_entry() -> None:
    entries = inventory()["examples"]
    assert set(entries) == {example_key(p) for p in example_paths()}


@pytest.mark.parametrize("key", sorted(inventory()["examples"]))
def test_provenance_entry_is_complete(key: str) -> None:
    entry = inventory()["examples"][key]
    assert set(entry) == PROVENANCE_KEYS
    assert entry["kind"] in {"export", "forecast"}
    assert isinstance(entry["tracked"], bool)
    assert isinstance(entry["edits"], list)


def fragment_paths() -> list[Path]:
    return sorted(SHARED_DIR.rglob("*.yaml"))


@pytest.mark.parametrize(
    "fragment", fragment_paths(), ids=lambda p: p.relative_to(SHARED_DIR).as_posix()
)
def test_shared_fragment_equals_its_package_copy(fragment: Path) -> None:
    package_copy = PACKAGE_SHARED_DIR / fragment.relative_to(SHARED_DIR)
    assert fragment.read_bytes().replace(b"\r\n", b"\n") == (
        package_copy.read_bytes().replace(b"\r\n", b"\n")
    )


@pytest.mark.parametrize(
    "fragment", fragment_paths(), ids=lambda p: p.relative_to(SHARED_DIR).as_posix()
)
def test_shared_fragment_is_used_by_an_example(fragment: Path) -> None:
    """A copy that no example refers to is stale: delete it."""
    name = fragment.relative_to(SHARED_DIR).as_posix()
    assert any(
        f"shared/{name}" in p.read_text(encoding="utf-8") for p in example_paths()
    ), f"no example refers to shared/{name}"
