"""Section 5 of the certify suite (``tools/certify_platform.py``): JPEG decode and preprocess.

The checks are in ``skellytracker.core.decode.certification.run_jpeg_certification`` of the package. When
this checkout does not have that module, the section is ``not-run`` with ``not-in-this-checkout``.

The section calls the entry point once with ``ep_key=None`` (the CPU paths, on each platform), and once
for each EP that passed section 3 (``pipeline_targets`` of ``section-3.json``, as section 4 reads it)
and that the module lists in ``GPU_FRAME_EPS``. A module with no such list gets each passed EP: it
answers ``not-run`` for an EP with no GPU frame path. Each check of a call goes into the section as
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


def jpeg_eps(module, work: Path) -> list[str]:
    """The EP keys of the GPU calls: each EP that passed section 3, and that the module supports when it lists them."""
    targets = ((read_json(work / "section-3.json") or {}).get("details") or {}).get("pipeline_targets") or []
    supported = getattr(module, "GPU_FRAME_EPS", None)
    keys = dict.fromkeys(t["key"] for t in targets if not t.get("ort_fallback"))
    return [key for key in keys if supported is None or key in supported]


def section_jpeg(work: Path) -> dict:
    try:
        module = importlib.import_module(ENTRY)
    except ModuleNotFoundError as error:
        if error.name not in (ENTRY, ENTRY.rpartition(".")[0]):
            raise  # a missing dependency of the module is a crash of the section, not an absent module
        return {"result": "not-run", "reason_code": "not-in-this-checkout",
                "summary": "the JPEG certification entry point is not in this checkout", "checks": [], "details": {}}
    checks, runs = [], {}
    for ep_key in (None, *jpeg_eps(module, work)):
        label = ep_key or "cpu"
        try:
            found = module.run_jpeg_certification(
                ep_key, progress=lambda name, label=label: print(f"section 5: {label}:{name}", file=sys.stderr, flush=True))
        except Exception as error:  # noqa: BLE001 - the other calls still run
            checks.append({"name": f"{label}:run", "result": "fail", "reason_code": type(error).__name__})
            continue
        new = [{"name": f"{label}:{c['name']}", "result": c["result"], "reason_code": c["reason"], "numbers": c.get("numbers", {}),
                "warnings": c.get("warnings", [])} for c in found["checks"]]
        checks += new
        runs[label] = {"ep_key": ep_key, "schema": found.get("schema"), "facts": found.get("facts"),
                       "counts": dict(Counter(c["result"] for c in new))}
    summary = "; ".join(f"{label}: " + ", ".join(f"{n} {result}" for result, n in sorted(run["counts"].items()))
                        for label, run in runs.items())
    result = {"result": outcome(checks), "reason_code": next((c["reason_code"] for c in checks if c["result"] == "fail"), None),
              "summary": summary or "no call of the entry point ended", "checks": checks, "details": {"runs": runs}}
    return scrub(result, *private_terms())
