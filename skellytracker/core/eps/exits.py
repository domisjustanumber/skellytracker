"""Unclean exits of a process that held a session on a GPU EP (ADR-21BK item 3, ADR-ER5X item 5).

`build_session()` calls `note_session()` before it opens a session on a GPU EP. The first call of a process
writes a marker file in the folder `sessions` of the EP store, and holds a lock on it for the life of the
process. A clean exit of the interpreter, and `note_exit_requested()`, remove the marker. A marker with no lock
is the marker of a process that ended in an other way: a crash, a kill or a power cut.

`collect()` reads such markers. Each one counts as one unclean exit of each EP and GPU model of the marker.
One unclean exit is a record only. Two in a row mark the EP as failed on this PC: the row of the pair in
`quick-checks.json` gets the result `failed` with the cause `unclean-exits`. A clean exit resets the count,
and a passed quick check replaces the row and removes the count.

The certification code writes no marker: it runs each EP in a child process, and it reports a crash of that
child itself. This module loads no library and uses no network.
"""

import atexit
import os
import sys
import threading
import time
from pathlib import Path

from skellytracker.core.eps import gate, store
from skellytracker.core.eps.catalog import EpCatalog

UNCLEAN_LIMIT = 2  # this many unclean exits in a row mark the EP as failed on this PC
CAUSE = "unclean-exits"

_guard = threading.Lock()
_handle = None  # the open marker of this process; its lock tells an other process that this process lives
_path: Path | None = None
_pairs: set[str] = set()
_exit_requested = False


def _sessions_dir() -> Path:
    return store.store_root() / "sessions"


def _counts_path() -> Path:
    return store.store_root() / "unclean-exits.json"


def _try_lock(handle) -> bool:
    """Take the lock of a marker with no wait. False when an other process holds it."""
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def note_session(catalog: EpCatalog, key: str, gpu, os_name: str) -> None:
    """Record that this process opens a session of the EP on the GPU. It never raises: a store that cannot be
    written gives no marker."""
    global _handle, _path  # noqa: PLW0603 - one marker for the process
    if gate.certification_active() or _exit_requested or gpu is None:
        return
    pair = gate.pair_key(catalog, key, gpu, os_name)
    with _guard:
        if pair in _pairs:
            return
        try:
            if _handle is None:
                collect()  # the markers of earlier processes, before this process adds its own
                folder = _sessions_dir()
                folder.mkdir(parents=True, exist_ok=True)
                _path = folder / f"{os.getpid()}-{time.time_ns()}.marker"
                _handle = open(_path, "a+b")  # noqa: SIM115 - it stays open for the life of the process
                _handle.write(b" ")  # one byte: the Windows lock needs a byte to lock
                _handle.flush()
                _try_lock(_handle)
                atexit.register(_clean_exit)
            _pairs.add(pair)
            store.write_json(_path.with_suffix(".json"), {"pairs": sorted(_pairs)})
        except OSError:
            pass


def _clean_exit() -> None:
    """Remove the marker of this process, and reset the count of each of its pairs."""
    global _handle, _path  # noqa: PLW0603
    with _guard:
        if _handle is None:
            return
        pairs, path = set(_pairs), _path
        try:
            _handle.close()
            path.unlink(missing_ok=True)
            path.with_suffix(".json").unlink(missing_ok=True)
        except OSError:
            pass
        _handle, _path = None, None
        _pairs.clear()
    try:
        with store.store_lock():
            counts = store.read_json(_counts_path()) or {}
            if any(counts.pop(pair, None) is not None for pair in pairs):
                store.write_json(_counts_path(), counts)
    except OSError:
        pass


def note_exit_requested() -> None:
    """The exit notice of an application: the user asked it to close, and it can now end this process in any way.

    After the call, an end of this process is not an unclean exit. The process writes no new marker.
    """
    global _exit_requested  # noqa: PLW0603
    _exit_requested = True
    _clean_exit()


def collect() -> list[str]:
    """Count the markers of each process that is gone, and mark an EP as failed after `UNCLEAN_LIMIT` in a row.

    It returns the pairs that this call marked as failed. It never raises.
    """
    marked = []
    try:
        folder = _sessions_dir()
        if not folder.is_dir():
            return marked
        with store.store_lock():
            gone = []
            for marker in sorted(folder.glob("*.marker")):
                if marker == _path:
                    continue
                try:
                    with open(marker, "r+b") as handle:
                        if not _try_lock(handle):
                            continue  # its process lives
                    record = store.read_json(marker.with_suffix(".json")) or {}
                    marker.unlink()
                    marker.with_suffix(".json").unlink(missing_ok=True)
                except OSError:
                    continue
                gone.extend(pair for pair in record.get("pairs", ()) if isinstance(pair, str))
            if not gone:
                return marked
            counts = store.read_json(_counts_path()) or {}
            checks_path = store.store_root() / "quick-checks.json"
            checks = store.read_json(checks_path) or {}
            for pair in gone:
                counts[pair] = int(counts.get(pair, 0)) + 1
                if counts[pair] >= UNCLEAN_LIMIT and (checks.get(pair) or {}).get("cause") != CAUSE:
                    checks[pair] = {"result": "failed", "cause": CAUSE, "unclean_exits": counts[pair],
                                    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                    marked.append(pair)
            store.write_json(_counts_path(), counts)
            if marked:
                store.write_json(checks_path, checks)
    except OSError:
        pass
    return marked


def forget(pair: str) -> None:
    """Remove the count of a pair. A quick check that passed calls it, inside `store.store_lock()`."""
    counts = store.read_json(_counts_path()) or {}
    if counts.pop(pair, None) is not None:
        store.write_json(_counts_path(), counts)
