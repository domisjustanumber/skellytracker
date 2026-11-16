"""The script of the frozen part of the local GPU gate.

It installs the `trt-rtx` pack into the EP store of `SKELLYTRACKER_EP_STORE` (a new folder), with
the verification in a child process, and builds one session on the pack. It prints
`BOUND <EP name>` for the first provider of the session. With `SKELLYTRACKER_GPU_GATE_WHEELS`, the
install reads the wheels from that folder, with no network.
"""

import multiprocessing
import os
import sys


def main() -> int:
    from skellytracker.core import eps
    from skellytracker.core.eps import _probe_model
    from skellytracker.core.eps.cli import main as eps_cli

    wheels = os.environ.get("SKELLYTRACKER_GPU_GATE_WHEELS")
    code = eps_cli(["install", "trt-rtx", "--yes", *(["--from-dir", wheels] if wheels else [])])
    if code != 0:
        return code
    session, report = eps.build_session(_probe_model.model_bytes(), execution_provider="trt-rtx")
    print(f"frozen={getattr(sys, 'frozen', False)} cpu_nodes={report.cpu_nodes} used_ep={report.used_ep}")
    print(f"BOUND {session.get_providers()[0]}")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()  # the verification child of a frozen app starts this script again
    sys.exit(main())
