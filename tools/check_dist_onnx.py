#!/usr/bin/env python3
"""Fail when a wheel or an sdist holds an ``.onnx`` file (decision AMJ8 item 5).

Usage::

    python tools/check_dist_onnx.py [PATH ...]

Each PATH is a wheel (``.whl``), an sdist (``.tar.gz``) or a folder. The tool checks each wheel and
each sdist directly in a folder. The default PATH is ``dist``. The release workflow
``.github/workflows/flit_publish_to_pypi.yml`` runs the tool after ``flit build`` and before the
upload.

flit puts each file of the package folder in a wheel, also a file that git ignores. An ONNX file of
the package sidecar root ``skellytracker/core/model_zoo/`` must not go in a release. The tool
prints each ``.onnx`` member and exits 1. It exits 2 when it finds no wheel and no sdist, because
then it checked nothing. Otherwise it exits 0. Standard library only.
"""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path


def archives(paths: list[Path]) -> list[Path]:
    """The wheels and the sdists of `paths`. A folder gives the archives directly in it."""
    found = []
    for path in paths:
        candidates = sorted(path.iterdir()) if path.is_dir() else [path]
        found += [p for p in candidates if p.name.endswith((".whl", ".tar.gz"))]
    return found


def onnx_members(archive: Path) -> list[str]:
    """The names of the ``.onnx`` members of a wheel or an sdist."""
    if archive.name.endswith(".whl"):
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
    else:
        with tarfile.open(archive, "r:gz") as tf:
            names = tf.getnames()
    return [name for name in names if name.lower().endswith(".onnx")]


def main(argv: list[str]) -> int:
    found = archives([Path(arg) for arg in argv] or [Path("dist")])
    if not found:
        print("no wheel and no sdist found", file=sys.stderr)
        return 2
    status = 0
    for archive in found:
        for name in onnx_members(archive):
            print(f"{archive.name}: {name}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
