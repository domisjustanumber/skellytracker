"""`ensure_registered()`: register the library of an EP pack with ONNX Runtime, one time for each process.

A registration does not carry over to a `spawn` child. Each process that builds a session
registers the pack. `build_session()` does that. The plugin module of a pack is never imported:
the library is registered by its path.
"""

import ctypes
import os
import sys
import threading
import time
from pathlib import Path

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.installer import core_mismatch
from skellytracker.core.eps.recommendation import install_hint
from skellytracker.core.eps.records import RegisteredEp
from skellytracker.core.errors import EpUnavailableError

_lock = threading.Lock()
_registered: dict[str, RegisteredEp] = {}  # pack id: the result
_groups: dict[str, str] = {}  # exclusive group: pack id


def prepare_libraries(folder: Path, manifest: dict, platform: str = sys.platform) -> None:
    """Make the dependency libraries of a pack loadable in this process.

    Windows: prepend each DLL folder to `PATH`. `os.add_dll_directory` does not work for these
    packs, because ONNX Runtime loads the library with an altered search path. Linux: load each
    library of the preload list with `RTLD_GLOBAL`, in order. The Linux step is not verified.
    """
    if platform == "win32":
        current = os.environ.get("PATH", "").split(os.pathsep)
        folders = [str(folder / name) for name in manifest.get("path_dirs", ())]
        os.environ["PATH"] = os.pathsep.join([*(f for f in folders if f not in current), *current])
    elif platform == "linux":
        for name in manifest.get("preload", ()):
            ctypes.CDLL(str(folder / name), mode=ctypes.RTLD_GLOBAL)


def describe_device(device) -> str:
    """One ONNX Runtime EP device as text: the EP name, the device type and the PCI vendor id and device id."""
    hardware = device.device
    kind = str(getattr(hardware, "type", "device")).rsplit(".", 1)[-1].lower()
    return f"{device.ep_name} on {kind} {hardware.vendor_id:04x}:{hardware.device_id:04x}"


def register_pack(ep_key: str, pack: dict, hint: str | None = None) -> RegisteredEp:
    """Register one pack row of the catalog. `ensure_registered()` and `selftest()` call it."""
    with _lock:
        pack_id = pack["id"]
        if pack_id in _registered:
            return _registered[pack_id]
        catalog = load_catalog()
        mismatch = core_mismatch(catalog)
        if mismatch:
            raise EpUnavailableError(f"The EP '{ep_key}' is not available: {mismatch}")
        folder = store.pack_dir(pack_id, pack["version"])
        manifest = store.read_json(folder / "pack.json")
        if manifest is None:
            raise EpUnavailableError(f"The EP pack '{pack_id}' {pack['version']} is not installed.", hint)
        guard = store.path_guard(folder, [entry[0] for entry in manifest.get("files", ())])
        if guard is not None:
            raise EpUnavailableError(f"The EP pack '{pack_id}' cannot load: {guard}")
        group = pack["exclusive_group"]
        if _groups.get(group, pack_id) != pack_id:
            raise EpUnavailableError(f"The EP pack '{pack_id}' cannot register: this process registered the pack "
                                     f"'{_groups[group]}' of the same EP.")
        prepare_libraries(folder, manifest)
        import onnxruntime

        ep_name = pack["ep_name"]
        try:
            onnxruntime.register_execution_provider_library(ep_name, str(folder / manifest["library"]))
        except Exception as error:  # noqa: BLE001 - ONNX Runtime raises its own error types
            if "already registered" not in str(error).lower():
                raise EpUnavailableError(f"The EP pack '{pack_id}' does not register: {sanitize_text(str(error))[:500]}") from error
        devices = list(onnxruntime.get_ep_devices())
        if ep_name not in {device.ep_name for device in devices}:
            # An EP gives no reason for an empty list. The devices of the other EPs show the hardware that it refused.
            listed = "; ".join(sorted({describe_device(device) for device in devices})) or "none"
            raise EpUnavailableError(f"The EP pack '{pack_id}' registers, but the EP '{ep_name}' lists no device on this host. "
                                     f"ONNX Runtime lists these devices: {listed}.")
        _groups[group] = pack_id
        _registered[pack_id] = RegisteredEp(ep_key, ep_name, pack_id, pack["version"], Path(manifest["library"]).name)
        try:  # the input of gc(): the last use of the pack, one time for each process
            verdicts = store.read_verdicts()
            verdicts.setdefault("last_used", {})[f"{pack_id}/{pack['version']}"] = int(time.time())
            store.write_json(store.store_root() / "verdicts.json", verdicts)
        except OSError:
            pass
        return _registered[pack_id]


def ensure_registered(ep_key: str) -> RegisteredEp:
    """Make the EP of an EP key usable in this process. A second call does nothing.

    A built-in EP needs no registration. For a plugin EP, the pack must be installed, register, and
    list a device. Else it raises `EpUnavailableError` with the install command.
    """
    catalog = load_catalog()
    row = catalog.ep(ep_key)
    pack = catalog.pack(ep_key)
    if pack is not None:
        return register_pack(ep_key, pack, install_hint(ep_key))
    import onnxruntime

    if row["ep_name"] not in onnxruntime.get_available_providers():
        raise EpUnavailableError(f"The EP '{ep_key}' is not a part of ONNX Runtime on this platform.")
    return RegisteredEp(ep_key, row["ep_name"])


def ort_device(ep_name: str, gpu, rank: int = 0):
    """The ONNX Runtime EP device of an EP for a GPU (`GpuInfo`); `None` when the EP does not list that GPU.

    The match is the PCI vendor id and device id, then the LUID on Windows.
    shortcut: with no LUID (Linux), the device number `rank` of the devices with these PCI ids is
    used. Check the order on a host with two GPUs of one model before such a host is supported.
    """
    import onnxruntime

    matches = [device for device in onnxruntime.get_ep_devices() if device.ep_name == ep_name
               and device.device.vendor_id == gpu.pci_vendor_id and device.device.device_id == gpu.pci_device_id]
    if gpu.luid is not None:
        by_luid = [device for device in matches if dict(device.device.metadata).get("LUID") == str(gpu.luid)]
        if by_luid:
            return by_luid[0]
    return matches[rank] if rank < len(matches) else None
