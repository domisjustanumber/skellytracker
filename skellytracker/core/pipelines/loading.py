"""Load and export a pipeline config (pipeline.file, Behaviour items 2, 6 and 8).

    load_pipeline("yolox-rtmw-wholebody@skellytracker")   # a key, with an optional `==<version>`
    load_pipeline(Path("my.pipeline.yaml"))               # a YAML file or a JSON file
    load_pipeline({...})                                  # a mapping with the same keys
    export_pipeline(config)                               # the mapping as written
    export_pipeline(config, resolved=True)                # each param with its default

A `Path` is a file. A string that ends in `.yaml`, `.yml` or `.json` is a file. Each other string
is a key of the pipeline catalog. A file that ends in `.json` is JSON. Each other file is YAML.

This module does the checks of a pipeline file that the model `PipelineConfig` does not do: the
implemented versions (`V-pipeline.file-1`), the file name of a YAML file (`V-pipeline.file-2`) and
duplicate keys (`V-pipeline.file-5`). Each of these checks raises `ValueError` with a message that
starts with its rule ID. A config that the model refuses raises `pydantic.ValidationError`, which
is also a `ValueError`. This module reads no sidecar.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from skellytracker.core.model_spec.resolution import _UniqueKeyLoader, lexical_path
from skellytracker.core.pipelines.config import PipelineConfig

IMPLEMENTED_VERSIONS: tuple[str, ...] = ("2.0.0",)
"""The `schema_version` values of a pipeline file that this release loads.

They are the version headings and the pre-release lines of `specs/pipeline/changelog.md`. A doc
test checks it.
"""

FILE_SUFFIXES = (".yaml", ".yml", ".json")
_DUPLICATE = "V-pipeline.file-5"


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"{_DUPLICATE}: duplicate key {key!r}")
        result[key] = value
    return result


def read_pipeline_file(path: Path | str) -> Any:
    """Return the plain data of a YAML file or a JSON file. Refuse a duplicate key (`V-pipeline.file-5`).

    The YAML loader is the safe loader of the sidecar loader. It makes only plain data.
    """
    path = lexical_path(path)
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text, object_pairs_hook=_unique)
        return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506 (a subclass of SafeLoader)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        message = " ".join(str(exc).split())
        if "duplicate key" in message:  # the sidecar loader names its own rule ID
            raise ValueError(f"{_DUPLICATE}: {path.name}: {message.replace('V-format.composition-6: ', '')}") from exc
        raise ValueError(f"cannot parse {path.name}: {message}") from exc
    except ValueError as exc:
        raise ValueError(f"{exc} (file: {path.name})") from exc


def _validate(data: Any) -> PipelineConfig:
    if not isinstance(data, Mapping):
        raise ValueError("V-pipeline.file-4: the top level of a pipeline config must be a mapping")
    config = PipelineConfig.model_validate(dict(data))
    if config.schema_version not in IMPLEMENTED_VERSIONS:
        raise ValueError(
            f"V-pipeline.file-1: this release does not load schema_version {config.schema_version!r}; "
            f"it loads {list(IMPLEMENTED_VERSIONS)}"
        )
    return config


def load_pipeline_file(path: Path | str) -> PipelineConfig:
    """Load the pipeline file at `path`. A load by path does not use the catalog."""
    path = lexical_path(path)
    config = _validate(read_pipeline_file(path))
    expected = f"{config.pipeline_id}.pipeline.yaml"
    if path.suffix.lower() != ".json" and path.name != expected:
        raise ValueError(f"V-pipeline.file-2: the name of the pipeline file {path.name} must be {expected}")
    return config


def load_pipeline(source: str | Path | Mapping[str, Any], *, user_root: Path | str | None = None) -> PipelineConfig:
    """Return the config of a key, a file or a mapping.

    `source` is a key `<pipeline_id>@<source.name>` with an optional pin `==<version>`, the path of
    a YAML file or a JSON file, or a mapping. The module docstring tells how a string is a path or
    a key. `user_root` is the user root of the catalog. Only a key uses it.

    Raise `PipelineNotFoundError` or `PipelineUnavailableError` for a key that the catalog cannot
    give, and `ValueError` for a file or a config that is not valid. The message holds the rule ID.
    """
    if isinstance(source, Mapping):
        config = _validate(source)
    elif isinstance(source, Path) or source.lower().endswith(FILE_SUFFIXES):
        config = load_pipeline_file(source)
    else:
        from skellytracker.core.pipelines.catalog import find_pipeline  # the catalog imports this module

        config = load_pipeline_file(find_pipeline(source, user_root).path)
    # phase 2: the load checks that need the sidecars go here
    return config


def export_pipeline(config: PipelineConfig, resolved: bool = False) -> dict[str, Any]:
    """Return the plain mapping of `config`, with only JSON types.

    With `resolved=False`, the mapping holds only the keys and the params that the config gives, so
    it loads again (ADR-97X9 item 10). A value that the caller changed after the load is a value
    that the config gives. With `resolved=True`, the mapping holds each key and each param of each
    node, with its default when the config does not give it.
    """
    if resolved:
        return config.model_dump(mode="json")
    # pydantic does not mark a change inside a default value, for example in the default `params`
    # of a node. The second dump holds each value that is not the default.
    return _union(config.model_dump(mode="json", exclude_unset=True), config.model_dump(mode="json", exclude_defaults=True))


def _union(written: Any, changed: Any) -> Any:
    """Return `written` with each key that only `changed` has, at each level."""
    if isinstance(written, dict) and isinstance(changed, dict):
        return {**changed, **{key: _union(value, changed[key]) if key in changed else value for key, value in written.items()}}
    if isinstance(written, list) and isinstance(changed, list) and len(written) == len(changed):
        return [_union(*pair) for pair in zip(written, changed, strict=True)]
    return written


__all__ = ["IMPLEMENTED_VERSIONS", "export_pipeline", "load_pipeline", "load_pipeline_file", "read_pipeline_file"]
