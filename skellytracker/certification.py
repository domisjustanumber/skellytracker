"""`certify()` and `certify_plan()`: the certification functions of the whole package (ADR-P0JZ, ADR-21BK).

    import skellytracker
    plan = skellytracker.certify_plan("quick")          # show the plan, then get the consent of the user
    report = skellytracker.certify("quick", progress=show, cancel=event)

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
PROBE_SECONDS = 15  # not calibrated: the time estimate of one L3 probe; the catalog gives the time of the image run
IMAGE_SECONDS = 30  # not calibrated: the time estimate of an image run for an EP that has no `certification.seconds`
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
                 "keypoint_box_fraction_median", "keypoint_box_fraction_p99", "points_compared", "seconds")


def certify_plan(level: str, *, execution_providers: Sequence[str] | None = None, pipeline=None) -> dict:
    """The plan of a `certify()` call with the same arguments. It loads no GPU library and downloads nothing.

    `downloads` names the test image of the quick level when it is not on this host. The quick level installs
    nothing: `details.not_run` gives each selected EP that will not run, with its reason code, for example
    `ep-not-installed`. `system_changes` and `questions` are empty. `pipeline` does not change the plan.
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
    selected = _selection(catalog, host, execution_providers)
    runnable = [key for key, _, _, reason in selected if reason is None]
    plan["seconds_estimate"] = sum(PROBE_SECONDS + settings["seconds"].get(key, IMAGE_SECONDS) for key in runnable)
    if runnable and not _image_path(store, settings).is_file():
        plan["downloads"].append({"name": settings["image"]["url"].rsplit("/", 1)[1], "bytes": settings["image"]["bytes"]})
    plan["details"] = {"execution_providers": [key for key, *_ in selected],
                       "not_run": {key: reason for key, _, _, reason in selected if reason}}
    return plan


def certify(level: str, progress: Callable[[dict], object] | None = None, cancel=None, *,
            execution_providers: Sequence[str] | None = None, pipeline=None) -> dict:
    """Run the certification checks of this package at `level`, and return the module report.

    - `level`: `quick` or `full`. Each other value raises `ValueError`. The level `full` is not built
      here: it is `tools/certify_platform.py` today. `certify("full")` returns a report with the
      check `full` as `not-run` and `not-built`.
    - `progress`: a callable that gets each progress message, a `dict` with the complete state, at most
      10 times a second. If it raises, it gets no other message, and the run continues.
    - `cancel`: an object with `is_set()`. A set cancel stops the running child process within about a
      second. Each check that did not end is `not-run` with `cancelled`.
    - `execution_providers`: the EP keys to check. The default is each usable plugin EP of this host
      with no reviewed row in `ep_evidence.yaml` for this GPU model and OS: the EPs of
      `status().certify_offers`. A `field-test` EP is checked only when the caller names it. An unknown
      or reserved key raises `EpRequestError` (a `ValueError`).
    - `pipeline`: the pipeline of the user, as a `PipelineConfig`, a key of the pipeline catalog or a
      path. The default is `certification.pipeline` of the EP catalog. A config that does not load
      raises, as `load_pipeline()` does.

    The quick check of one EP runs the L3 probe (`verify()`) and then the pipeline on one test image
    on the EP and on the CPU EP, each in a `spawn` child, and compares the two results with the
    thresholds of `certification` of the EP catalog. It runs on the first GPU of `run_devices(key)`.
    It downloads no model: with a model file that is not on this host, the image check is `not-run`
    with `models-missing`. Each EP gives three checks: `<key>:probe`, `<key>:image` and `<key>`. The
    check `<key>` passes only when the two others pass (ADR-21BK item 2). An EP that cannot run, for
    example a pack that is not installed, gives `not-run` with `ep-<state code>`. Each EP runs, also
    when an other EP fails.

    Evidence: the item of the quick level is one EP on this host. Thus a run of a part of the EPs is
    complete for each EP that it checks, and is not `partial-run`. A run with no EP to check has no
    check and is not valid as evidence (`no-check`). A `quick` report never gives a reviewed row.

    The package cannot see the pipelines of an application, so it never refuses a run with `gpu-busy`:
    the application must not call it while a pipeline holds the GPU.

    It writes in the EP store of the user: the report in the folder `reports`, the verdict of the
    probe, the answer in `certify.json` and the local result of each EP that ran to `pass` or `fail`
    in `quick-checks.json`. A `field-test` EP gets the opt-in during its check. The opt-in stays only
    when the check passes (ADR-21BK item 2). The test image is deleted at the end when this run
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
        selected = _selection(catalog, host, execution_providers)
        report["checks"] = [{"name": name, "result": None, "reason": None}
                            for key, *_ in selected for name in (f"{key}:probe", f"{key}:image", key)]
        estimates = {f"{key}:probe": PROBE_SECONDS for key, *_ in selected}
        estimates |= {f"{key}:image": catalog.data["certification"]["seconds"].get(key, IMAGE_SECONDS) for key, *_ in selected}
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

        path = certification.reports_dir() / f"quick-{created.replace('-', '').replace(':', '')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    sender.send("done", None, report["checks"], None)
    return report


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


def _selection(catalog, host, execution_providers) -> list[tuple]:
    """`(key, device_key, gpu, reason)` for each EP to check; `reason` is the code of an EP that cannot run, else None."""
    from skellytracker.core.eps import certification, store
    from skellytracker.core.eps.recommendation import ep_gpus

    if isinstance(execution_providers, str):
        raise ValueError("execution_providers is a list of EP keys, for example ['cuda']")
    if execution_providers is None:
        keys = [offer.ep_key for offer in certification.certify_offers(catalog, host)]
    else:
        keys = list(dict.fromkeys(execution_providers))
    found = []
    for key in keys:
        catalog.ep(key)  # an unknown or reserved key raises `EpRequestError`
        device_key, gpu = next(iter(ep_gpus(catalog, key, host)), (None, None))
        if catalog.device_row(key) is None:
            found.append((key, None, None, "not-gpu-ep"))
            continue
        found.append((key, device_key, gpu, _setup_reason(store.pack_state(catalog, key, gpu, device_key, host.os_build))))
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
    for key, device_key, gpu, setup in selected:
        if cancel is not None and cancel.is_set():
            break
        names = (f"{key}:probe", f"{key}:image", key)
        details["eps"][key] = {"gpu": None if gpu is None else evidence.gpu_id(gpu)}
        if setup is not None:
            for name in names:
                rows[name].update(result="not-run", reason=setup)
            sender.send("running", None, report["checks"])
            continue
        temporary = catalog.ep_status(key) == "field-test" and key not in store.field_test_opt_ins()
        if temporary:
            store.opt_in_field_test(key)
        try:
            setup = _setup_reason(store.pack_state(catalog, key, gpu, device_key, host.os_build)) if temporary else None
            if setup is None:
                _probe(report, key, device_key, sender, cancel)
                _image(report, key, device_key, settings, image_reason, sender, cancel, details["eps"][key])
            else:
                for name in names[:2]:
                    rows[name].update(result="not-run", reason=setup)
            parts = [rows[name] for name in names[:2]]
            failed = next((row for row in parts if row["result"] == "fail"), None)
            not_run = next((row for row in parts if row["result"] == "not-run"), None)
            if failed is None and not_run is None:
                rows[key].update(result="pass", reason=None)
            else:
                rows[key].update(result="fail" if failed else "not-run", reason=(failed or not_run)["reason"])
            if rows[key]["result"] in ("pass", "fail"):
                _record(certification, store, evidence, catalog, host, key, gpu, rows[key]["result"], pipeline_key,
                        details["eps"][key].get("models", ()), report["created_utc"])
            sender.send("running", None, report["checks"])
        finally:
            if temporary and rows[key]["result"] != "pass":
                _cleanup(report, "field-test-opt-in", lambda key=key: store.drop_field_test_opt_in(key))
    if not image_was_here and image.exists():
        _cleanup(report, "test-image", image.unlink)
    runtime = probe_runtime()  # imports onnxruntime in this process, as `eps.certify()` does
    ort = dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True))
    ort_name = "onnxruntime-windowsml" if "onnxruntime-windowsml" in ort else next(iter(ort), None)
    details["versions"] = {"ort_distribution": ort_name, "ort_version": ort.get(ort_name), "windowsml": runtime.windowsml_version,
                           "catalog_revision": catalog.revision, "set_hash": evidence.set_hash(catalog)}
    report["details"] = details


def _probe(report: dict, key: str, device_key: str | None, sender: _Progress, cancel) -> None:
    from skellytracker.core.eps import verification

    row = next(row for row in report["checks"] if row["name"] == f"{key}:probe")
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


def _image(report: dict, key: str, device_key: str | None, settings: dict, image_reason: str | None, sender: _Progress,
           cancel, details: dict) -> None:
    from skellytracker.core.eps import certification

    row = next(row for row in report["checks"] if row["name"] == f"{key}:image")
    probe = next(row for row in report["checks"] if row["name"] == f"{key}:probe")
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


def _add_exit(report: dict, name: str, code: str) -> None:
    """The check `exit` of the contract for a child that gave its result and then did not exit cleanly."""
    index = next(i for i, row in enumerate(report["checks"]) if row["name"] == name)
    report["checks"].insert(index + 1, {"name": f"{name}:exit", "result": "record-only", "reason": code})


def _record(certification, store, evidence, catalog, host, key, gpu, result: str, pipeline_key: str, models, created: str) -> None:
    """Store the answer that ends the prompt, and the local result of the quick check of the pair (ADR-21BK item 2)."""
    pair = certification.pair_key(catalog, key, gpu, host.os_name)
    certification.write_answer(pair, "passed" if result == "pass" else "failed")
    with store.store_lock():
        path = store.store_root() / "quick-checks.json"
        store.write_json(path, {**(store.read_json(path) or {}), pair: {
            "result": "passed" if result == "pass" else "failed", "set_hash": evidence.set_hash(catalog), "pipeline": pipeline_key,
            "precisions": {model["key"]: model["precision"] for model in models}, "created_utc": created}})


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
