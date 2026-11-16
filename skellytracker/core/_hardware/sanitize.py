"""Remove absolute paths from texts that leave the package."""

import ntpath
import os
import posixpath
import re
import sys

_PATH_TOKEN = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")


def _replace(text: str, path: str, mark: str) -> str:
    if not path or path in ("/", "\\"):
        return text
    # A Windows path has no case, also when the text is read on another OS.
    flags = re.IGNORECASE if os.name == "nt" or ntpath.splitdrive(path)[0] else 0
    for form in {path, path.replace("\\", "/"), path.replace("/", "\\")}:
        text = re.sub(re.escape(form), lambda _: mark, text, flags=flags)
    return text


def sanitize_text(text: str, prefix: str | None = None, home: str | None = None) -> str:
    """Change `sys.prefix` to `<prefix>` and then the home folder to `~` in an error or reason text."""
    text = _replace(text, sys.prefix if prefix is None else prefix, "<prefix>")
    return _replace(text, os.path.expanduser("~") if home is None else home, "~")


def reduce_token(token: str) -> str:
    """Change an absolute path or a `file:` URL to its basename. Other data tokens do not change."""
    head, sep, tail = token.partition("=") if token.startswith("-") else ("", "", token)
    if tail.startswith("file:") or _PATH_TOKEN.match(tail):
        tail = posixpath.basename(ntpath.basename(tail.rstrip("/\\")))
    return head + sep + tail


def error_line(source: str, error: BaseException | str) -> str:
    """One `probe_errors` or `sample_errors` line: `<source>: <message>`, sanitized."""
    message = error if isinstance(error, str) else f"{type(error).__name__}: {error}"
    return sanitize_text(f"{source}: {message}")
