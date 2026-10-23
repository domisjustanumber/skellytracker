"""The spec's reference examples parse, resolve, hold correct hashes and have provenance.

The examples under `specs/sidecar/examples/` follow the package's `detectors/`
layout, so their `$ref` paths resolve with that folder as the sidecar root. They
are not validated against `SidecarModel`: it does not load `vNEXT` sidecars yet.
They resolve with `sidecar_refs.resolve`, because the package resolver refuses
`sha256` next to `$ref`.
"""

import re
from pathlib import Path

import pytest
import sidecar_refs
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "specs" / "sidecar" / "examples"
INVENTORY_PATH = REPO_ROOT / "specs" / "sidecar" / "inventory.yaml"
SHARED_DIR = EXAMPLES_ROOT / "detectors" / "shared"
PACKAGE_SHARED_DIR = REPO_ROOT / "skellytracker" / "core" / "detectors" / "shared"

PROVENANCE_KEYS = {
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
    resolved = sidecar_refs.resolve(path, EXAMPLES_ROOT)
    assert resolved["model_id"] == path.stem
    assert resolved["schema_version"] == "vNEXT"


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_passes_the_reference_hash_check(path: Path) -> None:
    """`tools/sidecar_refs.py --check <example>` passes (the same root and the same checks)."""
    errors = sidecar_refs.check(path)
    assert not errors, "\n".join(errors)


SOURCE_NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_has_a_source(path: Path) -> None:
    """V-common.identity-4 to V-common.identity-6."""
    source = yaml.safe_load(path.read_text(encoding="utf-8"))["source"]
    assert isinstance(source, dict) and set(source) == {"name", "version"}
    assert isinstance(source["name"], str) and SOURCE_NAME.fullmatch(source["name"])
    assert isinstance(source["version"], str) and source["version"]


def placeholder_scan_paths() -> list[Path]:
    """Every YAML file of the package, the spec and the tools, and every Markdown file of the spec."""
    paths = [
        p
        for folder in ("skellytracker", "specs", "tools")
        for pattern in ("*.yaml", "*.yml")
        for p in (REPO_ROOT / folder).rglob(pattern)
    ]
    paths += (REPO_ROOT / "specs").rglob("*.md")
    return sorted(p for p in paths if EXAMPLES_ROOT not in p.parents)


def test_the_placeholder_scan_reads_the_sidecars_and_the_spec() -> None:
    shown = {p.relative_to(REPO_ROOT).as_posix() for p in placeholder_scan_paths()}
    assert "specs/sidecar/common/sizes-and-artifacts.md" in shown
    assert (
        "skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml"
        in shown
    )
    assert not any(name.startswith("specs/sidecar/examples/") for name in shown)


def test_no_file_outside_the_examples_holds_the_placeholder() -> None:
    """The placeholder hash is valid only under `specs/sidecar/examples/` (V-common.sizes_and_artifacts-12)."""
    holders = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in placeholder_scan_paths()
        if sidecar_refs.PLACEHOLDER in p.read_text(encoding="utf-8")
    ]
    assert not holders, holders


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
