"""The decision log keeps its index and its size limits (decision 0029)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

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


def row(number: int, status: str, name: str = "x", decision: str = "Title") -> str:
    return f"| [{number:04d}]({number:04d}-{name}.md) | {decision} | {status} |"


def proposed_entry(day: str) -> str:
    return f"# 0001\n\n**Status:** proposed, {day} (user).\n"


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
        entries={"0001-x.md": "", "0002-y.md": proposed_entry("2026-10-01"), "0003-z.md": ""},
    )
    errors = cdl.check(root, TODAY)
    assert any("'superseded by 0002' names an entry that is 'proposed'" in e for e in errors)
    assert any("'superseded by 0009' names no other indexed entry" in e for e in errors)


def test_used_evidence_is_historical(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active="\n".join([row(1, "accepted"), row(3, "evidence; used by 0001", "z")]),
        historical=row(2, "evidence; used by 0001", "y"),
        entries={"0001-x.md": "", "0002-y.md": "", "0003-z.md": ""},
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
