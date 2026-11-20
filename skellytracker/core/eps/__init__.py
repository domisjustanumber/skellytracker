"""Execution providers: the EP catalog, the EP store, the session build and the recommendation.

A plain `import skellytracker.core.eps` loads no `onnxruntime`. No environment variable selects
the EP or the device: the caller passes a concrete EP key as `execution_provider`.

An application, for example freemocap, holds no fact about an EP. It shows the EPs from `status()`
and takes its recommended and automatic choices from `recommend()`:

- `EpStatus.eps` has one `PackStatus` for each EP key of this platform, in the order of the EP
  catalog: `trt-rtx`, `cuda`, `coreml`, `amdgpu`, `migraphx`, `directml`, `cpu`. The order is a
  contract. A platform shows only its own EPs.
- A `field-test` EP (`PackStatus.catalog_status`, today `directml`, `amdgpu` and `migraphx`) is
  usable only after an explicit opt-in: `skellytracker-eps install KEY --field-test`, the certify
  suite or a passed quick check of `skellytracker.certify()` (ADR-21BK). Without the opt-in its `state` is `field_test`. `recommend()` never gives it (ADR-Z5X7).
- `migraphx` is a pack for the ROCm release of the host on Linux, and an EP of the Windows ML
  catalog on Windows. `amdgpu` is an EP of the Windows ML catalog on Windows only. Windows installs
  the package of a Windows ML EP: `PackStatus.source` is `windows-ml` (ADR-XSE7).
- `install(plan_install([key]), progress=..., cancel=...)` is the one install call for a pack EP
  and for a Windows ML EP (`InstallPlan.windows_ml_keys`). For a Windows ML EP, `InstallProgress`
  has `fraction` from Windows ML and no bytes, and a cancel asks Windows ML to stop the install.
  `remove(execution_provider=key)` removes the Windows ML package of the key only when this EP
  store installed it, and never a package that was on the PC before. It returns `RemoveResult`.
- `PackStatus.usable` is true when a run can use the EP now. An application does not compare
  `PackStatus.state` with a list of states.
- `PackStatus.install_hint` is the text with the command that installs or repairs the pack, or None.
- `PackStatus.uses_gpu` is true when the EP runs a model on a GPU.
- `PackStatus.description` is one sentence for a user, from `description` of the EP catalog.
- `PackStatus.devices` holds the GPUs of this host that the EP can use, as `RunDevice` records, in
  the order of `run_devices(key)`. `status()` still loads no library and uses no network.
- `PackStatus.checks` holds one `DeviceCheck` for each GPU that passes the floors of the EP:
  `certified`, `local_result` (`passed`, `failed` or None, from the quick check of
  `skellytracker.certify()` on this PC) and `usable`. An EP with no reviewed row is usable on a GPU
  only after the whole quick check passes there, and never after a quick check that failed there
  (ADR-21BK items 2 and 3). An application offers an EP on a GPU from `checks[n].usable`.
- The check rule (`gate.py`, ADR-ER5X): `check_start()` and `build_session()` raise
  `EpUnavailableError` with the quick-check command for an EP on a GPU that the rule does not let
  run. `PackStatus.usable` and `PackStatus.devices` obey the rule. `recommend()` names only an EP
  that can start now: it skips a candidate with `failed_locally` or `needs_check`. The rule has no
  setting. Only the certification code runs with the rule off.
- `suggest_execution_provider(saved_execution_provider)` gives the EP key to use on this host for an
  EP key that a setting of an older release holds, or None. The key is an EP that this host
  supports. It can need an install first: `PackStatus.usable` and `PackStatus.install_hint` of the
  key tell the application. An application calls it only for such a setting. On None, the
  application uses the recommendation.
- `PackStatus.certified` is true when the project has a reviewed pass of the EP on this GPU model
  on this OS. An application tests an EP with `skellytracker.certify_plan("quick")` and
  `skellytracker.certify("quick")`, with the EP and the GPU as options (ADR-X7WD item 9). Nothing
  leaves the host.
"""

from skellytracker.core.eps.catalog import EpCatalog, load_catalog
from skellytracker.core.eps.installer import download, gc, install, plan_install, remove
from skellytracker.core.eps.recommendation import recommend, run_devices, select_precision
from skellytracker.core.eps.records import (
    DeviceCheck,
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
    RemoveResult,
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
    "DeviceCheck",
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
    "RemoveResult",
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
