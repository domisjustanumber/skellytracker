"""Run one model on the TRT-RTX wheel plugin in a fresh process. Usage: trt_rtx_child.py JOB.json

The plugin library is registered by its path, as the EP store does: the plugin module is not imported.
The record holds each device before and after the registration, and the full path of each loaded
TensorRT, CUDA and ONNX Runtime library, to show that no Windows ML catalog library is in the process.
"""
import ctypes
import hashlib
import json
import statistics
import sys
import sysconfig
import time
import traceback
from ctypes import wintypes
from pathlib import Path

JOB = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
R = {"job": JOB["job"], "arm": JOB["arm"], "device": JOB["device"], "ok": False}
SITE = Path(sysconfig.get_paths()["purelib"])
WATCH = ("tensorrt", "nvinfer", "nvonnx", "cudart", "cublas", "cudnn", "nvrtc", "onnxruntime", "winml", "windowsapp")
EP = "NvTensorRTRTXExecutionProvider"


def modules():
    psapi, kernel = ctypes.WinDLL("psapi", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    process, handles, needed = kernel.GetCurrentProcess(), (wintypes.HMODULE * 4096)(), wintypes.DWORD()
    psapi.EnumProcessModules(process, handles, ctypes.sizeof(handles), ctypes.byref(needed))
    found = []
    for handle in handles[: needed.value // ctypes.sizeof(wintypes.HMODULE)]:
        text = ctypes.create_unicode_buffer(1024)
        psapi.GetModuleFileNameExW(process, handle, text, 1024)
        path = Path(text.value)
        if any(w in path.name.lower() for w in WATCH) or "windowsapps" in str(path).lower():
            where = "site-packages" if SITE in path.parents else "WindowsApps" if "windowsapps" in str(path).lower() else "other"
            found.append(f"{where}:{path.name.lower()}")
    return sorted(found)


def devices(ort):
    return sorted(f"{d.ep_name} {d.device.vendor_id:04x}:{d.device.device_id:04x}" for d in ort.get_ep_devices())


def main():
    import numpy as np
    import onnxruntime as ort

    R["ort"], R["available_providers"], R["devices_before"] = ort.__version__, ort.get_available_providers(), devices(ort)
    so = ort.SessionOptions()
    so.log_severity_level = 2
    so.add_session_config_entry("session.record_ep_graph_assignment_info", "1")
    if JOB["device"] == "trt-rtx":
        library = SITE / "onnxruntime_ep_nv_tensorrt_rtx" / "onnxruntime_providers_nv_tensorrt_rtx.dll"
        ort.register_execution_provider_library(EP, str(library))
        R["devices_after"] = devices(ort)
        mine = [d for d in ort.get_ep_devices() if d.ep_name == EP and d.device.vendor_id == 0x10DE]
        R["ep_device_count"] = len(mine)
        so.add_provider_for_devices([mine[0]], {"nv_runtime_cache_path": JOB["cache"]})
        R["after_register"] = modules()
    t0 = time.perf_counter()
    session = ort.InferenceSession(JOB["model"], sess_options=so, providers=None if JOB["device"] == "trt-rtx" else ["CPUExecutionProvider"])
    R["build_ms"], R["providers"] = round(1000 * (time.perf_counter() - t0), 1), session.get_providers()
    try:
        R["nodes"] = {i.ep_name: len(i.get_nodes()) for i in session.get_provider_graph_assignment_info()}
    except Exception as exc:  # noqa: BLE001
        R["nodes"] = f"unavailable: {exc}"
    rng, feed = np.random.default_rng(1234), {}
    for item in session.get_inputs():
        shape = [d if isinstance(d, int) else 1 for d in item.shape]
        kind = {"tensor(float)": np.float32, "tensor(float16)": np.float16, "tensor(uint8)": np.uint8}[item.type]
        feed[item.name] = rng.integers(0, 255, shape, dtype=np.uint8) if kind is np.uint8 else rng.standard_normal(shape).astype(kind)
    t0 = time.perf_counter()
    outs = session.run(None, feed)
    R["first_run_ms"] = round(1000 * (time.perf_counter() - t0), 1)
    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        session.run(None, feed)
        times.append(1000 * (time.perf_counter() - t0))
    R["median_ms"] = round(statistics.median(times), 3)
    digest = hashlib.sha256()
    for out in outs:
        digest.update(np.ascontiguousarray(out).tobytes())
    R["sha256"], R["nan"] = digest.hexdigest(), int(sum(np.isnan(o).sum() for o in outs if o.dtype.kind == "f"))
    np.savez(JOB["out"], *[o.astype(np.float64) for o in outs])
    R["after_run"] = modules()
    R["ok"] = True


try:
    main()
except BaseException as exc:  # noqa: BLE001
    R["error"], R["traceback"] = f"{type(exc).__name__}: {str(exc)[:3000]}", traceback.format_exc()[-2500:]
Path(JOB["result"]).write_text(json.dumps(R, indent=1), encoding="utf-8")
