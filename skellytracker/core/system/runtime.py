"""`probe_runtime()`: the versions of skellytracker, Python, MediaPipe and ONNX Runtime.

It gives facts only. It does not select an EP: `eps.recommend()` does that. A plugin EP is not in
`ep_names`: `eps.status()` gives the state of each EP pack.
"""

import importlib.metadata
import os
import platform
import threading

import skellytracker
from skellytracker.core._hardware import nvml
from skellytracker.core._hardware.sanitize import error_line
from skellytracker.core.system.environment import package_source
from skellytracker.core.system.records import NvidiaRuntimeInfo, RuntimeInfo

ORT_DISTRIBUTIONS = ("onnxruntime", "onnxruntime-windowsml", "onnxruntime-gpu", "onnxruntime-directml", "onnxruntime-openvino")

_lock = threading.Lock()
_cached: RuntimeInfo | None = None


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)  # a computed name: best effort in a frozen application
    except importlib.metadata.PackageNotFoundError:
        return None


def _probe() -> RuntimeInfo:
    errors: list[str] = []
    commit = None
    try:
        source = package_source(importlib.metadata.distribution("skellytracker").read_text("direct_url.json"))
        commit = None if source is None else source.commit
    except Exception as error:  # noqa: BLE001 - no metadata is a `probe_errors` line
        errors.append(error_line("skellytracker metadata", error))
    try:
        mediapipe_version = importlib.metadata.version("mediapipe")
    except importlib.metadata.PackageNotFoundError:
        mediapipe_version = None
    ort_version, ep_names = None, ()
    try:
        import onnxruntime

        ort_version, ep_names = onnxruntime.__version__, tuple(onnxruntime.get_available_providers())
    except Exception as error:  # noqa: BLE001 - a missing or broken ONNX Runtime is a `probe_errors` line
        errors.append(error_line("onnxruntime", error))
    try:
        windowsml_version = importlib.metadata.version("windowsml")
    except importlib.metadata.PackageNotFoundError:
        windowsml_version = None
    order, cuda = os.environ.get("CUDA_DEVICE_ORDER"), nvml.driver_supported_cuda_version()
    found = [(name, version) for name in ORT_DISTRIBUTIONS if (version := _version(name)) is not None]
    return RuntimeInfo(
        skellytracker_version=skellytracker.__version__, python_version=platform.python_version(),
        skellytracker_commit=commit, mediapipe_version=mediapipe_version,
        ort_packages=tuple(name for name, _ in found), ort_package_versions=tuple(version for _, version in found),
        windowsml_version=windowsml_version, ort_version=ort_version, ep_names=ep_names, probe_errors=tuple(errors),
        nvidia=None if order is None and cuda is None else NvidiaRuntimeInfo(order, cuda),
        ort_disable_telemetry=os.environ.get("ORT_DISABLE_TELEMETRY"),
    )


def probe_runtime() -> RuntimeInfo:
    """The runtime facts. The first call reads them and imports `onnxruntime`; each later call gives the same record."""
    global _cached
    with _lock:
        if _cached is None:
            _cached = _probe()
        return _cached
