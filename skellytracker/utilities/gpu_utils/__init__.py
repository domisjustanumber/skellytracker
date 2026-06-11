"""GPU utilities: enumeration, execution providers, and model catalog."""

from skellytracker.utilities.gpu_utils.execution_provider_catalog import (
  ExecutionProviderCapabilities,
  ExecutionProviderInfo,
  ExecutionProvidersInfo,
  list_execution_providers,
  recommend_execution_provider,
)
from skellytracker.utilities.gpu_utils.gpu_enumeration import GpuInfo, list_installed_gpus
from skellytracker.utilities.gpu_utils.gpu_extra_resolver import (
  CatalogProviderId,
  recommend_optimal_execution_provider,
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
  resolve_provider,
)

__all__ = [
  "CatalogProviderId",
  "ExecutionProviderCapabilities",
  "ExecutionProviderInfo",
  "ExecutionProviderName",
  "ExecutionProvidersInfo",
  "GpuInfo",
  "MODEL_CATALOG",
  "MODEL_REGISTRY",
  "ModelCatalogEntry",
  "PoseModelInfo",
  "list_detection_models",
  "list_execution_providers",
  "list_installed_gpus",
  "list_pose_models",
  "recommend_execution_provider",
  "recommend_optimal_execution_provider",
  "resolve_provider",
]
