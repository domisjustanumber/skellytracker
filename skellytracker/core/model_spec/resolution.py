"""File composition: read a sidecar file and resolve its `$ref` directives.

    read the bytes -> check the bytes -> parse (no duplicate key) -> resolve each `$ref`

The resolver checks the `sha256` of each `$ref` target against the bytes of the target before it
parses the target. Validation never sees `$ref` or the `sha256` of a directive. This module does
not validate the resolved tree.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any

import yaml

from skellytracker.core.model_spec.errors import SidecarParseError, SidecarRefError

HEX64 = re.compile(r"[0-9a-f]{64}")
_REF = "$ref"
_BOM = b"\xef\xbb\xbf"


class _UniqueKeyLoader(yaml.SafeLoader):
    """A safe loader that refuses a mapping with a duplicate key."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: list[Any] = []
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"V-format.composition-6: duplicate key {key!r}", key_node.start_mark
                )
            seen.append(key)
        return super().construct_mapping(node, deep=deep)


def lexical_path(path: Path | str) -> Path:
    """Return the absolute form of `path`, with `..` removed. It does not follow a symlink.

    A file of a Hugging Face snapshot is a symlink into `blobs/`. `Path.resolve()` leaves the
    snapshot, so the root check and the `$ref` paths fail.
    """
    return Path(os.path.abspath(path))


def parse_yaml_bytes(data: bytes, path: Path) -> Any:
    """Check the bytes of one file and parse them.

    Implements: format.composition

    The file must be UTF-8 without a BOM, with LF line endings (V-format.composition-3). A mapping
    must not repeat a key (V-format.composition-6).
    """
    rule = "V-format.composition-3"
    if data.startswith(_BOM):
        raise SidecarParseError(f"{rule}: the file starts with a byte order mark", path, (rule,))
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SidecarParseError(f"{rule}: the file is not valid UTF-8: {exc}", path, (rule,)) from exc
    if "\r" in text:
        raise SidecarParseError(f"{rule}: the file has CRLF line endings; it must have LF line endings", path, (rule,))
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506 (a subclass of SafeLoader)
    except yaml.YAMLError as exc:
        message = " ".join(str(exc).split())
        rules = ("V-format.composition-6",) if "V-format.composition-6" in message else ()
        raise SidecarParseError(f"cannot parse the YAML: {message}", path, rules) from exc


def resolve_sidecar_composition(path: Path | str, sidecar_root: Path | str) -> Any:
    """Read the file at `path` and replace each `$ref` directive with the content of its target.

    Implements: format.composition

    `sidecar_root` is the root of the file. Each target must stay inside it. The result has no
    `$ref` and no directive `sha256`.
    """
    path, root = lexical_path(path), lexical_path(sidecar_root)
    if not path.is_relative_to(root):
        raise SidecarRefError(f"the file is outside the sidecar root {root}", path)
    if not path.is_file():
        raise SidecarParseError("file not found", path)
    return _resolve(_read(path), path, root, (path,))


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SidecarParseError(f"cannot read the file: {exc}", path) from exc


def _resolve(data: bytes, path: Path, root: Path, stack: tuple[Path, ...]) -> Any:
    return _resolve_node(parse_yaml_bytes(data, path), path, root, stack)


def _resolve_node(node: Any, path: Path, root: Path, stack: tuple[Path, ...]) -> Any:
    if isinstance(node, list):
        return [_resolve_node(item, path, root, stack) for item in node]
    if not isinstance(node, dict):
        return node
    if _REF not in node:
        return {key: _resolve_node(value, path, root, stack) for key, value in node.items()}

    def refuse(rule: str, message: str) -> SidecarRefError:
        return SidecarRefError(f"{rule}: `$ref` {node[_REF]!r}: {message}", path, (rule,))

    if set(node) != {_REF, "sha256"}:
        raise refuse("V-format.composition-1", f"a directive must have exactly the keys `$ref` and `sha256`, found {sorted(map(str, node))}")
    reference, expected = node[_REF], node["sha256"]
    if not isinstance(reference, str) or not reference:
        raise refuse("V-format.composition-1", "the value of `$ref` must be a file path string")
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        raise refuse("V-format.composition-2", "`sha256` must be a string of 64 lowercase hexadecimal characters")
    target = lexical_path(path.parent / reference)
    if not target.is_relative_to(root):
        raise refuse("V-format.composition-4", f"the target is outside the sidecar root {root}")
    if target in stack:
        cycle = " -> ".join(str(item) for item in (*stack, target))
        raise refuse("V-format.composition-1", f"cycle in the composition: {cycle}")
    if not target.is_file():
        raise refuse("V-format.composition-1", f"the target {target} does not exist")
    data = _read(target)
    found = hashlib.sha256(data).hexdigest()
    if found != expected:
        raise refuse("V-format.composition-2", f"`sha256` does not match the target {target} (the file has {found}, the directive has {expected})")
    return _resolve(data, target, root, (*stack, target))
