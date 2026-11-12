"""The graphify hook installer and the hook body, in temporary git repositories (decision 87B2)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import graphify_hooks as gh
import pytest

ROOT = Path(__file__).resolve().parents[2]
SH = shutil.which("sh")
GIT = shutil.which("git")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run([GIT, "init", "-q", str(path)], check=True)  # noqa: S603
    return path


def hooks_of(repo: Path) -> Path:
    return gh.git_path(repo, "hooks")


def test_install_writes_the_four_hooks_and_the_ignore_line_once(repo: Path) -> None:
    assert gh.install(repo, build=False) == 0
    first = {name: (hooks_of(repo) / name).read_bytes() for name in gh.HOOK_NAMES}
    for body in first.values():
        assert gh.MARKER.encode() in body
        assert b"\r" not in body
    assert gh.install(repo, build=False) == 0
    assert {name: (hooks_of(repo) / name).read_bytes() for name in gh.HOOK_NAMES} == first
    exclude = gh.git_path(repo, "info/exclude").read_text(encoding="utf-8")
    assert exclude.splitlines().count(gh.IGNORE_LINE) == 1


def test_install_keeps_a_foreign_hook(repo: Path) -> None:
    foreign = hooks_of(repo) / "post-merge"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("#!/bin/sh\necho other tool\n")
    assert gh.install(repo, build=False) == 1
    assert foreign.read_text() == "#!/bin/sh\necho other tool\n"
    assert not (hooks_of(repo) / "post-commit").exists()


def test_uninstall_removes_only_graphify_hooks(repo: Path) -> None:
    assert gh.install(repo, build=False) == 0
    other = hooks_of(repo) / "pre-commit"
    other.write_text("#!/bin/sh\n")
    legacy = hooks_of(repo) / "post-commit.legacy"
    shutil.copy(hooks_of(repo) / "post-commit", legacy)
    assert gh.uninstall(repo) == 0
    assert not any((hooks_of(repo) / name).exists() for name in gh.HOOK_NAMES)
    assert not legacy.exists()
    assert other.exists()


def test_install_builds_without_the_variables_of_uv_run(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if Path(args[0]).stem == "uvx":
            calls.append((args, kwargs["env"]))
            return subprocess.CompletedProcess(args, 0)
        return real_run(args, **kwargs)

    real_run = subprocess.run
    monkeypatch.setattr(gh.subprocess, "run", fake_run)
    monkeypatch.setattr(gh.shutil, "which", lambda name: "uvx" if name == "uvx" else GIT)
    for name in gh.UV_RUN_VARIABLES:
        monkeypatch.setenv(name, "x")
    assert gh.install(repo) == 0
    [(args, env)] = calls
    assert args == ["uvx", "--from", gh.pin(), "graphify", "update", "."]
    assert not set(gh.UV_RUN_VARIABLES) & set(env)
    assert env["GRAPHIFY_BACKEND"] == "none"


def test_hook_unsets_the_variables_of_uv_run() -> None:
    assert f"unset {' '.join(gh.UV_RUN_VARIABLES)}" in gh.HOOK.read_text(encoding="utf-8")


def test_agents_md_uses_the_pin_of_the_hook() -> None:
    assert f"uvx --from {gh.pin()} graphify" in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def run_hook(repo: Path, home: Path, name: str, *args: str, fake_uvx: bool = True) -> None:
    """Run the installed hook ``name`` with a PATH that has only sh, git and maybe a fake uvx."""
    path = [str(Path(SH).parent), str(Path(GIT).parent)]
    if fake_uvx:
        bin_dir = home / "bin"
        bin_dir.mkdir(exist_ok=True)
        uvx = bin_dir / "uvx"
        uvx.write_bytes(b'#!/bin/sh\necho "$@" > "$HOME/uvx-args"\n')
        uvx.chmod(0o755)
        path.insert(0, str(bin_dir))
    elif shutil.which("uvx", path=os.pathsep.join(path)):
        pytest.skip("uvx is in the folder of sh or git")
    env = {**os.environ, "HOME": str(home), "PATH": os.pathsep.join(path)}
    env.pop("GRAPHIFY_SKIP_HOOK", None)
    # A Windows path with backslashes, as a caller on Windows can pass it.
    hook = str(hooks_of(repo) / name)
    result = subprocess.run([SH, hook, *args], cwd=repo, env=env, check=False)  # noqa: S603
    assert result.returncode == 0


def log_of(home: Path) -> str:
    log = home / ".cache" / "graphify-rebuild.log"
    return log.read_text(encoding="utf-8") if log.exists() else ""


@pytest.mark.skipif(SH is None or GIT is None, reason="needs sh and git on PATH")
@pytest.mark.parametrize(
    ("opted_in", "fake_uvx", "name", "args"),
    [
        (False, True, "post-commit", ()),
        (True, False, "post-commit", ()),
        (True, True, "post-checkout", ("a", "b", "0")),
        (True, True, "post-checkout", ("a", "a", "1")),
        (True, True, "post-rewrite", ("amend",)),
        (True, True, "post-checkout.legacy", ("a", "b", "0")),
    ],
    ids=["not-opted-in", "no-uvx", "file-checkout", "same-head", "amend", "legacy-name"],
)
def test_hook_does_nothing(
    repo: Path, tmp_path: Path, opted_in: bool, fake_uvx: bool, name: str, args: tuple[str, ...]
) -> None:
    gh.install(repo, build=False)
    if name.endswith(".legacy"):
        shutil.copy(hooks_of(repo) / name.removesuffix(".legacy"), hooks_of(repo) / name)
    if opted_in:
        (repo / "graphify-out").mkdir()
    run_hook(repo, tmp_path, name, *args, fake_uvx=fake_uvx)
    assert log_of(tmp_path) == ""


@pytest.mark.skipif(SH is None or GIT is None, reason="needs sh and git on PATH")
def test_hook_starts_a_background_update(repo: Path, tmp_path: Path) -> None:
    gh.install(repo, build=False)
    (repo / "graphify-out").mkdir()
    run_hook(repo, tmp_path, "post-checkout", "a", "b", "1")
    deadline = time.monotonic() + 30
    while "done rc=0" not in log_of(tmp_path) and time.monotonic() < deadline:
        time.sleep(0.2)
    assert "start post-checkout" in log_of(tmp_path)
    assert "done rc=0" in log_of(tmp_path)
    assert (tmp_path / "uvx-args").read_text().split() == [
        "--from", gh.pin(), "graphify", "update", ".", "--force"
    ]


def wait_for_done(home: Path, count: int) -> None:
    deadline = time.monotonic() + 30
    while log_of(home).count(" done rc=") < count and time.monotonic() < deadline:
        time.sleep(0.2)


@pytest.mark.skipif(GIT is None, reason="needs git on PATH")
@pytest.mark.parametrize(
    ("fast_forward", "hooks"),
    [(True, ["post-checkout"]), (False, ["post-checkout", "post-rewrite"])],
    ids=["fast-forward", "replay"],
)
def test_git_rebase_starts_an_update(
    repo: Path, tmp_path: Path, fast_forward: bool, hooks: list[str]
) -> None:
    home = tmp_path / "home"
    bin_dir = home / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "uvx").write_bytes(b"#!/bin/sh\n")
    (bin_dir / "uvx").chmod(0o755)
    author = "t" + "@" + "example.invalid"
    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": os.pathsep.join([str(bin_dir), os.environ["PATH"]]),
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": author,
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": author,
    }

    def run(*args: str) -> None:
        subprocess.run([GIT, *args], cwd=repo, env=env, check=True, capture_output=True)  # noqa: S603

    run("commit", "-q", "--allow-empty", "-m", "base")
    run("branch", "-q", "upstream")
    run("switch", "-q", "upstream")
    run("commit", "-q", "--allow-empty", "-m", "upstream")
    run("switch", "-q", "-")
    if not fast_forward:
        (repo / "local.txt").write_text("local\n")
        run("add", "local.txt")
        run("commit", "-q", "-m", "local")
    gh.install(repo, build=False)
    (repo / "graphify-out").mkdir()
    run("rebase", "-q", "upstream")
    wait_for_done(home, len(hooks))
    started = [line.split()[3] for line in log_of(home).splitlines() if " start " in line]
    assert started == hooks
