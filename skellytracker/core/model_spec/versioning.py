"""The `schema_version` values that this release implements.

A host loads only the versions that it implements. There is no legacy reading of an older version.
A pre-release host also lists its own pre-release value, for example `"2.0.0-rc.1"`.
"""
from __future__ import annotations

import re
from typing import Any

from skellytracker.core.model_spec.errors import Failure

IMPLEMENTED_SCHEMA_VERSIONS: tuple[str, ...] = ("2.0.0",)

# SemVer MAJOR.MINOR.PATCH with an optional pre-release tag, and no build metadata.
_IDENTIFIER = r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER = re.compile(rf"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-{_IDENTIFIER}(?:\.{_IDENTIFIER})*)?")


def check_schema_version(value: Any) -> Failure | None:
    """Return the failure of a `schema_version` value, or None when this release implements it.

    Implements: format.versioning
    """
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        return Failure(
            "V-format.versioning-1",
            f"schema_version {value!r} is not a SemVer string in quotes, for example \"2.0.0\"",
        )
    if value not in IMPLEMENTED_SCHEMA_VERSIONS:
        return Failure(
            "V-format.versioning-2",
            f"this release does not implement schema_version {value!r}; it implements {list(IMPLEMENTED_SCHEMA_VERSIONS)}",
        )
    return None
