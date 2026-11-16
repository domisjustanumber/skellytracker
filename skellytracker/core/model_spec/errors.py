"""The errors of the spec loader.

Each error names the file that causes it. `rules` holds the rule IDs of the sidecar spec that the
file fails, for example `V-format.composition-2`. An error with no rule ID has an empty `rules`.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class Failure(NamedTuple):
    """One failed check: the rule ID and what is wrong."""

    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.message}"


class SidecarError(Exception):
    """The base class of the spec loader errors."""

    def __init__(self, message: str, file_path: Path | None = None, rules: tuple[str, ...] = ()) -> None:
        self.file_path = file_path
        self.rules = rules
        if file_path is not None:
            message = f"{message} (file: {file_path})"
        super().__init__(message)


class SidecarParseError(SidecarError):
    """A sidecar, a fragment or a schema file is not readable YAML, has bad bytes or repeats a key."""


class SidecarRefError(SidecarError):
    """A `$ref` directive is not valid: its form, its target, its hash or a cycle."""


class SidecarSchemaVersionError(SidecarError):
    """The `schema_version` of a sidecar is not a version that this release implements."""


class SidecarValidationError(SidecarError):
    """A resolved sidecar or a landmark schema file fails one or more rules. `failures` lists them."""

    def __init__(self, failures: list[Failure], file_path: Path | None = None) -> None:
        self.failures = failures
        lines = "\n".join(f"  {failure}" for failure in failures)
        super().__init__(
            f"{len(failures)} failed check(s):\n{lines}",
            file_path=file_path,
            rules=tuple(dict.fromkeys(failure.rule for failure in failures)),
        )
