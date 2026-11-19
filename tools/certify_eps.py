"""Sections 3 and 4 of the certify suite (``tools/certify_platform.py``): the EP packs, and the level ``full`` of ``certify()``.

Both sections run only with the isolated EP store of the suite: the frame sets ``SKELLYTRACKER_EP_STORE``
and ``SKELLYTRACKER_EP_CACHE`` to folders of the work folder. Without them a section is ``not-run``
with ``no-isolated-store``, so that it never installs into the EP store of the user.

Section 3. The EPs come from ``eps.status()``: each EP key of the catalog that a GPU of this host can
use (a plugin EP that is not ``unsupported``) and each built-in EP of this platform (``cpu``, and
``coreml`` on macOS). An EP that the host cannot use is ``not-run`` with its state code. A plugin EP
is installed with ``eps.plan_install()`` and ``eps.install()``, the code path of
``skellytracker-eps install KEY --yes`` (``--wheel-dir`` gives ``from_dir``), and then tested with
``eps.certify(key, out=...)``. Its probe is ``verify()`` at level L3. A built-in EP gets
``eps.verify([key], level="L3", force=True)``. Before ``eps.status()``, the section opts in to each
``field-test`` EP in the isolated store (ADR-Z5X7). A built-in EP that runs on one GPU (``directml``
on Windows) gets that probe on each GPU of the host, as the check ``KEY@DEVICE_KEY``. Each result
counts, on each GPU. Each result records the ONNX Runtime version that it ran on (``ort_version``).

The AMD EPs (ADR-XSE7). On Windows, the section asks the Windows ML catalog which EPs it offers for
this PC (``windows_ml.find_eps()``). It tests each AMD EP key of the catalog (``amdgpu``, ``migraphx``)
that the catalog offers, on each AMD GPU, as a built-in EP that runs on one GPU. It installs the package
with ``windows_ml.install()``: for a package that is not on the PC, Windows downloads and installs it.
The record in the isolated EP store names each package that the install added, and the frame removes
exactly those at the end (``remove_windows_packages`` of ``certify_platform.py``), never a package
that was on the PC before. An EP that the catalog does not offer is ``not-run`` with ``not-offered``.
On Linux, ``migraphx`` is the pack of the ROCm release of the host: no ROCm is ``not-run`` with
``rocm-missing``, and an other release ``rocm-version``. The details give ``rocm_version``.

Section 4. It takes the model files of the ``models`` list of the ``certification`` block of the EP
catalog (``fetch_models``). The frame deletes each file that the section downloads, at the end of the
run. Then the section calls ``skellytracker.certify("full")`` with the default selection, in the
isolated EP store, so that it finds the packs of section 3. The package runs the pipeline timings and
the JPEG certification, and gives ``models-missing`` when a model file is absent. The result of the
section is the outcome of the checks of the module report. The key ``report`` of the result holds that
module report, and the frame builds the report file on it. A call that raises gives ``fail`` with the
exception class and no report.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

from certify_platform import MODEL_ROOT, check, outcome  # the frame deletes listed files only inside MODEL_ROOT

REPO_ROOT = Path(__file__).resolve().parents[1]
REMOVE_LIST = "remove-at-end.json"  # the frame deletes each file of this list at the end of the run


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def isolated() -> bool:
    from skellytracker.core.eps import store

    return bool(os.environ.get(store.STORE_VARIABLE)) and bool(os.environ.get(store.CACHE_VARIABLE))


def not_isolated() -> dict:
    return {"result": "not-run", "reason_code": "no-isolated-store", "summary": "the isolated EP store of the suite is not set",
            "checks": [], "details": {}}


def first_failure(checks: list[dict]) -> str | None:
    return next((c["reason_code"] for c in checks if c["result"] == "fail"), None)


# --------------------------------------------------------------------------------------------
# Section 3
# --------------------------------------------------------------------------------------------


def eps_downloads(options: dict) -> tuple[tuple[str, int], ...]:
    """The wheels of each pack that a GPU of this host can use, with their sizes from `ep_lock.yaml`. None with `--wheel-dir`."""
    if options.get("wheel_dir"):
        return ()
    sys.path.insert(0, str(REPO_ROOT))
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.eps.recommendation import ep_gpus
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    keys = [key for key in catalog.keys() if catalog.pack(key) and ep_gpus(catalog, key, host)]
    return tuple((wheel["filename"], wheel["download_bytes"]) for key in keys
                 for wheel in (catalog.pack_lock(catalog.pack(key)["id"]) or {}).get("wheels", ()))


def test_builtin(key: str, device_key: str | None = None) -> dict:
    from skellytracker.core import eps

    try:
        (verdict,) = eps.verify([key], level="L3", device_key=device_key, force=True)
    except Exception as error:  # noqa: BLE001 - a finding with a fixed code
        return {"result": "fail", "reason_code": type(error).__name__}
    return {"result": "pass" if verdict.ok else "fail", "reason_code": None if verdict.ok else f"probe-{verdict.level.lower()}-failed",
            "probe": {"ok": verdict.ok, "level": verdict.level, "max_abs_diff": verdict.max_abs_diff,
                      "exit_reason_code": verdict.exit_reason_code}}


def test_pack(key: str, wheel_dir: str | None, work: Path) -> dict:
    """Install the pack of `key` into the isolated store, then run `certify()` (its probe is `verify()` at L3)."""
    from skellytracker.core import eps
    from skellytracker.core.eps import store

    plan = eps.plan_install([key])
    (planned,) = plan.packs
    facts = {"pack_id": planned.pack_id, "pack_version": planned.version, "download_bytes": planned.download_bytes,
             "source": "wheel-dir" if wheel_dir else "network"}
    result = eps.install(plan, from_dir=Path(wheel_dir) if wheel_dir else None)
    code = "ok" if key in result.ok else next((c for k, c, _ in result.failed if k == key), "cancelled")
    facts["install"] = code
    if code not in ("ok", "verify-failed"):  # a pack that fails its verification stays installed: certify() gives the numbers
        return {**facts, "result": "fail", "reason_code": f"install-{code}"}
    manifest = store.read_manifest(planned.pack_id, planned.version) or {}
    facts["wheels"] = [{"filename": name, "sha256": sha} for name, sha in manifest.get("wheels", ())]
    try:
        report = json.loads(eps.certify(key, out=work / f"certify-{key}.json").report_json)
    except Exception as error:  # noqa: BLE001
        return {**facts, "result": "fail", "reason_code": type(error).__name__}
    versions = {name: value for name, value in report["versions"].items() if name != "skellytracker"}  # section 1 has the tag and commit
    facts.update(certify_result=report["result"], probe=report["probe"], gpu=report["gpu"], versions=versions)
    passed = report["result"] == "pass"
    return {**facts, "result": "pass" if passed else "fail",
            "reason_code": None if passed else report["reason_code"] or f"certify-{report['result']}"}


def ort_version() -> str | None:
    from skellytracker.core.eps.installer import installed_ort

    return (installed_ort() or (None, None))[1]


def windows_ml_offer() -> list[str]:
    """The EP names of the AMD EPs that the Windows ML catalog offers for an AMD GPU of this host. It installs nothing."""
    sys.path.insert(0, str(REPO_ROOT))
    from skellytracker.core.eps import windows_ml
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.eps.recommendation import ep_gpus
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    names = [catalog.ep(key)["ep_name"] for key in catalog.keys() if catalog.windows_ml(key) and ep_gpus(catalog, key, host)]
    return [name for name in names if name in windows_ml.find_eps()] if names else []


def windows_ml_eps(catalog, host) -> dict[str, dict]:
    """Install the package of each AMD EP that the Windows ML catalog offers for an AMD GPU of this host (ADR-XSE7).

    An EP key in the result with a `result` is not tested further. Each other EP key has the facts of the record of
    `windows_ml.install()`. The record stays in the isolated EP store: at the end the frame removes each package of
    `packages_installed`, also after a crash or a timeout of this section.
    """
    from skellytracker.core.eps import windows_ml
    from skellytracker.core.eps.recommendation import ep_gpus

    keys = [key for key in catalog.keys() if catalog.windows_ml(key) and ep_gpus(catalog, key, host)]
    if not keys:
        return {}
    try:
        offered = windows_ml.find_eps()
    except Exception as error:  # noqa: BLE001 - for example a Windows build with no Windows ML catalog
        return {key: {"result": "not-run", "reason_code": f"catalog-{type(error).__name__}"} for key in keys}
    found = {}
    for key in keys:
        state = offered.get(catalog.ep(key)["ep_name"])
        if state is None:
            found[key] = {"result": "not-run", "reason_code": "not-offered"}
            continue
        print(f"section 3: the Windows ML package of {key} ({state})", file=sys.stderr, flush=True)
        try:
            record = windows_ml.install(key)
            found[key] = {"catalog_state": state, "package_version": record["version"], "was_present": record["was_present"],
                          "package_family_name": record["package_family_name"], "packages_installed": record["packages_installed"]}
        except Exception as error:  # noqa: BLE001
            found[key] = {"result": "fail", "reason_code": type(error).__name__, "catalog_state": state}
    return found


def section_eps(work: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    if not isolated():
        return not_isolated()
    from skellytracker.core import eps
    from skellytracker.core.eps import store
    from skellytracker.core.system.host import gpu_device_keys, probe_host, rocm_version

    wheel_dir = (read_json(work / "options.json") or {}).get("wheel_dir")
    catalog = eps.load_catalog()
    for key in catalog.keys():  # the opt-in of the suite, in its own store: the frame deletes it at the end (ADR-Z5X7)
        if catalog.ep_status(key) == "field-test":
            store.opt_in_field_test(key)
    catalog_eps = windows_ml_eps(catalog, probe_host())  # before `status()`: an installed EP is then usable
    status = eps.status()
    rows, gpus = {row.key: row for row in status.eps}, dict(gpu_device_keys(status.host))
    checks, found, ort = [], {}, ort_version()
    for key in catalog.keys():
        row = rows.get(key)
        if "result" in catalog_eps.get(key, {}):  # a Windows ML EP that the suite does not test (ADR-XSE7)
            found[key] = catalog_eps[key]
            checks.append(check(key, found[key]["result"], found[key]["reason_code"]))
            continue
        if row is None or row.state == "unsupported":  # no row: an EP of an other platform
            found[key] = {"state": "unsupported", "reason_code": "os" if row is None else row.reason_code}
            checks.append(check(key, "not-run", found[key]["reason_code"]))
            continue
        on_each_gpu = row.pack_id is None and catalog.device_row(key) is not None  # `directml` or a Windows ML EP: each GPU
        for device in row.devices if on_each_gpu else (None,):
            name = key if device is None else f"{key}@{device.device_key}"
            print(f"section 3: {name}", file=sys.stderr, flush=True)
            started = time.monotonic()
            if device is not None:
                found[name] = {**test_builtin(key, device.device_key), "vendor": gpus[device.device_key].vendor,
                               **catalog_eps.get(key, {})}
            else:
                found[name] = test_builtin(key) if row.pack_id is None else test_pack(key, wheel_dir, work)
            found[name].update(seconds=round(time.monotonic() - started, 1), ort_version=ort)
            checks.append(check(name, found[name]["result"], found[name]["reason_code"]))
    tested = [c for c in checks if c["result"] != "not-run"]
    summary = ", ".join(f"{c['name']} {c['result']}" for c in tested) + f"; {len(checks) - len(tested)} not run"
    return {"result": outcome(checks), "reason_code": first_failure(checks), "summary": summary, "checks": checks,
            "details": {"hardware_class": status.performance.hardware_class, "store": "isolated", "eps": found,
                        "rocm_version": rocm_version()}}


# --------------------------------------------------------------------------------------------
# Section 4
# --------------------------------------------------------------------------------------------


def remember(work: Path, path: Path) -> None:
    """Add a file to the list that the frame deletes at the end, before the file exists: a timeout still deletes it."""
    listed = read_json(work / REMOVE_LIST) or []
    (work / REMOVE_LIST).write_text(json.dumps([*listed, str(path)]), encoding="utf-8")


def fetch_models(models, root: Path, work: Path) -> list[dict]:
    """Put each file of the catalog list `models` (`path`, `url`, `sha256`, `bytes`) at `root / path`.

    A file that is there with the right sha256 is used and kept. A file that is there with an other
    sha256 is not touched. A downloaded file with an other sha256 is deleted. Each downloaded file is
    on the remove list of the frame.
    """
    from skellytracker.core.eps import _download

    found = []
    for item in models:
        relative = Path(item["path"])
        row = {"path": relative.as_posix(), "bytes": item.get("bytes")}
        if relative.is_absolute() or ".." in relative.parts:
            found.append({**row, "state": "refused", "reason_code": "bad-path"})
            continue
        target = root / relative
        if target.is_file():
            ok = _download.sha256_of(target) == item["sha256"]
            found.append({**row, "state": "present" if ok else "wrong-file", "reason_code": None if ok else "hash-mismatch"})
            continue
        remember(work, target)
        try:
            part = _download.fetch(item["url"], item["sha256"], work / "partial" / f"{item['sha256']}.part")
            if _download.sha256_of(part) != item["sha256"]:  # the gate, whatever the fetch checked
                part.unlink()
                raise _download.DownloadError("hash-mismatch", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(part, target)
            found.append({**row, "state": "downloaded", "reason_code": None})
        except _download.DownloadError as error:
            found.append({**row, "state": "failed", "reason_code": error.code})
    return found


def pipeline_downloads(options: dict) -> tuple[tuple[str, int], ...]:
    sys.path.insert(0, str(REPO_ROOT))
    from skellytracker.core.eps.catalog import load_catalog

    settings = load_catalog().data["certification"]
    return (("the certification test image", settings["image"]["bytes"]),
            *((Path(m["path"]).name, m["bytes"]) for m in settings.get("models") or () if not (MODEL_ROOT / m["path"]).is_file()))


def time_run(pipeline: str, execution_provider: str, cameras: int, image, device: str | None = None) -> dict:
    """The timing of `certification.time_run()` of the package, with `not-available` for a VRAM value that no reader gives."""
    from skellytracker.core.eps import certification

    found = certification.time_run(pipeline, execution_provider, cameras, image, device)
    return {name: "not-available" if value is None and name.endswith("_mib") else value for name, value in found.items()}


def section_full(work: Path) -> dict:
    """Section 4: the model files of the `certification` block, then `skellytracker.certify("full")` with the default selection."""
    sys.path.insert(0, str(REPO_ROOT))
    if not isolated():
        return not_isolated()
    import skellytracker
    from skellytracker.core.eps.catalog import load_catalog

    details = {"models": fetch_models(load_catalog().data["certification"].get("models") or (), MODEL_ROOT, work)}

    def show(message: dict) -> None:
        if message["step"]:
            print(f"section 4: {message['step']['name']}", file=sys.stderr, flush=True)

    try:
        report = skellytracker.certify("full", show)
    except Exception as error:  # noqa: BLE001 - for example a pipeline file that does not load
        return {"result": "fail", "reason_code": type(error).__name__, "summary": "certify('full') raised", "checks": [],
                "details": details}
    checks = report["checks"]
    counts = Counter(c["result"] for c in checks)
    summary = f"{len(checks)} checks of certify('full'): " + ", ".join(
        f"{counts[result]} {result}" for result in ("pass", "fail", "not-run", "record-only") if counts[result])
    return {"result": outcome(checks), "reason_code": next((c["reason"] for c in checks if c["result"] == "fail"), None),
            "summary": summary, "checks": [], "details": details, "report": report}
