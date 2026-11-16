"""The download of a `url` artifact, with a fake of the network."""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from typing import Any

import pytest

from skellytracker.core.detectors.generic import download
from skellytracker.core.detectors.generic.download import ArtifactDownloadError, download_artifact
from skellytracker.core.eps._download import DownloadError
from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.model import ArtifactSpec

ONNX = b"the bytes of an ONNX file"
URL = "https://example.org/demo.bin"


def fake_fetch(content: bytes, calls: list[str] | None = None) -> Any:
    """Return a `fetch` that serves `content` and checks its hash, with no network."""

    def fetch(url: str, sha256: str, part: Path, *, opener: Any = None) -> Path:
        if calls is not None:
            calls.append(url)
        if hashlib.sha256(content).hexdigest() != sha256:
            raise DownloadError("hash-mismatch", "the sha256 is not the sha256 of the sidecar")
        part.write_bytes(content)
        return part

    return fetch


def zipped(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, content in files.items():
            bundle.writestr(name, content)
    return buffer.getvalue()


def spec(served: bytes, onnx_file: bytes = ONNX) -> ArtifactSpec:
    digest = hashlib.sha256
    return ArtifactSpec(filename="demo-n_b3_fp32.onnx", sha256=digest(onnx_file).hexdigest(), url=URL, url_sha256=digest(served).hexdigest())


@pytest.fixture
def destination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(artifacts, "default_hash_cache_path", lambda: tmp_path / "cache" / "hash-cache.json")
    monkeypatch.setattr(artifacts, "download_root", lambda: tmp_path / "cache" / "models")
    file = artifacts.download_path("demo@demo-exporter", "0.1.0", "demo-n_b3_fp32.onnx")
    assert file == tmp_path / "cache" / "models" / "demo@demo-exporter" / "0.1.0" / "demo-n_b3_fp32.onnx"
    file.parent.mkdir(parents=True)
    return file


# The name of the ONNX file in the archive selects no path: the host writes `filename`.
@pytest.mark.parametrize("served", [ONNX, zipped({"../folder/end2end.onnx": ONNX, "pipeline.json": b"{}"})], ids=["file", "archive"])
def test_a_download_writes_the_onnx_file_and_its_record_of_the_hash_check_cache(destination: Path, monkeypatch: pytest.MonkeyPatch, served: bytes) -> None:
    monkeypatch.setattr(download, "fetch", fake_fetch(served))
    artifact = spec(served)
    assert download_artifact(artifact, destination) == destination
    assert destination.read_bytes() == ONNX and [item.name for item in destination.parent.iterdir()] == [destination.name]
    monkeypatch.setattr(artifacts, "file_sha256", lambda path: pytest.fail(f"hashed {path} again"))
    assert artifacts.check_artifact_hash(destination, artifacts.download_root(), artifact.sha256, artifacts.HashCache()) is None


@pytest.mark.parametrize(
    ("served", "artifact", "message"),
    [
        (b"other bytes", spec(ONNX), "hash-mismatch"),  # the bytes at `url` are not `url_sha256`
        (zipped({"a.onnx": b"an other graph"}), spec(zipped({"a.onnx": b"an other graph"})), "V-common.sizes_and_artifacts-10"),
        (ONNX, spec(ONNX, b"an other graph"), "V-common.sizes_and_artifacts-10"),
        (zipped({"a.onnx": ONNX, "b.onnx": ONNX}), spec(zipped({"a.onnx": ONNX, "b.onnx": ONNX})), "exactly one ONNX file"),
    ],
    ids=["url_sha256", "sha256-in-archive", "sha256-of-file", "two-onnx-files"],
)
def test_a_download_with_a_wrong_hash_or_a_wrong_archive_writes_no_file(
    destination: Path, monkeypatch: pytest.MonkeyPatch, served: bytes, artifact: ArtifactSpec, message: str
) -> None:
    monkeypatch.setattr(download, "fetch", fake_fetch(served))
    with pytest.raises(ArtifactDownloadError, match=message):
        download_artifact(artifact, destination)
    assert list(destination.parent.iterdir()) == []


def test_an_artifact_with_no_url_has_no_download(destination: Path) -> None:
    with pytest.raises(ArtifactDownloadError, match="has no `url`"):
        download_artifact(ArtifactSpec(filename="demo.onnx", sha256="a" * 64), destination)
