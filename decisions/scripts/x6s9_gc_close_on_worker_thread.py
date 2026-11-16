"""Measure a close() of a MediaPipe Tasks landmarker from the garbage collector (ADR-X6S9).

The script puts an object that holds a landmarker in a reference cycle. Then it runs
``gc.collect()`` on the worker thread of that landmarker. The modes:

- ``direct``: a HolisticRunner whose finalizer closes the landmarker on the thread of the collector.
- ``runner``: a HolisticRunner with the finalizer of ``core/detectors/mediapipe_holistic.py``.
- ``old``: the old ``MediapipeHandKeypointDetector``.

Run: ``uv run --no-sync python -I decisions/scripts/x6s9_gc_close_on_worker_thread.py <mode>``.
It prints ``<mode> HANG`` or ``<mode> ok``.
"""
from __future__ import annotations

import gc
import os
import sys
import threading
import weakref

import numpy as np

mode = sys.argv[1]
image = np.zeros((64, 64, 3), np.uint8)
if mode == "old":
    from skellytracker.core.detectors.keypoint_detectors.mediapipe import (
        MediapipeHandDetectorConfig,
        MediapipeHandKeypointDetector,
        MediaPipeSession,
        MediaPipeSessionConfig,
    )

    holder = MediapipeHandKeypointDetector.create(
        MediapipeHandDetectorConfig(), MediaPipeSession.create(MediaPipeSessionConfig())
    )
    holder.detect(image)
    landmarker = holder.landmarker
else:
    from skellytracker.core.detectors.mediapipe_holistic import HolisticRunner

    holder = HolisticRunner("image")
    if mode == "direct":
        holder._finalizer.detach()
        holder._finalizer = weakref.finalize(holder, lambda lm: lm.close(), holder._landmarker)
    holder.run(image)
    landmarker = holder._landmarker
holder.cycle = holder
executor = landmarker._lib._executor  # MediaPipe 1.2.2: one worker thread for each landmarker
del holder, landmarker
gc.disable()
future = executor.submit(gc.collect)
waiter = threading.Thread(target=future.result, daemon=True)
waiter.start()
waiter.join(20)
print(mode, "HANG" if waiter.is_alive() else "ok", flush=True)
os._exit(0)  # a hung worker thread would block the normal exit
