# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""After measure.main returns: which InferenceSession / OrtValue / PipelineRun objects are still alive (before and after gc.collect)?
Shows whether the exact S8 path leaves sessions or device values for interpreter finalization (H1)."""
import gc, os, runpy, sys, weakref  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
import onnxruntime  # noqa: E402
from skellytracker.core import pipelines  # noqa: E402
refs = {"InferenceSession": [], "OrtValue": [], "PipelineRun": []}
for cls in (onnxruntime.InferenceSession, onnxruntime.OrtValue):
    real = cls.__init__
    def init(self, *a, _real=real, _name=cls.__name__, **k):
        _real(self, *a, **k); refs[_name].append(weakref.ref(self))  # noqa: E702
    cls.__init__ = init
real_start = pipelines.start_pipeline
def start(*a, **k):
    run = real_start(*a, **k); refs["PipelineRun"].append(weakref.ref(run)); return run  # noqa: E702
pipelines.start_pipeline = start
sys.argv = [os.path.join(HERE, "measure.py"), *sys.argv[1:]]
runpy.run_path(sys.argv[0], run_name="__main__")
alive = lambda: {k: f"{sum(r() is not None for r in v)}/{len(v)}" for k, v in refs.items()}  # noqa: E731
print("ALIVE after main returned:", alive(), flush=True)
print("gc.collect ->", gc.collect(), "ALIVE after gc:", alive(), flush=True)
import onnxruntime, psutil, skellytracker  # noqa: E401, E402
print(f"VERSIONS ort={onnxruntime.__version__} skellytracker={skellytracker.__file__}", flush=True)
for lib in sorted({m.path for m in psutil.Process().memory_maps() if "onnxruntime" in m.path.lower() and m.path.lower().endswith((".dll", ".pyd"))}):
    print(f"LOADED {lib}", flush=True)
