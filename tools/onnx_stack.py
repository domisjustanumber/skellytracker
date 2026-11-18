#!/usr/bin/env python3
"""Check, solve and apply the ONNX stack of this checkout: the pins, the EP packs and their GPU evidence.

Usage::

    uv run python tools/onnx_stack.py check
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
  it.

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
  version without such a wheel is refused.

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


def solve(snap: dict, catalog: dict, current: dict, allow_prerelease: bool = False) -> dict:
    """The newest set that obeys each rule of the module docstring. A pure function of its arguments."""
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
            fit = next((row for row in rows if not claims.ort_untested(row, ort) or excepted(row, ort)), None)
            if fit is None:
                reasons.append(f"{pack['id']}: no claim covers ONNX Runtime {ort}, and no exception names it: "
                               + "; ".join(f"{row['version']} {row.get('ort', {})}" for row in rows))
                continue
            chosen_packs[pack["id"]] = fit["version"]
            skipped += [f"{pack['id']} {row['version']}: the claim {row.get('ort', {})} does not cover ONNX Runtime {ort}"
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
    parser.add_argument("command", choices=["check", "solve", "apply"])
    parser.add_argument("solution", nargs="?", type=Path, help="apply: the solution file of solve --out")
    parser.add_argument("--snapshot", type=Path, help="solve, apply: read this snapshot and use no network")
    parser.add_argument("--write-snapshot", type=Path, help="solve: read the indexes and write the snapshot to this file")
    parser.add_argument("--out", type=Path, help="solve: write the solution to this file")
    parser.add_argument("--allow-prerelease", action="store_true", help="solve: allow a pre-release of windowsml")
    parser.add_argument("--dry-run", action="store_true", help="apply: print the diff and write no file")
    args = parser.parse_args(argv)
    tool = ep_catalog_tool()
    catalog_text = (tool.EPS / "ep_catalog.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(catalog_text)
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
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
        solution = solve(snap, data, current, args.allow_prerelease)
        if args.command == "apply":
            return apply(solution, REPO_ROOT, args.dry_run)
        print_solution(solution)
        if args.out:
            args.out.write_text(json.dumps(solution, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
        return 0
    lock = yaml.safe_load((tool.EPS / "ep_lock.yaml").read_text(encoding="utf-8")) or {}
    catalog = EpCatalog(data=data, lock=lock, revision=revision_of(catalog_text))
    rows = tuple((yaml.safe_load((tool.EPS / "ep_evidence.yaml").read_text(encoding="utf-8")) or {}).get("rows") or ())
    problems = tool.check(data, lock, catalog_text, pyproject_text, (REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    problems += check(catalog, rows)
    print(f"set hash: {evidence.set_hash(catalog)}")
    for problem in problems:
        print(problem)
    print("ONNX stack: pass" if not problems else f"ONNX stack: {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
