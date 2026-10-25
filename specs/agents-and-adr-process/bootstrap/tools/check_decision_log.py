#!/usr/bin/env python3
"""Check the index, the entry IDs and the size limits of the decision log (decision 0001).

Usage::

    python tools/check_decision_log.py [ROOT]
    python tools/check_decision_log.py --new [ROOT]

The tool reads ``notes/decisions/README.md`` under ROOT (default: the current directory). It reports:

- an entry file with no index row, and an index row with no entry file;
- a file name that starts like an entry but has no valid ID;
- two entry files with one ID, and two index rows with one ID;
- a link ``[XXXX](YYYY-<slug>.md)`` under ``notes/decisions`` where XXXX is not YYYY;
- a ``# XXXX`` heading that is not the ID of its file name;
- a Status cell that is not one of the status forms, or that is in the wrong table;
- a ``superseded by XXXX`` or ``used by XXXX`` that names no decided entry, or that the status line of
  the entry does not link to the file of entry XXXX;
- a Decision cell over its length limit;
- a ``proposed`` row in the Active table with a status date more than 183 days old;
- a file over its size limit.

It prints a warning, but does not fail, when the index, the open work or the read path is at 80% of
its limit or more. The check reads only the files. It does not run git.

An ID has 4 characters from ``ALPHABET``, Crockford base32 in lower case. A new ID starts with a
letter. An all-digit ID belongs only to an entry that had that number before random IDs (decision
0001).

``--new`` prints ``new: XXXX``, a random ID that is not in this tree, in each other worktree or on
each local and remote-tracking branch. Then it prints one line for each entry of this tree whose ID a
different file uses in one of those places. ``keep:`` tells you to keep the ID. ``re-ID:`` tells you
to rename the entry to the ID of a new ``--new`` run. Both sides of a collision get the same verdict:
an entry on ``TARGET_BRANCH`` wins, then an entry on a remote-tracking branch, then the entry whose
first commit has the earlier author date, then the file name that sorts first. An uncommitted file
loses to a committed file. Refs that are merged into ``HEAD``, the upstream and push refs of the
current branch, and local branches under ``backup/`` are not collisions, except on ``TARGET_BRANCH``.
A file whose slug is also the slug of an entry of this tree under a different ID is an old name of
that entry, not a collision. ``--new`` runs 5 git processes for any number of refs, and one more when
it finds a collision. It prints the age of the last ``git fetch``. It exits 1 when it prints a
``re-ID:`` line, and 0 otherwise. Without git, it reads only this tree.

Sizes are counted in characters after CRLF is changed to LF. About 4 characters make one token.
All-digit entries up to ``LAST_UNLIMITED_ENTRY`` keep their length, because the body of an old entry
does not change. An entry with ``renumber from XXXX`` or ``re-ID from XXXX`` keeps the exemption of
XXXX. Standard library and the git CLI only, with no import from another repo (decision 0001).
"""

from __future__ import annotations

import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

LOG_DIR = Path("notes") / "decisions"
OPEN_WORK = "open-work.md"
NOT_ENTRIES = {"README.md", OPEN_WORK}
TARGET_BRANCH = "main"  # Step 3 of the kit guide sets the branch that PRs target.
SKIPPED_BRANCHES = "refs/heads/backup/"

INDEX_LIMIT = 14_000
OPEN_WORK_LIMIT = 20_000
ENTRY_LIMIT = 6_000
READ_PATH_LIMIT = 220_000
LAST_UNLIMITED_ENTRY = 0
WARN_FRACTION = 0.8
DECISION_CELL_LIMIT = 160
DEFER_AFTER_DAYS = 183

LETTERS = "abcdefghjkmnpqrstvwxyz"
ALPHABET = "0123456789" + LETTERS
ID = r"(?:\d{4}|[" + LETTERS + "][" + ALPHABET + r"]{3})"

ABSORBED = r"absorbed into (?:\[[^\]]+\]\([^)\s]+\)|`[^`]+`)"
STATUS_FORMS = {
    "Active": ("proposed", "accepted", "evidence"),
    "Deferred": ("proposed",),
    "Historical": (
        rf"evidence; used by ({ID})",
        "rejected",
        rf"superseded by ({ID})",
        ABSORBED,
    ),
}
NOT_DECIDED = ("proposed", "rejected")

ENTRY_NAME = re.compile(rf"^({ID})-([a-z0-9-]+)\.md$")
ENTRY_LIKE = re.compile(r"^[0-9a-z]{4}-.*\.md$")
TABLE_HEADING = re.compile(r"^### (Active|Deferred|Historical)\s*$")
INDEX_ROW = re.compile(
    rf"^\| \[({ID})\]\((({ID})-[a-z0-9-]+\.md)\) \| (.+) \| (.+?) \|\s*$"
)
STATUS_LINE = re.compile(r"^\*\*Status:\*\*(.*)$", re.MULTILINE)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
ENTRY_LINK = re.compile(
    rf"\[({ID})\]\((?:[^)\s]*/)?(({ID})-[a-z0-9-]+\.md)(?:#[^)\s]*)?\)"
)
HEADING_ID = re.compile(rf"# ({ID})\b")
OLD_ID = re.compile(rf"(?:renumber|re-ID) from ({ID})")


@dataclass(frozen=True)
class IndexRow:
    id: str
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
                    row.group(1),
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


def entry_id(name: str) -> str:
    return name[:4]


def slug(name: str) -> str:
    return name[5:-3]


def status_match(status: str, table: str) -> re.Match[str] | None:
    """The match of `status` against a status form of `table`, or None."""
    for form in STATUS_FORMS[table]:
        match = re.fullmatch(form, status)
        if match:
            return match
    return None


def status_errors(r: IndexRow, by_id: dict[str, IndexRow]) -> list[str]:
    where = f"README.md:{r.line}"
    match = status_match(r.status, r.table)
    if match is None:
        tables = [t for t in STATUS_FORMS if status_match(r.status, t)]
        if not tables:
            return [f"{where}: unknown status {r.status!r}"]
        return [f"{where}: status {r.status!r} must not be in the {r.table} table"]
    errors = []
    if match.groups():
        target = match.group(1)
        named = by_id.get(target)
        if named is None or target == r.id:
            errors.append(f"{where}: status {r.status!r} names no other indexed entry")
        elif named.status.startswith(NOT_DECIDED):
            errors.append(f"{where}: status {r.status!r} names an entry that is {named.status!r}")
    if len(r.decision) > DECISION_CELL_LIMIT:
        errors.append(
            f"{where}: Decision cell has {len(r.decision)} characters, limit {DECISION_CELL_LIMIT}"
        )
    return errors


def status_link_errors(r: IndexRow, by_id: dict[str, IndexRow], path: Path) -> list[str]:
    """`superseded by XXXX` and `used by XXXX` must also be links to entry XXXX in the status line."""
    match = status_match(r.status, r.table)
    if match is None or not match.groups():
        return []
    named = by_id.get(match.group(1))
    if named is None or named.id == r.id:
        return []
    kind = "superseded by" if r.status.startswith("superseded by") else "used by"
    link = re.compile(
        rf"{kind} \[{named.id}\]\({re.escape(named.filename)}(?:#[^)\s]*)?\)"
    )
    line = STATUS_LINE.search(path.read_text(encoding="utf-8"))
    if line and link.search(line.group(1)):
        return []
    return [
        f"{r.filename}: the status line does not link {kind} {named.id} to {named.filename}"
    ]


def id_errors(log_dir: Path, rows: list[IndexRow], files: dict[str, Path]) -> list[str]:
    """Each ID has one file and one index row. Link texts and headings match the file names."""
    errors = [
        f"{p.name}: the file name starts like an entry, but {p.name[:4]!r} is not a valid ID"
        for p in sorted(log_dir.glob("*.md"))
        if ENTRY_LIKE.match(p.name) and not ENTRY_NAME.match(p.name) and p.name not in NOT_ENTRIES
    ]
    per_id = Counter(entry_id(name) for name in files)
    for found, count in sorted(per_id.items()):
        if count > 1:
            names = ", ".join(name for name in files if entry_id(name) == found)
            errors.append(f"entry ID {found} has {count} files: {names}")
    first_row: dict[str, IndexRow] = {}
    for r in rows:
        if r.id in first_row:
            errors.append(
                f"README.md:{r.line}: ID {r.id} is also in README.md:{first_row[r.id].line}"
            )
        else:
            first_row[r.id] = r
    for path in sorted(log_dir.rglob("*.md")):
        label = path.relative_to(log_dir).as_posix()
        for line_number, text in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            errors.extend(
                f"{label}:{line_number}: link text {link.group(1)} does not match {link.group(2)}"
                for link in ENTRY_LINK.finditer(text)
                if link.group(1) != link.group(3)
            )
    for name, path in files.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        heading = HEADING_ID.match(lines[0]) if lines else None
        if heading and heading.group(1) != entry_id(name):
            errors.append(
                f"{name}: heading ID {heading.group(1)} does not match the file name"
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


def unlimited(name: str, path: Path) -> bool:
    """True when the file ID, or an old ID of the entry, is all digits and at most LAST_UNLIMITED_ENTRY."""
    old = OLD_ID.findall(path.read_text(encoding="utf-8"))
    return any(i.isdigit() and int(i) <= LAST_UNLIMITED_ENTRY for i in [entry_id(name), *old])


def sizes(root: Path) -> list[tuple[str, int, int]]:
    """(label, characters, limit) for each file and total that has a limit."""
    log_dir = root / LOG_DIR
    found = [("README.md", size(log_dir / "README.md"), INDEX_LIMIT)]
    if (log_dir / OPEN_WORK).exists():
        found.append((OPEN_WORK, size(log_dir / OPEN_WORK), OPEN_WORK_LIMIT))
    for name, path in entry_files(log_dir).items():
        if not unlimited(name, path):
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
    by_id = {r.id: r for r in rows}
    listed = [r.filename for r in rows]
    errors = [
        f"{name}: {listed.count(name)} index rows, expected 1"
        for name in files
        if listed.count(name) != 1
    ]
    errors.extend(id_errors(log_dir, rows, files))
    for r in rows:
        if r.filename not in files:
            errors.append(f"README.md:{r.line}: row links to missing file {r.filename}")
            continue
        errors.extend(status_errors(r, by_id))
        errors.extend(status_link_errors(r, by_id, files[r.filename]))
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


# --new: entry IDs on other branches and worktrees. Only main() calls it, never check().


@dataclass
class Sources:
    """The entry file names of each other place, by a label: a ref name or `worktree <path>`."""

    found: dict[str, set[str]] = field(default_factory=dict)
    target: set[str] = field(default_factory=set)
    quiet: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


def git(root: Path, *args: str, stdin: bytes | None = None) -> bytes | None:
    """The stdout bytes of one git process, or None when git is missing or fails."""
    exe = shutil.which("git")
    if exe is None:
        return None
    try:
        done = subprocess.run(  # noqa: S603
            [exe, *args],
            cwd=root,
            input=stdin,
            capture_output=True,
            env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        )
    except OSError:
        return None
    return done.stdout if done.returncode == 0 else None


def decoded(data: bytes | None) -> str:
    return (data or b"").decode("utf-8", "replace")


def entry_names(folder: Path) -> set[str]:
    return {p.name for p in folder.glob("*.md") if ENTRY_NAME.match(p.name)} if folder.is_dir() else set()


def tree_entries(data: bytes, count: int) -> list[set[str] | None]:
    """The entry file names in each of `count` objects of `git cat-file --batch` output.

    An object that is missing or that is not a tree gives None. SHA-1 and SHA-256 both work.
    """
    found: list[set[str] | None] = []
    i = 0
    for _ in range(count):
        end = data.index(b"\n", i)
        head, i = data[i:end].split(), end + 1
        if len(head) != 3:
            found.append(None)
            continue
        length = int(head[2])
        body, i = data[i : i + length], i + length + 1
        if head[1] != b"tree":
            found.append(None)
            continue
        names, k, width = set(), 0, len(head[0]) // 2
        while k < len(body):
            space, nul = body.index(b" ", k), body.index(b"\0", k)
            name = body[space + 1 : nul].decode("utf-8", "surrogateescape")
            if body[k:space] != b"40000" and ENTRY_NAME.match(name):
                names.add(name)
            k = nul + 1 + width
        found.append(names)
    return found


def fetch_note(root: Path, git_dirs: list[str], has_remote_refs: bool) -> list[str]:
    """The age of the last `git fetch`, from the time of FETCH_HEAD."""
    times = [
        (root / d / "FETCH_HEAD").stat().st_mtime
        for d in git_dirs
        if (root / d / "FETCH_HEAD").is_file()
    ]
    if not times:
        return ["no git fetch is recorded: run `git fetch`, then run --new again"] if has_remote_refs else []
    hours = (time.time() - max(times)) / 3600
    age = f"{hours * 60:.0f} minutes" if hours < 2 else f"{hours:.0f} hours"
    note = f"the last git fetch was {age} ago"
    return [note + ("" if hours < 1 else ": run `git fetch`, then run --new again")]


def git_sources(root: Path) -> Sources:
    """Entry names in the other worktrees and on each branch, from 5 git processes."""
    sources = Sources()
    info = git(root, "rev-parse", "--git-dir", "--git-common-dir", "--show-prefix")
    if info is None:
        sources.notes.append("git is missing, or ROOT is not in a git repo: only this tree is read")
        return sources
    git_dir, common_dir, prefix = (decoded(info).split("\n") + ["", "", ""])[:3]
    me = root.resolve()
    for line in decoded(git(root, "worktree", "list", "--porcelain")).splitlines():
        if not line.startswith("worktree "):
            continue
        path = (Path(line[len("worktree ") :]) / prefix).resolve()
        if path == me:
            continue
        try:
            label = os.path.relpath(path, me)
        except ValueError:
            label = str(path)
        sources.found[f"worktree {Path(label).as_posix()}"] = entry_names(path / LOG_DIR)
    form = "--format=%(objectname)%09%(refname)%09%(HEAD)%09%(upstream)%09%(push)"
    refs = [
        line.split("\t")
        for line in decoded(git(root, "for-each-ref", form, "refs/heads", "refs/remotes")).splitlines()
    ]
    refs = [
        r for r in refs
        if len(r) == 5
        and not (r[1].startswith("refs/remotes/") and r[1].endswith("/HEAD"))
        and not r[1].startswith(SKIPPED_BRANCHES)
    ]
    merged = set(
        decoded(
            git(root, "for-each-ref", "--merged=HEAD", "--format=%(refname)", "refs/heads", "refs/remotes")
        ).split()
    )
    commits = sorted({r[0] for r in refs})
    if commits:
        batch = git(
            root,
            "cat-file",
            "--batch",
            stdin="".join(f"{c}:./{LOG_DIR.as_posix()}\n" for c in commits).encode(),
        )
        entries = tree_entries(batch, len(commits)) if batch else [None] * len(commits)
        trees = dict(zip(commits, entries, strict=True))
        for oid, ref, *_ in refs:
            if trees.get(oid) is not None:
                sources.found[ref] = trees[oid]
    sources.target = {
        ref
        for ref in sources.found
        if ref == f"refs/heads/{TARGET_BRANCH}"
        or (ref.startswith("refs/remotes/") and ref.endswith(f"/{TARGET_BRANCH}"))
    }
    own = {name for r in refs if r[2] == "*" for name in (r[3], r[4]) if name}
    sources.quiet = (own | merged) - sources.target
    sources.notes.extend(
        fetch_note(root, [git_dir, common_dir], any(r[1].startswith("refs/remotes/") for r in refs))
    )
    return sources


def short(label: str) -> str:
    return label.removeprefix("refs/heads/").removeprefix("refs/remotes/")


def new_id(used: set[str], draw: Callable[[], str] | None = None) -> str:
    """A random ID that is not in `used`. The first character is a letter."""

    def random_id() -> str:
        return secrets.choice(LETTERS) + "".join(secrets.choice(ALPHABET) for _ in range(3))

    while True:
        candidate = (draw or random_id)()
        if candidate not in used:
            return candidate


def first_commits(root: Path, names: set[str]) -> dict[str, int]:
    """The author time of the first commit that adds each file of `names`, on any branch: 1 git process."""
    if not names:
        return {}
    paths = [f"{LOG_DIR.as_posix()}/{name}" for name in sorted(names)]
    out = decoded(
        git(
            root, "log", "--branches", "--remotes", "HEAD", "--no-renames", "--diff-filter=A",
            "--name-only", "--format=@%at", "--", *paths,
        )
    )
    times: dict[str, int] = {}
    when = 0
    for line in out.splitlines():
        if line.startswith("@"):
            when = int(line[1:])
        elif line:
            name = line.rsplit("/", 1)[-1]
            times[name] = min(times.get(name, when), when)
    return times


def new_lines(root: Path, draw: Callable[[], str] | None = None) -> list[str]:
    """The `new:` line, a `keep:` or `re-ID:` line for each collision, and the notes."""
    mine = entry_names(root / LOG_DIR)
    sources = git_sources(root)
    used = {entry_id(n) for n in mine}.union(
        *({entry_id(n) for n in names} for names in sources.found.values())
    )
    lines = [f"new: {new_id(used, draw)}"]
    on_target = set().union(*(sources.found[s] for s in sources.target))
    on_remote = set().union(
        *(names for s, names in sources.found.items() if s.startswith("refs/remotes/"))
    )
    my_slugs = {slug(n): n for n in mine}
    collisions: dict[str, dict[str, list[str]]] = {}
    for name in sorted(mine):
        others: dict[str, list[str]] = {}
        for label, names in sources.found.items():
            if label in sources.quiet:
                continue
            for other in names:
                renamed = my_slugs.get(slug(other), other) != other
                if entry_id(other) == entry_id(name) and other != name and not renamed:
                    others.setdefault(other, []).append(short(label))
        if others:
            collisions[name] = others
    if collisions:
        times = first_commits(root, set(collisions).union(*collisions.values()))

        def rank(name: str) -> tuple[bool, bool, bool, int]:
            when = times.get(name)
            return (name in on_target, name in on_remote, when is not None, -(when or 0))

        for name, others in collisions.items():
            change = any((rank(other), name) > (rank(name), other) for other in others)
            uses = []
            for other, where in sorted(others.items()):
                places = ", ".join(sorted(where)[:3]) + (f" and {len(where) - 3} more" if len(where) > 3 else "")
                uses.append(f"{other} also uses {entry_id(name)} (on {places})")
            lines.append(f"{'re-ID' if change else 'keep'}: {name}; " + "; ".join(uses))
    return lines + [f"note: {note}" for note in sources.notes]


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args[:1] == ["--new"] and len(args) <= 2:
        lines = new_lines(Path(args[1]).resolve() if len(args) == 2 else Path.cwd())
        print("\n".join(lines))
        return 1 if any(line.startswith("re-ID:") for line in lines) else 0
    if len(args) > 1 or (args and args[0].startswith("-")):
        print(__doc__)
        return 2
    root = Path(args[0]).resolve() if args else Path.cwd()
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
