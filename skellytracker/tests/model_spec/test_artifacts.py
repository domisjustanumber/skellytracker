"""The hash check of an ONNX artifact and the hash check cache."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

import pytest

from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.artifacts import HashCache, check_artifact_hash, file_sha256

CONTENT = b"onnx bytes"
SHA = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "root" / "detectors").mkdir(parents=True)
    return tmp_path / "root"


@pytest.fixture
def model(root: Path) -> Path:
    path = root / "detectors" / "demo.onnx"
    path.write_bytes(CONTENT)
    return path


@pytest.fixture
def hashed(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """The files that the cache reads in full, in call order."""
    calls: list[Path] = []

    def counted(path: Path) -> str:
        calls.append(path)
        return file_sha256(path)

    monkeypatch.setattr(artifacts, "file_sha256", counted)
    return calls


def cache_at(tmp_path: Path, **options: bool) -> HashCache:
    return HashCache(tmp_path / "cache" / "hash-cache.json", **options)


def test_a_file_with_the_sidecar_hash_passes_and_a_different_hash_names_the_rule(tmp_path: Path, root: Path, model: Path) -> None:
    cache = cache_at(tmp_path)
    assert check_artifact_hash(model, root, SHA, cache) is None
    failure = check_artifact_hash(model, root, "b" * 64, cache)
    assert failure.rule == "V-common.sizes_and_artifacts-10" and SHA in failure.message and "b" * 64 in failure.message


def test_a_hit_does_not_read_the_file_again_also_from_a_new_process(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    assert cache.sha256_of(model, root) == SHA and cache.sha256_of(model, root) == SHA
    cache.save()
    assert cache_at(tmp_path).sha256_of(model, root) == SHA
    assert hashed == [model]
    record = json.loads(cache.path.read_text(encoding="utf-8"))["records"][f"{root.as_posix()}::detectors/demo.onnx"]
    assert set(record) == {"size", "mtime_ns", "file_id", "sha256", "checked_at"} and record["sha256"] == SHA


def test_a_changed_sidecar_hash_needs_no_new_hash(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    assert check_artifact_hash(model, root, SHA, cache) is None
    assert check_artifact_hash(model, root, "c" * 64, cache) is not None
    assert hashed == [model]


def test_a_change_of_the_size_is_a_miss(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    cache.sha256_of(model, root)
    state = os.stat(model)
    model.write_bytes(CONTENT + b"!")
    os.utime(model, ns=(state.st_atime_ns, state.st_mtime_ns))
    assert cache.sha256_of(model, root) == hashlib.sha256(CONTENT + b"!").hexdigest()
    assert len(hashed) == 2


def test_a_change_of_the_modification_time_is_a_miss(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    cache.sha256_of(model, root)
    state = os.stat(model)
    os.utime(model, ns=(state.st_atime_ns, state.st_mtime_ns + 2_000_000_000))
    assert cache.sha256_of(model, root) == SHA and len(hashed) == 2


def test_a_change_of_the_file_id_is_a_miss(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    cache.sha256_of(model, root)
    state = os.stat(model)
    other = model.with_name("other.onnx")
    other.write_bytes(b"other bits")  # the same size, a different file
    os.utime(other, ns=(state.st_atime_ns, state.st_mtime_ns))
    model.unlink()
    other.rename(model)
    assert os.stat(model).st_mtime_ns == state.st_mtime_ns and os.stat(model).st_size == state.st_size
    assert cache.sha256_of(model, root) == hashlib.sha256(b"other bits").hexdigest()
    assert len(hashed) == 2


def test_a_corrupt_cache_file_is_an_empty_cache_with_one_warning(
    tmp_path: Path, root: Path, model: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "cache" / "hash-cache.json"
    path.parent.mkdir()
    path.write_text('{"records": [', encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        cache = HashCache(path)
    assert len(caplog.records) == 1 and "does not parse" in caplog.text
    assert cache.sha256_of(model, root) == SHA
    cache.save()
    assert list(json.loads(path.read_text(encoding="utf-8"))["records"]) == [f"{root.as_posix()}::detectors/demo.onnx"]


def test_the_write_replaces_the_cache_file_and_leaves_no_temporary_file(
    tmp_path: Path, root: Path, model: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = cache_at(tmp_path)
    cache.sha256_of(model, root)
    replaced: list[tuple[Path, Path]] = []
    replace = os.replace

    def spy(source: str, target: Path) -> None:
        assert json.loads(Path(source).read_text(encoding="utf-8"))["records"]  # complete before the replace
        replaced.append((Path(source), Path(target)))
        replace(source, target)

    monkeypatch.setattr(artifacts.os, "replace", spy)
    cache.save()
    cache.save()  # no changed record: no second write
    assert [(source.parent, target) for source, target in replaced] == [(cache.path.parent, cache.path)]
    assert [item.name for item in cache.path.parent.iterdir()] == ["hash-cache.json"]


def test_the_record_of_a_download_needs_no_second_read(tmp_path: Path, root: Path, model: Path, hashed: list[Path]) -> None:
    cache = cache_at(tmp_path)
    cache.record(model, root, SHA)
    assert check_artifact_hash(model, root, SHA, cache) is None
    assert hashed == []


@pytest.mark.parametrize("by_variable", [False, True])
def test_the_forced_full_hash_reads_each_file_again(
    tmp_path: Path, root: Path, model: Path, hashed: list[Path], monkeypatch: pytest.MonkeyPatch, by_variable: bool
) -> None:
    stale = cache_at(tmp_path)
    stale.record(model, root, "d" * 64)  # a wrong record that a hit would return
    stale.save()
    if by_variable:
        monkeypatch.setenv(artifacts.FULL_HASH_VARIABLE, "1")
    cache = cache_at(tmp_path, full_hash=not by_variable)
    assert cache.sha256_of(model, root) == SHA and cache.sha256_of(model, root) == SHA
    assert len(hashed) == 2


def test_the_default_cache_file_is_in_the_user_cache_folder() -> None:
    path = artifacts.default_hash_cache_path()
    assert path.name == "hash-cache.json" and "skellytracker" in path.parts
