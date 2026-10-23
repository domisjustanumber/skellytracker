"""Check relative Markdown links and their #anchor targets.

Anchors are generated the way GitHub does: lowercase; punctuation dropped
except `-` and `_`; each space becomes `-`; a repeated heading gets `-1`,
`-2`, ... appended. Links inside fenced code blocks and inline code are
skipped.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LINK = re.compile(r"(?<!!)\[(?:[^\]\[]|\[[^\]]*\])*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_INLINE_CODE = re.compile(r"`[^`]*`")
_HTML_ANCHOR = re.compile(r"<a\s+(?:id|name)=\"([^\"]+)\"")


def _strip_inline_code(text: str) -> str:
    return _INLINE_CODE.sub("", text)


def github_slug(heading: str) -> str:
    """Return the anchor GitHub generates for a heading's text."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    # GitHub keeps the text of a code span literally (including `<...>`) and
    # drops HTML tags only outside code spans.
    parts = re.split(r"(`[^`]*`)", text)
    text = "".join(
        (
            part[1:-1]
            if len(part) > 1 and part.startswith("`") and part.endswith("`")
            else re.sub(r"<[^>]+>", "", part)
        )
        for part in parts
    )
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """Return every anchor a Markdown file defines."""
    found: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        found.update(_HTML_ANCHOR.findall(line))
        match = _HEADING.match(line)
        if not match:
            continue
        slug = github_slug(match.group(2))
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        found.add(slug if n == 0 else f"{slug}-{n}")
    return found


def links(path: Path) -> list[tuple[int, str]]:
    """Return `(line_number, target)` for each link outside code."""
    result: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        text = _strip_inline_code(line)
        for pattern in (_LINK, _IMAGE):
            result.extend((number, m.group(1)) for m in pattern.finditer(text))
    return result


def check_file(path: Path, root: Path) -> list[str]:
    """Return one error string per broken link in `path`."""
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for number, target in links(path):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue  # http:, https:, mailto:, ...
        file_part, _, anchor = target.partition("#")
        file_part = unquote(file_part)
        dest = path if not file_part else (path.parent / file_part).resolve()
        where = f"{path.relative_to(root).as_posix()}:{number}"
        if not dest.exists():
            errors.append(f"{where}: missing file {target}")
            continue
        if anchor and dest.suffix.lower() == ".md":
            if dest not in anchor_cache:
                anchor_cache[dest] = anchors(dest)
            if unquote(anchor) not in anchor_cache[dest]:
                errors.append(f"{where}: missing anchor {target}")
    return errors


def markdown_files(root: Path) -> list[Path]:
    """Return the tracked docs the link check covers."""
    files = [root / "AGENTS.md"] if (root / "AGENTS.md").exists() else []
    for folder in ("specs", "notes", ".claude/skills"):
        if (root / folder).is_dir():
            files.extend(sorted((root / folder).rglob("*.md")))
    return files


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    paths = [Path(p).resolve() for p in argv[2:]] or markdown_files(root)
    errors = [e for p in paths for e in check_file(p, root)]
    print("\n".join(errors) if errors else f"{len(paths)} files: all links resolve")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
