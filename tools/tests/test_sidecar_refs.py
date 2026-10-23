"""Tests for `tools/sidecar_refs.py`, the reference hash tool.

The trees in these tests are small copies of the layout in `specs/sidecar/format/file-layout.md`.
`--write` and `--check` must work without `skellytracker`. Only `resolve` imports it.
"""

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import sidecar_refs
from sidecar_refs import PLACEHOLDER, SidecarRefsError, check, resolve, write

TOOLS_DIR = Path(sidecar_refs.__file__).resolve().parent
SIDECAR_REL = "detectors/object_detectors/m/m.yaml"
BASE_REL = "detectors/object_detectors/b/b.yaml"
HEX = re.compile(r"[0-9a-f]{64}")
URL_HASH = "a6d08a575c9d8b8da7ce6c13e1c7341047fca35594a6d35de04b739eba51139c"

POINTS = "- nose\n- left_eye\n"
OUTER = "# a fragment that refers to a fragment\nnames: {$ref: points.yaml}\nextra: 1\n"
BASE = (
    '---\nschema_version: "vNEXT"\nmodel_id: b\n'
    "display_name: Base\nrole: [object_detector]\ninput:\n  layout: NCHW\n  name: images\n"
)
# One flow artifact, one flow artifact with spaces and quotes, one block artifact.
SIDECAR = f"""\
---
# A comment line

schema_version: "vNEXT"      # the version
model_id:   m
pose:
  tracked_points:   {{$ref: "../../shared/points.yaml"}}    # flow form, double quotes
  connections:
    $ref: ../../shared/outer.yaml    # block form

sizes:
  nano:
    onnx:
      batch_artifacts:
        "1":
          precision_artifacts:
            fp32: {{filename: m-nano_b1_fp32.onnx}}   # flow form
            fp16: {{ filename: 'm-nano_b1_fp16.onnx', url: https://example.invalid/a.zip, url_sha256: "{URL_HASH}" }}
            int8:
              filename: m-nano_b1_int8.onnx    # block form
              url: https://example.invalid/b.zip
              url_sha256: "{URL_HASH}"

# final comment
"""
ONNX_FILES = {
    "m-nano_b1_fp32.onnx": b"fp32 bytes",
    "m-nano_b1_fp16.onnx": b"fp16 bytes",
    "m-nano_b1_int8.onnx": b"int8 bytes",
}
DERIVED_REL = "detectors/object_detectors/d/d.yaml"
DERIVED = 'schema_version: "vNEXT"\nbase: ../b/b.yaml  # parent\nmodel_id: d\n'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put(root: Path, files: dict[str, str | bytes]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            content if isinstance(content, bytes) else content.encode("utf-8")
        )


def standard_files() -> dict[str, str | bytes]:
    return {
        SIDECAR_REL: SIDECAR,
        "detectors/shared/points.yaml": POINTS,
        "detectors/shared/outer.yaml": OUTER,
        BASE_REL: BASE,
    }


def add_onnx_files(root: Path) -> None:
    put(
        root,
        {f"detectors/object_detectors/m/{n}": data for n, data in ONNX_FILES.items()},
    )


@pytest.fixture
def root(tmp_path: Path) -> Path:
    put(tmp_path, standard_files())
    return tmp_path


@pytest.fixture
def root_with_onnx(root: Path) -> Path:
    add_onnx_files(root)
    return root


def sidecar_of(root: Path) -> Path:
    return root / SIDECAR_REL


def read(root: Path, rel: str = SIDECAR_REL) -> str:
    return (root / rel).read_bytes().decode("utf-8")


def run_python(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(  # noqa: S603
        [sys.executable, *args], capture_output=True, text=True, check=False
    )


def snapshot(root: Path) -> dict[Path, bytes]:
    return {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def strip_added(text: str) -> str:
    """Remove the entries that `--write` inserts: a `sha256` entry, a `base` mapping, `source`."""
    text = re.sub(r'base: \{\$ref: (.*?), sha256: "[0-9a-f]{64}"\}', r"base: \1", text)
    text = re.sub(r', sha256: "[0-9a-f]{64}"', "", text)
    text = re.sub(r'\n *sha256: "[0-9a-f]{64}"', "", text)
    return re.sub(r"\nsource:\n  name: .*\n  version: .*", "", text)


def mask_hashes(text: str) -> str:
    return HEX.sub("X" * 64, text)


# --------------------------------------------------------------------------------------------
# Hashed and unhashed trees
# --------------------------------------------------------------------------------------------


def test_an_unhashed_tree_fails_the_check(root: Path) -> None:
    errors = check(sidecar_of(root), root)
    text = "\n".join(errors)
    assert "`$ref` ../../shared/points.yaml has no `sha256`" in text
    assert "`$ref` ../../shared/outer.yaml has no `sha256`" in text
    # The last one is the reference inside the outer fragment.
    assert "`$ref` points.yaml has no `sha256`" in text
    for name in ONNX_FILES:
        assert f"artifact {name} has no `sha256`" in text
    assert len(errors) == 6


def test_write_fills_in_the_hashes_and_check_passes(root_with_onnx: Path) -> None:
    root = root_with_onnx
    changed = write(sidecar_of(root), root)
    assert [p.name for p in changed] == [
        "outer.yaml",
        "m.yaml",
    ]  # the fragment is done first
    assert check(sidecar_of(root), root) == []
    text = read(root)
    points = sha((root / "detectors/shared/points.yaml").read_bytes())
    outer = sha((root / "detectors/shared/outer.yaml").read_bytes())
    assert f'{{$ref: "../../shared/points.yaml", sha256: "{points}"}}' in text
    assert (
        f'$ref: ../../shared/outer.yaml    # block form\n    sha256: "{outer}"\n'
        in text
    )


def test_write_twice_changes_nothing_the_second_time(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    before = snapshot(root)
    assert write(sidecar_of(root), root) == []
    assert snapshot(root) == before


def test_nested_fragments_are_hashed_depth_first(root: Path) -> None:
    write(sidecar_of(root), root)
    outer = read(root, "detectors/shared/outer.yaml")
    inner_hash = sha((root / "detectors/shared/points.yaml").read_bytes())
    assert f'names: {{$ref: points.yaml, sha256: "{inner_hash}"}}' in outer
    # The sidecar holds the hash of the outer fragment AFTER the edit of the outer fragment.
    assert sha(outer.encode("utf-8")) in read(root)
    errors = check(sidecar_of(root), root)
    assert len(errors) == 3
    # Only the hashes of the absent ONNX files are missing.
    assert all("artifact" in e for e in errors)


def test_a_fragment_that_two_files_refer_to_is_read_once(root_with_onnx: Path) -> None:
    root = root_with_onnx
    put(root, {"detectors/shared/other.yaml": "other: {$ref: points.yaml}\n"})
    text = (
        read(root)
        + "second: {$ref: ../../shared/other.yaml}\nthird: {$ref: ../../shared/points.yaml}\n"
    )
    put(root, {SIDECAR_REL: text})
    write(sidecar_of(root), root)
    assert check(sidecar_of(root), root) == []


def test_base_becomes_a_hashed_mapping(root: Path) -> None:
    put(root, {DERIVED_REL: DERIVED})
    path = root / DERIVED_REL
    assert any("`base` ../b/b.yaml has no `sha256`" in e for e in check(path, root))
    write(path, root)
    expected = sha((root / BASE_REL).read_bytes())
    assert read(root, DERIVED_REL) == DERIVED.replace(
        "base: ../b/b.yaml", f'base: {{$ref: ../b/b.yaml, sha256: "{expected}"}}'
    )
    assert check(path, root) == []


def test_a_base_with_quotes_or_a_flow_indicator_stays_valid(root: Path) -> None:
    put(root, {"detectors/object_detectors/b,2/b2.yaml": BASE})
    quoted = 'base: "../b,2/b2.yaml"\n'
    plain = "base: ../b,2/b2.yaml\n"
    for text in (quoted, plain):
        put(root, {DERIVED_REL: text})
        write(root / DERIVED_REL, root)
        loaded = yaml.safe_load(read(root, DERIVED_REL))
        assert loaded["base"]["$ref"] == "../b,2/b2.yaml"
        assert check(root / DERIVED_REL, root) == []


def test_a_base_in_block_form_gets_a_sha256_line(root: Path) -> None:
    put(
        root,
        {
            DERIVED_REL: 'schema_version: "vNEXT"\nbase:\n  $ref: ../b/b.yaml\nmodel_id: d\n'
        },
    )
    path = root / DERIVED_REL
    write(path, root)
    loaded = yaml.safe_load(read(root, DERIVED_REL))
    assert loaded["base"] == {
        "$ref": "../b/b.yaml",
        "sha256": sha((root / BASE_REL).read_bytes()),
    }
    assert check(path, root) == []


# --------------------------------------------------------------------------------------------
# Tampered files, bad bytes, bad references
# --------------------------------------------------------------------------------------------


def test_a_tampered_fragment_fails_the_check(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    (root / "detectors/shared/outer.yaml").write_bytes(b"names: []\n")
    errors = check(sidecar_of(root), root)
    assert len(errors) == 1
    assert errors[0].startswith("detectors/object_detectors/m/m.yaml:")
    assert "`$ref` ../../shared/outer.yaml does not match the file" in errors[0]


def test_a_tampered_inner_fragment_is_found_where_it_is_referred_to(
    root_with_onnx: Path,
) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    (root / "detectors/shared/points.yaml").write_bytes(b"- nose\n- right_eye\n")
    errors = check(sidecar_of(root), root)
    # The outer fragment and the sidecar both hold the hash of the inner fragment.
    # The outer fragment itself is intact, so the sidecar has no error about it.
    assert len(errors) == 2
    assert any(
        e.startswith("detectors/shared/outer.yaml:")
        and "`$ref` points.yaml does not match" in e
        for e in errors
    )
    assert any(
        e.startswith("detectors/object_detectors/m/m.yaml:")
        and "points.yaml does not match" in e
        for e in errors
    )
    assert not any("outer.yaml does not match" in e for e in errors)


def test_write_updates_stale_hashes(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    (root / "detectors/shared/points.yaml").write_bytes(b"- nose\n- right_eye\n")
    changed = write(sidecar_of(root), root)
    assert [p.name for p in changed] == ["outer.yaml", "m.yaml"]
    assert check(sidecar_of(root), root) == []


def test_a_hash_with_the_wrong_form_is_an_error(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    upper = HEX.sub(lambda m: m.group(0).upper(), read(root), count=1)
    put(root, {SIDECAR_REL: upper})
    assert any("lowercase hexadecimal" in e for e in check(sidecar_of(root), root))


def test_an_unquoted_hash_that_loads_as_a_number_is_an_error_and_write_quotes_it(
    root: Path,
) -> None:
    ref = '{$ref: "../../shared/points.yaml"}'
    put(
        root,
        {SIDECAR_REL: SIDECAR.replace(ref, ref[:-1] + ", sha256: " + "0" * 64 + "}")},
    )
    assert any("write it in quotes" in e for e in check(sidecar_of(root), root))
    write(sidecar_of(root), root)
    assert '"../../shared/points.yaml", sha256: "' in read(root)


def test_an_empty_hash_value_is_filled_in(root: Path) -> None:
    put(
        root,
        {
            SIDECAR_REL: "a: {$ref: ../../shared/points.yaml, sha256: }\nb:\n  $ref: ../../shared/points.yaml\n  sha256:\n"
        },
    )
    write(sidecar_of(root), root)
    points = sha(POINTS.encode("utf-8"))
    loaded = yaml.safe_load(read(root))
    assert loaded["a"]["sha256"] == points
    assert loaded["b"]["sha256"] == points


def test_crlf_in_the_sidecar_is_its_own_error(root: Path) -> None:
    path = sidecar_of(root)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    errors = check(path, root)
    crlf = [e for e in errors if "CRLF" in e]
    assert len(crlf) == 1
    assert crlf[0].startswith("detectors/object_detectors/m/m.yaml: ")


def test_write_refuses_a_crlf_sidecar_and_changes_nothing(root: Path) -> None:
    path = sidecar_of(root)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    before = snapshot(root)
    with pytest.raises(SidecarRefsError, match="CRLF"):
        write(path, root, placeholder=True)
    assert snapshot(root) == before


def test_crlf_in_a_fragment_is_reported_once_and_its_hash_still_matches(
    root: Path,
) -> None:
    crlf = POINTS.replace("\n", "\r\n").encode("utf-8")
    assert sha(crlf) != sha(POINTS.encode("utf-8"))  # the reason why CRLF is an error
    put(
        root,
        {
            "detectors/shared/points.yaml": crlf,
            SIDECAR_REL: f'model_id: m\npose: {{$ref: ../../shared/points.yaml, sha256: "{sha(crlf)}"}}\n',
        },
    )
    errors = check(sidecar_of(root), root)
    assert len(errors) == 1
    assert errors[0].startswith("detectors/shared/points.yaml: ")
    assert "CRLF" in errors[0]


def test_write_refuses_a_crlf_fragment(root: Path) -> None:
    put(root, {"detectors/shared/points.yaml": POINTS.replace("\n", "\r\n")})
    before = snapshot(root)
    with pytest.raises(SidecarRefsError) as info:
        write(sidecar_of(root), root)
    assert any(
        e.startswith("detectors/shared/points.yaml: ") and "CRLF" in e
        for e in info.value.errors
    )
    assert snapshot(root) == before


def test_a_byte_order_mark_is_its_own_error(root: Path) -> None:
    path = sidecar_of(root)
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    errors = check(path, root)
    assert sum("byte order mark" in e for e in errors) == 1
    before = snapshot(root)
    with pytest.raises(SidecarRefsError, match="byte order mark"):
        write(path, root)
    assert snapshot(root) == before


def test_a_byte_order_mark_in_a_fragment_is_an_error(root: Path) -> None:
    bom = b"\xef\xbb\xbf" + POINTS.encode("utf-8")
    put(
        root,
        {
            "detectors/shared/points.yaml": bom,
            SIDECAR_REL: f'model_id: m\npose: {{$ref: ../../shared/points.yaml, sha256: "{sha(bom)}"}}\n',
        },
    )
    errors = check(sidecar_of(root), root)
    assert len(errors) == 1
    assert errors[0].startswith("detectors/shared/points.yaml: ")
    assert "byte order mark" in errors[0]


def test_a_file_that_is_not_utf8_is_an_error(root: Path) -> None:
    put(root, {"detectors/shared/points.yaml": b"- caf\xe9\n"})
    assert any("not valid UTF-8" in e for e in check(sidecar_of(root), root))


def test_a_cycle_is_an_error(root: Path) -> None:
    put(
        root,
        {
            "detectors/shared/a.yaml": "x: {$ref: b.yaml}\n",
            "detectors/shared/b.yaml": "y: {$ref: a.yaml}\n",
        },
    )
    path = root / "detectors/shared/a.yaml"
    chain = (
        "detectors/shared/a.yaml -> detectors/shared/b.yaml -> detectors/shared/a.yaml"
    )
    assert any("cycle" in e and chain in e for e in check(path, root))
    with pytest.raises(SidecarRefsError, match="cycle"):
        write(path, root)


def test_a_missing_target_is_an_error(root: Path) -> None:
    (root / "detectors/shared/points.yaml").unlink()
    assert any("does not exist" in e for e in check(sidecar_of(root), root))


def test_a_missing_sidecar_is_an_error(root: Path) -> None:
    assert check(root / "detectors/nothing.yaml", root) == [
        f"{(root / 'detectors/nothing.yaml').resolve().as_posix()}: file not found"
    ]


def test_a_target_outside_the_root_is_an_error(root: Path) -> None:
    (root.parent / "outside.yaml").write_text("- x\n", encoding="utf-8")
    put(root, {SIDECAR_REL: "model_id: m\nx: {$ref: ../../../../outside.yaml}\n"})
    assert any("outside the root" in e for e in check(sidecar_of(root), root))


def test_a_ref_mapping_with_other_keys_is_an_error(root: Path) -> None:
    put(
        root,
        {SIDECAR_REL: "model_id: m\nx: {$ref: ../../shared/points.yaml, other: 1}\n"},
    )
    assert any(
        "must hold only `$ref` and `sha256`" in e for e in check(sidecar_of(root), root)
    )
    with pytest.raises(SidecarRefsError):
        write(sidecar_of(root), root)


# --------------------------------------------------------------------------------------------
# Artifacts
# --------------------------------------------------------------------------------------------


def test_flow_mapping_artifacts_get_the_hash_after_the_filename(root: Path) -> None:
    put(
        root,
        {
            "detectors/object_detectors/m/m-nano_b1_fp32.onnx": ONNX_FILES[
                "m-nano_b1_fp32.onnx"
            ]
        },
    )
    write(sidecar_of(root), root)
    text = read(root)
    digest = sha(ONNX_FILES["m-nano_b1_fp32.onnx"])
    assert (
        f'fp32: {{filename: m-nano_b1_fp32.onnx, sha256: "{digest}"}}   # flow form'
        in text
    )
    # An ONNX file that is absent gets nothing without --placeholder.
    assert ", sha256:" not in next(
        line for line in text.splitlines() if "fp16:" in line
    )


def test_a_flow_mapping_with_spaces_and_quotes_keeps_them(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    digest = sha(ONNX_FILES["m-nano_b1_fp16.onnx"])
    expected = f"fp16: {{ filename: 'm-nano_b1_fp16.onnx', sha256: \"{digest}\", url: https://example.invalid/a.zip"
    assert expected in read(root)


def test_a_block_mapping_artifact_gets_a_line_after_the_filename_line(
    root_with_onnx: Path,
) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    digest = sha(ONNX_FILES["m-nano_b1_int8.onnx"])
    assert (
        "              filename: m-nano_b1_int8.onnx    # block form\n"
        f'              sha256: "{digest}"\n'
        "              url: https://example.invalid/b.zip\n"
    ) in read(root)


def test_the_placeholder_goes_on_an_artifact_without_a_hash_and_a_file(
    root: Path,
) -> None:
    write(sidecar_of(root), root, placeholder=True)
    assert read(root).count(f'sha256: "{PLACEHOLDER}"') == 3


def test_the_placeholder_never_replaces_a_real_hash(root: Path) -> None:
    real = "ab" * 32
    put(
        root,
        {
            SIDECAR_REL: SIDECAR.replace(
                "{filename: m-nano_b1_fp32.onnx}",
                f'{{filename: m-nano_b1_fp32.onnx, sha256: "{real}"}}',
            )
        },
    )
    write(sidecar_of(root), root, placeholder=True)
    text = read(root)
    assert f'm-nano_b1_fp32.onnx, sha256: "{real}"' in text
    assert text.count(f'sha256: "{PLACEHOLDER}"') == 2


def test_a_real_hash_of_an_absent_file_is_kept_without_the_option(root: Path) -> None:
    real = "ab" * 32
    put(
        root,
        {
            SIDECAR_REL: SIDECAR.replace(
                "{filename: m-nano_b1_fp32.onnx}",
                f'{{filename: m-nano_b1_fp32.onnx, sha256: "{real}"}}',
            )
        },
    )
    write(sidecar_of(root), root)
    assert f'm-nano_b1_fp32.onnx, sha256: "{real}"' in read(root)


def test_a_present_file_replaces_the_placeholder_with_its_real_hash(root: Path) -> None:
    write(sidecar_of(root), root, placeholder=True)
    put(root, {"detectors/object_detectors/m/m-nano_b1_fp32.onnx": b"new"})
    write(sidecar_of(root), root, placeholder=True)
    text = read(root)
    assert f'm-nano_b1_fp32.onnx, sha256: "{sha(b"new")}"' in text
    assert text.count(f'sha256: "{PLACEHOLDER}"') == 2


def test_check_verifies_an_onnx_hash_only_when_the_file_is_present(root: Path) -> None:
    real = "ab" * 32
    put(
        root,
        {
            SIDECAR_REL: SIDECAR.replace(
                "{filename: m-nano_b1_fp32.onnx}",
                f'{{filename: m-nano_b1_fp32.onnx, sha256: "{real}"}}',
            )
        },
    )
    other_files = [
        "detectors/object_detectors/m/m-nano_b1_fp16.onnx",
        "detectors/object_detectors/m/m-nano_b1_int8.onnx",
    ]
    put(root, dict.fromkeys(other_files, b"x"))
    write(sidecar_of(root), root)
    # The fp32 file is absent: check does not verify its hash.
    assert check(sidecar_of(root), root) == []
    put(root, {"detectors/object_detectors/m/m-nano_b1_fp32.onnx": b"other bytes"})
    errors = check(sidecar_of(root), root)
    assert len(errors) == 1
    assert (
        "`sha256` of artifact m-nano_b1_fp32.onnx does not match the file" in errors[0]
    )
    write(sidecar_of(root), root)
    assert check(sidecar_of(root), root) == []


def test_an_artifact_filename_cannot_leave_the_folder(root: Path) -> None:
    put(root, {SIDECAR_REL: SIDECAR.replace("m-nano_b1_fp32.onnx", "../x.onnx")})
    assert any("leaves the sidecar folder" in e for e in check(sidecar_of(root), root))


def test_artifacts_in_a_fragment_use_the_folder_of_the_sidecar(root: Path) -> None:
    # `filename` is relative to the leaf model folder, also when a fragment declares it.
    put(
        root,
        {
            "detectors/shared/arts.yaml": "precision_artifacts:\n  fp32: {filename: f.onnx}\n",
            "detectors/shared/f.onnx": b"next to the fragment",
            "detectors/object_detectors/m/f.onnx": b"next to the sidecar",
            SIDECAR_REL: "model_id: m\nsizes: {$ref: ../../shared/arts.yaml}\n",
        },
    )
    write(sidecar_of(root), root)
    fragment = read(root, "detectors/shared/arts.yaml")
    assert f'sha256: "{sha(b"next to the sidecar")}"' in fragment
    assert sha(b"next to the fragment") not in fragment
    assert check(sidecar_of(root), root) == []


def test_an_onnx_file_next_to_the_fragment_only_is_not_used(root: Path) -> None:
    put(
        root,
        {
            "detectors/shared/arts.yaml": "precision_artifacts:\n  fp32: {filename: f.onnx}\n",
            "detectors/shared/f.onnx": b"next to the fragment",
            SIDECAR_REL: "model_id: m\nsizes: {$ref: ../../shared/arts.yaml}\n",
        },
    )
    write(sidecar_of(root), root)  # it adds only the hash of the $ref
    assert "sha256" not in read(root, "detectors/shared/arts.yaml")


BASE_WITH_ARTIFACT = BASE + (
    "sizes:\n  nano:\n    onnx:\n      batch_artifacts:\n"
    '        "1":\n          precision_artifacts:\n            fp32: {filename: b.onnx}\n'
)


def test_artifacts_in_a_base_use_the_folder_of_the_derived_sidecar(root: Path) -> None:
    # The runtime loads `sidecar_dir / filename` with the folder of the leaf sidecar.
    put(
        root,
        {
            BASE_REL: BASE_WITH_ARTIFACT,
            DERIVED_REL: DERIVED,
            "detectors/object_detectors/b/b.onnx": b"next to the base",
            "detectors/object_detectors/d/b.onnx": b"next to the derived sidecar",
        },
    )
    write(root / DERIVED_REL, root)
    base = read(root, BASE_REL)
    assert f'sha256: "{sha(b"next to the derived sidecar")}"' in base
    assert sha(b"next to the base") not in base
    assert check(root / DERIVED_REL, root) == []


# --------------------------------------------------------------------------------------------
# The placeholder is valid only under specs/sidecar/examples/
# --------------------------------------------------------------------------------------------


def test_the_placeholder_is_accepted_only_under_the_examples_folder(
    tmp_path: Path,
) -> None:
    examples = tmp_path / "specs" / "sidecar" / "examples"
    elsewhere = tmp_path / "specs" / "sidecar" / "other"
    for base in (examples, elsewhere):
        put(base, standard_files())
        write(base / SIDECAR_REL, base, placeholder=True)
    assert check(examples / SIDECAR_REL, examples) == []
    errors = check(elsewhere / SIDECAR_REL, elsewhere)
    assert len(errors) == 3
    assert all("placeholder" in e and "specs/sidecar/examples/" in e for e in errors)


def test_the_placeholder_is_rejected_in_a_plain_folder(root: Path) -> None:
    write(sidecar_of(root), root, placeholder=True)
    assert len(check(sidecar_of(root), root)) == 3


def test_the_placeholder_in_a_fragment_outside_the_examples_is_rejected(
    tmp_path: Path,
) -> None:
    sidecar = tmp_path / "specs/sidecar/examples/detectors/m/m.yaml"
    fragment = tmp_path / "specs/sidecar/other/f.yaml"
    put(
        tmp_path,
        {
            "specs/sidecar/examples/detectors/m/m.yaml": "model_id: m\nx: {$ref: ../../../other/f.yaml}\n",
            "specs/sidecar/other/f.yaml": "precision_artifacts:\n  fp32: {filename: f.onnx}\n",
        },
    )
    write(sidecar, tmp_path, placeholder=True)
    errors = check(sidecar, tmp_path)
    assert len(errors) == 1
    assert errors[0].startswith("specs/sidecar/other/f.yaml:")
    assert fragment.exists()


# --------------------------------------------------------------------------------------------
# --write keeps every other byte
# --------------------------------------------------------------------------------------------


def test_write_keeps_every_byte_outside_the_inserted_entries(
    root_with_onnx: Path,
) -> None:
    root = root_with_onnx
    put(
        root,
        {
            SIDECAR_REL: SIDECAR.replace(
                "model_id:   m\n",
                "model_id:   m\nbase: '../b/b.yaml'   # single quotes\n",
            )
        },
    )
    before = {p: p.read_bytes().decode("utf-8") for p in root.rglob("*.yaml")}
    write(sidecar_of(root), root, source=("openmmlab-exporter", "0.1.0"))
    after = {p: p.read_bytes().decode("utf-8") for p in root.rglob("*.yaml")}
    changed = {p.name for p in before if before[p] != after[p]}
    assert changed == {"m.yaml", "outer.yaml"}
    for path in before:
        assert strip_added(after[path]) == before[path]
    assert "\r" not in after[sidecar_of(root)]
    hashes = HEX.findall(after[sidecar_of(root)])
    # Two url_sha256 values, then: the points fragment, the outer fragment, base, 3 artifacts.
    assert len(hashes) == 2 + 6


def test_write_keeps_a_file_without_a_final_newline(root: Path) -> None:
    put(root, {SIDECAR_REL: "model_id: m\npose:\n  $ref: ../../shared/points.yaml"})
    write(sidecar_of(root), root)
    text = read(root)
    assert text.startswith(
        'model_id: m\npose:\n  $ref: ../../shared/points.yaml\n  sha256: "'
    )
    assert not text.endswith("\n")
    assert check(sidecar_of(root), root) == []


def test_write_keeps_the_comments_around_a_block_value(root: Path) -> None:
    put(
        root,
        {
            SIDECAR_REL: "model_id: m\nx:\n  - $ref: ../../shared/points.yaml   # keep\n    # inner comment\n  - 2\n"
        },
    )
    write(sidecar_of(root), root)
    text = read(root)
    assert '  - $ref: ../../shared/points.yaml   # keep\n    sha256: "' in text
    assert text.endswith('"\n    # inner comment\n  - 2\n')
    assert yaml.safe_load(text)["x"][1] == 2


def test_an_update_keeps_the_quote_style_of_the_hash(root: Path) -> None:
    put(
        root,
        {
            SIDECAR_REL: "model_id: m\n"
            f"a: {{$ref: ../../shared/points.yaml, sha256: '{'1' * 64}'}}\n"
            f'b: {{$ref: ../../shared/points.yaml, sha256: "{"2" * 64}"}}\n',
        },
    )
    before = read(root)
    write(sidecar_of(root), root)
    after = read(root)
    assert mask_hashes(after) == mask_hashes(before)
    points = sha(POINTS.encode("utf-8"))
    assert f"sha256: '{points}'" in after
    assert f'sha256: "{points}"' in after


def test_write_changes_no_file_when_there_is_an_error(root: Path) -> None:
    (root / "detectors/shared/points.yaml").unlink()
    before = snapshot(root)
    with pytest.raises(SidecarRefsError):
        write(sidecar_of(root), root, placeholder=True)
    assert snapshot(root) == before


# --------------------------------------------------------------------------------------------
# --source
# --------------------------------------------------------------------------------------------


def test_source_is_inserted_after_schema_version_when_the_file_has_none(
    root: Path,
) -> None:
    write(sidecar_of(root), root, source=("openmmlab-exporter", "0.1.0"))
    text = read(root)
    assert (
        'schema_version: "vNEXT"      # the version\nsource:\n  name: openmmlab-exporter\n  version: 0.1.0\nmodel_id:'
        in text
    )
    assert yaml.safe_load(text)["source"] == {
        "name": "openmmlab-exporter",
        "version": "0.1.0",
    }
    assert strip_added(text) == SIDECAR


def test_source_never_changes_an_existing_source(root: Path) -> None:
    text = "schema_version: vNEXT\nsource:\n  name:   other   # mine\n  version: '9'\nmodel_id: m\n"
    put(root, {SIDECAR_REL: text})
    assert write(sidecar_of(root), root, source=("openmmlab-exporter", "0.1.0")) == []
    assert read(root) == text


def test_a_version_that_would_load_as_a_number_is_quoted(root: Path) -> None:
    put(root, {SIDECAR_REL: "schema_version: vNEXT\nmodel_id: m\n"})
    write(sidecar_of(root), root, source=("skellytracker", "1.0"))
    text = read(root)
    assert 'version: "1.0"' in text
    assert yaml.safe_load(text)["source"]["version"] == "1.0"


def test_source_goes_before_the_first_key_when_there_is_no_schema_version(
    root: Path,
) -> None:
    put(root, {SIDECAR_REL: "---\n# note\nmodel_id: m\nrole: [pose_estimator]\n"})
    write(sidecar_of(root), root, source=("x", "1.2.3"))
    assert (
        read(root)
        == "---\n# note\nsource:\n  name: x\n  version: 1.2.3\nmodel_id: m\nrole: [pose_estimator]\n"
    )


def test_source_is_added_to_the_named_sidecar_only(root: Path) -> None:
    put(root, {DERIVED_REL: DERIVED})
    write(root / DERIVED_REL, root, source=("x", "1"))
    assert "source:" in read(root, DERIVED_REL)
    assert "source:" not in read(root, BASE_REL)
    assert "source:" not in read(root, "detectors/shared/outer.yaml")


def test_source_works_with_the_hashes_in_one_write(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root, source=("x", "1"))
    assert check(sidecar_of(root), root) == []
    assert yaml.safe_load(read(root))["source"] == {"name": "x", "version": "1"}


# --------------------------------------------------------------------------------------------
# resolve (temporary helper)
# --------------------------------------------------------------------------------------------


def package_resolve(path: Path, root: Path) -> object:
    from skellytracker.core.sidecar.resolution import resolve_sidecar_composition

    return resolve_sidecar_composition(path, root)


def test_resolve_accepts_an_unhashed_tree_and_matches_the_package_resolver(
    root: Path,
) -> None:
    result = resolve(sidecar_of(root), root)
    assert result == package_resolve(sidecar_of(root), root)
    assert result["pose"]["connections"]["names"] == ["nose", "left_eye"]


def test_resolve_accepts_a_hashed_tree_and_gives_the_same_data(
    root_with_onnx: Path,
) -> None:
    root = root_with_onnx
    unhashed = resolve(sidecar_of(root), root)
    write(sidecar_of(root), root)
    assert "sha256" in read(root, "detectors/shared/outer.yaml")
    hashed = resolve(sidecar_of(root), root)
    assert hashed["pose"] == unhashed["pose"]
    # The artifact hashes stay in the data: they are valid fields.
    fp32 = hashed["sizes"]["nano"]["onnx"]["batch_artifacts"]["1"][
        "precision_artifacts"
    ]["fp32"]
    assert fp32 == {
        "filename": "m-nano_b1_fp32.onnx",
        "sha256": sha(ONNX_FILES["m-nano_b1_fp32.onnx"]),
    }


def test_resolve_handles_a_hashed_base(root: Path) -> None:
    put(root, {DERIVED_REL: DERIVED + "display_name: Derived\ninput:\n  name: null\n"})
    path = root / DERIVED_REL
    unhashed = resolve(path, root)
    assert unhashed == package_resolve(path, root)
    write(path, root)
    assert "base: {$ref: ../b/b.yaml, sha256:" in read(root, DERIVED_REL)
    hashed = resolve(path, root)
    assert hashed == unhashed
    assert hashed["model_id"] == "d"
    assert hashed["display_name"] == "Derived"
    assert hashed["input"] == {
        "layout": "NCHW"
    }  # `name: null` deletes the key of the base
    assert hashed["role"] == ["object_detector"]


def test_resolve_rejects_a_tampered_fragment(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    (root / "detectors/shared/outer.yaml").write_bytes(b"names: []\n")
    with pytest.raises(SidecarRefsError, match="does not match"):
        resolve(sidecar_of(root), root)


def test_resolve_rejects_a_bad_hash_in_a_nested_fragment(root: Path) -> None:
    write(sidecar_of(root), root)
    (root / "detectors/shared/points.yaml").write_bytes(b"- other\n")
    with pytest.raises(SidecarRefsError) as info:
        resolve(sidecar_of(root), root)
    assert any(e.startswith("detectors/shared/outer.yaml:") for e in info.value.errors)


def test_resolve_rejects_the_placeholder_outside_the_examples(root: Path) -> None:
    write(sidecar_of(root), root, placeholder=True)
    with pytest.raises(SidecarRefsError, match="placeholder"):
        resolve(sidecar_of(root), root)


def test_resolve_does_not_change_the_tree(root_with_onnx: Path) -> None:
    root = root_with_onnx
    write(sidecar_of(root), root)
    before = snapshot(root)
    resolve(sidecar_of(root), root)
    assert snapshot(root) == before


# --------------------------------------------------------------------------------------------
# --write and --check do not import skellytracker
# --------------------------------------------------------------------------------------------


def test_write_and_check_do_not_import_skellytracker(root_with_onnx: Path) -> None:
    root = root_with_onnx
    sidecar = str(sidecar_of(root))
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(TOOLS_DIR)!r})\n"
        "import sidecar_refs\n"
        f"assert sidecar_refs.main(['--write', {sidecar!r}, '--root', {str(root)!r}, '--source', 'x==1']) == 0\n"
        f"assert sidecar_refs.main(['--check', {sidecar!r}, '--root', {str(root)!r}]) == 0\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] == 'skellytracker')\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    result = run_python("-I", "-c", script)
    assert result.returncode == 0, result.stdout + result.stderr


def test_only_resolve_imports_skellytracker() -> None:
    tree = ast.parse((TOOLS_DIR / "sidecar_refs.py").read_text(encoding="utf-8"))
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    found = []
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        for module in modules:
            top = module.split(".")[0]
            assert top not in {"tests", "tools"}, module
            if top == "skellytracker":
                scope = parents[node]
                while not isinstance(scope, ast.FunctionDef | ast.Module):
                    scope = parents[scope]
                found.append(getattr(scope, "name", "<module>"))
    assert found == ["resolve"]


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


def test_the_command_line_writes_and_checks(
    root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = str(sidecar_of(root))
    assert sidecar_refs.main(["--check", path]) == 1
    assert "has no `sha256`" in capsys.readouterr().err
    assert sidecar_refs.main(["--write", path, "--placeholder"]) == 0
    assert "updated" in capsys.readouterr().out
    assert sidecar_refs.main(["--write", path, "--placeholder"]) == 0
    assert "no changes" in capsys.readouterr().out
    # The placeholder is not valid outside the examples folder.
    assert sidecar_refs.main(["--check", path]) == 1
    assert "placeholder" in capsys.readouterr().err


def test_the_command_line_runs_as_a_script(root: Path) -> None:
    path = str(sidecar_of(root))
    tool = str(TOOLS_DIR / "sidecar_refs.py")
    assert run_python(tool, "--write", path).returncode == 0
    result = run_python(tool, "--check", path)
    # The ONNX files are absent, so their hashes are missing.
    assert result.returncode == 1
    assert "artifact m-nano_b1_fp32.onnx has no `sha256`" in result.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--write", "a", "--check", "b"],
        ["--check", "a", "--placeholder"],
        ["--check", "a", "--source", "x==1"],
        ["--write", "a", "--source", "no-version"],
        ["--write", "a", "--source", "==1"],
    ],
)
def test_the_command_line_rejects_bad_arguments(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as info:
        sidecar_refs.main(argv)
    assert info.value.code == 2


def test_the_default_root(tmp_path: Path) -> None:
    sidecar = tmp_path / "exports" / "detectors" / "object_detectors" / "m" / "m.yaml"
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text("x: 1\n", encoding="utf-8")
    assert sidecar_refs.default_root(sidecar) == (tmp_path / "exports").resolve()
    loose = tmp_path / "loose" / "m.yaml"
    loose.parent.mkdir()
    assert sidecar_refs.default_root(loose) == loose.parent.resolve()
