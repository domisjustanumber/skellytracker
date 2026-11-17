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
is also a `ValueError`.

`load_pipeline` then runs the load checks that need the sidecars (`_runtime/resolve.py`).
`check_pipeline` gives the load result: the warnings that are known before a start.

`describe_port` is temporary. It serves only the legacy path of the freemocap metrics stage, and
stage 2.4 of the implementation plan deletes it with that path (ADR-C3A4).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from skellytracker.core.model_spec.resolution import _UniqueKeyLoader, lexical_path
from skellytracker.core.pipelines._runtime.resolve import resolve, sidecar_hashes
from skellytracker.core.pipelines.config import PipelineConfig
from skellytracker.core.pipelines.values import PortInfo
from skellytracker.core.pipelines.warnings import PipelineWarning

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
    The load runs each load check, also the checks that need the sidecars (ADR-ZYS9 item 7). An
    ONNX file or an extra that is absent is not an error: `check_pipeline` gives the warning.
    """
    if isinstance(source, Mapping):
        config = _validate(source)
    elif isinstance(source, Path) or source.lower().endswith(FILE_SUFFIXES):
        config = load_pipeline_file(source)
    else:
        from skellytracker.core.pipelines.catalog import get_pipeline  # the catalog imports this module

        config = load_pipeline_file(get_pipeline(source, user_root).path)
    resolve(config, user_root)
    return config


@dataclass(frozen=True)
class PipelineCheck:
    """The load result of a config: the warnings that are known before a start, and the output schema."""

    warnings: tuple[PipelineWarning, ...]
    needs_execution_provider: bool
    """True when a run must give an execution provider (`V-pipeline.running-8`)."""
    output_schema: dict[str, dict[str, Any]]


def check_pipeline(config: PipelineConfig, *, user_root: Path | str | None = None) -> PipelineCheck:
    """Run the load checks of `config` and return the load result (pipeline.running, Behaviour item 8).

    Raise `ValueError` for a config that fails a load rule. Use it for a config that changed after
    its load, and to read the warnings, for example `missing_dependency`.
    """
    resolved = resolve(config, user_root)
    return PipelineCheck(resolved.warnings, resolved.needs_execution_provider, resolved.output_schema)


def describe_port(config: PipelineConfig, port: str, *, user_root: Path | str | None = None) -> PortInfo:
    """Return the facts of one port of `config`, for example `"wholebody.keypoints"`: its raw `point_names` and `groups`.

    Temporary: it serves only the legacy path of the freemocap metrics stage (ADR-C3A4, ADR-92BE).
    That path puts the 133 points of the old tracker in the raw names of the port, then calls
    `to_canonical(value, port_info.groups)`. Stage 2.4 of the implementation plan deletes this
    function with the legacy path. Raise `KeyError` for a port that the config does not have.
    """
    node_id, _, name = port.partition(".")
    return resolve(config, user_root).port_info(node_id, name)


def export_pipeline(config: PipelineConfig, resolved: bool = False, *, user_root: Path | str | None = None) -> dict[str, Any]:
    """Return the plain mapping of `config`, with only JSON types.

    With `resolved=False`, the mapping holds only the keys and the params that the config gives, so
    it loads again (ADR-97X9 item 10). A value that the caller changed after the load is a value
    that the config gives. With `resolved=True`, the mapping holds each key and each param of each
    node, with its default when the config does not give it.

    In the two forms, each `onnx_model` node gets the `sidecar_sha256` of the sidecar file that its
    `key` resolves, when the config does not give it (ADR-7NY2 item 10). `user_root` is the user
    root of the catalog. Raise `ValueError` when the catalog does not have the key.
    """
    if resolved:
        data = config.model_dump(mode="json")
    else:
        # pydantic does not mark a change inside a default value, for example in the default `params`
        # of a node. The second dump holds each value that is not the default.
        data = _union(config.model_dump(mode="json", exclude_unset=True), config.model_dump(mode="json", exclude_defaults=True))
    if any(node.type == "onnx_model" and node.params.sidecar_sha256 is None for node in config.nodes):
        hashes = sidecar_hashes(config, user_root)
        for node, written in zip(config.nodes, data["nodes"], strict=True):
            if node.id in hashes and node.params.sidecar_sha256 is None:
                written["params"]["sidecar_sha256"] = hashes[node.id]
    return data


def _union(written: Any, changed: Any) -> Any:
    """Return `written` with each key that only `changed` has, at each level."""
    if isinstance(written, dict) and isinstance(changed, dict):
        return {**changed, **{key: _union(value, changed[key]) if key in changed else value for key, value in written.items()}}
    if isinstance(written, list) and isinstance(changed, list) and len(written) == len(changed):
        return [_union(*pair) for pair in zip(written, changed, strict=True)]
    return written


__all__ = [
    "IMPLEMENTED_VERSIONS",
    "PipelineCheck",
    "check_pipeline",
    "describe_port",
    "export_pipeline",
    "load_pipeline",
    "load_pipeline_file",
    "read_pipeline_file",
]
