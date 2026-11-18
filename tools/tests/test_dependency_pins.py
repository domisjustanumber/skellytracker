"""The dependency rules of ``pyproject.toml`` (decisions N6E8, W09C, D3VP and 8Z5Q).

This test checks these rules, and ``pyproject.toml`` holds them:

- Each dependency of ``pyproject.toml``, in ``dependencies``, in each extra and in each dependency
  group, has an exact pin (``==``), with no range. An environment marker can limit a pin to a
  platform.
- ``onnxruntime`` is a base dependency with an exact 1.30 pin. On Windows the distribution is
  ``onnxruntime-windowsml``, with the same release. No dependency is ``onnxruntime-gpu``,
  ``onnxruntime-directml``, ``tensorrt``, an ``nvidia-*-cu12`` package or a plugin EP pack
  ``onnxruntime-ep-*``: a GPU EP comes only as a plugin EP pack. No extra is ``onnx-cpu``,
  ``onnx-cuda``, ``onnx-trt``, ``onnx-directml``, ``all-*`` or ``recommended-*``.
- ``onnx`` is a base dependency with an exact 1.22 pin, because the package builds the preprocess
  graph at run time. No extra is ``onnx``. onnx 1.23 writes IR version 14, and onnxruntime 1.31
  reads IR version 13 or lower.
- ``requires-python`` is ``==3.13.18``, and ``.python-version`` holds ``3.13.18``. Each CI workflow
  that tests or lints the package sets up Python 3.13.18.
- The ``mediapipe`` extra is ``mediapipe==1.2.2``.
- The uv environments are Windows on x86_64, Linux on x86_64 and macOS on arm64, and
  ``required-environments`` has the same list, so that a missing wheel fails at lock time. macOS on
  x86_64 is not supported, and ``README.md`` says so.
- The OpenCV dependency is ``opencv-contrib-python`` with an exact pin. No dependency is a headless
  OpenCV package (``opencv-python-headless`` or ``opencv-contrib-python-headless``).
  ``exclude-dependencies`` of ``[tool.uv]`` holds ``opencv-python``.
- The dev group pins ``ruff==0.17.5``. ``[tool.ruff.lint]`` keeps the rule set of ruff 0.15.17:
  ``select = ["E4", "E7", "E9", "F", "B", "S", "C4", "ISC", "PERF"]`` and ``ignore = ["ISC004"]``.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PROJECT = PYPROJECT["project"]
UV = PYPROJECT["tool"]["uv"]
PYTHON = "3.13.18"
# The publish workflow only builds the pure-Python wheel and the sdist with flit.
NOT_TESTED_WORKFLOWS = {"flit_publish_to_pypi.yml"}


def requirements() -> dict[str, list[Requirement]]:
    """The requirements of each dependency list: `dependencies`, `extra <name>` and `group <name>`."""
    found = {"dependencies": [Requirement(r) for r in PROJECT["dependencies"]]}
    for name, items in PROJECT.get("optional-dependencies", {}).items():
        found[f"extra {name}"] = [Requirement(r) for r in items]
    for name, items in PYPROJECT.get("dependency-groups", {}).items():
        found[f"group {name}"] = [Requirement(r) for r in items if isinstance(r, str)]
    return found


def pins(where: str) -> dict[str, str]:
    """The exact version of each requirement of one list, by its normalized name."""
    return {canonicalize_name(r.name): next(iter(r.specifier)).version for r in requirements()[where]}


def all_names() -> set[str]:
    return {canonicalize_name(r.name) for items in requirements().values() for r in items}


def test_each_dependency_has_an_exact_pin() -> None:
    loose = [
        f"{where}: {r}"
        for where, items in requirements().items()
        for r in items
        if [s.operator for s in r.specifier] != ["=="] or "*" in str(r.specifier)
    ]
    assert loose == []


def test_onnxruntime_is_a_base_dependency_and_no_gpu_package_is_a_dependency() -> None:
    base = {canonicalize_name(r.name): r for r in requirements()["dependencies"]}
    assert pins("dependencies")["onnxruntime"] == "1.30.0" and '!= "win32"' in str(base["onnxruntime"].marker)
    assert pins("dependencies")["onnxruntime-windowsml"].startswith("1.30.0.")
    assert '== "win32"' in str(base["onnxruntime-windowsml"].marker)
    gpu = sorted(
        n
        for n in all_names()
        if n in {"onnxruntime-gpu", "onnxruntime-directml", "tensorrt"}
        or n.startswith("onnxruntime-ep-")
        or (n.startswith("nvidia-") and n.endswith("-cu12"))
    )
    assert gpu == []
    extras = set(PROJECT.get("optional-dependencies", {}))
    old = {"onnx-cpu", "onnx-cuda", "onnx-trt", "onnx-directml"}
    assert sorted(e for e in extras if e in old or e.startswith(("all-", "recommended-"))) == []


def test_onnx_is_a_base_dependency() -> None:
    assert pins("dependencies")["onnx"].startswith("1.22.")
    assert "onnx" not in PROJECT.get("optional-dependencies", {})


def test_one_python_patch_release() -> None:
    assert PROJECT["requires-python"] == f"=={PYTHON}"
    assert (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip() == PYTHON
    versions = {
        (path.name, line.split(":", 1)[1].strip().strip("'\""))
        for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
        if path.name not in NOT_TESTED_WORKFLOWS
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("python-version:")
    }
    assert versions
    assert sorted(v for v in versions if v[1] != PYTHON) == []


def test_mediapipe_extra() -> None:
    assert PROJECT["optional-dependencies"]["mediapipe"] == ["mediapipe==1.2.2"]


def test_supported_platforms() -> None:
    expected = [
        "sys_platform == 'darwin' and platform_machine == 'arm64'",
        "sys_platform == 'linux' and platform_machine == 'x86_64'",
        "sys_platform == 'win32' and platform_machine == 'AMD64'",
    ]
    assert UV["environments"] == expected
    assert UV["required-environments"] == expected
    readme = " ".join((REPO_ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "macOS on Intel (x86_64) is not supported." in readme


def test_opencv_is_the_contrib_package() -> None:
    assert "opencv-contrib-python" in pins("dependencies")
    assert sorted(all_names() & {"opencv-python-headless", "opencv-contrib-python-headless"}) == []
    assert "opencv-python" in UV["exclude-dependencies"]


def test_ruff_pin_and_rule_set() -> None:
    assert pins("group dev")["ruff"] == "0.17.5"
    lint = PYPROJECT["tool"]["ruff"]["lint"]
    assert lint["select"] == ["E4", "E7", "E9", "F", "B", "S", "C4", "ISC", "PERF"]
    assert lint["ignore"] == ["ISC004"]
