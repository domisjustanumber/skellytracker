"""Hardware-based optimal execution provider recommendations."""

from __future__ import annotations

import re
import sys
from typing import Literal

from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo

CatalogProviderId = Literal["trt-trx", "trt", "cuda", "coreml", "directml", "cpu"]

_RTX_PRODUCT_RE = re.compile(r"\bRTX\s*\d", re.IGNORECASE)


def recommend_optimal_execution_provider(gpus: list[GpuInfo]) -> CatalogProviderId:
  """Best EP id for detected hardware — independent of installed ORT packages."""
  if sys.platform == "darwin":
    return "coreml"

  if not gpus:
    return "cpu"

  nvidia_gpus = [g for g in gpus if g.vendor == "nvidia"]
  if nvidia_gpus:
    for gpu in nvidia_gpus:
      if _RTX_PRODUCT_RE.search(gpu.name):
        return "trt-trx"
    return "cuda"

  if sys.platform == "win32":
    if any(g.vendor in ("amd", "intel") for g in gpus):
      return "directml"

  return "cpu"
