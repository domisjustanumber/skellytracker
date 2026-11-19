# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""A child whose main returns while a non-daemon thread keeps running: Python waits for it at exit (threading._shutdown)."""
import threading, time  # noqa: E401
threading.Thread(target=lambda: time.sleep(10_000), name="stuck-worker").start()
print("dummy: main returns now", flush=True)
