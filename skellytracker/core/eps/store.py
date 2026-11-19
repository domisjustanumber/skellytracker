"""The EP store: its root, its layout, its lock, the verdict file and the state of each pack.

The store is `platformdirs.user_data_dir("skellytracker", appauthor=False)/eps`, or the folder of
`SKELLYTRACKER_EP_STORE`. The EP caches (`cache_root()`) are in the user cache folder, or in the
folder of `SKELLYTRACKER_EP_CACHE`. One store serves each checkout and each application of the user. A pack
folder `<pack_id>/<pack_ver>/` does not change after its install.

    <root>/<pack_id>/<pack_ver>/pack.json   the manifest
    <root>/<pack_id>/<pack_ver>/...         the unpacked wheels, and licenses/
    <root>/refs/<consumer_id>.json          one file for each consumer; the input of gc()
    <root>/verdicts.json                    the verification results
    <root>/field-test.json                  the opt-in to each `field-test` EP key (ADR-Z5X7)
    <root>/windows-ml.json                  each EP key that this store installed from the Windows ML catalog (ADR-XSE7)
    <root>/.lock                            the lock between processes
    <root>/.partial/                        downloads that are not complete, kept for a resume
    <root>/.staging/, <root>/.trash/        an install in progress, and deletes that wait
"""

import contextlib
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path

import platformdirs

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps.catalog import EpCatalog
from skellytracker.core.eps.records import PackState

PATH_LIMIT = 240  # a longer DLL path fails registration on Windows, also with long paths enabled
STORE_VARIABLE = "SKELLYTRACKER_EP_STORE"
CACHE_VARIABLE = "SKELLYTRACKER_EP_CACHE"
FALLBACK_VARIABLE = "SKELLYTRACKER_EP_ORT_FALLBACK"  # only the second environment of the certify suite sets it (ADR-XSE7)
logger = logging.getLogger(__name__)
_warned: set[str] = set()


def store_root() -> Path:
    override = os.environ.get(STORE_VARIABLE)
    return Path(override) if override else Path(platformdirs.user_data_dir("skellytracker", appauthor=False)) / "eps"


def cache_root() -> Path:
    """The folder of the EP caches, for example the TensorRT RTX runtime cache, or the folder of `SKELLYTRACKER_EP_CACHE`.

    The certify suite sets the two variables to folders of its work folder, so that a run uses and
    changes nothing of the user (decision Y14H).
    """
    override = os.environ.get(CACHE_VARIABLE)
    return Path(override) if override else Path(platformdirs.user_cache_dir("skellytracker", appauthor=False)) / "ep-cache"


def pack_dir(pack_id: str, version: str) -> Path:
    return store_root() / pack_id / version


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path: Path, data: dict) -> None:
    """Write a JSON file with one `os.replace`, so a reader never sees a part of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def read_manifest(pack_id: str, version: str) -> dict | None:
    return read_json(pack_dir(pack_id, version) / "pack.json")


def path_guard(folder: Path, relative_paths) -> str | None:
    """The reason when a file path of a pack in `folder` has `PATH_LIMIT` characters or more; else `None`."""
    longest = max((len(str(folder / path)) for path in relative_paths), default=len(str(folder)))
    if longest < PATH_LIMIT:
        return None
    return (f"a file path of the pack has {longest} characters, and the limit is {PATH_LIMIT - 1}. "
            f"Set {STORE_VARIABLE} to a shorter folder.")


@contextlib.contextmanager
def store_lock():
    """The lock between processes on `<root>/.lock`. It waits until the lock is free."""
    root = store_root()
    root.mkdir(parents=True, exist_ok=True)
    with open(root / ".lock", "a+b") as handle:
        if sys.platform == "win32":
            import msvcrt

            while True:  # LK_LOCK stops after 10 s, and an install can hold the lock for longer
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


def entry_digest(catalog: EpCatalog, pack: dict) -> str:
    """The sha256 of the catalog entry of a pack: its EP row with no pack list, its own pack row and its lock row.

    For a built-in EP and an EP of the Windows ML catalog, `pack["id"]` is the EP key, and the entry is the EP row.
    A YAML comment, an other EP, an other pack and the other blocks of the catalog are not in it (ADR-YPH2).
    """
    found = catalog.pack_by_id(pack["id"])
    key, row = found if found else (pack["id"], None)
    ep_row = {name: value for name, value in catalog.data["eps"][key].items() if name not in ("packs", "test_packs")}
    entry = [ep_row, row, catalog.pack_lock(pack["id"]) if row else None]
    return hashlib.sha256(json.dumps(entry, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def verdict_key(catalog: EpCatalog, pack: dict, gpu, device_key: str | None, os_build) -> str:
    """The key of a verification result. A new driver, ONNX Runtime distribution, pack, device, OS build or catalog
    entry of the pack (`entry_digest()`) gives a new key.

    In the second environment of the certify suite, the ONNX Runtime part is the version of that environment.
    """
    ids = "none" if gpu is None else f"{gpu.pci_vendor_id}:{gpu.pci_device_id}:{gpu.pci_subsys_id}"
    driver = None if gpu is None else gpu.driver_version
    ort = os.environ.get(FALLBACK_VARIABLE) or catalog.ort_distribution[1]
    return "|".join(str(part) for part in (ort, pack["id"], pack["version"], driver, ids, device_key,
                                           os_build, entry_digest(catalog, pack)))


def read_verdicts() -> dict:
    return read_json(store_root() / "verdicts.json") or {}


def write_verdict(key: str, record: dict) -> None:
    with store_lock():
        verdicts = read_verdicts()
        verdicts[key] = record
        write_json(store_root() / "verdicts.json", verdicts)


def field_test_opt_ins() -> dict:
    """The opt-in of each `field-test` EP key of this store: EP key -> `{"opted_in_at": <Unix time>}`."""
    return read_json(store_root() / "field-test.json") or {}


def opt_in_field_test(key: str) -> None:
    """Record the opt-in to a `field-test` EP key in this store. Only an explicit user action and the certify suite call it."""
    with store_lock():
        write_json(store_root() / "field-test.json", {**field_test_opt_ins(), key: {"opted_in_at": int(time.time())}})


def field_test_reason(catalog: EpCatalog, key: str) -> str | None:
    """The reason when an EP key is a `field-test` EP with no opt-in in this store; else `None`."""
    if catalog.ep_status(key) != "field-test" or key in field_test_opt_ins():
        return None
    return f"the EP '{key}' is in a field test, and this EP store has no opt-in for it"


def windows_ml_installs() -> dict:
    """The record of each EP key that this store installed from the Windows ML catalog (`windows_ml.install()`)."""
    return read_json(store_root() / "windows-ml.json") or {}


def _verdict_state(catalog: EpCatalog, pack: dict, gpu, device_key, os_build) -> tuple[PackState, str | None, str | None]:
    """The state of an installed EP from its stored verification result and its ONNX Runtime claim."""
    verdict = read_verdicts().get(verdict_key(catalog, pack, gpu, device_key, os_build))
    if verdict is not None and not verdict["ok"] and verdict["level"] == "L2":
        return "not_ready", "verify-failed", verdict.get("reason")
    if catalog.ort_untested(pack):
        return "untested-ort", "untested-ort", (f"the pack {pack['id']} {pack['version']} is not tested with "
                                                f"ONNX Runtime {catalog.ort_version}")
    if verdict is not None and verdict["ok"] and verdict["level"] == "L3":
        return "ready", None, None
    reason = "no trial session ran yet" if verdict is None or verdict["ok"] else verdict.get("reason")
    return "installed_unverified", None, reason


def windows_ml_pack(catalog: EpCatalog, key: str) -> dict:
    """The stand-in pack row of an EP of the Windows ML catalog: the package version of its record for the verification
    key, and the ONNX Runtime of the catalog as its claim, because Windows ML gives the EP for its own ONNX Runtime."""
    release = ".".join(catalog.ort_version.split(".")[:2])
    return {"id": key, "version": (windows_ml_installs().get(key) or {}).get("version") or "windows-ml",
            "ort": {"vendor_tested": [release, release]}}


def warn_once(key: str, text: str) -> None:
    """Log one warning line for each process and each key."""
    if key not in _warned:
        _warned.add(key)
        logger.warning(text)


def pack_state(catalog: EpCatalog, key: str, gpu=None, device_key: str | None = None,
               os_build=None) -> tuple[PackState, str | None, str | None]:
    """The state of an EP key for one GPU of this host: `(state, reason code, reason)`.

    It loads no library and uses no network. `gpu` is the `GpuInfo` of the device, or `None` when
    no GPU of the host passes the floors of the pack. A state in `USABLE_STATES` is ready.
    A built-in EP with `selects_gpu` takes `gpu` as a pack does. A `field-test` EP with no opt-in
    in this store is `field_test` (ADR-Z5X7). An EP of the Windows ML catalog takes `gpu` as a pack
    does. It is `not_installed` until `windows_ml.install()` records it in this store (ADR-XSE7).
    """
    row = catalog.ep(key)
    windows_ml = catalog.windows_ml(key)
    if row["kind"] == "builtin" or windows_ml:
        if "platforms" in row and catalog_module.platform_tag() not in row["platforms"]:
            return "unsupported", "os", f"the EP '{key}' is only for {', '.join(row['platforms'])}"
        if (row.get("selects_gpu") or windows_ml) and gpu is None:
            return "unsupported", "no-device", f"no GPU of this host can run the EP '{key}'"
        field_test = field_test_reason(catalog, key)
        if field_test:
            return "field_test", "field-test", field_test
        if not windows_ml:
            return "builtin", None, None
        if (windows_ml_installs().get(key) or {"pending": True}).get("pending"):  # an install that did not end is not one
            return "not_installed", None, f"the Windows ML package of the EP '{key}' is not installed"
        return _verdict_state(catalog, windows_ml_pack(catalog, key), gpu, device_key, os_build)
    pack = catalog.pack(key)
    if pack is None or catalog.pack_lock(pack["id"]) is None:
        return "unsupported", "os", f"the EP '{key}' has no pack for this platform"
    if gpu is None:
        return "unsupported", "no-device", f"no GPU of this host can run the EP '{key}'"
    floors = catalog.floors_reason(pack, gpu)
    if floors is not None:
        return "unsupported", floors[0], floors[1]
    field_test = field_test_reason(catalog, key)
    if field_test:
        return "field_test", "field-test", field_test
    folder = pack_dir(pack["id"], pack["version"])
    manifest = read_json(folder / "pack.json")
    if manifest is None:
        other = folder.parent.is_dir() and any(child.is_dir() for child in folder.parent.iterdir())
        if other:
            return "stale", "stale", f"the store has an other version of the pack {pack['id']}, not {pack['version']}"
        return "not_installed", None, f"the pack {pack['id']} is not installed"
    files = manifest.get("files", [])
    guard = path_guard(folder, [entry[0] for entry in files])
    if guard is not None:
        return "not_ready", "path-guard", guard
    for name, size, *_ in files:
        try:
            if (folder / name).stat().st_size != size:
                raise OSError
        except OSError:
            return "not_ready", "files", f"the file {name} of the pack {pack['id']} is missing or changed; install the pack again"
    return _verdict_state(catalog, pack, gpu, device_key, os_build)
