"""Linux readers: `/proc`, `/sys`, `pci.ids`, the container markers and one `systemd-detect-virt --vm` call.

Each function takes `root`, so a test gives a folder of fake files. psutil is not used on Linux.
"""

import ctypes
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from skellytracker.core._hardware import pci
from skellytracker.core.system.records import ContainerInfo, GpuInfo, NvidiaContainerInfo, VirtualizationInfo

ROOT = Path("/")
PCI_IDS = ("usr/share/hwdata/pci.ids", "usr/share/misc/pci.ids")  # the database that `lspci` reads


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _hex(path: Path) -> int | None:
    text = _read(path)
    try:
        return None if text is None else int(text, 16)
    except ValueError:
        return None


def cpu_name(root: Path = ROOT) -> str | None:
    match = re.search(r"^model name\s*:\s*(.+)$", _read(root / "proc/cpuinfo") or "", re.MULTILINE)
    return match.group(1).strip() if match else None


def cpu_max_frequency_hz(root: Path = ROOT) -> int | None:
    """`cpuinfo_max_freq` of CPU 0, from kHz to Hz; `None` with no `cpufreq` folder. No test ran it on Linux."""
    text = _read(root / "sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq") or ""
    return int(text) * 1000 if text.isdigit() and int(text) > 0 else None


def cores_and_memory(root: Path = ROOT) -> tuple[int | None, int | None, int]:
    cpuinfo = _read(root / "proc/cpuinfo") or ""
    cores = set()
    for block in cpuinfo.split("\n\n"):
        fields = dict(re.findall(r"^(physical id|core id)\s*:\s*(\d+)$", block, re.MULTILINE))
        if len(fields) == 2:
            cores.add((fields["physical id"], fields["core id"]))
    match = re.search(r"^MemTotal:\s*(\d+) kB$", _read(root / "proc/meminfo") or "", re.MULTILINE)
    return len(cores) or None, os.cpu_count(), int(match.group(1)) * 1024 if match else 0


# --- integrated or dedicated: the fact that the kernel driver states (ADR-8N03 item 7) ---
# Each constant is from a uapi header of the Linux kernel at the tag v6.12, and is the same at v6.18.
DRM_TIMEOUT_S = 2.0
_DRM_MACHINES = ("x86_64", "aarch64", "riscv64")  # the ioctl encoding of asm-generic/ioctl.h; powerpc has an other one


def _drm_request(direction: int, number: int, size: int) -> int:
    """`_IOC(direction, 'd', DRM_COMMAND_BASE + number, size)`: drm.h `DRM_IOCTL_BASE 'd'` and `DRM_COMMAND_BASE 0x40`."""
    return (direction << 30) | (size << 16) | (ord("d") << 8) | (0x40 + number)


AMDGPU_INFO = _drm_request(1, 0x05, 32)  # amdgpu_drm.h: DRM_IOW(DRM_COMMAND_BASE + DRM_AMDGPU_INFO, struct drm_amdgpu_info)
I915_QUERY = _drm_request(3, 0x39, 16)  # i915_drm.h: DRM_IOWR(DRM_COMMAND_BASE + DRM_I915_QUERY, struct drm_i915_query)
XE_DEVICE_QUERY = _drm_request(3, 0x00, 40)  # xe_drm.h: DRM_IOWR(DRM_COMMAND_BASE + DRM_XE_DEVICE_QUERY, struct drm_xe_device_query)
_QUERY_LIMIT = 65536  # no answer of these queries is longer


class _AmdgpuInfo(ctypes.Structure):  # struct drm_amdgpu_info, 32 bytes
    _fields_ = (("return_pointer", ctypes.c_uint64), ("return_size", ctypes.c_uint32), ("query", ctypes.c_uint32),
                ("rest", ctypes.c_uint32 * 4))


class _I915Item(ctypes.Structure):  # struct drm_i915_query_item, 24 bytes
    _fields_ = (("query_id", ctypes.c_uint64), ("length", ctypes.c_int32), ("flags", ctypes.c_uint32), ("data_ptr", ctypes.c_uint64))


class _I915Query(ctypes.Structure):  # struct drm_i915_query, 16 bytes
    _fields_ = (("num_items", ctypes.c_uint32), ("flags", ctypes.c_uint32), ("items_ptr", ctypes.c_uint64))


class _XeQuery(ctypes.Structure):  # struct drm_xe_device_query, 40 bytes
    _fields_ = (("extensions", ctypes.c_uint64), ("query", ctypes.c_uint32), ("size", ctypes.c_uint32), ("data", ctypes.c_uint64),
                ("reserved", ctypes.c_uint64 * 2))


def _drm_ioctl(node: Path, request: int, argument, keep: tuple = ()) -> bool:
    """One ioctl on a render node. False on each error, and when the call does not return in `DRM_TIMEOUT_S`.

    The call runs in a daemon thread: an open of a GPU that resumes cannot be interrupted. The thread holds `argument`
    and `keep`, the buffers that the kernel writes, so a late answer writes into live memory.
    """
    done = []

    def call() -> None:
        try:
            import fcntl

            handle = os.open(node, os.O_RDWR | os.O_CLOEXEC)
            try:
                fcntl.ioctl(handle, request, argument)
            finally:
                os.close(handle)
            done.append(keep)
        except (OSError, ImportError, AttributeError):
            pass

    thread = threading.Thread(target=call, daemon=True)
    thread.start()
    thread.join(DRM_TIMEOUT_S)
    return bool(done)


def integrated(device: Path, driver: str | None, root: Path = ROOT, ioctl=_drm_ioctl) -> bool | None:
    """True for a GPU that shares the system memory, False for a GPU with its own memory, None when no driver states it.

    - `amdgpu`: the kernel hides the file `board_info` on an APU (`amdgpu_board_attrs_is_visible`, kernel 6.7 or later),
      so the file means False. Else the bit `AMDGPU_IDS_FLAGS_FUSION` (0x1) of `ids_flags` of `AMDGPU_INFO_DEV_INFO` (0x16).
    - `i915`: `DRM_I915_QUERY_MEMORY_REGIONS` (4). A region of `I915_MEMORY_CLASS_DEVICE` (1) means False.
    - `xe`: `DRM_XE_DEVICE_QUERY_CONFIG` (2). `DRM_XE_QUERY_CONFIG_FLAG_HAS_VRAM` (bit 0 of `info[1]`) means False.
    - Each other driver, also `nvidia`: None. The driver of NVIDIA states it only through a CUDA call.

    An ioctl opens the render node, and that resumes a GPU that sleeps. So a GPU with the `runtime_status`
    `suspended` or `suspending` gives None. No test ran the ioctl paths on Linux hardware.
    """
    if driver == "amdgpu" and (device / "board_info").exists():
        return False
    if driver not in ("amdgpu", "i915", "xe") or platform.machine() not in _DRM_MACHINES:
        return None
    if _read(device / "power/runtime_status") in ("suspended", "suspending"):
        return None
    nodes = sorted((device / "drm").glob("renderD*"))
    if len(nodes) != 1:
        return None
    node = root / "dev/dri" / nodes[0].name
    if driver == "amdgpu":
        info = (ctypes.c_uint64 * 18)()  # struct drm_amdgpu_info_device to `ids_flags`, the __u64 at offset 136
        request = _AmdgpuInfo(ctypes.addressof(info), ctypes.sizeof(info), 0x16)
        return bool(info[17] & 0x1) if ioctl(node, AMDGPU_INFO, request, (info,)) else None
    if driver == "i915":
        item = _I915Item(4, 0, 0, 0)  # with the length 0, the kernel writes the length of the answer
        query = _I915Query(1, 0, ctypes.addressof(item))
        if not ioctl(node, I915_QUERY, query, (item,)) or not 16 <= item.length <= _QUERY_LIMIT:
            return None
        data = (ctypes.c_uint8 * item.length)()
        item.data_ptr = ctypes.addressof(data)
        if not ioctl(node, I915_QUERY, query, (item, data)) or item.length < 16:
            return None
        raw = bytes(data)  # struct drm_i915_query_memory_regions: __u32 num_regions, 12 bytes, then regions of 88 bytes
        count = min(int.from_bytes(raw[:4], sys.byteorder), (len(raw) - 16) // 88)
        classes = [int.from_bytes(raw[16 + 88 * index:18 + 88 * index], sys.byteorder) for index in range(count)]
        return 1 not in classes if classes else None
    query = _XeQuery(0, 2, 0, 0)  # with the size 0, the kernel writes the size of the answer
    if not ioctl(node, XE_DEVICE_QUERY, query, ()) or not 24 <= query.size <= _QUERY_LIMIT:
        return None
    data = (ctypes.c_uint8 * query.size)()
    query.data = ctypes.addressof(data)
    if not ioctl(node, XE_DEVICE_QUERY, query, (data,)):
        return None
    raw = bytes(data)  # struct drm_xe_query_config: __u32 num_params, __u32 pad, then __u64 info[]
    if int.from_bytes(raw[:4], sys.byteorder) < 2:
        return None
    return not int.from_bytes(raw[16:24], sys.byteorder) & 0x1


def gpus(root: Path = ROOT, ioctl=_drm_ioctl) -> list[GpuInfo]:
    """The GPUs of `/sys/class/drm`. `name` is the amdgpu `product_name`, else the device name of `pci.ids`.

    The function reads the first `pci.ids` file that exists one time. No test ran it on Linux.
    """
    result, pci_ids = {}, None
    for card in sorted((root / "sys/class/drm").glob("card*")):
        device = card / "device"
        if "-" in card.name or not (device / "vendor").exists():
            continue  # card0-HDMI-A-1 is a connector, not a GPU
        uevent = dict(line.split("=", 1) for line in (_read(device / "uevent") or "").splitlines() if "=" in line)
        bus = pci.normalize_bus_id(uevent.get("PCI_SLOT_NAME", ""))
        vendor_id, device_id = _hex(device / "vendor"), _hex(device / "device")
        name = _read(device / "product_name")
        if not name and vendor_id is not None and device_id is not None:
            if pci_ids is None:
                pci_ids = next((text for text in (_read(root / path) for path in PCI_IDS) if text is not None), "")
            name = pci.device_name(pci_ids, vendor_id, device_id)
        driver = uevent.get("DRIVER")
        vram = _read(device / "mem_info_vram_total")  # amdgpu only
        gpu = GpuInfo(
            key=bus or f"drm:{card.name}", vendor=pci.vendor_of(vendor_id), name=name or None,
            pci_bus_id=bus, pci_vendor_id=vendor_id, pci_device_id=device_id,
            pci_subsys_id=_hex(device / "subsystem_device"),
            is_integrated=integrated(device, driver, root, ioctl),
            driver_version=_read(root / "sys/module" / driver / "version") if driver else None,
            vram_total_bytes=int(vram) if vram and vram.isdigit() else None,
        )
        result[gpu.key] = gpu
    return list(result.values())


def virtualization(root: Path = ROOT, detect_virt: bool = True) -> VirtualizationInfo:
    is_wsl = "microsoft" in (_read(root / "proc/sys/kernel/osrelease") or "").lower()
    tool = shutil.which("systemd-detect-virt") if detect_virt else None
    if tool:
        try:
            run = subprocess.run([tool, "--vm"], capture_output=True, text=True, timeout=5, check=False)  # noqa: S603
            name = run.stdout.strip()
            if name:
                return VirtualizationInfo(is_wsl=is_wsl, is_vm=name != "none", hypervisor=None if name == "none" else name)
        except (OSError, subprocess.SubprocessError):
            pass
    cpuinfo = _read(root / "proc/cpuinfo")
    if cpuinfo is None:
        return VirtualizationInfo(is_wsl=is_wsl)
    is_vm = bool(re.search(r"^flags\s*:.*\bhypervisor\b", cpuinfo, re.MULTILINE))
    return VirtualizationInfo(is_wsl=is_wsl, is_vm=is_vm, hypervisor="unknown" if is_vm else None)


def container(root: Path = ROOT, environ=os.environ) -> ContainerInfo | None:
    cgroup = _read(root / "proc/1/cgroup") or ""
    if (root / "run/.containerenv").exists():
        runtime = "podman"
    elif (root / ".dockerenv").exists() or "docker" in cgroup:
        runtime = "docker"
    elif "containerd" in cgroup or "kubepods" in cgroup:
        runtime = "containerd"
    elif "lxc" in cgroup:
        runtime = "lxc"
    else:
        return None
    quota, limit = None, None
    cpu_max = (_read(root / "sys/fs/cgroup/cpu.max") or "").split()
    if len(cpu_max) == 2 and cpu_max[0].isdigit() and int(cpu_max[1]) > 0:
        quota = round(int(cpu_max[0]) / int(cpu_max[1]), 3)
    memory_max = _read(root / "sys/fs/cgroup/memory.max") or ""
    if memory_max.isdigit():
        limit = int(memory_max)
    release = re.search(r'^PRETTY_NAME="?([^"\n]+)', _read(root / "etc/os-release") or "", re.MULTILINE)
    nvidia = None
    if "NVIDIA_VISIBLE_DEVICES" in environ:
        nvidia = NvidiaContainerInfo(environ.get("NVIDIA_VISIBLE_DEVICES"), environ.get("NVIDIA_DRIVER_CAPABILITIES"),
                                     environ.get("CUDA_VERSION"))
    return ContainerInfo(runtime=runtime, base_os=release.group(1) if release else None,
                         cpuset=_read(root / "sys/fs/cgroup/cpuset.cpus.effective"), cpu_quota_cores=quota,
                         memory_limit_bytes=limit, nvidia=nvidia)


def memory(root: Path = ROOT) -> tuple[int, int]:
    """The total and the available memory in bytes: `MemAvailable`, else `MemFree`."""
    values = dict(re.findall(r"^(\w+):\s*(\d+) kB$", (root / "proc/meminfo").read_text(encoding="utf-8"), re.MULTILINE))
    return int(values["MemTotal"]) * 1024, int(values.get("MemAvailable", values["MemFree"])) * 1024


def cpu_times(root: Path = ROOT) -> tuple[float, float]:
    """The busy and the total CPU seconds of all logical CPUs since the start of the system."""
    ticks = [int(value) for value in (root / "proc/stat").read_text(encoding="utf-8").splitlines()[0].split()[1:9]]
    total = sum(ticks) / os.sysconf("SC_CLK_TCK")
    return total - (ticks[3] + ticks[4]) / os.sysconf("SC_CLK_TCK"), total  # idle and iowait are not busy


def process(pid: int, root: Path = ROOT) -> tuple[float, float, int]:
    """The identity, the CPU seconds and the RSS bytes of a process. A process that ended or a zombie raises `ProcessLookupError`."""
    try:
        fields = (root / f"proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
        pages = int((root / f"proc/{pid}/statm").read_text(encoding="utf-8").split()[1])
    except FileNotFoundError as error:
        raise ProcessLookupError(pid) from error
    if fields[0] == "Z":
        raise ProcessLookupError(pid)
    tick = os.sysconf("SC_CLK_TCK")  # fields[11] and [12] are utime and stime; fields[19] is starttime
    return float(fields[19]), (int(fields[11]) + int(fields[12])) / tick, pages * os.sysconf("SC_PAGE_SIZE")
