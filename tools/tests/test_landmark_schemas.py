"""Each schema file of the registry and each keypoint example follow the landmark schema rules (ADR-23F5).

The test checks these rules of the sidecar spec:

- `V-post.keypoint.landmark_schema-1` to `-3` and `V-post.keypoint.canonical_mapping-1` on each
  schema file of the package registry `skellytracker/core/model_zoo/landmark_schemas/`;
- `V-post.keypoint.schema-10` and `-11` on each keypoint example.

`V-post.keypoint.landmark_schema-4` (no two files with one `name`) needs the user root. The host
checks it at load (stage 1.4 of the implementation plan).
"""

import math
import re
from pathlib import Path

import pytest
import sidecar_refs
import yaml
from intake_bundle import _unique_yaml
from test_examples import EXAMPLES_ROOT, example_key, example_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "skellytracker" / "core" / "model_zoo" / "landmark_schemas"
SCHEMA_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
GROUP_NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
BAD_CHARACTER = re.compile(r"[/\s]")


def schema_paths() -> list[Path]:
    return sorted(SCHEMA_DIR.glob("*.yaml"))


def load(path: Path) -> dict:
    """Load a schema file and refuse a repeated key (V-post.keypoint.landmark_schema-1)."""
    return _unique_yaml(path.read_text(encoding="utf-8"), yaml)


def point_names(schema: dict) -> list[str]:
    return [point for group in schema["groups"] for point in group["points"]]


def test_the_registry_holds_coco_wholebody() -> None:
    assert SCHEMA_DIR / "COCO_WholeBody.yaml" in schema_paths()


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_schema_file_has_its_keys(path: Path) -> None:
    """V-post.keypoint.landmark_schema-1."""
    schema = load(path)
    assert {"name", "source", "groups"} <= set(schema) <= {"name", "source", "groups", "canonical_mapping"}
    assert schema["name"] == path.stem
    assert SCHEMA_NAME.fullmatch(schema["name"])
    assert isinstance(schema["source"], str) and schema["source"].strip()


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_schema_file_has_valid_groups(path: Path) -> None:
    """V-post.keypoint.landmark_schema-2."""
    groups = load(path)["groups"]
    assert isinstance(groups, list) and groups
    names = []
    for group in groups:
        assert isinstance(group, dict) and set(group) == {"name", "points"}, group
        assert isinstance(group["name"], str) and GROUP_NAME.fullmatch(group["name"]), group["name"]
        points = group["points"]
        assert isinstance(points, list) and points, group["name"]
        assert all(isinstance(point, str) for point in points), group["name"]
        names.append(group["name"])
    assert len(names) == len(set(names)), names


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_schema_file_has_unique_point_names(path: Path) -> None:
    """V-post.keypoint.landmark_schema-3."""
    names = point_names(load(path))
    assert len(names) == len(set(names))
    assert not [name for name in names if BAD_CHARACTER.search(name)]


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@pytest.mark.parametrize("path", schema_paths(), ids=lambda p: p.stem)
def test_schema_file_has_a_valid_canonical_mapping(path: Path) -> None:
    """V-post.keypoint.canonical_mapping-1."""
    schema = load(path)
    mapping = schema.get("canonical_mapping")
    if mapping is None:
        return
    groups = {group["name"] for group in schema["groups"]}
    points = set(point_names(schema))
    assert isinstance(mapping, dict) and mapping
    for region, entries in mapping.items():
        assert region in groups and region != "face", region
        assert isinstance(entries, dict) and entries, region
        for name, source in entries.items():
            assert isinstance(name, str) and not BAD_CHARACTER.search(name), (region, name)
            if isinstance(source, str):
                sources = [source]
            elif isinstance(source, list):
                assert source and all(isinstance(s, str) for s in source), (region, name)
                sources = source
            else:
                assert isinstance(source, dict) and source, (region, name)
                assert all(isinstance(s, str) and is_number(w) for s, w in source.items()), (region, name)
                assert abs(math.fsum(source.values()) - 1) <= 1e-6, (region, name)
                sources = list(source)
            assert set(sources) <= points, (region, name, set(sources) - points)


def keypoint_examples() -> list[Path]:
    return [
        path
        for path in example_paths()
        if "keypoint_detector" in sidecar_refs.resolve(path, EXAMPLES_ROOT)["role"]
    ]


def test_there_are_keypoint_examples() -> None:
    assert keypoint_examples()


@pytest.mark.parametrize("path", keypoint_examples(), ids=example_key)
def test_keypoint_example_names_a_registered_schema(path: Path) -> None:
    """V-post.keypoint.schema-10 and V-post.keypoint.schema-11."""
    keypoint = sidecar_refs.resolve(path, EXAMPLES_ROOT)["keypoint"]
    schema_path = SCHEMA_DIR / f"{keypoint['landmark_schema']}.yaml"
    assert schema_path.is_file(), keypoint["landmark_schema"]
    assert keypoint["point_names"] == point_names(load(schema_path))
    assert not [name for name in keypoint["point_names"] if BAD_CHARACTER.search(name)]
