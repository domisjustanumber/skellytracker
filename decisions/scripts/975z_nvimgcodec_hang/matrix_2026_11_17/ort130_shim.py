# Evidence of ADR-975Z. This scratch script ran on 2026-11-17. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run a script under onnxruntime 1.30.0 with the package's ORT version check bypassed.

The bypass: registration.core_mismatch (imported from installer) refuses any ORT other than the catalog's 1.31.1.
Nothing else changes. usage: ort130_shim.py <script.py> args...
"""
import runpy
import sys

import onnxruntime

from skellytracker.core.eps import registration

registration.core_mismatch = lambda catalog: None
print(f"SHIM onnxruntime {onnxruntime.__version__}: core_mismatch bypassed", flush=True)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
