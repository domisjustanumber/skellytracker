"""The check rule of an EP on a GPU (ADR-21BK items 2 and 3, ADR-ER5X): a run starts only after a check.

The rule also applies to `coreml`, which runs on the chip of a Mac and selects no GPU: `chip_of()` gives the
stand-in for its GPU, and the key of its results is the chip name.

An EP on a GPU can run when the project has a reviewed pass for the GPU model, the OS and the version set of this
release (`ep_evidence.yaml`, `evidence.certified()`), or
when a quick check of `skellytracker.certify()` passed on this PC. It cannot run after a quick check that
failed on this PC. `check_start()` and `build_session()` call `require()`, so each run and each session obeys
the rule. The rule has no setting and no environment variable.

The certification code must run an EP before the EP has a result. It runs inside `certification_run()`,
which switches the rule off for this process. Only the certification code uses it: the probe, the `video` and `live`
runs, the timings and the JPEG checks of `skellytracker.certify()`, the JPEG certification and the certify suite.

This module loads no library and uses no network. It reads `quick-checks.json` of the EP store.
"""

import contextlib
import dataclasses
import re

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import evidence, store
from skellytracker.core.eps.catalog import EpCatalog
from skellytracker.core.errors import EpUnavailableError

OS_LABELS = {"Darwin": "macOS"}  # `HostInfo.os_name` -> the `os` of a row of `ep_evidence.yaml`


@dataclasses.dataclass(frozen=True)
class Chip:
    """The stand-in for the GPU of an EP that runs on the chip of the host and selects no GPU: `coreml`.

    `chip_id` is the key of its results, for example `chip:apple-m2-pro`. A Mac gives no PCI ids.
    """

    name: str
    chip_id: str
    pci_vendor_id: None = None
    pci_device_id: None = None


def chip_of(catalog: EpCatalog, key: str, host) -> Chip | None:
    """The chip of the host for a built-in EP that runs on a GPU and selects none (`coreml`), on its platform. Else None."""
    row = catalog.ep(key)
    if row["kind"] != "builtin" or not row.get("gpu") or row.get("selects_gpu"):
        return None
    if "platforms" in row and catalog_module.platform_tag() not in row["platforms"]:
        return None
    name = host.cpu_name or "unknown chip"
    return Chip(name, "chip:" + (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"))


NEEDS_CHECK = "quick-check-needed"  # no reviewed row and no quick check on this PC
FAILED_CHECK = "quick-check-failed"  # the last quick check on this PC failed
UNCLEAN_EXITS = "unclean-exits"  # two unclean exits in a row marked the EP as failed on this PC (`exits.py`)
FAILED_CODES = (FAILED_CHECK, UNCLEAN_EXITS)  # the codes of an EP that failed on this PC
REASONS = {
    NEEDS_CHECK: "the project has no reviewed result for it on this GPU model, and no quick check passed on this system",
    FAILED_CHECK: "its last quick check failed on this system",
    UNCLEAN_EXITS: "the application ended two times in a row with no clean exit while it used this EP on this system",
}

_certification_runs = 0  # the depth of `certification_run()` in this process


@contextlib.contextmanager
def certification_run():
    """Switch the check rule off in this process, for the certification code only. A run of an application never uses it."""
    global _certification_runs  # noqa: PLW0603 - one switch for the process: the sessions of a run have no common argument
    _certification_runs += 1
    try:
        yield
    finally:
        _certification_runs -= 1


def certification_active() -> bool:
    """True inside `certification_run()`."""
    return bool(_certification_runs)


def pack_version(catalog: EpCatalog, key: str) -> str:
    """The pack version of the EP: of its pack, of its Windows ML record, or `builtin` for a built-in EP."""
    pack = catalog.pack(key) or (store.windows_ml_pack(catalog, key) if catalog.windows_ml(key) else {"version": "builtin"})
    return pack["version"]


def pair_key(catalog: EpCatalog, key: str, gpu, os_name: str) -> str:
    """The pair of a local result. The pack version is in it, so a pack upgrade needs a new quick check.

    `gpu` comes from `ep_gpus()`, which gives only GPUs with PCI ids, so `gpu_id` is never None here. An EP of
    the Windows ML catalog takes the package version of its record, and a built-in EP takes `builtin`.
    """
    return f"{key}|{pack_version(catalog, key)}|{os_name}|{evidence.gpu_id(gpu)}"


def local_result(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """`passed` or `failed`: the last quick check of the EP on this GPU model on this PC, for the pack version of today.

    None with no such check, and for a GPU with no PCI ids. It reads `quick-checks.json` of the EP store.
    """
    if evidence.gpu_id(gpu) is None:
        return None
    row = (store.read_json(store.store_root() / "quick-checks.json") or {}).get(pair_key(catalog, key, gpu, os_name))
    return row["result"] if isinstance(row, dict) and row.get("result") in ("passed", "failed") else None


def local_cause(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """`unclean-exits` when two unclean exits in a row gave the local result `failed` (`exits.py`), else None."""
    if evidence.gpu_id(gpu) is None:
        return None
    row = (store.read_json(store.store_root() / "quick-checks.json") or {}).get(pair_key(catalog, key, gpu, os_name))
    return "unclean-exits" if isinstance(row, dict) and row.get("result") == "failed" and row.get("cause") == "unclean-exits" else None


def check_reason(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """None when the rule lets the EP run on the GPU, else `quick-check-failed`, `unclean-exits` or `quick-check-needed`.

    It does not read the state of the pack. An EP with no GPU row, for example `cpu`, has no rule: call it only
    with a GPU of `ep_gpus()`.
    """
    local = local_result(catalog, key, gpu, os_name)
    if local == "failed":
        return UNCLEAN_EXITS if local_cause(catalog, key, gpu, os_name) else FAILED_CHECK
    return None if local == "passed" or evidence.certified(key, gpu, OS_LABELS.get(os_name, os_name)) else NEEDS_CHECK


def rule_passes(catalog: EpCatalog, key: str, gpu, os_name: str) -> bool:
    """True when `require()` does not raise for the EP on the GPU: the rule lets it run, or the rule is switched off."""
    return bool(_certification_runs) or check_reason(catalog, key, gpu, os_name) is None


def check_hint(key: str) -> str:
    return f"Run `skellytracker-eps certify {key}`."


def require(catalog: EpCatalog, key: str, gpu, os_name: str, device_key: str | None = None) -> None:
    """Raise `EpUnavailableError` with the quick-check command when the rule does not let the EP run on the GPU.

    The error holds the EP key, `device_key` and the reason code as fields.
    """
    if _certification_runs:
        return
    code = check_reason(catalog, key, gpu, os_name)
    if code is not None:
        raise EpUnavailableError(f"The EP '{key}' cannot run on '{gpu.name}': {REASONS[code]}.", check_hint(key),
                                 execution_provider=key, device_key=device_key, reason_code=code)
