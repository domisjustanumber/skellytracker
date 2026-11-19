"""Scratch measurement of `directml` on each GPU of this host (ADR-Z5X7). Not in git.

Usage: python -B dml_measure.py refusal | probe DEVICE_KEY | pipeline DEVICE_KEY
Each mode prints one JSON object. The caller sets SKELLYTRACKER_EP_STORE, SKELLYTRACKER_EP_CACHE and
SKELLYTRACKER_MODEL_CACHE to scratch folders.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.getcwd(), "tools"))


def luid_memory() -> dict:
    """Dedicated and shared GPU memory of this process for each adapter LUID (PDH `GPU Process Memory`)."""
    from skellytracker.core._hardware import windows_pdh

    found = {}
    for counter in ("Dedicated Usage", "Shared Usage"):
        kept = []
        windows_pdh.sum_by_pid = lambda items: kept.extend(items) or {}  # noqa: B023 - keep the instance names; read() runs in this loop pass
        reader = windows_pdh.GpuProcessMemory()
        windows_pdh.COUNTER = rf"\GPU Process Memory(*)\{counter}"
        reader._open()
        reader.read()
        for name, status, value in kept:
            if name.startswith(f"pid_{os.getpid()}_") and status in (0, 1):
                luid = int(name.split("_luid_")[1].split("_phys")[0].split("_")[1], 16)
                found.setdefault(luid, {})[counter] = found.setdefault(luid, {}).get(counter, 0) + int(value)
    return {str(k): {c: round(v / 2**20, 1) for c, v in d.items()} for k, d in found.items()}


def main() -> None:
    mode = sys.argv[1]
    from skellytracker.core import eps
    from skellytracker.core.eps import store
    from skellytracker.core.errors import EpUnavailableError

    out = {"mode": mode}
    if mode == "refusal":
        out["store_has_opt_in"] = sorted(store.field_test_opt_ins())
        try:
            eps.check_start("directml")
            out["check_start"] = "no error"
        except EpUnavailableError as error:
            out["check_start"] = f"{type(error).__name__}: {error}"
        status = eps.status()
        row = next(r for r in status.eps if r.key == "directml")
        out["status_row"] = {"state": row.state, "reason_code": row.reason_code, "usable": row.usable, "catalog_status": row.catalog_status,
                             "install_hint": row.install_hint, "devices": [d.device_key for d in row.devices]}
        perf = status.performance
        out["recommend"] = {"class": perf.hardware_class, "chosen": perf.chosen.ep_key, "device": perf.chosen.device_key,
                            "skipped": [c.ep_key for c in perf.skipped], "offers": [o.kind for o in perf.offers], "precision": perf.precision}
        try:
            from skellytracker.core import pipelines

            config = pipelines.load_pipeline("yolox-rtmw-wholebody@skellytracker")
            pipelines.start_pipeline(config, camera_ids=[0], running_mode="image", execution_provider="directml")
            out["start_pipeline"] = "no error"
        except EpUnavailableError as error:
            out["start_pipeline"] = f"{type(error).__name__}: {error}"
        print(json.dumps(out))
        return
    device = sys.argv[2]
    store.opt_in_field_test("directml")
    if mode == "probe":
        started = time.monotonic()
        (verdict,) = eps.verify(["directml"], level="L3", device_key=device, force=True)
        out.update(level=verdict.level, ok=verdict.ok, max_abs_diff=verdict.max_abs_diff, reason=verdict.reason,
                   seconds=round(time.monotonic() - started, 1))
        print(json.dumps(out))
        return
    import cv2
    import numpy as np

    import certify_eps
    from skellytracker.core import pipelines
    from skellytracker.core.eps import _download, certification

    settings = eps.load_catalog().data["certification"]
    image = settings["image"]
    path = store.cache_root() / "certify" / f"{image['sha256']}.jpg"
    if not (path.is_file() and _download.sha256_of(path) == image["sha256"]):
        path = _download.fetch(image["url"], image["sha256"], path)
    frame = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    out["memory_before"] = luid_memory()
    config = pipelines.load_pipeline(settings["pipeline"])
    with pipelines.start_pipeline(config, camera_ids=[0], running_mode="image", execution_provider="directml", timing="off",
                                  device=device) as run:
        run.process(pipelines.Frame(frame, frame_index=0))
        out["memory_with_sessions"] = luid_memory()
        out["models"] = {node: {k: m[k] for k in ("precision", "execution_provider", "device")} for node, m in run.models.items()}
        out["sessions"] = {node: [{"ep_device_id": r.ep_device_id, "device_key": r.device_key, "device_name": r.device_name,
                                   "nodes_by_ep": dict(r.nodes_by_ep), "cpu_nodes": r.cpu_nodes, "cpu_op_types": list(r.cpu_op_types),
                                   "build_ms": round(r.build_ns / 1e6), "precision": r.precision}
                                  for r in reports] for node, reports in run._executor.reports.items()}
        out["warnings"] = sorted({w.code for w in run.warnings})
    wide = certification._wide_run("directml", settings, lambda step: None, device)
    out["agreement"] = {k: wide.get(k) for k in ("ok", "reason_code", "box_iou_min", "keypoint_px_max", "keypoint_box_fraction_max",
                                                  "keypoint_box_fraction_median", "keypoint_box_fraction_p99", "points_compared",
                                                  "people_cpu", "people_ep", "warnings", "models", "seconds")}
    out["timing_1_camera"] = certify_eps.time_run(settings["pipeline"], "directml", 1, frame, device)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
