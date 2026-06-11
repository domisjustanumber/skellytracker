"""OS-native GPU enumeration without ONNX Runtime.

Uses ``nvidia-smi`` when available for NVIDIA GPUs (accurate VRAM, driver, CUDA max).
Falls back to OS backends (WMI / DRM / system_profiler) for other vendors and when
``nvidia-smi`` is absent. Best-effort: failures log a warning rather than raising.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import (
  CudaVersion,
  cuda_version_ge,
  max_nvidia_driver_cuda_required,
)

logger = logging.getLogger(__name__)

GpuVendor = Literal["nvidia", "intel", "amd", "apple", "unknown"]

_VIRTUAL_NAME_PATTERNS = re.compile(
    r"microsoft basic|remote|virtual|indirect display|parsec|meta virtual|mirror|idd|software adapter",
    re.IGNORECASE,
)

_CUDA_HEADER_RE = re.compile(r"CUDA Version\s*:\s*(\d+)\.(\d+)", re.IGNORECASE)

_PCI_VENDOR_NVIDIA = 0x10DE
_PCI_VENDOR_INTEL = 0x8086
_PCI_VENDOR_AMD = 0x1002
_PCI_VENDOR_APPLE = 0x106B

_FOUR_GIB = 4 * 1024 * 1024 * 1024
_MIB = 1024 * 1024


@dataclass(frozen=True)
class GpuInfo:
  id: str
  name: str
  vendor: GpuVendor
  vram_bytes: int | None
  online: bool = True
  driver_version: str | None = None
  cuda_driver_max: CudaVersion | None = None
  cuda_required_min: CudaVersion | None = None
  cuda_meets_nvidia_eps: bool | None = None


@runtime_checkable
class GpuBackend(Protocol):
  def enumerate_gpus(self) -> list[GpuInfo]: ...


def list_installed_gpus() -> list[GpuInfo]:
  backend = _backend_for_platform()
  os_gpus = _filter_virtual_adapters(backend.enumerate_gpus())
  nvidia_gpus = _enumerate_nvidia_smi_gpus()
  if not nvidia_gpus:
    return os_gpus
  non_nvidia = [gpu for gpu in os_gpus if gpu.vendor != "nvidia"]
  return non_nvidia + nvidia_gpus


def gpus_for_ep_recommendation(gpus: list[GpuInfo]) -> list[GpuInfo]:
  """Online GPUs only — offline adapters are listed but ignored for EP selection."""
  return [gpu for gpu in gpus if gpu.online]


def driver_cuda_max_from_gpus(gpus: list[GpuInfo]) -> CudaVersion | None:
  """Driver-reported max CUDA from the first NVIDIA GPU enumerated via nvidia-smi."""
  for gpu in gpus:
    if gpu.vendor == "nvidia" and gpu.cuda_driver_max is not None:
      return gpu.cuda_driver_max
  return None


def _backend_for_platform() -> GpuBackend:
  if sys.platform == "win32":
    return WindowsWmiGpuBackend()
  if sys.platform == "darwin":
    return MacSystemProfilerGpuBackend()
  return LinuxDrmGpuBackend()


def _filter_virtual_adapters(gpus: list[GpuInfo]) -> list[GpuInfo]:
  filtered: list[GpuInfo] = []
  for gpu in gpus:
    if _VIRTUAL_NAME_PATTERNS.search(gpu.name):
      continue
    filtered.append(gpu)
  return filtered


def _nvidia_smi_path() -> str | None:
  return shutil.which("nvidia-smi")


def _parse_cuda_driver_max(smi_stdout: str) -> CudaVersion | None:
  for line in smi_stdout.splitlines():
    match = _CUDA_HEADER_RE.search(line)
    if match:
      return (int(match.group(1)), int(match.group(2)))
  return None


def _run_nvidia_smi(args: list[str], *, timeout: float = 30) -> subprocess.CompletedProcess[str] | None:
  smi = _nvidia_smi_path()
  if smi is None:
    return None
  try:
    return subprocess.run(  # noqa: S603
      [smi, *args],
      capture_output=True,
      text=True,
      check=False,
      timeout=timeout,
    )
  except (OSError, subprocess.TimeoutExpired) as exc:
    logger.warning("nvidia-smi failed: %s", exc)
    return None


def _enumerate_nvidia_smi_gpus() -> list[GpuInfo]:
  header_result = _run_nvidia_smi([])
  if header_result is None:
    return []
  if header_result.returncode != 0:
    logger.warning(
      "nvidia-smi returned rc=%s: %s",
      header_result.returncode,
      header_result.stderr.strip(),
    )
    return []

  cuda_driver_max = _parse_cuda_driver_max(header_result.stdout)
  cuda_required_min = max_nvidia_driver_cuda_required()
  cuda_meets = (
    cuda_version_ge(cuda_driver_max, cuda_required_min)
    if cuda_driver_max is not None and cuda_required_min is not None
    else None
  )

  query_result = _run_nvidia_smi([
    "--query-gpu=index,name,memory.total,driver_version",
    "--format=csv,noheader,nounits",
  ])
  if query_result is None or query_result.returncode != 0 or not query_result.stdout.strip():
    logger.warning(
      "nvidia-smi GPU query failed (rc=%s): %s",
      None if query_result is None else query_result.returncode,
      "" if query_result is None else query_result.stderr.strip(),
    )
    return []

  gpus: list[GpuInfo] = []
  reader = csv.reader(io.StringIO(query_result.stdout.strip()))
  for row in reader:
    if len(row) < 4:
      continue
    index_str, name, memory_mib_str, driver_version = (field.strip() for field in row[:4])
    try:
      index = int(index_str)
      memory_mib = int(float(memory_mib_str))
    except ValueError:
      logger.warning("nvidia-smi row parse failed: %r", row)
      continue
    gpus.append(
      GpuInfo(
        id=f"nvidia:{index}",
        name=name,
        vendor="nvidia",
        vram_bytes=memory_mib * _MIB,
        driver_version=driver_version or None,
        cuda_driver_max=cuda_driver_max,
        cuda_required_min=cuda_required_min,
        cuda_meets_nvidia_eps=cuda_meets,
      )
    )
  return gpus


def _vendor_from_pci_id(vendor_hex: int) -> GpuVendor:
  if vendor_hex == _PCI_VENDOR_NVIDIA:
    return "nvidia"
  if vendor_hex == _PCI_VENDOR_INTEL:
    return "intel"
  if vendor_hex == _PCI_VENDOR_AMD:
    return "amd"
  if vendor_hex == _PCI_VENDOR_APPLE:
    return "apple"
  return "unknown"


def _vendor_from_name(name: str) -> GpuVendor:
  upper = name.upper()
  if "NVIDIA" in upper or "GEFORCE" in upper or "QUADRO" in upper:
    return "nvidia"
  if "INTEL" in upper:
    return "intel"
  if "AMD" in upper or "RADEON" in upper:
    return "amd"
  if "APPLE" in upper:
    return "apple"
  return "unknown"


def _vendor_from_pnp_device_id(pnp_id: str) -> GpuVendor:
  upper = pnp_id.upper()
  if "VEN_10DE" in upper:
    return "nvidia"
  if "VEN_8086" in upper:
    return "intel"
  if "VEN_1002" in upper:
    return "amd"
  return _vendor_from_name(pnp_id)


def _wmi_adapter_online(availability: int | None) -> bool:
  """WMI Win32_VideoController Availability 3 = Running / Full Power."""
  return availability is None or availability == 3


def _parse_wmi_vram(adapter_ram: int | None, name: str) -> int | None:
  if adapter_ram is None or adapter_ram <= 0:
    return None
  vendor = _vendor_from_name(name)
  if adapter_ram >= _FOUR_GIB - 1 and vendor in ("nvidia", "amd"):
    return None
  return adapter_ram


class WindowsWmiGpuBackend:
  def enumerate_gpus(self) -> list[GpuInfo]:
    script = (
      "Get-CimInstance Win32_VideoController | "
      "Select-Object Name, AdapterRAM, PNPDeviceID, Availability | "
      "ConvertTo-Json -Compress"
    )
    try:
      result = subprocess.run(  # noqa: S603
        ["powershell", "-NoProfile", "-Command", script],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
      )
    except (OSError, subprocess.TimeoutExpired) as exc:
      logger.warning("Windows GPU enumeration failed: %s", exc)
      return []

    if result.returncode != 0 or not result.stdout.strip():
      logger.warning(
        "Windows GPU enumeration returned no data (rc=%s): %s",
        result.returncode,
        result.stderr.strip(),
      )
      return []

    try:
      payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
      logger.warning("Windows GPU enumeration JSON parse failed: %s", exc)
      return []

    rows = payload if isinstance(payload, list) else [payload]
    gpus: list[GpuInfo] = []
    for index, row in enumerate(rows):
      if not isinstance(row, dict):
        continue
      availability = row.get("Availability")
      availability_int = int(availability) if availability is not None else None
      name = str(row.get("Name") or f"GPU {index}")
      pnp_id = str(row.get("PNPDeviceID") or "")
      adapter_ram = row.get("AdapterRAM")
      ram_int = int(adapter_ram) if adapter_ram is not None else None
      gpus.append(
        GpuInfo(
          id=f"win32:{index}",
          name=name,
          vendor=_vendor_from_pnp_device_id(pnp_id) if pnp_id else _vendor_from_name(name),
          vram_bytes=_parse_wmi_vram(ram_int, name),
          online=_wmi_adapter_online(availability_int),
        )
      )
    return gpus


class LinuxDrmGpuBackend:
  def enumerate_gpus(self) -> list[GpuInfo]:
    drm_root = Path("/sys/class/drm")
    if not drm_root.is_dir():
      return []

    gpus: list[GpuInfo] = []
    for card_dir in sorted(drm_root.glob("card[0-9]*")):
      if not card_dir.is_dir():
        continue
      card_name = card_dir.name
      if "Virtual" in card_name:
        continue
      device_dir = card_dir / "device"
      vendor_path = device_dir / "vendor"
      if not vendor_path.is_file():
        continue
      device_path = str(device_dir)
      if "virtio" in device_path or "vgem" in device_path:
        continue
      try:
        vendor_hex = int(vendor_path.read_text().strip(), 16)
      except (OSError, ValueError):
        continue

      name = card_name
      uevent_path = device_dir / "uevent"
      if uevent_path.is_file():
        for line in uevent_path.read_text().splitlines():
          if line.startswith("PCI_ID="):
            pci_id = line.split("=", 1)[1]
            name = pci_id
            break

      vram_bytes: int | None = None
      for vram_key in ("mem_info_vram_total", "mem_info_vis_vram_total"):
        vram_path = device_dir / vram_key
        if vram_path.is_file():
          try:
            vram_bytes = int(vram_path.read_text().strip())
          except (OSError, ValueError):
            vram_bytes = None
          break

      gpus.append(
        GpuInfo(
          id=f"drm:{card_name}",
          name=name,
          vendor=_vendor_from_pci_id(vendor_hex),
          vram_bytes=vram_bytes,
        )
      )
    return gpus


class MacSystemProfilerGpuBackend:
  def enumerate_gpus(self) -> list[GpuInfo]:
    try:
      result = subprocess.run(  # noqa: S603
        ["system_profiler", "SPDisplaysDataType", "-json"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
      )
    except (OSError, subprocess.TimeoutExpired) as exc:
      logger.warning("macOS GPU enumeration failed: %s", exc)
      return []

    if result.returncode != 0 or not result.stdout.strip():
      logger.warning("macOS GPU enumeration returned no data")
      return []

    try:
      payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
      logger.warning("macOS GPU enumeration JSON parse failed: %s", exc)
      return []

    displays = payload.get("SPDisplaysDataType", [])
    gpus: list[GpuInfo] = []
    for index, item in enumerate(displays):
      if not isinstance(item, dict):
        continue
      for sub in item.get("_items", []):
        if not isinstance(sub, dict):
          continue
        name = str(sub.get("sppci_model") or sub.get("_name") or f"GPU {index}")
        vram = sub.get("sppci_vram")
        if vram is None:
          vram = sub.get("vram_shared")
        vram_bytes: int | None
        if isinstance(vram, (int, float)):
          vram_bytes = int(vram)
        elif isinstance(vram, str):
          match = re.search(r"(\d+)", vram.replace(",", ""))
          vram_bytes = int(match.group(1)) * (1024 * 1024) if match else None
        else:
          vram_bytes = None
        gpus.append(
          GpuInfo(
            id=f"mac:{len(gpus)}",
            name=name,
            vendor="apple" if "apple" in name.lower() else _vendor_from_name(name),
            vram_bytes=vram_bytes,
          )
        )
    return gpus
