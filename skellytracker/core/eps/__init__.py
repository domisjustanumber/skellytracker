"""Execution providers: the EP catalog, the EP store, the session build and the recommendation.

A plain `import skellytracker.core.eps` loads no `onnxruntime`. No environment variable selects
the EP or the device: the caller passes a concrete EP key as `execution_provider`.
"""

from skellytracker.core.eps.catalog import EpCatalog, load_catalog
from skellytracker.core.eps.installer import download, gc, install, plan_install, remove
from skellytracker.core.eps.recommendation import recommend, run_devices, select_precision
from skellytracker.core.eps.records import (
    EpCandidate,
    EpRecommendation,
    EpStatus,
    GcResult,
    InstallOffer,
    InstallPlan,
    InstallProgress,
    InstallResult,
    ModelRef,
    PackStatus,
    PlannedPack,
    RecommendationSource,
    RegisteredEp,
    RunDevice,
    SelftestResult,
    SessionReport,
    Verdict,
    WheelRef,
)
from skellytracker.core.eps.registration import ensure_registered
from skellytracker.core.eps.session import build_session
from skellytracker.core.eps.store import store_root
from skellytracker.core.eps.verification import verify

__all__ = [
    "EpCandidate",
    "EpCatalog",
    "EpRecommendation",
    "EpStatus",
    "GcResult",
    "InstallOffer",
    "InstallPlan",
    "InstallProgress",
    "InstallResult",
    "ModelRef",
    "PackStatus",
    "PlannedPack",
    "RecommendationSource",
    "RegisteredEp",
    "RunDevice",
    "SelftestResult",
    "SessionReport",
    "Verdict",
    "WheelRef",
    "build_session",
    "download",
    "ensure_registered",
    "gc",
    "install",
    "load_catalog",
    "plan_install",
    "recommend",
    "remove",
    "run_devices",
    "select_precision",
    "store_root",
    "verify",
]
