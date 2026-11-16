"""The catalog of the pipeline files (pipeline.file, Behaviour items 6 and 7).

    list_pipelines()      # each pipeline file of the two roots
    find_pipeline(key)    # the entry of `<key>` or of the pin `<key>==<version>`

The roots are the package root `core/model_zoo/pipelines/` and `<user root>/pipelines/`. The user
root is the user root of the detector catalog. The catalog takes each file `*.pipeline.yaml`
directly in a root. It does not read a sub-folder.

The key of a file is `<pipeline_id>@<source.name>`. The catalog reads the key with a plain YAML
parse, so it also lists a file that does not load, with the reason. It does not list a file with no
plain parse or with no `pipeline_id`: it writes one log line for that file.

The key rules are the rules of the detector catalog, with its helpers: the newest `source.version`
of a key wins in PEP 440 order, `<key>==<version>` pins a version, and the source name
`skellytracker` is reserved for the package root. When two files have the same key and the same
version, the list shows both files, and `find_pipeline` raises an error that names both paths.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml
from packaging.version import InvalidVersion, Version

from skellytracker.core.detectors.catalog import (
    RESERVED_SOURCE,
    DetectorNotFoundError,
    _select,
    _text,
    resolve_user_root,
)
from skellytracker.core.model_spec.landmark_schemas import PACKAGE_SIDECAR_ROOT
from skellytracker.core.model_spec.resolution import lexical_path
from skellytracker.core.pipelines.loading import load_pipeline_file
from skellytracker.core.pipelines.warnings import PipelineWarning

logger = logging.getLogger(__name__)

PIPELINES_FOLDER = "pipelines"
PACKAGE_PIPELINE_ROOT = PACKAGE_SIDECAR_ROOT / PIPELINES_FOLDER
PATTERN = "*.pipeline.yaml"


class PipelineNotFoundError(KeyError):
    """The catalog has no pipeline with this key, or no pipeline with the pinned version."""


class PipelineUnavailableError(RuntimeError):
    """The pipeline file of the key does not load, or two files have the key and the version."""


@dataclass(frozen=True)
class PipelineEntry:
    """One pipeline file of the catalog.

    An entry is available when its file loads. `superseded` is true when the catalog has a newer
    `source.version` of the key. `warnings` holds the warnings that are known before a start.
    """

    key: str
    version: str
    path: Path
    description: str
    available: bool
    unavailable_reason: str | None = None
    superseded: bool = False
    warnings: tuple[PipelineWarning, ...] = ()


def _version_order(entry: PipelineEntry) -> tuple[int, Version]:
    """The order of the detector catalog. Its helper takes only a sidecar, so this module has a copy."""
    try:
        return 1, Version(entry.version)
    except InvalidVersion:
        return 0, Version("0")


def _read(path: Path, is_package_root: bool) -> PipelineEntry | None:
    try:
        top = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        top = exc
    if not isinstance(top, dict) or not isinstance(top.get("pipeline_id"), str):
        logger.warning("the pipeline catalog does not list %s: it has no plain parse with a `pipeline_id`", path)
        return None
    source: dict[Any, Any] = top["source"] if isinstance(top.get("source"), dict) else {}
    source_name, version = _text(source.get("name"), "unknown"), _text(source.get("version"), "unknown")
    reason = None
    if source_name == RESERVED_SOURCE and not is_package_root:
        reason = f"the source name `{RESERVED_SOURCE}` is reserved for the package root; this file is in {path.parent}"
    else:
        try:
            load_pipeline_file(path)
        except (ValueError, OSError) as exc:  # a `pydantic.ValidationError` is a `ValueError`
            reason = " ".join(str(exc).split())
    entry = PipelineEntry(f"{top['pipeline_id']}@{source_name}", version, path, _text(top.get("description"), ""), reason is None, reason)
    if reason is None and _version_order(entry)[0] == 0:
        entry = replace(entry, available=False, unavailable_reason=f"source.version {version!r} is not a PEP 440 version")
    # phase 2: the availability from the sidecars (`missing_dependency`) and the load warnings go here
    return entry


def list_pipelines(user_root: Path | str | None = None) -> list[PipelineEntry]:
    """Return each pipeline file of the two roots, sorted by key, with the newest version of a key first.

    `user_root` is the user root, as for `list_detectors`. An older version of a key is in the list,
    with `superseded=True`.
    """
    package_root = lexical_path(PACKAGE_PIPELINE_ROOT)
    by_key: dict[str, list[PipelineEntry]] = {}
    for root in dict.fromkeys((package_root, resolve_user_root(user_root) / PIPELINES_FOLDER)):
        for path in sorted(root.glob(PATTERN)) if root.is_dir() else ():
            if (entry := _read(path, is_package_root=root == package_root)) is not None:
                by_key.setdefault(entry.key, []).append(entry)
    result: list[PipelineEntry] = []
    for key in sorted(by_key):
        versions = sorted(by_key[key], key=_version_order, reverse=True)  # a stable sort: the package root is first
        result += [replace(entry, superseded=_version_order(entry) != _version_order(versions[0])) for entry in versions]
    return result


def find_pipeline(key: str, user_root: Path | str | None = None) -> PipelineEntry:
    """Return the entry of `<key>` (the newest version) or of the pin `<key>==<version>`.

    Raise `PipelineNotFoundError` when the catalog does not have it. Raise
    `PipelineUnavailableError` when two files have the key and the version, or when the file does
    not load. A load by path does not use this function, so it always works.
    """
    entries = list_pipelines(user_root)
    try:
        found: PipelineEntry = _select(key, entries)
    except DetectorNotFoundError as exc:
        raise PipelineNotFoundError(*exc.args) from None
    same = [entry for entry in entries if (entry.key, entry.version) == (found.key, found.version)]
    if len(same) > 1:
        paths = " and ".join(str(entry.path) for entry in same)
        raise PipelineUnavailableError(f"two pipeline files have the key {found.key} and the version {found.version}: {paths}")
    if not found.available:
        raise PipelineUnavailableError(f"{found.key} is unavailable: {found.unavailable_reason}")
    return found


__all__ = [
    "PACKAGE_PIPELINE_ROOT",
    "PipelineEntry",
    "PipelineNotFoundError",
    "PipelineUnavailableError",
    "find_pipeline",
    "list_pipelines",
]
