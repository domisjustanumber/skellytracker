#!/usr/bin/env python3
"""Hardware checks of ONNX Runtime execution provider (EP) routes on an NVIDIA GPU.

Usage::

    uv run --no-project --python 3.12 python -B run_checks.py [options]
    uv run --no-project --python 3.12 python -B run_checks.py compare REPORT.json REPORT.json [...]

The first form finds the GPU, predicts a verdict for each route from the rules table ``RULES``,
installs each route in its own uv environment, and runs the checks of the ladder in child
processes: L2 (registration and device), L3 (a probe model) and L4 (real models). It writes
``report.json`` and ``report.md``. The second form compares reports of one GPU, for example before
and after a driver change. See README.md. Standard library only.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import getpass
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import urllib.request
import zipfile
from pathlib import Path

SUITE = Path(__file__).resolve().parent
ORT = "onnxruntime==1.31.0"
NUMPY = "numpy==2.5.4"
NVIDIA = 0x10DE
PATH_LIMIT = 240
AZURE = "https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/{feed}/pypi/simple/"
WIN = "sys_platform == 'win32'"
LINUX = "sys_platform == 'linux'"

# ---------------------------------------------------------------------------------------------
# The rules table. Each prediction comes from this table, for each GPU and each OS.
# cc_min: the lowest compute capability (CC). sass: the CC list of the build; a device matches a
# listed CC with the same major and a minor that is not higher than the device minor.
# driver_min: the lowest driver branch. experimental_below: the floors pass, but the route is not
# proven below this CC.
# ---------------------------------------------------------------------------------------------
CU12_SASS = {
    "win32": ["6.1", "7.5", "8.6", "8.9", "12.0"],
    "linux": ["6.0", "7.0", "7.5", "8.0", "8.6", "8.9", "9.0", "12.0"],
}
RULES = {
    "cpu": {},
    "cuda-cu13": {"driver_min": 580, "cc_min": "7.5", "why_arch": "CUDA 13 has no build below CC 7.5"},
    "cuda-cu12": {"driver_min": 570, "sass": CU12_SASS, "why_arch": "the cu12 build has no SASS for this CC"},
    "trt-rtx-cu13": {"driver_min": 580, "cc_min": "7.5", "experimental_below": "8.0",
                     "why_arch": "TensorRT-RTX has no support below CC 7.5"},
    "trt-rtx-cu12": {"driver_min": 570, "cc_min": "8.0", "why_arch": "TensorRT-RTX cu12 needs CC 8.0 or higher"},
}
# The last driver branch for each CC range: L1 never offers an update past it.
LAST_BRANCH = [("7.0", 580)]  # Maxwell, Pascal and Volta end at R580
SCENARIOS = [(570, "A", "below R570"), (580, "B", "R570 to R579"), (10**6, "C", "R580 or newer")]

# The packs. The pins come from the EP catalog draft of this work.
ROUTES = {
    "cpu": {"ep": "CPUExecutionProvider", "select": {"type": "CPU"}, "atol": 1e-5, "deps": []},
    "cuda-cu13": {
        "ep": "CUDAExecutionProvider", "module": "onnxruntime_ep_cuda", "atol": 1e-3,
        "feed": "onnxruntime-cuda-13", "plugin": "onnxruntime-ep-cuda13==0.3.0",
        "deps": [f"nvidia-cublas==13.8.0.4; {WIN}", f"nvidia-cublas==13.8.2.12; {LINUX}",
                 "nvidia-cudnn-cu13==9.27.0.42"],
    },
    "cuda-cu12": {
        "ep": "CUDAExecutionProvider", "module": "onnxruntime_ep_cuda", "atol": 1e-3,
        "feed": "onnxruntime-cuda-12", "plugin": "onnxruntime-ep-cuda12==0.3.0",
        "deps": ["nvidia-cublas-cu12==12.9.2.10", "nvidia-cuda-runtime-cu12==12.9.79",
                 "nvidia-cudnn-cu12==9.27.0.42"],
    },
    "trt-rtx-cu13": {"ep": "NvTensorRTRTXExecutionProvider", "module": "onnxruntime_ep_nv_tensorrt_rtx",
                     "atol": 5e-2, "deps": ["onnxruntime-ep-nv-tensorrt-rtx-cu13==0.5.0"]},
    "trt-rtx-cu12": {"ep": "NvTensorRTRTXExecutionProvider", "module": "onnxruntime_ep_nv_tensorrt_rtx",
                     "atol": 5e-2, "deps": ["onnxruntime-ep-nv-tensorrt-rtx-cu12==0.5.0"]},
}
PREP_DEPS = [ORT, NUMPY, "onnx==1.23.2", "onnxconverter-common==1.16.0", "pillow==13.0.0"]

# The models, smallest first: the largest model runs last. vram_mb is the lowest total VRAM to try.
# The peak VRAM on an 8 GB card was 660 MB or less for each model; the values keep a margin for the
# desktop and the CUDA context. A 2 GB card skips YOLOX-m and RTMW-x.
OPENMMLAB = "https://download.openmmlab.com/mmpose/v1/projects/"
MODELS = {
    "rtmpose-m": {
        "url": OPENMMLAB + "rtmposev1/onnx_sdk/rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip",
        "zip_sha256": "f7fbb6c5c11a1bb70f3d445e4ddec5d144ea89ad5649c081ef976f9b24a0b741",
        "onnx_sha256": "5c0a4bf67953e6d2ac43ce15e77dc9d5d354ae18430a47d2c5963a7bc5683e3c",
        "kind": "pose", "size": [256, 192], "vram_mb": 1024},
    "rtmo-s": {
        "url": OPENMMLAB + "rtmo/onnx_sdk/rtmo-s_8xb32-600e_body7-640x640-dac2bf74_20231211.zip",
        "zip_sha256": "3da7ad88b209f9da8be87ba5c325610639af04de3b5c8a96649b98cd9e2848a2",
        "onnx_sha256": "d0703d40d19f3921da51ae725402d5fdae4d2478c7442072d3101bd396f370d8",
        "kind": "detector", "size": [640, 640], "vram_mb": 1024},
    "yolox-m": {
        "url": OPENMMLAB + "rtmposev1/onnx_sdk/yolox_m_8xb8-300e_humanart-c2c7a14a.zip",
        "zip_sha256": "a000224fd8ba283202bc62d4a5fcdfe353adb9f468777dbac1ea2ada2093adde",
        "onnx_sha256": "3dea6513388889f0fff4b77bf7a26013600321b9eb9ceb0e9a400a82572f5f23",
        "kind": "detector", "size": [640, 640], "vram_mb": 2560},
    "rtmw-x-384x288": {
        "url": OPENMMLAB + "rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip",
        "zip_sha256": "a87e1af41a0a067776dba7d46e1c21c8f6e9f18e247e0e606718dd1f31e96ffd",
        "onnx_sha256": "bd033156e5104c4f5d2edfe0453e02661e30a2f3da453ec93c8764d561b83054",
        "kind": "pose", "size": [384, 288], "vram_mb": 2560},
}
IMAGE = {
    "url": "https://github.com/freemocap/skellysamples/releases/download/single_images_v07_12_26/"
           "sample_recording_a_pose_image.jpg",
    "sha256": "5ec5b9e3a587ba06c8f9d0dfbc9749dda31c3380ab7f67d2395f267db79a580d",
}

WINDOWS_CODES = {
    0xC0000005: "access violation", 0xC0000135: "a DLL was not found", 0xC000001D: "illegal instruction",
    0xC00000FD: "stack overflow", 0xC0000409: "fail-fast or stack buffer overrun",
    0xE000007E: "a delay-loaded DLL was not found", 0xE06D7363: "an uncaught C++ exception",
}


# --------------------------------------------------------------------------------------------- GPU
def cc_tuple(text: str) -> tuple[int, int]:
    major, minor = text.split(".")
    return int(major), int(minor)


class Nvml:
    """A small NVML reader (ctypes). No UUID, no serial, no bus id."""

    def __init__(self) -> None:
        names = ["nvml.dll", r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll"] if os.name == "nt" \
            else ["libnvidia-ml.so.1"]
        self.lib = None
        for name in names:
            try:
                self.lib = ctypes.CDLL(name)
                break
            except OSError:
                continue
        if self.lib is None or self.lib.nvmlInit_v2() != 0:
            raise OSError("NVML is not available")
        self.handle = ctypes.c_void_p()
        if self.lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(self.handle)) != 0:
            raise OSError("NVML lists no GPU")

    def text(self, func: str, *args) -> str:
        buf = ctypes.create_string_buffer(96)
        getattr(self.lib, func)(*args, buf, 96)
        return buf.value.decode()

    def facts(self) -> dict:
        lib, h = self.lib, self.handle
        count, major, minor, cuda = ctypes.c_uint(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
        lib.nvmlDeviceGetCount_v2(ctypes.byref(count))
        lib.nvmlDeviceGetCudaComputeCapability(h, ctypes.byref(major), ctypes.byref(minor))
        lib.nvmlSystemGetCudaDriverVersion_v2(ctypes.byref(cuda))
        pci = (ctypes.c_uint * 32)()  # nvmlPciInfo_t: words 7 and 8 hold the device and subsystem ids
        lib.nvmlDeviceGetPciInfo_v3(h, ctypes.byref(pci))
        return {
            "source": "nvml", "count": count.value, "name": self.text("nvmlDeviceGetName", h),
            "cc": f"{major.value}.{minor.value}", "driver_version": self.text("nvmlSystemGetDriverVersion"),
            "cuda_driver_nvml": cuda_text(cuda.value), "vram_total_mb": round(self.memory()[0]),
            "pci": f"{pci[7] & 0xFFFF:04x}:{pci[7] >> 16:04x}:{pci[8]:08x}",
        }

    def memory(self) -> tuple[float, float]:
        class Memory(ctypes.Structure):
            _fields_ = [("total", ctypes.c_ulonglong), ("free", ctypes.c_ulonglong), ("used", ctypes.c_ulonglong)]

        mem = Memory()
        self.lib.nvmlDeviceGetMemoryInfo(self.handle, ctypes.byref(mem))
        return mem.total / 2**20, mem.used / 2**20


def driver_branch(version: str) -> int:
    """The release branch of a driver version: 582.78 is R580, 576.88 is R575, 570.124.04 is R570."""
    return int(version.split(".")[0]) // 5 * 5


def cuda_text(value: int) -> str | None:
    return f"{value // 1000}.{value % 1000 // 10}" if value > 0 else None


def cuda_driver_api() -> str | None:
    """The highest CUDA version of the driver, from cuDriverGetVersion (nvcuda.dll or libcuda.so.1)."""
    try:
        lib = ctypes.CDLL("nvcuda.dll" if os.name == "nt" else "libcuda.so.1")
        value = ctypes.c_int()
        return cuda_text(value.value) if lib.cuDriverGetVersion(ctypes.byref(value)) == 0 else None
    except OSError:
        return None


def smi_facts() -> dict | None:
    smi = shutil.which("nvidia-smi")
    if not smi:
        return None
    query = "name,compute_cap,driver_version,memory.total,pci.device_id,pci.sub_device_id,count"
    try:
        out = subprocess.run([smi, f"--query-gpu={query}", "--format=csv,noheader,nounits"],  # noqa: S603
                             capture_output=True, text=True, timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    name, cc, driver, mem, dev_id, sub_id, count = [v.strip() for v in out.splitlines()[0].split(",")]
    dev = int(dev_id, 16)
    return {"source": "nvidia-smi", "count": int(count), "name": name, "cc": cc, "driver_version": driver,
            "cuda_driver_nvml": None, "vram_total_mb": int(float(mem)),
            "pci": f"{dev & 0xFFFF:04x}:{dev >> 16:04x}:{int(sub_id, 16):08x}"}


def detect_gpu() -> tuple[dict | None, Nvml | None]:
    nvml = None
    try:
        nvml = Nvml()
        gpu = nvml.facts()
    except OSError:
        gpu = smi_facts()
    if gpu:
        gpu["cuda_driver_api"] = cuda_driver_api()
        gpu["driver_branch"] = driver_branch(gpu["driver_version"])
    return gpu, nvml


# ----------------------------------------------------------------------------------- predictions
def os_key() -> str:
    return "win32" if os.name == "nt" else "linux"


def last_branch(cc: str) -> int | None:
    return next((branch for cc_max, branch in LAST_BRANCH if cc_tuple(cc) <= cc_tuple(cc_max)), None)


def scenario(gpu: dict | None) -> dict:
    if not gpu:
        return {"name": "none", "text": "no NVIDIA GPU"}
    branch = gpu["driver_branch"]
    name, text = next((n, t) for limit, n, t in SCENARIOS if branch < limit)
    cap = last_branch(gpu["cc"])
    if name == "C" and cap:
        text = f"R{cap} (the last branch for CC {gpu['cc']})"
    return {"name": name, "text": text, "driver_branch": branch}


def anomalies(gpu: dict | None) -> list[str]:
    if not gpu:
        return []
    cap = last_branch(gpu["cc"])
    if cap and gpu["driver_branch"] > cap:
        return [f"driver branch R{gpu['driver_branch']} is newer than R{cap}, the last branch for CC {gpu['cc']}"]
    return []


def arch_ok(rule: dict, cc: str, osk: str) -> bool:
    if "cc_min" in rule:
        return cc_tuple(cc) >= cc_tuple(rule["cc_min"])
    major, minor = cc_tuple(cc)
    return any(m == major and n <= minor for m, n in map(cc_tuple, rule["sass"][osk]))


def predict(route: str, gpu: dict | None, osk: str) -> dict:
    """The L1 verdict for one route: ok, experimental, update-driver, unsupported or no-nvidia-gpu."""
    rule = RULES[route]
    if not rule:
        return {"verdict": "ok", "reason": "built in"}
    if not gpu:
        return {"verdict": "no-nvidia-gpu", "reason": "no NVIDIA GPU found"}
    cc, branch, need = gpu["cc"], gpu["driver_branch"], rule["driver_min"]
    if not arch_ok(rule, cc, osk):
        return {"verdict": "unsupported", "reason": f"CC {cc}: {rule['why_arch']}"}
    cap = last_branch(cc)
    if branch < need:
        if cap and need > cap:
            return {"verdict": "unsupported", "reason": f"needs R{need}; the last branch for CC {cc} is R{cap}"}
        return {"verdict": "update-driver", "target_branch": need,
                "reason": f"driver R{branch} is below R{need}; update to R{need} or newer"
                          + (f" (not past R{cap})" if cap else "")}
    if "experimental_below" in rule and cc_tuple(cc) < cc_tuple(rule["experimental_below"]):
        return {"verdict": "experimental", "reason": f"floors pass; not proven below CC {rule['experimental_below']}"}
    return {"verdict": "ok", "reason": "floors pass"}


def observed(rec: dict) -> dict:
    """The observed verdict of one route record: pass, partial, fail, error or not-run."""
    if not rec.get("ran"):
        return {"verdict": "not-run", "reason": rec.get("skip_reason", "")}
    if not rec["install"].get("ok"):
        return {"verdict": "error", "stage": "install", "reason": rec["install"].get("reason", "")}
    for level in ("l2", "l3"):
        part = rec.get(level) or {}
        if not part.get("ok"):
            return {"verdict": "fail", "stage": level.upper(), "mode": part.get("mode", ""),
                    "reason": part.get("reason", "not reached")}
    bad = [f"{r['model']} {r['precision']}" for r in rec.get("l4", []) if r.get("ran") and not r.get("ok")]
    if bad:
        return {"verdict": "partial", "stage": "L4", "reason": "L4 failed: " + ", ".join(bad)}
    return {"verdict": "pass"}


def match(pred: str, obs: str) -> str:
    if obs in ("not-run", "error"):
        return "n/a"
    if pred == "experimental":
        return "informational"
    expected_pass = pred == "ok"
    return "yes" if expected_pass == (obs in ("pass", "partial")) else "NO"


# ------------------------------------------------------------------------------- environments
def clean_env(work: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "PYTHONPATH", "PYTHONHOME", "CONDA_PREFIX")}
    env.setdefault("UV_CACHE_DIR", str(work / "uv-cache"))
    env["PYTHONUTF8"] = "1"
    return env


def pyproject(name: str, deps: list[str], feed: str | None, plugin: str | None) -> str:
    deps = [ORT, NUMPY, *deps] + ([plugin] if plugin else [])
    lines = [
        "[project]", f'name = "epdc-{name}"', 'version = "0"', 'requires-python = "==3.12.*"',
        "dependencies = [" + ", ".join(json.dumps(d) for d in deps) + "]", "",
        "[tool.uv]", "package = false",
        "environments = [\"sys_platform == 'win32' and platform_machine == 'AMD64'\", "
        "\"sys_platform == 'linux' and platform_machine == 'x86_64'\"]", "",
    ]
    if feed:
        lines += ["[[tool.uv.index]]", 'name = "ort-feed"', f'url = "{AZURE.format(feed=feed)}"',
                  "explicit = true", "", "[tool.uv.sources]",
                  f'{plugin.split("==")[0]} = {{ index = "ort-feed" }}', ""]
    return "\n".join(lines)


def venv_python(project: Path) -> Path:
    return project / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def install(work: Path, name: str, deps: list[str], feed=None, plugin=None) -> dict:
    project = work / "envs" / name
    project.mkdir(parents=True, exist_ok=True)
    (project / "pyproject.toml").write_text(pyproject(name, deps, feed, plugin), encoding="utf-8")
    uv = os.environ.get("UV") or shutil.which("uv")
    if not uv:
        return {"ok": False, "reason": "uv is not on the PATH"}
    start = time.perf_counter()
    try:
        proc = subprocess.run([uv, "sync", "--project", str(project), "--python", "3.12"],  # noqa: S603
                              capture_output=True, text=True, timeout=3600, env=clean_env(work))
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "uv sync timed out"}
    rec = {"ok": proc.returncode == 0, "seconds": round(time.perf_counter() - start, 1)}
    if proc.returncode:
        rec["reason"] = "uv sync failed: " + tail(proc.stderr, 12)
    else:
        rec["download_mb"] = lock_download_mb(project / "uv.lock")
    rec["python"] = str(venv_python(project))
    return rec


def lock_download_mb(lock: Path) -> float | None:
    """The wheel bytes of this platform in a uv.lock file (the download size with a cold cache)."""
    if not lock.is_file():
        return None
    plat = ("win_amd64",) if os.name == "nt" else ("manylinux", "x86_64")
    total = 0
    for pkg in tomllib.loads(lock.read_text(encoding="utf-8")).get("package", []):
        wheels = pkg.get("wheels", [])
        name = lambda w: w["url"].rsplit("/", 1)[-1]  # noqa: E731
        fits = [w for w in wheels if all(p in name(w) for p in plat) and ("cp312" in name(w) or "py3" in name(w)
                                                                         or "abi3" in name(w))]
        fits = fits or [w for w in wheels if name(w).endswith("none-any.whl")]
        total += fits[0].get("size", 0) if fits else 0
    return round(total / 2**20, 1)


def tail(text: str, lines: int) -> str:
    return "\n".join((text or "").strip().splitlines()[-lines:])[-1500:]


# ---------------------------------------------------------------------------------- downloads
def fetch(url: str, sha256: str, dest: Path) -> None:
    """Download to dest and check the sha256. Refuse a URL that is not https."""
    if not url.startswith("https://"):
        raise ValueError(f"not an https URL: {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=120) as resp, tmp.open("wb") as out:  # noqa: S310
        while chunk := resp.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != sha256:
        tmp.unlink()
        raise ValueError(f"sha256 mismatch for {url.rsplit('/', 1)[-1]}: got {digest.hexdigest()}")
    tmp.replace(dest)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 22):
            digest.update(chunk)
    return digest.hexdigest()


def get_model(work: Path, key: str) -> Path:
    spec, folder = MODELS[key], work / "models"
    folder.mkdir(parents=True, exist_ok=True)
    onnx = folder / f"{key}.onnx"
    if onnx.is_file() and file_sha256(onnx) == spec["onnx_sha256"]:
        return onnx
    archive = folder / f"{key}.zip"
    fetch(spec["url"], spec["zip_sha256"], archive)
    with zipfile.ZipFile(archive) as zf:
        member = next(n for n in zf.namelist() if n.endswith(".onnx"))
        onnx.write_bytes(zf.read(member))
    archive.unlink()
    if file_sha256(onnx) != spec["onnx_sha256"]:
        raise ValueError(f"sha256 mismatch for the model in {key}.zip")
    return onnx


# ----------------------------------------------------------------------------------- children
class VramSampler:
    """Sample the used memory of the device (NVML) while a child runs. Device wide, not per process."""

    def __init__(self, nvml: Nvml | None) -> None:
        self.nvml, self.peak, self.base, self.stop = nvml, 0.0, 0.0, threading.Event()

    def __enter__(self):
        if self.nvml:
            self.base = self.peak = self.nvml.memory()[1]
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()
        return self

    def loop(self) -> None:
        while not self.stop.wait(0.02):
            self.peak = max(self.peak, self.nvml.memory()[1])

    def __exit__(self, *exc) -> None:
        if self.nvml:
            self.stop.set()
            self.thread.join()

    def delta_mb(self) -> float | None:
        return round(self.peak - self.base) if self.nvml else None


def exit_reason(code: int) -> str:
    if code == 127:
        return "exit 127: a library or symbol failed to load (for example a partial cuDNN set)"
    if code < 0:
        return f"ended by signal {-code}"
    text = WINDOWS_CODES.get(code & 0xFFFFFFFF)
    return f"exit {code & 0xFFFFFFFF:#010x}: {text}" if text else f"exit {code}"


def run_child(ctx: dict, route: str, python: str, job: dict, timeout: float) -> dict:
    """Run route_check.py with one job. A crash or a timeout becomes a recorded reason."""
    jobs = ctx["work"] / "jobs"
    jobs.mkdir(exist_ok=True)
    stem = "-".join(str(job.get(k, "")) for k in ("stage", "tag")) + ("-fallback" if job["allow_fallback"] else "")
    job_file, result_file = jobs / f"{route}-{stem}.json", jobs / f"{route}-{stem}.result.json"
    result_file.unlink(missing_ok=True)
    spec = ROUTES[route]
    job = dict(job, result=str(result_file), path_limit=PATH_LIMIT, route=route, module=spec.get("module"),
               select=spec.get("select", {"vendor_id": NVIDIA}), atol=spec["atol"])
    job_file.write_text(json.dumps(job), encoding="utf-8")
    cmd = [python, "-I", "-B", str(SUITE / "route_check.py"), str(job_file)]
    start = time.perf_counter()
    with VramSampler(ctx["nvml"] if route != "cpu" else None) as vram:
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=timeout,  # noqa: S603
                                  env=clean_env(ctx["work"]), cwd=ctx["work"])
            code, err = proc.returncode, proc.stderr
        except subprocess.TimeoutExpired as exc:
            code, err = None, exc.stderr or ""
    if isinstance(err, bytes):  # the EP loggers can write NUL bytes
        err = err.decode("utf-8", "replace").replace("\x00", "")
    rec = json.loads(result_file.read_text(encoding="utf-8")) if result_file.is_file() else {}
    rec["child_s"] = round(time.perf_counter() - start, 1)
    errors = [ANSI.sub("", line).strip() for line in (err or "").splitlines()
              if "ERROR" in line or "[E:" in line]
    if errors:
        rec["ep_log"] = [e[max(e.find("ERROR"), 0):][:400] for e in dict.fromkeys(errors)][:4]
    rec["vram_peak_mb"] = vram.delta_mb()
    if code != 0:
        crash = f"timeout after {timeout:.0f} s" if code is None else exit_reason(code)
        rec["crash"] = crash
        rec["stderr_tail"] = tail(ANSI.sub("", err or ""), 8)
        if not rec.get("l2", {}).get("ok"):
            level = "l2"
        else:
            level = "l3" if job["stage"] == "l2l3" else "l4"
        part = rec.setdefault(level, {})
        part.update(ok=False, reason=f"child crashed: {crash}", mode="timeout" if code is None else "crash")
    return rec


def failure_mode(part: dict) -> str:
    reason = part.get("reason", "")
    if part.get("mode"):
        return part["mode"]
    for key, mode in (("path guard", "path-guard"), ("no device", "no-device"), ("fallback", "cpu-fallback"),
                      ("differs from CPU", "wrong-output"), ("not both on", "cpu-fallback"),
                      ("NaN", "wrong-output"), ("register", "register-error"), ("Error 126", "register-error"),
                      ("running", "run-error")):
        if key in reason:
            return mode
    return "session-error" if part.get("session_ms") is None else "run-error"


def check_route(ctx: dict, route: str, rec: dict) -> None:
    args, spec = ctx["args"], ROUTES[route]
    print(f"[{route}] install ...", flush=True)
    rec["install"] = install(ctx["work"], route, spec["deps"], spec.get("feed"), spec.get("plugin"))
    python = rec["install"].pop("python")
    if not rec["install"]["ok"]:
        return
    packages = ["onnxruntime", *[d.split("==")[0] for d in spec["deps"] + [spec.get("plugin") or ""] if d]]
    rec["packages"] = installed_versions(python, packages)
    print(f"[{route}] L2 + L3 ...", flush=True)
    probe = {"model": str(ctx["assets"] / "probe.onnx"), "input": str(ctx["assets"] / "probe.input.npy")}
    base = {"stage": "l2l3", "tag": "probe", "probe": probe, "allow_fallback": False}
    child = run_child(ctx, route, python, base, 300)
    rec["l2"], rec["l3"] = child.get("l2", {}), child.get("l3")
    rec["library_dirs"] = child.get("library_dirs", [])
    for key in ("crash", "stderr_tail"):
        if key in child:
            rec[f"l2l3_{key}"] = child[key]
    for part in (rec["l2"], rec["l3"]):
        if part and not part.get("ok"):
            part["mode"] = failure_mode(part)
    if rec["l2"].get("ok") and not (rec["l3"] or {}).get("ok"):
        retry = run_child(ctx, route, python, dict(base, allow_fallback=True), 300)
        rec["l3_with_fallback"] = slim(retry.get("l3"), retry)
    if args.quick or not (rec["l3"] or {}).get("ok"):
        rec["l4"] = []
        return
    rec["l4"] = [run_l4(ctx, route, python, key, prec) for key in ctx["models"] for prec in ctx["precisions"]]


def slim(part: dict | None, child: dict) -> dict:
    out = dict(part or {})
    if "crash" in child:
        out["crash"] = child["crash"]
    return out


def run_l4(ctx: dict, route: str, python: str, key: str, prec: str) -> dict:
    base = {"model": key, "precision": prec, "ran": False}
    prep = ctx["prep"].get("models", {}).get(key, {})
    if "error" in prep:
        return dict(base, reason=f"prep failed: {prep['error']}")
    if prec == "fp16" and prep.get("fp16") != "made":
        return dict(base, reason=f"no fp16 model: {prep.get('fp16', 'not asked')}")
    gpu = ctx["gpu"]
    if route != "cpu" and gpu and gpu["vram_total_mb"] < MODELS[key]["vram_mb"]:
        return dict(base, reason=f"skipped: VRAM ({gpu['vram_total_mb']} MB < {MODELS[key]['vram_mb']} MB)")
    print(f"[{route}] L4 {key} {prec} ...", flush=True)
    assets = ctx["assets"]
    onnx = str(ctx["model_paths"][key] if prec == "fp32" else assets / f"{key}.fp16.onnx")
    model = {"key": key, "precision": prec, "onnx": onnx, "input": str(assets / f"{key}.input.npy"),
             "ref": str(assets / f"{key}.ref.npz")}
    job = {"stage": "l4", "tag": f"{key}-{prec}", "model": model, "runs": ctx["args"].runs, "allow_fallback": False}
    strict = l4_part(run_child(ctx, route, python, job, ctx["args"].timeout))
    rec = dict(base, ran=True, strict_ok=bool(strict.get("ok")))
    if strict.get("ok"):
        rec.update(strict)
    else:
        # ORT puts shape nodes on the CPU EP, so a strict session can fail with no real problem.
        # Run once more with the fallback allowed: it gives the numbers and the op types on the CPU.
        rec["strict"] = {k: strict[k] for k in ("reason", "failed_op_type", "crash", "ep_log") if strict.get(k)}
        rec.update(l4_part(run_child(ctx, route, python, dict(job, allow_fallback=True), ctx["args"].timeout)))
        if not rec.get("ok"):
            rec["mode"] = failure_mode(rec)
    if prec == "fp16" and gpu and cc_tuple(gpu["cc"]) < (7, 0):
        rec["note"] = "informational: consumer Pascal fp16 throughput is very low"
    return rec


def l4_part(child: dict) -> dict:
    """The L4 result of one child, flat: measurements, node counts and the op types on the CPU EP."""
    part = dict(child.get("l4") or {})
    assign = part.pop("assignment", {})
    part["assign_counts"] = {ep: v["nodes"] for ep, v in assign.items()}
    part["cpu_op_types"] = assign.get("CPUExecutionProvider", {}).get("op_types", [])
    part["cpu_nodes"] = assign.get("CPUExecutionProvider", {}).get("nodes", 0)
    part["vram_peak_mb"] = child.get("vram_peak_mb")
    for key in ("crash", "stderr_tail", "ep_log"):
        if child.get(key):
            part[key] = child[key]
    if not child.get("l2", {}).get("ok"):
        part.update(ok=False, reason="L2 failed in the L4 child: " + child.get("l2", {}).get("reason", ""))
    part.pop("model", None)
    part.pop("precision", None)
    return part


def installed_versions(python: str, packages: list[str]) -> dict:
    code = ("import json,sys;from importlib.metadata import version as v;"
            "print(json.dumps({p: v(p) for p in sys.argv[1:]}))")
    try:
        out = subprocess.run([python, "-I", "-c", code, *packages], capture_output=True,  # noqa: S603
                             text=True, timeout=60, check=True).stdout
        return json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}


# ------------------------------------------------------------------------------------- report
def host_facts() -> dict:
    facts = {"os": platform.system(), "os_release": platform.release(), "os_build": platform.version(),
             "machine": platform.machine(), "python": platform.python_version()}
    if facts["os"] == "Linux":
        try:
            facts["os_name"] = platform.freedesktop_os_release().get("PRETTY_NAME", "")
        except OSError:
            pass
    return facts


def verdict_key(report: dict, rec: dict) -> dict:
    gpu = report["gpu"] or {}
    fields = {"driver_version": gpu.get("driver_version"), "pci": gpu.get("pci"),
              "os_build": report["host"]["os_build"], "packages": rec.get("packages", {})}
    return {"fields": fields, "hash": hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()[:16]}


def private_values() -> list[tuple[str, str]]:
    """(value, placeholder) pairs that the report must not hold."""
    pairs = [(str(Path.home()), "<home>"), (str(Path.home()).replace("\\", "/"), "<home>")]
    users = {getpass.getuser(), os.environ.get("USERNAME", ""), os.environ.get("USER", "")}
    pairs += [(value, "<user>") for value in users if len(value) > 1]
    for value in {socket.gethostname(), platform.node()}:
        if value:
            pairs += [(value, "<host>"), (value.split(".")[0], "<host>")]
    return sorted(pairs, key=lambda p: -len(p[0]))


def sanitize(obj, ctx_paths: list[tuple[str, str]]):
    if isinstance(obj, dict):
        return {k: sanitize(v, ctx_paths) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v, ctx_paths) for v in obj]
    if isinstance(obj, str):
        for value, placeholder in ctx_paths:
            if value in obj:
                obj = obj.replace(value, placeholder)
            if placeholder in ("<user>", "<host>"):
                obj = re.sub(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", placeholder, obj,
                             flags=re.IGNORECASE)
    return obj


ANSI = re.compile(r"\x1b\[[0-9;]*m")
USER_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?![<{%$])[\w.-]+|/home/(?![<{%$])[A-Za-z_][\w.-]*")


def redact_findings(text: str) -> list[str]:
    found = []
    for value, placeholder in private_values():
        if placeholder == "<home>" and value in text:
            found.append("home folder path")
        elif placeholder != "<home>" and re.search(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])",
                                                   text, re.IGNORECASE):
            found.append("user name" if placeholder == "<user>" else "host name")
    if USER_PATH.search(text):
        found.append("absolute user path")
    return sorted(set(found))


def fmt(value, digits=3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.0f}" if abs(value) >= 100 else f"{value:.{digits}g}"
    return str(value)


def markdown(report: dict) -> str:
    gpu, host, sc = report["gpu"] or {}, report["host"], report["scenario"]
    lines = [
        "# EP device checks", "",
        f"- GPU: {gpu.get('name', 'none')}, CC {gpu.get('cc', '-')}, {gpu.get('vram_total_mb', '-')} MB, "
        f"PCI {gpu.get('pci', '-')}",
        f"- Driver: {gpu.get('driver_version', '-')} (max CUDA {gpu.get('cuda_driver_api') or gpu.get('cuda_driver_nvml')})"
        f"; scenario {sc['name']}: {sc['text']}",
        f"- OS: {host['os']} {host['os_release']} build {host['os_build']}; Python {host['python']}",
        f"- Mode: {'quick (L2, L3)' if report['args']['quick'] else 'full (L2, L3, L4)'}; "
        f"precisions {','.join(report['args']['precisions'])}; runs {report['args']['runs']}; "
        f"duration {report['duration_s']} s",
    ]
    lines += [f"- ANOMALY: {a}" for a in report["anomalies"]]
    lines += ["", "| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms |"
              " L3 max diff | Install s | Download MB |", "|---|---|---|---|---|---|---|---|---|---|"]
    for route, rec in report["routes"].items():
        obs, l2, l3 = rec["observed"], rec.get("l2") or {}, rec.get("l3") or {}
        stage = " ".join(x for x in (obs.get("stage", ""), obs.get("mode", "")) if x) or "-"
        lines.append(f"| {route} | {rec['predicted']['verdict']} | {obs['verdict']} | {rec['match']} | {stage} | "
                     f"{fmt(l2.get('register_ms'))} | {fmt(l3.get('session_ms'))} | {fmt(l3.get('max_abs_diff'))} | "
                     f"{fmt(rec.get('install', {}).get('seconds'))} | {fmt(rec.get('install', {}).get('download_mb'))} |")
    l4 = [(r, x) for r, rec in report["routes"].items() for x in rec.get("l4", [])]
    if l4:
        lines += ["", "Strict: the session built with `session.disable_cpu_ep_fallback=1`. When it did not, the"
                  " numbers come from a second run with the fallback allowed.", "",
                  "| Route | Model | Prec | OK | Strict | Session ms | First ms | Median ms | Max diff | Rel diff |"
                  " NaN/Inf | CPU nodes (op types) | VRAM MB | Note |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for route, r in l4:
            rel = r["max_abs_diff"] / r["max_abs_ref"] if r.get("max_abs_diff") is not None and r.get("max_abs_ref") \
                else None
            note = r.get("reason", "") if not r.get("ok") else r.get("note", "")
            if r.get("ran") and not r.get("ok") and r.get("ep_log"):
                note += " / EP log: " + r["ep_log"][0][:200]
            cpu = f"{r.get('cpu_nodes', '-')} ({', '.join(r.get('cpu_op_types', []))})" if r.get("ran") else "-"
            lines.append(f"| {route} | {r['model']} | {r['precision']} | {r.get('ok', '-') if r['ran'] else 'skip'} | "
                         f"{r.get('strict_ok', '-')} | {fmt(r.get('session_ms'))} | {fmt(r.get('first_run_ms'))} | {fmt(r.get('median_ms'))} | "
                         f"{fmt(r.get('max_abs_diff'))} | {fmt(rel)} | {r.get('nan', '-')}/{r.get('inf', '-')} | "
                         f"{cpu} | {fmt(r.get('vram_peak_mb'))} | {' '.join(note.replace('|', '/').split())[:300]} |")
    lines += ["", "## Findings", ""] + ([f"- {f}" for f in report["findings"]] or ["- none"])
    return "\n".join(lines) + "\n"


def findings(report: dict) -> list[str]:
    out = [f"anomaly: {a}" for a in report["anomalies"]]
    for route, rec in report["routes"].items():
        pred, obs = rec["predicted"], rec["observed"]
        if rec["match"] == "NO":
            out.append(f"{route}: predicted {pred['verdict']} ({pred['reason']}), observed {obs['verdict']} "
                       f"({obs.get('reason', '')[:200]})")
        if obs["verdict"] == "error":
            out.append(f"{route}: install error: {obs.get('reason', '')[:300]}")
        for r in rec.get("l4", []):
            if r.get("ran") and not r.get("ok"):
                log = f"; EP log: {r['ep_log'][0][:250]}" if r.get("ep_log") else ""
                out.append(f"{route}: L4 {r['model']} {r['precision']} failed: {r.get('reason', '')[:250]}{log}")
            limit = 5e-2 if r["precision"] == "fp16" else 1e-2
            if r.get("ok") and r.get("max_abs_ref") and r["max_abs_diff"] / r["max_abs_ref"] > limit:
                out.append(f"{route}: {r['model']} {r['precision']}: relative diff "
                           f"{r['max_abs_diff'] / r['max_abs_ref']:.3g} > {limit}")
            if r.get("ok") and r.get("shapes_match") is False:
                out.append(f"{route}: {r['model']} {r['precision']}: output shapes differ from the CPU reference")
    return out


def disk_mb(folder: Path) -> float:
    seen, total = set(), 0
    for path in folder.rglob("*") if folder.is_dir() else []:
        try:
            st = path.stat()
        except OSError:
            continue
        if path.is_file() and (st.st_dev, st.st_ino) not in seen:
            seen.add((st.st_dev, st.st_ino))
            total += st.st_size
    return round(total / 2**20)


# ---------------------------------------------------------------------------------------- run
def default_work() -> Path:
    base = os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.environ.get("XDG_CACHE_HOME")
    return Path(base or Path.home() / ".cache") / "epdc"


def parse_run(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Hardware checks of ONNX Runtime EP routes.")
    p.add_argument("--routes", default=",".join(ROUTES), help="comma list (default: all)")
    p.add_argument("--include-unexpected", action="store_true", help="also run routes predicted to fail")
    p.add_argument("--quick", action="store_true", help="L2 and L3 only")
    p.add_argument("--models", default=",".join(MODELS), help="comma list (default: all)")
    p.add_argument("--precision", default=None, help="fp32,fp16 (default: fp32,fp16; fp32 below CC 7.0)")
    p.add_argument("--runs", type=int, default=20, help="timed runs for the median (default 20)")
    p.add_argument("--timeout", type=float, default=900, help="seconds for each L4 child (default 900)")
    p.add_argument("--out", type=Path, default=None, help="report folder (default: a new temp folder)")
    p.add_argument("--work", type=Path, default=default_work(), help="envs, models, uv cache (kept)")
    p.add_argument("--redact-check", action="store_true", help="scan the report for the user and host name")
    p.add_argument("--plan-only", action="store_true", help="print the plan and stop")
    args = p.parse_args(argv)
    for name, known in (("routes", ROUTES), ("models", MODELS)):
        bad = set(getattr(args, name).split(",")) - set(known)
        if bad:
            p.error(f"unknown {name}: {sorted(bad)}")
    return args


def plan(args, gpu) -> tuple[dict, dict]:
    sc, osk = scenario(gpu), os_key()
    force = args.include_unexpected or sc["name"] in ("A", "B")
    routes = {}
    for route in args.routes.split(","):
        pred = predict(route, gpu, osk)
        rec = routes[route] = {"predicted": pred, "ran": True}
        if pred["verdict"] in ("ok", "experimental"):
            rec["run_reason"] = "predicted to work"
        elif force:
            rec["run_reason"] = "predicted to fail: record how it fails"
        else:
            rec["ran"] = False
            rec["skip_reason"] = f"predicted {pred['verdict']}; use --include-unexpected"
    return sc, routes


def run_main(argv: list[str]) -> int:
    args = parse_run(argv)
    started = time.time()
    gpu, nvml = detect_gpu()
    cc = gpu["cc"] if gpu else "9.9"
    precisions = (args.precision or ("fp32,fp16" if cc_tuple(cc) >= (7, 0) else "fp32")).split(",")
    sc, routes = plan(args, gpu)
    print(f"GPU: {gpu['name']} CC {gpu['cc']} driver {gpu['driver_version']} "
          f"(max CUDA {gpu['cuda_driver_api']}) {gpu['vram_total_mb']} MB" if gpu else "GPU: no NVIDIA GPU")
    print(f"Scenario {sc['name']}: {sc['text']}")
    for a in anomalies(gpu):
        print(f"ANOMALY: {a}")
    for route, rec in routes.items():
        p = rec["predicted"]
        print(f"  {route:13} predicted {p['verdict']:14} {'run' if rec['ran'] else 'skip':4}  {p['reason']}")
    if args.plan_only:
        return 0
    work = args.work.resolve()
    (work / "assets").mkdir(parents=True, exist_ok=True)
    out = (args.out or Path(tempfile.mkdtemp(prefix="ep_device_checks-"))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    models = [] if args.quick else [m for m in MODELS if m in args.models.split(",")]
    ctx = {"args": args, "work": work, "assets": work / "assets", "gpu": gpu, "nvml": nvml,
           "models": models, "precisions": precisions, "model_paths": {}, "prep": {}}
    report = {"schema": 1, "suite": "ep_device_checks", "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
              "args": {"routes": args.routes.split(","), "quick": args.quick, "models": models,
                       "precisions": precisions, "runs": args.runs, "include_unexpected": args.include_unexpected},
              "host": host_facts(), "gpu": gpu, "scenario": sc, "anomalies": anomalies(gpu),
              "rules": {"RULES": RULES, "LAST_BRANCH": LAST_BRANCH}, "routes": routes}
    report["prep"] = prepare(ctx)
    for route, rec in routes.items():
        if rec["ran"]:
            try:
                check_route(ctx, route, rec)
            except Exception as exc:  # noqa: BLE001 - the suite records it and goes on
                rec.setdefault("install", {"ok": False})
                rec["suite_error"] = f"{type(exc).__name__}: {exc}"
        rec["observed"] = observed(rec) if "suite_error" not in rec else {"verdict": "error", "reason": rec["suite_error"]}
        rec["match"] = match(rec["predicted"]["verdict"], rec["observed"]["verdict"])
        rec["verdict_key"] = verdict_key(report, rec)
    report["findings"] = findings(report)
    report["disk_mb"] = {"uv_cache": disk_mb(Path(clean_env(work)["UV_CACHE_DIR"])), "envs": disk_mb(work / "envs"),
                         "models_and_assets": disk_mb(work / "models") + disk_mb(work / "assets"),
                         "work_total_hardlinks_once": disk_mb(work)}
    report["duration_s"] = round(time.time() - started)
    pairs = [(str(work), "<work>"), (str(SUITE), "<suite>"), *private_values()]
    report = sanitize(report, pairs)
    (out / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (out / "report.md").write_text(markdown(report), encoding="utf-8")
    print("\n" + markdown(report))
    print(f"Report folder: {out}")
    if args.redact_check:
        found = redact_findings((out / "report.json").read_text(encoding="utf-8")
                                + (out / "report.md").read_text(encoding="utf-8"))
        if found:
            print(f"REDACT CHECK FAILED: the report holds: {', '.join(found)}. Do not send it.")
            return 3
        print("Redact check: no user name, host name or user path in the report.")
    return 0


def prepare(ctx: dict) -> dict:
    """Fetch the models and the image, then run prep_assets.py in the prep environment."""
    work, assets, rec = ctx["work"], ctx["assets"], {"models": {}}
    for key in list(ctx["models"]):
        try:
            print(f"[prep] model {key} ...", flush=True)
            ctx["model_paths"][key] = get_model(work, key)
        except (OSError, ValueError) as exc:
            rec["models"][key] = {"error": f"download: {exc}"}
    image = assets / "image.jpg"
    try:
        if ctx["models"] and not (image.is_file() and file_sha256(image) == IMAGE["sha256"]):
            fetch(IMAGE["url"], IMAGE["sha256"], image)
    except (OSError, ValueError) as exc:
        rec["image_error"] = str(exc)
    print("[prep] install the prep environment ...", flush=True)
    rec["install"] = install(work, "prep", PREP_DEPS)
    python = rec["install"].pop("python")
    if not rec["install"]["ok"]:
        raise SystemExit(f"the prep environment failed: {rec['install']['reason']}")
    specs = [{"key": k, "onnx": str(p), **{f: MODELS[k][f] for f in ("kind", "size")}}
             for k, p in ctx["model_paths"].items() if "image_error" not in rec]
    job = {"folder": str(assets), "image": str(image), "models": specs, "fp16": "fp16" in ctx["precisions"]}
    (assets / "prep_job.json").write_text(json.dumps(job), encoding="utf-8")
    print("[prep] probe, inputs, CPU references, fp16 copies ...", flush=True)
    proc = subprocess.run([python, "-I", "-B", str(SUITE / "prep_assets.py"), str(assets / "prep_job.json")],  # noqa: S603
                          capture_output=True, text=True, timeout=3600, env=clean_env(work))
    if proc.returncode:
        raise SystemExit("prep_assets.py failed:\n" + tail(proc.stderr, 20))
    done = json.loads((assets / "prep_result.json").read_text(encoding="utf-8"))
    done["models"] = {**rec["models"], **done["models"]}
    done["install"] = rec["install"]
    ctx["prep"] = done
    return done


# ------------------------------------------------------------------------------------ compare
def compare_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="run_checks.py compare", description="Compare reports of one GPU.")
    p.add_argument("reports", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    if len(args.reports) < 2:
        p.error("give two or more reports")
    reports = sorted((json.loads(r.read_text(encoding="utf-8")) for r in args.reports), key=lambda r: r["created"])
    ids = {((r["gpu"] or {}).get("pci"), (r["gpu"] or {}).get("name")) for r in reports}
    if len(ids) > 1:
        print(f"The reports are from different GPUs: {sorted(map(str, ids))}")
        return 2
    result = {"gpu": reports[0]["gpu"], "steps": []}
    for before, after in zip(reports, reports[1:], strict=False):
        result["steps"].append(compare_pair(before, after))
    out = (args.out or Path(tempfile.mkdtemp(prefix="ep_device_checks-compare-"))).resolve()
    out.mkdir(parents=True, exist_ok=True)
    text = compare_markdown(result)
    (out / "compare.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    (out / "compare.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"Compare folder: {out}")
    return 0


def describe(rec: dict | None) -> dict:
    if not rec:
        return {"observed": "absent", "predicted": "absent", "key": None}
    return {"observed": rec["observed"]["verdict"], "predicted": rec["predicted"]["verdict"],
            "target_branch": rec["predicted"].get("target_branch"), "key": rec["verdict_key"]["hash"],
            "key_fields": rec["verdict_key"]["fields"]}


def compare_pair(before: dict, after: dict) -> dict:
    branch_after = (after["gpu"] or {}).get("driver_branch", 0)
    step = {"from": {"created": before["created"], "driver": (before["gpu"] or {}).get("driver_version"),
                     "scenario": before["scenario"]["name"]},
            "to": {"created": after["created"], "driver": (after["gpu"] or {}).get("driver_version"),
                   "scenario": after["scenario"]["name"]}, "routes": {}}
    for route in sorted(set(before["routes"]) | set(after["routes"])):
        b, a = describe(before["routes"].get(route)), describe(after["routes"].get(route))
        changed_fields = sorted(k for k in set(b.get("key_fields") or {}) | set(a.get("key_fields") or {})
                                if (b.get("key_fields") or {}).get(k) != (a.get("key_fields") or {}).get(k))
        ok_before, ok_after = b["observed"] in ("pass", "partial"), a["observed"] in ("pass", "partial")
        if b["predicted"] == "update-driver" and branch_after >= (b["target_branch"] or 0):
            outcome = ("as predicted: the driver update fixed it" if ok_after else
                       "NOT as predicted: the driver reached the target branch, but the route still fails"
                       if a["observed"] == "fail" else f"not checked: observed {a['observed']}")
        elif ok_before != ok_after and "not-run" not in (b["observed"], a["observed"]):
            outcome = f"changed with no prediction: {b['observed']} to {a['observed']}"
        else:
            outcome = "no change" if b["observed"] == a["observed"] else f"{b['observed']} to {a['observed']}"
        step["routes"][route] = {"before": {k: v for k, v in b.items() if k != "key_fields"},
                                 "after": {k: v for k, v in a.items() if k != "key_fields"},
                                 "outcome": outcome, "verdict_key_changed": b["key"] != a["key"],
                                 "key_fields_changed": changed_fields}
    return step


def compare_markdown(result: dict) -> str:
    gpu = result["gpu"] or {}
    lines = ["# EP device checks: compare", "", f"GPU: {gpu.get('name')}, CC {gpu.get('cc')}, PCI {gpu.get('pci')}"]
    for step in result["steps"]:
        f, t = step["from"], step["to"]
        lines += ["", f"## Driver {f['driver']} (scenario {f['scenario']}) to {t['driver']} (scenario {t['scenario']})",
                  "", "| Route | Before (predicted / observed) | After (predicted / observed) | Outcome |"
                  " Verdict key changed (re-verify) |", "|---|---|---|---|---|"]
        for route, r in step["routes"].items():
            b, a = r["before"], r["after"]
            key = f"yes ({', '.join(r['key_fields_changed'])})" if r["verdict_key_changed"] else "no"
            lines.append(f"| {route} | {b['predicted']} / {b['observed']} | {a['predicted']} / {a['observed']} | "
                         f"{r['outcome']} | {key} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "compare":
        return compare_main(argv[1:])
    return run_main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
