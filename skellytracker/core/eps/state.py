"""`status()`, `check_start()` and `suggest_execution_provider()`: the EP state of this host, with no `onnxruntime` import and no network.

The entries of the `detectors` list and of the `pipelines` list carry no EP state. `status()` and
`recommend()` give it. A pack can change after a list call, so a run checks the EP at its start.
"""

import os
import shutil
import sys
from collections.abc import Mapping, Sequence

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import certification, evidence, store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.installer import core_mismatch, installed_ort
from skellytracker.core.eps.recommendation import ep_gpus, install_hint, recommend, run_devices
from skellytracker.core.eps.records import USABLE_STATES, DeviceCheck, EpStatus, PackStatus, RunDevice
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import probe_host


def check_start(execution_provider: str, ep_options: Mapping[str, str] | None = None,
                device: str | Sequence[str] | None = None) -> tuple[RunDevice, ...]:
    """The start check of a run: the EP is a key of the EP catalog that is ready, and the catalog allows each option.

    It raises `EpRequestError` for a reserved or unknown key and for a refused option, and
    `EpUnavailableError` with the install command for an EP that is not ready or a `device` that the
    EP cannot use. It returns the GPUs of the run: `run_devices(execution_provider, device)`.
    A pack with no trial session yet, or with an ONNX Runtime that is not tested, is ready. A
    `field-test` EP with no opt-in raises `EpUnavailableError` with the opt-in command (ADR-Z5X7).
    """
    catalog = load_catalog()
    catalog.check_options(execution_provider, ep_options)
    devices = run_devices(execution_provider, device)
    if catalog.device_row(execution_provider) is None:
        state, _, reason = store.pack_state(catalog, execution_provider)
        if state not in USABLE_STATES:
            raise EpUnavailableError(f"The EP '{execution_provider}' is not available: {reason}.")
        return devices
    host = probe_host()
    gpus = dict(ep_gpus(catalog, execution_provider, host))
    states = [store.pack_state(catalog, execution_provider, gpus[d.device_key], d.device_key, host.os_build) for d in devices]
    if not devices:
        states = [store.pack_state(catalog, execution_provider)]
    for state, _, reason in states:
        if state not in USABLE_STATES:
            raise EpUnavailableError(f"The EP '{execution_provider}' is not available: {reason}.", install_hint(execution_provider))
    return devices


REPAIRABLE_STATES = ("not_installed", "stale", "not_ready")  # the states that `skellytracker-eps install` repairs
SOURCES = {"pypi": "pypi", "ort-cuda-13": "azure", "amd-ort": "amd"}  # the index of a pack -> `PackStatus.source`


def _device_checks(catalog, key: str, host) -> tuple[DeviceCheck, ...]:
    found = []
    for device_key, gpu in ep_gpus(catalog, key, host):
        ready = store.pack_state(catalog, key, gpu, device_key, host.os_build)[0] in USABLE_STATES
        certified = evidence.certified(key, gpu, host.os_name)
        local = certification.local_result(catalog, key, gpu, host.os_name)
        found.append(DeviceCheck(device_key, gpu.name, certified, local, ready and local != "failed" and (certified or local == "passed")))
    return tuple(found)


def _pack_status(catalog, key: str, host) -> PackStatus | None:
    row, pack = catalog.ep(key), catalog.pack(key)
    tag = catalog_module.platform_tag()
    if pack is None:
        windows_ml = catalog.windows_ml(key)
        if ("platforms" in row and tag not in row["platforms"]) or (row["kind"] == "plugin" and not windows_ml):
            return None  # for example `coreml` off macOS, or `amdgpu` off Windows
        device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))  # `directml` or a Windows ML EP
        state, code, reason = store.pack_state(catalog, key, gpu, device_key, host.os_build)
        if windows_ml and gpu is None and host.gpus:  # the floor that the GPUs of the host do not pass
            code, reason = min((catalog.floors_reason(row, g) for g in host.gpus), key=lambda floor: floor[0] == "no-device")
        usable = state in USABLE_STATES
        return PackStatus(key, row["display_name"], state, "windows-ml" if windows_ml else "builtin", row.get("status", "ready"),
                          code, reason, usable=usable,
                          install_hint=install_hint(key) if windows_ml and state in REPAIRABLE_STATES else None,
                          uses_gpu=row["gpu"], description=row["description"], devices=run_devices(key) if usable else (),
                          certified=None if gpu is None or not windows_ml else evidence.certified(key, gpu, host.os_name),
                          checks=_device_checks(catalog, key, host))
    lock = catalog.pack_lock(pack["id"])
    if lock is None:
        return None  # a platform with no pack, for example macOS
    device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
    state, code, reason = store.pack_state(catalog, key, gpu, device_key, host.os_build)
    if gpu is None and host.gpus:  # give the floor that the best GPU of the vendor does not pass
        floors = [catalog.floors_reason(pack, g) for g in host.gpus]
        code, reason = min(floors, key=lambda floor: floor[0] == "no-device")
    usable = state in USABLE_STATES
    component = catalog.component(key)
    component_lock = {} if component is None else catalog.pack_lock(component["id"]) or {}
    decoder = store.component_state(catalog, key)  # it never blocks the EP (ADR-88ZB)
    component_download = 0 if decoder == "installed" else component_lock.get("download_bytes", 0)
    return PackStatus(
        key, row["display_name"], state, SOURCES[pack["index"]], pack.get("status", "ready"), code, reason,
        lock["download_bytes"] + component_download, lock["unpacked_bytes"] + component_lock.get("unpacked_bytes", 0),
        pack["id"], pack["version"], pack["exclusive_group"],
        tuple((licence["name"], licence["url"]) for licence in [*pack.get("licences", ()), *(component or {}).get("licences", ())]),
        usable=usable, install_hint=install_hint(key) if state in REPAIRABLE_STATES else None, uses_gpu=row["gpu"],
        description=row["description"], devices=run_devices(key) if usable else (),  # `run_devices` reads only the cached host probe
        certified=None if gpu is None else evidence.certified(key, gpu, host.os_name), jpeg_decoder=decoder,
        jpeg_decoder_hint=install_hint(key) if decoder in ("missing", "other_version") and state != "unsupported" else None,
        checks=_device_checks(catalog, key, host))


def status() -> EpStatus:
    """The state of each EP key of this platform, the recommendations and the store. It loads no library.

    `eps` of the result is in the order of the EP catalog: `trt-rtx`, `cuda`, `coreml`, `amdgpu`,
    `migraphx`, `directml`, `cpu` (`EpStatus`). An application shows the EPs from this result and
    holds no EP fact of its own.
    """
    catalog, host = load_catalog(), probe_host()
    installed = installed_ort()
    root = store.store_root()
    existing = next((path for path in (root, *root.parents) if path.exists()), None)
    warnings = [text for text in (core_mismatch(catalog),) if text]
    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env and os.path.normcase(os.path.abspath(virtual_env)) != os.path.normcase(os.path.abspath(sys.prefix)):
        warnings.append("VIRTUAL_ENV is not the environment of this Python. The EP store serves the environment of this Python.")
    rows = [_pack_status(catalog, key, host) for key in catalog.keys()]
    return EpStatus(
        ort_version=None if installed is None else installed[1], catalog_revision=catalog.revision,
        core_matches_pin=installed == catalog.ort_distribution,
        platform_tag=catalog_module.platform_tag(), store_root=str(root),
        store_free_bytes=None if existing is None else shutil.disk_usage(existing).free, host=host,
        performance=recommend("performance", host), accuracy=recommend("accuracy", host),
        eps=tuple(row for row in rows if row is not None), warnings=tuple(warnings),
        certify_offers=certification.certify_offers(catalog, host),
    )


def suggest_execution_provider(saved_execution_provider: str) -> str | None:
    """The EP key to use on this host for an EP key that a setting of an older release holds, or None.

    An application calls it only for a setting that an older release saved. A choice of this release
    stays as chosen. None means: use the recommendation, `status().performance`.

    This host supports an EP key when `status().eps` has a row for the key and the `state` of that
    row is not `unsupported`. Thus a built-in EP on its platform is supported. A plugin EP is
    supported when a GPU of this host passes the floors of its pack: the vendor, the compute
    capability and the driver branch. The pack does not need to be installed. A driver that is too
    old fails a floor: `status().performance` then holds the `update-driver` offer.

    1. A key of `legacy_keys` of the EP catalog gives its first successor that this host supports,
       else None. `trt` and `cuda` have the successors `trt-rtx`, then `cuda`. `directml` has no
       successor.
    2. Each other EP key of the catalog on this platform gives that key when this host supports it,
       else None.
    3. Each other string gives None: a reserved key with no row in `legacy_keys`, an unknown key and
       the empty string. The function raises for no string. The match is exact and case-sensitive.

    The returned EP can be not usable yet, for example when its pack is not installed. The
    application reads `PackStatus.usable` and `PackStatus.install_hint` of the returned key in
    `status().eps`. Until the install, `check_start()` of the key raises `EpUnavailableError` with
    the install hint.

    It uses the state of `status()`: it loads no library and uses no network. A request does not
    change: `check_start("cuda")` starts `cuda`, and `check_start("trt")` raises `EpRequestError`.
    """
    catalog, host = load_catalog(), probe_host()
    for key in catalog.data["legacy_keys"].get(saved_execution_provider, (saved_execution_provider,)):
        row = _pack_status(catalog, key, host) if key in catalog.keys() else None
        if row is not None and row.state != "unsupported":
            return key
    return None
