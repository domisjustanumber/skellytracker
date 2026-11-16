"""The hash check of an ONNX artifact, with the hash check cache.

`V-common.sizes_and_artifacts-10` requires that each present ONNX file has the SHA-256 of its
`sha256` field. An ONNX file can have several hundred MB, so the host hashes a file only when it
first sees the file and after the file changes. The cache holds the hash of each file, not a pass
or a fail. Thus a changed sidecar `sha256` needs no new hash.

Limits: the cache finds a corrupt file, a partial download and a wrong file. It does not protect
against a local user with write access. FAT32 and exFAT store the modification time in steps of
2 s. A file that changes within 2 s, with the same size and the same file id, can hit an old record.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import platformdirs

from skellytracker.core.model_spec.errors import Failure

logger = logging.getLogger(__name__)

FULL_HASH_VARIABLE = "SKELLYTRACKER_FULL_HASH"
"""When this environment variable is `1`, each check reads the file and ignores the records."""

_CHUNK = 1 << 20
_RULE = "V-common.sizes_and_artifacts-10"


def default_hash_cache_path() -> Path:
    """Return the cache file in the user cache folder. The cache is not in a sidecar root."""
    return Path(platformdirs.user_cache_dir("skellytracker", appauthor=False)) / "hash-cache.json"


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file in lowercase hex. The function reads the file in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _file_state(path: Path) -> dict[str, Any]:
    # os.stat follows a symlink: a Hugging Face snapshot file gives the state of its blob.
    status = os.stat(path)
    return {"size": status.st_size, "mtime_ns": status.st_mtime_ns, "file_id": [status.st_dev, status.st_ino]}


class HashCache:
    """The hash of each ONNX file that the host hashed, in one JSON file.

    The key of a record is the sidecar root and the path of the file relative to that root. A
    record has `size`, `mtime_ns`, `file_id`, `sha256` and `checked_at`. `full_hash=True`, or the
    environment variable `SKELLYTRACKER_FULL_HASH=1`, hashes each file again.
    """

    def __init__(self, path: Path | None = None, full_hash: bool = False) -> None:
        self.path = default_hash_cache_path() if path is None else path
        self.full_hash = full_hash or os.environ.get(FULL_HASH_VARIABLE) == "1"
        self._records: dict[str, dict[str, Any]] = self._read()
        self._changed = False

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.is_file():
            return {}
        try:
            records = json.loads(self.path.read_text(encoding="utf-8"))["records"]
            if not isinstance(records, dict) or not all(isinstance(record, dict) for record in records.values()):
                raise TypeError("`records` is not a map of records")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            logger.warning("the hash check cache %s does not parse (%s); each file is hashed again", self.path, exc)
            return {}
        return records

    @staticmethod
    def _key(root: Path, file: Path) -> str:
        return f"{root.as_posix()}::{file.relative_to(root).as_posix()}"

    def sha256_of(self, file: Path, root: Path) -> str:
        """Return the SHA-256 of `file`: the record when the file did not change, else a new hash."""
        key, state = self._key(root, file), _file_state(file)
        record = self._records.get(key)
        if not self.full_hash and record is not None and all(record.get(name) == state[name] for name in state):
            return record["sha256"]
        return self._put(key, state, file_sha256(file))

    def record(self, file: Path, root: Path, sha256: str) -> None:
        """Write the record of a file whose hash the caller knows, for example from a download.

        The caller hashes the bytes while it writes them. This function does not read the file.
        """
        self._put(self._key(root, file), _file_state(file), sha256)

    def _put(self, key: str, state: dict[str, Any], sha256: str) -> str:
        checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._records[key] = {**state, "sha256": sha256, "checked_at": checked_at}
        self._changed = True
        return sha256

    def save(self) -> None:
        """Write the cache when a record changed: a temporary file, then `os.replace`.

        A reader never sees a partial file. When several processes write, the last write wins.
        """
        if not self._changed:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.name, suffix=".tmp")
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump({"version": 1, "records": self._records}, stream, indent=1)
            os.replace(temporary, self.path)
        except OSError as exc:  # a cache that cannot be written costs only a new hash at the next start
            logger.warning("cannot write the hash check cache %s: %s", self.path, exc)
            return
        self._changed = False


def check_artifact_hash(file: Path, root: Path, sha256: str, cache: HashCache) -> Failure | None:
    """Return the failure of a present ONNX file whose SHA-256 is not `sha256`, else None.

    Implements: common.sizes_and_artifacts

    `file` is the file that `filename` names, in the folder of its sidecar under the sidecar root
    `root`. `sha256` is the `sha256` field of the artifact (V-common.sizes_and_artifacts-10).
    """
    found = cache.sha256_of(file, root)
    if found == sha256:
        return None
    return Failure(_RULE, f"the file {file} has the SHA-256 {found}, and the sidecar has {sha256}")
