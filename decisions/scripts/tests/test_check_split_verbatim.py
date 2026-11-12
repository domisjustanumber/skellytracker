"""Unit tests for `check_split_verbatim` on tiny inputs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

import check_split_verbatim as csv_


def lines_of(text: str, name: str = "f.md", *, all_content: bool = False):
    """Content lines of a small Markdown document."""
    classified = csv_.classify_lines(
        csv_.split_text(text), name, all_content=all_content
    )
    return csv_.content_lines(classified)


def compare(old: str, *new: str, nav: tuple[str, ...] = (), generated=()):
    """Compare an old document against one or more new documents."""
    new_lines = [
        line
        for index, text in enumerate(new)
        for line in lines_of(text, f"new{index}.md")
    ]
    return csv_.compare_lines(
        lines_of(old, "old.md"),
        new_lines,
        [csv_.normalize_line(text) for text in nav],
        generated,
    )


# ---------------------------------------------------------------- the core verdicts


def test_moved_line_passes() -> None:
    old = "# Title\n\nFirst rule.\n\n## Part\n\nSecond rule.\n"
    new_a = "# Part\n\nSecond rule.\n"
    new_b = "# Title\n\nFirst rule.\n"
    assert compare(old, new_a, new_b).ok


def test_reworded_line_fails() -> None:
    result = compare("A rule.\n", "A rule!\n")
    assert not result.ok
    assert [text for text, _, _ in result.missing] == ["A rule."]
    assert [text for text, _, _ in result.unexpected] == ["A rule!"]


def test_link_target_change_passes() -> None:
    assert compare("See [Foo](#foo) now.\n", "See [Foo](../a/b.md#foo) now.\n").ok


def test_link_text_change_fails() -> None:
    assert not compare("See [Foo](#foo).\n", "See [Bar](#foo).\n").ok


def test_dropped_line_fails() -> None:
    result = compare("one\ntwo\nthree\n", "one\nthree\n")
    assert [(text, lines[0].number) for text, lines, _ in result.missing] == [
        ("two", 2)
    ]


def test_duplicated_line_is_unexpected() -> None:
    result = compare("same\n", "same\n", "same\n")
    assert [(text, count) for text, _, count in result.unexpected] == [("same", 1)]


def test_heading_inside_fence_is_content() -> None:
    text = "# Heading\n\n```yaml\n# comment\nkey: 1\n```\n"
    kinds = [
        line.kind for line in csv_.classify_lines(csv_.split_text(text), "f").lines
    ]
    assert kinds == ["heading", "blank", "fence", "content", "content", "fence"]
    # Dropping the comment from the fence is therefore a missing line, not a skipped heading.
    assert not compare(text, "```yaml\nkey: 1\n```\n").ok


def test_link_inside_code_is_not_neutralized() -> None:
    assert not compare("Use `[a](x)` here.\n", "Use `[a](y)` here.\n").ok
    fenced = "```text\n[a](x)\n```\n"
    assert not compare(fenced, "```text\n[a](y)\n```\n").ok


def test_trailing_whitespace_is_ignored() -> None:
    assert compare("text\n", "text   \n").ok


# ---------------------------------------------------------------- skipped lines


def test_front_matter_is_skipped() -> None:
    new = '---\nid: a.b\ntitle: "T"\nkind: format\n---\n\n# T\n\nbody\n'
    assert compare("body\n", new).ok


def test_table_header_and_separator_are_skipped() -> None:
    old = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"
    new_a = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    new_b = "| A | B |\n|---|---|\n| 3 | 4 |\n"  # a declared repeat of the header
    assert compare(old, new_a, new_b).ok


def test_bold_label_is_skipped_but_bold_sentence_is_content() -> None:
    assert compare("**Label:**\ntext\n", "text\n").ok
    assert not compare("**Rule.** The text.\n", "The text.\n").ok


def test_horizontal_rule_outside_fence_is_skipped() -> None:
    assert compare("a\n\n---\n\nb\n", "a\n\nb\n").ok
    assert not compare("```yaml\n---\nk: 1\n```\n", "```yaml\nk: 1\n```\n").ok


def test_yaml_example_file_is_all_content() -> None:
    old = "```yaml\n---\n# comment\nk: 1\n```\n"
    yaml_lines = lines_of("---\n# comment\nk: 1\n", "x.yaml", all_content=True)
    assert [line.text for line in yaml_lines] == ["---", "# comment", "k: 1"]
    assert csv_.compare_lines(lines_of(old), yaml_lines).ok


# ---------------------------------------------------------------- allowed additions


def test_rule_label_is_removed() -> None:
    assert compare("- [ ] Do it.\n", "- [ ] `V-pre.resize.fit-1` Do it.\n").ok
    assert not compare("- [ ] Do it.\n", "- [ ] `X-1` Do it.\n").ok


def test_declared_nav_line_is_allowed_once() -> None:
    nav = ("See [Other](../other.md#x).",)
    assert compare("body\n", "body\n\nSee [Other](a.md#y).\n", nav=nav).ok
    twice = compare("body\n", "body\nSee [Other](a.md).\nSee [Other](b.md).\n", nav=nav)
    assert [text for text, _, _ in twice.unexpected] == ["See [Other]()."]


def test_declared_nav_line_must_appear() -> None:
    result = compare("body\n", "body\n", nav=("See [Other](x.md).",))
    assert result.declared_nav_missing == ["See [Other]()."]
    assert not result.ok


def exact(kind: str, *lines: str) -> csv_.Generated:
    """A generated kind that allows exactly these (normalized) lines once each."""
    return csv_.Generated(kind, Counter(csv_.normalize_line(line) for line in lines))


def test_generated_line_is_an_allowed_addition_once() -> None:
    row = "| `a.b` | [a/b.md](a/b.md) | Title |"
    kinds = [exact("section_map_row", row)]
    result = compare("body\n", f"body\n{row}\n", generated=kinds)
    assert result.ok and result.additions["section_map_row"] == 1
    twice = compare("body\n", f"body\n{row}\n{row}\n", generated=kinds)
    assert [text for text, _, _ in twice.unexpected] == [csv_.normalize_line(row)]


def test_generated_line_the_manifest_implies_must_appear() -> None:
    result = compare(
        "body\n", "body\n", generated=[exact("vnext_note", "Rules marked.")]
    )
    assert result.generated_missing == [("vnext_note", "Rules marked.")]
    assert not result.ok


def test_generated_line_must_match_the_manifest_exactly() -> None:
    kinds = [exact("section_map_row", "| `a.b` | [a/b.md](a/b.md) | Title |")]
    wrong_title = "| `a.b` | [a/b.md](a/b.md) | A different title |"
    assert not compare("body\n", f"body\n{wrong_title}\n", generated=kinds).ok
    wrong_path = "| `a.b` | [a/c.md](a/c.md) | Title |"
    assert not compare("body\n", f"body\n{wrong_path}\n", generated=kinds).ok


def test_link_list_item_with_an_unknown_title_is_not_allowed() -> None:
    kinds = [
        exact("validation_index", "- [Identity](common/identity.md#validation-rules)")
    ]
    assert compare("body\n", "body\n- [Identity](x.md#y)\n", generated=kinds).ok
    assert not compare(
        "body\n", "body\n- [Anything else](x.md#y)\n", generated=kinds
    ).ok


def test_predicate_kind_is_capped_by_its_count() -> None:
    kind = csv_.Generated(
        "resize_methods", accepts=lambda t: t.startswith("Each"), count=1
    )
    assert compare("body\n", "body\nEach one.\n", generated=[kind]).ok
    assert not compare("body\n", "body\nEach one.\nEach two.\n", generated=[kind]).ok
    assert not compare("body\n", "body\n", generated=[kind]).ok


def test_invented_sentence_is_not_an_allowed_addition() -> None:
    assert not compare("body\n", "body\nMoved to the new place.\n").ok


# ---------------------------------------------------------------- old side and headings


def test_excluded_lines_are_dropped_from_the_old_side() -> None:
    old = csv_.classify_lines(csv_.split_text("a\nb\n\nc\n"), "old.md")
    kept, removed = csv_.old_side(old, [(2, 2)])
    assert [line.text for line in kept] == ["a", "c"]
    assert removed["content"] == 1
    kept, _ = csv_.old_side(old, [(2, 2)], moved_out=[1])
    assert [line.text for line in kept] == ["c"]


def test_github_anchors() -> None:
    headings = [
        "Overview",
        "Overview",
        "`$ref` — reference another file",
        "`sizes.<size>.onnx.batch_artifacts`",
        "Changes in this revision (`vNEXT`)",
    ]
    assert csv_.github_anchors(headings) == [
        "overview",
        "overview-1",
        "ref--reference-another-file",
        "sizessizeonnxbatch_artifacts",
        "changes-in-this-revision-vnext",
    ]


def test_index_check_requires_every_heading_in_order() -> None:
    old = csv_.classify_lines(csv_.split_text("# A\n\n## B\n\n### C\n"), "old")
    same = csv_.classify_lines(csv_.split_text("# A\n\n## B\n\nMoved.\n\n### C\n"), "i")
    swapped = csv_.classify_lines(csv_.split_text("# A\n\n### C\n\n## B\n"), "i")
    shallow = csv_.classify_lines(csv_.split_text("# A\n\n## B\n\n## C\n"), "i")
    assert not csv_.check_index_headings(old, same).failures
    assert csv_.check_index_headings(old, swapped).failures
    assert csv_.check_index_headings(old, shallow).failures
    assert csv_.check_index_headings(old, None).failures


def test_heading_in_fence_is_not_an_index_heading() -> None:
    old = csv_.classify_lines(csv_.split_text("# A\n\n```yaml\n# note\n```\n"), "old")
    assert [text for _, text, _ in csv_.headings_of(old)] == ["A"]


# ---------------------------------------------------------------- rule IDs


def spec_for(rule_count: int, section_id: str = "pre.fit") -> csv_.FileSpec:
    return csv_.FileSpec(
        path="x.md",
        front_matter={"id": section_id, "title": "T", "kind": "preprocessor"},
        title="T",
        nav_texts=(),
        rule_count=rule_count,
        has_legacy=False,
        generated=(),
    )


def rule_problems(text: str, rule_count: int) -> list[str]:
    classified = csv_.classify_lines(csv_.split_text(text), "x.md")
    return csv_.rule_id_problems(spec_for(rule_count), classified)


def test_rule_ids_in_order_pass() -> None:
    text = "- [ ] `V-pre.fit-1` a\n- [ ] `V-pre.fit-2` b\n"
    assert rule_problems(text, 2) == []


@pytest.mark.parametrize(
    "text",
    [
        "- [ ] `V-pre.fit-2` a\n- [ ] `V-pre.fit-1` b\n",  # out of order
        "- [ ] `V-pre.fit-1` a\n- [ ] `V-pre.fit-3` b\n",  # gap
        "- [ ] `V-pre.fit-1` a\n- [ ] b\n",  # unlabelled
        "- [ ] `V-other.id-1` a\n- [ ] `V-other.id-2` b\n",  # wrong id
        "- [ ] `V-pre.fit-1` a\n",  # fewer than the manifest lists
    ],
)
def test_bad_rule_ids_fail(text: str) -> None:
    assert rule_problems(text, 2)


# ---------------------------------------------------------------- command line


MANIFEST = """\
source: specs/sidecar-spec.md
excluded:
  - {lines: [3, 3], reason: "label"}
anchors:
  1: {file: README.md, heading: null}
  5: {file: part.md, heading: "Part"}
files:
  - path: part.md
    front_matter: {id: a.part, title: "Section", kind: format}
    title: "Section"
    blocks:
      - {h: 2, text: "Part"}
      - {lines: [7, 7]}
      - {nav: "See [README](README.md)."}
      - {h: 2, text: "Validation rules"}
      - {rules: [9]}
"""

OLD = """\
# Spec

**Label**

## Part

Body line.

- [ ] Rule one.
"""


def build_repo(root: Path, part_body: str) -> None:
    sidecar = root / "specs" / "sidecar"
    sidecar.mkdir(parents=True)
    (root / "specs" / "sidecar-spec.md").write_text(
        "# Spec\n\nThis specification is split into section files. "
        "Start at [the section map](sidecar/README.md).\n\n## Part\n\n"
        "Moved to [part.md](sidecar/part.md#part).\n",
        encoding="utf-8",
    )
    (sidecar / "part.md").write_text(part_body, encoding="utf-8")


GOOD_PART = (
    '---\nid: a.part\ntitle: "Section"\nkind: format\n---\n\n# Section\n\n## Part\n\n'
    "Body line.\n\nSee [README](README.md).\n\n## Validation rules\n\n"
    "- [ ] `V-a.part-1` Rule one.\n"
)


def run_cli(tmp_path: Path, part_body: str, *extra: str) -> int:
    old, manifest = tmp_path / "old.md", tmp_path / "manifest.yaml"
    old.write_text(OLD, encoding="utf-8")
    manifest.write_text(MANIFEST, encoding="utf-8")
    repo = tmp_path / "repo"
    build_repo(repo, part_body)
    argv = ["--old", str(old), "--manifest", str(manifest), "--repo", str(repo), *extra]
    return csv_.main(argv)


def test_cli_passes_on_a_faithful_split(tmp_path: Path, capsys) -> None:
    assert run_cli(tmp_path, GOOD_PART) == 0
    assert "RESULT: PASS" in capsys.readouterr().out


def test_cli_fails_on_a_reworded_line(tmp_path: Path, capsys) -> None:
    assert run_cli(tmp_path, GOOD_PART.replace("Body line.", "Body line!")) == 1
    out = capsys.readouterr().out
    assert "missing from new files, old line 7" in out
    assert "specs/sidecar/part.md" in out


def test_cli_fails_on_a_bad_front_matter_key(tmp_path: Path) -> None:
    assert run_cli(tmp_path, GOOD_PART.replace("kind: format", "kind: schema")) == 1


def test_cli_reports_a_missing_manifest(tmp_path: Path) -> None:
    argv = ["--old", str(tmp_path / "o.md"), "--manifest", str(tmp_path / "m.yaml")]
    assert csv_.main([*argv, "--repo", str(tmp_path)]) == 2


# ---------------------------------------------------------------- manifest-driven checks
#
# A tiny old spec, a manifest for it and a "split" of it that the tests then damage.

OLD_MD = """\
# Spec

## Part

**Label:**

See [Part](#part) and [the other](other.md#x).

| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |

```text
code
```

## Other

- [ ] Rule one.
"""
# line numbers: 1 H1, 3 H2 Part, 5 label, 7 links, 9-10 header+separator, 11-12 rows,
# 14-16 fence, 18 H2 Other, 20 rule

BASE_MANIFEST = """\
source: specs/sidecar-spec.md
excluded: []
link_overrides: []
anchors:
  1: {file: README.md, heading: null}
  3: {file: part.md, heading: "Part"}
  18: {file: part.md, heading: "Other"}
files:
  - path: README.md
    front_matter: null
    title: "Spec"
    blocks:
      - {nav: "Start at [part](part.md)."}
  - path: part.md
    front_matter: {id: a.part, title: "Part file", kind: format}
    blocks:
      - {h: 2, text: "Part"}
      - {line: 5}
      - {line: 7}
      - {header: [9, 10]}
      - {line: 11}
      - {header: [9, 10]}
      - {line: 12}
      - {lines: [14, 16]}
      - {h: 2, text: "Other"}
      - {rules: [20]}
"""

GOOD_PART_MD = """\
---
id: a.part
title: Part file
kind: format
---

# Part file

## Part

**Label:**

See [Part](#part) and [the other](../other.md#x).

| A | B |
|---|---|
| 1 | 2 |

| A | B |
|---|---|
| 3 | 4 |

```text
code
```

## Other

- [ ] `V-a.part-1` Rule one.
"""


def load_mini(tmp_path: Path, part: str = GOOD_PART_MD, manifest: str = BASE_MANIFEST):
    """(old, manifest, side) for the mini spec; `part` is the text of part.md."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(manifest, encoding="utf-8")
    loaded = csv_.load_manifest(manifest_path)
    old = csv_.classify_lines(csv_.split_text(OLD_MD), "old")
    side = csv_.NewSide()
    readme = csv_.classify_lines(
        csv_.split_text("# Spec\n\nStart at [part](part.md).\n"),
        "specs/sidecar/README.md",
    )
    classified_part = csv_.classify_lines(
        csv_.split_text(part), "specs/sidecar/part.md"
    )
    side.files = [readme, classified_part]
    side.by_manifest_path = {"README.md": readme, "part.md": classified_part}
    return old, loaded, side


def problems_of(
    tmp_path: Path, part: str = GOOD_PART_MD, manifest: str = BASE_MANIFEST
):
    old, loaded, side = load_mini(tmp_path, part, manifest)
    skipped, _ = csv_.skipped_line_problems(old, loaded, side, set(), "split")
    placement = csv_.check_placement_and_links(old, side, loaded, "split").failures
    tables = csv_.check_tables(side).failures
    return skipped, placement, tables


def test_mini_split_is_clean(tmp_path: Path) -> None:
    assert problems_of(tmp_path) == ([], [], [])


def test_lost_bold_label_is_detected(tmp_path: Path) -> None:
    skipped, _, _ = problems_of(tmp_path, GOOD_PART_MD.replace("**Label:**\n\n", ""))
    assert any(
        "missing from new files, bold label" in p and "**Label:**" in p for p in skipped
    )


def test_invented_bold_label_is_detected(tmp_path: Path) -> None:
    skipped, _, _ = problems_of(
        tmp_path, GOOD_PART_MD.replace("**Label:**", "**Label:**\n\n**New:**")
    )
    assert any("unexpected bold label" in p and "**New:**" in p for p in skipped)


def test_table_left_without_header_and_separator_is_detected(tmp_path: Path) -> None:
    # Both the header and the separator of the first table are gone: the rows would render as text.
    part = GOOD_PART_MD.replace("| A | B |\n|---|---|\n| 1 | 2 |", "| 1 | 2 |", 1)
    skipped, _, tables = problems_of(tmp_path, part)
    assert any("missing from new files, table header" in p for p in skipped)
    assert any("missing from new files, separator" in p for p in skipped)
    assert any("does not start with a header row" in p for p in tables)


def test_two_tables_joined_into_one_is_detected(tmp_path: Path) -> None:
    part = GOOD_PART_MD.replace("| 1 | 2 |\n\n| A | B |", "| 1 | 2 |\n| A | B |")
    _, _, tables = problems_of(tmp_path, part)
    assert any("second separator row" in p for p in tables)


def test_undeclared_header_repeat_is_detected(tmp_path: Path) -> None:
    manifest = BASE_MANIFEST.replace(
        "      - {header: [9, 10]}\n      - {line: 12}", "      - {line: 12}"
    )
    skipped, _, _ = problems_of(tmp_path, GOOD_PART_MD, manifest)
    assert any("unexpected table header" in p for p in skipped)
    assert any("unexpected separator" in p for p in skipped)


def test_lost_fence_delimiter_is_detected(tmp_path: Path) -> None:
    skipped, _, _ = problems_of(
        tmp_path, GOOD_PART_MD.replace("```text\ncode\n```", "code")
    )
    assert any("missing from new files, fence" in p for p in skipped)


def test_table_problems_cover_blank_lines_and_cells() -> None:
    def run(text: str) -> list[str]:
        return csv_.table_problems(csv_.classify_lines(csv_.split_text(text), "t.md"))

    assert run("# T\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\ntext\n") == []
    assert any(
        "not preceded by a blank line" in p
        for p in run("# T\ntext\n| A | B |\n|---|---|\n| 1 | 2 |\n")
    )
    assert any(
        "line directly after a table" in p
        for p in run("# T\n\n| A | B |\n|---|---|\n| 1 | 2 |\ntext\n")
    )
    assert any(
        "different cell counts" in p
        for p in run("# T\n\n| A | B |\n|---|\n| 1 | 2 |\n")
    )
    fenced = "# T\n\n```text\n| not a table\n```\n"
    assert run(fenced) == []
    assert run("# T\n\n| A \\| B | C |\n|---|---|\n| 1 | 2 |\n") == []


def test_link_to_the_wrong_existing_target_is_detected(tmp_path: Path) -> None:
    part = GOOD_PART_MD.replace("(../other.md#x)", "(../other.md#y)")
    _, placement, _ = problems_of(tmp_path, part)
    assert any(
        "link other.md#x became ../other.md#y, expected ../other.md#x" in p
        for p in placement
    )
    part = GOOD_PART_MD.replace("[Part](#part)", "[Part](#other)")
    _, placement, _ = problems_of(tmp_path, part)
    assert any("link #part became #other, expected #part" in p for p in placement)


def test_link_override_wins_over_the_anchor_rule(tmp_path: Path) -> None:
    manifest = BASE_MANIFEST.replace(
        "link_overrides: []",
        'link_overrides:\n  - {line: 7, from: "#part", to: "../elsewhere.md"}',
    )
    _, placement, _ = problems_of(tmp_path, GOOD_PART_MD, manifest)
    assert any(
        "link #part became #part, expected ../elsewhere.md" in p for p in placement
    )
    part = GOOD_PART_MD.replace("[Part](#part)", "[Part](../elsewhere.md)")
    assert problems_of(tmp_path, part, manifest)[1] == []


def test_declared_nav_line_with_a_wrong_target_is_detected(tmp_path: Path) -> None:
    old, loaded, side = load_mini(tmp_path)
    readme = csv_.classify_lines(
        csv_.split_text("# Spec\n\nStart at [part](other.md).\n"),
        "specs/sidecar/README.md",
    )
    side.by_manifest_path["README.md"] = readme
    failures = csv_.check_placement_and_links(old, side, loaded, "split").failures
    assert any("declared {nav} line is not in the file verbatim" in p for p in failures)


def test_copied_line_in_the_wrong_order_is_detected(tmp_path: Path) -> None:
    part = GOOD_PART_MD.replace(
        "**Label:**\n\nSee [Part](#part) and [the other](../other.md#x).\n",
        "See [Part](#part) and [the other](../other.md#x).\n\n**Label:**\n",
    )
    _, placement, _ = problems_of(tmp_path, part)
    assert any(
        "is not in this file after the previous copied line" in p for p in placement
    )


def test_generated_kinds_follow_the_manifest(tmp_path: Path) -> None:
    manifest = BASE_MANIFEST.replace(
        '      - {nav: "Start at [part](part.md)."}',
        "      - {generated: section_map_format}\n      - {generated: validation_index}",
    )
    _, loaded, _ = load_mini(tmp_path, manifest=manifest)
    kinds = {k.kind: k for k in csv_.generated_kinds(loaded, "split")[0]}
    assert kinds["section_map_row"].lines == Counter(
        {"| `a.part` | [part.md]() | Part file |": 1}
    )
    assert kinds["validation_index"].lines == Counter({"- [Part file]()": 1})
    assert kinds["index_moved"].lines == Counter({"Moved to [part.md]().": 2})
    assert not kinds["legacy_index"].lines  # no block asks for it
    examples = csv_.generated_kinds(loaded, "examples")[0][-1]
    assert examples.kind == "example_sidecar_link"


def test_resize_methods_line_needs_exactly_the_resize_sections(tmp_path: Path) -> None:
    text = """source: s.md
excluded: []
anchors: {1: {file: README.md, heading: null}}
files:
  - path: pre/resize-fit.md
    front_matter: {id: pre.resize.fit, title: Fit, kind: preprocessor}
    blocks: [{h: 3, text: Inverse}, {generated: resize_methods}]
  - path: pre/resize-none.md
    front_matter: {id: pre.resize.none, title: Nothing, kind: preprocessor}
    blocks: [{h: 3, text: Inverse}]
"""
    path = tmp_path / "m.yaml"
    path.write_text(text, encoding="utf-8")
    kinds = {
        k.kind: k for k in csv_.generated_kinds(csv_.load_manifest(path), "split")[0]
    }
    accepts = kinds["resize_methods"].accepts
    assert kinds["resize_methods"].count == 1
    assert accepts("Each `method` has its own section: [`fit`](), [`none`]().")
    assert accepts("Each `method` has its own section: [`none`](), [`fit`]()")
    assert not accepts("Each `method` has its own section: [`fit`]().")
    assert not accepts(
        "Each `method` has its own section: [`fit`](), [`none`](). And more text."
    )
    assert not accepts(
        "Each `method` has its own section: [`fit`](), [`none`](), prose [`x`]()."
    )


def test_moved_to_label_and_target_must_match(tmp_path: Path) -> None:
    old, loaded, _ = load_mini(tmp_path)
    repo = tmp_path / "repo"
    (repo / "specs" / "sidecar").mkdir(parents=True)
    (repo / "specs" / "sidecar" / "part.md").write_text(GOOD_PART_MD, encoding="utf-8")
    (repo / "specs" / "sidecar" / "README.md").write_text("# Spec\n", encoding="utf-8")

    def problems(index_text: str) -> list[str]:
        index = csv_.classify_lines(
            csv_.split_text(index_text), "specs/sidecar-spec.md"
        )
        return csv_.moved_to_problems(old, index, loaded, repo)

    good = "# Spec\n\n## Part\n\nMoved to [part.md](sidecar/part.md#part).\n\n## Other\n\nMoved to [part.md](sidecar/part.md#other).\n"
    assert problems(good) == []
    assert any(
        "link text is" in p
        for p in problems(
            good.replace(
                "[part.md](sidecar/part.md#part)",
                "[elsewhere.md](sidecar/part.md#part)",
            )
        )
    )
    assert any(
        "anchor #other should be #part" in p
        for p in problems(good.replace("part.md#part", "part.md#other", 1))
    )
    assert any(
        "link goes to" in p
        for p in problems(
            good.replace("sidecar/part.md#other", "sidecar/README.md#other")
        )
    )


def test_missing_inventory_is_an_expected_exception_only_when_allowed(
    tmp_path: Path,
) -> None:
    text = "\n".join(f"line {n}" for n in range(1, 1513))
    old = csv_.classify_lines(csv_.split_text(text), "old")
    warnings, info = csv_.inventory_warnings(old, tmp_path)
    assert warnings and not info
    warnings, info = csv_.inventory_warnings(old, tmp_path, allow_missing=True)
    assert not warnings and "expected exception" in info[0]
    (tmp_path / "specs" / "sidecar").mkdir(parents=True)
    (tmp_path / "specs" / "sidecar" / "inventory.yaml").write_text(
        "other\n", encoding="utf-8"
    )
    assert csv_.inventory_warnings(old, tmp_path, allow_missing=True)[
        0
    ]  # present but wrong: still a warning


def test_cli_fails_when_a_bold_label_is_lost(tmp_path: Path, capsys) -> None:
    old = tmp_path / "old.md"
    old.write_text(OLD_MD, encoding="utf-8")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(BASE_MANIFEST, encoding="utf-8")
    repo = tmp_path / "repo"
    sidecar = repo / "specs" / "sidecar"
    sidecar.mkdir(parents=True)
    (sidecar / "README.md").write_text(
        "# Spec\n\nStart at [part](part.md).\n", encoding="utf-8"
    )
    index = (
        "# Spec\n\nThis specification is split into section files. Start at [the section map](sidecar/README.md).\n\n"
        "## Part\n\nMoved to [part.md](sidecar/part.md#part).\n\n## Other\n\nMoved to [part.md](sidecar/part.md#other).\n"
    )
    (repo / "specs" / "sidecar-spec.md").write_text(index, encoding="utf-8")
    (sidecar / "part.md").write_text(GOOD_PART_MD, encoding="utf-8")
    argv = [
        "--old",
        str(old),
        "--manifest",
        str(manifest),
        "--repo",
        str(repo),
        "--strict",
    ]
    assert csv_.main(argv) == 0, capsys.readouterr().out
    (sidecar / "part.md").write_text(
        GOOD_PART_MD.replace("**Label:**\n\n", ""), encoding="utf-8"
    )
    assert csv_.main(argv) == 1
    assert "missing from new files, bold label" in capsys.readouterr().out


def test_example_links_must_point_at_their_own_yaml(tmp_path: Path) -> None:
    text = """\
source: s.md
excluded: []
anchors: {1: {file: README.md, heading: null}}
files:
  - path: examples/README.md
    front_matter: null
    title: Examples
    blocks: []
examples:
  - {fence: [10, 20], path: examples/a/one.yaml}
  - {fence: [30, 40], path: examples/b/two.yaml}
"""
    path = tmp_path / "m.yaml"
    path.write_text(text, encoding="utf-8")
    manifest = csv_.load_manifest(path)

    def problems(readme: str) -> list[str]:
        classified = csv_.classify_lines(
            csv_.split_text(readme), "specs/sidecar/examples/README.md"
        )
        side = csv_.NewSide()
        side.by_manifest_path = {"examples/README.md": classified}
        return csv_.example_link_problems(side, manifest)

    good = "# E\n\nSidecar: [`one.yaml`](a/one.yaml).\n\nSidecar: [`two.yaml`](b/two.yaml).\n"
    assert problems(good) == []
    assert problems(
        good.replace("(a/one.yaml)", "(b/two.yaml)")
    )  # text says one, target is two
    reordered = "# E\n\nSidecar: [`two.yaml`](b/two.yaml).\n\nSidecar: [`one.yaml`](a/one.yaml).\n"
    assert problems(reordered)
    assert problems(
        good.replace("Sidecar: [`two.yaml`](b/two.yaml).\n", "")
    )  # a link is missing
