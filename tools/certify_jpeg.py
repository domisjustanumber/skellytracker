"""Section 5 of the certify suite (``tools/certify_platform.py``): JPEG decode and preprocess.

The checks are in ``skellytracker.core.decode.certification.run_jpeg_certification`` of the package. When
this checkout does not have that module, the section is ``not-run`` with ``not-in-this-checkout``.

The section calls the entry point once with ``ep_key=None`` (the CPU paths, on each platform), and once
for each EP that passed section 3 (``pipeline_targets`` of ``section-3.json``, as section 4 reads it)
and that the module lists in ``GPU_FRAME_EPS`` or in ``AMD_EPS`` (when it has that list). A module
with no ``GPU_FRAME_EPS`` gets each passed EP: it answers ``not-run`` for an EP with no GPU frame path.
Section 3 tests ``directml`` once for each GPU (``directml@<device_key>``). The entry point takes no
device, so the section calls it once for each EP key, and ``details.runs`` records the GPUs that
section 3 tested for that key. The call counts only when each of those targets counts in section 3
(the hardware class of the GPU lists the EP, ``offered_on`` of ``certify_eps.py``). Otherwise each
``pass`` or ``fail`` of the call is ``record-only``: a ``directml`` failure on an NVIDIA or an Intel
GPU cannot fail the section. Each check of a call goes into the section as
``<ep>:<check name>`` (``cpu`` for the call with no EP), with its ``result``, its ``reason`` as the
``reason_code`` (unchanged), its ``numbers`` and its ``warnings``. The ``detail`` text of a check is
not kept: a report holds no error text (ADR-Y14H item 4). A call that raises is the check
``<ep>:run`` with ``fail``. ``scrub()`` of the frame runs over the whole result.

The section runs after section 4 (the frame runs ``SECTIONS`` in order). The pipeline checks then find
the model files that section 4 fetched: the frame deletes them only after the last section.
"""

from __future__ import annotations

import importlib
import json
import sys
from collections import Counter
from pathlib import Path

from certify_platform import outcome, private_terms, scrub

ENTRY = "skellytracker.core.decode.certification"


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def jpeg_eps(module, work: Path) -> dict[str, list[dict]]:
    """The section-3 targets of each GPU call, by EP key: each EP that passed section 3 and that the module supports when it lists them."""
    targets = ((read_json(work / "section-3.json") or {}).get("details") or {}).get("pipeline_targets") or []
    supported = getattr(module, "GPU_FRAME_EPS", None)
    if supported is not None:
        supported = (*supported, *getattr(module, "AMD_EPS", ()))  # AMD_EPS can be a dict: its keys are the EPs
    found: dict[str, list[dict]] = {}
    for target in targets:
        if not target.get("ort_fallback") and (supported is None or target["key"] in supported):
            found.setdefault(target["key"], []).append(target)
    return found


def section_jpeg(work: Path) -> dict:
    try:
        module = importlib.import_module(ENTRY)
    except ModuleNotFoundError as error:
        if error.name not in (ENTRY, ENTRY.rpartition(".")[0]):
            raise  # a missing dependency of the module is a crash of the section, not an absent module
        return {"result": "not-run", "reason_code": "not-in-this-checkout",
                "summary": "the JPEG certification entry point is not in this checkout", "checks": [], "details": {}}
    checks, runs = [], {}
    for ep_key, tested in ((None, []), *jpeg_eps(module, work).items()):
        label = ep_key or "cpu"
        scored = all(t.get("counts", True) for t in tested)  # as section 4: a target that does not count gives record-only

        def scored_result(result: str, scored: bool = scored) -> str:
            return result if scored or result not in ("pass", "fail") else "record-only"

        try:
            found = module.run_jpeg_certification(
                ep_key, progress=lambda name, label=label: print(f"section 5: {label}:{name}", file=sys.stderr, flush=True))
        except Exception as error:  # noqa: BLE001 - the other calls still run
            checks.append({"name": f"{label}:run", "result": scored_result("fail"), "reason_code": type(error).__name__})
            continue
        new = [{"name": f"{label}:{c['name']}", "result": scored_result(c["result"]), "reason_code": c["reason"],
                "numbers": c.get("numbers", {}), "warnings": c.get("warnings", [])} for c in found["checks"]]
        checks += new
        runs[label] = {"ep_key": ep_key, "schema": found.get("schema"), "facts": found.get("facts"), "scored": scored,
                       "device_keys": [t["device_key"] for t in tested if t.get("device_key")],
                       "counts": dict(Counter(c["result"] for c in new))}
    summary = "; ".join(f"{label}: " + ", ".join(f"{n} {result}" for result, n in sorted(run["counts"].items()))
                        for label, run in runs.items())
    result = {"result": outcome(checks), "reason_code": next((c["reason_code"] for c in checks if c["result"] == "fail"), None),
              "summary": summary or "no call of the entry point ended", "checks": checks, "details": {"runs": runs}}
    return scrub(result, *private_terms())
