#!/usr/bin/env python3
"""Write and check the reference hashes of a sidecar tree.

A sidecar can refer to other files. A ``$ref`` directive includes a fragment. A top-level ``base``
directive inherits from another sidecar. At ``vNEXT`` each of them holds the SHA-256 of the exact
bytes of its target file, and each ``filename`` artifact holds the SHA-256 of its ONNX file. The
rules are in ``notes/decisions/0016-sidecar-catalogs.md`` and in
``specs/model-sidecar/format/composition.md``.

Commands::

    python tools/sidecar_refs.py --write SIDECAR [--placeholder] [--source NAME==VERSION] [--root DIR]
    python tools/sidecar_refs.py --check SIDECAR [--root DIR]

``--write`` goes depth first. It fills in ``sha256`` on every ``$ref`` and ``base`` of the tree, so
the hashes inside a fragment are in place before the tool takes the hash of that fragment. It also
fills in ``sha256`` on every ``filename`` artifact whose ONNX file is in the folder of SIDECAR (the
leaf model folder). This is true also when a fragment or a base file declares the artifact:
``filename`` is relative to the leaf model folder
(``specs/model-sidecar/common/sizes-and-artifacts.md``, "Per-precision artifact fields"). ``--placeholder``
writes the reserved 64-zero value on an artifact that has no ``sha256`` and no ONNX file. It never
replaces a real hash. ``--source NAME==VERSION`` adds a top-level ``source`` mapping to SIDECAR when
SIDECAR has none. It never changes an existing one.

``--write`` edits text. It inserts or updates only the ``sha256`` entries (in block mappings and in
flow mappings) and the ``source`` block. It keeps every other byte, with the comments, the quotes,
the order and the blank lines. It never loads the YAML and writes it out again. It changes no file
when it reports an error.

``--check`` verifies every ``$ref`` and ``base`` hash against the exact bytes of the target file,
before any parsing. It verifies an ONNX hash only when the ONNX file is present in the folder of
SIDECAR. A CRLF file or a file with a byte order mark is an error of its own. The placeholder is
valid only in a file under ``specs/model-sidecar/examples/``. The exit status is 1 when a check fails.

``--write`` and ``--check`` use only the standard library and PyYAML. They do not import
``skellytracker``. An exporter can run them from a read-only worktree with its own Python.

``--root`` is the sidecar root. Every target must stay inside it. The default is the parent of the
nearest ``detectors`` folder above SIDECAR, or the folder of SIDECAR when there is none.

``resolve(path, root)`` is a temporary helper. The resolver in
``skellytracker/core/sidecar/resolution.py`` does not know the hashed forms yet. Delete ``resolve``
when that resolver checks hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PLACEHOLDER = "0" * 64
EXAMPLES_FOLDER = ("specs", "model-sidecar", "examples")

_STR_TAG = "tag:yaml.org,2002:str"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_PLAIN_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+\-]*")
_BOM_PREFIXES = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")
_FLOW_INDICATORS = ",[]{}"
_CHUNK = 1 << 20


class SidecarRefsError(Exception):
    """One or more problems in a sidecar tree. `errors` holds one line for each problem."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


# --------------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of `data`."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the lowercase hex SHA-256 of a file. The file is read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def is_in_examples(path: Path) -> bool:
    """Return True when `path` is under a `specs/model-sidecar/examples/` folder."""
    parts = path.resolve().parts
    size = len(EXAMPLES_FOLDER)
    return any(
        parts[i : i + size] == EXAMPLES_FOLDER for i in range(len(parts) - size + 1)
    )


def default_root(path: Path) -> Path:
    """Return the sidecar root of a sidecar path (see the module docstring)."""
    path = Path(path).resolve()
    for parent in path.parents:
        if parent.name == "detectors":
            return parent.parent
    return path.parent


def _format_problems(data: bytes) -> list[str]:
    """Return one message for each rule about bytes that `data` breaks."""
    problems: list[str] = []
    if data.startswith(_BOM_PREFIXES):
        problems.append(
            "the file starts with a byte order mark; sidecars and fragments must be UTF-8 without a BOM"
        )
    if b"\r" in data:
        problems.append(
            "the file has CRLF line endings; sidecars and fragments must have LF line endings"
        )
    return problems


def _yaml_scalar(value: str) -> str:
    """Return `value` as a YAML scalar. Quote it when a plain scalar would not load as this string."""
    if _PLAIN_SAFE.fullmatch(value):
        loaded = yaml.safe_load(value)
        if isinstance(loaded, str) and loaded == value:
            return value
    return json.dumps(value, ensure_ascii=False)


def _key_map(mapping: yaml.MappingNode) -> dict[str, yaml.Node]:
    return {k.value: v for k, v in mapping.value if isinstance(k, yaml.ScalarNode)}


def _sha_value(node: yaml.Node) -> tuple[str | None, str | None]:
    """Return `(hash, None)` for a good `sha256` node, else `(None, problem)`."""
    if not isinstance(node, yaml.ScalarNode) or node.tag != _STR_TAG:
        return None, "`sha256` must be a string; write it in quotes"
    if not _HEX64.fullmatch(node.value):
        return None, "`sha256` must be 64 lowercase hexadecimal characters"
    return node.value, None


# --------------------------------------------------------------------------------------------
# Finding the directives and the artifacts of one file
# --------------------------------------------------------------------------------------------


@dataclass
class _Reference:
    kind: str  # "$ref" or "base"
    line: int
    target: str
    path_node: yaml.ScalarNode
    mapping: yaml.MappingNode | None  # None for `base: <path>`
    sha_node: yaml.Node | None


@dataclass
class _Artifact:
    line: int
    filename: str
    filename_node: yaml.ScalarNode
    mapping: yaml.MappingNode
    sha_node: yaml.Node | None


@dataclass
class _Scan:
    root: yaml.Node | None = None
    references: list[_Reference] = field(default_factory=list)
    artifacts: list[_Artifact] = field(default_factory=list)
    problems: list[tuple[int, str]] = field(default_factory=list)
    _artifact_ids: set[int] = field(default_factory=set)


def _scan(text: str) -> _Scan:
    scan = _Scan()
    try:
        scan.root = yaml.compose(text, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        scan.problems.append((1, "cannot parse YAML: " + " ".join(str(exc).split())))
        return scan
    base_ids: set[int] = set()
    if isinstance(scan.root, yaml.MappingNode):
        for key, value in scan.root.value:
            if not (isinstance(key, yaml.ScalarNode) and key.value == "base"):
                continue
            line = key.start_mark.line + 1
            if isinstance(value, yaml.ScalarNode):
                if value.tag == _STR_TAG:
                    scan.references.append(
                        _Reference("base", line, value.value, value, None, None)
                    )
                else:
                    scan.problems.append((line, "`base` must be a file path string"))
            elif isinstance(value, yaml.MappingNode) and "$ref" in _key_map(value):
                base_ids.add(id(value))
            else:
                scan.problems.append(
                    (
                        line,
                        "`base` must be a file path or a mapping with `$ref` and `sha256`",
                    )
                )
    _walk(scan.root, scan, set(), base_ids)
    return scan


def _walk(
    node: yaml.Node | None, scan: _Scan, seen: set[int], base_ids: set[int]
) -> None:
    if node is None or id(node) in seen:
        return
    seen.add(id(node))
    if isinstance(node, yaml.SequenceNode):
        for item in node.value:
            _walk(item, scan, seen, base_ids)
        return
    if not isinstance(node, yaml.MappingNode):
        return
    keys = _key_map(node)
    if "$ref" in keys:
        _add_mapping_reference(
            node, keys, "base" if id(node) in base_ids else "$ref", scan
        )
        return
    for key, value in node.value:
        is_artifact_map = (
            isinstance(key, yaml.ScalarNode)
            and key.value == "precision_artifacts"
            and isinstance(value, yaml.MappingNode)
        )
        if is_artifact_map:
            for _, artifact in value.value:
                _add_artifact(artifact, scan)
        _walk(value, scan, seen, base_ids)


def _add_mapping_reference(
    node: yaml.MappingNode, keys: dict[str, yaml.Node], kind: str, scan: _Scan
) -> None:
    line = node.start_mark.line + 1
    extra = sorted(k for k in keys if k not in ("$ref", "sha256"))
    path_node = keys["$ref"]
    if extra:
        scan.problems.append(
            (
                line,
                f"a `{kind}` mapping must hold only `$ref` and `sha256`, found {extra}",
            )
        )
    elif not isinstance(path_node, yaml.ScalarNode) or path_node.tag != _STR_TAG:
        scan.problems.append(
            (line, f"the `$ref` of a `{kind}` mapping must be a file path string")
        )
    else:
        scan.references.append(
            _Reference(kind, line, path_node.value, path_node, node, keys.get("sha256"))
        )


def _add_artifact(node: yaml.Node, scan: _Scan) -> None:
    if not isinstance(node, yaml.MappingNode) or id(node) in scan._artifact_ids:
        return
    keys = _key_map(node)
    filename = keys.get("filename")
    if not isinstance(filename, yaml.ScalarNode) or filename.tag != _STR_TAG:
        return
    scan._artifact_ids.add(id(node))
    scan.artifacts.append(
        _Artifact(
            node.start_mark.line + 1, filename.value, filename, node, keys.get("sha256")
        )
    )


# --------------------------------------------------------------------------------------------
# Text edits
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Edit:
    start: int
    end: int
    text: str


def _line_end(text: str, index: int) -> int:
    position = text.find("\n", index)
    return len(text) if position < 0 else position


def _insert_pair(
    text: str, mapping: yaml.MappingNode, anchor: yaml.Node, key: str, value: str
) -> _Edit:
    """Insert `key: "value"` into `mapping`, directly after the pair whose value is `anchor`."""
    pair = f'{key}: "{value}"'
    if mapping.flow_style:
        at = anchor.end_mark.index
        return _Edit(at, at, ", " + pair)
    column = mapping.value[0][0].start_mark.column
    at = _line_end(text, anchor.end_mark.index)
    return _Edit(at, at, "\n" + " " * column + pair)


def _replace_hash(node: yaml.ScalarNode, value: str) -> _Edit | None:
    """Replace the value of a `sha256` entry. Keep its quotes. Return None when it is right."""
    if node.value == value and node.tag == _STR_TAG:
        return None
    quote = node.style if node.style in ('"', "'") else '"'
    new = f"{quote}{value}{quote}"
    if node.start_mark.index == node.end_mark.index:
        new = " " + new  # an empty value: the text has no space after the colon
    return _Edit(node.start_mark.index, node.end_mark.index, new)


def _apply(text: str, edits: list[_Edit]) -> str:
    ordered = sorted(edits, key=lambda e: (e.start, e.end))
    for before, after in zip(ordered, ordered[1:], strict=False):
        if before.end > after.start:
            raise ValueError("two edits overlap")
    for edit in sorted(
        enumerate(edits), key=lambda p: (p[1].start, p[0]), reverse=True
    ):
        text = text[: edit[1].start] + edit[1].text + text[edit[1].end :]
    return text


# --------------------------------------------------------------------------------------------
# The run: one depth-first walk for --write, --check and resolve
# --------------------------------------------------------------------------------------------


@dataclass
class _Run:
    root: Path
    top: Path
    write: bool = False
    strict: bool = True  # strict: a missing hash, a CRLF file and a BOM are errors
    placeholder: bool = False
    source: tuple[str, str] | None = None
    errors: list[str] = field(default_factory=list)
    # `final` holds the bytes of each file after the planned edits.
    final: dict[Path, bytes] = field(default_factory=dict)
    original: dict[Path, bytes] = field(default_factory=dict)
    order: list[Path] = field(default_factory=list)

    # ---- messages ------------------------------------------------------------------------

    def label(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def error(self, path: Path, line: int | None, message: str) -> None:
        where = self.label(path) + (f":{line}" if line else "")
        self.errors.append(f"{where}: {message}")

    # ---- the walk ------------------------------------------------------------------------

    def start(self) -> None:
        if not self.top.is_file():
            self.errors.append(f"{self.top.as_posix()}: file not found")
        elif not self.top.is_relative_to(self.root):
            self.errors.append(
                f"{self.top.as_posix()}: the file is outside the root {self.root}"
            )
        else:
            self.visit(self.top, ())

    def visit(self, path: Path, stack: tuple[Path, ...]) -> bytes:
        """Process one file after its targets. Return the bytes it has after the edits."""
        if path in self.final:
            return self.final[path]
        data = path.read_bytes()
        self.original[path] = data
        self.final[path] = data
        self._process(path, data, stack)
        self.order.append(path)  # a file comes after the files that it refers to
        return self.final[path]

    def _process(self, path: Path, data: bytes, stack: tuple[Path, ...]) -> None:
        if self._bad_bytes(path, data):
            return
        text = data.decode("utf-8")
        scan = _scan(text)
        for line, message in scan.problems:
            self.error(path, line, message)
        if scan.problems:
            return
        edits: list[_Edit] = []
        chain = (*stack, path)
        for reference in scan.references:
            self._reference(path, text, reference, chain, edits)
        for artifact in scan.artifacts:
            self._artifact(path, text, artifact, edits)
        if self.write and self.source is not None and path == self.top:
            self._source(path, text, scan, edits)
        if edits:
            self._commit(path, text, data, edits)

    def _bad_bytes(self, path: Path, data: bytes) -> bool:
        """Report a file with bad bytes. Return True when the walk must not read the file."""
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            self.error(path, None, "the file is not valid UTF-8")
            return True
        problems = _format_problems(data)
        if self.strict or self.write:
            for message in problems:
                self.error(path, None, message)
        return self.write and bool(problems)

    def _commit(self, path: Path, text: str, data: bytes, edits: list[_Edit]) -> None:
        try:
            new_text = _apply(text, edits)
            yaml.compose(new_text, Loader=yaml.SafeLoader)
        except (ValueError, yaml.YAMLError) as exc:
            self.error(path, None, f"the edits do not give valid YAML: {exc}")
            return
        new_data = new_text.encode("utf-8")
        if new_data != data:
            self.final[path] = new_data

    # ---- $ref and base -------------------------------------------------------------------

    def _reference(
        self,
        path: Path,
        text: str,
        ref: _Reference,
        chain: tuple[Path, ...],
        edits: list[_Edit],
    ) -> None:
        try:
            target = (path.parent / ref.target).resolve()
        except (OSError, ValueError):
            self.error(
                path,
                ref.line,
                f"`{ref.kind}` target {ref.target!r} is not a valid path",
            )
            return
        if not target.is_relative_to(self.root):
            self.error(
                path, ref.line, f"`{ref.kind}` target {ref.target} is outside the root"
            )
            return
        if not target.is_file():
            self.error(
                path, ref.line, f"`{ref.kind}` target {ref.target} does not exist"
            )
            return
        if target in chain:
            cycle = " -> ".join(self.label(p) for p in (*chain, target))
            self.error(path, ref.line, f"cycle in the composition: {cycle}")
            return
        digest = sha256_bytes(self.visit(target, chain))
        if self.write:
            self._write_reference(path, text, ref, digest, edits)
        else:
            self._check_reference(path, ref, digest)

    def _check_reference(self, path: Path, ref: _Reference, digest: str) -> None:
        if ref.sha_node is None:
            if self.strict:
                self.error(path, ref.line, f"`{ref.kind}` {ref.target} has no `sha256`")
            return
        value, problem = _sha_value(ref.sha_node)
        if problem:
            self.error(path, ref.line, f"`{ref.kind}` {ref.target}: {problem}")
        elif value != digest:
            self.error(
                path,
                ref.line,
                f"`sha256` of `{ref.kind}` {ref.target} does not match the file "
                f"(the file has {digest}, the directive has {value})",
            )

    def _write_reference(
        self, path: Path, text: str, ref: _Reference, digest: str, edits: list[_Edit]
    ) -> None:
        if ref.mapping is None:
            # `base: <path>` becomes `base: {$ref: <path>, sha256: "..."}`
            node = ref.path_node
            original = text[node.start_mark.index : node.end_mark.index]
            if node.style is None and any(c in original for c in _FLOW_INDICATORS):
                original = json.dumps(node.value, ensure_ascii=False)
            new = f'{{$ref: {original}, sha256: "{digest}"}}'
            edits.append(_Edit(node.start_mark.index, node.end_mark.index, new))
        elif ref.sha_node is None:
            edits.append(
                _insert_pair(text, ref.mapping, ref.path_node, "sha256", digest)
            )
        else:
            self._replace(path, ref.sha_node, digest, edits)

    def _replace(
        self, path: Path, node: yaml.Node, value: str, edits: list[_Edit]
    ) -> None:
        if not isinstance(node, yaml.ScalarNode) or node.style in ("|", ">"):
            line = node.start_mark.line + 1
            self.error(
                path, line, "cannot edit a `sha256` that is not a one-line scalar"
            )
            return
        edit = _replace_hash(node, value)
        if edit:
            edits.append(edit)

    # ---- artifacts -----------------------------------------------------------------------

    def _artifact(
        self, path: Path, text: str, art: _Artifact, edits: list[_Edit]
    ) -> None:
        name = Path(art.filename)
        if name.is_absolute() or ".." in name.parts or not art.filename:
            self.error(
                path,
                art.line,
                f"artifact filename {art.filename!r} leaves the sidecar folder",
            )
            return
        onnx = self.top.parent / name  # the leaf model folder, not the folder of `path`
        digest = sha256_file(onnx) if onnx.is_file() else None
        if self.write:
            self._write_artifact(path, text, art, digest, edits)
        else:
            self._check_artifact(path, art, digest)

    def _check_artifact(self, path: Path, art: _Artifact, digest: str | None) -> None:
        if art.sha_node is None:
            if self.strict:
                self.error(path, art.line, f"artifact {art.filename} has no `sha256`")
            return
        value, problem = _sha_value(art.sha_node)
        if problem:
            self.error(path, art.line, f"artifact {art.filename}: {problem}")
        elif digest is not None and value != digest:
            self.error(
                path,
                art.line,
                f"`sha256` of artifact {art.filename} does not match the file "
                f"(the file has {digest}, the entry has {value})",
            )
        elif digest is None and value == PLACEHOLDER and not is_in_examples(path):
            self.error(
                path,
                art.line,
                f"artifact {art.filename} has the placeholder `sha256`; "
                "it is valid only in files under specs/model-sidecar/examples/",
            )

    def _write_artifact(
        self,
        path: Path,
        text: str,
        art: _Artifact,
        digest: str | None,
        edits: list[_Edit],
    ) -> None:
        if digest is None:
            if art.sha_node is not None or not self.placeholder:
                return
            digest = PLACEHOLDER
        if art.sha_node is None:
            edits.append(
                _insert_pair(text, art.mapping, art.filename_node, "sha256", digest)
            )
        else:
            self._replace(path, art.sha_node, digest, edits)

    # ---- source --------------------------------------------------------------------------

    def _source(self, path: Path, text: str, scan: _Scan, edits: list[_Edit]) -> None:
        root = scan.root
        if not isinstance(root, yaml.MappingNode) or root.flow_style or not root.value:
            self.error(
                path,
                None,
                "cannot add `source`: the file has no top-level block mapping",
            )
            return
        keys = _key_map(root)
        if self.source is None or "source" in keys:
            return
        name, version = self.source
        first_key = root.value[0][0]
        pad = " " * first_key.start_mark.column
        block = f"{pad}source:\n{pad}  name: {_yaml_scalar(name)}\n{pad}  version: {_yaml_scalar(version)}"
        anchor = keys.get("schema_version")
        if anchor is not None:
            at = _line_end(text, anchor.end_mark.index)
            edits.append(_Edit(at, at, "\n" + block))
        else:
            at = first_key.start_mark.index - first_key.start_mark.column
            edits.append(_Edit(at, at, block + "\n"))


# --------------------------------------------------------------------------------------------
# The public functions
# --------------------------------------------------------------------------------------------


def check(path: Path, root: Path | None = None) -> list[str]:
    """Verify the hashes of a sidecar tree. Return one message for each problem (none: all good)."""
    path = Path(path).resolve()
    run = _Run(root=_root(path, root), top=path)
    run.start()
    return run.errors


def write(
    path: Path,
    root: Path | None = None,
    *,
    placeholder: bool = False,
    source: tuple[str, str] | None = None,
) -> list[Path]:
    """Fill in the hashes of a sidecar tree. Return the files that changed.

    Raise `SidecarRefsError` and change no file when there is any problem.
    """
    path = Path(path).resolve()
    run = _Run(
        root=_root(path, root),
        top=path,
        write=True,
        placeholder=placeholder,
        source=source,
    )
    run.start()
    if run.errors:
        raise SidecarRefsError(run.errors)
    changed = [p for p in run.order if run.final[p] != run.original[p]]
    for changed_path in changed:
        changed_path.write_bytes(run.final[changed_path])
    return changed


def resolve(path: Path, root: Path) -> Any:
    """Resolve a sidecar tree that can hold reference hashes. TEMPORARY.

    Verify every hash that the tree holds (a missing hash is accepted). Copy the files that the
    sidecar reaches to a temporary folder. Remove the hashes from `$ref` mappings, and change
    `base: {$ref: <path>, sha256: <hash>}` to `base: <path>`. Call the unchanged
    `resolve_sidecar_composition` on the copy. Raise `SidecarRefsError` on a bad hash.

    This function is the only place that imports `skellytracker`. Delete it when
    `skellytracker/core/sidecar/resolution.py` checks the hashes itself.
    """
    path = Path(path).resolve()
    root = Path(root).resolve()
    run = _Run(root=root, top=path, strict=False)
    run.start()
    if run.errors:
        raise SidecarRefsError(run.errors)
    from skellytracker.core.sidecar.resolution import resolve_sidecar_composition

    with tempfile.TemporaryDirectory() as folder:
        copy_root = Path(folder).resolve()
        for source in run.order:
            data = yaml.safe_load(run.original[source].decode("utf-8"))
            copy = copy_root / source.relative_to(root)
            copy.parent.mkdir(parents=True, exist_ok=True)
            dumped = yaml.safe_dump(
                _without_reference_hashes(data), sort_keys=False, width=1_000_000
            )
            copy.write_text(dumped, encoding="utf-8", newline="\n")
        return resolve_sidecar_composition(
            copy_root / path.relative_to(root), copy_root
        )


def _root(path: Path, root: Path | None) -> Path:
    return Path(root).resolve() if root is not None else default_root(path)


def _without_reference_hashes(data: Any) -> Any:
    def strip(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node and set(node) == {"$ref", "sha256"}:
                return {"$ref": node["$ref"]}
            return {key: strip(value) for key, value in node.items()}
        if isinstance(node, list):
            return [strip(item) for item in node]
        return node

    data = strip(data)
    base = data.get("base") if isinstance(data, dict) else None
    if isinstance(base, dict) and set(base) == {"$ref"}:
        data = {**data, "base": base["$ref"]}
    return data


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_source(parser: argparse.ArgumentParser, value: str) -> tuple[str, str]:
    name, separator, version = value.partition("==")
    if not (separator and name.strip() and version.strip()) or "\n" in value:
        parser.error(
            "--source must be NAME==VERSION, for example openmmlab-exporter==0.1.0"
        )
    return name.strip(), version.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sidecar_refs.py",
        description="Write and check the reference hashes of a sidecar tree.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", type=Path, metavar="SIDECAR", help="fill in the hashes"
    )
    mode.add_argument("--check", type=Path, metavar="SIDECAR", help="verify the hashes")
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="with --write: write the 64-zero placeholder on an artifact that has no sha256",
    )
    parser.add_argument(
        "--source",
        metavar="NAME==VERSION",
        help="with --write: add a top-level source mapping when the sidecar has none",
    )
    parser.add_argument(
        "--root", type=Path, help="the sidecar root (default: see the docstring)"
    )
    args = parser.parse_args(argv)
    if args.check and (args.placeholder or args.source):
        parser.error("--placeholder and --source work only with --write")
    source = _parse_source(parser, args.source) if args.source else None

    if args.write:
        try:
            changed = write(
                args.write, args.root, placeholder=args.placeholder, source=source
            )
        except SidecarRefsError as exc:
            print("\n".join(exc.errors), file=sys.stderr)
            return 1
        for path in changed:
            print(f"updated {_display(path)}")
        if not changed:
            print("no changes")
        return 0

    errors = check(args.check, args.root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"ok: {_display(args.check)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
