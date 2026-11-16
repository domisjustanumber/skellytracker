"""`selftest()`: the EP pack test of the `ep_pack` CI job. It runs no real model.

On Windows and Linux it installs the test pack of the EP catalog (an OpenVINO pack) into the EP
store, and checks that the pack registers and lists a device in a child process. The OpenVINO EP
lists a device only for a hardware device with the PCI vendor id of Intel (`8086`). A host has an
Intel device when one or more of the hardware devices that ONNX Runtime lists has that vendor id.
On a host with no Intel device the step passes when the pack registers, and its detail says that
the device list is not checked. When the hardware device list cannot be read, the step needs a
device of the EP. No session runs on the test pack. The test pack is never offered, selected or installed for a user. On macOS it
runs a trial session on the CoreML EP. On each platform it runs a trial session on the CPU EP.
"""

from collections.abc import Sequence

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import installer, verification
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.records import InstallPlan, SelftestResult
from skellytracker.core.eps.registration import NO_DEVICE

INTEL = 0x8086


def has_intel_device(hardware_vendor_ids: Sequence[int]) -> bool:
    """True when a hardware device that ONNX Runtime lists has the PCI vendor id of Intel. The OpenVINO EP uses the same test."""
    return INTEL in hardware_vendor_ids


def _trial(key: str) -> str:
    (verdict,) = verification.verify([key], force=True)
    if not verdict.ok:
        raise RuntimeError(verdict.reason)
    return f"{verdict.level}, largest difference {verdict.max_abs_diff}"


def _test_pack(index_url: str | None) -> str:
    catalog = load_catalog()
    key, pack = next((key, pack) for key, row in catalog.data["eps"].items() for pack in row.get("test_packs", ()))
    planned = installer.planned_pack(catalog, pack["id"], index_url=index_url)
    result = installer.install(InstallPlan((planned,), planned.download_bytes, planned.disk_bytes), verify=False)
    if result.failed:
        raise RuntimeError(f"{result.failed[0][1]}: {result.failed[0][2]}")
    record = verification.run_child({"key": key, "pack": pack, "gpu": None, "device_key": None, "level": "L2", "atol": 0.0})
    if record["ok"]:
        return f"{pack['id']} {pack['version']} registers and lists a device"
    vendor_ids = record.get("hardware_vendor_ids")
    if NO_DEVICE in (record["reason"] or ""):
        if vendor_ids is None:
            raise RuntimeError(f"{record['reason']} The hardware device list of ONNX Runtime could not be read, "
                               "so the step needs a device of the EP.")
        if not has_intel_device(vendor_ids):
            return f"{pack['id']} {pack['version']} registers; this host has no Intel device, so the device list is not checked"
    raise RuntimeError(record["reason"])


def selftest(index_url: str | None = None) -> SelftestResult:
    """Run the self test. `index_url` gives a local index that holds the wheels of the test pack."""
    steps = []

    def step(name: str, call) -> None:
        try:
            steps.append((name, True, call()))
        except Exception as error:  # noqa: BLE001 - each failure is a step result
            steps.append((name, False, sanitize_text(f"{type(error).__name__}: {error}")[:500]))

    step("catalog", lambda: f"revision {load_catalog().revision[:12]}")
    step("cpu trial session", lambda: _trial("cpu"))
    tag = catalog_module.platform_tag()
    if tag == "macosx_arm64":
        step("coreml trial session", lambda: _trial("coreml"))
    elif tag in load_catalog().data["platforms"]:
        step("test pack", lambda: _test_pack(index_url))
    return SelftestResult(all(ok for _, ok, _ in steps), tuple(steps))
