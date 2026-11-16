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


def _libc():
    return ctypes.CDLL("/usr/lib/libSystem.B.dylib")


def memory() -> tuple[int, int]:
    """The total and the available memory in bytes. Available is the free and the inactive pages."""
    libc = _libc()
    values, count = (ctypes.c_uint32 * 64)(), ctypes.c_uint(64)
    if libc.host_statistics64(libc.mach_host_self(), 4, values, ctypes.byref(count)) != 0:  # 4: HOST_VM_INFO64
        raise OSError("host_statistics64 failed")
    return int(sysctl("hw.memsize") or 0), (values[0] + values[2]) * int(sysctl("hw.pagesize") or 4096)


def cpu_times() -> tuple[float, float]:
    """The busy and the total CPU ticks of all logical CPUs. Only the ratio of two differences is used."""
    libc = _libc()
    ticks, count = (ctypes.c_uint32 * 4)(), ctypes.c_uint(4)  # user, system, idle, nice; each wraps at 2**32
    if libc.host_statistics(libc.mach_host_self(), 3, ticks, ctypes.byref(count)) != 0:  # 3: HOST_CPU_LOAD_INFO
        raise OSError("host_statistics failed")
    return float(ticks[0] + ticks[1] + ticks[3]), float(sum(ticks))


def process(pid: int) -> tuple[float, float, int]:
    """The identity, the CPU seconds and the RSS bytes of a process. A process that ended raises `ProcessLookupError`."""
    libc = _libc()
    info = (ctypes.c_uint64 * 12)()  # proc_taskinfo: virtual size, resident size, user time, system time, ...
    if libc.proc_pidinfo(pid, 4, ctypes.c_uint64(0), info, ctypes.sizeof(info)) <= 0:  # 4: PROC_PIDTASKINFO
        raise ProcessLookupError(pid)
    timebase = (ctypes.c_uint32 * 2)()
    libc.mach_timebase_info(timebase)
    return 0.0, (info[2] + info[3]) * timebase[0] / timebase[1] / 1e9, int(info[1])
