"""GPU utilities: enumeration, execution providers, and model catalog."""

from skellytracker.utilities.gpu_utils.execution_provider_catalog import (
  ExecutionProviderCapabilities,
  ExecutionProviderInfo,
  ExecutionProvidersInfo,
  list_execution_providers,
  recommend_execution_provider,
)
from skellytracker.utilities.gpu_utils.gpu_enumeration import (
  GpuInfo,
  driver_cuda_max_from_gpus,
  gpus_for_ep_recommendation,
  list_installed_gpus,
)
from skellytracker.utilities.gpu_utils.pyproject_cuda_requirements import (
  CudaVersion,
  cuda_version_ge,
  min_driver_cuda_for_ep,
  min_driver_cuda_for_extra,
  nvidia_driver_cuda_compatible,
)
from skellytracker.utilities.gpu_utils.gpu_extra_resolver import (
  CatalogProviderId,
  RtmposeExtra,
  recommend_optimal_execution_provider,
  recommend_rtmpose_extra,
)
from skellytracker.utilities.gpu_utils.model_registry import (
  MODEL_CATALOG,
  MODEL_REGISTRY,
  ModelCatalogEntry,
  PoseModelInfo,
  list_detection_models,
  list_pose_models,
)
from skellytracker.utilities.gpu_utils.ort_session_utils import (
  ExecutionProviderName,
  OnnxExecutionProviderStartupError,
  resolve_provider,
)

__all__ = [
  "CatalogProviderId",
  "CudaVersion",
  "ExecutionProviderCapabilities",
  "ExecutionProviderInfo",
  "ExecutionProviderName",
  "OnnxExecutionProviderStartupError",
  "ExecutionProvidersInfo",
  "GpuInfo",
  "cuda_version_ge",
  "driver_cuda_max_from_gpus",
  "gpus_for_ep_recommendation",
  "min_driver_cuda_for_ep",
  "min_driver_cuda_for_extra",
  "nvidia_driver_cuda_compatible",
  "MODEL_CATALOG",
  "MODEL_REGISTRY",
  "ModelCatalogEntry",
  "PoseModelInfo",
  "RtmposeExtra",
  "list_detection_models",
  "list_execution_providers",
  "list_installed_gpus",
  "list_pose_models",
  "recommend_execution_provider",
  "recommend_optimal_execution_provider",
  "recommend_rtmpose_extra",
  "resolve_provider",
]
