# Evidence of ADR-975Z. This scratch script ran on 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Compare matrix.txt with the prediction: HANG iff n = 1 and the effective S < T (a refused S > T falls back to T)."""
import re
import sys
from pathlib import Path

rows = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
table: dict[tuple[int, int], dict[int, str]] = {}
bad = []
for row in rows:
    m = re.search(r"^(\S+).*args=(\d+) (\d+) (\d+) ::(.*?)::", row)
    result, t, s, n = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    effective = s if s <= t else t
    predicted = "HANG" if n == 1 and effective < t else "ok"
    table.setdefault((t, s), {})[n] = result
    if result != predicted:
        bad.append(f"CONTRADICTS predicted={predicted}: {row}")
    if s == t + 1 and "Invalid" not in m.group(5):
        bad.append(f"no 'Invalid' log for refused S: {row}")
print("T  S   n=1   n=2")
for (t, s), cells in sorted(table.items()):
    print(f"{t}  {s}{'*' if s > t else ' '}  {cells.get(1, '?'):5} {cells.get(2, '?')}")
print(f"{len(rows)} cells, {len(bad)} contradictions")
print("\n".join(bad))
