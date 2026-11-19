"""`certify()` and `certify_plan()`: the certification functions of the whole package (ADR-P0JZ, ADR-21BK).

    import skellytracker
    plan = skellytracker.certify_plan("quick")          # show the plan, then get the consent of the user
    report = skellytracker.certify("quick", progress=show, cancel=event)

The hand-in list (ADR-21BK item 5) holds each report of `certify()` on this host with a check that ran:

    for row in skellytracker.pending_reports():         # the reports that the user did not hand in
        report = skellytracker.read_report(row["report_id"])
    skellytracker.mark_reports(ids, "covered", reference=issue_url)   # or "opened", or "pending"

This package sends nothing and makes no report file for a person: the application builds the file from
the module reports, shows it, hands it in and then marks the reports. A report with a failed check is
always worth an offer (`has_failure`). A pass alone gives no prompt. A new report of a quick check deletes
each older report of a pass that it repeats, when the user did not hand that report in.

The two functions are `skellytracker.certify` and `skellytracker.certify_plan`. They obey the contract
`report-format.md` of the repository `skellycertify`, format `skellycertify.report/1.0.0`. The reason codes
of this package are in `skellytracker/REASON_CODES.md`. A plain `import skellytracker` imports this
module only: it imports `eps`, `pipelines` and ONNX Runtime in the function bodies.

The result is a plain `dict`, not a frozen record of `eps`, because the contract fixes a JSON object.
"""

import importlib.metadata
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

SCHEMA = "skellycertify.report/1.0.0"
PACKAGE = "skellytracker"
LEVELS = ("quick", "full")
REPORT_STATES = ("pending", "opened", "covered")  # `opened`: the user saved the file and opened the issue form; `covered`: an issue holds it
REPORT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
PROBE_SECONDS = 15  # not calibrated: the time estimate of one L3 probe; the catalog gives the time of the image run
IMAGE_SECONDS = 30  # not calibrated: the time estimate of an image run for an EP that has no `certification.seconds`
JPEG_SECONDS = 5  # not calibrated: the time estimate of the two JPEG checks; 1.0 to 1.3 s on one RTX 3070
JPEG_TIMEOUT_SECONDS = 120.0
JPEG_EPS = ("cuda", "trt-rtx")  # `GPU_FRAME_EPS` of `core/decode/certification.py`; a test checks that they agree
JPEG_CHECKS = ("jpeg-decode", "jpeg-preprocess")  # the names of `run_jpeg_quick_checks()`, in its order
PROGRESS_INTERVAL = 0.1  # the contract allows at most 10 progress messages each second
RUNNABLE_STATES = ("builtin", "ready", "installed_unverified", "untested-ort", "not_ready", "field_test")
COMPARED_OUTPUTS = ("boxes", "wholebody")  # the outputs that `compare_results()` compares
CHILD_FAILURES = {"timed-out": "timed-out", "crashed": "crashed", "no-result": "crashed"}  # a child with no result
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
                    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
OS_NAMES = {"Darwin": "macOS"}
ARCHES = {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}
PATH_PATTERN = re.compile(r"(?:\b[A-Za-z]:[\\/]|\\\\[^\\\s]|/(?:home|Users|root)/|~[\\/])[^\s\"'|,;]*")
IMAGE_NUMBERS = ("people_cpu", "people_ep", "box_iou_min", "keypoint_px_max", "keypoint_box_fraction_max",
                 "keypoint_box_fraction_median", "keypoint_box_fraction_p99", "points_compared", "seconds", "ep_ms", "cpu_ms",
                 "speed_against_cpu")


def certify_plan(level: str, *, execution_providers: Sequence[str] | None = None, device: str | Sequence[str] | None = None,
                 pipeline=None) -> dict:
    """The plan of a `certify()` call with the same arguments. It loads no GPU library and downloads nothing.

    `downloads` names the test image of the quick level when it is not on this host. `details.checks` gives the
    name of each EP check, one for each EP and GPU. The quick level installs nothing: `details.not_run` gives each
    of them that will not run, with its reason code, for example `ep-not-installed`. `system_changes` and
    `questions` are empty. `pipeline` does not change the plan.
    """
    _check_level(level)
    plan = {"package": PACKAGE, "kind": level, "seconds_estimate": 0, "downloads": [], "system_changes": [], "questions": []}
    if level == "full":
        return plan
    from skellytracker.core.eps import store
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    settings = catalog.data["certification"]
    selected = _selection(catalog, host, execution_providers, device)
    runnable = [key for _, key, _, _, reason in selected if reason is None]
    plan["seconds_estimate"] = sum(PROBE_SECONDS + settings["seconds"].get(key, IMAGE_SECONDS) + JPEG_SECONDS * (key in JPEG_EPS)
                                   for key in runnable)
    if runnable and not _image_path(store, settings).is_file():
        plan["downloads"].append({"name": settings["image"]["url"].rsplit("/", 1)[1], "bytes": settings["image"]["bytes"]})
    plan["details"] = {"execution_providers": list(dict.fromkeys(key for _, key, *_ in selected)),
                       "checks": [label for label, *_ in selected],
                       "not_run": {label: reason for label, _, _, _, reason in selected if reason}}
    return plan


def certify(level: str, progress: Callable[[dict], object] | None = None, cancel=None, *,
            execution_providers: Sequence[str] | None = None, device: str | Sequence[str] | None = None, pipeline=None) -> dict:
    """Run the certification checks of this package at `level`, and return the module report.

    - `level`: `quick` or `full`. Each other value raises `ValueError`. The level `full` is not built
      here: it is `tools/certify_platform.py` today. `certify("full")` returns a report with the
      check `full` as `not-run` and `not-built`.
    - `progress`: a callable that gets each progress message, a `dict` with the complete state, at most
      10 times a second. If it raises, it gets no other message, and the run continues.
    - `cancel`: an object with `is_set()`. A set cancel stops the running child process within about a
      second. Each check that did not end is `not-run` with `cancelled`.
    - `execution_providers`: the EP keys to check. The default is each GPU EP of this host with no
      reviewed row in `ep_evidence.yaml` for the GPU model and OS: each usable plugin EP, and also
      `directml` and each EP of the Windows ML catalog (the `field-test` EPs with no pack), and `coreml`
      on a Mac. An unknown or reserved key raises `EpRequestError` (a `ValueError`).
    - `device`: one device key or a list of device keys, as in `run_devices()`: the GPUs to check on. The
      default is each GPU that the EP can use. In the default selection, a GPU with a reviewed row is not
      checked. A key that is not a GPU of this host raises `EpRequestError`. A named EP that cannot use
      a named GPU is `not-run` with `gpu-not-usable`.
    - `pipeline`: the pipeline of the user, as a `PipelineConfig`, a key of the pipeline catalog or a
      path. The default is `certification.pipeline` of the EP catalog. A config that does not load
      raises, as `load_pipeline()` does.

    The quick check of one EP runs the L3 probe (`verify()`) and then the pipeline on one test image
    on the EP and on the CPU EP, each in a `spawn` child, and compares the two results with the
    thresholds of `certification` of the EP catalog. It runs one time for each GPU of the selection.
    It downloads no model: with a model file that is not on this host, the image check is `not-run`
    with `models-missing`. The `numbers` of `<key>:image` also hold `ep_ms`, `cpu_ms` and
    `speed_against_cpu` (`faster`, `slower` or `similar`): a rough figure from one image, a record only
    that never changes the result. Each EP on each GPU gives three checks: `<ep>:probe`, `<ep>:image` and
    `<ep>`. `<ep>` is `<key>@<device>`, for example `cuda@10de-2484-0`: the EP key and the device key of
    the GPU with no `gpu:` and with `-` for `:`. It is `<key>` alone for an EP with no GPU to run on, and
    for `coreml`: it runs on the chip of the Mac and selects no GPU. The key of its stored result is the chip
    name, and `details.eps.coreml.gpu` gives it, for example `chip:apple-m2-pro` (ADR-ER5X item 6).
    Thus the name of an EP check has no `:`. `details.eps.<ep>.device` gives the device key. The
    check `<ep>` passes only when the two others pass (ADR-21BK item 2). On `cuda` and `trt-rtx`, an EP on
    a GPU also gives `<ep>:jpeg-decode` and `<ep>:jpeg-preprocess`: the two checks of
    `run_jpeg_quick_checks()` of the GPU frame path, in one more `spawn` child, after an image check that
    passed. They never change `<ep>`: a JPEG check that fails stops only the GPU frame path
    (ADR-R53H item 5). An EP that cannot run, for
    example a pack that is not installed, gives `not-run` with `ep-<state code>`. Each EP runs, also
    when an other EP fails.

    Evidence: the item of the quick level is one EP on one GPU of this host. Thus a run of a part of the EPs is
    complete for each EP that it checks, and is not `partial-run`. A run with no EP to check has no
    check and is not valid as evidence (`no-check`). A `quick` report never gives a reviewed row.

    The package cannot see the pipelines of an application, so it never refuses a run with `gpu-busy`:
    the application must not call it while a pipeline holds the GPU.

    It writes in the EP store of the user: the report in the folder `reports`, the verdict of the
    probe, the answer in `certify.json` and the local result of each EP that ran to `pass` or `fail`
    in `quick-checks.json`. A `field-test` EP gets the opt-in during its check. The opt-in stays only
    when the check passes on a GPU (ADR-21BK item 2). The stored result is for the GPU model: two GPUs of one
    model share it, and the last check wins. The row of `quick-checks.json` of `cuda` and `trt-rtx` also holds
    `jpeg`: the result of each of the two JPEG checks. The test image is deleted at the end when this run
    downloaded it.
    """
    _check_level(level)
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.host import probe_host

    catalog, host = load_catalog(), probe_host()
    package, reasons = _package()
    report = {"schema": SCHEMA, "package": package, "kind": level, "created_utc": created, "host": _host(host),
              "checks": [], "cleanup": [], "details": {}}
    sender = _Progress(progress, level)
    if level == "full":
        report["checks"] = [{"name": "full", "result": None, "reason": None}]
        sender.send("starting", None, report["checks"], None)
        report["checks"][0].update(result="not-run", reason="not-built")
        reasons.append("not-built")
    else:
        selected = _selection(catalog, host, execution_providers, device)
        report["checks"] = [{"name": name, "result": None, "reason": None}
                            for label, key, device_key, *_ in selected for name in _names(label, key, device_key)]
        estimates = {f"{label}:probe": PROBE_SECONDS for label, *_ in selected}
        estimates |= {f"{label}:{JPEG_CHECKS[0]}": JPEG_SECONDS for label, *_ in selected}
        estimates |= {f"{label}:image": catalog.data["certification"]["seconds"].get(key, IMAGE_SECONDS) for label, key, *_ in selected}
        sender.estimates = estimates
        resolved = _pipeline(catalog, pipeline) if selected else None  # a config that does not load raises before the start
        sender.send("starting", None, report["checks"], None)
        if selected:
            _quick(report, selected, catalog, host, sender, cancel, resolved)
        else:
            reasons.append("no-check")
        if cancel is not None and cancel.is_set():
            for row in report["checks"]:
                if row["result"] is None:
                    row.update(result="not-run", reason="cancelled")
            reasons.append("cancelled")
    sender.send("cleaning-up", None, report["checks"], None)
    report["evidence"] = {"valid": not reasons, "reasons": reasons}
    report = _scrub(report)
    if level == "quick" and report["checks"]:
        from skellytracker.core.eps import certification

        stem = f"quick-{created.replace('-', '').replace(':', '')}"
        path = certification.reports_dir() / f"{stem}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        for count in range(2, 1000):  # a second report in the same second keeps the first
            if not path.exists():
                break
            path = path.with_name(f"{stem}-{count}.json")
        path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        _prune_reports()
    sender.send("done", None, report["checks"], None)
    return report


def pending_reports(include_handed_in: bool = False) -> list[dict]:
    """The reports of `certify()` on this host that the user did not hand in, the oldest first.

    Each row is `{"report_id", "kind", "created_utc", "has_failure", "evidence_valid", "state", "reference"}`.
    `state` is `pending`, `opened` or `covered`, and `reference` is the text of `mark_reports()`, for example
    the address of the issue, or None. With `include_handed_in`, the list holds each report in each state.
    A report is in the list when a check of it ended `pass` or `fail`. It reads the EP store only.
    """
    from skellytracker.core.eps import certification, store

    marks = store.read_json(_marks_path(store)) or {}
    rows = []
    for path in sorted(certification.reports_dir().glob("*.json")):
        report = store.read_json(path)
        if not isinstance(report, dict) or report.get("schema") != SCHEMA or not REPORT_ID.match(path.stem):
            continue
        results = {check.get("result") for check in report.get("checks", ()) if isinstance(check, dict)}
        if not results & {"pass", "fail"}:
            continue
        mark = marks.get(path.stem) if isinstance(marks.get(path.stem), dict) else {}
        state = mark.get("state") if mark.get("state") in REPORT_STATES else "pending"
        if state == "pending" or include_handed_in:
            rows.append({"report_id": path.stem, "kind": report.get("kind"), "created_utc": report.get("created_utc"),
                         "has_failure": "fail" in results, "evidence_valid": bool((report.get("evidence") or {}).get("valid")),
                         "state": state, "reference": mark.get("reference") if state != "pending" else None})
    return sorted(rows, key=lambda row: (row["created_utc"] or "", row["report_id"]))


def read_report(report_id: str) -> dict:
    """The module report of a row of `pending_reports()`, unchanged. An id that is not in the list raises `ValueError`."""
    from skellytracker.core.eps import certification, store

    report = store.read_json(certification.reports_dir() / f"{report_id}.json") if REPORT_ID.match(str(report_id)) else None
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError(f"{report_id!r} is not a report of this host")
    return report


def mark_reports(report_ids: Sequence[str], state: str, *, reference: str | None = None) -> None:
    """Set the hand-in state of reports: `covered` (an issue holds them), `opened` (the user saved the file and
    opened the issue form) or `pending` (not sent: back in the list).

    `reference` is one text that this package stores and gives back unchanged, for example the address of the
    issue. It applies to each report of the call. `pending` removes a stored reference. An unknown state,
    an id that is not a report of this host, or a `reference` with `pending` raises `ValueError`, and the
    call then changes nothing.
    """
    from skellytracker.core.eps import store

    if isinstance(report_ids, str):
        raise ValueError("report_ids is a list of report ids")
    if state not in REPORT_STATES:
        raise ValueError(f"the state must be one of {', '.join(REPORT_STATES)}, not {state!r}")
    if state == "pending" and reference is not None:
        raise ValueError("a pending report has no reference")
    ids = list(dict.fromkeys(report_ids))
    for report_id in ids:
        read_report(report_id)
    with store.store_lock():
        marks = store.read_json(_marks_path(store)) or {}
        for report_id in ids:
            if state == "pending":
                marks.pop(report_id, None)
            else:
                marks[report_id] = {"state": state, "reference": reference}
        store.write_json(_marks_path(store), marks)


def _prune_reports() -> None:
    """Delete each older report of a pass that a newer report repeats (ADR-ER5X item 7).

    A report stays when it has a failed check, when the user handed it in (`opened` or `covered`), and when
    it is the newest pass of an EP on a GPU. A report with no check that passed is not a report of a pass:
    it stays. A file that this function cannot delete stays.
    """
    from skellytracker.core.eps import certification, store

    with store.store_lock():
        marks = store.read_json(_marks_path(store)) or {}
        found = []
        for path in certification.reports_dir().glob("*.json"):
            report = store.read_json(path)
            if not isinstance(report, dict) or report.get("schema") != SCHEMA or path.stem in marks:
                continue
            checks = [check for check in report.get("checks", ()) if isinstance(check, dict)]
            passed = {check.get("name") for check in checks if check.get("result") == "pass" and ":" not in str(check.get("name"))}
            if passed and not any(check.get("result") == "fail" for check in checks):
                found.append((str(report.get("created_utc") or ""), path.stem, path, passed))
        newer: set = set()
        for _, _, path, passed in sorted(found, key=lambda item: item[:2], reverse=True):
            if passed <= newer:
                try:
                    path.unlink()
                except OSError:
                    pass
            newer |= passed


def note_exit_requested() -> None:
    """The exit notice of an application (ADR-ER5X item 5): the user asked it to close, and it can now end this
    process in any way. Call it in the process that runs the pipelines, before the process ends.

    Without the notice, an end of a process that held a session on a GPU EP, with no clean exit of the
    interpreter, counts as one unclean exit of that EP on that GPU. Two in a row mark the EP as failed on
    this PC, until a quick check passes.
    """
    from skellytracker.core.eps import exits

    exits.note_exit_requested()


def _marks_path(store) -> Path:
    return store.store_root() / "hand-in.json"


def _check_level(level) -> None:
    if level not in LEVELS:
        raise ValueError(f"the level must be 'quick' or 'full', not {level!r}")


class _Progress:
    """The sender of the progress messages: each message is the complete state, at most 10 each second."""

    def __init__(self, callback, kind: str):
        self.callback, self.kind, self.last, self.estimates = callback, kind, 0.0, {}

    def send(self, state: str, step: str | None, checks: list[dict], total: int | None = None) -> None:
        if self.callback is None:
            return
        time.sleep(max(0.0, self.last + PROGRESS_INTERVAL - time.monotonic()))
        self.last = time.monotonic()
        message = {"package": PACKAGE, "kind": self.kind, "state": state, "step": None if step is None else {"name": step},
                   "checks": [{"name": row["name"], "result": row["result"]} for row in checks],
                   "done": sum(row["result"] is not None for row in checks), "total": len(checks) if total is None else total,
                   "seconds_left": sum(self.estimates.get(row["name"], 0) for row in checks if row["result"] is None)}
        try:
            self.callback(message)
        except Exception:  # noqa: BLE001 - the contract: stop calling it, and continue the run
            self.callback = None


def _label(key: str, device_key: str | None) -> str:
    """The name of the check of an EP on a GPU: `cuda@10de-2484-0`. It has no `:`, so each name with `:` is a part of it."""
    return key if device_key is None else f"{key}@{device_key.removeprefix('gpu:').replace(':', '-')}"


def _names(label: str, key: str, device_key: str | None) -> tuple[str, ...]:
    """The check names of an EP on a GPU, in the order of the report. The last name is the EP check."""
    jpeg = tuple(f"{label}:{name}" for name in JPEG_CHECKS) if key in JPEG_EPS and device_key is not None else ()
    return (f"{label}:probe", f"{label}:image", *jpeg, label)


def _selection(catalog, host, execution_providers, device=None) -> list[tuple]:
    """`(label, key, device_key, gpu, reason)` for each EP and GPU to check; `reason` is the code of one that cannot run."""
    from skellytracker.core import errors
    from skellytracker.core.eps import evidence, gate, store
    from skellytracker.core.eps.recommendation import ep_gpus
    from skellytracker.core.eps.records import USABLE_STATES
    from skellytracker.core.system.host import gpu_device_keys

    if isinstance(execution_providers, str):
        raise ValueError("execution_providers is a list of EP keys, for example ['cuda']")
    wanted = None if device is None else [device] if isinstance(device, str) else list(device)
    for item in wanted or ():
        if item not in dict(gpu_device_keys(host)):
            raise errors.EpRequestError(f"{item!r} is not the device key of a GPU of this host")
    default = execution_providers is None
    keys = ([key for key in catalog.keys() if catalog.device_row(key) is not None or gate.chip_of(catalog, key, host)] if default
            else list(dict.fromkeys(execution_providers)))
    found = []
    for key in keys:
        catalog.ep(key)  # an unknown or reserved key raises `EpRequestError`
        chip = gate.chip_of(catalog, key, host)
        if chip is not None:  # `coreml`: one check on the chip of the host, with no device key and the name `<key>`
            certified = evidence.certified(key, chip, gate.OS_LABELS.get(host.os_name, host.os_name))
            if not (default and (certified or wanted is not None)):
                found.append((key, key, None, chip, "gpu-not-usable" if wanted is not None else
                              _setup_reason(store.pack_state(catalog, key, None, None, host.os_build))))
            continue
        if catalog.device_row(key) is None:
            found.append((key, key, None, None, "not-gpu-ep"))
            continue
        usable = ep_gpus(catalog, key, host)
        pairs = [(device_key, gpu) for device_key, gpu in usable if wanted is None or device_key in wanted]
        for device_key, gpu in pairs:
            state = store.pack_state(catalog, key, gpu, device_key, host.os_build)
            # the default: no reviewed row; a plugin EP must be usable; `directml` and a Windows ML EP are always in it
            if default and (evidence.certified(key, gpu, host.os_name) or (catalog.pack(key) is not None and state[0] not in USABLE_STATES)):
                continue
            found.append((_label(key, device_key), key, device_key, gpu, _setup_reason(state)))
        if not pairs and not default:
            reason = "gpu-not-usable" if usable else _setup_reason(store.pack_state(catalog, key, None, None, host.os_build))
            found.append((key, key, None, None, reason))
    return found


def _setup_reason(state: tuple) -> str | None:
    return None if state[0] in RUNNABLE_STATES else "ep-" + (state[1] or state[0]).replace("_", "-")


def _image_path(store, settings: dict) -> Path:
    return store.cache_root() / "certify" / f"{settings['image']['sha256']}.jpg"  # the path of `_image_run()`


def _pipeline(catalog, pipeline) -> tuple[dict, str, str | None]:
    """The mapping of the pipeline for the child, its key, and the reason code when the image run cannot run."""
    from skellytracker.core import pipelines

    config = pipeline if isinstance(pipeline, pipelines.PipelineConfig) else pipelines.load_pipeline(
        catalog.data["certification"]["pipeline"] if pipeline is None else pipeline)
    check = pipelines.check_pipeline(config)
    reason = ("models-missing" if any(warning.code == "missing_dependency" for warning in check.warnings)
              else None if set(COMPARED_OUTPUTS) <= set(check.output_schema) else "outputs-not-comparable")
    return pipelines.export_pipeline(config), f"{config.pipeline_id}@{config.source.name}", reason


def _quick(report: dict, selected: list[tuple], catalog, host, sender: _Progress, cancel, resolved: tuple) -> None:
    from skellytracker.core.eps import certification, evidence, store
    from skellytracker.core.system.runtime import probe_runtime

    rows = {row["name"]: row for row in report["checks"]}
    mapping, pipeline_key, image_reason = resolved
    settings = {**catalog.data["certification"], "pipeline": mapping}
    image = _image_path(store, settings)
    image_was_here = image.is_file()
    details = {"pipeline": pipeline_key, "eps": {}}
    for label, key, device_key, gpu, setup in selected:
        if cancel is not None and cancel.is_set():
            break
        names = _names(label, key, device_key)
        details["eps"][label] = {"gpu": None if gpu is None else evidence.gpu_id(gpu), "device": device_key}
        if setup is not None:
            for name in names:
                rows[name].update(result="not-run", reason=setup)
            sender.send("running", None, report["checks"])
            continue
        jpeg = names[2:-1]
        temporary = catalog.ep_status(key) == "field-test" and key not in store.field_test_opt_ins()
        if temporary:
            store.opt_in_field_test(key)
        try:
            setup = _setup_reason(store.pack_state(catalog, key, gpu, device_key, host.os_build)) if temporary else None
            if setup is None:
                _probe(report, label, key, device_key, sender, cancel)
                _image(report, label, key, device_key, settings, image_reason, sender, cancel, details["eps"][label])
                if jpeg:
                    _jpeg(report, label, key, device_key, sender, cancel)
            else:
                for name in names[:-1]:
                    rows[name].update(result="not-run", reason=setup)
            parts = [rows[name] for name in names[:2]]
            failed = next((row for row in parts if row["result"] == "fail"), None)
            not_run = next((row for row in parts if row["result"] == "not-run"), None)
            if failed is None and not_run is None:
                rows[label].update(result="pass", reason=None)
            else:
                rows[label].update(result="fail" if failed else "not-run", reason=(failed or not_run)["reason"])
            if rows[label]["result"] in ("pass", "fail"):
                _record(certification, store, evidence, catalog, host, key, gpu, rows[label]["result"], pipeline_key,
                        details["eps"][label].get("models", ()), report["created_utc"],
                        {name.rsplit(":", 1)[1]: rows[name]["result"] for name in jpeg})
            sender.send("running", None, report["checks"])
        finally:
            if temporary and rows[label]["result"] != "pass":
                _cleanup(report, "field-test-opt-in", lambda key=key: store.drop_field_test_opt_in(key))
    if not image_was_here and image.exists():
        _cleanup(report, "test-image", image.unlink)
    runtime = probe_runtime()  # imports onnxruntime in this process, as `eps.certify()` does
    ort = dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True))
    ort_name = "onnxruntime-windowsml" if "onnxruntime-windowsml" in ort else next(iter(ort), None)
    details["versions"] = {"ort_distribution": ort_name, "ort_version": ort.get(ort_name), "windowsml": runtime.windowsml_version,
                           "catalog_revision": catalog.revision, "set_hash": evidence.set_hash(catalog)}
    report["details"] = details


def _probe(report: dict, label: str, key: str, device_key: str | None, sender: _Progress, cancel) -> None:
    from skellytracker.core.eps import verification

    row = next(row for row in report["checks"] if row["name"] == f"{label}:probe")
    sender.send("running", row["name"], report["checks"])
    started = time.monotonic()
    try:
        (verdict,) = verification.verify([key], device_key=device_key, force=True, cancel=cancel)
    except Exception as error:  # noqa: BLE001 - a setup failure: the EP did not run
        row.update(result="not-run", reason=type(error).__name__)
        return
    numbers = {"seconds": round(time.monotonic() - started, 1), "max_abs_diff": verdict.max_abs_diff}
    if verdict.ok:
        row.update(result="pass", reason=None)
    elif verdict.reason_code == "cancelled":
        row.update(result="not-run", reason="cancelled")
    elif verdict.reason_code in CHILD_FAILURES:
        row.update(result="fail", reason=CHILD_FAILURES[verdict.reason_code])
        numbers["exit_code"] = verdict.exit_code
    else:
        row.update(result="fail", reason=f"probe-{verdict.level.lower()}-failed")
    row["numbers"] = numbers
    if verdict.exit_reason_code:
        _add_exit(report, row["name"], verdict.exit_reason_code)


def _image(report: dict, label: str, key: str, device_key: str | None, settings: dict, image_reason: str | None,
           sender: _Progress, cancel, details: dict) -> None:
    from skellytracker.core.eps import certification

    row = next(row for row in report["checks"] if row["name"] == f"{label}:image")
    probe = next(row for row in report["checks"] if row["name"] == f"{label}:probe")
    if probe["result"] != "pass" or (cancel is not None and cancel.is_set()):
        row.update(result="not-run", reason="probe-not-passed" if probe["result"] != "pass" and probe["reason"] != "cancelled"
                   else "cancelled")
        return
    if image_reason is not None:
        row.update(result="not-run", reason=image_reason)
        return
    sender.send("running", row["name"], report["checks"])
    steps: list[str] = []
    try:
        found = certification._wide_run(key, settings, steps.append, device_key, cancel=cancel)
    except Exception as error:  # noqa: BLE001 - before the step `ep`, a setup failure
        found = {"ran": steps[-1:] == ["ep"], "ok": False, "reason_code": type(error).__name__}
    code = found.get("reason_code")
    if code == "cancelled":
        row.update(result="not-run", reason="cancelled")
    elif code in CHILD_FAILURES:
        row.update(result="fail", reason=CHILD_FAILURES[code])
    elif found["ran"]:
        row.update(result="pass" if found["ok"] else "fail", reason=None if found["ok"] else code)
    else:
        row.update(result="not-run", reason=code)
    numbers = {name: found[name] for name in IMAGE_NUMBERS if name in found}
    if code in CHILD_FAILURES:
        numbers["exit_code"] = found.get("exit_code")
    if numbers:
        row["numbers"] = numbers
    if found.get("exit_reason_code"):
        _add_exit(report, row["name"], found["exit_reason_code"])
    if "models" in found:
        details.update(models=found["models"], warnings=found.get("warnings", []))


def _jpeg_child(key: str, device_key: str | None, connection) -> None:
    """The child of `_jpeg()`: it sends the two checks of the GPU frame path, or `{"error": <exception class name>}`."""
    try:
        from skellytracker.core.decode.certification import run_jpeg_quick_checks

        result = {"checks": run_jpeg_quick_checks(key, device_key=device_key)}  # it switches the check rule off itself
    except Exception as error:  # noqa: BLE001 - a fixed code: an error text can hold a path
        result = {"error": type(error).__name__}
    connection.send(result)
    connection.close()


def _jpeg_spawn(key: str, device_key: str, cancel) -> tuple[dict | None, str | None, int | None]:
    from skellytracker.core.eps import verification

    return verification.spawn_child(_jpeg_child, (key, device_key), timeout=JPEG_TIMEOUT_SECONDS, cancel=cancel)


def _jpeg(report: dict, label: str, key: str, device_key: str, sender: _Progress, cancel) -> None:
    """The two JPEG checks of the GPU frame path, in one `spawn` child. They keep the reason codes of
    `core/decode/certification.py`, with no `detail` text. They never change the EP check."""
    rows = [next(row for row in report["checks"] if row["name"] == f"{label}:{name}") for name in JPEG_CHECKS]
    image = next(row for row in report["checks"] if row["name"] == f"{label}:image")
    if image["result"] != "pass" or (cancel is not None and cancel.is_set()):
        for row in rows:
            row.update(result="not-run", reason="cancelled" if image["result"] == "pass" or image["reason"] == "cancelled"
                       else "image-not-passed")
        return
    sender.send("running", rows[0]["name"], report["checks"])
    found, problem, exit_code = _jpeg_spawn(key, device_key, cancel)
    if found is None or "error" in found:
        code = found["error"] if found else problem
        for row in rows:
            if code == "cancelled":
                row.update(result="not-run", reason="cancelled")
            else:
                row.update(result="fail", reason=CHILD_FAILURES.get(code, code))
                if code in CHILD_FAILURES:
                    row["numbers"] = {"exit_code": exit_code}
        return
    by_name = {item["name"]: item for item in found.get("checks", ())}
    for row, name in zip(rows, JPEG_CHECKS, strict=True):
        item = by_name.get(name)
        if item is None:
            row.update(result="fail", reason="no-result")
            continue
        row.update(result=item["result"], reason=None if item["result"] == "pass" else item["reason"])
        numbers = {field: value for field, value in (item.get("numbers") or {}).items()
                   if value is None or isinstance(value, bool | int | float)}
        if numbers:
            row["numbers"] = numbers
    if problem:
        _add_exit(report, rows[-1]["name"], problem)


def _add_exit(report: dict, name: str, code: str) -> None:
    """The check `exit` of the contract for a child that gave its result and then did not exit cleanly."""
    index = next(i for i, row in enumerate(report["checks"]) if row["name"] == name)
    report["checks"].insert(index + 1, {"name": f"{name}:exit", "result": "record-only", "reason": code})


def _record(certification, store, evidence, catalog, host, key, gpu, result: str, pipeline_key: str, models, created: str,
            jpeg: dict) -> None:
    """Store the answer that ends the prompt, and the local result of the quick check of the pair (ADR-21BK item 2)."""
    from skellytracker.core.eps import exits

    pair = certification.pair_key(catalog, key, gpu, host.os_name)
    certification.write_answer(pair, "passed" if result == "pass" else "failed")
    with store.store_lock():
        if result == "pass":
            exits.forget(pair)  # a passed quick check removes the count of unclean exits (ADR-ER5X item 5)
        path = store.store_root() / "quick-checks.json"
        store.write_json(path, {**(store.read_json(path) or {}), pair: {
            "result": "passed" if result == "pass" else "failed", "set_hash": evidence.set_hash(catalog), "pipeline": pipeline_key,
            "precisions": {model["key"]: model["precision"] for model in models}, "created_utc": created,
            **({"jpeg": jpeg} if jpeg else {})}})


def _cleanup(report: dict, name: str, step: Callable[[], object]) -> None:
    try:
        step()
    except Exception as error:  # noqa: BLE001 - a failed cleanup step is a row of `cleanup`, and the report still returns
        report["cleanup"].append({"name": name, "result": "fail", "reason": type(error).__name__})


def _package() -> tuple[dict, list[str]]:
    """The block `package` and its evidence reasons: `no-version`, `no-commit` and `modified-tree`."""
    try:
        version = importlib.metadata.version("skellytracker")
    except importlib.metadata.PackageNotFoundError:
        version = None
    commit, modified = _commit()
    reasons = [code for code, bad in (("no-version", not (version and SEMVER.match(version))),
                                      ("no-commit", not (commit and COMMIT.match(commit))),
                                      ("modified-tree", modified is not False)) if bad]
    return {"name": PACKAGE, "version": version, "commit": commit, "tree_modified": modified}, reasons


def _commit() -> tuple[str | None, bool | None]:
    """The commit of the source and whether the tree had a change: from `skellytracker/_build_info.py`, which a build
    writes (`COMMIT`, `TREE_MODIFIED`); else from the PEP 610 record of an install from a git URL; else from `git` in a
    checkout; else `(None, None)`."""
    try:
        from skellytracker import _build_info  # absent in the repository: a build writes it

        return _build_info.COMMIT, _build_info.TREE_MODIFIED
    except ImportError:
        pass
    try:
        text = importlib.metadata.distribution("skellytracker").read_text("direct_url.json")
        commit = (json.loads(text or "{}").get("vcs_info") or {}).get("commit_id")
        if commit:
            return commit, False  # pip builds a git URL from a clean clone of that commit
    except (importlib.metadata.PackageNotFoundError, ValueError):
        pass
    root = Path(__file__).resolve().parents[1]
    if getattr(sys, "frozen", False) or not (root / ".git").exists() or shutil.which("git") is None:
        return None, None
    try:
        head, status = (subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30,  # noqa: S603, S607
                                       stdin=subprocess.DEVNULL, check=True).stdout
                        for args in (("rev-parse", "HEAD"), ("status", "--porcelain", "--untracked-files=normal")))
    except (OSError, subprocess.SubprocessError):
        return None, None
    return head.strip(), bool(status.strip())


def _host(host) -> dict:
    from skellytracker.core.eps import evidence

    return {"os": {"name": OS_NAMES.get(host.os_name, host.os_name), "release": host.os_release, "version": host.os_version,
                   "build": host.os_build, "label": host.os_label, "arch": ARCHES.get(host.arch.lower(), host.arch.lower())},
            "cpu": {"name": host.cpu_name}, "memory_bytes": host.memory_total_bytes,
            "gpus": [{"vendor": gpu.vendor, "name": gpu.name, "id": evidence.gpu_id(gpu), "driver_version": gpu.driver_version,
                      "vram_bytes": gpu.vram_total_bytes} for gpu in host.gpus]}


def _private_words() -> list[str]:
    words = {os.environ.get("USERNAME"), os.environ.get("USER"), Path.home().name, socket.gethostname(), platform.node()}
    words |= {word[: -len(".local")] for word in words if word and word.lower().endswith(".local")}  # the short macOS host name
    return sorted((word for word in words if word), key=len, reverse=True)


def _scrub(report: dict) -> dict:
    """Remove the user name, the host name, the home folder and each absolute path from each key and each value.

    A name that is also a word of a public fact (the host block, the check names, the reason codes) stays, and
    `details.scrub.exempted_terms` gives the count of such names (rules 12 and 13 of section 6 of the contract).
    """
    public = "\n".join([json.dumps(report["host"]), *(f"{row['name']} {row['reason']}" for row in report["checks"])])
    words = _private_words()
    kept = [word for word in words if not re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", public, re.IGNORECASE)]
    paths = sorted(filter(None, {str(Path.home()), sys.prefix}), key=len, reverse=True)

    def clean(value):
        if isinstance(value, dict):
            return {clean(name): clean(item) for name, item in value.items()}
        if isinstance(value, list | tuple):
            return [clean(item) for item in value]
        if not isinstance(value, str):
            return value
        for path in paths:
            for form in {path, path.replace("\\", "/"), path.replace("/", "\\")}:
                value = re.sub(re.escape(form), "<path>", value, flags=re.IGNORECASE)
        for word in kept:
            value = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", "<private>", value, flags=re.IGNORECASE)
        return PATH_PATTERN.sub("<path>", value)

    report = clean(report)
    report["details"]["scrub"] = {"exempted_terms": len(words) - len(kept)}
    return report
