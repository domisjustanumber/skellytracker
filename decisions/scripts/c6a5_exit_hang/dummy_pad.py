# Evidence of ADR-C6A5. This scratch script ran on 2026-11-18 and 2026-11-19. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""A child that writes PAD_KB KiB to stdout and to stderr in an atexit handler, as a CUDA/TensorRT teardown log would."""
import atexit, os, sys  # noqa: E401
def pad():
    line = "p" * 1023 + "\n"
    for _ in range(int(os.environ.get("PAD_KB", "1024"))):
        sys.stdout.write(line); sys.stderr.write(line)  # noqa: E702
    sys.stdout.flush(); sys.stderr.flush()  # noqa: E702
atexit.register(pad)
print("dummy_pad: main returns now", flush=True)
