"""Timestamps and the safe close of MediaPipe Tasks landmarkers."""
from __future__ import annotations

import threading
import time
import weakref
from typing import Any


def next_timestamp_ms(last_ms: int) -> int:
    """The fallback timestamp of a VIDEO-mode call: the clock, but always more than ``last_ms``."""
    return max(int(time.monotonic() * 1000), last_ms + 1)


def _close_off_thread(landmarker: Any) -> None:
    # The garbage collector can run on the landmarker's own worker thread; close() there waits on itself.
    try:
        threading.Thread(target=landmarker.close, daemon=True).start()
    except RuntimeError:
        pass  # Interpreter shutdown: MediaPipe ignores its calls from then on.


def close_on_collect(owner: object, landmarker: Any) -> weakref.finalize:
    """Close ``landmarker`` on a new thread when ``owner`` is freed (ADR-X6S9).

    Call ``detach()`` on the result before an explicit ``landmarker.close()``.
    """
    finalizer = weakref.finalize(owner, _close_off_thread, landmarker)
    finalizer.atexit = False
    return finalizer
