"""The warning of a pipeline load or a pipeline run (pipeline.running, Fields; ADR-V7GZ item 6).

A warning does not use the Python `warnings` module.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineWarning:
    """One warning. `code` is one of the codes of the pipeline spec, for example `missing_dependency`."""

    code: str
    message: str
    node_ids: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)
