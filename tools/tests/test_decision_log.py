"""The decision log keeps its index and its size limits (decision 0026)."""

from __future__ import annotations

from pathlib import Path

import check_decision_log as cdl

REPO_ROOT = Path(cdl.__file__).resolve().parents[1]

INDEX = """# Decision log

## Index

### Active

| # | Decision | Status |
|---|----------|--------|
{active}

### Historical

| # | Decision | Status |
|---|----------|--------|
{historical}

## Open work
"""


def make_log(
    tmp_path: Path,
    active: str = "",
    historical: str = "",
    entries: dict[str, str] | None = None,
) -> Path:
    log_dir = tmp_path / cdl.LOG_DIR
    log_dir.mkdir(parents=True)
    (log_dir / "README.md").write_text(
        INDEX.format(active=active, historical=historical), encoding="utf-8"
    )
    for name, text in (entries or {}).items():
        (log_dir / name).write_text(text, encoding="utf-8")
    return tmp_path


def row(number: int, status: str) -> str:
    return f"| [{number:04d}]({number:04d}-x.md) | Title | {status} |"


def test_repository_log_passes() -> None:
    assert cdl.check(REPO_ROOT) == []


def test_matching_index_passes(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "accepted"),
        historical=row(2, "absorbed into `AGENTS.md`").replace("0002-x", "0002-y"),
        entries={"0001-x.md": "# 0001\n", "0002-y.md": "# 0002\n"},
    )
    assert cdl.check(root) == []


def test_entry_without_row_and_row_without_entry_are_reported(tmp_path: Path) -> None:
    root = make_log(
        tmp_path, active=row(1, "accepted"), entries={"0002-y.md": "# 0002\n"}
    )
    errors = cdl.check(root)
    assert "0002-y.md: 0 index rows, expected 1" in errors
    assert any("row links to missing file 0001-x.md" in e for e in errors)


def test_status_must_match_its_table(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "superseded by 0002"),
        historical=row(2, "proposed").replace("0002-x", "0002-y"),
        entries={"0001-x.md": "", "0002-y.md": ""},
    )
    errors = cdl.check(root)
    assert any(
        "'superseded by 0002' must not be in the Active table" in e for e in errors
    )
    assert any("'proposed' must not be in the Historical table" in e for e in errors)


def test_unknown_status_is_reported(tmp_path: Path) -> None:
    root = make_log(tmp_path, active=row(1, "maybe"), entries={"0001-x.md": ""})
    assert any("unknown status 'maybe'" in e for e in cdl.check(root))


def test_new_entry_over_limit_is_reported_and_old_entry_is_not(tmp_path: Path) -> None:
    big = "x" * (cdl.ENTRY_LIMIT + 1)
    old = cdl.LAST_UNLIMITED_ENTRY
    new = old + 1
    root = make_log(
        tmp_path,
        active="\n".join(
            [
                row(old, "accepted"),
                row(new, "proposed").replace(f"{new:04d}-x", f"{new:04d}-y"),
            ]
        ),
        entries={f"{old:04d}-x.md": big, f"{new:04d}-y.md": big},
    )
    errors = cdl.check(root)
    assert (
        f"{new:04d}-y.md: {cdl.ENTRY_LIMIT + 1} characters, limit {cdl.ENTRY_LIMIT}"
        in errors
    )
    assert not any(e.startswith(f"{old:04d}-x.md") for e in errors)


def test_historical_entries_are_not_in_the_read_path(tmp_path: Path) -> None:
    root = make_log(
        tmp_path,
        active=row(1, "accepted"),
        historical=row(2, "rejected").replace("0002-x", "0002-y"),
        entries={"0001-x.md": "a" * 100, "0002-y.md": "b" * 1000},
    )
    index_size = cdl.size(root / cdl.LOG_DIR / "README.md")
    assert cdl.read_path_size(root) == index_size + 100


def test_crlf_counts_as_one_character(tmp_path: Path) -> None:
    path = tmp_path / "a.md"
    path.write_bytes(b"a\r\nb\r\n")
    assert cdl.size(path) == 4
