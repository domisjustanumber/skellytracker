"""Linux readers: `/proc`, `/sys`, the container markers and one `systemd-detect-virt --vm` call.

Each function takes `root`, so a test gives a folder of fake files. psutil is not used on Linux.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from skellytracker.core._hardware import pci
from skellytracker.core.system.records import ContainerInfo, GpuInfo, NvidiaContainerInfo, VirtualizationInfo

ROOT = Path("/")


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


def cores_and_memory(root: Path = ROOT) -> tuple[int | None, int | None, int]:
    cpuinfo = _read(root / "proc/cpuinfo") or ""
    cores = set()
    for block in cpuinfo.split("\n\n"):
        fields = dict(re.findall(r"^(physical id|core id)\s*:\s*(\d+)$", block, re.MULTILINE))
        if len(fields) == 2:
            cores.add((fields["physical id"], fields["core id"]))
    match = re.search(r"^MemTotal:\s*(\d+) kB$", _read(root / "proc/meminfo") or "", re.MULTILINE)
    return len(cores) or None, os.cpu_count(), int(match.group(1)) * 1024 if match else 0


def gpus(root: Path = ROOT) -> list[GpuInfo]:
    result = {}
    for card in sorted((root / "sys/class/drm").glob("card*")):
        device = card / "device"
        if "-" in card.name or not (device / "vendor").exists():
            continue  # card0-HDMI-A-1 is a connector, not a GPU
        uevent = dict(line.split("=", 1) for line in (_read(device / "uevent") or "").splitlines() if "=" in line)
        bus = pci.normalize_bus_id(uevent.get("PCI_SLOT_NAME", ""))
        vendor_id = _hex(device / "vendor")
        boot_vga = _read(device / "boot_vga")
        driver = uevent.get("DRIVER")
        vram = _read(device / "mem_info_vram_total")  # amdgpu only
        gpu = GpuInfo(
            key=bus or f"drm:{card.name}", vendor=pci.vendor_of(vendor_id), name=_read(device / "product_name"),
            pci_bus_id=bus, pci_vendor_id=vendor_id, pci_device_id=_hex(device / "device"),
            pci_subsys_id=_hex(device / "subsystem_device"),
            is_integrated=None if boot_vga is None else boot_vga == "1",  # heuristic: the boot GPU
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
