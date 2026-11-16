"""The guard test of the lazy `onnxruntime` import, and the freeze rule (ADR-0XW9 item 3)."""

import ast
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
COMPUTED_METADATA = {"core/system/runtime.py", "core/system/environment.py"}  # best effort when frozen


def test_import_of_eps_loads_no_onnxruntime():
    code = "import sys, skellytracker.core.eps; sys.exit(1 if 'onnxruntime' in sys.modules else 0)"
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0  # noqa: S603


def freeze_problems(source: str, name: str) -> list[str]:
    problems = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module == "importlib.metadata":
            problems.append(f"{name}:{node.lineno}: from importlib.metadata import")
        if isinstance(node, ast.Import):
            problems += [f"{name}:{node.lineno}: import importlib.metadata as" for a in node.names
                         if a.name == "importlib.metadata" and a.asname]
        if not isinstance(node, ast.Call):
            continue
        called = ast.unparse(node.func)
        literal = bool(node.args) and isinstance(node.args[0], ast.Constant)
        if called in ("exec", "eval", "__import__") or (called.endswith("import_module") and not literal):
            problems.append(f"{name}:{node.lineno}: {called}")
        if called.startswith("importlib.metadata.") and called != "importlib.metadata.distributions":
            if not literal and name not in COMPUTED_METADATA:
                problems.append(f"{name}:{node.lineno}: {called} with a computed name")
        if called == "importlib.metadata.distributions" and name != "core/system/environment.py":
            problems.append(f"{name}:{node.lineno}: {called}")
    return problems


def test_freeze_rule_of_each_package_module():
    problems = []
    for path in sorted(PACKAGE.rglob("*.py")):
        name = path.relative_to(PACKAGE).as_posix()
        if "tests/" in name or name.startswith("_pyinstaller/"):
            continue
        problems += freeze_problems(path.read_text(encoding="utf-8"), name)
    assert problems == []


def test_freeze_rule_finds_each_bad_form():
    bad = [
        "import importlib\nimportlib.import_module(name)",
        "__import__('x')",
        "exec('x')",
        "eval('x')",
        "import importlib.metadata as m",
        "from importlib.metadata import version",
        "import importlib.metadata\nimportlib.metadata.version(name)",
        "import importlib.metadata\nimportlib.metadata.distributions()",
    ]
    assert all(freeze_problems(source, "core/x.py") for source in bad)
    assert freeze_problems("import importlib.metadata\nimportlib.metadata.version('mediapipe')", "core/x.py") == []


def test_import_of_pipelines_loads_no_onnxruntime_and_no_mediapipe():
    code = ("import sys, skellytracker.core.pipelines; "
            "sys.exit(1 if {'onnxruntime', 'mediapipe'} & set(sys.modules) else 0)")
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0  # noqa: S603
