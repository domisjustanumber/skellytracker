#!/usr/bin/env python3
"""Write or check the copied files of the bootstrap kit (decision 0031).

Usage::

    python tools/sync_bootstrap_kit.py --check   # fail when a copy differs from its live file
    python tools/sync_bootstrap_kit.py --write   # write each copy again from its live file

The kit in ``specs/agents-and-adr-process/bootstrap/`` holds copies of the tools and configs of this
repo, for a new repo to copy. Each copy is its live file with a short list of exact text edits that
remove the parts that belong only to this repo. A change to a live file must be copied to the kit:
run ``--write`` and commit both files. The doc tests run ``--check``. Standard library only.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

KIT = Path("specs") / "agents-and-adr-process" / "bootstrap"


@dataclass(frozen=True)
class Copy:
    target: str
    source: str
    edits: tuple[tuple[str, str], ...] = ()


DECISION_0001 = "(decision 0001)"

COPIES = (
    Copy(
        "tools/check_decision_log.py",
        "tools/check_decision_log.py",
        (
            ("(decisions z934 and gtwq).", f"{DECISION_0001}."),
            ("random IDs (decision\ngtwq).", "random IDs (decision\n0001)."),
            ("another repo (decision gtwq).\n", f"another repo {DECISION_0001}.\n"),
            ("INDEX_LIMIT = 18_000\n", "INDEX_LIMIT = 14_000\n"),
            ("READ_PATH_LIMIT = 160_000\n", "READ_PATH_LIMIT = 220_000\n"),
            (
                'TARGET_BRANCH = "development"\n',
                'TARGET_BRANCH = "main"  # Step 3 of the kit guide sets the branch that PRs target.\n',
            ),
            ("LAST_UNLIMITED_ENTRY = 25\n", "LAST_UNLIMITED_ENTRY = 0\n"),
        ),
    ),
    Copy(
        "tools/tests/test_decision_log.py",
        "tools/tests/test_decision_log.py",
        (("(decision z934).", f"{DECISION_0001}."),),
    ),
    Copy(
        "tools/check_private_data.py",
        "tools/check_private_data.py",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            (
                'ALLOWED_EMAILS = {"info@freemocap.org", "noreply@anthropic.com"}\n',
                "# Add the public contact address of the project here, for example the one in pyproject.toml.\n"
                'ALLOWED_EMAILS = {"noreply@anthropic.com"}\n',
            ),
        ),
    ),
    Copy(
        "tools/tests/test_private_data.py",
        "tools/tests/test_private_data.py",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            ('    assert kinds("info" + at + "freemocap.org") == []\n', ""),
        ),
    ),
    Copy(
        "tools/check_links.py",
        "tools/check_links.py",
        (("(decision 0032).", f"{DECISION_0001}."),),
    ),
    Copy("tools/tests/test_links.py", "tools/tests/test_links.py"),
    Copy("tools/tests/conftest.py", "tools/tests/conftest.py"),
    Copy(
        ".pre-commit-config.yaml",
        ".pre-commit-config.yaml",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            ("# Decision gtwq: an entry ID", "# An entry ID"),
        ),
    ),
    Copy(
        ".gitleaks.toml",
        ".gitleaks.toml",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            (
                "The allowlists below hold only\n# reviewed false positives. Give the reason for each one.\n",
                "Add an [[allowlists]] table only\n# for a reviewed false positive, and give its reason.\n",
            ),
            (
                "\n[[allowlists]]\n"
                'description = "Model registry keys (pose_key: \\"rtmw-...\\") in the Rust port, not credentials"\n'
                'commits = ["e0af6f3bbe4f602c7ed1cf6ac07f36f6ea5415ea"]\n',
                "",
            ),
        ),
    ),
    Copy(
        ".github/workflows/secrets.yml",
        ".github/workflows/secrets.yml",
        (("    branches: [main, development]\n", "    branches: [main]\n"),),
    ),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def expected(root: Path, copy: Copy) -> str:
    """The text of the copy: the live file with the edits applied."""
    text = read(root / copy.source)
    for old, new in copy.edits:
        if text.count(old) != 1:
            raise SystemExit(
                f"{copy.source}: an edit for the bootstrap kit matches {text.count(old)} times, expected 1:\n{old}"
            )
        text = text.replace(old, new)
    return text


def check(root: Path) -> list[str]:
    errors = []
    for copy in COPIES:
        path = root / KIT / copy.target
        if not path.exists():
            errors.append(f"{KIT.as_posix()}/{copy.target}: missing; run --write")
        elif read(path) != expected(root, copy):
            errors.append(
                f"{KIT.as_posix()}/{copy.target}: differs from {copy.source}; run --write"
            )
    return errors


def write(root: Path) -> None:
    for copy in COPIES:
        path = root / KIT / copy.target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected(root, copy), encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if argv[1:] == ["--write"]:
        write(root)
        print(f"bootstrap kit: wrote {len(COPIES)} copies")
        return 0
    if argv[1:] == ["--check"]:
        errors = check(root)
        print("\n".join(errors) if errors else f"bootstrap kit: {len(COPIES)} copies match")
        return 1 if errors else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
