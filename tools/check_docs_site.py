#!/usr/bin/env python3
"""Check that the docs site in ``skellytracker-docs/`` agrees with the public API.

Usage::

    python tools/check_docs_site.py            # the coverage, dead-name and page checks
    python tools/check_docs_site.py --staged   # the commit reminder of the pre-commit hook

The default mode applies these rules. It prints one line for each finding and exits 1 on a finding:

1. Coverage. Each name that a module of ``EXPORT_FILES`` exports must occur in a code span or a
   code block of ``API_PAGE``. A module with ``__all__`` exports the names of ``__all__``. A module
   with no ``__all__`` exports each name that it imports at the top level from the package
   ``skellytracker``. A module with no ``__all__`` and no such import exports each function of its
   top level whose name does not start with ``_``. A name of ``UNDOCUMENTED`` is not checked. Each
   item of it gives its reason.
2. Dead names. In a table of ``API_PAGE`` whose first header cell is ``Signature``, the first cell
   of a row that starts with a code span ``name(`` must name an exported name. The rule does not
   check method names, because the method tables do not use the header ``Signature``.
3. Front matter. Each ``.mdx`` page under ``docs/`` and ``blog/`` must start with a front matter
   block that has ``title``.
4. Links. Each relative link of a page must go to a page file: the path, the path with ``.mdx`` or
   ``.md``, or the ``index.mdx`` or ``index.md`` of the folder. The tool does not check an anchor,
   an absolute path or a URL. The site build checks them.
5. Words. The words "machine" and "PC" must not occur outside code. The docs say "system".

The ``--staged`` mode reads the staged files from git. When the commit changes a file of
``PUBLIC_API_FILES`` and no file under ``skellytracker-docs/``, it prints one reminder line that
names the skill ``update-docs-site``. It always exits 0: not each API change needs a page change.

The tool uses only static reads: no network, no ``node``, and no import of the package, of
``onnxruntime`` or of ``mediapipe``. Exit codes: 0 when there is no finding, 1 on a finding, 2 for a
usage error. Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = "skellytracker-docs"
PAGE_DIRS = (f"{DOCS}/docs", f"{DOCS}/blog")
API_PAGE = f"{DOCS}/docs/technical/api-reference.mdx"
EXPORT_FILES = (
    "skellytracker/__init__.py",
    "skellytracker/core/pipelines/__init__.py",
    "skellytracker/core/detectors/__init__.py",
    "skellytracker/core/eps/__init__.py",
    "skellytracker/certification.py",
)
PUBLIC_API_FILES = (
    *EXPORT_FILES,
    "skellytracker/__main__.py",
    "skellytracker/core/pipelines/cli.py",
    "skellytracker/core/eps/cli.py",
    "skellytracker/core/detectors/cli.py",
    "skellytracker/core/detectors/factory.py",
    "pyproject.toml",
    "skellytracker/REASON_CODES.md",
    "skellytracker/core/model_zoo/pipelines/*.yaml",
)
SKILL = ".claude/skills/update-docs-site/SKILL.md"
# An exported name that is not public API, with its reason. Empty: the page names each export.
UNDOCUMENTED: dict[str, str] = {}
WORDS = (re.compile(r"\bmachines?\b", re.IGNORECASE), re.compile(r"\bPCs?\b"))

FENCE = re.compile(r"^[ \t]*```.*?^[ \t]*```[^\n]*$", re.MULTILINE | re.DOTALL)
SPAN = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
SIGNATURE = re.compile(r"^`([A-Za-z_]\w*)\(")


def exported_names(path: Path) -> list[str]:
    """The names that one module exports (rule 1)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            return list(ast.literal_eval(node.value))
    imported = [
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "skellytracker"
        for alias in node.names
    ]
    return imported or [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")]


def code_text(text: str) -> str:
    """The text of each code block and each code span of a page."""
    blocks = FENCE.findall(text)
    return "\n".join([*blocks, *SPAN.findall(FENCE.sub("", text))])


def prose(text: str) -> str:
    """The page without code, with the same line numbers."""
    return SPAN.sub("", FENCE.sub(lambda m: "\n" * m.group().count("\n"), text))


def missing_names(page: str, exported: list[str]) -> list[str]:
    """The exported names that no code of the page names (rule 1)."""
    code = code_text(page)
    return [n for n in exported if n not in UNDOCUMENTED and not re.search(rf"\b{re.escape(n)}\b", code)]


def dead_names(page: str, exported: set[str]) -> list[str]:
    """The signature names of the page that no module exports (rule 2)."""
    dead, lines, header = [], page.splitlines(), None
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            header = None
            continue
        first = line.strip("|").split("|")[0].strip()
        if i + 1 < len(lines) and lines[i + 1].startswith("|-"):
            header = first
        elif header == "Signature" and (match := SIGNATURE.match(first)) and match.group(1) not in exported:
            dead.append(match.group(1))
    return dead


def link_target_exists(page: Path, target: str) -> bool:
    base = page.parent / target.split("#")[0]
    candidates = (base, Path(f"{base}.mdx"), Path(f"{base}.md"), base / "index.mdx", base / "index.md")
    return any(c.is_file() for c in candidates)


def page_findings(page: Path, root: Path) -> list[str]:
    """The findings of rules 3, 4 and 5 for one page."""
    rel = page.relative_to(root).as_posix()
    text = page.read_text(encoding="utf-8")
    findings = []
    front = text.split("\n---", 1)[0] if text.startswith("---\n") else ""
    if not re.search(r"^title:\s*\S", front, re.MULTILINE):
        findings.append(f"{rel}:1: the page has no front matter with title")
    for number, line in enumerate(prose(text).splitlines(), 1):
        findings += [
            f"{rel}:{number}: the link {target} goes to no page file"
            for target in LINK.findall(line)
            if not target.startswith(("http:", "https:", "mailto:", "/", "#")) and not link_target_exists(page, target)
        ]
        findings += [f'{rel}:{number}: use "system", not "{m.group()}"' for word in WORDS for m in word.finditer(line)]
    return findings


def check(root: Path = ROOT) -> list[str]:
    """Each finding of the default mode."""
    exported = [n for f in EXPORT_FILES for n in exported_names(root / f)]
    api_page = (root / API_PAGE).read_text(encoding="utf-8")
    findings = [f"{API_PAGE}: the page does not name the exported name {n}" for n in missing_names(api_page, exported)]
    findings += [f"{API_PAGE}: the signature {n}() names no exported name" for n in dead_names(api_page, set(exported))]
    pages = sorted(p for d in PAGE_DIRS for p in (root / d).rglob("*.mdx"))
    for page in pages:
        findings += page_findings(page, root)
    return findings


def staged_reminder(paths: list[str]) -> str | None:
    """The reminder line for the staged paths, or None."""
    api = [p for p in paths if any(fnmatch(p, pattern) for pattern in PUBLIC_API_FILES)]
    if not api or any(p.startswith(f"{DOCS}/") for p in paths):
        return None
    return (
        f"docs site: the commit changes {', '.join(api)} and no file under {DOCS}/."
        f" If a page states a changed fact, load the skill update-docs-site ({SKILL})."
    )


def staged_files(root: Path) -> list[str]:
    exe = shutil.which("git")
    if exe is None:
        raise OSError("git is not on the PATH")
    out = subprocess.run([exe, "-C", str(root), "diff", "--cached", "--name-only", "-z"], capture_output=True, check=True)  # noqa: S603
    return [n for n in out.stdout.decode("utf-8").split("\0") if n]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check that the docs site agrees with the public API.")
    parser.add_argument("--staged", action="store_true", help="print the reminder for the staged files; always exit 0")
    args = parser.parse_args(argv[1:])
    if args.staged:
        try:
            line = staged_reminder(staged_files(Path.cwd()))
        except (OSError, subprocess.CalledProcessError) as error:
            line = f"docs site: the staged files are not available ({error})"
        if line:
            print(line)
        return 0
    findings = check()
    for finding in findings:
        print(finding)
    if findings:
        return 1
    print("docs site: no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
