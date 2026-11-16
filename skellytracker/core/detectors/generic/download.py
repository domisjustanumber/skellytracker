"""The download of a `url` artifact to the download folder (section `common.sizes_and_artifacts`)."""
from __future__ import annotations

import contextlib
import hashlib
import os
import sys
import threading
import time
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from skellytracker.core.eps._download import DownloadError, fetch
from skellytracker.core.model_spec import artifacts
from skellytracker.core.model_spec.model import ArtifactSpec

_CHUNK = 1 << 20


class ArtifactDownloadError(RuntimeError):
    """The download of an ONNX artifact failed, or its bytes do not have the hash of the sidecar."""


_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


@contextlib.contextmanager
def download_lock(destination: Path) -> Iterator[None]:
    """Hold the lock of one download target: between threads, and between processes on `<download root>/.lock`.

    It waits until the lock is free. The file lock has the form of the lock of the EP store: one
    file for the root, so the folder of a model holds only its ONNX files.
    """
    with _THREAD_LOCKS_GUARD:
        thread_lock = _THREAD_LOCKS.setdefault(os.path.normcase(os.path.abspath(destination)), threading.Lock())
    with thread_lock:
        destination.parent.mkdir(parents=True, exist_ok=True)
        root = artifacts.download_root()
        root.mkdir(parents=True, exist_ok=True)
        with open(root / ".lock", "a+b") as handle:
            if sys.platform == "win32":
                import msvcrt

                while True:  # LK_LOCK stops after 10 s, and a download can hold the lock for longer
                    try:
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle, fcntl.LOCK_UN)


def _extract_onnx(archive: Path, target: Path) -> str:
    """Write the one ONNX file of a zip archive to `target`. Return its SHA-256."""
    with zipfile.ZipFile(archive) as bundle:
        members = [info for info in bundle.infolist() if not info.is_dir() and info.filename.lower().endswith(".onnx")]
        if len(members) != 1:
            raise ArtifactDownloadError(f"the archive must hold exactly one ONNX file; it holds {len(members)}")
        digest = hashlib.sha256()
        # The member is read as a stream to one fixed file, so its name in the archive selects no path.
        with bundle.open(members[0]) as source, target.open("wb") as stream:
            while chunk := source.read(_CHUNK):
                digest.update(chunk)
                stream.write(chunk)
    return digest.hexdigest()


def download_artifact(artifact: ArtifactSpec, destination: Path, *, opener: Any = None) -> Path:
    """Download the ONNX file of `artifact` to `destination`, a file under the download folder.

    Implements: common.sizes_and_artifacts

    The function checks the bytes at `url` against `url_sha256`. When the bytes are a zip archive,
    it extracts the one ONNX file of the archive, with the name `filename`. Then it checks the ONNX
    file against `sha256` (V-common.sizes_and_artifacts-10) and writes the record of the file to
    the hash check cache. A reader never sees a partial file at `destination`. The function raises
    `ArtifactDownloadError` when a step fails, and then `destination` does not change.
    """
    if artifact.url is None or artifact.url_sha256 is None:
        raise ArtifactDownloadError(f"the artifact {artifact.filename} has no `url`")
    part = destination.with_name(destination.name + ".part")
    try:
        fetch(artifact.url, artifact.url_sha256, part, opener=opener)
    except DownloadError as exc:
        raise ArtifactDownloadError(f"the download of {artifact.filename} failed ({exc.code}): {exc}") from exc
    extracted = destination.with_name(destination.name + ".tmp")
    try:
        if zipfile.is_zipfile(part):
            onnx_file, found = extracted, _extract_onnx(part, extracted)
        else:
            onnx_file, found = part, artifact.url_sha256  # `fetch` checked this hash on the bytes of the file
        if found != artifact.sha256:
            raise ArtifactDownloadError(
                f"V-common.sizes_and_artifacts-10: the downloaded file {artifact.filename} has the SHA-256 {found}, "
                f"and the sidecar has {artifact.sha256}"
            )
        os.replace(onnx_file, destination)
    finally:
        part.unlink(missing_ok=True)
        extracted.unlink(missing_ok=True)
    cache = artifacts.HashCache()
    cache.record(destination, artifacts.download_root(), found)
    cache.save()
    return destination
