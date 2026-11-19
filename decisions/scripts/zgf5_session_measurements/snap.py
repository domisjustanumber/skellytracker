"""List file names, sizes and mtimes under the user folders of skellytracker. Usage: snap.py OUT."""

import json
import os
import sys
from pathlib import Path

roots = {"LOCALAPPDATA/skellytracker": Path(os.environ["LOCALAPPDATA"]) / "skellytracker",
         "~/.freemocap/skellytracker-models": Path.home() / ".freemocap" / "skellytracker-models",
         "~/.cache/skellytracker": Path.home() / ".cache" / "skellytracker"}
found = {}
for label, root in roots.items():
    if not root.exists():
        found[label] = None
        continue
    for folder, _, files in os.walk(root):
        for name in files:
            path = Path(folder) / name
            try:
                stat = path.stat()
                found[f"{label}/{path.relative_to(root).as_posix()}"] = [stat.st_size, int(stat.st_mtime)]
            except OSError:
                found[f"{label}/{path.relative_to(root).as_posix()}"] = "unreadable"
Path(sys.argv[1]).write_text(json.dumps(found, indent=0, sort_keys=True), encoding="utf-8")
print(len(found), "entries")
