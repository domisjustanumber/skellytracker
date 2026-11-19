# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Run measure.py (or another script) unchanged, with exit markers and one exit variant.

Env:
  EXIT_MODE   normal | gc (del + gc.collect after main) | osexit (flush, os._exit(0)) | leak (keep the run alive, skip close())
  EXIT_FH     faulthandler file; a traceback dump of each thread is armed EXIT_DUMP_S seconds after main returns
  EXIT_SCRIPT the script to run (default: measure.py next to this file)
Markers (stdout, flushed, wall time): main-returned, atexit-last, builtins-teardown (from a __del__ at module teardown).
"""
import atexit
import faulthandler
import gc
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = os.environ.get("EXIT_MODE", "normal")
SCRIPT = os.environ.get("EXIT_SCRIPT", os.path.join(HERE, "measure.py"))
fh = open(os.environ.get("EXIT_FH", os.devnull), "w")  # noqa: SIM115 - lives to the process end
faulthandler.enable(fh)


def mark(what: str) -> None:
    os.write(1, f"MARK {what} t={time.time():.3f}\n".encode())


atexit.register(mark, "atexit-last")  # registered first: runs last of the atexit handlers


class _Teardown:
    def __del__(self):
        os.write(1, f"MARK builtins-teardown t={time.time():.3f}\n".encode())


import builtins  # noqa: E402

builtins._exit_hang_marker = _Teardown()  # cleared late in module teardown

if MODE == "leak":
    from skellytracker.core import pipelines
    from skellytracker.core.pipelines import run as run_module

    kept = []
    real_start = pipelines.start_pipeline

    def start_and_keep(*args, **kwargs):
        run = real_start(*args, **kwargs)
        kept.append(run)
        return run

    pipelines.start_pipeline = start_and_keep
    run_module.PipelineRun.close = lambda self: None  # the run, its sessions and device values live into finalization
    builtins._exit_hang_kept = kept

sys.argv = [SCRIPT, *sys.argv[1:]]
runpy.run_path(SCRIPT, run_name="__main__")
mark("main-returned")
try:  # the loaded ONNX Runtime and EP libraries, and the versions (for the record of each run)
    import onnxruntime
    import psutil
    import skellytracker

    libs = sorted({m.path for m in psutil.Process().memory_maps() if "onnxruntime" in m.path.lower() and m.path.lower().endswith((".dll", ".pyd"))})
    print(f"VERSIONS ort={onnxruntime.__version__} skellytracker={skellytracker.__file__}", flush=True)
    for lib in libs:
        print(f"LOADED {lib}", flush=True)
except Exception as error:  # noqa: BLE001
    print(f"LOADED ? {error}", flush=True)
faulthandler.dump_traceback_later(float(os.environ.get("EXIT_DUMP_S", "60")), repeat=True, file=fh)
if MODE == "gc":
    print(f"gc.collect -> {gc.collect()}", flush=True)
    mark("gc-done")
if MODE == "unreg":  # free what is left, then unload the EP plugin library while every thread is alive and no loader lock is held
    import onnxruntime
    from skellytracker.core.eps import registration

    print(f"gc.collect -> {gc.collect()}", flush=True)
    for reg in list(registration._registered.values()):
        try:
            onnxruntime.unregister_execution_provider_library(reg.ep_name)
            print(f"unregistered {reg.ep_name}", flush=True)
        except Exception as error:  # noqa: BLE001
            print(f"unregister {reg.ep_name} failed: {error}", flush=True)
    try:
        import psutil

        still = [m.path for m in psutil.Process().memory_maps() if "onnxruntime_providers_cuda" in m.path.lower() or "tensorrt" in m.path.lower()]
        print(f"after unregister, EP libraries still mapped: {still}", flush=True)
    except Exception as error:  # noqa: BLE001
        print(f"after unregister, map check failed: {error}", flush=True)
    mark("unreg-done")
if MODE == "terminate":  # skip the DLL detach phase entirely
    import ctypes

    sys.stdout.flush()
    mark("terminate-now")
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    ok = k32.TerminateProcess(ctypes.c_void_p(-1), 0)  # -1: the pseudo-handle of this process (a c_int -1 is not it on x64)
    print(f"TerminateProcess failed: {ok} {ctypes.get_last_error()}", flush=True)
if MODE == "osexit":
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
