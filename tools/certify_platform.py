#!/usr/bin/env python3
"""Run the certify suite of this checkout on this host, and write one report file in the format of ``skellycertify``.

Usage::

    uv run python tools/certify_platform.py [--only N[,N...]] [--yes] [--out FILE] [--wheel-dir DIR]

A volunteer runs this command in a clone at a certification tag (decision Y14H). The suite:

1. prints the plan: each section with its time estimate, the total, and each download with its size;
2. asks for consent one time. ``--yes`` skips the question. With no terminal on stdin and no
   ``--yes``, it stops and runs nothing;
3. runs each section in its own child process (this script with the hidden flag ``--section N``),
   with the time limit of the section. A child prints one JSON object on its last stdout line and
   ends with ``os._exit``, so that the teardown of a GPU EP cannot crash or hang it. A child over
   its time limit is ``timed-out``: the suite kills the whole process tree. With no such object, a
   non-zero exit is ``crashed``, a timeout ``timed-out`` and an other output ``bad-output``: a ``fail``
   with the exit code and the seconds. A child that printed the object and then exited non-zero or
   timed out keeps its result, with the extra ``record-only`` check ``exit`` (``crashed`` or
   ``timed-out``). A child that does not exit ``EXIT_GRACE_SECONDS`` after its result is killed
   with its process tree; it keeps its result, with the check ``exit`` and ``hung-at-exit``
   (``os._exit`` still runs the DLL exit handlers, and an EP library can hang there). The suite goes on;
4. asks the yes/no questions of the sections and one optional free-text note, only when stdin is a
   terminal;
5. deletes its work folder ``.certify-work/`` (git ignores it), also after a failure, Ctrl+C,
   SIGTERM or SIGHUP, and writes the report file. Each cleanup step that fails is a row of ``cleanup``
   in the report, and the report is still written. The default report file is
   ``certify-report-<UTC start time>.md`` in the current folder, and ``created_utc`` of the report is
   the same instant. The tool prints its path. At the start, the suite first acts on the records of a
   work folder that an earlier run left, then deletes it.
   If it cannot delete it, the suite stops with exit code 1 and runs nothing.

The sections (``SECTIONS``): 1 ``checkout``, the checkout and the versions against ``uv.lock``; 2
``hardware``, the hardware probe against the tools of the OS (``tools/certify_hardware.py``); 3
``packs``, the install and the verify of each EP pack (``tools/certify_eps.py``); 4 ``full``,
``skellytracker.certify("full")`` (``tools/certify_eps.py``).

The report file obeys sections 4.1 and 4.2 of ``report-format.md`` of the repository ``skellycertify``.
It has the title, the line of the module, the system list, the GPU table, the benchmark table and the component
table (``| Module | Result |``, only when a module has a ``component`` item) from the ``summary`` items, the camera
line, the table of the checks that did not pass, the note and, last, one fenced JSON block (``report_data()`` reads it):
``{"schema", "app": null, "modules": [<module report>], "note"}``. The Markdown part prints each value with ``cell()``:
each match of the IPv4 pattern of rule 20 of section 6 has a space for each dot, for example ``2.1.0.5`` prints
``2 1 0 5``. The JSON block keeps the exact value. The one module report is the
report of section 4, with ``kind`` ``full`` and ``created_utc`` set to the start of the run. When
section 4 gave no report, it is the empty report of ``_base_report()`` of the package. Its ``checks``
start with the checks of the suite: ``suite:<slug>`` with the result of each section, and
``suite:<slug>:<name>`` for each check of a section. Section 4 gives ``suite:full`` only when it gave
no report. A result is ``pass``, ``fail``, ``not-run`` or ``record-only``, with a fixed reason code,
never an error text. A ``fail`` or a ``not-run`` with no code gets ``unspecified``.
``details.suite`` holds ``SUITE_VERSION``, the selected sections, the summary, the time and the
details of each section, ``telemetry_database`` and the answers. The free-text note is ``note`` of the
file object.

``evidence.reasons`` holds the reasons of the module report and the reasons of the suite
(``suite_reasons()``): ``section-1-not-run``, ``no-commit``, ``modified-tree``, ``python-differs`` and
``packages-differ`` from section 1, ``partial-run`` for a section that was not selected or did not
run, and ``cancelled`` after Ctrl+C. A report is valid as evidence only with no reason. The tag is a
fact of section 1, not a rule. The report holds no hostname,
no user name, no absolute path, no serial number and no bus address: each section takes OS facts
through an allowlist of fields, and ``scrub()`` removes the user name, the home folder, the checkout
folder and the hostname from each string. The report records whether the telemetry folder of ONNX Runtime
exists before and after the run (``telemetry_database``, booleans only), and section 1 records the value
of ``ORT_DISABLE_TELEMETRY``: the check ``telemetry-switch`` is ``record-only`` with ``telemetry-on`` when it
is not ``1`` or ``true`` (ADR-BZ7X). A user name or a hostname that is also a word of a public
fact (``report_words()``) stays in the report fields, and the report records only the count; the
note is scrubbed with each word. The suite needs no administrator rights. On Windows with
an AMD GPU, the one system change is the Windows ML package of each AMD EP that the catalog offers:
the consent names the EP, and at the end the frame removes each package that section 3 installed
(``remove_windows_packages``), also after a crash, a timeout or Ctrl+C. A package that stays is a
``fail`` check of section 3 (ADR-XSE7).

Each child gets ``SKELLYTRACKER_EP_STORE`` and ``SKELLYTRACKER_EP_CACHE`` set to folders of the work
folder: the suite installs and tests the EP packs in its own EP store, and uses and changes no EP
store or EP cache of the user. The suite writes ``options.json`` (for example ``--wheel-dir``) into
the work folder, and the result of each section as ``section-<N>.json``: a later section can read an
earlier result there. At the end it deletes each file of ``remove-at-end.json`` of the work folder:
a section lists each file that it downloads outside the work folder, for example a model file. It
deletes only a path inside the model folder ``skellytracker/core/model_zoo/``.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
WORK_DIR = REPO_ROOT / ".certify-work"
MODEL_ROOT = REPO_ROOT / "skellytracker" / "core" / "model_zoo"
REPORT_SCHEMA = "skellycertify.report/1.5.0"  # `SCHEMA` of `skellytracker/certification.py`
# rule 20 of section 6 of the contract: an IPv4 address; the Markdown part prints each match with spaces for the dots
IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b")
SUITE_VERSION = 2
RESULTS = ("pass", "fail", "not-run", "record-only")
EXIT_OK, EXIT_FAILURE, EXIT_NO_CONSENT, EXIT_CANCELLED = 0, 1, 2, 6  # the exit codes of `skellytracker-eps`
NOTES_LIMIT = 2000
REASON = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")  # a reason code of the contract
EXIT_GRACE_SECONDS = 20  # time a child gets to exit after its complete result (`hung-at-exit`); the package has the same value


@dataclass(frozen=True)
class Section:
    number: int
    slug: str  # the check names `suite:<slug>` and the key of `details.suite.sections`
    name: str
    estimate_seconds: int
    timeout_seconds: int
    run: Callable[[Path], dict]  # runs in the child process; it gets the work folder
    downloads: Callable[[dict], tuple[tuple[str, int], ...]] | None = None  # the options -> (name, bytes) of each download


def outcome(checks: list[dict]) -> str:
    """The result of a section from its checks: any `fail` fails; else any `pass` passes; else `record-only` or `not-run`."""
    results = {check["result"] for check in checks}
    for result in ("fail", "pass", "record-only"):
        if result in results:
            return result
    return "not-run"


def check(name: str, result: str, reason_code: str | None = None, **numbers) -> dict:
    return {"name": name, "result": result, "reason_code": reason_code, **numbers}


# --------------------------------------------------------------------------------------------
# Section 1: checkout and versions
# --------------------------------------------------------------------------------------------


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8",  # noqa: S603, S607
                          errors="replace", timeout=60, check=False)


def checkout_check(root: Path) -> tuple[dict, dict]:
    """The git tag at HEAD (exact match), the commit and whether the tree is clean. The suite's own work folder does not count."""
    facts = {"tag": None, "commit": None, "clean": None, "changed_files": None}
    if shutil.which("git") is None:
        return check("checkout", "record-only", "no-git"), facts
    head = git(root, "rev-parse", "HEAD")
    if head.returncode:
        return check("checkout", "record-only", "no-git"), facts
    tag = git(root, "describe", "--tags", "--exact-match", "HEAD")
    changed = [line for line in git(root, "status", "--porcelain", "--untracked-files=normal").stdout.splitlines()
               if line.strip() and not line[3:].startswith(WORK_DIR.name + "/")]
    facts.update(tag=tag.stdout.strip() if tag.returncode == 0 else None, commit=head.stdout.strip(),
                 clean=not changed, changed_files=len(changed))
    reasons = [code for code, bad in (("no-tag", facts["tag"] is None), ("modified-tree", changed)) if bad]
    return check("checkout", "record-only" if reasons else "pass", reasons[0] if reasons else None, reasons=reasons), facts


def lock_packages(lock: dict, environment: dict | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """The pinned packages of this platform in a parsed `uv.lock`: `(required, extras only)`, each a map name -> version.

    Required: the dependencies and the dependency groups of the project, which `uv run` installs.
    Extras only: what only an extra of the project adds. A dependency with a marker that is false
    for `environment` (default: this Python) is not followed. `packaging.markers` evaluates each marker.
    """
    from packaging.markers import Marker

    environment = {"extra": "", **(environment or {})}
    packages = {}
    for package in lock["package"]:
        packages.setdefault(package["name"], []).append(package)
    root = next(p for p in lock["package"] if "." in (p.get("source", {}).get("editable"), p.get("source", {}).get("virtual")))

    def pick(dependency: dict) -> dict:
        # a forked lock has two entries of one name; the dependency then names its version
        found = packages[dependency["name"]]
        return next((p for p in found if p.get("version") == dependency.get("version")), found[0])

    def walk(dependencies: list[dict]) -> dict[str, str]:
        seen, found, stack = set(), {}, list(dependencies)
        while stack:
            dependency = stack.pop()
            if "marker" in dependency and not Marker(dependency["marker"]).evaluate(environment):
                continue
            package = pick(dependency)
            found[package["name"]] = package.get("version")
            for extra in (None, *dependency.get("extra", ())):
                if (package["name"], extra) not in seen:
                    seen.add((package["name"], extra))
                    stack += package.get("dependencies", []) if extra is None else package.get("optional-dependencies", {}).get(extra, [])
        return found

    required = walk([*root.get("dependencies", []), *(d for group in root.get("dev-dependencies", {}).values() for d in group)])
    extras = walk([d for group in root.get("optional-dependencies", {}).values() for d in group])
    return required, {name: version for name, version in extras.items() if name not in required}


def compare_packages(required: dict, extras: dict, installed: Callable[[str], str | None]) -> dict:
    """Each pinned package against the installed distribution. A missing extras-only package is not a difference."""
    from packaging.version import Version

    found = {"required": len(required), "extras_only": len(extras), "mismatched": [], "missing": [], "extras_not_installed": []}
    for name, version in sorted({**extras, **required}.items()):
        have = installed(name)
        if have is None:
            found["missing" if name in required else "extras_not_installed"].append(name)
        elif Version(have) != Version(version):
            found["mismatched"].append({"name": name, "locked": version, "installed": have})
    return found


def installed_version(name: str) -> str | None:
    import importlib.metadata

    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def section_checkout(work: Path, root: Path = REPO_ROOT) -> dict:
    import tomllib

    checkout, facts = checkout_check(root)
    checks, details = [checkout], {"checkout": facts,
                                   "os": {"system": platform.system(), "release": platform.release(),
                                          "version": platform.version(), "machine": platform.machine()}}
    python = {"implementation": platform.python_implementation(), "version": platform.python_version(), "requires": None}
    lock_path = root / "uv.lock"
    if lock_path.is_file():
        from packaging.specifiers import SpecifierSet

        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
        python["requires"] = lock.get("requires-python")
        ok = python["requires"] is None or python["version"] in SpecifierSet(python["requires"])
        checks.append(check("python", "pass" if ok else "fail", None if ok else "python-mismatch"))
        packages = compare_packages(*lock_packages(lock), installed_version)
        bad = len(packages["mismatched"]) + len(packages["missing"])
        checks.append(check("packages", "fail" if bad else "pass", "packages-differ" if bad else None, differ=bad,
                            pinned=packages["required"] + packages["extras_only"]))
        details["packages"] = packages
    else:
        checks += [check("python", "record-only", "no-lock"), check("packages", "not-run", "no-lock")]
    details["python"] = python
    try:
        details["onnx_stack"] = onnx_stack_facts()
        checks.append(check("onnx-stack", "record-only"))
        off = str(details["onnx_stack"]["ort_disable_telemetry"]).strip().lower() in ("1", "true")
        checks.append(check("telemetry-switch", "pass" if off else "record-only", None if off else "telemetry-on"))
    except Exception as error:  # noqa: BLE001 - a broken install is a finding, not a crash of the section
        checks.append(check("onnx-stack", "not-run", type(error).__name__))
    packages = details.get("packages")
    differ = None if packages is None else len(packages["mismatched"]) + len(packages["missing"])
    summary = (f"tag {facts['tag'] or 'none'}, tree {'clean' if facts['clean'] else 'modified' if facts['clean'] is False else 'unknown'}; "
               f"Python {python['version']}; " + ("no uv.lock" if differ is None else f"{differ} package(s) differ from uv.lock"))
    return {"result": outcome(checks), "reason_code": next((c["reason_code"] for c in checks if c["result"] == "fail"), None),
            "summary": summary, "checks": checks, "details": details}


def onnx_stack_facts() -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    import certify_hardware  # the directory of this script is on sys.path
    from skellytracker.core.eps import evidence
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.runtime import probe_runtime

    # no package version: `skellytracker.__version__` is the same in each checkout; the tag and the commit identify the code
    runtime, catalog = probe_runtime(), load_catalog()  # probe_runtime imports onnxruntime; it makes no session
    return {"ort_distributions": dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True)),
            "ort_version": runtime.ort_version, "windowsml": runtime.windowsml_version, "ep_names": list(runtime.ep_names),
            "catalog_revision": catalog.revision, "set_hash": evidence.set_hash(catalog),
            "probe_errors": certify_hardware.error_sources(runtime.probe_errors),  # the source tags only: no error text
            "ort_disable_telemetry": runtime.ort_disable_telemetry}


# --------------------------------------------------------------------------------------------
# Sections 2 to 4
# --------------------------------------------------------------------------------------------


def section_hardware(work: Path) -> dict:
    import certify_hardware  # the directory of this script is on sys.path

    return certify_hardware.section_hardware(work)


def section_eps(work: Path) -> dict:
    import certify_eps

    return certify_eps.section_eps(work)


def section_full(work: Path) -> dict:
    import certify_eps

    return certify_eps.section_full(work)


def eps_downloads(options: dict) -> tuple:
    import certify_eps

    return certify_eps.eps_downloads(options)


def pipeline_downloads(options: dict) -> tuple:
    import certify_eps

    return certify_eps.pipeline_downloads(options)


def telemetry_database() -> bool:
    """True when the telemetry folder of ONNX Runtime exists (ADR-BZ7X). The report holds this boolean only, no path.

    Windows: under the local app data folder. Linux and macOS: under `XDG_CACHE_HOME`, else `~/.cache`
    (read from the strings of the Linux library, not measured).
    """
    base = os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else (
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"))
    return bool(base) and (Path(base) / "Microsoft" / "DeveloperTools" / ".onnxruntime").exists()


SECTIONS = (
    Section(1, "checkout", "Checkout and versions", 10, 120, section_checkout),
    Section(2, "hardware", "Hardware probe", 20, 300, section_hardware),
    # 3: on an RTX 3070 host, 40 s with the download of 1.12 GB on a fast link, 15 s from --wheel-dir; the limit allows a slow link
    Section(3, "packs", "EP packs: install and verify", 60, 2400, section_eps, eps_downloads),
    # 4: not calibrated. The pipeline part took about 135 s and the JPEG part 12.5 s to 20 s on a host with an RTX 3070 and an
    # Intel UHD 770; the limit allows a slow TensorRT RTX engine build on each camera count and a hang at exit
    Section(4, "full", "Full level of certify()", 200, 3000, section_full, pipeline_downloads),
)


# --------------------------------------------------------------------------------------------
# The frame
# --------------------------------------------------------------------------------------------


def finding(section: Section, result: str, reason_code: str | None, summary: str, **numbers) -> dict:
    return {"number": section.number, "slug": section.slug, "name": section.name, "result": result, "reason_code": reason_code, "summary": summary,
            "seconds": None, "exit_code": None, "checks": [], "details": {}, "questions": [], **numbers}


def default_command(section: Section, work: Path) -> list[str]:
    return [sys.executable, str(SCRIPT), "--section", str(section.number), "--work", str(work)]


def stop_tree(process: subprocess.Popen) -> None:
    """Kill the child and its children."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)  # noqa: S603, S607
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)  # the child leads its own session: this kills its children too
        except ProcessLookupError:
            pass
    process.kill()
    process.wait()


def child_env(work: Path) -> dict:
    """The environment of a child: the EP store, the EP cache and the model cache of the work folder (the variables of
    `core/eps/store.py` and `core/model_spec/artifacts.py`), and no `__pycache__` files in the checkout."""
    return {**os.environ, "SKELLYTRACKER_EP_STORE": str(work / "eps"), "SKELLYTRACKER_EP_CACHE": str(work / "ep-cache"),
            "SKELLYTRACKER_MODEL_CACHE": str(work / "model-cache"), "PYTHONDONTWRITEBYTECODE": "1"}


def remove_windows_packages(work: Path) -> list[dict]:
    """Remove each Windows ML package that section 3 installed: the records of the EP store of the work folder (ADR-XSE7).

    One row for each package (`key`, `package`, `result`, `reason_code`); `windows_ml.remove_installed()` never
    removes a package that was on the PC before. A failure is a row, never an exception.
    """
    records = read_records(work / "eps" / "windows-ml.json")
    if not records:
        return []
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from skellytracker.core.eps import windows_ml

        return [{"key": key, **row} for key, record in records.items() for row in windows_ml.remove_installed(record)]
    except Exception as error:  # noqa: BLE001 - the work folder must still go
        return [{"key": key, "package": None, "result": "fail", "reason_code": f"cleanup-{type(error).__name__}"} for key in records]


def read_records(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def add_cleanup(results: list[dict], rows: list[dict]) -> None:
    """Add one check to section 3 for each removed package; a package that stayed fails the section and is printed."""
    section = next((r for r in results if r["number"] == 3), None)
    for row in rows:
        name = f"remove-{row['package'] or row['key']}"
        if section is not None:
            section["checks"].append(check(name, row["result"], row["reason_code"]))
            if row["result"] == "fail" and section["result"] != "fail":
                section.update(result="fail", reason_code=row["reason_code"])
        if row["result"] == "fail":
            print(f"The Windows ML package of the EP '{row['key']}' ({row['package'] or 'name not known'}) may still be on this system. "
                  "PowerShell removes a package with: Remove-AppxPackage <full name>.", file=sys.stderr)


def remove_listed(work: Path, root: Path | None = None) -> list[dict]:
    """Delete each file that a section put on the remove list of the work folder, for example a downloaded model file.

    It accepts only a path that resolves inside the model root (`MODEL_ROOT`). It never raises: a refused path or a
    file that does not go is a `fail` cleanup row, with no path.
    """
    root = (root or MODEL_ROOT).resolve()
    try:
        listed = json.loads((work / "remove-at-end.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = []
    for path in listed if isinstance(listed, list) else ():
        try:
            target = Path(path).resolve()
            if not target.is_relative_to(root) or target == root:
                rows.append(check("remove-listed-file", "fail", "outside-model-root"))
                continue
            target.unlink(missing_ok=True)
        except (OSError, TypeError, ValueError) as error:
            rows.append(check("remove-listed-file", "fail", type(error).__name__))
    return rows


def cleanup_step(rows: list[dict], name: str, step: Callable[[], object]) -> None:
    """Run one cleanup step. An error is a `fail` cleanup row, never an exception: the next step and the report still run."""
    try:
        step()
    except Exception as error:  # noqa: BLE001
        rows.append(check(name, "fail", type(error).__name__))


def parse_result(stdout: str | None) -> dict | None:
    """The result object on the last non-empty stdout line of a child, or None."""
    lines = [line for line in (stdout or "").splitlines() if line.strip()]
    try:
        data = json.loads(lines[-1])
    except (IndexError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("result") in RESULTS else None


def run_section(section: Section, command: list[str], env: dict | None = None) -> dict:
    """Run one section in a child process. Each failure of the child is a finding; only Ctrl+C raises.

    A child that printed a complete result object keeps it, also when it then exits non-zero or hangs
    to the time limit: the section gets the extra check `exit`, `record-only`, with `crashed` or
    `timed-out`, and its own result does not change. A child that is still alive `EXIT_GRACE_SECONDS`
    after the result is killed, with `hung-at-exit`. With no complete result object, the section is
    `fail` with `crashed`, `timed-out` or `bad-output`.
    """
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True, encoding="utf-8",  # noqa: S603
                               errors="replace", cwd=REPO_ROOT, start_new_session=sys.platform != "win32", env=env)
    lines: list[str] = []
    complete = threading.Event()

    def pump() -> None:  # a thread drains the pipe, so a big result cannot block the child
        for line in process.stdout:
            lines.append(line)
            if line.strip():
                complete.set() if parse_result(line) else complete.clear()

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    problem, exit_code, complete_at = None, None, None
    try:
        while process.poll() is None:
            now = time.monotonic()
            complete_at = complete_at or (now if complete.is_set() else None)
            if now - started > section.timeout_seconds:
                stop_tree(process)
                problem = ("timed-out", f"stopped after the time limit of {section.timeout_seconds} s")
                break
            if complete_at is not None and now - complete_at > EXIT_GRACE_SECONDS:
                stop_tree(process)
                problem = ("hung-at-exit", f"stopped {EXIT_GRACE_SECONDS} s after the result")
                break
            time.sleep(0.05)
        else:
            exit_code = process.returncode
            if exit_code != 0:
                problem = ("crashed", f"the child process exited with {exit_code}")
    except KeyboardInterrupt:
        stop_tree(process)
        raise
    reader.join(5)  # a grandchild that holds the pipe must not block the suite
    seconds = round(time.monotonic() - started, 1)
    data = parse_result("".join(lines))
    if data is None:
        code, summary = problem or ("bad-output", "the child process printed no result object")
        return finding(section, "fail", code if code != "hung-at-exit" else "timed-out", summary, seconds=seconds, exit_code=exit_code,
                       no_result=True)
    extra = [check("exit", "record-only", problem[0], exit_code=exit_code,
                   **({"grace_seconds": EXIT_GRACE_SECONDS} if problem[0] == "hung-at-exit" else {}))] if problem else []
    return {**finding(section, data["result"], data.get("reason_code"), str(data.get("summary", ""))),
            "checks": [*data.get("checks", []), *extra], "details": data.get("details", {}), "questions": data.get("questions", []),
            "seconds": seconds, "exit_code": exit_code, **({"report": data["report"]} if isinstance(data.get("report"), dict) else {})}


def private_terms() -> tuple[list[str], list[str]]:
    """The paths and the words to remove from a report: the checkout folder, the home folder, the user name and the hostname."""
    words = {os.environ.get("USERNAME"), os.environ.get("USER"), Path.home().name, socket.gethostname(), platform.node()}
    try:
        words.add(getpass.getuser())
    except Exception:  # noqa: BLE001, S110 - no user name is fine
        pass
    words |= {word[: -len(".local")] for word in words if word and word.lower().endswith(".local")}  # the short macOS host name
    return [str(REPO_ROOT), sys.prefix, str(Path.home())], sorted(word for word in words if word)


PUBLIC_KEYS = {"result", "reason_code", "reason", "reasons", "state", "status", "catalog_status", "key", "ep", "name", "os_label",
               "os_version", "cpu_name", "system", "release", "version", "machine", "label", "arch",
               "vendor"}  # suite vocabulary and public host facts


def host_facts_text() -> list[str]:
    """The public OS facts of this host from the standard library: `platform` and, on Linux, the os-release fields."""
    facts = [platform.system(), platform.release(), platform.version(), platform.machine()]
    try:
        facts += list(platform.freedesktop_os_release().values())
    except (AttributeError, OSError):
        pass
    return facts


def report_words(words: list[str], data, public: list[str]) -> list[str]:
    """The words to scrub from the report fields: each word of `words` that no public text holds as a word.

    The public text is `public` (the vocabulary of the suite and the OS facts of this host) and each string under a
    key of `PUBLIC_KEYS` in `data` (results, reason codes, EP keys, catalog status values, section and check names,
    the OS label, the CPU and GPU names). So a host name `ubuntu` or a user name `test` does not delete the facts
    `Ubuntu 24.04.1 LTS` or `field-test`. The notes of the volunteer are always scrubbed with all words.
    """
    texts = list(public)

    def walk(value, key=None):
        if isinstance(value, dict):
            texts.extend(name for name in value if isinstance(name, str))
            for name, item in value.items():
                walk(item, name)
        elif isinstance(value, list | tuple):
            for item in value:
                walk(item, key)
        elif isinstance(value, str) and key in PUBLIC_KEYS:
            texts.append(value)

    walk(data)
    text = "\n".join(texts)
    return [word for word in words if not re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text, re.IGNORECASE)]


PATH_PATTERN = re.compile(r"(?:\b[A-Za-z]:[\\/]|\\\\[^\\\s]|/(?:home|Users|root)/|~[\\/])[^\s\"'|,;]*")  # rule 1 of section 6


def scrub(value, paths: list[str], words: list[str]):
    """`value` with each path of `paths` and each word of `words` replaced in each string, and each user path left as `<path>`."""
    if isinstance(value, dict):
        return {key: scrub(item, paths, words) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [scrub(item, paths, words) for item in value]
    if not isinstance(value, str):
        return value
    for path in sorted(filter(None, paths), key=len, reverse=True):
        for form in {path, path.replace("\\", "/"), path.replace("/", "\\")}:
            value = re.sub(re.escape(form), "<path>", value, flags=re.IGNORECASE)
    for word in sorted(words, key=len, reverse=True):  # `host.local` before `host`
        value = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", "<private>", value, flags=re.IGNORECASE)
    return PATH_PATTERN.sub("<path>", value)


def suite_reasons(results: list[dict], selected: set[int], interrupted: bool) -> list[str]:
    """The evidence reasons of the suite: the checkout and the versions of section 1, a part of the sections, and Ctrl+C."""
    first = next((r for r in results if r["number"] == 1), None)
    facts = (first or {}).get("details", {}).get("checkout") or {}
    failed = {c.get("name") for c in (first or {}).get("checks", ()) if c.get("result") == "fail"}
    partial = any(r["number"] not in selected or r["result"] == "not-run" or r.get("no_result")
                  or (r.get("slug") == "full" and not r.get("report"))  # `certify("full")` raised: the run has no EP check
                  for r in results)
    return [code for code, bad in (
        ("section-1-not-run", not facts), ("no-commit", bool(facts) and facts.get("commit") is None),
        ("modified-tree", bool(facts) and facts.get("clean") is not True), ("python-differs", "python" in failed),
        ("packages-differ", "packages" in failed), ("partial-run", partial), ("cancelled", interrupted)) if bad]


def reason_code(code, result: str) -> str | None:
    """`code` as a reason code of the contract, with `-` for each other character. A `fail` or `not-run` with no code: `unspecified`."""
    if code is None:
        return "unspecified" if result in ("fail", "not-run") else None
    return re.sub(r"[^A-Za-z0-9_-]", "-", str(code)).lstrip("_-")[:80] or "unspecified"


def suite_check(name: str, result: str, code, numbers: dict) -> dict:
    """One check of the module report: `-` for each character that a check name cannot hold, and only the numbers that
    the contract allows (a number, a boolean, None or a reason code)."""
    row = {"name": re.sub(r"[^A-Za-z0-9_.:@-]", "-", name)[:128], "result": result, "reason": reason_code(code, result)}
    numbers = {key: value for key, value in numbers.items()
               if value is None or isinstance(value, bool | int | float) or (isinstance(value, str) and REASON.match(value))}
    return {**row, "numbers": numbers} if numbers else row


def suite_checks(results: list[dict], report: dict | None) -> list[dict]:
    """`suite:<slug>` for each section (for section 4 only with no `report`), and `suite:<slug>:<name>` for each of its checks."""
    rows = []
    for r in results:
        if r["slug"] != "full" or report is None:
            rows.append(suite_check(f"suite:{r['slug']}", r["result"], r["reason_code"],
                                    {key: r[key] for key in ("seconds", "exit_code") if r[key] is not None}))
        rows += [suite_check(f"suite:{r['slug']}:{c['name']}", c["result"], c.get("reason_code"),
                             {key: value for key, value in c.items() if key not in ("name", "result", "reason_code")})
                 for c in r["checks"]]
    return rows


def base_report(created: str) -> tuple[dict, list[str]]:
    """The empty module report of the level `full` (`_base_report()` of the package) and its evidence reasons."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from skellytracker import certification
        from skellytracker.core.system.host import probe_host

        return certification._base_report("full", created, probe_host())
    except Exception:  # noqa: BLE001 - a broken install still gets its report file
        return ({"schema": REPORT_SCHEMA, "package": {"name": "skellytracker", "version": None, "commit": None, "tree_modified": None},
                 "kind": "full", "created_utc": created, "host": {}, "checks": [], "cleanup": [], "details": {}},
                ["no-version", "no-commit", "modified-tree"])


def module_report(results: list[dict], selected: set[int], interrupted: bool, created: str, cleanup: list[dict],
                  telemetry: dict, answers: list[dict]) -> dict:
    """The one module report of the run: the report of section 4, or an empty one, with the checks and the facts of the suite."""
    report = next((r.get("report") for r in results if r["slug"] == "full"), None)
    base, reasons = (report, (report.get("evidence") or {}).get("reasons", [])) if report else base_report(created)
    reasons = list(dict.fromkeys([*reasons, *suite_reasons(results, selected, interrupted)]))
    suite = {"version": SUITE_VERSION, "selected": [r["slug"] for r in results if r["number"] in selected],
             "sections": {r["slug"]: {"summary": r["summary"], "seconds": r["seconds"], "details": r["details"]} for r in results},
             "telemetry_database": telemetry, "answers": answers}
    return {**base, "kind": "full", "created_utc": created, "checks": [*suite_checks(results, report), *base.get("checks", [])],
            "cleanup": [*base.get("cleanup", []), *({"name": c["name"], "result": c["result"],
                                                    "reason": reason_code(c["reason_code"], c["result"])} for c in cleanup)],
            "details": {**base.get("details", {}), "suite": suite}, "evidence": {"valid": not reasons, "reasons": reasons}}


def cell(text) -> str:
    """A value as Markdown text: one line, `|` escaped, and each IPv4 match with spaces for the dots, again until none is left."""
    text = " ".join(str(text if text is not None else "").split()).replace("|", "\\|")
    while IPV4.search(text):
        text = IPV4.sub(lambda match: match.group().replace(".", " "), text)
    return text


def gpu_cell(gpu: dict) -> str:
    """The display name of a GPU, then its VRAM in whole GB when it is 1 GB or more (section 4.2 of the contract)."""
    name = " ".join(re.sub(r"\((R|TM)\)|\b(GeForce|Radeon|Arc|Graphics|GPU|Series)\b", " ", gpu.get("name") or gpu["id"]).split())
    vram = gpu.get("vram_bytes") or 0
    return cell(name + (f" {round(vram / 2**30)} GB" if vram >= 2**30 else ""))


def system_lines(modules: list[dict]) -> list[str]:
    """The system list, one time for the file: each value from the first module whose `host` has it, as a display name."""
    hosts = [m.get("host") or {} for m in modules]
    label = next((h["os"]["label"] for h in hosts if (h.get("os") or {}).get("label")), None)
    cpu = next((h["cpu"]["name"] for h in hosts if (h.get("cpu") or {}).get("name")), None)
    memory = next((h["memory_bytes"] for h in hosts if h.get("memory_bytes")), None)
    cpu = cpu and re.sub(r"\((R|TM)\)|\b\d+(st|nd|rd|th) Gen\b|\bCPU @ [\d.]+ ?GHz\b|\b\d+-Core Processor\b", " ", cpu)
    return [f"- {key}: {cell(value)}" for key, value in (("OS", label and re.sub(r"\b(Home|Pro)\b", " ", label)), ("CPU", cpu),
                                                        ("RAM", memory and f"{round(memory / 2**30)} GB")) if value]


def shown(item: dict) -> str:
    """The display of the result of a summary item (section 4.2 of the contract)."""
    if item["result"] == "skipped":
        return f"skipped ({'already reviewed' if item.get('reason') == 'reviewed' else item.get('reason')})"
    return {"record-only": "record"}.get(item["result"], item["result"])


def render(data: dict) -> str:
    """The report file of sections 4.1 and 4.2 of the contract: the short summary for a person, then the data as the last
    fenced JSON block. The tool writes one module with no app. The rows come from the `summary` items: nothing is computed."""
    modules = data["modules"]
    first = modules[0]
    proof, package = first["evidence"], first["package"]
    lines = ["# Certify report", "", " · ".join([
        f"{cell(package['name'])} {cell(package['version']) or 'with no version'}", f"{first.get('kind')} run",
        f"{first['created_utc'][:16].replace('T', ' ')} UTC",
        *(["incomplete"] if {"cancelled", "interrupted"} & set(proof["reasons"]) else []),
        "valid as evidence" if proof["valid"] else f"not valid as evidence: {', '.join(proof['reasons'])}"])]
    system = system_lines(modules)
    gpus, benchmarks, components, cameras, failed, checked, unchecked = [], [], [], [], [], set(), {}
    for m in modules:
        found = {g["id"]: g for g in (m.get("host") or {}).get("gpus") or []}
        unchecked.update({key: gpu for key, gpu in found.items() if key not in unchecked})
        for item in m.get("summary") or []:
            if item["group"] in ("camera", "component"):
                (cameras if item["group"] == "camera" else components).append(f"| {cell(item['name'])} | {shown(item)} |")
                continue
            device = item["device"]
            where = "-" if device is None else gpu_cell(found.get(device) or {"id": device})
            if item["group"] == "benchmark":
                benchmarks.append(f"| {where} | {cell(item['name'])} | {cell(item['stage'])} | {item['ms_per_frame']:.1f} | {item['fps']:.1f} |")
                continue
            gpus.append(f"| {where} | {cell(item['name'])}{' GPU decode' if item['group'] == 'gpu-jpeg' else ''} | {shown(item)} |")
            checked.update([device] if item["group"] == "ep" else [])
        # each `fail`, and each `not-run` of a module whose summary item is `partial` or `fail`; the module has no `sections`
        weak = {item["name"] for item in m.get("summary") or [] if item.get("result") in ("partial", "fail")}
        failed += [f"| {cell(m['package']['name'])} | {cell(c.get('module'))} | {cell(c['name'])} | "
                   f"{'fail' if c['result'] == 'fail' else 'not run'} | {cell(c['reason'])} |"
                   for c in m["checks"] if c["result"] == "fail" or (c["result"] == "not-run" and c.get("module") in weak)]
    gpus += [f"| {gpu_cell(gpu)} | | not checked |" for key, gpu in unchecked.items() if key not in checked]
    for part in (system, gpus and ["| GPU | Module | Result |", "|---|---|---|", *gpus],
                 benchmarks and ["| GPU | Module | Stage | ms/frame | FPS |", "|---|---|---|---|---|", *benchmarks],
                 components and ["| Module | Result |", "|---|---|", *components],
                 ["| Camera | Result |", "|---|---|", *cameras] if cameras else ["Cameras: not checked on this system."],
                 failed and ["Checks that did not pass:", "", "| Package | Module | Test | Result | Reason |", "|---|---|---|---|---|", *failed],
                 data["note"] and ["Note of the person:", "", *(f"> {cell(line)}" for line in data["note"].splitlines())]):
        if part:
            lines += ["", *part]
    text = json.dumps(data, indent=1)
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", text)), default=0))
    return "\n".join([*lines, "", "## Data", "", fence + "json", text, fence, ""])


def report_data(markdown: str) -> dict:
    """The data of a report file: the fenced JSON block at its end."""
    match = re.search(r"^(`{3,})json\n(.*)\n\1\s*\Z", markdown, re.DOTALL | re.MULTILINE)
    if match is None:
        raise ValueError("the report does not end with a fenced JSON block")
    return json.loads(match.group(2))


def ask_yes_no(text: str, ask: Callable[[str], str]) -> str | None:
    answer = ask(f"{text} [y/n, Enter to skip] ").strip().lower()
    return "yes" if answer.startswith("y") else "no" if answer.startswith("n") else None


def section_downloads(section: Section, options: dict) -> tuple[tuple[str, int], ...]:
    try:
        return section.downloads(options) if section.downloads else ()
    except Exception:  # noqa: BLE001 - the plan still shows; the section records its own failure
        return ((f"the downloads of section {section.number} (size unknown)", 0),)


def windows_ml_offer() -> list[str]:
    import certify_eps

    try:
        return certify_eps.windows_ml_offer()
    except Exception:  # noqa: BLE001 - no catalog: section 3 then records `catalog-<error>` and installs nothing
        return []


def megabytes(size: int) -> str:
    """A size in decimal MB (10**6 bytes): one decimal under 10 MB, else a whole number. `CERTIFY.md` uses the same form."""
    return f"{size / 1e6:.1f}" if size < 10**7 else f"{size / 1e6:.0f}"


def plan_text(sections: tuple[Section, ...], selected: set[int], out: Path, options: dict | None = None,
              os_platform: str = sys.platform, windows_eps: Callable[[], list[str]] | None = None) -> str:
    chosen = [s for s in sections if s.number in selected]
    lines = ["The certify suite will run these sections, each in its own process:"]
    lines += [f"  {s.number}. {s.name}: about {s.estimate_seconds} s" for s in chosen]
    lines.append(f"Total: about {sum(s.estimate_seconds for s in chosen)} s.")
    downloads = [item for s in chosen for item in section_downloads(s, options or {})]
    lines.append("Downloads: " + ("none." if not downloads else
                                  ", ".join(f"{name} ({megabytes(size)} MB)" for name, size in downloads) + "."))
    # ADR-XSE7: the catalog gives the package name only after the install, so the text names the EP
    packages = (windows_eps or windows_ml_offer)() if os_platform == "win32" and 3 in selected else []
    lines += [f"Windows downloads and installs the Windows ML package of the AMD execution provider {name}, if Windows does not "
              "have it yet. The suite removes that package at the end. It never removes a package that was on this system before."
              for name in packages]
    lines += ["Apart from that, the suite installs no system software. It needs no administrator rights." if packages else
              "The suite installs no system software and needs no administrator rights.",
              f"It keeps its files, also its own EP store, in {WORK_DIR.name}/ in this checkout and deletes that folder at the end.",
              f"The report goes to {out.name}. It holds hardware and software facts only. Nothing is sent."]
    return "\n".join(lines)


def run_suite(sections: tuple[Section, ...], selected: set[int], out: Path, *, yes: bool, work: Path = WORK_DIR,
              command: Callable[[Section, Path], list[str]] = default_command, interactive: bool | None = None,
              ask: Callable[[str], str] = input, options: dict | None = None, started: time.struct_time | None = None) -> int:
    """Ask for consent, run the selected sections, ask the end questions, delete the work folder and write the report.

    The sections read `options` from `options.json` of the work folder, and the result of an earlier
    section from `section-<N>.json` there. `created_utc` of the report is `started` (default: now), the start of the
    run: `main()` also puts it in the default file name.
    """
    started = started or time.gmtime()
    interactive = sys.stdin.isatty() and sys.stdout.isatty() if interactive is None else interactive
    print(plan_text(sections, selected, out, options), flush=True)
    if not yes:
        try:  # on Windows, NUL on stdin reports a terminal and then gives EOF
            answer = ask("Run the suite now? [y/N] ") if interactive else None
        except (EOFError, KeyboardInterrupt):
            answer = None
        if answer is None:
            print("\nNo terminal to ask for consent: run again with --yes. Nothing ran.", file=sys.stderr)
            return EXIT_NO_CONSENT
        if not answer.strip().lower().startswith("y"):
            print("Nothing ran.")
            return EXIT_NO_CONSENT
    results, interrupted, answers, notes, cleanup = [], False, [], None, []
    database_before = telemetry_database()
    # a work folder of a run whose frame did not end: its packages, its listed files, then the folder
    cleanup_step(cleanup, "remove-windows-packages", lambda: add_cleanup([], remove_windows_packages(work)))
    cleanup += remove_listed(work)
    shutil.rmtree(work, ignore_errors=True)
    if work.exists():
        print(f"The folder {work.name}/ of an earlier run cannot be deleted, for example because a program holds a file in it. "
              "Delete it by hand, then run the suite again. Nothing ran.", file=sys.stderr)
        return EXIT_FAILURE
    work.mkdir(parents=True)
    (work / "options.json").write_text(json.dumps(options or {}), encoding="utf-8")
    try:
        for section in sections:
            if section.number not in selected:
                results.append(finding(section, "not-run", "not-selected", "not selected with --only"))
                continue
            if interrupted:
                results.append(finding(section, "not-run", "cancelled", "the run was stopped with Ctrl+C"))
                continue
            print(f"Section {section.number}: {section.name} ...", flush=True)
            try:
                results.append(run_section(section, command(section, work), child_env(work)))
                (work / f"section-{section.number}.json").write_text(json.dumps(results[-1]), encoding="utf-8")
            except KeyboardInterrupt:
                interrupted = True
                results.append(finding(section, "not-run", "cancelled", "the run was stopped with Ctrl+C"))
            print(f"Section {section.number}: {results[-1]['result']}" + (f" ({results[-1]['reason_code']})" if results[-1]["reason_code"] else ""),
                  flush=True)
        if interactive and not interrupted:
            try:
                for r in results:
                    answers += [{"section": r["slug"], "id": q["id"], "text": q["text"], "answer": ask_yes_no(q["text"], ask)}
                                for q in r["questions"]]
                print("Optional: one line of notes about this run, for example a problem that you saw.")
                print("Do not write your name, contact details or other personal details.")
                notes = ask("Notes (Enter to skip): ").strip()[:NOTES_LIMIT] or None
            except (KeyboardInterrupt, EOFError):
                pass
    finally:  # each step survives an error of an other step, and the report is still written
        cleanup_step(cleanup, "remove-windows-packages", lambda: add_cleanup(results, remove_windows_packages(work)))
        cleanup += remove_listed(work)
        shutil.rmtree(work, ignore_errors=True)
        if work.exists():
            cleanup.append(check("delete-work-folder", "fail", "not-deleted"))
            print(f"Could not delete {work.name}/ completely: delete it by hand.", file=sys.stderr)
    module = module_report(results, selected, interrupted, time.strftime("%Y-%m-%dT%H:%M:%SZ", started), cleanup,
                           {"before": database_before, "after": telemetry_database()}, answers)
    report_id = module.get("id") or str(uuid.uuid4())  # the id of section 4; read before the scrub, so a private word cannot change it
    paths, words = private_terms()
    kept = report_words(words, module, [*RESULTS, *(s.name for s in sections), *host_facts_text()])
    module = scrub(module, paths, kept)
    found = (module["details"].get("scrub") or {}).get("exempted_terms", 0)
    module["details"]["scrub"] = {"exempted_terms": max(found, len(words) - len(kept))}
    module = {"schema": REPORT_SCHEMA, "id": report_id, **{key: value for key, value in module.items() if key not in ("schema", "id")}}
    data = {"schema": REPORT_SCHEMA, "app": None, "modules": [module], "note": scrub(notes, paths, words)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data), encoding="utf-8", newline="\n")
    print(f"Report written to {out}")
    return EXIT_CANCELLED if interrupted else EXIT_OK


def child(number: int, work: Path) -> int:
    section = next(s for s in SECTIONS if s.number == number)
    sys.path.insert(0, str(REPO_ROOT))
    from skellytracker.core.eps import gate

    with gate.certification_run():  # a section runs an EP before the EP has a result (ADR-ER5X)
        result = section.run(work)
    print(json.dumps(result), flush=True)
    return 0


def stop_on_signals() -> None:
    """Make SIGTERM, SIGHUP and SIGBREAK (Ctrl+Break on Windows) take the path of Ctrl+C, so that the cleanup runs.

    shortcut: closing the console window on Windows sends CTRL_CLOSE_EVENT, which Python does not map to a signal; Windows
    then ends the process with no cleanup. The next run removes what the record of the work folder names.
    """
    def interrupt(signum, frame):
        raise KeyboardInterrupt

    for name in ("SIGTERM", "SIGHUP", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), interrupt)


def main(argv: list[str] | None = None) -> int:
    # before each import of the checkout, so that a run without `-B` leaves no `__pycache__` in the clone; the children
    # get `PYTHONDONTWRITEBYTECODE=1` (`child_env`), and the imports above this function are of the standard library only
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="run only these section numbers, for example 1,2")
    parser.add_argument("--yes", action="store_true", help="do not ask for consent")
    parser.add_argument("--out", type=Path, help="the report file")
    parser.add_argument("--wheel-dir", type=Path,
                        help="install the EP packs from the wheels in this folder, with no network (`skellytracker-eps install --from-dir`)")
    parser.add_argument("--section", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--work", type=Path, default=WORK_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.section is not None:
        return child(args.section, args.work)
    numbers = {s.number for s in SECTIONS}
    try:
        selected = {int(n) for n in args.only.split(",")} if args.only else numbers
    except ValueError:
        parser.error("--only takes section numbers, for example 1,2")
    if not selected <= numbers:
        parser.error(f"--only takes the section numbers {min(numbers)} to {max(numbers)}")
    started = time.gmtime()
    out = args.out or Path.cwd() / time.strftime("certify-report-%Y%m%dT%H%M%SZ.md", started)
    if args.wheel_dir is not None and not args.wheel_dir.is_dir():
        parser.error("--wheel-dir takes a folder")
    options = {"wheel_dir": str(args.wheel_dir.resolve())} if args.wheel_dir else {}
    stop_on_signals()
    return run_suite(SECTIONS, selected, out, yes=args.yes, options=options, started=started)


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)  # the output is out: the interpreter teardown of a GPU EP must not crash or hang a section child
