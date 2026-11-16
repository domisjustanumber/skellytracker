"""`resolve_sidecar_composition`: the bytes of each file, `$ref` and the reference hashes.

Each test writes its files to `tmp_path`, which is the sidecar root.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from skellytracker.core.model_spec.errors import SidecarParseError, SidecarRefError
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition


def write(path: Path, text: str) -> str:
    """Write `text` with LF line endings. Return the SHA-256 of the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def ref(target: str, sha256: str) -> str:
    return f'{{$ref: {target}, sha256: "{sha256}"}}'


def refused(path: Path, root: Path, error: type[Exception], rule: str | None) -> str:
    with pytest.raises(error) as info:
        resolve_sidecar_composition(path, root)
    assert info.value.rules == ((rule,) if rule else ())  # type: ignore[attr-defined]
    return str(info.value)


def test_a_ref_gives_the_content_of_its_target_for_each_type(tmp_path: Path) -> None:
    names = write(tmp_path / "shared" / "names.yaml", "- a\n- b\n")
    block = write(tmp_path / "shared" / "block.yaml", "x: 1\n")
    scalar = write(tmp_path / "shared" / "scalar.yaml", "seven\n")
    top = tmp_path / "detectors" / "m.yaml"
    write(top, f"names: {ref('../shared/names.yaml', names)}\nblock: {ref('../shared/block.yaml', block)}\nitems:\n  - {ref('../shared/scalar.yaml', scalar)}\n")
    assert resolve_sidecar_composition(top, tmp_path) == {"names": ["a", "b"], "block": {"x": 1}, "items": ["seven"]}


def test_a_nested_ref_is_relative_to_the_file_that_holds_it(tmp_path: Path) -> None:
    leaf = write(tmp_path / "shared" / "deep" / "leaf.yaml", "- 1\n")
    middle = write(tmp_path / "shared" / "middle.yaml", f"leaf: {ref('deep/leaf.yaml', leaf)}\n")
    top = tmp_path / "m.yaml"
    write(top, f"middle: {ref('shared/middle.yaml', middle)}\n")
    assert resolve_sidecar_composition(top, tmp_path) == {"middle": {"leaf": [1]}}


def test_an_anchor_and_its_alias_resolve(tmp_path: Path) -> None:
    top = tmp_path / "m.yaml"
    write(top, "a: &shape [1, 2]\nb: *shape\n")
    assert resolve_sidecar_composition(top, tmp_path) == {"a": [1, 2], "b": [1, 2]}


def test_a_wrong_hash_is_refused_before_the_parse(tmp_path: Path) -> None:
    write(tmp_path / "names.yaml", "a: [not closed\n")  # not YAML: a parse would give a parse error
    top = tmp_path / "m.yaml"
    write(top, f"names: {ref('names.yaml', 'a' * 64)}\n")
    message = refused(top, tmp_path, SidecarRefError, "V-format.composition-2")
    assert "names.yaml" in message and "m.yaml" in message


@pytest.mark.parametrize("sha256", ['"ABC"', "1234", '"' + "A" * 64 + '"'])
def test_a_hash_that_is_not_64_lowercase_hex_characters_is_refused(tmp_path: Path, sha256: str) -> None:
    write(tmp_path / "names.yaml", "- a\n")
    top = tmp_path / "m.yaml"
    write(top, f"names: {{$ref: names.yaml, sha256: {sha256}}}\n")
    refused(top, tmp_path, SidecarRefError, "V-format.composition-2")


@pytest.mark.parametrize(
    "directive",
    ["{$ref: names.yaml}", '{$ref: names.yaml, sha256: "HASH", other: 1}', '{$ref: [names.yaml], sha256: "HASH"}'],
)
def test_a_directive_has_exactly_the_keys_ref_and_sha256(tmp_path: Path, directive: str) -> None:
    sha256 = write(tmp_path / "names.yaml", "- a\n")
    top = tmp_path / "m.yaml"
    write(top, f"names: {directive.replace('HASH', sha256)}\n")
    refused(top, tmp_path, SidecarRefError, "V-format.composition-1")


def test_a_missing_target_is_refused(tmp_path: Path) -> None:
    top = tmp_path / "m.yaml"
    write(top, f"names: {ref('nothing.yaml', 'a' * 64)}\n")
    refused(top, tmp_path, SidecarRefError, "V-format.composition-1")


def test_a_cycle_is_refused_and_named(tmp_path: Path) -> None:
    # A cycle cannot hold two correct hashes. The resolver finds the cycle before it reads the target.
    top, other = tmp_path / "m.yaml", tmp_path / "other.yaml"
    other_sha = write(other, f"back: {ref('m.yaml', 'a' * 64)}\n")
    write(top, f"other: {ref('other.yaml', other_sha)}\n")
    message = refused(top, tmp_path, SidecarRefError, "V-format.composition-1")
    assert "cycle" in message and "other.yaml" in message


def test_a_target_outside_the_root_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "root"
    sha256 = write(tmp_path / "outside.yaml", "- a\n")
    top = root / "m.yaml"
    write(top, f"names: {ref('../outside.yaml', sha256)}\n")
    refused(top, root, SidecarRefError, "V-format.composition-4")
    assert resolve_sidecar_composition(top, tmp_path) == {"names": ["a"]}


def test_a_file_outside_the_root_is_refused(tmp_path: Path) -> None:
    top = tmp_path / "m.yaml"
    write(top, "a: 1\n")
    refused(top, tmp_path / "root", SidecarRefError, None)


@pytest.mark.parametrize(
    ("data", "word"),
    [(b"a: 1\r\nb: 2\r\n", "CRLF"), (b"\xef\xbb\xbfa: 1\n", "byte order mark"), (b"a: \xff\n", "UTF-8")],
)
def test_bad_bytes_are_refused_in_the_sidecar_and_in_a_fragment(tmp_path: Path, data: bytes, word: str) -> None:
    top = tmp_path / "m.yaml"
    top.write_bytes(data)
    assert word in refused(top, tmp_path, SidecarParseError, "V-format.composition-3")
    fragment = tmp_path / "fragment.yaml"
    fragment.write_bytes(data)
    write(top, f"part: {ref('fragment.yaml', hashlib.sha256(data).hexdigest())}\n")
    assert "fragment.yaml" in refused(top, tmp_path, SidecarParseError, "V-format.composition-3")


def test_a_duplicate_key_is_refused_at_each_depth(tmp_path: Path) -> None:
    top = tmp_path / "m.yaml"
    write(top, "a: 1\na: 2\n")
    refused(top, tmp_path, SidecarParseError, "V-format.composition-6")
    write(top, "a:\n  - {b: 1, b: 2}\n")
    refused(top, tmp_path, SidecarParseError, "V-format.composition-6")
    sha256 = write(tmp_path / "fragment.yaml", "x: 1\nx: 1\n")
    write(top, f"part: {ref('fragment.yaml', sha256)}\n")
    refused(top, tmp_path, SidecarParseError, "V-format.composition-6")


def test_a_file_that_is_not_yaml_is_a_parse_error(tmp_path: Path) -> None:
    top = tmp_path / "m.yaml"
    write(top, "a: [1, 2\n")
    refused(top, tmp_path, SidecarParseError, None)
    refused(tmp_path / "nothing.yaml", tmp_path, SidecarParseError, None)
