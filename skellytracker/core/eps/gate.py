"""The check rule of an EP on a GPU (ADR-21BK items 2 and 3, ADR-ER5X): a run starts only after a check.

An EP on a GPU can run when the project has a reviewed pass for the GPU model and OS (`ep_evidence.yaml`), or
when a quick check of `skellytracker.certify()` passed on this PC. It cannot run after a quick check that
failed on this PC. `check_start()` and `build_session()` call `require()`, so each run and each session obeys
the rule. The rule has no setting and no environment variable.

The certification code must run an EP before the EP has a result. It runs inside `certification_run()`,
which switches the rule off for this process. Only the certification code uses it: the probe, the image run
and the JPEG checks of the quick check, the JPEG certification and the certify suite.

This module loads no library and uses no network. It reads `quick-checks.json` of the EP store.
"""

import contextlib

from skellytracker.core.eps import evidence, store
from skellytracker.core.eps.catalog import EpCatalog
from skellytracker.core.errors import EpUnavailableError

NEEDS_CHECK = "quick-check-needed"  # no reviewed row and no quick check on this PC
FAILED_CHECK = "quick-check-failed"  # the last quick check on this PC failed
REASONS = {
    NEEDS_CHECK: "the project has no reviewed result for it on this GPU model, and no quick check passed on this PC",
    FAILED_CHECK: "its last quick check failed on this PC",
}

_certification_runs = 0  # the depth of `certification_run()` in this process


@contextlib.contextmanager
def certification_run():
    """Switch the check rule off in this process, for the certification code only. A run of an application never uses it."""
    global _certification_runs  # noqa: PLW0603 - one switch for the process: the sessions of a run have no common argument
    _certification_runs += 1
    try:
        yield
    finally:
        _certification_runs -= 1


def pair_key(catalog: EpCatalog, key: str, gpu, os_name: str) -> str:
    """The pair of an answer and of a local result. The pack version is in it, so a pack upgrade asks again.

    `gpu` comes from `ep_gpus()`, which gives only GPUs with PCI ids, so `gpu_id` is never None here. An EP of
    the Windows ML catalog takes the package version of its record, and a built-in EP takes `builtin`.
    """
    pack = catalog.pack(key) or (store.windows_ml_pack(catalog, key) if catalog.windows_ml(key) else {"version": "builtin"})
    return f"{key}|{pack['version']}|{os_name}|{evidence.gpu_id(gpu)}"


def local_result(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """`passed` or `failed`: the last quick check of the EP on this GPU model on this PC, for the pack version of today.

    None with no such check, and for a GPU with no PCI ids. It reads `quick-checks.json` of the EP store.
    """
    if evidence.gpu_id(gpu) is None:
        return None
    row = (store.read_json(store.store_root() / "quick-checks.json") or {}).get(pair_key(catalog, key, gpu, os_name))
    return row["result"] if isinstance(row, dict) and row.get("result") in ("passed", "failed") else None


def check_reason(catalog: EpCatalog, key: str, gpu, os_name: str) -> str | None:
    """None when the rule lets the EP run on the GPU, else `quick-check-failed` or `quick-check-needed`.

    It does not read the state of the pack. An EP with no GPU row, for example `cpu`, has no rule: call it only
    with a GPU of `ep_gpus()`.
    """
    local = local_result(catalog, key, gpu, os_name)
    if local == "failed":
        return FAILED_CHECK
    return None if local == "passed" or evidence.certified(key, gpu, os_name) else NEEDS_CHECK


def rule_passes(catalog: EpCatalog, key: str, gpu, os_name: str) -> bool:
    """True when `require()` does not raise for the EP on the GPU: the rule lets it run, or the rule is switched off."""
    return bool(_certification_runs) or check_reason(catalog, key, gpu, os_name) is None


def check_hint(key: str) -> str:
    return f"Run `skellytracker-eps certify {key} --quick`."


def require(catalog: EpCatalog, key: str, gpu, os_name: str) -> None:
    """Raise `EpUnavailableError` with the quick-check command when the rule does not let the EP run on the GPU."""
    if _certification_runs:
        return
    code = check_reason(catalog, key, gpu, os_name)
    if code is not None:
        raise EpUnavailableError(f"The EP '{key}' cannot run on '{gpu.name}': {REASONS[code]}.", check_hint(key))
