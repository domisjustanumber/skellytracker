"""Windows readers: psutil, the registry, `RtlGetVersion`, `IsWow64Process2`, DXGI, one D3DKMT query and the DXCore
adapter property `IsIntegrated`.

Import this module only on Windows. No function here makes a CUDA call or loads an EP library.
"""

import ctypes
import re
import winreg
from ctypes import wintypes

from skellytracker.core._hardware import pci
from skellytracker.core.system.records import ContainerInfo, GpuInfo, VirtualizationInfo

_ARCH = {0x8664: "AMD64", 0xAA64: "ARM64", 0x014C: "x86"}
_HYPERVISORS = (("vmware", "vmware"), ("virtualbox", "virtualbox"), ("innotek", "virtualbox"), ("qemu", "kvm"),
                ("kvm", "kvm"), ("xen", "xen"), ("parallels", "parallels"), ("virtual machine", "hyper-v"))


def _registry_value(key: str, name: str, reg=winreg):
    try:
        with reg.OpenKey(reg.HKEY_LOCAL_MACHINE, key) as handle:
            return reg.QueryValueEx(handle, name)[0]
    except OSError:
        return None


def cpu_name(reg=winreg) -> str | None:
    value = _registry_value(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString", reg)
    return value.strip() if isinstance(value, str) else None


def cpu_max_frequency_hz(reg=winreg) -> int | None:
    """The registry value `~MHz` in Hz: the base frequency of the CPU, with no turbo frequency."""
    value = _registry_value(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "~MHz", reg)
    return value * 1_000_000 if isinstance(value, int) and value > 0 else None


def cores_and_memory() -> tuple[int | None, int | None, int]:
    import psutil

    return psutil.cpu_count(logical=False), psutil.cpu_count(logical=True), int(psutil.virtual_memory().total)


def os_build() -> int | None:
    class OsVersionInfo(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("major", wintypes.DWORD), ("minor", wintypes.DWORD),
                    ("build", wintypes.DWORD), ("platform", wintypes.DWORD), ("csd", wintypes.WCHAR * 128)]

    info = OsVersionInfo(size=ctypes.sizeof(OsVersionInfo))
    return int(info.build) if ctypes.WinDLL("ntdll").RtlGetVersion(ctypes.byref(info)) == 0 else None


def os_label(release: str, reg=winreg) -> str | None:
    """`Windows 11 Home 26H2`. `ProductName` keeps the number 10 on Windows 11, so `release` gives the number."""
    key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    product, version = (_registry_value(key, name, reg) for name in ("ProductName", "DisplayVersion"))
    edition = re.sub(r"^Windows \d+ ", "", product) if isinstance(product, str) else None
    parts = ["Windows", release, edition, version if isinstance(version, str) else None]
    return " ".join(p for p in parts if p) if edition or version else None


def native_arch() -> str | None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.IsWow64Process2.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.USHORT), ctypes.POINTER(wintypes.USHORT)]
    process, native = wintypes.USHORT(), wintypes.USHORT()
    if not kernel32.IsWow64Process2(kernel32.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(native)):
        return None
    return _ARCH.get(native.value, f"{native.value:#06x}")


def virtualization(reg=winreg) -> VirtualizationInfo:
    bios = r"HARDWARE\DESCRIPTION\System\BIOS"
    maker, product = (_registry_value(bios, name, reg) for name in ("SystemManufacturer", "SystemProductName"))
    if maker is None and product is None:
        return VirtualizationInfo()
    text = f"{maker} {product}".lower()
    hypervisor = next((name for mark, name in _HYPERVISORS if mark in text), None)
    return VirtualizationInfo(is_vm=hypervisor is not None, hypervisor=hypervisor)


def container(reg=winreg) -> ContainerInfo | None:
    kind = _registry_value(r"SYSTEM\CurrentControlSet\Control", "ContainerType", reg)
    return None if kind is None else ContainerInfo(runtime="docker")


class _Luid(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.LONG)]


class _Guid(ctypes.Structure):
    _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD), ("d", ctypes.c_ubyte * 8)]


class _AdapterDesc1(ctypes.Structure):
    _fields_ = [("description", wintypes.WCHAR * 128), ("vendor_id", wintypes.UINT), ("device_id", wintypes.UINT),
                ("subsys_id", wintypes.UINT), ("revision", wintypes.UINT), ("dedicated_video", ctypes.c_size_t),
                ("dedicated_system", ctypes.c_size_t), ("shared_system", ctypes.c_size_t), ("luid", _Luid),
                ("flags", wintypes.UINT)]


_IID_FACTORY1 = _Guid(0x770AAE78, 0xF26F, 0x4DBA, (ctypes.c_ubyte * 8)(0xA8, 0x29, 0x25, 0x3C, 0x83, 0xD1, 0xB3, 0x87))
_IID_DEVICE = _Guid(0x54EC77FA, 0x1377, 0x44E6, (ctypes.c_ubyte * 8)(0x8C, 0x32, 0x88, 0xFD, 0x5F, 0x44, 0xC8, 0x4C))
# DXCore, from `dxcore_interface.h` of the Windows SDK 10.0.22621.0: `DEFINE_GUID(IID_IDXCoreAdapterFactory, ...)`,
# `DEFINE_GUID(IID_IDXCoreAdapter, ...)` and `IsIntegrated = 12` of `enum class DXCoreAdapterProperty`
_IID_DXCORE_FACTORY = _Guid(0x78EE5945, 0xC36E, 0x4B13, (ctypes.c_ubyte * 8)(0xA6, 0x69, 0x00, 0x5D, 0xD1, 0x1C, 0x0F, 0x06))
_IID_DXCORE_ADAPTER = _Guid(0xF0DB4C7F, 0xFE5A, 0x42A2, (ctypes.c_ubyte * 8)(0xBD, 0x62, 0xF2, 0xA6, 0xCF, 0x6F, 0xC8, 0x3E))
_DXCORE_IS_INTEGRATED = 12


def _method(pointer: ctypes.c_void_p, index: int, *argtypes, restype=ctypes.c_long):
    """Method `index` of the COM object at `pointer`, as a callable that takes the arguments after `this`."""
    table = ctypes.cast(ctypes.cast(pointer, ctypes.POINTER(ctypes.c_void_p))[0], ctypes.POINTER(ctypes.c_void_p))
    function = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(table[index])
    return lambda *args: function(pointer, *args)


def dxcore_factory() -> ctypes.c_void_p | None:
    """The DXCore adapter factory (`DXCoreCreateAdapterFactory` of `dxcore.dll`), or None when DXCore is absent or fails.

    It creates no D3D device. The caller releases the factory (`IUnknown::Release`).
    """
    try:
        create = ctypes.WinDLL("dxcore").DXCoreCreateAdapterFactory
    except (OSError, AttributeError):
        return None
    factory = ctypes.c_void_p()
    if create(ctypes.byref(_IID_DXCORE_FACTORY), ctypes.byref(factory)) != 0 or not factory:
        return None
    return factory


def is_integrated(factory: ctypes.c_void_p | None, luid: _Luid) -> bool | None:
    """`IsIntegrated` of the DXCore adapter with this LUID: True for an integrated GPU, False for a dedicated GPU.

    None when there is no factory, when DXCore has no adapter with this LUID, or when the adapter does not give the
    property as one byte. The vtable indexes count the methods of `dxcore_interface.h` after the 3 methods of
    `IUnknown`: `IDXCoreAdapterFactory::GetAdapterByLuid` is 4, and `IDXCoreAdapter::IsPropertySupported`,
    `GetProperty` and `GetPropertySize` are 5, 6 and 7.
    """
    if factory is None:
        return None
    adapter = ctypes.c_void_p()
    get_adapter = _method(factory, 4, ctypes.POINTER(_Luid), ctypes.POINTER(_Guid), ctypes.POINTER(ctypes.c_void_p))
    try:
        if get_adapter(ctypes.byref(luid), ctypes.byref(_IID_DXCORE_ADAPTER), ctypes.byref(adapter)) != 0 or not adapter:
            return None
    except OSError:  # a fault in the call: the value stays unknown, and the other GPU facts stay
        return None
    try:
        if not _method(adapter, 5, wintypes.UINT, restype=ctypes.c_bool)(_DXCORE_IS_INTEGRATED):
            return None
        size = ctypes.c_size_t()
        if _method(adapter, 7, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t))(_DXCORE_IS_INTEGRATED, ctypes.byref(size)) != 0 or size.value != 1:
            return None  # the header asserts `sizeof(bool) == 1`
        value = ctypes.c_ubyte()
        if _method(adapter, 6, wintypes.UINT, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte))(_DXCORE_IS_INTEGRATED, 1, ctypes.byref(value)) != 0:
            return None
        return bool(value.value)
    except OSError:
        return None
    finally:
        _method(adapter, 2)()  # 2: IUnknown::Release


def bus_id_of_luid(low: int, high: int) -> str | None:
    """The PCI bus id of the adapter with this LUID: the one D3DKMT adapter-address query."""
    class Open(ctypes.Structure):
        _fields_ = [("luid", _Luid), ("handle", wintypes.UINT)]

    class Address(ctypes.Structure):
        _fields_ = [("bus", wintypes.UINT), ("device", wintypes.UINT), ("function", wintypes.UINT)]

    class Query(ctypes.Structure):
        _fields_ = [("handle", wintypes.UINT), ("type", wintypes.UINT), ("data", ctypes.c_void_p), ("size", wintypes.UINT)]

    gdi32 = ctypes.WinDLL("gdi32")
    opened = Open(luid=_Luid(low, high))
    if gdi32.D3DKMTOpenAdapterFromLuid(ctypes.byref(opened)) != 0:
        return None
    try:
        address = Address()
        query = Query(opened.handle, 6, ctypes.cast(ctypes.byref(address), ctypes.c_void_p), ctypes.sizeof(address))  # 6: KMTQAITYPE_ADAPTERADDRESS
        if gdi32.D3DKMTQueryAdapterInfo(ctypes.byref(query)) != 0 or address.bus > 0xFF:
            return None  # an adapter that is not on a PCI bus gives 0xFFFFFFFF
        return pci.bus_id(0, address.bus, address.device, address.function)
    finally:
        handle = wintypes.UINT(opened.handle)
        gdi32.D3DKMTCloseAdapter(ctypes.byref(handle))


def dxgi_adapters() -> list[GpuInfo]:
    """Each DXGI adapter, also a software adapter and a duplicate. `gpus()` removes them.

    `is_integrated` is `IsIntegrated` of DXCore for the adapter with the same LUID (`is_integrated()`), or None when
    DXCore does not give it.
    """
    factory = ctypes.c_void_p()
    if ctypes.WinDLL("dxgi").CreateDXGIFactory1(ctypes.byref(_IID_FACTORY1), ctypes.byref(factory)) != 0:
        raise OSError("CreateDXGIFactory1 failed")
    adapters = []
    dxcore = dxcore_factory()
    try:
        index = 0
        while True:
            adapter = ctypes.c_void_p()
            if _method(factory, 12, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p))(index, ctypes.byref(adapter)) != 0:
                break  # 12: IDXGIFactory1::EnumAdapters1; DXGI_ERROR_NOT_FOUND ends the list
            index += 1
            try:
                desc = _AdapterDesc1()
                if _method(adapter, 10, ctypes.POINTER(_AdapterDesc1))(ctypes.byref(desc)) != 0:  # 10: GetDesc1
                    continue
                version = ctypes.c_longlong()
                driver = None  # 9: IDXGIAdapter::CheckInterfaceSupport gives the user-mode driver version
                if _method(adapter, 9, ctypes.POINTER(_Guid), ctypes.POINTER(ctypes.c_longlong))(ctypes.byref(_IID_DEVICE), ctypes.byref(version)) == 0:
                    driver = ".".join(str(version.value >> shift & 0xFFFF) for shift in (48, 32, 16, 0))
                software = bool(desc.flags & 0x2)
                bus = None if software else bus_id_of_luid(desc.luid.low, desc.luid.high)
                luid = (desc.luid.high << 32) | desc.luid.low
                adapters.append(GpuInfo(
                    key=bus or f"luid:{luid:#x}", vendor=pci.vendor_of(desc.vendor_id), name=desc.description or None,
                    pci_bus_id=bus, pci_vendor_id=int(desc.vendor_id), pci_device_id=int(desc.device_id),
                    pci_subsys_id=int(desc.subsys_id), is_software=software, luid=luid, driver_version=driver,
                    vram_total_bytes=int(desc.dedicated_video) or None, shared_memory_bytes=int(desc.shared_system),
                    is_integrated=None if software else is_integrated(dxcore, desc.luid),
                ))
            finally:
                _method(adapter, 2)()  # 2: IUnknown::Release
    finally:
        _method(factory, 2)()
        if dxcore is not None:
            _method(dxcore, 2)()
    return adapters


def gpus(adapters: list[GpuInfo] | None = None) -> list[GpuInfo]:
    """The DXGI adapters without each software adapter and without a second adapter of one device."""
    return pci.drop_second_adapters(dxgi_adapters() if adapters is None else adapters)


def memory() -> tuple[int, int]:
    """The total and the available memory in bytes."""
    import psutil

    values = psutil.virtual_memory()
    return int(values.total), int(values.available)


def cpu_times() -> tuple[float, float]:
    """The busy and the total CPU seconds of all logical CPUs since the start of the system."""
    import psutil

    times = psutil.cpu_times()
    busy = float(times.user + times.system)
    return busy, busy + float(times.idle)


def process(pid: int) -> tuple[float, float, int]:
    """The identity, the CPU seconds and the RSS bytes of a process. A process that ended raises `ProcessLookupError`."""
    import psutil

    try:
        handle = psutil.Process(pid)
        with handle.oneshot():
            times = handle.cpu_times()
            return float(handle.create_time()), float(times.user + times.system), int(handle.memory_info().rss)
    except psutil.NoSuchProcess as error:
        raise ProcessLookupError(pid) from error
    except psutil.AccessDenied as error:
        raise PermissionError(pid) from error
