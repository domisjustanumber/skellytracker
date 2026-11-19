"""The package sets `ORT_DISABLE_TELEMETRY=1` before ONNX Runtime loads, and keeps a value that the host set (ADR-BZ7X).

Each test runs a new Python process. A finder on `sys.meta_path` records the value of the variable
at the moment that `onnxruntime` is imported.
"""

import os
import subprocess
import sys

PROBE = """
import os, sys
seen = []
class Watch:
    def find_spec(self, name, path=None, target=None):
        if name == "onnxruntime":
            seen.append(os.environ.get("ORT_DISABLE_TELEMETRY"))
sys.meta_path.insert(0, Watch())
import skellytracker.core.eps  # a submodule import runs skellytracker/__init__.py first; it loads no onnxruntime
assert not seen and "onnxruntime" not in sys.modules
import onnxruntime
print(seen[0])
"""


def run_probe(preset: str | None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "ORT_DISABLE_TELEMETRY"}
    if preset is not None:
        env["ORT_DISABLE_TELEMETRY"] = preset
    done = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, capture_output=True, text=True, timeout=300,  # noqa: S603
                          check=True)
    return done.stdout.strip().splitlines()[-1]


def test_the_package_switches_telemetry_off_before_onnxruntime_loads():
    assert run_probe(None) == "1"


def test_a_value_that_the_host_set_stays():
    assert run_probe("0") == "0"
