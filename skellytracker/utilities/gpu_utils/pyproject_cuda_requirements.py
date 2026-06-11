"""Derive minimum NVIDIA driver CUDA versions from pyproject optional-dependencies."""

from __future__ import annotations

import functools
import re
import tomllib

from skellytracker.utilities.gpu_utils.pyproject_paths import find_skellytracker_project_root

_CU_SUFFIX_RE = re.compile(r"-cu(\d+)\b")

# pyproject extra that installs wheels for each NVIDIA catalog EP
_NVIDIA_EP_INSTALL_EXTRA: dict[str, str] = {
  "cuda": "rtmpose-nvidia",
  "trt": "rtmpose-trt",
  "trt-trx": "rtmpose-trt-rtx",
}

CudaVersion = tuple[int, int]


def cuda_version_ge(driver_max: CudaVersion, required_min: CudaVersion) -> bool:
  """True when *driver_max* supports at least *required_min* CUDA major.minor."""
  if driver_max[0] != required_min[0]:
    return driver_max[0] > required_min[0]
  return driver_max[1] >= required_min[1]


def cuda_majors_from_dep_spec(spec: str) -> list[int]:
  """Extract CUDA major from a dependency name suffix such as ``-cu12``."""
  name = spec.split("[")[0].split("==")[0].split(">=")[0].split("~=")[0].strip()
  match = _CU_SUFFIX_RE.search(name)
  return [int(match.group(1))] if match else []


@functools.lru_cache(maxsize=1)
def load_optional_dependencies() -> dict[str, list[str]] | None:
  """Load ``[project.optional-dependencies]`` from the skellytracker pyproject.toml."""
  root = find_skellytracker_project_root()
  if root is None:
    return None
  pyproject = root / "pyproject.toml"
  try:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
  except (OSError, tomllib.TOMLDecodeError):
    return None
  optional = data.get("project", {}).get("optional-dependencies")
  if not isinstance(optional, dict):
    return None
  return optional


def min_driver_cuda_for_extra(extra: str) -> CudaVersion | None:
  """Minimum driver CUDA version for a pyproject extra (from ``-cuNN`` deps)."""
  optional = load_optional_dependencies()
  if optional is None:
    return None
  majors: list[int] = []
  deps = optional.get(extra, [])
  if not isinstance(deps, list):
    return None
  for spec in deps:
    if isinstance(spec, str):
      majors.extend(cuda_majors_from_dep_spec(spec))
  if not majors:
    return None
  return (max(majors), 0)


def min_driver_cuda_for_ep(ep_id: str) -> CudaVersion | None:
  """Minimum driver CUDA for a catalog NVIDIA execution provider."""
  extra = _NVIDIA_EP_INSTALL_EXTRA.get(ep_id)
  if extra is None:
    return None
  return min_driver_cuda_for_extra(extra)


def max_nvidia_driver_cuda_required() -> CudaVersion | None:
  """Highest driver CUDA requirement across all NVIDIA install extras."""
  majors: list[int] = []
  for extra in _NVIDIA_EP_INSTALL_EXTRA.values():
    required = min_driver_cuda_for_extra(extra)
    if required is not None:
      majors.append(required[0])
  if not majors:
    return None
  return (max(majors), 0)


def nvidia_driver_cuda_compatible(
  driver_max: CudaVersion | None,
  ep_id: str,
) -> bool | None:
  """Whether *driver_max* meets the pyproject CUDA requirement for *ep_id*."""
  if ep_id not in _NVIDIA_EP_INSTALL_EXTRA:
    return None
  required = min_driver_cuda_for_ep(ep_id)
  if driver_max is None or required is None:
    return None
  return cuda_version_ge(driver_max, required)
