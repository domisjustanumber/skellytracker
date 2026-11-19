# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
import sys, json  # noqa: E401
sys.path.insert(0, sys.argv[1])
import measure
measure.isolate(measure.ISO / "ep-cache")
from skellytracker.core.pipelines import get_pipeline, load_pipeline, start_pipeline  # noqa: E402
p = load_pipeline(get_pipeline("yolox-rtmw-wholebody@skellytracker").path)
run = start_pipeline(p, camera_ids=["a"], running_mode="video", execution_provider="cpu")
try:
    s = run.output_schema
    out = json.dumps(s, default=str)
    print(out[:3000])
    open(sys.argv[1] + "/output_schema.json", "w").write(json.dumps(s, default=str, indent=1))
finally:
    run.close()
