"""Facts that are fixed while the application runs: the host, the runtime and the environment.

Hardware facts and live metrics have one home: `core.system` and `core.metrics`. An application,
for example freemocap, takes each host fact from them, also the facts of its anonymous ping
(`probe_host()` and `probe_environment()`), and gathers none of its own. This package sends no
ping (ADR-K8Q0 item 1).
"""

from skellytracker.core.system.environment import probe_environment
from skellytracker.core.system.host import gpu_device_keys, probe_host
from skellytracker.core.system.loaded_libraries import probe_loaded_libraries
from skellytracker.core.system.records import (
    ContainerInfo,
    EnvironmentInfo,
    GpuInfo,
    GpuVendor,
    HostInfo,
    LibraryVersion,
    LoadedLibrariesInfo,
    NvidiaContainerInfo,
    NvidiaGpuInfo,
    NvidiaLoadedLibrariesInfo,
    NvidiaRuntimeInfo,
    PackageInfo,
    PackageSource,
    PythonInfo,
    RuntimeInfo,
    VirtualizationInfo,
)
from skellytracker.core.system.runtime import probe_runtime

__all__ = [
    "ContainerInfo",
    "EnvironmentInfo",
    "GpuInfo",
    "GpuVendor",
    "HostInfo",
    "LibraryVersion",
    "LoadedLibrariesInfo",
    "NvidiaContainerInfo",
    "NvidiaGpuInfo",
    "NvidiaLoadedLibrariesInfo",
    "NvidiaRuntimeInfo",
    "PackageInfo",
    "PackageSource",
    "PythonInfo",
    "RuntimeInfo",
    "VirtualizationInfo",
    "gpu_device_keys",
    "probe_environment",
    "probe_host",
    "probe_loaded_libraries",
    "probe_runtime",
]
