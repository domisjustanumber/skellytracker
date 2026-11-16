"""The spec loader: the loader and the typed model of a sidecar at the current spec version.

`load_sidecar(path, sidecar_root)` is the entry point. It takes the sidecar root as an argument.
"""
from skellytracker.core.model_spec.errors import (
    Failure,
    SidecarError,
    SidecarParseError,
    SidecarRefError,
    SidecarSchemaVersionError,
    SidecarValidationError,
)
from skellytracker.core.model_spec.landmark_schemas import (
    PACKAGE_SIDECAR_ROOT,
    LandmarkSchema,
    load_landmark_schema_registry,
)
from skellytracker.core.model_spec.loader import load_sidecar
from skellytracker.core.model_spec.model import SidecarModel, SizeSpec
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition
from skellytracker.core.model_spec.rules import check_sidecar
from skellytracker.core.model_spec.versioning import IMPLEMENTED_SCHEMA_VERSIONS

__all__ = [
    "IMPLEMENTED_SCHEMA_VERSIONS",
    "PACKAGE_SIDECAR_ROOT",
    "Failure",
    "LandmarkSchema",
    "SidecarError",
    "SidecarModel",
    "SidecarParseError",
    "SidecarRefError",
    "SidecarSchemaVersionError",
    "SidecarValidationError",
    "SizeSpec",
    "check_sidecar",
    "load_landmark_schema_registry",
    "load_sidecar",
    "resolve_sidecar_composition",
]
