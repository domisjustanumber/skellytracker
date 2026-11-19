# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Extract the three synchronized videos (data only, nothing run from the zip), probe them, and write the JPEG bytes of the first N frames.

Output (scratchpad only, deleted at the end): data/videos/*.mp4, data/jpeg_q{Q}.pkl = {"cams": [...], "frames": [[bytes per cam] per frame]}.
"""
import os
import json
import pickle
import sys
import zipfile
from pathlib import Path

import cv2

HERE = Path(__file__).resolve().parent
ZIP = Path(os.environ["SAMPLE_DATA_ZIP"])
DATA = HERE / "data"
VID = DATA / "videos"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600


def main():
    VID.mkdir(parents=True, exist_ok=False if not VID.exists() else True)
    with zipfile.ZipFile(ZIP) as z:
        names = [n for n in z.namelist() if n.startswith("freemocap_sample_data/synchronized_videos/") and n.endswith(".mp4")]
        for n in names:
            target = VID / Path(n).name  # flat name: no path from the zip is used
            if not target.exists():
                with z.open(n) as src, open(target, "wb") as dst:
                    while chunk := src.read(1 << 20):
                        dst.write(chunk)
    vids = sorted(VID.glob("*.mp4"))
    probe = []
    for v in vids:
        cap = cv2.VideoCapture(str(v))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        probe.append({"cam": v.stem[-4:], "w": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), "h": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                      "frames_meta": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), "fps": cap.get(cv2.CAP_PROP_FPS),
                      "codec": "".join(chr((fourcc >> 8 * i) & 0xFF) for i in range(4))})
        cap.release()
    caps = [cv2.VideoCapture(str(v)) for v in vids]
    out = {q: [] for q in (90, 75)}
    for i in range(N):
        row = {q: [] for q in out}
        for cap in caps:
            ok, frame = cap.read()
            if not ok:
                raise SystemExit(f"frame {i} missing")
            for q in out:
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, q])
                row[q].append(buf.tobytes())
        for q in out:
            out[q].append(row[q])
    for cap in caps:
        cap.release()
    cams = [p["cam"] for p in probe]
    for q, frames in out.items():
        with open(DATA / f"jpeg_q{q}.pkl", "wb") as f:
            pickle.dump({"cams": cams, "frames": frames}, f)
        sizes = [len(b) for r in frames for b in r]
        probe.append({"quality": q, "n": len(frames), "mean_kB": sum(sizes) / len(sizes) / 1e3})
    (HERE / "data_probe.json").write_text(json.dumps(probe, indent=1))
    print(json.dumps(probe, indent=1))


if __name__ == "__main__":
    main()
