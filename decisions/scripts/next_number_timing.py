#!/usr/bin/env python3
"""Time two designs of ``check_decision_log.py --next`` (decision 0032).

Usage::

    python notes/decisions/scripts/next_number_timing.py scratch DIR   # make a repo with 302 refs
    python notes/decisions/scripts/next_number_timing.py time ROOT [REPEATS]

``scratch`` makes a git repo in the new folder DIR: 301 commits on ``main``, 200 local branches
(100 at ``main``, 60 with an entry each and pairs of branches that share a number, 40 with no
``notes/decisions``), 100 remote-tracking refs, ``origin/HEAD``, and 2 worktrees next to DIR. It uses
one ``git fast-import`` process.

``time`` runs each design REPEATS times (default 5) on the repo at ROOT, and prints the median time
and the number of git processes:

- ``ls-tree per ref``: the first design. One ``git ls-tree`` for each ref.
- ``tool``: ``next_lines`` of ``tools/check_decision_log.py``. It runs 5 git processes for any number
  of refs.
- ``tool, full run``: ``python tools/check_decision_log.py --new ROOT`` in a new process, with the
  start-up of Python.

Standard library and the git CLI only. The script reads ROOT. It does not change it.
"""

from __future__ import annotations

import importlib.util
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOOL = REPO / "tools" / "check_decision_log.py"
LOG = "notes/decisions"
EMAIL = "timing" + "@" + "example.invalid"
GIT = shutil.which("git") or "git"


def load_tool():
    spec = importlib.util.spec_from_file_location("check_decision_log", TOOL)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603
        [GIT, "-c", "user.name=timing", "-c", f"user.email={EMAIL}", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        check=False,
    )


def scratch(root: Path) -> None:
    """A repo with 302 refs and 2 worktrees, for the timing."""
    if root.exists():
        raise SystemExit(f"{root} exists: give a new folder")
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    lines: list[str] = []
    mark = 0
    stamp = 1_700_000_000

    def commit(ref: str, files: dict[str, str], parent: str | None = None) -> str:
        nonlocal mark, stamp
        mark, stamp = mark + 1, stamp + 60
        lines.append(f"commit {ref}\nmark :{mark}\ncommitter t <{EMAIL}> {stamp} +0000\ndata 1\nc\n")
        if parent:
            lines.append(f"from {parent}\n")
        for path, body in files.items():
            lines.append(f"M 100644 inline {path}\ndata {len(body.encode())}\n{body}\n")
        return f":{mark}"

    tip = commit("refs/heads/main", {f"{LOG}/README.md": "# Decision log\n", "src/a.txt": "0"})
    for n in range(1, 31):
        tip = commit("refs/heads/main", {f"{LOG}/{n:04d}-entry-{n}.md": f"# {n:04d}\n"}, tip)
    for k in range(270):
        tip = commit("refs/heads/main", {"src/a.txt": f"x{k}"}, tip)
    for b in range(200):
        ref = f"refs/heads/feature/b{b:03d}"
        if b < 100:
            lines.append(f"reset {ref}\nfrom {tip}\n")
        elif b < 160:
            n = 31 + (b - 100) // 2
            commit(ref, {f"{LOG}/{n:04d}-topic-{b}.md": f"# {n:04d}\n"}, tip)
        else:
            commit(ref, {"other.txt": str(b)})
    git(root, "fast-import", "--quiet", stdin="".join(lines).encode())
    update = "".join(
        f"update refs/remotes/origin/feature/b{b:03d} refs/heads/feature/b{b:03d}\n"
        for b in range(50, 150)
    )
    git(root, "update-ref", "--stdin", stdin=update.encode())
    git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/feature/b050")
    git(root, "checkout", "-q", "main")
    (root / LOG / "0031-mine.md").write_text("# 0031\n", encoding="utf-8")
    git(root, "worktree", "add", "-q", str(root.parent / f"{root.name}-wt1"), "feature/b120")
    git(root, "worktree", "add", "-q", "--detach", str(root.parent / f"{root.name}-wt2"), "main")
    (root.parent / f"{root.name}-wt2" / LOG / "0099-wt.md").write_text("# 0099\n", encoding="utf-8")
    refs = git(root, "for-each-ref", "--format=x").stdout.count(b"x")
    print(f"scratch repo: {refs} refs")


def ls_tree_per_ref(root: Path, tool) -> str:
    """The first design: worktrees by `git worktree list`, then one `git ls-tree` for each ref."""
    names: set[str] = set(tool.entry_names(root / tool.LOG_DIR))
    for line in tool.decoded(tool.git(root, "worktree", "list", "--porcelain")).splitlines():
        if line.startswith("worktree "):
            names |= tool.entry_names(Path(line[9:]) / tool.LOG_DIR)
    refs = tool.decoded(tool.git(root, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes"))
    for ref in refs.split():
        listed = tool.decoded(tool.git(root, "ls-tree", "--name-only", ref, "--", f"{LOG}/"))
        names |= {Path(n).name for n in listed.splitlines() if tool.ENTRY_NAME.match(Path(n).name)}
    return f"next: {max((int(n[:4]) for n in names if n[:4].isdigit()), default=0) + 1:04d}"


def timed(run, repeats: int) -> tuple[float, str]:
    times, result = [], ""
    for _ in range(repeats):
        start = time.perf_counter()
        result = run()
        times.append(time.perf_counter() - start)
    return statistics.median(times) * 1000, result


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "scratch":
        scratch(Path(argv[2]).resolve())
        return 0
    if len(argv) not in (3, 4) or argv[1] != "time":
        print(__doc__)
        return 2
    root = Path(argv[2]).resolve()
    repeats = int(argv[3]) if len(argv) == 4 else 5
    tool = load_tool()
    count = [0]
    real_run = subprocess.run

    def counting_run(*args, **kwargs):
        count[0] += 1
        return real_run(*args, **kwargs)

    tool.subprocess.run = counting_run
    try:
        for label, run in (
            ("ls-tree per ref", lambda: ls_tree_per_ref(root, tool)),
            ("tool", lambda: tool.next_lines(root)[0]),
        ):
            count[0] = 0
            ms, result = timed(run, repeats)
            print(f"{label:16} {ms:8.1f} ms  {count[0] // repeats:4d} git processes  {result}")
    finally:
        tool.subprocess.run = real_run
    command = [sys.executable, str(TOOL), "--new", str(root)]
    ms, result = timed(lambda: real_run(command, capture_output=True, check=False).stdout.decode().split("\n")[0], repeats)  # noqa: S603
    print(f"{'tool, full run':16} {ms:8.1f} ms  {'':4}                {result}")
    print(f"git: {real_run([GIT, '--version'], capture_output=True, check=False).stdout.decode().strip()}")  # noqa: S603
    print(f"python: {sys.version.split()[0]}, {sys.platform}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
