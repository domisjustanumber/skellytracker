"""`recommend()`, `select_precision()` and `run_devices()`.

No function here imports `onnxruntime`, loads a library or uses the network. The recommended EP
comes only from the hardware classes of the EP catalog. No benchmark runs on the host.
"""

from collections.abc import Collection, Sequence

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import gate, store
from skellytracker.core.eps.catalog import EpCatalog, driver_branch, load_catalog, version_tuple
from skellytracker.core.eps.records import (
    USABLE_STATES,
    EpCandidate,
    EpRecommendation,
    InstallOffer,
    RecommendationSource,
    RunDevice,
)
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import gpu_device_keys, probe_host
from skellytracker.core.system.records import GpuInfo, HostInfo


def install_hint(key: str) -> str:
    """The install command of an EP key. A `field-test` EP needs the opt-in option `--field-test` (ADR-Z5X7)."""
    flag = " --field-test" if load_catalog().ep_status(key) == "field-test" else ""
    return f"Run `skellytracker-eps install {key}{flag}`."


def _by_vram(keyed_gpus) -> list[tuple[str, GpuInfo]]:
    """The GPUs with the most VRAM first; on a tie, the lowest PCI bus id first."""
    return sorted(keyed_gpus, key=lambda item: (-(item[1].vram_total_bytes or 0), item[1].pci_bus_id or "~", item[0]))


def ep_gpus(catalog: EpCatalog, key: str, host: HostInfo) -> list[tuple[str, GpuInfo]]:
    """The `(device_key, GpuInfo)` of each GPU that passes the floors of the pack of a plugin EP, in the default order.

    A built-in EP with `selects_gpu` (`directml`) can use each GPU of the host on its platforms.
    """
    row = catalog.device_row(key)
    platforms = catalog.ep(key).get("platforms")
    if row is None or (platforms and catalog_module.platform_tag() not in platforms):
        return []
    return _by_vram((device_key, gpu) for device_key, gpu in gpu_device_keys(host) if catalog.floors_reason(row, gpu) is None)


def _matches(match: dict, host: HostInfo, gpu: GpuInfo | None) -> bool:
    if match.get("os", host.os_name) != host.os_name or match.get("arch", host.arch) != host.arch:
        return False
    if match.get("native_arch", host.native_arch) != host.native_arch:
        return False
    if gpu is None:
        return True
    if match.get("vendor", gpu.vendor) != gpu.vendor:
        return False
    nvidia = gpu.nvidia
    if "brand" in match and (nvidia is None or nvidia.brand not in match["brand"]):
        return False
    if "cc_min" in match:
        capability = None if nvidia is None else nvidia.compute_capability
        if capability is None or version_tuple(capability) < version_tuple(match["cc_min"]):
            return False
    if "driver_branch_min" in match:
        branch = driver_branch(gpu.driver_version)
        if branch is None or branch < match["driver_branch_min"]:
            return False
    return True


def hardware_class(catalog: EpCatalog, host: HostInfo) -> dict:
    """The first hardware class of the catalog that a GPU of the host, or the host, matches."""
    for row in catalog.data["hardware_classes"]:
        match = row["match"]
        if match.get("host"):
            if _matches(match, host, None):
                return row
        elif any(_matches(match, host, gpu) for gpu in host.gpus):
            return row
    raise LookupError("the EP catalog has no hardware class for this host")  # the last row matches each host


def _candidate(catalog: EpCatalog, key: str, host: HostInfo) -> EpCandidate:
    row = catalog.ep(key)
    order = tuple(row["precision_order"])
    pack = catalog.pack(key)
    if catalog.device_row(key) is None:
        state, _, reason = store.pack_state(catalog, key)
        return EpCandidate(key, row["ep_name"], "ready" if state == "builtin" else state, precision_order=order, reason=reason)
    device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
    state, _, reason = store.pack_state(catalog, key, gpu, device_key, host.os_build)
    code = None if gpu is None else gate.check_reason(catalog, key, gpu, host.os_name)
    if code is not None and state in USABLE_STATES:
        reason = gate.REASONS[code]
    flags = (code == gate.FAILED_CHECK, code == gate.NEEDS_CHECK)
    if pack is None:  # a built-in EP that runs on one GPU
        return EpCandidate(key, row["ep_name"], "ready" if state == "builtin" else state, None, device_key, order, reason, *flags)
    return EpCandidate(key, pack["ep_name"], state, pack["id"], device_key, order, reason, *flags)


def recommend(form: str, host: HostInfo | None = None) -> EpRecommendation:
    """A concrete EP key with its options for a form. The caller passes them to a run.

    `accuracy` gives `cpu` with fp32 on each host. `performance` gives the first candidate of the
    hardware class of the host that is ready. `skipped` names each candidate before it, with the
    reason. `chosen.device_key` is the GPU with the most VRAM that the EP can use; on a tie, the
    lowest PCI bus id. A pack that is `installed_unverified` or `untested-ort` is ready. The result names
    only an EP that a run can start now: a candidate whose last quick check failed on this PC
    (`failed_locally`) and a candidate with no reviewed row and no quick check on this PC (`needs_check`)
    are skipped (`gate.py`, ADR-ER5X). An application offers the quick check for a skipped candidate
    with `needs_check`. A
    `field-test` EP is never a candidate, a skipped candidate or an offer, also after an opt-in
    (ADR-Z5X7).
    """
    if form not in ("performance", "accuracy"):
        raise ValueError(f"the form must be 'performance' or 'accuracy', not {form!r}")
    catalog = load_catalog()
    host = probe_host() if host is None else host
    row = hardware_class(catalog, host)
    evidence = None if row["ranking_evidence"] == "none" else row["ranking_evidence"]
    source = RecommendationSource(catalog.revision, row["id"], evidence)
    if form == "accuracy":
        return EpRecommendation(form, row["id"], _candidate(catalog, "cpu", host), "fp32", source)
    candidates = [_candidate(catalog, key, host) for key in row["candidates"] if catalog.ep_status(key) != "field-test"]
    chosen = next(candidate for candidate in candidates
                  if candidate.status in USABLE_STATES and not candidate.failed_locally and not candidate.needs_check)  # `cpu` is always ready
    skipped = tuple(candidates[: candidates.index(chosen)])
    offers = []
    for candidate in skipped if row.get("offer") == "add-pack" else ():
        if candidate.status in ("not_installed", "stale"):
            lock = catalog.pack_lock(candidate.pack_id)
            licences = catalog.pack(candidate.ep_key).get("licences") or [{}]
            offers.append(InstallOffer("add-pack", candidate.ep_key, candidate.pack_id, lock["download_bytes"],
                                       lock["unpacked_bytes"], licences[0].get("url"), install_hint(candidate.ep_key)))
    if row.get("offer") in ("update-driver", "none-available"):
        offers.append(InstallOffer(row["offer"], note=row["note"]))  # each such row has a note (test_each_offer_has_a_note)
    precision = chosen.precision_order[0]
    return EpRecommendation(form, row["id"], chosen, precision, source, catalog.default_options(chosen.ep_key, precision),
                            skipped, tuple(offers))


def select_precision(execution_provider: str, artifact_keys: Collection[str]) -> str:
    """The default precision of a model on an EP: fp16 on a GPU EP when the model has an fp16 artifact, else fp32."""
    order = load_catalog().ep(execution_provider)["precision_order"]
    return next((precision for precision in order if precision in artifact_keys), "fp32")


def run_devices(execution_provider: str, device: str | Sequence[str] | None = None) -> tuple[RunDevice, ...]:
    """The GPUs that a run on a GPU EP uses: the GPUs that pass the floors of the EP pack, or each GPU for `directml`.

    The GPU with the most VRAM is first; on a tie, the GPU with the lowest PCI bus id. `device` is
    one device key or a list of device keys. The result then holds exactly those GPUs. A key that is
    not such a GPU raises `EpUnavailableError`. `cpu` and `coreml` give no GPU.
    """
    catalog = load_catalog()
    usable = ep_gpus(catalog, execution_provider, probe_host())
    if catalog_module.platform_tag() not in catalog.data["platforms"]:
        usable = []
    if device is not None:
        wanted = [device] if isinstance(device, str) else list(device)
        known = dict(usable)
        for key in wanted:
            if key not in known:
                names = ", ".join(known) or "none"
                raise EpUnavailableError(f"'{key}' is not a GPU that the EP '{execution_provider}' can use on this host. "
                                         f"Its GPUs are: {names}.")
        usable = [(key, gpu) for key, gpu in usable if key in wanted]
    return tuple(RunDevice(key, gpu.key, gpu.name, gpu.pci_bus_id, gpu.vram_total_bytes) for key, gpu in usable)
