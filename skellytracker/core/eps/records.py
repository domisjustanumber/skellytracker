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
ComponentState = Literal["installed", "missing", "other_version"]  # no state blocks the EP (ADR-88ZB)


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
class DeviceCheck:
    """The certification state of one EP on one GPU of this host (ADR-21BK items 2 and 3).

    - `certified`: the project has a reviewed pass of the EP on this GPU model on this OS, for the version set of this release.
    - `local_result`: `passed` or `failed`, the last quick check of `skellytracker.certify()` of the EP on
      this GPU model on this PC, for the pack version of today. It is None with no such check.
    - `usable`: a run can use the EP on this GPU now: the EP is ready, no quick check failed here, and
      the EP is certified or passed a quick check here. An application offers the GPU from this field.
    - `local_cause`: `unclean-exits` when `local_result` is `failed` because the process that used the EP
      ended two times in a row with no clean exit (ADR-ER5X item 5). Else None: a quick check gave the result.
    - `reason_code`: why a run cannot use the EP on this GPU now, or None when `usable`. It is the reason code of
      the state of the EP when the EP is not ready, for example `not-installed`. Else it is the code of the check
      rule: `quick-check-needed`, `quick-check-failed` or `unclean-exits`.
    """

    device_key: str
    name: str | None = None
    certified: bool = False
    local_result: Literal["passed", "failed"] | None = None
    usable: bool = False
    local_cause: Literal["unclean-exits"] | None = None
    reason_code: str | None = None


@dataclass(frozen=True)
class EpCandidate:
    """One EP of a hardware class, with the state of its pack. A state in `USABLE_STATES` is ready.

    `failed_locally` is true when the last quick check of the EP on its GPU failed on this PC.
    `needs_check` is true when the EP has no reviewed row for the GPU and no quick check on this PC.
    A run does not start on such a candidate, and `recommend()` never chooses it.
    """

    ep_key: str
    ep_name: str
    status: PackState
    pack_id: str | None = None
    device_key: str | None = None
    precision_order: tuple[str, ...] = ("fp32",)
    reason: str | None = None
    failed_locally: bool = False
    needs_check: bool = False


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
    """The result of `plan_install()`. Each pack shows a plain licence link. There is no accept step.

    `windows_ml_keys` holds each EP key of the plan that comes from the Windows ML catalog. Windows downloads
    and installs its package, so the plan gives no bytes for it.
    """

    packs: tuple[PlannedPack, ...] = ()
    download_bytes: int = 0
    disk_bytes: int = 0
    warnings: tuple[str, ...] = ()
    windows_ml_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstallProgress:
    """One progress event of `install()`. `fraction` is the progress from 0 to 1 of the install of
    an EP of the Windows ML catalog, with no bytes (Windows ML gives 0 to 100). It is None for a pack, and before the first value of Windows ML."""

    key: str
    phase: Literal["download", "hash", "unpack", "register", "verify"]
    bytes_done: int = 0
    bytes_total: int = 0
    fraction: float | None = None


@dataclass(frozen=True)
class InstallResult:
    """The result of `install()`. `failed` holds `(key, error_code, message)`.

    `warnings` holds the failures of components in the same form. A component failure does not fail
    the install: the EP stays usable, and `PackStatus.jpeg_decoder` shows the missing component.
    """

    ok: tuple[str, ...] = ()
    failed: tuple[tuple[str, str, str], ...] = ()
    cancelled: tuple[str, ...] = ()
    needs_worker_restart: bool = False
    warnings: tuple[tuple[str, str, str], ...] = ()


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
    not exit cleanly. The result stays. Else it is None. `reason_code` is `timed-out`, `cancelled`,
    `crashed` or `no-result` when the child gave no result, with `exit_code` of the child; else both are None.
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
    reason_code: str | None = None
    exit_code: int | None = None


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
class PackStatus:
    """The state of one EP key on this host, for `status()`. An application shows an EP from these fields only.

    - `usable`: true when a run can use the EP now, on one GPU or more. An application does not compare
      `state`. An EP that is ready is not usable when the check rule lets it run on no GPU: `reason_code` is
      then `quick-check-needed`, `quick-check-failed` or `unclean-exits` (ADR-ER5X).
    - `install_hint`: the text with the command that installs or repairs the pack, or that runs the quick
      check. It is None when the EP is usable, and when no command helps: `reason` then gives the cause.
    - `uses_gpu`: true when the EP runs a model on a GPU.
    - `description`: one sentence for a user: what the EP runs on and what it needs.
    - `devices`: the GPUs of this host that a run of the EP can use now, in the order of
      `run_devices(key)`: the most VRAM first. It is empty for a built-in EP that runs on no GPU and for an
      EP that is not usable.
    - `catalog_status`: `ready`, or `field-test` for an EP in a field test (ADR-Z5X7). With no opt-in
      in the EP store, the `state` of a `field-test` EP is `field_test`, and `install_hint` is None:
      an application can show the EP as "available for a field test", but it never offers it.
    - `certified`: true when the project has a reviewed pass of the EP on this GPU model on this OS, for the version set of
      this release.
      It is None for a built-in EP and when no GPU of this host can use the EP.
    - `source`: where the EP comes from: the index of the pack (`pypi`, `azure` or `amd`),
      `windows-ml` for an EP of the Windows ML catalog, or `builtin` (ADR-XSE7).
    - `jpeg_decoder`: the state of the GPU JPEG decoder of the pack: `installed`, `missing` or
      `other_version` (from an older catalog). It is None for an EP with no GPU JPEG decoder. A
      decoder that is not installed does not block the EP: a run decodes on the CPU.
    - `jpeg_decoder_hint`: the text with the command that installs the decoder. It is None when
      `jpeg_decoder` is `installed` or None.
    - `download_bytes`: the download of the pack, plus the download of its component when the
      component is not installed. `disk_bytes`: the unpacked size of the pack and its component.
      `licences`: the licences of the pack and its component. Each EP that names a component
      counts it in its own row, so a sum over the EPs counts a shared component one time for each EP.
    - `checks`: one `DeviceCheck` for each GPU of this host that passes the floors of the EP, in the
      order of `run_devices(key)`, also when the EP is not installed. `checks[n].usable` gives the
      state of one GPU.
    - `installed`: true when the EP store holds the pack of the EP, or the record of an install of its Windows ML
      package that ended. False when it does not. None for an EP that needs no pack, for example `directml` and
      `cpu`. It does not depend on `state`: a `field-test` EP with no opt-in has the state `field_test`, and
      `installed` still tells an application if it offers the install or the removal.
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
    jpeg_decoder: ComponentState | None = None
    jpeg_decoder_hint: str | None = None
    checks: tuple[DeviceCheck, ...] = ()
    installed: bool | None = None


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


@dataclass(frozen=True)
class SelftestResult:
    """The result of `selftest()`. `steps` holds `(name, ok, detail)`."""

    ok: bool
    steps: tuple[tuple[str, bool, str], ...] = ()


@dataclass(frozen=True)
class RemoveResult:
    """The result of `remove(execution_provider=KEY)` for an EP of the Windows ML catalog. It is empty for a pack.

    `removed` holds the full name of each package that the call removed. `failed` holds `(package full
    name or None, reason code)`. `was_present` is true when the package was on the PC before the install of
    this EP store: the call never removes such a package.
    """

    removed: tuple[str, ...] = ()
    failed: tuple[tuple[str | None, str], ...] = ()
    was_present: bool = False
