"""The spec's reference examples parse, resolve, hold correct hashes and have provenance.

The examples under `specs/model-sidecar/examples/` follow the package's `detectors/`
layout, so their `$ref` paths resolve with that folder as the sidecar root. They
are not validated against `SidecarModel`: it does not load `vNEXT` sidecars yet.
They resolve with `sidecar_refs.resolve`, because the package resolver refuses
`sha256` next to `$ref`.

Every other YAML file under the examples is a fragment, in `shared/` or next to
a sidecar. A fragment has one source: a package copy with the same bytes, or a
`fragments` entry in `inventory.yaml` (ADR-yve0).
"""

import functools
import re
from pathlib import Path

import pytest
import sidecar_refs
import yaml
from intake_bundle import FRAGMENT_KEYS, INVENTORY_KEYS, OPTIONAL_INVENTORY_KEYS

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "specs" / "model-sidecar" / "examples"
INVENTORY_PATH = REPO_ROOT / "specs" / "model-sidecar" / "inventory.yaml"
EXAMPLES_DETECTORS = EXAMPLES_ROOT / "detectors"
PACKAGE_DETECTORS = REPO_ROOT / "skellytracker" / "core" / "detectors"


def is_sidecar(path: Path) -> bool:
    """The rule of `tools/sidecar_trace.py`: `schema_version`, and `model_id` equal to the file name."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return (
        isinstance(data, dict)
        and "schema_version" in data
        and data.get("model_id") == path.stem
    )


def example_paths() -> list[Path]:
    """Every example sidecar."""
    return sorted(p for p in EXAMPLES_DETECTORS.rglob("*.yaml") if is_sidecar(p))


def inventory() -> dict:
    return yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))


def fragment_entries() -> dict:
    return inventory().get("fragments") or {}


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


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_uses_one_batch_form(path: Path) -> None:
    """V-common.sizes_and_artifacts-13, V-common.batch_conversion-3 and V-common.batch_conversion-4."""
    resolved = sidecar_refs.resolve(path, EXAMPLES_ROOT)
    keys = {tuple(size["onnx"]["batch_artifacts"]) for size in resolved["sizes"].values()}
    assert len(keys) == 1 and next(iter(keys)) in {("3",), ("1",), ("dynamic",)}, keys
    conversion = (resolved.get("batching") or {}).get("batch_conversion")
    assert (keys == {("3",)}) == (conversion is not None)
    assert conversion in (None, {"profile_id": "static-batch-v1", "source_batch_size": 3})


SPEC_ROOT = REPO_ROOT / "specs" / "model-sidecar"
# The keys of these maps are names (sizes, batch sizes, precisions, groups), not fields.
NAME_KEYED_MAPS = {
    "sizes",
    "batch_artifacts",
    "precision_artifacts",
    "dtype",
    "normalization_by_precision",
    "groups",
}
# These map keypoint names to sources. The check does not read inside them.
KEYPOINT_MAPS = {"canonical_mapping", "derived_points"}


@functools.cache
def defined_keys() -> frozenset[str]:
    """Each name in backticks in a heading or a Field table of the spec index or a section file.

    A dotted name such as `pose.connections[].edges` defines each of its parts. The index gives the
    top-level keys, for example `batching`.
    shortcut: a name, not a path. A defined key in the wrong place passes. Check paths when the
    Fields tables give full paths.
    shortcut: the check does not read inside `canonical_mapping` or `derived_points`, and each word
    in backticks in a heading counts, also a value such as `none`. Parse the Field column only when
    a misspelt key passes.
    """
    names: set[str] = set()
    paths = [SPEC_ROOT / "sidecar-spec.md"]
    paths += [p for folder in ("format", "common", "pre", "post") for p in (SPEC_ROOT / folder).glob("*.md")]
    for path in paths:
        fence = field_table = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("```"):
                fence = not fence
            field_table = line.startswith("|") and (field_table or line.startswith("| Field |"))
            if fence:
                continue
            text = line if line.startswith("#") else line.split("|")[1] if field_table else ""
            for name in re.findall(r"`([^`]+)`", text):
                names.update(re.findall(r"[$\w]+", name))
    return frozenset(names)


def unknown_keys(node: object, parent: object = None) -> list[str]:
    if isinstance(node, list):
        return [key for item in node for key in unknown_keys(item, parent)]
    if not isinstance(node, dict):
        return []
    found = []
    for key, value in node.items():
        if parent not in NAME_KEYED_MAPS and str(key) not in defined_keys():
            found.append(str(key))
        if key not in KEYPOINT_MAPS:
            found += unknown_keys(value, key)
    return found


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_has_only_keys_that_the_spec_defines(path: Path) -> None:
    """A key that the spec does not define is invalid (V-format.composition-7, ADR-0QKK)."""
    assert not unknown_keys(sidecar_refs.resolve(path, EXAMPLES_ROOT))


@pytest.mark.parametrize(
    ("where", "key"),
    [
        (("input", "resize"), "preserve_aspect_ratio"),
        (("decode",), "requires_nms"),
        (("decode",), "may_include_non_person_classes"),
    ],
)
def test_the_key_check_finds_a_deleted_key(where: tuple[str, ...], key: str) -> None:
    sidecar = sidecar_refs.resolve(example_paths()[0], EXAMPLES_ROOT)
    functools.reduce(lambda node, name: node.setdefault(name, {}), where, sidecar)[key] = True
    assert unknown_keys(sidecar) == [key]


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_declares_its_normalization(path: Path) -> None:
    """`input.normalization` is required (ADR-0QKK)."""
    assert "normalization" in sidecar_refs.resolve(path, EXAMPLES_ROOT)["input"]


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
    assert "specs/model-sidecar/common/sizes-and-artifacts.md" in shown
    assert (
        "skellytracker/core/detectors/keypoint_detectors/rtmw/wholebody/rtmw-wholebody.yaml"
        in shown
    )
    assert not any(name.startswith("specs/model-sidecar/examples/") for name in shown)


def test_no_file_outside_the_examples_holds_the_placeholder() -> None:
    """The placeholder hash is valid only under `specs/model-sidecar/examples/` (V-common.sizes_and_artifacts-12)."""
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
    assert set(entry) - OPTIONAL_INVENTORY_KEYS == INVENTORY_KEYS
    assert re.fullmatch(r"(model|proposal)-\S+@\S+@v\d+", entry.get("bundle", "model-x@y@v1"))
    assert entry["kind"] in {"export", "forecast"}
    assert isinstance(entry["tracked"], bool)
    assert isinstance(entry["edits"], list)


def fragment_paths() -> list[Path]:
    """Every YAML file of the examples that is not a sidecar."""
    return sorted(p for p in EXAMPLES_DETECTORS.rglob("*.yaml") if not is_sidecar(p))


def package_copy(fragment: Path) -> Path:
    return PACKAGE_DETECTORS / fragment.relative_to(EXAMPLES_DETECTORS)


@pytest.mark.parametrize("fragment", fragment_paths(), ids=example_key)
def test_fragment_has_one_source(fragment: Path) -> None:
    """A package copy with the same bytes, or a `fragments` entry. Not both."""
    copy, entry = package_copy(fragment), fragment_entries().get(example_key(fragment))
    assert copy.is_file() != (entry is not None), example_key(fragment)
    if copy.is_file():
        assert fragment.read_bytes().replace(b"\r\n", b"\n") == (
            copy.read_bytes().replace(b"\r\n", b"\n")
        )


def test_every_fragment_entry_names_a_fragment() -> None:
    assert set(fragment_entries()) <= {example_key(p) for p in fragment_paths()}


@pytest.mark.parametrize("key", sorted(fragment_entries()))
def test_fragment_entry_is_complete(key: str) -> None:
    entry = fragment_entries()[key]
    assert set(entry) == FRAGMENT_KEYS
    assert isinstance(entry["tracked"], bool)


def test_every_fragment_is_used_by_an_example() -> None:
    """A copy that no example refers to is stale: delete it."""
    used = {f for p in example_paths() for f in sidecar_refs.files(p, EXAMPLES_ROOT)}
    unused = [example_key(p) for p in fragment_paths() if p.resolve() not in used]
    assert not unused, unused
