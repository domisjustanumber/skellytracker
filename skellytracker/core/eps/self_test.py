"""`selftest()`: the EP pack test of the `ep_pack` CI job. It runs no real model.

On Windows and Linux it installs the test pack of the EP catalog (an OpenVINO pack) into the EP
store, and checks that the pack registers and lists a device in a child process. No session runs
on the test pack. The test pack is never offered, selected or installed for a user. On macOS it
runs a trial session on the CoreML EP. On each platform it runs a trial session on the CPU EP.
"""

from skellytracker.core._hardware.sanitize import sanitize_text
from skellytracker.core.eps import catalog as catalog_module
from skellytracker.core.eps import installer, verification
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.records import InstallPlan, SelftestResult


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
    if not record["ok"]:
        raise RuntimeError(record["reason"])
    return f"{pack['id']} {pack['version']} registers and lists a device"


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
