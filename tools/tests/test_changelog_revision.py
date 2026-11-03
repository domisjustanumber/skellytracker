"""Each change of a normative heading or a `V-` rule comes with a new revision and a changelog row.

ADR-SS2E item 2: each content commit increments the spec revision `1.N` and adds a row to the
summary of changes of `specs/model-sidecar/changelog.md`. A test cannot see the commit that it runs
in, so the baseline is a value in the changelog: the `Fingerprint` of the latest revision under
`## Revisions`. The fingerprint is the SHA-256 of the sorted heading lines and `V-` rule lines of
the section files (`format/`, `common/`, `pre/`, `post/`), outside code blocks. The lines are
sorted, so a move of a section or a rule does not change the value. A checked rule counts as
unchecked, so the implementation of a rule does not change the value either.

A commit that changes a heading or a rule thus fails here until it adds a revision with the new
fingerprint. That revision must give a higher `Last row`, and the summary of changes must have that
row. The failure message gives the new fingerprint.

The test sees only the headings and the `V-` rule lines. Each `V-` rule is one line. A content
commit that changes other normative text or `status.spec` must still add a revision and a summary
row. Review checks it.

shortcut: the test cannot see an edit of the fields of an existing revision; review stops it. Compare
with the parent commit in CI if that edit happens.
"""

import hashlib
import re
from pathlib import Path

import sidecar_trace as st

CHANGELOG = st.spec_dir() / "changelog.md"
REVISION = re.compile(
    r"^### (\d+)\.(\d+)\n\n- Last row: (\d+)\.\n- Fingerprint: `([0-9a-f]{64})`\.$",
    re.MULTILINE,
)
SUMMARY_ROW = re.compile(r"^\| (\d+) \|", re.MULTILINE)


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


def revisions() -> list[tuple[int, int, int, str]]:
    """Return (major, minor, last row, fingerprint) of each revision, in text order."""
    text = CHANGELOG.read_text(encoding="utf-8").split("\n## Revisions\n", 1)[1]
    found = [(int(a), int(b), int(r), f) for a, b, r, f in REVISION.findall(text)]
    assert len(found) == len(re.findall(r"^### ", text, re.MULTILINE)), (
        "each revision heading must be followed by its `Last row` and `Fingerprint` lines"
    )
    return found


def test_the_revisions_count_up_from_1_0() -> None:
    found = revisions()
    assert [(a, b) for a, b, _, _ in found] == [(1, n) for n in range(len(found))]


def test_each_revision_adds_rows_and_the_latest_holds_the_last_row() -> None:
    last_rows = [r for _, _, r, _ in revisions()]
    assert last_rows == sorted(set(last_rows)), "each revision must add a summary row"
    rows = [int(n) for n in SUMMARY_ROW.findall(CHANGELOG.read_text(encoding="utf-8"))]
    assert max(rows) == last_rows[-1]


def test_the_latest_revision_records_the_normative_fingerprint() -> None:
    *_, (major, minor, _, recorded) = revisions()
    current = normative_fingerprint(st.section_files())
    assert recorded == current, (
        f"the normative text differs from revision {major}.{minor}: add a revision and a summary "
        f"row, with the fingerprint {current}"
    )


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
