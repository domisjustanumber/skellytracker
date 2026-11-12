"""The invariant-token checker of `tools/check_ste_tokens.py`, on tiny inputs."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import check_ste_tokens as cts

REPO_ROOT = Path(cts.__file__).resolve().parents[1]


def diff(old: str, new: str) -> list[tuple[str, str, int, int]]:
    """The differences between two texts as (kind, token, before, after) tuples."""
    return [(d.kind, d.token, d.before, d.after) for d in cts.compare_texts(old, new)]


def tokens(text: str, kind: str) -> list[str]:
    return cts.collect_tokens(cts.parse_markdown(text))[kind]


# --------------------------------------------------------------------------------------------
# What may change
# --------------------------------------------------------------------------------------------


def test_identical_text_has_no_differences() -> None:
    text = "---\nid: a\n---\n\n# T\n\nUse `x` for 3 things. See [a](b.md).\n"
    assert diff(text, text) == []


def test_rewording_prose_keeps_every_token() -> None:
    old = "# T\n\nThe host passes `x` through 3 stages, see [a](b.md).\n"
    new = "# T\n\nThree stages (3) take `x` from the host: [a](b.md) explains.\n"
    assert diff(old, new) == []


def test_crlf_and_lf_texts_are_equal() -> None:
    lf = "---\nid: a\n---\n\n```yaml\nk: v\n```\n\nText `x`.\n"
    assert diff(lf, lf.replace("\n", "\r\n")) == []


def test_a_byte_order_mark_is_ignored() -> None:
    assert diff("# T\n", "\ufeff# T\n") == []


# --------------------------------------------------------------------------------------------
# (1) code spans
# --------------------------------------------------------------------------------------------


def test_a_changed_code_span_is_a_difference() -> None:
    assert diff("Use `a` and `b`.", "Use `a` and `c`.") == [
        ("code-span", "b", 1, 0),
        ("code-span", "c", 0, 1),
    ]


def test_code_spans_are_counted() -> None:
    assert diff("`a` and `a`", "`a`") == [("code-span", "a", 2, 1)]


def test_a_double_backtick_span_may_hold_a_backtick() -> None:
    assert tokens("Use ``a`b`` here", cts.CODE_SPAN) == ["a`b"]


def test_a_padding_space_inside_a_span_is_dropped() -> None:
    assert diff("Use `a` here", "Use ` a ` here") == []


def test_an_escaped_backtick_does_not_open_a_span() -> None:
    assert cts.find_code_spans(r"a \`b\` c") == []
    assert tokens(r"a \`b `c`", cts.CODE_SPAN) == ["c"]


def test_an_unclosed_backtick_run_is_literal() -> None:
    assert tokens("a `` b `c`", cts.CODE_SPAN) == ["c"]


def test_a_span_may_cross_a_line_break_and_rewrapping_is_free() -> None:
    assert tokens("a `b\nc` d", cts.CODE_SPAN) == ["b c"]
    assert diff("a `b c` d", "a `b\nc` d") == []


def test_a_span_does_not_cross_list_items() -> None:
    assert tokens("- a ` b\n- c ` d\n", cts.CODE_SPAN) == []


def test_code_inside_a_fence_is_not_a_code_span() -> None:
    assert tokens("```\nuse `x`\n```\n", cts.CODE_SPAN) == []


# --------------------------------------------------------------------------------------------
# (2) numbers
# --------------------------------------------------------------------------------------------


def test_numbers_are_standalone_integers_and_decimals() -> None:
    assert tokens("Pad 2, scale 0.5, b2, 3x and v4.", cts.NUMBER) == ["2", "0.5"]


def test_a_changed_number_is_a_difference() -> None:
    assert diff("Use 3 passes.", "Use 4 passes.") == [
        ("number", "3", 1, 0),
        ("number", "4", 0, 1),
    ]


def test_numbers_in_code_spans_fences_and_front_matter_are_not_number_tokens() -> None:
    text = "---\nsince: 7\n---\nSee `a 5`.\n\n```\nb 6\n```\n"
    assert tokens(text, cts.NUMBER) == []


def test_numbers_in_a_link_target_are_ignored_but_not_those_in_its_text() -> None:
    text = "See [part 2](notes/0016-x.md#step-3) and <https://x.org/1> and https://y.org/9."
    assert tokens(text, cts.NUMBER) == ["2"]


def test_numbers_in_a_rule_id_are_ignored() -> None:
    text = "- [ ] `V-a.b-1` The rule 2 holds. Compare V-a.b-3 and (V-c-4)."
    assert tokens(text, cts.NUMBER) == ["2"]


def test_numbers_in_table_cells_count() -> None:
    assert tokens("| A | Description |\n|---|---|\n| 1 | has 2 |\n", cts.NUMBER) == [
        "1",
        "2",
    ]


# --------------------------------------------------------------------------------------------
# (3) fenced code blocks
# --------------------------------------------------------------------------------------------


def test_a_fence_is_compared_byte_for_byte() -> None:
    old = "```yaml\na: 1\n```\n"
    new = "```yaml\na:  1\n```\n"
    assert diff(old, new) == [
        ("fence", "```yaml\na:  1\n```", 0, 1),
        ("fence", "```yaml\na: 1\n```", 1, 0),
    ]


def test_moving_a_fence_is_not_a_difference() -> None:
    assert diff("```\nx\n```\n\nText\n", "Text\n\n```\nx\n```\n") == []


def test_a_tilde_fence_and_a_longer_fence_are_blocks() -> None:
    text = "~~~\na\n~~~\n\n````md\n```\nb\n```\n````\n"
    assert tokens(text, cts.FENCE) == ["~~~\na\n~~~", "````md\n```\nb\n```\n````"]


def test_an_unclosed_fence_runs_to_the_end_of_the_file() -> None:
    assert tokens("a\n```\nb\n\nc\n", cts.FENCE) == ["```\nb\n\nc\n"]


def test_three_backticks_on_one_line_are_not_a_fence() -> None:
    assert tokens("```x``` and more\n", cts.FENCE) == []
    assert tokens("```x``` and more\n", cts.CODE_SPAN) == ["x"]


def test_an_indented_fence_in_a_list_keeps_its_indentation() -> None:
    old = "- item\n\n  ```\n  x\n  ```\n"
    new = "- item\n\n```\nx\n```\n"
    assert [d[0] for d in diff(old, new)] == ["fence", "fence"]


# --------------------------------------------------------------------------------------------
# (4) tables
# --------------------------------------------------------------------------------------------

TABLE = "| Field | Type | Description |\n|---|---|---|\n| `a` | int | Old words. |\n"


def test_the_prose_last_column_of_a_table_may_be_reworded() -> None:
    assert diff(TABLE, TABLE.replace("Old words.", "Completely new words")) == []


@pytest.mark.parametrize(
    "header",
    ["Description", "Meaning", "Rule", "Semantics", "Purpose", "Reason", "Contents"]
    + ["Typical use", "Change", "description", "Typical  Use"],
)
def test_every_prose_header_frees_the_last_column(header: str) -> None:
    old = f"| A | {header} |\n|---|---|\n| x | one |\n"
    assert diff(old, old.replace("one", "two")) == []


def test_a_last_column_with_another_header_is_compared() -> None:
    old = "| Item | Value |\n|---|---|\n| x | one |\n"
    assert diff(old, old.replace("one", "two")) == [
        ("table", "Value: one", 1, 0),
        ("table", "Value: two", 0, 1),
    ]


def test_a_cell_before_the_last_column_is_compared() -> None:
    assert diff(TABLE, TABLE.replace("| int |", "| float |")) == [
        ("table", "Type: float", 0, 1),
        ("table", "Type: int", 1, 0),
    ]


def test_a_changed_header_row_is_a_difference() -> None:
    new = TABLE.replace("| Type |", "| Kind |")
    kinds = {d[0] for d in diff(TABLE, new)}
    assert kinds == {"table"}
    assert ("table", "header: Field | Kind | Description", 0, 1) in diff(TABLE, new)


def test_renaming_the_last_header_makes_its_cells_invariant() -> None:
    new = TABLE.replace("Description", "Notes")
    assert ("table", "Notes: Old words.", 0, 1) in diff(TABLE, new)


def test_an_escaped_pipe_does_not_split_a_cell() -> None:
    assert cts.split_row(r"| `a\|b` | c |") == [r"`a\|b`", "c"]


def test_a_table_ends_at_a_blank_line_or_a_line_without_a_pipe() -> None:
    text = "| A | B |\n|---|---|\n| 1 | 2 |\nplain\n| x | y |\n"
    assert tokens(text, cts.TABLE) == ["header: A | B", "A: 1", "B: 2"]


def test_a_delimiter_row_with_another_width_is_not_a_table() -> None:
    assert tokens("| A | B |\n|---|\n| 1 | 2 |\n", cts.TABLE) == []


def test_tables_in_a_fence_are_not_tables() -> None:
    assert tokens("```\n| A |\n|---|\n| 1 |\n```\n", cts.TABLE) == []


# --------------------------------------------------------------------------------------------
# (5) front matter
# --------------------------------------------------------------------------------------------


def test_front_matter_is_compared_byte_for_byte() -> None:
    old = "---\nid: a\n---\nText\n"
    assert diff(old, old.replace("id: a", "id:  a")) == [
        ("front-matter", "---\nid:  a\n---", 0, 1),
        ("front-matter", "---\nid: a\n---", 1, 0),
    ]


def test_losing_the_front_matter_is_a_difference() -> None:
    assert diff("---\nid: a\n---\nText\n", "Text\n") == [
        ("front-matter", "---\nid: a\n---", 1, 0)
    ]


def test_a_rule_line_that_is_not_at_the_top_is_not_front_matter() -> None:
    assert tokens("Text\n---\nid: a\n---\n", cts.FRONT_MATTER) == []


def test_a_hash_comment_in_front_matter_is_not_a_heading() -> None:
    assert tokens("---\n# note\nid: a\n---\n# Title\n", cts.HEADING) == ["# Title"]


# --------------------------------------------------------------------------------------------
# (6) headings
# --------------------------------------------------------------------------------------------


def test_a_heading_level_change_is_a_difference() -> None:
    assert diff("## Fields\n", "### Fields\n") == [
        ("heading", "## Fields", 1, 0),
        ("heading", "### Fields", 0, 1),
    ]


def test_a_heading_text_change_is_a_difference() -> None:
    assert ("heading", "# New", 0, 1) in diff("# Old\n", "# New\n")


def test_closing_hashes_and_hashtags() -> None:
    assert tokens("## Fields ##\n#hashtag\n# C#\n####### seven\n", cts.HEADING) == [
        "## Fields",
        "# C#",
    ]


def test_a_heading_in_a_fence_is_not_a_heading() -> None:
    assert tokens("```\n# comment\n```\n", cts.HEADING) == []


def test_reordering_headings_is_not_a_difference() -> None:
    assert diff("# A\n\n# B\n", "# B\n\n# A\n") == []


# --------------------------------------------------------------------------------------------
# (7) rule-ID labels
# --------------------------------------------------------------------------------------------

RULES = "- [ ] `V-a-1` One.\n- [ ] `V-a-2` Two.\n- [x] `V-a-3` Three.\n"


def test_rule_ids_are_the_leading_code_spans_of_list_items() -> None:
    text = RULES + "\nSee `V-a-9` and V-a-8.\n1. `V-b-1` ordered\n* `V-b-2` star\n"
    assert tokens(text, cts.RULE_ID) == ["V-a-1", "V-a-2", "V-a-3", "V-b-1", "V-b-2"]


def test_a_removed_rule_id_is_a_difference() -> None:
    new = RULES.replace("- [ ] `V-a-2` Two.\n", "")
    assert ("rule-id", "V-a-2", 1, 0) in diff(RULES, new)


def test_reordered_rule_ids_are_a_difference() -> None:
    new = "- [ ] `V-a-2` Two.\n- [ ] `V-a-1` One.\n- [x] `V-a-3` Three.\n"
    result = diff(RULES, new)
    assert [d[:2] for d in result if d[0] == "rule-id"] == [
        ("rule-id", "order changed at position 1: V-a-1 became V-a-2")
    ]
    assert [d[0] for d in result] == ["rule-id"]


def test_rewording_a_rule_keeps_its_label() -> None:
    assert diff(RULES, RULES.replace("One.", "First.")) == []


# --------------------------------------------------------------------------------------------
# (8) links
# --------------------------------------------------------------------------------------------


def test_a_link_is_its_text_and_its_target() -> None:
    assert tokens("See [the guide](a.md#b) now.", cts.LINK) == ["[the guide](a.md#b)"]


def test_a_changed_link_text_or_target_is_a_difference() -> None:
    old = "See [the guide](a.md)."
    assert diff(old, "See [a guide](a.md).") == [
        ("link", "[a guide](a.md)", 0, 1),
        ("link", "[the guide](a.md)", 1, 0),
    ]
    assert diff(old, "See [the guide](b.md).") == [
        ("link", "[the guide](a.md)", 1, 0),
        ("link", "[the guide](b.md)", 0, 1),
    ]


def test_link_text_may_hold_code_and_may_wrap() -> None:
    assert tokens("[`a.b`](c.md) and [two\nwords](d.md)", cts.LINK) == [
        "[`a.b`](c.md)",
        "[two words](d.md)",
    ]


def test_an_image_a_reference_definition_and_an_autolink_are_links() -> None:
    text = "![alt](i.png) and <https://x.org>\n\n[ref]: https://y.org/p\n"
    assert sorted(tokens(text, cts.LINK)) == [
        "![alt](i.png)",
        "<https://x.org>",
        "[ref]: https://y.org/p",
    ]


def test_a_link_in_code_is_not_a_link() -> None:
    assert (
        tokens("Write `[a](b.md)` like this.\n\n```\n[c](d.md)\n```\n", cts.LINK) == []
    )


def test_a_link_title_is_not_part_of_the_target() -> None:
    assert tokens('[a](b.md "Title") and [c](<d e.md>)', cts.LINK) == [
        "[a](b.md)",
        "[c](<d e.md>)",
    ]


def test_a_link_inside_a_table_cell_counts() -> None:
    assert tokens("| A |\n|---|\n| [x](y.md) |\n", cts.LINK) == ["[x](y.md)"]


# --------------------------------------------------------------------------------------------
# The allow file
# --------------------------------------------------------------------------------------------

ALLOW = """\
# approved differences
- file: specs/a.md
  kind: code-span
  token: "`none`"
  reason: Named in the opening sentence.
- file: ./specs\\b.md
  kind: fence
  token: |
    ```yaml
    a: 1
    ```
  reason: 'It''s a fix'   # note
- file: specs/c.md
  kind: number
  token: 3
  reason: plain words
"""


def test_the_allow_file_reads_plain_quoted_and_block_scalars() -> None:
    entries = cts.parse_allow_text(ALLOW)
    assert [(e.file, e.kind, e.token, e.reason) for e in entries] == [
        ("specs/a.md", "code-span", "`none`", "Named in the opening sentence."),
        ("./specs\\b.md", "fence", "```yaml\na: 1\n```\n", "It's a fix"),
        ("specs/c.md", "number", "3", "plain words"),
    ]


def test_a_strip_block_scalar_has_no_final_newline() -> None:
    text = "- file: a.md\n  kind: fence\n  token: |-\n    x\n    y\n  reason: r\n"
    assert [e.token for e in cts.parse_allow_text(text)] == ["x\ny"]


def test_the_allow_file_may_be_a_json_array() -> None:
    text = '[{"file": "a.md", "kind": "link", "token": "[a](b)", "reason": "r"}]'
    assert [e.token for e in cts.parse_allow_text(text)] == ["[a](b)"]


def test_an_empty_allow_file_has_no_entries() -> None:
    assert cts.parse_allow_text("# nothing\n") == []
    assert cts.parse_allow_text("[]") == []


@pytest.mark.parametrize(
    "text",
    [
        "- file: a.md\n  kind: link\n  token: x\n",  # no reason
        "- file: a.md\n  kind: link\n  token: x\n  reason: ''\n",  # empty reason
        "- file: a.md\n  kind: nope\n  token: x\n  reason: r\n",  # unknown kind
        "- file: a.md\n  kind: link\n  token: x\n  reason: r\n  extra: 1\n",  # unknown key
        '- file: a.md\n  kind: link\n  token: "x\n  reason: r\n',  # open quote
        "- file: a.md\n  kind: link\n  token: 'x\n  reason: r\n",  # open quote
        '- file: a.md\n  kind: link\n  token: "\\q"\n  reason: r\n',  # bad escape
        "- file: a.md\n  kind: link\n  token: |+\n    x\n  reason: r\n",  # keep chomping
        "kind: link\n",  # no list item
        "- {file: a.md, kind: link, token: x, reason: r}\n",  # flow style
        "just words\n",
        '[{"file": "a.md"}]',
        "[1]",
        "[oops",
    ],
)
def test_a_bad_allow_file_is_an_error(text: str) -> None:
    with pytest.raises(cts.CheckError):
        cts.parse_allow_text(text)


def test_an_allowance_matches_on_file_kind_and_token_whatever_the_counts() -> None:
    allowance = cts.Allowance("./specs\\a.md", "code-span", "x", "why")
    assert allowance.matches("specs/a.md", cts.Difference("code-span", "x", 5, 0))
    assert not allowance.matches("specs/b.md", cts.Difference("code-span", "x", 1, 0))
    assert not allowance.matches("specs/a.md", cts.Difference("number", "x", 1, 0))
    assert not allowance.matches("specs/a.md", cts.Difference("code-span", "y", 1, 0))


def test_match_allowances_pairs_each_difference() -> None:
    allowance = cts.Allowance("a.md", "number", "3", "why")
    differences = [
        cts.Difference("number", "3", 1, 0),
        cts.Difference("number", "4", 0, 1),
    ]
    findings = cts.match_allowances("a.md", differences, [allowance])
    assert [f.allowance for f in findings] == [allowance, None]


# --------------------------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------------------------


def test_the_report_groups_differences_by_kind_and_marks_approved_ones() -> None:
    allowance = cts.Allowance("a.md", "number", "3", "the count grew")
    differences = cts.compare_texts("Has `x` and 3.", "Has `y` and 4.")
    report = cts.format_report(
        "a.md", cts.match_allowances("a.md", differences, [allowance])
    )
    assert report.splitlines() == [
        "a.md: 3 difference(s), 1 approved",
        "  [code-span]",
        '    difference: "x" before=1 after=0',
        '    difference: "y" before=0 after=1',
        "  [number]",
        '    approved: "3" before=1 after=0 reason: the count grew',
        '    difference: "4" before=0 after=1',
    ]


def test_the_report_prints_a_token_with_a_newline_as_one_json_line() -> None:
    differences = cts.compare_texts("```\na\n```\n", "```\nb\n```\n")
    report = cts.format_report("a.md", cts.match_allowances("a.md", differences, []))
    assert '    difference: "```\\na\\n```" before=1 after=0' in report.splitlines()


def test_a_file_without_findings_reports_ok() -> None:
    assert cts.format_report("a.md", []) == "a.md: ok"


# --------------------------------------------------------------------------------------------
# The command line
# --------------------------------------------------------------------------------------------


@pytest.fixture
def fake_revision(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Replace git with a dict of {file name: old text}."""
    old: dict[str, str] = {}
    monkeypatch.setattr(cts, "locate", lambda path: (path.parent, path.name))

    def read(revision: str, root: Path, relative: str) -> str:
        if relative not in old:
            raise cts.CheckError(f"{relative} is not in {revision}")
        return old[relative]

    monkeypatch.setattr(cts, "read_at_revision", read)
    return old


def test_main_exits_0_when_the_tokens_are_kept(
    tmp_path: Path, fake_revision: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.md").write_text("Pass `x` in 3 steps.\n", encoding="utf-8")
    fake_revision["a.md"] = "The host passes `x`\nin 3 steps.\n"
    assert cts.main([str(tmp_path / "a.md")]) == 0
    assert capsys.readouterr().out == "a.md: ok\n"


def test_main_exits_1_and_prints_each_difference(
    tmp_path: Path, fake_revision: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.md").write_text("Pass `y` in 3 steps.\n", encoding="utf-8")
    fake_revision["a.md"] = "Pass `x` in 3 steps.\n"
    assert cts.main([str(tmp_path / "a.md")]) == 1
    out = capsys.readouterr().out
    assert 'difference: "x" before=1 after=0' in out
    assert 'difference: "y" before=0 after=1' in out


def test_main_exits_0_when_every_difference_is_approved(
    tmp_path: Path, fake_revision: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.md").write_text("Pass `y`.\n", encoding="utf-8")
    fake_revision["a.md"] = "Pass `x`.\n"
    allow = tmp_path / "allow.yaml"
    allow.write_text(
        "- file: a.md\n  kind: code-span\n  token: x\n  reason: renamed\n"
        "- file: a.md\n  kind: code-span\n  token: y\n  reason: renamed\n"
        "- file: a.md\n  kind: number\n  token: 9\n  reason: stale\n",
        encoding="utf-8",
    )
    assert cts.main(["--allow", str(allow), str(tmp_path / "a.md")]) == 0
    captured = capsys.readouterr()
    assert 'approved: "x" before=1 after=0 reason: renamed' in captured.out
    assert "a.md: 0 difference(s), 2 approved" in captured.out
    assert "unused allow entry: a.md [number] '9'" in captured.err


def test_main_still_exits_1_for_a_difference_that_no_entry_approves(
    tmp_path: Path, fake_revision: dict[str, str]
) -> None:
    (tmp_path / "a.md").write_text("Pass `y`.\n", encoding="utf-8")
    fake_revision["a.md"] = "Pass `x`.\n"
    allow = tmp_path / "allow.yaml"
    allow.write_text(
        "- file: a.md\n  kind: code-span\n  token: x\n  reason: renamed\n",
        encoding="utf-8",
    )
    assert cts.main(["--allow", str(allow), str(tmp_path / "a.md")]) == 1


def test_main_reads_the_given_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []
    monkeypatch.setattr(cts, "locate", lambda path: (path.parent, path.name))
    monkeypatch.setattr(
        cts, "read_at_revision", lambda rev, root, relative: seen.append(rev) or "x\n"
    )
    (tmp_path / "a.md").write_text("x\n", encoding="utf-8")
    cts.main(["--rev", "v1", str(tmp_path / "a.md")])
    cts.main([str(tmp_path / "a.md")])
    assert seen == ["v1", "HEAD"]


def test_main_exits_2_for_a_missing_file_and_still_checks_the_others(
    tmp_path: Path, fake_revision: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "b.md").write_text("`y`\n", encoding="utf-8")
    fake_revision["b.md"] = "`x`\n"
    assert cts.main([str(tmp_path / "a.md"), str(tmp_path / "b.md")]) == 2
    captured = capsys.readouterr()
    assert "a.md is not in HEAD" in captured.err
    assert "b.md: 2 difference(s)" in captured.out


def test_main_exits_2_for_a_bad_allow_file(
    tmp_path: Path, fake_revision: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.md").write_text("x\n", encoding="utf-8")
    allow = tmp_path / "allow.yaml"
    allow.write_text("nonsense\n", encoding="utf-8")
    assert cts.main(["--allow", str(allow), str(tmp_path / "a.md")]) == 2
    assert "error: allow file line 1" in capsys.readouterr().err
    assert (
        cts.main(["--allow", str(tmp_path / "none.yaml"), str(tmp_path / "a.md")]) == 2
    )


def test_main_requires_a_file(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        cts.main([])
    assert exit_info.value.code == 2


# --------------------------------------------------------------------------------------------
# Git (read-only commands against this repository)
# --------------------------------------------------------------------------------------------

needs_git = pytest.mark.skipif(
    shutil.which("git") is None or not (REPO_ROOT / ".git").exists(),
    reason="needs git and a git checkout",
)


@needs_git
def test_locate_finds_the_repository_path_with_forward_slashes() -> None:
    root, relative = cts.locate(REPO_ROOT / "tools" / "tests" / "conftest.py")
    assert root == REPO_ROOT.resolve()
    assert relative == "tools/tests/conftest.py"


@needs_git
def test_read_at_revision_returns_lf_text_of_a_committed_file() -> None:
    text = cts.read_at_revision("HEAD", REPO_ROOT, "pyproject.toml")
    assert "[project]" in text
    assert "\r" not in text


@needs_git
def test_read_at_revision_rejects_a_missing_path_and_a_bad_revision() -> None:
    with pytest.raises(cts.CheckError, match="git show failed"):
        cts.read_at_revision("HEAD", REPO_ROOT, "no/such/file.md")
    with pytest.raises(cts.CheckError, match="git show failed"):
        cts.read_at_revision("no-such-revision", REPO_ROOT, "pyproject.toml")


def test_read_at_revision_rejects_an_option_looking_revision() -> None:
    with pytest.raises(cts.CheckError, match="bad revision"):
        cts.read_at_revision("--output=x", REPO_ROOT, "pyproject.toml")


def test_locate_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(cts.CheckError, match="not a file"):
        cts.locate(tmp_path / "missing.md")
