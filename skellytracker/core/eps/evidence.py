"""The certification evidence of the EP packs: `ep_evidence.yaml`, the set hash and `certified()`.

An evidence row records that one EP ran the project models on one GPU model on one OS. A person
writes a row after a review. A row is not a verification of this host: `verify()` does that.
"""

import functools
import hashlib
import importlib.resources
import json
import re

import yaml

from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps.catalog import EpCatalog


def set_hash(catalog: EpCatalog) -> str:
    """The hash of the exact version set: the ONNX Runtime distributions and each wheel of each `ready` user pack.

    Only `ready` packs are in the set (user decision, 2026-11-18). A test pack and a `field-test` pack
    are not: a field-test pack enters it when a person moves it to `ready`, and the set then needs new
    evidence (ADR-XSE7). A pack `component`, for example the GPU JPEG decoder, is not in the set (user
    decision, 2026-11-18): the JPEG certification of the level `full` of `certify()` is its evidence. The package of the Windows
    ML catalog is not in the set: Windows updates it with no pin.
    shortcut: the `windowsml` pin and the `onnx` pin are not in the set, add them when a bump changes one alone.
    """
    packs = {pack["id"]: {tag: [[wheel["filename"], wheel["sha256"]] for wheel in row["wheels"]]
                          for tag, row in sorted(catalog.lock.get("packs", {}).get(pack["id"], {}).items())}
             for ep in catalog.data["eps"].values() for pack in ep.get("packs", ()) if pack.get("status", "ready") == "ready"}
    text = json.dumps({"ort_core": catalog.data["ort_core"], "packs": packs}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def gpu_id(gpu) -> str | None:
    """The PCI vendor id and device id of a GPU (`GpuInfo`) as `10de:2484`; `None` when the host gives no ids."""
    if gpu is None:
        return None
    if getattr(gpu, "chip_id", None):  # the chip of the host, for an EP that runs on no single GPU (`gate.Chip`)
        return gpu.chip_id
    if gpu.pci_vendor_id is None or gpu.pci_device_id is None:
        return None
    return f"{gpu.pci_vendor_id:04x}:{gpu.pci_device_id:04x}"


@functools.cache
def load_evidence() -> tuple[dict, ...]:
    """The rows of `ep_evidence.yaml`. The file is read one time for each process."""
    text = importlib.resources.files("skellytracker.core.eps").joinpath("ep_evidence.yaml").read_text(encoding="utf-8")
    return tuple((yaml.safe_load(text) or {}).get("rows") or ())


def certified(key: str, gpu, os_name: str) -> bool:
    """True when a row records a pass of the EP `key` on this GPU model on this OS, for the version set of this release.

    The `set` of the row must be equal to `set_hash()` of the EP catalog (ADR-X7WD item 2). A GPU with no PCI ids
    matches no row. A row that is not a mapping, or has no field, matches nothing.
    """
    ids = gpu_id(gpu)
    if ids is None:
        return False
    current = set_hash(catalog_module.load_catalog())
    return any(isinstance(row, dict) and row.get("ep") == key and row.get("os") == os_name and row.get("gpu") == ids
               and row.get("set") == current and row.get("result") == "pass" for row in load_evidence())


def os_key(os_label: str | None) -> str | None:
    """The key of an OS: its name and its release, from the OS label (ADR-X7WD item 8). None when the label has no release.

    `Windows 11 Home 26H2` gives `Windows 11`, `Ubuntu 24.04.1 LTS` gives `Ubuntu 24.04` and `macOS 15.1` gives
    `macOS 15`. An edition or an update of the OS is not a part of the key.
    """
    match = re.match(r"(\D+?)\s+(\d+)(\.\d+)?", os_label or "")
    if match is None:
        return None
    name, major, minor = match.groups()
    return f"{name} {major}{'' if name == 'macOS' else minor or ''}"
