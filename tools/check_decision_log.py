#!/usr/bin/env python3
"""Check the index and the size limits of the decision log (decision 0026).

Usage::

    python tools/check_decision_log.py [ROOT]

The tool reads ``notes/decisions/README.md`` under ROOT (default: the current directory). It reports:

- an entry file with no index row, and an index row with no entry file;
- a row in the wrong index table for its status;
- a file over its size limit.

Sizes are counted in characters after CRLF is changed to LF. About 4 characters make one token.
Entries up to ``LAST_UNLIMITED_ENTRY`` keep their length, because the body of an old entry does not
change. Standard library only.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

LOG_DIR = Path("notes") / "decisions"

INDEX_LIMIT = 24_000
ENTRY_LIMIT = 6_000
READ_PATH_LIMIT = 220_000
LAST_UNLIMITED_ENTRY = 25

ACTIVE_STATUSES = ("proposed", "accepted", "evidence")
HISTORICAL_STATUSES = ("rejected", "superseded by ", "absorbed into ")

ENTRY_NAME = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
TABLE_HEADING = re.compile(r"^### (Active|Historical)\s*$")
INDEX_ROW = re.compile(
    r"^\| \[(\d{4})\]\(((\d{4})-[a-z0-9-]+\.md)\) \| .+ \| (.+?) \|\s*$"
)


@dataclass(frozen=True)
class IndexRow:
    number: int
    filename: str
    status: str
    table: str
    line: int


def size(path: Path) -> int:
    """Characters in a file, with CRLF counted as one character."""
    return len(path.read_text(encoding="utf-8").replace("\r\n", "\n"))


def index_rows(index: Path) -> list[IndexRow]:
    """The entry rows of the Active and Historical tables, in file order."""
    rows = []
    table = ""
    for number, text in enumerate(
        index.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if text.startswith("## "):
            table = ""
        heading = TABLE_HEADING.match(text)
        if heading:
            table = heading.group(1)
            continue
        row = INDEX_ROW.match(text)
        if row and table:
            rows.append(
                IndexRow(
                    int(row.group(1)), row.group(2), row.group(4).strip(), table, number
                )
            )
    return rows


def entry_files(log_dir: Path) -> dict[str, Path]:
    return {p.name: p for p in sorted(log_dir.glob("*.md")) if ENTRY_NAME.match(p.name)}


def is_active(status: str) -> bool:
    return status.startswith(ACTIVE_STATUSES)


def check(root: Path) -> list[str]:
    log_dir = root / LOG_DIR
    index = log_dir / "README.md"
    rows = index_rows(index)
    files = entry_files(log_dir)
    listed = [r.filename for r in rows]
    errors = [
        f"{name}: {listed.count(name)} index rows, expected 1"
        for name in files
        if listed.count(name) != 1
    ]
    for r in rows:
        if r.filename not in files:
            errors.append(f"README.md:{r.line}: row links to missing file {r.filename}")
        if not r.status.startswith(ACTIVE_STATUSES + HISTORICAL_STATUSES):
            errors.append(f"README.md:{r.line}: unknown status {r.status!r}")
        elif r.table != ("Active" if is_active(r.status) else "Historical"):
            errors.append(
                f"README.md:{r.line}: status {r.status!r} must not be in the {r.table} table"
            )

    if size(index) > INDEX_LIMIT:
        errors.append(f"README.md: {size(index)} characters, limit {INDEX_LIMIT}")
    for name, path in files.items():
        number = int(name[:4])
        if number > LAST_UNLIMITED_ENTRY and size(path) > ENTRY_LIMIT:
            errors.append(f"{name}: {size(path)} characters, limit {ENTRY_LIMIT}")

    read_path = read_path_size(root)
    if read_path > READ_PATH_LIMIT:
        errors.append(
            f"read path (README.md and Active entries): {read_path} characters, limit {READ_PATH_LIMIT}"
        )
    return errors


def read_path_size(root: Path) -> int:
    """Characters in the index and in every Active entry: the part of the log that agents read."""
    log_dir = root / LOG_DIR
    files = entry_files(log_dir)
    rows = index_rows(log_dir / "README.md")
    return size(log_dir / "README.md") + sum(
        size(files[r.filename])
        for r in rows
        if is_active(r.status) and r.filename in files
    )


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    errors = check(root)
    if errors:
        print("\n".join(errors))
        return 1
    used = read_path_size(root)
    print(
        f"decision log: index and limits pass; read path {used} of {READ_PATH_LIMIT} characters"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
