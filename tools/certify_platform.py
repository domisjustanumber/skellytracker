#!/usr/bin/env python3
"""Run the certify suite of this checkout on this host, and write one Markdown report.

Usage::

    uv run python tools/certify_platform.py [--only N[,N...]] [--yes] [--out FILE] [--wheel-dir DIR]

A volunteer runs this command in a clone at a certification tag (decision Y14H). The suite:

1. prints the plan: each section with its time estimate, the total, and each download with its size;
2. asks for consent one time. ``--yes`` skips the question. With no terminal on stdin and no
   ``--yes``, it stops and runs nothing;
3. runs each section in its own child process (this script with the hidden flag ``--section N``),
   with the time limit of the section. A child prints one JSON object on its last stdout line. A
   non-zero exit is ``crashed``, an output that is not such an object is ``bad-output`` and a child
   over its time limit is ``timed-out``: the suite kills the whole process tree. Each of these is a
   ``fail`` with the exit code and the seconds, and the suite goes on;
4. asks the yes/no questions of the sections and one optional free-text note, only when stdin is a
   terminal;
5. deletes its work folder ``.certify-work/`` (git ignores it), also after a failure or Ctrl+C,
   and writes the report. The default report is ``certify-report-<UTC time>.md`` in the current
   folder. The tool prints its path.

The report has a summary table (section, result, one-line reason), the details of each section and,
last, the same data as one fenced JSON block (``report_data()`` reads it). The schema id is
``REPORT_SCHEMA``, and the report records ``SUITE_VERSION``. A result is ``pass``, ``fail``,
``not-run`` or ``record-only``, with a fixed reason code, never an error text. A report is valid as
evidence only from a clean checkout of a tag with all sections run. The report holds no hostname,
no user name, no absolute path, no serial number and no bus address: each section takes OS facts
through an allowlist of fields, and ``scrub()`` removes the user name, the home folder, the checkout
folder and the hostname from each string. The suite needs no administrator rights. On Windows with
an AMD GPU, the one system change is the Windows ML package of each AMD EP that the catalog offers:
the consent names the EP, and at the end the frame removes each package that section 3 installed
(``remove_windows_packages``), also after a crash, a timeout or Ctrl+C. A package that stays is a
``fail`` check of section 3 (ADR-XSE7).

Each child gets ``SKELLYTRACKER_EP_STORE`` and ``SKELLYTRACKER_EP_CACHE`` set to folders of the work
folder: the suite installs and tests the EP packs in its own EP store, and uses and changes no EP
store or EP cache of the user. The suite writes ``options.json`` (for example ``--wheel-dir``) into
the work folder, and the result of each section as ``section-<N>.json``: a later section reads an
earlier result there. At the end it deletes each file of ``remove-at-end.json`` of the work folder:
a section lists each file that it downloads outside the work folder, for example a model file.

Sections 3 and 4 are in ``tools/certify_eps.py``, section 5 is in ``tools/certify_jpeg.py``. Sections 6
and 7 are placeholders: their result is ``not-run`` with the reason code ``not-built``.
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
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
WORK_DIR = REPO_ROOT / ".certify-work"
REPORT_SCHEMA = "skellytracker.certify-suite/1"
SUITE_VERSION = 1
RESULTS = ("pass", "fail", "not-run", "record-only")
EXIT_OK, EXIT_NO_CONSENT, EXIT_CANCELLED = 0, 2, 6  # the exit codes of `skellytracker-eps`
NOTES_LIMIT = 2000


@dataclass(frozen=True)
class Section:
    number: int
    name: str
    estimate_seconds: int
    timeout_seconds: int
    run: Callable[[Path], dict]  # runs in the child process; it gets the work folder
    downloads: Callable[[dict], tuple[tuple[str, int], ...]] | None = None  # the options -> (name, bytes) of each download
    built: bool = True


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
    import skellytracker
    from skellytracker.core.eps import evidence
    from skellytracker.core.eps.catalog import load_catalog
    from skellytracker.core.system.runtime import probe_runtime

    runtime, catalog = probe_runtime(), load_catalog()  # probe_runtime imports onnxruntime; it makes no session
    return {"skellytracker": skellytracker.__version__,
            "ort_distributions": dict(zip(runtime.ort_packages, runtime.ort_package_versions, strict=True)),
            "ort_version": runtime.ort_version, "windowsml": runtime.windowsml_version, "ep_names": list(runtime.ep_names),
            "catalog_revision": catalog.revision, "set_hash": evidence.set_hash(catalog), "probe_errors": list(runtime.probe_errors)}


# --------------------------------------------------------------------------------------------
# Sections 2 to 7
# --------------------------------------------------------------------------------------------


def section_hardware(work: Path) -> dict:
    import certify_hardware  # the directory of this script is on sys.path

    return certify_hardware.section_hardware(work)


def section_eps(work: Path) -> dict:
    import certify_eps

    return certify_eps.section_eps(work)


def section_pipeline(work: Path) -> dict:
    import certify_eps

    return certify_eps.section_pipeline(work)


def section_jpeg(work: Path) -> dict:
    import certify_jpeg

    return certify_jpeg.section_jpeg(work)


def eps_downloads(options: dict) -> tuple:
    import certify_eps

    return certify_eps.eps_downloads(options)


def pipeline_downloads(options: dict) -> tuple:
    import certify_eps

    return certify_eps.pipeline_downloads(options)


def not_built(work: Path) -> dict:
    return {"result": "not-run", "reason_code": "not-built", "summary": "not built in this suite version", "checks": [], "details": {}}


SECTIONS = (
    Section(1, "Checkout and versions", 10, 120, section_checkout),
    Section(2, "Hardware probe", 20, 300, section_hardware),
    # 3: on an RTX 3070 host, 40 s with the download of 1.07 GB on a fast link, 15 s from --wheel-dir; the limit allows a slow link
    Section(3, "EPs: install, verify and certify", 60, 2400, section_eps, eps_downloads),
    # 4: about 115 s on a host with an RTX 3070 and an Intel UHD 770 (DirectML on each GPU); the limit allows a slow
    # TensorRT RTX engine build on each camera count
    Section(4, "Pipeline on each EP against the CPU EP", 120, 1800, section_pipeline, pipeline_downloads),
    # 5: after 4, so the model files of section 4 are still there. About 12.5 s for the CPU paths with the model files,
    # 14 s for cuda and 20 s for trt-rtx with no model files (RTX 3070); the limit allows an engine build and a hang at exit
    Section(5, "JPEG decode and preprocess", 60, 600, section_jpeg),
    Section(6, "Cameras", 0, 60, not_built, built=False),
    Section(7, "JPEG encode and decode speed", 0, 60, not_built, built=False),
)


# --------------------------------------------------------------------------------------------
# The frame
# --------------------------------------------------------------------------------------------


def finding(section: Section, result: str, reason_code: str | None, summary: str, **numbers) -> dict:
    return {"number": section.number, "name": section.name, "result": result, "reason_code": reason_code, "summary": summary,
            "seconds": None, "exit_code": None, "checks": [], "details": {}, "questions": [], **numbers}


def default_command(section: Section, work: Path) -> list[str]:
    return [sys.executable, str(SCRIPT), "--section", str(section.number), "--work", str(work)]


def kill_tree(process: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)  # noqa: S603, S607
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)  # the child leads its own session: this kills its children too
        except ProcessLookupError:
            pass
    process.kill()
    process.communicate()


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
            print(f"The Windows ML package of the EP '{row['key']}' ({row['package'] or 'name not known'}) may still be on this PC. "
                  "PowerShell removes a package with: Remove-AppxPackage <full name>.", file=sys.stderr)


def remove_listed(work: Path) -> None:
    """Delete each file that a section put on the remove list of the work folder, for example a downloaded model file."""
    try:
        listed = json.loads((work / "remove-at-end.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for path in listed:
        Path(path).unlink(missing_ok=True)


def run_section(section: Section, command: list[str], env: dict | None = None) -> dict:
    """Run one section in a child process. Each failure of the child is a finding; only Ctrl+C raises."""
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True, encoding="utf-8",  # noqa: S603
                               errors="replace", cwd=REPO_ROOT, start_new_session=sys.platform != "win32", env=env)
    try:
        stdout, _ = process.communicate(timeout=section.timeout_seconds)
    except subprocess.TimeoutExpired:
        kill_tree(process)
        return finding(section, "fail", "timed-out", f"stopped after the time limit of {section.timeout_seconds} s",
                       seconds=round(time.monotonic() - started, 1))
    except KeyboardInterrupt:
        kill_tree(process)
        raise
    seconds = round(time.monotonic() - started, 1)
    if process.returncode:
        return finding(section, "fail", "crashed", f"the child process exited with {process.returncode}",
                       seconds=seconds, exit_code=process.returncode)
    lines = [line for line in stdout.splitlines() if line.strip()]
    try:
        data = json.loads(lines[-1])
        if not (isinstance(data, dict) and data.get("result") in RESULTS):
            raise ValueError
    except (IndexError, ValueError):
        return finding(section, "fail", "bad-output", "the child process printed no result object", seconds=seconds, exit_code=0)
    return {**finding(section, data["result"], data.get("reason_code"), str(data.get("summary", ""))),
            "checks": data.get("checks", []), "details": data.get("details", {}), "questions": data.get("questions", []),
            "seconds": seconds, "exit_code": 0}


def private_terms() -> tuple[list[str], list[str]]:
    """The paths and the words to remove from a report: the checkout folder, the home folder, the user name and the hostname."""
    words = {os.environ.get("USERNAME"), os.environ.get("USER"), Path.home().name, socket.gethostname(), platform.node()}
    try:
        words.add(getpass.getuser())
    except Exception:  # noqa: BLE001, S110 - no user name is fine
        pass
    return [str(REPO_ROOT), sys.prefix, str(Path.home())], sorted(word for word in words if word)


PATH_PATTERN = re.compile(r"(?:\b[A-Za-z]:[\\/]|\\\\|/(?:home|Users)/)[^\s\"'|,;]*")


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
    for word in words:
        value = re.sub(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", "<private>", value, flags=re.IGNORECASE)
    return PATH_PATTERN.sub("<path>", value)


def evidence_state(results: list[dict], selected: set[int], sections: tuple[Section, ...]) -> dict:
    """Valid as evidence only from a clean checkout of a tag, with all sections selected and none interrupted."""
    first = next((r for r in results if r["number"] == 1), None)
    facts = (first or {}).get("details", {}).get("checkout") or {}
    reasons = [code for code, bad in (
        ("section-1-not-run", not facts), ("no-tag", facts and facts.get("tag") is None),
        ("modified-tree", facts and facts.get("clean") is not True), ("partial-run", selected != {s.number for s in sections}),
        ("interrupted", any(r["reason_code"] == "interrupted" for r in results))) if bad]
    return {"valid": not reasons, "reasons": reasons, "tag": facts.get("tag"), "commit": facts.get("commit")}


def cell(text) -> str:
    return " ".join(str(text if text is not None else "").split()).replace("|", "\\|")


def scalar(value) -> str:
    return "none" if value is None else json.dumps(value) if isinstance(value, bool) else str(value)


def markdown_lines(value, depth: int = 0) -> list[str]:
    """`value` as a nested Markdown list. A map or a list of plain values is one line."""
    def deep(item) -> bool:
        return isinstance(item, dict | list) and any(isinstance(v, dict | list) for v in (item.values() if isinstance(item, dict) else item))

    pad, lines = "  " * depth, []
    items = list(value.items()) if isinstance(value, dict) else [(None, item) for item in value]
    all_deep = isinstance(value, list) and any(deep(item) for item in value)  # the items of one list share one form
    for key, item in items:
        label = f"{key}: " if key is not None else ""
        if deep(item) or (all_deep and isinstance(item, dict) and item):
            lines += [f"{pad}- {label}".rstrip(), *markdown_lines(item, depth + 1)]
        elif isinstance(item, dict):
            lines.append(f"{pad}- {label}" + (", ".join(f"{k}: {scalar(v)}" for k, v in item.items()) or "none"))
        elif isinstance(item, list):
            lines.append(f"{pad}- {label}" + (", ".join(map(scalar, item)) or "none"))
        else:
            lines.append(f"{pad}- {label}{scalar(item)}")
    return lines


def render(data: dict) -> str:
    """The Markdown report: summary table, details of each section, then the data as the last fenced JSON block."""
    proof = data["evidence"]
    lines = ["# skellytracker certify report", "",
             f"Schema `{data['schema']}`, suite version {data['suite_version']}, created {data['created_utc']} (UTC).", "",
             (f"**Valid as evidence:** clean checkout of the tag `{proof['tag']}`, all sections run." if proof["valid"] else
              f"**Not valid as evidence:** {', '.join(proof['reasons'])}. The report is kept as a record only."), "",
             "| Section | Result | Reason |", "|---|---|---|"]
    lines += [f"| {r['number']}. {cell(r['name'])} | {r['result']} | {cell(r['summary'] or r['reason_code'])} |" for r in data["sections"]]
    for r in data["sections"]:
        lines += ["", f"## {r['number']}. {r['name']}", "",
                  f"Result: **{r['result']}**" + (f", reason `{r['reason_code']}`" if r["reason_code"] else "")
                  + (f", {r['seconds']} s" if r["seconds"] is not None else "")
                  + (f", exit code {r['exit_code']}" if r["exit_code"] not in (None, 0) else "") + "."]
        if r["checks"]:
            lines += ["", "| Check | Result | Reason |", "|---|---|---|"]
            lines += [f"| {cell(c['name'])} | {c['result']} | {cell(c.get('reason_code') or '')} |" for c in r["checks"]]
        if r["details"]:
            lines += ["", *markdown_lines(r["details"])]
    if data["answers"] or data["notes"]:
        lines += ["", "## Answers", "", *(f"- {cell(a['text'])} **{a['answer'] or 'no answer'}**" for a in data["answers"])]
        lines += ["", "Notes:", "", *(f"> {line}" for line in (data["notes"] or "").splitlines())] if data["notes"] else []
    text = json.dumps(data, indent=1)
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", text)), default=0))
    return "\n".join([*lines, "", "## Data", "", fence + "json", text, fence, ""])


def report_data(markdown: str) -> dict:
    """The data of a report: the fenced JSON block at its end."""
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


def plan_text(sections: tuple[Section, ...], selected: set[int], out: Path, options: dict | None = None,
              os_platform: str = sys.platform, windows_eps: Callable[[], list[str]] | None = None) -> str:
    chosen = [s for s in sections if s.number in selected]
    lines = ["The certify suite will run these sections, each in its own process:"]
    lines += [f"  {s.number}. {s.name}: " + (f"about {s.estimate_seconds} s" if s.built else "not built yet, skipped") for s in chosen]
    lines.append(f"Total: about {sum(s.estimate_seconds for s in chosen)} s.")
    downloads = [item for s in chosen for item in section_downloads(s, options or {})]
    lines.append("Downloads: " + ("none." if not downloads else
                                  ", ".join(f"{name} ({-(-size // 2**20)} MB)" for name, size in downloads) + "."))
    # ADR-XSE7: the catalog gives the package name only after the install, so the text names the EP
    packages = (windows_eps or windows_ml_offer)() if os_platform == "win32" and 3 in selected else []
    lines += [f"Windows downloads and installs the Windows ML package of the AMD execution provider {name}, if Windows does not "
              "have it yet. The suite removes that package at the end. It never removes a package that was on this PC before."
              for name in packages]
    lines += ["Apart from that, the suite installs no system software. It needs no administrator rights." if packages else
              "The suite installs no system software and needs no administrator rights.",
              f"It keeps its files, also its own EP store, in {WORK_DIR.name}/ in this checkout and deletes that folder at the end.",
              f"The report goes to {out.name}. It holds hardware and software facts only. Nothing is sent."]
    return "\n".join(lines)


def run_suite(sections: tuple[Section, ...], selected: set[int], out: Path, *, yes: bool, work: Path = WORK_DIR,
              command: Callable[[Section, Path], list[str]] = default_command, interactive: bool | None = None,
              ask: Callable[[str], str] = input, options: dict | None = None) -> int:
    """Ask for consent, run the selected sections, ask the end questions, delete the work folder and write the report.

    The sections read `options` from `options.json` of the work folder, and the result of an earlier
    section from `section-<N>.json` there.
    """
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
    results, interrupted, answers, notes = [], False, [], None
    add_cleanup([], remove_windows_packages(work))  # the packages of a run whose frame did not end
    shutil.rmtree(work, ignore_errors=True)  # a folder from a run that did not finish
    work.mkdir(parents=True)
    (work / "options.json").write_text(json.dumps(options or {}), encoding="utf-8")
    try:
        for section in sections:
            if section.number not in selected:
                results.append(finding(section, "not-run", "not-selected", "not selected with --only"))
                continue
            if interrupted:
                results.append(finding(section, "not-run", "interrupted", "the run was stopped with Ctrl+C"))
                continue
            print(f"Section {section.number}: {section.name} ...", flush=True)
            try:
                results.append(run_section(section, command(section, work), child_env(work)))
                (work / f"section-{section.number}.json").write_text(json.dumps(results[-1]), encoding="utf-8")
            except KeyboardInterrupt:
                interrupted = True
                results.append(finding(section, "not-run", "interrupted", "the run was stopped with Ctrl+C"))
            print(f"Section {section.number}: {results[-1]['result']}" + (f" ({results[-1]['reason_code']})" if results[-1]["reason_code"] else ""),
                  flush=True)
        if interactive and not interrupted:
            try:
                for r in results:
                    answers += [{"section": r["number"], "id": q["id"], "text": q["text"], "answer": ask_yes_no(q["text"], ask)}
                                for q in r["questions"]]
                print("Optional: one line of notes about this run, for example a problem that you saw.")
                print("Do not write your name, contact details or other personal details.")
                notes = ask("Notes (Enter to skip): ").strip()[:NOTES_LIMIT] or None
            except (KeyboardInterrupt, EOFError):
                pass
    finally:
        add_cleanup(results, remove_windows_packages(work))  # also after a crash, a timeout or Ctrl+C of section 3
        remove_listed(work)
        shutil.rmtree(work, ignore_errors=True)
        if work.exists():
            print(f"Could not delete {work.name}/ completely: delete it by hand.", file=sys.stderr)
    data = {"schema": REPORT_SCHEMA, "suite_version": SUITE_VERSION, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "selected": sorted(selected), "evidence": evidence_state(results, selected, sections), "sections": results,
            "answers": answers, "notes": notes}
    data = scrub(data, *private_terms())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data), encoding="utf-8", newline="\n")
    print(f"Report written to {out}")
    return EXIT_CANCELLED if interrupted else EXIT_OK


def child(number: int, work: Path) -> int:
    section = next(s for s in SECTIONS if s.number == number)
    print(json.dumps(section.run(work)), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
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
    out = args.out or Path.cwd() / time.strftime("certify-report-%Y%m%dT%H%M%SZ.md", time.gmtime())
    if args.wheel_dir is not None and not args.wheel_dir.is_dir():
        parser.error("--wheel-dir takes a folder")
    options = {"wheel_dir": str(args.wheel_dir.resolve())} if args.wheel_dir else {}
    return run_suite(SECTIONS, selected, out, yes=args.yes, options=options)


if __name__ == "__main__":
    sys.exit(main())
