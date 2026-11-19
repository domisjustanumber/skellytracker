"""The PyInstaller entry points and hook: fast checks, and the slow frozen smoke test (`pytest -m pyinstaller`)."""

import ast
import importlib.metadata
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

import skellytracker._pyinstaller as entry

FOLDER = Path(entry.__file__).parent
GPU_MARKS = ("cuda", "cudnn", "cublas", "nvinfer", "tensorrt", "nvjpeg", "nvidia")  # a GPU EP or an NVIDIA library


def test_entry_points_give_one_folder_each():
    points = {point.name: point for point in importlib.metadata.entry_points(group="pyinstaller40")
              if point.value.startswith("skellytracker.")}  # numpy and other packages have the same names
    assert points["hook-dirs"].value == "skellytracker._pyinstaller:get_hook_dirs"
    assert points["tests"].value == "skellytracker._pyinstaller:get_PyInstaller_tests"
    (hooks,), (tests,) = points["hook-dirs"].load()(), points["tests"].load()()
    assert Path(hooks) == FOLDER and Path(tests) == FOLDER / "tests" and Path(tests).is_dir()
    # no hook for an other package, except the hook of ONNX Runtime (ADR-K8Q0 item 2)
    assert sorted(path.name for path in FOLDER.glob("hook-*.py")) == ["hook-onnxruntime.py", "hook-skellytracker.py"]


def test_the_entry_module_imports_only_os_and_the_hook_is_data_only():
    tree = ast.parse((FOLDER / "__init__.py").read_text(encoding="utf-8"))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert [alias.name for node in imports for alias in node.names] == ["os"]
    hook = ast.parse((FOLDER / "hook-skellytracker.py").read_text(encoding="utf-8"))
    assigned = {node.targets[0].id: ast.unparse(node.value) for node in hook.body if isinstance(node, ast.Assign)}
    assert set(assigned) == {"datas", "hiddenimports"} and assigned["hiddenimports"] == "[]"
    assert "'**/*.yaml'" in assigned["datas"] and "'**/tests/**'" in assigned["datas"]
    assert "binaries" not in assigned and "copy_metadata" not in ast.unparse(hook)


def test_the_onnxruntime_hook_collects_the_installed_distribution_and_no_gpu_library():
    pytest.importorskip("PyInstaller")
    from skellytracker.core.eps.installer import installed_ort

    hook = runpy.run_path(str(FOLDER / "hook-onnxruntime.py"))
    binaries = [(Path(source).name.lower(), Path(dest).parts[0]) for source, dest in hook["binaries"]]
    assert binaries and {top for _, top in binaries} <= {"onnxruntime", "windowsml"}
    assert not [name for name, _ in binaries if any(mark in name for mark in GPU_MARKS)]
    names = {Path(dest).name.split("-")[0] for _, dest in hook["datas"] if dest.endswith(".dist-info")}
    assert installed_ort()[0].replace("-", "_") in names
    assert any(Path(dest).name == "datasets" for _, dest in hook["datas"])
    if sys.platform == "win32":
        assert "windowsml" in names and ("microsoft.windows.ai.machinelearning.dll", "windowsml") in binaries


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
    assert "frozen=True" in run.stdout and "used_ep=cpu" in run.stdout
    bundled = [path.name.lower() for path in app.parent.rglob("*") if path.is_file()]
    assert not [name for name in bundled if any(mark in name for mark in GPU_MARKS)]
