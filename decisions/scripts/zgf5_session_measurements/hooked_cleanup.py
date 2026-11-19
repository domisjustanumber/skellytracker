"""Run the cleanup step of the XSE7 rehearsal with the same in-memory catalog hook as its run step.

Usage: python hooked_cleanup.py PATH_TO_xse7_windows_ml_rehearsal.py
"""
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location("reh", sys.argv[1])
reh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reh)
reh.hook()
print(json.dumps({"step": "hooked-cleanup", **reh.cleanup()}, default=str))
