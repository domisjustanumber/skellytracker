"""`plan_install()`, `install()`, `download()`, `remove()` and `gc()` of the EP store.

A download starts only after an explicit user action: a call of `install()` or `download()`. No
function here starts one in the background. An EP flow has no licence accept step: each pack of a
plan shows a plain licence link.
"""

import hashlib
import importlib.metadata
import multiprocessing
import os
import shutil
import sys
import threading
import time
import uuid
import zipfile
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath

from skellytracker.core.eps import _download, store
from skellytracker.core.eps.catalog import EpCatalog, load_catalog, platform_tag
from skellytracker.core.eps.recommendation import ep_gpus, install_hint, recommend
from skellytracker.core.eps.records import GcResult, InstallPlan, InstallProgress, InstallResult, PlannedPack, WheelRef
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import probe_host

REF_DAYS, UNUSED_DAYS, PARTIAL_DAYS = 90, 30, 7
DAY = 86400
LICENCE_MARKS = ("LICENSE", "LICENCE", "NOTICE", "THIRD_PARTY", "EULA")


def installed_ort() -> tuple[str, str] | None:
    """The name and the version of the installed ONNX Runtime distribution; `None` when no metadata gives one."""
    try:
        return "onnxruntime-windowsml", importlib.metadata.version("onnxruntime-windowsml")
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        return "onnxruntime", importlib.metadata.version("onnxruntime")
    except importlib.metadata.PackageNotFoundError:
        return None


def core_mismatch(catalog: EpCatalog) -> str | None:
    """The reason when the installed ONNX Runtime is not the ONNX Runtime of the catalog; else `None`.

    The second environment of the certify suite sets `SKELLYTRACKER_EP_ORT_FALLBACK` to the version of
    `certification.ort_fallback` of the catalog. Only that exact `onnxruntime` version then passes too (ADR-XSE7).
    """
    installed = installed_ort()
    if installed is None:
        return None  # a frozen application can have no metadata: the verification child reads the version
    if installed == catalog.ort_distribution:
        return None
    fallback = catalog.data["certification"].get("ort_fallback") or {}
    if installed == (fallback.get("package"), fallback.get("version")) and os.environ.get(store.FALLBACK_VARIABLE) == installed[1]:
        return None
    return (f"{' '.join(installed)} is installed, and the EP catalog needs {' '.join(catalog.ort_distribution)}. "
            "Run `uv sync`.")


def planned_pack(catalog: EpCatalog, pack_id: str, tag: str | None = None, index_url: str | None = None) -> PlannedPack | None:
    """The plan of one pack for a platform tag; `None` when the platform has no such pack."""
    key, pack = catalog.pack_by_id(pack_id)
    lock = catalog.pack_lock(pack_id, tag)
    if lock is None:
        return None
    wheels = tuple(WheelRef(w["package"], w["version"], w["filename"], w["url"] if index_url is None else index_url + w["filename"],
                            w["sha256"], w["download_bytes"], w["unpacked_bytes"]) for w in lock["wheels"])
    licence = (pack.get("licences") or [{}])[0]
    return PlannedPack(key, pack_id, pack["version"], wheels, lock["download_bytes"], lock["unpacked_bytes"],
                       licence.get("name"), licence.get("url"))


def plan_install(selection: str | Sequence[str], index_url: str | None = None, *, field_test: bool = False) -> InstallPlan:
    """The packs to install for a selection, with the download bytes and the disk bytes.

    `selection` is `all-compatible` (each pack EP key that a GPU of this host can run), `recommended`
    (the pack of the performance recommendation), `cpu-only` (no pack) or a list of EP keys. A
    reserved key or an unknown key raises `EpRequestError`. `index_url` replaces the URL of each
    wheel with `<index_url><file name>`, for a local index.

    A `field-test` EP key of the list with no opt-in in the EP store raises `EpUnavailableError`,
    unless `field_test` is true: the caller then records the opt-in with the user action
    (`skellytracker-eps install KEY --field-test`). `all-compatible` holds no such key (ADR-Z5X7).
    """
    catalog, host, warnings = load_catalog(), probe_host(), []
    if selection == "cpu-only":
        keys = []
    elif selection == "all-compatible":
        keys = [key for key in catalog.keys() if catalog.pack(key) and ep_gpus(catalog, key, host)
                and not store.field_test_reason(catalog, key)]
    elif selection == "recommended":
        result = recommend("performance", host)
        keys = [c.ep_key for c in (*result.skipped, result.chosen) if c.pack_id is not None][:1]
    elif isinstance(selection, str):
        raise ValueError(f"the selection {selection!r} is not all-compatible, recommended, cpu-only or a list of EP keys")
    else:
        keys = list(dict.fromkeys(selection))
    packs = []
    for key in keys:
        pack = catalog.pack(key)  # raises EpRequestError for a reserved or unknown key
        refused = None if field_test else store.field_test_reason(catalog, key)
        if refused:
            raise EpUnavailableError(f"The EP '{key}' is not available: {refused}.", install_hint(key))
        planned = None if pack is None else planned_pack(catalog, pack["id"], index_url=index_url)
        if catalog.windows_ml(key):
            warnings.append(f"The EP '{key}' comes from the Windows ML catalog: Windows downloads and installs its package.")
        elif pack is None:
            warnings.append(f"The EP '{key}' is a part of ONNX Runtime. It needs no pack.")
        elif planned is None:
            warnings.append(f"The EP '{key}' has no pack for this platform.")
        else:
            device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
            state, _, reason = store.pack_state(catalog, key, gpu, device_key, host.os_build)
            if state == "unsupported":
                warnings.append(f"The EP '{key}' cannot run on this host: {reason}.")
            packs.append(planned)
    mismatch = core_mismatch(catalog)
    if mismatch:
        warnings.append(mismatch)
    return InstallPlan(tuple(packs), sum(p.download_bytes for p in packs), sum(p.disk_bytes for p in packs), tuple(warnings))


def _unpack(wheel: Path, filename: str, staging: Path, files: list) -> None:
    """Unpack a wheel into `staging`, and copy its licence and notice files to `licenses/`. A member that leaves the folder is refused."""
    with zipfile.ZipFile(wheel) as archive:
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            if info.is_dir():
                continue
            if name.is_absolute() or ".." in name.parts or ":" in info.filename or "\\" in info.filename:
                raise ValueError(f"the wheel {filename} has the unsafe member {info.filename}")
            targets = [staging / name]
            if any(mark in name.name.upper() for mark in LICENCE_MARKS) or "licenses" in name.parts:
                targets.append(staging / "licenses" / filename.split("-")[0] / name.name)
            digest = hashlib.sha256()
            targets[0].parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(targets[0], "wb") as out:
                for chunk in iter(lambda: source.read(1 << 20), b""):
                    digest.update(chunk)
                    out.write(chunk)
            for target in targets[1:]:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(targets[0], target)
            files += [[target.relative_to(staging).as_posix(), info.file_size, digest.hexdigest()] for target in targets]


def _install_pack(catalog: EpCatalog, planned: PlannedPack, progress, cancel, from_dir: Path | None) -> None:
    root, final = store.store_root(), store.pack_dir(planned.pack_id, planned.version)
    if (final / "pack.json").exists():
        return  # a pack folder does not change after its install
    lock = catalog.pack_lock(planned.pack_id) or {}
    done = 0
    wheels = []
    for wheel in planned.wheels:
        def report(have: int, base: int = done) -> None:
            if progress is not None:
                progress(InstallProgress(planned.ep_key, "download", base + have, planned.download_bytes))

        if from_dir is not None:
            path = Path(from_dir) / wheel.filename
            if not path.is_file():
                raise _download.DownloadError("offline", f"the folder has no file {wheel.filename}")
            if _download.sha256_of(path) != wheel.sha256:
                raise _download.DownloadError("hash-mismatch", f"the sha256 of {wheel.filename} is not the sha256 of the lock")
        else:
            path = _download.fetch(wheel.url, wheel.sha256, root / ".partial" / f"{wheel.sha256}.part", cancel=cancel, progress=report)
        done += wheel.download_bytes
        report(0, done)
        wheels.append(path)
    if shutil.disk_usage(root).free < planned.disk_bytes:
        raise OSError(28, "disk-full")
    names = []
    for path in wheels:
        with zipfile.ZipFile(path) as archive:
            names += archive.namelist()
    guard = store.path_guard(final, names)  # before the unpack: a path that is too long must not be written
    if guard is not None:
        raise ValueError(f"path-guard: {guard}")
    staging = root / ".staging" / uuid.uuid4().hex
    try:
        files: list = []
        for position, path in enumerate(wheels):
            if cancel is not None and cancel.is_set():
                raise _download.CancelledError(planned.pack_id)
            if progress is not None:
                progress(InstallProgress(planned.ep_key, "unpack", position, len(wheels)))
            _unpack(path, planned.wheels[position].filename, staging, files)
        _, pack = catalog.pack_by_id(planned.pack_id)
        store.write_json(staging / "pack.json", {
            "format": 1, "source": "wheel", "pack_id": planned.pack_id, "ep_key": planned.ep_key, "ep_name": pack["ep_name"],
            "package": pack["package"], "version": planned.version, "platform_tag": platform_tag(),
            "catalog_revision": catalog.revision, "library": lock.get("library"), "path_dirs": lock.get("path_dirs", []),
            "preload": lock.get("preload", []), "preload_ort_core": bool(pack.get("preload_ort_core")), "wheels": [[w.filename, w.sha256] for w in planned.wheels], "files": files,
            "installed_at": int(time.time()),
        })
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, final)  # the one move: a reader sees no pack or the whole pack
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    if from_dir is None:
        for path in wheels:
            path.unlink(missing_ok=True)


def _verify(key: str, progress) -> str | None:
    """The reason when the verification of a new pack fails; `None` for a pass or for a test pack."""
    from skellytracker.core.eps import verification
    from skellytracker.core.errors import EpRequestError, EpUnavailableError

    if progress is not None:
        progress(InstallProgress(key, "verify"))
    try:
        (verdict,) = verification.verify([key])
    except EpRequestError:
        return None  # a test pack of a reserved key: selftest() checks it
    except EpUnavailableError as error:
        return str(error)
    return None if verdict.ok else verdict.reason


def install(plan: InstallPlan, *, progress: Callable[[InstallProgress], None] | None = None,
            cancel: threading.Event | None = None, from_dir: Path | None = None, verify: bool = True) -> InstallResult:
    """Install each pack of a plan into the EP store. It does not raise for a pack that fails.

    After the install of a pack, `verify` runs the verification levels L2 and L3 in a child process.
    A pack that fails the verification stays in the store, with the error code `verify-failed`.

    `from_dir` installs from a folder that holds the wheels of the lock, with no network. The sha256
    of each wheel must be the sha256 of the lock. `InstallResult.failed` holds `(key, error code,
    message)`, with the error code `offline`, `http-error`, `hash-mismatch`, `disk-full`,
    `path-guard`, `core-mismatch`, `verify-failed` or `failed`.
    """
    catalog = load_catalog()
    ok, failed, cancelled = [], [], []
    mismatch = core_mismatch(catalog)
    for planned in plan.packs:
        key = planned.ep_key
        if mismatch:
            failed.append((key, "core-mismatch", mismatch))
        elif cancelled or (cancel is not None and cancel.is_set()):
            cancelled.append(key)
        else:
            try:
                with store.store_lock():
                    _install_pack(catalog, planned, progress, cancel, from_dir)
                reason = _verify(key, progress) if verify else None
                if reason is None:
                    ok.append(key)
                else:
                    failed.append((key, "verify-failed", reason))
            except _download.CancelledError:
                cancelled.append(key)
            except _download.DownloadError as error:
                failed.append((key, error.code, str(error)))
            except (OSError, ValueError, zipfile.BadZipFile) as error:
                text = str(error)
                code = "disk-full" if "disk-full" in text or getattr(error, "errno", None) == 28 else "path-guard" if text.startswith("path-guard") else "failed"
                failed.append((key, code, text))
    return InstallResult(tuple(ok), tuple(failed), tuple(cancelled))


def download(keys: Sequence[str], platform: str, dest: Path) -> Path:
    """Download the wheels of the lock for a platform tag to `dest`, for `install(..., from_dir=dest)`. It installs nothing."""
    catalog = load_catalog()
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"platform": platform, "wheels": [], "licences": []}
    for key in keys:
        pack = catalog.pack(key)
        planned = None if pack is None else planned_pack(catalog, pack["id"], platform)
        if planned is None:
            raise ValueError(f"the EP '{key}' has no pack for the platform {platform}")
        for wheel in planned.wheels:
            target = dest / wheel.filename
            if not (target.is_file() and _download.sha256_of(target) == wheel.sha256):
                os.replace(_download.fetch(wheel.url, wheel.sha256, dest / f"{wheel.sha256}.part"), target)
            manifest["wheels"].append({"filename": wheel.filename, "sha256": wheel.sha256})
        manifest["licences"] += pack.get("licences", [])
    store.write_json(dest / "manifest.json", manifest)
    (dest / "README.txt").write_text(
        "EP pack wheels for skellytracker.\nInstall them with: skellytracker-eps install <key> --from-dir <this folder>\n"
        "manifest.json gives the sha256 of each file and the licence links.\n", encoding="utf-8")
    return dest


def _trash(path: Path, deferred: list[str]) -> None:
    """Move a folder to `.trash/` and delete it. A file that a process holds stays in `.trash/` for the next `gc()`."""
    trash = store.store_root() / ".trash"
    trash.mkdir(parents=True, exist_ok=True)
    try:
        target = trash / uuid.uuid4().hex
        os.replace(path, target)
        shutil.rmtree(target)
    except OSError:
        deferred.append(path.name)


def remove(pack_id: str | None = None, *, consumer: str | None = None) -> None:
    """Remove one pack, or each pack (`all`), from the store. `consumer` removes the ref files of that consumer kind."""
    root = store.store_root()
    with store.store_lock():
        if consumer is not None:
            for ref in (root / "refs").glob("*.json"):
                if (store.read_json(ref) or {}).get("kind") == consumer:
                    ref.unlink()
        folders = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "refs"]
        for folder in folders if pack_id == "all" else [root / pack_id] if pack_id else []:
            if folder.is_dir() and folder.parent == root:
                _trash(folder, [])


def consumer_ref(catalog: EpCatalog) -> tuple[str, dict]:
    """The id and the ref record of this consumer: one environment or one frozen application."""
    frozen = bool(getattr(sys, "frozen", False))
    prefix = os.path.dirname(sys.executable) if frozen else sys.prefix
    packs = [[pack["id"], pack["version"]] for key in catalog.keys() for pack in catalog.ep(key).get("packs", ())]
    return hashlib.sha256(prefix.encode("utf-8")).hexdigest()[:16], {
        "kind": "frozen" if frozen else "environment", "prefix": prefix, "catalog_revision": catalog.revision,
        "ort_version": catalog.ort_version, "packs": packs, "last_seen": int(time.time())}


def gc(*, force: bool = False, cache: bool = False, now: float | None = None) -> GcResult:
    """Delete the packs that no consumer needs. Call it only in the main process.

    It writes the ref file of this consumer, and deletes each ref file that is older than 90 days
    or whose environment no longer exists. It deletes each pack that no ref names and that no
    process registered for 30 days (`force` ignores the 30 days), each partial download that is
    older than 7 days, and the content of `.trash/`. `cache` also deletes the EP cache folders of an
    other driver version.
    """
    if multiprocessing.parent_process() is not None:
        raise RuntimeError("gc() runs only in the main process")
    catalog, root, now = load_catalog(), store.store_root(), time.time() if now is None else now
    removed_packs, removed_refs, deferred, partials = [], [], [], 0
    with store.store_lock():
        consumer_id, ref = consumer_ref(catalog)
        store.write_json(root / "refs" / f"{consumer_id}.json", ref)
        named = set()
        for path in (root / "refs").glob("*.json"):
            record = store.read_json(path) or {}
            if now - record.get("last_seen", 0) > REF_DAYS * DAY or not os.path.isdir(record.get("prefix", "")):
                path.unlink()
                removed_refs.append(path.stem)
            else:
                named |= {tuple(pack) for pack in record.get("packs", ())}
        last_used = store.read_verdicts().get("last_used", {})
        for folder in [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "refs"]:
            for version in [v for v in folder.iterdir() if v.is_dir()]:
                name = f"{folder.name}/{version.name}"
                used = last_used.get(name, version.stat().st_mtime)
                if (folder.name, version.name) not in named and (force or now - used > UNUSED_DAYS * DAY):
                    _trash(version, deferred)
                    removed_packs.append(name)
        for leftover in (root / ".trash").glob("*"):
            shutil.rmtree(leftover, ignore_errors=True)
        for part in (root / ".partial").glob("*"):
            if now - part.stat().st_mtime > PARTIAL_DAYS * DAY:
                part.unlink()
                partials += 1
        if cache:
            drivers = {gpu.driver_version for gpu in probe_host().gpus}
            for folder in store.cache_root().glob("*/*/*"):
                if folder.is_dir() and folder.name not in drivers:
                    shutil.rmtree(folder, ignore_errors=True)
    return GcResult(tuple(removed_packs), tuple(removed_refs), partials, tuple(deferred))
