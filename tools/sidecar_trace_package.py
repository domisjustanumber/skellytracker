#!/usr/bin/env python3
"""Run the commands of `tools/sidecar_trace.py` with the package resolver and the package sidecars.

`tools/sidecar_trace.py` moves to the specs repository with the specs, and the specs repository
must not depend on the package. So it imports no skellytracker and has no sidecar resolver of its
own. This entry point stays in this repository. It gives the trace tool the resolver
`resolve_sidecar_composition` of the package and the package sidecar root `PACKAGE_ROOT`.

Commands::

    uv run python tools/sidecar_trace_package.py matrix [--check]
    uv run python tools/sidecar_trace_package.py impact GIT_RANGE
    uv run python tools/sidecar_trace_package.py examples --exporters-root DIR

The module docstring of `tools/sidecar_trace.py` gives what each command does.
"""

from __future__ import annotations

import sys
from pathlib import Path

import sidecar_trace
from skellytracker.core.model_spec.resolution import resolve_sidecar_composition

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "skellytracker" / "core" / "model_zoo"
# The keyword arguments of the scan functions of `sidecar_trace` for this checkout.
HOST = {"resolve": resolve_sidecar_composition, "package_root": PACKAGE_ROOT}


def main(argv: list[str] | None = None) -> int:
    return sidecar_trace.main(argv, **HOST, prog=Path(__file__).name)


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
