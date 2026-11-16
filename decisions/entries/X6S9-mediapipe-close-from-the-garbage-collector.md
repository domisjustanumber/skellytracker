# X6S9 — A MediaPipe landmarker that the garbage collector closes on its own worker thread hangs

**Status:** evidence, 2026-11-16 (measured in stage 1.8 of the implementation plan).

## Decision

1. In MediaPipe 1.2.2, a `close()` of a Tasks landmarker on the worker thread of that landmarker
   waits for ever. The garbage collector can run there. Thus an object in a reference cycle that
   holds a landmarker can hang the process when the collector frees it.
2. The Holistic runner `core/detectors/mediapipe_holistic.py` closes its landmarker from the
   collector on a new daemon thread. An explicit `close()` closes it on the calling thread.
   The finalizer does not run at exit: from then on, MediaPipe ignores its calls.
3. The old MediaPipe detectors had the same defect: the `__del__` of the MediaPipe landmarker
   closed it on the thread of the collector. In stage 1.8 they get the finalizer of the runner,
   `close_on_collect` of `core/detectors/keypoint_detectors/mediapipe/landmarker_lifetime.py`.

## Reason

- Each Tasks landmarker of MediaPipe 1.2.2 has a `SerialDispatcher` with a `ThreadPoolExecutor` of
  one worker (`mediapipe/tasks/python/core/serial_dispatcher.py`). Each C call goes to that worker,
  and the caller waits for its result (`create_python_wrapper` in
  `mediapipe/tasks/python/core/mediapipe_c_utils.py`). `close()` makes the C call
  `MpHolisticLandmarkerClose`, then shuts down the executor. On the worker thread, the call waits
  for the worker itself.
- The worker thread runs Python code, so the collector can run on it.
- A refused call keeps its frames in its traceback. These frames can make the reference cycle. The
  implementation plan gives this path for the hang of the MediaPipe tests
  ([1.8](../../specs/sidecar-implementation-plan.md#18-mediapipe-holistic-runner)).

## Evidence

- Tool: `mediapipe` 1.2.2, Python 3.13.18, Windows, CPU. Script:
  [`x6s9_gc_close_on_worker_thread.py`](../scripts/x6s9_gc_close_on_worker_thread.py). It puts the
  object in a cycle, then runs `gc.collect()` on the worker thread of its landmarker, and waits
  20 s.
- Result: mode `direct` (a finalizer that calls `close()`): `HANG`. Mode `runner` (the finalizer of
  the runner): `ok`. Mode `old` (`MediapipeHandKeypointDetector`): `HANG` before the fix of the
  old detectors in stage 1.8, and `ok` after it.
- The test `test_gc_on_the_landmarker_worker_thread_does_not_hang` of
  `skellytracker/tests/test_mediapipe_holistic.py` runs the `runner` case in a subprocess.

## Alternatives rejected

- A check of the current thread in the finalizer: it reads private names of MediaPipe for each
  close, and a new thread costs less.

## Not repeated

- The script reads the private attribute `_lib._executor` of the landmarker. A MediaPipe update can
  rename it.
