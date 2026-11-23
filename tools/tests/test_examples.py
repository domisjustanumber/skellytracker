"""The spec's reference examples hold correct hashes, keep the placeholder in place and have provenance.

The examples under `specs/model-sidecar/examples/` follow the package's `detectors/`
layout, so their `$ref` paths resolve with that folder as the sidecar root.

Every other YAML file under the examples is a fragment, in `shared/` or next to
a sidecar. Each fragment has a `fragments` entry in `inventory.yaml`. A package
copy is not a source (ADR-VV8B).

This file moves to the specs repository with the spec. It imports no skellytracker, onnx or
onnxruntime, and it reads no file of the package (`tools/tests/test_intake_gate.py` checks the
imports). The skellytracker test `tools/tests/test_package_examples.py` resolves and validates
each example with the spec loader `skellytracker/core/model_spec/`, and checks the package files
for the placeholder.
"""

import functools
import re
from pathlib import Path

import pytest
import sidecar_refs
import sidecar_trace
import yaml
from intake_bundle import FRAGMENT_KEYS, INVENTORY_KEYS

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "specs" / "model-sidecar" / "examples"
INVENTORY_PATH = REPO_ROOT / "specs" / "model-sidecar" / "inventory.yaml"
EXAMPLES_DETECTORS = EXAMPLES_ROOT / "detectors"


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


SPEC_ROOT = REPO_ROOT / "specs" / "model-sidecar"
# The keys of these maps are names (sizes, precisions, overlay parts), not fields.
NAME_KEYED_MAPS = {
    "sizes",
    "precision_artifacts",
    "dtype",
    "normalization_by_precision",
    "parts",
    "groups",  # sizes.<size>.score_map.groups: the keys are landmark-schema group names
}
# These map keypoint names to sources. The check does not read inside them.
KEYPOINT_MAPS = {"derived_points"}
# The section of the landmark schema files defines the keys of a schema file, not of a sidecar.
SCHEMA_FILE_SECTION = SPEC_ROOT / "post" / "keypoint" / "landmark-schema.md"
REMOVED_KEYS = frozenset({"canonical_mapping"})  # ADR-23F5: the field left the sidecar spec


@functools.cache
def defined_keys() -> frozenset[str]:
    """Each name in backticks in a heading or a Field table of the spec index or a section file.

    The field path of each `selectors` item of a section also counts, for example
    `batching.batch_conversion`, which no Field table names. A dotted name such as `keypoint.skeletons[].edges` defines each of its parts. The index gives the
    top-level keys, for example `batching`. The check skips `post/keypoint/landmark-schema.md`,
    because it defines the keys of a schema file. `REMOVED_KEYS` holds a key that a frozen heading
    or a schema-file heading still names, for example `canonical_mapping`.
    shortcut: a name, not a path. A defined key in the wrong place passes. Check paths when the
    Fields tables give full paths.
    shortcut: the check does not read inside `derived_points`, and each word
    in backticks in a heading counts, also a value such as `none`. Parse the Field column only when
    a misspelt key passes.
    """
    names: set[str] = set()
    paths = [SPEC_ROOT / "sidecar-spec.md"]
    paths += [p for folder in ("format", "common", "pre", "post") for p in (SPEC_ROOT / folder).rglob("*.md")]
    paths.remove(SCHEMA_FILE_SECTION)
    for path in paths[1:]:
        front, _ = sidecar_trace.parse_front_matter(path.read_text(encoding="utf-8"), str(path))
        for selector in front.get("selectors") or []:
            names.update(re.findall(r"\w+", str(selector).split("=")[0]))
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
    return frozenset(names) - REMOVED_KEYS


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


def test_a_selector_path_is_a_defined_key() -> None:
    """`batching.batch_conversion` is only in a selector and a note (ADR-JAA4)."""
    assert "batch_conversion" in defined_keys()


def placeholder_scan_paths(folders: tuple[str, ...] = ("specs", "tools")) -> list[Path]:
    """Every YAML file of `folders`, and every Markdown file of the spec when `folders` holds `specs`.

    `tools/tests/test_package_examples.py` scans the folder `skellytracker` of the package.
    """
    paths = [
        p
        for folder in folders
        for pattern in ("*.yaml", "*.yml")
        for p in (REPO_ROOT / folder).rglob(pattern)
    ]
    if "specs" in folders:
        paths += (REPO_ROOT / "specs").rglob("*.md")
    return sorted(p for p in paths if EXAMPLES_ROOT not in p.parents)


def placeholder_holders(folders: tuple[str, ...] = ("specs", "tools")) -> list[str]:
    """The files of `placeholder_scan_paths(folders)` that hold the placeholder hash."""
    return [
        p.relative_to(REPO_ROOT).as_posix()
        for p in placeholder_scan_paths(folders)
        if sidecar_refs.PLACEHOLDER in p.read_text(encoding="utf-8")
    ]


def test_the_placeholder_scan_reads_the_sidecars_and_the_spec() -> None:
    shown = {p.relative_to(REPO_ROOT).as_posix() for p in placeholder_scan_paths()}
    assert "specs/model-sidecar/common/sizes-and-artifacts.md" in shown
    assert not any(name.startswith("specs/model-sidecar/examples/") for name in shown)


def test_no_file_outside_the_examples_holds_the_placeholder() -> None:
    """The placeholder hash is valid only under `specs/model-sidecar/examples/` (V-common.sizes_and_artifacts-11).

    `tools/tests/test_package_examples.py` checks the files of the package.
    """
    holders = placeholder_holders()
    assert not holders, holders


def test_every_example_has_one_provenance_entry() -> None:
    entries = inventory()["examples"]
    assert set(entries) == {example_key(p) for p in example_paths()}


@pytest.mark.parametrize("key", sorted(inventory()["examples"]))
def test_provenance_entry_is_complete(key: str) -> None:
    entry = inventory()["examples"][key]
    assert set(entry) == INVENTORY_KEYS
    assert re.fullmatch(r"(model|proposal)-\S+@\S+@v\d+", entry["bundle"])
    assert entry["kind"] == "export"
    assert isinstance(entry["tracked"], bool)
    assert isinstance(entry["edits"], list)


# The family folder of an example, and the name of the family in the scope list of the changelog.
# A new family needs a row here.
SCOPE_NAMES = {"rtmw": "RTMW", "yolox-person": "YOLOX (person)"}


@pytest.mark.parametrize("key", sorted(inventory()["examples"]))
def test_example_family_is_in_the_scope_of_this_revision(key: str) -> None:
    """Procedure A of `change-sidecar-spec` adds the model of a new example to the scope list.

    Only this direction holds: the scope list also names models with no example.
    """
    family = key.split("/")[2]
    assert family in SCOPE_NAMES, f"add the scope name of the family {family!r} to SCOPE_NAMES"
    changelog = (REPO_ROOT / "specs" / "model-sidecar" / "changelog.md").read_text(encoding="utf-8")
    scope = changelog.split("### Scope of this revision", 1)[1].split("\nThe rules of this list:", 1)[0]
    exporter = inventory()["examples"][key]["exporter"]
    line = next((x for x in scope.splitlines() if x.startswith(f"- {exporter}: ")), "")
    assert SCOPE_NAMES[family] in line, (key, line)


def fragment_paths() -> list[Path]:
    """Every YAML file of the examples that is not a sidecar."""
    return sorted(p for p in EXAMPLES_DETECTORS.rglob("*.yaml") if not is_sidecar(p))


@pytest.mark.parametrize("fragment", fragment_paths(), ids=example_key)
def test_fragment_has_an_entry(fragment: Path) -> None:
    """Each fragment has a `fragments` entry. A package copy is not a source."""
    assert example_key(fragment) in fragment_entries(), example_key(fragment)


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
