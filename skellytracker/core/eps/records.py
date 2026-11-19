"""The records of `core.eps`.

Each record is frozen and has no `dict` field, so it hashes, pickles and converts to JSON with
`dataclasses.asdict`. Memory is `int` bytes and time is `int` ns. No text of a record holds an
absolute path, except `EpStatus.store_root`, which is for local output only.
"""

from dataclasses import dataclass
from typing import Literal

from skellytracker.core.system.records import HostInfo

Options = tuple[tuple[str, str], ...]
PackState = Literal["builtin", "ready", "installed_unverified", "untested-ort", "not_ready", "stale", "not_installed", "unsupported",
                    "field_test"]  # `field_test`: a `field-test` EP with no opt-in in the EP store (ADR-Z5X7)
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
    """The result of one verification of one EP. `level` is the highest level that ran.

    `exit_reason_code` is `hung-at-exit` or `crashed` when the child process gave its result and then did
    not exit cleanly. The result stays. Else it is None.
    """

    ep_key: str
    level: Literal["L2", "L3"]
    ok: bool
    key: str
    pack_id: str | None = None
    pack_version: str | None = None
    reason: str | None = None
    max_abs_diff: float | None = None
    exit_reason_code: str | None = None


@dataclass(frozen=True)
class SessionReport:
    """What a session of `build_session()` runs on. `cpu_nodes` and `cpu_op_types` are a stable contract.

    `cpu_threads` is the intra-op thread count of a session on the built-in CPU EP `cpu`, and None
    for each other EP.
    """

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
    cpu_threads: int | None = None


@dataclass(frozen=True)
class CertifyOffer:
    """One usable EP of this host that the project has not certified on this GPU model and this OS.

    `seconds` is the time of the wider run, for the question to the user. `prompt` is true when an
    application asks the user now: no certification ran here for the pair, and the user did not
    answer "do not ask again".
    """

    ep_key: str
    label: str
    device_key: str
    gpu_name: str | None = None
    seconds: int = 0
    prompt: bool = True


@dataclass(frozen=True)
class CertifyResult:
    """The result of `certify()`. `report_path` is an absolute path, for local output only.

    `ok` is true when the probe passes and the wider run, if it ran, passes. `wide_ok` is None when
    the wider run did not run. `reason_code` is a fixed code, never a free text.
    """

    ep_key: str
    ok: bool
    probe_ok: bool
    wide_ok: bool | None = None
    reason_code: str | None = None
    report_path: str = ""
    report_json: str = ""


@dataclass(frozen=True)
class PackStatus:
    """The state of one EP key on this host, for `status()`. An application shows an EP from these fields only.

    - `usable`: true when a run can use the EP now. An application does not compare `state`.
    - `install_hint`: the text with the command that installs or repairs the pack. It is None when
      the EP is usable, and when an install does not help: `reason` then gives the cause.
    - `uses_gpu`: true when the EP runs a model on a GPU.
    - `description`: one sentence for a user: what the EP runs on and what it needs.
    - `devices`: the GPUs of this host that the EP can use, in the order of `run_devices(key)`: the
      most VRAM first. It is empty for a built-in EP that runs on no GPU and for an EP that is not usable.
    - `catalog_status`: `ready`, or `field-test` for an EP in a field test (ADR-Z5X7). With no opt-in
      in the EP store, the `state` of a `field-test` EP is `field_test`, and `install_hint` is None:
      an application can show the EP as "available for a field test", but it never offers it.
    - `certified`: true when the project has a reviewed pass of the EP on this GPU model on this OS.
      It is None for a built-in EP and when no GPU of this host can use the EP.
    - `source`: where the EP comes from: the index of the pack (`pypi`, `azure` or `amd`),
      `windows-ml` for an EP of the Windows ML catalog, or `builtin` (ADR-XSE7).
    """

    key: str
    label: str
    state: PackState
    source: Literal["pypi", "azure", "amd", "windows-ml", "builtin"] = "builtin"
    catalog_status: str = "ready"
    reason_code: str | None = None
    reason: str | None = None
    download_bytes: int = 0
    disk_bytes: int = 0
    pack_id: str | None = None
    pack_version: str | None = None
    exclusive_group: str | None = None
    licences: tuple[tuple[str, str], ...] = ()
    usable: bool = False
    install_hint: str | None = None
    uses_gpu: bool = False
    description: str = ""
    devices: tuple[RunDevice, ...] = ()
    certified: bool | None = None


@dataclass(frozen=True)
class EpStatus:
    """The result of `status()`. It needs no `onnxruntime` import and no network.

    `eps` has one row for each EP key of this platform, in the order of the EP catalog: `trt-rtx`,
    `cuda`, `coreml`, `amdgpu`, `migraphx`, `directml`, `cpu`. This order is a contract. It is the order of preference: each hardware
    class of the catalog lists its candidates in this order. It is not the recommendation:
    `performance.chosen` and `accuracy.chosen` give the recommended EP of this host.
    """

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
    certify_offers: tuple[CertifyOffer, ...] = ()


@dataclass(frozen=True)
class SelftestResult:
    """The result of `selftest()`. `steps` holds `(name, ok, detail)`."""

    ok: bool
    steps: tuple[tuple[str, bool, str], ...] = ()
