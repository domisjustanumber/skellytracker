"""Execution provider introspection for skellytracker.

``list_execution_providers()`` may initialize GPU runtime libraries via
``prepare_ort_providers_for_probe()`` — not a pure read of installed packages.

Capability flags are best-effort hints derived from ORT ``get_ep_devices()`` when
available (ORT >= 1.22). Plugin EPs such as TRT-RTX are registered dynamically and
may appear only in ``get_ep_devices()``, not ``get_available_providers()``;
``prepare_ort_providers_for_probe()`` merges both sources.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

import onnxruntime as ort

from skellytracker.utilities.gpu_utils.gpu_enumeration import (
  driver_cuda_max_from_gpus,
  list_installed_gpus,
)
from skellytracker.utilities.gpu_utils.gpu_extra_resolver import (
  CatalogProviderId,
  recommend_optimal_execution_provider,
)
from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import (
  nvidia_driver_cuda_compatible,
)
from skellytracker.utilities.gpu_utils.ort_session_utils import (
  ExecutionProviderName,
  TRT_RTX_ORT_PROVIDER_NAME,
  prepare_ort_providers_for_probe,
  resolve_provider,
)

_FIXED_BATCH_PATTERNS = (
  "profile_min_shapes",
  "profile_max_shapes",
  "profile_opt_shapes",
  "nv_profile_min_shapes",
  "nv_profile_max_shapes",
  "nv_profile_opt_shapes",
  "RequireStaticInputShapes",
  "only_allow_static",
  "disable_dynamic_shapes",
  "fixed_batch",
  "static_batch",
  "static_input",
)

_DOWNCAST_PATTERNS = (
  "fp16_enable",
  "bf16_enable",
  "AllowLowPrecisionAccumulationOnGPU",
  "precision",
)

_QUANTIZE_PATTERNS = (
  "int8_enable",
  "qdq",
  "quantization",
  "enable_qdq_optimizer",
)

_CATALOG_ENTRIES: tuple[dict[str, Any], ...] = (
  {
    "id": "trt-trx",
    "display_name": "TensorRT RTX",
    "ort_name": TRT_RTX_ORT_PROVIDER_NAME,
    "platforms": frozenset({"win32", "linux"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/TensorRTRTX-ExecutionProvider.html",
  },
  {
    "id": "trt",
    "display_name": "TensorRT",
    "ort_name": "TensorrtExecutionProvider",
    "platforms": frozenset({"win32", "linux"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html",
  },
  {
    "id": "cuda",
    "display_name": "CUDA",
    "ort_name": "CUDAExecutionProvider",
    "platforms": frozenset({"win32", "linux"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html",
  },
  {
    "id": "directml",
    "display_name": "DirectML",
    "ort_name": "DmlExecutionProvider",
    "platforms": frozenset({"win32"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html",
  },
  {
    "id": "coreml",
    "display_name": "CoreML",
    "ort_name": "CoreMLExecutionProvider",
    "platforms": frozenset({"darwin"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html",
  },
  {
    "id": "cpu",
    "display_name": "CPU",
    "ort_name": "CPUExecutionProvider",
    "platforms": frozenset({"win32", "linux", "darwin"}),
    "doc_url": "https://onnxruntime.ai/docs/execution-providers/CPU-ExecutionProvider.html",
  },
)


@dataclass(frozen=True)
class ExecutionProviderCapabilities:
  fixed_batch_sizes: bool
  downcasting: bool
  quantization: bool


@dataclass(frozen=True)
class ExecutionProviderInfo:
  id: str
  display_name: str
  available: bool
  recommended: bool
  optimal: bool
  install_recommended: bool
  capabilities: ExecutionProviderCapabilities
  doc_url: str
  driver_cuda_compatible: bool | None = None


@dataclass(frozen=True)
class ExecutionProvidersInfo:
  providers: tuple[ExecutionProviderInfo, ...]
  recommended_provider_id: str | None
  optimal_provider_id: str | None
  install_recommended_provider_id: str | None


def recommend_execution_provider(
  available_ort: set[str] | None = None,
) -> ExecutionProviderName:
  """Public alias for ``resolve_provider(requested=None)``."""
  if available_ort is None:
    available_ort = prepare_ort_providers_for_probe()
  return resolve_provider(requested=None, available_ort=available_ort)


def list_execution_providers() -> ExecutionProvidersInfo:
  """Enumerate execution providers with installed-best and GPU-optimal signals."""
  available_ort = prepare_ort_providers_for_probe()
  ep_devices = ort.get_ep_devices() if hasattr(ort, "get_ep_devices") else []
  gpus = list_installed_gpus()
  driver_cuda_max = driver_cuda_max_from_gpus(gpus)
  optimal_id = recommend_optimal_execution_provider(gpus)
  installed_best_id = resolve_provider(requested=None, available_ort=available_ort)
  optimal_available = _catalog_entry_available(optimal_id, available_ort)
  optimal_driver_ok = nvidia_driver_cuda_compatible(driver_cuda_max, optimal_id)
  if optimal_driver_ok is False:
    optimal_available = False

  recommended_id: CatalogProviderId = installed_best_id  # type: ignore[assignment]
  install_recommended_id: CatalogProviderId | None
  if optimal_available:
    install_recommended_id = None
  else:
    install_recommended_id = optimal_id

  providers: list[ExecutionProviderInfo] = []
  for entry in _CATALOG_ENTRIES:
    provider_id: CatalogProviderId = entry["id"]
    ort_name = entry["ort_name"]
    on_platform = sys.platform in entry["platforms"]
    available = on_platform and ort_name in available_ort
    capabilities = (
      _probe_ep_capabilities(ort_name, ep_devices)
      if available
      else ExecutionProviderCapabilities(False, False, False)
    )
    providers.append(
      ExecutionProviderInfo(
        id=provider_id,
        display_name=entry["display_name"],
        available=available,
        recommended=provider_id == recommended_id,
        optimal=provider_id == optimal_id,
        install_recommended=provider_id == install_recommended_id,
        capabilities=capabilities,
        doc_url=entry["doc_url"],
        driver_cuda_compatible=nvidia_driver_cuda_compatible(driver_cuda_max, provider_id),
      )
    )

  return ExecutionProvidersInfo(
    providers=tuple(providers),
    recommended_provider_id=recommended_id,
    optimal_provider_id=optimal_id,
    install_recommended_provider_id=install_recommended_id,
  )


def _catalog_entry_available(provider_id: CatalogProviderId, available_ort: set[str]) -> bool:
  for entry in _CATALOG_ENTRIES:
    if entry["id"] == provider_id:
      return sys.platform in entry["platforms"] and entry["ort_name"] in available_ort
  return False


def _any_key_matches(keys: set[str], patterns: tuple[str, ...]) -> bool:
  for key in keys:
    for pattern in patterns:
      if pattern in key:
        return True
  return False


def _find_ep_device(ep_devices: list[Any], ort_provider_name: str) -> Any | None:
  for device in ep_devices:
    ep_name = getattr(device, "ep_name", None) or getattr(device, "name", None)
    if ep_name == ort_provider_name:
      return device
  return None


def _probe_ep_capabilities(
  ort_provider_name: str,
  ep_devices: list[Any],
) -> ExecutionProviderCapabilities:
  device = _find_ep_device(ep_devices, ort_provider_name)
  if device is None:
    return ExecutionProviderCapabilities(False, False, False)

  ep_options = getattr(device, "ep_options", None) or {}
  option_keys = set(ep_options.keys())
  return ExecutionProviderCapabilities(
    fixed_batch_sizes=_any_key_matches(option_keys, _FIXED_BATCH_PATTERNS),
    downcasting=_any_key_matches(option_keys, _DOWNCAST_PATTERNS),
    quantization=_any_key_matches(option_keys, _QUANTIZE_PATTERNS),
  )
