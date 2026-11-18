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
from types import ModuleType

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.installer import core_mismatch
from skellytracker.core.eps.recommendation import install_hint
from skellytracker.core.eps.records import RegisteredEp
from skellytracker.core.errors import EpUnavailableError

NO_DEVICE = "lists no device on this host"  # `selftest()` reads this text in the reason of a child process
_lock = threading.Lock()
_registered: dict[str, RegisteredEp] = {}  # pack id: the result
_groups: dict[str, str] = {}  # exclusive group: pack id


def prepare_libraries(folder: Path, manifest: dict, platform: str = sys.platform) -> None:
    """Make the dependency libraries of a pack loadable in this process.

    Windows: prepend each DLL folder to `PATH`. `os.add_dll_directory` does not work for these
    packs, because ONNX Runtime loads the library with an altered search path. Linux: load each
    library of the preload list with `RTLD_GLOBAL`, in order. With `preload_ort_core`, first load the
    ONNX Runtime core library of the installed `onnxruntime` (an EP library that needs
    `libonnxruntime.so.1`, ADR-XSE7). The Linux step is not verified.
    """
    if platform == "win32":
        current = os.environ.get("PATH", "").split(os.pathsep)
        folders = [str(folder / name) for name in manifest.get("path_dirs", ())]
        os.environ["PATH"] = os.pathsep.join([*(f for f in folders if f not in current), *current])
    elif platform == "linux":
        if manifest.get("preload_ort_core"):
            import onnxruntime

            for core in sorted((Path(onnxruntime.__file__).parent / "capi").glob("libonnxruntime.so.*")):
                ctypes.CDLL(str(core), mode=ctypes.RTLD_GLOBAL)
        for name in manifest.get("preload", ()):
            ctypes.CDLL(str(folder / name), mode=ctypes.RTLD_GLOBAL)


# The CUDA runtime in the wheel nvidia-cuda-runtime 13.4.92 of the component `gpu-jpeg-cu13`.
# shortcut: the Linux name comes from the wheel listing and no Linux host loaded it; load it on a Linux host before Linux is supported.
CUDART = {"win32": "nvidia/cu13/bin/x86_64/cudart64_13.dll", "linux": "nvidia/cu13/lib/libcudart.so.13"}
_decoders: dict[str, tuple[ModuleType, Path] | None] = {}  # component id: the result of the first call


def prepare_jpeg_decoder(ep_key: str) -> tuple[ModuleType, Path] | None:
    """Make the GPU JPEG decoder of the pack of an EP key importable, and import it (ADR-88ZB).

    It returns `(nvidia.nvimgcodec, the path of the CUDA runtime library of the component)`. The
    caller loads the CUDA runtime with `ctypes.CDLL` for `cudaStreamSynchronize`: no EP pack loads a
    CUDA runtime that exports it. The component folder goes first on `sys.path` and in
    `nvidia.__path__`, so a copy of nvImageCodec in the environment is not used.

    It returns None, and the run decodes on the CPU, when the pack has no decoder, when
    `store.component_state()` is not `installed`, when the import fails, or when an other copy of
    `nvidia.nvimgcodec` is imported already. The last two log one warning line with the reason, and
    undo the changes of `sys.path`, `nvidia.__path__` and `sys.modules`. The `PATH` entries and the
    Linux preload of the component libraries stay. The first result of a process stays for each call.
    """
    catalog = load_catalog()
    component = catalog.component(ep_key)
    if component is None or store.component_state(catalog, ep_key) != "installed":
        return None
    with _lock:
        if component["id"] in _decoders:
            return _decoders[component["id"]]
        folder = store.pack_dir(component["id"], component["version"])
        prepare_libraries(folder, store.read_json(folder / "pack.json") or {})
        saved_path, saved_modules = list(sys.path), set(sys.modules)
        package = sys.modules.get("nvidia")  # an `nvidia` package that is imported before does not read `sys.path` again
        saved_portions = list(package.__path__) if package is not None and isinstance(package.__path__, list) else None
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
        if saved_portions is not None and str(folder / "nvidia") not in saved_portions:
            package.__path__.insert(0, str(folder / "nvidia"))
        reason = None
        try:
            import nvidia.nvimgcodec

            if not Path(nvidia.nvimgcodec.__file__ or "").resolve().is_relative_to(folder.resolve()):
                reason = "an other copy of nvidia.nvimgcodec is imported already"
        except (ImportError, OSError) as error:
            reason = f"the import failed: {sanitize_text(str(error))[:300]}"
        if reason is None:
            _decoders[component["id"]] = (nvidia.nvimgcodec, folder / CUDART[sys.platform])
            return _decoders[component["id"]]
        sys.path[:] = saved_path
        if saved_portions is not None:
            package.__path__[:] = saved_portions
        for name in set(sys.modules) - saved_modules:
            if name == "nvidia" or name.startswith("nvidia."):
                del sys.modules[name]
        store.warn_once(f"jpeg-decoder:{component['id']}", f"The GPU JPEG decoder {component['id']} is not used: {reason}.")
        _decoders[component["id"]] = None
        return None


def hardware_vendor_ids() -> tuple[int, ...] | None:
    """The PCI vendor id of each hardware device that ONNX Runtime lists. An EP makes its device list from these devices.

    The value is `None` when the list cannot be read: the function is not a part of the public
    Python API of ONNX Runtime.
    """
    try:
        from onnxruntime.capi import _pybind_state

        return tuple(int(device.vendor_id) for device in _pybind_state.get_hardware_devices())
    except Exception:  # noqa: BLE001 - a different ONNX Runtime build can have no such function
        return None


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
            raise EpUnavailableError(f"The EP pack '{pack_id}' registers, but the EP '{ep_name}' {NO_DEVICE}. "
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
    list a device. An EP of the Windows ML catalog registers the library of its package, which must
    be on the PC (ADR-XSE7). Else it raises `EpUnavailableError` with the install command.
    """
    catalog = load_catalog()
    row = catalog.ep(ep_key)
    pack = catalog.pack(ep_key)
    if pack is not None:
        return register_pack(ep_key, pack, install_hint(ep_key))
    if catalog.windows_ml(ep_key):
        from skellytracker.core.eps import windows_ml

        return windows_ml.register(ep_key, install_hint(ep_key))
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
