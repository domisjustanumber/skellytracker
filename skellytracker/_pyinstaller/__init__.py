"""The PyInstaller entry points of skellytracker. No skellytracker module imports this package.

PyInstaller finds the hook folder through the entry point group `pyinstaller40`. The hook of
skellytracker is data only: it collects the YAML files of the package. It has no hidden imports,
because each import of the package is a plain statement. The hook of ONNX Runtime collects the
installed ONNX Runtime distribution (ADR-K8Q0 item 2). PyInstaller gives a hook of this folder
priority over the hook of `pyinstaller-hooks-contrib` for the same module.
"""

import os


def get_hook_dirs() -> list[str]:
    return [os.path.dirname(__file__)]


def get_PyInstaller_tests() -> list[str]:  # noqa: N802 - the name that PyInstaller looks for
    return [os.path.join(os.path.dirname(__file__), "tests")]
