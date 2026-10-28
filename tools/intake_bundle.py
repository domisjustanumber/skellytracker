#!/usr/bin/env python3
"""Pack, list and verify the hand-over bundles in `intakes/`.

The rules are in `specs/model-sidecar/model-addition-workflow/hand-over.md`.

Usage::

    python -B tools/intake_bundle.py pack --from DIR --fields FILE.json [--root INTAKES]
    python -B tools/intake_bundle.py list [--root INTAKES]
    uv run python -B tools/intake_bundle.py verify BUNDLE [--root INTAKES]
    uv run python -B tools/intake_bundle.py batch --fields FILE --out DIR [--inputs DIR] [--root INTAKES]

`pack` and `list` use only the standard library, so any Python 3 interpreter runs them. `verify`
reads YAML, so it runs in the environment of this repository. `batch` is the batch-conversion
check. It imports onnx, onnxruntime and the skellytracker converter, so it runs only in the `.venv`
of this checkout. `--fields` is a fields file or a manifest. No sub-command writes a response
file: the skellytracker session writes them.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import check_private_data

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "intakes"
SPEC = "specs/model-sidecar"
SECTION_FOLDERS = ("format", "common", "pre", "post")

BUNDLE_FORMAT = 1
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".json", ".txt", ".csv", ".toml"}
VECTOR_LIMIT = 256 * 1024

KINDS = ("model", "proposal")
CHANGE_CLASSES = ("vnext", "clarification", "breaking")
VERDICTS = ("describes", "does not describe", "pending")
BATCH_VERDICTS = ("converts", "does not convert", "not applicable", "to run")
BATCH_REASONS = ("host-runtime-cannot-load", "missing-verification-batch", "no-signal")
STATES = (
    "needs-contributor",
    "waiting",
    "recorded",
    "accepted",
    "landed",
    "rejected",
    "resolved-otherwise",
    "closed",
)
FINISHED = {"landed", "rejected", "resolved-otherwise", "closed"}
OWNING = {"recorded", "accepted", "landed"}

COMMON_KEYS = (
    "bundle_format",
    "kind",
    "name",
    "contributor",
    "version",
    "source_commit",
    "spec_commit",
    "created",
    "sections",
    "related",
    "files",
    "external",
)
KIND_KEYS = {
    "model": ("verdict", "batch_conversion", "batch_conversion_reason"),
    "proposal": ("change_class", "base", "depends_on", "contributes_to"),
}
COMPUTED = ("files", "version", "created")
EXTERNAL_KEYS = ("path", "role", "size", "batch", "precision", "published")
RESPONSE_KEYS = (
    "answers_version",
    "date",
    "state",
    "findings",
    "batch_conversion",
    "waiting_on",
    "records",
    "decision",
    "subject",
    "changes",
)
PROVENANCE_KEYS = {
    "exporter",
    "exporter_path",
    "kind",
    "exporter_layout_path",
    "tracked",
    "commit",
    "source",
}
FRAGMENT_KEYS = {"exporter", "exporter_path", "tracked", "commit", "notes"}

SOURCE_BATCH = 3
PROFILE = {"profile_id": "static-batch-v1", "source_batch_size": SOURCE_BATCH}
VERIFICATION_BATCHES = (1, 2, 3, 4)
TARGETS = (1, 2, 4)
DYNAMIC_BATCHES = (1, 2, 3)
TOLERANCE = {"fp32": 1e-5, "fp16": 1e-3}
INPUT_B_ITEMS = 4

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CONTRIBUTOR = re.compile(r"^[a-z0-9][a-z0-9-]*$")
BUNDLE_ID = re.compile(
    r"^(?P<kind>model|proposal)-(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)@(?P<contributor>[a-z0-9][a-z0-9-]*)$"
)
NO_GIT = "none (no git repo)"


class BundleError(Exception):
    """A bundle or a fields file that does not obey the hand-over rules."""


def bundle_id(manifest: dict) -> str:
    return f"{manifest['kind']}-{manifest['name']}@{manifest['contributor']}"


def is_text(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_SUFFIXES


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------------------------
# Manifest and response checks (standard library only)
# --------------------------------------------------------------------------------------------


def _is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def manifest_problems(manifest: dict, computed: bool = True) -> list[str]:
    """Return one text for each manifest key that is missing, unknown or has a bad value.

    With `computed=False`, the keys that `pack` computes must be absent (a fields file).
    """
    problems: list[str] = []
    kind = manifest.get("kind")
    if kind not in KINDS:
        return [f"kind must be one of {list(KINDS)}, not {kind!r}"]
    allowed = set(COMMON_KEYS) | set(KIND_KEYS[kind])
    required = allowed if computed else allowed - set(COMPUTED)
    problems += [f"missing key {key}" for key in sorted(required - set(manifest))]
    problems += [f"unknown key {key}" for key in sorted(set(manifest) - required)]
    get = manifest.get
    if get("bundle_format", BUNDLE_FORMAT) != BUNDLE_FORMAT:
        problems.append(f"bundle_format must be {BUNDLE_FORMAT}")
    if "name" in manifest and not NAME.match(str(get("name"))):
        problems.append("name must be a slug or a model_id (letters, digits, '.', '_', '-')")
    if "contributor" in manifest and not CONTRIBUTOR.match(str(get("contributor"))):
        problems.append("contributor must be the lower-case repo name")
    if "source_commit" in manifest and not (
        get("source_commit") == NO_GIT or SHA40.match(str(get("source_commit")))
    ):
        problems.append(f"source_commit must be 40 hex digits or {NO_GIT!r}")
    if "spec_commit" in manifest and not SHA40.match(str(get("spec_commit"))):
        problems.append("spec_commit must be 40 hex digits")
    if computed and not DATE.match(str(get("created", ""))):
        problems.append("created must be YYYY-MM-DD")
    if computed and not (isinstance(get("version"), int) and get("version", 0) >= 1):
        problems.append("version must be an integer of 1 or more")
    if "sections" in manifest and not (_is_str_list(get("sections")) and get("sections")):
        problems.append("sections must be a list of one or more section IDs")
    if "related" in manifest and not _is_str_list(get("related")):
        problems.append("related must be a list of bundle IDs")
    if kind == "proposal":
        if "change_class" in manifest and get("change_class") not in CHANGE_CLASSES:
            problems.append(f"change_class must be one of {list(CHANGE_CLASSES)}")
        problems += [
            f"{key} must be a string or null"
            for key in ("base", "contributes_to")
            if key in manifest and not (get(key) is None or isinstance(get(key), str))
        ]
        if "depends_on" in manifest and not _is_str_list(get("depends_on")):
            problems.append("depends_on must be a list of bundle IDs")
    else:
        if "verdict" in manifest and get("verdict") not in VERDICTS:
            problems.append(f"verdict must be one of {list(VERDICTS)}")
        if "batch_conversion" in manifest and get("batch_conversion") not in BATCH_VERDICTS:
            problems.append(f"batch_conversion must be one of {list(BATCH_VERDICTS)}")
        reason = get("batch_conversion_reason")
        if get("batch_conversion") == "to run":
            if reason not in BATCH_REASONS:
                problems.append(f"batch_conversion_reason must be one of {list(BATCH_REASONS)}")
        elif reason is not None:
            problems.append("batch_conversion_reason must be null unless batch_conversion is 'to run'")
    external = get("external", [])
    if not isinstance(external, list):
        problems.append("external must be a list")
        external = []
    for number, item in enumerate(external, 1):
        keys = set(EXTERNAL_KEYS) | ({"sha256"} if computed else set())
        if not isinstance(item, dict) or set(item) != keys:
            problems.append(f"external[{number}] must have exactly the keys {sorted(keys)}")
            continue
        if not str(item["path"]).startswith("../../"):
            problems.append(f"external[{number}].path must start with ../../")
        if not (isinstance(item["batch"], int) or item["batch"] == "dynamic"):
            problems.append(f"external[{number}].batch must be an integer or 'dynamic'")
        if not isinstance(item["published"], bool):
            problems.append(f"external[{number}].published must be true or false")
        if computed and not SHA64.match(str(item["sha256"])):
            problems.append(f"external[{number}].sha256 must be 64 hex digits")
    if computed:
        files = get("files", [])
        if not isinstance(files, list):
            problems.append("files must be a list")
            files = []
        for number, item in enumerate(files, 1):
            if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"}:
                problems.append(f"files[{number}] must have exactly the keys path, sha256, bytes")
                continue
            path = str(item["path"])
            if path.startswith("/") or ".." in Path(path).parts or "\\" in path:
                problems.append(f"files[{number}].path must be relative, with '/' and no '..'")
            if not SHA64.match(str(item["sha256"])) or not isinstance(item["bytes"], int):
                problems.append(f"files[{number}] needs a 64 hex sha256 and an integer bytes")
    return problems


def response_problems(response: object) -> list[str]:
    """Return one text for each problem in the schema of one response file."""
    if not isinstance(response, dict):
        return ["the response is not a mapping"]
    problems: list[str] = []
    allowed = set(RESPONSE_KEYS) | {"resolution"}
    problems += [f"missing key {key}" for key in sorted(set(RESPONSE_KEYS) - set(response))]
    problems += [f"unknown key {key}" for key in sorted(set(response) - allowed)]
    if not isinstance(response.get("answers_version"), int):
        problems.append("answers_version must be an integer")
    if not DATE.match(str(response.get("date", ""))):
        problems.append("date must be YYYY-MM-DD")
    state = response.get("state")
    if state not in STATES:
        problems.append(f"state must be one of {list(STATES)}")
    problems += [
        f"{key} must be a list of strings"
        for key in ("findings", "waiting_on", "records", "changes")
        if key in response and not _is_str_list(response[key])
    ]
    if response.get("batch_conversion") not in (None, *BATCH_VERDICTS):
        problems.append(f"batch_conversion must be null or one of {list(BATCH_VERDICTS)}")
    problems += [
        f"{key} must be a string or null"
        for key in ("decision", "subject")
        if not (response.get(key) is None or isinstance(response.get(key), str))
    ]
    if str(response.get("decision") or "").upper().startswith("ADR-"):
        problems.append("decision must be the bare ID, with no ADR- prefix")
    resolution = response.get("resolution")
    if state in ("rejected", "resolved-otherwise") and not isinstance(resolution, dict):
        problems.append(f"state {state} needs a resolution mapping")
    if state == "resolved-otherwise" and isinstance(resolution, dict):
        keys = ("by", "sections", "goals", "contributor_action")
        problems += [f"resolution needs the key {key}" for key in keys if key not in resolution]
        goals = resolution.get("goals") or []
        if any(not isinstance(g, dict) or g.get("status") not in ("met", "not-met") for g in goals):
            problems.append("each resolution goal needs goal, met_by and status met or not-met")
    if state == "rejected" and isinstance(resolution, dict) and not resolution.get("reason"):
        problems.append("a rejected response needs resolution.reason")
    return problems


# --------------------------------------------------------------------------------------------
# Reading the folder
# --------------------------------------------------------------------------------------------


def _numbered(folder: Path, prefix: str, suffix: str = "") -> list[tuple[int, Path]]:
    pattern = re.compile(rf"^{prefix}(\d+){re.escape(suffix)}$")
    found = []
    if folder.is_dir():
        for child in folder.iterdir():
            match = pattern.match(child.name)
            if match:
                found.append((int(match.group(1)), child))
    return sorted(found)


def read_manifest(version_dir: Path) -> dict | None:
    path = version_dir / "manifest.yaml"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def current_version(bundle_dir: Path) -> tuple[int, Path] | None:
    """Return the highest version folder that has a manifest, or None. A version with no manifest is in progress."""
    complete = [(k, d) for k, d in _numbered(bundle_dir, "v") if d.is_dir() and (d / "manifest.yaml").is_file()]
    return complete[-1] if complete else None


def responses(bundle_dir: Path) -> list[dict]:
    """Return the response files in order. The session writes them as JSON."""
    result = []
    for _, path in _numbered(bundle_dir / "responses", "r", ".yaml"):
        try:
            result.append(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            result.append({"state": "unreadable"})
    return result


def bundles(root: Path) -> dict[str, dict]:
    """Return each bundle in `root` with its current version, manifest, state and responses."""
    found: dict[str, dict] = {}
    if not root.is_dir():
        return found
    for bundle_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if not BUNDLE_ID.match(bundle_dir.name):
            continue
        current = current_version(bundle_dir)
        answers = responses(bundle_dir)
        state = answers[-1].get("state", "unreadable") if answers else "submitted"
        manifest = read_manifest(current[1]) if current else None
        recorded = next(
            (a.get("date", "") for a in answers if a.get("state") in OWNING), None
        )
        found[bundle_dir.name] = {
            "dir": bundle_dir,
            "version": current[0] if current else None,
            "manifest": manifest or {},
            "state": state if current else "in progress",
            "responses": answers,
            "recorded": recorded,
        }
    return found


def _named_by(info: dict) -> set[str]:
    """Return the bundle IDs and the `proposal-<slug>@` prefixes that a bundle names."""
    manifest = info["manifest"]
    names = {manifest.get("base")} | set(manifest.get("depends_on") or []) | set(
        manifest.get("related") or []
    )
    if manifest.get("contributes_to"):
        names.add(f"proposal-{manifest['contributes_to']}@")
    return {n for n in names if n}


def _names(name: str, bundle: str) -> bool:
    return bundle == name or (name.endswith("@") and bundle.startswith(name))


def owners(found: dict[str, dict]) -> dict[str, str]:
    """Return the owner contributor of each section.

    The owner is the contributor of the first proposal bundle on that section that reached
    `recorded`. A contribution never owns a section.
    """
    candidates = sorted(
        (info["recorded"], bid)
        for bid, info in found.items()
        if info["manifest"].get("kind") == "proposal"
        and not info["manifest"].get("contributes_to")
        and info["recorded"] is not None
        and info["state"] in OWNING
    )
    result: dict[str, str] = {}
    for _, bid in candidates:
        for section in found[bid]["manifest"].get("sections") or []:
            result.setdefault(section, found[bid]["manifest"]["contributor"])
    return result


# --------------------------------------------------------------------------------------------
# pack
# --------------------------------------------------------------------------------------------


def _text_form(data: bytes, rel: str) -> bytes:
    """Return the text as UTF-8 with no BOM and LF line ends. Raise on a file that is not UTF-8."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BundleError(f"{rel}: a text file must be UTF-8") from exc
    return text.removeprefix("﻿").replace("\r\n", "\n").encode("utf-8")


def pack(
    source: Path, fields: dict, root: Path = DEFAULT_ROOT, cwd: Path | None = None, today: str | None = None
) -> Path:
    """Write a new version of a bundle and return its folder. The manifest is written last."""
    problems = manifest_problems(fields, computed=False)
    if problems:
        raise BundleError("bad fields file:\n  " + "\n  ".join(problems))
    if not source.is_dir():
        raise BundleError(f"{source} is not a folder")
    payload: dict[str, bytes] = {}
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = path.relative_to(source).as_posix()
        if rel == "manifest.yaml":
            raise BundleError("the payload must not hold manifest.yaml: pack writes it")
        data = path.read_bytes()
        payload[rel] = _text_form(data, rel) if is_text(rel) else data
    terms = check_private_data.private_terms(REPO_ROOT) + check_private_data.private_terms(
        cwd or Path.cwd()
    )
    findings = [
        str(f)
        for rel, data in payload.items()
        if is_text(rel)
        for f in check_private_data.scan_text(rel, data.decode("utf-8"), terms)
    ]
    if findings:
        raise BundleError("private data in the payload:\n  " + "\n  ".join(findings))
    external = []
    for item in fields["external"]:
        target = (root.parent / item["path"]).resolve()
        if not target.is_file():
            raise BundleError(f"external file not found: {item['path']}")
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        external.append({**item, "sha256": digest.hexdigest()})
    bundle_dir = root / bundle_id(fields)
    existing = _numbered(bundle_dir, "v")
    version = existing[-1][0] + 1 if existing else 1
    version_dir = bundle_dir / f"v{version}"
    version_dir.mkdir(parents=True)
    files = []
    for rel, data in payload.items():
        target = version_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files.append({"path": rel, "sha256": sha256(data), "bytes": len(data)})
    manifest = {
        "bundle_format": BUNDLE_FORMAT,
        **{k: v for k, v in fields.items() if k != "bundle_format"},
        "version": version,
        "created": today or datetime.date.today().isoformat(),
        "files": files,
        "external": external,
    }
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (version_dir / "manifest.yaml").write_bytes(text.encode("utf-8"))
    return version_dir


# --------------------------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------------------------


def list_lines(root: Path = DEFAULT_ROOT) -> list[str]:
    """Return the text that `list` prints."""
    found = bundles(root)
    lines = []
    for bid, info in found.items():
        needed_by = sorted(
            other
            for other, o in found.items()
            if other != bid and any(_names(n, bid) for n in _named_by(o))
        )
        open_needers = [n for n in needed_by if found[n]["state"] not in FINISHED]
        version = f"v{info['version']}" if info["version"] else "-"
        line = f"{bid} {version} {info['state']}"
        if info["state"] in FINISHED and not open_needers:
            line += " (can delete)"
        lines.append(line)
        if needed_by:
            lines.append(f"  needed by: {', '.join(needed_by)}")
        last = info["responses"][-1] if info["responses"] else {}
        lines.extend(
            f"  {f}" for f in last.get("findings") or [] if str(f).startswith("deferred:")
        )
    owned = owners(found)
    if owned:
        lines.append("section owners:")
        lines.extend(f"  {section}: {owner}" for section, owner in sorted(owned.items()))
    return lines


# --------------------------------------------------------------------------------------------
# verify (reads YAML: run it in the environment of this repository)
# --------------------------------------------------------------------------------------------


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess:
    git = shutil.which("git")
    if git is None:
        raise BundleError("git is not on the PATH")
    return subprocess.run(  # noqa: S603
        [git, "-C", str(repo), *arguments], capture_output=True, text=True, check=False
    )


def changed_sections(spec_commit: str, repo: Path = REPO_ROOT) -> list[str] | None:
    """Return the IDs of the sections that changed since `spec_commit`, or None when git has no such commit."""
    if _git(repo, "cat-file", "-e", f"{spec_commit}^{{commit}}").returncode != 0:
        return None
    result = _git(repo, "diff", "--name-only", spec_commit, "HEAD", "--", f"{SPEC}/")
    ids = set()
    for rel in result.stdout.splitlines():
        parts = rel.split("/")
        if len(parts) != 4 or parts[2] not in SECTION_FOLDERS or not rel.endswith(".md"):
            continue
        path = repo / rel
        if not path.is_file():
            ids.add(rel)
            continue
        match = re.search(r"^id:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
        ids.add(match.group(1) if match else rel)
    return sorted(ids)


def _cases(data: object) -> dict[str, object]:
    cases = data.get("cases") if isinstance(data, dict) else None
    return {c["id"]: c for c in cases or [] if isinstance(c, dict) and "id" in c}


def _payload_problems(version_dir: Path, rel: str, yaml) -> list[str]:  # noqa: ANN001
    data = yaml.safe_load((version_dir / rel).read_text(encoding="utf-8"))
    problems = []
    if rel == "vector-runs.yaml":
        if not isinstance(data, dict) or set(data) != {"exporter", "commit", "runs"}:
            return ["vector-runs.yaml must have exactly the keys exporter, commit, runs"]
        if not SHA40.match(str(data["commit"])):
            problems.append("vector-runs.yaml commit must be 40 hex digits")
        for number, run in enumerate(data["runs"] or [], 1):
            keys = {"section", "function", "vectors_sha256", "cases", "result"}
            if not isinstance(run, dict) or set(run) != keys:
                problems.append(f"vector-runs.yaml runs[{number}] must have exactly the keys {sorted(keys)}")
                continue
            if run["result"] not in ("pass", "fail", "no vectors"):
                problems.append(f"vector-runs.yaml runs[{number}].result must be pass, fail or no vectors")
            if run["result"] != "no vectors" and not SHA64.match(str(run["vectors_sha256"])):
                problems.append(f"vector-runs.yaml runs[{number}].vectors_sha256 must be 64 hex digits")
            if any(v not in ("pass", "fail") for v in (run["cases"] or {}).values()):
                problems.append(f"vector-runs.yaml runs[{number}].cases values must be pass or fail")
    elif rel == "example/provenance.yaml":
        if not isinstance(data, dict) or not set(data) <= {"examples", "fragments"}:
            return ["example/provenance.yaml must have only the keys examples and fragments"]
        for path, entry in (data.get("examples") or {}).items():
            if not isinstance(entry, dict) or not PROVENANCE_KEYS <= set(entry) <= PROVENANCE_KEYS | {"notes"}:
                problems.append(f"example/provenance.yaml examples[{path}] must have the keys {sorted(PROVENANCE_KEYS)} and may have notes")
            elif entry["kind"] not in ("export", "forecast"):
                problems.append(f"example/provenance.yaml examples[{path}].kind must be export or forecast")
        for path, entry in (data.get("fragments") or {}).items():
            if not isinstance(entry, dict) or set(entry) != FRAGMENT_KEYS:
                problems.append(f"example/provenance.yaml fragments[{path}] must have exactly the keys {sorted(FRAGMENT_KEYS)}")
    return problems


def _publish_problems(version_dir: Path, listed: dict, manifest: dict, yaml) -> list[str]:  # noqa: ANN001
    """Return the findings of the publish rule (verdict `converts`) and of a failed dynamic check."""
    findings: list[str] = []
    external = manifest["external"]

    def load(rel: str) -> dict:
        data = yaml.safe_load((version_dir / rel).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    if manifest["batch_conversion"] == "converts":
        for size, precision in sorted({(i["size"], i["precision"]) for i in external}, key=str):
            count = sum(i["published"] for i in external if (i["size"], i["precision"]) == (size, precision))
            if count != 1:
                findings.append(f"publish rule: {size} {precision} must have exactly one published file, not {count}")
        published = {i["batch"] for i in external if i["published"]}
        if len(published) > 1 or not published <= {SOURCE_BATCH, "dynamic"}:
            findings.append(
                f"publish rule: each published file must have the batch {SOURCE_BATCH}, or each one dynamic, "
                f"not {sorted(map(str, published))}"
            )
        source = published == {SOURCE_BATCH}
        examples = load("example/provenance.yaml").get("examples") if "example/provenance.yaml" in listed else None
        # shortcut: reads the top-level `batching` of the sidecar only, not a `base`; enough for the spec examples.
        for rel in (f"example/{path}" for path in examples or {}):
            if rel not in listed:
                continue
            fragment = (load(rel).get("batching") or {}).get("batch_conversion") or {}
            if (fragment.get("source_batch_size") == SOURCE_BATCH) != source:
                findings.append(
                    f"publish rule: {rel} must have batching.batch_conversion.source_batch_size: {SOURCE_BATCH} "
                    f"if and only if the published batch is {SOURCE_BATCH}"
                )
        if source:
            fragment = (
                (load("batch/conversion.yaml").get("batching") or {}).get("batch_conversion") or {}
                if "batch/conversion.yaml" in listed
                else {}
            )
            if fragment.get("source_batch_size") != SOURCE_BATCH:
                findings.append(f"publish rule: batch/conversion.yaml must have source_batch_size: {SOURCE_BATCH}")
    if "batch/report.json" in listed:
        report = json.loads((version_dir / "batch/report.json").read_text(encoding="utf-8"))
        dynamic = {(i["size"], i["precision"]) for i in external if i["published"] and i["batch"] == "dynamic"}
        findings += [
            f"{check['size']} {check['precision']}: do not publish the dynamic export; publish b3 or fix the export"
            for check in report.get("dynamic_check") or []
            if check.get("result") == "fail" and (check.get("size"), check.get("precision")) in dynamic
        ]
    return findings


def verify(name: str, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT) -> list[str]:
    """Return the findings for the current version of one bundle. An empty list means it passes."""
    import yaml  # only verify needs it

    import check_links

    found = bundles(root)
    info = found.get(name)
    if info is None:
        return [f"no bundle {name} in {root}"]
    if info["version"] is None:
        return [f"{name} has no complete version (no manifest.yaml)"]
    version_dir = info["dir"] / f"v{info['version']}"
    manifest = info["manifest"]
    findings = [f"manifest: {p}" for p in manifest_problems(manifest)]
    if findings:
        return findings
    match = BUNDLE_ID.match(name)
    if (match["kind"], match["name"], match["contributor"]) != (
        manifest["kind"], manifest["name"], manifest["contributor"]
    ):
        findings.append("the manifest kind, name or contributor does not match the bundle ID")
    if manifest["version"] != info["version"]:
        findings.append(f"manifest version {manifest['version']} is not the folder v{info['version']}")

    # Hashes, layout and text form.
    listed = {f["path"]: f for f in manifest["files"]}
    on_disk = {p.relative_to(version_dir).as_posix() for p in version_dir.rglob("*") if p.is_file()}
    on_disk.discard("manifest.yaml")
    findings += [f"{rel}: the file is not in the manifest" for rel in sorted(on_disk - set(listed))]
    for rel, item in sorted(listed.items()):
        path = version_dir / rel
        if not path.is_file():
            findings.append(f"{rel}: the file is missing")
            continue
        data = path.read_bytes()
        if sha256(data) != item["sha256"] or len(data) != item["bytes"]:
            findings.append(f"{rel}: the hash or the size does not match the manifest")
        if is_text(rel):
            if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
                findings.append(f"{rel}: a text file must be UTF-8 with no BOM and LF line ends")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                findings.append(f"{rel}: a text file must be UTF-8")
    contribution = manifest["kind"] == "proposal" and manifest["contributes_to"]
    required = {
        "model": ["intake.md"],
        "proposal": ["evidence.md"] if contribution else ["proposal.md"],
    }[manifest["kind"]]
    what = "contribution" if contribution else manifest["kind"]
    findings += [f"{rel}: a {what} bundle needs this file" for rel in required if rel not in listed]
    vectors = sorted(r for r in listed if r.startswith("vectors/") and r.endswith(".yaml"))
    if contribution and not vectors:
        findings.append("a contribution needs at least one vectors/<section ID>.yaml")
    for rel in vectors:
        section = rel.removeprefix("vectors/").removesuffix(".yaml")
        if section not in manifest["sections"]:
            findings.append(f"{rel}: the section {section} is not in the manifest sections")
        if listed[rel]["bytes"] > VECTOR_LIMIT:
            findings.append(f"{rel}: a vector file must be 256 KiB or smaller")

    # Text checks: private data, plans/ paths, links.
    terms = check_private_data.private_terms(repo)
    record = (
        f"{SPEC}/proposals/{manifest['contributes_to']}/contributions/{manifest['contributor']}"
        if contribution
        else f"{SPEC}/proposals/{manifest['name']}"
    )
    for rel in sorted(r for r in listed if is_text(r) and (version_dir / r).is_file()):
        text = (version_dir / rel).read_text(encoding="utf-8", errors="replace")
        findings.extend(f"private data: {f}" for f in check_private_data.scan_text(rel, text, terms))
        for number, line in enumerate(text.splitlines(), 1):
            if "plans/" in line:
                findings.append(f"{rel}:{number}: cites a plans/ path")
        if manifest["kind"] != "proposal" or not rel.endswith(".md"):
            continue
        for number, target in check_links.links(version_dir / rel):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
                continue
            file_part = target.partition("#")[0]
            in_record = (Path(record) / rel).parent / file_part
            parts: list[str] = []
            for part in in_record.as_posix().split("/"):
                if part == "..":
                    if parts:
                        parts.pop()
                elif part not in ("", "."):
                    parts.append(part)
            resolved = "/".join(parts)
            inside = resolved.removeprefix(record + "/") if resolved.startswith(record + "/") else None
            if not ((inside is not None and inside in listed) or (repo / resolved).exists()):
                findings.append(f"{rel}:{number}: the link {target} does not resolve from {record}/")

    # Payload schemas.
    for rel in ("vector-runs.yaml", "example/provenance.yaml"):
        if rel in listed and manifest["kind"] == "model":
            findings.extend(_payload_problems(version_dir, rel, yaml))

    # Links between bundles, ownership and contribution cases.
    others = list(manifest["related"])
    if manifest["kind"] == "proposal":
        others += [manifest["base"], *manifest["depends_on"]]
    findings += [f"the bundle {o} does not exist" for o in others if o and o not in found]
    if manifest["kind"] == "proposal":
        owned = owners(found)
        if not contribution and not manifest["base"] and info["state"] not in OWNING:
            for section in manifest["sections"]:
                owner = owned.get(section)
                if owner and owner != manifest["contributor"]:
                    findings.append(
                        f"the section {section} has the owner {owner}: send a contribution or a follow-up"
                    )
        if contribution:
            owner_ids = [
                b for b, o in found.items()
                if o["manifest"].get("kind") == "proposal"
                and o["manifest"].get("name") == manifest["contributes_to"]
                and not o["manifest"].get("contributes_to")
            ]
            if not owner_ids:
                findings.append(f"no proposal bundle with the slug {manifest['contributes_to']}")
            for rel in vectors:
                mine = _cases(yaml.safe_load((version_dir / rel).read_text(encoding="utf-8")))
                theirs: dict[str, object] = {}
                landed = repo / SPEC / rel
                if landed.is_file():
                    theirs.update(_cases(yaml.safe_load(landed.read_text(encoding="utf-8"))))
                for owner_id in owner_ids:
                    owner_file = found[owner_id]["dir"] / f"v{found[owner_id]['version']}" / rel
                    if owner_file.is_file():
                        theirs.update(_cases(yaml.safe_load(owner_file.read_text(encoding="utf-8"))))
                findings += [
                    f"{rel}: the case {case_id} differs from the owner case with the same id"
                    for case_id in sorted(set(mine) & set(theirs))
                    if mine[case_id] != theirs[case_id]
                ]

    # External files.
    for item in manifest["external"]:
        target = (root.parent / item["path"]).resolve()
        if not target.is_file():
            findings.append(f"external file not found: {item['path']}")
        elif sha256(target.read_bytes()) != item["sha256"]:
            findings.append(f"external file does not match its sha256: {item['path']}")

    # Batch conversion: the publish rule and the dynamic check.
    if manifest["kind"] == "model":
        findings += _publish_problems(version_dir, listed, manifest, yaml)

    # Responses.
    for _, path in _numbered(info["dir"] / "responses", "r", ".yaml"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            findings.append(f"responses/{path.name}: not JSON")
            continue
        findings.extend(f"responses/{path.name}: {p}" for p in response_problems(data))

    # Spec drift.
    changed = changed_sections(manifest["spec_commit"], repo)
    if changed is None:
        findings.append("spec_commit not found in this checkout; pack again on the current checkout")
    else:
        findings += [
            f"the section {section} changed since spec_commit; rebase on the current text"
            for section in manifest["sections"]
            if section in changed
        ]
    return findings


# --------------------------------------------------------------------------------------------
# batch (imports onnx, onnxruntime and skellytracker: run it in the .venv of this checkout)
# --------------------------------------------------------------------------------------------


def _facts(model) -> dict:  # noqa: ANN001
    """Return the graph facts that the V1 report compares."""
    graph = model.graph

    def dims(items) -> dict:  # noqa: ANN001
        return {v.name: [d.dim_param or d.dim_value for d in v.type.tensor_type.shape.dim] for v in items}

    counts: dict[str, int] = {}
    for node in graph.node:
        counts[node.op_type] = counts.get(node.op_type, 0) + 1
    return {
        "ir_version": model.ir_version,
        "opset_import": {o.domain or "ai.onnx": o.version for o in model.opset_import},
        "producer": f"{model.producer_name} {model.producer_version}".strip(),
        "inputs": dims(graph.input),
        "outputs": dims(graph.output),
        "value_info": dims(graph.value_info),
        "initializers": {t.name: sha256(t.SerializeToString()) for t in graph.initializer},
        "metadata": {p.key: p.value for p in model.metadata_props},
        "node_counts": counts,
    }


def graph_diff(path_a: Path, path_b: Path) -> dict:
    """Return each fact of the V1 report that differs, as {fact: [a, b]} or {fact: {name: [a, b]}}."""
    import onnx

    a, b = (_facts(onnx.load(str(p), load_external_data=False)) for p in (path_a, path_b))
    diff: dict = {}
    for key in a:
        if isinstance(a[key], dict):
            names = sorted(set(a[key]) | set(b[key]))
            changed = {n: [a[key].get(n), b[key].get(n)] for n in names if a[key].get(n) != b[key].get(n)}
            if changed:
                diff[key] = changed
        elif a[key] != b[key]:
            diff[key] = [a[key], b[key]]
    return diff


def _diff_counts(diff: dict) -> dict:
    return {key: len(value) if isinstance(value, dict) else 1 for key, value in diff.items()}


def _load_problem(path: Path) -> str | None:
    """V0b: return why the onnx and onnxruntime of this environment cannot load the file, or None."""
    import onnx
    import onnxruntime

    model = onnx.load(str(path), load_external_data=False)
    if model.ir_version > onnx.IR_VERSION:
        return f"ir_version {model.ir_version} is above {onnx.IR_VERSION} of onnx {onnx.__version__}"
    schemas = onnx.defs.get_all_schemas_with_history()
    for opset in model.opset_import:
        if opset.domain in ("", "ai.onnx"):
            top = onnx.defs.onnx_opset_version()
        else:
            top = max((s.since_version for s in schemas if s.domain == opset.domain), default=None)
        if top is not None and opset.version > top:
            return f"opset {opset.domain or 'ai.onnx'} {opset.version} is above {top} of onnx {onnx.__version__}"
    try:
        onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception as exc:  # noqa: BLE001  # any refusal of the runtime is the reason
        return f"onnxruntime {onnxruntime.__version__}: {exc}"
    return None


class _Runner:
    """Run ONNX files on the CPU, with the inputs of V5 and V6."""

    DTYPES = {"tensor(float)": "float32", "tensor(float16)": "float16", "tensor(uint8)": "uint8"}

    def __init__(self) -> None:
        import numpy
        import onnxruntime

        self.np, self.ort, self.sessions = numpy, onnxruntime, {}

    def session(self, path: Path):  # noqa: ANN201
        if path not in self.sessions:
            self.sessions[path] = self.ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        return self.sessions[path]

    def _shape(self, item, batch: int) -> list[int]:  # noqa: ANN001
        shape = [batch, *item.shape[1:]]
        if not all(isinstance(d, int) for d in shape):
            raise BundleError(f"input {item.name} has a dynamic dim other than dim 0: {item.shape}")
        return shape

    def _dtype(self, item) -> str:  # noqa: ANN001
        if item.type not in self.DTYPES:
            raise BundleError(f"input {item.name} has the type {item.type}: batch takes float, float16 or uint8")
        return self.DTYPES[item.type]

    def input_a(self, path: Path, batch: int) -> dict:
        """Input A: seed 42; float inputs uniform in [0, 1), uint8 inputs integers in [0, 256)."""
        rng = self.np.random.default_rng(42)
        feeds = {}
        for item in self.session(path).get_inputs():
            shape, dtype = self._shape(item, batch), self._dtype(item)
            if dtype == "uint8":
                feeds[item.name] = rng.integers(0, 256, shape, dtype=self.np.uint8)
            else:
                feeds[item.name] = rng.random(shape).astype(dtype)
        return feeds

    def input_b(self, path: Path, items, batch: int) -> dict:  # noqa: ANN001
        """Input B: the first `batch` items feed the first input. Other inputs take input A."""
        feeds = self.input_a(path, batch)
        first = self.session(path).get_inputs()[0]
        dtype = self._dtype(first)
        data = items[:batch]
        if dtype == "float16" and data.dtype == self.np.float32:
            data = data.astype(self.np.float16)
        if data.dtype != self.np.dtype(dtype) or list(data.shape) != self._shape(first, batch):
            raise BundleError(f"input B {data.dtype} {list(data.shape)} does not fit the input {first.name}")
        feeds[first.name] = data
        return feeds

    def run(self, path: Path, feeds: dict) -> dict:
        session = self.session(path)
        names = [o.name for o in session.get_outputs()]
        return dict(zip(names, session.run(names, feeds), strict=True))

    def compare(self, got: dict, want: dict, tolerance: float) -> dict:
        """Compare two runs with the V5 rules. A run with only empty outputs is `empty`."""
        np = self.np
        result: dict = {"pass": list(got) == list(want), "outputs": {}}
        if not result["pass"]:
            result["error"] = f"output names {list(got)} and {list(want)} differ"
            return result
        for name, x in got.items():
            y = want[name]
            entry: dict = {"shape": list(x.shape), "rows": int(x.shape[0]) if x.ndim else None}
            if x.dtype != y.dtype or x.shape != y.shape:
                entry["error"] = f"{x.dtype} {list(x.shape)} against {y.dtype} {list(y.shape)}"
                result["pass"] = False
            elif x.size:
                a, b = x.astype(np.float64), y.astype(np.float64)
                gap = np.abs(a - b)
                entry["max_abs"] = float(np.nanmax(gap, initial=0.0))
                entry["max_rel"] = float(np.nanmax(gap / np.maximum(np.abs(b), np.finfo(np.float64).tiny), initial=0.0))
                if not np.allclose(a, b, rtol=tolerance, atol=tolerance, equal_nan=True):
                    result["pass"] = False
            result["outputs"][name] = entry
        result["empty"] = all(x.size == 0 for x in got.values()) and all(y.size == 0 for y in want.values())
        return result


def _input_items(inputs: Path, size: object, cache: dict):  # noqa: ANN202
    """Return the input B items of one size: `inputs/<size>.npy`, 4 different items."""
    if size not in cache:
        import numpy as np

        path = inputs / f"{size}.npy"
        if not path.is_file():
            raise BundleError(f"input B not found: {path.name} (write {INPUT_B_ITEMS} preprocessed images)")
        items = np.load(path, allow_pickle=False)
        if items.ndim < 1 or items.shape[0] != INPUT_B_ITEMS:
            raise BundleError(f"{path.name} must hold {INPUT_B_ITEMS} items, not shape {list(items.shape)}")
        if len(np.unique(items.reshape(INPUT_B_ITEMS, -1), axis=0)) != INPUT_B_ITEMS:
            raise BundleError(f"{path.name} holds one item more than once")
        cache[size] = items
    return cache[size]


def batch_check(
    fields: dict, out: Path, inputs: Path | None = None, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT
) -> dict:
    """Run the batch-conversion check (V0 to V6) and write its files to `out`. Return the report."""
    import tempfile

    import numpy
    import onnx
    import onnxruntime

    from skellytracker.core.sessions.batch_conversion import model_batch_convert

    inputs = inputs or out / "inputs"
    files: dict[tuple, Path] = {}
    names: dict[Path, str] = {}
    digests: dict[Path, str] = {}
    for item in fields.get("external") or []:
        key = (item["size"], item["precision"], item["batch"])
        if key in files:
            raise BundleError(f"two external files for size {key[0]}, precision {key[1]}, batch {key[2]}")
        if item["precision"] not in TOLERANCE:
            raise BundleError(f"precision {item['precision']} has no tolerance: use one of {list(TOLERANCE)}")
        path = (root.parent / item["path"]).resolve()
        if not path.is_file():
            raise BundleError(f"external file not found: {item['path']}")
        digests[path] = sha256(path.read_bytes())
        if item.get("sha256") not in (None, digests[path]):
            raise BundleError(f"external file does not match its sha256: {item['path']}")
        files[key], names[path] = path, item["path"]

    def clean(text: str) -> str:
        # Keep absolute paths out of the report: pack refuses them as private data.
        for path, name in names.items():
            text = text.replace(str(path), name)
        return text

    pairs = sorted({(s, p) for s, p, _ in files}, key=str)
    static = [k for k in files if k[2] != "dynamic"]
    sizes = {s for s, _, _ in files}
    per_size = {s: {b for s2, _, b in static if s2 == s} for s in sizes}

    # V0: applicability, for the whole family.
    missing = [
        [s, p, b] for s, p in pairs for b in VERIFICATION_BATCHES if (s, p, b) not in files
    ]
    if not static or all(len(b) <= 1 for b in per_size.values()):
        v0 = "not applicable"
    else:
        v0 = "missing-verification-batch" if missing else "pass"

    # V0b: can this environment load each file?
    v0b = {names[path]: problem for path in files.values() if (problem := _load_problem(path))}
    v0b = {name: clean(problem) for name, problem in v0b.items()}
    loadable = {path for path in files.values() if names[path] not in v0b}

    runner = _Runner()
    items: dict = {}
    reasons: list[str] = []
    empty: dict[tuple, list[bool]] = {pair: [] for pair in pairs}
    differences: dict = {}
    residuals: dict = {}
    tuples: list[dict] = []
    if v0 == "missing-verification-batch":
        reasons.append("missing-verification-batch")
    if v0b and v0 != "not applicable":
        reasons.append("host-runtime-cannot-load")

    with tempfile.TemporaryDirectory() as scratch:
        if v0 == "pass" and not v0b:
            for (size, precision), target in ((pair, n) for pair in pairs for n in TARGETS):
                source, native = files[(size, precision, SOURCE_BATCH)], files[(size, precision, target)]
                label = f"{size}/{precision}/b{SOURCE_BATCH}-to-b{target}"
                differences[label] = graph_diff(source, native)  # V1
                record: dict = {
                    "size": size, "precision": precision, "target": target,
                    "source": {"file": names[source], "sha256": digests[source]},
                    "native": {"file": names[native], "sha256": digests[native]},
                    "v1_counts": _diff_counts(differences[label]),
                }
                converted = Path(scratch) / f"{len(tuples)}.onnx"
                try:  # V3
                    summary = model_batch_convert(source, converted, target_batch=target, batch_conversion=PROFILE)
                    record["v3"] = {"result": "pass", "summary": dataclasses.asdict(summary)}
                except ValueError as exc:
                    record["v3"] = {"result": "fail", "error": clean(str(exc))}
                    residuals[label] = {}
                    tuples.append(record)
                    continue
                residual = graph_diff(converted, native)  # V4
                record["v4_counts"] = _diff_counts(residual)
                tolerance = TOLERANCE[precision]
                runs = {  # V5: input A and input B
                    "A": runner.input_a(native, target),
                    "B": runner.input_b(native, _input_items(inputs, size, items), target),
                }
                record["v5"] = {
                    k: runner.compare(runner.run(converted, f), runner.run(native, f), tolerance)
                    for k, f in runs.items()
                }
                empty[(size, precision)] += [r["empty"] for r in record["v5"].values()]
                record["v5"]["result"] = "pass" if all(r["pass"] for r in record["v5"].values()) else "fail"
                if record["v5"]["result"] == "fail":
                    residuals[label] = residual
                tuples.append(record)

    # V6: the dynamic check. It gates only the publication of the dynamic file.
    dynamic_check = []
    for size, precision in pairs:
        path = files.get((size, precision, "dynamic"))
        if path is None:
            continue
        check: dict = {"size": size, "precision": precision, "file": names[path], "static": {}, "self": {}}
        dynamic_check.append(check)
        tolerance = TOLERANCE[precision]
        has_static = any((size, precision, n) in files for n in VERIFICATION_BATCHES)
        need = [files.get((size, precision, n)) for n in DYNAMIC_BATCHES] if has_static else []
        if path not in loadable or any(n is not None and n not in loadable for n in need):
            check["result"], check["reason"] = "to run", "host-runtime-cannot-load"
            continue
        if None in need:
            check["result"], check["reason"] = "to run", "missing-verification-batch"
            continue
        passed = True
        for n, native in zip(DYNAMIC_BATCHES, need, strict=False):  # (a) against the static natives
            for k, feeds in (
                ("A", runner.input_a(native, n)),
                ("B", runner.input_b(native, _input_items(inputs, size, items), n)),
            ):
                result = runner.compare(runner.run(path, feeds), runner.run(native, feeds), tolerance)
                check["static"][f"b{n}/{k}"] = result
                empty[(size, precision)].append(result["empty"])
                passed &= result["pass"]
        three = max(DYNAMIC_BATCHES)
        for k, feeds in (  # (b) self-consistency on three different items
            ("A", runner.input_a(path, three)),
            ("B", runner.input_b(path, _input_items(inputs, size, items), three)),
        ):
            single = [runner.run(path, {i: v[r : r + 1] for i, v in feeds.items()}) for r in range(three)]
            for n in DYNAMIC_BATCHES[1:]:
                outputs = runner.run(path, {i: v[:n] for i, v in feeds.items()})
                for name, value in outputs.items():
                    if value.ndim == 0 or value.shape[0] != n or any(s[name].shape[:1] != (1,) for s in single):
                        check["self"][f"b{n}/{k}/{name}"] = "no check"
                        continue
                    rows = [
                        runner.compare({name: value[r : r + 1]}, {name: single[r][name]}, tolerance)
                        for r in range(n)
                    ]
                    check["self"][f"b{n}/{k}/{name}"] = "pass" if all(r["pass"] for r in rows) else "fail"
                    empty[(size, precision)] += [r["empty"] for r in rows]
                    passed &= all(r["pass"] for r in rows)
        check["result"] = "pass" if passed else "fail"

    if v0 != "not applicable" and not reasons:
        reasons += ["no-signal" for pair, flags in empty.items() if flags and all(flags)][:1]
    if v0 == "not applicable":
        verdict, reason = "not applicable", None
    elif reasons:
        verdict, reason = "to run", reasons[0]
    elif any(t["v3"]["result"] == "fail" or t["v5"]["result"] == "fail" for t in tuples):
        verdict, reason = "does not convert", None
    else:
        verdict, reason = "converts", None

    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    report = {
        "tool": "tools/intake_bundle.py batch",
        "skellytracker_commit": commit,
        "versions": {
            "python": sys.version.split()[0],
            "numpy": numpy.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": onnxruntime.__version__,
        },
        "profile_id": PROFILE["profile_id"],
        "S": SOURCE_BATCH,
        "v0": {"result": v0, "missing": missing if v0 != "not applicable" else []},
        "v0b": v0b,
        "tuples": tuples,
        "dynamic_check": dynamic_check,
        "batch_conversion": verdict,
        "batch_conversion_reason": reason,
    }
    out.mkdir(parents=True, exist_ok=True)
    for name in ("conversion.yaml", "residual-diff.json"):
        (out / name).unlink(missing_ok=True)

    def write(name: str, data: object) -> None:
        text = json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"
        (out / name).write_bytes(text.encode("utf-8"))

    write("report.json", report)
    write("differences.json", differences)
    if verdict == "converts":
        write("conversion.yaml", {"batching": {"batch_conversion": PROFILE}})
    elif verdict == "does not convert":
        write("residual-diff.json", residuals)
    return report


def checkout_environment_problem(repo: Path = REPO_ROOT) -> str | None:
    """Return why `batch` must not run in this interpreter, or None.

    uv only warns about a wrong `--project` path and then runs in another environment.
    """
    if Path(sys.prefix).resolve() != (repo / ".venv").resolve():
        return f"batch runs only in the .venv of the checkout that holds this script ({repo.name}/.venv)"
    return None


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    # Each sub-command takes --root after its name, as the usage of the module docstring shows.
    root = argparse.ArgumentParser(add_help=False)
    root.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="the intakes folder")
    commands = parser.add_subparsers(dest="command", required=True)
    pack_parser = commands.add_parser("pack", parents=[root], help="write a new version of a bundle")
    pack_parser.add_argument("--from", dest="source", type=Path, required=True)
    pack_parser.add_argument("--fields", type=Path, required=True)
    commands.add_parser("list", parents=[root], help="list the bundles, their states and the section owners")
    verify_parser = commands.add_parser("verify", parents=[root], help="check the current version of a bundle")
    verify_parser.add_argument("bundle")
    batch_parser = commands.add_parser("batch", parents=[root], help="run the batch-conversion check")
    batch_parser.add_argument("--fields", type=Path, required=True, help="a fields file or a manifest")
    batch_parser.add_argument("--out", type=Path, required=True, help="the batch/ folder to write")
    batch_parser.add_argument("--inputs", type=Path, help="the folder of input B (default: OUT/inputs)")
    args = parser.parse_args(argv)
    try:
        if args.command == "batch":
            problem = checkout_environment_problem()
            if problem:
                raise BundleError(problem)
            fields = json.loads(args.fields.read_text(encoding="utf-8"))
            report = batch_check(fields, args.out, args.inputs, args.root)
            print(f"batch_conversion: {report['batch_conversion']}")
            print(f"batch_conversion_reason: {report['batch_conversion_reason']}")
            for check in report["dynamic_check"]:
                print(f"dynamic check {check['size']} {check['precision']}: {check['result']}")
        elif args.command == "pack":
            fields = json.loads(args.fields.read_text(encoding="utf-8"))
            version_dir = pack(args.source, fields, args.root)
            print(f"packed {version_dir.parent.name} {version_dir.name}")
        elif args.command == "list":
            print("\n".join(list_lines(args.root)) or "no bundles")
        else:
            findings = verify(args.bundle, args.root)
            print("findings:")
            for finding in findings:
                print(f"  - {json.dumps(finding, ensure_ascii=False)}")
            return 1 if findings else 0
    except BundleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
