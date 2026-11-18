"""Sections 3 and 4 of the certify suite (``tools/certify_platform.py``): the EPs, and the pipeline on each EP.

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
on Windows) gets that probe on each GPU of the host, as the check ``KEY@DEVICE_KEY``. Its result
counts (``pass`` or ``fail``) only on a GPU whose hardware class lists the EP (an AMD GPU for
``directml``). On each other GPU the check is ``record-only``, and the details hold the probe result
(ADR-Y14H item 11). An AMD GPU adds the check ``amd-eps``: ``not-run``, ``not-built``, for the AMD
EPs that the suite does not build yet (MIGraphX and the AMD EP of the Windows ML catalog).

Section 4. It reads the result of section 3 from ``section-3.json`` of the work folder. It takes the
model files of the ``models`` list of the ``certification`` block of the EP catalog (``fetch_models``)
and needs the pipeline of that block to be available, else it is ``not-run`` with
``models-missing``. For the CPU EP (1 camera), and for each GPU EP and each ``directml`` GPU whose
probe passed in section 3 (``pipeline_targets`` of its details; 1, 3 and 6 cameras, the test image
on each camera), it times ``WARMUP_CALLS`` and then ``TIMED_CALLS`` calls
in the running mode ``video`` with the span ``pipeline.run``: the start time (the sessions, with the
TensorRT RTX engine build), the first call, and the median and p95 of the timed calls. The peak VRAM
is the largest VRAM of this process in a ``LiveSampler`` sample after each call. Then
``certification._wide_run()`` compares the EP with the CPU EP on the test image with the catalog
``thresholds``. The timings and the VRAM are ``record-only``. The agreement is ``pass`` or ``fail``.
It is ``record-only`` on a GPU where the result of section 3 does not count.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import statistics
import sys
import time
from pathlib import Path

from certify_platform import check, outcome

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = REPO_ROOT / "skellytracker" / "core" / "model_zoo"
REMOVE_LIST = "remove-at-end.json"  # the frame deletes each file of this list at the end of the run
WARMUP_CALLS, TIMED_CALLS, CAMERA_COUNTS = 10, 100, (1, 3, 6)  # about 60 s for section 4 with two GPU EPs on an RTX 3070
MIB = 2**20


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
    return tuple((wheel["filename"], wheel["download_bytes"]) for key in catalog.keys() if ep_gpus(catalog, key, host)
                 for wheel in (catalog.pack_lock(catalog.pack(key)["id"]) or {}).get("wheels", ()))


def test_builtin(key: str, device_key: str | None = None) -> dict:
    from skellytracker.core import eps

    try:
        (verdict,) = eps.verify([key], level="L3", device_key=device_key, force=True)
    except Exception as error:  # noqa: BLE001 - a finding with a fixed code
        return {"result": "fail", "reason_code": type(error).__name__}
    return {"result": "pass" if verdict.ok else "fail", "reason_code": None if verdict.ok else f"probe-{verdict.level.lower()}-failed",
            "probe": {"ok": verdict.ok, "level": verdict.level, "max_abs_diff": verdict.max_abs_diff}}


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
    facts.update(certify_result=report["result"], probe=report["probe"], gpu=report["gpu"], versions=report["versions"])
    passed = report["result"] == "pass"
    return {**facts, "result": "pass" if passed else "fail",
            "reason_code": None if passed else report["reason_code"] or f"certify-{report['result']}"}


def offered_on(key: str, host, gpu) -> bool:
    """True when the hardware class of this one GPU lists the EP: the app offers it there, so its result counts."""
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.eps.recommendation import hardware_class

    return key in hardware_class(load_catalog(), dataclasses.replace(host, gpus=(gpu,)))["candidates"]


def section_eps(work: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    if not isolated():
        return not_isolated()
    from skellytracker.core import eps
    from skellytracker.core.eps import store
    from skellytracker.core.system.host import gpu_device_keys

    wheel_dir = (read_json(work / "options.json") or {}).get("wheel_dir")
    catalog = eps.load_catalog()
    for key in catalog.keys():  # the opt-in of the suite, in its own store: the frame deletes it at the end (ADR-Z5X7)
        if catalog.ep_status(key) == "field-test":
            store.opt_in_field_test(key)
    status = eps.status()
    rows, gpus = {row.key: row for row in status.eps}, dict(gpu_device_keys(status.host))
    checks, found, targets = [], {}, []
    for key in catalog.keys():
        row = rows.get(key)
        if row is None or row.state == "unsupported":  # no row: an EP of an other platform
            found[key] = {"state": "unsupported", "reason_code": "os" if row is None else row.reason_code}
            checks.append(check(key, "not-run", found[key]["reason_code"]))
            continue
        on_each_gpu = row.pack_id is None and catalog.device_row(key) is not None  # `directml`: each GPU of the host
        for device in row.devices if on_each_gpu else (None,):
            name = key if device is None else f"{key}@{device.device_key}"
            counts = device is None or offered_on(key, status.host, gpus[device.device_key])
            print(f"section 3: {name}", file=sys.stderr, flush=True)
            started = time.monotonic()
            if device is not None:
                found[name] = {**test_builtin(key, device.device_key), "vendor": gpus[device.device_key].vendor, "counts": counts}
            else:
                found[name] = test_builtin(key) if row.pack_id is None else test_pack(key, wheel_dir, work)
            found[name]["seconds"] = round(time.monotonic() - started, 1)
            checks.append(check(name, found[name]["result"] if counts else "record-only", found[name]["reason_code"]))
            if found[name]["result"] == "pass" and key != "cpu":
                targets.append({"key": key, "device_key": None if device is None else device.device_key, "counts": counts})
    if any(gpu.vendor == "amd" for gpu in status.host.gpus):
        checks.append(check("amd-eps", "not-run", "not-built", eps=["migraphx", "windows-ml-amd"]))
    tested = [c for c in checks if c["result"] != "not-run"]
    summary = ", ".join(f"{c['name']} {c['result']}" for c in tested) + f"; {len(checks) - len(tested)} not run"
    return {"result": outcome(checks), "reason_code": first_failure(checks), "summary": summary, "checks": checks,
            "details": {"hardware_class": status.performance.hardware_class, "store": "isolated", "eps": found,
                        "pipeline_targets": targets}}


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


def process_vram(sampler, pid: int) -> int | None:
    """The VRAM bytes of this process: Windows PDH, or NVML per process on Linux; None when no reader gives it."""
    sample = sampler.sample([pid])
    values = [p.vram_used_bytes for p in sample.processes if p.pid == pid]
    values += [row.vram_used_bytes for gpu in sample.gpus for row in (gpu.processes or ()) if row.pid == pid]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def mib(value: int | None):
    return "not-available" if value is None else round(value / MIB)


def time_run(pipeline: str, execution_provider: str, cameras: int, image, device: str | None = None) -> dict:
    """Start the pipeline, run the warm-up and the timed calls, and give the times of the span `pipeline.run`."""
    from skellytracker.core import pipelines
    from skellytracker.core.metrics import LiveSampler
    from skellytracker.core.pipelines.timing import duration_ms

    config = pipelines.load_pipeline(pipeline)
    config.instrumentation.timing_spans = ["pipeline.run"]
    events, sampler, pid, ids = [], LiveSampler(), os.getpid(), list(range(cameras))
    before = process_vram(sampler, pid)
    peak = before
    started = time.perf_counter()
    with pipelines.start_pipeline(config, camera_ids=ids, running_mode="video", execution_provider=execution_provider,
                                  timing_sink=events.append, device=device) as run:
        start_seconds = time.perf_counter() - started
        for index in range(WARMUP_CALLS + TIMED_CALLS):
            run.process_batch({camera: pipelines.Frame(image, frame_index=index) for camera in ids})
            # shortcut: a sample after each call, not during it; the ONNX Runtime arenas keep their peak, so it is close
            now = process_vram(sampler, pid)
            peak = now if peak is None else max(peak, now or 0)
    calls = [duration_ms(event) for event in events if event.get("node_id") == "pipeline"]
    timed = sorted(calls[WARMUP_CALLS:])
    return {"cameras": cameras, "start_seconds": round(start_seconds, 2), "first_call_ms": round(calls[0], 1),
            "calls": len(timed), "median_ms": round(statistics.median(timed), 2),
            "p95_ms": round(timed[min(len(timed) - 1, round(0.95 * (len(timed) - 1)))], 2),
            "vram_before_mib": mib(before), "peak_vram_mib": mib(peak)}


AGREEMENT_FIELDS = ("box_iou_min", "keypoint_box_fraction_max", "keypoint_box_fraction_median", "keypoint_box_fraction_p99",
                    "points_compared")


def section_pipeline(work: Path) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    if not isolated():
        return not_isolated()
    import cv2
    import numpy as np

    from skellytracker.core import pipelines
    from skellytracker.core.eps import _download, certification, store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system import probe_loaded_libraries

    settings = load_catalog().data["certification"]
    details = {"models": fetch_models(settings.get("models") or (), MODEL_ROOT, work), "pipeline": settings["pipeline"],
               "calls": {"warmup": WARMUP_CALLS, "timed": TIMED_CALLS, "running_mode": "video"}, "eps": {}}
    if not pipelines.get_pipeline(settings["pipeline"]).available:
        return {"result": "not-run", "reason_code": "models-missing", "summary": "a model file of the pipeline is absent",
                "checks": [], "details": details}
    targets = ((read_json(work / "section-3.json") or {}).get("details") or {}).get("pipeline_targets") or []
    details["eps_from_section_3"] = [t["key"] if t["device_key"] is None else f"{t['key']}@{t['device_key']}" for t in targets]
    image = settings["image"]
    path = store.cache_root() / "certify" / f"{image['sha256']}.jpg"  # the cache of _wide_run(): in the work folder
    try:
        if not (path.is_file() and _download.sha256_of(path) == image["sha256"]):
            path = _download.fetch(image["url"], image["sha256"], path)
    except _download.DownloadError as error:
        return {"result": "not-run", "reason_code": f"image-{error.code}", "summary": "the test image did not download",
                "checks": [], "details": details}
    frame = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    checks, seen = [], set()
    for target in ({"key": "cpu", "device_key": None, "counts": True}, *targets):
        key, device = target["key"], target["device_key"]
        label = key if device is None else f"{key}@{device}"
        found = details["eps"][label] = {"timing": {}, "device_key": device, "counts": target["counts"]}
        for cameras in (1,) if key == "cpu" else CAMERA_COUNTS:
            print(f"section 4: {label}, {cameras} camera(s)", file=sys.stderr, flush=True)
            try:
                found["timing"][str(cameras)] = time_run(settings["pipeline"], key, cameras, frame, device)
                checks.append(check(f"timing-{label}-{cameras}", "record-only"))
            except Exception as error:  # noqa: BLE001 - for example VRAM exhaustion at 6 cameras
                checks.append(check(f"timing-{label}-{cameras}", "not-run", type(error).__name__))
        libraries = probe_loaded_libraries()
        loaded = [*libraries.libraries, *(libraries.nvidia.libraries if libraries.nvidia else ())]
        found["libraries_new"] = [{"name": lib.name, "version": lib.version} for lib in loaded if lib.name not in seen]
        seen |= {lib.name for lib in loaded}
        if key == "cpu":
            continue
        print(f"section 4: {label}, agreement with the CPU EP", file=sys.stderr, flush=True)
        try:
            wide = certification._wide_run(key, settings, lambda step: None, device)
        except Exception as error:  # noqa: BLE001
            wide = {"ran": False, "ok": False, "reason_code": type(error).__name__}
        found["agreement"] = wide
        result = ("pass" if wide.get("ok") else "fail") if target["counts"] else "record-only"  # ADR-Y14H item 11
        checks.append(check(f"agreement-{label}", result, wide.get("reason_code"), **{field: wide.get(field) for field in AGREEMENT_FIELDS}))
    agreements = [f"{c['name'].removeprefix('agreement-')} IoU {c['box_iou_min']:.3f}, keypoints max {c['keypoint_box_fraction_max']:.4f}"
                  for c in checks if c["name"].startswith("agreement-") and c["box_iou_min"] is not None
                  and c["keypoint_box_fraction_max"] is not None]
    summary = "; ".join(agreements) if agreements else "no GPU EP passed section 3: CPU EP timings only"
    result = outcome(checks)
    return {"result": result, "reason_code": first_failure(checks), "summary": summary, "checks": checks, "details": details}
