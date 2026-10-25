"""The decision log keeps its index and its size limits (decision 0035)."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

import check_decision_log as cdl

REPO_ROOT = Path(cdl.__file__).resolve().parents[1]

INDEX = """# Decision log

## Index

### Active

| # | Decision | Status |
|---|----------|--------|
{active}

### Deferred

| # | Decision | Status |
|---|----------|--------|
{deferred}

### Historical

| # | Decision | Status |
|---|----------|--------|
{historical}

## Open work
"""

TODAY = date(2026, 10, 24)


def make_log(
    tmp_path: Path,
    active: str = "",
    historical: str = "",
    entries: dict[str, str] | None = None,
    deferred: str = "",
) -> Path:
    log_dir = tmp_path / cdl.LOG_DIR
    log_dir.mkdir(parents=True)
    (log_dir / "README.md").write_text(
        INDEX.format(active=active, deferred=deferred, historical=historical),
        encoding="utf-8",
    )
    for name, text in (entries or {}).items():
        (log_dir / name).write_text(text, encoding="utf-8")
    return tmp_path


def row(number: int | str, status: str, name: str = "x", decision: str = "Title") -> str:
    i = f"{number:04d}" if isinstance(number, int) else number
    return f"| [{i}]({i}-{name}.md) | {decision} | {status} |"


def proposed_entry(day: str, number: int = 1) -> str:
    return f"# {number:04d}\n\n**Status:** proposed, {day} (user).\n"


def test_repository_log_passes() -> None:
    assert cdl.check(REPO_ROOT) == []


def test_matching_index_passes(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "accepted"),
        historical="\n".join(
            [
                row(2, "absorbed into `AGENTS.md`", "y"),
                row(3, "absorbed into [`AGENTS.md#5`](../../AGENTS.md#5)", "z"),
            ]
        ),
        entries={"0001-x.md": "# 0001\n", "0002-y.md": "# 0002\n", "0003-z.md": ""},
    )
    assert cdl.check(root, TODAY) == []


def test_entry_without_row_and_row_without_entry_are_reported(tmp_path: Path) -> None:
    root = make_log(
        tmp_path, active=row(1, "accepted"), entries={"0002-y.md": "# 0002\n"}
    )
    errors = cdl.check(root, TODAY)
    assert "0002-y.md: 0 index rows, expected 1" in errors
    assert any("row links to missing file 0001-x.md" in e for e in errors)


def test_status_must_match_its_table(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "superseded by 0002"),
        historical=row(2, "proposed", "y"),
        entries={"0001-x.md": "", "0002-y.md": ""},
    )
    errors = cdl.check(root, TODAY)
    assert any(
        "'superseded by 0002' must not be in the Active table" in e for e in errors
    )
    assert any("'proposed' must not be in the Historical table" in e for e in errors)


def test_unknown_status_is_reported(tmp_path: Path) -> None:
    root = make_log(tmp_path, active=row(1, "maybe"), entries={"0001-x.md": ""})
    assert any("unknown status 'maybe'" in e for e in cdl.check(root, TODAY))


def test_free_text_after_a_status_is_reported(tmp_path: Path) -> None:
    root = make_log(
        tmp_path, active=row(1, "accepted; extends 0002"), entries={"0001-x.md": ""}
    )
    assert any(
        "unknown status 'accepted; extends 0002'" in e for e in cdl.check(root, TODAY)
    )


def test_superseded_by_must_name_a_decided_entry(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(2, "proposed", "y"),
        historical="\n".join([row(1, "superseded by 0002"), row(3, "superseded by 0009", "z")]),
        entries={
            "0001-x.md": "",
            "0002-y.md": proposed_entry("2026-10-01", 2),
            "0003-z.md": "",
        },
    )
    errors = cdl.check(root, TODAY)
    assert any("'superseded by 0002' names an entry that is 'proposed'" in e for e in errors)
    assert any("'superseded by 0009' names no other indexed entry" in e for e in errors)


def test_used_evidence_is_historical(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(1, "accepted"), row(3, "evidence; used by 0001", "z")]),
        historical=row(2, "evidence; used by 0001", "y"),
        entries={
            "0001-x.md": "",
            "0002-y.md": "**Status:** evidence; used by [0001](0001-x.md), 2026-10-24 (#1).\n",
            "0003-z.md": "",
        },
    )
    assert cdl.check(root, TODAY) == [
        "README.md:10: status 'evidence; used by 0001' must not be in the Active table"
    ]


def test_long_decision_cell_is_reported(tmp_path: Path) -> None:
    long = "d" * (cdl.DECISION_CELL_LIMIT + 1)
    root = make_log(
        tmp_path, active=row(1, "accepted", decision=long), entries={"0001-x.md": ""}
    )
    assert any("Decision cell has 161 characters" in e for e in cdl.check(root, TODAY))


def test_old_proposal_must_move_to_deferred(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(1, "proposed"), row(2, "proposed", "y")]),
        entries={
            "0001-x.md": proposed_entry("2026-04-20"),
            "0002-y.md": "**Status:** proposed, 2026-01-01 (gap record); completed 2026-10-01 (proposal).\n",
        },
    )
    errors = cdl.check(root, TODAY)
    assert errors == [
        "README.md:9: proposed since 2026-04-20, more than 183 days: move the row to the Deferred table"
    ]


def test_deferred_entries_are_not_in_the_read_path(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        deferred=row(1, "proposed"),
        entries={"0001-x.md": proposed_entry("2025-01-01") + "a" * 500},
    )
    assert cdl.check(root, TODAY) == []
    assert cdl.read_path_size(root) == cdl.size(root / cdl.LOG_DIR / "README.md")


def test_new_entry_over_limit_is_reported_and_old_entry_is_not(tmp_path: Path) -> None:
    big = "x" * (cdl.ENTRY_LIMIT + 1)
    old = cdl.LAST_UNLIMITED_ENTRY
    new = old + 1
    root = make_log(
        tmp_path,
        active="\n".join([row(old, "accepted"), row(new, "accepted", "y")]),
        entries={f"{old:04d}-x.md": big, f"{new:04d}-y.md": big},
    )
    errors = cdl.check(root, TODAY)
    assert (
        f"{new:04d}-y.md: {cdl.ENTRY_LIMIT + 1} characters, limit {cdl.ENTRY_LIMIT}"
        in errors
    )
    assert not any(e.startswith(f"{old:04d}-x.md") for e in errors)


def test_open_work_at_80_percent_warns_and_passes(tmp_path: Path) -> None:
    near = "w" * int(cdl.OPEN_WORK_LIMIT * 0.9)
    root = make_log(tmp_path, entries={cdl.OPEN_WORK: near})
    assert cdl.check(root, TODAY) == []
    assert (
        f"{cdl.OPEN_WORK}: {len(near)} characters, 90% of the limit {cdl.OPEN_WORK_LIMIT}"
        in cdl.warnings(root)
    )


def test_entry_near_its_limit_does_not_warn(tmp_path: Path) -> None:
    new = cdl.LAST_UNLIMITED_ENTRY + 1
    near = "x" * int(cdl.ENTRY_LIMIT * 0.9)
    root = make_log(
        tmp_path, active=row(new, "accepted"), entries={f"{new:04d}-x.md": near}
    )
    assert cdl.check(root, TODAY) == []
    assert not any(w.startswith(f"{new:04d}-x.md") for w in cdl.warnings(root))


def test_historical_entries_are_not_in_the_read_path(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "accepted"),
        historical=row(2, "rejected", "y"),
        entries={"0001-x.md": "a" * 100, "0002-y.md": "b" * 1000},
    )
    index_size = cdl.size(root / cdl.LOG_DIR / "README.md")
    assert cdl.read_path_size(root) == index_size + 100


def test_open_work_is_in_the_read_path_and_has_a_limit(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        entries={cdl.OPEN_WORK: "w" * (cdl.OPEN_WORK_LIMIT + 1)},
    )
    index_size = cdl.size(root / cdl.LOG_DIR / "README.md")
    assert cdl.read_path_size(root) == index_size + cdl.OPEN_WORK_LIMIT + 1
    assert (
        f"{cdl.OPEN_WORK}: {cdl.OPEN_WORK_LIMIT + 1} characters, limit {cdl.OPEN_WORK_LIMIT}"
        in cdl.check(root, TODAY)
    )


def test_crlf_counts_as_one_character(tmp_path: Path) -> None:
    path = tmp_path / "a.md"
    path.write_bytes(b"a\r\nb\r\n")
    assert cdl.size(path) == 4


def test_two_files_with_one_number_are_reported(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(32, "accepted", "a"), row(32, "accepted", "b")]),
        entries={"0032-a.md": "# 0032\n", "0032-b.md": "# 0032\n"},
    )
    errors = cdl.check(root, TODAY)
    assert "entry ID 0032 has 2 files: 0032-a.md, 0032-b.md" in errors
    assert "README.md:10: ID 0032 is also in README.md:9" in errors


def test_link_text_must_match_file_number(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="| [0032](0033-x.md) | T | accepted |",
        entries={"0033-x.md": "# 0033\n"},
    )
    assert "README.md:9: link text 0032 does not match 0033-x.md" in cdl.check(root, TODAY)


def test_link_text_in_entry_must_match_file(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(1, "accepted"), row(3, "accepted", "z")]),
        entries={
            "0001-x.md": "# 0001\n\nSee [0002](0003-z.md) and [0003](0003-z.md#decision).\n",
            "0003-z.md": "",
        },
    )
    assert cdl.check(root, TODAY) == ["0001-x.md:3: link text 0002 does not match 0003-z.md"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("# 0032 — T\n", ["0033-x.md: heading ID 0032 does not match the file name"]),
        ("# 0033 — T\n", []),
        ("", []),
    ],
)
def test_heading_number_must_match_file_number(
    tmp_path: Path, text: str, expected: list[str]
) -> None:
    root = make_log(tmp_path, active=row(33, "accepted"), entries={"0033-x.md": text})
    assert cdl.check(root, TODAY) == expected


def test_gaps_in_numbers_pass(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(1, "accepted"), row(3, "accepted", "z")]),
        entries={"0001-x.md": "# 0001\n", "0003-z.md": "# 0003\n"},
    )
    assert cdl.check(root, TODAY) == []


@pytest.mark.parametrize(
    ("link", "expected"),
    [
        ("[0002](0002-y.md)", []),
        (
            "[0003](0003-z.md)",
            ["0001-x.md: the status line does not link superseded by 0002 to 0002-y.md"],
        ),
    ],
)
def test_superseded_by_must_match_status_link(
    tmp_path: Path, link: str, expected: list[str]
) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(2, "accepted", "y"), row(3, "accepted", "z")]),
        historical=row(1, "superseded by 0002"),
        entries={
            "0001-x.md": f"# 0001\n\n**Status:** superseded by {link}, 2026-10-24 (#1).\n",
            "0002-y.md": "",
            "0003-z.md": "",
        },
    )
    assert cdl.check(root, TODAY) == expected


def test_renumbered_old_entry_keeps_size_exemption(tmp_path: Path) -> None:
    old = cdl.LAST_UNLIMITED_ENTRY
    new = old + 1
    edit = f"\n\n_Edited 2026-10-24 (#1): renumber from {old:04d}._\n"
    root = make_log(
        tmp_path,
        active=row(new, "accepted"),
        entries={f"{new:04d}-x.md": "x" * (cdl.ENTRY_LIMIT + 1) + edit},
    )
    assert cdl.check(root, TODAY) == []


# The tests of `--new`. Each git test runs in its own repo, with no user or system config.

GIT = shutil.which("git")
needs_git = pytest.mark.skipif(GIT is None, reason="git is not installed")
EMAIL = "tester" + "@" + "example.invalid"


@pytest.fixture
def git_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate git from the user: no global or system config, no `GIT_*` variable, no parent repo."""
    for name in list(os.environ):
        if name.upper().startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    return tmp_path


def git(cwd: Path, *args: str, stdin: bytes | None = None) -> None:
    subprocess.run(  # noqa: S603
        [GIT or "git", "-c", "user.name=Tester", "-c", f"user.email={EMAIL}", *args],
        cwd=cwd,
        input=stdin,
        check=True,
        capture_output=True,
    )


def entry(root: Path, name: str) -> None:
    (root / cdl.LOG_DIR / name).write_text(f"# {name[:4]}\n", encoding="utf-8")


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def repo(root: Path) -> Path:
    """A new repo on `main` with entry 0001 committed."""
    (root / cdl.LOG_DIR).mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    entry(root, "0001-a.md")
    commit(root, "0001")
    return root


def verdicts(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith(("keep:", "re-ID:"))]


def scripted(*ids: str) -> Callable[[], str]:
    """A draw function that gives `ids` in order."""
    queue = list(ids)

    def draw() -> str:
        return queue.pop(0)

    return draw


def test_new_id_starts_with_a_letter_and_uses_the_alphabet() -> None:
    for _ in range(500):
        found = cdl.new_id(set())
        assert len(found) == 4
        assert found[0] in cdl.LETTERS
        assert set(found) <= set(cdl.ALPHABET)
        assert cdl.ENTRY_NAME.match(f"{found}-x.md")


def test_new_id_skips_used_ids() -> None:
    assert cdl.new_id({"k7m2", "a000"}, scripted("k7m2", "a000", "b111")) == "b111"


@pytest.mark.parametrize(
    ("name", "valid"),
    [
        ("0001-x.md", True),
        ("k7m2-x.md", True),
        ("z000-x.md", True),
        ("0k7m-x.md", False),
        ("i7m2-x.md", False),
        ("k7u2-x.md", False),
    ],
)
def test_entry_id_format(tmp_path: Path, name: str, valid: bool) -> None:
    root = make_log(tmp_path, entries={name: ""})
    errors = cdl.check(root, TODAY)
    if valid:
        assert errors == [f"{name}: 0 index rows, expected 1"]
    else:
        assert errors == [
            f"{name}: the file name starts like an entry, but {name[:4]!r} is not a valid ID"
        ]


def test_letter_ids_in_rows_links_and_status(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row("k7m2", "accepted", "y"),
        historical=row(1, "superseded by k7m2"),
        entries={
            "0001-x.md": "# 0001\n\n**Status:** superseded by [k7m2](k7m2-y.md), 2026-10-25 (#1).\n",
            "k7m2-y.md": "# k7m2 — T\n\nSee [0001](0001-x.md).\n",
        },
    )
    assert cdl.check(root, TODAY) == []


def test_re_id_keeps_size_exemption(tmp_path: Path) -> None:
    old = cdl.LAST_UNLIMITED_ENTRY
    edit = f"\n\n_Edited 2026-10-25 (#1): re-ID from {old:04d}._\n"
    root = make_log(
        tmp_path,
        active=row("k7m2", "accepted"),
        entries={"k7m2-x.md": "x" * (cdl.ENTRY_LIMIT + 1) + edit},
    )
    assert cdl.check(root, TODAY) == []


def test_letter_id_has_no_size_exemption(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row("a001", "accepted"),
        entries={"a001-x.md": "x" * (cdl.ENTRY_LIMIT + 1)},
    )
    errors = cdl.check(root, TODAY)
    assert f"a001-x.md: {cdl.ENTRY_LIMIT + 1} characters, limit {cdl.ENTRY_LIMIT}" in errors


def test_new_without_git(git_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = make_log(
        git_env / "plain",
        active="\n".join([row(1, "accepted"), row(3, "accepted", "z")]),
        entries={"0001-x.md": "# 0001\n", "0003-z.md": "# 0003\n"},
    )
    lines = cdl.new_lines(root, scripted("0001", "0003", "k7m2"))
    assert lines[0] == "new: k7m2"
    assert any(line.startswith("note: ") for line in lines)

    def no_git(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git")

    monkeypatch.setattr(cdl.subprocess, "run", no_git)
    assert cdl.new_lines(root, scripted("k7m2"))[0] == "new: k7m2"


@needs_git
def test_new_with_unborn_head(git_env: Path) -> None:
    root = git_env / "repo"
    (root / cdl.LOG_DIR).mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    lines = cdl.new_lines(root)
    assert cdl.ENTRY_NAME.match(lines[0].removeprefix("new: ") + "-x.md")
    assert verdicts(lines) == []


@needs_git
def test_new_sees_branch_and_worktree(git_env: Path) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "other")
    entry(root, "b222-b.md")
    commit(root, "b222-b")
    git(root, "checkout", "-q", "main")
    git(root, "worktree", "add", "-q", "-b", "wt", str(git_env / "wt"))
    entry(git_env / "wt", "c333-c.md")
    entry(root, "b222-a.md")
    lines = cdl.new_lines(root, scripted("0001", "b222", "c333", "d444"))
    assert lines[0] == "new: d444"
    assert verdicts(lines) == ["re-ID: b222-a.md; b222-b.md also uses b222 (on other)"]


@needs_git
def test_same_file_on_other_ref_is_not_a_collision(git_env: Path) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "other")
    entry(root, "0002-b.md")
    commit(root, "0002-b on other")
    git(root, "checkout", "-q", "main")
    entry(root, "0002-b.md")
    commit(root, "0002-b on main")
    assert verdicts(cdl.new_lines(root)) == []


@needs_git
def test_new_ignores_own_uncommitted_rename(git_env: Path) -> None:
    root = repo(git_env / "repo")
    git(root, "remote", "add", "origin", str(git_env / "remote.git"))
    git(root, "checkout", "-q", "-b", "feat")
    entry(root, "0002-old.md")
    commit(root, "0002-old")
    git(root, "update-ref", "refs/remotes/origin/feat", "HEAD")
    git(root, "branch", "-q", "--set-upstream-to=origin/feat")
    # A rebase makes a new commit, so origin/feat is no longer merged into HEAD.
    git(root, "commit", "-q", "--amend", "-m", "0002-old, rebased")
    git(root, "mv", "notes/decisions/0002-old.md", "notes/decisions/0002-new.md")
    assert verdicts(cdl.new_lines(root)) == []


@needs_git
def test_old_name_of_an_entry_is_not_a_collision(git_env: Path) -> None:
    """A stale branch has the old names of two entries that this tree gave new IDs."""
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "stale")
    entry(root, "0040-rules.md")
    entry(root, "0043-gate.md")
    commit(root, "old names")
    git(root, "checkout", "-q", "main")
    entry(root, "0043-rules.md")
    entry(root, "0046-gate.md")
    commit(root, "new names")
    assert verdicts(cdl.new_lines(root)) == []


@needs_git
def test_backup_branches_are_skipped(git_env: Path) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "backup/before-re-id")
    entry(root, "0002-z.md")
    commit(root, "0002-z")
    git(root, "checkout", "-q", "main")
    entry(root, "0002-a.md")
    commit(root, "0002-a")
    assert verdicts(cdl.new_lines(root)) == []


@needs_git
def test_new_verdicts_agree_between_worktrees(git_env: Path) -> None:
    root = repo(git_env / "repo")
    other = git_env / "wt"
    git(root, "worktree", "add", "-q", "-b", "wt", str(other))
    entry(root, "0003-x.md")
    entry(other, "0003-y.md")
    here = verdicts(cdl.new_lines(root))
    there = verdicts(cdl.new_lines(other))
    assert len(here) == 1 and here[0].startswith("keep: 0003-x.md; 0003-y.md also uses 0003")
    assert len(there) == 1
    assert there[0].startswith("re-ID: 0003-y.md; 0003-x.md also uses 0003")


@needs_git
def test_first_commit_wins(git_env: Path) -> None:
    """The entry with the earlier first commit keeps its ID, also when its file name sorts later."""
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "early")
    entry(root, "k7m2-z.md")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "early", "--date=2026-01-01T00:00:00")
    git(root, "checkout", "-q", "main")
    entry(root, "k7m2-a.md")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "late", "--date=2026-02-01T00:00:00")
    assert verdicts(cdl.new_lines(root)) == [
        "re-ID: k7m2-a.md; k7m2-z.md also uses k7m2 (on early)"
    ]


@needs_git
def test_uncommitted_entry_loses_to_committed(git_env: Path) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "other")
    entry(root, "k7m2-z.md")
    commit(root, "k7m2-z")
    git(root, "checkout", "-q", "main")
    entry(root, "k7m2-a.md")
    assert verdicts(cdl.new_lines(root)) == [
        "re-ID: k7m2-a.md; k7m2-z.md also uses k7m2 (on other)"
    ]


@needs_git
def test_new_target_wins(git_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "t")
    entry(root, "0002-t.md")
    commit(root, "0002-t")
    git(root, "update-ref", f"refs/remotes/origin/{cdl.TARGET_BRANCH}", "HEAD")
    git(root, "checkout", "-q", "main")
    git(root, "branch", "-q", "-D", "t")
    entry(root, "0002-a.md")
    commit(root, "0002-a")
    assert verdicts(cdl.new_lines(root)) == [
        f"re-ID: 0002-a.md; 0002-t.md also uses 0002 (on origin/{cdl.TARGET_BRANCH})"
    ]
    assert cdl.main(["check_decision_log.py", "--new", str(root)]) == 1
    assert "re-ID: 0002-a.md" in capsys.readouterr().out
    assert cdl.main(["check_decision_log.py", "--collisions", str(root)]) == 1
    out = capsys.readouterr().out
    assert "re-ID: 0002-a.md" in out
    assert "new:" not in out


@needs_git
def test_collisions_passes_without_a_collision(
    git_env: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = repo(git_env / "repo")
    git(root, "checkout", "-q", "-b", "other")
    entry(root, "0002-b.md")
    commit(root, "0002-b")
    git(root, "checkout", "-q", "main")
    entry(root, "k7m2-a.md")
    assert cdl.main(["check_decision_log.py", "--collisions", str(root)]) == 0
    assert "new:" not in capsys.readouterr().out


def branches(root: Path, count: int) -> None:
    """Add `count` branches, each with one new entry, in one `git fast-import` process."""
    stream = []
    for i in range(count):
        body = f"# {i + 2:04d}\n".encode()
        head = (
            f"commit refs/heads/b{i}\n"
            f"committer Tester <{EMAIL}> 1700000000 +0000\n"
            "data 1\nb\n"
            "from refs/heads/main^0\n"
            f"M 100644 inline notes/decisions/{i + 2:04d}-b{i}.md\n"
            f"data {len(body)}\n"
        )
        stream.append(head.encode() + body + b"\n")
    git(root, "fast-import", "--quiet", stdin=b"".join(stream))


@needs_git
def test_new_process_count_is_fixed(git_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_run = subprocess.run
    calls: list[object] = []

    def counting_run(*args: object, **kwargs: object) -> object:
        calls.append(args[0] if args else kwargs.get("args"))
        return real_run(*args, **kwargs)  # type: ignore[call-overload]

    counts = []
    for count in (2, 20):
        root = repo(git_env / f"repo{count}")
        branches(root, count)
        calls.clear()
        monkeypatch.setattr(cdl.subprocess, "run", counting_run)
        lines = cdl.new_lines(root)
        monkeypatch.setattr(cdl.subprocess, "run", real_run)
        assert verdicts(lines) == []
        counts.append(len(calls))
    assert counts[0] == counts[1] <= 5
