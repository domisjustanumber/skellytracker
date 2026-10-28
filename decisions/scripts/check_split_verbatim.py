#!/usr/bin/env python3
"""Prove that the sidecar specification split is move-only.

The sidecar spec used to be one Markdown file (``specs/sidecar-spec.md``). It is being split into
section files under ``specs/sidecar/`` plus a permanent index at the old path. The split may only
MOVE lines: every normative line must reappear verbatim, and the only additions allowed are
headings, link targets, rule-ID labels, front matter and declared navigation lines.

This checker reads only three inputs and never imports or reuses the generator:

* the old spec (``--old``),
* the split manifest (``--manifest``), for its ``excluded`` line ranges, its file list and blocks,
  its ``{nav}`` texts, its ``anchors`` and ``link_overrides`` and its ``examples``,
* the new files under ``--repo`` (the permanent index, every manifest ``files`` path under
  ``specs/sidecar/`` and, for ``--stage examples``, every manifest ``examples`` YAML path).

Line classification (applied to both sides)
    Content lines are compared as a multiset (check 0). Eight kinds of line are not content: blank
    lines, Markdown headings, YAML front matter at the top of a Markdown file, and the five
    "skipped" kinds: fence delimiter lines, table separator lines, table header lines (a line
    directly above a separator), whole-line bold labels and a ``---`` rule outside fences. Inside
    fenced code every line is content, and so is every line of a YAML example file (stage
    ``examples``). Content lines are normalized: trailing whitespace is stripped, the target of
    every Markdown link ``](...)`` outside inline code becomes ``]()`` and a rule-ID label
    ```- [ ] `V-<id>-<n>` ``` becomes ``- [ ] ``.

Comparison (check 0)
    The multiset of old content lines (minus the manifest's excluded ranges and, in stage
    ``examples``, old line 1512) must equal the multiset of new content lines after the allowed
    additions are subtracted: each manifest ``{nav}`` text once per occurrence, and the generated
    navigation lines the manifest implies, as exact lines (section-map rows with the manifest's
    ids, paths and titles, link lists with the manifest's titles, the "Moved to" lines, ...). A
    generated line the manifest implies but the files lack is a failure, as is any extra one.

    The five skipped kinds are compared as multisets too, so losing a bold label, a table header,
    a separator or a fence delimiter cannot go unnoticed. Old lines minus the excluded ones must
    equal the new lines minus the declared additions. A table header or separator may repeat only
    as the manifest declares: one copy per ``{header}`` block, one per ``{legacy}`` block (the
    header of the table that holds the legacy rows) and one per section map (generated).

Further checks
    1. The index has every old heading (same text, level and order), so the GitHub anchor sets agree.
    2. Every section file starts with front matter with exactly the keys ``id``, ``title`` and
       ``kind``, equal to the manifest values, and ids are unique.
    3. Rule IDs in each file are ``V-<id>-1`` .. ``V-<id>-n`` in order.
    4. Every table is well formed: a run of ``|`` lines starts with a header and a separator row
       with the same cell count, holds no second separator and has a blank line on both sides.
       Otherwise GitHub renders its rows as plain text or joins two tables.
    5. Every copied line sits in the file the manifest names, in the manifest's order, and each
       link in it points where the manifest says (``link_overrides`` first, else the new location
       of the old heading, else the old file path re-based). Every declared ``{nav}`` line is in
       its file verbatim, link targets included.
    6. Every "Moved to" link in the index names the manifest's file and the new heading's anchor.
    Warnings (promoted to failures by ``--strict``) cover only sanity checks the specification does
    not demand: the manifest's generated lists having the expected sizes, and old line 1512 being in
    an ``inventory.yaml`` (stage ``examples``; ``--allow-missing-inventory`` accepts that the file
    does not exist yet).

Exit status: 0 when every check passes, 1 when any check fails, 2 on unusable input.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

SIDECAR_DIR = "specs/sidecar"
DEFAULT_INDEX_PATH = "specs/sidecar-spec.md"
PROVENANCE_LINE = 1512  # old line that moves to inventory.yaml in stage "examples"
FRONT_MATTER_KEYS = ("id", "title", "kind")

SKIP_KINDS = (
    "blank",
    "heading",
    "fence",
    "separator",
    "table_header",
    "bold_label",
    "hr",
    "front_matter",
)

FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*))?$")
BOLD_LABEL = re.compile(r"^\*\*[^*].*\*\*:?$")
SEPARATOR_BODY = re.compile(r"^\s*\|?[\s:|\-]*-[\s:|\-]*$")
RULE_LABEL = re.compile(r"^(\s*- \[ \] )`V-[A-Za-z0-9_.]+-[0-9]+` ")
LABELLED_RULE = re.compile(r"^- \[ \] `V-(?P<id>[A-Za-z0-9_.]+)-(?P<n>[0-9]+)` ")
CHECKLIST_ITEM = re.compile(r"^- \[[ xX]\] ")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
FRONT_MATTER_LINE = re.compile(r"^[A-Za-z_][\w.\-]*:(\s|$)")
MOVED_TO = re.compile(r"^Moved to \[(?P<label>[^\]]+)\]\((?P<target>[^)]*)\)\.$")

LINK_TARGET_CAPTURE = re.compile(r"\]\(([^)]*)\)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
SECTION_MAP_HEADER = re.compile(r"^\|\s*Section ID\s*\|\s*File\s*\|\s*Title\s*\|$")
RESIZE_METHODS_LINE = re.compile(
    r"^Each `method` has its own section: (\[`[a-z_]+`\]\(\)(?:, \[`[a-z_]+`\]\(\))*)\.?$"
)
EXAMPLE_LINK = re.compile(r"^Sidecar: \[`([^`]+)`\]\(([^)]*)\)\.$")
INDEX_INTRO = (
    "This specification is split into section files. Start at [the section map]()."
)

# The skipped kinds that are compared as multisets (a heading is checked by the index, blank lines and
# front matter carry no content).
COMPARED_SKIPPED_KINDS = ("bold_label", "table_header", "separator", "fence", "hr")

# Sizes of the generated link lists, fixed by the manifest's `generated` descriptions.
EXPECTED_LIST_SIZES = {
    "unprojection_index": 5,
    "selection_index": 3,
    "decode_methods": 3,
}


class InputError(Exception):
    """Raised when an input file is missing or malformed (exit status 2)."""


# --------------------------------------------------------------------------------------------------
# Data types
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceLine:
    """One classified line. ``text`` is normalized for content lines and right-stripped otherwise."""

    path: str
    number: int
    kind: str  # "content" or one of SKIP_KINDS
    text: str
    raw: str
    in_fence: bool = False  # a content line between fence delimiters


@dataclass
class ClassifiedFile:
    path: str
    lines: list[SourceLine] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def of_kind(self, kind: str) -> list[SourceLine]:
        return [line for line in self.lines if line.kind == kind]


@dataclass(frozen=True)
class FileSpec:
    path: str
    front_matter: dict | None
    title: str
    nav_texts: tuple[str, ...]
    rule_count: int
    has_legacy: bool
    generated: tuple[str, ...]
    blocks: tuple[dict, ...] = ()  # the manifest blocks, in output order

    @property
    def has_rules(self) -> bool:
        return self.rule_count > 0

    @property
    def section_id(self) -> str:
        return str(self.front_matter["id"]) if self.front_matter else ""


@dataclass
class Manifest:
    source: str
    excluded: list[tuple[int, int]]
    files: list[FileSpec]
    examples: list[str]
    anchors: dict[int, dict]
    example_fences: list[tuple[int, int]] = field(default_factory=list)
    overrides: dict[tuple[int, str], str] = field(default_factory=dict)

    @property
    def section_files(self) -> list[FileSpec]:
        return [spec for spec in self.files if spec.front_matter is not None]


@dataclass
class Generated:
    """Lines of one kind of generated navigation that the manifest implies.

    ``lines`` lists the exact (normalized) lines still allowed, with multiplicity. A kind with an
    ``accepts`` predicate instead allows ``count`` lines the predicate accepts.
    """

    kind: str
    lines: Counter = field(default_factory=Counter)
    accepts: Callable[[str], bool] | None = None
    count: int = 0

    def fresh(self) -> Generated:
        return replace(self, lines=Counter(self.lines))

    def take(self, text: str, wanted: int) -> int:
        """Use up to ``wanted`` occurrences of ``text``; return how many were used."""
        if self.accepts is not None:
            used = min(wanted, self.count) if self.accepts(text) else 0
            self.count -= used
            return used
        used = min(wanted, self.lines[text])
        self.lines[text] -= used
        return used

    def unused(self) -> list[str]:
        if self.accepts is not None:
            return [f"{self.count} more line(s) of this kind"] if self.count else []
        return [text for text, n in sorted(self.lines.items()) for _ in range(n)]


@dataclass
class Comparison:
    """Result of comparing old and new content lines."""

    missing: list[tuple[str, list[SourceLine], int]] = field(default_factory=list)
    unexpected: list[tuple[str, list[SourceLine], int]] = field(default_factory=list)
    additions: Counter = field(default_factory=Counter)
    declared_nav_missing: list[str] = field(default_factory=list)
    generated_missing: list[tuple[str, str]] = field(
        default_factory=list
    )  # (kind, line)

    @property
    def ok(self) -> bool:
        return not (
            self.missing
            or self.unexpected
            or self.declared_nav_missing
            or self.generated_missing
        )


@dataclass
class CheckResult:
    name: str
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------------------------------
# Reading and classifying lines
# --------------------------------------------------------------------------------------------------


def split_text(text: str) -> list[str]:
    """Split on ``\\n`` only (so U+2028 and friends stay inside a line); drop the final empty piece."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def read_lines(path: Path) -> list[str]:
    try:
        return split_text(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"cannot read {path}: {error}") from error


def parse_fence_open(line: str) -> tuple[str, int] | None:
    """Return (marker character, run length) when ``line`` opens a fenced code block."""
    match = FENCE_OPEN.match(line)
    if not match:
        return None
    run, info = match.group(1), match.group(2)
    if run[0] == "`" and "`" in info:
        return None  # inline code, not a fence
    return run[0], len(run)


def is_fence_close(line: str, opener: tuple[str, int]) -> bool:
    match = FENCE_OPEN.match(line)
    if not match or match.group(2).strip():
        return False
    run = match.group(1)
    return run[0] == opener[0] and len(run) >= opener[1]


def is_separator(line: str) -> bool:
    return "|" in line and SEPARATOR_BODY.match(line) is not None


def front_matter_length(lines: Sequence[str]) -> int:
    """Number of lines of YAML front matter at the top (first line ``---`` to the next ``---``), else 0."""
    if not lines or lines[0].rstrip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return index + 1
    return 0


def skip_kind(line: str, next_line: str | None) -> str | None:
    """Kind of a skipped line outside fenced code, or None when the line is content."""
    if not line:
        return "blank"
    if HEADING.match(line):
        return "heading"
    if is_separator(line):
        return "separator"
    if "|" in line and next_line is not None and is_separator(next_line.rstrip()):
        return "table_header"
    if line.strip() == "---":
        return "hr"
    if BOLD_LABEL.match(line):
        return "bold_label"
    return None


def neutralize_links(text: str) -> str:
    """Replace every Markdown link target ``](...)`` with ``]()`` outside inline code spans."""
    pieces: list[str] = []
    position = 0
    for span in CODE_SPAN.finditer(text):
        pieces.append(LINK_TARGET.sub("]()", text[position : span.start()]))
        pieces.append(span.group(0))
        position = span.end()
    pieces.append(LINK_TARGET.sub("]()", text[position:]))
    return "".join(pieces)


def normalize_line(text: str) -> str:
    """Normalize a content line: strip trailing whitespace, drop a rule-ID label, neutralize links."""
    text = text.rstrip()
    text = RULE_LABEL.sub(r"\1", text)
    return neutralize_links(text)


def classify_lines(
    lines: Sequence[str], path: str, *, all_content: bool = False
) -> ClassifiedFile:
    """Classify every line of a file; ``all_content`` makes every line content (YAML example files)."""
    result = ClassifiedFile(path=path)

    def add(index: int, kind: str, text: str, in_fence: bool = False) -> None:
        result.lines.append(
            SourceLine(path, index + 1, kind, text, lines[index].rstrip(), in_fence)
        )

    start = 0 if all_content else front_matter_length(lines)
    for index in range(start):
        add(index, "front_matter", lines[index].rstrip())
    if start:
        bad = [
            i + 1
            for i in range(1, start - 1)
            if not FRONT_MATTER_LINE.match(lines[i].rstrip())
        ]
        if bad:
            result.problems.append(
                f"{path}: front matter has non-key lines at {bad[:5]} (unclosed block?)"
            )

    fence: tuple[str, int] | None = None
    fence_line = 0
    for index in range(start, len(lines)):
        stripped = lines[index].rstrip()
        if all_content:
            add(index, "content", stripped)
        elif fence is not None:
            if is_fence_close(stripped, fence):
                add(index, "fence", stripped)
                fence = None
            else:
                add(index, "content", stripped, True)
        elif (opener := parse_fence_open(stripped)) is not None:
            add(index, "fence", stripped)
            fence, fence_line = opener, index + 1
        else:
            next_line = lines[index + 1] if index + 1 < len(lines) else None
            kind = skip_kind(stripped, next_line)
            if kind is None:
                add(index, "content", normalize_line(stripped))
            else:
                add(index, kind, stripped)
    if fence is not None:
        result.problems.append(
            f"{path}: fenced code block opened at line {fence_line} is never closed"
        )
    return result


def content_lines(classified: ClassifiedFile) -> list[SourceLine]:
    return classified.of_kind("content")


def dropped_numbers(
    excluded: Iterable[tuple[int, int]], moved_out: Iterable[int] = ()
) -> set[int]:
    """Old line numbers that do not move into the new files."""
    dropped: set[int] = set(moved_out)
    for first, last in excluded:
        dropped.update(range(first, last + 1))
    return dropped


def old_side(
    old: ClassifiedFile,
    excluded: Iterable[tuple[int, int]],
    moved_out: Iterable[int] = (),
) -> tuple[list[SourceLine], Counter]:
    """Old content lines after dropping excluded ranges; also counts what was dropped, by kind."""
    dropped = dropped_numbers(excluded, moved_out)
    kept: list[SourceLine] = []
    removed: Counter = Counter()
    for line in old.lines:
        if line.number not in dropped:
            if line.kind == "content":
                kept.append(line)
        else:
            removed[line.kind] += 1
    return kept, removed


# --------------------------------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------------------------------


def _blocks_of(entry: dict) -> list[dict]:
    blocks = entry.get("blocks") or []
    return [block for block in blocks if isinstance(block, dict)]


def parse_file_spec(entry: dict) -> FileSpec:
    blocks = _blocks_of(entry)
    front = entry.get("front_matter")
    return FileSpec(
        path=str(entry["path"]),
        front_matter=front,
        title=str(front["title"] if front else entry.get("title", "")),
        nav_texts=tuple(str(block["nav"]) for block in blocks if "nav" in block),
        rule_count=sum(len(block["rules"]) for block in blocks if "rules" in block),
        has_legacy=any("legacy" in block for block in blocks),
        generated=tuple(
            str(block["generated"]) for block in blocks if "generated" in block
        ),
        blocks=tuple(blocks),
    )


def load_manifest(path: Path) -> Manifest:
    try:
        data = yaml.safe_load(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise InputError(f"cannot load manifest {path}: {error}") from error
    if not isinstance(data, dict) or "files" not in data:
        raise InputError(f"manifest {path} has no 'files' list")
    excluded = [
        (int(item["lines"][0]), int(item["lines"][1]))
        for item in data.get("excluded") or []
    ]
    return Manifest(
        source=str(data.get("source", DEFAULT_INDEX_PATH)),
        excluded=excluded,
        files=[parse_file_spec(entry) for entry in data["files"]],
        examples=[str(item["path"]) for item in data.get("examples") or []],
        anchors={
            int(line): value for line, value in (data.get("anchors") or {}).items()
        },
        example_fences=[
            (int(item["fence"][0]), int(item["fence"][1]))
            for item in data.get("examples") or []
        ],
        overrides={
            (int(item["line"]), str(item["from"])): str(item["to"])
            for item in data.get("link_overrides") or []
        },
    )


def nav_lines_of(manifest: Manifest) -> list[str]:
    """Normalized {nav} texts, one per manifest occurrence (a nav text that would be skipped is dropped)."""
    result: list[str] = []
    for spec in manifest.files:
        for text in spec.nav_texts:
            line = classify_lines([text], "nav").lines[0]
            if line.kind == "content":
                result.append(line.text)
    return result


def nav_skipped_lines_of(manifest: Manifest) -> dict[str, Counter]:
    """Normalized {nav} texts that are skipped lines (say a bold label), by skipped kind."""
    result: dict[str, Counter] = defaultdict(Counter)
    for spec in manifest.files:
        for text in spec.nav_texts:
            line = classify_lines([text], "nav").lines[0]
            if line.kind in COMPARED_SKIPPED_KINDS:
                result[line.kind][normalize_line(line.text)] += 1
    return result


def trimmed_range(old: ClassifiedFile, first: int, last: int) -> range:
    """Old lines first..last without leading and trailing blank lines (as a {lines} block copies them)."""
    while first <= last and not old.lines[first - 1].raw.strip():
        first += 1
    while last >= first and not old.lines[last - 1].raw.strip():
        last -= 1
    return range(first, last + 1)


def separator_above(old: ClassifiedFile, number: int) -> int | None:
    """Old line number of the separator row of the table that holds old line ``number``."""
    for k in range(number, 0, -1):
        line = old.lines[k - 1]
        if line.in_fence or not line.raw.startswith("|"):
            return None
        if line.kind == "separator":
            return k
    return None


def legacy_header_lines(old: ClassifiedFile, manifest: Manifest) -> tuple[int, ...]:
    """Old (header, separator) lines of the table whose rows the {legacy} blocks copy; () when none."""
    rows = [
        int(n)
        for spec in manifest.files
        for block in spec.blocks
        if "legacy" in block
        for n in block["legacy"]
    ]
    if not rows:
        return ()
    separators = {separator_above(old, n) for n in rows}
    if len(separators) != 1 or None in separators:
        raise InputError(
            "the manifest's {legacy} rows do not all belong to one table with a header row"
        )
    separator = separators.pop()
    return (separator - 1, separator)


def copied_old_lines(
    old: ClassifiedFile, blocks: Sequence[dict], legacy_header: Sequence[int]
) -> list[int]:
    """Old line numbers the blocks copy, in output order (repeated table headers included)."""
    result: list[int] = []
    for block in blocks:
        if "lines" in block:
            result.extend(trimmed_range(old, *block["lines"]))
        elif "line" in block:
            result.extend(trimmed_range(old, block["line"], block["line"]))
        elif "header" in block:
            result.extend(range(block["header"][0], block["header"][1] + 1))
        elif "rules" in block:
            result.extend(int(n) for n in block["rules"])
        elif "legacy" in block:
            result.extend(legacy_header)
            result.extend(int(n) for n in block["legacy"])
    return result


def declared_copies(
    old: ClassifiedFile, manifest: Manifest, legacy_header: Sequence[int]
) -> tuple[Counter, Counter]:
    """(repeated, covered): per old line, the {header}/{legacy} blocks that repeat it and the
    {line}/{lines} blocks that copy it."""
    repeated: Counter = Counter()
    covered: Counter = Counter()
    for spec in manifest.files:
        for block in spec.blocks:
            if "header" in block:
                repeated.update(range(block["header"][0], block["header"][1] + 1))
            elif "legacy" in block:
                repeated.update(legacy_header)
            elif "lines" in block:
                covered.update(trimmed_range(old, *block["lines"]))
            elif "line" in block:
                covered.update(trimmed_range(old, block["line"], block["line"]))
    return repeated, covered


# --------------------------------------------------------------------------------------------------
# The verbatim comparison
# --------------------------------------------------------------------------------------------------


def group_by_text(lines: Iterable[SourceLine]) -> dict[str, list[SourceLine]]:
    groups: dict[str, list[SourceLine]] = defaultdict(list)
    for line in lines:
        groups[line.text].append(line)
    return groups


def times(lines: Iterable[str], factor: int) -> Counter:
    """Counter of ``lines`` with every count multiplied by ``factor``."""
    return Counter({text: n * factor for text, n in Counter(lines).items()})


def resize_methods_of(manifest: Manifest) -> list[tuple[str, FileSpec]]:
    """(method, section) of every resize section that has an Inverse subsection."""
    return [
        (spec.section_id.rsplit(".", 1)[-1], spec)
        for spec in manifest.section_files
        if spec.section_id.startswith("pre.resize.")
        and any(b.get("text") == "Inverse" for b in spec.blocks if "h" in b)
    ]


def generated_kinds(
    manifest: Manifest, stage: str
) -> tuple[list[Generated], list[str]]:
    """The generated navigation lines the manifest implies, as exact normalized lines.

    Returns the kinds plus sanity warnings (a generated list with an unexpected size).
    """
    sections = manifest.section_files
    blocks = Counter(name for spec in manifest.files for name in spec.generated)
    methods = resize_methods_of(manifest)
    selection = [s for s in sections if s.section_id.startswith("post.det.selection.")]
    decoders = [s for s in sections if s.section_id.startswith("post.pose.decode.")]
    has_section_map = any(name.startswith("section_map_") for name in blocks)
    # The first heading is the index's own title, which has no "Moved to" line.
    anchor_files = [
        manifest.anchors[line]["file"] for line in sorted(manifest.anchors)
    ][1:]
    method_names = sorted(m for m, _ in methods)

    def listed(members: Iterable[FileSpec], name: str) -> Counter:
        return times((f"- [{s.title}]()" for s in members), blocks[name])

    def is_resize_methods_line(text: str) -> bool:
        found = RESIZE_METHODS_LINE.match(text)
        return (
            found is not None
            and sorted(re.findall(r"\[`([a-z_]+)`\]", found.group(1))) == method_names
        )

    kinds = [
        Generated(
            "section_map_row",
            times(
                (f"| `{s.section_id}` | [{s.path}]() | {s.title} |" for s in sections),
                1 if has_section_map else 0,
            ),
        ),
        Generated(
            "validation_index",
            listed([s for s in sections if s.has_rules], "validation_index"),
        ),
        Generated(
            "legacy_index",
            listed([s for s in sections if s.has_legacy], "legacy_index"),
        ),
        Generated(
            "unprojection_index",
            times(
                (f"- `{method}`: [{s.title}]()" for method, s in methods),
                blocks["unprojection_index"],
            ),
        ),
        Generated("selection_index", listed(selection, "selection_index")),
        Generated("decode_methods", listed(decoders, "decode_methods")),
        Generated("index_intro", Counter({INDEX_INTRO: 1})),
        Generated(
            "index_moved", Counter(f"Moved to [{file}]()." for file in anchor_files)
        ),
        Generated(
            "resize_methods",
            accepts=is_resize_methods_line,
            count=blocks["resize_methods"],
        ),
        Generated(
            "vnext_note",
            Counter(
                {
                    "Rules marked **(vNEXT)**: see [Validation rules]().": blocks[
                        "vnext_note"
                    ]
                }
            ),
        ),
    ]
    if stage == "examples":
        kinds.append(
            Generated(
                "example_sidecar_link",
                Counter(
                    f"Sidecar: [`{path.rsplit('/', 1)[-1]}`]()."
                    for path in manifest.examples
                ),
            )
        )
    sizes = {
        "unprojection_index": len(methods),
        "selection_index": len(selection),
        "decode_methods": len(decoders),
    }
    warnings = [
        f"generated list {name}: the manifest implies {sizes[name]} entries, expected {size}"
        for name, size in EXPECTED_LIST_SIZES.items()
        if blocks[name] and sizes[name] != size
    ]
    return kinds, warnings


def compare_lines(
    old: Sequence[SourceLine],
    new: Sequence[SourceLine],
    nav_lines: Sequence[str] = (),
    generated: Sequence[Generated] = (),
) -> Comparison:
    """Compare the old and new content-line multisets after subtracting the allowed additions."""
    result = Comparison()
    old_groups, new_groups = group_by_text(old), group_by_text(new)
    nav_budget = Counter(nav_lines)
    budgets = [kind.fresh() for kind in generated]
    for text in sorted(set(old_groups) | set(new_groups)):
        old_count, new_count = len(old_groups.get(text, ())), len(
            new_groups.get(text, ())
        )
        if old_count > new_count:
            result.missing.append((text, old_groups[text], old_count - new_count))
        elif new_count > old_count:
            extra = new_count - old_count
            declared = min(extra, nav_budget[text])
            if declared:
                result.additions["nav"] += declared
                nav_budget[text] -= declared
                extra -= declared
            for budget in budgets:
                if not extra:
                    break
                used = budget.take(text, extra)
                if used:
                    result.additions[budget.kind] += used
                    extra -= used
            if extra:
                result.unexpected.append((text, new_groups[text], extra))
    for text, remaining in sorted(nav_budget.items()):
        result.declared_nav_missing.extend([text] * remaining)
    for budget in budgets:
        result.generated_missing.extend((budget.kind, text) for text in budget.unused())
    result.missing.sort(key=lambda item: item[1][0].number)
    result.unexpected.sort(key=lambda item: (item[1][0].path, item[1][0].number))
    return result


def show(text: str) -> str:
    """Printable form of a compared line (blank lines occur inside fenced code)."""
    return text if text else "<blank line inside fenced code>"


def format_missing(
    item: tuple[str, list[SourceLine], int], unexpected_texts: Sequence[str]
) -> str:
    text, occurrences, count = item
    numbers = ", ".join(str(line.number) for line in occurrences[:6])
    more = ", ..." if len(occurrences) > 6 else ""
    detail = (
        f"old line {numbers}"
        if len(occurrences) == 1
        else f"old lines {numbers}{more} ({count} of {len(occurrences)} missing)"
    )
    hint = difflib.get_close_matches(text, unexpected_texts, n=1, cutoff=0.6)
    suffix = f"\n      closest unexpected new line: {hint[0]}" if hint else ""
    return f"missing from new files, {detail}: {show(text)}{suffix}"


def format_unexpected(item: tuple[str, list[SourceLine], int]) -> str:
    text, occurrences, count = item
    where = ", ".join(f"{line.path}:{line.number}" for line in occurrences[:6])
    more = ", ..." if len(occurrences) > 6 else ""
    extra = f" ({count} extra of {len(occurrences)})" if len(occurrences) > 1 else ""
    return f"unexpected new line{extra} at {where}{more}: {show(text)}"


def skipped_line_problems(
    old: ClassifiedFile,
    manifest: Manifest,
    side: NewSide,
    dropped: set[int],
    stage: str,
) -> tuple[list[str], list[str]]:
    """Compare the skipped kinds of line (bold labels, table headers and separators, fence delimiters,
    horizontal rules) as multisets. Returns (failures, info lines).

    Expected new lines are the old lines that were not dropped, plus the declared additions: a table
    header and its separator appear once per {header} block that repeats them (and once per {line} or
    {lines} block that copies them) and once per {legacy} block; the rows of a generated section map
    bring their own header and separator.
    """
    legacy_header = legacy_header_lines(old, manifest)
    repeated, covered = declared_copies(old, manifest, legacy_header)
    nav = nav_skipped_lines_of(manifest)
    section_maps = sum(
        1
        for spec in manifest.files
        for name in spec.generated
        if name.startswith("section_map_")
    )
    fence_delimiters = (
        {n for pair in manifest.example_fences for n in pair}
        if stage == "examples"
        else set()
    )
    problems: list[str] = []
    info: list[str] = []
    generated_tables = 0
    consumed: set[tuple[str, int]] = (
        set()
    )  # section-map separators, counted with their header
    for kind in COMPARED_SKIPPED_KINDS:
        label = kind.replace("_", " ")
        expected: Counter = Counter()
        expected_at: dict[str, list[SourceLine]] = defaultdict(list)
        for line in old.lines:
            if line.kind != kind or line.number in dropped:
                continue
            if kind == "fence" and line.number in fence_delimiters:
                continue
            text = normalize_line(line.text)
            repeats = repeated[line.number]
            expected[text] += repeats + covered[line.number] if repeats else 1
            expected_at[text].append(line)
        expected.update(nav.get(kind, Counter()))
        actual: Counter = Counter()
        actual_at: dict[str, list[SourceLine]] = defaultdict(list)
        for classified in side.files:
            if not classified.path.endswith(".md"):
                continue
            for index, line in enumerate(classified.lines):
                if line.kind != kind or (classified.path, line.number) in consumed:
                    continue
                text = normalize_line(line.text)
                if kind == "table_header" and SECTION_MAP_HEADER.match(text):
                    following = (
                        classified.lines[index + 1]
                        if index + 1 < len(classified.lines)
                        else None
                    )
                    if following is not None and following.kind == "separator":
                        generated_tables += 1
                        consumed.add((classified.path, following.number))
                        continue
                actual[text] += 1
                actual_at[text].append(line)
        for text in sorted(set(expected) | set(actual)):
            want, have = expected[text], actual[text]
            if want > have:
                where = ", ".join(str(line.number) for line in expected_at[text][:6])
                where = f"old line {where}" if where else "a declared {nav} line"
                problems.append(
                    f"missing from new files, {label} ({where}; {want - have} of {want} missing): {text}"
                )
            elif have > want:
                where = ", ".join(
                    f"{line.path}:{line.number}" for line in actual_at[text][:6]
                )
                problems.append(
                    f"unexpected {label} in the new files ({have - want} more than the old spec and "
                    f"the manifest allow) at {where}: {text}"
                )
        info.append(
            f"  {kind}: expected {sum(expected.values())}, found {sum(actual.values())}"
        )
    if generated_tables != section_maps:
        problems.append(
            f"section-map tables found: {generated_tables}, the manifest declares {section_maps}"
        )
    info.append(
        f"  generated section-map tables (header + separator): {generated_tables}"
    )
    return problems, info


def cell_count(row: str) -> int:
    """Number of cells GitHub reads in a table row (an escaped pipe does not split)."""
    text = row.strip()
    text = text[1:] if text.startswith("|") else text
    text = text[:-1] if text.endswith("|") and not text.endswith("\\|") else text
    return len(UNESCAPED_PIPE.split(text))


def table_problems(classified: ClassifiedFile) -> list[str]:
    """Problems with the tables of one Markdown file (see check 4)."""
    lines = classified.lines
    problems: list[str] = []

    def is_row(index: int) -> bool:
        line = lines[index]
        return (
            not line.in_fence
            and line.kind in ("content", "table_header", "separator")
            and line.raw.startswith("|")
        )

    index = 0
    while index < len(lines):
        if not is_row(index):
            index += 1
            continue
        end = index
        while end < len(lines) and is_row(end):
            end += 1
        run = lines[index:end]
        where = f"{classified.path}:{run[0].number}"
        if len(run) < 2 or run[0].kind != "table_header" or run[1].kind != "separator":
            problems.append(
                f"{where}: table does not start with a header row and a separator row: {run[0].raw[:70]}"
            )
        else:
            if cell_count(run[0].raw) != cell_count(run[1].raw):
                problems.append(
                    f"{where}: header row and separator row have different cell counts"
                )
            problems.extend(
                f"{classified.path}:{row.number}: second separator row inside one table "
                "(two tables joined)"
                for row in run[2:]
                if row.kind == "separator"
            )
        if index > 0 and lines[index - 1].raw.strip():
            problems.append(f"{where}: table is not preceded by a blank line")
        if end < len(lines) and lines[end].raw.strip():
            problems.append(
                f"{classified.path}:{lines[end].number}: line directly after a table is read as a table row"
            )
        index = end
    return problems


def check_tables(side: NewSide) -> CheckResult:
    result = CheckResult(
        "4. tables are well formed (header + separator, one table per run, blank lines around)"
    )
    count = 0
    for classified in side.files:
        if classified.path.endswith(".md"):
            result.failures.extend(table_problems(classified))
            count += sum(
                1
                for line in classified.lines
                if line.kind == "separator" and not line.in_fence
            )
    result.info.append(f"tables checked: {count}")
    return result


# --------------------------------------------------------------------------------------------------
# Headings and GitHub anchors
# --------------------------------------------------------------------------------------------------


def parse_heading(raw: str) -> tuple[int, str]:
    match = HEADING.match(raw)
    if not match:
        raise ValueError(f"not a heading: {raw!r}")
    text = re.sub(r"[ \t]+#+$", "", (match.group(2) or "").strip())
    return len(match.group(1)), text


def headings_of(classified: ClassifiedFile) -> list[tuple[int, str, int]]:
    """(level, text, line number) of every heading outside fenced code."""
    return [
        (*parse_heading(line.raw), line.number)
        for line in classified.of_kind("heading")
    ]


def github_slug(heading: str) -> str:
    """GitHub's anchor for one heading text, without the duplicate suffix."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "")
    kept = []
    for char in text.lower():
        category = unicodedata.category(char)
        if char in " -" or category[0] in "LMN" or category == "Pc":
            kept.append(char)
    return "".join(kept).replace(" ", "-")


def github_anchors(headings: Sequence[str]) -> list[str]:
    """Anchors of a heading sequence in order; duplicates get -1, -2, ..."""
    seen: Counter = Counter()
    anchors: list[str] = []
    for heading in headings:
        slug = github_slug(heading)
        anchors.append(slug if seen[slug] == 0 else f"{slug}-{seen[slug]}")
        seen[slug] += 1
    return anchors


def check_index_headings(
    old: ClassifiedFile, index: ClassifiedFile | None
) -> CheckResult:
    result = CheckResult(
        "1. index keeps every old heading (text, level, order, GitHub anchors)"
    )
    if index is None:
        result.failures.append("the permanent index is missing")
        return result
    old_headings = [(level, text) for level, text, _ in headings_of(old)]
    new_headings = [(level, text) for level, text, _ in headings_of(index)]
    result.info.append(
        f"old spec headings: {len(old_headings)}; index headings: {len(new_headings)}"
    )
    if old_headings != new_headings:
        old_labels = [f"{'#' * level} {text}" for level, text in old_headings]
        new_labels = [f"{'#' * level} {text}" for level, text in new_headings]
        diff = [
            d
            for d in difflib.unified_diff(
                old_labels, new_labels, "old", "index", lineterm="", n=0
            )
            if d[0] in "+-"
        ]
        result.failures.append(
            "index headings differ from the old headings (- old, + index):"
        )
        result.failures.extend(f"    {entry}" for entry in diff[:40])
    old_anchors = github_anchors([text for _, text in old_headings])
    new_anchors = github_anchors([text for _, text in new_headings])
    result.info.append(
        f"GitHub anchors: old {len(set(old_anchors))}, index {len(set(new_anchors))}"
    )
    if set(old_anchors) != set(new_anchors):
        lost = sorted(set(old_anchors) - set(new_anchors))
        gained = sorted(set(new_anchors) - set(old_anchors))
        result.failures.append(
            f"anchor sets differ: lost {lost[:10]}, gained {gained[:10]}"
        )
    return result


def moved_to_problems(
    old: ClassifiedFile, index: ClassifiedFile, manifest: Manifest, repo: Path
) -> list[str]:
    """Problems with the index 'Moved to' lines: each must name the manifest's file for that heading and
    link to it (with the new heading's anchor, or no anchor for the top of a file)."""
    warnings: list[str] = []
    old_numbers = [number for _, _, number in headings_of(old)]
    if set(old_numbers) != set(manifest.anchors):
        diff = sorted(set(old_numbers) ^ set(manifest.anchors))
        warnings.append(
            f"manifest anchors do not match the old heading lines; differing lines: {diff[:10]}"
        )
    index_lines = index.lines
    anchor_cache: dict[str, list[tuple[str, str]]] = {}
    for position, (_, _, index_number) in enumerate(headings_of(index)):
        if position == 0 or position >= len(old_numbers):
            continue
        target = manifest.anchors.get(old_numbers[position])
        following = next(
            (item for item in index_lines if item.number > index_number and item.raw),
            None,
        )
        match = MOVED_TO.match(following.raw) if following else None
        if target is None or not match:
            warnings.append(
                f"{index.path}:{index_number}: heading is not followed by a 'Moved to' link"
            )
            continue
        expected_file, expected_heading = target["file"], target["heading"]
        path, _, fragment = match.group("target").partition("#")
        if match.group("label") != expected_file:
            warnings.append(
                f"{index.path}:{following.number}: link text is {match.group('label')!r}, "
                f"manifest says {expected_file!r}"
            )
        if path != f"sidecar/{expected_file}":
            warnings.append(
                f"{index.path}:{following.number}: link goes to {path}, manifest says sidecar/{expected_file}"
            )
            continue
        if expected_heading is None:
            if fragment:
                warnings.append(
                    f"{index.path}:{following.number}: link should have no #anchor (top of file)"
                )
            continue
        if expected_file not in anchor_cache:
            file_lines = (
                read_lines(repo / SIDECAR_DIR / expected_file)
                if (repo / SIDECAR_DIR / expected_file).is_file()
                else []
            )
            titles = [
                text
                for _, text, _ in headings_of(classify_lines(file_lines, expected_file))
            ]
            anchor_cache[expected_file] = list(
                zip(titles, github_anchors(titles), strict=True)
            )
        found = [
            anchor
            for text, anchor in anchor_cache[expected_file]
            if text == expected_heading
        ]
        if not found:
            warnings.append(
                f"{expected_file}: no heading '{expected_heading}' (index line {following.number})"
            )
        elif fragment != found[0]:
            warnings.append(
                f"{index.path}:{following.number}: anchor #{fragment} should be #{found[0]}"
            )
    return warnings


def check_moved_to(
    old: ClassifiedFile, side: NewSide, manifest: Manifest, repo: Path
) -> CheckResult:
    result = CheckResult(
        "6. index 'Moved to' links name the manifest's file and the new heading's anchor"
    )
    if side.index is None:
        result.failures.append("the permanent index is missing")
        return result
    result.failures.extend(moved_to_problems(old, side.index, manifest, repo))
    result.info.append(f"manifest anchors: {len(manifest.anchors)}")
    return result


# --------------------------------------------------------------------------------------------------
# Copied lines: placement and link targets
# --------------------------------------------------------------------------------------------------


def link_targets(text: str) -> list[str]:
    """Targets of the Markdown links in ``text``, outside inline code spans."""
    targets: list[str] = []
    position = 0
    for span in CODE_SPAN.finditer(text):
        targets.extend(LINK_TARGET_CAPTURE.findall(text[position : span.start()]))
        position = span.end()
    targets.extend(LINK_TARGET_CAPTURE.findall(text[position:]))
    return targets


def relative_path(target: str, from_dir: str) -> str:
    """Path of ``target`` seen from folder ``from_dir`` (both relative to one root, no ``..`` in either)."""
    t = target.split("/")
    f = [part for part in from_dir.split("/") if part]
    i = 0
    while i < len(f) and i < len(t) - 1 and f[i] == t[i]:
        i += 1
    return "/".join([".."] * (len(f) - i) + t[i:])


def normalize_path(path: str) -> str:
    """Collapse ``.`` and ``..`` parts of a relative POSIX path."""
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == ".." and parts and parts[-1] != "..":
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


class LinkExpectations:
    """Where each link in a copied old line must point in the new files, per the manifest."""

    def __init__(self, old: ClassifiedFile, side: NewSide, manifest: Manifest) -> None:
        self.manifest = manifest
        heads = headings_of(old)
        anchors = github_anchors([text for _, text, _ in heads])
        self.old_anchor_line = {
            a: number for a, (_, _, number) in zip(anchors, heads, strict=True)
        }
        self.new_anchor: dict[str, dict[str, str]] = {}
        for path, classified in side.by_manifest_path.items():
            new_heads = headings_of(classified)
            table: dict[str, str] = {}
            for (_, text, _), anchor in zip(
                new_heads, github_anchors([t for _, t, _ in new_heads]), strict=True
            ):
                table.setdefault(
                    text, anchor
                )  # the first heading of that text, as a link finds it
            self.new_anchor[path] = table

    def expected(self, file: str, old_line: int, target: str) -> tuple[str | None, str]:
        """(expected new target, problem); the target is None when the manifest cannot say."""
        if SCHEME.match(target):
            return target, ""
        override = self.manifest.overrides.get((old_line, target))
        if override is not None:
            return override, ""
        if target.startswith("#"):
            heading_line = self.old_anchor_line.get(target[1:])
            dest = self.manifest.anchors.get(heading_line) if heading_line else None
            if dest is None:
                return (
                    None,
                    f"old link {target} matches no old heading with an `anchors` entry",
                )
            anchor = None
            if dest["heading"] is not None:
                anchor = self.new_anchor.get(dest["file"], {}).get(dest["heading"])
                if anchor is None:
                    return (
                        None,
                        f"{dest['file']} has no heading {dest['heading']!r} (old link {target})",
                    )
            if dest["file"] == file:
                return (f"#{anchor}" if anchor else file.rsplit("/", 1)[-1]), ""
            from_dir = file.rsplit("/", 1)[0] if "/" in file else ""
            return (
                relative_path(dest["file"], from_dir)
                + (f"#{anchor}" if anchor else ""),
                "",
            )
        path, separator, fragment = target.partition("#")
        if not path:
            return target, ""
        # A file link was relative to specs/; it must now be relative to the new file's folder.
        from_specs = normalize_path(f"specs/{path}")
        from_dir = SIDECAR_DIR + ("/" + file.rsplit("/", 1)[0] if "/" in file else "")
        return relative_path(from_specs, from_dir) + separator + fragment, ""


def aligned_text(line: SourceLine) -> str:
    return line.raw if line.in_fence else normalize_line(line.raw)


def check_placement_and_links(
    old: ClassifiedFile, side: NewSide, manifest: Manifest, stage: str
) -> CheckResult:
    result = CheckResult(
        "5. copied lines sit where the manifest puts them, with the expected link targets"
    )
    legacy_header = legacy_header_lines(old, manifest)
    expectations = LinkExpectations(old, side, manifest)
    moved_out = {PROVENANCE_LINE} if stage == "examples" else set()
    placed = links = navs = 0
    for spec in manifest.files:
        classified = side.by_manifest_path.get(spec.path)
        if classified is None:
            continue  # reported as a missing file by check 0
        candidates = [
            line
            for line in classified.lines
            if line.kind not in ("blank", "heading", "front_matter")
        ]
        texts = [aligned_text(line) for line in candidates]
        position = 0
        for number in copied_old_lines(old, spec.blocks, legacy_header):
            old_line = old.lines[number - 1]
            if (
                number in moved_out
                or old_line.in_fence
                or old_line.kind in ("blank", "fence", "heading")
            ):
                continue
            wanted = normalize_line(old_line.raw)
            found = next(
                (k for k in range(position, len(texts)) if texts[k] == wanted), None
            )
            if found is None:
                result.failures.append(
                    f"{spec.path}: old line {number} is not in this file after the previous copied line "
                    f"(the manifest puts it here): {wanted[:90]}"
                )
                continue
            position = found + 1
            placed += 1
            old_targets = link_targets(old_line.raw)
            if not old_targets:
                continue
            new_targets = link_targets(candidates[found].raw)
            where = f"{spec.path}:{candidates[found].number}"
            if len(new_targets) != len(old_targets):
                result.failures.append(
                    f"{where}: old line {number} has {len(old_targets)} links, the copy has {len(new_targets)}"
                )
                continue
            for target, actual in zip(old_targets, new_targets, strict=True):
                links += 1
                expected, problem = expectations.expected(spec.path, number, target)
                if expected is None:
                    result.failures.append(f"{where}: old line {number}: {problem}")
                elif actual != expected:
                    result.failures.append(
                        f"{where}: old line {number}: link {target} became {actual}, expected {expected}"
                    )
        raw_lines = Counter(line.raw for line in classified.lines)
        needed = Counter(text.rstrip() for text in spec.nav_texts)
        for text, count in sorted(needed.items()):
            navs += count
            if raw_lines[text] < count:
                result.failures.append(
                    f"{spec.path}: declared {{nav}} line is not in the file verbatim "
                    f"(link targets included): {text[:120]}"
                )
    if stage == "examples":
        result.failures.extend(example_link_problems(side, manifest))
    result.info.append(
        f"copied lines placed: {placed}; links in copied lines checked: {links}; "
        f"declared nav lines found verbatim: {navs}"
    )
    return result


def example_link_problems(side: NewSide, manifest: Manifest) -> list[str]:
    """Stage examples: examples/README.md has one 'Sidecar: [`name.yaml`](path).' line per example fence,
    in fence order, and each link text is the file name of the YAML file the link points at.
    """
    classified = side.by_manifest_path.get("examples/README.md")
    if classified is None:
        return []
    expected = [
        path
        for _, path in sorted(
            zip(manifest.example_fences, manifest.examples, strict=True)
        )
    ]
    found = [line for line in classified.lines if line.raw.startswith("Sidecar: ")]
    problems: list[str] = []
    if len(found) != len(expected):
        problems.append(
            f"examples/README.md: {len(found)} 'Sidecar:' lines, the manifest has {len(expected)} example fences"
        )
    for line, path in zip(found, expected, strict=False):
        match = EXAMPLE_LINK.match(line.raw)
        if match is None:
            problems.append(
                f"examples/README.md:{line.number}: not a 'Sidecar: [`name`](path).' line"
            )
        elif (
            match.group(1) != path.rsplit("/", 1)[-1]
            or normalize_path("examples/" + match.group(2)) != path
        ):
            problems.append(
                f"examples/README.md:{line.number}: link {match.group(1)} -> {match.group(2)}, "
                f"the manifest puts {path} here"
            )
    return problems


# --------------------------------------------------------------------------------------------------
# Front matter and rule IDs
# --------------------------------------------------------------------------------------------------


def parse_front_matter(lines: Sequence[str]) -> tuple[dict | None, int, str]:
    """Return (mapping, number of front matter lines, error). The mapping is None on error."""
    length = front_matter_length(lines)
    if not length:
        return (
            None,
            0,
            "file does not start with front matter (a '---' line, then a closing '---')",
        )
    body = "\n".join(lines[1 : length - 1])
    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError as error:
        return (
            None,
            length,
            f"front matter is not valid YAML: {str(error).splitlines()[0]}",
        )
    if not isinstance(data, dict):
        return None, length, "front matter is not a mapping"
    return data, length, ""


def check_front_matter(manifest: Manifest, repo: Path) -> CheckResult:
    result = CheckResult(
        "2. section files: front matter is exactly id, title, kind with manifest values; ids unique"
    )
    ids: dict[str, str] = {}
    for spec in manifest.files:
        path = repo / SIDECAR_DIR / spec.path
        if not path.is_file():
            if spec.front_matter is not None:
                result.failures.append(f"{spec.path}: file is missing")
            continue
        lines = [line.rstrip() for line in read_lines(path)]
        data, length, error = parse_front_matter(lines)
        if spec.front_matter is None:
            if length:
                result.failures.append(
                    f"{spec.path}: starts with front matter but the manifest has none"
                )
            continue
        expected = dict(spec.front_matter)
        if data is None:
            result.failures.append(f"{spec.path}: {error}")
            continue
        if set(data) != set(FRONT_MATTER_KEYS):
            result.failures.append(
                f"{spec.path}: front matter keys are {sorted(data)}, expected {sorted(FRONT_MATTER_KEYS)}"
            )
        for key in FRONT_MATTER_KEYS:
            if data.get(key) != expected.get(key):
                result.failures.append(
                    f"{spec.path}: front matter {key} is {data.get(key)!r}, manifest says {expected.get(key)!r}"
                )
        for section_id in {str(expected.get("id")), str(data.get("id"))}:
            if section_id in ids and ids[section_id] != spec.path:
                result.failures.append(
                    f"{spec.path}: id {section_id} is also used by {ids[section_id]}"
                )
            ids[section_id] = spec.path
        heading = next((line for line in lines[length:] if line), "")
        if heading != f"# {expected.get('title')}":
            result.warnings.append(
                f"{spec.path}: first line after front matter is {heading!r}, expected '# {expected.get('title')}'"
            )
    result.info.append(
        f"section files checked: {len(manifest.section_files)}; unique ids: {len(ids)}"
    )
    return result


def rule_id_problems(spec: FileSpec, classified: ClassifiedFile) -> list[str]:
    """Problems with the rule IDs of one file: labels must be V-<id>-1..n in order, one per checklist item."""
    problems: list[str] = []
    section_id = str(spec.front_matter["id"]) if spec.front_matter else None
    seen = 0
    for line in classified.of_kind("content"):
        if not CHECKLIST_ITEM.match(line.raw):
            continue
        match = LABELLED_RULE.match(line.raw)
        if section_id is None:
            problems.append(
                f"{line.path}:{line.number}: checklist item in a file that has no rules"
            )
            continue
        seen += 1
        if not match:
            problems.append(
                f"{line.path}:{line.number}: checklist item has no V-{section_id}-<n> label"
            )
        elif match.group("id") != section_id or int(match.group("n")) != seen:
            problems.append(
                f"{line.path}:{line.number}: label is V-{match.group('id')}-{match.group('n')}, expected V-{section_id}-{seen}"
            )
    if section_id is not None and seen != spec.rule_count:
        problems.append(
            f"{classified.path}: {seen} checklist items, manifest lists {spec.rule_count} rules"
        )
    return problems


def check_rule_ids(
    manifest: Manifest, repo: Path, classified_by_path: dict[str, ClassifiedFile]
) -> CheckResult:
    result = CheckResult("3. rule IDs are V-<id>-1..n in order in every file")
    total = 0
    for spec in manifest.files:
        classified = classified_by_path.get(spec.path)
        if classified is None:
            continue
        result.failures.extend(rule_id_problems(spec, classified))
        total += spec.rule_count
    result.info.append(f"rules expected from the manifest: {total}")
    return result


# --------------------------------------------------------------------------------------------------
# Loading the new side
# --------------------------------------------------------------------------------------------------


@dataclass
class NewSide:
    files: list[ClassifiedFile] = field(default_factory=list)
    by_manifest_path: dict[str, ClassifiedFile] = field(default_factory=dict)
    index: ClassifiedFile | None = None
    missing: list[str] = field(default_factory=list)


def load_new_side(repo: Path, manifest: Manifest, stage: str) -> NewSide:
    side = NewSide()

    def load(rel: str, path: Path, *, all_content: bool) -> ClassifiedFile | None:
        if not path.is_file():
            side.missing.append(rel)
            return None
        classified = classify_lines(read_lines(path), rel, all_content=all_content)
        side.files.append(classified)
        return classified

    side.index = load(manifest.source, repo / manifest.source, all_content=False)
    for spec in manifest.files:
        rel = f"{SIDECAR_DIR}/{spec.path}"
        classified = load(rel, repo / rel, all_content=False)
        if classified is not None:
            side.by_manifest_path[spec.path] = classified
    if stage == "examples":
        for example in manifest.examples:
            rel = f"{SIDECAR_DIR}/{example}"
            load(rel, repo / rel, all_content=True)
    return side


def inventory_warnings(
    old: ClassifiedFile, repo: Path, allow_missing: bool = False
) -> tuple[list[str], list[str]]:
    """Best-effort check that old line 1512 reappears in an inventory.yaml (stage examples).

    Returns (warnings, info). With ``allow_missing`` an absent inventory.yaml is an expected
    exception (the file is created by a later step) and is reported as information only.
    """
    line = next((item for item in old.lines if item.number == PROVENANCE_LINE), None)
    candidates = (
        sorted((repo / SIDECAR_DIR).rglob("inventory.yaml"))
        if (repo / SIDECAR_DIR).is_dir()
        else []
    )
    if line is None:
        return [f"old spec has no line {PROVENANCE_LINE}"], []
    if not candidates:
        message = (
            f"old line {PROVENANCE_LINE} should move to inventory.yaml but no inventory.yaml exists "
            f"under {SIDECAR_DIR}"
        )
        if allow_missing:
            return [], [f"expected exception (--allow-missing-inventory): {message}"]
        return [message], []
    text = "\n".join(read_lines(candidates[0]))
    if line.raw.strip() not in text:
        return [
            f"old line {PROVENANCE_LINE} text not found verbatim in {candidates[0].name} (it may have been reformatted)"
        ], []
    return [], []


# --------------------------------------------------------------------------------------------------
# The verbatim check as a whole
# --------------------------------------------------------------------------------------------------


def check_verbatim(
    old: ClassifiedFile,
    manifest: Manifest,
    side: NewSide,
    stage: str,
    repo: Path,
    allow_missing_inventory: bool = False,
) -> tuple[CheckResult, Counter]:
    result = CheckResult(
        f"0. move-only: old and new content multisets agree (stage {stage})"
    )
    moved_out = (PROVENANCE_LINE,) if stage == "examples" else ()
    old_lines, removed = old_side(old, manifest.excluded, moved_out)
    new_lines = [
        line for classified in side.files for line in content_lines(classified)
    ]
    generated, generated_warnings = generated_kinds(manifest, stage)
    nav = nav_lines_of(manifest)
    comparison = compare_lines(old_lines, new_lines, nav, generated)

    skipped_old = Counter(line.kind for line in old.lines if line.kind != "content")
    skipped_new = Counter(
        line.kind
        for classified in side.files
        for line in classified.lines
        if line.kind != "content"
    )
    result.info.append(
        f"old spec: {len(old.lines)} lines, {len(old_lines)} content lines compared"
    )
    result.info.append(
        f"  dropped by the manifest (excluded{' + moved out' if moved_out else ''}): {dict(removed)}"
    )
    result.info.append(
        f"  skipped old lines by kind: {dict(sorted(skipped_old.items()))}"
    )
    result.info.append(f"new files: {len(side.files)}, {len(new_lines)} content lines")
    result.info.append(
        f"  skipped new lines by kind: {dict(sorted(skipped_new.items()))}"
    )
    result.info.append("allowed additions subtracted from the new side:")
    for kind in ("nav",) + tuple(g.kind for g in generated):
        result.info.append(f"  {kind}: {comparison.additions[kind]}")
    result.info.append(f"  total: {sum(comparison.additions.values())}")

    for rel in side.missing:
        result.failures.append(f"new file is missing: {rel}")
    for classified in side.files:
        result.failures.extend(classified.problems)
    unexpected_texts = [text for text, _, _ in comparison.unexpected]
    result.failures.extend(
        format_missing(item, unexpected_texts) for item in comparison.missing
    )
    result.failures.extend(format_unexpected(item) for item in comparison.unexpected)
    result.failures.extend(
        f"declared {{nav}} line not found in the new files: {text}"
        for text in comparison.declared_nav_missing
    )
    result.failures.extend(
        f"generated {kind} line the manifest implies is not in the new files: {text}"
        for kind, text in comparison.generated_missing
    )

    result.info.append(
        "skipped kinds compared as multisets (old minus excluded plus declared repeats):"
    )
    skipped_problems, skipped_info = skipped_line_problems(
        old, manifest, side, dropped_numbers(manifest.excluded, moved_out), stage
    )
    result.info.extend(skipped_info)
    result.failures.extend(skipped_problems)

    result.warnings.extend(generated_warnings)
    if stage == "examples":
        inventory_problems, inventory_info = inventory_warnings(
            old, repo, allow_missing_inventory
        )
        result.warnings.extend(inventory_problems)
        result.info.extend(inventory_info)
    return result, comparison.additions


# --------------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prove that the sidecar spec split is move-only."
    )
    parser.add_argument(
        "--old", required=True, type=Path, help="the old single-file spec (Markdown)"
    )
    parser.add_argument(
        "--manifest", required=True, type=Path, help="the split manifest (YAML)"
    )
    parser.add_argument(
        "--repo",
        required=True,
        type=Path,
        help="repository root that holds the new files",
    )
    parser.add_argument(
        "--stage",
        choices=("split", "examples"),
        default="split",
        help="split: Markdown only; examples: also the YAML example files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="maximum failures or warnings printed per check (default 40)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    parser.add_argument(
        "--allow-missing-inventory",
        action="store_true",
        help="stage examples: accept that no inventory.yaml exists yet (old line 1512 moves there later)",
    )
    return parser.parse_args(argv)


def print_result(result: CheckResult, limit: int, strict: bool) -> bool:
    """Print one check; return True when it passed."""
    failed = bool(result.failures) or (strict and bool(result.warnings))
    print(f"[{'FAIL' if failed else 'PASS'}] {result.name}")
    for line in result.info:
        print(f"    {line}")
    for label, entries in (("FAILURE", result.failures), ("WARNING", result.warnings)):
        for entry in entries[:limit]:
            print(f"    {label}: {entry}")
        if len(entries) > limit:
            print(
                f"    ... {len(entries) - limit} more {label.lower()}s (raise --limit to see them)"
            )
    return not failed


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def run(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    old = classify_lines(read_lines(args.old), "old spec")
    side = load_new_side(args.repo, manifest, args.stage)
    verbatim, _ = check_verbatim(
        old, manifest, side, args.stage, args.repo, args.allow_missing_inventory
    )
    results = [
        verbatim,
        check_index_headings(old, side.index),
        check_front_matter(manifest, args.repo),
        check_rule_ids(manifest, args.repo, side.by_manifest_path),
        check_tables(side),
        check_placement_and_links(old, side, manifest, args.stage),
        check_moved_to(old, side, manifest, args.repo),
    ]
    passed = [print_result(result, args.limit, args.strict) for result in results]
    print("RESULT: " + ("PASS (move-only)" if all(passed) else "FAIL"))
    return 0 if all(passed) else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_output()
    try:
        return run(args)
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
