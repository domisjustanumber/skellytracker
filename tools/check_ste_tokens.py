#!/usr/bin/env python3
"""Check that a rewording of a Markdown file kept its invariant tokens.

Usage::

    python tools/check_ste_tokens.py [--rev REV] [--allow ALLOW.yaml] FILE...

For each FILE the tool reads the version at git revision REV (default ``HEAD``, read with
``git show REV:path``) and the working-tree version, and compares eight kinds of token as
multisets. Prose may change freely. A token that gains or loses an occurrence is a difference.
Line endings are normalized to ``\\n`` on both sides first, so a CRLF checkout does not matter.

Token kinds (the name is the ``kind`` of an allow entry)
    ``code-span``     the text of every inline code span outside fenced code. A span opens and
                      closes with backtick runs of the same length and may cross a line break
                      inside its paragraph. One padding space on each side is dropped and a line
                      break counts as one space.
    ``number``        every standalone number (``\\b\\d+(?:\\.\\d+)?\\b``) outside code spans, fenced
                      code and front matter. Numbers in a rule-ID (``V-common.input-6``), in a link
                      target, in a bare URL and in an autolink are ignored.
    ``fence``         every fenced code block, as one string, byte for byte, delimiter lines
                      included.
    ``table``         the header row of every table, and its body cells as ``header: cell``
                      tokens. When the header of the last column is Description, Meaning, Rule,
                      Semantics, Purpose, Reason, Contents, Typical use or Change (case does not
                      matter), the cells of that column are prose and are skipped.
    ``front-matter``  the YAML front matter block, delimiter lines included, byte for byte.
    ``heading``       every ATX heading as ``#``-marks plus text, for example ``## Fields``.
    ``rule-id``       every rule-ID label (the code span ``V-...`` that opens a list item or
                      checklist item) as a multiset, and also their order in the file.
    ``link``          every link as ``[text](target)`` (``![text](target)`` for an image), every
                      reference definition as ``[label]: target`` and every autolink as ``<url>``.

The tool does not read setext headings or indented code blocks. It splits a table row on every
pipe that has no backslash before it, the way GitHub does.

Allow file (``--allow``)
    A YAML list of approved differences. Each entry has the keys ``file`` (repository-relative,
    forward slashes), ``kind``, ``token`` and ``reason``. ``token`` is the token as the report
    prints it, which is a JSON string and so also a YAML double-quoted string::

        - file: specs/model-sidecar/pre/normalization.md
          kind: code-span
          token: "`none`"
          reason: The mode is now named in the opening sentence.

    The tool has no YAML library (standard library only), so it reads a small subset: a block
    list of flat mappings, scalars that are plain, ``'single quoted'``, ``"double quoted"`` (JSON
    escapes, one line) or a ``|`` block, ``#`` comment lines, or a JSON array of objects. An
    approved difference matches on file, kind and token whatever its counts are.

Exit status: 0 when every difference is approved (or there is none), 1 when a difference is not
approved, 2 when a file, a revision or the allow file cannot be read.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

CODE_SPAN = "code-span"
NUMBER = "number"
FENCE = "fence"
TABLE = "table"
FRONT_MATTER = "front-matter"
HEADING = "heading"
RULE_ID = "rule-id"
LINK = "link"
KINDS = (CODE_SPAN, NUMBER, FENCE, TABLE, FRONT_MATTER, HEADING, RULE_ID, LINK)
"""The token kinds, in the order the report prints them."""

PROSE_LAST_COLUMNS = frozenset(
    {
        "description",
        "meaning",
        "rule",
        "semantics",
        "purpose",
        "reason",
        "contents",
        "typical use",
        "change",
    }
)
"""Headers of a last column whose cells are prose."""

_ALLOW_KEYS = ("file", "kind", "token", "reason")

_FENCE_OPEN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_HEADING = re.compile(r"^ {0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<text>.*))?$")
_LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d{1,9}[.)])(?:[ \t]+|$)")
_DELIMITER_ROW = re.compile(
    r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$"
)
_RULE_LABEL = re.compile(
    r"^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+(?:\[[ xX]\][ \t]+)?`(?P<id>V-[^`]+)`"
)
_RULE_ID = re.compile(r"\bV-[\w.<>]+(?:-[\w.<>]+)*")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_BACKTICKS = re.compile(r"`+")
_LINK = re.compile(
    r"(?P<bang>!?)\[(?P<text>(?:[^\[\]\\]|\\.|\[[^\[\]]*\])*)\]"
    r"\(\s*(?P<target><[^<>]*>|(?:[^()\s]|\([^()\s]*\))*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_REFERENCE = re.compile(
    r"^[ ]{0,3}\[(?P<label>[^\]]+)\]:[ \t]*(?P<target><[^<>]*>|\S+)", re.MULTILINE
)
_AUTOLINK = re.compile(r"<(?P<url>[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*)>")
_BARE_URL = re.compile(r"\bhttps?://\S+")
_DOUBLE_QUOTED = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$')
_SINGLE_QUOTED = re.compile(r"^'((?:[^']|'')*)'\s*(?:#.*)?$")


class CheckError(Exception):
    """A file, a revision or the allow file cannot be read."""


# --------------------------------------------------------------------------------------------
# Parsing a Markdown file into blocks
# --------------------------------------------------------------------------------------------


@dataclass
class Table:
    """A table: the stripped header cells and the stripped cells of each body row."""

    header: list[str]
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class Parsed:
    """The blocks of one file. `prose` holds one string per paragraph, heading or table row."""

    front_matter: list[str] = field(default_factory=list)
    fences: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    prose: list[str] = field(default_factory=list)


def normalize_newlines(text: str) -> str:
    """Return `text` with LF line endings and without a byte order mark."""
    return text.removeprefix("﻿").replace("\r\n", "\n")


def _front_matter_end(lines: Sequence[str]) -> int:
    """Return the index of the line after the front matter, or 0 when there is none."""
    if not lines or lines[0] != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].rstrip() in ("---", "..."):
            return index + 1
    return 0


def _fence_start(line: str) -> tuple[str, int] | None:
    """Return the fence character and length when `line` opens a fenced code block."""
    match = _FENCE_OPEN.match(line)
    if match is None:
        return None
    fence = match.group("fence")
    if fence[0] == "`" and "`" in match.group("info"):
        return None  # ```code``` on one line is an inline code span
    return fence[0], len(fence)


def _closes_fence(line: str, char: str, length: int) -> bool:
    stripped = line.strip()
    return len(stripped) >= length and set(stripped) == {char}


def _take_fence(
    lines: Sequence[str], start: int, char: str, length: int
) -> tuple[str, int]:
    """Return the whole block that opens at `start` and the index of the line after it."""
    end = start + 1
    while end < len(lines) and not _closes_fence(lines[end], char, length):
        end += 1
    end = min(end + 1, len(lines))
    return "\n".join(lines[start:end]), end


def split_row(line: str) -> list[str]:
    """Split a table row into stripped cells at every pipe without a backslash before it."""
    body = line.strip()
    body = body.removeprefix("|")
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", body)]


def _starts_table(lines: Sequence[str], index: int) -> bool:
    if (
        index + 1 >= len(lines)
        or "|" not in lines[index]
        or "|" not in lines[index + 1]
    ):
        return False
    if not _DELIMITER_ROW.match(lines[index + 1]):
        return False
    return len(split_row(lines[index])) == len(split_row(lines[index + 1]))


def _ends_table(line: str) -> bool:
    if not line.strip() or "|" not in line or _LIST_ITEM.match(line):
        return True
    return _fence_start(line) is not None or _heading_token(line) is not None


def _take_table(lines: Sequence[str], start: int) -> tuple[Table, list[str], int]:
    """Return the table at `start`, its row lines (without the delimiter row) and the next index."""
    table = Table(header=split_row(lines[start]))
    row_lines = [lines[start]]
    end = start + 2
    while end < len(lines) and not _ends_table(lines[end]):
        table.rows.append(split_row(lines[end]))
        row_lines.append(lines[end])
        end += 1
    return table, row_lines, end


def _heading_token(line: str) -> str | None:
    match = _HEADING.match(line)
    if match is None:
        return None
    text = re.sub(r"(?:^|[ \t]+)#+[ \t]*$", "", (match.group("text") or "").strip())
    return f"{match.group('marks')} {text}".rstrip()


def parse_markdown(text: str) -> Parsed:
    """Split LF-normalized Markdown into front matter, fences, headings, tables and prose."""
    lines = text.split("\n")
    parsed = Parsed()
    index = _front_matter_end(lines)
    parsed.front_matter = lines[:index]
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            parsed.prose.append("\n".join(paragraph))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        fence = _fence_start(line)
        heading = _heading_token(line)
        if fence is not None:
            flush()
            block, index = _take_fence(lines, index, *fence)
            parsed.fences.append(block)
        elif _starts_table(lines, index):
            flush()
            table, row_lines, index = _take_table(lines, index)
            parsed.tables.append(table)
            parsed.prose.extend(row_lines)
        elif heading is not None:
            flush()
            parsed.headings.append(heading)
            parsed.prose.append(line)
            index += 1
        else:
            if not line.strip() or _LIST_ITEM.match(line):
                flush()
            if line.strip():
                paragraph.append(line)
            index += 1
    flush()
    return parsed


# --------------------------------------------------------------------------------------------
# Inline tokens: code spans, numbers, links
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Span:
    """A code span: where it sits in the text (delimiters included) and its content."""

    start: int
    end: int
    content: str


def _is_escaped(text: str, position: int) -> bool:
    backslashes = len(text[:position]) - len(text[:position].rstrip("\\"))
    return backslashes % 2 == 1


def _span_content(raw: str) -> str:
    content = re.sub(r"[ \t]*\n[ \t]*", " ", raw)
    if (
        len(content) > 2
        and content[0] == " "
        and content[-1] == " "
        and content.strip()
    ):
        content = content[1:-1]
    return content


def find_code_spans(text: str) -> list[Span]:
    """Find the code spans of one paragraph. A backtick run closes a run of equal length."""
    runs = [(m.start(), m.end()) for m in _BACKTICKS.finditer(text)]
    spans: list[Span] = []
    index = 0
    while index < len(runs):
        start, end = runs[index]
        if _is_escaped(text, start):
            start += 1  # an escaped backtick is a literal one
        length = end - start
        closer = next(
            (
                j
                for j in range(index + 1, len(runs))
                if runs[j][1] - runs[j][0] == length
            ),
            None,
        )
        if length == 0 or closer is None:
            index += 1
            continue
        close_start, close_end = runs[closer]
        spans.append(Span(start, close_end, _span_content(text[end:close_start])))
        index = closer + 1
    return spans


def mask_spans(text: str, spans: Iterable[Span]) -> str:
    """Return `text` with every code span replaced by spaces of the same length."""
    chars = list(text)
    for span in spans:
        chars[span.start : span.end] = " " * (span.end - span.start)
    return "".join(chars)


def _link_token(match: re.Match[str], text: str) -> str:
    label = re.sub(r"\s+", " ", text[match.start("text") : match.end("text")]).strip()
    return f"{match.group('bang')}[{label}]({match.group('target')})"


def find_links(unit: str, masked: str) -> list[str]:
    """Return the link tokens of one paragraph. `masked` is `unit` with code spans blanked."""
    tokens = [_link_token(match, unit) for match in _LINK.finditer(masked)]
    tokens += [f"[{m['label']}]: {m['target']}" for m in _REFERENCE.finditer(masked)]
    tokens += [f"<{m['url']}>" for m in _AUTOLINK.finditer(masked)]
    return tokens


def find_numbers(masked: str) -> list[str]:
    """Return the numbers of one paragraph outside code, link targets and rule-IDs."""
    text = _LINK.sub(lambda m: f"{m['bang']}[{m['text']}] ", masked)
    text = _REFERENCE.sub(lambda m: f"[{m['label']}]: ", text)
    for pattern in (_AUTOLINK, _BARE_URL, _RULE_ID):
        text = pattern.sub(" ", text)
    return _NUMBER.findall(text)


def rule_label(unit: str) -> str | None:
    """Return the rule-ID that opens the list item in `unit`, if there is one."""
    match = _RULE_LABEL.match(unit)
    return match.group("id") if match else None


# --------------------------------------------------------------------------------------------
# Collecting the tokens of a file
# --------------------------------------------------------------------------------------------


def table_tokens(table: Table) -> list[str]:
    """Return the header row and the non-prose body cells of `table` as tokens."""
    tokens = ["header: " + " | ".join(table.header)]
    last = len(table.header) - 1
    last_name = re.sub(r"\s+", " ", table.header[-1]).casefold()
    skip_last = last_name in PROSE_LAST_COLUMNS
    for row in table.rows:
        for index, cell in enumerate(row):
            if skip_last and index == last:
                continue
            column = table.header[index] if index <= last else f"column {index + 1}"
            tokens.append(f"{column}: {cell}")
    return tokens


def collect_tokens(parsed: Parsed) -> dict[str, list[str]]:
    """Return the tokens of every kind. Only ``rule-id`` keeps the order of the file."""
    tokens: dict[str, list[str]] = {kind: [] for kind in KINDS}
    tokens[FENCE] = list(parsed.fences)
    tokens[HEADING] = list(parsed.headings)
    tokens[FRONT_MATTER] = (
        ["\n".join(parsed.front_matter)] if parsed.front_matter else []
    )
    for table in parsed.tables:
        tokens[TABLE].extend(table_tokens(table))
    for unit in parsed.prose:
        spans = find_code_spans(unit)
        masked = mask_spans(unit, spans)
        tokens[CODE_SPAN].extend(span.content for span in spans)
        tokens[NUMBER].extend(find_numbers(masked))
        tokens[LINK].extend(find_links(unit, masked))
        label = rule_label(unit)
        if label is not None:
            tokens[RULE_ID].append(label)
    return tokens


# --------------------------------------------------------------------------------------------
# Comparing
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Difference:
    """A token whose count changed. For a changed order of rule-IDs, both counts are the total."""

    kind: str
    token: str
    before: int
    after: int


def diff_multisets(
    kind: str, before: Iterable[str], after: Iterable[str]
) -> list[Difference]:
    """Return one difference per token that occurs a different number of times, sorted."""
    old, new = Counter(before), Counter(after)
    return [
        Difference(kind, token, old[token], new[token])
        for token in sorted(old.keys() | new.keys())
        if old[token] != new[token]
    ]


def diff_order(
    kind: str, before: Sequence[str], after: Sequence[str]
) -> list[Difference]:
    """Return one difference when the same tokens appear in a different order."""
    if Counter(before) != Counter(after) or list(before) == list(after):
        return []
    at = next(i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b)
    token = f"order changed at position {at + 1}: {before[at]} became {after[at]}"
    return [Difference(kind, token, len(before), len(after))]


def compare_texts(old: str, new: str) -> list[Difference]:
    """Return the differences between the invariant tokens of two versions of a file."""
    before = collect_tokens(parse_markdown(normalize_newlines(old)))
    after = collect_tokens(parse_markdown(normalize_newlines(new)))
    differences: list[Difference] = []
    for kind in KINDS:
        differences += diff_multisets(kind, before[kind], after[kind])
    return differences + diff_order(RULE_ID, before[RULE_ID], after[RULE_ID])


# --------------------------------------------------------------------------------------------
# The allow file
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Allowance:
    """An approved difference."""

    file: str
    kind: str
    token: str
    reason: str

    def matches(self, file: str, difference: Difference) -> bool:
        return (
            normalize_path(self.file) == file
            and self.kind == difference.kind
            and self.token == difference.token
        )


def normalize_path(path: str) -> str:
    """Return `path` with forward slashes and without a leading ``./``."""
    return path.replace("\\", "/").removeprefix("./")


def _scalar(text: str, line_number: int) -> str:
    """Read a one-line plain, single-quoted or double-quoted scalar."""
    text = text.strip()
    where = f"allow file line {line_number}"
    if text.startswith('"'):
        match = _DOUBLE_QUOTED.match(text)
        if match is None:
            raise CheckError(f"{where}: bad double-quoted string")
        try:
            return str(json.loads(f'"{match.group(1)}"'))
        except json.JSONDecodeError as error:
            raise CheckError(
                f"{where}: bad escape in a double-quoted string"
            ) from error
    if text.startswith("'"):
        match = _SINGLE_QUOTED.match(text)
        if match is None:
            raise CheckError(f"{where}: bad single-quoted string")
        return match.group(1).replace("''", "'")
    return re.sub(r"\s+#.*$", "", text)


def _block_scalar(
    lines: Sequence[str], start: int, header: str, key_indent: int
) -> tuple[str, int]:
    """Read a ``|`` or ``|-`` block whose body begins at `start`. Return the text and next index."""
    if header not in ("|", "|-"):
        raise CheckError(
            f"allow file line {start}: only '|' and '|-' block scalars are read"
        )
    body: list[str] = []
    end = start
    while end < len(lines) and (
        not lines[end].strip() or _indent(lines[end]) > key_indent
    ):
        body.append(lines[end])
        end += 1
    content = [line for line in body if line.strip()]
    indent = min((_indent(line) for line in content), default=0)
    text = "\n".join(line[indent:] for line in body).rstrip("\n")
    return (text if header == "|-" else text + "\n"), end


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _read_entry_lines(lines: Sequence[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = _indent(raw)
        item = re.match(r"^(\s*)-\s+(.*)$", raw)
        if item:
            entries.append({})
            raw = " " * (len(item.group(1)) + 2) + item.group(2)
            indent = _indent(raw)
        pair = re.match(r"^\s+([A-Za-z_]+):(?:\s+(.*))?$", raw)
        if pair is None or not entries:
            raise CheckError(
                f"allow file line {index}: expected '- key: value' or 'key: value'"
            )
        key, value = pair.group(1), (pair.group(2) or "").strip()
        if value.startswith("|"):
            value, index = _block_scalar(lines, index, value, indent)
        else:
            value = _scalar(value, index)
        entries[-1][key] = value
    return entries


def _build_allowance(entry: dict[str, object]) -> Allowance:
    unknown = sorted(set(entry) - set(_ALLOW_KEYS))
    missing = [
        key
        for key in _ALLOW_KEYS
        if not isinstance(entry.get(key), str) or not str(entry[key]).strip()
    ]
    if unknown or missing:
        raise CheckError(
            f"allow entry {entry}: unknown keys {unknown}, missing or empty {missing}"
        )
    if entry["kind"] not in KINDS:
        raise CheckError(f"allow entry {entry}: kind must be one of {', '.join(KINDS)}")
    return Allowance(*(str(entry[key]) for key in _ALLOW_KEYS))


def parse_allow_text(text: str) -> list[Allowance]:
    """Parse an allow file. See the module docstring for the YAML subset that it reads."""
    text = normalize_newlines(text)
    if text.lstrip().startswith("["):
        try:
            entries = json.loads(text)
        except json.JSONDecodeError as error:
            raise CheckError(f"allow file is not a JSON array: {error}") from error
        if not all(isinstance(entry, dict) for entry in entries):
            raise CheckError("allow file: every entry must be a mapping")
    else:
        entries = _read_entry_lines(text.split("\n"))
    return [_build_allowance(entry) for entry in entries]


# --------------------------------------------------------------------------------------------
# Git and the report
# --------------------------------------------------------------------------------------------


def _git(directory: Path, *arguments: str) -> bytes:
    """Run a read-only git command in `directory` and return its standard output."""
    git = shutil.which("git")
    if git is None:
        raise CheckError("git is not on the PATH")
    result = subprocess.run(  # noqa: S603
        [git, "-C", str(directory), *arguments], capture_output=True, check=False
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise CheckError(f"git {arguments[0]} failed: {message}")
    return result.stdout


def locate(path: Path) -> tuple[Path, str]:
    """Return the repository root of `path` and its path under the root with forward slashes."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise CheckError(f"{path}: not a file")
    root = Path(
        _git(resolved.parent, "rev-parse", "--show-toplevel").decode().strip()
    ).resolve()
    try:
        return root, resolved.relative_to(root).as_posix()
    except ValueError as error:
        raise CheckError(f"{path}: not inside the repository {root}") from error


def read_at_revision(revision: str, root: Path, relative: str) -> str:
    """Return the text of `relative` at `revision` (``git show REV:path``)."""
    if revision.startswith("-"):
        raise CheckError(f"bad revision {revision!r}")
    return _git(root, "show", f"{revision}:{relative}").decode("utf-8")


def read_working_tree(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


@dataclass(frozen=True)
class Finding:
    """A difference and the allow entry that approves it, if any."""

    difference: Difference
    allowance: Allowance | None


def match_allowances(
    file: str, differences: Iterable[Difference], allowances: Sequence[Allowance]
) -> list[Finding]:
    """Pair each difference with the first allow entry that approves it."""
    findings = []
    for difference in differences:
        allowance = next((a for a in allowances if a.matches(file, difference)), None)
        findings.append(Finding(difference, allowance))
    return findings


def format_report(file: str, findings: Sequence[Finding]) -> str:
    """Return the report for one file: its differences, grouped by kind."""
    pending = sum(1 for finding in findings if finding.allowance is None)
    approved = len(findings) - pending
    if not findings:
        return f"{file}: ok"
    lines = [f"{file}: {pending} difference(s), {approved} approved"]
    for kind in KINDS:
        group = [f for f in findings if f.difference.kind == kind]
        if not group:
            continue
        lines.append(f"  [{kind}]")
        for finding in group:
            d = finding.difference
            label = "approved" if finding.allowance else "difference"
            token = json.dumps(d.token, ensure_ascii=False)
            line = f"    {label}: {token} before={d.before} after={d.after}"
            if finding.allowance:
                line += f" reason: {finding.allowance.reason}"
            lines.append(line)
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


def check_file(
    path: Path, revision: str, allowances: Sequence[Allowance]
) -> tuple[str, list[Finding]]:
    """Compare one file with its version at `revision`. Return its display name and findings."""
    root, relative = locate(path)
    old = read_at_revision(revision, root, relative)
    new = read_working_tree(path)
    return relative, match_allowances(relative, compare_texts(old, new), allowances)


def load_allowances(path: Path | None) -> list[Allowance]:
    if path is None:
        return []
    try:
        return parse_allow_text(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        raise CheckError(f"{path}: {error}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that a rewording kept the invariant tokens of Markdown files."
    )
    parser.add_argument("files", nargs="+", type=Path, metavar="FILE")
    parser.add_argument(
        "--rev", default="HEAD", help="git revision of the old text (HEAD)"
    )
    parser.add_argument("--allow", type=Path, help="YAML list of approved differences")
    return parser


def run(
    args: argparse.Namespace, out: Callable[[str], None], err: Callable[[str], None]
) -> int:
    """Check every file and print the reports. Return the exit status."""
    allowances = load_allowances(args.allow)
    used: set[Allowance] = set()
    checked: set[str] = set()
    status = 0
    for path in args.files:
        try:
            name, findings = check_file(path, args.rev, allowances)
        except (CheckError, OSError, UnicodeDecodeError) as error:
            err(f"error: {error}")
            status = 2
            continue
        out(format_report(name, findings))
        checked.add(name)
        used.update(f.allowance for f in findings if f.allowance)
        if status == 0 and any(f.allowance is None for f in findings):
            status = 1
    for allowance in allowances:
        if allowance not in used and normalize_path(allowance.file) in checked:
            err(
                f"unused allow entry: {allowance.file} [{allowance.kind}] {allowance.token!r}"
            )
    return status


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args, print, lambda text: print(text, file=sys.stderr))
    except CheckError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
