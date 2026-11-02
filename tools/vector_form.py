"""The form of a sidecar vector case, and the comparison of two results of a case.

This module uses only the standard library and imports under Python 3.9, so that
a tool of a contributor can check a vector file without the environment of this
repository.

- `problems` returns what is wrong with the form of one case. It is the shape
  check of `tools/tests/test_vectors.py`, for the files of this repo and for the
  vectors of a proposal.
- `agrees` compares two results of one case within its `tolerance` and its
  per-field `compare` rules. NaN equals NaN.
- `defect` raises `CaseDefect`: a case or a formula is broken. `CaseDefect` is
  not a `ValueError`, so `make_vectors.outcome` never writes it as a refusal.
"""

from __future__ import annotations

import math
import re
from numbers import Real
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from types import ModuleType

CASE_KEYS = frozenset(
    {
        "id",
        "params",
        "input",
        "expect",
        "unproject",
        "tolerance",
        "compare",
        "function",
        "verified_against",
    }
)
REQUIRED_CASE_KEYS = frozenset({"id", "params", "input", "expect"})
COMPARE_KEYS = frozenset({"atol", "period"})
NO_RULE = "no-rule"
EXPORTER_ENTRY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*")
FUNCTION_REFERENCE = re.compile(r"[A-Za-z0-9_./-]+\.py::[A-Za-z_][A-Za-z0-9_]*")


class CaseDefect(Exception):
    """A case does not show what it claims, or a formula breaks its own invariant."""


def defect(message: str) -> NoReturn:
    """Stop the generator: the case or the formula is broken, the spec refuses nothing."""
    raise CaseDefect(message)


def has_fraction(value: Any) -> bool:
    """Return True when `value` holds a number with a fractional part."""
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(has_fraction(item) for item in value.values())
    if isinstance(value, list):
        return any(has_fraction(item) for item in value)
    return False


def entry_problems(entry: Any, package_function: Callable[[str], Any]) -> list[str]:
    """Check one `verified_against` entry.

    A string names a skellytracker function (`path::function`):
    `package_function(entry)` must return a callable. A mapping is one
    `{<Exporter repo>: <file>::<function>}`.
    """
    if isinstance(entry, str):
        return [] if callable(package_function(entry)) else [f"{entry}: not a function"]
    if not (isinstance(entry, dict) and len(entry) == 1):
        return [f"{entry!r}: not one exporter entry"]
    ((repo, reference),) = entry.items()
    if not (isinstance(repo, str) and EXPORTER_ENTRY.fullmatch(repo)):
        return [f"{entry!r}: the exporter repo name has a wrong form"]
    if not (isinstance(reference, str) and FUNCTION_REFERENCE.fullmatch(reference)):
        return [f"{entry!r}: not a <file>::<function> reference"]
    return []


def problems(
    case: Any,
    rule_ids: Collection[str],
    *,
    reference: Callable[[], ModuleType],
    package_function: Callable[[str], Any],
) -> list[str]:
    """Return what is wrong with the form of one case; an empty list when nothing is.

    `rule_ids` are the rule IDs that the section files define. `reference()`
    returns the reference module of the section of the case; it is called only
    when the case names a `function`. `package_function` resolves a skellytracker
    entry of `verified_against` (see `entry_problems`). An exception of either
    callable propagates.
    """
    if not isinstance(case, dict):
        return [f"{case!r}: a case is a mapping"]
    case_id = case.get("id")
    if not REQUIRED_CASE_KEYS <= set(case) <= CASE_KEYS:
        return [f"{case_id}: the keys {sorted(case)} are not a case form"]
    if not all(isinstance(case[key], dict) for key in ("params", "input", "expect")):
        return [f"{case_id}: params, input and expect must be mappings"]
    found: list[str] = []
    expect, unproject = case["expect"], case.get("unproject")
    if has_fraction(expect) or has_fraction(unproject):
        if "tolerance" not in case and "compare" not in case:
            found.append(f"{case_id}: a fractional result needs tolerance or compare")
    elif "tolerance" in case:
        found.append(f"{case_id}: tolerance without a fractional result")
    if "error" in expect:
        if set(expect) != {"error"}:
            found.append(f"{case_id}: an error result has no other key")
        error = expect["error"]
        if error != NO_RULE and error not in rule_ids:
            found.append(f"{case_id}: {error} is not a defined rule ID")
    if "failed" in expect:
        if set(expect) != {"failed"}:
            found.append(f"{case_id}: a failed result has no other key")
        failed = expect["failed"]
        if not (isinstance(failed, list) and failed == sorted(set(failed))):
            found.append(f"{case_id}: failed must be a sorted list without repeats")
        elif not set(failed) <= set(rule_ids):
            found.append(f"{case_id}: {failed} names an undefined rule ID")
    if "compare" in case:
        compare = case["compare"]
        if not isinstance(compare, dict):
            found.append(f"{case_id}: compare must be a mapping")
            compare = {}
        fields = set(expect) | set(unproject or {})
        for field, rule in compare.items():
            if field not in fields:
                found.append(f"{case_id}: compare names the unknown field {field}")
            if not (rule and isinstance(rule, dict) and set(rule) <= COMPARE_KEYS):
                found.append(f"{case_id}: compare.{field} has keys other than atol and period")
                continue
            if not all(isinstance(v, (int, float)) and v >= 0 for v in rule.values()):
                found.append(f"{case_id}: compare.{field} needs numbers of 0 or more")
            elif not rule.get("period", 1) > 0:
                found.append(f"{case_id}: compare.{field}.period must be more than 0")
    if "function" in case:
        module = reference()
        function = getattr(module, case["function"], None)
        if not callable(function):
            found.append(f"{case_id}: no function {case['function']} in {module.__name__}")
        # The function of a case is defined in the module of its own section.
        elif function.__module__ != module.__name__:
            found.append(f"{case_id}: {case['function']} is from another module")
    for entry in case.get("verified_against", []):
        found.extend(entry_problems(entry, package_function))
    return found


def agrees(given: Any, computed: Any, case: dict[str, Any] | None = None) -> bool:
    """Return True when two results of a case are equal within the case's tolerance.

    Without `case`, the comparison is exact. With `case`, `given` and
    `computed` are results of that case (for example two `expect` mappings): a
    number that is not an integer on both sides may differ by `tolerance`, and
    `compare.<field>` replaces it for one top-level field (`atol`, and `period`
    for an angle). Integers on both sides must be equal. NaN equals NaN.
    """
    if case is None:
        return _agrees(given, computed, 0.0, None)
    tolerance = case.get("tolerance", 0.0)
    compare = case.get("compare") or {}
    if not (isinstance(given, dict) and isinstance(computed, dict)):
        return _agrees(given, computed, tolerance, None)
    if given.keys() != computed.keys():
        return False
    for key in given:
        rule = compare.get(key)  # `compare` replaces `tolerance` for its field
        atol = rule.get("atol", 0.0) if rule else tolerance
        if not _agrees(given[key], computed[key], atol, rule.get("period") if rule else None):
            return False
    return True


def _agrees(a: Any, b: Any, atol: float, period: float | None) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_agrees(a[k], b[k], atol, period) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_agrees(x, y, atol, period) for x, y in zip(a, b))  # noqa: B905 (3.9 has no strict; the lengths are equal)
    if a == b:
        return True
    if not (_is_number(a) and _is_number(b)) or isinstance(a, int) and isinstance(b, int):
        return False  # integers must match exactly
    a, b = float(a), float(b)
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    if not (math.isfinite(a) and math.isfinite(b)):
        return False  # unequal infinities, or an infinity and a finite number
    difference = abs(a - b)
    if period is not None:
        difference %= period
        difference = min(difference, period - difference)
    return difference <= atol


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)
