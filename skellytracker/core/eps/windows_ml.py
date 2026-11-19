"""The EPs of the Windows ML catalog on Windows: find, install, register and remove (ADR-XSE7).

Only this module imports `windowsml`, and only in a function. An EP key whose `windows_ml` row names
this platform (`EpCatalog.windows_ml()`) has no pack here. Windows installs its package, and the EP
store keeps one record for each such key in `windows-ml.json`.

- `find_eps()` lists the EPs that the catalog offers for this PC, with their ready state. It
  downloads nothing.
- `install(key, progress=..., cancel=...)` makes the package of the EP ready (`ensure_ready_async`).
  For a package that is not on the PC, Windows downloads and installs it. Call it only after the
  opt-in and the consent of the user. The API gives a fraction from 0 to 1, with no bytes. The record holds `was_present` (the catalog state before the call, or a package of the
  family in the list before the call), the package family that the catalog reports, and
  `packages_installed`: the full name of each package of that family that the call added for the
  current user (`Get-AppxPackage` before and after the call). With `was_present`, the list is empty,
  also when the call updated the package to a new full name.
  The `pending` record of a call that did not end holds `packages_before`: each full name before.
- `register(key)` registers the library of a package that is on the PC with ONNX Runtime. It never
  downloads: a package that is not on the PC raises `EpUnavailableError`.
- `remove_installed(record)` removes each package of `packages_installed` of a record for the current
  user (`Remove-AppxPackage <PackageFullName>`, no administrator rights), and never an other package.
  For a `pending` record it removes each package of the family that the catalog gives now and that
  is not in `packages_before`. The certify suite calls it at the end of a run.
- `remove(key)` calls `remove_installed()` with the record of the key in this EP store, and deletes
  the record when no row fails. `eps.remove(execution_provider=key)` and
  `skellytracker-eps remove --windows-ml KEY` call it.

The catalog gives the package family and the version only after `ensure_ready`, and only on a new
enumeration: the provider object of the call keeps the empty values.
"""

import os
import re
import subprocess
import threading
import time
from collections.abc import Callable

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import _download, store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.records import InstallProgress, RegisteredEp, RemoveResult
from skellytracker.core.errors import EpUnavailableError

NOT_PRESENT = "NotPresent"
PACKAGE_VARIABLE = "SKELLYTRACKER_REMOVE_PACKAGE"  # the full name goes to PowerShell in this variable, never in the script text
# Name_Version_Architecture_ResourceId_PublisherId; a package name has no `_`
FULL_NAME = re.compile(r"(?P<name>[A-Za-z0-9.\-]+)_[0-9.]+_[A-Za-z0-9]*_[A-Za-z0-9.\-~]*_(?P<publisher>[a-z0-9]{13})")
_lock = threading.Lock()
_catalog = None  # the open `windowsml.EpCatalog`: an EP handle must not outlive it, so it stays open in the process
_registered: dict[str, RegisteredEp] = {}


def _open():
    global _catalog
    if _catalog is None:
        import windowsml

        _catalog = windowsml.EpCatalog()
    return _catalog


def _provider(ep_name: str):
    return next((provider for provider in _open().find_all_providers() if provider.name == ep_name), None)


def _powershell(script: str, **variables: str) -> subprocess.CompletedProcess:
    """Run Windows PowerShell for the current user. A value goes in an environment variable, never in the script text."""
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],  # noqa: S603, S607
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, check=False,
                          env={**os.environ, **variables})


def installed_packages() -> dict[str, str]:
    """The package family of each package of the current user, by its full name (`Get-AppxPackage`). It raises `OSError`."""
    done = _powershell("Get-AppxPackage | ForEach-Object { $_.PackageFullName + '|' + $_.PackageFamilyName }")
    if done.returncode:
        raise OSError(f"Get-AppxPackage exited with {done.returncode}")
    return dict(line.strip().split("|", 1) for line in done.stdout.splitlines() if "|" in line)


def _remove_appx(full_name: str) -> bool:
    """True when `Remove-AppxPackage` of one full name exited with 0. It needs no administrator rights for the current user."""
    return _powershell(f"Remove-AppxPackage -Package $env:{PACKAGE_VARIABLE}", **{PACKAGE_VARIABLE: full_name}).returncode == 0


def family_of(full_name: str) -> str | None:
    """The package family of a package full name: `Name_PublisherId`; None when the text is not a full name."""
    match = FULL_NAME.fullmatch(full_name)
    return None if match is None else f"{match['name']}_{match['publisher']}"


def remove_package(full_name: str, family: str) -> str | None:
    """Remove one package of the current user by its full name. It gives None, or a reason code when it removed nothing.

    It refuses a full name that is not of `family` (the family that the catalog reported for the EP),
    also when Windows lists the package under an other family. A package that is not on the PC is
    not an error. It tries one time.
    """
    if not family or family_of(full_name) != family:
        return "package-name-mismatch"
    packages = installed_packages()
    if full_name not in packages:
        return None
    if packages[full_name] != family:
        return "package-name-mismatch"
    if not _remove_appx(full_name) or full_name in installed_packages():
        return "package-not-removed"
    return None


def _catalog_family(ep_name: str) -> str | None:
    """The package family that a new enumeration of the catalog gives for the EP now; None when it gives none."""
    try:
        with _lock:
            provider = _provider(ep_name)
        return (provider.package_family_name or None) if provider is not None else None
    except Exception:  # noqa: BLE001 - no catalog, or a Windows build with no Windows ML: the family is not known
        return None


def remove_installed(record: dict) -> list[dict]:
    """Remove each package that `install()` added, and never an other package.

    One row for each package: `{"package", "result", "reason_code"}`, with `result` `pass` or `fail`.
    A record whose `ep_name` is not a Windows ML EP of the EP catalog gives one `fail` row with
    `record-refused`. A record with `was_present` gives no row: a package of a family that was on
    the PC before is never removed. The family is the one that the catalog gives now, else the one
    of the record; each full name must be of that family (`remove_package`). A `pending` record (an
    install that did not end) removes each package of that family that is not in `packages_before`.
    With no family from the catalog or no `packages_before`, it gives one `fail` row with
    `package-unknown`, and so does a record that is not pending and has no package in the list.
    """
    unknown = [{"package": None, "result": "fail", "reason_code": "package-unknown"}]
    if record.get("ep_name") not in {row.get("ep_name") for row in load_catalog().data["eps"].values() if row.get("windows_ml")}:
        return [{"package": None, "result": "fail", "reason_code": "record-refused"}]
    if record.get("was_present"):
        return []
    family = _catalog_family(record["ep_name"])
    if record.get("pending"):
        before = record.get("packages_before")
        if family is None or not isinstance(before, list):
            return unknown
        if any(family_of(name) == family for name in before):
            return []
        try:
            names = sorted(name for name, of in installed_packages().items() if of == family and name not in before)
        except (OSError, subprocess.SubprocessError):
            return unknown
    else:
        names, family = record.get("packages_installed") or [], family or record.get("package_family_name") or ""
        if not names:
            return unknown
    rows = []
    for full_name in names:
        try:
            code = remove_package(full_name, family)
        except (OSError, subprocess.SubprocessError):
            code = "package-not-removed"
        rows.append({"package": full_name, "result": "fail" if code else "pass", "reason_code": code})
    return rows


def remove(key: str) -> RemoveResult:
    """Remove the Windows ML package of the EP `key` that `install()` of this EP store added, and never an other package.

    It calls `remove_installed()` with the record of the key in `windows-ml.json`. With no record, `failed`
    holds `(None, "no-record")`. When no row fails, it deletes the record, and the EP is then `not_installed`.
    With `was_present`, it removes no package: the package was on the PC before the install, and it stays.
    An unknown or reserved key raises `EpRequestError`.
    """
    load_catalog().ep(key)
    record = store.windows_ml_installs().get(key)
    if record is None:
        return RemoveResult(failed=((None, "no-record"),))
    rows = remove_installed(record)
    failed = tuple((row["package"], row["reason_code"]) for row in rows if row["result"] == "fail")
    if not failed:
        with store.store_lock():
            store.write_json(store.store_root() / "windows-ml.json", {k: v for k, v in store.windows_ml_installs().items() if k != key})
    return RemoveResult(tuple(row["package"] for row in rows if row["result"] == "pass"), failed, bool(record.get("was_present")))


def find_eps() -> dict[str, str]:
    """The ready state (`Ready`, `NotReady` or `NotPresent`) of each EP name that the catalog offers for this PC."""
    with _lock:
        return {provider.name: provider.ready_state.name for provider in _open().find_all_providers()}


def _write_record(key: str, record: dict) -> None:
    with store.store_lock():
        store.write_json(store.store_root() / "windows-ml.json", {**store.windows_ml_installs(), key: record})


def _ensure_ready(provider, key: str, progress, cancel) -> bool:
    """Run `ensure_ready_async` of the provider and wait for its end. False when it ended with an error after a cancel request.

    The callbacks of `windowsml` run on a native thread. This function only keeps their values, and calls
    `progress` on the thread of the caller. It raises `OSError` when the operation fails.
    """
    done, latest = threading.Event(), [None]
    operation = provider.ensure_ready_async(on_complete=done.set, on_progress=lambda value: latest.__setitem__(0, value))
    shown, asked = None, False
    try:
        while not done.wait(0.2):
            if progress is not None and latest[0] != shown:
                shown = latest[0]
                progress(InstallProgress(key, "download", fraction=shown))
            if cancel is not None and cancel.is_set():
                operation.cancel()
                asked = True
                break
        try:
            operation.wait()
        except OSError:
            if asked:
                return False
            raise
        if progress is not None and latest[0] != shown:
            progress(InstallProgress(key, "download", fraction=latest[0]))
        return True
    finally:
        operation.close()


def install(key: str, *, progress: Callable[[InstallProgress], None] | None = None,
            cancel: threading.Event | None = None) -> dict:
    """Make the package of the EP `key` ready. It can make Windows download and install the package.

    Before the call it writes a `pending` record, so that a crash leaves a trace. After the call it
    records the EP name, the package version, the package family, `was_present`, `packages_installed`
    and the time in the EP store, and returns the record. It raises `EpUnavailableError` when the
    catalog does not offer the EP for this PC, `Get-AppxPackage` fails, or the install fails.

    `progress` gets `InstallProgress` with the phase `download`, no bytes, and `fraction`, the value
    from 0 to 1 that Windows ML gives, or None before the first value. Windows ML can give no value.
    `cancel` set before the start of the install raises `CancelledError` of `_download`, and changes
    nothing. `cancel` set during the install asks Windows ML to stop it (`AsyncOperation.cancel`).
    When the install then ends with an error, the `pending` record stays and it raises `CancelledError`:
    `remove(key)` removes each package that the install added. When the install ends without an error,
    the cancel came too late: it records the install and returns the record.
    """
    ep_name = load_catalog().ep(key)["ep_name"]
    with _lock:
        provider = _provider(ep_name)
        if provider is None:
            raise EpUnavailableError(f"The Windows ML catalog offers no EP {ep_name} for this PC.")
        was_present = provider.ready_state.name != NOT_PRESENT
        try:
            before = installed_packages()  # all packages: the catalog gives the family only after `ensure_ready`
        except (OSError, subprocess.SubprocessError) as error:
            raise EpUnavailableError(f"The packages of this PC are not known, so the suite cannot remove the package later: "
                                     f"{sanitize_text(str(error))[:200]}") from error
        if cancel is not None and cancel.is_set():
            raise _download.CancelledError(key)
        _write_record(key, {"ep_name": ep_name, "was_present": was_present, "pending": True, "packages_before": sorted(before),
                            "installed_at": int(time.time())})
        if progress is not None:
            progress(InstallProgress(key, "download"))
        try:
            if not _ensure_ready(provider, key, progress, cancel):
                raise _download.CancelledError(key)
        except OSError as error:
            raise EpUnavailableError(f"The Windows ML package of the EP '{key}' did not install: "
                                     f"{sanitize_text(str(error))[:500]}") from error
        ready = _provider(ep_name) or provider  # a new enumeration gives the version and the family
        family = ready.package_family_name
        # never a package of a family that was on the PC before, also when `ensure_ready` updated it to a new full name
        present = was_present or family in before.values()
        added = [] if present else sorted(name for name, of in installed_packages().items() if family and of == family and name not in before)
        record = {"ep_name": ep_name, "version": ready.version, "package_family_name": family, "was_present": present,
                  "packages_installed": added, "installed_at": int(time.time())}
    _write_record(key, record)
    return record


def register(key: str, hint: str | None = None) -> RegisteredEp:
    """Register the library of the Windows ML package of the EP `key` with ONNX Runtime, one time for each process."""
    with _lock:
        if key in _registered:
            return _registered[key]
        ep_name = load_catalog().ep(key)["ep_name"]
        provider = _provider(ep_name)
        if provider is None or provider.ready_state.name == NOT_PRESENT:
            raise EpUnavailableError(f"The Windows ML package of the EP '{key}' is not on this PC.", hint)
        import onnxruntime

        from skellytracker.core.eps.registration import NO_DEVICE

        try:
            provider.ensure_ready()  # the package is on the PC: this adds it to the process and downloads nothing
            onnxruntime.register_execution_provider_library(ep_name, provider.library_path)
        except Exception as error:  # noqa: BLE001 - ONNX Runtime and windowsml raise their own error types
            if "already registered" not in str(error).lower():
                raise EpUnavailableError(f"The Windows ML EP '{key}' does not register: {sanitize_text(str(error))[:500]}") from error
        if ep_name not in {device.ep_name for device in onnxruntime.get_ep_devices()}:
            raise EpUnavailableError(f"The Windows ML EP '{key}' registers, but the EP '{ep_name}' {NO_DEVICE}.")
        _registered[key] = RegisteredEp(key, ep_name)
        return _registered[key]
