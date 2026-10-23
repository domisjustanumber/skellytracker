"""Normalize a resolved sidecar and match section selectors against it.

A section file of the sidecar spec lists ``selectors`` in its front matter. A selector tells which
sidecars the section applies to. This module holds the two pure functions that answer the question:

- ``normalize(resolved)`` applies the derivations of ``NORMALIZATION_TABLE`` to a resolved
  sidecar. A resolved sidecar is the dict that ``resolve_sidecar_composition`` returns.
- ``matches(selector, normalized)`` and ``applies(front_matter, normalized)`` match selectors
  against the normalized dict.

The module is written to move into ``skellytracker/core/sidecar/`` without a change. It uses only the
standard library and imports nothing from ``tools/``. The trace tool imports it today. The runtime
capability check (``notes/decisions/0016-sidecar-catalogs.md``) will use the same functions, so the
rules are read in one place only.

Selector syntax
---------------

A selector is ``<path>=<value>`` or ``<path>``.

- ``<path>`` is a list of keys, separated by dots, on the normalized dict. A segment ``name[]``
  means "any element of the list at ``name``", for example ``outputs[].semantic=heatmap``.
- A selector without ``=value`` matches when the path exists and the node is not null.
- A selector with ``=value`` compares strings: ``str(node) == value``, with ``True`` and ``False``
  written ``true`` and ``false``. When the node is a list of scalars, the selector matches when any
  element is equal to the value, for example ``role=object_detector``.
- A section applies to a sidecar when any selector of the section matches (OR). A section of kind
  ``format`` or ``common`` applies to every sidecar and has ``selectors: []``.

The table is small on purpose. It holds only what the matching needs. It is not a validator.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

UNIVERSAL_KINDS = frozenset({"format", "common"})
"""Section kinds that apply to every sidecar."""

_SEGMENT = re.compile(r"[A-Za-z0-9_\-]+(\[\])?")


# --------------------------------------------------------------------------------------------
# The normalization table
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizationRule:
    """One derivation. `section` and `heading` name the spec text that the derivation follows.

    `apply` changes the dict in place and returns True when it changed something. A rule with no
    `apply` records a case where nothing changes.
    """

    name: str
    section: str
    heading: str
    summary: str
    apply: Callable[[dict[str, Any]], bool] | None = None


def _roles(data: Mapping[str, Any]) -> list[Any]:
    role = data.get("role")
    if isinstance(role, str):
        return [role]
    return list(role) if isinstance(role, (list, tuple)) else []


def _input_of(data: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return `input` when it is a mapping. The input defaults apply to nothing else."""
    value = data.get("input")
    return value if isinstance(value, dict) else None


def _derive_selection(data: dict[str, Any]) -> bool:
    if "object_detector" not in _roles(data):
        return False
    decode = data.get("decode")
    if decode is None:
        decode = data["decode"] = {}
    if not isinstance(decode, dict) or decode.get("selection") is not None:
        return False
    decode["selection"] = "nms" if decode.get("requires_nms") is True else "none"
    return True


def _default_resize(data: dict[str, Any]) -> bool:
    input_ = _input_of(data)
    if input_ is None or input_.get("resize") is not None:
        return False
    input_["resize"] = {"method": "none"}
    return True


def _letterbox_alias(data: dict[str, Any]) -> bool:
    input_ = _input_of(data)
    resize = input_.get("resize") if input_ is not None else None
    if not isinstance(resize, dict):
        return False
    if (
        resize.get("method") != "letterbox"
        or resize.get("preserve_aspect_ratio") is not False
    ):
        return False
    resize["method"] = "stretch"
    return True


def _default_normalization(data: dict[str, Any]) -> bool:
    input_ = _input_of(data)
    if input_ is None or input_.get("normalization") is not None:
        return False
    input_["normalization"] = "imagenet_bgr"
    return True


NORMALIZATION_TABLE: tuple[NormalizationRule, ...] = (
    NormalizationRule(
        name="selection",
        section="post.det.decode",
        heading="Legacy behaviour",
        summary=(
            "When `role` includes `object_detector` and `decode.selection` is absent, "
            "`decode.selection` is `nms` if `decode.requires_nms` is true, and `none` otherwise."
        ),
        apply=_derive_selection,
    ),
    NormalizationRule(
        name="resize",
        section="common.input",
        heading="Fields",
        summary="When `input.resize` is absent, `input.resize.method` is `none`.",
        apply=_default_resize,
    ),
    NormalizationRule(
        name="letterbox_alias",
        section="pre.resize.letterbox",
        heading="Legacy behaviour",
        summary=(
            "When `input.resize.method` is `letterbox` and "
            "`input.resize.preserve_aspect_ratio` is false, `input.resize.method` is `stretch`."
        ),
        apply=_letterbox_alias,
    ),
    NormalizationRule(
        name="normalization",
        section="pre.normalize",
        heading="Fields",
        summary="When `input.normalization` is absent, it is `imagenet_bgr`.",
        apply=_default_normalization,
    ),
    NormalizationRule(
        name="custom_normalization",
        section="pre.normalize",
        heading="Behaviour",
        summary=(
            "An `input.normalization` object `{mode: custom, ...}` stays an object. "
            "Its selector is `input.normalization.mode=custom`."
        ),
    ),
)
"""The derivations, in the order that `normalize` applies them."""


def normalize(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a resolved sidecar with the derivations of `NORMALIZATION_TABLE` applied."""
    return _normalize(resolved)[0]


def derived_by(resolved: Mapping[str, Any]) -> tuple[str, ...]:
    """Return the names of the rules that change the resolved sidecar, in table order."""
    return _normalize(resolved)[1]


def _normalize(resolved: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    if not isinstance(resolved, Mapping):
        raise TypeError(
            f"a resolved sidecar is a mapping, not {type(resolved).__name__}"
        )
    data = copy.deepcopy(dict(resolved))
    changed = tuple(
        rule.name
        for rule in NORMALIZATION_TABLE
        if rule.apply is not None and rule.apply(data)
    )
    return data, changed


# --------------------------------------------------------------------------------------------
# Selector matching
# --------------------------------------------------------------------------------------------


def parse_selector(selector: str) -> tuple[tuple[str, ...], str | None]:
    """Split a selector into its path segments and its value (None when there is no value).

    Raise `ValueError` when the selector is not well formed.
    """
    if not isinstance(selector, str):
        raise ValueError(f"a selector is a string, not {type(selector).__name__}")
    path, separator, value = selector.partition("=")
    segments = tuple(path.split("."))
    for segment in segments:
        if not _SEGMENT.fullmatch(segment):
            raise ValueError(f"selector {selector!r}: bad path segment {segment!r}")
    if separator and not value:
        raise ValueError(f"selector {selector!r}: empty value")
    return segments, (value if separator else None)


def _text(node: Any) -> str | None:
    """Return the comparison text of a scalar node, or None for any other node."""
    if isinstance(node, bool):
        return "true" if node else "false"
    if isinstance(node, (str, int, float)):
        return str(node)
    return None


def _child(node: Any, key: str) -> tuple[bool, Any]:
    if not isinstance(node, Mapping):
        return False, None
    if key in node:
        return True, node[key]
    for name, value in node.items():
        if str(name) == key:
            return True, value
    return False, None


def _nodes(root: Any, segments: tuple[str, ...]) -> list[Any]:
    current = [root]
    for segment in segments:
        fan_out = segment.endswith("[]")
        key = segment[:-2] if fan_out else segment
        following: list[Any] = []
        for node in current:
            found, child = _child(node, key)
            if not found:
                continue
            if fan_out:
                if isinstance(child, list):
                    following.extend(child)
            else:
                following.append(child)
        current = following
    return current


def matches(selector: str, normalized: Mapping[str, Any]) -> bool:
    """Return True when the selector matches the normalized sidecar."""
    segments, value = parse_selector(selector)
    nodes = _nodes(normalized, segments)
    if value is None:
        return any(node is not None for node in nodes)
    for node in nodes:
        candidates = node if isinstance(node, list) else [node]
        if any(_text(candidate) == value for candidate in candidates):
            return True
    return False


def applies(front_matter: Mapping[str, Any], normalized: Mapping[str, Any]) -> bool:
    """Return True when a section applies to a normalized sidecar.

    `front_matter` is the parsed front matter of the section file. A section of kind `format` or
    `common` applies to every sidecar. Any other section applies when any selector matches.
    """
    if front_matter.get("kind") in UNIVERSAL_KINDS:
        return True
    selectors = front_matter.get("selectors") or []
    if not isinstance(selectors, list):
        raise ValueError("`selectors` is a list of strings")
    return any(matches(selector, normalized) for selector in selectors)
