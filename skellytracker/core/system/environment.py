"""`probe_environment()`: the Python, the installed distributions and the command line.

No text of the result holds an absolute path. In a frozen application `packages` holds only the
distributions whose metadata the application bundles.
"""

import importlib.metadata
import json
import platform
import re
import sys
import threading

from skellytracker.core._hardware.sanitize import error_line, reduce_token
from skellytracker.core.system.records import EnvironmentInfo, PackageInfo, PackageSource, PythonInfo

_lock = threading.Lock()
_cached: EnvironmentInfo | None = None


def package_source(direct_url_text: str | None) -> PackageSource | None:
    """The PEP 610 source of a distribution from its `direct_url.json` text. `None` for an index install."""
    if not direct_url_text:
        return None
    data = json.loads(direct_url_text)
    url = re.sub(r"://[^/@]*@", "://", str(data.get("url", "")))  # no user name and no token
    vcs = data.get("vcs_info") or {}
    is_file = url.startswith("file:") or "+file:" in url
    hashes = (data.get("archive_info") or {}).get("hashes") or {}
    return PackageSource(
        vcs=vcs.get("vcs"), url=None if is_file else url or None, commit=vcs.get("commit_id"),
        requested_revision=vcs.get("requested_revision"), local=reduce_token(url.split("+", 1)[-1]) if is_file else None,
        editable=bool((data.get("dir_info") or {}).get("editable")), hashes=tuple(sorted(hashes.items())),
    )


def _packages(errors: list[str]) -> tuple[PackageInfo, ...]:
    packages = {}
    for distribution in importlib.metadata.distributions():
        try:
            name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
            packages[name] = PackageInfo(name, distribution.version, package_source(distribution.read_text("direct_url.json")))
        except Exception as error:  # noqa: BLE001 - broken metadata of one distribution is one line
            errors.append(error_line("distribution", error))
    return tuple(packages[name] for name in sorted(packages))


def probe_environment() -> EnvironmentInfo:
    """The environment facts. The first call reads them; each later call gives the same record."""
    global _cached
    with _lock:
        if _cached is None:
            errors: list[str] = []
            number, date = platform.python_build()
            _cached = EnvironmentInfo(
                python=PythonInfo(platform.python_implementation(), platform.python_version(), f"{number}, {date}",
                                  platform.python_compiler()),
                packages=_packages(errors), argv=tuple(reduce_token(token) for token in sys.orig_argv),
                frozen=bool(getattr(sys, "frozen", False)), probe_errors=tuple(errors),
            )
        return _cached
