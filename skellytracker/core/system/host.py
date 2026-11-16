"""`probe_host()` and the device keys of the GPUs.

`probe_host()` makes no CUDA call, loads no EP library and imports no `onnxruntime`. It does not
raise for missing hardware: the field is `None`, with one line in `probe_errors`.
On macOS, it runs no external command: `sysctlbyname` and IOKit, through `ctypes`, give the values.
"""

import os
import platform
import sys
import threading

from skellytracker.core._hardware import nvml
from skellytracker.core._hardware.sanitize import error_line
from skellytracker.core.system.records import GpuInfo, HostInfo, NvidiaGpuInfo, VirtualizationInfo

_lock = threading.Lock()
_cached: HostInfo | None = None


def _new_lock() -> None:
    global _lock
    _lock = threading.Lock()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_new_lock)


def probe_host() -> HostInfo:
    """The host facts. The first call reads them; each later call of the process gives the same record."""
    global _cached
    with _lock:
        if _cached is None:
            _cached = _probe()
        return _cached


def merge_gpus(nvml_gpus: list, os_gpus: list[GpuInfo]) -> tuple[GpuInfo, ...]:
    """The NVML GPUs first, each with the OS facts of its PCI bus id, then each other OS GPU."""
    by_bus = {gpu.pci_bus_id: gpu for gpu in os_gpus if gpu.pci_bus_id is not None}
    merged = []
    for gpu in nvml_gpus:
        os_gpu = by_bus.get(gpu.pci_bus_id)
        merged.append(GpuInfo(
            key=gpu.pci_bus_id or f"nvml:{gpu.uuid}", vendor="nvidia", name=gpu.name, pci_bus_id=gpu.pci_bus_id,
            pci_vendor_id=gpu.pci_vendor_id, pci_device_id=gpu.pci_device_id, pci_subsys_id=gpu.pci_subsys_id,
            is_integrated=None if os_gpu is None else os_gpu.is_integrated, is_software=False,
            luid=None if os_gpu is None else os_gpu.luid, driver_version=gpu.driver_version,
            vram_total_bytes=gpu.vram_total_bytes,
            nvidia=NvidiaGpuInfo(uuid=gpu.uuid, compute_capability=gpu.compute_capability, brand=gpu.brand),
        ))
    nvml_buses = {gpu.pci_bus_id for gpu in nvml_gpus}
    nvml_names = {gpu.name for gpu in nvml_gpus}
    for gpu in os_gpus:
        same_device = gpu.pci_bus_id in nvml_buses if gpu.pci_bus_id else (gpu.vendor == "nvidia" and gpu.name in nvml_names)
        if not same_device:
            merged.append(gpu)
    return tuple(sorted(merged, key=lambda gpu: gpu.key))


def gpu_device_keys(host: HostInfo | None = None) -> tuple[tuple[str, GpuInfo], ...]:
    """Each GPU with its `device_key`: `gpu:<pci_vendor>:<pci_device>:<n>`.

    `n` is the rank by PCI bus id among the GPUs with the same vendor id and device id. A GPU with
    no bus id ranks after the GPUs with one. A GPU with no PCI ids has no device key.
    """
    host = probe_host() if host is None else host
    ranks: dict[tuple[int, int], int] = {}
    result = []
    for gpu in sorted(host.gpus, key=lambda g: (g.pci_bus_id is None, g.pci_bus_id or "", g.key)):
        if gpu.pci_vendor_id is None or gpu.pci_device_id is None:
            continue
        ids = (gpu.pci_vendor_id, gpu.pci_device_id)
        rank = ranks.get(ids, 0)
        ranks[ids] = rank + 1
        result.append((f"gpu:{ids[0]:04x}:{ids[1]:04x}:{rank}", gpu))
    return tuple(result)


def _probe() -> HostInfo:
    errors: list[str] = []

    def read(source: str, call, default=None):
        try:
            return call()
        except Exception as error:  # noqa: BLE001 - a missing source is a `probe_errors` line, not a raise
            errors.append(error_line(source, error))
            return default

    os_build, native_arch, container = None, platform.machine(), None
    if sys.platform == "win32":
        from skellytracker.core._hardware import windows as reader

        os_build = read("RtlGetVersion", reader.os_build)
        native_arch = read("IsWow64Process2", reader.native_arch)
        container = read("registry", reader.container)
    elif sys.platform == "darwin":
        from skellytracker.core._hardware import darwin as reader

        os_build = platform.mac_ver()[0] or None
        native_arch = read("sysctl", lambda: reader.native_arch(platform.machine()), platform.machine())
    else:
        from skellytracker.core._hardware import linux as reader

        os_build = platform.release() or None
        container = read("container", reader.container)
    physical, logical, memory = read("cpu and memory", reader.cores_and_memory, (None, os.cpu_count(), 0))
    nvml_gpus = read("nvml", nvml.read_gpus, [])
    return HostInfo(
        os_name=platform.system(), os_release=platform.release(), os_version=platform.version(),
        arch=platform.machine(), memory_total_bytes=memory, os_platform=platform.platform() or None,
        os_build=os_build, native_arch=native_arch, cpu_name=read("cpu name", reader.cpu_name),
        cpu_physical_cores=physical, cpu_logical_cores=logical,
        cpu_max_frequency_hz=read("cpu frequency", reader.cpu_max_frequency_hz),
        gpus=merge_gpus(nvml_gpus, read("os gpus", reader.gpus, [])),
        virtualization=read("virtualization", reader.virtualization, VirtualizationInfo()),
        container=container, probe_errors=tuple(errors),
    )
