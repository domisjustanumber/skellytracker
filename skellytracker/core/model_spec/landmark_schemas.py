"""The landmark schema registry: the schema files of `landmark_schemas/` in two sidecar roots.

A landmark schema names the points of one keypoint convention, in output order, and puts them in
groups. The registry reads each `*.yaml` file in the branch `landmark_schemas/` of the package root
and of the user root. It reads no subfolder. A schema is found by its `name`.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skellytracker.core.model_spec.errors import Failure, SidecarValidationError
from skellytracker.core.model_spec.resolution import parse_yaml_bytes

PACKAGE_SIDECAR_ROOT = Path(__file__).resolve().parents[1] / "model_zoo"
SCHEMA_FOLDER = "landmark_schemas"
WEIGHT_TOLERANCE = 1e-6

_SCHEMA_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_GROUP_NAME = re.compile(r"[a-z][a-z0-9_-]*")
_BAD_POINT_CHARACTER = re.compile(r"[\s/]")
_L = "V-post.keypoint.landmark_schema-"
_C = "V-post.keypoint.canonical_mapping-1"


def _is_name(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def has_bad_point_character(name: str) -> bool:
    """Return True when a point name contains `/` or a whitespace character."""
    return bool(_BAD_POINT_CHARACTER.search(name))


def weights_sum_to_one(weights: Any) -> bool:
    """Return True when `weights` is a name-to-number map whose numbers sum to 1, within 1e-6."""
    if not (isinstance(weights, dict) and weights):
        return False
    values = list(weights.values())
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values):
        return False
    return all(_is_name(k) for k in weights) and abs(math.fsum(values) - 1.0) <= WEIGHT_TOLERANCE


def source_names(source: Any) -> list[str] | None:
    """Return the point names that one derivation reads, or None when its form is not valid.

    The forms are a string (passthrough), a list of one or more names (mean) and a name-to-number
    map whose numbers sum to 1 (weighted).
    """
    if _is_name(source):
        return [source]
    if isinstance(source, list) and source and all(_is_name(name) for name in source):
        return list(source)
    if weights_sum_to_one(source):
        return list(source)
    return None


@dataclass(frozen=True)
class LandmarkGroup:
    """One group of a landmark schema: its name and its point names, in output order."""

    name: str
    points: tuple[str, ...]


@dataclass(frozen=True)
class LandmarkSchema:
    """One landmark schema file. `canonical_mapping` maps a region to its canonical points."""

    name: str
    source: str
    groups: tuple[LandmarkGroup, ...]
    canonical_mapping: dict[str, dict[str, Any]]
    path: Path

    @property
    def point_names(self) -> tuple[str, ...]:
        """The point names of the schema: the points of its groups, in the order of the groups."""
        return tuple(point for group in self.groups for point in group.points)


def check_landmark_schema(data: Any, file_stem: str) -> list[Failure]:
    """Return the failed rules of the parsed content of one schema file.

    Implements: post.keypoint.landmark_schema
    Implements: post.keypoint.canonical_mapping

    The rules are V-post.keypoint.landmark_schema-1 to -3 and V-post.keypoint.canonical_mapping-1.
    The parser refuses a duplicate key before this check.
    """
    if not isinstance(data, dict):
        return [Failure(_L + "1", "a schema file must be a mapping")]
    found: list[Failure] = []
    extra = sorted(str(key) for key in set(data) - {"name", "source", "groups", "canonical_mapping"})
    missing = sorted({"name", "source", "groups"} - set(data))
    if extra or missing:
        found.append(Failure(_L + "1", f"missing keys {missing}, keys that the spec does not define {extra}"))
    name = data.get("name")
    if "name" in data and not (isinstance(name, str) and _SCHEMA_NAME.fullmatch(name) and name == file_stem):
        found.append(Failure(_L + "1", f"name {name!r} must match ^[A-Za-z][A-Za-z0-9_]*$ and equal the file name {file_stem!r}"))
    if "source" in data and not _is_name(data["source"]):
        found.append(Failure(_L + "1", "source must be a non-empty string"))

    groups = data.get("groups")
    group_names: list[str] = []
    points: list[str] = []
    if "groups" in data and not (isinstance(groups, list) and groups):
        found.append(Failure(_L + "2", "groups must be a non-empty list"))
    for index, group in enumerate(groups if isinstance(groups, list) else []):
        where = f"groups[{index}]"
        if not (isinstance(group, dict) and set(group) == {"name", "points"}):
            found.append(Failure(_L + "2", f"{where} must have exactly the keys name and points"))
            continue
        group_name, group_points = group["name"], group["points"]
        if not (isinstance(group_name, str) and _GROUP_NAME.fullmatch(group_name)):
            found.append(Failure(_L + "2", f"{where}.name {group_name!r} must match ^[a-z][a-z0-9_-]*$"))
        elif group_name in group_names:
            found.append(Failure(_L + "2", f"the group name {group_name!r} is not unique"))
        else:
            group_names.append(group_name)
        if not (isinstance(group_points, list) and group_points and all(isinstance(p, str) for p in group_points)):
            found.append(Failure(_L + "2", f"{where}.points must be a non-empty list of strings"))
            continue
        for point in group_points:
            if point in points:
                found.append(Failure(_L + "3", f"the point name {point!r} is not unique in the file"))
            if not point or has_bad_point_character(point):
                found.append(Failure(_L + "3", f"the point name {point!r} is empty or contains `/` or whitespace"))
            points.append(point)

    if "canonical_mapping" in data:
        found.extend(_check_canonical_mapping(data["canonical_mapping"], group_names, points))
    return found


def _check_canonical_mapping(mapping: Any, group_names: list[str], points: list[str]) -> list[Failure]:
    if not isinstance(mapping, dict):
        return [Failure(_C, "canonical_mapping must be a mapping")]
    found: list[Failure] = []
    for region, entries in mapping.items():
        if region not in group_names or region == "face":
            found.append(Failure(_C, f"the region {region!r} must be a group name of the file, and not `face`"))
        if not isinstance(entries, dict):
            found.append(Failure(_C, f"the region {region!r} must be a mapping"))
            continue
        for canonical, source in entries.items():
            where = f"{region}/{canonical}"
            if not _is_name(canonical) or has_bad_point_character(canonical):
                found.append(Failure(_C, f"the canonical point name of {where} is empty or contains `/` or whitespace"))
            names = source_names(source)
            if names is None:
                found.append(Failure(_C, f"the source of {where} must be a name, a list of names or a name-to-number map that sums to 1"))
            elif unknown := [n for n in names if n not in points]:
                found.append(Failure(_C, f"the source of {where} names {unknown}, which are not point names of the file"))
    return found


def load_landmark_schema(path: Path) -> LandmarkSchema:
    """Read and check one schema file. Raise `SidecarValidationError` when it fails a rule.

    Implements: post.keypoint.landmark_schema
    """
    data = parse_yaml_bytes(path.read_bytes(), path)
    failures = check_landmark_schema(data, path.stem)
    if failures:
        raise SidecarValidationError(failures, file_path=path)
    return LandmarkSchema(
        name=data["name"],
        source=data["source"],
        groups=tuple(LandmarkGroup(group["name"], tuple(group["points"])) for group in data["groups"]),
        canonical_mapping=data.get("canonical_mapping", {}),
        path=path,
    )


def load_landmark_schema_registry(
    user_root: Path | None = None, package_root: Path = PACKAGE_SIDECAR_ROOT
) -> dict[str, LandmarkSchema]:
    """Return the schemas of the registry, by name.

    Implements: post.keypoint.landmark_schema

    The registry reads `landmark_schemas/*.yaml` of the package root and of the user root. Two files
    with the same `name` are an error that names both paths (V-post.keypoint.landmark_schema-4).
    """
    registry: dict[str, LandmarkSchema] = {}
    for root in (package_root, user_root):
        folder = None if root is None else Path(root) / SCHEMA_FOLDER
        if folder is None or not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.yaml")):
            schema = load_landmark_schema(path)
            if schema.name in registry:
                failure = Failure(_L + "4", f"the schema name {schema.name!r} is in two files: {registry[schema.name].path} and {path}")
                raise SidecarValidationError([failure], file_path=path)
            registry[schema.name] = schema
    return registry
