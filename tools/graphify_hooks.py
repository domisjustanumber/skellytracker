#!/usr/bin/env python3
"""Install the local graphify hooks and build the graph of a checkout (decision 87B2).

Usage::

    uv run python tools/graphify_hooks.py install [--no-build]
    uv run python tools/graphify_hooks.py uninstall

``install`` copies ``tools/graphify_hook.sh`` to the post-commit, post-checkout, post-merge and
post-rewrite hooks of the common git folder. Thus the hooks apply to each worktree. The copy has LF
line endings. ``install`` adds ``graphify-out/`` to ``info/exclude``. This also covers the branches
that do not have the line in ``.gitignore``. Then it builds the graph of the current checkout with
``uvx`` and the pin of the hook. The hook updates only a checkout that has ``graphify-out/``, so
this first build opts the checkout in. ``--no-build`` skips the build.

Run ``install`` in each checkout that must have a graph. Run it again after
``tools/graphify_hook.sh`` changes. If one of the four hooks exists and is not a graphify hook,
``install`` changes nothing and exits 1.

``uninstall`` removes only the graphify hooks, also their ``*.legacy`` copies. It does not remove
``graphify-out/``. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("graphify_hook.sh")
HOOK_NAMES = ("post-commit", "post-checkout", "post-merge", "post-rewrite")
MARKER = "graphify-local"
IGNORE_LINE = "graphify-out/"
# `uv run` sets these. The interpreter that uvx starts must not read them: on Windows, PYTHONHOME of a
# different Python version stops it with "SRE module mismatch". The hook unsets the same names.
UV_RUN_VARIABLES = (
    "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "UV_INTERNAL__PYTHONHOME", "UV_RUN_RECURSION_DEPTH"
)


def git(cwd: Path, *args: str) -> str:
    exe = shutil.which("git")
    if exe is None:
        raise SystemExit("git is not on the PATH")
    return subprocess.run(  # noqa: S603
        [exe, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def git_path(cwd: Path, name: str) -> Path:
    """A path in the git folder. ``hooks`` and ``info/exclude`` are in the common folder."""
    return Path(git(cwd, "rev-parse", "--path-format=absolute", "--git-path", name))


def pin() -> str:
    """The package pin of the hook, for example ``graphifyy==0.9.100``."""
    match = re.search(r"^PIN=(\S+)$", HOOK.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise SystemExit(f"{HOOK.name}: no PIN= line")
    return match.group(1)


def is_ours(path: Path) -> bool:
    return MARKER in path.read_text(encoding="utf-8", errors="replace")


def install(cwd: Path, build: bool = True) -> int:
    hooks = git_path(cwd, "hooks")
    foreign = [name for name in HOOK_NAMES if (hooks / name).exists() and not is_ours(hooks / name)]
    if foreign:
        print(f"graphify hooks: not installed. These hooks exist in {hooks}: {', '.join(foreign)}")
        return 1
    body = HOOK.read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    hooks.mkdir(parents=True, exist_ok=True)
    for name in HOOK_NAMES:
        path = hooks / name
        path.write_bytes(body)
        path.chmod(path.stat().st_mode | 0o111)

    exclude = git_path(cwd, "info/exclude")
    text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if IGNORE_LINE not in text.splitlines():
        exclude.parent.mkdir(parents=True, exist_ok=True)
        separator = "" if text.endswith("\n") or not text else "\n"
        exclude.write_text(f"{text}{separator}{IGNORE_LINE}\n", encoding="utf-8")
    print(f"graphify hooks: installed in {hooks}")

    if not build:
        return 0
    uvx = shutil.which("uvx")
    if uvx is None:
        print("graphify hooks: uvx is not on the PATH. Install uv, then run install again.")
        return 1
    env = {key: value for key, value in os.environ.items() if key not in UV_RUN_VARIABLES}
    env.update(GRAPHIFY_BACKEND="none", GRAPHIFY_NO_TIPS="1")
    return subprocess.run(  # noqa: S603
        [uvx, "--from", pin(), "graphify", "update", "."],
        cwd=git(cwd, "rev-parse", "--show-toplevel"),
        env=env,
        check=False,
    ).returncode


def uninstall(cwd: Path) -> int:
    hooks = git_path(cwd, "hooks")
    for name in HOOK_NAMES:
        for path in (hooks / name, hooks / f"{name}.legacy"):
            if path.exists() and is_ours(path):
                path.unlink()
    print("graphify hooks: removed. To remove a graph, delete graphify-out/ of its checkout.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    install_parser = commands.add_parser("install")
    install_parser.add_argument("--no-build", action="store_true", help="do not build the graph")
    commands.add_parser("uninstall")
    args = parser.parse_args(argv)
    if args.command == "install":
        return install(Path.cwd(), build=not args.no_build)
    return uninstall(Path.cwd())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
