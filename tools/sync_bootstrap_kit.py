#!/usr/bin/env python3
"""Write or check the copied files and blocks of the bootstrap kit (decisions 0031 and Z05A).

Usage::

    python tools/sync_bootstrap_kit.py --check   # fail when a copy differs from its live file
    python tools/sync_bootstrap_kit.py --write   # write each copy again from its live file

The kit in ``specs/agents-and-adr-process/bootstrap/`` holds copies of the tools and configs of this
repo, for a new repo to copy. Each copy is its live file with a short list of exact text edits that
remove the parts that belong only to this repo. A change to a live file must be copied to the kit:
run ``--write`` and commit both files. The doc tests run ``--check``. Standard library only.

The kit templates also hold blocks of live text. A block named ``## <heading>`` is the whole
section under that heading, up to the next ``## `` heading. Any other block name is the text between
the lines ``<!-- kit:<name> -->`` and ``<!-- /kit -->``, which are in the live file and in the kit
file. The kit text of a block is the live text without its citations of single live entries, with
the edits applied. ``--write`` writes only the text of each block and keeps the rest of the kit file.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

KIT = Path("specs") / "agents-and-adr-process" / "bootstrap"


@dataclass(frozen=True)
class Copy:
    target: str
    source: str
    edits: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Block:
    live: str  # repo-relative path of the live file
    kit: str  # repo-relative path of the kit template
    name: str  # "## <heading>" for a whole section, else the name of a marker block
    edits: tuple[tuple[str, str], ...] = ()


# A link in parentheses to one live entry, for example "([ADR-JW9N](JW9N-....md))".
CITATION = re.compile(
    r"\s*\((?:ADR-)?\[(?:ADR-)?([0-9A-Z]{4})\]\((?:[^():\s]*/)?\1-[^():\s]*\.md\)\)", re.IGNORECASE
)
MARKER = re.compile(r"^[ \t]*<!-- (?:kit:([a-z0-9-]+)|/kit) -->[ \t]*$")

DECISION_0001 = "(decision 0001)"

COPIES = (
    Copy(
        "tools/check_decision_log.py",
        "tools/check_decision_log.py",
        (
            ("(decisions z934 and gtwq).", f"{DECISION_0001}."),
            ("(decision QPS7).", f"{DECISION_0001}."),
            ("(decision NB91).", f"{DECISION_0001}."),
            ("(decisions Z05A and QPS7).", f"{DECISION_0001}."),
            ("random IDs (decision\ngtwq).", "random IDs (decision\n0001)."),
            ("another repo (decision gtwq).\n", f"another repo {DECISION_0001}.\n"),
            ("INDEX_LIMIT = 18_000\n", "INDEX_LIMIT = 14_000\n"),
            ("READ_PATH_LIMIT = 160_000\n", "READ_PATH_LIMIT = 220_000\n"),
            (
                'TARGET_BRANCH = "development"\n',
                'TARGET_BRANCH = "main"  # Step 3 of the kit guide sets the branch that PRs target.\n',
            ),
            ("LAST_UNLIMITED_ENTRY = 25\n", "LAST_UNLIMITED_ENTRY = 0\n"),
            (
                'LOG_DIRS = (LOG_DIR, Path("specs") / "model-sidecar" / "decisions")\n',
                "LOG_DIRS = (LOG_DIR,)  # A step of the kit guide adds the module logs.\n",
            ),
            (
                'OLD_LOG_DIRS: tuple[Path, ...] = (Path("notes") / "decisions",)\n',
                "OLD_LOG_DIRS: tuple[Path, ...] = ()\n",
            ),
        ),
    ),
    Copy(
        "tools/tests/test_decision_log.py",
        "tools/tests/test_decision_log.py",
        (("(decision z934).", f"{DECISION_0001}."), ("(decision Z05A).", f"{DECISION_0001}.")),
    ),
    Copy(
        "tools/check_private_data.py",
        "tools/check_private_data.py",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            (
                'ALLOWED_EMAILS = {"info@freemocap.org", "noreply@anthropic.com"}\n',
                "# Add the public contact address of the project here, for example the one in pyproject.toml.\n"
                'ALLOWED_EMAILS = {"noreply@anthropic.com"}\n',
            ),
        ),
    ),
    Copy(
        "tools/tests/test_private_data.py",
        "tools/tests/test_private_data.py",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            ('    assert kinds("info" + at + "freemocap.org") == []\n', ""),
        ),
    ),
    Copy(
        "tools/check_links.py",
        "tools/check_links.py",
        (("(decision 0032).", f"{DECISION_0001}."),),
    ),
    Copy("tools/tests/test_links.py", "tools/tests/test_links.py"),
    Copy(
        "tools/check_ai_attribution.py",
        "tools/check_ai_attribution.py",
        (("(decision p3n3).", f"{DECISION_0001}."),),
    ),
    Copy(
        "tools/tests/test_check_ai_attribution.py",
        "tools/tests/test_check_ai_attribution.py",
        (("(decision p3n3).", f"{DECISION_0001}."),),
    ),
    Copy("tools/tests/conftest.py", "tools/tests/conftest.py"),
    Copy(
        ".pre-commit-config.yaml",
        ".pre-commit-config.yaml",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            ("# Decision gtwq: an entry ID", "# An entry ID"),
            ("# Decision p3n3: AI attribution", "# AI attribution"),
        ),
    ),
    Copy(
        ".gitleaks.toml",
        ".gitleaks.toml",
        (
            ("(decision 0030).", f"{DECISION_0001}."),
            (
                "The allowlists below hold only\n# reviewed false positives. Give the reason for each one.\n",
                "Add an [[allowlists]] table only\n# for a reviewed false positive, and give its reason.\n",
            ),
            (
                "\n[[allowlists]]\n"
                'description = "Model registry keys (pose_key: \\"rtmw-...\\") in the Rust port, not credentials"\n'
                'commits = ["e0af6f3bbe4f602c7ed1cf6ac07f36f6ea5415ea"]\n',
                "",
            ),
        ),
    ),
    Copy(
        "decisions/template.md",
        "decisions/template.md",
        (("`proposed` is a spec change\n  proposal that waits for a decision.", "`proposed` waits for a\n  decision."),),
    ),
    Copy(
        ".github/workflows/secrets.yml",
        ".github/workflows/secrets.yml",
        (("    branches: [main, development]\n", "    branches: [main]\n"),),
    ),
)

AGENTS = ("AGENTS.md", f"{KIT.as_posix()}/AGENTS.md")
INDEX = ("decisions/README.md", f"{KIT.as_posix()}/decisions/README.md")
BRANCH = "`{{DEFAULT_BRANCH}}`"
KIT_0001 = "decisions/entries/0001-decision-log-agents-md-and-private-data.md"

BLOCKS = (
    Block(
        *AGENTS,
        "writing-rules",
        (
            (
                "This rule applies to each `AGENTS.md`, skills, decision entries, templates, the model addition\n"
                "workflow, the exporter guide and the sidecar spec.",
                "This rule applies to `AGENTS.md`, skills, decision entries and templates.",
            ),
            ("field names, enum values", "field names, values"),
        ),
    ),
    Block(*AGENTS, "skills", (("Git tracks `.claude/skills/` and ignores the rest of `.claude/`.\n", ""),)),
    Block(
        *AGENTS,
        "plans-folder",
        (("cite the content of a plan.", f"cite the content of a plan\n  ([ADR-0001]({KIT_0001}))."),),
    ),
    Block(
        *AGENTS,
        "push-and-attribution",
        (
            (
                "description or a change of a draft PR to ready. A force-push is a\n  new push.",
                "description, a change of a draft PR to ready, a release or a\n  published image."
                " A force-push is a new push.",
            ),
        ),
    ),
    Block(
        *AGENTS,
        "## 5. Decision Log",
        (
            (
                "before you change sidecar code, a sidecar, an example,\nthe spec, the agent instructions or the PR"
                " workflow.\nFor spec work, also read the [`README.md`](specs/model-sidecar/decisions/README.md) and"
                " the\n[`open-work.md`](specs/model-sidecar/decisions/open-work.md) of the spec log in\n"
                "`specs/model-sidecar/decisions/`.\nAn entry goes in the spec log only when each file that its"
                " Decision section names or changes is in\n`specs/model-sidecar/`.",
                "before you change {{AREAS}} or these instructions.\nFor a task in a module with a log, also read"
                " the `decisions/README.md` and the\n`decisions/open-work.md` of that module. The `AGENTS.md` of"
                " the module links to its log.\nAn entry goes in the log of a module only when each file that its"
                " Decision section names or\nchanges is in that module.",
            ),
            ("[ADR-JB5J](decisions/entries/JB5J-one-batch-form-for-each-sidecar.md).", f"[ADR-0001]({KIT_0001})."),
            ("This rule also applies to an older entry with a lower-case file name.\n", ""),
            (
                "\n([ADR-Z05A](decisions/entries/Z05A-essential-decision-log-rules.md); see the\n"
                "[Rules](decisions/README.md#rules)).",
                "\n(see the [Rules](decisions/README.md#rules)).",
            ),
            (
                "\nThe bootstrap kit in `specs/agents-and-adr-process/` is guidance, not a part of the sidecar spec.\n"
                "It holds the final form of the rules of this decision log for a new repository.\n"
                "Each kit copy is its live file with the text edits that `tools/sync_bootstrap_kit.py` lists.\n"
                "The kit templates also hold blocks of the live files: whole sections, and the text between the\n"
                "lines `<!-- kit:<name> -->` and `<!-- /kit -->`. The tool lists them with their edits.\n"
                "When you change a copied live file or a block, run `uv run python tools/sync_bootstrap_kit.py"
                " --write`.\nCommit the kit files in the same PR.\nThe kit decision log must stay valid.\n"
                "Change the rest of a kit template by hand when a rule of this log changes.\n",
                "",
            ),
        ),
    ),
    Block(*AGENTS, "## 7. Tool Calls"),
    Block(
        *AGENTS,
        "## 8. Private Data",
        (
            (
                "This repository is public, and git history is permanent.",
                f"This repository is public, or it can become public. Git history is permanent\n([ADR-0001]({KIT_0001})).",
            ),
            (
                "- A GitHub permalink to a repo of a freemocap exporter is not a private URL. This is also true when\n"
                "  the repo is private. The permalink can contain the user name of the account that owns the repo. Do\n"
                "  not write that user name in prose. Do not put that user\n"
                "  name in `.private-terms`. The check would then fail on each permalink.\n",
                "",
            ),
            ("`../OpenMMLab-Exporter/notes/`", "`../{{SIBLING_REPO}}/notes/`"),
        ),
    ),
    Block(
        *INDEX,
        "## Rules",
        (
            ("only to an entry that is on `development`.", f"only to an entry that is on {BRANCH}."),
            (
                "the spec, the root or a nested `AGENTS.md`, the skills, the model addition workflow, the exporter\n"
                "  guide, the templates of `specs/model-sidecar/templates/`, the Rules of this file with\n"
                "  [template.md](template.md), and the docstring of a tool in `tools/` for the rules that it checks.",
                "the root or a nested `AGENTS.md`, the skills, {{NORMATIVE_DOCS, for example the spec or the\n"
                "  contract files}}, the Rules of this file with [template.md](template.md), and the docstring of a\n"
                "  tool in `tools/` for the rules that it checks.",
            ),
            ("Until a commit is on `development`,", f"Until a commit is on {BRANCH},"),
            (
                " Write one at the end of the spec-build stage, and when the read-path limit\n  fails.",
                " Write one when the read-path limit fails.",
            ),
            (
                " An older entry keeps its lower-case ID in its file name, heading and index row. Do not edit\n"
                "  older text only to change the case.",
                "",
            ),
        ),
    ),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def apply(text: str, edits: tuple[tuple[str, str], ...], where: str) -> str:
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit(
                f"{where}: an edit for the bootstrap kit matches {text.count(old)} times, expected 1:\n{old}"
            )
        text = text.replace(old, new)
    return text


def expected(root: Path, copy: Copy) -> str:
    """The text of the copy: the live file with the edits applied."""
    return apply(read(root / copy.source), copy.edits, copy.source)


def spans(root: Path, path: str) -> tuple[list[str], dict[str, tuple[int, int]], list[str]]:
    """The lines of `path`, the line range of each section and marker block, and the marker errors."""
    lines = read(root / path).split("\n")
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")] + [len(lines)]
    found = {lines[i]: (i + 1, j) for i, j in zip(heads, heads[1:], strict=False)}
    errors: list[str] = []
    name, start = "", 0
    for number, line in enumerate(lines, 1):
        marker = MARKER.match(line)
        if not marker:
            continue
        new = marker.group(1)
        if new and name:
            errors.append(f"{path}:{number}: kit:{new} starts inside kit:{name}; blocks do not nest")
        elif new and new in found:
            errors.append(f"{path}:{number}: a second block kit:{new}")
        elif new:
            name, start = new, number
        elif not name:
            errors.append(f"{path}:{number}: <!-- /kit --> closes no block")
        else:
            found[name], name = (start, number - 1), ""
    if name:
        errors.append(f"{path}:{start}: kit:{name} has no <!-- /kit -->")
    return lines, found, errors


def block_expected(root: Path, block: Block) -> str:
    """The kit text: the live block without citations of single live entries, with the edits applied."""
    lines, found, errors = spans(root, block.live)
    if errors or block.name not in found:
        raise SystemExit("\n".join(errors) or f"{block.live}: no block {block.name}")
    start, end = found[block.name]
    return apply(CITATION.sub("", "\n".join(lines[start:end])), block.edits, f"{block.live} {block.name}")


def block_errors(root: Path) -> list[str]:
    errors: list[str] = []
    files: dict[str, dict[str, tuple[int, int]]] = {}
    for path in dict.fromkeys(p for b in BLOCKS for p in (b.live, b.kit)):
        _, files[path], more = spans(root, path)
        errors += more
    names = {(p, b.name) for b in BLOCKS for p in (b.live, b.kit)}
    errors += [
        f"{p}: kit:{n} is not in BLOCKS of tools/sync_bootstrap_kit.py"
        for p in files
        for n in files[p]
        if not n.startswith("## ") and (p, n) not in names
    ]
    errors += [f"{p}: no block {n}" for p, n in sorted(names) if n not in files[p]]
    for p in files:
        # A heading block also owns its heading line, so it starts one line before its text.
        owned = sorted((s - n.startswith("## "), e, n) for n, (s, e) in files[p].items() if (p, n) in names)
        errors += [f"{p}: {b} overlaps {a}; blocks do not overlap" for (_, end, a), (start, _, b) in zip(owned, owned[1:], strict=False) if start < end]
    if errors:
        return errors
    for b in BLOCKS:
        lines, found, _ = spans(root, b.kit)
        start, end = found[b.name]
        if "\n".join(lines[start:end]) != block_expected(root, b):
            errors.append(f"{b.kit}: {b.name} differs from {b.live}; run --write")
    return errors


def write_blocks(root: Path) -> None:
    errors = [e for e in block_errors(root) if not e.endswith("run --write")]
    if errors:
        raise SystemExit("\n".join(errors))
    for path in dict.fromkeys(b.kit for b in BLOCKS):
        lines, found, _ = spans(root, path)
        for b in sorted((b for b in BLOCKS if b.kit == path), key=lambda b: -found[b.name][0]):
            start, end = found[b.name]
            lines[start:end] = block_expected(root, b).split("\n")
        (root / path).write_text("\n".join(lines), encoding="utf-8", newline="\n")


def check(root: Path) -> list[str]:
    errors = block_errors(root)
    for copy in COPIES:
        path = root / KIT / copy.target
        if not path.exists():
            errors.append(f"{KIT.as_posix()}/{copy.target}: missing; run --write")
        elif read(path) != expected(root, copy):
            errors.append(
                f"{KIT.as_posix()}/{copy.target}: differs from {copy.source}; run --write"
            )
    return errors


def write(root: Path) -> None:
    for copy in COPIES:
        path = root / KIT / copy.target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected(root, copy), encoding="utf-8", newline="\n")
    write_blocks(root)


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if argv[1:] == ["--write"]:
        write(root)
        print(f"bootstrap kit: wrote {len(COPIES)} copies and {len(BLOCKS)} blocks")
        return 0
    if argv[1:] == ["--check"]:
        errors = check(root)
        print("\n".join(errors) if errors else f"bootstrap kit: {len(COPIES)} copies and {len(BLOCKS)} blocks match")
        return 1 if errors else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
