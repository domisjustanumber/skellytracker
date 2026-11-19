"""`certify()`: test one EP on this host, and write a report file. The report does not leave the host.

The probe is `verify()` at level L3. The wider run is the pipeline of `certification.pipeline` of
the EP catalog on one public test image, on the EP and on the CPU EP of this host. Each runs in its
own `spawn` child process, so an EP that ends or hangs its process gives a report. The report holds
versions, the GPU model and results. It holds no hostname, no path, no serial number and no user id.
A failure is a fixed reason code, because an error text can hold a path.

The `result` of a report is `pass`, `fail` (the EP ran and failed) or `not-run` (a setup step
failed before the EP ran, for example a pack that is not installed or a failed download). Only
`pass` and `fail` store an answer that ends the prompt. When the ONNX files of the pipeline are
not on this host, the wider run does not run (`models-missing`), and the result comes from the
probe only.
"""

import json
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path

import skellytracker
from skellytracker.core.eps import _download, evidence, store, verification
from skellytracker.core.eps.catalog import EpCatalog, load_catalog
from skellytracker.core.eps.recommendation import ep_gpus
from skellytracker.core.eps.records import USABLE_STATES, CertifyOffer, CertifyResult
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import probe_host
from skellytracker.core.system.runtime import probe_runtime

REPORT_SCHEMA = "skellytracker.eps.certification/1"
PARTIAL_PLACEMENT = "ep_partial_placement"  # the warning code of the pipeline runtime; `_runtime` is private
SCORE_MARGIN = 0.1  # not calibrated: fp16 noise near `score_min` must not fail a good EP
SIMILAR_SPEED = 0.2  # `similar`: the warm call on the EP is within 20 % of the warm call on the CPU EP
WARM_CALLS = 2  # extra calls after the first, so that the first-call cost is not the figure; the fastest one is the figure
WIDE_TIMEOUT_SECONDS = 600.0  # not calibrated: the start of the child, two pipeline starts with a TensorRT RTX engine build, two calls


def reports_dir() -> Path:
    return store.store_root() / "reports"


def pair_key(catalog: EpCatalog, key: str, gpu, os_name: str) -> str:
    """The pair of an answer. The pack version is in it, so a pack upgrade asks again.

    `gpu` comes from `ep_gpus()`, which gives only GPUs with PCI ids, so `gpu_id` is never None here. An EP of
    the Windows ML catalog takes the package version of its record, and a built-in EP takes `builtin`.
    """
    pack = catalog.pack(key) or (store.windows_ml_pack(catalog, key) if catalog.windows_ml(key) else {"version": "builtin"})
    return f"{key}|{pack['version']}|{os_name}|{evidence.gpu_id(gpu)}"


def local_result(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """`passed` or `failed`: the last quick check of the EP on this GPU model on this PC, for the pack version of today.

    None with no such check, and for a GPU with no PCI ids. It reads `quick-checks.json` of the EP store.
    """
    if evidence.gpu_id(gpu) is None:
        return None
    row = (store.read_json(store.store_root() / "quick-checks.json") or {}).get(pair_key(catalog, key, gpu, os_name))
    return row["result"] if isinstance(row, dict) and row.get("result") in ("passed", "failed") else None


def read_answers() -> dict:
    """The stored answer or result of each pair: `dismissed`, `passed` or `failed`."""
    return store.read_json(store.store_root() / "certify.json") or {}


def write_answer(pair: str, answer: str) -> None:
    with store.store_lock():
        store.write_json(store.store_root() / "certify.json", {**read_answers(), pair: answer})


def certify_offers(catalog: EpCatalog, host) -> tuple[CertifyOffer, ...]:
    """One offer for each usable plugin EP of this host that `ep_evidence.yaml` does not certify. It loads no library."""
    answers, offers = read_answers(), []
    for key in catalog.keys():
        if catalog.pack(key) is None:
            continue
        device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
        if gpu is None or evidence.certified(key, gpu, host.os_name):
            continue
        if store.pack_state(catalog, key, gpu, device_key, host.os_build)[0] not in USABLE_STATES:
            continue
        offers.append(CertifyOffer(key, catalog.ep(key)["display_name"], device_key, gpu.name,
                                   catalog.data["certification"]["seconds"].get(key, 0),
                                   prompt=pair_key(catalog, key, gpu, host.os_name) not in answers))
    return tuple(offers)


def dismiss_certification(key: str) -> None:
    """Store the answer "do not ask again" for the EP `key` on the GPU of this host. The offer stays, with `prompt` false."""
    catalog, host = load_catalog(), probe_host()
    _, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
    if gpu is not None:
        write_answer(pair_key(catalog, key, gpu, host.os_name), "dismissed")


def speed_against_cpu(ep_ms: float, cpu_ms: float) -> str:
    """`faster`, `slower` or `similar` (within `SIMILAR_SPEED` of the CPU time). It is a record only: it never fails an EP."""
    if abs(ep_ms - cpu_ms) <= SIMILAR_SPEED * cpu_ms:
        return "similar"
    return "faster" if ep_ms < cpu_ms else "slower"


def compare_results(cpu: dict, ep: dict, thresholds: dict) -> dict:
    """Compare the pipeline result of the EP with the result of the CPU EP on one image.

    The rule: the same count of present rows, at least one; each box IoU at least `box_iou_min`;
    no NaN in the EP result where the CPU result is finite; each point with a CPU score of
    `score_min` or more has an EP score of `score_min - SCORE_MARGIN` or more; each point with a
    score of `score_min` or more in the two results within `keypoint_box_fraction_max` of the diagonal
    of the CPU box of its row. The limit is a part of the box size, because the decode step of a
    keypoint model has a pixel size that grows with the person. The result holds the worst values
    and a reason code.
    """
    import numpy as np

    found = {"people_cpu": int(cpu["boxes"].present.sum()), "people_ep": int(ep["boxes"].present.sum()),
             "box_iou_min": None, "keypoint_px_max": None, "keypoint_box_fraction_max": None,
             "keypoint_box_fraction_median": None, "keypoint_box_fraction_p99": None, "points_compared": 0,
             "ok": False, "reason_code": None}
    present = cpu["boxes"].present
    if found["people_cpu"] == 0:
        return {**found, "reason_code": "no-person-on-cpu"}
    if not np.array_equal(present, ep["boxes"].present) or not np.array_equal(cpu["wholebody"].present, ep["wholebody"].present):
        return {**found, "reason_code": "people-differ"}
    a, b = cpu["boxes"].xyxy[present], ep["boxes"].xyxy[present]
    overlap = np.clip(np.minimum(a[:, 2:], b[:, 2:]) - np.maximum(a[:, :2], b[:, :2]), 0, None).prod(axis=1)
    union = (a[:, 2:] - a[:, :2]).prod(axis=1) + (b[:, 2:] - b[:, :2]).prod(axis=1) - overlap
    found["box_iou_min"] = float((overlap / union).min())
    rows = cpu["wholebody"].present
    cpu_score, ep_score = cpu["wholebody"].score[rows], ep["wholebody"].score[rows]
    cpu_xy, ep_xy = cpu["wholebody"].xy[rows], ep["wholebody"].xy[rows]
    lost = (np.isfinite(cpu_score) & ~np.isfinite(ep_score)).any() or (np.isfinite(cpu_xy) & ~np.isfinite(ep_xy)).any()
    both = (cpu_score >= thresholds["score_min"]) & (ep_score >= thresholds["score_min"])
    distance = np.linalg.norm(cpu_xy - ep_xy, axis=-1)
    fraction = (distance / np.hypot(*(cpu["boxes"].xyxy[rows, 2:] - cpu["boxes"].xyxy[rows, :2]).T)[:, None])[both]
    distance = distance[both]
    found["points_compared"] = int(both.sum())
    found["keypoint_px_max"] = float(distance.max()) if distance.size else None
    found["keypoint_box_fraction_max"] = float(fraction.max()) if distance.size else None
    found["keypoint_box_fraction_median"] = float(np.median(fraction)) if distance.size else None
    found["keypoint_box_fraction_p99"] = float(np.percentile(fraction, 99)) if distance.size else None
    if lost or not np.isfinite(found["box_iou_min"]) or (distance.size and not np.isfinite(distance).all()):
        return {**found, "reason_code": "not-finite"}
    if found["box_iou_min"] < thresholds["box_iou_min"]:
        return {**found, "reason_code": "box-differs"}
    if ((cpu_score >= thresholds["score_min"]) & (ep_score < thresholds["score_min"] - SCORE_MARGIN)).any():
        return {**found, "reason_code": "scores-differ"}
    if not distance.size:
        return {**found, "reason_code": "no-point-to-compare"}
    if not found["keypoint_box_fraction_max"] <= thresholds["keypoint_box_fraction_max"]:
        return {**found, "reason_code": "keypoints-differ"}
    return {**found, "ok": True}


def _wide_run(key: str, settings: dict, progress: Callable[[str], None], device_key: str | None = None, *,
              cancel: threading.Event | None = None, timeout: float = WIDE_TIMEOUT_SECONDS,
              grace: float = verification.EXIT_GRACE_SECONDS) -> dict:
    """Run `_image_run()` in a `spawn` child, so that an EP that ends or hangs the process gives a reason code.

    This process loads no EP library and no pipeline for it. `progress` gets the steps of the child. A child
    that gives no result gives `ok` false and the reason code `timed-out`, `cancelled`, `crashed` (with
    `exit_code`) or `no-result`. `ran` is true when the child got to the step `ep`, except for `cancelled`.
    An error in the child gives its exception class name as the reason code. A result keeps
    `exit_reason_code`: None, or `hung-at-exit` or `crashed` when the child did not exit cleanly after it.
    """
    steps = []

    def relay(step: str) -> None:
        steps.append(step)
        progress(step)

    found, problem, exit_code = verification.spawn_child(_wide_child, (key, settings, device_key), timeout=timeout,
                                                         grace=grace, cancel=cancel, progress=relay)
    ran = steps[-1:] == ["ep"]
    if found is None:
        return {"ran": ran and problem != "cancelled", "ok": False, "reason_code": problem,
                **({"exit_code": exit_code} if problem == "crashed" else {})}
    if "error" in found:
        found = {"ran": ran, "ok": False, "reason_code": found["error"]}
    return {**found, "exit_reason_code": problem}


def _wide_child(key: str, settings: dict, device_key: str | None, connection) -> None:
    """The child of `_wide_run()`: it sends each step, then the result, or `{"error": <exception class name>}`."""
    try:
        result = _image_run(key, settings, connection.send, device_key)
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def _image_run(key: str, settings: dict, progress: Callable[[str], None], device_key: str | None = None) -> dict:
    """Run the certification pipeline on the test image on the CPU EP and on the EP `key`, and compare.

    `settings["pipeline"]` is a key of the pipeline catalog, or the mapping of a config (`export_pipeline()`):
    the caller checks the model files of a mapping. `device_key` selects the GPU of the EP run; with None, the
    run uses the default GPU of the EP. It runs in the child of `_wide_run()`.

    `ep_ms` and `cpu_ms` are the fastest of `WARM_CALLS` calls after the first call on the EP and on the CPU EP, and
    `speed_against_cpu` compares them. They are a rough figure from one image and one camera, a record only.
    """
    import cv2
    import numpy as np

    from skellytracker.core import pipelines

    started, image, source = time.monotonic(), settings["image"], settings["pipeline"]
    if isinstance(source, str) and not pipelines.get_pipeline(source).available:  # no wheel holds the ONNX files
        return {"ran": False, "reason_code": "models-missing"}
    progress("download")
    path = store.cache_root() / "certify" / f"{image['sha256']}.jpg"
    if not (path.is_file() and _download.sha256_of(path) == image["sha256"]):
        path = _download.fetch(image["url"], image["sha256"], path)
    frame = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    config = pipelines.load_pipeline(source)
    results, models, warnings, warm = {}, {}, [], {}
    for name, ep_key in (("cpu", "cpu"), ("ep", key)):
        progress(name)
        with pipelines.start_pipeline(config, camera_ids=[0], running_mode="image", execution_provider=ep_key, timing="off",
                                      device=device_key if name == "ep" else None) as run:
            results[name] = run.process(pipelines.Frame(frame, frame_index=0))
            times = []
            for index in range(1, WARM_CALLS + 1):
                before = time.perf_counter()
                run.process(pipelines.Frame(frame, frame_index=index))
                times.append((time.perf_counter() - before) * 1000)
            warm[name] = round(min(times), 1)
            models, warnings = run.models, sorted({warning.code for warning in run.warnings})
    found = compare_results(results["cpu"], results["ep"], settings["thresholds"])
    if found["ok"] and PARTIAL_PLACEMENT in warnings:  # the warnings of the EP run: some nodes ran on the CPU EP
        found = {**found, "ok": False, "reason_code": "partial-placement"}
    return {**found, "ran": True, "pipeline": source if isinstance(source, str) else f"{config.pipeline_id}@{config.source.name}",
            "image_sha256": image["sha256"], "warnings": warnings, "ep_ms": warm["ep"], "cpu_ms": warm["cpu"],
            "speed_against_cpu": speed_against_cpu(warm["ep"], warm["cpu"]),
            "models": [{field: model[field] for field in ("key", "version", "size", "precision", "execution_provider", "device")}
                       for _, model in sorted(models.items())],
            "thresholds": settings["thresholds"], "seconds": round(time.monotonic() - started, 1)}


def certify(key: str, *, wide: bool = False, out: Path | str | None = None,
            progress: Callable[[str], None] | None = None, cancel: threading.Event | None = None) -> CertifyResult:
    """Test the plugin EP `key` on this host, and write the report file. It sends nothing.

    - The probe always runs: `verify()` at level L3, in a child process. A pass makes the EP `ready`
      on this host.
    - `wide`: also run the certification pipeline on the test image, on the EP and on the CPU EP, in
      a child process. It downloads the test image, and it needs the ONNX files of the pipeline. Ask
      the user before a call with `wide`: `CertifyOffer.seconds` gives the time.
    - `out`: the report file. With None, the file is in the folder `reports` of the EP store.
    - `progress`: a callable that gets the name of each step: `probe`, `download`, `cpu`, `ep`, `report`.
    - `cancel`: an object with `is_set()`, for example a `threading.Event`. When it is set, the
      child of the probe or of the wider run stops within about a second. A cancelled run gives
      `not-run` with `cancelled`.

    It does not raise for an EP that fails: the report then holds the result `fail` or `not-run`
    and the reason code. `exit_reason_code` of `probe` and of `wide` is `hung-at-exit` or `crashed`
    when that child gave its result and then did not exit cleanly; the result stays. A built-in EP
    and an EP with no GPU on this host raise `EpUnavailableError`.
    """
    progress = progress or (lambda step: None)
    catalog, host = load_catalog(), probe_host()
    pack = catalog.pack(key)
    device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
    if pack is None or gpu is None:
        raise EpUnavailableError(f"The EP '{key}' has no pack, or no GPU of this host can use it. A certification needs both.")
    steps = []

    def step(name: str) -> None:
        steps.append(name)
        progress(name)

    step("probe")
    probe = {"ok": False, "level": None, "max_abs_diff": None, "reason_code": None, "exit_reason_code": None}
    outcome = "not-run"
    try:
        (verdict,) = verification.verify([key], force=True, cancel=cancel)
        probe.update(ok=verdict.ok, level=verdict.level, max_abs_diff=verdict.max_abs_diff,
                     reason_code=None if verdict.ok else verdict.reason_code or f"probe-{verdict.level.lower()}-failed",
                     exit_reason_code=verdict.exit_reason_code)
        outcome = "pass" if verdict.ok else "not-run" if verdict.reason_code == "cancelled" else "fail"
    except Exception as error:  # noqa: BLE001 - a setup failure, for example a pack that is not installed or stale
        probe["reason_code"] = type(error).__name__
    wide_result = {"ran": False}
    if wide and outcome == "pass":
        try:
            wide_result = _wide_run(key, catalog.data["certification"], step, cancel=cancel)
        except Exception as error:  # noqa: BLE001 - before the step `ep`, it is a setup failure: the EP did not run
            wide_result = {"ran": steps[-1] == "ep", "ok": False, "reason_code": type(error).__name__}
        if wide_result["ran"] and not wide_result["ok"]:
            outcome = "fail"
        elif wide_result.get("reason_code") not in (None, "models-missing"):
            outcome = "not-run"
    reason = probe["reason_code"] or wide_result.get("reason_code")
    runtime = probe_runtime()  # imports onnxruntime: only here, never at module level
    ort = dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True))
    ort_name = "onnxruntime-windowsml" if "onnxruntime-windowsml" in ort else next(iter(ort), None)
    now = time.gmtime()
    report = {
        "schema": REPORT_SCHEMA, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", now), "result": outcome,
        "reason_code": reason,
        "versions": {"skellytracker": skellytracker.__version__, "ort_distribution": ort_name,
                     "ort_version": ort.get(ort_name), "windowsml": runtime.windowsml_version, "catalog_revision": catalog.revision,
                     "set_hash": evidence.set_hash(catalog)},
        "ep": {"key": key, "pack_id": pack["id"], "pack_version": pack["version"]},
        "host": {"os_name": host.os_name, "os_release": host.os_release, "os_version": host.os_version, "os_build": host.os_build,
                 "os_label": host.os_label, "arch": host.arch},
        "gpu": {"vendor": gpu.vendor, "name": gpu.name, "id": evidence.gpu_id(gpu), "driver_version": gpu.driver_version,
                "compute_capability": None if gpu.nvidia is None else gpu.nvidia.compute_capability},
        "probe": probe, "wide": wide_result,
    }
    progress("report")
    text = json.dumps(report, indent=1)
    slug = re.sub(r"[^a-z0-9]+", "-", (gpu.name or "gpu").lower()).strip("-")
    path = Path(out) if out else reports_dir() / f"{time.strftime('%Y%m%d-%H%M%S', now)}-{key}-{slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    if outcome != "not-run":  # a setup failure keeps the prompt
        write_answer(pair_key(catalog, key, gpu, host.os_name), "passed" if outcome == "pass" else "failed")
    return CertifyResult(key, outcome == "pass", probe["ok"], wide_result.get("ok") if wide_result["ran"] else None, reason, str(path), text)

