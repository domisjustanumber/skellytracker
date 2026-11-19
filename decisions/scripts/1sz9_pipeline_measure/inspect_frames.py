# Evidence of ADR-1SZ9. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Read the 720p and 1080p frames in place: byte size, SOF type, chroma sampling, DHT present. Writes no image."""
import os
import json
import sys
from pathlib import Path

FRAMES = Path(os.environ["JPEG_FRAMES_DIR"])


def segments(data: bytes):
    i, out = 2, []
    while i < len(data) - 4 and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xDA:
            out.append((marker, None))
            break
        length = int.from_bytes(data[i + 2:i + 4], "big")
        out.append((marker, data[i + 4:i + 2 + length]))
        i += 2 + length
    return out


def describe(path: Path) -> dict:
    data = path.read_bytes()
    segs = segments(data)
    info = {"file": path.name, "bytes": len(data), "dht": sum(1 for m, _ in segs if m == 0xC4)}
    for marker, body in segs:
        if marker in (0xC0, 0xC1, 0xC2):
            h, w, n = int.from_bytes(body[1:3], "big"), int.from_bytes(body[3:5], "big"), body[5]
            comps = [(body[6 + 3 * k] , body[7 + 3 * k] >> 4, body[7 + 3 * k] & 15) for k in range(n)]
            y = comps[0]
            chroma = {(2, 1): "4:2:2", (2, 2): "4:2:0", (1, 1): "4:4:4"}.get((y[1], y[2]), f"{y[1]}x{y[2]}")
            info.update(sof=hex(marker), width=w, height=h, components=n, chroma=chroma)
    return info


if __name__ == "__main__":
    rows = [describe(p) for p in sorted(FRAMES.glob("*.jpg")) if any(r in p.name for r in ("_1280x720_", "_1920x1080_"))]
    for row in rows:
        print(json.dumps(row))
    Path(sys.argv[1]).write_text(json.dumps(rows, indent=1))
