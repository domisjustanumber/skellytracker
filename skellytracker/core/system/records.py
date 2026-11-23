"""The records of `core.system`. Each value is fixed while the application runs.

Each record is frozen and has no `dict` field, so it hashes, pickles and converts to JSON with
`dataclasses.asdict`. Memory is `int` bytes. Vendor data is in a last field `nvidia`.
No text holds an absolute path or a hostname.
"""

from dataclasses import dataclass
from typing import Literal

GpuVendor = Literal["nvidia", "amd", "intel", "apple", "other"]


@dataclass(frozen=True)
class NvidiaGpuInfo:
    uuid: str
    compute_capability: str | None = None
    brand: str | None = None


@dataclass(frozen=True)
class GpuInfo:
    """One GPU. `key` is the join key: the `pci_bus_id`, else an OS id.

    On Linux, `name` of a GPU with no NVML name and no `product_name` file is the device name of
    the `pci.ids` database: `/usr/share/hwdata/pci.ids`, else `/usr/share/misc/pci.ids`. It is
    `None` when no file holds the ids. On macOS, `vram_total_bytes` is the IOKit value
    `VRAM,totalMB`. It is `None` for an Apple Silicon GPU, because that GPU has unified memory.
    `shared_memory_bytes` is the shared system memory that the GPU can use: `SharedSystemMemory` of DXGI on Windows.
    It is `None` on Linux and macOS. `is_integrated` is the DXCore adapter property `IsIntegrated` on Windows, or
    `None` when DXCore does not give it. On Linux it is the fact that the kernel driver states (`amdgpu`, `i915`, `xe`),
    and `None` for each other driver. On macOS it is `None`.
    """

    key: str
    vendor: GpuVendor
    name: str | None = None
    pci_bus_id: str | None = None
    pci_vendor_id: int | None = None
    pci_device_id: int | None = None
    pci_subsys_id: int | None = None
    is_integrated: bool | None = None
    is_software: bool | None = None
    luid: int | None = None
    driver_version: str | None = None
    vram_total_bytes: int | None = None
    shared_memory_bytes: int | None = None
    nvidia: NvidiaGpuInfo | None = None


@dataclass(frozen=True)
class VirtualizationInfo:
    is_wsl: bool = False
    is_vm: bool | None = None
    hypervisor: str | None = None


@dataclass(frozen=True)
class NvidiaContainerInfo:
    visible_devices: str | None = None
    driver_capabilities: str | None = None
    image_cuda_version: str | None = None


@dataclass(frozen=True)
class ContainerInfo:
    runtime: str
    container_id: str | None = None
    image: str | None = None
    image_digest: str | None = None
    base_os: str | None = None
    cpuset: str | None = None
    cpu_quota_cores: float | None = None
    memory_limit_bytes: int | None = None
    nvidia: NvidiaContainerInfo | None = None


@dataclass(frozen=True)
class HostInfo:
    """The result of `probe_host()`. It has no hostname field.

    `cpu_max_frequency_hz` is the nominal maximum frequency of the CPU: the registry value `~MHz`
    on Windows, `cpuinfo_max_freq` of CPU 0 on Linux, and `hw.cpufrequency_max`, else
    `hw.cpufrequency`, on macOS. It is `None` when the OS gives no value, for example on an Apple
    Silicon Mac.
    """

    os_name: str
    os_release: str
    os_version: str
    arch: str
    memory_total_bytes: int
    os_platform: str | None = None
    os_build: int | str | None = None
    os_label: str | None = None
    native_arch: str | None = None
    cpu_name: str | None = None
    cpu_physical_cores: int | None = None
    cpu_logical_cores: int | None = None
    cpu_max_frequency_hz: int | None = None
    gpus: tuple[GpuInfo, ...] = ()
    virtualization: VirtualizationInfo = VirtualizationInfo()
    container: ContainerInfo | None = None
    probe_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class NvidiaRuntimeInfo:
    cuda_device_order: str | None = None
    driver_supported_cuda_version: str | None = None


@dataclass(frozen=True)
class RuntimeInfo:
    """The result of `probe_runtime()`: facts only. `eps.recommend()` selects an EP."""

    skellytracker_version: str
    python_version: str
    skellytracker_commit: str | None = None
    mediapipe_version: str | None = None
    ort_packages: tuple[str, ...] = ()
    ort_package_versions: tuple[str, ...] = ()  # the distribution version of each item of `ort_packages`, in the same order
    windowsml_version: str | None = None
    ort_version: str | None = None
    ep_names: tuple[str, ...] = ()
    probe_errors: tuple[str, ...] = ()
    ort_disable_telemetry: str | None = None  # the value of ORT_DISABLE_TELEMETRY; `skellytracker` sets "1" unless the host set one
    nvidia: NvidiaRuntimeInfo | None = None


@dataclass(frozen=True)
class PythonInfo:
    implementation: str
    version: str
    build: str
    compiler: str


@dataclass(frozen=True)
class PackageSource:
    """The PEP 610 source of a distribution. `url` is never a `file:` URL; `local` is a basename."""

    vcs: str | None = None
    url: str | None = None
    commit: str | None = None
    requested_revision: str | None = None
    local: str | None = None
    editable: bool = False
    hashes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PackageInfo:
    name: str
    version: str
    source: PackageSource | None = None


@dataclass(frozen=True)
class EnvironmentInfo:
    """The result of `probe_environment()`. `packages` is partial when `frozen` is true."""

    python: PythonInfo
    packages: tuple[PackageInfo, ...] = ()
    argv: tuple[str, ...] = ()
    frozen: bool = False
    probe_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class LibraryVersion:
    """One loaded library. `source` is `<kind>:<detail>` with no absolute path."""

    name: str
    version: str | None = None
    source: str = ""


@dataclass(frozen=True)
class NvidiaLoadedLibrariesInfo:
    libraries: tuple[LibraryVersion, ...] = ()


@dataclass(frozen=True)
class LoadedLibrariesInfo:
    """The result of `probe_loaded_libraries()`."""

    libraries: tuple[LibraryVersion, ...] = ()
    probe_errors: tuple[str, ...] = ()
    nvidia: NvidiaLoadedLibrariesInfo | None = None
