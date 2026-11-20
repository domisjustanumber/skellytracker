"""`verify()`: check an EP in a `spawn` child, and keep the result in the EP store.

| Level | Check |
|---|---|
| L0 | The pack is present and current. `status()` and `recommend()` make this check with no library load. |
| L1 | The floors of the pack against `probe_host()`: vendor, compute capability, driver branch. |
| L2 | The pack registers, and the EP lists the device. |
| L3 | A trial session on a probe model: each node on the EP, and the output within `l3_atol` of the CPU EP. |

An EP pack is ready when it is installed, current, registers and lists a device. A pack with no
L3 pass stays usable, with one warning line for each process. Do not call `verify()` in a daemonic
worker process: it starts a child process. `spawn_child()` runs each child of `eps` that loads an EP
library: the probe of `verify()`, the image run of `certify()` and the `video` and `live` runs of the quick check.
"""

import multiprocessing
import os
import signal
import sys
import time
from collections.abc import Callable, Sequence

from skellytracker.core.eps import _verify_child, store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.recommendation import ep_gpus, install_hint
from skellytracker.core.eps.records import USABLE_STATES, Verdict
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import probe_host

TIMEOUT_SECONDS = 180.0  # the first TensorRT RTX session compiles the model
EXIT_GRACE_SECONDS = 20.0  # time a child gets to exit after its result (`hung-at-exit`); tools/certify_platform.py has the same value


def child_failure_reason(exit_code: int | None, timeout: float = TIMEOUT_SECONDS) -> str:
    if exit_code is None:
        return f"the verification process did not end in {timeout:.0f} s"
    if exit_code == 127:
        return "a library of the pack is missing or not complete (exit code 127)"
    return f"the verification process ended with the exit code {exit_code}"


def _child_main(target, args: tuple, connection) -> None:
    """The entry of each child of `spawn_child()`. On POSIX the child leads its own process group, so a stop gets its children too."""
    if os.name == "posix":
        os.setpgrp()
    target(*args, connection)


def _stop_tree(process) -> None:
    """Kill the child and its children."""
    if sys.platform == "win32":
        import psutil

        try:
            children = psutil.Process(process.pid).children(recursive=True)
        except psutil.Error:
            children = []
        for child in children:
            try:
                child.kill()
            except psutil.Error:
                pass
    elif os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    process.kill()
    process.join()


def spawn_child(target, args: tuple, *, timeout: float, grace: float = EXIT_GRACE_SECONDS, cancel=None,
                progress: Callable[[str], None] | None = None) -> tuple[dict | None, str | None, int | None]:
    """Run `target(*args, connection)` in a `spawn` child. Give `(result, problem, exit_code)`.

    The child sends each progress step as a `str` and then its result as one `dict`. `progress` gets each step in
    this process. `cancel` is an object with `is_set()`, for example a `threading.Event`. The child is stopped,
    with its process tree, after `timeout` s with no result, within about 0.1 s after `cancel` is set, and
    `grace` s after its result when it does not exit. `problem` is a fixed code: None, `timed-out`, `cancelled`,
    `crashed` (an exit code that is not 0), `no-result` (exit code 0 and no result) or, with a result,
    `hung-at-exit` or `crashed`. A child that gave its result keeps it.
    """
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_child_main, args=(target, args, sender))
    process.start()
    sender.close()
    started, result, done_at, problem, closed = time.monotonic(), None, None, None, False
    try:
        while True:
            if result is None and not closed:
                try:
                    if receiver.poll(0.1):
                        message = receiver.recv()
                        if isinstance(message, dict):
                            result, done_at = message, time.monotonic()
                        elif progress is not None:
                            progress(message)
                        continue
                except (EOFError, OSError):
                    closed = True
            else:
                process.join(0.1)
            if not process.is_alive():
                break
            now = time.monotonic()
            if cancel is not None and cancel.is_set() and result is None:
                problem = "cancelled"
            elif result is None and now - started > timeout:
                problem = "timed-out"
            elif result is not None and now - done_at > grace:
                problem = "hung-at-exit"
            if problem:
                _stop_tree(process)
                break
        while result is None and not closed:  # a result sent just before the exit
            try:
                if not receiver.poll(0):
                    break
                message = receiver.recv()
                result = message if isinstance(message, dict) else None
            except (EOFError, OSError):
                break
    finally:
        if process.is_alive():  # an error of `progress`, or Ctrl+C
            _stop_tree(process)
        receiver.close()
    exit_code = process.exitcode if problem is None else None
    if problem is None and exit_code != 0:
        problem = "crashed"
    elif problem is None and result is None:
        problem = "no-result"
    return result, problem, exit_code


def run_child(job: dict, *, timeout: float = TIMEOUT_SECONDS, grace: float = EXIT_GRACE_SECONDS, cancel=None) -> dict:
    """Run one verification job in a `spawn` child. A child that ends with no result gives a failed result.

    That failed result has `reason_code` (`timed-out`, `cancelled`, `crashed` or `no-result`) and `exit_code`.
    A child that gave its result and then did not exit cleanly keeps the result, and `exit_reason_code` is
    `hung-at-exit` or `crashed`. Else `exit_reason_code` is None. `cancel` is as for `spawn_child()`.
    """
    result, problem, exit_code = spawn_child(_verify_child.main, (job,), timeout=timeout, grace=grace, cancel=cancel)
    if result is None:
        reason = "the verification was cancelled" if problem == "cancelled" else child_failure_reason(
            None if problem == "timed-out" else exit_code, timeout)
        return {"level": job["level"], "ok": False, "reason": reason, "max_abs_diff": None, "exit_reason_code": None,
                "reason_code": problem, "exit_code": exit_code}
    return {**result, "exit_reason_code": problem}


def verify(keys: Sequence[str] | None = None, *, level: str = "L3", device_key: str | None = None,
           force: bool = False, cancel=None) -> tuple[Verdict, ...]:
    """Verify each EP key at level `L2` or `L3`. With no keys: each EP that is usable on this host.

    A stored result with the same key is returned with no new check, unless `force` is true. The
    key holds the ONNX Runtime distribution version, the pack, the driver version, the device, the OS
    build and the sha256 of the catalog entry of the pack (`store.entry_digest()`). A change elsewhere
    in the catalog keeps the stored result. A pack that is not installed raises `EpUnavailableError`.
    `cancel` is an object with `is_set()`: when it is set, the child of the running check stops within about
    0.1 s, its verdict has `reason_code` `cancelled` and is not stored, and no other key is checked.
    """
    if level not in ("L2", "L3"):
        raise ValueError(f"the level must be 'L2' or 'L3', not {level!r}")
    catalog, host = load_catalog(), probe_host()
    verdicts = []
    for key in catalog.keys() if keys is None else keys:
        row, pack = catalog.ep(key), catalog.pack(key)
        usable = ep_gpus(catalog, key, host)
        target = device_key if device_key is not None else usable[0][0] if usable else None
        gpu = dict(usable).get(target)
        state, _, reason = store.pack_state(catalog, key, gpu, target, host.os_build)
        if state not in USABLE_STATES and not (state == "not_ready" and force):
            if keys is None:
                continue
            raise EpUnavailableError(f"The EP '{key}' is not available: {reason}.", install_hint(key))
        stand_in = store.windows_ml_pack(catalog, key) if catalog.windows_ml(key) else {"id": key, "version": "builtin"}
        stored_key = store.verdict_key(catalog, pack or stand_in, gpu, target, host.os_build)
        record = None if force else store.read_verdicts().get(stored_key)
        if record is None or (level == "L3" and record["level"] == "L2" and record["ok"]):
            record = run_child({"key": key, "pack": pack, "gpu": gpu, "device_key": target, "level": level,
                                "atol": float(row.get("l3_atol", 1e-4))}, cancel=cancel)
            if record.get("reason_code") != "cancelled":
                store.write_verdict(stored_key, record)
        verdicts.append(Verdict(key, record["level"], record["ok"], stored_key, pack["id"] if pack else None,
                                pack["version"] if pack else None, record.get("reason"), record.get("max_abs_diff"),
                                record.get("exit_reason_code"), record.get("reason_code"), record.get("exit_code")))
        if record.get("reason_code") == "cancelled":
            break
    return tuple(verdicts)
