"""Each change of a normative heading or a `V-` rule comes with a summary row and a `Row` line.

ADR-6GE2 item 4 (it restates the rule of ADR-SS2E item 2, item 6): a spec version is the
skellytracker version, in SemVer, that first releases a spec change. Each `### X.Y.Z` heading under
`## Revisions` of `specs/model-sidecar/changelog.md` is one version. Its first line is
`- Released: no.` or `- Released: yes.`. Each content commit appends one line
``- Row N: `<fingerprint>`.`` under the open target, the one unreleased version, and adds row `N`
to the summary of changes. The session of a skellytracker pre-release appends
`- Pre-release X.Y.Z-<tag>: row N.` (ADR-6GE2 item 7).

A test cannot see the commit that it runs in, so the baseline is a value in the changelog: the
fingerprint of the last `Row` line. The fingerprint is the SHA-256 of the sorted heading lines and
`V-` rule lines of the section files (`format/`, `common/`, `pre/`, `post/`), outside code blocks.
The lines are sorted, so a move of a section or a rule does not change the value. A checked rule
counts as unchecked, so the implementation of a rule does not change the value either.

A commit that changes a heading or a rule thus fails here until it adds a summary row and a `Row`
line with the new fingerprint. The failure message gives the new fingerprint. After a release, the
commit must first add a new version heading.

The test sees only the headings and the `V-` rule lines. Each `V-` rule is one line. A content
commit that changes other normative text or `status.spec` must still add a summary row and a `Row`
line. Review checks it.

shortcut: the test cannot see an edit of an earlier line or of a released version; review stops it.
Compare with the parent commit in CI if that edit happens.
"""

import hashlib
import re
from pathlib import Path
from typing import NamedTuple

import pytest
import sidecar_trace as st

CHANGELOG = st.spec_dir() / "changelog.md"
SUMMARY_ROW = re.compile(r"^\| (\d+) \|", re.MULTILINE)
NUMBER = r"(\d+)\.(\d+)\.(\d+)"
RELEASED = re.compile(r"- Released: (yes|no)\.")
ROW = re.compile(r"- Row (\d+): `([0-9a-f]{64})`\.")
PRE_RELEASE = re.compile(
    rf"- Pre-release {NUMBER}-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*): row (\d+)\."
)


class Version(NamedTuple):
    number: tuple[int, int, int]
    released: bool
    rows: list[tuple[int, str]]
    # (number, tag, row, count of `Row` lines above it)
    pre_releases: list[tuple[tuple[int, int, int], str, int, int]]


def normative_fingerprint(paths: list[Path]) -> str:
    """Return the SHA-256 of the sorted heading lines and `V-` rule lines of the section files."""
    lines = []
    for path in paths:
        _, body = st.parse_front_matter(path.read_text(encoding="utf-8"), path.name)
        fenced = False
        for line in body.splitlines():
            if line.startswith("```"):
                fenced = not fenced
            elif not fenced and (line.startswith("#") or st.RULE_LINE.match(line)):
                lines.append(re.sub(r"^- \[[xX]\]", "- [ ]", line.rstrip()))
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def parse_versions(revisions_text: str) -> list[Version]:
    """Return each `### X.Y.Z` version of the `## Revisions` text, in text order."""
    found = []
    for block in re.split(r"^### ", revisions_text, flags=re.MULTILINE)[1:]:
        heading, *lines = block.splitlines()
        number = re.fullmatch(NUMBER, heading)
        assert number, f"`### {heading}` is not a version `X.Y.Z`"
        items = [line for line in lines if line.startswith("- ")]
        released = RELEASED.fullmatch(items[0]) if items else None
        assert released, (
            f"the first line of `### {heading}` must be `- Released: yes.` or `no.`"
        )
        rows, pre_releases = [], []
        for item in items[1:]:
            if row := ROW.fullmatch(item):
                rows.append((int(row[1]), row[2]))
            elif pre := PRE_RELEASE.fullmatch(item):
                pre_number = (int(pre[1]), int(pre[2]), int(pre[3]))
                pre_releases.append((pre_number, pre[4], int(pre[5]), len(rows)))
            else:
                raise AssertionError(f"`### {heading}` has an unknown line: {item}")
        assert rows, f"`### {heading}` must have a `- Row N:` line"
        found.append(
            Version(
                tuple(int(n) for n in number.groups()),
                released[1] == "yes",
                rows,
                pre_releases,
            )
        )
    return found


def versions() -> list[Version]:
    text = CHANGELOG.read_text(encoding="utf-8").split("\n## Revisions\n", 1)[1]
    return parse_versions(text.split("\n## ", 1)[0])


def show(number: tuple[int, int, int]) -> str:
    return ".".join(map(str, number))


def test_the_versions_ascend_and_only_the_last_can_be_unreleased() -> None:
    found = versions()
    numbers = [v.number for v in found]
    assert numbers == sorted(set(numbers)), "the version headings must ascend as SemVer"
    assert all(v.released for v in found[:-1]), (
        "only the last version can be unreleased"
    )


def test_the_rows_rise_and_each_pre_release_names_an_earlier_row() -> None:
    found = versions()
    rows = [n for v in found for n, _ in v.rows]
    assert rows == sorted(set(rows)), "each `- Row N:` line must name a new, higher row"
    for v in found:
        for number, tag, row, above in v.pre_releases:
            name = f"{show(number)}-{tag}"
            assert number == v.number, (
                f"pre-release {name} is under `### {show(v.number)}`"
            )
            assert row in [n for n, _ in v.rows[:above]], (
                f"pre-release {name} must name the row of a `- Row` line above it"
            )


def test_the_last_row_line_holds_the_last_row_and_the_fingerprint() -> None:
    *_, last = versions()
    row, recorded = last.rows[-1]
    rows = [int(n) for n in SUMMARY_ROW.findall(CHANGELOG.read_text(encoding="utf-8"))]
    current = normative_fingerprint(st.section_files())
    if last.released:
        action = (
            "add a new version heading with `- Released: no.` and a `- Row N:` line"
        )
    else:
        action = f"append a `- Row N:` line under `### {show(last.number)}`"
    message = (
        f"the last `- Row` line does not match the changelog: add a summary row and {action}, "
        f"with N = the new highest summary row and the fingerprint {current}"
    )
    assert max(rows) == row, message
    assert recorded == current, message


def test_the_parse_reads_the_version_lines() -> None:
    fp_a, fp_b = "a" * 64, "b" * 64
    text = (
        "Prose.\n\n### 2.0.0\n\n- Released: yes.\n"
        f"- Row 30: `{fp_a}`.\n- Pre-release 2.0.0-rc.1: row 30.\n\nA paragraph.\n\n"
        f"### 2.1.0\n\n- Released: no.\n- Row 31: `{fp_b}`.\n"
    )
    assert parse_versions(text) == [
        Version((2, 0, 0), True, [(30, fp_a)], [((2, 0, 0), "rc.1", 30, 1)]),
        Version((2, 1, 0), False, [(31, fp_b)], []),
    ]
    for bad in (
        "### 1.0\n\n- Released: no.\n",
        f"### 2.0.0\n\n- Row 30: `{fp_a}`.\n",
        "### 2.0.0\n\n- Released: no.\n- Last row: 30.\n",
        "### 2.0.0\n\n- Released: no.\n",
    ):
        with pytest.raises(AssertionError):
            parse_versions(bad)


def test_the_fingerprint_ignores_order_checkboxes_and_code(tmp_path: Path) -> None:
    page = tmp_path / "a.md"

    def fingerprint(body: str) -> str:
        page.write_text("---\nid: a\n---\n" + body, encoding="utf-8")
        return normative_fingerprint([page])

    base = fingerprint("# A\n\n- [ ] `V-ab-1` x\n- [ ] `V-ab-2` y\n")
    assert fingerprint("# A\n\n- [x] `V-ab-2` y\n- [ ] `V-ab-1` x\n\nprose\n") == base
    assert (
        fingerprint(
            "# A\n\n```yaml\n# comment\n```\n- [ ] `V-ab-1` x\n- [ ] `V-ab-2` y\n"
        )
        == base
    )
    assert fingerprint("# A\n\n- [ ] `V-ab-1` x\n- [ ] `V-ab-2` z\n") != base
    assert fingerprint("# B\n\n- [ ] `V-ab-1` x\n- [ ] `V-ab-2` y\n") != base
