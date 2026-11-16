"""The records of `core.eps`.

Each record is frozen and has no `dict` field, so it hashes, pickles and converts to JSON with
`dataclasses.asdict`. Memory is `int` bytes and time is `int` ns. No text of a record holds an
absolute path, except `EpStatus.store_root`, which is for local output only.
"""

from dataclasses import dataclass
from typing import Literal

from skellytracker.core.system.records import HostInfo

Options = tuple[tuple[str, str], ...]
PackState = Literal["builtin", "ready", "installed_unverified", "untested-ort", "not_ready", "stale", "not_installed", "unsupported"]
USABLE_STATES = ("builtin", "ready", "installed_unverified", "untested-ort")


@dataclass(frozen=True)
class ModelRef:
    """The model facts that the caller reads from the sidecar. `eps` reads no sidecar."""

    family: str
    artifact_sha256: str | None = None
    precisions: tuple[str, ...] = ()
    batch: int | None = None


@dataclass(frozen=True)
class RunDevice:
    """One GPU that an EP can use in a run."""

    device_key: str
    gpu_key: str
    name: str | None = None
    pci_bus_id: str | None = None
    vram_total_bytes: int | None = None


@dataclass(frozen=True)
class EpCandidate:
    """One EP of a hardware class, with the state of its pack. A state in `USABLE_STATES` is ready."""

    ep_key: str
    ep_name: str
    status: PackState
    pack_id: str | None = None
    device_key: str | None = None
    precision_order: tuple[str, ...] = ("fp32",)
    reason: str | None = None


@dataclass(frozen=True)
class InstallOffer:
    kind: Literal["add-pack", "update-driver", "none-available"]
    ep_key: str | None = None
    pack_id: str | None = None
    download_bytes: int | None = None
    disk_bytes: int | None = None
    licence_url: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class RecommendationSource:
    """Where a recommendation comes from. `ranking_evidence` is an entry ID, `single-ep` or `None` (not measured)."""

    catalog_revision: str
    row_id: str
    ranking_evidence: str | None = None
    kind: Literal["hardware-table"] = "hardware-table"


@dataclass(frozen=True)
class EpRecommendation:
    """The result of `recommend()`: a concrete EP key with its options. `skipped` names each candidate before it."""

    form: Literal["performance", "accuracy"]
    hardware_class: str
    chosen: EpCandidate
    precision: str
    source: RecommendationSource
    options: Options = ()
    skipped: tuple[EpCandidate, ...] = ()
    offers: tuple[InstallOffer, ...] = ()


@dataclass(frozen=True)
class WheelRef:
    package: str
    version: str
    filename: str
    url: str
    sha256: str
    download_bytes: int
    unpacked_bytes: int


@dataclass(frozen=True)
class PlannedPack:
    ep_key: str
    pack_id: str
    version: str
    wheels: tuple[WheelRef, ...]
    download_bytes: int
    disk_bytes: int
    licence_name: str | None = None
    licence_url: str | None = None


@dataclass(frozen=True)
class InstallPlan:
    """The result of `plan_install()`. Each pack shows a plain licence link. There is no accept step."""

    packs: tuple[PlannedPack, ...] = ()
    download_bytes: int = 0
    disk_bytes: int = 0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstallProgress:
    key: str
    phase: Literal["download", "hash", "unpack", "register", "verify"]
    bytes_done: int = 0
    bytes_total: int = 0


@dataclass(frozen=True)
class InstallResult:
    """The result of `install()`. `failed` holds `(key, error_code, message)`."""

    ok: tuple[str, ...] = ()
    failed: tuple[tuple[str, str, str], ...] = ()
    cancelled: tuple[str, ...] = ()
    needs_worker_restart: bool = False


@dataclass(frozen=True)
class GcResult:
    removed_packs: tuple[str, ...] = ()
    removed_refs: tuple[str, ...] = ()
    removed_partials: int = 0
    deferred: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisteredEp:
    ep_key: str
    ep_name: str
    pack_id: str | None = None
    pack_version: str | None = None
    library: str | None = None


@dataclass(frozen=True)
class Verdict:
    """The result of one verification of one EP. `level` is the highest level that ran."""

    ep_key: str
    level: Literal["L2", "L3"]
    ok: bool
    key: str
    pack_id: str | None = None
    pack_version: str | None = None
    reason: str | None = None
    max_abs_diff: float | None = None


@dataclass(frozen=True)
class SessionReport:
    """What a session of `build_session()` runs on. `cpu_nodes` and `cpu_op_types` are a stable contract."""

    requested_ep: str
    used_ep: str | None
    ep_name: str
    ort_version: str
    catalog_revision: str
    device_kind: Literal["cpu", "gpu", "npu", "soc"] = "cpu"
    pack_id: str | None = None
    pack_version: str | None = None
    device_key: str | None = None
    device_name: str | None = None
    gpu_uuid: str | None = None
    gpu_key: str | None = None
    ep_device_id: str | None = None
    ep_options: Options = ()
    precision: str | None = None
    artifact_sha256: str | None = None
    nodes_by_ep: tuple[tuple[str, int], ...] = ()
    cpu_nodes: int = 0
    cpu_op_types: tuple[str, ...] = ()
    build_ns: int = 0
    warmup_ns: int = 0


@dataclass(frozen=True)
class PackStatus:
    """The state of one EP key on this host, for `status()`."""

    key: str
    label: str
    state: PackState
    source: Literal["pypi", "azure", "builtin"] = "builtin"
    catalog_status: str = "ready"
    reason_code: str | None = None
    reason: str | None = None
    download_bytes: int = 0
    disk_bytes: int = 0
    pack_id: str | None = None
    pack_version: str | None = None
    exclusive_group: str | None = None
    licences: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class EpStatus:
    """The result of `status()`. It needs no `onnxruntime` import and no network."""

    ort_version: str | None
    catalog_revision: str
    core_matches_pin: bool
    platform_tag: str
    store_root: str
    store_free_bytes: int | None
    host: HostInfo
    performance: EpRecommendation
    accuracy: EpRecommendation
    eps: tuple[PackStatus, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelftestResult:
    """The result of `selftest()`. `steps` holds `(name, ok, detail)`."""

    ok: bool
    steps: tuple[tuple[str, bool, str], ...] = ()
