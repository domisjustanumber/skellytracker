#!/usr/bin/env python3
"""Pack, list and verify the hand-over bundles in `intakes/`.

The rules are in `specs/model-sidecar/model-addition-workflow/hand-over.md` and
`specs/model-sidecar/model-addition-workflow/batch-conversion-check.md`.

Usage::

    python -B tools/intake_bundle.py pack --from DIR --fields FILE.json [--root INTAKES]
    uv run python -B tools/intake_bundle.py pack --dry-run --from DIR --fields FILE.json [--root INTAKES]
    python -B tools/intake_bundle.py list [--root INTAKES]
    uv run python -B tools/intake_bundle.py verify BUNDLE [--root INTAKES]
    python -B tools/intake_bundle.py record BUNDLE [--root INTAKES]
    uv run python -B tools/intake_bundle.py batch --fields FILE --out DIR [--inputs DIR] [--root INTAKES]

`pack` and `list` use only the standard library, so Python 3.9 or later runs them. `verify`
reads YAML and the producers of this checkout, so it runs in the environment of this repository.
It reads each Python file of a bundle as text and never runs it (ADR-AD33). `pack --dry-run` packs
in a temporary folder, takes the external files from the real `--root`, runs `verify` on the result
and writes nothing, so it runs where `verify` runs. `record` copies the bytes of the current version
of a proposal bundle to its tracked record and checks each hash. It never imports or runs a file of
the bundle. `batch` is the
batch-conversion check. It imports onnx, onnxruntime and the skellytracker converter, so it runs
only in the `.venv` of this checkout. `--fields` is a fields file or a manifest. No sub-command
writes a response file: the skellytracker session writes them.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote

import check_private_data

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "intakes"
SPEC = "specs/model-sidecar"
SECTION_FOLDERS = ("format", "common", "pre", "post")

BUNDLE_FORMAT = 1
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".json", ".txt", ".csv", ".toml"}
# shortcut: a suffix test only; an ONNX external-data file with another name passes; add a magic check if one appears.
FORBIDDEN_SUFFIXES = (".onnx", ".onnx.data", ".ort")
# Compiled Python cannot be reviewed as text (ADR-1GG7).
COMPILED_SUFFIXES = (".pyc", ".pyo")
VECTOR_LIMIT = 256 * 1024


def link_findings(folder: Path, rels: object, manifest: dict, repo: Path = REPO_ROOT) -> list[str]:
    """Return one text for each relative link of a proposal `.md` file that fails from its record path.

    The link test checks each record as `tools/tests/test_links.py` does: the file of a link is a
    file of the bundle or of `repo`, and its `#anchor` is a heading of that Markdown file. A record
    is a byte copy, so `pack` refuses such a link and `verify` gives a finding (ADR-730P).
    """
    import check_links  # standard library only, so `pack` still runs on Python 3.9

    if manifest.get("kind") != "proposal":
        return []
    contribution = manifest.get("contributes_to")
    record = (
        f"{SPEC}/proposals/{contribution}/contributions/{manifest.get('contributor')}"
        if contribution
        else f"{SPEC}/proposals/{manifest.get('name')}"
    )
    listed = set(rels)
    found: list[str] = []
    for rel in sorted(r for r in listed if r.endswith(".md") and (folder / r).is_file()):
        for number, target in check_links.links(folder / rel):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            file_part, _, anchor = target.partition("#")
            parts: list[str] = []
            for part in ((Path(record) / rel).parent / unquote(file_part)).as_posix().split("/"):
                if part == "..":
                    if parts:
                        parts.pop()
                elif part not in ("", "."):
                    parts.append(part)
            resolved = "/".join(parts) if file_part else f"{record}/{rel}"
            inside = resolved.removeprefix(record + "/") if resolved.startswith(record + "/") else None
            dest = folder / inside if inside in listed else repo / resolved
            if not dest.exists():
                found.append(f"{rel}:{number}: the link {target} does not resolve from {record}/")
            elif anchor and dest.suffix.lower() == ".md" and unquote(anchor) not in check_links.anchors(dest):
                found.append(f"{rel}:{number}: the link {target} names a heading that does not exist")
    return found


def refused_file(rel: str) -> str | None:
    """Return why `pack` and `verify` refuse the payload file `rel`, or None (ADR-AD33; ADR-1GG7)."""
    lower = rel.lower()
    if lower.endswith(FORBIDDEN_SUFFIXES):
        return f"{rel}: do not copy ONNX files into a bundle; name them in external"
    if lower.endswith(COMPILED_SUFFIXES) or "__pycache__" in lower.split("/"):
        return f"{rel}: do not put compiled files in a bundle; run Python with -B"
    return None

KINDS = ("model", "proposal")
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
# A bundle with no entry: the latest response gives the state and the owner role.
OWNING = {"recorded", "accepted", "landed"}
NOT_OWNING = {"rejected", "resolved-otherwise", "closed"}
UNREADABLE = {"_unreadable": True}
# The status of the spec-log entry of a proposal record is the authority for its state (ADR-ZXD7, item 3).
# Each status allows these response states; the first one is the state when the latest response disagrees.
ALLOWED_RESPONSES = {
    "proposed": ("recorded", "accepted", "needs-contributor"),
    "rejected": ("rejected", "resolved-otherwise"),
    "accepted": ("landed",),
    "absorbed into": ("landed",),
    "superseded by": ("landed",),
}
OWNING_ENTRY = {"proposed", "accepted", "absorbed into"}

COMMON_KEYS = (
    "bundle_format",
    "kind",
    "name",
    "contributor",
    "version",
    "source_commit",
    "spec_commit",
    "spec_version",
    "created",
    "sections",
    "related",
    "files",
    "external",
)
KIND_KEYS = {
    "model": ("verdict", "batch_conversion", "batch_conversion_reason", "batch_forced", "batch_forced_reason",
              "no_static_reason"),
    "proposal": ("base", "depends_on", "contributes_to"),
}
COMPUTED = ("files", "version", "created", "spec_version")
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
# The provenance key sets. The header of specs/model-sidecar/inventory.yaml gives their meaning;
# tools/tests/test_examples.py checks the inventory with them.
COPY_KEYS = {"exporter", "exporter_path", "kind", "exporter_layout_path", "tracked", "commit"}
# An example entry of example/provenance.yaml; notes optional. It has no source: the session takes
# source from the example sidecar (ADR-ZXD7, item 6).
PROVENANCE_KEYS = COPY_KEYS
# An example entry of inventory.yaml. Each entry has bundle (ADR-ZXD7, item 6; ADR-C0YD).
INVENTORY_KEYS = COPY_KEYS | {"edits", "notes", "bundle"}
FRAGMENT_KEYS = {"exporter", "exporter_path", "tracked", "commit", "notes"}

SOURCE_BATCH = 3
PROFILE = {"profile_id": "static-batch-v1"}  # the whole batching.batch_conversion of a b3 sidecar (ADR-JAA4)
VERIFICATION_BATCHES = (1, 2, 3, 6)
FORMS = (SOURCE_BATCH, 1, "dynamic")  # the values of batching.batch (ADR-JAA4)
TARGETS = (1, 2, 6)
DYNAMIC_BATCHES = (1, 2, 3)
TOLERANCE = {"fp32": 1e-5, "fp16": 1e-3}
INPUT_B_ITEMS = 6

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_HEADING = re.compile(r"^### (\d+\.\d+\.\d+)[ \t]*$", re.MULTILINE)
ENTRY_FILE = re.compile(r"^[0-9A-Za-z]{4}-(?P<slug>.+)\.md$")
ENTRY_STATUS = re.compile(r"^\*\*Status:\*\*\s*(proposed|accepted|absorbed into|superseded by|rejected)\b", re.MULTILINE)
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
    if not isinstance(manifest, dict):
        return ["the manifest is not a mapping"]
    problems: list[str] = []
    kind = manifest.get("kind")
    if kind not in KINDS:
        return [f"kind must be one of {list(KINDS)}, not {kind!r}"]
    allowed = set(COMMON_KEYS) | set(KIND_KEYS[kind])
    required = allowed if computed else allowed - set(COMPUTED)
    # A manifest with no spec_version is from before ADR-ZXD7: pack writes each computed key.
    problems += [
        f"missing key {key}" + ("; pack a new version" if key in COMPUTED else "")
        for key in sorted(required - set(manifest))
    ]
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
    if computed and "spec_version" in manifest and not SEMVER.match(str(get("spec_version"))):
        problems.append("spec_version must be MAJOR.MINOR.PATCH, a version heading of the changelog")
    if computed and not (isinstance(get("version"), int) and get("version", 0) >= 1):
        problems.append("version must be an integer of 1 or more")
    if "sections" in manifest and not (_is_str_list(get("sections")) and get("sections")):
        problems.append("sections must be a list of one or more section IDs")
    if "related" in manifest and not _is_str_list(get("related")):
        problems.append("related must be a list of bundle IDs")
    if kind == "proposal":
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
        forced, why = get("batch_forced"), get("batch_forced_reason")
        if "batch_forced" in manifest and (forced not in (None, 1, "dynamic") or isinstance(forced, bool)):
            problems.append("batch_forced must be null, 1 or 'dynamic'")
        if forced is None and why is not None:
            problems.append("batch_forced_reason must be null unless batch_forced is set")
        if forced is not None and not (isinstance(why, str) and why.strip()):
            problems.append("batch_forced_reason must give the reason for batch_forced")
        items = get("external")
        dynamic_only = isinstance(items, list) and bool(items) and all(
            isinstance(i, dict) and i.get("batch") == "dynamic" for i in items
        )
        # A dynamic-only family states why it has no static graph, or forces dynamic (ADR-JB5J, item 2).
        no_static = get("no_static_reason")
        if no_static is not None and not (isinstance(no_static, str) and no_static.strip()):
            problems.append("no_static_reason must be null or give the reason")
        if no_static is not None and not (dynamic_only and forced is None):
            problems.append("no_static_reason must be null unless each external file is dynamic and batch_forced is null")
        if "no_static_reason" in manifest and dynamic_only and forced is None and no_static is None:
            problems.append(
                "only dynamic external files need no_static_reason (why the model cannot export a static graph), "
                "or batch_forced: dynamic with batch_forced_reason"
            )
        if (
            "batch_forced" in manifest and forced is None and get("batch_conversion") == "not applicable"
            and not dynamic_only
        ):
            problems.append(
                "batch_conversion 'not applicable' needs batch_forced, or only dynamic external files "
                "with no_static_reason: the batch check runs by default"
            )
        if (forced is not None or (dynamic_only and no_static)) and reason == "missing-verification-batch":
            problems.append(
                "batch_conversion_reason 'missing-verification-batch' is not possible with batch_forced, "
                "or with only dynamic external files and no_static_reason: V0 then gives 'not applicable'"
            )
    external = get("external", [])
    if not isinstance(external, list):
        problems.append("external must be a list")
        external = []
    for number, item in enumerate(external, 1):
        keys = set(EXTERNAL_KEYS) | ({"sha256"} if computed else set())
        if not isinstance(item, dict) or set(item) != keys:
            problems.append(f"external[{number}] must have exactly the keys {sorted(keys)}")
            continue
        if not str(item["path"]).startswith("../") or "\\" in str(item["path"]):
            problems.append(f"external[{number}].path must start with ../ and use '/'")
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
            if path.startswith("/") or ".." in Path(path).parts or "\\" in path or re.match(r"^[A-Za-z]:", path):
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
        goals = resolution.get("goals")
        if not isinstance(goals, list) or not goals or any(
            not isinstance(g, dict)
            or not {"goal", "met_by", "status"} <= set(g)
            or g["status"] not in ("met", "not-met")
            for g in goals
        ):
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
    """Return the manifest, None when there is none, or UNREADABLE when it is not a JSON mapping."""
    path = version_dir / "manifest.yaml"
    if not path.is_file():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return dict(UNREADABLE)
    return manifest if isinstance(manifest, dict) else dict(UNREADABLE)


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


def version_headings(repo: Path = REPO_ROOT) -> list[str]:
    """Return the version headings of the changelog of the spec, for example `["2.0.0"]`.

    A heading is never a pre-release: the changelog gives a pre-release as a line under its version.
    """
    path = repo / SPEC / "changelog.md"
    return VERSION_HEADING.findall(path.read_text(encoding="utf-8")) if path.is_file() else []


def spec_version(repo: Path = REPO_ROOT) -> str | None:
    """Return the newest version heading of the changelog of the spec, for example `2.0.0`, or None."""
    found = version_headings(repo)
    return max(found, key=_version_key) if found else None


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def record_entries(repo: Path = REPO_ROOT) -> dict[str, list[Path]]:
    """Return the spec-log entry files `<id>-<slug>.md` of each record folder `proposals/<slug>/`.

    Each record has exactly one entry (ADR-ZXD7, item 3).
    """
    proposals = repo / SPEC / "proposals"
    slugs = sorted(p.name for p in proposals.iterdir() if p.is_dir()) if proposals.is_dir() else []
    entries = sorted((repo / SPEC / "decisions" / "entries").glob("*.md"))
    names = {e: ENTRY_FILE.match(e.name) for e in entries}
    return {s: [e for e in entries if names[e] and names[e]["slug"] == s] for s in slugs}


def entry_statuses(repo: Path = REPO_ROOT) -> dict[str, str]:
    """Return the entry status of each proposal record, by the bundle ID of the record manifest.

    The check reads the status line of the entry as plain text. A record with no entry, or with a
    status that is not a proposal status, is not in the result.
    """
    result: dict[str, str] = {}
    for slug, paths in record_entries(repo).items():
        manifest = read_manifest(repo / SPEC / "proposals" / slug) or {}
        status = ENTRY_STATUS.search(paths[0].read_text(encoding="utf-8")) if paths else None
        if status and all(isinstance(manifest.get(k), str) for k in ("kind", "name", "contributor")):
            result[bundle_id(manifest)] = status.group(1)
    return result


def _state(answers: list[dict], entry: str | None) -> str:
    """Return the state of a bundle: the latest response, unless the entry status does not allow it."""
    state = answers[-1].get("state", "unreadable") if answers else "submitted"
    allowed = ALLOWED_RESPONSES.get(entry or "")
    return state if allowed is None or state in allowed else allowed[0]


def bundles(root: Path, repo: Path = REPO_ROOT) -> dict[str, dict]:
    """Return each bundle in `root` with its current version, manifest, state, entry status and responses."""
    found: dict[str, dict] = {}
    if not root.is_dir():
        return found
    statuses = entry_statuses(repo)
    for bundle_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if not BUNDLE_ID.match(bundle_dir.name):
            continue
        current = current_version(bundle_dir)
        answers = responses(bundle_dir)
        entry = statuses.get(bundle_dir.name)
        state = _state(answers, entry)
        manifest = read_manifest(current[1]) if current else None
        if manifest is not None and manifest.get("_unreadable"):
            manifest, state = {}, "unreadable manifest"
        recorded = next(
            (a.get("date", "") for a in answers if a.get("state") in OWNING), None
        )
        found[bundle_dir.name] = {
            "dir": bundle_dir,
            "version": current[0] if current else None,
            "manifest": manifest or {},
            "state": state if current else "in progress",
            "entry": entry,
            "responses": answers,
            "recorded": recorded,
        }
    return found


def _named_by(info: dict) -> set[str]:
    """Return the bundle IDs and the `proposal-<slug>@` prefixes that a bundle names.

    The `waiting_on` of the latest response also counts: a waiting model bundle names its proposals there.
    """
    manifest = info["manifest"]
    last = info["responses"][-1] if info["responses"] else {}
    names = (
        {manifest.get("base")}
        | set(manifest.get("depends_on") or [])
        | set(manifest.get("related") or [])
        | set(last.get("waiting_on") or [])
    )
    if manifest.get("contributes_to"):
        names.add(f"proposal-{manifest['contributes_to']}@")
    return {n for n in names if n}


def _names(name: str, bundle: str) -> bool:
    return bundle == name or (name.endswith("@") and bundle.startswith(name))


def owners(found: dict[str, dict], repo: Path | None = None) -> dict[str, str]:
    """Return the owner contributor of each section (ADR-ZXD7, item 3).

    A proposal with an entry owns its sections while the entry status is proposed, accepted or
    absorbed into. A proposal bundle with no entry owns them from its first `recorded` response
    until it is rejected, resolved otherwise or closed. A tracked record in
    `specs/model-sidecar/proposals/` keeps the role after the user deletes the bundle. A
    contribution never owns a section. When more than one proposal can own a section, the owner has
    the earlier manifest `created`, then the slug that sorts first.
    """
    candidates = []
    if repo is not None:
        statuses = entry_statuses(repo)
        for path in sorted((repo / SPEC / "proposals").glob("*/manifest.yaml")):
            manifest = read_manifest(path.parent) or {}
            names = all(isinstance(manifest.get(k), str) for k in ("kind", "name", "contributor"))
            if names and statuses.get(bundle_id(manifest)) in OWNING_ENTRY:
                candidates.append(manifest)
    for info in found.values():
        manifest = info["manifest"]
        if manifest.get("kind") != "proposal" or manifest.get("contributes_to"):
            continue
        if info["entry"] in OWNING_ENTRY or (
            info["entry"] is None and info["recorded"] is not None and info["state"] not in NOT_OWNING
        ):
            candidates.append(manifest)
    result: dict[str, str] = {}
    for manifest in sorted(candidates, key=lambda m: (str(m.get("created", "")), str(m.get("name", "")))):
        for section in manifest.get("sections") or []:
            result.setdefault(section, str(manifest.get("contributor", "")))
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
    text = text.removeprefix("﻿").replace("\r\n", "\n")
    if "\r" in text:
        raise BundleError(f"{rel}: a text file must have LF line ends (lone CR found)")
    return text.encode("utf-8")


def pack(
    source: Path,
    fields: dict,
    root: Path = DEFAULT_ROOT,
    cwd: Path | None = None,
    today: str | None = None,
    repo: Path = REPO_ROOT,
    external_base: Path | None = None,
) -> Path:
    """Write a new version of a bundle and return its folder. The manifest is written last.

    `spec_version` is the newest version heading of the changelog of `repo` (ADR-ZXD7, item 2).
    Each later version keeps the `created` of version 1. The `external` paths are relative to
    `external_base`, by default the parent of `root`.
    """
    problems = manifest_problems(fields, computed=False)
    if problems:
        raise BundleError("bad fields file:\n  " + "\n  ".join(problems))
    if not source.is_dir():
        raise BundleError(f"{source} is not a folder")
    newest = spec_version(repo)
    if newest is None:
        raise BundleError(f"{SPEC}/changelog.md has no version heading")
    payload: dict[str, bytes] = {}
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = path.relative_to(source).as_posix()
        if rel == "manifest.yaml":
            raise BundleError("the payload must not hold manifest.yaml: pack writes it")
        if reason := refused_file(rel):
            raise BundleError(reason)
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
    if findings := link_findings(source, payload, fields, repo):
        raise BundleError("links that fail from the record path:\n  " + "\n  ".join(findings))
    external = []
    base = external_base or root.parent
    for item in fields["external"]:
        target = (base / item["path"]).resolve()
        if not target.is_file():
            raise BundleError(f"external file not found: {item['path']}")
        if target.is_relative_to(base.resolve()):
            raise BundleError(f"external file must be outside the skellytracker repo: {item['path']}")
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        external.append({**item, "sha256": digest.hexdigest()})
    bundle_dir = root / bundle_id(fields)
    answers = responses(bundle_dir)
    state = _state(answers, entry_statuses(repo).get(bundle_id(fields)))
    if any(a.get("state") == "accepted" for a in answers):
        state = "accepted"
    if fields["kind"] == "proposal" and (state == "accepted" or state in FINISHED):
        raise BundleError(f"the bundle is {state}: write a new bundle with a new slug")
    existing = _numbered(bundle_dir, "v")
    version = existing[-1][0] + 1 if existing else 1
    created = [m.get("created") for _, d in existing for m in [read_manifest(d) or {}] if DATE.match(str(m.get("created")))]
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
        "spec_version": newest,
        "version": version,
        "created": created[0] if created else today or datetime.date.today().isoformat(),
        "files": files,
        "external": external,
    }
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (version_dir / "manifest.yaml").write_bytes(text.encode("utf-8"))
    return version_dir


def dry_pack(
    source: Path, fields: dict, root: Path = DEFAULT_ROOT, cwd: Path | None = None, repo: Path = REPO_ROOT
) -> list[str]:
    """Pack in a temporary folder and return the `verify` findings of the result. Write nothing in `root`.

    The temporary folder gets the version folders, the manifests and the responses of the bundle in
    `root`. The external files resolve from the parent of `root`, as in a real pack.
    """
    problems = manifest_problems(fields, computed=False)
    if problems:
        raise BundleError("bad fields file:\n  " + "\n  ".join(problems))
    name = bundle_id(fields)
    with tempfile.TemporaryDirectory() as temp:
        overlay = Path(temp)
        old = root / name
        for _, version_dir in _numbered(old, "v"):
            (overlay / name / version_dir.name).mkdir(parents=True)
            if (version_dir / "manifest.yaml").is_file():
                shutil.copyfile(version_dir / "manifest.yaml", overlay / name / version_dir.name / "manifest.yaml")
        if (old / "responses").is_dir():
            shutil.copytree(old / "responses", overlay / name / "responses")
        pack(source, fields, overlay, cwd, repo=repo, external_base=root.parent)
        return verify(name, root, repo, overlay=overlay)


# --------------------------------------------------------------------------------------------
# record (standard library only; a byte copy, never a run: ADR-AD33)
# --------------------------------------------------------------------------------------------


def record_folder(manifest: dict, repo: Path = REPO_ROOT) -> Path:
    """Return the tracked record folder of a proposal or a contribution ([Tracked records] of hand-over.md)."""
    contribution = manifest.get("contributes_to")
    if contribution:
        return repo / SPEC / "proposals" / contribution / "contributions" / manifest["contributor"]
    return repo / SPEC / "proposals" / manifest["name"]


def record(name: str, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT) -> Path:
    """Copy the current version of a proposal bundle byte for byte to its tracked record, and return the record.

    The copy replaces the old record in full. A proposal record keeps its `contributions/` folder.
    Each file is read as bytes and checked against the manifest before the copy, and the copy is
    read back after it. No file of the bundle is imported or run (ADR-AD33).
    """
    match = BUNDLE_ID.match(name)
    current = current_version(root / name) if match else None
    if current is None:
        raise BundleError(f"no complete version of the bundle {name} in {root}")
    version_dir = current[1]
    manifest = read_manifest(version_dir) or {}
    if problems := manifest_problems(manifest):
        raise BundleError("bad manifest; run verify:\n  " + "\n  ".join(problems))
    own = (manifest["kind"], manifest["name"], manifest["contributor"])
    if (match["kind"], match["name"], match["contributor"]) != own:
        raise BundleError("the manifest kind, name or contributor does not match the bundle ID; run verify")
    if manifest["kind"] != "proposal":
        raise BundleError("a model bundle gets no tracked record")
    contribution = manifest["contributes_to"]
    if contribution is not None and not NAME.match(contribution):
        raise BundleError(f"contributes_to must be a slug, not {contribution!r}")
    status = entry_statuses(repo).get(name)
    if not contribution and status not in (None, "proposed"):
        raise BundleError(f"the entry of the record is {status}: do not change the record")
    folder = record_folder(manifest, repo)
    old = read_manifest(folder)
    if old is not None and (old.get("kind"), old.get("name"), old.get("contributor")) != own:
        raise BundleError(f"{folder.relative_to(repo).as_posix()} is the record of another bundle; resolve the slug")
    listed = {f["path"]: f for f in manifest["files"]}
    on_disk = {p.relative_to(version_dir).as_posix() for p in version_dir.rglob("*") if p.is_file()}
    if on_disk - {"manifest.yaml"} != set(listed):
        raise BundleError("the files of the version are not the files of its manifest; run verify")
    payload = {"manifest.yaml": (version_dir / "manifest.yaml").read_bytes()}
    for rel, item in listed.items():
        if reason := refused_file(rel):
            raise BundleError(reason)
        payload[rel] = (version_dir / rel).read_bytes()
        if sha256(payload[rel]) != item["sha256"] or len(payload[rel]) != item["bytes"]:
            raise BundleError(f"{rel}: the hash or the size does not match the manifest; run verify")
    if folder.is_dir():
        for child in folder.iterdir():
            if not contribution and child.name == "contributions":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    for rel, data in payload.items():
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if changed := [rel for rel, data in payload.items() if (folder / rel).read_bytes() != data]:
        raise BundleError("the copy differs from the bundle: " + ", ".join(changed))
    return folder


# --------------------------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------------------------


def list_lines(root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT) -> list[str]:
    """Return the text that `list` prints.

    A `waiting` model bundle gets the line `waiting_on no longer open: <ids>` when a bundle of the
    `waiting_on` of its latest response is finished. The session then writes its next response
    (ADR-FM0B).
    """
    found = bundles(root, repo)
    lines = []
    for bid, info in found.items():
        # A contribution is not named by the slug prefix that its siblings give; only its owner bundle is.
        sibling = bool(info["manifest"].get("contributes_to"))
        needed_by = sorted(
            other
            for other, o in found.items()
            if other != bid
            and any(_names(n, bid) and not (sibling and n.endswith("@")) for n in _named_by(o))
        )
        open_needers = [n for n in needed_by if found[n]["state"] not in FINISHED]
        last = info["responses"][-1] if info["responses"] else {}
        version = f"v{info['version']}" if info["version"] else "-"
        line = f"{bid} {version} {info['state']}"
        if info["responses"] and info["version"] and last.get("answers_version") != info["version"]:
            line += " (new version)"
        goals = (last.get("resolution") or {}).get("goals") or []
        not_met = any(isinstance(g, dict) and g.get("status") == "not-met" for g in goals)
        followed = any(bid in (o["manifest"].get("related") or []) for o in found.values())
        kept = info["state"] == "resolved-otherwise" and not_met and not followed
        if info["state"] in FINISHED and not open_needers and not kept:
            line += " (can delete)"
        lines.append(line)
        if needed_by:
            lines.append(f"  needed by: {', '.join(needed_by)}")
        if info["manifest"].get("kind") == "model" and info["state"] == "waiting":
            done = [w for w in last.get("waiting_on") or [] if found.get(w, {}).get("state") in FINISHED]
            if done:
                lines.append(f"  waiting_on no longer open: {', '.join(done)}")
        if info["manifest"].get("sections"):
            lines.append(f"  sections: {', '.join(info['manifest']['sections'])}")
        if info["manifest"].get("spec_version"):
            lines.append(f"  spec_version: {info['manifest']['spec_version']}")
        lines.extend(
            f"  {f}" for f in last.get("findings") or [] if str(f).startswith("deferred:")
        )
    owned = owners(found, repo)
    if owned:
        lines.append("section owners:")
        lines.extend(f"  {section}: {owner}" for section, owner in sorted(owned.items()))
    return lines


# --------------------------------------------------------------------------------------------
# The static check of a reference module (standard library only; ADR-AD33, item 2)
# --------------------------------------------------------------------------------------------

# The standard-library modules that a reference module can import. Each one only computes: it has
# no access to files, the network, processes, the environment or the interpreter.
REFERENCE_STDLIB = frozenset({
    "__future__",  # `annotations`
    "math", "cmath", "statistics",  # real and complex functions, means and medians
    "numbers", "fractions", "decimal",  # the number types and exact arithmetic
    "itertools", "functools", "operator",  # loops, `reduce` and the operators as functions
    "bisect", "heapq",  # sorted search and priority queues (top-k, NMS)
    "collections", "dataclasses", "enum", "typing", "copy",  # containers, records and type hints
})
REFERENCE_PACKAGES = frozenset({"numpy", "cv2"})
# Part 3 of a new profile of common.batch_conversion also imports onnx (ADR-JB5J).
PROFILE_MODULE = "common_batch_conversion"
# A use of one of these names gives a finding: code, the interpreter or the file system.
FORBIDDEN_NAMES = frozenset({
    "open", "eval", "exec", "compile", "__import__", "breakpoint", "help",
    "globals", "locals", "vars", "__builtins__", "__loader__", "__spec__", "__file__",
    "get_type_hints", "ForwardRef", "singledispatch", "singledispatchmethod",  # these evaluate annotation text
})
# The allowed modules expose these modules or entries as attributes, for example `cv2.os`,
# `typing.sys`, `enum.bltns` and `np.testing.measure` (which runs text as code). The check matches
# them on each attribute, on any receiver.
SYSTEM_NAMES = frozenset({
    "os", "sys", "importlib", "inspect", "builtins", "bltns", "subprocess", "types", "ctypes", "io",
    "pathlib", "shutil", "socket", "threading", "multiprocessing", "signal", "platform", "runpy",
    "pickle", "marshal", "gc", "tempfile", "glob", "urllib", "http", "codecs", "linecache",
    "tokenize", "pkgutil", "zipimport", "posix", "nt", "contextlib", "warnings", "copyreg",
    "modules", "environ", "getenv", "putenv", "system", "popen", "testing", "measure", "as_strided",
})
# A call that takes an attribute name: the name must be a string literal.
NAME_CALLS = {"getattr": slice(1, 2), "setattr": slice(1, 2), "delattr": slice(1, 2),
              "attrgetter": slice(None), "methodcaller": slice(0, 1)}
# The NumPy and OpenCV names that read or write a file, or load other code. The check matches
# them on each attribute, on any receiver.
FILE_NAMES = frozenset({
    "fromfile", "fromregex", "fromtextfile", "tofile", "memmap", "open_memmap", "genfromtxt",
    "DataSource", "ctypeslib", "f2py", "distutils", "imcount",
})
FILE_PREFIX = re.compile(r"^(load|save|read|write(?!able$)|dump|imread|imwrite)|_(load|save)", re.IGNORECASE)
# The OpenCV modules, classes and factories that load a model or a data file, also as the flat
# `dnn_*` and `<module>_*` aliases of opencv-contrib.
CV2_FILE_PREFIX = re.compile(
    r"^(dnn|Face(Detector|Recognizer)|face_|(Base)?CascadeClassifier|haarcascade|HOGDescriptor|Tracker|legacy_"
    r"|rapid_|text(_|$)|wechat_qrcode|barcode|datasets|gapi|ml(_|$)|dpm_|linemod_|mcc_|ppf_match"
    r"|IStreamReader|utils(_|$)|File(Node|Storage)|Video(Capture|Writer)|samples|haveImage)"
)
SECTION_MODULE = re.compile(r"^(format|common|pre|post)_[a-z0-9_]*[a-z0-9]$")
SAFE_DUNDERS = frozenset({"__name__", "__doc__", "__init__", "__post_init__", "__all__", "__main__"})
NOT_CONSTANT = (ast.Call, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
                ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)
# The one call that a class body can hold: a dataclass field with arguments that call nothing.
FIELD_CALLS = frozenset({"field", "dataclasses.field"})


def _section_id(path: Path) -> str | None:
    match = re.search(r"^id:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def section_modules(repo: Path = REPO_ROOT) -> set[str]:
    """Return the module name of each section of the spec, for example `pre_resize_letterbox`."""
    ids = (_section_id(p) for folder in SECTION_FOLDERS for p in sorted((repo / SPEC / folder).glob("*.md")))
    return {i.replace(".", "_") for i in ids if i}


def module_names(manifests: list) -> set[str]:
    """Return the module name of each string of the `sections` of the manifests, for example `post_det_clamp`."""
    sections = (s for m in manifests if isinstance(m, dict) for s in m.get("sections") or [])
    return {s.replace(".", "_") for s in sections if isinstance(s, str)}


def _bad_name(name: str) -> bool:
    """True for a name that reaches code, the interpreter, a process or a file."""
    private = name.startswith("_") and name not in SAFE_DUNDERS
    return (
        private or name in FORBIDDEN_NAMES or name in SYSTEM_NAMES or name in FILE_NAMES
        or bool(FILE_PREFIX.search(name)) or bool(CV2_FILE_PREFIX.match(name))
    )


def _runs(node: ast.AST | None) -> bool:
    """True when the expression calls code when Python evaluates it."""
    return node is not None and any(isinstance(n, NOT_CONSTANT) for n in ast.walk(node))


def _call_ok(node: ast.AST | None, callees: frozenset | None) -> bool:
    """True when the expression calls nothing, or is one call of `callees` (None: any) with arguments that call nothing."""
    if isinstance(node, ast.Call) and (callees is None or ast.unparse(node.func) in callees):
        return not any(_runs(p) for p in [node.func, *node.args, *(k.value for k in node.keywords)])
    return not _runs(node)


def _body_problems(body: list, where: str, in_class: bool = False) -> list[str]:
    """Return a finding for each statement of a module or class body that runs code at import.

    The header of a `def` or a `class` also runs at import: the decorators, the default values, the
    annotations, the bases and the keywords.
    """
    found = []
    for number, node in enumerate(body):
        docstring = number == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        if docstring or isinstance(node, (ast.Import, ast.ImportFrom, ast.Pass)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(node, ast.ClassDef):
                header = [*node.bases, *(k.value for k in node.keywords)]
                found += _body_problems(node.body, f"the class {node.name}", in_class=True)
            else:
                a = node.args
                arguments = [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]
                header = [*a.defaults, *a.kw_defaults, node.returns, *(x.annotation for x in arguments if x)]
            if any(_runs(h) for h in header) or not all(_call_ok(d, None) for d in node.decorator_list):
                found.append(
                    f"line {node.lineno}: {where} runs code at import (the header of {node.name}); "
                    "a decorator can be one call with arguments that call nothing"
                )
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
        names = [n for t in targets for n in (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])]
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and all(isinstance(n, ast.Name) for n in names)
            and _call_ok(node.value, FIELD_CALLS if in_class else frozenset())
            and not _runs(getattr(node, "annotation", None))
        ):
            continue
        test = ast.unparse(node.test) if isinstance(node, ast.If) else None
        type_checking = (
            test in ("TYPE_CHECKING", "typing.TYPE_CHECKING") and not node.orelse
            and all(isinstance(n, (ast.Import, ast.ImportFrom)) for n in node.body)
        )
        if not type_checking:
            found.append(
                f"line {node.lineno}: {where} runs code at import ({type(node).__name__}); "
                "use only a docstring, imports, constants and definitions"
            )
    return found


def reference_problems(path: Path, sections: object = ()) -> tuple[list[str], list[str]]:
    """Read one reference module as text and return (findings, the names of its top-level functions).

    The check parses the file with `ast` only. It never imports, compiles or runs it (ADR-AD33,
    item 2). A module can import NumPy, OpenCV, `REFERENCE_STDLIB` and a section module by its name:
    a section of the spec or a name in `sections` (the manifest `sections` of the bundle, its owner,
    its `base` and its `depends_on`, with `_` for `.`). A file next to the module does not count.
    `PROFILE_MODULE` can also import onnx. The check cannot prove that code is safe: the review of
    item 3 stays the gate.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
        return [f"not a readable Python file: {type(exc).__name__}: {exc}"], []
    profile = path.stem == PROFILE_MODULE
    packages = REFERENCE_PACKAGES | ({"onnx"} if profile else set())
    spec_modules = section_modules()
    # A new section name has a section folder prefix, so it cannot stand for `os`. It must also not
    # be an installed module, for example `pre_commit`: after the copy, the import would load that.
    # `find_spec` of a top-level name only searches the paths; it runs no code of the bundle.
    new = {n for n in sections if SECTION_MODULE.match(n)} - spec_modules
    installed = {n for n in new if importlib.util.find_spec(n) is not None}
    known = spec_modules | (new - installed)
    # The local names of onnx in a profile module: its own model files are its job.
    onnx_names = {
        (a.asname or a.name).split(".")[0]
        for n in ast.walk(tree) if profile and isinstance(n, ast.Import) for a in n.names if a.name.split(".")[0] == "onnx"
    }
    found = _body_problems(tree.body, "the module")
    named = set()  # the Name and Attribute nodes that a checked NAME_CALLS call uses
    for node in ast.walk(tree):
        line = f"line {getattr(node, 'lineno', '?')}"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.level:
                found.append(f"{line}: a relative import")
                continue
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for module in modules:
                top, *rest = module.split(".")
                if isinstance(node, ast.ImportFrom) and top in known:
                    found.append(f"{line}: from {module} import: import the section module by its name")
                elif top in installed:
                    found.append(f"{line}: imports {module}: the section name is also the name of an installed module")
                elif top not in REFERENCE_STDLIB | packages | known:
                    found.append(f"{line}: imports {module}: not NumPy, OpenCV, a listed standard-library module or a section module")
                parts = rest + ([a.name for a in node.names] if isinstance(node, ast.ImportFrom) and top in packages else [])
                found += [f"{line}: imports {part} from {top}: it reaches a file or code" for part in parts
                          if part == "*" or (_bad_name(part) and not (top == "onnx" and profile))]
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name == "input" and isinstance(func, ast.Name):
                found.append(f"{line}: calls input")
            if name in NAME_CALLS:
                named.add(func)
                if not all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args[NAME_CALLS[name]]):
                    found.append(f"{line}: {name} with a name that is not a string literal")
        elif isinstance(node, ast.Name) and node not in named and (node.id in FORBIDDEN_NAMES or node.id in NAME_CALLS):
            found.append(f"{line}: uses {node.id}")
        elif isinstance(node, ast.Attribute) and node not in named and (_bad_name(node.attr) or node.attr in NAME_CALLS):
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if not (isinstance(root, ast.Name) and root.id in onnx_names and not node.attr.startswith("_")):
                found.append(f"{line}: uses the attribute {node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts = [p for p in node.value.split(".") if p.isidentifier() and p.strip("_") and _bad_name(p)]
            found += [f"{line}: the string {node.value!r} names {p}" for p in parts]
    functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return found, functions


def static_module(name: str, functions: list[str]) -> types.ModuleType:
    """Return a module object that has only the given function names. No line of the file runs."""
    module = types.ModuleType(name)
    for function in functions:
        def stub() -> None: ...
        stub.__module__ = name
        setattr(module, function, stub)
    return module


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
        ids.add(_section_id(path) or rel)
    return sorted(ids)


def _cases(data: object) -> dict[str, object]:
    cases = data.get("cases") if isinstance(data, dict) else None
    return {c["id"]: c for c in cases or [] if isinstance(c, dict) and "id" in c}


PART_2_4 = re.compile(r"^### 2\.4\b.*?(?=^#{1,3} |\Z)", re.MULTILINE | re.DOTALL)
RULE_ID = re.compile(r"`(V-[a-z][a-z0-9_.]*[a-z0-9]-\d+)`")


def vector_problems(data: object, section: str, folders: list[Path]) -> list[str]:
    """Return the form problems of one bundle or record vector file (ADR-8DSW, item 2).

    `folders` are bundle or record folders, the own folder first. The functions of a case are the
    top-level `def` names of `reference/<section_module>.py` of the first folder that has it. The
    check reads that file as text and never runs it (ADR-AD33, item 2). Without such a file, the
    producer of this checkout gives them. The rule IDs are those of the section files and of part
    2.4 of each `proposal.md` in `folders`. This loads numpy and the package, so `pack` and `list`
    never call it.
    """
    import make_vectors
    from vector_form import file_problems

    module = f"{section.replace('.', '_')}.py"
    own = next((f / "reference" / module for f in folders if (f / "reference" / module).is_file()), None)
    rules = set(make_vectors.rule_ids())
    for folder in folders:
        if (folder / "proposal.md").is_file():
            text = (folder / "proposal.md").read_text(encoding="utf-8", errors="replace")
            rules.update(RULE_ID.findall("".join(PART_2_4.findall(text))))
    loaded: list = []

    def reference():  # noqa: ANN202
        if not loaded:
            loaded.append(
                static_module(own.stem, reference_problems(own)[1]) if own else make_vectors.producer(section)
            )
        return loaded[0]

    try:
        return file_problems(data, rules, reference=reference, package_function=make_vectors.package_function)
    except Exception as exc:  # noqa: BLE001  # a producer that does not load, or data the check cannot read
        return [f"the form check stopped: {type(exc).__name__}: {exc}"]


def _same_case(mine: dict, theirs: dict, tolerance: object) -> bool:
    """A contribution case agrees with the case of its id: `expect` within the tolerance, `verified_against` aside (ADR-8DSW, item 5)."""
    from vector_form import agrees

    def rest(case: dict) -> dict:
        return {k: v for k, v in case.items() if k not in ("expect", "verified_against")}

    atol = tolerance if isinstance(tolerance, (int, float)) and not isinstance(tolerance, bool) else 0.0
    return rest(mine) == rest(theirs) and agrees(mine.get("expect"), theirs.get("expect"), theirs, atol)


def _load_yaml(version_dir: Path, rel: str, yaml) -> tuple[object, str | None]:  # noqa: ANN001
    """Return (data, None), or (None, finding) for a file that YAML (or JSON) cannot read."""
    try:
        return yaml.safe_load((version_dir / rel).read_text(encoding="utf-8")), None
    except (yaml.YAMLError, ValueError):
        return None, f"{rel}: not valid YAML/JSON"


def _payload_problems(version_dir: Path, rel: str, yaml, repo: Path = REPO_ROOT) -> list[str]:  # noqa: ANN001
    data, problem = _load_yaml(version_dir, rel, yaml)
    if problem:
        return [problem]
    problems = []
    if rel == "vector-runs.yaml":
        if not isinstance(data, dict) or set(data) != {"exporter", "commit", "runs"}:
            return ["vector-runs.yaml must have exactly the keys exporter, commit, runs"]
        if not SHA40.match(str(data["commit"])):
            problems.append("vector-runs.yaml commit must be 40 hex digits")
        if not isinstance(data["runs"], (list, type(None))):
            return [*problems, "vector-runs.yaml runs must be a list"]
        for number, run in enumerate(data["runs"] or [], 1):
            keys = {"section", "function", "vectors_sha256", "cases", "result"}
            if not isinstance(run, dict) or set(run) != keys:
                problems.append(f"vector-runs.yaml runs[{number}] must have exactly the keys {sorted(keys)}")
                continue
            if run["result"] not in ("pass", "fail", "no vectors"):
                problems.append(f"vector-runs.yaml runs[{number}].result must be pass, fail or no vectors")
            if run["result"] != "no vectors" and not SHA64.match(str(run["vectors_sha256"])):
                problems.append(f"vector-runs.yaml runs[{number}].vectors_sha256 must be 64 hex digits")
            if not isinstance(run["cases"], (dict, type(None))):
                problems.append(f"vector-runs.yaml runs[{number}].cases must be a mapping")
            elif any(v not in ("pass", "fail", "not used") for v in (run["cases"] or {}).values()):
                problems.append(f"vector-runs.yaml runs[{number}].cases values must be pass, fail or not used")
            if run["result"] != "no vectors" and SHA64.match(str(run["vectors_sha256"])):
                landed = repo / SPEC / "vectors" / f"{run['section']}.yaml"
                if not landed.is_file():
                    problems.append(f"vector-runs.yaml runs[{number}]: no landed vector file for {run['section']}")
                elif sha256(landed.read_bytes()) != run["vectors_sha256"]:
                    problems.append(
                        f"vector-runs.yaml runs[{number}]: vectors_sha256 is not the hash of the landed vector "
                        "file; run the cases again"
                    )
    elif rel == "example/provenance.yaml":
        if not isinstance(data, dict) or not set(data) <= {"examples", "fragments"}:
            return ["example/provenance.yaml must have only the keys examples and fragments"]
        for key in ("examples", "fragments"):
            if not isinstance(data.get(key), (dict, type(None))):
                return [f"example/provenance.yaml {key} must be a mapping"]
        for path, entry in (data.get("examples") or {}).items():
            if not isinstance(entry, dict) or not PROVENANCE_KEYS <= set(entry) <= PROVENANCE_KEYS | {"notes"}:
                problems.append(f"example/provenance.yaml examples[{path}] must have the keys {sorted(PROVENANCE_KEYS)} and may have notes")
            elif entry["kind"] != "export":
                problems.append(f"example/provenance.yaml examples[{path}].kind must be export")
        for path, entry in (data.get("fragments") or {}).items():
            if not isinstance(entry, dict) or set(entry) != FRAGMENT_KEYS:
                problems.append(f"example/provenance.yaml fragments[{path}] must have exactly the keys {sorted(FRAGMENT_KEYS)}")
    return problems


def _publish_problems(version_dir: Path, listed: dict, manifest: dict, yaml) -> list[str]:  # noqa: ANN001
    """Return the findings of the publish rule (every verdict) and of the dynamic check (ADR-JB5J)."""
    findings: list[str] = []
    external = manifest["external"]
    verdict, forced = manifest["batch_conversion"], manifest["batch_forced"]

    def load(rel: str, report: bool = True) -> dict:
        if rel not in listed:
            return {}
        data, problem = _load_yaml(version_dir, rel, yaml)
        if problem and report:
            findings.append(problem)
        return data if isinstance(data, dict) else {}

    published = {i["batch"] for i in external if i["published"]}
    pairs = sorted({(i["size"], i["precision"]) for i in external}, key=str)
    # A `describes` bundle lands an example, so each pair publishes one file (ADR-JB5J, item 4).
    if published or manifest.get("verdict") == "describes":
        for size, precision in pairs:
            count = sum(i["published"] for i in external if (i["size"], i["precision"]) == (size, precision))
            if count != 1:
                findings.append(f"publish rule: {size} {precision} must have exactly one published file, not {count}")
    if len(published) > 1 or not published <= set(FORMS):
        findings.append(
            f"publish rule: each published file must have one batch form ({SOURCE_BATCH}, 1 or dynamic), "
            f"not {sorted(map(str, published))}"
        )
    elif published:
        (form,) = published
        # A `to run` bundle plans its form; the session verdict decides it (hand-over.md, "The session run").
        # The session cannot add a missing verification batch, so that reason allows no form (ADR-JB5J, item 2).
        unverifiable = manifest.get("batch_conversion_reason") == "missing-verification-batch"
        allowed = {forced} if forced is not None else {
            "converts": {SOURCE_BATCH}, "does not convert": {1, "dynamic"}, "not applicable": {"dynamic"},
            "to run": set() if unverifiable else set(FORMS),
        }.get(verdict, set())
        if form not in allowed:
            findings.append(
                f"publish rule: the batch form {form} is not allowed with batch_conversion {verdict!r} "
                f"and batch_forced {forced!r}"
                + ("; export the verification batches 1, 2, 3 and 6, or set batch_forced" if unverifiable else "")
            )
        if form == SOURCE_BATCH:
            missing = [
                f"{s}/{p}/b{n}" for s, p in pairs for n in VERIFICATION_BATCHES
                if not any((i["size"], i["precision"], i["batch"]) == (s, p, n) for i in external)
            ]
            if missing:
                findings.append(f"publish rule: a b{SOURCE_BATCH} publish needs the verification batches: {missing}")
    source = published == {SOURCE_BATCH}
    examples = load("example/provenance.yaml", report=False).get("examples")
    examples = examples if isinstance(examples, dict) else {}
    published_files = {
        Path(i["path"]).name: (str(i["batch"]), i["precision"]) for i in external if i["published"]
    }
    # shortcut: reads the top-level `batching` and `sizes` of the sidecar only, not a `$ref`;
    # enough for the spec examples.
    for rel in (f"example/{path}" for path in examples):
        if rel not in listed:
            continue
        sidecar = load(rel)
        batching = sidecar.get("batching") or {}
        sidecar_batch = str(batching.get("batch"))  # one batch for each size and precision (ADR-JAA4)
        listed_files: dict[str, tuple[str, str]] = {}
        sizes = sidecar.get("sizes")
        for size in sizes.values() if isinstance(sizes, dict) else []:
            artifacts = ((size or {}).get("onnx") or {}).get("precision_artifacts") or {}
            for precision, entry in artifacts.items() if isinstance(artifacts, dict) else []:
                if isinstance(entry, dict) and entry.get("filename"):
                    listed_files[entry["filename"]] = (sidecar_batch, precision)
        if isinstance(sizes, dict):
            for name, (batch, precision) in sorted(published_files.items()):
                if listed_files.get(name) != (batch, precision):
                    findings.append(
                        f"precision mismatch: {name} is batch {batch} {precision} in the manifest "
                        f"but not in {rel}"
                    )
            findings += [
                f"{rel}: {name} has no published external entry"
                for name in sorted(set(listed_files) - set(published_files))
            ]
        if (batching.get("batch_conversion") is not None) != source:
            findings.append(
                f"publish rule: {rel} must have batching.batch_conversion "
                f"if and only if the published batch is {SOURCE_BATCH}"
            )
        elif source and batching["batch_conversion"] != PROFILE:
            findings.append(f"publish rule: {rel} must have batching.batch_conversion: {PROFILE}")
        if source and batching.get("batch") != SOURCE_BATCH:
            findings.append(f"publish rule: {rel} must have batching.batch: {SOURCE_BATCH}")
    if source and verdict == "converts":
        fragment = (
            (load("batch/conversion.yaml").get("batching") or {}).get("batch_conversion") or {}
            if "batch/conversion.yaml" in listed
            else {}
        )
        if fragment != PROFILE:
            findings.append(f"publish rule: batch/conversion.yaml must have batching.batch_conversion: {PROFILE}")
    dynamic = sorted(
        {(i["size"], i["precision"]) for i in external if i["published"] and i["batch"] == "dynamic"}, key=str
    )
    if dynamic:
        report = load("batch/report.json")
        checks = {
            (c.get("size"), c.get("precision")): c
            for c in report.get("dynamic_check") or []
            if isinstance(c, dict)
        }
        for size, precision in dynamic:
            check = checks.get((size, precision))
            if check is not None and check.get("result") == "pass":
                continue
            if "batch/report.json" not in listed:
                state = "has no batch/report.json"
            elif check is None:
                state = "has no entry in batch/report.json"
            else:
                state = f"is {check.get('result')}" + (f" ({check['reason']})" if check.get("reason") else "")
            findings.append(
                f"{size} {precision}: the dynamic check {state}; do not publish the dynamic export; "
                "publish another batch form or fix the export"
            )
    return findings


def verify(name: str, root: Path = DEFAULT_ROOT, repo: Path = REPO_ROOT, overlay: Path | None = None) -> list[str]:
    """Return the findings for the current version of one bundle. An empty list means it passes.

    The bundles in `overlay` replace those of `root` with the same ID (`pack --dry-run`). The
    external files resolve from the parent of `root`.
    """
    import yaml  # only verify needs it

    found = bundles(root, repo)
    if overlay is not None:
        found.update(bundles(overlay, repo))
    info = found.get(name)
    if info is None:
        return [f"no bundle {name} in {root}"]
    if info["version"] is None:
        return [f"{name} has no complete version (no manifest.yaml)"]
    if info["state"] == "unreadable manifest":
        return [f"manifest: v{info['version']}/manifest.yaml is not a JSON mapping"]
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
        if reason := refused_file(rel):
            findings.append(reason)
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
    if manifest["kind"] == "proposal" and not contribution and "proposal.md" in listed:
        # Parts 3 and 4 name the reference and vector files by their bundle path.
        text = (version_dir / "proposal.md").read_text(encoding="utf-8", errors="replace")
        named = set(re.findall(r"`((?:reference|vectors)/[^`<>\s]+)`", text))
        findings += [f"{rel}: proposal.md names this file, but the bundle does not have it" for rel in sorted(named - set(listed))]
    vectors = sorted(r for r in listed if r.startswith("vectors/") and r.endswith(".yaml"))
    if contribution and not vectors:
        findings.append("a contribution needs at least one vectors/<section ID>.yaml")
    owner_dirs = [
        o["dir"] / f"v{o['version']}"
        for o in found.values()
        if contribution
        and o["manifest"].get("kind") == "proposal"
        and o["manifest"].get("name") == manifest["contributes_to"]
        and not o["manifest"].get("contributes_to")
    ]
    # Reference modules, also those of the owner: read as text, never run (ADR-AD33, item 2). A
    # module can import the sections of this bundle, its owner, its `base` and its `depends_on`
    # (also from their records), never a file only because it is in the folder.
    linked = [manifest["base"], *manifest["depends_on"]] if manifest["kind"] == "proposal" else []
    manifests = [manifest, *(read_manifest(d) or {} for d in owner_dirs)]
    manifests += [found[b]["manifest"] for b in linked if b in found]
    manifests += [
        read_manifest(repo / SPEC / "proposals" / m["name"]) or {} for m in map(BUNDLE_ID.match, filter(None, linked)) if m
    ]
    sections = module_names(manifests)
    for folder in [version_dir, *owner_dirs]:
        prefix = "" if folder == version_dir else f"{folder.parent.name}/{folder.name}/"
        own = module_names([read_manifest(folder) or {}])
        for path in sorted((folder / "reference").rglob("*.py")):
            rel = path.relative_to(folder).as_posix()
            if path.parent != folder / "reference" or path.stem not in own | {PROFILE_MODULE}:
                findings.append(f"{prefix}{rel}: not reference/<section_module>.py of a section of the manifest")
            findings += [f"{prefix}{rel}: {p}" for p in reference_problems(path, sections)[0]]
    vector_data: dict[str, object] = {}
    for rel in vectors:
        section = rel.removeprefix("vectors/").removesuffix(".yaml")
        if section not in manifest["sections"]:
            findings.append(f"{rel}: the section {section} is not in the manifest sections")
        if listed[rel]["bytes"] > VECTOR_LIMIT:
            findings.append(f"{rel}: a vector file must be 256 KiB or smaller")
        if not (version_dir / rel).is_file():
            continue
        data, problem = _load_yaml(version_dir, rel, yaml)
        if problem:
            findings.append(problem)
            continue
        vector_data[rel] = data
        findings += [f"{rel}: {p}" for p in vector_problems(data, section, [version_dir, *owner_dirs])]

    # Text checks: private data, plans/ paths, links.
    terms = check_private_data.private_terms(repo)
    for rel in sorted(r for r in listed if is_text(r) and (version_dir / r).is_file()):
        text = (version_dir / rel).read_text(encoding="utf-8", errors="replace")
        findings.extend(f"private data: {f}" for f in check_private_data.scan_text(rel, text, terms))
        for number, line in enumerate(text.splitlines(), 1):
            if "plans/" in line:
                findings.append(f"{rel}:{number}: cites a plans/ path")
    findings += link_findings(version_dir, listed, manifest, repo)

    # Payload schemas.
    for rel in ("vector-runs.yaml", "example/provenance.yaml"):
        if rel in listed and manifest["kind"] == "model":
            findings.extend(_payload_problems(version_dir, rel, yaml, repo))

    # Links between bundles, ownership and contribution cases.
    others = list(manifest["related"])
    if manifest["kind"] == "proposal":
        others += [manifest["base"], *manifest["depends_on"]]
    findings += [f"the bundle {o} does not exist" for o in others if o and o not in found]
    if manifest["kind"] == "proposal":
        owned = owners(found, repo)
        if not contribution and not manifest["base"] and info["recorded"] is None and info["entry"] is None:
            for section in manifest["sections"]:
                owner = owned.get(section)
                if owner and owner != manifest["contributor"]:
                    findings.append(
                        f"the section {section} has the owner {owner}: send a contribution or a follow-up"
                    )
        if contribution:
            if not owner_dirs:
                findings.append(f"no proposal bundle with the slug {manifest['contributes_to']}")
            for rel, data in vector_data.items():
                mine = _cases(data)
                theirs: dict[str, tuple[dict, object]] = {}
                for source in (s for s in [repo / SPEC / rel, *(d / rel for d in owner_dirs)] if s.is_file()):
                    other, _ = _load_yaml(source.parent, source.name, yaml)
                    tolerance = other.get("tolerance") if isinstance(other, dict) else None
                    theirs.update({i: (case, tolerance) for i, case in _cases(other).items()})
                findings += [
                    f"{rel}: the case {case_id} differs from the owner case with the same id"
                    for case_id in sorted(set(mine) & set(theirs))
                    if not _same_case(mine[case_id], *theirs[case_id])
                ]

    # External files.
    for item in manifest["external"]:
        target = (root.parent / item["path"]).resolve()
        if not target.is_file():
            findings.append(f"external file not found: {item['path']}")
        elif target.is_relative_to(root.parent.resolve()):
            findings.append(f"external file must be outside the skellytracker repo: {item['path']}")
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
    # A response answers an existing version; a higher number hides the next version from list (hand-over.md, Responses).
    answered = info["responses"][-1].get("answers_version") if info["responses"] else None
    if isinstance(answered, int) and info["version"] and not 1 <= answered <= info["version"]:
        findings.append(
            f"responses: the latest response gives answers_version {answered}, but the current version is "
            f"v{info['version']}; answers_version is the version that the response answers"
        )
    allowed = ALLOWED_RESPONSES.get(info["entry"] or "")
    latest = info["responses"][-1].get("state") if info["responses"] else "submitted"
    if allowed and latest not in allowed:
        findings.append(
            f"responses: the latest state {latest} does not agree with the entry status {info['entry']}; "
            f"the session writes a response {' or '.join(allowed)}"
        )

    # Spec drift: the changed sections since spec_commit, and a newer version in the checkout (ADR-ZXD7, item 2).
    # A finished bundle gets no drift finding: no later response asks for a new version (ADR-FM0B).
    if latest in FINISHED:
        return findings
    changed = changed_sections(manifest["spec_commit"], repo)
    if changed is None:
        findings.append("spec_commit not found in this checkout; pack again on the current checkout")
    else:
        findings += [
            f"the section {section} changed since spec_commit; rebase on the current text"
            for section in manifest["sections"]
            if section in changed
        ]
    headings = version_headings(repo)
    newest = max(headings, key=_version_key) if headings else None
    if headings and manifest["spec_version"] not in headings:
        findings.append(
            f"spec_version {manifest['spec_version']} is not a version heading of the changelog of this "
            "checkout; pack a new version"
        )
    elif newest and _version_key(newest) > _version_key(manifest["spec_version"]):
        findings.append(
            f"the checkout has the newer spec version {newest} (spec_version {manifest['spec_version']}); "
            "read its changes and pack a new version"
        )
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


# The operator domains that onnxruntime builds in: the domains of
# `onnxruntime.capi.onnxruntime_pybind11_state.get_all_operator_schema()` of onnxruntime 1.27.0
# (CPU), and "ai.onnx", the other name of "".
ORT_DOMAINS = frozenset({"", "ai.onnx", "ai.onnx.ml", "com.microsoft", "com.microsoft.nchwc", "com.ms.internal.nhwc"})


def _sparse(items) -> list:  # noqa: ANN001
    return [t for s in items for t in (s.values, s.indices)]


def _attribute_tensors(attributes) -> list:  # noqa: ANN001
    return [t for a in attributes for t in (a.t, *a.tensors, *_sparse([a.sparse_tensor, *a.sparse_tensors]))]


def _graph_problems(graph, folder: Path, nodes=None, tensors=None) -> list[str]:  # noqa: ANN001
    """Return the node domains and the external data locations of `graph` and its subgraphs that `batch` refuses.

    For a model-local function, `nodes` and `tensors` give its nodes and the tensors of its attributes.
    """
    from onnx import TensorProto

    found = []
    if nodes is None:
        nodes, tensors = graph.node, [*graph.initializer, *_sparse(graph.sparse_initializer)]
    tensors = list(tensors)
    for node in nodes:
        if node.domain not in ORT_DOMAINS:
            found.append(f"the node {node.name or node.op_type} has the domain {node.domain!r}, which onnxruntime does not build in")
        tensors += _attribute_tensors(node.attribute)
        for attribute in node.attribute:
            found += [p for g in (attribute.g, *attribute.graphs) for p in _graph_problems(g, folder)]
    for tensor in tensors:
        if tensor.data_location != TensorProto.EXTERNAL:
            continue
        location = next((e.value for e in tensor.external_data if e.key == "location"), "")
        target = (folder / location).resolve()
        if not location or location.startswith(("/", "\\")) or PureWindowsPath(location).drive or Path(location).is_absolute() or ".." in location or not target.is_relative_to(folder):
            found.append(f"the tensor {tensor.name} has external data outside the folder of the model: {location!r}")
    return found


def onnx_problems(path: Path) -> list[str]:
    """Return why `batch` refuses an ONNX file (ADR-AD33, item 4). It reads the file with onnx only and runs nothing.

    `batch` refuses an operator domain that onnxruntime does not build in (`ORT_DOMAINS`), and
    external data with an absolute location, a `..` or a location outside the folder of the model.
    It checks the graph, its subgraphs, the model-local functions, the initializers and the dense
    and sparse tensors of each attribute.
    """
    import onnx

    try:
        model = onnx.load(str(path), load_external_data=False)
    except Exception as exc:  # noqa: BLE001  # any file that onnx cannot read is refused
        return [f"onnx cannot read the file: {type(exc).__name__}"]
    opsets = [*model.opset_import, *(o for f in model.functions for o in f.opset_import)]
    found = [f"the opset domain {o.domain!r} is not built into onnxruntime" for o in opsets if o.domain not in ORT_DOMAINS]
    folder = path.parent.resolve()
    for function in model.functions:  # model-local functions: their nodes and their attribute defaults
        found += _graph_problems(None, folder, function.node, _attribute_tensors(function.attribute_proto))
    return list(dict.fromkeys(found + _graph_problems(model.graph, folder)))


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

    @staticmethod
    def batched(item, batch: int) -> bool:  # noqa: ANN001
        """An input has a batch axis when dim 0 is symbolic or equals the batch of the graph."""
        dims = list(item.shape)
        return bool(dims) and (not isinstance(dims[0], int) or dims[0] == batch)

    def _shape(self, item, batch: int, rest: tuple | None = None) -> list[int]:  # noqa: ANN001
        """Return the feed shape. `rest` (the dims of input B after dim 0) fills a symbolic dim of the first input."""
        dims = list(item.shape)
        if not self.batched(item, batch):
            shape = dims
        else:
            tail = dims[1:]
            if rest is not None and len(rest) == len(tail):
                tail = [d if isinstance(d, int) else int(r) for d, r in zip(tail, rest, strict=True)]
            shape = [batch, *tail]
        if not all(isinstance(d, int) for d in shape):
            raise BundleError(f"input {item.name} has a dynamic dim other than dim 0: {item.shape}")
        return shape

    def _dtype(self, item) -> str:  # noqa: ANN001
        if item.type not in self.DTYPES:
            raise BundleError(f"input {item.name} has the type {item.type}: batch takes float, float16 or uint8")
        return self.DTYPES[item.type]

    def input_a(self, path: Path, batch: int, rest: tuple | None = None) -> dict:
        """Input A: seed 42; float inputs uniform in [0, 1), uint8 inputs integers in [0, 256)."""
        rng = self.np.random.default_rng(42)
        feeds = {}
        for index, item in enumerate(self.session(path).get_inputs()):
            shape, dtype = self._shape(item, batch, rest if index == 0 else None), self._dtype(item)
            if dtype == "uint8":
                feeds[item.name] = rng.integers(0, 256, shape, dtype=self.np.uint8)
            else:
                feeds[item.name] = rng.random(shape).astype(dtype)
        return feeds

    def input_b(self, path: Path, items, batch: int) -> dict:  # noqa: ANN001
        """Input B: the first `batch` items feed the first input. Other inputs take input A."""
        feeds = self.input_a(path, batch, items.shape[1:])
        first = self.session(path).get_inputs()[0]
        dtype = self._dtype(first)
        data = items[:batch]
        if dtype == "float16" and data.dtype == self.np.float32:
            data = data.astype(self.np.float16)
        if data.dtype != self.np.dtype(dtype) or list(data.shape) != self._shape(first, batch, items.shape[1:]):
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
        result: dict = {"pass": list(got) == list(want), "outputs": {}, "empty": False}
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
    """Return the input B items of one size: `inputs/<size>.npy`, INPUT_B_ITEMS different items."""
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
    # Remove the outputs of an earlier run first, so that a stop never leaves old evidence.
    out.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "differences.json", "conversion.yaml", "residual-diff.json"):
        (out / name).unlink(missing_ok=True)
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
        problems = onnx_problems(path)  # before any run (ADR-AD33, item 4)
        if problems:
            raise BundleError(f"batch does not run {item['path']}: " + "; ".join(problems))
        files[key], names[path] = path, item["path"]

    def clean(text: str) -> str:
        # Keep absolute paths out of the report: pack refuses them as private data.
        for path, name in names.items():
            text = text.replace(str(path), name)
        return text

    pairs = sorted({(s, p) for s, p, _ in files}, key=str)
    static = [k for k in files if k[2] != "dynamic"]

    # V0: applicability, for the whole family.
    missing = [
        [s, p, b] for s, p in pairs for b in VERIFICATION_BATCHES if (s, p, b) not in files
    ]
    # ADR-JB5J: a recorded batch_forced, or a dynamic-only family with no_static_reason, skips the check.
    # A b3-only or empty family is `to run`.
    if files and not static and fields.get("no_static_reason"):
        v0 = "not applicable"
    elif missing or not files:
        v0 = "not applicable" if fields.get("batch_forced") is not None else "missing-verification-batch"
    else:
        v0 = "pass"

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
                    # shortcut: the package converter still needs source_batch_size; drop it when M8 of
                    # specs/sidecar-implementation-plan.md changes the converter.
                    profile = {**PROFILE, "source_batch_size": SOURCE_BATCH}
                    summary = model_batch_convert(source, converted, target_batch=target, batch_conversion=profile)
                    record["v3"] = {"result": "pass", "summary": dataclasses.asdict(summary)}
                except Exception as exc:  # noqa: BLE001  # any refusal of the converter is a V3 failure
                    record["v3"] = {"result": "fail", "error": clean(str(exc))}
                    residuals[label] = {}
                    tuples.append(record)
                    continue
                residual = graph_diff(converted, native)  # V4
                record["v4_counts"] = _diff_counts(residual)
                tolerance = TOLERANCE[precision]
                batch_items = _input_items(inputs, size, items)
                try:  # V5: input A and input B on the native file
                    runs = {
                        "A": runner.input_a(native, target, batch_items.shape[1:]),
                        "B": runner.input_b(native, batch_items, target),
                    }
                    want = {k: runner.run(native, f) for k, f in runs.items()}
                except BundleError:
                    raise
                except Exception as exc:  # noqa: BLE001  # the native file does not run: not proof of a failure
                    record["v5"] = {"result": "to run", "error": clean(str(exc))}
                    reasons.append("host-runtime-cannot-load")
                    tuples.append(record)
                    continue
                record["v5"] = {}
                for k, f in runs.items():
                    try:
                        got = runner.run(converted, f)
                    except Exception as exc:  # noqa: BLE001  # a converted file that does not run fails V5
                        record["v5"][k] = {"pass": False, "outputs": {}, "empty": False, "error": clean(str(exc))}
                        continue
                    record["v5"][k] = runner.compare(got, want[k], tolerance)
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
        # (a) compares with each static file of the pair that exists at the batches 1, 2 and 3.
        need = {n: files[(size, precision, n)] for n in DYNAMIC_BATCHES if (size, precision, n) in files}
        if path not in loadable or any(n not in loadable for n in need.values()):
            check["result"], check["reason"] = "to run", "host-runtime-cannot-load"
            continue
        passed, compared = True, 0
        try:
            batch_items = _input_items(inputs, size, items)
            rest = batch_items.shape[1:]
            for n, native in need.items():  # (a) against the static natives
                for k, feeds in (
                    ("A", runner.input_a(native, n, rest)),
                    ("B", runner.input_b(native, batch_items, n)),
                ):
                    result = runner.compare(runner.run(path, feeds), runner.run(native, feeds), tolerance)
                    check["static"][f"b{n}/{k}"] = result
                    empty[(size, precision)].append(result["empty"])
                    compared += not result["empty"]
                    passed &= result["pass"]
            three = max(DYNAMIC_BATCHES)
            sliced = {i.name for i in runner.session(path).get_inputs() if runner.batched(i, three)}
            for k, feeds in (  # (b) self-consistency on three different items
                ("A", runner.input_a(path, three, rest)),
                ("B", runner.input_b(path, batch_items, three)),
            ):
                def part(start: int, stop: int, feeds: dict = feeds, sliced: set = sliced) -> dict:
                    return {i: v[start:stop] if i in sliced else v for i, v in feeds.items()}

                single = [runner.run(path, part(r, r + 1)) for r in range(three)]
                for n in DYNAMIC_BATCHES[1:]:
                    outputs = runner.run(path, part(0, n))
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
                        compared += not all(r["empty"] for r in rows)
                        passed &= all(r["pass"] for r in rows)
        except BundleError as exc:  # the tool cannot feed this file; it gates only the dynamic publication
            check["result"], check["reason"] = "to run", clean(str(exc))
            continue
        except Exception as exc:  # noqa: BLE001  # a dynamic file that does not run fails the check
            check["result"], check["error"] = "fail", clean(str(exc))
            continue
        if not passed:
            check["result"] = "fail"
        elif not compared:
            check["result"], check["reason"] = "to run", "no-signal"
        else:
            check["result"] = "pass"

    if v0 != "not applicable" and not reasons:
        reasons += ["no-signal" for pair, flags in empty.items() if flags and all(flags)][:1]
    if v0 == "not applicable":
        verdict, reason = "not applicable", None
    elif reasons:
        verdict, reason = "to run", reasons[0]
    elif any(t["v3"]["result"] == "fail" or t.get("v5", {}).get("result") == "fail" for t in tuples):
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
    pack_parser.add_argument(
        "--dry-run", action="store_true", help="pack in a temporary folder, run verify and write nothing"
    )
    commands.add_parser("list", parents=[root], help="list the bundles, their states and the section owners")
    verify_parser = commands.add_parser("verify", parents=[root], help="check the current version of a bundle")
    verify_parser.add_argument("bundle")
    record_parser = commands.add_parser(
        "record", parents=[root], help="copy the current version of a proposal bundle to its tracked record"
    )
    record_parser.add_argument("bundle")
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
        elif args.command == "pack" and not args.dry_run:
            fields = json.loads(args.fields.read_text(encoding="utf-8"))
            version_dir = pack(args.source, fields, args.root)
            print(f"packed {version_dir.parent.name} {version_dir.name}")
        elif args.command == "list":
            print("\n".join(list_lines(args.root)) or "no bundles")
        elif args.command == "record":
            folder = record(args.bundle, args.root)
            print(f"recorded {args.bundle} in {folder.relative_to(REPO_ROOT).as_posix()}")
        else:
            if args.command == "pack":
                print("dry run: nothing written")
                fields = json.loads(args.fields.read_text(encoding="utf-8"))
                findings = dry_pack(args.source, fields, args.root)
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
