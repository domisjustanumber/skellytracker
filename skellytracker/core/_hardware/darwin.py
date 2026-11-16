"""macOS readers: `sysctlbyname` of `libSystem`, and IOKit with CoreFoundation for the GPUs.

The readers use `ctypes` only and run no external command. No test ran them on a Mac.
"""

import ctypes

from skellytracker.core._hardware import pci
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


def cpu_max_frequency_hz(read=sysctl) -> int | None:
    """`hw.cpufrequency_max`, else `hw.cpufrequency`, in Hz. An Apple Silicon Mac has neither: `None`."""
    value = read("hw.cpufrequency_max") or read("hw.cpufrequency")  # the names of `sysctl hw`
    return value if isinstance(value, int) and value > 0 else None


def cores_and_memory() -> tuple[int | None, int | None, int]:
    return sysctl("hw.physicalcpu"), sysctl("hw.logicalcpu"), int(sysctl("hw.memsize") or 0)


def native_arch(machine: str) -> str:
    return "arm64" if sysctl("sysctl.proc_translated") == 1 else machine


def virtualization() -> VirtualizationInfo:
    present = sysctl("kern.hv_vmm_present")
    return VirtualizationInfo(is_vm=None if present is None else present == 1,
                              hypervisor="unknown" if present == 1 else None)


def _number(value) -> int | None:
    """An `int` from a CFNumber (`int`) or from little-endian CFData (`bytes`); `None` for other types."""
    if isinstance(value, bytes):
        return int.from_bytes(value, "little") if value else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def gpus_from_registry(entries: list) -> list[GpuInfo]:
    """The GPUs of the IORegistry property dicts that `gpu_registry_entries()` gives.

    Each dict has the IORegistry key names. A value is a `str` (CFString), `bytes` (CFData) or an
    `int` (CFNumber). An Apple Silicon GPU has unified memory and no VRAM property: its
    `vram_total_bytes` is `None`.
    """
    result = []
    for slot, entry in enumerate(entries):
        name = entry.get("model")  # IORegistry key `model`: CFData on an IOPCIDevice, CFString on an AGXAccelerator
        if isinstance(name, bytes):
            name = name.split(b"\x00", 1)[0].decode("utf-8", "replace")
        name = name.strip() or None if isinstance(name, str) else None
        vendor = pci.vendor_of(_number(entry.get("vendor-id")))  # IORegistry key `vendor-id`: 4 bytes, little-endian
        if vendor == "other" and name and "apple" in name.lower():
            vendor = "apple"
        megabytes = _number(entry.get("VRAM,totalMB"))  # IORegistry key `VRAM,totalMB` of the IOPCIDevice of a GPU
        result.append(GpuInfo(key=f"apple:{slot}:{name}", vendor=vendor, name=name,
                              vram_total_bytes=megabytes * 2**20 if megabytes else None))
    return result


_GPU_KEYS = ("model", "vendor-id", "VRAM,totalMB")


def gpu_registry_entries() -> list[dict]:
    """One property dict for each `IOAccelerator` service of the IORegistry; `[]` on each failure.

    This function was written from the IOKit and CoreFoundation documentation. No test ran it on a
    Mac. Compare its keys with the output of `ioreg -l -w0 -r -c IOAccelerator` and
    `ioreg -l -w0 -r -c IOPCIDevice`. The search goes from the accelerator to its parents, because
    the `IOPCIDevice` parent holds the keys of a PCI GPU.
    """
    try:
        iokit = ctypes.CDLL("/System/Library/Frameworks/IOKit.framework/IOKit")
        cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        pointer, u32 = ctypes.c_void_p, ctypes.c_uint32
        for library, name, restype, argtypes in (
            (iokit, "IOServiceMatching", pointer, [ctypes.c_char_p]),
            (iokit, "IOServiceGetMatchingServices", ctypes.c_int, [u32, pointer, ctypes.POINTER(u32)]),
            (iokit, "IOIteratorNext", u32, [u32]),
            (iokit, "IOObjectRelease", ctypes.c_int, [u32]),
            (iokit, "IORegistryEntrySearchCFProperty", pointer, [u32, ctypes.c_char_p, pointer, pointer, u32]),
            (cf, "CFStringCreateWithCString", pointer, [pointer, ctypes.c_char_p, u32]),
            (cf, "CFStringGetCString", ctypes.c_bool, [pointer, ctypes.c_char_p, ctypes.c_long, u32]),
            (cf, "CFGetTypeID", ctypes.c_ulong, [pointer]),
            (cf, "CFStringGetTypeID", ctypes.c_ulong, []),
            (cf, "CFDataGetTypeID", ctypes.c_ulong, []),
            (cf, "CFNumberGetTypeID", ctypes.c_ulong, []),
            (cf, "CFDataGetLength", ctypes.c_long, [pointer]),
            (cf, "CFDataGetBytePtr", pointer, [pointer]),
            (cf, "CFNumberGetValue", ctypes.c_bool, [pointer, ctypes.c_long, pointer]),
            (cf, "CFRelease", None, [pointer]),
        ):
            function = getattr(library, name)
            function.restype, function.argtypes = restype, argtypes
        utf8 = 0x08000100  # kCFStringEncodingUTF8

        def to_python(value):
            kind = cf.CFGetTypeID(value)
            if kind == cf.CFStringGetTypeID():
                buffer = ctypes.create_string_buffer(1024)
                return buffer.value.decode("utf-8", "replace") if cf.CFStringGetCString(value, buffer, 1024, utf8) else None
            if kind == cf.CFDataGetTypeID():
                return ctypes.string_at(cf.CFDataGetBytePtr(value), cf.CFDataGetLength(value))
            if kind == cf.CFNumberGetTypeID():
                number = ctypes.c_int64()
                return number.value if cf.CFNumberGetValue(value, 4, ctypes.byref(number)) else None  # 4: kCFNumberSInt64Type
            return None

        matching = iokit.IOServiceMatching(b"IOAccelerator")  # kIOAcceleratorClassName of IOKit/graphics/IOAccelTypes.h
        iterator = u32()
        # 0: kIOMainPortDefault. The call releases `matching`.
        if not matching or iokit.IOServiceGetMatchingServices(0, matching, ctypes.byref(iterator)) != 0:
            return []
        entries = []
        try:
            while service := iokit.IOIteratorNext(iterator):
                try:
                    entry = {}
                    for key in _GPU_KEYS:
                        cf_key = cf.CFStringCreateWithCString(None, key.encode(), utf8)
                        if not cf_key:
                            continue
                        try:  # 3: kIORegistryIterateRecursively | kIORegistryIterateParents
                            value = iokit.IORegistryEntrySearchCFProperty(service, b"IOService", cf_key, None, 3)
                        finally:
                            cf.CFRelease(cf_key)
                        if value:
                            try:
                                entry[key] = to_python(value)
                            finally:
                                cf.CFRelease(value)
                    entries.append(entry)
                finally:
                    iokit.IOObjectRelease(service)
        finally:
            iokit.IOObjectRelease(iterator.value)
        return entries
    except Exception:  # noqa: BLE001 - a missing framework or symbol gives no GPU, not a raise into the probe
        return []


def gpus() -> list[GpuInfo]:
    return gpus_from_registry(gpu_registry_entries())


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
