"""`probe_loaded_libraries()`: the NVIDIA and OpenVINO libraries that this process has loaded.

It loads nothing and makes no CUDA context. It has no cache: call it in the process that ran a
model, after the first run.
"""

from skellytracker.core._hardware import libraries
from skellytracker.core._hardware.sanitize import error_line
from skellytracker.core.system.records import LibraryVersion, LoadedLibrariesInfo, NvidiaLoadedLibrariesInfo

NVIDIA_PREFIXES = ("cudart", "cudnn", "cublas", "nvinfer", "tensorrt_rtx")
OTHER_PREFIXES = ("openvino",)


def probe_loaded_libraries() -> LoadedLibrariesInfo:
    try:
        paths = libraries.loaded_module_paths()
    except Exception as error:  # noqa: BLE001 - a failed read is a `probe_errors` line
        return LoadedLibrariesInfo(probe_errors=(error_line("loaded modules", error),))
    nvidia, other = {}, {}
    for path in paths:
        name = libraries.library_name(path)
        rows = nvidia if name.startswith(NVIDIA_PREFIXES) else other if name.startswith(OTHER_PREFIXES) else None
        if rows is not None and name not in rows:
            version, source = libraries.library_version(path)
            rows[name] = LibraryVersion(name=name, version=version, source=source)
    return LoadedLibrariesInfo(
        libraries=tuple(other[name] for name in sorted(other)),
        nvidia=NvidiaLoadedLibrariesInfo(tuple(nvidia[name] for name in sorted(nvidia))) if nvidia else None,
    )
