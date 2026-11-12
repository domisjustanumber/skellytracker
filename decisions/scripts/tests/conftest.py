"""Make the scripts in `decisions/scripts/` importable from their tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
