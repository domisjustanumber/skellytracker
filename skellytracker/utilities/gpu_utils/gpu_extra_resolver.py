"""Hardware-based execution provider and pyproject extra recommendations."""

from __future__ import annotations

import re
import sys
from typing import Literal

from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo, gpus_for_ep_recommendation

CatalogProviderId = Literal["trt-trx", "trt", "cuda", "coreml", "directml", "cpu"]

RtmposeExtra = Literal["rtmpose", "rtmpose-nvidia", "rtmpose-trt-rtx", "rtmpose-directml"]

_RTX_PRODUCT_RE = re.compile(r"\bRTX\s*\d", re.IGNORECASE)

_EXTRA_FOR_EP: dict[CatalogProviderId, RtmposeExtra] = {
  "trt-trx": "rtmpose-trt-rtx",
  "trt": "rtmpose-nvidia",
  "cuda": "rtmpose-nvidia",
  "directml": "rtmpose-directml",
  "coreml": "rtmpose",
  "cpu": "rtmpose",
}


def recommend_optimal_execution_provider(gpus: list[GpuInfo]) -> CatalogProviderId:
  """Best EP id for detected hardware — independent of installed ORT packages."""
  if sys.platform == "darwin":
    return "coreml"

  active_gpus = gpus_for_ep_recommendation(gpus)
  if not active_gpus:
    return "cpu"

  nvidia_gpus = [g for g in active_gpus if g.vendor == "nvidia"]
  if nvidia_gpus:
    for gpu in nvidia_gpus:
      if _RTX_PRODUCT_RE.search(gpu.name):
        return "trt-trx"
    return "cuda"

  if sys.platform == "win32":
    if any(g.vendor in ("amd", "intel") for g in active_gpus):
      return "directml"

  return "cpu"


def recommend_rtmpose_extra(gpus: list[GpuInfo]) -> RtmposeExtra:
  return _EXTRA_FOR_EP[recommend_optimal_execution_provider(gpus)]
