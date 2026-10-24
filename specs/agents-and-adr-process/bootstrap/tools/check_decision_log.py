#!/usr/bin/env python3
"""Check the index and the size limits of the decision log (decision 0001).

Usage::

    python tools/check_decision_log.py [ROOT]

The tool reads ``notes/decisions/README.md`` under ROOT (default: the current directory). It reports:

- an entry file with no index row, and an index row with no entry file;
- a Status cell that is not one of the status forms, or that is in the wrong table;
- a ``superseded by NNNN`` or ``used by NNNN`` that names no decided entry;
- a Decision cell over its length limit;
- a ``proposed`` row in the Active table with a status date more than 183 days old;
- a file over its size limit.

It prints a warning, but does not fail, when the index, the open work or the read path is at 80% of
its limit or more.

Sizes are counted in characters after CRLF is changed to LF. About 4 characters make one token.
Entries up to ``LAST_UNLIMITED_ENTRY`` keep their length, because the body of an old entry does not
change. Standard library only, with no import from another repo (decision 0001).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

LOG_DIR = Path("notes") / "decisions"
OPEN_WORK = "open-work.md"

INDEX_LIMIT = 14_000
OPEN_WORK_LIMIT = 20_000
ENTRY_LIMIT = 6_000
READ_PATH_LIMIT = 220_000
LAST_UNLIMITED_ENTRY = 0
WARN_FRACTION = 0.8
DECISION_CELL_LIMIT = 160
DEFER_AFTER_DAYS = 183

ABSORBED = r"absorbed into (?:\[[^\]]+\]\([^)\s]+\)|`[^`]+`)"
STATUS_FORMS = {
    "Active": ("proposed", "accepted", "evidence"),
    "Deferred": ("proposed",),
    "Historical": (
        r"evidence; used by (\d{4})",
        "rejected",
        r"superseded by (\d{4})",
        ABSORBED,
    ),
}
NOT_DECIDED = ("proposed", "rejected")

ENTRY_NAME = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
TABLE_HEADING = re.compile(r"^### (Active|Deferred|Historical)\s*$")
INDEX_ROW = re.compile(
    r"^\| \[(\d{4})\]\(((\d{4})-[a-z0-9-]+\.md)\) \| (.+) \| (.+?) \|\s*$"
)
STATUS_LINE = re.compile(r"^\*\*Status:\*\*(.*)$", re.MULTILINE)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class IndexRow:
    number: int
    filename: str
    decision: str
    status: str
    table: str
    line: int


def size(path: Path) -> int:
    """Characters in a file, with CRLF counted as one character."""
    return len(path.read_text(encoding="utf-8").replace("\r\n", "\n"))


def index_rows(index: Path) -> list[IndexRow]:
    """The entry rows of the Active, Deferred and Historical tables, in file order."""
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
                    int(row.group(1)),
                    row.group(2),
                    row.group(4).strip(),
                    row.group(5).strip(),
                    table,
                    number,
                )
            )
    return rows


def entry_files(log_dir: Path) -> dict[str, Path]:
    return {p.name: p for p in sorted(log_dir.glob("*.md")) if ENTRY_NAME.match(p.name)}


def status_match(status: str, table: str) -> re.Match[str] | None:
    """The match of `status` against a status form of `table`, or None."""
    for form in STATUS_FORMS[table]:
        match = re.fullmatch(form, status)
        if match:
            return match
    return None


def status_errors(r: IndexRow, by_number: dict[int, IndexRow]) -> list[str]:
    where = f"README.md:{r.line}"
    match = status_match(r.status, r.table)
    if match is None:
        tables = [t for t in STATUS_FORMS if status_match(r.status, t)]
        if not tables:
            return [f"{where}: unknown status {r.status!r}"]
        return [f"{where}: status {r.status!r} must not be in the {r.table} table"]
    errors = []
    if match.groups():
        target = int(match.group(1))
        named = by_number.get(target)
        if named is None or target == r.number:
            errors.append(f"{where}: status {r.status!r} names no other indexed entry")
        elif named.status.startswith(NOT_DECIDED):
            errors.append(f"{where}: status {r.status!r} names an entry that is {named.status!r}")
    if len(r.decision) > DECISION_CELL_LIMIT:
        errors.append(
            f"{where}: Decision cell has {len(r.decision)} characters, limit {DECISION_CELL_LIMIT}"
        )
    return errors


def deferral_errors(r: IndexRow, path: Path, today: date) -> list[str]:
    """A proposed row in Active must have a status date at most DEFER_AFTER_DAYS old."""
    if r.table != "Active" or r.status != "proposed":
        return []
    line = STATUS_LINE.search(path.read_text(encoding="utf-8"))
    dates = DATE.findall(line.group(1)) if line else []
    if not dates:
        return [f"{r.filename}: the status line has no date"]
    latest = max(date.fromisoformat(d) for d in dates)
    if (today - latest).days > DEFER_AFTER_DAYS:
        return [
            f"README.md:{r.line}: proposed since {latest}, more than {DEFER_AFTER_DAYS} days: "
            "move the row to the Deferred table"
        ]
    return []


def sizes(root: Path) -> list[tuple[str, int, int]]:
    """(label, characters, limit) for each file and total that has a limit."""
    log_dir = root / LOG_DIR
    found = [("README.md", size(log_dir / "README.md"), INDEX_LIMIT)]
    if (log_dir / OPEN_WORK).exists():
        found.append((OPEN_WORK, size(log_dir / OPEN_WORK), OPEN_WORK_LIMIT))
    for name, path in entry_files(log_dir).items():
        if int(name[:4]) > LAST_UNLIMITED_ENTRY:
            found.append((name, size(path), ENTRY_LIMIT))
    found.append(
        ("read path (README.md, open-work.md and Active entries)", read_path_size(root), READ_PATH_LIMIT)
    )
    return found


def check(root: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    log_dir = root / LOG_DIR
    index = log_dir / "README.md"
    rows = index_rows(index)
    files = entry_files(log_dir)
    by_number = {r.number: r for r in rows}
    listed = [r.filename for r in rows]
    errors = [
        f"{name}: {listed.count(name)} index rows, expected 1"
        for name in files
        if listed.count(name) != 1
    ]
    for r in rows:
        if r.filename not in files:
            errors.append(f"README.md:{r.line}: row links to missing file {r.filename}")
            continue
        errors.extend(status_errors(r, by_number))
        errors.extend(deferral_errors(r, files[r.filename], today))
    errors.extend(
        f"{label}: {used} characters, limit {limit}"
        for label, used, limit in sizes(root)
        if used > limit
    )
    return errors


def warnings(root: Path) -> list[str]:
    """Shared sizes at WARN_FRACTION of their limit or more, but not over it.

    Entries do not warn: an entry is written once, so a warning cannot make it shorter.
    """
    return [
        f"{label}: {used} characters, {used / limit:.0%} of the limit {limit}"
        for label, used, limit in sizes(root)
        if WARN_FRACTION * limit <= used <= limit and not ENTRY_NAME.match(label)
    ]


def read_path_size(root: Path) -> int:
    """Characters in the index, the open work and every Active entry: the part that agents read."""
    log_dir = root / LOG_DIR
    files = entry_files(log_dir)
    rows = index_rows(log_dir / "README.md")
    open_work = log_dir / OPEN_WORK
    return (
        size(log_dir / "README.md")
        + (size(open_work) if open_work.exists() else 0)
        + sum(
            size(files[r.filename])
            for r in rows
            if r.table == "Active" and r.filename in files
        )
    )


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    for warning in warnings(root):
        print(f"warning: {warning}")
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
