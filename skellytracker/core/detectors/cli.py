"""The CLI commands `detectors` and `describe` of `python -m skellytracker`."""
from __future__ import annotations

import argparse
import dataclasses
import json
from typing import Any

from skellytracker.core.detectors.catalog import DetectorEntry, DetectorNotFoundError, describe_detector, list_detectors

COMMANDS = ("detectors", "describe")


def _state(entry: DetectorEntry) -> str:
    state = "available" if entry.available else f"unavailable: {entry.unavailable_reason}"
    return f"superseded, {state}" if entry.superseded else state


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def main(arguments: list[str]) -> int:
    """Run `detectors` or `describe <key>`. Return the exit code: 0, or 1 for a key that is not in the catalog."""
    parser = argparse.ArgumentParser(prog="skellytracker")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (("detectors", "list the models of the catalog"), ("describe", "show one model of the catalog")):
        command = commands.add_parser(name, help=text)
        if name == "describe":
            command.add_argument("key", help="<model_id>@<source.name>, with an optional pin ==<version>")
        command.add_argument("--json", action="store_true", help="print JSON")
        command.add_argument("--user-root", default=None, help="the user root (default: SKELLYTRACKER_USER_ROOT, else the user data folder)")
        command.add_argument("--full-hash", action="store_true", help="hash each ONNX file again; do not use the hash check cache")
    options = parser.parse_args(arguments)

    if options.command == "detectors":
        entries = list_detectors(options.user_root, full_hash=options.full_hash)
        if options.json:
            _print_json([dataclasses.asdict(entry) for entry in entries])
        else:
            for entry in entries:
                version = "" if entry.version is None else f"=={entry.version}"
                print(f"{entry.key}{version}  [{entry.category}]  {_state(entry)}")
        return 0

    try:
        description = describe_detector(options.key, options.user_root, full_hash=options.full_hash)
    except DetectorNotFoundError as exc:
        print(exc.args[0])
        return 1
    if options.json:
        _print_json(dataclasses.asdict(description))
        return 0
    entry = description.entry
    print(f"{entry.key}  [{entry.category}]  {entry.display_name}")
    print(f"  state: {_state(entry)}")
    if entry.sidecar_path is not None:
        print(f"  version: {entry.version}")
        print(f"  sidecar: {entry.sidecar_path}")
        print(f"  sidecar_sha256: {entry.sidecar_sha256}")
    for artifact in entry.artifacts:
        state = f"unavailable: {artifact.unavailable_reason}"
        if artifact.available:
            state = "available" if artifact.downloaded else "available, not downloaded"
        print(f"  size {artifact.size}, {artifact.precision}: {artifact.filename}  {state}")
    for port in description.ports:
        print(f"  port {port.name}: {port.direction}, {port.port_type}")
    for name, value in description.params.items():
        print(f"  param {name}: {json.dumps(value)}")
    if description.point_names:
        print(f"  point names ({len(description.point_names)}): {', '.join(description.point_names)}")
    return 0
