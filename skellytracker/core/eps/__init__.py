"""Execution providers: the EP catalog, the EP store, the session build and the recommendation.

A plain `import skellytracker.core.eps` loads no `onnxruntime`. No environment variable selects
the EP or the device: the caller passes a concrete EP key as `execution_provider`.

An application, for example freemocap, holds no fact about an EP. It shows the EPs from `status()`
and takes its recommended and automatic choices from `recommend()`:

- `EpStatus.eps` has one `PackStatus` for each EP key of this platform, in the order of the EP
  catalog: `trt-rtx`, `cuda`, `coreml`, `cpu`. The order is a contract.
- `PackStatus.usable` is true when a run can use the EP now. An application does not compare
  `PackStatus.state` with a list of states.
- `PackStatus.install_hint` is the text with the command that installs or repairs the pack, or None.
- `PackStatus.uses_gpu` is true when the EP runs a model on a GPU.
- `PackStatus.description` is one sentence for a user, from `description` of the EP catalog.
- `PackStatus.devices` holds the GPUs of this host that the EP can use, as `RunDevice` records, in
  the order of `run_devices(key)`. `status()` still loads no library and uses no network.
- `suggest_execution_provider(saved_execution_provider)` gives the EP key to use on this host for an
  EP key that a setting of an older release holds, or None. The key is an EP that this host
  supports. It can need an install first: `PackStatus.usable` and `PackStatus.install_hint` of the
  key tell the application. An application calls it only for such a setting. On None, the
  application uses the recommendation.
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
from skellytracker.core.eps.self_test import selftest
from skellytracker.core.eps.session import build_session
from skellytracker.core.eps.state import check_start, status, suggest_execution_provider
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
    "check_start",
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
    "selftest",
    "status",
    "store_root",
    "suggest_execution_provider",
    "verify",
]
