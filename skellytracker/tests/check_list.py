"""The list of the check names of skellytracker, `core/eps/certify_checks.yaml`, for the tests of section 5.7 of the format.

`entry_of(name)` gives the entry of the list that a check name of a report matches, or None.
"""

import functools
import importlib.resources
import re

import yaml

# the variable parts of a template name; a label is an EP key, with `@<vendor>-<device>-<rank>` for a pair on a GPU
PLACEHOLDERS = {"<label>": r"[a-z0-9-]+(?:@[0-9a-f]{4}-[0-9a-f]{4}-\d+)?", "<n>": r"\d+", "<check>": r".+", "<slug>": r"[a-z0-9-]+",
                "<name>": r".+"}
JPEG_PREFIX = "<label>:jpeg:"


@functools.cache
def entries() -> tuple[dict, ...]:
    text = (importlib.resources.files("skellytracker.core.eps") / "certify_checks.yaml").read_text(encoding="utf-8")
    return tuple(yaml.safe_load(text)["checks"])


@functools.cache
def _patterns() -> tuple[tuple[re.Pattern, dict], ...]:
    found = []
    for entry in entries():
        pattern = re.escape(entry["name"])
        for placeholder, part in PLACEHOLDERS.items():
            pattern = pattern.replace(re.escape(placeholder), part)
        found.append((re.compile(pattern), entry))
    return tuple(found)


def entry_of(name: str) -> dict | None:
    """The first entry whose template matches the whole check name, or None."""
    return next((entry for pattern, entry in _patterns() if pattern.fullmatch(name)), None)


def jpeg_entries() -> dict[str, dict]:
    """The entries of the JPEG checks by the name of `CHECK_NAMES` of `core/decode/certification.py`."""
    return {entry["name"][len(JPEG_PREFIX):]: entry for entry in entries() if entry["name"].startswith(JPEG_PREFIX)}
