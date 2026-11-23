"""Each skellytracker entry of `verified_against` in the vector files names a function of the package.

This test stays in skellytracker. The vector tools (`tools/make_vectors.py`, `tools/vector_form.py`)
move to the specs repository, which has no package. So they check the form of an entry only
(`vector_form.PACKAGE_ENTRY`). This test imports the package module of each entry and checks that
the entry names a callable. It reads only the vector files of this checkout, never a file of
`intakes/` or of a record (ADR-AD33).
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
import yaml

from vector_form import PACKAGE_ENTRY

REPO_ROOT = Path(__file__).resolve().parents[2]
VECTOR_FOLDERS = (REPO_ROOT / "specs" / "model-sidecar" / "vectors", REPO_ROOT / "specs" / "pipeline" / "vectors")


def package_function(entry: str) -> Any:
    """Return the skellytracker function named by `skellytracker/<path>.py::function`, else None.

    The function imports only a module of the package of this checkout. It refuses an entry of
    another form, a path with `..` and a path that is not a file of the package.
    """
    path, _, name = entry.partition("::")
    if not PACKAGE_ENTRY.fullmatch(entry) or ".." in path or not (REPO_ROOT / path).is_file():
        return None
    module = importlib.import_module(Path(path).with_suffix("").as_posix().replace("/", "."))
    return getattr(module, name, None)


def package_entries() -> list[Any]:
    """Each skellytracker entry of each vector file, at file and at case level, once for each file."""
    params = []
    for folder in VECTOR_FOLDERS:
        for path in sorted(folder.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            entries = [
                *data.get("verified_against", []),
                *(entry for case in data["cases"] for entry in case.get("verified_against", [])),
            ]
            params += [
                pytest.param(entry, id=f"{path.name}:{entry}")
                for entry in dict.fromkeys(e for e in entries if isinstance(e, str))
            ]
    return params


def test_the_vector_files_name_package_functions() -> None:
    assert package_entries()


@pytest.mark.parametrize("entry", package_entries())
def test_each_package_entry_names_a_function(entry: str) -> None:
    assert callable(package_function(entry)), f"{entry}: not a function"


@pytest.mark.parametrize(
    "entry",
    [
        "tools/make_vectors.py::main",
        "skellytracker/../tools/make_vectors.py::main",
        "skellytracker/core/no_such_module.py::run",
        "skellytracker/core/model_spec/rules.py",
    ],
)
def test_an_entry_outside_the_package_imports_nothing(entry: str) -> None:
    assert package_function(entry) is None
