# Evidence of ADR-1SZ9. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Count the person boxes that yolox-person finds in each 720p/1080p frame (read in place). Prints numbers only."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure  # noqa: E402

measure.isolate(measure.ISO / "ep-cache")
import numpy as np  # noqa: E402, F401

from skellytracker.core.pipelines import Frame, get_pipeline, load_pipeline, start_pipeline  # noqa: E402

data = load_pipeline(get_pipeline("yolox-rtmw-wholebody@skellytracker").path).model_dump(mode="json", exclude_unset=True)
person = next(n for n in data["nodes"] if n["id"] == "person")
person["inputs"] = {"image": "frame.image"}
person["params"]["object_decode"] = {"min_score": float(sys.argv[1]), "nms": {"post_nms_top_k": 20}}
person["params"]["max_instances"] = 20
data["nodes"] = [person]
data["outputs"] = {"boxes": "person.boxes"}
rows = []
for res in ("1280x720", "1920x1080"):
    for f in sorted(measure.FRAMES.glob(f"*_{res}_*.jpg"))[:int(sys.argv[3])]:
        with start_pipeline(load_pipeline(data), camera_ids=[0], running_mode="image", execution_provider=sys.argv[2]) as run:
            r = run.process(Frame(f.read_bytes(), 0))
        det = r["boxes"]
        scores = sorted((float(s) for s, p in zip(det.score, det.present) if p), reverse=True)  # noqa: B905
        rows.append({"file": f.name, "boxes": len(scores), "top_scores": [round(s, 3) for s in scores[:5]]})
        print(json.dumps(rows[-1]))
Path(measure.HERE / "people.json").write_text(json.dumps(rows, indent=1))
