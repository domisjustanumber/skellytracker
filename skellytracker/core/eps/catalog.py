"""The loader of the EP catalog (`ep_catalog.yaml`) and of its lock (`ep_lock.yaml`).

The catalog owns the EP keys, the allowed EP options, the packs and the hardware classes. The lock
holds the URL, the sha256 and the sizes of each wheel of each pack. Both files are package data.
"""

import functools
import hashlib
import importlib.resources
import platform
import sys
from collections.abc import Mapping
from dataclasses import dataclass

import yaml

from skellytracker.core.eps.records import Options
from skellytracker.core.errors import EpRequestError

POSITIVE_INT = "positive-int"


def revision_of(catalog_text: str) -> str:
    """The catalog revision: the sha256 of the catalog text with `\\n` line ends."""
    return hashlib.sha256(catalog_text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def platform_tag() -> str:
    """The pack platform of this process: `win_amd64`, `manylinux_x86_64`, `macosx_arm64`, or an other tag."""
    machine = platform.machine().lower()
    if sys.platform == "win32" and machine in ("amd64", "x86_64"):
        return "win_amd64"
    if sys.platform == "linux" and machine in ("x86_64", "amd64"):
        return "manylinux_x86_64"
    if sys.platform == "darwin" and machine == "arm64":
        return "macosx_arm64"
    return f"{sys.platform}_{machine}"


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split(".") if part.isdigit())


def driver_branch(driver_version: str | None) -> int | None:
    """The NVIDIA driver branch: the major version, down to a multiple of 5. `582.78` is R580."""
    major = (driver_version or "").split(".")[0]
    return int(major) // 5 * 5 if major.isdigit() else None


@dataclass(frozen=True)
class EpCatalog:
    data: dict
    lock: dict
    revision: str

    @property
    def ort_version(self) -> str:
        return self.data["ort_core"]["version"]

    def keys(self) -> tuple[str, ...]:
        """The EP keys that a request can name, in catalog order. A reserved key is not one of them."""
        return tuple(key for key, row in self.data["eps"].items() if row["kind"] != "reserved")

    def ep(self, key: str) -> dict:
        """The row of an EP key. A reserved key or an unknown key raises `EpRequestError` with the reason."""
        row = self.data["eps"].get(key) if isinstance(key, str) else None
        if row is None:
            raise EpRequestError(f"'{key}' is not an EP key. The EP keys are: {', '.join(self.keys())}.")
        if row["kind"] == "reserved":
            raise EpRequestError(f"The EP key '{key}' is reserved: {row['reason']}.")
        return row

    def pack(self, key: str) -> dict | None:
        """The pack row of a plugin EP key; `None` for a built-in EP."""
        packs = self.ep(key).get("packs")
        return packs[0] if packs else None

    def pack_by_id(self, pack_id: str) -> tuple[str, dict] | None:
        """The EP key and the row of a pack id, also for a test pack."""
        for key, row in self.data["eps"].items():
            for pack in [*row.get("packs", ()), *row.get("test_packs", ())]:
                if pack["id"] == pack_id:
                    return key, pack
        return None

    def pack_lock(self, pack_id: str, tag: str | None = None) -> dict | None:
        """The lock row of a pack for a platform tag; `None` when the platform has no such pack."""
        return self.lock.get("packs", {}).get(pack_id, {}).get(tag or platform_tag())

    def check_options(self, key: str, options: Mapping | None) -> Options:
        """The options as a sorted tuple. A name or a value that the catalog does not list raises `EpRequestError`."""
        allowed = self.ep(key)["options"]["allowed"]
        for name, value in (options or {}).items():
            if name not in allowed:
                raise EpRequestError(
                    f"The EP '{key}' has no option '{name}'. The allowed options are: {', '.join(allowed) or 'none'}.")
            rule = allowed[name]
            ok = isinstance(value, str) and (
                (value.isascii() and value.isdigit() and int(value) > 0) if rule == POSITIVE_INT else value in rule)
            if not ok:
                wanted = "a positive integer" if rule == POSITIVE_INT else " or ".join(rule)
                raise EpRequestError(f"The option '{name}' of the EP '{key}' must be {wanted}, as a string, not {value!r}.")
        return tuple(sorted((options or {}).items()))

    def default_options(self, key: str, precision: str | None = None) -> Options:
        """The performance options of an EP for a precision. A caller passes them as `ep_options`."""
        return tuple(sorted(self.ep(key)["options"].get("defaults", {}).get(precision, {}).items()))

    def ort_untested(self, pack: dict, ort_version: str | None = None) -> bool:
        """True when ONNX Runtime `ort_version` is outside the versions that the pack was tested with."""
        core = ort_version or self.ort_version
        ort = pack.get("ort", {})
        if "vendor_tested" in ort:
            low, high = (version_tuple(text) for text in ort["vendor_tested"])
            return not low <= version_tuple(core)[: len(high)] <= high
        return core not in ort.get("verified_by_us", ())

    def floors_reason(self, pack: dict, gpu) -> tuple[str, str] | None:
        """Why a GPU (`GpuInfo`) does not pass the floors of a pack: `(reason code, reason)`, or `None`."""
        requires = pack.get("requires", {})
        if requires.get("vendor") and gpu.vendor != requires["vendor"]:
            return "no-device", f"the pack needs a GPU of the vendor {requires['vendor']}"
        capability = None if gpu.nvidia is None else gpu.nvidia.compute_capability
        if "cc_min" in requires and (capability is None or version_tuple(capability) < version_tuple(requires["cc_min"])):
            return "cc-too-low", f"the pack needs compute capability {requires['cc_min']} or higher, the GPU has {capability}"
        branch = driver_branch(gpu.driver_version)
        if "driver_branch_min" in requires and (branch is None or branch < requires["driver_branch_min"]):
            return "driver-too-old", (f"the pack needs an NVIDIA driver of R{requires['driver_branch_min']} or later, "
                                      f"the driver is {gpu.driver_version}")
        return None


@functools.cache
def load_catalog() -> EpCatalog:
    """The EP catalog of this package. It is read one time for each process."""
    files = importlib.resources.files("skellytracker.core.eps")
    text = files.joinpath("ep_catalog.yaml").read_text(encoding="utf-8")
    lock = yaml.safe_load(files.joinpath("ep_lock.yaml").read_text(encoding="utf-8")) or {}
    return EpCatalog(data=yaml.safe_load(text), lock=lock, revision=revision_of(text))
