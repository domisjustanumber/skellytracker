"""The rehearsal of the Windows ML route of ADR-XSE7 on a PC with no AMD GPU, with the NVIDIA TensorRT RTX EP of the catalog.

Usage, one step for each process (`uv run --no-sync python -B decisions/scripts/xse7_windows_ml_rehearsal.py STEP`):

    state      the Windows ML packages of the current user (`Get-AppxPackage`)
    run        `windows_ml.install()`, the registration, the EP device and the L3 probe of `_verify_child.run()`
    remove     remove the TensorRT RTX package of the catalog with `windows_ml.remove_package()`
    cleanup    `remove_windows_packages()` of the certify frame on the records of the store

The test hook: in this process only, the EP row `amdgpu` takes the EP name of the TensorRT RTX EP of
the catalog and the floor `vendor: nvidia`. Each other line is the code of the package and of the
certify frame. The script refuses to run without `SKELLYTRACKER_EP_STORE` and
`SKELLYTRACKER_EP_CACHE`, so that it never changes the EP store of the user. It removes only a
package of the family `ALLOWED_FAMILY`. Each step prints one JSON object.
"""

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(REPO_ROOT / "tools")]

EP_NAME = "NvTensorRTRTXExecutionProvider"
ALLOWED_FAMILY = "Microsoft.WinML.NVIDIA.TRT-RTX.EP.Framework.2_8wekyb3d8bbwe"  # the one package that the user allowed to remove
KEY = "amdgpu"


def winml_packages() -> list[str]:
    from skellytracker.core.eps import windows_ml

    return sorted(name for name in windows_ml.installed_packages() if name.startswith("Microsoft.WinML."))


def hook() -> None:
    from skellytracker.core.eps.catalog import load_catalog

    row = load_catalog().data["eps"][KEY]  # the cached catalog of this process: each caller sees the change
    row["ep_name"], row["requires"] = EP_NAME, {"vendor": "nvidia"}


def run() -> dict:
    from skellytracker.core.eps import _verify_child, registration, store, windows_ml
    from skellytracker.core.system.host import gpu_device_keys

    hook()
    store.opt_in_field_test(KEY)
    found = {"before": winml_packages(), "catalog": windows_ml.find_eps()}
    started = time.perf_counter()
    found["record"] = windows_ml.install(KEY)
    found["install_seconds"] = round(time.perf_counter() - started, 2)
    device_key, gpu = next((k, g) for k, g in gpu_device_keys() if g.vendor == "nvidia")
    started = time.perf_counter()
    registered = windows_ml.register(KEY)
    device = registration.ort_device(registered.ep_name, gpu, int(device_key.rsplit(":", 1)[1]))
    found["register_seconds"] = round(time.perf_counter() - started, 2)
    found["device"] = None if device is None else {"ep_name": device.ep_name, "vendor_id": hex(device.device.vendor_id),
                                                  "device_id": hex(device.device.device_id), "gpu": gpu.name}
    started = time.perf_counter()
    probe = _verify_child.run({"key": KEY, "pack": None, "gpu": gpu, "device_key": device_key, "level": "L3", "atol": 1.5e-2})
    found["probe"] = {**probe, "seconds": round(time.perf_counter() - started, 2)}
    found["after"] = winml_packages()
    return found


def remove() -> dict:
    from skellytracker.core.eps import windows_ml

    targets = [name for name, family in windows_ml.installed_packages().items() if family == ALLOWED_FAMILY]
    return {"before": winml_packages(), "removed": {name: windows_ml.remove_package(name, ALLOWED_FAMILY) for name in targets},
            "after": winml_packages()}


def cleanup() -> dict:
    import certify_platform

    work = Path(os.environ["SKELLYTRACKER_EP_STORE"]).parent  # the store is `<work>/eps`, as in the certify frame
    records = certify_platform.read_records(work / "eps" / "windows-ml.json")
    if not all(r.get("package_family_name") in (None, ALLOWED_FAMILY) for r in records.values()):
        sys.exit("A record names an other package family: nothing removed.")
    return {"before": winml_packages(), "rows": certify_platform.remove_windows_packages(work), "after": winml_packages()}


if __name__ == "__main__":
    if not (os.environ.get("SKELLYTRACKER_EP_STORE") and os.environ.get("SKELLYTRACKER_EP_CACHE")):
        sys.exit("Set SKELLYTRACKER_EP_STORE and SKELLYTRACKER_EP_CACHE to scratch folders.")
    step = sys.argv[1]
    result = {"state": lambda: {"packages": winml_packages()}, "run": run, "remove": remove, "cleanup": cleanup}[step]()
    print(json.dumps({"step": step, **result}, default=str), flush=True)
