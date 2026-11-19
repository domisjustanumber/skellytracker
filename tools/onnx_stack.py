#!/usr/bin/env python3
"""Check, solve and apply the ONNX stack of this checkout: the pins, the EP packs and their GPU evidence.

Usage::

    uv run python tools/onnx_stack.py check [--wheel-dir DIR ...]
    uv run python tools/onnx_stack.py scan --wheel-dir DIR [--wheel-dir DIR ...]
    uv run python tools/onnx_stack.py solve --write-snapshot FILE [--out SOLUTION] [--allow-prerelease]
    uv run python tools/onnx_stack.py solve --snapshot FILE [--out SOLUTION] [--allow-prerelease]
    uv run python tools/onnx_stack.py apply SOLUTION [--dry-run]
    uv run python tools/onnx_stack.py apply --snapshot FILE [--allow-prerelease] [--dry-run]

``check`` uses no network. It prints the set hash: the hash of the ONNX Runtime distributions and of
each wheel of each user pack. It fails when:

- ``tools/ep_catalog.py --check`` finds a problem: the pins, the EP catalog and its lock must agree;
- a row of ``ep_evidence.yaml`` has a field that is missing or not valid: ``ep``, ``os``, ``gpu``
  (``10de:2484``), ``set`` (64 hex digits), ``source`` (``maintainer`` or ``field``) and ``result``
  (``pass`` or ``fail``) are necessary, and ``catalog_package`` is an optional string;
- a user pack is outside the ONNX Runtime range that its vendor tested, and its ``ort`` row has no
  ``exception`` with a decision entry (``entry``) that names this ONNX Runtime version
  (``ort_version``);
- ``ep_evidence.yaml`` has no row with ``source: maintainer``, ``result: pass`` and this set hash for
  a user pack with the status ``ready`` on Windows or on Linux. Each OS needs its own row. Evidence
  for a pack of another vendor than NVIDIA comes from reviewed reports, and this check does not need
  it;
- the telemetry check below finds a problem.

Telemetry (ADR-BZ7X). The Microsoft 1DS telemetry client of ONNX Runtime is present in a native
library (``.dll``, ``.pyd``, ``.dylib``, ``.so``, ``.so.N``) that holds ``OneCollector`` or
``mobile.events.data.microsoft.com``. The kill-switch string is ``ORT_DISABLE_TELEMETRY``. The scan
searches each marker as ASCII and as UTF-16LE, in any case. An HTTP import (``WINHTTP.dll``,
``libcurl``) is a hint only, and the scan does not use it. The ``telemetry`` list of
``ep_evidence.yaml`` is the reviewed record: one row for each package, version and OS (``Windows``,
``Linux``, ``macOS``), with ``client`` (true or false) and ``switch_verified``: an evidence reference
when a run showed that the variable switches the client off, else ``false``. A row with the client
and ``switch_verified: false`` needs a ``reason``.

- ``scan --wheel-dir DIR`` prints the result of each native library of each wheel in DIR. Run it
  on each wheel of a new candidate, and write its row before the bump.
- ``check --wheel-dir DIR`` scans each wheel of the pinned set that DIR holds: the ONNX Runtime
  core of each OS (files and sha256 from ``uv.lock``) and each wheel of each user pack (from
  ``ep_lock.yaml``). Without the file, the wheel is ``not-scanned``, and the line says so. It fails
  for a row that is not valid, for a file whose sha256 is not the locked one, for a scanned library
  with the client and no row, and for a row that the scan contradicts. It prints a ``WARNING`` line
  for a row with the client and ``switch_verified: false``. The pinned set can have such a row (user
  decision: stay on ONNX Runtime 1.30.0).
- ``solve`` and ``apply`` refuse a package version that is not in the current set when it has no
  row for an OS of the catalog, or a row with the client and ``switch_verified: false``. The core
  needs rows for Linux and macOS (``onnxruntime``) and for Windows (``onnxruntime-windowsml``), a
  pack for each platform of the catalog.

``solve --write-snapshot FILE`` reads the PEP 503 pages of ``onnxruntime``, ``onnxruntime-windowsml``,
``windowsml`` and the package of each user pack, and the PyPI JSON metadata (``requires_dist``) of
each ``windowsml`` release from the pinned one. It writes these facts to the snapshot FILE, a JSON
file with sorted keys. ``solve --snapshot FILE`` reads an existing snapshot and uses no network. The
solve itself reads only the snapshot, ``pyproject.toml`` and ``ep_catalog.yaml``. One snapshot always
gives one result. The result is the newest set that obeys each rule on each supported OS (Windows
x86_64, Linux x86_64 and macOS arm64, all on CPython 3.13):

- plain ``onnxruntime`` and ``onnxruntime-windowsml`` are the same ONNX Runtime release: their first
  three version parts are equal;
- the ``with-ort`` extra of the ``windowsml`` release pins the ``onnxruntime-windowsml`` version;
- ``onnxruntime`` has a cp313 wheel for manylinux x86_64 and for macOS arm64, and
  ``onnxruntime-windowsml`` and ``windowsml`` have a cp313 wheel for win_amd64;
- a pre-release is refused. Only ``--allow-prerelease`` allows a ``windowsml`` pre-release. The
  pinned ``windowsml`` version is allowed, because a person chose it;
- each user pack with the status ``ready`` has a pack version whose ``ort`` claim covers the ONNX
  Runtime release (``EpCatalog.ort_untested``), or whose ``ort`` claim has an ``exception`` with an
  ``entry`` and an ``ort_version`` equal to the release. An exception lifts the block only for that
  release. A claim belongs to the pack version of its row. The pack versions are the version of the
  pack row and each version of its ``newer_versions`` list. A newer pack version on the index that
  ``newer_versions`` does not name has no claim, and the solve reports it;
- the pack version of the pack row has a wheel for each platform of the catalog. A newer pack
  version without such a wheel is refused;
- each new package version has a telemetry row (see Telemetry above).

A row of ``newer_versions`` is the reviewed claim for one newer pack version. It is one line in flow
style, with ``version``, ``ort`` and an optional ``dependency_wheels`` map from a dependency package
of the pack to its new version, for example
``- {version: "0.3.0", ort: {verified_by_us: ["1.31.1"]}, dependency_wheels: {nvidia-cublas: "13.9.0.1"}}``.

The result is the newest set: the newest ONNX Runtime release first, then the newest version of each
pack. It names the current set, the proposed set, and one line for each newer candidate with the rule
that refused it. When no newer set obeys each rule, the result is "no bump". The solve does not read
GPU evidence: a proposed set needs new evidence, and ``check`` asks for it.

``apply`` writes the proposed set to ``pyproject.toml`` and ``ep_catalog.yaml`` of the working tree.
For a new pack version, it writes the ``version``, the ``ort`` claim and the dependency versions of
its ``newer_versions`` row to the pack row. It then removes each ``newer_versions`` row up to that
version, so that one claim is in one place. It refuses when these files do not hold the current set
of the solution, when ``newer_versions`` has no row for a proposed pack version, and when a text to
replace is not in its file exactly one time. It keeps the line ends. It never commits, and it runs no
other command: it prints the commands that a person must run next. It does not write
``ep_lock.yaml``: only ``tools/ep_catalog.py --refresh`` writes it. ``--dry-run`` prints the diff and
writes no file.

Not in the solve: the ``onnx`` pin, the wheels of the dependency packages of a pack, and the
``Requires-Dist`` of the pack wheels (only the reviewed claims of the catalog count).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import sys
import tomllib
import zipfile
from collections.abc import Callable
from pathlib import Path

import yaml
from packaging.requirements import Requirement
from packaging.utils import InvalidWheelFilename, canonicalize_name, parse_wheel_filename
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from skellytracker.core.eps import evidence  # noqa: E402 - after the path of this checkout
from skellytracker.core.eps.catalog import EpCatalog, revision_of  # noqa: E402

EVIDENCE_OS = ("Windows", "Linux")
EVIDENCE_VENDOR = "nvidia"
CATALOG = Path("skellytracker/core/eps/ep_catalog.yaml")
PYPI_JSON = "https://pypi.org/pypi/{package}/{version}/json"
PINS = {"onnxruntime": "onnxruntime", "onnxruntime-windowsml": "onnxruntime-windowsml", "windowsml": "windowsml[with-ort]"}
ENVIRONMENTS = {"win_amd64": r"win_amd64", "manylinux_x86_64": r"manylinux(?:_\d+_\d+|2014|2010|1)_x86_64",
                "macosx_arm64": r"macosx_\d+_\d+_(?:arm64|universal2)"}
PLAIN_ENVIRONMENTS = ("manylinux_x86_64", "macosx_arm64")
FOLLOW_UP = ("uv lock", "uv run python tools/ep_catalog.py --refresh", "uv run python tools/onnx_stack.py check")
EVIDENCE = Path("skellytracker/core/eps/ep_evidence.yaml")
OS_OF_PLATFORM = {"win_amd64": "Windows", "manylinux_x86_64": "Linux", "macosx_arm64": "macOS"}
CORE_OS = {"onnxruntime": ("Linux", "macOS"), "onnxruntime-windowsml": ("Windows",)}  # the core package of each OS
LIBRARY = re.compile(r"\.(?:dll|pyd|dylib|so)(?:\.\d+)*$", re.IGNORECASE)


def markers(words: tuple[str, ...]) -> re.Pattern:
    """One pattern for each word as ASCII and as UTF-16LE, in any case (IGNORECASE folds the ASCII letters of both forms)."""
    return re.compile(b"|".join(re.escape(word.encode(encoding)) for word in words for encoding in ("ascii", "utf-16-le")), re.IGNORECASE)


TELEMETRY_CLIENT = markers(("OneCollector", "mobile.events.data.microsoft.com"))
TELEMETRY_SWITCH = markers(("ORT_DISABLE_TELEMETRY",))


def ep_catalog_tool():
    spec = importlib.util.spec_from_file_location("ep_catalog", REPO_ROOT / "tools" / "ep_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(catalog: EpCatalog, rows: tuple[dict, ...]) -> list[str]:
    """The problems of the evidence rows, of the vendor ranges and of the GPU evidence. An empty list is a pass."""
    problems, current, valid = [], evidence.set_hash(catalog), []
    fields = {"ep": r".+", "os": r".+", "gpu": r"[0-9a-f]{4}:[0-9a-f]{4}", "set": r"[0-9a-f]{64}",
              "source": r"maintainer|field", "result": r"pass|fail"}
    for number, row in enumerate(rows):
        row = row if isinstance(row, dict) else {}
        bad = [name for name, pattern in fields.items()
               if not (isinstance(row.get(name), str) and re.fullmatch(pattern, row[name]))]
        bad += ["catalog_package"] if not isinstance(row.get("catalog_package", ""), str) else []
        if bad:
            problems.append(f"ep_evidence.yaml row {number}: the field {', '.join(bad)} is missing or not valid")
        else:
            valid.append(row)
    for key in catalog.keys():
        pack = catalog.pack(key)
        if pack is None or pack.get("status", "ready") != "ready":
            continue
        if "vendor_tested" in pack.get("ort", {}) and catalog.ort_untested(pack) and not excepted(pack, catalog.ort_version):
            problems.append(f"{key}: ONNX Runtime {catalog.ort_version} is outside the range that the vendor tested, "
                            f"{pack['ort']['vendor_tested']}, and no exception names this version")
        if pack.get("requires", {}).get("vendor") != EVIDENCE_VENDOR:
            continue
        problems += [f"{key}: no maintainer evidence on {os_name} for the set {current[:12]}" for os_name in EVIDENCE_OS
                     if not any(row["ep"] == key and row["os"] == os_name and row["set"] == current
                                and row["source"] == "maintainer" and row["result"] == "pass" for row in valid)]
    return problems


def excepted(claim: dict, ort: str) -> bool:
    """True when the `ort` claim of a pack row or a `newer_versions` row has an exception with an entry for ONNX Runtime `ort`."""
    exception = claim.get("ort", {}).get("exception") or {}
    return bool(exception.get("entry")) and exception.get("ort_version") == ort


def pack_claims(pack: dict) -> list[dict]:
    """The claim rows of a pack, newest first: each row of `newer_versions`, then the pack row."""
    return [*sorted(pack.get("newer_versions") or (), key=lambda row: Version(row["version"]), reverse=True), pack]


def scan_wheel(path: Path) -> list[tuple[str, bool, bool]]:
    """`(member, client, switch string)` of each native library of a wheel. A streamed byte search: no library loads."""
    found = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not LIBRARY.search(info.filename):
                continue
            client = switch = False
            tail = b""
            with archive.open(info) as member:
                while chunk := member.read(1 << 24):
                    block = tail + chunk
                    client = client or bool(TELEMETRY_CLIENT.search(block))
                    switch = switch or bool(TELEMETRY_SWITCH.search(block))
                    tail = block[-128:]  # longer than the longest marker in UTF-16LE (64 bytes)
            found.append((info.filename, client, switch))
    return found


def telemetry_rows(rows) -> tuple[list[dict], list[str]]:
    """The valid rows of the `telemetry` list of ep_evidence.yaml, and one problem for each row that is not valid."""
    valid, problems = [], []
    for number, row in enumerate(rows or ()):
        row = row if isinstance(row, dict) else {}
        text = {name: isinstance(row.get(name), str) and bool(row[name]) for name in ("package", "version", "switch_verified", "reason")}
        proof = row.get("switch_verified", False) is False or text["switch_verified"]
        reason = not row.get("client") or row.get("switch_verified", False) is not False or text["reason"]
        if text["package"] and text["version"] and row.get("os") in OS_OF_PLATFORM.values() and isinstance(row.get("client"), bool) \
                and proof and reason:
            valid.append(row)
        else:
            problems.append(f"ep_evidence.yaml telemetry row {number}: needs package, version, os (Windows, Linux or macOS), client "
                            "(true or false), switch_verified (an evidence reference or false) and, for a client without proof, a reason")
    return valid, problems


def telemetry_row(rows: list[dict], package: str, version: str, os_name: str) -> dict | None:
    return next((row for row in rows if canonicalize_name(row["package"]) == canonicalize_name(package) and row["version"] == version
                 and row["os"] == os_name), None)


def telemetry_refusals(rows: list[dict], package: str, version: str, os_names) -> list[str]:
    """Why a new package version cannot enter the set: no reviewed row, or the client and no proof that the switch works."""
    found = []
    for os_name in os_names:
        row = telemetry_row(rows, package, version, os_name)
        if row is None:
            found.append(f"{package} {version} on {os_name}: ep_evidence.yaml has no telemetry row (scan the wheel with "
                         "tools/onnx_stack.py scan)")
        elif row["client"] and row.get("switch_verified", False) is False:
            found.append(f"{package} {version} on {os_name}: it has the telemetry client, and no evidence shows that "
                         "ORT_DISABLE_TELEMETRY switches it off")
    return found


def pack_os_names(catalog: dict) -> list[str]:
    return [OS_OF_PLATFORM[platform] for platform in catalog["platforms"]]


def set_telemetry_refusals(proposed: dict, current: dict, catalog: dict, rows: list[dict]) -> list[str]:
    """The telemetry refusals of each package version of `proposed` that is not in `current`."""
    found = []
    for package, os_names in CORE_OS.items():
        if proposed[package] != current[package]:
            found += telemetry_refusals(rows, package, proposed[package], os_names)
    for pack in user_packs(catalog):
        version = proposed["packs"].get(pack["id"])
        if version is not None and version != current["packs"].get(pack["id"]):
            found += telemetry_refusals(rows, pack["package"], version, pack_os_names(catalog))
    return found


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1 << 24):
            digest.update(chunk)
    return digest.hexdigest()


def pinned_wheels(catalog: dict, lock: dict, uv_lock_text: str) -> list[tuple[str, str, str, str, str]]:
    """`(package, version, OS, file name, sha256)` of each wheel of the pinned set: the core of each OS and each user pack wheel."""
    found = []
    locked = {(row["name"], row.get("version")): row for row in tomllib.loads(uv_lock_text)["package"]}
    core = catalog["ort_core"]
    for package, version in ((core["package"], core["version"]), (core["windows"]["package"], core["windows"]["version"])):
        for wheel in locked.get((package, version), {}).get("wheels", ()):
            filename = wheel["url"].rsplit("/", 1)[-1]
            environments = {env for tag in parse_wheel_filename(filename)[3] for env in ENVIRONMENTS if fits(tag, env)}
            found += [(package, version, OS_OF_PLATFORM[env], filename, wheel["hash"].removeprefix("sha256:"))
                      for env in sorted(environments) if OS_OF_PLATFORM[env] in CORE_OS[package]]
    for pack in user_packs(catalog):
        for platform, row in sorted(lock.get("packs", {}).get(pack["id"], {}).items()):
            found += [(wheel["package"], wheel["version"], OS_OF_PLATFORM[platform], wheel["filename"], wheel["sha256"])
                      for wheel in row["wheels"]]
    return found


def telemetry_check(wheels: list[tuple[str, str, str, str, str]], rows: list[dict], wheel_dirs: list[Path]) -> tuple[list[str], list[str]]:
    """`(lines, problems)` of the telemetry check of the pinned set. A wheel that no folder holds is `not-scanned`, never a pass."""
    lines, problems = [], []
    for package, version, os_name, filename, sha256 in wheels:
        name, row = f"{package} {version} on {os_name}", telemetry_row(rows, package, version, os_name)
        path = next((folder / filename for folder in wheel_dirs if (folder / filename).is_file()), None)
        reviewed = "no reviewed row" if row is None else f"reviewed row: client {'yes' if row['client'] else 'no'}"
        client = None
        if path is None:
            lines.append(f"telemetry: {name}: not-scanned ({filename} is not in a --wheel-dir); {reviewed}")
        elif sha256_of(path) != sha256:
            problems.append(f"telemetry: {name}: {path.name} is not the locked file (sha256)")
        else:
            libraries = scan_wheel(path)
            client = any(found for _, found, _ in libraries)
            lines += [f"telemetry: {filename}!{member}: client {'yes' if found else 'no'}, switch string {'yes' if switch else 'no'}"
                      for member, found, switch in libraries if found or switch]
            lines.append(f"telemetry: {name}: {len(libraries)} libraries scanned, client {'yes' if client else 'no'}; {reviewed}")
            if client and row is None:
                problems.append(f"telemetry: {name}: a library has the telemetry client, and ep_evidence.yaml has no telemetry row")
            elif row is not None and row["client"] != client:
                problems.append(f"telemetry: {name}: the reviewed row says client {row['client']}, the scan found {client}")
        if row is not None and row["client"] and row.get("switch_verified", False) is False and client is not False:
            lines.append(f"WARNING: telemetry: {name} has the telemetry client, and no run has shown that ORT_DISABLE_TELEMETRY "
                         f"switches it off: {row['reason']}")
    return lines, problems


def flow(value) -> str:
    """`value` in the flow style of ep_catalog.yaml: plain keys and quoted strings."""
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key}: {flow(item)}" for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(map(flow, value)) + "]"
    return json.dumps(value)


def replace_once(text: str, old: str, new: str, where: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"{where}: the text {old!r} is there {text.count(old)} times, not one time")
    return text.replace(old, new)


def user_packs(catalog: dict) -> list[dict]:
    """The pack row of each EP key that is not reserved, with the status `ready`."""
    return [row["packs"][0] for row in catalog["eps"].values()
            if row["kind"] != "reserved" and row.get("packs") and row["packs"][0].get("status", "ready") == "ready"]


def current_set(pyproject_text: str, catalog: dict) -> dict:
    """The pinned set of the working tree: the three ONNX Runtime pins and the version of each user pack."""
    found = {}
    for key, requirement in PINS.items():
        hits = re.findall(rf'"{re.escape(requirement)}==([^ ";]+) ;', pyproject_text)
        if len(hits) != 1:
            raise ValueError(f"pyproject.toml: the pin of {requirement} is there {len(hits)} times, not one time")
        found[key] = hits[0]
    return {**found, "packs": {pack["id"]: pack["version"] for pack in user_packs(catalog)}}


def snapshot(catalog: dict, windowsml_floor: str, get: Callable[[str], bytes] | None = None) -> dict:
    """The facts of the indexes that the solve reads. Only this function uses the network."""
    tool = ep_catalog_tool()
    get = get or tool.http_get
    pages = dict.fromkeys(PINS, catalog["indexes"]["pypi"])
    pages |= {pack["package"]: catalog["indexes"][pack["index"]] for pack in user_packs(catalog)}
    pages = {name: index + canonicalize_name(name) + "/" for name, index in pages.items()}
    wheels = {name: sorted({text for _, text in tool.Anchors(get(url).decode("utf-8", "replace")).found if text.endswith(".whl")})
              for name, url in pages.items()}
    requires = {}
    for version in sorted({str(v) for v in wheel_environments(wheels["windowsml"]) if v >= Version(windowsml_floor)}, key=Version):
        info = json.loads(get(PYPI_JSON.format(package="windowsml", version=version)))["info"]
        requires[version] = sorted(info.get("requires_dist") or [])
    return {"schema": 1, "pages": pages, "wheels": wheels, "windowsml_requires_dist": requires}


def fits(tag, environment: str) -> bool:
    """True when a wheel tag installs on CPython 3.13 (not free-threaded) in a supported environment."""
    if tag.platform != "any" and not re.fullmatch(ENVIRONMENTS[environment], tag.platform):
        return False
    if tag.abi == "abi3":
        return bool(re.fullmatch(r"cp3\d+", tag.interpreter)) and int(tag.interpreter[3:]) <= 13
    return tag.interpreter in ("cp313", "py3", "py313") and tag.abi in ("cp313", "none")


def wheel_environments(filenames: list[str]) -> dict[Version, set[str]]:
    """The supported environments of each version that has a wheel. A file name that is not a wheel name is ignored."""
    found: dict[Version, set[str]] = {}
    for filename in filenames:
        try:
            _, version, _, tags = parse_wheel_filename(filename)
        except InvalidWheelFilename:
            continue
        found.setdefault(version, set()).update(env for env in ENVIRONMENTS for tag in tags if fits(tag, env))
    return found


def release(version: Version) -> str:
    return ".".join(str(part) for part in (*version.release, 0, 0)[:3])


def windowsml_pin(lines: list[str]) -> Version | None:
    """The exact `onnxruntime-windowsml` version that the `with-ort` extra pins, on Windows."""
    environment = {"extra": "with-ort", "sys_platform": "win32", "platform_system": "Windows", "os_name": "nt"}
    for line in lines:
        requirement = Requirement(line)
        if canonicalize_name(requirement.name) != "onnxruntime-windowsml":
            continue
        if requirement.marker is not None and not requirement.marker.evaluate(environment):
            continue
        exact = [spec.version for spec in requirement.specifier if spec.operator == "=="]
        if len(exact) == 1:
            return Version(exact[0])
    return None


def set_key(row: dict) -> tuple[Version, ...]:
    return tuple(Version(row[key]) for key in PINS) + tuple(Version(version) for _, version in sorted(row["packs"].items()))


def solve(snap: dict, catalog: dict, current: dict, allow_prerelease: bool = False, telemetry: list[dict] | None = None) -> dict:
    """The newest set that obeys each rule of the module docstring. A pure function of its arguments.

    `telemetry` holds the valid telemetry rows of ep_evidence.yaml. With no rows, each new package version is refused.
    """
    telemetry = telemetry or []
    plain = wheel_environments(snap["wheels"]["onnxruntime"])
    windows = wheel_environments(snap["wheels"]["onnxruntime-windowsml"])
    windowsml = wheel_environments(snap["wheels"]["windowsml"])
    claims = EpCatalog(data=catalog, lock={}, revision="")
    rejected, pack_reasons, options = [], [], {}
    for pack in user_packs(catalog):
        versions = wheel_environments(snap["wheels"][pack["package"]])
        named = {Version(row["version"]) for row in pack_claims(pack)}
        rejected += [f"{pack['id']} {v}: ep_catalog.yaml records no ONNX Runtime claim for this pack version"
                     for v in sorted(versions, reverse=True) if v > Version(pack["version"]) and v not in named]
        options[pack["id"]] = []
        for row in pack_claims(pack):
            missing = sorted(set(catalog["platforms"]) - versions.get(Version(row["version"]), set()))
            if missing:
                (pack_reasons if row is pack else rejected).append(f"{pack['id']} {row['version']} has no wheel for {', '.join(missing)}")
            if row is pack or not missing:
                options[pack["id"]].append(row)
    floor = release(Version(current["onnxruntime"]))
    releases = sorted({r for r in map(release, [*plain, *windows]) if Version(r) >= Version(floor)}, key=Version, reverse=True)
    proposed = None
    for ort in releases:
        reasons, windowsml_reasons = list(pack_reasons), []
        finals = sorted((v for v in plain if release(v) == ort and not v.is_prerelease), reverse=True)
        chosen_plain = next((v for v in finals if set(PLAIN_ENVIRONMENTS) <= plain[v]), None)
        if not finals:
            reasons.append(f"onnxruntime has no release {ort}")
        elif chosen_plain is None:
            reasons.append(f"onnxruntime {finals[0]} has no cp313 wheel for {', '.join(sorted(set(PLAIN_ENVIRONMENTS) - plain[finals[0]]))}")
        chosen_packs, skipped = {}, []
        for pack in user_packs(catalog):
            rows = options[pack["id"]]
            refused = {row["version"]: [] if row["version"] == current["packs"].get(pack["id"])
                       else telemetry_refusals(telemetry, pack["package"], row["version"], pack_os_names(catalog)) for row in rows}
            covers = [row for row in rows if not claims.ort_untested(row, ort) or excepted(row, ort)]
            fit = next((row for row in covers if not refused[row["version"]]), None)
            if fit is None and covers:
                reasons += [reason for row in covers for reason in refused[row["version"]]]
                continue
            if fit is None:
                reasons.append(f"{pack['id']}: no claim covers ONNX Runtime {ort}, and no exception names it: "
                               + "; ".join(f"{row['version']} {row.get('ort', {})}" for row in rows))
                continue
            chosen_packs[pack["id"]] = fit["version"]
            skipped += [f"{pack['id']} {row['version']}: " + ("; ".join(refused[row["version"]]) if row in covers else
                                                              f"the claim {row.get('ort', {})} does not cover ONNX Runtime {ort}")
                        for row in rows[:rows.index(fit)]]
        chosen_windowsml = None
        for version in sorted(windowsml, reverse=True):
            pin = windowsml_pin(snap["windowsml_requires_dist"].get(str(version), []))  # an older release has no metadata
            if pin is None or release(pin) != ort:
                continue
            if version.is_prerelease and not allow_prerelease and str(version) != current["windowsml"]:
                windowsml_reasons.append(f"windowsml {version} is a pre-release (allow it with --allow-prerelease)")
            elif "win_amd64" not in windowsml[version]:
                windowsml_reasons.append(f"windowsml {version} has no cp313 wheel for win_amd64")
            elif "win_amd64" not in windows.get(pin, set()):
                windowsml_reasons.append(f"onnxruntime-windowsml {pin} (the pin of windowsml {version}) has no cp313 wheel for win_amd64")
            else:
                chosen_windowsml = (version, pin)
                break
        if chosen_windowsml is None:
            reasons += windowsml_reasons or [f"no windowsml release pins onnxruntime-windowsml {ort}"]
        if chosen_plain is not None and chosen_windowsml is not None:
            core = {"onnxruntime": str(chosen_plain), "onnxruntime-windowsml": str(chosen_windowsml[1])}
            reasons += [reason for package, os_names in CORE_OS.items() if core[package] != current[package]
                        for reason in telemetry_refusals(telemetry, package, core[package], os_names)]
        if reasons:
            rejected.append(f"ONNX Runtime {ort}: {'; '.join(reasons)}")
            continue
        proposed = {"onnxruntime": str(chosen_plain), "onnxruntime-windowsml": str(chosen_windowsml[1]),
                    "windowsml": str(chosen_windowsml[0]), "packs": chosen_packs}
        rejected += [f"ONNX Runtime {ort}: {reason}" for reason in [*windowsml_reasons, *skipped]]
        break
    canonical = json.dumps(snap, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": 1, "snapshot_sha256": hashlib.sha256(canonical).hexdigest(), "allow_prerelease": allow_prerelease,
            "current": current, "proposed": proposed,
            "bump": proposed is not None and set_key(proposed) > set_key(current), "rejected": rejected}


def edits(current: dict, proposed: dict) -> list[tuple[Path, str, str]]:
    """`(file, old text, new text)` of each replacement that writes `proposed` over `current`."""
    found = [(Path("pyproject.toml"), f'"{requirement}=={current[key]} ;', f'"{requirement}=={proposed[key]} ;')
             for key, requirement in PINS.items()]
    found += [(CATALOG, f'version: "{current["onnxruntime"]}", windows:', f'version: "{proposed["onnxruntime"]}", windows:'),
              (CATALOG, f'windows: {{package: onnxruntime-windowsml, version: "{current["onnxruntime-windowsml"]}"}}',
               f'windows: {{package: onnxruntime-windowsml, version: "{proposed["onnxruntime-windowsml"]}"}}')]
    return [edit for edit in found if edit[1] != edit[2]]


def pack_edit(text: str, pack: dict, claim: dict) -> str:
    """`text` with the pack row at the version, the `ort` claim and the dependency versions of its `newer_versions` row `claim`.

    Each `newer_versions` row up to that version leaves the row. An empty list leaves with its key.
    """
    where = f"{CATALOG.as_posix()} {pack['id']}"

    def one(pattern: str, text: str) -> re.Match:
        found = list(re.finditer(pattern, text, re.MULTILINE))
        if len(found) != 1:
            raise ValueError(f"{where}: {len(found)} lines match {pattern!r}, not one line")
        return found[0]

    head = one(rf"^([ \t]*)- id: {re.escape(pack['id'])}\r?$", text)
    end = re.compile(rf"\n {{0,{len(head.group(1))}}}\S").search(text, head.end())
    start, end = head.start(), end.start() if end else len(text)
    row = replace_once(text[start:end], f'version: "{pack["version"]}"', f'version: "{claim["version"]}"', where)
    ort = one(r"^([ \t]*ort: )[^\r\n]*", row)
    row = row[:ort.start()] + ort.group(1) + flow(claim["ort"]) + row[ort.end():]
    wheels = {wheel["package"]: wheel for wheel in pack.get("dependency_wheels", ())}
    for package, version in (claim.get("dependency_wheels") or {}).items():
        old = f"package: {package}, index: {wheels[package]['index']}, version: "
        row = replace_once(row, old + flow(wheels[package]["version"]) + "}", old + flow(version) + "}", where)
    newer = pack.get("newer_versions") or ()
    gone = [r["version"] for r in newer if Version(r["version"]) <= Version(claim["version"])]
    for version in gone + (["newer_versions"] if len(gone) == len(newer) else []):
        line = one(r"^[ \t]*newer_versions:[ \t]*\r?\n" if version == "newer_versions"
                   else rf'^[ \t]*- \{{version: "{re.escape(version)}"[^\r\n]*\r?\n', row)
        row = row[:line.start()] + row[line.end():]
    return text[:start] + row + text[end:]


def apply(solution: dict, root: Path, dry_run: bool = False) -> int:
    """Write the proposed set of `solution` to the files under `root`. All files change, or no file changes."""
    texts = {path: (root / path).read_bytes().decode("utf-8") for path in (Path("pyproject.toml"), CATALOG)}
    data = yaml.safe_load(texts[CATALOG])
    now = current_set(texts[Path("pyproject.toml")], data)
    if now != solution["current"]:
        print(f"apply: refused. The working tree holds {now}, not the current set of the solution, {solution['current']}.")
        return 1
    if not solution["bump"]:
        print("apply: no bump. No file changes.")
        return 0
    packs, claimed = {pack["id"]: pack for pack in user_packs(data)}, {}
    if set(solution["proposed"]["packs"]) != set(packs):
        print(f"apply: refused. The solution names the packs {sorted(solution['proposed']['packs'])}, not {sorted(packs)}.")
        return 1
    for pack_id, version in solution["proposed"]["packs"].items():
        claimed[pack_id] = next((row for row in pack_claims(packs[pack_id]) if row["version"] == version), None)
        if claimed[pack_id] is None:
            print(f"apply: refused. The newer_versions list of {pack_id} in ep_catalog.yaml has no claim for {version}.")
            return 1
    rows, _ = telemetry_rows((yaml.safe_load((root / EVIDENCE).read_text(encoding="utf-8")) or {}).get("telemetry"))
    refused = set_telemetry_refusals(solution["proposed"], now, data, rows)
    if refused:
        print("apply: refused. " + " ".join(f"{reason}." for reason in refused))
        return 1
    new = dict(texts)
    for path, old, replacement in edits(now, solution["proposed"]):
        new[path] = replace_once(new[path], old, replacement, path.as_posix())
    for pack_id, claim in claimed.items():
        if claim is not packs[pack_id]:
            new[CATALOG] = pack_edit(new[CATALOG], packs[pack_id], claim)
    for path in texts:
        if dry_run:
            sys.stdout.writelines(difflib.unified_diff(texts[path].splitlines(keepends=True), new[path].splitlines(keepends=True),
                                                       f"a/{path.as_posix()}", f"b/{path.as_posix()}"))
        else:
            (root / path).write_bytes(new[path].encode("utf-8"))
    if not dry_run:
        print("apply: written. Nothing is committed. apply does not write uv.lock or ep_lock.yaml.")
        print("Run these commands, then add GPU evidence for the new set hash:")
        print("\n".join(f"  {command}" for command in FOLLOW_UP))
    return 0


def print_solution(solution: dict) -> None:
    def text(row):
        return ", ".join(f"{key} {row[key]}" for key in PINS) + "".join(f", {pack} {v}" for pack, v in sorted(row["packs"].items()))
    print(f"snapshot sha256: {solution['snapshot_sha256']}")
    print(f"current: {text(solution['current'])}")
    print(f"proposed: {text(solution['proposed'])}" if solution["bump"] else "no bump")
    print("\n".join(f"refused: {line}" for line in solution["rejected"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["check", "scan", "solve", "apply"])
    parser.add_argument("solution", nargs="?", type=Path, help="apply: the solution file of solve --out")
    parser.add_argument("--snapshot", type=Path, help="solve, apply: read this snapshot and use no network")
    parser.add_argument("--write-snapshot", type=Path, help="solve: read the indexes and write the snapshot to this file")
    parser.add_argument("--out", type=Path, help="solve: write the solution to this file")
    parser.add_argument("--allow-prerelease", action="store_true", help="solve: allow a pre-release of windowsml")
    parser.add_argument("--dry-run", action="store_true", help="apply: print the diff and write no file")
    parser.add_argument("--wheel-dir", type=Path, action="append", default=[], help="check, scan: a folder of wheel files to scan")
    args = parser.parse_args(argv)
    if args.command == "scan":
        if not args.wheel_dir:
            parser.error("scan needs --wheel-dir")
        for path in sorted(p for folder in args.wheel_dir for p in folder.glob("*.whl")):
            for member, client, switch in scan_wheel(path):
                print(f"{path.name}!{member}: client {'yes' if client else 'no'}, switch string {'yes' if switch else 'no'}")
        return 0
    tool = ep_catalog_tool()
    catalog_text = (tool.EPS / "ep_catalog.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(catalog_text)
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    evidence_data = yaml.safe_load((REPO_ROOT / EVIDENCE).read_text(encoding="utf-8")) or {}
    telemetry, telemetry_problems = telemetry_rows(evidence_data.get("telemetry"))
    if args.command == "apply" and args.solution:
        return apply(json.loads(args.solution.read_text(encoding="utf-8")), REPO_ROOT, args.dry_run)
    if args.command in ("solve", "apply"):
        current = current_set(pyproject_text, data)
        if args.snapshot:
            snap = json.loads(args.snapshot.read_text(encoding="utf-8"))
        elif args.command == "solve" and args.write_snapshot:
            snap = snapshot(data, current["windowsml"])
            args.write_snapshot.write_text(json.dumps(snap, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
        else:
            parser.error("solve needs --snapshot or --write-snapshot; apply needs a solution file or --snapshot")
        solution = solve(snap, data, current, args.allow_prerelease, telemetry)
        if args.command == "apply":
            return apply(solution, REPO_ROOT, args.dry_run)
        print_solution(solution)
        if args.out:
            args.out.write_text(json.dumps(solution, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
        return 0
    lock = yaml.safe_load((tool.EPS / "ep_lock.yaml").read_text(encoding="utf-8")) or {}
    catalog = EpCatalog(data=data, lock=lock, revision=revision_of(catalog_text))
    rows = tuple(evidence_data.get("rows") or ())
    uv_lock_text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    problems = tool.check(data, lock, catalog_text, pyproject_text, uv_lock_text)
    problems += check(catalog, rows) + telemetry_problems
    lines, found = telemetry_check(pinned_wheels(data, lock, uv_lock_text), telemetry, args.wheel_dir)
    problems += found
    print(f"set hash: {evidence.set_hash(catalog)}")
    for line in lines:
        print(line)
    for problem in problems:
        print(problem)
    print("ONNX stack: pass" if not problems else f"ONNX stack: {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
