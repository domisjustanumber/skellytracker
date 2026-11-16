"""NVML access through `nvidia-ml-py`. One init for each process id. A failed init is cached.

No function here makes a CUDA call or loads an EP library.
"""

import os
import sys
import threading
from dataclasses import dataclass

from skellytracker.core._hardware import pci

_lock = threading.Lock()
_state: tuple | None = None  # (pid, the pynvml module or None, the error text or None)


class NvmlUnavailableError(Exception):
    """NVML does not load or does not start. The text is the cached reason."""


@dataclass(frozen=True)
class NvmlGpu:
    index: int
    uuid: str
    name: str | None
    pci_bus_id: str | None
    pci_vendor_id: int | None
    pci_device_id: int | None
    pci_subsys_id: int | None
    driver_version: str | None
    vram_total_bytes: int | None
    compute_capability: str | None
    brand: str | None


def _reset_after_fork() -> None:
    """Make new locks and drop the cached init in a fork child. It never calls `nvmlShutdown`."""
    global _lock, _state
    _lock = threading.Lock()
    _state = None
    module = sys.modules.get("pynvml")
    if module is not None:
        module.libLoadLock = threading.Lock()  # pynvml has no fork handler of its own


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_after_fork)


def lib():
    """The started pynvml module. Call it with `lock()` held. It raises `NvmlUnavailableError`."""
    global _state
    pid = os.getpid()
    if _state is None or _state[0] != pid:
        try:
            import pynvml

            pynvml.nvmlInit()
            _state = (pid, pynvml, None)
        except Exception as error:  # noqa: BLE001 - a missing driver or library is a result, not a fault
            _state = (pid, None, f"{type(error).__name__}: {error}")
    if _state[1] is None:
        raise NvmlUnavailableError(_state[2])
    return _state[1]


def lock() -> threading.Lock:
    return _lock


def text(value) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)


def attempt(call, *args):
    try:
        return call(*args)
    except Exception:  # noqa: BLE001 - NotSupported and each other NVML error give None
        return None


def handles(nvml_lib) -> list[tuple[str | None, object]]:
    """The PCI bus id and the handle of each GPU."""
    result = []
    for index in range(int(nvml_lib.nvmlDeviceGetCount())):
        handle = nvml_lib.nvmlDeviceGetHandleByIndex(index)
        info = attempt(nvml_lib.nvmlDeviceGetPciInfo, handle)
        result.append((None if info is None else pci.normalize_bus_id(text(info.busId)), handle))
    return result


def read_gpus() -> list[NvmlGpu]:
    """The static facts of each NVML GPU. It raises `NvmlUnavailableError` with no NVML."""
    with _lock:
        nvml_lib = lib()
        brands = {getattr(nvml_lib, n): n[11:].lower() for n in dir(nvml_lib) if n.startswith("NVML_BRAND_")}
        driver = attempt(nvml_lib.nvmlSystemGetDriverVersion)
        gpus = []
        for index, (bus, handle) in enumerate(handles(nvml_lib)):
            info = attempt(nvml_lib.nvmlDeviceGetPciInfo, handle)
            memory = attempt(nvml_lib.nvmlDeviceGetMemoryInfo, handle)
            capability = attempt(nvml_lib.nvmlDeviceGetCudaComputeCapability, handle)
            name = attempt(nvml_lib.nvmlDeviceGetName, handle)
            ids = None if info is None else int(info.pciDeviceId)
            gpus.append(NvmlGpu(
                index=index,
                uuid=text(nvml_lib.nvmlDeviceGetUUID(handle)),
                name=None if name is None else text(name),
                pci_bus_id=bus,
                pci_vendor_id=None if ids is None else ids & 0xFFFF,
                pci_device_id=None if ids is None else ids >> 16,
                pci_subsys_id=None if info is None else int(info.pciSubSystemId),
                driver_version=None if driver is None else text(driver),
                vram_total_bytes=None if memory is None else int(memory.total),
                compute_capability=None if capability is None else f"{int(capability[0])}.{int(capability[1])}",
                brand=brands.get(attempt(nvml_lib.nvmlDeviceGetBrand, handle)),
            ))
        return gpus


def free_bytes(bus: str) -> int | None:
    """One read of the free VRAM of the GPU with this PCI bus id. `None` with no NVML value."""
    try:
        with _lock:
            nvml_lib = lib()
            handle = dict(handles(nvml_lib)).get(bus)
            return None if handle is None else int(nvml_lib.nvmlDeviceGetMemoryInfo(handle).free)
    except Exception:  # noqa: BLE001 - no NVML value gives None
        return None


def driver_supported_cuda_version() -> str | None:
    """`13.3` from the NVML value 13030. Only `probe_runtime()` makes this read: it maps `nvcuda.dll`."""
    try:
        with _lock:
            value = int(lib().nvmlSystemGetCudaDriverVersion())
        return f"{value // 1000}.{value % 1000 // 10}"
    except Exception:  # noqa: BLE001 - no NVML value gives None
        return None
