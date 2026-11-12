"""The spec's reference examples parse, resolve, hold correct hashes and have provenance.

The examples under `specs/model-sidecar/examples/` follow the package's `detectors/`
layout, so their `$ref` paths resolve with that folder as the sidecar root. They
are not validated against `SidecarModel`: it does not load `schema_version: "2.0.0"` yet.
They resolve with `sidecar_refs.resolve`, because the package resolver refuses
`sha256` next to `$ref`.

Every other YAML file under the examples is a fragment, in `shared/` or next to
a sidecar. Each fragment has a `fragments` entry in `inventory.yaml`. A package
copy is not a source (ADR-VV8B).
"""

import functools
import re
from pathlib import Path
from typing import Any

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
def test_example_resolves(path: Path) -> None:
    resolved = sidecar_refs.resolve(path, EXAMPLES_ROOT)
    assert resolved["model_id"] == path.stem
    assert resolved["schema_version"] == "2.0.0"


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
def test_example_has_one_batch_field(path: Path) -> None:
    """One `batching.batch`, and `batching.batch_conversion` only with batch 3 (ADR-JAA4, item 1).

    The key check does not find `batch_artifacts`: its Removed stub heading still names it.
    """
    resolved = sidecar_refs.resolve(path, EXAMPLES_ROOT)
    batching = resolved["batching"]
    batch = batching["batch"]
    assert not isinstance(batch, bool) and batch in (3, 1, "dynamic"), batching
    assert set(batching) <= {"batch", "batch_conversion"}, batching
    conversion = batching.get("batch_conversion")
    assert (batch == 3) == (conversion is not None), batching
    assert conversion in (None, {"profile_id": "static-batch-v1"}), batching
    for size, entry in resolved["sizes"].items():
        assert "batch_artifacts" not in entry["onnx"], size


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_gives_output_shapes_in_each_size(path: Path) -> None:
    """`onnx.output_shapes` of each size: one entry for each output, in order (ADR-JAA4, item 2).

    An entry has the dims of `outputs[i].shape`. Each fixed dim of that shape is equal or -1 in the
    entry. Dim 0 is `batching.batch`, or -1 for `dynamic`.
    """
    resolved = sidecar_refs.resolve(path, EXAMPLES_ROOT)
    outputs, batch = resolved["outputs"], resolved["batching"]["batch"]
    for size, entry in resolved["sizes"].items():
        shapes = entry["onnx"].get("output_shapes")
        assert isinstance(shapes, list) and len(shapes) == len(outputs), size
        for output, shape in zip(outputs, shapes, strict=True):
            where = (size, output["name"])
            assert isinstance(shape, list) and shape, where
            assert shape[0] == (-1 if batch == "dynamic" else batch), where
            family = output.get("shape")
            if family is None:
                continue
            assert len(shape) == len(family), where
            assert all(f == -1 or d in (f, -1) for f, d in zip(family, shape, strict=True)), where


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_the_hash_tool_finds_the_artifacts_of_each_size(path: Path) -> None:
    """`sidecar_refs` scans each `precision_artifacts` entry. A moved key hides an artifact from the hash check."""
    scanned = {
        artifact.filename
        for file in sidecar_refs.files(path, EXAMPLES_ROOT)
        for artifact in sidecar_refs._scan(file.read_text(encoding="utf-8")).artifacts
    }
    for size, entry in sidecar_refs.resolve(path, EXAMPLES_ROOT)["sizes"].items():
        names = {artifact["filename"] for artifact in entry["onnx"]["precision_artifacts"].values()}
        assert names and names <= scanned, (size, sorted(names - scanned))


SPEC_ROOT = REPO_ROOT / "specs" / "model-sidecar"
# The keys of these maps are names (sizes, precisions, overlay parts), not fields.
NAME_KEYED_MAPS = {
    "sizes",
    "precision_artifacts",
    "dtype",
    "normalization_by_precision",
    "parts",
}
# These map keypoint names to sources. The check does not read inside them.
KEYPOINT_MAPS = {"canonical_mapping", "derived_points"}


@functools.cache
def defined_keys() -> frozenset[str]:
    """Each name in backticks in a heading or a Field table of the spec index or a section file.

    The field path of each `selectors` item of a section also counts, for example
    `batching.batch_conversion`, which no Field table names. A dotted name such as `keypoint.skeletons[].edges` defines each of its parts. The index gives the
    top-level keys, for example `batching`.
    shortcut: a name, not a path. A defined key in the wrong place passes. Check paths when the
    Fields tables give full paths.
    shortcut: the check does not read inside `canonical_mapping` or `derived_points`, and each word
    in backticks in a heading counts, also a value such as `none`. Parse the Field column only when
    a misspelt key passes.
    """
    names: set[str] = set()
    paths = [SPEC_ROOT / "sidecar-spec.md"]
    paths += [p for folder in ("format", "common", "pre", "post") for p in (SPEC_ROOT / folder).rglob("*.md")]
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


def test_a_selector_path_is_a_defined_key() -> None:
    """`batching.batch_conversion` is only in a selector and a note (ADR-JAA4)."""
    assert "batch_conversion" in defined_keys()


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_has_only_keys_that_the_spec_defines(path: Path) -> None:
    """A key that the spec does not define is invalid (V-format.composition-5, ADR-0QKK)."""
    assert not unknown_keys(sidecar_refs.resolve(path, EXAMPLES_ROOT))


@pytest.mark.parametrize(
    ("where", "key"),
    [
        (("input", "resize"), "preserve_aspect_ratio"),
        (("object", "decode"), "requires_nms"),
        (("object", "decode"), "may_include_non_person_classes"),
        (("input",), "layout"),
        (("input", "resize"), "supports_dynamic_size"),
        (("outputs", 0), "rank"),
        (("sizes", "m", "onnx", "precision_artifacts", "fp32"), "input_dtype"),
        (("keypoint", "decode"), "is_3d"),
    ],
)
def test_the_key_check_finds_a_deleted_key(where: tuple[str | int, ...], key: str) -> None:
    sidecar = sidecar_refs.resolve(example_paths()[0], EXAMPLES_ROOT)

    def step(node: Any, name: str | int) -> Any:
        return node[name] if isinstance(name, int) else node.setdefault(name, {})

    functools.reduce(step, where, sidecar)[key] = True
    assert unknown_keys(sidecar) == [key]


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_declares_its_normalization(path: Path) -> None:
    """`input.normalization` is required (ADR-0QKK)."""
    assert "normalization" in sidecar_refs.resolve(path, EXAMPLES_ROOT)["input"]


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_keypoint_example_declares_its_geometry(path: Path) -> None:
    """`keypoint.geometry` is required at the keypoint level (ADR-90CE)."""
    keypoint = sidecar_refs.resolve(path, EXAMPLES_ROOT).get("keypoint")
    assert keypoint is None or keypoint.get("geometry") in {"2d", "3d"}


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
    """The placeholder hash is valid only under `specs/model-sidecar/examples/` (V-common.sizes_and_artifacts-11)."""
    holders = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in placeholder_scan_paths()
        if sidecar_refs.PLACEHOLDER in p.read_text(encoding="utf-8")
    ]
    assert not holders, holders


TOKENS = r"[a-z0-9]+(-[a-z0-9]+)*"  # the pattern of {family} and {variant} (V-common.identity-7)


@pytest.mark.parametrize("path", example_paths(), ids=example_key)
def test_example_follows_the_storage_layout(path: Path) -> None:
    """The folder and the keypoint detector id (V-common.identity-7, V-common.identity-8)."""
    parts = path.relative_to(EXAMPLES_ROOT / "detectors").parts
    if parts[0] == "object_detectors":
        assert len(parts) == 3, parts
        return
    assert parts[0] == "keypoint_detectors"
    assert len(parts) == 4, parts
    family, group = parts[1], parts[2]
    model_id = sidecar_refs.resolve(path, EXAMPLES_ROOT)["model_id"]
    assert re.fullmatch(TOKENS, family), parts
    assert model_id == f"{family}-{group}" or (
        model_id.startswith(f"{family}-{group}-")
        and re.fullmatch(TOKENS, model_id.removeprefix(f"{family}-{group}-"))
    ), (model_id, parts)
    keypoint_set = re.fullmatch(r"[a-z]+([1-9][0-9]*)", group)
    assert group in {"hand", "face", "body", "wholebody"} or keypoint_set, parts
    if keypoint_set:
        points = sidecar_refs.resolve(path, EXAMPLES_ROOT)["keypoint"]["point_names"]
        assert int(keypoint_set.group(1)) == len(points), (group, len(points))


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
