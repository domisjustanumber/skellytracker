"""The PyInstaller hook of ONNX Runtime (ADR-K8Q0 item 2). It replaces the hook of `pyinstaller-hooks-contrib`.

It collects the native libraries, the data files and the metadata of the ONNX Runtime distribution
that is installed on the build OS: `onnxruntime` on Linux and macOS, `onnxruntime-windowsml` and
`windowsml` on Windows. `windowsml` loads its DLL from `windowsml/lib` when it is imported. The EP
store reads the metadata to compare the installed version with `ort_core`. The GPU EPs are plugin
packs that the EP store downloads at run time. Thus the hook collects no GPU EP and no NVIDIA library.
"""

import importlib.metadata

from PyInstaller.utils.hooks import PY_DYLIB_PATTERNS, collect_data_files, collect_dynamic_libs, copy_metadata

LIBRARIES = [*PY_DYLIB_PATTERNS, "lib*.so.*"]  # `lib*.so` does not find a Linux library with a version suffix

binaries = collect_dynamic_libs("onnxruntime", search_patterns=LIBRARIES)
datas = collect_data_files("onnxruntime", excludes=[f"**/{pattern}" for pattern in LIBRARIES])
for name in ("onnxruntime", "onnxruntime-windowsml", "windowsml"):
    try:
        datas += copy_metadata(name)
    except importlib.metadata.PackageNotFoundError:
        continue
    if name == "windowsml":
        binaries += collect_dynamic_libs("windowsml")
