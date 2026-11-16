"""`verify()`: check an EP in a `spawn` child, and keep the result in the EP store.

| Level | Check |
|---|---|
| L0 | The pack is present and current. `status()` and `recommend()` make this check with no library load. |
| L1 | The floors of the pack against `probe_host()`: vendor, compute capability, driver branch. |
| L2 | The pack registers, and the EP lists the device. |
| L3 | A trial session on a probe model: each node on the EP, and the output within `l3_atol` of the CPU EP. |

An EP pack is ready when it is installed, current, registers and lists a device. A pack with no
L3 pass stays usable, with one warning line for each process. Do not call `verify()` in a daemonic
worker process: it starts a child process.
"""

import multiprocessing
from collections.abc import Sequence

from skellytracker.core.eps import _verify_child, store
from skellytracker.core.eps.catalog import load_catalog
from skellytracker.core.eps.recommendation import ep_gpus
from skellytracker.core.eps.records import USABLE_STATES, Verdict
from skellytracker.core.errors import EpUnavailableError
from skellytracker.core.system.host import probe_host

TIMEOUT_SECONDS = 180.0  # the first TensorRT RTX session compiles the model


def child_failure_reason(exit_code: int | None) -> str:
    if exit_code is None:
        return f"the verification process did not end in {TIMEOUT_SECONDS:.0f} s"
    if exit_code == 127:
        return "a library of the pack is missing or not complete (exit code 127)"
    return f"the verification process ended with the exit code {exit_code}"


def run_child(job: dict) -> dict:
    """Run one verification job in a `spawn` child. A child that ends with no result gives a failed result."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_verify_child.main, args=(job, sender))
    process.start()
    sender.close()
    result = None
    try:
        if receiver.poll(TIMEOUT_SECONDS):
            result = receiver.recv()
    except (EOFError, OSError):
        pass
    process.join(10)
    if process.is_alive():
        process.kill()
        process.join()
        return {"level": job["level"], "ok": False, "reason": child_failure_reason(None), "max_abs_diff": None}
    return result or {"level": job["level"], "ok": False, "reason": child_failure_reason(process.exitcode), "max_abs_diff": None}


def verify(keys: Sequence[str] | None = None, *, level: str = "L3", device_key: str | None = None,
           force: bool = False) -> tuple[Verdict, ...]:
    """Verify each EP key at level `L2` or `L3`. With no keys: each EP that is usable on this host.

    A stored result with the same key is returned with no new check, unless `force` is true. The
    key holds the ONNX Runtime version, the pack, the driver version, the device, the OS build and
    the catalog revision. A pack that is not installed raises `EpUnavailableError`.
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
            raise EpUnavailableError(f"The EP '{key}' is not available: {reason}.")
        stored_key = store.verdict_key(catalog, pack or {"id": key, "version": "builtin"}, gpu, target, host.os_build)
        record = None if force else store.read_verdicts().get(stored_key)
        if record is None or (level == "L3" and record["level"] == "L2" and record["ok"]):
            record = run_child({"key": key, "pack": pack, "gpu": gpu, "device_key": target, "level": level,
                                "atol": float(row.get("l3_atol", 1e-4))})
            store.write_verdict(stored_key, record)
        verdicts.append(Verdict(key, record["level"], record["ok"], stored_key, pack["id"] if pack else None,
                                pack["version"] if pack else None, record.get("reason"), record.get("max_abs_diff")))
    return tuple(verdicts)
