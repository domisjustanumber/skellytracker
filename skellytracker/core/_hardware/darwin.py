"""macOS readers: `sysctlbyname` of `libSystem` and `system_profiler`. No test ran them on a Mac."""

import ctypes
import json
import subprocess

from skellytracker.core.system.records import GpuInfo, VirtualizationInfo


def sysctl(name: str, as_text: bool = False):
    """One `sysctlbyname` value as an `int` or a `str`; `None` when the name does not exist."""
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
    size = ctypes.c_size_t(0)
    if libc.sysctlbyname(name.encode(), None, ctypes.byref(size), None, 0) != 0:
        return None
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctlbyname(name.encode(), buffer, ctypes.byref(size), None, 0) != 0:
        return None
    if as_text:
        return buffer.value.decode("utf-8", "replace")
    return int.from_bytes(buffer.raw[: size.value], "little")


def cpu_name() -> str | None:
    return sysctl("machdep.cpu.brand_string", as_text=True)


def cores_and_memory() -> tuple[int | None, int | None, int]:
    return sysctl("hw.physicalcpu"), sysctl("hw.logicalcpu"), int(sysctl("hw.memsize") or 0)


def native_arch(machine: str) -> str:
    return "arm64" if sysctl("sysctl.proc_translated") == 1 else machine


def virtualization() -> VirtualizationInfo:
    present = sysctl("kern.hv_vmm_present")
    return VirtualizationInfo(is_vm=None if present is None else present == 1,
                              hypervisor="unknown" if present == 1 else None)


def gpus_from_profiler(report: dict) -> list[GpuInfo]:
    """The GPUs of a `system_profiler SPDisplaysDataType -json` report."""
    result = []
    for slot, item in enumerate(report.get("SPDisplaysDataType", [])):
        name = item.get("sppci_model") or item.get("_name")
        vendor = "apple" if "apple" in str(item.get("spdisplays_vendor", "")).lower() else "other"
        result.append(GpuInfo(key=f"apple:{slot}:{name}", vendor=vendor, name=name))
    return result


def gpus() -> list[GpuInfo]:
    run = subprocess.run(["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json"],  # noqa: S603
                         capture_output=True, text=True, timeout=10, check=True)
    return gpus_from_profiler(json.loads(run.stdout))
