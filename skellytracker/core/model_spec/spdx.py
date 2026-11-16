"""SPDX license expressions, checked against a pinned copy of the SPDX License List.

`spdx_license_list.json` holds the license ids and the exception ids of one release of
https://github.com/spdx/license-list-data, with the SHA-256 of its two input files. It holds no
license text. Do not edit it by hand.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

_IDSTRING = r"[A-Za-z0-9.\-]+"
_LICENSE_REF = re.compile(rf"(?:DocumentRef-{_IDSTRING}:)?LicenseRef-{_IDSTRING}")
_ADDITION_REF = re.compile(rf"(?:DocumentRef-{_IDSTRING}:)?AdditionRef-{_IDSTRING}")
_TOKEN = re.compile(r"\(|\)|[^\s()]+")
_OPERATORS = {"AND", "OR", "and", "or"}
_WITH = {"WITH", "with"}


@functools.cache
def _ids() -> tuple[frozenset[str], frozenset[str], str]:
    data = json.loads((Path(__file__).parent / "spdx_license_list.json").read_text(encoding="utf-8"))
    # SPDX matches a license id without regard to case.
    licenses = frozenset(name.lower() for name in data["license_ids"])
    exceptions = frozenset(name.lower() for name in data["exception_ids"])
    return licenses, exceptions, data["license_list_version"]


def spdx_license_list_version() -> str:
    """Return the version of the pinned SPDX License List."""
    return _ids()[2]


def has_license_ref(expression: str) -> bool:
    """Return True when the expression holds a `LicenseRef-` id."""
    return any(_LICENSE_REF.fullmatch(token) for token in _TOKEN.findall(expression))


def is_spdx_expression(expression: str) -> bool:
    """Return True when `expression` is a valid SPDX license expression.

    Implements: common.license

    The grammar is that of the SPDX specification: `AND`, `OR`, `WITH`, `+`, parentheses and
    `LicenseRef-` ids. An operator is all upper case or all lower case.
    """
    licenses, exceptions, _ = _ids()
    tokens = _TOKEN.findall(expression)
    position = 0

    def peek() -> str | None:
        return tokens[position] if position < len(tokens) else None

    def simple() -> bool:
        nonlocal position
        word = peek()
        if word is None:
            return False
        position += 1
        if word == "(":
            if not compound() or peek() != ")":
                return False
            position += 1
            return True
        known = _LICENSE_REF.fullmatch(word) or word.removesuffix("+").lower() in licenses
        if not known:
            return False
        if peek() in _WITH:
            exception = tokens[position + 1] if position + 1 < len(tokens) else ""
            position += 2
            return exception.lower() in exceptions or bool(_ADDITION_REF.fullmatch(exception))
        return True

    def compound() -> bool:
        nonlocal position
        if not simple():
            return False
        while peek() in _OPERATORS:
            position += 1
            if not simple():
                return False
        return True

    return compound() and position == len(tokens)
