"""The form of a sidecar vector file, and the comparison of two results of a case.

This module uses only the standard library and imports under Python 3.9, so that
a tool of a contributor can check a vector file without the environment of this
repository.

- `file_problems` returns what is wrong with the form of one vector file, and
  `problems` what is wrong with one case. They are the shape check of
  `tools/tests/test_vectors.py`, for the files of this repo and for the vectors
  of a proposal.
- `agrees` compares two results of one case within the `tolerance` of its file
  and the per-field `compare` rules of the case. NaN equals NaN.
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

# The keys of a file, in their order. `None` stands for `verified_against` or `unverified`.
FILE_KEYS = ("section", "notes", "tolerance", "checks", None, "cases")
REQUIRED_FILE_KEYS = frozenset({"section", "tolerance", "cases"})
# The keys of a case, in their order.
CASE_KEYS = (
    "id",
    "note",
    "function",
    "checks",
    "params",
    "input",
    "expect",
    "compare",
    "verified_against",
)
REQUIRED_CASE_KEYS = frozenset({"id", "params", "input", "expect"})
COMPARE_KEYS = frozenset({"atol", "period"})
NO_RULE = "no-rule"
# The `function` of a data-only validator case: the generator does not run it.
DATA_ONLY = "none"
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


def _in_order(keys: list[Any], order: tuple[Any, ...]) -> bool:
    """True when each key is in `order` once and the keys keep that order."""
    if not all(key in order for key in keys):
        return False
    positions = [order.index(key) for key in keys]
    return positions == sorted(set(positions))


def _names(value: Any) -> bool:
    """True when `value` is a list of strings without repeats."""
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and len(value) == len(set(value))
    )


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


def _verified_problems(
    owner: Any, entries: Any, package_function: Callable[[str], Any]
) -> list[str]:
    if not isinstance(entries, list):
        return [f"{owner}: verified_against must be a list"]
    return [problem for entry in entries for problem in entry_problems(entry, package_function)]


def file_problems(
    data: Any,
    rule_ids: Collection[str],
    *,
    reference: Callable[[], ModuleType],
    package_function: Callable[[str], Any],
) -> list[str]:
    """Return what is wrong with the form of one vector file and its cases.

    Over `problems` of each case, it checks the rules between cases and the file:
    an `error` result iff the check `refused` (of the case or the file), and the
    place, `params` and `input` of each `<id>-inverse` case. The arguments after
    `data` are those of `problems`.
    """
    if not isinstance(data, dict):
        return [f"{data!r}: a vector file is a mapping"]
    keys = [None if key in ("verified_against", "unverified") else key for key in data]
    if not (
        REQUIRED_FILE_KEYS <= set(keys) and keys.count(None) == 1 and _in_order(keys, FILE_KEYS)
    ):
        return [f"the keys {list(data)} are not a file form"]
    found: list[str] = []
    section = data["section"]
    if not isinstance(section, str):
        found.append(f"{section!r}: section must be a string")
    notes = data.get("notes", [])
    if not (isinstance(notes, list) and all(isinstance(note, str) and note for note in notes)):
        found.append(f"{section}: notes must be a list of strings")
    tolerance = data["tolerance"]
    if not (_is_number(tolerance) and tolerance >= 0):
        found.append(f"{section}: tolerance must be a number of 0 or more")
    file_checks = data.get("checks", [])
    if not _names(file_checks):
        found.append(f"{section}: checks must be a list of names without repeats")
        file_checks = []
    if "unverified" in data and not (isinstance(data["unverified"], str) and data["unverified"]):
        found.append(f"{section}: unverified must give a reason")
    found.extend(_verified_problems(section, data.get("verified_against", []), package_function))
    cases = data["cases"]
    if not (isinstance(cases, list) and cases):
        return [*found, f"{section}: cases must be a list of one or more cases"]
    ids = [case.get("id") if isinstance(case, dict) else None for case in cases]
    if len(ids) != len(set(ids)):
        found.append(f"{section}: the case ids repeat")
    for before, case in zip([None, *cases], cases):  # noqa: B905 (3.9 has no strict)
        found.extend(
            problems(case, rule_ids, reference=reference, package_function=package_function)
        )
        if not isinstance(case, dict):
            continue
        case_checks = case.get("checks", [])
        if not _names(case_checks):
            case_checks = []  # `problems` reports it
        if set(file_checks) & set(case_checks):
            found.append(f"{case.get('id')}: a check of the file is also a check of the case")
        expect = case.get("expect")
        if ("error" in expect if isinstance(expect, dict) else False) != (
            "refused" in [*file_checks, *case_checks]
        ):
            found.append(f"{case.get('id')}: an error result needs the check refused, and only it")
        found.extend(_inverse_problems(case, before))
    return found


INVERSE_SUFFIX = "-inverse"


def _inverse_problems(case: dict[str, Any], before: Any) -> list[str]:
    """One case is one call: `<id>-inverse` follows the case `<id>` and adds `model_xy` to its input."""
    case_id = case.get("id")
    if not isinstance(case_id, str):
        return []  # `problems` reports the id
    is_inverse = case.get("function") == "inverse"
    if is_inverse != case_id.endswith(INVERSE_SUFFIX):
        return [f"{case_id}: an Inverse case has function inverse and an id <forward id>-inverse"]
    if not is_inverse:
        return []
    forward_id = case_id[: -len(INVERSE_SUFFIX)]
    if not (isinstance(before, dict) and before.get("id") == forward_id):
        return [f"{case_id}: an Inverse case follows the case {forward_id} directly"]
    found = []
    if case.get("params") != before.get("params"):
        found.append(f"{case_id}: an Inverse case has the params of its forward case")
    given, forward_input = case.get("input"), before.get("input")
    if not (
        isinstance(given, dict)
        and isinstance(forward_input, dict)
        and "model_xy" in given
        and "model_xy" not in forward_input
        and {key: value for key, value in given.items() if key != "model_xy"} == forward_input
    ):
        found.append(f"{case_id}: the input of an Inverse case is the forward input plus model_xy")
    return found


def problems(
    case: Any,
    rule_ids: Collection[str],
    *,
    reference: Callable[[], ModuleType],
    package_function: Callable[[str], Any],
) -> list[str]:
    """Return what is wrong with the form of one case; an empty list when nothing is.

    `rule_ids` are the rule IDs that the section files define. `reference()`
    returns the producer module of the section of the case; it is called only
    when the case runs a function (`run` when `function` is absent, and not for
    `function: none`). `package_function` resolves a skellytracker entry of
    `verified_against` (see `entry_problems`). An exception of either callable
    propagates.
    """
    if not isinstance(case, dict):
        return [f"{case!r}: a case is a mapping"]
    case_id = case.get("id")
    if not (REQUIRED_CASE_KEYS <= set(case) and _in_order(list(case), CASE_KEYS)):
        return [f"{case_id}: the keys {list(case)} are not a case form"]
    if not isinstance(case_id, str):
        return [f"{case_id!r}: the id must be a string"]
    if not all(isinstance(case[key], dict) for key in ("params", "input", "expect")):
        return [f"{case_id}: params, input and expect must be mappings"]
    found: list[str] = []
    expect = case["expect"]
    shared = set(case["params"]) & set(case["input"])
    if shared:
        found.append(f"{case_id}: params and input share the keys {sorted(shared)}")
    if "note" in case and not (isinstance(case["note"], str) and case["note"]):
        found.append(f"{case_id}: note must be a string")
    if "checks" in case and not _names(case["checks"]):
        found.append(f"{case_id}: checks must be a list of names without repeats")
    if "error" in expect:
        if set(expect) != {"error"}:
            found.append(f"{case_id}: an error result has no other key")
        error = expect["error"]
        if error == NO_RULE and "note" not in case:
            found.append(f"{case_id}: a no-rule result needs a note")
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
        for field, rule in compare.items():
            if field not in expect:
                found.append(f"{case_id}: compare names the unknown field {field}")
            if not (rule and isinstance(rule, dict) and set(rule) <= COMPARE_KEYS):
                found.append(f"{case_id}: compare.{field} has keys other than atol and period")
                continue
            if not all(isinstance(v, (int, float)) and v >= 0 for v in rule.values()):
                found.append(f"{case_id}: compare.{field} needs numbers of 0 or more")
            elif not rule.get("period", 1) > 0:
                found.append(f"{case_id}: compare.{field}.period must be more than 0")
    name = case.get("function", "run")
    if name == DATA_ONLY:
        if set(expect) != {"failed"}:
            found.append(f"{case_id}: function none is only for a failed result")
    elif not isinstance(name, str):
        found.append(f"{case_id}: function must be a name")
    else:
        module = reference()
        function = getattr(module, name, None)
        if not callable(function):
            found.append(f"{case_id}: no function {name} in {module.__name__}")
        # The function of a case is defined in the module of its own section.
        elif function.__module__ != module.__name__:
            found.append(f"{case_id}: {name} is from another module")
    found.extend(_verified_problems(case_id, case.get("verified_against", []), package_function))
    return found


def agrees(
    given: Any, computed: Any, case: dict[str, Any] | None = None, tolerance: float = 0.0
) -> bool:
    """Return True when two results of a case are equal within the file's tolerance.

    `tolerance` is the `tolerance` of the vector file. With `case`, `given` and
    `computed` are results of that case (for example two `expect` mappings), and
    `compare.<field>` of the case replaces `tolerance` for one top-level field
    (`atol`, and `period` for an angle). A number that is not an integer on both
    sides may differ by the tolerance. Integers on both sides must be equal. NaN
    equals NaN. Without `case` and `tolerance`, the comparison is exact.
    """
    compare = (case or {}).get("compare") or {}
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
