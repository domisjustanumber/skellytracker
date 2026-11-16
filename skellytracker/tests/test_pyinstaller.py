"""The PyInstaller entry points and hook: fast checks, and the slow frozen smoke test (`pytest -m pyinstaller`)."""

import ast
import importlib.metadata
import subprocess
import sys
from pathlib import Path

import pytest

import skellytracker._pyinstaller as entry

FOLDER = Path(entry.__file__).parent


def test_entry_points_give_one_folder_each():
    points = {point.name: point for point in importlib.metadata.entry_points(group="pyinstaller40")
              if point.value.startswith("skellytracker.")}  # numpy and other packages have the same names
    assert points["hook-dirs"].value == "skellytracker._pyinstaller:get_hook_dirs"
    assert points["tests"].value == "skellytracker._pyinstaller:get_PyInstaller_tests"
    (hooks,), (tests,) = points["hook-dirs"].load()(), points["tests"].load()()
    assert Path(hooks) == FOLDER and Path(tests) == FOLDER / "tests" and Path(tests).is_dir()
    assert [path.name for path in FOLDER.glob("hook-*.py")] == ["hook-skellytracker.py"]  # no hook for an other package


def test_the_entry_module_imports_only_os_and_the_hook_is_data_only():
    tree = ast.parse((FOLDER / "__init__.py").read_text(encoding="utf-8"))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert [alias.name for node in imports for alias in node.names] == ["os"]
    hook = ast.parse((FOLDER / "hook-skellytracker.py").read_text(encoding="utf-8"))
    assigned = {node.targets[0].id: ast.unparse(node.value) for node in hook.body if isinstance(node, ast.Assign)}
    assert set(assigned) == {"datas", "hiddenimports"} and assigned["hiddenimports"] == "[]"
    assert "'**/*.yaml'" in assigned["datas"] and "'**/tests/**'" in assigned["datas"]
    assert "binaries" not in assigned and "copy_metadata" not in ast.unparse(hook)


def test_the_entry_points_do_not_import_pyinstaller():
    code = ("import sys, skellytracker._pyinstaller as e\ne.get_hook_dirs(); e.get_PyInstaller_tests()\n"
            "sys.exit(1 if 'PyInstaller' in sys.modules else 0)")
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0  # noqa: S603


@pytest.mark.pyinstaller
def test_frozen_smoke_app(tmp_path):
    pytest.importorskip("PyInstaller")
    build = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--name", "smoke", "--distpath", str(tmp_path / "dist"),
             "--workpath", str(tmp_path / "work"), "--specpath", str(tmp_path), str(FOLDER / "tests" / "frozen_smoke.py")]
    done = subprocess.run(build, capture_output=True, text=True, check=False, cwd=tmp_path)  # noqa: S603
    assert done.returncode == 0, done.stderr[-3000:]
    app = tmp_path / "dist" / "smoke" / ("smoke.exe" if sys.platform == "win32" else "smoke")
    other = tmp_path / "other"
    other.mkdir()
    run = subprocess.run([str(app)], capture_output=True, text=True, check=False, cwd=other)  # noqa: S603
    assert run.returncode == 0 and "SMOKE OK" in run.stdout, (run.stdout[-2000:], run.stderr[-3000:])
    assert "frozen=True" in run.stdout
